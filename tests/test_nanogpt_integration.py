"""Tests for the NanoGPT integration across TinCan Mesh OS, gateway router, server, and CLI."""

import io
import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import pytest

from iot_federated_agent_memory import ai_gateway
from iot_federated_agent_memory.ai_gateway import (
    DEFAULT_NANOGPT_MODELS,
    DynamicAIGatewayRouter,
    _normalize_nanogpt_pricing,
)
from iot_federated_agent_memory.cyberspace_board import KNOWN_AI_AGENTS
from iot_federated_agent_memory.space_notes import RelayChatRouter, pick_router


class _MockHTTPResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_normalize_nanogpt_pricing():
    norm = _normalize_nanogpt_pricing({"prompt": 0.22, "completion": 0.9, "unit": "per_million_tokens"})
    assert norm["prompt_per_1m"] == pytest.approx(0.22)
    assert norm["completion_per_1m"] == pytest.approx(0.9)
    assert float(norm["prompt"]) == pytest.approx(0.22 / 1_000_000.0)
    assert float(norm["completion"]) == pytest.approx(0.9 / 1_000_000.0)


def test_nanogpt_routing_and_default_brain():
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="")
    assert "nanogpt-brain" in router.providers
    assert router.providers["nanogpt-brain"].api_key_env == "NANOGPT_API_KEY"
    assert router.providers["nanogpt-brain"].endpoint == router.NANOGPT_ENDPOINT

    cfg_prefixed = router.route_request("nanogpt/openai/gpt-6-astra", estimated_cost=0.05)
    assert cfg_prefixed.api_key_env == "NANOGPT_API_KEY"
    assert cfg_prefixed.endpoint == router.NANOGPT_ENDPOINT

    cfg_unprefixed = router.route_request("abliteration-ai/abliterated-model-large-v2", estimated_cost=0.05)
    assert cfg_unprefixed.api_key_env == "NANOGPT_API_KEY"
    assert cfg_unprefixed.input_cost_per_1m == pytest.approx(3.0)
    assert cfg_unprefixed.output_cost_per_1m == pytest.approx(5.0)

    cfg_tee = router.route_request("TEE/deepseek-v4.1-flash", estimated_cost=0.05)
    assert cfg_tee.api_key_env == "NANOGPT_API_KEY"


def test_nanogpt_simulated_dispatch_without_key(monkeypatch):
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="")
    res = router.dispatch_completion("nanogpt-brain", [{"role": "user", "content": "hello"}])
    assert res["gateway"] == "nanogpt"
    assert "NanoGPT router: key pending" in res["choices"][0]["message"]["content"]


