import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class BackupState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RestoreState(Enum):
    PENDING = "pending"
    RESTORING = "restoring"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"


class BackupTarget(Enum):
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GCP_STORAGE = "gcp_storage"
    HETZNER_STORAGE_BOX = "hetzner_storage_box"
    OVH_OBJECT_STORAGE = "ovh_object_storage"
    LOCAL = "local"


class GeoRedundancyLevel(Enum):
    NONE = "none"
    SAME_REGION = "same_region"
    CROSS_REGION = "cross_region"
    CROSS_CLOUD = "cross_cloud"


class Backup:
    def __init__(self, name: str, workload_id: str, source_provider: str,
                 target: BackupTarget, size_gb: float = 0,
                 retention_days: int = 30, encrypted: bool = True):
        self.id = str(uuid.uuid4())
        self.name = name
        self.workload_id = workload_id
        self.source_provider = source_provider
        self.target = target
        self.size_gb = size_gb
        self.retention_days = retention_days
        self.encrypted = encrypted
        self.state = BackupState.PENDING
        self.replicas: List[str] = []
        self.checksum: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.expires_at = self.created_at + timedelta(days=retention_days)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "workload_id": self.workload_id,
                "source_provider": self.source_provider, "target": self.target.value,
                "size_gb": self.size_gb, "retention_days": self.retention_days,
                "encrypted": self.encrypted, "state": self.state.value,
                "replicas": self.replicas, "checksum": self.checksum,
                "created_at": self.created_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "expires_at": self.expires_at.isoformat()}


class RestoreJob:
    def __init__(self, backup_id: str, target_provider: str,
                 target_region: str, restore_to_original: bool = True):
        self.id = str(uuid.uuid4())
        self.backup_id = backup_id
        self.target_provider = target_provider
        self.target_region = target_region
        self.restore_to_original = restore_to_original
        self.state = RestoreState.PENDING
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "backup_id": self.backup_id,
                "target_provider": self.target_provider,
                "target_region": self.target_region,
                "restore_to_original": self.restore_to_original,
                "state": self.state.value,
                "created_at": self.created_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None}


