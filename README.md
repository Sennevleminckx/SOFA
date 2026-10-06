# SOFA-ABM

A toy agent-based model of **Self-Organised Funding Allocation** (Bollen et al. 2014, 2017):
every researcher receives an equal base amount each year and must pass a fixed fraction α of
everything they receive on to colleagues of their choice. The model asks what happens when donors
respond to incentives and information (cartels, herding, reciprocity, transparency, safeguards).

The full specification is in [`CLAUDE.md`](CLAUDE.md). Checkpoint reports are in [`reports/`](reports/).

**Status:** Milestone 1 (flows, core metrics, configuration, RNG streams, analytic verification E0).

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
```

Results are written as parquet (with config hash and git commit in the file metadata) to
`results/<experiment>/`, figures to `results/<experiment>/figures/` (PNG and PDF).

## Layout

```
src/sofa/      config, rng, flows, safeguards (S2 cap only), strategies (cartel rows only),
               metrics, experiments (CLI), plotting
experiments/   YAML configurations per experiment
tests/         analytic (§2.3) and mechanical tests
reports/       checkpoint reports M1.md …
```
