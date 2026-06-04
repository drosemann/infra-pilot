"""Tests for SelfServiceReportingPage component."""
import pytest
from services.management_panel.src.pages.data_platform.SelfServiceReportingPage import SelfServiceReportingPage

class TestSelfServiceReportingPage:
    def test_page_render(self):
        assert SelfServiceReportingPage is not None

    def test_reports_state(self):
        page = SelfServiceReportingPage()
        assert hasattr(page, "reports")

    def test_create_report(self):
        page = SelfServiceReportingPage()
        n = len(page.reports)
        page.create_report("monthly-sales", "Monthly sales", "visual")
        assert len(page.reports) == n + 1

    def test_execute_report(self):
        page = SelfServiceReportingPage()
        page.create_report("exec-test", "test", "visual")
        result = page.execute_report(page.reports[0]["report_id"])
        assert result["status"] == "executed"

    def test_export_report(self):
        page = SelfServiceReportingPage()
        page.create_report("export-test", "test", "visual")
        result = page.export_report(page.reports[0]["report_id"], "pdf")
        assert result["format"] == "pdf"

    def test_schedule_report(self):
        page = SelfServiceReportingPage()
        page.create_report("sched-test", "test", "visual")
        result = page.schedule_report(page.reports[0]["report_id"], "daily", ["admin@co.com"], "pdf")
        assert result["frequency"] == "daily"
