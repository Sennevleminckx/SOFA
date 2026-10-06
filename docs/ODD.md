# SOFA-ABM — ODD protocol (version 2, Milestone 3)

Model description following the ODD protocol (Grimm et al. 2020). Section numbers in brackets refer
to `CLAUDE.md`. Elements marked *(planned, Mn)* are specified but not yet implemented. The model
refuses to run with those switched on (`NotImplementedError`), so no parameter is silently ignored.

---

## 1. Purpose and patterns

**Purpose.** To explain how Self-Organised Funding Allocation (SOFA; Bollen et al. 2014, 2017)
distributes research money when donors respond to incentives and information, and to compare it with
conventional allocation mechanisms. The model is a *toy*: it favours analytic tractability and
transparent mechanisms over realism. The research questions are RQ1–RQ6 [§1]. Version 2 addresses
RQ1 (mechanics under sincere but noisy donors), RQ2 (cartels), RQ3 (transparency) and RQ4 (safeguards).

**Patterns used to evaluate the model.**
1. With a fixed donation matrix W, the closed-form results of [§2.3] hold exactly: steady state, conservation,
   group balance, cartel premium. Verified in E0 (`reports/M1.md`).
2. With sincere donors, concentration rises with the pass-on fraction α [H1].
3. With sincere, perfectly informed donors and α → 0, every allocation tends to equal split.
4. A cartel's aggregate funding obeys the exact identity of [§2.3.5] in the full model; its premium
   stays below 1/(1 − αφ) [H2].
5. A ring cartel has zero pairwise mutual flow, so pairwise discounts cannot see it [§2.3.6, H3].

## 2. Entities, state variables and scales

| Entity | State variables | Static? |
|---|---|---|
| **Researcher** i = 1…N | latent quality q_i (mean 1); field f_i; lab ℓ_i; career stage (early / mid / senior); supervisor (early-career only: a senior in the same lab); visibility v_i; strategy s_i ∈ {sincere, herder, reciprocator, cartel member, deferential}; cartel id; receipts R_i(t); kept amount K_i(t) | q, f, ℓ, stage, strategy static; v static until M4 |
| **Awareness network** | directed Boolean matrix A, A_ij = i is aware of j | static until M4 |
| **Perception** | persistent taste ε_ij ~ N(0, 1) | static |
| **Donation matrix** | W(t), W_ij = share of i's donation to j | rebuilt each year (cached when it cannot change) |
| **Platform** | sees all flows F(t); transparency regime T0–T3; applies safeguards S1–S4; pool balance | — |
| **Collectives** | fields (G = 5, unequal sizes), labs (about 6, nested in fields); cartels (n_C of size k, topology clique / ring / star) | static |

**Scales.** One step = one year. Horizon T = 60 years; outcomes are averaged over the last
T_eval = 10. N = 500 by default (development 300). Money is scale-free (base B = 1).

## 3. Process overview and scheduling

Each year t, in this order [§3]:

1. **Observe** the information permitted by the transparency regime, dated t − 1 (§7.8 below).
   Strategies needing more information than the regime gives fall back to sincere and are counted.
2. **Donation rows:** each agent builds w_i(t) from its effective strategy (§7.9 below).
3. **Row-level safeguards:** S1 COI, then S2 cap. Removed or unplaced shares go to the pool.
4. **Flows:** F_ij(t) = α w_ij(t) R_i(t − 1); then flow-level safeguards S3, then S4 (→ pool).
5. **Update:** R(t) = B·1 + pool(t − 1)/N·1 + α W(t)ᵀ R(t − 1); K(t) = (1 − α) R(t).
6. Production and visibility update *(planned, M4)*.
7. Audits, adaptation, turnover *(planned, M4–M5)*.
8. **Record** metrics.

With `flow_mode = "equilibrium"`, steps 4–5 are replaced by the steady state for the current W,
R = B(I − αWᵀ)⁻¹1 (plus the steady pool), or the exact fixed point when S3/S4 are on. This separates
time scales: money settles within a year.

**Solved versus simulated cells** (M2 review decision). When W cannot change between years (all
strategies static, no feedback), experiments use the steady state directly instead of simulating T
years. `SOFAModel.is_static()` guards this, and each experiment cross-checks one cell by annual
simulation. Herders (under T1+) and reciprocators (under T2+) make W dynamic, and those cells are
always simulated.

