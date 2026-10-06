"""Shared fixtures: random static W at the §10 reference scale (N = 400)."""

from __future__ import annotations

import numpy as np
import pytest

from sofa.strategies import random_sparse_W

N_REF = 400
D_REF = 40


def make_W(seed: int, N: int = N_REF, d: int = D_REF) -> np.ndarray:
    """Reproducible random sparse row-stochastic W."""
    return random_sparse_W(N, d, np.random.default_rng(seed))


@pytest.fixture(scope="session")
def W400() -> np.ndarray:
    return make_W(12345)


def years_to_converge(alpha: float, tol: float = 1e-14, pool: bool = False) -> int:
    """Years for the start-up transient to fall below ``tol`` (§2.3.1).

    Without a pool the transient decays at rate α. Pooled money arrives one year later
    than direct flows (§2.2, §4.7: pool(t−1) comes from R(t−2)), so the pool channel
    decays at up to √α per year and needs up to twice as many years.
    """
    rate = np.sqrt(alpha) if pool else alpha
    if rate == 0:
        return 2
    return int(np.ceil(np.log(tol) / np.log(rate))) + 5
