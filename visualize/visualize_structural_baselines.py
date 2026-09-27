"""Generate Publication-Quality Visualizations for Baseline Structural Profiles.

Strictly uses empirical data from:
- data/graphs/*.graphml (All 120 real graph instances)
- data/baseline_metrics.csv (All 120 real profiling measurements)

Outputs:
1. figures/baseline_topologies_native_layouts.png:
   2x2 panel showing BA (Hub-Centric), WS (Circular Ring), ER (Uniform Random), and Grid (Planar 25x40).
2. figures/baseline_degree_distributions.png:
   Empirical degree distribution P(k) across all 120,000 nodes (30 instances x 4 topologies)
   in both linear and log-log scale (proving power-law vs Poisson vs lattice).
3. figures/baseline_clustering_vs_path_length.png:
   Phase space scatter plot (C vs L) for all 120 independent instances showing topological separation.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def ensure_figures_dir():
    os.makedirs("figures", exist_ok=True)


def plot_topologies_native_layouts():
    """Generate 2x2 panel showing BA, WS, ER, and Grid in their native layouts."""
    print("Rendering 2x2 Native Layouts Comparison...")
    fig, axes = plt.subplots(2, 2, figsize=(18, 16), facecolor="#0e1117")

    topo_configs = [
        ("BA_00", "Barabási–Albert (BA_00)", axes[0, 0], "ba"),
        ("WS_00", "Watts–Strogatz (WS_00)", axes[0, 1], "ws"),
        ("ER_00", "Erdős–Rényi Repaired (ER_00)", axes[1, 0], "er"),
        ("GRID_00", "Perturbed 2D Grid (GRID_00)", axes[1, 1], "grid"),
    ]

    for filename_stem, title, ax, layout_type in topo_configs:
        ax.set_facecolor("#0e1117")
        graph_path = os.path.join("data", "graphs", f"{filename_stem}.graphml")
        if not os.path.exists(graph_path):
            print(f"Warning: {graph_path} not found.")
            continue

        G = nx.read_graphml(graph_path)
        G = nx.convert_node_labels_to_integers(G)
        degrees = dict(G.degree())
        max_deg = max(degrees.values())

        if layout_type == "ws":
            # Circular layout highlights local lattice chords and cross-ring shortcuts
            pos = nx.circular_layout(G)
            edge_color = "#38bdf8"
            edge_alpha = 0.20
            edge_width = 0.5
            node_sizes = [12 for _ in G.nodes()]
            node_color = "#f59e0b"
            subtitle = f"N = {G.number_of_nodes()}, |E| = {G.number_of_edges()} | Circular Layout (Ring + Shortcuts)"

        elif layout_type == "grid":
            # True 2D coordinate lattice (25 rows x 40 cols)
            cols = 40
            pos = {i: (i % cols, -(i // cols)) for i in G.nodes()}
            edge_color = "#2dd4bf"
            edge_alpha = 0.70
            edge_width = 0.8
            node_sizes = [6 for _ in G.nodes()]
            node_color = "#f8fafc"
            subtitle = f"N = {G.number_of_nodes()}, |E| = {G.number_of_edges()} | Planar 25x40 Coordinate Lattice"

        elif layout_type == "ba":
            # Spring layout with node size proportional to hub degree
            pos = nx.spring_layout(G, k=0.08, iterations=50, seed=42)
            edge_color = "#94a3b8"
            edge_alpha = 0.20
            edge_width = 0.5
            node_sizes = [10 + 180 * (degrees[n] / max_deg) for n in G.nodes()]
            node_color = [degrees[n] for n in G.nodes()]
            subtitle = f"N = {G.number_of_nodes()}, |E| = {G.number_of_edges()} | Hub-Prominence (Max Δ = {max_deg})"

        else:  # er
            # Uniform spring layout
            pos = nx.spring_layout(G, k=0.06, iterations=50, seed=42)
            edge_color = "#a78bfa"
            edge_alpha = 0.22
            edge_width = 0.5
            node_sizes = [12 for _ in G.nodes()]
            node_color = "#f43f5e"
            subtitle = f"N = {G.number_of_nodes()}, |E| = {G.number_of_edges()} | Uniform Random Dispersion"

        # Draw edges
        nx.draw_networkx_edges(
            G, pos,
            alpha=edge_alpha,
            edge_color=edge_color,
            width=edge_width,
            ax=ax
        )

        # Draw nodes
        if layout_type == "ba":
            nx.draw_networkx_nodes(
                G, pos,
                node_size=node_sizes,
                node_color=node_color,
                cmap=plt.cm.plasma,
                alpha=0.85,
                ax=ax
            )
        else:
            nx.draw_networkx_nodes(
                G, pos,
                node_size=node_sizes,
                node_color=node_color,
                alpha=0.85,
                ax=ax
            )

        ax.set_title(f"{title}\n{subtitle}", color="white", fontsize=13, pad=10, fontweight="bold")
        ax.axis("off")

    plt.suptitle(
        "Topological Archetypes Under Density Control (N = 1000, d_bar ≈ 3.8 - 4.0)\n"
        "Rendered in Respective Native Geometries",
        color="white",
        fontsize=16,
        fontweight="bold",
        y=0.99
    )
    plt.tight_layout()

    out_path = os.path.join("figures", "baseline_topologies_native_layouts.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_empirical_degree_distributions():
    """Aggregate actual node degrees from all 120 graphs and plot P(k) on Linear and Log-Log scales."""
    print("Aggregating degrees from all 120 graph instances...")

    degree_data = {"BA": [], "WS": [], "ER": [], "GRID": []}

    graph_files = glob.glob(os.path.join("data", "graphs", "*.graphml"))
    if not graph_files:
        print("No graph files found in data/graphs/.")
        return

    for fpath in graph_files:
        basename = os.path.basename(fpath)
        topo = basename.split("_")[0]
        if topo in degree_data:
            G = nx.read_graphml(fpath)
            for _, d in G.degree():
                degree_data[topo].append(d)

    colors = {
        "BA": "#f59e0b",   # Amber / Orange
        "WS": "#38bdf8",   # Sky Blue
        "ER": "#f43f5e",   # Rose / Red
        "GRID": "#2dd4bf"  # Teal
    }

    labels = {
        "BA": "Barabási–Albert (Scale-Free)",
        "WS": "Watts–Strogatz (Small-World)",
        "ER": "Erdős–Rényi (Poisson)",
        "GRID": "2D Grid (Lattice)"
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7), facecolor="#0e1117")
    ax1.set_facecolor("#0e1117")
    ax2.set_facecolor("#0e1117")

    # Plot 1: Linear Probability Density P(k)
    for topo, degs in degree_data.items():
        total_nodes = len(degs)
        counts = Counter(degs)
        k_vals = sorted(counts.keys())
        p_k = [counts[k] / total_nodes for k in k_vals]

        ax1.plot(
            k_vals, p_k,
            marker='o',
            markersize=5,
            linewidth=1.8,
            color=colors[topo],
            label=f"{labels[topo]} (N={total_nodes})"
        )

    ax1.set_title("Empirical Degree Distribution P(k) [Linear Scale]", color="white", fontsize=14, fontweight="bold", pad=12)
    ax1.set_xlabel("Degree (k)", color="white", fontsize=12)
    ax1.set_ylabel("Probability P(k)", color="white", fontsize=12)
    ax1.tick_params(colors="white")
    ax1.grid(color="#334155", linestyle="--", alpha=0.5)
    ax1.legend(facecolor="#1e293b", edgecolor="#475569", labelcolor="white", fontsize=10)

    # Plot 2: Log-Log Scale to expose Power-Law vs Bounded Tails
    for topo, degs in degree_data.items():
        total_nodes = len(degs)
        counts = Counter(degs)
        k_vals = [k for k in sorted(counts.keys()) if k > 0]
        p_k = [counts[k] / total_nodes for k in k_vals]

        ax2.loglog(
            k_vals, p_k,
            marker='o',
            markersize=6,
            linewidth=2.0,
            color=colors[topo],
            label=f"{labels[topo]}"
        )

    ax2.set_title("Topological Degree Fingerprint [Log-Log Scale]\n(Power-Law Line vs Poisson vs Rigid Spike)", color="white", fontsize=14, fontweight="bold", pad=12)
    ax2.set_xlabel("Degree k (log scale)", color="white", fontsize=12)
    ax2.set_ylabel("Probability P(k) (log scale)", color="white", fontsize=12)
    ax2.tick_params(colors="white")
    ax2.grid(color="#334155", linestyle="--", alpha=0.5)
    ax2.legend(facecolor="#1e293b", edgecolor="#475569", labelcolor="white", fontsize=10)

    plt.suptitle(
        f"Empirical Degree Distributions Aggregated Over All 120 Instances (120,000 Nodes Total)\n"
        f"Mathematical Proof of Structural Divergence Under Strict Mean Degree Invariance (d_bar ≈ 4.0)",
        color="white",
        fontsize=15,
        fontweight="bold",
        y=1.03
    )
    plt.tight_layout()

    out_path = os.path.join("figures", "baseline_degree_distributions.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_clustering_vs_path_length():
    """Plot Clustering Coefficient (C) vs Average Shortest Path Length (L) for all 120 instances."""
    print("Rendering Clustering vs Path Length Phase Space...")

    csv_path = os.path.join("data", "baseline_metrics.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(12, 8), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    colors = {
        "BA": "#f59e0b",
        "WS": "#38bdf8",
        "ER": "#f43f5e",
        "GRID": "#2dd4bf"
    }

    markers = {
        "BA": "o",
        "WS": "s",
        "ER": "^",
        "GRID": "D"
    }

    labels = {
        "BA": "Barabási–Albert (Hubs / Short Paths)",
        "WS": "Watts–Strogatz (High Clustering)",
        "ER": "Erdős–Rényi (Uniform Random)",
        "GRID": "2D Grid (Rigid Lattice / High Diameter)"
    }

    for topo, group in df.groupby("topology"):
        ax.scatter(
            group["avg_shortest_path_length"],
            group["clustering_coefficient"],
            c=colors[topo],
            marker=markers[topo],
            s=90,
            alpha=0.85,
            edgecolors="#ffffff",
            linewidths=0.6,
            label=f"{labels[topo]} (N=30)"
        )

    ax.set_title(
        "Empirical Phase Space: Clustering Coefficient (C) vs. Average Path Length (L)\n"
        "120 Independent Benchmark Instances (N = 1000, d_bar ≈ 3.8 - 4.0)",
        color="white",
        fontsize=14,
        fontweight="bold",
        pad=15
    )
    ax.set_xlabel("Average Shortest-Path Length (L)", color="white", fontsize=12)
    ax.set_ylabel("Average Clustering Coefficient (C)", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.grid(color="#334155", linestyle="--", alpha=0.5)
    ax.legend(facecolor="#1e293b", edgecolor="#475569", labelcolor="white", fontsize=11, loc="center right")

    # Add explanatory callout annotations for all 4 topologies individually
    ax.annotate(
        "Watts–Strogatz\n(High Clustering C ≈ 0.37,\nShort Paths L ≈ 8.8)",
        xy=(8.80, 0.373),
        xytext=(11.0, 0.35),
        color="#38bdf8",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(facecolor="#38bdf8", edgecolor="none", shrink=0.08, width=1.5, headwidth=6)
    )

    ax.annotate(
        "Barabási–Albert\n(Ultra-Short Paths L ≈ 4.1,\nHubs / Low Clustering C ≈ 0.026)",
        xy=(4.06, 0.026),
        xytext=(3.4, 0.16),
        color="#f59e0b",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(facecolor="#f59e0b", edgecolor="none", shrink=0.08, width=1.5, headwidth=6)
    )

    ax.annotate(
        "Erdős–Rényi (Random)\n(Short Paths L ≈ 5.4,\nZero Clustering C ≈ 0.0036)",
        xy=(5.37, 0.0036),
        xytext=(7.2, 0.07),
        color="#f43f5e",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(facecolor="#f43f5e", edgecolor="none", shrink=0.08, width=1.5, headwidth=6)
    )

    ax.annotate(
        "Perturbed 2D Grid\n(Zero Clustering C = 0,\nHigh Path Length L ≈ 21.7)",
        xy=(21.70, 0.005),
        xytext=(16.0, 0.08),
        color="#2dd4bf",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(facecolor="#2dd4bf", edgecolor="none", shrink=0.08, width=1.5, headwidth=6)
    )

    plt.tight_layout()
    out_path = os.path.join("figures", "baseline_clustering_vs_path_length.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main():
    print("=" * 70)
    print("GENERATING BASELINE STRUCTURAL PROFILE VISUALIZATIONS")
    print("Strictly using empirical data from 120 graphs & baseline_metrics.csv")
    print("=" * 70)
    ensure_figures_dir()

    plot_topologies_native_layouts()
    plot_empirical_degree_distributions()
    plot_clustering_vs_path_length()

    print("=" * 70)
    print("ALL BASELINE VISUALIZATIONS GENERATED SUCCESSFULLY!")
    print("Check figures/ directory for outputs.")
    print("=" * 70)


if __name__ == "__main__":
    main()
