"""Greedy t-Spanner Construction and Permutation Engine.

Implements:
1. bounded_bfs_has_path: Fast depth-limited Breadth-First Search (depth <= t).
2. build_greedy_spanner: Core greedy t-spanner algorithm on unweighted graphs.
3. verify_spanner_correctness: Global assertion that d_H(u, v) <= t for all (u, v) in E_G.
4. run_spanner_permutations: Wrapper running randomized edge-order permutations.
"""

import random
from collections import deque
from typing import List, Tuple, Optional, Dict, Any
import networkx as nx


def bounded_bfs_distance(
    graph: nx.Graph,
    source: int,
    target: int,
    max_depth: int
) -> Optional[int]:
    """Compute exact shortest-path distance between source and target if <= max_depth.

    Args:
        graph: The current spanner graph H.
        source: Starting vertex u.
        target: Destination vertex v.
        max_depth: Maximum allowable path length (t).

    Returns:
        Shortest-path distance in H if d_H(source, target) <= max_depth, else None.
    """
    if source == target:
        return 0
    if max_depth <= 0:
        return None

    # Direct edge lookup (O(1) in NetworkX adjacency dictionary)
    if graph.has_edge(source, target):
        return 1

    # If max_depth is 1 and no direct edge exists, path length must be > 1
    if max_depth == 1:
        return None

    # Degree / neighbor fast check: if either node has 0 degree, no path exists
    if source not in graph or target not in graph:
        return None
    if graph.degree[source] == 0 or graph.degree[target] == 0:
        return None

    visited = {source}
    queue = deque([(source, 0)])
    adj = graph._adj

    while queue:
        curr, depth = queue.popleft()
        next_depth = depth + 1
        for nbr in adj[curr]:
            if nbr == target:
                return next_depth
            if next_depth < max_depth and nbr not in visited:
                visited.add(nbr)
                queue.append((nbr, next_depth))

    return None


def bounded_bfs_has_path(
    graph: nx.Graph,
    source: int,
    target: int,
    max_depth: int
) -> bool:
    """Determine whether there exists a path between source and target of length <= max_depth.

    Uses an optimized Breadth-First Search with early termination.
    Halts strictly at max_depth to prevent computational bottlenecking.

    Args:
        graph: The current spanner graph H.
        source: Starting vertex u.
        target: Destination vertex v.
        max_depth: Maximum allowable path length (t).

    Returns:
        True if d_H(source, target) <= max_depth, False otherwise.
    """
    return bounded_bfs_distance(graph, source, target, max_depth) is not None


def compute_exact_edge_max_stretch(
    graph: nx.Graph,
    spanner: nx.Graph,
    t: int,
    assume_valid: bool = False
) -> int:
    """Compute the exact global worst-case stretch across all original edges.

    For unweighted graphs, max_{u != v} d_H(u,v)/d_G(u,v) equals max_{(u,v) in E_G} d_H(u,v).

    Args:
        graph: Original input graph G.
        spanner: Constructed spanner subgraph H.
        t: Stretch factor.
        assume_valid: If True, returns t immediately once any pruned edge attains distance t.

    Returns:
        Exact maximum spanner distance across all edges in E_G.

    Raises:
        ValueError: If any edge in E_G violates d_H(u, v) <= t.
    """
    max_d = 1 if spanner.number_of_edges() > 0 else 0
    for u, v in graph.edges():
        if spanner.has_edge(u, v):
            continue
        d = bounded_bfs_distance(spanner, u, v, max_depth=t)
        if d is None:
            raise ValueError(f"Spanner invariant violated at edge ({u}, {v}) for t={t}.")
        if d > max_d:
            max_d = d
            if assume_valid and max_d == t:
                return t
    return max_d


def build_greedy_spanner(
    graph: nx.Graph,
    t: int,
    edge_order: Optional[List[Tuple[int, int]]] = None
) -> nx.Graph:
    """Construct an unweighted greedy t-spanner subgraph H for graph G.

    Execution Flow:
    1. Initialize an empty skeleton graph H = (V, empty_set).
    2. Treat all edges as unweighted (hop-count distance, all weights tied at 1).
    3. Loop through edges in the specified order. If bounded_bfs_has_path fails
       to find a path within depth t, add the edge to H. Otherwise, discard it.

    Args:
        graph: Original input graph G.
        t: Stretch factor (e.g. 3, 5, 7).
        edge_order: Pre-shuffled list of edges. If None, uses list(graph.edges()).

    Returns:
        The resulting t-spanner subgraph H.
    """
    if edge_order is None:
        edge_order = list(graph.edges())

    # Initialize skeleton with all original vertices
    H = nx.Graph()
    H.add_nodes_from(graph.nodes())

    # Greedy edge selection
    for u, v in edge_order:
        # Check if u and v already have a path of length <= t in H
        if not bounded_bfs_has_path(H, u, v, max_depth=t):
            H.add_edge(u, v)

    return H


def verify_spanner_correctness(
    graph: nx.Graph,
    spanner: nx.Graph,
    t: int
) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """Verify that spanner H is a valid t-spanner of G.

    Checks that d_H(u, v) <= t for EVERY original edge e(u, v) in E_G.

    Args:
        graph: Original input graph G.
        spanner: Constructed spanner subgraph H.
        t: Stretch factor.

    Returns:
        (True, None) if spanner condition holds globally.
        (False, (u, v)) identifying the first violating edge if it fails.
    """
    for u, v in graph.edges():
        if not bounded_bfs_has_path(spanner, u, v, max_depth=t):
            return False, (u, v)
    return True, None


def generate_edge_permutation(
    graph: nx.Graph,
    seed: Optional[int] = None
) -> List[Tuple[int, int]]:
    """Generate a randomized permutation of the graph's edge list.

    Args:
        graph: Original graph G.
        seed: Random seed for deterministic reproducibility.

    Returns:
        A shuffled copy of the edge list.
    """
    rng = random.Random(seed)
    edges = list(graph.edges())
    rng.shuffle(edges)
    return edges
