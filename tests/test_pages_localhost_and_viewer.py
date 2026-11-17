"""Tests for GH-Pages `.space` site hosting (/pages/), /localhost/:port proxy, #win-localhost, and Universal File Viewer."""

from __future__ import annotations

import base64
import gzip
import io
import json
import os
import re
import sqlite3
import struct
import subprocess
import sys
import tarfile
import tempfile
import threading
import urllib.error
import urllib.request
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

import pytest

import server
from iot_federated_agent_memory.file_inspector import guess_mime_type, inspect_binary_file
from iot_federated_agent_memory.glb_rigger import parse_glb
from iot_federated_agent_memory.localhost_ui import render_localhost_window_html
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import legacy_palette_classes


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_no_redir(url: str):
    """Fetch a single HTTP response without following 302/301 redirects."""
    try:
        return urllib.request.build_opener(_NoRedirect()).open(urllib.request.Request(url), timeout=10)
    except urllib.error.HTTPError as err:
        return err


@pytest.fixture(scope="module")
def live_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}", port
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(scope="module")
def mock_dev_server():
    class _DevHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/redir"):
                self.send_response(302)
                self.send_header("Location", "/after-redirect")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = json.dumps({"ok": True, "path": self.path, "method": "GET"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n).decode("utf-8", errors="replace") if n else ""
            body = json.dumps({"ok": True, "path": self.path, "method": "POST", "body": raw}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _DevHandler)
    dev_port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield dev_port
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_guess_mime_types_extended():
    assert guess_mime_type("/models3d/pika.glb") == "model/gltf-binary"
    assert guess_mime_type("/models3d/pika.stl") == "model/stl"
    assert guess_mime_type("/assets/font.woff2") == "font/woff2"
    assert guess_mime_type("/app/module.wasm") == "application/wasm"
    assert guess_mime_type("/site/app.mjs") == "application/javascript; charset=utf-8"
    assert guess_mime_type("/docs/paper.pdf") == "application/pdf"


def test_file_inspector_covers_archives_office_sqlite_meshes_dxf_and_hex():
    # 1. ZIP
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as zf:
        zf.writestr("hello.txt", "world")
    zres = inspect_binary_file(zbuf.getvalue(), "/bundle.zip")
    assert zres["kind"] == "archive" and zres["format"] == "zip"
    assert any(e["name"] == "hello.txt" for e in zres["entries"])

    # 2. TAR.GZ
    tbuf = io.BytesIO()
    with tarfile.open(fileobj=tbuf, mode="w:gz") as tf:
        info = tarfile.TarInfo("readme.md")
        raw_md = b"# Archive"
        info.size = len(raw_md)
        tf.addfile(info, io.BytesIO(raw_md))
    tres = inspect_binary_file(tbuf.getvalue(), "/pkg.tar.gz")
    assert tres["kind"] == "archive" and tres["format"] == "tar"
    assert tres["entries"][0]["name"] == "readme.md"

    # 3. DOCX
    dbuf = io.BytesIO()
    with zipfile.ZipFile(dbuf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>TinCan Spec</w:t></w:r></w:p></w:body></w:document>",
        )
    dres = inspect_binary_file(dbuf.getvalue(), "/notes/spec.docx")
    assert dres["kind"] == "docx" and dres["paragraphs"] == ["TinCan Spec"]

    # 4. XLSX
    xbuf = io.BytesIO()
    with zipfile.ZipFile(xbuf, "w") as zf:
        zf.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Budget" sheetId="1"/></sheets></workbook>',
        )
        zf.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Item</t></si></sst>',
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>42</v></c></row>'
            "</sheetData></worksheet>",
        )
    xres = inspect_binary_file(xbuf.getvalue(), "/sheets/budget.xlsx")
    assert xres["kind"] == "xlsx"
    assert xres["sheets"][0]["name"] == "Budget"
    assert xres["sheets"][0]["rows"][0] == ["Item", "42"]

    # 5. PPTX
    pbuf = io.BytesIO()
    with zipfile.ZipFile(pbuf, "w") as zf:
        zf.writestr(
            "ppt/slides/slide1.xml",
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Pitch Deck Slide</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>",
        )
    pres = inspect_binary_file(pbuf.getvalue(), "/decks/pitch.pptx")
    assert pres["kind"] == "pptx" and pres["slides"][0]["texts"] == ["Pitch Deck Slide"]

    # 6. SQLite
    with tempfile.NamedTemporaryFile(suffix=".sqlite") as sf:
        c = sqlite3.connect(sf.name)
        c.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, label TEXT)")
        c.execute("INSERT INTO items (label) VALUES ('pikachu')")
        c.commit()
        c.close()
        with open(sf.name, "rb") as fh:
            sbytes = fh.read()
    sres = inspect_binary_file(sbytes, "/data/cache.sqlite")
    assert sres["kind"] == "sqlite"
    assert sres["tables"][0]["name"] == "items"
    assert sres["tables"][0]["rows"][0] == [1, "pikachu"]

    # 7. OBJ + STL -> GLB
    obj_txt = b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
    ores = inspect_binary_file(obj_txt, "/models3d/tri.obj")
    assert ores["kind"] == "model_glb"
    gltf, _ = parse_glb(base64.b64decode(ores["glb_b64"]))
    assert len(gltf["meshes"]) == 1

    stl_hdr = b"TinCan STL" + b"\x00" * 70 + struct.pack("<I", 1) + struct.pack("<12fH", 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0)
    stl_res = inspect_binary_file(stl_hdr, "/models3d/part.stl")
    assert stl_res["kind"] == "model_glb"

    # 8. DXF + Generic Binary Hex
    dxf_bytes = b"0\nSECTION\n2\nENTITIES\n0\nLINE\n10\n0\n20\n0\n11\n10\n21\n5\n0\nCIRCLE\n10\n5\n20\n5\n40\n2\n0\nENDSEC\n0\nEOF\n"
    dxf_res = inspect_binary_file(dxf_bytes, "/artcraft/floor.dxf")
    assert dxf_res["kind"] == "dxf" and len(dxf_res["segments"]) == 1 and len(dxf_res["circles"]) == 1

    hex_res = inspect_binary_file(b"\x00asm\x01\x00\x00\x00\xde\xad\xbe\xef", "/bin/mod.wasm")
    assert hex_res["kind"] == "hex"
    assert "WebAssembly" in hex_res["signature"]
    assert "00000000" in hex_res["hex_dump"]


