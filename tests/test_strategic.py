"""Milestone 3: roles, regimes, strategic donors, cartels in the full model, S1–S4."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from conftest import make_W, years_to_converge
from sofa import metrics
from sofa.config import Params
from sofa.flows import iterate_fixed_W, steady_state, steady_state_general
from sofa.information import REGIMES, effective_strategies, feasible
from sofa.model import SOFAModel, build_world
from sofa.population import (
    CARTEL,
    DEFERENTIAL,
    EARLY,
    HERDER,
    RECIPROCATOR,
    SINCERE,
    assign_roles,
)
from sofa.rng import RNGStreams
from sofa.safeguards import (
    FlowSafeguards,
    cap_project,
    cycle_return_discount,
    mutual_flow_discount,
)
from sofa.strategies import (
    herder_scores,
    internal_rows,
    random_sparse_W,
    reciprocator_rows,
    reciprocity_shares,
)

P = Params(N=300)


@pytest.fixture(scope="module")
def world():
    return build_world(P, RNGStreams(11))


# --- Roles ------------------------------------------------------------------------------
@pytest.mark.parametrize("selection", ["random", "same_field", "low_q", "high_q"])
def test_cartel_roles(world, selection):
    p = P.replace(cartels=True, n_C=4, k=5, cartel_selection=selection)
    roles = assign_roles(world.pop, p, RNGStreams(11))
    assert len(roles.cartels) == 4
    members = np.concatenate(roles.cartels)
    assert members.size == np.unique(members).size == 20  # disjoint
    assert np.all(roles.strategy[members] == CARTEL)
    assert np.all(roles.cartel_id[roles.cartels[2]] == 2)
    q = world.pop.q
    for c in roles.cartels:
        if selection == "same_field":
            assert np.unique(world.pop.field[c]).size == 1
        if selection == "low_q":
            assert q[c].max() <= np.quantile(q, 0.25)
        if selection == "high_q":
            assert q[c].min() >= np.quantile(q, 0.75)


def test_cartel_share_x_C(world):
    roles = assign_roles(world.pop, P.replace(cartels=True, x_C=0.1, k=5), RNGStreams(1))
    assert len(roles.cartels) == 6  # 0.1 · 300 / 5


def test_herder_reciprocator_shares_nested(world):
    r1 = assign_roles(world.pop, P.replace(x_herd=0.1, x_recip=0.1), RNGStreams(3))
    r2 = assign_roles(world.pop, P.replace(x_herd=0.25, x_recip=0.1), RNGStreams(3))
    assert (r1.strategy == HERDER).sum() == 30 and (r1.strategy == RECIPROCATOR).sum() == 30
    assert np.all(r2.strategy[r1.strategy == HERDER] == HERDER)  # nested as share grows


def test_herders_exclude_cartel_members(world):
    p = P.replace(cartels=True, n_C=3, x_herd=0.5)
    roles = assign_roles(world.pop, p, RNGStreams(3))
    assert not np.any(roles.in_cartel & (roles.strategy == HERDER))


def test_deference_only_early_sincere(world):
    roles = assign_roles(world.pop, P.replace(gamma_up=2.0, x_herd=0.2), RNGStreams(3))
    d = roles.strategy == DEFERENTIAL
    assert np.all(world.pop.stage[d] == EARLY)
    assert not np.any((world.pop.stage == EARLY) & (roles.strategy == SINCERE))


def test_cartel_toggle_crn():
    """Switching cartels on leaves population, network and tastes bit-identical (§10)."""
    a = SOFAModel(P, seed=4)
    b = SOFAModel(P.replace(cartels=True, n_C=2), seed=4)
    assert np.array_equal(a.world.A, b.world.A)
    assert np.array_equal(a.world.eps, b.world.eps)
    assert np.array_equal(a.pop.q, b.pop.q)
    assert np.array_equal(a.pop.v0, b.pop.v0)


# --- Regimes and fallbacks --------------------------------------------------------------
def test_feasibility_table():
    for regime in REGIMES:
        assert feasible(SINCERE, regime) and feasible(CARTEL, regime)
        assert feasible(DEFERENTIAL, regime)
    assert [feasible(HERDER, r) for r in REGIMES] == [False, True, True, True]
    assert [feasible(RECIPROCATOR, r) for r in REGIMES] == [False, False, True, True]


@pytest.mark.parametrize("regime", REGIMES)
def test_fallbacks_counted(world, regime):
    p = P.replace(x_herd=0.1, x_recip=0.2, regime=regime)
    m = SOFAModel(p, seed=11, world=world)
    expected = {"T0": 90, "T1": 60, "T2": 0, "T3": 0}[regime]
    assert m.n_fallbacks == expected
    assert np.all(m.eff[m.roles.strategy == HERDER] == (HERDER if regime != "T0" else SINCERE))
    eff, n = effective_strategies(m.roles.strategy, regime)
    assert n == expected and np.array_equal(eff, m.eff)


def test_infeasible_strategies_reproduce_sincere(world):
    """Herders and reciprocators under T0 play sincere: identical to the all-sincere run."""
    base = SOFAModel(P, seed=11, world=world).equilibrium()[1]
    fb = SOFAModel(P.replace(x_herd=0.3, x_recip=0.3), seed=11, world=world)
    assert fb.is_static()
    assert np.array_equal(fb.equilibrium()[1], base)


def test_regime_irrelevant_for_sincere(world):
    ref = SOFAModel(P, seed=11, world=world).equilibrium()[1]
    for regime in REGIMES:
        K = SOFAModel(P.replace(regime=regime), seed=11, world=world).equilibrium()[1]
        assert np.array_equal(K, ref)


# --- Strategy rules ---------------------------------------------------------------------
def test_herder_h_zero_is_sincere():
    rng = np.random.default_rng(0)
    S = rng.lognormal(size=(20, 20))
    R = rng.lognormal(size=20)
    np.testing.assert_allclose(herder_scores(S, R, 0.0), S)
    H1 = herder_scores(S, R, 1.0)
    np.testing.assert_allclose(H1, np.broadcast_to(R / R.mean(), (20, 20)))


def test_reciprocity_shares():
    F = np.array([[0, 2.0, 0], [1.0, 0, 0], [3.0, 1.0, 0]])
    g, received = reciprocity_shares(F)
    np.testing.assert_allclose(g[0], [0, 0.25, 0.75])  # 0 received 1 from 1, 3 from 2
    assert not received[2]
    w = np.full((3, 3), 1 / 3)
    out = reciprocator_rows(w, g, received, 0.5)
    np.testing.assert_allclose(out[2], w[2])  # received nothing → sincere
    np.testing.assert_allclose(out.sum(axis=1), 1.0)


def test_reactive_strategies_make_W_dynamic(world):
    for change in ({"x_herd": 0.2, "regime": "T1"}, {"x_recip": 0.2, "regime": "T2"}):
        m = SOFAModel(P.replace(**change), seed=11, world=world)
        assert not m.is_static()
        with pytest.raises(ValueError, match="simulate"):
            m.equilibrium()


def test_herders_concentrate(world):
    """Herding on last year's receipts (T1) raises concentration relative to sincere."""
    p = P.replace(T=40, T_eval=5)
    g0 = SOFAModel(p, seed=11, world=world).run().summary()["gini"]
    g1 = SOFAModel(p.replace(x_herd=0.5, regime="T1"), seed=11, world=world).run().summary()
    assert g1["gini"] > g0
    assert g1["fallbacks"] == 0


