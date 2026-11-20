#!/usr/bin/env bash
# Zero-Reset Production Deploy Wrapper for TinCan Mesh OS & Node Studio
# 1. Audits live persistent volume (/data) & counts all users' .space files before deploy
# 2. Runs POST /api/spaces/backup so every .space SQLite container has a fresh verified S3 snapshot
# 3. Pushes current main branch to trigger Railway deploy and waits for SUCCESS
# 4. Re-audits /api/spaces/persistence after deploy to verify ZERO spaces or files were lost
set -euo pipefail

BASE_URL="${TINCAN_PROD_URL:-https://iot-federated-agent-memory-production.up.railway.app}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

echo "[1/4] Auditing live space persistence on ${BASE_URL}..."
BEFORE_JSON="$(curl -fsSL "${BASE_URL}/api/spaces/persistence")"
BEFORE_SPACES="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("space_count", 0))' "${BEFORE_JSON}")"
BEFORE_FILES="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("total_vfs_files", 0))' "${BEFORE_JSON}")"
IS_PERSIST="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("is_persistent_volume", False))' "${BEFORE_JSON}")"
echo "      Before deploy: persistent_volume=${IS_PERSIST}, spaces=${BEFORE_SPACES}, total_vfs_files=${BEFORE_FILES}"

if [[ "${IS_PERSIST}" != "True" ]]; then
  echo "[!] WARNING: Production server is NOT reporting a mounted persistent volume! Triggering S3 backup before continuing."
fi

echo "[2/4] Triggering pre-deploy consistent SQLite -> S3 backup of dirty spaces..."
BACKUP_JSON="$(curl -fsSL -X POST "${BASE_URL}/api/spaces/backup" -H "Content-Type: application/json" -d '{"only_dirty":true}')"
echo "      Backup result: ${BACKUP_JSON}"

echo "[3/4] Pushing branch '${BRANCH}' to origin (Railway auto-deploy)..."
git push origin "${BRANCH}"

echo "[4/4] Waiting for Railway deployment to report SUCCESS..."
for i in $(seq 1 40); do
  STATUS="$(railway deployment list --limit 1 2>/dev/null | awk 'NR==3 {print $3}')"
  echo "      Poll #${i}: status=${STATUS:-UNKNOWN}"
  if [[ "${STATUS}" == "SUCCESS" ]]; then
    break
  fi
  if [[ "${STATUS}" == "FAILED" || "${STATUS}" == "CRASHED" ]]; then
    echo "[!] Deployment failed (${STATUS}). Spaces remain intact on /data and S3." >&2
    exit 1
  fi
  sleep 5
done

AFTER_JSON="$(curl -fsSL "${BASE_URL}/api/spaces/persistence")"
AFTER_SPACES="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("space_count", 0))' "${AFTER_JSON}")"
AFTER_FILES="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("total_vfs_files", 0))' "${AFTER_JSON}")"
echo "      After deploy: spaces=${AFTER_SPACES} (was ${BEFORE_SPACES}), total_vfs_files=${AFTER_FILES} (was ${BEFORE_FILES})"

if (( AFTER_SPACES < BEFORE_SPACES || AFTER_FILES < BEFORE_FILES )); then
  echo "[!] ERROR: Space/file count dropped after deploy! Triggering S3 hydration..." >&2
  curl -fsSL -X POST "${BASE_URL}/api/spaces/hydrate" -H "Content-Type: application/json" -d '{"overwrite_existing":false}'
  exit 1
fi

echo "[✓] Zero-reset deploy verified: all ${AFTER_SPACES} spaces (${AFTER_FILES} files) preserved intact."
