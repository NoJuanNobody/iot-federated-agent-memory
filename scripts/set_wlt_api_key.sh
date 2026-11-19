#!/usr/bin/env bash
set -euo pipefail

# Zero-exposure helper to store WLT_API_KEY in:
# 1. Local TinCan .env (~/dev/iot-federated-agent-memory/.env)
# 2. World Labs CLI (~/.config/worldlabs via `worldlabs auth login --api-key-stdin`)
# 3. Railway secrets for TinCan (project: iot-federated-agent-memory)

if [[ -n "${1:-}" ]]; then
  KEY="$1"
else
  printf "Enter your World Labs Atlas API key (wl_live_...): " >&2
  read -rs KEY
  printf "\n" >&2
fi

KEY="$(printf '%s' "$KEY" | tr -d '\r\n ')"
if [[ -z "$KEY" ]]; then
  echo "Error: empty API key." >&2
  exit 1
fi

ENV_FILE="$HOME/dev/iot-federated-agent-memory/.env"
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"
grep -vE '^(WLT_API_KEY|WLT_API_BASE_URL)=' "$ENV_FILE" > "${ENV_FILE}.tmp" || true
{
  cat "${ENV_FILE}.tmp"
  printf 'WLT_API_BASE_URL="https://api.atlas.worldlabs.ai/api/v2"\n'
  printf 'WLT_API_KEY="%s"\n' "$KEY"
} > "$ENV_FILE"
rm -f "${ENV_FILE}.tmp"
echo "[1/3] Saved WLT_API_KEY & WLT_API_BASE_URL to $ENV_FILE"

printf '%s\n' "$KEY" | worldlabs auth login --api-key-stdin --no-browser
echo "[2/3] Authenticated worldlabs CLI"

(
  cd "$HOME/dev/iot-federated-agent-memory"
  printf '%s' "$KEY" | railway variable set WLT_API_KEY --stdin
  railway variable set WLT_API_BASE_URL="https://api.atlas.worldlabs.ai/api/v2"
)
echo "[3/3] Stored WLT_API_KEY & WLT_API_BASE_URL in Railway secrets for TinCan (iot-federated-agent-memory)"
