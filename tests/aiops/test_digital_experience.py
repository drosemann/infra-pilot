"""Tests for Feature 53: Digital Experience Monitoring."""

import pytest
from services.integration_service.src.aiops.digital_experience import DigitalExperienceMonitor


@pytest.fixture
def monitor():
    return DigitalExperienceMonitor({})


class TestDigitalExperience:
    def test_create_monitor(self, monitor):
        m = monitor.create_monitor("Test Site", "https://example.com", "browser_synthetic")
        assert m["name"] == "Test Site"
        assert m["status"] == "active"

    def test_get_monitor(self, monitor):
        m = monitor.create_monitor("Get Test", "https://test.com")
        found = monitor.get_monitor(m["id"])
        assert found["id"] == m["id"]

    def test_update_monitor(self, monitor):
        m = monitor.create_monitor("Update Test", "https://update.com")
        updated = monitor.update_monitor(m["id"], {"name": "Updated Name"})
        assert updated["name"] == "Updated Name"

    def test_delete_monitor(self, monitor):
        m = monitor.create_monitor("Delete Test", "https://delete.com")
        assert monitor.delete_monitor(m["id"]) is True
        assert monitor.get_monitor(m["id"]) is None

    def test_run_check(self, monitor):
        m = monitor.create_monitor("Check Test", "https://check.com")
        result = monitor.run_check(m["id"])
        assert "result" in result
        assert "metrics" in result

    def test_monitor_stats(self, monitor):
        m = monitor.create_monitor("Stats Test", "https://stats.com")
        stats = monitor.get_monitor_stats(m["id"])
        assert "uptime_percentage" in stats

    def test_global_summary(self, monitor):
        summary = monitor.get_global_summary()
        assert "total_monitors" in summary

    def test_core_web_vitals(self, monitor):
        m = monitor.create_monitor("Vitals Test", "https://vitals.com")
        monitor.run_check(m["id"])
        vitals = monitor.get_core_web_vitals(m["id"])
        assert "data_points" in vitals

    def test_list_monitors_filtered(self, monitor):
        monitor.create_monitor("Active", "https://a.com")
        monitor.create_monitor("Paused", "https://b.com", status="paused")
        active = monitor.list_monitors(status="active")
        assert all(m["status"] == "active" for m in active)
