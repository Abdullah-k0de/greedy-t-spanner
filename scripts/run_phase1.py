"""Phase 1 Master Script: Controlled Generation & Structural Profiling.

Executes:
1. Generates 30 independent instances for 4 topologies (BA, WS, ER, Grid).
2. Performs structural profiling (nodes, edges, d_bar, Delta, C, L, diameter).
3. Samples 1,000 static unordered node pairs without replacement for each instance.
4. Serializes all graphs to data/graphs/ and pair sets to data/pairs/.
5. Exports baseline metrics to data/baseline_metrics.csv and displays statistical summary.
"""

import os
import csv
import time
import pandas as pd
import networkx as nx
from tqdm import tqdm

from src.generators import (
    generate_barabasi_albert,
    generate_watts_strogatz,
    generate_erdos_renyi_repaired,
    generate_perturbed_grid,
)
from src.profiling import (
    compute_baseline_metrics,
    sample_static_pairs,
    save_pairs,
)


def ensure_directories():
    """Create data directories if they do not exist."""
    os.makedirs("data/graphs", exist_ok=True)
    os.makedirs("data/pairs", exist_ok=True)


def main():
    print("=" * 80)
    print("PHASE 1: CONTROLLED GRAPH GENERATION & STRUCTURAL PROFILING")
    print("=" * 80)

    ensure_directories()

    csv_path = os.path.join("data", "baseline_metrics.csv")
    csv_headers = [
        "graph_id",
        "topology",
        "instance_id",
        "nodes",
        "edges",
        "avg_degree",
        "max_degree",
        "clustering_coefficient",
        "avg_shortest_path_length",
        "diameter",
        "is_connected"
    ]

    # Initialize CSV with header
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

    topologies = [
        ("BA", generate_barabasi_albert, 1000),
        ("WS", generate_watts_strogatz, 2000),
        ("ER", generate_erdos_renyi_repaired, 3000),
        ("GRID", generate_perturbed_grid, 4000),
    ]

    num_instances = 30
    total_graphs = len(topologies) * num_instances
    global_pair_seed_base = 5000

    print(f"Generating {total_graphs} graphs ({num_instances} instances x 4 topologies)...")
    start_time = time.time()

    all_metrics = []
    pbar = tqdm(total=total_graphs, desc="Phase 1 Progress")

    for topo_name, generator_fn, seed_base in topologies:
        for i in range(num_instances):
            instance_seed = seed_base + i
            pair_seed = global_pair_seed_base + (seed_base // 10) + i
            graph_id = f"{topo_name}_{i:02d}"

            # 1. Generate graph with strict controls
            G = generator_fn(seed=instance_seed)

            # Ensure all node labels are integers
            G = nx.convert_node_labels_to_integers(G)

            # 2. Structural Profiling
            metrics = compute_baseline_metrics(
                graph=G,
                graph_id=graph_id,
                topology=topo_name,
                instance_id=i
            )
            all_metrics.append(metrics)

            # Incremental CSV append
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csv_headers)
                writer.writerow(metrics)

            # 3. Static Pair Sampling (1,000 distinct pairs without replacement)
            pairs = sample_static_pairs(G, num_pairs=1000, seed=pair_seed)
            pair_file = os.path.join("data", "pairs", f"{graph_id}_pairs.json")
            save_pairs(pairs, pair_file)

            # 4. Save GraphML for Phase 2/3
            graph_file = os.path.join("data", "graphs", f"{graph_id}.graphml")
            nx.write_graphml(G, graph_file)

            pbar.update(1)

    pbar.close()
    elapsed = time.time() - start_time
    print(f"\nSuccessfully generated and profiled {total_graphs} graphs in {elapsed:.2f} seconds.")
    print(f"Baseline metrics saved to: {csv_path}\n")

    # Display Publication-Ready Table 1
    df = pd.DataFrame(all_metrics)
    print("=" * 80)
    print("TABLE 1: BASELINE STRUCTURAL PROFILES (Mean ± Std over N=30 instances)")
    print("=" * 80)

    summary = df.groupby("topology").agg(
        Nodes=("nodes", "mean"),
        Edges_mean=("edges", "mean"),
        Edges_std=("edges", "std"),
        AvgDeg_mean=("avg_degree", "mean"),
        AvgDeg_std=("avg_degree", "std"),
        MaxDeg_mean=("max_degree", "mean"),
        MaxDeg_std=("max_degree", "std"),
        Clustering_mean=("clustering_coefficient", "mean"),
        Clustering_std=("clustering_coefficient", "std"),
        AvgPath_mean=("avg_shortest_path_length", "mean"),
        AvgPath_std=("avg_shortest_path_length", "std"),
        Diameter_mean=("diameter", "mean"),
        Diameter_std=("diameter", "std")
    ).reset_index()

    formatted_rows = []
    for _, row in summary.iterrows():
        formatted_rows.append({
            "Topology": row["topology"],
            "|V|": int(row["Nodes"]),
            "|E|": f"{row['Edges_mean']:.1f} ± {row['Edges_std']:.1f}",
            "Avg Degree (d_bar)": f"{row['AvgDeg_mean']:.2f} ± {row['AvgDeg_std']:.2f}",
            "Max Degree (Δ)": f"{row['MaxDeg_mean']:.1f} ± {row['MaxDeg_std']:.1f}",
            "Clustering (C)": f"{row['Clustering_mean']:.4f} ± {row['Clustering_std']:.4f}",
            "Avg Path (L)": f"{row['AvgPath_mean']:.2f} ± {row['AvgPath_std']:.2f}",
            "Diameter (D)": f"{row['Diameter_mean']:.1f} ± {row['Diameter_std']:.1f}"
        })

    summary_df = pd.DataFrame(formatted_rows)
    print(summary_df.to_string(index=False))
    print("=" * 80)


if __name__ == "__main__":
    main()
