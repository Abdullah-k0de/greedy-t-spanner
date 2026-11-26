"""Generate IEEE Publication Figures for the Greedy t-Spanner Empirical Study.

Produces single-column and multi-panel figures in `figures/` from the baseline
profiles (`data/baseline_metrics.csv`) and spanner evaluation dataset
(`data/spanner_experiments.csv`).
"""

import os
import sys
import glob
from collections import Counter
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.spanner import build_greedy_spanner, generate_edge_permutation

FIGURES_DIR = "figures"
EXP_CSV = os.path.join("data", "spanner_experiments.csv")
BASE_CSV = os.path.join("data", "baseline_metrics.csv")

# IEEE Publication Styling Configuration
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
    "mathtext.fontset": "stix",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9.5,
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Colorblind-safe, high-contrast academic palette (Okabe-Ito / Tol inspired)
TOPO_COLORS = {
    "BA": "#D55E00",    # Vermilion / Deep Orange-Amber
    "WS": "#0072B2",    # Strong Blue
    "ER": "#CC79A7",    # Reddish Purple / Crimson-Rose
    "GRID": "#009E73",  # Bluish Green / Teal
}

# Better high-contrast crimson for ER in line/scatter plots
TOPO_COLORS["ER"] = "#C02942"

TOPO_MARKERS = {
    "BA": "o",
    "WS": "s",
    "ER": "^",
    "GRID": "D",
}

TOPO_LINESTYLES = {
    "BA": "-",
    "WS": "--",
    "ER": "-.",
    "GRID": ":",
}

TOPO_NAMES = {
    "BA": "Barabási–Albert (BA)",
    "WS": "Watts–Strogatz (WS)",
    "ER": "Erdős–Rényi (ER)",
    "GRID": "2D Grid (GRID)",
}

TOPO_ORDER = ["BA", "WS", "ER", "GRID"]


def style_axis(ax, grid_axis="both"):
    """Apply clean IEEE axis formatting with subtle gridlines and top/right spine control."""
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    for spine in ax.spines.values():
        spine.set_color("#444444")
        spine.set_linewidth(0.8)
    ax.tick_params(direction="in", length=4, width=0.8, colors="#111111", top=True, right=True)
    if grid_axis:
        ax.grid(True, axis=grid_axis, linestyle=":", linewidth=0.6, color="#cccccc", alpha=0.8)
    else:
        ax.grid(False)


def load_datasets():
    """Load raw experiments, baseline metrics, and compute nested instance-level dataset."""
    df_exp = pd.read_csv(EXP_CSV)
    df_base = pd.read_csv(BASE_CSV)

    # Instance-level nested aggregation (across 10 permutations per graph)
    nested = df_exp.groupby(["graph_id", "topology", "instance_id", "t_limit"]).agg(
        edge_retention_mean=("edge_retention_ratio", "mean"),
        edge_retention_std=("edge_retention_ratio", "std"),
        avg_stretch_mean=("avg_stretch", "mean"),
        avg_stretch_std=("avg_stretch", "std"),
        p95_stretch_mean=("p95_stretch", "mean"),
        median_stretch_mean=("median_stretch", "mean"),
        max_stretch_mean=("max_stretch", "mean"),
        avg_additive_delay_mean=("avg_additive_delay", "mean"),
        exact_max_stretch_mean=("exact_max_stretch", "mean"),
        build_time_mean=("build_time_sec", "mean"),
    ).reset_index()

    merged = pd.merge(
        nested,
        df_base[["graph_id", "nodes", "edges", "avg_degree", "max_degree",
                 "clustering_coefficient", "avg_shortest_path_length", "diameter"]],
        on="graph_id",
        how="left"
    )

    merged["retention_pct"] = merged["edge_retention_mean"] * 100.0
    merged["retention_perm_std_pct"] = merged["edge_retention_std"] * 100.0
    merged["additive_hops"] = merged["avg_additive_delay_mean"]
    merged["theoretical_slack"] = merged["t_limit"] - merged["max_stretch_mean"]
    merged["exact_bound_slack"] = merged["t_limit"] - merged["exact_max_stretch_mean"]
    merged["budget_pct"] = (merged["avg_stretch_mean"] / merged["t_limit"]) * 100.0
    merged["build_time_ms"] = merged["build_time_mean"] * 1000.0

    return df_exp, df_base, merged


