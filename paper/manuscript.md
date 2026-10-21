---
title: "Gaming self-organised funding: a stylised agent-based model of SOFA"
author:
  - "Senne Vleminckx (University of Antwerp) [co-authors to add]"
target: "Journal of Artificial Societies and Social Simulation (JASSS)"
status: "Draft 0.2. Discussion is a placeholder."
---

<!--
Drafting notes (remove before submission)
- Source of all numbers: reports/M1.md … M6.md and reports/summary.md. N = 500, 50 seeds, unless
  stated otherwise.
- Conceptual figures (1–3): paper/figures/schematics.py. Result figures (4–10): reports/figures/,
  to be redrawn for print (no titles, JASSS sizes).
- Citations follow JASSS author–year style. Items marked [check] need the source before submission.
- Terms used throughout: sincere donor, cartel, defector, ideal allocation, platform.
-->

# Abstract

Self-Organised Funding Allocation (SOFA) would replace grant competitions with a peer-to-peer rule.
Every researcher receives the same base amount each year and must pass a fixed share of all money
received to colleagues of their choice. Earlier tests of SOFA used citations in place of donations,
which assumes that every donor gives sincerely. We built a stylised agent-based model in which donors
can also give strategically, and we used it to study collusion by cartels: groups of researchers who
agree to pass their donations to each other. When donations do not change over time, the model can
be solved exactly. A cartel that keeps all its donations inside the group can then raise its funding
by at most the inverse of the share that each researcher keeps, a bound that is known from collusion
in PageRank. In the simulations, sincere SOFA produced more expected research output than an equal
split in 70 % of the sampled parameter space, mainly where returns to funding diminished slowly and
quality varied strongly between researchers. Cartels gained close to the full bound whatever the
quality of their members. Most of that gain was money that sincere donors would otherwise have given
to the most productive researchers outside the cartel. When funding raised a researcher's visibility
and donors rewarded visibility, a cartel's gain grew to about twice the bound. Each step towards a
public donation ledger made one more strategy possible, and the pass-on share was the strongest
driver of how far strategic giving spread. Every safeguard we tested stopped some cartel structures
and missed others. Because the model is not calibrated, the results identify mechanisms and the
parameters that control them.

**Keywords:** research funding; peer-to-peer allocation; collusion; agent-based model; mechanism
design; transparency

---

# Introduction

Most public research money is allocated through competitions in which researchers write proposals
and panels of peers rank them. The process is expensive. In the 2012 round of Project Grants of the
Australian National Health and Medical Research Council, a proposal took on average 34 working days
of researcher time; the 3727 proposals together took an estimated 550 working years, or AU$66
million in salaries, and 21 % of them were funded (Herbert et al. 2013). More time spent on a
proposal did not raise its chance of success. Contest models of grant funding, in which applicants
spend effort to win a fixed number of awards, show that at low success rates the effort that all
applicants spend together can approach the value of the money awarded (Gross & Bergstrom 2019).

A second problem is that review is noisy. Graves et al. (2011) re-analysed the scores of Australian
review panels and allowed for the variation between panel members: only 9 % of proposals were funded
in every re-sample, 61 % in none and 29 % in some but not others. When 43 reviewers rated the same 25
applications to the US National Institutes of Health (NIH), their ratings showed no agreement on the
quality of the applications (Pier et al. 2018). Chance in one round also carries into later rounds.
Among applicants for an early-career grant in the Netherlands, those just above the funding line
received more than twice as much further funding over eight years as those just below it (Bol et al.
2018), a pattern that Merton (1968) called the Matthew effect.

These costs are now rising. Generative language models make proposals cheaper to write, while
reviewing them takes as much expert time as before. In 2025 the NIH limited each principal
investigator to six applications per calendar year and stated that applications substantially
written by artificial intelligence would not count as original work (NIH 2025 [check]). A system in
which writing is cheap and reviewing is costly cannot grow with the number of applications, so
funders have a practical reason to look again at ways of allocating money that need fewer proposals
or none.

Two such alternatives are already in use. Equal base funding gives every qualified researcher the
same unconditional amount. Vaesen and Katzav (2017) estimated that an equal division of competitive
funds would let researchers in the Netherlands, the United Kingdom and the United States keep their
current staffing levels and still leave a moderate to considerable budget for other costs. Partial
lotteries keep peer review for a first selection and then draw the winners at random from proposals
that review cannot separate (Fang & Casadevall 2016). Several funders now use them, from the Health Research Council
of New Zealand (Liu et al. 2020) to the Swiss National Science Foundation (Heyard et al. 2022), and
UK Research and Innovation made partial randomisation an optional part of assessment in 2025
(Research Professional News 2025 [check]). Both alternatives reduce the cost of review, but
both also give up some or all of the judgement that peers bring.

Self-Organised Funding Allocation (SOFA) keeps peer judgement and removes proposals (Bollen et al.
2014, 2017). Every researcher receives the same base amount each year and must pass a fixed share of
everything they receive, for example half, to colleagues of their choice. Money circulates through
the community and, in principle, accumulates with the researchers whom their peers value most.
Bollen et al. (2017) tested the idea on citation data for 867,872 researchers from the Web of
Science, with each researcher's donations set in proportion to the citations that researcher gave,
and found a distribution of funding similar to that of the NIH and the US National Science
Foundation. The authors stressed that
citations stood in for each researcher's own judgement and were not a proposed basis for donations.
The Dutch Parliament later asked the Dutch Research Council (NWO) to explore alternatives of this
kind, and NWO held a workshop to plan a pilot of SOFA (Bollen 2018). Huang (2018) added cumulative
advantage to a model of the same type and found regimes in which a small elite captured a large
share of the money.

These studies assume that donors give sincerely, because a citation is treated as an honest signal
of value. In a real SOFA scheme, donations are money, and money that a donor gives away can come back
to the donor through the recipients' own donations. Campbell (1979) stated the general risk: the more
a quantitative indicator is used for social decisions, the more it is subject to pressures that
corrupt it. Science already offers a close parallel. Groups of authors who cite each other in order
to raise their citation indicators have been found in citation networks (Fister et al. 2016), and a
simulation of journal peer review showed that a small share of selfish referees, together with
networks of mutual support between authors and referees, can lower the quality of accepted work to
the level of chance (Thurner & Hanel 2011). Strategic behaviour also does not need intent: when
practices that pay are copied, they spread even if no one sets out to cheat (Smaldino & McElreath
2016).

The structure of SOFA has been studied in another setting. When donations are fixed, the funding
that each researcher receives in the long run is a Katz centrality of the donation network (Katz
1953), the same family of measures as PageRank (Page et al. 1999). Collusion in such rankings is well
documented. Web pages can be linked into "spam farms" whose structure maximises their rank, and
alliances of farms can raise the rank of every member (Gyöngyi & Garcia-Molina 2005). Zhang et al.
(2004) proved that a colluding group can raise its PageRank by at most a factor 1/ε, where ε is the
probability that the random walk restarts, and found that colluding pairs on real web graphs came
close to this bound. In SOFA, the share of receipts that each researcher keeps plays the role of ε.
Mechanism design has studied the related problem of a group that selects its best members when every
member is also a candidate, and has shown that rules in which no member's report can affect their own
selection exist but are restrictive (Holzman & Moulin 2013; Kurokawa et al. 2015). SOFA has no such
property, because part of a donation can return to the donor.

Agent-based models are an established tool for studying peer review, because large experiments with
real funding systems are difficult to run (Squazzoni & Takács 2011; Feliciani et al. 2019). They have
compared allocation rules such as equal shares, lotteries and panels (Höylä et al. 2016) and studied
referees who act strategically or reciprocate (Squazzoni & Gandelli 2013; Bianchi et al. 2018). In
none of these models are the reviewers also the funders. To our knowledge, no published model has studied SOFA with donors who respond to the
incentives that SOFA itself creates.

