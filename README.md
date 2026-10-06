# SOFA-ABM

A toy agent-based model of **Self-Organised Funding Allocation** (Bollen et al. 2014, 2017):
every researcher receives an equal base amount each year and must pass a fixed fraction α of
everything they receive on to colleagues of their choice. The model asks what happens when donors
respond to incentives and information (cartels, herding, reciprocity, transparency, safeguards).

The full specification is in [`CLAUDE.md`](CLAUDE.md). Checkpoint reports are in [`reports/`](reports/).

**Status:** Milestone 2 complete (population, awareness network, perception, sincere donors,
baselines A0–A2, `SOFAModel`, ODD v1, experiment E1). See `reports/M1.md` and `reports/M2.md`.

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
```

A single model run:

```python
from sofa import Params
from sofa.model import SOFAModel

res = SOFAModel(Params(alpha=0.6), seed=1).run()
res.summary()  # means over the last T_eval years
```

Results are written as parquet (with config hash and git commit in the file metadata) to
`results/<experiment>/`, figures to `results/<experiment>/figures/` (PNG and PDF).

## Layout

```
src/sofa/      config, rng, flows, population, network, perception, strategies (sincere,
               cartel rows), safeguards (S2 cap only), baselines (A0–A2), metrics, model,
               experiments (CLI), plotting
docs/ODD.md    ODD protocol
experiments/   YAML configurations per experiment
tests/         analytic (§2.3) and mechanical tests
reports/       checkpoint reports M1.md …
```
