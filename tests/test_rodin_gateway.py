"""Unit tests for Hyper3D Rodin v2 3D Generative AI Gateway, GLB generator, and billing."""

import base64
import json
import os
import struct
from unittest.mock import MagicMock, patch

import pytest

from iot_federated_agent_memory.ai_gateway import (
    DynamicAIGatewayRouter,
    _resolve_hyper3d_key_fallback,
    generate_minimal_glb_bytes,
)
from iot_federated_agent_memory.sponsor_ads import (
    DEFAULT_SPONSORS,
    SponsorAd,
    SponsorAdManager,
    SponsorCreative,
)


def test_generate_minimal_glb_bytes():
    """Verify that generate_minimal_glb_bytes produces a valid binary glTF 2.0 buffer."""
    glb = generate_minimal_glb_bytes("test_mesh")
    assert isinstance(glb, bytes)
    assert glb.startswith(b"glTF"), "Must start with magic header b'glTF'"

    # Header check: magic, version, length
    magic, version, total_length = struct.unpack_from("<4sII", glb, 0)
    assert magic == b"glTF"
    assert version == 2
    assert total_length == len(glb)

    # Chunk 0: JSON chunk
    json_len, json_type = struct.unpack_from("<II", glb, 12)
    assert json_type == 0x4E4F534A, "Chunk 0 must be JSON (0x4E4F534A)"
    json_data = json.loads(glb[20 : 20 + json_len].decode("utf-8"))
    assert json_data["asset"]["version"] == "2.0"
    assert json_data["asset"]["generator"] == "Hyper3D Rodin Gateway"
    assert len(json_data["meshes"]) == 1
    assert json_data["meshes"][0]["primitives"][0]["attributes"]["POSITION"] == 1

    # Chunk 1: BIN chunk
    bin_header_offset = 20 + json_len
    # Pad alignment to 4 bytes if needed
    if bin_header_offset % 4 != 0:
        bin_header_offset += 4 - (bin_header_offset % 4)

    bin_len, bin_type = struct.unpack_from("<II", glb, bin_header_offset)
    assert bin_type == 0x004E4942, "Chunk 1 must be BIN (0x004E4942)"
    bin_data = glb[bin_header_offset + 8 : bin_header_offset + 8 + bin_len]
    assert len(bin_data) >= 36, "BIN chunk must contain position vectors"


def test_resolve_hyper3d_key_fallback(monkeypatch):
    """Verify environment variable fallback resolution."""
    monkeypatch.delenv("HYPER3D_API_KEY", raising=False)
    monkeypatch.delenv("RODIN_API_KEY", raising=False)
    assert _resolve_hyper3d_key_fallback() is None

    monkeypatch.setenv("HYPER3D_API_KEY", "h3d-secret-token")
    assert _resolve_hyper3d_key_fallback() == "h3d-secret-token"

    monkeypatch.delenv("HYPER3D_API_KEY", raising=False)
    monkeypatch.setenv("RODIN_API_KEY", "rodin-fallback-token")
    assert _resolve_hyper3d_key_fallback() == "rodin-fallback-token"


def test_rodin_endpoints_and_tier_costs():
    """Verify router constants for Rodin endpoints and tier pricing."""
    router = DynamicAIGatewayRouter()
    assert router.RODIN_GENERATE_URL == "https://api.hyper3d.com/api/v2/rodin"
    assert router.RODIN_STATUS_URL == "https://api.hyper3d.com/api/v2/status"
    assert router.RODIN_DOWNLOAD_URL == "https://api.hyper3d.com/api/v2/download"
    assert router.RODIN_BALANCE_URL == "https://api.hyper3d.com/api/v2/check_balance"
    assert router.RODIN_TIER_COSTS == {
        "Regular": 0.50,
        "Sketch": 0.25,
        "Detail": 1.00,
        "Smooth": 0.75,
    }


def test_get_hyper3d_billing_offline(monkeypatch):
    """Verify billing status returns structured offline response when no key is configured."""
    monkeypatch.delenv("HYPER3D_API_KEY", raising=False)
    monkeypatch.delenv("RODIN_API_KEY", raising=False)
    router = DynamicAIGatewayRouter(hyper3d_key=None)

    billing = router.get_hyper3d_billing()
    assert billing["connected"] is False
    assert billing["provider"] == "Hyper3D Rodin (Ronin) v2"
    assert billing["endpoint"] == router.RODIN_GENERATE_URL
    assert billing["account_remaining_credits"] == 0.0
    assert billing["account_remaining_balance_usd"] == 0.0
    assert billing["session_total_tasks"] == 0
    assert billing["session_total_spend_usd"] == 0.0
    assert billing["key_label"] == "not_configured"
    assert billing["tier_pricing_usd"]["Regular"] == 0.50


def test_get_hyper3d_billing_connected():
    """Verify billing status with simulated live API key response and caching."""
    router = DynamicAIGatewayRouter(hyper3d_key="test-rodin-key")

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "credits": 142.50,
        "balance_usd": 71.25,
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        billing = router.get_hyper3d_billing(force_refresh=True)
        assert billing["connected"] is True
        assert billing["account_remaining_credits"] == 142.50
        assert billing["account_remaining_balance_usd"] == 71.25
        assert billing["key_label"] == "pooled-rodin-key [redacted]"

    # Second call uses stale-while-revalidate cache without hitting urlopen
    cached_billing = router.get_hyper3d_billing(force_refresh=False)
    assert cached_billing["connected"] is True
    assert cached_billing["account_remaining_credits"] == 142.50


