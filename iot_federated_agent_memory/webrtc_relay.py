"""WebRTC UDP Peer Screensharing and Signaling Relay Service."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class PeerSession:
    peer_id: str
    display_name: str
    udp_address: str
    udp_port: int
    connected_at: float
    active_stream: bool


class WebRTCSignalingRelay:
    """Manages WebRTC SDP offers/answers, ICE candidates, and low-latency UDP streams."""

    def __init__(self):
        self.peers: Dict[str, PeerSession] = {}
        self.signaling_messages: List[Dict[str, Any]] = []

    def register_peer(self, peer_id: str, display_name: str, udp_address: str = "127.0.0.1", udp_port: int = 50000) -> PeerSession:
        session = PeerSession(
            peer_id=peer_id,
            display_name=display_name,
            udp_address=udp_address,
            udp_port=udp_port,
            connected_at=time.time(),
            active_stream=True,
        )
        self.peers[peer_id] = session
        return session

    def exchange_signal(self, sender_id: str, receiver_id: str, signal_type: str, sdp_or_candidate: Dict[str, Any]) -> Dict[str, Any]:
        msg = {
            "from": sender_id,
            "to": receiver_id,
            "type": signal_type,  # "offer", "answer", "candidate"
            "payload": sdp_or_candidate,
            "timestamp": time.time(),
        }
        self.signaling_messages.append(msg)
        return msg

    def get_active_streams(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.peers.values() if p.active_stream]
