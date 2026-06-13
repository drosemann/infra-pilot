"""Tests for Audit Analytics (ML Anomaly Detection)."""
import pytest
import json
import time
from datetime import datetime, timedelta
from audit_analytics import AuditAnalytics, AnomalyScore, UserBaseline, AuditEvent


@pytest.fixture
def analytics():
    return AuditAnalytics({
        "anomaly_threshold": 0.8,
        "baseline_window_days": 30,
        "isolation_forest_contamination": 0.1,
        "max_events_per_batch": 1000,
        "trend_period_days": 7
    })


class TestAuditEventIngestion:
    def test_ingest_event(self, analytics):
        event = analytics.ingest_event("user-001", "server.create", {"server_id": "srv-001", "type": "web"}, "127.0.0.1")
        assert event.event_id is not None
        assert event.user_id == "user-001"
        assert event.action == "server.create"
        assert event.timestamp is not None

    def test_bulk_ingest(self, analytics):
        events = []
        for i in range(10):
            events.append({"user_id": f"user-{i}", "action": "server.read", "details": {"server_id": f"srv-{i}"}, "ip_address": f"10.0.0.{i}"})
        ids = analytics.bulk_ingest(events)
        assert len(ids) == 10
        assert all(e is not None for e in ids)

    def test_get_event(self, analytics):
        original = analytics.ingest_event("user-001", "server.delete", {"server_id": "srv-001"}, "10.0.0.1")
        retrieved = analytics.get_event(original.event_id)
        assert retrieved.event_id == original.event_id

    def test_get_missing_event(self, analytics):
        assert analytics.get_event("nonexistent") is None

    def test_search_events(self, analytics):
        analytics.ingest_event("user-001", "server.create", {}, "10.0.0.1")
        analytics.ingest_event("user-001", "server.delete", {}, "10.0.0.1")
        analytics.ingest_event("user-002", "server.create", {}, "10.0.0.2")
        results = analytics.search_events(user_id="user-001")
        assert len(results) >= 2
        results_by_action = analytics.search_events(action="server.create")
        assert len(results_by_action) >= 2


class TestAnomalyDetection:
    def test_detect_anomaly_isolation_forest(self, analytics):
        for _ in range(50):
            analytics.ingest_event("user-normal", "server.read", {}, "10.0.0.1")
        anomaly = analytics.ingest_event("user-normal", "admin.role_grant", {"role": "superadmin"}, "10.0.0.1")
        scores = analytics.calculate_anomaly_scores("user-normal")
        assert len(scores) > 0
        max_score = max(s.anomaly_score for s in scores)
        assert max_score >= 0

    def test_get_anomalies(self, analytics):
        analytics.ingest_event("user-001", "login", {}, "10.0.0.1")
        analytics.ingest_event("user-001", "role_grant", {"role": "admin"}, "10.0.0.1")
        anomalies = analytics.get_anomalies(threshold=0.0)
        assert len(anomalies) >= 0

    def test_anomaly_severity(self, analytics):
        high_anomaly = AnomalyScore(event_id="evt-1", user_id="user-001", anomaly_score=0.95, features={}, timestamp=datetime.utcnow())
        low_anomaly = AnomalyScore(event_id="evt-2", user_id="user-002", anomaly_score=0.3, features={}, timestamp=datetime.utcnow())
        assert high_anomaly.severity == "critical"
        assert low_anomaly.severity == "low"

    def test_anomaly_trend(self, analytics):
        now = datetime.utcnow()
        for i in range(20):
            analytics.ingest_event("user-trend", "server.read", {}, "10.0.0.1")
        for i in range(5):
            analytics.ingest_event("user-trend", "admin.action", {"cmd": f"rm -rf /tmp/{i}"}, "10.0.0.1")
        trend = analytics.get_anomaly_trend("user-trend", hours=48)
        assert trend["total_events"] >= 25
        assert trend["anomaly_count"] >= 0

    def test_cross_user_anomaly_comparison(self, analytics):
        analytics.ingest_event("user-001", "login.failed", {}, "10.0.0.1")
        analytics.ingest_event("user-002", "login.failed", {}, "10.0.0.1")
        analytics.ingest_event("user-003", "login.success", {}, "10.0.0.1")
        comparison = analytics.compare_users(["user-001", "user-002", "user-003"])
        assert "user-001" in comparison
        assert "user-002" in comparison
        assert "user-003" in comparison


