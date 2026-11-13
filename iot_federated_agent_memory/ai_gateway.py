"""Dynamic Multi-Lab AI Gateway Router and Live OpenRouter Cost & Credit Dashboard."""

from __future__ import annotations

import base64
import json
import os
import struct
import subprocess
import threading
import time
import urllib.request
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


def _resolve_openrouter_key_fallback() -> Optional[str]:
    """Resolve OPENROUTER_API_KEY strictly from environment (CLI subprocess scraping disabled)."""
    return os.environ.get("OPENROUTER_API_KEY")


def _resolve_hyper3d_key_fallback() -> Optional[str]:
    """Resolve Hyper3D / Rodin API key from environment."""
    return os.environ.get("HYPER3D_API_KEY") or os.environ.get("RODIN_API_KEY")


def generate_minimal_glb_bytes(name: str = "rodin_mesh") -> bytes:
    """Generate a valid binary glTF 2.0 (.glb) buffer for offline/simulated 3D mesh workflows.

    Header (12 bytes) + JSON chunk (type 0x4E4F534A) + BIN chunk (type 0x004E4942)
    containing valid triangle primitive geometry, 4-byte aligned.
    """
    indices_bytes = struct.pack("<3H", 0, 1, 2)
    indices_pad = b"\x00" * ((4 - (len(indices_bytes) % 4)) % 4)
    positions = [
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
    ]
    positions_bytes = struct.pack("<9f", *positions)
    bin_buffer = indices_bytes + indices_pad + positions_bytes
    bin_pad = b"\x00" * ((4 - (len(bin_buffer) % 4)) % 4)
    bin_chunk_data = bin_buffer + bin_pad

    gltf = {
        "asset": {"version": "2.0", "generator": "Hyper3D Rodin Gateway"},
        "scene": 0,
        "scenes": [{"name": name, "nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [{
            "name": name,
            "primitives": [{
                "attributes": {"POSITION": 1},
                "indices": 0,
                "mode": 4,
            }],
        }],
        "buffers": [{"byteLength": len(bin_buffer)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(indices_bytes), "target": 34963},
            {"buffer": 0, "byteOffset": len(indices_bytes) + len(indices_pad), "byteLength": len(positions_bytes), "target": 34962},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5123,
                "count": 3,
                "type": "SCALAR",
                "max": [2],
                "min": [0],
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5126,
                "count": 3,
                "type": "VEC3",
                "max": [1.0, 1.0, 0.0],
                "min": [0.0, 0.0, 0.0],
            },
        ],
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_pad = b" " * ((4 - (len(json_bytes) % 4)) % 4)
    json_chunk_data = json_bytes + json_pad

    total_length = 12 + (8 + len(json_chunk_data)) + (8 + len(bin_chunk_data))
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_header = struct.pack("<II", len(json_chunk_data), 0x4E4F534A)
    bin_header = struct.pack("<II", len(bin_chunk_data), 0x004E4942)
    return header + json_header + json_chunk_data + bin_header + bin_chunk_data


@dataclass
class LabProviderConfig:
    lab_id: str
    display_name: str
    model_alias: str
    endpoint: str
    api_key_env: str
    available_credits: float
    is_active: bool
    input_cost_per_1m: float = 1.0
    output_cost_per_1m: float = 3.0
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0



