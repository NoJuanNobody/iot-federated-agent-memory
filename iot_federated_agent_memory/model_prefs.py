"""Unified Text / Image / Video / World Model Preferences for all TinCan harnesses & terminals.

Persists user/operator modality model preferences to both:
  1. JSON file (``TINCAN_MODEL_PREFS_PATH``, ``/data/model_prefs.json`` on Railway,
     or ``~/.tincan/model_prefs.json`` locally), and
  2. Optional ``PeerAccountRegistry.economy_settings['model_preferences']`` in SQLite.

Resolves NanoGPT and OpenRouter endpoints, API keys, and model env vars for every
coding harness (claude-code, codex, opencode, aider, goose, dsx, antigravity,
gemini-cli) and every interactive terminal (bash, zsh, sh).
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Mapping, Optional

NANOGPT_OPENAI_BASE_URL = "https://nano-gpt.com/api/v1"
NANOGPT_ANTHROPIC_BASE_URL = "https://nano-gpt.com/api/v1"
OPENROUTER_OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_ANTHROPIC_BASE_URL = "https://openrouter.ai/api"

MODALITIES = ("text", "image", "video", "world")

DEFAULT_MODEL_PREFS: Dict[str, Any] = {
    "version": 1,
    "default_provider": "nanogpt",
    "modalities": {
        "text": {
            "provider": "nanogpt",
            "model": "nanogpt/TEE/deepseek-v4.1-flash",
            "fallback_provider": "openrouter",
            "fallback_model": "anthropic/claude-sonnet-4",
        },
        "image": {
            "provider": "nanogpt",
            "model": "nanogpt/flux-pro",
            "fallback_provider": "openrouter",
            "fallback_model": "openai/gpt-image-1",
        },
        "video": {
            "provider": "nanogpt",
            "model": "nanogpt/kling-v2.1",
            "fallback_provider": "openrouter",
            "fallback_model": "google/veo-2",
        },
        "world": {
            "provider": "worldlabs",
            "model": "worldlabs/marble-v2",
            "fallback_provider": "hyper3d-rodin",
            "fallback_model": "rodin/Regular",
        },
    },
    "harness_overrides": {},
}


def default_prefs_path() -> str:
    """Return the canonical JSON path for saved model preferences."""
    explicit = (os.environ.get("TINCAN_MODEL_PREFS_PATH") or "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data/model_prefs.json"
    return os.path.expanduser("~/.tincan/model_prefs.json")


def normalize_model_prefs(raw: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Deep-merge arbitrary input into a valid, complete model preferences document."""
    base = copy.deepcopy(DEFAULT_MODEL_PREFS)
    if not isinstance(raw, Mapping):
        return base

    if isinstance(raw.get("default_provider"), str) and raw["default_provider"].strip():
        base["default_provider"] = raw["default_provider"].strip().lower()

    raw_mods = raw.get("modalities")
    if isinstance(raw_mods, Mapping):
        for mod in MODALITIES:
            entry = raw_mods.get(mod)
            if isinstance(entry, Mapping):
                dst = base["modalities"][mod]
                for field in ("provider", "model", "fallback_provider", "fallback_model"):
                    val = entry.get(field)
                    if isinstance(val, str) and val.strip():
                        dst[field] = val.strip()

    # Also accept shorthand top-level keys like {"text": {"provider": ..., "model": ...}}
    for mod in MODALITIES:
        entry = raw.get(mod)
        if isinstance(entry, Mapping):
            dst = base["modalities"][mod]
            for field in ("provider", "model", "fallback_provider", "fallback_model"):
                val = entry.get(field)
                if isinstance(val, str) and val.strip():
                    dst[field] = val.strip()
        elif isinstance(entry, str) and entry.strip():
            base["modalities"][mod]["model"] = entry.strip()

    raw_overrides = raw.get("harness_overrides")
    if isinstance(raw_overrides, Mapping):
        cleaned: Dict[str, Dict[str, str]] = {}
        for hid, hcfg in raw_overrides.items():
            if not isinstance(hid, str) or not hid.strip():
                continue
            if isinstance(hcfg, Mapping):
                item: Dict[str, str] = {}
                if isinstance(hcfg.get("provider"), str) and hcfg["provider"].strip():
                    item["provider"] = hcfg["provider"].strip().lower()
                if isinstance(hcfg.get("model"), str) and hcfg["model"].strip():
                    item["model"] = hcfg["model"].strip()
                if item:
                    cleaned[hid.strip().lower()] = item
        base["harness_overrides"] = cleaned

    return base