We built such a model. It is a stylised model for theoretical exploration in the sense of Edmonds et
al. (2019): it shows what the mechanism does under stated assumptions and identifies the parameters
that decide the outcome, and its parameters are not calibrated to a real research community. With
fixed donations the model can be solved exactly, which gives a reference for the simulations and
extends the collusion bound of Zhang et al. (2004) to cartels that keep only part of their donations
inside the group. In the simulations, donors perceive each colleague's quality with error and with a
bias towards reputation. Some donors follow strategic rules, which Section 2 describes: they follow
the crowd, return favours, form cartels, defect from cartels, or copy the strategies of
better-funded colleagues. The organisation that runs the scheme can make the record of donations
more or less public and can apply rules against collusion. We address six research questions:

- **RQ1.** When all donors give sincerely, how do the concentration of funding and the efficiency of
  its allocation depend on the share passed on, on errors in perception and on the weight given to
  reputation?
- **RQ2.** How much can a cartel gain, and who pays for that gain?
- **RQ3.** How does the transparency of the donation record change which strategies are feasible and
  how far they spread?
- **RQ4.** Which safeguards reduce the gain from collusion, and what do they cost when all donors are
  sincere?
- **RQ5.** Does a feedback loop from funding to reputation amplify cumulative advantage, and how are
  early-career researchers and small fields funded?
- **RQ6.** How does SOFA compare with an equal split of the budget and with the allocation that
  maximises expected output?

Section 2 describes the model and its analytic properties, and Section 3 the experiments. Section 4
presents the results by research question, and Section 5 discusses what they imply for the design
of peer-to-peer funding and what a stylised model cannot show.

---

# Model

## Overview

The model represents one research community over several decades. Figure 1 shows its central
element, the flow of money for one researcher in one year, and the three forms of cartel that we
study. The model has two types of entity. Researchers receive money, keep part of it for research,
produce output and donate the rest. The platform, which stands for the funding organisation that
runs the scheme, records every donation, decides what participants may see of that record and
applies safeguards. Appendix A gives the full description of the model in the ODD format (Grimm et
al. 2020). The model is written in Python 3.13 with NumPy 2.5, SciPy 1.18 and pandas 3.0; code,
configuration files and tests are available at [repository and CoMSES link to add].

> **Figure 1.** (a) The money of one researcher i in one year. Receipts are the base amount, the
> donations received and an equal share of the pool. The researcher keeps the share 1 − α for
> research and donates the share α in the next year. The platform records all flows, and money that
> a safeguard removes from donations is paid back to everyone in equal shares. (b) The three cartel
> shapes, shown for five members who keep all their donations inside the cartel.
> `figures/fig1_structure.png`

## The funding rule

There are $N$ researchers. Each receives a base amount $B$ each year; we set $B = 1$, so all amounts
are expressed in units of the base amount. Each researcher must donate a share $\alpha$ of everything
received in the previous year and keeps the rest. Let $W(t)$ be the $N \times N$ donation matrix, in
which $w_{ij}$ is the share of researcher $i$'s donation that goes to researcher $j$; $w_{ii} = 0$,
and each row sums to 1. Receipts $R$ and the funds kept for research $K$ then follow

$$R(t) = B\,\mathbf{1} + \frac{\text{pool}(t-1)}{N}\,\mathbf{1} + \alpha\,W(t)^\top R(t-1), \qquad K(t) = (1-\alpha)\,R(t). \tag{1}$$

The pool contains money that the platform's safeguards removed from donations in the previous year,
for example the part of a donation above a cap on what one recipient may receive. The platform pays
it back to all researchers in equal shares. This lagged form, in which this year's donations are a
share of last year's receipts, follows Bollen et al. (2017).

## Analytic properties with fixed donations

If the donation matrix $W$ does not change from year to year, Equation 1 converges to

$$R^* = B\,(I - \alpha W^\top)^{-1}\mathbf{1}, \qquad K^* = (1-\alpha)\,R^*. \tag{2}$$

The distance to this steady state shrinks by the factor $\alpha$ each year. $R^*$ is the Katz
centrality of the donation network (Katz 1953). If the rows of $W$ sum to 1, total funding equals
$N B$: SOFA redistributes the budget and does not add to it. With $\alpha = 0$, or when every
researcher divides their donation equally over all others, everyone keeps $B$. For any group of
researchers, the funds kept by the group equal the group's base amounts plus the money that flows
into the group minus the money that flows out of it.

Now let a cartel $C$ of $k$ researchers route a share $\varphi$ of their donations to fellow members
and give the rest sincerely to non-members. If $I_C$ is the money that the cartel receives from
non-members, the cartel keeps exactly

$$\sum_{i \in C} K_i = \frac{(1-\alpha)(kB + I_C)}{1 - \alpha\varphi}. \tag{3}$$

The cartel premium $\Pi$ is the cartel's funding divided by the funding of the same researchers
without the cartel. If the money from non-members does not rise when the cartel forms,

$$\Pi = \frac{\sum_{i\in C} K_i(\text{cartel})}{\sum_{i\in C} K_i(\text{no cartel})} \le \frac{1}{1-\alpha\varphi}. \tag{4}$$

The bound does not depend on the quality of the members, and it is reached when the cartel is small
relative to the community. At $\alpha = 0.5$ and $\varphi = 1$ a cartel can double its funding; at
$\alpha = 0.9$ it can multiply its funding by ten. With $\varphi = 1$, Equation 4 is the PageRank bound
$1/\varepsilon$ of Zhang et al. (2004) with the kept share $1 - \alpha$ in place of $\varepsilon$, and
Equation 3 corresponds to their amplification factor, which compares a group's total weight with the
weight that flows into it. Two consequences matter for safeguards. A ring cartel, in which each
member gives to the next and the last gives to the first, has no pair of members who give to each
other, yet it obtains the same premium as a clique. A cap $c$ on the share of a donation that one
recipient may receive limits a clique's internal share to $\varphi_{\max} = \min(1, (k-1)c)$, so a
clique with at least $1/c + 1$ members is not affected by the cap.

Equations 2–4 describe SOFA completely when donations are fixed, and simulating such cases adds
nothing. The model is needed when donations change because donors respond to incentives, to the
information available to them and to reputation.

## Researchers, fields and visibility

The default community has $N = 500$ researchers. Each has a latent quality $q_i$, drawn from a
log-normal distribution with spread $\sigma_q = 0.5$ and scaled to a mean of 1; no agent observes
quality directly. Researchers belong to five fields of unequal size (35, 25, 20, 12 and 8 % of the
community) and, within fields, to labs of about six members. Forty per cent are early-career, 35 %
mid-career and 25 % senior, and every lab has at least one senior member. Each researcher has a
visibility $v_i$, which stands for reputation. Initial visibility is $q_i^{\kappa}$ multiplied by a
stage factor (0.5 for early-career, 1.0 for mid-career and 1.5 for senior researchers) and by
log-normal noise, scaled to a mean of 1. Visibility is therefore correlated with quality but is not
the same, and it favours senior researchers.

## Awareness and perception

A researcher can donate only to colleagues they know. Researcher $i$ knows researcher $j$ with
probability $\min(1, p_f\, v_j^{\tau})$, where $p_f$ is ten times larger for colleagues in the same
field than for colleagues in other fields, and is scaled so that a researcher knows on average 40
of the 499 others. Everyone knows the members of their own lab. Because the probability rises with
visibility, visible researchers are known by more people. The parameter $\tau$ sets how strongly
awareness follows visibility.

Researcher $i$ perceives the quality of a known colleague $j$ as

