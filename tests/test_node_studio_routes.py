"""Tests for Nano Banana Gemini Node Studio routes, Home Screen mounting, #win-nodes, and Design Gallery."""

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
from iot_federated_agent_memory.ai_home_shell import render_ai_home_hub_html
from iot_federated_agent_memory.designs_gallery import (
    AEONIK_MOCKUPS,
    render_designs_gallery_html,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI


EXPECTED_NODE_DESIGN_ASSETS = (
    "tincan_gemini_node_studio_01.png",
    "tincan_gemini_node_spec_02.png",
    "tincan_gemini_node_sheet.png",
    "tincan_gemini_node_editor.figcraft",
)

SCRAPPED_NODE_DESIGN_ASSETS = (
    "tincan_gemini_node_terminal_04.png",
    "tincan_gemini_node_terminal_04_text.png",
    "tincan_gemini_node_terminal_04_video.png",
    "tincan_gemini_node_terminal_04_modalities_sheet.png",
    "tincan_gemini_node_modes_03.png",
)

EXPECTED_GALLERY_ENTRIES = (
    (
        "/assets/designs/tincan_gemini_node_studio_01.png",
        "Nano Banana Gemini Node Studio · Infinite Canvas, Prompt Island & Lumina Library",
        "/nodes",
    ),
    (
        "/assets/designs/tincan_gemini_node_spec_02.png",
        "Nano Banana Gemini Node Studio · Modes, Model Selector & API Spec",
        "/gemini-node-studio",
    ),
    (
        "/assets/designs/tincan_gemini_node_sheet.png",
        "Nano Banana Gemini Node Studio · Composite Contact Sheet",
        "/nodes",
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


def test_designs_gallery_keeps_only_nano_banana_node_studio_mockups():
    by_img = {m["img"]: m for m in AEONIK_MOCKUPS}
    html = render_designs_gallery_html("aeonik")
    for img_path, title, link in EXPECTED_GALLERY_ENTRIES:
        assert img_path in by_img, f"Missing {img_path} in AEONIK_MOCKUPS"
        assert by_img[img_path]["title"] == title
        assert by_img[img_path]["link"] == link
        assert img_path in html
        assert title in html
        assert f'href="{link}"' in html

    for removed_fname in SCRAPPED_NODE_DESIGN_ASSETS:
        assert removed_fname not in by_img
        assert removed_fname not in html

    assert f"01 · Aeonik Celadon &amp; Ink ({len(AEONIK_MOCKUPS)})" in html


def test_node_studio_design_assets_exist_and_scrapped_removed(live_node_server):
    assets_dir = os.path.join(WORKTREE_DIR, "assets", "designs")
    for fname in EXPECTED_NODE_DESIGN_ASSETS:
        fpath = os.path.join(assets_dir, fname)
        assert os.path.isfile(fpath), f"Missing asset file: {fpath}"
        assert os.path.getsize(fpath) > 0, f"Empty asset file: {fpath}"

    for removed_fname in SCRAPPED_NODE_DESIGN_ASSETS:
        fpath = os.path.join(assets_dir, removed_fname)
        assert not os.path.exists(fpath), f"Scrapped asset still present: {fpath}"

    for img_path, _, _ in EXPECTED_GALLERY_ENTRIES:
        with urllib.request.urlopen(f"{live_node_server}{img_path}") as resp:
            assert resp.status == 200
            assert resp.headers["Content-Type"] == "image/png"
            assert len(resp.read()) > 1000


def test_home_screen_and_mesh_os_mount_node_studio():
    assert 'id="win-nodes"' in MESH_OS_HTML_UI
    assert 'data-tc-titlebar="win-nodes"' in MESH_OS_HTML_UI
    assert 'id="dockBtn-win-nodes"' in MESH_OS_HTML_UI
    assert "'win-nodes'" in MESH_OS_HTML_UI
    assert "window.location.pathname === '/nodes'" in MESH_OS_HTML_UI
    assert "window.location.pathname === '/gemini-node-studio'" in MESH_OS_HTML_UI

    # Zen Home quickbar, TOOLS, SLASH, and HELP_TEXT
    assert '<button class="zen-btn zq-extra" type="button" data-tool="win-nodes">Node Studio</button>' in MESH_OS_HTML_UI
    assert "id: 'win-nodes'" in MESH_OS_HTML_UI
    assert "cmd: '/nodes', tool: 'win-nodes'" in MESH_OS_HTML_UI
    assert "cmd: '/gemini-node-studio', tool: 'win-nodes'" in MESH_OS_HTML_UI

    # AI Home Shell prominent launch & embed
    home_frag = render_ai_home_hub_html()
    assert 'id="aiHomeNodeStudioMount"' in home_frag
    assert 'id="aiHomeLaunchNodeStudioBtn"' in home_frag
    assert 'data-window="win-nodes"' in home_frag
    assert 'data-route="/nodes"' in home_frag
    assert 'href="/nodes"' in home_frag
    assert 'id="aiHomeNodeStudioMount"' in MESH_OS_HTML_UI
    assert 'id="aiHomeLaunchNodeStudioBtn"' in MESH_OS_HTML_UI


def test_nodes_html_routes_fallback_and_delegated(live_node_server, monkeypatch):
    # 1. Fallback mode when node_studio_ui is absent
    monkeypatch.setattr(server, "_node_studio_ui", None)
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "iot_federated_agent_memory.node_studio_ui", None)
        for path in (
            "/nodes",
            "/gemini-node-studio",
            "/nodes/timeline?modality=video",
            "/nodes/gateway?modality=text",
        ):
            status, body, hdrs = _http_req(f"{live_node_server}{path}")
            assert status == 200
            assert "text/html" in hdrs.get("Content-Type", "")
            assert "Node Studio" in body
            assert "#ecf1e6" in body

    # 2. Delegate cleanly to zero-arg render_node_studio_html() as well as parameterized signatures
    zero_arg_calls = []
    fake_zero_ui = types.ModuleType("iot_federated_agent_memory.node_studio_ui")

    def _fake_zero_arg_render():
        zero_arg_calls.append("called")
        return "<html><body>NANO BANANA NODE STUDIO ZERO-ARG</body></html>"

    fake_zero_ui.render_node_studio_html = _fake_zero_arg_render
    monkeypatch.setattr(server, "_node_studio_ui", fake_zero_ui)

    for path in ("/nodes", "/gemini-node-studio"):
        status, body, _ = _http_req(f"{live_node_server}{path}")
        assert status == 200
        assert "NANO BANANA NODE STUDIO ZERO-ARG" in body
    assert len(zero_arg_calls) == 2

    # 3. Delegate cleanly to active_modality signature
    mod_calls = []
    fake_mod_ui = types.ModuleType("iot_federated_agent_memory.node_studio_ui")

    def _fake_mod_render(active_modality="image"):
        mod_calls.append(active_modality)
        return f"<html><body>FAKE NODE STUDIO [{active_modality}]</body></html>"

    fake_mod_ui.render_node_studio_html = _fake_mod_render
    monkeypatch.setattr(server, "_node_studio_ui", fake_mod_ui)

    status, body, _ = _http_req(f"{live_node_server}/nodes?modality=video")
    assert status == 200
    assert "FAKE NODE STUDIO [video]" in body
    assert mod_calls == ["video"]


def test_nodes_and_prompt_island_api_routes(live_node_server, monkeypatch):
    # 1. Fallback mode (before node_studio_engine is merged)
    monkeypatch.setattr(server, "_node_studio_engine", None)
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "iot_federated_agent_memory.node_studio_engine", None)
        for health_path in ("/api/nodes/health", "/api/health"):
            status, raw, _ = _http_req(f"{live_node_server}{health_path}")
            assert status == 200
            health = json.loads(raw)
            assert health["ok"] is True
            assert health["modalities"] == ["text", "image", "video"]

        for gen_path in ("/api/nodes/generate", "/api/generate"):
            status, raw, _ = _http_req(f"{live_node_server}{gen_path}", method="POST", payload={"prompt": ""})
            assert status == 400
            assert json.loads(raw)["ok"] is False

            status, raw, _ = _http_req(
                f"{live_node_server}{gen_path}",
                method="POST",
                payload={"prompt": "Celadon studio cube", "selected_node_ids": ["01", "02"]},
            )
            assert status == 200
            gen = json.loads(raw)
            assert gen["ok"] is True
            assert gen["mode"] == "MERGE"

        status, raw, _ = _http_req(f"{live_node_server}/api/nodes/state?modality=image")
        assert status == 200
        assert json.loads(raw)["modality"] == "image"

        status, raw, _ = _http_req(
            f"{live_node_server}/api/nodes/filter",
            method="POST",
            payload={"node_id": "03", "modality": "image", "filters": {"kodak_2383": 85}},
        )
        assert status == 200
        assert json.loads(raw)["ok"] is True

    # 2. Delegated mode (with node_studio_engine present)
    recorded = {}
    fake_engine = types.ModuleType("iot_federated_agent_memory.node_studio_engine")

    def _fake_health(headers=None, env=None):
        recorded["health_headers"] = dict(headers or {})
        return {
            "ok": True,
            "hasServerKey": True,
            "hasGeminiKey": True,
            "hasNanogptKey": True,
            "modalities": ["text", "image", "video"],
            "models": {"image": ["nano-banana-2.1"]},
        }

    def _fake_state(modality="image"):
        recorded["state_modality"] = modality
        return {"modality": modality, "nodes": [{"id": "01"}], "edges": [], "timeline": []}

    def _fake_generate(payload, headers=None, env=None):
        recorded["generate_payload"] = payload
        return {"ok": True, "mode": "EDIT", "node": {"id": "01.a1"}, "edges": [], "timeline": []}

    def _fake_filter(payload):
        recorded["filter_payload"] = payload
        return {"ok": True, "node_id": payload.get("node_id"), "filters": payload.get("filters", {})}

    fake_engine.get_node_studio_health = _fake_health
    fake_engine.get_default_studio_state = _fake_state
    fake_engine.handle_node_studio_generate = _fake_generate
    fake_engine.handle_node_studio_filter = _fake_filter
    monkeypatch.setattr(server, "_node_studio_engine", fake_engine)

    status, raw, _ = _http_req(
        f"{live_node_server}/api/health",
        headers={"X-NanoGPT-Api-Key": "ng-test-key"},
    )
    assert status == 200
    assert json.loads(raw)["hasNanogptKey"] is True
    norm_hdrs = {k.lower(): v for k, v in recorded["health_headers"].items()}
    assert norm_hdrs.get("x-nanogpt-api-key") == "ng-test-key"

    status, raw, _ = _http_req(
        f"{live_node_server}/api/generate",
        method="POST",
        payload={"prompt": "Nano Banana Pro 4K", "selected_node_ids": ["01"]},
    )
    assert status == 200
    assert json.loads(raw)["mode"] == "EDIT"
    assert recorded["generate_payload"]["prompt"] == "Nano Banana Pro 4K"

    status, raw, _ = _http_req(
        f"{live_node_server}/api/nodes/filter",
        method="POST",
        payload={"node_id": "01", "filters": {"halation": 35}},
    )
    assert status == 200
    assert json.loads(raw)["filters"] == {"halation": 35}


def test_fastapi_routes_registered_for_node_studio():
    expected_get = (
        "/nodes",
        "/gemini-node-studio",
        "/nodes/timeline",
        "/nodes/gateway",
        "/api/nodes/health",
        "/api/health",
        "/api/nodes/state",
    )
    expected_post = ("/api/nodes/generate", "/api/generate", "/api/nodes/filter")
    if hasattr(server.app, "routes") and isinstance(server.app.routes, dict):
        for route in expected_get:
            assert route in server.app.routes
        for route in expected_post:
            assert route in server.app.post_routes
    else:
        paths = {getattr(r, "path", None) for r in getattr(server.app, "routes", [])}
        for route in expected_get + expected_post:
            assert route in paths
