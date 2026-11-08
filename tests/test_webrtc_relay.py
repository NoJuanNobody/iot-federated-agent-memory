from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay

def test_webrtc_signaling_and_peer_registration():
    relay = WebRTCSignalingRelay()
    peer_a = relay.register_peer("mac-studio-01", "Studio Host", "192.168.1.100", 50004)
    peer_b = relay.register_peer("macbook-laptop-02", "Remote Peer", "192.168.1.105", 50006)

    assert len(relay.get_active_streams()) == 2

    signal = relay.exchange_signal(
        sender_id=peer_a.peer_id,
        receiver_id=peer_b.peer_id,
        signal_type="offer",
        sdp_or_candidate={"sdp": "v=0\r\no=- 0 0 IN IP4 127.0.0.1...", "codec": "H264"}
    )
    assert signal["type"] == "offer"
    assert signal["to"] == "macbook-laptop-02"
    assert signal["payload"]["codec"] == "H264"
