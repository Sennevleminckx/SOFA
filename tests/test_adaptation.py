"""Milestone 5: imitation, shirking, detection, audits (S5), peer reports, best responses."""

from __future__ import annotations

import numpy as np
import pytest

from sofa import adaptation
from sofa.config import Params
from sofa.flows import return_multiplier_rows, return_multipliers
from sofa.model import SOFAModel, build_world
from sofa.population import BEST, CARTEL, SHIRKER, SINCERE
from sofa.rng import RNGStreams
from sofa.strategies import random_sparse_W

P = Params(N=200, T=30, T_eval=5)


@pytest.fixture(scope="module")
def world():
    return build_world(P, RNGStreams(31))


# --- Unit rules -------------------------------------------------------------------------
def test_fermi_probability():
    assert adaptation.fermi_probability(np.array([1.0]), np.array([1.0]), 0.1, 1.0)[0] == 0.5
    hi = adaptation.fermi_probability(np.array([0.0]), np.array([5.0]), 0.1, 1.0)[0]
    lo = adaptation.fermi_probability(np.array([5.0]), np.array([0.0]), 0.1, 1.0)[0]
    assert hi > 0.999 and lo < 0.001


def test_imitation_pairs_use_contacts():
    A = np.zeros((5, 5), dtype=bool)
    A[0, 3] = A[1, 4] = True
    learners, models = adaptation.imitation_pairs(A, 1.0, np.random.default_rng(0))
    assert list(learners) == [0, 1] and list(models) == [3, 4]  # agents 2–4 know nobody


def test_cartel_registry():
    reg = adaptation.CartelRegistry.from_cartels(10, [np.array([0, 1, 2])])
    assert reg.active() == [0] and list(reg.cartel_id[:3]) == [0, 0, 0]
    assert reg.join(3, 0, k_max=4, year=1) == 0
    assert reg.join(4, 0, k_max=4, year=1) == 1  # full: 4 founds a new cartel
    assert reg.active() == [0] and reg.alive() == [0, 1]
    reg.leave(4, 2)
    assert reg.dissolved[1] == 2 and reg.cartel_id[4] == -1
    former = reg.dissolve(0, 3)
    assert sorted(former) == [0, 1, 2, 3] and (reg.cartel_id == -1).all()
    log = reg.survival(10)
    assert log[0]["ended"] == 3 and not log[0]["censored"]


def test_best_response_rows():
    gamma = np.array([[0.0, 0.5, 0.9, 0.1, 0.7]])
    E = np.array([[False, True, True, True, False]])  # 4 is the best but ineligible
    w1 = adaptation.best_response_rows(gamma, E, 1.0)
    np.testing.assert_array_equal(w1, [[0, 0, 1, 0, 0]])
    w3 = adaptation.best_response_rows(gamma, E, 0.4)
    np.testing.assert_allclose(w3, [[0, 0.4, 0.4, 0.2, 0]])
    assert adaptation.best_response_rows(gamma, np.zeros_like(E), 1.0).sum() == 0


def test_return_multiplier_rows_match_full_matrix():
    W = random_sparse_W(40, 6, np.random.default_rng(0))
    full = return_multipliers(W, 0.7)
    rows = np.array([3, 17, 25])
    np.testing.assert_allclose(return_multiplier_rows(W, 0.7, rows), full[rows], atol=1e-12)


def test_shirk_return_loss():
    W = random_sparse_W(20, 4, np.random.default_rng(1))
    G = return_multipliers(W, 0.5)
    R = np.ones(20)
    np.testing.assert_allclose(adaptation.shirk_return_loss(W, W, R, G, 0.5), 0.0)


def test_audit_and_detection_rules():
    K = np.array([1.0, 2.0, 3.0])
    r = np.array([0.1, 0.3, 0.5])
    sanc, flagged = adaptation.audit_sanctions(K, r, 0.2, 0.5, True)
    assert list(flagged) == [False, True, True]
    np.testing.assert_allclose(sanc, [0, 1.0, 1.5])
    assert adaptation.audit_sanctions(K, r, 0.2, 0.5, False)[0].sum() == 0
    assert adaptation.detection_probability("T2", 0.1) == 1.0
    assert adaptation.detection_probability("T1", 0.1) == 0.1


# --- Model behaviour --------------------------------------------------------------------
def _registry_consistent(m):
    reg, strat = m.registry, m.strategy
    in_reg = reg.cartel_id >= 0
    assert np.all(np.isin(strat[in_reg], (CARTEL, SHIRKER)))
    assert np.all(in_reg[np.isin(strat, (CARTEL, SHIRKER))])
    for c in reg.alive():
        assert np.all(reg.cartel_id[reg.members[c]] == c)


