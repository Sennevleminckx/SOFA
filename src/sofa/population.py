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

SINCERE = 0
STRATEGY_NAMES = ("sincere",)  # extended at Milestones 3 and 5


@dataclass(frozen=True)
class Population:
    """Static agent attributes (Phases 1–3). Arrays have length N."""

    q: FloatArray  # latent quality, mean 1 (§4.1)
    field: IntArray  # 0..G−1
    lab: IntArray  # global lab id; labs are nested in fields
    stage: IntArray  # EARLY, MID or SENIOR
    supervisor: IntArray  # index of a senior in the same lab for early-career; −1 otherwise
    v0: FloatArray  # initial visibility, mean 1
    strategy: IntArray  # strategy code (all SINCERE at Milestone 2)

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
    strategy = np.full(N, SINCERE, dtype=int)  # §4.4: own stream from Milestone 3
    return Population(
        q=q, field=field, lab=lab, stage=stage, supervisor=supervisor, v0=v0, strategy=strategy
    )
