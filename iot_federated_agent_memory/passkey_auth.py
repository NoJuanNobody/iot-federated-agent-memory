#!/usr/bin/env python3
"""Passwordless sign-in for TinCan Mesh OS: passkeys (WebAuthn) plus one-time email codes.

There are no passwords anywhere in this flow.

* **Sign up**: ``/api/account/register`` creates the account and hands back a
  short-lived, single-use *enrollment grant*. The browser spends it to create a
  passkey (platform authenticator, user verification required).
* **Sign in on another device**: a passkey assertion unlocks the existing
  account and links the current browser's ``peer_id`` to it.
* **Recovery** for an account that has no passkey yet: a 6-digit code is emailed
  to the address on file (stored only as an HMAC, 10 min expiry, 5 attempts,
  rate limited). A correct code yields an enrollment grant for a new passkey.

All state (credentials, challenges, grants, codes) lives in the same SQLite DB as
the account registry, in new tables created with ``CREATE TABLE IF NOT EXISTS``,
so existing data on the Railway volume is untouched.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from . import mailer
from .account_registry import PeerAccountRegistry

try:  # py_webauthn (PyPI: "webauthn")
    from webauthn import (
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
    from webauthn.helpers.structs import (
        AuthenticatorAttachment,
        AuthenticatorSelectionCriteria,
        AuthenticatorTransport,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    WEBAUTHN_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when the dependency is missing
    WEBAUTHN_AVAILABLE = False

    def bytes_to_base64url(val: bytes) -> str:
        return base64.urlsafe_b64encode(val).decode("ascii").rstrip("=")

    def base64url_to_bytes(val: str) -> bytes:
        return base64.urlsafe_b64decode(val + "=" * (-len(val) % 4))


RP_NAME = "TinCan Mesh OS"
CHALLENGE_TTL_SECONDS = 5 * 60
GRANT_TTL_SECONDS = 15 * 60
CODE_TTL_SECONDS = 10 * 60
CODE_MAX_ATTEMPTS = 5
CODE_MAX_PER_EMAIL_WINDOW = 3
CODE_EMAIL_WINDOW_SECONDS = 15 * 60
CODE_MAX_PER_CLIENT_HOUR = 10


class PasskeyError(Exception):
    """A user-facing auth failure. ``message`` is safe to show; ``code`` is for the UI."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# --------------------------------------------------------------------------- RP ID
