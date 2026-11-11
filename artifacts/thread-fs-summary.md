# TinCan per-thread filesystem and agent runner — summary

Uncommitted work in `~/dev/tincan-skills` on Alejandro's Mac. Nothing was
committed or pushed. No Railway CLI, deploy, or spend. `~/.tin-can` was not
modified. ScriptCraft was not used: it is a screenplay app and does not apply
to this Python work.

## Railway volume root (confirmed in place)

`resolve_threads_root()` precedence (blank env values ignored):

1. Explicit `root` argument
2. `TINCAN_THREADS_DIR`
3. `$TINCAN_DATA_DIR/threads` (same data dir as `PeerAccountRegistry`)
4. `$RAILWAY_VOLUME_MOUNT_PATH/threads` (set by Railway when a volume is attached)
5. `$TINCAN_DIR/threads`
6. `~/.tin-can/threads` (local default)

On this Mac, with no volume/data-dir env set, `resolve_threads_root()` returns
`/Users/alejandrolondono/.tin-can/threads`. That directory was **not** created
by this work. On Railway, once a volume is attached, thread files go on the
volume rather than a home directory.

## Locked behavior (already implemented, unchanged in this phase)

- Each new conversation mints a UUID-4 hex thread id. A client `thread_id` is
  reused only if `thread.json` already exists for that peer; otherwise a new id
  is minted. Cross-peer ids are not accepted.
- Layout: `<threads_root>/<peer_id>/<thread_id>/{thread.json,files/}`.
- Missing/blank `peer_id` on `/api/chat` uses the `anonymous` filesystem bucket.
  Billing still falls back to `"peer"`. Unsanitary peer ids set `thread_error`
  and skip FS setup; the chat itself still runs.
- The agent loop stores the server-returned `thread_id` and sends it on later
  turns; `/clear` drops it so the next turn starts a new conversation.

## (4) File limits and tokens

Modest free per-thread tier, env-configurable:

- Free: 256 KiB per file, 1 MiB total (`TINCAN_THREAD_MAX_FILE_BYTES`,
  `TINCAN_THREAD_MAX_TOTAL_BYTES`).
- Hard cap (cannot be paid past): 10 MiB per file, 32 MiB total
  (`TINCAN_THREAD_HARD_MAX_*`).
- Overage price: 1 token per KiB over the free cap
  (`TINCAN_THREAD_OVERAGE_TOKENS_PER_KIB`), minimum 1 token if any overage.

Over-tier writes call the existing `PeerAccountRegistry.bill_tokens` hook
(`charge_thread_quota`) with model name `thread-fs-quota` and
`allow_overage=False`, so the charge shows up on the token ledger. If no
billing hook is provided, `ThreadQuotaError` (`tokens_required`) is raised and
the write is refused. Insufficient balance raises `ThreadQuotaError`
(`insufficient_tokens`). Hard-cap writes raise `ThreadQuotaError`
(`hard_limit`) and never call billing.

HTTP maps those to 402 (token issues) and 413 (hard cap).

## (5) Scam-case preload

New threads created with `template` or `kind` set to `scam-case` (also
accepted on `POST /api/chat`) are seeded from
`templates/threads/scam-case/`. Existing threads are not re-seeded.

**There are no real case files in the repo.** The seed files are clearly
labeled placeholders:

- `templates/threads/scam-case/README.txt`
- `templates/threads/scam-case/case-brief.md`
- `templates/threads/scam-case/evidence/inbox-excerpt.txt`

Override the templates root with `TINCAN_THREAD_TEMPLATES_DIR`.

## (6) Agent-runner access (HTTP + MCP)

Same token gate as `/api/chat`: registered peer with a zero balance → 402.
Missing/blank peer → `anonymous` bucket. Unsanitary peer → `thread_error`,
no FS access. List/read/write require an already-minted thread (404 otherwise).

HTTP:

- `GET /api/thread/files?peer_id=&thread_id=&subpath=`
- `GET /api/thread/file?peer_id=&thread_id=&path=`
- `POST /api/thread/file` with JSON `{peer_id, thread_id, path, content}`

MCP tools in `tincan_mcp.py`: `tincan_thread_list_files`,
`tincan_thread_read_file`, `tincan_thread_write_file`.

Shared implementation: `iot_federated_agent_memory/thread_api.py`.

## Agent runner (phase 2)

Backend compute process that runs a task for a peer/thread, using that
thread's `files/` directory as the workspace (I/O only through `thread_fs`).

- Task model: `AgentTask` in `iot_federated_agent_memory/agent_runner.py`
- Runner / worker: `AgentRunner.run(task)`
- Model calls: existing `DynamicAIGatewayRouter.dispatch_completion` (OpenRouter).
  No new client was added.
- Tools: `list_files`, `read_file`, `write_file`, `finish` (JSON tool protocol)

How to run:

```
python -m iot_federated_agent_memory.agent_runner \
  --peer PEER_ID --thread THREAD_ID --prompt "..."
```

Optional: `--model gemini-brain` (default), `--max-steps 6`.

The CLI calls OpenRouter only if `OPENROUTER_API_KEY` is set. Without a key,
the existing router returns a simulated reply. Tests inject a mock router and
make no paid API calls.

## Tests

The repo had no test tree besides the thread-fs tests added in this work.
Full suite: `python3 -m pytest -v` → **44 passed**, 0 failed. No pre-existing
unrelated failures.

## What still needs doing on Railway

This repo still has no `railway.toml` / `railway.json` / `.railway/` IaC (and
Config as Code cannot declare volume mounts). An operator still needs to, in
the Railway dashboard:

1. Attach a volume to the existing TinCan Mesh / relay service (or reuse one
   already used for `peer_accounts.db`).
2. Set the mount path, e.g. `/data`, so Railway injects
   `RAILWAY_VOLUME_MOUNT_PATH=/data`.
3. Optionally set `TINCAN_DATA_DIR` to the same path so accounts, the board,
   and threads share the volume (`/data/peer_accounts.db`, `/data/threads/...`).
4. Redeploy or restart. Volumes mount at container start, not at build time.

## Open questions

- Confirm or tune the free-tier and hard-cap byte sizes, and the tokens-per-KiB
  overage rate.
- Replace the scam-case placeholder seeds with approved fiction-only episode
  materials when they exist.
- Whether `/api/chat` should default new threads to the `scam-case` template
  for that episode, or only when the client sends `template`/`kind`.
- Whether the agent runner should be exposed as its own HTTP job API
  (`POST /api/agent/run`) in addition to the CLI entry point.

## Files touched in this work (uncommitted)

New:

- `iot_federated_agent_memory/thread_fs.py`
- `iot_federated_agent_memory/thread_api.py`
- `iot_federated_agent_memory/agent_runner.py`
- `templates/threads/scam-case/` (placeholder seeds)
- `tests/test_thread_fs.py`
- `tests/test_thread_quota_and_templates.py`
- `tests/test_thread_api.py`
- `tests/test_agent_runner.py`
- `docs/thread-filesystem.md`
- `artifacts/thread-fs-summary.md`

Modified (additive):

- `server.py` (`/api/chat` hook; `GET/POST /api/thread/*`)
- `iot_federated_agent_memory/tincan_mcp.py` (three thread tools)
- `iot_federated_agent_memory/tincan_agent.py` (store/send thread id)
- `iot_federated_agent_memory/__init__.py` (exports)

Pre-existing dirty files not edited for this work: `account_registry.py`,
`mesh_os_ui.py`.
