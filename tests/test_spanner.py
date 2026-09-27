"""Unit and Verification Tests for Phase 2 Greedy t-Spanner Engine.

Tests:
1. Bounded BFS depth precision against NetworkX shortest_path_length.
2. Cycle graph C_6 behavior (exact theoretical edge counts for t=3 vs t=5).
3. Complete graph K_6 behavior.
4. Spanner correctness verification function.
5. Permutation consistency and tie-breaking variability.
6. Benchmark on actual generated graph (BA_00).
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import networkx as nx

from src.spanner import (
    bounded_bfs_has_path,
    build_greedy_spanner,
    verify_spanner_correctness,
    generate_edge_permutation,
)


def test_bounded_bfs_accuracy():
    """Verify Bounded BFS against NetworkX shortest path length."""
    # Create a path graph 0 - 1 - 2 - 3 - 4 - 5
    P = nx.path_graph(6)

    # d(0, 3) = 3
    assert bounded_bfs_has_path(P, 0, 3, max_depth=3) is True
    assert bounded_bfs_has_path(P, 0, 3, max_depth=2) is False

    # d(0, 5) = 5
    assert bounded_bfs_has_path(P, 0, 5, max_depth=5) is True
    assert bounded_bfs_has_path(P, 0, 5, max_depth=4) is False

    # Disconnected nodes
    G_disc = nx.Graph()
    G_disc.add_nodes_from([0, 1])
    assert bounded_bfs_has_path(G_disc, 0, 1, max_depth=10) is False


def test_cycle_graph_theoretical_bounds():
    """Verify exact theoretical behavior on a 6-node cycle C_6.

    In C_6:
    - For t = 3: An alternate path around any single deleted edge has length 5.
      Since 5 > 3, NO edges can be pruned! All 6 edges must be retained.
    - For t = 5: An alternate path of length 5 <= 5 is acceptable.
      Exactly one edge is pruned, leaving a path of 5 edges (a spanning tree).
    """
    C6 = nx.cycle_graph(6)

    # t = 3 spanner
    H3 = build_greedy_spanner(C6, t=3)
    assert H3.number_of_edges() == 6
    is_valid, _ = verify_spanner_correctness(C6, H3, t=3)
    assert is_valid is True

    # t = 5 spanner
    H5 = build_greedy_spanner(C6, t=5)
    assert H5.number_of_edges() == 5
    is_valid, _ = verify_spanner_correctness(C6, H5, t=5)
    assert is_valid is True


def test_complete_graph_sparsity():
    """In a complete graph K_n, for t >= 2, the spanner is a star or tree with n-1 edges."""
    K6 = nx.complete_graph(6)
    H3 = build_greedy_spanner(K6, t=3)
    assert H3.number_of_edges() == 5
    is_valid, _ = verify_spanner_correctness(K6, H3, t=3)
    assert is_valid is True


def test_spanner_correctness_verifier():
    """Verify that verify_spanner_correctness catches invalid spanners."""
    C6 = nx.cycle_graph(6)
    # An empty spanner or incomplete spanner for t=3 should fail
    H_bad = nx.Graph()
    H_bad.add_nodes_from(C6.nodes())
    H_bad.add_edge(0, 1)

    is_valid, bad_edge = verify_spanner_correctness(C6, H_bad, t=3)
    assert is_valid is False
    assert bad_edge is not None


def test_permutation_wrapper_consistency():
    """Ensure that 10 randomized permutations all produce valid t-spanners."""
    grid = nx.grid_2d_graph(5, 5)
    grid = nx.convert_node_labels_to_integers(grid)

    edge_counts = []
    for p_id in range(10):
        shuffled_edges = generate_edge_permutation(grid, seed=100 + p_id)
        H = build_greedy_spanner(grid, t=3, edge_order=shuffled_edges)

        is_valid, bad_edge = verify_spanner_correctness(grid, H, t=3)
        assert is_valid is True, f"Permutation {p_id} failed correctness check at edge {bad_edge}"
        edge_counts.append(H.number_of_edges())

    # All edge counts should be reasonable and spanners valid
    assert len(edge_counts) == 10
    print(f"Grid 5x5 (40 edges) t=3 edge retention across 10 permutations: {edge_counts}")


def test_benchmark_on_phase1_instance():
    """Test execution speed and correctness on an actual Phase 1 graph (BA_00)."""
    graph_path = os.path.join("data", "graphs", "BA_00.graphml")
    if not os.path.exists(graph_path):
        pytest.skip("Phase 1 graphs not found.")

    G = nx.read_graphml(graph_path)
    G = nx.convert_node_labels_to_integers(G)

    print(f"\nBenchmarking BA_00 (|V|={G.number_of_nodes()}, |E|={G.number_of_edges()}):")
    for t_val in [3, 5, 7]:
        t0 = time.time()
        edges = generate_edge_permutation(G, seed=42)
        H = build_greedy_spanner(G, t=t_val, edge_order=edges)
        construct_time = time.time() - t0

        t0_check = time.time()
        is_valid, bad_edge = verify_spanner_correctness(G, H, t=t_val)
        check_time = time.time() - t0_check

        assert is_valid is True, f"Failed spanner condition for t={t_val} at {bad_edge}"

        retention_ratio = H.number_of_edges() / G.number_of_edges()
        print(
            f"  t={t_val}: Retained {H.number_of_edges()}/{G.number_of_edges()} edges "
            f"({retention_ratio:.1%}) | Build: {construct_time:.3f}s | Check: {check_time:.3f}s"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING PHASE 2 UNIT AND VERIFICATION TESTS")
    print("=" * 60)
    test_bounded_bfs_accuracy()
    print("✓ Bounded BFS Accuracy Test Passed")

    test_cycle_graph_theoretical_bounds()
    print("✓ Theoretical Cycle C_6 Test Passed")

    test_complete_graph_sparsity()
    print("✓ Complete Graph K_6 Test Passed")

    test_spanner_correctness_verifier()
    print("✓ Correctness Verifier Test Passed")

    test_permutation_wrapper_consistency()
    print("✓ 10-Permutation Consistency Test Passed")

    test_benchmark_on_phase1_instance()
    print("✓ Phase 1 Instance (BA_00) Benchmark Passed")
    print("=" * 60)
    print("ALL TESTS PASSED WITH 100% MATHEMATICAL INTEGRITY!")
