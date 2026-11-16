"""Dynamic Multi-Lab AI Gateway Router and Live OpenRouter Cost & Credit Dashboard."""

from __future__ import annotations

import base64
import json
import os
import re
import struct
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
OWLCHAT_BASE_URL = "https://chat.hpc.fau.edu/openai"
TRUSSED_AI_BASE_URL = "https://trussed.ai.hpc.fau.edu/provider/generic"


def normalize_openai_compat_base_url(base_url: str, *, default_v1: bool = False) -> str:
    """Normalize an OpenAI-compatible base URL, stripping trailing endpoint paths."""
    cleaned = (base_url or "").strip().rstrip("/")
    if not cleaned:
        return DEFAULT_OLLAMA_BASE_URL if default_v1 else ""
    if "://" not in cleaned:
        cleaned = f"http://{cleaned}"
    for suffix in ("/chat/completions", "/models"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].rstrip("/")
            break
    if default_v1:
        parsed = urllib.parse.urlparse(cleaned)
        if not parsed.path or parsed.path == "/":
            cleaned = f"{cleaned}/v1"
    return cleaned


def build_chat_completions_url(base_url: str, *, default_v1: bool = False) -> str:
    """Return the /chat/completions endpoint URL for an OpenAI-compatible base URL."""
    base = normalize_openai_compat_base_url(base_url, default_v1=default_v1)
    return f"{base}/chat/completions"


def build_models_url(base_url: str, *, default_v1: bool = False) -> str:
    """Return the /models endpoint URL for an OpenAI-compatible base URL."""
    base = normalize_openai_compat_base_url(base_url, default_v1=default_v1)
    return f"{base}/models"


def resolve_ollama_base_url(override: Optional[str] = None) -> str:
    """Resolve the local Ollama OpenAI-compatible /v1 base URL."""
    raw = override or os.environ.get("TINCAN_OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or DEFAULT_OLLAMA_BASE_URL
    return normalize_openai_compat_base_url(raw, default_v1=True)


def resolve_owlchat_key(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve an FAU OwlChat API key from explicit input or environment."""
    return explicit or os.environ.get("OWLCHAT_API_KEY") or os.environ.get("FAU_OWLCHAT_API_KEY") or os.environ.get("OPENAI_API_KEY")


def resolve_trussed_key(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve an FAU Trussed AI API key from explicit input or environment."""
    return explicit or os.environ.get("TRUSSED_AI_API_KEY") or os.environ.get("OWLCHAT_API_KEY") or os.environ.get("OPENAI_API_KEY")


def resolve_local_compat_key(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve an optional API key for a local or custom OpenAI-compatible server."""
    return explicit or os.environ.get("TINCAN_AI_API_KEY") or os.environ.get("OLLAMA_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _resolve_openrouter_key_fallback() -> Optional[str]:
    """Resolve OPENROUTER_API_KEY strictly from environment (CLI subprocess scraping disabled)."""
    return os.environ.get("OPENROUTER_API_KEY")


def _resolve_nanogpt_key_fallback() -> Optional[str]:
    """Resolve NANOGPT_API_KEY strictly from environment."""
    return os.environ.get("NANOGPT_API_KEY")


def _resolve_hyper3d_key_fallback() -> Optional[str]:
    """Resolve Hyper3D / Rodin API key from environment."""
    return os.environ.get("HYPER3D_API_KEY") or os.environ.get("RODIN_API_KEY")


def _normalize_nanogpt_pricing(pricing: Any) -> Dict[str, Any]:
    """Normalize NanoGPT per-1M token pricing into OpenRouter-compatible per-token fields."""
    if not isinstance(pricing, dict):
        return {"prompt": "0", "completion": "0", "prompt_per_1m": 0.0, "completion_per_1m": 0.0}
    unit = str(pricing.get("unit") or "").lower()
    raw_p = pricing.get("prompt")
    raw_c = pricing.get("completion")
    try:
        p_val = float(raw_p) if raw_p is not None else 0.0
    except (TypeError, ValueError):
        p_val = 0.0
    try:
        c_val = float(raw_c) if raw_c is not None else 0.0
    except (TypeError, ValueError):
        c_val = 0.0

    # NanoGPT's ?detailed=true endpoint reports USD per million tokens; convert to per-token strings.
    if unit == "per_million_tokens" or p_val >= 0.001 or c_val >= 0.001:
        p_per_1m, c_per_1m = p_val, c_val
        p_per_tok, c_per_tok = p_val / 1_000_000.0, c_val / 1_000_000.0
    else:
        p_per_tok, c_per_tok = p_val, c_val
        p_per_1m, c_per_1m = p_val * 1_000_000.0, c_val * 1_000_000.0

    return {
        "prompt": f"{p_per_tok:.12g}",
        "completion": f"{c_per_tok:.12g}",
        "prompt_per_1m": round(p_per_1m, 6),
        "completion_per_1m": round(c_per_1m, 6),
        "currency": pricing.get("currency", "USD"),
        "unit": "per_token",
    }


def filter_gateway_models(
    models: List[Dict[str, Any]],
    *,
    category: Optional[str] = None,
    exact_category: bool = False,
    uncensored: bool = False,
    tee: bool = False,
    subscription: bool = False,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter normalized gateway model descriptors by category, privacy/uncensored flags, and query."""
    result = list(models)
    cat = (category or "").strip().lower()
    if cat:
        if exact_category:
            result = [m for m in result if str(m.get("category", "")).lower() == cat]
        else:
            result = [m for m in result if cat in str(m.get("category", "")).lower()]
    if uncensored:
        result = [
            m
            for m in result
            if "uncensor" in str(m.get("category", "")).lower()
            or any(k in str(m.get("id", "")).lower() for k in ("abliterat", "heretic", "uncensor"))
        ]
    if tee:
        result = [
            m
            for m in result
            if "tee" in str(m.get("category", "")).lower()
            or "/tee/" in str(m.get("id", "")).lower()
        ]
    if subscription:
        result = [m for m in result if m.get("subscription_included")]
    q = (search or "").strip().lower()
    if q:
        result = [
            m
            for m in result
            if q in str(m.get("id", "")).lower()
            or q in str(m.get("name", "")).lower()
            or q in str(m.get("description", "")).lower()
        ]
    return result


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
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B Instruct (:free)",
        "provider": "Meta · OpenRouter Free",
        "description": "Zero-cost OpenRouter :free tier model ideal for instant board suggestions and routing hints.",
        "category": "Free",
        "context_length": 131072,
        "pricing": {"prompt": "0.0", "completion": "0.0"},
    },
    {
        "id": "qwen/qwen-2.5-72b-instruct:free",
        "name": "Qwen 2.5 72B Instruct (:free)",
        "provider": "Qwen · OpenRouter Free",
        "description": "Zero-cost OpenRouter :free tier model for structured suggestions and tag completion.",
        "category": "Free",
        "context_length": 32768,
        "pricing": {"prompt": "0.0", "completion": "0.0"},
    },
    # OpenRouter 2D Image Generative models
    {
        "id": "google/gemini-2.5-flash-image",
        "name": "Google Gemini 2.5 Flash Image",
        "provider": "Google",
        "description": "Fast 2D raster image generation and editing via OpenRouter multimodal completions.",
        "category": "2D Image Generative",
        "context_length": 32768,
        "output_modalities": ["image", "text"],
        "pricing": {"prompt": "0.0000003", "completion": "0.0000025", "image": "0.039"},
    },
    {
        "id": "google/gemini-3.1-flash-image-preview",
        "name": "Google Gemini 3.1 Flash Image Preview",
        "provider": "Google",
        "description": "High-detail 2D image generation via OpenRouter.",
        "category": "2D Image Generative",
        "context_length": 65536,
        "output_modalities": ["image", "text"],
        "pricing": {"prompt": "0.0000005", "completion": "0.000003"},
    },
    {
        "id": "openai/gpt-5-image-mini",
        "name": "OpenAI GPT-5 Image Mini",
        "provider": "OpenAI",
        "description": "Fast instruction-following 2D raster image generator via OpenRouter.",
        "category": "2D Image Generative",
        "context_length": 32768,
        "output_modalities": ["image", "text"],
        "pricing": {"prompt": "0.0000025", "completion": "0.000008"},
    },
]


DEFAULT_NANOGPT_MODELS: List[Dict[str, Any]] = [
    {
        "id": "nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
        "upstream_id": "pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
        "name": "NanoGPT DeepSeek V4.1 Flash Heretic",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Heretic directional-ablation DeepSeek V4.1 Flash with 512k context and reasoning.",
        "category": "Uncensored",
        "context_length": 512000,
        "open_weights": True,
        "subscription_included": True,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.198, "completion": 0.792, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/abliteration-ai/abliterated-model-large-v2",
        "upstream_id": "abliteration-ai/abliterated-model-large-v2",
        "name": "NanoGPT Abliterated Large V2",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Flagship 1M-context abliterated generalist with reasoning and tool calling.",
        "category": "Uncensored",
        "context_length": 1000000,
        "open_weights": True,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 3.0, "completion": 5.0, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/abliteration-ai/abliterated-model-large-flash",
        "upstream_id": "abliteration-ai/abliterated-model-large-flash",
        "name": "NanoGPT Abliterated Large Flash",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Fast 1M-context abliterated multimodal reasoning model.",
        "category": "Uncensored",
        "context_length": 1048576,
        "open_weights": True,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 1.0, "completion": 2.0, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/z-ai/glm-5.3-flash-apex-abliterated",
        "upstream_id": "z-ai/glm-5.3-flash-apex-abliterated",
        "name": "NanoGPT GLM-5.3 Flash Apex Abliterated",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "1M-context abliterated GLM-5.3 Flash Apex variant.",
        "category": "Uncensored",
        "context_length": 1048576,
        "open_weights": True,
        "subscription_included": True,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.15, "completion": 0.5, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/xiaomi/mimo-v2.6-flash-abliterated",
        "upstream_id": "xiaomi/mimo-v2.6-flash-abliterated",
        "name": "NanoGPT MiMo V2.6 Flash Abliterated",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "1M-context abliterated MiMo V2.6 Flash model.",
        "category": "Uncensored",
        "context_length": 1048576,
        "open_weights": True,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.5, "completion": 1.5, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
        "upstream_id": "Gemma-4-31B-Gembrain-uncensored-heretic",
        "name": "NanoGPT Gemma 4 31B Gembrain Heretic",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "262k-context Gemma 4 31B Heretic uncensored generalist.",
        "category": "Uncensored",
        "context_length": 262144,
        "open_weights": True,
        "subscription_included": True,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.306, "completion": 0.306, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/huihui-ai/Llama-3.3-70B-Instruct-abliterated",
        "upstream_id": "huihui-ai/Llama-3.3-70B-Instruct-abliterated",
        "name": "NanoGPT Llama 3.3 70B Abliterated",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Huihui-AI refusal-ablated Llama 3.3 70B Instruct.",
        "category": "Uncensored",
        "context_length": 32768,
        "open_weights": True,
        "subscription_included": True,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.7, "completion": 0.7, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/TEE/deepseek-v4.1-flash",
        "upstream_id": "TEE/deepseek-v4.1-flash",
        "name": "NanoGPT Private/TEE DeepSeek V4.1 Flash",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Hardware-attested TEE DeepSeek V4.1 Flash on NanoGPT.",
        "category": "Private/TEE",
        "context_length": 1048576,
        "open_weights": True,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.375, "completion": 1.5, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/TEE/gemma-4-26b-a4b-uncensored",
        "upstream_id": "TEE/gemma-4-26b-a4b-uncensored",
        "name": "NanoGPT Private/TEE Gemma 4 26B Uncensored",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Hardware-attested TEE Gemma 4 26B A4B Uncensored on NanoGPT.",
        "category": "Private/TEE",
        "context_length": 65536,
        "open_weights": True,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.15, "completion": 0.7, "unit": "per_million_tokens"}),
    },
    {
        "id": "nanogpt/auto-model",
        "upstream_id": "auto-model",
        "name": "NanoGPT Auto Router",
        "provider": "NanoGPT",
        "gateway": "nanogpt",
        "description": "Automatic prompt-aware model routing across NanoGPT's catalog.",
        "category": "NanoGPT",
        "context_length": 128000,
        "open_weights": False,
        "subscription_included": False,
        "pricing": _normalize_nanogpt_pricing({"prompt": 0.5, "completion": 1.5, "unit": "per_million_tokens"}),
    },
]


