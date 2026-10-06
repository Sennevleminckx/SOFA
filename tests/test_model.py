"""Milestone 2: sincere strategy (§4.4), model orchestration (§3), baselines A0–A2 (§4.10)."""

from __future__ import annotations

import time

import numpy as np
import pytest

from conftest import make_W
from sofa import metrics
from sofa.baselines import a0_equal_split, a1_oracle, a2_sincere_sofa
from sofa.config import Params
from sofa.flows import iterate_fixed_W, steady_state
from sofa.model import SOFAModel, build_world
from sofa.rng import RNGStreams
from sofa.strategies import eligible_mask, sincere_rows, sincere_scores

P = Params(N=300)


# --- Sincere rows -----------------------------------------------------------------------
def _S_E(seed=0, N=60, density=0.3):
    rng = np.random.default_rng(seed)
    S = rng.lognormal(size=(N, N))
    E = eligible_mask(rng.random((N, N)) < density)
    return S, E


@pytest.mark.parametrize("m", [1, 3, 10, 10_000])
@pytest.mark.parametrize("beta", [0.0, 1.0, 2.5])
def test_sincere_rows_properties(m, beta):
    S, E = _S_E()
    W = sincere_rows(S, E, m, beta)
    n_elig = E.sum(axis=1)
    assert np.all(W[~E] == 0)
    assert np.all((W > 0).sum(axis=1) == np.minimum(m, n_elig))
    np.testing.assert_allclose(W.sum(axis=1)[n_elig > 0], 1.0)
    for i in range(0, 60, 7):  # kept recipients are the top-m by S; w ∝ S^β
        kept = np.nonzero(W[i])[0]
        if kept.size == 0:
            continue
        dropped = np.setdiff1d(np.nonzero(E[i])[0], kept)
        if dropped.size:
            assert S[i, kept].min() >= S[i, dropped].max()
        np.testing.assert_allclose(W[i, kept], S[i, kept] ** beta / (S[i, kept] ** beta).sum())


def test_sincere_empty_row_is_zero():
    S, E = _S_E()
    E[5] = False
    assert np.all(sincere_rows(S, E, 10, 1.0)[5] == 0)


def test_homophily_raises_own_field_share():
    world = build_world(P, RNGStreams(2))
    sf = world.pop.same_field()

    def own_share(mu):
        W = SOFAModel(P.replace(mu=mu), seed=2, world=world).donation_matrix(1)
        return W[sf].sum() / W.sum()

    assert own_share(3.0) > own_share(1.0) + 0.05


def test_sincere_scores_mu_one_is_identity():
    S, _ = _S_E()
    assert sincere_scores(S, np.ones_like(S, dtype=bool), 1.0) is S


# --- Model ------------------------------------------------------------------------------
def test_same_seed_identical_results():
    a = SOFAModel(P, seed=5).run().yearly
    b = SOFAModel(P, seed=5).run().yearly
    assert a.equals(b)
    c = SOFAModel(P, seed=6).run().yearly
    assert not a.equals(c)


def test_world_crn_across_cells():
    """α, σ_p, ω, β, m change nothing in the world (population, network, tastes; §9)."""
    w0 = build_world(P, RNGStreams(7))
    for change in ({"alpha": 0.8}, {"sigma_p": 1.2}, {"omega": 0.9}, {"beta": 2.0}, {"m": 3}):
        w = SOFAModel(P.replace(**change), seed=7).world
        assert np.array_equal(w.pop.q, w0.pop.q)
        assert np.array_equal(w.A, w0.A)
        assert np.array_equal(w.eps, w0.eps)


def test_annual_converges_to_equilibrium():
    for alpha in (0.3, 0.8):
        p = P.replace(alpha=alpha, T=120)
        res = SOFAModel(p, seed=1).run()
        _, K_eq, _ = SOFAModel(p, seed=1).equilibrium()
        np.testing.assert_allclose(res.snapshots[120]["K"], K_eq, rtol=1e-9)
        eq = SOFAModel(p.replace(flow_mode="equilibrium"), seed=1).run()
        np.testing.assert_allclose(eq.snapshots[120]["K"], K_eq, rtol=1e-12)


