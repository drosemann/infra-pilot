"""Tests for self_service_reporting module."""
import pytest
from services.integration_service.src.data_platform.self_service_reporting import (
    ReportManager, Report, Widget, ReportSchedule
)

@pytest.fixture
def manager():
    mgr = ReportManager()
    yield mgr
    mgr._reports.clear()

class TestReportCRUD:
    def test_create_report(self, manager):
        r = manager.create_report(name="monthly-sales", description="Monthly sales report", mode="visual")
        assert r.report_id is not None
        assert r.name == "monthly-sales"
        assert r.mode == "visual"

    def test_get_report(self, manager):
        r = manager.create_report(name="test", description="test", mode="sql")
        retrieved = manager.get_report(r.report_id)
        assert retrieved is not None

    def test_list_reports(self, manager):
        manager.create_report(name="r1", description="d1", mode="visual")
        manager.create_report(name="r2", description="d2", mode="sql")
        assert len(manager.list_reports()) >= 2

class TestExecution:
    def test_execute_report(self, manager):
        r = manager.create_report(name="exec-test", description="test", mode="visual")
        result = manager.execute_report(r.report_id)
        assert result.status == "executed"
        assert result.widgets >= 0

class TestExport:
    def test_export_report(self, manager):
        r = manager.create_report(name="export-test", description="test", mode="visual")
        result = manager.export_report(r.report_id, format="pdf")
        assert result.format == "pdf"
        assert result.url is not None

class TestScheduling:
    def test_create_schedule(self, manager):
        r = manager.create_report(name="sched-test", description="test", mode="visual")
        s = manager.create_schedule(report_id=r.report_id, frequency="daily", recipients=["admin@co.com"], format="pdf")
        assert s.schedule_id is not None
        assert s.frequency == "daily"
