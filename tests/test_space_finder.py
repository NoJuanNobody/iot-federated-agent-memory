"""Tests for the Space file manager injected by space_finder, and the /api/space/raw route."""

import base64
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.space_finder import apply_space_finder


def test_apply_injects_once_and_is_idempotent():
    assert MESH_OS_HTML_UI.count('id="tcSpaceScript"') == 1
    assert apply_space_finder(MESH_OS_HTML_UI) == MESH_OS_HTML_UI
    frag = "<html><head></head><body></body></html>"
    once = apply_space_finder(frag)
    assert once != frag
    assert apply_space_finder(once) == once
    assert apply_space_finder("<div>fragment</div>") == "<div>fragment</div>"


def test_space_markup_present():
    for el in ("tcSpaceFiles", "tcRgCur", "tcRgPreview", "tcSpaceExt", "tcSpaceArt"):
        assert f'id="{el}"' in MESH_OS_HTML_UI


def test_old_mock_markup_is_gone():
    for gone in ("finderTab-vscode", "Launch in Wasm", "/media/demo.mp4"):
        assert gone not in MESH_OS_HTML_UI


def test_extensions_use_open_vsx_and_vscode_recommendations():
    assert "open-vsx.org" in MESH_OS_HTML_UI
    assert "/.vscode/extensions.json" in MESH_OS_HTML_UI


@pytest.fixture(scope="module")
def raw_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 18177), server.MeshGatewayHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.3)
    yield "http://127.0.0.1:18177"
    httpd.shutdown()
    httpd.server_close()


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def test_space_raw_serves_file_bytes(raw_server):
    owner = "raw-tester"
    data = b"\x89PNG\r\n\x1a\n" + bytes(range(256))
    _post(f"{raw_server}/api/space/file", {
        "scope": "user", "owner_id": owner, "path": "/media/pic.jpg",
        "content": base64.b64encode(data).decode(), "is_base64": True, "action": "write",
    })
    _post(f"{raw_server}/api/space/file", {
        "scope": "user", "owner_id": owner, "path": "/notes/a.txt", "content": "hello raw", "action": "write",
    })
    with urllib.request.urlopen(f"{raw_server}/api/space/raw?scope=user&owner_id={owner}&path=/notes/a.txt", timeout=5) as r:
        assert r.read() == b"hello raw"
        assert r.headers["Content-Type"].startswith("text/")
        assert r.headers["Content-Disposition"].startswith("inline")
    with urllib.request.urlopen(f"{raw_server}/api/space/raw?scope=user&owner_id={owner}&path=/media/pic.jpg", timeout=5) as r:
        assert r.read() == data
        assert r.headers["Content-Type"] == "image/jpeg"
    with urllib.request.urlopen(f"{raw_server}/api/space/raw?scope=user&owner_id={owner}&path=/notes/a.txt&download=1", timeout=5) as r:
        cd = r.headers["Content-Disposition"]
        assert cd.startswith("attachment") and 'filename="a.txt"' in cd


def test_space_raw_404_for_missing_path(raw_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{raw_server}/api/space/raw?scope=user&owner_id=raw-tester&path=/nope/missing.bin", timeout=5)
    assert exc.value.code == 404