def test_dispatch_rodin_generation_simulated(monkeypatch):
    """Verify offline 3D generation dispatch returns valid task receipt with GLB payload."""
    monkeypatch.delenv("HYPER3D_API_KEY", raising=False)
    monkeypatch.delenv("RODIN_API_KEY", raising=False)
    router = DynamicAIGatewayRouter(hyper3d_key=None)

    task = router.dispatch_rodin_generation(
        prompt="Cyberpunk flying drone quadcopter",
        tier="Detail",
        geometry_file_format="glb",
        mesh_mode="Quad",
    )

    assert task["uuid"].startswith("rodin-")
    assert task["subscription_key"].startswith("sub-")
    assert task["prompt"] == "Cyberpunk flying drone quadcopter"
    assert task["tier"] == "Detail"
    assert task["format"] == "glb"
    assert task["mesh_mode"] == "Quad"
    assert task["status"] == "Done"
    assert task["cost_usd"] == 1.00
    assert task["simulated"] is True
    assert task["created_at"] > 0

    # Ensure GLB is valid
    glb_bytes = base64.b64decode(task["glb_bytes_b64"])
    assert glb_bytes.startswith(b"glTF")

    # Ensure session counters incremented
    assert router.rodin_total_calls == 1
    assert router.rodin_total_cost_usd == 1.00
    assert task["uuid"] in router.rodin_tasks


def test_dispatch_rodin_generation_mock_live():
    """Verify live API dispatch parses response correctly and handles network error gracefully."""
    router = DynamicAIGatewayRouter(hyper3d_key="sk-live-rodin")

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "uuid": "live-mesh-456",
        "subscription_key": "sub-live-789",
        "status": "Processing",
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        task = router.dispatch_rodin_generation(
            prompt="Alien crystal monolith",
            tier="Regular",
        )
        assert task["uuid"] == "live-mesh-456"
        assert task["subscription_key"] == "sub-live-789"
        assert task["status"] == "Processing"
        assert task["cost_usd"] == 0.50
        assert task["simulated"] is False

    # Graceful fallback on network error
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        task_fallback = router.dispatch_rodin_generation(
            prompt="Obsidian obelisk",
            tier="Sketch",
        )
        assert task_fallback["status"] == "Done"
        assert task_fallback["simulated"] is True
        assert task_fallback["cost_usd"] == 0.25


def test_check_rodin_status():
    """Verify check_rodin_status retrieves task state."""
    router = DynamicAIGatewayRouter(hyper3d_key=None)
    task = router.dispatch_rodin_generation("Tactical drone scout")

    status_data = router.check_rodin_status(task["subscription_key"])
    assert status_data["subscription_key"] == task["subscription_key"]
    assert status_data["status"] == "Done"
    assert len(status_data["jobs"]) == 1
    assert status_data["jobs"][0]["uuid"] == task["uuid"]

    # Unknown key returns fallback Done status
    unknown = router.check_rodin_status("sub-unregistered-99")
    assert unknown["subscription_key"] == "sub-unregistered-99"
    assert unknown["status"] == "Done"


def test_download_rodin_assets():
    """Verify download_rodin_assets provides file manifest and base64 GLB mesh."""
    router = DynamicAIGatewayRouter(hyper3d_key=None)
    task = router.dispatch_rodin_generation("Sci-fi rover")

    assets = router.download_rodin_assets(task["uuid"])
    assert assets["task_uuid"] == task["uuid"]
    assert assets["format"] == "glb"
    assert len(assets["files"]) == 1
    assert assets["files"][0]["name"] == f"{task['uuid']}.glb"
    assert assets["files"][0]["format"] == "glb"

    glb_bytes = base64.b64decode(assets["glb_bytes_b64"])
    assert glb_bytes.startswith(b"glTF")


def test_get_analytics_includes_hyper3d():
    """Verify get_analytics incorporates Hyper3D billing and session counters."""
    router = DynamicAIGatewayRouter(hyper3d_key=None)
    router.dispatch_rodin_generation("Item 1", tier="Sketch")  # 0.25
    router.dispatch_rodin_generation("Item 2", tier="Detail")  # 1.00

    analytics = router.get_analytics(include_live_billing=True)
    assert "hyper3d" in analytics
    h3d = analytics["hyper3d"]
    assert h3d["provider"] == "Hyper3D Rodin (Ronin) v2"
    assert h3d["session_total_tasks"] == 2
    assert h3d["session_total_spend_usd"] == 1.25
    assert h3d["tier_pricing_usd"]["Detail"] == 1.00

    analytics_no_billing = router.get_analytics(include_live_billing=False)
    assert analytics_no_billing["hyper3d"] == {}


def test_sponsor_ad_hyper3d_rodin():
    """Verify sponsor_ads contains hyper3d-rodin right after openrouter."""
    ids = [s.id for s in DEFAULT_SPONSORS]
    assert "hyper3d-rodin" in ids
    openrouter_idx = ids.index("openrouter")
    rodin_idx = ids.index("hyper3d-rodin")
    assert rodin_idx == openrouter_idx + 1

    mgr = SponsorAdManager()
    sp = mgr.get_sponsor("hyper3d-rodin")
    assert sp["id"] == "hyper3d-rodin"
    assert "Hyper3D Rodin" in sp["name"]
    assert sp["badge"] == "3D GenAI Partner"
    assert sp["reward_tokens"] == 5000
    assert sp["reward_usd"] == 0.05
    assert SponsorAd is SponsorCreative
