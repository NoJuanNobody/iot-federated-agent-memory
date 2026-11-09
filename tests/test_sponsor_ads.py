"""Unit & Integration tests for Sponsor Ads and Rewarded Token Top-Up."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.sponsor_ads import SponsorAdManager, SponsorCreative


@pytest.fixture(scope="module")
def live_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def test_sponsor_ad_manager_rotation_and_clicks():
    mgr = SponsorAdManager()
    s1 = mgr.get_sponsor()
    s2 = mgr.get_sponsor()
    assert s1["id"] != s2["id"]

    # Target specific sponsor
    railway = mgr.get_sponsor("railway")
    assert railway["id"] == "railway"
    assert "Railway" in railway["name"]
    assert railway["reward_tokens"] == 5000

    # Record click
    assert mgr.record_click("railway") is True
    assert mgr.clicks.get("railway", 0) >= 1

    # Record completion
    comp = mgr.record_completion("railway")
    assert comp["status"] == "verified"
    assert comp["reward_tokens"] == 5000
    assert mgr.completions.get("railway", 0) >= 1


def test_sponsor_sync_from_playlist():
    mgr = SponsorAdManager()
    items = [
        {"id": "v1", "video_id": "111", "title": "Regular Video", "category": "spotlight"},
        {"id": "v2", "video_id": "222", "title": "Sponsor Video", "creator": "@partner", "category": "ad", "embed_url": "/videos/222.mp4"},
    ]
    added = mgr.sync_from_playlist(items)
    assert added == 1

    ad_sponsor = mgr.get_sponsor("video-222")
    assert ad_sponsor["id"] == "video-222"
    assert ad_sponsor["name"] == "Sponsor Video"
    assert ad_sponsor["video_url"] == "/videos/222.mp4"


def test_http_sponsor_endpoints(live_server):
    # 1. GET /api/ads/sponsor
    with urllib.request.urlopen(f"{live_server}/api/ads/sponsor") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "sponsor" in data
        assert "networks" in data
        assert "ethical_ads" in data["networks"]
        assert "google_adsense" in data["networks"]

    # 2. GET /api/ads/sponsor?id=railway
    with urllib.request.urlopen(f"{live_server}/api/ads/sponsor?id=railway") as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data["sponsor"]["id"] == "railway"

    # 3. POST /api/ads/click
    req = urllib.request.Request(
        f"{live_server}/api/ads/click",
        data=json.dumps({"sponsor_id": "railway"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "ok"
        assert res["recorded"] is True

    # 4. Register peer account before topup
    peer_id = "peer-sponsor-test"
    reg_req = urllib.request.Request(
        f"{live_server}/api/account/register",
        data=json.dumps({
            "peer_id": peer_id,
            "full_name": "Sponsor Test Peer",
            "email": f"{peer_id}@fau.edu",
            "phone_number": "+15615551234",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(reg_req) as reg_resp:
        assert reg_resp.status == 201

    # 5. POST /api/account/billing/topup with sponsor_id
    req2 = urllib.request.Request(
        f"{live_server}/api/account/billing/topup",
        data=json.dumps({
            "peer_id": peer_id,
            "tokens": 5000,
            "amount_usd": 0.05,
            "sponsor_id": "railway"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req2) as resp:
        assert resp.status == 200
        res2 = json.loads(resp.read().decode("utf-8"))
        assert res2["status"] == "topup_success"
        assert res2["account"]["token_balance"] >= 55000
