"""param_sweep.py

Run parameter sweeps over model parameters (alpha, beta, topology) and
collect metrics such as total avalanches, mean avalanche size, and maximum avalanche.

Saves summary CSV and representative plots into results/.
"""
import os
import itertools
import csv
from statistics import mean
from typing import List, Dict

from .simulation import Simulation
from .visualization import plot_stress_heatmap, plot_node_state_evolution, plot_network_state


def run_single(alpha: float, beta: float, topology: str, run_id: int, out_root: str) -> Dict:
    cfg_name = f"alpha{alpha:.3f}_beta{beta:.3f}_{topology}_run{run_id}"
    out_dir = os.path.join(out_root, cfg_name)
    os.makedirs(out_dir, exist_ok=True)
    sim = Simulation(n_nodes=120, topology=topology, seed=42 + run_id, results_dir=out_dir)
    sim.alpha = alpha
    sim.beta = beta
    sim.run(steps=120, snapshot_interval=4)

    # compute summary metrics
    avals = [a["size"] for a in sim.avalanches]
    metrics = {
        "cfg": cfg_name,
        "alpha": alpha,
        "beta": beta,
        "topology": topology,
        "n_avalanches": len(avals),
        "mean_avalanche": float(mean(avals)) if avals else 0.0,
        "max_avalanche": int(max(avals)) if avals else 0,
    }

    # additional visuals
    # stress heatmap at final snapshot
    final_snap = sim.failure_snapshots[-1] if sim.failure_snapshots else {}
    # attach latest agent states into graph
    for nid in sim.G.nodes():
        if nid in final_snap:
            sim.G.nodes[nid]["agent"].stress = final_snap[nid].get("stress", sim.G.nodes[nid]["agent"].stress)
    plot_stress_heatmap(sim.G, os.path.join(out_dir, "stress_final.png"))
    plot_network_state(sim.G, os.path.join(out_dir, "network_final.png"))
    plot_node_state_evolution(sim.failure_snapshots, os.path.join(out_dir, "node_raster.png"))

    return metrics


def sweep(out_root: str = "results/sweeps"):
    os.makedirs(out_root, exist_ok=True)
    alphas = [0.05, 0.1, 0.15]
    betas = [0.5, 0.9, 1.2]
    topologies = ["barabasi", "watts"]

    combos = list(itertools.product(alphas, betas, topologies))
    results: List[Dict] = []
    run_id = 0
    for alpha, beta, topo in combos:
        for r in range(2):
            run_id += 1
            print(f"Running sweep: alpha={alpha} beta={beta} topo={topo} run={r}")
            metrics = run_single(alpha, beta, topo, r, out_root)
            results.append(metrics)

    # write summary CSV
    csv_path = os.path.join(out_root, "sweep_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cfg", "alpha", "beta", "topology", "n_avalanches", "mean_avalanche", "max_avalanche"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"Sweep complete. Summary at {csv_path}")


if __name__ == "__main__":
    sweep(out_root=os.path.join(os.getcwd(), "results", "sweeps"))
