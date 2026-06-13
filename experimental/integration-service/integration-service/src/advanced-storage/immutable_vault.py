"""Immutable Vault integration module."""
import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LockMode(Enum):
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"
    LEGAL_HOLD = "legal_hold"


class VaultStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AUDIT_PENDING = "audit_pending"
    BREACHED = "breached"


class RetentionMode(Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    CUSTOM = "custom"


@dataclass
class VaultObject:
    object_id: str
    name: str
    bucket: str
    size_bytes: int
    checksum_sha256: str
    content_type: str
    created_at: str
    retention_until: str
    locked: bool
    lock_mode: Optional[LockMode]
    legal_hold: bool
    access_count: int
    last_accessed: Optional[str]
    tags: Dict[str, str]
    metadata: Dict[str, str]
    version: int
    immutable: bool
    compliance_tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "bucket": self.bucket,
            "size_bytes": self.size_bytes,
            "size_display": self._format_size(),
            "checksum_sha256": self.checksum_sha256[:16] + "...",
            "content_type": self.content_type,
            "created_at": self.created_at,
            "retention_until": self.retention_until,
            "locked": self.locked,
            "lock_mode": self.lock_mode.value if self.lock_mode else None,
            "legal_hold": self.legal_hold,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "tags": self.tags,
            "version": self.version,
            "immutable": self.immutable,
            "days_until_expiry": self._days_until_expiry(),
            "compliance_tags": self.compliance_tags,
        }

    def _days_until_expiry(self) -> int:
        retention = datetime.fromisoformat(self.retention_until)
        delta = retention - datetime.utcnow()
        return max(0, delta.days)

    def _format_size(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 ** 2:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 ** 3:
            return f"{self.size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{self.size_bytes / 1024 ** 3:.2f} GB"


@dataclass
class RetentionPolicy:
    policy_id: str
    name: str
    description: str
    retention_days: int
    compliance_hold: bool
    legal_hold: bool
    lock_mode: LockMode
    created_at: str
    updated_at: str
    enabled: bool
    applies_to_buckets: List[str]
    min_versions: int
    auto_expire: bool
    notify_before_expiry_days: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "retention_days": self.retention_days,
            "compliance_hold": self.compliance_hold,
            "legal_hold": self.legal_hold,
            "lock_mode": self.lock_mode.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": self.enabled,
            "applies_to_buckets": self.applies_to_buckets,
            "min_versions": self.min_versions,
            "auto_expire": self.auto_expire,
            "notify_before_expiry_days": self.notify_before_expiry_days,
        }


@dataclass
class ComplianceAudit:
    audit_id: str
    timestamp: str
    status: VaultStatus
    checks_passed: int
    checks_failed: int
    details: List[Dict[str, Any]]
    checked_by: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "details": self.details,
            "checked_by": self.checked_by,
        }


