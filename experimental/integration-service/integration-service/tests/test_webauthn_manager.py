"""Tests for WebAuthn Manager."""
import pytest
import json
from unittest.mock import Mock, patch
from webauthn_manager import (
    WebAuthnManager, CredentialDevice, AuthenticatorSelection,
    generate_registration_options, verify_registration,
    generate_authentication_options, verify_authentication
)


@pytest.fixture
def manager():
    return WebAuthnManager({"rp_name": "Infra Pilot", "rp_id": "auth.infra-pilot.io", "origin": "https://auth.infra-pilot.io"})


class TestCredentialDevice:
    def test_create_credential(self, manager):
        cred = manager.create_credential("user-123", "TestDevice")
        assert cred.credential_id is not None
        assert cred.user_id == "user-123"
        assert cred.device_name == "TestDevice"
        assert cred.is_active is True

    def test_get_user_credentials(self, manager):
        manager.create_credential("user-123", "Device1")
        manager.create_credential("user-123", "Device2")
        creds = manager.get_user_credentials("user-123")
        assert len(creds) == 2

    def test_get_credential_by_id(self, manager):
        original = manager.create_credential("user-123", "MyKey")
        retrieved = manager.get_credential(original.credential_id)
        assert retrieved.credential_id == original.credential_id

    def test_update_credential_counter(self, manager):
        cred = manager.create_credential("user-123", "MyKey")
        old_count = cred.signature_count
        manager.update_signature_count(cred.credential_id, old_count + 5)
        assert cred.signature_count == old_count + 5

    def test_remove_credential(self, manager):
        cred = manager.create_credential("user-123", "MyKey")
        assert manager.remove_credential(cred.credential_id) is True
        retrieved = manager.get_credential(cred.credential_id)
        assert retrieved is None

    def test_remove_missing_credential(self, manager):
        assert manager.remove_credential("nonexistent") is False


class TestRegistrationFlow:
    def test_generate_registration_options(self, manager):
        options = manager.generate_registration_options("user-456", "user-456", "New User")
        assert options is not None
        assert "rp" in options
        assert options["rp"]["name"] == "Infra Pilot"
        assert "user" in options
        assert options["user"]["name"] == "New User"
        assert "challenge" in options
        assert "pubKeyCredParams" in options
        assert len(options["pubKeyCredParams"]) > 0

    def test_generate_registration_options_exclude_credentials(self, manager):
        manager.create_credential("user-456", "Existing Key")
        options = manager.generate_registration_options("user-456", "user-456", "New User")
        assert "excludeCredentials" in options
        assert len(options["excludeCredentials"]) > 0

    def test_verify_registration_success(self, manager):
        options = manager.generate_registration_options("user-789", "user-789", "TestUser")
        client_data = {"type": "webauthn.create", "challenge": options["challenge"], "origin": "https://auth.infra-pilot.io"}
        attestation = {"id": "base64credentialid", "response": {"attestationObject": "base64data", "clientDataJSON": json.dumps(client_data)}}
        result = manager.verify_registration(attestation)
        assert result is True

    def test_verify_registration_bad_origin(self, manager):
        options = manager.generate_registration_options("user-789", "user-789", "TestUser")
        client_data = {"type": "webauthn.create", "challenge": options["challenge"], "origin": "https://evil.com"}
        attestation = {"id": "cred123", "response": {"attestationObject": "base64", "clientDataJSON": json.dumps(client_data)}}
        result = manager.verify_registration(attestation)
        assert result is False

    def test_verify_registration_bad_challenge(self, manager):
        manager.generate_registration_options("user-789", "user-789", "TestUser")
        client_data = {"type": "webauthn.create", "challenge": "wrongchallenge", "origin": "https://auth.infra-pilot.io"}
        attestation = {"id": "cred123", "response": {"attestationObject": "base64", "clientDataJSON": json.dumps(client_data)}}
        result = manager.verify_registration(attestation)
        assert result is False


class TestAuthenticationFlow:
    def test_generate_authentication_options(self, manager):
        manager.create_credential("user-111", "MyKey")
        options = manager.generate_authentication_options("user-111")
        assert options is not None
        assert "challenge" in options
        assert "allowCredentials" in options
        assert len(options["allowCredentials"]) > 0

    def test_verify_authentication_success(self, manager):
        manager.create_credential("user-222", "MyKey")
        options = manager.generate_authentication_options("user-222")
        client_data = {"type": "webauthn.get", "challenge": options["challenge"], "origin": "https://auth.infra-pilot.io"}
        assertion = {"id": "credentialid", "response": {"authenticatorData": "base64", "clientDataJSON": json.dumps(client_data), "signature": "basesig"}}
        result = manager.verify_authentication(assertion)
        assert result is True

    def test_verify_authentication_no_credentials(self, manager):
        options = manager.generate_authentication_options("user-333")
        client_data = {"type": "webauthn.get", "challenge": options.get("challenge", ""), "origin": "https://auth.infra-pilot.io"}
        assertion = {"id": "nonexistent", "response": {"authenticatorData": "base64", "clientDataJSON": json.dumps(client_data), "signature": "sig"}}
        result = manager.verify_authentication(assertion)
        assert result is False


class TestPasskeys:
    def test_generate_passkey_registration(self, manager):
        opts = manager.generate_passkey_registration("user-444", "user-444", "DisplayName")
        assert opts is not None
        assert opts["rp"]["name"] == "Infra Pilot"

    def test_verify_passkey_registration(self, manager):
        opts = manager.generate_passkey_registration("user-555", "user-555", "User")
        client_data = {"type": "webauthn.create", "challenge": opts["challenge"], "origin": "https://auth.infra-pilot.io"}
        assertion = {"id": "passkeyid", "response": {"clientDataJSON": json.dumps(client_data), "attestationObject": "base64"}}
        result = manager.verify_passkey_registration(assertion)
        assert result is True

    def test_generate_passkey_authentication(self, manager):
        manager.create_credential("user-666", "Passkey")
        opts = manager.generate_passkey_authentication()
        assert opts is not None
        assert "challenge" in opts
        assert "allowCredentials" in opts
        assert len(opts["allowCredentials"]) > 0

    def test_list_passkeys(self, manager):
        manager.create_credential("user-777", "YubiKey")
        manager.create_credential("user-777", "TouchID")
        passkeys = manager.list_passkeys("user-777")
        assert len(passkeys) >= 2

    def test_rename_passkey(self, manager):
        cred = manager.create_credential("user-888", "OldName")
        assert manager.rename_passkey(cred.credential_id, "NewName") is True
        assert cred.device_name == "NewName"

    def test_rename_missing_passkey(self, manager):
        assert manager.rename_passkey("nonexistent", "NewName") is False


class TestRateLimiting:
    def test_rate_limiter_allows_requests(self, manager):
        for _ in range(10):
            assert manager.check_rate_limit("user-999") is True

    def test_rate_limiter_blocks_excess(self, manager):
        for _ in range(60):
            manager.check_rate_limit("user-brute")
        assert manager.check_rate_limit("user-brute") is False
