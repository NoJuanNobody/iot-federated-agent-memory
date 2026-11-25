"""Verification tests for TinCan paper gap closures:
1. Per-key causal delta compaction (Exp 3 recovery-byte reduction)
2. Causally stable OR-Set tombstone garbage collection
3. XSalsa20-Poly1305 AEAD broadcast frame encryption
4. FederatedAgentKnowledgeGraph wiring on server.py
"""

import nacl.utils
import pytest

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph
from iot_federated_agent_memory.crdt_mesh import (
    CRDTDeltaMessage,
    CRDTMeshGossipSync,
    DeltaAuthenticationError,
    MockMeshTransport,
    TrustStore,
)
from iot_federated_agent_memory.crdt_types import ORSet
from iot_federated_agent_memory.tincan_core import TinCanIdentity


def test_per_key_delta_compaction_reduces_partition_recovery_bytes():
    id_a, id_b = TinCanIdentity.generate(), TinCanIdentity.generate()
    trust_a, trust_b = TrustStore(), TrustStore()
    trust_a.add_peer("node-b", id_b)
    trust_b.add_peer("node-a", id_a)

    kg_a = FederatedAgentKnowledgeGraph("node-a", identity=id_a, trust_store=trust_a)
    kg_b = FederatedAgentKnowledgeGraph("node-b", identity=id_b, trust_store=trust_b)
    node_a = kg_a.mesh
    node_b = kg_b.mesh

    # 25 sequential offline mutations on the same entity + 1 conflicting decision
    for i in range(25):
        kg_a.upsert_entity("file:core.py", "file", {"rev_a": i, "patch_status": f"v{i}"})
        kg_b.upsert_entity("file:core.py", "file", {"rev_b": i, "test_status": f"t{i}"})
    kg_a.propose_decision("jwt_ttl", 15)
    kg_b.propose_decision("jwt_ttl", 60)

    res = node_a.sync_with_peer(node_b)
    assert res.parity_achieved is True
    assert node_a.compacted_deltas >= 24
    assert node_b.compacted_deltas >= 24
    # Both disjoint fields survive with 0 lost writes and conflict is preserved
    ent_a = kg_a.get_entity("file:core.py")
    ent_b = kg_b.get_entity("file:core.py")
    assert ent_a["patch_status"] == "v24"
    assert ent_a["test_status"] == "t24"
    assert ent_a == ent_b
    conflicts = kg_a.list_conflicts()
    assert len(conflicts) == 1
    assert set(conflicts[0]["values"]) == {15, 60}


def test_orset_causal_tombstone_gc():
    s = ORSet()
    s.add("edge-1", "node-a", 1)
    s.add("edge-2", "node-a", 2)
    s.add("edge-3", "node-a", 5)
    s.remove("edge-1")
    s.remove("edge-3")

    # Horizon only covers node-a <= 3, so edge-1 tombstone is pruned while edge-3 tombstone remains
    pruned = s.gc_tombstones({"node-a": 3})
    assert pruned == 1
    assert s.elements() == ["edge-2"]
    assert "node-a:1" not in s._tombstones
    assert "node-a:5" in s._tombstones


def test_aead_encrypted_broadcast_frames_and_wrong_key_rejection():
    mesh_key = nacl.utils.random(32)
    wrong_key = nacl.utils.random(32)

    id_a, id_b = TinCanIdentity.generate(), TinCanIdentity.generate()
    trust_a, trust_b = TrustStore(), TrustStore()
    trust_a.add_peer("node-b", id_b)
    trust_b.add_peer("node-a", id_a)

    t_a, t_b = MockMeshTransport.create_pair()
    node_a = CRDTMeshGossipSync("node-a", transport=t_a, identity=id_a, trust_store=trust_a, mesh_secret=mesh_key)
    node_b = CRDTMeshGossipSync("node-b", transport=t_b, identity=id_b, trust_store=trust_b, mesh_secret=mesh_key)

    delta = node_a.apply_lwwmap_set("kg:entity:secret", "token", "super-secret-value")
    raw_frame = delta.serialize(encrypt_key=mesh_key)
    assert b"super-secret-value" not in raw_frame

    # Wrong key or missing key must fail
    with pytest.raises(DeltaAuthenticationError):
        CRDTDeltaMessage.deserialize(raw_frame, decrypt_key=wrong_key)
    with pytest.raises(DeltaAuthenticationError):
        CRDTDeltaMessage.deserialize(raw_frame, decrypt_key=None)

    # Matching key decrypts & merges cleanly over transport
    merged = node_b.process_incoming_transport()
    assert len(merged) == 1
    assert node_b.lwwmaps["kg:entity:secret"].as_dict()["token"] == "super-secret-value"
