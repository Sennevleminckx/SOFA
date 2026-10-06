"""Donation strategies → donation rows (§4.4).

* Milestone 1 (static-W verification, E0): :func:`random_sparse_W`, a stand-in for
  sincere rows, and :func:`cartel_rows`, the cartel topologies (clique, ring, star).
* Milestone 2: the sincere strategy (:func:`eligible_mask`, :func:`sincere_scores`,
  :func:`sincere_rows`).

Herders, reciprocators, deference and best-responders follow at Milestones 3 and 5.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

FloatArray = np.ndarray
IntArray = np.ndarray
BoolArray = np.ndarray

TOPOLOGIES = ("clique", "ring", "star")


# --- Sincere donors (§4.4) ---------------------------------------------------------------
def eligible_mask(A: BoolArray, same_lab: BoolArray | None = None) -> BoolArray:
    """E_i = awareness set minus self, minus own lab when S1 is on (``same_lab`` given)."""
    E = A.copy()
    np.fill_diagonal(E, False)
    if same_lab is not None:
        E &= ~same_lab
    return E


def sincere_scores(qhat: FloatArray, same_field: BoolArray, mu: float) -> FloatArray:
    """S_ij = q̂_ij · μ^[f_i = f_j] (homophily μ ≥ 1; §4.4)."""
    return qhat if mu == 1.0 else np.where(same_field, mu * qhat, qhat)


def sincere_rows(S: FloatArray, E: BoolArray, m: int, beta: float) -> FloatArray:
    """Keep the top-m eligible recipients by S_ij and set w_ij ∝ S_ij^β (§4.4).

    Rows with fewer than m eligible recipients use all of them; rows with none are zero
    (their donations go to the pool). Scores must be positive on eligible entries.
    """
    N = S.shape[0]
    Se = np.where(E, S, 0.0)
    if m < N - 1:
        top = np.argpartition(-Se, m - 1, axis=1)[:, :m]
        keep = np.zeros_like(E)
        np.put_along_axis(keep, top, True, axis=1)
        keep &= E
    else:
        keep = E
    W = np.where(keep, Se**beta if beta != 1.0 else Se, 0.0)
    tot = W.sum(axis=1, keepdims=True)
    return np.divide(W, tot, out=np.zeros_like(W), where=tot > 0)


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
