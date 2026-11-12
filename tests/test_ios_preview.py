"""Tests for the native iOS app interactive simulator & wire bridge."""

import os
from iot_federated_agent_memory.ios_preview import (
    IOS_SCREENS,
    IOS_TABS,
    get_ios_wire_contract,
    render_ios_simulator_html,
)


def test_ios_screens_and_tabs_constants():
    assert len(IOS_SCREENS) == 9
    assert IOS_SCREENS == (
        "01-onboarding",
        "02-inbox",
        "03-thread",
        "04-verify",
        "05-arena",
        "06-call",
        "07-keys",
        "08-relay",
        "09-credits",
    )
    assert len(IOS_TABS) == 4
    assert IOS_TABS == ("inbox", "arena", "calls", "you")


def test_get_ios_wire_contract_structure():
    contract = get_ios_wire_contract()
    assert contract["version"] == "2.2.0"
    assert contract["app_name"] == "TinCan Native iOS"
    assert "default_relay" in contract
    assert contract["screens"] == list(IOS_SCREENS)
    assert contract["tabs"] == list(IOS_TABS)

    endpoints = {ep["path"]: ep for ep in contract["wire_endpoints"]}
    required_paths = [
        "/api/tincan/send",
        "/api/tincan/inbox",
        "/api/tincan/whoami",
        "/api/mesh/arena/battle",
        "/api/mesh/arena/vote",
        "/api/mesh/xp/award",
        "/api/webrtc/register",
        "/api/webrtc/signal",
        "/api/webrtc/signals",
        "/api/webrtc/leave",
        "/api/account/billing",
        "/api/account/billing/topup",
        "/api/version",
    ]
    for path in required_paths:
        assert path in endpoints, f"Missing endpoint {path} in wire contract"
        assert "method" in endpoints[path]
        assert "description" in endpoints[path]


def test_render_ios_simulator_html_zen_tokens_and_screens():
    html = render_ios_simulator_html(initial_screen="02-inbox")
    assert "<!DOCTYPE html>" in html
    assert "TinCan 2.2 · Native iOS Interactive Simulator" in html

    # Zen tokens check
    assert "--sumi: #0e0d0b" in html
    assert "--sumi-2: #17150f" in html
    assert "--washi: #ece6da" in html
    assert "--kaki: #d0703f" in html
    assert "Shippori Mincho" in html
    assert "Zen Kaku Gothic New" in html

    # SVG dirty-gradient washes and feTurbulence filters
    assert "feTurbulence" in html
    assert "dirt-washes" in html

    # All 9 screens must be rendered into the DOM
    for screen in IOS_SCREENS:
        assert f'id="screen-{screen}"' in html, f"Missing container for screen {screen}"
        assert f'data-screen="{screen}"' in html
        assert f'onclick="switchScreen(\'{screen}\')"' in html

    # All 4 tabs must be present in the navigation bar
    for tab in IOS_TABS:
        assert f'data-tab="{tab}"' in html
        assert f'onclick="switchTab(\'{tab}\')"' in html

    # Wire API actions in the console
    for action in ("/api/tincan/whoami", "/api/tincan/inbox", "/api/tincan/send", "/api/mesh/arena/battle", "/api/account/billing"):
        assert action in html


def test_interactive_preview_file_exists_and_valid():
    file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "docs",
            "designs",
            "ios-app",
            "interactive_preview.html",
        )
    )
    assert os.path.isfile(file_path), "interactive_preview.html file does not exist"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert len(content) > 10000
    for screen in IOS_SCREENS:
        assert f'id="screen-{screen}"' in content
        assert f'data-screen="{screen}"' in content
    for tab in IOS_TABS:
        assert f'data-tab="{tab}"' in content
