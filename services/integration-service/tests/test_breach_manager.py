"""Tests for Breach Notification Manager (GDPR)."""
import pytest
from datetime import datetime, timedelta
from breach_manager import BreachManager, BreachIncident, BreachNotification, BreachTimelineEntry


@pytest.fixture
def manager():
    return BreachManager({
        "notification_authority_within_hours": 72,
        "notification_subject_within_hours": 24,
        "escalation_threshold_hours": 48,
        "max_severity": "critical",
        "auto_escalate": True,
        "jurisdictions": ["GDPR", "CCPA", "LGPD"]
    })


class TestBreachLifecycle:
    def test_report_breach(self, manager):
        breach = manager.report_breach(
            detected_by="soc-analyst-001",
            description="Unauthorized access to production database",
            affected_data_types=["pii", "credentials"],
            affected_users_count=1250,
            suspected_cause="phishing_attack",
            systems_affected=["prod-db-01", "auth-service"]
        )
        assert breach.breach_id is not None
        assert breach.status == "detected"
        assert breach.severity == "critical"
        assert len(breach.affected_data_types) == 2

    def test_get_breach(self, manager):
        original = manager.report_breach("soc-001", "Test breach", ["pii"], 10, "unknown", ["srv-1"])
        retrieved = manager.get_breach(original.breach_id)
        assert retrieved.breach_id == original.breach_id

    def test_get_missing_breach(self, manager):
        assert manager.get_breach("nonexistent") is None

    def test_list_breaches(self, manager):
        manager.report_breach("soc-001", "Breach 1", ["pii"], 100, "phishing", ["srv-1"])
        manager.report_breach("soc-002", "Breach 2", ["phi"], 50, "malware", ["srv-2"])
        breaches = manager.list_breaches()
        assert len(breaches) >= 2

    def test_list_breaches_by_status(self, manager):
        b1 = manager.report_breach("soc-001", "Active breach", ["pii"], 10, "unknown", ["srv-1"])
        b2 = manager.report_breach("soc-002", "Resolved breach", ["pii"], 10, "unknown", ["srv-2"])
        manager.resolve_breach(b2.breach_id, "Root cause fixed", "applied_patch")
        active = manager.list_breaches(status="detected")
        assert len(active) >= 1
        resolved = manager.list_breaches(status="resolved")
        assert len(resolved) >= 1

    def test_update_breach_status(self, manager):
        breach = manager.report_breach("soc-001", "Test breach", ["pii"], 10, "unknown", ["srv-1"])
        assert manager.update_status(breach.breach_id, "investigating") is True
        assert breach.status == "investigating"

    def test_update_breach_severity(self, manager):
        breach = manager.report_breach("soc-001", "Test breach", ["pii"], 10, "unknown", ["srv-1"])
        assert manager.update_severity(breach.breach_id, "high") is True
        assert breach.severity == "high"


class TestContainment:
    def test_contain_breach(self, manager):
        breach = manager.report_breach("soc-001", "Active breach", ["pii"], 200, "ransomware", ["srv-1", "srv-2"])
        actions = ["disconnected_network", "isolated_systems", "disabled_compromised_accounts"]
        result = manager.contain_breach(breach.breach_id, actions, "contained manually")
        assert result is True
        assert breach.status == "contained"
        assert breach.containment_actions == actions

    def test_contain_already_resolved(self, manager):
        breach = manager.report_breach("soc-001", "Old breach", ["pii"], 10, "unknown", ["srv-1"])
        manager.resolve_breach(breach.breach_id, "Fixed", "patch")
        result = manager.contain_breach(breach.breach_id, ["disconnect"], "too late")
        assert result is False


class TestInvestigation:
    def test_add_timeline_entry(self, manager):
        breach = manager.report_breach("soc-001", "Investigation test", ["pii"], 50, "unknown", ["srv-1"])
        entry = manager.add_timeline_entry(
            breach.breach_id,
            "Started forensic analysis",
            "investigation",
            "analyst-001",
            {"tools": ["volatility", "autopsy"]}
        )
        assert entry is not None
        assert entry.description == "Started forensic analysis"
        assert entry.entry_type == "investigation"

    def test_get_timeline(self, manager):
        breach = manager.report_breach("soc-001", "Timeline test", ["pii"], 10, "unknown", ["srv-1"])
        manager.add_timeline_entry(breach.breach_id, "Entry 1", "detection", "soc-001", {})
        manager.add_timeline_entry(breach.breach_id, "Entry 2", "investigation", "analyst-001", {})
        manager.add_timeline_entry(breach.breach_id, "Entry 3", "containment", "responder-001", {})
        timeline = manager.get_timeline(breach.breach_id)
        assert len(timeline) >= 3

    def test_add_evidence(self, manager):
        breach = manager.report_breach("soc-001", "Evidence test", ["pii"], 10, "unknown", ["srv-1"])
        evidence_id = manager.add_evidence(breach.breach_id, "access_logs.txt", "log_file", {"source": "/var/log/auth.log"})
        assert evidence_id is not None

    def test_get_evidence(self, manager):
        breach = manager.report_breach("soc-001", "Evidence get", ["pii"], 10, "unknown", ["srv-1"])
        eid = manager.add_evidence(breach.breach_id, "dump.pcap", "network_capture", {"size": "2GB"})
        evidence = manager.get_evidence(breach.breach_id)
        assert len(evidence) >= 1
        assert evidence[0]["file_name"] == "dump.pcap"


