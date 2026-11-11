from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.tincan_voice import speak_text
from iot_federated_agent_memory.tincan_cli import main as cli_main


def test_webrtc_signaling_and_peer_registration():
    relay = WebRTCSignalingRelay()
    peer_a = relay.register_peer("mac-studio-01", "Studio Host", "192.168.1.100", 50004)
    peer_b = relay.register_peer("macbook-laptop-02", "Remote Peer", "192.168.1.105", 50006)

    assert len(relay.get_active_streams()) == 2

    signal = relay.exchange_signal(
        sender_id=peer_a.peer_id,
        receiver_id=peer_b.peer_id,
        signal_type="offer",
        sdp_or_candidate={"sdp": "v=0\r\no=- 0 0 IN IP4 127.0.0.1...", "codec": "H264"},
    )
    assert signal["type"] == "offer"
    assert signal["to"] == "macbook-laptop-02"
    assert signal["payload"]["codec"] == "H264"

    # Poll signals for peer_b
    polled = relay.poll_signals(receiver_id="macbook-laptop-02", room="main", since_seq=0)
    assert len(polled["signals"]) == 1
    assert polled["signals"][0]["seq"] == signal["seq"]
    assert len(polled["peers"]) == 2

    # Leave room
    assert relay.leave_peer("mac-studio-01") is True
    assert len(relay.get_active_streams()) == 1


def test_privacy_and_peripheral_consent_defaults():
    """Verify IP addresses are redacted and peripherals (cam, mic, screen) default to OFF."""
    relay = WebRTCSignalingRelay()
    session = relay.register_peer("anon-peer-01", "Anonymous Peer", "203.0.113.42", 50004)
    assert session.udp_address == "redacted"
    assert session.has_video is False
    assert session.has_audio is False
    assert session.has_screen is False
    streams = relay.get_active_streams()
    assert streams[0]["udp_address"] == "redacted"


def test_tincan_voice_speak_text(monkeypatch):
    monkeypatch.setattr("iot_federated_agent_memory.tincan_voice.find_tts_binary", lambda: "/usr/local/bin/kokoro-say")
    called = []

    def fake_run(cmd, **kwargs):
        called.append(cmd)

    monkeypatch.setattr("subprocess.run", fake_run)
    res = speak_text("Testing voice synthesis", voice="bella", background=True)
    assert res["status"] == "spoken"
    assert res["engine"] == "kokoro-say"
    assert "--bg" in called[0]
    assert "bella" in called[0]


def test_tincan_cli_say_and_call(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "iot_federated_agent_memory.tincan_voice.speak_text",
        lambda text, voice=None, background=True: {"status": "spoken", "engine": "kokoro-say", "text": text},
    )
    rc = cli_main(["--dir", str(tmp_path), "say", "Hello from TinCan voice", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kokoro-say" in out

    rc_call = cli_main(["--dir", str(tmp_path), "--relay", "http://127.0.0.1:9", "call", "--room", "lab-room", "--no-browser", "--json"])
    assert rc_call == 0
    out_call = capsys.readouterr().out
    assert "lab-room" in out_call
    assert "call_ready" in out_call


def test_relay_video_playlist_collection():
    from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist

    pl = RelayVideoPlaylist()
    state = pl.get_playlist()
    default_total = len(RelayVideoPlaylist.DEFAULT_COLLECTION)
    assert state["total"] == default_total
    assert state["videos"][0]["video_id"] == "7705677376465767711"
    assert state["videos"][0]["creator"] == "@nojuannobody"

    # Add an extra video via raw blockquote embed snippet
    snippet = '<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@nojuannobody/video/7705677376465767799" data-video-id="7705677376465767799"></blockquote>'
    added = pl.add_video(snippet, title="Part 2 Walkthrough", category="ad", auto_download=False)
    assert added["video_id"] == "7705677376465767799"
    assert added["embed_url"] == "/videos/7705677376465767799.mp4"
    assert pl.get_playlist()["total"] == default_total + 1

    # Remove the extra video
    assert pl.remove_video("7705677376465767799") is True
    assert pl.get_playlist()["total"] == default_total


def test_tincan_cli_disconnect(tmp_path, monkeypatch, capsys):
    called_requests = []

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            import json
            return json.dumps({"status": "left", "peer_id": "test-peer-123", "removed": True}).encode()

    def fake_urlopen(req, timeout=None):
        called_requests.append(req)
        return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    rc = cli_main(["--dir", str(tmp_path), "disconnect", "test-peer-123", "--room", "test-room", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-peer-123" in out
    assert '"removed": true' in out
    assert len(called_requests) == 1
    assert "/api/webrtc/leave" in called_requests[0].full_url


def test_tincan_cli_broadcast(tmp_path, monkeypatch, capsys):
    called_requests = []

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            import json
            return json.dumps({
                "status": "signaled",
                "signal": {"type": "chat", "room": "main", "payload": {"text": "Hello mesh!"}}
            }).encode()

    def fake_urlopen(req, timeout=None):
        called_requests.append(req)
        return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    rc = cli_main(["--dir", str(tmp_path), "msg", "Hello mesh!", "--room", "main", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Hello mesh!" in out
    assert '"status": "signaled"' in out
    assert len(called_requests) == 1
    assert "/api/webrtc/signal" in called_requests[0].full_url
