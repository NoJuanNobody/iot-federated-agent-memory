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
    STORYBOARD_MOCKUPS,
    DESKTOP_MOCKUPS,
)


def test_designs_gallery_html_structure():
    html = render_designs_gallery_html()
    assert "<!DOCTYPE html>" in html
    assert "TinCan 2.2 Design Systems" in html
    assert "Native iOS App" in html
    assert "Car Head-Unit UI" in html
    assert "Zen Narrative Storyboard" in html
    assert "Zen Desktop Windows" in html

    # Verify mockup counts
    assert len(IOS_MOCKUPS) == 11
    assert len(CAR_MOCKUPS) == 5
    assert len(STORYBOARD_MOCKUPS) == 7
    assert len(DESKTOP_MOCKUPS) == 3

    # Check key mockups are referenced
    assert "01-onboarding.png" in html
    assert "sumi-dock-driving.png" in html
    assert "zen_storyboard_contact_sheet.png" in html
    assert "tincan_zen_windows_contact_sheet.png" in html


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

    # Test /storyboard
    with urllib.request.urlopen(f"{running_test_server}/storyboard") as resp:
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]

    # Test static file serving: /docs/designs/ios-app/01-onboarding.png
    with urllib.request.urlopen(f"{running_test_server}/docs/designs/ios-app/01-onboarding.png") as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "image/png"
        assert len(resp.read()) > 1000