class TestGDPRNotifications:
    def test_notify_authority(self, manager):
        breach = manager.report_breach("soc-001", "GDPR test breach", ["pii"], 500, "phishing", ["srv-1"])
        notification = manager.notify_authority(
            breach.breach_id,
            authority_name="DPA Ireland",
            authority_email="dpa@dataprotection.ie",
            notification_body="We are reporting a personal data breach involving 500 users..."
        )
        assert notification is not None
        assert notification.type == "authority"
        assert notification.recipient_name == "DPA Ireland"
        assert breach.notifications_sent >= 1

    def test_notify_affected_subjects(self, manager):
        breach = manager.report_breach("soc-001", "Subject notification test", ["pii", "email"], 1000, "hack", ["srv-1"])
        notification = manager.notify_subjects(
            breach.breach_id,
            subject_count=1000,
            notification_body="Your personal data may have been compromised...",
            method="email",
            contact_details="affected-users@company.com"
        )
        assert notification is not None
        assert notification.type == "subject"
        assert notification.subject_count == 1000

    def test_gdpr_72_hour_deadline(self, manager):
        breach = manager.report_breach("soc-001", "Deadline test", ["pii"], 100, "attack", ["srv-1"])
        deadline = manager.get_notification_deadline(breach.breach_id)
        assert deadline is not None
        assert deadline > datetime.utcnow()
        assert (deadline - breach.detected_at).total_seconds() <= 72 * 3600

    def test_notification_template_authority(self, manager):
        template = manager.get_notification_template("authority", {
            "breach_id": "BR-001",
            "description": "Data breach",
            "affected_count": 500,
            "date": datetime.utcnow().isoformat()
        })
        assert template is not None
        assert "Art. 33" in template or "personal data breach" in template.lower()

    def test_notification_template_subject(self, manager):
        template = manager.get_notification_template("subject", {
            "breach_id": "BR-002",
            "description": "Credential leak",
            "affected_data": ["passwords", "emails"],
            "date": datetime.utcnow().isoformat()
        })
        assert template is not None
        assert "Art. 34" in template or "personal data" in template.lower()

    def test_notification_history(self, manager):
        breach = manager.report_breach("soc-001", "Notif history", ["pii"], 100, "hack", ["srv-1"])
        manager.notify_authority(breach.breach_id, "DPA", "dpa@dpa.com", "Notification body")
        manager.notify_subjects(breach.breach_id, 100, "Subject body", "email", "users@co.com")
        history = manager.get_notification_history(breach.breach_id)
        assert len(history) >= 2


class TestResolution:
    def test_resolve_breach(self, manager):
        breach = manager.report_breach("soc-001", "Resolvable breach", ["pii"], 10, "unknown", ["srv-1"])
        result = manager.resolve_breach(breach.breach_id, "Root cause identified and patched", "security_patch")
        assert result is True
        assert breach.status == "resolved"
        assert breach.resolution_notes == "Root cause identified and patched"

    def test_generate_report(self, manager):
        breach = manager.report_breach("soc-001", "Reportable breach", ["pii"], 250, "phishing", ["srv-1", "srv-2"])
        manager.add_timeline_entry(breach.breach_id, "Detected", "detection", "soc-001", {})
        manager.add_timeline_entry(breach.breach_id, "Contained", "containment", "responder-001", {})
        manager.add_timeline_entry(breach.breach_id, "Resolved", "resolution", "analyst-001", {})
        report = manager.generate_report(breach.breach_id)
        assert report is not None
        assert "breach_id" in report
        assert "timeline" in report
        assert "affected_data_types" in report


class TestEscalation:
    def test_escalate_if_needed(self, manager):
        breach = manager.report_breach("soc-001", "Escalation test", ["phi"], 5000, "ransomware", ["prod-*"])
        escalated = manager.check_escalation(breach.breach_id)
        assert escalated is True
        assert breach.is_escalated is True

    def test_no_escalation_for_low_severity(self, manager):
        breach = manager.report_breach("soc-001", "Low severity", ["pii"], 5, "user_error", ["srv-1"])
        manager.update_severity(breach.breach_id, "low")
        escalated = manager.check_escalation(breach.breach_id)
        assert escalated is False

    def test_escalation_threshold_check(self, manager):
        breach = manager.report_breach("soc-001", "Time escalation", ["pii"], 100, "unknown", ["srv-1"])
        breach.detected_at = datetime.utcnow() - timedelta(hours=72)
        escalated = manager.check_escalation(breach.breach_id)
        assert escalated is True
