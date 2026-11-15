"""WebRTC UDP Peer Video, Voice & Screensharing Signaling Relay Service."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class PeerSession:
    peer_id: str
    display_name: str
    udp_address: str = "redacted"
    udp_port: int = 50000
    connected_at: float = 0.0
    last_seen: float = 0.0
    active_stream: bool = True
    room: str = "main"
    has_video: bool = False
    has_audio: bool = False
    has_screen: bool = False

    def to_dict(self, now: Optional[float] = None, stale_after: float = 60.0) -> Dict[str, Any]:
        ts = time.time() if now is None else now
        seen = self.last_seen or self.connected_at or 0.0
        has_live_media = bool(self.has_video or self.has_audio or self.has_screen)
        is_online = bool(self.active_stream and (seen <= 0.0 or (ts - seen) <= stale_after))
        data = asdict(self)
        data["last_seen"] = seen
        data["is_online"] = is_online
        data["has_live_media"] = has_live_media
        return data


class WebRTCSignalingRelay:
    """Manages WebRTC SDP offers/answers, ICE candidates, rooms, and low-latency UDP streams."""

    def __init__(self, stale_after: float = 60.0):
        self._lock = threading.Lock()
        self.peers: Dict[str, PeerSession] = {}
        self.signaling_messages: List[Dict[str, Any]] = []
        self._next_seq: int = 1
        self.stale_after: float = float(stale_after)

    def _serialize_peers(self, now: float, room: Optional[str] = None) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        target_room = (room or "main") if room is not None else None
        for p in self.peers.values():
            if not p.active_stream:
                continue
            if target_room is not None and p.room != target_room:
                continue
            serialized = p.to_dict(now=now, stale_after=self.stale_after)
            if serialized["is_online"]:
                result.append(serialized)
        return result

    def register_peer(
        self,
        peer_id: str,
        display_name: str,
        udp_address: str = "redacted",
        udp_port: int = 50000,
        room: str = "main",
        has_video: bool = False,
        has_audio: bool = False,
        has_screen: bool = False,
    ) -> PeerSession:
        with self._lock:
            now = time.time()
            # Privacy Guard: Never store or expose raw client IP addresses in PeerSession
            session = PeerSession(
                peer_id=peer_id,
                display_name=display_name,
                udp_address="redacted",
                udp_port=int(udp_port),
                connected_at=now,
                last_seen=now,
                active_stream=True,
                room=room or "main",
                has_video=bool(has_video),
                has_audio=bool(has_audio),
                has_screen=bool(has_screen),
            )
            self.peers[peer_id] = session
            return session

    def leave_peer(self, peer_id: str) -> bool:
        with self._lock:
            if peer_id in self.peers:
                self.peers[peer_id].active_stream = False
                return True
            return False

    def touch_peer(self, peer_id: str) -> None:
        with self._lock:
            if peer_id in self.peers and self.peers[peer_id].active_stream:
                self.peers[peer_id].last_seen = time.time()

    def exchange_signal(
        self,
        sender_id: str,
        receiver_id: str,
        signal_type: str,
        sdp_or_candidate: Dict[str, Any],
        room: str = "main",
    ) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            if sender_id in self.peers and self.peers[sender_id].active_stream:
                self.peers[sender_id].last_seen = now
            seq = self._next_seq
            self._next_seq += 1
            msg = {
                "seq": seq,
                "from": sender_id,
                "to": receiver_id,
                "room": room or "main",
                "type": signal_type,  # "offer", "answer", "candidate", "hangup", "ping", "pong", "chat"
                "payload": sdp_or_candidate,
                "timestamp": now,
            }
            self.signaling_messages.append(msg)
            # Keep bounded buffer of recent 1000 signaling messages
            if len(self.signaling_messages) > 1000:
                self.signaling_messages = self.signaling_messages[-1000:]
            return msg

    def poll_signals(
        self,
        receiver_id: str,
        room: str = "main",
        since_seq: int = 0,
    ) -> Dict[str, Any]:
        """Return queued SDP offers/answers and ICE candidates for receiver_id or broadcast in room."""
        with self._lock:
            now = time.time()
            if receiver_id in self.peers and self.peers[receiver_id].active_stream:
                self.peers[receiver_id].last_seen = now
            matched = [
                m
                for m in self.signaling_messages
                if m["seq"] > since_seq
                and m.get("from") != receiver_id
                and m.get("room", "main") == (room or "main")
                and (m.get("to") in (receiver_id, "*", "room", None, ""))
            ]
            latest_seq = self._next_seq - 1
            room_peers = self._serialize_peers(now=now, room=room or "main")
            return {
                "room": room or "main",
                "receiver_id": receiver_id,
                "latest_seq": latest_seq,
                "signals": matched,
                "peers": room_peers,
            }

    def get_room_peers(self, room: str = "main") -> List[Dict[str, Any]]:
        with self._lock:
            return self._serialize_peers(now=time.time(), room=room or "main")

    def get_active_streams(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self._serialize_peers(now=time.time(), room=None)
