"""HTTP tests: per-user brain context endpoints, isolation, duel injection and billing.

Identity is the server-side session (Bearer token / tincan_session cookie).
Context duels go through the per-account arena flow (/api/mesh/arena/match,
then /api/chat arena=true per side). Runs with OPENROUTER_API_KEY unset; the
only thing mocked is the outbound OpenRouter chat-completions HTTP call.
"""

import base64
import http.client
import io
import json
import os
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory import ai_gateway
from iot_federated_agent_memory.arena_context import ArenaContextRegistry, DriveMirrorSource


@pytest.fixture(autouse=True)
def _no_paid_calls(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture()
def ctx_registry(tmp_path, monkeypatch):
    reg = ArenaContextRegistry(str(tmp_path / "arena_context"), drive=DriveMirrorSource(module=None))
    monkeypatch.setattr(server.ARENA_CONTEXT_API, "registry", reg)
    return reg


@pytest.fixture(scope="module")
def base_url():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield httpd.server_address
    httpd.shutdown()


class Acct(str):
    """An account peer_id that also carries its session token."""
    token = ""


def _account(tokens=5000):
    pid = f"ctx-{uuid.uuid4().hex[:10]}"
    server.account_registry.register_account(
        peer_id=pid, full_name="Ctx Tester", phone_number="+15615550100",
        email=f"{pid}@example.com", initial_tokens=tokens, initial_credit_usd=1.0)
    acct = Acct(pid)
    acct.token = server.account_registry.create_session(pid)
    return acct


def call(addr, method, path, body=None, peer=None, headers=None, token=None):
    """``peer`` is an Acct (signed in via its session) or a raw string sent only
    as an untrusted X-TinCan-Peer header / peer_id, which must never authenticate."""
    conn = http.client.HTTPConnection(*addr, timeout=30)
    h = dict(headers or {})
    if isinstance(peer, Acct):
        h["Authorization"] = f"Bearer {peer.token}"
    elif peer is not None:
        h["X-TinCan-Peer"] = peer
    if token is not None:
        h["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=data, headers=h)
    resp = conn.getresponse()
    raw = resp.read()
    conn.close()
    try:
        return resp.status, json.loads(raw.decode() or "{}")
    except ValueError:
        return resp.status, raw.decode(errors="replace")


def q(**kw):
    return urllib.parse.urlencode(kw)


class FakeOpenRouter:
    """Stands in for urllib.request.urlopen, only for openrouter.ai URLs."""

    def __init__(self, real):
        self.real = real
        self.calls = []

    def __call__(self, req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "openrouter.ai" not in url:
            return self.real(req, *args, **kwargs)
        if not url.endswith("/chat/completions"):
            raise urllib.error.URLError("offline test: only chat completions are faked")
        payload = json.loads(req.data.decode())
        self.calls.append(payload)
        system = " ".join(m["content"] for m in payload["messages"] if m["role"] == "system")
        body = {
            "id": f"gen-{len(self.calls)}",
            "model": payload["model"],
            "choices": [{"message": {"role": "assistant",
                                     "content": f"{payload['model']} answered with {system.count('<file ')} file(s)"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "cost": 0.0012},
        }
        return _Resp(json.dumps(body).encode())


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture()
def fake_llm(monkeypatch):
    fake = FakeOpenRouter(urllib.request.urlopen)
    monkeypatch.setattr(ai_gateway.urllib.request, "urlopen", fake)
    # A non-secret placeholder so dispatch_completion takes its real HTTP path.
    monkeypatch.setattr(server.router, "openrouter_key", "test-placeholder-not-a-key")
    return fake


def _ledger(peer_id):
    with sqlite3.connect(server.account_registry.db_path) as conn:
        return conn.execute("SELECT COUNT(*), COALESCE(SUM(total_tokens),0) FROM token_ledger WHERE peer_id = ?",
                            (peer_id,)).fetchone()


# --------------------------------------------------------------------- auth
@pytest.mark.parametrize("peer", [None, "", "peer", "anonymous", "never-registered-peer", "REAL"])
def test_endpoints_require_a_session(base_url, ctx_registry, peer):
    if peer == "REAL":
        peer = str(_account())  # a real account's peer_id is not a credential by itself
    for method, path, body in (
        ("GET", "/api/arena/context/files?agent_id=brain-a", None),
        ("GET", "/api/arena/context/search?agent_id=brain-a&q=x", None),
        ("POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "peer_id": peer,
                                               "files": [{"name": "a.md", "content": "x"}]}),
    ):
        status, data = call(base_url, method, path, body, peer=peer)
        assert status == 401, (path, peer, data)
        assert data["code"] == "sign_in_required"
    status, _ = call(base_url, "GET", "/api/arena/context/files?agent_id=brain-a", token="not-a-session")
    assert status == 401


def test_guest_mesh_local_ledger_is_refused(base_url, ctx_registry):
    guest = f"guest-{uuid.uuid4().hex[:8]}"
    server.account_registry.bill_tokens(peer_id=guest, prompt_tokens=0, completion_tokens=0,
                                        total_tokens=0, cost_usd=0.0, model="x")  # auto-provisions @mesh.local
    token = server.account_registry.create_session(guest)
    status, data = call(base_url, "GET", "/api/arena/context/status", token=token)
    assert status == 403 and data["code"] == "shared_bucket_refused"


# ------------------------------------------------------------ endpoints
def test_ingest_list_read_search_delete(base_url, ctx_registry):
    me = _account()
    note = "# Deploys\nTinCan deploys to Railway on push to main; the volume is mounted at /data."
    status, data = call(base_url, "POST", "/api/arena/context/ingest", {
        "agent_id": "brain-a",
        "files": [
            {"name": "deploy.md", "content": note, "source": "paste"},
            {"name": "upload.txt", "content_b64": base64.b64encode(b"Uploaded: passkeys use the full host.").decode()},
        ]}, peer=me)
    assert status == 200, data
    assert [a["path"] for a in data["added"]] == ["/pasted/deploy.md", "/uploads/upload.txt"]

    status, data = call(base_url, "GET", "/api/arena/context/files?" + q(agent_id="brain-a"), peer=me)
    assert status == 200 and data["count"] == 2
    assert {f["path"] for f in data["files"]} == {"/pasted/deploy.md", "/uploads/upload.txt"}

    status, data = call(base_url, "GET", "/api/arena/context/file?" + q(agent_id="brain-a", path="/pasted/deploy.md"), peer=me)
    assert status == 200 and data["content"] == note

    status, data = call(base_url, "GET", "/api/arena/context/search?" + q(agent_id="brain-a", q="where is the volume mounted"), peer=me)
    assert status == 200 and data["files"][0] == "/pasted/deploy.md"
    assert "mounted at /data" in data["snippets"][0]["text"]

    status, data = call(base_url, "GET", "/api/arena/context/status", peer=me)
    assert status == 200 and data["auth"] == "session" and data["account"]["peer_id"] == me
    assert [a["agent_id"] for a in data["agents"]] == ["brain-a"]

    status, data = call(base_url, "POST", "/api/arena/context/delete", {"agent_id": "brain-a", "path": "/uploads/upload.txt"}, peer=me)
    assert status == 200 and data["file_count"] == 1


def test_client_peer_id_never_selects_the_store(base_url, ctx_registry):
    alice, bob = _account(), _account()
    call(base_url, "POST", "/api/arena/context/ingest",
         {"agent_id": "brain-a", "files": [{"name": "n.md", "content": "alice only"}]}, peer=alice)
    # Bob signed in, claiming to be Alice via header, body and query: still Bob's store.
    status, data = call(base_url, "GET", "/api/arena/context/files?" + q(agent_id="brain-a", peer_id=str(alice)),
                        peer=bob, headers={"X-TinCan-Peer": str(alice)})
    assert status == 200 and data["count"] == 0


def test_no_cross_user_access(base_url, ctx_registry):
    alice, bob = _account(), _account()
    secret = "Alice's vault phrase is periwinkle-42."
    status, _ = call(base_url, "POST", "/api/arena/context/ingest",
                     {"agent_id": "brain-a", "files": [{"name": "secret.md", "content": secret}]}, peer=alice)
    assert status == 200

    # Same agent_id, other user: an empty, separate store.
    status, data = call(base_url, "GET", "/api/arena/context/files?agent_id=brain-a", peer=bob)
    assert status == 200 and data["count"] == 0
    status, data = call(base_url, "GET", "/api/arena/context/file?" + q(agent_id="brain-a", path="/uploads/secret.md"), peer=bob)
    assert status == 404
    status, data = call(base_url, "GET", "/api/arena/context/search?" + q(agent_id="brain-a", q="vault phrase periwinkle"), peer=bob)
    assert status == 200 and data["snippets"] == []
    status, data = call(base_url, "POST", "/api/arena/context/delete", {"agent_id": "brain-a", "path": "/uploads/secret.md"}, peer=bob)
    assert status == 404
    status, data = call(base_url, "GET", "/api/arena/context/agents", peer=bob)
    assert all(a["file_count"] == 0 for a in data["agents"])

    # The account is never a request parameter: naming Alice in the body changes nothing.
    status, data = call(base_url, "GET", "/api/arena/context/files?" + q(agent_id="brain-a", peer_id=alice, account=alice), peer=bob)
    assert data["count"] == 0

    # Bob's duel cannot see Alice's files either.
    status, data = call(base_url, "GET", "/api/arena/context/files?agent_id=brain-a", peer=alice)
    assert data["count"] == 1
    a_dir = ctx_registry.store(alice, "brain-a").dir
    b_dir = ctx_registry.store(bob, "brain-a").dir
    assert a_dir != b_dir and not b_dir.startswith(a_dir) and not a_dir.startswith(b_dir)


@pytest.mark.parametrize("name", ["../../etc/passwd", "/uploads/../../../peer_accounts.db", "..", "a/../../b.md", "x\\..\\y"])
def test_ingest_rejects_path_traversal(base_url, ctx_registry, name):
    me = _account()
    status, data = call(base_url, "POST", "/api/arena/context/ingest",
                        {"agent_id": "brain-a", "files": [{"name": name, "content": "pwn"}]}, peer=me)
    assert status == 400
    assert data["added"] == [] and data["errors"]


@pytest.mark.parametrize("path", ["../../etc/passwd", "/uploads/../../x", "%2e%2e/%2e%2e/etc/passwd"])
def test_read_rejects_path_traversal(base_url, ctx_registry, path):
    me = _account()
    raw_q = "agent_id=brain-a&path=" + (path if "%" in path else urllib.parse.quote(path))
    status, data = call(base_url, "GET", "/api/arena/context/file?" + raw_q, peer=me)
    assert status == 400 and data["code"] == "path_traversal"


@pytest.mark.parametrize("agent", ["../brain-a", "brain-a/../../x", "BRAIN A", "", "a" * 60])
def test_agent_id_cannot_escape(base_url, ctx_registry, agent):
    me = _account()
    status, data = call(base_url, "GET", "/api/arena/context/files?" + q(agent_id=agent), peer=me)
    assert status == 400 and data["code"] == "bad_agent_id"


def test_import_only_from_own_space(base_url, ctx_registry, tmp_path, monkeypatch):
    from iot_federated_agent_memory.agent_space import AgentSpaceManager
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    monkeypatch.setattr(server.ARENA_CONTEXT_API, "space_manager_getter", lambda: sm)
    alice, bob = _account(), _account()
    sm.get_or_create_space("user", alice).write_file("/plans/q4.md", "Alice Q4: ship arena context.", updated_by="user")
    sm.get_or_create_space("user", bob).write_file("/bob.md", "Bob's private notes.", updated_by="user")

    status, data = call(base_url, "POST", "/api/arena/context/import",
                        {"agent_id": "brain-b", "space_owner": str(alice)}, peer=alice)
    assert status == 200 and [a["path"] for a in data["added"]] == ["/my-space/plans/q4.md"]

    status, data = call(base_url, "POST", "/api/arena/context/import",
                        {"agent_id": "brain-b", "space_owner": str(bob)}, peer=alice)
    assert status == 403 and data["code"] == "not_your_space"


def test_drive_link_refused_without_mirror(base_url, ctx_registry):
    me = _account()
    status, data = call(base_url, "POST", "/api/arena/context/drive/link",
                        {"agent_id": "brain-a", "drive_path": "/dev"}, peer=me)
    assert status == 403 and data["code"] == "drive_mirror_unavailable"


def test_drive_link_uses_real_drive_mirror_on_localhost(base_url, tmp_path, monkeypatch):
    """Real drive_mirror.py: linked from a loopback request, refused through a proxy hop."""
    home = tmp_path / "home"
    (home / "dev").mkdir(parents=True)
    (home / "dev" / "plan.md").write_text("Launch plan: ship the arena context panel on Friday.")
    monkeypatch.setenv("TINCAN_DRIVE_ROOT", str(home))
    monkeypatch.delenv("TINCAN_DRIVE_MIRROR", raising=False)
    for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID", "RAILWAY_STATIC_URL"):
        monkeypatch.delenv(k, raising=False)
    reg = ArenaContextRegistry(str(tmp_path / "arena_context"), drive=DriveMirrorSource())
    monkeypatch.setattr(server.ARENA_CONTEXT_API, "registry", reg)
    me = _account()

    status, data = call(base_url, "POST", "/api/arena/context/drive/link",
                        {"agent_id": "brain-a", "drive_path": "/dev/plan.md"}, peer=me,
                        headers={"X-Forwarded-For": "203.0.113.9"})
    assert status == 403 and data["code"] == "drive_mirror_unavailable"

    status, data = call(base_url, "POST", "/api/arena/context/drive/link",
                        {"agent_id": "brain-a", "drive_path": "/dev/plan.md"}, peer=me)
    assert status == 200, data
    status, data = call(base_url, "GET", "/api/arena/context/search?" + q(agent_id="brain-a", q="launch plan arena"),
                        peer=me)
    assert data["files"] == ["/drive/dev/plan.md"]
    status, data = call(base_url, "POST", "/api/arena/context/drive/link",
                        {"agent_id": "brain-a", "drive_path": "/../../etc/passwd"}, peer=me)
    assert status in (400, 403)


# ------------------------------------------------------------------- duel
def _duel(addr, acct, prompt, sides):
    """Run a duel through the per-account billing flow: match, then A, then B."""
    status, m = call(addr, "POST", "/api/mesh/arena/match",
                     {"model_a": sides["A"]["model"], "model_b": sides["B"]["model"], "prompt": prompt}, peer=acct)
    assert status == 201, m
    out = {}
    for side in ("A", "B"):
        body = {"model": sides[side]["model"], "prompt": prompt, "arena": True,
                "match_id": m["match"]["match_id"], "arena_side": side}
        body.update({k: v for k, v in sides[side].items() if k != "model"})
        out[side] = call(addr, "POST", "/api/chat", body, peer=acct)
    return m["match"]["match_id"], out


def test_duel_injects_each_brains_own_files_and_bills_the_caller(base_url, ctx_registry, fake_llm):
    alice, bob = _account(tokens=5000), _account(tokens=5000)
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "files": [
        {"name": "railway.md", "content": "Railway volume for TinCan is mounted at /data (brain A notes)."}]}, peer=alice)
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-b", "files": [
        {"name": "volume.md", "content": "Brain B notes: the TinCan Railway volume holds peer_accounts.db."}]}, peer=alice)
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "files": [
        {"name": "bob.md", "content": "Bob's Railway volume secret is tangerine."}]}, peer=bob)
    peer_before = _ledger("peer")
    bob_before = server.account_registry.get_account_by_peer(bob)["token_balance"]

    prompt = "Where is the TinCan Railway volume mounted?"
    match_id, res = _duel(base_url, alice, prompt, {
        "A": {"model": "gemini-brain", "agent_id": "brain-a"},
        "B": {"model": "claude-brain", "agent_id": "brain-b"},
    })
    (sa, a), (sb, b) = res["A"], res["B"]
    assert sa == 200 and sb == 200, (a, b)
    assert len(fake_llm.calls) == 2

    sys_a, sys_b = fake_llm.calls[0]["messages"][0], fake_llm.calls[1]["messages"][0]
    assert sys_a["role"] == "system" and "mounted at /data" in sys_a["content"]
    assert "/uploads/railway.md" in sys_a["content"] and "volume.md" not in sys_a["content"]
    assert "peer_accounts.db" in sys_b["content"] and "railway.md" not in sys_b["content"]
    for c in fake_llm.calls:
        assert "tangerine" not in json.dumps(c)  # never another user's files
        assert c["messages"][-1] == {"role": "user", "content": prompt}

    assert a["arena_context"]["files"] == ["/uploads/railway.md"]
    assert b["arena_context"]["files"] == ["/uploads/volume.md"]
    assert a["arena_context"]["snippets"][0]["text"].startswith("Railway volume")
    assert a["choices"][0]["message"]["content"].endswith("answered with 1 file(s)")

    # Billing: both sides charged to Alice's own account through the arena match, never the shared bucket.
    assert a["billing"]["peer_id"] == alice and b["billing"]["peer_id"] == alice
    assert a["arena"]["match_id"] == match_id
    assert server.account_registry.get_account_by_peer(alice)["token_balance"] == 5000 - 240
    assert _ledger(alice) == (2, 240)
    assert _ledger("peer") == peer_before
    assert server.account_registry.get_account_by_peer(bob)["token_balance"] == bob_before


