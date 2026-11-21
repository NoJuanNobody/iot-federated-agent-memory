"""Unit economics, credit pack catalog, rate card, and token ledger serializer.

Provides pure, fault-tolerant data normalization for TinCan Mesh OS Token Vault
and ``/api/tokens/summary`` without mutating account or router state.
"""

from __future__ import annotations

import csv
import io
import math
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Aligns directly with server.TOKEN_PACKS:
#   pack_100  -> (100 cents, 120 tokens)
#   pack_500  -> (500 cents, 650 tokens)
#   pack_2000 -> (2000 cents, 2800 tokens)
TOKEN_PACK_CATALOG: Dict[str, Dict[str, Any]] = {
    "pack_100": {
        "id": "pack_100",
        "name": "Starter Pack",
        "tier": "Starter",
        "price_cents": 100,
        "price_usd": 1.00,
        "credits": 120,
        "tokens": 120,
        "bonus_pct": 0,
        "badge": "STARTER",
        "featured": False,
        "tagline": "Cloud gateway bursts & Arena duels. Zero-burn local Ollama stays free.",
        "cta_label": "Checkout $1.00 ->",
    },
    "pack_500": {
        "id": "pack_500",
        "name": "Builder Pack",
        "tier": "Builder",
        "price_cents": 500,
        "price_usd": 5.00,
        "credits": 650,
        "tokens": 650,
        "bonus_pct": 8,
        "badge": "BUILDER · +8% BONUS",
        "featured": True,
        "tagline": "Cloud Arena duels, Vault RAG ingestion + Hyper3D Rodin 3D GLB generations.",
        "cta_label": "Buy 650 CR ($5) ->",
    },
    "pack_2000": {
        "id": "pack_2000",
        "name": "Studio Pack",
        "tier": "Studio",
        "price_cents": 2000,
        "price_usd": 20.00,
        "credits": 2800,
        "tokens": 2800,
        "bonus_pct": 17,
        "badge": "STUDIO · +17% BONUS",
        "featured": False,
        "tagline": "Full cluster RAG pipelines, multi-model sweeps, Rodin Detail meshes & team spaces.",
        "cta_label": "Buy 2,800 CR ($20) ->",
    },
}

SERVICE_RATE_CARD: Tuple[Dict[str, Any], ...] = (
    {
        "id": "local_byok",
        "service": "Local Ollama / FAU BYOK",
        "gateway": "ollama / owlchat / trussed",
        "rate_label": "0 CR",
        "credits_per_unit": 0.0,
        "unit": "turn",
        "cost_usd_label": "$0.00",
        "margin_label": "LOCAL FREE",
    },
    {
        "id": "open_weight",
        "service": "Open-Weight Pool (NanoGPT)",
        "gateway": "nanogpt",
        "rate_label": "0.2 CR / 1K",
        "credits_per_unit": 0.2,
        "unit": "1K tokens",
        "cost_usd_label": "$0.0002 / 1K",
        "margin_label": "1.25x markup",
    },
    {
        "id": "frontier_cloud",
        "service": "Frontier Cloud",
        "gateway": "openrouter",
        "rate_label": "3-15 CR / 1K",
        "credits_per_unit": 3.0,
        "unit": "1K tokens",
        "cost_usd_label": "$0.003-$0.015 / 1K",
        "margin_label": "billed by cost_usd",
    },
    {
        "id": "hyper3d_rodin",
        "service": "Hyper3D Rodin GLB",
        "gateway": "hyper3d-rodin",
        "rate_label": "$0.25-$1.00 / mesh",
        "credits_per_unit": 50.0,
        "unit": "mesh",
        "cost_usd_label": "$0.25-$1.00",
        "margin_label": "Sketch $0.25 · Regular $0.50 · Smooth $0.75 · Detail $1.00",
    },
)

FRONTIER_BASELINE_USD_PER_1K = 0.009
ESTIMATED_TOKENS_PER_LOCAL_TURN = 1500
DEFAULT_AD_PAYOUT_USD = 0.05
DEFAULT_AD_COMPUTE_COST_USD = 0.002
DEFAULT_AD_REWARD_TOKENS = 25
DEFAULT_MARKUP_MULTIPLIER = 1.25
MIN_MARKUP_MULTIPLIER = 1.0
MAX_MARKUP_MULTIPLIER = 2.0


