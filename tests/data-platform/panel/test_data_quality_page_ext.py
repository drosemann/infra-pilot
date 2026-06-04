"""Tests for DataQualityPage component."""
import pytest
from services.management_panel.src.pages.data_platform.DataQualityPage import DataQualityPage

class TestDataQualityPage:
    def test_page_render(self):
        assert DataQualityPage is not None

    def test_rules_state(self):
        page = DataQualityPage()
        assert hasattr(page, "rules")

    def test_create_rule(self):
        page = DataQualityPage()
        n = len(page.rules)
        page.create_rule("check", "users", "email", "not_null", "high")
        assert len(page.rules) == n + 1

    def test_run_validation(self):
        page = DataQualityPage()
        page.create_rule("r1", "users", "email", "not_null", "high")
        result = page.run_validation()
        assert result["total"] >= 1

    def test_get_violations(self):
        page = DataQualityPage()
        page.create_rule("r1", "users", "email", "not_null", "high")
        page.run_validation()
        violations = page.get_violations()
        assert isinstance(violations, list)

    def test_get_scorecard(self):
        page = DataQualityPage()
        page.create_rule("r1", "users", "email", "not_null", "high")
        scorecard = page.get_scorecard("users")
        assert scorecard["dataset"] == "users"
