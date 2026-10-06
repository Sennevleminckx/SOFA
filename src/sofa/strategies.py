"""Donation strategies → donation rows (§4.4).

Milestone 1 contains only what the static-W verification (E0) needs:

* :func:`random_sparse_W`, a stand-in for sincere rows (random weights on a random
  set of ``d`` recipients), and
* :func:`cartel_rows`, the cartel topologies (clique, ring, star) of §4.4.

The behavioural strategies (sincere, herder, reciprocator, deferential, best-responder)
follow at Milestones 2, 3 and 5.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

FloatArray = np.ndarray
IntArray = np.ndarray

TOPOLOGIES = ("clique", "ring", "star")


def random_sparse_W(N: int, d: int, rng: np.random.Generator) -> FloatArray:
    """Random row-stochastic W with ``d`` recipients per donor and w_ii = 0 (§2.3 checks).

    Recipients are drawn uniformly without replacement; weights are Exp(1), normalised.
    """
    if not 1 <= d <= N - 1:
        raise ValueError("need 1 ≤ d ≤ N − 1")
    W = np.zeros((N, N))
    for i in range(N):
        others = np.delete(np.arange(N), i)
        js = rng.choice(others, size=d, replace=False)
        W[i, js] = rng.exponential(size=d)
    return W / W.sum(axis=1, keepdims=True)


def internal_rows(members: Sequence[int], N: int, topology: str) -> FloatArray:
    """Rows (one per member, in order) of the cartel's internal routing (§4.4).

    Clique: equally to all other members. Ring: all to the next member. Star: the
    first member is the hub; spokes → hub, hub → spokes equally. Each row sums to 1.
    """
    members = list(members)
    k = len(members)
    if k < 2:
        raise ValueError("a cartel needs at least two members")
    if len(set(members)) != k:
        raise ValueError("cartel members must be distinct")
    if topology not in TOPOLOGIES:
        raise ValueError(f"unknown topology {topology!r}")
    out = np.zeros((k, N))
    for a, i in enumerate(members):
        if topology == "clique":
            out[a, [j for j in members if j != i]] = 1.0 / (k - 1)
        elif topology == "ring":
            out[a, members[(a + 1) % k]] = 1.0
        elif a == 0:  # star hub
            out[a, members[1:]] = 1.0 / (k - 1)
        else:  # star spoke
            out[a, members[0]] = 1.0
    return out


def cartel_rows(
    W_sincere: FloatArray,
    members: Sequence[int],
    phi: float,
    topology: str = "clique",
) -> FloatArray:
    """Return a copy of ``W_sincere`` with cartel members' rows replaced (§4.4).

    Member row = φ·internal + (1 − φ)·(sincere row restricted to non-members,
    renormalised), so the internal share is exactly φ (§2.3.5). If a member's sincere
    row has no weight outside the cartel, that (1 − φ) share is unplaced and goes to the
    pool (§4.4: empty eligible set → pool).
    """
    if not 0.0 <= phi <= 1.0:
        raise ValueError("phi must lie in [0, 1]")
    members = list(members)
    N = W_sincere.shape[0]
    W = np.array(W_sincere, dtype=float, copy=True)
    inside = np.zeros(N, dtype=bool)
    inside[members] = True
    internal = internal_rows(members, N, topology)
    for a, i in enumerate(members):
        outside = np.where(inside, 0.0, W_sincere[i])
        mass = outside.sum()
        sincere_part = outside / mass if mass > 0 else np.zeros(N)
        W[i] = phi * internal[a] + (1.0 - phi) * sincere_part
    return W


def choose_members(N: int, k: int, rng: np.random.Generator) -> IntArray:
    """Random cartel membership (``cartel_selection = "random"``, §4.4)."""
    return np.sort(rng.choice(N, size=k, replace=False))
