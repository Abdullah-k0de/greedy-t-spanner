"""Intuitive, Human-Readable Visualizations of Greedy Spanner Thinning.

Generates:
1. figures/grid_spanner_thinning.png:
   Clean 4-panel planar wireframe of GRID_00 (25x40).
   Since edges do not cross, mesh thinning is 100% visible and uncluttered.

2. figures/ba_zoomed_hub_thinning.png:
   Zoomed-in 35-node neighborhood around BA_00's primary hub.
   Shows exactly which spoke connections and cross-edges are pruned vs retained.
"""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.spanner import build_greedy_spanner, generate_edge_permutation


def ensure_figures_dir():
    os.makedirs("figures", exist_ok=True)


def plot_grid_spanner_thinning():
    """Plot planar 2D grid thinning progression (zero edge crossings)."""
    grid_path = os.path.join("data", "graphs", "GRID_00.graphml")
    if not os.path.exists(grid_path):
        print(f"Error: {grid_path} not found.")
        return

    G = nx.read_graphml(grid_path)
    G = nx.convert_node_labels_to_integers(G)

    # 25 rows x 40 columns coordinate mapping
    cols = 40
    pos = {i: (i % cols, -(i // cols)) for i in G.nodes()}

    fig, axes = plt.subplots(1, 4, figsize=(26, 6), facecolor="#0e1117")
    t_values = [None, 3, 5, 7]
    shuffled_edges = generate_edge_permutation(G, seed=42)
    original_edges = set(G.edges())

    for idx, (ax, t_val) in enumerate(zip(axes, t_values)):
        ax.set_facecolor("#0e1117")

        if t_val is None:
            retained = list(original_edges)
            pruned = []
            title = f"Original 2D Grid (GRID_00)\n|E| = {len(retained)} edges (100%)"
            edge_color = "#38bdf8"
        else:
            H = build_greedy_spanner(G, t=t_val, edge_order=shuffled_edges)
            retained_set = set(H.edges())
            retained = list(retained_set)
            pruned = [
                (u, v) for u, v in original_edges
                if (u, v) not in retained_set and (v, u) not in retained_set
            ]
            pct = (len(retained) / len(original_edges)) * 100
            title = f"t = {t_val} Spanner\n|E_H| = {len(retained)} ({pct:.1f}%) | Pruned: {len(pruned)}"
            edge_color = "#2dd4bf"

        # Pruned edges in dashed red
        if pruned:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=pruned,
                alpha=0.35,
                edge_color="#ef4444",
                style="dashed",
                width=1.0,
                ax=ax
            )

        # Retained edges in solid teal
        nx.draw_networkx_edges(
            G, pos,
            edgelist=retained,
            alpha=0.85,
            edge_color=edge_color,
            width=1.2,
            ax=ax
        )

        # Tiny node dots
        nx.draw_networkx_nodes(
            G, pos,
            node_size=6,
            node_color="#f8fafc",
            alpha=0.7,
            ax=ax
        )

        ax.set_title(title, color="white", fontsize=12, pad=10, fontweight="bold")
        ax.axis("off")

    plt.suptitle(
        "Planar Grid Spanner Thinning on GRID_00 (25 x 40 Lattice, N = 1000)\n"
        "(Pruned edges = dashed red | Retained spanner edges = solid teal)",
        color="white",
        fontsize=14,
        fontweight="bold",
        y=1.04
    )
    plt.tight_layout()

    out_path = os.path.join("figures", "grid_spanner_thinning.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_zoomed_hub_thinning():
    """Zoom in on a primary hub and its 35 immediate neighbors in BA_00."""
    ba_path = os.path.join("data", "graphs", "BA_00.graphml")
    if not os.path.exists(ba_path):
        print(f"Error: {ba_path} not found.")
        return

    G = nx.read_graphml(ba_path)
    G = nx.convert_node_labels_to_integers(G)

    # Find the top hub
    degrees = dict(G.degree())
    hub_node = max(degrees, key=degrees.get)
    all_neighbors = list(G.neighbors(hub_node))

    # Take the top 35 neighbors by degree for a perfectly readable local subgraph
    all_neighbors.sort(key=lambda n: degrees[n], reverse=True)
    selected_nodes = [hub_node] + all_neighbors[:35]

    subgraph = G.subgraph(selected_nodes).copy()
    sub_edges = set(subgraph.edges())

    # Build full spanners first to see which edges in this neighborhood survive
    shuffled_edges = generate_edge_permutation(G, seed=42)

    # Position: Hub in center, neighbors in a circle
    pos = nx.spring_layout(subgraph, seed=42, k=0.35)
    # Force the central hub directly into the center (0, 0)
    pos[hub_node] = (0.0, 0.0)

    fig, axes = plt.subplots(1, 4, figsize=(24, 6), facecolor="#0e1117")
    t_values = [None, 3, 5, 7]

    node_colors = ["#f59e0b" if n == hub_node else "#38bdf8" for n in subgraph.nodes()]
    node_sizes = [450 if n == hub_node else 120 for n in subgraph.nodes()]

    for idx, (ax, t_val) in enumerate(zip(axes, t_values)):
        ax.set_facecolor("#0e1117")

        if t_val is None:
            retained = list(sub_edges)
            pruned = []
            title = f"Original Hub Neighborhood\n|E_local| = {len(retained)} edges"
            edge_color = "#38bdf8"
        else:
            H = build_greedy_spanner(G, t=t_val, edge_order=shuffled_edges)
            retained_global = set(H.edges())
            retained = [
                (u, v) for u, v in sub_edges
                if (u, v) in retained_global or (v, u) in retained_global
            ]
            pruned = [
                (u, v) for u, v in sub_edges
                if (u, v) not in retained_global and (v, u) not in retained_global
            ]
            title = f"t = {t_val} Spanner\nRetained: {len(retained)} | Pruned: {len(pruned)}"
            edge_color = "#2dd4bf"

        # Draw pruned edges in dashed red
        if pruned:
            nx.draw_networkx_edges(
                subgraph, pos,
                edgelist=pruned,
                alpha=0.5,
                edge_color="#ef4444",
                style="dashed",
                width=1.8,
                ax=ax
            )

        # Draw retained edges in solid teal
        nx.draw_networkx_edges(
            subgraph, pos,
            edgelist=retained,
            alpha=0.9,
            edge_color=edge_color,
            width=2.0,
            ax=ax
        )

        # Draw nodes (Hub in gold, neighbors in blue)
        nx.draw_networkx_nodes(
            subgraph, pos,
            node_size=node_sizes,
            node_color=node_colors,
            alpha=0.95,
            ax=ax
        )

        ax.set_title(title, color="white", fontsize=12, pad=10, fontweight="bold")
        ax.axis("off")

    plt.suptitle(
        f"Zoomed-In View: Hub Node #{hub_node} (Gold Center) & 35 Neighbors in BA_00\n"
        "(Pruned edges = dashed red | Retained edges = solid teal)",
        color="white",
        fontsize=14,
        fontweight="bold",
        y=1.04
    )
    plt.tight_layout()

    out_path = os.path.join("figures", "ba_zoomed_hub_thinning.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main():
    print("=" * 60)
    print("GENERATING INTUITIVE SPANNER VISUALIZATIONS")
    print("=" * 60)
    ensure_figures_dir()

    print("1. Rendering Planar Grid Spanner Thinning (figures/grid_spanner_thinning.png)...")
    plot_grid_spanner_thinning()

    print("2. Rendering Zoomed-In Hub Neighborhood (figures/ba_zoomed_hub_thinning.png)...")
    plot_zoomed_hub_thinning()

    print("=" * 60)
    print("ALL INTUITIVE VISUALIZATIONS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
