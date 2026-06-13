"""Backup Chain API integration module."""
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
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    LOG = "log"


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"
    RESTORING = "restoring"
    RESTORED = "restored"
    DELETED = "deleted"


class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"
    BZIP2 = "bzip2"
    LZ4 = "lz4"


@dataclass
class Backup:
    backup_id: str
    chain_id: str
    type: BackupType
    status: BackupStatus
    name: str
    source: str
    destination: str
    size_bytes: int
    compression: CompressionType
    encryption: bool
    checksum: str
    parent_backup_id: Optional[str]
    retention_days: int
    created_at: str
    completed_at: Optional[str]
    verified_at: Optional[str]
    restored_at: Optional[str]
    metadata: Dict[str, str]
    tags: List[str]
    version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "chain_id": self.chain_id,
            "type": self.type.value,
            "status": self.status.value,
            "name": self.name,
            "source": self.source,
            "destination": self.destination,
            "size_bytes": self.size_bytes,
            "size_display": self._format_size(),
            "compression": self.compression.value,
            "encryption": self.encryption,
            "checksum": self.checksum[:16] + "...",
            "parent_backup_id": self.parent_backup_id,
            "retention_days": self.retention_days,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "verified_at": self.verified_at,
            "tags": self.tags,
            "version": self.version,
        }

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
class BackupChain:
    chain_id: str
    name: str
    source: str
    destination: str
    retention_days: int
    full_backup_interval_days: int
    incremental_interval_hours: int
    compression: CompressionType
    encryption: bool
    created_at: str
    updated_at: str
    enabled: bool
    last_full_backup: Optional[str]
    last_backup: Optional[str]
    total_backups: int
    total_size_bytes: int
    verifications_passed: int
    verifications_failed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "name": self.name,
            "source": self.source,
            "destination": self.destination,
            "retention_days": self.retention_days,
            "full_backup_interval_days": self.full_backup_interval_days,
            "incremental_interval_hours": self.incremental_interval_hours,
            "compression": self.compression.value,
            "encryption": self.encryption,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": self.enabled,
            "last_full_backup": self.last_full_backup,
            "last_backup": self.last_backup,
            "total_backups": self.total_backups,
            "total_size_bytes": self.total_size_bytes,
            "total_size_display": self._format_bytes(self.total_size_bytes),
            "verifications_passed": self.verifications_passed,
            "verifications_failed": self.verifications_failed,
            "health_score": self._calculate_health(),
        }

    def _calculate_health(self) -> float:
        total = self.verifications_passed + self.verifications_failed
        if total == 0:
            return 0.0
        return round(self.verifications_passed / total * 100, 1)

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"


