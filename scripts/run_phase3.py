"""Phase 3 Master Script: The Automated Experiment Pipeline.

Executes:
- 120 Graphs (30 instances x 4 topologies)
- 3 Stretch Limits (t = 3, 5, 7)
- 10 Randomized Edge Permutations per parameter
- Total: 3,600 Greedy Spanner Constructions & Correctness Checks

Controls Applied:
1. Reuses locked static 1,000 node pairs sampled without replacement per graph.
2. Precomputes baseline original distances d_G(u, v) once per graph.
3. Certifies global correctness: d_H(u, v) <= t for all e(u, v) in E_G.
4. Incremental CSV persistence (mode='a') after every single permutation.
5. Resumption capability: skips already-completed runs if interrupted.
"""

import os
import sys
import csv
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import networkx as nx
from tqdm import tqdm

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.profiling import load_pairs
from src.spanner import build_greedy_spanner, generate_edge_permutation
from src.pipeline import compute_pair_distances, evaluate_spanner_run


CSV_PATH = os.path.join("data", "spanner_experiments.csv")
CSV_FIELDS = [
    "graph_id",
    "topology",
    "instance_id",
    "t_limit",
    "permutation_id",
    "original_edges",
    "spanner_edges",
    "edge_retention_ratio",
    "avg_stretch",
    "p95_stretch",
    "median_stretch",
    "max_stretch",
    "avg_additive_delay",
    "exact_max_stretch",
    "failed_pairs_count",
    "is_valid_spanner",
    "build_time_sec"
]


