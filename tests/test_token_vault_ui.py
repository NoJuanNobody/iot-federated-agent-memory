"""Tests for Token Vault unit-economics ledger and Aeonik Celadon UI."""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import subprocess
from collections import Counter

import pytest

import server
from iot_federated_agent_memory.sponsor_ads import SponsorAdManager
from iot_federated_agent_memory.token_ledger import (
    FRONTIER_BASELINE_USD_PER_1K,
    SERVICE_RATE_CARD,
    TOKEN_PACK_CATALOG,
    build_token_summary,
    format_ledger_csv,
)
from iot_federated_agent_memory.token_vault_ui import (
    TOKEN_VAULT_CSS,
    TOKEN_VAULT_CSS_SLOT,
    TOKEN_VAULT_JS,
    TOKEN_VAULT_JS_SLOT,
    TOKEN_VAULT_TITLEBAR,
    TOKEN_VAULT_WINDOW_SLOT,
    apply_token_vault_ui,
    render_token_vault_window_html,
)
from iot_federated_agent_memory.window_chrome import (
    apply_window_chrome,
    expand_titlebars,
    legacy_palette_classes,
)


REQUIRED_LEGACY_IDS = (
    "win-billing",
    "billingWindowTokens",
    "billingWindowCredits",
    "billingTotalUsedText",
    "billingLedgerRows",
    "billingAdminSponsorBtn",
    "sponsorAdContainer",
    "adSponsorIcon",
    "adSponsorName",
    "adSponsorBadge",
    "adSponsorTagline",
    "adSponsorCtaBtn",
    "watchAdBtn",
    "adVideoContainer",
    "adVideoPlayer",
    "adVideoTitle",
    "adProgressWrap",
    "adProgressText",
    "adTimerText",
    "adProgressBar",
    "rodinBillingStatusBadge",
    "rodinBalanceCredits",
    "rodinBalanceUsd",
    "rodinSessionTasks",
    "rodinKeyLabel",
)

REQUIRED_NEW_IDS = (
    "tokenAdCapBar",
    "tokenAdCapLabel",
    "tvLocalSavedUsd",
    "tvLocalTurnsSub",
    "tvAdArbitrageVal",
    "tvAdArbitrageSub",
    "tvUnitEconVal",
    "tvUnitEconSub",
    "tvArbPayout",
    "tvArbCost",
    "tvRateCardGrid",
)

REQUIRED_CALLBACKS = (
    "buyTokens(1.00, 120)",
    "buyTokens(5.00, 650)",
    "buyTokens(20.00, 2800)",
    "watchSponsoredAd()",
    "fetchNextSponsor()",
    "trackSponsorClick()",
    "openSponsorInfoModal()",
    "openAdminSponsorStudio()",
    "refreshBillingWindow()",
    "toggleWindow('win-agentspace')",
    "toggleWindow('win-workstation')",
)


def test_token_pack_catalog_matches_server_token_packs():
    assert set(TOKEN_PACK_CATALOG.keys()) == {"pack_100", "pack_500", "pack_2000"}
    assert set(server.TOKEN_PACKS.keys()) == set(TOKEN_PACK_CATALOG.keys())

    for pack_id, (server_cents, server_credits) in server.TOKEN_PACKS.items():
        pack = TOKEN_PACK_CATALOG[pack_id]
        assert pack["price_cents"] == server_cents
        assert pack["credits"] == server_credits
        assert pack["tokens"] == server_credits
        assert pack["price_usd"] == pytest.approx(server_cents / 100.0)

    assert TOKEN_PACK_CATALOG["pack_100"]["bonus_pct"] == 0
    assert TOKEN_PACK_CATALOG["pack_500"]["bonus_pct"] == 8
    assert TOKEN_PACK_CATALOG["pack_2000"]["bonus_pct"] == 17

    featured_ids = [pid for pid, p in TOKEN_PACK_CATALOG.items() if p["featured"]]
    assert featured_ids == ["pack_500"]


