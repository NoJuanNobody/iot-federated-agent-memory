"""Tests for Nano Banana Gemini Node Studio routes, Home Screen mounting, #win-nodes, and Design Gallery."""

import base64
import json
import os
import sys
import threading
import types
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR in sys.path:
    sys.path.remove(WORKTREE_DIR)
sys.path.insert(0, WORKTREE_DIR)

for _mod in list(sys.modules.keys()):
    if _mod.startswith("iot_federated_agent_memory") or _mod == "server":
        del sys.modules[_mod]

import server
from iot_federated_agent_memory.agent_space import AgentSpaceManager, generate_minimal_glb_bytes
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
        "/api/nodes/video/status",
        "/api/nodes/mesh/status",
        "/api/nodes/audio/status",
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


def _http_req_bytes(url: str, headers=None):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return resp.status, resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as err:
        return err.code, err.read(), {k.lower(): v for k, v in err.headers.items()}


def _start_fixture_media_server(routes: dict):
    class _FixtureHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            item = routes.get(self.path)
            if item is None:
                self.send_response(404)
                self.end_headers()
                return
            ctype, body = item
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def test_space_file_raw_http_range_206_and_416(live_node_server, tmp_path, monkeypatch):
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=server.router)
    monkeypatch.setattr(server, "_space_manager", temp_mgr)
    monkeypatch.setattr(server, "_get_space_manager", lambda: temp_mgr)

    payload_bytes = bytes(range(100))
    sp = temp_mgr.get_or_create_space("user", "range_peer")
    sp.write_file("/videos/sample.mp4", payload_bytes, mime_type="video/mp4", updated_by="range_peer")

    raw_url = f"{live_node_server}/api/space/file?raw=1&scope=user&owner_id=range_peer&path=/videos/sample.mp4"

    # Full GET includes Accept-Ranges: bytes
    st_full, body_full, hdrs_full = _http_req_bytes(raw_url)
    assert st_full == 200
    assert hdrs_full.get("accept-ranges") == "bytes"
    assert body_full == payload_bytes

    # Explicit byte slice Range: bytes=0-9 -> 206 Partial Content
    st_206, body_206, hdrs_206 = _http_req_bytes(raw_url, headers={"Range": "bytes=0-9"})
    assert st_206 == 206
    assert hdrs_206.get("accept-ranges") == "bytes"
    assert hdrs_206.get("content-range") == "bytes 0-9/100"
    assert hdrs_206.get("content-length") == "10"
    assert body_206 == payload_bytes[0:10]

    # Open-ended Range: bytes=90-
    st_open, body_open, hdrs_open = _http_req_bytes(raw_url, headers={"Range": "bytes=90-"})
    assert st_open == 206
    assert hdrs_open.get("content-range") == "bytes 90-99/100"
    assert body_open == payload_bytes[90:100]

    # Suffix Range: bytes=-5
    st_suf, body_suf, hdrs_suf = _http_req_bytes(raw_url, headers={"Range": "bytes=-5"})
    assert st_suf == 206
    assert hdrs_suf.get("content-range") == "bytes 95-99/100"
    assert body_suf == payload_bytes[95:100]

    # Out-of-bounds Range -> 416
    st_416, _, hdrs_416 = _http_req_bytes(raw_url, headers={"Range": "bytes=200-300"})
    assert st_416 == 416
    assert hdrs_416.get("content-range") == "bytes */100"


