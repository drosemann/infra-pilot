"""Tests for Identity Provider (SSO/OIDC)."""
import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from identity_provider import (
    IdentityProvider, OIDCClient, OIDCSession, SAMLAssertion,
    generate_jwk, verify_id_token, create_auth_code, exchange_code,
    generate_saml_response, validate_saml_assertion
)


@pytest.fixture
def provider():
    p = IdentityProvider({"issuer": "https://auth.infra-pilot.io", "token_ttl": 3600, "refresh_ttl": 86400})
    return p


class TestOIDCClient:
    def test_register_client(self, provider):
        client = provider.register_client(
            client_name="Test App",
            redirect_uris=["https://app.example.com/callback"],
            grant_types=["authorization_code"],
            client_type="confidential"
        )
        assert client.client_id is not None
        assert client.client_secret is not None
        assert client.client_name == "Test App"
        assert client.client_type == "confidential"

    def test_register_public_client(self, provider):
        client = provider.register_client(
            client_name="SPA App",
            redirect_uris=["https://spa.example.com/callback"],
            grant_types=["authorization_code", "refresh_token"],
            client_type="public"
        )
        assert client.client_type == "public"
        assert client.client_secret is None

    def test_get_client(self, provider):
        original = provider.register_client("Test", ["https://example.com/callback"])
        retrieved = provider.get_client(original.client_id)
        assert retrieved.client_id == original.client_id
        assert retrieved.client_secret == original.client_secret

    def test_get_missing_client(self, provider):
        assert provider.get_client("nonexistent") is None

    def test_authenticate_client_valid(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        assert provider.authenticate_client(client.client_id, client.client_secret) is True

    def test_authenticate_client_invalid_secret(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        assert provider.authenticate_client(client.client_id, "wrong_secret") is False

    def test_delete_client(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        assert provider.delete_client(client.client_id) is True
        assert provider.get_client(client.client_id) is None

    def test_list_clients(self, provider):
        provider.register_client("App1", ["https://app1.com/callback"])
        provider.register_client("App2", ["https://app2.com/callback"])
        clients = provider.list_clients()
        assert len(clients) >= 2


class TestAuthorizationCodeFlow:
    def test_create_auth_code(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(
            client_id=client.client_id,
            redirect_uri="https://example.com/callback",
            user_id="user-123",
            scope="openid profile email"
        )
        assert code is not None
        assert len(code) > 10

    def test_exchange_code_valid(self, provider):
        client = provider.register_client("Confidential", ["https://example.com/callback"], client_type="confidential")
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(
            code=code,
            client_id=client.client_id,
            client_secret=client.client_secret,
            redirect_uri="https://example.com/callback"
        )
        assert token is not None
        assert "access_token" in token
        assert "id_token" in token
        assert "refresh_token" in token
        assert token["token_type"] == "Bearer"

    def test_exchange_code_expired(self, provider):
        provider.config["auth_code_ttl"] = 0
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        assert token is None

    def test_exchange_code_wrong_redirect(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://evil.com/callback")
        assert token is None

    def test_exchange_code_wrong_client_secret(self, provider):
        client = provider.register_client("Confidential", ["https://example.com/callback"], client_type="confidential")
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, "wrong_secret", "https://example.com/callback")
        assert token is None


class TestTokenManagement:
    def test_verify_id_token_valid(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid profile")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        claims = provider.verify_id_token(token["id_token"])
        assert claims is not None
        assert claims["sub"] == "user-123"
        assert claims["aud"] == client.client_id
        assert claims["iss"] == provider.config["issuer"]

    def test_verify_access_token_valid(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        claims = provider.verify_access_token(token["access_token"])
        assert claims is not None
        assert claims["sub"] == "user-123"

    def test_refresh_token_valid(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        refreshed = provider.refresh_access_token(token["refresh_token"], client.client_id, client.client_secret)
        assert refreshed is not None
        assert "access_token" in refreshed
        assert refreshed["refresh_token"] != token["refresh_token"]

    def test_revoke_token(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        assert provider.revoke_token(token["access_token"], "access_token") is True
        assert provider.verify_access_token(token["access_token"]) is None

    def test_get_jwks(self, provider):
        jwks = provider.get_jwks()
        assert "keys" in jwks
        assert len(jwks["keys"]) > 0
        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert "n" in key
        assert "e" in key
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"

    def test_get_well_known_config(self, provider):
        config = provider.get_well_known_config()
        assert config["issuer"] == provider.config["issuer"]
        assert "authorization_endpoint" in config
        assert "token_endpoint" in config
        assert "userinfo_endpoint" in config
        assert "jwks_uri" in config
        assert "response_types_supported" in config
        assert "grant_types_supported" in config
        assert "id_token_signing_alg_values_supported" in config


class TestSAMLAssertion:
    def test_generate_saml_response(self, provider):
        response = provider.generate_saml_response(
            user_id="user-456",
            issuer="https://app.example.com",
            audience="https://sp.example.com/saml/acs"
        )
        assert response is not None
        assert "<samlp:Response" in response
        assert "<saml:Assertion" in response
        assert "user-456" in response
        assert "https://sp.example.com/saml/acs" in response

    def test_validate_saml_assertion(self, provider):
        client = provider.register_client("SAML App", ["https://sp.example.com/saml/acs"])
        response = provider.generate_saml_response("user-456", "https://app.example.com", "https://sp.example.com/saml/acs")
        result = provider.validate_saml_response(response)
        assert result is not None
        assert result["user_id"] == "user-456"

    def test_register_saml_client(self, provider):
        sp_meta = {
            "entity_id": "https://sp.example.com/saml/metadata",
            "acs_url": "https://sp.example.com/saml/acs",
            "certificate": "fake-cert"
        }
        client = provider.register_saml_client("SAML App", sp_meta)
        assert client.client_name == "SAML App"
        assert client.saml_config["entity_id"] == "https://sp.example.com/saml/metadata"
        assert client.saml_config["acs_url"] == "https://sp.example.com/saml/acs"


class TestUserInfo:
    def test_get_userinfo(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid profile email")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        userinfo = provider.get_userinfo(token["access_token"])
        assert userinfo is not None
        assert userinfo["sub"] == "user-123"

    def test_get_userinfo_claims_scope(self, provider):
        provider._user_claims["user-123"] = {"name": "Test User", "email": "test@example.com", "picture": "https://example.com/avatar.png"}
        client = provider.register_client("Test", ["https://example.com/callback"])
        code = provider.create_authorization_code(client.client_id, "https://example.com/callback", "user-123", "openid profile email")
        token = provider.exchange_code(code, client.client_id, client.client_secret, "https://example.com/callback")
        userinfo = provider.get_userinfo(token["access_token"])
        assert userinfo["name"] == "Test User"
        assert userinfo["email"] == "test@example.com"


class TestOIDCSession:
    def test_create_session(self, provider):
        session = provider.create_session("user-123", "Test App", "127.0.0.1")
        assert session.session_id is not None
        assert session.user_id == "user-123"
        assert session.client_name == "Test App"
        assert session.ip_address == "127.0.0.1"
        assert session.is_active is True

    def test_get_active_sessions(self, provider):
        provider.create_session("user-123", "App1", "10.0.0.1")
        provider.create_session("user-123", "App2", "10.0.0.2")
        sessions = provider.get_active_sessions("user-123")
        assert len(sessions) >= 2

    def test_end_session(self, provider):
        session = provider.create_session("user-123", "Test App", "127.0.0.1")
        assert provider.end_session(session.session_id) is True
        assert session.is_active is False

    def test_end_session_not_found(self, provider):
        assert provider.end_session("nonexistent") is False


class TestClientAuthentication:
    def test_client_credentials_grant(self, provider):
        client = provider.register_client("Service", ["https://example.com/callback"], client_type="confidential")
        token = provider.client_credentials_grant(client.client_id, client.client_secret, ["read", "write"])
        assert token is not None
        assert "access_token" in token

    def test_rotate_client_secret(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"], client_type="confidential")
        old_secret = client.client_secret
        new_secret = provider.rotate_client_secret(client.client_id)
        assert new_secret is not None
        assert new_secret != old_secret
        assert client.client_secret == new_secret
        # old secret should still work during grace period
        assert provider.authenticate_client(client.client_id, old_secret) is True

    def test_rotate_client_secret_expire_old(self, provider):
        client = provider.register_client("Test", ["https://example.com/callback"], client_type="confidential")
        old_secret = client.client_secret
        provider.rotate_client_secret(client.client_id, expire_old=True)
        assert provider.authenticate_client(client.client_id, old_secret) is False


class TestJWKGeneration:
    def test_generate_jwk_rs256(self):
        jwk = generate_jwk("RS256")
        assert jwk["kty"] == "RSA"
        assert jwk["alg"] == "RS256"
        assert "n" in jwk
        assert "e" in jwk
        assert "d" in jwk
        assert "p" in jwk
        assert "q" in jwk

    def test_public_jwk(self, provider):
        jwks = provider.get_public_jwks()
        for key in jwks["keys"]:
            assert "d" not in key
            assert "p" not in key
            assert "q" not in key
            assert "dp" not in key
            assert "dq" not in key
            assert "qi" not in key