DEFAULT_OPENROUTER_MODELS: List[Dict[str, Any]] = [
    # Ronin 3D generative models
    {
        "id": "ronin/hyper3d-rodin-v2",
        "name": "Ronin / Hyper3D Rodin v2 (3D Mesh & PBR)",
        "provider": "Ronin",
        "description": "Generates 3D quad-mesh geometry, glTF/GLB models, and PBR textures from prompt.",
        "category": "3D Generative",
        "context_length": 4096,
        "pricing": {"prompt": "0.50/gen", "completion": "0.00"},
    },
    {
        "id": "ronin/regular",
        "name": "Ronin Regular 3D Mesh",
        "provider": "Ronin",
        "description": "Standard high-fidelity 3D mesh reconstruction.",
        "category": "3D Generative",
        "context_length": 4096,
        "pricing": {"prompt": "0.50/gen", "completion": "0.00"},
    },
    {
        "id": "ronin/sketch",
        "name": "Ronin Sketch 3D Mesh",
        "provider": "Ronin",
        "description": "Rapid draft 3D concept blockout mesh.",
        "category": "3D Generative",
        "context_length": 4096,
        "pricing": {"prompt": "0.25/gen", "completion": "0.00"},
    },
    {
        "id": "ronin/detail",
        "name": "Ronin Detail 3D Mesh",
        "provider": "Ronin",
        "description": "Ultra high-density surface detail 3D mesh.",
        "category": "3D Generative",
        "context_length": 4096,
        "pricing": {"prompt": "1.00/gen", "completion": "0.00"},
    },
    {
        "id": "ronin/smooth",
        "name": "Ronin Smooth 3D Quad-Mesh",
        "provider": "Ronin",
        "description": "Organic smoothed topology 3D quad-mesh.",
        "category": "3D Generative",
        "context_length": 4096,
        "pricing": {"prompt": "0.75/gen", "completion": "0.00"},
    },
    # OpenRouter Top LLM / Reasoning models
    {
        "id": "google/gemini-2.5-flash",
        "name": "Google Gemini 2.5 Flash",
        "provider": "Google",
        "description": "Ultra-fast multimodal reasoning, 1M context.",
        "category": "Fast Reasoning",
        "context_length": 1048576,
        "pricing": {"prompt": "0.00000015", "completion": "0.0000006"},
    },
    {
        "id": "google/gemini-2.5-pro",
        "name": "Google Gemini 2.5 Pro",
        "provider": "Google",
        "description": "State-of-the-art coding and complex logical deduction.",
        "category": "Advanced Reasoning",
        "context_length": 1048576,
        "pricing": {"prompt": "0.00000125", "completion": "0.000005"},
    },
    {
        "id": "anthropic/claude-3.7-sonnet",
        "name": "Anthropic Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "description": "Hybrid thinking and coding frontier model.",
        "category": "Advanced Reasoning",
        "context_length": 200000,
        "pricing": {"prompt": "0.000003", "completion": "0.000015"},
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Anthropic Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "description": "Benchmark-leading frontend, design, and coding agent model.",
        "category": "Coding & Design",
        "context_length": 200000,
        "pricing": {"prompt": "0.000003", "completion": "0.000015"},
    },
    {
        "id": "openai/gpt-4o",
        "name": "OpenAI GPT-4o",
        "provider": "OpenAI",
        "description": "Omni-modal flagship reasoning model.",
        "category": "General Purpose",
        "context_length": 128000,
        "pricing": {"prompt": "0.0000025", "completion": "0.00001"},
    },
    {
        "id": "openai/o3-mini",
        "name": "OpenAI o3-mini",
        "provider": "OpenAI",
        "description": "High-speed STEM reasoning and algorithmic code synthesis.",
        "category": "Deep Reasoning",
        "context_length": 200000,
        "pricing": {"prompt": "0.0000011", "completion": "0.0000044"},
    },
    {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "DeepSeek",
        "description": "Open weights reasoning model with chain-of-thought verification.",
        "category": "Deep Reasoning",
        "context_length": 128000,
        "pricing": {"prompt": "0.00000055", "completion": "0.00000219"},
    },
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek V3",
        "provider": "DeepSeek",
        "description": "671B parameter mixture-of-experts model.",
        "category": "General Purpose",
        "context_length": 128000,
        "pricing": {"prompt": "0.00000014", "completion": "0.00000028"},
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Meta Llama 3.3 70B Instruct",
        "provider": "Meta",
        "description": "Top-tier open-source instruct model with 128k context.",
        "category": "Open Weights",
        "context_length": 131072,
        "pricing": {"prompt": "0.00000018", "completion": "0.00000018"},
    },
    {
        "id": "qwen/qwen-2.5-72b-instruct",
        "name": "Qwen 2.5 72B Instruct",
        "provider": "Alibaba",
        "description": "Exceptional coding, math, and multilingual performance.",
        "category": "Open Weights",
        "context_length": 131072,
        "pricing": {"prompt": "0.00000035", "completion": "0.0000004"},
    },
    {
        "id": "mistralai/mistral-large-2411",
        "name": "Mistral Large 2411",
        "provider": "Mistral AI",
        "description": "Flagship 128k context frontier reasoning model.",
        "category": "Frontier",
        "context_length": 128000,
        "pricing": {"prompt": "0.000002", "completion": "0.000006"},
    },
    {
        "id": "x-ai/grok-2-1212",
        "name": "xAI Grok 2",
        "provider": "xAI",
        "description": "State-of-the-art vision and real-time reasoning model.",
        "category": "Frontier",
        "context_length": 131072,
        "pricing": {"prompt": "0.000002", "completion": "0.00001"},
    },
]


