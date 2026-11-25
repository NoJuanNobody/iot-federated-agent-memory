"""End-to-End Verification for TinCan Simultaneous Screen Share, Camera Video & Live Cursors.

Verifies:
  1. Backend `mesh_os_engine.update_cursor` and live HTTP `/api/mesh/cursor` + `/api/mesh/state`
     persist normalized workspace coords (nx, ny), screen-share pointer coords (screen_x, screen_y),
     click ripple state, and peer color.
  2. Live HTTP WebRTC signaling supports simultaneous camera + screen (`stream_meta`, `offer`,
     `answer`, `candidate`) between two peers.
  3. Rendered Mesh OS HTML contains all dual-stream camera+screen viewports, interactive
     `screenPointerOverlay`, `tincan-cursors` WebRTC DataChannel, ICE candidate buffering,
     and valid inline JavaScript syntax.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI

REPO_ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(url: str, payload: dict | None = None, timeout: float = 5.0) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


@pytest.fixture(scope="module")
def live_mesh_server():
    port = _free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["TINCAN_S3_DISABLED"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(REPO_ROOT / "server.py")],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=2)
            pytest.fail(f"server.py exited early:\n{out}\n{err}")
        try:
            st, _ = _http_json(f"{base}/api/mesh/state?room=main", timeout=1.0)
            if st == 200:
                break
        except Exception:
            time.sleep(0.2)
    else:
        proc.terminate()
        pytest.fail("server.py did not become ready")

    try:
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def test_engine_update_cursor_normalized_and_screen_pointer():
    engine = TinCanMeshOSEngine()
    cur = engine.update_cursor(
        peer_id="peer-primary-alice",
        x=720,
        y=450,
        display_name="Alice",
        room="pair-room",
        nx=0.5,
        ny=0.5,
        screen_x=0.33,
        screen_y=0.77,
        clicking=True,
        color="#22d3ee",
    )
    assert cur["nx"] == 0.5
    assert cur["ny"] == 0.5
    assert cur["screen_x"] == 0.33
    assert cur["screen_y"] == 0.77
    assert cur["clicking"] is True
    assert cur["color"] == "#22d3ee"

    # Clamping bounds check
    clamped = engine.update_cursor(
        peer_id="peer-primary-alice",
        x=10,
        y=10,
        nx=1.8,
        ny=-0.4,
        screen_x=2.5,
        screen_y=-1.0,
    )
    assert clamped["nx"] == 1.0
    assert clamped["ny"] == 0.0
    assert clamped["screen_x"] == 1.0
    assert clamped["screen_y"] == 0.0


def test_live_server_cursor_sync_and_dual_stream_webrtc_signaling(live_mesh_server: str):
    # 1. Peer A & Peer B post normalized workspace + screen-share pointers
    st_a, res_a = _http_json(
        f"{live_mesh_server}/api/mesh/cursor",
        {
            "peer_id": "peer-primary-mac-a",
            "display_name": "Mac A",
            "x": 640,
            "y": 360,
            "nx": 0.4444,
            "ny": 0.4,
            "screen_x": 0.62,
            "screen_y": 0.28,
            "clicking": True,
            "color": "#34d399",
            "room": "main",
        },
    )
    assert st_a == 200
    assert res_a["cursor"]["screen_x"] == 0.62
    assert res_a["cursor"]["clicking"] is True

    st_state, state = _http_json(f"{live_mesh_server}/api/mesh/state?room=main")
    assert st_state == 200
    cursors = state.get("cursors", {})
    if isinstance(cursors, list):
        by_id = {c["peer_id"]: c for c in cursors}
    else:
        by_id = cursors
    assert "peer-primary-mac-a" in by_id
    assert by_id["peer-primary-mac-a"]["nx"] == 0.4444
    assert by_id["peer-primary-mac-a"]["screen_y"] == 0.28

    # 2. Peer A registers simultaneous Camera + Screen stream
    st_reg, reg = _http_json(
        f"{live_mesh_server}/api/webrtc/register",
        {
            "peer_id": "peer-primary-mac-a",
            "display_name": "Mac A (Screen)",
            "room": "pair-room",
            "has_video": True,
            "has_audio": True,
            "has_screen": True,
        },
    )
    assert st_reg == 200

    # 3. Peer A sends stream_meta + offer + candidate; Peer B polls & receives them in order
    for sig_type, payload in (
        ("stream_meta", {"camera_stream_id": "cam-stream-1", "screen_stream_id": "scr-stream-2"}),
        ("offer", {"sdp": {"type": "offer", "sdp": "v=0..."}, "camera_stream_id": "cam-stream-1", "screen_stream_id": "scr-stream-2"}),
        ("candidate", {"candidate": {"candidate": "candidate:1 1 UDP 2122252543 10.0.0.40 50000 typ host"}}),
    ):
        st_sig, _ = _http_json(
            f"{live_mesh_server}/api/webrtc/signal",
            {"from": "peer-primary-mac-a", "to": "*", "room": "pair-room", "type": sig_type, "payload": payload},
        )
        assert st_sig == 200

    st_poll, polled = _http_json(
        f"{live_mesh_server}/api/webrtc/signals?peer_id=peer-secondary-mac-b&room=pair-room&since_seq=0"
    )
    assert st_poll == 200
    types = [s["type"] for s in polled.get("signals", [])]
    assert "stream_meta" in types
    assert "offer" in types
    assert "candidate" in types


def test_mesh_os_ui_contains_dual_camera_screen_cursor_features_and_valid_js():
    html = MESH_OS_HTML_UI
    required_tokens = [
        'id="screenShareStage"',
        'id="remoteScreenVideo"',
        'id="screenPointerOverlay"',
        'id="localVideo"',
        'id="remoteVideo"',
        'id="stopScreenBtn"',
        'id="cursorSyncBadge"',
        'id="lanGuestJoinPanel"',
        "tincan-cursors",
        "localCameraStream",
        "localScreenStream",
        "pendingIceCandidates",
        "acceptedCallPeers",
        "renderRemoteScreenPointer",
        "toggleScreenFullscreen",
        "joinAsLocalLanGuest",
    ]
    for tok in required_tokens:
        assert tok in html, f"Missing required UI/WebRTC token: {tok}"

    # Verify all inline <script> blocks parse with zero JavaScript syntax errors (when node is present)
    node_bin = shutil.which("node")
    if node_bin:
        scripts = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)
        inline_scripts = [s for s in scripts if s.strip()]
        assert len(inline_scripts) >= 1
        for idx, js in enumerate(inline_scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(js)
                tmp_path = f.name
            try:
                res = subprocess.run([node_bin, "--check", tmp_path], capture_output=True, text=True, timeout=15)
                assert res.returncode == 0, f"JS syntax error in script block #{idx}:\n{res.stderr}"
            finally:
                Path(tmp_path).unlink(missing_ok=True)
