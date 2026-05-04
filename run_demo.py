"""Small entry script to run the demo simulation from project root.

This script makes the `src` package importable and runs the simulation.
"""
import os
import sys

T_SIM = 150

# Add src path to sys.path to allow imports when run from project root
HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from src.simulation import Simulation
from src.utils import write_model_equations_summary


def main():
    results_dir = os.path.join(HERE, "results")
    sim = Simulation(n_nodes=120, topology="barabasi", seed=42, results_dir=results_dir)
    sim.run(steps=T_SIM, snapshot_interval=2)
    write_model_equations_summary(os.path.join(results_dir, "model_equations.txt"))


if __name__ == "__main__":
    main()
