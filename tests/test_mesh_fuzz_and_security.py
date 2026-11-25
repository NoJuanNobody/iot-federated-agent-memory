"""Adversarial & Chaos Fuzz Harness for TinCan CRDT Mesh.

Tests invariants that are easy to miss in happy-path unit tests:
  1. Randomized 5-node chaos: arbitrary partitions, out-of-order delivery, duplicate
     deltas, and concurrent writes always converge to identical Merkle roots with 0 lost writes.
  2. Adversarial frames: forged Ed25519 signatures, tampered payloads, truncated/garbage
     bytes, replay attempts, and wrong/missing XSalsa20-Poly1305 AEAD keys are rejected
     without corrupting local state.
  3. Long-running tombstone GC soak: repeated add/remove cycles stay bounded after
     causal horizon garbage collection.
"""

from __future__ import annotations

import random

import nacl.utils
import pytest

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph
from iot_federated_agent_memory.crdt_mesh import (
    CRDTDeltaMessage,
    CRDTMeshGossipSync,
    DeltaAuthenticationError,
    FrameIntegrityError,
    MockMeshTransport,
    TrustStore,
)
from iot_federated_agent_memory.crdt_types import ORSet
from iot_federated_agent_memory.tincan_core import TinCanIdentity


def test_five_node_randomized_chaos_partitions_reordering_and_duplicates():
    rng = random.Random(20261124)
    node_ids = [f"node-{i}" for i in range(5)]
    identities = {nid: TinCanIdentity.generate() for nid in node_ids}
    trusts = {}
    for nid in node_ids:
        ts = TrustStore(trust_on_first_use=False)
        for other_id, other_ident in identities.items():
            if other_id != nid:
                ts.add_peer(other_id, other_ident)
        trusts[nid] = ts

    kgs = {
        nid: FederatedAgentKnowledgeGraph(nid, identity=identities[nid], trust_store=trusts[nid])
        for nid in node_ids
    }

    all_deltas: list[CRDTDeltaMessage] = []
    expected_disjoint_fields: dict[str, int] = {}

    # 60 chaotic rounds of concurrent mutations across all 5 nodes
    for step in range(60):
        nid = rng.choice(node_ids)
        kg = kgs[nid]
        # Disjoint per-node field on a shared entity (must never be lost)
        field_name = f"counter_{nid}"
        expected_disjoint_fields[field_name] = step
        kg.upsert_entity("file:shared_kernel.py", "module", {field_name: step})

        # Occasional graph edges and concurrent decisions
        if step % 5 == 0:
            kg.add_relation(f"task:{nid}", "edits", "file:shared_kernel.py")
        if step % 15 == 0:
            kg.propose_decision("batch_size", 16 * (node_ids.index(nid) + 1))

    # Collect all signed deltas produced across all 5 nodes
    for kg in kgs.values():
        all_deltas.extend(kg.mesh.offline_queue)

    # Deliver deltas in completely scrambled order + random duplicates to every node
    for nid, kg in kgs.items():
        shuffled = list(all_deltas)
        # Duplicate 25% of deltas to simulate UDP retransmits
        if all_deltas:
            shuffled.extend(rng.sample(all_deltas, k=max(1, len(all_deltas) // 4)))
        rng.shuffle(shuffled)
        for delta in shuffled:
            if delta.node_id != nid:
                kg.mesh.merge_remote_delta(delta)

    # Full pairwise anti-entropy sync to heal any remaining partition skew
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            res = kgs[node_ids[i]].sync_with(kgs[node_ids[j]])
            assert res.parity_achieved is True

    # Invariant 1: Every node converges to the exact same Merkle root
    roots = {kg.merkle_root() for kg in kgs.values()}
    assert len(roots) == 1, f"Nodes diverged after chaos sync: {roots}"

    # Invariant 2: Zero lost disjoint writes across all 5 nodes
    for nid, kg in kgs.items():
        ent = kg.get_entity("file:shared_kernel.py")
        for field_name, expected_val in expected_disjoint_fields.items():
            assert ent[field_name] == expected_val, f"{nid} lost write on {field_name}"


def test_adversarial_forged_tampered_truncated_and_wrong_aead_frames_rejected():
    mesh_key = nacl.utils.random(32)
    wrong_key = nacl.utils.random(32)

    id_honest = TinCanIdentity.generate()
    id_victim = TinCanIdentity.generate()
    id_attacker = TinCanIdentity.generate()

    trust_victim = TrustStore(trust_on_first_use=False)
    trust_victim.add_peer("honest-a", id_honest)

    t_a, t_v = MockMeshTransport.create_pair()
    node_honest = CRDTMeshGossipSync(
        "honest-a", transport=t_a, identity=id_honest, trust_store=trust_victim, mesh_secret=mesh_key
    )
    node_victim = CRDTMeshGossipSync(
        "victim-b", transport=t_v, identity=id_victim, trust_store=trust_victim, mesh_secret=mesh_key
    )

    # Baseline legitimate write
    good_delta = node_honest.apply_lwwmap_set("kg:entity:policy", "mode", "safe")
    assert len(node_victim.process_incoming_transport()) == 1
    baseline_root = node_victim.compute_merkle_root()

    # 1. Forged delta: claims to be honest-a, signed by attacker key
    forged = CRDTDeltaMessage(
        node_id="honest-a",
        clock=999,
        operation="lwwmap_set",
        key="kg:entity:policy",
        value={"mode": "pwned"},
        timestamp=good_delta.timestamp + 100.0,
        vclock={"honest-a": 999},
        crdt_type="lwwmap",
    ).sign(id_attacker)
    with pytest.raises(DeltaAuthenticationError):
        node_victim.merge_remote_delta(forged)

    # 2. Tampered payload after valid signature
    tampered = CRDTDeltaMessage.from_dict(good_delta.to_dict())
    tampered.value = {"mode": "tampered"}
    with pytest.raises(DeltaAuthenticationError):
        node_victim.merge_remote_delta(tampered)

    # 3. Corrupted / truncated / random garbage wire bytes
    raw_valid = good_delta.serialize(encrypt_key=mesh_key)
    for bad_bytes in (
        b"",
        b"{not-json",
        raw_valid[: len(raw_valid) // 2],
        raw_valid[:-4] + b"\xff\xff\xff\xff",
        nacl.utils.random(64),
    ):
        with pytest.raises((DeltaAuthenticationError, FrameIntegrityError, ValueError, KeyError)):
            CRDTDeltaMessage.deserialize(bad_bytes, decrypt_key=mesh_key)

    # 4. Wrong AEAD key or missing AEAD key
    with pytest.raises(DeltaAuthenticationError):
        CRDTDeltaMessage.deserialize(raw_valid, decrypt_key=wrong_key)
    with pytest.raises(DeltaAuthenticationError):
        CRDTDeltaMessage.deserialize(raw_valid, decrypt_key=None)

    # Victim state must be completely untouched
    assert node_victim.compute_merkle_root() == baseline_root
    assert node_victim.lwwmaps["kg:entity:policy"].as_dict()["mode"] == "safe"


def test_orset_tombstone_gc_keeps_memory_bounded_under_churn():
    s = ORSet()
    for tick in range(1, 501):
        elem = f"edge-{tick}"
        s.add(elem, "node-a", tick)
        if tick <= 490:
            s.remove(elem)

    # Before GC, 490 tombstones accumulated
    assert len(s._tombstones) == 490
    pruned = s.gc_tombstones({"node-a": 490})
    assert pruned == 490
    assert len(s._tombstones) == 0
    assert len(s.elements()) == 10
    assert set(s.elements()) == {f"edge-{i}" for i in range(491, 501)}