def test_service_rate_card_structure():
    assert isinstance(SERVICE_RATE_CARD, tuple)
    assert len(SERVICE_RATE_CARD) == 4
    services = [row["service"] for row in SERVICE_RATE_CARD]
    assert services == [
        "Local Ollama / FAU BYOK",
        "Open-Weight Pool (NanoGPT)",
        "Frontier Cloud",
        "Hyper3D Rodin GLB",
    ]
    required_keys = {
        "id",
        "service",
        "gateway",
        "rate_label",
        "credits_per_unit",
        "unit",
        "cost_usd_label",
        "margin_label",
    }
    for row in SERVICE_RATE_CARD:
        assert required_keys.issubset(row.keys())
        assert isinstance(row["credits_per_unit"], (int, float))


def test_build_token_summary_empty_and_none_inputs():
    for args in [
        (),
        (None, None, None),
        ({}, {}, {}),
        ("bad", ["bad"], 123),
    ]:
        summary = build_token_summary(*args)
        assert summary["credits_balance"] == 0
        assert summary["balance_usd"] == 0.0
        assert summary["local_turns"] == 0
        assert summary["local_tokens"] == 0
        assert summary["local_usd_saved"] == 0.0
        assert summary["ad_views_today"] == 0
        assert summary["daily_ad_cap"] == 5
        assert summary["ad_views_remaining"] == 5
        assert summary["ad_cap_pct"] == 0.0
        assert summary["ad_margin_pct"] == 96.0
        assert summary["ledger_rows"] == []
        assert len(summary["rate_card"]) == 4
        assert len(summary["pack_catalog"]) == 3
        assert summary["rodin"]["connected"] is False
        # Must remain strictly JSON-serializable for FastAPI responses.
        json.dumps(summary)


def test_build_token_summary_local_turns_and_savings_avoid_double_counting():
    analytics = {
        "providers": {
            "ollama-local": {
                "gateway": "ollama",
                "model": "ollama/qwen3-coder:30b",
                "total_calls": 4,
                "total_tokens": 6000,
            },
            "fau-owlchat": {
                "gateway": "owlchat",
                "model": "owlchat/llama3.3",
                "total_calls": 2,
                "total_tokens": 4000,
            },
            "frontier": {
                "gateway": "openrouter",
                "model": "anthropic/claude-sonnet-4",
                "total_calls": 9,
                "total_tokens": 20000,
            },
        },
        "recent_routing_log": [
            # Same alias/model as ollama-local provider -> must NOT double-count.
            {
                "timestamp": 1731600000,
                "alias": "ollama-local",
                "lab": "ollama",
                "model": "ollama/qwen3-coder:30b",
                "tokens": 1500,
                "cost": 0.0,
                "status": "routed",
            },
            # Distinct uncounted local entry -> MUST add 1 turn + 2000 tokens.
            {
                "timestamp": 1731600050,
                "alias": "trussed-edge",
                "lab": "trussed",
                "model": "trussed/mistral-7b",
                "tokens": 2000,
                "cost": 0.0,
                "status": "routed",
            },
        ],
    }
    summary = build_token_summary({}, analytics, {}, daily_ad_cap=server.AD_DAILY_REWARD_CAP)
    assert summary["local_turns"] == 7
    assert summary["local_tokens"] == 12000
    expected_saved = round((12000 / 1000.0) * FRONTIER_BASELINE_USD_PER_1K, 4)
    assert summary["local_usd_saved"] == pytest.approx(expected_saved)

    # Turn-only fallback when local_tokens == 0
    turns_only = build_token_summary(
        {},
        {"providers": {"ollama-local": {"gateway": "ollama", "total_calls": 10, "total_tokens": 0}}},
        {},
    )
    assert turns_only["local_turns"] == 10
    assert turns_only["local_usd_saved"] == pytest.approx(0.135)


