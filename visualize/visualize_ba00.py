"""Visualize BA_00 Topology and Spanner Thinning Progression.

Generates:
1. figures/ba_00_topology.png:
   Standalone high-resolution visualization of BA_00 highlighting scale-free hubs.
2. figures/ba_00_spanner_thinning.png:
   4-panel comparative visualization showing Original Graph vs t=3, t=5, t=7 Spanners.
   Pruned edges are drawn in faint dashed gray; retained edges are solid vibrant teal.
"""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.spanner import build_greedy_spanner, generate_edge_permutation


def ensure_figures_dir():
    os.makedirs("figures", exist_ok=True)


def plot_ba00_standalone(G, pos):
    """Plot the standalone BA_00 graph with node size scaled by degree."""
    plt.figure(figsize=(12, 12), facecolor="#ffffff")
    ax = plt.gca()
    ax.set_facecolor="#ffffff"

    degrees = dict(G.degree())
    max_deg = max(degrees.values())
    node_sizes = [15 + 250 * (degrees[n] / max_deg) for n in G.nodes()]
    node_colors = [degrees[n] for n in G.nodes()]

    # Draw edges with subtle alpha
    nx.draw_networkx_edges(
        G, pos,
        alpha=0.25,
        edge_color="#64748b",
        width=0.6,
        ax=ax
    )

    # Draw nodes colored by degree using a vibrant colormap
    nodes = nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.plasma,
        alpha=0.9,
        ax=ax
    )

    cbar = plt.colorbar(nodes, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Node Degree (Hub Prominence)", color="#111827", fontsize=12)
    cbar.ax.yaxis.set_tick_params(color="#111827")
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#111827')

    plt.title(
        f"Barabási–Albert Network (BA_00)\nN = {G.number_of_nodes()}, |E| = {G.number_of_edges()}, Max Degree Δ = {max_deg}",
        color="#111827",
        fontsize=15,
        pad=15,
        fontweight="bold"
    )
    plt.axis("off")
    plt.tight_layout()

    out_path = os.path.join("figures", "ba_00_topology.png")
    plt.savefig(out_path, dpi=300, facecolor="#ffffff", bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_spanner_thinning_progression(G, pos):
    """Plot a 4-panel progression comparing original BA_00 to t=3, t=5, and t=7 spanners."""
    fig, axes = plt.subplots(1, 4, figsize=(24, 6), facecolor="#ffffff")

    t_values = [None, 3, 5, 7]
    degrees = dict(G.degree())
    max_deg = max(degrees.values())
    node_sizes = [10 + 120 * (degrees[n] / max_deg) for n in G.nodes()]

    original_edges = set(G.edges())
    # Deterministic edge permutation
    shuffled_edges = generate_edge_permutation(G, seed=42)

    for idx, (ax, t_val) in enumerate(zip(axes, t_values)):
        ax.set_facecolor("#ffffff")

        if t_val is None:
            # Original Graph
            title = f"Original Graph\n|E| = {G.number_of_edges()} (100%)"
            retained_edges = list(original_edges)
            pruned_edges = []
            edge_color = "#0284c7"  # vibrant blue
        else:
            # Build Greedy t-Spanner
            H = build_greedy_spanner(G, t=t_val, edge_order=shuffled_edges)
            retained_set = set(H.edges())
            retained_edges = list(retained_set)
            pruned_edges = [
                (u, v) for u, v in original_edges
                if (u, v) not in retained_set and (v, u) not in retained_set
            ]
            retention_pct = (len(retained_edges) / len(original_edges)) * 100
            pruned_count = len(pruned_edges)
            title = f"Greedy t-Spanner (t = {t_val})\n|E_H| = {len(retained_edges)} ({retention_pct:.1f}%) | Pruned: {pruned_count}"
            edge_color = "#0d9488"  # teal

        # Draw pruned edges in faint dashed red/gray
        if pruned_edges:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=pruned_edges,
                alpha=0.20,
                edge_color="#e11d48",
                style="dashed",
                width=0.45,
                ax=ax
            )

        # Draw retained spanner edges
        nx.draw_networkx_edges(
            G, pos,
            edgelist=retained_edges,
            alpha=0.60,
            edge_color=edge_color,
            width=0.75,
            ax=ax
        )

        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_size=node_sizes,
            node_color="#d97706",
            alpha=0.85,
            ax=ax
        )

        ax.set_title(title, color="#111827", fontsize=12, pad=10, fontweight="bold")
        ax.axis("off")

    plt.suptitle(
        "Empirical Greedy Map-Thinning on Barabási–Albert Instance BA_00 (N = 1000)\n"
        "(Pruned edges shown in faint red; retained spanner edges in solid teal)",
        color="#111827",
        fontsize=15,
        fontweight="bold",
        y=1.03
    )
    plt.tight_layout()

    out_path = os.path.join("figures", "ba_00_spanner_thinning.png")
    plt.savefig(out_path, dpi=300, facecolor="#ffffff", bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main():
    print("=" * 60)
    print("VISUALIZING BA_00 TOPOLOGY & SPANNER THINNING")
    print("=" * 60)
    ensure_figures_dir()

    graph_path = os.path.join("data", "graphs", "BA_00.graphml")
    if not os.path.exists(graph_path):
        print(f"Error: {graph_path} not found. Run Phase 1 first.")
        return

    print("Loading BA_00.graphml...")
    G = nx.read_graphml(graph_path)
    G = nx.convert_node_labels_to_integers(G)

    print("Computing spring layout (k=0.08, iterations=60)...")
    # k controls distance between nodes; optimal layout for 1000 nodes
    pos = nx.spring_layout(G, k=0.08, iterations=60, seed=42)

    print("Rendering standalone BA_00 hub visualization...")
    plot_ba00_standalone(G, pos)

    print("Rendering 4-panel spanner thinning progression (Original vs t=3, 5, 7)...")
    plot_spanner_thinning_progression(G, pos)

    print("=" * 60)
    print("VISUALIZATIONS COMPLETE!")
    print("Check figures/ directory for outputs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