$$\hat q_{ij} = q_j^{1-\omega}\, v_j^{\omega}\, \exp\!\left(\sigma_p\varepsilon_{ij} - \sigma_p^2/2\right), \qquad \varepsilon_{ij}\sim N(0,1). \tag{5}$$

The weight $\omega$ sets how much donors rely on reputation rather than quality. The term
$\varepsilon_{ij}$ is a fixed personal view of $i$ about $j$, drawn once at the start. It makes donors
disagree about the same colleague, and because it does not change, each donor's opinion is stable
over time. Its spread $\sigma_p$ is the size of the perception error.

## Donation strategies

Every strategy acts on the eligible colleagues of a donor: those the donor knows, excluding the donor
and, when the conflict-of-interest rule is on, the donor's own lab. Table 1 lists the strategies.
A sincere donor ranks eligible colleagues by perceived quality, keeps the ten highest and divides
the donation in proportion to perceived quality raised to the power $\beta = 1$. The strategic rules
change this in different ways. A cartel member routes a share $\varphi$ of the donation to fellow
members, in one of the shapes of Figure 1b, and gives the rest sincerely to non-members. A defector
is a cartel member who secretly gives sincerely while still receiving donations from the other
members.

**Table 1.** Donation strategies and the information each needs. A strategy that the current
transparency regime does not support falls back to sincere giving.

| Strategy | Rule | Needs at least |
|---|---|---|
| Sincere | gives to the ten best-perceived eligible colleagues | T0 |
| Herder | tilts the sincere ranking towards colleagues with high receipts last year (weight $h = 0.5$) | T1 |
| Reciprocator | returns a share $\rho = 0.5$ to last year's donors, in proportion to their gifts; gives the rest sincerely | T2 |
| Best-responder | gives to the colleague through whom the most money returns to the donor, given last year's donations | T3 |
| Cartel member | routes a share $\varphi$ to fellow members; gives the rest sincerely to non-members | T0 |
| Defector | a cartel member who gives sincerely while still receiving from the cartel | T0 |
| Deferential | early-career only: sincere, with extra weight on seniors in the own field | T0 |

## Transparency regimes

The platform always sees the full record of donations. What participants see depends on the regime.
In the sealed regime (T0), each researcher sees only their own receipts. When totals are public (T1),
everyone sees everyone's receipts of the previous year. When donors are revealed (T2), each
researcher also sees who gave them how much. With a full ledger (T3), everyone sees the whole record
of last year's donations. Each regime makes the strategies of Table 1 that need it feasible; a donor
who holds an infeasible strategy gives sincerely, and we count these fallbacks.

## Safeguards

The platform can apply five safeguards, alone or together. The conflict-of-interest rule (S1)
excludes donations to members of the donor's own lab. The per-recipient cap (S2) limits the share of
a donation that any one recipient may receive to $c$ and spreads the excess over the donor's other
recipients. The mutual-flow discount (S3) looks at every pair of researchers who give to each other
and reduces both flows by a fraction $\delta$ of the smaller one. The cycle discount (S4) reduces a
donor's outgoing flows in proportion to the share of the donation that returns to the donor within
$L$ steps. As specified, S4 weights each step by $\alpha$, the share that each intermediate
recipient passes on; a variant (S4u) uses the unweighted probability that a unit of donation returns.
Audits (S5) take place each year with probability $p_{\text{audit}}$ and remove a share $s$ of the
funds of donors whose return probability exceeds a threshold. Under a full ledger, peers can also
report a cartel, which then loses the same share and is dissolved. Money removed by S1–S5 goes to the
pool and returns to all researchers in equal shares.

## Production and reputation feedback

Expected research output is $\bar y_i = q_i \left(K_i/B\right)^{\theta} (1 - c_i)$, where $0 < \theta < 1$
makes returns to funding diminish and $c_i$ is the share of research time spent on the allocation
mechanism itself ($c_i = 0.01$ under SOFA). Realised output adds log-normal noise. When reputation
feedback is switched on, visibility moves towards recent output,

$$v_i(t+1) = (1-\lambda)\,v_i(t) + \lambda\, y_i(t)/\bar y(t), \tag{6}$$

where $\lambda$ sets the speed of the feedback and $\bar y(t)$ is mean output. Figure 2 shows the
resulting loop. With $\lambda > 0$ and $\omega > 0$, more funding leads to more output, more output to
more visibility, and more visibility to higher perceived quality and therefore to more donations.
Two optional mechanisms change the population and the network. With turnover, senior researchers
leave at a rate of 1/35 per year and are replaced by early-career newcomers. With contact
resampling, each researcher replaces a share $r_A$ of their contacts each year, choosing new ones in
proportion to current visibility.

> **Figure 2.** Feedback between funding and reputation. An arrow means that an increase in the source
> raises the target. The reputation loop is closed only when visibility follows output ($\lambda > 0$)
> and donors weight visibility ($\omega > 0$); otherwise a cartel's gain is bounded by Equation 4.
> The dashed path through the awareness network acts only when contacts are resampled.
> `figures/fig2_loops.png`

## Strategy change

In some experiments the strategies themselves change over time. Each year a randomly chosen tenth
of the researchers compare their payoff with that of one random contact and copy the contact's
strategy with a probability that rises with the payoff difference, following the Fermi rule of Szabó
and Tőke (1998). The payoff is the funding kept, minus a moral or reputational cost $c_m B$ for
playing a strategic rule, minus any sanctions. Copying a cartel member means joining that cartel, up
to 20 members. In addition, 1 % of researchers each year adopt a random strategy, which represents
experimentation. A cartel member defects when the moral cost saved exceeds the funding the member
would lose by giving sincerely. Other members detect a defector with certainty when donors are
revealed (T2 and T3) and with probability 0.1 per year otherwise, and detected defectors are expelled.

## Reference allocations

We compare SOFA with two reference allocations that spend the same budget $N B$ each year. Equal
split gives everyone $K_i = B$. The ideal allocation gives $K_i \propto q_i^{1/(1-\theta)}$, which
maximises expected output when quality is known. For scale we also report a simplified panel review,
in which a noisy panel funds the top 20 % of applicants on top of an equal base of $(1-\alpha)B$ for
everyone, and a lottery among the applicants that the panel shortlists. In both, applicants lose 10 %
of their output to writing proposals and 1 % per review they write (three each). The panels in this
model are never gamed, so we use them only as a point of reference.

## Schedule

Figure 3 shows the order of events in one simulated year. One step is one year. Each run lasts 60
years, and outcomes are averaged over the last 10; runs with strategy change last 100 years and are
averaged over the last 20. These horizons are long enough for the effect of the starting state to
fall below 1 % of the result.

> **Figure 3.** Order of events within one simulated year. Steps 6–8 are active only when production
> feedback, strategy change or turnover is switched on.
> `figures/fig3_schedule.png`

---

# Experiments and analysis

## Design

Table 2 links the eight experiments to the research questions. The main experiments vary a few
parameters on a grid around the defaults of Appendix B. Each grid cell was run with 50 random seeds
for a community of $N = 500$. Before each full run, the same grid was run at a smaller scale
($N = 300$, 10 seeds) as a check, and the two scales agreed in sign and approximate size for every
result we report. The sensitivity analysis (E7) then varies all parameters together over the ranges
in Appendix B.

**Table 2.** Experiments, the research questions they address, and how cells were computed. "Solved"
cells use the steady state of Equation 2; "simulated" cells run the yearly model of Equation 1.