def test_build_token_summary_daily_ad_cap_clamping_and_margin():
    over_cap = build_token_summary(
        account={"token_balance": 650, "credit_balance_usd": 6.50},
        sponsor_state={
            "ad_views_today": 17,
            "active_sponsor": {"name": "PartnerX", "reward_usd": 0.05, "reward_tokens": 5000},
            "avg_compute_cost_usd": 0.002,
        },
        daily_ad_cap=5,
    )
    assert over_cap["ad_views_today"] == 5
    assert over_cap["daily_ad_cap"] == 5
    assert over_cap["ad_views_remaining"] == 0
    assert over_cap["ad_cap_pct"] == 100.0
    assert over_cap["ad_margin_pct"] == 96.0
    assert over_cap["ad_earned_today_tokens"] == 25000
    assert over_cap["ad_daily_max_tokens"] == 25000

    neg_views = build_token_summary(sponsor_state={"ad_views_today": -4}, daily_ad_cap=5)
    assert neg_views["ad_views_today"] == 0
    assert neg_views["ad_views_remaining"] == 5
    assert neg_views["ad_cap_pct"] == 0.0

    zero_cap = build_token_summary(sponsor_state={"ad_views_today": 3}, daily_ad_cap=0)
    assert zero_cap["daily_ad_cap"] == 0
    assert zero_cap["ad_views_today"] == 0
    assert zero_cap["ad_cap_pct"] == 0.0

    zero_payout = build_token_summary(
        sponsor_state={"active_sponsor": {"reward_usd": 0.0, "reward_tokens": 1000}}
    )
    assert zero_payout["ad_payout_usd"] == 0.0
    assert zero_payout["ad_net_margin_usd"] == 0.0
    assert zero_payout["ad_margin_pct"] == 0.0

    # Compatible with SponsorAdManager.get_state() payload.
    manager_state = SponsorAdManager().get_state()
    from_manager = build_token_summary(sponsor_state=manager_state, daily_ad_cap=server.AD_DAILY_REWARD_CAP)
    assert from_manager["active_sponsor"] is not None
    assert from_manager["ad_views_today"] == 0
    assert from_manager["daily_ad_cap"] == server.AD_DAILY_REWARD_CAP


def test_build_token_summary_merges_ledger_rodin_and_csv():
    account = {
        "peer_id": "tc:testpeer1234",
        "token_balance": 1420,
        "credit_balance_usd": 14.20,
        "total_tokens_used": 8500,
        "total_billed_usd": 0.0425,
        "recent_invoices": [
            "malformed",
            {
                "timestamp": 1731600200,
                "kind": "arena",
                "match_id": "match_991a",
                "model": "anthropic/claude-sonnet-4",
                "total_tokens": 1200,
                "cost_usd": 0.012,
            },
            {
                "timestamp": 1731600100,
                "kind": "chat",
                "model": "ollama/llama3.2",
                "total_tokens": 900,
                "cost_usd": 0.0,
            },
        ],
    }
    analytics = {
        "recent_routing_log": [
            None,
            {
                "timestamp": 1731600300,
                "alias": "rodin-gen",
                "lab": "hyper3d-rodin",
                "model": "rodin/v2-detail",
                "tokens": 500,
                "cost": 1.0,
                "status": "routed",
            },
            {
                "timestamp": 1731600150,
                "alias": "openrouter-fast",
                "lab": "openrouter",
                "model": "google/gemini-2.5-flash",
                "tokens": float("nan"),
                "cost": 0.004,
                "status": "fallback",
                "fallback_to": "nanogpt-qwen",
            },
        ],
        "hyper3d": {
            "connected": True,
            "account_remaining_credits": 88.5,
            "account_remaining_balance_usd": 44.25,
            "session_total_tasks": 3,
            "key_label": "pool-prod-1",
        },
    }

    summary = build_token_summary(account, analytics, None)
    assert summary["peer_id"] == "tc:testpeer1234"
    assert summary["credits_balance"] == 1420
    assert summary["balance_usd"] == pytest.approx(14.20)
    assert summary["rodin"]["connected"] is True
    assert summary["rodin"]["account_remaining_credits"] == pytest.approx(88.5)
    assert summary["rodin"]["session_total_tasks"] == 3
    assert summary["rodin"]["key_label"] == "pool-prod-1"

    rows = summary["ledger_rows"]
    assert len(rows) == 4
    # Sorted strictly newest first.
    timestamps = [r["timestamp"] for r in rows]
    assert timestamps == sorted(timestamps, reverse=True)
    assert rows[0]["workflow"] == "rodin (rodin-gen)"
    assert rows[1]["workflow"] == "arena duel #991a"
    assert rows[2]["workflow"] == "fallback -> nanogpt-qwen"
    assert rows[2]["tokens"] == 0
    assert rows[3]["margin_label"] == "LOCAL FREE"

    csv_text = format_ledger_csv(rows)
    parsed = list(csv.reader(io.StringIO(csv_text)))
    assert parsed[0] == ["time", "workflow", "gateway", "tokens", "upstream_usd", "credits_net", "margin", "status"]
    assert len(parsed) == 5


