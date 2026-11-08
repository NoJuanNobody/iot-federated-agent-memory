"""Dimension 4: IoT Sensor & Edge Device Telemetry Ingestion (MQTT / CoAP / Matter)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class SensorTelemetryPacket:
    device_id: str
    protocol: str  # "mqtt", "coap", "matter"
    metric_name: str
    value: float
    unit: str
    timestamp: float

    def to_vault_node(self) -> Dict[str, Any]:
        """Convert live IoT telemetry stream packet into an atomic GraphRAG Vault Node."""
        return {
            "title": f"telemetry_{self.device_id}_{self.metric_name}",
            "tags": ["#iot", "#telemetry", f"#{self.protocol}"],
            "frontmatter": {
                "device_id": self.device_id,
                "protocol": self.protocol,
                "metric": self.metric_name,
                "unit": self.unit,
                "recorded_at": self.timestamp,
            },
            "content": f"Sensor {self.device_id} reported {self.metric_name} = {self.value} {self.unit} over {self.protocol.upper()}.",
        }


class EdgeTelemetryIngestor:
    """Ingests MQTT/CoAP/Matter IoT telemetry and publishes atomic nodes to the Vault."""

    def __init__(self, target_vault_dir: Optional[str] = None):
        self.target_vault_dir = target_vault_dir
        self.buffer = []

    def ingest_packet(self, device_id: str, protocol: str, metric_name: str, value: float, unit: str) -> Dict[str, Any]:
        pkt = SensorTelemetryPacket(
            device_id=device_id,
            protocol=protocol.lower(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=time.time(),
        )
        node = pkt.to_vault_node()
        self.buffer.append(node)
        return node
