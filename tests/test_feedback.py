"""Milestone 4: production, visibility feedback, turnover, contact resampling, A3/A4."""

from __future__ import annotations

import numpy as np
import pytest

from sofa import baselines, metrics
from sofa.config import Params
from sofa.model import SOFAModel, build_world, evaluate
from sofa.population import EARLY, MID, SENIOR
from sofa.production import (
    expected_output,
    realised_output,
    resample_contacts,
    stage_from_age,
    update_visibility,
)
from sofa.rng import RNGStreams

P = Params(N=300)


@pytest.fixture(scope="module")
def world():
    return build_world(P, RNGStreams(21))


# --- Production and visibility (§4.8) ---------------------------------------------------
def test_expected_output_formula():
    q, K = np.array([1.0, 2.0]), np.array([4.0, 1.0])
    np.testing.assert_allclose(expected_output(q, K, 1.0, 0.5, 0.1), [1.8, 1.8])


def test_realised_output_mean_preserving():
    rng = np.random.default_rng(0)
    ybar = np.full(200_000, 2.0)
    assert realised_output(ybar, 0.5, rng).mean() == pytest.approx(2.0, rel=0.01)
    assert np.array_equal(realised_output(ybar, 0.0, rng), ybar)


def test_visibility_update():
    v = np.array([0.5, 1.5])
    y = np.array([3.0, 1.0])
    assert update_visibility(v, y, 0.0) is v
    np.testing.assert_allclose(update_visibility(v, y, 1.0), y / y.mean())
    assert update_visibility(v, y, 0.3).mean() == pytest.approx(1.0)  # mean stays 1


def test_feedback_makes_model_dynamic_and_moves_visibility(world):
    m = SOFAModel(P.replace(lam=0.3, T=20, T_eval=5), seed=21, world=world)
    assert not m.is_static()
    v0 = m.v.copy()
    res = m.run()
    assert not np.allclose(m.v, v0)
    assert m.v.mean() == pytest.approx(1.0)
    # with feedback, visibility tracks funded output: correlation of v with K rises
    assert np.corrcoef(m.v, res.snapshots[20]["K"])[0, 1] > np.corrcoef(v0, m.K)[0, 1]


def test_lambda_zero_production_does_not_change_allocation(world):
    a = SOFAModel(P.replace(T=15, T_eval=3), seed=21, world=world).run()
    b = SOFAModel(P.replace(T=15, T_eval=3, sigma_y=0.8), seed=21, world=world).run()
    assert np.array_equal(a.snapshots[15]["K"], b.snapshots[15]["K"])


def test_overhead_and_net_efficiency(world):
    row = SOFAModel(P, seed=21, world=world).solve()
    assert row["overhead_share"] == pytest.approx(P.c_sofa)
    assert row["efficiency_net"] < row["efficiency"]
    free = SOFAModel(P.replace(c_sofa=0.0), seed=21, world=world).solve()
    assert free["efficiency_net"] == pytest.approx(free["efficiency"])


# --- Turnover (§4.8) --------------------------------------------------------------------
def test_stage_from_age():
    np.testing.assert_array_equal(
        stage_from_age(np.array([0, 4.9, 5, 11.9, 12, 40]), (5, 12)),
        [EARLY, EARLY, MID, MID, SENIOR, SENIOR],
    )


def test_turnover_dynamics(world):
    p = P.replace(turnover=True, T=40, T_eval=5)
    m = SOFAModel(p, seed=21, world=world)
    q0 = m.q.copy()
    res = m.run()
    assert not np.array_equal(m.q, q0)  # researchers were replaced
    assert np.array_equal(world.pop.q, q0)  # the world itself is untouched
    shares = np.bincount(m.stage, minlength=3) / P.N
    assert np.all(shares > 0.1)  # all stages persist
    early = np.nonzero(m.stage == EARLY)[0]
    sup = m.supervisor[early]
    assert np.all(sup >= 0) and np.all(m.stage[sup] == SENIOR)
    same_lab = world.pop.same_lab()
    np.fill_diagonal(same_lab, False)
    assert np.all(m.A[same_lab])  # own lab still always known
    np.testing.assert_allclose(res.yearly.total_K.iloc[-1], P.N * P.B, rtol=1e-6)


def test_turnover_reproducible(world):
    p = P.replace(turnover=True, T=15, T_eval=3)
    a = SOFAModel(p, seed=21, world=world).run().yearly
    b = SOFAModel(p, seed=21, world=world).run().yearly
    assert a.equals(b)


