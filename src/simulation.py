"""simulation.py

Main Simulation engine for the agent-based digital twin. Run this module
to execute a representative experiment that saves plots and a GIF.
"""
import os
import random
import math
from typing import Dict, List, Tuple
import numpy as np
import networkx as nx
from .agents import NodeAgent, node_type_capacity
from .network_generation import generate_topology, assign_node_types, extract_agents_from_graph
from .visualization import plot_network_state, make_animation
from .analysis import analyze_avalanches, plot_failure_fraction
from .utils import ensure_dirs, save_json


class Simulation:
    """Simulation class encapsulating the digital twin.

    Key features:
    - nodes represented as NodeAgent objects
    - cascading failure rules with probability P_fail
    - load redistribution on failure
    """

    def __init__(self, n_nodes: int = 80, topology: str = "barabasi", seed: int = 1, results_dir: str = None):
        self.seed = int(seed)
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.G = generate_topology(n_nodes, topology=topology, seed=self.seed)
        assign_node_types(self.G, seed=self.seed)
        agents_info = extract_agents_from_graph(self.G)
        self.agents: Dict[int, NodeAgent] = {
            info["id"]: NodeAgent(info["id"], info["node_type"], info["capacity"], info["initial_load"]) for info in agents_info
        }

        # attach NodeAgent objects to graph
        for nid, agent in self.agents.items():
            self.G.nodes[nid]["agent"] = agent

        self.time = 0
        self.failure_time_series: List[float] = []
        self.failure_snapshots: List[Dict[int, Dict]] = []
        self.avalanches: List[Dict] = []
        self.results_dir = results_dir or os.path.join(os.getcwd(), "results")
        ensure_dirs(self.results_dir)
        ensure_dirs(os.path.join(self.results_dir, "plots"))
        ensure_dirs(os.path.join(self.results_dir, "animations"))
        ensure_dirs(os.path.join(self.results_dir, "data"))

        # model parameters (tunable)
        self.P0 = 0.001
        self.alpha = 0.12
        self.beta = 0.9
        self.noise_sigma = 0.05
        self.redistribution_factor = 0.9
        self.degradation_rate = 0.0005
        # maintenance/recovery keeps the system from collapsing into one-shot failure,
        # enabling richer avalanche statistics in long runs.
        self.recovery_prob = 0.002
        self.recovery_health = 0.6

    def step(self) -> Tuple[int, int]:
        """Execute one simulation timestep with cascading failure propagation.

        Returns (avalanche_size, avalanche_duration)
        """
        self.time += 1
        # exogenous maintenance: a fraction of failed nodes may recover.
        for nid, agent in self.agents.items():
            if agent.failed and np.random.random() < self.recovery_prob:
                agent.repair(self.recovery_health)
                # restart at a small load after repair.
                agent.load = abs(np.random.normal(loc=0.2 * agent.capacity, scale=0.05 * agent.capacity))
                agent.update_stress()

        # stochastic fluctuations: change generation nodes' load
        for nid, agent in self.agents.items():
            if agent.failed:
                continue
            if agent.node_type in ("solar", "wind"):
                # generation fluctuates: negative load means generation
                gen = -abs(np.random.normal(loc=0.5 * agent.capacity, scale=0.18 * agent.capacity))
                # add Gaussian noise
                gen += np.random.normal(scale=self.noise_sigma * agent.capacity)
                agent.load = gen
            else:
                # consumption/process nodes have variable demand
                demand = abs(np.random.normal(loc=0.5 * agent.capacity, scale=0.2 * agent.capacity))
                agent.load = demand

            # random small degradation
            agent.apply_degradation(np.random.normal(loc=0.0, scale=0.0002))
            agent.update_stress()

        # compute initial failures by probabilistic check
        newly_failed = set()
        for nid, agent in self.agents.items():
            if agent.failed:
                continue
            failed_neighbors = sum(1 for nbr in self.G.neighbors(nid) if self.agents[nbr].failed)
            p_fail = min(1.0, self.P0 + self.alpha * failed_neighbors + self.beta * agent.stress)
            if np.random.random() < p_fail:
                newly_failed.add(nid)

        # cascading: iteratively redistribute load and check for secondary failures
        avalanche_nodes = set(newly_failed)
        duration = 0
        while newly_failed:
            duration += 1
            next_failed = set()
            # redistribute load of each failed node
            for fid in list(newly_failed):
                if self.agents[fid].failed:
                    continue
                failed_agent = self.agents[fid]
                failed_agent.fail()
                # gather neighbors that are alive
                neighbors = [n for n in self.G.neighbors(fid) if not self.agents[n].failed]
                if not neighbors:
                    continue
                total_cap = sum(self.agents[n].capacity * (1 - self.agents[n].degradation) for n in neighbors)
                if total_cap <= 0:
                    continue
                # redistribute a fraction of failed load among neighbors
                transfer = (failed_agent.load if failed_agent.load > 0 else 0.0) * self.redistribution_factor
                for n in neighbors:
                    share = (self.agents[n].capacity * (1 - self.agents[n].degradation)) / total_cap
                    self.agents[n].load += transfer * share
                    self.agents[n].update_stress()

            # after redistribution, evaluate new failures
            for nid, agent in self.agents.items():
                if agent.failed:
                    continue
                failed_neighbors = sum(1 for nbr in self.G.neighbors(nid) if self.agents[nbr].failed)
                p_fail = min(1.0, self.P0 + self.alpha * failed_neighbors + self.beta * agent.stress)
                if np.random.random() < p_fail:
                    next_failed.add(nid)

            newly_failed = next_failed
            avalanche_nodes.update(newly_failed)

        avalanche_size = len(avalanche_nodes)
        # store snapshot and statistics
        failed_fraction = sum(1 for a in self.agents.values() if a.failed) / len(self.agents)
        self.failure_time_series.append(failed_fraction)
        snapshot = {nid: self.agents[nid].to_dict() for nid in self.agents}
        self.failure_snapshots.append(snapshot)
        if avalanche_size > 0:
            self.avalanches.append({"time": self.time, "size": avalanche_size, "duration": duration})

        return avalanche_size, duration

    def run(self, steps: int = 200, snapshot_interval: int = 1):
        """Run simulation for a number of steps and produce analysis/visuals."""
        frames = []
        for t in range(steps):
            size, dur = self.step()
            if t % snapshot_interval == 0:
                # create a plot and capture filename
                fname = os.path.join(self.results_dir, "plots", f"network_{t:04d}.png")
                plot_network_state(self.G, fname)
                frames.append(fname)

        # save time series and avalanches
        save_json(os.path.join(self.results_dir, "data", "failure_time_series.json"), self.failure_time_series)
        save_json(os.path.join(self.results_dir, "data", "avalanches.json"), self.avalanches)

        # generate analysis and plots
        analyze_avalanches(self.avalanches, os.path.join(self.results_dir, "plots"))
        plot_failure_fraction(self.failure_time_series, os.path.join(self.results_dir, "plots", "failure_fraction.png"))

        # assemble animation
        gif_path = os.path.join(self.results_dir, "animations", "cascading_failures.gif")
        make_animation(frames, gif_path, fps=6)
        print(f"Simulation complete. Results in {self.results_dir}")


if __name__ == "__main__":
    sim = Simulation(n_nodes=120, topology="barabasi", seed=42, results_dir=os.path.join(os.getcwd(), "green_results"))
    sim.run(steps=160, snapshot_interval=2)
