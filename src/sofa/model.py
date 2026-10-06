"""SOFAModel: initialisation, the yearly step and ``run()`` (§3). Orchestration only.

The maths lives in the submodules; every step below names the section it follows.
Mechanisms from later milestones raise ``NotImplementedError`` when switched on, so
that no parameter is silently ignored.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from sofa import metrics
from sofa.config import Params
from sofa.flows import flow_step, flows_at_steady_state, steady_state
from sofa.network import build_network
from sofa.perception import draw_taste, perceived_quality, yearly_noise
from sofa.population import Population, build_population
from sofa.rng import RNGStreams
from sofa.safeguards import cap_project
from sofa.strategies import eligible_mask, sincere_rows, sincere_scores

FloatArray = np.ndarray


@dataclass(frozen=True)
class World:
    """Everything drawn once per seed before the first year: population, network, tastes."""

    pop: Population
    A: np.ndarray  # awareness network (§4.2)
    eps: FloatArray  # persistent perception tastes ε (§4.3)


def build_world(p: Params, rngs: RNGStreams) -> World:
    """Draw population, awareness network and tastes from their own streams (§4.1–4.3)."""
    pop = build_population(p, rngs)
    return World(pop=pop, A=build_network(pop, p, rngs), eps=draw_taste(p.N, rngs))


def check_implemented(p: Params) -> None:
    """Raise if a mechanism from a later milestone is switched on."""
    pending = {
        "coi (S1, Milestone 3)": p.coi,
        "delta (S3, Milestone 3)": p.delta > 0,
        "delta_L (S4, Milestone 3)": p.delta_L > 0,
        "p_audit (S5, Milestone 5)": p.p_audit > 0,
        "K_max (S6)": p.K_max is not None,
        "lam (visibility feedback, Milestone 4)": p.lam > 0,
        "turnover (Milestone 4)": p.turnover,
        "r_A (contact resampling, Milestone 4)": p.r_A > 0,
        "gamma_up (deference, Milestone 3)": p.gamma_up != 1.0,
    }
    on = [name for name, flag in pending.items() if flag]
    if on:
        raise NotImplementedError(f"not implemented yet: {', '.join(on)}")


@dataclass
class Results:
    """Output of :meth:`SOFAModel.run`."""

    params: Params
    seed: int
    yearly: pd.DataFrame  # one row per year: metrics of §6
    snapshots: dict[int, dict[str, FloatArray]] = field(default_factory=dict)  # eval years

    def summary(self) -> dict[str, float]:
        """Mean of each yearly metric over the last T_eval years (§6)."""
        last = self.yearly[self.yearly.year > self.params.T - self.params.T_eval]
        return last.drop(columns="year").mean().to_dict()


class SOFAModel:
    """The SOFA agent-based model (§3).

    Parameters
    ----------
    params
        Model parameters.
    seed
        Master seed; defaults to ``params.seed``.
    world
        Pre-built population, network and tastes. Must have been built with the same
        seed; used to share one world across parameter cells that do not affect it
        (common random numbers). Built from ``seed`` if omitted.
    W_override
        Fixed donation matrix replacing the strategies (switch-off to the static-W
        model of Milestone 1).
    """

    def __init__(
        self,
        params: Params,
        seed: int | None = None,
        world: World | None = None,
        W_override: FloatArray | None = None,
    ) -> None:
        check_implemented(params)
        self.p = params
        self.seed = params.seed if seed is None else int(seed)
        self.rngs = RNGStreams(self.seed)
        self.world = world if world is not None else build_world(params, self.rngs)
        self.pop = self.world.pop
        self.N = self.pop.N
        self.v = self.pop.v0.copy()  # visibility (static until Milestone 4)
        self.W_override = W_override
        self.t = 0
        self.R = np.full(self.N, params.B)  # §2.2: R(0) = B·1
        self.K = (1.0 - params.alpha) * self.R
        self.F = np.zeros((self.N, self.N))
        self.pool = 0.0
        self._W_cache: FloatArray | None = None
        self._same_field = self.pop.same_field()

    # --- Donation matrix (§3 steps 1–3) ------------------------------------------------
    def is_static(self) -> bool:
        """Return True when W(t) cannot change between years (then it is built once)."""
        p = self.p
        return self.W_override is not None or (p.sigma_pt == 0.0 and p.lam == 0.0)

    def donation_matrix(self, t: int) -> FloatArray:
        """W(t): strategies (§4.4) then row-level safeguards (§4.6). Cached when static."""
        if self._W_cache is not None:
            return self._W_cache
        p = self.p
        if self.W_override is not None:
            W = np.asarray(self.W_override, dtype=float)
        else:
            eps_t = yearly_noise(self.N, t, self.rngs) if p.sigma_pt > 0 else None
            qhat = perceived_quality(
                self.pop.q, self.v, self.world.eps, p.omega, p.sigma_p, eps_t, p.sigma_pt
            )  # §4.3
            S = sincere_scores(qhat, self._same_field, p.mu)  # §4.4
            E = eligible_mask(self.world.A)  # §4.4 (S1 from Milestone 3)
            W = sincere_rows(S, E, p.m, p.beta)  # §4.4
        if p.cap < 1.0:
            W = cap_project(W, p.cap).W  # §4.6 S2 → excess to the pool via row sums
        if self.is_static():
            self._W_cache = W
        return W

    # --- One year (§3 process order) ---------------------------------------------------
    def step(self) -> dict[str, float]:
        """Advance one year and return that year's metrics."""
        p = self.p
        self.t += 1
        W = self.donation_matrix(self.t)  # steps 1–3
        if p.flow_mode == "annual":  # steps 4–5, §2.2
            st = flow_step(self.R, W, p.alpha, p.B, self.pool)
            self.R, self.K, self.F, self.pool = st.R, st.K, st.F, st.pool
        else:  # separation of time scales: steady state for the current W (§3)
            self.R, self.K = steady_state(W, p.alpha, p.B)
            self.F = flows_at_steady_state(W, p.alpha, self.R)
            self.pool = float(p.alpha * self.R @ (1.0 - W.sum(axis=1)))
        return self.record(W)  # step 8 (steps 6–7 arrive at Milestones 4–5)

    def record(self, W: FloatArray) -> dict[str, float]:
        """Metrics of §6 for the current year."""
        p = self.p
        row = {"year": self.t, "pool": self.pool}
        row.update(
            metrics.allocation_metrics(
                self.K, self.pop.q, self.pop.stage, self.pop.field, p.theta, p.B, p.G
            )
        )
        row["reciprocity"] = metrics.reciprocity_index(self.F)
        row["recipients_mean"] = float((W > 0).sum(axis=1).mean())
        return row

    def run(self) -> Results:
        """Run T years; agent snapshots of R and K are kept for the evaluation years."""
        p = self.p
        if p.flow_mode == "annual":
            p.check_horizon()  # §3: warn if the start-up transient is not negligible
        rows, snaps = [], {}
        K_prev = None
        for _ in range(p.T):
            row = self.step()
            row["stability"] = (
                metrics.spearman(self.K, K_prev)
                if K_prev is not None and np.ptp(self.K) > 0 and np.ptp(K_prev) > 0
                else float("nan")
            )
            rows.append(row)
            if self.t > p.T - p.T_eval:
                snaps[self.t] = {"R": self.R.copy(), "K": self.K.copy()}
            K_prev = self.K.copy()
        return Results(params=p, seed=self.seed, yearly=pd.DataFrame(rows), snapshots=snaps)

    # --- Shortcut for static W ----------------------------------------------------------
    def equilibrium(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Closed-form steady state for the year-1 W (§2.3.1): returns (R*, K*, W).

        For static W this is what ``run()`` converges to; use it instead of simulating
        when the closed form suffices (§2.3).
        """
        W = self.donation_matrix(1)
        R, K = steady_state(W, self.p.alpha, self.p.B)
        return R, K, W
