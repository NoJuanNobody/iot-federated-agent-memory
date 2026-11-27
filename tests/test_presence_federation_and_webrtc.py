"""Tests for Split-Plane Local Space + Shared Relay Presence, Talk Roster, and WebRTC Signaling."""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server as srv
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.tui import status_summary


def _start_test_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.MeshGatewayHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, f"http://127.0.0.1:{port}"


def _req_json(url: str, method: str = "GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_unified_online_peers_merges_webrtc_and_cursors(monkeypatch):
    monkeypatch.delenv("TINCAN_LOCAL_NODE", raising=False)
    monkeypatch.delenv("TINCAN_UPSTREAM_RELAY", raising=False)

    httpd, base = _start_test_server()
    try:
        # Peer A registers via WebRTC with screen share
        st, _ = _req_json(
            f"{base}/api/webrtc/register",
            method="POST",
            payload={
                "peer_id": "peer-test-alpha",
                "display_name": "Alpha Operator",
                "room": "main",
                "has_video": True,
                "has_audio": True,
                "has_screen": True,
            },
        )
        assert st == 200

        # Peer B sends a live cursor heartbeat only (no WebRTC call yet)
        st, _ = _req_json(
            f"{base}/api/mesh/cursor",
            method="POST",
            payload={
                "peer_id": "peer-test-beta",
                "display_name": "Beta Visitor",
                "room": "main",
                "x": 120,
                "y": 240,
                "window_id": "win-call",
            },
        )
        assert st == 200

        # /api/mesh/state must include both peers in online_peers & peers map
        st, state = _req_json(f"{base}/api/mesh/state?room=main")
        assert st == 200
        assert "online_peers" in state
        assert "peers" in state
        assert state["peers_count"] >= 2
        ids = {p["peer_id"] for p in state["online_peers"]}
        assert "peer-test-alpha" in ids
        assert "peer-test-beta" in ids
        assert "peer-test-alpha" in state["peers"]
        assert "peer-test-beta" in state["peers"]
        assert state["peers"]["peer-test-alpha"]["has_screen"] is True

        # /api/status must also report unified online_peers for the TUI
        st, status_data = _req_json(f"{base}/api/status")
        assert st == 200
        status_ids = {p["peer_id"] for p in status_data.get("online_peers", [])}
        assert "peer-test-alpha" in status_ids
        assert "peer-test-beta" in status_ids
    finally:
        srv.relay.leave_peer("peer-test-alpha")
        with srv.mesh_os._lock:
            srv.mesh_os.cursors.pop("peer-test-beta", None)
        httpd.shutdown()
        httpd.server_close()


def test_local_node_proxies_shared_comms_but_keeps_spaces_local(monkeypatch):
    # Spin up a fake upstream relay server (same handler, non-local mode)
    monkeypatch.delenv("TINCAN_LOCAL_NODE", raising=False)
    monkeypatch.delenv("TINCAN_UPSTREAM_RELAY", raising=False)

    # Verify routing classifier directly:
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/mesh/state") is True
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/webrtc/register") is True
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/webrtc/signal") is True
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/webrtc/signals") is True
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/mesh/cursor") is True
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/board/topics") is True

    # Personal spaces & local workstation MUST remain local!
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/spaces") is False
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/space/ls") is False
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/space/file") is False
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/local/identity") is False
    assert srv.MeshGatewayHandler._should_proxy_to_upstream("/api/workstation/status") is False


def test_mesh_os_ui_presence_and_late_joiner_hooks():
    html = MESH_OS_HTML_UI
    assert "registerPresenceHeartbeat" in html
    assert "joinPeerStream" in html
    assert "request_offer" in html
    assert "st && st.online_peers" in html
    assert "online: !!u.verified" not in html


def test_tui_status_summary_counts_online_peers():
    snap = {
        "data": {
            "online_peers": [
                {"peer_id": "a", "display_name": "Alice"},
                {"peer_id": "b", "display_name": "Bob"},
            ],
            "active_webrtc_streams": [],
            "ai_providers": {"openrouter": 10},
        },
        "error": None,
    }
    label, _ = status_summary(snap, is_local=True)
    assert "2 peers" in label
