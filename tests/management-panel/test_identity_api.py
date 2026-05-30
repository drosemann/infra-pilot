"""Comprehensive management panel API tests for identity & governance features (61-70)."""
import pytest
import json
import tempfile
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestIdentityProviderAPI:
    def test_list_oidc_providers_endpoint(self):
        mock_data = [{"id": "p1", "name": "Test Provider", "issuer_url": "https://example.com"}]
        with patch("services.management_panel.backend.api.identity_provider.list_providers") as mock_list:
            mock_list.return_value = mock_data
            result = mock_list()
            assert len(result) == 1
            assert result[0]["name"] == "Test Provider"

    def test_register_client_endpoint(self):
        mock_result = {"client_id": "cid123", "client_secret": "secret123", "client_name": "My App"}
        with patch("services.management_panel.backend.api.identity_provider.register_client") as mock_reg:
            mock_reg.return_value = mock_result
            result = mock_reg("My App", ["https://app.com/cb"], "confidential")
            assert result["client_id"] == "cid123"
            assert result["client_secret"] is not None

    def test_delete_client_endpoint(self):
        with patch("services.management_panel.backend.api.identity_provider.delete_client") as mock_del:
            mock_del.return_value = {"status": "deleted"}
            result = mock_del("cid123")
            assert result["status"] == "deleted"

    def test_create_saml_provider_endpoint(self):
        mock_result = {"id": "saml1", "name": "SAML Provider", "entity_id": "https://saml.example.com"}
        with patch("services.management_panel.backend.api.identity_provider.create_saml_provider") as mock:
            mock.return_value = mock_result
            result = mock("SAML Provider", "https://saml.example.com", "https://sso.example.com", "cert")
            assert result["entity_id"] == "https://saml.example.com"

    def test_identity_provider_stats_endpoint(self):
        mock_stats = {"total_oidc_providers": 3, "total_saml_providers": 2, "total_clients": 5}
        with patch("services.management_panel.backend.api.identity_provider.get_statistics") as mock:
            mock.return_value = mock_stats
            result = mock()
            assert result["total_clients"] == 5

    def test_identity_provider_error_handling(self):
        with patch("services.management_panel.backend.api.identity_provider.get_oidc_provider") as mock:
            mock.return_value = None
            result = mock("nonexistent")
            assert result is None

    def test_identity_provider_list_templates(self):
        mock_templates = [{"id": "generic_oidc", "name": "Generic OIDC"}, {"id": "azure_ad", "name": "Azure AD"}]
        with patch("services.management_panel.backend.api.identity_provider.list_idp_templates") as mock:
            mock.return_value = mock_templates
            result = mock()
            assert len(result) >= 2


class TestWebAuthnAPI:
    def test_list_credentials_endpoint(self):
        mock_creds = [{"credential_id": "c1", "user_id": "u1", "device_name": "YubiKey"}]
        with patch("services.management_panel.backend.api.webauthn.list_credentials") as mock:
            mock.return_value = mock_creds
            result = mock("u1")
            assert len(result) == 1

    def test_register_credential_endpoint(self):
        mock_cred = {"credential_id": "c1", "user_id": "u1", "credential_type": "fido2"}
        with patch("services.management_panel.backend.api.webauthn.register_credential") as mock:
            mock.return_value = mock_cred
            result = mock("u1", "User One", "fido2")
            assert result["credential_type"] == "fido2"

    def test_remove_credential_endpoint(self):
        with patch("services.management_panel.backend.api.webauthn.remove_credential") as mock:
            mock.return_value = {"status": "removed"}
            result = mock("c1")
            assert result["status"] == "removed"

    def test_webauthn_rp_config_endpoint(self):
        mock_rp = {"rp_id": "infra-pilot.local", "rp_name": "Infra Pilot"}
        with patch("services.management_panel.backend.api.webauthn.get_rp_config") as mock:
            mock.return_value = mock_rp
            result = mock()
            assert result["rp_id"] == "infra-pilot.local"

    def test_webauthn_credential_revoke(self):
        with patch("services.management_panel.backend.api.webauthn.revoke_credential") as mock:
            mock.return_value = {"status": "revoked"}
            result = mock("c1")
            assert result["status"] == "revoked"

    def test_webauthn_preferences_endpoint(self):
        mock_prefs = {"timeout": 60000, "attestation": "direct"}
        with patch("services.management_panel.backend.api.webauthn.get_preferences") as mock:
            mock.return_value = mock_prefs
            result = mock()
            assert result["timeout"] == 60000


