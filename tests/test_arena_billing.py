"""Brain Arena duels bill the signed-in account (server-side session), never the shared bucket."""

import json
import sqlite3
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory.account_registry import ArenaBillingError, PeerAccountRegistry


@pytest.fixture()
def env(tmp_path, monkeypatch):
    import server

    # Use the registry class the live server module was imported with (another test
    # module purges sys.modules, so the top-level import can be a different copy).
    reg = server.PeerAccountRegistry(db_path=str(tmp_path / "accounts.db"))
    monkeypatch.setattr(server, "account_registry", reg)
    calls = []

    def fake_dispatch(alias, messages, temperature=0.7, max_tokens=512):
        calls.append(alias)
        return {
            "choices": [{"message": {"content": f"answer from {alias}"}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 80, "total_tokens": 100},
            "cost_usd": 0.0015 if alias == "gemini-brain" else 0.0042,
        }

    monkeypatch.setattr(server.router, "dispatch_completion", fake_dispatch)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield {"url": f"http://127.0.0.1:{httpd.server_address[1]}", "reg": reg, "calls": calls, "server": server}
    httpd.shutdown()


def _req(url, body=None, token=None, cookie=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if cookie:
        headers["Cookie"] = cookie
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), dict(e.headers)


def _account(reg, peer_id, tokens=5000):
    reg.register_account(peer_id=peer_id, full_name="Duel Tester", phone_number="+15615550199",
                         email=f"{peer_id}@example.com", initial_tokens=tokens, initial_credit_usd=1.0)
    return reg.create_session(peer_id)


def _ledger(reg, peer_id):
    with sqlite3.connect(reg.db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute("SELECT * FROM token_ledger WHERE peer_id = ? ORDER BY id", (peer_id,))]


def test_duel_without_sign_in_is_refused_and_shared_bucket_untouched(env):
    url, reg = env["url"], env["reg"]
    code, body, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"})
    assert code == 401 and body["code"] == "sign_in_required"
    # A client-sent peer_id is not an identity: still refused, nothing dispatched, nothing billed.
    code, body, _ = _req(f"{url}/api/chat", {"model": "gemini-brain", "prompt": "hi", "arena": True,
                                             "peer_id": "peer", "match_id": "x", "arena_side": "A"})
    assert code == 401
    assert env["calls"] == []
    assert reg.get_account_by_peer("peer") is None
    assert _ledger(reg, "peer") == []


def test_full_duel_bills_the_signed_in_account(env):
    url, reg = env["url"], env["reg"]
    token = _account(reg, "acct-alice")
    code, body, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain",
                                                         "prompt": "Explain CRDTs"}, token=token)
    assert code == 201
    match_id = body["match"]["match_id"]

    # peer_id in the body is ignored: the session decides who pays.
    code, a, _ = _req(f"{url}/api/chat", {"model": "gemini-brain", "prompt": "Explain CRDTs", "arena": True,
                                          "match_id": match_id, "arena_side": "A", "peer_id": "peer"}, token=token)
    assert code == 200 and a["billing"]["peer_id"] == "acct-alice" and a["billing"]["kind"] == "arena"
    code, b, _ = _req(f"{url}/api/chat", {"model": "claude-brain", "prompt": "Explain CRDTs", "arena": True,
                                          "match_id": match_id, "arena_side": "B"}, token=token)
    assert code == 200
    assert b["billing"]["match_total_tokens"] == 200
    assert b["billing"]["match_total_cost_usd"] == pytest.approx(0.0057)

    acct = reg.get_account_by_peer("acct-alice")
    assert acct["token_balance"] == 4800
    assert acct["total_billed_usd"] == pytest.approx(0.0057)
    assert reg.get_account_by_peer("peer") is None  # shared bucket never touched

    rows = _ledger(reg, "acct-alice")
    assert [(r["kind"], r["match_id"], r["arena_side"], r["model"]) for r in rows] == [
        ("arena", match_id, "A", "gemini-brain"), ("arena", match_id, "B", "claude-brain")]
    note = json.loads(rows[0]["note"])
    assert note == {"arena_match": match_id, "side": "A", "model_a": "gemini-brain", "model_b": "claude-brain"}

    match = reg.get_arena_match(match_id)
    assert match["status"] == "complete" and match["account_peer_id"] == "acct-alice"
    assert match["tokens_a"] == 100 and match["cost_a_usd"] == pytest.approx(0.0015)
    assert match["tokens_b"] == 100 and match["cost_b_usd"] == pytest.approx(0.0042)

    # Vote uses the match record for the models and stores the cost with the match.
    code, v, _ = _req(f"{url}/api/mesh/arena/vote", {"match_id": match_id, "winner_side": "B",
                                                     "model_a": "spoofed", "model_b": "spoofed"}, token=token)
    assert code == 200 and v["winner_alias"] == "claude-brain" and v["match_id"] == match_id
    assert v["cost_usd"] == pytest.approx(0.0057) and v["tokens"] == 200
    assert env["server"].mesh_os.arena_matches[-1]["match_id"] == match_id
    assert reg.get_arena_match(match_id)["winner_side"] == "B"
    code, _, _ = _req(f"{url}/api/mesh/arena/vote", {"match_id": match_id, "winner_side": "A"}, token=token)
    assert code == 409


