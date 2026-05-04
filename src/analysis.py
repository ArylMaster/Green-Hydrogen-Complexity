"""analysis.py

Functions to analyze avalanche statistics and create publication-quality plots.
"""
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.stats import linregress, pearsonr


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


def plot_duration_vs_size(sizes: List[int], durations: List[int], out_path: str):
    """Plot avalanche duration against size with a log-log regression line."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sizes_arr = np.asarray(sizes, dtype=float)
    durations_arr = np.asarray(durations, dtype=float)
    mask = (sizes_arr > 0) & (durations_arr > 0)
    sizes_arr = sizes_arr[mask]
    durations_arr = durations_arr[mask]
    if len(sizes_arr) < 2:
        return {"pearson_r": None, "slope": None, "n_events": int(len(sizes_arr))}

    log_sizes = np.log10(sizes_arr)
    log_durations = np.log10(durations_arr)
    r_value, _ = pearsonr(log_sizes, log_durations)
    fit = linregress(log_sizes, log_durations)
    x_line = np.linspace(log_sizes.min(), log_sizes.max(), 100)
    y_line = fit.intercept + fit.slope * x_line

    plt.figure(figsize=(6, 4))
    plt.scatter(sizes_arr, durations_arr, alpha=0.65, s=14, label="Events")
    plt.plot(10 ** x_line, 10 ** y_line, color="red", linewidth=1.5, label=f"Fit r={r_value:.3f}")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Avalanche size")
    plt.ylabel("Avalanche duration")
    plt.title("Avalanche duration vs. size")
    plt.grid(True, which="both", ls="--", alpha=0.25)
    plt.legend()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return {"pearson_r": float(r_value), "slope": float(fit.slope), "n_events": int(len(sizes_arr))}


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
