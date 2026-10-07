# SOFA-ABM — a toy agent-based model of Self-Organised Funding Allocation

> Project brief and build specification for Claude Code.
> Owner: Senne Vleminckx (University of Antwerp). Language: Python. Write all prose, comments,
> docstrings and figure labels in **UK English**.

---

## 0. How to work on this project

- Read this whole file before writing code. It is the single source of truth; if something here is
  ambiguous or looks wrong, **ask** rather than improvise, and propose an amendment to this file.
- Build in the milestones of §11. At every **checkpoint**: run the full test suite, run the
  milestone's experiment at development scale, write `reports/M<x>.md` (what was built, key numbers,
  figures, anything surprising or unresolved), then **stop and wait for review**.
- This is a *toy* model. Prefer clarity and analytic tractability over realism. Every mechanism added
  after Milestone 1 must have a switch that recovers the simpler model, plus a test showing that the
  switched-off model reproduces earlier results exactly (same seed → identical output).
- Never tune parameters to make a hypothesis in §8 come true. Report null and unexpected results
  plainly.

---

## 1. Purpose and research questions

Bollen et al. (2014, 2017) proposed **SOFA** (Self-Organised Funding Allocation): every researcher
receives an equal, unconditional base amount each year and must pass a fixed fraction of *everything
they receive* on to other researchers of their choice. Money circulates and, in theory, concentrates on
the researchers the community values most — no proposals, no panels.

Their validation used citations as a stand-in for donations, so donors were sincere by construction.
This model asks what happens when donors respond to **incentives and information**.

- **RQ1 — Mechanics.** With sincere but noisy donors, how do concentration (Gini) and allocative
  efficiency depend on the pass-on fraction α, perception noise, and reliance on reputation versus
  actual quality?
- **RQ2 — Manipulability.** How much can collusive groups (cartels) gain, and how does this depend on
  α, cartel size, internal share and topology (clique, ring, star)?
- **RQ3 — Information.** How does transparency of the donation ledger (sealed → fully public) change
  which strategic behaviours are feasible and stable (herding, reciprocity, cartels)?
- **RQ4 — Safeguards.** Which rules (conflict-of-interest exclusion, per-recipient caps, mutual-flow
  and cycle discounts, audits, choice of α) reduce gaming, and what do they cost in efficiency when
  everyone is sincere?
- **RQ5 — Feedback and equity.** With a reputation feedback loop (funding → output → visibility →
  donations), does SOFA amplify the Matthew effect, and what happens to early-career researchers and
  small fields?
- **RQ6 — Comparison.** How does SOFA compare with equal split, an oracle allocation, noisy panel
  review and a lottery, at the same total budget and including overhead costs?

---

## 2. The mechanism and what is already known analytically

### 2.1 Notation

| Symbol | Meaning |
|---|---|
| N | number of researchers, indexed i, j |
| B | base amount per researcher per year (scale-free; default 1) |
| α | pass-on fraction, 0 ≤ α < 1 (Bollen used 0.5) |
| W(t) | N×N donation-weight matrix; row i = how i splits their donations; w_ii = 0; rows sum to 1 (or to less than 1 when a safeguard diverts money, see §4.6) |
| R_i(t) | total received by i in year t (base + donations + pool top-up) |
| K_i(t) = (1 − α) R_i(t) | amount i keeps and spends on research in year t |
| α R_i(t) | amount i must donate in year t + 1 |
| F_ij(t) = α w_ij(t) R_i(t − 1) | money flowing from i to j in year t |

### 2.2 Annual update (Bollen's lagged form)

At the start of year t, agents choose W(t) using information up to t − 1, then donate what they
received last year:

```
R(t) = B·1 + pool(t−1)/N · 1 + α · W(t)ᵀ R(t−1)        R(0) = B·1
K(t) = (1 − α) · R(t)
```

`pool(t−1)` is money diverted by safeguards in year t − 1, redistributed equally as a base top-up.

### 2.3 Verified analytic results (use these as test targets)

These were checked numerically (N = 400, random sparse W) before writing this spec.

1. **Steady state for fixed W.** R* = B (I − αWᵀ)⁻¹ 1 and K* = (1 − α) R*. This is Katz/PageRank-type
   centrality of the donation graph. The annual iteration converges geometrically at rate α, so
   burn-in must scale with −1/ln α (≈ 60 years for 1e-6 precision at α = 0.8).
2. **Conservation.** If rows of W sum to 1, Σ K* = N·B exactly: SOFA redistributes, it never creates
   money. With a pool, Σ K* = N·B still holds at steady state.
3. **Degenerate cases.** α = 0 → K = B for everyone. Uniform W (w_ij = 1/(N−1)) → K = B for everyone.
4. **Group balance identity.** For *any* subset C, at steady state:
   Σ_{i∈C} K_i = |C|·B + (inflow into C) − (outflow from C), with flows as defined by F. (Exact.)
