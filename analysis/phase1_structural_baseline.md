# Phase 1: Structural Baseline & Topological Validation Report

## 1. Experimental Setup & Controls

To investigate the empirical performance of greedy $t$-spanners, the experiment isolates graph topology while holding network scale ($N = 1,000$) and edge density ($\bar{d} \approx 3.8 - 4.0$) strictly controlled. A total of **120 independent graph instances** (30 instances across 4 topologies) were synthetically generated with guaranteed 1-connectivity.

---

## 2. Table 1: Baseline Structural Profiles

The metrics below represent the empirical mean and standard deviation ($\text{Mean} \pm \text{Std}$) computed across $N = 30$ independent instances for each topological family.

| Topology | $|V|$ | $|E|$ | Avg Degree ($\bar{d}$) | Max Degree ($\Delta$) | Clustering ($C$) | Avg Path ($L$) | Diameter ($D$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Barabási–Albert (BA)** | 1,000 | $1996.0 \pm 0.0$ | $3.99 \pm 0.00$ | $84.1 \pm 13.8$ | $0.0261 \pm 0.0070$ | $4.06 \pm 0.06$ | $7.2 \pm 0.4$ |
| **Erdős–Rényi (ER)** | 1,000 | $2018.8 \pm 37.4$ | $4.04 \pm 0.07$ | $12.1 \pm 1.4$ | $0.0036 \pm 0.0013$ | $5.37 \pm 0.17$ | $25.0 \pm 4.5$ |
| **Perturbed 2D Grid (GRID)**| 1,000 | $1896.0 \pm 0.0$ | $3.79 \pm 0.00$ | $4.0 \pm 0.0$ | $0.0000 \pm 0.0000$ | $21.70 \pm 0.01$ | $63.0 \pm 0.0$ |
| **Watts–Strogatz (WS)** | 1,000 | $2000.0 \pm 0.0$ | $4.00 \pm 0.00$ | $6.7 \pm 0.6$ | $0.3735 \pm 0.0085$ | $8.80 \pm 0.24$ | $17.7 \pm 1.4$ |

---

## 3. Mathematical & Topological Validation (Manipulation Check)

In empirical algorithmics, a manipulation check ensures that generated benchmarks genuinely embody their theoretical archetypes. The empirical results match theoretical expectations across every metric:

### 3.1. Density Control Invariance ($\bar{d} \approx 3.79 - 4.04$)
- **BA ($m=2$):** $|E| = (1000 - 2) \times 2 = 1,996$ edges, yielding $\bar{d} = 3.992$ exactly.
- **WS ($k=4$):** $|E| = 1000 \times 4 / 2 = 2,000$ edges, yielding $\bar{d} = 4.000$ exactly.
- **ER ($p \approx 4/999$ + chain repair):** Expected base edges $\approx 2,000$. The randomized inter-component chain repair adds exactly $c - 1$ bridge edges (where $c$ is the number of disconnected components), yielding $2018.8 \pm 37.4$ edges ($\bar{d} = 4.04 \pm 0.07$).
- **Perturbed 2D Grid ($25 \times 40$):** Base grid has $25(39) + 40(24) = 1,935$ edges ($\bar{d} = 3.87$). Removing exactly 2% (39 edges) without disconnecting the graph leaves $1,896$ edges ($\bar{d} = 3.792$).
- **Significance:** Because edge density is practically identical across all 120 graphs, any empirical variation observed in spanner stretch or edge retention in Phases 2–3 is strictly attributable to **underlying graph geometry**, entirely ruling out density as a confounder.

---

### 3.2. Topology-Specific Structural Signatures

#### A. Barabási–Albert (Scale-Free / Power-Law Hubs)
- **Max Degree ($\Delta = 84.1 \pm 13.8$):** Reflects the preferential attachment mechanism ("rich-get-richer"). The maximum hub degree is over $7\times$ larger than ER and over $20\times$ larger than the grid.
- **Path Length & Diameter ($L = 4.06, D = 7.2$):** Possesses the shortest average path length and smallest diameter of all 4 topologies. The dense core of major hubs acts as high-throughput transit expressways across the entire graph.
- **Hypothesis for Greedy Spanners:** When the greedy spanner considers removing an edge, an alternative path through an adjacent hub of depth $\le t$ is almost guaranteed to exist. BA is expected to tolerate substantial edge pruning with minimal path stretch.

#### B. Watts–Strogatz (Small-World / High Clustering)
- **Clustering Coefficient ($C = 0.3735 \pm 0.0085$):** More than $100\times$ higher than ER ($0.0036$) and $14\times$ higher than BA ($0.0261$). This confirms dense local triadic closure (cliques of friends).
- **Path Length ($L = 8.80$):** Despite strong local clustering, random shortcut rewiring ($p=0.1$) drastically compresses average path length relative to a pure lattice ($L=8.80$ vs $L=21.70$).
- **Degree Uniformity ($\Delta = 6.7 \pm 0.6$):** Degrees remain tightly concentrated around $k=4$, demonstrating a decentralized, hub-free structure.

#### C. Erdős–Rényi (Uniform Random)
- **Clustering Coefficient ($C = 0.0036 \pm 0.0013$):** Closely tracks theoretical random expectation $C \approx p \approx 4/1000 = 0.004$. Absence of triadic closure.
- **Degree Distribution ($\Delta = 12.1 \pm 1.4$):** Follows a classical Poisson distribution. Degree fluctuations are purely stochastic without power-law hubs.
- **Path Length ($L = 5.37, D = 25.0$):** Homogeneous expansion with moderate path lengths.

#### D. Perturbed 2D Grid (Rigid Local Constraints)
- **Zero Clustering ($C = 0.0000$):** A 2D rectangular lattice is bipartite; its shortest cycle is 4 (girth $= 4$). There are zero triangles.
- **Strict Degree Bounds ($\Delta = 4.0 \pm 0.0$):** Interior nodes have degree 4, boundaries 3, and corners 2.
- **High Path Length & Diameter ($L = 21.70 \pm 0.01, D = 63.0 \pm 0.0$):** Over $5\times$ higher average path length and nearly $9\times$ higher diameter than BA.
- **Hypothesis for Greedy Spanners:** Because cycles are long ($\ge 4$) and shortcuts/hubs do not exist, any edge pruned by the spanner forces detours along large perimeters. Grids represent the hardest topological constraint for greedy spanners.

---

## 4. Sampling & Reproducibility Controls

1. **Deterministic Seeds:** Seeds are mapped deterministically per topology (`BA: 1000+i`, `WS: 2000+i`, `ER: 3000+i`, `GRID: 4000+i`).
2. **Static Without-Replacement Node Pairs:** Exactly 1,000 distinct unordered node pairs $\{u, v\}$ ($u < v$) were sampled without replacement from $\binom{1000}{2} = 499,500$ possibilities per instance and serialized to `data/pairs/{GRAPH_ID}_pairs.json`. These identical pair sets will be evaluated across all $t \in \{3, 5, 7\}$ and all 10 randomized permutations.
