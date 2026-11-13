"""Terminal is just the terminal; Space is the IDE (install_card.py + shell_component.py)."""

import re

from iot_federated_agent_memory.install_card import (
    BREW_SHELL_COMMAND,
    INSTALL_COMMANDS,
    render_install_card,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI as HTML


def _window(win_id: str) -> str:
    """The markup of one top-level mesh window (up to the next window)."""
    start = HTML.index(f'<div id="{win_id}" class="mesh-window')
    nxt = HTML.find('<div id="win-', start + 10)
    return HTML[start:nxt if nxt != -1 else len(HTML)]


def test_install_card_component_renders_the_commands():
    card = render_install_card("demo", shell="#shellHere")
    assert 'data-tc-install="demo"' in card
    assert 'data-shell="#shellHere"' in card
    for key in ("brew", "curl", "npx", "chat"):
        assert f'data-tab="{key}"' in card
        assert f'data-cmd="{key}"' in card
    assert "brew install https://iot-federated-agent-memory-production.up.railway.app/Formula/tincan.rb" in card
    assert "curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash" in card
    assert "npx skills add NoJuanNobody/tincan-skills -g -y" in card
    assert "Copy install command" in card
    assert "/install.command" in card
    assert BREW_SHELL_COMMAND == "brew install tincan context-palace"
    assert set(INSTALL_COMMANDS) == {"brew", "curl", "npx", "chat"}


def test_install_card_ids_do_not_collide_across_mounts():
    a, b = render_install_card("a"), render_install_card("b")
    assert 'id="tcInstallCard-a"' in a and 'id="tcInstallCard-b"' in b
    assert not re.findall(r'\sid="(?!tcInstallCard-)', a)  # nothing else needs a global id


def test_terminal_window_is_install_card_plus_shell_only():
    term = _window("win-terminal")
    assert 'data-tc-install="terminal"' in term
    assert "One-Click Terminal Install" in term
    assert 'id="termShellMount"' in term and "data-tc-shell-mount" in term
    for gone in ("termTree", "termDriveTree", "termStatFiles", "termRunsTable", "aeonikRecentOutput", "RECENT"):
        assert gone not in term
    # shared titlebar is kept
    assert "tc-titlebar" in term and "Pop Out" in term
    assert "/fono" in term


def test_space_window_is_a_vscode_style_ide():
    space = _window("win-agentspace")
    assert "Space · Ranger VFS &amp; Wasm Studio" in space
    # explorer (existing ranger list + places), editor with tabs, integrated terminal, status bar
    assert 'id="rangerListPane"' in space and 'id="spaceFileList"' in space and 'id="drivePlacesList"' in space
    assert 'id="ideTabs"' in space and 'id="agentspaceEditor"' in space
    assert 'id="idePanel"' in space
    assert re.search(r'id="ideTermMount"[^>]*data-tc-shell-mount', space)
    assert 'id="ideStatus"' in space
    # scope switching + owner survive
    for ident in ("scopeUserBtn", "scopeTopicBtn", "scopeDynamicBtn", "spaceOwnerInput"):
        assert f'id="{ident}"' in space
    # no dark navy / neon palette left in the IDE chrome
    assert "bg-slate-950" not in space.split('id="finderTab-vscode"')[0]
    assert "#020617" not in space


def test_tincan_shell_global_api():
    assert "window.TinCanShell = (function" in HTML
    api = HTML[HTML.index("window.TinCanShell = (function"):]
    assert "async function run(line, opts)" in api
    assert "function mount(el, opts)" in api
    assert "return { version: 1, run, mount, instances }" in api
    # one interpreter: both the headless run and the interactive exec call it
    assert api.count("await termInterpret(line, opts)") == 1
    assert api.count("await termInterpret(line, o)") == 1


def test_shell_command_set_and_legacy_wrappers():
    for verb in ("ls", "cat", "tree", "run", "py", "runs", "drive", "status", "ask", "help", "clear", "brew", "open"):
        assert re.search(rf"verb === '{verb}'|cmd === '{verb}'|'{verb}'", HTML), verb
    for legacy in ("function execAeonikShellCommand(", "function clearAeonikShell(", "async function termExec(", "function termScope(", "function termOwner(", "function termPrompt("):
        assert legacy in HTML, legacy
    # old fixed ids are gone: the shell is mountable more than once
    for fixed in ('id="aeonikShellInput"', 'id="termShellTranscript"', 'id="termShellStatusPill"'):
        assert fixed not in HTML


def test_no_unfilled_component_slots():
    assert "/*TC_SHELL_JS*/" not in HTML and "/*TC_SHELL_CSS*/" not in HTML and "/*TC_INSTALL_CARD_JS*/" not in HTML
    assert "<!--TC_INSTALL_CARD" not in HTML
    assert ".tcsh {" in HTML and "window.TinCanInstallCard" in HTML
