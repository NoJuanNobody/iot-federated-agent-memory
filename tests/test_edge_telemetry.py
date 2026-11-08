from iot_federated_agent_memory.edge_telemetry import EdgeTelemetryIngestor, SensorTelemetryPacket

def test_sensor_packet_conversion():
    pkt = SensorTelemetryPacket("esp32-cabin-01", "mqtt", "temperature_c", 23.4, "C", 1700000000.0)
    node = pkt.to_vault_node()
    assert node["title"] == "telemetry_esp32-cabin-01_temperature_c"
    assert "#iot" in node["tags"]
    assert node["frontmatter"]["protocol"] == "mqtt"

def test_telemetry_ingestor():
    ingestor = EdgeTelemetryIngestor()
    node = ingestor.ingest_packet("jetson-node-02", "matter", "power_draw_w", 12.8, "W")
    assert len(ingestor.buffer) == 1
    assert "power_draw_w" in node["title"]