def load_model_prefs(
    *,
    path: Optional[str] = None,
    registry: Optional[Any] = None,
) -> Dict[str, Any]:
    """Load saved model preferences from SQLite registry (if given) and/or JSON file."""
    if registry is not None and hasattr(registry, "get_economy_setting"):
        try:
            raw_db = registry.get_economy_setting("model_preferences")
            if raw_db:
                return normalize_model_prefs(json.loads(raw_db))
        except Exception:
            pass

    target = path or default_prefs_path()
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as fh:
                return normalize_model_prefs(json.load(fh))
        except Exception:
            pass
    return normalize_model_prefs(None)


def save_model_prefs(
    prefs: Mapping[str, Any],
    *,
    path: Optional[str] = None,
    registry: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist normalized model preferences to JSON file and optional SQLite registry."""
    normalized = normalize_model_prefs(prefs)
    target = path or default_prefs_path()
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(normalized, fh, indent=2)
        fh.write("\n")

    if registry is not None and hasattr(registry, "set_economy_setting"):
        try:
            registry.set_economy_setting("model_preferences", json.dumps(normalized))
        except Exception:
            pass
    return normalized


def _strip_provider_prefix(model: str, provider: str) -> str:
    m = (model or "").strip()
    low = m.lower()
    if provider == "nanogpt" and low.startswith("nanogpt/"):
        return m[len("nanogpt/"):]
    if provider == "openrouter" and low.startswith("openrouter/"):
        return m[len("openrouter/"):]
    return m


def _pick_provider_and_model(
    harness_id: str,
    prefs: Dict[str, Any],
    env: Mapping[str, str],
) -> tuple[str, str, str]:
    """Resolve (provider, model_id, api_key) for a harness using saved prefs + available keys."""
    hid = (harness_id or "bash").strip().lower()
    text_cfg = prefs.get("modalities", {}).get("text", {})
    override = (prefs.get("harness_overrides") or {}).get(hid) or {}

    provider = str(override.get("provider") or text_cfg.get("provider") or "nanogpt").strip().lower()
    model = str(override.get("model") or text_cfg.get("model") or "").strip()

    nano_key = (env.get("NANOGPT_API_KEY") or "").strip()
    or_key = (env.get("OPENROUTER_API_KEY") or "").strip()

    if provider == "nanogpt" and not nano_key and or_key:
        provider = str(text_cfg.get("fallback_provider") or "openrouter").strip().lower()
        model = str(text_cfg.get("fallback_model") or "anthropic/claude-sonnet-4").strip()
    elif provider == "openrouter" and not or_key and nano_key:
        provider = str(text_cfg.get("fallback_provider") or "nanogpt").strip().lower()
        model = str(text_cfg.get("fallback_model") or "nanogpt/TEE/deepseek-v4.1-flash").strip()

    api_key = nano_key if provider == "nanogpt" else (or_key if provider == "openrouter" else "")
    return provider, model, api_key


def resolve_harness_env(
    harness_id: str = "bash",
    *,
    prefs: Optional[Dict[str, Any]] = None,
    base_env: Optional[Mapping[str, str]] = None,
    prefs_path: Optional[str] = None,
    include_secrets: bool = True,
) -> Dict[str, str]:
    """Build environment variables plugging NanoGPT & OpenRouter into any harness or terminal."""
    env_src = base_env if base_env is not None else os.environ
    active = normalize_model_prefs(prefs) if prefs is not None else load_model_prefs(path=prefs_path)
    mods = active["modalities"]
    hid = (harness_id or "bash").strip().lower()

    provider, raw_model, api_key = _pick_provider_and_model(hid, active, env_src)
    clean_model = _strip_provider_prefix(raw_model, provider)

    out: Dict[str, str] = {
        "TINCAN_MODEL_PREFS_PATH": prefs_path or default_prefs_path(),
        "TINCAN_TEXT_PROVIDER": str(mods["text"]["provider"]),
        "TINCAN_TEXT_MODEL": str(mods["text"]["model"]),
        "TINCAN_IMAGE_PROVIDER": str(mods["image"]["provider"]),
        "TINCAN_IMAGE_MODEL": str(mods["image"]["model"]),
        "TINCAN_VIDEO_PROVIDER": str(mods["video"]["provider"]),
        "TINCAN_VIDEO_MODEL": str(mods["video"]["model"]),
        "TINCAN_WORLD_PROVIDER": str(mods["world"]["provider"]),
        "TINCAN_WORLD_MODEL": str(mods["world"]["model"]),
        "NANOGPT_BASE_URL": NANOGPT_OPENAI_BASE_URL,
        "OPENROUTER_BASE_URL": OPENROUTER_OPENAI_BASE_URL,
    }

    # Universal OpenAI-compatible bridge for shells, codex, aider, python scripts, etc.
    if provider == "nanogpt":
        out["OPENAI_BASE_URL"] = NANOGPT_OPENAI_BASE_URL
        out["OPENAI_API_BASE"] = NANOGPT_OPENAI_BASE_URL
        out["NANOGPT_MODEL"] = clean_model
        if include_secrets and api_key and not env_src.get("OPENAI_API_KEY"):
            out["OPENAI_API_KEY"] = api_key
    elif provider == "openrouter":
        out["OPENAI_BASE_URL"] = OPENROUTER_OPENAI_BASE_URL
        out["OPENAI_API_BASE"] = OPENROUTER_OPENAI_BASE_URL
        out["OPENROUTER_MODEL"] = clean_model
        if include_secrets and api_key and not env_src.get("OPENAI_API_KEY"):
            out["OPENAI_API_KEY"] = api_key

    # Harness-specific bridge variables
    if hid == "claude-code":
        if provider == "nanogpt" and api_key and not env_src.get("ANTHROPIC_API_KEY"):
            out["ANTHROPIC_BASE_URL"] = NANOGPT_ANTHROPIC_BASE_URL
            if include_secrets:
                out["ANTHROPIC_AUTH_TOKEN"] = api_key
                out["ANTHROPIC_API_KEY"] = ""
            out["CLAUDE_MODEL"] = clean_model
        elif provider == "openrouter" and api_key and not env_src.get("ANTHROPIC_API_KEY"):
            out["ANTHROPIC_BASE_URL"] = OPENROUTER_ANTHROPIC_BASE_URL
            if include_secrets:
                out["ANTHROPIC_AUTH_TOKEN"] = api_key
                out["ANTHROPIC_API_KEY"] = ""
            out["CLAUDE_MODEL"] = clean_model
    elif hid == "opencode":
        out["OPENCODE_MODEL"] = f"{provider}/{clean_model}" if provider in ("openrouter", "nanogpt") else raw_model
    elif hid == "codex":
        out["CODEX_MODEL"] = clean_model
    elif hid == "aider":
        out["AIDER_MODEL"] = f"openrouter/{clean_model}" if provider == "openrouter" else f"openai/{clean_model}"
    elif hid == "goose":
        if provider == "openrouter":
            out["GOOSE_PROVIDER"] = "openrouter"
            out["GOOSE_MODEL"] = clean_model
        elif provider == "nanogpt":
            out["GOOSE_PROVIDER"] = "openai"
            out["OPENAI_HOST"] = NANOGPT_OPENAI_BASE_URL
            out["GOOSE_MODEL"] = clean_model

    return out


def resolve_harness_model_flag(
    harness_id: str,
    *,
    prefs: Optional[Dict[str, Any]] = None,
    base_env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Return the preferred ``--model`` argument for a harness based on saved preferences."""
    env_src = base_env if base_env is not None else os.environ
    active = normalize_model_prefs(prefs) if prefs is not None else load_model_prefs()
    provider, raw_model, api_key = _pick_provider_and_model(harness_id, active, env_src)
    if not api_key or not raw_model:
        return None
    clean = _strip_provider_prefix(raw_model, provider)
    hid = (harness_id or "").strip().lower()
    if hid == "opencode" and provider in ("openrouter", "nanogpt"):
        return f"{provider}/{clean}"
    return clean
