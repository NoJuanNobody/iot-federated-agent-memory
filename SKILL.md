---
name: iot-federated-agent-memory
description: Evaluate, benchmark, and orchestrate Multi-Account Gemini Harvester pooling, Antigravity collaborator memory/file synchronization, Grok (xAI/MCP) bidirectional bridges, and the L1-L5 Internet of Things (IoT) Federated Edge Memory Readiness Scale.
---

# IoT Federated Agent Memory & Readiness Scale (`iot-federated-agent-memory`)

Unifies everything built in the **Multi-Account Gemini + Antigravity Collaborators + Grok Shared Memory Setup** and establishes the **L1–L5 IoT Federated Agent Memory Evaluation Scale** for the future Internet of Things research roadmap.

## 1. Completed Foundation (100% Built & Verified)
1. **Multi-Account Gemini Harvesting (`D1_MULTI_ACCOUNT_GEMINI_HARVEST`)**:
   - Uses `MultiAccountHarvester` (`gemini-activity-harvester sync-accounts`) to pool and deduplicate prompts, shared Gemini app URLs, and model responses across multiple Google accounts into `vault_data/gemini_accounts/`.
2. **Antigravity Collaborator Memory & File Sync (`D2_ANTIGRAVITY_COLLAB_MEMORY`)**:
   - Uses `SharedCollaboratorHub` and `AtomicTrajectoryGraphImporter` to synchronize `AGENTS.md`, `GEMINI.md`, and sanitized collaborator trajectories (`transcript_full.jsonl`) into a Merkle-verified Obsidian Vault (`shared_hub_manifest.json`).
3. **Grok Bidirectional Memory & File Bridge (`D3_GROK_BIDIRECTIONAL_BRIDGE`)**:
   - Uses `GrokBridgeAdapter` (`vault-paywall shared-sync`) to connect Antigravity collaborators with Grok via `https://api.x.ai/v1/chat/completions`, `mcp_shared_hub_config.json`, and portable `grok_workspace_bundle.md` handoffs.

## 2. Future IoT Research Scale Dimensions (L1–L5)
- **D4 (`D4_IOT_MQTT_EDGE_TELEMETRY`)**: MQTT / CoAP / Matter sensor stream ingestion into atomic Vault GraphRAG telemetry nodes.
- **D5 (`D5_IOT_CRDT_MESH_GOSSIP`)**: Offline-first CRDT mesh gossip and SHA-256 Merkle delta synchronization across intermittent IoT edge nodes (ESP32, Raspberry Pi, Jetson).
- **D6 (`D6_IOT_HARDWARE_ACTUATION_GUARDRAILS`)**: Deterministic `no_std` DFA safety guardrails and `remote-control-skill` HITL checkpoints prior to physical IoT actuation.

## CLI Usage

```bash
# Run the IoT Federated Memory & Readiness Scale audit
PYTHONPATH=/Users/alejandrolondono/dev/iot-federated-agent-memory python3 -m iot_federated_agent_memory.cli
```
