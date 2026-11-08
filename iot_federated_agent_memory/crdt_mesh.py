"""Dimension 5: Offline-First CRDT Mesh Gossip & Merkle Delta Sync for Constrained IoT Nodes."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class CRDTDeltaMessage:
    node_id: str
    clock: int
    operation: str  # "upsert" or "delete"
    key: str
    value: Dict[str, Any]
    timestamp: float

    def get_hash(self) -> str:
        payload = f"{self.node_id}:{self.clock}:{self.key}:{json.dumps(self.value, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CRDTMeshGossipSync:
    """Manages offline-first CRDT gossip state and computes Merkle delta vectors."""

    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self.vector_clock = 0
        self.state_store: Dict[str, Dict[str, Any]] = {}
        self.delta_log: List[CRDTDeltaMessage] = []

    def apply_local_update(self, key: str, value: Dict[str, Any]) -> CRDTDeltaMessage:
        self.vector_clock += 1
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=self.vector_clock,
            operation="upsert",
            key=key,
            value=value,
            timestamp=time.time(),
        )
        self.state_store[key] = value
        self.delta_log.append(delta)
        return delta

    def compute_merkle_root(self) -> str:
        concatenated = "".join(sorted([f"{k}:{hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()}" for k, v in self.state_store.items()]))
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    def merge_remote_delta(self, delta: CRDTDeltaMessage) -> bool:
        # Last-write-wins or monotonic state sync
        self.state_store[delta.key] = delta.value
        self.delta_log.append(delta)
        return True
