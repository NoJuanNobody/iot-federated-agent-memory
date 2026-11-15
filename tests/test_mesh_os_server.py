"""Integration tests for TinCan Mesh OS UI and HTTP routes in server.py."""

import json
import threading
import urllib.error
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


def test_terminal_ai_redesign_routes_and_telemetry_endpoints(live_mesh_server):
    # Single-window routes for AI Copilot, AI Home Hub, and Token Vault
    route_markers = [
        ("/copilot", 'id="win-copilot"', "singleWindowParam = 'win-copilot'"),
        ("/ai", 'id="win-ai-home"', "id=\"aiHomeHub\""),
        ("/home", 'id="win-ai-home"', "id=\"aiHomeHub\""),
        ("/tokens", 'id="win-billing"', "billingWindowTokens"),
    ]
    for route, marker_a, marker_b in route_markers:
        with urllib.request.urlopen(f"{live_mesh_server}{route}") as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert marker_a in html
            assert marker_b in html

    # Gateway telemetry + pre-flight local zero-burn endpoint
    with urllib.request.urlopen(
        f"{live_mesh_server}/api/gateway/telemetry?model=ollama/qwen2.5:3b&prompt_chars=400"
    ) as resp:
        assert resp.status == 200
        gw_data = json.loads(resp.read().decode("utf-8"))
        assert "gateways" in gw_data and len(gw_data["gateways"]) >= 4
        assert "arbitrage" in gw_data
        assert gw_data["preflight"]["estimated_credits"] == 0
        assert gw_data["preflight"]["is_zero_burn"] is True

    # Token summary + unit economics ledger endpoint
    with urllib.request.urlopen(f"{live_mesh_server}/api/tokens/summary") as resp:
        assert resp.status == 200
        tok_data = json.loads(resp.read().decode("utf-8"))
        assert "credits_balance" in tok_data
        assert "rate_card" in tok_data and len(tok_data["rate_card"]) == 4
        assert "daily_ad_cap" in tok_data
        assert "ledger_rows" in tok_data
        assert "rodin" in tok_data


def test_network_no_seed_peers_and_quests_admin_mint_and_home_auto_earn(live_mesh_server, monkeypatch):
    # 1. Server must NOT pre-seed fake Mac Studio / Collaborator Node streams
    with urllib.request.urlopen(f"{live_mesh_server}/api/mesh/state?room=main") as resp:
        state = json.loads(resp.read().decode("utf-8"))
        stream_ids = {p.get("peer_id") for p in state["active_webrtc_streams"]}
        assert "peer-primary-mac" not in stream_ids
        assert "peer-secondary-node" not in stream_ids

    # 2. UI merges network tabs/stats cleanly, supports Ping/Message on visitors & peers,
    # removes hardcoded fallback peer strings, and gently routes Arena & Leaderboard in Quests
    for marker in (
        'id="netMessageDrawer"',
        "pingNetworkPeer(",
        "openPeerMessage(",
        'id="mintRequestDrawer"',
        'id="questsAdminMintCard"',
        "openAddMoneyFromQuests()",
        'id="questsArenaDisclosure"',
        'id="questsLeaderboardDisclosure"',
        "startHomeSponsoredAd(",
        "completeHomeSponsoredAd(",
    ):
        assert marker in MESH_OS_HTML_UI, f"Missing expected updated marker: {marker}"

    for stale_seed in (
        "Mac Studio (M1 Max)",
        "Collaborator MacBook",
        "Active WebRTC Stream",
        "24ms RTT",
        "mintedRewardBalance +=",
    ):
        assert stale_seed not in MESH_OS_HTML_UI, f"Found stale hardcoded marker: {stale_seed}"

    # 3. Sign-on onboarding quests award XP at most once per peer
    q_peer = "peer-signon-once"
    for expected_status, expected_xp in (("awarded", 100), ("already_completed", 0)):
        q_req = urllib.request.Request(
            f"{live_mesh_server}/api/mesh/quest",
            data=json.dumps({"peer_id": q_peer, "action_key": "sealed_courier"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(q_req) as resp:
            q_data = json.loads(resp.read().decode("utf-8"))
            assert q_data["status"] == expected_status
            assert q_data["signon_only"] is True
            assert q_data["award"]["awarded_xp"] == expected_xp

    # 4. Mint Request queue + Admin-only credit routing
    req_peer = "peer-mint-req"
    cust_peer = "peer-mint-cust"
    for pid, name in ((req_peer, "Requester Peer"), (cust_peer, "Customer Peer")):
        reg = urllib.request.Request(
            f"{live_mesh_server}/api/account/register",
            data=json.dumps({
                "peer_id": pid,
                "full_name": name,
                "email": f"{pid}@fau.edu",
                "phone_number": "+15615550101",
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(reg) as r:
            assert r.status == 201

    with urllib.request.urlopen(f"{live_mesh_server}/api/account/billing?peer_id={cust_peer}") as resp:
        bal_initial = json.loads(resp.read().decode("utf-8"))["token_balance"]

    mreq = urllib.request.Request(
        f"{live_mesh_server}/api/tokens/mint-request",
        data=json.dumps({
            "peer_id": req_peer,
            "target_peer_id": cust_peer,
            "tokens": 250,
            "reason": "Route welcome grant to customer",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(mreq) as resp:
        assert resp.status == 201
        m_data = json.loads(resp.read().decode("utf-8"))
        assert m_data["status"] == "pending_admin_approval"
        req_id = m_data["request"]["id"]

    # Requesting mint must NOT change the customer balance before admin approval
    with urllib.request.urlopen(f"{live_mesh_server}/api/account/billing?peer_id={cust_peer}") as resp:
        bal_before = json.loads(resp.read().decode("utf-8"))["token_balance"]
        assert bal_before == bal_initial

    # Non-admin resolution attempt fails 403
    monkeypatch.setattr(server, "TINCAN_ADMIN_KEY", "test-secret-admin-key")
    bad_resolve = urllib.request.Request(
        f"{live_mesh_server}/api/tokens/mint-requests/resolve",
        data=json.dumps({"request_id": req_id, "decision": "approve"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(bad_resolve)
    assert exc.value.code == 403

    # Valid Admin Key approves & routes tokens to target customer peer
    good_resolve = urllib.request.Request(
        f"{live_mesh_server}/api/tokens/mint-requests/resolve",
        data=json.dumps({"request_id": req_id, "decision": "approve"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Admin-Key": "test-secret-admin-key"},
        method="POST",
    )
    with urllib.request.urlopen(good_resolve) as resp:
        assert resp.status == 200
        res_data = json.loads(resp.read().decode("utf-8"))
        assert res_data["status"] == "approved"
        assert res_data["account"]["token_balance"] == bal_initial + 250
