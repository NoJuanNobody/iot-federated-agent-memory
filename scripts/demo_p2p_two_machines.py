#!/usr/bin/env python3
"""Two-Machine Direct P2P CRDT Mesh Demo (AI-236, AI-237, AI-240).

Run on Machine A (e.g., Mac):
    python3 scripts/demo_p2p_two_machines.py --node-id mac-a --port 45454

Run on Machine B (e.g., Raspberry Pi or laptop on the same LAN):
    python3 scripts/demo_p2p_two_machines.py --node-id pi-b --port 45455 --peer <MAC_LAN_IP>:45454

Or omit --peer on both machines to use automatic decentralized LAN discovery (mDNS/multicast).
"""

import argparse
import time

from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, TrustStore
from iot_federated_agent_memory.mdns_discovery import (
    DecentralizedPeerDiscovery,
    PeerAnnouncement,
    detect_lan_ip,
)
from iot_federated_agent_memory.p2p_transport import MultiPeerUDPTransport
from iot_federated_agent_memory.tincan_core import TinCanIdentity


def main() -> None:
    parser = argparse.ArgumentParser(description="TinCan Direct P2P Two-Machine CRDT Demo")
    parser.add_argument("--node-id", required=True, help="Unique node ID (e.g. mac-a, pi-b)")
    parser.add_argument("--port", type=int, default=45454, help="Local UDP port to bind")
    parser.add_argument("--peer", default="", help="Optional explicit peer host:port (else auto-discover)")
    parser.add_argument("--duration", type=int, default=30, help="Seconds to run demo")
    args = parser.parse_args()

    identity = TinCanIdentity.generate()
    trust = TrustStore(trust_on_first_use=True)
    transport = MultiPeerUDPTransport(bind_host="0.0.0.0", bind_port=args.port)
    mesh = CRDTMeshGossipSync(args.node_id, transport=transport, identity=identity, trust_store=trust)

    if args.peer:
        host, port_s = args.peer.rsplit(":", 1)
        transport.add_peer("explicit-peer", host, int(port_s))

    def _on_peer(peer: PeerAnnouncement) -> None:
        transport.add_peer(peer.node_id, peer.host, peer.port)
        if peer.pubkey:
            trust.add_peer(peer.node_id, peer.pubkey)
        print(f"[discovery] Joined peer {peer.node_id} at {peer.host}:{peer.port}")

    discovery = DecentralizedPeerDiscovery(
        node_id=args.node_id,
        mesh_port=transport.bound_port,
        pubkey=identity.address,
        on_peer_discovered=_on_peer,
    )
    discovery.start()

    print(f"[*] {args.node_id} listening on {detect_lan_ip()}:{transport.bound_port} ({identity.address})")
    print(f"[*] Zero Railway relay in path. Exchanging signed CRDT deltas for {args.duration}s...")

    start = time.time()
    step = 0
    try:
        while (time.time() - start) < args.duration:
            step += 1
            mesh.apply_local_update(
                f"heartbeat:{args.node_id}",
                {"step": step, "node": args.node_id, "ts": round(time.time(), 2)},
            )
            merged = mesh.process_incoming_transport(ignore_auth_errors=True)
            for d in merged:
                print(f"[recv] verified Ed25519 delta from {d.node_id}: {d.key}={d.value}")
            print(
                f"[state] peers={len(transport.peers)} keys={len(mesh.state_store)} "
                f"merkle_root={mesh.compute_merkle_root()[:12]} "
                f"bytes_tx={transport.stats.bytes_sent} bytes_rx={transport.stats.bytes_received}"
            )
            time.sleep(2.0)
    finally:
        discovery.stop()
        transport.close()


if __name__ == "__main__":
    main()
