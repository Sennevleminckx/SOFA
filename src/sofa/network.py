"""Awareness network: who i can donate to (§4.2). Static in Phases 1–3.

``A[i, j]`` is True when i is aware of j. P(i aware of j) = min(1, p_f · v_j^τ), with
p_f = p_in for the same field and p_out otherwise, p_in : p_out fixed, and the overall
scale chosen so that the expected mean out-degree (including the always-known own lab)
equals d. Every agent is aware of their own lab, and has at least ``min_eligible``
contacts outside their lab (the non-COI contacts), topped up at random within the field.
"""

from __future__ import annotations

import numpy as np

from sofa.config import Params
from sofa.population import Population
from sofa.rng import RNGStreams

BoolArray = np.ndarray
FloatArray = np.ndarray


def awareness_probabilities(pop: Population, p: Params, v: FloatArray | None = None) -> FloatArray:
    """N×N matrix of P(i aware of j) for the random part of the network (§4.2).

    Own-lab pairs and the diagonal are set to 0 here (the lab is added with certainty).
    """
    v = pop.v0 if v is None else v
    same_field = pop.same_field()
    not_lab = ~pop.same_lab()
    attract = v**p.tau  # v_j^τ, broadcast over rows
    base = np.where(same_field, p.p_in_out_ratio, 1.0) * attract[None, :]
    base = np.where(not_lab, base, 0.0)
    lab_deg = (~not_lab).sum(axis=1) - 1  # own-lab contacts excluding self
    target = p.d - lab_deg.mean()  # expected random contacts per agent
    if target <= 0:
        return np.zeros_like(base)
    lo, hi = 0.0, 1.0
    while np.minimum(1.0, hi * base).sum() / pop.N < target:  # bracket the scale
        hi *= 2.0
        if hi > 1e12:  # the target exceeds the number of possible contacts
            return np.where(base > 0, 1.0, 0.0)
    for _ in range(100):  # bisection: expected degree is monotone in the scale
        mid = 0.5 * (lo + hi)
        if np.minimum(1.0, mid * base).sum() / pop.N < target:
            lo = mid
        else:
            hi = mid
    return np.minimum(1.0, hi * base)  # p_out = hi, p_in = hi · ratio


def top_up(A: BoolArray, pop: Population, minimum: int, rng: np.random.Generator) -> BoolArray:
    """Ensure each agent has at least ``minimum`` contacts outside their lab (§4.2).

    Missing contacts are drawn uniformly from the agent's field (outside the lab); if the
    field is too small, from the whole population.
    """
    A = A.copy()
    not_lab = ~pop.same_lab()
    n_out = (A & not_lab).sum(axis=1)
    for i in np.nonzero(n_out < minimum)[0]:
        need = minimum - n_out[i]
        pool = np.nonzero((pop.field == pop.field[i]) & not_lab[i] & ~A[i])[0]
        if pool.size < need:
            pool = np.nonzero(not_lab[i] & ~A[i])[0]
        A[i, rng.choice(pool, size=min(need, pool.size), replace=False)] = True
    return A


def build_network(pop: Population, p: Params, rngs: RNGStreams) -> BoolArray:
    """Draw the static awareness network for one seed (§4.2)."""
    P = awareness_probabilities(pop, p)
    A = rngs.get("network", "edges").random(P.shape) < P
    A |= pop.same_lab()  # always aware of own lab
    np.fill_diagonal(A, False)
    return top_up(A, pop, p.min_eligible, rngs.get("network", "topup"))
