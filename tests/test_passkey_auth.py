import json
import logging
import sqlite3
import threading
import urllib.error
import urllib.request
import uuid
from types import SimpleNamespace

import pytest

from iot_federated_agent_memory import mailer, passkey_auth
from iot_federated_agent_memory.account_registry import (
    EMAIL_EXISTS_MESSAGE,
    EmailAlreadyRegisteredError,
    PeerAccountRegistry,
)
from iot_federated_agent_memory.passkey_auth import (
    CHALLENGE_TTL_SECONDS,
    CODE_MAX_ATTEMPTS,
    CODE_TTL_SECONDS,
    PasskeyAuthService,
    PasskeyError,
    resolve_relying_party,
)
from webauthn.helpers import bytes_to_base64url

RP = "iot-federated-agent-memory-production.up.railway.app"
ORIGINS = [f"https://{RP}"]


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def env(tmp_path):
    registry = PeerAccountRegistry(db_path=str(tmp_path / "peer_accounts.db"))
    clock = Clock()
    svc = PasskeyAuthService(registry, secret=b"x" * 32, clock=clock)
    return registry, svc, clock


@pytest.fixture
def outbox():
    sent = []
    mailer.set_email_sender(lambda m: sent.append(m) or mailer.SendResult(True, "test"))
    yield sent
    mailer.set_email_sender(None)


def register(registry, peer, email, name="Tony Example"):
    return registry.register_account(peer_id=peer, full_name=name, phone_number="+15615550199", email=email)