def test_402_when_account_cannot_cover_a_side(env):
    url, reg = env["url"], env["reg"]
    # Zero balance: the match itself is refused.
    broke = _account(reg, "acct-broke", tokens=0)
    code, body, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"}, token=broke)
    assert code == 402

    # Enough for side A's worst case but not side B's after A is billed.
    need = reg.estimate_side_tokens("hi", 512)
    tight = _account(reg, "acct-tight", tokens=need + 50)
    _, m, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"}, token=tight)
    mid = m["match"]["match_id"]
    code, _, _ = _req(f"{url}/api/chat", {"model": "gemini-brain", "prompt": "hi", "arena": True,
                                          "match_id": mid, "arena_side": "A"}, token=tight)
    assert code == 200
    code, body, _ = _req(f"{url}/api/chat", {"model": "claude-brain", "prompt": "hi", "arena": True,
                                             "match_id": mid, "arena_side": "B"}, token=tight)
    assert code == 402 and body["code"] == "insufficient_tokens" and body["side"] == "B"
    assert body["required_tokens"] == need and body["token_balance"] == need + 50 - 100
    assert env["calls"] == ["gemini-brain"]  # side B was never dispatched
    assert reg.get_arena_match(mid)["tokens_b"] is None


def test_match_ownership_side_and_replay_are_enforced(env):
    url, reg = env["url"], env["reg"]
    alice = _account(reg, "acct-a")
    mallory = _account(reg, "acct-m")
    _, m, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"}, token=alice)
    mid = m["match"]["match_id"]
    body = {"model": "gemini-brain", "prompt": "hi", "arena": True, "match_id": mid, "arena_side": "A"}
    assert _req(f"{url}/api/chat", body, token=mallory)[0] == 403
    assert _req(f"{url}/api/chat", {**body, "model": "claude-brain"}, token=alice)[0] == 400
    assert _req(f"{url}/api/chat", {**body, "arena_side": "C"}, token=alice)[0] == 400
    assert _req(f"{url}/api/chat", body, token=alice)[0] == 200
    assert _req(f"{url}/api/chat", body, token=alice)[0] == 409  # a side bills once
    assert _req(f"{url}/api/mesh/arena/vote", {"match_id": mid, "winner_side": "A"}, token=alice)[0] == 409  # B not run
    assert _req(f"{url}/api/mesh/arena/vote", {"match_id": mid, "winner_side": "A"})[0] == 401
    assert reg.get_account_by_peer("acct-m")["token_balance"] == 5000


def test_signup_sets_http_only_session_cookie_and_logout_revokes(env):
    url, reg = env["url"], env["reg"]
    code, body, headers = _req(f"{url}/api/account/register", {
        "peer_id": "peer-newbie", "name": "New Bie", "phone": "+15615550123", "email": "newbie@example.com",
        "username": "newbie"})
    assert code == 201 and body["signed_in"] is True
    set_cookie = headers.get("Set-Cookie", "")
    assert set_cookie.startswith("tincan_session=") and "HttpOnly" in set_cookie and "SameSite=Lax" in set_cookie
    cookie = set_cookie.split(";", 1)[0]
    assert cookie.split("=", 1)[1] not in json.dumps(body)  # token only in the cookie
    code, s, _ = _req(f"{url}/api/account/session", cookie=cookie)
    assert s == {**s, "signed_in": True, "peer_id": "peer-newbie"}
    # Cookie works for the arena too (10 starter tokens is enough to open a match).
    code, _, _ = _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"}, cookie=cookie)
    assert code == 201
    _req(f"{url}/api/account/logout", {}, cookie=cookie)
    assert _req(f"{url}/api/account/session", cookie=cookie)[1] == {"signed_in": False}
    assert _req(f"{url}/api/mesh/arena/match", {"model_a": "gemini-brain", "model_b": "claude-brain"}, cookie=cookie)[0] == 401
    # Re-registering an existing (non-guest) account does not hand out a session.
    code, body, headers = _req(f"{url}/api/account/register", {
        "peer_id": "peer-newbie", "name": "New Bie", "phone": "+15615550123", "email": "newbie@example.com"})
    assert "Set-Cookie" not in headers


def test_registry_session_expiry_and_unknown_tokens(tmp_path):
    reg = PeerAccountRegistry(db_path=str(tmp_path / "a.db"))
    reg.register_account(peer_id="p1", full_name="Pat One", phone_number="+15615550100", email="p1@example.com")
    tok = reg.create_session("p1", ttl_seconds=1)
    assert reg.resolve_session(tok)["peer_id"] == "p1"
    assert reg.resolve_session("nope") is None and reg.resolve_session("") is None
    import time as _t
    _t.sleep(1.1)
    assert reg.resolve_session(tok) is None
    with pytest.raises(ValueError):
        reg.create_session("ghost")
    with pytest.raises(ArenaBillingError):
        reg.create_arena_match("ghost", "gemini-brain", "claude-brain")