def initialize_csv():
    """Create CSV with headers if it does not already exist."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def get_completed_runs() -> set:
    """Read existing CSV to support interruption recovery / resuming."""
    completed = set()
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            for _, row in df.iterrows():
                completed.add((row["graph_id"], int(row["t_limit"]), int(row["permutation_id"])))
        except Exception:
            pass
    return completed


BACKFILL_CKPT_PATH = os.path.join("data", "spanner_experiments_backfill.csv")


def _load_graph_and_pairs_retry(graph_file: str, pair_file: str):
    """Load graph and static pairs with brief retries for transient file locks."""
    for attempt in range(3):
        try:
            G = nx.read_graphml(graph_file)
            G = nx.convert_node_labels_to_integers(G)
            static_pairs = load_pairs(pair_file)
            return G, static_pairs
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.2)


def _process_single_graph_backfill(task_tuple):
    """Worker computing true pairwise additive delay and exact max stretch for one graph (30 runs)."""
    topo, topo_idx, instance_id, prev_rows = task_tuple
    graph_id = f"{topo}_{instance_id:02d}"
    graph_file = os.path.join("data", "graphs", f"{graph_id}.graphml")
    pair_file = os.path.join("data", "pairs", f"{graph_id}_pairs.json")

    G, static_pairs = _load_graph_and_pairs_retry(graph_file, pair_file)
    cached_orig_distances = compute_pair_distances(G, static_pairs)

    out_rows = []
    for t_val in [3, 5, 7]:
        for p_id in range(10):
            key = (graph_id, t_val, p_id)
            if key not in prev_rows:
                continue
            prev = prev_rows[key]

            seed = 10000 * (topo_idx * 100 + instance_id) + 100 * t_val + p_id
            shuffled_edges = generate_edge_permutation(G, seed=seed)
            H = build_greedy_spanner(G, t=t_val, edge_order=shuffled_edges)

            assert H.number_of_edges() == int(prev["spanner_edges"]), (
                f"Edge count mismatch on {key}: {H.number_of_edges()} vs {prev['spanner_edges']}"
            )

            results = evaluate_spanner_run(
                original_graph=G,
                spanner=H,
                t=t_val,
                static_pairs=static_pairs,
                cached_orig_distances=cached_orig_distances,
                graph_id=graph_id,
                topology=topo,
                instance_id=instance_id,
                permutation_id=p_id,
                build_time=float(prev["build_time_sec"]),
                skip_full_audit=True
            )
            assert abs(results["avg_stretch"] - float(prev["avg_stretch"])) < 1e-4, (
                f"Stretch mismatch on {key}: {results['avg_stretch']} vs {prev['avg_stretch']}"
            )
            out_rows.append(results)

    return graph_id, out_rows


def backfill_missing_columns():
    """Backfill avg_additive_delay and exact_max_stretch in parallel with per-graph checkpointing."""
    if not os.path.exists(CSV_PATH):
        return

    df = pd.read_csv(CSV_PATH)
    if "avg_additive_delay" in df.columns and "exact_max_stretch" in df.columns:
        return

    print("Backfilling avg_additive_delay and exact_max_stretch into existing CSV (multi-core)...")
    existing_map = {}
    for _, row in df.iterrows():
        key = (row["graph_id"], int(row["t_limit"]), int(row["permutation_id"]))
        existing_map[key] = row.to_dict()

    done_graphs = set()
    if os.path.exists(BACKFILL_CKPT_PATH):
        try:
            ckpt_df = pd.read_csv(BACKFILL_CKPT_PATH)
            counts = ckpt_df.groupby("graph_id").size()
            done_graphs = {gid for gid, cnt in counts.items() if cnt == 30}
            if len(ckpt_df) > 0 and len(done_graphs) < len(counts):
                # Keep only complete graphs in checkpoint
                ckpt_df = ckpt_df[ckpt_df["graph_id"].isin(done_graphs)]
                ckpt_df.to_csv(BACKFILL_CKPT_PATH, index=False)
            print(f"Resuming from checkpoint: {len(done_graphs)}/120 graphs already completed.")
        except Exception:
            done_graphs = set()

    if not os.path.exists(BACKFILL_CKPT_PATH) or len(done_graphs) == 0:
        with open(BACKFILL_CKPT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

    topologies = ["BA", "WS", "ER", "GRID"]
    tasks = []
    for topo_idx, topo in enumerate(topologies):
        for i in range(30):
            graph_id = f"{topo}_{i:02d}"
            if graph_id in done_graphs:
                continue
            graph_prev = {
                k: v for k, v in existing_map.items() if k[0] == graph_id
            }
            if graph_prev:
                tasks.append((topo, topo_idx, i, graph_prev))

    if tasks:
        max_workers = min(6, os.cpu_count() or 4)
        pbar = tqdm(total=120, initial=len(done_graphs), desc="Backfilling Graphs (30 runs/graph)")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_process_single_graph_backfill, t_arg) for t_arg in tasks]
            for fut in as_completed(futures):
                graph_id, rows = fut.result()
                with open(BACKFILL_CKPT_PATH, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                    writer.writerows(rows)
                    f.flush()
                pbar.update(1)
        pbar.close()

    # Sort deterministically and replace master CSV
    final_df = pd.read_csv(BACKFILL_CKPT_PATH)
    topo_order = {"BA": 0, "WS": 1, "ER": 2, "GRID": 3}
    final_df["_topo_rank"] = final_df["topology"].map(topo_order)
    final_df = final_df.sort_values(["_topo_rank", "instance_id", "t_limit", "permutation_id"]).drop(columns=["_topo_rank"])
    tmp_path = CSV_PATH + ".tmp"
    final_df[CSV_FIELDS].to_csv(tmp_path, index=False)
    os.replace(tmp_path, CSV_PATH)
    if os.path.exists(BACKFILL_CKPT_PATH):
        os.remove(BACKFILL_CKPT_PATH)
    print(f"Successfully backfilled {len(final_df)} rows -> {CSV_PATH}")


def main():
    print("=" * 80)
    print("PHASE 3: THE AUTOMATED EXPERIMENT PIPELINE")
    print("3,600 Greedy Spanner Constructions (120 Graphs x 3 t-limits x 10 Permutations)")
    print("=" * 80)

    initialize_csv()
    backfill_missing_columns()
    completed_runs = get_completed_runs()
    print(f"Existing runs detected in CSV: {len(completed_runs)}/3600")

    topologies = ["BA", "WS", "ER", "GRID"]
    num_instances = 30
    t_values = [3, 5, 7]
    num_permutations = 10

    total_tasks = len(topologies) * num_instances * len(t_values) * num_permutations
    remaining_tasks = total_tasks - len(completed_runs)

    if remaining_tasks == 0:
        print("All 3,600 runs have already been completed!")
        print_summary_table()
        return

    print(f"Remaining runs to execute: {remaining_tasks}/{total_tasks}")
    start_time = time.time()

    pbar = tqdm(total=total_tasks, initial=len(completed_runs), desc="Phase 3 Progress")

    for topo in topologies:
        for i in range(num_instances):
            graph_id = f"{topo}_{i:02d}"
            graph_file = os.path.join("data", "graphs", f"{graph_id}.graphml")
            pair_file = os.path.join("data", "pairs", f"{graph_id}_pairs.json")

            if not os.path.exists(graph_file) or not os.path.exists(pair_file):
                print(f"Warning: Skipping {graph_id}, files not found.")
                continue

            # Load Graph
            G = nx.read_graphml(graph_file)
            G = nx.convert_node_labels_to_integers(G)

            # Load locked static 1,000 pairs
            static_pairs = load_pairs(pair_file)

            # Precompute baseline shortest paths in G once for these 1,000 pairs
            cached_orig_distances = compute_pair_distances(G, static_pairs)

            for t_val in t_values:
                for p_id in range(num_permutations):
                    run_key = (graph_id, t_val, p_id)
                    if run_key in completed_runs:
                        continue

                    # Seed for edge permutation: unique and deterministic per (graph, t, perm)
                    seed = 10000 * (topologies.index(topo) * 100 + i) + 100 * t_val + p_id
                    shuffled_edges = generate_edge_permutation(G, seed=seed)

                    # Build greedy spanner
                    t0 = time.time()
                    H = build_greedy_spanner(G, t=t_val, edge_order=shuffled_edges)
                    build_time = time.time() - t0

                    # Evaluate metrics (correctness check + 1,000 pair stretch)
                    results = evaluate_spanner_run(
                        original_graph=G,
                        spanner=H,
                        t=t_val,
                        static_pairs=static_pairs,
                        cached_orig_distances=cached_orig_distances,
                        graph_id=graph_id,
                        topology=topo,
                        instance_id=i,
                        permutation_id=p_id,
                        build_time=build_time
                    )

                    # Incremental CSV append (mode='a')
                    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                        writer.writerow(results)

                    completed_runs.add(run_key)
                    pbar.update(1)

    pbar.close()
    elapsed = time.time() - start_time
    print(f"\nAll spanner runs completed in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes).")
    print(f"Master empirical dataset saved to: {CSV_PATH}\n")

    print_summary_table()


def print_summary_table():
    """Print high-level aggregated summary of spanner performance across topologies."""
    if not os.path.exists(CSV_PATH):
        return

    df = pd.read_csv(CSV_PATH)
    print("=" * 80)
    print("PRELIMINARY EXPERIMENTAL SUMMARY (Mean across all runs)")
    print("=" * 80)

    summary = df.groupby(["topology", "t_limit"]).agg(
        Runs=("permutation_id", "count"),
        Retention=("edge_retention_ratio", "mean"),
        AvgStretch=("avg_stretch", "mean"),
        P95Stretch=("p95_stretch", "mean"),
        MaxStretch=("max_stretch", "mean")
    ).reset_index()

    formatted = []
    for _, row in summary.iterrows():
        formatted.append({
            "Topology": row["topology"],
            "t": int(row["t_limit"]),
            "Runs": int(row["Runs"]),
            "Edge Retention": f"{row['Retention'] * 100:.1f}%",
            "Avg Stretch": f"{row['AvgStretch']:.4f}",
            "95th-Pctl Stretch": f"{row['P95Stretch']:.4f}",
            "Max Stretch": f"{row['MaxStretch']:.2f}"
        })

    summary_df = pd.DataFrame(formatted)
    print(summary_df.to_string(index=False))
    print("=" * 80)


if __name__ == "__main__":
    main()
