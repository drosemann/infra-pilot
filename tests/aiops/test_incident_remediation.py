"""Tests for Feature 52: Automated Incident Remediation."""

import pytest
from services.integration_service.src.aiops.incident_remediation import IncidentRemediationEngine, RemediationStatus


@pytest.fixture
def engine():
    return IncidentRemediationEngine({})


class TestIncidentRemediation:
    def test_suggest_remediation(self, engine):
        incident = {"title": "High CPU Usage Detected", "description": "CPU at 95% for 5 minutes"}
        suggestions = engine.suggest_remediation(incident)
        assert len(suggestions) > 0
        assert suggestions[0]["adjusted_confidence"] > 0

    def test_create_remediation(self, engine):
        rem = engine.create_remediation("inc-001", "restart_service", {"service": "nginx"}, 0.85, "service_down")
        assert rem["status"] == "pending"
        assert rem["incident_id"] == "inc-001"

    def test_auto_approve_high_confidence(self, engine):
        rem = engine.create_remediation("inc-002", "rollback_deploy", {}, 0.95, "deploy_failure")
        assert rem["status"] == "approved"

    def test_approve_remediation(self, engine):
        rem = engine.create_remediation("inc-003", "scale_up", {}, 0.7, "high_cpu")
        result = engine.approve_remediation(rem["id"], "admin")
        assert result["status"] == "approved"

    def test_reject_remediation(self, engine):
        rem = engine.create_remediation("inc-004", "restart_service", {}, 0.6, "generic")
        result = engine.reject_remediation(rem["id"], "No approval for this action")
        assert result["status"] == "rejected"

    def test_execute_remediation(self, engine):
        rem = engine.create_remediation("inc-005", "restart_service", {}, 0.9, "service_down")
        result = engine.execute_remediation(rem["id"])
        assert result["status"] in ("completed", "failed")

    def test_list_remediations(self, engine):
        engine.create_remediation("inc-a", "restart", {}, 0.8, "pattern-a")
        engine.create_remediation("inc-b", "scale", {}, 0.7, "pattern-b")
        all_rems = engine.list_remediations()
        assert len(all_rems) >= 2

    def test_get_statistics(self, engine):
        stats = engine.get_statistics()
        assert "total_remediations" in stats
        assert "success_rate" in stats

    def test_get_patterns(self, engine):
        patterns = engine.get_patterns()
        assert len(patterns) > 0
        assert any(p["pattern"] == "high_cpu" for p in patterns)