class DynamicAIGatewayRouter:
    """Manages hot-swappable AI provider models, live OpenRouter/NanoGPT billing/credits, and per-call cost tracking."""

    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"
    OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/auth/key"

    NANOGPT_BASE_URL = "https://api.nano-gpt.com"
    NANOGPT_ENDPOINT = "https://api.nano-gpt.com/api/v1/chat/completions"
    NANOGPT_IMAGE_ENDPOINT = "https://api.nano-gpt.com/api/v1/images/generations"
    NANOGPT_MEDIA_SUBMIT_URL = "https://api.nano-gpt.com/api/generate-video"
    NANOGPT_MEDIA_STATUS_URL = "https://api.nano-gpt.com/api/video/status"
    NANOGPT_3D_MODELS_URL = "https://api.nano-gpt.com/api/v1/3d-models"
    NANOGPT_MODELS_URL = "https://api.nano-gpt.com/api/v1/models?detailed=true"
    NANOGPT_BALANCE_URL = "https://api.nano-gpt.com/api/check-balance"
    DEFAULT_IMAGE_MODEL = "google/gemini-2.5-flash-image"
    FALLBACK_IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"
    TERTIARY_IMAGE_MODEL = "openai/gpt-5-image-mini"
    NANOGPT_DEFAULT_IMAGE_MODEL = "minimax-h3-image"
    NANOGPT_FALLBACK_IMAGE_MODEL = "blackforestlabs/flux-3/klein/text-to-image"
    NANOGPT_DEFAULT_RODIN_MODEL = "hyper3d/rodin-v2.5"
    NANOGPT_3D_FALLBACK_MODELS = (
        "hyper3d/rodin-v2.5",
        "tripo3d/h3.0",
        "wavespeed-ai/hunyuan-3d-v3.1-rapid",
    )

    # Hyper3D Rodin (Ronin) v2 3D Generation Endpoints
    RODIN_GENERATE_URL = "https://api.hyper3d.com/api/v2/rodin"
    RODIN_FALLBACK_GENERATE_URL = "https://hyperhuman.deemos.com/api/v2/rodin"
    RODIN_STATUS_URL = "https://api.hyper3d.com/api/v2/status"
    RODIN_DOWNLOAD_URL = "https://api.hyper3d.com/api/v2/download"
    RODIN_BALANCE_URL = "https://api.hyper3d.com/api/v2/check_balance"
    RODIN_TIER_COSTS = {"Regular": 0.50, "Sketch": 0.25, "Detail": 1.00, "Smooth": 0.75}

    # Local & OpenAI-Compatible Institutional Endpoints
    DEFAULT_OLLAMA_BASE_URL = DEFAULT_OLLAMA_BASE_URL
    OWLCHAT_BASE_URL = OWLCHAT_BASE_URL
    TRUSSED_AI_BASE_URL = TRUSSED_AI_BASE_URL
    _OPENAI_COMPAT_GATEWAYS = ("ollama", "owlchat", "trussed", "local")
    _COMPAT_PREFIXES = ("ollama/", "owlchat/", "trussed/", "local/", "openai-compat/")

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
        "nanogpt-brain": LabProviderConfig(
            lab_id="nanogpt",
            display_name="NanoGPT DeepSeek Heretic",
            model_alias="nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
            endpoint=NANOGPT_ENDPOINT,
            api_key_env="NANOGPT_API_KEY",
            available_credits=100.0,
            is_active=True,
            input_cost_per_1m=0.198,
            output_cost_per_1m=0.792,
        ),
    }

    def __init__(
        self,
        openrouter_key: Optional[str] = None,
        hyper3d_key: Optional[str] = None,
        nanogpt_key: Optional[str] = None,
        *,
        ollama_base_url: Optional[str] = None,
        local_base_url: Optional[str] = None,
        local_api_key: Optional[str] = None,
        owlchat_key: Optional[str] = None,
        trussed_key: Optional[str] = None,
    ):
        self.openrouter_key = openrouter_key if openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")
        self.hyper3d_key = hyper3d_key if hyper3d_key is not None else _resolve_hyper3d_key_fallback()
        self.nanogpt_key = nanogpt_key if nanogpt_key is not None else os.environ.get("NANOGPT_API_KEY")
        self.ollama_base_url = resolve_ollama_base_url(ollama_base_url)
        raw_local_base = local_base_url or os.environ.get("TINCAN_AI_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        self.local_base_url = normalize_openai_compat_base_url(raw_local_base) if raw_local_base else None
        self.local_api_key = local_api_key
        self.owlchat_key = owlchat_key
        self.trussed_key = trussed_key
        self.providers: Dict[str, LabProviderConfig] = {
            k: LabProviderConfig(**asdict(v)) for k, v in self.DEFAULT_LABS.items()
        }
        self.routing_log: List[Dict[str, Any]] = []
        self._billing_cache: Optional[Dict[str, Any]] = None
        self._billing_cached_at: float = 0.0
        self._billing_refreshing: bool = False
        self._billing_lock = threading.Lock()
        self.BILLING_CACHE_TTL: float = 60.0

        # NanoGPT billing & catalog caches
        self._nanogpt_billing_cache: Optional[Dict[str, Any]] = None
        self._nanogpt_billing_cached_at: float = 0.0
        self._nanogpt_billing_refreshing: bool = False
        self._nanogpt_billing_lock = threading.Lock()
        self._nanogpt_models_cache: Optional[List[Dict[str, Any]]] = None
        self._nanogpt_models_cached_at: float = 0.0
        self._nanogpt_models_live_cached: bool = False
        self._nanogpt_upstream_ids: set = {
            str(m.get("upstream_id") or "") for m in DEFAULT_NANOGPT_MODELS if m.get("upstream_id")
        }

        # Hyper3D Rodin state & caching
        self.rodin_tasks: Dict[str, Dict[str, Any]] = {}
        self.rodin_total_calls: int = 0
        self.rodin_total_cost_usd: float = 0.0
        self._rodin_billing_cache: Optional[Dict[str, Any]] = None
        self._rodin_billing_cached_at: float = 0.0
        self._rodin_billing_refreshing: bool = False
        self._rodin_billing_lock = threading.Lock()

        # Available models cache (OpenRouter + NanoGPT + Ronin)
        self._available_models_cache: Optional[List[Dict[str, Any]]] = None
        self._available_models_cached_at: float = 0.0

    @staticmethod
    def _strip_nanogpt_prefix(model_id: str) -> str:
        return model_id[len("nanogpt/"):] if model_id.startswith("nanogpt/") else model_id

    @classmethod
    def _strip_compat_prefix(cls, model_id: str) -> str:
        for prefix in cls._COMPAT_PREFIXES:
            if model_id.startswith(prefix):
                return model_id[len(prefix):]
        return model_id

    def _detect_compat_gateway(
        self,
        alias_or_model: str,
        gateway: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Optional[str]:
        """Identify whether a model/gateway targets Ollama, FAU OwlChat, Trussed AI, or custom OpenAI-compat."""
        gw = (gateway or "").strip().lower()
        if gw in ("openrouter", "nanogpt", "ronin", "hyper3d"):
            return None
        if gw == "openai-compat":
            return "local"
        if gw in self._OPENAI_COMPAT_GATEWAYS:
            return gw
        m = (alias_or_model or "").strip()
        if m.startswith("ollama/") or m == "ollama-brain":
            return "ollama"
        if m.startswith("owlchat/") or m == "owlchat-brain":
            return "owlchat"
        if m.startswith("trussed/") or m == "trussed-brain":
            return "trussed"
        if m.startswith(("local/", "openai-compat/")) or m == "local-brain":
            return "local"
        if base_url:
            low_u = base_url.lower()
            if "chat.hpc.fau.edu" in low_u:
                return "owlchat"
            if "trussed.ai.hpc.fau.edu" in low_u:
                return "trussed"
            if ":11434" in low_u:
                return "ollama"
            return "local"
        return None

    def _resolve_compat_spec(self, gw: str, base_url: Optional[str] = None) -> tuple[str, str, str]:
        """Return (chat_completions_endpoint, api_key_env, display_label) for a compat gateway."""
        table = {
            "ollama": (
                build_chat_completions_url(base_url or self.ollama_base_url, default_v1=True),
                "OLLAMA_API_KEY",
                "Ollama (Local)",
            ),
            "owlchat": (
                build_chat_completions_url(base_url or self.OWLCHAT_BASE_URL),
                "OWLCHAT_API_KEY",
                "FAU OwlChat",
            ),
            "trussed": (
                build_chat_completions_url(base_url or self.TRUSSED_AI_BASE_URL),
                "TRUSSED_AI_API_KEY",
                "FAU Trussed AI",
            ),
            "local": (
                build_chat_completions_url(base_url or self.local_base_url or self.ollama_base_url, default_v1=False),
                "TINCAN_AI_API_KEY",
                "Local / OpenAI-Compatible",
            ),
        }
        return table[gw]

    def _build_compat_config(
        self,
        alias_or_model: str,
        gw: str,
        *,
        base_url: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> LabProviderConfig:
        endpoint, key_env, label = self._resolve_compat_spec(gw, base_url=base_url)
        clean_model = self._strip_compat_prefix(alias_or_model)
        return LabProviderConfig(
            lab_id=gw,
            display_name=display_name or f"{label}: {clean_model}",
            model_alias=alias_or_model,
            endpoint=endpoint,
            api_key_env=key_env,
            available_credits=1000.0,
            is_active=True,
            input_cost_per_1m=0.0,
            output_cost_per_1m=0.0,
        )

    def _provider_gateway(self, p: LabProviderConfig) -> str:
        if p.api_key_env == "NANOGPT_API_KEY" or p.endpoint == self.NANOGPT_ENDPOINT:
            return "nanogpt"
        if p.api_key_env == "HYPER3D_API_KEY":
            return "hyper3d"
        if p.lab_id in self._OPENAI_COMPAT_GATEWAYS:
            return p.lab_id
        if p.api_key_env == "OLLAMA_API_KEY":
            return "ollama"
        if p.api_key_env == "OWLCHAT_API_KEY":
            return "owlchat"
        if p.api_key_env == "TRUSSED_AI_API_KEY":
            return "trussed"
        if p.api_key_env == "TINCAN_AI_API_KEY":
            return "local"
        return "openrouter"

    def _is_nanogpt_model(self, model_id: str) -> bool:
        if not model_id or not isinstance(model_id, str):
            return False
        if model_id.startswith("nanogpt/"):
            return True
        if model_id in self._nanogpt_upstream_ids:
            return True
        low = model_id.lower()
        return model_id.startswith(("abliteration-ai/", "huihui-ai/", "TEE/", "pqhaz/", "xtools-at/")) or (
            "abliterated" in low or low.endswith("-heretic") or "-heretic:" in low
        )

    def _lookup_catalog_rates(self, model_id: str) -> Optional[tuple]:
        candidates = {model_id, self._strip_nanogpt_prefix(model_id), f"nanogpt/{self._strip_nanogpt_prefix(model_id)}"}
        pools: List[List[Dict[str, Any]]] = [DEFAULT_OPENROUTER_MODELS, DEFAULT_NANOGPT_MODELS]
        if self._available_models_cache:
            pools.append(self._available_models_cache)
        if self._nanogpt_models_cache:
            pools.append(self._nanogpt_models_cache)
        for pool in pools:
            for item in pool:
                if item.get("id") in candidates or item.get("upstream_id") in candidates:
                    pricing = item.get("pricing") or {}
                    try:
                        if "prompt_per_1m" in pricing or "completion_per_1m" in pricing:
                            return (
                                float(pricing.get("prompt_per_1m") or 0.0),
                                float(pricing.get("completion_per_1m") or 0.0),
                            )
                        p_raw = str(pricing.get("prompt") or "0")
                        c_raw = str(pricing.get("completion") or "0")
                        if "/gen" in p_raw:
                            continue
                        return (float(p_raw) * 1_000_000.0, float(c_raw) * 1_000_000.0)
                    except (TypeError, ValueError):
                        return None
        return None

    def get_nanogpt_models(
        self,
        force_refresh: bool = False,
        include_live_public: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return NanoGPT model catalog, fetching live /api/v1/models?detailed=true when key is set or public sync is requested."""
        now = time.time()
        api_key = self.nanogpt_key if self.nanogpt_key is not None else _resolve_nanogpt_key_fallback()
        want_live = bool(api_key or include_live_public)

        if (
            not force_refresh
            and self._nanogpt_models_cache is not None
            and (now - self._nanogpt_models_cached_at < 600.0)
            and (not want_live or self._nanogpt_models_live_cached)
        ):
            return list(self._nanogpt_models_cache)

        models = [dict(m) for m in DEFAULT_NANOGPT_MODELS]
        live_fetched = False

        if want_live:
            try:
                headers = {"Accept": "application/json", "User-Agent": "TinCan-Mesh-OS/2.2"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                    headers["x-api-key"] = api_key
                req = urllib.request.Request(self.NANOGPT_MODELS_URL, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_list = data.get("data", []) if isinstance(data, dict) else []
                    known_ids = {m["id"] for m in models}
                    for item in raw_list:
                        raw_id = item.get("id")
                        if not raw_id:
                            continue
                        self._nanogpt_upstream_ids.add(raw_id)
                        prefixed_id = raw_id if raw_id.startswith("nanogpt/") else f"nanogpt/{raw_id}"
                        if prefixed_id in known_ids:
                            continue
                        sub_info = item.get("subscription") or {}
                        models.append({
                            "id": prefixed_id,
                            "upstream_id": raw_id,
                            "name": item.get("name") or raw_id,
                            "provider": "NanoGPT",
                            "gateway": "nanogpt",
                            "description": item.get("description", ""),
                            "context_length": item.get("context_length", 8192),
                            "max_output_tokens": item.get("max_output_tokens"),
                            "category": item.get("category") or "NanoGPT",
                            "open_weights": bool(item.get("open_weights")),
                            "subscription_included": bool(sub_info.get("included")),
                            "pricing": _normalize_nanogpt_pricing(item.get("pricing")),
                        })
                        known_ids.add(prefixed_id)
                    live_fetched = True
            except Exception:
                pass

        self._nanogpt_models_cache = models
        self._nanogpt_models_cached_at = now
        self._nanogpt_models_live_cached = live_fetched
        return list(models)

    def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Return full catalog of OpenRouter, NanoGPT, and Ronin/Hyper3D models with caching."""
        now = time.time()
        if not force_refresh and self._available_models_cache and (now - self._available_models_cached_at < 600.0):
            return list(self._available_models_cache)

        models = [dict(m, gateway=m.get("gateway") or ("ronin" if m["id"].startswith("ronin/") else "openrouter")) for m in DEFAULT_OPENROUTER_MODELS]
        known_ids = {m["id"] for m in models}
        api_key = self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")

        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
                req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_list = data.get("data", [])
                    for item in raw_list:
                        m_id = item.get("id")
                        if m_id and m_id not in known_ids:
                            pricing = item.get("pricing", {})
                            models.append({
                                "id": m_id,
                                "name": item.get("name") or m_id,
                                "provider": m_id.split("/")[0].capitalize(),
                                "gateway": "openrouter",
                                "description": item.get("description", ""),
                                "context_length": item.get("context_length", 8192),
                                "category": "OpenRouter",
                                "pricing": pricing,
                            })
                            known_ids.add(m_id)
            except Exception:
                pass

        for ng_m in self.get_nanogpt_models(force_refresh=force_refresh, include_live_public=False):
            m_id = ng_m.get("id")
            if m_id and m_id not in known_ids:
                models.append(ng_m)
                known_ids.add(m_id)

        self._available_models_cache = models
        self._available_models_cached_at = now
        return models

    def get_openai_compat_models(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        gateway_name: str = "local",
        prefix: str = "local",
        timeout: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """Query an OpenAI-compatible /models endpoint (OwlChat, vLLM, LM Studio, Ollama /v1)."""
        models_url = build_models_url(base_url, default_v1=(gateway_name == "ollama"))
        headers = {"Accept": "application/json", "User-Agent": "TinCan-Mesh-OS/2.2"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        out: List[Dict[str, Any]] = []
        try:
            req = urllib.request.Request(models_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return out
        raw_list = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            raw_id = item.get("id") or item.get("name")
            if not raw_id:
                continue
            prefixed_id = raw_id if raw_id.startswith(f"{prefix}/") else f"{prefix}/{raw_id}"
            out.append({
                "id": prefixed_id,
                "upstream_id": raw_id,
                "name": item.get("name") or raw_id,
                "provider": gateway_name.capitalize(),
                "gateway": gateway_name,
                "description": item.get("description") or f"OpenAI-compatible model via {base_url}",
                "context_length": item.get("context_length", 8192),
                "category": "FAU OwlChat" if gateway_name == "owlchat" else "Local / Open-Weight",
                "open_weights": True,
                "pricing": {"prompt": "0", "completion": "0", "prompt_per_1m": 0.0, "completion_per_1m": 0.0},
            })
        return out

    def get_ollama_models(
        self,
        base_url: Optional[str] = None,
        timeout: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Discover models pulled on a local/tunneled Ollama instance without failing if stopped."""
        resolved = resolve_ollama_base_url(base_url or self.ollama_base_url)
        origin = resolved[:-3] if resolved.endswith("/v1") else resolved
        tags_url = f"{origin}/api/tags"
        try:
            req = urllib.request.Request(tags_url, headers={"Accept": "application/json"}, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            models_raw = data.get("models") if isinstance(data, dict) else None
            if isinstance(models_raw, list):
                out: List[Dict[str, Any]] = []
                for item in models_raw:
                    name = item.get("name") or item.get("model")
                    if not name:
                        continue
                    details = item.get("details") or {}
                    param_size = details.get("parameter_size", "")
                    quant = details.get("quantization_level", "")
                    meta = " ".join(x for x in (param_size, quant) if x).strip()
                    desc = f"Local Ollama model ({meta})" if meta else "Local Ollama model"
                    out.append({
                        "id": f"ollama/{name}",
                        "upstream_id": name,
                        "name": name,
                        "provider": "Ollama (Local)",
                        "gateway": "ollama",
                        "description": desc,
                        "context_length": 32768,
                        "category": "Local / Open-Weight",
                        "open_weights": True,
                        "pricing": {"prompt": "0", "completion": "0", "prompt_per_1m": 0.0, "completion_per_1m": 0.0},
                    })
                return out
        except Exception:
            pass
        return self.get_openai_compat_models(
            resolved,
            api_key=resolve_local_compat_key(self.local_api_key),
            gateway_name="ollama",
            prefix="ollama",
            timeout=timeout,
        )

    # Default AI Brain Arena match-up: the two configured brains the duel always used.
    ARENA_DEFAULT_PAIR = ("gemini-brain", "claude-brain")
    _NON_CHAT_PREFIXES = ("ronin/", "rodin/", "hyper3d/")

    def get_arena_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Chat models the Brain Arena may compare.

        Built from what this router actually supports: the configured provider
        aliases (claude-brain, gemini-brain, ..., nanogpt-brain) first, then the
        chat models in the router catalog (OpenRouter + NanoGPT models). 3D
        generators (Ronin/Rodin) are left out because they are not chat
        completions and bill per generation.
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
            cat = str(m.get("category", "")).lower()
            if cat.startswith("3d") or cat.startswith("2d image"):
                continue
            out.append({
                "id": mid,
                "name": m.get("name") or mid,
                "secondary": mid,
                "provider": m.get("provider") or mid.split("/")[0],
                "model": mid,
                "upstream_id": m.get("upstream_id"),
                "kind": "catalog",
            })
            seen.add(mid)
        return out

    def is_arena_model_allowed(self, model_id: str) -> bool:
        """True for any listed arena model, or the raw/upstream id behind a configured alias."""
        if not model_id or not isinstance(model_id, str):
            return False
        return any(
            model_id in (m["id"], m["model"], m.get("upstream_id"))
            for m in self.get_arena_models()
        )

    def arena_default_pair(self) -> Dict[str, str]:
        ids = [m["id"] for m in self.get_arena_models()]
        a, b = self.ARENA_DEFAULT_PAIR
        if a not in ids:
            a = ids[0] if ids else a
        if b not in ids or b == a:
            b = next((i for i in ids if i != a), b)
        return {"a": a, "b": b}

    def route_request(
        self,
        requested_alias: str,
        estimated_cost: float = 0.02,
        *,
        gateway: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> LabProviderConfig:
        """Route request to the target lab, or fallback if credit pool is exhausted."""
        compat_gw = self._detect_compat_gateway(requested_alias, gateway=gateway, base_url=base_url)
        if compat_gw and (base_url is not None or gateway is not None):
            ephemeral = self._build_compat_config(requested_alias, compat_gw, base_url=base_url)
            self.routing_log.append({
                "timestamp": time.time(),
                "alias": requested_alias,
                "lab": ephemeral.lab_id,
                "model": ephemeral.model_alias,
                "cost": 0.0,
                "status": "routed",
            })
            return ephemeral

        primary = self.providers.get(requested_alias)
        if not primary:
            # Dynamically register custom model alias (Ronin 3D, local/compat, NanoGPT, or OpenRouter)
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
            elif compat_gw:
                primary = self._build_compat_config(requested_alias, compat_gw, base_url=base_url)
            elif self._is_nanogpt_model(requested_alias):
                upstream = self._strip_nanogpt_prefix(requested_alias)
                rates = self._lookup_catalog_rates(requested_alias)
                in_rate, out_rate = rates if rates else (0.5, 1.5)
                model_name = upstream.split("/")[-1].replace("-", " ").title()
                primary = LabProviderConfig(
                    lab_id="nanogpt",
                    display_name=f"NanoGPT {model_name}",
                    model_alias=requested_alias,
                    endpoint=self.NANOGPT_ENDPOINT,
                    api_key_env="NANOGPT_API_KEY",
                    available_credits=100.0,
                    is_active=True,
                    input_cost_per_1m=in_rate,
                    output_cost_per_1m=out_rate,
                )
            else:
                parts = requested_alias.split("/")
                lab_id = parts[0] if len(parts) > 1 else "openrouter"
                model_name = parts[-1].replace("-", " ").title()
                rates = self._lookup_catalog_rates(requested_alias)
                in_rate, out_rate = rates if rates else (1.0, 3.0)
                primary = LabProviderConfig(
                    lab_id=lab_id,
                    display_name=f"{lab_id.capitalize()} {model_name}",
                    model_alias=requested_alias,
                    endpoint=self.OPENROUTER_ENDPOINT,
                    api_key_env="OPENROUTER_API_KEY",
                    available_credits=100.0,
                    is_active=True,
                    input_cost_per_1m=in_rate,
                    output_cost_per_1m=out_rate,
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
            cfg = self.providers[alias]
            cfg.model_alias = new_model
            compat_gw = self._detect_compat_gateway(new_model, base_url=new_endpoint)
            if new_endpoint:
                cfg.endpoint = new_endpoint
                if compat_gw:
                    _, key_env, _ = self._resolve_compat_spec(compat_gw, base_url=new_endpoint)
                    cfg.lab_id = compat_gw
                    cfg.api_key_env = key_env
                    cfg.input_cost_per_1m = 0.0
                    cfg.output_cost_per_1m = 0.0
            elif compat_gw:
                endpoint, key_env, _ = self._resolve_compat_spec(compat_gw)
                cfg.lab_id = compat_gw
                cfg.endpoint = endpoint
                cfg.api_key_env = key_env
                cfg.input_cost_per_1m = 0.0
                cfg.output_cost_per_1m = 0.0
            elif self._is_nanogpt_model(new_model):
                cfg.endpoint = self.NANOGPT_ENDPOINT
                cfg.api_key_env = "NANOGPT_API_KEY"
            elif new_model.startswith("openrouter/"):
                cfg.model_alias = new_model[len("openrouter/"):]
                cfg.endpoint = self.OPENROUTER_ENDPOINT
                cfg.api_key_env = "OPENROUTER_API_KEY"

    def set_model(
        self,
        alias: str,
        new_model: str,
        display_name: Optional[str] = None,
        gateway: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> LabProviderConfig:
        """Set or update model name (and gateway endpoint if applicable) for a provider alias."""
        compat_gw = self._detect_compat_gateway(new_model, gateway=gateway, base_url=base_url)
        if compat_gw:
            built = self._build_compat_config(new_model, compat_gw, base_url=base_url, display_name=display_name or alias)
            if alias not in self.providers:
                self.providers[alias] = built
            else:
                cfg = self.providers[alias]
                cfg.lab_id = built.lab_id
                cfg.model_alias = built.model_alias
                cfg.endpoint = built.endpoint
                cfg.api_key_env = built.api_key_env
                cfg.input_cost_per_1m = 0.0
                cfg.output_cost_per_1m = 0.0
                if display_name:
                    cfg.display_name = display_name
            return self.providers[alias]

        use_nanogpt = (
            gateway == "nanogpt"
            or self._is_nanogpt_model(new_model)
            or (alias == "nanogpt-brain" and gateway != "openrouter" and not new_model.startswith("openrouter/"))
        )
        clean_model = (
            new_model[len("openrouter/"):]
            if new_model.startswith("openrouter/")
            else new_model
        )
        target_endpoint = self.NANOGPT_ENDPOINT if use_nanogpt else self.OPENROUTER_ENDPOINT
        target_env = "NANOGPT_API_KEY" if use_nanogpt else "OPENROUTER_API_KEY"
        rates = self._lookup_catalog_rates(clean_model)

        if alias not in self.providers:
            self.providers[alias] = LabProviderConfig(
                lab_id="nanogpt" if use_nanogpt else "custom",
                display_name=display_name or alias,
                model_alias=clean_model,
                endpoint=target_endpoint,
                api_key_env=target_env,
                available_credits=50.0,
                is_active=True,
                input_cost_per_1m=rates[0] if rates else 1.0,
                output_cost_per_1m=rates[1] if rates else 3.0,
            )
        else:
            cfg = self.providers[alias]
            cfg.model_alias = clean_model
            cfg.endpoint = target_endpoint
            cfg.api_key_env = target_env
            if use_nanogpt and cfg.lab_id == "custom":
                cfg.lab_id = "nanogpt"
            if rates:
                cfg.input_cost_per_1m, cfg.output_cost_per_1m = rates
            if display_name:
                cfg.display_name = display_name
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

    def _fetch_nanogpt_billing_sync(self, api_key: str) -> Dict[str, Any]:
        """Perform synchronous NanoGPT /api/check-balance request and update cache."""
        now = time.time()
        headers = {
            "x-api-key": api_key,
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "TinCan-Mesh-OS/2.2",
        }
        balance_data: Dict[str, Any] = {}
        connected = False
        err_msg: Optional[str] = None

        try:
            req = urllib.request.Request(
                self.NANOGPT_BALANCE_URL,
                data=b"{}",
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                raw = resp.read().decode("utf-8")
                balance_data = json.loads(raw) or {}
                connected = True
        except Exception as exc:
            err_msg = str(exc)

        data_obj = balance_data.get("data") if isinstance(balance_data.get("data"), dict) else balance_data
        try:
            usd_val = float(
                data_obj.get("usd_balance")
                or data_obj.get("usdBalance")
                or data_obj.get("balance")
                or 0.0
            )
        except (TypeError, ValueError):
            usd_val = 0.0
        try:
            nano_val = float(
                data_obj.get("nano_balance")
                or data_obj.get("nanoBalance")
                or 0.0
            )
        except (TypeError, ValueError):
            nano_val = 0.0

        nano_providers = [p for p in self.providers.values() if p.api_key_env == "NANOGPT_API_KEY"]
        billing: Dict[str, Any] = {
            "connected": connected,
            "provider": "NanoGPT",
            "endpoint": self.NANOGPT_ENDPOINT,
            "account_remaining_balance_usd": round(usd_val, 6),
            "account_remaining_nano": round(nano_val, 6),
            "session_total_calls": sum(p.total_calls for p in nano_providers),
            "session_total_tokens": sum(p.total_tokens for p in nano_providers),
            "session_total_spend_usd": round(sum(p.total_cost for p in nano_providers), 6),
            "key_label": "pooled-nanogpt-key [redacted]" if api_key else "not_configured",
            "fetched_at": now,
        }
        if err_msg and not connected:
            billing["error"] = err_msg

        with self._nanogpt_billing_lock:
            self._nanogpt_billing_cache = billing
            self._nanogpt_billing_cached_at = now
            self._nanogpt_billing_refreshing = False
        return billing

    def get_nanogpt_billing(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch live NanoGPT account balance with 60s stale-while-revalidate caching."""
        now = time.time()
        if (
            not force_refresh
            and self._nanogpt_billing_cached_at
            and (now - self._nanogpt_billing_cached_at) < self.BILLING_CACHE_TTL
            and self._nanogpt_billing_cache
        ):
            return self._nanogpt_billing_cache

        api_key = self.nanogpt_key if self.nanogpt_key is not None else _resolve_nanogpt_key_fallback()
        nano_providers = [p for p in self.providers.values() if p.api_key_env == "NANOGPT_API_KEY"]
        if not api_key:
            return {
                "connected": False,
                "provider": "NanoGPT",
                "endpoint": self.NANOGPT_ENDPOINT,
                "account_remaining_balance_usd": 0.0,
                "account_remaining_nano": 0.0,
                "session_total_calls": sum(p.total_calls for p in nano_providers),
                "session_total_tokens": sum(p.total_tokens for p in nano_providers),
                "session_total_spend_usd": round(sum(p.total_cost for p in nano_providers), 6),
                "key_label": "not_configured",
            }

        if not force_refresh and self._nanogpt_billing_cache is not None:
            with self._nanogpt_billing_lock:
                should_spawn = not self._nanogpt_billing_refreshing
                if should_spawn:
                    self._nanogpt_billing_refreshing = True
            if should_spawn:
                threading.Thread(
                    target=self._fetch_nanogpt_billing_sync,
                    args=(api_key,),
                    daemon=True,
                ).start()
            return self._nanogpt_billing_cache

        return self._fetch_nanogpt_billing_sync(api_key)

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

    @staticmethod
    def _encode_multipart_fields(fields: Dict[str, Any]) -> tuple[bytes, str]:
        """Encode simple text/JSON-serializable fields as multipart/form-data for Hyper3D Rodin v2."""
        boundary = f"----TinCanBoundary{uuid.uuid4().hex[:16]}"
        parts: List[bytes] = []
        for k, v in fields.items():
            if v is None:
                continue
            val = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{val}\r\n".encode("utf-8")
            )
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(parts), f"multipart/form-data; boundary={boundary}"

    @staticmethod
    def _map_nanogpt_rodin_payload(
        prompt: str,
        *,
        model: Optional[str] = None,
        images: Optional[List[str]] = None,
        tier: str = "Regular",
        material: str = "PBR",
        quality: str = "medium",
        mesh_mode: str = "Quad",
    ) -> Dict[str, Any]:
        """Build clean JSON request body for NanoGPT 3D endpoints (/api/generate-video)."""
        target_model = model or DynamicAIGatewayRouter.NANOGPT_DEFAULT_RODIN_MODEL
        body: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
        }
        if images:
            first_img = str(images[0])
            if first_img.startswith("data:"):
                body["imageDataUrl"] = first_img
            elif first_img.startswith(("http://", "https://")):
                body["imageUrl"] = first_img
        return body

    @classmethod
    def _extract_nanogpt_glb_urls(cls, data: Any) -> List[str]:
        """Extract all output asset URLs from a NanoGPT /api/video/status payload, preferring .glb."""
        urls: List[str] = []

        def _add(val: Any) -> None:
            raw_u = val.get("url") if isinstance(val, dict) else (val if isinstance(val, str) else None)
            if not raw_u or not isinstance(raw_u, str):
                return
            u = raw_u.strip()
            if u.startswith("/api/"):
                u = cls.NANOGPT_BASE_URL + u
            if u.startswith(("http://", "https://")) and u not in urls:
                urls.append(u)

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                for k in ("model_url", "glb_url", "model_mesh", "url", "outputUrl", "output_url", "videoUrl", "video_url", "video", "model"):
                    if k in node:
                        _add(node[k])
                for k in ("model3d_assets", "videoUrls", "files", "list", "assets", "outputs"):
                    if isinstance(node.get(k), list):
                        for item in node[k]:
                            _add(item)
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        _walk(v)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(data)
        glb_first = [u for u in urls if ".glb" in u.lower()]
        other = [u for u in urls if ".glb" not in u.lower()]
        return glb_first + other

    def _dispatch_nanogpt_rodin(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        images: Optional[List[str]] = None,
        tier: str = "Regular",
        material: str = "PBR",
        quality: str = "medium",
        mesh_mode: str = "Quad",
    ) -> Dict[str, Any]:
        """Submit a 3D generation job to NanoGPT (/api/generate-video)."""
        nanogpt_key = self.nanogpt_key if self.nanogpt_key is not None else os.environ.get("NANOGPT_API_KEY")
        if not nanogpt_key:
            return {"ok": False, "error": "NANOGPT_API_KEY not configured"}
        target_model = model or self.NANOGPT_DEFAULT_RODIN_MODEL
        payload = self._map_nanogpt_rodin_payload(
            prompt, model=target_model, images=images, tier=tier, material=material, quality=quality, mesh_mode=mesh_mode
        )
        headers = {
            "Authorization": f"Bearer {nanogpt_key}",
            "x-api-key": nanogpt_key,
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            self.NANOGPT_MEDIA_SUBMIT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8")) or {}
            run_id = (
                resp_data.get("runId")
                or resp_data.get("requestId")
                or resp_data.get("id")
                or resp_data.get("jobId")
            )
            if not run_id:
                return {"ok": False, "error": f"NanoGPT 3D submit returned no runId: {json.dumps(resp_data)[:200]}"}
            default_cost = {"hyper3d/rodin-v2.5": 0.48, "tripo3d/h3.0": 0.24, "wavespeed-ai/hunyuan-3d-v3.1-rapid": 0.27}.get(target_model, 0.48)
            return {
                "ok": True,
                "run_id": str(run_id),
                "model_slug": str(resp_data.get("modelSlug") or resp_data.get("model") or target_model),
                "status": str(resp_data.get("status") or "pending"),
                "cost_usd": float(resp_data.get("cost") or default_cost),
                "raw": resp_data,
            }
        except urllib.error.HTTPError as http_err:
            detail = ""
            try:
                detail = http_err.read().decode("utf-8", errors="replace").strip()[:240]
            except Exception:
                pass
            return {"ok": False, "error": f"NanoGPT ({target_model}) HTTP {http_err.code}{' — ' + detail if detail else ''}"}
        except Exception as err:
            return {"ok": False, "error": f"NanoGPT ({target_model}) 3D submit failed: {err}"}

    def _dispatch_nanogpt_rodin_with_fallback(
        self,
        *,
        prompt: str,
        images: Optional[List[str]] = None,
        excluded_models: Optional[List[str]] = None,
        tier: str = "Regular",
        material: str = "PBR",
        quality: str = "medium",
        mesh_mode: str = "Quad",
    ) -> Dict[str, Any]:
        """Try NanoGPT 3D models in priority order until one accepts the job."""
        tried: List[str] = list(excluded_models or [])
        errors: List[str] = []
        for candidate in self.NANOGPT_3D_FALLBACK_MODELS:
            if candidate in tried:
                continue
            tried.append(candidate)
            res = self._dispatch_nanogpt_rodin(
                prompt=prompt,
                model=candidate,
                images=images,
                tier=tier,
                material=material,
                quality=quality,
                mesh_mode=mesh_mode,
            )
            if res.get("ok"):
                res["attempted_models"] = tried
                if errors:
                    res["previous_errors"] = errors
                return res
            errors.append(str(res.get("error") or f"{candidate} failed"))
        return {
            "ok": False,
            "attempted_models": tried,
            "error": "; ".join(errors) if errors else "All NanoGPT 3D models failed or exhausted",
        }

    def _retry_nanogpt_3d_fallback(
        self,
        matching_task: Dict[str, Any],
        prev_error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """When an async NanoGPT 3D run transitions to Failed, automatically submit the next fallback 3D model."""
        prev_model = str(matching_task.get("model_slug") or matching_task.get("model") or self.NANOGPT_DEFAULT_RODIN_MODEL)
        tried = list(matching_task.get("attempted_models") or [])
        if prev_model not in tried:
            tried.append(prev_model)
        next_res = self._dispatch_nanogpt_rodin_with_fallback(
            prompt=str(matching_task.get("prompt") or "3D generative mesh"),
            images=matching_task.get("images"),
            excluded_models=tried,
            tier=str(matching_task.get("tier") or "Regular"),
            material=str(matching_task.get("material") or "PBR"),
            quality=str(matching_task.get("quality") or "medium"),
            mesh_mode=str(matching_task.get("mesh_mode") or "Quad"),
        )
        if not next_res.get("ok"):
            matching_task["attempted_models"] = next_res.get("attempted_models", tried)
            if prev_error:
                matching_task["remote_error"] = prev_error
            return None

        old_run_id = str(matching_task.get("uuid") or "")
        new_run_id = str(next_res["run_id"])
        new_model = str(next_res.get("model_slug") or "")
        old_cost = float(matching_task.get("cost_usd") or 0.0)
        new_cost = float(next_res.get("cost_usd") or old_cost)
        prev_ids = list(matching_task.get("previous_run_ids") or [])
        if old_run_id and old_run_id not in prev_ids:
            prev_ids.append(old_run_id)

        matching_task["uuid"] = new_run_id
        matching_task["subscription_key"] = new_run_id
        matching_task["model_slug"] = new_model
        matching_task["model"] = new_model
        matching_task["status"] = "Processing"
        matching_task["cost_usd"] = new_cost
        matching_task["attempted_models"] = next_res.get("attempted_models", tried)
        matching_task["previous_run_ids"] = prev_ids
        matching_task["fallback_from"] = prev_model
        matching_task.pop("glb_url", None)
        matching_task.pop("urls", None)
        if prev_error:
            matching_task["previous_error"] = prev_error
        matching_task.pop("remote_error", None)

        self.rodin_total_cost_usd = max(0.0, self.rodin_total_cost_usd + (new_cost - old_cost))
        self.rodin_tasks[new_run_id] = matching_task
        return {
            "subscription_key": new_run_id,
            "uuid": new_run_id,
            "gateway": "nanogpt",
            "model": new_model,
            "status": "Processing",
            "raw_status": "fallback_submitted",
            "jobs": [{"uuid": new_run_id, "status": "Processing"}],
            "urls": [],
            "fallback_from": prev_model,
            "previous_error": prev_error,
        }

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
        """Dispatch 3D generative task to Hyper3D Rodin v2 API or NanoGPT Rodin v2.5 fallback."""
        cost_usd = float(self.RODIN_TIER_COSTS.get(tier, 0.50))
        task_uuid = f"rodin-{uuid.uuid4().hex[:12]}"
        sub_key = f"sub-{uuid.uuid4().hex[:12]}"
        status = "Done"
        simulated = True
        gateway = "hyper3d"
        provider_model = "rodin-v2"
        model_slug: Optional[str] = None
        remote_error: Optional[str] = None
        hyper3d_direct_error: Optional[str] = None

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

            mp_body, mp_ctype = self._encode_multipart_fields(payload)
            json_body = json.dumps(payload).encode("utf-8")
            minimal_mp_body, minimal_mp_ctype = self._encode_multipart_fields({
                "prompt": prompt,
                "tier": tier,
                "geometry_file_format": geometry_file_format,
            })
            attempts = [
                (self.RODIN_GENERATE_URL, mp_body, mp_ctype),
                (self.RODIN_GENERATE_URL, minimal_mp_body, minimal_mp_ctype),
                (self.RODIN_FALLBACK_GENERATE_URL, minimal_mp_body, minimal_mp_ctype),
                (self.RODIN_GENERATE_URL, json_body, "application/json"),
            ]
            for url, body_bytes, ctype in attempts:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": ctype,
                }
                req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=30.0) as resp:
                        resp_data = json.loads(resp.read().decode("utf-8")) or {}
                    err_flag = resp_data.get("error")
                    if err_flag and str(err_flag).upper() != "OK":
                        remote_error = f"{err_flag}: {resp_data.get('message') or ''}".strip(": ")
                        continue
                    jobs_obj = resp_data.get("jobs") if isinstance(resp_data.get("jobs"), dict) else {}
                    found_sub = resp_data.get("subscription_key") or jobs_obj.get("subscription_key")
                    found_uuid = resp_data.get("uuid")
                    if not found_uuid and not found_sub:
                        remote_error = f"Unexpected Rodin response at {url}: {json.dumps(resp_data)[:200]}"
                        continue
                    if found_uuid:
                        task_uuid = str(found_uuid)
                    if found_sub:
                        sub_key = str(found_sub)
                    status = resp_data.get("status", "Waiting" if found_sub and not resp_data.get("status") else "Done")
                    simulated = False
                    remote_error = None
                    break
                except urllib.error.HTTPError as http_err:
                    detail = ""
                    try:
                        detail = http_err.read().decode("utf-8", errors="replace").strip()[:200]
                    except Exception:
                        pass
                    remote_error = f"HTTP {http_err.code} at {url}{' — ' + detail if detail else ''}"
                    if http_err.code in (400, 404, 415, 422, 502, 503, 504):
                        continue
                    break
                except Exception as err:
                    remote_error = str(err)
                    simulated = True
                    status = "Done"
                    break

        # Fallback to NanoGPT (Rodin v2.5 -> Tripo3D -> Hunyuan3D) when direct Hyper3D is unconfigured or rejected
        attempted_models: List[str] = []
        nanogpt_key = self.nanogpt_key if self.nanogpt_key is not None else os.environ.get("NANOGPT_API_KEY")
        if simulated and nanogpt_key:
            hyper3d_direct_error = remote_error
            nano_res = self._dispatch_nanogpt_rodin_with_fallback(
                prompt=prompt,
                images=images,
                tier=tier,
                material=material,
                quality=quality,
                mesh_mode=mesh_mode,
            )
            attempted_models = list(nano_res.get("attempted_models") or [])
            if nano_res.get("ok"):
                task_uuid = nano_res["run_id"]
                sub_key = nano_res["run_id"]
                model_slug = nano_res.get("model_slug") or self.NANOGPT_DEFAULT_RODIN_MODEL
                provider_model = model_slug
                gateway = "nanogpt"
                status = nano_res.get("status") or "pending"
                cost_usd = float(nano_res.get("cost_usd") or 0.48)
                simulated = False
                remote_error = None
            else:
                nano_err = nano_res.get("error") or "NanoGPT 3D submission failed"
                remote_error = f"{hyper3d_direct_error}; {nano_err}" if hyper3d_direct_error else nano_err

        # Only generate the synthetic placeholder GLB when running simulated/offline;
        # real async jobs populate glb_bytes_b64 after /api/3d/download completes.
        if simulated:
            glb_bytes = generate_minimal_glb_bytes(name=prompt[:24] if prompt else "rodin_mesh")
            glb_b64 = base64.b64encode(glb_bytes).decode("utf-8")
        else:
            glb_b64 = ""

        task_record: Dict[str, Any] = {
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
            "gateway": gateway,
            "model": provider_model,
        }
        if model_slug:
            task_record["model_slug"] = model_slug
        if attempted_models:
            task_record["attempted_models"] = attempted_models
        if images:
            task_record["images"] = images
        if remote_error:
            task_record["remote_error"] = remote_error
        if hyper3d_direct_error and not remote_error:
            task_record["hyper3d_direct_error"] = hyper3d_direct_error

        self.rodin_tasks[task_uuid] = task_record
        self.rodin_total_calls += 1
        self.rodin_total_cost_usd += cost_usd
        return dict(task_record)

    def check_rodin_status(self, subscription_key: str, allow_fallback: bool = True) -> Dict[str, Any]:
        """Check status of Rodin generation task via NanoGPT, Hyper3D API, or local task registry."""
        matching_task = self.rodin_tasks.get(subscription_key)
        if not matching_task:
            for t in self.rodin_tasks.values():
                prev_ids = t.get("previous_run_ids") or []
                if (
                    t.get("subscription_key") == subscription_key
                    or t.get("uuid") == subscription_key
                    or subscription_key in prev_ids
                ):
                    matching_task = t
                    break

        is_nanogpt_task = bool(
            (matching_task and matching_task.get("gateway") == "nanogpt" and not matching_task.get("simulated"))
            or str(subscription_key).startswith("vid_")
        )
        nanogpt_key = self.nanogpt_key if self.nanogpt_key is not None else os.environ.get("NANOGPT_API_KEY")
        if is_nanogpt_task and nanogpt_key:
            req_id = (matching_task.get("uuid") if matching_task else None) or subscription_key
            params: Dict[str, str] = {"requestId": str(req_id), "runId": str(req_id)}
            if matching_task and matching_task.get("model_slug"):
                params["modelSlug"] = str(matching_task["model_slug"])
            url = f"{self.NANOGPT_MEDIA_STATUS_URL}?{urllib.parse.urlencode(params)}"
            headers = {
                "Authorization": f"Bearer {nanogpt_key}",
                "x-api-key": nanogpt_key,
            }
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=20.0) as resp:
                    raw_data = json.loads(resp.read().decode("utf-8")) or {}
                job = raw_data.get("data") if isinstance(raw_data.get("data"), dict) else raw_data
                raw_st = str(job.get("status") or job.get("state") or raw_data.get("status") or "pending").lower()
                if raw_st in ("succeeded", "success", "completed", "complete", "done"):
                    norm_st = "Done"
                elif raw_st in ("failed", "error", "canceled", "cancelled", "timed_out"):
                    norm_st = "Failed"
                else:
                    norm_st = "Processing"
                urls = self._extract_nanogpt_glb_urls(raw_data)
                err_txt = job.get("error") or raw_data.get("error")

                if norm_st == "Failed" and allow_fallback and matching_task is not None:
                    fallback_status = self._retry_nanogpt_3d_fallback(
                        matching_task, prev_error=str(err_txt) if err_txt else None
                    )
                    if fallback_status is not None:
                        return fallback_status

                if matching_task is not None:
                    matching_task["status"] = norm_st
                    if urls:
                        matching_task["glb_url"] = urls[0]
                        matching_task["urls"] = urls
                    if err_txt and norm_st == "Failed":
                        matching_task["remote_error"] = str(err_txt)
                out: Dict[str, Any] = {
                    "subscription_key": str(req_id),
                    "uuid": str(req_id),
                    "gateway": "nanogpt",
                    "model": (matching_task or {}).get("model_slug") or (matching_task or {}).get("model") or self.NANOGPT_DEFAULT_RODIN_MODEL,
                    "status": norm_st,
                    "raw_status": raw_st,
                    "jobs": [{"uuid": str(req_id), "status": norm_st}],
                    "urls": urls,
                }
                if err_txt:
                    out["error"] = err_txt
                return out
            except urllib.error.HTTPError as http_err:
                if http_err.code == 404:
                    return {
                        "subscription_key": str(req_id),
                        "uuid": str(req_id),
                        "gateway": "nanogpt",
                        "model": (matching_task or {}).get("model_slug") or self.NANOGPT_DEFAULT_RODIN_MODEL,
                        "status": "Processing",
                        "jobs": [{"uuid": str(req_id), "status": "Processing"}],
                    }
            except Exception:
                pass

        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        if api_key and not subscription_key.startswith("sub-") and not is_nanogpt_task:
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
        """Download Rodin assets via NanoGPT, Hyper3D API, or return deterministic asset manifest."""
        task = self.rodin_tasks.get(task_uuid) or {}
        if not task:
            for t in self.rodin_tasks.values():
                if (
                    t.get("uuid") == task_uuid
                    or t.get("subscription_key") == task_uuid
                    or task_uuid in (t.get("previous_run_ids") or [])
                ):
                    task = t
                    break
        active_uuid = str(task.get("uuid") or task_uuid)
        is_simulated = task.get("simulated", True)
        download_error: Optional[str] = None

        if task.get("gateway") == "nanogpt" and not is_simulated:
            glb_url = task.get("glb_url")
            if not glb_url:
                st = self.check_rodin_status(task.get("subscription_key") or active_uuid, allow_fallback=False)
                urls = st.get("urls") or []
                glb_url = urls[0] if urls else None
            if glb_url:
                try:
                    mesh_req = urllib.request.Request(str(glb_url), method="GET")
                    with urllib.request.urlopen(mesh_req, timeout=60.0) as mesh_resp:
                        raw_mesh = mesh_resp.read()
                    if raw_mesh:
                        b64_str = base64.b64encode(raw_mesh).decode("ascii")
                        task["glb_bytes_b64"] = b64_str
                        task["status"] = "Done"
                        task["downloaded"] = True
                        task["url"] = glb_url
                        return {
                            "task_uuid": active_uuid,
                            "gateway": "nanogpt",
                            "model": task.get("model_slug") or task.get("model"),
                            "format": task.get("format", "glb"),
                            "url": glb_url,
                            "urls": task.get("urls") or [glb_url],
                            "files": [{"name": f"{active_uuid}.glb", "format": "glb", "url": glb_url, "bytes_b64": b64_str}],
                            "glb_bytes_b64": b64_str,
                            "simulated": False,
                            "downloaded": True,
                        }
                except Exception as err:
                    download_error = str(err)
            return {
                "task_uuid": active_uuid,
                "gateway": "nanogpt",
                "model": task.get("model_slug") or task.get("model"),
                "status": task.get("status", "Processing"),
                "format": task.get("format", "glb"),
                "glb_bytes_b64": "",
                "simulated": False,
                "downloaded": False,
                "download_error": download_error or task.get("remote_error") or "3D asset not ready yet",
            }

        api_key = self.hyper3d_key or _resolve_hyper3d_key_fallback()
        if api_key and not is_simulated and task.get("gateway") != "nanogpt":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            req = urllib.request.Request(
                self.RODIN_DOWNLOAD_URL,
                data=json.dumps({"task_uuid": active_uuid, "uuid": active_uuid}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15.0) as resp:
                    dl_data = json.loads(resp.read().decode("utf-8")) or {}
                glb_url = None
                for item in (dl_data.get("list") or []):
                    if isinstance(item, dict) and str(item.get("name", "")).lower().endswith(".glb") and item.get("url"):
                        glb_url = str(item["url"])
                        break
                if not glb_url and isinstance(dl_data.get("files"), dict):
                    glb_url = dl_data["files"].get("glb")
                if glb_url and not dl_data.get("glb_bytes_b64"):
                    mesh_req = urllib.request.Request(glb_url, method="GET")
                    with urllib.request.urlopen(mesh_req, timeout=30.0) as mesh_resp:
                        raw_mesh = mesh_resp.read()
                    if raw_mesh:
                        dl_data["glb_bytes_b64"] = base64.b64encode(raw_mesh).decode("ascii")
                        dl_data["simulated"] = False
                        dl_data["downloaded"] = True
                return dl_data
            except Exception as err:
                download_error = str(err)

        fmt = task.get("format", "glb")
        glb_b64 = task.get("glb_bytes_b64")
        if not glb_b64 and is_simulated:
            glb_b64 = base64.b64encode(generate_minimal_glb_bytes(active_uuid[:16])).decode("utf-8")

        out = {
            "task_uuid": active_uuid,
            "format": fmt,
            "files": [
                {
                    "name": f"{active_uuid}.{fmt}",
                    "format": fmt,
                    "bytes_b64": glb_b64 or "",
                }
            ],
            "glb_bytes_b64": glb_b64 or "",
            "simulated": is_simulated,
        }
        if download_error:
            out["download_error"] = download_error
        return out

    def wait_for_rodin_glb(self, task_record: Dict[str, Any], max_wait_sec: float = 120.0) -> Dict[str, Any]:
        """Poll a live Rodin/NanoGPT 3D task and hydrate glb_bytes_b64 with the real downloaded mesh."""
        if not task_record or task_record.get("simulated"):
            return task_record
        is_nano = task_record.get("gateway") == "nanogpt"
        poll_interval = 3.0 if is_nano else 2.0
        deadline = time.time() + float(max_wait_sec)
        while time.time() < deadline:
            sub_key = str(task_record.get("subscription_key") or "")
            task_uuid = str(task_record.get("uuid") or "")
            st_data = self.check_rodin_status(sub_key, allow_fallback=True) if sub_key else {}
            if st_data.get("uuid") and st_data["uuid"] != task_uuid:
                # Sync task_record if an automatic model fallback switched run_id
                updated = self.rodin_tasks.get(str(st_data["uuid"]))
                if updated and updated is not task_record:
                    task_record.update(updated)
            sub_key = str(task_record.get("subscription_key") or sub_key)
            task_uuid = str(task_record.get("uuid") or task_uuid)

            jobs = st_data.get("jobs") or []
            statuses = [str(j.get("status") or "") for j in jobs if isinstance(j, dict)]
            top_status = str(st_data.get("status") or "")
            if top_status == "Done" or (statuses and all(s == "Done" for s in statuses)):
                dl = self.download_rodin_assets(task_uuid)
                if dl.get("glb_bytes_b64") and not dl.get("simulated"):
                    task_record["glb_bytes_b64"] = dl["glb_bytes_b64"]
                    task_record["status"] = "Done"
                    task_record["downloaded"] = True
                    if dl.get("url"):
                        task_record["url"] = dl["url"]
                elif dl.get("download_error"):
                    task_record["download_error"] = dl["download_error"]
                break
            if top_status == "Failed" or any(s == "Failed" for s in statuses):
                task_record["status"] = "Failed"
                if st_data.get("error"):
                    task_record["remote_error"] = str(st_data["error"])
                break
            time.sleep(min(poll_interval, max(0.05, deadline - time.time())))
        return task_record

    def get_analytics(self, include_live_billing: bool = True) -> Dict[str, Any]:
        """Aggregate usage analytics, per-model token rates, and live OpenRouter/NanoGPT/Hyper3D spend."""
        session_calls = sum(p.total_calls for p in self.providers.values())
        session_tokens = sum(p.total_tokens for p in self.providers.values())
        session_spend = sum(p.total_cost for p in self.providers.values())
        billing = self.get_openrouter_billing() if include_live_billing else {}
        nanogpt_billing = self.get_nanogpt_billing() if include_live_billing else {}
        hyper3d_billing = self.get_hyper3d_billing() if include_live_billing else {}

        providers_out: Dict[str, Any] = {}
        for k, p in self.providers.items():
            gw_name = self._provider_gateway(p)
            gw_billing = nanogpt_billing if gw_name == "nanogpt" else (billing if gw_name == "openrouter" else {})
            rem_credits = (
                gw_billing.get("account_remaining_balance_usd", p.available_credits)
                if gw_billing.get("connected")
                else p.available_credits
            )
            providers_out[k] = {
                "display_name": p.display_name,
                "model": p.model_alias,
                "gateway": gw_name,
                "input_cost_per_1m_usd": p.input_cost_per_1m,
                "output_cost_per_1m_usd": p.output_cost_per_1m,
                "est_cost_per_1k_prompt_usd": round((p.input_cost_per_1m * 0.5 + p.output_cost_per_1m * 0.5) / 1000.0, 6),
                "total_calls": p.total_calls,
                "prompt_tokens": p.total_prompt_tokens,
                "completion_tokens": p.total_completion_tokens,
                "total_tokens": p.total_tokens,
                "cost_usd": round(p.total_cost, 6),
                "remaining_credits": round(rem_credits, 4),
                "is_active": p.is_active,
            }

        return {
            "total_calls": session_calls,
            "total_tokens": session_tokens,
            "total_spend_usd": round(session_spend, 6),
            "openrouter": billing,
            "nanogpt": nanogpt_billing,
            "hyper3d": hyper3d_billing,
            "providers": providers_out,
            "recent_routing_log": self.routing_log[-20:],
        }

    def _resolve_dispatch_params(
        self,
        config: LabProviderConfig,
        *,
        gateway_override: Optional[str] = None,
        explicit_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resolve upstream model ID, auth key, headers, fallback policy, and timeout uniformly."""
        gw = gateway_override if gateway_override in self._OPENAI_COMPAT_GATEWAYS else self._provider_gateway(config)
        if gw == "nanogpt":
            api_key = explicit_api_key or (self.nanogpt_key if self.nanogpt_key is not None else _resolve_nanogpt_key_fallback())
            headers = {
                "Authorization": f"Bearer {api_key}",
                "x-api-key": api_key or "",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "TinCan-Mesh-OS/2.2",
            }
            return {
                "gateway": "nanogpt",
                "router_label": "NanoGPT",
                "api_key": api_key,
                "requires_key": True,
                "upstream_model": self._strip_nanogpt_prefix(config.model_alias),
                "fallback_model": "auto-model",
                "headers": headers,
                "timeout": 30.0,
            }

        if gw in self._OPENAI_COMPAT_GATEWAYS:
            key_resolvers = {
                "owlchat": lambda: resolve_owlchat_key(explicit_api_key or self.owlchat_key),
                "trussed": lambda: resolve_trussed_key(explicit_api_key or self.trussed_key),
                "ollama": lambda: resolve_local_compat_key(explicit_api_key or self.local_api_key),
                "local": lambda: resolve_local_compat_key(explicit_api_key or self.local_api_key),
            }
            labels = {
                "ollama": "Ollama",
                "owlchat": "FAU OwlChat",
                "trussed": "FAU Trussed AI",
                "local": "OpenAI-Compatible",
            }
            api_key = key_resolvers[gw]()
            requires_key = gw in ("owlchat", "trussed")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "TinCan-Mesh-OS/2.2",
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return {
                "gateway": gw,
                "router_label": labels[gw],
                "api_key": api_key,
                "requires_key": requires_key,
                "upstream_model": self._strip_compat_prefix(config.model_alias),
                "fallback_model": None,
                "headers": headers,
                "timeout": float(os.environ.get("TINCAN_AI_TIMEOUT", "120")),
            }

        api_key = explicit_api_key or (self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY"))
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/NoJuanNobody/tin-can",
            "X-Title": "TinCan 2 / IoT Federated Agent Memory",
        }
        return {
            "gateway": "openrouter",
            "router_label": "OpenRouter",
            "api_key": api_key,
            "requires_key": True,
            "upstream_model": config.model_alias,
            "fallback_model": "google/gemini-2.5-flash",
            "headers": headers,
            "timeout": 30.0,
        }

    def resolve_free_model(self) -> Dict[str, Any]:
        """Pick the best zero-cost model alias (local Ollama first if configured, else OpenRouter :free)."""
        if self.local_base_url:
            return {"alias": "ollama/llama3.2", "gateway": "ollama", "is_free": True}
        env_free = os.environ.get("TINCAN_FREE_SUGGEST_MODEL", "").strip()
        if env_free:
            gw = "ollama" if env_free.startswith("ollama/") else "openrouter"
            return {"alias": env_free, "gateway": gw, "is_free": True}
        return {
            "alias": "meta-llama/llama-3.3-70b-instruct:free",
            "gateway": "openrouter",
            "is_free": True,
        }

    def free_complete(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 160,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Run a zero-cost completion via the resolved free model with safe offline handling."""
        spec = self.resolve_free_model()
        return self.dispatch_completion(
            alias=spec["alias"],
            gateway=spec["gateway"],
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=6.0,
        )

    def dispatch_completion(
        self,
        alias: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        gateway: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Dispatch chat completion to OpenRouter, NanoGPT, Ollama/local OpenAI-compat, FAU OwlChat, or Ronin 3D."""
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
            if not rodin_res.get("simulated") and hasattr(self, "wait_for_rodin_glb"):
                rodin_res = self.wait_for_rodin_glb(rodin_res, max_wait_sec=120.0)
            status_desc = f"Live {rodin_res.get('gateway', 'hyper3d').upper()} ({rodin_res.get('model', 'rodin-v2')})" if not rodin_res.get("simulated") else "Local Generative Engine"
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

        config = self.route_request(alias, gateway=gateway, base_url=base_url)
        spec = self._resolve_dispatch_params(
            config,
            gateway_override=gateway,
            explicit_api_key=api_key,
        )
        gw = spec["gateway"]
        router_label = spec["router_label"]
        upstream_model = spec["upstream_model"]
        fallback_model = spec["fallback_model"]
        headers = spec["headers"]
        req_timeout = timeout if timeout is not None else spec["timeout"]

        if spec["requires_key"] and not spec["api_key"]:
            # Simulated offline response if no API key is injected
            self.record_usage(alias, 10, 32, 42, 0.0)
            return {
                "id": f"sim-{alias}",
                "model": config.model_alias,
                "gateway": gw,
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"[Simulated {config.display_name} via {router_label} router: key pending]",
                    }
                }],
                "usage": {"total_tokens": 42},
            }

        payload = {
            "model": upstream_model,
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
            with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            # If a configured model alias is unavailable (400/404), retry with the gateway's default model.
            if fallback_model and http_err.code in (400, 404) and payload.get("model") != fallback_model:
                fallback_payload = dict(payload, model=fallback_model)
                req_fb = urllib.request.Request(
                    config.endpoint,
                    data=json.dumps(fallback_payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req_fb, timeout=req_timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            elif gw in self._OPENAI_COMPAT_GATEWAYS:
                detail = ""
                try:
                    raw_err = http_err.read().decode("utf-8", errors="replace").strip()
                    if raw_err:
                        detail = f" — {raw_err[:300]}"
                except Exception:
                    pass
                raise RuntimeError(f"{router_label} HTTP {http_err.code} at {config.endpoint}{detail}") from http_err
            else:
                raise
        usage = data.get("usage", {})
        prompt_toks = int(usage.get("prompt_tokens", 0))
        comp_toks = int(usage.get("completion_tokens", 0))
        total_toks = int(usage.get("total_tokens", prompt_toks + comp_toks))
        cost = float(usage.get("cost") or 0.0)
        if cost <= 0.0 and gw == "nanogpt" and (prompt_toks > 0 or comp_toks > 0):
            cost = (
                (prompt_toks / 1_000_000.0) * config.input_cost_per_1m
                + (comp_toks / 1_000_000.0) * config.output_cost_per_1m
            )
            data.setdefault("cost_usd", round(cost, 8))
        elif gw in self._OPENAI_COMPAT_GATEWAYS:
            data.setdefault("cost_usd", 0.0)
        data.setdefault("gateway", gw)
        data.setdefault("endpoint", config.endpoint)
        self.record_usage(alias, prompt_toks, comp_toks, total_toks, cost)
        return data

    @staticmethod
    def _detect_image_mime(raw_bytes: bytes, declared_mime: Optional[str] = None) -> tuple[str, str]:
        """Return (mime_type, ext) inferred from magic bytes or declared MIME."""
        if raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png", ".png"
        if raw_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg", ".jpg"
        if len(raw_bytes) >= 12 and raw_bytes[:4] == b"RIFF" and raw_bytes[8:12] == b"WEBP":
            return "image/webp", ".webp"
        if raw_bytes.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif", ".gif"
        if declared_mime:
            clean = declared_mime.split(";")[0].strip().lower()
            ext_map = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }
            if clean in ext_map:
                return ("image/jpeg" if clean == "image/jpg" else clean), ext_map[clean]
        return "image/png", ".png"

    @classmethod
    def _decode_data_url_or_b64(cls, value: str, declared_mime: Optional[str] = None) -> tuple[Optional[bytes], str, str]:
        """Decode either a data:image/... URI or raw base64 string into (bytes, mime, ext)."""
        if not value or not isinstance(value, str):
            return None, "image/png", ".png"
        m = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", value.strip(), re.DOTALL)
        if m:
            declared_mime = m.group(1)
            b64_part = re.sub(r"\s+", "", m.group(2))
        else:
            b64_part = re.sub(r"\s+", "", value.strip())
        try:
            raw = base64.b64decode(b64_part)
        except Exception:
            return None, "image/png", ".png"
        mime, ext = cls._detect_image_mime(raw, declared_mime=declared_mime)
        return raw, mime, ext

    @classmethod
    def _extract_openrouter_image(cls, data: Dict[str, Any]) -> tuple[Optional[bytes], str, str, str]:
        """Extract (image_bytes, mime_type, ext, caption) from an OpenRouter image completion payload."""
        choices = data.get("choices") or []
        if not choices:
            return None, "image/png", ".png", ""
        msg = choices[0].get("message") or {}
        caption_parts: List[str] = []

        # 1. OpenRouter standard msg["images"] list
        for img_item in msg.get("images") or []:
            if not isinstance(img_item, dict):
                continue
            url = (
                (img_item.get("image_url") or {}).get("url")
                if isinstance(img_item.get("image_url"), dict)
                else img_item.get("image_url")
            ) or img_item.get("url")
            b64 = img_item.get("b64_json") or img_item.get("data")
            if url and str(url).startswith("data:image/"):
                raw, mime, ext = cls._decode_data_url_or_b64(str(url))
                if raw:
                    return raw, mime, ext, ""
            if b64:
                raw, mime, ext = cls._decode_data_url_or_b64(str(b64))
                if raw:
                    return raw, mime, ext, ""
            if url and str(url).startswith(("http://", "https://")):
                try:
                    with urllib.request.urlopen(str(url), timeout=20.0) as r:
                        raw = r.read()
                        mime, ext = cls._detect_image_mime(raw, declared_mime=r.headers.get("Content-Type"))
                        if raw:
                            return raw, mime, ext, ""
                except Exception:
                    pass

        # 2. Structured list or data URI inside msg["content"]
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and block.get("text"):
                    caption_parts.append(str(block["text"]))
                elif block.get("type") in ("image_url", "image", "output_image"):
                    url = (
                        (block.get("image_url") or {}).get("url")
                        if isinstance(block.get("image_url"), dict)
                        else block.get("image_url")
                    ) or block.get("url")
                    b64 = block.get("b64_json") or block.get("data")
                    if url and str(url).startswith("data:image/"):
                        raw, mime, ext = cls._decode_data_url_or_b64(str(url))
                        if raw:
                            return raw, mime, ext, " ".join(caption_parts).strip()
                    if b64:
                        raw, mime, ext = cls._decode_data_url_or_b64(str(b64))
                        if raw:
                            return raw, mime, ext, " ".join(caption_parts).strip()
        elif isinstance(content, str) and content:
            m = re.search(r"(data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+)", content)
            if m:
                raw, mime, ext = cls._decode_data_url_or_b64(m.group(1))
                cleaned_caption = re.sub(r"!\[[^\]]*\]\(data:image/[^)]+\)", "", content)
                cleaned_caption = cleaned_caption.replace(m.group(1), "").strip()
                if raw:
                    return raw, mime, ext, cleaned_caption
            caption_parts.append(content.strip())

        return None, "image/png", ".png", " ".join(caption_parts).strip()

    def dispatch_image_generation(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        gateway: Optional[str] = None,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """Generate a 2D raster image using OpenRouter image modalities or NanoGPT image API."""
        clean_prompt = (prompt or "").strip()
        if not clean_prompt:
            return {"ok": False, "error": "Image generation prompt is required."}

        openrouter_key = self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")
        nanogpt_key = self.nanogpt_key if self.nanogpt_key is not None else os.environ.get("NANOGPT_API_KEY")
        errors: List[str] = []

        # 1. Try OpenRouter chat completions with modalities=["image", "text"]
        if gateway != "nanogpt" and openrouter_key:
            candidates: List[str] = []
            for m in (model, self.DEFAULT_IMAGE_MODEL, self.FALLBACK_IMAGE_MODEL, self.TERTIARY_IMAGE_MODEL):
                if m and not m.startswith("nanogpt/") and m not in candidates:
                    candidates.append(m)
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/NoJuanNobody/tin-can",
                "X-Title": "TinCan 2 / IoT Federated Agent Memory",
            }
            for idx, candidate in enumerate(candidates):
                payload: Dict[str, Any] = {
                    "model": candidate,
                    "modalities": ["image", "text"],
                    "messages": [{"role": "user", "content": clean_prompt}],
                }
                if aspect_ratio:
                    payload["image_config"] = {"aspect_ratio": aspect_ratio}
                req = urllib.request.Request(
                    self.OPENROUTER_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    raw, mime, ext, caption = self._extract_openrouter_image(data)
                    if raw:
                        usage = data.get("usage") or {}
                        p_toks = int(usage.get("prompt_tokens", 0))
                        c_toks = int(usage.get("completion_tokens", 0))
                        t_toks = int(usage.get("total_tokens", p_toks + c_toks))
                        cost = float(usage.get("cost") or 0.039)
                        self.record_usage(candidate, p_toks, c_toks, t_toks, cost)
                        return {
                            "ok": True,
                            "gateway": "openrouter",
                            "model": data.get("model") or candidate,
                            "mime_type": mime,
                            "ext": ext,
                            "size_bytes": len(raw),
                            "image_bytes": raw,
                            "image_b64": base64.b64encode(raw).decode("ascii"),
                            "caption": caption,
                            "cost_usd": cost,
                            "usage": usage,
                            "simulated": False,
                        }
                    errors.append(f"{candidate}: OpenRouter response contained no image payload")
                except urllib.error.HTTPError as http_err:
                    detail = ""
                    try:
                        detail = http_err.read().decode("utf-8", errors="replace").strip()[:240]
                    except Exception:
                        pass
                    errors.append(f"{candidate}: HTTP {http_err.code}{' — ' + detail if detail else ''}")
                    if http_err.code in (400, 404, 422) and idx + 1 < len(candidates):
                        continue
                    if http_err.code == 402:
                        break
                except Exception as err:
                    errors.append(f"{candidate}: {err}")

        # 2. Try NanoGPT Image API fallback or explicit gateway="nanogpt"
        if nanogpt_key:
            primary_nano = model[len("nanogpt/"):] if model and model.startswith("nanogpt/") else (
                model if gateway == "nanogpt" and model else self.NANOGPT_DEFAULT_IMAGE_MODEL
            )
            nano_candidates: List[str] = []
            for nm in (primary_nano, self.NANOGPT_DEFAULT_IMAGE_MODEL, self.NANOGPT_FALLBACK_IMAGE_MODEL):
                if nm and nm not in nano_candidates:
                    nano_candidates.append(nm)
            headers = {
                "Authorization": f"Bearer {nanogpt_key}",
                "Content-Type": "application/json",
            }
            for nano_model in nano_candidates:
                payload = {
                    "model": nano_model,
                    "prompt": clean_prompt,
                    "n": 1,
                    "response_format": "b64_json",
                }
                req = urllib.request.Request(
                    self.NANOGPT_IMAGE_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("data") or []
                    first = items[0] if items and isinstance(items[0], dict) else {}
                    raw = None
                    mime, ext = "image/png", ".png"
                    if first.get("b64_json"):
                        raw, mime, ext = self._decode_data_url_or_b64(str(first["b64_json"]))
                    elif first.get("url"):
                        with urllib.request.urlopen(str(first["url"]), timeout=20.0) as img_r:
                            raw = img_r.read()
                            mime, ext = self._detect_image_mime(raw, declared_mime=img_r.headers.get("Content-Type"))
                    if raw:
                        cost = float(data.get("cost") or 0.04)
                        self.record_usage(f"nanogpt/{nano_model}", len(clean_prompt.split()), 0, len(clean_prompt.split()), cost)
                        return {
                            "ok": True,
                            "gateway": "nanogpt",
                            "model": f"nanogpt/{nano_model}",
                            "mime_type": mime,
                            "ext": ext,
                            "size_bytes": len(raw),
                            "image_bytes": raw,
                            "image_b64": base64.b64encode(raw).decode("ascii"),
                            "caption": str(first.get("revised_prompt") or ""),
                            "cost_usd": cost,
                            "usage": {"cost": cost},
                            "simulated": False,
                        }
                    errors.append(f"nanogpt/{nano_model}: empty image response")
                except urllib.error.HTTPError as http_err:
                    detail = ""
                    try:
                        detail = http_err.read().decode("utf-8", errors="replace").strip()[:240]
                    except Exception:
                        pass
                    errors.append(f"nanogpt/{nano_model}: HTTP {http_err.code}{' — ' + detail if detail else ''}")
                except Exception as err:
                    errors.append(f"nanogpt/{nano_model}: {err}")

        if not openrouter_key and not nanogpt_key:
            return {
                "ok": False,
                "simulated": True,
                "error": "No OPENROUTER_API_KEY or NANOGPT_API_KEY configured for 2D image generation.",
            }
        return {
            "ok": False,
            "simulated": False,
            "error": "; ".join(errors) or "2D image generation failed.",
        }
