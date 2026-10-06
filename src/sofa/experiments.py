"""Experiment runners and command-line interface (§7, §9).

Usage::

    python -m sofa.experiments run E0 --seeds 10 --n 400 --out results/
    python -m sofa.experiments plot E0 --out results/

Implemented: E0 (verification against §2.3, M1), E1 (sincere mechanics, M2), E2 (cartels),
E3 (transparency) and E4 (safeguards) (M3), E5 (feedback, equity, mechanism comparison;
M4), E6 (evolution of strategies; M5). Cells in which W cannot change are solved,
with a guard and one annual cross-check per experiment (M2 review decision).
"""

from __future__ import annotations

import argparse
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from joblib import Parallel, delayed, parallel_config

from sofa import baselines, metrics
from sofa.config import Params, load_experiment_config
from sofa.flows import (
    cycle_return_shares,
    flows_at_steady_state,
    iterate_fixed_W,
    steady_state,
)
from sofa.model import SOFAModel, World, build_world, evaluate
from sofa.population import Roles, assign_roles
from sofa.rng import RNGStreams
from sofa.safeguards import cap_project
from sofa.strategies import cartel_rows, choose_members, random_sparse_W

CONFIG_DIR = Path(__file__).resolve().parents[2] / "experiments" / "configs"


# --- Helpers ----------------------------------------------------------------------------
def map_seeds(fn: Callable, cfg: dict[str, Any], seeds: int, n_jobs: int) -> list:
    """Run ``fn(cfg, seed)`` for every seed in parallel, one BLAS thread per worker.

    Without the thread limit each worker's linear algebra spawns its own threads and the
    cores are oversubscribed (solves at N = 500 slowed from about 10 ms to 0.7 s).
    """
    with parallel_config(backend="loky", inner_max_num_threads=1):
        return Parallel(n_jobs=n_jobs)(delayed(fn)(cfg, s) for s in range(seeds))


def git_commit() -> str:
    """Return the current git commit (short hash), or "unknown" outside a repository."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_parquet(df: pd.DataFrame, path: Path, meta: dict[str, str]) -> None:
    """Write a tidy frame to parquet with config hash, commit etc. in the file metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    existing = table.schema.metadata or {}
    table = table.replace_schema_metadata(
        {**existing, **{f"sofa.{k}".encode(): str(v).encode() for k, v in meta.items()}}
    )
    pq.write_table(table, path)


def years_to_tolerance(errors: np.ndarray, tol: float) -> int:
    """First year (1-based) from which the error stays below ``tol``."""
    above = np.nonzero(errors >= tol)[0]
    return 1 if above.size == 0 else int(above[-1]) + 2


