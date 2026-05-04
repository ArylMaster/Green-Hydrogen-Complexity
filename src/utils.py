"""Utility helpers for data saving and common math operations."""
import json
import os
from typing import Any


def ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_json(path: str, obj: Any) -> None:
    ensure_dirs(os.path.dirname(path) or "./")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def save_text(path: str, text: str) -> None:
    ensure_dirs(os.path.dirname(path) or "./")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_model_equations_summary(path: str) -> None:
    text = "\n".join(
        [
            "Model equations summary",
            "",
            "1. Failure probability: P_fail,i = min(1, P0 + alpha * N_failed-neigh^(i) + beta * S_i(t)) [eq:failure_prob]",
            "2. Stress: S_i(t) = tanh(|L_i(t)| / (C_i * (1 - d_i(t)))) [eq:stress]",
            "3. Load redistribution: Delta L_i = rho * L_j * C_i * (1 - d_i) / sum_k(C_k * (1 - d_k)) [eq:load_redist]",
            "4. Degradation: d_i(t+1) = min(d_i(t) + r_degrad * S_i(t), 0.99) [eq:degradation]",
        ]
    )
    save_text(path, text)
