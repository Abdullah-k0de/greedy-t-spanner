# Comprehensive Analysis of Experimental Benchmark Figures

This document provides an academic explanation of all figures generated in the `figures/` directory. These figures serve as the visual evidence and manipulation checks for the research paper: **"Empirical Evaluation of Greedy $t$-Spanners: The Impact of Graph Topology on Path Stretch and Edge Sparsity."**

---

## 1. Native Topologies Comparison (`figures/baseline_topologies_native_layouts.png`)

### Purpose
To visually demonstrate that holding graph scale ($N = 1000$) and average degree ($\bar{d} \approx 4.0$) constant does not make the graphs identical. Each network embodies a fundamentally different geometry.

### Detailed Breakdown
- **Panel A: Barabási–Albert (`BA_00`) — Hub-Prominence Layout**
  - **Visual Observation:** The central core contains glowing yellow/orange nodes of substantial diameter, surrounded by hundreds of smaller purple nodes radiating inward.
  - **Topological Meaning:** Reflects the "rich-get-richer" preferential attachment mechanism. The maximum degree reaches $\Delta = 82$. These hubs act as high-capacity structural bridges.
- **Panel B: Watts–Strogatz (`WS_00`) — Circular Ring Layout**
  - **Visual Observation:** A circular perimeter where adjacent nodes form a dense orange ring, with thin blue chord lines cutting across the interior of the circle.
  - **Topological Meaning:** Visualizes the Small-World effect ($k=4, p=0.1$). The ring demonstrates strong local clustering (cliques of neighbors), while the inner chords represent random shortcut rewirings that compress global path lengths.
- **Panel C: Erdős–Rényi Repaired (`ER_00`) — Uniform Random Dispersion**
  - **Visual Observation:** A decentralized, homogeneous cloud of randomly connected pink nodes. A thin curved chain connects a few peripheral nodes to the main body.
  - **Topological Meaning:** Visualizes uniform edge probability ($p \approx 4/999$). The thin chain illustrates the randomized component repair: $c$ components were chained together using exactly $c-1$ bridge edges to guarantee 1-connectivity without dropping isolated nodes.
- **Panel D: Perturbed 2D Grid (`GRID_00`) — Planar $25 \times 40$ Coordinate Lattice**
  - **Visual Observation:** A clean, flat rectangular grid with zero diagonal shortcuts and zero edge crossings. Small gaps appear where edges are absent.
  - **Topological Meaning:** Represents rigid planar local geometry. Every cycle has length $\ge 4$ (no triangles). The small gaps represent the 2% random bridge-preserving removals, creating localized detours.

---

## 2. Empirical Degree Distributions (`figures/baseline_degree_distributions.png`)

### Why This Figure is NOT Useless (The Primary Scientific Proof)
In your thesis or paper defense, a reviewer will ask:
> *"Your hypothesis claims that structural hubs protect greedy spanners from severe stretch compared to hub-free networks. How do you prove that your graphs actually had hubs, and that the other topologies did not, when all four had the exact same average degree ($\bar{d} \approx 4.0$)?"*

**Figure 2 is the mathematical proof that answers this question.** It aggregates all **120,000 nodes** across all 120 generated instances.

### Detailed Breakdown
- **Linear Scale (Left Panel):**
  - For **ER, WS, and Grid**, almost 100% of nodes are tightly packed between degree $k = 2$ and $k = 6$. There are no outliers and no privileged nodes.
  - For **BA**, the distribution is heavily skewed toward low degrees, but extends in an extremely long, thin tail out to $k > 100$.
- **Log-Log Scale (Right Panel — The Hallmark Signature):**
  - **Barabási–Albert (Orange Line):** Forms a **clean, straight downward slope** spanning two orders of magnitude in degree ($k = 2$ to $k = 116$). In statistical physics and graph theory, a straight line on a log-log plot is the unmistakable proof of a **Power-Law Degree Distribution** ($P(k) \propto k^{-\gamma}$). This empirically proves the existence of heavy-tailed super-hubs.
  - **Erdős–Rényi (Red Line):** Forms a parabolic downward bowl centered at $k = 4$. This is the exact signature of a **Poisson distribution** ($P(k) = \frac{\lambda^k e^{-\lambda}}{k!}$), proving pure stochastic randomness with an exponential cutoff (no hubs exceed degree 16).
  - **Watts–Strogatz (Blue Line) & 2D Grid (Green Line):** Form vertical spikes at $k = 4$, confirming uniform local regular degree bounds ($\Delta \le 8$ for WS, $\Delta \le 4$ for Grid).

---

## 3. Clustering vs. Path Length Phase Space (`figures/baseline_clustering_vs_path_length.png`)

### Purpose
Plots every single one of your **120 independent graph instances** in the two-dimensional parameter space of **Average Shortest-Path Length ($L$)** versus **Average Clustering Coefficient ($C$)**.

### Key Observations
1. **Watts–Strogatz (Blue Squares, Top-Left):**
   - High clustering ($C \approx 0.3735$) and short path length ($L \approx 8.80$). It occupies an isolated region, isolating the effect of **triadic closure**.
2. **Barabási–Albert (Orange Circles, Bottom-Left):**
   - Ultra-short paths ($L \approx 4.06$) and low clustering ($C \approx 0.0261$). The central hubs create network-wide expressways.
3. **Erdős–Rényi (Red Triangles, Bottom-Left):**
   - Completely separated from BA with near-zero clustering ($C \approx 0.0036 \approx p$) and slightly longer path lengths ($L \approx 5.37$).
4. **Perturbed 2D Grid (Green Diamonds, Bottom-Right):**
   - Sits in its own extreme corner with zero clustering ($C = 0.0$) and high path length ($L \approx 21.70$). It isolates the effect of **rigid planar distances**.

---

## 4. Spanner Thinning Demonstration Figures

### A. Planar Grid Thinning (`figures/grid_spanner_thinning.png`)
- **What it shows:** A 4-panel progression of `GRID_00` comparing the Original Grid to $t=3$, $t=5$, and $t=7$ greedy spanners.
- **Why it is clear:** Because nodes sit on fixed $(x, y)$ grid coordinates with zero edge crossings, you can visually observe the rectangular wireframe open up as more edges turn into dashed red lines (pruned) while vital structural paths remain solid teal (retained).

### B. Zoomed-In Hub Neighborhood (`figures/ba_zoomed_hub_thinning.png`)
- **What it shows:** Focuses on the single highest-degree hub in `BA_00` (gold center node) and its 35 immediate neighbors.
- **What you observe:** 
  - At $t=3$, almost all radial spoke connections to the hub are preserved.
  - At $t=5$ and $t=7$, peripheral cross-connections are pruned into dashed red, but the radial spoke connections connecting the hub directly to its neighbors remain intact in solid teal.
  - This provides clear micro-level visual proof of the **hub protection phenomenon**: greedy spanners naturally preserve connections to central hubs because hubs provide the shortest routing detour for multiple pairs simultaneously.
