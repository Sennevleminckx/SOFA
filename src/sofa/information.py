"""Transparency regimes, strategy feasibility and fallbacks (§4.5, §4.4).

What *participants* see (the platform always sees everything):

* T0 sealed — only their own total R_i;
* T1 totals public — everyone's R_j(t−1);
* T2 donors revealed — T1 plus the identity and amount of each of their own donors;
* T3 full ledger — the whole matrix F(t−1).

A strategy that needs more information than the regime gives falls back to sincere,
and the fallback is counted (§4.4).
"""

from __future__ import annotations

import numpy as np

from sofa.population import CARTEL, DEFERENTIAL, HERDER, RECIPROCATOR, SINCERE

REGIMES: tuple[str, ...] = ("T0", "T1", "T2", "T3")

#: Minimum regime (index into REGIMES) each strategy needs to operate (§4.4 table).
REQUIRED_REGIME: dict[int, int] = {
    SINCERE: 0,
    HERDER: 1,  # needs everyone's R_j(t−1)
    RECIPROCATOR: 2,  # needs the identity and amount of own donors
    CARTEL: 0,  # operates under any regime (monitoring depends on the regime, §4.9)
    DEFERENTIAL: 0,
}


def regime_level(regime: str) -> int:
    """Index of ``regime`` in REGIMES (T0 = 0 … T3 = 3)."""
    return REGIMES.index(regime)


def feasible(strategy: int, regime: str) -> bool:
    """Whether ``strategy`` can operate under ``regime``."""
    return regime_level(regime) >= REQUIRED_REGIME[strategy]


def effective_strategies(strategy: np.ndarray, regime: str) -> tuple[np.ndarray, int]:
    """Strategies actually played under ``regime`` and the number of fallbacks.

    Infeasible strategies are replaced by SINCERE.
    """
    level = regime_level(regime)
    need = np.vectorize(REQUIRED_REGIME.__getitem__, otypes=[int])(strategy)
    infeasible = need > level
    eff = np.where(infeasible, SINCERE, strategy)
    return eff, int(infeasible.sum())
