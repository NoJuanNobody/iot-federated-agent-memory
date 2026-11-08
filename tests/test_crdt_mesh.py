import time
import pytest
from iot_federated_agent_memory.crdt_mesh import (
    CRDTMeshGossipSync,
    CRDTDeltaMessage,
    FrameIntegrityError,
    MockMeshTransport,
    BLELoRaFrameBufferChannel,
    UDPTransportChannel,
    WebRTCDataChannel,
    HEADER_SIZE,
    FRAME_MAGIC,
)


def test_crdt_local_and_remote_merge():
    node_a = CRDTMeshGossipSync("node-mac-m1")
    node_b = CRDTMeshGossipSync("node-esp32-cabin")

    delta = node_a.apply_local_update("vault_topic_01", {"status": "synced", "value": 42})
    assert delta.clock == 1
    assert len(delta.get_hash()) == 64

    # Merge into node_b
    merged = node_b.merge_remote_delta(delta)
    assert merged is True
    assert node_b.state_store["vault_topic_01"]["value"] == 42
    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()


def test_delta_message_serialization_framing_and_integrity():
    delta = CRDTDeltaMessage(
        node_id="node-test-01",
        clock=5,
        operation="upsert",
        key="sensor_temp",
        value={"temp": 24.5, "unit": "C"},
        timestamp=1700000000.0,
    )

    # Serialize
    frame = delta.serialize()
    assert len(frame) >= HEADER_SIZE
    assert frame[:6] == FRAME_MAGIC

    # Deserialize
    decoded = CRDTDeltaMessage.deserialize(frame)
    assert decoded.node_id == delta.node_id
    assert decoded.clock == delta.clock
    assert decoded.key == delta.key
    assert decoded.value == delta.value
    assert decoded.get_hash() == delta.get_hash()

    # Corrupt payload byte -> CRC32 mismatch
    corrupted_payload = bytearray(frame)
    corrupted_payload[-1] ^= 0xFF
    with pytest.raises(FrameIntegrityError, match="CRC32 checksum mismatch"):
        CRDTDeltaMessage.deserialize(bytes(corrupted_payload))

    # Corrupt magic header
    bad_magic = bytearray(frame)
    bad_magic[0] = ord(b"X")
    with pytest.raises(FrameIntegrityError, match="Invalid frame magic"):
        CRDTDeltaMessage.deserialize(bytes(bad_magic))

    # Truncated frame
    with pytest.raises(FrameIntegrityError, match="less than header size"):
        CRDTDeltaMessage.deserialize(frame[:20])


def test_mesh_transport_channels():
    # 1. MockMeshTransport pair
    chan_a, chan_b = MockMeshTransport.create_pair()
    assert chan_a.is_connected and chan_b.is_connected

    delta = CRDTDeltaMessage("node-a", 1, "upsert", "k1", {"val": 10}, time.time())
    frame = delta.serialize()
    chan_a.send(frame)

    recv = chan_b.receive()
    assert recv == frame
    decoded = CRDTDeltaMessage.deserialize(recv)
    assert decoded.key == "k1"

    # Disconnect
    chan_a.disconnect()
    assert not chan_a.send(frame)
    assert chan_a.receive() is None

    # 2. BLELoRaFrameBufferChannel with segmentation and reassembly
    # Set MTU to 70 bytes so a ~180-byte frame gets split into multiple chunks
    ble_a = BLELoRaFrameBufferChannel(channel_type="ble", mtu=70)
    ble_b = BLELoRaFrameBufferChannel(channel_type="ble", mtu=70)
    ble_a.link_peer(ble_b)

    large_delta = CRDTDeltaMessage(
        "constrained-iot-lora-node",
        12,
        "upsert",
        "long_key_with_nested_payload",
        {"temperature": 23.4, "metadata": "ambient sensor package inside greenhouse #4", "battery": 98.5},
        time.time(),
    )
    large_frame = large_delta.serialize()
    assert len(large_frame) > 150  # Must exceed MTU=70

    sent = ble_a.send(large_frame)
    assert sent is True

    reassembled_frame = ble_b.receive()
    assert reassembled_frame == large_frame
    reassembled_delta = CRDTDeltaMessage.deserialize(reassembled_frame)
    assert reassembled_delta.node_id == "constrained-iot-lora-node"
    assert reassembled_delta.value["battery"] == 98.5

    # 3. WebRTCDataChannel
    rtc_a = WebRTCDataChannel(label="test-rtc")
    rtc_b = WebRTCDataChannel(label="test-rtc")
    rtc_a.link(rtc_b)
    rtc_a.send(frame)
    assert rtc_b.receive() == frame

    # 4. UDPTransportChannel (localhost)
    udp_a = UDPTransportChannel(bind_host="127.0.0.1", bind_port=0)
    udp_b = UDPTransportChannel(bind_host="127.0.0.1", bind_port=0)
    udp_a.set_peer_port(udp_b.bound_port)
    udp_b.set_peer_port(udp_a.bound_port)

    udp_a.send(frame)
    time.sleep(0.01)
    udp_recv = udp_b.receive()
    assert udp_recv == frame
    udp_a.close()
    udp_b.close()


