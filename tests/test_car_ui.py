"""Tests for the Aftermarket Car Head-Unit UI (1280x720 Sumi-Dock) and /car routes."""

import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.car_ui import CAR_MODES, render_car_headunit_html

# FastAPI TestClient compatibility helper
try:
    from fastapi.testclient import TestClient
except ImportError:
    class TestClient:
        """Lightweight TestClient shim matching FastAPI's TestClient interface."""
        __test__ = False  # Inform pytest this is not a test suite class

        def __init__(self, app):
            self.app = app

        def get(self, url: str, headers: dict = None):
            if hasattr(self.app, "handle"):
                return self.app.handle("GET", url)
            raise RuntimeError("Unsupported app instance")


@pytest.fixture(scope="module")
def car_http_server():
    """Spin up an ephemeral live ThreadingHTTPServer on an open port."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def test_render_car_headunit_html_modes():
    """Verify all 4 car modes render valid HTML5 documents with expected structure."""
    assert CAR_MODES == ("driving", "parked", "dashcam", "identity")

    for mode in CAR_MODES:
        html = render_car_headunit_html(mode)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "TinCan OS · Car Head Unit" in html


def test_car_headunit_design_invariants():
    """Check required dimensions, touch targets, colors, noise filter, and safety gating."""
    html = render_car_headunit_html("driving")

    # Dimensions
    assert "1280" in html
    assert "720" in html

    # Minimum touch target floor
    assert "76px" in html

    # Zen shell palette tokens
    assert "--sumi: #0e0d0b" in html
    assert "--sumi-2: #17150f" in html
    assert "--washi: #ece6da" in html
    assert "--kaki: #d0703f" in html
    assert "--rust: #964622" in html
    assert "--moss: #42522e" in html

    # Typography
    assert "Shippori Mincho" in html
    assert "Zen Kaku Gothic New" in html

    # Dirty gradient noise filter
    assert "feTurbulence" in html
    assert 'type="fractalNoise"' in html

    # Client-side mode switching & safety gate enforcement
    assert "switchCarMode" in html
    assert "VEHICLE_STATE" in html
    assert "safetyToast" in html
    assert "Parked-safety gate" in html

    # Dashcam telemetry & live fetch hooks
    assert "REC 1080p60" in html
    assert "/api/tincan/whoami" in html
    assert "/api/mesh/state" in html


def test_fastapi_testclient_car_routes():
    """Verify FastAPI TestClient(app) requests return HTTP 200 across /car routes."""
    client = TestClient(server.app)

    routes = ["/car", "/car/driving", "/car/parked", "/car/dashcam", "/car/identity"]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Expected 200 for {route}, got {response.status_code}"
        assert "<!DOCTYPE html>" in response.text
        assert "1280" in response.text
        assert "720" in response.text


def test_live_http_car_and_ios_routes(car_http_server):
    """Verify live HTTP server handles /car and /ios endpoints with HTTP 200."""
    base_url = car_http_server
    test_paths = [
        "/car",
        "/car/driving",
        "/car/parked",
        "/car/dashcam",
        "/car/identity",
        "/ios",
        "/ios/01-onboarding",
    ]

    for path in test_paths:
        req = urllib.request.Request(f"{base_url}{path}")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"Failed on {path}: status {resp.status}"
            content = resp.read().decode("utf-8")
            assert len(content) > 100
            if path.startswith("/car"):
                assert "--sumi" in content
                assert "76px" in content