class ImmutableVault:
    """WORM storage vault with Object Lock and compliance features."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.objects: Dict[str, VaultObject] = {}
        self.policies: Dict[str, RetentionPolicy] = {}
        self.audits: List[ComplianceAudit] = []
        self.audit_log: List[Dict[str, Any]] = []
        self._running = False
        self._total_bytes_protected = 0
        self._lock_operations = 0
        self._breach_attempts = 0

    async def initialize(self) -> None:
        self._running = True
        logger.info("Immutable Vault initialized")

    async def close(self) -> None:
        self._running = False
        logger.info("Immutable Vault shut down")

    async def store_object(
        self,
        name: str,
        bucket: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        retention_days: int = 365,
        lock_mode: str = "compliance",
        legal_hold: bool = False,
        tags: Optional[Dict[str, str]] = None,
        compliance_tags: Optional[List[str]] = None,
    ) -> VaultObject:
        obj_id = f"obj-{uuid.uuid4().hex[:12]}"
        checksum = hashlib.sha256(data).hexdigest()
        retention_until = (datetime.utcnow() + timedelta(days=retention_days)).isoformat()

        obj = VaultObject(
            object_id=obj_id,
            name=name,
            bucket=bucket,
            size_bytes=len(data),
            checksum_sha256=checksum,
            content_type=content_type,
            created_at=datetime.utcnow().isoformat(),
            retention_until=retention_until,
            locked=True,
            lock_mode=LockMode(lock_mode),
            legal_hold=legal_hold,
            access_count=0,
            last_accessed=None,
            tags=tags or {},
            metadata={},
            version=1,
            immutable=True,
            compliance_tags=compliance_tags or [],
        )
        self.objects[obj_id] = obj
        self._total_bytes_protected += len(data)
        self._lock_operations += 1
        self._audit_log_entry("STORE", f"Stored '{name}' in vault (retention: {retention_days}d)")
        return obj

    async def get_object(self, object_id: str) -> Optional[VaultObject]:
        obj = self.objects.get(object_id)
        if obj:
            obj.access_count += 1
            obj.last_accessed = datetime.utcnow().isoformat()
        return obj

    async def list_objects(
        self,
        bucket: Optional[str] = None,
        locked_only: bool = False,
        legal_hold_only: bool = False,
    ) -> List[Dict[str, Any]]:
        results = list(self.objects.values())
        if bucket:
            results = [o for o in results if o.bucket == bucket]
        if locked_only:
            results = [o for o in results if o.locked]
        if legal_hold_only:
            results = [o for o in results if o.legal_hold]
        return [o.to_dict() for o in sorted(results, key=lambda x: x.created_at, reverse=True)]

    async def extend_retention(
        self, object_id: str, additional_days: int
    ) -> bool:
        obj = self.objects.get(object_id)
        if not obj:
            return False
        current = datetime.fromisoformat(obj.retention_until)
        obj.retention_until = (current + timedelta(days=additional_days)).isoformat()
        self._audit_log_entry("EXTEND_RETENTION", f"Extended retention for '{obj.name}' by {additional_days}d")
        return True

    async def add_legal_hold(self, object_id: str) -> bool:
        obj = self.objects.get(object_id)
        if not obj:
            return False
        obj.legal_hold = True
        self._audit_log_entry("LEGAL_HOLD", f"Added legal hold to '{obj.name}'")
        return True

    async def remove_legal_hold(self, object_id: str) -> bool:
        obj = self.objects.get(object_id)
        if not obj:
            return False
        obj.legal_hold = False
        self._audit_log_entry("REMOVE_LEGAL_HOLD", f"Removed legal hold from '{obj.name}'")
        return True

    async def create_retention_policy(
        self,
        name: str,
        retention_days: int,
        lock_mode: str = "compliance",
        compliance_hold: bool = False,
        legal_hold: bool = False,
        applies_to_buckets: Optional[List[str]] = None,
        min_versions: int = 1,
        auto_expire: bool = False,
        notify_before_expiry_days: int = 30,
    ) -> RetentionPolicy:
        policy = RetentionPolicy(
            policy_id=f"pol-{uuid.uuid4().hex[:8]}",
            name=name,
            description="",
            retention_days=retention_days,
            compliance_hold=compliance_hold,
            legal_hold=legal_hold,
            lock_mode=LockMode(lock_mode),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            enabled=True,
            applies_to_buckets=applies_to_buckets or [],
            min_versions=min_versions,
            auto_expire=auto_expire,
            notify_before_expiry_days=notify_before_expiry_days,
        )
        self.policies[policy.policy_id] = policy
        self._audit_log_entry("CREATE_POLICY", f"Created retention policy '{name}' ({retention_days}d)")
        return policy

    async def list_policies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self.policies.values()]

    async def delete_policy(self, policy_id: str) -> bool:
        if policy_id not in self.policies:
            return False
        del self.policies[policy_id]
        self._audit_log_entry("DELETE_POLICY", f"Deleted retention policy '{policy_id}'")
        return True

    async def run_compliance_audit(self, checked_by: str = "system") -> ComplianceAudit:
        checks_passed = 0
        checks_failed = 0
        details = []

        for obj_id, obj in self.objects.items():
            if obj.legal_hold:
                checks_passed += 1
            elif obj.locked and not obj.immutable:
                checks_failed += 1
                details.append({"object_id": obj_id, "issue": "Object locked but not immutable"})
            else:
                checks_passed += 1

            retention = datetime.fromisoformat(obj.retention_until)
            if datetime.utcnow() > retention and not obj.legal_hold:
                checks_failed += 1
                details.append({"object_id": obj_id, "issue": "Retention period expired"})

        status = VaultStatus.COMPLIANT if checks_failed == 0 else VaultStatus.NON_COMPLIANT
        audit = ComplianceAudit(
            audit_id=f"audit-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat(),
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
            checked_by=checked_by,
        )
        self.audits.append(audit)
        self._audit_log_entry("AUDIT", f"Compliance audit: {checks_passed} passed, {checks_failed} failed")
        return audit

    async def generate_air_gap_recovery_plan(self) -> Dict[str, Any]:
        total_size = sum(o.size_bytes for o in self.objects.values())
        return {
            "plan_id": f"recovery-{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.utcnow().isoformat(),
            "total_objects": len(self.objects),
            "total_size_bytes": total_size,
            "total_size_display": self._format_bytes(total_size),
            "required_media": self._estimate_media(total_size),
            "procedure_steps": [
                "Retrieve physical media from secure storage",
                "Connect to isolated recovery workstation",
                "Authenticate with hardware security key",
                "Decrypt vault encryption keys",
                "Verify data integrity using SHA-256 checksums",
                "Restore to temporary isolated environment",
                "Run validation against known-good snapshots",
                "Transfer verified data to production",
                "Log and sign off on recovery operation",
            ],
            "estimated_recovery_time": self._estimate_recovery_time(total_size),
        }

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_objects": len(self.objects),
            "locked_objects": sum(1 for o in self.objects.values() if o.locked),
            "legal_hold_objects": sum(1 for o in self.objects.values() if o.legal_hold),
            "total_bytes_protected": self._total_bytes_protected,
            "total_size_display": self._format_bytes(self._total_bytes_protected),
            "policies": len(self.policies),
            "lock_operations": self._lock_operations,
            "breach_attempts": self._breach_attempts,
            "audits_performed": len(self.audits),
            "running": self._running,
        }

    async def health_check(self) -> Dict[str, Any]:
        audit_status = VaultStatus.COMPLIANT
        for audit in reversed(self.audits):
            if audit.status != VaultStatus.COMPLIANT:
                audit_status = audit.status
                break
        return {
            "status": "healthy" if self._running else "unhealthy",
            "compliance_status": audit_status.value,
            "total_objects": len(self.objects),
            "locked_percentage": round(sum(1 for o in self.objects.values() if o.locked) / max(len(self.objects), 1) * 100, 1),
        }

    def _estimate_media(self, size_bytes: int) -> List[Dict[str, Any]]:
        lto9_capacity = 18 * 1024 ** 4
        tapes_needed = max(1, (size_bytes + lto9_capacity - 1) // lto9_capacity)
        return [
            {"media_type": "LTO-9 Tape", "capacity": "18 TB", "count": tapes_needed},
            {"media_type": "Encryption Key USB", "capacity": "64 GB", "count": 2},
        ]

    def _estimate_recovery_time(self, size_bytes: int) -> str:
        restore_speed_mbps = 500
        seconds = size_bytes / (restore_speed_mbps * 1024 * 1024 / 8)
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            return f"{seconds / 60:.0f} minutes"
        else:
            return f"{seconds / 3600:.1f} hours"

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"

    def _audit_log_entry(self, action: str, details: str) -> None:
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
        })
