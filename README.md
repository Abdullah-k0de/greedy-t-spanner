# Empirical Evaluation of Greedy $t$-Spanners

An experimental evaluation of multiplicative greedy $t$-spanner algorithms across canonical graph topologies (Barabási–Albert, Watts–Strogatz, Erdős–Rényi, and 2D Planar Grids) under controlled scale ($N = 1,000$) and baseline edge density ($\bar{d} \approx 3.8\text{–}4.0$).

This repository contains the complete experimental pipeline, reproducible statistical verification suite, publication figure generators, and IEEE conference manuscript.

---

## Repository Structure

```text
├── src/                        # Core algorithmic framework
│   ├── generators.py           # Controlled synthetic network generators
│   ├── spanner.py              # Greedy t-spanner constructor & bounded BFS
│   ├── profiling.py            # Baseline structural profiling (C, L, D, Delta)
│   └── pipeline.py             # Pairwise distance, stretch, and invariant evaluation engine
├── scripts/                    # Automated experiments & figure generators
│   ├── run_phase1.py           # Baseline topology generation & profiling
│   ├── run_phase3.py           # 3,600 spanner experimental pipeline execution
│   ├── run_phase4_analysis.py  # Statistical aggregation & hypothesis testing
│   ├── run_proposal_extensions.py # Delay duality & runtime metrics
│   ├── generate_fig3_point_range.py # IEEE Fig. 3 point-and-range distributions
│   ├── generate_ieee_figures.py# IEEE publication figures
│   └── verify_statistical_questions.py # Formal 45-test statistical validation
├── visualize/                  # Network layout & edge-thinning visualizations
│   ├── visualize_structural_baselines.py
│   ├── visualize_ba00.py
│   └── visualize_spanner_thinning.py
├── tests/                      # Algorithmic invariant & correctness test suite
│   └── test_spanner.py
├── data/                       # Experimental CSV datasets
│   ├── baseline_metrics.csv
│   ├── spanner_experiments.csv
│   ├── nested_aggregated_metrics.csv
│   ├── proposal_extensions_metrics.csv
│   └── final_publication_table2.csv
├── figures/                    # Publication charts and topology diagrams
├── main.tex                    # IEEE formatted conference manuscript
├── requirements.txt            # Pinned Python package dependencies
└── .gitignore                  # Environment and build exclusion rules
```

---

## Experimental Setup & Methodology

The study evaluates the greedy $t$-spanner algorithm across four distinct structural regimes:
1. **Scale-Free / Heavy-Tailed (Barabási–Albert):** Preferential attachment ($m = 2$), pronounced degree hubs ($\Delta = 84.1 \pm 13.8$), and ultra-short path lengths ($L = 4.06$).
2. **Small-World / High-Clustering (Watts–Strogatz):** Dense local triadic closure ($C = 0.3735 \pm 0.0085$) with short global shortcuts ($k = 4, p = 0.10$).
3. **Homogeneous Random (Erdős–Rényi):** Uniform connection probability ($p \approx 4/999$) with randomized bridge-preserving connectivity repair.
4. **Planar Lattice (Perturbed 2D Grid):** $25 \times 40$ bipartite coordinate lattice ($C = 0$) with uniform degree ($\Delta = 4.0$) and long diameter ($D = 63.0$).

For each topology, $n = 30$ independent baseline instances are generated ($120$ graphs total). For each graph, greedy $t$-spanners are constructed across stretch factors $t \in \{3, 5, 7\}$ over $10$ independent random edge permutations, yielding **3,600 evaluated spanners** and **3.6 million sampled vertex-pair shortest-path queries** ($M = 1,000$ static pairs per graph), alongside exact edge-level worst-case stretch verification.

---

## Requirements & Environment

Python 3.12+ with pinned dependencies in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Reproducing the Results

### 1. Run Unit & Invariant Tests
```bash
pytest tests/test_spanner.py -v
```

### 2. Generate Baseline Topologies & Profiles
```bash
python scripts/run_phase1.py
```

### 3. Run the Spanner Construction Pipeline (3,600 Runs)
```bash
python scripts/run_phase3.py
```

### 4. Run Statistical Analysis & Nested Aggregation
```bash
python scripts/run_phase4_analysis.py
python scripts/run_proposal_extensions.py
python scripts/verify_statistical_questions.py
```

### 5. Generate IEEE Publication Figures
```bash
python scripts/generate_fig3_point_range.py
python scripts/generate_ieee_figures.py
```

---

## Invariant Guarantees

All generated spanners satisfy:
- **Multiplicative Stretch Bound:** $d_H(u, v) \le t \cdot d_G(u, v)$ for all $(u, v) \in E_G$.
- **Exact Worst-Case Stretch Tightness:** $s_{\max}^{\mathrm{exact}} = \max_{(u,v) \in E_G} d_H(u,v) = t$ across all $3,600$ constructed spanners (exact edge-level bound slack $= 0.00$).
- **Global 1-Connectivity:** $0$ disconnected vertex pairs across all $3.6 \times 10^6$ evaluated queries.
