#!/usr/bin/env python3
"""
Decentralized Local P2P Mesh Node (LAN mDNS / Multicast + Multi-Peer UDP CRDT).
Runs entirely locally with zero Railway or central registry dependency (AI-236, AI-237).
"""

import argparse
import signal
import sys
import time

from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, TrustStore
from iot_federated_agent_memory.mdns_discovery import (
    DecentralizedPeerDiscovery,
    PeerAnnouncement,
    detect_lan_ip,
)
from iot_federated_agent_memory.p2p_transport import MultiPeerUDPTransport
from iot_federated_agent_memory.tincan_core import TinCanIdentity

DEFAULT_LOCAL_PORT = 45454


def get_local_ip() -> str:
    return detect_lan_ip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Decentralized Local P2P CRDT Mesh Node")
    parser.add_argument("--node-id", default=f"tincan-{int(time.time()) % 10000}", help="Unique node ID")
    parser.add_argument("--port", type=int, default=DEFAULT_LOCAL_PORT, help="UDP mesh port to bind (0=ephemeral)")
    parser.add_argument("--bind", default="0.0.0.0", help="Bind host address")
    parser.add_argument("--backend", choices=["auto", "zeroconf", "multicast"], default="auto")
    args = parser.parse_args()

    identity = TinCanIdentity.generate()
    trust = TrustStore(trust_on_first_use=True)
    transport = MultiPeerUDPTransport(bind_host=args.bind, bind_port=args.port)
    mesh = CRDTMeshGossipSync(args.node_id, transport=transport, identity=identity, trust_store=trust)

    def _on_peer(peer: PeerAnnouncement) -> None:
        transport.add_peer(peer.node_id, peer.host, peer.port)
        if peer.pubkey:
            trust.add_peer(peer.node_id, peer.pubkey)
        print(f"[+] Discovered peer: {peer.node_id} @ {peer.host}:{peer.port}")

    def _on_lost(nid: str) -> None:
        transport.remove_peer(nid)
        print(f"[-] Peer dropped: {nid}")

    def _on_rejoin(peer: PeerAnnouncement) -> None:
        _on_peer(peer)
        mesh.flush_offline_queue()
        print(f"[*] Peer rejoined (flushed offline queue): {peer.node_id}")

    discovery = DecentralizedPeerDiscovery(
        node_id=args.node_id,
        mesh_port=transport.bound_port,
        pubkey=identity.address,
        backend=args.backend,
        on_peer_discovered=_on_peer,
        on_peer_lost=_on_lost,
        on_peer_rejoined=_on_rejoin,
    )
    discovery.start()

    local_ip = detect_lan_ip()
    print("=" * 64)
    print(f"[*] DECENTRALIZED TINCAN CRDT MESH NODE ACTIVE (NO CENTRAL SERVER)")
    print(f"[*] Node ID   : {args.node_id}")
    print(f"[*] Identity  : {identity.address}")
    print(f"[*] UDP Mesh  : {local_ip}:{transport.bound_port}")
    print(f"[*] Discovery : {discovery.backend} (automatic LAN peer join/rejoin)")
    print("=" * 64)

    running = True

    def _handle_sig(_sig, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    try:
        while running:
            merged = mesh.process_incoming_transport(ignore_auth_errors=True)
            for d in merged:
                print(f"[sync] {d.node_id} -> {d.key} (root={mesh.compute_merkle_root()[:12]})")
            time.sleep(0.1)
    finally:
        discovery.stop()
        transport.close()
        print("\n[*] Mesh node stopped cleanly.")


if __name__ == "__main__":
    main()
