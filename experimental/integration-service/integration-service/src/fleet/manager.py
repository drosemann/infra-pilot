import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    PROVISIONING = "provisioning"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    RETIRED = "retired"


class DeviceType(Enum):
    SENSOR = "sensor"
    GATEWAY = "gateway"
    EDGE_NODE = "edge_node"
    ACTUATOR = "actuator"
    CAMERA = "camera"
    ROUTER = "router"
    SERVER = "server"
    UNKNOWN = "unknown"


@dataclass
class DeviceFirmware:
    version: str
    build: str
    release_date: datetime
    checksum: str
    download_url: str
    changelog: List[str] = field(default_factory=list)
    required: bool = False


@dataclass
class DeviceCapability:
    name: str
    version: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceConfig:
    device_id: str
    name: str
    device_type: DeviceType = DeviceType.UNKNOWN
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: DeviceStatus = DeviceStatus.PROVISIONING
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    firmware: Optional[DeviceFirmware] = None
    capabilities: List[DeviceCapability] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    owner: Optional[str] = None
    group: Optional[str] = None
    priority: int = 5
    power_state: bool = False
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    temperature: Optional[float] = None


@dataclass
class FleetGroup:
    group_id: str
    name: str
    description: str = ""
    device_ids: Set[str] = field(default_factory=set)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    parent_group_id: Optional[str] = None
    policies: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentPlan:
    plan_id: str
    name: str
    description: str = ""
    target_groups: List[str] = field(default_factory=list)
    target_devices: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    rollback_plan: Optional[str] = None
    approved_by: Optional[str] = None


@dataclass
class FleetCommand:
    command_id: str
    device_id: str
    command_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timeout: int = 30
    priority: int = 5


@dataclass
class FleetHealthReport:
    report_id: str
    fleet_id: str
    total_devices: int
    online_count: int
    offline_count: int
    degraded_count: int
    error_count: int
    avg_cpu: float
    avg_memory: float
    avg_signal: float
    avg_battery: float
    generated_at: datetime = field(default_factory=datetime.utcnow)
    issues: List[Dict[str, Any]] = field(default_factory=list)