class BackupChainManager:
    """Full + incremental + differential backup chain management."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chains: Dict[str, BackupChain] = {}
        self.backups: Dict[str, Backup] = {}
        self._running = False
        self._total_bytes_backed_up = 0
        self._active_backups: set = set()
        self._restore_operations = 0

    async def initialize(self) -> None:
        self._running = True
        logger.info("Backup Chain Manager initialized")

    async def close(self) -> None:
        self._running = False
        logger.info("Backup Chain Manager shut down")

    async def create_chain(
        self,
        name: str,
        source: str,
        destination: str,
        retention_days: int = 30,
        full_backup_interval_days: int = 7,
        incremental_interval_hours: int = 6,
        compression: str = "zstd",
        encryption: bool = True,
    ) -> BackupChain:
        chain = BackupChain(
            chain_id=f"chain-{uuid.uuid4().hex[:8]}",
            name=name,
            source=source,
            destination=destination,
            retention_days=retention_days,
            full_backup_interval_days=full_backup_interval_days,
            incremental_interval_hours=incremental_interval_hours,
            compression=CompressionType(compression),
            encryption=encryption,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            enabled=True,
            last_full_backup=None,
            last_backup=None,
            total_backups=0,
            total_size_bytes=0,
            verifications_passed=0,
            verifications_failed=0,
        )
        self.chains[chain.chain_id] = chain
        logger.info(f"Created backup chain '{name}'")
        return chain

    async def create_backup(
        self,
        chain_id: str,
        type: str = "incremental",
        data: Optional[bytes] = None,
        tags: Optional[List[str]] = None,
    ) -> Backup:
        chain = self.chains.get(chain_id)
        if not chain:
            raise ValueError(f"Chain '{chain_id}' not found")

        backup_type = BackupType(type)
        parent_id = None
        if backup_type == BackupType.INCREMENTAL:
            last_backup = self._get_last_backup(chain_id)
            if last_backup:
                parent_id = last_backup.backup_id
        elif backup_type == BackupType.DIFFERENTIAL:
            last_full = self._get_last_full_backup(chain_id)
            if last_full:
                parent_id = last_full.backup_id

        backup = Backup(
            backup_id=f"bk-{uuid.uuid4().hex[:12]}",
            chain_id=chain_id,
            type=backup_type,
            status=BackupStatus.COMPLETED,
            name=f"{chain.name}-{backup_type.value}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            source=chain.source,
            destination=chain.destination,
            size_bytes=len(data) if data else 1024 * 1024,
            compression=chain.compression,
            encryption=chain.encryption,
            checksum=hashlib.sha256(data or b"").hexdigest(),
            parent_backup_id=parent_id,
            retention_days=chain.retention_days,
            created_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            verified_at=None,
            restored_at=None,
            metadata={},
            tags=tags or [],
            version=chain.total_backups + 1,
        )

        self.backups[backup.backup_id] = backup
        chain.total_backups += 1
        chain.total_size_bytes += backup.size_bytes
        chain.last_backup = backup.created_at
        chain.updated_at = datetime.utcnow().isoformat()
        self._total_bytes_backed_up += backup.size_bytes

        if backup_type == BackupType.FULL:
            chain.last_full_backup = backup.created_at

        return backup

    async def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        backup = self.backups.get(backup_id)
        return backup.to_dict() if backup else None

    async def list_backups(
        self,
        chain_id: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = list(self.backups.values())
        if chain_id:
            results = [b for b in results if b.chain_id == chain_id]
        if type:
            results = [b for b in results if b.type.value == type]
        if status:
            results = [b for b in results if b.status.value == status]
        results.sort(key=lambda b: b.created_at, reverse=True)
        return [b.to_dict() for b in results]

    async def verify_backup(self, backup_id: str) -> bool:
        backup = self.backups.get(backup_id)
        if not backup:
            return False
        backup.status = BackupStatus.VERIFIED
        backup.verified_at = datetime.utcnow().isoformat()

        chain = self.chains.get(backup.chain_id)
        if chain:
            chain.verifications_passed += 1
        return True

    async def restore_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        backup = self.backups.get(backup_id)
        if not backup:
            return None

        backup.status = BackupStatus.RESTORED
        backup.restored_at = datetime.utcnow().isoformat()
        self._restore_operations += 1

        restore_path = f"/restore/{backup.chain_id}/{backup.backup_id}"
        return {
            "backup_id": backup_id,
            "restore_path": restore_path,
            "size_bytes": backup.size_bytes,
            "type": backup.type.value,
            "restored_at": backup.restored_at,
            "includes_parents": backup.parent_backup_id is not None,
        }

    async def get_restore_path(self, backup_id: str) -> List[Dict[str, Any]]:
        backup = self.backups.get(backup_id)
        if not backup:
            return []

        chain = []
        current = backup
        while current:
            chain.append(current.to_dict())
            if current.parent_backup_id and current.parent_backup_id in self.backups:
                current = self.backups[current.parent_backup_id]
            else:
                current = None

        return chain

    async def delete_backup(self, backup_id: str) -> bool:
        if backup_id not in self.backups:
            return False
        backup = self.backups.pop(backup_id)
        backup.status = BackupStatus.DELETED
        chain = self.chains.get(backup.chain_id)
        if chain:
            chain.total_backups = max(0, chain.total_backups - 1)
            chain.total_size_bytes = max(0, chain.total_size_bytes - backup.size_bytes)
        return True

    async def get_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        chain = self.chains.get(chain_id)
        return chain.to_dict() if chain else None

    async def list_chains(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.chains.values()]

    async def delete_chain(self, chain_id: str) -> bool:
        if chain_id not in self.chains:
            return False
        chain_backups = [b.backup_id for b in self.backups.values() if b.chain_id == chain_id]
        for bid in chain_backups:
            self.backups.pop(bid, None)
        del self.chains[chain_id]
        return True

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chains": len(self.chains),
            "total_backups": len(self.backups),
            "total_bytes": self._total_bytes_backed_up,
            "total_size_display": self._format_bytes(self._total_bytes_backed_up),
            "full_backups": sum(1 for b in self.backups.values() if b.type == BackupType.FULL),
            "incremental_backups": sum(1 for b in self.backups.values() if b.type == BackupType.INCREMENTAL),
            "differential_backups": sum(1 for b in self.backups.values() if b.type == BackupType.DIFFERENTIAL),
            "verified_backups": sum(1 for b in self.backups.values() if b.status == BackupStatus.VERIFIED),
            "restore_operations": self._restore_operations,
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "chains": len(self.chains),
            "recent_backups": sum(1 for b in self.backups.values() if b.created_at > (datetime.utcnow() - timedelta(hours=24)).isoformat()),
        }

    def _get_last_backup(self, chain_id: str) -> Optional[Backup]:
        chain_backups = [b for b in self.backups.values() if b.chain_id == chain_id]
        if not chain_backups:
            return None
        return max(chain_backups, key=lambda b: b.created_at)

    def _get_last_full_backup(self, chain_id: str) -> Optional[Backup]:
        full_backups = [b for b in self.backups.values() if b.chain_id == chain_id and b.type == BackupType.FULL]
        if not full_backups:
            return None
        return max(full_backups, key=lambda b: b.created_at)

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"
