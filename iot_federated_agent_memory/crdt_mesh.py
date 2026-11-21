"""Dimension 5: Offline-First CRDT Mesh Gossip, Prefix-Merkle Anti-Entropy & Ed25519 Signed Deltas."""

from __future__ import annotations

import base64
import collections
import hashlib
import json
import socket
import struct
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import nacl.exceptions
import nacl.signing

from iot_federated_agent_memory.crdt_types import (
    HLC,
    HLCTimestamp,
    LWWMap,
    MVRegister,
    ORSet,
    VectorClock,
)
from iot_federated_agent_memory.merkle_tree import MerkleDiffStats, PrefixMerkleTree
from iot_federated_agent_memory.tincan_core import (
    TinCanIdentity,
    address_to_verify_key,
)


FRAME_MAGIC = b"CRDT\x01\x00"  # 6-byte network framing header identifier
HEADER_SIZE = 46  # 6s (magic) + I (payload_len) + I (crc32) + 32s (sha256 digest)
DELTA_SIG_DOMAIN = b"TINCAN-CRDT-DELTA-V1\x00"


class FrameIntegrityError(Exception):
    """Raised when incoming network frame fails CRC32 checksum, SHA-256 verification, or framing format."""


class DeltaAuthenticationError(FrameIntegrityError):
    """Raised when a CRDT delta fails Ed25519 signature verification or signer trust checks."""


class TrustStore:
    """Manages trusted peer Ed25519 VerifyKeys for authenticated CRDT delta verification (AI-240)."""

    def __init__(self, trust_on_first_use: bool = False):
        self.trust_on_first_use = trust_on_first_use
        self._keys: Dict[str, nacl.signing.VerifyKey] = {}
        self._addresses: Dict[str, str] = {}

    @staticmethod
    def _coerce_verify_key(
        key_or_addr: Union[str, bytes, nacl.signing.VerifyKey, TinCanIdentity],
    ) -> Tuple[nacl.signing.VerifyKey, str]:
        if isinstance(key_or_addr, TinCanIdentity):
            return key_or_addr.verify_key, key_or_addr.address
        if isinstance(key_or_addr, nacl.signing.VerifyKey):
            return key_or_addr, base64.b64encode(bytes(key_or_addr)).decode("ascii")
        if isinstance(key_or_addr, bytes):
            vk = nacl.signing.VerifyKey(key_or_addr)
            return vk, base64.b64encode(key_or_addr).decode("ascii")
        if isinstance(key_or_addr, str):
            if key_or_addr.startswith("tc:"):
                return address_to_verify_key(key_or_addr), key_or_addr
            raw = base64.b64decode(key_or_addr.encode("ascii"))
            return nacl.signing.VerifyKey(raw), key_or_addr
        raise TypeError(f"Unsupported public key type: {type(key_or_addr).__name__}")

    def add_peer(
        self,
        node_id: str,
        key_or_addr: Union[str, bytes, nacl.signing.VerifyKey, TinCanIdentity],
    ) -> None:
        vk, addr = self._coerce_verify_key(key_or_addr)
        self._keys[node_id] = vk
        self._addresses[node_id] = addr

    def remove_peer(self, node_id: str) -> None:
        self._keys.pop(node_id, None)
        self._addresses.pop(node_id, None)

    def is_trusted(self, node_id: str) -> bool:
        return node_id in self._keys

    def resolve_verify_key(
        self, node_id: str, sender_pubkey: Optional[str]
    ) -> nacl.signing.VerifyKey:
        if not sender_pubkey:
            raise DeltaAuthenticationError(f"Delta from '{node_id}' is missing sender_pubkey")

        incoming_vk, _ = self._coerce_verify_key(sender_pubkey)
        pinned = self._keys.get(node_id)
        if pinned is not None:
            if bytes(pinned) != bytes(incoming_vk):
                raise DeltaAuthenticationError(
                    f"Key mismatch for node '{node_id}': sender_pubkey does not match pinned trust key"
                )
            return pinned

        if self.trust_on_first_use:
            self._keys[node_id] = incoming_vk
            self._addresses[node_id] = sender_pubkey
            return incoming_vk

        raise DeltaAuthenticationError(f"Untrusted peer '{node_id}' (public key not in TrustStore)")


