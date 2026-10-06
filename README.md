# SOFA-ABM

A toy agent-based model of **Self-Organised Funding Allocation** (Bollen et al. 2014, 2017):
every researcher receives an equal base amount each year and must pass a fixed fraction α of
everything they receive on to colleagues of their choice. The model asks what happens when donors
respond to incentives and information (cartels, herding, reciprocity, transparency, safeguards).

The full specification is in [`CLAUDE.md`](CLAUDE.md). Checkpoint reports are in [`reports/`](reports/).

**Status:** Milestone 5 complete (imitation, mutation, shirking and detection, S5 audits, peer
reports, best-responders; experiment E6), awaiting review. See `reports/M1.md` … `reports/M5.md`.

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
```

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
                 p_audit=0.5, s4_weighted=False, T=100, T_eval=20), seed=1).run()
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
               responses), baselines (A0–A4), metrics, model, experiments (CLI), plotting
docs/ODD.md    ODD protocol
experiments/   YAML configurations per experiment
tests/         analytic (§2.3) and mechanical tests
reports/       checkpoint reports M1.md …
```
