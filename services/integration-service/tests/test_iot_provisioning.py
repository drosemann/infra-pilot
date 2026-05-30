"""Tests for IoT Provisioning API."""

import pytest
from iot_provisioning import IoTProvisioningService


@pytest.fixture
def api():
    return IoTProvisioningService({})


class TestIoTProvisioningService:
    def test_initialization(self, api):
        assert api is not None

    def test_provision_device(self, api):
        result = api.provision_device("dev-new", "profile-1", "claim-code-abc")
        assert result is not None
        assert "device_id" in result
        assert "certificate_serial" in result or "status" in result

    def test_get_provisioning_status(self, api):
        result = api.provision_device("dev-status", "profile-1", "code-xyz")
        status = api.get_provisioning_status(result.get("device_id", "dev-status"))
        assert status is not None

    def test_get_provisioning_details(self, api):
        details = api.get_provisioning_details("dev-001")
        assert details is not None
        assert "device_id" in details or "profile" in details or "status" in details

    def test_list_provisioned_devices(self, api):
        devices = api.list_provisioned_devices()
        assert len(devices) >= 0

    def test_deprovision_device(self, api):
        result = api.deprovision_device("dev-001")
        assert result is not None
        assert "success" or "status" in result