@dataclass
class CRDTDeltaMessage:
    node_id: str
    clock: int
    operation: str  # "upsert", "delete", "orset_merge", "mvreg_set", "lwwmap_merge"
    key: str
    value: Dict[str, Any]
    timestamp: float
    vclock: Optional[Dict[str, int]] = None
    hlc: Optional[Dict[str, Any]] = None
    crdt_type: str = "lww"
    sender_pubkey: Optional[str] = None
    signature: Optional[str] = None

    def canonical_signing_bytes(self) -> bytes:
        """Deterministic byte representation signed by Ed25519 (excludes `signature`)."""
        data = self.to_dict()
        data.pop("signature", None)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return DELTA_SIG_DOMAIN + canonical

    def sign(self, identity: TinCanIdentity) -> CRDTDeltaMessage:
        """Sign this delta in-place using the node's Ed25519 TinCanIdentity."""
        self.sender_pubkey = identity.address
        sig = identity.signing_key.sign(self.canonical_signing_bytes()).signature
        self.signature = base64.b64encode(sig).decode("ascii")
        return self

    def verify(self, verify_key: Optional[nacl.signing.VerifyKey] = None) -> bool:
        """Verify the Ed25519 signature on this delta."""
        if not self.signature or not self.sender_pubkey:
            return False
        try:
            vk = verify_key
            if vk is None:
                vk, _ = TrustStore._coerce_verify_key(self.sender_pubkey)
            sig_bytes = base64.b64decode(self.signature.encode("ascii"))
            vk.verify(self.canonical_signing_bytes(), sig_bytes)
            return True
        except (nacl.exceptions.BadSignatureError, ValueError, TypeError):
            return False

    def get_hash(self) -> str:
        payload = (
            f"{self.node_id}:{self.clock}:{self.crdt_type}:{self.operation}:{self.key}:"
            f"{json.dumps(self.vclock or {}, sort_keys=True)}:"
            f"{json.dumps(self.value, sort_keys=True)}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CRDTDeltaMessage:
        return cls(
            node_id=str(data["node_id"]),
            clock=int(data["clock"]),
            operation=str(data["operation"]),
            key=str(data["key"]),
            value=dict(data.get("value", {})),
            timestamp=float(data["timestamp"]),
            vclock=dict(data["vclock"]) if data.get("vclock") is not None else None,
            hlc=dict(data["hlc"]) if data.get("hlc") is not None else None,
            crdt_type=str(data.get("crdt_type", "lww")),
            sender_pubkey=data.get("sender_pubkey"),
            signature=data.get("signature"),
        )

    def serialize(self) -> bytes:
        """Frame delta message into network bytes with CRC32 checksum and SHA-256 digest."""
        payload_bytes = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        payload_len = len(payload_bytes)
        crc32_val = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        sha256_digest = hashlib.sha256(payload_bytes).digest()

        header = struct.pack("!6sII32s", FRAME_MAGIC, payload_len, crc32_val, sha256_digest)
        return header + payload_bytes

    @classmethod
    def deserialize(cls, frame_bytes: bytes) -> CRDTDeltaMessage:
        """Deserialize network frame, verifying magic header, CRC32, and SHA-256 checksums."""
        if len(frame_bytes) < HEADER_SIZE:
            raise FrameIntegrityError(f"Frame length {len(frame_bytes)} is less than header size {HEADER_SIZE}")

        magic, payload_len, expected_crc32, expected_sha256 = struct.unpack("!6sII32s", frame_bytes[:HEADER_SIZE])

        if magic != FRAME_MAGIC:
            raise FrameIntegrityError(f"Invalid frame magic: {magic!r}, expected {FRAME_MAGIC!r}")

        payload_bytes = frame_bytes[HEADER_SIZE : HEADER_SIZE + payload_len]
        if len(payload_bytes) != payload_len:
            raise FrameIntegrityError(f"Truncated frame payload: expected {payload_len} bytes, got {len(payload_bytes)}")

        actual_crc32 = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        if actual_crc32 != expected_crc32:
            raise FrameIntegrityError(
                f"CRC32 checksum mismatch: expected {expected_crc32:#010x}, calculated {actual_crc32:#010x}"
            )

        actual_sha256 = hashlib.sha256(payload_bytes).digest()
        if actual_sha256 != expected_sha256:
            raise FrameIntegrityError("SHA-256 verification failed: digest mismatch")

        try:
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            raise FrameIntegrityError(f"Failed to decode JSON payload: {e}")

        return cls.from_dict(data)


class MeshTransportChannel(ABC):
    """Abstract transport channel for mesh gossip (UDP, WebRTC, BLE/LoRa frame buffers)."""

    def __init__(self, channel_type: str = "generic", mtu: int = 65535):
        self.channel_type = channel_type
        self.mtu = mtu
        self.is_connected: bool = True

    @abstractmethod
    def connect(self) -> None:
        """Establish or resume transport connectivity."""

    @abstractmethod
    def disconnect(self) -> None:
        """Drop or pause transport connectivity."""

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Transmit raw framed bytes across the channel."""

    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """Receive available framed bytes from the channel."""


class MockMeshTransport(MeshTransportChannel):
    """In-memory peer-to-peer transport channel for deterministic testing and local mesh simulations."""

    def __init__(self, channel_type: str = "mock", mtu: int = 65535):
        super().__init__(channel_type=channel_type, mtu=mtu)
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peers: List[MockMeshTransport] = []

    def link_peer(self, peer: MockMeshTransport) -> None:
        if peer not in self.peers:
            self.peers.append(peer)
        if self not in peer.peers:
            peer.peers.append(self)

    @classmethod
    def create_pair(cls, mtu: int = 65535) -> Tuple[MockMeshTransport, MockMeshTransport]:
        a = cls(mtu=mtu)
        b = cls(mtu=mtu)
        a.link_peer(b)
        return a, b

    @classmethod
    def create_mesh(cls, count: int = 3, mtu: int = 65535) -> List[MockMeshTransport]:
        nodes = [cls(mtu=mtu) for _ in range(count)]
        for i in range(count):
            for j in range(i + 1, count):
                nodes[i].link_peer(nodes[j])
        return nodes

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Payload size {len(data)} exceeds transport MTU {self.mtu}")

        delivered = False
        for peer in self.peers:
            if peer.is_connected:
                peer.inbox.append(data)
                delivered = True
        return delivered

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


class BLELoRaFrameBufferChannel(MeshTransportChannel):
    """Constrained frame-buffered transport channel (BLE MTU ~240B, LoRa MTU ~222B)

    with automatic segmentation and reassembly (SAR) of framed deltas.
    """

    def __init__(self, channel_type: str = "ble", mtu: int = 240):
        super().__init__(channel_type=channel_type, mtu=mtu)
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peers: List[BLELoRaFrameBufferChannel] = []
        self._reassembly_buffers: Dict[int, Dict[int, bytes]] = {}
        self._expected_chunks: Dict[int, int] = {}
        self._msg_counter: int = 0

    def link_peer(self, peer: BLELoRaFrameBufferChannel) -> None:
        if peer not in self.peers:
            self.peers.append(peer)
        if self not in peer.peers:
            peer.peers.append(self)

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected:
            return False

        chunk_header_size = 8  # !IHH: msg_id (4), chunk_index (2), total_chunks (2)
        max_chunk_payload = self.mtu - chunk_header_size
        if max_chunk_payload <= 0:
            raise ValueError(f"MTU {self.mtu} is too small for segmentation header")

        self._msg_counter = (self._msg_counter + 1) & 0xFFFFFFFF
        msg_id = self._msg_counter

        chunks = []
        offset = 0
        total_len = len(data)
        while offset < total_len:
            chunks.append(data[offset : offset + max_chunk_payload])
            offset += max_chunk_payload

        total_chunks = len(chunks)
        delivered = False

        for idx, chunk in enumerate(chunks):
            header = struct.pack("!IHH", msg_id, idx, total_chunks)
            packet = header + chunk
            for peer in self.peers:
                if peer.is_connected:
                    peer._receive_chunk(packet)
                    delivered = True

        return delivered

    def _receive_chunk(self, chunk_packet: bytes) -> None:
        if not self.is_connected or len(chunk_packet) < 8:
            return
        msg_id, chunk_idx, total_chunks = struct.unpack("!IHH", chunk_packet[:8])
        chunk_data = chunk_packet[8:]

        if msg_id not in self._reassembly_buffers:
            self._reassembly_buffers[msg_id] = {}
            self._expected_chunks[msg_id] = total_chunks

        self._reassembly_buffers[msg_id][chunk_idx] = chunk_data

        if len(self._reassembly_buffers[msg_id]) == self._expected_chunks[msg_id]:
            ordered = [self._reassembly_buffers[msg_id][i] for i in range(total_chunks)]
            full_frame = b"".join(ordered)
            self.inbox.append(full_frame)
            del self._reassembly_buffers[msg_id]
            del self._expected_chunks[msg_id]

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


class UDPTransportChannel(MeshTransportChannel):
    """Real socket-based UDP datagram transport channel for local/LAN mesh node gossip."""

    def __init__(
        self,
        bind_host: str = "127.0.0.1",
        bind_port: int = 0,
        peer_host: str = "127.0.0.1",
        peer_port: Optional[int] = None,
        mtu: int = 1472,
    ):
        super().__init__(channel_type="udp", mtu=mtu)
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.peer_host = peer_host
        self.peer_port = peer_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_host, self.bind_port))
        self.sock.setblocking(False)
        self.bound_port = self.sock.getsockname()[1]

    def set_peer_port(self, port: int) -> None:
        self.peer_port = port

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected or self.peer_port is None:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Payload {len(data)} exceeds UDP MTU {self.mtu}")
        try:
            self.sock.sendto(data, (self.peer_host, self.peer_port))
            return True
        except Exception:
            return False

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        try:
            data, _ = self.sock.recvfrom(65535)
            return data
        except BlockingIOError:
            return None
        except Exception:
            return None

    def close(self) -> None:
        self.sock.close()


class WebRTCDataChannel(MeshTransportChannel):
    """Simulated WebRTC SCTP data channel for peer-to-peer browser/agent mesh links."""

    def __init__(self, label: str = "crdt-sync", mtu: int = 16384):
        super().__init__(channel_type="webrtc", mtu=mtu)
        self.label = label
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peer: Optional[WebRTCDataChannel] = None

    def link(self, peer: WebRTCDataChannel) -> None:
        self.peer = peer
        peer.peer = self

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected or not self.peer or not self.peer.is_connected:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Data {len(data)} exceeds WebRTC MTU {self.mtu}")
        self.peer.inbox.append(data)
        return True

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


@dataclass
class MerkleSyncResult:
    """Result of Merkle delta synchronization between mesh gossip nodes."""

    parity_achieved: bool
    local_merkle_root: str
    remote_merkle_root: str
    deltas_synced: int
    local_clock: int
    remote_clock: int
    divergent_keys: Optional[List[str]] = None
    merkle_stats: Optional[MerkleDiffStats] = None


class CRDTMeshGossipSync:
    """Offline-first CRDT mesh node with VectorClocks/HLC, OR-Set/MVRegister/LWWMap,
    PrefixMerkleTree Dynamo-style anti-entropy, and Ed25519 signed delta verification.
    """

    def __init__(
        self,
        local_node_id: str,
        transport: Optional[MeshTransportChannel] = None,
        identity: Optional[TinCanIdentity] = None,
        trust_store: Optional[TrustStore] = None,
        require_signatures: Optional[bool] = None,
        merkle_depth: int = 3,
    ):
        self.local_node_id = local_node_id
        self.vector_clock = 0  # Legacy Lamport counter preserved for backward compatibility
        self.vclock = VectorClock()
        self.hlc = HLC(local_node_id)

        self.state_store: Dict[str, Dict[str, Any]] = {}
        self.orsets: Dict[str, ORSet] = {}
        self.mvregisters: Dict[str, MVRegister] = {}
        self.lwwmaps: Dict[str, LWWMap] = {}
        self.merkle_tree = PrefixMerkleTree(depth=merkle_depth)

        self.delta_log: List[CRDTDeltaMessage] = []
        self._deltas_by_key: Dict[str, List[CRDTDeltaMessage]] = {}
        self.offline_queue: List[CRDTDeltaMessage] = []
        self.seen_delta_hashes: Set[str] = set()
        self.key_metadata: Dict[str, Tuple[float, int, str]] = {}  # key -> (timestamp, clock, node_id)
        self.key_vclocks: Dict[str, VectorClock] = {}

        # Telemetry counters for evaluation harness (AI-242)
        self.conflicts_detected: int = 0
        self.rejected_deltas: int = 0

        # Cryptographic identity & peer trust store (AI-240)
        self.identity: Optional[TinCanIdentity] = identity
        self.trust_store: Optional[TrustStore] = trust_store
        if require_signatures is None:
            self.require_signatures = (identity is not None) or (trust_store is not None)
        else:
            self.require_signatures = require_signatures
        if self.identity is not None and self.trust_store is not None:
            self.trust_store.add_peer(self.local_node_id, self.identity)

        self.transport: Optional[MeshTransportChannel] = transport
        self.is_online: bool = transport.is_connected if transport else True

    def attach_transport(self, transport: MeshTransportChannel) -> None:
        """Attach a transport channel to this node."""
        self.transport = transport
        self.is_online = transport.is_connected

    @staticmethod
    def _hash_value(value: Any) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _update_merkle_for_key(self, key: str) -> None:
        if key in self.orsets:
            self.merkle_tree.upsert(key, self.orsets[key].state_hash())
        elif key in self.mvregisters:
            self.merkle_tree.upsert(key, self.mvregisters[key].state_hash())
        elif key in self.lwwmaps:
            self.merkle_tree.upsert(key, self.lwwmaps[key].state_hash())
        elif key in self.state_store:
            self.merkle_tree.upsert(key, self._hash_value(self.state_store[key]))
        else:
            self.merkle_tree.delete(key)

    def _emit_delta(self, delta: CRDTDeltaMessage) -> CRDTDeltaMessage:
        if self.identity is not None:
            delta.sign(self.identity)

        delta_hash = delta.get_hash()
        self.seen_delta_hashes.add(delta_hash)
        self.delta_log.append(delta)
        self._deltas_by_key.setdefault(delta.key, []).append(delta)

        if self.is_online and self.transport and self.transport.is_connected:
            try:
                frame = delta.serialize()
                sent = self.transport.send(frame)
                if not sent:
                    self.offline_queue.append(delta)
            except Exception:
                self.offline_queue.append(delta)
        else:
            self.offline_queue.append(delta)
        return delta

    def _advance_clocks(self) -> Tuple[int, Dict[str, int], HLCTimestamp]:
        self.vector_clock += 1
        self.vclock.increment(self.local_node_id)
        hlc_ts = self.hlc.tick()
        return self.vector_clock, self.vclock.to_dict(), hlc_ts

    def apply_local_update(
        self, key: str, value: Dict[str, Any], operation: str = "upsert"
    ) -> CRDTDeltaMessage:
        """Apply a local LWW key/value modification, advance clocks, and broadcast or buffer."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        ts = time.time()
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation=operation,
            key=key,
            value=value,
            timestamp=ts,
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="lww",
        )

        self.key_metadata[key] = (ts, clock, self.local_node_id)
        self.key_vclocks[key] = VectorClock.from_dict(vc_dict)

        if operation == "delete":
            self.state_store.pop(key, None)
        else:
            self.state_store[key] = value
        self._update_merkle_for_key(key)
        return self._emit_delta(delta)

    def apply_orset_add(self, key: str, element: Any) -> CRDTDeltaMessage:
        """Add an element to an add-wins OR-Set CRDT under `key`."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        orset = self.orsets.setdefault(key, ORSet())
        orset.add(element, self.local_node_id, self.vclock.get(self.local_node_id))
        self.state_store[key] = {"elements": orset.elements()}
        self._update_merkle_for_key(key)
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation="orset_merge",
            key=key,
            value=orset.to_dict(),
            timestamp=time.time(),
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="orset",
        )
        return self._emit_delta(delta)

    def apply_orset_remove(self, key: str, element: Any) -> CRDTDeltaMessage:
        """Remove currently observed dots for `element` from the OR-Set under `key`."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        orset = self.orsets.setdefault(key, ORSet())
        orset.remove(element)
        self.state_store[key] = {"elements": orset.elements()}
        self._update_merkle_for_key(key)
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation="orset_merge",
            key=key,
            value=orset.to_dict(),
            timestamp=time.time(),
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="orset",
        )
        return self._emit_delta(delta)

    def apply_mvregister_set(self, key: str, value: Any) -> CRDTDeltaMessage:
        """Set a Multi-Value Register under `key`, preserving concurrent siblings."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        reg = self.mvregisters.setdefault(key, MVRegister())
        reg.set(value, VectorClock.from_dict(vc_dict), self.local_node_id)
        self.state_store[key] = {"values": reg.values(), "conflict": reg.has_conflict()}
        self._update_merkle_for_key(key)
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation="mvreg_merge",
            key=key,
            value=reg.to_dict(),
            timestamp=time.time(),
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="mvreg",
        )
        return self._emit_delta(delta)

    def apply_lwwmap_set(self, key: str, field_name: str, value: Any) -> CRDTDeltaMessage:
        """Set a single field on a per-field HLC LWWMap under `key`."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        lmap = self.lwwmaps.setdefault(key, LWWMap())
        lmap.set_field(field_name, value, hlc_ts)
        self.state_store[key] = lmap.as_dict()
        self._update_merkle_for_key(key)
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation="lwwmap_merge",
            key=key,
            value=lmap.to_dict(),
            timestamp=time.time(),
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="lwwmap",
        )
        return self._emit_delta(delta)

    def apply_lwwmap_delete(self, key: str, field_name: str) -> CRDTDeltaMessage:
        """Delete a single field on a per-field HLC LWWMap under `key`."""
        clock, vc_dict, hlc_ts = self._advance_clocks()
        lmap = self.lwwmaps.setdefault(key, LWWMap())
        lmap.delete_field(field_name, hlc_ts)
        self.state_store[key] = lmap.as_dict()
        self._update_merkle_for_key(key)
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=clock,
            operation="lwwmap_merge",
            key=key,
            value=lmap.to_dict(),
            timestamp=time.time(),
            vclock=vc_dict,
            hlc=hlc_ts.to_dict(),
            crdt_type="lwwmap",
        )
        return self._emit_delta(delta)

    def compute_merkle_root(self) -> str:
        """Deterministic root hash from the prefix-bucketed PrefixMerkleTree."""
        return self.merkle_tree.root_hash()

    def _verify_delta_signature(self, delta: CRDTDeltaMessage) -> None:
        """Enforce Ed25519 signature + TrustStore verification when enabled."""
        if not self.require_signatures and not delta.signature:
            return
        if not delta.signature or not delta.sender_pubkey:
            self.rejected_deltas += 1
            raise DeltaAuthenticationError(
                f"Unsigned delta from '{delta.node_id}' rejected (require_signatures=True)"
            )
        verify_key: Optional[nacl.signing.VerifyKey] = None
        if self.trust_store is not None:
            try:
                verify_key = self.trust_store.resolve_verify_key(delta.node_id, delta.sender_pubkey)
            except DeltaAuthenticationError:
                self.rejected_deltas += 1
                raise
        if not delta.verify(verify_key=verify_key):
            self.rejected_deltas += 1
            raise DeltaAuthenticationError(
                f"Invalid Ed25519 signature on delta from '{delta.node_id}' for key '{delta.key}'"
            )

    def merge_remote_delta(self, delta: CRDTDeltaMessage) -> bool:
        """Verify signature, deduplicate, merge causality clocks, and apply CRDT semilattice join."""
        self._verify_delta_signature(delta)

        delta_hash = delta.get_hash()
        if delta_hash in self.seen_delta_hashes:
            return False

        self.seen_delta_hashes.add(delta_hash)
        self.vector_clock = max(self.vector_clock, delta.clock)

        if delta.vclock:
            incoming_vc = VectorClock.from_dict(delta.vclock)
            self.vclock.merge(incoming_vc)
        else:
            incoming_vc = None

        if delta.hlc:
            self.hlc.receive(delta.hlc)

        if delta.crdt_type == "orset":
            incoming_set = ORSet.from_dict(delta.value)
            local_set = self.orsets.setdefault(delta.key, ORSet())
            local_set.merge(incoming_set)
            self.state_store[delta.key] = {"elements": local_set.elements()}
        elif delta.crdt_type == "mvreg":
            incoming_reg = MVRegister.from_dict(delta.value)
            local_reg = self.mvregisters.setdefault(delta.key, MVRegister())
            had_conflict = local_reg.has_conflict()
            now_conflict = local_reg.merge(incoming_reg)
            if now_conflict and not had_conflict:
                self.conflicts_detected += 1
            self.state_store[delta.key] = {
                "values": local_reg.values(),
                "conflict": local_reg.has_conflict(),
            }
        elif delta.crdt_type == "lwwmap":
            incoming_map = LWWMap.from_dict(delta.value)
            local_map = self.lwwmaps.setdefault(delta.key, LWWMap())
            local_map.merge(incoming_map)
            self.state_store[delta.key] = local_map.as_dict()
        else:
            # Legacy LWW register with concurrent-write detection via VectorClock
            prev_vc = self.key_vclocks.get(delta.key)
            if prev_vc is not None and incoming_vc is not None and prev_vc.is_concurrent_with(incoming_vc):
                self.conflicts_detected += 1

            current_meta = self.key_metadata.get(delta.key)
            incoming_meta = (delta.timestamp, delta.clock, delta.node_id)
            should_apply = current_meta is None or incoming_meta >= current_meta

            if should_apply:
                self.key_metadata[delta.key] = incoming_meta
                if incoming_vc is not None:
                    self.key_vclocks[delta.key] = (
                        prev_vc.merged(incoming_vc) if prev_vc is not None else incoming_vc
                    )
                if delta.operation == "delete":
                    self.state_store.pop(delta.key, None)
                else:
                    self.state_store[delta.key] = delta.value
            elif incoming_vc is not None and prev_vc is not None:
                self.key_vclocks[delta.key] = prev_vc.merged(incoming_vc)

        self._update_merkle_for_key(delta.key)
        self.delta_log.append(delta)
        self._deltas_by_key.setdefault(delta.key, []).append(delta)
        return True

    def disconnect(self) -> None:
        """Simulate transport link failure or offline edge node condition."""
        self.is_online = False
        if self.transport:
            self.transport.disconnect()

    def reconnect(self, peer: Optional[CRDTMeshGossipSync] = None) -> MerkleSyncResult:
        """Restore connectivity, flush buffered offline deltas, and reconcile via Merkle anti-entropy."""
        self.is_online = True
        if self.transport:
            self.transport.connect()

        flushed_count = self.flush_offline_queue()
        self.process_incoming_transport()

        if peer is not None:
            return self.sync_with_peer(peer)

        local_root = self.compute_merkle_root()
        return MerkleSyncResult(
            parity_achieved=True,
            local_merkle_root=local_root,
            remote_merkle_root=local_root,
            deltas_synced=flushed_count,
            local_clock=self.vector_clock,
            remote_clock=self.vector_clock,
        )

    def flush_offline_queue(self) -> int:
        """Transmit all deltas buffered in the offline queue."""
        if not self.transport or not self.transport.is_connected:
            return 0

        flushed = 0
        remaining = []
        for delta in self.offline_queue:
            try:
                frame = delta.serialize()
                if self.transport.send(frame):
                    flushed += 1
                else:
                    remaining.append(delta)
            except Exception:
                remaining.append(delta)

        self.offline_queue = remaining
        return flushed

    def process_incoming_transport(self, ignore_auth_errors: bool = False) -> List[CRDTDeltaMessage]:
        """Poll transport for serialized network frames, verify integrity + Ed25519 signature, and merge."""
        if not self.transport or not self.transport.is_connected:
            return []

        merged: List[CRDTDeltaMessage] = []
        while True:
            frame_bytes = self.transport.receive()
            if not frame_bytes:
                break
            delta = CRDTDeltaMessage.deserialize(frame_bytes)
            try:
                if self.merge_remote_delta(delta):
                    merged.append(delta)
            except DeltaAuthenticationError:
                if not ignore_auth_errors:
                    raise

        return merged

    def estimate_full_state_bytes(self) -> int:
        """Estimate serialized byte size of full state transfer (baseline for AI-239 / AI-242)."""
        return len(json.dumps(self.state_store, sort_keys=True, separators=(",", ":")).encode("utf-8"))

    def sync_with_peer(self, peer: CRDTMeshGossipSync) -> MerkleSyncResult:
        """Dynamo-style Merkle tree anti-entropy: walk prefix trees to isolate divergent keys
        and transfer ONLY deltas for those divergent keys.
        """
        full_bytes = self.estimate_full_state_bytes() + peer.estimate_full_state_bytes()
        divergent_keys, diff_stats = self.merkle_tree.diff_with(
            peer.merkle_tree, full_state_bytes=full_bytes
        )

        synced_count = 0
        delta_bytes_sent = 0

        for key in sorted(divergent_keys):
            for d in self._deltas_by_key.get(key, []):
                if d.get_hash() not in peer.seen_delta_hashes:
                    delta_bytes_sent += len(d.serialize())
                    if peer.merge_remote_delta(d):
                        synced_count += 1
            for d in peer._deltas_by_key.get(key, []):
                if d.get_hash() not in self.seen_delta_hashes:
                    delta_bytes_sent += len(d.serialize())
                    if self.merge_remote_delta(d):
                        synced_count += 1

        diff_stats.merkle_bytes_exchanged += delta_bytes_sent

        local_root = self.compute_merkle_root()
        remote_root = peer.compute_merkle_root()
        parity_achieved = local_root == remote_root

        return MerkleSyncResult(
            parity_achieved=parity_achieved,
            local_merkle_root=local_root,
            remote_merkle_root=remote_root,
            deltas_synced=synced_count,
            local_clock=self.vector_clock,
            remote_clock=peer.vector_clock,
            divergent_keys=sorted(divergent_keys),
            merkle_stats=diff_stats,
        )
