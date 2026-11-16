"""Tests for live interactive PTY TUI sessions (WebSocket + HTTP) and .space VFS AI context injection."""

from __future__ import annotations

import base64
import hashlib
import http.client
import os
import shutil
import socket
import struct
import time
from pathlib import Path

from iot_federated_agent_memory.agent_space import AgentSpaceManager, build_space_context_summary
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.pty_sessions import PTYSessionManager, prepare_tui_command
from iot_federated_agent_memory.shell_component import SHELL_JS
from tests.test_tincan_ux_updates import _http_json, _live_server


def test_build_space_context_summary_includes_active_file_and_palace(tmp_path):
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    vfs = sm.get_or_create_space("user", "ctx_user")
    vfs.write_file("/src/app.py", "def greet():\n    return 'hello-vfs'\n", updated_by="test")
    vfs.write_file("/assets/blob.bin", b"\x00\xff\x01\x02", mime_type="application/octet-stream", updated_by="test")

    summary = build_space_context_summary(
        vfs,
        active_file="/src/app.py",
        palace_snippets=[{"canonical_name": "deploy_rule", "active_value": "always verify live"}],
    )
    assert summary["scope"] == "user"
    assert summary["owner_id"] == "ctx_user"
    assert summary["active_file"] == "/src/app.py"
    assert "/src/app.py" in summary["text"]
    assert "hello-vfs" in summary["text"]
    assert "deploy_rule: always verify live" in summary["text"]
    assert "/assets/blob.bin" in summary["text"]  # listed in tree, binary bytes skipped


