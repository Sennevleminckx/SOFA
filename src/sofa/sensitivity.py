"""Global sensitivity analysis: Latin hypercube sampling and PRCC (§7 E7).

Partial rank correlation coefficients follow Marino et al. (2008): every factor and the
outcome are rank-transformed; the PRCC of factor j is the correlation between the
residuals of rank(x_j) and rank(y), each regressed linearly on the ranks of all other
factors. PRCC measures the strength of a *monotone* association with the other factors
held fixed, so it is reported together with scatter plots that reveal non-monotone
effects. A dummy factor that the model never reads gives the noise floor.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import qmc

from sofa.config import Params

SCALES = ("linear", "log", "int", "logint", "levels")


@dataclass(frozen=True)
class Factor:
    """One sampled input.

    Parameters
    ----------
    name
        A ``Params`` field, or one of the special names ``early_visibility`` (the
        early-career multiplier of ``stage_visibility``) and ``dummy`` (never read).
    low, high
        Range for numeric scales. Ignored for ``levels``.
    scale
        ``linear`` (uniform), ``log`` (log-uniform), ``int`` (uniform integers,
        inclusive), ``logint`` (log-uniform integers, inclusive) or ``levels``
        (equiprobable categories, coded 0, 1, … in order for the PRCC).
    levels
        Categories for ``levels``.
    """

    name: str
    low: float = 0.0
    high: float = 1.0
    scale: str = "linear"
    levels: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if self.scale not in SCALES:
            raise ValueError(f"unknown scale {self.scale!r}; known: {SCALES}")
        if self.scale == "levels" and len(self.levels) < 2:
            raise ValueError(f"factor {self.name!r} needs at least two levels")
        if self.scale != "levels" and not self.low < self.high:
            raise ValueError(f"factor {self.name!r}: low must be below high")
        if self.scale in ("log", "logint") and self.low <= 0:
            raise ValueError(f"factor {self.name!r}: a log scale needs low > 0")

    def code(self, u: np.ndarray) -> np.ndarray:
        """Map uniform draws u ∈ [0, 1) to the numeric value used in the PRCC."""
        u = np.asarray(u, dtype=float)
        lo, hi = self.low, self.high
        if self.scale == "linear":
            return lo + u * (hi - lo)
        if self.scale == "log":
            return np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))
        if self.scale == "int":
            return np.floor(lo + u * (hi - lo + 1)).clip(lo, hi)
        if self.scale == "logint":
            edges = np.log(lo - 0.5), np.log(hi + 0.5)
            return np.round(np.exp(edges[0] + u * (edges[1] - edges[0]))).clip(lo, hi)
        return np.floor(u * len(self.levels)).clip(0, len(self.levels) - 1)

    def value(self, code: float) -> Any:
        """Return the model value for one numeric code."""
        if self.scale == "levels":
            return self.levels[int(code)]
        if self.scale in ("int", "logint"):
            return int(code)
        return float(code)

    @classmethod
    def from_spec(cls, name: str, spec: Sequence[Any] | Mapping[str, Any]) -> Factor:
        """Build from YAML: ``[low, high]``, ``[low, high, scale]`` or ``{levels: [...]}``."""
        if isinstance(spec, Mapping):
            return cls(name=name, scale="levels", levels=tuple(spec["levels"]))
        if len(spec) == 2:
            return cls(name=name, low=float(spec[0]), high=float(spec[1]))
        return cls(name=name, low=float(spec[0]), high=float(spec[1]), scale=str(spec[2]))


def factors_from_config(specs: Mapping[str, Any]) -> list[Factor]:
    """Factors from a YAML mapping ``name → spec`` (see :meth:`Factor.from_spec`)."""
    return [Factor.from_spec(name, spec) for name, spec in specs.items()]


def latin_hypercube(factors: Sequence[Factor], n: int, seed: int) -> pd.DataFrame:
    """Draw a Latin hypercube of ``n`` samples: one column of numeric codes per factor.

    Each factor's range is cut into n equiprobable strata and every stratum holds exactly
    one sample (McKay et al. 1979), so each margin is covered evenly whatever n is.
    """
    u = qmc.LatinHypercube(d=len(factors), seed=np.random.default_rng(seed)).random(n)
    return pd.DataFrame({f.name: f.code(u[:, j]) for j, f in enumerate(factors)})


def apply_sample(base: Params, factors: Sequence[Factor], row: Mapping[str, float]) -> Params:
    """Parameters for one sample: ``base`` with every factor set to its sampled value."""
    changes: dict[str, Any] = {}
    for f in factors:
        v = f.value(row[f.name])
        if f.name == "dummy":
            continue
        if f.name == "early_visibility":
            changes["stage_visibility"] = (float(v), *base.stage_visibility[1:])
        else:
            changes[f.name] = v
    return base.replace(**changes)


def _residuals(Z: np.ndarray, v: np.ndarray) -> np.ndarray:
    coef, *_ = np.linalg.lstsq(Z, v, rcond=None)
    return v - Z @ coef


def prcc(X: pd.DataFrame, y: pd.Series | np.ndarray, level: float = 0.95) -> pd.DataFrame:
    """Partial rank correlation of each column of X with y (Marino et al. 2008).

    Rows with a missing outcome are dropped. Returns one row per factor with the PRCC,
    a two-sided p-value from t = r·√(df/(1 − r²)), df = n − 2 − p (p = number of other
    factors), and a Fisher-z confidence interval with standard error 1/√(n − 3 − p).
    Constant factors get NaN.
    """
    y = np.asarray(y, dtype=float)
    keep = np.isfinite(y)
    Xr = np.column_stack([stats.rankdata(X[c].to_numpy()[keep]) for c in X.columns])
    yr = stats.rankdata(y[keep])
    n, D = Xr.shape
    df = n - 2 - (D - 1)
    if df < 1:
        raise ValueError(f"PRCC needs more samples than factors (n = {n}, factors = {D})")
    z_crit = stats.norm.ppf(0.5 + level / 2)
    rows = []
    for j, name in enumerate(X.columns):
        if np.ptp(Xr[:, j]) == 0:
            rows.append(dict(factor=name, prcc=np.nan, p_value=np.nan, lo=np.nan, hi=np.nan))
            continue
        Z = np.column_stack([np.ones(n), np.delete(Xr, j, axis=1)])
        rx, ry = _residuals(Z, Xr[:, j]), _residuals(Z, yr)
        denom = np.sqrt((rx @ rx) * (ry @ ry))
        r = float(np.clip(rx @ ry / denom, -1.0, 1.0)) if denom > 0 else np.nan
        if not np.isfinite(r):
            rows.append(dict(factor=name, prcc=np.nan, p_value=np.nan, lo=np.nan, hi=np.nan))
            continue
        t = r * np.sqrt(df / max(1.0 - r * r, 1e-300))
        p = float(2 * stats.t.sf(abs(t), df))
        z, se = np.arctanh(np.clip(r, -0.999999, 0.999999)), 1.0 / np.sqrt(max(n - 3 - (D - 1), 1))
        rows.append(
            dict(
                factor=name,
                prcc=r,
                p_value=p,
                lo=float(np.tanh(z - z_crit * se)),
                hi=float(np.tanh(z + z_crit * se)),
            )
        )
    out = pd.DataFrame(rows)
    out["n"] = n
    return out


def prcc_table(
    design: pd.DataFrame, outcomes: pd.DataFrame, names: Sequence[str], level: float = 0.95
) -> pd.DataFrame:
    """PRCC of every factor for every outcome in ``names``, in long format.

    Adds ``significant``: p below 0.05 after a Bonferroni correction over the factors.
    """
    parts = []
    for name in names:
        t = prcc(design, outcomes[name], level=level)
        t.insert(0, "outcome", name)
        t["significant"] = t.p_value < 0.05 / design.shape[1]
        parts.append(t)
    return pd.concat(parts, ignore_index=True)
