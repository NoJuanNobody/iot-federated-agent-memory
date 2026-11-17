"""Tests for TinCan Browser engine, HTTP endpoints, Desktop UI (#win-browser), and sandbox CLI."""

from __future__ import annotations

import base64
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.request

import pytest

from iot_federated_agent_memory.agent_space import (
    AgentSpaceManager,
    build_tincan_capability_manifest,
    prepare_harness_sandbox_env,
)
from iot_federated_agent_memory.browser_engine import (
    TinCanBrowserManager,
    normalize_and_validate_url,
)
from iot_federated_agent_memory.browser_ui import render_browser_window_html
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import (
    apply_window_chrome,
    expand_titlebars,
    legacy_palette_classes,
)


def test_url_normalization_and_ssrf_guardrails():
    assert normalize_and_validate_url("example.com") == "https://example.com"
    assert normalize_and_validate_url("https://arxiv.org/list/cs.AI/recent") == "https://arxiv.org/list/cs.AI/recent"

    for bad in ("javascript:alert(1)", "file:///etc/passwd", "http://127.0.0.1:8080/", "http://169.254.169.254/latest", "http://localhost:3000"):
        with pytest.raises(ValueError):
            normalize_and_validate_url(bad, allow_private=False)

    assert normalize_and_validate_url("http://127.0.0.1:8080/hi", allow_private=True) == "http://127.0.0.1:8080/hi"


@pytest.fixture()
def demo_web_server():
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/page2":
                html = "<html><head><title>Page Two</title></head><body><h1>Second Page</h1><p>Reached page two cleanly.</p></body></html>"
            else:
                html = (
                    "<html><head><title>TinCan Demo Site</title></head><body>"
                    "<h1>Welcome to TinCan Web</h1>"
                    "<p>Playwright &amp; Reader test paragraph.</p>"
                    '<input id="q" name="query" placeholder="Search...">'
                    '<button type="submit">Go</button>'
                    '<a href="/page2">Go To Page 2</a>'
                    "</body></html>"
                )
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            return

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{srv.server_port}"
    finally:
        srv.shutdown()
        srv.server_close()


def test_browser_manager_navigate_history_elements_and_save(tmp_path, demo_web_server):
    bm = TinCanBrowserManager(allow_private=True, prefer_playwright=False)
    nav1 = bm.navigate(demo_web_server, session_id="s-test")
    assert nav1["ok"] is True
    assert nav1["engine"] == "reader"
    assert nav1["title"] == "TinCan Demo Site"
    assert "Welcome to TinCan Web" in nav1["text"]
    assert any(l["href"].endswith("/page2") for l in nav1["links"])
    assert any(el["tag"] == "input" for el in nav1["elements"])
    assert base64.b64decode(nav1["screenshot_b64"]).startswith(b"\x89PNG")

    # Click extracted link element navigates to /page2 and enables Back
    link_ref = next(el["ref"] for el in nav1["elements"] if el["tag"] == "a")
    nav2 = bm.action("s-test", "click", selector=link_ref)
    assert nav2["title"] == "Page Two"
    assert nav2["can_back"] is True

    back = bm.action("s-test", "back")
    assert back["title"] == "TinCan Demo Site"
    assert back["can_forward"] is True

    # Save Markdown + Screenshot into .space VFS
    sm = AgentSpaceManager(base_dir=str(tmp_path))
    saved_md = bm.save_to_space("s-test", sm, scope="user", owner_id="br_user", kind="markdown")
    saved_png = bm.save_to_space("s-test", sm, scope="user", owner_id="br_user", kind="screenshot")
    assert saved_md["path"].startswith("/notes/web_") and saved_md["path"].endswith(".md")
    assert saved_png["path"].startswith("/images/web_") and saved_png["path"].endswith(".png")
    sp = sm.get_space("user", "br_user")
    assert "Welcome to TinCan Web" in sp.read_file(saved_md["path"])["content"]
    assert base64.b64decode(sp.read_file(saved_png["path"], as_text=False)["content_b64"]).startswith(b"\x89PNG")


def test_browser_http_routes_end_to_end(tmp_path, monkeypatch, demo_web_server):
    import tests.test_tincan_ux_updates as ux_mod

    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)

    bm = TinCanBrowserManager(allow_private=True, prefer_playwright=False)
    monkeypatch.setattr(srv, "_get_browser_manager", lambda: bm)

    with ux_mod._live_server() as (host, port):
        base = f"http://{host}:{port}"

        def _req(path, payload=None):
            data = json.dumps(payload).encode("utf-8") if payload is not None else None
            r = urllib.request.Request(
                f"{base}{path}",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST" if data is not None else "GET",
            )
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")

        st_raw, _ = _req("/api/browser/state")
        assert "engine_default" in json.loads(st_raw.decode("utf-8"))

        nav_raw, _ = _req("/api/browser/navigate", {"url": demo_web_server, "session_id": "http-br"})
        nav = json.loads(nav_raw.decode("utf-8"))
        assert nav["title"] == "TinCan Demo Site"

        shot_raw, ctype = _req("/api/browser/screenshot?session_id=http-br")
        assert ctype.startswith("image/png")
        assert shot_raw.startswith(b"\x89PNG")

        save_raw, _ = _req("/api/browser/save", {"session_id": "http-br", "scope": "user", "owner_id": "http_br", "kind": "markdown"})
        save_res = json.loads(save_raw.decode("utf-8"))
        assert save_res["ok"] is True
        assert save_res["path"].endswith(".md")


def test_browser_ui_celadon_js_and_mesh_os_registration():
    br_html = render_browser_window_html()
    assert 'id="win-browser"' in br_html
    assert legacy_palette_classes(br_html) == []

    expanded = expand_titlebars(br_html)
    assert 'data-tc-titlebar="win-browser"' in expanded
    chromed = apply_window_chrome(f"<!doctype html><html><head></head><body>{br_html}</body></html>")
    assert legacy_palette_classes(chromed.split("<body>", 1)[1]) == []

    br_ids = re.findall(r'(?<![\w-])id="([^"]+)"', br_html)
    assert len(br_ids) == len(set(br_ids))
    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    assert [eid for eid in br_ids if mesh_counts[eid] != 1] == []

    assert 'id="dockBtn-win-browser"' in MESH_OS_HTML_UI
    assert "'win-browser'" in MESH_OS_HTML_UI

    # JS syntax & partial-DOM execution check
    m = re.search(r'<script\s+id="browserUiScript"[^>]*>(.*?)</script>', br_html, flags=re.DOTALL)
    assert m
    script = m.group(1)
    node = shutil.which("node")
    if node:
        chk = subprocess.run([node, "--check", "-"], input=script, text=True, capture_output=True, check=False)
        assert chk.returncode == 0, chk.stderr


def test_sandbox_installs_tincan_browse_and_manifest(tmp_path):
    env = prepare_harness_sandbox_env(str(tmp_path / "work"), str(tmp_path / "cache"))
    bin_dir = env["PATH"].split(os.pathsep)[0]
    browse_bin = os.path.join(bin_dir, "tincan-browse")
    assert os.path.isfile(browse_bin)
    assert os.access(browse_bin, os.X_OK)
    manifest = build_tincan_capability_manifest()
    assert "tincan-browse" in manifest
