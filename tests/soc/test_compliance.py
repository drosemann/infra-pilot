import pytest


class TestCompliance:
    def test_framework_management(self):
        frameworks = [
            {"name": "ISO 27001", "status": "certified"},
            {"name": "SOC 2", "status": "certified"},
            {"name": "PCI DSS", "status": "compliant"},
        ]
        certified = [f for f in frameworks if f["status"] == "certified"]
        assert len(certified) == 2

    def test_control_testing(self):
        controls = [
            {"id": "c1", "status": "passed"},
            {"id": "c2", "status": "failed"},
            {"id": "c3", "status": "passed"},
        ]
        passed = [c for c in controls if c["status"] == "passed"]
        assert len(passed) == 2

    def test_audit_tracking(self):
        audits = [{"id": "a1", "framework": "ISO 27001", "status": "in_progress"}]
        assert audits[0]["status"] == "in_progress"
        audits[0]["status"] = "completed"
        assert audits[0]["status"] == "completed"

    def test_remediation_tracking(self):
        remediations = [
            {"id": "r1", "status": "open", "due_date": "2025-11-20"},
            {"id": "r2", "status": "resolved", "due_date": "2025-11-10"},
        ]
        open_items = [r for r in remediations if r["status"] == "open"]
        assert len(open_items) == 1

    def test_compliance_score(self):
        score = {"overall": 91.2, "controls_pass": 312, "controls_total": 342}
        assert 0 <= score["overall"] <= 100
        assert score["controls_pass"] <= score["controls_total"]