def test_render_token_vault_window_html_preserves_legacy_ids_and_callbacks():
    html = render_token_vault_window_html()

    assert TOKEN_VAULT_TITLEBAR in html
    assert '"id": "win-billing"' in TOKEN_VAULT_TITLEBAR
    assert '"badge": "STRIPE + ARBITRAGE"' in TOKEN_VAULT_TITLEBAR

    win_idx = html.index('id="win-billing"')
    assert 'data-zen-window="true"' in html[win_idx : win_idx + 150]

    for dom_id in REQUIRED_LEGACY_IDS + REQUIRED_NEW_IDS:
        assert f'id="{dom_id}"' in html, f"Missing required DOM id={dom_id}"

    for callback in REQUIRED_CALLBACKS:
        assert callback in html, f"Missing required JS callback {callback}"

    # Every id inside #win-billing must be unique (avoid matching data-*-id attributes).
    all_ids = re.findall(r'(?<![\w-])id="([^"]+)"', html)
    dupes = [k for k, v in Counter(all_ids).items() if v > 1]
    assert dupes == [], f"Duplicate DOM ids found: {dupes}"
    assert all_ids.count("win-billing") == 1

    # Verify Aeonik KPI & panel headings + pack labels.
    for label in (
        "Credit Pool Balance",
        "Local Zero-Burn Saved",
        "Sponsor Ad Arbitrage",
        "Unit Economics",
        "Service Rate Card",
        "Sponsor Video Compute Subsidy",
        "Token &amp; Margin Ledger",
        "120 Credits",
        "650 Credits · +8%",
        "2,800 Credits · +17%",
    ):
        assert label in html


def test_token_vault_aeonik_palette_and_no_legacy_dark_classes():
    html = render_token_vault_window_html()
    assert legacy_palette_classes(html) == []
    assert legacy_palette_classes(TOKEN_VAULT_CSS) == []
    assert legacy_palette_classes(TOKEN_VAULT_JS) == []

    combined = "\n".join((html, TOKEN_VAULT_CSS, TOKEN_VAULT_JS))
    for forbidden in (
        "bg-slate-",
        "text-slate-",
        "border-slate-",
        "bg-cyan-",
        "text-cyan-",
        "bg-emerald-",
        "bg-gradient-to-",
    ):
        assert forbidden not in combined, f"Forbidden legacy utility token found: {forbidden}"

    for token in (
        "#ecf1e6",
        "#f4f8f0",
        "#ffffff",
        "#111111",
        "#107a47",
        "#8a1c1c",
        "Inter",
        "JetBrains Mono",
        "#win-billing",
    ):
        assert token in TOKEN_VAULT_CSS, f"Missing Aeonik CSS token: {token}"


def test_apply_token_vault_ui_idempotent_slots_and_window_chrome():
    shell_with_slots = f"""<!doctype html>
<html>
<head><style>{TOKEN_VAULT_CSS_SLOT}</style></head>
<body>
  <div id="desktop">{TOKEN_VAULT_WINDOW_SLOT}</div>
  <script>{TOKEN_VAULT_JS_SLOT}</script>
</body>
</html>"""

    rendered = apply_token_vault_ui(shell_with_slots)
    assert TOKEN_VAULT_CSS_SLOT not in rendered
    assert TOKEN_VAULT_WINDOW_SLOT not in rendered
    assert TOKEN_VAULT_JS_SLOT not in rendered
    assert 'id="win-billing"' in rendered
    assert "/* tc-token-vault-css */" in rendered
    assert "window.TinCanTokenVault" in rendered
    assert apply_token_vault_ui(rendered) == rendered
    assert legacy_palette_classes(rendered) == []

    expanded = expand_titlebars(rendered)
    assert "<!--TC_TITLEBAR" not in expanded
    assert 'class="window-header tc-titlebar"' in expanded
    assert 'data-tc-titlebar="win-billing"' in expanded
    assert "Token Vault · Stripe Packs &amp; Sponsor Arbitrage" in expanded
    assert "STRIPE + ARBITRAGE" in expanded
    assert legacy_palette_classes(expanded) == []

    chromed = apply_window_chrome(rendered)
    assert "<!--TC_TITLEBAR" not in chromed
    assert 'data-tc-titlebar="win-billing"' in chromed

    # Fallback mode when only <!--TC_TOKEN_VAULT_WINDOW--> is present.
    fallback_shell = f"""<!doctype html>
<html>
<head></head>
<body>
  <div id="desktop">{TOKEN_VAULT_WINDOW_SLOT}</div>
</body>
</html>"""
    fallback_rendered = apply_token_vault_ui(fallback_shell)
    assert '<style id="tcTokenVaultCss">' in fallback_rendered
    assert '<script id="tcTokenVaultJs">' in fallback_rendered
    assert apply_token_vault_ui(fallback_rendered) == fallback_rendered