def test_reciprocators_raise_reciprocity(world):
    p = P.replace(T=40, T_eval=5)
    r0 = SOFAModel(p, seed=11, world=world).run().summary()["reciprocity"]
    r1 = SOFAModel(p.replace(x_recip=0.5, regime="T2"), seed=11, world=world).run().summary()
    assert r1["reciprocity"] > r0 + 0.05


def test_deference_shifts_money_to_seniors(world):
    def senior(g):
        m = SOFAModel(P.replace(gamma_up=g), seed=11, world=world)
        return metrics.share_ratios(m.equilibrium()[1], m.pop.stage, 3)[2]

    assert senior(3.0) > senior(1.0)


# --- Cartels in the full model ----------------------------------------------------------
@pytest.mark.parametrize("topology", ["clique", "ring", "star"])
@pytest.mark.parametrize("phi", [0.4, 1.0])
def test_full_model_cartel_internal_share_and_exact_form(world, topology, phi):
    p = P.replace(cartels=True, n_C=2, k=5, phi=phi, topology=topology)
    m = SOFAModel(p, seed=11, world=world)
    st_, W = m.equilibrium_state()
    for C in m.roles.cartels:
        np.testing.assert_allclose(W[np.ix_(C, C)].sum(axis=1), phi, atol=1e-12)
        np.testing.assert_allclose(W[C].sum(axis=1), 1.0, atol=1e-12)
        I_C, _ = metrics.group_flows(st_.F, C)
        exact = (1 - p.alpha) * (len(C) * p.B + I_C) / (1 - p.alpha * phi)  # §2.3.5
        assert abs(st_.K[C].sum() - exact) < 1e-10


