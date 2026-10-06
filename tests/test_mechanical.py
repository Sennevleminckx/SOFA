"""Mechanical tests (§10) for the Milestone 1 components."""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from conftest import make_W, years_to_converge
from sofa.config import HorizonWarning, Params
from sofa.flows import (
    cycle_return_shares,
    flow_step,
    iterate_fixed_W,
    return_multipliers,
    steady_state,
)
from sofa.metrics import (
    efficiency,
    gini,
    lorenz,
    oracle_allocation,
    reciprocity_index,
    top_share,
    who_pays,
)
from sofa.rng import RNGStreams
from sofa.safeguards import cap_project
from sofa.strategies import cartel_rows, internal_rows, random_sparse_W


# --- Cap projection (S2) ----------------------------------------------------------------
@pytest.mark.parametrize("c", [0.03, 0.1, 0.25, 0.6])
def test_cap_projection_properties(c):
    rng = np.random.default_rng(0)
    W = random_sparse_W(60, 12, rng) ** 3  # skewed rows
    W /= W.sum(axis=1, keepdims=True)
    res = cap_project(W, c)
    P = res.W
    assert P.max() <= c + 1e-12
    assert np.all(P.sum(axis=1) <= W.sum(axis=1) + 1e-12)
    np.testing.assert_allclose(P.sum(axis=1) + res.excess, W.sum(axis=1), atol=1e-12)
    # no new recipients; weak order preserved within each row
    assert np.all((P > 0) <= (W > 0))
    for i in range(W.shape[0]):
        a, b = W[i], P[i]
        order = np.argsort(a)
        assert np.all(np.diff(b[order]) >= -1e-12)
    # idempotent
    np.testing.assert_allclose(cap_project(P, c).W, P, atol=1e-15)
    # rows with at least ⌈1/c⌉ recipients place everything
    full = (W > 0).sum(axis=1) * c >= 1.0 - 1e-12
    np.testing.assert_allclose(res.excess[full], 0.0, atol=1e-12)


def test_cap_one_is_switched_off(W400):
    res = cap_project(W400, 1.0)
    assert np.array_equal(res.W, W400)
    assert np.all(res.excess == 0)


def test_cap_clique_internal_share():
    """φ = 1 clique under cap c routes exactly (k − 1)c internally (§2.3.7)."""
    W = make_W(0, N=50, d=10)
    C = [3, 10, 20, 30, 40]
    for c in (0.1, 0.2):
        P = cap_project(cartel_rows(W, C, 1.0, "clique"), c).W
        inside = P[np.ix_(C, C)].sum(axis=1)
        np.testing.assert_allclose(inside, min(1.0, (len(C) - 1) * c), atol=1e-12)


# --- Cartel rows ------------------------------------------------------------------------
@pytest.mark.parametrize("topology", ["clique", "ring", "star"])
def test_cartel_rows_internal_share_exact(topology):
    W = make_W(1, N=80, d=15)
    C = [0, 5, 9, 33]
    # make sincere rows point at fellow members to check they are excluded
    W[0, 5] += 1.0
    W /= W.sum(axis=1, keepdims=True)
    for phi in (0.0, 0.3, 1.0):
        Wc = cartel_rows(W, C, phi, topology)
        np.testing.assert_allclose(Wc[np.ix_(C, C)].sum(axis=1), phi, atol=1e-14)
        np.testing.assert_allclose(Wc.sum(axis=1), 1.0, atol=1e-14)
        assert np.all(np.diag(Wc) == 0)
        others = np.setdiff1d(np.arange(80), C)
        assert np.array_equal(Wc[others], W[others])


def test_internal_rows_topologies():
    I_ring = internal_rows([2, 4, 6], 8, "ring")
    assert I_ring[0, 4] == I_ring[1, 6] == I_ring[2, 2] == 1.0
    I_star = internal_rows([2, 4, 6], 8, "star")
    assert I_star[0, 4] == I_star[0, 6] == 0.5
    assert I_star[1, 2] == I_star[2, 2] == 1.0
    with pytest.raises(ValueError):
        internal_rows([1], 8, "clique")


# --- Flows ------------------------------------------------------------------------------
def test_return_multipliers_match_finite_difference():
    W, alpha = make_W(4, N=60, d=8), 0.7
    G = return_multipliers(W, alpha)
    R0, _ = steady_state(W, alpha, 1.0)
    j = 17
    extra = np.zeros(60)
    extra[j] = 1.0
    R1 = np.linalg.solve(np.eye(60) - alpha * W.T, np.ones(60) + extra)
    np.testing.assert_allclose(R1 - R0, G[:, j], atol=1e-12)


def test_cycle_return_shares_ring():
    """A pure ring of length k returns α^{k−1} after k hops; nothing earlier (§4.6 S4)."""
    k, alpha = 3, 0.5
    W = internal_rows(list(range(k)), k, "ring")
    np.testing.assert_allclose(cycle_return_shares(W, alpha, L=3), alpha**2)
    np.testing.assert_allclose(cycle_return_shares(W, alpha, L=2), 0.0)
    pair = internal_rows([0, 1], 2, "clique")
    np.testing.assert_allclose(cycle_return_shares(pair, alpha, L=3), alpha)


