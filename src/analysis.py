"""analysis.py

Functions to analyze avalanche statistics and create publication-quality plots.
"""
from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np
import os


def analyze_avalanches(avalanches: List[Dict], out_dir: str):
    """Produce a log-log plot of avalanche sizes and save results."""
    os.makedirs(out_dir, exist_ok=True)
    if not avalanches:
        return
    sizes = np.array([a["size"] for a in avalanches])
    durations = np.array([a["duration"] for a in avalanches])

    # plot size distribution
    plt.figure(figsize=(6, 4))
    counts, bins = np.histogram(sizes, bins=np.logspace(np.log10(1), np.log10(max(1, sizes.max())), 15))
    bincenters = (bins[:-1] + bins[1:]) / 2
    plt.loglog(bincenters[counts > 0], counts[counts > 0], marker="o", linestyle="None")
    plt.xlabel("Avalanche size")
    plt.ylabel("Count")
    plt.title("Avalanche size distribution (log-log)")
    plt.grid(True, which="both", ls="--", alpha=0.3)
    plt.savefig(os.path.join(out_dir, "avalanche_size_distribution.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # size vs duration scatter
    plt.figure(figsize=(6, 4))
    plt.scatter(durations, sizes, alpha=0.6, s=10)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Duration (steps)")
    plt.ylabel("Size (nodes)")
    plt.title("Avalanche size vs duration")
    plt.grid(True, which="both", ls="--", alpha=0.25)
    plt.savefig(os.path.join(out_dir, "avalanche_size_vs_duration.png"), dpi=150, bbox_inches="tight")
    plt.close()


def plot_failure_fraction(series: List[float], out_path: str):
    plt.figure(figsize=(8, 3))
    plt.plot(series, color="#b30000")
    plt.xlabel("Timestep")
    plt.ylabel("Fraction failed")
    plt.title("Failure fraction over time")
    plt.grid(alpha=0.25)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