def _host_only(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        return ""
    if "://" in value:
        value = urlparse(value).hostname or ""
    else:
        value = value.split("/")[0]
        if value.startswith("["):
            return ""  # IPv6 literals can't be RP IDs
        value = value.split(":")[0]
    return value.strip(".")


def resolve_relying_party(request_host: str = "", environ: Optional[Dict[str, str]] = None) -> Tuple[str, List[str]]:
    """Return ``(rp_id, allowed_origins)``.

    RP ID comes from ``TINCAN_RP_ID``, else the host of ``TINCAN_PUBLIC_URL``, else
    the request's Host header. It must be the full host (``up.railway.app`` is a
    public suffix, so a Railway app's RP ID is its whole ``*.up.railway.app`` name).
    The expected origin is ``https://<rp_id>``; ``http://localhost[:port]`` is also
    accepted when the RP ID is ``localhost`` for local development.
    """
    env = os.environ if environ is None else environ
    rp_id = _host_only(env.get("TINCAN_RP_ID", "")) or _host_only(env.get("TINCAN_PUBLIC_URL", "")) or _host_only(request_host)
    if not rp_id:
        raise PasskeyError("rp_unresolved", "Passkeys aren't configured for this server.", 503)

    origins = [f"https://{rp_id}"]
    public_url = (env.get("TINCAN_PUBLIC_URL") or "").strip()
    if public_url:
        parsed = urlparse(public_url)
        if parsed.hostname and parsed.hostname.lower() == rp_id and parsed.scheme in ("http", "https"):
            netloc = parsed.netloc.lower()
            origin = f"{parsed.scheme}://{netloc}"
            if origin not in origins and (parsed.scheme == "https" or rp_id == "localhost"):
                origins.append(origin)
    if rp_id == "localhost":
        req = (request_host or "").strip().lower()
        for candidate in ("http://localhost", f"http://{req}" if req.startswith("localhost") else ""):
            if candidate and candidate not in origins:
                origins.append(candidate)
    return rp_id, origins


# --------------------------------------------------------------------------- service
class PasskeyAuthService:
    def __init__(
        self,
        registry: PeerAccountRegistry,
        secret: Optional[bytes] = None,
        clock: Callable[[], float] = time.time,
    ):
        self.registry = registry
        self.db_path = registry.db_path
        self.clock = clock
        self._secret = secret or self._load_secret()
        self._client_hits: Dict[str, List[float]] = {}
        self._client_lock = threading.Lock()
        self._init_db()

    # ---------------------------------------------------------------- storage
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            cols = [c[1] for c in conn.execute("PRAGMA table_info(accounts)").fetchall()]
            if "webauthn_user_id" not in cols:
                conn.execute("ALTER TABLE accounts ADD COLUMN webauthn_user_id TEXT DEFAULT ''")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS passkey_credentials (
                    credential_id TEXT PRIMARY KEY,
                    account_peer_id TEXT NOT NULL,
                    public_key BLOB NOT NULL,
                    sign_count INTEGER NOT NULL DEFAULT 0,
                    transports TEXT NOT NULL DEFAULT '[]',
                    aaguid TEXT NOT NULL DEFAULT '',
                    backed_up INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_used_at REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_passkey_account ON passkey_credentials(account_peer_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_challenges (
                    challenge_id TEXT PRIMARY KEY,
                    challenge TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    peer_id TEXT NOT NULL,
                    account_peer_id TEXT NOT NULL DEFAULT '',
                    grant_hash TEXT NOT NULL DEFAULT '',
                    rp_id TEXT NOT NULL,
                    origins TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    used_at REAL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_grants (
                    grant_hash TEXT PRIMARY KEY,
                    account_peer_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    used_at REAL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recovery_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_peer_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    used_at REAL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_recovery_email ON recovery_codes(email, created_at)")
            conn.commit()
        self._purge_expired()

    def _purge_expired(self) -> None:
        cutoff = self.clock() - 24 * 3600
        with self._connect() as conn:
            conn.execute("DELETE FROM auth_challenges WHERE expires_at < ?", (cutoff,))
            conn.execute("DELETE FROM auth_grants WHERE expires_at < ?", (cutoff,))
            conn.execute("DELETE FROM recovery_codes WHERE expires_at < ?", (cutoff,))
            conn.commit()

    def _load_secret(self) -> bytes:
        env_secret = os.environ.get("TINCAN_AUTH_SECRET", "").strip()
        if env_secret:
            return env_secret.encode("utf-8")
        path = os.path.join(os.path.dirname(os.path.abspath(self.registry.db_path)), "auth_secret.key")
        try:
            with open(path, "rb") as fh:
                data = fh.read()
                if len(data) >= 32:
                    return data
        except FileNotFoundError:
            pass
        data = secrets.token_bytes(32)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return data

    def _hash(self, *parts: str) -> str:
        return hmac.new(self._secret, "\x1f".join(parts).encode("utf-8"), hashlib.sha256).hexdigest()

    # ---------------------------------------------------------------- helpers
    def _require_webauthn(self) -> None:
        if not WEBAUTHN_AVAILABLE:
            raise PasskeyError("passkeys_unavailable", "Passkeys aren't available on this server yet.", 503)

    def _account_or_error(self, account_peer_id: str) -> Dict:
        account = self.registry.get_account_by_peer(account_peer_id)
        if not account:
            raise PasskeyError("account_not_found", "Account not found.", 404)
        return account

    def _user_handle(self, account_peer_id: str) -> bytes:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT webauthn_user_id FROM accounts WHERE peer_id = ?", (account_peer_id,)
            ).fetchone()
            if row and row[0]:
                return base64url_to_bytes(row[0])
            handle = secrets.token_bytes(32)
            conn.execute(
                "UPDATE accounts SET webauthn_user_id = ? WHERE peer_id = ? AND (webauthn_user_id IS NULL OR webauthn_user_id = '')",
                (bytes_to_base64url(handle), account_peer_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT webauthn_user_id FROM accounts WHERE peer_id = ?", (account_peer_id,)
            ).fetchone()
            return base64url_to_bytes(row[0])

    def list_credentials(self, account_peer_id: str) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM passkey_credentials WHERE account_peer_id = ? ORDER BY created_at",
                (self.registry.resolve_account_peer_id(account_peer_id),),
            ).fetchall()
        return [dict(r) for r in rows]

    def has_passkey(self, account_peer_id: str) -> bool:
        return bool(self.list_credentials(account_peer_id))

    @staticmethod
    def _descriptors(creds: List[Dict]) -> List["PublicKeyCredentialDescriptor"]:
        out = []
        for c in creds:
            transports = []
            for t in json.loads(c.get("transports") or "[]"):
                try:
                    transports.append(AuthenticatorTransport(t))
                except ValueError:
                    continue
            out.append(
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(c["credential_id"]), transports=transports or None
                )
            )
        return out

    # ---------------------------------------------------------------- grants
    def issue_enrollment_grant(self, account_peer_id: str, purpose: str = "enroll") -> str:
        token = secrets.token_urlsafe(32)
        now = self.clock()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO auth_grants (grant_hash, account_peer_id, purpose, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (self._hash("grant", token), account_peer_id, purpose, now, now + GRANT_TTL_SECONDS),
            )
            conn.commit()
        return token

    def _peek_grant(self, token: str) -> Dict:
        if not token:
            raise PasskeyError("grant_required", "Start from sign-up or an email code to add a passkey.", 403)
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM auth_grants WHERE grant_hash = ?", (self._hash("grant", token),)).fetchone()
        if not row or row["used_at"] is not None or row["expires_at"] < self.clock():
            raise PasskeyError("grant_invalid", "That passkey setup link has expired. Request a new email code.", 403)
        return dict(row)

    def _consume_grant(self, grant_hash: str) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE auth_grants SET used_at = ? WHERE grant_hash = ? AND used_at IS NULL AND expires_at >= ?",
                (self.clock(), grant_hash, self.clock()),
            )
            conn.commit()
        if cur.rowcount != 1:
            raise PasskeyError("grant_invalid", "That passkey setup link has expired. Request a new email code.", 403)

    # ---------------------------------------------------------------- challenges
    def _store_challenge(self, challenge: bytes, purpose: str, peer_id: str, rp_id: str,
                         origins: List[str], account_peer_id: str = "", grant_hash: str = "") -> str:
        challenge_id = secrets.token_urlsafe(18)
        now = self.clock()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_challenges (challenge_id, challenge, purpose, peer_id, account_peer_id,
                    grant_hash, rp_id, origins, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (challenge_id, bytes_to_base64url(challenge), purpose, peer_id, account_peer_id,
                 grant_hash, rp_id, json.dumps(origins), now, now + CHALLENGE_TTL_SECONDS),
            )
            conn.commit()
        return challenge_id

    def consume_challenge(self, challenge_id: str, purpose: str, peer_id: str) -> Dict:
        """Single use: the row is marked used before verification, success or not."""
        now = self.clock()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM auth_challenges WHERE challenge_id = ?", (challenge_id or "",)).fetchone()
            if not row or row["purpose"] != purpose:
                raise PasskeyError("challenge_invalid", "This sign-in attempt is no longer valid. Please try again.")
            cur = conn.execute(
                "UPDATE auth_challenges SET used_at = ? WHERE challenge_id = ? AND used_at IS NULL",
                (now, challenge_id),
            )
            conn.commit()
        if cur.rowcount != 1:
            raise PasskeyError("challenge_used", "This sign-in attempt was already used. Please try again.")
        if row["expires_at"] < now:
            raise PasskeyError("challenge_expired", "This sign-in attempt expired. Please try again.")
        if row["peer_id"] != (peer_id or "").strip():
            raise PasskeyError("challenge_invalid", "This sign-in attempt is no longer valid. Please try again.")
        return dict(row)

    # ---------------------------------------------------------------- registration
    def begin_registration(self, peer_id: str, enroll_token: str, rp_id: str, origins: List[str]) -> Dict:
        self._require_webauthn()
        peer_id = (peer_id or "").strip()
        if not peer_id:
            raise PasskeyError("peer_required", "Missing device id.")
        grant = self._peek_grant(enroll_token)
        account = self._account_or_error(grant["account_peer_id"])
        account_peer_id = account["peer_id"]
        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=RP_NAME,
            user_id=self._user_handle(account_peer_id),
            user_name=account["email"],
            user_display_name=account.get("full_name") or account.get("username") or account["email"],
            challenge=secrets.token_bytes(32),
            timeout=CHALLENGE_TTL_SECONDS * 1000,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            exclude_credentials=self._descriptors(self.list_credentials(account_peer_id)),
        )
        challenge_id = self._store_challenge(
            options.challenge, "register", peer_id, rp_id, origins,
            account_peer_id=account_peer_id, grant_hash=grant["grant_hash"],
        )
        return {"challenge_id": challenge_id, "publicKey": json.loads(options_to_json(options))}

    def finish_registration(self, peer_id: str, challenge_id: str, credential: Dict) -> Dict:
        self._require_webauthn()
        ch = self.consume_challenge(challenge_id, "register", peer_id)
        try:
            verified = verify_registration_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(ch["challenge"]),
                expected_rp_id=ch["rp_id"],
                expected_origin=json.loads(ch["origins"]),
                require_user_verification=True,
            )
        except PasskeyError:
            raise
        except Exception:
            raise PasskeyError("verification_failed", "Your device couldn't create the passkey. Please try again.")
        self._consume_grant(ch["grant_hash"])

        transports = []
        if isinstance(credential, dict):
            transports = [t for t in (credential.get("response") or {}).get("transports") or [] if isinstance(t, str)]
        cred_id = bytes_to_base64url(verified.credential_id)
        now = self.clock()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO passkey_credentials (credential_id, account_peer_id, public_key, sign_count,
                        transports, aaguid, backed_up, created_at, last_used_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cred_id, ch["account_peer_id"], verified.credential_public_key, int(verified.sign_count or 0),
                     json.dumps(transports), str(getattr(verified, "aaguid", "") or ""),
                     1 if getattr(verified, "credential_backed_up", False) else 0, now, now),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            raise PasskeyError("credential_exists", "This passkey is already registered.")
        account = self.registry.link_peer(peer_id, ch["account_peer_id"], via="passkey_register")
        return account

    # ---------------------------------------------------------------- authentication
    def begin_authentication(self, peer_id: str, rp_id: str, origins: List[str], email: str = "") -> Dict:
        self._require_webauthn()
        peer_id = (peer_id or "").strip()
        if not peer_id:
            raise PasskeyError("peer_required", "Missing device id.")
        allow: List = []
        account_peer_id = ""
        if email:
            account = self.registry.get_account_by_email(email)
            if account:
                creds = self.list_credentials(account["peer_id"])
                if creds:
                    allow = self._descriptors(creds)
                    account_peer_id = account["peer_id"]
        options = generate_authentication_options(
            rp_id=rp_id,
            challenge=secrets.token_bytes(32),
            timeout=CHALLENGE_TTL_SECONDS * 1000,
            allow_credentials=allow,
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        challenge_id = self._store_challenge(
            options.challenge, "authenticate", peer_id, rp_id, origins, account_peer_id=account_peer_id
        )
        return {"challenge_id": challenge_id, "publicKey": json.loads(options_to_json(options))}

    def finish_authentication(self, peer_id: str, challenge_id: str, credential: Dict) -> Dict:
        self._require_webauthn()
        ch = self.consume_challenge(challenge_id, "authenticate", peer_id)
        if not isinstance(credential, dict):
            raise PasskeyError("verification_failed", "Passkey sign-in failed. Please try again.")
        cred_id = credential.get("id") or credential.get("rawId") or ""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM passkey_credentials WHERE credential_id = ?", (cred_id,)).fetchone()
        if not row:
            raise PasskeyError("unknown_passkey", "That passkey isn't registered with TinCan.", 401)
        if ch["account_peer_id"] and row["account_peer_id"] != ch["account_peer_id"]:
            raise PasskeyError("verification_failed", "Passkey sign-in failed. Please try again.", 401)
        user_handle = (credential.get("response") or {}).get("userHandle")
        if user_handle:
            expected = self._user_handle(row["account_peer_id"])
            try:
                ok = hmac.compare_digest(base64url_to_bytes(user_handle), expected)
            except Exception:
                ok = False
            if not ok:
                raise PasskeyError("verification_failed", "Passkey sign-in failed. Please try again.", 401)
        try:
            verified = verify_authentication_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(ch["challenge"]),
                expected_rp_id=ch["rp_id"],
                expected_origin=json.loads(ch["origins"]),
                credential_public_key=row["public_key"],
                credential_current_sign_count=int(row["sign_count"] or 0),
                require_user_verification=True,
            )
        except Exception:
            raise PasskeyError("verification_failed", "Passkey sign-in failed. Please try again.", 401)
        with self._connect() as conn:
            conn.execute(
                "UPDATE passkey_credentials SET sign_count = ?, last_used_at = ? WHERE credential_id = ?",
                (int(verified.new_sign_count or 0), self.clock(), cred_id),
            )
            conn.commit()
        return self.registry.link_peer(peer_id, row["account_peer_id"], via="passkey_login")

    # ---------------------------------------------------------------- email recovery
    def _client_allowed(self, client_key: str) -> bool:
        now = self.clock()
        with self._client_lock:
            hits = [t for t in self._client_hits.get(client_key, []) if t > now - 3600]
            if len(hits) >= CODE_MAX_PER_CLIENT_HOUR:
                self._client_hits[client_key] = hits
                return False
            hits.append(now)
            self._client_hits[client_key] = hits
            return True

    def request_recovery_code(self, email: str, client_key: str = "") -> Dict:
        email = (email or "").strip().lower()
        if not PeerAccountRegistry.validate_email(email):
            raise PasskeyError("invalid_email", "Enter the email on your account.")
        if not self._client_allowed(client_key or "unknown"):
            raise PasskeyError("rate_limited", "Too many code requests. Try again later.", 429)
        now = self.clock()
        with self._connect() as conn:
            recent = conn.execute(
                "SELECT COUNT(*) FROM recovery_codes WHERE email = ? AND created_at > ?",
                (email, now - CODE_EMAIL_WINDOW_SECONDS),
            ).fetchone()[0]
        if recent >= CODE_MAX_PER_EMAIL_WINDOW:
            raise PasskeyError("rate_limited", "Too many codes requested for this email. Wait 15 minutes and try again.", 429)

        response = {
            "status": "sent_if_eligible",
            "message": "If that email belongs to an account without a passkey, we sent it a 6-digit code.",
            "delivery_configured": mailer.delivery_configured(),
        }
        account = self.registry.get_account_by_email(email)
        if not account or self.has_passkey(account["peer_id"]):
            return response

        code = f"{secrets.randbelow(10 ** 6):06d}"
        salt = secrets.token_hex(8)
        with self._connect() as conn:
            conn.execute(
                "UPDATE recovery_codes SET used_at = ? WHERE email = ? AND used_at IS NULL", (now, email)
            )
            conn.execute(
                """
                INSERT INTO recovery_codes (account_peer_id, email, code_hash, salt, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account["peer_id"], email, self._hash("code", salt, email, code), salt, now, now + CODE_TTL_SECONDS),
            )
            conn.commit()
        minutes = CODE_TTL_SECONDS // 60
        mailer.send_email(
            to=email,
            subject="Your TinCan sign-in code",
            text=(
                f"Your TinCan Mesh OS code is {code}.\n\n"
                f"It expires in {minutes} minutes and can be used once to set up a passkey on your account. "
                "If you didn't ask for it, you can ignore this email."
            ),
        )
        return response

    def verify_recovery_code(self, email: str, code: str) -> str:
        """Check a code and return a single-use enrollment grant for a new passkey."""
        email = (email or "").strip().lower()
        code = "".join(ch for ch in str(code or "") if ch.isdigit())
        generic = PasskeyError("code_invalid", "That code is wrong or expired. Request a new one.", 400)
        now = self.clock()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM recovery_codes WHERE email = ? AND used_at IS NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                (email,),
            ).fetchone()
            if not row or row["expires_at"] < now:
                raise generic
            if row["attempts"] >= CODE_MAX_ATTEMPTS:
                raise PasskeyError("code_locked", "Too many wrong tries. Request a new code.", 429)
            conn.execute("UPDATE recovery_codes SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
            conn.commit()
            if len(code) != 6 or not hmac.compare_digest(self._hash("code", row["salt"], email, code), row["code_hash"]):
                if row["attempts"] + 1 >= CODE_MAX_ATTEMPTS:
                    raise PasskeyError("code_locked", "Too many wrong tries. Request a new code.", 429)
                raise generic
            cur = conn.execute(
                "UPDATE recovery_codes SET used_at = ? WHERE id = ? AND used_at IS NULL", (now, row["id"])
            )
            conn.commit()
            if cur.rowcount != 1:
                raise generic
        return self.issue_enrollment_grant(row["account_peer_id"], purpose="recovery")
