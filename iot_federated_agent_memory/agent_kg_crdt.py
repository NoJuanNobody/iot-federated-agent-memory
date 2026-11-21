"""Federated Agent Knowledge Graph on top of TinCan's CRDT Mesh (AI-241 — Core Paper Claim).

Models each coding agent's working memory as a conflict-free replicated knowledge graph:
- Entities (`kg:entity:<id>`): per-field HLC LWWMap so concurrent attribute edits merge cleanly.
- Entity Index (`kg:index:entities`): add-wins OR-Set tracking live entity IDs.
- Relations (`kg:edges`): add-wins OR-Set of `[src, predicate, dst]` triples.
- Decisions (`kg:decision:<topic>`): MVRegister preserving concurrent conflicting choices
  from partitioned agents until explicitly resolved.
- Provenance: every entity and relation is signed with the authoring agent's Ed25519 key.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from iot_federated_agent_memory.crdt_mesh import (
    CRDTMeshGossipSync,
    MerkleSyncResult,
    MeshTransportChannel,
    TrustStore,
)
from iot_federated_agent_memory.tincan_core import TinCanIdentity

ENTITY_INDEX_KEY = "kg:index:entities"
EDGES_KEY = "kg:edges"


class FederatedAgentKnowledgeGraph:
    """CRDT-backed knowledge graph for multi-agent pair programming across edge nodes."""

    def __init__(
        self,
        agent_id: str,
        transport: Optional[MeshTransportChannel] = None,
        identity: Optional[TinCanIdentity] = None,
        trust_store: Optional[TrustStore] = None,
        require_signatures: Optional[bool] = None,
        merkle_depth: int = 3,
    ):
        self.agent_id = agent_id
        self.mesh = CRDTMeshGossipSync(
            local_node_id=agent_id,
            transport=transport,
            identity=identity,
            trust_store=trust_store,
            require_signatures=require_signatures,
            merkle_depth=merkle_depth,
        )

    @staticmethod
    def _entity_key(entity_id: str) -> str:
        return f"kg:entity:{entity_id}"

    @staticmethod
    def _decision_key(topic: str) -> str:
        return f"kg:decision:{topic}"

    # --- Mutations ---

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create or update an entity's attributes using per-field HLC LWWMap CRDTs."""
        self.mesh.apply_orset_add(ENTITY_INDEX_KEY, entity_id)
        ekey = self._entity_key(entity_id)
        self.mesh.apply_lwwmap_set(ekey, "entity_id", entity_id)
        self.mesh.apply_lwwmap_set(ekey, "type", entity_type)
        self.mesh.apply_lwwmap_set(ekey, "last_author", self.agent_id)
        if self.mesh.identity is not None:
            self.mesh.apply_lwwmap_set(ekey, "author_pubkey", self.mesh.identity.address)
        for field_name, val in (attributes or {}).items():
            self.mesh.apply_lwwmap_set(ekey, field_name, val)

    def update_entity_field(self, entity_id: str, field_name: str, value: Any) -> None:
        """Update a single attribute on an entity without clobbering sibling fields."""
        self.mesh.apply_orset_add(ENTITY_INDEX_KEY, entity_id)
        ekey = self._entity_key(entity_id)
        self.mesh.apply_lwwmap_set(ekey, field_name, value)
        self.mesh.apply_lwwmap_set(ekey, "last_author", self.agent_id)

    def delete_entity(self, entity_id: str) -> None:
        self.mesh.apply_orset_remove(ENTITY_INDEX_KEY, entity_id)

    def add_relation(self, src: str, predicate: str, dst: str) -> None:
        """Add a directed knowledge-graph edge `[src, predicate, dst]` to the OR-Set."""
        self.mesh.apply_orset_add(EDGES_KEY, [src, predicate, dst])

    def remove_relation(self, src: str, predicate: str, dst: str) -> None:
        self.mesh.apply_orset_remove(EDGES_KEY, [src, predicate, dst])

    def propose_decision(self, topic: str, choice: Any) -> None:
        """Record an architectural/task decision in an MVRegister (preserves concurrent conflicts)."""
        self.mesh.apply_mvregister_set(self._decision_key(topic), choice)

    # --- Queries ---

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        index = self.mesh.orsets.get(ENTITY_INDEX_KEY)
        if index is None or not index.contains(entity_id):
            return None
        lmap = self.mesh.lwwmaps.get(self._entity_key(entity_id))
        return lmap.as_dict() if lmap is not None else {}

    def list_entities(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        index = self.mesh.orsets.get(ENTITY_INDEX_KEY)
        if index is None:
            return []
        results: List[Dict[str, Any]] = []
        for eid in index.elements():
            ent = self.get_entity(str(eid))
            if ent is None:
                continue
            if entity_type is None or ent.get("type") == entity_type:
                results.append(ent)
        return results

    def list_relations(
        self,
        src: Optional[str] = None,
        predicate: Optional[str] = None,
        dst: Optional[str] = None,
    ) -> List[Tuple[str, str, str]]:
        edges_set = self.mesh.orsets.get(EDGES_KEY)
        if edges_set is None:
            return []
        out: List[Tuple[str, str, str]] = []
        for triple in edges_set.elements():
            if not isinstance(triple, list) or len(triple) != 3:
                continue
            s, p, d = str(triple[0]), str(triple[1]), str(triple[2])
            if src is not None and s != src:
                continue
            if predicate is not None and p != predicate:
                continue
            if dst is not None and d != dst:
                continue
            out.append((s, p, d))
        return out

    def neighbors(self, entity_id: str, predicate: Optional[str] = None) -> List[Tuple[str, str]]:
        """Return outgoing `(predicate, dst)` neighbors of `entity_id`."""
        return [
            (p, d)
            for _s, p, d in self.list_relations(src=entity_id, predicate=predicate)
        ]

    def get_decision(self, topic: str) -> Dict[str, Any]:
        reg = self.mesh.mvregisters.get(self._decision_key(topic))
        if reg is None:
            return {"topic": topic, "values": [], "conflict": False}
        return {
            "topic": topic,
            "values": reg.values(),
            "conflict": reg.has_conflict(),
        }

    def list_conflicts(self) -> List[Dict[str, Any]]:
        conflicts: List[Dict[str, Any]] = []
        for key, reg in sorted(self.mesh.mvregisters.items()):
            if key.startswith("kg:decision:") and reg.has_conflict():
                topic = key[len("kg:decision:") :]
                conflicts.append({"topic": topic, "values": reg.values()})
        return conflicts

    def context_snapshot(self, focus_entity: Optional[str] = None) -> Dict[str, Any]:
        """Export a deterministic snapshot of shared agent memory for LLM prompt injection."""
        entities = self.list_entities()
        if focus_entity is not None:
            related_ids = {focus_entity}
            for s, _p, d in self.list_relations():
                if s == focus_entity:
                    related_ids.add(d)
                elif d == focus_entity:
                    related_ids.add(s)
            entities = [e for e in entities if e.get("entity_id") in related_ids]

        return {
            "agent_id": self.agent_id,
            "merkle_root": self.mesh.compute_merkle_root(),
            "vclock": self.mesh.vclock.to_dict(),
            "entities": entities,
            "relations": [list(r) for r in self.list_relations()],
            "conflicts": self.list_conflicts(),
        }

    # --- Synchronization helpers ---

    def merkle_root(self) -> str:
        return self.mesh.compute_merkle_root()

    def disconnect(self) -> None:
        self.mesh.disconnect()

    def reconnect(self, peer: Optional[FederatedAgentKnowledgeGraph] = None) -> MerkleSyncResult:
        return self.mesh.reconnect(peer=peer.mesh if peer is not None else None)

    def process_incoming(self, ignore_auth_errors: bool = False) -> int:
        return len(self.mesh.process_incoming_transport(ignore_auth_errors=ignore_auth_errors))

    def sync_with(self, peer: FederatedAgentKnowledgeGraph) -> MerkleSyncResult:
        return self.mesh.sync_with_peer(peer.mesh)
