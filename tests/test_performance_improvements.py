"""Tests for Railway metrics & HTTP performance optimizations."""

import gzip
import http.client
import json
import os
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import pytest

import server
from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter


@pytest.fixture(scope="module")
def perf_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield ("127.0.0.1", port)
    httpd.shutdown()


def test_http11_gzip_and_etag_on_html_ui(perf_server):
    host, port = perf_server
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/os", headers={"Accept-Encoding": "gzip"})
    resp = conn.getresponse()
    body = resp.read()
    assert resp.status == 200
    assert resp.version == 11  # HTTP/1.1
    assert resp.getheader("Content-Encoding") == "gzip"
    assert int(resp.getheader("Content-Length")) == len(body)
    etag = resp.getheader("ETag")
    assert etag is not None

    decompressed = gzip.decompress(body).decode("utf-8")
    assert "TinCan Mesh OS" in decompressed
    assert len(body) < len(decompressed.encode("utf-8")) // 2

    # Second request on same keep-alive connection with If-None-Match -> 304 Not Modified
    conn.request("GET", "/os", headers={"If-None-Match": etag})
    resp304 = conn.getresponse()
    body304 = resp304.read()
    assert resp304.status == 304
    assert body304 == b""
    conn.close()


def test_head_requests_do_not_write_body(perf_server):
    host, port = perf_server
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request("HEAD", "/api/status")
    resp = conn.getresponse()
    body = resp.read()
    assert resp.status == 200
    assert int(resp.getheader("Content-Length")) > 50
    assert body == b""
    conn.close()


def test_unified_mesh_sync_endpoint_and_json_gzip(perf_server):
    host, port = perf_server
    conn = http.client.HTTPConnection(host, port, timeout=5)
    conn.request(
        "GET",
        "/api/mesh/sync?room=main&peer_id=peer-primary-mac&since_seq=0&include_analytics=1",
        headers={"Accept-Encoding": "gzip"},
    )
    resp = conn.getresponse()
    raw_body = resp.read()
    assert resp.status == 200
    assert resp.getheader("Content-Encoding") == "gzip"
    data = json.loads(gzip.decompress(raw_body).decode("utf-8"))
    assert "state" in data
    assert "signals" in data
    assert "analytics" in data
    assert "xp" in data["state"]
    conn.close()


def test_cached_commit_hash_in_version_endpoint(perf_server):
    host, port = perf_server
    with patch("subprocess.check_output", side_effect=AssertionError("git should not be spawned per request")):
        with urllib.request.urlopen(f"http://{host}:{port}/api/version") as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            assert payload["service"] == "tincan"
            assert payload["commit"] == server.COMMIT_HASH


def test_stale_while_revalidate_openrouter_billing():
    router = DynamicAIGatewayRouter(openrouter_key="sk-or-test")
    router._billing_cache = {
        "connected": True,
        "account_total_credits_usd": 25.0,
        "account_total_usage_usd": 5.0,
        "account_remaining_balance_usd": 20.0,
        "fetched_at": time.time() - 120.0,
    }
    router._billing_cached_at = time.time() - 120.0  # Expired (>60s TTL)

    called_bg = threading.Event()

    def slow_fetch(api_key):
        called_bg.set()
        return router._billing_cache

    with patch.object(router, "_fetch_openrouter_billing_sync", side_effect=slow_fetch):
        t0 = time.monotonic()
        res = router.get_openrouter_billing(force_refresh=False)
        elapsed = time.monotonic() - t0
        assert elapsed < 0.05
        assert res["account_remaining_balance_usd"] == 20.0
        assert called_bg.wait(timeout=1.0)


def test_account_registry_volume_env_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_vol:
        monkeypatch.setenv("TINCAN_DATA_DIR", tmp_vol)
        reg = PeerAccountRegistry()
        assert reg.db_path == os.path.join(tmp_vol, "peer_accounts.db")
        acc = reg.register_account("vol-peer-1", "Vol User", "+15615550199", "vol@fau.edu")
        assert acc["peer_id"] == "vol-peer-1"


def test_server_side_mandatory_identity_gate_blocks_unidentified_peers(perf_server):
    host, port = perf_server
    conn = http.client.HTTPConnection(host, port, timeout=5)

    # 1. Unidentified default-* CLI node is rejected with 403
    conn.request(
        "POST",
        "/api/webrtc/register",
        body=json.dumps({"peer_id": "default-1234abcd", "display_name": "default (1234abcd)", "room": "lab-room"}),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 403
    assert body.get("require_identity") is True

    # 2. Unidentified browser cursor (peer-xxxx with no real name/account) is rejected with 403
    conn.request(
        "POST",
        "/api/mesh/cursor",
        body=json.dumps({"peer_id": "peer-anon99", "display_name": "peer-anon99", "x": 50, "y": 50, "room": "main"}),
        headers={"Content-Type": "application/json"},
    )
    resp2 = conn.getresponse()
    body2 = json.loads(resp2.read().decode("utf-8"))
    assert resp2.status == 403
    assert body2.get("require_identity") is True

    # 3. Identified operator is allowed in both cursor and WebRTC room
    conn.request(
        "POST",
        "/api/webrtc/register",
        body=json.dumps({"peer_id": "peer-alex01", "display_name": "Alejandro Londono (@alex_londono)", "room": "main"}),
        headers={"Content-Type": "application/json"},
    )
    resp3 = conn.getresponse()
    body3 = json.loads(resp3.read().decode("utf-8"))
    assert resp3.status == 200
    assert body3["display_name"] == "Alejandro Londono (@alex_londono)"
    conn.close()