def generate_fig1_topologies():
    """IEEE Fig 1: 2x2 Native Geometry Comparison of the 4 Benchmark Topologies."""
    print("Generating IEEE Fig 1: Benchmark Topologies...")
    fig, axes = plt.subplots(2, 2, figsize=(10, 8.8))

    configs = [
        ("BA_00", "(a) Barabási–Albert (Scale-Free, $m = 2$)", axes[0, 0], "ba"),
        ("WS_00", "(b) Watts–Strogatz (Small-World, $k = 4, p = 0.1$)", axes[0, 1], "ws"),
        ("ER_00", "(c) Erdős–Rényi (Repaired Random, $p = 4/999$)", axes[1, 0], "er"),
        ("GRID_00", "(d) Perturbed 2D Grid ($25 \\times 40$ Lattice)", axes[1, 1], "grid"),
    ]

    for stem, title, ax, mode in configs:
        G = nx.read_graphml(os.path.join("data", "graphs", f"{stem}.graphml"))
        G = nx.convert_node_labels_to_integers(G)
        degrees = dict(G.degree())
        max_deg = max(degrees.values())

        if mode == "ba":
            pos = nx.spring_layout(G, k=0.10, iterations=60, seed=42)
            nx.draw_networkx_edges(G, pos, alpha=0.22, edge_color="#7f8c8d", width=0.5, ax=ax)
            sizes = [8 + 160 * (degrees[n] / max_deg) ** 1.2 for n in G.nodes()]
            colors = [degrees[n] for n in G.nodes()]
            nodes = nx.draw_networkx_nodes(
                G, pos, node_size=sizes, node_color=colors,
                cmap=plt.cm.YlOrRd, vmin=1, vmax=max_deg,
                edgecolors="#222222", linewidths=0.3, alpha=0.92, ax=ax
            )
            cbar = plt.colorbar(nodes, ax=ax, fraction=0.038, pad=0.02, shrink=0.82)
            cbar.set_label("Node Degree $k$", fontsize=9)
            cbar.ax.tick_params(labelsize=8)

        elif mode == "ws":
            pos = nx.circular_layout(G)
            # Separate ring lattice edges from rewired long-range chords
            ring_edges, chord_edges = [], []
            n_nodes = G.number_of_nodes()
            for u, v in G.edges():
                dist = min(abs(u - v), n_nodes - abs(u - v))
                if dist <= 2:
                    ring_edges.append((u, v))
                else:
                    chord_edges.append((u, v))
            nx.draw_networkx_edges(G, pos, edgelist=ring_edges, alpha=0.6, edge_color="#95a5a6", width=1.2, ax=ax)
            nx.draw_networkx_edges(G, pos, edgelist=chord_edges, alpha=0.45, edge_color=TOPO_COLORS["WS"], width=0.65, ax=ax)
            nx.draw_networkx_nodes(G, pos, node_size=8, node_color=TOPO_COLORS["WS"], ax=ax)

        elif mode == "er":
            # Radially bound extreme periphery nodes so the core component remains legible
            pos = nx.spring_layout(G, k=0.14, iterations=80, seed=42)
            # Radially bound extreme outlier chain nodes using unit vector (vec / r) so main core fills the frame
            coords = np.array(list(pos.values()))
            center = np.median(coords, axis=0)
            dists = np.linalg.norm(coords - center, axis=1)
            r_cap = np.percentile(dists, 94)
            for n, p in pos.items():
                vec = p - center
                r = np.linalg.norm(vec)
                if r > r_cap and r > 0:
                    unit_vec = vec / r
                    new_r = r_cap + 0.18 * r_cap * np.tanh((r - r_cap) / r_cap)
                    pos[n] = center + unit_vec * new_r

            nx.draw_networkx_edges(G, pos, alpha=0.22, edge_color="#7f8c8d", width=0.5, ax=ax)
            nx.draw_networkx_nodes(
                G, pos, node_size=12, node_color=TOPO_COLORS["ER"],
                edgecolors="#222222", linewidths=0.25, alpha=0.85, ax=ax
            )

        elif mode == "grid":
            cols = 40
            pos = {i: (i % cols, -(i // cols)) for i in G.nodes()}
            nx.draw_networkx_edges(G, pos, alpha=0.85, edge_color=TOPO_COLORS["GRID"], width=0.9, ax=ax)
            nx.draw_networkx_nodes(G, pos, node_size=7, node_color="#111111", ax=ax)

        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
        ax.axis("off")

    plt.tight_layout(pad=1.2)
    out = os.path.join(FIGURES_DIR, "fig1_topologies.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def generate_fig2_degree_and_phase_space(df_base):
    """IEEE Fig 2: 3-Panel Structural Baseline Verification (Linear P(k), Log-Log P(k), C vs L Phase Space)."""
    print("Generating IEEE Fig 2: Degree Distributions & Phase Space...")
    degree_data = {t: [] for t in TOPO_ORDER}
    for fpath in glob.glob(os.path.join("data", "graphs", "*.graphml")):
        topo = os.path.basename(fpath).split("_")[0]
        if topo in degree_data:
            G = nx.read_graphml(fpath)
            for _, d in G.degree():
                degree_data[topo].append(d)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))

    # Panel (a): Linear degree distribution for k <= 20
    ax1 = axes[0]
    style_axis(ax1)
    for topo in TOPO_ORDER:
        degs = degree_data[topo]
        counts = Counter(degs)
        k_vals = [k for k in sorted(counts.keys()) if k <= 20]
        p_k = [counts[k] / len(degs) for k in k_vals]
        ax1.plot(
            k_vals, p_k,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=5, linewidth=1.6, alpha=0.9
        )
    ax1.set_title("(a) Empirical Degree Distribution (Linear)", fontweight="bold", pad=8)
    ax1.set_xlabel("Node Degree $k$ (clipped at $k \\leq 20$)")
    ax1.set_ylabel("Probability $P(k)$")
    ax1.set_xlim(0.5, 20.5)
    ax1.set_ylim(-0.02, 0.86)
    ax1.legend(loc="upper right", frameon=True, edgecolor="#cccccc")

    # Panel (b): Log-Log scale showing full power-law tail up to k = 116
    ax2 = axes[1]
    style_axis(ax2)
    for topo in TOPO_ORDER:
        degs = degree_data[topo]
        counts = Counter(degs)
        k_vals = [k for k in sorted(counts.keys()) if k > 0]
        p_k = [counts[k] / len(degs) for k in k_vals]
        ax2.loglog(
            k_vals, p_k,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=4.5, linewidth=1.4, alpha=0.88
        )
    # Reference power-law line k^-3
    k_ref = np.linspace(3, 85, 50)
    p_ref = 3.2 * (k_ref ** -3.0)
    ax2.loglog(k_ref, p_ref, color="#333333", linestyle="--", linewidth=1.2, label="Power-Law Ref. ($k^{-3}$)")
    ax2.set_title("(b) Heavy-Tail Fingerprint (Log–Log)", fontweight="bold", pad=8)
    ax2.set_xlabel("Node Degree $k$ (log scale)")
    ax2.set_ylabel("Probability $P(k)$ (log scale)")
    ax2.legend(loc="upper right", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    # Panel (c): Clustering vs Path Length Phase Space
    ax3 = axes[2]
    style_axis(ax3)
    for topo in TOPO_ORDER:
        sub = df_base[df_base["topology"] == topo]
        ax3.scatter(
            sub["avg_shortest_path_length"], sub["clustering_coefficient"],
            c=TOPO_COLORS[topo], marker=TOPO_MARKERS[topo],
            s=55, alpha=0.85, edgecolors="#222222", linewidths=0.5,
            label=TOPO_NAMES[topo]
        )

    # Cluster centroid annotations
    ax3.text(9.6, 0.365, "WS ($C \\approx 0.37, L \\approx 8.8$)", color=TOPO_COLORS["WS"], fontsize=9, fontweight="bold")
    ax3.text(3.8, 0.068, "BA ($L \\approx 4.1, \\Delta \\leq 116$)", color=TOPO_COLORS["BA"], fontsize=9, fontweight="bold")
    ax3.text(6.2, 0.015, "ER ($C \\approx 0.004, L \\approx 5.4$)", color=TOPO_COLORS["ER"], fontsize=9, fontweight="bold")
    ax3.text(14.8, 0.035, "GRID ($C = 0, L \\approx 21.7$)", color=TOPO_COLORS["GRID"], fontsize=9, fontweight="bold")

    ax3.set_title("(c) Topological Phase Space ($C$ vs. $L$)", fontweight="bold", pad=8)
    ax3.set_xlabel("Average Shortest-Path Length $L$")
    ax3.set_ylabel("Average Clustering Coefficient $C$")
    ax3.set_xlim(3.0, 23.0)
    ax3.set_ylim(-0.02, 0.42)
    ax3.legend(loc="center right", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    plt.tight_layout(pad=1.2)
    out = os.path.join(FIGURES_DIR, "ieee_fig2_degree_and_phase_space.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def generate_fig3_stretch_distributions(merged):
    """IEEE Fig 3: Cleveland/Tukey Point & Range Plot (Marker: Median | Bar: IQR | Whiskers: Min-Max)."""
    print("Generating IEEE Fig 3: Point & Range Stretch Distributions...")
    import scripts.generate_fig3_point_range as p_range
    p_range.main()


def generate_fig4_sparsity_and_pareto(merged):
    """IEEE Fig 4: Edge Retention Ratio vs. t and Stretch-Sparsity Pareto Frontier."""
    print("Generating IEEE Fig 4: Edge Retention & Pareto Frontier...")

    summary = merged.groupby(["topology", "t_limit"]).agg(
        ret_mean=("retention_pct", "mean"),
        ret_std=("retention_pct", "std"),
        stretch_mean=("avg_stretch_mean", "mean"),
        stretch_std=("avg_stretch_mean", "std"),
        count=("retention_pct", "count"),
    ).reset_index()
    # Student's t critical value for exact 95% CI (df = count - 1 = 29)
    summary["ret_ci"] = stats.t.ppf(0.975, summary["count"] - 1) * summary["ret_std"] / np.sqrt(summary["count"])

    label_offsets = {
        ("ER", 3): (0, 8), ("ER", 5): (0, 8), ("ER", 7): (0, 8),
        ("BA", 3): (0, -14), ("BA", 5): (0, 8), ("BA", 7): (0, 8),
        ("GRID", 3): (0, 8), ("GRID", 5): (0, 8), ("GRID", 7): (-18, 7),
        ("WS", 3): (0, -14), ("WS", 5): (0, -14), ("WS", 7): (14, -13),
    }

    pareto_offsets = {
        ("BA", 3): (7, 2), ("BA", 5): (7, -2), ("BA", 7): (7, -3),
        ("ER", 3): (-28, -9), ("ER", 5): (-28, -10), ("ER", 7): (-28, -9),
        ("WS", 3): (7, -2), ("WS", 5): (7, -2), ("WS", 7): (-8, 8),
        ("GRID", 3): (7, -3), ("GRID", 5): (-26, -4), ("GRID", 7): (-26, -3),
    }
    pareto_keys = [("WS", 7), ("GRID", 7), ("GRID", 5), ("GRID", 3), ("ER", 3)]
    p_x = [summary[(summary["topology"] == tp) & (summary["t_limit"] == tl)]["ret_mean"].values[0] for tp, tl in pareto_keys]
    p_y = [summary[(summary["topology"] == tp) & (summary["t_limit"] == tl)]["stretch_mean"].values[0] for tp, tl in pareto_keys]

    # Standalone single-column fig4_sparsity.png
    fig_sp, ax_sp = plt.subplots(figsize=(6.5, 4.8))
    style_axis(ax_sp)
    for topo in TOPO_ORDER:
        sub = summary[summary["topology"] == topo].sort_values("t_limit")
        t_vals = sub["t_limit"].values
        means = sub["ret_mean"].values
        cis = sub["ret_ci"].values
        ax_sp.plot(
            t_vals, means,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=7, linewidth=2.0
        )
        ax_sp.fill_between(t_vals, means - cis, means + cis, color=TOPO_COLORS[topo], alpha=0.15)
        for t_v, m_v in zip(t_vals, means):
            dx, dy = label_offsets[(topo, int(t_v))]
            ax_sp.annotate(
                f"{m_v:.1f}%",
                (t_v, m_v),
                textcoords="offset points", xytext=(dx, dy),
                ha="center", fontsize=8.5, fontweight="bold", color=TOPO_COLORS[topo]
            )
    ax_sp.axhline(50.0, color="#555555", linestyle=":", linewidth=1.3, label="Approximate connectivity lower bound (~50%)")
    ax_sp.set_title("Edge Retention Ratio vs. Stretch Factor $t$", fontweight="bold", pad=8)
    ax_sp.set_xlabel("Stretch Factor $t$")
    ax_sp.set_ylabel("Edge Retention Ratio $|E_H| / |E_G|$ (%)")
    ax_sp.set_xticks([3, 5, 7])
    ax_sp.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax_sp.set_xlim(2.7, 7.35)
    ax_sp.set_ylim(33, 104)
    ax_sp.legend(loc="lower left", frameon=True, edgecolor="#cccccc", fontsize=8.2)
    plt.tight_layout(pad=1.0)
    plt.savefig(os.path.join(FIGURES_DIR, "fig4_sparsity.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {os.path.join(FIGURES_DIR, 'fig4_sparsity.png')}")

    # Standalone single-column fig4_pareto.png
    fig_pr, ax_pr = plt.subplots(figsize=(6.5, 4.8))
    style_axis(ax_pr)
    for topo in TOPO_ORDER:
        sub = summary[summary["topology"] == topo].sort_values("t_limit")
        x_vals = sub["ret_mean"].values
        y_vals = sub["stretch_mean"].values
        ax_pr.plot(
            x_vals, y_vals,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=7, linewidth=2.0
        )
        for _, row in sub.iterrows():
            t_int = int(row["t_limit"])
            dx, dy = pareto_offsets[(topo, t_int)]
            ax_pr.annotate(
                f"$t={t_int}$",
                (row["ret_mean"], row["stretch_mean"]),
                textcoords="offset points", xytext=(dx, dy),
                fontsize=8.5, fontweight="bold", color="#222222"
            )
    ax_pr.plot(p_x, p_y, color="#111111", linestyle="--", linewidth=1.5, alpha=0.6, zorder=3, label="Pareto Envelope")
    ax_pr.scatter(p_x, p_y, s=120, facecolors="none", edgecolors="#111111", linewidths=1.8, zorder=5)
    ax_pr.set_title("Stretch–Sparsity Pareto Trade-Off Landscape", fontweight="bold", pad=8)
    ax_pr.set_xlabel("Edge Retention Ratio (%) [$\\leftarrow$ Sparser]")
    ax_pr.set_ylabel("Empirical Average Stretch [$\\downarrow$ Lower Distortion]")
    ax_pr.set_xlim(55, 101)
    ax_pr.set_ylim(0.98, 1.66)
    ax_pr.legend(loc="upper right", frameon=True, edgecolor="#cccccc", fontsize=8.5)
    plt.tight_layout(pad=1.0)
    plt.savefig(os.path.join(FIGURES_DIR, "fig4_pareto.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {os.path.join(FIGURES_DIR, 'fig4_pareto.png')}")


def generate_fig5_structural_mechanisms(merged):
    """IEEE Fig 5: 3-Panel Structural Associations (Clustering, Path Length, Maximum Degree)."""
    print("Generating IEEE Fig 5: Three Structural Mechanisms...")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.4))

    sub_t3 = merged[merged["t_limit"] == 3]
    sub_t7 = merged[merged["t_limit"] == 7]

    # Panel (a): Clustering C vs Edge Retention at t=3 (Triangle Pruning Mechanism)
    style_axis(ax1)
    for topo in TOPO_ORDER:
        t_df = sub_t3[sub_t3["topology"] == topo]
        ax1.scatter(
            t_df["clustering_coefficient"], t_df["retention_pct"],
            c=TOPO_COLORS[topo], marker=TOPO_MARKERS[topo],
            s=50, alpha=0.85, edgecolors="#222222", linewidths=0.5,
            label=TOPO_NAMES[topo]
        )
    x1, y1 = sub_t3["clustering_coefficient"], sub_t3["retention_pct"]
    s1, i1, r1, p1, _ = stats.linregress(x1, y1)
    xs1 = np.linspace(x1.min(), x1.max(), 100)
    ax1.plot(xs1, i1 + s1 * xs1, color="#333333", linestyle="--", linewidth=1.4, label=f"Fit ($r = {r1:.2f}$)")
    ax1.set_title("(a) Triadic Closure vs. Sparsity ($t=3$)", fontweight="bold", pad=8)
    ax1.set_xlabel("Baseline Clustering Coefficient $C$")
    ax1.set_ylabel("Edge Retention Ratio at $t=3$ (%)")
    ax1.set_ylim(60, 102)
    ax1.legend(loc="lower left", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    # Panel (b): Baseline Path Length L vs Average Stretch at t=7 (Distance Dilution Mechanism)
    style_axis(ax2)
    for topo in TOPO_ORDER:
        t_df = sub_t7[sub_t7["topology"] == topo]
        ax2.scatter(
            t_df["avg_shortest_path_length"], t_df["avg_stretch_mean"],
            c=TOPO_COLORS[topo], marker=TOPO_MARKERS[topo],
            s=50, alpha=0.85, edgecolors="#222222", linewidths=0.5,
            label=TOPO_NAMES[topo]
        )
    x2, y2 = sub_t7["avg_shortest_path_length"], sub_t7["avg_stretch_mean"]
    s2, i2, r2, p2, _ = stats.linregress(x2, y2)
    xs2 = np.linspace(x2.min(), x2.max(), 100)
    ax2.plot(xs2, i2 + s2 * xs2, color="#333333", linestyle="--", linewidth=1.4, label=f"Fit ($r = {r2:.2f}$)")
    ax2.set_title("(b) Baseline Distance Dilution ($t=7$)", fontweight="bold", pad=8)
    ax2.set_xlabel("Baseline Shortest-Path Length $L$")
    ax2.set_ylabel("Empirical Average Stretch ($t=7$)")
    ax2.set_ylim(1.15, 1.68)
    ax2.legend(loc="upper right", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    # Panel (c): Max Hub Degree Delta vs 95th-Percentile Stretch at t=7 (Hub Funneling)
    style_axis(ax3)
    for topo in TOPO_ORDER:
        t_df = sub_t7[sub_t7["topology"] == topo]
        ax3.scatter(
            t_df["max_degree"], t_df["p95_stretch_mean"],
            c=TOPO_COLORS[topo], marker=TOPO_MARKERS[topo],
            s=50, alpha=0.85, edgecolors="#222222", linewidths=0.5,
            label=TOPO_NAMES[topo]
        )
    x3, y3 = sub_t7["max_degree"], sub_t7["p95_stretch_mean"]
    s3, i3, r3, p3, _ = stats.linregress(x3, y3)
    xs3 = np.linspace(x3.min(), x3.max(), 100)
    ax3.plot(xs3, i3 + s3 * xs3, color="#333333", linestyle="--", linewidth=1.4, label=f"Fit ($r = {r3:.2f}$)")
    ax3.set_title("(c) Hub Prominence vs. Tail Stretch ($t=7$)", fontweight="bold", pad=8)
    ax3.set_xlabel("Maximum Hub Degree $\\Delta$")
    ax3.set_ylabel("95th-Percentile Stretch $P_{95}$ ($t=7$)")
    ax3.set_ylim(1.48, 2.75)
    ax3.legend(loc="lower right", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    plt.tight_layout(pad=1.2)
    out = os.path.join(FIGURES_DIR, "fig5_structural_mechanisms.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def generate_fig6_relative_vs_absolute_duality(merged):
    """IEEE Fig 6: Multiplicative Relative Stretch vs. Absolute Additive Hop Delay."""
    print("Generating IEEE Fig 6: Relative vs Absolute Detour Duality...")
    t_vals = [3, 5, 7]
    x = np.arange(len(t_vals))
    width = 0.19

    # Standalone single-column fig6_multiplicative.png
    fig_m, ax_m = plt.subplots(figsize=(6.5, 4.4))
    style_axis(ax_m, grid_axis="y")
    for i, topo in enumerate(TOPO_ORDER):
        sub = merged[merged["topology"] == topo]
        means = [sub[sub["t_limit"] == t]["avg_stretch_mean"].mean() for t in t_vals]
        stds = [sub[sub["t_limit"] == t]["avg_stretch_mean"].std() for t in t_vals]
        pos = x + (i - 1.5) * width
        bars = ax_m.bar(
            pos, means, width, yerr=stds, capsize=3,
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            edgecolor="#222222", linewidth=0.7, alpha=0.9
        )
        for bar, std_v in zip(bars, stds):
            yval = bar.get_height()
            ax_m.text(
                bar.get_x() + bar.get_width() / 2.0, yval + std_v + 0.015,
                f"{yval:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#111111"
            )
    ax_m.set_title("Multiplicative Relative Stretch $\\mathbb{E}[d_H / d_G]$", fontweight="bold", pad=8)
    ax_m.set_xlabel("Stretch Factor $t$")
    ax_m.set_ylabel("Empirical Average Stretch Ratio ($\\pm 1$ SD)")
    ax_m.set_xticks(x)
    ax_m.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax_m.set_ylim(0.95, 1.75)
    ax_m.legend(loc="upper left", frameon=True, edgecolor="#cccccc", fontsize=8.8)
    plt.tight_layout(pad=1.0)
    plt.savefig(os.path.join(FIGURES_DIR, "fig6_multiplicative.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {os.path.join(FIGURES_DIR, 'fig6_multiplicative.png')}")

    # Standalone single-column fig6_additive.png
    fig_a, ax_a = plt.subplots(figsize=(6.5, 4.4))
    style_axis(ax_a, grid_axis="y")
    for i, topo in enumerate(TOPO_ORDER):
        sub = merged[merged["topology"] == topo]
        means = [sub[sub["t_limit"] == t]["additive_hops"].mean() for t in t_vals]
        stds = [sub[sub["t_limit"] == t]["additive_hops"].std() for t in t_vals]
        pos = x + (i - 1.5) * width
        bars = ax_a.bar(
            pos, means, width, yerr=stds, capsize=3,
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            edgecolor="#222222", linewidth=0.7, alpha=0.9
        )
        for bar, std_v in zip(bars, stds):
            yval = bar.get_height()
            ax_a.text(
                bar.get_x() + bar.get_width() / 2.0, yval + std_v + 0.08,
                f"+{yval:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#111111"
            )
    ax_a.set_title("Absolute Additive Path Delay $\\mathbb{E}[d_H - d_G]$ (Hops)", fontweight="bold", pad=8)
    ax_a.set_xlabel("Stretch Factor $t$")
    ax_a.set_ylabel("Mean Extra Detour Hops Added ($\\pm 1$ SD)")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax_a.set_ylim(0, 4.3)
    ax_a.legend(loc="upper left", frameon=True, edgecolor="#cccccc", fontsize=8.8)
    plt.tight_layout(pad=1.0)
    plt.savefig(os.path.join(FIGURES_DIR, "fig6_additive.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {os.path.join(FIGURES_DIR, 'fig6_additive.png')}")


def generate_fig7_pessimism_runtime_stability(merged):
    """IEEE Fig 7: 3-Panel Practical Heuristics (Theoretical Slack, BFS Runtime Overhead, Permutation Stability)."""
    print("Generating IEEE Fig 7: Theoretical Slack, Runtime & Permutation Stability...")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.4))
    t_vals = [3, 5, 7]

    # Panel (a): Theoretical Slack (t - Max Stretch)
    style_axis(ax1)
    for topo in TOPO_ORDER:
        sub = merged[merged["topology"] == topo]
        means = [sub[sub["t_limit"] == t]["theoretical_slack"].mean() for t in t_vals]
        stds = [sub[sub["t_limit"] == t]["theoretical_slack"].std() for t in t_vals]
        ax1.plot(
            t_vals, means,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=6.5, linewidth=1.9
        )
        ax1.fill_between(t_vals, np.array(means) - np.array(stds), np.array(means) + np.array(stds),
                         color=TOPO_COLORS[topo], alpha=0.14)
    ax1.set_title("(a) Sampled Route Bound Slack ($t - s_{\\max}$)", fontweight="bold", pad=8)
    ax1.set_xlabel("Stretch Factor $t$")
    ax1.set_ylabel("Sampled Bound Slack ($t - s_{\\max}$)")
    ax1.set_xticks(t_vals)
    ax1.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax1.legend(loc="upper left", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    # Panel (b): Runtime Scaling (Milliseconds)
    style_axis(ax2)
    for topo in TOPO_ORDER:
        sub = merged[merged["topology"] == topo]
        means = [sub[sub["t_limit"] == t]["build_time_ms"].mean() for t in t_vals]
        stds = [sub[sub["t_limit"] == t]["build_time_ms"].std() for t in t_vals]
        ax2.plot(
            t_vals, means,
            marker=TOPO_MARKERS[topo], linestyle=TOPO_LINESTYLES[topo],
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            markersize=6.5, linewidth=1.9
        )
        ax2.fill_between(t_vals, np.array(means) - np.array(stds), np.array(means) + np.array(stds),
                         color=TOPO_COLORS[topo], alpha=0.14)
    ax2.set_title("(b) Bounded-BFS Construction Time", fontweight="bold", pad=8)
    ax2.set_xlabel("Stretch Factor $t$")
    ax2.set_ylabel("Mean Execution Time (ms)")
    ax2.set_xticks(t_vals)
    ax2.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax2.legend(loc="upper left", frameon=True, edgecolor="#cccccc", fontsize=8.5)

    # Panel (c): Edge-Ordering Permutation Sensitivity (Intra-graph SD across 10 permutations)
    style_axis(ax3, grid_axis="y")
    x = np.arange(len(t_vals))
    width = 0.19
    for i, topo in enumerate(TOPO_ORDER):
        sub = merged[merged["topology"] == topo]
        means = [sub[sub["t_limit"] == t]["retention_perm_std_pct"].mean() for t in t_vals]
        stds = [sub[sub["t_limit"] == t]["retention_perm_std_pct"].std() for t in t_vals]
        pos = x + (i - 1.5) * width
        ax3.bar(
            pos, means, width, yerr=stds, capsize=2.5,
            color=TOPO_COLORS[topo], label=TOPO_NAMES[topo],
            edgecolor="#222222", linewidth=0.7, alpha=0.9
        )
    ax3.axhline(1.0, color="#C02942", linestyle="--", linewidth=1.2, label="1.0% Variance Threshold")
    ax3.set_title("(c) Edge-Ordering Sensitivity ($\\sigma_{\\text{perm}}$)", fontweight="bold", pad=8)
    ax3.set_xlabel("Stretch Factor $t$")
    ax3.set_ylabel("Intra-Instance Retention Std. Dev. (%)")
    ax3.set_xticks(x)
    ax3.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])
    ax3.set_ylim(0, 1.15)
    ax3.legend(loc="upper left", frameon=True, edgecolor="#cccccc", fontsize=8.0)

    plt.tight_layout(pad=1.2)
    out = os.path.join(FIGURES_DIR, "ieee_fig7_pessimism_runtime_stability.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def generate_fig8_visual_spanner_thinning():
    """IEEE Fig 8: 2x4 Visual Demonstration of Spanner Thinning on a 10x12 Grid Window and BA Hub Subgraph."""
    print("Generating IEEE Fig 8: Visual Spanner Thinning Progression...")
    fig, axes = plt.subplots(2, 4, figsize=(15, 7.2))
    t_values = [None, 3, 5, 7]

    # Row 1: Interior 10x12 Sub-Grid of GRID_00
    G_grid = nx.read_graphml(os.path.join("data", "graphs", "GRID_00.graphml"))
    G_grid = nx.convert_node_labels_to_integers(G_grid)
    cols = 40
    # Select a 10x12 window in the interior (rows 5..14, cols 10..21)
    win_nodes = [r * cols + c for r in range(5, 15) for c in range(10, 22)]
    sub_grid = G_grid.subgraph(win_nodes).copy()
    pos_grid = {n: (n % cols, -(n // cols)) for n in sub_grid.nodes()}
    grid_edges = set(sub_grid.edges())
    perm_grid = generate_edge_permutation(G_grid, seed=42)

    panel_letters_top = ["(a)", "(b)", "(c)", "(d)"]
    for idx, (ax, t_val, let) in enumerate(zip(axes[0], t_values, panel_letters_top)):
        if t_val is None:
            retained = list(grid_edges)
            pruned = []
            title = f"{let} 2D Grid Window (Original)\n$|E_{{\\text{{sub}}}}| = {len(retained)}$ (100%)"
        else:
            H = build_greedy_spanner(G_grid, t=t_val, edge_order=perm_grid)
            h_edges = set(H.edges())
            retained = [e for e in grid_edges if e in h_edges or (e[1], e[0]) in h_edges]
            pruned = [e for e in grid_edges if e not in h_edges and (e[1], e[0]) not in h_edges]
            pct = len(retained) / len(grid_edges) * 100
            title = f"{let} Grid Spanner ($t = {t_val}$)\nRetained: {len(retained)} ({pct:.0f}%), Pruned: {len(pruned)}"

        if pruned:
            nx.draw_networkx_edges(sub_grid, pos_grid, edgelist=pruned,
                                   edge_color="#C02942", style="dashed", alpha=0.55, width=1.2, ax=ax)
        nx.draw_networkx_edges(sub_grid, pos_grid, edgelist=retained,
                               edge_color=TOPO_COLORS["GRID"], alpha=0.95, width=1.8, ax=ax)
        nx.draw_networkx_nodes(sub_grid, pos_grid, node_size=22, node_color="#111111", ax=ax)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.axis("off")

    # Row 2: BA_00 Hub Neighborhood (Hub + 35 neighbors)
    G_ba = nx.read_graphml(os.path.join("data", "graphs", "BA_00.graphml"))
    G_ba = nx.convert_node_labels_to_integers(G_ba)
    degrees = dict(G_ba.degree())
    hub_node = max(degrees, key=degrees.get)
    nbrs = sorted(list(G_ba.neighbors(hub_node)), key=lambda n: degrees[n], reverse=True)[:35]
    sub_ba = G_ba.subgraph([hub_node] + nbrs).copy()
    ba_edges = set(sub_ba.edges())
    perm_ba = generate_edge_permutation(G_ba, seed=42)

    pos_ba = nx.spring_layout(sub_ba, seed=42, k=0.38)
    pos_ba[hub_node] = np.array([0.0, 0.0])

    node_colors = [TOPO_COLORS["BA"] if n == hub_node else TOPO_COLORS["WS"] for n in sub_ba.nodes()]
    node_sizes = [280 if n == hub_node else 75 for n in sub_ba.nodes()]

    panel_letters_bot = ["(e)", "(f)", "(g)", "(h)"]
    for idx, (ax, t_val, let) in enumerate(zip(axes[1], t_values, panel_letters_bot)):
        if t_val is None:
            retained = list(ba_edges)
            pruned = []
            title = f"{let} BA Hub Ego-Net (Original)\n$|E_{{\\text{{sub}}}}| = {len(retained)}$ (100%)"
        else:
            H = build_greedy_spanner(G_ba, t=t_val, edge_order=perm_ba)
            h_edges = set(H.edges())
            retained = [e for e in ba_edges if e in h_edges or (e[1], e[0]) in h_edges]
            pruned = [e for e in ba_edges if e not in h_edges and (e[1], e[0]) not in h_edges]
            pct = len(retained) / len(ba_edges) * 100
            title = f"{let} BA Hub Spanner ($t = {t_val}$)\nRetained: {len(retained)} ({pct:.0f}%), Pruned: {len(pruned)}"

        if pruned:
            nx.draw_networkx_edges(sub_ba, pos_ba, edgelist=pruned,
                                   edge_color="#C02942", style="dashed", alpha=0.55, width=1.3, ax=ax)
        nx.draw_networkx_edges(sub_ba, pos_ba, edgelist=retained,
                               edge_color=TOPO_COLORS["GRID"], alpha=0.92, width=1.7, ax=ax)
        nx.draw_networkx_nodes(sub_ba, pos_ba, node_size=node_sizes, node_color=node_colors,
                               edgecolors="#111111", linewidths=0.8, ax=ax)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.axis("off")

    # Shared figure legend at the bottom
    legend_handles = [
        mlines.Line2D([], [], color=TOPO_COLORS["GRID"], linewidth=2.0, linestyle="-", label="Retained Spanner Edge ($e \\in E_H$)"),
        mlines.Line2D([], [], color="#C02942", linewidth=1.5, linestyle="--", label="Pruned Redundant Edge ($e \\in E_G \\setminus E_H$)"),
        mlines.Line2D([], [], color=TOPO_COLORS["BA"], marker="o", linestyle="None", markersize=9, markeredgecolor="#111111", label="Primary Scale-Free Hub ($\\Delta = 82$)"),
        mlines.Line2D([], [], color=TOPO_COLORS["WS"], marker="o", linestyle="None", markersize=6, markeredgecolor="#111111", label="Hub Neighbor Node"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4, frameon=True, edgecolor="#cccccc", fontsize=9.5, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout(rect=[0, 0.04, 1, 1], pad=1.0)
    out = os.path.join(FIGURES_DIR, "ieee_fig8_visual_spanner_thinning.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def main():
    print("=" * 72)
    print("GENERATING IEEE PUBLICATION FIGURES")
    print("=" * 72)
    os.makedirs(FIGURES_DIR, exist_ok=True)
    df_exp, df_base, merged = load_datasets()

    generate_fig1_topologies()
    generate_fig3_stretch_distributions(merged)
    generate_fig4_sparsity_and_pareto(merged)
    generate_fig5_structural_mechanisms(merged)
    generate_fig6_relative_vs_absolute_duality(merged)
    print("=" * 72)
    print("All IEEE figures generated successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