def test_token_vault_js_node_syntax_and_vm_hydration():
    node_bin = shutil.which("node")
    assert node_bin, "Node.js is required to validate TOKEN_VAULT_JS"

    syntax_proc = subprocess.run(
        [node_bin, "--check", "-"],
        input=TOKEN_VAULT_JS,
        text=True,
        capture_output=True,
        check=False,
    )
    assert syntax_proc.returncode == 0, f"node --check failed:\n{syntax_proc.stderr}"

    sample_summary = build_token_summary(
        account={
            "peer_id": "tc:vmtest",
            "token_balance": 2800,
            "credit_balance_usd": 28.0,
            "total_tokens_used": 4500,
            "total_billed_usd": 0.0315,
            "recent_invoices": [
                {
                    "timestamp": 1731600200,
                    "kind": "chat",
                    "model": "anthropic/claude-sonnet-4",
                    "total_tokens": 1000,
                    "cost_usd": 0.009,
                }
            ],
        },
        analytics={
            "providers": {
                "ollama-local": {"gateway": "ollama", "total_calls": 3, "total_tokens": 4500}
            },
            "hyper3d": {
                "connected": True,
                "account_remaining_credits": 75.0,
                "account_remaining_balance_usd": 37.5,
                "session_total_tasks": 2,
                "key_label": "pool-vm",
            },
        },
        sponsor_state={
            "ad_views_today": 2,
            "active_sponsor": {
                "name": "Acme Compute",
                "tagline": "Edge sandbox pods",
                "badge": "Partner",
                "icon": "◈",
                "url": "https://example.com",
                "cta": "Launch ↗",
                "reward_usd": 0.05,
                "reward_tokens": 5000,
            },
        },
        daily_ad_cap=5,
    )

    ids_in_dom = list(
        set(REQUIRED_LEGACY_IDS)
        | set(REQUIRED_NEW_IDS)
        | {"hudTokenPill", "tvFooterAdCap"}
    )
    harness = f"""
const vm = require('vm');
const assert = require('assert');
const elements = new Map();
const trackedIds = {json.dumps(sorted(ids_in_dom))};
for (const id of trackedIds) {{
  elements.set(id, {{
    id,
    innerText: '',
    textContent: '',
    innerHTML: '',
    className: '',
    style: {{ width: '' }},
    href: '',
    title: '',
    disabled: false,
  }});
}}
const summaryPayload = {json.dumps(sample_summary)};
const sandbox = {{
  console,
  URL,
  encodeURIComponent,
  setTimeout: () => 0,
  myPeerId: 'tc:vmtest',
  localStorage: {{ getItem: () => 'tc:vmtest' }},
  document: {{
    getElementById: (id) => elements.get(id) || null,
  }},
  window: {{}},
  fetch: async (url) => {{
    if (String(url).startsWith('/api/tokens/summary')) {{
      return {{ ok: true, json: async () => summaryPayload }};
    }}
    return {{ ok: false, json: async () => ({{}}) }};
  }},
}};
sandbox.window = sandbox;
vm.runInNewContext({json.dumps(TOKEN_VAULT_JS)}, sandbox);

(async () => {{
  assert.ok(sandbox.TinCanTokenVault, 'TinCanTokenVault global missing');
  assert.strictEqual(typeof sandbox.refreshBillingWindow, 'function');
  assert.strictEqual(typeof sandbox.buyTokens, 'function');
  await sandbox.TinCanTokenVault.refresh();

  assert.strictEqual(elements.get('billingWindowTokens').innerText, (2800).toLocaleString());
  assert.strictEqual(elements.get('billingWindowCredits').innerText, '$28.00 USD');
  assert.strictEqual(elements.get('tvLocalSavedUsd').innerText, '$0.04');
  assert.ok(elements.get('tvLocalTurnsSub').innerText.includes('3 local turns'));
  assert.strictEqual(elements.get('tokenAdCapBar').style.width, '40.0%');
  assert.ok(elements.get('tokenAdCapLabel').innerText.includes('2 / 5 VIEWS COMPLETED'));
  assert.ok(elements.get('billingLedgerRows').innerHTML.includes('gateway chat'));
  assert.strictEqual(elements.get('rodinBalanceCredits').textContent, '75.0');
  assert.strictEqual(elements.get('rodinBalanceUsd').textContent, '$37.50');
  assert.strictEqual(elements.get('adSponsorName').innerText, 'Acme Compute');

  const csvOut = sandbox.TinCanTokenVault.exportCsv();
  assert.ok(csvOut.startsWith('time,workflow,gateway,tokens,upstream_usd,credits_net,margin\\n'));
  assert.ok(csvOut.includes('gateway chat'));
}})().catch((err) => {{
  console.error(err);
  process.exit(1);
}});
"""
    vm_proc = subprocess.run(
        [node_bin, "-e", harness],
        text=True,
        capture_output=True,
        check=False,
    )
    assert vm_proc.returncode == 0, f"Node VM harness failed:\n{vm_proc.stderr}\n{vm_proc.stdout}"