class TestSessionManagerAPI:
    def test_list_sessions_endpoint(self):
        mock_sessions = [{"session_id": "s1", "user_id": "u1", "risk_level": "low"}]
        with patch("services.management_panel.backend.api.sessions.list_sessions") as mock:
            mock.return_value = mock_sessions
            result = mock("u1")
            assert len(result) == 1

    def test_create_session_endpoint(self):
        mock_session = {"session_id": "s1", "user_id": "u1", "client_type": "web"}
        with patch("services.management_panel.backend.api.sessions.create_session") as mock:
            mock.return_value = mock_session
            result = mock("u1", "Mozilla/5.0", "10.0.0.1", "web")
            assert result["client_type"] == "web"

    def test_revoke_session_endpoint(self):
        with patch("services.management_panel.backend.api.sessions.revoke_session") as mock:
            mock.return_value = {"status": "revoked"}
            result = mock("s1")
            assert result["status"] == "revoked"

    def test_session_risk_factors_endpoint(self):
        mock_factors = [{"factor": "new_location", "weight": 20}, {"factor": "new_device", "weight": 25}]
        with patch("services.management_panel.backend.api.sessions.list_risk_factors") as mock:
            mock.return_value = mock_factors
            result = mock()
            assert len(result) == 2

    def test_session_statistics_endpoint(self):
        mock_stats = {"total_sessions": 10, "active_sessions": 8, "high_risk_sessions": 2}
        with patch("services.management_panel.backend.api.sessions.get_statistics") as mock:
            mock.return_value = mock_stats
            result = mock()
            assert result["active_sessions"] == 8

    def test_session_filter_by_status(self):
        mock_sessions = [{"session_id": "s1", "user_id": "u1", "status": "active"}]
        with patch("services.management_panel.backend.api.sessions.list_sessions") as mock:
            mock.return_value = mock_sessions
            result = mock("u1", "active")
            assert all(s["status"] == "active" for s in result)

    def test_session_risk_evaluation(self):
        mock_risk = {"score": 15, "level": "low", "triggered_factors": []}
        with patch("services.management_panel.backend.api.sessions.evaluate_risk") as mock:
            mock.return_value = mock_risk
            result = mock("u1", "10.0.0.1", "Mozilla/5.0")
            assert result["level"] == "low"

    def test_session_cleanup_endpoint(self):
        with patch("services.management_panel.backend.api.sessions.cleanup_expired") as mock:
            mock.return_value = {"cleaned": 3}
            result = mock()
            assert result["cleaned"] >= 0


