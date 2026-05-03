"""visualization.py

Plotting utilities for network state, stress heatmaps and animation assembly.
"""
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import imageio
import os


def node_color_map(G: nx.Graph) -> List[str]:
    """Return a list of colors for nodes based on their state and type."""
    cmap = {
        "solar": "#ffcc33",
        "wind": "#66ccff",
        "electrolyzer": "#ff6666",
        "storage": "#66ff99",
        "ammonia": "#cc66ff",
        "pipeline": "#cccccc",
    }
    colors = []
    for n in G.nodes():
        agent = G.nodes[n].get("agent")
        base = cmap.get(G.nodes[n].get("node_type", "pipeline"), "#999999")
        if agent is None:
            colors.append(base)
            continue
        if agent.failed:
            colors.append("#2b2b2b")
        else:
            # vary brightness by stress
            stress = min(1.0, getattr(agent, "stress", 0.0))
            # blend color toward red as stress grows
            colors.append(base)
    return colors


def plot_network_state(G: nx.Graph, out_path: str = None, figsize=(10, 8)) -> None:
    """Plot the network with node coloring by type/state and node sizes by capacity.

    Saves to out_path if provided.
    """
    pos = nx.get_node_attributes(G, "pos")
    plt.figure(figsize=figsize)
    colors = node_color_map(G)
    sizes = [max(40, G.nodes[n].get("capacity", 20.0) * 4) for n in G.nodes()]
    nx.draw_networkx_edges(G, pos, alpha=0.25)
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, linewidths=0.5)

    # small legend by plotting dummy nodes
    types = set(nx.get_node_attributes(G, "node_type").values())
    # annotate nodes with small labels
    labels = {n: G.nodes[n].get("label", str(n)) for n in G.nodes()}
    # draw labels sparsely for readability
    for i, (n, label) in enumerate(labels.items()):
        if i % max(1, len(labels) // 15) == 0:
            x, y = pos[n]
            plt.text(x, y, label, fontsize=6)

    plt.axis("off")
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_stress_heatmap(G: nx.Graph, out_path: str = None, figsize=(8, 6)):
    """Plot node stress as a heatmap over the network layout.

    Uses node positions in `pos` attribute; colors by `agent.stress`.
    """
    pos = nx.get_node_attributes(G, "pos")
    stresses = [getattr(G.nodes[n].get("agent"), "stress", 0.0) for n in G.nodes()]
    plt.figure(figsize=figsize)
    nx.draw_networkx_edges(G, pos, alpha=0.25)
    nodes = nx.draw_networkx_nodes(G, pos, node_size=[max(30, G.nodes[n].get("capacity", 20.0) * 3) for n in G.nodes()], cmap="inferno", node_color=stresses)
    plt.colorbar(nodes, label="Stress (0-1)")
    plt.title("Node stress heatmap")
    plt.axis("off")
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_node_state_evolution(snapshots: List[Dict[int, Dict]], out_path: str = None, max_display: int = 50):
    """Plot evolution of node states (failed or not) over time as a raster/heatmap.

    `snapshots` is a list where each element maps node id -> node dict produced by `NodeAgent.to_dict()`.
    """
    if not snapshots:
        return
    times = len(snapshots)
    node_ids = sorted(list(snapshots[0].keys()))
    # limit number of nodes displayed for readability
    if len(node_ids) > max_display:
        node_ids = node_ids[:max_display]

    mat = np.zeros((len(node_ids), times), dtype=int)
    for t, snap in enumerate(snapshots):
        for i, nid in enumerate(node_ids):
            st = snap.get(nid, {}).get("failed", False)
            mat[i, t] = 1 if st else 0

    plt.figure(figsize=(10, max(3, len(node_ids) * 0.12)))
    plt.imshow(mat, aspect="auto", cmap="Greys", interpolation="nearest")
    plt.xlabel("Timestep")
    plt.ylabel("Node index (subset)")
    plt.title("Node failure raster over time (1 = failed)")
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def make_animation(frame_paths: List[str], gif_path: str, fps: int = 6):
    """Compose a GIF from a list of frame image paths."""
    if not frame_paths:
        return
    images = []
    for p in frame_paths:
        try:
            img = imageio.v2.imread(p)
            images.append(img)
        except Exception:
            continue
    if not images:
        return
    os.makedirs(os.path.dirname(gif_path), exist_ok=True)
    imageio.mimsave(gif_path, images, fps=fps)
