"""Dynamic Multi-Lab AI Gateway Router and Subscription Credit Pooling."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class LabProviderConfig:
    lab_id: str
    display_name: str
    model_alias: str
    endpoint: str
    api_key_env: str
    available_credits: float
    is_active: bool


class DynamicAIGatewayRouter:
    """Manages hot-swappable AI provider subscriptions, credit budgets, and fallback cascading."""

    DEFAULT_LABS = {
        "claude-brain": LabProviderConfig(
            lab_id="anthropic",
            display_name="Anthropic Claude Sonnet",
            model_alias="claude-3-7-sonnet",
            endpoint="https://api.anthropic.com/v1/messages",
            api_key_env="ANTHROPIC_API_KEY",
            available_credits=100.0,
            is_active=True,
        ),
        "grok-brain": LabProviderConfig(
            lab_id="xai",
            display_name="xAI Grok",
            model_alias="grok-beta",
            endpoint="https://api.x.ai/v1/chat/completions",
            api_key_env="XAI_API_KEY",
            available_credits=50.0,
            is_active=True,
        ),
        "gemini-brain": LabProviderConfig(
            lab_id="google",
            display_name="Google Gemini Flash",
            model_alias="gemini-2.0-flash",
            endpoint="https://generativelanguage.googleapis.com/v1beta",
            api_key_env="GEMINI_API_KEY",
            available_credits=80.0,
            is_active=True,
        ),
        "openai-brain": LabProviderConfig(
            lab_id="openai",
            display_name="OpenAI GPT-4o",
            model_alias="gpt-4o",
            endpoint="https://api.openai.com/v1/chat/completions",
            api_key_env="OPENAI_API_KEY",
            available_credits=60.0,
            is_active=True,
        ),
    }

    def __init__(self):
        self.providers: Dict[str, LabProviderConfig] = dict(self.DEFAULT_LABS)
        self.routing_log: List[Dict[str, Any]] = []

    def route_request(self, requested_alias: str, estimated_cost: float = 0.02) -> LabProviderConfig:
        """Route request to the target lab, or fallback if credit pool is exhausted."""
        primary = self.providers.get(requested_alias)
        if primary and primary.is_active and primary.available_credits >= estimated_cost:
            primary.available_credits -= estimated_cost
            self.routing_log.append({"alias": requested_alias, "lab": primary.lab_id, "cost": estimated_cost, "status": "routed"})
            return primary

        # Fallback to any active provider with available credit balance
        for alias, config in self.providers.items():
            if config.is_active and config.available_credits >= estimated_cost:
                config.available_credits -= estimated_cost
                self.routing_log.append({"alias": requested_alias, "fallback_to": alias, "lab": config.lab_id, "status": "fallback"})
                return config

        raise RuntimeError("All AI lab subscription credit pools are exhausted.")

    def swap_lab_endpoint(self, alias: str, new_model: str, new_endpoint: str) -> None:
        if alias in self.providers:
            self.providers[alias].model_alias = new_model
            self.providers[alias].endpoint = new_endpoint