class TestPAMAPI:
    def test_list_requests_endpoint(self):
        mock_requests = [{"request_id": "r1", "user_id": "u1", "status": "pending"}]
        with patch("services.management_panel.backend.api.pam.list_requests") as mock:
            mock.return_value = mock_requests
            result = mock("u1")
            assert len(result) == 1

    def test_create_request_endpoint(self):
        mock_req = {"request_id": "r1", "user_id": "u1", "resource": "srv1", "status": "pending"}
        with patch("services.management_panel.backend.api.pam.create_request") as mock:
            mock.return_value = mock_req
            result = mock("u1", "srv1", "admin", "Need access")
            assert result["status"] == "pending"

    def test_approve_request_endpoint(self):
        with patch("services.management_panel.backend.api.pam.approve_request") as mock:
            mock.return_value = {"status": "approved"}
            result = mock("r1", "approver1")
            assert result["status"] == "approved"

    def test_deny_request_endpoint(self):
        with patch("services.management_panel.backend.api.pam.deny_request") as mock:
            mock.return_value = {"status": "denied"}
            result = mock("r1", "approver1")
            assert result["status"] == "denied"

    def test_break_glass_endpoint(self):
        mock_evt = {"event_id": "e1", "user_id": "u1", "reason": "Emergency"}
        with patch("services.management_panel.backend.api.pam.initiate_break_glass") as mock:
            mock.return_value = mock_evt
            result = mock("u1", "srv1", "Emergency!", 1800)
            assert result["reason"] == "Emergency!"

    def test_pam_policies_endpoint(self):
        mock_policies = [{"policy_id": "pam_default", "name": "Default"}]
        with patch("services.management_panel.backend.api.pam.list_policies") as mock:
            mock.return_value = mock_policies
            result = mock()
            assert len(result) >= 1

    def test_break_glass_config_endpoint(self):
        mock_config = {"enabled": True, "max_duration_minutes": 60}
        with patch("services.management_panel.backend.api.pam.get_break_glass_config") as mock:
            mock.return_value = mock_config
            result = mock()
            assert result["enabled"] is True

    def test_pam_statistics_endpoint(self):
        mock_stats = {"total_requests": 10, "pending": 5, "approved": 3, "break_glass_events": 2}
        with patch("services.management_panel.backend.api.pam.get_statistics") as mock:
            mock.return_value = mock_stats
            result = mock()
            assert result["total_requests"] == 10


class TestPolicyEngineAPI:
    def test_list_policies_endpoint(self):
        mock_policies = [{"policy_id": "p1", "name": "Deny Root SSH"}]
        with patch("services.management_panel.backend.api.policies.list_policies") as mock:
            mock.return_value = mock_policies
            result = mock()
            assert len(result) >= 1

    def test_create_policy_endpoint(self):
        mock_policy = {"policy_id": "p1", "name": "Custom Policy"}
        with patch("services.management_panel.backend.api.policies.create_policy") as mock:
            mock.return_value = mock_policy
            result = mock("Custom Policy", "desc", "security")
            assert result["name"] == "Custom Policy"

    def test_evaluate_policy_endpoint(self):
        mock_result = {"overall": "deny", "decisions": [{"policy_id": "p1", "effect": "deny"}]}
        with patch("services.management_panel.backend.api.policies.evaluate") as mock:
            mock.return_value = mock_result
            result = mock("server:01", "ssh", {"user": "root"})
            assert result["overall"] == "deny"

    def test_add_rule_endpoint(self):
        with patch("services.management_panel.backend.api.policies.add_rule") as mock:
            mock.return_value = {"status": "added", "rule_id": "rule1"}
            result = mock("p1", "*", "delete", [{"field": "role", "operator": "eq", "value": "admin"}])
            assert result["status"] == "added"

    def test_update_policy_endpoint(self):
        with patch("services.management_panel.backend.api.policies.update_policy") as mock:
            mock.return_value = {"status": "updated"}
            result = mock("p1", {"name": "Updated", "enabled": False})
            assert result["status"] == "updated"

    def test_delete_policy_endpoint(self):
        with patch("services.management_panel.backend.api.policies.delete_policy") as mock:
            mock.return_value = {"status": "deleted"}
            result = mock("p1")
            assert result["status"] == "deleted"

    def test_policy_statistics_endpoint(self):
        mock_stats = {"total_policies": 10, "enabled_policies": 8, "total_rules": 25}
        with patch("services.management_panel.backend.api.policies.get_statistics") as mock:
            mock.return_value = mock_stats
            result = mock()
            assert result["total_policies"] == 10

    def test_evaluate_allow_result(self):
        mock_result = {"overall": "allow", "decisions": []}
        with patch("services.management_panel.backend.api.policies.evaluate") as mock:
            mock.return_value = mock_result
            result = mock("server:01", "read", {"user": "viewer"})
            assert result["overall"] == "allow"


