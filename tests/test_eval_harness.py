"""Tests for the reproducible TinCan Paper Evaluation Harness (AI-242)."""

from pathlib import Path

from scripts.eval_mesh_benchmarks import run_all_benchmarks


def test_eval_harness_generates_csvs_charts_and_proves_gains(tmp_path: Path):
    summary = run_all_benchmarks(tmp_path, seed=42)

    # All expected CSVs, JSON summary, and print-ready SVG charts exist
    expected_files = {
        "exp1_scalability.csv",
        "exp2_packet_loss.csv",
        "exp3_partition_conflicts.csv",
        "fig_bytes_vs_nodes.svg",
        "fig_convergence_vs_loss.svg",
        "fig_lost_writes_vs_partition.svg",
        "summary.json",
    }
    assert expected_files.issubset({p.name for p in tmp_path.iterdir()})

    metrics = summary["headline_metrics"]
    # TinCan Merkle-CRDT cuts sync bandwidth dramatically vs. naive full-state gossip
    assert metrics["n25_bandwidth_reduction_pct"] > 50.0
    # Zero silently lost writes for TinCan CRDTs vs. many lost writes on LWW baselines
    assert metrics["partition_lost_writes_tincan"] == 0
    assert metrics["partition_lost_writes_baselines"] > 0
    # Concurrent decision conflicts are explicitly surfaced
    assert metrics["partition_conflicts_detected_tincan"] > 0
