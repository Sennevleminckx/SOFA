---
title: "Gaming self-organised funding: a toy agent-based model of SOFA"
author:
  - "Senne Vleminckx (University of Antwerp) [co-authors to add]"
target: "Journal of Artificial Societies and Social Simulation (JASSS)"
status: "Draft 0.1. Introduction and Discussion are placeholders."
---

<!--
Drafting notes (remove before submission)
- Source of all numbers: reports/M1.md … M6.md and reports/summary.md (commit 6a9b991).
  Default scale N = 500, 50 seeds, unless stated otherwise.
- Figures point to ../reports/figures/. Redraw for print at the end (titles off, JASSS sizes).
- Citation keys are in [Author Year] form. Check every reference before use (see the list at the end).
- Style: UK English, short sentences, one statement per sentence where possible.
-->

# Abstract

Self-Organised Funding Allocation (SOFA) gives every researcher an equal base amount and requires
each to pass a fixed fraction $α$ of all money received to colleagues of their choice. Earlier
evaluations used citations in place of donations, so donors were honest by construction. We{#Do U use 'we' in a single author paper?} built
a toy agent-based model to ask what happens when donors respond to incentives and information.
With fixed donations, the model has closed-form results. Funding is a Katz-type centrality of the
donation graph, and a cartel that routes a share φ of its donations internally multiplies its
funding by at most 1/(1 − αφ){#is it current practice in JASS to include equations in the abstract?}, whatever its quality. The simulations add four results. First,
honest SOFA raised expected output above an equal split only when returns to funding and the spread
of quality were large; it beat equal split in 70 % of the sampled parameter space. Second, the
cost of a cartel {#explain what a 'cartel' is} fell mostly on the best non-members {#this is unclear}. Third, with a reputation feedback loop, a
cartel's premium exceeded the static bound, up to about twice the bound on our grid {#this is unclear} . Fourth, each
step towards a public ledger made another strategy feasible, and $α$ was the strongest driver of how
far strategic play spread. Safeguards were specific to the shape of a cartel: per-recipient caps stopped
ring-shapes but not large cliques, and pairwise discounts stopped cliques but rewarded rings. These are
results for a stylised model with uncalibrated behaviour; they do not predict the performance of a real SOFA scheme. {# Avoid tell-tale LLM-grammar like X does this, it does not do Y}

**Keywords:** research funding; peer-to-peer allocation; collusion; agent-based model;
mechanism design; transparency

---

# 1 Introduction

{#add to the framing: due to the rise of LLM's, funders are currently flooded with proposals, far extending the capabilities of their reviewers; and monetary capabilities. see this --> https://maartenweyn.substack.com/p/by-2035-our-current-research-system; which is offcourse no real source. This roots this paper in a real timely issue of needing alternative research strategies. Furthermore, the intro seems quite extensive. I've removed the subheadings, i don't care for them. So unless thisi s required by JASSS, make sure it is clear from the body of the text.}
Most public research money is allocated by competition. Researchers write proposals, peers review
them, and a panel ranks them. This process is expensive. In the 2012 round of Australian NHMRC
Project Grants, a proposal took on average 34 working days of researcher time. The 3727
proposals took an estimated 550 working years, or AU$66 million in salary costs, and 21 % were
funded [Herbert et al. 2013] {#what is the prefered ref-style for JASSS? I prefer numbered}. More time spent on a proposal did not raise its chance of success. Contest models {#unclear what a contest model is} suggest that, at low success
rates, a large part of the value of a grant programme can be spent on the competition itself {#sentence is unclear}
[Gross & Bergstrom 2019].

{# A second (or third) issue is that the review process is also noisy} The process is also noisy. Graves et al. [2011] re-analysed panel scores of the Australian National
Health and Medical Research Council. After they allowed for variation between panel members, only
9 % of proposals were always funded, 61 % were never funded and 29 % were funded in some
re-samples but not in others. In a replication of NIH review, 43 reviewers rated the same 25
applications and showed no agreement on their quality [Pier et al. 2018]. Chance also has lasting
effects. Among applicants for an early-career grant in the Netherlands, those just above the
funding line received more than twice as much further funding over eight years as those just below
it [Bol et al. 2018]. Merton [1968] called this pattern the Matthew effect.

Three kinds of alternatives {#Alternative funding allocation strategies?} have been proposed. The first removes competition from part of the
budget {#this needs more explanation, both of the alternatives in this paragraph do. If we will refer to them later in intro/discussion, maybe give them a name: the lottery system and }. Vaesen and Katzav [2017] estimated that an equal share of competitive funds would let
researchers in the Netherlands, the United Kingdom and the United States keep current staffing
levels, with a moderate to considerable budget left for other costs. The second strategy keeps review but
uses chance where review cannot separate proposals [Fang & Casadevall 2016]. The Health Research
Council of New Zealand was the first major government funder to use a lottery, for its Explorer
Grants [Liu et al. 2020]. The Volkswagen Foundation and the Austrian Science Fund have also used
lotteries, and the Swiss National Science Foundation introduced one for proposals near the funding
line in its junior fellowship scheme [Heyard et al. 2022]. {#Didn't the UK just this year start with a lottery as well?}

The third kind, Self-Organised Funding Allocation (SOFA), moves the judgement from a panel to the community [Bollen et al. 2014, 2017]. In distributed peer review, applicants rank each other's proposals [Merrifield & Saari 2009; Kurokawa et al. 2015].
In SOFA, it removes proposals altogether by giving every researcher the same base amount each year. Each must then
pass a fixed fraction of everything they receive, for example half, to colleagues of their choice [Bollen et al. 2014, 2017].
Money circulates and, in theory, accumulates with the researchers whom the community values most.
The Dutch Parliament asked the Dutch Research Council (NWO) to explore such alternatives, and NWO
held a workshop to plan a SOFA pilot [Bollen 2018].

Bollen et al. [2017] tested SOFA with citation data. They used 37 million articles from the Web of
Science (1992–2010) and 867,872 researchers who published in every year from 2000 to 2010. Each
researcher's donations were set in proportion to their citations. The resulting distribution of
funding was similar to the distributions of NIH and NSF funding. The authors made clear that
citations were a proxy for each researcher's own judgement, not a proposed basis for donations.
Huang [2018] added cumulative advantage to a model of this kind and found regimes in which a small
elite captured a large share of the money.

These studies share one assumption. Donors are honest by construction: a citation is taken as
a signal of value. In a real SOFA scheme, donations are money, and donors know that money
they give can come back to them. Campbell [1979] stated the general risk: the more a quantitative
indicator is used for social decisions, the more it is subject to corruption pressures, and the
more it distorts the processes it is meant to monitor. Science offers examples: groups of authors cite each
other to raise their respective indicators [Fister et al. 2016]. Authors have reviewed their own papers under
false reviewer identities [Ferguson et al. 2014]. Incentives can also select poor practices without
any deliberate cheating, because the practices that pay are the ones that spread
[Smaldino & McElreath 2016]. A funding rule that pays researchers to route money is therefore
likely to meet routing strategies. {#This entire section (from 'Science offers examples') needs reworking. They seem unattached from eachother, and not worked out properly. better to decrease to number of examples, and work out what is relevant}

With fixed donations, SOFA's steady state is a Katz-type
centrality of the donation graph [Katz 1953], the same family as PageRank [Page et al. 1999].
Collusion in such rankings is well studied. Web pages can be linked in "*spam farms*" whose structure
maximises their rank, and alliances of farms can raise the rank of every member
[Gyöngyi & Garcia-Molina 2005]. Zhang et al. [2004] studied collusion in eigenvector-based reputation
systems and proposed changes to make them more robust. In SOFA the pass-on fraction plays the role of PageRank's damping
factor. Other peer-to-peer funding schemes face the same problem. The designers of quadratic {#not explained before as an alternative?}
funding, for example, discuss variants that protect against collusion
[Buterin et al. 2019].

Mechanism design asks a related question: can a group select its best members when every member
is also a candidate? An award rule is impartial if no member's report can change whether that
member wins. Impartial rules exist, but they are restrictive [Holzman & Moulin 2013; Alon et al.
2011]. Kurokawa et al. [2015] designed impartial versions of distributed peer review. SOFA is not
impartial. A donor's gift raises the receipts of the recipient, part of which the recipient passes
on, and part of that can return to the donor.

## 1.5 Agent-based models of science funding {#Is this really needed for JASSS? The intro is already quite long, also remove subtitle if we keep paragraph}

Agent-based models are a common tool for studying peer review, because large experiments with real
funding systems are hard to run. Feliciani et al. [2019] reviewed 46 simulation models of peer
review. They found many models with incompatible assumptions, few comparisons between models and
few empirical tests. In this journal, Squazzoni and Takács [2011] argued that peer review is a
problem of social interaction, and Squazzoni and Gandelli [2013] modelled how reciprocity among
referees affects the quality of review. Bianchi et al. [2018] treated journal peer review as a cooperation
dilemma and found that a moderate level of competition supports review quality when referees
review for reciprocity. Thurner and Hanel [2011] showed that a small share of selfish referees,
who have no interest in promoting good work other than their own, can lower the quality of
accepted work to the level of chance, and that mutual support networks of authors and referees
make it worse. For funding, Höylä et al. [2016] simulated four allocation strategies (equal
shares, lottery, a realistic panel and an ideal panel) and found strong effects on researchers'
careers. These models study strategic behaviour in peer review and the effect of allocation rules.
They do not study a peer-to-peer allocation rule, in which the reviewers are also the funders. To our knowledge, no published model has studied SOFA with donors who respond to the incentives
that SOFA itself creates.

We built a toy agent-based model of SOFA in which donors choose whom to fund. Its purpose is
theoretical exploration in the sense of Edmonds et al. [2019]. It shows what the mechanism can do
under stated assumptions; it does not predict what a real scheme would do.{# Avoid tell-tale LLM-grammar like X does this, it does not do Y}

The model has two layers. The first layer is analytic: with fixed donations, the steady state of
SOFA has a closed form, and so does the gain of a collusive group. The second layer is
behavioural: donors perceive quality with noise and with a bias towards reputation {#not entirely clear}. They can herd {#explain each, or refer to the section where?},
reciprocate, form cartels, shirk inside cartels and copy better-paid colleagues. A platform can make
the donation ledger more or less public and can apply safeguards.

We asked six questions {#Pose these as research questions}:

1. How do concentration and allocative efficiency depend on the pass-on fraction, perception noise
   and reputation bias when donors are honest?
2. How much can cartels gain, and who pays for it?
3. How does the transparency of the ledger change which strategies are feasible and stable?
4. Which safeguards reduce gaming, and what do they cost when everyone is honest?
5. Does a reputation feedback loop amplify cumulative advantage, and what happens to early-career
   researchers and small fields?
6. How does SOFA compare with equal split and with an ideal allocation, at the same budget?

The paper makes three contributions. First, it gives closed-form results for SOFA with fixed
donations and uses them to verify the simulation. Second, it shows that the parameter that makes
SOFA informative, the pass-on fraction, also sets the gain from collusion. This holds for the spread
of strategic behaviour as well as for a fixed cartel. Third, it shows that each safeguard we tested
blocks one cartel shape and misses another, and that reputation feedback creates a channel for
collusion that flow-based safeguards cannot see.

Section 2 describes the model, and Section 3 the experiments. Section 4 gives the results.
Section 5 discusses what they mean for the design of SOFA-like schemes, and what a toy model cannot
show.

---

# 2 Model

We describe the model in brief here. Appendix A gives the full ODD protocol [Grimm et al. 2020].
The model is written in Python [{#version}]. Code, configuration files and tests are
available at [repository / CoMSES link to add].

## 2.1 The SOFA mechanism

There are N researchers. Each receives a base amount $B$ each year ($B = 1$; money is scale-free).
Each researcher must donate a fraction α of everything received in the previous year and keeps
the rest for research. Let $W(t)$ be the $N × N$ donation matrix: $w_{ij}$ is the share of $i$'s donation
that goes to $j, w_{ii} = 0$, and each row sums to 1. Receipts $R$ and kept funds $K$ follow

$$R(t) = B\,\mathbf{1} + \frac{\text{pool}(t-1)}{N}\mathbf{1} + \alpha\,W(t)^\top R(t-1), \qquad K(t) = (1-\alpha)\,R(t). \tag{1}$$

The pool collects money that safeguards remove from donations {#unclear}. It is returned in equal shares the
next year. This lagged form follows Bollen et al. [2017].

## 2.2 Analytic properties with fixed donations

If $W$ does not change, Equation 1 converges geometrically at rate $α$ to

$$R^* = B\,(I - \alpha W^\top)^{-1}\mathbf{1}, \qquad K^* = (1-\alpha)\,R^*. \tag{2}$$

This is a Katz-type centrality of the donation graph [Katz 1953]. Four further results follow.

- **Conservation.** If the rows of $W$ sum to 1, then $ΣK* = N·B$. SOFA redistributes money; it does
  not create it. With a pool, conservation also holds at the steady state.
- **Degenerate cases.** With $α = 0$, or with uniform $W$, every researcher keeps $K = B$. {# Continue using $ $ where it is needed in text like I did}
- **Group balance.** For any group C, $ΣK$ over C equals $|C|·B$ plus the inflow into C minus the
  outflow from C.
- **Cartel premium.** Let a cartel C of $k$ members route a share $φ$ of their donations to each
  other and give the rest honestly to non-members. With $I_C$ the realised inflow from outsiders,
  the cartel keeps exactly

$$\sum_{i \in C} K_i = \frac{(1-\alpha)(kB + I_C)}{1 - \alpha\varphi}. \tag{3}$$

If the inflow from outsiders does not rise, the cartel's premium over its counterfactual funding is

$$\Pi = \frac{\sum_{i\in C} K_i(\text{cartel})}{\sum_{i\in C} K_i(\text{no cartel})} \le \frac{1}{1-\alpha\varphi}. \tag{4}$$

The bound does not depend on the members' quality. It is reached as $k/N → 0$. At $α = 0.5$ and
$φ = 1$ a cartel can double its funding; at $α = 0.9$ it can multiply it by ten. A ring cartel
($i₁ → i₂ → … → i_k → i₁$) has zero pairwise mutual flow but obtains the same premium as a clique.
A per-recipient cap c limits the internal share to $φ_{max} = min(1, (k − 1)c)$, so a clique with
$k ≥ 1/c + 1$ is not affected by the cap.

These results are the motivation for an agent-based model; with fixed donations, simulation does not add
anything to Equations 2–4. The model is needed where $W$ changes because donors respond to
incentives, information and reputation.

## 2.3 Entities and scales

- **Researchers.** N = 500 by default. Each has a latent quality q_i ~ LogNormal(0, σ_q), scaled to
  mean 1. Quality is not observed by any agent.
- **Fields and labs.** Five fields of unequal size (35, 25, 20, 12 and 8 % of researchers). Labs of
  about six researchers are nested in fields. The lab is the conflict-of-interest unit.
- **Career stages.** Early (40 %), mid (35 %) and senior (25 %), every lab has at least one senior.
- **Visibility.** v_i(0) = q_i^κ × a stage multiplier (0.5 / 1.0 / 1.5) × LogNormal(0, 0.3),
  scaled to mean 1. Visibility is reputation. It is correlated with quality but is not the same.
- **Time.** One step is one year. Runs last T = 60 years. Outcomes are averaged over the last 10.
  Experiments with strategy change run 100 years and average over the last 20.

## 2.4 Awareness and perception

A researcher can donate only to colleagues they know. The directed awareness network has
$P(i knows j) = min(1, p_f · v_j^τ)$, with $p_f$ ten times larger within a field than between fields.
The mean out-degree is 40 {#unclear}. Everyone knows their own lab. Visible researchers are known by more
people.

Researcher $i$ perceives the quality of $j$ as

$$\hat q_{ij} = q_j^{1-\omega}\, v_j^{\omega}\, \exp\!\left(\sigma_p\varepsilon_{ij} - \sigma_p^2/2\right), \qquad \varepsilon_{ij}\sim N(0,1). \tag{5}$$

The weight $ω$ sets the reliance on reputation instead of quality. The taste term $ε_{ij}$ is drawn once
and does not change {#unclear what this is and what it does}.

## 2.5 Donation strategies

All strategies act on the eligible set: the colleagues a donor knows, minus the donor, minus their
own lab when the conflict-of-interest rule is on.

- **Honest (sincere).** The donor scores each eligible colleague by perceived quality, keeps the
  m = 10 highest scores and gives in proportion to $score^β$.
- **Herder.** The donor tilts the honest score towards last year's high receivers, with weight $h$.
- **Reciprocator.** The donor gives a share $ρ$ back to last year's donors, in proportion to what
  each gave, and the rest honestly.
- **Cartel member.** The donor routes a share $φ$ inside the cartel and the rest honestly to
  non-members. In a clique, members give equally to all other members. In a ring, each gives to
  the next member. In a star, spokes give to the hub and the hub gives equally to the spokes.
- **Deferential** (early-career only). Honest, with an extra weight on seniors of the own field.
- **Best-responder.** The donor gives to the colleague whose receipts return the most money to the
  donor, using the return multipliers $(I − αWᵀ)⁻¹$ of last year's donation matrix.
- **Shirker {#strange word}.** A cartel member who secretly gives honestly while still receiving from partners.

## 2.6 Transparency regimes

The platform sees every flow {#unclear; typical LLM-style}, participants can see less {#(Table 1; or in text in stead of table)}. A strategy that the regime does not support falls back to honest giving.

| Regime | Participants observe | Strategies it makes feasible |
|---|---|---|
| T0 sealed | own receipts only | honest, cartel, deferential |
| T1 totals public | everyone's receipts last year | + herding |
| T2 donors revealed | T1 + identity and amount of own donors | + reciprocity |
| T3 full ledger | the whole flow matrix of last year | + best responses |

## 2.7 Safeguards

Each safeguard can be switched on alone. Money that a safeguard removes goes to the pool.{#Reads LLM-like}

- **S1 Conflict of interest.** No donations to own lab members.
- **S2 Per-recipient cap $c$.** No recipient may get more than a share $c$ of a donor's donation. The
  excess is spread over the donor's other recipients.
- **S3 Pairwise mutual-flow discount $δ$.** For each pair, both directions are reduced by $δ$ times the
  smaller of the two flows.
- **S4 Cycle-return discount ($δ_L, L$).** A donor's outgoing flows are scaled down by $δ_L$ times the
  share of their donation that returns to them within $L$ steps. The specified rule weights each step
  by $α$. A variant (S4u) uses the unweighted probability that a unit returns.
- **S5 Audit.** Each year, with probability $p_{audit}$, the platform removes a share $s$ of $K$ from donors
  whose unweighted return share exceeds a threshold.
- **Peer reports** (T3 only). Each cartel is reported by peers with probability $p_{peer}$ per year and
  is then sanctioned and dissolved.

## 2.8 Production and reputation feedback

Expected output is $ȳ_i = q_i (K_i/B)^θ (1 − cost_i)$ {#Not sure wether it is $(K_i/B)^θ$ or $(K_{i/B})^θ$}, with $0 < θ < 1$, so returns to funding
diminish. Realised output adds log-normal noise. The cost term is the share of research time spent
on the allocation mechanism: $c_{sofa} = 0.01$ for SOFA. When feedback is on, visibility follows output,

$$v_i(t+1) = (1-\lambda)\,v_i(t) + \lambda\, y_i(t)/\bar y(t). \tag{6}$$

With $λ > 0$ and $ω > 0$, funding raises output, output raises visibility, and visibility raises
perceived quality and therefore donations. Optional turnover replaces seniors (exit rate 1/35 per
year) with early-career newcomers. Optional contact resampling replaces a share $r_A$ of each
researcher's contacts each year, using current visibility.

## 2.9 Behaviour change

When adaptation is on{#"when adaption is on"; what is adaptation: a strategy? a policy? This needs to be clarified. don't expect to much pre-knowledge derived from context|This goes for this entire section. Some things are not clear at all for a reader without prior knowledge of our code}, each year a share $r_{imit} = 0.1$ of agents compares its payoff with that of
one random contact and copies the contact's visible strategy with a Fermi probability [Szabó &
Tőke 1998]. The payoff is $K_i$ minus a moral or reputational cost $c_m·B$ for strategic play, minus
sanctions. A share $μ_s = 0.01$ of agents mutates to a random strategy each year. A cartel member
shirks when the moral cost saved exceeds the funding it would lose by giving honestly. Shirkers are
detected with probability 1 under T2 and T3 and with probability $p_{low} = 0.1$ under T0 and T1, and
are then expelled. Imitating a cartel member means joining that cartel, up to 20 members.

## 2.10 Reference allocations

All reference allocations spend the same total $N·B$ per year and face the same production and
feedback.

- **A0 Equal split:** $K_i = B$.
- **A1 Oracle:** $K_i ∝ q_i^{1/(1−θ)}$, the allocation that maximises expected output.
- **A2 Honest SOFA:** all donors honest, sealed ledger, no safeguards. This is the scenario of
  Bollen et al. [2017].
- **A3 Simplified panel review** and **A4 lottery** are included as reference points. The
  panel scores applicants with noise and funds the top 20 %. Everyone also receives an equal base
  $(1 − α)·B$, which matches SOFA's guaranteed floor. Applicants lose 10 % of their output to writing
  and 1 % per review written, and complete three reviews each. Panels are never gamed in this model. The
  comparison is therefore between honest panels and SOFA, and we use it only for scale.

## 2.11 Parameters

Table 1{#Is this nescesarry in a JASSS paper? Should we not put this in Appendix?} lists the defaults and the ranges used in the sensitivity analysis. Behavioural parameters ($h$, $ρ$, $c_m$, $μ_s$, $r_{imit}$, $κ_F$) are assumptions {#These short sentences are also LLM=tells}.

**Table 1.** Main parameters {# add $$}. Full list with rationale: Appendix B.

| Parameter | Meaning | Default | Range in E7{#E7 comes out of nowhere} |
|---|---|---|---|
| N | researchers | 500 | 200–2000 |
| α | pass-on fraction | 0.5 | 0.1–0.9 |
| σ_q | spread of log quality | 0.5 | 0.2–1.0 |
| κ | visibility follows quality | 1.0 | 0–2 |
| d | mean number of contacts | 40 | 10–100 |
| τ | awareness follows visibility | 1.0 | 0–2 |
| σ_p | perception noise | 0.5 | 0–1.5 |
| ω | weight on reputation | 0.3 | 0–1 |
| m, β | recipients per donor, score exponent | 10, 1.0 | 3–100, 0.5–3 |
| k, φ | cartel size, internal share | 5, 1.0 | 2–20, 0–1 |
| c | per-recipient cap | off | 0.05–0.5 |
| δ, δ_L, L | S3 and S4 strength, S4 horizon | off, off, 3 | 0–1, 0–1, 2–5 |
| θ | returns to funding | 0.5 | 0.2–0.9 |
| λ | visibility feedback | 0 or 0.2 | 0–0.5 |
| c_m | moral cost of strategic play (× B) | 0.05 | 0–0.2 |
| μ_s | mutation rate | 0.01 | 0–0.05 |

---

# 3 Experiments and analysis

## 3.1 Design

Table 2 lists the experiments. Each experiment ran with 50 seeds at N = 500, and also at a
development scale (N = 300, 10 seeds). The two scales agreed in sign and approximate size for every
headline result. {#this needs more explanation. And if possible, it would be a good idea to link it to the RQ's}

**Table 2.** Experiments.

| | Question | Design | Mode |
|---|---|---|---|
| E0 | Verification | Fixed W, N = 400, 10 seeds: closed forms against simulation | both |
| E1 | Honest mechanics | α × σ_p × ω | solved |
| E2 | Cartel premium | α ∈ {0.2 … 0.9} × k ∈ {2, 3, 5, 10, 20} × φ ∈ {0.25 … 1} × topology × member selection | solved |
| E2-fb | Cartels with feedback | α ∈ {0.5, 0.8} × k ∈ {2, 5, 10} × φ ∈ {0.5, 1} × ω ∈ {0, 0.3, 0.6} × λ ∈ {0, 0.2} | simulated |
| E3 | Transparency | regime × share of herders, reciprocators or cartel members ∈ {0, 0.1, 0.25, 0.5} | both |
| E4 | Safeguards | S1–S4 and α, alone and combined, against cliques (k = 5, 11, 20) and rings (k = 3, 5) | solved |
| E5 | Feedback, equity, reference allocations | λ × ω × turnover × r_A × mechanism | simulated |
| E6 | Evolution | regime × audit × c_m, from 80 % honest, with two null models | simulated |
| E6-fb | Evolution with feedback | E6 × λ ∈ {0, 0.2} × ω ∈ {0.3, 0.6} | simulated |
| E7 | Global sensitivity | three Latin hypercubes of 1000 samples; PRCC | both |

## 3.2 Solved and simulated cells

Where $W$ cannot change between years, we used the steady state (Equation 2) instead of simulating {#make sure equations are numbered when we refactor in Latex later. now in markdown, they are not}.
With the nonlinear S3 discount we used the exact fixed point of Equation 1. Herders, reciprocators, feedback and adaptation make $W$ change, so those cells were always simulated. In each solved experiment we also simulated one cell year by year. The largest relative difference was 3.6 × 10⁻¹²{#unclear what this adds to the narrative without context}.

## 3.3 Common random numbers

Each random component (population, network, perception, strategies, production, adaptation) draws
from its own named stream of one master seed . Switching a mechanism on or off therefore leaves all
other draws unchanged{# are we sure of this? given the stochasticity in the model}. We computed each cartel premium against the same seed without the cartel.

## 3.4 Outcomes

- **Output relative to equal split** (primary): $Y_{net} / Y_{A0} − 1$, with $Y_{net}$ the expected output
  after mechanism overhead.
- **Allocative efficiency** $E = (Y − Y_{A0})/(Y_{A1} − Y_{A0})$. $E = 0$ is equal split and $E = 1$ is the
  oracle. The oracle gains only 13.3 % over equal split at the defaults, so $E$ magnifies small
  differences. We report it next to output, not instead of it{#X, not y; tell-tale}.
- **Concentration:** Gini(K) and the top-10 % share.
- **Cartel premium** Π (Equation 4) and **who pays**: the change in $K$ among non-members by quality
  decile.
- **Equity:** the early-career share of $K$ divided by their population share, and the same ratio for
  the smallest field.
- **Behaviour:** the share of agents who actually play a strategic rule (after fallbacks), the share
  in cartels, shirkers, cartel lifetimes.

## 3.5 Sensitivity analysis

E7 used three Latin hypercubes with 1000 samples each, one per model configuration. A single
hypercube would have forced safeguards and adaptation on in every sample, so every outcome would
describe a safeguarded, adaptive SOFA. The *mechanics* block (26 factors) samples honest SOFA with
feedback ($λ$ is a factor), plus one clique cartel and a panel for comparison. The *safeguards* block
(12 factors) uses fixed donations and is solved. The *evolution* block (10 factors) uses the E6
model. We computed partial rank correlation coefficients (PRCC) with Bonferroni-corrected tests
[Marino et al. 2008]. A dummy factor that the model never reads {#LLM-like wording} gave the noise floor; it was not
significant for any of 23 outcomes. PRCC assumes monotone relations, so we checked scatter plots of
each outcome against its leading factors. We did not compute Sobol indices{#answer inline to me: why not?}.

## 3.6 Verification

The test suite (326 tests) checks every analytic result of Section 2.2 to a tolerance of 10⁻¹⁰,
conservation under random W, α and safeguards (property-based tests), and that every mechanism,
when switched off, reproduces the simpler model bit for bit. In E0 the simulated steady state
matched Equation 2 to within 1.1 × 10⁻¹³ and Equation 3 held to within 2 × 10⁻¹³.{#entire paragraph unclear, entire section even. These also seem like results in a methods section}

The premium bound (Equation 4) held in every E0 cell. Larger cartels fell short of it, because
their withheld outflow lowers outsiders' receipts and so the cartel's own inflow. At α = 0.8 and
k = 5 the shortfall was 8.8 %, 4.7 % and 2.2 % for N = 200, 400 and 800. Two refinements came out of
verification. First, when a cap pushes money to the pool, members recapture a share $k/N$ of it, and
the bound must use $φ′ = φ_max + (1 − φ_max)k/N$. Second, pooled
money arrives one year later than direct flows, so runs with a pool need twice the burn-in{#needs twice the burn-in is not academic nor clear).

---

# 4 Results

## 4.1 Honest SOFA

With honest donors at the defaults, SOFA reached an allocative efficiency of E = 0.63 (95 % interval
0.62–0.64) and a rank correlation with quality of 0.82 (Table 3). Its expected output after
overhead was 7.3 % above equal split; the oracle reached 13.3 %. The Gini coefficient of funding was
0.40.

**Table 3.** Honest SOFA at the defaults (α = 0.5, σ_p = 0.5, ω = 0.3, θ = 0.5, λ = 0), mean over 50
seeds. Panel and lottery values are for honest applicants and reviewers.

| | Output vs equal split | E | Gini(K) | Overhead | Early-career ratio |
|---|---|---|---|---|---|
| A1 Oracle | +13.3 % | 1 | 0.52 | 0 % | 1.01 |
| A2 Honest SOFA | +7.3 % | 0.63 | 0.40 | 1 % | 0.69 |
| A0 Equal split | 0 | 0 | 0 | 0 % | 1.00 |
| A3 Panel (floor 1 − α) | −14.7 % | −0.15 | 0.40 | 13 % | 0.91 |
| A4 Lottery (floor 1 − α) | −17.6 % | −0.40 | 0.40 | 13 % | 0.95 |

**α sets concentration{# these types of short starts to a paragraph in bold are not typically done in science. Make sure to use the appropriate structure for prose, make a consistent story throughout. Check JASSS conventions}.** The Gini coefficient rose with α in all 36 combinations of σ_p and ω in
E1, and α was the leading factor for Gini across the hypercube (PRCC +0.97). Efficiency peaked at
intermediate α{# What does this <u>mean</u>?!}. In E7 the median E was 0.29 for α ≤ 0.3, 0.42 for 0.3 < α ≤ 0.7 and 0.21 for
α > 0.7. At high α combined with low noise or high reputation weight, SOFA did worse than equal
split (Figure 1).

**Perception noise had two effects.** Noise blurred the ranking, which lowered efficiency at low α.
Noise also made donors disagree, which spread money over more people and reduced over-concentration
at high α. With noiseless perception, all donors picked the same top researchers, and only 27 % of
researchers received any donation. At α = 0.9 and ω = 0.3, E rose from −0.59 at σ_p = 0 to +0.33 at
σ_p = 1. The hypothesis that efficiency falls with noise therefore held in only 15 % of the (ω, α)
cells. Efficiency fell with ω in every cell.

> **Figure 1.** Gini(K) and allocative efficiency E over α × σ_p × ω, honest donors.{# in the figure, we use 'sincere' in stead of honest. Make sure we are consistent}
> `../reports/figures/E1_surfaces.png`

**Whether SOFA beats equal split depends on two parameters we cannot observe.** In E7, honest SOFA
gave more output than equal split in 70 % of samples (p10 −5.4 %, median +4.5 %, p90 +51 %). The
leading factors were the spread of quality σ_q (PRCC +0.81) and the returns to funding θ (+0.75).
For θ ≤ 0.4 the median gain was +0.1 %; for θ > 0.6 it was +18 %. When returns diminish steeply,
no selective allocation gains much over an equal split. Honest SOFA gave more output than our
simplified panel in 98 % of samples. This mainly reflects the panel's assumed overhead (c_write
PRCC +0.63) and noise, and we do not interpret it further.

**Early-career researchers and small fields received less than their share.** At the defaults,
early-career researchers received 0.69 times their population share, and the smallest field 0.85
times its size. The ideal allocation gave 1.01, because quality does not depend on career stage in
the model. Across the hypercube the early-career ratio was below 1 in 97 % of samples (median 0.82),
and fell with α (PRCC −0.71) and with τ (−0.43). The cause is mainly the awareness network.
Early-career researchers start with low visibility, so fewer colleagues know them (mean in-degree
24, against 61 for seniors). Reputation feedback did not cause the deficit. Without turnover,
feedback raised the early-career ratio from 0.69 to 0.77, and feedback plus contact resampling
(r_A = 0.1) removed it (1.00, 95 % interval 0.98–1.03). With turnover the deficit persisted (0.70),
because every newcomer arrives with low visibility. The small-field deficit followed from group
balance: members of small fields have few in-field colleagues and send 47 % of their donations out
of the field. When the network gave every field the same in-field share of contacts, the deficit
disappeared (field ratios 0.98–1.01).

## 4.2 Cartels {#Subtitle was unclear. better to avoid subtitles, or use the RQ's?, or use my brief suggestions}

Without reputation feedback, the cartel premium followed Equation 4 closely (Table 4; Figure 2). A
5-member clique that routed all donations internally almost doubled its funding at α = 0.5 and
gained a factor of 4.8 at $α$ = 0.8. With $φ$ = 1, ring, clique and star cartels gained the same
aggregate premium, to machine precision{#to machine precision is NOT academic prose!}. Topology changed who inside the cartel received the money,
not how much the cartel received. In the full model, 0.3 % of the 62,400 E2 cells exceeded the
bound, by at most 0.8 %. All had φ < 1: internal equalisation sent some outside giving to
recipients who fed the cartel.

**Table 4.** Cartel premium $Π$, clique, φ = 1, random members, mean over 50 seeds.

| α | Bound $1/(1 − α)$ | k = 2 | k = 5 | k = 10 | k = 20 |
|---|---|---|---|---|---|
| 0.5 | 2 | 1.99 | 1.98 | 1.97 | 1.92 |
| 0.8 | 5 | 4.92 | 4.78 | 4.63 | 4.26 |
| 0.9 | 10 | 9.67 | 9.13 | 8.53 | 7.25 |

> **Figure 2.** Cartel premium Π against the bound 1/(1 − αφ), all E2 cells {#'the bound' is unclear; caption should explain what the viewer sees}.
> `../reports/figures/E2_premium_vs_bound.png`

**The relative premium did not depend on quality.** At $α$ = 0.9, a 5-member cartel of low-quality
researchers (bottom quartile) gained $Π$ = 9.97, close to the bound. A high-quality cartel (top
quartile) gained 7.76, because part of its counterfactual inflow depended on its own outflow coming
back. In absolute terms however, the high-quality cartel gained more than the low-quality: 19.5 $B$ per member per year vs. 1.0 $B$, respectively.

**The cost fell on the best non-members.** Cartel members withdraw the honest donations they would
otherwise have made, and those donations went mostly to high-quality researchers. At α = 0.8 and
k = 5, the top quality decile of no n-members bore 55 % of the outsiders' loss, and the top two
deciles 75 % (Figure 3). Gaming SOFA therefore moves money away from the researchers that an ideal
allocation would fund most.

> **Figure 3.** Who pays: change in K among non-members, by quality decile.
> `../reports/figures/E2_who_pays.png`

**Widespread collusion lowered efficiency.** In E3, when half the population formed 5-member
cliques, E fell by 0.35 (95 % interval 0.35–0.36) relative to all-honest SOFA. With the oracle's {#'oracle' is such a strange word}
gain at 13.3 % of output, this is about 4.7 percentage points of output. Gini fell, because randomly
chosen members pooled money among themselves. Herding by half the population lowered E by 0.13.
Reciprocity lowered it by only 0.015 and made funding more equal.

## 4.3 With reputation feedback, the cartel premium compounds {#compounds is an LLM-word. See prev feedback on subtitles. here: 'Reputation Feedback'?}

Equation 4 assumes that outsiders do not give more to the cartel. Reputation feedback breaks that
assumption. The cartel's extra money raises its output, output raises visibility, and, when
donors weight reputation ($ω > 0$), visibility raises honest outsiders' donations to members.

In E2-fb, the premium stayed at or below the bound whenever one part of the loop was off (λ = 0:
maximum 1.002 times the bound; ω = 0: maximum 1.001). With both parts on, it exceeded the bound
(Table 5; Figure 4). At α = 0.8, φ = 1 and ω = 0.6, a 5-member clique ended with 9.6 times its
counterfactual funding, against a static bound of 5. A 2-member clique reached 11.0 times. Smaller
cartels gained more relative to the bound, because the extra visibility was shared by fewer
members. The excess built up over 6–7 years at α = 0.5 and 10–13 years at α = 0.8, then levelled off.

**Table 5.** Π divided by the static bound 1/(1 − αφ), k = 5, mean [95 % interval] over 50 seeds.

| α, φ | λ = 0 | λ = 0.2, ω = 0 | λ = 0.2, ω = 0.3 | λ = 0.2, ω = 0.6 |
|---|---|---|---|---|
| 0.5, 0.5 | 0.99 | 0.99 | 1.02 [1.02, 1.03] | 1.05 [1.04, 1.07] |
| 0.5, 1 | 0.99 | 0.99 | 1.06 [1.05, 1.08] | 1.16 [1.12, 1.20] |
| 0.8, 0.5 | 0.99 | 0.99 | 1.06 [1.04, 1.09] | 1.18 [1.09, 1.27] |
| 0.8, 1 | 0.96 | 0.96 | 1.28 [1.20, 1.35] | 1.91 [1.63, 2.19] |

> **Figure 4.** Cartel premium relative to the static bound over time (left) and in the evaluation
> years (right), with and without feedback. `../reports/figures/E2_feedback.png`

Furthermore, this was confirmed in the hypercube experiment: the premium exceeded 1.05 times the bound in 19 % of samples. The share
rose with ω: 4 % for ω < 0.25 and 28 % for ω > 0.75. The largest ratio, 11.9, came from an extreme
sample (k = 2, α = 0.79, φ = 0.95, ω = 0.94). We report it as an illustration of the channel {#Channel?}, not
as a likely value. Under feedback, collusion turns money into reputation, and reputation attracts
honest money. The flows that carry this extra money are honest donations, so no flow-based
safeguard in the model can see them.

## 4.4 Safeguards

Table 6 shows the share of the excess premium ($Π − 1$) that each safeguard removed, and its
collateral cost: the loss of $E$ when every donor is honest (Figure 5).

**Table 6.** Share of the excess premium removed (α = 0.5, φ = 1, 50 seeds) and collateral cost.
Negative values mean the premium rose.

| Safeguard | Clique 5 | Clique 11 | Clique 20 | Ring 3 | Ring 5 | Collateral ΔE |
|---|---|---|---|---|---|---|
| S1 conflict of interest | 0.02 | — | — | 0.03 | 0.01 | 0.016 |
| S2 cap c = 0.1 | 0.75 | 0.00 | 0.00 | 0.95 | 0.95 | 0.001 |
| S2 cap c = 0.05 | 0.89 | 0.66 | 0.09 | 0.97 | 0.97 | 0.159 |
| S3 pairwise δ = 1 | 0.83 | 0.80 | 0.76 | −0.07 | −0.07 | 0.002 |
| S4 cycle, α-weighted, L = 5 | 0.34 | 0.16 | 0.09 | 0.40 | 0.12 | 0.000 |
| S4u cycle, unweighted, L = 5 | 0.91 | 0.53 | 0.32 | 1.00 | 1.00 | 0.000 |
| S1 + S2 (0.1) + S3 | 0.91 | 0.81 | 0.78 | 0.91 | 0.91 | 0.025 |
| α lowered to 0.2 | 0.75 | 0.75 | 0.74 | 0.75 | 0.75 | 0.195 |

> **Figure 5.** Safeguards against one cartel: premium removed (left) and collateral cost (right).
> `../reports/figures/E4_dotplot.png`

The table shows five results. (1) A ring member gives everything to one recipient, so
a cap of c = 0.1 removed 95 % of the ring premium. An honest donor with ten recipients rarely
gives anyone more than 10 %, so the collateral cost was close to zero. However, cliques of 11 or more
members spread their internal giving thinly enough to pass under the cap and did not lose anything. (2) the pairwise discount (S3) removed most of a clique's premium, but the ring
premium rose by 7 %. S3 taxes the ordinary two-way flows of honest donors. Ring members give
nothing to outsiders, so their flows are never mutual and escape the tax. (3) in the α-weighted cycle, each returning step is weighted by α, so a 5-ring has a
return share of only α⁴ = 0.06 at α = 0.5. The unweighted variant removed ring premiums
completely, but only when its horizon L was at least the ring length, and it was weak against
large cliques. (4) Combined rules covered more shapes at a cost of about 0.025 in E, mostly from the
conflict-of-interest rule, which removes labmates from honest donors' choice sets. (5)Lowering α works against every shape, but costs signal. At α = 0.2 every cartel lost 75 % of
its excess premium, and honest SOFA lost 0.20 in E.

In the hypercube, collateral costs were small (median 0.0, p90 0.3 percentage points of output).
At α > 0.7 they were negative in 96 % of samples: caps and discounts curbed over-concentration and
so raised honest output. The cycle rule had no significant PRCC on Π, because it acts only through
an interaction (rings with L ≥ k). The design of E4 shows this effect; PRCC cannot.{#final paragraph here must be clearer}

## 4.5 Transparency

Each step towards a public ledger made another strategy feasible {#explain these steps, or refer to them}. Under adaptation{#vague}, the share of
agents who actually played a strategic rule rose from 12 % under T0 to 24 %, 41 % and 51 % under T1,
T2 and T3 (c_m = 0.05, no audits). Across the evolution hypercube the medians were 12, 29, 49 and
64 %.

Mutation alone (no imitation) took the honest share from 80 % to 44 %. We therefore compare each result with two null models (Figure 6). With
imitation only, honest giving held or grew when strategic play carried a moral cost of $0.2·B$: the
honest share rose from 80 % to between 84 % (T0) and 90 % (T3). At a moral cost of 0.05·B, honest
giving held under T0 and T1 (about 82 %), but fell to 75 % under T2 and T3, where reciprocity and
best responses became feasible.

> **Figure 6.** Honest share after 100 years under imitation only, imitation plus mutation, and
> mutation only, by regime and moral cost. `../reports/figures/E6_selection.png`

**Anonymity produced shirking; transparency stabilised cartels.** Shirkers made up about 3 % of the
population under T0 and T1, and none under T2 and T3, where partners detect them at once. With a
moral cost of 0.2·B, 47 % of cartels survived to the end under T0, against 79 % under T2. The median
life of cartels that ended was 20 years under T0 and 38 years under T2 (Table 7).

**Table 7.** Cartels under each regime (E6, 50 seeds).

| | T0 | T1 | T2 | T3 | T3 + peer reports |
|---|---|---|---|---|---|
| Shirkers (share of population) | 3.2 % | 3.5 % | 0 | 0 | 0 |
| In routing cartels (c_m = 0.05) | 15 % | 16 % | 20 % | 18 % | 1.8 % |
| Cartels alive at the end (c_m = 0.2) | 47 % | 50 % | 79 % | 74 % | 7 % |
| Median life of ended cartels (c_m = 0.2) | 20 y | 22 y | 38 y | 36 y | 7 y |

**Peer reports were the strongest measure; platform audits were weak.** Under a full ledger, a
report probability of 0.1 per cartel per year cut cartel membership to under 2 %. Platform audits on
return shares (p_audit = 0.5, sanction 0.5 of K) reduced membership only from 15 % to 12 % under T0
and from 20 % to 16 % under T2. An expected sanction of about a quarter of K per year is small
against a premium of about 2.

**α decided how far strategic play spread.** In the evolution hypercube, α was the leading factor for
strategic play (PRCC +0.83) and cartel membership (+0.88). Median strategic play was 20 % for
α ≤ 0.3 and 79 % for α > 0.7; cartel membership rose from 6 % to 59 %. The regime (+0.73), the moral
cost (−0.55) and the mutation rate (+0.29) followed. The same α that makes honest SOFA informative
also makes collusion pay, and this now holds for behaviour as well as for a fixed cartel.

## 4.6 Collusion under imitation with reputation feedback

We repeated E6 with reputation feedback on (λ = 0.2) at two reputation weights (ω = 0.3 and 0.6).
Each feedback cell was compared with the same seed and the same ω without feedback (Figure 7).

Feedback made collusion spread a little further. With a moral cost of 0.05·B and no audits,
averaged over the four regimes, the share in routing cartels rose by 1.6 percentage points (95 %
interval 0.7–2.4) at ω = 0.3 and by 3.1 points (2.3–3.9) at ω = 0.6. With a moral cost of 0.2·B
the rise was 0.2 points (−0.1 to 0.6) and 1.0 point (0.6–1.3). The null model with imitation only
gave the same picture: at c_m = 0.05, cartel membership rose by 1.3–2.1 points in every regime,
and the honest share fell by 0.8–3.3 points. Shirking rose slightly under T0 and T1 (at most 1
point). The ordering of the regimes did not change: strategic play still rose from T0 to T3.

Output relative to equal split rose with feedback, by 0.5–1.7 percentage points. Feedback also
helps honest donors, because visibility then follows output. In E5, honest SOFA at ω = 0.3 gained
+8.2 % over equal split with feedback against +7.3 % without. Gamed SOFA under a full ledger
(T3, c_m = 0.05, no audits) reached +5.6 % with feedback. The gap to honest SOFA was therefore
about 2.6 percentage points with feedback and 2.2 points without. This comparison combines two
experiments with different horizons and is approximate.

> **Figure 7.** E6 with and without reputation feedback: share in routing cartels, strategic play
> and output relative to equal split, by regime and moral cost (no audits).
> `../reports/figures/E6_feedback.png`

The effect was smaller than the compounding of Section 4.3 might suggest. E6 fixes α at 0.5, where
feedback raised a fixed cartel's premium by only 2–16 % above the static bound (Table 5). The large
excess in Table 5 arose at α = 0.8. We did not test evolution with feedback at high α.

## 4.7 What gaming costs in output

At the default α = 0.5, the output cost of strategic behaviour was modest. In E6, output relative to
equal split ranged from +5.1 % (T3, c_m = 0.05, no audits) to +8.1 % (T3, c_m = 0.2, audits),
against +7.3 % for all-honest SOFA. Even with half the population playing strategically, gamed SOFA
lost at most about 2 percentage points, roughly a sixth of the oracle's gain over equal split. In
the evolution hypercube, however, output relative to equal split fell with α (PRCC −0.66) and with
ω (−0.34). The cost of gaming is therefore small at moderate α and grows where α is high, which is
also where honest SOFA is most informative per unit of money passed on.

These figures leave out two costs. First, the who-pays result (Section 4.2) means that gaming
reallocates money away from the best researchers, which an aggregate output measure with
θ = 0.5 under-weights. Second, with reputation feedback at α = 0.5 the gap to honest SOFA widened
only slightly (Section 4.6), but the compounding of Section 4.3 is much stronger at high α, where
we did not test evolution with feedback.

## 4.8 Which parameters decide the outcome

Across the three hypercubes, four groups of parameters decided the results:

1. **θ and σ_q** decided whether SOFA, or any selective allocation, was worth having.
2. **α** decided nearly everything else: concentration, equity, the cartel premium and the spread of
   strategic play.
3. **c_m and μ_s** decided how far manipulation spread.
4. **τ**, the extent to which awareness follows visibility, decided equity.

---

# 5 Discussion

> **[PLACEHOLDER: to be written.]** Points to cover:

**5.1 Is SOFA a good idea? (answer in the model's terms)**
- Honest SOFA is cheap and informative, but its gain over equal split depends on θ and σ_q.
- α is a single dial for signal and for manipulability; there is no α that is high on signal and
  low on gaming.
- Equity: the early-career deficit comes from who knows whom, not from the funding rule as such.
  Possible remedies: network exposure, newcomer visibility, ring-fenced shares.

**5.2 What gaming does, compared with honest SOFA and with the current system**
- Cartels capture up to 1/(1 − αφ), more with reputation feedback; the cost falls on top outsiders.
- At moderate α the aggregate output loss is small (≤ 2 pp); at high α strategic play dominates.
- Panel review is not gamed in our model. Panels can be gamed too (review rings, lobbying,
  grantsmanship): add literature. Do not claim that gamed SOFA beats the current system.

**5.3 Design implications (hedged)**
- Safeguards must be layered: caps against rings, pairwise discounts against cliques, cycle-aware
  detection with a long enough horizon.
- Transparency is double-edged: it enables reciprocity and best responses but also enables
  detection; peer reporting under a full ledger was the strongest measure in the model.
- The reputation channel needs its own safeguard (for example, normalising visibility by funding
  received). Not tested.

**5.4 Relation to the literature**
- Link to collusion in PageRank-type systems, quadratic funding, impartial peer selection.
- Link to lottery and base-funding debates.

**5.5 Limitations**
- Toy model; no calibration of awareness networks, behaviour or production.
- Single funder, person-based, single-year funding; no multi-year grants or teams.
- Behavioural rules (shirking, imitation, moral cost) are assumptions; the shirking rule is our
  construction.
- Panels and lotteries are simplified and honest.
- Evolution experiments fix α = 0.5 and exclude turnover; evolution with feedback was tested only
  at α = 0.5. Cartels with turnover are not modelled.
- PRCC misses non-monotone and interaction effects (efficiency against α; S4 against rings).
- Output with θ = 0.5 is an assumed production function.

**5.6 Next steps**
- Calibrate awareness from co-authorship and citation data (for example, OpenAlex).
- Elicit donor behaviour in an incentivised allocation game.
- Test safeguards against the reputation channel.

---

# Data and code availability

[To add: repository URL, commit hash, CoMSES model library entry, licence.] All results can be
reproduced with `python -m sofa.experiments run E<x> --seeds 50 --n 500`.

# Acknowledgements

[To add.]

# References

> **[PLACEHOLDER.]** JASSS uses author–year citations. Entries below are those cited in the text
> or listed for the introduction. Check every bibliographic detail before submission.

- Alon N, Fischer F, Procaccia A, Tennenholtz M (2011). Sum of us: strategyproof selection from the
  selectors. *TARK 2011*.
- Aziz H, Lev O, Mattei N, Rosenschein JS, Walsh T (2016). Strategyproof peer selection. *AAAI 2016*.
- Bianchi F, Grimaldo F, Bravo G, Squazzoni F (2018). The peer review game: an agent-based model
  of scientists facing resource constraints and institutional pressures. *Scientometrics*
  116:1401–1420.
- Bol T, de Vaan M, van de Rijt A (2018). The Matthew effect in science funding. *PNAS*
  115(19):4887–4890.
- Bollen J (2018). Who would you share your funding with? *Nature* 560:143.
- Bollen J, Crandall D, Junk D, Ding Y, Börner K (2014). From funding agencies to scientific agency.
  *EMBO Reports* 15(2):131–133.
- Bollen J, Crandall D, Junk D, Ding Y, Börner K (2017). An efficient system to fund science: from
  proposal review to peer-to-peer distributions. *Scientometrics* 110(1):521–528.
  doi:10.1007/s11192-016-2110-3
- Buterin V, Hitzig Z, Weyl EG (2019). A flexible design for funding public goods. *Management
  Science* 65(11):5171–5187.
- Campbell DT (1979). Assessing the impact of planned social change. *Evaluation and Program
  Planning* 2(1):67–90.
- Edmonds B et al. (2019). Different modelling purposes. *JASSS* 22(3):6.
- Fang FC, Casadevall A (2016). Research funding: the case for a modified lottery. *mBio* 7(2).
- Feliciani T, Luo J, Ma L, Lucas P, Squazzoni F, Marušić A, Shankar K (2019). A scoping review of
  simulation models of peer review. *Scientometrics* 121(1):555–594.
- Ferguson C, Marcus A, Oransky I (2014). Publishing: the peer-review scam. *Nature* 515.
- Fister I Jr, Fister I, Perc M (2016). Toward the discovery of citation cartels in citation
  networks. *Frontiers in Physics* 4.
- Graves N, Barnett AG, Clarke P (2011). Funding grant proposals for scientific research: retrospective
  analysis of scores by members of grant review panel. *BMJ* 343.
- Grimm V et al. (2020). The ODD protocol … second update. *JASSS* 23(2):7.
- Gross K, Bergstrom CT (2019). Contest models highlight inherent inefficiencies of scientific
  funding competitions. *PLoS Biology* 17(1):e3000065.
- Gyöngyi Z, Garcia-Molina H (2005). Link spam alliances. *VLDB 2005*, 517–528.
- Herbert DL, Barnett AG, Clarke P, Graves N (2013). On the time spent preparing grant proposals:
  an observational study of Australian researchers. *BMJ Open* 3:e002800.
- Heyard R, Ott M, Salanti G, Egger M (2022). Rethinking the funding line at the Swiss National
  Science Foundation: Bayesian ranking and lottery. *Statistics and Public Policy* 9(1):110–121.
- Holzman R, Moulin H (2013). Impartial nominations for a prize. *Econometrica* 81(1):173–196.
- Huang D-W (2018). Optimal distribution of science funding. *Physica A* 502:613–618.
- Höylä T, Bartneck C, Tiihonen T (2016). The consequences of competition: simulating the effects
  of research grant allocation strategies. *Scientometrics* 108:263–288.
- Katz L (1953). A new status index derived from sociometric analysis. *Psychometrika* 18(1).
- Kurokawa D, Lev O, Morgenstern J, Procaccia AD (2015). Impartial peer review. *IJCAI 2015*, 582–588.
- Liu M et al. (2020). The acceptability of using a lottery to allocate research funding. *Research
  Integrity and Peer Review* 5.
- Marino S, Hogue IB, Ray CJ, Kirschner DE (2008). A methodology for performing global uncertainty
  and sensitivity analysis in systems biology. *J Theor Biol* 254:178–196.
- Merrifield MR, Saari DG (2009). Telescope time without tears. *Astronomy & Geophysics* 50(4).
- Merton RK (1968). The Matthew effect in science. *Science* 159.
- Page L, Brin S, Motwani R, Winograd T (1999). The PageRank citation ranking. Stanford InfoLab.
- Pier EL et al. (2018). Low agreement among reviewers evaluating the same NIH grant applications.
  *PNAS* 115(12):2952–2957.
- Smaldino PE, McElreath R (2016). The natural selection of bad science. *Royal Society Open
  Science* 3:160384.
- Squazzoni F, Gandelli C (2013). Opening the black-box of peer review: an agent-based model of
  scientist behaviour. *JASSS* 16(2):3.
- Squazzoni F, Takács K (2011). Social simulation that "peers into peer review". *JASSS* 14(4):3.
- Szabó G, Tőke C (1998). Evolutionary prisoner's dilemma game on a square lattice. *Phys Rev E* 58:69.
- Thurner S, Hanel R (2011). Peer-review in a world with rational scientists: toward selection of
  the average. *Eur Phys J B* 84:707–711.
- Vaesen K, Katzav J (2017). How much would each researcher receive if competitive government
  research funding were distributed equally among researchers? *PLoS ONE* 12(9).
- Zhang H, Goel A, Govindan R, Mason K, Van Roy B (2004). Making eigenvector-based reputation systems
  robust to collusion. *WAW 2004*, LNCS 3243.

Candidates for the Discussion (not yet cited):

- Roebber PJ, Schultz DM (2011). Peer review, program officers and science funding. *PLoS ONE* 6(4).
- Avin S (2019). Mavericks and lotteries. *Studies in History and Philosophy of Science A* 76:13–23.
- Bornmann L (2011). Scientific peer review. *Annual Review of Information Science and Technology* 45.
- Cheng A, Friedman E (2005). Sybilproof reputation mechanisms. *P2PECON 2005*.
- Cole S, Cole JR, Simon GA (1981). Chance and consensus in peer review. *Science* 214.
- Davis P (2012). The emergence of a citation cartel. *The Scholarly Kitchen* (blog).
- Guthrie S, Ghiga I, Wooding S (2018). What do we know about grant peer review in the health
  sciences? *F1000Research* 6.
- Roumbanis L (2019). Peer review or lottery? *Science, Technology, & Human Values* 44(6).
- Szabó G, Fáth G (2007). Evolutionary games on graphs. *Physics Reports* 446.

---

# Appendix A: ODD protocol

[To insert: `docs/ODD.md` (version 5), edited for publication. Remove internal milestone references
and code names.]

# Appendix B: Full parameter table

[To insert: `sofa.config.Params`, with unit, default, range and rationale per parameter.]

# Appendix C: Supplementary results

[Candidates: E1 line plots and equity panels; E2 member selection; E3 heatmaps; E5 trajectories
and equity with turnover; E6 prevalence over time; E7 tornado plots and scatter plots for all three
blocks. Files in `reports/figures/`.]