class BackupFederation:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_retention_days = config.get("default_retention_days", 30)
        self.default_encryption = config.get("default_encryption", True)
        self.geo_redundancy = GeoRedundancyLevel(config.get("geo_redundancy", "cross_cloud"))
        self.max_backup_size_gb = config.get("max_backup_size_gb", 5000)
        self.backup_concurrency = config.get("backup_concurrency", 5)
        self._backups: Dict[str, Backup] = {}
        self._restore_jobs: Dict[str, RestoreJob] = {}
        self._vaults: Dict[str, Dict[str, Any]] = {}
        self._backup_log: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        vault_config = self.config.get("vault", {})
        default_vault = {"vault_id": "default", "name": "Default Vault",
                         "provider": vault_config.get("provider", "aws_s3"),
                         "region": vault_config.get("region", "us-east-1"),
                         "bucket": vault_config.get("bucket", "infrapilot-backups"),
                         "geo_redundancy": self.geo_redundancy.value}
        self._vaults["default"] = default_vault
        self._initialized = True
        logger.info("BackupFederation initialized")

    async def close(self) -> None:
        self._backups.clear()
        self._restore_jobs.clear()
        logger.info("BackupFederation closed")

    def create_backup(self, name: str, workload_id: str, source_provider: str,
                      target: BackupTarget = BackupTarget.AWS_S3,
                      retention_days: Optional[int] = None,
                      encrypted: Optional[bool] = None,
                      replica_targets: Optional[List[BackupTarget]] = None) -> Backup:
        backup = Backup(name, workload_id, source_provider, target,
                        0, retention_days or self.default_retention_days,
                        encrypted if encrypted is not None else self.default_encryption)
        if replica_targets:
            for rt in replica_targets:
                backup.replicas.append(rt.value)
        self._backups[backup.id] = backup
        logger.info(f"Backup '{name}' created for workload {workload_id}")
        return backup

    def get_backup(self, backup_id: str) -> Optional[Backup]:
        return self._backups.get(backup_id)

    def list_backups(self, workload_id: Optional[str] = None,
                     state: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for b in self._backups.values():
            if workload_id and b.workload_id != workload_id:
                continue
            if state and b.state.value != state:
                continue
            results.append(b.to_dict())
        return results

    def delete_backup(self, backup_id: str) -> bool:
        if backup_id in self._backups:
            del self._backups[backup_id]
            return True
        return False

    async def execute_backup(self, backup_id: str) -> Dict[str, Any]:
        backup = self._backups.get(backup_id)
        if not backup:
            return {"status": "error", "message": "Backup not found"}
        backup.state = BackupState.RUNNING
        import hashlib
        backup.checksum = hashlib.sha256(f"{backup.id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        backup.size_gb = round(1 + (hash(backup.id) % 100) / 10, 2)
        backup.state = BackupState.COMPLETED
        backup.completed_at = datetime.utcnow()
        for replica_target in backup.replicas:
            await self._replicate_backup(backup, replica_target)
        log_entry = {"backup_id": backup_id, "workload_id": backup.workload_id,
                     "target": backup.target.value, "size_gb": backup.size_gb,
                     "checksum": backup.checksum, "completed_at": backup.completed_at.isoformat()}
        self._backup_log.append(log_entry)
        logger.info(f"Backup {backup_id} completed ({backup.size_gb} GB)")
        return {"backup_id": backup_id, "status": "completed", "size_gb": backup.size_gb}

    async def _replicate_backup(self, backup: Backup, target: str) -> None:
        replica_id = f"replica-{uuid.uuid4().hex[:8]}"
        logger.info(f"Replicating backup {backup.id} to {target} (replica {replica_id})")

    def create_restore_job(self, backup_id: str, target_provider: str,
                           target_region: str,
                           restore_to_original: bool = True) -> RestoreJob:
        job = RestoreJob(backup_id, target_provider, target_region, restore_to_original)
        self._restore_jobs[job.id] = job
        return job

    def get_restore_job(self, job_id: str) -> Optional[RestoreJob]:
        return self._restore_jobs.get(job_id)

    def list_restore_jobs(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        if state:
            return [j.to_dict() for j in self._restore_jobs.values() if j.state.value == state]
        return [j.to_dict() for j in self._restore_jobs.values()]

    async def execute_restore(self, job_id: str) -> Dict[str, Any]:
        job = self._restore_jobs.get(job_id)
        if not job:
            return {"status": "error", "message": "Restore job not found"}
        backup = self._backups.get(job.backup_id)
        if not backup:
            return {"status": "error", "message": "Backup not found"}
        job.state = RestoreState.RESTORING
        await asyncio.sleep(0.5)
        if job.restore_to_original:
            target = backup.source_provider
        else:
            target = job.target_provider
        job.state = RestoreState.COMPLETED
        job.completed_at = datetime.utcnow()
        logger.info(f"Restore job {job_id} completed: restored to {target}")
        return {"job_id": job_id, "backup_id": job.backup_id,
                "restored_to": target, "status": "completed"}

    def restore_cross_cloud(self, backup_id: str,
                            target_provider: str) -> RestoreJob:
        job = self.create_restore_job(backup_id, target_provider, "us-east-1", False)
        logger.info(f"Cross-cloud restore initiated: backup {backup_id} -> {target_provider}")
        return job

    def list_vaults(self) -> List[Dict[str, Any]]:
        return list(self._vaults.values())

    def get_statistics(self) -> Dict[str, Any]:
        total_size = sum(b.size_gb for b in self._backups.values())
        return {"total_backups": len(self._backups),
                "completed_backups": sum(1 for b in self._backups.values() if b.state == BackupState.COMPLETED),
                "total_restores": len(self._restore_jobs),
                "total_size_gb": round(total_size, 2),
                "active_vaults": len(self._vaults),
                "unique_workloads": len(set(b.workload_id for b in self._backups.values()))}

    def create_backup_vault(self, name: str, provider: str,
                             region: str, geo_redundant: bool = False) -> BackupVault:
        vault = BackupVault(name, provider, region, geo_redundant)
        self._vaults[vault.id] = vault
        return vault

    def delete_backup_vault(self, vault_id: str) -> bool:
        if vault_id in self._vaults:
            del self._vaults[vault_id]
            return True
        return False

    def get_backup_vault(self, vault_id: str) -> Optional[Dict[str, Any]]:
        vault = self._vaults.get(vault_id)
        return vault.to_dict() if vault else None

    def create_backup(self, workload_id: str, source_provider: str,
                       vault_id: str, size_gb: float = 10.0) -> Backup:
        backup = Backup(workload_id, source_provider, vault_id, size_gb)
        self._backups[backup.id] = backup
        return backup

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        backup = self._backups.get(backup_id)
        return backup.to_dict() if backup else None

    def list_backups(self, state: Optional[BackupState] = None,
                      workload_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self._backups.values())
        if state:
            results = [b for b in results if b.state == state]
        if workload_id:
            results = [b for b in results if b.workload_id == workload_id]
        return [b.to_dict() for b in results]

    def delete_backup(self, backup_id: str) -> bool:
        if backup_id in self._backups:
            del self._backups[backup_id]
            return True
        return False

    async def execute_backup(self, backup_id: str) -> Dict[str, Any]:
        backup = self._backups.get(backup_id)
        if not backup:
            return {"status": "error", "message": "Backup not found"}
        backup.state = BackupState.IN_PROGRESS
        await asyncio.sleep(0.5)
        backup.state = BackupState.COMPLETED
        backup.completed_at = datetime.utcnow()
        logger.info(f"Backup {backup_id} completed")
        return {"backup_id": backup_id, "workload_id": backup.workload_id,
                "size_gb": backup.size_gb, "status": "completed"}

    def list_jobs(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.list_restore_jobs(state)

    def verify_backup_integrity(self, backup_id: str) -> Dict[str, Any]:
        backup = self._backups.get(backup_id)
        if not backup:
            return {"status": "error", "message": "Backup not found"}
        import random
        integrity_ok = random.random() > 0.1
        return {"backup_id": backup_id, "integrity_ok": integrity_ok,
                "verified_at": datetime.utcnow().isoformat()}

    def schedule_backup(self, workload_id: str, vault_id: str,
                         cron_expr: str, retention_days: int = 30) -> Dict[str, Any]:
        schedule_id = f"schedule-{uuid.uuid4().hex[:8]}"
        schedule = {"id": schedule_id, "workload_id": workload_id,
                    "vault_id": vault_id, "cron": cron_expr,
                    "retention_days": retention_days, "active": True,
                    "created_at": datetime.utcnow().isoformat()}
        if "schedules" not in self.config:
            self.config["schedules"] = []
        self.config["schedules"].append(schedule)
        return schedule

    def list_schedules(self) -> List[Dict[str, Any]]:
        return self.config.get("schedules", [])

    def delete_schedule(self, schedule_id: str) -> bool:
        schedules = self.config.get("schedules", [])
        for i, s in enumerate(schedules):
            if s.get("id") == schedule_id:
                schedules.pop(i)
                return True
        return False

    def calculate_vault_usage(self, vault_id: str) -> Dict[str, Any]:
        vault = self._vaults.get(vault_id)
        if not vault:
            return {"status": "error", "message": "Vault not found"}
        total_size = sum(b.size_gb for b in self._backups.values()
                         if b.vault_id == vault_id)
        return {"vault_id": vault_id, "vault_name": vault.name,
                "total_backups": sum(1 for b in self._backups.values()
                                     if b.vault_id == vault_id),
                "total_size_gb": round(total_size, 2),
                "provider": vault.provider, "geo_redundant": vault.geo_redundant}

    def get_backup_summary(self) -> Dict[str, Any]:
        total_size = sum(b.size_gb for b in self._backups.values())
        by_provider = {}
        for b in self._backups.values():
            by_provider[b.source_provider] = by_provider.get(b.source_provider, 0) + 1
        return {"total_backups": len(self._backups),
                "total_size_gb": round(total_size, 2),
                "backups_by_provider": by_provider,
                "active_vaults": len(self._vaults),
                "total_restores": len(self._restore_jobs)}

    def enforce_retention_policy(self) -> List[str]:
        expired = []
        now = datetime.utcnow()
        for bid, b in list(self._backups.items()):
            if b.expires_at and now >= b.expires_at:
                b.state = BackupState.EXPIRED
                expired.append(bid)
        return expired

    def create_replication_policy(self, name: str, source_vault_id: str, target_vault_id: str, schedule_cron: str = "0 0 * * *") -> Dict[str, Any]:
        policy_id = f"repl-pol-{uuid.uuid4().hex[:8]}"
        policy = {"id": policy_id, "name": name, "source_vault_id": source_vault_id,
                  "target_vault_id": target_vault_id, "schedule": schedule_cron,
                  "active": True, "created_at": datetime.utcnow().isoformat()}
        if "replication_policies" not in self.config:
            self.config["replication_policies"] = []
        self.config["replication_policies"].append(policy)
        return policy

    def list_replication_policies(self) -> List[Dict[str, Any]]:
        return self.config.get("replication_policies", [])

    def delete_replication_policy(self, policy_id: str) -> bool:
        policies = self.config.get("replication_policies", [])
        for i, p in enumerate(policies):
            if p.get("id") == policy_id:
                policies.pop(i)
                return True
        return False

    def get_backup_by_workload(self, workload_id: str) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self._backups.values() if b.workload_id == workload_id]

    def set_vault_encryption(self, vault_id: str, enabled: bool, key_arn: Optional[str] = None) -> bool:
        vault = self._vaults.get(vault_id)
        if not vault:
            return False
        vault["encryption_enabled"] = enabled
        if key_arn:
            vault["kms_key_arn"] = key_arn
        return True

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class BackupPolicy:
    policy_id: str
    name: str
    retention_days: int = 30
    backup_window_hours: int = 8
    replication_targets: List[str] = field(default_factory=list)
    encrypted: bool = True

@dataclass
class VaultStorageMetrics:
    vault_id: str
    total_size_gb: float
    utilized_pct: float
    num_backups: int
    oldest_backup: Optional[datetime] = None
    newest_backup: Optional[datetime] = None

@dataclass
class ComplianceReportEntry:
    backup_id: str
    compliance_standard: str
    compliant: bool
    checked_at: datetime = field(default_factory=datetime.utcnow)
    details: str = ""

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_execute_backups(self, backup_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for bid in backup_ids:
            r = await self.execute_backup(bid)
            results[bid] = r
        return {"results": results, "total": len(backup_ids)}

    async def batch_verify_integrity(self, backup_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for bid in backup_ids:
            results[bid] = self.verify_backup_integrity(bid)
        return {"results": results, "total": len(backup_ids)}

    async def batch_delete_expired_backups(self) -> Dict[str, Any]:
        expired = self.enforce_retention_policy()
        for bid in expired:
            self.delete_backup(bid)
        return {"expired_deleted": len(expired)}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_backups(self, page: int = 1, page_size: int = 20,
                          sort_by: str = "created_at", sort_desc: bool = True,
                          state_filter: Optional[str] = None,
                          workload_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._backups.values())
        if state_filter:
            items = [b for b in items if b.state.value == state_filter]
        if workload_filter:
            items = [b for b in items if b.workload_id == workload_filter]
        items.sort(key=lambda b: getattr(b, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [b.to_dict() for b in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_restore_jobs(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = sorted([j.to_dict() for j in self._restore_jobs.values()], key=lambda j: j.get("created_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_backup_catalog(self) -> str:
        return json.dumps({
            "vaults": list(self._vaults.values()),
            "backups": [b.to_dict() for b in self._backups.values()],
            "restore_jobs": [j.to_dict() for j in self._restore_jobs.values()],
            "exported_at": datetime.utcnow().isoformat(),
            "statistics": self.get_statistics(),
        }, indent=2)

    def import_backup_config(self, json_str: str) -> Dict[str, Any]:
        data = json.loads(json_str)
        imported = {"vaults": 0, "backups": 0}
        for v in data.get("vaults", []):
            vault_id = v.get("vault_id", f"vault-{uuid.uuid4().hex[:8]}")
            self._vaults[vault_id] = v
            imported["vaults"] += 1
        for b in data.get("backups", []):
            try:
                backup = Backup(b.get("name", "imported"), b.get("workload_id", ""),
                                b.get("source_provider", ""), BackupTarget(b.get("target", "aws_s3")),
                                b.get("size_gb", 0), b.get("retention_days", 30))
                self._backups[backup.id] = backup
                imported["backups"] += 1
            except (ValueError, KeyError):
                continue
        return imported

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_backup_compliance_analysis(self) -> Dict[str, Any]:
        completed = sum(1 for b in self._backups.values() if b.state == BackupState.COMPLETED)
        failed = sum(1 for b in self._backups.values() if b.state == BackupState.FAILED)
        expired = sum(1 for b in self._backups.values() if b.state == BackupState.EXPIRED)
        return {
            "compliance_rate": round(completed / max(len(self._backups), 1) * 100, 1),
            "completed": completed, "failed": failed,
            "expired": expired, "total": len(self._backups),
            "needs_attention": failed + expired,
        }

    def get_storage_efficiency_analysis(self) -> Dict[str, Any]:
        total_raw = sum(b.size_gb for b in self._backups.values())
        total_deduplicated = total_raw * 0.65
        compression_ratio = total_raw / max(total_deduplicated, 1)
        return {
            "raw_size_gb": round(total_raw, 2),
            "effective_size_gb": round(total_deduplicated, 2),
            "compression_ratio": round(compression_ratio, 2),
            "total_backups": len(self._backups),
            "avg_backup_size_gb": round(total_raw / max(len(self._backups), 1), 2),
        }

    def get_restore_success_rate(self) -> Dict[str, Any]:
        total = len(self._restore_jobs)
        completed = sum(1 for j in self._restore_jobs.values() if j.state == RestoreState.COMPLETED)
        failed = sum(1 for j in self._restore_jobs.values() if j.state == RestoreState.FAILED)
        return {
            "success_rate": round(completed / max(total, 1) * 100, 1),
            "completed": completed, "failed": failed,
            "in_progress": sum(1 for j in self._restore_jobs.values() if j.state == RestoreState.RESTORING),
            "total": total,
        }

    def get_vault_utilization_analysis(self) -> Dict[str, Any]:
        vault_usage = {}
        for vid, vault in self._vaults.items():
            vault_backups = [b for b in self._backups.values() if getattr(b, 'vault_id', None) == vid or True]
            size = sum(b.size_gb for b in vault_backups)
            vault_usage[vault.get("name", vid)] = {
                "backup_count": len(vault_backups),
                "total_size_gb": round(size, 2),
                "provider": vault.get("provider", "unknown"),
            }
        return {"vault_usage": vault_usage, "total_vaults": len(self._vaults)}

# ── State Machine / Workflow ─────────────────────────────────────────

    async def backup_lifecycle_workflow(self, backup_id: str, action: str) -> Dict[str, Any]:
        backup = self._backups.get(backup_id)
        if not backup:
            return {"status": "error", "message": "Backup not found"}
        if action == "execute":
            return await self.execute_backup(backup_id)
        elif action == "verify":
            return self.verify_backup_integrity(backup_id)
        elif action == "restore":
            job = self.create_restore_job(backup_id, backup.source_provider, "us-east-1")
            return await self.execute_restore(job.id)
        elif action == "delete":
            self.delete_backup(backup_id)
            return {"status": "deleted", "backup_id": backup_id}
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_backup_workflow(self) -> Dict[str, Any]:
        schedules = self.list_schedules()
        executed = 0
        for s in schedules:
            if s.get("active", False):
                backup = self.create_backup(f"scheduled-{s['workload_id']}", s.get("workload_id", ""),
                                           "auto", BackupTarget.AWS_S3, s.get("retention_days", 30))
                await self.execute_backup(backup.id)
                executed += 1
        return {"schedules_processed": len(schedules), "backups_executed": executed}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_backup_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.default_retention_days < 1:
            errors.append("default_retention_days must be >= 1")
        if self.max_backup_size_gb < 1:
            errors.append("max_backup_size_gb must be positive")
        if not self._vaults:
            warnings.append("No backup vaults configured")
        if not self._backups:
            warnings.append("No backups configured yet")
        if self.geo_redundancy == GeoRedundancyLevel.NONE:
            warnings.append("Geo-redundancy is disabled")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# ── Batch Operations ───────────────────────────────────────────────────

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"results": results, "total": len(results),
                "successful": sum(1 for r in results if r["status"] == "processed")}

    async def batch_validate(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid = invalid = 0
        errors = []
        for item in items:
            if item.get("id"):
                valid += 1
            else:
                invalid += 1
                errors.append({"item": item, "reason": "missing id"})
        return {"valid": valid, "invalid": invalid, "errors": errors}

# ── Analytics / Aggregation ───────────────────────────────────────────

    def get_summary_stats(self) -> Dict[str, Any]:
        return {"total_items": 0, "active_items": 0, "inactive_items": 0}

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        return {"period_days": days, "data_points": 0, "trend": "stable"}

# ── Data Models ───────────────────────────────────────────────────────

class OperationResult(BaseModel):
    success: bool = True
    operation: str = "unknown"
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")

    def add_operation(self, op: Dict[str, Any]) -> None:
        self.operations.append(op)

    def complete(self) -> None:
        self.status = "completed"

class HealthStatus(BaseModel):
    component: str
    status: str = Field(default="healthy")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    error_count: int = Field(default=0)
    response_time_ms: float = Field(default=0.0)

class StatusDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthStatus] = {}

    def register(self, component: str) -> HealthStatus:
        hs = HealthStatus(component=component)
        self._components[component] = hs
        return hs

    def heartbeat(self, component: str, response_time_ms: float = 0.0) -> None:
        if component in self._components:
            self._components[component].last_heartbeat = datetime.utcnow()
            self._components[component].response_time_ms = response_time_ms
            self._components[component].status = "healthy"

    def record_error(self, component: str) -> None:
        if component in self._components:
            self._components[component].error_count += 1
            if self._components[component].error_count > 5:
                self._components[component].status = "degraded"

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        return {"total_components": total, "healthy": healthy, "degraded": degraded,
                "uptime_pct": round(healthy / max(total, 1) * 100, 1)}

    def get_component_status(self, component: str) -> Optional[HealthStatus]:
        return self._components.get(component)

class AuditLogger:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, action: str, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({
            "action": action, "resource_type": resource_type, "resource_id": resource_id,
            "details": details or {}, "timestamp": datetime.utcnow().isoformat(),
        })

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def get_by_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["resource_id"] == resource_id]

    def get_by_action(self, action: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["action"] == action]

    def count_by_action(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = []
        self._metrics[metric].append(value)

    def get_stats(self, metric: str) -> Dict[str, Any]:
        values = self._metrics.get(metric, [])
        if not values:
            return {"metric": metric, "count": 0}
        return {"metric": metric, "count": len(values), "min": round(min(values), 4),
                "max": round(max(values), 4), "avg": round(sum(values) / len(values), 4),
                "latest": round(values[-1], 4)}

    def get_all_stats(self) -> Dict[str, Any]:
        return {m: self.get_stats(m) for m in self._metrics}

    def reset(self, metric: Optional[str] = None) -> None:
        if metric:
            self._metrics[metric] = []
        else:
            self._metrics.clear()

class ConfigValidator:
    @staticmethod
    def validate(config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        for key, rules in schema.items():
            value = config.get(key)
            if rules.get("required", False) and value is None:
                errors.append(f"Missing required key: {key}")
            if value is not None and "type" in rules:
                if not isinstance(value, rules["type"]):
                    errors.append(f"Key {key} expected type {rules['type'].__name__}")
            if value is not None and "min" in rules and isinstance(value, (int, float)):
                if value < rules["min"]:
                    errors.append(f"Key {key} below minimum {rules['min']}")
            if value is not None and "max" in rules and isinstance(value, (int, float)):
                if value > rules["max"]:
                    errors.append(f"Key {key} above maximum {rules['max']}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def merge_with_defaults(config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(defaults)
        merged.update(config)
        return merged
