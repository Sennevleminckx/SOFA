"""Comparator allocation mechanisms A0–A4 at the same total budget N·B per year (§4.10).

Milestone 2: A0 equal split, A1 oracle, A2 sincere SOFA. A3 panel review and A4
lottery follow at Milestone 4.
"""

from __future__ import annotations

import numpy as np

from sofa.config import Params
from sofa.metrics import oracle_allocation
from sofa.model import SOFAModel, World
from sofa.population import Population

FloatArray = np.ndarray


def a0_equal_split(pop: Population, p: Params) -> FloatArray:
    """A0: K_i = B (§4.10)."""
    return np.full(pop.N, p.B)


def a1_oracle(pop: Population, p: Params) -> FloatArray:
    """A1: K_i ∝ q_i^{1/(1−θ)}, Σ K = N·B (§2.3.8, §4.10)."""
    return oracle_allocation(pop.q, p.theta, p.B)


def a2_params(p: Params) -> Params:
    """Bollen's scenario: all sincere, T0, every safeguard off (§4.10)."""
    return p.replace(coi=False, cap=1.0, delta=0.0, delta_L=0.0, p_audit=0.0, K_max=None)


def a2_sincere_sofa(p: Params, seed: int, world: World | None = None) -> FloatArray:
    """A2: steady-state K of sincere SOFA with no safeguards (closed form, §2.3.1)."""
    return SOFAModel(a2_params(p), seed=seed, world=world).equilibrium()[1]
