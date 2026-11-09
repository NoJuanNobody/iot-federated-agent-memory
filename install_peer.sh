#!/usr/bin/env bash
# ==============================================================================
# TinCan 2.2 CLI & Skills Installer (Zero PII / Safe GitHub Clone)
# Usage: curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash
# ==============================================================================
set -e

REPO_URL="https://github.com/NoJuanNobody/iot-federated-agent-memory.git"
INSTALL_DIR="$HOME/dev/iot-federated-agent-memory"
SKILLS_DIR="$HOME/.gemini/config/skills/connect-peer"
AGENTS_SKILLS_DIR="$HOME/.agents/skills/connect-peer"

echo "=========================================================="
echo "[*] Installing TinCan 2.2 Mesh OS & Peer Connector"
echo "=========================================================="

# 1. Ensure dev directory exists
mkdir -p "$HOME/dev"

# 2. Clone or update repository from GitHub
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[+] Updating existing repository in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --rebase origin main || true
elif [ ! -d "$INSTALL_DIR" ]; then
    echo "[+] Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 3. Link global 'tincan' executable to ~/.local/bin
mkdir -p "$HOME/.local/bin"
if [ -f "$INSTALL_DIR/tincan_cli.py" ]; then
    chmod +x "$INSTALL_DIR/tincan_cli.py"
    ln -sf "$INSTALL_DIR/tincan_cli.py" "$HOME/.local/bin/tincan"
    chmod +x "$HOME/.local/bin/tincan"
    echo "[+] Linked global 'tincan' command -> $HOME/.local/bin/tincan"
fi

# 4. Install official TinCan Agent Skills via npx skills
if command -v npx >/dev/null 2>&1; then
    echo "[*] Installing TinCan agent skills via npx skills..."
    npx -y skills add NoJuanNobody/tincan-skills -g -y
else
    echo "[!] Warning: 'npx' not found. Please install Node.js to use agent skills."
fi

# 5. Register connect-peer natural language skill
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
EOF
cp "$SKILLS_DIR/SKILL.md" "$AGENTS_SKILLS_DIR/SKILL.md"

echo ""
echo "=========================================================="
echo "✓ TinCan 2.2 Installation Complete!"
echo "  • Run 'tincan' or 'tincan --help' in your terminal."
echo "  • Skills installed: tincan, tincan-agent-hitl, tincan-crypto-comms, tincan-mesh-os, tincan-webrtc-media, connect-peer"
echo "  • All peripherals (camera, microphone, screen) remain OFF by default."
echo "=========================================================="
