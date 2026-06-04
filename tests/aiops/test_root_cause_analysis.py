"""Tests for Feature 51: AI Root Cause Analysis."""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.aiops.root_cause_analysis import RootCauseAnalyzer


@pytest.fixture
def analyzer():
    return RootCauseAnalyzer({})


class TestRootCauseAnalyzer:
    def test_ingest_event(self, analyzer):
        event = analyzer.ingest_event("metric", "prometheus", "High CPU", "CPU at 95%", {"value": 95}, "critical")
        assert event["event_type"] == "metric"
        assert event["source"] == "prometheus"
        assert event["severity"] == "critical"

    def test_analyze_with_no_events(self, analyzer):
        result = analyzer.analyze(incident_title="Test Incident", incident_description="Testing")
        assert result["root_cause"] is None
        assert result["confidence"] == 0.0

    def test_analyze_with_events(self, analyzer):
        analyzer.ingest_event("metric", "web-server", "High CPU", "CPU at 95%", {"value": 95}, "critical")
        analyzer.ingest_event("log", "web-server", "Error rate spike", "Connection timeout errors", {}, "high")
        result = analyzer.analyze(incident_title="Web Server Down", incident_description="Server unreachable")
        assert result["incident_id"] is not None

    def test_dependency_graph(self, analyzer):
        analyzer.set_dependency("web-server", ["database", "cache"])
        graph = analyzer.get_dependency_graph()
        assert "web-server" in graph
        assert "database" in graph["web-server"]

    def test_list_incidents(self, analyzer):
        analyzer.analyze(incident_title="Incident A")
        analyzer.analyze(incident_title="Incident B")
        incidents = analyzer.list_incidents()
        assert len(incidents) >= 2

    def test_get_events_filtered(self, analyzer):
        analyzer.ingest_event("metric", "source-a", "Event A", "")
        analyzer.ingest_event("log", "source-b", "Event B", "")
        filtered = analyzer.get_events(source="source-a")
        assert all(e["source"] == "source-a" for e in filtered)

    def test_clear_events(self, analyzer):
        analyzer.ingest_event("metric", "test", "Test", "")
        analyzer.clear_events()
        assert len(analyzer.events) == 0

    def test_clear_incidents(self, analyzer):
        analyzer.analyze(incident_title="Test")
        analyzer.clear_incidents()
        assert len(analyzer.incidents) == 0