def clamp_markup_multiplier(value: Any, default: float = DEFAULT_MARKUP_MULTIPLIER) -> float:
    """Clamp a credit markup multiplier safely into [MIN_MARKUP_MULTIPLIER, MAX_MARKUP_MULTIPLIER]."""
    raw = _safe_float(value, default)
    if raw <= 0:
        raw = default
    return round(min(MAX_MARKUP_MULTIPLIER, max(MIN_MARKUP_MULTIPLIER, raw)), 4)


def compute_gross_margin_pct(multiplier: Any) -> float:
    """Convert a cost markup multiplier (e.g. 1.25x -> 20.0%, 1.43x -> 30.1%) to gross margin %."""
    m = clamp_markup_multiplier(multiplier)
    if m <= 1.0:
        return 0.0
    return round(((m - 1.0) / m) * 100.0, 1)


def multiplier_from_target_margin_pct(margin_pct: Any) -> float:
    """Convert a desired gross margin % (0..50%) to its equivalent cost markup multiplier."""
    pct = max(0.0, min(50.0, _safe_float(margin_pct, 20.0)))
    if pct <= 0.0:
        return MIN_MARKUP_MULTIPLIER
    return clamp_markup_multiplier(1.0 / (1.0 - (pct / 100.0)))

_LOCAL_GATEWAYS = frozenset({"ollama", "owlchat", "trussed", "local", "openai-compat", "fau", "byok"})
_LOCAL_PREFIXES = ("ollama/", "owlchat/", "trussed/", "local/", "openai-compat/")
_LOCAL_ALIASES = frozenset({"ollama-brain", "owlchat-brain", "trussed-brain", "local-brain"})
_RODIN_PREFIXES = ("ronin/", "rodin/", "hyper3d/")


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert arbitrary input to int safely without raising."""
    if value is None or isinstance(value, bool):
        return default
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(num):
        return default
    return int(round(num))


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert arbitrary input to finite float safely without raising."""
    if value is None or isinstance(value, bool):
        return default
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return num if math.isfinite(num) else default


def _format_time_label(ts: float) -> str:
    """Format an epoch timestamp as HH:MM:SS or return a placeholder if unset."""
    if ts <= 0:
        return "--:--:--"
    try:
        return time.strftime("%H:%M:%S", time.localtime(ts))
    except (OverflowError, OSError, ValueError):
        return "--:--:--"


def _is_local_target(gateway: str = "", model: str = "", alias: str = "") -> bool:
    gw = str(gateway or "").strip().lower()
    mdl = str(model or "").strip().lower()
    als = str(alias or "").strip().lower()
    return (
        gw in _LOCAL_GATEWAYS
        or mdl.startswith(_LOCAL_PREFIXES)
        or als in _LOCAL_ALIASES
        or als.startswith(_LOCAL_PREFIXES)
    )


def _is_rodin_target(gateway: str = "", model: str = "", alias: str = "") -> bool:
    gw = str(gateway or "").strip().lower()
    mdl = str(model or "").strip().lower()
    als = str(alias or "").strip().lower()
    return (
        gw in {"ronin", "rodin", "hyper3d", "hyper3d-rodin"}
        or mdl.startswith(_RODIN_PREFIXES)
        or als.startswith(_RODIN_PREFIXES)
        or als in {"ronin", "rodin", "hyper3d"}
    )


