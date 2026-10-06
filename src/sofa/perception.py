"""Perceived quality q̂_ij (§4.3).

q̂_ij = q_j^(1−ω) · v_j^ω · exp(σ_p ε_ij − σ_p²/2), with ε_ij ~ N(0, 1) a persistent
idiosyncratic taste drawn once. An optional yearly noise term with log-sd σ_p,t is off
by default. The mean-one log-normal factor keeps E[q̂_ij] = q_j^(1−ω) v_j^ω.

The taste matrix ε is drawn as *standard* normals and scaled by σ_p only when used, so
runs that differ only in σ_p share the same draws (common random numbers).
"""

from __future__ import annotations

import numpy as np

from sofa.rng import RNGStreams

FloatArray = np.ndarray


def draw_taste(N: int, rngs: RNGStreams) -> FloatArray:
    """Draw the persistent tastes ε_ij ~ N(0, 1), once per seed (§4.3)."""
    return rngs.get("perception", "taste").standard_normal((N, N))


def perceived_quality(
    q: FloatArray,
    v: FloatArray,
    eps: FloatArray,
    omega: float,
    sigma_p: float,
    eps_t: FloatArray | None = None,
    sigma_pt: float = 0.0,
) -> FloatArray:
    """N×N matrix q̂ with q̂[i, j] = agent i's perception of j (§4.3)."""
    log_hat = (1.0 - omega) * np.log(q) + omega * np.log(v)  # log of q_j^(1−ω) v_j^ω
    noise = sigma_p * eps - 0.5 * sigma_p**2
    if eps_t is not None and sigma_pt > 0.0:
        noise = noise + sigma_pt * eps_t - 0.5 * sigma_pt**2  # optional yearly noise
    return np.exp(log_hat[None, :] + noise)


def yearly_noise(N: int, t: int, rngs: RNGStreams) -> FloatArray:
    """Yearly perception noise draw for year t (only used when σ_p,t > 0)."""
    return rngs.fresh("perception", "yearly", t).standard_normal((N, N))
