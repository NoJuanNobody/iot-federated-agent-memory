"""Prefix-bucketed Merkle Tree and Dynamo-style anti-entropy subtree diffing (AI-239).

Keys are mapped into a fixed-depth 16-way radix tree using the hex prefix of
`sha256(key)`. Two replicas compare root hashes, then descend only along mismatched
prefix branches to isolate the exact set of divergent keys without transferring
unchanged state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

HEX_DIGITS = "0123456789abcdef"
EMPTY_HASH = hashlib.sha256(b"").hexdigest()


def _key_bucket_prefix(key: str, depth: int) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:depth]


@dataclass
class MerkleDiffStats:
    """Bandwidth and round-trip telemetry for comparing Merkle sync vs. full-state sync."""

    rounds: int
    nodes_compared: int
    divergent_buckets: int
    divergent_keys: int
    merkle_bytes_exchanged: int
    full_state_bytes: int

    @property
    def bandwidth_savings_ratio(self) -> float:
        if self.full_state_bytes <= 0:
            return 0.0
        return max(0.0, 1.0 - (self.merkle_bytes_exchanged / self.full_state_bytes))


class PrefixMerkleTree:
    """Incremental 16-way prefix-bucketed Merkle tree over `(key -> value_hash)` entries."""

    def __init__(self, depth: int = 3):
        if depth < 1 or depth > 6:
            raise ValueError("PrefixMerkleTree depth must be between 1 and 6")
        self.depth = depth
        # leaf_prefix (len == depth) -> {key: value_hash}
        self._buckets: Dict[str, Dict[str, str]] = {}
        # prefix (len 0..depth) -> sha256 hex digest
        self._hashes: Dict[str, str] = {"": EMPTY_HASH}

    def upsert(self, key: str, value_hash: str) -> str:
        """Insert or update a key's value hash and recompute only O(depth) ancestors."""
        bucket_prefix = _key_bucket_prefix(key, self.depth)
        bucket = self._buckets.setdefault(bucket_prefix, {})
        bucket[key] = value_hash
        self._recompute_path(bucket_prefix)
        return self._hashes[""]

    def delete(self, key: str) -> str:
        """Remove a key and recompute only O(depth) ancestors."""
        bucket_prefix = _key_bucket_prefix(key, self.depth)
        bucket = self._buckets.get(bucket_prefix)
        if bucket and key in bucket:
            del bucket[key]
            if not bucket:
                del self._buckets[bucket_prefix]
            self._recompute_path(bucket_prefix)
        return self._hashes[""]

    def _recompute_path(self, leaf_prefix: str) -> None:
        # 1. Recompute leaf hash
        bucket = self._buckets.get(leaf_prefix)
        if not bucket:
            self._hashes.pop(leaf_prefix, None)
        else:
            leaf_payload = "|".join(f"{k}:{bucket[k]}" for k in sorted(bucket.keys()))
            self._hashes[leaf_prefix] = hashlib.sha256(leaf_payload.encode("utf-8")).hexdigest()

        # 2. Walk up to root ("")
        for level in range(self.depth - 1, -1, -1):
            prefix = leaf_prefix[:level]
            child_parts = []
            for nibble in HEX_DIGITS:
                child_prefix = prefix + nibble
                ch = self._hashes.get(child_prefix)
                if ch:
                    child_parts.append(f"{nibble}:{ch}")
            if not child_parts:
                if prefix == "":
                    self._hashes[""] = EMPTY_HASH
                else:
                    self._hashes.pop(prefix, None)
            else:
                self._hashes[prefix] = hashlib.sha256("|".join(child_parts).encode("utf-8")).hexdigest()

    def root_hash(self) -> str:
        return self._hashes.get("", EMPTY_HASH)

    def node_hash(self, prefix: str) -> str:
        return self._hashes.get(prefix, EMPTY_HASH)

    def children_hashes(self, prefix: str) -> Dict[str, str]:
        """Return non-empty immediate child hashes under `prefix`."""
        if len(prefix) >= self.depth:
            return {}
        out: Dict[str, str] = {}
        for nibble in HEX_DIGITS:
            cp = prefix + nibble
            if cp in self._hashes:
                out[cp] = self._hashes[cp]
        return out

    def bucket_entries(self, leaf_prefix: str) -> Dict[str, str]:
        return dict(self._buckets.get(leaf_prefix, {}))

    def all_keys(self) -> Set[str]:
        keys: Set[str] = set()
        for bucket in self._buckets.values():
            keys.update(bucket.keys())
        return keys

    def diff_with(
        self,
        remote: PrefixMerkleTree,
        full_state_bytes: int = 0,
    ) -> Tuple[Set[str], MerkleDiffStats]:
        """Dynamo-style top-down subtree walk returning exact divergent keys and byte telemetry."""
        if self.depth != remote.depth:
            raise ValueError(f"Merkle tree depth mismatch: {self.depth} vs {remote.depth}")

        bytes_exchanged = 64  # root hash exchange (32B each way or 64B hex)
        nodes_compared = 1
        rounds = 1

        if self.root_hash() == remote.root_hash():
            return set(), MerkleDiffStats(
                rounds=rounds,
                nodes_compared=nodes_compared,
                divergent_buckets=0,
                divergent_keys=0,
                merkle_bytes_exchanged=bytes_exchanged,
                full_state_bytes=full_state_bytes,
            )

        frontier: List[str] = [""]
        divergent_leaves: List[str] = []

        while frontier:
            next_frontier: List[str] = []
            rounds += 1
            for prefix in frontier:
                local_children = self.children_hashes(prefix)
                remote_children = remote.children_hashes(prefix)
                # Account for wire exchange of child hash maps
                bytes_exchanged += len(json.dumps(local_children, separators=(",", ":")).encode("utf-8"))
                bytes_exchanged += len(json.dumps(remote_children, separators=(",", ":")).encode("utf-8"))

                all_child_prefixes = sorted(set(local_children.keys()) | set(remote_children.keys()))
                for cp in all_child_prefixes:
                    nodes_compared += 1
                    if local_children.get(cp) != remote_children.get(cp):
                        if len(cp) == self.depth:
                            divergent_leaves.append(cp)
                        else:
                            next_frontier.append(cp)
            frontier = next_frontier

        divergent_keys: Set[str] = set()
        if divergent_leaves:
            rounds += 1
            for leaf in divergent_leaves:
                local_entries = self.bucket_entries(leaf)
                remote_entries = remote.bucket_entries(leaf)
                bytes_exchanged += len(json.dumps(local_entries, separators=(",", ":")).encode("utf-8"))
                bytes_exchanged += len(json.dumps(remote_entries, separators=(",", ":")).encode("utf-8"))
                for k in set(local_entries.keys()) | set(remote_entries.keys()):
                    if local_entries.get(k) != remote_entries.get(k):
                        divergent_keys.add(k)

        return divergent_keys, MerkleDiffStats(
            rounds=rounds,
            nodes_compared=nodes_compared,
            divergent_buckets=len(divergent_leaves),
            divergent_keys=len(divergent_keys),
            merkle_bytes_exchanged=bytes_exchanged,
            full_state_bytes=full_state_bytes,
        )