def test_adaptation_run_consistent_and_reproducible(world):
    p = P.replace(adaptation=True, cartels=True, n_C=3, x_herd=0.1, regime="T1")
    m = SOFAModel(p, seed=31, world=world)
    res = m.run()
    _registry_consistent(m)
    shares = res.yearly.filter(like="share_").drop(columns="share_in_cartels")
    np.testing.assert_allclose(shares.sum(axis=1), 1.0)
    again = SOFAModel(p, seed=31, world=world).run().yearly
    assert res.yearly.equals(again)
    assert not m.is_static()


def test_imitation_follows_payoffs(world):
    """With no moral cost cartels pay and spread; with a large one they shrink."""
    base = P.replace(adaptation=True, cartels=True, n_C=4, mu_s=0.0, r_imit=0.3, T=40)
    cheap = SOFAModel(base.replace(c_m=0.0), seed=31, world=world).run().yearly
    dear = SOFAModel(base.replace(c_m=2.0), seed=31, world=world).run().yearly
    assert cheap.share_in_cartels.iloc[-1] > cheap.share_in_cartels.iloc[0]
    assert dear.share_in_cartels.iloc[-1] < dear.share_in_cartels.iloc[0]


def test_shirkers_detected_under_t2_not_t0(world):
    """A huge moral cost makes members shirk; T2 expels them at once, T0 rarely does."""
    base = P.replace(
        adaptation=True,
        cartels=True,
        n_C=5,
        mu_s=0.0,
        r_imit=1.0,
        c_m=5.0,
        kappa_F=1e6,
        p_low=0.0,
        T=6,
        T_eval=2,
    )  # κ_F huge: no imitation
    t0 = SOFAModel(base.replace(regime="T0"), seed=31, world=world).run().yearly
    t2 = SOFAModel(base.replace(regime="T2"), seed=31, world=world).run().yearly
    assert t0.share_shirker.iloc[-1] > 0.05
    assert t2.share_shirker.iloc[-1] == 0.0 and t2.shirk_detected.sum() > 0


def test_audit_sanctions_cartels_and_conserves(world):
    p = P.replace(
        cartels=True,
        n_C=3,
        p_audit=1.0,
        s4_weighted=False,
        r_thr=0.2,
        s_sanction=0.5,
        T=20,
        T_eval=2,
    )
    m = SOFAModel(p, seed=31, world=world)
    res = m.run()
    assert (res.yearly.flagged >= 15).all()  # every member of the three 5-cliques
    members = np.concatenate(m.roles.cartels)
    assert np.all(m.sanctions[members] > 0)
    # sanctions go to the pool and are recycled as a base top-up, so at steady state the
    # kept K net of sanctions sums to N·B (gross K exceeds it by the sanctions)
    assert m.K.sum() == pytest.approx(P.N * P.B, rel=1e-5)
    assert (m.K + m.sanctions).sum() == pytest.approx(P.N * P.B + m.sanctions.sum(), rel=1e-5)


def test_peer_reports_dissolve_cartels_under_t3(world):
    p = P.replace(
        adaptation=True,
        cartels=True,
        n_C=3,
        regime="T3",
        p_peer=1.0,
        mu_s=0.0,
        r_imit=0.0,
        T=5,
        T_eval=2,
    )
    res = SOFAModel(p, seed=31, world=world).run()
    assert res.yearly.cartels_reported.iloc[0] == 3
    assert res.yearly.n_cartels.iloc[-1] == 0


def test_best_responders_need_t3(world):
    p = P.replace(x_best=0.1, T=5, T_eval=2)
    m0 = SOFAModel(p.replace(regime="T2"), seed=31, world=world)
    assert m0.n_fallbacks == 20 and m0.is_static()
    m3 = SOFAModel(p.replace(regime="T3"), seed=31, world=world)
    assert not m3.is_static()
    m3.run()
    W = m3.donation_matrix(m3.t + 1)
    best = np.nonzero(m3.eff == BEST)[0]
    assert np.all((W[best] > 0).sum(axis=1) == 1)  # cap = 1: everything to the best target


def test_switched_off_adaptation_leaves_strategies(world):
    m = SOFAModel(P.replace(cartels=True, n_C=2), seed=31, world=world)
    m.run()
    assert m.registry is None and np.all(m.strategy[np.concatenate(m.roles.cartels)] == CARTEL)
    assert (m.strategy == SINCERE).sum() == P.N - 10
