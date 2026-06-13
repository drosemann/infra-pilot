import pytest
import asyncio
from datetime import datetime, timedelta
from services.integration_service.src.fleet.manager import (
    DeviceRegistry, FleetManager, FleetCommand, DeploymentPlan, FleetGroup,
    DeviceConfig, DeviceFirmware, DeviceCapability, DeviceStatus, DeviceType,
    FleetHealthReport,
)


class TestDeviceConfig:
    def test_create_device(self):
        device = DeviceConfig(device_id="dev-001", name="Sensor-1", device_type=DeviceType.SENSOR)
        assert device.device_id == "dev-001"
        assert device.status == DeviceStatus.PROVISIONING
        assert device.priority == 5

    def test_device_with_all_fields(self):
        fw = DeviceFirmware(version="2.0.0", build="20240101", release_date=datetime.utcnow(), checksum="abc123", download_url="https://example.com/fw.bin")
        cap = DeviceCapability(name="temperature", version="1.0", enabled=True)
        device = DeviceConfig(
            device_id="dev-002", name="Gateway-1", device_type=DeviceType.GATEWAY,
            location="Rack-A", status=DeviceStatus.ONLINE, firmware=fw,
            capabilities=[cap], battery_level=85.0, signal_strength=-65.0,
            cpu_usage=45.0, memory_usage=60.0,
        )
        assert device.firmware.version == "2.0.0"
        assert len(device.capabilities) == 1
        assert device.battery_level == 85.0

    def test_device_defaults(self):
        device = DeviceConfig(device_id="dev-003", name="Test")
        assert device.status == DeviceStatus.PROVISIONING
        assert device.power_state is False
        assert device.battery_level is None


class TestDeviceRegistry:
    def test_register_device(self):
        registry = DeviceRegistry()
        device = DeviceConfig(device_id="dev-001", name="Test Device")
        registry.register_device(device)
        assert registry.get_device("dev-001") is not None

    def test_register_duplicate(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="dev-001", name="A"))
        with pytest.raises(ValueError):
            registry.register_device(DeviceConfig(device_id="dev-001", name="B"))

    def test_get_device_not_found(self):
        registry = DeviceRegistry()
        assert registry.get_device("nonexistent") is None

    def test_update_device(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="dev-001", name="Original"))
        registry.update_device("dev-001", {"name": "Updated", "cpu_usage": 75.0})
        device = registry.get_device("dev-001")
        assert device.name == "Updated"
        assert device.cpu_usage == 75.0

    def test_update_nonexistent(self):
        registry = DeviceRegistry()
        assert registry.update_device("nope", {"name": "Nope"}) is None

    def test_deregister_device(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="dev-001", name="Temp"))
        assert registry.deregister_device("dev-001") is True
        assert registry.get_device("dev-001") is None

    def test_deregister_nonexistent(self):
        registry = DeviceRegistry()
        assert registry.deregister_device("ghost") is False

    def test_list_devices(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="A", device_type=DeviceType.SENSOR, status=DeviceStatus.ONLINE))
        registry.register_device(DeviceConfig(device_id="d2", name="B", device_type=DeviceType.GATEWAY, status=DeviceStatus.OFFLINE))
        registry.register_device(DeviceConfig(device_id="d3", name="C", device_type=DeviceType.SENSOR, status=DeviceStatus.ONLINE))
        assert len(registry.list_devices()) == 3
        assert len(registry.list_devices(status=DeviceStatus.ONLINE)) == 2
        assert len(registry.list_devices(device_type=DeviceType.GATEWAY)) == 1

    def test_search_devices(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="sensor-01", name="Temperature Sensor", location="Building A"))
        registry.register_device(DeviceConfig(device_id="gateway-01", name="Main Gateway", location="Building B"))
        results = registry.search_devices("temperature")
        assert len(results) == 1
        results = registry.search_devices("building")
        assert len(results) == 2

    def test_search_devices_by_tag(self):
        registry = DeviceRegistry()
        device = DeviceConfig(device_id="tagged-device", name="Tagged", tags={"floor": "3", "zone": "north"})
        registry.register_device(device)
        results = registry.search_devices("north")
        assert len(results) == 1

    def test_generate_health_report(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="A", status=DeviceStatus.ONLINE, cpu_usage=50, memory_usage=60))
        registry.register_device(DeviceConfig(device_id="d2", name="B", status=DeviceStatus.OFFLINE, cpu_usage=0, memory_usage=0))
        registry.register_device(DeviceConfig(device_id="d3", name="C", status=DeviceStatus.ERROR, cpu_usage=95, memory_usage=98))
        report = registry.generate_health_report("fleet-1")
        assert report.total_devices == 3
        assert report.online_count == 1
        assert report.offline_count == 1
        assert report.error_count == 1
        assert len(report.issues) >= 1

    def test_health_report_empty(self):
        registry = DeviceRegistry()
        report = registry.generate_health_report("empty-fleet")
        assert report.total_devices == 0
        assert report.avg_cpu == 0.0


