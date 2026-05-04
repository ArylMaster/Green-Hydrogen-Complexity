# regenerate duration_vs_size.png by aggregating avalanches from saved runs
import json
import os
import sys
# ensure project root is on sys.path so `src` can be imported when running the script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.analysis import plot_duration_vs_size

ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "research", "runs")
# Collect runs for both topologies, n=120, seeds 301-303 (same as pipeline)
run_dirs = [
    "sizes_barabasi_n120_seed301",
    "sizes_barabasi_n120_seed302",
    "sizes_barabasi_n120_seed303",
    "sizes_watts_n120_seed301",
    "sizes_watts_n120_seed302",
    "sizes_watts_n120_seed303",
]

sizes = []
durations = []
for rd in run_dirs:
    p = os.path.join(ROOT, rd, "data", "avalanches.json")
    if not os.path.exists(p):
        print(f"Missing {p}")
        continue
    with open(p, "r", encoding="utf-8") as f:
        a = json.load(f)
    for ev in a:
        sizes.append(ev.get("size", 0))
        durations.append(ev.get("duration", 0))

out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "overleaf2", "duration_vs_size.png")
res = plot_duration_vs_size(sizes, durations, out_path)
print("wrote", out_path, "result:", res)
