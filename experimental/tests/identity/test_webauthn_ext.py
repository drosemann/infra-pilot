"""Tests for webauthn_ext module."""
import pytest
import tempfile
import os
from datetime import datetime
from services.integration_service.src.webauthn_ext import WebAuthnManager, PasskeyChallenge, AuthenticatorData, FIDO2MetadataEntry


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = WebAuthnManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestPasskeyChallenge:
    def test_create_challenge(self, manager):
        challenge = manager.create_passkey_challenge(user_id="user123", relying_party="example.com")
        assert challenge.challenge_id is not None
        assert challenge.user_id == "user123"
        assert challenge.rp_id == "example.com"
        assert challenge.expires_at is not None

    def test_get_challenge(self, manager):
        challenge = manager.create_passkey_challenge(user_id="user123", relying_party="example.com")
        retrieved = manager.get_challenge(challenge.challenge_id)
        assert retrieved is not None
        assert retrieved.challenge_id == challenge.challenge_id

    def test_verify_challenge(self, manager):
        challenge = manager.create_passkey_challenge(user_id="user123", relying_party="example.com")
        result = manager.verify_challenge(challenge.challenge_id)
        assert result is True

    def test_verify_nonexistent_challenge(self, manager):
        result = manager.verify_challenge("nonexistent-challenge")
        assert result is False

    def test_expired_challenge(self, manager):
        challenge = manager.create_passkey_challenge(user_id="user123", relying_party="example.com")
        challenge.expires_at = datetime(2020, 1, 1)
        result = manager.verify_challenge(challenge.challenge_id)
        assert result is False

    def test_cleanup_expired(self, manager):
        challenge = manager.create_passkey_challenge(user_id="user123", relying_party="example.com")
        challenge.expires_at = datetime(2020, 1, 1)
        count = manager.cleanup_expired_challenges()
        assert count >= 1


class TestAuthenticator:
    def test_register_authenticator(self, manager):
        auth = manager.register_authenticator(
            user_id="user123",
            credential_id="cred-id-1",
            public_key="public-key-data",
            device_name="YubiKey 5 NFC",
            aaguid="aaguid-1234",
        )
        assert auth.authenticator_id is not None
        assert auth.user_id == "user123"
        assert auth.credential_id == "cred-id-1"
        assert auth.device_name == "YubiKey 5 NFC"

    def test_get_authenticator(self, manager):
        auth = manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1")
        retrieved = manager.get_authenticator(auth.authenticator_id)
        assert retrieved is not None
        assert retrieved.authenticator_id == auth.authenticator_id

    def test_list_user_authenticators(self, manager):
        manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1", device_name="Key1")
        manager.register_authenticator(user_id="user1", credential_id="c2", public_key="pk2", device_name="Key2")
        manager.register_authenticator(user_id="user2", credential_id="c3", public_key="pk3", device_name="Key3")
        user1_auths = manager.list_user_authenticators("user1")
        assert len(user1_auths) == 2
        user2_auths = manager.list_user_authenticators("user2")
        assert len(user2_auths) == 1

    def test_remove_authenticator(self, manager):
        auth = manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1")
        assert manager.remove_authenticator(auth.authenticator_id) == True
        assert manager.get_authenticator(auth.authenticator_id) is None

    def test_update_authenticator(self, manager):
        auth = manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1", device_name="Old Name")
        updated = manager.update_authenticator(auth.authenticator_id, device_name="New Name", last_used=datetime.utcnow())
        assert updated is not None
        assert updated.device_name == "New Name"


class TestCredentialImportExport:
    def test_export_credentials(self, manager):
        manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1", device_name="Key1")
        manager.register_authenticator(user_id="user1", credential_id="c2", public_key="pk2", device_name="Key2")
        exported = manager.export_credentials("user1")
        assert len(exported) == 2
        assert exported[0]["credential_id"] == "c1"
        assert exported[1]["credential_id"] == "c2"

    def test_import_credentials(self, manager):
        credentials = [
            {"credential_id": "imported-c1", "public_key": "pk-imported-1", "device_name": "Imported Key 1"},
            {"credential_id": "imported-c2", "public_key": "pk-imported-2", "device_name": "Imported Key 2"},
        ]
        count = manager.import_credentials("user1", credentials)
        assert count == 2
        auths = manager.list_user_authenticators("user1")
        assert len(auths) == 2


class TestFIDOMetadata:
    def test_add_metadata_entry(self, manager):
        entry = manager.add_fido2_metadata_entry(
            aaguid="aaguid-test",
            name="YubiKey 5 NFC",
            icon_url="https://example.com/icon.png",
            description="Yubico YubiKey 5 Series",
            is_passkey=True,
        )
        assert entry.aaguid == "aaguid-test"
        assert entry.name == "YubiKey 5 NFC"

    def test_get_metadata(self, manager):
        manager.add_fido2_metadata_entry(aaguid="aaguid-1", name="Key1")
        entry = manager.get_fido2_metadata("aaguid-1")
        assert entry is not None
        assert entry.name == "Key1"

    def test_get_nonexistent_metadata(self, manager):
        entry = manager.get_fido2_metadata("nonexistent-aaguid")
        assert entry is None


class TestEdgeCases:
    def test_multiple_challenges_same_user(self, manager):
        c1 = manager.create_passkey_challenge(user_id="user1", relying_party="example.com")
        c2 = manager.create_passkey_challenge(user_id="user1", relying_party="example.com")
        assert c1.challenge_id != c2.challenge_id
        assert manager.verify_challenge(c1.challenge_id) is True
        assert manager.verify_challenge(c2.challenge_id) is True

    def test_double_removal(self, manager):
        auth = manager.register_authenticator(user_id="user1", credential_id="c1", public_key="pk1")
        assert manager.remove_authenticator(auth.authenticator_id) == True
        assert manager.remove_authenticator(auth.authenticator_id) == False

    def test_export_empty_user(self, manager):
        exported = manager.export_credentials("nonexistent-user")
        assert exported == []

    def test_import_empty_list(self, manager):
        count = manager.import_credentials("user1", [])
        assert count == 0

    def test_statistics(self, manager):
        manager.register_authenticator(user_id="u1", credential_id="c1", public_key="pk1")
        stats = manager.get_statistics()
        assert stats["total_authenticators"] >= 1
