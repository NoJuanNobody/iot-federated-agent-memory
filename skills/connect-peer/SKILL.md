---
name: connect-peer
description: >-
  Connect this computer to the live IoT Federated Agent Mesh, WebRTC UDP screensharing relay,
  shared Obsidian brain, and dynamic AI token gateway on Railway. Trigger with natural phrases
  like "connect peer", "join mesh", "link to friend", "start screen share", or "/connect-peer".
---

# Connect Peer Skill (`connect-peer`)

Seamlessly handshakes with the live Railway mesh relay (`https://iot-federated-agent-memory-production.up.railway.app`), announces this machine's presence, registers WebRTC UDP low-latency screen channels, and synchronizes shared skills and AI token pools.

## Quick Trigger Phrases
- "connect peer"
- "connect to friend's computer"
- "join mesh"
- "start peer screen share"
- "/connect-peer"

## Execution Runbook

When invoked, the agent should run:

```bash
python3 "$HOME/dev/iot-federated-agent-memory/connect_peer.py" \
  --peer-id "$(whoami)-$(hostname -s)" \
  --display-name "$(whoami) Workstation"
```

And verify the live dashboard status at `https://iot-federated-agent-memory-production.up.railway.app/api/status`.
