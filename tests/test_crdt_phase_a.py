"""Comprehensive test suite for TinCan Paper Phase A:
- AI-238: VectorClock, HLC, OR-Set, MVRegister, LWWMap + SEC properties
- AI-239: PrefixMerkleTree Dynamo-style anti-entropy & bandwidth reduction vs. full-state sync
- AI-240: Per-node Ed25519 signed deltas, TrustStore verification, tamper & forgery rejection
"""

import pytest

from iot_federated_agent_memory.crdt_mesh import (
    CRDTDeltaMessage,
    CRDTMeshGossipSync,
    DeltaAuthenticationError,
    MockMeshTransport,
    TrustStore,
)
from iot_federated_agent_memory.crdt_types import (
    HLC,
    LWWMap,
    MVRegister,
    ORSet,
    VectorClock,
)
from iot_federated_agent_memory.merkle_tree import PrefixMerkleTree
from iot_federated_agent_memory.tincan_core import TinCanIdentity


# ---------------------------------------------------------------------------
# AI-238: VectorClock, HLC, OR-Set, MVRegister, LWWMap
# ---------------------------------------------------------------------------


def test_vector_clock_causal_and_concurrent_detection():
    vc_a = VectorClock()
    vc_b = VectorClock()

    vc_a.increment("node-a")
    assert vc_a.compare(vc_b) == "after"
    assert vc_b.compare(vc_a) == "before"

    # Concurrent write on node-b without seeing node-a
    vc_b.increment("node-b")
    assert vc_a.compare(vc_b) == "concurrent"
    assert vc_b.compare(vc_a) == "concurrent"

    # Merge resolves causality; subsequent write dominates both
    vc_a.merge(vc_b)
    vc_a.increment("node-a")
    assert vc_a.compare(vc_b) == "after"


def test_hlc_monotonicity_and_total_order():
    hlc_a = HLC("node-a")
    hlc_b = HLC("node-b")

    t1 = hlc_a.tick(now_ms=1_000_000)
    t2 = hlc_a.tick(now_ms=1_000_000)  # same physical ms -> logical increments
    assert t2 > t1
    assert t2.logical == 1

    # Remote receives t2 even if its wall clock is slightly behind
    t3 = hlc_b.receive(t2, now_ms=999_500)
    assert t3 > t2
    assert t3.wall_ms == 1_000_000
    assert t3.logical == 2


def test_orset_add_wins_and_sec_properties():
    # Node A and Node B both start with "entity:auth"
    a = ORSet()
    a.add("entity:auth", "node-a", 1)
    b = ORSet.from_dict(a.to_dict())

    # Partition: Node A removes "entity:auth", Node B concurrently re-adds it
    a.remove("entity:auth")
    assert not a.contains("entity:auth")
    b.add("entity:auth", "node-b", 1)

    # Commutativity & convergence (add-wins)
    ab = ORSet.from_dict(a.to_dict()).merge(b)
    ba = ORSet.from_dict(b.to_dict()).merge(a)
    assert ab.elements() == ["entity:auth"]
    assert ba.elements() == ["entity:auth"]
    assert ab.state_hash() == ba.state_hash()

    # Idempotence
    ab_again = ORSet.from_dict(ab.to_dict()).merge(b)
    assert ab_again.state_hash() == ab.state_hash()


def test_mvregister_preserves_concurrent_siblings_and_resolves():
    node_a = CRDTMeshGossipSync("node-a")
    node_b = CRDTMeshGossipSync("node-b")

    # Concurrent writes to the same MVRegister key during a partition
    node_a.apply_mvregister_set("decision:transport", "udp-multipeer")
    node_b.apply_mvregister_set("decision:transport", "reticulum-rns")

    res = node_a.sync_with_peer(node_b)
    assert res.parity_achieved is True
    assert node_a.mvregisters["decision:transport"].has_conflict() is True
    assert sorted(node_a.mvregisters["decision:transport"].values()) == [
        "reticulum-rns",
        "udp-multipeer",
    ]
    assert node_a.conflicts_detected >= 1

    # A causally dominating write resolves the siblings back to one value
    node_a.apply_mvregister_set("decision:transport", "udp-plus-reticulum")
    res2 = node_a.sync_with_peer(node_b)
    assert res2.parity_achieved is True
    assert node_b.mvregisters["decision:transport"].has_conflict() is False
    assert node_b.mvregisters["decision:transport"].values() == ["udp-plus-reticulum"]


def test_lwwmap_merges_distinct_fields_without_loss():
    node_a = CRDTMeshGossipSync("node-a")
    node_b = CRDTMeshGossipSync("node-b")

    # Concurrent updates to different fields of the same entity
    node_a.apply_lwwmap_set("entity:server_py", "owner", "agent-a")
    node_b.apply_lwwmap_set("entity:server_py", "status", "refactored")

    res = node_a.sync_with_peer(node_b)
    assert res.parity_achieved is True
    expected = {"owner": "agent-a", "status": "refactored"}
    assert node_a.state_store["entity:server_py"] == expected
    assert node_b.state_store["entity:server_py"] == expected