# --- E0: verification of §2.3 -----------------------------------------------------------
def _e0_seed(cfg: dict[str, Any], seed: int) -> tuple[list[dict], list[dict]]:
    """All E0 checks for one seed. Returns (check rows, premium rows)."""
    p: Params = cfg["base"]
    N, B, d = p.N, p.B, int(cfg["d"])
    rngs = RNGStreams(seed)
    W = random_sparse_W(N, d, rngs.get("verification", "W"))
    checks: list[dict] = []

    def check(name: str, section: str, analytic: float, simulated: float, tol: float, **kw):
        err = abs(simulated - analytic)
        checks.append(
            dict(
                seed=seed,
                check=name,
                section=section,
                analytic=analytic,
                simulated=simulated,
                abs_error=err,
                tolerance=tol,
                passed=err <= tol,
                **kw,
            )
        )

    # §2.3.1 iteration vs closed form; years to reach 1e-6 (no pool) and with a heavy pool
    for alpha in cfg["alphas"]:
        R_star, _ = steady_state(W, alpha, B)
        T = int(np.ceil(np.log(1e-14) / np.log(alpha))) + 5
        states = iterate_fixed_W(W, alpha, B, T)
        err = np.array([np.abs(s.R - R_star).max() for s in states])
        check(
            "iteration_vs_closed_form",
            "2.3.1",
            0.0,
            float(err[-1]),
            1e-10,
            alpha=alpha,
            years=T,
            years_to_1e6=years_to_tolerance(err / B, 1e-6),
            predicted_years_to_1e6=float(np.log(1e-6) / np.log(alpha)),
        )
        # pool lag (§2.2/§4.7): a cap below 1/d forces most donations through the pool
        Wp = cap_project(W, 0.5 / d).W
        Rp, _ = steady_state(Wp, alpha, B)
        Tp = int(np.ceil(np.log(1e-14) / np.log(np.sqrt(alpha)))) + 5
        sp = iterate_fixed_W(Wp, alpha, B, Tp)
        errp = np.array([np.abs(s.R - Rp).max() for s in sp])
        check(
            "iteration_vs_closed_form_heavy_pool",
            "2.3.1",
            0.0,
            float(errp[-1]),
            1e-10,
            alpha=alpha,
            years=Tp,
            years_to_1e6=years_to_tolerance(errp / B, 1e-6),
            predicted_years_to_1e6=float(np.log(1e-6) / np.log(alpha)),
            pool_share=float(sp[-1].pool / (alpha * sp[-1].R.sum())),
        )

    # §2.3.2 conservation
    for alpha in (0.5, 0.9):
        _, K = steady_state(W, alpha, B)
        check("conservation", "2.3.2", N * B, float(K.sum()), 1e-10 * N, alpha=alpha)
        _, Kp = steady_state(cap_project(W, 0.5 / d).W, alpha, B)
        check("conservation_with_pool", "2.3.2", N * B, float(Kp.sum()), 1e-10 * N, alpha=alpha)

    # §2.3.3 degenerate cases
    _, K = steady_state(W, 0.0, B)
    check("alpha_zero_equal_split", "2.3.3", B, float(np.abs(K - B).max() + B), 1e-10)
    U = np.full((N, N), 1.0 / (N - 1))
    np.fill_diagonal(U, 0.0)
    _, K = steady_state(U, 0.8, B)
    check("uniform_W_equal_split", "2.3.3", B, float(np.abs(K - B).max() + B), 1e-10)

    # §2.3.4 group balance identity (worst over random subsets)
    alpha = p.alpha
    R, K = steady_state(W, alpha, B)
    F = flows_at_steady_state(W, alpha, R)
    gr = rngs.get("verification", "subsets")
    worst = 0.0
    for size in (1, 5, 20, 100, 200):
        for _ in range(5):
            C = gr.choice(N, size=size, replace=False)
            inflow, outflow = metrics.group_flows(F, C)
            worst = max(worst, abs(K[C].sum() - (size * B + inflow - outflow)))
    check("group_balance_identity", "2.3.4", 0.0, worst, 1e-10 * N, alpha=alpha)

    # §2.3.5–6 cartel premium over the E2 grid; exact form; ring mutual flow
    premiums: list[dict] = []
    cr = rngs.get("strategy", "cartels")
    members_by_k = {k: choose_members(N, k, cr) for k in cfg["ks"]}
    worst_exact = 0.0
    for alpha in cfg["alphas"]:
        R0, K0 = steady_state(W, alpha, B)  # CRN counterfactual: same W, no cartel
        F0 = flows_at_steady_state(W, alpha, R0)
        for k, C in members_by_k.items():
            I_C0, _ = metrics.group_flows(F0, C)
            for topology in cfg["topologies"]:
                for phi in cfg["phis"]:
                    Wc = cartel_rows(W, C, phi, topology)
                    Rc, Kc = steady_state(Wc, alpha, B)
                    Fc = flows_at_steady_state(Wc, alpha, Rc)
                    I_C, _ = metrics.group_flows(Fc, C)
                    exact = (1 - alpha) * (k * B + I_C) / (1 - alpha * phi)
                    worst_exact = max(worst_exact, abs(Kc[C].sum() - exact))
                    P = metrics.cartel_premium(Kc, K0, C)
                    bound = metrics.premium_bound(alpha, phi)
                    premiums.append(
                        dict(
                            seed=seed,
                            N=N,
                            alpha=alpha,
                            k=k,
                            phi=phi,
                            topology=topology,
                            premium=P,
                            bound=bound,
                            shortfall=1 - P / bound,
                            mutual_flow_in_cartel=metrics.mutual_flow(Fc, C),
                            reciprocity_in_cartel=metrics.reciprocity_index(Fc, C),
                            cycle_return_mean=float(cycle_return_shares(Wc, alpha, p.L)[C].mean()),
                            inflow_change=I_C / I_C0 - 1,
                            outsider_K_change=float((Kc - K0).sum() - (Kc - K0)[C].sum()),
                        )
                    )
    check("cartel_exact_form", "2.3.5", 0.0, worst_exact, 1e-10)
    pdf = pd.DataFrame(premiums)
    check(
        "premium_never_exceeds_bound",
        "2.3.5",
        0.0,
        float(max(0.0, (pdf.premium - pdf.bound).max())),
        1e-9,
    )
    ring = pdf[(pdf.topology == "ring") & (pdf.phi == 1.0) & (pdf.k > 2)]
    check("ring_zero_mutual_flow", "2.3.6", 0.0, float(ring.mutual_flow_in_cartel.max()), 0.0)
    a5 = pdf[(pdf.alpha == 0.5) & (pdf.phi == 1.0) & (pdf.k == 5)].set_index("topology")
    check(
        "ring_vs_clique_premium",
        "2.3.6",
        float(a5.loc["clique", "premium"]),
        float(a5.loc["ring", "premium"]),
        0.05 * float(a5.loc["clique", "premium"]),
    )

    # §2.3.7 cap bound
    ca, ck = float(cfg["cap_alpha"]), int(cfg["cap_k"])
    C = members_by_k[ck] if ck in members_by_k else choose_members(N, ck, cr)
    phi_max_of = {c: min(1.0, (ck - 1) * c) for c in cfg["caps"]}
    for c in cfg["caps"]:
        _, K0c = steady_state(cap_project(W, c).W, ca, B)
        for topology in ("clique", "ring"):
            for phi in (0.5, 1.0):
                capped = cap_project(cartel_rows(W, C, phi, topology), c)
                _, Kc = steady_state(capped.W, ca, B)
                P = metrics.cartel_premium(Kc, K0c, C)
                strict = metrics.premium_bound(ca, phi_max_of[c])
                leaks = bool(capped.excess[C].max() > 1e-12)  # members' excess → pool
                extra = dict(
                    alpha=ca,
                    k=ck,
                    cap=c,
                    phi=phi,
                    topology=topology,
                    member_pool_leak=float(capped.excess[C].mean()),
                )
                if leaks:
                    # Excess routed to the pool: members recapture a share k/N of it, a
                    # return channel §2.3.7 omits. Report the strict and amended bounds.
                    amended = metrics.premium_bound_pool_recapture(ca, phi_max_of[c], ck, N)
                    bounds = (
                        ("cap_bounds_premium_pool_leak_strict", strict),
                        ("cap_bounds_premium_pool_leak_amended", amended),
                    )
                else:
                    bounds = (("cap_bounds_premium", strict),)
                for name, bound in bounds:
                    checks.append(
                        dict(
                            seed=seed,
                            check=name,
                            section="2.3.7",
                            analytic=bound,
                            simulated=P,
                            abs_error=max(0.0, P - bound),
                            tolerance=1e-9,
                            passed=bound + 1e-9 >= P,
                            **extra,
                        )
                    )

    # §2.3.8 oracle optimality: random budget-preserving perturbations never raise Y
    theta = float(cfg["theta"])
    q = rngs.get("verification", "quality").lognormal(0.0, p.sigma_q, N)
    q /= q.mean()
    K1 = metrics.oracle_allocation(q, theta, B)
    Y1 = metrics.expected_output(K1, q, theta, B)
    pr = rngs.get("verification", "perturb")
    gain = -np.inf
    for _ in range(500):
        z = pr.normal(size=N)
        z -= z.mean()
        Kp = K1 + pr.uniform(0.001, 0.5) * K1.min() / np.abs(z).max() * z
        gain = max(gain, metrics.expected_output(Kp, q, theta, B) - Y1)
    check(
        "oracle_max_perturbation_gain", "2.3.8", 0.0, max(0.0, gain), 1e-12, worst_gain=float(gain)
    )
    check("efficiency_oracle_is_one", "6", 1.0, metrics.efficiency(K1, q, theta, B), 1e-12)
    check(
        "efficiency_equal_split_is_zero",
        "6",
        0.0,
        metrics.efficiency(np.full(N, B), q, theta, B),
        1e-12,
    )
    return checks, premiums