def fake_registration(monkeypatch, cred_id=b"cred-1", calls=None):
    def _verify(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        return SimpleNamespace(
            credential_id=cred_id, credential_public_key=b"pubkey", sign_count=0,
            aaguid="00000000-0000-0000-0000-000000000000", credential_backed_up=True,
        )
    monkeypatch.setattr(passkey_auth, "verify_registration_response", _verify)


def fake_authentication(monkeypatch, new_sign_count=1, calls=None):
    def _verify(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        return SimpleNamespace(new_sign_count=new_sign_count, user_verified=True)
    monkeypatch.setattr(passkey_auth, "verify_authentication_response", _verify)


def enroll(svc, peer, token, monkeypatch, cred_id=b"cred-1"):
    fake_registration(monkeypatch, cred_id=cred_id)
    opts = svc.begin_registration(peer, token, RP, ORIGINS)
    cred = {"id": bytes_to_base64url(cred_id), "rawId": bytes_to_base64url(cred_id), "type": "public-key",
            "response": {"transports": ["internal", "hybrid"]}}
    return svc.finish_registration(peer, opts["challenge_id"], cred)


# --------------------------------------------------------------- duplicate email
def test_duplicate_email_raises_friendly_error(env):
    registry, _, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    with pytest.raises(EmailAlreadyRegisteredError) as exc:
        register(registry, "peer-phone", "Tony@Example.com")
    assert str(exc.value) == EMAIL_EXISTS_MESSAGE
    assert "UNIQUE" not in str(exc.value)
    assert isinstance(exc.value, ValueError)  # existing ValueError handlers still work
    # Same peer re-syncing with its own email is still fine.
    assert register(registry, "peer-desktop", "tony@example.com")["email"] == "tony@example.com"


def test_integrity_error_race_never_leaks(env, monkeypatch):
    registry, _, _ = env

    def boom(*a, **k):
        raise sqlite3.IntegrityError("UNIQUE constraint failed: accounts.email")

    monkeypatch.setattr(PeerAccountRegistry, "_upsert_account", staticmethod(boom))
    with pytest.raises(EmailAlreadyRegisteredError):
        register(registry, "peer-x", "race@example.com")


# --------------------------------------------------------------- peer linking
def test_peer_linking_routes_lookups_and_billing_to_account(env):
    registry, _, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    registry.link_peer("peer-phone", "peer-desktop")
    registry.link_peer("peer-tablet", "peer-phone")  # links resolve to the primary account

    assert registry.get_account_by_peer("peer-phone")["peer_id"] == "peer-desktop"
    assert registry.get_account_by_peer("peer-desktop")["peer_id"] == "peer-desktop"
    assert registry.get_account_by_peer("peer-unknown") is None
    assert set(registry.list_linked_peers("peer-desktop")) == {"peer-phone", "peer-tablet"}

    registry.bill_tokens("peer-phone", 1, 1, 2, 0.0, "m")
    assert registry.get_account_by_peer("peer-desktop")["total_tokens_used"] == 2
    assert registry.credit_once("ref-1", "peer-tablet", "purchase", 5)["applied"]
    assert registry.get_account_by_peer("peer-desktop")["token_balance"] == 10 - 2 + 5
    assert registry.count_credit_events("peer-phone", "purchase", 0) == 1

    # A linked device re-syncing its profile updates the account instead of colliding.
    acc = register(registry, "peer-phone", "tony@example.com", name="Tony Updated")
    assert acc["peer_id"] == "peer-desktop" and acc["full_name"] == "Tony Updated"
    with sqlite3.connect(registry.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 1

    with pytest.raises(ValueError):
        registry.link_peer("peer-z", "peer-nobody")


def test_migration_is_additive_on_existing_db(tmp_path):
    db = str(tmp_path / "legacy.db")
    with sqlite3.connect(db) as conn:  # pre-passkey schema with live data
        conn.execute(
            "CREATE TABLE accounts (peer_id TEXT PRIMARY KEY, full_name TEXT NOT NULL, phone_number TEXT NOT NULL,"
            " email TEXT NOT NULL UNIQUE, created_at REAL NOT NULL, status TEXT DEFAULT 'active',"
            " token_balance INTEGER DEFAULT 10, credit_balance_usd REAL DEFAULT 0.10,"
            " total_tokens_used INTEGER DEFAULT 0, total_billed_usd REAL DEFAULT 0.0)"
        )
        conn.execute("INSERT INTO accounts (peer_id, full_name, phone_number, email, created_at, token_balance)"
                     " VALUES ('peer-old', 'Old User', '+15615550000', 'old@example.com', 1, 777)")
    for _ in range(2):  # idempotent
        registry = PeerAccountRegistry(db_path=db)
        PasskeyAuthService(registry, secret=b"s" * 32)
    acc = registry.get_account_by_peer("peer-old")
    assert acc["token_balance"] == 777 and acc["email"] == "old@example.com"
    assert acc["webauthn_user_id"] == ""


# --------------------------------------------------------------- RP ID
def test_rp_id_resolution_order():
    assert resolve_relying_party("req.example", {"TINCAN_RP_ID": RP, "TINCAN_PUBLIC_URL": "https://other.example"})[0] == RP
    rp, origins = resolve_relying_party("req.example", {"TINCAN_PUBLIC_URL": f"https://{RP}/"})
    assert rp == RP and origins == [f"https://{RP}"]  # full host, never the up.railway.app suffix
    assert resolve_relying_party(f"{RP}:443", {})[0] == RP
    rp, origins = resolve_relying_party("localhost:8080", {})
    assert rp == "localhost" and "http://localhost:8080" in origins
    with pytest.raises(PasskeyError):
        resolve_relying_party("", {})


# --------------------------------------------------------------- challenges
def test_challenge_lifecycle_single_use_expiry_and_peer_binding(env, monkeypatch):
    registry, svc, clock = env
    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    pk = opts["publicKey"]
    assert pk["rpId"] == RP and pk["userVerification"] == "required"

    with pytest.raises(PasskeyError) as exc:
        svc.consume_challenge(opts["challenge_id"], "register", "peer-phone")  # wrong purpose
    assert exc.value.code == "challenge_invalid"
    row = svc.consume_challenge(opts["challenge_id"], "authenticate", "peer-phone")
    assert row["rp_id"] == RP
    with pytest.raises(PasskeyError) as exc:
        svc.consume_challenge(opts["challenge_id"], "authenticate", "peer-phone")
    assert exc.value.code == "challenge_used"

    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    clock.t += CHALLENGE_TTL_SECONDS + 1
    with pytest.raises(PasskeyError) as exc:
        svc.consume_challenge(opts["challenge_id"], "authenticate", "peer-phone")
    assert exc.value.code == "challenge_expired"

    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    with pytest.raises(PasskeyError):
        svc.consume_challenge(opts["challenge_id"], "authenticate", "peer-attacker")
    with pytest.raises(PasskeyError):  # burned even though the first use failed
        svc.consume_challenge(opts["challenge_id"], "authenticate", "peer-phone")


# --------------------------------------------------------------- passkey flows (mocked webauthn)
def test_registration_requires_grant_and_uses_platform_uv(env, monkeypatch):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    with pytest.raises(PasskeyError) as exc:
        svc.begin_registration("peer-desktop", "", RP, ORIGINS)
    assert exc.value.code == "grant_required"
    with pytest.raises(PasskeyError):
        svc.begin_registration("peer-desktop", "forged-token", RP, ORIGINS)

    token = svc.issue_enrollment_grant("peer-desktop")
    opts = svc.begin_registration("peer-desktop", token, RP, ORIGINS)
    sel = opts["publicKey"]["authenticatorSelection"]
    assert sel["authenticatorAttachment"] == "platform"
    assert sel["residentKey"] == "preferred"
    assert sel["userVerification"] == "required"
    assert opts["publicKey"]["rp"]["id"] == RP

    calls = []
    fake_registration(monkeypatch, calls=calls)
    cred = {"id": "Y3JlZC0x", "response": {"transports": ["internal"]}}
    svc.finish_registration("peer-desktop", opts["challenge_id"], cred)
    assert calls[0]["expected_rp_id"] == RP
    assert calls[0]["expected_origin"] == ORIGINS
    assert calls[0]["require_user_verification"] is True
    stored = svc.list_credentials("peer-desktop")
    assert len(stored) == 1 and stored[0]["public_key"] == b"pubkey"
    assert json.loads(stored[0]["transports"]) == ["internal"] and stored[0]["sign_count"] == 0

    # The grant is single use.
    with pytest.raises(PasskeyError) as exc:
        svc.begin_registration("peer-desktop", token, RP, ORIGINS)
    assert exc.value.code == "grant_invalid"


def test_failed_registration_verification_is_friendly(env, monkeypatch):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    token = svc.issue_enrollment_grant("peer-desktop")
    opts = svc.begin_registration("peer-desktop", token, RP, ORIGINS)

    def bad(**kwargs):
        raise ValueError("Unexpected client data origin")

    monkeypatch.setattr(passkey_auth, "verify_registration_response", bad)
    with pytest.raises(PasskeyError) as exc:
        svc.finish_registration("peer-desktop", opts["challenge_id"], {"id": "x"})
    assert exc.value.code == "verification_failed"
    assert not svc.has_passkey("peer-desktop")
    # The grant survives a failed attempt so the user can retry.
    svc.begin_registration("peer-desktop", token, RP, ORIGINS)


def test_sign_in_links_new_device(env, monkeypatch):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    enroll(svc, "peer-desktop", svc.issue_enrollment_grant("peer-desktop"), monkeypatch)
    handle = svc._user_handle("peer-desktop")

    calls = []
    fake_authentication(monkeypatch, new_sign_count=7, calls=calls)
    opts = svc.begin_authentication("peer-phone", RP, ORIGINS, email="tony@example.com")
    assert opts["publicKey"]["allowCredentials"][0]["id"] == bytes_to_base64url(b"cred-1")
    cred = {"id": bytes_to_base64url(b"cred-1"), "response": {"userHandle": bytes_to_base64url(handle)}}
    account = svc.finish_authentication("peer-phone", opts["challenge_id"], cred)

    assert account["peer_id"] == "peer-desktop"
    assert registry.get_account_by_peer("peer-phone")["email"] == "tony@example.com"
    assert calls[0]["credential_public_key"] == b"pubkey"
    assert calls[0]["credential_current_sign_count"] == 0
    assert calls[0]["require_user_verification"] is True
    assert svc.list_credentials("peer-desktop")[0]["sign_count"] == 7
    # The phone can no longer register the same email as a fresh account; it's the same account now.
    assert register(registry, "peer-phone", "tony@example.com")["peer_id"] == "peer-desktop"


def test_sign_in_rejects_unknown_credential_wrong_user_handle_and_bad_signature(env, monkeypatch):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    enroll(svc, "peer-desktop", svc.issue_enrollment_grant("peer-desktop"), monkeypatch)
    fake_authentication(monkeypatch)

    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    with pytest.raises(PasskeyError) as exc:
        svc.finish_authentication("peer-phone", opts["challenge_id"], {"id": "bm9wZQ"})
    assert exc.value.code == "unknown_passkey"

    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    bad_handle = {"id": bytes_to_base64url(b"cred-1"), "response": {"userHandle": bytes_to_base64url(b"other")}}
    with pytest.raises(PasskeyError):
        svc.finish_authentication("peer-phone", opts["challenge_id"], bad_handle)

    def bad(**kwargs):
        raise ValueError("Could not verify authentication signature")

    monkeypatch.setattr(passkey_auth, "verify_authentication_response", bad)
    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    with pytest.raises(PasskeyError) as exc:
        svc.finish_authentication("peer-phone", opts["challenge_id"], {"id": bytes_to_base64url(b"cred-1")})
    assert exc.value.code == "verification_failed"
    assert registry.resolve_account_peer_id("peer-phone") == "peer-phone"  # never linked


# --------------------------------------------------------------- email recovery
def _code_from(outbox):
    import re
    return re.search(r"\b(\d{6})\b", outbox[-1].text).group(1)


def test_recovery_code_flow_hashed_and_grants_passkey(env, outbox, monkeypatch):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    res = svc.request_recovery_code("Tony@example.com", client_key="1.2.3.4")
    assert res["delivery_configured"] is True and len(outbox) == 1 and outbox[0].to == "tony@example.com"
    code = _code_from(outbox)
    with sqlite3.connect(registry.db_path) as conn:
        row = conn.execute("SELECT code_hash FROM recovery_codes").fetchone()
    assert row[0] != code and len(row[0]) == 64

    token = svc.verify_recovery_code("tony@example.com", code)
    account = enroll(svc, "peer-phone", token, monkeypatch)
    assert account["peer_id"] == "peer-desktop"
    assert registry.get_account_by_peer("peer-phone")["peer_id"] == "peer-desktop"
    with pytest.raises(PasskeyError):  # code is single use
        svc.verify_recovery_code("tony@example.com", code)

    # Once the account has a passkey, email codes are no longer issued for it.
    svc.request_recovery_code("tony@example.com", client_key="1.2.3.4")
    assert len(outbox) == 1


def test_recovery_code_expiry(env, outbox):
    registry, svc, clock = env
    register(registry, "peer-desktop", "tony@example.com")
    svc.request_recovery_code("tony@example.com")
    code = _code_from(outbox)
    clock.t += CODE_TTL_SECONDS + 1
    with pytest.raises(PasskeyError) as exc:
        svc.verify_recovery_code("tony@example.com", code)
    assert exc.value.code == "code_invalid"


def test_recovery_code_attempt_limit(env, outbox):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    svc.request_recovery_code("tony@example.com")
    code = _code_from(outbox)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(CODE_MAX_ATTEMPTS - 1):
        with pytest.raises(PasskeyError) as exc:
            svc.verify_recovery_code("tony@example.com", wrong)
        assert exc.value.code == "code_invalid"
    with pytest.raises(PasskeyError) as exc:
        svc.verify_recovery_code("tony@example.com", wrong)
    assert exc.value.code == "code_locked"
    with pytest.raises(PasskeyError) as exc:  # even the right code is refused now
        svc.verify_recovery_code("tony@example.com", code)
    assert exc.value.code == "code_locked"


def test_recovery_rate_limits_and_no_enumeration(env, outbox):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    for _ in range(3):
        svc.request_recovery_code("tony@example.com", client_key="a")
    with pytest.raises(PasskeyError) as exc:
        svc.request_recovery_code("tony@example.com", client_key="b")
    assert exc.value.status == 429
    # Unknown email: same response, nothing sent.
    before = len(outbox)
    res = svc.request_recovery_code("nobody@example.com", client_key="c")
    assert res["status"] == "sent_if_eligible" and len(outbox) == before
    # Per-client limit.
    for i in range(7):
        svc.request_recovery_code(f"u{i}@example.com", client_key="a")
    with pytest.raises(PasskeyError):
        svc.request_recovery_code("z@example.com", client_key="a")


def test_new_code_invalidates_previous(env, outbox):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    svc.request_recovery_code("tony@example.com")
    first = _code_from(outbox)
    svc.request_recovery_code("tony@example.com")
    second = _code_from(outbox)
    if first != second:
        with pytest.raises(PasskeyError):
            svc.verify_recovery_code("tony@example.com", first)
    assert svc.verify_recovery_code("tony@example.com", second)


def test_unconfigured_mailer_never_logs_code_in_production(env, monkeypatch, caplog):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    mailer.set_email_sender(None)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("TINCAN_ENV", "production")
    monkeypatch.setenv("TINCAN_EMAIL_DEV_LOG", "1")
    issued = {}
    real_randbelow = passkey_auth.secrets.randbelow
    monkeypatch.setattr(passkey_auth.secrets, "randbelow", lambda n: issued.setdefault("v", real_randbelow(n)))
    with caplog.at_level(logging.DEBUG):
        res = svc.request_recovery_code("tony@example.com")
    assert res["delivery_configured"] is False
    code = f"{issued['v']:06d}"
    assert "NOT delivered" in caplog.text
    assert code not in caplog.text
    assert "tony@example.com" not in caplog.text


# --------------------------------------------------------------- HTTP API
@pytest.fixture(scope="module")
def live_server():
    import server
    from server import HTTPServer, MeshGatewayHandler

    httpd = HTTPServer(("127.0.0.1", 8994), MeshGatewayHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:8994"
    httpd.shutdown()


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_api_register_duplicate_email_and_passkey_options(live_server):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    base = {"full_name": "Dup Tester", "phone_number": "+15615550111", "email": email}
    status, body = _post(f"{live_server}/api/account/register", {**base, "peer_id": f"peer-a-{uuid.uuid4().hex[:6]}"})
    assert status == 201 and body["enroll_token"] and body["has_passkey"] is False

    status, body = _post(f"{live_server}/api/account/register", {**base, "peer_id": f"peer-b-{uuid.uuid4().hex[:6]}"})
    assert status == 409
    assert body == {"error": EMAIL_EXISTS_MESSAGE, "code": "email_exists"}

    status, body = _post(f"{live_server}/api/passkey/login/options", {"peer_id": "peer-b"})
    assert status == 200 and body["challenge_id"] and body["publicKey"]["rpId"]

    status, body = _post(f"{live_server}/api/passkey/register/options", {"peer_id": "peer-b", "enroll_token": "nope"})
    assert status == 403 and body["code"] == "grant_invalid"

    status, body = _post(f"{live_server}/api/passkey/login/verify", {"peer_id": "peer-b", "challenge_id": "x", "credential": {}})
    assert status == 400 and "Traceback" not in json.dumps(body)


# --------------------------------------------------------------- real WebAuthn (software authenticator, no mocks)
class SoftAuthenticator:
    """Minimal platform authenticator: 'none' attestation, ES256, UV flag set."""

    def __init__(self, rp_id, origin, user_verified=True):
        from cryptography.hazmat.primitives.asymmetric import ec

        self.rp_id, self.origin = rp_id, origin
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.cred_id = uuid.uuid4().bytes
        self.count = 0
        self.flags = 0x01 | (0x04 if user_verified else 0)

    def _cose(self):
        nums = self.key.public_key().public_numbers()
        return {1: 2, 3: -7, -1: 1, -2: nums.x.to_bytes(32, "big"), -3: nums.y.to_bytes(32, "big")}

    def _client_data(self, typ, challenge_b64):
        return json.dumps({"type": typ, "challenge": challenge_b64, "origin": self.origin, "crossOrigin": False}).encode()

    def create(self, public_key):
        import hashlib
        import struct
        from webauthn.helpers import encode_cbor

        rp_hash = hashlib.sha256(self.rp_id.encode()).digest()
        attested = b"\x00" * 16 + struct.pack(">H", len(self.cred_id)) + self.cred_id + encode_cbor(self._cose())
        auth_data = rp_hash + bytes([self.flags | 0x40]) + struct.pack(">I", self.count) + attested
        att_obj = encode_cbor({"fmt": "none", "attStmt": {}, "authData": auth_data})
        cid = bytes_to_base64url(self.cred_id)
        return {"id": cid, "rawId": cid, "type": "public-key", "response": {
            "clientDataJSON": bytes_to_base64url(self._client_data("webauthn.create", public_key["challenge"])),
            "attestationObject": bytes_to_base64url(att_obj), "transports": ["internal"]}}

    def get(self, public_key, user_handle):
        import hashlib
        import struct
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        self.count += 1
        rp_hash = hashlib.sha256(self.rp_id.encode()).digest()
        auth_data = rp_hash + bytes([self.flags]) + struct.pack(">I", self.count)
        cdj = self._client_data("webauthn.get", public_key["challenge"])
        sig = self.key.sign(auth_data + hashlib.sha256(cdj).digest(), ec.ECDSA(hashes.SHA256()))
        cid = bytes_to_base64url(self.cred_id)
        return {"id": cid, "rawId": cid, "type": "public-key", "response": {
            "clientDataJSON": bytes_to_base64url(cdj), "authenticatorData": bytes_to_base64url(auth_data),
            "signature": bytes_to_base64url(sig), "userHandle": bytes_to_base64url(user_handle)}}


def test_real_webauthn_register_then_sign_in_from_new_device(env):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    device = SoftAuthenticator(RP, ORIGINS[0])

    opts = svc.begin_registration("peer-desktop", svc.issue_enrollment_grant("peer-desktop"), RP, ORIGINS)
    svc.finish_registration("peer-desktop", opts["challenge_id"], device.create(opts["publicKey"]))
    handle = svc._user_handle("peer-desktop")

    opts = svc.begin_authentication("peer-phone", RP, ORIGINS)
    account = svc.finish_authentication("peer-phone", opts["challenge_id"], device.get(opts["publicKey"], handle))
    assert account["peer_id"] == "peer-desktop"
    assert registry.get_account_by_peer("peer-phone")["email"] == "tony@example.com"
    assert svc.list_credentials("peer-desktop")[0]["sign_count"] == 1

    # Replaying the same signed assertion against a fresh challenge fails.
    opts2 = svc.begin_authentication("peer-tablet", RP, ORIGINS)
    replay = device.get(opts["publicKey"], handle)
    with pytest.raises(PasskeyError):
        svc.finish_authentication("peer-tablet", opts2["challenge_id"], replay)


def test_real_webauthn_rejects_wrong_origin_and_missing_user_verification(env):
    registry, svc, _ = env
    register(registry, "peer-desktop", "tony@example.com")
    phishing = SoftAuthenticator(RP, "https://evil.example")
    opts = svc.begin_registration("peer-desktop", svc.issue_enrollment_grant("peer-desktop"), RP, ORIGINS)
    with pytest.raises(PasskeyError):
        svc.finish_registration("peer-desktop", opts["challenge_id"], phishing.create(opts["publicKey"]))

    no_uv = SoftAuthenticator(RP, ORIGINS[0], user_verified=False)
    opts = svc.begin_registration("peer-desktop", svc.issue_enrollment_grant("peer-desktop"), RP, ORIGINS)
    with pytest.raises(PasskeyError):
        svc.finish_registration("peer-desktop", opts["challenge_id"], no_uv.create(opts["publicKey"]))

    wrong_rp = SoftAuthenticator("up.railway.app", ORIGINS[0])
    opts = svc.begin_registration("peer-desktop", svc.issue_enrollment_grant("peer-desktop"), RP, ORIGINS)
    with pytest.raises(PasskeyError):
        svc.finish_registration("peer-desktop", opts["challenge_id"], wrong_rp.create(opts["publicKey"]))
    assert not svc.has_passkey("peer-desktop")
