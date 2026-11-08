from iot_federated_agent_memory.ansi import Canvas, rgb_to_256
from iot_federated_agent_memory.logo import LogoImage, draw_title, load_logo, resample, title_width
from iot_federated_agent_memory.tui import App, Dashboard, Screensaver, status_summary

FAKE_STATUS = {
    "data": {
        "status": "online",
        "readiness_tier": "L3: Test Tier",
        "composite_score": 64.5,
        "active_webrtc_streams": [
            {"peer_id": "peer-a", "display_name": "Peer A", "udp_address": "10.0.0.1", "udp_port": 50004,
             "connected_at": 1794150890.0, "active_stream": True},
        ],
        "ai_providers": {"claude-brain": 100.0, "grok-brain": 50.0},
    },
    "error": None,
    "updated_at": 1794150900.0,
    "fetching": False,
}


def _text(canvas):
    return "\n".join("".join(row) for row in canvas.ch)


def test_logo_asset_loads_real_artwork():
    px = load_logo()
    assert (len(px[0]), len(px)) == (110, 119)
    # The eyes of the artwork are glowing green: some pixels must be strongly green.
    assert any(g > 180 and g > r + 60 for row in px for (r, g, b) in row)


def test_resample_and_fit():
    small = resample(load_logo(), 22, 24)
    assert len(small) == 24 and len(small[0]) == 22
    logo = LogoImage.fit(40, 20)
    assert logo.width <= 40 and logo.cell_rows <= 20 and logo.height % 2 == 0


def test_logo_draw_uses_half_blocks_and_animates():
    logo = LogoImage(30, 32)
    c = Canvas(40, 20)
    logo.draw(c, 0, 0, t=0.0)
    assert c.ch[5][5] == "\u2580"
    eye = [(x, y) for y in range(logo.height) for x in range(logo.width) if logo.glow[y][x] == 2]
    assert eye, "expected glowing-eye pixels"
    x, y = eye[0]
    assert logo.color_at(x, y, None) == logo.pixels[y][x]
    assert logo.color_at(x, y, 0.46) != logo.color_at(x, y, 1.38)  # pulses


def test_title_font():
    c = Canvas(80, 4)
    draw_title(c, 0, 0, "THE AI MESSIAH")
    assert title_width("THE AI MESSIAH") <= 80
    assert any(ch in ("\u2580", "\u2584") for row in c.ch for ch in row)


def test_screensaver_and_dashboard_render():
    saver = Screensaver()
    c = Canvas(120, 45)
    saver.draw(c, 0.5, FAKE_STATUS, "[q] quit")
    assert "C O N S U L T I N G" in _text(c)
    assert "relay online" in _text(c)

    dash = Dashboard()
    c = Canvas(120, 40)
    dash.draw(c, 0.5, FAKE_STATUS, "http://relay", idle_left=30)
    text = _text(c)
    assert "Peer A" in text and "claude-brain" in text and "L3: Test Tier" in text


def test_offline_status_and_render_modes():
    label, _ = status_summary({"data": None, "error": "timed out"})
    assert label == "relay offline"
    app = App("http://127.0.0.1:9", "dashboard", 0, None, "256", False)
    frame = app.frame(100, 30, 0.0, None).render("256")
    assert "\x1b[" in frame and "38;2" not in frame
    assert 16 <= rgb_to_256((255, 214, 90)) <= 255