5. **Cartel premium.** Let a cartel C of size k direct a share φ of its donations internally (the rest
   sincerely), with others' behaviour unchanged. Relative to the same seed without the cartel:
   ```
   Π = Σ_{i∈C} K_i(cartel) / Σ_{i∈C} K_i(no cartel) ≈ 1 / (1 − αφ)
   ```
   independent of the members' quality. It is an upper bound, exact as k/N → 0, provided the inflow
   from outsiders does not rise. Larger cartels fall
   slightly short because their lost outflow lowers outsiders' receipts and so the cartel's own inflow.
   (M3 review.) With φ < 1 in a heterogeneous network, internal equalisation can redirect members'
   outside giving towards recipients who feed the cartel, raising I_C. The full model exceeds the bound
   in 0.3 % of E2 cells, by ≤ 0.8 %. The exact form below always holds; the static-W test of §10 is
   unaffected.
   **The bound holds only without the reputation feedback loop (M6 review).** With feedback (λ > 0,
   ω > 0), the cartel's extra funding raises its output, then its visibility, then sincere outsiders'
   donations, so I_C can rise without limit. E7 finds Π above the bound in 19 % of the hypercube, up to
   12×; with λ = 0 or ω = 0 the same samples fall back below it.
   This shortfall grows with α and k/N. Numerical check at N = 400, φ = 1: α = 0.5 → Π = 1.996 / 1.975 /
   1.946 for k = 2 / 5 / 10 (prediction 2.00); α = 0.8 → worst-case shortfall 2 % / 7 % / 10 %;
   α = 0.9 → 4 % / 11 % / 19 %.
   **Exact form:** with I_C the realised inflow from outsiders under the cartel,
   Σ_{i∈C} K_i = (1 − α)(k·B + I_C) / (1 − αφ). This requires every member to route exactly φ
   internally, so the sincere remainder must exclude fellow members.
   **α is therefore both the "signal strength" lever and the "manipulability" lever.**
6. **Rings evade pairwise safeguards.** A ring cartel (i₁ → i₂ → … → i_k → i₁) with φ = 1 has
   *zero* pairwise mutual flow, yet obtains the same premium (≈ 1.96 at α = 0.5, k = 5).
7. **Per-recipient cap.** With cap c on the share of a donor's budget that any single recipient may
   get, a clique can route at most φ_max = min(1, (k − 1)c) internally, so Π ≤ 1/(1 − α·φ_max)
   when the capped excess is redistributed outside the cartel. If the excess instead goes to the
   pool, members recapture k/N of it through the equal pool top-up, and
   φ′ = φ_max + (1 − φ_max)·k/N replaces φ_max (verified numerically, not proven; see reports/M1.md).
8. **Oracle allocation.** With expected output y_i = q_i K_i^θ (0 < θ < 1) and Σ K = N·B, the
   output-maximising allocation is K_i ∝ q_i^{1/(1−θ)}.

The ABM earns its keep **only** where W becomes endogenous: agents choosing whom to fund in response
to incentives, information and a reputation feedback loop. Mechanics with fixed W must never be
simulated where the closed form suffices; use the closed form as the reference.

**Decision (M2 review): solve, with a guard.** Any experiment cell in which W cannot change between
years uses the steady state directly: the closed form, or the exact fixed point when a nonlinear
flow-level safeguard (S3) is on. It never simulates T years. The runner must check
`SOFAModel.is_static()` and raise if W can change. Each such experiment also simulates at least one
cell in annual mode and reports the largest difference from the solved result. Cells in which agents
respond to last year's state (herders, reciprocators, feedback, adaptation) are always simulated.

---

## 3. Model overview (ODD-style summary)

- **Entities.** Researchers (agents). Collectives: fields, labs, cartels. A platform (the funder) that
  sees all flows, applies safeguards and may audit.
- **Scales.** One step = one year. Default horizon T = 60 years; outcomes averaged over the last
  T_eval = 10 years. Require T − T_eval ≥ 5/(−ln α) so the start-up transient is below e⁻⁵ ≈ 0.7 %
  (≈ 22 years at α = 0.8, ≈ 48 at α = 0.9); `run()` should raise a warning otherwise. When any
  safeguard diverts money to the pool, require T − T_eval ≥ 10/(−ln α) instead (≈ 45 years at
  α = 0.8, ≈ 95 at α = 0.9): pooled money arrives one year later than direct flows (§2.2, §4.7), so
  the pool channel decays at up to √α per year (see reports/M1.md). Default N = 500 (development 300; maximum about 2000 with dense matrices).
- **Process order within a year t:**
  1. Observe information permitted by the transparency regime (§4.5), all dated t − 1.
  2. Each agent builds its donation row w_i(t) from its strategy (§4.4).
  3. Platform applies row-level safeguards (COI, cap) → W(t); diverted money → pool.
  4. Compute flows F(t); platform applies flow-level safeguards (mutual/cycle discount) → pool.
  5. Update R(t), K(t) (§2.2).
  6. Production y_i(t) and visibility update (§4.8; off until Phase 4).
  7. Optional: audit and sanctions, strategy adaptation, turnover (§4.9).
  8. Record metrics.