def test_empty_row_goes_to_pool():
    W = make_W(2, N=30, d=5)
    W[4] = 0.0
    st_ = flow_step(np.full(30, 1.0), W, 0.5, 1.0)
    assert st_.pool == pytest.approx(0.5)
    _, K = steady_state(W, 0.5, 1.0)
    assert K.sum() == pytest.approx(30.0, abs=1e-10)


# --- Property-based conservation -------------------------------------------------------
@settings(max_examples=60, deadline=None)
@given(
    seed=st.integers(0, 10_000),
    N=st.integers(5, 40),
    alpha=st.floats(0.0, 0.95),
    c=st.floats(0.05, 1.0),
    zero_rows=st.integers(0, 3),
)
def test_conservation_property(seed, N, alpha, c, zero_rows):
    rng = np.random.default_rng(seed)
    d = int(rng.integers(1, N))
    W = cap_project(random_sparse_W(N, d, rng), c).W
    W[rng.choice(N, size=min(zero_rows, N - 1), replace=False)] = 0.0
    _, K = steady_state(W, alpha, 1.0)
    assert np.all(K >= 0)
    assert K.sum() == pytest.approx(N, rel=1e-9)
    T = years_to_converge(alpha, tol=1e-13, pool=True)
    last = iterate_fixed_W(W, alpha, 1.0, T)[-1]
    np.testing.assert_allclose(last.K, K, rtol=1e-8, atol=1e-9)


# --- Metrics ----------------------------------------------------------------------------
def test_gini_known_vectors():
    assert gini(np.ones(10)) == 0.0
    assert gini(np.array([0, 0, 0, 1.0])) == pytest.approx(0.75)
    assert gini(np.array([1.0, 2, 3, 4])) == pytest.approx(0.25)
    assert gini(np.zeros(5)) == 0.0


def test_top_share_and_lorenz():
    x = np.arange(1, 11, dtype=float)
    assert top_share(x, 0.1) == pytest.approx(10 / 55)
    pop, cum = lorenz(x)
    assert pop[0] == cum[0] == 0.0
    assert pop[-1] == cum[-1] == pytest.approx(1.0)
    assert np.all(cum <= pop + 1e-12)


def test_efficiency_endpoints():
    rng = np.random.default_rng(0)
    q = rng.lognormal(0, 0.5, 100)
    assert efficiency(np.ones(100), q, 0.5, 1.0) == pytest.approx(0.0, abs=1e-12)
    assert efficiency(oracle_allocation(q, 0.5, 1.0), q, 0.5, 1.0) == pytest.approx(1.0)
    assert efficiency(oracle_allocation(1 / q, 0.5, 1.0), q, 0.5, 1.0) < 0


def test_reciprocity_index():
    F = np.array([[0, 2.0, 0], [1.0, 0, 0], [0, 0, 0]])
    assert reciprocity_index(F) == pytest.approx(2 / 3)
    assert reciprocity_index(np.zeros((3, 3))) == 0.0


def test_who_pays_shape():
    rng = np.random.default_rng(0)
    q = rng.lognormal(size=200)
    out = who_pays(rng.normal(size=200), np.zeros(200), q, [0, 1, 2])
    assert out.shape == (10,)


# --- Reproducibility and CRN ------------------------------------------------------------
def test_same_seed_identical():
    a = RNGStreams(42)["network"].random(5)
    b = RNGStreams(42)["network"].random(5)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, RNGStreams(43)["network"].random(5))


def test_streams_independent_of_use_order():
    """Drawing from one stream never changes another (CRN, §9)."""
    r1 = RNGStreams(7)
    pop1 = r1["population"].random(10)
    r2 = RNGStreams(7)
    r2["strategy"].random(1000)  # e.g. a cartel switched on
    pop2 = r2["population"].random(10)
    assert np.array_equal(pop1, pop2)
    assert not np.array_equal(pop1, RNGStreams(7)["network"].random(10))


def test_unknown_stream_rejected():
    with pytest.raises(KeyError):
        RNGStreams(0)["nonsense"]


# --- Config -----------------------------------------------------------------------------
def test_params_defaults_and_hash():
    p = Params()
    assert p.alpha == 0.5 and p.N == 500
    assert p.config_hash() == Params().config_hash()
    assert p.config_hash() == p.replace(seed=99).config_hash()
    assert p.config_hash() != p.replace(alpha=0.6).config_hash()
    assert Params.from_dict(p.to_dict()) == p
    assert all({"unit", "explore", "rationale"} <= set(r) for r in Params.describe())


def test_params_validation():
    with pytest.raises(ValueError):
        Params(alpha=1.0)
    with pytest.raises(ValueError):
        Params(field_shares=(0.5, 0.5))
    with pytest.raises(KeyError):
        Params.from_dict({"not_a_param": 1})


def test_horizon_warning():
    with pytest.warns(HorizonWarning):
        Params(alpha=0.9, T=40, T_eval=10).check_horizon()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Params(alpha=0.8, T=60, T_eval=10).check_horizon()