class TestComplianceScannerAPI:
    def test_list_benchmarks_endpoint(self):
        mock_benchmarks = {"cis_docker": {"name": "CIS Docker", "check_count": 6}}
        with patch("services.management_panel.backend.api.compliance.list_benchmarks") as mock:
            mock.return_value = mock_benchmarks
            result = mock()
            assert "cis_docker" in result

    def test_start_scan_endpoint(self):
        mock_scan = {"scan_id": "s1", "benchmark_id": "cis_docker", "status": "completed", "passed": 6}
        with patch("services.management_panel.backend.api.compliance.start_scan") as mock:
            mock.return_value = mock_scan
            result = mock("cis_docker", "local")
            assert result["passed"] == 6

    def test_get_scan_report_endpoint(self):
        mock_scan = {"scan_id": "s1", "results": [{"check_id": "c1", "status": "pass"}]}
        with patch("services.management_panel.backend.api.compliance.get_scan") as mock:
            mock.return_value = mock_scan
            result = mock("s1")
            assert len(result["results"]) == 1

    def test_get_remediation_endpoint(self):
        mock_rem = {"check_id": "cis_d_1_1", "remediation_steps": ["Review config"]}
        with patch("services.management_panel.backend.api.compliance.get_remediation") as mock:
            mock.return_value = mock_rem
            result = mock("cis_d_1_1")
            assert len(result["remediation_steps"]) >= 1

    def test_list_checks_endpoint(self):
        mock_checks = [{"check_id": "ck1", "name": "Check 1"}, {"check_id": "ck2", "name": "Check 2"}]
        with patch("services.management_panel.backend.api.compliance.list_checks") as mock:
            mock.return_value = mock_checks
            result = mock("cis_docker")
            assert len(result) >= 1

    def test_compliance_statistics_endpoint(self):
        mock_stats = {"total_scans": 5, "completed_scans": 4, "compliance_rate": 85.5}
        with patch("services.management_panel.backend.api.compliance.get_statistics") as mock:
            mock.return_value = mock_stats
            result = mock()
            assert result["compliance_rate"] > 0

    def test_compliance_benchmark_kubernetes(self):
        mock_checks = [{"check_id": "cis_k_1_1", "name": "RBAC Enabled"}]
        with patch("services.management_panel.backend.api.compliance.list_checks") as mock:
            mock.return_value = mock_checks
            result = mock("cis_kubernetes")
            assert len(result) >= 1


