"""Tests for identity_provider_ext module."""
import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.identity_provider_ext import IdentityProviderManager, OIDCProviderConfig, SAMLProviderConfig, ClientRegistration, TokenType


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = IdentityProviderManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestOIDCProvider:
    def test_create_oidc_provider(self, manager):
        provider = manager.create_oidc_provider(
            name="Test OIDC",
            issuer_url="https://accounts.example.com",
            client_id="test-client-id",
            client_secret="test-secret",
            scopes=["openid", "profile", "email"],
        )
        assert provider.id is not None
        assert provider.name == "Test OIDC"
        assert provider.issuer_url == "https://accounts.example.com"
        assert provider.client_id == "test-client-id"
        assert provider.enabled == True

    def test_get_oidc_provider(self, manager):
        provider = manager.create_oidc_provider(name="Test", issuer_url="https://example.com", client_id="cid")
        retrieved = manager.get_oidc_provider(provider.id)
        assert retrieved is not None
        assert retrieved.id == provider.id

    def test_update_oidc_provider(self, manager):
        provider = manager.create_oidc_provider(name="Test", issuer_url="https://example.com", client_id="cid")
        updated = manager.update_oidc_provider(provider.id, {"name": "Updated", "enabled": False})
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.enabled == False

    def test_delete_oidc_provider(self, manager):
        provider = manager.create_oidc_provider(name="Test", issuer_url="https://example.com", client_id="cid")
        assert manager.delete_oidc_provider(provider.id) == True
        assert manager.get_oidc_provider(provider.id) is None


class TestSAMLProvider:
    def test_create_saml_provider(self, manager):
        provider = manager.create_saml_provider(
            name="Test SAML",
            entity_id="https://sp.example.com/saml",
            acs_url="https://sp.example.com/saml/acs",
            metadata_url="https://idp.example.com/metadata",
        )
        assert provider.id is not None
        assert provider.entity_id == "https://sp.example.com/saml"
        assert provider.acs_url == "https://sp.example.com/saml/acs"

    def test_get_saml_provider(self, manager):
        provider = manager.create_saml_provider(name="Test", entity_id="eid", acs_url="https://example.com/acs")
        retrieved = manager.get_saml_provider(provider.id)
        assert retrieved is not None

    def test_update_saml_provider(self, manager):
        provider = manager.create_saml_provider(name="Test", entity_id="eid", acs_url="https://example.com/acs")
        updated = manager.update_saml_provider(provider.id, {"name": "Updated SAML"})
        assert updated.name == "Updated SAML"


