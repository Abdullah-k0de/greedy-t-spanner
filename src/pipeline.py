"""Phase 3 Pipeline Engine: Metrics Evaluation and Pair Stretch Computation.

Implements:
1. compute_pair_distances: Fast BFS distance query for a list of node pairs.
2. evaluate_spanner_run: Measures edge retention, global correctness, average stretch,
   and 95th-percentile stretch against pre-cached original graph distances.
"""

from collections import deque, defaultdict
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import networkx as nx

from src.spanner import verify_spanner_correctness


def compute_pair_distances(
    graph: nx.Graph,
    pairs: List[Tuple[int, int]]
) -> Dict[Tuple[int, int], Optional[int]]:
    """Compute exact shortest path distances (hop counts) for a list of node pairs.

    Optimized by grouping queries by source vertex and running a single-source BFS
    per unique source, exploring only as deep as needed to reach all targets for that source.

    Args:
        graph: nx.Graph instance (unweighted).
        pairs: List of unordered pairs (u, v) with u < v.

    Returns:
        Dictionary mapping (u, v) -> shortest path distance, or None if disconnected.
    """
    # Group target nodes by source node
    targets_by_source = defaultdict(set)
    for u, v in pairs:
        targets_by_source[u].add(v)

    distances = {}
    adj = graph._adj

    for source, targets in targets_by_source.items():
        remaining_targets = set(targets)
        visited = {source: 0}
        queue = deque([source])

        # If source is isolated or not in graph
        if source not in graph:
            for t in targets:
                distances[(source, t)] = None
            continue

        while queue and remaining_targets:
            curr = queue.popleft()
            curr_dist = visited[curr]

            for nbr in adj[curr]:
                if nbr not in visited:
                    nbr_dist = curr_dist + 1
                    visited[nbr] = nbr_dist
                    queue.append(nbr)

                    if nbr in remaining_targets:
                        distances[(source, nbr)] = nbr_dist
                        remaining_targets.remove(nbr)
                        if not remaining_targets:
                            break

        # Any targets not reached are disconnected
        for t in remaining_targets:
            distances[(source, t)] = None

    return distances


def evaluate_spanner_run(
    original_graph: nx.Graph,
    spanner: nx.Graph,
    t: int,
    static_pairs: List[Tuple[int, int]],
    cached_orig_distances: Dict[Tuple[int, int], int],
    graph_id: str,
    topology: str,
    instance_id: int,
    permutation_id: int,
    build_time: float
) -> Dict[str, Any]:
    """Evaluate a single constructed spanner against experimental controls.

    Computes:
    - Global Correctness Assertion: d_H(u, v) <= t for all (u, v) in E_G.
    - Edge-Retention Ratio: |E_H| / |E_G|.
    - Empirical Stretch on the 1,000 static pairs: d_H(u, v) / d_G(u, v).
    - Empirical Average Stretch.
    - 95th-Percentile Stretch.
    - Maximum Stretch observed.
    - Count of disconnected pairs (if any).

    Returns:
        Dictionary with all permutation-level results ready for incremental CSV persistence.
    """
    orig_edges = original_graph.number_of_edges()
    spanner_edges = spanner.number_of_edges()
    retention_ratio = spanner_edges / orig_edges if orig_edges > 0 else 0.0

    # 1. Global Correctness Check
    is_valid, bad_edge = verify_spanner_correctness(original_graph, spanner, t)
    if not is_valid:
        raise ValueError(
            f"Spanner verification failed on {graph_id} (t={t}, perm={permutation_id}) at edge {bad_edge}!"
        )

    # 2. Compute spanner shortest path distances for the 1,000 static pairs
    spanner_distances = compute_pair_distances(spanner, static_pairs)

    # 3. Calculate empirical stretch values
    stretches = []
    failed_pairs_count = 0

    for pair in static_pairs:
        d_orig = cached_orig_distances[pair]
        d_span = spanner_distances[pair]

        if d_orig is None or d_orig == 0:
            continue

        if d_span is None:
            # Pair is disconnected in spanner
            failed_pairs_count += 1
        else:
            stretch = d_span / d_orig
            stretches.append(stretch)

    if stretches:
        avg_stretch = float(np.mean(stretches))
        p95_stretch = float(np.percentile(stretches, 95))
        max_stretch = float(np.max(stretches))
        median_stretch = float(np.median(stretches))
    else:
        avg_stretch = 0.0
        p95_stretch = 0.0
        max_stretch = 0.0
        median_stretch = 0.0

    return {
        "graph_id": graph_id,
        "topology": topology,
        "instance_id": instance_id,
        "t_limit": t,
        "permutation_id": permutation_id,
        "original_edges": orig_edges,
        "spanner_edges": spanner_edges,
        "edge_retention_ratio": round(retention_ratio, 6),
        "avg_stretch": round(avg_stretch, 6),
        "p95_stretch": round(p95_stretch, 6),
        "median_stretch": round(median_stretch, 6),
        "max_stretch": round(max_stretch, 6),
        "failed_pairs_count": failed_pairs_count,
        "is_valid_spanner": is_valid,
        "build_time_sec": round(build_time, 4)
    }