def _e0_shortfall_vs_N(cfg: dict[str, Any], seed: int) -> list[dict]:
    """§10: mean shortfall for k = 5, α = 0.8, φ = 1 at several N (clique)."""
    rows = []
    for N in cfg["shortfall_Ns"]:
        rngs = RNGStreams(seed)
        W = random_sparse_W(N, int(cfg["d"]), rngs.get("verification", "W", N))
        C = choose_members(N, 5, rngs.get("strategy", "cartels", N))
        _, K0 = steady_state(W, 0.8, 1.0)
        _, K1 = steady_state(cartel_rows(W, C, 1.0, "clique"), 0.8, 1.0)
        P = metrics.cartel_premium(K1, K0, C)
        rows.append(
            dict(
                seed=seed,
                N=N,
                alpha=0.8,
                k=5,
                phi=1.0,
                premium=P,
                shortfall=1 - P / metrics.premium_bound(0.8, 1.0),
            )
        )
    return rows


def run_e0(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E0 over ``seeds`` seeds and write parquet tables to ``out/E0``."""
    t0 = time.perf_counter()
    res = map_seeds(_e0_seed, cfg, seeds, n_jobs)
    sf = map_seeds(_e0_shortfall_vs_N, cfg, seeds, n_jobs)
    checks = pd.DataFrame([r for c, _ in res for r in c])
    prem = pd.DataFrame([r for _, pr in res for r in pr])
    short = pd.DataFrame([r for rows in sf for r in rows])
    meta = dict(
        experiment="E0",
        config_hash=cfg["base"].config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        d=cfg["d"],
        runtime_s=f"{time.perf_counter() - t0:.1f}",
    )
    paths = {
        "checks": out / "E0" / "E0_checks.parquet",
        "premium": out / "E0" / "E0_premium.parquet",
        "shortfall_vs_N": out / "E0" / "E0_shortfall_vs_N.parquet",
    }
    write_parquet(checks, paths["checks"], meta)
    write_parquet(prem, paths["premium"], meta)
    write_parquet(short, paths["shortfall_vs_N"], meta)
    return paths


def summarise_e0(out: Path) -> pd.DataFrame:
    """Analytic vs simulated table across seeds (worst case per check)."""
    checks = pd.read_parquet(out / "E0" / "E0_checks.parquet")
    g = checks.groupby(["section", "check"], sort=True)
    return g.agg(
        analytic=("analytic", "mean"),
        simulated=("simulated", "mean"),
        worst_abs_error=("abs_error", "max"),
        tolerance=("tolerance", "max"),
        n=("passed", "size"),
        all_passed=("passed", "all"),
    ).reset_index()


# --- E1: sincere mechanics (§7) ---------------------------------------------------------
def _e1_seed(cfg: dict[str, Any], seed: int) -> list[dict]:
    """All E1 cells for one seed, sharing one world (CRN across the grid).

    W depends on (σ_p, ω) but not on α (no safeguards), so it is built once per
    (σ_p, ω) and the closed-form steady state is solved for each α.
    """
    p: Params = cfg["base"]
    rngs = RNGStreams(seed)
    world = build_world(p, rngs)
    pop = world.pop

    def row(mechanism: str, K: np.ndarray, **cell: float) -> dict:
        out = {"seed": seed, "mechanism": mechanism, **cell}
        out.update(metrics.allocation_metrics(K, pop.q, pop.stage, pop.field, p.theta, p.B, p.G))
        return out

    rows = [
        row("A0", baselines.a0_equal_split(pop, p)),
        row("A1", baselines.a1_oracle(pop, p)),
    ]
    for sigma_p in cfg["sigma_ps"]:
        for omega in cfg["omegas"]:
            pc = baselines.a2_params(p.replace(sigma_p=sigma_p, omega=omega))
            model = SOFAModel(pc, seed=seed, world=world)
            if not model.is_static():  # the closed form is valid only for a fixed W (§2.3)
                raise ValueError("E1 uses the closed form, but this W changes over time")
            W = model.donation_matrix(1)
            for alpha in cfg["alphas"]:
                R, K = steady_state(W, alpha, p.B)
                r = row("A2", K, alpha=alpha, sigma_p=sigma_p, omega=omega)
                r["reciprocity"] = metrics.reciprocity_index(flows_at_steady_state(W, alpha, R))
                rows.append(r)
    return rows


def run_e1(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E1 over ``seeds`` seeds; write one tidy table to ``out/E1``."""
    t0 = time.perf_counter()
    res = map_seeds(_e1_seed, cfg, seeds, n_jobs)
    df = pd.DataFrame([r for rows in res for r in rows])
    p: Params = cfg["base"]
    meta = dict(
        experiment="E1",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
    )
    xcheck = annual_crosscheck(baselines.a2_params(p), 0, build_world(p, RNGStreams(0)))
    meta.update(
        annual_crosscheck="default cell, seed 0", annual_crosscheck_max_rel_diff=f"{xcheck:.3e}"
    )
    path = out / "E1" / "E1_cells.parquet"
    write_parquet(df, path, meta)
    return {"cells": path}


# --- Shared helpers for solved experiments (M2 review decision) -------------------------
def annual_crosscheck(p: Params, seed: int, world: World, roles: Roles | None = None) -> float:
    """Simulate one solved cell in annual mode; return max |K_annual/K_solved − 1|.

    The horizon is long enough for the transient (including the pool lag, rate √α) to
    fall below 1e-12.
    """
    m = SOFAModel(p, seed=seed, world=world, roles=roles)
    K_solved = m.equilibrium()[1]
    rate = np.sqrt(p.alpha) if p.diverts_to_pool() or p.coi else p.alpha
    T = int(np.ceil(np.log(1e-12) / np.log(rate))) + 5
    pa = p.replace(T=T, T_eval=1, flow_mode="annual")
    res = SOFAModel(pa, seed=seed, world=world, roles=roles).run()
    return float(np.abs(res.snapshots[T]["K"] / K_solved - 1.0).max())


def _who_pays_cols(K: np.ndarray, K0: np.ndarray, q: np.ndarray, members) -> dict:
    """ΔK of non-members by quality decile, as columns ``who_pays_d0`` … ``d9`` (§6)."""
    return {f"who_pays_d{i}": float(v) for i, v in enumerate(metrics.who_pays(K, K0, q, members))}


# --- E2: cartels (§7) -------------------------------------------------------------------
def _e2_seed(cfg: dict[str, Any], seed: int) -> list[dict]:
    """All E2 cells for one seed. W is static in every cell, so each is solved.

    Members are drawn per (k, selection) from a fresh ``strategy`` stream, so α, φ and
    topology share the same members (CRN); W does not depend on α, so it is built once
    per (k, selection, topology, φ) and solved for each α.
    """
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(seed))
    pop = world.pop
    W0 = SOFAModel(p, seed=seed, world=world).donation_matrix(1)
    K0 = {a: steady_state(W0, a, p.B)[1] for a in cfg["alphas"]}
    rows = []
    for k in cfg["ks"]:
        for sel in cfg["selections"]:
            pk = p.replace(cartels=True, k=k, cartel_selection=sel)
            roles = assign_roles(pop, pk, RNGStreams(seed))
            C = roles.cartels[0]
            for topo in cfg["topologies"]:
                if topo != "clique" and k == 2:
                    continue  # a ring or star of two is the clique of two
                for phi in cfg["phis"]:
                    model = SOFAModel(
                        pk.replace(topology=topo, phi=phi), seed=seed, world=world, roles=roles
                    )
                    if not model.is_static():
                        raise ValueError("E2 solves cells, but this W changes over time")
                    W = model.donation_matrix(1)
                    for alpha in cfg["alphas"]:
                        _, K = steady_state(W, alpha, p.B)
                        Pi = metrics.cartel_premium(K, K0[alpha], C)
                        bound = metrics.premium_bound(alpha, phi)
                        row = dict(
                            seed=seed,
                            alpha=alpha,
                            k=k,
                            phi=phi,
                            topology=topo,
                            selection=sel,
                            premium=Pi,
                            bound=bound,
                            shortfall=1 - Pi / bound,
                            members_q=float(pop.q[C].mean()),
                            members_K0=float(K0[alpha][C].mean()),
                            outsiders_dK=float((K - K0[alpha]).sum() - (K - K0[alpha])[C].sum()),
                        )
                        row.update(_who_pays_cols(K, K0[alpha], pop.q, C))
                        rows.append(row)
    return rows