class DeviceRegistry:
    def __init__(self):
        self._devices: Dict[str, DeviceConfig] = {}
        self._groups: Dict[str, FleetGroup] = {}
        self._commands: Dict[str, FleetCommand] = {}
        self._deployments: Dict[str, DeploymentPlan] = {}

    def register_device(self, config: DeviceConfig) -> DeviceConfig:
        if config.device_id in self._devices:
            raise ValueError(f"Device {config.device_id} already registered")
        self._devices[config.device_id] = config
        return config

    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        return self._devices.get(device_id)

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> Optional[DeviceConfig]:
        device = self._devices.get(device_id)
        if not device:
            return None
        for key, value in updates.items():
            if hasattr(device, key):
                setattr(device, key, value)
        device.updated_at = datetime.utcnow()
        return device

    def deregister_device(self, device_id: str) -> bool:
        if device_id in self._devices:
            del self._devices[device_id]
            for group in self._groups.values():
                group.device_ids.discard(device_id)
            return True
        return False

    def list_devices(self, status: Optional[DeviceStatus] = None,
                     device_type: Optional[DeviceType] = None,
                     group_id: Optional[str] = None) -> List[DeviceConfig]:
        devices = list(self._devices.values())
        if status:
            devices = [d for d in devices if d.status == status]
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        if group_id:
            group = self._groups.get(group_id)
            if group:
                devices = [d for d in devices if d.device_id in group.device_ids]
        return devices

    def create_group(self, group: FleetGroup) -> FleetGroup:
        if group.group_id in self._groups:
            raise ValueError(f"Group {group.group_id} already exists")
        self._groups[group.group_id] = group
        return group

    def get_group(self, group_id: str) -> Optional[FleetGroup]:
        return self._groups.get(group_id)

    def update_group(self, group_id: str, updates: Dict[str, Any]) -> Optional[FleetGroup]:
        group = self._groups.get(group_id)
        if not group:
            return None
        for key, value in updates.items():
            if key == "device_ids" and isinstance(value, list):
                group.device_ids = set(value)
            elif hasattr(group, key):
                setattr(group, key, value)
        group.updated_at = datetime.utcnow()
        return group

    def delete_group(self, group_id: str) -> bool:
        if group_id in self._groups:
            del self._groups[group_id]
            return True
        return False

    def add_device_to_group(self, device_id: str, group_id: str) -> bool:
        group = self._groups.get(group_id)
        if not group or device_id not in self._devices:
            return False
        group.device_ids.add(device_id)
        group.updated_at = datetime.utcnow()
        return True

    def remove_device_from_group(self, device_id: str, group_id: str) -> bool:
        group = self._groups.get(group_id)
        if not group:
            return False
        group.device_ids.discard(device_id)
        group.updated_at = datetime.utcnow()
        return True

    def list_groups(self) -> List[FleetGroup]:
        return list(self._groups.values())

    def create_deployment(self, plan: DeploymentPlan) -> DeploymentPlan:
        if plan.plan_id in self._deployments:
            raise ValueError(f"Deployment plan {plan.plan_id} already exists")
        self._deployments[plan.plan_id] = plan
        return plan

    def get_deployment(self, plan_id: str) -> Optional[DeploymentPlan]:
        return self._deployments.get(plan_id)

    def update_deployment(self, plan_id: str, updates: Dict[str, Any]) -> Optional[DeploymentPlan]:
        plan = self._deployments.get(plan_id)
        if not plan:
            return None
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()
        return plan

    def list_deployments(self, status: Optional[str] = None) -> List[DeploymentPlan]:
        if status:
            return [p for p in self._deployments.values() if p.status == status]
        return list(self._deployments.values())

    def queue_command(self, command: FleetCommand) -> FleetCommand:
        if command.command_id in self._commands:
            raise ValueError(f"Command {command.command_id} already exists")
        self._commands[command.command_id] = command
        return command

    def get_command(self, command_id: str) -> Optional[FleetCommand]:
        return self._commands.get(command_id)

    def update_command(self, command_id: str, updates: Dict[str, Any]) -> Optional[FleetCommand]:
        cmd = self._commands.get(command_id)
        if not cmd:
            return None
        for key, value in updates.items():
            if hasattr(cmd, key):
                setattr(cmd, key, value)
        return cmd

    def list_commands(self, device_id: Optional[str] = None,
                      status: Optional[str] = None) -> List[FleetCommand]:
        cmds = list(self._commands.values())
        if device_id:
            cmds = [c for c in cmds if c.device_id == device_id]
        if status:
            cmds = [c for c in cmds if c.status == status]
        return sorted(cmds, key=lambda c: (-c.priority, c.created_at))

    def search_devices(self, query: str) -> List[DeviceConfig]:
        query = query.lower()
        results = []
        for device in self._devices.values():
            if (query in device.name.lower() or
                query in device.device_id.lower() or
                query in str(device.location or "").lower() or
                query in str(device.owner or "").lower() or
                any(query in v.lower() for v in device.tags.values())):
                results.append(device)
        return results

    def generate_health_report(self, fleet_id: str) -> FleetHealthReport:
        devices = list(self._devices.values())
        total = len(devices)
        online = sum(1 for d in devices if d.status == DeviceStatus.ONLINE)
        offline = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE)
        degraded = sum(1 for d in devices if d.status == DeviceStatus.DEGRADED)
        error = sum(1 for d in devices if d.status == DeviceStatus.ERROR)
        cpus = [d.cpu_usage for d in devices if d.cpu_usage is not None]
        mems = [d.memory_usage for d in devices if d.memory_usage is not None]
        sigs = [d.signal_strength for d in devices if d.signal_strength is not None]
        bats = [d.battery_level for d in devices if d.battery_level is not None]
        issues = []
        for d in devices:
            if d.cpu_usage and d.cpu_usage > 90:
                issues.append({"device_id": d.device_id, "issue": "high_cpu", "value": d.cpu_usage})
            if d.memory_usage and d.memory_usage > 90:
                issues.append({"device_id": d.device_id, "issue": "high_memory", "value": d.memory_usage})
            if d.battery_level and d.battery_level < 20:
                issues.append({"device_id": d.device_id, "issue": "low_battery", "value": d.battery_level})
            if d.signal_strength and d.signal_strength < -80:
                issues.append({"device_id": d.device_id, "issue": "weak_signal", "value": d.signal_strength})
            if d.status == DeviceStatus.ERROR:
                issues.append({"device_id": d.device_id, "issue": "device_error", "value": 0})
        return FleetHealthReport(
            report_id=str(uuid.uuid4()),
            fleet_id=fleet_id,
            total_devices=total,
            online_count=online,
            offline_count=offline,
            degraded_count=degraded,
            error_count=error,
            avg_cpu=statistics.mean(cpus) if cpus else 0.0,
            avg_memory=statistics.mean(mems) if mems else 0.0,
            avg_signal=statistics.mean(sigs) if sigs else 0.0,
            avg_battery=statistics.mean(bats) if bats else 0.0,
            issues=issues,
        )


