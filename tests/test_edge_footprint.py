"""Tests for TinCan slim edge footprint measurement & Dockerfile.edge (AI-244)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.measure_edge_footprint import SLIM_EDGE_MODULES, measure_edge_footprint

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_measure_edge_footprint_function(tmp_path: Path) -> None:
    out_file = tmp_path / "edge_footprint.json"
    result = measure_edge_footprint(num_keys=200, output_path=out_file)

    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded == result

    # Workload verification
    wl = loaded["workload"]
    assert wl["target_keys"] == 200
    assert wl["keys_synced_node_a"] >= 200
    assert wl["keys_synced_node_b"] == wl["keys_synced_node_a"]
    assert wl["merkle_parity"] is True
    assert wl["ed25519_signatures_enforced"] is True
    assert wl["conflicts_detected"] >= 1
    assert isinstance(wl["merkle_root"], str) and len(wl["merkle_root"]) == 64

    # Positive memory metrics
    mem = loaded["memory"]
    assert mem["peak_rss_mb"] > 0
    assert mem["current_rss_mb"] > 0
    assert mem["rss_before_mb"] > 0
    assert mem["rss_after_mb"] > 0

    # Positive CPU metrics
    cpu = loaded["cpu"]
    assert cpu["cpu_time_ms"] > 0
    assert cpu["wall_time_ms"] > 0

    # Positive disk metrics
    disk = loaded["disk"]
    assert disk["slim_modules_count"] == len(SLIM_EDGE_MODULES)
    assert disk["slim_modules_bytes"] > 0
    assert disk["slim_modules_kb"] > 0
    assert disk["code_footprint_reduction_pct"] > 50.0
    for mod in SLIM_EDGE_MODULES:
        assert disk["module_sizes_bytes"][mod] > 0

    # Positive real UDP network metrics
    net = loaded["network"]
    assert net["network_bytes_sent"] > 0
    assert net["network_bytes_received"] > 0
    assert net["packets_sent"] > 0
    assert net["packets_received"] > 0
    assert net["merkle_sync_bytes_exchanged"] > 0


def test_measure_edge_footprint_cli_execution(tmp_path: Path) -> None:
    out_file = tmp_path / "cli_edge_footprint.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "measure_edge_footprint.py"),
            "--keys",
            "200",
            "--output",
            str(out_file),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert "[edge-footprint]" in proc.stdout
    assert out_file.exists()

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["workload"]["merkle_parity"] is True
    assert data["memory"]["peak_rss_mb"] > 0
    assert data["cpu"]["cpu_time_ms"] > 0
    assert data["disk"]["slim_modules_kb"] > 0
    assert data["network"]["network_bytes_sent"] > 0
    assert data["network"]["network_bytes_received"] > 0


def test_dockerfile_edge_is_minimal_and_valid() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile.edge").read_text(encoding="utf-8")
    active_lines = "\n".join(
        line for line in dockerfile.splitlines() if not line.lstrip().startswith("#")
    )

    assert "python:3.11-slim" in active_lines
    assert "PyNaCl" in active_lines
    assert "zeroconf" in active_lines
    assert "local_p2p_mesh.py" in active_lines
    assert "ENTRYPOINT" in active_lines

    # Ensure zero dev toolchain or server/WebAuthn bloat in active Dockerfile instructions
    for forbidden in ("build-essential", "playwright", "webauthn", "server.py", "linuxbrew", "rustup"):
        assert forbidden not in active_lines


def test_slim_edge_module_set_imports_in_isolation(tmp_path: Path) -> None:
    """Verify the exact Dockerfile.edge module subset executes without server/UI modules."""
    import shutil

    pkg_dir = tmp_path / "iot_federated_agent_memory"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text('"""Slim edge package."""\n', encoding="utf-8")
    for rel_path in SLIM_EDGE_MODULES:
        src = REPO_ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(tmp_path / "local_p2p_mesh.py"), "--help"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    assert "Start Decentralized Local P2P CRDT Mesh Node" in proc.stdout