class TestClientRegistration:
    def test_register_client(self, manager):
        client = manager.register_client(
            name="Test App",
            redirect_uris=["https://app.example.com/callback"],
            grant_types=["authorization_code", "refresh_token"],
        )
        assert client.client_id is not None
        assert client.client_secret is not None
        assert client.name == "Test App"
        assert "https://app.example.com/callback" in client.redirect_uris

    def test_get_client(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        retrieved = manager.get_client(client.client_id)
        assert retrieved is not None
        assert retrieved.client_id == client.client_id

    def test_update_client(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        updated = manager.update_client(client.client_id, {"name": "Updated App"})
        assert updated.name == "Updated App"

    def test_delete_client(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        assert manager.delete_client(client.client_id) == True
        assert manager.get_client(client.client_id) is None

    def test_rotate_secret(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        old_secret = client.client_secret
        rotated = manager.rotate_client_secret(client.client_id)
        assert rotated.client_secret != old_secret

    def test_list_clients(self, manager):
        manager.register_client(name="App1", redirect_uris=["https://app1.com/callback"])
        manager.register_client(name="App2", redirect_uris=["https://app2.com/callback"])
        clients = manager.list_clients()
        assert len(clients) >= 2


class TestTokenManagement:
    def test_generate_token(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        token = manager.generate_token(client_id=client.client_id, user_id="user123", scopes=["openid", "profile"])
        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == TokenType.BEARER

    def test_validate_token(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        token = manager.generate_token(client_id=client.client_id, user_id="user123", scopes=["openid"])
        validated = manager.validate_token(token.access_token)
        assert validated is not None
        assert validated["user_id"] == "user123"

    def test_revoke_token(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        token = manager.generate_token(client_id=client.client_id, user_id="user123", scopes=["openid"])
        assert manager.revoke_token(token.access_token) == True
        assert manager.validate_token(token.access_token) is None

    def test_refresh_token(self, manager):
        client = manager.register_client(name="Test", redirect_uris=["https://example.com/callback"])
        token = manager.generate_token(client_id=client.client_id, user_id="user123", scopes=["openid", "email"])
        refreshed = manager.refresh_access_token(token.refresh_token)
        assert refreshed is not None
        assert refreshed.access_token != token.access_token


class TestProviderConfig:
    def test_create_with_all_scopes(self, manager):
        provider = manager.create_oidc_provider(name="Full", issuer_url="https://accounts.example.com", client_id="cid", client_secret="secret", scopes=["openid", "profile", "email", "address", "phone", "offline_access"])
        assert len(provider.scopes) == 6

    def test_create_saml_with_attributes(self, manager):
        provider = manager.create_saml_provider(name="Attr SAML", entity_id="eid", acs_url="https://example.com/acs", attribute_mapping={"email": "mail", "name": "displayName"})
        assert provider.attribute_mapping is not None

    def test_statistics(self, manager):
        provider = manager.create_oidc_provider(name="Stats", issuer_url="https://example.com", client_id="cid")
        stats = manager.get_statistics()
        assert stats["total_providers"] >= 1


class TestEdgeCases:
    def test_get_nonexistent_provider(self, manager):
        assert manager.get_oidc_provider("nonexistent-id") is None

    def test_delete_nonexistent_client(self, manager):
        assert manager.delete_client("nonexistent-id") == False

    def test_validate_invalid_token(self, manager):
        assert manager.validate_token("invalid-token-string") is None

    def test_refresh_with_invalid_token(self, manager):
        assert manager.refresh_access_token("invalid-refresh-token") is None

    def test_rotate_nonexistent_client(self, manager):
        assert manager.rotate_client_secret("nonexistent-id") is None


class TestPKCE:
    def test_generate_pkce(self, manager):
        pkce = manager.generate_pkce()
        assert pkce["code_verifier"] is not None
        assert pkce["code_challenge"] is not None
        assert len(pkce["code_verifier"]) >= 43
        assert len(pkce["code_challenge"]) == 44

    def test_generate_multiple_pkce(self, manager):
        pkce1 = manager.generate_pkce()
        pkce2 = manager.generate_pkce()
        assert pkce1["code_verifier"] != pkce2["code_verifier"]


class TestDeviceCodeFlow:
    def test_initiate_device_code(self, manager):
        client = manager.register_client(name="Device App", redirect_uris=["https://example.com/callback"])
        result = manager.initiate_device_code(client.client_id, ["openid", "profile"])
        assert result["device_code"] is not None
        assert result["user_code"] is not None
        assert result["verification_uri"] is not None
        assert result["interval"] > 0

    def test_poll_device_code(self, manager):
        client = manager.register_client(name="Device App", redirect_uris=["https://example.com/callback"])
        result = manager.initiate_device_code(client.client_id, ["openid"])
        status = manager.poll_device_code(result["device_code"])
        assert status is not None

    def test_invalid_device_code(self, manager):
        assert manager.poll_device_code("invalid-code") is None


class TestFederation:
    def test_create_federation(self, manager):
        fed = manager.create_federation(
            name="Test Federation",
            domain="example.com",
            identity_providers=["provider1", "provider2"],
        )
        assert fed.id is not None
        assert fed.domain == "example.com"

    def test_get_federation(self, manager):
        fed = manager.create_federation(name="Test", domain="example.com", identity_providers=["p1"])
        retrieved = manager.get_federation(fed.id)
        assert retrieved is not None
        assert retrieved.id == fed.id
