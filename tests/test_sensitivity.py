"""Milestone 6: Latin hypercube sampling and PRCC (§7 E7)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sofa.config import Params
from sofa.sensitivity import Factor, apply_sample, latin_hypercube, prcc, prcc_table

FACTORS = [
    Factor("alpha", 0.1, 0.9),
    Factor("p_in_out_ratio", 1.0, 50.0, "log"),
    Factor("L", 2, 5, "int"),
    Factor("m", 3, 100, "logint"),
    Factor("regime", scale="levels", levels=("T0", "T1", "T2", "T3")),
    Factor("early_visibility", 0.25, 1.0),
    Factor("dummy"),
]


def test_lhs_one_sample_per_stratum():
    n = 50
    X = latin_hypercube([Factor("a"), Factor("b", 2.0, 4.0)], n, seed=1)
    for col, (lo, hi) in (("a", (0.0, 1.0)), ("b", (2.0, 4.0))):
        strata = np.floor((X[col].to_numpy() - lo) / (hi - lo) * n).astype(int)
        assert sorted(strata) == list(range(n))


def test_lhs_ranges_and_types():
    X = latin_hypercube(FACTORS, 400, seed=2)
    assert X.alpha.between(0.1, 0.9).all()
    assert X.p_in_out_ratio.between(1.0, 50.0).all()
    assert (X.p_in_out_ratio < 7.07).mean() == pytest.approx(0.5, abs=0.02)  # log-uniform
    assert set(X.L) == {2, 3, 4, 5}
    assert X.m.between(3, 100).all() and (X.m == X.m.round()).all()
    assert set(X.regime) == {0, 1, 2, 3}
    assert X.regime.value_counts().min() == 100  # equiprobable levels


def test_lhs_reproducible():
    assert latin_hypercube(FACTORS, 30, seed=3).equals(latin_hypercube(FACTORS, 30, seed=3))
    assert not latin_hypercube(FACTORS, 30, seed=3).equals(latin_hypercube(FACTORS, 30, seed=4))


def test_apply_sample_sets_parameters():
    row = latin_hypercube(FACTORS, 5, seed=5).iloc[0]
    p = apply_sample(Params(), FACTORS, row)
    assert p.alpha == pytest.approx(row.alpha)
    assert isinstance(p.L, int) and p.L == row.L
    assert p.regime == ("T0", "T1", "T2", "T3")[int(row.regime)]
    assert p.stage_visibility == (pytest.approx(row.early_visibility), 1.0, 1.5)


def test_factor_validation():
    with pytest.raises(ValueError):
        Factor("x", 1.0, 0.5)
    with pytest.raises(ValueError):
        Factor("x", 0.0, 1.0, "log")
    with pytest.raises(ValueError):
        Factor("x", scale="levels", levels=("a",))


def _toy(n=600, seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.random((n, 4)), columns=["strong", "negative", "weak", "dummy"])
    y = np.exp(4 * X.strong) - 2 * X.negative + 0.3 * X.weak + 0.3 * rng.normal(size=n)
    return X, y


def test_prcc_recovers_signs_and_noise_floor():
    X, y = _toy()
    t = prcc(X, y).set_index("factor")
    assert t.loc["strong", "prcc"] > 0.9
    assert t.loc["negative", "prcc"] < -0.5
    assert 0 < t.loc["weak", "prcc"] < t.loc["strong", "prcc"]
    assert t.loc["dummy", "p_value"] > 0.01
    assert (t.lo <= t.prcc).all() and (t.prcc <= t.hi).all()


def test_prcc_invariant_to_monotone_transforms():
    X, y = _toy()
    a = prcc(X, y).prcc.to_numpy()
    b = prcc(X.assign(strong=X.strong**3), np.exp(y)).prcc.to_numpy()
    np.testing.assert_allclose(a, b, atol=1e-12)


def test_prcc_matches_pearson_for_single_factor():
    """With one factor there is nothing to partial out: PRCC = Spearman correlation."""
    X, y = _toy()
    r = prcc(X[["strong"]], y).prcc.iloc[0]
    assert r == pytest.approx(pd.Series(y).corr(X.strong, method="spearman"))


def test_prcc_drops_missing_and_flags_constant():
    X, y = _toy()
    y = np.asarray(y).copy()
    y[:10] = np.nan
    t = prcc(X.assign(dummy=1.0), y)
    assert (t.n == len(X) - 10).all()
    assert np.isnan(t.set_index("factor").loc["dummy", "prcc"])


def test_prcc_table_bonferroni():
    X, y = _toy()
    t = prcc_table(X, pd.DataFrame({"y": y, "z": -y}), ["y", "z"])
    assert set(t.outcome) == {"y", "z"}
    np.testing.assert_allclose(
        t[t.outcome == "y"].prcc.to_numpy(), -t[t.outcome == "z"].prcc.to_numpy()
    )
    assert t.set_index(["outcome", "factor"]).loc[("y", "strong"), "significant"]
