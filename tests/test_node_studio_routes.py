"""Tests for Aeonik Node Studio routes, Mesh OS #win-nodes window, and Design Gallery entries."""

import json
import os
import sys
import threading
import types
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR in sys.path:
    sys.path.remove(WORKTREE_DIR)
sys.path.insert(0, WORKTREE_DIR)

for _mod in list(sys.modules.keys()):
    if _mod.startswith("iot_federated_agent_memory") or _mod == "server":
        del sys.modules[_mod]

import server
from iot_federated_agent_memory.designs_gallery import (
    AEONIK_MOCKUPS,
    render_designs_gallery_html,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI


EXPECTED_NODE_DESIGN_ASSETS = (
    "tincan_gemini_node_terminal_04.png",
    "tincan_gemini_node_terminal_04_text.png",
    "tincan_gemini_node_terminal_04_video.png",
    "tincan_gemini_node_terminal_04_modalities_sheet.png",
    "tincan_gemini_node_studio_01.png",
    "tincan_gemini_node_spec_02.png",
    "tincan_gemini_node_modes_03.png",
    "tincan_gemini_node_sheet.png",
    "tincan_gemini_node_editor.figcraft",
)

EXPECTED_GALLERY_ENTRIES = (
    (
        "/assets/designs/tincan_gemini_node_terminal_04.png",
        "Aeonik Node Studio · Image DAG & LUT Filter Rack",
        "/nodes?modality=image",
    ),
    (
        "/assets/designs/tincan_gemini_node_terminal_04_text.png",
        "Aeonik Node Studio · Text Prose Filter & Beat Timeline",
        "/nodes?modality=text",
    ),
    (
        "/assets/designs/tincan_gemini_node_terminal_04_video.png",
        "Aeonik Node Studio · Video Cut Timeline & 60fps/LUFS Rack",
        "/nodes?modality=video",
    ),
    (
        "/assets/designs/tincan_gemini_node_terminal_04_modalities_sheet.png",
        "Aeonik Node Studio · 3-Modality Master Sheet (Image · Text · Video)",
        "/nodes",
    ),
    (
        "/assets/designs/tincan_gemini_node_studio_01.png",
        "Node Studio Window · Prompt Island & DAG Canvas",
        "/nodes",
    ),
    (
        "/assets/designs/tincan_gemini_node_spec_02.png",
        "Node Timeline & Non-Destructive Filter Rack",
        "/nodes?view=timeline",
    ),
    (
        "/assets/designs/tincan_gemini_node_modes_03.png",
        "Prompt Island Modes (Generate / Edit / Merge) & NanoGPT Hookup",
        "/nodes?view=gateway",
    ),
)


@pytest.fixture
def live_node_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def _http_req(url: str, method: str = "GET", payload=None, headers=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req_headers = {"Accept": "application/json"}
    if data is not None:
        req_headers["Content-Type"] = "application/json"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        return err.code, raw, dict(err.headers)


def test_designs_gallery_includes_all_node_studio_mockups():
    by_img = {m["img"]: m for m in AEONIK_MOCKUPS}
    html = render_designs_gallery_html("aeonik")
    for img_path, title, link in EXPECTED_GALLERY_ENTRIES:
        assert img_path in by_img, f"Missing {img_path} in AEONIK_MOCKUPS"
        assert by_img[img_path]["title"] == title
        assert by_img[img_path]["link"] == link
        assert img_path in html
        assert title in html
        assert f'href="{link}"' in html
    assert f"01 · Aeonik Celadon &amp; Ink ({len(AEONIK_MOCKUPS)})" in html


def test_node_studio_design_assets_exist_and_serve(live_node_server):
    assets_dir = os.path.join(WORKTREE_DIR, "assets", "designs")
    for fname in EXPECTED_NODE_DESIGN_ASSETS:
        fpath = os.path.join(assets_dir, fname)
        assert os.path.isfile(fpath), f"Missing asset file: {fpath}"
        assert os.path.getsize(fpath) > 0, f"Empty asset file: {fpath}"

    for img_path, _, _ in EXPECTED_GALLERY_ENTRIES:
        with urllib.request.urlopen(f"{live_node_server}{img_path}") as resp:
            assert resp.status == 200
            assert resp.headers["Content-Type"] == "image/png"
            assert len(resp.read()) > 1000


def test_mesh_os_ui_registers_win_nodes_window():
    assert 'id="win-nodes"' in MESH_OS_HTML_UI
    assert 'data-tc-titlebar="win-nodes"' in MESH_OS_HTML_UI
    assert 'id="dockBtn-win-nodes"' in MESH_OS_HTML_UI
    assert "'win-nodes'" in MESH_OS_HTML_UI
    assert "window.location.pathname === '/nodes'" in MESH_OS_HTML_UI


def test_nodes_html_routes_fallback_and_delegated(live_node_server, monkeypatch):
    # 1. Work cleanly even when node_studio_ui is absent (fallback)
    monkeypatch.setattr(server, "_node_studio_ui", None)
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "iot_federated_agent_memory.node_studio_ui", None)
        for path, expected_mod in (
            ("/nodes", "Image"),
            ("/nodes?modality=text", "Text"),
            ("/nodes?modality=video", "Video"),
            ("/nodes/timeline?modality=video", "Video"),
            ("/nodes/gateway?modality=text", "Text"),
        ):
            status, body, hdrs = _http_req(f"{live_node_server}{path}")
            assert status == 200
            assert "text/html" in hdrs.get("Content-Type", "")
            assert f"Node Studio · {expected_mod}" in body
            assert "#ecf1e6" in body

    # 2. Delegate cleanly to node_studio_ui.render_node_studio_html when present
    calls = []
    fake_ui = types.ModuleType("iot_federated_agent_memory.node_studio_ui")

    def _fake_render(active_modality="image"):
        calls.append(active_modality)
        return f"<html><body>FAKE NODE STUDIO [{active_modality}]</body></html>"

    fake_ui.render_node_studio_html = _fake_render
    monkeypatch.setattr(server, "_node_studio_ui", fake_ui)

    status, body, _ = _http_req(f"{live_node_server}/nodes?modality=video")
    assert status == 200
    assert "FAKE NODE STUDIO [video]" in body

    status, body, _ = _http_req(f"{live_node_server}/nodes/timeline?modality=text")
    assert status == 200
    assert "FAKE NODE STUDIO [text]" in body

    status, body, _ = _http_req(f"{live_node_server}/nodes/gateway")
    assert status == 200
    assert "FAKE NODE STUDIO [image]" in body
    assert calls == ["video", "text", "image"]


def test_nodes_api_routes_fallback_and_delegated(live_node_server, monkeypatch):
    # 1. Fallback mode (before node_studio_engine is merged)
    monkeypatch.setattr(server, "_node_studio_engine", None)
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "iot_federated_agent_memory.node_studio_engine", None)
        status, raw, _ = _http_req(f"{live_node_server}/api/nodes/health")
        assert status == 200
        health = json.loads(raw)
        assert health["ok"] is True
        assert health["modalities"] == ["text", "image", "video"]

        for mod in ("image", "text", "video"):
            status, raw, _ = _http_req(f"{live_node_server}/api/nodes/state?modality={mod}")
            assert status == 200
            st = json.loads(raw)
            assert st["ok"] is True
            assert st["modality"] == mod

        status, raw, _ = _http_req(
            f"{live_node_server}/api/nodes/generate",
            method="POST",
            payload={"prompt": ""},
        )
        assert status == 400
        assert json.loads(raw)["ok"] is False

        status, raw, _ = _http_req(
            f"{live_node_server}/api/nodes/generate",
            method="POST",
            payload={"prompt": "Kodak 2383 portrait", "modality": "image", "selected_node_ids": ["01", "02"]},
        )
        assert status == 200
        gen = json.loads(raw)
        assert gen["ok"] is True
        assert gen["mode"] == "MERGE"

        status, raw, _ = _http_req(
            f"{live_node_server}/api/nodes/filter",
            method="POST",
            payload={"node_id": "03", "modality": "image", "filters": {"kodak_2383": 85}},
        )
        assert status == 200
        flt = json.loads(raw)
        assert flt["ok"] is True
        assert flt["node_id"] == "03"
        assert flt["filters"]["kodak_2383"] == 85

    # 2. Delegated mode (with node_studio_engine present)
    recorded = {}
    fake_engine = types.ModuleType("iot_federated_agent_memory.node_studio_engine")

    def _fake_health(headers=None, env=None):
        recorded["health_headers"] = dict(headers or {})
        return {
            "ok": True,
            "hasServerKey": True,
            "hasGeminiKey": False,
            "hasNanogptKey": True,
            "modalities": ["text", "image", "video"],
            "models": {"image": ["nano-banana-2.1"]},
        }

    def _fake_state(modality="image"):
        recorded["state_modality"] = modality
        return {
            "modality": modality,
            "nodes": [{"id": "01", "filters": {}}],
            "edges": [],
            "timeline": [{"timecode": "00:00", "node_id": "01"}],
        }

    def _fake_generate(payload, headers=None, env=None):
        recorded["generate_payload"] = payload
        recorded["generate_headers"] = dict(headers or {})
        return {"ok": True, "mode": "EDIT", "node": {"id": "01.a1"}, "edges": [], "timeline": []}

    def _fake_apply_filters(node, filters):
        recorded["filter_call"] = (node, filters)
        return {**node, "filters": filters}

    def _fake_timeline(nodes, edges, target_node_id=None):
        recorded["timeline_target"] = target_node_id
        return [{"timecode": "00:00", "node_id": target_node_id or "01"}]

    fake_engine.get_node_studio_health = _fake_health
    fake_engine.get_default_studio_state = _fake_state
    fake_engine.handle_node_studio_generate = _fake_generate
    fake_engine.apply_node_filters = _fake_apply_filters
    fake_engine.build_timeline_sequence = _fake_timeline
    monkeypatch.setattr(server, "_node_studio_engine", fake_engine)

    status, raw, _ = _http_req(
        f"{live_node_server}/api/nodes/health",
        headers={"X-NanoGPT-Api-Key": "ng-test-key"},
    )
    assert status == 200
    assert json.loads(raw)["hasNanogptKey"] is True
    norm_hdrs = {k.lower(): v for k, v in recorded["health_headers"].items()}
    assert norm_hdrs.get("x-nanogpt-api-key") == "ng-test-key"

    status, raw, _ = _http_req(f"{live_node_server}/api/nodes/state?modality=video")
    assert status == 200
    assert json.loads(raw)["modality"] == "video"
    assert recorded["state_modality"] == "video"

    status, raw, _ = _http_req(
        f"{live_node_server}/api/nodes/generate",
        method="POST",
        payload={"prompt": "Add halation", "selected_node_ids": ["01"]},
    )
    assert status == 200
    assert json.loads(raw)["mode"] == "EDIT"
    assert recorded["generate_payload"]["prompt"] == "Add halation"

    status, raw, _ = _http_req(
        f"{live_node_server}/api/nodes/filter",
        method="POST",
        payload={"node_id": "01", "modality": "image", "filters": {"halation": 35}},
    )
    assert status == 200
    body = json.loads(raw)
    assert body["ok"] is True
    assert body["updated"]["filters"] == {"halation": 35}
    assert recorded["timeline_target"] == "01"


def test_fastapi_routes_registered_for_node_studio():
    if hasattr(server.app, "routes") and isinstance(server.app.routes, dict):
        for route in ("/nodes", "/nodes/timeline", "/nodes/gateway", "/api/nodes/health", "/api/nodes/state"):
            assert route in server.app.routes
        for route in ("/api/nodes/generate", "/api/nodes/filter"):
            assert route in server.app.post_routes
    else:
        paths = {getattr(r, "path", None) for r in getattr(server.app, "routes", [])}
        for route in (
            "/nodes",
            "/nodes/timeline",
            "/nodes/gateway",
            "/api/nodes/health",
            "/api/nodes/state",
            "/api/nodes/generate",
            "/api/nodes/filter",
        ):
            assert route in paths
