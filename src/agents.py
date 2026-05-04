"""agents.py

Defines the agent abstraction used in the digital twin.

Each node is represented by a NodeAgent with typed parameters that capture
health, stress, load, capacity, degradation and failure state.
"""
from typing import Dict, Any
import numpy as np


class NodeAgent:
    """Represents a node in the industrial network.

    Attributes
    - id: unique integer identifier
    - node_type: string e.g. 'solar', 'wind', 'electrolyzer', 'storage', 'ammonia', 'pipeline'
    - capacity: maximum load the node can normally handle
    - load: current load (positive = consumption, negative = net generation)
    - stress: normalized stress metric (0..1)
    - health: remaining health (0..1); 0 means fully failed
    - failed: boolean failure state
    - degradation: long-term degradation multiplier that slowly reduces capacity via d_i(t+1)=min(d_i(t)+r_degrad*S_i(t), 0.99)
    """

    def __init__(self, id: int, node_type: str, capacity: float, initial_load: float = 0.0):
        self.id = id
        self.node_type = node_type
        self.capacity = float(capacity)
        self.load = float(initial_load)
        self.stress = 0.0
        self.health = 1.0
        self.failed = False
        self.degradation = 0.0

    def update_stress(self):
        """Update stress as a function of load vs capacity and degradation.

        Stress is normalized to [0, 1]. Over-capacity increases stress.
        """
        effective_cap = max(1e-6, self.capacity * (1 - self.degradation))
        # stress scales with load fraction above zero; generation nodes may have negative load
        load_ratio = abs(self.load) / effective_cap
        # soft cap
        self.stress = float(np.tanh(load_ratio))
        return self.stress

    def apply_degradation(self, delta: float):
        """Increase degradation according to d_i(t+1)=min(d_i(t)+delta, 0.99).

        In the simulation, delta = r_degrad * S_i(t).
        """
        self.degradation = min(0.99, max(0.0, self.degradation + float(delta)))

    def fail(self):
        """Set node to failed state. Reduce health and mark failed."""
        self.failed = True
        self.health = 0.0
        # when failed, capacity effectively zero
        self.load = 0.0

    def repair(self, health_fraction: float = 1.0):
        """Repair node (bring back to operation)."""
        self.failed = False
        self.health = float(max(0.0, min(1.0, health_fraction)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "capacity": self.capacity,
            "load": self.load,
            "stress": self.stress,
            "health": self.health,
            "failed": self.failed,
            "degradation": self.degradation,
        }


def node_type_capacity(node_type: str) -> float:
    """Return a representative capacity scale for each node type.

    Numbers are chosen to create heterogeneity but remain interpretable.
    """
    scales = {
        "solar": 10.0,
        "wind": 12.0,
        "electrolyzer": 30.0,
        "storage": 50.0,
        "ammonia": 80.0,
        "pipeline": 40.0,
    }
    return float(scales.get(node_type, 20.0))
