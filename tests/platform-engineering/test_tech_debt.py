"""Tests for Tech Debt Tracker manager."""
import pytest
from services.integration_service.src.platform_engineering.tech_debt_tracker import TechDebtTracker


class TestTechDebtTracker:
    def setup_method(self):
        self.mgr = TechDebtTracker()

    def test_report_item(self):
        d = self.mgr.report_item("Bug in parser", "high", 8, "code")
        assert d.id is not None
        assert d.title == "Bug in parser"

    def test_get_item(self):
        d = self.mgr.report_item("Refactor needed", "medium", 4, "code")
        found = self.mgr.get_item(d.id)
        assert found.id == d.id

    def test_list_items(self):
        self.mgr.report_item("i1", "low", 2, "code")
        self.mgr.report_item("i2", "high", 10, "config")
        assert len(self.mgr.list_items()) == 2

    def test_list_items_filter_severity(self):
        self.mgr.report_item("a", "low", 1, "code")
        self.mgr.report_item("b", "high", 5, "code")
        high = self.mgr.list_items(severity="high")
        assert len(high) == 1

    def test_fix_item(self):
        d = self.mgr.report_item("Fix me", "critical", 12, "code")
        assert d.remediated is False
        self.mgr.fix_item(d.id)
        assert self.mgr.get_item(d.id).remediated is True

    def test_get_summary(self):
        self.mgr.report_item("d1", "high", 5, "code")
        self.mgr.report_item("d2", "medium", 3, "docs")
        s = self.mgr.get_summary()
        assert s["total_items"] == 2
        assert s["total_effort_hours"] == 8

    def test_to_dict_from_dict(self):
        d = self.mgr.report_item("roundtrip", "medium", 6, "code")
        d2 = d.to_dict()
        from services.integration_service.src.platform_engineering.tech_debt_tracker import TechDebtItem
        restored = TechDebtItem.from_dict(d2)
        assert restored.title == "roundtrip"
        assert restored.severity == "medium"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_items"] == 0
        assert s["total_effort_hours"] == 0

    def test_trend_analysis(self):
        self.mgr.report_item("old-item", "critical", 5, "security")
        trend = self.mgr.get_trend_analysis(days=365)
        assert trend["created"] >= 1

    def test_schedule_and_cancel_scan(self):
        scan = self.mgr.schedule_scan("svc-1", "full", 24)
        assert "scan_id" in scan
        cancelled = self.mgr.cancel_scheduled_scan(scan["scan_id"])
        assert cancelled

    def test_bulk_remediate(self):
        i1 = self.mgr.report_item("fix-me-1", "high", 3, "code")
        i2 = self.mgr.report_item("fix-me-2", "medium", 2, "code")
        result = self.mgr.bulk_remediate_items([i1.item_id, i2.item_id])
        assert result["succeeded"] == 2

    def test_get_debt_report(self):
        self.mgr.report_item("report-item", "critical", 8, "security")
        report = self.mgr.get_debt_report()
        assert report["total_items"] >= 1
        assert report["critical_open"] >= 1

    def test_service_rankings(self):
        self.mgr.report_item("rank-item", "critical", 5, "code", service_id="svc-alpha")
        rankings = self.mgr.get_service_rankings()
        assert len(rankings) >= 1

    def test_export_csv(self):
        self.mgr.report_item("csv-item", "low", 1, "test")
        csv = self.mgr.export_debt_csv()
        assert "csv-item" in csv
        assert csv.startswith("id")

    def test_dependency_links(self):
        i1 = self.mgr.report_item("dep-a", "medium", 2, "code")
        i2 = self.mgr.report_item("dep-b", "high", 3, "code")
        self.mgr.add_dependency_link(i1.item_id, i2.item_id)
        chain = self.mgr.get_dependency_chain(i1.item_id)
        assert len(chain) >= 2

    def test_batch_update_effort(self):
        i1 = self.mgr.report_item("effort-1", "low", 1, "code")
        i2 = self.mgr.report_item("effort-2", "low", 1, "code")
        count = self.mgr.batch_update_effort([i1.item_id, i2.item_id], 10)
        assert count == 2