| | Research question | Design | Computed by |
|---|---|---|---|
| E0 | verification | fixed donation matrices: closed forms against simulation | both |
| E1 | RQ1, RQ6 | sincere donors; α × perception error σ_p × reputation weight ω | solved |
| E2 | RQ2 | one cartel; α ∈ {0.2, …, 0.9} × size k ∈ {2, …, 20} × internal share φ ∈ {0.25, …, 1} × shape × choice of members | solved |
| E2-fb | RQ2, RQ5 | as E2 on a smaller grid, with reputation feedback λ ∈ {0, 0.2} × ω ∈ {0, 0.3, 0.6} | simulated |
| E3 | RQ3 | regime × share of herders, reciprocators or cartel members ∈ {0, 0.1, 0.25, 0.5} | both |
| E4 | RQ4 | each safeguard and lower α, alone and combined, against cliques (k = 5, 11, 20) and rings (k = 3, 5) | solved |
| E5 | RQ5, RQ6 | feedback λ × ω × turnover × contact resampling, for SOFA and the reference allocations | simulated |
| E6 | RQ3, RQ4 | strategy change from 80 % sincere donors; regime × audits or peer reports × moral cost $c_m$ | simulated |
| E6-fb | RQ3, RQ5 | as E6, with λ ∈ {0, 0.2} × ω ∈ {0.3, 0.6} | simulated |
| E7 | all | three Latin hypercubes of 1000 samples each | both |

## Solved and simulated cells

When donations cannot change from year to year, the yearly model converges to Equation 2, so we
computed those cells from Equation 2 directly. With the nonlinear mutual-flow discount (S3), we
computed the exact fixed point of Equation 1 instead. Herders, reciprocators, reputation feedback and
strategy change all make donations depend on the previous year, so those cells were always
simulated. As a check, we also simulated one solved cell per experiment year by year; the two
methods agreed to within rounding error.

## Common random numbers

Each random component of the model (population, network, perceptions, strategies, production and
strategy change) draws its numbers from a separate stream derived from the seed. Switching one
mechanism on therefore leaves the random draws of all other components unchanged. For example, with
and without a cartel, the same seed produces the same researchers, the same network and the same
personal views; the test suite checks that these are identical. The simulated histories still
differ once the cartel acts, and that difference is the effect we measure. We computed every cartel
premium against the same seed without the cartel.

## Outcomes

Our main measure of performance is expected output relative to equal split, $Y/Y_{\text{equal}} - 1$,
after the cost of running the mechanism. We also report allocative efficiency,
$E = (Y - Y_{\text{equal}})/(Y_{\text{ideal}} - Y_{\text{equal}})$, which is 0 for equal split and 1
for the ideal allocation. At the defaults the ideal allocation yields only 13.3 % more output than
equal split, so small differences in output become large differences in $E$; we therefore report
both. Concentration is measured by the Gini coefficient of the funds kept. For cartels we report the
premium of Equation 4 and the loss among non-members by decile of quality. For equity we report the
share of funding received by early-career researchers divided by their share of the population, and
the same ratio for the smallest field. For behaviour we report the share of researchers who actually
play a strategic rule (after fallbacks), the share in cartels and the share of defectors.

## Sensitivity analysis

E7 uses three Latin hypercubes of 1000 samples each, one per configuration of the model. A single
hypercube would have switched safeguards and strategy change on in every sample, so every result
would have described a safeguarded and adaptive SOFA. The first hypercube (26 factors) covers
sincere SOFA with reputation feedback, one clique cartel and the panel for comparison. The second (12
factors) covers safeguards against one cartel, with fixed donations. The third (10 factors) covers
the model with strategy change. For each outcome we computed partial rank correlation coefficients
(PRCC) with Bonferroni-corrected tests (Marino et al. 2008). An extra factor that does not enter the
model served as a reference for noise, and it was not significant for any of the 23 outcomes. PRCC
measures monotone relations, so we inspected scatter plots of each outcome against its leading
factors. Variance-based Sobol indices would have required about 54,000 runs for the first hypercube
alone, and we did not compute them.

## Verification

The test suite (328 tests) checks every analytic result above against the simulation, checks that
money is conserved for random donation matrices and safeguards, and checks that the model with any
mechanism switched off reproduces the simpler model exactly. Appendix C reports the verification
results. Two refinements to the analytic results came out of this work. When a cap sends money to
the pool, cartel members receive back their share $k/N$ of it, so the cap bound must use
$\varphi' = \varphi_{\max} + (1 - \varphi_{\max})k/N$. Money in the pool also returns one year later
than direct donations, so runs with a pool need a burn-in period twice as long before outcomes are
measured.

---

# Results

## Sincere donors

With sincere donors at the defaults, SOFA reached an allocative efficiency of 0.63 (95 % interval
0.62–0.64), and the rank correlation between funding and quality was 0.82 (Table 3). After the cost
of the mechanism, expected output was 7.3 % above equal split, against 13.3 % for the ideal
allocation. The Gini coefficient of funding was 0.40. The simplified panel and lottery produced less
output than equal split, mainly because of their assumed costs of writing and reviewing proposals.

**Table 3.** Sincere SOFA and the reference allocations at the defaults (α = 0.5, σ_p = 0.5, ω = 0.3,
θ = 0.5, no feedback), means over 50 seeds. The early-career ratio is the early-career share of
funding divided by their share of the population.

| | Output vs equal split | E | Gini | Overhead | Early-career ratio |
|---|---|---|---|---|---|
| Ideal allocation | +13.3 % | 1 | 0.52 | 0 % | 1.01 |
| Sincere SOFA | +7.3 % | 0.63 | 0.40 | 1 % | 0.69 |
| Equal split | 0 | 0 | 0 | 0 % | 1.00 |
| Panel (equal base 1 − α) | −14.7 % | −0.15 | 0.40 | 13 % | 0.91 |
| Lottery (equal base 1 − α) | −17.6 % | −0.40 | 0.40 | 13 % | 0.95 |

The share passed on, $\alpha$, set the concentration of funding. The Gini coefficient rose with
$\alpha$ in all 36 combinations of perception error and reputation weight in E1, and $\alpha$ was
the leading factor for the Gini coefficient across the hypercube (PRCC +0.97). Efficiency was highest
at intermediate values of $\alpha$ (Figure 4). At low $\alpha$, little money circulates, so funding
stays close to an equal split and the judgement of peers has little effect. At high $\alpha$, money
accumulates on a few researchers, and because returns to funding diminish, the extra money produces
little extra output. Across the hypercube the median efficiency was 0.29 for $\alpha \le 0.3$, 0.42
for $0.3 < \alpha \le 0.7$ and 0.21 for $\alpha > 0.7$. With high $\alpha$ and either small
perception errors or a high weight on reputation, SOFA produced less output than equal split.

Perception errors had two opposing effects. They blurred the ranking of researchers, which lowered
efficiency when $\alpha$ was low. They also made donors disagree, which spread money over more
researchers and reduced over-concentration when $\alpha$ was high. When perception was exact, every
donor chose the same top researchers, and only 27 % of researchers received any donation. At
$\alpha = 0.9$ and $\omega = 0.3$, efficiency rose from −0.59 without perception errors to +0.33
with $\sigma_p = 1$. Efficiency therefore fell with perception error in only 15 % of the
combinations of $\omega$ and $\alpha$, whereas it fell with the weight on reputation in every
combination.

> **Figure 4.** Gini coefficient of funding (top row) and allocative efficiency (bottom row) of
> sincere SOFA. Columns show the reputation weight ω; within each panel the share passed on α is on
> the horizontal axis and the perception error σ_p on the vertical axis. White dots mark the α with
> the highest efficiency for each σ_p; to the right of the dashed line, SOFA does worse than equal
> split (E < 0). Means over 50 seeds. `../reports/figures/E1_surfaces.png`

