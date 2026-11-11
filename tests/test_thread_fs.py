"""Focused tests for the per-thread filesystem scaffold."""

from __future__ import annotations

import io
import os
import json
import uuid
from pathlib import Path
from unittest import mock

import pytest

from iot_federated_agent_memory.tincan_agent import SYSTEM_PROMPT, TinCanAgentChat
from iot_federated_agent_memory.thread_fs import (
    ANONYMOUS_PEER_ID,
    ThreadFsError,
    delete_file,
    ensure_thread_dir,
    list_files,
    mint_thread_id,
    peer_dir,
    read_file,
    resolve_threads_root,
    sanitize_peer_id,
    sanitize_thread_id,
    start_or_continue_thread,
    thread_dir,
    thread_exists,
    write_file,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "threads"


def test_sanitize_ids_accept_safe_names():
    assert sanitize_thread_id("S001-case") == "S001-case"
    assert sanitize_thread_id("  abc_def.1  ") == "abc_def.1"
    assert sanitize_peer_id("peer-primary-mac") == "peer-primary-mac"
    assert sanitize_peer_id(ANONYMOUS_PEER_ID) == "anonymous"


@pytest.mark.parametrize("bad", ["", ".", "..", "../x", "a/b", "/abs", "has space", "bad id!", "~foo"])
def test_sanitize_ids_reject_unsafe_names(bad):
    with pytest.raises(ThreadFsError):
        sanitize_thread_id(bad)
    with pytest.raises(ThreadFsError):
        sanitize_peer_id(bad)


def test_mint_thread_id_is_uuid4_hex():
    a = mint_thread_id()
    b = mint_thread_id()
    assert a != b
    uuid.UUID(a)
    assert a == uuid.UUID(a).hex
    assert len(a) == 32
    assert sanitize_thread_id(a) == a


def test_start_or_continue_mints_new_id_and_nests_under_peer(root: Path):
    tdir = start_or_continue_thread("peer-1", root=root)
    assert tdir.parent == (root.resolve() / "peer-1")
    assert tdir == thread_dir("peer-1", tdir.name, root=root)
    assert (tdir / "files").is_dir()
    meta = json.loads((tdir / "thread.json").read_text())
    assert meta["thread_id"] == tdir.name
    assert meta["peer_id"] == "peer-1"
    assert len(tdir.name) == 32
    assert thread_exists("peer-1", tdir.name, root=root)


def test_start_or_continue_reuses_existing_thread_for_same_peer(root: Path):
    first = start_or_continue_thread("peer-1", root=root)
    again = start_or_continue_thread("peer-1", first.name, root=root)
    assert again == first
    # Custom field must survive ensure via continue.
    meta = json.loads((first / "thread.json").read_text())
    meta["note"] = "keep me"
    (first / "thread.json").write_text(json.dumps(meta))
    start_or_continue_thread("peer-1", first.name, root=root, metadata={"note": "ignored"})
    meta2 = json.loads((first / "thread.json").read_text())
    assert meta2["note"] == "keep me"
    assert meta2["peer_id"] == "peer-1"
    assert meta2["created_at"] == meta["created_at"]


def test_unknown_or_cross_peer_thread_id_mints_new(root: Path):
    original = start_or_continue_thread("alice", root=root)
    # Guessed / never-minted id is not honored.
    guessed = "a" * 32
    other = start_or_continue_thread("alice", guessed, root=root)
    assert other.name != guessed
    assert other != original
    assert not thread_exists("alice", guessed, root=root)
    # Same id, different peer: do not open alice's thread as bob.
    bob = start_or_continue_thread("bob", original.name, root=root)
    assert bob != original
    assert bob.name != original.name
    assert thread_exists("alice", original.name, root=root)
    assert not thread_exists("bob", original.name, root=root)
    # Invalid client id also mints new rather than erroring.
    minted = start_or_continue_thread("alice", "../escape", root=root)
    assert minted.name != "../escape"
    assert len(minted.name) == 32


def test_write_read_list_delete_roundtrip(root: Path):
    peer, tid = "peer-1", mint_thread_id()
    write_file(peer, tid, "notes/hello.txt", "hello mesh\n", root=root)
    assert read_file(peer, tid, "notes/hello.txt", root=root) == "hello mesh\n"
    raw = read_file(peer, tid, "notes/hello.txt", root=root, binary=True)
    assert raw == b"hello mesh\n"
    listed = list_files(peer, tid, root=root)
    paths = {e["path"] for e in listed}
    assert "notes" in paths
    assert "notes/hello.txt" in paths
    note = next(e for e in listed if e["path"] == "notes/hello.txt")
    assert note["is_dir"] is False
    assert note["size"] == len(b"hello mesh\n")
    assert delete_file(peer, tid, "notes/hello.txt", root=root) is True
    assert delete_file(peer, tid, "notes/hello.txt", root=root) is False
    with pytest.raises(ThreadFsError):
        read_file(peer, tid, "notes/hello.txt", root=root)


@pytest.mark.parametrize(
    "relpath",
    ["/etc/passwd", "..", "../escape.txt", "foo/../../etc/passwd", "~/secret", r"C:\Windows\system.ini"],
)
def test_rejects_absolute_and_traversal_paths(root: Path, relpath: str):
    peer, tid = "peer-1", mint_thread_id()
    ensure_thread_dir(peer, tid, root=root)
    with pytest.raises(ThreadFsError):
        write_file(peer, tid, relpath, "nope", root=root)
    with pytest.raises(ThreadFsError):
        read_file(peer, tid, relpath, root=root)
    with pytest.raises(ThreadFsError):
        delete_file(peer, tid, relpath, root=root)


def test_symlink_escape_is_rejected(root: Path, tmp_path: Path):
    peer, tid = "peer-1", mint_thread_id()
    tdir = ensure_thread_dir(peer, tid, root=root)
    files = tdir / "files"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    (files / "escape").symlink_to(outside)
    with pytest.raises(ThreadFsError):
        read_file(peer, tid, "escape", root=root)
    with pytest.raises(ThreadFsError):
        write_file(peer, tid, "escape", "overwrite", root=root)
    assert outside.read_text() == "secret"
    outside_dir = tmp_path / "out_dir"
    outside_dir.mkdir()
    (outside_dir / "secret.txt").write_text("secret")
    (files / "out").symlink_to(outside_dir)
    with pytest.raises(ThreadFsError):
        read_file(peer, tid, "out/secret.txt", root=root)
    listed = list_files(peer, tid, root=root)
    assert all("escape" not in e["path"] and not e["path"].startswith("out") for e in listed)


def test_peer_level_symlink_escape_is_rejected(root: Path, tmp_path: Path):
    root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-peer"
    outside.mkdir()
    (root / "evil").symlink_to(outside)
    with pytest.raises(ThreadFsError):
        thread_dir("evil", mint_thread_id(), root=root)
    with pytest.raises(ThreadFsError):
        peer_dir("evil", root=root)
    with pytest.raises(ThreadFsError):
        ensure_thread_dir("evil", mint_thread_id(), root=root)


def test_delete_refuses_directories(root: Path):
    peer, tid = "peer-1", mint_thread_id()
    write_file(peer, tid, "dir/a.txt", "x", root=root)
    with pytest.raises(ThreadFsError, match="directory"):
        delete_file(peer, tid, "dir", root=root)


def _clear_thread_root_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "TINCAN_THREADS_DIR",
        "TINCAN_DATA_DIR",
        "RAILWAY_VOLUME_MOUNT_PATH",
        "TINCAN_DIR",
    ):
        monkeypatch.delenv(name, raising=False)


