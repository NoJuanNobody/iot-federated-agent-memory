"""Decentralized LAN peer discovery for TinCan Mesh (AI-237).

Supports two zero-infrastructure discovery backends:
1. mDNS / DNS-SD via `python-zeroconf` (`_tincan-mesh._udp.local.`) when installed.
2. Built-in zero-dependency UDP multicast/broadcast beacon (`239.255.77.88:5354`)
   as a resilient fallback for air-gapped or minimal edge devices.

Handles automatic peer join, TTL expiry (drop), and rejoin callbacks so the
CRDT gossip mesh reconciles state automatically without any central registry.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

try:
    from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf  # type: ignore

    HAS_ZEROCONF = True
except ImportError:
    ServiceBrowser = None  # type: ignore
    ServiceInfo = None  # type: ignore
    ServiceListener = object  # type: ignore
    Zeroconf = None  # type: ignore
    HAS_ZEROCONF = False


SERVICE_TYPE = "_tincan-mesh._udp.local."
DEFAULT_MCAST_GROUP = "239.255.77.88"
DEFAULT_MCAST_PORT = 5354
BEACON_MAGIC = "TINCAN-DISC-V1"


def detect_lan_ip() -> str:
    """Detect the primary non-loopback LAN IPv4 address without sending network traffic."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        ip = sock.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    finally:
        sock.close()
    return "127.0.0.1"


@dataclass
class PeerAnnouncement:
    node_id: str
    host: str
    port: int
    pubkey: str = ""
    protocol_version: str = "1"
    last_seen: float = field(default_factory=time.monotonic)