Whether SOFA outperforms equal split depends on two quantities that are hard to measure. Across the
hypercube, sincere SOFA produced more output than equal split in 70 % of samples (10th percentile
−5.4 %, median +4.5 %, 90th percentile +51 %). The leading factors were the spread of quality,
$\sigma_q$ (PRCC +0.81), and the returns to funding, $\theta$ (+0.75). For $\theta \le 0.4$ the
median gain was 0.1 %, and for $\theta > 0.6$ it was 18 %. When returns to funding diminish steeply,
no selective allocation gains much over an equal split. Sincere SOFA produced more output than the
simplified panel in 98 % of samples, mostly because of the panel's assumed overhead (PRCC of the
proposal-writing cost +0.63), and we do not interpret this comparison further.

## Equity

Early-career researchers and small fields received less than their share. At the defaults,
early-career researchers received 0.69 times their share of the population and the smallest field
0.85 times its share, whereas the ideal allocation gave early-career researchers 1.01 times their
share, because quality does not depend on career stage in the model. Across the hypercube, the
early-career ratio was below 1 in 97 % of samples (median 0.82) and fell with $\alpha$ (PRCC −0.71)
and with $\tau$ (−0.43). The main cause is the awareness network. Early-career researchers start with
low visibility, so fewer colleagues know them: their mean number of colleagues who know them was 24,
against 61 for seniors. Reputation feedback did not create this deficit. Without turnover, feedback
raised the early-career ratio from 0.69 to 0.77, and feedback combined with contact resampling
($r_A = 0.1$) removed it (1.00; 95 % interval 0.98–1.03). With turnover the deficit remained (0.70),
because each newcomer arrives with low visibility.

The deficit of the smallest field followed from the balance of flows into and out of each group.
With a fixed preference for colleagues in the same field, members of small fields know few
colleagues in their own field and sent 47 % of their donations out of the field. When we built the
network so that every field had the same share of contacts inside the field, the deficit
disappeared (field ratios 0.98–1.01).

## Cartels

Without reputation feedback, the cartel premium followed Equation 4 closely (Table 4, Figure 5). A
5-member clique that kept all its donations inside the group almost doubled its funding at
$\alpha = 0.5$ and multiplied it by 4.8 at $\alpha = 0.8$. Larger cartels fell somewhat short of the
bound, because the donations they withheld lowered the receipts of outsiders, and with them the
money that outsiders passed back to the cartel. With $\varphi = 1$, clique, ring and star cartels
obtained the same total premium; the differences were below $10^{-14}$. The shape decided only how
the money was divided among the members. In the full model, 0.3 %
of the 62,400 cells of E2 exceeded the bound, by at most 0.8 %. All of them had $\varphi < 1$: by
evening out receipts among members, the cartel moved part of its sincere giving to recipients who
passed money back to it.

**Table 4.** Cartel premium Π for a clique of randomly chosen members that keeps all donations
inside the group (φ = 1), means over 50 seeds.

| α | Bound 1/(1 − α) | k = 2 | k = 5 | k = 10 | k = 20 |
|---|---|---|---|---|---|
| 0.5 | 2 | 1.99 | 1.98 | 1.97 | 1.92 |
| 0.8 | 5 | 4.92 | 4.78 | 4.63 | 4.26 |
| 0.9 | 10 | 9.67 | 9.13 | 8.53 | 7.25 |

> **Figure 5.** Cartel premium against its analytic upper bound 1/(1 − αφ) for clique, ring and star
> cartels of randomly chosen members. Each point is one combination of α, φ and cartel size k (mean
> over 50 seeds). Points on the dashed diagonal reach the bound; large cartels at high α fall short.
> `../reports/figures/E2_premium_vs_bound.png`

The relative premium did not depend on the quality of the members. At $\alpha = 0.9$, a 5-member
cartel drawn from the lowest quartile of quality gained $\Pi = 9.97$, close to the bound of 10. A
cartel drawn from the highest quartile gained 7.76, because part of the money it would have received
anyway came back from its own sincere donations. In absolute terms, however, the high-quality cartel
gained more: 19.5 base amounts per member per year, against 1.0 for the low-quality cartel.

The cost fell on the best researchers outside the cartel. Cartel members withdraw the sincere
donations they would otherwise have made, and those donations went mainly to high-quality
researchers. At $\alpha = 0.8$ and $k = 5$, the top decile of quality among non-members bore 55 % of
the total loss of non-members, and the top two deciles bore 75 % (Figure 6). Collusion in SOFA
therefore moves money away from the researchers to whom the ideal allocation would give most.

> **Figure 6.** Mean change in the funding of non-members, in per cent of the base amount, when one
> clique forms (φ = 1), by decile of the non-members' quality, for four cartel sizes at α = 0.5 and
> α = 0.8. `../reports/figures/E2_who_pays.png`

When collusion was widespread, efficiency fell substantially. In E3, when half of the community
formed 5-member cliques, efficiency fell by 0.35 (95 % interval 0.35–0.36) compared with sincere
SOFA. Because the ideal allocation gains 13.3 % over equal split, this corresponds to about 4.7
percentage points of output. The Gini coefficient fell at the same time, because the randomly
chosen members pooled money among themselves. When half of the community herded, efficiency fell by
0.13. Reciprocity lowered it by only 0.015 and made funding more equal.

## Cartels with reputation feedback

Equation 4 assumes that non-members do not give more to the cartel once it forms. Reputation
feedback breaks this assumption, through the loop of Figure 2: the cartel's extra money raises its
members' output, their output raises their visibility, and when donors weight visibility, sincere
non-members give more to the members.

In E2-fb, the premium stayed at or below the bound whenever either part of the loop was missing.
Without feedback ($\lambda = 0$), the largest ratio of premium to bound was 1.002, and without weight
on reputation ($\omega = 0$) it was 1.001. With both parts present, the premium exceeded the bound
(Table 5, Figure 7). At $\alpha = 0.8$, $\varphi = 1$ and $\omega = 0.6$, a 5-member clique ended
with 9.6 times its funding without the cartel, against a bound of 5, and a 2-member clique reached
11.0 times. Smaller cartels gained more relative to the bound, because their extra visibility was
shared among fewer members. The excess took 6–7 years to build up at $\alpha = 0.5$ and 10–13 years
at $\alpha = 0.8$, after which it levelled off.

**Table 5.** Cartel premium divided by the bound 1/(1 − αφ), clique of five, mean [95 % interval]
over 50 seeds. Values above 1 exceed the bound.

| α, φ | λ = 0 | λ = 0.2, ω = 0 | λ = 0.2, ω = 0.3 | λ = 0.2, ω = 0.6 |
|---|---|---|---|---|
| 0.5, 0.5 | 0.99 | 0.99 | 1.02 [1.02, 1.03] | 1.05 [1.04, 1.07] |
| 0.5, 1 | 0.99 | 0.99 | 1.06 [1.05, 1.08] | 1.16 [1.12, 1.20] |
| 0.8, 0.5 | 0.99 | 0.99 | 1.06 [1.04, 1.09] | 1.18 [1.09, 1.27] |
| 0.8, 1 | 0.96 | 0.96 | 1.28 [1.20, 1.35] | 1.91 [1.63, 2.19] |

> **Figure 7.** Cartel premium divided by its bound over time (left, clique of five) and averaged over
> the last ten years by cartel size (right), with feedback (solid) and without (dotted). The dashed
> line marks the bound. `../reports/figures/E2_feedback.png`

