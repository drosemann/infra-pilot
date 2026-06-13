import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RegistryProvider(Enum):
    AWS_ECR = "aws_ecr"
    AZURE_ACR = "azure_acr"
    GCP_GCR = "gcp_gcr"
    GCP_ARTIFACT = "gcp_artifact"
    DOCKER_HUB = "docker_hub"
    GHCR = "ghcr"
    GITLAB = "gitlab"
    HETZNER = "hetzner"
    OVH = "ovh"
    DIGITALOCEAN = "digitalocean"


class ReplicationState(Enum):
    PENDING = "pending"
    REPLICATING = "replicating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScanSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ContainerImage:
    def __init__(self, name: str, tag: str, digest: str,
                 registry: RegistryProvider, repository: str,
                 size_bytes: int = 0):
        self.id = str(uuid.uuid4())
        self.name = name
        self.tag = tag
        self.digest = digest
        self.registry = registry
        self.repository = repository
        self.size_bytes = size_bytes
        self.labels: Dict[str, str] = {}
        self.created_at = datetime.utcnow()
        self.last_pulled: Optional[datetime] = None
        self.vulnerability_count = 0
        self.max_severity = ScanSeverity.NONE

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "tag": self.tag,
                "digest": self.digest, "registry": self.registry.value,
                "repository": self.repository, "size_bytes": self.size_bytes,
                "labels": self.labels, "created_at": self.created_at.isoformat(),
                "last_pulled": self.last_pulled.isoformat() if self.last_pulled else None,
                "vulnerability_count": self.vulnerability_count,
                "max_severity": self.max_severity.value}


class ReplicationRule:
    def __init__(self, source_registry: RegistryProvider,
                 target_registries: List[RegistryProvider],
                 image_pattern: str = "*",
                 filter_tags: Optional[List[str]] = None,
                 sync_on_push: bool = True):
        self.id = str(uuid.uuid4())
        self.source_registry = source_registry
        self.target_registries = target_registries
        self.image_pattern = image_pattern
        self.filter_tags = filter_tags or ["*"]
        self.sync_on_push = sync_on_push
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "source_registry": self.source_registry.value,
                "target_registries": [r.value for r in self.target_registries],
                "image_pattern": self.image_pattern, "filter_tags": self.filter_tags,
                "sync_on_push": self.sync_on_push, "created_at": self.created_at.isoformat()}