# ---------------------------------------------------------------------------
# AI-239: Real PrefixMerkleTree Dynamo-Style Anti-Entropy
# ---------------------------------------------------------------------------


def test_prefix_merkle_tree_isolates_divergent_keys_with_bandwidth_savings():
    node_a = CRDTMeshGossipSync("node-a", merkle_depth=3)
    node_b = CRDTMeshGossipSync("node-b", merkle_depth=3)

    # Populate 500 identical keys on both nodes
    for i in range(500):
        val = {"idx": i, "summary": f"knowledge graph fact payload #{i} " + ("x" * 64)}
        d = node_a.apply_local_update(f"kg:fact:{i:04d}", val)
        node_b.merge_remote_delta(d)

    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()

    # Mutate only 3 keys while partitioned
    node_a.apply_local_update("kg:fact:0042", {"idx": 42, "summary": "updated by A"})
    node_b.apply_local_update("kg:fact:0317", {"idx": 317, "summary": "updated by B"})
    node_b.apply_local_update("kg:fact:0999", {"idx": 999, "summary": "new on B"})

    assert node_a.compute_merkle_root() != node_b.compute_merkle_root()

    sync_res = node_a.sync_with_peer(node_b)
    assert sync_res.parity_achieved is True
    assert set(sync_res.divergent_keys or []) == {
        "kg:fact:0042",
        "kg:fact:0317",
        "kg:fact:0999",
    }
    assert sync_res.merkle_stats is not None
    # Merkle diff + 3 divergent deltas must use far fewer bytes than full-state sync
    assert sync_res.merkle_stats.merkle_bytes_exchanged < sync_res.merkle_stats.full_state_bytes * 0.25
    assert sync_res.merkle_stats.bandwidth_savings_ratio > 0.75


# ---------------------------------------------------------------------------
# AI-240: Per-Node Ed25519 Signed Deltas & TrustStore Verification
# ---------------------------------------------------------------------------


def test_signed_deltas_verified_and_tampering_or_forgery_rejected():
    id_a = TinCanIdentity.generate()
    id_b = TinCanIdentity.generate()
    id_attacker = TinCanIdentity.generate()

    trust_a = TrustStore(trust_on_first_use=False)
    trust_a.add_peer("node-b", id_b)

    trust_b = TrustStore(trust_on_first_use=False)
    trust_b.add_peer("node-a", id_a)

    chan_a, chan_b = MockMeshTransport.create_pair()
    node_a = CRDTMeshGossipSync("node-a", transport=chan_a, identity=id_a, trust_store=trust_a)
    node_b = CRDTMeshGossipSync("node-b", transport=chan_b, identity=id_b, trust_store=trust_b)

    # 1. Valid signed delta propagates and verifies cleanly
    delta = node_a.apply_local_update("kg:auth_rule", {"rule": "ed25519-only"})
    assert delta.sender_pubkey == id_a.address
    assert delta.signature is not None
    assert delta.verify() is True

    received = node_b.process_incoming_transport()
    assert len(received) == 1
    assert node_b.state_store["kg:auth_rule"] == {"rule": "ed25519-only"}

    # 2. Tampered payload (re-framed with valid CRC32 + SHA-256!) must fail Ed25519 check
    tampered = CRDTDeltaMessage.from_dict(delta.to_dict())
    tampered.value = {"rule": "allow-all-backdoor"}
    tampered.clock = 99
    tampered_frame = tampered.serialize()  # CRC32 & SHA-256 are freshly valid!
    chan_a.send(tampered_frame)

    with pytest.raises(DeltaAuthenticationError, match="Invalid Ed25519 signature"):
        node_b.process_incoming_transport()
    assert node_b.state_store["kg:auth_rule"] == {"rule": "ed25519-only"}
    assert node_b.rejected_deltas == 1

    # 3. Forged delta: attacker claims node_id="node-a" and signs with attacker's key
    forged = CRDTDeltaMessage(
        node_id="node-a",
        clock=100,
        operation="upsert",
        key="kg:auth_rule",
        value={"rule": "forged"},
        timestamp=delta.timestamp + 10.0,
    ).sign(id_attacker)

    with pytest.raises(DeltaAuthenticationError, match="Key mismatch"):
        node_b.merge_remote_delta(forged)

    # 4. Unknown untrusted peer with valid self-signature is rejected in strict TrustStore mode
    rogue = CRDTDeltaMessage(
        node_id="node-rogue",
        clock=1,
        operation="upsert",
        key="kg:poison",
        value={"evil": True},
        timestamp=delta.timestamp + 20.0,
    ).sign(id_attacker)

    with pytest.raises(DeltaAuthenticationError, match="Untrusted peer"):
        node_b.merge_remote_delta(rogue)
    assert "kg:poison" not in node_b.state_store