The hypercube gave the same picture over a wider range of parameters. The premium exceeded 1.05 times
the bound in 19 % of samples, and this share rose with the weight on reputation, from 4 % for
$\omega < 0.25$ to 28 % for $\omega > 0.75$. The largest ratio, 11.9, came from an extreme sample
($k = 2$, $\alpha = 0.79$, $\varphi = 0.95$, $\omega = 0.94$), with parameters at the edge of their
ranges, and we report it only to show how far the mechanism can go. With reputation feedback, a cartel converts money into reputation, and reputation
attracts sincere donations. Because this extra money arrives as ordinary sincere donations, none of
the flow-based safeguards in the model can detect it.

## Safeguards

Table 6 shows, for each safeguard, the share of the cartel's excess premium ($\Pi - 1$) that it
removed, together with its collateral cost: the loss of efficiency that it caused when every donor
was sincere (Figure 8).

**Table 6.** Share of the excess premium removed (α = 0.5, φ = 1, 50 seeds) and loss of efficiency
for a community of sincere donors. Negative values mean that the premium rose.

| Safeguard | Clique 5 | Clique 11 | Clique 20 | Ring 3 | Ring 5 | Collateral loss in E |
|---|---|---|---|---|---|---|
| S1 conflict of interest | 0.02 | — | — | 0.03 | 0.01 | 0.016 |
| S2 cap c = 0.1 | 0.75 | 0.00 | 0.00 | 0.95 | 0.95 | 0.001 |
| S2 cap c = 0.05 | 0.89 | 0.66 | 0.09 | 0.97 | 0.97 | 0.159 |
| S3 mutual-flow discount δ = 1 | 0.83 | 0.80 | 0.76 | −0.07 | −0.07 | 0.002 |
| S4 cycle discount, weighted, L = 5 | 0.34 | 0.16 | 0.09 | 0.40 | 0.12 | 0.000 |
| S4u cycle discount, unweighted, L = 5 | 0.91 | 0.53 | 0.32 | 1.00 | 1.00 | 0.000 |
| S1 + S2 (c = 0.1) + S3 | 0.91 | 0.81 | 0.78 | 0.91 | 0.91 | 0.025 |
| α lowered to 0.2 | 0.75 | 0.75 | 0.74 | 0.75 | 0.75 | 0.195 |

> **Figure 8.** Share of the excess premium removed by each safeguard for five cartels (left) and the
> loss of efficiency that each causes when all donors are sincere (right).
> `../reports/figures/E4_dotplot.png`

The per-recipient cap was effective against rings and ineffective against large cliques. A ring
member gives the whole donation to one colleague, so a cap of 10 % removed 95 % of a ring's excess
premium. A sincere donor with ten recipients rarely gives anyone more than 10 %, so the cap cost
almost nothing. A clique of 11 or more members, however, gives each member less than 10 % and was not
affected at all. The mutual-flow discount showed the reverse pattern. It removed most of the premium
of every clique, but it raised the premium of rings by 7 %. The discount taxes the two-way flows that
are common among sincere donors. Ring members give nothing to outsiders and never give back to the
member they receive from, so their own flows escape the tax, while their sincere counterparts would
have paid it.

The cycle discount as specified was weak, because each step of a cycle is weighted by $\alpha$: in a
ring of five at $\alpha = 0.5$, only $\alpha^4 \approx 6\,\%$ of a donation counts as returning. The
unweighted variant removed the whole premium of rings, but only when its horizon $L$ was at least
the length of the ring, and it was much weaker against large cliques. Combining the conflict-of-
interest rule, the cap and the mutual-flow discount removed 78–91 % of the excess premium of every
cartel at a cost of 0.025 in efficiency, most of which came from the conflict-of-interest rule
because it removes lab members from the choices of sincere donors. Lowering $\alpha$ to 0.2 worked
equally against all shapes and removed about 75 % of each excess premium, but it cost 0.20 in
efficiency, because it also weakens the effect of sincere judgement.

Across the safeguard hypercube, collateral costs were small (median 0.0 and 90th percentile 0.3
percentage points of output). For $\alpha > 0.7$ they were negative in 96 % of samples: by limiting
concentration, caps and discounts raised the output of sincere SOFA. The cycle discount had no
significant PRCC on the premium, because it worked only for rings no longer than its horizon. An
average over the whole hypercube hides such a conditional effect, which the grid of E4 shows.

## Transparency and the spread of strategic donating

Each step towards a public record made one more strategy of Table 1 feasible: herding when totals
became public, reciprocity when donors were revealed, and best responses under a full ledger. In E6,
where strategies change by imitation and experimentation, the share of researchers who actually
played a strategic rule rose from 12 % in the sealed regime to 24 %, 41 % and 51 % in regimes T1, T2
and T3 (moral cost $0.05B$, no audits). Across the hypercube the medians were 12, 29, 49 and 64 %.

Most of the change from the starting mix came from random experimentation rather than from
selection. Experimentation alone, without imitation, lowered the sincere share from 80 % to 44 %. We
therefore compared each result with two null models, one with imitation only and one with
experimentation only (Figure 9). With imitation only and a moral cost of $0.2B$, sincere giving held
its ground or grew in every regime, reaching 84 % in the sealed regime and 90 % under a full ledger.
With a moral cost of $0.05B$, the sincere share stayed at about 82 % in regimes T0 and T1 and fell to
75 % in regimes T2 and T3, where reciprocity and best responses became feasible.

> **Figure 9.** Share of sincere donors after 100 years without audits, under imitation only,
> imitation with experimentation, and experimentation only, by regime and moral cost. The dotted line
> marks the starting share of 80 %. `../reports/figures/E6_selection.png`

Anonymity led to defection, and transparency kept cartels together (Table 7). Defectors made up
about 3 % of the community in regimes T0 and T1 and none in regimes T2 and T3, where other members
detect them at once. With a moral cost of $0.2B$, 47 % of cartels survived to the end of the run in
the sealed regime, against 79 % when donors were revealed, and cartels that ended had lasted a median
of 20 and 38 years respectively.

**Table 7.** Cartels under each transparency regime (E6, 50 seeds).

| | T0 | T1 | T2 | T3 | T3 with peer reports |
|---|---|---|---|---|---|
| Defectors (share of community) | 3.2 % | 3.5 % | 0 | 0 | 0 |
| In cartels (moral cost 0.05B) | 15 % | 16 % | 20 % | 18 % | 1.8 % |
| Cartels alive at the end (moral cost 0.2B) | 47 % | 50 % | 79 % | 74 % | 7 % |
| Median life of ended cartels (moral cost 0.2B) | 20 years | 22 years | 38 years | 36 years | 7 years |

Reports by peers were the most effective measure against cartels, and audits by the platform were
weak. Under a full ledger, a probability of 0.1 per year that peers report a cartel reduced cartel
membership to below 2 %. Audits of return probabilities, held with probability 0.5 per year and
removing half of the funds of flagged donors, reduced membership only from 15 % to 12 % in the sealed
regime and from 20 % to 16 % when donors were revealed. An expected sanction of about a quarter of
the funds per year is small compared with a premium of about 2.

The share passed on was the strongest driver of strategic donating. In the hypercube of strategy
change, $\alpha$ was the leading factor for strategic play (PRCC +0.83) and for cartel membership
(+0.88), followed by the regime (+0.73), the moral cost (−0.55) and the rate of experimentation
(+0.29). The median share of strategic play was 20 % for $\alpha \le 0.3$ and 79 % for
$\alpha > 0.7$, and cartel membership rose from 6 % to 59 %. The same $\alpha$ that lets sincere
judgement shape funding also raises the gain from collusion, and in this experiment it decided how
far collusion spread.

