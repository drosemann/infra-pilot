"""Tests for Feature 58: Change Risk Analysis."""

import pytest
from services.integration_service.src.aiops.change_risk import ChangeRiskAnalyzer


@pytest.fixture
def analyzer():
    return ChangeRiskAnalyzer({})


class TestChangeRisk:
    def test_plan_change(self, analyzer):
        result = analyzer.plan_change("Update nginx config", "Update SSL cert", "config_change",
                                       "nginx-proxy", ["nginx-config", "ssl-certs"])
        assert "change" in result
        assert "analysis" in result

    def test_analyze_risk(self, analyzer):
        result = analyzer.plan_change("Database migration", "Migrate to new schema", "migration",
                                       "postgres-db", ["db-primary", "db-replica", "app-config", "cache"])
        analysis = result["analysis"]
        assert "overall_risk_level" in analysis
        assert "risk_factors" in analysis

    def test_approve_change(self, analyzer):
        result = analyzer.plan_change("Test change", "", "deployment", "web", ["web-1"])
        change_id = result["change"]["id"]
        approved = analyzer.approve_change(change_id, "admin")
        assert approved["status"] == "approved"

    def test_reject_change(self, analyzer):
        result = analyzer.plan_change("Bad change", "", "deployment", "web", ["web-1"])
        change_id = result["change"]["id"]
        rejected = analyzer.reject_change(change_id, "Too risky")
        assert rejected["status"] == "rejected"

    def test_record_outcome(self, analyzer):
        result = analyzer.plan_change("Outcome test", "", "deployment", "api", ["api-1"])
        change_id = result["change"]["id"]
        outcome = analyzer.record_outcome(change_id, "completed", {"rollback_plan": True})
        assert outcome["status"] == "completed"

    def test_high_risk_migration(self, analyzer):
        result = analyzer.plan_change("Critical DB migration", "", "migration", "db",
                                       ["db-1", "db-2", "db-3", "cache", "app", "worker"])
        assert result["analysis"]["overall_risk_level"] in ("high", "critical", "medium")

    def test_low_risk_change(self, analyzer):
        result = analyzer.plan_change("Minor config", "", "config_change", "web", ["web-config"])
        assert result["change"]["status"] == "pending"

    def test_statistics(self, analyzer):
        stats = analyzer.get_statistics()
        assert "total_changes" in stats
        assert "success_rate" in stats
