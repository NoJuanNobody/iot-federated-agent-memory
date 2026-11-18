"""Tests for TinCan 2.2 Dark Mode, Always-Dark Terminal (.tcsh), and 12-Artboard FigCraft Dark Mode System."""

from __future__ import annotations

import json
import os
import zipfile

from iot_federated_agent_memory.ai_home_shell import AI_HOME_SHELL_CSS, render_ai_home_hub_html
from iot_federated_agent_memory.arena_duel_ui import ARENA_DUEL_RESPONSIVE_CSS, render_arena_duel
from iot_federated_agent_memory.browser_ui import render_browser_window_html
from iot_federated_agent_memory.car_ui import render_car_headunit_html
from iot_federated_agent_memory.copilot_ui import COPILOT_CSS, render_copilot_window_html
from iot_federated_agent_memory.cyberspace_board import CYBERSPACE_BOARD_DARK_CSS
from iot_federated_agent_memory.designs_gallery import (
    DARK_MODE_MOCKUPS,
    render_designs_gallery_html,
)
from iot_federated_agent_memory.install_card import INSTALL_CARD_CSS
from iot_federated_agent_memory.ios_preview import render_ios_simulator_html
from iot_federated_agent_memory.localhost_ui import render_localhost_window_html
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.node_studio_ui import (
    render_node_studio_html,
    render_node_studio_window_html,
)
from iot_federated_agent_memory.shell_component import SHELL_CSS, SHELL_JS
from iot_federated_agent_memory.token_vault_ui import TOKEN_VAULT_CSS, render_token_vault_window_html
from iot_federated_agent_memory.window_chrome import CELADON_BODY_JS, CELADON_HEAD, render_titlebar
from iot_federated_agent_memory.workstation_ui import render_workstation_window_html
from iot_federated_agent_memory.zen_shell import ZEN_HEAD

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS_DIR = os.path.join(REPO_ROOT, "assets", "designs")

BANNED_GREEN_HEX_CODES = (
    "#10b981",
    "#34d399",
    "#030605",
    "#070b09",
    "#0d1310",
)

EXPECTED_DARK_PNGS = (
    "tincan_dark_mode_master_sheet.png",
    "tincan_dark_01_zen_shell_launcher.png",
    "tincan_dark_02_terminal_pty_tui.png",
    "tincan_dark_03_ai_home_shell.png",
    "tincan_dark_04_ai_copilot.png",
    "tincan_dark_05_workstation_ide.png",
    "tincan_dark_06_3d_studio_rodin.png",
    "tincan_dark_07_node_studio.png",
    "tincan_dark_08_brain_arena_palace.png",
    "tincan_dark_09_cyberspace_board.png",
    "tincan_dark_10_comms_webrtc_call.png",
    "tincan_dark_11_watchparty_token_vault.png",
    "tincan_dark_12_system_mobile_car_suite.png",
)


def test_figcraft_dark_mode_system_bundle_and_13_png_exports_exist() -> None:
    fig_path = os.path.join(DESIGNS_DIR, "tincan_dark_mode_system.figcraft")
    assert os.path.isfile(fig_path), f"Missing {fig_path}"
    assert os.path.getsize(fig_path) > 50_000

    with zipfile.ZipFile(fig_path, "r") as zf:
        names = zf.namelist()
        assert "document.json" in names
        assert "thumbnail.png" in names
        raw_doc = zf.read("document.json").decode("utf-8")
        doc = json.loads(raw_doc)

    # Pure monochrome verification: zero green hex codes in document.json
    raw_doc_lower = raw_doc.lower()
    for banned_hex in BANNED_GREEN_HEX_CODES:
        assert banned_hex not in raw_doc_lower, (
            f"Found banned green hex code {banned_hex} in tincan_dark_mode_system.figcraft document.json"
        )
    assert "#000000" in raw_doc_lower
    assert "#ffffff" in raw_doc_lower

    assert doc["format"] == "figcraft"
    nodes = doc["nodes"]
    assert len(nodes) >= 1800

    page = nodes["1"]
    top_frames = [nodes[str(cid)] for cid in page["children"] if nodes[str(cid)].get("type") == "frame"]
    assert len(top_frames) == 12

    expected_prefixes = [f"{i:02d} ·" for i in range(1, 13)]
    actual_names = [f["name"] for f in top_frames]
    for prefix in expected_prefixes:
        assert any(name.startswith(prefix) for name in actual_names), f"Missing artboard starting with {prefix}"

    # Verify pitch-black terminal containers exist across the FigCraft document
    serialized = json.dumps(nodes)
    assert "TinCanShell (.tcsh)" in serialized
    assert "DOCKED WORKSTATION TERMINAL" in serialized
    assert "WebRtcLiveDarkTerminalScreenshare" in serialized
    assert "NODE STUDIO DARK TERMINAL" in serialized
    assert "TOKEN VAULT & WATCH PARTY CLI LEDGER" in serialized

    for png_name in EXPECTED_DARK_PNGS:
        p = os.path.join(DESIGNS_DIR, png_name)
        assert os.path.isfile(p), f"Missing exported Dark Mode PNG: {p}"
        with open(p, "rb") as f:
            sig = f.read(8)
        assert sig == b"\x89PNG\r\n\x1a\n", f"Invalid PNG header in {p}"
        assert os.path.getsize(p) > 100_000, f"Unexpectedly small PNG: {p}"


