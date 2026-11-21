"""Tests for Role-Based Token Vault, Persistent Economy Dials, and Admin Treasury UI."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

import server
from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.admin_treasury_ui import (
    ADMIN_TREASURY_JS,
    apply_admin_treasury_ui,
    render_admin_treasury_window_html,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.sponsor_ads import DEFAULT_SPONSORS
from iot_federated_agent_memory.token_ledger import DEFAULT_AD_REWARD_TOKENS, build_token_summary


def test_role_tiers_and_economy_settings_persist(tmp_path):
    db_file = str(tmp_path / "rbac.db")
    reg = PeerAccountRegistry(db_path=db_file)
    acc = reg.register_account(
        peer_id="tc:student1",
        full_name="Student One",
        phone_number="+15551112222",
        email="student1@fau.edu",
        initial_tokens=50,
        initial_credit_usd=0.50,
    )
    assert acc["role_tier"] == "free"

    updated = reg.set_role_tier("tc:student1", "student")
    assert updated["role_tier"] == "student"

    with pytest.raises(ValueError):
        reg.set_role_tier("tc:student1", "supervillain")

    reg.set_economy_setting("credit_markup", 1.43)
    reg.set_economy_setting("ad_reward_credits", 25)
    reg.set_economy_setting("cloud_routing_paused", "1")

    # Re-open from disk to prove persistence
    reg2 = PeerAccountRegistry(db_path=db_file)
    assert reg2.get_account_by_peer("tc:student1")["role_tier"] == "student"
    assert float(reg2.get_economy_setting("credit_markup")) == pytest.approx(1.43)
    assert int(reg2.get_economy_setting("ad_reward_credits")) == 25
    assert reg2.get_economy_setting("cloud_routing_paused") == "1"


def test_aligned_ad_rewards_and_user_balance_equivalents():
    assert DEFAULT_AD_REWARD_TOKENS == 25
    for sp in DEFAULT_SPONSORS:
        assert sp.reward_tokens == 25

    summary = build_token_summary(
        account={"peer_id": "tc:u1", "token_balance": 1420, "credit_balance_usd": 11.80, "role_tier": "builder"},
        daily_ad_cap=5,
        markup_multiplier=1.43,
        ad_reward_credits=25,
        is_admin=False,
    )
    assert summary["role_tier"] == "builder"
    assert summary["is_admin"] is False
    assert summary["ad_reward_tokens"] == 25
    assert summary["ad_daily_max_tokens"] == 125
    assert summary["est_nanogpt_chats"] == 7100
    assert summary["est_openrouter_chats"] == 142


def test_global_audit_ledger_and_stripe_revenue_summary(tmp_path):
    reg = PeerAccountRegistry(db_path=str(tmp_path / "audit.db"))
    reg.register_account(
        peer_id="tc:builder1",
        full_name="Builder One",
        phone_number="+15553334444",
        email="builder1@mesh.local",
        initial_tokens=650,
        initial_credit_usd=5.00,
    )
    reg.set_role_tier("tc:builder1", "builder")
    reg.credit_once(ref="stripe:cs_test_1", peer_id="tc:builder1", kind="purchase", tokens=650, amount_usd=5.00)
    reg.bill_tokens(
        peer_id="tc:builder1",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        cost_usd=0.01,
        model="openrouter/claude-sonnet-4",
        markup_multiplier=1.43,
    )

    rows = reg.get_global_audit_ledger(limit=10)
    assert len(rows) == 1
    assert rows[0]["peer_id"] == "tc:builder1"
    assert rows[0]["role_tier"] == "builder"
    assert rows[0]["cost_usd"] == pytest.approx(0.0143)

    rev = reg.get_stripe_revenue_summary(days=30)
    assert rev["purchase_count"] == 1
    assert rev["gross_usd"] == pytest.approx(5.0)
    assert rev["stripe_fees_usd"] == pytest.approx(0.445)
    assert rev["net_after_stripe_usd"] == pytest.approx(4.555)


def test_admin_treasury_window_wired_into_mesh_os_html():
    assert 'id="win-admin-treasury"' in MESH_OS_HTML_UI
    assert 'id="tvOpenAdminTreasuryBtn"' in MESH_OS_HTML_UI
    assert 'id="adminKillSwitchBtn"' in MESH_OS_HTML_UI
    assert 'id="adminMarkupSlider"' in MESH_OS_HTML_UI
    assert 'id="adminAdRewardSlider"' in MESH_OS_HTML_UI
    assert 'id="adminAuditLedgerRows"' in MESH_OS_HTML_UI
    assert "'win-admin-treasury'" in MESH_OS_HTML_UI

    # Idempotency check
    once = apply_admin_treasury_ui(MESH_OS_HTML_UI)
    assert once == MESH_OS_HTML_UI
    assert "Token Treasury" in render_admin_treasury_window_html()


def test_server_economy_dials_and_kill_switch_helpers():
    prev_m = server.get_credit_markup_multiplier()
    prev_ad = server.get_ad_reward_credits()
    prev_cap = server.get_daily_ad_cap()
    prev_pause = server.is_cloud_routing_paused()
    try:
        assert server.set_credit_markup_multiplier(1.43) == pytest.approx(1.43)
        assert server.set_ad_reward_credits(30) == 30
        assert server.set_daily_ad_cap(4) == 4
        assert server.set_cloud_routing_paused(True) is True
        assert server.is_cloud_routing_paused() is True
    finally:
        server.set_credit_markup_multiplier(prev_m)
        server.set_ad_reward_credits(prev_ad)
        server.set_daily_ad_cap(prev_cap)
        server.set_cloud_routing_paused(prev_pause)


def test_admin_treasury_js_hydrates_in_node_vm():
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node not available")

    payload = {
        "admin_authenticated": True,
        "cloud_routing_paused": True,
        "pools": {
            "nanogpt": {"account_remaining_balance_usd": 42.80, "account_remaining_nano": 18.4, "session_total_calls": 12},
            "openrouter": {"account_remaining_balance_usd": 128.40, "key_usage_daily_usd": 6.12, "connected": True},
            "rodin": {"account_remaining_balance_usd": 50.0, "account_remaining_credits": 100.0, "session_total_tasks": 4},
        },
        "stripe_30d": {"purchase_count": 3, "gross_usd": 30.0, "stripe_fees_usd": 1.77, "net_after_stripe_usd": 28.23, "credits_sold": 4100},
        "dials": {"markup_multiplier": 1.43, "ad_reward_credits": 25, "daily_ad_cap": 5},
        "pending_mint_requests": [{"target_peer_id": "tc:alex-fau", "tokens": 300, "reason": "capstone"}],
        "audit_ledger": [
            {"timestamp": 1731600100, "peer_id": "tc:maria91", "role_tier": "builder", "model": "nanogpt/deepseek", "total_tokens": 2000, "cost_usd": 0.0053}
        ],
    }

    harness = f"""
