"""HTTP helper and MCP tool coverage for thread file access."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.tincan_mcp import handle_mcp_request
from iot_federated_agent_memory.thread_api import (
    api_list_files,
    api_read_file,
    api_write_file,
    set_account_registry,
)
from iot_federated_agent_memory.thread_fs import start_or_continue_thread, write_file


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "threads"
    monkeypatch.setenv("TINCAN_THREADS_DIR", str(root))
    # Isolate the other data-dir env so MCP/default root stays on this folder.
    monkeypatch.delenv("TINCAN_DATA_DIR", raising=False)
    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    return root


@pytest.fixture
def registry(tmp_path: Path) -> PeerAccountRegistry:
    reg = PeerAccountRegistry(db_path=str(tmp_path / "accounts.db"))
    set_account_registry(reg)
    return reg


def test_list_read_write_happy_path(root: Path, registry: PeerAccountRegistry):
    tdir = start_or_continue_thread("peer-1", root=root)
    write_file("peer-1", tdir.name, "notes.txt", "hi", root=root)
    code, body = api_list_files("peer-1", tdir.name, registry=registry, root=root)
    assert code == 200
    assert any(e["path"] == "notes.txt" for e in body["files"])
    code, body = api_read_file("peer-1", tdir.name, "notes.txt", registry=registry, root=root)
    assert code == 200
    assert body["content"] == "hi"
    code, body = api_write_file(
        "peer-1", tdir.name, "notes.txt", "updated", registry=registry, root=root
    )
    assert code == 200
    code, body = api_read_file("peer-1", tdir.name, "notes.txt", registry=registry, root=root)
    assert body["content"] == "updated"


def test_zero_balance_registered_peer_is_402(root: Path, registry: PeerAccountRegistry):
    registry.register_account(
        "peer-1", "Test Peer", "+15555550100", "peer1@mesh.local", initial_tokens=0
    )
    tdir = start_or_continue_thread("peer-1", root=root)
    write_file("peer-1", tdir.name, "notes.txt", "hi", root=root)
    code, body = api_list_files("peer-1", tdir.name, registry=registry, root=root)
    assert code == 402
    code, body = api_read_file("peer-1", tdir.name, "notes.txt", registry=registry, root=root)
    assert code == 402
    code, body = api_write_file("peer-1", tdir.name, "notes.txt", "x", registry=registry, root=root)
    assert code == 402


def test_unsafe_peer_id_returns_thread_error(root: Path, registry: PeerAccountRegistry):
    code, body = api_list_files("../etc", "abc", registry=registry, root=root)
    assert code == 400
    assert "thread_error" in body


def test_missing_peer_uses_anonymous_bucket(root: Path, registry: PeerAccountRegistry):
    from iot_federated_agent_memory.thread_fs import ANONYMOUS_PEER_ID

    tdir = start_or_continue_thread(ANONYMOUS_PEER_ID, root=root)
    write_file(ANONYMOUS_PEER_ID, tdir.name, "hello.txt", "anon", root=root)
    code, body = api_list_files(None, tdir.name, registry=registry, root=root)
    assert code == 200
    assert body["peer_id"] == ANONYMOUS_PEER_ID
    code, body = api_read_file("", tdir.name, "hello.txt", registry=registry, root=root)
    assert code == 200
    assert body["content"] == "anon"


def test_unknown_thread_is_404(root: Path, registry: PeerAccountRegistry):
    code, body = api_list_files("peer-1", "a" * 32, registry=registry, root=root)
    assert code == 404


def test_mcp_tools_list_and_call(root: Path, registry: PeerAccountRegistry):
    tdir = start_or_continue_thread("peer-1", root=root)
    write_file("peer-1", tdir.name, "notes.txt", "via-mcp", root=root)
    listed = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = [t["name"] for t in listed["result"]["tools"]]
    assert "tincan_thread_list_files" in names
    assert "tincan_thread_read_file" in names
    assert "tincan_thread_write_file" in names
    resp = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "tincan_thread_read_file",
                "arguments": {
                    "peer_id": "peer-1",
                    "thread_id": tdir.name,
                    "path": "notes.txt",
                },
            },
        }
    )
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["content"] == "via-mcp"
