"""Tests for Mesh OS Zen Interior Design System."""

import pytest
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI


def test_mesh_os_ui_zen_css_variables():
    """Verify Zen Interior CSS variables are defined in :root."""
    html = MESH_OS_HTML_UI
    assert "--sumi: #0e0d0b;" in html
    assert "--sumi-2: #17150f;" in html
    assert "--sumi-card: #201d16;" in html
    assert "--sumi-well: #0a0907;" in html
    assert "--washi: #ece6da;" in html
    assert "--washi-quiet: rgba(236, 230, 218, 0.70);" in html
    assert "--washi-dim: rgba(236, 230, 218, 0.40);" in html
    assert "--line: rgba(236, 230, 218, 0.14);" in html
    assert "--kaki: #d0703f;" in html
    assert "--rust: #964622;" in html
    assert "--moss: #42522e;" in html
    assert "--indigo: #2e365c;" in html
    assert "--mincho: 'Shippori Mincho', serif;" in html
    assert "--gothic: 'Zen Kaku Gothic New', sans-serif;" in html


def test_mesh_os_ui_zen_fonts():
    """Verify Shippori Mincho and Zen Kaku Gothic New Google Fonts are loaded."""
    html = MESH_OS_HTML_UI
    assert "Shippori+Mincho" in html
    assert "Zen+Kaku+Gothic+New" in html


def test_mesh_os_ui_zen_dirt_surface():
    """Verify inline SVG feTurbulence dirty-gradient ambient noise filter is present."""
    html = MESH_OS_HTML_UI
    assert 'id="zenDirtSurface"' in html
    assert 'id="zenDirt"' in html
    assert "<feTurbulence" in html
    assert 'baseFrequency="0.75"' in html


def test_mesh_os_ui_zen_windows_attributes():
    """Verify all 11 windows have data-zen-window="true" attribute."""
    html = MESH_OS_HTML_UI
    expected_windows = [
        "win-terminal",
        "win-tv",
        "win-arena",
        "win-call",
        "win-comms",
        "win-quests",
        "win-moderator",
        "win-billing",
        "win-board",
        "win-network",
        "win-agentspace",
    ]
    for win_id in expected_windows:
        assert f'id="{win_id}"' in html, f"Window {win_id} missing from HTML"
        snippet = html[html.find(f'id="{win_id}"') : html.find(f'id="{win_id}"') + 150]
        assert 'data-zen-window="true"' in snippet, f"Window {win_id} missing data-zen-window attribute: {snippet}"


def test_mesh_os_ui_zen_modal():
    """Verify accountSetupModal has data-zen-modal="true" attribute."""
    html = MESH_OS_HTML_UI
    assert 'id="accountSetupModal"' in html
    modal_idx = html.find('id="accountSetupModal"')
    snippet = html[modal_idx : modal_idx + 150]
    assert 'data-zen-modal="true"' in snippet


def test_mesh_os_ui_one_click_terminal_installer():
    """Verify One-Click Terminal Installer controls exist via install_card component."""
    html = MESH_OS_HTML_UI
    assert 'data-tc-install=' in html
    assert 'data-role="display"' in html
    assert 'href="/install.command"' in html
    assert 'data-tab="curl"' in html
    assert 'data-action="copy-install"' in html


def test_format_board_mentions_does_not_corrupt_celadon_hex_classes():
    """Verify single-pass formatBoardMentions never re-parses #f4f8f0/#111111 inside span attributes."""
    import json
    import re
    import shutil
    import subprocess

    html = MESH_OS_HTML_UI
    esc_match = re.search(r"function escapeHtml\(str\)\s*\{.*?\n    \}", html, re.DOTALL)
    fmt_match = re.search(r"function formatBoardMentions\(text\)\s*\{.*?\n    \}", html, re.DOTALL)
    assert esc_match and fmt_match, "escapeHtml or formatBoardMentions missing from MESH_OS_HTML_UI"

    node_bin = shutil.which("node")
    assert node_bin, "node binary required to evaluate formatBoardMentions JS"

    sample = (
        "[@claude-brain Synthesis]: Attesting @verifier-agent protocol. "
        "Combining #ed25519 node keys with verified operator forms ensures "
        "sybil-resistant #cyberspace discussions. It's <safe> for @alice!"
    )
    js_program = (
        f"{esc_match.group(0)}\n"
        f"{fmt_match.group(0)}\n"
        f"process.stdout.write(formatBoardMentions({json.dumps(sample)}));\n"
    )
    proc = subprocess.run([node_bin, "-e", js_program], capture_output=True, text=True, check=True)
    rendered = proc.stdout

    assert "quickSearchBoardEntity('#f4f8f0')" not in rendered
    assert "quickSearchBoardEntity('#111111')" not in rendered
    assert "quickSearchBoardEntity('#039')" not in rendered
    assert ">🤖 @claude-brain</span>" in rendered
    assert ">🤖 @verifier-agent</span>" in rendered
    assert ">🪪 @alice</span>" in rendered
    assert ">#ed25519</span>" in rendered
    assert ">#cyberspace</span>" in rendered
    assert "It&#039;s &lt;safe&gt;" in rendered
    assert 'bg-[#f4f8f0]' in rendered
    assert 'text-[#111111]' in rendered
