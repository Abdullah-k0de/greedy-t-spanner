"""Graph Generators with Strict Density and Connectivity Controls.

Topologies generated for N = 1000, d_bar ≈ 3.8 - 4.0:
1. Barabási-Albert (BA): m=2
2. Connected Watts-Strogatz (WS): k=4, p_rewire=0.1
3. Connectivity-Repaired Erdős-Rényi (ER): G(1000, p=4/999) + chain repair (c-1 edges)
4. Perturbed 2D Grid: 25x40 base, exactly 2% random edge removal (bridge-preserving)
"""

import random
import networkx as nx
from typing import Optional


def generate_barabasi_albert(
    n: int = 1000,
    m: int = 2,
    seed: Optional[int] = None
) -> nx.Graph:
    """Generate a Barabási-Albert scale-free graph.

    Args:
        n: Number of nodes (default: 1000).
        m: Number of edges to attach from a new node to existing nodes (default: 2).
        seed: Random seed for reproducibility.

    Returns:
        A connected nx.Graph with |V| = n, |E| = (n - m) * m (approx d_bar = 3.992).
    """
    G = nx.barabasi_albert_graph(n=n, m=m, seed=seed)
    # Ensure node labels are integer 0..n-1
    return nx.convert_node_labels_to_integers(G)


def generate_watts_strogatz(
    n: int = 1000,
    k: int = 4,
    p_rewire: float = 0.1,
    seed: Optional[int] = None
) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph guaranteed to be connected.

    Args:
        n: Number of nodes (default: 1000).
        k: Each node is joined with its k nearest neighbors in a ring topology (default: 4).
        p_rewire: Probability of rewiring each edge (default: 0.1).
        seed: Random seed for reproducibility.

    Returns:
        A connected nx.Graph with |V| = n, |E| = n * k / 2 = 2000 (d_bar = 4.0).
    """
    G = nx.connected_watts_strogatz_graph(
        n=n,
        k=k,
        p=p_rewire,
        tries=1000,
        seed=seed
    )
    return nx.convert_node_labels_to_integers(G)


def generate_erdos_renyi_repaired(
    n: int = 1000,
    p: Optional[float] = None,
    seed: Optional[int] = None
) -> nx.Graph:
    """Generate an Erdős-Rényi G(n, p) graph with strict chain connectivity repair.

    Control Specification:
        1. Generate G(1000, p) where p ≈ 4 / (n - 1) = 4 / 999.
        2. Identify all c disconnected components.
        3. Randomly order them into a chain (C_1, C_2, ..., C_c).
        4. Insert exactly one random inter-component edge between C_i and C_{i+1}.
           This guarantees a connected graph using exactly c - 1 repair edges,
           maintaining N = 1000 without deleting any nodes.

    Args:
        n: Number of nodes (default: 1000).
        p: Edge creation probability. Defaults to 4.0 / (n - 1).
        seed: Random seed for reproducibility.

    Returns:
        A connected nx.Graph with |V| = n.
    """
    if p is None:
        p = 4.0 / (n - 1)

    rng = random.Random(seed)
    # Generate base ER graph
    G = nx.erdos_renyi_graph(n=n, p=p, seed=seed)
    G = nx.convert_node_labels_to_integers(G)

    # Identify connected components
    components = [list(c) for c in nx.connected_components(G)]
    c = len(components)

    if c > 1:
        # Randomly order components into a chain
        rng.shuffle(components)
        for i in range(c - 1):
            comp_u = components[i]
            comp_v = components[i + 1]
            u = rng.choice(comp_u)
            v = rng.choice(comp_v)
            G.add_edge(u, v)

    assert nx.is_connected(G), f"Repaired ER graph must be connected, but has {nx.number_connected_components(G)} components."
    return G


def generate_perturbed_grid(
    rows: int = 25,
    cols: int = 40,
    removal_ratio: float = 0.02,
    seed: Optional[int] = None
) -> nx.Graph:
    """Generate a 2D Grid graph with exactly 2% random bridge-preserving edge removal.

    Control Specification:
        - Base grid: rows=25, cols=40 (N = 1000, |E_base| = 1935).
        - Remove exactly 2% of edges (round(1935 * 0.02) = 39 edges).
        - Explicitly reject any edge removal that disconnects the graph.

    Args:
        rows: Grid row dimension (default: 25).
        cols: Grid column dimension (default: 40).
        removal_ratio: Fraction of edges to remove (default: 0.02).
        seed: Random seed for reproducibility.

    Returns:
        A connected nx.Graph with |V| = rows * cols and |E| = |E_base| - removed_count.
    """
    rng = random.Random(seed)
    base_grid = nx.grid_2d_graph(rows, cols)
    G = nx.convert_node_labels_to_integers(base_grid)

    total_edges = G.number_of_edges()
    target_removals = round(total_edges * removal_ratio)

    # Candidate edges shuffled
    edge_candidates = list(G.edges())
    rng.shuffle(edge_candidates)

    removed_count = 0
    for u, v in edge_candidates:
        if removed_count >= target_removals:
            break

        # Temporarily remove the edge
        G.remove_edge(u, v)

        # In an unweighted graph that was previously connected, removing edge (u, v)
        # preserves global connectivity if and only if an alternate path still exists between u and v.
        if nx.has_path(G, u, v):
            removed_count += 1
        else:
            # Reinsert edge if it was a bridge
            G.add_edge(u, v)

    if removed_count < target_removals:
        raise RuntimeError(
            f"Could only remove {removed_count}/{target_removals} edges without disconnecting the grid."
        )

    assert nx.is_connected(G), "Perturbed grid must remain connected."
    return G
