"""Unit and CLI/server integration tests for local Ollama, FAU OwlChat/Trussed AI,
and custom OpenAI-compatible inference routing in TinCan.
"""

from __future__ import annotations

import io
import json
import sys
import threading
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from iot_federated_agent_memory import tincan_cli
from iot_federated_agent_memory.ai_gateway import (
    DEFAULT_OLLAMA_BASE_URL,
    OWLCHAT_BASE_URL,
    TRUSSED_AI_BASE_URL,
    DynamicAIGatewayRouter,
    build_chat_completions_url,
    build_models_url,
    normalize_openai_compat_base_url,
    resolve_ollama_base_url,
)
from iot_federated_agent_memory.tincan_agent import TinCanAgentChat


class _FakeHTTPResponse:
    def __init__(self, payload: Dict[str, Any], status: int = 200) -> None:
        self._raw = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_url_normalization_for_ollama_owlchat_trussed_and_custom_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    assert resolve_ollama_base_url() == DEFAULT_OLLAMA_BASE_URL
    assert resolve_ollama_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434/v1"
    assert resolve_ollama_base_url("http://localhost:11434/v1/") == "http://localhost:11434/v1"

    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11435")
    assert resolve_ollama_base_url() == "http://127.0.0.1:11435/v1"

    assert normalize_openai_compat_base_url(OWLCHAT_BASE_URL) == "https://chat.hpc.fau.edu/openai"
    assert build_chat_completions_url(OWLCHAT_BASE_URL) == "https://chat.hpc.fau.edu/openai/chat/completions"
    assert build_models_url(OWLCHAT_BASE_URL) == "https://chat.hpc.fau.edu/openai/models"

    assert build_chat_completions_url(TRUSSED_AI_BASE_URL) == (
        "https://trussed.ai.hpc.fau.edu/provider/generic/chat/completions"
    )
    assert build_chat_completions_url("http://localhost:8000/v1/chat/completions") == (
        "http://localhost:8000/v1/chat/completions"
    )
    assert build_models_url("http://localhost:8000/v1/chat/completions") == (
        "http://localhost:8000/v1/models"
    )