def test_full_model_ring_zero_mutual_flow(world):
    m = SOFAModel(P.replace(cartels=True, k=5, phi=1.0, topology="ring"), seed=11, world=world)
    st_, _ = m.equilibrium_state()
    assert metrics.mutual_flow(st_.F, m.roles.cartels[0]) == 0.0


def test_full_model_premium_below_bound(world):
    K0 = SOFAModel(P, seed=11, world=world).equilibrium()[1]
    for alpha, phi in ((0.5, 1.0), (0.8, 0.5)):
        K0 = SOFAModel(P.replace(alpha=alpha), seed=11, world=world).equilibrium()[1]
        p = P.replace(alpha=alpha, cartels=True, k=5, phi=phi)
        m = SOFAModel(p, seed=11, world=world)
        Pi = metrics.cartel_premium(m.equilibrium()[1], K0, m.roles.cartels[0])
        assert 1.0 < Pi <= metrics.premium_bound(alpha, phi) + 1e-9


# --- Safeguards -------------------------------------------------------------------------
def test_coi_no_flow_within_lab(world):
    p = P.replace(coi=True, cartels=True, n_C=3, cartel_selection="same_field")
    st_, W = SOFAModel(p, seed=11, world=world).equilibrium_state()
    same_lab = world.pop.same_lab()
    assert st_.F[same_lab].sum() == 0.0
    assert W[same_lab].sum() == 0.0
    assert st_.K.sum() == pytest.approx(P.N * P.B, rel=1e-12)


def test_mutual_flow_discount():
    F = np.array([[0, 2.0, 1.0], [1.0, 0, 0], [0, 0, 0]])
    F2, leak = mutual_flow_discount(F, 1.0)
    assert leak == pytest.approx(2.0)  # min(2, 1) removed from both directions
    assert F2[0, 1] == 1.0 and F2[1, 0] == 0.0 and F2[0, 2] == 1.0
    assert np.minimum(F2, F2.T).sum() == 0.0


def test_cycle_discount_sees_ring_only_within_L():
    k, alpha = 5, 0.5
    W = internal_rows(list(range(k)), k, "ring")
    F = alpha * W
    _, leak3, r3 = cycle_return_discount(F, W, alpha, 1.0, L=3)
    _, leak5, r5 = cycle_return_discount(F, W, alpha, 1.0, L=5)
    assert leak3 == 0.0 and np.all(r3 == 0)  # a 5-ring evades L = 3
    np.testing.assert_allclose(r5, alpha**4)
    assert leak5 == pytest.approx(F.sum() * alpha**4)


def test_cycle_discount_factor_clipped():
    W = internal_rows([0, 1], 2, "clique")
    F2, leak, r = cycle_return_discount(0.9 * W, W, 0.9, 1.0, L=5)
    assert np.all(r > 1)  # α + α³
    assert np.all(F2 == 0.0) and leak == pytest.approx(1.8)