## 4. Design concepts

- **Basic principles.** Money circulates on a donation graph. The steady state is Katz/PageRank-type
  centrality of that graph [§2.3.1]. SOFA redistributes and never creates money [§2.3.2].
- **Emergence.** The distribution of K (concentration, rank order, equity across groups) emerges from
  individual donation rows propagated through the network. With fixed W it is analytically known; it
  becomes genuinely emergent only when W responds to the state (M3 onwards).
- **Adaptation.** Herders tilt their ranking towards last year's high receivers. Reciprocators return
  part of their donation to last year's donors. Both respond to the previous year's state. Strategies
  themselves are fixed; imitation and shirking follow at M5.
- **Objectives.** Sincere donors have none beyond their perceived-quality ranking. Cartel members
  follow a fixed collusive routing; no agent optimises explicitly before M5 (best-responders).
- **Learning, prediction.** None.
- **Sensing.** Agents perceive others' quality with persistent noise and reputation bias (§7.2 below),
  and can donate only to researchers they are aware of (cartel members also know each other). What
  else they observe depends on the transparency regime (§7.8 below).
- **Interaction.** Indirect, through money flows on the awareness network.
- **Stochasticity.** Quality, visibility noise, career stages, supervisors, network edges, top-up
  contacts and tastes are random. Each is drawn from its own named sub-stream of a master seed
  (`numpy.random.SeedSequence` with name-derived spawn keys). Changing one mechanism therefore never
  shifts another's draws: common random numbers across scenarios.
- **Collectives.** Fields and labs are fixed and exogenous. Cartels are exogenous at M3: members are
  chosen by `cartel_selection` and route a fixed share φ internally.
- **Observation.** Per year: total K, pool, Gini(K), top-10 % share, allocative efficiency E,
  Spearman ρ(K, q), share ratios by career stage and field, reciprocity index, mean number of
  recipients, year-on-year rank stability, strategy fallbacks, cartel share of K, and (evaluation years)
  mean cycle-return share overall and within cartels. Agent-level R and K are kept for the evaluation
  years. Cartel premium Π and "who pays" are computed by experiments against a CRN counterfactual.

## 5. Initialisation

For a given seed (all draws from named streams):

1. q_i ~ LogNormal(0, σ_q), rescaled to mean 1.
2. Fields by largest-remainder quota from shares 0.35/0.25/0.20/0.12/0.08, in contiguous blocks.
   Agents are exchangeable, so no randomness is needed.
3. Labs: within each field, round(n_f / lab_size) labs of near-equal size.
4. Career stages by quota (0.40/0.35/0.25). One random member per lab is made senior first, so every lab
   has a senior; the remaining quotas are then filled at random.
5. Each early-career researcher gets a random senior from their lab as supervisor.
6. v_i(0) = q_i^κ × (0.5 / 1.0 / 1.5 by stage) × LogNormal(0, σ_v), rescaled to mean 1.
7. Awareness network (§4.2 below), then tastes ε.
8. Roles (from the `strategy` stream, so toggling them never changes any draw above):
   cartels first (n_C, or round(x_C·N/k); members by `cartel_selection`; member order is the ring
   order and the first member is the star hub), then herders and reciprocators among non-members (each
   by the lowest values of its own uniform draw, so the sets are nested as shares grow), then deference
   for all otherwise-sincere early-career researchers when γ_up ≠ 1.
9. R(0) = B·1, pool = 0.

## 6. Input data

None. The model uses no external data. Empirical calibration is out of scope for now [§13].

## 7. Submodels

### 7.1 Awareness network [§4.2]
P(i aware of j) = min(1, s·r_ij·v_j^τ), where r_ij = 10 within a field and 1 between fields (p_in : p_out = 10 : 1).
The scale s is found by bisection so that the expected mean out-degree, including own-lab contacts
(always known), equals d = 40. Agents are always aware of their own lab. Agents with fewer than 5 contacts
outside their lab are topped up at random within their field, so that at least 5 non-COI contacts exist
regardless of whether S1 is on.

