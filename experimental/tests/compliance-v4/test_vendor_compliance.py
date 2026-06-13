import pytest
from services.integration_service.src.compliance_v4.vendor_compliance import (
    VendorComplianceManager, VendorRiskTier,
)

@pytest.fixture
def manager(tmp_path):
    return VendorComplianceManager({"vendor_compliance_file": str(tmp_path / "vc.json")})

def test_register_vendor(manager):
    v = manager.register_vendor("Acme Corp", "acme.com", "saas", "Cloud provider")
    assert v.name == "Acme Corp"
    assert v.risk_tier == VendorRiskTier.MEDIUM
    assert v.status == "active"

def test_register_duplicate_domain(manager):
    manager.register_vendor("Acme", "acme.com", "saas")
    with pytest.raises(ValueError):
        manager.register_vendor("Acme2", "acme.com", "saas")

def test_create_assessment(manager):
    vendor = manager.register_vendor("Acme", "acme.com", "saas")
    assessment = manager.create_assessment(vendor.vendor_id)
    assert assessment is not None
    assert assessment.status.value == "draft"
    assert len(assessment.questions) > 0

def test_submit_assessment(manager):
    vendor = manager.register_vendor("Acme", "acme.com", "saas")
    assessment = manager.create_assessment(vendor.vendor_id)
    answers = {q.question_id: "Yes" for q in assessment.questions}
    submitted = manager.submit_assessment(assessment.assessment_id, answers)
    assert submitted.overall_score == 100.0
    assert submitted.findings_count == 0

def test_review_assessment(manager):
    vendor = manager.register_vendor("Acme", "acme.com", "saas")
    assessment = manager.create_assessment(vendor.vendor_id)
    manager.submit_assessment(assessment.assessment_id, {q.question_id: "Yes" for q in assessment.questions})
    reviewed = manager.review_assessment(assessment.assessment_id, "reviewer@example.com")
    assert reviewed.status.value == "reviewed"

def test_get_vendors(manager):
    manager.register_vendor("Acme", "acme.com", "saas")
    manager.register_vendor("Beta", "beta.com", "infra")
    vendors = manager.get_vendors()
    assert len(vendors) == 2

def test_get_vendors_by_category(manager):
    manager.register_vendor("Acme", "acme.com", "saas")
    manager.register_vendor("Beta", "beta.com", "infra")
    saas = manager.get_vendors(category="saas")
    assert len(saas) == 1

def test_get_risk_summary(manager):
    manager.register_vendor("Acme", "acme.com", "saas")
    summary = manager.get_risk_summary()
    assert summary["total_vendors"] == 1

def test_categorize_vendors(manager):
    v = manager.register_vendor("Acme", "acme.com", "saas")
    result = manager.categorize_vendors({v.vendor_id: "security"})
    assert result["categories"] == ["security"]

def test_discover_vendors(manager):
    discovered = manager.discover_vendors(["newvendor.com", "another.io"])
    assert len(discovered) == 2
    assert discovered[0].status == "pending_review"

def test_bulk_assess(manager):
    v1 = manager.register_vendor("A", "a.com", "saas")
    v2 = manager.register_vendor("B", "b.com", "saas")
    results = manager.bulk_assess([v1.vendor_id, v2.vendor_id])
    assert len(results) == 2

def test_get_scorecard(manager):
    v = manager.register_vendor("Acme", "acme.com", "saas")
    a = manager.create_assessment(v.vendor_id)
    manager.submit_assessment(a.assessment_id, {q.question_id: "Yes" for q in a.questions})
    scorecard = manager.get_scorecard(v.vendor_id)
    assert scorecard["latest_score"] == 100.0

def test_migrate_tier(manager):
    v = manager.register_vendor("Acme", "acme.com", "saas")
    updated = manager.migrate_tier(v.vendor_id, "high", "Increased risk profile")
    assert updated.risk_tier == VendorRiskTier.HIGH
    assert updated.risk_score == 75

def test_continuous_monitoring(manager):
    v = manager.register_vendor("Acme", "acme.com", "saas")
    result = manager.continuous_monitoring(v.vendor_id)
    assert v.vendor_id in result
