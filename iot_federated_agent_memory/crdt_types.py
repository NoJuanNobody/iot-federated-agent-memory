"""Causality clocks and conflict-free replicated data types (CRDTs) for TinCan Mesh.

Implements Strong Eventual Consistency (SEC) primitives for federated agent memory:
- VectorClock: per-node causal history detecting happens-before vs. concurrent writes
- HLC (Hybrid Logical Clock): wall-clock bounded logical timestamps with total ordering
- ORSet (Observed-Remove Set): add-wins set CRDT for entity tags, graph edges, and sets
- MVRegister (Multi-Value Register): retains all concurrent sibling values instead of silent drops
- LWWMap: per-field HLC last-write-wins map so concurrent edits to distinct fields merge cleanly
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Literal, Optional, Set, Tuple

CausalOrder = Literal["before", "after", "equal", "concurrent"]


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class VectorClock:
    """Per-node causal vector clock supporting partial ordering and concurrent-write detection."""

    def __init__(self, entries: Optional[Dict[str, int]] = None):
        self._clock: Dict[str, int] = {str(k): int(v) for k, v in (entries or {}).items() if int(v) > 0}

    def copy(self) -> VectorClock:
        return VectorClock(self._clock)

    def get(self, node_id: str) -> int:
        return self._clock.get(node_id, 0)

    def increment(self, node_id: str) -> int:
        new_val = self._clock.get(node_id, 0) + 1
        self._clock[node_id] = new_val
        return new_val

    def merge(self, other: VectorClock | Dict[str, int]) -> VectorClock:
        other_map = other._clock if isinstance(other, VectorClock) else other
        for nid, val in other_map.items():
            iv = int(val)
            if iv > self._clock.get(nid, 0):
                self._clock[nid] = iv
        return self

    def merged(self, other: VectorClock | Dict[str, int]) -> VectorClock:
        res = self.copy()
        res.merge(other)
        return res

    def compare(self, other: VectorClock | Dict[str, int]) -> CausalOrder:
        """Return 'equal', 'before' (self < other), 'after' (self > other), or 'concurrent'."""
        other_map = other._clock if isinstance(other, VectorClock) else other
        all_nodes = set(self._clock.keys()) | set(other_map.keys())
        less = False
        greater = False
        for nid in all_nodes:
            a = self._clock.get(nid, 0)
            b = int(other_map.get(nid, 0))
            if a < b:
                less = True
            elif a > b:
                greater = True
            if less and greater:
                return "concurrent"
        if not less and not greater:
            return "equal"
        return "before" if less else "after"

    def dominates(self, other: VectorClock | Dict[str, int]) -> bool:
        return self.compare(other) in ("after", "equal")

    def is_concurrent_with(self, other: VectorClock | Dict[str, int]) -> bool:
        return self.compare(other) == "concurrent"

    def total_events(self) -> int:
        return sum(self._clock.values())

    def to_dict(self) -> Dict[str, int]:
        return dict(sorted(self._clock.items()))

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, int]]) -> VectorClock:
        return cls(data or {})

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VectorClock):
            return self._clock == other._clock
        if isinstance(other, dict):
            return self._clock == {str(k): int(v) for k, v in other.items() if int(v) > 0}
        return False

    def __repr__(self) -> str:
        return f"VectorClock({self.to_dict()})"


@dataclass(frozen=True, order=True)
class HLCTimestamp:
    """Immutable Hybrid Logical Clock timestamp with deterministic total order."""

    wall_ms: int
    logical: int
    node_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"wall_ms": self.wall_ms, "logical": self.logical, "node_id": self.node_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HLCTimestamp:
        return cls(
            wall_ms=int(data["wall_ms"]),
            logical=int(data["logical"]),
            node_id=str(data["node_id"]),
        )


class HLC:
    """Hybrid Logical Clock (Kulkarni et al., 2014) for causal + wall-time bounded ordering."""

    def __init__(self, node_id: str, wall_ms: int = 0, logical: int = 0):
        self.node_id = str(node_id)
        self.wall_ms = int(wall_ms)
        self.logical = int(logical)

    def current(self) -> HLCTimestamp:
        return HLCTimestamp(self.wall_ms, self.logical, self.node_id)

    def tick(self, now_ms: Optional[int] = None) -> HLCTimestamp:
        pt = int(time.time() * 1000) if now_ms is None else int(now_ms)
        if pt > self.wall_ms:
            self.wall_ms = pt
            self.logical = 0
        else:
            self.logical += 1
        return self.current()

    def receive(self, remote: HLCTimestamp | Dict[str, Any], now_ms: Optional[int] = None) -> HLCTimestamp:
        r = remote if isinstance(remote, HLCTimestamp) else HLCTimestamp.from_dict(remote)
        pt = int(time.time() * 1000) if now_ms is None else int(now_ms)
        prev_wall = self.wall_ms
        self.wall_ms = max(prev_wall, r.wall_ms, pt)
        if self.wall_ms == prev_wall and self.wall_ms == r.wall_ms:
            self.logical = max(self.logical, r.logical) + 1
        elif self.wall_ms == prev_wall:
            self.logical += 1
        elif self.wall_ms == r.wall_ms:
            self.logical = r.logical + 1
        else:
            self.logical = 0
        return self.current()


class ORSet:
    """Observed-Remove Set (add-wins semantics) CRDT.

    Each added element is tagged with a unique dot `(node_id, counter)`.
    Removing an element tombstones only the dots currently observed locally, so a
    concurrent add on another replica survives the merge (add-wins, SEC guaranteed).
    """

    def __init__(
        self,
        adds: Optional[Dict[str, Set[str]]] = None,
        tombstones: Optional[Set[str]] = None,
    ):
        # canonical_element_json -> set of dot strings "node_id:counter"
        self._adds: Dict[str, Set[str]] = {
            k: set(v) for k, v in (adds or {}).items()
        }
        self._tombstones: Set[str] = set(tombstones or set())

    @staticmethod
    def _encode_elem(element: Any) -> str:
        return _canonical_json(element)

    @staticmethod
    def _decode_elem(encoded: str) -> Any:
        return json.loads(encoded)

    @staticmethod
    def make_dot(node_id: str, counter: int) -> str:
        return f"{node_id}:{counter}"

    def add(self, element: Any, node_id: str, counter: int) -> str:
        dot = self.make_dot(node_id, counter)
        key = self._encode_elem(element)
        self._adds.setdefault(key, set()).add(dot)
        return dot

    def remove(self, element: Any) -> Set[str]:
        key = self._encode_elem(element)
        observed = set(self._adds.get(key, set())) - self._tombstones
        self._tombstones.update(observed)
        return observed

    def elements(self) -> List[Any]:
        active = []
        for encoded in sorted(self._adds.keys()):
            live_dots = self._adds[encoded] - self._tombstones
            if live_dots:
                active.append(self._decode_elem(encoded))
        return active

    def contains(self, element: Any) -> bool:
        key = self._encode_elem(element)
        return bool(self._adds.get(key, set()) - self._tombstones)

    def merge(self, other: ORSet) -> ORSet:
        """Semilattice join: union of adds and union of tombstones (commutative, associative, idempotent)."""
        for elem_key, dots in other._adds.items():
            self._adds.setdefault(elem_key, set()).update(dots)
        self._tombstones.update(other._tombstones)
        return self

    def gc_tombstones(self, causal_horizon: Dict[str, int]) -> int:
        """Garbage-collect causally stable tombstones whose dot counter <= causal_horizon[node_id].

        Only call with a causal stability vector (minimum observed clock across all active peers)
        so pruned tombstones can never be resurrected by an in-flight delayed delta.
        Returns the number of tombstones pruned.
        """
        pruned: Set[str] = set()
        for dot in self._tombstones:
            if ":" not in dot:
                continue
            node_id, counter_s = dot.rsplit(":", 1)
            try:
                counter = int(counter_s)
            except ValueError:
                continue
            if counter <= causal_horizon.get(node_id, 0):
                pruned.add(dot)

        if not pruned:
            return 0

        self._tombstones -= pruned
        empty_keys: List[str] = []
        for elem_key, dots in self._adds.items():
            dots -= pruned
            if not dots:
                empty_keys.append(elem_key)
        for elem_key in empty_keys:
            self._adds.pop(elem_key, None)
        return len(pruned)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crdt_type": "orset",
            "adds": {k: sorted(v) for k, v in sorted(self._adds.items())},
            "tombstones": sorted(self._tombstones),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ORSet:
        adds = {k: set(v) for k, v in data.get("adds", {}).items()}
        tombstones = set(data.get("tombstones", []))
        return cls(adds=adds, tombstones=tombstones)

    def state_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass
class _MVEntry:
    value: Any
    vclock: VectorClock
    node_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "vclock": self.vclock.to_dict(),
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> _MVEntry:
        return cls(
            value=data["value"],
            vclock=VectorClock.from_dict(data.get("vclock", {})),
            node_id=str(data.get("node_id", "")),
        )

    def sort_key(self) -> str:
        return _canonical_json(self.to_dict())


class MVRegister:
    """Multi-Value Register CRDT.

    Detects concurrent writes using VectorClocks and preserves all concurrent sibling
    values rather than silently overwriting them. A subsequent write with a causally
    dominating VectorClock resolves the conflict back to a single value.
    """

    def __init__(self, entries: Optional[List[_MVEntry]] = None):
        self._entries: List[_MVEntry] = list(entries or [])
        self._prune()

    def _prune(self) -> None:
        """Drop any entry causally dominated by another entry, and deduplicate identical entries."""
        unique: Dict[str, _MVEntry] = {}
        for entry in self._entries:
            unique[entry.sort_key()] = entry
        candidates = list(unique.values())
        kept: List[_MVEntry] = []
        for i, cand in enumerate(candidates):
            dominated = False
            for j, other in enumerate(candidates):
                if i == j:
                    continue
                if cand.vclock.compare(other.vclock) == "before":
                    dominated = True
                    break
            if not dominated:
                kept.append(cand)
        kept.sort(key=lambda e: e.sort_key())
        self._entries = kept

    def set(self, value: Any, vclock: VectorClock, node_id: str) -> bool:
        """Insert a write; returns True if this write is concurrent with an existing value."""
        is_concurrent = any(
            vclock.is_concurrent_with(existing.vclock) for existing in self._entries
        )
        self._entries.append(_MVEntry(value=value, vclock=vclock.copy(), node_id=node_id))
        self._prune()
        return is_concurrent

    def merge(self, other: MVRegister) -> bool:
        """Merge another MVRegister. Returns True if the merged register holds concurrent siblings."""
        self._entries.extend(
            _MVEntry(e.value, e.vclock.copy(), e.node_id) for e in other._entries
        )
        self._prune()
        return self.has_conflict()

    def has_conflict(self) -> bool:
        return len(self._entries) > 1

    def values(self) -> List[Any]:
        return [e.value for e in self._entries]

    def vclock(self) -> VectorClock:
        merged = VectorClock()
        for e in self._entries:
            merged.merge(e.vclock)
        return merged

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crdt_type": "mvreg",
            "entries": [e.to_dict() for e in self._entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MVRegister:
        entries = [_MVEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(entries=entries)

    def state_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


class LWWMap:
    """Per-field HLC Last-Write-Wins Map CRDT (suited for agent knowledge-graph entity attributes).

    Each field has its own HLC timestamp and tombstone flag so concurrent updates to
    different fields of the same entity merge cleanly without losing either update.
    """

    def __init__(
        self,
        fields: Optional[Dict[str, Tuple[Any, HLCTimestamp, bool]]] = None,
    ):
        # field_name -> (value, hlc_timestamp, is_deleted)
        self._fields: Dict[str, Tuple[Any, HLCTimestamp, bool]] = dict(fields or {})

    def set_field(self, field_name: str, value: Any, ts: HLCTimestamp) -> bool:
        existing = self._fields.get(field_name)
        if existing is None or ts >= existing[1]:
            self._fields[field_name] = (value, ts, False)
            return True
        return False

    def delete_field(self, field_name: str, ts: HLCTimestamp) -> bool:
        existing = self._fields.get(field_name)
        if existing is None or ts >= existing[1]:
            self._fields[field_name] = (None, ts, True)
            return True
        return False

    def merge(self, other: LWWMap) -> LWWMap:
        for fname, (val, ts, deleted) in other._fields.items():
            existing = self._fields.get(fname)
            if existing is None or ts >= existing[1]:
                self._fields[fname] = (val, ts, deleted)
        return self

    def as_dict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, (v, _ts, deleted) in sorted(self._fields.items())
            if not deleted
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crdt_type": "lwwmap",
            "fields": {
                k: {"value": v, "hlc": ts.to_dict(), "deleted": deleted}
                for k, (v, ts, deleted) in sorted(self._fields.items())
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LWWMap:
        parsed: Dict[str, Tuple[Any, HLCTimestamp, bool]] = {}
        for k, meta in data.get("fields", {}).items():
            parsed[k] = (
                meta.get("value"),
                HLCTimestamp.from_dict(meta["hlc"]),
                bool(meta.get("deleted", False)),
            )
        return cls(fields=parsed)

    def state_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()