- **Flow modes.** `flow_mode="annual"` (default, §2.2) or `flow_mode="equilibrium"` (solve the steady
  state for the current W each year; separation of time scales, useful for strategy experiments).

A full ODD protocol (Grimm et al. 2020) is to be maintained in `docs/ODD.md` from Milestone 2 onward.

---

## 4. Submodels

### 4.1 Population (static in Phases 1–3)

- **Latent quality** q_i ~ LogNormal(0, σ_q), rescaled to mean 1. It is unobserved by agents and is
  what an ideal allocation would track.
- **Field** f_i ∈ {1..G}, unequal sizes (default G = 5, shares 0.35/0.25/0.20/0.12/0.08).
- **Lab** ℓ_i: labs of about 6 researchers nested in fields (the conflict-of-interest unit).
- **Career stage** ∈ {early, mid, senior}, shares 0.40/0.35/0.25. Each early-career researcher has a
  supervisor: a senior in the same lab.
- **Visibility** v_i(0) = q_i^κ × stage multiplier (0.5/1.0/1.5) × LogNormal(0, 0.3), rescaled to mean 1.
- **Strategy** s_i (§4.4), assigned from its own RNG stream so that toggling strategies never changes
  any other draw.

### 4.2 Awareness network (who i can donate to)

Directed. P(i aware of j) = min(1, p_f · v_j^τ), with p_f = p_in for the same field and p_out
otherwise. p_in : p_out = 10 : 1, scaled so that mean out-degree ≈ d = 40. Always aware of own lab.
Guarantee at least 5 eligible (non-COI) contacts per agent by topping up at random within the field.
Switch `in_field_share` (default `None`): with a fixed p_in : p_out ratio, the in-field share of
contacts grows with field size (≈ 55 % in the 8 % field, ≈ 85 % in the 35 % field at N = 500), so small
fields are structural net donors. Setting `in_field_share = x` instead calibrates p_in and p_out per
field so that every field expects a share x of its d contacts inside the field (own lab included).
Use x = 0.8 as a sensitivity run in E5 (agreed at the M2 review). Fields too small to supply x·d
contacts saturate and `build_network` warns.
Static in Phases 1–3. In Phase 4, a fraction r_A of each agent's contacts is resampled each year
using current visibility.

### 4.3 Perception

Agent i's perceived quality of j:

```
q̂_ij = q_j^(1−ω) · v_j^ω · exp(σ_p ε_ij − σ_p²/2),    ε_ij ~ N(0, 1)
```

ε_ij is a persistent idiosyncratic taste, drawn once. An optional yearly noise term (σ_p,t) is off
by default. ω is the weight on reputation versus actual quality.

### 4.4 Donation strategies

All rules act on eligible recipients E_i = awareness set minus self minus COI-excluded (when S1 is on).
Weights are normalised to sum to 1 over E_i. If E_i is empty, i's donation goes to the pool.

| Strategy | Rule | Needs regime |
|---|---|---|
| **Sincere** | S_ij = q̂_ij · μ^{[f_i = f_j]} (homophily μ ≥ 1); keep top-m by S_ij; w_ij ∝ S_ij^β | T0+ |
| **Herder** | S_ij^herd = S_ij^{1−h} · (R_j(t−1)/mean R)^h, then as sincere | T1+ |
| **Reciprocator** | w_i = (1−ρ) w_i^sincere + ρ g_i, where g_ij = share of i's received donations last year that came from j (fall back to sincere if i received none) | T2+ |
| **Cartel member** | share φ routed inside the cartel by topology, (1−φ) sincere over non-members only (so the internal share is exactly φ). *Clique*: equally to all other members. *Ring*: all to the next member. *Star*: spokes → hub; hub → spokes equally | T0+ to operate; monitoring depends on regime (§4.9) |
| **Deferential** (early-career only) | sincere with an extra multiplier γ_up on seniors of the own field | T0+ |
| **Best-responder** (Phase 5, optional) | give to the eligible j with the largest return multiplier Γ_ij, where Γ = (I − αW(t−1)ᵀ)⁻¹ (Γ_ij = ∂R_i per extra unit received by j), filling up to the cap | T3 |

If a strategy is not feasible under the current regime, the agent falls back to sincere and the
fallback is counted in the metrics.

Cartel formation (`cartel_selection`): `random` (default) | `same_field` | `low_q` | `high_q`.
Membership can be set by a number of cartels n_C of size k, or by a population share x_C.

### 4.5 Transparency regimes (what *participants* see; the platform always sees everything)

| Regime | Participants observe |
|---|---|
| **T0 sealed** | only their own total R_i |
| **T1 totals public** | everyone's R_j(t−1) |
| **T2 donors revealed** | T1 + the identity and amount of each of their own donors |
| **T3 full ledger** | the whole matrix F(t−1) |

### 4.6 Safeguards (platform rules; each independently switchable)

- **S1 COI exclusion.** No donations to own lab members (optional extension: plus 2 random
  "co-authors" in the field).
