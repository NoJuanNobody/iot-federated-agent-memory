from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, CRDTDeltaMessage

def test_crdt_local_and_remote_merge():
    node_a = CRDTMeshGossipSync("node-mac-m1")
    node_b = CRDTMeshGossipSync("node-esp32-cabin")

    delta = node_a.apply_local_update("vault_topic_01", {"status": "synced", "value": 42})
    assert delta.clock == 1
    assert len(delta.get_hash()) == 64

    # Merge into node_b
    merged = node_b.merge_remote_delta(delta)
    assert merged is True
    assert node_b.state_store["vault_topic_01"]["value"] == 42
    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()
