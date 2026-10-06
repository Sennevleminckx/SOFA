"""Behaviour change: imitation, mutation, shirking, audits and best responses (§4.9, §4.6 S5).

Pure functions plus a small mutable :class:`CartelRegistry`. Every random draw comes from
the ``adaptation`` stream (one named sub-stream per purpose and year), so switching
adaptation on never changes population, network, perception, strategy or production draws.

Rules not fixed by the specification are marked "assumption" and listed in reports/M5.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

FloatArray = np.ndarray
IntArray = np.ndarray
BoolArray = np.ndarray


# --- Imitation (§4.9) -------------------------------------------------------------------
def fermi_probability(pi_i: FloatArray, pi_j: FloatArray, kappa_F: float, mean_K: float):
    """P(i adopts j's strategy) = 1 / (1 + exp(−(π_j − π_i) / (κ_F · mean K))) (§4.9)."""
    scale = max(kappa_F * mean_K, 1e-12)
    z = np.clip((pi_j - pi_i) / scale, -500.0, 500.0)
    return 1.0 / (1.0 + np.exp(-z))


def imitation_pairs(A: BoolArray, r_imit: float, rng: np.random.Generator):
    """Learners (a share r_imit, each independently) and one random contact each (§4.9).

    Agents with no contacts do not learn. Returns (learners, models).
    """
    N = A.shape[0]
    learners = np.nonzero(rng.random(N) < r_imit)[0]
    out_l, out_m = [], []
    for i in learners:
        contacts = np.nonzero(A[i])[0]
        contacts = contacts[contacts != i]
        if contacts.size:
            out_l.append(i)
            out_m.append(rng.choice(contacts))
    return np.asarray(out_l, dtype=int), np.asarray(out_m, dtype=int)


def payoffs(
    K: FloatArray, strategic: BoolArray, c_m: float, B: float, sanctions: FloatArray
) -> FloatArray:
    """π_i = K_i − c_m·B·[strategic] − sanctions_i (§4.9; K before sanctions)."""
    return K - c_m * B * strategic - sanctions


# --- Shirking (§4.9) --------------------------------------------------------------------
def shirk_return_loss(
    W_member: FloatArray,
    W_sincere: FloatArray,
    R_prev: FloatArray,
    Gamma: FloatArray,
    alpha: float,
) -> FloatArray:
    """Own K lost by switching from cartel routing to sincere giving (assumption).

    A member's donation α·R_i raises its own receipts only through returns. Redirecting
    it from the cartel row to the sincere row changes own K by
    (1 − α)·α R_i · Σ_j (w_ij^cartel − w_ij^sincere) Γ_ij, with Γ = (I − αWᵀ)⁻¹ the
    return multipliers of last year's W (§4.4). Rows are for the members only; Γ rows
    are taken for the same members.
    """
    return (1.0 - alpha) * alpha * R_prev * np.einsum("ij,ij->i", W_member - W_sincere, Gamma)


# --- Best responses (§4.4, Phase 5) -----------------------------------------------------
def best_response_rows(Gamma_rows: FloatArray, E_rows: BoolArray, cap: float) -> FloatArray:
    """Give to the eligible j with the largest return multiplier Γ_ij, filling up to the cap.

    With cap c the best ⌈1/c⌉ recipients get c each (the last one the remainder), so
    the row sums to 1. Rows with no eligible recipient are zero (→ pool).
    """
    n, N = Gamma_rows.shape
    W = np.zeros((n, N))
    score = np.where(E_rows, Gamma_rows, -np.inf)
    n_rec = int(np.ceil(1.0 / cap - 1e-12))
    order = np.argsort(-score, axis=1, kind="stable")[:, :n_rec]
    for a in range(n):
        left = 1.0
        for j in order[a]:
            if not np.isfinite(score[a, j]) or left <= 1e-15:
                break
            give = min(cap, left)
            W[a, j] = give
            left -= give
    return W


# --- Audits (§4.6 S5) -------------------------------------------------------------------
def audit_sanctions(
    K: FloatArray, r: FloatArray, r_thr: float, s: float, audit_now: bool
) -> tuple[FloatArray, BoolArray]:
    """If the platform audits this year, agents with r_i > r_thr lose a share s of K."""
    flagged = (r > r_thr) if audit_now else np.zeros(K.size, dtype=bool)
    return np.where(flagged, s * K, 0.0), flagged


def detection_probability(regime: str, p_low: float) -> float:
    """p_det = 1 under T2/T3 (donors revealed), p_low under T0/T1 (§4.9)."""
    return 1.0 if regime in ("T2", "T3") else p_low


# --- Cartel registry --------------------------------------------------------------------
@dataclass
class CartelRegistry:
    """Mutable cartel membership with founding and dissolution years.

    ``members[c]`` keeps the routing order (ring order; the first member is the star
    hub). A cartel of one has nobody to route to: its founder donates sincerely and pays
    no moral cost until someone joins (assumption).
    """

    N: int
    members: list[list[int]] = field(default_factory=list)
    founded: list[int] = field(default_factory=list)
    dissolved: list[int | None] = field(default_factory=list)
    cartel_id: IntArray = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.cartel_id is None:
            self.cartel_id = np.full(self.N, -1, dtype=int)

    @classmethod
    def from_cartels(cls, N: int, cartels, year: int = 0) -> CartelRegistry:
        """Registry seeded with the initial cartels (routing order preserved)."""
        reg = cls(N=N)
        for members in cartels:
            reg.members.append([int(i) for i in members])
            reg.founded.append(year)
            reg.dissolved.append(None)
            reg.cartel_id[np.asarray(members)] = len(reg.members) - 1
        return reg

    def alive(self) -> list[int]:
        """Return the indices of cartels not yet dissolved."""
        return [c for c, d in enumerate(self.dissolved) if d is None]

    def active(self) -> list[int]:
        """Living cartels with at least two members (the ones that route money)."""
        return [c for c in self.alive() if len(self.members[c]) >= 2]

    def join(self, i: int, c: int, k_max: int, year: int) -> int:
        """Add i to cartel c, or found a new one if c is full. Returns i's cartel."""
        self.leave(i, year)
        if c >= 0 and self.dissolved[c] is None and len(self.members[c]) < k_max:
            self.members[c].append(i)
            self.cartel_id[i] = c
            return c
        return self.found(i, year)

    def found(self, i: int, year: int) -> int:
        """Start a new cartel with i as its only member."""
        self.leave(i, year)
        self.members.append([i])
        self.founded.append(year)
        self.dissolved.append(None)
        self.cartel_id[i] = len(self.members) - 1
        return self.cartel_id[i]

    def leave(self, i: int, year: int) -> None:
        """Remove i from its cartel; a cartel left empty is dissolved."""
        c = self.cartel_id[i]
        if c < 0:
            return
        self.members[c].remove(i)
        self.cartel_id[i] = -1
        if not self.members[c]:
            self.dissolved[c] = year

    def dissolve(self, c: int, year: int) -> list[int]:
        """Disband cartel c (for example after a peer report); returns its former members."""
        former = list(self.members[c])
        for i in former:
            self.cartel_id[i] = -1
        self.members[c] = []
        self.dissolved[c] = year
        return former

    def open_cartels(self, k_max: int) -> list[int]:
        """Living cartels with room for another member."""
        return [c for c in self.alive() if len(self.members[c]) < k_max]

    def survival(self, end_year: int) -> list[dict]:
        """Return one record per cartel: founding year, end year and whether censored."""
        return [
            {
                "cartel": c,
                "founded": f,
                "ended": d if d is not None else end_year,
                "censored": d is None,
            }
            for c, (f, d) in enumerate(zip(self.founded, self.dissolved, strict=True))
        ]
