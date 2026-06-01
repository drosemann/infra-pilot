"""Tests for Vendor Risk Assessment."""
import pytest
import json
from datetime import datetime, timedelta
from vendor_risk import VendorRiskManager, Vendor, Assessment, Finding, SIGQuestionnaire, CAIQQuestionnaire


@pytest.fixture
def manager():
    return VendorRiskManager({
        "default_risk_tier": "medium",
        "assessment_frequency_days": 365,
        "score_weight_security": 0.4,
        "score_weight_privacy": 0.3,
        "score_weight_compliance": 0.2,
        "score_weight_operations": 0.1,
        "auto_tier_update": True
    })


class TestVendorLifecycle:
    def test_register_vendor(self, manager):
        vendor = manager.register_vendor(
            name="CloudProvider Inc",
            domain="cloudprovider.com",
            category="cloud_infrastructure",
            contact_email="security@cloudprovider.com",
            tier="critical"
        )
        assert vendor.vendor_id is not None
        assert vendor.name == "CloudProvider Inc"
        assert vendor.tier == "critical"
        assert vendor.status == "active"

    def test_get_vendor(self, manager):
        original = manager.register_vendor("Acme Corp", "acme.com", "saas", "security@acme.com")
        retrieved = manager.get_vendor(original.vendor_id)
        assert retrieved.vendor_id == original.vendor_id

    def test_get_missing_vendor(self, manager):
        assert manager.get_vendor("nonexistent") is None

    def test_list_vendors(self, manager):
        manager.register_vendor("Vendor A", "a.com", "saas", "a@a.com")
        manager.register_vendor("Vendor B", "b.com", "infrastructure", "b@b.com")
        all_vendors = manager.list_vendors()
        assert len(all_vendors) >= 2

    def test_list_vendors_by_tier(self, manager):
        manager.register_vendor("Critical Vendor", "c.com", "cloud", "c@c.com", tier="critical")
        manager.register_vendor("Low Vendor", "l.com", "saas", "l@l.com", tier="low")
        critical = manager.list_vendors(tier="critical")
        assert len(critical) >= 1
        for v in critical:
            assert v.tier == "critical"

    def test_update_vendor(self, manager):
        vendor = manager.register_vendor("UpdateCo", "upd.com", "saas", "upd@upd.com")
        manager.update_vendor(vendor.vendor_id, {"name": "UpdateCo Renamed", "tier": "high"})
        assert vendor.name == "UpdateCo Renamed"
        assert vendor.tier == "high"

    def test_deactivate_vendor(self, manager):
        vendor = manager.register_vendor("Old Vendor", "old.com", "saas", "old@old.com")
        assert manager.deactivate_vendor(vendor.vendor_id) is True
        assert vendor.status == "inactive"

    def test_get_vendor_risk_score(self, manager):
        vendor = manager.register_vendor("RiskTest", "risk.com", "cloud", "risk@risk.com")
        score = manager.get_risk_score(vendor.vendor_id)
        assert score is not None
        assert 0 <= score.overall_score <= 100


class TestAssessments:
    def test_create_assessment(self, manager):
        vendor = manager.register_vendor("AssessCo", "assess.com", "saas", "a@a.com")
        assessment = manager.create_assessment(
            vendor_id=vendor.vendor_id,
            assessor="auditor-001",
            questionnaire_type="sig"
        )
        assert assessment.assessment_id is not None
        assert assessment.vendor_id == vendor.vendor_id
        assert assessment.status == "in_progress"

    def test_submit_assessment(self, manager):
        vendor = manager.register_vendor("AssessCo2", "assess2.com", "saas", "a@a.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-001", "sig")
        responses = {
            "security": {"encryption": "AES-256", "mfa": True, "sso": True},
            "privacy": {"gdpr": True, "data_classification": "confidential"},
            "compliance": {"soc2": True, "iso27001": True}
        }
        result = manager.submit_assessment(assessment.assessment_id, responses)
        assert result is True
        assert assessment.status == "completed"

    def test_get_assessment(self, manager):
        vendor = manager.register_vendor("GetAssess", "get.com", "saas", "g@g.com")
        original = manager.create_assessment(vendor.vendor_id, "auditor-001", "sig")
        retrieved = manager.get_assessment(original.assessment_id)
        assert retrieved.assessment_id == original.assessment_id

    def test_list_vendor_assessments(self, manager):
        vendor = manager.register_vendor("ListAssess", "list.com", "cloud", "l@l.com")
        manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        manager.create_assessment(vendor.vendor_id, "auditor-2", "caiq")
        assessments = manager.list_assessments(vendor_id=vendor.vendor_id)
        assert len(assessments) >= 2

    def test_assessment_scoring(self, manager):
        vendor = manager.register_vendor("ScoreTest", "score.com", "saas", "s@s.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-001", "sig")
        responses = {
            "security": {"encryption": "AES-256", "mfa": True, "pentest": True, "bug_bounty": True},
            "privacy": {"gdpr": True, "ccpa": True, "dpa": True},
            "compliance": {"soc2": True, "iso27001": True, "hipaa": False},
            "operations": {"uptime_sla": 99.99, "incident_response": True}
        }
        manager.submit_assessment(assessment.assessment_id, responses)
        assert assessment.score is not None
        assert assessment.score >= 0


