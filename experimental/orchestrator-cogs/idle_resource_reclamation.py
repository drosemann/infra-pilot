"""Idle Resource Reclamation Cog - Detect and clean up idle resources."""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    ZOMBIE_CONTAINER = "zombie_container"
    UNUSED_VOLUME = "unused_volume"
    ORPHANED_NETWORK = "orphaned_network"
    DANGLING_IMAGE = "dangling_image"
    UNUSED_SNAPSHOT = "unused_snapshot"
    STALE_CACHE = "stale_cache"
    ORPHANED_CONFIG = "orphaned_config"


class ReclamationMode(Enum):
    MANUAL = "manual"
    APPROVAL = "approval"
    AUTO_SAFE = "auto_safe"
    AUTO_AGGRESSIVE = "auto_aggressive"


class Resource:
    """Represents a potentially idle resource."""

    def __init__(self, resource_id: str, resource_type: ResourceType,
                 name: str, size_bytes: int = 0):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.name = name
        self.size_bytes = size_bytes
        self.age_days: float = 0.0
        self.status = "identified"
        self.container_id: Optional[str] = None
        self.server_id: Optional[str] = None
        self.metadata: dict[str, Any] = {}
        self.identified_at = datetime.utcnow()
        self.cleaned_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "age_days": self.age_days,
            "status": self.status,
            "container_id": self.container_id,
            "server_id": self.server_id,
            "identified_at": self.identified_at.isoformat(),
            "cleaned_at": self.cleaned_at.isoformat() if self.cleaned_at else None,
        }


class ReclamationReport:
    """Weekly reclamation savings report."""

    def __init__(self, report_id: str):
        self.report_id = report_id
        self.period_start = datetime.utcnow() - timedelta(days=7)
        self.period_end = datetime.utcnow()
        self.resources_identified: int = 0
        self.resources_cleaned: int = 0
        self.resources_pending: int = 0
        self.disk_space_recovered_bytes: int = 0
        self.cost_savings: float = 0.0
        self.breakdown: dict[str, dict[str, Any]] = {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "resources_identified": self.resources_identified,
            "resources_cleaned": self.resources_cleaned,
            "resources_pending": self.resources_pending,
            "disk_space_recovered_bytes": self.disk_space_recovered_bytes,
            "disk_space_recovered_gb": round(self.disk_space_recovered_bytes / (1024**3), 2),
            "cost_savings": round(self.cost_savings, 2),
            "breakdown": self.breakdown,
            "created_at": self.created_at.isoformat(),
        }