def test_switch_off_to_static_W_reproduces_m1():
    """With a fixed W the model reproduces the Milestone 1 iteration exactly."""
    W = make_W(0, N=300, d=20)
    p = P.replace(alpha=0.6, T=40)
    res = SOFAModel(p, seed=0, W_override=W).run()
    ref = iterate_fixed_W(W, 0.6, 1.0, 40)
    for t in (31, 40):
        assert np.array_equal(res.snapshots[t]["K"], ref[t - 1].K)


def test_conservation_every_year():
    res = SOFAModel(P.replace(T=30), seed=3).run()
    # annual mode from R(0) = B·1: Σ K(t) = N·B·(1 − α^(t+1)) exactly, rising to N·B
    t = res.yearly.year.to_numpy()
    np.testing.assert_allclose(res.yearly.total_K, P.N * P.B * (1 - P.alpha ** (t + 1)))
    eq = SOFAModel(P.replace(flow_mode="equilibrium", T=12, T_eval=2), seed=3).run()
    np.testing.assert_allclose(eq.yearly.total_K, P.N * P.B, rtol=1e-12)


def test_cap_in_model_uses_pool_and_conserves():
    p = P.replace(cap=0.05, flow_mode="equilibrium", T=12, T_eval=2)  # m = 10 → 20 needed
    res = SOFAModel(p, seed=4).run()
    assert res.yearly.pool.iloc[-1] > 0
    np.testing.assert_allclose(res.yearly.total_K, p.N * p.B, rtol=1e-12)


@pytest.mark.parametrize(
    "change",
    [
        {"coi": True},
        {"delta": 0.5},
        {"delta_L": 0.5},
        {"lam": 0.2},
        {"turnover": True},
        {"p_audit": 0.1},
        {"K_max": 3.0},
        {"r_A": 0.1},
        {"gamma_up": 2.0},
    ],
)
def test_unbuilt_mechanisms_refuse(change):
    with pytest.raises(NotImplementedError):
        SOFAModel(P.replace(**change), seed=0)


def test_default_run_under_two_seconds():
    """§9: a single-seed run of the default scenario at N = 500 in about 2 s."""
    t0 = time.perf_counter()
    SOFAModel(Params(), seed=0).run()
    assert time.perf_counter() - t0 < 2.0


# --- Baselines --------------------------------------------------------------------------
def test_budgets_equal_N_B():
    world = build_world(P, RNGStreams(1))
    for K in (a0_equal_split(world.pop, P), a1_oracle(world.pop, P), a2_sincere_sofa(P, 1, world)):
        assert K.sum() == pytest.approx(P.N * P.B, rel=1e-12)
        assert np.all(K >= 0)


def test_efficiency_of_baselines():
    world = build_world(P, RNGStreams(1))
    q, th = world.pop.q, P.theta
    assert metrics.efficiency(a0_equal_split(world.pop, P), q, th, P.B) == pytest.approx(0.0)
    assert metrics.efficiency(a1_oracle(world.pop, P), q, th, P.B) == pytest.approx(1.0)


def test_a2_ignores_safeguards():
    world = build_world(P, RNGStreams(1))
    K = a2_sincere_sofa(P.replace(cap=0.05), 1, world)
    np.testing.assert_allclose(K, a2_sincere_sofa(P, 1, world))


def test_alpha_zero_model_is_equal_split():
    _, K, _ = SOFAModel(P.replace(alpha=0.0), seed=0).equilibrium()
    np.testing.assert_allclose(K, P.B)


def test_share_ratios():
    K = np.array([1.0, 1.0, 2.0, 4.0])
    r = metrics.share_ratios(K, np.array([0, 0, 1, 1]), 2)
    np.testing.assert_allclose(r, [0.25 / 0.5, 0.75 / 0.5])


def test_equilibrium_matches_flows_module():
    m = SOFAModel(P, seed=8)
    _, K, W = m.equilibrium()
    _, K2 = steady_state(W, P.alpha, P.B)
    assert np.array_equal(K, K2)