def test_chat_endpoint_injects_space_vfs_context(tmp_path, monkeypatch):
    import tests.test_tincan_ux_updates as _ux

    srv = _ux.server
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    vfs = sm.get_or_create_space("user", "chat_ctx_peer")
    vfs.write_file("/src/secret_note.txt", "VFS_CONTEXT_MARKER_42", updated_by="test")
    monkeypatch.setattr(srv, "_space_manager", sm)

    captured = {}

    def fake_dispatch(*, alias, messages, temperature=0.7, max_tokens=512):
        captured["alias"] = alias
        captured["messages"] = messages
        return {
            "id": "sim-1",
            "choices": [{"message": {"role": "assistant", "content": "Saw VFS_CONTEXT_MARKER_42"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    monkeypatch.setattr(srv.router, "dispatch_completion", fake_dispatch)
    monkeypatch.setattr(srv.account_registry, "get_account_by_peer", lambda p: None)

    with _live_server() as addr:
        st, data = _http_json(
            addr,
            "POST",
            "/api/chat",
            {
                "model": "gemini-brain",
                "prompt": "What is in my space?",
                "scope": "user",
                "owner_id": "chat_ctx_peer",
                "active_file": "/src/secret_note.txt",
                "use_space_context": True,
                "peer_id": "chat_ctx_peer",
            },
        )
    assert st == 200, data
    assert data["space_context"]["owner_id"] == "chat_ctx_peer"
    assert len(captured["messages"]) == 2
    assert captured["messages"][0]["role"] == "system"
    assert "VFS_CONTEXT_MARKER_42" in captured["messages"][0]["content"]


def test_prepare_tui_command_uses_interactive_modes(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    fake_bins = {}
    for cli in ("claude", "opencode", "dsx", "codex", "goose"):
        p = tmp_path / cli
        p.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        p.chmod(0o755)
        fake_bins[cli] = str(p)
    monkeypatch.setattr(shutil, "which", lambda c: fake_bins.get(c))

    c_argv, c_env, c_id = prepare_tui_command("claude", space_context_text="VFS summary")
    assert c_id == "claude-code"
    assert "-p" not in c_argv and "--permission-mode" in c_argv and "--append-system-prompt" in c_argv
    assert c_env["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"

    o_argv, _, o_id = prepare_tui_command("opencode")
    assert o_id == "opencode" and "run" not in o_argv and "--model" in o_argv

    d_argv, _, d_id = prepare_tui_command("dsx")
    assert d_id == "dsx" and "-p" not in d_argv

    x_argv, _, x_id = prepare_tui_command("codex")
    assert x_id == "codex" and "exec" not in x_argv and "--dangerously-bypass-approvals-and-sandbox" in x_argv

    g_argv, g_env, g_id = prepare_tui_command("goose")
    assert g_id == "goose" and "session" in g_argv and g_env["GOOSE_PROVIDER"] == "openrouter"


def _ws_pack_client_frame(payload: bytes, opcode: int = 0x1) -> bytes:
    mask = b"\x12\x34\x56\x78"
    length = len(payload)
    if length < 126:
        hdr = bytes([0x80 | opcode, 0x80 | length])
    else:
        hdr = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, length)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return hdr + mask + masked


def _ws_read_server_frame(sock: socket.socket) -> tuple[int, bytes]:
    hdr = sock.recv(2)
    while len(hdr) < 2:
        hdr += sock.recv(2 - len(hdr))
    opcode = hdr[0] & 0x0F
    length = hdr[1] & 0x7F
    if length == 126:
        ext = sock.recv(2)
        while len(ext) < 2:
            ext += sock.recv(2 - len(ext))
        length = struct.unpack("!H", ext)[0]
    elif length == 127:
        ext = sock.recv(8)
        while len(ext) < 8:
            ext += sock.recv(8 - len(ext))
        length = struct.unpack("!Q", ext)[0]
    buf = bytearray()
    while len(buf) < length:
        buf.extend(sock.recv(length - len(buf)))
    return opcode, bytes(buf)


def test_live_pty_websocket_resize_and_space_sync(tmp_path, monkeypatch):
    import tests.test_tincan_ux_updates as _ux

    srv = _ux.server
    sm = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    vfs = sm.get_or_create_space("user", "pty_tester")
    vfs.write_file("/src/hello.py", "print('hello_space')\n", updated_by="test")
    monkeypatch.setattr(srv, "_space_manager", sm)
    monkeypatch.setattr(srv, "_pty_manager", PTYSessionManager())

    with _live_server() as addr:
        st_start, d_start = _http_json(
            addr,
            "POST",
            "/api/terminal/pty/start",
            {"harness": "sh", "scope": "user", "owner_id": "pty_tester", "active_file": "/src/hello.py", "cols": 90, "rows": 24},
        )
        assert st_start == 200, d_start
        sid = d_start["session_id"]

        host, port = addr
        sock = socket.create_connection((host, port), timeout=5)
        try:
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            req = (
                f"GET /api/terminal/pty/ws?session_id={sid} HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode("ascii")
            sock.sendall(req)

            resp_buf = bytearray()
            while b"\r\n\r\n" not in resp_buf:
                resp_buf.extend(sock.recv(1024))
            assert b"101 Switching Protocols" in resp_buf
            expected_accept = base64.b64encode(
                hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
            ).decode("ascii").encode("ascii")
            assert expected_accept in resp_buf

            # Send resize control message + shell command checking context file & writing a new space file.
            sock.sendall(_ws_pack_client_frame(b'\x01{"type":"resize","cols":120,"rows":36}'))
            sock.sendall(_ws_pack_client_frame(b"cat .tincan/SPACE_CONTEXT.md >/dev/null && printf 'PTY_OK\\n' && printf 'from_tui' > tui_created.txt\n"))

            collected = b""
            deadline = time.time() + 5.0
            while time.time() < deadline and b"PTY_OK" not in collected:
                op, data = _ws_read_server_frame(sock)
                if op in (0x1, 0x2):
                    collected += data
            assert b"PTY_OK" in collected
        finally:
            sock.close()

        # Wait briefly for printf redirection to finish before syncing
        time.sleep(0.15)
        st_sync, d_sync = _http_json(addr, "POST", "/api/terminal/pty/sync", {"session_id": sid})
        assert st_sync == 200, d_sync
        assert "/tui_created.txt" in d_sync["synced_files"]
        assert "AGENTS.md" not in d_sync["synced_files"]
        assert vfs.read_file("/tui_created.txt")["content"] == "from_tui"

        st_stop, d_stop = _http_json(addr, "POST", "/api/terminal/pty/stop", {"session_id": sid})
        assert st_stop == 200, d_stop

        # Also verify vendored xterm assets serve 200
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/assets/vendor/xterm/xterm.js")
        r = conn.getresponse()
        r.read()
        assert r.status == 200
        conn.close()


def test_ui_wires_xterm_tui_and_space_context():
    for path in ("/assets/vendor/xterm/xterm.css", "/assets/vendor/xterm/xterm.js", "/assets/vendor/xterm/addon-fit.js"):
        assert path in MESH_OS_HTML_UI
        assert (Path(__file__).resolve().parent.parent / path.lstrip("/")).is_file()
    assert 'data-tui="claude"' in SHELL_JS and "use_space_context: true" in SHELL_JS
    assert "/api/terminal/pty/ws" in SHELL_JS and "/api/terminal/pty/stream" in SHELL_JS