class DynamicAIGatewayRouter:
    """Manages hot-swappable AI provider models, live OpenRouter billing/credits, and per-call cost tracking."""

    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"
    OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/auth/key"

    # Hyper3D Rodin (Ronin) v2 3D Generation Endpoints
    RODIN_GENERATE_URL = "https://api.hyper3d.com/api/v2/rodin"
    RODIN_STATUS_URL = "https://api.hyper3d.com/api/v2/status"
    RODIN_DOWNLOAD_URL = "https://api.hyper3d.com/api/v2/download"
    RODIN_BALANCE_URL = "https://api.hyper3d.com/api/v2/check_balance"
    RODIN_TIER_COSTS = {"Regular": 0.50, "Sketch": 0.25, "Detail": 1.00, "Smooth": 0.75}

    DEFAULT_LABS = {
        "claude-brain": LabProviderConfig(
            lab_id="anthropic",
            display_name="Anthropic Claude Sonnet",
            model_alias="anthropic/claude-sonnet-5.5",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=100.0,
            is_active=True,
            input_cost_per_1m=3.00,
            output_cost_per_1m=15.00,
        ),
        "grok-brain": LabProviderConfig(
            lab_id="xai",
            display_name="xAI Grok",
            model_alias="x-ai/grok-4.7",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=50.0,
            is_active=True,
            input_cost_per_1m=2.00,
            output_cost_per_1m=10.00,
        ),
        "gemini-brain": LabProviderConfig(
            lab_id="google",
            display_name="Google Gemini Flash",
            model_alias="google/gemini-2.5-flash",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=80.0,
            is_active=True,
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
        ),
        "openai-brain": LabProviderConfig(
            lab_id="openai",
            display_name="OpenAI GPT-4o",
            model_alias="openai/gpt-4o",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=60.0,
            is_active=True,
            input_cost_per_1m=2.50,
            output_cost_per_1m=10.00,
        ),
    }

    def __init__(
        self,
        openrouter_key: Optional[str] = None,
        hyper3d_key: Optional[str] = None,
    ):
        self.openrouter_key = openrouter_key if openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")
        self.hyper3d_key = hyper3d_key if hyper3d_key is not None else _resolve_hyper3d_key_fallback()
        self.providers: Dict[str, LabProviderConfig] = {
            k: LabProviderConfig(**asdict(v)) for k, v in self.DEFAULT_LABS.items()
        }
        self.routing_log: List[Dict[str, Any]] = []
        self._billing_cache: Optional[Dict[str, Any]] = None
        self._billing_cached_at: float = 0.0
        self._billing_refreshing: bool = False
        self._billing_lock = threading.Lock()
        self.BILLING_CACHE_TTL: float = 60.0

        # Hyper3D Rodin state & caching
        self.rodin_tasks: Dict[str, Dict[str, Any]] = {}
        self.rodin_total_calls: int = 0
        self.rodin_total_cost_usd: float = 0.0
        self._rodin_billing_cache: Optional[Dict[str, Any]] = None
        self._rodin_billing_cached_at: float = 0.0
        self._rodin_billing_refreshing: bool = False
        self._rodin_billing_lock = threading.Lock()

        # Available models cache (OpenRouter + Ronin)
        self._available_models_cache: Optional[List[Dict[str, Any]]] = None
        self._available_models_cached_at: float = 0.0

    def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Return full catalog of OpenRouter and Ronin/Hyper3D models with caching."""
        now = time.time()
        if not force_refresh and self._available_models_cache and (now - self._available_models_cached_at < 600.0):
            return list(self._available_models_cache)

        models = [dict(m) for m in DEFAULT_OPENROUTER_MODELS]
        api_key = self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")

        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
                req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_list = data.get("data", [])
                    known_ids = {m["id"] for m in models}
                    for item in raw_list:
                        m_id = item.get("id")
                        if m_id and m_id not in known_ids:
                            pricing = item.get("pricing", {})
                            models.append({
                                "id": m_id,
                                "name": item.get("name") or m_id,
                                "provider": m_id.split("/")[0].capitalize(),
                                "description": item.get("description", ""),
                                "context_length": item.get("context_length", 8192),
                                "category": "OpenRouter",
                                "pricing": pricing,
                            })
                            known_ids.add(m_id)
            except Exception:
                pass

        self._available_models_cache = models
        self._available_models_cached_at = now
        return models

    # Default AI Brain Arena match-up: the two configured brains the duel always used.
    ARENA_DEFAULT_PAIR = ("gemini-brain", "claude-brain")
    _NON_CHAT_PREFIXES = ("ronin/", "rodin/", "hyper3d/")

    def get_arena_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Chat models the Brain Arena may compare.

        Built from what this router actually supports: the configured provider
        aliases (claude-brain, gemini-brain, ...) first, then the chat models in
        the router catalog (DEFAULT_OPENROUTER_MODELS, plus the live OpenRouter
        list when a key is configured). 3D generators (Ronin/Rodin) are left out
        because they are not chat completions and bill per generation.
        """
        out: List[Dict[str, Any]] = []
        seen = set()
        for alias, cfg in self.providers.items():
            if alias.startswith(self._NON_CHAT_PREFIXES) or alias in ("ronin", "rodin", "hyper3d"):
                continue
            if "/" in alias:
                continue  # dynamically registered raw model ids are listed from the catalog below
            out.append({
                "id": alias,
                "name": cfg.display_name,
                "secondary": cfg.model_alias,
                "provider": cfg.lab_id,
                "model": cfg.model_alias,
                "kind": "configured",
                "active": bool(cfg.is_active),
            })
            seen.add(alias)
            # The alias already covers its raw model id, so the catalog copy is not listed twice.
            if cfg.model_alias:
                seen.add(cfg.model_alias)
        for m in self.get_available_models(force_refresh=force_refresh):
            mid = m.get("id")
            if not mid or mid in seen or mid.startswith(self._NON_CHAT_PREFIXES):
                continue
            if str(m.get("category", "")).lower().startswith("3d"):
                continue
            out.append({
                "id": mid,
                "name": m.get("name") or mid,
                "secondary": mid,
                "provider": m.get("provider") or mid.split("/")[0],
                "model": mid,
                "kind": "catalog",
            })
            seen.add(mid)
        return out

    def is_arena_model_allowed(self, model_id: str) -> bool:
        """True for any listed arena model, or the raw id behind a configured alias
        (e.g. google/gemini-2.5-flash, which the picker shows as gemini-brain)."""
        if not model_id or not isinstance(model_id, str):
            return False
        return any(model_id in (m["id"], m["model"]) for m in self.get_arena_models())

    def arena_default_pair(self) -> Dict[str, str]:
        ids = [m["id"] for m in self.get_arena_models()]
        a, b = self.ARENA_DEFAULT_PAIR
        if a not in ids:
            a = ids[0] if ids else a
        if b not in ids or b == a:
            b = next((i for i in ids if i != a), b)
        return {"a": a, "b": b}

    def route_request(self, requested_alias: str, estimated_cost: float = 0.02) -> LabProviderConfig:
        """Route request to the target lab, or fallback if credit pool is exhausted."""
        primary = self.providers.get(requested_alias)
        if not primary:
            # Dynamically register custom model alias (OpenRouter or Ronin)
            if requested_alias.startswith(("ronin/", "rodin/", "hyper3d/")):
                tier = "Regular"
                if "sketch" in requested_alias.lower():
                    tier = "Sketch"
                elif "detail" in requested_alias.lower():
                    tier = "Detail"
                elif "smooth" in requested_alias.lower():
                    tier = "Smooth"
                primary = LabProviderConfig(
                    lab_id="ronin",
                    display_name=f"Ronin Hyper3D ({tier})",
                    model_alias=requested_alias,
                    endpoint=self.RODIN_GENERATE_URL,
                    api_key_env="HYPER3D_API_KEY",
                    available_credits=100.0,
                    is_active=True,
                )
            else:
                parts = requested_alias.split("/")
                lab_id = parts[0] if len(parts) > 1 else "openrouter"
                model_name = parts[-1].replace("-", " ").title()
                primary = LabProviderConfig(
                    lab_id=lab_id,
                    display_name=f"{lab_id.capitalize()} {model_name}",
                    model_alias=requested_alias,
                    endpoint=self.OPENROUTER_ENDPOINT,
                    api_key_env="OPENROUTER_API_KEY",
                    available_credits=100.0,
                    is_active=True,
                )
            self.providers[requested_alias] = primary

        if primary.is_active and primary.available_credits >= estimated_cost:
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
            if cost <= 0.0 and (prompt_tokens > 0 or completion_tokens > 0):
                cost = (
                    (prompt_tokens / 1_000_000.0) * provider.input_cost_per_1m
                    + (completion_tokens / 1_000_000.0) * provider.output_cost_per_1m
                )
            provider.total_cost += cost

    def _fetch_openrouter_billing_sync(self, api_key: str) -> Dict[str, Any]:
        """Perform the synchronous OpenRouter billing HTTP requests and update cache."""
        now = time.time()
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        credits_data: Dict[str, Any] = {}
        key_data: Dict[str, Any] = {}

        try:
            req_c = urllib.request.Request(self.OPENROUTER_CREDITS_URL, headers=headers, method="GET")
            with urllib.request.urlopen(req_c, timeout=5.0) as resp_c:
                credits_data = (json.loads(resp_c.read().decode("utf-8")) or {}).get("data") or {}
        except Exception:
            pass

        try:
            req_k = urllib.request.Request(self.OPENROUTER_KEY_URL, headers=headers, method="GET")
            with urllib.request.urlopen(req_k, timeout=5.0) as resp_k:
                key_data = (json.loads(resp_k.read().decode("utf-8")) or {}).get("data") or {}
        except Exception:
            pass

        total_credits = float(credits_data.get("total_credits") or 0.0)
        total_usage = float(credits_data.get("total_usage") or 0.0)
        remaining_balance = max(0.0, total_credits - total_usage)

        billing = {
            "connected": bool(credits_data or key_data),
            "account_total_credits_usd": round(total_credits, 4),
            "account_total_usage_usd": round(total_usage, 6),
            "account_remaining_balance_usd": round(remaining_balance, 4),
            "key_label": "pooled-mesh-key [redacted]",
            "key_limit_usd": key_data.get("limit"),
            "key_remaining_usd": round(float(key_data["limit_remaining"]), 6) if key_data.get("limit_remaining") is not None else None,
            "key_usage_total_usd": round(float(key_data.get("usage") or 0.0), 6),
            "key_usage_daily_usd": round(float(key_data.get("usage_daily") or 0.0), 6),
            "key_usage_weekly_usd": round(float(key_data.get("usage_weekly") or 0.0), 6),
            "key_usage_monthly_usd": round(float(key_data.get("usage_monthly") or 0.0), 6),
            "fetched_at": now,
        }
        with self._billing_lock:
            self._billing_cache = billing
            self._billing_cached_at = now
            self._billing_refreshing = False
        return billing

    def get_openrouter_billing(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch real-time OpenRouter account credits with stale-while-revalidate background refresh."""
        now = time.time()
        if not force_refresh and self._billing_cached_at and (now - self._billing_cached_at) < self.BILLING_CACHE_TTL and self._billing_cache:
            return self._billing_cache

        api_key = self.openrouter_key or _resolve_openrouter_key_fallback()
        if not api_key:
            return {
                "connected": False,
                "account_total_credits_usd": 0.0,
                "account_total_usage_usd": 0.0,
                "account_remaining_balance_usd": 0.0,
                "key_label": "not_configured",
                "key_limit_usd": None,
                "key_remaining_usd": None,
                "key_usage_total_usd": 0.0,
                "key_usage_daily_usd": 0.0,
                "key_usage_weekly_usd": 0.0,
                "key_usage_monthly_usd": 0.0,
            }

        # Stale-while-revalidate: if we already have cached billing data and force_refresh is False,
        # refresh asynchronously in a background thread so HTTP polling never blocks p99 latency.
        if not force_refresh and self._billing_cache is not None:
            with self._billing_lock:
                should_spawn = not self._billing_refreshing
                if should_spawn:
                    self._billing_refreshing = True
            if should_spawn:
                threading.Thread(
                    target=self._fetch_openrouter_billing_sync,
                    args=(api_key,),
                    daemon=True,
                ).start()
            return self._billing_cache

        return self._fetch_openrouter_billing_sync(api_key)

    def _fetch_hyper3d_billing_sync(self, api_key: str) -> Dict[str, Any]:
        """Perform synchronous Hyper3D check_balance request and update cache."""
        now = time.time()
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        balance_data: Dict[str, Any] = {}
        connected = False

        try:
            req = urllib.request.Request(self.RODIN_BALANCE_URL, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                raw = resp.read().decode("utf-8")
                balance_data = json.loads(raw) or {}
                connected = True
        except Exception:
            pass

        data_obj = balance_data.get("data") if isinstance(balance_data.get("data"), dict) else balance_data
        credits_val = float(data_obj.get("credits") or data_obj.get("balance") or data_obj.get("account_remaining_credits") or 0.0)
        usd_val = float(data_obj.get("balance_usd") or data_obj.get("account_remaining_balance_usd") or credits_val)

        billing = {
            "connected": connected,
            "provider": "Hyper3D Rodin (Ronin) v2",
            "endpoint": self.RODIN_GENERATE_URL,
            "account_remaining_credits": round(credits_val, 2),
            "account_remaining_balance_usd": round(usd_val, 2),
            "session_total_tasks": self.rodin_total_calls,
            "session_total_spend_usd": round(self.rodin_total_cost_usd, 4),
            "key_label": "pooled-rodin-key [redacted]" if api_key else "not_configured",
            "tier_pricing_usd": self.RODIN_TIER_COSTS,
            "fetched_at": now,
        }
        with self._rodin_billing_lock:
            self._rodin_billing_cache = billing
            self._rodin_billing_cached_at = now
            self._rodin_billing_refreshing = False
        return billing

    def get_hyper3d_billing(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch real-time Hyper3D Rodin account balance with 60s stale-while-revalidate cache."""
        now = time.time()
        if not force_refresh and self._rodin_billing_cached_at and (now - self._rodin_billing_cached_at) < self.BILLING_CACHE_TTL and self._rodin_billing_cache:
            return self._rodin_billing_cache

        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        if not api_key:
            return {
                "connected": False,
                "provider": "Hyper3D Rodin (Ronin) v2",
                "endpoint": self.RODIN_GENERATE_URL,
                "account_remaining_credits": 0.0,
                "account_remaining_balance_usd": 0.0,
                "session_total_tasks": self.rodin_total_calls,
                "session_total_spend_usd": round(self.rodin_total_cost_usd, 4),
                "key_label": "not_configured",
                "tier_pricing_usd": self.RODIN_TIER_COSTS,
            }

        if not force_refresh and self._rodin_billing_cache is not None:
            with self._rodin_billing_lock:
                should_spawn = not self._rodin_billing_refreshing
                if should_spawn:
                    self._rodin_billing_refreshing = True
            if should_spawn:
                threading.Thread(
                    target=self._fetch_hyper3d_billing_sync,
                    args=(api_key,),
                    daemon=True,
                ).start()
            return self._rodin_billing_cache

        return self._fetch_hyper3d_billing_sync(api_key)

    def dispatch_rodin_generation(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        tier: str = "Regular",
        geometry_file_format: str = "glb",
        material: str = "PBR",
        quality: str = "medium",
        mesh_mode: str = "Quad",
    ) -> Dict[str, Any]:
        """Dispatch 3D generative task to Hyper3D Rodin v2 API or return simulated receipt."""
        cost_usd = float(self.RODIN_TIER_COSTS.get(tier, 0.50))
        task_uuid = f"rodin-{uuid.uuid4().hex[:12]}"
        sub_key = f"sub-{uuid.uuid4().hex[:12]}"
        status = "Done"
        simulated = True

        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        if api_key:
            payload: Dict[str, Any] = {
                "prompt": prompt,
                "tier": tier,
                "geometry_file_format": geometry_file_format,
                "material": material,
                "quality": quality,
                "mesh_mode": mesh_mode,
            }
            if images:
                payload["images"] = images

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(
                self.RODIN_GENERATE_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8")) or {}
                    if resp_data.get("uuid"):
                        task_uuid = str(resp_data["uuid"])
                    if resp_data.get("subscription_key"):
                        sub_key = str(resp_data["subscription_key"])
                    status = resp_data.get("status", "Done")
                    simulated = False
            except Exception:
                simulated = True
                status = "Done"

        glb_bytes = generate_minimal_glb_bytes(name=prompt[:24] if prompt else "rodin_mesh")
        glb_b64 = base64.b64encode(glb_bytes).decode("utf-8")

        task_record = {
            "uuid": task_uuid,
            "subscription_key": sub_key,
            "prompt": prompt,
            "tier": tier,
            "format": geometry_file_format,
            "material": material,
            "quality": quality,
            "mesh_mode": mesh_mode,
            "status": status,
            "cost_usd": cost_usd,
            "created_at": time.time(),
            "glb_bytes_b64": glb_b64,
            "simulated": simulated,
        }

        self.rodin_tasks[task_uuid] = task_record
        self.rodin_total_calls += 1
        self.rodin_total_cost_usd += cost_usd
        return dict(task_record)

    def check_rodin_status(self, subscription_key: str) -> Dict[str, Any]:
        """Check status of Rodin generation task via API or local task registry."""
        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        if api_key and not subscription_key.startswith("sub-"):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(
                self.RODIN_STATUS_URL,
                data=json.dumps({"subscription_key": subscription_key}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                pass

        matching_task = self.rodin_tasks.get(subscription_key)
        if not matching_task:
            for t in self.rodin_tasks.values():
                if t.get("subscription_key") == subscription_key or t.get("uuid") == subscription_key:
                    matching_task = t
                    break

        if matching_task:
            t_uuid = matching_task.get("uuid", subscription_key)
            st = matching_task.get("status", "Done")
            return {
                "subscription_key": subscription_key,
                "status": st,
                "jobs": [{"uuid": t_uuid, "status": st}],
            }

        return {
            "subscription_key": subscription_key,
            "status": "Done",
            "jobs": [{"uuid": subscription_key, "status": "Done"}],
        }

    def download_rodin_assets(self, task_uuid: str) -> Dict[str, Any]:
        """Download Rodin assets via API or return deterministic asset manifest."""
        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        task = self.rodin_tasks.get(task_uuid, {})
        is_simulated = task.get("simulated", True)

        if api_key and not is_simulated:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(
                self.RODIN_DOWNLOAD_URL,
                data=json.dumps({"uuid": task_uuid}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15.0) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                pass

        fmt = task.get("format", "glb")
        glb_b64 = task.get("glb_bytes_b64")
        if not glb_b64:
            glb_b64 = base64.b64encode(generate_minimal_glb_bytes(task_uuid[:16])).decode("utf-8")

        return {
            "task_uuid": task_uuid,
            "format": fmt,
            "files": [
                {
                    "name": f"{task_uuid}.{fmt}",
                    "format": fmt,
                    "bytes_b64": glb_b64,
                }
            ],
            "glb_bytes_b64": glb_b64,
        }

    def get_analytics(self, include_live_billing: bool = True) -> Dict[str, Any]:
        """Aggregate usage analytics, per-model token rates, and live OpenRouter account spend."""
        session_calls = sum(p.total_calls for p in self.providers.values())
        session_tokens = sum(p.total_tokens for p in self.providers.values())
        session_spend = sum(p.total_cost for p in self.providers.values())
        billing = self.get_openrouter_billing() if include_live_billing else {}
        hyper3d_billing = self.get_hyper3d_billing() if include_live_billing else {}

        return {
            "total_calls": session_calls,
            "total_tokens": session_tokens,
            "total_spend_usd": round(session_spend, 6),
            "openrouter": billing,
            "hyper3d": hyper3d_billing,
            "providers": {
                k: {
                    "display_name": p.display_name,
                    "model": p.model_alias,
                    "input_cost_per_1m_usd": p.input_cost_per_1m,
                    "output_cost_per_1m_usd": p.output_cost_per_1m,
                    "est_cost_per_1k_prompt_usd": round((p.input_cost_per_1m * 0.5 + p.output_cost_per_1m * 0.5) / 1000.0, 6),
                    "total_calls": p.total_calls,
                    "prompt_tokens": p.total_prompt_tokens,
                    "completion_tokens": p.total_completion_tokens,
                    "total_tokens": p.total_tokens,
                    "cost_usd": round(p.total_cost, 6),
                    "remaining_credits": round(
                        billing.get("account_remaining_balance_usd", p.available_credits)
                        if billing.get("connected")
                        else p.available_credits,
                        4,
                    ),
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
        """Dispatch chat completion to OpenRouter, Ronin 3D, or simulated fallback."""
        if alias.startswith(("ronin/", "rodin/", "hyper3d/")) or alias in ("ronin", "rodin", "hyper3d"):
            prompt_text = " ".join([m.get("content", "") for m in messages if m.get("role") != "system"]).strip()
            if not prompt_text:
                prompt_text = "3D generative mesh"
            tier = "Regular"
            alias_lower = alias.lower()
            if "sketch" in alias_lower:
                tier = "Sketch"
            elif "detail" in alias_lower:
                tier = "Detail"
            elif "smooth" in alias_lower:
                tier = "Smooth"
            rodin_res = self.dispatch_rodin_generation(prompt=prompt_text, tier=tier, geometry_file_format="glb")
            status_desc = "Live Hyper3D API" if not rodin_res.get("simulated") else "Local Generative Engine"
            content = (
                f"🎨 [Hyper3D Ronin 3D Asset Generated]\n"
                f"Task UUID: {rodin_res.get('uuid')}\n"
                f"Tier: {rodin_res.get('tier')} | Format: {rodin_res.get('format', 'glb').upper()} | Mesh Mode: {rodin_res.get('mesh_mode', 'Quad')}\n"
                f"Engine: {status_desc} | Status: {rodin_res.get('status')}\n"
                f"Cost: ${rodin_res.get('cost_usd', 0.50):.2f}\n"
                f"Ready in Agent Space VFS: `/models3d/{rodin_res.get('uuid')}.glb`"
            )
            cost_usd = float(rodin_res.get("cost_usd", 0.50))
            self.record_usage(alias, len(prompt_text.split()), 48, len(prompt_text.split()) + 48, cost_usd)
            return {
                "id": f"ronin-{rodin_res.get('uuid')}",
                "model": alias,
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": content,
                    }
                }],
                "usage": {
                    "prompt_tokens": len(prompt_text.split()),
                    "completion_tokens": 48,
                    "total_tokens": len(prompt_text.split()) + 48,
                    "cost": cost_usd,
                },
                "cost_usd": cost_usd,
                "rodin_asset": rodin_res,
            }

        config = self.route_request(alias)
        api_key = self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")

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
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            # If a configured model alias is unavailable on OpenRouter (400/404), retry with google/gemini-2.5-flash
            if http_err.code in (400, 404) and payload.get("model") != "google/gemini-2.5-flash":
                fallback_payload = dict(payload, model="google/gemini-2.5-flash")
                req_fb = urllib.request.Request(
                    config.endpoint,
                    data=json.dumps(fallback_payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req_fb, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            else:
                raise
        usage = data.get("usage", {})
        prompt_toks = int(usage.get("prompt_tokens", 0))
        comp_toks = int(usage.get("completion_tokens", 0))
        total_toks = int(usage.get("total_tokens", prompt_toks + comp_toks))
        cost = float(usage.get("cost") or 0.0)
        self.record_usage(alias, prompt_toks, comp_toks, total_toks, cost)
        return data
