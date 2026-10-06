"""Model parameters (§5): one frozen dataclass, YAML loading and a stable config hash.

Every parameter records its unit, default, explored range and rationale in the field
metadata. "assumption" marks entries without an empirical source. No numbers that
belong here may be hard-coded elsewhere in the package.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _p(default: Any, unit: str, explore: str, rationale: str) -> Any:
    """Declare a parameter with its documentation in the field metadata."""
    meta = {"unit": unit, "explore": explore, "rationale": rationale}
    if isinstance(default, list | dict):
        raise TypeError("use tuples for sequence defaults so that Params stays hashable")
    return field(default=default, metadata=meta)


class HorizonWarning(UserWarning):
    """Raised when T − T_eval is too short for the start-up transient to decay (§3)."""


@dataclass(frozen=True)
class Params:
    """All model parameters (§5). Instances are immutable; use :meth:`replace`."""

    # --- Core -------------------------------------------------------------------------
    N: int = _p(500, "researchers", "200–2000", "§3 default; development scale 300")
    B: float = _p(1.0, "money per researcher per year", "fixed", "scale-free (§2.1)")
    alpha: float = _p(0.5, "fraction", "0.1–0.9", "Bollen et al. 2017 used 0.5")
    T: int = _p(60, "years", "≥ 5/(−ln α) + T_eval", "§3 default horizon")
    T_eval: int = _p(10, "years", "—", "§3: outcomes averaged over the last T_eval years")
    flow_mode: str = _p("annual", "—", "annual, equilibrium", "§3; lagged form of §2.2")

    # --- Population (§4.1) ------------------------------------------------------------
    sigma_q: float = _p(0.5, "log-sd of quality", "0.2–1.0", "assumption")
    G: int = _p(5, "fields", "—", "assumption")
    field_shares: tuple[float, ...] = _p(
        (0.35, 0.25, 0.20, 0.12, 0.08), "fractions", "—", "assumption: unequal field sizes"
    )
    lab_size: int = _p(6, "researchers", "4–8", "assumption")
    stage_shares: tuple[float, float, float] = _p(
        (0.40, 0.35, 0.25), "fractions (early, mid, senior)", "—", "assumption"
    )
    stage_visibility: tuple[float, float, float] = _p(
        (0.5, 1.0, 1.5), "multipliers (early, mid, senior)", "—", "§4.1; assumption"
    )
    sigma_v: float = _p(0.3, "log-sd of visibility noise", "—", "§4.1; assumption")
    kappa: float = _p(1.0, "elasticity", "0–2", "visibility ~ quality^κ; assumption")

    # --- Network (§4.2) ---------------------------------------------------------------
    d: float = _p(40.0, "contacts", "10–100", "mean out-degree of awareness; assumption")
    p_in_out_ratio: float = _p(10.0, "ratio", "1–50", "within- vs between-field; assumption")
    tau: float = _p(1.0, "elasticity", "0–2", "visibility → awareness; assumption")
    min_eligible: int = _p(5, "contacts", "—", "§4.2 guarantee of eligible contacts")
    r_A: float = _p(0.0, "fraction per year", "—", "§4.2 contact resampling (Phase 4)")

    # --- Perception (§4.3) ------------------------------------------------------------
    sigma_p: float = _p(0.5, "log-sd", "0–1.5", "persistent taste noise; assumption")
    sigma_pt: float = _p(0.0, "log-sd", "—", "yearly perception noise; off by default")
    omega: float = _p(0.3, "weight", "0–1", "weight on reputation vs quality; assumption")
    mu: float = _p(1.0, "multiplier", "1–5", "own-field homophily; 1 = off")

    # --- Sincere strategy (§4.4) ------------------------------------------------------
    beta: float = _p(1.0, "exponent", "0.5–3", "w ∝ S^β; assumption")
    m: int = _p(10, "recipients", "3–all", "top-m recipients; assumption")

    # --- Strategic behaviour (§4.4) ---------------------------------------------------
    h: float = _p(0.5, "weight", "0–1", "herding weight; assumption")
    rho: float = _p(0.5, "weight", "0–1", "reciprocity weight; assumption")
    k: int = _p(5, "members", "2–20", "cartel size")
    phi: float = _p(1.0, "fraction", "0–1", "share routed inside the cartel")
    topology: str = _p("clique", "—", "clique, ring, star", "§4.4")
    n_C: int = _p(1, "cartels", "—", "number of cartels (alternative to x_C)")
    x_C: float | None = _p(None, "fraction", "0–0.3", "population share in cartels")
    cartel_selection: str = _p("random", "—", "random, same_field, low_q, high_q", "§4.4")
    gamma_up: float = _p(1.0, "multiplier", "1–5", "deference to seniors; 1 = off")

    # --- Safeguards (§4.6) ------------------------------------------------------------
    coi: bool = _p(False, "switch", "on/off", "S1 conflict-of-interest exclusion")
    cap: float = _p(1.0, "fraction of a donor's budget", "0.05–0.5", "S2; 1 = off")
    delta: float = _p(0.0, "fraction", "0–1", "S3 pairwise mutual-flow discount")
    delta_L: float = _p(0.0, "fraction", "0–1", "S4 cycle-return discount")
    L: int = _p(3, "hops", "2–5", "S4 cycle length")
    p_audit: float = _p(0.0, "probability per year", "—", "S5 audits (Phase 5)")
    r_thr: float = _p(0.2, "return share", "—", "S5 audit threshold")
    s_sanction: float = _p(0.5, "fraction of K", "—", "S5 sanction")
    K_max: float | None = _p(None, "money", "—", "S6 receipt ceiling; None = off")

    # --- Production and feedback (§4.8) -----------------------------------------------
    theta: float = _p(0.5, "elasticity", "0.2–0.9", "diminishing returns to funding")
    sigma_y: float = _p(0.3, "log-sd", "0–0.8", "output noise; assumption")
    lam: float = _p(0.0, "fraction per year", "0–0.5", "visibility feedback; 0 = off")
    c_sofa: float = _p(0.01, "fraction of research time", "0–0.05", "assumption")
    turnover: bool = _p(False, "switch", "on/off", "§4.8 turnover; off by default")
    exit_rate: float = _p(1 / 35, "per year", "—", "senior exit rate (§4.8)")
    promotion_years: tuple[int, int] = _p((5, 12), "years", "—", "early→mid, mid→senior")

    # --- Panel review and lottery (§4.10) ---------------------------------------------
    p_s: float = _p(0.2, "fraction funded", "0.1–0.4", "assumption")
    sigma_panel: float = _p(1.0, "sd of log score", "0.3–2", "assumption")
    omega_p: float = _p(0.3, "weight", "0–1", "panel weight on reputation; assumption")
    c_write: float = _p(0.10, "fraction of output", "0.02–0.25", "Herbert et al. 2013")
    c_rev: float = _p(0.01, "fraction of output per review", "—", "assumption")
    n_rev: int = _p(3, "reviews per proposal", "—", "assumption")
    b_share: float = _p(0.0, "fraction of budget", "—", "equal-base variant of A3")
    p_triage: float = _p(0.5, "fraction", "—", "A4 triage share; assumption")

    # --- Adaptation (§4.9) ------------------------------------------------------------
    r_imit: float = _p(0.1, "fraction per year", "—", "assumption")
    kappa_F: float = _p(0.1, "× mean K", "—", "Fermi noise (Szabó & Tőke 1998)")
    mu_s: float = _p(0.01, "per year", "—", "strategy mutation rate")
    c_m: float = _p(0.05, "× B", "0–0.2", "moral/reputational cost of strategy")
    p_low: float = _p(0.1, "probability", "0–0.5", "shirking detection under T0/T1")
    p_peer: float = _p(0.0, "probability", "—", "peer reporting under T3")
    k_max: int = _p(20, "members", "—", "maximum cartel size under imitation")

    # --- Runs -------------------------------------------------------------------------
    seed: int = _p(0, "—", "—", "master seed for SeedSequence")
    n_seeds: int = _p(50, "seeds per scenario", "development: 10", "§5")

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha < 1.0:
            raise ValueError(f"alpha must lie in [0, 1); got {self.alpha}")
        if self.N < 2:
            raise ValueError("N must be at least 2")
        if self.T_eval < 1 or self.T_eval > self.T:
            raise ValueError("need 1 ≤ T_eval ≤ T")
        for name in ("field_shares", "stage_shares"):
            shares = getattr(self, name)
            if not math.isclose(sum(shares), 1.0, abs_tol=1e-9):
                raise ValueError(f"{name} must sum to 1; got {sum(shares)}")
        if len(self.field_shares) != self.G:
            raise ValueError("field_shares must have length G")
        if not 0.0 < self.cap <= 1.0:
            raise ValueError("cap must lie in (0, 1]")
        if self.flow_mode not in ("annual", "equilibrium"):
            raise ValueError(f"unknown flow_mode {self.flow_mode!r}")
        if self.topology not in ("clique", "ring", "star"):
            raise ValueError(f"unknown topology {self.topology!r}")

    # --- Horizon check (§3) -----------------------------------------------------------
    def diverts_to_pool(self) -> bool:
        """Whether any safeguard is switched on that diverts money to the pool (§4.6)."""
        return (
            self.cap < 1.0
            or self.delta > 0.0
            or self.delta_L > 0.0
            or self.p_audit > 0.0
            or self.K_max is not None
        )

    def min_transient_years(self) -> float:
        """Years needed for the start-up transient to fall below e⁻⁵ (§3, §2.3.1).

        5/(−ln α) without a pool; 10/(−ln α) when a safeguard diverts money to the pool,
        because pooled money arrives one year later and decays at up to √α per year (§3).
        """
        if self.alpha == 0.0:
            return 0.0
        factor = 10.0 if self.diverts_to_pool() else 5.0
        return factor / (-math.log(self.alpha))

    def check_horizon(self) -> None:
        """Warn if the burn-in T − T_eval is too short, as required of ``run()`` (§3)."""
        need = self.min_transient_years()
        if self.T - self.T_eval < need:
            rule = "10/(−ln α) (pool in use)" if self.diverts_to_pool() else "5/(−ln α)"
            warnings.warn(
                f"T − T_eval = {self.T - self.T_eval} years < {rule} = {need:.1f} years "
                f"at α = {self.alpha}: the start-up transient exceeds e⁻⁵ in the evaluation "
                "window.",
                HorizonWarning,
                stacklevel=2,
            )

    # --- Convenience ------------------------------------------------------------------
    def replace(self, **changes: Any) -> Params:
        """Return a copy with ``changes`` applied (validated)."""
        return dataclasses.replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        """Plain dictionary of parameter values (tuples become lists)."""
        return {
            f.name: list(v) if isinstance(v := getattr(self, f.name), tuple) else v
            for f in dataclasses.fields(self)
        }

    def config_hash(self, length: int = 12) -> str:
        """Stable SHA-256 hash of the parameter values (excluding the seed)."""
        d = self.to_dict()
        d.pop("seed")
        blob = json.dumps(d, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:length]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Params:
        """Build from a dictionary, rejecting unknown keys and converting lists to tuples."""
        names = {f.name for f in dataclasses.fields(cls)}
        unknown = set(d) - names
        if unknown:
            raise KeyError(f"unknown parameter(s): {sorted(unknown)}")
        return cls(**{k: tuple(v) if isinstance(v, list) else v for k, v in d.items()})

    @classmethod
    def describe(cls) -> list[dict[str, Any]]:
        """Parameter table: name, default, unit, explored range, rationale."""
        return [
            {"name": f.name, "default": f.default, **f.metadata} for f in dataclasses.fields(cls)
        ]


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    """Load an experiment YAML file.

    The file holds a ``base`` mapping of parameter overrides plus any experiment-specific
    keys (grids, seeds). The returned dictionary has ``base`` converted to :class:`Params`.
    """
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    cfg["base"] = Params.from_dict(cfg.get("base", {}))
    return cfg
