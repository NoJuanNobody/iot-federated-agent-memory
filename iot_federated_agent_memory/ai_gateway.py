"""Dynamic Multi-Lab AI Gateway Router and OpenRouter Unified Credit Pooling."""

from __future__ import annotations

import json
import os
import urllib.request
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
    """Manages hot-swappable AI provider subscriptions, credit budgets, and OpenRouter unified routing."""

    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    DEFAULT_LABS = {
        "claude-brain": LabProviderConfig(
            lab_id="anthropic",
            display_name="Anthropic Claude Sonnet",
            model_alias="anthropic/claude-sonnet-5.5",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=100.0,
            is_active=True,
        ),
        "grok-brain": LabProviderConfig(
            lab_id="xai",
            display_name="xAI Grok",
            model_alias="x-ai/grok-4.7",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=50.0,
            is_active=True,
        ),
        "gemini-brain": LabProviderConfig(
            lab_id="google",
            display_name="Google Gemini Flash",
            model_alias="google/gemini-2.5-flash",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=80.0,
            is_active=True,
        ),
        "openai-brain": LabProviderConfig(
            lab_id="openai",
            display_name="OpenAI GPT-4o",
            model_alias="openai/gpt-4o",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=60.0,
            is_active=True,
        ),
    }

    def __init__(self, openrouter_key: Optional[str] = None):
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY")
        self.providers: Dict[str, LabProviderConfig] = {
            k: LabProviderConfig(**asdict(v)) for k, v in self.DEFAULT_LABS.items()
        }
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

    def swap_lab_endpoint(self, alias: str, new_model: str, new_endpoint: Optional[str] = None) -> None:
        if alias in self.providers:
            self.providers[alias].model_alias = new_model
            if new_endpoint:
                self.providers[alias].endpoint = new_endpoint

    def dispatch_completion(
        self,
        alias: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Dispatch real chat completion to OpenRouter using single OPENROUTER_API_KEY."""
        config = self.route_request(alias)
        api_key = self.openrouter_key or os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            # Simulated offline response if no API key is injected
            return {
                "id": f"sim-{alias}",
                "model": config.model_alias,
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"[Simulated {config.display_name} via OpenRouter router: key pending]",
                    }
                }],
                "usage": {"total_tokens": 42},
            }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/NoJuanNobody/tin-can",
            "X-Title": "TinCan 2 / IoT Federated Agent Memory",
        }
        payload = {
            "model": config.model_alias,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(
            config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