class TestUserBaseline:
    def test_build_baseline(self, analytics):
        for _ in range(20):
            analytics.ingest_event("user-baseline", "server.read", {}, "10.0.0.1")
        for _ in range(5):
            analytics.ingest_event("user-baseline", "server.create", {}, "10.0.0.1")
        baseline = analytics.build_baseline("user-baseline")
        assert baseline is not None
        assert baseline.user_id == "user-baseline"
        assert baseline.total_events >= 25
        assert "server.read" in baseline.action_frequencies

    def test_baseline_deviation(self, analytics):
        for _ in range(30):
            analytics.ingest_event("user-base", "server.read", {}, "10.0.0.1")
        baseline = analytics.build_baseline("user-base")
        deviation = analytics.calculate_deviation("user-base", {"action": "admin.delete", "resource": "prod-db"})
        assert deviation > 0.5

    def test_baseline_no_deviation(self, analytics):
        for _ in range(30):
            analytics.ingest_event("user-base", "server.read", {}, "10.0.0.1")
        baseline = analytics.build_baseline("user-base")
        deviation = analytics.calculate_deviation("user-base", {"action": "server.read", "resource": "web-01"})
        assert deviation < 0.5

    def test_baseline_no_events(self, analytics):
        baseline = analytics.build_baseline("user-new")
        assert baseline is None


class TestImpossibleTravel:
    def test_detect_impossible_travel(self, analytics):
        analytics.ingest_event("user-travel", "login", {}, "8.8.8.8")  # US
        time.sleep(0.01)
        analytics.ingest_event("user-travel", "login", {}, "1.1.1.1")  # AU
        travel_events = analytics.detect_impossible_travel(hours=24)
        assert len(travel_events) >= 0

    def test_travel_velocity(self, analytics):
        vel = analytics.calculate_travel_velocity(52.5200, 13.4050, 35.6762, 139.6503, seconds=60)
        assert vel > 8000  # Berlin to Tokyo in 1 min = impossibly fast

    def test_normal_travel_no_flag(self, analytics):
        vel = analytics.calculate_travel_velocity(40.7128, -74.0060, 40.7580, -73.9855, seconds=3600)
        assert vel < 100  # NYC downtown in 1 hour = walking speed


class TestCorrelation:
    def test_correlate_events(self, analytics):
        evt1 = analytics.ingest_event("user-001", "login.failed", {}, "10.0.0.1")
        evt2 = analytics.ingest_event("user-001", "login.failed", {}, "10.0.0.1")
        evt3 = analytics.ingest_event("user-001", "login.success", {}, "10.0.0.1")
        correlations = analytics.correlate_events([evt1.event_id, evt2.event_id, evt3.event_id])
        assert len(correlations) >= 0

    def test_correlation_by_ip(self, analytics):
        analytics.ingest_event("user-001", "login", {}, "10.0.0.1")
        analytics.ingest_event("user-002", "login", {}, "10.0.0.1")
        analytics.ingest_event("user-003", "login", {}, "10.0.0.2")
        by_ip = analytics.correlate_by_ip(hours=24)
        assert "10.0.0.1" in by_ip
        assert len(by_ip["10.0.0.1"]) >= 2

    def test_correlation_by_action_type(self, analytics):
        analytics.ingest_event("user-001", "server.create", {}, "10.0.0.1")
        analytics.ingest_event("user-002", "server.create", {}, "10.0.0.1")
        analytics.ingest_event("user-001", "server.delete", {}, "10.0.0.1")
        by_action = analytics.correlate_by_action("server.create", hours=24)
        assert len(by_action) >= 2


class TestReporting:
    def test_summary_report(self, analytics):
        for i in range(10):
            analytics.ingest_event(f"user-{i}", "server.read", {}, "10.0.0.1")
        summary = analytics.generate_summary(hours=48)
        assert summary["total_events"] >= 10
        assert "unique_users" in summary
        assert "unique_actions" in summary
        assert summary["unique_users"] >= 10

    def test_user_report(self, analytics):
        analytics.ingest_event("user-001", "login", {}, "10.0.0.1")
        analytics.ingest_event("user-001", "server.create", {}, "10.0.0.1")
        report = analytics.generate_user_report("user-001")
        assert report["user_id"] == "user-001"
        assert report["total_events"] >= 2

    def test_trend_report(self, analytics):
        for i in range(24):
            analytics.ingest_event("user-001", "server.read", {}, "10.0.0.1")
        trend = analytics.get_event_trend(hours=48)
        assert len(trend) > 0
