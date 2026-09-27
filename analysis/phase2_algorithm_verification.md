# Phase 2: Algorithm & Permutation Engine Verification Report

This document records the unit tests and verification checks performed on the core greedy $t$-spanner algorithm and permutation engine before running the full 3,600-run experimental pipeline.

---

## 1. Summary of Tests in Plain English

### Test 1: Bounded BFS Accuracy Test
- **What was tested:** Does our custom depth-limited search measure distances accurately and stop exactly when it hits the limit?
- **Result:** We tested on a 6-node line graph ($0 - 1 - 2 - 3 - 4 - 5$). The search confirmed that distance between node 0 and 3 is $\le 3$, but correctly reported "no path" when restricted to a limit of 2 steps. The search works with 100% accuracy.

### Test 2: Theoretical Cycle Test ($C_6$)
- **What was tested:** Does the algorithm know when an edge *must* be kept versus when it can safely be deleted?
- **Result:** Imagine 6 nodes connected in a ring. If any one edge is removed, the detour around the ring requires 5 steps.
  - When allowed stretch is $t = 3$, a 5-step detour is not allowed. The algorithm kept all 6 edges.
  - When allowed stretch is $t = 5$, a 5-step detour is allowed. The algorithm safely pruned 1 edge, leaving 5.
  - This perfectly matches theoretical graph proofs.

### Test 3: Complete Graph Test ($K_6$)
- **What was tested:** Can the algorithm thin out a dense graph down to its bare minimum skeleton?
- **Result:** In a graph where every node is connected to every other node (15 edges total), a $t=3$ spanner only needs a tree of 5 edges to ensure everyone is within 2 hops of each other. The algorithm pruned 10 edges and retained exactly 5.

### Test 4: Correctness Verifier Test
- **What was tested:** Does our verification tool catch broken or invalid spanners?
- **Result:** We intentionally created a broken spanner with missing edges. The verifier caught the error immediately and identified the exact edge that violated the stretch limit.

### Test 5: The 10-Permutation Tie-Breaker Test
- **What was tested:** Does changing the order in which edges are examined produce different edge choices, and are all of them valid?
- **Result:** On a 40-edge grid, shuffling the edge list 10 times produced valid spanners with edge counts varying between 28 and 32 edges:
  `[30, 32, 29, 30, 30, 30, 31, 29, 28, 31]`
  Every single one of the 10 spanners was 100% valid. This proves why edge shuffling is required: a single fixed order would bias the results.

### Test 6: Benchmark on Real Phase 1 Graph (`BA_00`, $N = 1000$)
- **What was tested:** Speed and sparsity on our actual experimental graphs ($N=1000$, $|E|=1996$).
- **Result:**
  - **$t=3$:** Retained 1,820 edges (91.2%) in 0.016 seconds.
  - **$t=5$:** Retained 1,528 edges (76.6%) in 0.060 seconds.
  - **$t=7$:** Retained 1,318 edges (66.0%) in 0.096 seconds.
  - As the allowed stretch $t$ increases, more edges are pruned. Average build time is ~0.06s, meaning all 3,600 spanner runs in Phase 3 will finish in under 5 minutes.
