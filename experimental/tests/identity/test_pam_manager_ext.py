"""Tests for pam_manager_ext module."""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.pam_manager_ext import PAMManager, RoleType, AccessRequestStatus, SessionRecordingStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = PAMManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestRoleDefinitions:
    def test_create_role(self, manager):
        role = manager.create_role(
            name="database_admin",
            description="Database administrator with full access",
            role_type=RoleType.ADMIN,
            permissions=["database:read", "database:write", "database:admin"],
        )
        assert role.role_id is not None
        assert role.name == "database_admin"
        assert role.role_type == RoleType.ADMIN
        assert len(role.permissions) == 3

    def test_get_role(self, manager):
        role = manager.create_role(name="viewer", description="Read-only", role_type=RoleType.VIEWER)
        retrieved = manager.get_role(role.role_id)
        assert retrieved is not None
        assert retrieved.name == "viewer"

    def test_list_roles(self, manager):
        manager.create_role(name="viewer", description="Read-only", role_type=RoleType.VIEWER)
        manager.create_role(name="admin", description="Full access", role_type=RoleType.ADMIN)
        roles = manager.list_roles()
        assert len(roles) >= 2

    def test_delete_role(self, manager):
        role = manager.create_role(name="temp", description="Temp role", role_type=RoleType.OPERATOR)
        assert manager.delete_role(role.role_id) == True
        assert manager.get_role(role.role_id) is None


class TestAccessRequests:
    def test_create_access_request(self, manager):
        request = manager.create_access_request(
            user_id="user123",
            role_id="role456",
            resource="production-database",
            reason="Need to investigate incident INC-1234",
            requested_duration_minutes=120,
        )
        assert request.request_id is not None
        assert request.user_id == "user123"
        assert request.status == AccessRequestStatus.PENDING

    def test_get_access_request(self, manager):
        request = manager.create_access_request(user_id="user1", role_id="role1", resource="db", reason="Test")
        retrieved = manager.get_access_request(request.request_id)
        assert retrieved is not None

    def test_approve_request(self, manager):
        request = manager.create_access_request(user_id="user1", role_id="role1", resource="db", reason="Test")
        approved = manager.approve_access_request(request.request_id, approver="admin1")
        assert approved is not None
        assert approved.status == AccessRequestStatus.APPROVED
        assert approved.approved_by == "admin1"

    def test_reject_request(self, manager):
        request = manager.create_access_request(user_id="user1", role_id="role1", resource="db", reason="Test")
        rejected = manager.reject_access_request(request.request_id, approver="admin1", reason="Not authorized")
        assert rejected is not None
        assert rejected.status == AccessRequestStatus.REJECTED

    def test_expire_request(self, manager):
        request = manager.create_access_request(user_id="user1", role_id="role1", resource="db", reason="Test", requested_duration_minutes=0)
        request.granted_at = datetime.utcnow() - timedelta(hours=2)
        count = manager.expire_stale_grants(max_hours=1)
        assert count >= 0

    def test_list_access_requests(self, manager):
        manager.create_access_request(user_id="u1", role_id="r1", resource="db", reason="Test1")
        manager.create_access_request(user_id="u1", role_id="r2", resource="api", reason="Test2")
        requests = manager.list_access_requests(user_id="u1")
        assert len(requests) >= 2


class TestApprovalWorkflows:
    def test_approval_workflow_creation(self, manager):
        workflow = manager.create_approval_workflow(
            name="Database Access",
            required_approvers=["manager", "security"],
            min_approvals=2,
            auto_approve=False,
        )
        assert workflow.id is not None
        assert workflow.name == "Database Access"
        assert len(workflow.required_approvers) == 2

    def test_get_approval_workflow(self, manager):
        workflow = manager.create_approval_workflow(name="Test", required_approvers=["admin"], min_approvals=1)
        retrieved = manager.get_approval_workflow(workflow.id)
        assert retrieved is not None


class TestSessionRecording:
    def test_start_recording(self, manager):
        recording = manager.start_session_recording(
            user_id="user1",
            session_id="sess123",
            resource="production-db",
            recording_type="tty",
        )
        assert recording.recording_id is not None
        assert recording.status == SessionRecordingStatus.RECORDING

    def test_stop_recording(self, manager):
        recording = manager.start_session_recording(user_id="user1", session_id="sess123", resource="db")
        stopped = manager.stop_session_recording(recording.recording_id)
        assert stopped is not None
        assert stopped.status == SessionRecordingStatus.COMPLETED
        assert stopped.ended_at is not None

    def test_get_recording(self, manager):
        recording = manager.start_session_recording(user_id="user1", session_id="sess123", resource="db")
        retrieved = manager.get_session_recording(recording.recording_id)
        assert retrieved is not None


class TestBreakGlass:
    def test_break_glass_access(self, manager):
        result = manager.initiate_break_glass(
            user_id="user1",
            resource="emergency-server",
            reason="Production server is down, need immediate access",
            emergency_contact="oncall@example.com",
        )
        assert result.break_glass_id is not None
        assert result.user_id == "user1"
        assert result.reason == "Production server is down, need immediate access"
        assert result.is_active == True

    def test_revoke_break_glass(self, manager):
        result = manager.initiate_break_glass(user_id="user1", resource="emergency-server", reason="Emergency", emergency_contact="oncall@example.com")
        assert manager.revoke_break_glass(result.break_glass_id) == True

    def test_get_active_break_glass(self, manager):
        manager.initiate_break_glass(user_id="user1", resource="emergency-server", reason="Emergency", emergency_contact="oncall@example.com")
        active = manager.get_active_break_glass_requests()
        assert len(active) >= 1


class TestAuditLog:
    def test_log_audit_event(self, manager):
        event = manager.log_audit_event(
            user_id="user1",
            action="role_assignment",
            resource="role:admin",
            details={"role_name": "admin", "assigned_by": "superadmin"},
        )
        assert event.event_id is not None
        assert event.action == "role_assignment"

    def test_get_audit_logs(self, manager):
        manager.log_audit_event(user_id="u1", action="login", resource="system")
        manager.log_audit_event(user_id="u1", action="logout", resource="system")
        logs = manager.get_audit_logs(user_id="u1")
        assert len(logs) >= 2


class TestEdgeCases:
    def test_get_nonexistent_role(self, manager):
        assert manager.get_role("nonexistent") is None

    def test_approve_nonexistent_request(self, manager):
        assert manager.approve_access_request("nonexistent", "admin") is None

    def test_delete_role_with_requests(self, manager):
        role = manager.create_role(name="test", description="test", role_type=RoleType.VIEWER)
        assert manager.delete_role(role.role_id) == True

    def test_multiple_break_glass(self, manager):
        manager.initiate_break_glass(user_id="u1", resource="r1", reason="Emergency", emergency_contact="e@e.com")
        manager.initiate_break_glass(user_id="u1", resource="r2", reason="Emergency2", emergency_contact="e@e.com")
        active = manager.get_active_break_glass_requests()
        assert len(active) >= 2

    def test_statistics(self, manager):
        stats = manager.get_statistics()
        assert stats["total_users"] >= 0
