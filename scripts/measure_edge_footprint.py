#!/usr/bin/env python3
"""Measure real edge runtime footprint for a slim TinCan CRDT + P2P node (AI-244).

Starts two real `FederatedAgentKnowledgeGraph` nodes backed by `MultiPeerUDPTransport`
(loopback AF_INET/SOCK_DGRAM sockets) and `TinCanIdentity` (Ed25519 signed deltas),
runs a 200-key CRDT + PrefixMerkleTree anti-entropy sync workload, and records:
  - Peak & current RSS memory (MB via `resource.getrusage` and `ps`)
  - CPU time (ms) and wall-clock time (ms)
  - Disk footprint (KB) of the slim CRDT + P2P edge module set vs full server/package
  - Real UDP network bytes & packets sent/received + Merkle sync bytes exchanged

Writes structured JSON results to `docs/paper/results/edge_footprint.json`.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph
from iot_federated_agent_memory.crdt_mesh import TrustStore
from iot_federated_agent_memory.p2p_transport import MultiPeerUDPTransport
from iot_federated_agent_memory.tincan_core import TinCanIdentity

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "paper" / "results" / "edge_footprint.json"

SLIM_EDGE_MODULES: Tuple[str, ...] = (
    "iot_federated_agent_memory/crdt_types.py",
    "iot_federated_agent_memory/merkle_tree.py",
    "iot_federated_agent_memory/tincan_core.py",
    "iot_federated_agent_memory/crdt_mesh.py",
    "iot_federated_agent_memory/p2p_transport.py",
    "iot_federated_agent_memory/mdns_discovery.py",
    "iot_federated_agent_memory/agent_kg_crdt.py",
    "local_p2p_mesh.py",
)


def _get_peak_rss_mb() -> float:
    """Return peak RSS of the current process in MiB via resource.getrusage."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # macOS reports ru_maxrss in bytes; Linux reports KiB.
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024.0 * 1024.0)
    return usage.ru_maxrss / 1024.0


def _get_current_rss_mb() -> float:
    """Return current RSS of the current process in MiB via `ps` (fallback: peak RSS)."""
    try:
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(os.getpid())],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        ).strip()
        if out:
            return int(out) / 1024.0
    except Exception:
        pass
    return _get_peak_rss_mb()


