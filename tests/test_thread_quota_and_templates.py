"""Quota, billing hook, and scam-case template seeds."""

from __future__ import annotations

from pathlib import Path

import pytest

from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.thread_fs import (
    ThreadQuotaError,
    list_files,
    list_templates,
    read_file,
    start_or_continue_thread,
    thread_quota_settings,
    write_file,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "threads"


@pytest.fixture
def small_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TINCAN_THREAD_MAX_FILE_BYTES", "64")
    monkeypatch.setenv("TINCAN_THREAD_MAX_TOTAL_BYTES", "100")
    monkeypatch.setenv("TINCAN_THREAD_HARD_MAX_FILE_BYTES", "200")
    monkeypatch.setenv("TINCAN_THREAD_HARD_MAX_TOTAL_BYTES", "250")
    monkeypatch.setenv("TINCAN_THREAD_OVERAGE_TOKENS_PER_KIB", "1")


@pytest.fixture
def registry(tmp_path: Path) -> PeerAccountRegistry:
    return PeerAccountRegistry(db_path=str(tmp_path / "accounts.db"))


def test_quota_settings_read_env(small_quota):
    s = thread_quota_settings()
    assert s["max_file_bytes"] == 64
    assert s["max_total_bytes"] == 100
    assert s["hard_max_file_bytes"] == 200
    assert s["overage_tokens_per_kib"] == 1


def test_free_tier_write_allowed_without_billing(root: Path, small_quota):
    tdir = start_or_continue_thread("peer-1", root=root)
    write_file("peer-1", tdir.name, "ok.txt", "hello", root=root)
    assert read_file("peer-1", tdir.name, "ok.txt", root=root) == "hello"


def test_over_tier_without_billing_raises(root: Path, small_quota):
    tdir = start_or_continue_thread("peer-1", root=root)
    with pytest.raises(ThreadQuotaError) as ei:
        write_file("peer-1", tdir.name, "big.txt", "x" * 80, root=root)
    assert ei.value.code == "tokens_required"
    assert ei.value.tokens_required >= 1


def test_hard_limit_rejected_even_with_billing(root: Path, small_quota, registry: PeerAccountRegistry):
    registry.register_account(
        "peer-1", "Test Peer", "+15555550100", "peer1@mesh.local", initial_tokens=50_000
    )
    tdir = start_or_continue_thread("peer-1", root=root)

    def _bill(plan):
        raise AssertionError("billing must not run for hard-limit writes")

    with pytest.raises(ThreadQuotaError) as ei:
        write_file("peer-1", tdir.name, "huge.txt", "x" * 201, root=root, billing=_bill)
    assert ei.value.code == "hard_limit"


def test_over_tier_debits_tokens(root: Path, small_quota, registry: PeerAccountRegistry):
    registry.register_account(
        "peer-1", "Test Peer", "+15555550100", "peer1@mesh.local", initial_tokens=100
    )
    tdir = start_or_continue_thread("peer-1", root=root)
    from iot_federated_agent_memory.thread_fs import charge_thread_quota

    receipt_box = {}

    def _bill(plan):
        receipt_box["r"] = charge_thread_quota(registry, "peer-1", plan)
        return receipt_box["r"]

    write_file("peer-1", tdir.name, "big.txt", "x" * 80, root=root, billing=_bill)
    assert read_file("peer-1", tdir.name, "big.txt", root=root) == "x" * 80
    assert receipt_box["r"]["tokens_billed"] >= 1
    assert receipt_box["r"]["model"] == "thread-fs-quota"
    remaining = registry.get_account_by_peer("peer-1")["token_balance"]
    assert remaining == 100 - receipt_box["r"]["tokens_billed"]


def test_over_tier_insufficient_tokens(root: Path, small_quota, registry: PeerAccountRegistry):
    registry.register_account(
        "peer-1", "Test Peer", "+15555550100", "peer1@mesh.local", initial_tokens=0
    )
    tdir = start_or_continue_thread("peer-1", root=root)
    from iot_federated_agent_memory.thread_fs import charge_thread_quota

    def _bill(plan):
        return charge_thread_quota(registry, "peer-1", plan)

    with pytest.raises(ThreadQuotaError) as ei:
        write_file("peer-1", tdir.name, "big.txt", "x" * 80, root=root, billing=_bill)
    assert ei.value.code == "insufficient_tokens"


def test_scam_case_template_seeds_placeholder_files(root: Path):
    assert "scam-case" in list_templates()
    tdir = start_or_continue_thread("peer-1", root=root, template="scam-case")
    paths = {e["path"] for e in list_files("peer-1", tdir.name, root=root)}
    assert "README.txt" in paths
    assert "case-brief.md" in paths
    assert "evidence/inbox-excerpt.txt" in paths
    readme = read_file("peer-1", tdir.name, "README.txt", root=root)
    assert "PLACEHOLDER" in readme
    brief = read_file("peer-1", tdir.name, "case-brief.md", root=root)
    assert "PLACEHOLDER" in brief
    excerpt = read_file("peer-1", tdir.name, "evidence/inbox-excerpt.txt", root=root)
    assert "PLACEHOLDER" in excerpt
    # Continue does not mint a new thread or fail
    again = start_or_continue_thread("peer-1", tdir.name, root=root, template="scam-case")
    assert again == tdir


def test_unknown_template_raises(root: Path):
    from iot_federated_agent_memory.thread_fs import ThreadFsError

    with pytest.raises(ThreadFsError, match="unknown thread template"):
        start_or_continue_thread("peer-1", root=root, kind="not-a-real-template")
