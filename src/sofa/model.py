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
from sofa.flows import (
    FlowState,
    cycle_return_shares,
    flow_step,
    steady_state_general,
)
from sofa.information import effective_strategies
from sofa.network import build_network
from sofa.perception import draw_taste, perceived_quality, yearly_noise
from sofa.population import (
    DEFERENTIAL,
    HERDER,
    RECIPROCATOR,
    SENIOR,
    Population,
    Roles,
    assign_roles,
    build_population,
)
from sofa.rng import RNGStreams
from sofa.safeguards import FlowSafeguards, cap_project, coi_exclude
from sofa.strategies import (
    cartel_member_rows,
    deference_scores,
    eligible_mask,
    herder_scores,
    reciprocator_rows,
    reciprocity_shares,
    sincere_rows,
    sincere_scores,
)

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
        "p_audit (S5, Milestone 5)": p.p_audit > 0,
        "K_max (S6)": p.K_max is not None,
        "lam (visibility feedback, Milestone 4)": p.lam > 0,
        "turnover (Milestone 4)": p.turnover,
        "r_A (contact resampling, Milestone 4)": p.r_A > 0,
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
    roles
        Pre-assigned strategies and cartels; drawn from the ``strategy`` stream if
        omitted.
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
        roles: Roles | None = None,
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
        self._score_cache: tuple[FloatArray, np.ndarray, FloatArray] | None = None
        self._same_field = self.pop.same_field()
        self._same_lab = self.pop.same_lab()
        self.roles = roles if roles is not None else assign_roles(self.pop, params, self.rngs)
        # §4.5: strategies needing more information than the regime gives fall back
        self.eff, self.n_fallbacks = effective_strategies(self.roles.strategy, params.regime)
        self.flow_sg = FlowSafeguards(
            params.alpha, params.delta, params.delta_L, params.L, params.s4_weighted
        )

    # --- Donation matrix (§3 steps 1–3) ------------------------------------------------
    def is_static(self) -> bool:
        """Return True when W(t) cannot change between years (then it is built once).

        W is dynamic when visibility or perception changes over time, or when any agent
        effectively plays a strategy that reacts to last year's state (herders under
        T1+, reciprocators under T2+).
        """
        p = self.p
        if self.W_override is not None:
            return True
        reactive = np.isin(self.eff, (HERDER, RECIPROCATOR)).any()
        return p.sigma_pt == 0.0 and p.lam == 0.0 and not reactive

    def strategy_rows(self, t: int) -> FloatArray:
        """Donation rows from each agent's effective strategy (§3 steps 1–2, §4.4)."""
        p, eff = self.p, self.eff
        S, E, W_sincere = self._scores(t)
        W = W_sincere.copy()
        herd = eff == HERDER
        if herd.any():  # §4.4: uses everyone's R(t − 1), visible under T1+
            W[herd] = sincere_rows(herder_scores(S[herd], self.R, p.h), E[herd], p.m, p.beta)
        recip = eff == RECIPROCATOR
        if recip.any():  # §4.4: uses own donors in F(t − 1), visible under T2+
            g, received = reciprocity_shares(self.F)
            W[recip] = reciprocator_rows(W[recip], g[recip], received[recip], p.rho)
        for members in self.roles.cartels:  # §4.4 cartel topologies
            W[members] = cartel_member_rows(S, E, members, p.phi, p.m, p.beta, p.topology)
        return W

    def _scores(self, t: int) -> tuple[FloatArray, np.ndarray, FloatArray]:
        """Sincere scores S, eligibility E and sincere rows; cached while perception is static."""
        if self._score_cache is not None:
            return self._score_cache
        p, eff = self.p, self.eff
        eps_t = yearly_noise(self.N, t, self.rngs) if p.sigma_pt > 0 else None
        qhat = perceived_quality(
            self.pop.q, self.v, self.world.eps, p.omega, p.sigma_p, eps_t, p.sigma_pt
        )  # §4.3
        S = sincere_scores(qhat, self._same_field, p.mu)  # §4.4
        deferential = eff == DEFERENTIAL
        if deferential.any():  # §4.4 deference to own-field seniors
            S = deference_scores(
                S, deferential, self.pop.stage == SENIOR, self._same_field, p.gamma_up
            )
        E = eligible_mask(self.world.A, self._same_lab if p.coi else None)  # §4.4
        out = (S, E, sincere_rows(S, E, p.m, p.beta))
        if p.sigma_pt == 0.0 and p.lam == 0.0:  # perception and visibility static
            self._score_cache = out
        return out

    def donation_matrix(self, t: int) -> FloatArray:
        """W(t): strategies (§4.4) then row-level safeguards (§4.6). Cached when static."""
        if self._W_cache is not None:
            return self._W_cache
        p = self.p
        if self.W_override is not None:
            W = np.asarray(self.W_override, dtype=float)
        else:
            W = self.strategy_rows(t)
        if p.coi:
            W = coi_exclude(W, self._same_lab)  # §4.6 S1 → removed share to the pool
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
        sg = self.flow_sg if self.flow_sg.active else None  # step 4: S3/S4
        if p.flow_mode == "annual":  # steps 4–5, §2.2
            st = flow_step(self.R, W, p.alpha, p.B, self.pool, sg)
        else:  # separation of time scales: steady state for the current W (§3)
            st = steady_state_general(W, p.alpha, p.B, sg)
        self.R, self.K, self.F, self.pool = st.R, st.K, st.F, st.pool
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
        row["fallbacks"] = self.n_fallbacks
        members = self.roles.in_cartel
        row["cartel_K_share"] = float(self.K[members].sum() / self.K.sum())
        if self.t > p.T - p.T_eval:  # §6: mean cycle-return share (costly; eval years)
            r = cycle_return_shares(W, p.alpha, p.L)
            row["cycle_return_mean"] = float(r.mean())
            row["cycle_return_cartel"] = float(r[members].mean()) if members.any() else np.nan
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
    def equilibrium_state(self) -> tuple[FlowState, FloatArray]:
        """Steady state for the year-1 W, solved rather than simulated (§2.3, M2 decision).

        Closed form without flow-level safeguards, exact fixed point with S3/S4. Raises
        if W can change between years, because the solution would then be meaningless.
        """
        if not self.is_static():
            raise ValueError("W changes between years: simulate with run() instead")
        W = self.donation_matrix(1)
        sg = self.flow_sg if self.flow_sg.active else None
        return steady_state_general(W, self.p.alpha, self.p.B, sg), W

    def equilibrium(self) -> tuple[FloatArray, FloatArray, FloatArray]:
        """Return (R*, K*, W) of :meth:`equilibrium_state`."""
        st, W = self.equilibrium_state()
        return st.R, st.K, W

    def solve(self) -> dict[str, float]:
        """Metrics of the solved steady state, as one evaluation-year row (static W only).

        Used by experiments for cells in which W cannot change (M2 review decision):
        the steady state replaces simulating T years. Raises if W is dynamic.
        """
        st, W = self.equilibrium_state()
        self.t = self.p.T
        self.R, self.K, self.F, self.pool = st.R, st.K, st.F, st.pool
        row = self.record(W)
        row["stability"] = 1.0  # static W: ranks never change
        return row


def evaluate(model: SOFAModel) -> dict[str, float]:
    """Solve the cell if W is static, otherwise simulate it (M2 review decision).

    Returns the cell's metrics (for simulated cells, means over the last T_eval years)
    plus ``solved`` (1.0 or 0.0) recording which path was taken.
    """
    if model.is_static():
        out = model.solve()
        out["solved"] = 1.0
    else:
        out = model.run().summary()
        out["solved"] = 0.0
    return out
