"""Data Migration integration module."""
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
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TransferMethod(Enum):
    RSYNC = "rsync"
    RCLONE = "rclone"
    S3_SYNC = "s3_sync"
    MULTIPART = "multipart_upload"
    STREAM = "stream_copy"


class ChecksumAlgorithm(Enum):
    MD5 = "md5"
    SHA256 = "sha256"
    XXHASH = "xxhash"
    BLAKE3 = "blake3"


@dataclass
class MigrationJob:
    job_id: str
    name: str
    source_type: str
    source_path: str
    destination_type: str
    destination_path: str
    status: MigrationStatus
    progress: float
    total_bytes: int
    transferred_bytes: int
    total_files: int
    transferred_files: int
    error_count: int
    warning_count: int
    started_at: Optional[str]
    completed_at: Optional[str]
    checksum_algorithm: ChecksumAlgorithm
    checksum_match: Optional[bool]
    bandwidth_limit_mbps: int
    rollback_available: bool
    retry_count: int
    estimated_time_remaining: Optional[str]
    created_by: str
    tags: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "destination_type": self.destination_type,
            "destination_path": self.destination_path,
            "status": self.status.value,
            "progress": round(self.progress, 1),
            "total_bytes": self.total_bytes,
            "total_gb": round(self.total_bytes / (1024**3), 2),
            "transferred_bytes": self.transferred_bytes,
            "transferred_gb": round(self.transferred_bytes / (1024**3), 2),
            "total_files": self.total_files,
            "transferred_files": self.transferred_files,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "checksum_algorithm": self.checksum_algorithm.value,
            "checksum_match": self.checksum_match,
            "bandwidth_limit_mbps": self.bandwidth_limit_mbps,
            "rollback_available": self.rollback_available,
            "retry_count": self.retry_count,
            "created_by": self.created_by,
            "tags": self.tags,
        }


@dataclass
class MigrationLog:
    log_id: str
    job_id: str
    level: str
    message: str
    timestamp: str
    file_path: Optional[str] = None
    bytes_processed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "job_id": self.job_id,
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "bytes_processed": self.bytes_processed,
        }


