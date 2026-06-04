"""Tests for Feature 54: Intelligent Alert Correlation."""

import pytest
from services.integration_service.src.aiops.alert_correlation import AlertCorrelationEngine


@pytest.fixture
def engine():
    return AlertCorrelationEngine({})


class TestAlertCorrelation:
    def test_ingest_alert(self, engine):
        alert = engine.ingest_alert("HighCPU", "prometheus", "critical", "CPU at 95%")
        assert alert["name"] == "HighCPU"
        assert alert["status"] in ("firing", "suppressed")

    def test_dedup_same_alert(self, engine):
        a1 = engine.ingest_alert("DupTest", "source", "warning", "test message")
        a2 = engine.ingest_alert("DupTest", "source", "warning", "test message")
        assert a1["id"] == a2["id"]

    def test_create_incident(self, engine):
        engine.ingest_alert("Alert1", "source", "critical", "message 1")
        engine.ingest_alert("Alert2", "source", "warning", "message 2 about same source")
        incidents = engine.list_incidents()
        assert len(incidents) >= 1

    def test_acknowledge_alert(self, engine):
        alert = engine.ingest_alert("AckTest", "source", "warning", "ack me")
        engine.acknowledge_alert(alert["id"])
        assert alert["status"] == "acknowledged"

    def test_resolve_alert(self, engine):
        alert = engine.ingest_alert("ResolveTest", "source", "warning", "resolve me")
        engine.resolve_alert(alert["id"])
        assert alert["status"] == "resolved"

    def test_suppression_rule(self, engine):
        rule = engine.add_suppression_rule("Suppress Test CPU", match_name="CPU")
        assert rule["status"] == "active"
        suppressed = engine.ingest_alert("HighCPUAlert", "test", "critical", "CPU high")
        assert suppressed["status"] == "suppressed"

    def test_incident_resolution(self, engine):
        engine.ingest_alert("IncTest", "source", "critical", "incident test")
        incident = engine.list_incidents(status="firing")[0]
        engine.resolve_incident(incident["id"])
        assert incident["status"] == "resolved"

    def test_statistics(self, engine):
        stats = engine.get_statistics()
        assert "total_alerts" in stats
        assert "noise_reduction_percentage" in stats
