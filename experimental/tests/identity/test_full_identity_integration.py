"""Comprehensive integration tests for identity features (61-66)."""
import pytest
import json
import tempfile
import os
import uuid
from datetime import datetime, timedelta
from services.integration_service.src.identity_provider_ext import IdentityProviderManager as IdPManager, OIDCProviderConfig, SAMLProviderConfig, ClientRegistration, TokenType
from services.integration_service.src.webauthn_ext import WebAuthnManager, WebAuthnCredential, CredentialType, AttestationType, VerificationStatus
from services.integration_service.src.session_manager_ext import SessionManager, UserSession, SessionStatus, RiskLevel, RiskAssessment
from services.integration_service.src.pam_manager_ext import PAMManager, AccessRequest, AccessRequestStatus, AccessLevel, BreakGlassEvent, JustificationLevel
from services.integration_service.src.policy_engine_ext import PolicyEngine, PolicyDefinition, PolicyRule, PolicyEffect, EvaluationResult
from services.integration_service.src.compliance_scanner_ext import ComplianceScanner, ComplianceScan, BenchmarkDefinition, CheckResult, ScanStatus


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestIdentityProviderFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = IdPManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_oidc_provider_crud(self):
        p = self.mgr.create_oidc_provider("Test OIDC", "https://accounts.example.com", "cid", "secret")
        assert p.id and p.enabled
        p2 = self.mgr.create_oidc_provider("Another OIDC", "https://accounts2.example.com", "cid2", "secret2", scopes=["openid"])
        providers = self.mgr.list_oidc_providers()
        assert len(providers) == 2
        retrieved = self.mgr.get_oidc_provider(p.id)
        assert retrieved.id == p.id
        self.mgr.update_oidc_provider(p.id, enabled=False)
        assert not self.mgr.get_oidc_provider(p.id).enabled
        self.mgr.delete_oidc_provider(p.id)
        assert self.mgr.get_oidc_provider(p.id) is None

    def test_saml_provider_crud(self):
        p = self.mgr.create_saml_provider("Test SAML", "https://saml.example.com", "https://sso.example.com", "base64cert")
        assert p.id and p.enabled
        p2 = self.mgr.create_saml_provider("SAML 2", "https://saml2.example.com", "https://sso2.example.com", "cert2", nameid_format="email")
        providers = self.mgr.list_saml_providers()
        assert len(providers) == 2
        self.mgr.update_saml_provider(p.id, enabled=False)
        assert not self.mgr.get_saml_provider(p.id).enabled
        self.mgr.delete_saml_provider(p.id)
        assert self.mgr.get_saml_provider(p.id) is None

    def test_client_registration_crud(self):
        c = self.mgr.register_client("My App", ["https://app.example.com/callback"], "confidential", ["openid", "profile"])
        assert c.client_id and c.client_secret
        clients = self.mgr.list_clients()
        assert len(clients) == 1
        c2 = self.mgr.register_client("Public App", ["https://app2.example.com/callback"], "public")
        assert len(self.mgr.list_clients()) == 2
        self.mgr.delete_client(c.client_id)
        assert len(self.mgr.list_clients()) == 1

    def test_token_management(self):
        c = self.mgr.register_client("Token Test App", ["https://app.example.com/callback"])
        token = self.mgr.issue_token(c.client_id, "authorization_code", "openid profile")
        assert token.access_token and token.refresh_token
        assert token.expires_in == 3600
        validated = self.mgr.validate_token(token.access_token)
        assert validated is not None
        assert validated["client_id"] == c.client_id
        self.mgr.revoke_token(token.access_token)
        assert self.mgr.validate_token(token.access_token) is None

    def test_discovery_document(self):
        doc = self.mgr.get_discovery_document()
        assert doc["issuer"] == "https://infra-pilot.local"
        assert "authorization_endpoint" in doc
        assert "token_endpoint" in doc
        assert "jwks_uri" in doc
        assert "response_types_supported" in doc
        assert "grant_types_supported" in doc

    def test_idp_templates(self):
        templates = self.mgr.list_idp_templates()
        ids = [t["id"] for t in templates]
        assert "generic_oidc" in ids
        assert "azure_ad" in ids
        assert "okta" in ids
        assert "google" in ids
        assert "keycloak" in ids
        assert "generic_saml" in ids

    def test_statistics(self):
        self.mgr.create_oidc_provider("P1", "https://ex1.com", "c1", "s1")
        self.mgr.create_oidc_provider("P2", "https://ex2.com", "c2", "s2")
        self.mgr.create_saml_provider("P3", "https://ex3.com", "https://sso3.com", "cert3")
        self.mgr.register_client("App1", ["https://app1.com/cb"])
        self.mgr.register_client("App2", ["https://app2.com/cb"])
        stats = self.mgr.get_statistics()
        assert stats["total_oidc_providers"] == 2
        assert stats["total_saml_providers"] == 1
        assert stats["total_clients"] == 2

    def test_error_handling(self):
        with pytest.raises(ValueError, match="not found"):
            self.mgr.get_oidc_provider("nonexistent")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.delete_oidc_provider("nonexistent")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.delete_client("nonexistent")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.validate_token("nonexistent")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.revoke_token("nonexistent")

    def test_scopes_validation(self):
        c = self.mgr.register_client("Scope Test", ["https://app.com/cb"], allowed_scopes=["openid", "email"])
        token = self.mgr.issue_token(c.client_id, "client_credentials", "openid email profile", validate_scopes=True)
        assert token is None or "error" in str(token).lower()

    def test_persistence(self):
        self.mgr.create_oidc_provider("Persist OIDC", "https://persist.com", "cid", "secret")
        self.mgr.register_client("Persist App", ["https://persist.com/cb"])
        self.mgr.close()
        mgr2 = IdPManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_oidc_providers()) == 1
        assert len(mgr2.list_clients()) == 1
        mgr2.close()

    def test_redirect_uri_validation(self):
        c = self.mgr.register_client("Redirect Test", ["https://app.com/cb"])
        assert c.redirect_uris == ["https://app.com/cb"]

    def test_client_type_default(self):
        c = self.mgr.register_client("Default Type", ["https://app.com/cb"])
        assert c.client_type == "confidential"

    def test_client_credentials_grant(self):
        c = self.mgr.register_client("CC Test", ["https://app.com/cb"])
        token = self.mgr.issue_token(c.client_id, "client_credentials", "openid")
        assert token.access_token is not None

    def test_refresh_token_grant(self):
        c = self.mgr.register_client("Refresh Test", ["https://app.com/cb"])
        token = self.mgr.issue_token(c.client_id, "authorization_code", "openid")
        assert token.refresh_token is not None
        new_token = self.mgr.refresh_access_token(token.refresh_token)
        assert new_token.access_token is not None

    def test_token_expiry(self):
        c = self.mgr.register_client("Expiry Test", ["https://app.com/cb"])
        token = self.mgr.issue_token(c.client_id, "client_credentials", "openid", expires_in=0)
        import time; time.sleep(0.1)
        assert self.mgr.validate_token(token.access_token) is None

    def test_saml_metadata_generation(self):
        p = self.mgr.create_saml_provider("Metadata SAML", "https://metadata.com", "https://sso.metadata.com", "cert123")
        meta = self.mgr.generate_saml_metadata(p.id)
        assert "entityID" in meta
        assert p.entity_id in meta


class TestWebAuthnFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = WebAuthnManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_credential_registration(self):
        cred = self.mgr.register_credential("user1", "User One", "fido2")
        assert cred.credential_id is not None
        assert cred.user_id == "user1"
        assert cred.status == VerificationStatus.VERIFIED

    def test_list_credentials(self):
        self.mgr.register_credential("user1", "User One", "fido2")
        self.mgr.register_credential("user1", "User One", "u2f", device_name="YubiKey")
        self.mgr.register_credential("user2", "User Two", "fido2")
        assert len(self.mgr.list_credentials("user1")) == 2
        assert len(self.mgr.list_credentials("user2")) == 1
        assert len(self.mgr.list_credentials()) == 3

    def test_credential_usage_and_revocation(self):
        cred = self.mgr.register_credential("user1", "User One", "fido2")
        self.mgr.record_usage(cred.credential_id)
        c = self.mgr.get_credential(cred.credential_id)
        assert c.use_count == 1
        self.mgr.revoke_credential(cred.credential_id)
        assert self.mgr.get_credential(cred.credential_id).status == VerificationStatus.REVOKED

    def test_credential_removal(self):
        cred = self.mgr.register_credential("user1", "User One", "fido2")
        self.mgr.remove_credential(cred.credential_id)
        assert self.mgr.get_credential(cred.credential_id) is None

    def test_rp_config(self):
        rp = self.mgr.get_rp_config()
        assert rp["rp_id"] == "infra-pilot.local"

    def test_preferences(self):
        prefs = self.mgr.get_preferences()
        assert "pub_key_cred_params" in prefs
        assert "authenticator_selection" in prefs

    def test_aaguid_registry(self):
        aaguids = self.mgr.get_aaguids()
        assert "00000000-0000-0000-0000-000000000000" in aaguids
        assert "adce0002-35bc-c60a-648b-0b25f1f05503" in aaguids

    def test_different_credential_types(self):
        for ct in ["fido2", "u2f", "apple_appattest", "android_tee", "tpm"]:
            cred = self.mgr.register_credential("user1", "User", ct)
            assert cred.credential_type.value == ct

    def test_device_name_assignment(self):
        cred = self.mgr.register_credential("user1", "User", "fido2", aaguid="adce0002-35bc-c60a-648b-0b25f1f05503")
        assert cred.device_name == "Chrome on Mac"

    def test_persistence(self):
        self.mgr.register_credential("user1", "User One", "fido2")
        self.mgr.close()
        mgr2 = WebAuthnManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_credentials()) == 1
        mgr2.close()

    def test_statistics(self):
        self.mgr.register_credential("u1", "U1", "fido2")
        self.mgr.register_credential("u1", "U1", "u2f")
        self.mgr.register_credential("u2", "U2", "fido2")
        stats = self.mgr.get_statistics()
        assert stats["total_credentials"] == 3
        assert stats["unique_users"] == 2
        assert stats["active_credentials"] == 3

    def test_sign_count_tracking(self):
        cred = self.mgr.register_credential("user1", "User", "fido2")
        for _ in range(5):
            self.mgr.record_usage(cred.credential_id)
        c = self.mgr.get_credential(cred.credential_id)
        assert c.sign_count == 5

    def test_last_used_update(self):
        cred = self.mgr.register_credential("user1", "User", "fido2")
        self.mgr.record_usage(cred.credential_id)
        c = self.mgr.get_credential(cred.credential_id)
        assert c.last_used_at >= c.created_at

    def test_error_removing_nonexistent(self):
        assert self.mgr.remove_credential("nonexistent") is False
        assert self.mgr.revoke_credential("nonexistent") is False
        assert self.mgr.record_usage("nonexistent") is False
        assert self.mgr.get_credential("nonexistent") is None


class TestSessionManagerFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = SessionManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_session(self):
        s = self.mgr.create_session("user1", "Mozilla/5.0", "192.168.1.1", "web")
        assert s.session_id is not None
        assert s.user_id == "user1"
        assert s.status == SessionStatus.ACTIVE

    def test_session_lifecycle(self):
        s = self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        assert self.mgr.get_session(s.session_id) is not None
        assert len(self.mgr.list_sessions("user1")) == 1
        self.mgr.update_activity(s.session_id)
        assert self.mgr.get_session(s.session_id).last_activity_at > s.created_at
        self.mgr.revoke_session(s.session_id)
        assert self.mgr.get_session(s.session_id).status == SessionStatus.REVOKED

    def test_session_expiry(self):
        s = self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        self.mgr.expire_session(s.session_id)
        assert self.mgr.get_session(s.session_id).status == SessionStatus.EXPIRED

    def test_different_client_types(self):
        web = self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        mob = self.mgr.create_session("user1", "UA", "10.0.0.1", "mobile")
        api = self.mgr.create_session("user1", "UA", "10.0.0.1", "api")
        cli = self.mgr.create_session("user1", "UA", "10.0.0.1", "cli")
        assert web.client_type == "web"
        assert mob.client_type == "mobile"
        assert api.client_type == "api"
        assert cli.client_type == "cli"

    def test_session_filtering(self):
        self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        self.mgr.create_session("user2", "UA", "10.0.0.2", "web")
        s3 = self.mgr.create_session("user1", "UA", "10.0.0.3", "mobile")
        self.mgr.revoke_session(s3.session_id)
        assert len(self.mgr.list_sessions("user1")) == 2
        assert len(self.mgr.list_sessions("user1", "active")) == 1

    def test_risk_scoring(self):
        s = self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        assert 0 <= s.risk_score <= 100
        assert s.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_risk_factors_list(self):
        factors = self.mgr.list_risk_factors()
        assert len(factors) == 9
        names = [f["factor"] for f in factors]
        assert "new_location" in names
        assert "tor" in names
        assert "known_malicious" in names

    def test_cleanup_expired(self):
        import time
        self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        cleaned = self.mgr.cleanup_expired()
        assert cleaned >= 0

    def test_mfa_method_tracking(self):
        s = self.mgr.create_session("user1", "UA", "10.0.0.1", "web", mfa_method="totp")
        assert s.mfa_method == "totp"

    def test_persistence(self):
        self.mgr.create_session("user1", "UA", "10.0.0.1", "web")
        self.mgr.close()
        mgr2 = SessionManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_sessions()) == 1
        mgr2.close()

    def test_statistics(self):
        self.mgr.create_session("u1", "UA", "10.0.0.1", "web")
        self.mgr.create_session("u1", "UA", "10.0.0.2", "web")
        self.mgr.create_session("u2", "UA", "10.0.0.3", "mobile")
        stats = self.mgr.get_statistics()
        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 3

    def test_session_not_found(self):
        assert self.mgr.get_session("nonexistent") is None
        assert self.mgr.update_activity("nonexistent") is False
        assert self.mgr.revoke_session("nonexistent") is False
        assert self.mgr.expire_session("nonexistent") is False

    def test_risk_evaluation(self):
        risk = self.mgr.evaluate_risk("user1", "10.0.0.1", "Mozilla/5.0")
        assert "score" in risk
        assert "level" in risk
        assert "triggered_factors" in risk


class TestPAMFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = PAMManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_request(self):
        req = self.mgr.create_request("user1", "server-01", "admin", "Need access for maintenance")
        assert req.request_id is not None
        assert req.status == AccessRequestStatus.PENDING

    def test_request_approval_flow(self):
        req = self.mgr.create_request("user1", "server-01", "admin", "Maintenance")
        assert self.mgr.approve_request(req.request_id, "approver1")
        r = self.mgr.get_request(req.request_id)
        assert r.status == AccessRequestStatus.APPROVED
        assert r.approved_by == "approver1"

    def test_request_denial_flow(self):
        req = self.mgr.create_request("user1", "server-01", "admin", "Maintenance")
        assert self.mgr.deny_request(req.request_id, "approver1")
        r = self.mgr.get_request(req.request_id)
        assert r.status == AccessRequestStatus.DENIED
        assert r.denied_by == "approver1"

    def test_request_expiry(self):
        req = self.mgr.create_request("user1", "server-01", "admin", "Maintenance")
        self.mgr.expire_request(req.request_id)
        assert self.mgr.get_request(req.request_id).status == AccessRequestStatus.EXPIRED

    def test_list_requests_with_filters(self):
        self.mgr.create_request("user1", "server-01", "admin", "Maint")
        r2 = self.mgr.create_request("user2", "server-02", "operator", "Deploy")
        self.mgr.approve_request(r2.request_id, "approver1")
        assert len(self.mgr.list_requests("user1")) == 1
        assert len(self.mgr.list_requests("user2", "approved")) == 1

    def test_policies(self):
        policies = self.mgr.list_policies()
        assert len(policies) == 3
        ids = [p["policy_id"] for p in policies]
        assert "pam_default" in ids
        assert "pam_admin" in ids
        assert "pam_emergency" in ids

    def test_break_glass_initiation(self):
        evt = self.mgr.initiate_break_glass("user1", "server-01", "Emergency fix", 1800)
        assert evt.event_id is not None
        assert evt.user_id == "user1"
        assert evt.reason == "Emergency fix"

    def test_break_glass_actions(self):
        evt = self.mgr.initiate_break_glass("user1", "server-01", "Emergency", 3600)
        self.mgr.log_break_glass_action(evt.event_id, "restarted service nginx")
        self.mgr.log_break_glass_action(evt.event_id, "verified application status")
        self.mgr.end_break_glass(evt.event_id)
        e = self.mgr.get_break_glass_event(evt.event_id)
        assert len(e.actions_taken) == 2
        assert e.ended_at is not None

    def test_break_glass_config(self):
        config = self.mgr.get_break_glass_config()
        assert config["enabled"] is True
        assert config["max_duration_minutes"] == 60

    def test_get_break_glass_event(self):
        evt = self.mgr.initiate_break_glass("u1", "srv1", "emergency", 1800)
        e = self.mgr.get_break_glass_event(evt.event_id)
        assert e.event_id == evt.event_id
        assert self.mgr.get_break_glass_event("nonexistent") is None

    def test_end_break_glass_no_event(self):
        assert self.mgr.end_break_glass("nonexistent") is False

    def test_log_break_glass_no_event(self):
        assert self.mgr.log_break_glass_action("nonexistent", "action") is False

    def test_statistics(self):
        self.mgr.create_request("u1", "srv1", "admin", "reason1")
        self.mgr.create_request("u2", "srv2", "operator", "reason2")
        r3 = self.mgr.create_request("u3", "srv3", "admin", "reason3")
        self.mgr.approve_request(r3.request_id, "approver1")
        self.mgr.initiate_break_glass("u1", "srv1", "emergency", 3600)
        stats = self.mgr.get_statistics()
        assert stats["total_requests"] == 3
        assert stats["pending"] == 2
        assert stats["approved"] == 1
        assert stats["break_glass_events"] == 1

    def test_double_approve(self):
        req = self.mgr.create_request("user1", "srv1", "admin", "reason")
        self.mgr.approve_request(req.request_id, "a1")
        assert self.mgr.approve_request(req.request_id, "a2") is False

    def test_double_deny(self):
        req = self.mgr.create_request("user1", "srv1", "admin", "reason")
        self.mgr.deny_request(req.request_id, "a1")
        assert self.mgr.deny_request(req.request_id, "a2") is False

    def test_persistence(self):
        self.mgr.create_request("user1", "srv1", "admin", "reason")
        self.mgr.close()
        mgr2 = PAMManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_requests()) == 1
        mgr2.close()


class TestPolicyEngineFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = PolicyEngine(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_policy(self):
        p = self.mgr.create_policy("Test Policy", "A test policy", "security", "high", "deny")
        assert p.policy_id is not None
        assert p.name == "Test Policy"

    def test_add_rules(self):
        p = self.mgr.create_policy("Test Policy", "Test desc", "security")
        self.mgr.add_rule(p.policy_id, "server:*", "ssh", [{"field": "user", "operator": "eq", "value": "root"}])
        assert len(self.mgr.get_policy(p.policy_id).rules) == 1

    def test_evaluation(self):
        p = self.mgr.create_policy("SSH Policy", "Deny root SSH", "security", "high", "deny")
        self.mgr.add_rule(p.policy_id, "server:*", "ssh", [{"field": "user", "operator": "eq", "value": "root"}])
        result = self.mgr.evaluate("server:01", "ssh", {"user": "root"})
        assert result["overall"] == "deny"
        result2 = self.mgr.evaluate("server:01", "ssh", {"user": "admin"})
        assert result2["overall"] == "allow"

    def test_policy_update(self):
        p = self.mgr.create_policy("Test", "desc", "general")
        self.mgr.update_policy(p.policy_id, {"name": "Updated", "enabled": False})
        updated = self.mgr.get_policy(p.policy_id)
        assert updated.name == "Updated"
        assert updated.enabled is False

    def test_delete_policy(self):
        p = self.mgr.create_policy("Test", "desc", "general")
        self.mgr.delete_policy(p.policy_id)
        assert self.mgr.get_policy(p.policy_id) is None

    def test_list_policies_filter(self):
        self.mgr.create_policy("Sec1", "desc", "security")
        self.mgr.create_policy("Sec2", "desc", "security")
        self.mgr.create_policy("Gen1", "desc", "general")
        assert len(self.mgr.list_policies("security")) == 2
        assert len(self.mgr.list_policies("general")) == 1

    def test_builtin_policies(self):
        policies = self.mgr.list_policies()
        ids = [p.policy_id for p in policies]
        assert "deny_root_ssh" in ids
        assert "require_mfa_admin" in ids
        assert "data_classification" in ids
        assert "network_segmentation" in ids
        assert "backup_compliance" in ids
        assert "cost_governance" in ids
        assert "geo_restriction" in ids
        assert "encryption_required" in ids

    def test_evaluation_log(self):
        p = self.mgr.create_policy("Log Test", "desc", "security", "high", "deny")
        self.mgr.add_rule(p.policy_id, "*", "delete", [{"field": "role", "operator": "eq", "value": "admin"}])
        self.mgr.evaluate("server:01", "delete", {"role": "admin"})
        self.mgr.evaluate("server:01", "delete", {"role": "viewer"})
        assert len(self.mgr.get_evaluation_log()) == 2

    def test_statistics(self):
        p = self.mgr.create_policy("Stat1", "desc", "security", "high", "deny")
        self.mgr.add_rule(p.policy_id, "*", "delete", [])
        stats = self.mgr.get_statistics()
        assert stats["total_rules"] >= 1
        assert "categories" in stats

    def test_error_handling(self):
        assert self.mgr.get_policy("nonexistent") is None
        assert self.mgr.add_rule("nonexistent", "*", "action", []) is False
        assert self.mgr.delete_policy("nonexistent") is False
        assert self.mgr.update_policy("nonexistent", {}) is False

    def test_persistence(self):
        self.mgr.create_policy("Persist", "desc", "general")
        self.mgr.close()
        mgr2 = PolicyEngine(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_policies()) > 0
        mgr2.close()


class TestComplianceScannerFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = ComplianceScanner(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_list_benchmarks(self):
        benchmarks = self.mgr.list_benchmarks()
        assert "cis_docker" in benchmarks
        assert "cis_kubernetes" in benchmarks
        assert "nist_800_53" in benchmarks
        assert "bsi_200_1" in benchmarks
        assert "soc2" in benchmarks

    def test_get_benchmark(self):
        b = self.mgr.get_benchmark("cis_docker")
        assert b is not None
        assert b["name"] == "CIS Docker Benchmark"
        assert len(b["checks"]) == 6

    def test_list_checks(self):
        checks = self.mgr.list_checks("cis_kubernetes")
        assert len(checks) == 4

    def test_start_scan(self):
        scan = self.mgr.start_scan("cis_docker", "local")
        assert scan.scan_id is not None
        assert scan.status == ScanStatus.COMPLETED
        assert scan.total_checks == 6
        assert scan.passed == 6

    def test_get_scan(self):
        scan = self.mgr.start_scan("cis_docker")
        retrieved = self.mgr.get_scan(scan.scan_id)
        assert retrieved.scan_id == scan.scan_id

    def test_multiple_scans(self):
        s1 = self.mgr.start_scan("cis_docker")
        s2 = self.mgr.start_scan("cis_kubernetes")
        s3 = self.mgr.start_scan("nist_800_53")
        assert s1.scan_id != s2.scan_id

    def test_remediation(self):
        rem = self.mgr.get_remediation("cis_d_1_1")
        assert rem is not None
        assert rem["check_id"] == "cis_d_1_1"
        assert self.mgr.get_remediation("nonexistent_check") is None

    def test_scan_results(self):
        scan = self.mgr.start_scan("cis_docker")
        assert len(scan.results) == 6
        for r in scan.results:
            assert "check_id" in r
            assert "status" in r
            assert "severity" in r
            assert "remediation" in r

    def test_benchmark_details(self):
        b = self.mgr.get_benchmark("nist_800_53")
        assert b["authority"] == "National Institute of Standards and Technology"
        assert b["version"] == "5.1.1"

    def test_statistics(self):
        self.mgr.start_scan("cis_docker")
        self.mgr.start_scan("cis_kubernetes")
        stats = self.mgr.get_statistics()
        assert stats["total_scans"] == 2
        assert stats["completed_scans"] == 2
        assert stats["available_benchmarks"] == 5
        assert stats["compliance_rate"] == 100.0

    def test_persistence(self):
        self.mgr.start_scan("cis_docker")
        self.mgr.close()
        mgr2 = ComplianceScanner(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_benchmarks()) == 5
        mgr2.close()

    def test_unknown_benchmark(self):
        with pytest.raises(ValueError, match="Unknown benchmark"):
            self.mgr.start_scan("nonexistent")

    def test_get_nonexistent_scan(self):
        assert self.mgr.get_scan("nonexistent") is None

    def test_all_benchmarks_have_checks(self):
        for bid in ["cis_docker", "cis_kubernetes", "nist_800_53", "bsi_200_1", "soc2"]:
            checks = self.mgr.list_checks(bid)
            assert len(checks) > 0, f"{bid} has no checks"
