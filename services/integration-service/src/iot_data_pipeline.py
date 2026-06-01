"""IoT Data Pipeline - Ingest MQTT/CoAP/HTTP sensor data, transform, filter, route."""

import asyncio
import json
import logging
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    MQTT = "mqtt"
    COAP = "coap"
    HTTP = "http"


class PipelineStage(Enum):
    INGEST = "ingest"
    PARSE = "parse"
    TRANSFORM = "transform"
    FILTER = "filter"
    ROUTE = "route"
    STORE = "store"


class SinkType(Enum):
    POSTGRESQL = "postgresql"
    INFLUXDB = "influxdb"
    MQTT = "mqtt"
    WEBHOOK = "webhook"
    KAFKA = "kafka"


class SensorReading:
    """A single sensor reading from an IoT device."""

    def __init__(self, device_id: str, sensor: str, value: float,
                 unit: str, timestamp: Optional[datetime] = None):
        self.reading_id = str(uuid.uuid4())
        self.device_id = device_id
        self.sensor = sensor
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or datetime.utcnow()
        self.protocol: Optional[ProtocolType] = None
        self.raw_payload: Optional[dict] = None
        self.tags: dict[str, str] = {}
        self.quality: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "device_id": self.device_id,
            "sensor": self.sensor,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "protocol": self.protocol.value if self.protocol else None,
            "tags": self.tags,
            "quality": self.quality,
        }


class PipelineMessage:
    """A message flowing through the pipeline."""

    def __init__(self, source: str, payload: dict, protocol: ProtocolType):
        self.message_id = str(uuid.uuid4())
        self.source = source
        self.payload = payload
        self.protocol = protocol
        self.received_at = datetime.utcnow()
        self.readings: list[SensorReading] = []
        self.transformed_payload: Optional[dict] = None
        self.routes: list[str] = []
        self.dropped: bool = False
        self.error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "source": self.source,
            "payload": self.payload,
            "protocol": self.protocol.value,
            "received_at": self.received_at.isoformat(),
            "readings_count": len(self.readings),
            "dropped": self.dropped,
            "error": self.error,
        }


class RuleCondition:
    """A condition for the rule engine."""

    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator
        self.value = value

    def evaluate(self, reading: SensorReading) -> bool:
        actual = getattr(reading, self.field, None)
        if actual is None:
            return False
        try:
            if self.operator == ">":
                return float(actual) > float(self.value)
            elif self.operator == "<":
                return float(actual) < float(self.value)
            elif self.operator == ">=":
                return float(actual) >= float(self.value)
            elif self.operator == "<=":
                return float(actual) <= float(self.value)
            elif self.operator == "==":
                return str(actual) == str(self.value)
            elif self.operator == "!=":
                return str(actual) != str(self.value)
            elif self.operator == "in":
                return str(actual) in [str(v) for v in self.value]
            elif self.operator == "between":
                lo, hi = self.value
                return float(lo) <= float(actual) <= float(hi)
        except (ValueError, TypeError):
            return False
        return False


class RuleAction:
    """An action to take when a rule fires."""

    def __init__(self, action_type: str, target: Optional[str] = None,
                 params: Optional[dict] = None):
        self.action_type = action_type  # alert, store, forward, transform, drop
        self.target = target
        self.params = params or {}

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.action_type, "target": self.target, "params": self.params}


