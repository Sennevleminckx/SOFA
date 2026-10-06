"""Production, visibility feedback, contact resampling and turnover (§4.8, §4.2 Phase 4).

All functions are pure; ``SOFAModel`` holds the state. Random draws come from the
``production`` stream (output noise, turnover) and the ``network`` stream (contact
resampling), each in its own named sub-stream, so switching these mechanisms on never
changes population, perception or strategy draws.
"""

from __future__ import annotations

import numpy as np

FloatArray = np.ndarray
IntArray = np.ndarray
BoolArray = np.ndarray

EARLY, MID, SENIOR = 0, 1, 2


# --- Output (§4.8) ----------------------------------------------------------------------
def expected_output(
    q: FloatArray, K: FloatArray, B: float, theta: float, cost: FloatArray | float
) -> FloatArray:
    """ȳ_i = q_i · (K_i/B)^θ · (1 − cost_i) (§4.8)."""
    return q * (np.asarray(K) / B) ** theta * (1.0 - np.asarray(cost))


def realised_output(ybar: FloatArray, sigma_y: float, rng: np.random.Generator) -> FloatArray:
    """y_i = ȳ_i · LogNormal(−σ_y²/2, σ_y): mean-preserving noise (§4.8)."""
    if sigma_y == 0.0:
        return ybar.copy()
    return ybar * rng.lognormal(-0.5 * sigma_y**2, sigma_y, ybar.size)


def update_visibility(v: FloatArray, y: FloatArray, lam: float) -> FloatArray:
    """v_i(t+1) = (1 − λ) v_i(t) + λ · y_i(t)/mean(y) (§4.8). λ = 0 leaves v unchanged."""
    if lam == 0.0:
        return v
    my = y.mean()
    return (1.0 - lam) * v + lam * (y / my if my > 0 else np.ones_like(y))


# --- Career stages and turnover (§4.8, optional) ----------------------------------------
def initial_career_age(stage: IntArray, promotion: tuple[int, int], rng: np.random.Generator):
    """Years since entry, uniform within each stage band (assumption).

    early ∈ [0, a₁), mid ∈ [a₁, a₂), senior ∈ [a₂, a₂ + 23) with (a₁, a₂) = ``promotion``;
    23 ≈ the expected remaining senior career at an exit rate of 1/35, truncated.
    """
    a1, a2 = promotion
    lo = np.select([stage == EARLY, stage == MID], [0.0, a1], default=a2)
    hi = np.select([stage == EARLY, stage == MID], [a1, a2], default=a2 + 23.0)
    return lo + rng.random(stage.size) * (hi - lo)


def stage_from_age(age: FloatArray, promotion: tuple[int, int]) -> IntArray:
    """Stage promotion after a₁ and a₂ years (§4.8: 5 and 12)."""
    a1, a2 = promotion
    return np.select([age < a1, age < a2], [EARLY, MID], default=SENIOR)


def thin_awareness_column(
    known_by: BoolArray, v_new: float, v_old: float, tau: float, rng: np.random.Generator
) -> BoolArray:
    """Keep each existing 'aware of' link with probability min(1, (v_new/v_old)^τ).

    Used when a newcomer takes over a departing researcher's slot: awareness is
    P ∝ v^τ (§4.2), so thinning by the visibility ratio keeps the calibrated network
    consistent without recomputing it (assumption).
    """
    keep_p = 1.0 if v_old <= 0 else min(1.0, (v_new / v_old) ** tau)
    return known_by & (rng.random(known_by.size) < keep_p)


# --- Contact resampling (§4.2, Phase 4) ---------------------------------------------------
def resample_contacts(
    A: BoolArray,
    same_lab: BoolArray,
    same_field: BoolArray,
    v: FloatArray,
    tau: float,
    ratio: float,
    r_A: float,
    rng: np.random.Generator,
) -> BoolArray:
    """Each agent drops a fraction r_A of its non-lab contacts and draws as many new ones.

    New contacts are drawn without replacement from non-contacts outside the lab with
    probability ∝ (ratio if same field else 1)·v_j^τ, i.e. by current visibility (§4.2).
    The out-degree, and hence the guarantee of eligible contacts, is preserved.
    """
    if r_A == 0.0:
        return A
    A = A.copy()
    N = A.shape[0]
    attract = v**tau
    for i in range(N):
        contacts = np.nonzero(A[i] & ~same_lab[i])[0]
        n_drop = rng.binomial(contacts.size, r_A)
        if n_drop == 0:
            continue
        A[i, rng.choice(contacts, size=n_drop, replace=False)] = False
        cand = np.nonzero(~A[i] & ~same_lab[i])[0]
        cand = cand[cand != i]
        w = attract[cand] * np.where(same_field[i, cand], ratio, 1.0)
        A[i, rng.choice(cand, size=min(n_drop, cand.size), replace=False, p=w / w.sum())] = True
    return A