def _measure_disk_footprint(repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
    """Measure exact disk size of the slim edge module set vs full repository Python footprint."""
    module_sizes_bytes: Dict[str, int] = {}
    for rel_path in SLIM_EDGE_MODULES:
        full_path = repo_root / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Expected slim edge module not found: {full_path}")
        module_sizes_bytes[rel_path] = full_path.stat().st_size

    slim_total_bytes = sum(module_sizes_bytes.values())

    # Full package + server.py size for comparison
    pkg_dir = repo_root / "iot_federated_agent_memory"
    full_pkg_bytes = sum(p.stat().st_size for p in pkg_dir.glob("*.py"))
    server_py = repo_root / "server.py"
    if server_py.exists():
        full_pkg_bytes += server_py.stat().st_size

    reduction_pct = (
        round((1.0 - (slim_total_bytes / full_pkg_bytes)) * 100.0, 2)
        if full_pkg_bytes > 0
        else 0.0
    )

    return {
        "slim_modules_count": len(SLIM_EDGE_MODULES),
        "slim_modules_bytes": slim_total_bytes,
        "slim_modules_kb": round(slim_total_bytes / 1024.0, 2),
        "full_server_and_package_bytes": full_pkg_bytes,
        "full_server_and_package_kb": round(full_pkg_bytes / 1024.0, 2),
        "code_footprint_reduction_pct": reduction_pct,
        "module_sizes_bytes": module_sizes_bytes,
    }


def _drain_pair(
    kg_a: FederatedAgentKnowledgeGraph,
    kg_b: FederatedAgentKnowledgeGraph,
    max_passes: int = 12,
) -> int:
    """Drain real UDP loopback datagrams between two nodes until both queues are quiet."""
    total_merged = 0
    for _ in range(max_passes):
        m_b = kg_b.process_incoming(ignore_auth_errors=False)
        m_a = kg_a.process_incoming(ignore_auth_errors=False)
        total_merged += m_a + m_b
        if m_a == 0 and m_b == 0:
            time.sleep(0.002)
            m_b2 = kg_b.process_incoming(ignore_auth_errors=False)
            m_a2 = kg_a.process_incoming(ignore_auth_errors=False)
            total_merged += m_a2 + m_b2
            if m_a2 == 0 and m_b2 == 0:
                break
    return total_merged


def measure_edge_footprint(
    num_keys: int = 200,
    output_path: Optional[Path] = DEFAULT_OUTPUT_PATH,
) -> Dict[str, Any]:
    """Run the real 200-key CRDT + Merkle + UDP edge workload and return measured metrics."""
    if num_keys < 20:
        raise ValueError("num_keys must be at least 20")

    disk = _measure_disk_footprint(REPO_ROOT)

    # Reserve 2 keys for entity index + edges OR-Sets and 8 keys for MVRegister decisions.
    num_decisions = 8
    num_entities = num_keys - 2 - num_decisions

    id_a = TinCanIdentity.generate()
    id_b = TinCanIdentity.generate()

    trust_a = TrustStore(trust_on_first_use=False)
    trust_a.add_peer("edge-node-a", id_a)
    trust_a.add_peer("edge-node-b", id_b)

    trust_b = TrustStore(trust_on_first_use=False)
    trust_b.add_peer("edge-node-a", id_a)
    trust_b.add_peer("edge-node-b", id_b)

    transport_a = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0)
    transport_b = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0)
    transport_a.add_peer("edge-node-b", "127.0.0.1", transport_b.bound_port)
    transport_b.add_peer("edge-node-a", "127.0.0.1", transport_a.bound_port)

    kg_a = FederatedAgentKnowledgeGraph(
        agent_id="edge-node-a",
        transport=transport_a,
        identity=id_a,
        trust_store=trust_a,
        require_signatures=True,
        merkle_depth=3,
    )
    kg_b = FederatedAgentKnowledgeGraph(
        agent_id="edge-node-b",
        transport=transport_b,
        identity=id_b,
        trust_store=trust_b,
        require_signatures=True,
        merkle_depth=3,
    )

    try:
        rss_before_mb = _get_current_rss_mb()
        rusage_start = resource.getrusage(resource.RUSAGE_SELF)
        cpu_start = time.process_time()
        wall_start = time.perf_counter()

        # Phase 1: Live UDP replication of entities and relations across loopback sockets
        online_entities = int(num_entities * 0.85)
        for i in range(online_entities):
            eid = f"ent-{i:04d}"
            author = kg_a if (i % 2 == 0) else kg_b
            author.upsert_entity(
                eid,
                "service_module" if (i % 3 == 0) else "agent_fact",
                {
                    "summary": f"edge-record-{i:04d}",
                    "status": "active",
                    "owner": author.agent_id,
                },
            )
            if i > 0 and i % 4 == 0:
                author.add_relation(f"ent-{i - 1:04d}", "depends_on", eid)
            # Periodically drain sockets so OS UDP receive buffers never overflow
            if (i + 1) % 25 == 0:
                _drain_pair(kg_a, kg_b)

        _drain_pair(kg_a, kg_b)

        # Phase 2: Simulated network partition with concurrent offline mutations + MVRegister conflicts
        kg_a.disconnect()
        kg_b.disconnect()

        for i in range(online_entities, num_entities):
            eid = f"ent-{i:04d}"
            if i % 2 == 0:
                kg_a.upsert_entity(eid, "offline_fact", {"summary": f"offline-a-{i:04d}"})
                kg_a.add_relation(eid, "authored_offline_by", "edge-node-a")
            else:
                kg_b.upsert_entity(eid, "offline_fact", {"summary": f"offline-b-{i:04d}"})
                kg_b.add_relation(eid, "authored_offline_by", "edge-node-b")

        for d_idx in range(num_decisions):
            topic = f"policy-{d_idx:02d}"
            kg_a.propose_decision(topic, f"choice-a-{d_idx}")
            if d_idx < 3:
                # Deliberate concurrent conflicting choices on 3 topics
                kg_b.propose_decision(topic, f"choice-b-{d_idx}")

        # Phase 3: Reconnect and run PrefixMerkleTree anti-entropy reconciliation
        kg_a.reconnect()
        kg_b.reconnect()
        _drain_pair(kg_a, kg_b)

        sync_ab = kg_a.sync_with(kg_b)
        sync_ba = kg_b.sync_with(kg_a)
        _drain_pair(kg_a, kg_b)

        wall_end = time.perf_counter()
        cpu_end = time.process_time()
        rusage_end = resource.getrusage(resource.RUSAGE_SELF)
        rss_after_mb = _get_current_rss_mb()
        peak_rss_mb = _get_peak_rss_mb()

        root_a = kg_a.merkle_root()
        root_b = kg_b.merkle_root()
        merkle_parity = root_a == root_b

        total_crdt_keys_a = len(
            set(kg_a.mesh.state_store)
            | set(kg_a.mesh.lwwmaps)
            | set(kg_a.mesh.orsets)
            | set(kg_a.mesh.mvregisters)
        )
        total_crdt_keys_b = len(
            set(kg_b.mesh.state_store)
            | set(kg_b.mesh.lwwmaps)
            | set(kg_b.mesh.orsets)
            | set(kg_b.mesh.mvregisters)
        )
        conflicts_a = len(kg_a.list_conflicts())
        conflicts_b = len(kg_b.list_conflicts())

        merkle_bytes_exchanged = 0
        if sync_ab.merkle_stats:
            merkle_bytes_exchanged += sync_ab.merkle_stats.merkle_bytes_exchanged
        if sync_ba.merkle_stats:
            merkle_bytes_exchanged += sync_ba.merkle_stats.merkle_bytes_exchanged

        net_bytes_sent = transport_a.stats.bytes_sent + transport_b.stats.bytes_sent
        net_bytes_received = transport_a.stats.bytes_received + transport_b.stats.bytes_received
        packets_sent = transport_a.stats.packets_sent + transport_b.stats.packets_sent
        packets_received = transport_a.stats.packets_received + transport_b.stats.packets_received

        user_cpu_ms = (rusage_end.ru_utime - rusage_start.ru_utime) * 1000.0
        sys_cpu_ms = (rusage_end.ru_stime - rusage_start.ru_stime) * 1000.0
        total_cpu_ms = (cpu_end - cpu_start) * 1000.0
        wall_time_ms = (wall_end - wall_start) * 1000.0

        result: Dict[str, Any] = {
            "measured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
            },
            "workload": {
                "target_keys": num_keys,
                "keys_synced_node_a": total_crdt_keys_a,
                "keys_synced_node_b": total_crdt_keys_b,
                "entities_count": len(kg_a.list_entities()),
                "relations_count": len(kg_a.list_relations()),
                "decisions_count": num_decisions,
                "conflicts_detected": max(conflicts_a, conflicts_b),
                "ed25519_signatures_enforced": True,
                "merkle_parity": merkle_parity,
                "merkle_root": root_a,
            },
            "memory": {
                "rss_before_mb": round(rss_before_mb, 3),
                "rss_after_mb": round(rss_after_mb, 3),
                "current_rss_mb": round(rss_after_mb, 3),
                "peak_rss_mb": round(peak_rss_mb, 3),
                "rss_delta_mb": round(max(0.0, rss_after_mb - rss_before_mb), 3),
            },
            "cpu": {
                "cpu_time_ms": round(total_cpu_ms, 3),
                "user_cpu_ms": round(user_cpu_ms, 3),
                "system_cpu_ms": round(sys_cpu_ms, 3),
                "wall_time_ms": round(wall_time_ms, 3),
            },
            "disk": disk,
            "network": {
                "transport": "MultiPeerUDPTransport (AF_INET/SOCK_DGRAM loopback)",
                "network_bytes_sent": net_bytes_sent,
                "network_bytes_received": net_bytes_received,
                "packets_sent": packets_sent,
                "packets_received": packets_received,
                "sar_messages_sent": (
                    transport_a.stats.sar_messages_sent + transport_b.stats.sar_messages_sent
                ),
                "sar_messages_reassembled": (
                    transport_a.stats.sar_messages_reassembled
                    + transport_b.stats.sar_messages_reassembled
                ),
                "merkle_sync_bytes_exchanged": merkle_bytes_exchanged,
                "node_a_bytes_sent": transport_a.stats.bytes_sent,
                "node_a_bytes_received": transport_a.stats.bytes_received,
                "node_b_bytes_sent": transport_b.stats.bytes_sent,
                "node_b_bytes_received": transport_b.stats.bytes_received,
            },
        }
    finally:
        transport_a.close()
        transport_b.close()

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure TinCan slim edge CRDT + P2P node runtime footprint (AI-244)."
    )
    parser.add_argument(
        "--keys",
        type=int,
        default=200,
        help="Total CRDT keys in the knowledge-graph workload (default: 200)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    result = measure_edge_footprint(num_keys=args.keys, output_path=args.output)
    print(
        f"[edge-footprint] keys={result['workload']['keys_synced_node_a']} "
        f"parity={result['workload']['merkle_parity']} "
        f"peak_rss={result['memory']['peak_rss_mb']:.2f}MB "
        f"current_rss={result['memory']['current_rss_mb']:.2f}MB "
        f"cpu={result['cpu']['cpu_time_ms']:.2f}ms "
        f"wall={result['cpu']['wall_time_ms']:.2f}ms "
        f"slim_disk={result['disk']['slim_modules_kb']:.2f}KB "
        f"udp_tx={result['network']['network_bytes_sent']}B "
        f"udp_rx={result['network']['network_bytes_received']}B "
        f"merkle_sync={result['network']['merkle_sync_bytes_exchanged']}B "
        f"-> {args.output}"
    )


if __name__ == "__main__":
    main()