def test_core_theme_stylesheets_enforce_pitch_black_terminal_and_zero_emerald_greens() -> None:
    core_stylesheets = {
        "SHELL_CSS (shell_component.py)": SHELL_CSS,
        "CELADON_HEAD (window_chrome.py)": CELADON_HEAD,
        "ZEN_HEAD (zen_shell.py)": ZEN_HEAD,
        "INSTALL_CARD_CSS (install_card.py)": INSTALL_CARD_CSS,
    }
    for label, css in core_stylesheets.items():
        low = css.lower()
        assert "#000000" in low, f"{label} must enforce pitch-black #000000 terminal viewport"
        assert "#ffffff" in low, f"{label} must enforce high-contrast #ffffff border/foreground"
        for banned_hex in BANNED_GREEN_HEX_CODES:
            assert banned_hex not in low, f"{label} must contain zero {banned_hex} emerald greens"


def test_tincan_shell_is_pitch_dark_by_default_and_has_theme_command() -> None:
    # .tcsh must be unmistakably dark (#000000 background, #f5f5f5 fg, #ffffff border, #ffffff prompt)
    assert "background: #000000" in SHELL_CSS
    assert "color: #f5f5f5" in SHELL_CSS
    assert "border: 1.5px solid #ffffff" in SHELL_CSS
    assert ".tcsh-ps { font-weight: 700; color: #ffffff; }" in SHELL_CSS
    assert ".tcsh-dots" in SHELL_CSS
    assert "verb === 'theme'" in SHELL_JS
    assert 'data-tc-theme-toggle="1"' in SHELL_JS


def test_window_chrome_and_zen_shell_dark_mode_and_theme_controller() -> None:
    tb = render_titlebar("win-terminal", "Terminal", badge="TINCAN")
    assert "tc-ctl--theme" in tb
    assert 'data-tc-theme-toggle="1"' in tb

    assert 'html[data-theme="dark"]' in CELADON_HEAD
    assert "body.tc-dark" in CELADON_HEAD
    assert 'html[data-theme="dark"]' in ZEN_HEAD
    assert "body.tc-dark" in ZEN_HEAD
    assert 'html[data-theme="dark"]' in INSTALL_CARD_CSS
    assert "body.tc-dark" in INSTALL_CARD_CSS
    assert "window.TinCanTheme" in CELADON_BODY_JS
    assert "tincan:theme-changed" in CELADON_BODY_JS

    assert "window.TinCanTheme" in MESH_OS_HTML_UI
    assert 'id="zenThemeToggleBtn"' in MESH_OS_HTML_UI
    assert "background: #000000 !important" in MESH_OS_HTML_UI


def test_node_studio_and_designs_gallery_dark_mode_integration() -> None:
    ns_html = render_node_studio_html()
    assert 'html[data-theme="dark"]' in ns_html
    assert "--ns-bg: #080808;" in ns_html

    assert len(DARK_MODE_MOCKUPS) == 13
    gallery_html = render_designs_gallery_html("dark-mode")
    assert 'id="tab-dark-mode" class="tab-section active"' in gallery_html
    assert "06 · Dark Mode &amp; Dark Terminal (13)" in gallery_html
    assert "/assets/designs/tincan_dark_mode_system.figcraft" in gallery_html
    for png_name in EXPECTED_DARK_PNGS:
        assert f"/assets/designs/{png_name}" in gallery_html


def test_all_13_ui_modules_enforce_dark_mode_rules_and_pitch_black_terminal_styles() -> None:
    ui_surfaces = {
        "ai_home_shell.py": AI_HOME_SHELL_CSS + render_ai_home_hub_html(),
        "copilot_ui.py": COPILOT_CSS + render_copilot_window_html(),
        "workstation_ui.py": render_workstation_window_html(),
        "node_studio_ui.py": render_node_studio_html() + render_node_studio_window_html(),
        "arena_duel_ui.py": ARENA_DUEL_RESPONSIVE_CSS + render_arena_duel("arena"),
        "cyberspace_board.py": CYBERSPACE_BOARD_DARK_CSS,
        "token_vault_ui.py": TOKEN_VAULT_CSS + render_token_vault_window_html(),
        "mesh_os_ui.py": MESH_OS_HTML_UI,
        "browser_ui.py": render_browser_window_html(),
        "localhost_ui.py": render_localhost_window_html(),
        "ios_preview.py": render_ios_simulator_html(),
        "car_ui.py": render_car_headunit_html(),
        "designs_gallery.py": render_designs_gallery_html("dark-mode"),
    }

    for module_name, surface_html in ui_surfaces.items():
        low = surface_html.lower()
        assert 'html[data-theme="dark"]' in surface_html, (
            f"{module_name} is missing html[data-theme=\"dark\"] Dark Mode overrides"
        )
        assert "body.tc-dark" in surface_html, (
            f"{module_name} is missing body.tc-dark Dark Mode overrides"
        )
        assert "#000000" in low, (
            f"{module_name} is missing pitch-black #000000 terminal/console styles"
        )
        assert "#ffffff" in low, (
            f"{module_name} is missing high-contrast #ffffff monochrome border/accent rules"
        )
        if module_name != "mesh_os_ui.py":
            for banned_hex in BANNED_GREEN_HEX_CODES:
                assert banned_hex not in low, (
                    f"{module_name} contains banned green hex code {banned_hex}"
                )