def test_duel_without_context_sends_no_system_message(base_url, ctx_registry, fake_llm):
    me = _account()
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "files": [
        {"name": "n.md", "content": "Zebras migrate in July."}]}, peer=me)
    _mid, res = _duel(base_url, me, "When do zebras migrate?", {
        "A": {"model": "gemini-brain", "agent_id": "brain-a", "use_context": False},
        "B": {"model": "claude-brain", "agent_id": "brain-a"},
    })
    assert [len(c["messages"]) for c in fake_llm.calls] == [1, 2]
    assert res["A"][1]["arena_context"]["enabled"] is False
    assert res["B"][1]["arena_context"]["files"] == ["/uploads/n.md"]


def test_context_side_rejects_bad_agent_before_any_call(base_url, ctx_registry, fake_llm):
    me = _account()
    _mid, res = _duel(base_url, me, "hi", {
        "A": {"model": "gemini-brain", "agent_id": "../other"},
        "B": {"model": "claude-brain", "agent_id": "brain-b"},
    })
    assert res["A"][0] == 400 and res["A"][1]["code"] == "bad_agent_id"
    assert len(fake_llm.calls) == 1  # only side B ran


def test_context_duel_without_session_never_reaches_the_model(base_url, ctx_registry, fake_llm):
    victim = _account()
    status, data = call(base_url, "POST", "/api/chat", {"model": "gemini-brain", "prompt": "hi", "arena": True,
                                                       "match_id": "x", "arena_side": "A", "agent_id": "brain-a",
                                                       "peer_id": str(victim)}, peer=str(victim))
    assert status == 401
    assert fake_llm.calls == []


