"""Tests for DataMaskingPage component."""
import pytest
from services.management_panel.src.pages.data_platform.DataMaskingPage import DataMaskingPage

class TestDataMaskingPage:
    def test_page_render(self):
        assert DataMaskingPage is not None

    def test_rules_state(self):
        page = DataMaskingPage()
        assert hasattr(page, "rules")

    def test_create_rule(self):
        page = DataMaskingPage()
        n = len(page.rules)
        page.create_rule("hide-email", "email", "redact", "high")
        assert len(page.rules) == n + 1

    def test_profiles_state(self):
        page = DataMaskingPage()
        assert hasattr(page, "profiles")

    def test_create_profile(self):
        page = DataMaskingPage()
        page.create_rule("email-rule", "email", "redact", "high")
        rid = page.rules[0]["rule_id"]
        n = len(page.profiles)
        page.create_profile("pii", ["users"], [rid])
        assert len(page.profiles) == n + 1

    def test_apply_profile(self):
        page = DataMaskingPage()
        page.create_rule("er", "email", "redact", "high")
        page.create_profile("p", ["users"], [page.rules[0]["rule_id"]])
        result = page.apply_profile(page.profiles[0]["profile_id"])
        assert result["status"] == "applied"
