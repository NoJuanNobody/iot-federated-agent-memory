"""Telemetry, arbitrage accounting, and pre-flight cost estimation for DynamicAIGatewayRouter."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .ai_gateway import (
    DEFAULT_NANOGPT_MODELS,
    DEFAULT_OPENROUTER_MODELS,
    DEFAULT_OLLAMA_BASE_URL,
    OWLCHAT_BASE_URL,
    DynamicAIGatewayRouter,
    resolve_owlchat_key,
)

_ZERO_BURN_GATEWAYS = frozenset({"ollama", "local", "fau-owlchat", "owlchat", "trussed", "fau-trussed"})
_LOCAL_GATEWAYS = frozenset({"ollama", "local"})
_DEFAULT_FRONTIER_RATES = (3.0, 15.0)
_DEFAULT_CLOUD_TURN_SAVED_USD = 0.02
_CREDITS_PER_USD = 1000.0


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _safe_call(obj: Any, method_name: str, *args: Any, **kwargs: Any) -> Any:
    if obj is None:
        return None
    fn = getattr(obj, method_name, None)
    if not callable(fn):
        return None
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


def _read_field(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def classify_gateway(alias_or_config: Any, *, router: Any = None) -> str:
    """Normalize a model alias, provider config, or routing entry into a canonical gateway id."""
    if isinstance(alias_or_config, str):
        raw = alias_or_config.strip()
        low = raw.lower()
        if not raw or raw == "ollama-brain" or low.startswith("ollama/") or ":11434" in low or low == "ollama":
            return "ollama"
        if (
            raw in ("owlchat-brain", "trussed-brain")
            or low.startswith(("owlchat/", "trussed/"))
            or "chat.hpc.fau.edu" in low
            or "trussed.ai.hpc.fau.edu" in low
            or low in ("owlchat", "fau-owlchat", "trussed", "fau-trussed")
        ):
            return "fau-owlchat"
        if raw == "local-brain" or low.startswith(("local/", "openai-compat/")) or low == "local":
            return "local"
        if raw.startswith(("ronin/", "rodin/", "hyper3d/")) or low in ("ronin", "rodin", "hyper3d"):
            return "hyper3d"
        if (
            raw == "nanogpt-brain"
            or low.startswith(("nanogpt/", "tee/", "abliteration-ai/", "huihui-ai/", "pqhaz/", "xtools-at/"))
            or "abliterated" in low
            or low.endswith("-heretic")
            or "-heretic:" in low
            or low in ("nanogpt", "nanogpt-tee")
        ):
            return "nanogpt-tee"
        return "openrouter"

    # Provider config object or serialized provider dict
    if router is not None and not isinstance(alias_or_config, dict):
        gw_hint = _safe_call(router, "_provider_gateway", alias_or_config)
        if isinstance(gw_hint, str) and gw_hint:
            return classify_gateway(gw_hint)

    api_key_env = _safe_str(_read_field(alias_or_config, "api_key_env")).upper()
    endpoint = _safe_str(_read_field(alias_or_config, "endpoint")).lower()
    lab_id = _safe_str(_read_field(alias_or_config, "lab_id")).lower()
    gateway = _safe_str(_read_field(alias_or_config, "gateway")).lower()
    model_alias = _safe_str(_read_field(alias_or_config, "model_alias") or _read_field(alias_or_config, "model"))

    if api_key_env == "OLLAMA_API_KEY" or gateway == "ollama" or lab_id == "ollama" or ":11434" in endpoint:
        return "ollama"
    if (
        api_key_env in ("OWLCHAT_API_KEY", "TRUSSED_AI_API_KEY")
        or gateway in ("owlchat", "trussed", "fau-owlchat")
        or lab_id in ("owlchat", "trussed")
        or "hpc.fau.edu" in endpoint
    ):
        return "fau-owlchat"
    if api_key_env == "TINCAN_AI_API_KEY" or gateway == "local" or lab_id == "local":
        return "local"
    if api_key_env == "NANOGPT_API_KEY" or gateway in ("nanogpt", "nanogpt-tee") or lab_id == "nanogpt" or "nano-gpt.com" in endpoint:
        return "nanogpt-tee"
    if api_key_env == "HYPER3D_API_KEY" or gateway in ("hyper3d", "ronin") or lab_id in ("ronin", "hyper3d", "rodin"):
        return "hyper3d"
    if model_alias:
        return classify_gateway(model_alias)
    return "openrouter"


def _lookup_model_rates(model_alias: str, router: Any = None) -> Tuple[float, float]:
    """Return (input_per_1m_usd, output_per_1m_usd) for a cloud model alias."""
    if router is not None:
        providers = getattr(router, "providers", None)
        if isinstance(providers, dict) and model_alias in providers:
            cfg = providers[model_alias]
            in_rate = _safe_float(_read_field(cfg, "input_cost_per_1m"), -1.0)
            out_rate = _safe_float(_read_field(cfg, "output_cost_per_1m"), -1.0)
            if in_rate >= 0.0 and out_rate >= 0.0:
                return (in_rate, out_rate)
        rates = _safe_call(router, "_lookup_catalog_rates", model_alias)
        if isinstance(rates, (tuple, list)) and len(rates) == 2:
            return (_safe_float(rates[0], 1.0), _safe_float(rates[1], 3.0))

    if model_alias in DynamicAIGatewayRouter.DEFAULT_LABS:
        cfg = DynamicAIGatewayRouter.DEFAULT_LABS[model_alias]
        return (float(cfg.input_cost_per_1m), float(cfg.output_cost_per_1m))

    stripped_nano = model_alias[len("nanogpt/") :] if model_alias.startswith("nanogpt/") else model_alias
    candidates = {model_alias, stripped_nano, f"nanogpt/{stripped_nano}"}
    for pool in (DEFAULT_OPENROUTER_MODELS, DEFAULT_NANOGPT_MODELS):
        for item in pool:
            if item.get("id") in candidates or item.get("upstream_id") in candidates:
                pricing = item.get("pricing") or {}
                if "prompt_per_1m" in pricing or "completion_per_1m" in pricing:
                    return (
                        _safe_float(pricing.get("prompt_per_1m"), 0.5),
                        _safe_float(pricing.get("completion_per_1m"), 1.5),
                    )
                p_raw = str(pricing.get("prompt") or "0")
                c_raw = str(pricing.get("completion") or "0")
                if "/gen" not in p_raw:
                    return (
                        _safe_float(p_raw, 0.0) * 1_000_000.0,
                        _safe_float(c_raw, 0.0) * 1_000_000.0,
                    )

    if classify_gateway(model_alias) == "nanogpt-tee":
        return (0.5, 1.5)
    return (1.0, 3.0)


def estimate_preflight(
    model_alias: str,
    prompt_chars: int = 0,
    *,
    router: Any = None,
) -> Dict[str, Any]:
    """Estimate pre-flight credits, USD cost, and recommended route for a prompt before dispatch."""
    alias = _safe_str(model_alias).strip() or "ollama/qwen2.5:3b"
    chars = max(0, _safe_int(prompt_chars, 0))
    est_prompt_tokens = max(1, (chars + 3) // 4) if chars > 0 else 128
    est_completion_tokens = max(128, min(1024, (est_prompt_tokens // 2) + 128))

    gw = classify_gateway(alias, router=router)
    zero_burn = gw in _ZERO_BURN_GATEWAYS

    eq_in, eq_out = _DEFAULT_FRONTIER_RATES
    cloud_eq_usd = round(
        (est_prompt_tokens / 1_000_000.0) * eq_in + (est_completion_tokens / 1_000_000.0) * eq_out,
        6,
    )
    cloud_eq_credits = max(3, int(round(cloud_eq_usd * _CREDITS_PER_USD)))

    if zero_burn:
        route_map = {
            "ollama": "direct ollama localhost:11434",
            "fau-owlchat": "direct fau-owlchat hpc",
            "local": "direct openai-compat local",
        }
        recommended_route = route_map.get(gw, "direct local zero-burn")
        return {
            "model_alias": alias,
            "gateway": gw,
            "is_local": gw in _LOCAL_GATEWAYS,
            "is_zero_burn": True,
            "estimated_credits": 0,
            "credits_label": "0 CR",
            "estimated_usd": 0.0,
            "cloud_equivalent_credits": cloud_eq_credits,
            "cloud_equivalent_usd": cloud_eq_usd,
            "estimated_prompt_tokens": est_prompt_tokens,
            "estimated_completion_tokens": est_completion_tokens,
            "recommended_route": recommended_route,
            "display_badge": f"Est: 0 CR Free | Cloud Eq: {cloud_eq_credits} CR",
        }

    if gw == "hyper3d":
        low = alias.lower()
        tier_usd = 0.25 if "sketch" in low else (1.00 if "detail" in low else (0.75 if "smooth" in low else 0.50))
        credits = int(round(tier_usd * _CREDITS_PER_USD))
        return {
            "model_alias": alias,
            "gateway": "hyper3d",
            "is_local": False,
            "is_zero_burn": False,
            "estimated_credits": credits,
            "credits_label": f"{credits} CR",
            "estimated_usd": tier_usd,
            "cloud_equivalent_credits": credits,
            "cloud_equivalent_usd": tier_usd,
            "estimated_prompt_tokens": est_prompt_tokens,
            "estimated_completion_tokens": 48,
            "recommended_route": "hyper3d rodin v2",
            "display_badge": f"Est: {credits} CR (${tier_usd:.2f})",
        }

    in_per_1m, out_per_1m = _lookup_model_rates(alias, router=router)
    est_usd = round(
        (est_prompt_tokens / 1_000_000.0) * in_per_1m + (est_completion_tokens / 1_000_000.0) * out_per_1m,
        6,
    )
    est_credits = max(1, int(round(est_usd * _CREDITS_PER_USD)))
    recommended_route = "nanogpt-tee enclave" if gw == "nanogpt-tee" else "openrouter pooled"
    return {
        "model_alias": alias,
        "gateway": gw,
        "is_local": False,
        "is_zero_burn": False,
        "estimated_credits": est_credits,
        "credits_label": f"{est_credits} CR",
        "estimated_usd": est_usd,
        "cloud_equivalent_credits": max(est_credits, cloud_eq_credits),
        "cloud_equivalent_usd": max(est_usd, cloud_eq_usd),
        "estimated_prompt_tokens": est_prompt_tokens,
        "estimated_completion_tokens": est_completion_tokens,
        "recommended_route": recommended_route,
        "display_badge": f"Est: {est_credits} CR (~${est_usd:.4f})",
    }


def _collect_analytics_dict(router: Any) -> Dict[str, Any]:
    if router is None:
        return {}
    get_analytics = getattr(router, "get_analytics", None)
    if not callable(get_analytics):
        return {}
    try:
        res = get_analytics(include_live_billing=False)
    except TypeError:
        try:
            res = get_analytics()
        except Exception:
            return {}
    except Exception:
        return {}
    return res if isinstance(res, dict) else {}


def _collect_billing_dict(router: Any, method_name: str, fallback: Any) -> Dict[str, Any]:
    res = _safe_call(router, method_name)
    if isinstance(res, dict):
        return res
    return dict(fallback) if isinstance(fallback, dict) else {}


def _collect_vfs_context(space_owner: str, vfs: Any) -> Dict[str, Any]:
    owner = _safe_str(space_owner).strip()
    merkle_root = ""
    raw_files: List[Dict[str, Any]] = []

    if vfs is not None:
        if not owner:
            owner = _safe_str(getattr(vfs, "owner_id", "")).strip()
        summary = _safe_call(vfs, "get_summary")
        if isinstance(summary, dict):
            owner = owner or _safe_str(summary.get("owner_id")).strip()
            merkle_root = _safe_str(summary.get("merkle_root"))
            if isinstance(summary.get("files"), list):
                raw_files = summary["files"]
        if not merkle_root:
            merkle_root = _safe_str(_safe_call(vfs, "compute_merkle_root"))
        if not raw_files:
            listed = _safe_call(vfs, "list_files")
            if isinstance(listed, list):
                raw_files = listed
            elif isinstance(getattr(vfs, "files", None), list):
                raw_files = getattr(vfs, "files")

    files_out: List[Dict[str, Any]] = []
    for item in raw_files[:20]:
        if not isinstance(item, dict):
            continue
        path = _safe_str(item.get("path"))
        if not path:
            continue
        size_bytes = _safe_int(item.get("size_bytes"), 0)
        files_out.append(
            {
                "path": path,
                "size_bytes": size_bytes,
                "est_tokens": max(1, (size_bytes + 3) // 4) if size_bytes > 0 else 0,
                "mime_type": _safe_str(item.get("mime_type"), "text/plain"),
            }
        )

    return {
        "owner_id": owner or "default_user",
        "merkle_root": merkle_root,
        "file_count": len(raw_files) if raw_files else len(files_out),
        "files": files_out,
    }


def _aggregate_usage(
    router: Any,
    analytics: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = {
        gw: {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        for gw in ("ollama", "local", "fau-owlchat", "nanogpt-tee", "openrouter", "hyper3d")
    }

    raw_providers = getattr(router, "providers", None)
    if not isinstance(raw_providers, dict) or not raw_providers:
        raw_providers = analytics.get("providers") if isinstance(analytics.get("providers"), dict) else {}

    prov_local_turns = 0
    prov_cloud_turns = 0
    prov_local_prompt_toks = 0
    prov_local_comp_toks = 0
    prov_total_tokens = 0

    for alias, cfg in raw_providers.items():
        if not isinstance(cfg, dict) and not hasattr(cfg, "model_alias"):
            continue
        gw = classify_gateway(cfg, router=router)
        if gw not in buckets:
            gw = "openrouter"
        calls = _safe_int(_read_field(cfg, "total_calls"), 0)
        prompt_toks = _safe_int(_read_field(cfg, "total_prompt_tokens", _read_field(cfg, "prompt_tokens")), 0)
        comp_toks = _safe_int(_read_field(cfg, "total_completion_tokens", _read_field(cfg, "completion_tokens")), 0)
        tokens = _safe_int(_read_field(cfg, "total_tokens"), prompt_toks + comp_toks)
        cost = _safe_float(_read_field(cfg, "total_cost", _read_field(cfg, "cost_usd")), 0.0)

        buckets[gw]["calls"] += calls
        buckets[gw]["tokens"] += tokens
        buckets[gw]["cost_usd"] += cost
        prov_total_tokens += tokens

        if gw in _ZERO_BURN_GATEWAYS:
            prov_local_turns += calls
            prov_local_prompt_toks += prompt_toks
            prov_local_comp_toks += comp_toks
        else:
            prov_cloud_turns += calls

    raw_log = getattr(router, "routing_log", None)
    if not isinstance(raw_log, list):
        raw_log = analytics.get("recent_routing_log") if isinstance(analytics.get("recent_routing_log"), list) else []

    log_local_turns = 0
    log_cloud_turns = 0
    for entry in raw_log:
        if not isinstance(entry, dict):
            continue
        gw_hint = _safe_str(entry.get("lab") or entry.get("gateway") or entry.get("model") or entry.get("alias"))
        gw = classify_gateway(gw_hint)
        if gw in _ZERO_BURN_GATEWAYS:
            log_local_turns += 1
        else:
            log_cloud_turns += 1

    local_turns = max(prov_local_turns, log_local_turns)
    cloud_turns = max(prov_cloud_turns, log_cloud_turns)
    analytics_calls = _safe_int(analytics.get("total_calls"), 0)
    analytics_tokens = _safe_int(analytics.get("total_tokens"), 0)

    if (local_turns + cloud_turns) == 0 and analytics_calls > 0:
        cloud_turns = analytics_calls

    total_calls = max(local_turns + cloud_turns, analytics_calls)
    total_tokens = max(prov_total_tokens, analytics_tokens)
    total_turns = local_turns + cloud_turns
    local_ratio = round(local_turns / total_turns, 4) if total_turns > 0 else 0.0

    token_saved_usd = (prov_local_prompt_toks / 1_000_000.0) * 3.0 + (prov_local_comp_toks / 1_000_000.0) * 15.0
    estimated_usd_saved = (
        round(max(local_turns * _DEFAULT_CLOUD_TURN_SAVED_USD, token_saved_usd), 4)
        if local_turns > 0
        else 0.0
    )

    arbitrage = {
        "local_turns": local_turns,
        "cloud_turns": cloud_turns,
        "local_ratio": local_ratio,
        "estimated_usd_saved": estimated_usd_saved,
        "total_calls": total_calls,
        "total_tokens": total_tokens,
    }
    return buckets, arbitrage


def _strip_model_subset(models: Any, *, limit: int = 16) -> List[Dict[str, Any]]:
    if not isinstance(models, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in models[:limit]:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        out.append(
            {
                "id": item.get("id"),
                "name": item.get("name") or item.get("id"),
                "gateway": item.get("gateway") or classify_gateway(str(item.get("id"))),
                "category": item.get("category") or "",
                "context_length": _safe_int(item.get("context_length"), 8192),
                "pricing": item.get("pricing") if isinstance(item.get("pricing"), dict) else {},
            }
        )
    return out


def collect_gateway_telemetry(
    router: Any,
    space_owner: str = "",
    vfs: Any = None,
) -> Dict[str, Any]:
    """Collect normalized gateway status cards, arbitrage savings, and Space context safely."""
    analytics = _collect_analytics_dict(router)
    nano_billing = _collect_billing_dict(router, "get_nanogpt_billing", analytics.get("nanogpt"))
    or_billing = _collect_billing_dict(router, "get_openrouter_billing", analytics.get("openrouter"))

    ollama_models = _safe_call(router, "get_ollama_models")
    if not isinstance(ollama_models, list):
        ollama_models = []

    nanogpt_models = _safe_call(router, "get_nanogpt_models", include_live_public=False)
    if nanogpt_models is None:
        nanogpt_models = _safe_call(router, "get_nanogpt_models")
    if not isinstance(nanogpt_models, list):
        nanogpt_models = []

    available_models = _safe_call(router, "get_available_models")
    if not isinstance(available_models, list):
        available_models = []

    buckets, arbitrage = _aggregate_usage(router, analytics)

    ollama_url = _safe_str(getattr(router, "ollama_base_url", "")) or DEFAULT_OLLAMA_BASE_URL
    ollama_calls = buckets["ollama"]["calls"] + buckets["local"]["calls"]
    ollama_tokens = buckets["ollama"]["tokens"] + buckets["local"]["tokens"]
    ollama_connected = len(ollama_models) > 0 or ollama_calls > 0

    owl_key = _safe_str(getattr(router, "owlchat_key", "")) or resolve_owlchat_key()
    owl_url = _safe_str(getattr(router, "OWLCHAT_BASE_URL", "")) or OWLCHAT_BASE_URL
    owl_calls = buckets["fau-owlchat"]["calls"]
    owl_tokens = buckets["fau-owlchat"]["tokens"]
    owl_configured = bool(owl_key)
    owl_connected = owl_configured or owl_calls > 0

    nano_key = _safe_str(getattr(router, "nanogpt_key", "")) or _safe_str(os.environ.get("NANOGPT_API_KEY"))
    nano_connected = bool(nano_billing.get("connected", False))
    nano_bal = _safe_float(nano_billing.get("account_remaining_balance_usd"), 0.0)
    nano_configured = bool(nano_key or nano_connected or nano_bal > 0.0)
    nano_rate_label = (
        f"${nano_bal:.2f} pool"
        if (nano_connected or nano_bal > 0.0)
        else ("TEE · configured" if nano_configured else "$0.00 offline")
    )

    or_key = _safe_str(getattr(router, "openrouter_key", "")) or _safe_str(os.environ.get("OPENROUTER_API_KEY"))
    or_connected = bool(or_billing.get("connected", False))
    or_bal = _safe_float(or_billing.get("account_remaining_balance_usd"), 0.0)
    or_configured = bool(or_key or or_connected or or_bal > 0.0)
    or_rate_label = (
        f"${or_bal:.2f} pool"
        if (or_connected or or_bal > 0.0)
        else ("Cloud · configured" if or_configured else "$0.00 offline")
    )
    openrouter_models = [
        m for m in available_models if isinstance(m, dict) and str(m.get("gateway", "openrouter")).lower() == "openrouter"
    ]

    gateways: List[Dict[str, Any]] = [
        {
            "id": "ollama",
            "name": "ollama (local)",
            "priority": 1,
            "rate_label": "FREE · $0.00",
            "connected": ollama_connected,
            "configured": bool(ollama_url),
            "balance_usd": 0.0,
            "endpoint": ollama_url,
            "models_count": len(ollama_models),
            "calls": ollama_calls,
            "tokens": ollama_tokens,
            "cost_usd": 0.0,
            "quota_pct": 100 if ollama_connected else 68,
            "is_zero_burn": True,
        },
        {
            "id": "fau-owlchat",
            "name": "fau-owlchat",
            "priority": 2,
            "rate_label": "BYOK · HPC",
            "connected": owl_connected,
            "configured": owl_configured,
            "balance_usd": 0.0,
            "endpoint": owl_url,
            "models_count": 0,
            "calls": owl_calls,
            "tokens": owl_tokens,
            "cost_usd": 0.0,
            "quota_pct": 85 if owl_connected else 24,
            "is_zero_burn": True,
        },
        {
            "id": "nanogpt-tee",
            "name": "nanogpt-tee",
            "priority": 3,
            "rate_label": nano_rate_label,
            "connected": nano_connected,
            "configured": nano_configured,
            "balance_usd": round(nano_bal, 4),
            "endpoint": _safe_str(nano_billing.get("endpoint")) or DynamicAIGatewayRouter.NANOGPT_ENDPOINT,
            "models_count": len(nanogpt_models),
            "calls": buckets["nanogpt-tee"]["calls"],
            "tokens": buckets["nanogpt-tee"]["tokens"],
            "cost_usd": round(buckets["nanogpt-tee"]["cost_usd"], 6),
            "quota_pct": min(100, max(12, int(round((nano_bal / 50.0) * 100)))) if (nano_connected or nano_bal > 0) else (24 if nano_configured else 10),
            "is_zero_burn": False,
        },
        {
            "id": "openrouter",
            "name": "openrouter",
            "priority": 4,
            "rate_label": or_rate_label,
            "connected": or_connected,
            "configured": or_configured,
            "balance_usd": round(or_bal, 4),
            "endpoint": DynamicAIGatewayRouter.OPENROUTER_ENDPOINT,
            "models_count": len(openrouter_models),
            "calls": buckets["openrouter"]["calls"],
            "tokens": buckets["openrouter"]["tokens"],
            "cost_usd": round(buckets["openrouter"]["cost_usd"], 6),
            "quota_pct": min(100, max(12, int(round((or_bal / 150.0) * 100)))) if (or_connected or or_bal > 0) else (24 if or_configured else 10),
            "is_zero_burn": False,
        },
    ]

    return {
        "gateways": gateways,
        "arbitrage": arbitrage,
        "active_route": {
            "gateway": "ollama",
            "label": "direct ollama localhost:11434",
            "status_text": "DIRECT LOCALHOST:11434 · 0ms HOP",
        },
        "space": _collect_vfs_context(space_owner, vfs),
        "models": {
            "ollama": _strip_model_subset(ollama_models),
            "nanogpt": _strip_model_subset(nanogpt_models),
            "openrouter": _strip_model_subset(openrouter_models),
        },
        "collected_at": time.time(),
    }


__all__ = [
    "classify_gateway",
    "collect_gateway_telemetry",
    "estimate_preflight",
]
