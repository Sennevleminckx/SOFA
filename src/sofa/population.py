"""Researchers: quality, fields, labs, career stages, supervisors, visibility (§4.1).

Each attribute is drawn from its own named sub-stream of ``population`` so that changing
how one attribute is drawn never shifts the draws of another. Strategy assignment uses
the separate ``strategy`` stream (§4.1), so toggling strategies never changes any draw
made here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sofa.config import Params
from sofa.rng import RNGStreams

FloatArray = np.ndarray
IntArray = np.ndarray

EARLY, MID, SENIOR = 0, 1, 2
STAGE_NAMES = ("early", "mid", "senior")

# Strategy codes (§4.4, §4.9). A shirker is a cartel member who secretly donates sincerely.
SINCERE, HERDER, RECIPROCATOR, CARTEL, DEFERENTIAL, SHIRKER, BEST = 0, 1, 2, 3, 4, 5, 6
STRATEGY_NAMES = (
    "sincere",
    "herder",
    "reciprocator",
    "cartel",
    "deferential",
    "shirker",
    "best_responder",
)


@dataclass(frozen=True)
class Population:
    """Static agent attributes (Phases 1–3). Arrays have length N."""

    q: FloatArray  # latent quality, mean 1 (§4.1)
    field: IntArray  # 0..G−1
    lab: IntArray  # global lab id; labs are nested in fields
    stage: IntArray  # EARLY, MID or SENIOR
    supervisor: IntArray  # index of a senior in the same lab for early-career; −1 otherwise
    v0: FloatArray  # initial visibility, mean 1

    @property
    def N(self) -> int:
        """Number of researchers."""
        return self.q.size

    def same_lab(self) -> np.ndarray:
        """Boolean N×N matrix: True where i and j share a lab (diagonal included)."""
        return self.lab[:, None] == self.lab[None, :]

    def same_field(self) -> np.ndarray:
        """Boolean N×N matrix: True where i and j share a field (diagonal included)."""
        return self.field[:, None] == self.field[None, :]


def quota(n: int, shares: tuple[float, ...]) -> IntArray:
    """Integer counts summing to ``n`` closest to ``n·shares`` (largest remainder)."""
    raw = np.asarray(shares, dtype=float) * n
    counts = np.floor(raw).astype(int)
    short = n - counts.sum()
    counts[np.argsort(-(raw - counts), kind="stable")[:short]] += 1
    return counts


def draw_quality(N: int, sigma_q: float, rng: np.random.Generator) -> FloatArray:
    """q_i ~ LogNormal(0, σ_q), rescaled to mean 1 (§4.1)."""
    q = rng.lognormal(0.0, sigma_q, N)
    return q / q.mean()


def assign_fields_and_labs(N: int, p: Params) -> tuple[IntArray, IntArray]:
    """Fields in contiguous blocks by quota; labs of about ``lab_size`` within each field (§4.1).

    Agents are exchangeable (quality is drawn independently), so block assignment loses
    no generality and needs no randomness.
    """
    counts = quota(N, p.field_shares)
    field = np.repeat(np.arange(p.G), counts)
    lab = np.empty(N, dtype=int)
    next_lab = 0
    for g in range(p.G):
        idx = np.nonzero(field == g)[0]
        n_labs = max(1, round(idx.size / p.lab_size))
        for chunk in np.array_split(idx, n_labs):
            lab[chunk] = next_lab
            next_lab += 1
    return field, lab


def assign_stages(
    lab: IntArray, shares: tuple[float, float, float], rng: np.random.Generator
) -> IntArray:
    """Career stages with population shares ``shares`` and at least one senior per lab (§4.1).

    One random member of every lab is made senior first, so that every early-career
    researcher can have a senior supervisor in the same lab. The remaining seniors, then
    the early- and mid-career researchers, are allocated at random to hit the quotas.
    If there are fewer seniors than labs, labs without a senior get no early-career
    members where possible.
    """
    N = lab.size
    n_early, n_mid, n_senior = quota(N, shares)
    stage = np.full(N, -1, dtype=int)
    labs = rng.permutation(np.unique(lab))
    anchors = np.array([rng.choice(np.nonzero(lab == ell)[0]) for ell in labs])
    anchors = anchors[:n_senior]  # guard: fewer seniors than labs
    stage[anchors] = SENIOR
    rest = rng.permutation(np.nonzero(stage < 0)[0])
    n_extra = n_senior - anchors.size
    stage[rest[:n_extra]] = SENIOR
    rest = rest[n_extra:]
    # early-career only in labs that have a senior
    has_senior = np.isin(lab[rest], np.unique(lab[stage == SENIOR]))
    rest = np.concatenate([rest[has_senior], rest[~has_senior]])
    stage[rest[:n_early]] = EARLY
    stage[rest[n_early:]] = MID
    assert (stage >= 0).all() and np.count_nonzero(stage == MID) == n_mid
    return stage


def assign_supervisors(
    lab: IntArray, field: IntArray, stage: IntArray, rng: np.random.Generator
) -> IntArray:
    """Each early-career researcher gets a random senior from their lab (§4.1).

    Falls back to a senior in the same field only if the lab has none (cannot happen
    when there are at least as many seniors as labs).
    """
    sup = np.full(lab.size, -1, dtype=int)
    for i in np.nonzero(stage == EARLY)[0]:
        cands = np.nonzero((lab == lab[i]) & (stage == SENIOR))[0]
        if cands.size == 0:
            cands = np.nonzero((field == field[i]) & (stage == SENIOR))[0]
        sup[i] = rng.choice(cands)
    return sup


def draw_visibility(
    q: FloatArray, stage: IntArray, p: Params, rng: np.random.Generator
) -> FloatArray:
    """v_i(0) = q_i^κ × stage multiplier × LogNormal(0, σ_v), rescaled to mean 1 (§4.1)."""
    mult = np.asarray(p.stage_visibility)[stage]
    v = q**p.kappa * mult * rng.lognormal(0.0, p.sigma_v, q.size)
    return v / v.mean()


def build_population(p: Params, rngs: RNGStreams) -> Population:
    """Draw the full static population for one seed (§4.1)."""
    N = p.N
    q = draw_quality(N, p.sigma_q, rngs.get("population", "quality"))
    field, lab = assign_fields_and_labs(N, p)
    stage = assign_stages(lab, p.stage_shares, rngs.get("population", "stage"))
    supervisor = assign_supervisors(lab, field, stage, rngs.get("population", "supervisor"))
    v0 = draw_visibility(q, stage, p, rngs.get("population", "visibility"))
    return Population(q=q, field=field, lab=lab, stage=stage, supervisor=supervisor, v0=v0)


# --- Strategy roles (§4.1, §4.4) --------------------------------------------------------
@dataclass(frozen=True)
class Roles:
    """Strategy of each agent and cartel membership. Drawn from the ``strategy`` stream."""

    strategy: IntArray  # strategy code per agent
    cartel_id: IntArray  # index into ``cartels``; −1 for non-members
    cartels: tuple[IntArray, ...]  # members in routing order (ring order; star hub first)

    @property
    def in_cartel(self) -> np.ndarray:
        """Boolean mask of cartel members."""
        return self.cartel_id >= 0

    def same_cartel(self) -> np.ndarray:
        """Boolean N×N matrix: True where i and j are members of the same cartel."""
        c = self.cartel_id
        return (c[:, None] == c[None, :]) & (c[:, None] >= 0)


def n_cartels(p: Params) -> int:
    """Return the number of cartels: n_C, or round(x_C·N/k) when a share x_C is given."""
    if not p.cartels:
        return 0
    return p.n_C if p.x_C is None else round(p.x_C * p.N / p.k)


def _select_cartel(
    pop: Population, free: np.ndarray, k: int, selection: str, rng: np.random.Generator
) -> IntArray:
    """Choose k unassigned agents by ``cartel_selection`` (§4.4).

    random: uniformly. same_field: k agents of the field of a random unassigned agent.
    low_q / high_q: uniformly among unassigned agents in the bottom / top quartile of
    quality (falling back to the k lowest / highest unassigned when the quartile runs
    out). Assumption: quartiles, not the exact extremes, so that cartels are not all
    identical across seeds.
    """
    cand = np.nonzero(free)[0]
    if selection == "same_field":
        g = pop.field[rng.choice(cand)]
        cand = cand[pop.field[cand] == g]
    elif selection in ("low_q", "high_q"):
        lo, hi = np.quantile(pop.q, [0.25, 0.75])
        quart = cand[pop.q[cand] <= lo] if selection == "low_q" else cand[pop.q[cand] >= hi]
        if quart.size >= k:
            cand = quart
        else:
            order = np.argsort(pop.q[cand])
            cand = cand[order[:k]] if selection == "low_q" else cand[order[-k:]]
    if cand.size < k:
        raise ValueError(f"not enough unassigned agents to form a cartel of size {k}")
    return rng.choice(cand, size=k, replace=False)  # random order = routing order


def assign_roles(pop: Population, p: Params, rngs: RNGStreams) -> Roles:
    """Assign cartels, herders, reciprocators and deference (§4.1, §4.4).

    Order: cartels first, then herders and reciprocators among non-members (each by
    the lowest values of its own uniform draw, so the sets are nested as shares grow),
    then deference for early-career sincere agents when γ_up ≠ 1 (assumption: deference
    applies to every early-career researcher who is otherwise sincere).
    """
    N = pop.N
    strategy = np.full(N, SINCERE, dtype=int)
    cartel_id = np.full(N, -1, dtype=int)
    cartels: list[IntArray] = []
    rng_c = rngs.get("strategy", "cartels")
    for c in range(n_cartels(p)):
        members = _select_cartel(pop, cartel_id < 0, p.k, p.cartel_selection, rng_c)
        cartel_id[members] = c
        strategy[members] = CARTEL
        cartels.append(members)
    shares = (
        (HERDER, p.x_herd, "herder"),
        (RECIPROCATOR, p.x_recip, "recip"),
        (BEST, p.x_best, "best"),
    )
    for code, share, name in shares:
        n = round(share * N)
        if n == 0:
            continue
        u = rngs.get("strategy", name).random(N)
        cand = np.nonzero(strategy == SINCERE)[0]
        strategy[cand[np.argsort(u[cand])[:n]]] = code
    if p.gamma_up != 1.0:
        strategy[(strategy == SINCERE) & (pop.stage == EARLY)] = DEFERENTIAL
    return Roles(strategy=strategy, cartel_id=cartel_id, cartels=tuple(cartels))