def test_credit_margin_dial_math_server_and_ui(tmp_path):
    from iot_federated_agent_memory.account_registry import PeerAccountRegistry
    from iot_federated_agent_memory.token_ledger import (
        clamp_markup_multiplier,
        compute_gross_margin_pct,
        multiplier_from_target_margin_pct,
    )

    assert clamp_markup_multiplier(0.5) == 1.0
    assert clamp_markup_multiplier(5.0) == 2.0
    assert compute_gross_margin_pct(1.25) == pytest.approx(20.0)
    assert compute_gross_margin_pct(1.43) == pytest.approx(30.1)
    assert multiplier_from_target_margin_pct(30.0) == pytest.approx(1.4286, abs=1e-3)

    prev = server.get_credit_markup_multiplier()
    try:
        updated = server.set_credit_markup_multiplier(1.43)
        assert updated == pytest.approx(1.43)
        assert server.get_credit_markup_multiplier() == pytest.approx(1.43)
        summary = build_token_summary(markup_multiplier=updated)
        assert summary["markup_multiplier"] == pytest.approx(1.43)
        assert summary["gross_margin_pct"] == pytest.approx(30.1)
    finally:
        server.set_credit_markup_multiplier(prev)

    reg = PeerAccountRegistry(db_path=str(tmp_path / "dial.db"))
    reg.register_account(
        peer_id="tc:dialtest",
        full_name="Dial Test",
        phone_number="+15550001111",
        email="dial@mesh.local",
        initial_tokens=1000,
        initial_credit_usd=10.0,
    )
    receipt = reg.bill_tokens(
        peer_id="tc:dialtest",
        prompt_tokens=100,
        completion_tokens=100,
        total_tokens=200,
        cost_usd=1.0,
        model="openrouter/claude",
        markup_multiplier=1.43,
    )
    assert receipt["upstream_cost_usd"] == pytest.approx(1.0)
    assert receipt["cost_usd"] == pytest.approx(1.43)
    assert receipt["remaining_credit_usd"] == pytest.approx(8.57)

    html = render_token_vault_window_html()
    assert 'id="tvMarginDialBar"' in html
    assert 'id="tvMarginDialSlider"' in html
    assert 'id="tvMarginDialReadout"' in html
    assert 'id="tvMarginDialApplyBtn"' in html
    assert "setMarginPreset(1.43)" in html
