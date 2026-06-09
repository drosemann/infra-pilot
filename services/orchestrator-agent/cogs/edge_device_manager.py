"""Edge Device Manager Cog - Register, monitor, and manage edge devices."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional
from collections import defaultdict

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class EdgeDevice:
    """Represents an edge device registered in the system."""

    def __init__(self, device_id: str, name: str, device_type: str, hardware_id: str):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.hardware_id = hardware_id
        self.fingerprint = ""
        self.geolocation: dict[str, Any] = {"lat": 0.0, "lng": 0.0, "label": ""}
        self.tags: list[str] = []
        self.firmware_version = ""
        self.agent_version = ""
        self.status = "provisioning"
        self.last_heartbeat: Optional[datetime] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: dict[str, Any] = {}
        self.resources: dict[str, Any] = {
            "cpu_cores": 0,
            "cpu_usage": 0.0,
            "memory_total_mb": 0,
            "memory_used_mb": 0,
            "disk_total_gb": 0,
            "disk_used_gb": 0,
            "temperature_celsius": 0.0,
            "uptime_seconds": 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type,
            "hardware_id": self.hardware_id,
            "fingerprint": self.fingerprint,
            "geolocation": self.geolocation,
            "tags": self.tags,
            "firmware_version": self.firmware_version,
            "agent_version": self.agent_version,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "resources": self.resources,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EdgeDevice":
        device = cls(data["device_id"], data["name"], data["device_type"], data["hardware_id"])
        device.fingerprint = data.get("fingerprint", "")
        device.geolocation = data.get("geolocation", {"lat": 0.0, "lng": 0.0, "label": ""})
        device.tags = data.get("tags", [])
        device.firmware_version = data.get("firmware_version", "")
        device.agent_version = data.get("agent_version", "")
        device.status = data.get("status", "provisioning")
        if data.get("last_heartbeat"):
            device.last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        if data.get("created_at"):
            device.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            device.updated_at = datetime.fromisoformat(data["updated_at"])
        device.metadata = data.get("metadata", {})
        device.resources = data.get("resources", {})
        return device


class DeviceGroup:
    """Group edge devices for organizational purposes."""

    def __init__(self, group_id: str, name: str, description: str = ""):
        self.group_id = group_id
        self.name = name
        self.description = description
        self.device_ids: list[str] = []
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "device_ids": self.device_ids,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FirmwareUpdate:
    """Represents a firmware update job for an edge device."""

    def __init__(self, update_id: str, device_id: str, target_version: str):
        self.update_id = update_id
        self.device_id = device_id
        self.target_version = target_version
        self.status = "pending"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.artifact_url: Optional[str] = None
        self.checksum: Optional[str] = None
        self.progress_pct: float = 0.0
        self.retry_count: int = 0
        self.max_retries: int = 3
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "update_id": self.update_id,
            "device_id": self.device_id,
            "target_version": self.target_version,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "artifact_url": self.artifact_url,
            "checksum": self.checksum,
            "progress_pct": self.progress_pct,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
        }


class RemoteCommand:
    """Represents a remote command to execute on an edge device."""

    def __init__(self, command_id: str, device_id: str, command: str):
        self.command_id = command_id
        self.device_id = device_id
        self.command = command
        self.status = "queued"
        self.executed_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.exit_code: Optional[int] = None
        self.stdout: str = ""
        self.stderr: str = ""
        self.timeout_seconds: int = 30
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "device_id": self.device_id,
            "command": self.command,
            "status": self.status,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:1000],
            "stderr": self.stderr[:1000],
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
        }


class EdgeDeviceManager:
    """Manager class for edge device lifecycle and monitoring."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.devices: dict[str, EdgeDevice] = {}
        self.groups: dict[str, DeviceGroup] = {}
        self.firmware_updates: dict[str, FirmwareUpdate] = {}
        self.command_queue: dict[str, list[RemoteCommand]] = defaultdict(list)
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._seed_devices()

    def _seed_devices(self):
        """Seed some example edge devices for demo purposes."""
        demo_devices = [
            ("dev-001", "raspberry-pi-4-factory", "raspberry_pi", "b8:27:eb:12:34:56"),
            ("dev-002", "jetson-nano-line-1", "jetson_nano", "00:04:4b:78:90:12"),
            ("dev-003", "raspberry-pi-5-warehouse", "raspberry_pi", "b8:27:eb:34:56:78"),
            ("dev-004", "rockpi-office-sensor", "rockpi", "dc:a6:32:90:12:34"),
            ("dev-005", "generic-arm-gateway-1", "generic_arm", "aa:bb:cc:dd:ee:01"),
            ("dev-006", "jetson-orin-edge-ai", "jetson_nano", "00:04:4b:ab:cd:ef"),
            ("dev-007", "raspberry-pi-4-kiosk", "raspberry_pi", "b8:27:eb:56:78:90"),
            ("dev-008", "rockpi-display-unit", "rockpi", "dc:a6:32:12:34:56"),
        ]
        for dev_id, name, dtype, hwid in demo_devices:
            device = EdgeDevice(dev_id, name, dtype, hwid)
            device.fingerprint = f"fp_{dev_id}_{uuid.uuid4().hex[:8]}"
            device.status = "online"
            device.firmware_version = "2.1.0"
            device.agent_version = "1.0.0"
            device.last_heartbeat = datetime.utcnow() - timedelta(seconds=hash(dev_id) % 300)
            device.resources = {
                "cpu_cores": 4 if "raspberry" in name else 6,
                "cpu_usage": round(10 + (hash(dev_id) % 60), 1),
                "memory_total_mb": 4096 if "raspberry" in name else 8192,
                "memory_used_mb": int(1024 + (hash(dev_id) % 2048)),
                "disk_total_gb": 32 if "raspberry" in name else 64,
                "disk_used_gb": int(8 + (hash(dev_id) % 16)),
                "temperature_celsius": round(45 + (hash(dev_id) % 20), 1),
                "uptime_seconds": int(86400 * (1 + hash(dev_id) % 30)),
            }
            device.tags = [dtype, "production"] if dev_id != "dev-008" else [dtype, "staging"]
            self.devices[dev_id] = device

    async def initialize(self):
        """Start background monitoring tasks."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("EdgeDeviceManager initialized with %d devices", len(self.devices))

    async def close(self):
        """Clean up background tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("EdgeDeviceManager closed")

    async def _heartbeat_monitor(self):
        """Check for devices that have stopped sending heartbeats."""
        while True:
            try:
                await asyncio.sleep(60)
                threshold = datetime.utcnow() - timedelta(minutes=5)
                for device in self.devices.values():
                    if device.last_heartbeat and device.last_heartbeat < threshold:
                        if device.status == "online":
                            device.status = "offline"
                            device.updated_at = datetime.utcnow()
                            logger.warning("Device %s went offline (no heartbeat)", device.device_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat monitor error: %s", e)

    async def _cleanup_loop(self):
        """Periodic cleanup of old commands and updates."""
        while True:
            try:
                await asyncio.sleep(3600)
                cutoff = datetime.utcnow() - timedelta(days=7)
                for dev_id in list(self.command_queue.keys()):
                    self.command_queue[dev_id] = [
                        cmd for cmd in self.command_queue[dev_id]
                        if cmd.created_at > cutoff
                    ]
                stale_updates = [
                    uid for uid, upd in self.firmware_updates.items()
                    if upd.status in ("completed", "failed")
                    and upd.completed_at
                    and upd.completed_at < cutoff
                ]
                for uid in stale_updates:
                    del self.firmware_updates[uid]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup error: %s", e)

    def register_device(self, name: str, device_type: str, hardware_id: str,
                        geolocation: Optional[dict] = None,
                        tags: Optional[list[str]] = None) -> EdgeDevice:
        device_id = f"dev-{uuid.uuid4().hex[:8]}"
        device = EdgeDevice(device_id, name, device_type, hardware_id)
        device.fingerprint = f"fp_{device_id}_{uuid.uuid4().hex[:8]}"
        if geolocation:
            device.geolocation = geolocation
        if tags:
            device.tags = tags
        self.devices[device_id] = device
        logger.info("Registered new device: %s (%s)", device_id, name)
        return device

    def get_device(self, device_id: str) -> Optional[EdgeDevice]:
        return self.devices.get(device_id)

    def list_devices(self, status: Optional[str] = None,
                     device_type: Optional[str] = None,
                     tag: Optional[str] = None) -> list[EdgeDevice]:
        if not any([status, device_type, tag]):
            return list(self.devices.values())
        result = []
        for d in self.devices.values():
            if status and d.status != status:
                continue
            if device_type and d.device_type != device_type:
                continue
            if tag and tag not in d.tags:
                continue
            result.append(d)
        return result

    def update_device(self, device_id: str, updates: dict[str, Any]) -> Optional[EdgeDevice]:
        device = self.devices.get(device_id)
        if not device:
            return None
        if "name" in updates:
            device.name = updates["name"]
        if "geolocation" in updates:
            device.geolocation.update(updates["geolocation"])
        if "tags" in updates:
            device.tags = updates["tags"]
        if "metadata" in updates:
            device.metadata.update(updates["metadata"])
        device.updated_at = datetime.utcnow()
        return device

    def delete_device(self, device_id: str) -> bool:
        if device_id in self.devices:
            del self.devices[device_id]
            for group in self.groups.values():
                if device_id in group.device_ids:
                    group.device_ids.remove(device_id)
            logger.info("Deleted device: %s", device_id)
            return True
        return False

    def process_heartbeat(self, device_id: str, resources: dict[str, Any]) -> bool:
        device = self.devices.get(device_id)
        if not device:
            return False
        device.last_heartbeat = datetime.utcnow()
        device.status = "online"
        device.resources.update(resources)
        device.updated_at = datetime.utcnow()
        return True

    def create_group(self, name: str, description: str = "") -> DeviceGroup:
        group_id = f"grp-{uuid.uuid4().hex[:8]}"
        group = DeviceGroup(group_id, name, description)
        self.groups[group_id] = group
        return group

    def add_device_to_group(self, group_id: str, device_id: str) -> bool:
        group = self.groups.get(group_id)
        if not group or device_id not in self.devices:
            return False
        if device_id not in group.device_ids:
            group.device_ids.append(device_id)
            group.updated_at = datetime.utcnow()
        return True

    def remove_device_from_group(self, group_id: str, device_id: str) -> bool:
        group = self.groups.get(group_id)
        if not group or device_id not in group.device_ids:
            return False
        group.device_ids.remove(device_id)
        group.updated_at = datetime.utcnow()
        return True

    def list_groups(self) -> list[DeviceGroup]:
        return list(self.groups.values())

    def queue_command(self, device_id: str, command: str,
                      timeout_seconds: int = 30) -> RemoteCommand:
        cmd = RemoteCommand(f"cmd-{uuid.uuid4().hex[:8]}", device_id, command)
        cmd.timeout_seconds = timeout_seconds
        self.command_queue[device_id].append(cmd)
        asyncio.create_task(self._execute_command(cmd))
        return cmd

    async def _execute_command(self, cmd: RemoteCommand):
        device = self.devices.get(cmd.device_id)
        if not device:
            cmd.status = "failed"
            cmd.stderr = "Device not found"
            return
        cmd.status = "running"
        cmd.executed_at = datetime.utcnow()
        try:
            await asyncio.sleep(0.5)
            cmd.status = "completed"
            cmd.exit_code = 0
            cmd.stdout = f"[simulated] Ran '{cmd.command}' on {device.name}"
            cmd.completed_at = datetime.utcnow()
        except Exception as e:
            cmd.status = "failed"
            cmd.stderr = str(e)
            cmd.exit_code = -1
            cmd.completed_at = datetime.utcnow()

    def get_device_commands(self, device_id: str,
                            limit: int = 20) -> list[RemoteCommand]:
        cmds = self.command_queue.get(device_id, [])
        return sorted(cmds, key=lambda c: c.created_at, reverse=True)[:limit]

    def schedule_firmware_update(self, device_id: str, target_version: str,
                                  artifact_url: str, checksum: str) -> FirmwareUpdate:
        update = FirmwareUpdate(
            f"fw-{uuid.uuid4().hex[:8]}", device_id, target_version
        )
        update.artifact_url = artifact_url
        update.checksum = checksum
        self.firmware_updates[update.update_id] = update
        asyncio.create_task(self._apply_firmware_update(update))
        return update

    async def _apply_firmware_update(self, update: FirmwareUpdate):
        device = self.devices.get(update.device_id)
        if not device:
            update.status = "failed"
            update.error_message = "Device not found"
            return
        update.status = "downloading"
        update.started_at = datetime.utcnow()
        try:
            await asyncio.sleep(2)
            update.progress_pct = 50.0
            await asyncio.sleep(2)
            update.progress_pct = 100.0
            update.status = "completed"
            device.firmware_version = update.target_version
            device.updated_at = datetime.utcnow()
            update.completed_at = datetime.utcnow()
        except Exception as e:
            update.status = "failed"
            update.error_message = str(e)
            update.completed_at = datetime.utcnow()

    def get_firmware_updates(self, device_id: Optional[str] = None) -> list[FirmwareUpdate]:
        updates = list(self.firmware_updates.values())
        if device_id:
            updates = [u for u in updates if u.device_id == device_id]
        return sorted(updates, key=lambda u: u.created_at, reverse=True)

    def get_devices_summary(self) -> dict[str, Any]:
        online = offline = degraded = provisioning = 0
        for d in self.devices.values():
            if d.status == "online":
                online += 1
            elif d.status == "offline":
                offline += 1
            elif d.status == "degraded":
                degraded += 1
            elif d.status == "provisioning":
                provisioning += 1
        pending = 0
        for u in self.firmware_updates.values():
            if u.status not in ("completed", "failed"):
                pending += 1
        return {
            "total": len(self.devices),
            "online": online,
            "offline": offline,
            "degraded": degraded,
            "provisioning": provisioning,
            "groups_count": len(self.groups),
            "pending_updates": pending,
        }


class EdgeDeviceManagerCog(commands.Cog):
    """Discord cog for edge device management."""

    def __init__(self, bot):
        self.bot = bot
        config = getattr(bot, "config", {})
        edge_config = getattr(config, "EDGE_CONFIG", {}) if hasattr(config, "EDGE_CONFIG") else {}
        self.manager = EdgeDeviceManager(edge_config)

    async def cog_load(self):
        await self.manager.initialize()
        logger.info("EdgeDeviceManagerCog loaded")

    async def cog_unload(self):
        await self.manager.close()

    @discord.app_commands.command(name="edge_list", description="List all edge devices")
    async def edge_list(self, interaction: discord.Interaction,
                        status: Optional[str] = None,
                        device_type: Optional[str] = None):
        devices = self.manager.list_devices(status=status, device_type=device_type)
        embed = discord.Embed(title="Edge Devices", color=discord.Color.blue())
        if not devices:
            embed.description = "No devices found."
            embed.color = discord.Color.orange()
        else:
            lines = []
            for d in devices[:25]:
                status_emoji = {"online": "🟢", "offline": "🔴", "degraded": "🟡", "provisioning": "🟣"}
                emoji = status_emoji.get(d.status, "⚪")
                lines.append(f"{emoji} **{d.name}** (`{d.device_id}`)")
                lines.append(f"   Type: {d.device_type} | CPU: {d.resources['cpu_usage']}% | "
                           f"Temp: {d.resources['temperature_celsius']}°C")
            embed.description = "\n".join(lines[:25])
        summary = self.manager.get_devices_summary()
        embed.set_footer(text=f"Total: {summary['total']} | "
                            f"Online: {summary['online']} | "
                            f"Offline: {summary['offline']}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_register", description="Register a new edge device")
    async def edge_register(self, interaction: discord.Interaction,
                            name: str, device_type: str, hardware_id: str):
        device = self.manager.register_device(name, device_type, hardware_id)
        embed = discord.Embed(
            title="Device Registered",
            description=f"Device **{device.name}** registered successfully.",
            color=discord.Color.green()
        )
        embed.add_field(name="Device ID", value=device.device_id, inline=True)
        embed.add_field(name="Type", value=device.device_type, inline=True)
        embed.add_field(name="Hardware ID", value=device.hardware_id, inline=True)
        embed.add_field(name="Fingerprint", value=device.fingerprint, inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_status", description="Get edge device status")
    async def edge_status(self, interaction: discord.Interaction, device_id: str):
        device = self.manager.get_device(device_id)
        if not device:
            await interaction.response.send_message("Device not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Device: {device.name}", color=discord.Color.blue())
        embed.add_field(name="ID", value=device.device_id, inline=True)
        embed.add_field(name="Type", value=device.device_type, inline=True)
        embed.add_field(name="Status", value=device.status, inline=True)
        embed.add_field(name="Firmware", value=device.firmware_version, inline=True)
        embed.add_field(name="Agent", value=device.agent_version, inline=True)
        res = device.resources
        embed.add_field(name="CPU Usage", value=f"{res['cpu_usage']}%", inline=True)
        embed.add_field(name="Memory", value=f"{res['memory_used_mb']}/{res['memory_total_mb']} MB", inline=True)
        embed.add_field(name="Disk", value=f"{res['disk_used_gb']}/{res['disk_total_gb']} GB", inline=True)
        embed.add_field(name="Temperature", value=f"{res['temperature_celsius']}°C", inline=True)
        embed.add_field(name="Uptime", value=f"{res['uptime_seconds'] // 86400}d", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_delete", description="Delete an edge device")
    @discord.app_commands.checks.has_permission(administrator=True)
    async def edge_delete(self, interaction: discord.Interaction, device_id: str):
        if self.manager.delete_device(device_id):
            await interaction.response.send_message(f"Device {device_id} deleted.")
        else:
            await interaction.response.send_message("Device not found.", ephemeral=True)

    @discord.app_commands.command(name="edge_command", description="Run command on edge device")
    async def edge_command(self, interaction: discord.Interaction, device_id: str, command: str):
        cmd = self.manager.queue_command(device_id, command)
        await interaction.response.send_message(
            f"Command queued: `{command}` on `{device_id}`\n"
            f"Command ID: `{cmd.command_id}`"
        )

    @discord.app_commands.command(name="edge_update_firmware", description="Trigger firmware update")
    async def edge_update_firmware(self, interaction: discord.Interaction,
                                    device_id: str, target_version: str):
        update = self.manager.schedule_firmware_update(
            device_id, target_version,
            f"https://firmware.infra-pilot.dev/{target_version}/image.img",
            f"sha256:{uuid.uuid4().hex}"
        )
        await interaction.response.send_message(
            f"Firmware update scheduled: `{device_id}` → v{target_version}"
        )


async def setup(bot):
    await bot.add_cog(EdgeDeviceManagerCog(bot))