def test_dispatch_ollama_without_api_key_or_cloud_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    seen_requests: List[Dict[str, Any]] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        body = json.loads(req.data.decode("utf-8"))
        seen_requests.append({
            "url": req.full_url,
            "headers": {k.lower(): v for k, v in req.header_items()},
            "body": body,
            "timeout": timeout,
        })
        return _FakeHTTPResponse({
            "id": "chatcmpl-ollama-1",
            "model": body["model"],
            "choices": [{"message": {"role": "assistant", "content": "Local Ollama OK"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
        })

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    router = DynamicAIGatewayRouter()
    original_gemini_endpoint = router.providers["gemini-brain"].endpoint

    out = router.dispatch_completion(
        "ollama/qwen2.5:3b",
        [{"role": "user", "content": "hello"}],
    )

    assert len(seen_requests) == 1
    req_info = seen_requests[0]
    assert req_info["url"] == "http://localhost:11434/v1/chat/completions"
    assert req_info["body"]["model"] == "qwen2.5:3b"
    assert "authorization" not in req_info["headers"]
    assert out["gateway"] == "ollama"
    assert out["cost_usd"] == 0.0
    assert out["choices"][0]["message"]["content"] == "Local Ollama OK"
    assert router.providers["gemini-brain"].endpoint == original_gemini_endpoint


def test_dispatch_ollama_404_raises_without_gemini_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_models: List[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        body = json.loads(req.data.decode("utf-8"))
        seen_models.append(body["model"])
        raise urllib.error.HTTPError(
            req.full_url,
            404,
            "Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"error":"model \'missing:latest\' not found"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    router = DynamicAIGatewayRouter()
    with pytest.raises(RuntimeError, match="Ollama HTTP 404"):
        router.dispatch_completion("ollama/missing:latest", [{"role": "user", "content": "hi"}])

    assert seen_models == ["missing:latest"]


def test_dispatch_owlchat_and_trussed_and_explicit_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OWLCHAT_API_KEY", raising=False)
    monkeypatch.delenv("FAU_OWLCHAT_API_KEY", raising=False)
    monkeypatch.delenv("TRUSSED_AI_API_KEY", raising=False)

    router_no_key = DynamicAIGatewayRouter()
    sim = router_no_key.dispatch_completion("owlchat/Gemma4-vibe", [{"role": "user", "content": "hi"}])
    assert sim["gateway"] == "owlchat"
    assert "Simulated" in sim["choices"][0]["message"]["content"]
    assert "OwlChat" in sim["choices"][0]["message"]["content"]

    calls: List[Dict[str, Any]] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        body = json.loads(req.data.decode("utf-8"))
        calls.append({
            "url": req.full_url,
            "headers": {k.lower(): v for k, v in req.header_items()},
            "body": body,
        })
        return _FakeHTTPResponse({
            "id": "chatcmpl-fau-1",
            "model": body["model"],
            "choices": [{"message": {"role": "assistant", "content": f"ok:{body['model']}"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        })

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("OWLCHAT_API_KEY", "owl-secret-123")
    monkeypatch.setenv("TRUSSED_AI_API_KEY", "trussed-secret-456")

    router = DynamicAIGatewayRouter()
    original_gemini = (
        router.providers["gemini-brain"].endpoint,
        router.providers["gemini-brain"].model_alias,
    )

    res_owl = router.dispatch_completion("owlchat/Gemma4-vibe", [{"role": "user", "content": "hi"}])
    res_trussed = router.dispatch_completion("trussed/llama-3.3-70b", [{"role": "user", "content": "hi"}])
    res_custom = router.dispatch_completion(
        "meta-llama/Llama-3.3-70B-Instruct",
        [{"role": "user", "content": "hi"}],
        base_url="http://localhost:8000/v1",
        gateway="local",
    )

    assert len(calls) == 3
    assert calls[0]["url"] == "https://chat.hpc.fau.edu/openai/chat/completions"
    assert calls[0]["headers"]["authorization"] == "Bearer owl-secret-123"
    assert calls[0]["body"]["model"] == "Gemma4-vibe"
    assert res_owl["gateway"] == "owlchat"

    assert calls[1]["url"] == "https://trussed.ai.hpc.fau.edu/provider/generic/chat/completions"
    assert calls[1]["headers"]["authorization"] == "Bearer trussed-secret-456"
    assert calls[1]["body"]["model"] == "llama-3.3-70b"
    assert res_trussed["gateway"] == "trussed"

    assert calls[2]["url"] == "http://localhost:8000/v1/chat/completions"
    assert calls[2]["body"]["model"] == "meta-llama/Llama-3.3-70B-Instruct"
    assert res_custom["gateway"] == "local"

    assert (
        router.providers["gemini-brain"].endpoint,
        router.providers["gemini-brain"].model_alias,
    ) == original_gemini


def test_catalog_discovery_ollama_and_openai_compat(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        if req.full_url == "http://localhost:11434/api/tags":
            return _FakeHTTPResponse({
                "models": [
                    {"name": "qwen2.5:3b", "details": {"parameter_size": "3.1B"}},
                    {"name": "llama3.1:8b", "details": {"parameter_size": "8.0B"}},
                ]
            })
        if req.full_url == "https://chat.hpc.fau.edu/openai/models":
            auth = {k.lower(): v for k, v in req.header_items()}.get("authorization")
            assert auth == "Bearer owl-test"
            return _FakeHTTPResponse({
                "data": [
                    {"id": "Gemma4-vibe"},
                    {"id": "gpt-oss:120b"},
                ]
            })
        raise AssertionError(f"Unexpected URL: {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    router = DynamicAIGatewayRouter()

    ollama_models = router.get_ollama_models()
    assert [m["id"] for m in ollama_models] == ["ollama/qwen2.5:3b", "ollama/llama3.1:8b"]
    assert all(m["gateway"] == "ollama" for m in ollama_models)

    owl_models = router.get_openai_compat_models(
        OWLCHAT_BASE_URL,
        api_key="owl-test",
        gateway_name="owlchat",
        prefix="owlchat",
    )
    assert [m["id"] for m in owl_models] == ["owlchat/Gemma4-vibe", "owlchat/gpt-oss:120b"]
    assert all(m["gateway"] == "owlchat" for m in owl_models)

    def fail_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)
    assert router.get_ollama_models() == []


def test_tincan_agent_chat_relay_vs_direct_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        calls.append(req.full_url)
        if req.full_url == "http://relay.example/api/chat":
            return _FakeHTTPResponse({
                "choices": [{"message": {"role": "assistant", "content": "relay reply"}}],
                "thread_id": "thr-1",
            })
        if req.full_url == "http://localhost:11434/v1/chat/completions":
            body = json.loads(req.data.decode("utf-8"))
            return _FakeHTTPResponse({
                "choices": [{"message": {"role": "assistant", "content": f"direct:{body['model']}"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            })
        if req.full_url == "http://localhost:8000/v1/chat/completions":
            body = json.loads(req.data.decode("utf-8"))
            return _FakeHTTPResponse({
                "choices": [{"message": {"role": "assistant", "content": f"tunneled:{body['model']}"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            })
        raise AssertionError(f"Unexpected URL: {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    relay_agent = TinCanAgentChat("http://relay.example", peer_id="peer-1")
    assert relay_agent.is_direct_mode() is False
    assert relay_agent.ask("hi") == "relay reply"
    assert calls[-1] == "http://relay.example/api/chat"

    local_agent = TinCanAgentChat("http://relay.example", model_alias="qwen2.5:3b", local=True)
    assert local_agent.is_direct_mode() is True
    assert local_agent.ask("hi") == "direct:qwen2.5:3b"
    assert calls[-1] == "http://localhost:11434/v1/chat/completions"

    prefixed_agent = TinCanAgentChat("http://relay.example", model_alias="ollama/qwen2.5:3b")
    assert prefixed_agent.is_direct_mode() is True
    assert prefixed_agent.ask("hi") == "direct:qwen2.5:3b"

    owl_agent = TinCanAgentChat("http://relay.example", model_alias="owlchat/Gemma4-vibe")
    assert owl_agent.is_direct_mode() is True

    custom_agent = TinCanAgentChat(
        "http://relay.example",
        model_alias="Qwen/Qwen2.5-72B-Instruct",
        base_url="http://localhost:8000/v1",
    )
    assert custom_agent.is_direct_mode() is True
    assert custom_agent.ask("hi") == "tunneled:Qwen/Qwen2.5-72B-Instruct"
    assert calls[-1] == "http://localhost:8000/v1/chat/completions"


def test_tincan_cli_models_and_ask_local_compat(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0.0):
        calls.append({"url": req.full_url, "method": req.get_method()})
        if req.full_url == "http://localhost:11434/api/tags":
            return _FakeHTTPResponse({"models": [{"name": "qwen2.5:3b", "details": {"parameter_size": "3.1B"}}]})
        if req.full_url == "https://chat.hpc.fau.edu/openai/models":
            return _FakeHTTPResponse({"data": [{"id": "Gemma4-vibe"}]})
        if req.full_url == "http://localhost:11434/v1/chat/completions":
            body = json.loads(req.data.decode("utf-8"))
            return _FakeHTTPResponse({
                "choices": [{"message": {"role": "assistant", "content": f"cli-ollama:{body['model']}"}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
            })
        if req.full_url == "http://localhost:8000/v1/chat/completions":
            body = json.loads(req.data.decode("utf-8"))
            return _FakeHTTPResponse({
                "choices": [{"message": {"role": "assistant", "content": f"cli-vllm:{body['model']}"}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
            })
        raise AssertionError(f"Unexpected URL: {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tincan_cli.main([
            "--dir", str(tmp_path),
            "models", "--gateway", "ollama", "--json",
        ])
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert data["gateway"] == "ollama"
    assert [m["id"] for m in data["models"]] == ["ollama/qwen2.5:3b"]

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tincan_cli.main([
            "--dir", str(tmp_path),
            "models", "--gateway", "owlchat", "--api-key", "k-test", "--json",
        ])
    assert rc == 0
    owl_data = json.loads(buf.getvalue())
    assert owl_data["gateway"] == "owlchat"
    assert [m["id"] for m in owl_data["models"]] == ["owlchat/Gemma4-vibe"]

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tincan_cli.main([
            "--dir", str(tmp_path),
            "--relay", "http://relay-should-not-be-called.invalid",
            "ask", "hi", "--local", "--model", "qwen2.5:3b",
        ])
    assert rc == 0
    assert buf.getvalue().strip() == "cli-ollama:qwen2.5:3b"

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = tincan_cli.main([
            "--dir", str(tmp_path),
            "--relay", "http://relay-should-not-be-called.invalid",
            "ask", "hi", "--base-url", "http://localhost:8000/v1", "--model", "meta-llama/Llama-3.3-70B-Instruct",
        ])
    assert rc == 0
    assert buf.getvalue().strip() == "cli-vllm:meta-llama/Llama-3.3-70B-Instruct"


def test_server_models_available_gateway_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    import server as srv

    monkeypatch.setattr(
        srv.router,
        "get_ollama_models",
        lambda base_url=None: [{"id": "ollama/qwen2.5:3b", "name": "qwen2.5:3b", "gateway": "ollama"}],
    )

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.MeshGatewayHandler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/models/available?gateway=ollama", timeout=5.0) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        assert payload["count"] == 1
        assert payload["models"][0]["id"] == "ollama/qwen2.5:3b"
    finally:
        httpd.shutdown()
        httpd.server_close()