Reputation feedback made collusion spread somewhat further (Figure 10). In E6-fb, with a moral cost
of $0.05B$ and no audits, feedback ($\lambda = 0.2$) raised the share of researchers in cartels by 1.6
percentage points (95 % interval 0.7–2.4) at $\omega = 0.3$ and by 3.1 points (2.3–3.9) at
$\omega = 0.6$, averaged over the four regimes and compared with the same seeds without feedback.
With a moral cost of $0.2B$, the increases were 0.2 points (−0.1 to 0.6) and 1.0 point (0.6–1.3).
The null model with imitation only gave the same result: cartel membership rose by 1.3–2.1 points in
every regime, and the sincere share fell by 0.8–3.3 points. The order of the regimes did not change.
The effect is small because E6 fixes $\alpha$ at 0.5, where feedback raised a fixed cartel's premium
by only 2–16 % above the bound (Table 5); we did not run strategy change with feedback at high
$\alpha$.

> **Figure 10.** Share in cartels, share of strategic play and output relative to equal split, with
> and without reputation feedback, by regime and moral cost (no audits).
> `../reports/figures/E6_feedback.png`

## The cost of gaming

At the default $\alpha = 0.5$, strategic donating cost little output. In E6, output relative to equal
split ranged from 5.1 % (full ledger, moral cost $0.05B$, no audits) to 8.1 % (full ledger, moral
cost $0.2B$, audits), against 7.3 % for sincere SOFA. Even with half of the community playing a
strategic rule, the loss was at most about 2 percentage points, roughly one sixth of the gain of the
ideal allocation over equal split. With reputation feedback, sincere SOFA gained 8.2 % over equal
split (E5) and strategic SOFA under a full ledger 5.6 % (E6-fb), a gap of about 2.6 points; because
the two experiments use different run lengths, this comparison is approximate. In the hypercube of
strategy change, however, output relative to equal split fell with $\alpha$ (PRCC −0.66) and with
the weight on reputation (−0.34). The cost of gaming is therefore small at moderate $\alpha$ and grows
where $\alpha$ is high.

These figures understate two costs. The aggregate measure of output gives little weight to who
loses: in the cartel experiments, most of the loss fell on the best researchers outside the cartel.
And at high $\alpha$, where the compounding through reputation was strongest, we did not run strategy
change with feedback.

## Sensitivity

Across the three hypercubes, four groups of parameters decided the results. Returns to funding
($\theta$) and the spread of quality ($\sigma_q$) decided whether SOFA, or any selective allocation,
was worth having at all. The share passed on ($\alpha$) decided the concentration of funding, the
position of early-career researchers, the cartel premium and the spread of strategic play. The moral
cost of strategic play and the rate of experimentation decided how far manipulation spread, and the
extent to which awareness follows visibility ($\tau$) decided equity. None of these parameters has
been measured for a real research community.

---

# Discussion

> **[PLACEHOLDER: to be written.]** Points to cover:

**Is SOFA a good idea, in the terms of the model?**
- Sincere SOFA is cheap and informative, but its gain over equal split depends on θ and σ_q.
- α sets both the effect of sincere judgement and the gain from collusion; no value of α is high on
  the first and low on the second.
- Equity: the early-career deficit comes from who knows whom. Possible remedies: exposure of
  newcomers, initial visibility, a reserved share.

**What gaming does, compared with sincere SOFA and with current practice**
- Cartels capture up to 1/(1 − αφ), more with reputation feedback; the cost falls on the best
  outsiders.
- At moderate α the aggregate loss is small (about 2 points); at high α strategic play dominates.
- Panels are not gamed in this model. Panels can be gamed too (review rings, lobbying,
  grantsmanship): add literature. Do not claim that gamed SOFA beats current practice.
- Link to the AI-driven rise in applications: SOFA needs no proposals, but it moves the incentive to
  game from writing to giving.

**Design implications**
- Safeguards must be combined: caps against rings, pairwise discounts against cliques, cycle-aware
  detection with a long enough horizon.
- Transparency cuts both ways: it enables reciprocity and best responses, and it enables detection.
  Peer reports under a full ledger were the strongest measure in the model.
- The reputation loop needs its own safeguard, for example visibility measured relative to funding
  received. Not tested.
- A targeted α, the analogue of the adaptive restart probability of Zhang et al. (2004): a lower
  share passed on only for donors whose receipts react strongly to α. Lowering α for everyone
  removed 75 % of the excess premium but cost 0.20 in efficiency. Not tested.
- The cartels in the model do not hide. Detecting colluding groups is NP-hard and return statistics
  can be disguised (Zhang et al. 2004), so the success of cycle-based rules against our rings is an
  upper bound.

**Relation to the literature**
- Collusion in PageRank-type rankings, impartial peer selection, lotteries and base funding.

**Limitations**
- Stylised model; no calibration of awareness networks, behaviour or production.
- One funder, funding of persons, one-year awards; no multi-year grants or teams.
- The behavioural rules (defection, imitation, moral cost) are assumptions; the defection rule is
  our own construction.
- Panels and lotteries are simplified and never gamed.
- Strategy change was run at α = 0.5 only, without turnover; with feedback only at α = 0.5. Cartels
  with turnover are not modelled.
- PRCC misses non-monotone and conditional effects (efficiency against α; cycle discount against
  rings).
- The production function with θ = 0.5 is an assumption.

**Next steps**
- Calibrate awareness from co-authorship and citation data (for example OpenAlex).
- Measure donor behaviour in an incentivised allocation game.
- Test safeguards against the reputation loop.

---

# Data and code availability

[To add: repository URL, commit hash, CoMSES model library entry, licence.] All results can be
reproduced with `python -m sofa.experiments run E<x> --seeds 50 --n 500`.

# Acknowledgements

[To add.]

# References

> JASSS author–year style. Check every entry before submission; [check] marks items not yet seen in
> the original.

Bianchi, F., Grimaldo, F., Bravo, G. & Squazzoni, F. (2018). The peer review game: An agent-based
model of scientists facing resource constraints and institutional pressures. *Scientometrics*,
116(3), 1401–1420.

Bol, T., de Vaan, M. & van de Rijt, A. (2018). The Matthew effect in science funding. *Proceedings
of the National Academy of Sciences*, 115(19), 4887–4890.

Bollen, J. (2018). Who would you share your funding with? *Nature*, 560, 143.

Bollen, J., Crandall, D., Junk, D., Ding, Y. & Börner, K. (2014). From funding agencies to
scientific agency. *EMBO Reports*, 15(2), 131–133.

Bollen, J., Crandall, D., Junk, D., Ding, Y. & Börner, K. (2017). An efficient system to fund
science: From proposal review to peer-to-peer distributions. *Scientometrics*, 110(1), 521–528.

Campbell, D. T. (1979). Assessing the impact of planned social change. *Evaluation and Program
Planning*, 2(1), 67–90.

Edmonds, B., Le Page, C., Bithell, M., Chattoe-Brown, E., Grimm, V., Meyer, R., Montañola-Sales,
C., Ormerod, P., Root, H. & Squazzoni, F. (2019). Different modelling purposes. *Journal of
Artificial Societies and Social Simulation*, 22(3), 6. [check author list]

Fang, F. C. & Casadevall, A. (2016). Research funding: The case for a modified lottery. *mBio*,
7(2), e00422-16.

Feliciani, T., Luo, J., Ma, L., Lucas, P., Squazzoni, F., Marušić, A. & Shankar, K. (2019). A
scoping review of simulation models of peer review. *Scientometrics*, 121(1), 555–594.

Fister, I., Jr., Fister, I. & Perc, M. (2016). Toward the discovery of citation cartels in citation
networks. *Frontiers in Physics*, 4, 49.

Graves, N., Barnett, A. G. & Clarke, P. (2011). Funding grant proposals for scientific research:
Retrospective analysis of scores by members of grant review panel. *BMJ*, 343, d4797.