def run_e2(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E2; write ``out/E2/E2_cells.parquet`` with the annual cross-check in metadata."""
    t0 = time.perf_counter()
    res = map_seeds(_e2_seed, cfg, seeds, n_jobs)
    df = pd.DataFrame([r for rows in res for r in rows])
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(0))
    pc = p.replace(cartels=True, k=5, phi=1.0, alpha=0.8)
    xcheck = annual_crosscheck(pc, 0, world)
    meta = dict(
        experiment="E2",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
        annual_crosscheck="k=5 clique phi=1 alpha=0.8 seed 0",
        annual_crosscheck_max_rel_diff=f"{xcheck:.3e}",
    )
    path = out / "E2" / "E2_cells.parquet"
    write_parquet(df, path, meta)
    return {"cells": path}


# --- E3: transparency (§7) --------------------------------------------------------------
def e3_params(p: Params, behaviour: str, share: float, regime: str) -> Params:
    """Parameters of one E3 cell: one strategic behaviour at population share ``share``."""
    pc = p.replace(regime=regime)
    if share == 0.0:
        return pc
    if behaviour == "herder":
        return pc.replace(x_herd=share)
    if behaviour == "reciprocator":
        return pc.replace(x_recip=share)
    return pc.replace(cartels=True, x_C=share, k=5, topology="clique", phi=1.0)


def _e3_seed(cfg: dict[str, Any], seed: int) -> list[dict]:
    """All E3 cells for one seed: solved when W is static, simulated otherwise."""
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(seed))
    rows = []
    for behaviour in cfg["behaviours"]:
        for share in cfg["shares"]:
            for regime in cfg["regimes"]:
                model = SOFAModel(e3_params(p, behaviour, share, regime), seed=seed, world=world)
                row = dict(seed=seed, behaviour=behaviour, share=share, regime=regime)
                row.update(evaluate(model))
                rows.append(row)
    return rows


def run_e3(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E3; write ``out/E3/E3_cells.parquet``."""
    t0 = time.perf_counter()
    res = map_seeds(_e3_seed, cfg, seeds, n_jobs)
    df = pd.DataFrame([r for rows in res for r in rows])
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(0))
    xcheck = annual_crosscheck(e3_params(p, "cartel", 0.25, "T0"), 0, world)
    meta = dict(
        experiment="E3",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
        annual_crosscheck="cartel share 0.25, T0, seed 0",
        annual_crosscheck_max_rel_diff=f"{xcheck:.3e}",
    )
    path = out / "E3" / "E3_cells.parquet"
    write_parquet(df, path, meta)
    return {"cells": path}


