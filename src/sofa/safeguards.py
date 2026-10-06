"""Platform safeguards (§4.6).

Row level (applied to W after the strategies): S1 conflict-of-interest exclusion and the
S2 per-recipient cap. Flow level (applied to F): S3 pairwise mutual-flow discount, then S4
cycle-return discount. Everything removed goes to the pool, so money is conserved.
S5 audits and S6 receipt ceiling follow at Milestone 5.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sofa.flows import cycle_return_shares

FloatArray = np.ndarray

_TOL = 1e-12


@dataclass(frozen=True)
class CapResult:
    """Outcome of the S2 cap projection."""

    W: FloatArray  # projected rows: max ≤ c, row sums ≤ original
    excess: FloatArray  # per-row share that could not be placed (→ pool)


def cap_project(W: FloatArray, c: float) -> CapResult:
    """Project donation rows onto the per-recipient cap by water-filling (§4.6 S2).

    Entries above ``c`` are clipped to ``c`` and the excess is redistributed
    proportionally over the row's uncapped eligible recipients (those with positive
    weight); this repeats until no entry exceeds ``c``. Excess that cannot be placed is
    returned per row and goes to the pool.

    Properties (tested): max ≤ c; row sums do not increase; the weak order of recipients
    within a row is preserved; the projection is idempotent.
    """
    if not 0.0 < c <= 1.0:
        raise ValueError("cap must lie in (0, 1]")
    W = np.array(W, dtype=float, copy=True)
    original = W.sum(axis=1)
    if c >= 1.0:
        return CapResult(W=W, excess=np.zeros(W.shape[0]))
    eligible = W > 0.0
    capped = np.zeros_like(eligible)
    for _ in range(W.shape[1] + 1):  # each pass caps at least one more entry
        over = c + _TOL < W
        if not over.any():
            break
        excess = np.where(over, W - c, 0.0).sum(axis=1)
        W[over] = c
        capped |= over
        free = eligible & ~capped
        free_mass = np.where(free, W, 0.0).sum(axis=1)
        has_room = (excess > 0) & (free_mass > 0)
        scale = np.divide(excess, free_mass, out=np.zeros_like(excess), where=has_room)
        W += np.where(free, W * scale[:, None], 0.0)
    W = np.minimum(W, c)  # remove sub-tolerance overshoot
    return CapResult(W=W, excess=np.maximum(original - W.sum(axis=1), 0.0))


# --- S1: conflict of interest (row level) -----------------------------------------------
def coi_exclude(W: FloatArray, same_lab: np.ndarray) -> FloatArray:
    """Remove donations to own-lab members (§4.6 S1); the removed share goes to the pool.

    Sincere rows already skip lab members when S1 is on (§4.4), so in practice this
    only removes strategic weight (for example cartel routing inside a lab).
    """
    return np.where(same_lab, 0.0, W)


# --- S3 and S4: flow level ---------------------------------------------------------------
def mutual_flow_discount(F: FloatArray, delta: float) -> tuple[FloatArray, float]:
    """S3: m_ij = min(F_ij, F_ji); each direction is reduced by δ·m_ij (§4.6)."""
    M = np.minimum(F, F.T)
    return F - delta * M, float(delta * M.sum())


def cycle_return_discount(
    F: FloatArray, W: FloatArray, alpha: float, delta_L: float, L: int
) -> tuple[FloatArray, float, FloatArray]:
    """S4: scale i's outgoing flows by (1 − δ_L·r_i), r_i the L-hop return share (§4.6).

    r_i can exceed 1 for tight cycles at high α (for example a pair at α = 0.9, L = 5:
    r = α + α³ = 1.63), so the factor is clipped at 0 (assumption). Returns
    (F_after, leak, r).
    """
    r = cycle_return_shares(W, alpha, L)
    factor = np.clip(1.0 - delta_L * r, 0.0, 1.0)
    F_after = F * factor[:, None]
    return F_after, float(F.sum() - F_after.sum()), r


@dataclass(frozen=True)
class FlowSafeguards:
    """Flow-level platform rules S3 then S4 (§4.6, §4.7); implements ``FlowSafeguard``."""

    alpha: float
    delta: float = 0.0
    delta_L: float = 0.0
    L: int = 3

    @property
    def active(self) -> bool:
        """Whether any flow-level safeguard is switched on."""
        return self.delta > 0.0 or self.delta_L > 0.0

    def apply_flow_level(self, F: FloatArray, W: FloatArray) -> tuple[FloatArray, float]:
        """Return discounted flows and the total diverted to the pool."""
        leak = 0.0
        if self.delta > 0.0:
            F, lk = mutual_flow_discount(F, self.delta)
            leak += lk
        if self.delta_L > 0.0:
            F, lk, _ = cycle_return_discount(F, W, self.alpha, self.delta_L, self.L)
            leak += lk
        return F, leak
