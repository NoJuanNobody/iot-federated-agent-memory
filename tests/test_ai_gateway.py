import pytest
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter

def test_dynamic_ai_gateway_routing():
    router = DynamicAIGatewayRouter()
    provider = router.route_request("claude-brain", estimated_cost=10.0)
    assert provider.lab_id == "anthropic"
    assert provider.available_credits == 90.0

def test_ai_gateway_fallback_on_exhaustion():
    router = DynamicAIGatewayRouter()
    router.providers["grok-brain"].available_credits = 0.005

    # Should fallback gracefully to another funded lab
    fallback = router.route_request("grok-brain", estimated_cost=0.02)
    assert fallback.lab_id != "xai"
    assert fallback.available_credits > 0
