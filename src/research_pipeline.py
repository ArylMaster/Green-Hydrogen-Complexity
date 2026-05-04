"""research_pipeline.py

Step-by-step post-processing workflow for:
1) critical regime extraction
2) topology comparison plots
3) SOC fit + finite-size checks
4) publication panel figure

Outputs are written to results/research/.
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

from run_demo import T_SIM

from .simulation import Simulation
from .analysis import plot_duration_vs_size
from .utils import write_model_equations_summary


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SWEEP_CSV = os.path.join(PROJECT_ROOT, "results", "sweeps", "sweep_summary.csv")
RESEARCH_DIR = os.path.join(PROJECT_ROOT, "results", "research")


def ensure_dirs() -> None:
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    os.makedirs(os.path.join(RESEARCH_DIR, "plots"), exist_ok=True)
    os.makedirs(os.path.join(RESEARCH_DIR, "data"), exist_ok=True)
    os.makedirs(os.path.join(RESEARCH_DIR, "runs"), exist_ok=True)


def read_sweep_csv(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                {
                    "cfg": r["cfg"],
                    "alpha": float(r["alpha"]),
                    "beta": float(r["beta"]),
                    "topology": r["topology"],
                    "n_avalanches": int(r["n_avalanches"]),
                    "mean_avalanche": float(r["mean_avalanche"]),
                    "max_avalanche": int(r["max_avalanche"]),
                }
            )
    return rows


def aggregate_by_setting(rows: List[Dict]) -> List[Dict]:
    grouped: Dict[Tuple[float, float, str], List[Dict]] = defaultdict(list)
    for r in rows:
        grouped[(r["alpha"], r["beta"], r["topology"])].append(r)

    out = []
    for (alpha, beta, topo), vals in grouped.items():
        mean_aval = float(np.mean([v["mean_avalanche"] for v in vals]))
        std_aval = float(np.std([v["mean_avalanche"] for v in vals]))
        mean_n = float(np.mean([v["n_avalanches"] for v in vals]))
        max_aval = float(np.mean([v["max_avalanche"] for v in vals]))
        out.append(
            {
                "alpha": alpha,
                "beta": beta,
                "topology": topo,
                "mean_avalanche": mean_aval,
                "std_avalanche": std_aval,
                "mean_n_avalanches": mean_n,
                "mean_max_avalanche": max_aval,
            }
        )
    return out


def pick_critical_setting(agg: List[Dict], n_nodes: int = 120) -> Dict:
    # score near transition: avoid fully stable (~0) and fully collapsed (~n_nodes)
    candidates = []
    for r in agg:
        norm = r["mean_avalanche"] / max(1.0, n_nodes)
        # center target at 0.4 with variance bonus
        score = -abs(norm - 0.4) + 0.5 * (r["std_avalanche"] / max(1.0, n_nodes)) + 0.2 * r["mean_n_avalanches"]
        candidates.append((score, r))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def collect_avalanche_events(alpha: float, beta: float, topology: str, n_nodes: int, seeds: List[int]) -> Tuple[List[int], List[int]]:
    sizes: List[int] = []
    durations: List[int] = []
    for seed in seeds:
        run_dir = os.path.join(RESEARCH_DIR, "runs", f"events_{topology}_n{n_nodes}_seed{seed}")
        sim = Simulation(n_nodes=n_nodes, topology=topology, seed=seed, results_dir=run_dir)
        sim.alpha = alpha
        sim.beta = beta
        sim.P0 = 0.0005
        sim.redistribution_factor = 0.8
        sim.recovery_prob = 0.01
        sim.run(steps=T_SIM, snapshot_interval=40)
        sizes.extend([a["size"] for a in sim.avalanches])
        durations.extend([a["duration"] for a in sim.avalanches])
    return sizes, durations


def run_topology_comparison(alpha: float, beta: float, out_dir: str) -> Dict[str, Dict[str, List[float]]]:
    stats = {"barabasi": {"mean_avalanche": [], "n_avalanches": [], "max_avalanche": [], "final_failed": []}, "watts": {"mean_avalanche": [], "n_avalanches": [], "max_avalanche": [], "final_failed": []}}

    for topo in ["barabasi", "watts"]:
        for seed in [101, 102, 103, 104, 105]:
            run_dir = os.path.join(out_dir, f"topology_cmp_{topo}_seed{seed}")
            sim = Simulation(n_nodes=120, topology=topo, seed=seed, results_dir=run_dir)
            sim.alpha = alpha
            sim.beta = beta
            sim.P0 = 0.0005
            sim.redistribution_factor = 0.8
            sim.recovery_prob = 0.01
            sim.run(steps=T_SIM, snapshot_interval=20)

            sizes = [a["size"] for a in sim.avalanches]
            stats[topo]["mean_avalanche"].append(float(np.mean(sizes)) if sizes else 0.0)
            stats[topo]["n_avalanches"].append(len(sizes))
            stats[topo]["max_avalanche"].append(float(np.max(sizes)) if sizes else 0.0)
            stats[topo]["final_failed"].append(sim.failure_time_series[-1] if sim.failure_time_series else 0.0)

    return stats


def plot_topology_comparison(stats: Dict[str, Dict[str, List[float]]], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    metrics = ["mean_avalanche", "n_avalanches", "max_avalanche", "final_failed"]

    plt.figure(figsize=(11, 7))
    for i, m in enumerate(metrics, start=1):
        plt.subplot(2, 2, i)
        vals_ba = stats["barabasi"][m]
        vals_ws = stats["watts"][m]
        plt.boxplot([vals_ba, vals_ws], tick_labels=["Barabasi-Albert", "Watts-Strogatz"], patch_artist=True)
        plt.title(m.replace("_", " ").title())
        plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "topology_comparison_panel.png"), dpi=180)
    plt.close()


def collect_avalanche_sizes(alpha: float, beta: float, topology: str, n_nodes: int, seeds: List[int]) -> List[int]:
    sizes = []
    for seed in seeds:
        run_dir = os.path.join(RESEARCH_DIR, "runs", f"sizes_{topology}_n{n_nodes}_seed{seed}")
        sim = Simulation(n_nodes=n_nodes, topology=topology, seed=seed, results_dir=run_dir)
        sim.alpha = alpha
        sim.beta = beta
        sim.P0 = 0.0005
        sim.redistribution_factor = 0.8
        sim.recovery_prob = 0.01
        sim.run(steps=T_SIM, snapshot_interval=40)
        sizes.extend([a["size"] for a in sim.avalanches])
    return sizes


def fit_power_law_like(sizes: List[int], out_path: str) -> Dict:
    if not sizes:
        return {"slope": None, "tau": None, "r_squared": None, "n_events": 0}

    vals = np.asarray(sizes)
    vals = vals[vals > 0]
    uniq, cnt = np.unique(vals, return_counts=True)
    x = np.log10(uniq)
    y = np.log10(cnt)

    if len(x) < 3:
        return {"slope": None, "tau": None, "r_squared": None, "n_events": int(len(vals))}

    fit = linregress(x, y)
    r_squared = float(fit.rvalue ** 2)
    slope = float(fit.slope)
    tau = float(-slope)

    plt.figure(figsize=(6, 4))
    plt.scatter(uniq, cnt, s=16, label="Data")
    fit_y = 10 ** (fit.intercept + fit.slope * np.log10(uniq))
    plt.plot(uniq, fit_y, color="red", linewidth=1.5, label=f"Fit slope={slope:.2f}, tau={tau:.2f}, R2={r_squared:.2f}")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Avalanche size")
    plt.ylabel("Frequency")
    plt.title("Avalanche size distribution (log-log)")
    plt.grid(alpha=0.25, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

    return {"slope": slope, "tau": tau, "r_squared": r_squared, "n_events": int(len(vals))}


def finite_size_check(alpha: float, beta: float, topology: str, out_dir: str) -> Dict:
    sizes_by_n = {}
    means = []
    ns = [80, 120, 180]
    for n in ns:
        sizes = collect_avalanche_sizes(alpha, beta, topology, n, seeds=[201, 202, 203])
        sizes_by_n[n] = sizes
        means.append(float(np.mean(sizes)) if sizes else 0.0)

    plt.figure(figsize=(6, 4))
    plt.plot(ns, means, marker="o")
    plt.xlabel("Network size N")
    plt.ylabel("Mean avalanche size")
    plt.title(f"Finite-size check ({topology})")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"finite_size_{topology}.png"), dpi=180)
    plt.close()

    return {"sizes_by_n": sizes_by_n, "means": means, "ns": ns}


def build_publication_panel(alpha: float, beta: float, out_dir: str) -> None:
    # Run one representative simulation for snapshots and failure trajectory.
    run_dir = os.path.join(out_dir, "panel_rep_run")
    sim = Simulation(n_nodes=120, topology="barabasi", seed=999, results_dir=run_dir)
    sim.alpha = alpha
    sim.beta = beta
    sim.P0 = 0.0005
    sim.redistribution_factor = 0.8
    sim.recovery_prob = 0.01
    sim.run(steps=T_SIM, snapshot_interval=10)

    # A single 2x2 panel assembled from existing saved assets + simple plots.
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # A: failure fraction trajectory
    axes[0, 0].plot(sim.failure_time_series, color="#7f0000")
    axes[0, 0].set_title("A. Failure Fraction vs Time")
    axes[0, 0].set_xlabel("Timestep")
    axes[0, 0].set_ylabel("Failed fraction")
    axes[0, 0].grid(alpha=0.25)

    # B: avalanche size histogram (log bins)
    sizes = np.array([a["size"] for a in sim.avalanches])
    if len(sizes) > 0:
        bins = np.logspace(np.log10(1), np.log10(max(2, int(sizes.max()))), 12)
        axes[0, 1].hist(sizes, bins=bins, color="#4e79a7", alpha=0.8)
        axes[0, 1].set_xscale("log")
        axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("B. Avalanche Distribution")
    axes[0, 1].set_xlabel("Size")
    axes[0, 1].set_ylabel("Count")

    # C: running average avalanche size
    if len(sizes) > 0:
        rolling = np.cumsum(sizes) / np.arange(1, len(sizes) + 1)
        axes[1, 0].plot(rolling, color="#2a9d8f")
    axes[1, 0].set_title("C. Emergent Avalanche Scale")
    axes[1, 0].set_xlabel("Avalanche index")
    axes[1, 0].set_ylabel("Running mean size")
    axes[1, 0].grid(alpha=0.25)

    # D: node failure final snapshot (bar)
    final_failed = sim.failure_time_series[-1] if sim.failure_time_series else 0.0
    axes[1, 1].bar(["Final Failed", "Final Healthy"], [final_failed, max(0.0, 1.0 - final_failed)], color=["#b30000", "#3a7d44"])
    axes[1, 1].set_ylim(0, 1)
    axes[1, 1].set_title("D. Final State Composition")

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "publication_panel.png"), dpi=200)
    plt.close()


def write_summary_json(path: str, payload: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    ensure_dirs()
    rows = read_sweep_csv(SWEEP_CSV)
    agg = aggregate_by_setting(rows)
    critical = pick_critical_setting(agg)
    write_model_equations_summary(os.path.join(PROJECT_ROOT, "results", "model_equations.txt"))
    with open(os.path.join(RESEARCH_DIR, "data", "critical_params.json"), "w", encoding="utf-8") as f:
        json.dump(critical, f, indent=2)

    # Step 2: topology comparison
    topology_stats = run_topology_comparison(critical["alpha"], critical["beta"], os.path.join(RESEARCH_DIR, "runs"))
    plot_topology_comparison(topology_stats, os.path.join(RESEARCH_DIR, "plots"))

    # Step 3: SOC + finite-size
    combined_sizes = []
    combined_durations = []
    for topo in ["barabasi", "watts"]:
        sizes, durations = collect_avalanche_events(critical["alpha"], critical["beta"], topo, 120, seeds=[301, 302, 303])
        combined_sizes.extend(sizes)
        combined_durations.extend(durations)
    fit = fit_power_law_like(combined_sizes, os.path.join(RESEARCH_DIR, "plots", "soc_fit_loglog.png"))
    plot_duration_vs_size(combined_sizes, combined_durations, os.path.join(RESEARCH_DIR, "plots", "duration_vs_size.png"))
    with open(os.path.join(RESEARCH_DIR, "data", "soc_fit.json"), "w", encoding="utf-8") as f:
        json.dump(fit, f, indent=2)
    finite_ba = finite_size_check(critical["alpha"], critical["beta"], "barabasi", os.path.join(RESEARCH_DIR, "plots"))
    finite_ws = finite_size_check(critical["alpha"], critical["beta"], "watts", os.path.join(RESEARCH_DIR, "plots"))

    # Step 4: publication panel
    build_publication_panel(critical["alpha"], critical["beta"], os.path.join(RESEARCH_DIR, "plots"))

    summary = {
        "critical_setting": critical,
        "soc_fit": fit,
        "topology_stats": topology_stats,
        "finite_size_barabasi": {"ns": finite_ba["ns"], "means": finite_ba["means"]},
        "finite_size_watts": {"ns": finite_ws["ns"], "means": finite_ws["means"]},
    }
    write_summary_json(os.path.join(RESEARCH_DIR, "data", "research_summary.json"), summary)
    print("Research pipeline complete.")
    print(f"Critical setting: alpha={critical['alpha']}, beta={critical['beta']}, topology={critical['topology']}")
    if fit["slope"] is not None:
        print(f"SOC fit slope={fit['slope']:.3f}, tau={fit['tau']:.3f}, R2={fit['r_squared']:.3f}, n={fit['n_events']}")
    print(f"Outputs at: {RESEARCH_DIR}")


if __name__ == "__main__":
    main()
