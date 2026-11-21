# Edge Deployment Strategy (AI-244)

TinCan separates its research-grade decentralized agent memory plane from the full workstation/server stack so constrained edge devices (Raspberry Pi 3/4/5, ARM64 single-board computers, and air-gapped field laptops) can participate in the CRDT knowledge-graph mesh with minimal memory, disk, and dependency overhead.

## 1. Slim Node Installation (`Dockerfile.edge` & `install_peer.sh`)

### Containerized Slim Edge Build (`Dockerfile.edge`)
Unlike the full server `Dockerfile` (which bundles Node.js, Rust, Linuxbrew, Playwright/Chromium, WebAuthn, and UI modules), `Dockerfile.edge` builds directly on `python:3.11-slim` with **zero C/C++ build toolchain** and installs only:
- **`PyNaCl>=1.5.0`** (ships prebuilt `x86_64` and `aarch64` wheels with bundled `libsodium` for Ed25519/X25519 cryptography), and
- **Optional `zeroconf>=0.131.0`** (controlled via `--build-arg INSTALL_ZEROCONF=1`, set to `0` for zero-mDNS air-gapped multicast-only images).

Only the 8 core CRDT/P2P modules (`crdt_types.py`, `merkle_tree.py`, `tincan_core.py`, `crdt_mesh.py`, `p2p_transport.py`, `mdns_discovery.py`, `agent_kg_crdt.py`, and `local_p2p_mesh.py`) are copied into `/app`, running as an unprivileged `tincan` user with `local_p2p_mesh.py` as the container `ENTRYPOINT`:

```bash
# Standard LAN edge image (PyNaCl + zeroconf mDNS)
docker build -f Dockerfile.edge -t tincan-edge:latest .

# Ultra-minimal air-gapped image (PyNaCl only; uses built-in UDP multicast beacon)
docker build -f Dockerfile.edge --build-arg INSTALL_ZEROCONF=0 -t tincan-edge:multicast .

# Run with host networking for automatic LAN discovery on UDP 45454 / 5353 / 5354
docker run --rm --network host tincan-edge:latest --node-id pi-edge-01 --port 45454
```

### Bare-Metal Workstation / SBC Bootstrap (`install_peer.sh`)
For bare-metal Linux and macOS edge peers, `install_peer.sh` clones the repository (with automatic mirror fallback), installs `PyNaCl` into the local Python environment, links the `tincan` CLI into `~/.local/bin`, and gates skill registration behind a live `tincan --help` binary verification check. Alternatively, minimal Python environments can install directly from `pyproject.toml`:

```bash
pip install -e ".[p2p]"        # Core PyNaCl + zeroconf LAN discovery
pip install -e ".[disaster]"   # Core PyNaCl + zeroconf + Reticulum (rns) off-grid radio
```

## 2. Measured Edge Runtime Footprint

Real runtime measurements were collected via `PYTHONPATH=. python3 scripts/measure_edge_footprint.py` and persisted in [`docs/paper/results/edge_footprint.json`](results/edge_footprint.json). The benchmark starts two real `FederatedAgentKnowledgeGraph` nodes backed by `MultiPeerUDPTransport` (AF_INET/SOCK_DGRAM loopback sockets) and `TinCanIdentity` (Ed25519 signatures enforced via `TrustStore`), executes a **200-key CRDT workload** (190 entities, 69 directed relations, 8 `MVRegister` decisions with 3 deliberate concurrent partition conflicts), and reconciles across a simulated partition via `PrefixMerkleTree` anti-entropy.

| Metric | Measured Value | Notes |
| --- | --- | --- |
| **Slim CRDT + P2P Code Footprint** | **118.42 KB** (121,266 B across 8 files) | **96.88% reduction** vs. full server + package (3,793.17 KB) |
| **Peak / Post-Workload RSS Memory** | **51.47 MB** (baseline 32.31 MB; delta +19.16 MB) | Measured via `resource.getrusage` and `ps` hosting 2 in-process nodes |
| **Workload CPU Time** | **1,055.86 ms** (1,033.51 ms user, 22.37 ms sys) | 1,079.15 ms wall-clock for 200 signed keys + partition recovery |
| **UDP Loopback Traffic** | **2,316,391 B** TX / **2,316,391 B** RX | 2,228 datagrams; 383 SAR messages fragmented & reassembled |
| **Post-Reconnect Merkle Anti-Entropy** | **128 B** exchanged | Exact `PrefixMerkleTree` root parity verified across both nodes |
| **Conflicts Surfaced** | **3 / 3** concurrent `MVRegister` decisions | Zero lost writes; Ed25519 signature verification enforced |

