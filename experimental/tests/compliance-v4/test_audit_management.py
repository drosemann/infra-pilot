import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.audit_management import (
    AuditManagementEngine,
)

@pytest.fixture
def engine(tmp_path):
    return AuditManagementEngine({"audit_mgmt_data_file": str(tmp_path / "am.json")})

def test_register_customer_right(engine):
    right = engine.register_customer_right("cust-1", "Acme Corp", "SOC_2",
                                            "Full Audit", 365, "CT-001")
    assert right.customer_id == "cust-1"
    assert right.status == "active"
    assert right.audit_frequency_days == 365

def test_schedule_audit(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "Security Controls",
                                   datetime.utcnow() + timedelta(days=30))
    assert sched.audit_type.value == "internal"
    assert sched.status.value == "scheduled"

def test_schedule_audit_with_customer(engine):
    engine.register_customer_right("cust-1", "Acme", "SOC_2", "Full", 365, "CT-001")
    sched = engine.schedule_audit("external", "SOC_2", "Full",
                                   datetime.utcnow() + timedelta(days=30),
                                   customer_id="cust-1", customer_name="Acme")
    assert sched.customer_id == "cust-1"

def test_update_audit_status(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "Scope",
                                   datetime.utcnow() + timedelta(days=30))
    engine.update_audit_status(sched.schedule_id, "in_progress")
    assert sched.status.value == "in_progress"

def test_get_schedules(engine):
    engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    engine.schedule_audit("external", "HIPAA", "S2", datetime.utcnow() + timedelta(days=20))
    schedules = engine.get_schedules()
    assert len(schedules) == 2

def test_get_schedules_by_type(engine):
    engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    engine.schedule_audit("external", "HIPAA", "S2", datetime.utcnow() + timedelta(days=20))
    internal = engine.get_schedules(audit_type="internal")
    assert len(internal) == 1

def test_get_rights(engine):
    engine.register_customer_right("c1", "Acme", "SOC_2", "Full", 365, "CT-1")
    engine.register_customer_right("c2", "Beta", "HIPAA", "Partial", 180, "CT-2")
    rights = engine.get_rights()
    assert len(rights) == 2

def test_get_upcoming_audits(engine):
    engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=5))
    engine.schedule_audit("internal", "HIPAA", "S2", datetime.utcnow() + timedelta(days=60))
    upcoming = engine.get_upcoming_audits(days=30)
    assert len(upcoming) == 1

def test_get_overdue_audits(engine):
    engine.register_customer_right("c1", "Acme", "SOC_2", "Full", 1, "CT-1")
    overdue = engine.get_overdue_audits()
    assert len(overdue) >= 1

def test_get_statistics(engine):
    engine.register_customer_right("c1", "Acme", "SOC_2", "Full", 365, "CT-1")
    engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    stats = engine.get_statistics()
    assert stats["total_rights"] == 1
    assert stats["total_schedules"] == 1

def test_collect_audit_evidence(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    result = engine.collect_audit_evidence(sched.schedule_id)
    assert result["status"] == "collected"

def test_generate_audit_report(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    report = engine.generate_audit_report(sched.schedule_id, "All controls reviewed")
    assert report["status"] == "draft"
    assert report["summary"]["controls_reviewed"] == 24

def test_track_remediation(engine):
    result = engine.track_remediation("finding-1", "in_progress", "user@example.com")
    assert result["status"] == "in_progress"
    assert result["assigned_to"] == "user@example.com"

def test_workflow_action(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    result = engine.workflow_action(sched.schedule_id, "start", "auditor@example.com")
    assert result["new_status"] == "in_progress"

def test_workflow_complete(engine):
    sched = engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    result = engine.workflow_action(sched.schedule_id, "complete")
    assert result["new_status"] == "completed"

def test_get_customer_portal_status(engine):
    engine.register_customer_right("cust-1", "Acme Corp", "SOC_2", "Full", 365, "CT-001")
    status = engine.get_customer_portal_status("cust-1")
    assert status["customer_id"] == "cust-1"
    assert status["active_rights"] == 1

def test_sync_calendar(engine):
    engine.schedule_audit("internal", "SOC_2", "S1", datetime.utcnow() + timedelta(days=10))
    result = engine.sync_calendar()
    assert result["events_synced"] >= 1
