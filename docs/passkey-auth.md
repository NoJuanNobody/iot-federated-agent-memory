# Passwordless sign-in: passkeys + email codes

TinCan Mesh OS has no passwords. Accounts are unlocked with a **passkey**
(Face ID, Touch ID, fingerprint or device PIN via WebAuthn) or, once, with a
**6-digit email code** that lets a device set up its first passkey.

## Why

Accounts used to be keyed only by the browser's random `peer_id`
(`localStorage.tincan_peer_id`). A new phone got a new `peer_id`, registering
again with the same email hit `UNIQUE constraint failed: accounts.email`, and
there was no way to reach the existing account.

## Flows

| Flow | Endpoints |
| --- | --- |
| Sign up → create passkey | `POST /api/account/register` returns `enroll_token` for a new account → `POST /api/passkey/register/options` → `navigator.credentials.create` → `POST /api/passkey/register/verify` |
| Sign in on another device | `POST /api/passkey/login/options` (optional `email` hint) → `navigator.credentials.get` → `POST /api/passkey/login/verify` (links this device's `peer_id` to the account) |
| Existing account, no passkey yet | `POST /api/account/recovery/request {email}` → code emailed → `POST /api/account/recovery/verify {email, code}` returns `enroll_token` → register a passkey as above |
| Email already registered | `/api/account/register` returns `409 {"code": "email_exists", "error": "You already have an account — sign in with your passkey."}` |

Details:

* Registration asks for a **platform** authenticator, `residentKey: preferred`,
  `userVerification: required`; verification also requires UV.
* Challenges are 32 random bytes stored server-side (`auth_challenges`), bound to
  the requesting `peer_id`, expire after 5 minutes and are burned on first use
  (even if verification fails).
* Adding a passkey always needs a single-use enrollment grant (15 min): one is
  issued only to a brand-new signup (or a guest `@mesh.local` placeholder being
  upgraded), or after a correct email code. Knowing someone's `peer_id` is not
  enough to attach a passkey to their account.
* Email codes: 6 digits, stored only as HMAC-SHA256 (per-code salt + server
  secret), 10 minute expiry, 5 wrong tries locks the code, max 3 codes per email
  per 15 minutes and 10 requests per client IP per hour. A new code cancels the
  previous one. Codes are only issued for accounts that have **no** passkey yet,
  and the response is the same whether or not the email exists.
* Linked devices live in `account_peer_links (peer_id → account_peer_id)`. The
  account's original `peer_id` stays the primary key of `accounts`, so ledgers,
  Stripe metadata and every existing `get_account_by_peer` caller keep working;
  a linked `peer_id` simply resolves to its account.

## Relying Party ID

Resolved in this order:

1. `TINCAN_RP_ID`
2. host of `TINCAN_PUBLIC_URL`
3. the request `Host` header

The expected origin is `https://<rp_id>` (plus `http://localhost[:port]` when the
RP ID is `localhost`). `up.railway.app` is on the Public Suffix List, so the RP
ID must be the full host: `iot-federated-agent-memory-production.up.railway.app`.
Changing the RP ID later (e.g. moving to a custom domain) invalidates every
existing passkey; users would need an email code to enroll again.

## Environment variables (names only)

| Variable | Required | Purpose |
| --- | --- | --- |
| `TINCAN_RP_ID` | Recommended in production | Pin the RP ID instead of trusting headers. Set to the full Railway host above. |
| `TINCAN_PUBLIC_URL` | Already used for Stripe | Fallback for the RP ID / origin. |
| `RESEND_API_KEY` | Needed for email codes | Enables delivery through Resend. Without it no code is ever delivered (the API reports `delivery_configured: false`). |
| `TINCAN_EMAIL_FROM` | With `RESEND_API_KEY` | Sender on a Resend-verified domain, e.g. `TinCan <auth@yourdomain>`. |
| `TINCAN_AUTH_SECRET` | Optional | HMAC key for codes/grants. If unset, a random key is generated once into `auth_secret.key` next to the DB on the data volume (mode 0600). |
| `TINCAN_EMAIL_DEV_LOG` | Local dev only | `1` prints undelivered emails (including codes) to the log. Ignored when `TINCAN_ENV` / `RAILWAY_ENVIRONMENT_NAME` is `production`. |

There was no mailer in the repo before this change; `iot_federated_agent_memory/mailer.py`
is a small pluggable sender (Resend over HTTPS, or log-only). Without a sender it
logs only that a message was issued, with the address masked, never the code.

## Database migration

All changes are additive and idempotent, run at startup against the existing
`peer_accounts.db` in `TINCAN_DATA_DIR`:

* `ALTER TABLE accounts ADD COLUMN webauthn_user_id TEXT DEFAULT ''`
* new tables `account_peer_links`, `passkey_credentials`, `auth_challenges`,
  `auth_grants`, `recovery_codes`

No existing rows are rewritten or deleted.
