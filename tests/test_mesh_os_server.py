"""Integration tests for TinCan Mesh OS UI and HTTP routes in server.py."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI


@pytest.fixture(scope="module")
def live_mesh_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def test_mesh_os_html_ui_invariants():
    for token in (
        'data-cmd="npx"',
        'data-cmd="chat"',
        'id="tv"',
        'id="relayNativeVideo"',
        'id="nowPlayingTitle"',
        'id="playlistCounterBadge"',
        'id="playlistQueue"',
        'id="newVideoInput"',
        'id="autoRotateBtn"',
        'id="soundToggleBtn"',
        'id="providerCards"',
        'id="analyticsHeader"',
        'id="aliasSelect"',
        'id="modelInput"',
        'id="updateFeedback"',
        'id="call"',
        'id="roomInput"',
        'id="callStatusBadge"',
        'id="localVideo"',
        'id="remoteVideo"',
        'id="localPeerLabel"',
        'id="remotePeerLabel"',
        'id="roomPeersGrid"',
        'id="muteBtn"',
        'id="camBtn"',
        'id="osTierBadge"',
        'id="osXpBar"',
        'id="meshTopologyCanvas"',
        'id="multiplayerCursorsLayer"',
        'id="questDeckGrid"',
        'id="arenaBattleBox"',
        'id="operatorLeaderboard"',
        'id="currentTargetModelBadge"',
        "syncSelectedAliasModel",
        "quickPickModel",
        "BroadcastChannel",
        "openPopoutWindow",
        'id="win-billing"',
        'id="dockBtn-win-billing"',
        'id="watchAdBtn"',
        'id="accountSetupModal"',
        'id="hudAccountBtn"',
        'id="accInputUsername"',
        'syncDockIndicators',
        'minimizeWindow',
        'popout-fullscreen',
        'WINDOW_POPOUT',
        'WINDOW_REDOCK',
        'id="win-network"',
        'id="operatorLeaderboardStandalone"',
        'id="btnLayoutTile2x2"',
        'id="btnLayoutSplit"',
        'id="btnLayoutFree"',
        'setDesktopLayout',
        'switchNetTab',
        'dockBtn-win-network',
        'id="netMetricPeers"',
        'id="netMetricVisitors"',
        'id="netWinActiveNum"',
        'startDirectCall',
    ):
        assert token in MESH_OS_HTML_UI, f"Missing expected UI token: {token}"


def test_mesh_os_inline_javascript_syntax():
    import re
    import shutil
    import subprocess
    import tempfile

    scripts = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", MESH_OS_HTML_UI, re.S)
    assert len(scripts) >= 1
    if shutil.which("node"):
        for script in scripts:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(script)
                fname = f.name
            res = subprocess.run(["node", "--check", fname], capture_output=True, text=True)
            assert res.returncode == 0, f"Inline JS syntax error:\n{res.stderr}"


def test_model_swap_reflects_in_analytics(live_mesh_server):
    req = urllib.request.Request(
        f"{live_mesh_server}/api/models/set",
        data=json.dumps({"alias": "gemini-brain", "model": "google/gemini-2.5-pro"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "updated"
        assert res["alias"] == "gemini-brain"
        assert res["model"] == "google/gemini-2.5-pro"

    with urllib.request.urlopen(f"{live_mesh_server}/api/models/analytics") as resp:
        analytics = json.loads(resp.read().decode("utf-8"))
        assert analytics["providers"]["gemini-brain"]["model"] == "google/gemini-2.5-pro"


def test_mesh_os_http_endpoints(live_mesh_server):
    # 1. GET /os and /mesh return HTML_UI
    for route in ("/os", "/mesh"):
        with urllib.request.urlopen(f"{live_mesh_server}{route}") as resp:
            html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "TinCan Mesh OS" in html

    # 2. GET /api/mesh/state
    with urllib.request.urlopen(f"{live_mesh_server}/api/mesh/state?room=main") as resp:
        state = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200
        assert "xp" in state
        assert "tier" in state
        assert "quests" in state
        assert "leaderboard" in state
        assert "active_webrtc_streams" in state

    # 3. POST /api/mesh/cursor
    req = urllib.request.Request(
        f"{live_mesh_server}/api/mesh/cursor",
        data=json.dumps({"peer_id": "peer-test-1", "x": 320, "y": 240, "room": "main"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "ok"
        assert res["cursor"]["x"] == 320.0

    # 4. POST /api/mesh/react
    req = urllib.request.Request(
        f"{live_mesh_server}/api/mesh/react",
        data=json.dumps({"peer_id": "peer-test-1", "emoji": "🥫"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "reacted"
        assert res["reaction"]["emoji"] == "🥫"

    # 5. POST /api/mesh/quest
    req = urllib.request.Request(
        f"{live_mesh_server}/api/mesh/quest",
        data=json.dumps({"peer_id": "peer-test-1", "action_key": "sealed_courier"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "awarded"
        assert res["award"]["awarded_xp"] == 100

    # 6. POST /api/mesh/arena/vote
    req = urllib.request.Request(
        f"{live_mesh_server}/api/mesh/arena/vote",
        data=json.dumps({"peer_id": "peer-test-1", "winner_alias": "gemini-brain", "prompt_preview": "test"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "voted"
        assert res["winner_alias"] == "gemini-brain"
        assert res["xp_awarded"] == 150
