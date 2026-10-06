"""Analytic tests (§10): static W, N = 400, tolerance 1e-10 unless stated otherwise."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import N_REF, make_W, years_to_converge
from sofa.flows import (
    flows_at_steady_state,
    iterate_fixed_W,
    steady_state,
)
from sofa.metrics import (
    cartel_premium,
    efficiency,
    expected_output,
    group_flows,
    mutual_flow,
    oracle_allocation,
    premium_bound,
    premium_bound_pool_recapture,
)
from sofa.safeguards import cap_project
from sofa.strategies import cartel_rows, choose_members

B = 1.0
TOL = 1e-10


def premium(W: np.ndarray, members: np.ndarray, alpha: float, phi: float, topology: str) -> float:
    _, K0 = steady_state(W, alpha, B)
    _, K1 = steady_state(cartel_rows(W, members, phi, topology), alpha, B)
    return cartel_premium(K1, K0, members)


# --- §2.3.1 ---------------------------------------------------------------------------
@pytest.mark.parametrize("alpha", [0.2, 0.5, 0.8])
def test_iteration_matches_closed_form(W400, alpha):
    R_star, K_star = steady_state(W400, alpha, B)
    np.testing.assert_allclose(
        R_star,
        B * np.linalg.solve(np.eye(N_REF) - alpha * W400.T, np.ones(N_REF)),
        rtol=0,
        atol=TOL,
    )
    last = iterate_fixed_W(W400, alpha, B, years_to_converge(alpha))[-1]
    np.testing.assert_allclose(last.R, R_star, rtol=0, atol=TOL)
    np.testing.assert_allclose(last.K, K_star, rtol=0, atol=TOL)


def test_convergence_rate_is_alpha(W400):
    """The transient shrinks geometrically at rate α (§2.3.1)."""
    alpha = 0.6
    R_star, _ = steady_state(W400, alpha, B)
    states = iterate_fixed_W(W400, alpha, B, 30)
    err = np.array([np.abs(s.R - R_star).sum() for s in states])
    # with row-stochastic W, Σ|R(t) − R*| contracts by exactly α per year in the L1 norm
    ratios = err[5:20] / err[4:19]
    assert np.all(ratios <= alpha + 1e-9)


# --- §2.3.2 ---------------------------------------------------------------------------
@pytest.mark.parametrize("alpha", [0.1, 0.5, 0.9])
def test_conservation(W400, alpha):
    _, K = steady_state(W400, alpha, B)
    assert abs(K.sum() - N_REF * B) < TOL * N_REF


@pytest.mark.parametrize("c", [0.01, 0.02])  # below 1/d, so rows leak to the pool
def test_conservation_with_pool(W400, c):
    """Rows that cannot place everything leak to the pool; Σ K* = N·B still (§2.3.2)."""
    alpha = 0.7
    capped = cap_project(W400, c)
    assert capped.excess.max() > 0  # the pool is actually used
    R, K = steady_state(capped.W, alpha, B)
    assert abs(K.sum() - N_REF * B) < TOL * N_REF
    last = iterate_fixed_W(capped.W, alpha, B, years_to_converge(alpha, pool=True))[-1]
    np.testing.assert_allclose(last.K, K, rtol=0, atol=TOL)
    # steady pool equals the unplaced donations
    assert abs(last.pool - float(alpha * R @ (1 - capped.W.sum(axis=1)))) < TOL * N_REF


def test_conservation_with_flow_level_leak(W400):
    """A generic flow-level safeguard diverting money to the pool conserves Σ K* (§4.6)."""

    class HalveMutual:
        def apply_flow_level(self, F, W):
            m = np.minimum(F, F.T)
            return F - 0.5 * m, float(0.5 * m.sum())

    alpha = 0.6
    last = iterate_fixed_W(W400, alpha, B, years_to_converge(alpha, pool=True), sg=HalveMutual())[
        -1
    ]
    assert last.pool > 0
    assert abs(last.K.sum() - N_REF * B) < TOL * N_REF


# --- §2.3.3 ---------------------------------------------------------------------------
def test_alpha_zero_is_equal_split(W400):
    _, K = steady_state(W400, 0.0, B)
    np.testing.assert_allclose(K, B, rtol=0, atol=TOL)
    np.testing.assert_allclose(iterate_fixed_W(W400, 0.0, B, 3)[-1].K, B, rtol=0, atol=TOL)


@pytest.mark.parametrize("alpha", [0.3, 0.9])
def test_uniform_W_is_equal_split(alpha):
    W = np.full((N_REF, N_REF), 1.0 / (N_REF - 1))
    np.fill_diagonal(W, 0.0)
    _, K = steady_state(W, alpha, B)
    np.testing.assert_allclose(K, B, rtol=0, atol=TOL)


# --- §2.3.4 ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed", range(5))
def test_group_balance_identity(W400, seed):
    alpha = 0.65
    rng = np.random.default_rng(seed)
    R, K = steady_state(W400, alpha, B)
    F = flows_at_steady_state(W400, alpha, R)
    for size in (1, 7, 50, 200):
        C = rng.choice(N_REF, size=size, replace=False)
        inflow, outflow = group_flows(F, C)
        assert abs(K[C].sum() - (size * B + inflow - outflow)) < TOL * N_REF


def test_group_balance_identity_with_pool():
    """With a pool, each member also receives pool/N (§2.2)."""
    alpha, W = 0.5, cap_project(make_W(3), 0.08).W
    states = iterate_fixed_W(W, alpha, B, years_to_converge(alpha, pool=True))
    prev, last = states[-2], states[-1]
    C = np.arange(0, N_REF, 9)
    inflow, outflow = group_flows(last.F, C)
    expected = len(C) * (B + prev.pool / N_REF) + inflow - outflow
    assert abs(last.K[C].sum() - expected) < TOL * N_REF


# --- §2.3.5 ---------------------------------------------------------------------------
@pytest.mark.parametrize("topology", ["clique", "ring", "star"])
@pytest.mark.parametrize(("alpha", "phi", "k"), [(0.5, 1.0, 5), (0.8, 0.5, 10), (0.3, 0.25, 2)])
def test_cartel_exact_form(W400, topology, alpha, phi, k):
    if topology != "clique" and k == 2:
        k = 3
    C = choose_members(N_REF, k, np.random.default_rng(k))
    Wc = cartel_rows(W400, C, phi, topology)
    R, K = steady_state(Wc, alpha, B)
    I_C, _ = group_flows(flows_at_steady_state(Wc, alpha, R), C)
    assert abs(K[C].sum() - (1 - alpha) * (k * B + I_C) / (1 - alpha * phi)) < TOL


def test_cartel_premium_analytic():
    """Clique, k = 2, φ = 1, α = 0.5: Π within 1 % of 2.0 (seed average; §10)."""
    Ps = []
    for seed in range(10):
        rng = np.random.default_rng(seed)
        W = make_W(seed)
        Ps.append(premium(W, choose_members(N_REF, 2, rng), 0.5, 1.0, "clique"))
    assert abs(np.mean(Ps) - 2.0) / 2.0 < 0.01
    assert max(Ps) <= 2.0 + 1e-9


@pytest.mark.parametrize("alpha", [0.2, 0.35, 0.5, 0.65, 0.8, 0.9])
@pytest.mark.parametrize("topology", ["clique", "ring", "star"])
def test_cartel_premium_never_exceeds_bound(W400, alpha, topology):
    """Across the E2 grid, Π ≤ 1/(1 − αφ) + 1e-9 (§10)."""
    for k in (2, 3, 5, 10, 20):
        C = choose_members(N_REF, k, np.random.default_rng(100 + k))
        for phi in (0.25, 0.5, 0.75, 1.0):
            P = premium(W400, C, alpha, phi, topology)
            assert premium_bound(alpha, phi) + 1e-9 >= P
            assert P > 1.0


def test_cartel_shortfall_shrinks_with_N():
    """K = 5, α = 0.8: the mean relative shortfall falls monotonically for N = 200 → 800 (§10)."""
    alpha, k, bound = 0.8, 5, premium_bound(0.8, 1.0)
    shortfalls = []
    for N in (200, 400, 800):
        Ps = []
        for seed in range(8):
            rng = np.random.default_rng(seed)
            W = make_W(seed, N=N)
            Ps.append(premium(W, choose_members(N, k, rng), alpha, 1.0, "clique"))
        shortfalls.append(1 - np.mean(Ps) / bound)
    assert shortfalls[0] > shortfalls[1] > shortfalls[2] > 0


# --- §2.3.6 ---------------------------------------------------------------------------
def test_ring_zero_mutual_flow_same_premium():
    alpha, k = 0.5, 5
    rel = []
    for seed in range(5):
        W = make_W(seed)
        C = choose_members(N_REF, k, np.random.default_rng(seed))
        Wr = cartel_rows(W, C, 1.0, "ring")
        R, _ = steady_state(Wr, alpha, B)
        assert mutual_flow(flows_at_steady_state(Wr, alpha, R), C) == 0.0
        Pr, Pc = premium(W, C, alpha, 1.0, "ring"), premium(W, C, alpha, 1.0, "clique")
        rel.append(abs(Pr - Pc) / Pc)
    assert max(rel) < 0.05


def test_clique_has_positive_mutual_flow(W400):
    alpha, C = 0.5, choose_members(N_REF, 5, np.random.default_rng(1))
    Wc = cartel_rows(W400, C, 1.0, "clique")
    R, _ = steady_state(Wc, alpha, B)
    assert mutual_flow(flows_at_steady_state(Wc, alpha, R), C) > 0


# --- §2.3.7 ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("c", [0.05, 0.1, 0.2, 0.5])
@pytest.mark.parametrize("topology", ["clique", "ring"])
def test_cap_bounds_premium(seed, c, topology):
    """Π ≤ 1/(1 − α·min(1, (k−1)c)) when the capped excess is placed outside the cartel."""
    alpha, k, phi = 0.8, 5, 0.5
    W = make_W(seed)
    C = choose_members(N_REF, k, np.random.default_rng(seed))
    capped = cap_project(cartel_rows(W, C, phi, topology), c)
    assert capped.excess[C].max() < 1e-12  # no pool leak: the strict bound applies
    _, K0 = steady_state(cap_project(W, c).W, alpha, B)
    _, K1 = steady_state(capped.W, alpha, B)
    phi_max = min(1.0, (k - 1) * c)
    assert cartel_premium(K1, K0, C) <= premium_bound(alpha, phi_max) + 1e-9


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("c", [0.05, 0.1])
def test_cap_bound_with_pool_leak(seed, c):
    """φ = 1 clique: capped excess goes to the pool and members recapture k/N of it.

    The strict §2.3.7 bound can be exceeded (by < 1 % here); the amended bound with
    φ′ = φ_max + (1 − φ_max)k/N holds. Proposed amendment, see reports/M1.md.
    """
    alpha, k = 0.8, 5
    W = make_W(seed)
    C = choose_members(N_REF, k, np.random.default_rng(seed))
    capped = cap_project(cartel_rows(W, C, 1.0, "clique"), c)
    assert capped.excess[C].min() > 0
    _, K0 = steady_state(cap_project(W, c).W, alpha, B)
    _, K1 = steady_state(capped.W, alpha, B)
    P = cartel_premium(K1, K0, C)
    phi_max = min(1.0, (k - 1) * c)
    assert premium_bound(alpha, phi_max) * 1.01 >= P
    assert premium_bound_pool_recapture(alpha, phi_max, k, N_REF) + 1e-9 >= P


# --- §2.3.8 ---------------------------------------------------------------------------
@pytest.mark.parametrize("theta", [0.2, 0.5, 0.9])
def test_oracle_optimal(theta):
    rng = np.random.default_rng(int(theta * 10))
    q = rng.lognormal(0, 0.5, N_REF)
    q /= q.mean()
    K1 = oracle_allocation(q, theta, B)
    assert abs(K1.sum() - N_REF * B) < TOL * N_REF
    Y1 = expected_output(K1, q, theta, B)
    for _ in range(200):
        # budget-preserving perturbation that keeps K ≥ 0
        z = rng.normal(size=N_REF)
        z -= z.mean()
        step = rng.uniform(0.001, 0.5) * K1.min() / np.abs(z).max()
        assert expected_output(K1 + step * z, q, theta, B) <= Y1 + 1e-12
    assert abs(efficiency(K1, q, theta, B) - 1.0) < 1e-12