def _extract_local_usage(analytics: Dict[str, Any]) -> Tuple[int, int, float]:
    """Compute (local_turns, local_tokens, local_usd_saved) from gateway analytics."""
    providers = analytics.get("providers")
    routing_log = analytics.get("recent_routing_log")

    provider_turns = 0
    provider_tokens = 0
    counted_keys = set()

    if isinstance(providers, dict):
        for alias, info in providers.items():
            if not isinstance(info, dict):
                continue
            gw = str(info.get("gateway") or "")
            mdl = str(info.get("model") or "")
            if not _is_local_target(gw, mdl, str(alias)):
                continue
            calls = max(0, _safe_int(info.get("total_calls"), 0))
            toks = max(0, _safe_int(info.get("total_tokens"), 0))
            provider_turns += calls
            provider_tokens += toks
            if calls > 0:
                counted_keys.add(str(alias).strip().lower())
                if mdl:
                    counted_keys.add(mdl.strip().lower())

    extra_log_turns = 0
    extra_log_tokens = 0
    if isinstance(routing_log, list):
        for entry in routing_log:
            if not isinstance(entry, dict):
                continue
            lab = str(entry.get("lab") or entry.get("gateway") or "")
            mdl = str(entry.get("model") or "")
            als = str(entry.get("alias") or "")
            if not _is_local_target(lab, mdl, als):
                continue
            if als.strip().lower() in counted_keys or (mdl and mdl.strip().lower() in counted_keys):
                continue
            extra_log_turns += 1
            extra_log_tokens += max(0, _safe_int(entry.get("tokens") or entry.get("total_tokens"), 0))

    if analytics.get("local_turns") is not None:
        local_turns = max(0, _safe_int(analytics.get("local_turns"), 0))
    else:
        local_turns = provider_turns + extra_log_turns

    if analytics.get("local_tokens") is not None:
        local_tokens = max(0, _safe_int(analytics.get("local_tokens"), 0))
    else:
        local_tokens = provider_tokens + extra_log_tokens

    if analytics.get("local_usd_saved") is not None:
        local_usd_saved = round(max(0.0, _safe_float(analytics.get("local_usd_saved"), 0.0)), 4)
    elif local_tokens > 0:
        local_usd_saved = round((local_tokens / 1000.0) * FRONTIER_BASELINE_USD_PER_1K, 4)
    elif local_turns > 0:
        local_usd_saved = round(
            ((local_turns * ESTIMATED_TOKENS_PER_LOCAL_TURN) / 1000.0) * FRONTIER_BASELINE_USD_PER_1K,
            4,
        )
    else:
        local_usd_saved = 0.0

    return local_turns, local_tokens, local_usd_saved


def _normalize_invoice_row(inv: Dict[str, Any], markup_multiplier: float = DEFAULT_MARKUP_MULTIPLIER) -> Dict[str, Any]:
    """Normalize a PeerAccountRegistry token_ledger invoice into a unified ledger row."""
    ts = max(0.0, _safe_float(inv.get("timestamp"), 0.0))
    model = str(inv.get("model") or "unknown")
    kind = str(inv.get("kind") or "chat").lower()
    match_id = str(inv.get("match_id") or "")
    tokens = max(0, _safe_int(inv.get("total_tokens"), 0))
    cost_usd = round(max(0.0, _safe_float(inv.get("cost_usd"), 0.0)), 6)
    mult = clamp_markup_multiplier(markup_multiplier)
    markup_delta = max(0.0, mult - 1.0)
    markup_pct_int = int(round(markup_delta * 100.0))

    if _is_local_target(model=model, alias=model) and cost_usd == 0.0:
        workflow = "tincan ask --local"
        gateway = "ollama/local" if "ollama" in model.lower() else "fau/byok"
        credits_net = 0
        margin_label = "LOCAL FREE"
        status = "local_free"
    elif _is_rodin_target(model=model, alias=model):
        workflow = "rodin 3d mesh"
        gateway = "hyper3d-v2"
        credits_net = -tokens
        margin_usd = round(cost_usd * markup_delta, 4)
        margin_label = f"+${margin_usd:.4f} (rodin)" if cost_usd > 0 else "POOLED"
        status = "billed"
    elif kind == "arena":
        suffix = f" #{match_id[-4:]}" if match_id else ""
        workflow = f"arena duel{suffix}"
        gateway = model
        credits_net = -tokens
        margin_usd = round(cost_usd * markup_delta, 4)
        margin_label = f"+${margin_usd:.4f} (+{markup_pct_int}%)" if cost_usd > 0 else "SIMULATED"
        status = "billed"
    else:
        workflow = f"gateway {kind}"
        gateway = model
        credits_net = -tokens
        margin_usd = round(cost_usd * markup_delta, 4)
        margin_label = f"+${margin_usd:.4f} (+{markup_pct_int}%)" if cost_usd > 0 else "0 CR"
        status = "billed"

    return {
        "timestamp": ts,
        "time_label": _format_time_label(ts),
        "source": "invoice",
        "workflow": workflow,
        "gateway": gateway,
        "model": model,
        "tokens": tokens,
        "total_tokens": tokens,
        "upstream_usd": cost_usd,
        "cost_usd": cost_usd,
        "credits_net": credits_net,
        "margin_label": margin_label,
        "status": status,
    }


