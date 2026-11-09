import os
import tempfile
import pytest
from iot_federated_agent_memory.account_registry import PeerAccountRegistry


def test_peer_account_registration_and_billing_flow():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db = tf.name

    try:
        registry = PeerAccountRegistry(db_path=temp_db)
        
        # Test registration
        acc = registry.register_account(
            peer_id="peer-primary-mac",
            full_name="Alejandro Londono",
            phone_number="+15615550199",
            email="alondono@example.com",
            initial_tokens=50000,
            initial_credit_usd=1.00,
        )
        assert acc["peer_id"] == "peer-primary-mac"
        assert acc["token_balance"] == 50000

        # Bill tokens
        receipt = registry.bill_tokens(
            peer_id="peer-primary-mac",
            prompt_tokens=500,
            completion_tokens=250,
            total_tokens=750,
            cost_usd=0.0015,
            model="gemini-brain",
        )
        assert receipt["tokens_billed"] == 750
        assert receipt["remaining_token_balance"] == 49250
        assert receipt["remaining_credit_usd"] == 0.9985

        # Top up credits
        topped = registry.top_up_credits("peer-primary-mac", amount_usd=5.00, tokens=20000)
        assert topped["token_balance"] == 69250

        # Billing summary
        summary = registry.get_billing_summary("peer-primary-mac")
        assert summary["token_balance"] == 69250
        assert len(summary["recent_invoices"]) == 1
        assert summary["recent_invoices"][0]["total_tokens"] == 750
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
