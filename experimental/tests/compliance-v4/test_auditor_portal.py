import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.auditor_portal import (
    AuditorPortalEngine, FindingStatus, AuditStatus,
)

@pytest.fixture
def engine(tmp_path):
    return AuditorPortalEngine({"auditor_data_file": str(tmp_path / "ap.json")})

def test_create_engagement(engine):
    eng = engine.create_engagement("Big4 Audit", "John Auditor", "john@big4.com",
                                    "SOC_2", "full", "Full SOC 2 audit",
                                    datetime.utcnow(), datetime.utcnow() + timedelta(days=30))
    assert eng.auditor_organization == "Big4 Audit"
    assert eng.status == AuditStatus.SCHEDULED

def test_create_session(engine):
    session = engine.create_session("John Auditor", "john@big4.com", "Big4",
                                     "full", ["SOC_2", "HIPAA"])
    assert session.status == "active"
    assert session.permissions["view_evidence"] is True

def test_access_evidence(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    result = engine.access_evidence(session.session_id, "ev_policy_001")
    assert result is not None
    assert "access_record" in result

def test_access_evidence_expired_session(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    session.access_expires_at = datetime.utcnow() - timedelta(hours=1)
    result = engine.access_evidence(session.session_id, "ev_policy_001")
    assert result is None

def test_get_evidence_by_control(engine):
    evidence = engine.get_evidence_by_control("SOC2-CC1")
    assert len(evidence) >= 1

def test_get_all_evidence(engine):
    evidence = engine.get_all_evidence()
    assert len(evidence) >= 15

def test_get_all_evidence_by_framework(engine):
    soc2 = engine.get_all_evidence(framework="SOC_2")
    assert len(soc2) >= 1
    for e in soc2:
        assert e["framework"] == "SOC_2"

def test_control_mapping_by_framework(engine):
    mapping = engine.control_mapping_by_framework("SOC_2")
    assert mapping["framework"] == "SOC_2"
    assert mapping["evidence_count"] > 0

def test_create_finding(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    finding = engine.create_finding(session.session_id, eng.audit_id, "SOC2-CC1",
                                     "SOC_2", "Missing control", "Control not implemented", "high")
    assert finding is not None
    assert finding.severity.value == "high"

def test_create_finding_no_permission(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "read_only", ["SOC_2"])
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    finding = engine.create_finding(session.session_id, eng.audit_id, "SOC2-CC1",
                                     "SOC_2", "Test", "Desc", "medium")
    assert finding is None

def test_update_finding_status(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    finding = engine.create_finding(session.session_id, eng.audit_id, "SOC2-CC1",
                                     "SOC_2", "Finding", "Desc", "critical")
    updated = engine.update_finding_status(finding.finding_id, "acknowledged", "Reviewed")
    assert updated.status == FindingStatus.ACKNOWLEDGED

def test_get_findings(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    engine.create_finding(session.session_id, eng.audit_id, "SOC2-CC1",
                           "SOC_2", "F1", "D1", "high")
    findings = engine.get_findings()
    assert len(findings) >= 1

def test_get_engagements(engine):
    engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                              "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    engagements = engine.get_engagements()
    assert len(engagements) == 1

def test_get_session(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    retrieved = engine.get_session(session.session_id)
    assert retrieved.session_id == session.session_id

def test_expire_session(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    engine.expire_session(session.session_id)
    assert session.status == "expired"

def test_get_evidence_access_log(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    engine.access_evidence(session.session_id, "ev_policy_001")
    log = engine.get_evidence_access_log()
    assert len(log) >= 1

def test_get_evidence_access_log_by_session(engine):
    s1 = engine.create_session("John", "j@c.com", "Big4", "full", ["SOC_2"])
    s2 = engine.create_session("Jane", "j2@c.com", "Big4", "full", ["SOC_2"])
    engine.access_evidence(s1.session_id, "ev_policy_001")
    engine.access_evidence(s2.session_id, "ev_policy_001")
    log = engine.get_evidence_access_log(session_id=s1.session_id)
    for entry in log:
        assert entry.session_id == s1.session_id

def test_get_statistics(engine):
    session = engine.create_session("John", "john@co.com", "Big4", "full", ["SOC_2"])
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    engine.create_finding(session.session_id, eng.audit_id, "SOC2-CC1",
                           "SOC_2", "F1", "D1", "medium")
    stats = engine.get_statistics()
    assert stats["active_sessions"] >= 1
    assert stats["total_findings"] >= 1

def test_complete_engagement(engine):
    eng = engine.create_engagement("Big4", "John", "john@co.com", "SOC_2", "full",
                                    "Audit", datetime.utcnow(), datetime.utcnow()+timedelta(days=30))
    engine.complete_engagement(eng.audit_id, "https://reports.example.com/report.pdf")
    assert eng.status == AuditStatus.COMPLETED
    assert eng.report_url == "https://reports.example.com/report.pdf"