def test_nanogpt_live_dispatch_headers_stripped_model_and_cost():
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="ng-test-key")
    captured = {}

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        body = {
            "id": "ng-chat-1",
            "model": captured["payload"]["model"],
            "choices": [{"message": {"role": "assistant", "content": "heretic ok"}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
        }
        return _MockHTTPResponse(json.dumps(body).encode("utf-8"))

    with patch.object(ai_gateway.urllib.request, "urlopen", side_effect=fake_urlopen):
        res = router.dispatch_completion(
            "nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
            [{"role": "user", "content": "hi"}],
        )

    assert captured["url"] == router.NANOGPT_ENDPOINT
    headers_low = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_low["authorization"] == "Bearer ng-test-key"
    assert headers_low["x-api-key"] == "ng-test-key"
    assert captured["payload"]["model"] == "pqhaz/DeepSeek-V4.1-Flash-1017-heretic"
    assert res["choices"][0]["message"]["content"] == "heretic ok"
    # Computed cost: (1000 * 0.198 + 500 * 0.792) / 1e6 = 0.000594
    assert res["cost_usd"] == pytest.approx(0.000594, rel=1e-4)


def test_nanogpt_404_fallback_to_auto_model():
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="ng-test-key")
    seen_models = []

    def fake_urlopen(req, timeout=30):
        payload = json.loads(req.data.decode("utf-8"))
        seen_models.append(payload["model"])
        if payload["model"] != "auto-model":
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b""))
        return _MockHTTPResponse(
            json.dumps({
                "id": "ng-auto-1",
                "model": "auto-model",
                "choices": [{"message": {"role": "assistant", "content": "auto ok"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }).encode("utf-8")
        )

    with patch.object(ai_gateway.urllib.request, "urlopen", side_effect=fake_urlopen):
        res = router.dispatch_completion("nanogpt/some-retired-model", [{"role": "user", "content": "hi"}])

    assert seen_models == ["some-retired-model", "auto-model"]
    assert res["choices"][0]["message"]["content"] == "auto ok"


def test_nanogpt_live_catalog_and_billing_and_swr():
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="ng-test-key")

    def fake_urlopen(req, timeout=8):
        url = req.full_url
        if "api/v1/models" in url:
            return _MockHTTPResponse(json.dumps({
                "data": [
                    {
                        "id": "z-ai/glm-5.3-flash-apex-abliterated",
                        "name": "GLM 5.3 Flash Apex Abliterated",
                        "description": "Uncensored 1M",
                        "context_length": 1048576,
                        "category": "Uncensored",
                        "open_weights": True,
                        "subscription": {"included": True},
                        "pricing": {"prompt": 0.15, "completion": 0.5, "unit": "per_million_tokens"},
                    },
                    {
                        "id": "openai/gpt-6-astra",
                        "name": "GPT-6 Astra",
                        "context_length": 400000,
                        "category": "More",
                        "open_weights": False,
                        "subscription": {"included": False},
                        "pricing": {"prompt": 2.0, "completion": 8.0, "unit": "per_million_tokens"},
                    },
                ]
            }).encode("utf-8"))
        if "check-balance" in url:
            return _MockHTTPResponse(json.dumps({
                "usd_balance": "42.125",
                "nano_balance": "15.5",
            }).encode("utf-8"))
        raise AssertionError(f"Unexpected URL: {url}")

    with patch.object(ai_gateway.urllib.request, "urlopen", side_effect=fake_urlopen):
        models = router.get_nanogpt_models(force_refresh=True, include_live_public=True)
        assert any(m["id"] == "nanogpt/openai/gpt-6-astra" for m in models)
        assert router.is_arena_model_allowed("nanogpt/openai/gpt-6-astra")

        analytics = router.get_analytics(include_live_billing=True)
        ng = analytics["nanogpt"]
        assert ng["connected"] is True
        assert ng["account_remaining_balance_usd"] == pytest.approx(42.125)
        assert ng["account_remaining_nano"] == pytest.approx(15.5)
        assert analytics["providers"]["nanogpt-brain"]["gateway"] == "nanogpt"
        assert analytics["providers"]["nanogpt-brain"]["remaining_credits"] == pytest.approx(42.125)

    # Stale-while-revalidate when cache is expired
    router._nanogpt_billing_cached_at = time.time() - 120.0
    bg_called = threading.Event()

    def slow_fetch(api_key):
        bg_called.set()
        return router._nanogpt_billing_cache

    with patch.object(router, "_fetch_nanogpt_billing_sync", side_effect=slow_fetch):
        t0 = time.monotonic()
        cached = router.get_nanogpt_billing(force_refresh=False)
        assert time.monotonic() - t0 < 0.05
        assert cached["account_remaining_balance_usd"] == pytest.approx(42.125)
        assert bg_called.wait(timeout=1.0)


def test_set_model_switches_gateway_between_openrouter_and_nanogpt():
    router = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="")
    cfg = router.set_model("gemini-brain", "nanogpt/abliteration-ai/abliterated-model-large-v2")
    assert cfg.endpoint == router.NANOGPT_ENDPOINT
    assert cfg.api_key_env == "NANOGPT_API_KEY"
    assert cfg.input_cost_per_1m == pytest.approx(3.0)

    cfg2 = router.set_model("gemini-brain", "google/gemini-2.5-pro")
    assert cfg2.endpoint == router.OPENROUTER_ENDPOINT
    assert cfg2.api_key_env == "OPENROUTER_API_KEY"


def test_cyberspace_and_space_notes_nanogpt_awareness(monkeypatch):
    assert "nanogpt-brain" in KNOWN_AI_AGENTS
    fake_router = MagicMock(openrouter_key=None, nanogpt_key="ng-key")
    assert pick_router(fake_router, "http://relay.local", "peer-1") is fake_router
    no_key_router = MagicMock(openrouter_key=None, nanogpt_key=None)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    assert isinstance(pick_router(no_key_router, "http://relay.local", "peer-1"), RelayChatRouter)


@pytest.fixture(scope="module")
def live_nanogpt_server():
    import server
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_server_nanogpt_endpoints(live_nanogpt_server):
    with urllib.request.urlopen(f"{live_nanogpt_server}/api/models/nanogpt?live=0&uncensored=1", timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
        assert data["gateway"] == "nanogpt"
        assert data["count"] >= 5
        assert all(m["id"].startswith("nanogpt/") for m in data["models"])

    with urllib.request.urlopen(f"{live_nanogpt_server}/api/models/available?gateway=openrouter", timeout=10) as r:
        or_data = json.loads(r.read().decode("utf-8"))
        assert or_data["count"] > 0
        assert not any(m.get("gateway") == "nanogpt" for m in or_data["models"])

    req = urllib.request.Request(
        f"{live_nanogpt_server}/api/models/set",
        data=json.dumps({
            "alias": "nanogpt-brain",
            "model": "nanogpt/z-ai/glm-5.3-flash-apex-abliterated",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        upd = json.loads(r.read().decode("utf-8"))
        assert upd["status"] == "updated"
        assert upd["gateway"] == "nanogpt"
        assert upd["endpoint"] == DynamicAIGatewayRouter.NANOGPT_ENDPOINT

    with urllib.request.urlopen(f"{live_nanogpt_server}/api/models/analytics", timeout=10) as r:
        analytics = json.loads(r.read().decode("utf-8"))
        assert "nanogpt" in analytics
        assert analytics["providers"]["nanogpt-brain"]["gateway"] == "nanogpt"


def test_cli_models_nanogpt_json():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "iot_federated_agent_memory.tincan_cli",
            "models",
            "--gateway",
            "nanogpt",
            "--uncensored",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    assert out["gateway"] == "nanogpt"
    assert out["count"] >= 5
    assert any(m["id"] == DEFAULT_NANOGPT_MODELS[0]["id"] for m in out["models"])
