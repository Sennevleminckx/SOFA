"""Comparator allocation mechanisms A0–A4 at the same total budget N·B per year (§4.10).

A0 equal split, A1 oracle, A2 sincere SOFA (Milestone 2); A3 panel review and A4
lottery (Milestone 4). Every comparator spends exactly N·B per year.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from sofa.config import Params
from sofa.metrics import oracle_allocation
from sofa.population import Population

if TYPE_CHECKING:  # the model imports this module, so import it lazily below
    from sofa.model import World

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
    from sofa.model import SOFAModel

    return SOFAModel(a2_params(p), seed=seed, world=world).equilibrium()[1]


# --- A3 panel review and A4 lottery (§4.10) ---------------------------------------------
def panel_scores(
    q: FloatArray, v: FloatArray, omega_p: float, sigma_panel: float, rng: np.random.Generator
) -> FloatArray:
    """Score = (1 − ω_p) log q_i + ω_p log v_i + N(0, σ_panel) (§4.10)."""
    return (1.0 - omega_p) * np.log(q) + omega_p * np.log(v) + rng.normal(0.0, sigma_panel, q.size)


def _grants(funded: np.ndarray, N: int, B: float, b_share: float) -> FloatArray:
    """Equal base b_share·B for all plus the competitive budget split over funded agents.

    The grant is (1 − b_share)·N·B / n_funded, so the budget is exactly N·B.
    """
    K = np.full(N, b_share * B)
    K[funded] += (1.0 - b_share) * N * B / funded.size
    return K


def n_funded(N: int, p_s: float) -> int:
    """Return the number of awards: round(p_s·N), at least 1."""
    return max(1, round(p_s * N))


def a3_panel(scores: FloatArray, p: Params) -> FloatArray:
    """A3: fund the top p_s by panel score with grant B/p_s (single-year awards, §4.10)."""
    N = scores.size
    funded = np.argsort(-scores, kind="stable")[: n_funded(N, p.p_s)]
    return _grants(funded, N, p.B, p.b_share)


def a4_lottery(scores: FloatArray, p: Params, rng: np.random.Generator) -> FloatArray:
    """A4: triage the top p_triage by panel score, then fund a random p_s·N of them (§4.10)."""
    N = scores.size
    n_triage = max(n_funded(N, p.p_s), round(p.p_triage * N))
    triaged = np.argsort(-scores, kind="stable")[:n_triage]
    funded = rng.choice(triaged, size=n_funded(N, p.p_s), replace=False)
    return _grants(funded, N, p.B, p.b_share)


def mechanism_cost(mechanism: str, N: int, p: Params) -> FloatArray:
    """Share of research time spent on the allocation mechanism, per agent (§4.8, §4.10).

    SOFA: c_sofa for everyone. Panel and lottery: everyone applies (c_write) and writes
    n_rev reviews (c_rev each); assumption: equal review load, and the lottery's triage
    needs the same reviews. Equal split and oracle: no cost.
    """
    cost = {
        "sofa": p.c_sofa,
        "panel": p.c_write + p.n_rev * p.c_rev,
        "lottery": p.c_write + p.n_rev * p.c_rev,
        "equal": 0.0,
        "oracle": 0.0,
    }[mechanism]
    return np.full(N, cost)
