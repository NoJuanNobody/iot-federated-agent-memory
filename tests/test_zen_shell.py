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