# --- E4: safeguards (§7) ----------------------------------------------------------------
def _e4_seed(cfg: dict[str, Any], seed: int) -> list[dict]:
    """All E4 cells for one seed (all static, all solved).

    For every safeguard configuration: the all-sincere population (collateral cost,
    pool use) and, per cartel variant, the cartel's premium against the same safeguard
    without the cartel.
    """
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(seed))
    pop = world.pop
    rows = []
    for name, overrides in cfg["safeguards"].items():
        ps = p.replace(**overrides)
        sincere = SOFAModel(ps, seed=seed, world=world)
        st0, _ = sincere.equilibrium_state()  # raises if W were dynamic
        base = dict(seed=seed, safeguard=name, alpha=ps.alpha)
        row = dict(
            base,
            cartel="none",
            premium=np.nan,
            efficiency=metrics.efficiency(st0.K, pop.q, p.theta, p.B),
            gini=metrics.gini(st0.K),
            pool_share=st0.pool / (ps.alpha * st0.R.sum()),
            reciprocity=metrics.reciprocity_index(st0.F),
        )
        rows.append(row)
        for topo, k in cfg["cartels"]:
            pc = ps.replace(cartels=True, k=k, topology=topo, phi=1.0)
            m = SOFAModel(pc, seed=seed, world=world)
            st1, _ = m.equilibrium_state()
            C = m.roles.cartels[0]
            rows.append(
                dict(
                    base,
                    cartel=f"{topo} k={k}",
                    premium=metrics.cartel_premium(st1.K, st0.K, C),
                    efficiency=metrics.efficiency(st1.K, pop.q, p.theta, p.B),
                    gini=metrics.gini(st1.K),
                    pool_share=st1.pool / (pc.alpha * st1.R.sum()),
                    reciprocity=metrics.reciprocity_index(st1.F),
                    mutual_flow_in_cartel=metrics.mutual_flow(st1.F, C),
                )
            )
    return rows


