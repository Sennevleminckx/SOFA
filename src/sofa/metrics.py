"""Outcome metrics (§6). Milestone 1: the core set used by E0 and later milestones."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats

FloatArray = np.ndarray


# --- Concentration ----------------------------------------------------------------------
def gini(x: FloatArray) -> float:
    """Gini coefficient of a non-negative vector (0 = equal; (n − 1)/n = one holds all)."""
    x = np.sort(np.asarray(x, dtype=float))
    if np.any(x < 0):
        raise ValueError("Gini is defined here for non-negative values only")
    n, total = x.size, x.sum()
    if n == 0 or total == 0:
        return 0.0
    ranks = np.arange(1, n + 1)
    return float(2.0 * (ranks @ x) / (n * total) - (n + 1) / n)


def top_share(x: FloatArray, q: float = 0.10) -> float:
    """Share of the total held by the top fraction ``q`` (default top 10 %)."""
    x = np.sort(np.asarray(x, dtype=float))[::-1]
    n_top = max(1, int(np.ceil(q * x.size)))
    return float(x[:n_top].sum() / x.sum())


def lorenz(x: FloatArray) -> tuple[FloatArray, FloatArray]:
    """Lorenz curve: population share and cumulative share of the total, from (0, 0)."""
    x = np.sort(np.asarray(x, dtype=float))
    cum = np.concatenate([[0.0], np.cumsum(x)]) / x.sum()
    pop = np.linspace(0.0, 1.0, x.size + 1)
    return pop, cum


# --- Efficiency (§6, §2.3.8) ------------------------------------------------------------
def expected_output(
    K: FloatArray, q: FloatArray, theta: float, B: float, cost: FloatArray | float = 0.0
) -> float:
    """Y = Σ ȳ_i with ȳ_i = q_i (K_i/B)^θ (1 − cost_i) (§4.8)."""
    return float(np.sum(q * (np.asarray(K) / B) ** theta * (1.0 - np.asarray(cost))))


def oracle_allocation(q: FloatArray, theta: float, B: float) -> FloatArray:
    """A1: K_i ∝ q_i^{1/(1−θ)} with Σ K = N·B (§2.3.8, §4.10)."""
    z = np.asarray(q, dtype=float) ** (1.0 / (1.0 - theta))
    return z / z.sum() * (z.size * B)


def efficiency(K: FloatArray, q: FloatArray, theta: float, B: float) -> float:
    """E = (Y − Y_A0)/(Y_A1 − Y_A0) (§6). 0 = equal split; 1 = oracle; may be negative."""
    y = expected_output(K, q, theta, B)
    y0 = expected_output(np.full_like(np.asarray(q, float), B), q, theta, B)
    y1 = expected_output(oracle_allocation(q, theta, B), q, theta, B)
    if np.isclose(y1, y0, rtol=1e-12, atol=0.0):
        return float("nan")  # all qualities equal: E undefined
    return (y - y0) / (y1 - y0)


def spearman(a: FloatArray, b: FloatArray) -> float:
    """Spearman rank correlation (e.g. ρ(K, q) or year-on-year stability of K)."""
    return float(stats.spearmanr(a, b).statistic)


# --- Flows ------------------------------------------------------------------------------
def reciprocity_index(F: FloatArray, subset: Sequence[int] | None = None) -> float:
    """Σ min(F_ij, F_ji) / Σ F_ij (§6), optionally restricted to flows within ``subset``."""
    if subset is not None:
        idx = np.asarray(subset)
        F = F[np.ix_(idx, idx)]
    total = F.sum()
    return 0.0 if total == 0 else float(np.minimum(F, F.T).sum() / total)


def mutual_flow(F: FloatArray, subset: Sequence[int] | None = None) -> float:
    """Σ_{i≠j} min(F_ij, F_ji), optionally within ``subset`` (§2.3.6)."""
    if subset is not None:
        idx = np.asarray(subset)
        F = F[np.ix_(idx, idx)]
    M = np.minimum(F, F.T)
    return float(M.sum() - np.trace(M))


def group_flows(F: FloatArray, members: Sequence[int]) -> tuple[float, float]:
    """(inflow into C from outsiders, outflow from C to outsiders) (§2.3.4)."""
    inside = np.zeros(F.shape[0], dtype=bool)
    inside[np.asarray(members)] = True
    inflow = float(F[np.ix_(~inside, inside)].sum())
    outflow = float(F[np.ix_(inside, ~inside)].sum())
    return inflow, outflow


# --- Cartels ----------------------------------------------------------------------------
def cartel_premium(
    K_cartel: FloatArray, K_counterfactual: FloatArray, members: Sequence[int]
) -> float:
    """Π = Σ_C K(cartel) / Σ_C K(no cartel), against a CRN counterfactual (§2.3.5, §6)."""
    idx = np.asarray(members)
    return float(K_cartel[idx].sum() / K_counterfactual[idx].sum())


def premium_bound(alpha: float, phi_eff: float) -> float:
    """Analytic upper bound 1/(1 − α·φ_eff) on the cartel premium (§2.3.5, §2.3.7)."""
    return 1.0 / (1.0 - alpha * phi_eff)


def premium_bound_pool_recapture(alpha: float, phi_max: float, k: int, N: int) -> float:
    """Cap bound amended for pool recapture (proposed amendment to §2.3.7; see reports/M1.md).

    When a capped clique cannot place its excess, the excess goes to the pool and each
    member receives pool/N, so the cartel recaptures a share k/N of it. The effective
    internal share becomes φ′ = φ_max + (1 − φ_max)·k/N. Verified numerically, not proven.
    """
    return premium_bound(alpha, phi_max + (1.0 - phi_max) * k / N)


def who_pays(
    K_cartel: FloatArray,
    K_counterfactual: FloatArray,
    q: FloatArray,
    members: Sequence[int],
    n_bins: int = 10,
) -> FloatArray:
    """Mean change in K among non-members by quality decile (§6, "who pays")."""
    outside = np.ones(len(q), dtype=bool)
    outside[np.asarray(members)] = False
    dK = (K_cartel - K_counterfactual)[outside]
    qo = np.asarray(q)[outside]
    edges = np.quantile(qo, np.linspace(0, 1, n_bins + 1))
    bins = np.clip(np.searchsorted(edges, qo, side="right") - 1, 0, n_bins - 1)
    return np.array([dK[bins == b].mean() if np.any(bins == b) else np.nan for b in range(n_bins)])


# --- Equity (§6) ------------------------------------------------------------------------
def share_ratios(K: FloatArray, labels: np.ndarray, n_groups: int) -> FloatArray:
    """Each group's share of K divided by its population share (1 = proportional; §6)."""
    K = np.asarray(K, dtype=float)
    k_share = np.bincount(labels, weights=K, minlength=n_groups) / K.sum()
    pop_share = np.bincount(labels, minlength=n_groups) / labels.size
    return np.divide(k_share, pop_share, out=np.full(n_groups, np.nan), where=pop_share > 0)


