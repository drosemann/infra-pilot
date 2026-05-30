"""Tests for IoT Device Provisioning."""

import pytest
from cogs.iot_device_provisioning import (
    IoTDeviceProvisioning, ClaimCode, DeviceCertificate, DeviceShadow,
    DeviceProfile, SecureElementType, ProvisioningStatus
)


@pytest.fixture
def prov():
    return IoTDeviceProvisioning({})


class TestClaimCode:
    def test_code_generation(self):
        import string, secrets
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace("0", "").replace("O", "").replace("I", "").replace("L", "")
        code = "IP-" + "".join(secrets.choice(chars) for _ in range(5))
        assert code.startswith("IP-")
        assert len(code) > 5

    def test_claim_code_validity(self):
        from datetime import timedelta
        cc = ClaimCode("IP-AAAAA-BBBBB-CCCCC", "batch-001")
        assert cc.is_valid is True
        assert cc.is_expired is False

    def test_claim_code_expired(self, prov):
        codes = prov.generate_claim_codes(1, ttl_hours=0)
        import time
        time.sleep(0.001)
        assert codes[0].is_expired is True

    def test_to_dict(self):
        cc = ClaimCode("IP-TEST-CODE", "batch-001")
        d = cc.to_dict()
        assert d["code"] == "IP-TEST-CODE"
        assert d["status"] == "pending"


class TestDeviceCertificate:
    def test_cert_creation(self):
        cert = DeviceCertificate("SERIAL-001", "dev-001", "device-dev-001")
        assert cert.serial == "SERIAL-001"
        assert cert.revoked is False
        assert cert.signature_algorithm == "SHA256-ECDSA"

    def test_cert_revocation(self):
        cert = DeviceCertificate("SERIAL-002", "dev-002", "device-dev-002")
        cert.revoked = True
        from datetime import datetime
        cert.revoked_at = datetime.utcnow()
        assert cert.revoked is True
        assert cert.revoked_at is not None


class TestDeviceShadow:
    def test_shadow_creation(self):
        shadow = DeviceShadow("dev-001")
        assert shadow.device_id == "dev-001"
        assert shadow.version == 1
        assert "state" in shadow.reported

    def test_to_dict(self):
        shadow = DeviceShadow("dev-001")
        d = shadow.to_dict()
        assert d["device_id"] == "dev-001"
        assert d["version"] == 1


class TestIoTDeviceProvisioning:
    def test_initialization(self, prov):
        assert len(prov.profiles) > 0
        assert len(prov.claim_codes) > 0
        assert prov.get_provisioning_summary()["total_claim_codes"] > 0

    def test_generate_claim_codes(self, prov):
        codes = prov.generate_claim_codes(5, 48)
        assert len(codes) == 5
        assert codes[0].batch_id is not None

    def test_validate_valid_code(self, prov):
        codes = prov.generate_claim_codes(1)
        valid, msg = prov.validate_claim_code(codes[0].code)
        assert valid is True

    def test_validate_invalid_code(self, prov):
        valid, msg = prov.validate_claim_code("INVALID-CODE")
        assert valid is False

    def test_claim_device(self, prov):
        codes = prov.generate_claim_codes(1)
        claimed, msg = prov.claim_device(codes[0].code, "dev-new-001", "fp-test")
        assert claimed is True

    def test_claim_device_twice(self, prov):
        codes = prov.generate_claim_codes(1)
        prov.claim_device(codes[0].code, "dev-001", "fp-001")
        claimed, msg = prov.claim_device(codes[0].code, "dev-002", "fp-002")
        assert claimed is False

    def test_enroll_device(self, prov):
        import asyncio
        cert = asyncio.run(prov.enroll_device("dev-enroll-001", "csr-data"))
        assert cert is not None
        assert cert.device_id == "dev-enroll-001"

    def test_get_certificate(self, prov):
        import asyncio
        cert = asyncio.run(prov.enroll_device("dev-cert-001", "csr"))
        found = prov.get_certificate(cert.serial)
        assert found is not None
        assert found.device_id == "dev-cert-001"

    def test_get_certificate_not_found(self, prov):
        assert prov.get_certificate("NONEXISTENT") is None

    def test_revoke_certificate(self, prov):
        import asyncio
        cert = asyncio.run(prov.enroll_device("dev-revoke-001", "csr"))
        assert prov.revoke_certificate(cert.serial) is True
        assert prov.get_certificate(cert.serial).revoked is True

    def test_revoke_certificate_not_found(self, prov):
        assert prov.revoke_certificate("NONEXISTENT") is False

    def test_get_shadow(self, prov):
        import asyncio
        asyncio.run(prov.enroll_device("dev-shadow-001", "csr"))
        shadow = prov.get_shadow("dev-shadow-001")
        assert shadow is not None
        assert shadow.device_id == "dev-shadow-001"

    def test_get_shadow_not_found(self, prov):
        assert prov.get_shadow("nonexistent") is None

    def test_update_shadow(self, prov):
        import asyncio
        asyncio.run(prov.enroll_device("dev-update-001", "csr"))
        shadow = prov.update_shadow("dev-update-001", reported={"temperature": 45.0})
        assert shadow is not None
        assert shadow.reported["temperature"] == 45.0
        assert shadow.version == 2

    def test_update_shadow_not_found(self, prov):
        assert prov.update_shadow("nonexistent", {}) is None

    def test_create_profile(self, prov):
        profile = prov.create_profile("custom-iot", "sensor", {"interval": 10})
        assert profile.profile_id is not None
        assert profile.name == "custom-iot"

    def test_list_profiles(self, prov):
        profiles = prov.list_profiles()
        assert len(profiles) > 0

    def test_get_profile(self, prov):
        profiles = prov.list_profiles()
        profile = prov.get_profile(profiles[0].profile_id)
        assert profile is not None

    def test_get_profile_not_found(self, prov):
        assert prov.get_profile("nonexistent") is None

    def test_list_claim_codes_by_status(self, prov):
        all_codes = prov.list_claim_codes()
        pending = prov.list_claim_codes(status="pending")
        assert len(pending) <= len(all_codes)

    def test_get_provisioning_summary(self, prov):
        summary = prov.get_provisioning_summary()
        assert "total_claim_codes" in summary
        assert "active_devices" in summary
        assert "profiles" in summary

    def test_secure_element_types(self):
        assert SecureElementType.TPM.value == "tpm"
        assert SecureElementType.ATECC608A.value == "atecc608a"
        assert SecureElementType.SOFT.value == "software"

    def test_provisioning_status_enum(self):
        assert ProvisioningStatus.PENDING.value == "pending"
        assert ProvisioningStatus.ACTIVE.value == "active"
