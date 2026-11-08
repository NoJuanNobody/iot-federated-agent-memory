"""Dynamic Multi-Lab AI Gateway Router and OpenRouter Unified Credit Pooling."""

from __future__ import annotations

import json
import os
import time
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
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


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
            self.routing_log.append({
                "timestamp": time.time(),
                "alias": requested_alias,
                "lab": primary.lab_id,
                "model": primary.model_alias,
                "cost": estimated_cost,
                "status": "routed",
            })
            return primary

        # Fallback to any active provider with available credit balance
        for alias, config in self.providers.items():
            if config.is_active and config.available_credits >= estimated_cost:
                config.available_credits -= estimated_cost
                self.routing_log.append({
                    "timestamp": time.time(),
                    "alias": requested_alias,
                    "fallback_to": alias,
                    "lab": config.lab_id,
                    "model": config.model_alias,
                    "status": "fallback",
                })
                return config

        raise RuntimeError("All AI lab subscription credit pools are exhausted.")

    def swap_lab_endpoint(self, alias: str, new_model: str, new_endpoint: Optional[str] = None) -> None:
        if alias in self.providers:
            self.providers[alias].model_alias = new_model
            if new_endpoint:
                self.providers[alias].endpoint = new_endpoint

    def set_model(self, alias: str, new_model: str, display_name: Optional[str] = None) -> LabProviderConfig:
        """Set or update model name for a provider alias."""
        if alias not in self.providers:
            # Create custom provider slot
            self.providers[alias] = LabProviderConfig(
                lab_id="custom",
                display_name=display_name or alias,
                model_alias=new_model,
                endpoint=self.OPENROUTER_ENDPOINT,
                api_key_env="OPENROUTER_API_KEY",
                available_credits=50.0,
                is_active=True,
            )
        else:
            self.providers[alias].model_alias = new_model
            if display_name:
                self.providers[alias].display_name = display_name
        return self.providers[alias]

    def record_usage(
        self,
        alias: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float = 0.0,
    ) -> None:
        if alias in self.providers:
            provider = self.providers[alias]
            provider.total_calls += 1
            provider.total_prompt_tokens += prompt_tokens
            provider.total_completion_tokens += completion_tokens
            provider.total_tokens += total_tokens
            provider.total_cost += cost

    def get_analytics(self) -> Dict[str, Any]:
        """Aggregate usage analytics across all models."""
        total_calls = sum(p.total_calls for p in self.providers.values())
        total_tokens = sum(p.total_tokens for p in self.providers.values())
        total_spend = sum(p.total_cost for p in self.providers.values())
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_spend_usd": round(total_spend, 6),
            "providers": {
                k: {
                    "display_name": p.display_name,
                    "model": p.model_alias,
                    "total_calls": p.total_calls,
                    "prompt_tokens": p.total_prompt_tokens,
                    "completion_tokens": p.total_completion_tokens,
                    "total_tokens": p.total_tokens,
                    "cost_usd": round(p.total_cost, 6),
                    "remaining_credits": round(p.available_credits, 4),
                    "is_active": p.is_active,
                }
                for k, p in self.providers.items()
            },
            "recent_routing_log": self.routing_log[-20:],
        }

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
            self.record_usage(alias, 10, 32, 42, 0.0)
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
            data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            prompt_toks = usage.get("prompt_tokens", 0)
            comp_toks = usage.get("completion_tokens", 0)
            total_toks = usage.get("total_tokens", prompt_toks + comp_toks)
            cost = usage.get("cost", 0.0)
            self.record_usage(alias, prompt_toks, comp_toks, total_toks, cost)
            return data
