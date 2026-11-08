"""Tests for MQTT/Matter broker telemetry adapter and HMAC vending paywall deduction."""

import json
import pytest
from iot_federated_agent_memory.edge_telemetry import (
    EdgeTelemetryIngestor,
    SensorTelemetryPacket,
    MQTTTelemetryClientAdapter,
    HMACVendingMachine,
    CreditExhaustionError,
    InsufficientBalanceError,
    mqtt_topic_match,
)


def test_mqtt_topic_matching():
    # Exact match
    assert mqtt_topic_match("devices/esp32/telemetry", "devices/esp32/telemetry")
    assert not mqtt_topic_match("devices/esp32/telemetry", "devices/esp32/status")

    # Single-level '+' wildcard
    assert mqtt_topic_match("devices/+/telemetry", "devices/esp32/telemetry")
    assert mqtt_topic_match("devices/+/telemetry", "devices/jetson-02/telemetry")
    assert not mqtt_topic_match("devices/+/telemetry", "devices/esp32/sensor1/telemetry")
    assert not mqtt_topic_match("+/telemetry", "devices/esp32/telemetry")
    assert mqtt_topic_match("+/telemetry", "devices/telemetry")

    # Multi-level '#' wildcard
    assert mqtt_topic_match("devices/#", "devices/esp32")
    assert mqtt_topic_match("devices/#", "devices/esp32/telemetry")
    assert mqtt_topic_match("devices/#", "devices/esp32/cabin/sensor/temp")
    assert mqtt_topic_match("#", "any/arbitrary/mqtt/topic")
    assert not mqtt_topic_match("devices/#", "home/devices/esp32")


def test_adapter_subscription_and_filtering():
    ingestor = EdgeTelemetryIngestor()
    adapter = MQTTTelemetryClientAdapter(ingestor=ingestor, batch_size=5)

    dispatched = []
    def custom_handler(topic, pkt):
        dispatched.append((topic, pkt.metric_name))

    adapter.subscribe("devices/+/telemetry", handler=custom_handler)

    # Ignored topic
    ignored = adapter.receive_message("alerts/critical", json.dumps({"metric_name": "fire", "value": 1, "unit": "bool"}))
    assert ignored is None
    assert len(adapter.pending_batch) == 0
    assert len(dispatched) == 0

    # Matching topic
    payload = {"device_id": "esp32-01", "metric_name": "temp_c", "value": 24.5, "unit": "C"}
    pkt = adapter.receive_message("devices/esp32-01/telemetry", json.dumps(payload))
    assert pkt is not None
    assert pkt.metric_name == "temp_c"
    assert len(adapter.pending_batch) == 1
    assert len(dispatched) == 1
    assert dispatched[0] == ("devices/esp32-01/telemetry", "temp_c")

    # Unsubscribe
    adapter.unsubscribe("devices/+/telemetry")
    assert not adapter.is_subscribed_to("devices/esp32-01/telemetry")


def test_telemetry_payload_parsing_and_validation():
    adapter = MQTTTelemetryClientAdapter()

    # Valid JSON string
    p1 = adapter.parse_and_validate("devices/test", json.dumps({
        "device_id": "sensor-1",
        "metric_name": "lux",
        "value": 450.0,
        "unit": "lx"
    }))
    assert p1.device_id == "sensor-1"
    assert p1.value == 450.0

    # Valid bytes
    raw_bytes = json.dumps({
        "device_id": "sensor-2",
        "metric": "pressure_hpa",
        "value": 1013.25,
        "unit": "hPa"
    }).encode("utf-8")
    p2 = adapter.parse_and_validate("devices/test", raw_bytes)
    assert p2.metric_name == "pressure_hpa"

    # Infer device_id from topic
    p3 = adapter.parse_and_validate("devices/edge-rpi-4/telemetry", {
        "metric_name": "cpu_temp",
        "value": 52.3,
        "unit": "C"
    })
    assert p3.device_id == "edge-rpi-4"

    # Infer matter protocol from topic
    p4 = adapter.parse_and_validate("matter/lightbulb/telemetry", {
        "device_id": "matter-bulb-01",
        "metric_name": "brightness",
        "value": 85,
        "unit": "%"
    })
    assert p4.protocol == "matter"

    # Validation errors: missing metric
    with pytest.raises(ValueError, match="metric_name"):
        adapter.parse_and_validate("devices/test", {"device_id": "s1", "value": 10, "unit": "V"})

    # Validation errors: non-numeric value
    with pytest.raises(ValueError, match="numeric"):
        adapter.parse_and_validate("devices/test", {"device_id": "s1", "metric_name": "volts", "value": "high", "unit": "V"})

    # Validation errors: missing unit
    with pytest.raises(ValueError, match="unit"):
        adapter.parse_and_validate("devices/test", {"device_id": "s1", "metric_name": "volts", "value": 12.0})


