#!/usr/bin/env bash
# ==============================================================================
# TinCan 2.2 Local Mesh Node, CLI & Skills Installer (AI-247)
# Usage:
#   curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash
#   curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash -s -- --slim
# ==============================================================================
set -e

SLIM_MODE=0
for arg in "$@"; do
    case "$arg" in
        --slim) SLIM_MODE=1 ;;
    esac
done

REPO_URL="https://github.com/NoJuanNobody/iot-federated-agent-memory.git"
MIRROR_REPO_URL="https://github.com/NoJuanNobody/tincan-skills.git"
INSTALL_DIR="$HOME/dev/iot-federated-agent-memory"
VENV_DIR="$INSTALL_DIR/.venv"
TINCAN_CONFIG_DIR="${TINCAN_CONFIG_DIR:-$HOME/.tincan}"
TINCAN_DATA_DIR="${TINCAN_DATA_DIR:-$TINCAN_CONFIG_DIR/node_data}"
SKILLS_DIR="$HOME/.gemini/config/skills/connect-peer"
AGENTS_SKILLS_DIR="$HOME/.agents/skills/connect-peer"

echo "=========================================================="
if [ "$SLIM_MODE" -eq 1 ]; then
    echo "[*] Installing TinCan 2.2 Local Mesh Node (Slim Edge Mode)"
else
    echo "[*] Installing TinCan 2.2 Local Mesh Node, OS & CLI"
fi
echo "=========================================================="

# 1. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] ERROR: python3 is required. Install Python 3.10+ and re-run."
    exit 1
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[+] Found Python $PY_VER"

# 2. Ensure dev & local node data directories exist
mkdir -p "$HOME/dev" "$TINCAN_CONFIG_DIR" "$TINCAN_DATA_DIR"

# 3. Clone or update repository from GitHub (with mirror fallback)
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[+] Updating existing repository in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --rebase origin main || true
elif [ ! -d "$INSTALL_DIR" ]; then
    echo "[+] Cloning repository to $INSTALL_DIR..."
    if ! git clone "$REPO_URL" "$INSTALL_DIR"; then
        echo "[!] Primary repo clone failed; falling back to public mirror $MIRROR_REPO_URL..."
        git clone "$MIRROR_REPO_URL" "$INSTALL_DIR"
    fi
fi

# 4. Provision isolated Python venv with local node & server dependencies
echo "[+] Setting up Python virtual environment at $VENV_DIR..."
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    python3 -m venv "$VENV_DIR" 2>/dev/null || true
fi

if [ -x "$VENV_DIR/bin/python3" ]; then
    VENV_PY="$VENV_DIR/bin/python3"
    "$VENV_PY" -m pip install --upgrade --quiet pip 2>/dev/null || true
    if [ "$SLIM_MODE" -eq 1 ]; then
        echo "[+] Installing slim edge dependencies (PyNaCl + zeroconf)..."
        "$VENV_PY" -m pip install --quiet PyNaCl zeroconf 2>/dev/null || "$VENV_PY" -m pip install --quiet PyNaCl || true
    else
        echo "[+] Installing local Mesh OS node dependencies..."
        "$VENV_PY" -m pip install --quiet PyNaCl zeroconf 2>/dev/null || true
        if [ -f "$INSTALL_DIR/pyproject.toml" ]; then
            "$VENV_PY" -m pip install --quiet --no-build-isolation -e "$INSTALL_DIR" 2>/dev/null || true
        fi
    fi
else
    VENV_PY="$(command -v python3)"
    echo "[!] python3 -m venv unavailable; falling back to system $VENV_PY"
    "$VENV_PY" -c "import nacl" 2>/dev/null || "$VENV_PY" -m pip install --user --quiet PyNaCl 2>/dev/null || "$VENV_PY" -m pip install --break-system-packages --quiet PyNaCl 2>/dev/null || true
fi

# 5. Link global 'tincan' wrapper executable using the provisioned venv Python
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

if [ ! -f "$INSTALL_DIR/tincan_cli.py" ]; then
    echo "[!] ERROR: $INSTALL_DIR/tincan_cli.py not found after clone. Aborting."
    exit 1
fi

chmod +x "$INSTALL_DIR/tincan_cli.py"
cat << EOF > "$HOME/.local/bin/tincan"
#!/usr/bin/env bash
exec "$VENV_PY" "$INSTALL_DIR/tincan_cli.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/tincan"
echo "[+] Installed global 'tincan' wrapper -> $HOME/.local/bin/tincan (using $VENV_PY)"

if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$HOME/.local/bin/tincan" "/usr/local/bin/tincan" 2>/dev/null || true
fi

# Ensure ~/.local/bin is persisted in shell RC files so 'which tincan' works in new terminals
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [ -f "$rc" ] && ! grep -q '\.local/bin' "$rc" 2>/dev/null; then
        printf '\n# TinCan CLI PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
    fi
done

# 6. Verify CLI binary and initialize the node's Ed25519 identity + local data dir
if ! "$HOME/.local/bin/tincan" --help >/dev/null 2>&1; then
    echo "[!] ERROR: 'tincan --help' verification failed. Aborting."
    exit 1
fi
echo "[+] Verified 'tincan' CLI binary is executable and operational."

NODE_ADDR=$("$VENV_PY" -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); from iot_federated_agent_memory.os_launcher import ensure_local_identity; print(ensure_local_identity('$TINCAN_CONFIG_DIR').get('tc_address', ''))" 2>/dev/null || true)
echo "[+] Local node Ed25519 identity ready: ${NODE_ADDR:-initialized}"
echo "[+] Local node data directory: $TINCAN_DATA_DIR"

# 7. Install official TinCan Agent Skills (skipped in --slim edge mode)
if [ "$SLIM_MODE" -eq 0 ]; then
    if command -v npx >/dev/null 2>&1; then
        echo "[*] Installing TinCan agent skills via npx skills..."
        npx -y skills add NoJuanNobody/tincan-skills -g -y || true
    else
        echo "[!] Warning: 'npx' not found. Skipping agent skills installation."
    fi

    mkdir -p "$SKILLS_DIR" "$AGENTS_SKILLS_DIR"
    cat << 'EOF' > "$SKILLS_DIR/SKILL.md"
---
name: connect-peer
description: >-
  Connect this computer to the live IoT Federated Agent Mesh, WebRTC UDP screensharing relay,
  shared Obsidian brain, and dynamic AI token gateway. Trigger with natural phrases
  like "connect peer", "join mesh", "link to friend", "start screen share", or "/connect-peer".
---

# Connect Peer Skill (`connect-peer`)

Launch the local offline-capable Mesh OS node (`tincan os`) or connect peers over LAN/mDNS/UDP and Railway fallback.
EOF
    cp "$SKILLS_DIR/SKILL.md" "$AGENTS_SKILLS_DIR/SKILL.md"
fi

echo ""
echo "=========================================================="
echo "✓ TinCan 2.2 Local Mesh Node Installation Complete!"
echo "  • Binary verified at : $(command -v tincan || echo "$HOME/.local/bin/tincan")"
echo "  • Node identity      : ${NODE_ADDR:-ready}"
echo "  • Local data folder  : $TINCAN_DATA_DIR"
echo ""
echo "  Next steps:"
echo "    tincan os                 # Start local offline-ready Mesh OS & open window"
echo "    tincan open board         # Open Board (or space, terminal, arena, node-studio)"
echo "    tincan open --list        # List all available Mesh OS app windows"
echo "    tincan os --status        # Check local node status"
echo "=========================================================="