def test_steady_state_general_matches_annual_limit():
    W = cap_project(make_W(1, N=200, d=15), 0.1).W
    for sg in (
        FlowSafeguards(0.6, delta=0.5),
        FlowSafeguards(0.6, delta_L=0.7, L=3),
        FlowSafeguards(0.6, delta=1.0, delta_L=1.0, L=4),
    ):
        st_ = steady_state_general(W, 0.6, 1.0, sg)
        last = iterate_fixed_W(W, 0.6, 1.0, years_to_converge(0.6, pool=True), sg=sg)[-1]
        np.testing.assert_allclose(st_.K, last.K, rtol=1e-9)
        assert st_.K.sum() == pytest.approx(200.0, rel=1e-12)
        assert st_.pool > 0


def test_steady_state_general_without_safeguards_is_closed_form():
    W = make_W(2, N=100, d=10)
    st_ = steady_state_general(W, 0.7, 1.0, FlowSafeguards(0.7))
    np.testing.assert_array_equal(st_.K, steady_state(W, 0.7, 1.0)[1])


def test_s3_does_not_stop_ring_but_s4_does(world):
    """H3 in miniature: S3 cuts the clique premium but not the ring's; S4 (L ≥ k) cuts both.

    S3 even *raises* the ring's premium: it discounts ordinary two-way flows between
    sincere donors, and ring members, who give nothing to outsiders, escape that discount
    on their inflow (finding reported in reports/M3.md).
    """

    def premium(topology, **sg):
        base = P.replace(**sg)
        K0 = SOFAModel(base, seed=11, world=world).equilibrium()[1]
        m = SOFAModel(
            base.replace(cartels=True, k=5, phi=1.0, topology=topology), seed=11, world=world
        )
        return metrics.cartel_premium(m.equilibrium()[1], K0, m.roles.cartels[0])

    none = {t: premium(t) for t in ("clique", "ring")}
    s3 = {t: premium(t, delta=1.0) for t in ("clique", "ring")}
    s4 = {t: premium(t, delta_L=1.0, L=5) for t in ("clique", "ring")}
    assert s3["clique"] < none["clique"] - 0.3
    assert s3["ring"] >= none["ring"]
    # S4 sees a k-ring only through r = α^(k−1) (here 0.5⁴): the internal share falls to
    # φ′ = 1 − δ_L·α^(k−1), so the reduction is real but small (reported in M3)
    assert s4["ring"] < none["ring"] - 0.05
    phi_eff = 1 - 1.0 * 0.5**4
    assert s4["ring"] <= metrics.premium_bound(0.5, phi_eff) + 1e-9
    assert s4["clique"] < none["clique"]


@settings(max_examples=50, deadline=None)
@given(
    seed=st.integers(0, 10_000),
    N=st.integers(5, 30),
    alpha=st.floats(0.05, 0.9),
    c=st.floats(0.05, 1.0),
    delta=st.floats(0.0, 1.0),
    delta_L=st.floats(0.0, 1.0),
    L=st.integers(2, 5),
)
def test_conservation_property_with_safeguards(seed, N, alpha, c, delta, delta_L, L):
    """Property: Σ K* = N·B under random W, α, cap, S3 and S4 (§4.6, §10)."""
    rng = np.random.default_rng(seed)
    W = cap_project(random_sparse_W(N, int(rng.integers(1, N)), rng), c).W
    st_ = steady_state_general(W, alpha, 1.0, FlowSafeguards(alpha, delta, delta_L, L))
    assert np.all(st_.K >= 0)
    assert st_.K.sum() == pytest.approx(N, rel=1e-9)


# --- Switch-off -------------------------------------------------------------------------
def test_switched_off_m3_reproduces_m2(world):
    """Every M3 switch at its off value gives the same K as the plain sincere model."""
    ref = SOFAModel(P, seed=11, world=world).equilibrium()[1]
    off = P.replace(
        cartels=False,
        x_herd=0.0,
        x_recip=0.0,
        gamma_up=1.0,
        coi=False,
        delta=0.0,
        delta_L=0.0,
        regime="T3",
    )
    assert np.array_equal(SOFAModel(off, seed=11, world=world).equilibrium()[1], ref)
