"""Tests for Edge Device Manager."""

import pytest
import asyncio
from datetime import datetime, timedelta
from cogs.edge_device_manager import (
    EdgeDevice, EdgeDeviceManager, DeviceGroup, FirmwareUpdate, RemoteCommand
)


@pytest.fixture
def manager():
    m = EdgeDeviceManager({})
    return m


class TestEdgeDevice:
    def test_create_device(self):
        device = EdgeDevice("dev-001", "test-pi", "raspberry_pi", "b8:27:eb:00:00:01")
        assert device.device_id == "dev-001"
        assert device.name == "test-pi"
        assert device.device_type == "raspberry_pi"
        assert device.status == "provisioning"

    def test_device_to_dict(self):
        device = EdgeDevice("dev-001", "test", "jetson_nano", "00:00:00:00:00:01")
        d = device.to_dict()
        assert d["device_id"] == "dev-001"
        assert d["name"] == "test"
        assert d["device_type"] == "jetson_nano"
        assert "resources" in d

    def test_device_from_dict(self):
        data = {
            "device_id": "dev-002", "name": "restored", "device_type": "rockpi",
            "hardware_id": "aa:bb:cc:dd:ee:ff", "status": "online",
            "fingerprint": "fp_test123", "tags": ["production"],
            "resources": {"cpu_usage": 45.0, "memory_used_mb": 2048},
            "created_at": "2026-01-01T00:00:00",
        }
        device = EdgeDevice.from_dict(data)
        assert device.device_id == "dev-002"
        assert device.name == "restored"
        assert device.status == "online"
        assert device.resources["cpu_usage"] == 45.0

    def test_device_fingerprint_validation(self):
        device = EdgeDevice("dev-003", "test", "generic_arm", "11:22:33:44:55:66")
        assert device.fingerprint == ""
        device.fingerprint = "fp_dev003_a1b2c3d4"
        assert device.fingerprint.startswith("fp_")


class TestEdgeDeviceManager:
    def test_manager_initialization(self, manager):
        assert len(manager.devices) > 0
        assert manager.get_devices_summary()["total"] > 0

    def test_register_device(self, manager):
        device = manager.register_device("new-device", "raspberry_pi", "de:ad:be:ef:00:01")
        assert device.device_id is not None
        assert device.name == "new-device"
        assert manager.get_device(device.device_id) is not None

    def test_get_device_not_found(self, manager):
        assert manager.get_device("non-existent") is None

    def test_list_devices_filter(self, manager):
        all_devices = manager.list_devices()
        assert len(all_devices) > 0
        online = manager.list_devices(status="online")
        assert all(d.status == "online" for d in online)

    def test_update_device(self, manager):
        first_id = list(manager.devices.keys())[0]
        updated = manager.update_device(first_id, {"name": "renamed-device"})
        assert updated is not None
        assert updated.name == "renamed-device"

    def test_update_device_not_found(self, manager):
        assert manager.update_device("nonexistent", {"name": "x"}) is None

    def test_delete_device(self, manager):
        first_id = list(manager.devices.keys())[0]
        assert manager.delete_device(first_id) is True
        assert manager.get_device(first_id) is None

    def test_delete_device_not_found(self, manager):
        assert manager.delete_device("nonexistent") is False

    def test_process_heartbeat(self, manager):
        first_id = list(manager.devices.keys())[0]
        result = manager.process_heartbeat(first_id, {"cpu_usage": 50.0, "temperature_celsius": 65.0})
        assert result is True
        device = manager.get_device(first_id)
        assert device.status == "online"
        assert device.resources["cpu_usage"] == 50.0

    def test_process_heartbeat_unknown_device(self, manager):
        assert manager.process_heartbeat("unknown", {}) is False

    def test_create_group(self, manager):
        group = manager.create_group("test-group", "A test group")
        assert group.group_id is not None
        assert group.name == "test-group"

    def test_add_device_to_group(self, manager):
        group = manager.create_group("g1", "")
        device_id = list(manager.devices.keys())[0]
        assert manager.add_device_to_group(group.group_id, device_id) is True
        assert device_id in manager.groups[group.group_id].device_ids

    def test_add_device_to_group_not_found(self, manager):
        assert manager.add_device_to_group("nonexistent", "dev-001") is False

    def test_remove_device_from_group(self, manager):
        group = manager.create_group("g2", "")
        device_id = list(manager.devices.keys())[0]
        manager.add_device_to_group(group.group_id, device_id)
        assert manager.remove_device_from_group(group.group_id, device_id) is True
        assert device_id not in manager.groups[group.group_id].device_ids

    def test_list_groups(self, manager):
        manager.create_group("group-a", "")
        manager.create_group("group-b", "")
        assert len(manager.list_groups()) >= 2

    def test_queue_command(self, manager):
        first_id = list(manager.devices.keys())[0]
        cmd = manager.queue_command(first_id, "uptime")
        assert cmd.command_id is not None
        assert cmd.command == "uptime"
        assert cmd.status == "queued"

    def test_get_device_commands(self, manager):
        first_id = list(manager.devices.keys())[0]
        manager.queue_command(first_id, "echo hello")
        commands = manager.get_device_commands(first_id)
        assert len(commands) > 0

    def test_devices_summary(self, manager):
        summary = manager.get_devices_summary()
        assert "total" in summary
        assert "online" in summary
        assert "offline" in summary

    def test_schedule_firmware_update(self, manager):
        first_id = list(manager.devices.keys())[0]
        update = manager.schedule_firmware_update(first_id, "2.0.0",
                                                   "https://example.com/fw.img", "sha256:abc")
        assert update.update_id is not None
        assert update.target_version == "2.0.0"

    def test_get_firmware_updates(self, manager):
        first_id = list(manager.devices.keys())[0]
        manager.schedule_firmware_update(first_id, "2.0.0", "http://ex.com/fw", "sha256:x")
        updates = manager.get_firmware_updates(first_id)
        assert len(updates) > 0

    def test_device_type_filter(self, manager):
        pis = manager.list_devices(device_type="raspberry_pi")
        assert all(d.device_type == "raspberry_pi" for d in pis)

    def test_delete_device_removes_from_groups(self, manager):
        group = manager.create_group("g3", "")
        device_id = list(manager.devices.keys())[0]
        manager.add_device_to_group(group.group_id, device_id)
        manager.delete_device(device_id)
        assert device_id not in manager.groups[group.group_id].device_ids

    def test_initialize_and_close(self, manager):
        import asyncio
        asyncio.run(manager.initialize())
        asyncio.run(manager.close())

    def test_geolocation_update(self, manager):
        first_id = list(manager.devices.keys())[0]
        updated = manager.update_device(first_id, {"geolocation": {"lat": 52.52, "lng": 13.40, "label": "Berlin"}})
        assert updated.geolocation["lat"] == 52.52


class TestRemoteCommand:
    def test_command_creation(self):
        cmd = RemoteCommand("cmd-001", "dev-001", "ls -la")
        assert cmd.command_id == "cmd-001"
        assert cmd.device_id == "dev-001"
        assert cmd.command == "ls -la"
        assert cmd.status == "queued"

    def test_command_to_dict(self):
        cmd = RemoteCommand("cmd-002", "dev-001", "reboot")
        d = cmd.to_dict()
        assert d["command_id"] == "cmd-002"
        assert d["command"] == "reboot"
