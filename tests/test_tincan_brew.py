import json
from pathlib import Path

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.tincan_actions import execute_action, load_pending_actions
from iot_federated_agent_memory.tincan_brew import (
    generate_homebrew_formula,
    handle_brew_command,
    load_cellar_state,
)
from iot_federated_agent_memory.tincan_cli import main as tincan_main


def test_generate_homebrew_formulas() -> None:
    rb_tincan = generate_homebrew_formula("tincan")
    assert "class Tincan < Formula" in rb_tincan
    assert 'depends_on "python@3.13"' in rb_tincan
    assert "tincan brew list" in rb_tincan

    rb_palace = generate_homebrew_formula("context-palace")
    assert "class ContextPalace < Formula" in rb_palace
    assert "context_palace.cli" in rb_palace


def test_handle_brew_commands_and_hitl_gate(tmp_path: Path) -> None:
    cfg = str(tmp_path)

    # 1. Tap NoJuanNobody/tap
    tap_res = handle_brew_command("brew tap NoJuanNobody/tap", config_dir=cfg)
    assert tap_res["status"] == "ok"
    assert "NoJuanNobody/tap" in tap_res["taps"]

    # 2. Install packages and queue HITL Accessibility Gate action
    inst_res = handle_brew_command("brew install context-palace jq", peer_id="aeonik", config_dir=cfg, queue_hitl=True)
    assert inst_res["status"] == "ok"
    assert "context-palace" in inst_res["installed_now"]
    assert "jq" in inst_res["installed_now"]
    assert "🍺  /opt/homebrew/Cellar/context-palace/2.0.0" in inst_res["output"]

    # Verify cellar persistence
    cellar = load_cellar_state(cfg)
    assert "context-palace" in cellar["installed"]
    assert "jq" in cellar["installed"]

    # Verify HITL Accessibility Gate queued the native brew install
    pending = load_pending_actions(cfg)
    assert any(a["action_type"] == "brew" and "context-palace" in a["command"] for a in pending)
    first_seq = pending[0]["seq"]
    exec_res = execute_action(str(first_seq), config_dir=cfg)
    assert exec_res["status"] == "completed"
    assert "Approved & executed via TinCan Homebrew Bridge" in exec_res["result"]

    # 3. List, Search, Info, Doctor, Uninstall
    list_res = handle_brew_command("brew list", config_dir=cfg)
    assert "context-palace" in list_res["installed"]

    search_res = handle_brew_command("brew search kokoro", config_dir=cfg)
    assert any("kokoro-tts" in m for m in search_res["matches"])

    info_res = handle_brew_command("brew info tincan", config_dir=cfg)
    assert info_res["package"]["version"] == "2.2.0"

    doc_res = handle_brew_command("brew doctor", config_dir=cfg)
    assert "Your system is ready to brew." in doc_res["output"]

    rm_res = handle_brew_command("brew uninstall jq", config_dir=cfg)
    assert "jq" in rm_res["removed"]
    assert "jq" not in rm_res["installed"]


def test_tincan_cli_brew_subcommand_and_terminal_ui(tmp_path: Path, capsys) -> None:
    rc = tincan_main(["--dir", str(tmp_path), "brew", "install", "kokoro-tts", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert "kokoro-tts" in out["installed_now"]

    # Verify web terminal UI has brew tab, formula command, and /api/terminal/brew handler
    assert 'data-tab="brew"' in MESH_OS_HTML_UI
    assert 'data-cmd="brew"' in MESH_OS_HTML_UI
    assert "/Formula/tincan.rb" in MESH_OS_HTML_UI
    assert "/api/terminal/brew" in MESH_OS_HTML_UI
