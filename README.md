# SOFA-ABM

A toy agent-based model of **Self-Organised Funding Allocation** (Bollen et al. 2014, 2017):
every researcher receives an equal base amount each year and must pass a fixed fraction α of
everything they receive on to colleagues of their choice. The model asks what happens when donors
respond to incentives and information (cartels, herding, reciprocity, transparency, safeguards).

The full specification is in [`CLAUDE.md`](CLAUDE.md). Checkpoint reports are in [`reports/`](reports/).

**Status:** all six milestones built (M6: global sensitivity analysis E7, final figures, complete
ODD), awaiting review of M6. Findings in one page: [`reports/summary.md`](reports/summary.md).
Checkpoint reports: `reports/M1.md` … `reports/M6.md`.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Python ≥ 3.11.

## Usage

```bash
pytest                                                      # full test suite
python -m sofa.experiments run E0 --seeds 10 --n 400 --out results/
python -m sofa.experiments plot E0 --out results/
python -m sofa.experiments run E1 --seeds 10 --n 300 --out results/dev   # development scale
python -m sofa.experiments run E1 --seeds 50 --n 500 --out results/full  # full scale
python -m sofa.experiments plot E1 --out results/full
for E in E2 E3 E4 E5 E6; do python -m sofa.experiments run $E --seeds 50 --n 500 --out results/full; done
for E in E2 E3 E4 E5 E6; do python -m sofa.experiments plot $E --out results/full; done
python -m sofa.experiments run E7 --seeds 1000 --n 500 --out results/full  # 1000 LHS samples
python -m sofa.experiments plot E7 --out results/full
```

For E7, `--seeds` is the number of Latin hypercube samples (each with its own seed) and `--n` sets N
where N is not itself a factor (the evolution block). The full E7 run takes about two hours on four
cores, mostly the mechanics block at N up to 2000.

Cells in which the donation matrix cannot change between years are solved directly rather than
simulated (guarded by `SOFAModel.is_static()`, with one annual cross-check per experiment).

A single model run:

```python
from sofa import Params
from sofa.model import SOFAModel

res = SOFAModel(Params(alpha=0.6), seed=1).run()
res.summary()  # means over the last T_eval years

# a 5-member ring cartel under the cycle-return discount, solved directly
m = SOFAModel(Params(cartels=True, topology="ring", delta_L=1.0, L=5), seed=1)
R, K, W = m.equilibrium()

# panel review (equal base 1 − α by default) under reputation feedback and turnover
SOFAModel(Params(mechanism="panel", lam=0.2, turnover=True), seed=1).run()

# strategies evolving by imitation under full transparency, with platform audits
SOFAModel(Params(adaptation=True, cartels=True, x_C=0.05, x_herd=0.05, regime="T3",
                 p_audit=0.5, T=100, T_eval=20), seed=1).run()

# partial rank correlations of any outcome table against its sampled factors
from sofa.sensitivity import Factor, latin_hypercube, prcc
X = latin_hypercube([Factor("alpha", 0.1, 0.9), Factor("dummy")], n=200, seed=0)
```

Experiment seeds run in parallel (joblib) with one BLAS thread per worker; without that limit
the workers oversubscribe the cores and dense solves slow down by two orders of magnitude.

Results are written as parquet (with config hash and git commit in the file metadata) to
`results/<experiment>/`, figures to `results/<experiment>/figures/` (PNG and PDF).

## Layout

```
src/sofa/      config, rng, flows, population (incl. strategy roles), network, perception,
               information (regimes), strategies, safeguards (S1–S4), production (output,
               feedback, turnover), adaptation (imitation, shirking, audits S5, best
               responses), baselines (A0–A4), metrics, model, experiments (CLI),
               sensitivity (LHS, PRCC), plotting
docs/ODD.md    ODD protocol
experiments/   YAML configurations per experiment
tests/         analytic (§2.3) and mechanical tests
reports/       checkpoint reports M1.md … M6.md, one-page summary, figures/
```
