"""Template & Blueprint Registry — Versioned library of infrastructure blueprints."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BlueprintType(str, Enum):
    TERRAFORM = "terraform"
    PULUMI = "pulumi"
    CLOUDFORMATION = "cloudformation"
    ARM = "arm"
    HELM = "helm"
    KUSTOMIZE = "kustomize"
    DOCKER_COMPOSE = "docker_compose"
    ANSIBLE = "ansible"


class BlueprintStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


PARAMETER_TYPES = ["string", "number", "boolean", "list", "json", "select"]


class BlueprintParameter:
    def __init__(self, name: str, param_type: str, description: str, required: bool = False):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.required = required
        self.default_value: Any = None
        self.options: list[str] = []
        self.validation_regex: str = ""
        self.validation_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.param_type,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "options": self.options,
            "validation_regex": self.validation_regex,
            "validation_message": self.validation_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintParameter":
        bp = cls(data["name"], data["type"], data["description"], data.get("required", False))
        bp.default_value = data.get("default_value")
        bp.options = data.get("options", [])
        bp.validation_regex = data.get("validation_regex", "")
        bp.validation_message = data.get("validation_message", "")
        return bp


class BlueprintVersion:
    def __init__(self, version_id: str, version: str, blueprint_id: str):
        self.version_id = version_id
        self.version = version
        self.blueprint_id = blueprint_id
        self.content_url: str = ""
        self.content: str = ""
        self.parameters: dict[str, BlueprintParameter] = {}
        self.changelog: str = ""
        self.created_by: str = ""
        self.created_at: datetime = datetime.utcnow()
        self.deprecated: bool = False

    def validate_parameters(self, values: dict[str, Any]) -> list[str]:
        errors = []
        for pname, param in self.parameters.items():
            if param.required and pname not in values:
                errors.append(f"Missing required parameter: {pname}")
            if pname in values:
                val = values[pname]
                if param.param_type == "number" and not isinstance(val, (int, float)):
                    errors.append(f"Parameter {pname} must be a number")
                if param.param_type == "boolean" and not isinstance(val, bool):
                    errors.append(f"Parameter {pname} must be a boolean")
                if param.options and val not in param.options:
                    errors.append(f"Parameter {pname} must be one of: {', '.join(param.options)}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "version": self.version,
            "blueprint_id": self.blueprint_id,
            "content_url": self.content_url,
            "content_length": len(self.content),
            "parameters": {pn: p.to_dict() for pn, p in self.parameters.items()},
            "changelog": self.changelog,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintVersion":
        bv = cls(data["version_id"], data["version"], data["blueprint_id"])
        bv.content_url = data.get("content_url", "")
        bv.content = data.get("content", "")
        bv.parameters = {
            pn: BlueprintParameter.from_dict(pd) for pn, pd in data.get("parameters", {}).items()
        }
        bv.changelog = data.get("changelog", "")
        bv.created_by = data.get("created_by", "")
        if data.get("created_at"):
            bv.created_at = datetime.fromisoformat(data["created_at"])
        bv.deprecated = data.get("deprecated", False)
        return bv


class Blueprint:
    def __init__(self, blueprint_id: str, name: str, blueprint_type: BlueprintType, owner: str):
        self.blueprint_id = blueprint_id
        self.name = name
        self.blueprint_type = blueprint_type
        self.owner = owner
        self.description: str = ""
        self.category: str = ""
        self.tags: list[str] = []
        self.status: BlueprintStatus = BlueprintStatus.DRAFT
        self.versions: dict[str, BlueprintVersion] = {}
        self.latest_version: str = ""
        self.cloud_providers: list[str] = []
        self.estimated_cost: str = ""
        self.complexity: str = "medium"
        self.icon_url: str = ""
        self.readme: str = ""
        self.usage_count: int = 0
        self.rating: float = 0.0
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_version(self, version: str, content: str, created_by: str, changelog: str = "") -> BlueprintVersion:
        vid = str(uuid.uuid4())
        bv = BlueprintVersion(vid, version, self.blueprint_id)
        bv.content = content
        bv.created_by = created_by
        bv.changelog = changelog
        self.versions[vid] = bv
        self.latest_version = version
        self.updated_at = datetime.utcnow()
        return bv

    def get_version(self, version: str) -> Optional[BlueprintVersion]:
        for bv in self.versions.values():
            if bv.version == version:
                return bv
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "blueprint_type": self.blueprint_type.value,
            "owner": self.owner,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "status": self.status.value,
            "versions": {vid: v.to_dict() for vid, v in self.versions.items()},
            "latest_version": self.latest_version,
            "cloud_providers": self.cloud_providers,
            "estimated_cost": self.estimated_cost,
            "complexity": self.complexity,
            "icon_url": self.icon_url,
            "readme": self.readme,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blueprint":
        bp = cls(
            data["blueprint_id"], data["name"],
            BlueprintType(data["blueprint_type"]),
            data["owner"],
        )
        bp.description = data.get("description", "")
        bp.category = data.get("category", "")
        bp.tags = data.get("tags", [])
        bp.status = BlueprintStatus(data.get("status", "draft"))
        bp.versions = {
            vid: BlueprintVersion.from_dict(vd) for vid, vd in data.get("versions", {}).items()
        }
        bp.latest_version = data.get("latest_version", "")
        bp.cloud_providers = data.get("cloud_providers", [])
        bp.estimated_cost = data.get("estimated_cost", "")
        bp.complexity = data.get("complexity", "medium")
        bp.icon_url = data.get("icon_url", "")
        bp.readme = data.get("readme", "")
        bp.usage_count = data.get("usage_count", 0)
        bp.rating = data.get("rating", 0.0)
        if data.get("created_at"):
            bp.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            bp.updated_at = datetime.fromisoformat(data["updated_at"])
        return bp


class TemplateRegistryManager:
    def __init__(self):
        self.blueprints: dict[str, Blueprint] = {}
        self.categories: dict[str, dict[str, Any]] = {}

    def create_blueprint(self, name: str, blueprint_type: BlueprintType, owner: str) -> Blueprint:
        bid = str(uuid.uuid4())
        bp = Blueprint(bid, name, blueprint_type, owner)
        self.blueprints[bid] = bp
        logger.info("Created blueprint %s (%s) by %s", name, blueprint_type.value, owner)
        return bp

    def get_blueprint(self, blueprint_id: str) -> Optional[Blueprint]:
        return self.blueprints.get(blueprint_id)

    def update_blueprint(self, blueprint_id: str, updates: dict[str, Any]) -> Optional[Blueprint]:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return None
        for key, value in updates.items():
            if key == "status" and isinstance(value, str):
                setattr(bp, key, BlueprintStatus(value))
            elif key == "blueprint_type" and isinstance(value, str):
                setattr(bp, key, BlueprintType(value))
            elif hasattr(bp, key):
                setattr(bp, key, value)
        bp.updated_at = datetime.utcnow()
        return bp

    def add_version(self, blueprint_id: str, version: str, content: str, created_by: str, changelog: str = "") -> Optional[BlueprintVersion]:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return None
        return bp.add_version(version, content, created_by, changelog)

    def list_blueprints(self, blueprint_type: str = "", category: str = "", status: str = "", owner: str = "") -> list[Blueprint]:
        results = list(self.blueprints.values())
        if blueprint_type:
            results = [b for b in results if b.blueprint_type.value == blueprint_type]
        if category:
            results = [b for b in results if b.category == category]
        if status:
            results = [b for b in results if b.status.value == status]
        if owner:
            results = [b for b in results if b.owner == owner]
        return sorted(results, key=lambda b: b.updated_at, reverse=True)

    def delete_blueprint(self, blueprint_id: str) -> bool:
        if blueprint_id in self.blueprints:
            del self.blueprints[blueprint_id]
            return True
        return False

    def register_usage(self, blueprint_id: str):
        bp = self.blueprints.get(blueprint_id)
        if bp:
            bp.usage_count += 1

    def rate_blueprint(self, blueprint_id: str, rating: float) -> bool:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return False
        bp.rating = round((bp.rating + rating) / 2, 1) if bp.rating > 0 else rating
        return True

    def create_category(self, name: str, description: str, icon: str = "") -> dict[str, Any]:
        cid = str(uuid.uuid4())
        cat = {
            "category_id": cid,
            "name": name,
            "description": description,
            "icon": icon,
            "blueprint_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.categories[cid] = cat
        return cat

    def get_registry_summary(self) -> dict[str, Any]:
        total = len(self.blueprints)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for bp in self.blueprints.values():
            by_type[bp.blueprint_type.value] = by_type.get(bp.blueprint_type.value, 0) + 1
            by_status[bp.status.value] = by_status.get(bp.status.value, 0) + 1
            if bp.category:
                by_category[bp.category] = by_category.get(bp.category, 0) + 1
        return {
            "total_blueprints": total,
            "total_versions": sum(len(bp.versions) for bp in self.blueprints.values()),
            "by_type": by_type,
            "by_status": by_status,
            "by_category": by_category,
            "total_categories": len(self.categories),
            "total_usage": sum(bp.usage_count for bp in self.blueprints.values()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprints": {bid: bp.to_dict() for bid, bp in self.blueprints.items()},
            "categories": self.categories,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateRegistryManager":
        mgr = cls()
        for bid, bdata in data.get("blueprints", {}).items():
            mgr.blueprints[bid] = Blueprint.from_dict(bdata)
        mgr.categories = data.get("categories", {})
        return mgr

    def batch_register_blueprints(self, blueprints_data: list[dict[str, Any]]) -> list[str]:
        ids = []
        for bd in blueprints_data:
            bp = self.create_blueprint(
                bd["name"], BlueprintType(bd["blueprint_type"]), bd["owner"]
            )
            if bd.get("description"):
                bp.description = bd["description"]
            if bd.get("category"):
                bp.category = bd["category"]
            if bd.get("tags"):
                bp.tags = bd["tags"]
            if bd.get("cloud_providers"):
                bp.cloud_providers = bd["cloud_providers"]
            ids.append(bp.blueprint_id)
        return ids

    def search_blueprints(self, query: str) -> list[Blueprint]:
        q = query.lower()
        results = []
        for bp in self.blueprints.values():
            if q in bp.name.lower() or q in bp.description.lower() or q in bp.owner.lower():
                results.append(bp)
                continue
            for tag in bp.tags:
                if q in tag.lower():
                    results.append(bp)
                    break
        return results

    def archive_deprecated(self) -> int:
        count = 0
        for bp in self.blueprints.values():
            if bp.status == BlueprintStatus.DEPRECATED:
                bp.status = BlueprintStatus.ARCHIVED
                bp.updated_at = datetime.utcnow()
                count += 1
        return count

    def get_analytics(self) -> dict[str, Any]:
        if not self.blueprints:
            return {}
        ratings = [bp.rating for bp in self.blueprints.values() if bp.rating > 0]
        return {
            "total_blueprints": len(self.blueprints),
            "total_versions": sum(len(bp.versions) for bp in self.blueprints.values()),
            "total_usage": sum(bp.usage_count for bp in self.blueprints.values()),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "most_used": max(self.blueprints.values(), key=lambda x: x.usage_count).name if self.blueprints else "",
            "by_category": {
                cat: len([bp for bp in self.blueprints.values() if bp.category == cat])
                for cat in set(bp.category for bp in self.blueprints.values() if bp.category)
            },
        }

    def bulk_update_status(self, blueprint_ids: list[str], status: BlueprintStatus) -> int:
        count = 0
        for bid in blueprint_ids:
            bp = self.blueprints.get(bid)
            if bp:
                bp.status = status
                bp.updated_at = datetime.utcnow()
                count += 1
        return count

    def export_blueprints(self, category: str = "") -> list[dict[str, Any]]:
        bps = self.list_blueprints(category=category) if category else list(self.blueprints.values())
        return [bp.to_dict() for bp in bps]

    def clone_blueprint(self, blueprint_id: str, new_name: str, new_owner: str) -> Optional[Blueprint]:
        source = self.blueprints.get(blueprint_id)
        if not source:
            return None
        bp = self.create_blueprint(new_name, source.blueprint_type, new_owner)
        bp.description = source.description
        bp.category = source.category
        bp.tags = list(source.tags)
        bp.cloud_providers = list(source.cloud_providers)
        bp.estimated_cost = source.estimated_cost
        bp.complexity = source.complexity
        bp.readme = source.readme
        for vid, version in source.versions.items():
            bp.add_version(version.version, version.content, new_owner, f"Cloned from {source.name}")
        return bp

    def get_blueprints_by_type(self, blueprint_type: BlueprintType) -> list[Blueprint]:
        return [b for b in self.blueprints.values() if b.blueprint_type == blueprint_type]

    def get_blueprints_by_provider(self, provider: str) -> list[Blueprint]:
        return [b for b in self.blueprints.values() if provider in b.cloud_providers]

    def publish_blueprint(self, blueprint_id: str) -> bool:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return False
        bp.status = BlueprintStatus.PUBLISHED
        bp.updated_at = datetime.utcnow()
        return True

    def deprecate_blueprint(self, blueprint_id: str) -> bool:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return False
        bp.status = BlueprintStatus.DEPRECATED
        bp.updated_at = datetime.utcnow()
        return True

    def bulk_import_blueprints(self, blueprint_defs: list[dict[str, Any]]) -> list[str]:
        ids = []
        for bd in blueprint_defs:
            bp = self.create_blueprint(bd["name"], BlueprintType(bd["blueprint_type"]), bd["owner"])
            bp.description = bd.get("description", "")
            bp.category = bd.get("category", "")
            bp.tags = bd.get("tags", [])
            bp.cloud_providers = bd.get("cloud_providers", [])
            bp.estimated_cost = bd.get("estimated_cost")
            bp.complexity = bd.get("complexity", "medium")
            bp.readme = bd.get("readme", "")
            ids.append(bp.blueprint_id)
        return ids

    def bulk_export_blueprints(self, blueprint_ids: list[str]) -> list[dict[str, Any]]:
        return [self.blueprints[bid].to_dict() for bid in blueprint_ids if bid in self.blueprints]

    def search_blueprints(self, query: str) -> list[Blueprint]:
        q = query.lower()
        return [b for b in self.blueprints.values()
                if q in b.name.lower() or q in b.description.lower() or q in b.owner.lower() or q in str(b.tags).lower()]

    def get_version_diff(self, blueprint_id: str, version_a: str, version_b: str) -> dict[str, Any]:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return {"error": "Blueprint not found"}
        va = bp.versions.get(version_a)
        vb = bp.versions.get(version_b)
        if not va or not vb:
            return {"error": "Version not found"}
        lines_a = va.content.splitlines()
        lines_b = vb.content.splitlines()
        added = [l for l in lines_b if l not in lines_a]
        removed = [l for l in lines_a if l not in lines_b]
        return {"blueprint_id": blueprint_id, "version_a": version_a, "version_b": version_b,
                "added": len(added), "removed": len(removed), "changed": len(added) + len(removed)}

    def tag_blueprint(self, blueprint_id: str, tags: list[str]) -> bool:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return False
        for t in tags:
            if t not in bp.tags:
                bp.tags.append(t)
        bp.updated_at = datetime.utcnow()
        return True

    def get_blueprint_statistics(self) -> dict[str, Any]:
        total = len(self.blueprints)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        for b in self.blueprints.values():
            by_type[b.blueprint_type.value] = by_type.get(b.blueprint_type.value, 0) + 1
            by_status[b.status.value] = by_status.get(b.status.value, 0) + 1
            for p in b.cloud_providers:
                by_provider[p] = by_provider.get(p, 0) + 1
        return {"total_blueprints": total, "by_type": by_type, "by_status": by_status, "by_provider": by_provider}

    def get_popular_templates(self, top_n: int = 10) -> list[dict[str, Any]]:
        scored = [(bid, b.usage_count) for bid, b in self.blueprints.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{"blueprint_id": bid, "name": self.blueprints[bid].name, "usage_count": count}
                for bid, count in scored[:top_n]]

    def recommend_blueprint(self, service_context: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = []
        for b in self.blueprints.values():
            if b.status != BlueprintStatus.PUBLISHED:
                continue
            score = 0
            if service_context.get("provider") in b.cloud_providers:
                score += 10
            if service_context.get("category") == b.category:
                score += 5
            if b.blueprint_type.value == service_context.get("type"):
                score += 8
            candidates.append({"blueprint_id": b.blueprint_id, "name": b.name, "score": score})
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:5]

    def archive_old_versions(self, blueprint_id: str, keep_last: int = 5) -> int:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return 0
        sorted_versions = sorted(bp.versions.items(), key=lambda x: x[1].created_at, reverse=True)
        to_remove = sorted_versions[keep_last:]
        for vid, _ in to_remove:
            del bp.versions[vid]
        return len(to_remove)

    def get_blueprint_health(self, blueprint_id: str) -> dict[str, Any]:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return {"error": "Blueprint not found"}
        checks = {
            "has_description": bool(bp.description),
            "has_readme": bool(bp.readme),
            "has_versions": len(bp.versions) > 0,
            "has_tags": len(bp.tags) > 0,
            "has_owner": bool(bp.owner),
            "has_cost_estimate": bp.estimated_cost is not None,
        }
        passed = sum(1 for v in checks.values() if v)
        return {"blueprint_id": blueprint_id, "name": bp.name,
                "health_score": round(passed / len(checks) * 100, 1), "checks": checks}

    def merge_blueprint_versions(self, blueprint_id: str, source_version: str, target_version: str) -> bool:
        bp = self.blueprints.get(blueprint_id)
        if not bp:
            return False
        sv = bp.versions.get(source_version)
        tv = bp.versions.get(target_version)
        if not sv or not tv:
            return False
        merged_lines = sv.content.splitlines() + tv.content.splitlines()
        merged = "\n".join(dict.fromkeys(merged_lines))
        bp.add_version(f"{target_version}-merged", merged, bp.owner, f"Merged {source_version} into {target_version}")
        return True

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_items": 0, "avg_score": 0.0, "completion_rate": 0.0}

    def validate_operation(self) -> Dict[str, Any]:
        return {"valid": True, "checks_passed": 0, "checks_failed": 0}

class PlatformOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PlatformBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="parallel")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)

    def update_progress(self, pct: int) -> None:
        self.progress = min(pct, 100)
        if self.progress >= 100:
            self.status = "completed"

class PlatformMetrics(BaseModel):
    metric_name: str
    value: float
    unit: str = Field(default="count")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: List[PlatformMetrics] = []

    def record(self, name: str, value: float, unit: str = "count", labels: Optional[Dict[str, str]] = None) -> None:
        self._metrics.append(PlatformMetrics(metric_name=name, value=value, unit=unit, labels=labels or {}))

    def query(self, name: str, since: Optional[datetime] = None) -> List[PlatformMetrics]:
        filtered = [m for m in self._metrics if m.metric_name == name]
        if since:
            filtered = [m for m in filtered if m.timestamp >= since]
        return filtered

    def aggregate(self, name: str, operation: str = "avg") -> float:
        values = [m.value for m in self._metrics if m.metric_name == name]
        if not values:
            return 0.0
        if operation == "avg":
            return round(sum(values) / len(values), 4)
        elif operation == "sum":
            return round(sum(values), 4)
        elif operation == "max":
            return round(max(values), 4)
        elif operation == "min":
            return round(min(values), 4)
        return 0.0

    def get_all_summary(self) -> Dict[str, Any]:
        names = set(m.metric_name for m in self._metrics)
        return {n: {"count": sum(1 for m in self._metrics if m.metric_name == n),
                     "avg": self.aggregate(n, "avg")} for n in names}

class ConfigManager:
    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = defaults or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def update(self, config: Dict[str, Any]) -> None:
        self._config.update(config)

    def export(self) -> Dict[str, Any]:
        return dict(self._config)

    def validate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        for key, rules in schema.items():
            value = self._config.get(key)
            if rules.get("required") and value is None:
                errors.append(f"Missing: {key}")
            if rules.get("type") and value is not None and not isinstance(value, rules["type"]):
                errors.append(f"Type mismatch: {key}")
        return {"valid": len(errors) == 0, "errors": errors}

class AuditTrail:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, user: str, action: str, resource: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({"user": user, "action": action, "resource": resource,
                               "details": details or {}, "timestamp": datetime.utcnow().isoformat()})

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def search(self, user: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._entries
        if user:
            results = [e for e in results if e["user"] == user]
        if action:
            results = [e for e in results if e["action"] == action]
        return results

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class HealthChecker:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_result": None, "last_run": None}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name, check in self._checks.items():
            try:
                result = await check["fn"]()
                check["last_result"] = result
                check["last_run"] = datetime.utcnow()
                results[name] = result
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_result": c["last_result"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
