"""SOFAModel: initialisation, the yearly step and ``run()`` (§3). Orchestration only.

The maths lives in the submodules; every step below names the section it follows.
Mechanisms from later milestones raise ``NotImplementedError`` when switched on, so
that no parameter is silently ignored.

From Milestone 4 the model also runs the comparator mechanisms A0, A1, A3 and A4
(``Params.mechanism``) inside the same yearly loop, so that every mechanism faces the
same production, visibility feedback and turnover (§7 E5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.linalg

from sofa import adaptation, baselines, metrics
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
    BEST,
    CARTEL,
    DEFERENTIAL,
    EARLY,
    HERDER,
    RECIPROCATOR,
    SENIOR,
    SHIRKER,
    SINCERE,
    STRATEGY_NAMES,
    Population,
    Roles,
    assign_roles,
    build_population,
)
from sofa.production import (
    expected_output,
    initial_career_age,
    realised_output,
    resample_contacts,
    stage_from_age,
    thin_awareness_column,
    update_visibility,
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

MECHANISMS = ("sofa", "equal", "oracle", "panel", "lottery")  # A2(+), A0, A1, A3, A4


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
    """Raise if a mechanism from a later milestone, or an unsupported combination, is on."""
    pending = {
        "K_max (S6)": p.K_max is not None,
        "turnover with cartels (membership of departing researchers is not specified)": (
            p.turnover and p.cartels
        ),
        "turnover with adaptation (cartel membership of departing researchers)": (
            p.turnover and p.adaptation
        ),
        "adaptation or audits with a non-SOFA mechanism": (
            p.mechanism != "sofa" and (p.adaptation or p.p_audit > 0)
        ),
    }
    on = [name for name, flag in pending.items() if flag]
    if on:
        raise NotImplementedError(f"not implemented: {', '.join(on)}")
    if p.mechanism not in MECHANISMS:
        raise ValueError(f"unknown mechanism {p.mechanism!r}; known: {MECHANISMS}")


@dataclass
class Results:
    """Output of :meth:`SOFAModel.run`."""

    params: Params
    seed: int
    yearly: pd.DataFrame  # one row per year: metrics of §6
    snapshots: dict[int, dict[str, FloatArray]] = field(default_factory=dict)  # eval years
    cartel_log: list[dict] = field(default_factory=list)  # founding/end years (adaptation)

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
    roles
        Pre-assigned strategies and cartels; drawn from the ``strategy`` stream if
        omitted.
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
        p = params
        self.p = p
        self.seed = p.seed if seed is None else int(seed)
        self.rngs = RNGStreams(self.seed)
        self.world = world if world is not None else build_world(p, self.rngs)
        self.pop = self.world.pop
        self.N = self.pop.N
        self.W_override = W_override
        self.t = 0
        self.R = np.full(self.N, p.B)  # §2.2: R(0) = B·1
        self.K = (1.0 - p.alpha) * self.R
        self.F = np.zeros((self.N, self.N))
        self.pool = 0.0
        self._W_cache: FloatArray | None = None
        self._score_cache: tuple[FloatArray, np.ndarray, FloatArray] | None = None
        self._same_field = self.pop.same_field()
        self._same_lab = self.pop.same_lab()
        self.roles = roles if roles is not None else assign_roles(self.pop, p, self.rngs)
        # §4.5: strategies needing more information than the regime gives fall back
        self.eff, self.n_fallbacks = effective_strategies(self.roles.strategy, p.regime)
        self.flow_sg = FlowSafeguards(p.alpha, p.delta, p.delta_L, p.L, p.s4_weighted)
        # --- Dynamic agent state (§4.8). Copies only where something can change, so
        # that the switched-off model shares the world's arrays (and is bit-identical).
        self.q = self.pop.q.copy() if p.turnover else self.pop.q
        self.stage = self.pop.stage.copy()
        self.supervisor = self.pop.supervisor.copy()
        self.v = self.pop.v0.copy()
        self.A = self.world.A.copy() if (p.turnover or p.r_A > 0) else self.world.A
        self.eps = self.world.eps.copy() if p.turnover else self.world.eps
        self.career_age = (
            initial_career_age(self.stage, p.promotion_years, self.rngs.get("production", "career"))
            if p.turnover
            else None
        )
        self.cost = baselines.mechanism_cost(p.mechanism, self.N, p)  # §4.8 overhead
        self.y = np.zeros(self.N)  # last year's realised output
        # --- Behaviour change (§4.9). The registry exists only with adaptation on; then
        # strategies and cartel membership change, otherwise ``roles`` stays fixed.
        self.strategy = self.roles.strategy.copy() if p.adaptation else self.roles.strategy
        self.registry = (
            adaptation.CartelRegistry.from_cartels(self.N, self.roles.cartels)
            if p.adaptation
            else None
        )
        self.W_prev: FloatArray | None = None  # last year's W (best responses, shirking)
        self._lu, self._lu_key = None, None  # LU factors of (I − αW) for Γ rows
        self.sanctions = np.zeros(self.N)

    # --- What can change between years ------------------------------------------------
    def perception_static(self) -> bool:
        """Perceived quality, eligibility and qualities are fixed over time."""
        p = self.p
        return p.sigma_pt == 0.0 and p.lam == 0.0 and not p.turnover and p.r_A == 0.0

    def is_static(self) -> bool:
        """Return True when the allocation cannot change between years.

        For SOFA: W is fixed (static perception, no strategy reacting to last year's
        state, i.e. no herders under T1+ or reciprocators under T2+). Equal split and
        the oracle are static unless turnover changes qualities; panel review and the
        lottery redraw scores every year, so they are never static.
        """
        p = self.p
        if self.W_override is not None:
            return True
        if p.mechanism in ("panel", "lottery"):
            return False
        if p.mechanism in ("equal", "oracle"):
            return not p.turnover
        reactive = np.isin(self.eff, (HERDER, RECIPROCATOR, BEST)).any()
        changing = p.adaptation or p.p_audit > 0 or p.p_peer > 0
        return self.perception_static() and not reactive and not changing

    def gamma_rows(self, W: FloatArray, rows: np.ndarray) -> FloatArray:
        """Rows of the return multipliers Γ = (I − αWᵀ)⁻¹ for W (§4.4).

        (I − αW) is LU-factorised once per W and reused: this year's shirking decisions and
        next year's best responses use the same matrix. Row i solves (I − αW) x = e_i.
        """
        if self._lu_key is not W:
            self._lu = scipy.linalg.lu_factor(np.eye(self.N) - self.p.alpha * W)
            self._lu_key = W
        E = np.zeros((self.N, len(rows)))
        E[np.asarray(rows, dtype=int), np.arange(len(rows))] = 1.0
        return scipy.linalg.lu_solve(self._lu, E).T

    # --- Cartels (static roles, or the registry under adaptation) -------------------------
    def cartel_lists(self) -> list:
        """Member lists of the cartels that route money (two or more members)."""
        if self.registry is None:
            return list(self.roles.cartels)
        return [np.asarray(self.registry.members[c]) for c in self.registry.active()]

    def in_active_cartel(self) -> np.ndarray:
        """Boolean mask of members of cartels that route money."""
        if self.registry is None:
            return self.roles.in_cartel
        mask = np.zeros(self.N, dtype=bool)
        for members in self.cartel_lists():
            mask[members] = True
        return mask

    # --- Donation matrix (§3 steps 1–3) ------------------------------------------------
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
        for members in self.cartel_lists():  # §4.4 cartel topologies
            rows = cartel_member_rows(S, E, members, p.phi, p.m, p.beta, p.topology)
            routing = eff[members] == CARTEL  # shirkers keep their sincere row (§4.9)
            W[members[routing]] = rows[routing]
        best = np.nonzero(eff == BEST)[0]
        if best.size and self.W_prev is not None:  # §4.4: best responses need F(t − 1), T3
            gamma = self.gamma_rows(self.W_prev, best)
            W[best] = adaptation.best_response_rows(gamma, E[best], p.cap)
        return W

    def _scores(self, t: int) -> tuple[FloatArray, np.ndarray, FloatArray]:
        """Sincere scores S, eligibility E and sincere rows; cached while perception is static."""
        if self._score_cache is not None:
            return self._score_cache
        p, eff = self.p, self.eff
        eps_t = yearly_noise(self.N, t, self.rngs) if p.sigma_pt > 0 else None
        qhat = perceived_quality(
            self.q, self.v, self.eps, p.omega, p.sigma_p, eps_t, p.sigma_pt
        )  # §4.3
        S = sincere_scores(qhat, self._same_field, p.mu)  # §4.4
        deferential = eff == DEFERENTIAL
        if deferential.any():  # §4.4 deference to own-field seniors
            S = deference_scores(S, deferential, self.stage == SENIOR, self._same_field, p.gamma_up)
        E = eligible_mask(self.A, self._same_lab if p.coi else None)  # §4.4
        out = (S, E, sincere_rows(S, E, p.m, p.beta))
        if self.perception_static():
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

    # --- Comparator allocations (§4.10) ------------------------------------------------
    def comparator_allocation(self, t: int) -> FloatArray:
        """K(t) for A0, A1, A3 or A4, from the ``baselines`` stream (CRN across mechanisms)."""
        p = self.p
        if p.mechanism == "equal":
            return np.full(self.N, p.B)
        if p.mechanism == "oracle":
            return metrics.oracle_allocation(self.q, p.theta, p.B)
        scores = baselines.panel_scores(
            self.q, self.v, p.omega_p, p.sigma_panel, self.rngs.fresh("baselines", "panel", t)
        )
        if p.mechanism == "panel":
            return baselines.a3_panel(scores, p)
        return baselines.a4_lottery(scores, p, self.rngs.fresh("baselines", "lottery", t))

    # --- One year (§3 process order) ---------------------------------------------------
    def step(self) -> dict[str, float]:
        """Advance one year and return that year's metrics."""
        p = self.p
        self.t += 1
        if p.mechanism == "sofa":
            W = self.donation_matrix(self.t)  # steps 1–3
            sg = self.flow_sg if self.flow_sg.active else None  # step 4: S3/S4
            if p.flow_mode == "annual":  # steps 4–5, §2.2
                st = flow_step(self.R, W, p.alpha, p.B, self.pool, sg)
            else:  # separation of time scales: steady state for the current W (§3)
                st = steady_state_general(W, p.alpha, p.B, sg)
            self.R, self.K, self.F, self.pool = st.R, st.K, st.F, st.pool
        else:
            W = None
            self.K = self.comparator_allocation(self.t)
            self.R, self.pool = self.K, 0.0
        row = self.produce_and_record(W)  # steps 6 and 8
        if W is not None and (p.p_audit > 0 or p.p_peer > 0):  # step 7: S5 and reports
            row.update(self.audit(W))
        if p.adaptation:  # step 7: imitation, shirking, detection, mutation (§4.9)
            row.update(self.adapt(W))
        self.W_prev = W
        self.update_population()  # step 7: turnover and contact resampling
        return row

    # --- Audits and peer reports (§4.6 S5, §4.9) ----------------------------------------
    def audit(self, W: FloatArray) -> dict[str, float]:
        """S5: with probability p_audit the platform sanctions agents with r_i > r_thr.

        Under T3, each routing cartel is also reported by peers with probability p_peer;
        its members are sanctioned and the cartel is dissolved. Sanctions (a share s of
        K) go to the pool, so money is conserved.
        """
        p, t = self.p, self.t
        rng = self.rngs.fresh("adaptation", "audit", t)
        audit_now = rng.random() < p.p_audit
        r = cycle_return_shares(W, p.alpha, p.L, p.s5_weighted) if audit_now else None
        sanc, flagged = adaptation.audit_sanctions(
            self.K, r if r is not None else np.zeros(self.N), p.r_thr, p.s_sanction, audit_now
        )
        reported = 0
        if p.regime == "T3" and p.p_peer > 0:
            for members in self.cartel_lists():
                if rng.random() < p.p_peer:
                    reported += 1
                    sanc[members] = np.maximum(sanc[members], p.s_sanction * self.K[members])
                    if self.registry is not None:
                        c = self.registry.cartel_id[members[0]]
                        for i in self.registry.dissolve(c, t):
                            self.strategy[i] = SINCERE
        self.sanctions = sanc
        self.K = self.K - sanc
        self.pool += float(sanc.sum())
        return {
            "audited": float(audit_now),
            "flagged": float(flagged.sum()),
            "sanctions_total": float(sanc.sum()),
            "cartels_reported": float(reported),
        }

    # --- Behaviour change (§4.9) ----------------------------------------------------------
    def adapt(self, W: FloatArray) -> dict[str, float]:
        """Shirking, detection, imitation and mutation, in that order (§4.9).

        Decisions use the state at the start of the step (payoffs and visible strategies)
        and are then applied in turn. Records strategy shares and cartel statistics.
        """
        p, t, reg = self.p, self.t, self.registry
        if t <= p.T_burn_strategies:
            return self._strategy_stats()
        rng = self.rngs.fresh("adaptation", "imitate", t)
        strat = self.strategy
        in_active = self.in_active_cartel()
        strategic = np.isin(self.eff, (HERDER, RECIPROCATOR, BEST)) | (
            (self.eff == CARTEL) & in_active
        )
        pi = adaptation.payoffs(self.K + self.sanctions, strategic, p.c_m, p.B, self.sanctions)
        # Shirking: revising active members shirk when c_m exceeds their own return loss
        members = np.nonzero((strat == CARTEL) & in_active)[0]
        revising = members[rng.random(members.size) < p.r_imit]
        if revising.size:
            gamma = self.gamma_rows(W, revising)
            W_sincere = self._scores(t)[2]
            loss = adaptation.shirk_return_loss(
                W[revising], W_sincere[revising], self.R[revising], gamma, p.alpha
            )
            strat[revising[p.c_m * p.B > loss]] = SHIRKER
        # Detection by partners: p_det = 1 under T2/T3, p_low under T0/T1
        p_det = adaptation.detection_probability(p.regime, p.p_low)
        shirkers = np.nonzero(strat == SHIRKER)[0]
        detected = shirkers[rng.random(shirkers.size) < p_det]
        for i in detected:
            reg.leave(int(i), t)
            strat[i] = SINCERE
        # Imitation: one random contact, Fermi rule, visible strategies (shirking is secret)
        visible = np.where(
            reg.cartel_id >= 0, CARTEL, np.where(strat == DEFERENTIAL, SINCERE, strat)
        )
        cartel_of = reg.cartel_id.copy()
        learners, models = adaptation.imitation_pairs(self.A, p.r_imit, rng)
        if learners.size:
            prob = adaptation.fermi_probability(
                pi[learners], pi[models], p.kappa_F, float(self.K.mean())
            )
            adopt = rng.random(learners.size) < prob
            for i, j in zip(learners[adopt], models[adopt], strict=True):
                self._switch(int(i), int(visible[j]), int(cartel_of[j]), rng)
        # Mutation
        codes = [STRATEGY_NAMES.index(name) for name in p.evo_strategies]
        for i in np.nonzero(rng.random(self.N) < p.mu_s)[0]:
            self._switch(int(i), int(rng.choice(codes)), -2, rng)
        self.eff, self.n_fallbacks = effective_strategies(strat, p.regime)
        out = self._strategy_stats()
        out["shirk_new"] = float((strat[revising] == SHIRKER).sum()) if revising.size else 0.0
        out["shirk_detected"] = float(detected.size)
        return out

    def _switch(self, i: int, code: int, cartel: int, rng: np.random.Generator) -> None:
        """Agent i adopts strategy ``code``; joining a cartel goes through the registry.

        ``cartel`` ≥ 0 joins that cartel (or founds one if it is full); −2 joins a random
        open cartel, or founds one if none is open.
        """
        reg, p = self.registry, self.p
        if code == CARTEL:
            if cartel == -2:
                open_ = reg.open_cartels(p.k_max)
                cartel = int(rng.choice(open_)) if open_ else -1
            if cartel >= 0 and reg.cartel_id[i] == cartel:
                return
            reg.join(i, cartel, p.k_max, self.t)
            self.strategy[i] = CARTEL
        else:
            reg.leave(i, self.t)
            self.strategy[i] = SINCERE if code == DEFERENTIAL else code

    def _strategy_stats(self) -> dict[str, float]:
        """Strategy shares (true strategies) and cartel statistics."""
        out = {
            f"share_{name}": float(np.mean(self.strategy == code))
            for code, name in enumerate(STRATEGY_NAMES)
        }
        active = self.cartel_lists()
        out["n_cartels"] = float(len(active))
        out["cartel_size_mean"] = float(np.mean([len(m) for m in active])) if active else 0.0
        out["share_in_cartels"] = float(sum(len(m) for m in active) / self.N)
        return out

    def produce_and_record(self, W: FloatArray | None) -> dict[str, float]:
        """Step 6 (§4.8): output and visibility; then the year's metrics (§6).

        Metrics are recorded before turnover so that K and quality refer to the same
        researchers.
        """
        p = self.p
        ybar = expected_output(self.q, self.K, p.B, p.theta, self.cost)
        rng = self.rngs.fresh("production", "output", self.t)
        self.y = realised_output(ybar, p.sigma_y, rng)
        row = self.record(W, ybar)
        self.v = update_visibility(self.v, self.y, p.lam)
        return row

    def update_population(self) -> None:
        """Step 7: turnover (§4.8) and contact resampling (§4.2, Phase 4)."""
        p = self.p
        if p.turnover:
            self._turnover()
        if p.r_A > 0.0:
            self.A = resample_contacts(
                self.A,
                self._same_lab,
                self._same_field,
                self.v,
                p.tau,
                p.p_in_out_ratio,
                p.r_A,
                self.rngs.fresh("network", "resample", self.t),
            )

    def _turnover(self) -> None:
        """Seniors exit at ``exit_rate``; newcomers take their slot as early-career (§4.8).

        A newcomer inherits the slot's lab, field and contact list (the lab's contacts);
        others' awareness of the slot is thinned by the visibility ratio (P ∝ v^τ), the
        own lab always knows them, and their tastes are redrawn. Quality and visibility are
        drawn as at initialisation, with the early-career multiplier (assumptions).
        """
        p, N = self.p, self.N
        rng = self.rngs.fresh("production", "turnover", self.t)
        self.career_age = self.career_age + 1.0
        exits = np.nonzero((self.stage == SENIOR) & (rng.random(N) < p.exit_rate))[0]
        self.stage = stage_from_age(self.career_age, p.promotion_years)
        v_norm = float(
            np.mean(self.pop.q**p.kappa * np.asarray(p.stage_visibility)[self.pop.stage])
        ) * np.exp(0.5 * p.sigma_v**2)  # mean of unnormalised v(0)
        for i in exits:
            q_new = rng.lognormal(0.0, p.sigma_q) / np.exp(0.5 * p.sigma_q**2)
            v_new = q_new**p.kappa * p.stage_visibility[EARLY] * rng.lognormal(0, p.sigma_v)
            v_new /= v_norm
            col = thin_awareness_column(self.A[:, i], v_new, self.v[i], p.tau, rng)
            col |= self._same_lab[:, i]
            col[i] = False
            self.A[:, i] = col
            self.eps[i, :] = rng.standard_normal(N)
            self.eps[:, i] = rng.standard_normal(N)
            self.q[i], self.v[i] = q_new, v_new
            self.career_age[i], self.stage[i] = 0.0, EARLY
        self.eff = self.eff.copy()
        self.eff[exits] = SINCERE
        if p.gamma_up != 1.0:  # deference follows the current career stage
            plain = np.isin(self.eff, (SINCERE, DEFERENTIAL))
            self.eff[plain] = np.where(self.stage[plain] == EARLY, DEFERENTIAL, SINCERE)
        self._reassign_supervisors(rng)

    def _reassign_supervisors(self, rng: np.random.Generator) -> None:
        """Early-career researchers keep a senior supervisor in their lab (else field)."""
        lab, field_ = self.pop.lab, self.pop.field
        sup = np.where(self.stage == EARLY, self.supervisor, -1)
        for i in np.nonzero(self.stage == EARLY)[0]:
            s = sup[i]
            if s >= 0 and self.stage[s] == SENIOR and lab[s] == lab[i]:
                continue
            cands = np.nonzero((lab == lab[i]) & (self.stage == SENIOR))[0]
            if cands.size == 0:
                cands = np.nonzero((field_ == field_[i]) & (self.stage == SENIOR))[0]
            sup[i] = rng.choice(cands) if cands.size else -1
        self.supervisor = sup

    # --- Metrics (§6) -------------------------------------------------------------------
    def record(self, W: FloatArray | None, ybar: FloatArray) -> dict[str, float]:
        """Metrics of §6 for the current year."""
        p = self.p
        row = {"year": self.t, "pool": self.pool}
        row.update(
            metrics.allocation_metrics(
                self.K, self.q, self.stage, self.pop.field, p.theta, p.B, p.G
            )
        )
        row.update(metrics.output_metrics(self.K, self.q, ybar, self.y, self.cost, p.theta, p.B))
        row["visibility_gini"] = metrics.gini(self.v)
        row["reciprocity"] = metrics.reciprocity_index(self.F)
        row["recipients_mean"] = float((W > 0).sum(axis=1).mean()) if W is not None else np.nan
        row["fallbacks"] = self.n_fallbacks
        members = self.in_active_cartel()
        row["cartel_K_share"] = float(self.K[members].sum() / self.K.sum())
        if W is not None and self.t > p.T - p.T_eval:  # §6: cycle-return share (eval years)
            r = cycle_return_shares(W, p.alpha, p.L)
            row["cycle_return_mean"] = float(r.mean())
            row["cycle_return_cartel"] = float(r[members].mean()) if members.any() else np.nan
        return row

    def run(self) -> Results:
        """Run T years; agent snapshots of R and K are kept for the evaluation years."""
        p = self.p
        if p.flow_mode == "annual" and p.mechanism == "sofa":
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
        log = self.registry.survival(self.t) if self.registry is not None else []
        return Results(
            params=p, seed=self.seed, yearly=pd.DataFrame(rows), snapshots=snaps, cartel_log=log
        )

    # --- Shortcut for static allocations ------------------------------------------------
    def equilibrium_state(self) -> tuple[FlowState, FloatArray]:
        """Steady state for the year-1 W, solved rather than simulated (§2.3, M2 decision).

        Closed form without flow-level safeguards, exact fixed point with S3/S4. Raises
        if W can change between years, because the solution would then be meaningless.
        """
        if self.p.mechanism != "sofa":
            raise ValueError("equilibrium_state() applies to SOFA only")
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
        """Metrics of the solved steady state, as one evaluation-year row (static only).

        Used by experiments for cells in which the allocation cannot change (M2 review
        decision): the steady state replaces simulating T years. Raises if dynamic.
        """
        if not self.is_static():
            raise ValueError("the allocation changes between years: simulate instead")
        self.t = self.p.T
        if self.p.mechanism == "sofa":
            st, W = self.equilibrium_state()
            self.R, self.K, self.F, self.pool = st.R, st.K, st.F, st.pool
        else:
            W = None
            self.K = self.comparator_allocation(self.t)
            self.R, self.pool = self.K, 0.0
        row = self.produce_and_record(W)
        row["stability"] = 1.0  # static allocation: ranks never change
        return row


def evaluate(model: SOFAModel) -> dict[str, float]:
    """Solve the cell if the allocation is static, otherwise simulate it (M2 decision).

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