def test_nodes_video_status_and_sync_mirroring_to_space(live_node_server, tmp_path, monkeypatch):
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=server.router)
    monkeypatch.setattr(server, "_space_manager", temp_mgr)
    monkeypatch.setattr(server, "_get_space_manager", lambda: temp_mgr)

    fake_mp4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"VIDEOBYTES" * 8
    media_srv, media_base = _start_fixture_media_server({"/clip.mp4": ("video/mp4", fake_mp4)})
    try:
        remote_mp4_url = f"{media_base}/clip.mp4"
        eng = server._get_node_studio_engine()
        assert eng is not None

        # 1. Poll status -> SUCCEEDED -> mirrors into .space/videos/ and returns durable raw URL
        monkeypatch.setattr(
            eng,
            "poll_nanogpt_video_status",
            lambda job_id, *, model_slug=None, api_key="", http_get_json=None: {
                "ok": True,
                "done": True,
                "status": "SUCCEEDED",
                "job_id": job_id,
                "model_slug": model_slug,
                "remote_url": remote_mp4_url,
                "urls": [remote_mp4_url],
            },
        )
        st, raw, _ = _http_req(
            f"{live_node_server}/api/nodes/video/status?job_id=vid_done_1&model=ltx-video&scope=user&owner_id=vid_peer&prompt=Neon+Alley",
            headers={"X-NanoGPT-Api-Key": "ngpt-key"},
        )
        assert st == 200
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["done"] is True
        assert data["status"] == "SUCCEEDED"
        assert data["job_id"] == "vid_done_1"
        assert data["remote_url"] == remote_mp4_url
        assert data["vfs_path"].startswith("/videos/") and data["vfs_path"].endswith(".mp4")
        assert data["video_url"].startswith("/api/space/file?raw=1&")
        assert data["size_bytes"] == len(fake_mp4)

        # Verify durable raw URL serves 206 byte ranges with exact MP4 bytes
        st_r, chunk, hdrs_r = _http_req_bytes(
            f"{live_node_server}{data['video_url']}",
            headers={"Range": "bytes=0-11"},
        )
        assert st_r == 206
        assert hdrs_r.get("accept-ranges") == "bytes"
        assert chunk == fake_mp4[:12]

        # 2. Synchronous video response in /api/nodes/generate also mirrors into .space/videos/
        monkeypatch.setattr(
            eng,
            "handle_node_studio_generate",
            lambda payload, headers=None, env=None: {
                "ok": True,
                "statusCode": 200,
                "mode": "GENERATE",
                "modality": "video",
                "node": {
                    "id": "node-v1",
                    "data": {
                        "modality": "video",
                        "content": {"text": "Synced", "videoUrl": remote_mp4_url, "mimeType": "video/mp4"},
                    },
                },
                "edges": [],
                "timeline": {},
                "result": {"video": {"url": remote_mp4_url, "mimeType": "video/mp4"}},
            },
        )
        st_g, raw_g, _ = _http_req(
            f"{live_node_server}/api/nodes/generate",
            method="POST",
            payload={"prompt": "Sync dolly shot", "modality": "video", "scope": "user", "owner_id": "vid_peer"},
        )
        assert st_g == 200
        gen = json.loads(raw_g)
        content = gen["node"]["data"]["content"]
        assert content["videoUrl"].startswith("/api/space/file?raw=1&")
        assert content["remoteUrl"] == remote_mp4_url
        assert content["vfsPath"].startswith("/videos/")
    finally:
        media_srv.shutdown()
        media_srv.server_close()


