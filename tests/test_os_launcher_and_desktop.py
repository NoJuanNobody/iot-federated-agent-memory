"""End-to-end tests for TinCan OS local node launcher (AI-246), installer (AI-247),
and Tauri 2 desktop shell parity & theme fixes (AI-249).

Zero mocks or stubs: spawns a real local `server.py` node bound to 127.0.0.1 on
an ephemeral port with isolated temp config/data directories, verifies `/windows`,
`/api/local/identity`, every single window route loading on its own, and the CLI
`tincan os` / `tincan open` lifecycle.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest

from iot_federated_agent_memory.os_launcher import (
    LocalNodeManager,
    WINDOW_CATALOG,
    resolve_window_entry,
)
from iot_federated_agent_memory.window_chrome import CELADON_BODY_JS
from iot_federated_agent_memory.zen_shell import ZEN_BODY, ZEN_HEAD

REPO_ROOT = Path(__file__).resolve().parent.parent


def _http_get(url: str, timeout: float = 5.0):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def test_window_catalog_resolution():
    assert resolve_window_entry(None)["route"] == "/"
    assert resolve_window_entry("")["route"] == "/"
    assert resolve_window_entry("board")["route"] == "/board"
    assert resolve_window_entry("cyberspace")["route"] == "/board"
    assert resolve_window_entry("space")["route"] == "/workstation"
    assert resolve_window_entry("node-studio")["route"] == "/nodes"
    assert resolve_window_entry("terminal")["route"] == "/terminal"
    assert resolve_window_entry("arena")["route"] == "/arena"
    assert resolve_window_entry("nonexistent-app-xyz") is None


def test_local_node_lifecycle_and_all_window_routes(tmp_path):
    cfg_dir = tmp_path / "cfg"
    data_dir = tmp_path / "data"
    mgr = LocalNodeManager(
        config_dir=str(cfg_dir),
        data_dir=str(data_dir),
        repo_root=str(REPO_ROOT),
    )

    try:
        state, started_new = mgr.start(host="127.0.0.1", port=0, startup_timeout=25.0)
        assert started_new is True
        assert state.host == "127.0.0.1"
        assert state.port > 0
        assert state.url == f"http://127.0.0.1:{state.port}"

        # Idempotent second start attaches to existing node
        state2, started_new2 = mgr.start(host="127.0.0.1", port=0)
        assert started_new2 is False
        assert state2.pid == state.pid
        assert state2.port == state.port

        # Status reports live node
        st = mgr.status()
        assert st["running"] is True
        assert st["pid"] == state.pid
        assert st["windows_count"] == len(WINDOW_CATALOG)

        # GET /windows returns canonical catalog with live base_url
        code, body = _http_get(f"{state.url}/windows")
        assert code == 200
        win_data = json.loads(body)
        assert win_data["node_mode"] == "local"
        assert win_data["count"] == len(WINDOW_CATALOG)
        routes = [w["route"] for w in win_data["windows"]]
        assert "/" in routes and "/board" in routes and "/workstation" in routes and "/nodes" in routes

        # GET /api/local/identity returns passwordless local identity
        code, id_body = _http_get(f"{state.url}/api/local/identity")
        assert code == 200
        id_data = json.loads(id_body)
        assert id_data["local_node"] is True
        assert id_data["offline_ready"] is True
        assert id_data["passwordless"] is True

        # Every single window route in /windows must load cleanly on its own (200 OK)
        for entry in win_data["windows"]:
            status_code, html = _http_get(entry["url"])
            assert status_code == 200, f"Route {entry['route']} failed with {status_code}"
            assert "<html" in html.lower() or "<!doctype html" in html.lower(), (
                f"Route {entry['route']} did not return HTML"
            )

        # CLI `tincan open board --no-open --json` and `tincan open --no-open --json`
        env = os.environ.copy()
        env["TINCAN_CONFIG_DIR"] = str(cfg_dir)
        env["TINCAN_DATA_DIR"] = str(data_dir)

        res_board = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tincan_cli.py"), "--dir", str(cfg_dir), "open", "board", "--no-open", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
            check=True,
        )
        board_out = json.loads(res_board.stdout)
        assert board_out["app"] == "board"
        assert board_out["url"] == f"{state.url}/board"

        res_desktop = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tincan_cli.py"), "--dir", str(cfg_dir), "open", "--no-open", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
            check=True,
        )
        desktop_out = json.loads(res_desktop.stdout)
        assert desktop_out["app"] == "desktop"
        assert desktop_out["url"] == f"{state.url}/"

        # Stop cleanly via CLI `tincan os --stop --json`
        res_stop = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tincan_cli.py"), "--dir", str(cfg_dir), "os", "--stop", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
            check=True,
        )
        stop_out = json.loads(res_stop.stdout)
        assert stop_out["stopped"] is True
        assert mgr.status()["running"] is False
    finally:
        mgr.stop()


def test_design_system_theme_and_launcher_parity():
    # AI-249: OS appearance default + warm sumi/washi/persimmon dark mode
    assert "prefers-color-scheme" in CELADON_BODY_JS
    assert "clean === 'system'" in CELADON_BODY_JS
    assert "#0e0d0b" in ZEN_HEAD
    assert "#17150f" in ZEN_HEAD
    assert "#ece6da" in ZEN_HEAD
    assert "#d0703f" in ZEN_HEAD
    assert "Shippori Mincho" in ZEN_HEAD
    assert "Zen Kaku Gothic New" in ZEN_HEAD

    # AI-249: Missing tools added to Cmd-K launcher + /theme + TinCanZen bridge
    for token in ("'win-call'", "'win-browser'", "'win-localhost'", "'/theme'", "window.TinCanZen"):
        assert token in ZEN_BODY, f"Expected {token} in zen_shell.py ZEN_BODY"


def test_installer_syntax_and_local_node_setup():
    installer = REPO_ROOT / "install_peer.sh"
    res = subprocess.run(["bash", "-n", str(installer)], capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"bash -n failed: {res.stderr}"
    text = installer.read_text(encoding="utf-8")
    assert "--slim" in text
    assert "tincan os" in text
    assert "ensure_local_identity" in text


def test_desktop_tauri_shell_has_no_hardcoded_user_paths():
    main_rs = (REPO_ROOT / "tincan-desktop" / "src" / "main.rs").read_text(encoding="utf-8")
    assert "/Users/alejandrolondono" not in main_rs
    assert "find_tincan_bin" in main_rs
    assert "CmdOrCtrl+K" in main_rs
    assert "Theme: Follow System" in main_rs
    assert "Theme: Light (Celadon)" in main_rs
    assert "Theme: Dark (Ink & Paper)" in main_rs
    assert "on_new_window" in main_rs


def test_terminal_tui_renders_all_mesh_os_tabs():
    from iot_federated_agent_memory.tui import App

    app = App("http://127.0.0.1:1", "overview", 0, None, "256", False, is_local=True)
    for tab in ("overview", "apps", "board", "workstation", "quests"):
        app.view = tab
        rendered = app.frame(110, 32, 0.0, None).render("256")
        assert "TinCan Mesh OS" in rendered
    app.view = "apps"
    apps_frame = app.frame(110, 32, 0.0, None).render("256")
    assert "board" in apps_frame and "workstation" in apps_frame and "node-studio" in apps_frame
    app.cmd_open = True
    app.cmd_query = "board"
    cmd_frame = app.frame(110, 32, 0.0, None).render("256")
    assert "/board" in cmd_frame

