"""Smoke tests: each experiment runner end to end on a tiny grid (structure and routing)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from sofa.config import Params
from sofa.experiments import run_e1, run_e2, run_e3, run_e4

BASE = Params(N=120)


def _meta(path):
    return {
        k.decode(): v.decode()
        for k, v in pq.read_schema(path).metadata.items()
        if k.startswith(b"sofa.")
    }


def test_e1_runner(tmp_path):
    cfg = {
        "base": BASE.replace(flow_mode="equilibrium"),
        "alphas": [0.3, 0.7],
        "sigma_ps": [0.5],
        "omegas": [0.0, 0.3],
    }
    path = run_e1(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert set(df.mechanism) == {"A0", "A1", "A2"} and (df.mechanism == "A2").sum() == 4
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


def test_e2_runner(tmp_path):
    cfg = {
        "base": BASE,
        "alphas": [0.5],
        "ks": [2, 5],
        "phis": [1.0],
        "topologies": ["clique", "ring"],
        "selections": ["random", "high_q"],
    }
    path = run_e2(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert len(df) == 6  # k = 2 has no ring
    assert (df.premium <= df.bound + 1e-9).all() and (df.premium > 1).all()
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


def test_e3_runner_routes_static_and_dynamic(tmp_path):
    cfg = {
        "base": BASE.replace(T=30, T_eval=5),
        "regimes": ["T0", "T2"],
        "behaviours": ["herder", "reciprocator", "cartel"],
        "shares": [0.0, 0.25],
    }
    df = pd.read_parquet(run_e3(cfg, 1, tmp_path, n_jobs=1)["cells"])
    s = df.set_index(["behaviour", "share", "regime"])
    assert s.loc[("herder", 0.25, "T0"), "solved"] == 1.0  # fallback → static
    assert s.loc[("herder", 0.25, "T2"), "solved"] == 0.0  # feasible → simulated
    assert s.loc[("reciprocator", 0.25, "T2"), "solved"] == 0.0
    assert s.loc[("cartel", 0.25, "T2"), "solved"] == 1.0
    assert s.loc[("herder", 0.25, "T0"), "fallbacks"] == 30


def test_e4_runner(tmp_path):
    cfg = {
        "base": BASE,
        "cartels": [["clique", 5], ["ring", 5]],
        "safeguards": {"none": {}, "S3": {"delta": 1.0}, "S2": {"cap": 0.1}},
    }
    path = run_e4(cfg, 1, tmp_path, n_jobs=1)["cells"]
    df = pd.read_parquet(path)
    assert len(df) == 9
    ring = df[df.cartel == "ring k=5"].set_index("safeguard")
    assert ring.loc["none", "mutual_flow_in_cartel"] == 0.0
    assert np.isfinite(df.efficiency).all()
    assert float(_meta(path)["sofa.annual_crosscheck_max_rel_diff"]) < 1e-9


@pytest.mark.parametrize("name", ["E1", "E2", "E3", "E4"])
def test_configs_load(name):
    from sofa.config import load_experiment_config
    from sofa.experiments import CONFIG_DIR

    cfg = load_experiment_config(CONFIG_DIR / f"{name}.yaml")
    assert isinstance(cfg["base"], Params)
