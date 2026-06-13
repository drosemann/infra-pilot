"""Tests for PAM (Privileged Access Management) Manager."""
import pytest
import time
from datetime import datetime, timedelta
from pam_manager import (
    PAMManager, AccessRequest, AccessApproval, BreakGlassAccess,
    SessionRecording, JustInTimeRequest, ApprovalWorkflow
)


@pytest.fixture
def manager():
    return PAMManager({
        "request_ttl": 3600,
        "max_session_duration": 14400,
        "break_glass_cooldown": 86400,
        "require_approval": True,
        "recording_enabled": True,
        "approval_threshold": 1
    })


class TestAccessRequest:
    def test_create_request(self, manager):
        req = manager.create_request(
            user_id="user-001",
            resource="prod-db-01",
            role="db_admin",
            reason="Need to fix replication lag",
            duration=3600,
            ip_address="10.0.0.1"
        )
        assert req.request_id is not None
        assert req.user_id == "user-001"
        assert req.resource == "prod-db-01"
        assert req.role == "db_admin"
        assert req.status == "pending"

    def test_get_request(self, manager):
        original = manager.create_request("user-001", "server-01", "admin", "Maintenance", 3600)
        retrieved = manager.get_request(original.request_id)
        assert retrieved.request_id == original.request_id

    def test_get_missing_request(self, manager):
        assert manager.get_request("nonexistent") is None

    def test_list_user_requests(self, manager):
        manager.create_request("user-001", "res-1", "role-1", "Reason 1", 3600)
        manager.create_request("user-001", "res-2", "role-2", "Reason 2", 7200)
        manager.create_request("user-002", "res-3", "role-1", "Reason 3", 3600)
        user_reqs = manager.list_requests(user_id="user-001")
        assert len(user_reqs) == 2

    def test_list_requests_by_status(self, manager):
        r1 = manager.create_request("user-001", "res-1", "admin", "Reason", 3600)
        r2 = manager.create_request("user-002", "res-2", "admin", "Reason", 3600)
        manager.approve_request(r1.request_id, "approver-1")
        pending = manager.list_requests(status="pending")
        assert len(pending) >= 1
        for p in pending:
            assert p.status == "pending"

    def test_cancel_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Cancelling", 3600)
        assert manager.cancel_request(req.request_id) is True
        assert req.status == "cancelled"

    def test_cancel_approved_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Testing", 3600)
        manager.approve_request(req.request_id, "approver-1")
        assert manager.cancel_request(req.request_id) is False


