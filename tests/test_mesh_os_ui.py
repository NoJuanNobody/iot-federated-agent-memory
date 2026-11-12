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