class TestFindings:
    def test_create_finding(self, manager):
        vendor = manager.register_vendor("FindCo", "find.com", "saas", "f@f.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        manager.submit_assessment(assessment.assessment_id, {})
        finding = manager.create_finding(
            assessment_id=assessment.assessment_id,
            title="Missing MFA",
            severity="high",
            category="security",
            description="Vendor does not require MFA for admin accounts",
            remediation="Implement MFA within 30 days"
        )
        assert finding.finding_id is not None
        assert finding.title == "Missing MFA"
        assert finding.severity == "high"

    def test_list_findings(self, manager):
        vendor = manager.register_vendor("FindCo2", "find2.com", "saas", "f2@f2.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        manager.submit_assessment(assessment.assessment_id, {})
        manager.create_finding(assessment.assessment_id, "Finding 1", "high", "security", "Desc", "Remed")
        manager.create_finding(assessment.assessment_id, "Finding 2", "medium", "privacy", "Desc", "Remed")
        findings = manager.list_findings(assessment_id=assessment.assessment_id)
        assert len(findings) >= 2

    def test_update_finding_status(self, manager):
        vendor = manager.register_vendor("FindCo3", "find3.com", "saas", "f3@f3.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        manager.submit_assessment(assessment.assessment_id, {})
        finding = manager.create_finding(assessment.assessment_id, "Test Finding", "low", "operations", "Desc", "Remed")
        assert manager.update_finding_status(finding.finding_id, "resolved", "Fixed MFA implementation") is True
        assert finding.status == "resolved"
        assert finding.resolution_notes == "Fixed MFA implementation"

    def test_get_open_findings_count(self, manager):
        vendor = manager.register_vendor("FindCo4", "find4.com", "saas", "f4@f4.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        manager.submit_assessment(assessment.assessment_id, {})
        for i in range(3):
            manager.create_finding(assessment.assessment_id, f"Finding {i}", "medium", "security", "Desc", "Remed")
        open_count = manager.get_open_findings_count(vendor.vendor_id)
        assert open_count >= 3


class TestQuestionnaires:
    def test_get_sig_questionnaire(self, manager):
        sig = manager.get_questionnaire("sig")
        assert sig is not None
        assert sig.type == "sig"
        assert len(sig.sections) > 0

    def test_get_caiq_questionnaire(self, manager):
        caiq = manager.get_questionnaire("caiq")
        assert caiq is not None
        assert caiq.type == "caiq"
        assert len(caiq.sections) > 0

    def test_get_invalid_questionnaire(self, manager):
        assert manager.get_questionnaire("invalid_type") is None

    def test_score_calculation_weights(self, manager):
        vendor = manager.register_vendor("WeightTest", "weight.com", "cloud", "w@w.com")
        assessment = manager.create_assessment(vendor.vendor_id, "auditor-1", "sig")
        responses = {
            "security": {"encryption": True, "mfa": True, "pentest": True, "ids": True},
            "privacy": {"gdpr": True, "ccpa": True},
            "compliance": {"soc2": True},
            "operations": {"uptime": 99.9}
        }
        manager.submit_assessment(assessment.assessment_id, responses)
        assert assessment.score > 50


class TestRiskTierAutoUpdate:
    def test_auto_update_tier_critical(self, manager):
        vendor = manager.register_vendor("AutoTier", "auto.com", "saas", "a@a.com")
        manager._vendor_scores[vendor.vendor_id] = 95.0
        new_tier = manager._calculate_risk_tier(vendor.vendor_id)
        assert new_tier == "low"

    def test_auto_update_tier_critical_low_score(self, manager):
        vendor = manager.register_vendor("HighRiskCo", "highrisk.com", "saas", "h@h.com")
        manager._vendor_scores[vendor.vendor_id] = 25.0
        new_tier = manager._calculate_risk_tier(vendor.vendor_id)
        assert new_tier == "critical"

    def test_auto_update_tier_medium(self, manager):
        vendor = manager.register_vendor("MediumCo", "med.com", "saas", "m@m.com")
        manager._vendor_scores[vendor.vendor_id] = 55.0
        new_tier = manager._calculate_risk_tier(vendor.vendor_id)
        assert new_tier == "medium"
