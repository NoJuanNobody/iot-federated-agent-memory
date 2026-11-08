import pytest
from unittest.mock import patch, MagicMock
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter

def test_dynamic_ai_gateway_routing():
    router = DynamicAIGatewayRouter()
    provider = router.route_request("claude-brain", estimated_cost=10.0)
    assert provider.lab_id == "anthropic"
    assert provider.api_key_env == "OPENROUTER_API_KEY"
    assert provider.available_credits == 90.0

def test_ai_gateway_fallback_on_exhaustion():
    router = DynamicAIGatewayRouter()
    router.providers["grok-brain"].available_credits = 0.005

    # Should fallback gracefully to another funded lab
    fallback = router.route_request("grok-brain", estimated_cost=0.02)
    assert fallback.lab_id != "xai"
    assert fallback.available_credits > 0

def test_ai_gateway_simulated_dispatch():
    router = DynamicAIGatewayRouter(openrouter_key=None)
    res = router.dispatch_completion("claude-brain", [{"role": "user", "content": "hi"}])
    assert "Simulated" in res["choices"][0]["message"]["content"]
    assert res["model"] == "anthropic/claude-3.7-sonnet"

def test_ai_gateway_real_openrouter_dispatch():
    router = DynamicAIGatewayRouter(openrouter_key="sk-or-v1-mock-test")
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"id":"gen-123","model":"anthropic/claude-3.7-sonnet","choices":[{"message":{"role":"assistant","content":"hello"}}]}'
    mock_resp.__enter__.return_value = mock_resp
    
    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = router.dispatch_completion("claude-brain", [{"role": "user", "content": "test"}])
        assert res["choices"][0]["message"]["content"] == "hello"
