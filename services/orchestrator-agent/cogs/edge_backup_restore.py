"""Edge Backup & Restore Cog - Periodic backup of edge device state."""

import asyncio
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class BackupType(Enum):
    FULL = "full"
    SYSTEM_CONFIG = "system_config"
    APP_DATA = "app_data"
    ML_MODELS = "ml_models"
    CERTIFICATES = "certificates"


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"


class RestoreStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class BackupArtifact:
    """A single file in a backup set."""

    def __init__(self, name: str, data: bytes, encrypted: bool = False):
        self.name = name
        self.data = data
        self.encrypted = encrypted
        self.checksum = hashlib.sha256(data).hexdigest()
        self.size_bytes = len(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "encrypted": self.encrypted,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
        }


class BackupManifest:
    """Manifest describing a backup's contents."""

    def __init__(self, backup_id: str, device_id: str, backup_type: BackupType):
        self.backup_id = backup_id
        self.device_id = device_id
        self.backup_type = backup_type
        self.timestamp = datetime.utcnow()
        self.device_fingerprint: str = ""
        self.software_version: str = ""
        self.artifacts: list[BackupArtifact] = []
        self.checksums: dict[str, str] = {}
        self.total_size_bytes: int = 0
        self.encryption_algorithm: str = "AES-256-GCM"

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "device_id": self.device_id,
            "backup_type": self.backup_type.value,
            "timestamp": self.timestamp.isoformat(),
            "device_fingerprint": self.device_fingerprint,
            "software_version": self.software_version,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "checksums": self.checksums,
            "total_size_bytes": self.total_size_bytes,
            "encryption_algorithm": self.encryption_algorithm,
        }


class BackupJob:
    """A backup job tracking state."""

    def __init__(self, backup_id: str, device_id: str, backup_type: BackupType):
        self.backup_id = backup_id
        self.device_id = device_id
        self.backup_type = backup_type
        self.status = BackupStatus.PENDING
        self.manifest: Optional[BackupManifest] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress_pct: float = 0.0
        self.error_message: Optional[str] = None
        self.cloud_synced: bool = False
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "device_id": self.device_id,
            "backup_type": self.backup_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_pct": self.progress_pct,
            "error_message": self.error_message,
            "cloud_synced": self.cloud_synced,
            "created_at": self.created_at.isoformat(),
        }


class RestoreJob:
    """A restore job tracking state."""

    def __init__(self, restore_id: str, backup_id: str, device_id: str, target_device_id: str):
        self.restore_id = restore_id
        self.backup_id = backup_id
        self.device_id = device_id
        self.target_device_id = target_device_id
        self.status = RestoreStatus.PENDING
        self.dry_run: bool = False
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress_pct: float = 0.0
        self.error_message: Optional[str] = None
        self.restored_artifacts: int = 0
        self.total_artifacts: int = 0
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "restore_id": self.restore_id,
            "backup_id": self.backup_id,
            "device_id": self.device_id,
            "target_device_id": self.target_device_id,
            "status": self.status.value,
            "dry_run": self.dry_run,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_pct": self.progress_pct,
            "error_message": self.error_message,
            "restored_artifacts": self.restored_artifacts,
            "total_artifacts": self.total_artifacts,
            "created_at": self.created_at.isoformat(),
        }


class RetentionPolicy:
    """Backup retention configuration."""

    def __init__(self, name: str):
        self.name = name
        self.full_backup_retention_days: int = 90
        self.daily_retention_days: int = 30
        self.weekly_retention_weeks: int = 12
        self.monthly_retention_months: int = 12
        self.min_backups_to_keep: int = 5
        self.auto_cleanup_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "full_backup_retention_days": self.full_backup_retention_days,
            "daily_retention_days": self.daily_retention_days,
            "weekly_retention_weeks": self.weekly_retention_weeks,
            "monthly_retention_months": self.monthly_retention_months,
            "min_backups_to_keep": self.min_backups_to_keep,
            "auto_cleanup_enabled": self.auto_cleanup_enabled,
        }


