"""network_generation.py

Functions to create industrial network topologies (Barabasi-Albert and Watts-Strogatz)
and assign node types and capacities.
"""
from typing import Tuple, Dict, Any, List
import networkx as nx
import random
import numpy as np
from .agents import node_type_capacity


NODE_TYPE_POOL = [
    "solar",
    "wind",
    "electrolyzer",
    "storage",
    "ammonia",
    "pipeline",
]


def generate_topology(n_nodes: int = 80, topology: str = "barabasi", seed: int = 1) -> nx.Graph:
    """Generate a networkx graph according to requested topology.

    topology: 'barabasi' or 'watts'
    """
    rng = np.random.default_rng(seed)
    if topology == "barabasi":
        # BA network produces hub-and-spoke structures suitable for pipelines
        G = nx.barabasi_albert_graph(n_nodes, max(1, n_nodes // 30), seed=seed)
    elif topology == "watts":
        # small-world topology for distributed industrial landscapes
        k = max(2, (n_nodes // 20) * 2)
        G = nx.watts_strogatz_graph(n_nodes, k, 0.1, seed=seed)
    else:
        raise ValueError("Unknown topology: choose 'barabasi' or 'watts'")

    # add positional attributes to improve plotting layout
    pos = nx.spring_layout(G, seed=seed)
    nx.set_node_attributes(G, {i: pos[i] for i in G.nodes()}, "pos")
    return G


def assign_node_types(G: nx.Graph, distribution: Dict[str, float] = None, seed: int = 1) -> None:
    """Assign node types and capacity attributes to each node in-place.

    distribution: optional dict mapping node_type to fraction.
    """
    rng = random.Random(seed)
    n = G.number_of_nodes()
    if distribution is None:
        # default distribution tuned for industrial hydrogen network
        distribution = {
            "solar": 0.18,
            "wind": 0.12,
            "electrolyzer": 0.22,
            "storage": 0.12,
            "ammonia": 0.18,
            "pipeline": 0.18,
        }

    types = []
    for t, frac in distribution.items():
        types.extend([t] * int(round(frac * n)))
    # pad or trim
    while len(types) < n:
        types.append(rng.choice(NODE_TYPE_POOL))
    if len(types) > n:
        types = types[:n]

    rng.shuffle(types)
    for i, node in enumerate(G.nodes()):
        nt = types[i]
        cap = node_type_capacity(nt) * rng.uniform(0.7, 1.4)
        # attach attributes
        G.nodes[node]["node_type"] = nt
        G.nodes[node]["capacity"] = float(cap)
        # baseline load: generation nodes negative load if producing
        baseline = 0.0
        if nt in ("solar", "wind"):
            baseline = -abs(rng.normalvariate(0.4 * cap, 0.15 * cap))
        elif nt == "electrolyzer":
            baseline = abs(rng.normalvariate(0.6 * cap, 0.2 * cap))
        elif nt == "storage":
            baseline = 0.0
        elif nt == "ammonia":
            baseline = abs(rng.normalvariate(0.8 * cap, 0.25 * cap))
        elif nt == "pipeline":
            baseline = abs(rng.normalvariate(0.3 * cap, 0.15 * cap))
        G.nodes[node]["initial_load"] = float(baseline)
        # record a human-friendly label
        G.nodes[node]["label"] = f"{nt[:3].upper()}_{node}"


def extract_agents_from_graph(G: nx.Graph) -> List[Dict[str, Any]]:
    """Return a list of node dicts usable to construct NodeAgent objects."""
    agents = []
    for node in G.nodes():
        d = G.nodes[node]
        agents.append({
            "id": int(node),
            "node_type": d.get("node_type", "pipeline"),
            "capacity": float(d.get("capacity", 20.0)),
            "initial_load": float(d.get("initial_load", 0.0)),
        })
    return agents