class IdleResourceReclamation:
    """Manager for detecting and reclaiming idle resources."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.resources: dict[str, Resource] = {}
        self.reports: dict[str, ReclamationReport] = {}
        self.mode = ReclamationMode.APPROVAL
        self._scan_task: Optional[asyncio.Task] = None
        self._report_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        demo_resources = [
            ("res-001", ResourceType.ZOMBIE_CONTAINER, "app-server-old", 250 * 1024 * 1024, 12),
            ("res-002", ResourceType.ZOMBIE_CONTAINER, "db-backup-test", 800 * 1024 * 1024, 5),
            ("res-003", ResourceType.UNUSED_VOLUME, "volume_minecraft_world", 45 * 1024 * 1024 * 1024, 60),
            ("res-004", ResourceType.UNUSED_VOLUME, "volume_build_cache", 12 * 1024 * 1024 * 1024, 30),
            ("res-005", ResourceType.DANGLING_IMAGE, "node:18-alpine-old", 180 * 1024 * 1024, 45),
            ("res-006", ResourceType.DANGLING_IMAGE, "python:3.9-slim-old", 120 * 1024 * 1024, 60),
            ("res-007", ResourceType.DANGLING_IMAGE, "ubuntu:22.04-base", 80 * 1024 * 1024, 90),
            ("res-008", ResourceType.ORPHANED_NETWORK, "net_bridge_test", 0, 20),
            ("res-009", ResourceType.STALE_CACHE, "pip-cache-volume", 2 * 1024 * 1024 * 1024, 35),
            ("res-010", ResourceType.ORPHANED_CONFIG, "config_nginx_old", 5 * 1024, 100),
        ]
        for rid, rtype, name, size, age in demo_resources:
            res = Resource(rid, rtype, name, size)
            res.age_days = age
            res.status = "identified"
            self.resources[rid] = res

    async def initialize(self):
        self._scan_task = asyncio.create_task(self._scan_loop())
        self._report_task = asyncio.create_task(self._report_loop())
        logger.info("IdleResourceReclamation initialized")

    async def close(self):
        if self._scan_task:
            self._scan_task.cancel()
        if self._report_task:
            self._report_task.cancel()
        logger.info("IdleResourceReclamation closed")

    async def _scan_loop(self):
        while True:
            try:
                await asyncio.sleep(3600)
                self._scan_for_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scan error: %s", e)

    def _scan_for_resources(self):
        new_count = 0
        for i in range(random.randint(1, 5)):
            rid = f"res-auto-{uuid.uuid4().hex[:8]}"
            rtype = random.choice(list(ResourceType))
            name = f"auto-detected-{rtype.value}-{i}"
            size = random.randint(1024, 10 * 1024 * 1024 * 1024)
            res = Resource(rid, rtype, name, size)
            res.age_days = random.uniform(1, 90)
            self.resources[rid] = res
            new_count += 1
        if new_count:
            logger.info("Discovered %d idle resources", new_count)

    async def _report_loop(self):
        while True:
            try:
                await asyncio.sleep(604800)
                self._generate_report()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Report error: %s", e)

    def _generate_report(self):
        report_id = f"rprt-{uuid.uuid4().hex[:8]}"
        report = ReclamationReport(report_id)
        identified = [r for r in self.resources.values() if r.status == "identified"]
        cleaned = [r for r in self.resources.values() if r.status == "cleaned"]
        pending = [r for r in self.resources.values() if r.status == "pending_approval"]

        report.resources_identified = len(identified)
        report.resources_cleaned = len(cleaned)
        report.resources_pending = len(pending)
        report.disk_space_recovered_bytes = sum(r.size_bytes for r in cleaned)
        report.cost_savings = report.disk_space_recovered_bytes / (1024**3) * 0.10

        for rtype in ResourceType:
            type_resources = [r for r in cleaned if r.resource_type == rtype]
            if type_resources:
                report.breakdown[rtype.value] = {
                    "count": len(type_resources),
                    "space_bytes": sum(r.size_bytes for r in type_resources),
                    "space_gb": round(sum(r.size_bytes for r in type_resources) / (1024**3), 2),
                }

        self.reports[report_id] = report
        logger.info("Generated reclamation report: %s", report_id)

    def scan_now(self) -> int:
        self._scan_for_resources()
        return len(self.resources)

    def list_resources(self, resource_type: Optional[str] = None,
                        status: Optional[str] = None) -> list[Resource]:
        result = list(self.resources.values())
        if resource_type:
            result = [r for r in result if r.resource_type.value == resource_type]
        if status:
            result = [r for r in result if r.status == status]
        return sorted(result, key=lambda r: r.age_days, reverse=True)

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        return self.resources.get(resource_id)

    def approve_cleanup(self, resource_id: str) -> bool:
        res = self.resources.get(resource_id)
        if not res or res.status != "pending_approval":
            return False
        res.status = "cleaned"
        res.cleaned_at = datetime.utcnow()
        logger.info("Approved cleanup of %s (%s)", resource_id, res.name)
        return True

    def reject_cleanup(self, resource_id: str) -> bool:
        res = self.resources.get(resource_id)
        if not res:
            return False
        res.status = "rejected"
        return True

    def auto_cleanup_safe(self) -> int:
        count = 0
        for res in self.resources.values():
            if res.status == "identified":
                if self._is_safe_to_remove(res):
                    res.status = "cleaned"
                    res.cleaned_at = datetime.utcnow()
                    count += 1
                else:
                    res.status = "pending_approval"
        return count

    def _is_safe_to_remove(self, res: Resource) -> bool:
        if res.resource_type in (ResourceType.ORPHANED_NETWORK, ResourceType.STALE_CACHE):
            return res.age_days > 30
        if res.resource_type == ResourceType.ZOMBIE_CONTAINER:
            return res.age_days > 7
        return False

    def get_stats(self) -> dict[str, Any]:
        total = len(self.resources)
        cleaned = sum(1 for r in self.resources.values() if r.status == "cleaned")
        pending = sum(1 for r in self.resources.values() if r.status == "pending_approval")
        total_recovered = sum(r.size_bytes for r in self.resources.values() if r.status == "cleaned")
        return {
            "total_resources": total,
            "cleaned": cleaned,
            "pending_approval": pending,
            "identified": total - cleaned - pending,
            "disk_recovered_gb": round(total_recovered / (1024**3), 2),
            "estimated_savings": round(total_recovered / (1024**3) * 0.10, 2),
            "scan_mode": self.mode.value,
        }

    def get_latest_report(self) -> Optional[ReclamationReport]:
        reports = sorted(self.reports.values(), key=lambda r: r.created_at, reverse=True)
        return reports[0] if reports else None


class IdleResourceReclamationCog(commands.Cog):
    """Discord cog for idle resource reclamation."""

    def __init__(self, bot):
        self.bot = bot
        self.reclamation = IdleResourceReclamation({})

    async def cog_load(self):
        await self.reclamation.initialize()

    async def cog_unload(self):
        await self.reclamation.close()

    @discord.app_commands.command(name="reclaim_scan", description="Scan for idle resources")
    async def reclaim_scan(self, interaction: discord.Interaction):
        count = self.reclamation.scan_now()
        embed = discord.Embed(title="Resource Scan Complete",
                            description=f"Discovered {count} total resources",
                            color=discord.Color.blue())
        stats = self.reclamation.get_stats()
        embed.add_field(name="Identified", value=str(stats["identified"]), inline=True)
        embed.add_field(name="Pending Approval", value=str(stats["pending_approval"]), inline=True)
        embed.add_field(name="Cleaned", value=str(stats["cleaned"]), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="reclaim_list", description="List idle resources")
    async def reclaim_list(self, interaction: discord.Interaction,
                           resource_type: Optional[str] = None):
        resources = self.reclamation.list_resources(resource_type=resource_type)
        embed = discord.Embed(title="Idle Resources", color=discord.Color.orange())
        if not resources:
            embed.description = "No idle resources found."
        else:
            lines = []
            for r in resources[:25]:
                status_emoji = {"identified": "🔍", "pending_approval": "⏳",
                                "cleaned": "✅", "rejected": "❌"}
                emoji = status_emoji.get(r.status, "⚪")
                size_gb = r.size_bytes / (1024**3)
                lines.append(f"{emoji} **{r.name}** (`{r.resource_id}`)")
                lines.append(f"   Type: {r.resource_type.value} | Size: {size_gb:.2f} GB | "
                           f"Age: {r.age_days:.0f}d")
            embed.description = "\n".join(lines[:25])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="reclaim_approve", description="Approve resource cleanup")
    async def reclaim_approve(self, interaction: discord.Interaction, resource_id: str):
        if self.reclamation.approve_cleanup(resource_id):
            await interaction.response.send_message(f"Cleanup approved for {resource_id}")
        else:
            await interaction.response.send_message("Resource not found or not pending approval.", ephemeral=True)

    @discord.app_commands.command(name="reclaim_auto", description="Run auto-cleanup")
    async def reclaim_auto(self, interaction: discord.Interaction):
        count = self.reclamation.auto_cleanup_safe()
        await interaction.response.send_message(f"Auto-cleaned {count} safe resources")

    @discord.app_commands.command(name="reclaim_report", description="Get reclamation report")
    async def reclaim_report(self, interaction: discord.Interaction):
        report = self.reclamation.get_latest_report()
        embed = discord.Embed(title="Weekly Reclamation Report",
                            color=discord.Color.blue())
        if report:
            d = report.to_dict()
            embed.add_field(name="Period", value=f"{d['period_start'][:10]} to {d['period_end'][:10]}", inline=False)
            embed.add_field(name="Identified", value=d["resources_identified"], inline=True)
            embed.add_field(name="Cleaned", value=d["resources_cleaned"], inline=True)
            embed.add_field(name="Space Recovered", value=f"{d['disk_space_recovered_gb']} GB", inline=True)
            embed.add_field(name="Cost Savings", value=f"${d['cost_savings']}", inline=True)
            if d["breakdown"]:
                for rtype, data in d["breakdown"].items():
                    embed.add_field(name=rtype, value=f"{data['count']} items, {data['space_gb']} GB", inline=True)
        else:
            embed.description = "No reports available yet."
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="reclaim_stats", description="Get reclamation statistics")
    async def reclaim_stats(self, interaction: discord.Interaction):
        stats = self.reclamation.get_stats()
        embed = discord.Embed(title="Reclamation Statistics", color=discord.Color.blue())
        for k, v in stats.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(IdleResourceReclamationCog(bot))