*Switch* `in_field_share` (default off). The fixed ratio makes the in-field share of contacts grow with
field size, so small fields are structural net donors. With `in_field_share = x`, p_in and p_out are
calibrated per field (two bisections per field) so that every field expects a share x of its d contacts,
own lab included, inside the field. This is a sensitivity switch for E5.

### 7.2 Perception [§4.3]
q̂_ij = q_j^(1−ω) · v_j^ω · exp(σ_p ε_ij − σ_p²/2). The log-normal factor has mean 1. An optional yearly
term exp(σ_p,t ε_ij,t − σ_p,t²/2) is off by default.

### 7.3 Sincere donation rule [§4.4]
Eligible set E_i = awareness set minus self (minus own lab when S1 is on). Score
S_ij = q̂_ij · μ^[f_i = f_j]. Keep the m = 10 eligible recipients with the highest S_ij; w_ij ∝ S_ij^β. An empty
eligible set sends i's donation to the pool.

### 7.4 Per-recipient cap S2 [§4.6]
Water-filling: clip at c, redistribute the excess proportionally over uncapped recipients in the
row, and repeat. What cannot be placed goes to the pool.

### 7.5 Flows and pool [§2.2, §4.7]
As in step 5. Pooled money is redistributed equally the following year. Because it originates from
R(t − 2), it arrives one year later than direct flows. The burn-in rule is therefore T − T_eval ≥ 10/(−ln α) whenever
a pool-diverting safeguard is on, instead of 5/(−ln α) [§3].

### 7.6 Comparators [§4.10]
A0 equal split (K = B); A1 oracle K ∝ q^{1/(1−θ)} with Σ K = N·B; A2 sincere SOFA with no safeguards
(closed-form steady state). A3 panel review and A4 lottery *(planned, M4)*.

### 7.7 Efficiency [§6]
E = (Y − Y_A0)/(Y_A1 − Y_A0), with Y = Σ q_i (K_i/B)^θ and θ = 0.5. Mechanism costs (c_sofa, panel
overhead) enter from M4, when production is switched on.

### 7.8 Transparency regimes [§4.5]
T0 sealed (own R_i only); T1 totals public (everyone's R_j(t − 1)); T2 donors revealed (T1 plus the
identity and amount of own donors); T3 full ledger (F(t − 1)). Required regimes: herder T1, reciprocator
T2; sincere, cartel and deferential T0. The platform always sees everything.

### 7.9 Strategic donors [§4.4]
- **Herder:** S_ij^herd = S_ij^{1−h} (R_j(t − 1)/mean R)^h, then the sincere rule.
- **Reciprocator:** w_i = (1 − ρ) w_i^sincere + ρ g_i, with g_ij the share of i's receipts last year that
  came from j (sincere if i received nothing).
- **Cartel member:** φ·internal routing (clique: equally to the other members; ring: to the next
  member; star: spokes → hub, hub → spokes equally) + (1 − φ)·the sincere rule over eligible
  non-members, so the internal share is exactly φ. Members know each other (internal routing ignores
  awareness).
- **Deferential (early-career):** sincere, with S_ij multiplied by γ_up for seniors of the own field.

### 7.10 Safeguards S1, S3, S4 [§4.6]
- **S1 COI:** own-lab entries are removed from W (sincere rows already skip them); the removed
  share goes to the pool.
- **S3 mutual-flow discount:** m_ij = min(F_ij, F_ji); both directions are reduced by δ·m_ij.
- **S4 cycle-return discount:** r_i = Σ_{l=2}^{L} α^{l−1}(W^l)_ii, and i's outgoing flows are scaled by
  max(0, 1 − δ_L r_i). The clip is needed because r_i can exceed 1 for tight cycles at high α.
  Because each hop is weighted by α, a k-ring is seen only when L ≥ k, and then only through
  r = α^{k−1}.
- **Steady state with S3/S4:** S3 is nonlinear in R, so the steady state is the exact fixed point of
  the annual map, iterated with same-year pool redistribution (same fixed point, faster convergence).

---

*Change log.* v1 (M2): population, network, perception, sincere strategy, S2 cap, A0–A2.
v1.1 (M2 review): `in_field_share` network switch.
v2 (M3): roles, transparency regimes, herders, reciprocators, cartels, deference, S1, S3, S4;
solved-versus-simulated rule.
