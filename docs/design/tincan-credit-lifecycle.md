# TINCAN credit lifecycle

This is a trace of how credits enter, live in and leave TinCan, checked against `main` at `79a6f87`. The one exception is the arena billing section, which describes PR #12.

## Where credits live

`iot_federated_agent_memory/account_registry.py` (`PeerAccountRegistry`) uses SQLite `peer_accounts.db` under `TINCAN_DATA_DIR` or the Railway volume mount. Its tables:

- **`accounts`:** `token_balance`, `credit_balance_usd`, `total_tokens_used` and `total_billed_usd` per account.
- **`credit_events`:** one row per credit, keyed by a unique `ref` so a payment or ad view can only credit once.
- **`token_ledger`:** one row per charge (tokens, cost, model, timestamp, note). PR #12 adds `kind`, `match_id` and `arena_side` columns.

New accounts start with **10 tokens and $0.10** (`DEFAULT_INITIAL_TOKENS`, `DEFAULT_INITIAL_CREDIT_USD`). `bill_tokens` auto-provisions the same starter guest account for an unknown `peer_id`.

## How credits are added

These are the only three paths that write a credit. All of them go through `credit_once(ref, peer_id, kind, tokens, amount_usd)`.

| Path | Trigger | `ref` | Amount |
| --- | --- | --- | --- |
| **Stripe checkout** | Stripe-signed webhook after `/api/billing/checkout` | `stripe:<session id>` | `TOKEN_PACKS` in `server.py`: `pack_100` $1 = 120 tokens, `pack_500` $5 = 650, `pack_2000` $20 = 2,800 |
| **Sponsor ads** | Server-timed view; must watch **90%** (`AD_MIN_WATCH_FRACTION = 0.9`); capped at **5 per day** (`AD_DAILY_REWARD_CAP`, env `TINCAN_AD_DAILY_CAP`) | `ad:<view token>` | `reward_tokens = 5000` per ad (`sponsor_ads.py`) |
| **Admin top-up** | `POST /api/account/billing/topup` with `X-Admin-Key` = `TINCAN_ADMIN_KEY` | `admin:<random>` | Whatever the operator grants |

## Not real credits

- **Relay, eval and vote rewards** exist only in the browser. `mintTincanRewardTokens()` in `mesh_os_ui.py` adds to a page counter (`mintedRewardBalance`) and the HUD pill. Nothing is written to `accounts` or `credit_events`.
- **Telemetry vending** is simulated. `HMACVendingMachine` in `edge_telemetry.py` keeps in-memory wallets and receipts, not the account ledger.

## How credits are spent

- **AI chat:** `/api/chat` calls `bill_tokens` with the model's real usage and cost (`completion.cost_usd`), with `allow_overage=True`, so the last request can take the balance to 0. The next request is refused with **402** at a zero balance.
- **Thread storage quota:** writes beyond the free per-thread tier cost **1 token per KiB** (`DEFAULT_OVERAGE_TOKENS_PER_KIB = 1`, env `TINCAN_THREAD_OVERAGE_TOKENS_PER_KIB`). `thread_fs.charge_thread_quota` charges this through `bill_tokens` (model `thread-fs-quota`, `allow_overage=False`), called from `thread_api.py` and `agent_runner.py`.

## Brain Arena duels

- **On main (79a6f87):** the duel's two `/api/chat` calls send no `peer_id`, so both sides bill the shared `peer` account.
- **With PR #12 ([AI-188](https://linear.app/ai-mesiah/issue/AI-188/arena-bill-duels-to-the-individual-account-not-the-shared-bucket)):** duels bill the **signed-in account only**, never the shared bucket:
  - **Identity:** the server resolves it from a session. It's stored hashed in `account_sessions`, and the HttpOnly `tincan_session` cookie is set on passkey login, passkey registration and a new signup (or `Authorization: Bearer` for the CLI). A client `peer_id` is ignored.
  - **No sign-in:** `POST /api/mesh/arena/match` returns 401 `sign_in_required`. A zero balance gets 402. Otherwise it creates an `arena_matches` row (account, both models).
  - **Each side:** `/api/chat` with `arena: true` needs `match_id` and `arena_side`. It's checked before dispatch for ownership, the side's model and replay. It returns **402** if the balance can't cover the side's worst case, which is the prompt estimate plus `max_tokens` (capped at 1024).
  - **Charging:** `bill_tokens(..., arena_match_id=, arena_side=)` charges the account at the real cost in one transaction. It writes a `token_ledger` row with `kind='arena'`, the match id, the side and both models, and stores per-side and total tokens and cost on `arena_matches`.
  - **Votes:** a vote with a match id reads the models and cost from the match record.
  - **Practical effect:** a new account (10 tokens) has to top up or watch an ad before its first full duel.

## Gaps

- **No margin:** chat is billed at exactly the model's cost.
- **No revenue split:** there's no partner, sponsor or creator split.
- **No sponsor revenue tracking:** sponsor payments to TinCan aren't recorded; only the tokens given to viewers are.
- **Inconsistent prices:** packs and ad rewards don't line up. $1 buys 120 tokens (`pack_100`), while one 90% ad view gives 5,000.
- **No refunds or expiry:** no refund path, and credits never expire.
- **Simulated vending:** telemetry vending isn't connected to real balances.
- **Fake rewards:** relay, eval and vote rewards are shown to users but never become real credits.
