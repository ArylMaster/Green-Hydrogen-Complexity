# Agent-Based Digital Twin of Cascading Failures in a Green Hydrogen Industrial Network

This repository contains a research-grade, modular, reproducible Python project that implements an agent-based digital twin for cascading failures in a green hydrogen industrial ecosystem. It is designed for complexity scientists, network scientists, and systems engineers.

## Complexity Science Motivation

Green hydrogen infrastructure couples intermittently powered generation with process-constrained industrial conversion and transport. Such systems naturally exhibit nonlinear stress transfer, correlated failures, and network-dependent vulnerability. This project models these effects as a stochastic interacting-agent system and studies:

- cascading failures and load redistribution,
- avalanche size and duration statistics,
- topology effects (scale-free vs small-world),
- self-organized criticality (SOC)-like signatures,
- finite-size scaling tendencies.

## Project Structure

- `src/agents.py`: node-level digital twin agent model.
- `src/network_generation.py`: industrial network topology generation and node typing.
- `src/simulation.py`: stochastic simulation engine and cascading propagation dynamics.
- `src/analysis.py`: avalanche distribution and trajectory plotting.
- `src/visualization.py`: network, stress, and evolution visualizations.
- `src/param_sweep.py`: parameter sweep over `alpha`, `beta`, and topology.
- `src/research_pipeline.py`: critical-regime extraction, topology comparison, SOC fit, finite-size checks, and publication panel generation.
- `results/`: generated outputs for plots, animations, sweeps, and research post-processing.
- `report/manuscript.tex`: journal-style manuscript template.

## Mathematical Formulation

Failure probability of node $i$:

$$
P_{\text{fail},i}(t) = \min\left(1, P_0 + \alpha\,N^{(i)}_{\text{failed-neigh}}(t) + \beta\,S_i(t)\right)
$$

where:

- $P_0$: baseline failure probability,
- $N^{(i)}_{\text{failed-neigh}}$: number of failed neighbors,
- $S_i$: node stress from dynamic load/capacity ratio.

When a node fails, a fraction of its load is redistributed to operational neighbors proportionally to effective residual capacities, enabling secondary and higher-order cascades.

## Installation

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Simulation Workflow

1. Run baseline demo:

```bash
python run_demo.py
```

2. Run topology/parameter sweep:

```bash
python -m src.param_sweep
```

3. Run research-grade post-processing and figure generation:

```bash
python -m src.research_pipeline
```

4. Outputs:

- baseline: `results/plots/`, `results/animations/`, `results/data/`
- sweep: `results/sweeps/`
- research package: `results/research/plots/`, `results/research/data/`, `results/research/runs/`

## Generated Results (Current Run)

From `results/research/data/research_summary.json`:

- selected critical setting: `alpha=0.05`, `beta=0.5`, `topology=barabasi`
- SOC log-log fit: slope `-0.977`, $R^2=0.648$, sample count `n=654`
- finite-size trend (Barabasi mean avalanche): `N=80 -> 2.77`, `N=120 -> 3.14`, `N=180 -> 3.68`
- finite-size trend (Watts mean avalanche): `N=80 -> 2.61`, `N=120 -> 2.83`, `N=180 -> 3.41`

## Key Visual Outputs

- `results/research/plots/topology_comparison_panel.png`
- `results/research/plots/soc_fit_loglog.png`
- `results/research/plots/finite_size_barabasi.png`
- `results/research/plots/finite_size_watts.png`
- `results/research/plots/publication_panel.png`

## Reproducibility Notes

- Randomness is controlled via explicit seeds in sweep and research scripts.
- The simulation includes stochastic noise, degradation, and low-rate recovery to avoid trivial one-shot collapse and support richer avalanche ensembles.

## Future Work

- Introduce directed and weighted flow constraints for explicit commodity routing.
- Calibrate node/edge parameters from empirical industrial datasets.
- Add intervention optimization (adaptive load shedding, targeted hardening).
- Extend SOC diagnostics with maximum-likelihood power-law fitting and model comparison.

See `report/manuscript.tex` for manuscript-ready structuring of the study.

License
This project is provided for research and educational purposes. Please cite appropriately when using or extending this work.
