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
