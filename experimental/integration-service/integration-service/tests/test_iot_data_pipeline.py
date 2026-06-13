"""Tests for IoT Data Pipeline."""

import pytest
from datetime import datetime, timedelta
from src.iot_data_pipeline import (
    IoTDataPipeline, SensorReading, PipelineMessage, PipelineRule,
    RuleCondition, RuleAction, DataSink, SinkType, ProtocolType
)


@pytest.fixture
def pipeline():
    return IoTDataPipeline({})


class TestSensorReading:
    def test_create_reading(self):
        r = SensorReading("dev-001", "temperature", 23.5, "°C")
        assert r.device_id == "dev-001"
        assert r.sensor == "temperature"
        assert r.value == 23.5
        assert r.reading_id is not None

    def test_reading_to_dict(self):
        r = SensorReading("dev-001", "humidity", 65.0, "%")
        d = r.to_dict()
        assert d["sensor"] == "humidity"
        assert d["value"] == 65.0


class TestPipelineRule:
    def test_rule_creation(self):
        conditions = [RuleCondition("value", ">", 85.0)]
        actions = [RuleAction("alert", "webhook")]
        rule = PipelineRule("rule-001", "High Temp", conditions, actions)
        assert rule.name == "High Temp"
        assert len(rule.conditions) == 1
        assert rule.fire_count == 0

    def test_rule_evaluate_true(self):
        conditions = [RuleCondition("value", ">", 80.0)]
        rule = PipelineRule("r1", "Test", conditions, [])
        reading = SensorReading("d1", "temperature", 90.0, "°C")
        assert rule.evaluate(reading) is True

    def test_rule_evaluate_false(self):
        conditions = [RuleCondition("value", ">", 100.0)]
        rule = PipelineRule("r2", "Test", conditions, [])
        reading = SensorReading("d1", "temperature", 50.0, "°C")
        assert rule.evaluate(reading) is False

    def test_rule_disabled(self):
        conditions = [RuleCondition("value", ">", 0)]
        rule = PipelineRule("r3", "Test", conditions, [], enabled=False)
        reading = SensorReading("d1", "temp", 100.0, "°C")
        assert rule.evaluate(reading) is False


class TestDataSink:
    def test_sink_creation(self):
        sink = DataSink("sink-001", "PostgreSQL", SinkType.POSTGRESQL, {"host": "localhost"})
        assert sink.sink_id == "sink-001"
        assert sink.sink_type == SinkType.POSTGRESQL
        assert sink.messages_written == 0


class TestIoTDataPipeline:
    def test_pipeline_initialization(self, pipeline):
        assert len(pipeline.rules) > 0
        assert len(pipeline.sinks) > 0
        assert len(pipeline.readings) > 0

    def test_ingest_mqtt(self, pipeline):
        msg = pipeline.ingest("dev-001", {"temperature": 25.0, "humidity": 60.0}, "mqtt")
        assert msg.protocol == ProtocolType.MQTT
        assert len(msg.readings) > 0

    def test_ingest_coap(self, pipeline):
        msg = pipeline.ingest("dev-002", {"pressure": 1013.0}, "coap")
        assert msg.protocol == ProtocolType.COAP

    def test_ingest_http(self, pipeline):
        msg = pipeline.ingest("dev-003", {"value": 42}, "http")
        assert msg.protocol == ProtocolType.HTTP

    def test_ingest_nested_payload(self, pipeline):
        msg = pipeline.ingest("dev-004", {"sensors": {"temp": 22.5, "hum": 55}}, "mqtt")
        assert len(msg.readings) >= 2

    def test_add_rule(self, pipeline):
        conditions = [RuleCondition("value", ">", 100)]
        actions = [RuleAction("store", "sink-001")]
        rule = pipeline.add_rule("New Rule", conditions, actions)
        assert rule.rule_id is not None
        assert rule.name == "New Rule"
        assert pipeline.get_rule(rule.rule_id) is not None

    def test_get_rule_not_found(self, pipeline):
        assert pipeline.get_rule("nonexistent") is None

    def test_list_rules(self, pipeline):
        rules = pipeline.list_rules()
        assert len(rules) > 0

    def test_list_rules_enabled_only(self, pipeline):
        enabled = pipeline.list_rules(enabled_only=True)
        assert all(r.enabled for r in enabled)

    def test_update_rule(self, pipeline):
        rule_id = list(pipeline.rules.keys())[0]
        updated = pipeline.update_rule(rule_id, {"enabled": False})
        assert updated is not None
        assert updated.enabled is False

    def test_update_rule_not_found(self, pipeline):
        assert pipeline.update_rule("nonexistent", {}) is None

    def test_delete_rule(self, pipeline):
        rule_id = list(pipeline.rules.keys())[0]
        assert pipeline.delete_rule(rule_id) is True
        assert pipeline.get_rule(rule_id) is None

    def test_delete_rule_not_found(self, pipeline):
        assert pipeline.delete_rule("nonexistent") is False

    def test_add_sink(self, pipeline):
        sink = pipeline.add_sink("Test Sink", SinkType.WEBHOOK, {"url": "http://hook.test"})
        assert sink.sink_id is not None
        assert pipeline.get_sink(sink.sink_id) is not None

    def test_get_sink_not_found(self, pipeline):
        assert pipeline.get_sink("nonexistent") is None

    def test_list_sinks(self, pipeline):
        sinks = pipeline.list_sinks()
        assert len(sinks) > 0

    def test_delete_sink_not_found(self, pipeline):
        assert pipeline.delete_sink("nonexistent") is False

    def test_get_statistics(self, pipeline):
        stats = pipeline.get_statistics()
        assert "total_messages" in stats
        assert "total_readings" in stats
        assert "active_rules" in stats
        assert "active_sinks" in stats

    def test_query_readings(self, pipeline):
        readings = pipeline.query_readings(limit=5)
        assert len(readings) <= 5

    def test_query_readings_by_device(self, pipeline):
        if pipeline.readings:
            device_id = pipeline.readings[0].device_id
            readings = pipeline.query_readings(device_id=device_id)
            assert all(r["device_id"] == device_id for r in readings)

    def test_get_sink_status(self, pipeline):
        status = pipeline.get_sink_status()
        assert len(status) > 0

    def test_register_transformer(self, pipeline):
        def dummy(reading):
            return reading
        pipeline.register_transformer("dummy", dummy)
        assert "dummy" in pipeline._transformers

    def test_rule_condition_between(self):
        cond = RuleCondition("value", "between", [20, 80])
        reading = SensorReading("d1", "temp", 50.0, "°C")
        assert cond.evaluate(reading) is True
        reading.value = 10.0
        assert cond.evaluate(reading) is False

    def test_rule_condition_equals(self):
        cond = RuleCondition("sensor", "==", "temperature")
        reading = SensorReading("d1", "temperature", 25.0, "°C")
        assert cond.evaluate(reading) is True
        reading2 = SensorReading("d1", "humidity", 50.0, "%")
        assert cond.evaluate(reading2) is False

    def test_rule_condition_not_equals(self):
        cond = RuleCondition("sensor", "!=", "temperature")
        reading = SensorReading("d1", "humidity", 50.0, "%")
        assert cond.evaluate(reading) is True