import statistics


class FleetManager:
    def __init__(self):
        self.registry = DeviceRegistry()
        self._heartbeat_timeout: int = 300
        self._firmware_repo: Dict[str, DeviceFirmware] = {}
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._scheduled_actions: List[Dict[str, Any]] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []

    from collections import defaultdict

    def register_event_handler(self, event: str, handler: Callable):
        self._event_handlers[event].append(handler)

    async def emit_event(self, event: str, data: Any):
        for handler in self._event_handlers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception:
                pass

    async def handle_heartbeat(self, device_id: str, metrics: Optional[Dict[str, Any]] = None):
        device = self.registry.get_device(device_id)
        if not device:
            raise ValueError(f"Unknown device: {device_id}")
        device.last_seen = datetime.utcnow()
        if device.status in (DeviceStatus.OFFLINE, DeviceStatus.ERROR):
            device.status = DeviceStatus.ONLINE
        if metrics:
            device.cpu_usage = metrics.get("cpu")
            device.memory_usage = metrics.get("memory")
            device.battery_level = metrics.get("battery")
            device.signal_strength = metrics.get("signal")
            device.temperature = metrics.get("temperature")
        device.updated_at = datetime.utcnow()
        await self.emit_event("heartbeat", {"device_id": device_id, "metrics": metrics})

    async def check_stale_devices(self):
        now = datetime.utcnow()
        for device in self.registry.list_devices():
            if device.status == DeviceStatus.ONLINE and device.last_seen:
                elapsed = (now - device.last_seen).total_seconds()
                if elapsed > self._heartbeat_timeout:
                    device.status = DeviceStatus.OFFLINE
                    await self.emit_event("device_offline", {"device_id": device.device_id})

    async def run_health_checks(self, interval: int = 60):
        while self._running:
            for device in self.registry.list_devices():
                checks = []
                if device.cpu_usage and device.cpu_usage > 95:
                    checks.append("critical_cpu")
                if device.memory_usage and device.memory_usage > 95:
                    checks.append("critical_memory")
                if device.disk_usage and device.disk_usage > 95:
                    checks.append("critical_disk")
                if device.temperature and device.temperature > 85:
                    checks.append("overheating")
                if checks:
                    device.status = DeviceStatus.DEGRADED
                    await self.emit_event("health_degraded", {"device_id": device.device_id, "issues": checks})
            await asyncio.sleep(interval)

    async def execute_command(self, command_id: str) -> Dict[str, Any]:
        command = self.registry.get_command(command_id)
        if not command:
            return {"error": "Command not found"}
        command.status = "executing"
        command.executed_at = datetime.utcnow()
        try:
            result = {"status": "success", "output": f"Executed {command.command_type} on {command.device_id}"}
            command.result = result
            command.status = "completed"
            await self.emit_event("command_completed", {"command_id": command_id, "result": result})
            return result
        except Exception as e:
            command.error = str(e)
            command.status = "failed"
            await self.emit_event("command_failed", {"command_id": command_id, "error": str(e)})
            return {"error": str(e)}

    async def execute_deployment(self, plan_id: str) -> Dict[str, Any]:
        plan = self.registry.get_deployment(plan_id)
        if not plan:
            return {"error": "Deployment plan not found"}
        plan.status = "in_progress"
        plan.started_at = datetime.utcnow()
        target_device_ids: Set[str] = set()
        for gid in plan.target_groups:
            group = self.registry.get_group(gid)
            if group:
                target_device_ids.update(group.device_ids)
        target_device_ids.update(plan.target_devices)
        total = len(target_device_ids)
        completed = 0
        results = []
        for device_id in target_device_ids:
            device = self.registry.get_device(device_id)
            if not device:
                continue
            for action in plan.actions:
                action_type = action.get("type")
                action_payload = action.get("payload", {})
                cmd = FleetCommand(
                    command_id=str(uuid.uuid4()),
                    device_id=device_id,
                    command_type=action_type,
                    payload=action_payload,
                )
                self.registry.queue_command(cmd)
                result = await self.execute_command(cmd.command_id)
                results.append({"device_id": device_id, "action": action_type, "result": result})
            completed += 1
            plan.progress = int((completed / total) * 100) if total > 0 else 100
            plan.updated_at = datetime.utcnow()
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        plan.progress = 100
        await self.emit_event("deployment_completed", {"plan_id": plan_id, "results": results})
        return {"status": "completed", "total": total, "results": results}

    def add_firmware(self, firmware: DeviceFirmware):
        self._firmware_repo[firmware.version] = firmware

    def get_firmware(self, version: str) -> Optional[DeviceFirmware]:
        return self._firmware_repo.get(version)

    def list_firmware(self) -> List[DeviceFirmware]:
        return list(self._firmware_repo.values())

    def is_latest_firmware(self, device_id: str) -> bool:
        device = self.registry.get_device(device_id)
        if not device or not device.firmware or not self._firmware_repo:
            return True
        latest_version = max(self._firmware_repo.keys())
        return device.firmware.version >= latest_version

    def schedule_action(self, action: str, device_ids: List[str],
                        execute_at: datetime, payload: Optional[Dict[str, Any]] = None):
        self._scheduled_actions.append({
            "action": action,
            "device_ids": device_ids,
            "execute_at": execute_at,
            "payload": payload or {},
            "created_at": datetime.utcnow(),
        })

    async def process_scheduled_actions(self):
        now = datetime.utcnow()
        pending = [a for a in self._scheduled_actions if a["execute_at"] <= now]
        self._scheduled_actions = [a for a in self._scheduled_actions if a["execute_at"] > now]
        for action in pending:
            for device_id in action["device_ids"]:
                cmd = FleetCommand(
                    command_id=str(uuid.uuid4()),
                    device_id=device_id,
                    command_type=action["action"],
                    payload=action["payload"],
                )
                self.registry.queue_command(cmd)
                await self.execute_command(cmd.command_id)

    async def start(self):
        self._running = True
        self._tasks.append(asyncio.create_task(self.run_health_checks()))
        self._tasks.append(asyncio.create_task(self._stale_device_checker()))
        self._tasks.append(asyncio.create_task(self._scheduled_action_processor()))

    def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    async def _stale_device_checker(self):
        while self._running:
            await self.check_stale_devices()
            await asyncio.sleep(60)

    async def _scheduled_action_processor(self):
        while self._running:
            await self.process_scheduled_actions()
            await asyncio.sleep(30)

    async def health_check(self) -> Dict[str, Any]:
        report = self.registry.generate_health_report("main")
        return {
            "status": "healthy" if self._running else "stopped",
            "total_devices": report.total_devices,
            "online": report.online_count,
            "offline": report.offline_count,
            "degraded": report.degraded_count,
            "error": report.error_count,
            "avg_cpu": report.avg_cpu,
            "avg_memory": report.avg_memory,
            "avg_signal": report.avg_signal,
            "avg_battery": report.avg_battery,
            "issues": report.issues,
            "pending_commands": len(self.registry.list_commands(status="pending")),
            "deployments": len(self.registry.list_deployments()),
            "groups": len(self.registry.list_groups()),
        }

    def batch_register(self, configs: List[DeviceConfig]) -> List[DeviceConfig]:
        registered = []
        for config in configs:
            try:
                self.registry.register_device(config)
                registered.append(config)
            except ValueError:
                pass
        return registered

    async def batch_command(self, device_ids: List[str], command_type: str,
                            payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = []
        for device_id in device_ids:
            cmd = FleetCommand(
                command_id=str(uuid.uuid4()),
                device_id=device_id,
                command_type=command_type,
                payload=payload or {},
            )
            self.registry.queue_command(cmd)
            result = await self.execute_command(cmd.command_id)
            results.append({"device_id": device_id, "result": result})
        return results

    async def ota_update(self, device_ids: List[str], firmware_version: str) -> Dict[str, Any]:
        firmware = self._firmware_repo.get(firmware_version)
        if not firmware:
            return {"error": f"Firmware {firmware_version} not found"}
        results = []
        for device_id in device_ids:
            device = self.registry.get_device(device_id)
            if not device:
                results.append({"device_id": device_id, "error": "Device not found"})
                continue
            cmd = FleetCommand(
                command_id=str(uuid.uuid4()),
                device_id=device_id,
                command_type="firmware_update",
                payload={"firmware_version": firmware_version, "download_url": firmware.download_url, "checksum": firmware.checksum},
            )
            self.registry.queue_command(cmd)
            result = await self.execute_command(cmd.command_id)
            device.firmware = firmware
            device.updated_at = datetime.utcnow()
            results.append({"device_id": device_id, "result": result})
        return {"status": "completed", "firmware": firmware_version, "results": results}

    async def reboot_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        return await self.batch_command(device_ids, "reboot", {"force": False})

    async def shutdown_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        return await self.batch_command(device_ids, "shutdown", {"force": True})

    async def configure_devices(self, device_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        return await self.batch_command(device_ids, "configure", config)

    async def collect_logs(self, device_ids: List[str], log_type: str = "system") -> Dict[str, Any]:
        return await self.batch_command(device_ids, "collect_logs", {"log_type": log_type})

    async def reset_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        return await self.batch_command(device_ids, "factory_reset", {})

    async def get_device_analytics(self, device_id: str) -> Dict[str, Any]:
        device = self.registry.get_device(device_id)
        if not device:
            return {"error": "Device not found"}
        return {
            "device_id": device.device_id,
            "name": device.name,
            "device_type": device.device_type.value,
            "status": device.status.value,
            "uptime": (datetime.utcnow() - device.created_at).total_seconds() if device.created_at else 0,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "cpu": device.cpu_usage,
            "memory": device.memory_usage,
            "disk": device.disk_usage,
            "battery": device.battery_level,
            "signal": device.signal_strength,
            "temperature": device.temperature,
            "firmware_version": device.firmware.version if device.firmware else None,
            "capabilities": [c.name for c in device.capabilities],
            "tags": device.tags,
            "commands_sent": len(self.registry.list_commands(device_id=device_id)),
        }

    def group_devices_by_type(self) -> Dict[str, List[DeviceConfig]]:
        groups: Dict[str, List[DeviceConfig]] = {}
        for device in self.registry.list_devices():
            dtype = device.device_type.value
            if dtype not in groups:
                groups[dtype] = []
            groups[dtype].append(device)
        return groups

    def group_devices_by_status(self) -> Dict[str, List[DeviceConfig]]:
        groups: Dict[str, List[DeviceConfig]] = {}
        for device in self.registry.list_devices():
            status = device.status.value
            if status not in groups:
                groups[status] = []
            groups[status].append(device)
        return groups

    def group_devices_by_location(self) -> Dict[str, List[DeviceConfig]]:
        groups: Dict[str, List[DeviceConfig]] = {}
        for device in self.registry.list_devices():
            loc = device.location or "unknown"
            if loc not in groups:
                groups[loc] = []
            groups[loc].append(device)
        return groups

    def search_fleet(self, query: str) -> Dict[str, Any]:
        devices = self.registry.search_devices(query)
        return {
            "query": query,
            "results": devices,
            "count": len(devices),
        }

    async def bulk_status_update(self, device_ids: List[str], status: DeviceStatus) -> Dict[str, Any]:
        updated = []
        for device_id in device_ids:
            device = self.registry.update_device(device_id, {"status": status})
            if device:
                updated.append(device_id)
        return {"status": "completed", "updated": len(updated), "device_ids": updated}

    async def create_deployment_from_template(self, name: str, template: Dict[str, Any]) -> DeploymentPlan:
        plan = DeploymentPlan(
            plan_id=str(uuid.uuid4()),
            name=name,
            description=template.get("description", ""),
            target_groups=template.get("target_groups", []),
            target_devices=template.get("target_devices", []),
            actions=template.get("actions", []),
        )
        return self.registry.create_deployment(plan)