def run_e4(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E4; write ``out/E4/E4_cells.parquet``."""
    t0 = time.perf_counter()
    res = map_seeds(_e4_seed, cfg, seeds, n_jobs)
    df = pd.DataFrame([r for rows in res for r in rows])
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(0))
    pc = p.replace(
        cartels=True, k=5, topology="ring", phi=1.0, coi=True, cap=0.1, delta=1.0, delta_L=1.0, L=5
    )
    xcheck = annual_crosscheck(pc, 0, world)
    meta = dict(
        experiment="E4",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
        annual_crosscheck="ring k=5 under S1+S2(0.1)+S3(1)+S4(L=5), seed 0",
        annual_crosscheck_max_rel_diff=f"{xcheck:.3e}",
    )
    path = out / "E4" / "E4_cells.parquet"
    write_parquet(df, path, meta)
    return {"cells": path}


# --- E5: feedback, equity and mechanism comparison (§7) --------------------------------
def e5_params(p: Params, mechanism: str, b_share: float, **cell: Any) -> Params:
    """One E5 cell. ω is the evaluators' reputation weight for donors and panels alike."""
    omega = cell.pop("omega", p.omega)
    return p.replace(mechanism=mechanism, b_share=b_share, omega=omega, omega_p=omega, **cell)


def _e5_cell(p: Params, seed: int, world: World, keep: list[str]) -> tuple[dict, list[dict]]:
    """Evaluate one cell; return its summary and (for simulated cells) its yearly path.

    Solved cells have no transient: their path is the solved value in every year.
    """
    model = SOFAModel(p, seed=seed, world=world)
    if model.is_static():
        summary = model.solve()
        summary["solved"] = 1.0
        path = [{"year": t, **{k: summary.get(k, np.nan) for k in keep}} for t in range(1, p.T + 1)]
    else:
        res = model.run()
        summary = res.summary()
        summary["solved"] = 0.0
        path = res.yearly[["year", *[k for k in keep if k in res.yearly]]].to_dict("records")
    return summary, path


def _e5_seed(cfg: dict[str, Any], seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    """All E5 cells for one seed: (feedback summaries, trajectories, comparison)."""
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(seed))
    keep = list(cfg["trajectory_metrics"])
    cells, paths, comp = [], [], []

    def add(target: list, label: dict, pc: Params, with_path: bool) -> None:
        summary, path = _e5_cell(pc, seed, world, keep)
        target.append({"seed": seed, **label, **summary})
        if with_path:
            paths.extend({"seed": seed, **label, **r} for r in path)

    for mech, b in cfg["mechanisms"]:
        # Only SOFA uses the awareness network, so r_A is varied for SOFA alone (M4 review)
        r_as = cfg.get("r_As", [0.0]) if mech == "sofa" else [0.0]
        for lam in cfg["lams"]:
            for omega in cfg["omegas"]:
                for turnover in cfg["turnover"]:
                    for r_a in r_as:
                        label = dict(
                            mechanism=mech,
                            b_share=b,
                            lam=lam,
                            omega=omega,
                            turnover=turnover,
                            r_A=r_a,
                            theta=p.theta,
                            sigma_p=p.sigma_p,
                        )
                        pc = e5_params(p, mech, b, lam=lam, omega=omega, turnover=turnover, r_A=r_a)
                        add(cells, label, pc, with_path=True)
        for theta in cfg["theta_sensitivity"]["thetas"]:
            label = dict(
                mechanism=mech,
                b_share=b,
                lam=0.2,
                omega=0.3,
                turnover=False,
                r_A=0.0,
                theta=theta,
                sigma_p=p.sigma_p,
            )
            add(
                cells,
                label,
                e5_params(p, mech, b, lam=0.2, omega=0.3, theta=theta),
                with_path=False,
            )
        sigmas = cfg["comparison"]["sigma_ps"] if mech == "sofa" else [p.sigma_p]
        for omega in cfg["comparison"]["omegas"]:
            for sp in sigmas:
                label = dict(mechanism=mech, b_share=b, omega=omega, sigma_p=sp)
                add(comp, label, e5_params(p, mech, b, omega=omega, sigma_p=sp), with_path=False)
    return cells, paths, comp


def run_e5(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E5; write cells, trajectories and comparison tables to ``out/E5``."""
    t0 = time.perf_counter()
    res = map_seeds(_e5_seed, cfg, seeds, n_jobs)
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(0))
    xcheck = annual_crosscheck(p, 0, world)  # the λ = 0 SOFA cells are solved
    meta = dict(
        experiment="E5",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
        annual_crosscheck="SOFA λ = 0, default cell, seed 0",
        annual_crosscheck_max_rel_diff=f"{xcheck:.3e}",
    )
    paths = {}
    for i, name in enumerate(("cells", "trajectories", "comparison")):
        df = pd.DataFrame([r for parts in res for r in parts[i]])
        paths[name] = out / "E5" / f"E5_{name}.parquet"
        write_parquet(df, paths[name], meta)
    return paths


# --- E6: evolution of strategies (§7) --------------------------------------------------
def e6_cells(cfg: dict[str, Any]) -> list[tuple[dict, dict]]:
    """(label, overrides) for every E6 cell; peer reports only under T3."""
    out = []
    for regime in cfg["regimes"]:
        for audit, overrides in cfg["audits"].items():
            if "p_peer" in overrides and regime != "T3":
                continue
            for c_m in cfg["c_ms"]:
                out.append(
                    (
                        {"regime": regime, "audit": audit, "c_m": c_m},
                        {"regime": regime, "c_m": c_m, **overrides},
                    )
                )
    return out


def _e6_seed(cfg: dict[str, Any], seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    """All E6 cells for one seed: (summaries, trajectories, cartel survival records)."""
    p: Params = cfg["base"]
    world = build_world(p, RNGStreams(seed))
    keep = list(cfg["trajectory_metrics"])
    cells, paths, logs = [], [], []
    for label, overrides in e6_cells(cfg):
        res = SOFAModel(p.replace(**overrides), seed=seed, world=world).run()
        cells.append({"seed": seed, **label, **res.summary()})
        cols = ["year", *[k for k in keep if k in res.yearly]]
        paths.extend({"seed": seed, **label, **r} for r in res.yearly[cols].to_dict("records"))
        logs.extend({"seed": seed, **label, **r} for r in res.cartel_log)
    return cells, paths, logs


def run_e6(cfg: dict[str, Any], seeds: int, out: Path, n_jobs: int = -1) -> dict[str, Path]:
    """Run E6; write cells, trajectories and cartel survival tables to ``out/E6``."""
    t0 = time.perf_counter()
    res = map_seeds(_e6_seed, cfg, seeds, n_jobs)
    p: Params = cfg["base"]
    meta = dict(
        experiment="E6",
        config_hash=p.config_hash(),
        git_commit=git_commit(),
        seeds=seeds,
        N=p.N,
        runtime_s=f"{time.perf_counter() - t0:.1f}",
    )
    paths = {}
    for i, name in enumerate(("cells", "trajectories", "cartels")):
        df = pd.DataFrame([r for parts in res for r in parts[i]])
        paths[name] = out / "E6" / f"E6_{name}.parquet"
        write_parquet(df, paths[name], meta)
    return paths


# --- Registry and CLI -------------------------------------------------------------------
RUNNERS: dict[str, Callable[..., dict[str, Path]]] = {
    "E0": run_e0,
    "E1": run_e1,
    "E2": run_e2,
    "E3": run_e3,
    "E4": run_e4,
    "E5": run_e5,
    "E6": run_e6,
}


def main(argv: list[str] | None = None) -> None:
    """Command-line entry point."""
    ap = argparse.ArgumentParser(prog="python -m sofa.experiments")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run an experiment")
    r.add_argument("experiment", choices=sorted(RUNNERS))
    r.add_argument("--seeds", type=int, default=None)
    r.add_argument("--n", type=int, default=None, help="override N")
    r.add_argument("--out", type=Path, default=Path("results"))
    r.add_argument("--jobs", type=int, default=-1)
    pl = sub.add_parser("plot", help="plot an experiment's results")
    pl.add_argument("experiment", choices=sorted(RUNNERS))
    pl.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args(argv)

    if args.cmd == "run":
        cfg = load_experiment_config(CONFIG_DIR / f"{args.experiment}.yaml")
        if args.n is not None:
            cfg["base"] = cfg["base"].replace(N=args.n)
        seeds = args.seeds or int(cfg.get("seeds", 10))
        paths = RUNNERS[args.experiment](cfg, seeds, args.out, n_jobs=args.jobs)
        for name, path in paths.items():
            print(f"{name}: {path}")
        if args.experiment == "E0":
            with pd.option_context("display.width", 200, "display.max_columns", 20):
                print(summarise_e0(args.out).to_string(index=False))
    else:
        from sofa import plotting

        for path in plotting.PLOTTERS[args.experiment](args.out):
            print(path)


if __name__ == "__main__":
    main()
