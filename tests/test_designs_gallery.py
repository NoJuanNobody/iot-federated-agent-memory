"""Tests for the updated Mockups & Designs showcase gallery and static asset routes."""

import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest
import server
from iot_federated_agent_memory.designs_gallery import (
    render_designs_gallery_html,
    IOS_MOCKUPS,
    CAR_MOCKUPS,
    DESKTOP_MOCKUPS,
    TERMINAL_AI_MOCKUPS,
)


def test_designs_gallery_html_structure():
    html = render_designs_gallery_html()
    assert "<!DOCTYPE html>" in html
    assert "TinCan 2.2 Design Systems" in html
    assert "Native iOS App" in html
    assert "Car Head-Unit UI" in html
    assert "Zen Narrative Storyboard" not in html
    assert "/storyboard" not in html
    assert "Zen Desktop Windows" in html

    # Verify mockup counts
    assert len(IOS_MOCKUPS) == 11
    assert len(CAR_MOCKUPS) == 5
    assert len(DESKTOP_MOCKUPS) == 6
    assert len(TERMINAL_AI_MOCKUPS) == 5
    assert "04 · Mesh OS Windows (6)" in html
    assert "05 · Terminal AI Redesign (5)" in html

    # Check key mockups are referenced
    assert "01-onboarding.png" in html
    assert "sumi-dock-driving.png" in html
    assert "tincan_zen_windows_contact_sheet.png" in html

    # Check Terminal AI Redesign mockups and routes
    expected_terminal_ai_imgs = (
        "/assets/designs/tincan_terminal_ai_sheet.png",
        "/assets/designs/tincan_terminal_01_home.png",
        "/assets/designs/tincan_terminal_02_copilot.png",
        "/assets/designs/tincan_terminal_03_arena.png",
        "/assets/designs/tincan_terminal_04_tokens.png",
    )
    for img_path in expected_terminal_ai_imgs:
        assert img_path in html
    for route in ("/", "/copilot", "/arena", "/tokens"):
        assert f'href="{route}"' in html

    tab_html = render_designs_gallery_html("terminal-ai")
    assert 'id="tab-terminal-ai" class="tab-section active"' in tab_html

    # Check Workstation FigCraft designs are registered and linked cleanly
    desktop_ids = {m["id"] for m in DESKTOP_MOCKUPS}
    assert {"ws-studio", "ws-stories", "ws-dual"}.issubset(desktop_ids)
    assert "Workstation · Multi-Model & 3D Studio" in html
    assert "Workstation · 4 User Story Workflows" in html
    assert "Space + Workstation Dual Zen Desktop" in html
    assert "/assets/designs/workstation_studio_design.png" in html
    assert "/assets/designs/workstation_user_stories.png" in html
    assert "/assets/designs/workstation_dual_space_desktop.png" in html
    assert '<a href="/workstation" class="btn-sm primary">Open Workstation</a>' in html


def test_workstation_design_assets_exist():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "designs")
    expected_files = (
        "tincan_workstation_designs.figcraft",
        "workstation_studio_design.png",
        "workstation_user_stories.png",
        "workstation_dual_space_desktop.png",
        "tincan_terminal_ai_sheet.png",
        "tincan_terminal_01_home.png",
        "tincan_terminal_02_copilot.png",
        "tincan_terminal_03_arena.png",
        "tincan_terminal_04_tokens.png",
    )
    for fname in expected_files:
        fpath = os.path.join(assets_dir, fname)
        assert os.path.isfile(fpath), f"Missing design asset: {fpath}"
        assert os.path.getsize(fpath) > 0, f"Empty design asset: {fpath}"


@pytest.fixture
def running_test_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def test_server_designs_routes(running_test_server):
    # Test /designs
    with urllib.request.urlopen(f"{running_test_server}/designs") as resp:
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]
        body = resp.read().decode("utf-8")
        assert "TinCan 2.2 Design Systems" in body

    # Test /mockups
    with urllib.request.urlopen(f"{running_test_server}/mockups") as resp:
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]

    # The storyboard UI page has been removed from the app.
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{running_test_server}/storyboard")
    assert exc.value.code == 404

    # Test /fono
    with urllib.request.urlopen(f"{running_test_server}/fono") as resp:
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]
        body = resp.read().decode("utf-8")
        assert "Aeonik Fono" in body

    # Test static file serving: /docs/designs/aeonik-terminal.png and Workstation assets
    with urllib.request.urlopen(f"{running_test_server}/docs/designs/aeonik-terminal.png") as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "image/png"
        assert len(resp.read()) > 1000

    for fname in (
        "workstation_studio_design.png",
        "workstation_user_stories.png",
        "workstation_dual_space_desktop.png",
        "tincan_terminal_ai_sheet.png",
        "tincan_terminal_01_home.png",
        "tincan_terminal_02_copilot.png",
        "tincan_terminal_03_arena.png",
        "tincan_terminal_04_tokens.png",
    ):
        with urllib.request.urlopen(f"{running_test_server}/assets/designs/{fname}") as resp:
            assert resp.status == 200
            assert resp.headers["Content-Type"] == "image/png"
            assert len(resp.read()) > 1000

    # Test /install.command launcher download
    with urllib.request.urlopen(f"{running_test_server}/install.command") as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "application/octet-stream"
        assert 'filename="Install-TinCan.command"' in (resp.headers.get("Content-Disposition") or "")
        script_body = resp.read().decode("utf-8")
        assert "tincan" in script_body
        assert "Press [Enter] to launch tincan" in script_body
