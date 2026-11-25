#!/usr/bin/env python3
"""Two-Machine Direct P2P CRDT Mesh Demo (LAN or Internet over NAT — AI-236, AI-237, AI-240).

Works over LAN (automatic mDNS/multicast discovery) OR over the open internet
(RFC 5389 STUN external endpoint discovery + UDP NAT hole-punching + auto return-address learning)
with ZERO Railway relay in the data path.

Usage:
    # Machine A:
    python3 scripts/demo_p2p_two_machines.py --node-id mac-a --port 45454

    # Machine B (pass Machine A's printed Public or LAN IP:port):
    python3 scripts/demo_p2p_two_machines.py --node-id remote-b --port 45454 --peer <A_IP>:<A_PORT>
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
    parser = argparse.ArgumentParser(description="TinCan Direct P2P Two-Machine CRDT Demo (LAN & Internet)")
    parser.add_argument("--node-id", required=True, help="Unique node ID (e.g. mac-a, remote-b)")
    parser.add_argument("--bind", default="0.0.0.0", help="Local interface IP to bind (e.g. Wi-Fi IP or iPhone USB IP)")
    parser.add_argument("--port", type=int, default=45454, help="Local UDP port to bind")
    parser.add_argument("--peer", default="", help="Optional peer host:port (LAN or public STUN endpoint)")
    parser.add_argument("--no-stun", action="store_true", help="Skip STUN public IP discovery (offline LAN)")
    parser.add_argument("--no-discovery", action="store_true", help="Disable LAN mDNS/multicast (force direct WAN/NAT path)")
    parser.add_argument("--duration", type=int, default=60, help="Seconds to run demo")
    args = parser.parse_args()

    identity = TinCanIdentity.generate()
    trust = TrustStore(trust_on_first_use=True)
    transport = MultiPeerUDPTransport(bind_host=args.bind, bind_port=args.port)
    mesh = CRDTMeshGossipSync(args.node_id, transport=transport, identity=identity, trust_store=trust)

    public_ep = None if args.no_stun else transport.discover_public_endpoint()

    explicit_peer = None
    if args.peer:
        host, port_s = args.peer.rsplit(":", 1)
        explicit_peer = (host, int(port_s))
        transport.add_peer("explicit-peer", host, int(port_s))
        transport.send_punch(host, int(port_s), local_node_id=args.node_id)

    def _on_peer(peer: PeerAnnouncement) -> None:
        transport.add_peer(peer.node_id, peer.host, peer.port)
        if peer.pubkey:
            trust.add_peer(peer.node_id, peer.pubkey)
        print(f"[discovery] Joined LAN peer {peer.node_id} at {peer.host}:{peer.port}")

    discovery = None
    if not args.no_discovery:
        discovery = DecentralizedPeerDiscovery(
            node_id=args.node_id,
            mesh_port=transport.bound_port,
            pubkey=identity.address,
            on_peer_discovered=_on_peer,
        )
        discovery.start()

    print("=" * 68)
    print(f"[*] Node ID   : {args.node_id} ({identity.address})")
    bind_display = args.bind if args.bind != "0.0.0.0" else detect_lan_ip()
    print(f"[*] Local UDP : {bind_display}:{transport.bound_port}")
    if public_ep:
        print(f"[*] Public UDP: {public_ep[0]}:{public_ep[1]}  <-- pass to --peer on remote machine")
    else:
        print("[*] Public UDP: (STUN unavailable / offline LAN mode)")
    print("[*] Zero Railway relay in path. Exchanging signed CRDT deltas...")
    print("=" * 68)

    start = time.time()
    step = 0
    try:
        while (time.time() - start) < args.duration:
            step += 1
            if explicit_peer:
                transport.send_punch(explicit_peer[0], explicit_peer[1], local_node_id=args.node_id)

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
                f"tx={transport.stats.bytes_sent}B rx={transport.stats.bytes_received}B"
            )
            time.sleep(2.0)
    finally:
        if discovery is not None:
            discovery.stop()
        transport.close()


if __name__ == "__main__":
    main()
