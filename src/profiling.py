"""Structural Profiling and Static Node-Pair Sampling.

Functions:
- compute_baseline_metrics: Measures Clustering Coefficient, Average Shortest-Path Length,
  Maximum Degree, Average Degree, etc.
- sample_static_pairs: Samples 1,000 distinct, unordered node pairs without replacement.
- save_pairs / load_pairs: JSON serialization for static pair sets.
"""

import json
import random
from typing import Dict, Any, List, Tuple
import networkx as nx


def compute_baseline_metrics(
    graph: nx.Graph,
    graph_id: str,
    topology: str,
    instance_id: int
) -> Dict[str, Any]:
    """Calculate and record baseline topological metrics for a generated graph.

    Metrics recorded:
    - Number of Nodes (|V|)
    - Number of Edges (|E|)
    - Average Degree (d_bar)
    - Maximum Degree (Delta)
    - Average Clustering Coefficient (C)
    - Average Shortest Path Length (L)
    - Graph Diameter
    - Connectivity confirmation

    Args:
        graph: Connected nx.Graph instance.
        graph_id: Unique string identifier (e.g. 'BA_01').
        topology: Topology family ('BA', 'WS', 'ER', 'GRID').
        instance_id: Integer index (0..29).

    Returns:
        Dictionary of baseline metrics.
    """
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    avg_degree = (2.0 * m) / n if n > 0 else 0.0

    degrees = [d for _, d in graph.degree()]
    max_degree = max(degrees) if degrees else 0

    is_conn = nx.is_connected(graph)
    if not is_conn:
        raise ValueError(f"Graph {graph_id} is disconnected. All instances must be 1-connected.")

    # Clustering Coefficient
    clustering = nx.average_clustering(graph)

    # Average Shortest Path Length (O(V * (V + E)) via BFS on unweighted graph)
    avg_spl = nx.average_shortest_path_length(graph)

    # Diameter
    diameter = nx.diameter(graph)

    return {
        "graph_id": graph_id,
        "topology": topology,
        "instance_id": instance_id,
        "nodes": n,
        "edges": m,
        "avg_degree": round(avg_degree, 4),
        "max_degree": max_degree,
        "clustering_coefficient": round(clustering, 6),
        "avg_shortest_path_length": round(avg_spl, 4),
        "diameter": diameter,
        "is_connected": is_conn
    }


def sample_static_pairs(
    graph: nx.Graph,
    num_pairs: int = 1000,
    seed: int = None
) -> List[Tuple[int, int]]:
    """Uniformly sample a fixed set of distinct, unordered node pairs without replacement.

    Each pair (u, v) satisfies u < v.
    This exact set of pairs is locked and reused across all t-values and edge permutations
    for this graph instance.

    Args:
        graph: nx.Graph instance with N nodes.
        num_pairs: Number of unique pairs to sample (default: 1000).
        seed: Random seed for reproducibility.

    Returns:
        Sorted list of tuples [(u, v), ...] with u < v.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    total_possible_pairs = n * (n - 1) // 2

    if num_pairs > total_possible_pairs:
        raise ValueError(
            f"Requested {num_pairs} pairs, but graph only has {total_possible_pairs} possible unordered pairs."
        )

    rng = random.Random(seed)
    selected_pairs = set()

    # Rejection sampling is extremely fast when num_pairs (1,000) << total pairs (499,500)
    while len(selected_pairs) < num_pairs:
        u, v = rng.sample(nodes, 2)
        pair = (min(u, v), max(u, v))
        selected_pairs.add(pair)

    # Return deterministically sorted list
    return sorted(list(selected_pairs))


def save_pairs(pairs: List[Tuple[int, int]], filepath: str) -> None:
    """Save sampled node pairs to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pairs, f)


def load_pairs(filepath: str) -> List[Tuple[int, int]]:
    """Load sampled node pairs from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_pairs = json.load(f)
    return [tuple(p) for p in raw_pairs]
