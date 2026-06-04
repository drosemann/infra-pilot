"""Tests for realtime_analytics module."""
import pytest
from services.integration_service.src.data_platform.realtime_analytics import (
    RealtimeManager, RealtimeDashboard, DashboardPanel, LiveMetric
)

@pytest.fixture
def manager():
    mgr = RealtimeManager()
    yield mgr
    mgr._dashboards.clear()

class TestDashboardCRUD:
    def test_create_dashboard(self, manager):
        d = manager.create_dashboard(name="infra-monitor", refresh=10)
        assert d.dashboard_id is not None
        assert d.name == "infra-monitor"
        assert d.refresh == 10

    def test_get_dashboard(self, manager):
        d = manager.create_dashboard(name="test", refresh=5)
        retrieved = manager.get_dashboard(d.dashboard_id)
        assert retrieved is not None

    def test_list_dashboards(self, manager):
        manager.create_dashboard(name="d1", refresh=5)
        manager.create_dashboard(name="d2", refresh=10)
        assert len(manager.list_dashboards()) >= 2

    def test_delete_dashboard(self, manager):
        d = manager.create_dashboard(name="del", refresh=5)
        assert manager.delete_dashboard(d.dashboard_id) is True

class TestLiveData:
    def test_get_live_data(self, manager):
        d = manager.create_dashboard(name="live-test", refresh=5)
        data = manager.get_live_data(d.dashboard_id)
        assert data is not None
        assert "panels" in data

class TestMetricIngestion:
    def test_ingest_metric(self, manager):
        result = manager.ingest_metric(name="cpu_usage", value=87.5, tags={"host": "web-01"})
        assert result.name == "cpu_usage"
        assert result.ingested is True

    def test_ingest_metric_no_tags(self, manager):
        result = manager.ingest_metric(name="memory_usage", value=65.0)
        assert result.ingested is True
