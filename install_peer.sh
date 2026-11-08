#!/usr/bin/env bash
# ==============================================================================
# Install Peer Mesh & Register "connect-peer" Natural Language Skill
# Usage: curl -sSL https://raw.githubusercontent.com/NoJuanNobody/iot-federated-agent-memory/main/install_peer.sh | bash
# Or run locally: ./install_peer.sh
# ==============================================================================

set -e

REPO_URL="https://github.com/NoJuanNobody/iot-federated-agent-memory.git"
INSTALL_DIR="$HOME/dev/iot-federated-agent-memory"
SKILLS_DIR="$HOME/.gemini/config/skills/connect-peer"
AGENTS_SKILLS_DIR="$HOME/.agents/skills/connect-peer"

echo "=========================================================="
echo "[*] Installing IoT Federated Agent Mesh & Peer Connector"
echo "=========================================================="

# 1. Ensure dev directory exists
mkdir -p "$HOME/dev"

# 2. Clone or pull latest repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[+] Updating existing repository in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --rebase origin main || true
else
    echo "[+] Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 3. Make python connection script executable
chmod +x "$INSTALL_DIR/connect_peer.py"

# 4. Install the "connect-peer" natural language skill into Antigravity
echo "[+] Registering 'connect-peer' natural language skill..."
mkdir -p "$SKILLS_DIR"
mkdir -p "$AGENTS_SKILLS_DIR"

cat << 'EOF' > "$SKILLS_DIR/SKILL.md"
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
EOF

# Mirror to .agents/skills for local project discovery
cp "$SKILLS_DIR/SKILL.md" "$AGENTS_SKILLS_DIR/SKILL.md"

# 5. Run initial handshake verification
echo "[+] Performing initial test handshake with live Railway relay..."
python3 "$INSTALL_DIR/connect_peer.py" \
  --peer-id "$(whoami)-$(hostname -s)" \
  --display-name "$(whoami) Workstation"

echo ""
echo "=========================================================="
echo "✓ Installation Complete!"
echo "Your friend can now simply say to their agent:"
echo "  \"connect peer\""
echo "  \"connect to friend's computer\""
echo "  \"join mesh\""
echo "=========================================================="
