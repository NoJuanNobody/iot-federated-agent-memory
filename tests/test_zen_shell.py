"""Tests for the zen startup shell injection into the Mesh OS UI."""

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.zen_shell import apply_zen_shell


def test_shell_is_injected_once_in_head_and_body():
    html = MESH_OS_HTML_UI
    assert html.count('id="zenStage"') == 1
    assert html.index("zen-boot") < html.index("</head>")
    assert html.index('id="zenStage"') > html.index('id="meshOsDock"')
    assert html.rstrip().endswith("</html>")


def test_apply_is_idempotent_and_tolerates_fragments():
    assert apply_zen_shell(MESH_OS_HTML_UI) == MESH_OS_HTML_UI
    assert apply_zen_shell("<div>no document</div>") == "<div>no document</div>"


def test_classic_routes_and_gate_hooks_are_kept():
    html = MESH_OS_HTML_UI
    # pop-outs, single-window routes and ?classic=1 skip the shell
    for marker in ("q.get('classic') === '1'", "q.get('window')", "'/tv'", "singleWindowParam"):
        assert marker in html
    # registration still gates every tool through the classic check
    assert "requireVerifiedIdentity(what)" in html
    assert "accountSetupModal" in html


def test_feed_has_visible_quick_launch_for_terminal():
    html = MESH_OS_HTML_UI
    assert html.count('id="zenQuick"') == 1
    # every quick-launch target is a real tool window
    for tool_id in ("win-terminal", "win-agentspace", "win-arena"):
        assert f'data-tool="{tool_id}"' in html
        assert f'id="{tool_id}"' in html
    assert 'data-tool="all"' in html


def test_launcher_is_a_command_bar():
    html = MESH_OS_HTML_UI
    # empty-input hint row and placeholder
    assert "Search tools · @ message someone · &gt; run a command · / commands" in html or \
        "Search tools · @ message someone · > run a command · / commands" in html
    assert 'placeholder="Search, @message, > run…"' in html
    # prefix modes are wired
    assert "first === '@'" in html
    assert "first === '>' || first === '$'" in html
    assert "first === '/'" in html
    for cmd in ("/terminal", "/space", "/arena", "/board", "/talk", "/tokens", "/quests", "/help"):
        assert f"cmd: '{cmd}'" in html
    # people come from the existing roster; messages go through the room chat path
    assert "/api/board/roster" in html
    assert "sendChatMessage" in html and "/api/webrtc/signal" in html
    # fallback actions under the tool matches
    for label in ("Send to room", "Ask AI", "Search the board"):
        assert label in html
    assert "/api/chat" in html


def test_command_bar_shell_adapter_and_identity_gate():
    html = MESH_OS_HTML_UI
    assert "window.TinCanShell" in html
    assert "async function legacyShell" in html
    assert "/api/space/exec" in html
    # sending, asking and running all pass the same identity gate as tools
    assert "gated('send messages in the room chat'" in html
    assert "gated('run commands'" in html
    assert "gated('use the AI gateway'" in html
    # user text is rendered with textContent only
    assert ".textContent = t.name" in html
