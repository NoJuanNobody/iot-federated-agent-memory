"""Tests for the read-only, login-time hard-drive mirror used by the Ranger VFS."""

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory import drive_mirror


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "Developer" / "tincan" / "src").mkdir(parents=True)
    (home / "Developer" / "tincan" / "node_modules" / "left-pad").mkdir(parents=True)
    (home / "Developer" / "tincan" / ".git").mkdir()
    (home / "Developer" / "tincan" / "README.md").write_text("# TinCan\n")
    (home / "Documents").mkdir()
    (home / "Documents" / "notes.txt").write_text("hello")
    (home / "Documents" / "blob.bin").write_bytes(b"\x00\x01\x02" * 10)
    (home / ".ssh").mkdir()
    (home / ".ssh" / "id_rsa").write_text("secret")
    (home / "Library").mkdir()
    for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID",
              "TINCAN_DRIVE_MIRROR", "TINCAN_DEV_DIR"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("TINCAN_DRIVE_ROOT", str(home))
    return home


def _snapshot(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for n in sorted(dirnames + filenames):
            p = os.path.join(dirpath, n)
            out.append((p, os.path.getmtime(p)))
    return sorted(out)


def test_dev_folder_detected_and_pinned_first(fake_home):
    assert drive_mirror.find_dev_folder(str(fake_home)) == os.path.realpath(fake_home / "Developer")
    m = drive_mirror.gather_mirror(str(fake_home))
    assert m["dev_folder"] == "/Developer"
    assert m["places"][0]["kind"] == "dev" and m["places"][0]["pinned"] is True
    names = [p["name"] for p in m["places"]]
    assert names.count("Developer") == 1
    assert "Documents" in names
    assert ".ssh" not in names and "Library" not in names
    assert m["persisted"] is False


def test_dev_folder_env_override(fake_home, monkeypatch):
    (fake_home / "work").mkdir()
    monkeypatch.setenv("TINCAN_DEV_DIR", str(fake_home / "work"))
    assert drive_mirror.find_dev_folder(str(fake_home)) == os.path.realpath(fake_home / "work")


def test_scan_skips_vendor_and_hidden_dirs(fake_home):
    m = drive_mirror.gather_mirror(str(fake_home))
    tincan = next(c for c in m["places"][0]["children"] if c["name"] == "tincan")
    child_names = [c["name"] for c in tincan["children"]]
    assert child_names == ["src"]


def test_gather_is_fresh_each_time(fake_home):
    first = drive_mirror.gather_mirror(str(fake_home))
    (fake_home / "Music").mkdir()
    second = drive_mirror.gather_mirror(str(fake_home))
    assert "Music" not in [p["name"] for p in first["places"]]
    assert "Music" in [p["name"] for p in second["places"]]


def test_caps_limit_scan(fake_home):
    for i in range(30):
        (fake_home / "Developer" / f"proj{i:02d}").mkdir()
    m = drive_mirror.gather_mirror(str(fake_home), max_entries=5)
    assert m["truncated"] is True
    m2 = drive_mirror.gather_mirror(str(fake_home), max_depth=1)
    assert all(c.get("more") for c in m2["places"][0]["children"])


def test_list_dir_and_preview(fake_home):
    ls = drive_mirror.list_dir(str(fake_home), "/Documents")
    assert [f["name"] for f in ls["files"]] == ["blob.bin", "notes.txt"]
    txt = drive_mirror.read_text_preview(str(fake_home), "/Documents/notes.txt")
    assert txt["content"] == "hello" and txt["is_binary"] is False and txt["read_only"] is True
    binf = drive_mirror.read_text_preview(str(fake_home), "/Documents/blob.bin")
    assert binf["is_binary"] is True and binf["content"] is None


def test_large_text_truncated(fake_home):
    (fake_home / "Documents" / "big.log").write_text("x" * 5000)
    rec = drive_mirror.read_text_preview(str(fake_home), "/Documents/big.log", max_bytes=1000)
    assert rec["truncated"] is True and len(rec["content"]) == 1000


def test_path_traversal_blocked(fake_home, tmp_path):
    (tmp_path / "outside.txt").write_text("nope")
    with pytest.raises(drive_mirror.MirrorAccessError):
        drive_mirror.read_text_preview(str(fake_home), "/../outside.txt")
    os.symlink(tmp_path, fake_home / "Documents" / "escape")
    with pytest.raises(drive_mirror.MirrorAccessError):
        drive_mirror.read_text_preview(str(fake_home), "/Documents/escape/outside.txt")


def test_mirror_never_writes_to_disk(fake_home):
    before = _snapshot(fake_home)
    drive_mirror.gather_mirror(str(fake_home))
    drive_mirror.list_dir(str(fake_home), "/Developer/tincan")
    drive_mirror.read_text_preview(str(fake_home), "/Developer/tincan/README.md")
    assert _snapshot(fake_home) == before


def test_disabled_on_railway_unless_forced(fake_home, monkeypatch):
    assert drive_mirror.mirror_enabled() is True
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    assert drive_mirror.mirror_enabled() is False
    assert drive_mirror.request_allowed("127.0.0.1", "localhost:8080") is False
    monkeypatch.setenv("TINCAN_DRIVE_MIRROR", "1")
    assert drive_mirror.mirror_enabled() is True


def test_request_allowed_local_only(fake_home):
    assert drive_mirror.request_allowed("127.0.0.1", "localhost:8080") is True
    assert drive_mirror.request_allowed("::1", "[::1]:8080") is True
    assert drive_mirror.request_allowed("10.0.0.5", "localhost:8080") is False
    assert drive_mirror.request_allowed("127.0.0.1", "evil.example:8080") is False  # DNS rebinding
    assert drive_mirror.request_allowed("127.0.0.1", "localhost", forwarded_for="1.2.3.4") is False


@pytest.fixture
def live_server(fake_home):
    import server
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://localhost:{port}"
    httpd.shutdown()


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


def test_drive_endpoints(live_server, fake_home):
    status, headers, body = _get(f"{live_server}/api/drive/status")
    assert json.loads(body)["available"] is True
    status, headers, body = _get(f"{live_server}/api/drive/mirror")
    data = json.loads(body)
    assert data["dev_folder"] == "/Developer"
    assert headers.get("Cache-Control") == "no-store"
    assert "Access-Control-Allow-Origin" not in headers
    _, _, body = _get(f"{live_server}/api/drive/ls?path=/Developer/tincan")
    ls = json.loads(body)
    assert [d["name"] for d in ls["dirs"]] == ["src"]
    _, _, body = _get(f"{live_server}/api/drive/file?path=/Developer/tincan/README.md")
    assert json.loads(body)["content"] == "# TinCan\n"
    _, headers, body = _get(f"{live_server}/api/drive/raw?path=/Documents/notes.txt&download=1")
    assert body == b"hello" and "attachment" in headers.get("Content-Disposition", "")
    with pytest.raises(urllib.error.HTTPError) as ei:
        _get(f"{live_server}/api/drive/file?path=/../../etc/passwd")
    assert ei.value.code == 403


def test_drive_endpoints_refused_on_railway(live_server, monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    _, _, body = _get(f"{live_server}/api/drive/status")
    assert json.loads(body)["available"] is False
    with pytest.raises(urllib.error.HTTPError) as ei:
        _get(f"{live_server}/api/drive/mirror")
    assert ei.value.code == 403


def test_ui_has_drive_mirror_and_split():
    from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI as H
    for token in ('id="drivePlacesList"', 'id="rangerSplitter"', 'id="rangerListPane"', 'id="rangerViewerPane"',
                  'id="finderViewer"', "gatherDriveMirror('login')", "gatherDriveMirror('session-start')",
                  'tincan_ranger_list_pct', 'arrow keys to navigate'):
        assert token in H, token
    # The old hard-coded fake "places" are gone.
    assert "navigateFinderPath('/media/videos')" not in H
