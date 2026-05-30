"""Object Storage Gateway integration module."""
import asyncio
import json
import hashlib
import hmac
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    B2 = "backblaze_b2"
    WASABI = "wasabi"
    MINIO = "minio"
    CEPH = "ceph_rgw"
    LOCAL = "local"


class BucketVisibility(Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    AUTHENTICATED_READ = "authenticated-read"


class StorageClass(Enum):
    STANDARD = "standard"
    INFREQUENT_ACCESS = "infrequent_access"
    GLACIER = "glacier"
    DEEP_ARCHIVE = "deep_archive"


@dataclass
class BucketPolicy:
    policy_id: str
    bucket_name: str
    statements: List[Dict[str, Any]]
    version: str = "2012-10-17"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Version": self.version,
            "Statement": self.statements,
        }

    @staticmethod
    def make_read_policy(bucket: str, principals: List[str] = None) -> "BucketPolicy":
        stmt = {
            "Effect": "Allow",
            "Principal": principals or ["*"],
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        }
        return BucketPolicy(
            policy_id=str(uuid.uuid4()),
            bucket_name=bucket,
            statements=[stmt],
        )


@dataclass
class LifecycleRule:
    rule_id: str
    prefix: str
    status: str = "Enabled"
    expiration_days: Optional[int] = None
    transition_to_ia_days: Optional[int] = None
    transition_to_glacier_days: Optional[int] = None
    abort_incomplete_multipart_days: int = 7
    noncurrent_version_expiration_days: Optional[int] = None

    def validate(self) -> List[str]:
        errors = []
        if self.expiration_days and self.expiration_days < 1:
            errors.append("expiration_days must be >= 1")
        if self.transition_to_ia_days and self.transition_to_ia_days < 30:
            errors.append("transition_to_ia_days must be >= 30")
        if self.transition_to_glacier_days and self.transition_to_glacier_days < 60:
            errors.append("transition_to_glacier_days must be >= 60")
        return errors


@dataclass
class Bucket:
    name: str
    region: str = "us-east-1"
    backend: StorageBackend = StorageBackend.S3
    visibility: BucketVisibility = BucketVisibility.PRIVATE
    storage_class: StorageClass = StorageClass.STANDARD
    versioning: bool = False
    encryption: bool = True
    object_lock: bool = False
    created_at: str = ""
    size_bytes: int = 0
    object_count: int = 0
    owner: str = "admin"
    tags: Dict[str, str] = field(default_factory=dict)
    lifecycle_rules: List[LifecycleRule] = field(default_factory=list)
    policy: Optional[BucketPolicy] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "region": self.region,
            "backend": self.backend.value,
            "visibility": self.visibility.value,
            "storage_class": self.storage_class.value,
            "versioning": self.versioning,
            "encryption": self.encryption,
            "object_lock": self.object_lock,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
            "object_count": self.object_count,
            "owner": self.owner,
            "tags": self.tags,
            "lifecycle_rules": [asdict(r) for r in self.lifecycle_rules],
            "has_policy": self.policy is not None,
        }


@dataclass
class StoredObject:
    key: str
    bucket: str
    size_bytes: int
    etag: str
    content_type: str = "application/octet-stream"
    storage_class: StorageClass = StorageClass.STANDARD
    version_id: str = ""
    last_modified: str = ""
    checksum_sha256: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    retention_until: Optional[str] = None
    legal_hold: bool = False

    def __post_init__(self):
        if not self.last_modified:
            self.last_modified = datetime.utcnow().isoformat()
        if not self.version_id:
            self.version_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "bucket": self.bucket,
            "size_bytes": self.size_bytes,
            "size_display": self._format_size(),
            "etag": self.etag,
            "content_type": self.content_type,
            "storage_class": self.storage_class.value,
            "version_id": self.version_id,
            "last_modified": self.last_modified,
            "checksum_sha256": self.checksum_sha256,
            "metadata": self.metadata,
            "tags": self.tags,
            "retention_until": self.retention_until,
            "legal_hold": self.legal_hold,
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