def test_gh_pages_style_space_routes_and_list(live_server):
    base_url, _ = live_server
    owner = f"ghp-{uuid.uuid4().hex[:8]}"

    files = {
        "/dist/index.html": (b"<!DOCTYPE html><script src='./app.js'></script><h1>Dist Build</h1>", "text/html"),
        "/dist/app.js": (b"console.log('dist-ok');", "application/javascript"),
        "/models3d/pikachu_walk.html": (b"<h1>Pikachu Walk</h1>", "text/html"),
    }
    for fpath, (raw, mime) in files.items():
        payload = json.dumps({
            "scope": "user", "owner_id": owner, "path": fpath,
            "content": base64.b64encode(raw).decode("ascii"),
            "is_base64": True, "mime_type": mime, "action": "write", "updated_by": owner,
        }).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/api/space/file", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200

    # Trailing slash canonical redirect on `/pages/user/<owner>`
    with _open_no_redir(f"{base_url}/pages/user/{owner}") as red:
        assert red.status == 302
        assert red.headers["Location"] == f"/pages/user/{owner}/"

    # Root `/pages/user/<owner>/` serves `/dist/index.html` automatically
    with urllib.request.urlopen(f"{base_url}/pages/user/{owner}/", timeout=10) as r:
        assert r.status == 200
        assert "<h1>Dist Build</h1>" in r.read().decode("utf-8")
        assert "text/html" in r.headers.get("Content-Type", "")

    # Relative asset shorthand `/pages/<owner>/dist/app.js`
    with urllib.request.urlopen(f"{base_url}/pages/{owner}/dist/app.js", timeout=10) as r:
        assert r.status == 200
        assert "dist-ok" in r.read().decode("utf-8")
        assert "javascript" in r.headers.get("Content-Type", "")

    # Directory listing when folder lacks index.html
    with urllib.request.urlopen(f"{base_url}/pages/user/{owner}/models3d/", timeout=10) as r:
        html = r.read().decode("utf-8")
        assert "pikachu_walk.html" in html

    # Entrypoint discovery endpoint + /api/file/inspect on .space file
    with urllib.request.urlopen(f"{base_url}/api/pages/list?scope=user&owner_id={owner}", timeout=10) as r:
        lp = json.loads(r.read().decode("utf-8"))
        assert lp["ok"] is True
        paths = [e["path"] for e in lp["entrypoints"]]
        assert "/dist/index.html" in paths and "/models3d/pikachu_walk.html" in paths

    insp_req = urllib.request.Request(
        f"{base_url}/api/file/inspect",
        data=json.dumps({"scope": "user", "owner_id": owner, "source": "space", "path": "/dist/app.js"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(insp_req, timeout=10) as r:
        insp = json.loads(r.read().decode("utf-8"))
        assert insp["ok"] is True and insp["kind"] == "hex" and "hex_dump" in insp


def test_localhost_port_proxy_and_safety_guards(live_server, mock_dev_server):
    base_url, own_port = live_server

    # Proxied GET + query string
    with urllib.request.urlopen(f"{base_url}/localhost/{mock_dev_server}/hello?foo=bar", timeout=10) as r:
        assert r.status == 200
        data = json.loads(r.read().decode("utf-8"))
        assert data == {"ok": True, "path": "/hello?foo=bar", "method": "GET"}

    # Redirect Location rewriting
    with _open_no_redir(f"{base_url}/localhost/{mock_dev_server}/redir") as r:
        assert r.status == 302
        assert r.headers["Location"] == f"/localhost/{mock_dev_server}/after-redirect"

    # Proxied POST body
    req_post = urllib.request.Request(
        f"{base_url}/localhost/{mock_dev_server}/submit",
        data=b'{"a":1}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req_post, timeout=10) as r:
        pdata = json.loads(r.read().decode("utf-8"))
        assert pdata["method"] == "POST" and pdata["body"] == '{"a":1}'

    # Self-loop protection
    with pytest.raises(urllib.error.HTTPError) as exc_loop:
        urllib.request.urlopen(f"{base_url}/localhost/{own_port}/", timeout=5)
    assert exc_loop.value.code == 508

    # Privileged port block
    with pytest.raises(urllib.error.HTTPError) as exc_priv:
        urllib.request.urlopen(f"{base_url}/localhost/80/", timeout=5)
    assert exc_priv.value.code == 403


def test_localhost_ui_and_universal_viewer_markers_and_js_syntax():
    lh_html = render_localhost_window_html()
    assert legacy_palette_classes(lh_html) == []
    assert 'id="win-localhost"' in lh_html
    assert 'id="lhFrame"' in lh_html
    assert "TinCanLocalhost" in lh_html

    for marker in (
        'id="win-localhost"',
        'id="dockBtn-win-localhost"',
        'id="finderPdfContainer"',
        'id="finderHtmlContainer"',
        'id="finderRichContainer"',
        "renderCsvTableView",
        "renderNotebookView",
        "renderFontPreview",
        "renderBinaryInspectView",
        "openCurrentHtmlInLocalhostBrowser",
        "window.location.pathname === '/localhost'",
    ):
        assert marker in MESH_OS_HTML_UI

    # Verify every inline <script> inside MESH_OS_HTML_UI parses cleanly in node
    scripts = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", MESH_OS_HTML_UI, re.S)
    for idx, src in enumerate(scripts):
        if not src.strip():
            continue
        with tempfile.NamedTemporaryFile("w", suffix=f"_{idx}.js", delete=False) as tf:
            tf.write(src)
            p = tf.name
        try:
            subprocess.run(["node", "--check", p], check=True, capture_output=True, text=True)
        finally:
            os.unlink(p)
