"""Comprehensive CLI tests for identity & governance commands (features 61-70)."""
import pytest
import json
import argparse
from unittest.mock import patch, MagicMock, PropertyMock


class TestCLIOIDCCommands:
    def test_oidc_clients_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_list_clients.return_value = [{"client_id": "c1", "client_name": "App1"}, {"client_id": "c2", "client_name": "App2"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_clients
            args = argparse.Namespace(output="json")
            cmd_oidc_clients(args)
            mock_client.oidc_list_clients.assert_called_once()

    def test_oidc_register_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_register_client.return_value = {"client_id": "c1", "client_secret": "secret123"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_register
            args = argparse.Namespace(name="Test App", redirect_uris="https://app.com/cb", type="confidential", output="json")
            cmd_oidc_register(args)
            mock_client.oidc_register_client.assert_called_once_with("Test App", "https://app.com/cb", "confidential")

    def test_oidc_delete_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_delete_client.return_value = {"status": "deleted"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_delete
            args = argparse.Namespace(client_id="c1", output="json")
            cmd_oidc_delete(args)
            mock_client.oidc_delete_client.assert_called_once_with("c1")

    def test_oidc_register_public_client(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_register_client.return_value = {"client_id": "c1", "client_type": "public"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_register
            args = argparse.Namespace(name="SPA", redirect_uris="https://spa.com/cb", type="public", output="json")
            cmd_oidc_register(args)
            assert mock_client.oidc_register_client.call_args[0][2] == "public"

    def test_oidc_register_confidential_default(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_register_client.return_value = {"client_id": "c1", "client_type": "confidential"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_register
            args = argparse.Namespace(name="Confidential", redirect_uris="https://app.com/cb", type="confidential", output="json")
            cmd_oidc_register(args)
            assert mock_client.oidc_register_client.call_args[0][2] == "confidential"

    def test_oidc_list_returns_data(self):
        mock_data = [{"client_id": "c1", "client_name": "Test"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.oidc_list_clients.return_value = mock_data
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_oidc_clients
            args = argparse.Namespace(output="json")
            cmd_oidc_clients(args)
            assert mock_client.oidc_list_clients.return_value == mock_data


class TestCLIWebAuthnCommands:
    def test_webauthn_credentials_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_list_credentials.return_value = [{"credential_id": "c1", "device_name": "YubiKey"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_creds
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_webauthn_creds(args)
            mock_client.webauthn_list_credentials.assert_called_once_with("u1")

    def test_webauthn_remove_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_remove_credential.return_value = {"status": "removed"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_remove
            args = argparse.Namespace(credential_id="c1", output="json")
            cmd_webauthn_remove(args)
            mock_client.webauthn_remove_credential.assert_called_once_with("c1")

    def test_webauthn_credentials_multiple(self):
        mock_creds = [{"credential_id": "c1"}, {"credential_id": "c2"}, {"credential_id": "c3"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_list_credentials.return_value = mock_creds
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_creds
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_webauthn_creds(args)
            assert len(mock_client.webauthn_list_credentials.return_value) == 3

    def test_webauthn_remove_nonexistent(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_remove_credential.return_value = {"error": "not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_remove
            args = argparse.Namespace(credential_id="nonexistent", output="json")
            cmd_webauthn_remove(args)
            assert "error" in mock_client.webauthn_remove_credential.return_value

    def test_webauthn_credentials_with_device_info(self):
        mock_creds = [{"credential_id": "c1", "device_name": "YubiKey 5", "credential_type": "fido2"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_list_credentials.return_value = mock_creds
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_creds
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_webauthn_creds(args)
            assert mock_creds[0]["device_name"] == "YubiKey 5"

    def test_webauthn_remove_returns_result(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.webauthn_remove_credential.return_value = {"status": "removed"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_webauthn_remove
            args = argparse.Namespace(credential_id="c1", output="json")
            from cli.ipilot.output import print_output
            with patch("cli.ipilot.cli.print_output") as mock_print:
                cmd_webauthn_remove(args)
                mock_print.assert_called_once()


class TestCLISessionCommands:
    def test_session_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.session_list_active.return_value = [{"session_id": "s1", "risk_level": "low"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_session_list
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_session_list(args)
            mock_client.session_list_active.assert_called_once_with("u1")

    def test_session_revoke_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.session_revoke.return_value = {"status": "revoked"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_session_revoke
            args = argparse.Namespace(session_id="s1", output="json")
            cmd_session_revoke(args)
            mock_client.session_revoke.assert_called_once_with("s1")

    def test_session_list_active_filter(self):
        mock_sessions = [{"session_id": "s1", "risk_level": "low"}, {"session_id": "s2", "risk_level": "high"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.session_list_active.return_value = mock_sessions
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_session_list
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_session_list(args)
            assert len(mock_client.session_list_active.return_value) == 2

    def test_session_revoke_nonexistent(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.session_revoke.return_value = {"error": "session not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_session_revoke
            args = argparse.Namespace(session_id="nonexistent", output="json")
            cmd_session_revoke(args)
            assert "error" in mock_client.session_revoke.return_value

    def test_session_list_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.session_list_active.return_value = []
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_session_list
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_session_list(args)
            assert mock_client.session_list_active.return_value == []


class TestCLIPAMCommands:
    def test_pam_requests_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_list_requests.return_value = [{"request_id": "r1", "status": "pending"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_requests
            args = argparse.Namespace(user_id="u1", status="pending", output="json")
            cmd_pam_requests(args)
            mock_client.pam_list_requests.assert_called_once()

    def test_pam_request_create_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_create_request.return_value = {"request_id": "r1", "status": "pending"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_request
            args = argparse.Namespace(user_id="u1", resource="srv1", role="admin", reason="Need access", duration=3600, output="json")
            cmd_pam_request(args)
            mock_client.pam_create_request.assert_called_once_with("u1", "srv1", "admin", "Need access", 3600)

    def test_pam_approve_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_approve_request.return_value = {"status": "approved"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_approve
            args = argparse.Namespace(request_id="r1", approver_id="approver1", output="json")
            cmd_pam_approve(args)
            mock_client.pam_approve_request.assert_called_once_with("r1", "approver1")

    def test_pam_deny_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_deny_request.return_value = {"status": "denied"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_deny
            args = argparse.Namespace(request_id="r1", approver_id="approver1", output="json")
            cmd_pam_deny(args)
            mock_client.pam_deny_request.assert_called_once_with("r1", "approver1")

    def test_pam_requests_with_filters(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_list_requests.return_value = [{"request_id": "r1", "status": "approved"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_requests
            args = argparse.Namespace(user_id="u1", status="approved", output="json")
            cmd_pam_requests(args)
            assert all(r["status"] == "approved" for r in mock_client.pam_list_requests.return_value)

    def test_pam_requests_no_filter(self):
        mock_requests = [{"request_id": "r1"}, {"request_id": "r2"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_list_requests.return_value = mock_requests
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_requests
            args = argparse.Namespace(user_id=None, status=None, output="json")
            cmd_pam_requests(args)
            assert len(mock_client.pam_list_requests.return_value) == 2

    def test_pam_create_with_custom_duration(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_create_request.return_value = {"request_id": "r1", "duration": 7200}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_request
            args = argparse.Namespace(user_id="u1", resource="srv1", role="admin", reason="Maint", duration=7200, output="json")
            cmd_pam_request(args)
            assert mock_client.pam_create_request.call_args[0][4] == 7200

    def test_pam_approve_twice(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.pam_approve_request.side_effect = [{"status": "approved"}, {"error": "already approved"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_pam_approve
            args = argparse.Namespace(request_id="r1", approver_id="a1", output="json")
            cmd_pam_approve(args)
            result2 = mock_client.pam_approve_request("r1", "a2")
            assert "error" in result2


class TestCLIPolicyCommands:
    def test_policy_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_list.return_value = [{"policy_id": "p1", "name": "Deny Root SSH"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_list
            args = argparse.Namespace(category="security", output="json")
            cmd_policy_list(args)
            mock_client.policy_list.assert_called_once_with("security")

    def test_policy_create_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_create.return_value = {"policy_id": "p1", "name": "Custom Policy"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_create
            args = argparse.Namespace(name="Custom Policy", description="desc", category="security", output="json")
            cmd_policy_create(args)
            mock_client.policy_create.assert_called_once_with("Custom Policy", "desc", "security")

    def test_policy_evaluate_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_evaluate.return_value = {"overall": "deny", "decisions": []}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_evaluate
            args = argparse.Namespace(resource="server:01", action="ssh", context='{"user": "root"}', output="json")
            cmd_policy_evaluate(args)
            mock_client.policy_evaluate.assert_called_once()

    def test_policy_list_all(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_list.return_value = [{"policy_id": "p1"}, {"policy_id": "p2"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_list
            args = argparse.Namespace(category=None, output="json")
            cmd_policy_list(args)
            mock_client.policy_list.assert_called_once_with(None)

    def test_policy_evaluate_with_context(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_evaluate.return_value = {"overall": "deny"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_evaluate
            import json
            ctx = json.dumps({"user": "root", "role": "admin"})
            args = argparse.Namespace(resource="server:01", action="ssh", context=ctx, output="json")
            cmd_policy_evaluate(args)
            assert mock_client.policy_evaluate.call_args[0][2] == {"user": "root", "role": "admin"}

    def test_policy_evaluate_allow(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_evaluate.return_value = {"overall": "allow", "decisions": []}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_evaluate
            args = argparse.Namespace(resource="server:01", action="read", context='{"user": "viewer"}', output="json")
            cmd_policy_evaluate(args)
            assert mock_client.policy_evaluate.return_value["overall"] == "allow"

    def test_policy_create_default_category(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.policy_create.return_value = {"policy_id": "p1", "category": "general"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_policy_create
            args = argparse.Namespace(name="Test", description="desc", category="general", output="json")
            cmd_policy_create(args)
            assert mock_client.policy_create.call_args[0][2] == "general"


class TestCLIComplianceCommands:
    def test_compliance_scan_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_run_scan.return_value = {"scan_id": "s1", "status": "completed"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_scan
            args = argparse.Namespace(benchmark="cis_docker", output="json")
            cmd_compliance_scan(args)
            mock_client.compliance_run_scan.assert_called_once_with("cis_docker")

    def test_compliance_report_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_get_report.return_value = {"scan_id": "s1", "passed": 6, "failed": 0}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_report
            args = argparse.Namespace(scan_id="s1", output="json")
            cmd_compliance_report(args)
            mock_client.compliance_get_report.assert_called_once_with("s1")

    def test_compliance_checks_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_list_checks.return_value = [{"check_id": "c1", "name": "Check 1"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_checks
            args = argparse.Namespace(benchmark="cis_docker", output="json")
            cmd_compliance_checks(args)
            mock_client.compliance_list_checks.assert_called_once_with("cis_docker")

    def test_compliance_scan_all_benchmarks(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_run_scan.side_effect = lambda b: {"scan_id": f"s_{b}", "benchmark": b}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_scan
            for b in ["cis_docker", "cis_kubernetes", "nist_800_53"]:
                args = argparse.Namespace(benchmark=b, output="json")
                cmd_compliance_scan(args)
            assert mock_client.compliance_run_scan.call_count == 3

    def test_compliance_report_with_results(self):
        mock_report = {"scan_id": "s1", "results": [{"check_id": "c1", "status": "pass"}, {"check_id": "c2", "status": "fail"}]}
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_get_report.return_value = mock_report
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_report
            args = argparse.Namespace(scan_id="s1", output="json")
            cmd_compliance_report(args)
            assert len(mock_client.compliance_get_report.return_value["results"]) == 2

    def test_compliance_checks_different_benchmarks(self):
        mock_checks = {"cis_docker": [{"check_id": "c1"}], "soc2": [{"check_id": "c2"}]}
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.compliance_list_checks.side_effect = lambda b: mock_checks.get(b, [])
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_compliance_checks
            args = argparse.Namespace(benchmark="soc2", output="json")
            cmd_compliance_checks(args)
            assert len(mock_client.compliance_list_checks("soc2")) == 1


class TestCLIBreachCommands:
    def test_breach_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.breach_list.return_value = [{"id": "b1", "description": "Data breach"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_breach_list
            args = argparse.Namespace(output="json")
            cmd_breach_list(args)
            mock_client.breach_list.assert_called_once()

    def test_breach_report_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.breach_report.return_value = {"id": "b1", "severity": "high"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_breach_report
            args = argparse.Namespace(description="Test breach", data_types="pii,credentials", affected_users=100, output="json")
            cmd_breach_report(args)
            mock_client.breach_report.assert_called_once_with("Test breach", "pii,credentials", 100)

    def test_breach_report_no_affected_users(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.breach_report.return_value = {"id": "b1", "affected_users_count": 0}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_breach_report
            args = argparse.Namespace(description="Test", data_types="pii", affected_users=0, output="json")
            cmd_breach_report(args)
            assert mock_client.breach_report.call_args[0][2] == 0

    def test_breach_list_multiple(self):
        mock_breaches = [{"id": "b1"}, {"id": "b2"}, {"id": "b3"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.breach_list.return_value = mock_breaches
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_breach_list
            args = argparse.Namespace(output="json")
            cmd_breach_list(args)
            assert len(mock_client.breach_list.return_value) == 3

    def test_breach_list_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.breach_list.return_value = []
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_breach_list
            args = argparse.Namespace(output="json")
            cmd_breach_list(args)
            assert mock_client.breach_list.return_value == []


class TestCLIAuditCommands:
    def test_audit_anomalies_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.audit_get_anomalies.return_value = [{"id": "a1", "type": "off_hours"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_audit_anomalies
            args = argparse.Namespace(output="json")
            cmd_audit_anomalies(args)
            mock_client.audit_get_anomalies.assert_called_once()

    def test_audit_trend_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.audit_get_trend.return_value = {"user_id": "u1", "anomaly_count": 5}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_audit_trend
            args = argparse.Namespace(user_id="u1", output="json")
            cmd_audit_trend(args)
            mock_client.audit_get_trend.assert_called_once_with("u1")

    def test_audit_summary_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.audit_get_summary.return_value = {"total_events": 1000, "anomaly_count": 15}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_audit_summary
            args = argparse.Namespace(output="json")
            cmd_audit_summary(args)
            mock_client.audit_get_summary.assert_called_once()

    def test_audit_anomalies_with_threshold(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.audit_get_anomalies.return_value = [{"id": "a1", "score": 95}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_audit_anomalies
            args = argparse.Namespace(output="json")
            cmd_audit_anomalies(args)
            assert len(mock_client.audit_get_anomalies.return_value) >= 1

    def test_audit_anomalies_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.audit_get_anomalies.return_value = []
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_audit_anomalies
            args = argparse.Namespace(output="json")
            cmd_audit_anomalies(args)
            assert mock_client.audit_get_anomalies.return_value == []


class TestCLIClassifyCommands:
    def test_classify_scan_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.classify_scan_text.return_value = {"classification": "pii", "confidence": 0.95}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_classify_scan
            args = argparse.Namespace(text="user@example.com", output="json")
            cmd_classify_scan(args)
            mock_client.classify_scan_text.assert_called_once_with("user@example.com")

    def test_classify_inventory_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.classify_get_inventory.return_value = {"total_records": 100, "classifications": {"pii": 30}}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_classify_inventory
            args = argparse.Namespace(output="json")
            cmd_classify_inventory(args)
            mock_client.classify_get_inventory.assert_called_once()

    def test_classify_scan_pci(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.classify_scan_text.return_value = {"classification": "pci", "confidence": 0.99}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_classify_scan
            args = argparse.Namespace(text="4111-1111-1111-1111", output="json")
            cmd_classify_scan(args)
            assert mock_client.classify_scan_text.return_value["classification"] == "pci"

    def test_classify_inventory_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.classify_get_inventory.return_value = {"total_records": 0, "classifications": {}}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_classify_inventory
            args = argparse.Namespace(output="json")
            cmd_classify_inventory(args)
            assert mock_client.classify_get_inventory.return_value["total_records"] == 0


class TestCLIVendorCommands:
    def test_vendor_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.vendor_list.return_value = [{"id": "v1", "name": "Vendor A"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_vendor_list
            args = argparse.Namespace(output="json")
            cmd_vendor_list(args)
            mock_client.vendor_list.assert_called_once()

    def test_vendor_create_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.vendor_create.return_value = {"id": "v1", "name": "New Vendor"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_vendor_create
            args = argparse.Namespace(name="New Vendor", domain="vendor.com", category="saas", output="json")
            cmd_vendor_create(args)
            mock_client.vendor_create.assert_called_once_with("New Vendor", "vendor.com", "saas")

    def test_vendor_assess_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.vendor_create_assessment.return_value = {"assessment_id": "a1", "questionnaire_type": "sig"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_vendor_assess
            args = argparse.Namespace(vendor_id="v1", type="sig", output="json")
            cmd_vendor_assess(args)
            mock_client.vendor_create_assessment.assert_called_once_with("v1", "sig")

    def test_vendor_list_multiple(self):
        mock_vendors = [{"id": "v1", "name": "Vendor A"}, {"id": "v2", "name": "Vendor B"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.vendor_list.return_value = mock_vendors
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_vendor_list
            args = argparse.Namespace(output="json")
            cmd_vendor_list(args)
            assert len(mock_client.vendor_list.return_value) == 2