def _normalize_routing_row(entry: Dict[str, Any], markup_multiplier: float = DEFAULT_MARKUP_MULTIPLIER) -> Dict[str, Any]:
    """Normalize a DynamicAIGatewayRouter routing_log dict into a unified ledger row."""
    ts = max(0.0, _safe_float(entry.get("timestamp"), 0.0))
    alias = str(entry.get("alias") or entry.get("fallback_to") or "gateway")
    lab = str(entry.get("lab") or entry.get("gateway") or "gateway")
    model = str(entry.get("model") or alias)
    raw_cost = entry.get("cost") if entry.get("cost") is not None else entry.get("cost_usd")
    cost_usd = round(max(0.0, _safe_float(raw_cost, 0.0)), 6)
    tokens = max(0, _safe_int(entry.get("tokens") or entry.get("total_tokens"), 0))
    status = str(entry.get("status") or "routed")
    mult = clamp_markup_multiplier(markup_multiplier)
    markup_delta = max(0.0, mult - 1.0)
    markup_pct_int = int(round(markup_delta * 100.0))

    if _is_local_target(lab, model, alias):
        workflow = "tincan ask --local"
        gateway = model if "/" in model else f"{lab}/{model}"
        credits_net = 0
        margin_label = "LOCAL FREE"
    elif _is_rodin_target(lab, model, alias):
        workflow = f"rodin ({alias})"
        gateway = "hyper3d-v2"
        credits_net = -tokens if tokens > 0 else 0
        margin_usd = round(cost_usd * markup_delta, 4)
        margin_label = f"+${margin_usd:.4f}" if cost_usd > 0 else "ROUTED"
    else:
        workflow = f"route {alias}" if status != "fallback" else f"fallback -> {entry.get('fallback_to') or alias}"
        gateway = model if "/" in model else f"{lab}/{model}"
        credits_net = -tokens if tokens > 0 else 0
        margin_usd = round(cost_usd * markup_delta, 4)
        margin_label = f"+${margin_usd:.4f} (+{markup_pct_int}%)" if cost_usd > 0 else status.upper()

    return {
        "timestamp": ts,
        "time_label": _format_time_label(ts),
        "source": "routing",
        "workflow": workflow,
        "gateway": gateway,
        "model": model,
        "tokens": tokens,
        "total_tokens": tokens,
        "upstream_usd": cost_usd,
        "cost_usd": cost_usd,
        "credits_net": credits_net,
        "margin_label": margin_label,
        "status": status,
    }


def _merge_ledger_rows(
    invoices: Optional[Iterable[Any]],
    routing_log: Optional[Iterable[Any]],
    limit: int = 25,
    markup_multiplier: float = DEFAULT_MARKUP_MULTIPLIER,
) -> List[Dict[str, Any]]:
    """Combine account invoices and gateway routing log entries safely, newest first."""
    rows: List[Dict[str, Any]] = []
    if isinstance(invoices, list):
        for inv in invoices:
            if isinstance(inv, dict):
                rows.append(_normalize_invoice_row(inv, markup_multiplier=markup_multiplier))
    if isinstance(routing_log, list):
        for entry in routing_log:
            if isinstance(entry, dict):
                rows.append(_normalize_routing_row(entry, markup_multiplier=markup_multiplier))

    rows.sort(key=lambda r: r.get("timestamp", 0.0), reverse=True)
    return rows[: max(1, limit)]