def test_offline_queuing_and_reconnection():
    chan_a, chan_b = MockMeshTransport.create_pair()
    node_a = CRDTMeshGossipSync("node-field-sensor", transport=chan_a)
    node_b = CRDTMeshGossipSync("node-gateway-base", transport=chan_b)

    # Node A goes offline
    node_a.disconnect()
    assert not node_a.is_online
    assert not chan_a.is_connected

    # Node A generates 3 local updates while offline
    node_a.apply_local_update("soil_moisture", {"depth_cm": 10, "moisture_pct": 42.1})
    node_a.apply_local_update("solar_irradiance", {"lux": 75000})
    node_a.apply_local_update("battery_soc", {"pct": 89.2})

    # Deltas buffered in offline queue
    assert len(node_a.offline_queue) == 3
    assert len(node_a.state_store) == 3
    assert len(node_b.state_store) == 0

    # Node A reconnects
    sync_res = node_a.reconnect()
    assert node_a.is_online
    assert chan_a.is_connected
    assert len(node_a.offline_queue) == 0
    assert sync_res.deltas_synced == 3

    # Node B pulls queued frames from transport
    received = node_b.process_incoming_transport()
    assert len(received) == 3
    assert len(node_b.state_store) == 3
    assert node_b.state_store["soil_moisture"]["moisture_pct"] == 42.1

    # Merkle parity verified
    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()


def test_multi_node_mesh_merge_over_transport():
    transports = MockMeshTransport.create_mesh(count=3)
    node_a = CRDTMeshGossipSync("node-alpha", transport=transports[0])
    node_b = CRDTMeshGossipSync("node-beta", transport=transports[1])
    node_c = CRDTMeshGossipSync("node-gamma", transport=transports[2])

    # Each node generates a local update broadcasted to all mesh peers
    node_a.apply_local_update("metric_a", {"value": 100})
    node_b.apply_local_update("metric_b", {"value": 200})
    node_c.apply_local_update("metric_c", {"value": 300})

    # Each node drains transport inbox
    node_a.process_incoming_transport()
    node_b.process_incoming_transport()
    node_c.process_incoming_transport()

    # All nodes have all 3 keys
    assert set(node_a.state_store.keys()) == {"metric_a", "metric_b", "metric_c"}
    assert set(node_b.state_store.keys()) == {"metric_a", "metric_b", "metric_c"}
    assert set(node_c.state_store.keys()) == {"metric_a", "metric_b", "metric_c"}

    # Full Merkle parity across 3-node mesh
    root_a = node_a.compute_merkle_root()
    root_b = node_b.compute_merkle_root()
    root_c = node_c.compute_merkle_root()
    assert root_a == root_b == root_c


def test_merkle_parity_recovery_after_partition():
    node_a = CRDTMeshGossipSync("node-edge-01")
    node_b = CRDTMeshGossipSync("node-edge-02")

    # Initial synchronized state
    d0 = node_a.apply_local_update("cluster_config", {"mode": "federated"})
    node_b.merge_remote_delta(d0)
    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()

    # Network partition: both nodes disconnect
    node_a.disconnect()
    node_b.disconnect()

    # Independent updates while partitioned
    node_a.apply_local_update("sensor_pressure", {"hpa": 1014.2})
    node_a.apply_local_update("device_status", {"state": "active_a"})

    node_b.apply_local_update("sensor_humidity", {"pct": 68.4})
    node_b.apply_local_update("device_status", {"state": "active_b"})

    # Merkle roots diverge
    assert node_a.compute_merkle_root() != node_b.compute_merkle_root()

    # Partition heals and reconnects with peer
    sync_result = node_a.reconnect(peer=node_b)

    assert sync_result.parity_achieved is True
    assert sync_result.local_merkle_root == sync_result.remote_merkle_root
    assert node_a.compute_merkle_root() == node_b.compute_merkle_root()
    assert set(node_a.state_store.keys()) == {
        "cluster_config",
        "sensor_pressure",
        "sensor_humidity",
        "device_status",
    }