class TestFleetGroups:
    def test_create_group(self):
        registry = DeviceRegistry()
        group = FleetGroup(group_id="g-001", name="Sensors", description="All temperature sensors")
        registry.create_group(group)
        assert registry.get_group("g-001") is not None

    def test_create_duplicate_group(self):
        registry = DeviceRegistry()
        registry.create_group(FleetGroup(group_id="g-001", name="A"))
        with pytest.raises(ValueError):
            registry.create_group(FleetGroup(group_id="g-001", name="B"))

    def test_update_group(self):
        registry = DeviceRegistry()
        registry.create_group(FleetGroup(group_id="g-001", name="Original"))
        registry.update_group("g-001", {"name": "Updated Group"})
        assert registry.get_group("g-001").name == "Updated Group"

    def test_delete_group(self):
        registry = DeviceRegistry()
        registry.create_group(FleetGroup(group_id="g-001", name="Temp"))
        assert registry.delete_group("g-001") is True
        assert registry.get_group("g-001") is None

    def test_list_groups(self):
        registry = DeviceRegistry()
        registry.create_group(FleetGroup(group_id="g-001", name="A"))
        registry.create_group(FleetGroup(group_id="g-002", name="B"))
        assert len(registry.list_groups()) == 2

    def test_add_device_to_group(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        registry.create_group(FleetGroup(group_id="g1", name="Group1"))
        assert registry.add_device_to_group("d1", "g1") is True
        assert "d1" in registry.get_group("g1").device_ids

    def test_add_device_to_nonexistent_group(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        assert registry.add_device_to_group("d1", "ghost") is False

    def test_remove_device_from_group(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        registry.create_group(FleetGroup(group_id="g1", name="Group1"))
        registry.add_device_to_group("d1", "g1")
        assert registry.remove_device_from_group("d1", "g1") is True
        assert "d1" not in registry.get_group("g1").device_ids

    def test_list_devices_by_group(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        registry.register_device(DeviceConfig(device_id="d2", name="Dev2"))
        registry.register_device(DeviceConfig(device_id="d3", name="Dev3"))
        registry.create_group(FleetGroup(group_id="g1", name="Group1"))
        registry.add_device_to_group("d1", "g1")
        registry.add_device_to_group("d2", "g1")
        grouped = registry.list_devices(group_id="g1")
        assert len(grouped) == 2

    def test_deregister_removes_from_groups(self):
        registry = DeviceRegistry()
        registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        registry.create_group(FleetGroup(group_id="g1", name="Group1"))
        registry.add_device_to_group("d1", "g1")
        registry.deregister_device("d1")
        assert "d1" not in registry.get_group("g1").device_ids


class TestDeployments:
    def test_create_deployment(self):
        registry = DeviceRegistry()
        plan = DeploymentPlan(plan_id="plan-001", name="Update all sensors", actions=[{"type": "reboot"}])
        result = registry.create_deployment(plan)
        assert result.plan_id == "plan-001"
        assert result.status == "draft"

    def test_create_duplicate_deployment(self):
        registry = DeviceRegistry()
        registry.create_deployment(DeploymentPlan(plan_id="p1", name="P1"))
        with pytest.raises(ValueError):
            registry.create_deployment(DeploymentPlan(plan_id="p1", name="P2"))

    def test_get_deployment(self):
        registry = DeviceRegistry()
        registry.create_deployment(DeploymentPlan(plan_id="p1", name="Test"))
        assert registry.get_deployment("p1") is not None

    def test_update_deployment(self):
        registry = DeviceRegistry()
        registry.create_deployment(DeploymentPlan(plan_id="p1", name="Initial"))
        registry.update_deployment("p1", {"status": "in_progress", "progress": 50})
        plan = registry.get_deployment("p1")
        assert plan.status == "in_progress"
        assert plan.progress == 50

    def test_list_deployments(self):
        registry = DeviceRegistry()
        registry.create_deployment(DeploymentPlan(plan_id="p1", name="A", status="draft"))
        registry.create_deployment(DeploymentPlan(plan_id="p2", name="B", status="completed"))
        assert len(registry.list_deployments()) == 2
        assert len(registry.list_deployments(status="draft")) == 1


class TestFleetCommands:
    def test_queue_command(self):
        registry = DeviceRegistry()
        cmd = FleetCommand(command_id="cmd-001", device_id="dev-001", command_type="reboot")
        registry.queue_command(cmd)
        assert registry.get_command("cmd-001") is not None

    def test_get_command(self):
        registry = DeviceRegistry()
        registry.queue_command(FleetCommand(command_id="c1", device_id="d1", command_type="restart"))
        cmd = registry.get_command("c1")
        assert cmd.command_id == "c1"

    def test_update_command(self):
        registry = DeviceRegistry()
        registry.queue_command(FleetCommand(command_id="c1", device_id="d1", command_type="restart"))
        registry.update_command("c1", {"status": "completed", "result": {"ok": True}})
        cmd = registry.get_command("c1")
        assert cmd.status == "completed"
        assert cmd.result == {"ok": True}

    def test_list_commands_by_device(self):
        registry = DeviceRegistry()
        registry.queue_command(FleetCommand(command_id="c1", device_id="d1", command_type="a"))
        registry.queue_command(FleetCommand(command_id="c2", device_id="d1", command_type="b"))
        registry.queue_command(FleetCommand(command_id="c3", device_id="d2", command_type="c"))
        assert len(registry.list_commands(device_id="d1")) == 2
        assert len(registry.list_commands(device_id="d2")) == 1

    def test_list_commands_by_status(self):
        registry = DeviceRegistry()
        cmd1 = FleetCommand(command_id="c1", device_id="d1", command_type="a", status="pending")
        cmd2 = FleetCommand(command_id="c2", device_id="d1", command_type="b", status="completed")
        registry.queue_command(cmd1)
        registry.queue_command(cmd2)
        assert len(registry.list_commands(status="pending")) == 1
        assert len(registry.list_commands(status="completed")) == 1

    def test_command_priority_sorting(self):
        registry = DeviceRegistry()
        low = FleetCommand(command_id="c1", device_id="d1", command_type="a", priority=1)
        high = FleetCommand(command_id="c2", device_id="d1", command_type="b", priority=10)
        registry.queue_command(low)
        registry.queue_command(high)
        cmds = registry.list_commands(device_id="d1")
        assert cmds[0].priority >= cmds[-1].priority


class TestFleetManager:
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1", status=DeviceStatus.OFFLINE))
        await manager.handle_heartbeat("d1", {"cpu": 30, "memory": 50, "battery": 90})
        device = manager.registry.get_device("d1")
        assert device.status == DeviceStatus.ONLINE
        assert device.cpu_usage == 30
        assert device.battery_level == 90

    @pytest.mark.asyncio
    async def test_handle_heartbeat_unknown_device(self):
        manager = FleetManager()
        with pytest.raises(ValueError):
            await manager.handle_heartbeat("unknown-device")

    @pytest.mark.asyncio
    async def test_check_stale_devices(self):
        manager = FleetManager()
        device = DeviceConfig(device_id="d1", name="Stale", status=DeviceStatus.ONLINE)
        device.last_seen = datetime.utcnow() - timedelta(hours=2)
        manager.registry.register_device(device)
        await manager.check_stale_devices()
        assert manager.registry.get_device("d1").status == DeviceStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_execute_command(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        manager.registry.queue_command(FleetCommand(command_id="c1", device_id="d1", command_type="reboot"))
        result = await manager.execute_command("c1")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self):
        manager = FleetManager()
        result = await manager.execute_command("ghost")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_deployment(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        manager.registry.create_group(FleetGroup(group_id="g1", name="Group1"))
        manager.registry.add_device_to_group("d1", "g1")
        plan = DeploymentPlan(plan_id="p1", name="Test Deploy", target_groups=["g1"], actions=[{"type": "reboot", "payload": {}}])
        manager.registry.create_deployment(plan)
        result = await manager.execute_deployment("p1")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_deployment_not_found(self):
        manager = FleetManager()
        result = await manager.execute_deployment("nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_batch_register(self):
        manager = FleetManager()
        configs = [DeviceConfig(device_id=f"batch-{i}", name=f"Batch-{i}") for i in range(10)]
        registered = manager.batch_register(configs)
        assert len(registered) == 10

    @pytest.mark.asyncio
    async def test_batch_command(self):
        manager = FleetManager()
        for i in range(3):
            manager.registry.register_device(DeviceConfig(device_id=f"d{i}", name=f"Dev{i}"))
        results = await manager.batch_command(["d0", "d1", "d2"], "ping", {})
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_health_check(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1", status=DeviceStatus.ONLINE))
        health = await manager.health_check()
        assert health["total_devices"] == 1
        assert health["online"] == 1

    @pytest.mark.asyncio
    async def test_health_check_stopped(self):
        manager = FleetManager()
        health = await manager.health_check()
        assert health["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_ota_update(self):
        manager = FleetManager()
        fw = DeviceFirmware(version="2.0.0", build="B001", release_date=datetime.utcnow(), checksum="abc", download_url="https://fw.example.com/v2.bin")
        manager.add_firmware(fw)
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.ota_update(["d1"], "2.0.0")
        assert result["status"] == "completed"
        assert manager.registry.get_device("d1").firmware.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_ota_update_no_firmware(self):
        manager = FleetManager()
        result = await manager.ota_update(["d1"], "nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_reboot_devices(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.reboot_devices(["d1"])
        assert result is not None

    @pytest.mark.asyncio
    async def test_shutdown_devices(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.shutdown_devices(["d1"])
        assert result is not None

    @pytest.mark.asyncio
    async def test_configure_devices(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.configure_devices(["d1"], {"setting": "value"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_collect_logs(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.collect_logs(["d1"], "system")
        assert result is not None

    @pytest.mark.asyncio
    async def test_reset_devices(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        result = await manager.reset_devices(["d1"])
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_device_analytics(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Analytics Test", cpu_usage=55, memory_usage=70))
        analytics = await manager.get_device_analytics("d1")
        assert analytics["device_id"] == "d1"
        assert analytics["cpu"] == 55
        assert analytics["memory"] == 70

    @pytest.mark.asyncio
    async def test_get_device_analytics_not_found(self):
        manager = FleetManager()
        analytics = await manager.get_device_analytics("ghost")
        assert "error" in analytics

    def test_group_devices_by_type(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="s1", name="Sensor", device_type=DeviceType.SENSOR))
        manager.registry.register_device(DeviceConfig(device_id="g1", name="Gateway", device_type=DeviceType.GATEWAY))
        manager.registry.register_device(DeviceConfig(device_id="s2", name="Sensor2", device_type=DeviceType.SENSOR))
        groups = manager.group_devices_by_type()
        assert len(groups["sensor"]) == 2
        assert len(groups["gateway"]) == 1

    def test_group_devices_by_status(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Online", status=DeviceStatus.ONLINE))
        manager.registry.register_device(DeviceConfig(device_id="d2", name="Offline", status=DeviceStatus.OFFLINE))
        groups = manager.group_devices_by_status()
        assert len(groups["online"]) == 1
        assert len(groups["offline"]) == 1

    def test_group_devices_by_location(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="A", location="Rack-1"))
        manager.registry.register_device(DeviceConfig(device_id="d2", name="B", location="Rack-2"))
        manager.registry.register_device(DeviceConfig(device_id="d3", name="C"))
        groups = manager.group_devices_by_location()
        assert "Rack-1" in groups
        assert "unknown" in groups

    def test_search_fleet(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="sensor-temp", name="Temperature Sensor", location="Lab"))
        manager.registry.register_device(DeviceConfig(device_id="gateway-main", name="Main Gateway"))
        result = manager.search_fleet("temperature")
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_bulk_status_update(self):
        manager = FleetManager()
        manager.registry.register_device(DeviceConfig(device_id="d1", name="A", status=DeviceStatus.ONLINE))
        manager.registry.register_device(DeviceConfig(device_id="d2", name="B", status=DeviceStatus.ONLINE))
        result = await manager.bulk_status_update(["d1", "d2"], DeviceStatus.MAINTENANCE)
        assert result["updated"] == 2
        assert manager.registry.get_device("d1").status == DeviceStatus.MAINTENANCE

    def test_firmware_management(self):
        manager = FleetManager()
        fw = DeviceFirmware(version="1.0.0", build="B1", release_date=datetime.utcnow(), checksum="x", download_url="https://example.com/fw.bin")
        manager.add_firmware(fw)
        fw2 = DeviceFirmware(version="2.0.0", build="B2", release_date=datetime.utcnow(), checksum="y", download_url="https://example.com/fw2.bin")
        manager.add_firmware(fw2)
        assert manager.get_firmware("1.0.0") is not None
        assert manager.get_firmware("3.0.0") is None
        assert len(manager.list_firmware()) == 2

    def test_is_latest_firmware(self):
        manager = FleetManager()
        fw_old = DeviceFirmware(version="1.0.0", build="B1", release_date=datetime.utcnow(), checksum="x", download_url="https://example.com/fw.bin")
        fw_new = DeviceFirmware(version="2.0.0", build="B2", release_date=datetime.utcnow(), checksum="y", download_url="https://example.com/fw2.bin")
        manager.add_firmware(fw_new)
        device = DeviceConfig(device_id="d1", name="Dev", firmware=fw_old)
        manager.registry.register_device(device)
        assert manager.is_latest_firmware("d1") is False

    def test_schedule_action(self):
        manager = FleetManager()
        future = datetime.utcnow() + timedelta(hours=1)
        manager.schedule_action("reboot", ["d1"], future, {"force": True})
        assert len(manager._scheduled_actions) == 1

    def test_create_deployment_from_template(self):
        manager = FleetManager()
        template = {
            "description": "Test template",
            "target_groups": ["g1"],
            "target_devices": ["d1"],
            "actions": [{"type": "reboot", "payload": {}}],
        }
        plan = manager.registry.create_deployment(DeploymentPlan(
            plan_id="template-plan", name="Template Deploy",
            description=template["description"],
            target_groups=template["target_groups"],
            target_devices=template["target_devices"],
            actions=template["actions"],
        ))
        assert plan.name == "Template Deploy"
        assert len(plan.actions) == 1

    @pytest.mark.asyncio
    async def test_event_handling(self):
        manager = FleetManager()
        events = []
        async def handler(data):
            events.append(data)
        manager.register_event_handler("heartbeat", handler)
        manager.registry.register_device(DeviceConfig(device_id="d1", name="Dev1"))
        await manager.handle_heartbeat("d1")
        await asyncio.sleep(0.1)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        manager = FleetManager()
        device = DeviceConfig(device_id="d1", name="Overloaded", cpu_usage=99, memory_usage=98, status=DeviceStatus.ONLINE)
        manager.registry.register_device(device)
        manager._running = True
        await asyncio.wait_for(manager.run_health_checks(interval=1), timeout=1)
        assert device.status == DeviceStatus.DEGRADED
        manager._running = False

    @pytest.mark.asyncio
    async def test_start_stop(self):
        manager = FleetManager()
        await manager.start()
        assert manager._running is True
        assert len(manager._tasks) > 0
        manager.stop()
        assert manager._running is False
