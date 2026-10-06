"""Smoke tests: each experiment runner end to end on a tiny grid (structure and routing)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from sofa.config import Params
from sofa.experiments import run_e1, run_e2, run_e3, run_e4

BASE = Params(N=120)


def _meta(path):
    return {
        k.decode(): v.decode()
        for k, v in pq.read_schema(path).metadata.items()
        if k.startswith(b"sofa.")
    }


def test_e1_runner(tmp_path):
    cfg = {
        "base": BASE.replace(flow_mode="equilibrium"),
        "alphas": [0.3, 0.7],
        "sigma_ps": [0.5],
        "omegas": [0.0, 0.3],
    }
    path = run_e1(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert set(df.mechanism) == {"A0", "A1", "A2"} and (df.mechanism == "A2").sum() == 4
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


def test_e2_runner(tmp_path):
    cfg = {
        "base": BASE,
        "alphas": [0.5],
        "ks": [2, 5],
        "phis": [1.0],
        "topologies": ["clique", "ring"],
        "selections": ["random", "high_q"],
    }
    path = run_e2(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert len(df) == 6  # k = 2 has no ring
    assert (df.premium <= df.bound + 1e-9).all() and (df.premium > 1).all()
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


def test_e3_runner_routes_static_and_dynamic(tmp_path):
    cfg = {
        "base": BASE.replace(T=30, T_eval=5),
        "regimes": ["T0", "T2"],
        "behaviours": ["herder", "reciprocator", "cartel"],
        "shares": [0.0, 0.25],
    }
    df = pd.read_parquet(run_e3(cfg, 1, tmp_path, n_jobs=1)["cells"])
    s = df.set_index(["behaviour", "share", "regime"])
    assert s.loc[("herder", 0.25, "T0"), "solved"] == 1.0  # fallback → static
    assert s.loc[("herder", 0.25, "T2"), "solved"] == 0.0  # feasible → simulated
    assert s.loc[("reciprocator", 0.25, "T2"), "solved"] == 0.0
    assert s.loc[("cartel", 0.25, "T2"), "solved"] == 1.0
    assert s.loc[("herder", 0.25, "T0"), "fallbacks"] == 30


def test_e4_runner(tmp_path):
    cfg = {
        "base": BASE,
        "cartels": [["clique", 5], ["ring", 5]],
        "safeguards": {"none": {}, "S3": {"delta": 1.0}, "S2": {"cap": 0.1}},
    }
    path = run_e4(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert len(df) == 9
    ring = df[df.cartel == "ring k=5"].set_index("safeguard")
    assert ring.loc["none", "mutual_flow_in_cartel"] == 0.0
    assert np.isfinite(df.efficiency).all()
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


@pytest.mark.parametrize("name", ["E1", "E2", "E3", "E4"])
def test_configs_load(name):
    from sofa.config import load_experiment_config
    from sofa.experiments import CONFIG_DIR

    cfg = load_experiment_config(CONFIG_DIR / f"{name}.yaml")
    assert isinstance(cfg["base"], Params)


def test_e5_runner(tmp_path):
    from sofa.experiments import run_e5

    cfg = {
        "base": BASE.replace(T=20, T_eval=4),
        "mechanisms": [["sofa", 0.0], ["panel", 0.5], ["equal", 0.0]],
        "lams": [0.0, 0.3],
        "omegas": [0.3],
        "turnover": [False],
        "theta_sensitivity": {"thetas": [0.8]},
        "comparison": {"omegas": [0.0], "sigma_ps": [0.5, 1.0]},
        "trajectory_metrics": ["gini", "early_ratio"],
    }
    paths = run_e5(cfg, 1, tmp_path, n_jobs=1)
    cells = pd.read_parquet(paths["cells"])
    traj = pd.read_parquet(paths["trajectories"])
    comp = pd.read_parquet(paths["comparison"])
    assert len(cells) == 3 * (2 + 1)
    s = cells.set_index(["mechanism", "lam", "theta"])
    assert s.loc[("sofa", 0.0, 0.5), "solved"] == 1.0
    assert s.loc[("sofa", 0.3, 0.5), "solved"] == 0.0
    assert s.loc[("panel", 0.0, 0.5), "solved"] == 0.0
    assert len(traj) == 3 * 2 * 20
    assert len(comp) == 2 + 1 + 1  # SOFA over two σ_p, one cell each for the others
    assert float(_meta(paths["cells"])["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9
    assert (cells.total_K - 120).abs().max() < 1e-3  # short T: SOFA transient α^(t+1) remains


def test_e6_runner(tmp_path):
    from sofa.experiments import run_e6

    cfg = {
        "base": BASE.replace(
            T=12, T_eval=4, adaptation=True, cartels=True, x_C=0.05, x_herd=0.05, x_best=0.05
        ),
        "regimes": ["T0", "T3"],
        "audits": {
            "none": {},
            "S5 audit": {"p_audit": 1.0},
            "T3 peer reports": {"p_peer": 0.5},
        },
        "c_ms": [0.05],
        "trajectory_metrics": ["share_sincere", "share_cartel", "n_cartels"],
    }
    paths = run_e6(cfg, 1, tmp_path, n_jobs=1)
    cells = pd.read_parquet(paths["cells"])
    traj = pd.read_parquet(paths["trajectories"])
    logs = pd.read_parquet(paths["cartels"])
    assert len(cells) == 2 * 2 + 1  # peer reports only under T3
    assert set(cells[cells.audit == "T3 peer reports"].regime) == {"T3"}
    assert len(traj) == len(cells) * 12
    assert {"founded", "ended", "censored"} <= set(logs.columns)


def test_e7_runner(tmp_path):
    """Every block runs; designs are reproducible; the PRCC table covers every outcome."""
    from sofa.config import load_experiment_config
    from sofa.experiments import CONFIG_DIR, e7_block, run_e7

    cfg = load_experiment_config(CONFIG_DIR / "E7.yaml")
    cfg["base"] = cfg["base"].replace(N=120, T=25, T_eval=3)
    for block in cfg["blocks"].values():
        block["factors"].pop("N", None)  # keep the smoke test small
        block["factors"]["alpha"] = [0.2, 0.6]  # short horizon: T − T_eval ≥ 10/(−ln α)
        block["base"].update(T=25, T_eval=3)
    cfg["samples"] = 30
    a, b = e7_block(cfg, "evolution"), e7_block(cfg, "evolution")
    assert a["design"].equals(b["design"])
    paths = run_e7(cfg, 30, tmp_path, n_jobs=1)
    prcc = pd.read_parquet(paths["prcc"])
    for name, spec in cfg["blocks"].items():
        df = pd.read_parquet(paths[name])
        assert len(df) == 30 and (df.seed == df["sample"]).all()
        got = prcc[prcc.block == name]
        assert set(got.outcome) == set(spec["outcomes"])
        assert set(got.factor) == set(spec["factors"])
    sg = pd.read_parquet(paths["safeguards"])
    assert np.isfinite(sg[cfg["blocks"]["safeguards"]["outcomes"]].to_numpy(float)).all()
    meta = pq.read_schema(paths["safeguards"]).metadata
    assert float(meta[b"sofa.annual_crosscheck_max_rel_diff"]) < 1e-9