class TestApprovalWorkflow:
    def test_approve_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Approval test", 3600)
        approval = manager.approve_request(req.request_id, "approver-1", "Looks good")
        assert approval is not None
        assert req.status == "approved"
        assert approval.approver_id == "approver-1"

    def test_deny_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Denial test", 3600)
        approval = manager.deny_request(req.request_id, "approver-1", "Not authorized")
        assert approval is not None
        assert req.status == "denied"
        assert approval.reason == "Not authorized"

    def test_multi_approval_required(self, manager):
        manager.config["approval_threshold"] = 2
        req = manager.create_request("user-001", "res-1", "admin", "Multi approval", 3600)
        manager.approve_request(req.request_id, "approver-1")
        assert req.status == "pending_approval"
        manager.approve_request(req.request_id, "approver-2")
        assert req.status == "approved"

    def test_approval_self_not_allowed(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Self app test", 3600)
        approval = manager.approve_request(req.request_id, "user-001")
        assert approval is None
        assert req.status == "pending"

    def test_approve_expired_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Expired test", 3600)
        req.created_at = datetime.utcnow() - timedelta(hours=2)
        approval = manager.approve_request(req.request_id, "approver-1")
        assert approval is None


class TestJustInTimeAccess:
    def test_activate_jit(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "JIT test", 3600)
        manager.approve_request(req.request_id, "approver-1")
        jit = manager.activate_jit_access(req.request_id, "10.0.0.1")
        assert jit is not None
        assert jit.status == "active"
        assert req.jit_activated is True

    def test_deactivate_jit(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "JIT deact", 3600)
        manager.approve_request(req.request_id, "approver-1")
        jit = manager.activate_jit_access(req.request_id, "10.0.0.1")
        assert manager.deactivate_jit_access(jit.jit_id) is True
        assert jit.status == "expired"

    def test_activate_unapproved_request(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "No approval", 3600)
        jit = manager.activate_jit_access(req.request_id, "10.0.0.1")
        assert jit is None

    def test_activate_expired_jit(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Exp JIT", 3600)
        manager.approve_request(req.request_id, "approver-1")
        jit = manager.activate_jit_access(req.request_id, "10.0.0.1")
        jit.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert jit.is_expired is True

    def test_get_active_jit_sessions(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Active JITs", 3600)
        manager.approve_request(req.request_id, "approver-1")
        manager.activate_jit_access(req.request_id, "10.0.0.1")
        req2 = manager.create_request("user-001", "res-2", "admin", "More JIT", 3600)
        manager.approve_request(req2.request_id, "approver-1")
        manager.activate_jit_access(req2.request_id, "10.0.0.2")
        sessions = manager.get_active_jit_sessions("user-001")
        assert len(sessions) >= 2


class TestBreakGlassAccess:
    def test_trigger_break_glass(self, manager):
        bg = manager.trigger_break_glass("user-001", "prod-critical-01", "root", "Production down!", "10.0.0.1")
        assert bg is not None
        assert bg.access_id is not None
        assert bg.user_id == "user-001"
        assert bg.resource == "prod-critical-01"
        assert bg.status == "active"
        assert bg.incident_reported is True

    def test_break_glass_auto_revoke(self, manager):
        bg = manager.trigger_break_glass("user-001", "critical-01", "root", "Emergency!", "10.0.0.1")
        bg.expires_at = datetime.utcnow() + timedelta(minutes=30)
        assert bg.time_remaining.total_seconds() > 0

    def test_revoke_break_glass(self, manager):
        bg = manager.trigger_break_glass("user-001", "critical-01", "root", "Emergency!", "10.0.0.1")
        assert manager.revoke_break_glass(bg.access_id) is True
        assert bg.status == "revoked"

    def test_get_break_glass_history(self, manager):
        manager.trigger_break_glass("user-001", "critical-01", "root", "Emergency 1", "10.0.0.1")
        manager.trigger_break_glass("user-002", "critical-02", "root", "Emergency 2", "10.0.0.2")
        history = manager.get_break_glass_history()
        assert len(history) >= 2

    def test_break_glass_cooldown(self, manager):
        manager.trigger_break_glass("user-001", "critical-01", "root", "First", "10.0.0.1")
        bg2 = manager.trigger_break_glass("user-001", "critical-01", "root", "Second", "10.0.0.1")
        assert bg2 is None

    def test_break_glass_notification(self, manager):
        bg = manager.trigger_break_glass("user-001", "critical-01", "root", "Notif test", "10.0.0.1")
        notif = manager.notify_break_glass(bg.access_id)
        assert notif is True


class TestSessionRecording:
    def test_start_recording(self, manager):
        recording = manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        assert recording is not None
        assert recording.session_id is not None
        assert recording.status == "recording"

    def test_write_to_recording(self, manager):
        recording = manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        result = manager.write_recording(recording.session_id, "ls -la\n", "input")
        assert result is True
        result2 = manager.write_recording(recording.session_id, "total 42\n", "output")
        assert result2 is True

    def test_stop_recording(self, manager):
        recording = manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        assert manager.stop_recording(recording.session_id) is True
        assert recording.status == "completed"
        assert recording.ended_at is not None

    def test_get_recording(self, manager):
        recording = manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        manager.write_recording(recording.session_id, "command1\n", "input")
        manager.write_recording(recording.session_id, "output1\n", "output")
        manager.stop_recording(recording.session_id)
        playback = manager.get_recording(recording.session_id)
        assert playback is not None
        assert len(playback["events"]) >= 2

    def test_get_user_recordings(self, manager):
        manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        manager.start_recording("user-001", "server-02", "rdp", "10.0.0.2")
        recordings = manager.get_user_recordings("user-001")
        assert len(recordings) >= 2

    def test_recording_format(self, manager):
        recording = manager.start_recording("user-001", "server-01", "ssh", "10.0.0.1")
        manager.write_recording(recording.session_id, "sudo rm -rf /\n", "input")
        manager.stop_recording(recording.session_id)
        playback = manager.get_recording(recording.session_id)
        assert "format" in playback
        assert playback["format"] == "asciicast"
        assert "version" in playback
        assert playback["version"] == 2


class TestExpirationAndCleanup:
    def test_cleanup_expired_requests(self, manager):
        for i in range(5):
            req = manager.create_request(f"user-{i}", f"res-{i}", "admin", "Cleanup test", 3600)
            req.created_at = datetime.utcnow() - timedelta(hours=48)
            req.status = "pending"
        cleaned = manager.cleanup_expired_requests()
        assert cleaned >= 5

    def test_cleanup_expired_sessions(self, manager):
        req = manager.create_request("user-001", "res-1", "admin", "Session cleanup", 3600)
        manager.approve_request(req.request_id, "approver-1")
        jit = manager.activate_jit_access(req.request_id, "10.0.0.1")
        jit.expires_at = datetime.utcnow() - timedelta(hours=24)
        cleaned = manager.cleanup_expired_sessions()
        assert cleaned >= 1
        assert jit.status == "expired"
