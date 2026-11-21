# Paper Figures Index & Captions

All figures are monochrome, print-ready vector SVGs (`#ffffff` background, `#111111` primary ink, `#555555` secondary strokes, `#f4f4f4` fills) designed for direct inclusion in the TinCan Federated Agent Memory research paper.

## Architecture, Protocol, and Wireframe Figures (`docs/paper/figures/`)

| Figure | File | Caption |
| --- | --- | --- |
| **Figure 1** | [`fig1_architecture.svg`](./fig1_architecture.svg) | **TinCan Federated Agent Memory: Zero-Relay Edge Mesh Architecture.** Three heterogeneous edge nodes (Workstation Mac, Raspberry Pi ARM64, and Field Laptop) each host a local `FederatedAgentKnowledgeGraph` (`LWWMap` entities, `ORSet` relations/index, `MVRegister` decisions), `CRDTMeshGossipSync` with a 16-way depth-3 `PrefixMerkleTree`, `VectorClock`/`HLC`, and `TinCanIdentity` (Ed25519 + `TrustStore`), communicating over a zero-relay P2P layer (`MultiPeerUDPTransport` with SAR/STUN, `DecentralizedPeerDiscovery` via mDNS/multicast, and optional `ReticulumTransportChannel`). |
| **Figure 2** | [`fig2_sync_sequence.svg`](./fig2_sync_sequence.svg) | **Partitioned Knowledge Graph Sync & Conflict Resolution Sequence.** End-to-end synchronization between `agent-mac-backend` and `agent-pi-tests` across a network partition: initial Merkle parity, offline concurrent mutations (`LWWMap` fields, `ORSet` edges, conflicting `MVRegister` decision), peer rejoin, Ed25519 signature verification via `TrustStore`, 16-way `PrefixMerkleTree` subtree diffing, targeted delta exchange, explicit conflict surfacing and resolution, and restored Merkle parity. |
| **Figure 3** | [`fig3_mesh_state_view.svg`](./fig3_mesh_state_view.svg) | **Local Mesh State Inspector — Monochrome Wireframe View.** Read-only diagnostic wireframe displaying the 3-node peer-to-peer topology map, per-node `tc:<base32>` Ed25519 `TrustStore` verification badges, `VectorClock`/`HLC` status, `PrefixMerkleTree` root-hash parity indicator, replicated `FederatedAgentKnowledgeGraph` state, and the live `MVRegister` conflict inspector. |

## Experimental Evaluation Figures (`docs/paper/results/`)

| Figure | File | Caption |
| --- | --- | --- |
| **Figure 4** | [`../results/fig_bytes_vs_nodes.svg`](../results/fig_bytes_vs_nodes.svg) | **Sync Bandwidth per Peer Exchange vs. Mesh Size ($N$).** Comparison of per-sync wire transfer (KB) across $N \in \{3, 5, 10, 25\}$ edge nodes for TinCan Merkle-CRDT anti-entropy, naive full-state gossip, and central-server sync, achieving a 94.43% bandwidth reduction at $N=25$ (3,589 B vs. 64,430 B). |
| **Figure 5** | [`../results/fig_convergence_vs_loss.svg`](../results/fig_convergence_vs_loss.svg) | **Convergence Latency vs. UDP Packet Loss Rate.** Mesh convergence time across 0%–30% simulated packet loss at 25 ms RTT, demonstrating resilient delta convergence under degraded edge links. |
| **Figure 6** | [`../results/fig_lost_writes_vs_partition.svg`](../results/fig_lost_writes_vs_partition.svg) | **Lost Writes Across Network Partitions.** Comparison of silently overwritten concurrent updates under network partitions, showing 0 lost writes and 42 surfaced conflicts for TinCan's `MVRegister`/`ORSet`/`LWWMap` CRDTs versus 84 lost writes on LWW and central-server baselines. |