def test_nodes_mesh_status_and_omni_route_3d_async_vs_completed(live_node_server, tmp_path, monkeypatch):
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=server.router)
    monkeypatch.setattr(server, "_space_manager", temp_mgr)
    monkeypatch.setattr(server, "_get_space_manager", lambda: temp_mgr)

    real_glb = generate_minimal_glb_bytes("guardian_mech")
    media_srv, media_base = _start_fixture_media_server({"/mesh.glb": ("model/gltf-binary", real_glb)})
    try:
        remote_glb_url = f"{media_base}/mesh.glb"

        # 1. GET /api/nodes/mesh/status -> RUNNING, FAILED, then Done -> persists .glb into .space/models3d/
        monkeypatch.setattr(
            server.router,
            "check_rodin_status",
            lambda job_id, **kw: {"subscription_key": job_id, "uuid": job_id, "status": "Processing"},
        )
        st_run, raw_run, _ = _http_req(
            f"{live_node_server}/api/nodes/mesh/status?job_id=rodin_live_1&scope=user&owner_id=mesh_peer"
        )
        assert st_run == 200
        d_run = json.loads(raw_run)
        assert d_run == {"ok": True, "done": False, "status": "RUNNING", "job_id": "rodin_live_1"}

        monkeypatch.setattr(
            server.router,
            "check_rodin_status",
            lambda job_id, **kw: {"subscription_key": job_id, "uuid": job_id, "status": "Failed", "error": "Mesh error"},
        )
        st_fail, raw_fail, _ = _http_req(
            f"{live_node_server}/api/nodes/mesh/status?job_id=rodin_live_1&scope=user&owner_id=mesh_peer"
        )
        assert st_fail == 200
        d_fail = json.loads(raw_fail)
        assert d_fail["ok"] is False
        assert d_fail["done"] is True
        assert d_fail["status"] == "FAILED"
        assert "Mesh error" in d_fail["error"]

        monkeypatch.setattr(
            server.router,
            "check_rodin_status",
            lambda job_id, **kw: {
                "subscription_key": job_id,
                "uuid": job_id,
                "status": "Done",
                "urls": [remote_glb_url],
            },
        )
        st_done, raw_done, _ = _http_req(
            f"{live_node_server}/api/nodes/mesh/status?job_id=rodin_live_1&scope=user&owner_id=mesh_peer&prompt=Bronze+Sentinel"
        )
        assert st_done == 200
        d_done = json.loads(raw_done)
        assert d_done["ok"] is True
        assert d_done["done"] is True
        assert d_done["status"] == "SUCCEEDED"
        assert d_done["vfs_path"].startswith("/models3d/") and d_done["vfs_path"].endswith(".glb")
        assert d_done["glb_raw_url"].startswith("/api/space/file?raw=1&")
        assert d_done["size_bytes"] == len(real_glb)
        assert base64.b64decode(d_done["glb_bytes_b64"]) == real_glb

        st_glb, glb_body, _ = _http_req_bytes(f"{live_node_server}{d_done['glb_raw_url']}")
        assert st_glb == 200
        assert glb_body == real_glb

        # 2. POST /api/omni/route /3d -> live async Rodin returns async: True, done: False, job_id
        monkeypatch.setattr(
            server,
            "_dispatch_rodin",
            lambda rtr, **kw: {
                "uuid": "rodin_async_777",
                "subscription_key": "sub_async_777",
                "status": "Waiting",
                "simulated": False,
                "glb_bytes_b64": "",
            },
        )
        st_async, raw_async, _ = _http_req(
            f"{live_node_server}/api/omni/route",
            method="POST",
            payload={"command": "/3d brutalist sentinel mech", "scope": "user", "owner_id": "mesh_peer"},
        )
        assert st_async == 200
        d_async = json.loads(raw_async)
        assert d_async["ok"] is True
        assert d_async["async"] is True
        assert d_async["done"] is False
        assert d_async["status"] == "RUNNING"
        assert d_async["job_id"] == "sub_async_777"

        # 3. POST /api/omni/route /3d -> completed/simulated includes glb_raw_url in result & top-level
        monkeypatch.setattr(
            server,
            "_dispatch_rodin",
            lambda rtr, **kw: {
                "uuid": "rodin_sim_888",
                "subscription_key": "sub_sim_888",
                "status": "Done",
                "simulated": True,
                "glb_bytes_b64": base64.b64encode(real_glb).decode("ascii"),
            },
        )
        st_sim, raw_sim, _ = _http_req(
            f"{live_node_server}/api/omni/route",
            method="POST",
            payload={"command": "/3d celadon bonsai statue", "scope": "user", "owner_id": "mesh_peer"},
        )
        assert st_sim == 200
        d_sim = json.loads(raw_sim)
        assert d_sim["ok"] is True
        assert d_sim["glb_raw_url"].startswith("/api/space/file?raw=1&")
        assert d_sim["result"]["glb_raw_url"] == d_sim["glb_raw_url"]
        st_sim_glb, sim_body, _ = _http_req_bytes(f"{live_node_server}{d_sim['glb_raw_url']}")
        assert st_sim_glb == 200
        assert sim_body == real_glb
    finally:
        media_srv.shutdown()
        media_srv.server_close()