class EdgeBackupRestore:
    """Manager for edge device backup and restore operations."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.backup_jobs: dict[str, BackupJob] = {}
        self.restore_jobs: dict[str, RestoreJob] = {}
        self.backup_storage: dict[str, list[BackupManifest]] = {}
        self.retention_policies: dict[str, RetentionPolicy] = {}
        self._backup_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        self.retention_policies["default"] = RetentionPolicy("default")
        self.retention_policies["strict"] = RetentionPolicy("strict")
        self.retention_policies["strict"].full_backup_retention_days = 365
        self.retention_policies["strict"].monthly_retention_months = 24

        demo_backups = [
            ("dev-001", BackupType.FULL),
            ("dev-001", BackupType.SYSTEM_CONFIG),
            ("dev-002", BackupType.FULL),
            ("dev-002", BackupType.ML_MODELS),
            ("dev-003", BackupType.APP_DATA),
            ("dev-004", BackupType.FULL),
            ("dev-005", BackupType.FULL),
        ]
        for device_id, btype in demo_backups:
            bid = f"bkp-{uuid.uuid4().hex[:8]}"
            job = BackupJob(bid, device_id, btype)
            job.status = BackupStatus.COMPLETED
            job.started_at = datetime.utcnow() - timedelta(hours=hash(bid) % 72)
            job.completed_at = job.started_at + timedelta(minutes=hash(bid) % 30)
            job.progress_pct = 100.0
            manifest = BackupManifest(bid, device_id, btype)
            manifest.device_fingerprint = f"fp_{device_id}"
            manifest.software_version = "1.0.0"
            for i in range(3):
                data = f"backup_data_{bid}_{i}".encode() * 1000
                art = BackupArtifact(f"artifact_{i}.tar.gz" + (".enc" if i > 0 else ""), data)
                manifest.artifacts.append(art)
                manifest.checksums[art.name] = art.checksum
                manifest.total_size_bytes += art.size_bytes
            job.manifest = manifest
            self.backup_jobs[bid] = job
            if device_id not in self.backup_storage:
                self.backup_storage[device_id] = []
            self.backup_storage[device_id].append(manifest)

    async def initialize(self):
        self._backup_task = asyncio.create_task(self._scheduled_backup_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("EdgeBackupRestore initialized")

    async def close(self):
        if self._backup_task:
            self._backup_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("EdgeBackupRestore closed")

    async def _scheduled_backup_loop(self):
        while True:
            try:
                await asyncio.sleep(3600)
                for device_id in set(j.device_id for j in self.backup_jobs.values()
                                     if j.status == BackupStatus.COMPLETED):
                    pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduled backup error: %s", e)

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(86400)
                self._apply_retention_policy()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup error: %s", e)

    def _apply_retention_policy(self):
        policy = self.retention_policies.get("default")
        if not policy or not policy.auto_cleanup_enabled:
            return
        cutoff = datetime.utcnow() - timedelta(days=policy.full_backup_retention_days)
        for device_id in list(self.backup_storage.keys()):
            manifests = self.backup_storage[device_id]
            filtered = [m for m in manifests if m.timestamp > cutoff]
            if len(filtered) < policy.min_backups_to_keep:
                filtered = manifests[-policy.min_backups_to_keep:]
            self.backup_storage[device_id] = filtered
            removed = len(manifests) - len(filtered)
            if removed > 0:
                logger.info("Cleaned %d old backups for %s", removed, device_id)

    def create_backup(self, device_id: str, backup_type: BackupType = BackupType.FULL) -> BackupJob:
        backup_id = f"bkp-{uuid.uuid4().hex[:8]}"
        job = BackupJob(backup_id, device_id, backup_type)
        self.backup_jobs[backup_id] = job
        asyncio.create_task(self._execute_backup(job))
        return job

    async def _execute_backup(self, job: BackupJob):
        job.status = BackupStatus.RUNNING
        job.started_at = datetime.utcnow()
        manifest = BackupManifest(job.backup_id, job.device_id, job.backup_type)
        try:
            await asyncio.sleep(1)
            job.progress_pct = 25.0
            data = f"config_data_{job.backup_id}".encode() * 5000
            manifest.artifacts.append(BackupArtifact("config.tar.gz.enc", data))
            manifest.checksums["config.tar.gz.enc"] = hashlib.sha256(data).hexdigest()
            await asyncio.sleep(1)
            job.progress_pct = 50.0
            data = f"app_data_{job.backup_id}".encode() * 5000
            manifest.artifacts.append(BackupArtifact("data.tar.gz.enc", data))
            manifest.checksums["data.tar.gz.enc"] = hashlib.sha256(data).hexdigest()
            await asyncio.sleep(1)
            job.progress_pct = 75.0
            if job.backup_type in (BackupType.FULL, BackupType.ML_MODELS):
                data = f"model_data_{job.backup_id}".encode() * 5000
                manifest.artifacts.append(BackupArtifact("models.tar.gz.enc", data))
                manifest.checksums["models.tar.gz.enc"] = hashlib.sha256(data).hexdigest()
            manifest.total_size_bytes = sum(a.size_bytes for a in manifest.artifacts)
            manifest.device_fingerprint = f"fp_{job.device_id}"
            manifest.software_version = "1.0.0"
            job.manifest = manifest
            job.status = BackupStatus.COMPLETED
            job.progress_pct = 100.0
            job.completed_at = datetime.utcnow()
            if job.device_id not in self.backup_storage:
                self.backup_storage[job.device_id] = []
            self.backup_storage[job.device_id].append(manifest)
            logger.info("Backup %s completed: %d bytes", job.backup_id, manifest.total_size_bytes)
        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error("Backup %s failed: %s", job.backup_id, e)

    def get_backup_job(self, backup_id: str) -> Optional[BackupJob]:
        return self.backup_jobs.get(backup_id)

    def list_backups(self, device_id: Optional[str] = None,
                     backup_type: Optional[str] = None) -> list[BackupJob]:
        result = list(self.backup_jobs.values())
        if device_id:
            result = [j for j in result if j.device_id == device_id]
        if backup_type:
            result = [j for j in result if j.backup_type.value == backup_type]
        return sorted(result, key=lambda j: j.created_at, reverse=True)

    def get_backup_manifests(self, device_id: str) -> list[BackupManifest]:
        return self.backup_storage.get(device_id, [])

    def restore_backup(self, backup_id: str, target_device_id: Optional[str] = None,
                       dry_run: bool = False) -> Optional[RestoreJob]:
        job = self.backup_jobs.get(backup_id)
        if not job or job.status != BackupStatus.COMPLETED or not job.manifest:
            return None
        target = target_device_id or job.device_id
        restore_id = f"rst-{uuid.uuid4().hex[:8]}"
        restore = RestoreJob(restore_id, backup_id, job.device_id, target)
        restore.dry_run = dry_run
        self.restore_jobs[restore_id] = restore
        asyncio.create_task(self._execute_restore(restore, job.manifest))
        return restore

    async def _execute_restore(self, restore: RestoreJob, manifest: BackupManifest):
        restore.status = RestoreStatus.VERIFYING
        restore.started_at = datetime.utcnow()
        try:
            await asyncio.sleep(1)
            restore.progress_pct = 30.0
            for name, checksum in manifest.checksums.items():
                expected = hashlib.sha256(f"verified_{name}".encode()).hexdigest()[:16]
            restore.status = RestoreStatus.APPLYING
            await asyncio.sleep(1)
            restore.progress_pct = 70.0
            restore.total_artifacts = len(manifest.artifacts)
            restore.restored_artifacts = len(manifest.artifacts)
            await asyncio.sleep(1)
            restore.progress_pct = 100.0
            restore.status = RestoreStatus.COMPLETED
            restore.completed_at = datetime.utcnow()
            logger.info("Restore %s completed to %s", restore.restore_id, restore.target_device_id)
        except Exception as e:
            restore.status = RestoreStatus.FAILED
            restore.error_message = str(e)
            restore.completed_at = datetime.utcnow()

    def get_restore_job(self, restore_id: str) -> Optional[RestoreJob]:
        return self.restore_jobs.get(restore_id)

    def list_restores(self, device_id: Optional[str] = None) -> list[RestoreJob]:
        result = list(self.restore_jobs.values())
        if device_id:
            result = [r for r in result if r.device_id == device_id or r.target_device_id == device_id]
        return sorted(result, key=lambda r: r.created_at, reverse=True)

    def get_device_backup_summary(self, device_id: str) -> dict[str, Any]:
        backups = [j for j in self.backup_jobs.values() if j.device_id == device_id]
        completed = [b for b in backups if b.status == BackupStatus.COMPLETED]
        total_size = sum(b.manifest.total_size_bytes for b in completed if b.manifest)
        return {
            "device_id": device_id,
            "total_backups": len(backups),
            "completed": len(completed),
            "failed": sum(1 for b in backups if b.status == BackupStatus.FAILED),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "last_backup": completed[0].completed_at.isoformat() if completed else None,
        }


class EdgeBackupRestoreCog(commands.Cog):
    """Discord cog for edge backup and restore."""

    def __init__(self, bot):
        self.bot = bot
        self.backup_mgr = EdgeBackupRestore({})

    async def cog_load(self):
        await self.backup_mgr.initialize()

    async def cog_unload(self):
        await self.backup_mgr.close()

    @discord.app_commands.command(name="edge_backup", description="Create edge device backup")
    async def edge_backup(self, interaction: discord.Interaction,
                          device_id: str, backup_type: Optional[str] = None):
        btype = BackupType(backup_type) if backup_type else BackupType.FULL
        job = self.backup_mgr.create_backup(device_id, btype)
        embed = discord.Embed(title="Backup Started", color=discord.Color.blue())
        embed.add_field(name="Backup ID", value=job.backup_id, inline=True)
        embed.add_field(name="Device", value=device_id, inline=True)
        embed.add_field(name="Type", value=btype.value, inline=True)
        embed.add_field(name="Status", value=job.status.value, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_backups", description="List edge backups")
    async def edge_backups(self, interaction: discord.Interaction,
                           device_id: Optional[str] = None):
        backups = self.backup_mgr.list_backups(device_id=device_id)
        embed = discord.Embed(title="Edge Backups", color=discord.Color.blue())
        if not backups:
            embed.description = "No backups found."
        else:
            lines = []
            for b in backups[:20]:
                status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}
                emoji = status_emoji.get(b.status.value, "⚪")
                size = f"{b.manifest.total_size_bytes / 1024 / 1024:.1f}MB" if b.manifest else "N/A"
                lines.append(f"{emoji} **{b.backup_id}** - {b.device_id}")
                lines.append(f"   Type: {b.backup_type.value} | Size: {size} | "
                           f"{b.completed_at.strftime('%Y-%m-%d %H:%M') if b.completed_at else 'N/A'}")
            embed.description = "\n".join(lines[:20])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_restore", description="Restore edge device from backup")
    async def edge_restore(self, interaction: discord.Interaction,
                           backup_id: str, target_device_id: Optional[str] = None,
                           dry_run: bool = False):
        restore = self.backup_mgr.restore_backup(backup_id, target_device_id, dry_run)
        if not restore:
            await interaction.response.send_message("Backup not found or incomplete.", ephemeral=True)
            return
        embed = discord.Embed(title="Restore Started", color=discord.Color.blue())
        embed.add_field(name="Restore ID", value=restore.restore_id, inline=True)
        embed.add_field(name="Backup ID", value=backup_id, inline=True)
        embed.add_field(name="Target", value=restore.target_device_id, inline=True)
        embed.add_field(name="Dry Run", value=str(restore.dry_run), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="edge_backup_summary", description="Get backup summary")
    async def edge_backup_summary(self, interaction: discord.Interaction, device_id: str):
        summary = self.backup_mgr.get_device_backup_summary(device_id)
        embed = discord.Embed(title=f"Backup Summary: {device_id}", color=discord.Color.blue())
        for k, v in summary.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EdgeBackupRestoreCog(bot))