- **S2 Per-recipient cap c.** No recipient may get more than share c of a donor's budget. Apply by
  water-filling: clip at c and redistribute the excess proportionally over uncapped eligible
  recipients; repeat until feasible. Whatever cannot be placed goes to the pool. This implies at
  least ⌈1/c⌉ recipients.
- **S3 Pairwise mutual-flow discount δ.** For each pair, m_ij = min(F_ij, F_ji); each direction is
  reduced by δ·m_ij and the difference goes to the pool.
- **S4 Cycle-return discount (δ_L, L).** For donor i, the return share
  r_i = Σ_{l=2}^{L} α^{l−1} (W^l)_ii is the fraction of a unit donated by i that comes back to i
  within L hops (each onward hop passes on α). Scale i's outgoing flows by (1 − δ_L · r_i); the
  reduction goes to the pool. Default L = 3. It targets rings that S3 misses.
  Switch `s4_weighted` (default True = the α-weighted rule above). Because each hop is weighted by α,
  a k-ring is seen only when L ≥ k, and then only through r = α^{k−1}. With `s4_weighted = False`,
  r_i = Σ_{l=2}^{L} (W^l)_ii is the unweighted probability that a unit returns within L hops, so a
  k-ring with φ = 1 is seen fully (r = 1) when L ≥ k (M3 review; still needs L ≥ k).
- **S5 Audit and sanction (Phase 5).** Each year, with probability p_audit, the platform flags agents
  with r_i > r_thr (or cartel-level anomalies) and removes a fraction s of their K, which goes to the
  pool. Switch `s5_weighted` (default False, M5 review): the audit flags on the *unweighted* return
  share of S4. An audit asks whether a donor's routing is circular, which the unweighted share
  measures directly; the α-weighted share falls with α, so a fixed r_thr would mean a different
  thing at every α, and at r_thr = 0.2 it misses 5-member cliques (r ≈ 0.17 at α = 0.5).
  `s5_weighted = True` restores the α-weighted share.
- **S6 Receipt ceiling K_max** (optional): excess K goes to the pool.
- **α itself** is treated as a policy lever in every experiment.

Every safeguard must preserve conservation (Σ K + change in pool balances to N·B at steady state).

### 4.7 Flow step (reference implementation sketch)

```python
def flow_step(R_prev, W, alpha, B, pool_prev, sg):
    """W: rows sum to 1, or less when row-level safeguards (S1/S2) could not place
    everything; a row of zeros means no eligible recipients."""
    N = len(R_prev)
    row_leak = alpha * R_prev * (1.0 - W.sum(axis=1))   # unplaced donations → pool
    F = alpha * W * R_prev[:, None]                      # F[i, j] = flow i → j
    F, flow_leak = sg.apply_flow_level(F)                # S3/S4 discounts → pool
    R = B + pool_prev / N + F.sum(axis=0)
    K = (1.0 - alpha) * R
    pool = row_leak.sum() + flow_leak                    # redistributed next year
    return R, K, F, pool
```

### 4.8 Production and reputation feedback (Phase 4; off in Phases 1–3)

- Expected output: ȳ_i(t) = q_i · (K_i(t)/B)^θ · (1 − cost_i). Realised output:
  y_i = ȳ_i · LogNormal(−σ_y²/2, σ_y). θ ∈ (0, 1) gives diminishing returns. Without it,
  concentration looks efficient by construction.
- cost_i is the fraction of research time spent on the allocation mechanism (SOFA: c_sofa; panel
  review: c_write for applicants plus c_rev per review written).
- Visibility: v_i(t+1) = (1 − λ) v_i(t) + λ · y_i(t)/mean(y). λ = 0 switches the feedback off.
- Optional turnover: seniors exit at rate 1/35 per year and are replaced by early-career researchers
  with low visibility; stage promotion after 5 and 12 years. Off by default.

### 4.9 Behaviour change (Phase 5)

- **Imitation.** Each year a fraction r_imit of agents compare themselves with one random contact and
  adopt the contact's strategy with Fermi probability
  1 / (1 + exp(−(π_j − π_i) / (κ_F · mean K))). Payoff π_i = K_i − c_m·[strategic] − sanctions.
  c_m is a moral or reputational cost. Mutation rate μ_s. Imitating a cartel member means joining
  that cartel (up to k_max; otherwise start a new one).
- **Shirking inside cartels.** A cartel member may secretly donate sincerely (saving c_m) while still
  receiving from partners. Detection probability p_det = 1 under T2/T3 and p_det = p_low under T0/T1
  (only totals are observable). Detected shirkers are expelled: partners stop donating to them.
  **Shirking rule (accepted at the M5 review; myopic).** Each year a share r_imit of active members
  reconsider. A member shirks when c_m·B exceeds the own K it would lose by giving sincerely
  instead of to partners, (1 − α)·αR_i·Σ_j (w_ij^cartel − w_ij^sincere)·Γ_ij, with Γ the return
  multipliers of the best-responder. Shirkers stay shirkers until detected.
  Hypothesis: anonymity makes cartels unravel and full transparency stabilises them. Platform audits
  (S5) work under every regime because the platform always sees all flows; T3 additionally lets
  *peers* spot and report cartels (optional: peer reporting probability p_peer under T3).