# --- One-stop allocation summary --------------------------------------------------------
def allocation_metrics(
    K: FloatArray,
    q: FloatArray,
    stage: np.ndarray,
    field: np.ndarray,
    theta: float,
    B: float,
    n_fields: int,
) -> dict[str, float]:
    """All per-allocation metrics of §6 that need only K and the population.

    Returns a flat dictionary: total K, Gini, top-10 % share, efficiency E, Spearman
    ρ(K, q), early/mid/senior share ratios and per-field share ratios
    (``field_<g>_ratio``, fields in order of size, largest first).
    """
    stage_r = share_ratios(K, stage, 3)
    field_r = share_ratios(K, field, n_fields)
    out = {
        "total_K": float(np.sum(K)),
        "gini": gini(K),
        "top10_share": top_share(K, 0.10),
        "efficiency": efficiency(K, q, theta, B),
        "spearman_Kq": spearman(K, q) if np.ptp(K) > 0 else float("nan"),
        "early_ratio": float(stage_r[0]),
        "mid_ratio": float(stage_r[1]),
        "senior_ratio": float(stage_r[2]),
    }
    out.update({f"field_{g}_ratio": float(r) for g, r in enumerate(field_r)})
    return out


# --- Output and overhead (§4.8, §6) -----------------------------------------------------
def output_metrics(
    K: FloatArray,
    q: FloatArray,
    ybar: FloatArray,
    y: FloatArray,
    cost: FloatArray,
    theta: float,
    B: float,
) -> dict[str, float]:
    """Compute expected and realised output, overhead and net efficiency (§4.8, §6).

    ``overhead`` is the output forgone through time spent on the mechanism,
    Σ q_i (K_i/B)^θ cost_i. ``efficiency_net`` = (Y_net − Y_A0)/(Y_A1 − Y_A0), with Y_net
    the expected output after overhead and A0/A1 cost-free; it equals ``efficiency`` when
    the mechanism costs nothing. Because Y_A1 − Y_A0 can be small, E magnifies
    differences; ``output_vs_equal`` (Y_net/Y_A0 − 1) gives the same comparison on a plain
    scale, and ``oracle_vs_equal`` the attainable gain.
    """
    gross = expected_output(K, q, theta, B)
    y0 = expected_output(np.full_like(np.asarray(q, float), B), q, theta, B)
    y1 = expected_output(oracle_allocation(q, theta, B), q, theta, B)
    net = float(np.sum(ybar))
    return {
        "output_expected": net,
        "output_realised": float(np.sum(y)),
        "overhead": gross - net,
        "overhead_share": (gross - net) / gross if gross > 0 else float("nan"),
        "efficiency_net": (net - y0) / (y1 - y0) if not np.isclose(y1, y0) else float("nan"),
        "output_vs_equal": net / y0 - 1.0,  # expected output after overhead vs A0, as a ratio
        "oracle_vs_equal": y1 / y0 - 1.0,  # the attainable gain, for scale
    }
