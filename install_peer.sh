#!/usr/bin/env bash
# ==============================================================================
# Install Peer Mesh & Register "connect-peer" Natural Language Skill
# Usage: curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash
# Or: wget -qO- https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash
# Or run locally: ./install_peer.sh
# ==============================================================================

set -e

RELAY_URL="${RELAY_URL:-https://iot-federated-agent-memory-production.up.railway.app}"
INSTALL_DIR="$HOME/dev/iot-federated-agent-memory"
SKILLS_DIR="$HOME/.gemini/config/skills/connect-peer"
AGENTS_SKILLS_DIR="$HOME/.agents/skills/connect-peer"

echo "=========================================================="
echo "[*] Installing IoT Federated Agent Mesh & Peer Connector"
echo "=========================================================="

# 1. Ensure dev directory exists
mkdir -p "$HOME/dev"

# 2. Download and unpack project bundle from live Railway relay (no GitHub account required)
echo "[+] Fetching project bundle from $RELAY_URL..."
TMP_ARCHIVE=$(mktemp /tmp/iot_bundle_XXXXXX.tar.gz)
if command -v curl >/dev/null 2>&1; then
    curl -sSL "$RELAY_URL/download/bundle.tar.gz" -o "$TMP_ARCHIVE"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMP_ARCHIVE" "$RELAY_URL/download/bundle.tar.gz"
else
    echo "[-] Error: Neither curl nor wget found on this system."
    exit 1
fi

mkdir -p "$INSTALL_DIR"
tar -xzf "$TMP_ARCHIVE" -C "$HOME/dev"
rm -f "$TMP_ARCHIVE"

# 3. Make executables runnable and install global `tincan` CLI
chmod +x "$INSTALL_DIR/connect_peer.py"
chmod +x "$INSTALL_DIR/tincan_cli.py"

mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/tincan_cli.py" "$HOME/.local/bin/tincan"
chmod +x "$HOME/.local/bin/tincan"
echo "[+] Linked global 'tincan' command -> $HOME/.local/bin/tincan"

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