class CrossCloudRegistryReplicator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pull_through_cache_enabled = config.get("pull_through_cache_enabled", True)
        self.cache_ttl_hours = config.get("cache_ttl_hours", 24)
        self.max_concurrent_replications = config.get("max_concurrent_replications", 10)
        self.scan_on_replicate = config.get("scan_on_replicate", True)
        self.default_registry = RegistryProvider(config.get("default_registry", "docker_hub"))
        self._images: Dict[str, ContainerImage] = {}
        self._rules: Dict[str, ReplicationRule] = {}
        self._replication_jobs: List[Dict[str, Any]] = []
        self._pull_through_cache: Dict[str, Dict[str, Any]] = {}
        self._registries: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        for provider in RegistryProvider:
            reg_config = self.config.get(provider.value, {})
            if reg_config:
                self._registries[provider.value] = {
                    "provider": provider.value, "name": reg_config.get("name", provider.value),
                    "endpoint": reg_config.get("endpoint", ""), "configured": True
                }
        self._initialized = True
        logger.info(f"CrossCloudRegistryReplicator initialized with {len(self._registries)} registries")

    async def close(self) -> None:
        self._images.clear()
        self._rules.clear()
        logger.info("CrossCloudRegistryReplicator closed")

    def register_image(self, name: str, tag: str, digest: str,
                       registry: RegistryProvider, repository: str,
                       size_bytes: int = 0,
                       labels: Optional[Dict[str, str]] = None) -> ContainerImage:
        img = ContainerImage(name, tag, digest, registry, repository, size_bytes)
        if labels:
            img.labels = labels
        self._images[img.id] = img
        logger.info(f"Image registered: {name}:{tag} on {registry.value}")
        return img

    def get_image(self, image_id: str) -> Optional[ContainerImage]:
        return self._images.get(image_id)

    def list_images(self, registry: Optional[str] = None,
                    repository: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for img in self._images.values():
            if registry and img.registry.value != registry:
                continue
            if repository and img.repository != repository:
                continue
            results.append(img.to_dict())
        return results

    def delete_image(self, image_id: str) -> bool:
        if image_id in self._images:
            del self._images[image_id]
            return True
        return False

    def create_replication_rule(self, source_registry: RegistryProvider,
                                 target_registries: List[RegistryProvider],
                                 image_pattern: str = "*",
                                 filter_tags: Optional[List[str]] = None,
                                 sync_on_push: bool = True) -> ReplicationRule:
        rule = ReplicationRule(source_registry, target_registries,
                               image_pattern, filter_tags, sync_on_push)
        self._rules[rule.id] = rule
        logger.info(f"Replication rule created: {source_registry.value} -> {[r.value for r in target_registries]}")
        return rule

    def get_rule(self, rule_id: str) -> Optional[ReplicationRule]:
        return self._rules.get(rule_id)

    def list_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._rules.values()]

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    async def replicate_image(self, image_id: str,
                               target_registries: Optional[List[RegistryProvider]] = None) -> Dict[str, Any]:
        img = self._images.get(image_id)
        if not img:
            return {"status": "error", "message": "Image not found"}
        targets = target_registries or [r for r in RegistryProvider if r != img.registry]
        results = []
        for target in targets:
            job_id = f"repl-{uuid.uuid4().hex[:10]}"
            job = {"job_id": job_id, "image_id": image_id,
                   "image_name": f"{img.name}:{img.tag}",
                   "source_registry": img.registry.value,
                   "target_registry": target.value,
                   "state": ReplicationState.REPLICATING.value,
                   "started_at": datetime.utcnow().isoformat()}
            await asyncio.sleep(0.3)
            job["state"] = ReplicationState.COMPLETED.value
            job["completed_at"] = datetime.utcnow().isoformat()
            self._replication_jobs.append(job)
            results.append(job)
            logger.info(f"Replicated {img.name}:{img.tag} to {target.value}")
        return {"image_id": image_id, "results": results, "replicated_count": len(results)}

    def get_pull_through_cache(self, image_key: str) -> Optional[Dict[str, Any]]:
        return self._pull_through_cache.get(image_key)

    def set_pull_through_cache(self, image_key: str, registry: RegistryProvider,
                                data: Dict[str, Any]) -> None:
        cache_entry = {"image_key": image_key, "registry": registry.value,
                       "data": data, "cached_at": datetime.utcnow().isoformat(),
                       "ttl_hours": self.cache_ttl_hours}
        self._pull_through_cache[image_key] = cache_entry

    def list_cached_images(self) -> List[Dict[str, Any]]:
        return list(self._pull_through_cache.values())

    def clear_cache(self) -> int:
        count = len(self._pull_through_cache)
        self._pull_through_cache.clear()
        return count

    def scan_image_vulnerabilities(self, image_id: str) -> Dict[str, Any]:
        img = self._images.get(image_id)
        if not img:
            return {"status": "error", "message": "Image not found"}
        import random
        img.vulnerability_count = random.randint(0, 15)
        severities = [s for s in ScanSeverity]
        img.max_severity = severities[random.randint(0, min(img.vulnerability_count, 4))]
        return {"image_id": image_id, "vulnerability_count": img.vulnerability_count,
                "max_severity": img.max_severity.value,
                "scan_date": datetime.utcnow().isoformat()}

    def list_registries(self) -> List[Dict[str, Any]]:
        return list(self._registries.values())

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_images": len(self._images),
                "total_rules": len(self._rules),
                "total_replications": len(self._replication_jobs),
                "configured_registries": len(self._registries),
                "cached_images": len(self._pull_through_cache)}

    def register_registry(self, provider: RegistryProvider, endpoint: str,
                           credentials: Optional[Dict[str, str]] = None) -> ContainerRegistry:
        registry = ContainerRegistry(provider, endpoint, credentials or {})
        self._registries[provider.value] = registry
        return registry

    def remove_registry(self, provider: RegistryProvider) -> bool:
        if provider.value in self._registries:
            del self._registries[provider.value]
            return True
        return False

    def get_registry(self, provider: RegistryProvider) -> Optional[Dict[str, Any]]:
        reg = self._registries.get(provider.value)
        return reg.to_dict() if reg else None

    def add_image(self, name: str, tag: str = "latest",
                   registry: RegistryProvider = RegistryProvider.DOCKER_HUB,
                   size_mb: float = 100.0, os: str = "linux") -> ContainerImage:
        image = ContainerImage(name, tag, registry, size_mb, os)
        self._images[image.id] = image
        return image

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        img = self._images.get(image_id)
        return img.to_dict() if img else None

    def delete_image(self, image_id: str) -> bool:
        if image_id in self._images:
            del self._images[image_id]
            return True
        return False

    def list_images(self, registry: Optional[RegistryProvider] = None,
                     os_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self._images.values())
        if registry:
            results = [i for i in results if i.registry == registry]
        if os_filter:
            results = [i for i in results if i.os == os_filter]
        return [i.to_dict() for i in results]

    def create_replication_rule(self, name: str, source_registry: RegistryProvider,
                                 target_registries: List[RegistryProvider],
                                 image_filter: Optional[str] = None) -> ReplicationRule:
        rule = ReplicationRule(name, source_registry, target_registries, image_filter)
        self._rules[rule.id] = rule
        return rule

    def delete_replication_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_replication_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        rule = self._rules.get(rule_id)
        return rule.to_dict() if rule else None

    def list_replication_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._rules.values()]

    async def run_replication_rule(self, rule_id: str) -> Dict[str, Any]:
        rule = self._rules.get(rule_id)
        if not rule:
            return {"status": "error", "message": "Rule not found"}
        all_results = []
        for img in self._images.values():
            if rule.image_filter and rule.image_filter not in img.name:
                continue
            if img.registry == rule.source_registry:
                result = await self.replicate_image(img.id, rule.target_registries)
                all_results.append(result)
        return {"rule_id": rule_id, "rule_name": rule.name,
                "replications_executed": len(all_results),
                "results": all_results}

    def get_replication_jobs(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        if state:
            return [j for j in self._replication_jobs if j.get("state") == state]
        return self._replication_jobs

    def cache_image(self, image_key: str, registry: RegistryProvider,
                     data: Dict[str, Any]) -> None:
        self.set_pull_through_cache(image_key, registry, data)

    def clear_image_vulnerabilities(self) -> int:
        count = 0
        for img in self._images.values():
            if img.vulnerability_count > 0:
                img.vulnerability_count = 0
                img.max_severity = ScanSeverity.NONE
                count += 1
        return count

    def export_registry_state(self) -> Dict[str, Any]:
        return {"registries": [r.to_dict() for r in self._registries.values()],
                "images": [i.to_dict() for i in self._images.values()],
                "rules": [r.to_dict() for r in self._rules.values()],
                "replication_jobs": self._replication_jobs,
                "cached_images": list(self._pull_through_cache.values()),
                "exported_at": datetime.utcnow().isoformat()}

    def get_vulnerability_summary(self) -> Dict[str, Any]:
        total = sum(1 for i in self._images.values() if i.vulnerability_count > 0)
        critical = sum(1 for i in self._images.values()
                       if i.max_severity == ScanSeverity.CRITICAL)
        high = sum(1 for i in self._images.values()
                   if i.max_severity == ScanSeverity.HIGH)
        return {"total_images_scanned": len(self._images),
                "images_with_vulns": total,
                "critical": critical, "high": high,
                "medium": sum(1 for i in self._images.values()
                              if i.max_severity == ScanSeverity.MEDIUM),
                "low": sum(1 for i in self._images.values()
                           if i.max_severity == ScanSeverity.LOW)}

    def get_replication_stats(self) -> Dict[str, Any]:
        completed = sum(1 for j in self._replication_jobs if j.get("state") == "completed")
        failed = sum(1 for j in self._replication_jobs if j.get("state") == "failed")
        return {"total_jobs": len(self._replication_jobs), "completed": completed,
                "failed": failed, "success_rate": round(completed / max(len(self._replication_jobs), 1) * 100, 1)}

    def set_pull_through_cache_ttl(self, ttl_hours: int) -> None:
        self.cache_ttl_hours = ttl_hours

    def batch_register_images(self, images: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for img_data in images:
            img = self.register_image(img_data.get("name", "unknown"), img_data.get("tag", "latest"),
                                       img_data.get("digest", ""), RegistryProvider(img_data.get("registry", "docker_hub")),
                                       img_data.get("repository", ""), img_data.get("size_bytes", 0))
            ids.append(img.id)
        return ids

    def get_images_by_severity(self, severity: ScanSeverity) -> List[Dict[str, Any]]:
        return [i.to_dict() for i in self._images.values() if i.max_severity == severity]

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field
from typing import Set

@dataclass
class RegistrySyncJob:
    job_id: str
    source_registry: RegistryProvider
    target_registry: RegistryProvider
    image_count: int
    total_bytes: int
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ImageLayer:
    digest: str
    size_bytes: int
    media_type: str = "application/vnd.docker.image.rootfs.diff.tar.gzip"

@dataclass
class RegistryQuota:
    provider: RegistryProvider
    used_bytes: int
    limit_bytes: int
    image_count: int

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_replicate_images(self, image_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for iid in image_ids:
            r = await self.replicate_image(iid)
            results[iid] = r
        return {"results": results, "total": len(image_ids)}

    async def batch_scan_images(self, image_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for iid in image_ids:
            r = self.scan_image_vulnerabilities(iid)
            results[iid] = r
        return {"results": results, "total": len(image_ids)}

    async def batch_apply_retention(self, max_images_per_repo: int = 10) -> Dict[str, Any]:
        repo_groups: Dict[str, List[ContainerImage]] = {}
        for img in self._images.values():
            key = f"{img.registry.value}/{img.repository}"
            if key not in repo_groups:
                repo_groups[key] = []
            repo_groups[key].append(img)
        removed = 0
        for repo, imgs in repo_groups.items():
            imgs.sort(key=lambda i: i.created_at, reverse=True)
            for old in imgs[max_images_per_repo:]:
                del self._images[old.id]
                removed += 1
        return {"repositories_processed": len(repo_groups), "images_removed": removed}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_images(self, page: int = 1, page_size: int = 20,
                         sort_by: str = "created_at", sort_desc: bool = True,
                         registry_filter: Optional[str] = None,
                         severity_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._images.values())
        if registry_filter:
            items = [i for i in items if i.registry.value == registry_filter]
        if severity_filter:
            items = [i for i in items if i.max_severity.value == severity_filter]
        items.sort(key=lambda i: getattr(i, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [i.to_dict() for i in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_replication_jobs(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = sorted(self._replication_jobs, key=lambda j: j.get("started_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_images_to_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "tag", "registry", "repository", "size_bytes", "vulnerability_count", "max_severity"])
        for img in self._images.values():
            writer.writerow([img.id, img.name, img.tag, img.registry.value, img.repository, img.size_bytes, img.vulnerability_count, img.max_severity.value])
        return output.getvalue()

    def import_images_from_csv(self, csv_content: str) -> int:
        import csv, io
        reader = csv.DictReader(io.StringIO(csv_content))
        count = 0
        for row in reader:
            try:
                img = ContainerImage(row["name"], row.get("tag", "latest"), row.get("digest", ""),
                                     RegistryProvider(row.get("registry", "docker_hub")),
                                     row.get("repository", ""), int(row.get("size_bytes", 0)))
                self._images[img.id] = img
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_registry_cost_analysis(self) -> Dict[str, Any]:
        storage_cost_per_gb = {"aws_ecr": 0.10, "azure_acr": 0.12, "gcp_gcr": 0.08, "docker_hub": 0.05}
        total_cost = 0.0
        by_registry: Dict[str, float] = {}
        for img in self._images.values():
            cost_per_gb = storage_cost_per_gb.get(img.registry.value, 0.10)
            cost = (img.size_bytes / (1024**3)) * cost_per_gb
            by_registry[img.registry.value] = by_registry.get(img.registry.value, 0) + cost
            total_cost += cost
        return {"total_monthly_cost": round(total_cost, 2),
                "by_registry": {k: round(v, 2) for k, v in by_registry.items()},
                "total_images": len(self._images)}

    def get_scan_coverage_analysis(self) -> Dict[str, Any]:
        scanned = sum(1 for i in self._images.values() if i.vulnerability_count > 0)
        return {
            "total_images": len(self._images),
            "scanned": scanned,
            "unscanned": len(self._images) - scanned,
            "coverage_pct": round(scanned / max(len(self._images), 1) * 100, 1),
            "critical_images": sum(1 for i in self._images.values() if i.max_severity == ScanSeverity.CRITICAL),
        }

    def get_storage_savings_analysis(self) -> Dict[str, Any]:
        total_bytes = sum(i.size_bytes for i in self._images.values())
        unreplicated = sum(i.size_bytes for i in self._images.values() if not any(j.get("image_id") == i.id for j in self._replication_jobs))
        return {"total_bytes": total_bytes, "total_gb": round(total_bytes / (1024**3), 2),
                "unreplicated_bytes": unreplicated,
                "potential_savings_gb": round(unreplicated / (1024**3), 2),
                "dedup_ratio": round(total_bytes / max(unreplicated, 1), 2)}

# ── State Machine / Workflow ─────────────────────────────────────────

    async def image_lifecycle_workflow(self, image_id: str, action: str) -> Dict[str, Any]:
        img = self._images.get(image_id)
        if not img:
            return {"status": "error", "message": "Image not found"}
        if action == "replicate_all":
            targets = [r for r in RegistryProvider if r != img.registry]
            return await self.replicate_image(image_id, targets)
        elif action == "scan":
            return self.scan_image_vulnerabilities(image_id)
        elif action == "delete":
            self.delete_image(image_id)
            return {"status": "deleted", "image_id": image_id}
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_cleanup_workflow(self, max_age_days: int = 90) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        removed = 0
        for iid, img in list(self._images.items()):
            if img.created_at < cutoff:
                del self._images[iid]
                removed += 1
        return {"images_removed": removed, "max_age_days": max_age_days}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_replication_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.max_concurrent_replications < 1:
            errors.append("max_concurrent_replications must be >= 1")
        if self.cache_ttl_hours < 1:
            warnings.append("cache_ttl_hours is very low")
        if not any(r.get("configured") for r in self._registries.values()):
            warnings.append("No registries are configured")
        if self.scan_on_replicate and not self.config.get("scanner_endpoint"):
            warnings.append("scan_on_replicate enabled but no scanner_endpoint configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def create_registry_alert(self, name: str, threshold_pct: int, metric: str = "vulnerability_count") -> Dict[str, Any]:
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        alert = {"id": alert_id, "name": name, "metric": metric, "threshold_pct": threshold_pct, "active": True, "created_at": datetime.utcnow().isoformat()}
        if "alerts" not in self.config: self.config["alerts"] = []
        self.config["alerts"].append(alert)
        return alert

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
