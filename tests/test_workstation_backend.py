"""Integration and unit tests for Workstation backend routes in server.py."""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import pytest

# Ensure this worktree has highest priority in sys.path
WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR in sys.path:
    sys.path.remove(WORKTREE_DIR)
sys.path.insert(0, WORKTREE_DIR)

PARENT_DIR = os.path.dirname(os.path.dirname(WORKTREE_DIR))
while PARENT_DIR in sys.path:
    sys.path.remove(PARENT_DIR)

for mod in list(sys.modules.keys()):
    if mod.startswith("iot_federated_agent_memory") or mod == "server":
        del sys.modules[mod]

import server
from iot_federated_agent_memory.agent_space import AgentSpaceManager
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter


class _FakeNotesRouter:
    """Fake AI router returning queued completion JSON replies and recording calls."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.nanogpt_key = None

    def dispatch_completion(self, alias, messages, temperature=0.7, max_tokens=1024):
        self.calls.append({"alias": alias, "messages": messages, "temperature": temperature})
        content = self.replies.pop(0) if self.replies else ""
        return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture
def live_ws_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def _http_req(url: str, method: str = "GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        return err.code, raw, dict(err.headers)


def test_workstation_single_window_route(live_ws_server):
    assert "/workstation" in server.SINGLE_WINDOW_ROUTES
    status, body, headers = _http_req(f"{live_ws_server}/workstation", method="GET")
    assert status == 200
    assert "text/html" in headers.get("Content-Type", "")
    assert "TinCan Mesh OS" in body


def test_workstation_status_endpoint(live_ws_server, tmp_path, monkeypatch):
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    monkeypatch.delenv("HYPER3D_API_KEY", raising=False)
    monkeypatch.delenv("RODIN_API_KEY", raising=False)
    for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID"):
        monkeypatch.delenv(k, raising=False)

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("TINCAN_DRIVE_ROOT", str(fake_home))
    monkeypatch.delenv("TINCAN_DRIVE_MIRROR", raising=False)

    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    sp = sm.get_or_create_space("user", "ws-tester")
    sp.write_file("/hello.txt", "world", updated_by="test")
    monkeypatch.setattr(server, "_space_manager", sm)

    offline_router = DynamicAIGatewayRouter(openrouter_key="", hyper3d_key=None, nanogpt_key="")
    monkeypatch.setattr(server, "router", offline_router)

    seen_flags = []
    orig_get_ng = offline_router.get_nanogpt_models

    def spy_get_ng(force_refresh=False, include_live_public=False):
        seen_flags.append((force_refresh, include_live_public))
        return orig_get_ng(force_refresh=force_refresh, include_live_public=include_live_public)

    monkeypatch.setattr(offline_router, "get_nanogpt_models", spy_get_ng)

    status, raw, _ = _http_req(f"{live_ws_server}/api/workstation/status?scope=user&owner_id=ws-tester")
    assert status == 200
    data = json.loads(raw)

    assert set(data.keys()) >= {"rodin", "rodin_tiers", "nanogpt", "space", "drive_mirror"}
    assert data["rodin_tiers"] == {"Sketch": 0.25, "Regular": 0.50, "Smooth": 0.75, "Detail": 1.00}
    assert data["rodin"]["tier_pricing_usd"] == data["rodin_tiers"]

    assert data["nanogpt"]["configured"] is False
    assert data["nanogpt"]["total_count"] >= 10
    assert data["nanogpt"]["tee_count"] >= 2
    assert data["nanogpt"]["heretic_count"] >= 5
    assert seen_flags == [(False, False)]

    assert data["space"]["scope"] == "user"
    assert data["space"]["owner_id"] == "ws-tester"
    assert data["space"]["file_count"] == len(sp.list_files())
    assert data["space"]["merkle_root"] == sp.compute_merkle_root()

    assert data["drive_mirror"]["connected"] is True
    assert data["drive_mirror"]["available"] is True
    assert data["drive_mirror"]["root_name"] == "home"

    # On Railway, drive mirror is disabled and root_name is withheld.
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    status_rw, raw_rw, _ = _http_req(f"{live_ws_server}/api/workstation/status")
    assert status_rw == 200
    rw_data = json.loads(raw_rw)
    assert rw_data["drive_mirror"]["connected"] is False
    assert rw_data["drive_mirror"]["root_name"] is None


def test_rodin_spend_cap_guardrail(live_ws_server, tmp_path, monkeypatch):
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    monkeypatch.setattr(server, "_space_manager", sm)

    dispatch_calls = []

    def spy_dispatch(ai_router, prompt, images=None, tier="Regular", geometry_file_format="glb", material="PBR", quality="medium", mesh_mode="Quad"):
        dispatch_calls.append({"prompt": prompt, "tier": tier})
        return {
            "uuid": "rodin-task-test",
            "subscription_key": "sub-test",
            "prompt": prompt,
            "tier": tier,
            "format": geometry_file_format,
            "status": "Done",
            "cost_usd": server._estimate_rodin_tier_cost(tier),
            "glb_bytes_b64": "Z2xURg==",
        }

    with patch.object(server, "_dispatch_rodin", side_effect=spy_dispatch):
        # Detail ($1.00) must be blocked when max_cost_usd=0.50 WITHOUT calling _dispatch_rodin
        code, raw, _ = _http_req(
            f"{live_ws_server}/api/3d/generate",
            method="POST",
            payload={"prompt": "detailed mech", "tier": "Detail", "max_cost_usd": 0.50, "owner_id": "budget-user"},
        )
        assert code == 400
        err = json.loads(raw)
        assert err["budget_exceeded"] is True
        assert err["estimated_cost_usd"] == pytest.approx(1.00)
        assert err["max_cost_usd"] == pytest.approx(0.50)
        assert "error" in err
        assert dispatch_calls == []

        # Smooth ($0.75) also blocked on /api/rodin/generate when max_cost_usd=0.50
        code_smooth, raw_smooth, _ = _http_req(
            f"{live_ws_server}/api/rodin/generate",
            method="POST",
            payload={"prompt": "smooth vase", "tier": "Smooth", "max_cost_usd": 0.50},
        )
        assert code_smooth == 400
        assert json.loads(raw_smooth)["budget_exceeded"] is True
        assert dispatch_calls == []

        # Invalid max_cost_usd rejected cleanly
        code_bad, _, _ = _http_req(
            f"{live_ws_server}/api/3d/generate",
            method="POST",
            payload={"prompt": "x", "tier": "Sketch", "max_cost_usd": "not-a-number"},
        )
        assert code_bad == 400
        assert dispatch_calls == []

        # Sketch ($0.25) is allowed under max_cost_usd=0.50
        code_ok, raw_ok, _ = _http_req(
            f"{live_ws_server}/api/3d/generate",
            method="POST",
            payload={"prompt": "sketch cube", "tier": "Sketch", "max_cost_usd": 0.50, "owner_id": "budget-user"},
        )
        assert code_ok == 200
        ok_data = json.loads(raw_ok)
        assert ok_data["tier"] == "Sketch"
        assert len(dispatch_calls) == 1

        # Exact cap boundary Regular ($0.50) with max_cost_usd=0.50 is allowed
        code_eq, _, _ = _http_req(
            f"{live_ws_server}/api/3d/generate",
            method="POST",
            payload={"prompt": "regular cube", "tier": "Regular", "max_cost_usd": 0.50, "owner_id": "budget-user"},
        )
        assert code_eq == 200
        assert len(dispatch_calls) == 2


def test_space_notes_http_roundtrip_propose_commit_revert(live_ws_server, tmp_path, monkeypatch):
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    sp = sm.get_or_create_space("user", "notes-tester")
    sp.write_file("/doc/story.md", "# Title\n\nThe cat sat.\n", updated_by="seed")
    sp.write_file("/doc/legacy.txt", "obsolete line\n", updated_by="seed")
    initial_merkle = sp.compute_merkle_root()

    plan_json = json.dumps({
        "summary": "Swap cat for dog, add ending, remove legacy",
        "edits": [
            {"path": "/doc/story.md", "op": "patch", "target": "The cat sat.", "replacement": "The dog sat."},
            {"path": "/doc/ending.md", "op": "write", "content": "The end.\n"},
            {"path": "/doc/legacy.txt", "op": "delete"},
        ],
        "skipped": [],
        "conflicts": [],
    })
    conflict_plan_json = json.dumps({
        "summary": "Will conflict",
        "edits": [{"path": "/doc/story.md", "op": "write", "content": "overwrite\n"}],
        "skipped": [],
        "conflicts": [],
    })
    fake_router = _FakeNotesRouter(f"```json\n{plan_json}\n```", conflict_plan_json)

    monkeypatch.setattr(server, "_space_manager", sm)
    monkeypatch.setattr(server, "router", fake_router)

    # 1. Empty pending notes -> propose returns 400 EditPlanError
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/propose",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester"},
    )
    assert code == 400
    assert "No pending notes" in json.loads(raw)["error"]

    # 2. Add notes via POST /api/space/notes
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={
            "action": "add",
            "scope": "user",
            "owner_id": "notes-tester",
            "body": "Cat should be a dog",
            "kind": "edit",
            "path": "/doc/story.md",
            "author": "alice",
        },
    )
    assert code == 200
    n1 = json.loads(raw)["note"]
    assert n1["kind"] == "edit"

    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={"action": "add", "scope": "user", "owner_id": "notes-tester", "body": "Discard me"},
    )
    assert code == 200
    n_drop = json.loads(raw)["note"]

    # Invalid kind -> 400
    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={"action": "add", "scope": "user", "owner_id": "notes-tester", "body": "bad", "kind": "nonsense"},
    )
    assert code == 400

    # Drop note -> 200; dropping again -> 404
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={"action": "drop", "scope": "user", "owner_id": "notes-tester", "note_id": n_drop["note_id"]},
    )
    assert code == 200
    assert json.loads(raw)["dropped"] is True

    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={"action": "drop", "scope": "user", "owner_id": "notes-tester", "note_id": n_drop["note_id"]},
    )
    assert code == 404

    # Banned peer enforcement on POST /api/space/notes
    monkeypatch.setitem(server.banned_peers, "bad-actor", {"reason": "abuse"})
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes",
        method="POST",
        payload={"action": "add", "scope": "user", "owner_id": "bad-actor", "body": "spam"},
    )
    assert code == 403
    assert json.loads(raw)["banned"] is True

    # 3. GET /api/space/notes (pending vs all)
    code, raw, _ = _http_req(f"{live_ws_server}/api/space/notes?scope=user&owner_id=notes-tester")
    assert code == 200
    listed = json.loads(raw)
    assert [n["note_id"] for n in listed["notes"]] == [n1["note_id"]]
    assert listed["merkle_root"] == initial_merkle
    assert listed["versions"] == []

    code, raw_all, _ = _http_req(f"{live_ws_server}/api/space/notes?scope=user&owner_id=notes-tester&status=all")
    assert code == 200
    assert len(json.loads(raw_all)["notes"]) == 2

    # 4. Propose with inline note_body + path & verify unified diff_preview without mutating VFS
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/propose",
        method="POST",
        payload={
            "scope": "user",
            "owner_id": "notes-tester",
            "note_body": "Add ending and remove legacy",
            "path": "/doc/ending.md",
        },
    )
    assert code == 200
    plan = json.loads(raw)
    assert fake_router.calls[0]["alias"] == "nanogpt/TEE/deepseek-v4.1-flash"
    assert sp.compute_merkle_root() == initial_merkle  # propose must not mutate VFS

    previews = {p["path"]: p for p in plan["diff_preview"]}
    assert set(previews.keys()) == {"/doc/story.md", "/doc/ending.md", "/doc/legacy.txt"}
    assert "-The cat sat." in previews["/doc/story.md"]["diff"]
    assert "+The dog sat." in previews["/doc/story.md"]["diff"]
    assert "--- /dev/null" in previews["/doc/ending.md"]["diff"]
    assert "+The end." in previews["/doc/ending.md"]["diff"]
    assert "+++ /dev/null" in previews["/doc/legacy.txt"]["diff"]
    assert "-obsolete line" in previews["/doc/legacy.txt"]["diff"]

    # 5. Commit the proposed plan
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/commit",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "plan_id": plan["plan_id"], "author": "alice"},
    )
    assert code == 200
    ver = json.loads(raw)
    assert sp.read_file("/doc/story.md")["content"] == "# Title\n\nThe dog sat.\n"
    assert sp.read_file("/doc/ending.md")["content"] == "The end.\n"
    with pytest.raises(FileNotFoundError):
        sp.read_file("/doc/legacy.txt")
    assert sp.compute_merkle_root() == ver["merkle_root"]

    # Re-committing same plan_id returns 409; missing plan_id returns 400; unknown plan_id returns 404
    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes/commit",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "plan_id": plan["plan_id"]},
    )
    assert code == 409

    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes/commit",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester"},
    )
    assert code == 400

    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes/commit",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "plan_id": "plan_missing"},
    )
    assert code == 404

    # 6. Revert the committed version -> restores VFS & reopens notes
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/revert",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "version_id": ver["version_id"], "author": "alice"},
    )
    assert code == 200
    rev = json.loads(raw)
    assert rev["reverted"] is True
    assert rev["merkle_root"] == initial_merkle
    assert sp.read_file("/doc/story.md")["content"] == "# Title\n\nThe cat sat.\n"
    assert sp.read_file("/doc/legacy.txt")["content"] == "obsolete line\n"
    with pytest.raises(FileNotFoundError):
        sp.read_file("/doc/ending.md")

    # Re-reverting same version returns 409
    code, _, _ = _http_req(
        f"{live_ws_server}/api/space/notes/revert",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "version_id": ver["version_id"]},
    )
    assert code == 409

    # 7. Stale-space conflict on commit -> 409
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/propose",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "model": "nanogpt/TEE/deepseek-v4.1-flash"},
    )
    assert code == 200
    plan2 = json.loads(raw)
    sp.write_file("/doc/story.md", "concurrent change", updated_by="peer")
    code, raw, _ = _http_req(
        f"{live_ws_server}/api/space/notes/commit",
        method="POST",
        payload={"scope": "user", "owner_id": "notes-tester", "plan_id": plan2["plan_id"]},
    )
    assert code == 409
    assert "changed since" in json.loads(raw)["error"]
