"""Milestone 2: population (§4.1), awareness network (§4.2), perception (§4.3)."""

from __future__ import annotations

import numpy as np
import pytest

from sofa.config import Params
from sofa.network import build_network
from sofa.perception import draw_taste, perceived_quality
from sofa.population import EARLY, SENIOR, build_population, quota
from sofa.rng import RNGStreams

P300 = Params(N=300)


@pytest.fixture(scope="module")
def pop():
    return build_population(P300, RNGStreams(3))


@pytest.fixture(scope="module")
def A(pop):
    return build_network(pop, P300, RNGStreams(3))


# --- Population -------------------------------------------------------------------------
def test_quota_sums_and_rounds():
    c = quota(300, (0.35, 0.25, 0.20, 0.12, 0.08))
    assert c.sum() == 300
    assert np.all(np.abs(c - 300 * np.array([0.35, 0.25, 0.20, 0.12, 0.08])) < 1)


def test_quality_mean_one(pop):
    assert pop.q.mean() == pytest.approx(1.0)
    assert np.all(pop.q > 0)


def test_fields_labs_nested(pop):
    assert np.array_equal(np.bincount(pop.field), quota(300, P300.field_shares))
    for ell in np.unique(pop.lab):
        members = pop.lab == ell
        assert np.unique(pop.field[members]).size == 1  # labs nested in fields
        assert 4 <= members.sum() <= 8


def test_stages_and_supervisors(pop):
    assert np.array_equal(np.bincount(pop.stage, minlength=3), quota(300, P300.stage_shares))
    early = np.nonzero(pop.stage == EARLY)[0]
    assert np.all(pop.supervisor[early] >= 0)
    assert np.all(pop.stage[pop.supervisor[early]] == SENIOR)
    assert np.all(pop.lab[pop.supervisor[early]] == pop.lab[early])
    assert np.all(pop.supervisor[pop.stage != EARLY] == -1)
    for ell in np.unique(pop.lab):  # every lab has a senior
        assert np.any((pop.lab == ell) & (pop.stage == SENIOR))


def test_visibility(pop):
    assert pop.v0.mean() == pytest.approx(1.0)
    # stage multiplier 0.5/1.0/1.5 and κ = 1: seniors more visible on average
    assert pop.v0[pop.stage == SENIOR].mean() > pop.v0[pop.stage == EARLY].mean()
    assert np.corrcoef(np.log(pop.q), np.log(pop.v0))[0, 1] > 0.5


def test_population_reproducible_and_independent_of_other_streams():
    a = build_population(P300, RNGStreams(9))
    r = RNGStreams(9)
    r["strategy"].random(1000)
    r["network"].random(1000)
    b = build_population(P300, r)
    for name in ("q", "field", "lab", "stage", "supervisor", "v0"):
        assert np.array_equal(getattr(a, name), getattr(b, name))


# --- Network ----------------------------------------------------------------------------
def test_network_degree_and_lab(pop, A):
    assert not A.diagonal().any()
    same_lab = pop.same_lab()
    np.fill_diagonal(same_lab, False)
    assert np.all(A[same_lab])  # always aware of own lab
    assert abs(A.sum(axis=1).mean() - P300.d) / P300.d < 0.05
    assert (A & ~pop.same_lab()).sum(axis=1).min() >= P300.min_eligible


def test_network_homophily_ratio(pop, A):
    """Within-field link probability ≈ 10 × between-field, for comparable visibility (§4.2)."""
    sf, nl = pop.same_field(), ~pop.same_lab()
    p_in = A[sf & nl].mean()
    p_out = A[~sf].mean()
    assert 6 < p_in / p_out < 15  # 10:1 before the min(1, ·) clip and visibility mixing


def test_network_visibility_attracts(pop, A):
    indeg = (A & ~pop.same_lab()).sum(axis=0)
    assert np.corrcoef(pop.v0, indeg)[0, 1] > 0.5


def test_top_up_guarantee_small_degree():
    p = Params(N=200, d=6.0)
    pop = build_population(p, RNGStreams(1))
    A = build_network(pop, p, RNGStreams(1))
    assert (A & ~pop.same_lab()).sum(axis=1).min() >= 5


def test_network_crn():
    """Perception and strategy draws never shift the network (§9)."""
    p = Params(N=200)
    r1, r2 = RNGStreams(4), RNGStreams(4)
    pop1, pop2 = build_population(p, r1), build_population(p, r2)
    r2["perception"].random(10_000)
    assert np.array_equal(build_network(pop1, p, r1), build_network(pop2, p, r2))


# --- Perception -------------------------------------------------------------------------
def test_perception_limits(pop):
    eps = draw_taste(pop.N, RNGStreams(0))
    q0 = perceived_quality(pop.q, pop.v0, eps, omega=0.0, sigma_p=0.0)
    assert np.allclose(q0, pop.q[None, :])
    q1 = perceived_quality(pop.q, pop.v0, eps, omega=1.0, sigma_p=0.0)
    assert np.allclose(q1, pop.v0[None, :])


def test_perception_noise_mean_one(pop):
    """E[exp(σ ε − σ²/2)] = 1, so the noise does not bias perceived quality (§4.3)."""
    eps = draw_taste(pop.N, RNGStreams(0))
    qh = perceived_quality(pop.q, pop.v0, eps, omega=0.0, sigma_p=0.5)
    ratio = qh / pop.q[None, :]
    assert ratio.mean() == pytest.approx(1.0, abs=0.01)
    assert np.log(ratio).std() == pytest.approx(0.5, abs=0.01)