def test_nodes_audio_status_and_omni_route_audio_streaming(live_node_server, tmp_path, monkeypatch):
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=server.router)
    monkeypatch.setattr(server, "_space_manager", temp_mgr)
    monkeypatch.setattr(server, "_get_space_manager", lambda: temp_mgr)

    fake_mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"LIVEMP3STREAM" * 16
    fake_mp3_b64 = base64.b64encode(fake_mp3).decode("ascii")

    # 1. Immediate real MP3 generation via /api/omni/route saves .mp3 into .space/audio/ and streams 206 Range
    monkeypatch.setattr(
        server.router,
        "generate_omni_audio",
        lambda prompt, **kw: {
            "ok": True,
            "done": True,
            "simulated": False,
            "kind": kw.get("kind") or "tts",
            "model": kw.get("model") or "elevenlabs/eleven-v4",
            "audio_bytes_b64": fake_mp3_b64,
            "mime_type": "audio/mpeg",
            "ext": ".mp3",
            "size_bytes": len(fake_mp3),
        },
    )
    st_imm, raw_imm, _ = _http_req(
        f"{live_node_server}/api/omni/route",
        method="POST",
        payload={"command": '/audio tts --model elevenlabs/eleven-v4 "Hello TinCan"', "scope": "user", "owner_id": "aud_peer"},
        headers={"X-NanoGPT-Api-Key": "ng-aud-key"},
    )
    assert st_imm == 200
    d_imm = json.loads(raw_imm)
    assert d_imm["ok"] is True
    assert d_imm["audio_raw_url"].startswith("/api/space/file?raw=1&")
    assert d_imm["saved_to_space"]["path"].startswith("/audio/")
    assert d_imm["saved_to_space"]["path"].endswith(".mp3")

    st_206, chunk_206, hdrs_206 = _http_req_bytes(
        f"{live_node_server}{d_imm['audio_raw_url']}",
        headers={"Range": "bytes=0-15"},
    )
    assert st_206 == 206
    assert hdrs_206.get("accept-ranges") == "bytes"
    assert chunk_206 == fake_mp3[:16]

    # 2. Async audio job propagation via /api/omni/route -> GET /api/nodes/audio/status (RUNNING -> FAILED -> SUCCEEDED)
    monkeypatch.setattr(
        server.router,
        "generate_omni_audio",
        lambda prompt, **kw: {
            "ok": True,
            "async": True,
            "done": False,
            "status": "RUNNING",
            "job_id": "aud_run_900",
            "model": "google/lyria-3.5",
            "cost": 0.11,
            "payment_source": "USD",
        },
    )
    st_async, raw_async, _ = _http_req(
        f"{live_node_server}/api/omni/route",
        method="POST",
        payload={"command": '/audio music "Ambient alpine koto"', "scope": "user", "owner_id": "aud_peer"},
    )
    assert st_async == 200
    d_async = json.loads(raw_async)
    assert d_async["ok"] is True
    assert d_async["async"] is True
    assert d_async["done"] is False
    assert d_async["job_id"] == "aud_run_900"
    assert d_async["cost"] == 0.11

    monkeypatch.setattr(
        server.router,
        "poll_nanogpt_audio_status",
        lambda jid, **kw: {"ok": True, "done": False, "status": "RUNNING", "job_id": jid, "model": kw.get("model") or ""},
    )
    st_p1, raw_p1, _ = _http_req(
        f"{live_node_server}/api/nodes/audio/status?job_id=aud_run_900&model=google/lyria-3.5&scope=user&owner_id=aud_peer"
    )
    assert st_p1 == 200
    assert json.loads(raw_p1)["done"] is False

    monkeypatch.setattr(
        server.router,
        "poll_nanogpt_audio_status",
        lambda jid, **kw: {
            "ok": True,
            "done": True,
            "status": "SUCCEEDED",
            "job_id": jid,
            "model": "google/lyria-3.5",
            "audio_bytes_b64": fake_mp3_b64,
            "mime_type": "audio/mpeg",
            "ext": ".mp3",
            "size_bytes": len(fake_mp3),
        },
    )
    st_p2, raw_p2, _ = _http_req(
        f"{live_node_server}/api/nodes/audio/status?job_id=aud_run_900&model=google/lyria-3.5&kind=music&scope=user&owner_id=aud_peer&prompt=Alpine+koto"
    )
    assert st_p2 == 200
    d_p2 = json.loads(raw_p2)
    assert d_p2["ok"] is True
    assert d_p2["done"] is True
    assert d_p2["status"] == "SUCCEEDED"
    assert d_p2["vfs_path"].startswith("/audio/") and d_p2["vfs_path"].endswith(".mp3")
    assert d_p2["audio_url"].startswith("/api/space/file?raw=1&")

    st_aud_r, aud_r_bytes, _ = _http_req_bytes(
        f"{live_node_server}{d_p2['audio_url']}",
        headers={"Range": "bytes=0-9"},
    )
    assert st_aud_r == 206
    assert aud_r_bytes == fake_mp3[:10]

    # 3. Upstream error surfaces cleanly without faking a beep
    monkeypatch.setattr(
        server.router,
        "generate_omni_audio",
        lambda prompt, **kw: {"ok": False, "status_code": 502, "error": "NanoGPT audio quota exceeded"},
    )
    st_err, raw_err, _ = _http_req(
        f"{live_node_server}/api/omni/route",
        method="POST",
        payload={"command": '/audio music "Fail test"', "scope": "user", "owner_id": "aud_peer"},
    )
    assert st_err == 502
    d_err = json.loads(raw_err)
    assert d_err["ok"] is False
    assert "quota exceeded" in d_err["error"]
