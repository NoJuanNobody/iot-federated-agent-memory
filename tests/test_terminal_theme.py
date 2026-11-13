"""Tests for the terminal theme: shared window chrome, the shell, the chat room and ad credits."""

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.terminal_theme import apply_terminal_theme


def test_theme_is_injected_once_after_the_zen_shell():
    html = MESH_OS_HTML_UI
    assert html.count('id="tcTheme"') == 1
    assert html.count('id="tcThemeScript"') == 1
    assert html.index('id="tcTheme"') < html.index("</head>")
    # the theme script runs after the zen shell so it can restyle the feed and every window
    assert html.index('id="zenStage"') < html.index('id="tcThemeScript"')
    assert html.rstrip().endswith("</html>")


def test_apply_is_idempotent_and_tolerates_fragments():
    assert apply_terminal_theme(MESH_OS_HTML_UI) == MESH_OS_HTML_UI
    assert apply_terminal_theme("<div>no document</div>") == "<div>no document</div>"


def test_terminal_is_a_working_shell_not_a_mockup():
    html = MESH_OS_HTML_UI
    for el in ('id="tcTermInput"', 'id="tcTermOut"', 'id="curlInstallCmd"'):
        assert el in html
    # the tree and editor panes were removed on purpose; `edit` hands off to the Space window
    assert 'id="tcTermTree"' not in html
    assert 'id="tcEdText"' not in html
    assert "window.tcSpace.open" in html
    # one-click install is still there
    assert 'href="/install.command"' in html
    # commands are backed by the relay's API and the visitor's Space VFS
    for route in ("/api/space/ls", "/api/space/file", "/api/space/exec", "/api/status", "/api/chat"):
        assert route in html
    # the fake cargo/aeonik transcript is gone
    assert "aeonik@studio" not in html
    assert "AEONIK_FILES" not in html


def test_comms_is_a_channel_room():
    html = MESH_OS_HTML_UI
    for el in ('id="tcChanList"', 'id="tcDmList"', 'id="tcOnlineList"', 'id="chatMessagesList"', 'id="chatInput"'):
        assert el in html
    # room messages carry their channel; direct messages go to one peer
    assert "channel: dmPeer ? 'dm' : channel" in html
    assert "to: dmPeer || '*'" in html


def test_ads_credit_passively_in_the_feed_and_watch_party():
    html = MESH_OS_HTML_UI
    assert html.count('id="tcAdCreditsScript"') == 1
    # the tracker is defined in <head>, before the zen feed and the watch party use it
    assert html.index('id="tcAdCreditsScript"') < html.index("</head>")
    assert "window.tcAdCredits.track(video, renderCredits)" in html
    assert "window.tcAdCredits.track(vid," in html
    # it goes through the server-clocked view token flow, never a client-side award
    assert "/api/ads/view/start" in html and "/api/ads/view/complete" in html


def _head(html):
    return html[: html.index("</head>")]


def test_popout_mode_detection_script_is_in_head():
    head = _head(MESH_OS_HTML_UI)
    assert "tc-popout" in head
    assert "window" in head and "classList.add('tc-popout')" in head.replace('"', "'")
    for route in ("/tv", "/call", "/arena", "/terminal", "/billing", "/tokens", "/board", "/cyberspace"):
        assert route in head


def test_popout_css_hides_the_old_desktop():
    html = MESH_OS_HTML_UI
    assert "tc-popout" in html
    for sel in ("#meshOsHud", "#meshOsDock", "#zenStage", "#zenLauncher", "#meshTopologyCanvas"):
        assert sel in html
    assert "html.tc-popout #meshOsHud" in html


def test_header_meta_buttons_present():
    html = MESH_OS_HTML_UI
    for kind in ("account", "peers", "chat"):
        assert f"data-tc-meta=\"{kind}\"" in html or f"'{kind}'" in html and "data-tc-meta" in html
    assert "openPopoutWindow" in html
    assert "window.close()" in html


def test_popout_overrides_fullscreen_class_and_account_chip_forces_modal():
    html = MESH_OS_HTML_UI
    # mesh_os_ui's .popout-fullscreen sets height: calc(100vh - 64px); pop-outs must fill the viewport
    assert "html.tc-popout .mesh-window.popout-fullscreen" in html
    assert "max-height: 100dvh !important" in html
    # the zen shell blocks openAccountModal unless armed; the account chip must still open it
    assert "accountSetupModal" in html and "m.classList.remove('hidden')" in html
