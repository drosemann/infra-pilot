"""Tests for RealtimeAnalyticsPage component."""
import pytest
from services.management_panel.src.pages.data_platform.RealtimeAnalyticsPage import RealtimeAnalyticsPage

class TestRealtimeAnalyticsPage:
    def test_page_render(self):
        assert RealtimeAnalyticsPage is not None

    def test_dashboards_state(self):
        page = RealtimeAnalyticsPage()
        assert hasattr(page, "dashboards")

    def test_create_dashboard(self):
        page = RealtimeAnalyticsPage()
        n = len(page.dashboards)
        page.create_dashboard("infra-monitor", 10)
        assert len(page.dashboards) == n + 1

    def test_delete_dashboard(self):
        page = RealtimeAnalyticsPage()
        page.create_dashboard("del-dash", 5)
        did = page.dashboards[0]["dashboard_id"]
        page.delete_dashboard(did)
        assert did not in [d["dashboard_id"] for d in page.dashboards]

    def test_get_live(self):
        page = RealtimeAnalyticsPage()
        page.create_dashboard("live", 5)
        data = page.get_live_data(page.dashboards[0]["dashboard_id"])
        assert "panels" in data

    def test_ingest_metric(self):
        page = RealtimeAnalyticsPage()
        result = page.ingest_metric("cpu_usage", 87.5)
        assert result["ingested"] is True