def test_context_tokens_count_toward_the_side_estimate(base_url, ctx_registry, fake_llm):
    """A big context can push a side over the balance: refused (402) before dispatch."""
    me = _account(tokens=400)
    big = "Railway volume notes. " + ("The volume is mounted at /data. " * 200)
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "files": [
        {"name": "big.md", "content": big}]}, peer=me)
    _mid, res = _duel(base_url, me, "Where is the Railway volume mounted?", {
        "A": {"model": "gemini-brain", "agent_id": "brain-a", "max_tokens": 64},
        "B": {"model": "claude-brain", "agent_id": "brain-a", "use_context": False, "max_tokens": 64},
    })
    assert res["A"][0] == 402, res["A"]
    assert res["B"][0] == 200
    assert [len(c["messages"]) for c in fake_llm.calls] == [1]


def test_duel_offline_without_key_still_bills_the_caller(base_url, ctx_registry, monkeypatch):
    """No key and no mock: the gateway's offline simulation runs, nothing leaves the box."""
    monkeypatch.setattr(server.router, "openrouter_key", None)
    me = _account(tokens=1000)
    call(base_url, "POST", "/api/arena/context/ingest", {"agent_id": "brain-a", "files": [
        {"name": "n.md", "content": "hello offline brain"}]}, peer=me)
    _mid, res = _duel(base_url, me, "hello offline", {
        "A": {"model": "gemini-brain", "agent_id": "brain-a"},
        "B": {"model": "claude-brain", "agent_id": "brain-b"},
    })
    assert res["A"][0] == 200 and res["B"][0] == 200
    assert res["A"][1]["id"].startswith("sim-")
    assert res["A"][1]["arena_context"]["files"] == ["/uploads/n.md"]
    assert server.account_registry.get_account_by_peer(me)["token_balance"] == 1000 - 84


def test_generic_space_api_scope_cannot_traverse(tmp_path):
    from iot_federated_agent_memory.agent_space import SingleFileSpaceVFS
    sp = SingleFileSpaceVFS(scope="../../arena_context/x", owner_id="agent", base_dir=str(tmp_path))
    assert os.path.dirname(sp.space_path).startswith(str(tmp_path / "spaces"))
    assert ".." not in sp.space_path
