"""Generate IEEE Figure 3: Cleveland/Tukey Point-and-Range Stretch Distributions.

Renders non-parametric distributional summaries (median marker, interquartile range
bar, and min-max whiskers) across N = 30 nested graph-level means per topology:
- figures/fig3_stretch_distributions.png
- figures/fig3_stretch_distributions_95th.png
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# IEEE Publication Styling Configuration
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
    "mathtext.fontset": "stix",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.9,
    "axes.labelsize": 11.5,
    "axes.titlesize": 11.5,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "legend.fontsize": 9.2,
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

TOPO_COLORS = {
    "BA": "#D55E00",    # Vermilion / Deep Amber-Orange
    "WS": "#0072B2",    # Strong Blue
    "ER": "#C02942",    # High-contrast Crimson Red
    "GRID": "#009E73",  # Sea Green / Teal
}

TOPO_NAMES = {
    "BA": "Barabási–Albert (BA)",
    "WS": "Watts–Strogatz (WS)",
    "ER": "Erdős–Rényi (ER)",
    "GRID": "Perturbed 2D Grid (GRID)",
}

TOPO_MARKERS = {
    "BA": "o",
    "WS": "s",
    "ER": "^",
    "GRID": "D",
}

TOPO_ORDER = ["BA", "WS", "ER", "GRID"]

def style_axis(ax):
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    ax.tick_params(direction="in", top=True, right=True, length=3.5, width=0.8)
    ax.yaxis.grid(True, linestyle=":", color="#d0d0d0", linewidth=0.7, alpha=0.9)
    ax.set_axisbelow(True)

def render_panel(ax, nested, col, title, ylabel):
    style_axis(ax)
    t_vals = [3, 5, 7]
    width = 0.175

    for i, t in enumerate(t_vals):
        for j, topo in enumerate(TOPO_ORDER):
            pos = i + (j - 1.5) * width * 1.18
            sub = nested[(nested["t_limit"] == t) & (nested["topology"] == topo)][col]
            
            q25 = sub.quantile(0.25)
            q50 = sub.median()
            q75 = sub.quantile(0.75)
            min_val = sub.min()
            max_val = sub.max()
            
            # Thin whisker spanning full Min-Max range with small end caps
            ax.errorbar(
                pos, q50, yerr=[[q50 - min_val], [max_val - q50]],
                fmt="none", ecolor=TOPO_COLORS[topo], elinewidth=1.2,
                capsize=3.5, capthick=1.2, zorder=2
            )
            
            # Thick colored vertical bar representing IQR (25th to 75th percentile)
            ax.plot(
                [pos, pos], [q25, q75],
                color=TOPO_COLORS[topo], linewidth=5.0,
                solid_capstyle="round", zorder=3
            )
            
            # Prominent large marker at the median
            ax.scatter(
                [pos], [q50],
                marker=TOPO_MARKERS[topo],
                s=85,
                color=TOPO_COLORS[topo],
                edgecolor="#111111",
                linewidth=1.2,
                zorder=4
            )

    ax.set_title(title, fontweight="bold", pad=9)
    ax.set_xlabel("Stretch Factor $t$", labelpad=6)
    ax.set_ylabel(ylabel, labelpad=6)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["$t = 3$", "$t = 5$", "$t = 7$"])

    topo_handles = [
        plt.Line2D(
            [0], [0],
            marker=TOPO_MARKERS[t],
            color="w",
            markerfacecolor=TOPO_COLORS[t],
            markeredgecolor="#111111",
            markeredgewidth=1.1,
            markersize=8.5,
            label=TOPO_NAMES[t]
        )
        for t in TOPO_ORDER
    ]
    
    key_handle = plt.Line2D(
        [0], [0],
        color="#444444",
        linewidth=4.0,
        marker="o",
        markersize=5.5,
        markerfacecolor="#444444",
        markeredgecolor="#111111",
        label="Marker: Median | Bar: IQR | Whiskers: Min–Max"
    )

    ax.legend(
        handles=topo_handles + [key_handle],
        loc="upper left",
        frameon=True,
        facecolor="#ffffff",
        edgecolor="#cccccc",
        framealpha=0.96,
        title=None,
    )

def main():
    exp_csv = os.path.join("data", "spanner_experiments.csv")
    df = pd.read_csv(exp_csv)
    
    # 2-stage nested aggregation across 10 permutations
    nested = df.groupby(["topology", "graph_id", "t_limit"]).agg(
        avg_stretch_mean=("avg_stretch", "mean"),
        p95_stretch_mean=("p95_stretch", "mean"),
    ).reset_index()

    out_dir = "figures"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Standalone panel (a)
    fig_a, ax_a = plt.subplots(figsize=(6.8, 4.6))
    render_panel(
        ax_a, nested, "avg_stretch_mean",
        r"Empirical Average Stretch ($\bar{s}$) Across $t$",
        r"Empirical Average Stretch Ratio ($\bar{s}$)"
    )
    plt.tight_layout(pad=1.0)
    out_a = os.path.join(out_dir, "fig3_stretch_distributions.png")
    plt.savefig(out_a, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_a}")

    # 2. Standalone panel (b)
    fig_b, ax_b = plt.subplots(figsize=(6.8, 4.6))
    render_panel(
        ax_b, nested, "p95_stretch_mean",
        r"95th-Percentile Tail Stretch ($P_{95}$) Across $t$",
        r"95th-Percentile Tail Stretch ($P_{95}$)"
    )
    plt.tight_layout(pad=1.0)
    out_b = os.path.join(out_dir, "fig3_stretch_distributions_95th.png")
    plt.savefig(out_b, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_b}")

if __name__ == "__main__":
    main()