class ObjectStorageGateway:
    """S3-compatible object storage gateway supporting multiple backends."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.buckets: Dict[str, Bucket] = {}
        self.objects: Dict[str, Dict[str, StoredObject]] = {}
        self.access_keys: Dict[str, Dict[str, Any]] = {}
        self.presigned_urls: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._maintenance_mode = False
        self._operation_count = 0
        self._error_count = 0
        self._total_bytes_stored = 0
        self._bandwidth_used_today = 0
        self._request_count_today = 0

    async def initialize(self) -> None:
        self._running = True
        logger.info("Object Storage Gateway initialized")
        for bucket_config in self.config.get("buckets", []):
            bucket = Bucket(**bucket_config)
            self.buckets[bucket.name] = bucket
            self.objects[bucket.name] = {}

    async def close(self) -> None:
        self._running = False
        logger.info("Object Storage Gateway shut down")

    async def create_bucket(
        self,
        name: str,
        region: str = "us-east-1",
        backend: str = "s3",
        visibility: str = "private",
        versioning: bool = False,
        encryption: bool = True,
        tags: Optional[Dict[str, str]] = None,
    ) -> Bucket:
        if name in self.buckets:
            raise ValueError(f"Bucket '{name}' already exists")

        bucket = Bucket(
            name=name,
            region=region,
            backend=StorageBackend(backend),
            visibility=BucketVisibility(visibility),
            storage_class=StorageClass.STANDARD,
            versioning=versioning,
            encryption=encryption,
            tags=tags or {},
        )
        self.buckets[name] = bucket
        self.objects[name] = {}
        self._operation_count += 1
        logger.info(f"Created bucket '{name}' in {region}")
        return bucket

    async def delete_bucket(self, name: str) -> bool:
        if name not in self.buckets:
            raise ValueError(f"Bucket '{name}' not found")
        if self.objects.get(name):
            raise ValueError(f"Bucket '{name}' is not empty")
        del self.buckets[name]
        del self.objects[name]
        self._operation_count += 1
        logger.info(f"Deleted bucket '{name}'")
        return True

    async def list_buckets(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.buckets.values()]

    async def get_bucket(self, name: str) -> Dict[str, Any]:
        if name not in self.buckets:
            raise ValueError(f"Bucket '{name}' not found")
        return self.buckets[name].to_dict()

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> StoredObject:
        if bucket not in self.buckets:
            raise ValueError(f"Bucket '{bucket}' not found")

        checksum = hashlib.sha256(data).hexdigest()
        etag = hashlib.md5(data).hexdigest()

        obj = StoredObject(
            key=key,
            bucket=bucket,
            size_bytes=len(data),
            etag=etag,
            content_type=content_type,
            checksum_sha256=checksum,
            metadata=metadata or {},
            tags=tags or {},
        )

        if key not in self.objects[bucket]:
            self.objects[bucket][key] = obj
        else:
            existing = self.objects[bucket][key]
            existing.etag = etag
            existing.size_bytes = len(data)
            existing.checksum_sha256 = checksum
            existing.content_type = content_type
            existing.last_modified = datetime.utcnow().isoformat()
            existing.metadata = metadata or {}
            existing.tags = tags or {}
            existing.version_id = str(uuid.uuid4())

        self.buckets[bucket].size_bytes += len(data)
        self.buckets[bucket].object_count += 1
        self._total_bytes_stored += len(data)
        self._operation_count += 1

        return obj

    async def get_object(self, bucket: str, key: str) -> Optional[StoredObject]:
        if bucket not in self.objects:
            return None
        return self.objects[bucket].get(key)

    async def delete_object(self, bucket: str, key: str) -> bool:
        if bucket not in self.objects or key not in self.objects[bucket]:
            return False
        obj = self.objects[bucket].pop(key)
        self.buckets[bucket].size_bytes -= obj.size_bytes
        self.buckets[bucket].object_count -= 1
        self._operation_count += 1
        return True

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "",
        max_keys: int = 1000,
    ) -> Dict[str, Any]:
        if bucket not in self.objects:
            return {"objects": [], "common_prefixes": [], "is_truncated": False}

        objects = list(self.objects[bucket].values())
        if prefix:
            objects = [o for o in objects if o.key.startswith(prefix)]

        objects.sort(key=lambda o: o.key)

        common_prefixes = set()
        if delimiter:
            filtered = []
            for o in objects:
                rest = o.key[len(prefix):] if prefix else o.key
                if delimiter in rest:
                    common_prefixes.add(prefix + rest.split(delimiter)[0] + delimiter)
                else:
                    filtered.append(o)
            objects = filtered

        truncated = len(objects) > max_keys
        return {
            "objects": [o.to_dict() for o in objects[:max_keys]],
            "common_prefixes": sorted(common_prefixes),
            "is_truncated": truncated,
        }

    async def set_bucket_policy(self, bucket: str, policy: BucketPolicy) -> bool:
        if bucket not in self.buckets:
            raise ValueError(f"Bucket '{bucket}' not found")
        self.buckets[bucket].policy = policy
        return True

    async def get_bucket_policy(self, bucket: str) -> Optional[Dict[str, Any]]:
        if bucket not in self.buckets:
            return None
        policy = self.buckets[bucket].policy
        return policy.to_dict() if policy else None

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        method: str = "GET",
        expires_in: int = 3600,
    ) -> str:
        url_id = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        self.presigned_urls[url_id] = {
            "bucket": bucket,
            "key": key,
            "method": method,
            "expires_at": expiry.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
        return f"https://storage.infrapilot.io/{bucket}/{key}?token={url_id}&expires={int(expiry.timestamp())}"

    async def set_lifecycle_rules(
        self, bucket: str, rules: List[LifecycleRule]
    ) -> bool:
        if bucket not in self.buckets:
            raise ValueError(f"Bucket '{bucket}' not found")
        errors = []
        for rule in rules:
            errors.extend(rule.validate())
        if errors:
            raise ValueError(f"Lifecycle rule validation failed: {errors}")
        self.buckets[bucket].lifecycle_rules = rules
        return True

    async def get_lifecycle_rules(self, bucket: str) -> List[Dict[str, Any]]:
        if bucket not in self.buckets:
            return []
        return [asdict(r) for r in self.buckets[bucket].lifecycle_rules]

    async def set_bucket_versioning(self, bucket: str, enabled: bool) -> bool:
        if bucket not in self.buckets:
            raise ValueError(f"Bucket '{bucket}' not found")
        self.buckets[bucket].versioning = enabled
        return True

    async def set_bucket_encryption(self, bucket: str, enabled: bool) -> bool:
        if bucket not in self.buckets:
            raise ValueError(f"Bucket '{bucket}' not found")
        self.buckets[bucket].encryption = enabled
        return True

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_buckets": len(self.buckets),
            "total_objects": sum(len(objs) for objs in self.objects.values()),
            "total_bytes_stored": self._total_bytes_stored,
            "total_bytes_display": self._format_bytes(self._total_bytes_stored),
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "bandwidth_used_today": self._bandwidth_used_today,
            "requests_today": self._request_count_today,
            "maintenance_mode": self._maintenance_mode,
            "running": self._running,
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "buckets": len(self.buckets),
            "objects": sum(len(objs) for objs in self.objects.values()),
            "errors": self._error_count,
        }

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"

    async def simulate_workload(self, num_ops: int = 100) -> Dict[str, Any]:
        start = time.monotonic()
        ops_done = 0
        errors = 0

        for i in range(num_ops // 3):
            bname = f"test-bucket-{uuid.uuid4().hex[:8]}"
            try:
                await self.create_bucket(bname, region="us-east-1")
                ops_done += 1
                for j in range(3):
                    data = os.urandom(1024)
                    await self.put_object(bname, f"test-obj-{j}.bin", data)
                    ops_done += 1
                await self.delete_bucket(bname)
                ops_done += 1
            except Exception as e:
                errors += 1
                logger.warning(f"Workload error: {e}")

        elapsed = time.monotonic() - start
        return {
            "operations": ops_done,
            "errors": errors,
            "elapsed_seconds": round(elapsed, 2),
            "ops_per_second": round(ops_done / elapsed, 2) if elapsed > 0 else 0,
        }