const assert = require('assert');
const vm = require('vm');
const ids = [
  'adminKillSwitchBtn','adminPoolNanoVal','adminPoolNanoSub','adminPoolOrVal','adminPoolOrSub',
  'adminPoolRodinVal','adminPoolRodinSub','adminPoolMarginVal','adminPoolMarginSub',
  'adminMarkupSlider','adminMarkupBadge','adminAdRewardSlider','adminAdRewardBadge',
  'adminDailyCapVal','adminStripeHealthSub','adminMintQueueList','adminAuditLedgerRows'
];
const els = new Map();
ids.forEach((id) => els.set(id, {{ id, textContent: '', innerHTML: '', value: '1.25', className: '' }}));
const sandbox = {{
  console,
  localStorage: {{ getItem: () => 'secret-admin' }},
  document: {{ getElementById: (id) => els.get(id) || null }},
  window: {{}},
  fetch: async () => ({{ ok: true, json: async () => ({json.dumps(payload)}) }}),
}};
sandbox.window = sandbox;
vm.runInNewContext({json.dumps(ADMIN_TREASURY_JS)}, sandbox);
(async () => {{
  await sandbox.TinCanAdminTreasury.refresh();
  assert.strictEqual(els.get('adminPoolNanoVal').textContent, '$42.80');
  assert.strictEqual(els.get('adminPoolOrVal').textContent, '$128.40');
  assert.strictEqual(els.get('adminPoolMarginVal').textContent, '$28.23');
  assert.ok(els.get('adminKillSwitchBtn').textContent.includes('Resume Cloud Routing'));
  assert.ok(els.get('adminMarkupBadge').textContent.includes('1.43x'));
  assert.ok(els.get('adminAuditLedgerRows').innerHTML.includes('tc:maria91'));
  const csv = sandbox.TinCanAdminTreasury.exportCsv();
  assert.ok(csv.includes('tc:maria91'));
}})().catch((e) => {{ console.error(e); process.exit(1); }});
"""
    proc = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert proc.returncode == 0, f"Node VM failed:\n{proc.stderr}\n{proc.stdout}"
