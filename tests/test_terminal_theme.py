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
    for el in ('id="tcTermInput"', 'id="tcTermOut"', 'id="tcTermTree"', 'id="tcEdText"', 'id="curlInstallCmd"'):
        assert el in html
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