class DecentralizedPeerDiscovery:
    """Zero-registry LAN peer discovery with automatic join, drop, and rejoin tracking."""

    def __init__(
        self,
        node_id: str,
        mesh_port: int,
        pubkey: str = "",
        advertise_host: Optional[str] = None,
        backend: str = "auto",  # "auto" | "zeroconf" | "multicast"
        mcast_group: str = DEFAULT_MCAST_GROUP,
        mcast_port: int = DEFAULT_MCAST_PORT,
        beacon_interval_s: float = 1.0,
        peer_ttl_s: float = 4.0,
        on_peer_discovered: Optional[Callable[[PeerAnnouncement], None]] = None,
        on_peer_lost: Optional[Callable[[str], None]] = None,
        on_peer_rejoined: Optional[Callable[[PeerAnnouncement], None]] = None,
    ):
        self.node_id = node_id
        self.mesh_port = int(mesh_port)
        self.pubkey = pubkey
        self.advertise_host = advertise_host or detect_lan_ip()
        self.mcast_group = mcast_group
        self.mcast_port = int(mcast_port)
        self.beacon_interval_s = beacon_interval_s
        self.peer_ttl_s = peer_ttl_s

        self.on_peer_discovered = on_peer_discovered
        self.on_peer_lost = on_peer_lost
        self.on_peer_rejoined = on_peer_rejoined

        if backend == "auto":
            self.backend = "zeroconf" if HAS_ZEROCONF else "multicast"
        elif backend == "zeroconf" and not HAS_ZEROCONF:
            raise RuntimeError("zeroconf is not installed; install with `pip install zeroconf`")
        else:
            self.backend = backend

        self._lock = threading.Lock()
        self._peers: Dict[str, PeerAnnouncement] = {}
        self._ever_seen: set[str] = set()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        # Zeroconf state
        self._zc: Any = None
        self._zc_info: Any = None
        self._zc_browser: Any = None

        # Multicast socket state
        self._recv_sock: Optional[socket.socket] = None
        self._send_sock: Optional[socket.socket] = None

    def active_peers(self) -> Dict[str, PeerAnnouncement]:
        with self._lock:
            return dict(self._peers)

    def _handle_peer_seen(self, peer: PeerAnnouncement) -> None:
        if peer.node_id == self.node_id:
            return
        callback: Optional[Callable[[PeerAnnouncement], None]] = None
        with self._lock:
            already_active = peer.node_id in self._peers
            previously_known = peer.node_id in self._ever_seen
            peer.last_seen = time.monotonic()
            self._peers[peer.node_id] = peer
            self._ever_seen.add(peer.node_id)

            if not already_active:
                if previously_known:
                    callback = self.on_peer_rejoined or self.on_peer_discovered
                else:
                    callback = self.on_peer_discovered

        if callback is not None:
            callback(peer)

    def _handle_peer_removed(self, node_id: str) -> None:
        if node_id == self.node_id:
            return
        removed = False
        with self._lock:
            if node_id in self._peers:
                del self._peers[node_id]
                removed = True
        if removed and self.on_peer_lost is not None:
            self.on_peer_lost(node_id)

    def _prune_expired_peers(self) -> None:
        now = time.monotonic()
        expired: list[str] = []
        with self._lock:
            for nid, peer in list(self._peers.items()):
                if (now - peer.last_seen) > self.peer_ttl_s:
                    del self._peers[nid]
                    expired.append(nid)
        for nid in expired:
            if self.on_peer_lost is not None:
                self.on_peer_lost(nid)

    # --- Zeroconf (mDNS / DNS-SD) backend ---

    def _start_zeroconf(self) -> None:
        self._zc = Zeroconf()
        props = {
            "node_id": self.node_id,
            "pubkey": self.pubkey,
            "mesh_port": str(self.mesh_port),
            "protocol_v": "1",
        }
        service_name = f"{self.node_id}.{SERVICE_TYPE}"
        self._zc_info = ServiceInfo(
            SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(self.advertise_host)],
            port=self.mesh_port,
            properties=props,
        )
        self._zc.register_service(self._zc_info)

        parent = self

        class _Listener(ServiceListener):
            def add_service(self, zc: Any, stype: str, name: str) -> None:
                info = zc.get_service_info(stype, name)
                if not info:
                    return
                parsed_props = {
                    (k.decode() if isinstance(k, bytes) else k): (
                        v.decode() if isinstance(v, bytes) else str(v)
                    )
                    for k, v in (info.properties or {}).items()
                }
                nid = parsed_props.get("node_id") or name.split(".")[0]
                addrs = info.parsed_addresses() if hasattr(info, "parsed_addresses") else []
                host = addrs[0] if addrs else "127.0.0.1"
                parent._handle_peer_seen(
                    PeerAnnouncement(
                        node_id=nid,
                        host=host,
                        port=int(parsed_props.get("mesh_port", info.port)),
                        pubkey=parsed_props.get("pubkey", ""),
                        protocol_version=parsed_props.get("protocol_v", "1"),
                    )
                )

            def update_service(self, zc: Any, stype: str, name: str) -> None:
                self.add_service(zc, stype, name)

            def remove_service(self, zc: Any, stype: str, name: str) -> None:
                nid = name.split(".")[0]
                parent._handle_peer_removed(nid)

        self._zc_browser = ServiceBrowser(self._zc, SERVICE_TYPE, _Listener())

    # --- Zero-dependency UDP Multicast / Broadcast backend ---

    def _beacon_payload(self, kind: str = "hello") -> bytes:
        return json.dumps(
            {
                "magic": BEACON_MAGIC,
                "kind": kind,
                "node_id": self.node_id,
                "host": self.advertise_host,
                "port": self.mesh_port,
                "pubkey": self.pubkey,
                "protocol_v": "1",
            },
            separators=(",", ":"),
        ).encode("utf-8")

    def _start_multicast(self) -> None:
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        recv_sock.bind(("", self.mcast_port))

        iface_ip = self.advertise_host or "0.0.0.0"
        mreq = struct.pack("4s4s", socket.inet_aton(self.mcast_group), socket.inet_aton(iface_ip))
        try:
            recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except OSError:
            try:
                mreq_any = struct.pack("4s4s", socket.inet_aton(self.mcast_group), socket.inet_aton("0.0.0.0"))
                recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq_any)
            except OSError:
                pass
        recv_sock.settimeout(0.2)
        self._recv_sock = recv_sock

        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        try:
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(iface_ip))
        except OSError:
            pass
        self._send_sock = send_sock

        t_recv = threading.Thread(target=self._multicast_recv_loop, daemon=True)
        t_send = threading.Thread(target=self._multicast_beacon_loop, daemon=True)
        self._threads = [t_recv, t_send]
        t_recv.start()
        t_send.start()

    def _multicast_recv_loop(self) -> None:
        while not self._stop_event.is_set() and self._recv_sock is not None:
            try:
                data, addr = self._recv_sock.recvfrom(4096)
            except socket.timeout:
                self._prune_expired_peers()
                continue
            except OSError:
                break

            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            if msg.get("magic") != BEACON_MAGIC:
                continue

            nid = str(msg.get("node_id", ""))
            if not nid or nid == self.node_id:
                continue

            if msg.get("kind") == "bye":
                self._handle_peer_removed(nid)
            else:
                host = str(msg.get("host") or addr[0])
                self._handle_peer_seen(
                    PeerAnnouncement(
                        node_id=nid,
                        host=host,
                        port=int(msg["port"]),
                        pubkey=str(msg.get("pubkey", "")),
                        protocol_version=str(msg.get("protocol_v", "1")),
                    )
                )

    def _multicast_beacon_loop(self) -> None:
        hello = self._beacon_payload("hello")
        while not self._stop_event.is_set() and self._send_sock is not None:
            try:
                self._send_sock.sendto(hello, (self.mcast_group, self.mcast_port))
            except OSError:
                pass
            self._stop_event.wait(self.beacon_interval_s)

    def start(self) -> None:
        self._stop_event.clear()
        if self.backend == "zeroconf":
            self._start_zeroconf()
        else:
            self._start_multicast()

    def stop(self) -> None:
        self._stop_event.set()
        if self.backend == "zeroconf":
            if self._zc is not None:
                try:
                    if self._zc_info is not None:
                        self._zc.unregister_service(self._zc_info)
                except Exception:
                    pass
                try:
                    self._zc.close()
                except Exception:
                    pass
                self._zc = None
        else:
            if self._send_sock is not None:
                try:
                    self._send_sock.sendto(self._beacon_payload("bye"), (self.mcast_group, self.mcast_port))
                except OSError:
                    pass
                try:
                    self._send_sock.close()
                except OSError:
                    pass
                self._send_sock = None
            if self._recv_sock is not None:
                try:
                    self._recv_sock.close()
                except OSError:
                    pass
                self._recv_sock = None
            for t in self._threads:
                t.join(timeout=1.0)
            self._threads = []
