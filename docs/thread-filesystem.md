# Per-thread filesystem storage

Thread workspaces live under `<threads_root>/<peer_id>/<thread_id>/`.
`resolve_threads_root()` chooses that root in this order (blank env values are ignored):

1. Explicit `root` argument (tests and local helpers)
2. `TINCAN_THREADS_DIR` — override the threads folder directly
3. `$TINCAN_DATA_DIR/threads` — same data directory as `PeerAccountRegistry` (`peer_accounts.db`) and the cyberspace board
4. `$RAILWAY_VOLUME_MOUNT_PATH/threads` — injected by Railway when a volume is attached to the service
5. `$TINCAN_DIR/threads` — local CLI identity directory
6. `~/.tin-can/threads` — local default

On Railway, thread files should live on a persistent volume, not the container filesystem or a developer home directory. This repo has no `railway.toml`, `railway.json`, `Procfile`, `Dockerfile`, or `.railway/` Infrastructure-as-Code file. Railway Config as Code (`railway.toml` / `railway.json`) cannot declare volume mounts (and is deprecated). Railway IaC (`.railway/railway.ts`) *can* declare a volume, but it was not added here: applying it requires the Railway CLI against the existing project graph and can create billed resources.

## What still needs doing on Railway (dashboard, not in this change)

1. Open the existing TinCan Mesh / relay service in the Railway dashboard.
2. Attach a volume to that service (or reuse one already used for `peer_accounts.db`).
3. Set the volume mount path, e.g. `/data`. Railway will then set `RAILWAY_VOLUME_MOUNT_PATH=/data` at runtime.
4. Optionally set `TINCAN_DATA_DIR` to the same mount path so accounts, the board, and threads share the volume (`/data/peer_accounts.db` and `/data/threads/...`).
5. Redeploy or restart the service. Volumes are mounted at container start, not at build time.

Do not set `RAILWAY_VOLUME_MOUNT_PATH` by hand unless you are testing locally; Railway provides it when a volume is attached.

## Free-tier file limits

Writes within the free per-thread tier are unpaid. Larger writes debit the
peer's token balance through the existing `PeerAccountRegistry.bill_tokens`
ledger using model name `thread-fs-quota` (`allow_overage=False`). A hard cap
cannot be exceeded even with tokens.

| Setting | Env var | Default |
|---|---|---|
| Max file size (free) | `TINCAN_THREAD_MAX_FILE_BYTES` | 262144 (256 KiB) |
| Max total bytes (free) | `TINCAN_THREAD_MAX_TOTAL_BYTES` | 1048576 (1 MiB) |
| Hard max file size | `TINCAN_THREAD_HARD_MAX_FILE_BYTES` | 10485760 (10 MiB) |
| Hard max total bytes | `TINCAN_THREAD_HARD_MAX_TOTAL_BYTES` | 33554432 (32 MiB) |
| Tokens per KiB over the free cap | `TINCAN_THREAD_OVERAGE_TOKENS_PER_KIB` | 1 |

`ThreadQuotaError` is raised when a write is over-tier and no billing hook is
provided (`tokens_required`), when the peer cannot pay (`insufficient_tokens`),
or when the hard cap is hit (`hard_limit`). HTTP status: 402 for token issues,
413 for the hard cap.

## Scam-case template

Pass `template` or `kind` (`scam-case`) to `start_or_continue_thread` or to
`POST /api/chat`. New threads are seeded from `templates/threads/scam-case/`.
The files in that directory are clearly labeled **placeholders**, not real
case materials. Existing threads are not re-seeded. Override the templates
root with `TINCAN_THREAD_TEMPLATES_DIR`.

## HTTP and MCP access

Same token gate as `POST /api/chat`: a registered peer with a zero balance
gets 402. Missing/blank `peer_id` uses the `anonymous` filesystem bucket.
Unsanitary peer ids return `thread_error` and do not touch the filesystem.
List/read/write require an existing (already minted) thread.

- `GET /api/thread/files?peer_id=&thread_id=&subpath=`
- `GET /api/thread/file?peer_id=&thread_id=&path=`
- `POST /api/thread/file` JSON `{peer_id, thread_id, path, content}`

MCP tools (same helpers): `tincan_thread_list_files`, `tincan_thread_read_file`,
`tincan_thread_write_file`.

## Agent runner

`python -m iot_federated_agent_memory.agent_runner --peer PEER --thread THREAD_ID --prompt "..."`

Uses `DynamicAIGatewayRouter.dispatch_completion` (OpenRouter). Workspace I/O
goes through `thread_fs` only. The CLI will call OpenRouter only if
`OPENROUTER_API_KEY` is set; without a key the existing router returns a
simulated reply. Tests mock the router and never make paid calls.