### 4.10 Comparator allocation mechanisms A0–A4 (same total budget N·B per year)

(Labelled A0–A4 to avoid confusion with milestones M1–M6.)

- **A0 Equal split:** K_i = B.
- **A1 Oracle:** K_i ∝ q_i^{1/(1−θ)} (§2.3.8).
- **A2 Sincere SOFA:** all agents sincere, T0, no safeguards (Bollen's scenario).
- **A3 Panel review:** everyone applies. Score = (1−ω_p) log q_i + ω_p log v_i + N(0, σ_panel). The top
  share p_s is funded with grant B/p_s (variant: fraction b_share of the budget as equal base, the
  rest competitive). Applicants lose c_write of output; reviewers lose c_rev per review (n_rev reviews
  per proposal). Single-year awards in this toy version.
  **Headline variant (M4 review):** b_share = 1 − α, which matches SOFA's unconditional floor
  (1 − α)·B, so both systems guarantee everyone the same share and differ only in how the rest is
  distributed. b_share = 0 (grant B/p_s, nothing for the unfunded) is kept as a labelled variant.
- **A4 Lottery:** triage the top p_triage by panel score, then fund a random subset of size p_s·N
  (same b_share convention as A3).

---

## 5. Parameters (defaults and ranges)

All parameters live in one frozen dataclass (`sofa.config.Params`). No numbers are hard-coded
elsewhere. Every entry records its unit, default, range and rationale; write "assumption" where there
is no source.

| Group | Parameter | Default | Explore |
|---|---|---|---|
| Core | N | 500 | 200–2000 |
| | B | 1.0 | fixed (scale-free) |
| | α | 0.5 | 0.1–0.9 |
| | T, T_eval, burn-in | 60, 10, — | T ≥ 5/(−ln α) + T_eval |
| | flow_mode | annual | annual, equilibrium |
| Population | σ_q | 0.5 | 0.2–1.0 |
| | G, field shares | 5; .35/.25/.20/.12/.08 | — |
| | lab size | 6 | 4–8 |
| | stage shares | .40/.35/.25 | — |
| | κ (visibility ~ quality) | 1.0 | 0–2 |
| Network | d (mean degree) | 40 | 10–100 |
| | p_in : p_out | 10 : 1 | 1–50 |
| | τ (visibility → awareness) | 1.0 | 0–2 |
| | in_field_share | None (fixed ratio) | None, 0.8 |
| Perception | σ_p | 0.5 | 0–1.5 |
| | ω (weight on reputation) | 0.3 | 0–1 |
| | μ (homophily) | 1.0 | 1–5 |
| Sincere | β | 1.0 | 0.5–3 |
| | m (top-m recipients) | 10 | 3–all |
| Strategies | h (herding) | 0.5 | 0–1 |
| | ρ (reciprocity) | 0.5 | 0–1 |
| | k, φ, topology | 5, 1.0, clique | 2–20, 0–1, {clique, ring, star} |
| | n_C or x_C | 1 cartel | 0–30 % of the population |
| | γ_up (deference) | 1.0 (off) | 1–5 |
| Safeguards | c (cap) | 1.0 (off) | 0.05–0.5 |
| | δ, δ_L, L | 0, 0, 3 | 0–1, 0–1, 2–5 |
| | s4_weighted | True | True, False |
| | p_audit, r_thr, s | 0, 0.2, 0.5 | — |
| Production | θ | 0.5 | 0.2–0.9 |
| | σ_y | 0.3 | 0–0.8 |
| | λ | 0 (Phases 1–3); 0.2 | 0–0.5 |
| | c_sofa | 0.01 | 0–0.05 |
| Panel | p_s, σ_panel, ω_p | 0.2, 1.0, 0.3 | 0.1–0.4, 0.3–2, 0–1 |
| | b_share | 1 − α (matched floor; M4 review) | 0, 1 − α |
| | c_write, c_rev, n_rev | 0.10, 0.01, 3 | 0.02–0.25 |
| Adaptation | r_imit, κ_F, μ_s | 0.1, 0.1, 0.01 | — |
| | c_m (× B), p_low | 0.05, 0.1 | 0–0.2, 0–0.5 |
| | μ_s (E7 only, M5 review) | 0.01 | 0–0.05 |
| Population | early-career visibility multiplier (E7, M5 review) | 0.5 | 0.25–1.0 |
| Safeguards | s5_weighted (M5 review) | False | True, False |
| Runs | seeds per scenario | 50 (development: 10) | — |

---

## 6. Outputs and metrics

Record per (scenario, seed, year). Report the mean over the last T_eval years, then mean and 95 %
interval across seeds.

- **Output relative to equal split** (primary, M4 review): Y_net/Y_A0 − 1, with Y_net the expected
  output after mechanism overhead; report the oracle's gain Y_A1/Y_A0 − 1 for scale.
- **Allocative efficiency** E = (Y − Y_A0)/(Y_A1 − Y_A0), where Y = Σ ȳ_i is expected output.
  E = 0 means no better than equal split; E = 1 means oracle; E can be negative. Also report
  Spearman ρ(K, q). Because Y_A1 − Y_A0 is small (≈ 13 % of output at the defaults), E magnifies
  differences; report it alongside, not instead of, output relative to equal split.
- **Concentration:** Gini(K), top-10 % share, Lorenz curves.
- **Cartel premium** Π (§2.3.5), computed against a common-random-numbers counterfactual (same
  seed, cartel switched off), plotted against the analytic 1/(1 − αφ_eff). Also report **who pays**:
  the change in K among non-members, by quality decile.
- **Reciprocity index:** Σ min(F_ij, F_ji) / Σ F_ij. Mean cycle-return share r̄.
- **Equity:** early-career share of K relative to their population share; field share of K relative to
  field size; senior share.
- **Stability:** year-on-year Spearman correlation of K.
- **Overhead:** total time cost of the mechanism (as output forgone).
- **Safeguard side-effects:** money routed through the pool; efficiency loss when the safeguard is
  applied to an all-sincere population (the *collateral cost*).
- **Behaviour (Phase 5):** strategy prevalence over time, number of cartels, their size and survival
  time, shirking rate, and number of strategy fallbacks per regime.

---

## 7. Experiments

Each experiment has a YAML config in `experiments/configs/` and a runner entry point.

- **E0 Verification (Milestone 1).** Static W: closed form vs iteration, conservation, degenerate
  cases, group balance, cartel premium and ring results from §2.3.
- **E1 Mechanics (sincere only).** α × σ_p × ω grid → Gini, E, ρ(K, q). Include A0–A2 for reference.
- **E2 Cartels.** α ∈ {0.2, 0.35, 0.5, 0.65, 0.8, 0.9} × k ∈ {2, 3, 5, 10, 20} × φ ∈ {0.25, 0.5, 0.75, 1}
  × topology × selection. Plot Π against 1/(1 − αφ) and show who pays. Feedback variant (M6 review):
  λ = 0.2 × ω ∈ {0, 0.3, 0.6} for a reduced grid (simulated, because W changes with visibility), with
  Π over time against the same seed without the cartel.
- **E3 Transparency.** Regime T0–T3 × share x of herders / reciprocators / cartel members
  ∈ {0, 0.1, 0.25, 0.5} → Gini, E, equity metrics, fallbacks.
- **E4 Safeguards.** Each of S1–S4 and α, alone and combined, against clique and ring cartels →
  trade-off frontier (reduction in Π on one axis, collateral efficiency loss on the other). Must show
  ring evasion of S3 and its correction by S4. Include S4 in both weightings, and cliques of
  k ∈ {5, 11, 20} under the cap, because a clique with k ≥ 1/c + 1 is untouched by cap c (M3 review).
- **E5 Feedback and equity.** λ > 0, ω, θ, turnover on/off, contact resampling r_A ∈ {0, 0.1}
  (M4 review) → concentration over time, early-career and small-field shares, rank stability.
  Compare with A3/A4 under the same feedback.
- **E6 Evolution (Phase 5).** Imitation dynamics × regime × audit → long-run prevalence of strategic
  behaviour. Is sincere donating evolutionarily stable, and under which rules? Keep μ_s = 0.01 and
  report every prevalence result against two null models, "imitation only" (μ_s = 0) and
  "mutation only" (r_imit = 0), because mutation drift dominates raw prevalence (M5 review).
- **E7 Global sensitivity.** Latin hypercube (n ≈ 1000) over the "Explore" ranges + PRCC for
  Gini, E, Π and early-career share (Marino et al. 2008). Sobol indices via SALib as an optional
  extra. Add to the hypercube (M5 review): the early-career visibility multiplier, θ, μ_s and c_m.
  **Design (M6 review):** three hypercubes, one per model configuration, so that switches forced on in
  every sample do not condition the others: *mechanics* (sincere SOFA with feedback, one clique for Π,
  a panel comparator), *safeguards* (static, solved) and *evolution* (the E6 model). Sobol indices are
  not computed (M6 review: cost about 50 hours for the mechanics block; PRCC suffices).

---

## 8. Working hypotheses (for interpretation — never for tuning)

- **H1** In sincere SOFA, concentration rises with α. Efficiency peaks at intermediate α and
  falls with σ_p and ω.
- **H2** The cartel premium ≈ 1/(1 − αφ) whatever the members' quality, so low-quality cartels gain
  as much in relative terms as high-quality ones.
- **H3** Pairwise reciprocity discounts are evaded by rings; caps and cycle-aware rules are needed.
- **H4** Anonymity (T0/T1) destabilises cartels through undetectable shirking but allows herding
  under T1. T3 lets cartels enforce their internal deals but also exposes them to detection by peers.
- **H5** With reputation feedback (λ > 0, ω > 0), SOFA shifts funding towards visible and senior
  researchers, and the early-career share falls below the population share.
- **H6** Compared with panel review, SOFA saves overhead, but its efficiency advantage depends on
  ω and σ_p.

---

## 9. Code architecture

```
sofa-abm/
├── CLAUDE.md                  # this file
├── README.md
├── pyproject.toml             # python >= 3.11; numpy, scipy, pandas, pyarrow, networkx,
│                              # matplotlib, pyyaml, joblib, SALib; dev: pytest, ruff, hypothesis
├── src/sofa/
│   ├── config.py              # Params (frozen dataclass), YAML loading, config hash
│   ├── rng.py                 # named RNG streams from SeedSequence (CRN across scenarios)
│   ├── population.py          # quality, fields, labs, stages, visibility, strategy assignment
│   ├── network.py             # awareness network (§4.2)
│   ├── perception.py          # q̂_ij (§4.3)
│   ├── strategies.py          # one function per strategy → donation rows (§4.4)
│   ├── information.py         # transparency regimes, feasibility, fallbacks (§4.5)
│   ├── safeguards.py          # S1–S6 (§4.6)
│   ├── flows.py               # flow_step, steady_state, return multipliers (§2, §4.7)
│   ├── production.py          # output, visibility, turnover (§4.8)
│   ├── adaptation.py          # imitation, shirking, audits (§4.9)
│   ├── baselines.py           # A0–A4 (§4.10)
│   ├── metrics.py             # §6
│   ├── model.py               # SOFAModel: init, step(), run() → results object
│   ├── experiments.py         # scenario grids, parallel seeds, CLI
│   ├── sensitivity.py         # LHS–PRCC, Sobol
│   └── plotting.py            # one function per figure
├── experiments/configs/       # E0.yaml … E7.yaml
├── tests/
├── docs/ODD.md
├── reports/                   # M1.md … checkpoint reports
└── results/                   # git-ignored; parquet + figures
```

Implementation notes:

- **Vectorise.** Agents are rows of arrays; W is a dense float64 N×N matrix. Loop over agents only
  where unavoidable (for example cartel topologies). Use `np.linalg.solve`, never an explicit
  inverse. For the return multipliers M and cycle shares, use solves or truncated power series.
- **Randomness.** A master seed goes to `SeedSequence`, which spawns named streams (`population`,
  `network`, `perception`, `strategy`, `production`, `adaptation`, `baselines`). Switching a
  mechanism on or off must leave draws in other streams unchanged: that is what makes
  counterfactual comparisons valid.
- **Results.** Tidy long-format pandas → parquet, one file per experiment, with the config hash and
  git commit in metadata. Save agent-level snapshots only at the evaluation years.
- **CLI:** `python -m sofa.experiments run E2 --seeds 50 --n 500 --out results/`
  and `python -m sofa.experiments plot E2`.
- **Parallelism:** joblib over seeds. Keep a single-seed run of the default scenario under about 2 s
  at N = 500.
- **Figures:** matplotlib, colour-blind-safe palette, PNG and PDF, axis labels with units, and the
  analytic reference line wherever one exists.

---

## 10. Tests (pytest; all must pass at every checkpoint)

Analytic (static W, N = 400; tolerance 1e-10 unless stated otherwise):

- `test_iteration_matches_closed_form`: the annual iteration converges to B(I − αWᵀ)⁻¹1.
- `test_conservation`: Σ K* = N·B, with and without the pool/safeguards (at steady state).
- `test_alpha_zero_is_equal_split`; `test_uniform_W_is_equal_split`.
- `test_group_balance_identity` for random subsets C.
- `test_cartel_exact_form`: for any clique, α, φ, Σ_{i∈C} K_i = (1−α)(k·B + I_C)/(1−αφ) using the
  realised inflow I_C (tolerance 1e-10).
- `test_cartel_premium_analytic`: clique, k = 2, φ = 1, α = 0.5 → Π within 1 % of 2.0 for the mean
  over at least 10 seeds (single random graphs can fall about 2 % short), and Π ≤ 2.0 for every seed. Across the
  E2 grid, Π ≤ 1/(1−αφ) + 1e-9 always. For k = 5 and α = 0.8, the relative shortfall, averaged over
  at least 5 seeds, shrinks monotonically as N goes 200 → 400 → 800 (reference: about 9 %, 4 %, 2 %). (Do not assert a fixed tolerance at high α and large k;
  the shortfall legitimately reaches about 20 % at α = 0.9, k = 10, N = 400.)
- `test_ring_zero_mutual_flow_same_premium`: ring with φ = 1 has Σ min(F_ij, F_ji) = 0 within the
  cartel and Π ≈ clique Π (within 5 %).
- `test_cap_bounds_premium`: with cap c, Π ≤ 1/(1 − α·min(1, (k−1)c)) + 1e-9 when the capped excess
  is placed outside the cartel; when it leaks to the pool, Π ≤ the amended bound with φ′ (§2.3.7).
- `test_horizon_warning`: `run()` warns when T − T_eval is below 5/(−ln α), or below 10/(−ln α) when
  a pool-diverting safeguard is on.
- `test_oracle_optimal`: random budget-preserving perturbations of A1 never raise Y.

Mechanical:

- The cap projection: max ≤ c, row sum ≤ 1, recipients' order preserved, idempotent, excess
  reported.
- COI: no flow within a lab when S1 is on.
- Strategy feasibility: every infeasible strategy/regime pair falls back to sincere and is counted.
- Budgets: every comparator spends exactly N·B per year.
- Metrics: Gini of known vectors; E(A0) = 0 and E(A1) = 1.
- Reproducibility: the same seed gives identical results; CRN: toggling a cartel leaves population,
  network and perception draws bit-identical.
- Switch-off tests: each Phase-2+ mechanism switched off reproduces the earlier-phase output.
- Property-based tests (hypothesis) for conservation under random W, α and safeguards.

---

## 11. Milestones and checkpoints

"Phase n" in §4 refers to the model as it stands after milestone Mn.

| # | Build | Experiments | Checkpoint output |
|---|---|---|---|
| **M1** | `flows.py`, `metrics.py` (core), config, RNG, analytic tests | E0 | `reports/M1.md`: table of analytic vs simulated values; Π vs 1/(1−αφ) plot |
| **M2** | population, network, perception, sincere strategy, A0–A2, `docs/ODD.md` v1 | E1 | Gini/E surfaces over α × σ_p × ω |
| **M3** | cartels, herders, reciprocators, deference; transparency regimes; safeguards S1–S4 | E2, E3, E4 | premium plots, regime heatmaps, safeguard trade-off frontier |
| **M4** | production, visibility feedback, turnover; A3 panel review and A4 lottery | E5 + comparator runs | equity and concentration over time; mechanism comparison |
| **M5** | imitation, shirking, audits (S5), best-responder | E6 | strategy-prevalence trajectories per regime |
| **M6** | sensitivity analysis, final figures, README, ODD complete | E7 | PRCC tornado plots; one-page summary of findings |

Stop after each checkpoint and wait for review before continuing.

---

## 12. Conventions

- Python ≥ 3.11, type hints throughout, NumPy-style docstrings, `ruff` for lint and format.
- UK English everywhere (behaviour, organisation, modelling, colour).
- Small pure functions. `model.py` orchestrates and holds no maths.
- Every formula in the code carries a comment pointing to the section of this file it implements
  (for example `# §4.3`).
- Do not add dependencies beyond §9 without asking. Do not use Mesa: the model is flows on a network
  and vectorised numpy is clearer and faster.
- Commits are small and each is tied to a milestone task. Tests are written alongside or before the
  code they test.

---

## 13. Out of scope for now (possible later extensions)

- Empirical calibration of awareness and donation networks from OpenAlex citation and co-authorship
  data for a real field; validating against observed funding distributions.
- Behavioural parameters from an incentivised allocation game or DCE among researchers.
- Multi-year grants, project-based (rather than person-based) funding, team funding, and
  international or cross-funder flows.
- Graph-based collusion detection beyond S4/S5 (for example TrustRank-style personalised seeding).

---

## 14. Key references (check bibliographic details before citing in a manuscript)

- Bollen J, Crandall D, Junk D, Ding Y, Börner K (2014). From funding agencies to scientific agency.
  *EMBO Reports* 15(2):131–133.
- Bollen J, Crandall D, Junk D, Ding Y, Börner K (2017). An efficient system to fund science: from
  proposal review to peer-to-peer distributions. *Scientometrics* 110(1). doi:10.1007/s11192-016-2110-3
- Bollen J (2018). Who would you share your funding with? *Nature* 560:143.
- Huang D-W (2018). Optimal distribution of science funding. *Physica A* 502:613–618.
- Zhang H, Goel A, Govindan R, Mason K, Van Roy B (2004). Making eigenvector-based reputation
  systems robust to collusion. *WAW 2004*, LNCS 3243.
- Gyöngyi Z, Garcia-Molina H (2005). Link spam alliances. *VLDB 2005*.
- Gross K, Bergstrom CT (2019). Contest models highlight inherent inefficiencies of scientific funding
  competitions. *PLoS Biology* 17(1):e3000065.
- Herbert DL, Barnett AG, Clarke P, Graves N (2013). On the time spent preparing grant proposals.
  *BMJ Open* 3:e002800.
- Bianchi F, Grimaldo F, Bravo G, Squazzoni F (2018). The peer review game: an agent-based model of
  scientists facing resource constraints and institutional pressures. *Scientometrics* 116.
- Szabó G, Tőke C (1998). Evolutionary prisoner's dilemma game on a square lattice. *Phys Rev E* 58:69.
- Marino S, Hogue IB, Ray CJ, Kirschner DE (2008). A methodology for performing global uncertainty
  and sensitivity analysis in systems biology. *J Theor Biol* 254:178–196.
- Grimm V et al. (2020). The ODD protocol for describing agent-based and other simulation models:
  a second update. *JASSS* 23(2):7.