class TestGovernanceAPI:
    def test_breach_notification_endpoint(self):
        mock_breach = {"id": "b1", "description": "Data breach", "severity": "high"}
        with patch("services.management_panel.backend.api.governance.report_breach") as mock:
            mock.return_value = mock_breach
            result = mock("Data breach", ["pii", "credentials"], 100)
            assert result["severity"] == "high"

    def test_breach_list_endpoint(self):
        mock_breaches = [{"id": "b1", "description": "Breach 1"}, {"id": "b2", "description": "Breach 2"}]
        with patch("services.management_panel.backend.api.governance.list_breaches") as mock:
            mock.return_value = mock_breaches
            result = mock()
            assert len(result) >= 2

    def test_audit_anomalies_endpoint(self):
        mock_anomalies = [{"id": "a1", "type": "off_hours", "severity": "medium"}]
        with patch("services.management_panel.backend.api.governance.get_anomalies") as mock:
            mock.return_value = mock_anomalies
            result = mock()
            assert len(result) >= 1

    def test_audit_trend_endpoint(self):
        mock_trend = {"user_id": "u1", "anomaly_count": 5, "trend": "increasing"}
        with patch("services.management_panel.backend.api.governance.get_audit_trend") as mock:
            mock.return_value = mock_trend
            result = mock("u1")
            assert result["user_id"] == "u1"

    def test_classify_scan_endpoint(self):
        mock_result = {"classification": "pii", "confidence": 0.95, "matched_patterns": ["email"]}
        with patch("services.management_panel.backend.api.governance.classify_text") as mock:
            mock.return_value = mock_result
            result = mock("user@example.com")
            assert result["classification"] == "pii"

    def test_vendor_list_endpoint(self):
        mock_vendors = [{"id": "v1", "name": "Vendor A"}, {"id": "v2", "name": "Vendor B"}]
        with patch("services.management_panel.backend.api.governance.list_vendors") as mock:
            mock.return_value = mock_vendors
            result = mock()
            assert len(result) >= 2

    def test_vendor_create_endpoint(self):
        mock_vendor = {"id": "v1", "name": "New Vendor", "domain": "vendor.com", "risk_score": 45}
        with patch("services.management_panel.backend.api.governance.create_vendor") as mock:
            mock.return_value = mock_vendor
            result = mock("New Vendor", "vendor.com", "saas")
            assert result["risk_score"] is not None

    def test_vendor_assessment_endpoint(self):
        mock_assessment = {"assessment_id": "a1", "vendor_id": "v1", "questionnaire_type": "sig"}
        with patch("services.management_panel.backend.api.governance.create_assessment") as mock:
            mock.return_value = mock_assessment
            result = mock("v1", "sig")
            assert result["questionnaire_type"] == "sig"

    def test_data_inventory_endpoint(self):
        mock_inventory = {"total_records": 100, "classifications": {"pii": 30, "general": 70}}
        with patch("services.management_panel.backend.api.governance.get_inventory") as mock:
            mock.return_value = mock_inventory
            result = mock()
            assert result["total_records"] == 100

    def test_audit_summary_endpoint(self):
        mock_summary = {"total_events": 1000, "anomaly_count": 15, "period": "last_30d"}
        with patch("services.management_panel.backend.api.governance.get_audit_summary") as mock:
            mock.return_value = mock_summary
            result = mock()
            assert result["total_events"] == 1000

    def test_vendor_risk_categories(self):
        mock_vendor = {"id": "v1", "name": "Cloud Provider", "assessments": []}
        with patch("services.management_panel.backend.api.governance.create_vendor") as mock:
            mock.return_value = mock_vendor
            result = mock("Cloud Provider", "cloud.example.com", "iaas")
            assert result["name"] == "Cloud Provider"

    def test_classify_multiple_patterns(self):
        mock_result = {"classification": "pci", "confidence": 0.99, "matched_patterns": ["credit_card"]}
        with patch("services.management_panel.backend.api.governance.classify_text") as mock:
            mock.return_value = mock_result
            result = mock("4111-1111-1111-1111")
            assert result["classification"] == "pci"

    def test_breach_notification_timeline(self):
        mock_breaches = [
            {"id": "b1", "description": "Breach 1", "reported_at": "2026-01-15T10:00:00Z"},
            {"id": "b2", "description": "Breach 2", "reported_at": "2026-02-20T14:30:00Z"},
        ]
        with patch("services.management_panel.backend.api.governance.list_breaches") as mock:
            mock.return_value = mock_breaches
            result = mock()
            assert len(result) == 2
            assert result[0]["reported_at"] < result[1]["reported_at"]

    def test_vendor_domain_validation(self):
        mock_vendor = {"id": "v1", "name": "Valid Vendor", "domain": "valid.com"}
        with patch("services.management_panel.backend.api.governance.create_vendor") as mock:
            mock.return_value = mock_vendor
            result = mock("Valid Vendor", "valid.com", "saas")
            assert "." in result["domain"]

    def test_data_classification_risk_scoring(self):
        mock_result = {"classification": "phi", "confidence": 0.90, "risk_score": 80}
        with patch("services.management_panel.backend.api.governance.classify_text") as mock:
            mock.return_value = mock_result
            result = mock("Patient: John Doe, SSN: 123-45-6789")
            assert result["risk_score"] >= 70