def test_turnover_off_keeps_stages(world):
    m = SOFAModel(P.replace(T=10, T_eval=2), seed=21, world=world)
    m.run()
    assert np.array_equal(m.stage, world.pop.stage)


# --- Contact resampling (§4.2, Phase 4) -------------------------------------------------
def test_resample_contacts_preserves_degree_and_lab(world):
    pop = world.pop
    rng = np.random.default_rng(1)
    A2 = resample_contacts(world.A, pop.same_lab(), pop.same_field(), pop.v0, 1.0, 10.0, 0.2, rng)
    np.testing.assert_array_equal(A2.sum(axis=1), world.A.sum(axis=1))
    same_lab = pop.same_lab()
    assert np.array_equal(A2[same_lab], world.A[same_lab])
    assert not A2.diagonal().any()
    changed = (A2 != world.A).sum() / 2 / world.A[~same_lab].sum()
    assert 0.1 < changed < 0.3
    assert (
        resample_contacts(world.A, same_lab, pop.same_field(), pop.v0, 1, 10, 0.0, rng) is world.A
    )


# --- A3 panel and A4 lottery (§4.10) ----------------------------------------------------
def test_panel_budget_and_selection():
    rng = np.random.default_rng(0)
    scores = rng.normal(size=500)
    K = baselines.a3_panel(scores, P.replace(N=500))
    assert K.sum() == pytest.approx(500.0)
    funded = K > 0
    assert funded.sum() == 100
    assert scores[funded].min() > scores[~funded].max()
    Kb = baselines.a3_panel(scores, P.replace(N=500, b_share=0.4))
    assert Kb.sum() == pytest.approx(500.0) and Kb.min() == pytest.approx(0.4)


def test_lottery_budget_and_triage():
    rng = np.random.default_rng(0)
    scores = rng.normal(size=500)
    K = baselines.a4_lottery(scores, P.replace(N=500), np.random.default_rng(3))
    assert K.sum() == pytest.approx(500.0)
    funded = np.nonzero(K > 0)[0]
    triaged = np.argsort(-scores)[:250]
    assert funded.size == 100 and np.isin(funded, triaged).all()
    K2 = baselines.a4_lottery(scores, P.replace(N=500), np.random.default_rng(4))
    assert not np.array_equal(K, K2)


def test_mechanism_costs():
    assert baselines.mechanism_cost("panel", 3, P)[0] == pytest.approx(0.13)
    assert baselines.mechanism_cost("sofa", 3, P)[0] == pytest.approx(0.01)
    assert baselines.mechanism_cost("equal", 3, P)[0] == 0.0


@pytest.mark.parametrize("mech", ["equal", "oracle", "panel", "lottery"])
def test_comparators_in_model(world, mech):
    p = P.replace(mechanism=mech, T=12, T_eval=3)
    m = SOFAModel(p, seed=21, world=world)
    out = evaluate(m)
    assert out["total_K"] == pytest.approx(P.N * P.B)
    assert out["solved"] == (1.0 if mech in ("equal", "oracle") else 0.0)
    if mech == "equal":
        assert out["efficiency"] == pytest.approx(0.0, abs=1e-12)
    if mech == "oracle":
        assert out["efficiency"] == pytest.approx(1.0)
    if mech in ("panel", "lottery"):
        assert out["overhead_share"] == pytest.approx(0.13)
        assert out["efficiency_net"] < out["efficiency"]


def test_panel_and_lottery_share_scores(world):
    """CRN: the lottery triages on exactly the panel's scores in the same year."""
    a = SOFAModel(P.replace(mechanism="panel"), seed=21, world=world)
    b = SOFAModel(P.replace(mechanism="lottery"), seed=21, world=world)
    Ka, Kb = a.comparator_allocation(1), b.comparator_allocation(1)
    scores = baselines.panel_scores(
        world.pop.q,
        world.pop.v0,
        P.omega_p,
        P.sigma_panel,
        RNGStreams(21).fresh("baselines", "panel", 1),
    )
    triaged = np.argsort(-scores)[:150]
    assert np.isin(np.nonzero(Ka > 0)[0], triaged).all()
    assert np.isin(np.nonzero(Kb > 0)[0], triaged).all()


def test_output_metrics_identity():
    q = np.array([1.0, 2.0])
    K = np.array([1.0, 1.0])
    ybar = expected_output(q, K, 1.0, 0.5, 0.2)
    out = metrics.output_metrics(K, q, ybar, ybar, np.full(2, 0.2), 0.5, 1.0)
    assert out["overhead"] == pytest.approx(0.6)
    assert out["overhead_share"] == pytest.approx(0.2)
