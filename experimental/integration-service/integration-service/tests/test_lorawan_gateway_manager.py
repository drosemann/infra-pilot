"""Tests for LoRaWAN Gateway Manager."""

import pytest
from lorawan_gateway_manager import (
    LoRaWANGatewayManager, LoRaWANGateway, LoRaWANDevice,
    GatewayStatus, DeviceClass, SpreadingFactor
)


@pytest.fixture
def gw_manager():
    return LoRaWANGatewayManager({})


class TestLoRaWANGateway:
    def test_create(self):
        gw = LoRaWANGateway(
            "gw-001", "us915", "37.7749", "-122.4194",
            "gateway-1"
        )
        assert gw.gateway_id == "gw-001"
        assert gw.status == GatewayStatus.OFFLINE

    def test_to_dict(self):
        gw = LoRaWANGateway("gw-001", "eu868", "48.85", "2.35", "gw-1")
        d = gw.to_dict()
        assert d["region"] == "eu868"
        assert d["location_lat"] == "48.85"


class TestLoRaWANDevice:
    def test_create(self):
        device = LoRaWANDevice("dev-001", "app-key-123", "dev-eui-abc",
                                DeviceClass.CLASS_A)
        assert device.device_id == "dev-001"
        assert device.dev_class == DeviceClass.CLASS_A
        assert device.is_active is False

    def test_to_dict(self):
        device = LoRaWANDevice("dev-001", "key", "eui", DeviceClass.CLASS_C)
        d = device.to_dict()
        assert d["device_id"] == "dev-001"


class TestLoRaWANGatewayManager:
    def test_initialization(self, gw_manager):
        assert len(gw_manager.gateways) > 0
        assert len(gw_manager.devices) > 0

    def test_register_gateway(self, gw_manager):
        gw = gw_manager.register_gateway(
            "gw-new", "as923", "1.35", "103.82",
            "gateway-sg"
        )
        assert gw.gateway_id == "gw-new"
        assert gw.status == GatewayStatus.ONLINE

    def test_get_gateway(self, gw_manager):
        gid = list(gw_manager.gateways.keys())[0]
        assert gw_manager.get_gateway(gid) is not None

    def test_get_gateway_not_found(self, gw_manager):
        assert gw_manager.get_gateway("nonexistent") is None

    def test_list_gateways(self, gw_manager):
        gateways = gw_manager.list_gateways()
        assert len(gateways) > 0

    def test_update_gateway(self, gw_manager):
        gid = list(gw_manager.gateways.keys())[0]
        updated = gw_manager.update_gateway(gid, {"region": "au915"})
        assert updated is not None
        assert updated.region == "au915"

    def test_delete_gateway(self, gw_manager):
        gid = list(gw_manager.gateways.keys())[0]
        assert gw_manager.delete_gateway(gid) is True
        assert gw_manager.get_gateway(gid) is None

    def test_register_device(self, gw_manager):
        device = gw_manager.register_device(
            "dev-new", "app-key-new", "dev-eui-new",
            DeviceClass.CLASS_B, "gw-001"
        )
        assert device.device_id == "dev-new"
        assert device.is_active is True

    def test_get_device(self, gw_manager):
        did = list(gw_manager.devices.keys())[0]
        assert gw_manager.get_device(did) is not None

    def test_get_device_not_found(self, gw_manager):
        assert gw_manager.get_device("nonexistent") is None

    def test_list_devices(self, gw_manager):
        devices = gw_manager.list_devices()
        assert len(devices) > 0

    def test_delete_device(self, gw_manager):
        did = list(gw_manager.devices.keys())[0]
        assert gw_manager.delete_device(did) is True

    def test_get_gateway_stats(self, gw_manager):
        gid = list(gw_manager.gateways.keys())[0]
        stats = gw_manager.get_gateway_stats(gid)
        assert "gateway_id" in stats
        assert "packets_received" in stats
        assert "status" in stats

    def test_get_all_stats(self, gw_manager):
        stats = gw_manager.get_all_stats()
        assert "total_gateways" in stats
        assert "online_gateways" in stats
        assert "total_devices" in stats
        assert "active_devices" in stats
        assert "total_packets" in stats

    def test_update_device_data_rate(self, gw_manager):
        did = list(gw_manager.devices.keys())[0]
        result = gw_manager.update_device_data_rate(did, SpreadingFactor.SF9,
                                                      bandwidth=125)
        assert result is True

    def test_update_device_data_rate_not_found(self, gw_manager):
        assert gw_manager.update_device_data_rate("nonexistent",
                                                    SpreadingFactor.SF7, 125) is False

    def test_get_coverage_map(self, gw_manager):
        coverage = gw_manager.get_coverage_map()
        assert "gateways" in coverage
        assert "estimated_coverage_km2" in coverage

    def test_gateway_status_enum(self):
        assert GatewayStatus.ONLINE.value == "online"
        assert GatewayStatus.OFFLINE.value == "offline"
        assert GatewayStatus.DEGRADED.value == "degraded"

    def test_device_class_enum(self):
        assert DeviceClass.CLASS_A.value == "class_a"
        assert DeviceClass.CLASS_B.value == "class_b"
        assert DeviceClass.CLASS_C.value == "class_c"

    def test_spreading_factor_enum(self):
        assert SpreadingFactor.SF7.value == 7
        assert SpreadingFactor.SF12.value == 12