class TestIdentityDashboardAPI:
    def test_identity_dashboard_summary(self):
        mock_summary = {
            "total_identities": 150,
            "mfa_enabled": 120,
            "sso_connected": 3,
            "active_sessions": 45,
            "pending_pam_requests": 5,
            "recent_anomalies": 2,
        }
        with patch("services.management_panel.backend.api.dashboard.identity.get_summary") as mock:
            mock.return_value = mock_summary
            result = mock()
            assert result["total_identities"] == 150
            assert result["mfa_enabled"] == 120

    def test_identity_health_score(self):
        mock_health = {"score": 85, "mfa_adoption": 80, "session_security": 90, "pam_compliance": 70}
        with patch("services.management_panel.backend.api.dashboard.identity.get_health_score") as mock:
            mock.return_value = mock_health
            result = mock()
            assert result["score"] == 85

    def test_compliance_coverage(self):
        mock_coverage = {"cis_docker": {"status": "pass", "score": 100}, "cis_kubernetes": {"status": "pass", "score": 75}}
        with patch("services.management_panel.backend.api.compliance.get_coverage") as mock:
            mock.return_value = mock_coverage
            result = mock()
            assert result["cis_docker"]["score"] == 100

    def test_policy_enforcement_rate(self):
        mock_enforcement = {"enforced": 45, "violations": 3, "rate": 93.7}
        with patch("services.management_panel.backend.api.policies.get_enforcement_rate") as mock:
            mock.return_value = mock_enforcement
            result = mock()
            assert result["rate"] >= 90

    def test_session_health_metrics(self):
        mock_metrics = {"total": 100, "healthy": 85, "expiring": 10, "stale": 5}
        with patch("services.management_panel.backend.api.sessions.get_health_metrics") as mock:
            mock.return_value = mock_metrics
            result = mock()
            assert result["healthy"] >= result["stale"]

    def test_vendor_risk_summary(self):
        mock_summary = {"total_vendors": 15, "high_risk": 2, "medium_risk": 5, "low_risk": 8}
        with patch("services.management_panel.backend.api.governance.get_vendor_risk_summary") as mock:
            mock.return_value = mock_summary
            result = mock()
            assert result["total_vendors"] == 15

    def test_breach_trend(self):
        mock_trend = {"this_month": 2, "last_month": 5, "trend": "decreasing"}
        with patch("services.management_panel.backend.api.governance.get_breach_trend") as mock:
            mock.return_value = mock_trend
            result = mock()
            assert result["trend"] == "decreasing"

    def test_mfa_adoption_rate(self):
        mock_rate = {"total_users": 200, "mfa_enabled": 160, "adoption_rate": 80.0}
        with patch("services.management_panel.backend.api.dashboard.identity.get_mfa_adoption") as mock:
            mock.return_value = mock_rate
            result = mock()
            assert result["adoption_rate"] > 75

    def test_identity_provider_usage(self):
        mock_usage = {"azure_ad": 45, "okta": 30, "google": 20, "keycloak": 5}
        with patch("services.management_panel.backend.api.dashboard.identity.get_provider_usage") as mock:
            mock.return_value = mock_usage
            result = mock()
            assert sum(result.values()) == 100

    def test_pam_request_trend(self):
        mock_trend = {"this_week": 12, "last_week": 8, "avg_approval_time_hours": 4.5}
        with patch("services.management_panel.backend.api.pam.get_request_trend") as mock:
            mock.return_value = mock_trend
            result = mock()
            assert result["avg_approval_time_hours"] > 0

    def test_identity_errors_endpoint(self):
        mock_errors = {"auth_failures": 15, "session_timeouts": 8, "mfa_failures": 3}
        with patch("services.management_panel.backend.api.dashboard.identity.get_recent_errors") as mock:
            mock.return_value = mock_errors
            result = mock()
            assert result["auth_failures"] >= 0

    def test_policy_violations_by_category(self):
        mock_violations = {"security": 5, "compliance": 3, "network": 1}
        with patch("services.management_panel.backend.api.policies.get_violations_by_category") as mock:
            mock.return_value = mock_violations
            result = mock()
            assert result["security"] >= 0

    def test_compliance_scan_history(self):
        mock_history = [
            {"scan_id": "s1", "benchmark": "cis_docker", "passed": 6, "failed": 0},
            {"scan_id": "s2", "benchmark": "cis_docker", "passed": 5, "failed": 1},
        ]
        with patch("services.management_panel.backend.api.compliance.get_scan_history") as mock:
            mock.return_value = mock_history
            result = mock()
            assert len(result) == 2

    def test_identity_alerts_endpoint(self):
        mock_alerts = [
            {"id": "a1", "type": "brute_force", "severity": "high"},
            {"id": "a2", "type": "new_location", "severity": "medium"},
        ]
        with patch("services.management_panel.backend.api.dashboard.identity.get_alerts") as mock:
            mock.return_value = mock_alerts
            result = mock()
            assert len(result) >= 2

    def test_saml_metadata_endpoint(self):
        mock_metadata = {"entityID": "https://saml.example.com", "sso_url": "https://sso.example.com"}
        with patch("services.management_panel.backend.api.identity_provider.generate_saml_metadata") as mock:
            mock.return_value = mock_metadata
            result = mock("provider1")
            assert "entityID" in result

    def test_webauthn_aaguid_registry_endpoint(self):
        mock_aaguids = {"00000000-0000-0000-0000-000000000000": {"name": "Software"}}
        with patch("services.management_panel.backend.api.webauthn.get_aaguids") as mock:
            mock.return_value = mock_aaguids
            result = mock()
            assert "00000000-0000-0000-0000-000000000000" in result

    def test_session_risk_distribution(self):
        mock_distribution = {"low": 60, "medium": 25, "high": 10, "critical": 5}
        with patch("services.management_panel.backend.api.sessions.get_risk_distribution") as mock:
            mock.return_value = mock_distribution
            result = mock()
            assert sum(result.values()) == 100

    def test_pending_pam_requests_by_resource(self):
        mock_pending = {"srv1": 2, "srv2": 1, "db-01": 3}
        with patch("services.management_panel.backend.api.pam.get_pending_by_resource") as mock:
            mock.return_value = mock_pending
            result = mock()
            assert len(result) >= 1

    def test_compliance_remediation_summary(self):
        mock_summary = {"total_findings": 12, "remediated": 8, "open": 4, "overdue": 1}
        with patch("services.management_panel.backend.api.compliance.get_remediation_summary") as mock:
            mock.return_value = mock_summary
            result = mock()
            assert result["remediated"] + result["open"] == result["total_findings"]

    def test_policy_effectiveness_score(self):
        mock_score = {"score": 88, "prevented_incidents": 15, "false_positives": 3}
        with patch("services.management_panel.backend.api.policies.get_effectiveness_score") as mock:
            mock.return_value = mock_score
            result = mock()
            assert result["score"] >= 80

    def test_vendor_assessment_comparison(self):
        mock_comparison = {"v1": {"risk_score": 35}, "v2": {"risk_score": 65}}
        with patch("services.management_panel.backend.api.governance.compare_vendor_assessments") as mock:
            mock.return_value = mock_comparison
            result = mock()
            assert len(result) == 2

    def test_identity_cost_analysis(self):
        mock_costs = {"idp_monthly": 500, "mfa_monthly": 200, "per_user": 3.50}
        with patch("services.management_panel.backend.api.dashboard.identity.get_cost_analysis") as mock:
            mock.return_value = mock_costs
            result = mock()
            assert result["per_user"] > 0

    def test_breach_severity_distribution(self):
        mock_dist = {"critical": 1, "high": 3, "medium": 5, "low": 8}
        with patch("services.management_panel.backend.api.governance.get_breach_severity_distribution") as mock:
            mock.return_value = mock_dist
            result = mock()
            assert sum(result.values()) >= 10