These figures confirm that a single slim edge node fits comfortably inside a 64–128 MB RAM budget (e.g., Raspberry Pi Zero 2 W or older ARM SBCs) with sub-120 KB of application code.

## 3. Zero-Config LAN Join (`mdns_discovery.py` + `MultiPeerUDPTransport`)

When `local_p2p_mesh.py` starts, it binds `MultiPeerUDPTransport` (default UDP port `45454`, 1,400-byte MTU with automatic 12-byte SAR fragmentation/reassembly) and launches `DecentralizedPeerDiscovery` with `--backend auto`:

1. **Primary (mDNS / DNS-SD):** When `zeroconf` is installed, nodes advertise `_tincan-mesh._udp.local.` with TXT records carrying `node_id`, `mesh_port`, `pubkey` (`tc:<base32>` Ed25519 address), and `protocol_v`.
2. **Fallback (Zero-Dependency Multicast):** When `zeroconf` is absent (e.g., `INSTALL_ZEROCONF=0` air-gapped builds), `DecentralizedPeerDiscovery` automatically falls back to a stdlib-only UDP multicast beacon on `239.255.77.88:5354` (`TINCAN-DISC-V1`) with 1-second heartbeats and 4-second TTL expiry.
3. **Automatic Join / Drop / Rejoin:** Discovering a peer registers its UDP endpoint in `MultiPeerUDPTransport` and pins its Ed25519 key in `TrustStore`. When a partitioned peer returns, `on_peer_rejoined` flushes queued offline deltas and triggers `PrefixMerkleTree` parity reconciliation with zero central registry.

## 4. STUN / UDP Internet Peering

To federate edge nodes across separate NATs without placing a central relay in the data path, `MultiPeerUDPTransport` implements lightweight RFC 5389 STUN and UDP hole-punching (demonstrated end-to-end in `scripts/demo_p2p_two_machines.py`):

1. **External Endpoint Discovery:** `discover_public_endpoint()` sends an RFC 5389 Binding Request from the **same bound UDP socket** to public STUN servers (`stun.l.google.com:19302`, `stun.cloudflare.com:3478`) and parses `XOR-MAPPED-ADDRESS` / `MAPPED-ADDRESS` to learn the node's external `public_ip:public_port`.
2. **NAT Hole-Punching & Return-Address Learning:** Both peers exchange `PACKET_TYPE_PUNCH` (`0x03`) datagrams via `send_punch(host, port, local_node_id)` to open outbound NAT pinholes. Upon receiving a punch packet, the remote transport records the sender's reflexive `(ip, port)` directly into `self.peers`, enabling bidirectional Ed25519-signed CRDT gossip directly over UDP.

## 5. Off-Grid Radio Option (Reticulum Network Stack)

For disaster zones, rural deployments, or RF-only environments without IP connectivity, `p2p_transport.py` provides `ReticulumTransportChannel` targeting the optional `rns>=0.8.0` stack (`pip install -e ".[disaster]"`):
- Uses Reticulum's **464-byte** single-packet encrypted payload ceiling as its channel MTU, allowing TinCan's compact CRDT deltas and 16-way `PrefixMerkleTree` digests to traverse LoRa (RNode), VHF/UHF packet radio, and serial links.
- Preserves the same `MeshTransportChannel` interface (`connect`, `disconnect`, `send`, `receive`) so upper-layer `CRDTMeshGossipSync` and `FederatedAgentKnowledgeGraph` logic remains transport-agnostic.

## 6. Package Distribution & Security-Hardened Updates

- **Zero-RCE Update Posture:** Unattended remote `curl | bash` auto-upgrades are **permanently disabled** in `iot_federated_agent_memory/auto_upgrade.py` (`check_and_auto_upgrade()` unconditionally returns `False`) to eliminate supply-chain remote code execution risk on autonomous edge devices.
- **Reproducible Upgrades:** Operators upgrade edge nodes explicitly through immutable container image digests (`Dockerfile.edge`), pinned Python wheel/package releases (`pyproject.toml` extras `[p2p]` / `[disaster]`), or versioned Homebrew formula updates (`Formula/tincan.rb`), preserving local Ed25519 identities and CRDT state across restarts.
