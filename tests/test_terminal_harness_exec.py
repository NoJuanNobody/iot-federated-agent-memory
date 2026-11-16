"""Tests for real non-interactive harness execution inside .space sandboxes and HITL gate."""

import json
import os
import shutil
import stat
from pathlib import Path

from iot_federated_agent_memory.agent_space import (
    AgentSpaceManager,
    SingleFileSpaceVFS,
    WasmAndCodePlaygroundRunner,
)
from iot_federated_agent_memory.shell_component import SHELL_JS
from iot_federated_agent_memory.tincan_actions import enqueue_action, execute_action
from iot_federated_agent_memory.tincan_brew import (
    _build_harness_exec_argv,
    discover_harnesses,
    handle_harness_command,
    save_cellar_state,
)
from tests.test_tincan_ux_updates import _http_json, _live_server


def _write_fake_cli(path: Path, body: str) -> str:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(path)


def test_discover_harnesses_prefers_installed_over_stale_cellar(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = tmp_path / ".tin-can"
    save_cellar_state(
        {
            "taps": ["homebrew/core", "NoJuanNobody/tap"],
            "installed": {
                "antigravity": {"name": "antigravity", "version": "2.0.0", "kind": "formula"},
            },
        },
        config_dir=str(cfg),
    )
    fake_claude = _write_fake_cli(tmp_path / "claude", "#!/bin/sh\necho 1.0\n")
    monkeypatch.setattr(shutil, "which", lambda cmd: fake_claude if cmd == "claude" else None)

    snap = discover_harnesses(str(tmp_path))
    assert snap["best_harness"] == "claude-code"
    assert snap["best_cli"] == "claude"


def test_build_harness_exec_argv_variants():
    target_claude = {"id": "claude-code", "cli": "claude", "bin_path": "/usr/local/bin/claude", "detected_local": []}
    argv, cmd = _build_harness_exec_argv(target_claude, '"summarize main.py"')
    assert argv == [
        "/usr/local/bin/claude",
        "-p",
        "--permission-mode",
        "acceptEdits",
        "--no-session-persistence",
        "summarize main.py",
    ]
    assert "summarize main.py" in cmd

    argv_ver, _ = _build_harness_exec_argv(target_claude, "--version")
    assert argv_ver == ["/usr/local/bin/claude", "--version"]

    target_dsx = {
        "id": "dsx",
        "cli": "dsx",
        "bin_path": None,
        "detected_local": ["/opt/dsx/dist/index.js"],
    }
    argv_dsx, _ = _build_harness_exec_argv(target_dsx, "check files")
    assert argv_dsx == ["node", "/opt/dsx/dist/index.js", "--yes", "-p", "check files"]


def test_handle_harness_command_executes_and_syncs_space(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key-123")

    fake_claude = _write_fake_cli(
        tmp_path / "claude",
        """#!/usr/bin/env python3
import os, pathlib, sys
print("ARGS:" + "|".join(sys.argv[1:]))
print("KEY:" + os.environ.get("OPENROUTER_API_KEY", ""))
pathlib.Path("harness_out.txt").write_text("from claude\\n", encoding="utf-8")
pathlib.Path(".claude").mkdir(exist_ok=True)
pathlib.Path(".claude/session.json").write_text("{}", encoding="utf-8")
""",
    )
    monkeypatch.setattr(shutil, "which", lambda cmd: fake_claude if cmd == "claude" else None)

    vfs = SingleFileSpaceVFS(scope="user", owner_id="tester_exec", base_dir=str(tmp_path / "spaces"))
    runner = WasmAndCodePlaygroundRunner()

    # Bare invocation explains non-interactive usage without blocking on a TTY
    bare = handle_harness_command("claude", execute=True, space_vfs=vfs, space_runner=runner)
    assert bare["status"] == "ok"
    assert bare["executed"] is False
    assert "Pass a prompt" in bare["output"]

    # Prompt invocation runs inside materialized .space, passes API key, and syncs outputs
    res = handle_harness_command(
        'claude "create output"',
        peer_id="tester",
        execute=True,
        space_vfs=vfs,
        space_runner=runner,
    )
    assert res["status"] == "ok", res
    assert res["executed"] is True
    assert res["exit_code"] == 0
    assert "KEY:or-test-key-123" in res["stdout"]
    assert "create output" in res["stdout"]
    assert "/harness_out.txt" in res["synced_files"]
    assert not any(".claude" in p for p in res["synced_files"])
    assert vfs.read_file("/harness_out.txt")["content"] == "from claude\n"


def test_http_terminal_harness_exec_and_error_status(tmp_path, monkeypatch):
    import server

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(server, "_space_manager", AgentSpaceManager(base_dir=str(tmp_path / "spaces")))
    fake_codex = _write_fake_cli(
        tmp_path / "codex",
        """#!/usr/bin/env python3
import pathlib, sys
if "--fail" in sys.argv:
    sys.stderr.write("missing auth\\n")
    sys.exit(2)
pathlib.Path("codex_note.md").write_text("done\\n", encoding="utf-8")
print("codex ok")
""",
    )
    monkeypatch.setattr(shutil, "which", lambda cmd: fake_codex if cmd == "codex" else None)

    with _live_server() as addr:
        st_ok, data_ok = _http_json(
            addr,
            "POST",
            "/api/terminal/harness",
            {"command": "codex write note", "scope": "user", "owner_id": "http_exec", "peer_id": "http_exec"},
        )
        assert st_ok == 200, data_ok
        assert data_ok["executed"] is True
        assert data_ok["exit_code"] == 0
        assert "/codex_note.md" in data_ok["synced_files"]

        st_err, data_err = _http_json(
            addr,
            "POST",
            "/api/terminal/harness",
            {"command": "codex --fail", "scope": "user", "owner_id": "http_exec", "peer_id": "http_exec"},
        )
        assert st_err == 400, data_err
        assert data_err["status"] == "error"
        assert data_err["exit_code"] == 2
        assert "missing auth" in data_err["output"]


def test_tincan_actions_executes_harness_type(tmp_path):
    fake_bin = _write_fake_cli(
        tmp_path / "echo_harness",
        "#!/usr/bin/env python3\nimport sys\nprint('HITL:' + ' '.join(sys.argv[1:]))\n",
    )
    cfg = str(tmp_path)
    enqueue_action(
        seq=77,
        sender="tc:test",
        sender_alias="tester",
        command_text=f"{fake_bin} -p hello",
        config_dir=cfg,
        action_type="harness",
    )
    res = execute_action("77", config_dir=cfg)
    assert res["status"] == "completed"
    assert "HITL:-p hello" in res["result"]


def test_shell_js_and_dockerfile_harness_wiring():
    assert "'gemini'" in SHELL_JS and "scope: c.scope" in SHELL_JS and "termSpaceChanged(c)" in SHELL_JS
    dockerfile = (Path(__file__).resolve().parent.parent / "Dockerfile").read_text(encoding="utf-8")
    for pkg in ("@anthropic-ai/claude-code", "opencode-ai", "@openai/codex", "@google/gemini-cli", "vendor/dsx", "aaif-goose/goose"):
        assert pkg in dockerfile
    for check in ("claude --version", "opencode --version", "codex --version", "gemini --version", "dsx --help", "goose --version"):
        assert check in dockerfile