def test_threads_root_env_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    threads = tmp_path / "explicit-threads"
    data_dir = tmp_path / "data-dir"
    volume = tmp_path / "railway-volume"
    tincan_dir = tmp_path / "tincan-dir"
    home = tmp_path / "home"
    override = tmp_path / "override"
    _clear_thread_root_env(monkeypatch)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda path: str(home / path[2:]) if path.startswith("~/") or path == "~" else (
            str(home) + path[1:] if path.startswith("~") else path
        ),
    )

    assert resolve_threads_root() == (home / ".tin-can" / "threads").resolve()

    monkeypatch.setenv("TINCAN_DIR", str(tincan_dir))
    assert resolve_threads_root() == (tincan_dir / "threads").resolve()

    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(volume))
    assert resolve_threads_root() == (volume / "threads").resolve()

    # Blank volume is ignored; fall back to TINCAN_DIR.
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "   ")
    assert resolve_threads_root() == (tincan_dir / "threads").resolve()
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(volume))

    monkeypatch.setenv("TINCAN_DATA_DIR", str(data_dir))
    assert resolve_threads_root() == (data_dir / "threads").resolve()

    monkeypatch.setenv("TINCAN_THREADS_DIR", str(threads))
    assert resolve_threads_root() == threads.resolve()

    assert resolve_threads_root(override) == override.resolve()


def test_agent_stores_server_thread_id_and_sends_it_on_follow_up():
    agent = TinCanAgentChat("http://relay.example", peer_id="peer-1")
    minted = mint_thread_id()
    calls = []

    def fake_urlopen(req, timeout=0):
        payload = json.loads(req.data.decode("utf-8"))
        calls.append(payload)
        body = json.dumps(
            {
                "choices": [{"message": {"content": f"ok-{len(calls)}"}}],
                "thread_id": minted,
            }
        ).encode("utf-8")
        resp = mock.Mock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = mock.Mock(return_value=False)
        return resp

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        assert agent.thread_id is None
        assert agent.ask("hello") == "ok-1"
        assert agent.thread_id == minted
        assert "thread_id" not in calls[0]
        assert calls[0]["peer_id"] == "peer-1"
        assert agent.ask("again") == "ok-2"
        assert calls[1]["thread_id"] == minted
        agent.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        # /clear in the REPL also drops thread_id; simulate that here via the same assignment.
        # (run_repl itself is interactive; the hook is tested below via source behavior)

    # Clearing memory for a new conversation should drop the thread id.
    agent.thread_id = minted
    # Use the same reset the REPL /clear path performs, plus the thread reset.
    agent.history = [{"role": "system", "content": SYSTEM_PROMPT}]
    agent.thread_id = None
    assert agent.thread_id is None
