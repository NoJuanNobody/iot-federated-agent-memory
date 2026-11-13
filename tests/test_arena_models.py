"""Brain Arena model selection: list comes from the router, is validated, and is stored with votes."""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter
from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine


def test_arena_models_from_router_without_3d():
    router = DynamicAIGatewayRouter(openrouter_key="", hyper3d_key="")
    models = router.get_arena_models()
    ids = [m["id"] for m in models]
    # Configured brains first
    assert ids[:4] == list(router.providers.keys())[:4]
    # No duplicates: gemini-brain already is google/gemini-2.5-flash, so the raw id is not listed again.
    assert "google/gemini-2.5-flash" not in ids and "openai/gpt-4o" not in ids
    assert len({m["model"] for m in models}) == len(models)
    assert "google/gemini-2.5-pro" in ids
    gem = next(m for m in models if m["id"] == "gemini-brain")
    assert gem["name"] == "Google Gemini Flash" and gem["secondary"] == "google/gemini-2.5-flash"
    assert not any(i.startswith(("ronin/", "rodin/", "hyper3d/")) for i in ids)
    assert router.arena_default_pair() == {"a": "gemini-brain", "b": "claude-brain"}


def test_arena_model_validation():
    router = DynamicAIGatewayRouter(openrouter_key="", hyper3d_key="")
    assert router.is_arena_model_allowed("claude-brain")
    assert router.is_arena_model_allowed("google/gemini-2.5-flash")
    assert not router.is_arena_model_allowed("ronin/regular")
    assert not router.is_arena_model_allowed("made-up/model")
    assert not router.is_arena_model_allowed("")
    assert not router.is_arena_model_allowed(None)


def test_vote_records_models():
    engine = TinCanMeshOSEngine()
    res = engine.vote_arena("peer-x", "claude-brain", "hello", model_a="gemini-brain", model_b="claude-brain", winner_side="B")
    assert res["model_a"] == "gemini-brain" and res["model_b"] == "claude-brain" and res["winner_side"] == "B"
    rec = engine.arena_matches[-1]
    assert rec["winner_alias"] == "claude-brain" and rec["model_a"] == "gemini-brain"
    assert engine.get_state()["arena_recent_matches"][-1]["model_b"] == "claude-brain"


@pytest.fixture(scope="module")
def live(monkeypatch_module=None):
    import server
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def test_arena_models_endpoint(live):
    with urllib.request.urlopen(f"{live}/api/mesh/arena/models", timeout=15) as r:
        data = json.loads(r.read())
    assert data["count"] == len(data["models"]) > 0
    assert data["default"]["a"] != data["default"]["b"]


def test_chat_rejects_disallowed_arena_model(live):
    with pytest.raises(urllib.error.HTTPError) as ei:
        _post(f"{live}/api/chat", {"model": "ronin/regular", "prompt": "hi", "arena": True})
    assert ei.value.code == 400


def test_vote_endpoint_validates_and_stores(live):
    import server
    out = _post(f"{live}/api/mesh/arena/vote", {
        "peer_id": "peer-arena-test", "winner_side": "A", "model_a": "gemini-brain", "model_b": "claude-brain",
        "winner_alias": "ignored", "prompt_preview": "p",
    })
    assert out["winner_alias"] == "gemini-brain" and out["model_b"] == "claude-brain"
    assert server.mesh_os.arena_matches[-1]["model_a"] == "gemini-brain"
    with pytest.raises(urllib.error.HTTPError) as ei:
        _post(f"{live}/api/mesh/arena/vote", {"peer_id": "p", "winner_side": "A", "model_a": "evil/model", "model_b": "claude-brain"})
    assert ei.value.code == 400
    # Legacy body (no models) still works.
    legacy = _post(f"{live}/api/mesh/arena/vote", {"peer_id": "p", "winner_alias": "claude-brain"})
    assert legacy["status"] == "voted"


def test_ui_arena_pickers():
    from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI as H
    assert '<select id="arenaModelAInput"' in H and '<select id="arenaModelBInput"' in H
    assert 'id="arenaSwapBtn"' in H and "tincan_arena_models" in H and "/api/mesh/arena/models" in H
    # The duel itself is no longer hard-coded (the Aeonik terminal's `ask` command may still use a default).
    start = H.index("async function runArenaBattle()")
    duel = H[start:H.index("\n    }\n", start)]
    assert "model: 'gemini-brain'" not in duel and "model: 'claude-brain'" not in duel
