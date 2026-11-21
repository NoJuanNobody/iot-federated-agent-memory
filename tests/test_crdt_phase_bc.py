"""Tests for TinCan Paper Phase B & Phase C:
- AI-236: Real MultiPeerUDPTransport (multi-peer fan-out, SAR chunking/reassembly) + Reticulum adapter
- AI-237: DecentralizedPeerDiscovery (multicast LAN discovery, peer join/drop/rejoin)
- AI-241: FederatedAgentKnowledgeGraph on CRDT mesh + end-to-end pair-programming demo
"""

import time
import pytest

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph
from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, TrustStore
from iot_federated_agent_memory.mdns_discovery import (
    DecentralizedPeerDiscovery,
    PeerAnnouncement,
    detect_lan_ip,
)
from iot_federated_agent_memory.p2p_transport import (
    MultiPeerUDPTransport,
    ReticulumTransportChannel,
)
from iot_federated_agent_memory.tincan_core import TinCanIdentity
from scripts.demo_pair_programming_mesh import run_demo


# ---------------------------------------------------------------------------
# AI-236: Real Multi-Peer UDP Transport + SAR + Reticulum Adapter
# ---------------------------------------------------------------------------


def test_multipeer_udp_fanout_and_sar_reassembly():
    udp_a = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0, mtu=300)
    udp_b = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0, mtu=300)
    udp_c = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0, mtu=300)

    try:
        udp_a.add_peer("node-b", "127.0.0.1", udp_b.bound_port)
        udp_a.add_peer("node-c", "127.0.0.1", udp_c.bound_port)

        node_a = CRDTMeshGossipSync("node-a", transport=udp_a)
        node_b = CRDTMeshGossipSync("node-b", transport=udp_b)
        node_c = CRDTMeshGossipSync("node-c", transport=udp_c)

        # Large payload (>1,500 bytes) forces SAR segmentation across >5 UDP datagrams
        large_blob = "disaster-mesh-context-" * 80
        node_a.apply_local_update("kg:large_context", {"blob": large_blob})

        time.sleep(0.05)
        recv_b = node_b.process_incoming_transport()
        recv_c = node_c.process_incoming_transport()

        assert len(recv_b) == 1
        assert len(recv_c) == 1
        assert node_b.state_store["kg:large_context"]["blob"] == large_blob
        assert node_c.state_store["kg:large_context"]["blob"] == large_blob
        assert node_a.compute_merkle_root() == node_b.compute_merkle_root() == node_c.compute_merkle_root()
        assert udp_a.stats.sar_messages_sent >= 1
        assert udp_b.stats.sar_messages_reassembled >= 1
        assert udp_c.stats.sar_messages_reassembled >= 1
    finally:
        udp_a.close()
        udp_b.close()
        udp_c.close()


def test_reticulum_adapter_interface():
    delivered = []
    rns_b = ReticulumTransportChannel(send_fn=lambda data: True)
    rns_a = ReticulumTransportChannel(send_fn=lambda data: (delivered.append(data), rns_b.inject_packet(data), True)[-1])

    node_a = CRDTMeshGossipSync("lora-node-a", transport=rns_a)
    node_b = CRDTMeshGossipSync("lora-node-b", transport=rns_b)

    node_a.apply_local_update("sos:beacon", {"lat": 26.37, "lon": -80.10})
    assert len(delivered) == 1
    merged = node_b.process_incoming_transport()
    assert len(merged) == 1
    assert node_b.state_store["sos:beacon"]["lat"] == 26.37


# ---------------------------------------------------------------------------
# AI-237: Decentralized Peer Discovery (Join, Drop, Rejoin)
# ---------------------------------------------------------------------------


def test_decentralized_multicast_discovery_join_drop_rejoin():
    assert isinstance(detect_lan_ip(), str)

    discovered_a: list[str] = []
    lost_a: list[str] = []
    rejoined_a: list[str] = []

    mcast_port = 55354
    disc_a = DecentralizedPeerDiscovery(
        node_id="node-alpha",
        mesh_port=41001,
        advertise_host="127.0.0.1",
        backend="multicast",
        mcast_port=mcast_port,
        beacon_interval_s=0.1,
        peer_ttl_s=0.6,
        on_peer_discovered=lambda p: discovered_a.append(p.node_id),
        on_peer_lost=lambda nid: lost_a.append(nid),
        on_peer_rejoined=lambda p: rejoined_a.append(p.node_id),
    )
    disc_b = DecentralizedPeerDiscovery(
        node_id="node-beta",
        mesh_port=41002,
        advertise_host="127.0.0.1",
        backend="multicast",
        mcast_port=mcast_port,
        beacon_interval_s=0.1,
        peer_ttl_s=0.6,
    )

    try:
        disc_a.start()
        disc_b.start()

        # Wait up to 2s for automatic discovery
        deadline = time.monotonic() + 2.0
        while "node-beta" not in discovered_a and time.monotonic() < deadline:
            time.sleep(0.05)

        assert "node-beta" in discovered_a
        assert "node-beta" in disc_a.active_peers()

        # Peer B drops cleanly (sends bye)
        disc_b.stop()
        deadline = time.monotonic() + 2.0
        while "node-beta" not in lost_a and time.monotonic() < deadline:
            time.sleep(0.05)
        assert "node-beta" in lost_a
        assert "node-beta" not in disc_a.active_peers()

        # Peer B rejoins -> triggers on_peer_rejoined
        disc_b.start()
        deadline = time.monotonic() + 2.0
        while "node-beta" not in rejoined_a and time.monotonic() < deadline:
            time.sleep(0.05)
        assert "node-beta" in rejoined_a
        assert "node-beta" in disc_a.active_peers()
    finally:
        disc_b.stop()
        disc_a.stop()


# ---------------------------------------------------------------------------
# AI-241: Federated Agent Knowledge Graph on CRDT Mesh + End-to-End Demo
# ---------------------------------------------------------------------------


def test_federated_agent_knowledge_graph_end_to_end_demo():
    result = run_demo()

    assert result["diverged_during_partition"] is True
    assert result["parity_after_heal"] is True
    assert result["final_parity"] is True

    # Both concurrent entity fields survived on file:auth.py!
    merged_auth = result["merged_auth_entity"]
    assert merged_auth["patch_status"] == "refresh_lock_added"
    assert merged_auth["test_status"] == "regression_test_added"

    # All 3 relations from both agents survived!
    assert result["relations_count"] == 3

    # Concurrent conflicting decision on jwt_ttl_minutes was detected before resolution
    assert len(result["conflicts_detected"]) == 1
    assert sorted(result["conflicts_detected"][0]["values"]) == [15, 60]

    # After resolution, both agents hold single value 30
    assert result["resolved_decision"]["conflict"] is False
    assert result["resolved_decision"]["values"] == [30]
    assert result["udp_bytes_sent"] > 0
