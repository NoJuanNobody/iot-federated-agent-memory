#!/usr/bin/env python3
"""End-to-End Federated Agent Pair-Programming Demo over Real UDP CRDT Mesh (AI-241).

Demonstrates the TinCan paper's core claim:
Two autonomous coding agents (`agent-mac-backend` and `agent-pi-tests`) share a
CRDT knowledge graph of entities, relations, and architectural decisions over real
UDP sockets with Ed25519 signed deltas, survive a network partition with concurrent
edits, and converge to identical Merkle roots with zero lost writes.
"""

import json
import time

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph
from iot_federated_agent_memory.crdt_mesh import TrustStore
from iot_federated_agent_memory.p2p_transport import MultiPeerUDPTransport
from iot_federated_agent_memory.tincan_core import TinCanIdentity


def run_demo() -> dict:
    # 1. Provision independent Ed25519 identities and mutual TrustStores
    id_a = TinCanIdentity.generate()
    id_b = TinCanIdentity.generate()

    trust_a = TrustStore(trust_on_first_use=False)
    trust_a.add_peer("agent-pi-tests", id_b)
    trust_b = TrustStore(trust_on_first_use=False)
    trust_b.add_peer("agent-mac-backend", id_a)

    # 2. Bind real UDP sockets (loopback here; works identically across LAN IPs)
    udp_a = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0)
    udp_b = MultiPeerUDPTransport(bind_host="127.0.0.1", bind_port=0)
    udp_a.add_peer("agent-pi-tests", "127.0.0.1", udp_b.bound_port)
    udp_b.add_peer("agent-mac-backend", "127.0.0.1", udp_a.bound_port)

    kg_a = FederatedAgentKnowledgeGraph("agent-mac-backend", transport=udp_a, identity=id_a, trust_store=trust_a)
    kg_b = FederatedAgentKnowledgeGraph("agent-pi-tests", transport=udp_b, identity=id_b, trust_store=trust_b)

    try:
        # 3. Initial synced task state
        kg_a.upsert_entity("task:auth-refresh", "task", {"title": "Fix JWT refresh race", "status": "in_progress"})
        kg_a.upsert_entity("file:auth.py", "module", {"path": "src/auth.py", "owner": "agent-mac-backend"})
        kg_a.add_relation("task:auth-refresh", "touches", "file:auth.py")

        time.sleep(0.05)
        kg_b.process_incoming()
        assert kg_a.merkle_root() == kg_b.merkle_root()

        # 4. Simulate disaster / LAN partition
        kg_a.disconnect()
        kg_b.disconnect()

        # Agent A works offline on backend implementation
        kg_a.update_entity_field("file:auth.py", "patch_status", "refresh_lock_added")
        kg_a.upsert_entity("file:token_store.py", "module", {"path": "src/token_store.py"})
        kg_a.add_relation("file:auth.py", "calls", "file:token_store.py")
        kg_a.propose_decision("jwt_ttl_minutes", 15)

        # Agent B concurrently works offline on test suite & discovers a failing edge case
        kg_b.update_entity_field("file:auth.py", "test_status", "regression_test_added")
        kg_b.upsert_entity("file:test_auth.py", "test", {"path": "tests/test_auth.py", "passing": True})
        kg_b.add_relation("file:test_auth.py", "verifies", "file:auth.py")
        kg_b.propose_decision("jwt_ttl_minutes", 60)

        diverged = kg_a.merkle_root() != kg_b.merkle_root()

        # 5. Partition heals: flush offline queues over real UDP + Merkle anti-entropy
        kg_a.reconnect()
        kg_b.reconnect()
        time.sleep(0.05)
        kg_a.process_incoming()
        kg_b.process_incoming()
        sync_res = kg_a.sync_with(kg_b)

        # Verify conflict was surfaced rather than silently dropped
        conflicts_before_resolution = kg_a.list_conflicts()

        # 6. Agent A resolves the concurrent TTL decision -> propagates over UDP
        kg_a.propose_decision("jwt_ttl_minutes", 30)
        time.sleep(0.05)
        kg_b.process_incoming()

        return {
            "diverged_during_partition": diverged,
            "parity_after_heal": sync_res.parity_achieved,
            "final_parity": kg_a.merkle_root() == kg_b.merkle_root(),
            "final_merkle_root": kg_a.merkle_root(),
            "merged_auth_entity": kg_b.get_entity("file:auth.py"),
            "relations_count": len(kg_b.list_relations()),
            "conflicts_detected": conflicts_before_resolution,
            "resolved_decision": kg_b.get_decision("jwt_ttl_minutes"),
            "udp_bytes_sent": udp_a.stats.bytes_sent + udp_b.stats.bytes_sent,
        }
    finally:
        udp_a.close()
        udp_b.close()


if __name__ == "__main__":
    result = run_demo()
    print(json.dumps(result, indent=2))
