"""Money flows: the annual update, its steady state and return multipliers (§2, §4.7).

All functions are pure. ``W`` is a dense ``(N, N)`` float64 donation-weight matrix with
``W[i, j]`` the share of i's donations going to j; rows sum to 1, or to less than 1 when
a row-level safeguard could not place everything (the remainder goes to the pool).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

FloatArray = np.ndarray


class FlowSafeguard(Protocol):
    """Flow-level safeguard interface (S3/S4, §4.6): returns discounted flows and leakage."""

    def apply_flow_level(self, F: FloatArray, W: FloatArray) -> tuple[FloatArray, float]:
        """Return ``(F_after, money_diverted_to_pool)``."""
        ...


class NoFlowSafeguard:
    """Identity flow-level safeguard (all flow-level safeguards switched off)."""

    def apply_flow_level(self, F: FloatArray, W: FloatArray) -> tuple[FloatArray, float]:
        """Return the flows unchanged and zero leakage."""
        return F, 0.0


@dataclass(frozen=True)
class FlowState:
    """Outcome of one annual flow step (§4.7)."""

    R: FloatArray  # total received in year t
    K: FloatArray  # kept for research in year t
    F: FloatArray  # F[i, j] = flow i → j in year t (after flow-level safeguards)
    pool: float  # money diverted in year t, redistributed equally in year t + 1


def flow_step(
    R_prev: FloatArray,
    W: FloatArray,
    alpha: float,
    B: float,
    pool_prev: float = 0.0,
    sg: FlowSafeguard | None = None,
) -> FlowState:
    """One year of Bollen's lagged update (§2.2, reference sketch §4.7).

    R(t) = B·1 + pool(t−1)/N·1 + α·W(t)ᵀ R(t−1);  K(t) = (1 − α)·R(t).
    """
    N = len(R_prev)
    sg = sg or NoFlowSafeguard()
    row_leak = alpha * R_prev * (1.0 - W.sum(axis=1))  # §4.7: unplaced donations → pool
    F = alpha * W * R_prev[:, None]  # §2.1: F_ij = α w_ij R_i(t−1)
    F, flow_leak = sg.apply_flow_level(F, W)  # §4.6 S3/S4 → pool
    R = B + pool_prev / N + F.sum(axis=0)  # §2.2
    K = (1.0 - alpha) * R  # §2.1
    pool = float(row_leak.sum() + flow_leak)
    return FlowState(R=R, K=K, F=F, pool=pool)


def iterate_fixed_W(
    W: FloatArray,
    alpha: float,
    B: float,
    T: int,
    sg: FlowSafeguard | None = None,
    R0: FloatArray | None = None,
) -> list[FlowState]:
    """Run the annual update for ``T`` years with a fixed ``W`` (verification only, §2.3.1).

    Returns the states for years 1..T. ``R(0) = B·1`` unless ``R0`` is given.
    """
    N = W.shape[0]
    R = np.full(N, B, dtype=float) if R0 is None else np.asarray(R0, dtype=float)
    pool = 0.0
    out: list[FlowState] = []
    for _ in range(T):
        st = flow_step(R, W, alpha, B, pool, sg)
        R, pool = st.R, st.pool
        out.append(st)
    return out


def steady_state(W: FloatArray, alpha: float, B: float) -> tuple[FloatArray, FloatArray]:
    """Closed-form steady state for fixed ``W`` without flow-level safeguards (§2.3.1).

    Solves R* from R* = B·1 + p*/N·1 + αWᵀR*, where the steady pool p* collects the
    unplaced share of rows that sum to less than 1 (§4.7). With full rows p* = 0 and
    R* = B(I − αWᵀ)⁻¹1.

    Returns
    -------
    R, K
        Steady-state receipts and kept amounts.
    """
    N = W.shape[0]
    A = np.eye(N) - alpha * W.T
    one = np.ones(N)
    x = np.linalg.solve(A, one)  # response to a unit top-up for everyone
    leak = alpha * (1.0 - W.sum(axis=1))  # pool per unit of R
    if not np.any(leak > 0):
        R = B * x
    else:
        # R = (B + p/N)·x and p = leakᵀR  →  p = B·leakᵀx / (1 − leakᵀx/N)
        lx = float(leak @ x)
        p = B * lx / (1.0 - lx / N)
        R = (B + p / N) * x
    return R, (1.0 - alpha) * R


def return_multipliers(W: FloatArray, alpha: float) -> FloatArray:
    """Γ = (I − αWᵀ)⁻¹, with Γ[i, j] = ∂R_i per extra unit received by j (§4.4).

    Computed by a linear solve against the identity (one factorisation), never by
    ``np.linalg.inv``.
    """
    N = W.shape[0]
    return np.linalg.solve(np.eye(N) - alpha * W.T, np.eye(N))


def cycle_return_shares(W: FloatArray, alpha: float, L: int = 3) -> FloatArray:
    """r_i = Σ_{l=2}^{L} α^{l−1} (W^l)_ii: share of i's donation returning within L hops (§4.6 S4).

    Truncated power series; costs (L − 1) dense matrix products.
    """
    if L < 2:
        return np.zeros(W.shape[0])
    r = np.zeros(W.shape[0])
    P = W
    for ell in range(2, L + 1):
        P = P @ W  # P = W^ell
        r += alpha ** (ell - 1) * np.diag(P)
    return r


def flows_at_steady_state(W: FloatArray, alpha: float, R: FloatArray) -> FloatArray:
    """F = α·diag(R)·W, the flow matrix implied by receipts R (§2.1)."""
    return alpha * W * R[:, None]
