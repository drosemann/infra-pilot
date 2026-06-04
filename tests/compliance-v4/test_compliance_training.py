import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.compliance_training import (
    ComplianceTrainingManager, TrainingStatus,
)

@pytest.fixture
def manager(tmp_path):
    return ComplianceTrainingManager({"training_data_file": str(tmp_path / "ct.json")})

def test_get_modules(manager):
    modules = manager.get_modules()
    assert len(modules) >= 7

def test_get_modules_by_framework(manager):
    gdpr = manager.get_modules(framework="GDPR")
    assert len(gdpr) >= 1
    for m in gdpr:
        assert m.framework == "GDPR"

def test_assign_training(manager):
    modules = manager.get_modules()
    mod = modules[0]
    assignment = manager.assign_training("user-1", "Alice", mod.module_id)
    assert assignment.user_id == "user-1"
    assert assignment.status == TrainingStatus.NOT_STARTED

def test_assign_inactive_module(manager):
    modules = manager.get_modules()
    mod = modules[0]
    mod.status = "inactive"
    with pytest.raises(ValueError):
        manager.assign_training("user-1", "Alice", mod.module_id)

def test_start_assignment(manager):
    modules = manager.get_modules()
    mod = modules[0]
    assignment = manager.assign_training("user-1", "Alice", mod.module_id)
    started = manager.start_assignment(assignment.assignment_id)
    assert started.status == TrainingStatus.IN_PROGRESS
    assert started.started_at is not None

def test_submit_quiz_pass(manager):
    modules = manager.get_modules()
    mod = modules[0]
    assignment = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(assignment.assignment_id)
    answers = {q.question_id: q.correct_answer for q in mod.questions}
    submitted = manager.submit_quiz(assignment.assignment_id, answers)
    assert submitted.status == TrainingStatus.COMPLETED
    assert submitted.score == len(mod.questions)

def test_submit_quiz_fail(manager):
    modules = manager.get_modules()
    mod = modules[0]
    assignment = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(assignment.assignment_id)
    wrong_answers = {q.question_id: "Wrong answer" for q in mod.questions}
    submitted = manager.submit_quiz(assignment.assignment_id, wrong_answers)
    assert submitted.status == TrainingStatus.FAILED

def test_get_assignments(manager):
    modules = manager.get_modules()
    mod = modules[0]
    manager.assign_training("user-1", "Alice", mod.module_id)
    assignments = manager.get_assignments()
    assert len(assignments) == 1

def test_get_assignments_by_user(manager):
    modules = manager.get_modules()
    mod = modules[0]
    manager.assign_training("user-1", "Alice", mod.module_id)
    manager.assign_training("user-2", "Bob", mod.module_id)
    user1 = manager.get_assignments(user_id="user-1")
    assert len(user1) == 1

def test_get_certifications(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    answers = {q.question_id: q.correct_answer for q in mod.questions}
    manager.submit_quiz(a.assignment_id, answers)
    certs = manager.get_certifications()
    assert len(certs) == 1

def test_get_certifications_by_user(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    manager.submit_quiz(a.assignment_id, {q.question_id: q.correct_answer for q in mod.questions})
    certs = manager.get_certifications(user_id="user-1")
    assert len(certs) == 1

def test_check_expirations(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    manager.submit_quiz(a.assignment_id, {q.question_id: q.correct_answer for q in mod.questions})
    cert = list(manager.certifications.values())[0]
    cert.expires_at = datetime.utcnow() - timedelta(days=1)
    expired = manager.check_expirations()
    assert len(expired) >= 1

def test_get_expiring_soon(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    manager.submit_quiz(a.assignment_id, {q.question_id: q.correct_answer for q in mod.questions})
    expiring = manager.get_expiring_soon(days=365)
    assert len(expiring) >= 1

def test_mark_reminder_sent(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    manager.submit_quiz(a.assignment_id, {q.question_id: q.correct_answer for q in mod.questions})
    cert = list(manager.certifications.values())[0]
    updated = manager.mark_reminder_sent(cert.cert_id)
    assert updated.renewal_reminder_sent is True

def test_get_statistics(manager):
    modules = manager.get_modules()
    mod = modules[0]
    a = manager.assign_training("user-1", "Alice", mod.module_id)
    manager.start_assignment(a.assignment_id)
    manager.submit_quiz(a.assignment_id, {q.question_id: q.correct_answer for q in mod.questions})
    stats = manager.get_statistics()
    assert stats["total_modules"] >= 7
    assert stats["total_assignments"] >= 1
    assert stats["passed"] >= 1
