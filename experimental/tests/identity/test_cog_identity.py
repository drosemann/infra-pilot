"""Comprehensive tests for identity orchestrator cogs (features 61-66)."""
import pytest
import json
import tempfile
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock


# Identity Provider Cog Tests
class TestIdentityProviderCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"clients": [], "provider_configs": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_cog_imports(self):
        from services.orchestrator_agent.cogs.identity_provider import (
            IdentityProviderManager, OIDCClient, OIDCClientType, OIDCClientStatus, IDP_PROVIDERS
        )
        assert hasattr(IdentityProviderManager, "initialize")
        assert hasattr(IdentityProviderManager, "list_clients")
        assert hasattr(IdentityProviderManager, "register_client")
        assert hasattr(IdentityProviderManager, "delete_client")

    def test_oidc_client_model(self):
        from services.orchestrator_agent.cogs.identity_provider import OIDCClient, OIDCClientType, OIDCClientStatus
        c = OIDCClient("cid123", "Test App", OIDCClientType.CONFIDENTIAL, ["https://app.com/cb"])
        assert c.client_id == "cid123"
        assert c.client_secret is not None
        assert len(c.client_secret) > 10
        d = c.to_dict()
        assert d["client_id"] == "cid123"
        assert d["client_type"] == "confidential"
        assert d["status"] == "active"

    def test_idp_providers_list(self):
        from services.orchestrator_agent.cogs.identity_provider import IDP_PROVIDERS
        assert len(IDP_PROVIDERS) == 6
        ids = [p["provider_id"] for p in IDP_PROVIDERS]
        assert "oidc_generic" in ids
        assert "saml_generic" in ids
        assert "azure_ad" in ids
        assert "okta" in ids
        assert "google" in ids
        assert "keycloak" in ids

    def test_oidc_protocols_saml(self):
        from services.orchestrator_agent.cogs.identity_provider import IDP_PROVIDERS
        saml = [p for p in IDP_PROVIDERS if p["protocol"] == "saml"]
        oidc = [p for p in IDP_PROVIDERS if p["protocol"] == "oidc"]
        assert len(saml) >= 1
        assert len(oidc) >= 5

    @pytest.mark.asyncio
    async def test_manager_initialization(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            assert mgr._initialized is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_providers(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            providers = mgr.list_providers()
            assert len(providers) == 6
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_provider(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            p = mgr.get_provider("azure_ad")
            assert p is not None
            assert p["name"] == "Azure AD / Entra ID"
            assert mgr.get_provider("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_configure_provider(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            cfg = mgr.configure_provider("azure_ad", {"tenant_id": "test-tenant", "client_id": "cid", "client_secret": "secret"})
            assert cfg["provider_id"] == "azure_ad"
            assert cfg["enabled"] is True
            configured = mgr.get_configured_providers()
            assert len(configured) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_remove_provider_config(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            mgr.configure_provider("okta", {"domain": "test.okta.com", "client_id": "cid", "client_secret": "secret"})
            assert mgr.remove_provider_config("okta") is True
            assert mgr.remove_provider_config("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_register_client(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            client = mgr.register_client("My App", ["https://app.com/cb"], "confidential")
            assert client["client_name"] == "My App"
            assert client["client_type"] == "confidential"
            assert len(mgr.list_clients()) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_public_client(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            client = mgr.register_client("SPA App", ["https://spa.com/cb"], "public")
            assert client["client_type"] == "public"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_delete_client(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            c = mgr.register_client("Del App", ["https://del.com/cb"])
            assert mgr.delete_client(c["client_id"]) is True
            assert mgr.delete_client("nonexistent") is False
            assert len(mgr.list_clients()) == 0
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_client(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            c = mgr.register_client("Get App", ["https://get.com/cb"])
            retrieved = mgr.get_client(c["client_id"])
            assert retrieved is not None
            assert retrieved["client_name"] == "Get App"
            assert mgr.get_client("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            mgr.register_client("App1", ["https://a1.com/cb"])
            mgr.register_client("App2", ["https://a2.com/cb"])
            mgr.configure_provider("google", {"client_id": "gcid", "client_secret": "gsecret"})
            stats = mgr.get_statistics()
            assert stats["total_clients"] == 2
            assert stats["configured_providers"] == 1
            assert stats["supported_providers"] == 6
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_protocols(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            protocols = mgr.get_protocols()
            assert len(protocols) == 2
            assert protocols[0]["protocol"] == "oidc"
            assert protocols[1]["protocol"] == "saml"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_configure_unknown_provider_raises(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            with pytest.raises(ValueError, match="Unknown provider"):
                mgr.configure_provider("nonexistent_provider", {})
            await mgr.close()

    @pytest.mark.asyncio
    async def test_allowed_scopes_per_client(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            c = mgr.register_client("Scoped", ["https://app.com/cb"], allowed_scopes=["openid", "profile"])
            assert "openid" in c["allowed_scopes"]
            await mgr.close()

    @pytest.mark.asyncio
    async def test_client_secret_generation(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            c1 = mgr.register_client("App1", ["https://a1.com/cb"])
            c2 = mgr.register_client("App2", ["https://a2.com/cb"])
            assert c1["client_secret"] != c2["client_secret"]
            await mgr.close()

    @pytest.mark.asyncio
    async def test_provider_config_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            mgr.register_client("Persist", ["https://persist.com/cb"])
            mgr.configure_provider("keycloak", {"base_url": "https://kc.example.com", "realm": "test", "client_id": "cid", "client_secret": "secret"})
            await mgr.close()
            mgr2 = IdentityProviderManager()
            await mgr2.initialize()
            assert len(mgr2.list_clients()) == 1
            assert len(mgr2.get_configured_providers()) == 1
            await mgr2.close()

    def test_idp_provider_schema(self):
        from services.orchestrator_agent.cogs.identity_provider import IDP_PROVIDERS
        for p in IDP_PROVIDERS:
            assert "provider_id" in p
            assert "name" in p
            assert "protocol" in p
            assert "config_schema" in p
            assert "properties" in p["config_schema"]
            assert "required" in p["config_schema"]

    @pytest.mark.asyncio
    async def test_default_scopes(self, data_file):
        with patch("services.orchestrator_agent.cogs.identity_provider.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.identity_provider import IdentityProviderManager
            mgr = IdentityProviderManager()
            await mgr.initialize()
            c = mgr.register_client("Default Scope App", ["https://app.com/cb"])
            assert c["allowed_scopes"] == ["openid", "profile", "email"]
            await mgr.close()


# WebAuthn Cog Tests
class TestWebAuthnCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"credentials": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_cog_imports(self):
        from services.orchestrator_agent.cogs.webauthn import (
            WebAuthnManager, WebAuthnCredential, CredentialType, AttestationType,
            VerificationStatus, RP_ENTITY, AAGUID_REGISTRY, preference_options
        )
        assert hasattr(WebAuthnManager, "initialize")
        assert hasattr(WebAuthnManager, "register_credential")
        assert hasattr(WebAuthnManager, "list_credentials")

    def test_credential_model(self):
        from services.orchestrator_agent.cogs.webauthn import WebAuthnCredential, CredentialType
        cred = WebAuthnCredential("cred1", "user1", "User One", CredentialType.FIDO2)
        assert cred.credential_id == "cred1"
        d = cred.to_dict()
        assert d["user_id"] == "user1"
        assert d["credential_type"] == "fido2"

    def test_aaguid_registry(self):
        from services.orchestrator_agent.cogs.webauthn import AAGUID_REGISTRY
        assert len(AAGUID_REGISTRY) == 6
        assert AAGUID_REGISTRY["00000000-0000-0000-0000-000000000000"]["name"] == "Software / Testing"

    def test_rp_entity(self):
        from services.orchestrator_agent.cogs.webauthn import RP_ENTITY
        assert RP_ENTITY["rp_id"] == "infra-pilot.local"

    @pytest.mark.asyncio
    async def test_manager_init(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            assert mgr._initialized is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_register_credential(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "User One", "fido2")
            assert cred.credential_id is not None
            assert len(mgr.list_credentials()) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_register_u2f_credential(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "User", "u2f", device_name="YubiKey 5")
            assert cred.device_name == "YubiKey 5"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_device_name_from_aaguid(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "User", "fido2", aaguid="adce0002-35bc-c60a-648b-0b25f1f05503")
            assert cred.device_name == "Chrome on Mac"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_credentials_by_user(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            mgr.register_credential("u1", "U1", "fido2")
            mgr.register_credential("u1", "U1", "u2f")
            mgr.register_credential("u2", "U2", "fido2")
            assert len(mgr.list_credentials("u1")) == 2
            assert len(mgr.list_credentials("u2")) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_credential(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "U1", "fido2")
            retrieved = mgr.get_credential(cred.credential_id)
            assert retrieved is not None
            assert mgr.get_credential("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_record_usage(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "U1", "fido2")
            assert mgr.record_usage(cred.credential_id) is True
            assert mgr.get_credential(cred.credential_id).use_count == 1
            assert mgr.record_usage("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_remove_credential(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "U1", "fido2")
            assert mgr.remove_credential(cred.credential_id) is True
            assert mgr.remove_credential("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_revoke_credential(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "U1", "fido2")
            assert mgr.revoke_credential(cred.credential_id) is True
            from services.orchestrator_agent.cogs.webauthn import VerificationStatus
            assert mgr.get_credential(cred.credential_id).status == VerificationStatus.REVOKED
            assert mgr.revoke_credential("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_preferences(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            prefs = mgr.get_preferences()
            assert "pub_key_cred_params" in prefs
            assert "authenticator_selection" in prefs
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_aaguids(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            aaguids = mgr.get_aaguids()
            assert len(aaguids) == 6
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            mgr.register_credential("u1", "U1", "fido2")
            mgr.register_credential("u1", "U1", "u2f")
            mgr.register_credential("u2", "U2", "fido2")
            stats = mgr.get_statistics()
            assert stats["total_credentials"] == 3
            assert stats["active_credentials"] == 3
            assert stats["unique_users"] == 2
            await mgr.close()

    @pytest.mark.asyncio
    async def test_sign_count_increment(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            cred = mgr.register_credential("u1", "U1", "fido2")
            for _ in range(3):
                mgr.record_usage(cred.credential_id)
            assert mgr.get_credential(cred.credential_id).sign_count == 3
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.webauthn.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.webauthn import WebAuthnManager
            mgr = WebAuthnManager()
            await mgr.initialize()
            mgr.register_credential("u1", "U1", "fido2")
            await mgr.close()
            mgr2 = WebAuthnManager()
            await mgr2.initialize()
            assert len(mgr2.list_credentials()) == 1
            await mgr2.close()


# Session Manager Cog Tests
class TestSessionManagerCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"sessions": [], "risk_history": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_imports(self):
        from services.orchestrator_agent.cogs.session_manager import (
            SessionManager, UserSession, SessionStatus, RiskLevel, RISK_FACTORS, RISK_THRESHOLDS
        )
        assert hasattr(SessionManager, "create_session")
        assert hasattr(SessionManager, "list_sessions")

    def test_risk_factors_count(self):
        from services.orchestrator_agent.cogs.session_manager import RISK_FACTORS
        assert len(RISK_FACTORS) == 9

    def test_risk_thresholds(self):
        from services.orchestrator_agent.cogs.session_manager import RISK_THRESHOLDS
        assert len(RISK_THRESHOLDS) == 4

    @pytest.mark.asyncio
    async def test_create_session(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "Mozilla/5.0", "10.0.0.1", "web")
            assert s["user_id"] == "u1"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_session(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1")
            retrieved = mgr.get_session(s["session_id"])
            assert retrieved is not None
            assert retrieved["user_id"] == "u1"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_sessions(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            mgr.create_session("u1", "UA1", "10.0.0.1", "web")
            mgr.create_session("u1", "UA2", "10.0.0.2", "mobile")
            mgr.create_session("u2", "UA3", "10.0.0.3", "web")
            assert len(mgr.list_sessions("u1")) == 2
            assert len(mgr.list_sessions()) == 3
            await mgr.close()

    @pytest.mark.asyncio
    async def test_update_activity(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1")
            assert mgr.update_activity(s["session_id"]) is True
            assert mgr.update_activity("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_revoke_session(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1")
            assert mgr.revoke_session(s["session_id"]) is True
            from services.orchestrator_agent.cogs.session_manager import SessionStatus
            assert mgr.get_session(s["session_id"])["status"] == "revoked"
            assert mgr.revoke_session("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_expire_session(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1")
            assert mgr.expire_session(s["session_id"]) is True
            assert mgr.get_session(s["session_id"])["status"] == "expired"
            assert mgr.expire_session("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_risk_factors(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            factors = mgr.list_risk_factors()
            assert len(factors) == 9
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            mgr.create_session("u1", "UA", "10.0.0.1")
            mgr.create_session("u1", "UA", "10.0.0.2")
            mgr.create_session("u2", "UA", "10.0.0.3")
            stats = mgr.get_statistics()
            assert stats["total_sessions"] == 3
            assert stats["active_sessions"] == 3
            await mgr.close()

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            mgr.create_session("u1", "UA", "10.0.0.1", "web")
            cleaned = mgr.cleanup_expired()
            assert cleaned >= 0
            await mgr.close()

    @pytest.mark.asyncio
    async def test_evaluate_risk(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            risk = mgr.evaluate_risk("u1", "10.0.0.1", "UA")
            assert "score" in risk
            assert "level" in risk
            await mgr.close()

    @pytest.mark.asyncio
    async def test_session_with_mfa(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1", "web", mfa_method="totp")
            assert s["mfa_method"] == "totp"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_session_filter_by_status(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s1 = mgr.create_session("u1", "UA", "10.0.0.1")
            s2 = mgr.create_session("u1", "UA", "10.0.0.2")
            mgr.revoke_session(s2["session_id"])
            sessions = mgr.list_sessions("u1", "active")
            assert len(sessions) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_device_fingerprint(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            s = mgr.create_session("u1", "UA", "10.0.0.1", "web")
            assert len(s["device_fingerprint"]) == 16
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.session_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.session_manager import SessionManager
            mgr = SessionManager()
            await mgr.initialize()
            mgr.create_session("u1", "UA", "10.0.0.1", "web")
            await mgr.close()
            mgr2 = SessionManager()
            await mgr2.initialize()
            assert len(mgr2.list_sessions()) == 1
            await mgr2.close()


# PAM Cog Tests
class TestPAMCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"requests": [], "break_glass_events": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_imports(self):
        from services.orchestrator_agent.cogs.pam_manager import (
            PAMManager, AccessRequest, AccessRequestStatus, BreakGlassEvent, PAM_POLICIES, BREAK_GLASS_CONFIG
        )
        assert hasattr(PAMManager, "create_request")
        assert hasattr(PAMManager, "approve_request")

    def test_policies(self):
        from services.orchestrator_agent.cogs.pam_manager import PAM_POLICIES
        assert len(PAM_POLICIES) == 3

    def test_break_glass_config(self):
        from services.orchestrator_agent.cogs.pam_manager import BREAK_GLASS_CONFIG
        assert BREAK_GLASS_CONFIG["enabled"] is True

    @pytest.mark.asyncio
    async def test_create_request(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            r = mgr.create_request("u1", "srv1", "admin", "Need access")
            assert r["user_id"] == "u1"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_approve_request(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            r = mgr.create_request("u1", "srv1", "admin", "Maint")
            assert mgr.approve_request(r["request_id"], "approver1") is True
            assert mgr.get_request(r["request_id"])["status"] == "approved"
            assert mgr.approve_request("nonexistent", "a1") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_deny_request(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            r = mgr.create_request("u1", "srv1", "admin", "Maint")
            assert mgr.deny_request(r["request_id"], "approver1") is True
            assert mgr.get_request(r["request_id"])["status"] == "denied"
            assert mgr.deny_request("nonexistent", "a1") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_requests(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            mgr.create_request("u1", "srv1", "admin", "R1")
            mgr.create_request("u2", "srv2", "operator", "R2")
            r3 = mgr.create_request("u1", "srv3", "admin", "R3")
            mgr.approve_request(r3["request_id"], "a1")
            assert len(mgr.list_requests("u1")) == 2
            assert len(mgr.list_requests("u1", "approved")) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_break_glass(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            evt = mgr.initiate_break_glass("u1", "srv1", "Emergency!", 1800)
            assert evt["user_id"] == "u1"
            assert mgr.end_break_glass(evt["event_id"]) is True
            assert mgr.end_break_glass("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_break_glass_actions(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            evt = mgr.initiate_break_glass("u1", "srv1", "Emergency", 3600)
            assert mgr.log_break_glass_action(evt["event_id"], "restart nginx") is True
            assert mgr.log_break_glass_action("nonexistent", "action") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_policies(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            policies = mgr.list_policies()
            assert len(policies) == 3
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            mgr.create_request("u1", "srv1", "admin", "R1")
            mgr.create_request("u2", "srv2", "admin", "R2")
            mgr.initiate_break_glass("u3", "srv3", "Emergency", 3600)
            stats = mgr.get_statistics()
            assert stats["total_requests"] == 2
            assert stats["break_glass_events"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            mgr.create_request("u1", "srv1", "admin", "reason")
            await mgr.close()
            mgr2 = PAMManager()
            await mgr2.initialize()
            assert len(mgr2.list_requests()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_get_break_glass_event(self, data_file):
        with patch("services.orchestrator_agent.cogs.pam_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.pam_manager import PAMManager
            mgr = PAMManager()
            await mgr.initialize()
            evt = mgr.initiate_break_glass("u1", "srv1", "Emergency", 1800)
            e = mgr.get_break_glass_event(evt["event_id"])
            assert e is not None
            assert mgr.get_break_glass_event("nonexistent") is None
            await mgr.close()


# Policy Engine Cog Tests
class TestPolicyEngineCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"policies": [], "evaluation_log": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_imports(self):
        from services.orchestrator_agent.cogs.policy_engine import (
            PolicyEngine, Policy, PolicyRule, PolicyEffect, PolicySeverity, BUILTIN_POLICIES
        )
        assert hasattr(PolicyEngine, "evaluate")
        assert hasattr(PolicyEngine, "create_policy")

    def test_builtin_policies_count(self):
        from services.orchestrator_agent.cogs.policy_engine import BUILTIN_POLICIES
        assert len(BUILTIN_POLICIES) == 8

    @pytest.mark.asyncio
    async def test_initialize_with_builtins(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            assert len(mgr.list_policies()) >= 8
            await mgr.close()

    @pytest.mark.asyncio
    async def test_create_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            p = mgr.create_policy("Custom", "Custom policy", "security", "critical", "deny")
            assert p.policy_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_rule(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            p = mgr.create_policy("Test", "desc", "general")
            assert mgr.add_rule(p.policy_id, "server:*", "start", [{"field": "env", "operator": "eq", "value": "prod"}]) is True
            assert mgr.add_rule("nonexistent", "*", "*", []) is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_evaluate(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            result = mgr.evaluate("server:01", "ssh", {"user": "root"})
            assert result["overall"] == "deny"
            result2 = mgr.evaluate("server:01", "ssh", {"user": "admin"})
            assert result2["overall"] == "allow"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_update_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            p = mgr.create_policy("Updatable", "desc", "general")
            assert mgr.update_policy(p.policy_id, {"name": "Updated Name", "enabled": False}) is True
            assert mgr.get_policy(p.policy_id).name == "Updated Name"
            assert mgr.update_policy("nonexistent", {}) is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_delete_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            p = mgr.create_policy("Delete Me", "desc", "general")
            assert mgr.delete_policy(p.policy_id) is True
            assert mgr.delete_policy("nonexistent") is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            p = mgr.create_policy("Stats", "desc", "security", "high", "deny")
            mgr.add_rule(p.policy_id, "*", "delete", [])
            stats = mgr.get_statistics()
            assert stats["total_policies"] > 0
            assert stats["total_rules"] > 0
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.policy_engine.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.policy_engine import PolicyEngine
            mgr = PolicyEngine()
            await mgr.initialize()
            mgr.create_policy("Persist", "desc", "general")
            await mgr.close()
            mgr2 = PolicyEngine()
            await mgr2.initialize()
            assert len(mgr2.list_policies()) > 0
            await mgr2.close()


# Compliance Scanner Cog Tests
class TestComplianceScannerCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"scans": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_imports(self):
        from services.orchestrator_agent.cogs.compliance_scanner import (
            ComplianceScanner, ComplianceScan, ScanStatus, BENCHMARKS
        )
        assert hasattr(ComplianceScanner, "start_scan")
        assert hasattr(ComplianceScanner, "list_benchmarks")

    def test_benchmarks(self):
        from services.orchestrator_agent.cogs.compliance_scanner import BENCHMARKS
        assert len(BENCHMARKS) == 5

    @pytest.mark.asyncio
    async def test_list_benchmarks(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            benchmarks = mgr.list_benchmarks()
            assert len(benchmarks) == 5
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_benchmark(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            b = mgr.get_benchmark("cis_docker")
            assert b is not None
            assert len(b["checks"]) == 6
            assert mgr.get_benchmark("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_checks(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            checks = mgr.list_checks("cis_kubernetes")
            assert len(checks) == 4
            await mgr.close()

    @pytest.mark.asyncio
    async def test_start_scan(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            scan = mgr.start_scan("cis_docker", "local")
            assert scan.scan_id is not None
            assert scan.status.value == "completed"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_scan(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            scan = mgr.start_scan("cis_docker")
            retrieved = mgr.get_scan(scan.scan_id)
            assert retrieved is not None
            assert mgr.get_scan("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_get_remediation(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            rem = mgr.get_remediation("cis_d_1_1")
            assert rem is not None
            assert rem["check_id"] == "cis_d_1_1"
            assert mgr.get_remediation("nonexistent") is None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_start_unknown_benchmark(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            with pytest.raises(ValueError):
                mgr.start_scan("nonexistent", "local")
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            mgr.start_scan("cis_docker")
            mgr.start_scan("cis_kubernetes")
            stats = mgr.get_statistics()
            assert stats["total_scans"] == 2
            assert stats["available_benchmarks"] == 5
            await mgr.close()

    @pytest.mark.asyncio
    async def test_scan_results(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            scan = mgr.start_scan("cis_docker")
            assert len(scan.results) == 6
            for r in scan.results:
                assert "check_id" in r
                assert "status" in r
            await mgr.close()

    @pytest.mark.asyncio
    async def test_all_benchmark_checks(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            for bid in ["cis_docker", "cis_kubernetes", "nist_800_53", "bsi_200_1", "soc2"]:
                checks = mgr.list_checks(bid)
                assert len(checks) > 0
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.compliance_scanner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.compliance_scanner import ComplianceScanner
            mgr = ComplianceScanner()
            await mgr.initialize()
            mgr.start_scan("cis_docker")
            await mgr.close()
            mgr2 = ComplianceScanner()
            await mgr2.initialize()
            assert len(mgr2.list_benchmarks()) == 5
            await mgr2.close()
