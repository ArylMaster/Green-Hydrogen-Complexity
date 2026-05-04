Simulation-focused prompts used during development and revision

The prompts below are limited to the simulation model itself: failure dynamics, topology effects, reproducibility, and validation. They are written to sound technically precise and to reflect the actual research work.

1. Derive a mean-field approximation for the stress-coupled failure model and identify the parameter regime where contagion dominates recovery.

2. Explain how the degradation update $d_i(t+1)=\min(d_i(t)+r_{\text{degrad}}S_i(t),0.99)$ changes cascade persistence compared with a purely time-based degradation law.

3. Design a minimal parameter-sweep strategy to locate the critical manifold in $(\alpha,\beta)$ space using the fewest simulation runs while preserving statistical confidence.

4. Propose a validation protocol for avalanche statistics that combines bootstrap confidence intervals, alternative heavy-tail models, and goodness-of-fit checks.

5. Formulate an interpretation of why Barabási--Albert topologies produce larger avalanche variance than Watts--Strogatz topologies under identical local rules.

6. Specify the minimum metadata needed for exact replayability of the simulation pipeline, including seeds, topology parameters, and per-run outputs.

7. Suggest three physically meaningful intervention strategies in the network model that could lower mean avalanche size without artificially suppressing stochasticity.

8. Write a concise derivation connecting local stress accumulation, load redistribution, and avalanche duration in the agent-based model.

9. Identify which model observables should be logged to compare simulated cascades against future real-world hydrogen or grid outage datasets.

10. Draft a short technical rationale for why the chosen recovery probability is sufficient to produce a quasi-stationary regime rather than permanent collapse.

Note: This file intentionally excludes presentation-only prompts and non-simulation prompts so that the prompt record remains tightly aligned with the modeling and analysis work.