Grimm, V., Railsback, S. F., Vincenot, C. E., Berger, U., Gallagher, C., DeAngelis, D. L., Edmonds,
B., Ge, J., Giske, J., Groeneveld, J., Johnston, A. S. A., Milles, A., Nabe-Nielsen, J., Polhill,
J. G., Radchuk, V., Rohwäder, M.-S., Stillman, R. A., Thiele, J. C. & Ayllón, D. (2020). The ODD
protocol for describing agent-based and other simulation models: A second update to improve
clarity, replication, and structural realism. *Journal of Artificial Societies and Social
Simulation*, 23(2), 7.

Gross, K. & Bergstrom, C. T. (2019). Contest models highlight inherent inefficiencies of scientific
funding competitions. *PLoS Biology*, 17(1), e3000065.

Gyöngyi, Z. & Garcia-Molina, H. (2005). Link spam alliances. *Proceedings of the 31st International
Conference on Very Large Data Bases*, 517–528.

Herbert, D. L., Barnett, A. G., Clarke, P. & Graves, N. (2013). On the time spent preparing grant
proposals: An observational study of Australian researchers. *BMJ Open*, 3(5), e002800.

Heyard, R., Ott, M., Salanti, G. & Egger, M. (2022). Rethinking the funding line at the Swiss
National Science Foundation: Bayesian ranking and lottery. *Statistics and Public Policy*, 9(1),
110–121.

Holzman, R. & Moulin, H. (2013). Impartial nominations for a prize. *Econometrica*, 81(1), 173–196.

Höylä, T., Bartneck, C. & Tiihonen, T. (2016). The consequences of competition: Simulating the
effects of research grant allocation strategies. *Scientometrics*, 108(1), 263–288.

Huang, D.-W. (2018). Optimal distribution of science funding. *Physica A*, 502, 613–618.

Katz, L. (1953). A new status index derived from sociometric analysis. *Psychometrika*, 18(1),
39–43.

Kurokawa, D., Lev, O., Morgenstern, J. & Procaccia, A. D. (2015). Impartial peer review.
*Proceedings of the 24th International Joint Conference on Artificial Intelligence*, 582–588.

Liu, M., Choy, V., Clarke, P., Barnett, A., Blakely, T. & Pomeroy, L. (2020). The acceptability of
using a lottery to allocate research funding: A survey of applicants. *Research Integrity and Peer
Review*, 5, 3. [check author list]

Marino, S., Hogue, I. B., Ray, C. J. & Kirschner, D. E. (2008). A methodology for performing global
uncertainty and sensitivity analysis in systems biology. *Journal of Theoretical Biology*, 254(1),
178–196.

Merton, R. K. (1968). The Matthew effect in science. *Science*, 159(3810), 56–63.

NIH (2025). Supporting fairness and originality in NIH research applications. Notice
NOT-OD-25-132, National Institutes of Health. [check title and date]

Page, L., Brin, S., Motwani, R. & Winograd, T. (1999). The PageRank citation ranking: Bringing order
to the web. Technical report, Stanford InfoLab.

Pier, E. L., Brauer, M., Filut, A., Kaatz, A., Raclaw, J., Nathan, M. J., Ford, C. E. & Carnes, M.
(2018). Low agreement among reviewers evaluating the same NIH grant applications. *Proceedings of
the National Academy of Sciences*, 115(12), 2952–2957.

Research Professional News (2025). UKRI urged to be 'transparent' after adopting grant lotteries.
[check date, author and whether a primary UKRI source exists]

Smaldino, P. E. & McElreath, R. (2016). The natural selection of bad science. *Royal Society Open
Science*, 3(9), 160384.

Squazzoni, F. & Gandelli, C. (2013). Opening the black-box of peer review: An agent-based model of
scientist behaviour. *Journal of Artificial Societies and Social Simulation*, 16(2), 3.

Squazzoni, F. & Takács, K. (2011). Social simulation that 'peers into peer review'. *Journal of
Artificial Societies and Social Simulation*, 14(4), 3.

Szabó, G. & Tőke, C. (1998). Evolutionary prisoner's dilemma game on a square lattice. *Physical
Review E*, 58(1), 69–73.

Thurner, S. & Hanel, R. (2011). Peer-review in a world with rational scientists: Toward selection of
the average. *The European Physical Journal B*, 84(4), 707–711.

Vaesen, K. & Katzav, J. (2017). How much would each researcher receive if competitive government
research funding were distributed equally among researchers? *PLoS ONE*, 12(9), e0183967.

Zhang, H., Goel, A., Govindan, R., Mason, K. & Van Roy, B. (2004). Making eigenvector-based
reputation systems robust to collusion. In S. Leonardi (Ed.), *Algorithms and Models for the
Web-Graph (WAW 2004)*, Lecture Notes in Computer Science 3243 (pp. 92–104). Berlin: Springer.

Candidates for the Discussion (not yet cited): Alon et al. (2011), Sum of us: strategyproof selection
from the selectors; Aziz et al. (2016), Strategyproof peer selection; Avin (2019), Mavericks and
lotteries; Bornmann (2011), Scientific peer review; Cheng & Friedman (2005), Sybilproof reputation
mechanisms; Cole, Cole & Simon (1981), Chance and consensus in peer review; Ferguson, Marcus &
Oransky (2014), The peer-review scam; Guthrie, Ghiga & Wooding (2018), What do we know about grant
peer review in the health sciences?; Merrifield & Saari (2009), Telescope time without tears;
Roebber & Schultz (2011), Peer review, program officers and science funding; Roumbanis (2019), Peer
review or lottery?; Szabó & Fáth (2007), Evolutionary games on graphs.

---

# Appendix A: ODD protocol

[To insert: `docs/ODD.md` (version 5), edited for publication: no milestone references or code
names, and the terms of the main text (sincere, defector, ideal allocation).]

# Appendix B: Parameters

[To insert: the full parameter table from `sofa.config.Params` with unit, default, range in the
sensitivity analysis and rationale. Draft of the main entries:]

| Parameter | Meaning | Default | Range in E7 |
|---|---|---|---|
| $N$ | number of researchers | 500 | 200–2000 |
| $\alpha$ | share of receipts passed on | 0.5 | 0.1–0.9 |
| $\sigma_q$ | spread of log quality | 0.5 | 0.2–1.0 |
| $\kappa$ | link between visibility and quality | 1.0 | 0–2 |
| $d$ | mean number of colleagues known | 40 | 10–100 |
| $\tau$ | link between awareness and visibility | 1.0 | 0–2 |
| $\sigma_p$ | perception error | 0.5 | 0–1.5 |
| $\omega$ | weight on reputation | 0.3 | 0–1 |
| $m$, $\beta$ | recipients per donor, exponent of perceived quality | 10, 1.0 | 3–100, 0.5–3 |
| $k$, $\varphi$ | cartel size, internal share | 5, 1.0 | 2–20, 0–1 |
| $c$ | per-recipient cap | off | 0.05–0.5 |
| $\delta$, $\delta_L$, $L$ | strength of S3 and S4, horizon of S4 | off, off, 3 | 0–1, 0–1, 2–5 |
| $\theta$ | returns to funding | 0.5 | 0.2–0.9 |
| $\lambda$ | speed of reputation feedback | 0 or 0.2 | 0–0.5 |
| $c_m$ | moral cost of strategic play (× B) | 0.05 | 0–0.2 |
| $\mu_s$ | rate of experimentation | 0.01 | 0–0.05 |

# Appendix C: Verification and supplementary results

[To insert: the E0 table of analytic against simulated values (largest differences below
$10^{-12}$), the shortfall of the cartel premium with N, and the burn-in analysis (reports/M1.md).
Supplementary figures: E1 line plots and equity, E2 member selection, E3 heatmaps, E5 trajectories,
E6 prevalence over time, E7 tornado and scatter plots.]