class PipelineRule:
    """A rule in the pipeline rule engine."""

    def __init__(self, rule_id: str, name: str, conditions: list[RuleCondition],
                 actions: list[RuleAction], enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.enabled = enabled
        self.priority: int = 100
        self.created_at = datetime.utcnow()
        self.fire_count: int = 0

    def evaluate(self, reading: SensorReading) -> bool:
        if not self.enabled:
            return False
        return all(c.evaluate(reading) for c in self.conditions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "conditions": [{"field": c.field, "operator": c.operator, "value": c.value}
                          for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "priority": self.priority,
            "fire_count": self.fire_count,
        }


class DataSink:
    """A data output sink for the pipeline."""

    def __init__(self, sink_id: str, name: str, sink_type: SinkType,
                 config: dict[str, Any]):
        self.sink_id = sink_id
        self.name = name
        self.sink_type = sink_type
        self.config = config
        self.enabled: bool = True
        self.connected: bool = False
        self.messages_written: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sink_id": self.sink_id,
            "name": self.name,
            "sink_type": self.sink_type.value,
            "config": {k: v for k, v in self.config.items() if k not in ("password", "token")},
            "enabled": self.enabled,
            "connected": self.connected,
            "messages_written": self.messages_written,
        }


class IoTDataPipeline:
    """Main pipeline for IoT data ingestion, transformation, and routing."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.rules: dict[str, PipelineRule] = {}
        self.sinks: dict[str, DataSink] = {}
        self.messages: list[PipelineMessage] = []
        self.readings: list[SensorReading] = []
        self._transformers: dict[str, Callable] = {}
        self._seed_data()

    def _seed_data(self):
        self.sinks["sink-postgres"] = DataSink(
            "sink-postgres", "PostgreSQL Main", SinkType.POSTGRESQL,
            {"host": "localhost", "port": 5432, "database": "iot_data"}
        )
        self.sinks["sink-influxdb"] = DataSink(
            "sink-influxdb", "InfluxDB Metrics", SinkType.INFLUXDB,
            {"url": "http://localhost:8086", "org": "infra-pilot", "bucket": "iot"}
        )
        self.sinks["sink-webhook"] = DataSink(
            "sink-webhook", "Alert Webhook", SinkType.WEBHOOK,
            {"url": "https://hooks.infra-pilot.dev/iot-alerts"}
        )
        self.sinks["sink-kafka"] = DataSink(
            "sink-kafka", "Kafka Stream", SinkType.KAFKA,
            {"brokers": "localhost:9092", "topic": "iot-events"}
        )

        self.add_rule("High Temperature Alert", [
            RuleCondition("value", ">", 85.0),
        ], [RuleAction("alert", "sink-webhook", {"severity": "critical"})])

        self.add_rule("Low Battery Warning", [
            RuleCondition("sensor", "==", "battery"),
            RuleCondition("value", "<", 10.0),
        ], [RuleAction("alert", "sink-webhook", {"severity": "warning"})])

        self.add_rule("Vibration Anomaly", [
            RuleCondition("sensor", "==", "vibration"),
            RuleCondition("value", ">", 5.0),
        ], [RuleAction("store", "sink-influxdb", {"priority": "high"})])

        self.add_rule("Temperature Range Check", [
            RuleCondition("sensor", "==", "temperature"),
            RuleCondition("value", "between", [0, 50]),
        ], [RuleAction("store", "sink-postgres", {})])

        for i in range(50):
            reading = SensorReading(
                f"demo-device-{i % 10:03d}",
                ["temperature", "humidity", "pressure", "vibration", "battery"][i % 5],
                round(20 + (hash(f"demo_{i}") % 60), 1),
                ["°C", "%", "hPa", "mm/s", "%"][i % 5],
                datetime.utcnow() - timedelta(minutes=i * 10)
            )
            reading.protocol = ProtocolType.MQTT
            self.readings.append(reading)

    async def initialize(self):
        logger.info("IoTDataPipeline initialized with %d rules, %d sinks",
                    len(self.rules), len(self.sinks))

    async def close(self):
        logger.info("IoTDataPipeline closed")

    def add_rule(self, name: str, conditions: list[RuleCondition],
                 actions: list[RuleAction], priority: int = 100) -> PipelineRule:
        rule_id = f"rule-{uuid.uuid4().hex[:8]}"
        rule = PipelineRule(rule_id, name, conditions, actions)
        rule.priority = priority
        self.rules[rule_id] = rule
        return rule

    def get_rule(self, rule_id: str) -> Optional[PipelineRule]:
        return self.rules.get(rule_id)

    def list_rules(self, enabled_only: bool = False) -> list[PipelineRule]:
        result = sorted(self.rules.values(), key=lambda r: r.priority)
        if enabled_only:
            result = [r for r in result if r.enabled]
        return result

    def update_rule(self, rule_id: str, updates: dict) -> Optional[PipelineRule]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        if "enabled" in updates:
            rule.enabled = updates["enabled"]
        if "priority" in updates:
            rule.priority = updates["priority"]
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def add_sink(self, name: str, sink_type: SinkType,
                 config: dict[str, Any]) -> DataSink:
        sink_id = f"sink-{uuid.uuid4().hex[:8]}"
        sink = DataSink(sink_id, name, sink_type, config)
        self.sinks[sink_id] = sink
        return sink

    def get_sink(self, sink_id: str) -> Optional[DataSink]:
        return self.sinks.get(sink_id)

    def list_sinks(self) -> list[DataSink]:
        return list(self.sinks.values())

    def delete_sink(self, sink_id: str) -> bool:
        if sink_id in self.sinks:
            del self.sinks[sink_id]
            return True
        return False

    def register_transformer(self, name: str, func: Callable):
        self._transformers[name] = func

    def ingest(self, source: str, payload: dict, protocol: str) -> PipelineMessage:
        try:
            proto = ProtocolType(protocol)
        except ValueError:
            proto = ProtocolType.HTTP
        msg = PipelineMessage(source, payload, proto)
        self.messages.append(msg)

        if len(self.messages) > 10000:
            self.messages = self.messages[-5000:]

        readings = self._parse_payload(source, payload)
        for reading in readings:
            msg.readings.append(reading)
            self._process_reading(reading)
            self.readings.append(reading)

        if len(self.readings) > 100000:
            self.readings = self.readings[-50000:]

        return msg

    def _parse_payload(self, device_id: str, payload: dict) -> list[SensorReading]:
        readings = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, (int, float)):
                    reading = SensorReading(device_id, key, float(value), "unknown")
                    readings.append(reading)
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            reading = SensorReading(device_id, f"{key}_{sub_key}",
                                                    float(sub_value), "unknown")
                            readings.append(reading)
            if not readings:
                reading = SensorReading(device_id, "payload", 0.0, "unknown")
                reading.raw_payload = payload
                readings.append(reading)
        elif isinstance(payload, list):
            for i, item in enumerate(payload):
                if isinstance(item, dict):
                    readings.extend(self._parse_payload(f"{device_id}[{i}]", item))
        return readings

    def _process_reading(self, reading: SensorReading):
        for rule in sorted(self.rules.values(), key=lambda r: r.priority):
            if not rule.enabled:
                continue
            if rule.evaluate(reading):
                rule.fire_count += 1
                for action in rule.actions:
                    if action.action_type == "drop":
                        return
                    elif action.action_type == "store":
                        sink = self.sinks.get(action.target)
                        if sink and sink.enabled:
                            sink.messages_written += 1
                    elif action.action_type == "alert":
                        logger.info("RULE ALERT: %s - %s = %s %s",
                                   rule.name, reading.sensor, reading.value, reading.unit)

    def get_statistics(self) -> dict[str, Any]:
        return {
            "total_messages": len(self.messages),
            "total_readings": len(self.readings),
            "active_rules": sum(1 for r in self.rules.values() if r.enabled),
            "active_sinks": sum(1 for s in self.sinks.values() if s.enabled),
            "total_rule_fires": sum(r.fire_count for r in self.rules.values()),
            "total_sink_writes": sum(s.messages_written for s in self.sinks.values()),
            "readings_by_sensor": dict(self._count_by_sensor()),
            "readings_last_hour": self._count_last_hour(),
        }

    def _count_by_sensor(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.readings[-1000:]:
            counts[r.sensor] = counts.get(r.sensor, 0) + 1
        return counts

    def _count_last_hour(self) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=1)
        return sum(1 for r in self.readings if r.timestamp > cutoff)

    def query_readings(self, device_id: Optional[str] = None,
                       sensor: Optional[str] = None,
                       limit: int = 100) -> list[dict]:
        result = self.readings
        if device_id:
            result = [r for r in result if r.device_id == device_id]
        if sensor:
            result = [r for r in result if r.sensor == sensor]
        return [r.to_dict() for r in result[-limit:]]

    def get_sink_status(self) -> list[dict]:
        return [s.to_dict() for s in self.sinks.values()]