class DataMigrationManager:
    """Guided migration manager between storage backends."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jobs: Dict[str, MigrationJob] = {}
        self.logs: Dict[str, List[MigrationLog]] = {}
        self.snapshots: Dict[str, str] = {}
        self._running = False
        self._total_bytes_migrated = 0
        self._active_jobs: Set[str] = set()
        self._cancellation_flags: Set[str] = set()
        self._supported_backends = {
            "local", "s3", "backblaze_b2", "wasabi", "gcs",
            "azure", "minio", "nfs", "ceph_rgw", "smb",
        }

    async def initialize(self) -> None:
        self._running = True
        logger.info("Data Migration Manager initialized")

    async def close(self) -> None:
        self._running = False
        for job_id in list(self._active_jobs):
            await self.cancel_job(job_id)
        logger.info("Data Migration Manager shut down")

    async def create_job(
        self,
        name: str,
        source_type: str,
        source_path: str,
        destination_type: str,
        destination_path: str,
        checksum_algorithm: str = "sha256",
        bandwidth_limit_mbps: int = 100,
        created_by: str = "admin",
        tags: Optional[Dict[str, str]] = None,
    ) -> MigrationJob:
        if source_type not in self._supported_backends:
            raise ValueError(f"Unsupported source type: {source_type}")
        if destination_type not in self._supported_backends:
            raise ValueError(f"Unsupported destination type: {destination_type}")

        job = MigrationJob(
            job_id=f"mig-{int(time.time())}",
            name=name,
            source_type=source_type,
            source_path=source_path,
            destination_type=destination_type,
            destination_path=destination_path,
            status=MigrationStatus.PENDING,
            progress=0.0,
            total_bytes=0,
            transferred_bytes=0,
            total_files=0,
            transferred_files=0,
            error_count=0,
            warning_count=0,
            started_at=None,
            completed_at=None,
            checksum_algorithm=ChecksumAlgorithm(checksum_algorithm),
            checksum_match=None,
            bandwidth_limit_mbps=bandwidth_limit_mbps,
            rollback_available=True,
            retry_count=0,
            estimated_time_remaining=None,
            created_by=created_by,
            tags=tags or {},
        )
        self.jobs[job.job_id] = job
        self.logs[job.job_id] = []
        logger.info(f"Created migration job '{job.job_id}': {name}")
        return job

    async def start_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")
        if job.status != MigrationStatus.PENDING:
            raise ValueError(f"Job '{job_id}' is not in pending state")

        job.status = MigrationStatus.RUNNING
        job.started_at = datetime.utcnow().isoformat()
        self._active_jobs.add(job_id)
        self._add_log(job_id, "INFO", f"Migration job '{job.name}' started")
        return True

    async def update_progress(
        self,
        job_id: str,
        progress: float,
        transferred_bytes: int,
        transferred_files: int,
    ) -> None:
        job = self.jobs.get(job_id)
        if not job:
            return
        job.progress = min(progress, 100.0)
        job.transferred_bytes = transferred_bytes
        job.transferred_files = transferred_files
        self._total_bytes_migrated += transferred_bytes

    async def complete_job(
        self, job_id: str, checksum_match: bool
    ) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.status = MigrationStatus.COMPLETED
        job.progress = 100.0
        job.completed_at = datetime.utcnow().isoformat()
        job.checksum_match = checksum_match
        self._active_jobs.discard(job_id)
        self._add_log(job_id, "INFO", f"Migration job completed. Checksum: {'OK' if checksum_match else 'MISMATCH'}")
        return True

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.status = MigrationStatus.FAILED
        job.completed_at = datetime.utcnow().isoformat()
        self._active_jobs.discard(job_id)
        self._add_log(job_id, "ERROR", f"Migration failed: {error_message}")
        return True

    async def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False

        self._cancellation_flags.add(job_id)
        job.status = MigrationStatus.CANCELLED
        job.completed_at = datetime.utcnow().isoformat()
        self._active_jobs.discard(job_id)
        self._add_log(job_id, "WARN", "Migration cancelled by user")
        return True

    async def pause_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.status != MigrationStatus.RUNNING:
            return False
        job.status = MigrationStatus.PAUSED
        self._add_log(job_id, "WARN", "Migration paused")
        return True

    async def resume_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.status != MigrationStatus.PAUSED:
            return False
        job.status = MigrationStatus.RUNNING
        self._add_log(job_id, "INFO", "Migration resumed")
        return True

    async def rollback_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        if not job.rollback_available:
            raise ValueError("Rollback not available for this job")

        job.status = MigrationStatus.ROLLED_BACK
        job.rollback_available = False
        job.completed_at = datetime.utcnow().isoformat()
        self._add_log(job_id, "INFO", "Migration rolled back successfully")
        return True

    async def retry_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.status != MigrationStatus.FAILED:
            return False

        job.status = MigrationStatus.PENDING
        job.progress = 0.0
        job.transferred_bytes = 0
        job.transferred_files = 0
        job.error_count = 0
        job.warning_count = 0
        job.started_at = None
        job.completed_at = None
        job.checksum_match = None
        job.retry_count += 1
        self._add_log(job_id, "INFO", f"Job queued for retry (attempt {job.retry_count})")
        return True

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    async def list_jobs(
        self,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = list(self.jobs.values())
        if status:
            results = [j for j in results if j.status.value == status]
        if created_by:
            results = [j for j in results if j.created_by == created_by]
        results.sort(key=lambda j: j.started_at or "", reverse=True)
        return [j.to_dict() for j in results]

    async def get_job_logs(
        self,
        job_id: str,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        logs = self.logs.get(job_id, [])
        if level:
            logs = [l for l in logs if l.level == level]
        return [l.to_dict() for l in logs[-limit:]]

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": len(self._active_jobs),
            "completed": sum(1 for j in self.jobs.values() if j.status == MigrationStatus.COMPLETED),
            "failed": sum(1 for j in self.jobs.values() if j.status == MigrationStatus.FAILED),
            "total_bytes_migrated": self._total_bytes_migrated,
            "total_gb_migrated": round(self._total_bytes_migrated / (1024**3), 2),
            "running": self._running,
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "active_jobs": len(self._active_jobs),
            "failed_jobs": sum(1 for j in self.jobs.values() if j.status == MigrationStatus.FAILED),
        }

    async def validate_paths(
        self, source_path: str, destination_path: str
    ) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not source_path:
            errors.append("Source path is required")
        if not destination_path:
            errors.append("Destination path is required")
        if source_path == destination_path:
            warnings.append("Source and destination are the same")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _add_log(
        self, job_id: str, level: str, message: str, file_path: Optional[str] = None
    ) -> None:
        log = MigrationLog(
            log_id=f"log-{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            level=level,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            file_path=file_path,
        )
        if job_id in self.logs:
            self.logs[job_id].append(log)