def test_adapter_batching_and_ingestion():
    ingestor = EdgeTelemetryIngestor()
    adapter = MQTTTelemetryClientAdapter(ingestor=ingestor, batch_size=3)

    # Feed 2 packets - buffer does not flush yet
    adapter.receive_message("devices/node-a/telemetry", {"metric_name": "m1", "value": 1.0, "unit": "u"})
    adapter.receive_message("devices/node-a/telemetry", {"metric_name": "m2", "value": 2.0, "unit": "u"})
    assert len(adapter.pending_batch) == 2
    assert len(ingestor.buffer) == 0

    # 3rd packet hits batch_size=3 -> automatic flush
    adapter.receive_message("devices/node-a/telemetry", {"metric_name": "m3", "value": 3.0, "unit": "u"})
    assert len(adapter.pending_batch) == 0
    assert len(ingestor.buffer) == 3
    assert ingestor.buffer[0]["title"] == "telemetry_node-a_m1"
    assert ingestor.buffer[2]["title"] == "telemetry_node-a_m3"


def test_hmac_vending_paywall_deduction():
    vending = HMACVendingMachine(secret_key="my-secret-key-123", cost_per_batch=0.05)
    wallet_id = "wallet-faustudent-z23961745"
    vending.mint_credits(wallet_id, 0.15)
    assert vending.get_balance(wallet_id) == 0.15

    ingestor = EdgeTelemetryIngestor()
    adapter = MQTTTelemetryClientAdapter(
        ingestor=ingestor,
        wallet_id=wallet_id,
        vending_machine=vending,
        batch_size=2,
    )

    # 1st batch of 2 items -> $0.05 deducted
    adapter.receive_message("devices/node-1/telemetry", {"metric_name": "temp", "value": 21.0, "unit": "C"})
    adapter.receive_message("devices/node-1/telemetry", {"metric_name": "humidity", "value": 55.0, "unit": "%"})

    assert vending.get_balance(wallet_id) == 0.10
    assert len(adapter.receipts) == 1
    receipt = adapter.receipts[0]
    assert receipt.cost_usd == 0.05
    assert receipt.remaining_balance_usd == 0.10
    assert vending.verify_receipt(receipt) is True

    # 2nd batch of 2 items -> $0.05 deducted
    adapter.receive_message("devices/node-1/telemetry", {"metric_name": "temp", "value": 21.5, "unit": "C"})
    adapter.receive_message("devices/node-1/telemetry", {"metric_name": "humidity", "value": 54.8, "unit": "%"})

    assert vending.get_balance(wallet_id) == 0.05
    assert len(adapter.receipts) == 2
    assert vending.verify_receipt(adapter.receipts[1]) is True


def test_credit_exhaustion_safety_check():
    vending = HMACVendingMachine(cost_per_batch=0.05)
    wallet_id = "low-balance-wallet"
    vending.mint_credits(wallet_id, 0.02)  # Less than $0.05

    ingestor = EdgeTelemetryIngestor()
    adapter = MQTTTelemetryClientAdapter(
        ingestor=ingestor,
        wallet_id=wallet_id,
        vending_machine=vending,
        batch_size=2,
    )

    # 1st packet buffers safely
    adapter.receive_message("devices/s1/telemetry", {"metric_name": "val", "value": 1.0, "unit": "u"})
    assert len(adapter.pending_batch) == 1

    # 2nd packet hits batch_size=2 -> triggers flush -> CreditExhaustionError
    with pytest.raises(CreditExhaustionError) as exc_info:
        adapter.receive_message("devices/s1/telemetry", {"metric_name": "val", "value": 2.0, "unit": "u"})
    assert "Credit exhaustion" in str(exc_info.value)

    # Balance remains untouched and items remain safe in pending batch
    assert vending.get_balance(wallet_id) == 0.02
    assert len(adapter.pending_batch) == 2
    assert len(ingestor.buffer) == 0

    # Top up wallet
    vending.mint_credits(wallet_id, 0.50)
    assert vending.get_balance(wallet_id) == 0.52

    # Flush batch now succeeds
    nodes = adapter.flush_batch()
    assert len(nodes) == 2
    assert len(ingestor.buffer) == 2
    assert vending.get_balance(wallet_id) == 0.47


def test_paywall_callback_hook():
    callback_batches = []
    def on_batch(packets):
        callback_batches.append(list(packets))

    adapter = MQTTTelemetryClientAdapter(batch_size=2, paywall_callback=on_batch)
    adapter.receive_message("devices/d1/telemetry", {"metric_name": "flow", "value": 3.4, "unit": "lpm"})
    adapter.receive_message("devices/d1/telemetry", {"metric_name": "flow", "value": 3.6, "unit": "lpm"})

    assert len(callback_batches) == 1
    assert len(callback_batches[0]) == 2
    assert callback_batches[0][0].metric_name == "flow"


def test_tampered_receipt_fails_verification():
    vending = HMACVendingMachine(secret_key="secret-key", cost_per_batch=0.05)
    vending.mint_credits("wallet-test", 1.00)
    receipt = vending.deduct_batch("wallet-test", "hash123")
    assert vending.verify_receipt(receipt) is True

    # Tamper with cost or signature
    tampered_dict = receipt.to_dict()
    tampered_dict["cost_usd"] = 0.00
    assert vending.verify_receipt(tampered_dict) is False

    tampered_dict = receipt.to_dict()
    tampered_dict["signature"] = "tampered_bad_signature"
    assert vending.verify_receipt(tampered_dict) is False