def build_token_summary(
    account: Optional[Dict[str, Any]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    sponsor_state: Optional[Dict[str, Any]] = None,
    daily_ad_cap: int = 5,
    markup_multiplier: Optional[float] = None,
    ad_reward_credits: Optional[int] = None,
    role_tier: Optional[str] = None,
    is_admin: bool = False,
    cloud_routing_paused: bool = False,
) -> Dict[str, Any]:
    """Serialize unit economics, sponsor ad arbitrage, rate card, and ledger rows.

    Tolerates ``None`` or empty dicts for every argument so unauthenticated or
    offline peers never trigger KeyError/ZeroDivisionError/TypeError.
    """
    acct = account if isinstance(account, dict) else {}
    an = analytics if isinstance(analytics, dict) else {}
    sp = sponsor_state if isinstance(sponsor_state, dict) else {}

    raw_credits = acct.get("token_balance") if acct.get("token_balance") is not None else acct.get("credits_balance")
    credits_balance = max(0, _safe_int(raw_credits, 0))

    raw_usd = acct.get("credit_balance_usd") if acct.get("credit_balance_usd") is not None else acct.get("balance_usd")
    balance_usd = round(max(0.0, _safe_float(raw_usd, 0.0)), 4)

    total_tokens_used = max(0, _safe_int(acct.get("total_tokens_used"), 0))
    total_billed_usd = round(max(0.0, _safe_float(acct.get("total_billed_usd"), 0.0)), 6)

    local_turns, local_tokens, local_usd_saved = _extract_local_usage(an)

    cap = max(0, _safe_int(daily_ad_cap, 5))
    raw_views: Any = None
    if sp.get("ad_views_today") is not None:
        raw_views = sp.get("ad_views_today")
    elif acct.get("ad_views_today") is not None:
        raw_views = acct.get("ad_views_today")
    else:
        telemetry = sp.get("telemetry")
        if isinstance(telemetry, dict) and isinstance(telemetry.get("completions"), dict):
            raw_views = sum(max(0, _safe_int(v, 0)) for v in telemetry["completions"].values())

    ad_views_today = min(max(0, _safe_int(raw_views, 0)), cap)
    ad_views_remaining = max(0, cap - ad_views_today)
    ad_cap_pct = round((ad_views_today / cap) * 100.0, 1) if cap > 0 else 0.0

    active_sponsor = sp.get("active_sponsor") if isinstance(sp.get("active_sponsor"), dict) else None
    if active_sponsor is None and isinstance(sp.get("all_sponsors"), list):
        for candidate in sp["all_sponsors"]:
            if isinstance(candidate, dict):
                active_sponsor = candidate
                break

    payout_raw = active_sponsor.get("reward_usd") if isinstance(active_sponsor, dict) else None
    ad_payout_usd = round(max(0.0, _safe_float(payout_raw, DEFAULT_AD_PAYOUT_USD)), 4)
    ad_compute_cost_usd = round(
        max(0.0, _safe_float(sp.get("avg_compute_cost_usd"), DEFAULT_AD_COMPUTE_COST_USD)),
        4,
    )
    ad_net_margin_usd = round(max(0.0, ad_payout_usd - ad_compute_cost_usd), 4)
    ad_margin_pct = round((ad_net_margin_usd / ad_payout_usd) * 100.0, 2) if ad_payout_usd > 0 else 0.0

    reward_tok_raw = (
        ad_reward_credits
        if ad_reward_credits is not None
        else (active_sponsor.get("reward_tokens") if isinstance(active_sponsor, dict) else None)
    )
    ad_reward_tokens = max(0, _safe_int(reward_tok_raw, DEFAULT_AD_REWARD_TOKENS))
    ad_earned_today_tokens = ad_views_today * ad_reward_tokens
    ad_daily_max_tokens = cap * ad_reward_tokens
    effective_role = str(role_tier or acct.get("role_tier") or "free").strip().lower()
    est_nanogpt_chats = int(round(credits_balance / 0.2)) if credits_balance > 0 else 0
    est_openrouter_chats = int(round(credits_balance / 10.0)) if credits_balance > 0 else 0

    active_markup = clamp_markup_multiplier(
        markup_multiplier if markup_multiplier is not None else DEFAULT_MARKUP_MULTIPLIER
    )
    markup_pct = round((active_markup - 1.0) * 100.0, 1)
    gross_margin_pct = compute_gross_margin_pct(active_markup)

    ledger_rows = _merge_ledger_rows(
        acct.get("recent_invoices"),
        an.get("recent_routing_log"),
        markup_multiplier=active_markup,
    )

    hyper3d_raw = an.get("hyper3d") if isinstance(an.get("hyper3d"), dict) else {}
    rodin_summary = {
        "connected": bool(hyper3d_raw.get("connected", False)),
        "account_remaining_credits": round(_safe_float(hyper3d_raw.get("account_remaining_credits"), 0.0), 2),
        "account_remaining_balance_usd": round(_safe_float(hyper3d_raw.get("account_remaining_balance_usd"), 0.0), 2),
        "session_total_tasks": max(0, _safe_int(hyper3d_raw.get("session_total_tasks"), 0)),
        "key_label": str(hyper3d_raw.get("key_label") or "pooled-rodin"),
    }

    dynamic_rate_card = []
    for rate in SERVICE_RATE_CARD:
        item = dict(rate)
        if item.get("id") == "open_weight":
            item["margin_label"] = f"{active_markup:.2f}x markup"
        dynamic_rate_card.append(item)

    return {
        "peer_id": str(acct.get("peer_id") or ""),
        "role_tier": effective_role,
        "is_admin": bool(is_admin or effective_role == "admin"),
        "cloud_routing_paused": bool(cloud_routing_paused),
        "credits_balance": credits_balance,
        "balance_usd": balance_usd,
        "est_nanogpt_chats": est_nanogpt_chats,
        "est_openrouter_chats": est_openrouter_chats,
        "total_tokens_used": total_tokens_used,
        "total_billed_usd": total_billed_usd,
        "local_turns": local_turns,
        "local_tokens": local_tokens,
        "local_usd_saved": local_usd_saved,
        "ad_views_today": ad_views_today,
        "daily_ad_cap": cap,
        "ad_views_remaining": ad_views_remaining,
        "ad_cap_pct": ad_cap_pct,
        "ad_payout_usd": ad_payout_usd,
        "ad_compute_cost_usd": ad_compute_cost_usd,
        "ad_net_margin_usd": ad_net_margin_usd,
        "ad_margin_pct": ad_margin_pct,
        "ad_reward_tokens": ad_reward_tokens,
        "ad_earned_today_tokens": ad_earned_today_tokens,
        "ad_daily_max_tokens": ad_daily_max_tokens,
        "markup_multiplier": active_markup,
        "markup_pct": markup_pct,
        "gross_margin_pct": gross_margin_pct,
        "markup_min": MIN_MARKUP_MULTIPLIER,
        "markup_max": MAX_MARKUP_MULTIPLIER,
        "billing_mode": "cost_usd",
        "active_sponsor": dict(active_sponsor) if active_sponsor else None,
        "pack_catalog": [dict(pack) for pack in TOKEN_PACK_CATALOG.values()],
        "rate_card": dynamic_rate_card,
        "ledger_rows": ledger_rows,
        "rodin": rodin_summary,
    }


def format_ledger_csv(ledger_rows: Optional[List[Dict[str, Any]]]) -> str:
    """Serialize normalized token ledger rows as RFC-4180 CSV text."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["time", "workflow", "gateway", "tokens", "upstream_usd", "credits_net", "margin", "status"])
    if isinstance(ledger_rows, list):
        for row in ledger_rows:
            if not isinstance(row, dict):
                continue
            writer.writerow([
                row.get("time_label", "--:--:--"),
                row.get("workflow", ""),
                row.get("gateway", row.get("model", "")),
                _safe_int(row.get("tokens", row.get("total_tokens")), 0),
                f"{_safe_float(row.get('upstream_usd', row.get('cost_usd')), 0.0):.6f}",
                _safe_int(row.get("credits_net"), 0),
                row.get("margin_label", ""),
                row.get("status", ""),
            ])
    return buf.getvalue()
