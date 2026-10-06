"""Platform safeguards (§4.6).

Milestone 1 implements only the S2 per-recipient cap projection, because the analytic
cap bound (§2.3.7) is part of the E0 verification. S1, S3, S4, S5 and S6 follow at
Milestones 3 and 5.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
