# SOFA-ABM — summary of findings (M1–M6)

A toy model of Self-Organised Funding Allocation: everyone gets base B and must pass a fraction α
of everything received to colleagues of their choice. Default scale N = 500, 50 seeds. Every result
was checked against the specification's hypotheses (§8) without tuning. Details: `reports/M1.md` …
`M6.md`.

**1. The mechanics are analytically clear** (M1, E0). With fixed donations, funding is a Katz-type
centrality of the donation graph, K* = (1 − α)B(I − αWᵀ)⁻¹1. SOFA redistributes and never creates
money. A cartel routing a share φ internally earns Π ≈ 1/(1 − αφ) times its counterfactual funding,
whatever its quality. Every closed-form result was verified to 1e-10.

**2. α is the master lever, and it cuts both ways** (E1, E2, E7). Concentration rises with α
everywhere (PRCC +0.97). Efficiency peaks at intermediate α (median E 0.42 at α = 0.3–0.7, 0.21 above
0.7), and at high α SOFA can do worse than equal split. The same α sets the cartel premium (2× at
α = 0.5, 10× at α = 0.9). Under imitation it decides how far strategic behaviour spreads: median
strategic play is 20 % at α ≤ 0.3 and 79 % at α > 0.7.

**3. Sincere SOFA beats panels robustly, but beats equal split only when funding pays off strongly**
(E5, E7). At the defaults SOFA yields +7.3 % output over equal split, against −14.7 % for panel review
and −17.6 % for a lottery (matched floor). Its overhead is 1 % against 13 %. Across the parameter
space SOFA beats panels in 98 % of cases. It beats equal split in only 70 %: the gain is about zero
when returns to funding diminish steeply (θ ≤ 0.4) and +18 % when they do not (θ > 0.6). θ and the
spread of quality decide whether *any* selective mechanism is worth having. Both are empirical
questions.

**4. Early-career researchers and small fields are underfunded** (E1, E5, E7). The early-career share
is below the population share in 97 % of the parameter space (0.69× at the defaults). The cause is
mainly who knows whom: the awareness network follows visibility, which starts low for newcomers.
Reputation feedback is not the cause. In a closed population, feedback plus contact resampling
removes the deficit. With turnover it persists, because every newcomer arrives with low visibility.
Small fields lose 8–16 % of their share, because their members must give outside the field.

**5. Cartels gain the full premium, and the best researchers pay** (E2). Low-quality cartels capture
the whole relative premium. High-quality cartels gain most in absolute terms. The cost falls on
high-quality non-members (the top quality decile bears 55 % of outsiders' loss at α = 0.8).

**6. With reputation feedback, collusion compounds** (E7, new in M6). When funding raises
visibility and visibility guides donors (λ, ω > 0), a cartel's extra money becomes reputation that
attracts sincere donations. The premium then exceeds 1/(1 − αφ) in 19 % of the parameter space, up to
12×. Without the feedback loop the bound holds.

**7. Safeguards: one rule per shape, none for all** (E4, E7).
- A **per-recipient cap** (c = 0.1) removes 95 % of a ring's premium at no collateral cost, but
  cliques larger than 1/c + 1 evade it completely.
- The **pairwise mutual-flow discount** (S3) catches cliques but *raises* ring premiums.
- The specified **cycle discount** (S4, α-weighted) is too weak. Its unweighted variant removes rings
  entirely when its horizon L reaches the ring's length.
- Collateral costs are small, and negative at high α, where curbing concentration helps.
- **Lowering α** works against every cartel shape, but costs efficiency (E falls by 0.20 at α = 0.2).

**8. Transparency enables strategies; it does not discipline them** (E6, E7). Each step from
sealed ledger to full ledger unlocks a strategy: herding at T1, reciprocity at T2, best responses at
T3. Strategic play rises from 12 % to 64 % (E7 medians). Anonymity breeds shirking inside cartels
(H4 supported), whereas full transparency stabilises cartels (they live twice as long). The strongest
anti-cartel measure is **peer reporting under a full ledger**, which nearly eliminates cartels.
Platform audits on cycle-return shares are weak. Sincere donating is evolutionarily stable only if
strategic play carries a moral or reputational cost (c_m ≈ 0.2·B); at 0.05·B it is invaded once the
ledger is transparent. Mutation drift, not selection, explains most raw prevalence. Results are
therefore reported against null models.

**What would change these conclusions.** In order of PRCC influence:
1. returns to funding (θ) and the spread of quality (σ_q), for whether SOFA is worth having;
2. α, for nearly everything else;
3. the moral cost of strategic play (c_m) and the mutation rate (μ_s), for how far manipulation
   spreads;
4. how strongly awareness follows visibility (τ), for equity.

None of these is known from data. Calibration (CLAUDE.md §13) is the natural next step.
