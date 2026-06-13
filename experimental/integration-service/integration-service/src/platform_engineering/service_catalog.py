"""Service Catalog & Scoring — Register all services with metadata and auto-score."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ServiceTier(str, Enum):
    TIER_1 = "t1"
    TIER_2 = "t2"
    TIER_3 = "t3"
    TIER_4 = "t4"
    TIER_5 = "t5"


class ServiceStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    IN_DEVELOPMENT = "in_development"


SCORING_WEIGHTS = {
    "has_documentation": 15,
    "has_tests": 15,
    "has_monitoring": 15,
    "has_on_call": 10,
    "has_sla": 10,
    "has_backup": 10,
    "has_disaster_recovery": 10,
    "has_security_scanning": 10,
    "has_dependency_tracking": 5,
    "has_api_spec": 10,
    "has_owner": 10,
    "has_lifecycle": 5,
    "has_cost_allocation": 5,
    "has_health_check": 10,
    "has_versioning": 5,
}


class ServiceEntry:
    def __init__(self, service_id: str, name: str, owner: str, language: str, tier: ServiceTier):
        self.service_id = service_id
        self.name = name
        self.owner = owner
        self.language = language
        self.tier = tier
        self.status: ServiceStatus = ServiceStatus.ACTIVE
        self.description: str = ""
        self.team: str = ""
        self.sla_target: float = 99.9
        self.repository_url: str = ""
        self.documentation_url: str = ""
        self.api_spec_url: str = ""
        self.health_check_url: str = ""
        self.monitoring_dashboard: str = ""
        self.on_call_channel: str = ""
        self.tags: list[str] = []
        self.dependencies: list[str] = []
        self.production_readiness_score: float = 0.0
        self.last_score_update: Optional[datetime] = None
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.metadata: dict[str, Any] = {
            "has_documentation": False,
            "has_tests": False,
            "has_monitoring": False,
            "has_on_call": False,
            "has_sla": False,
            "has_backup": False,
            "has_disaster_recovery": False,
            "has_security_scanning": False,
            "has_dependency_tracking": False,
            "has_api_spec": False,
            "has_owner": True,
            "has_lifecycle": False,
            "has_cost_allocation": False,
            "has_health_check": False,
            "has_versioning": False,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "owner": self.owner,
            "language": self.language,
            "tier": self.tier.value,
            "status": self.status.value,
            "description": self.description,
            "team": self.team,
            "sla_target": self.sla_target,
            "repository_url": self.repository_url,
            "documentation_url": self.documentation_url,
            "api_spec_url": self.api_spec_url,
            "health_check_url": self.health_check_url,
            "monitoring_dashboard": self.monitoring_dashboard,
            "on_call_channel": self.on_call_channel,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "production_readiness_score": self.production_readiness_score,
            "last_score_update": self.last_score_update.isoformat() if self.last_score_update else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceEntry":
        se = cls(
            data["service_id"],
            data["name"],
            data["owner"],
            data["language"],
            ServiceTier(data.get("tier", "t3")),
        )
        se.status = ServiceStatus(data.get("status", "active"))
        se.description = data.get("description", "")
        se.team = data.get("team", "")
        se.sla_target = data.get("sla_target", 99.9)
        se.repository_url = data.get("repository_url", "")
        se.documentation_url = data.get("documentation_url", "")
        se.api_spec_url = data.get("api_spec_url", "")
        se.health_check_url = data.get("health_check_url", "")
        se.monitoring_dashboard = data.get("monitoring_dashboard", "")
        se.on_call_channel = data.get("on_call_channel", "")
        se.tags = data.get("tags", [])
        se.dependencies = data.get("dependencies", [])
        se.production_readiness_score = data.get("production_readiness_score", 0.0)
        if data.get("last_score_update"):
            se.last_score_update = datetime.fromisoformat(data["last_score_update"])
        if data.get("created_at"):
            se.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            se.updated_at = datetime.fromisoformat(data["updated_at"])
        se.metadata = data.get("metadata", {})
        return se


class ServiceCatalogManager:
    def __init__(self):
        self.services: dict[str, ServiceEntry] = {}
        self.categories: dict[str, dict[str, Any]] = {}

    def register_service(self, name: str, owner: str, language: str, tier: ServiceTier = ServiceTier.TIER_3) -> ServiceEntry:
        sid = str(uuid.uuid4())
        service = ServiceEntry(sid, name, owner, language, tier)
        self.services[sid] = service
        self._calculate_score(sid)
        logger.info("Registered service %s (%s) owned by %s", name, language, owner)
        return service

    def get_service(self, service_id: str) -> Optional[ServiceEntry]:
        return self.services.get(service_id)

    def update_service(self, service_id: str, updates: dict[str, Any]) -> Optional[ServiceEntry]:
        svc = self.services.get(service_id)
        if not svc:
            return None
        for key, value in updates.items():
            if key == "tier" and isinstance(value, str):
                setattr(svc, key, ServiceTier(value))
            elif key == "status" and isinstance(value, str):
                setattr(svc, key, ServiceStatus(value))
            elif key == "metadata" and isinstance(value, dict):
                svc.metadata.update(value)
            elif hasattr(svc, key):
                setattr(svc, key, value)
        svc.updated_at = datetime.utcnow()
        self._calculate_score(service_id)
        return svc

    def delete_service(self, service_id: str) -> bool:
        if service_id in self.services:
            del self.services[service_id]
            return True
        return False

    def list_services(self, owner: str = "", tier: str = "", status: str = "", language: str = "") -> list[ServiceEntry]:
        results = list(self.services.values())
        if owner:
            results = [s for s in results if s.owner == owner]
        if tier:
            results = [s for s in results if s.tier.value == tier]
        if status:
            results = [s for s in results if s.status.value == status]
        if language:
            results = [s for s in results if s.language == language]
        return sorted(results, key=lambda s: s.production_readiness_score, reverse=True)

    def _calculate_score(self, service_id: str):
        svc = self.services.get(service_id)
        if not svc:
            return
        score = 0.0
        max_score = sum(SCORING_WEIGHTS.values())
        for check, weight in SCORING_WEIGHTS.items():
            if svc.metadata.get(check, False):
                score += weight
        if svc.documentation_url:
            score += SCORING_WEIGHTS.get("has_documentation", 0)
        if svc.api_spec_url:
            score += SCORING_WEIGHTS.get("has_api_spec", 0)
        if svc.monitoring_dashboard:
            score += SCORING_WEIGHTS.get("has_monitoring", 0)
        svc.production_readiness_score = round((score / max_score) * 100, 1)
        svc.last_score_update = datetime.utcnow()

    def score_all_services(self):
        for sid in self.services:
            self._calculate_score(sid)

    def get_catalog_summary(self) -> dict[str, Any]:
        total = len(self.services)
        if total == 0:
            return {"total_services": 0}
        by_tier: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_language: dict[str, int] = {}
        by_owner: dict[str, int] = {}
        scores = []
        for svc in self.services.values():
            by_tier[svc.tier.value] = by_tier.get(svc.tier.value, 0) + 1
            by_status[svc.status.value] = by_status.get(svc.status.value, 0) + 1
            by_language[svc.language] = by_language.get(svc.language, 0) + 1
            by_owner[svc.owner] = by_owner.get(svc.owner, 0) + 1
            scores.append(svc.production_readiness_score)
        avg_score = round(sum(scores) / total, 1) if scores else 0
        return {
            "total_services": total,
            "average_score": avg_score,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "by_tier": by_tier,
            "by_status": by_status,
            "by_language": by_language,
            "by_owner": by_owner,
            "services_below_threshold": len([s for s in scores if s < 50]),
        }

    def create_category(self, name: str, description: str, parent: str = "") -> dict[str, Any]:
        cid = str(uuid.uuid4())
        category = {
            "category_id": cid,
            "name": name,
            "description": description,
            "parent": parent,
            "service_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.categories[cid] = category
        return category

    def categorize_service(self, service_id: str, category_id: str) -> bool:
        if service_id in self.services and category_id in self.categories:
            svc = self.services[service_id]
            if "categories" not in svc.metadata:
                svc.metadata["categories"] = []
            if category_id not in svc.metadata["categories"]:
                svc.metadata["categories"].append(category_id)
                self.categories[category_id]["service_count"] += 1
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "services": {sid: s.to_dict() for sid, s in self.services.items()},
            "categories": self.categories,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceCatalogManager":
        mgr = cls()
        for sid, sdata in data.get("services", {}).items():
            mgr.services[sid] = ServiceEntry.from_dict(sdata)
        mgr.categories = data.get("categories", {})
        return mgr

    def bulk_register_services(self, services_data: list[dict[str, Any]]) -> list[str]:
        ids = []
        for sd in services_data:
            svc = self.register_service(
                sd["name"], sd["owner"], sd.get("language", "unknown"),
                ServiceTier(sd.get("tier", "t3")),
            )
            if sd.get("description"):
                svc.description = sd["description"]
            if sd.get("tags"):
                svc.tags = sd["tags"]
            if sd.get("repository_url"):
                svc.repository_url = sd["repository_url"]
            if sd.get("metadata"):
                svc.metadata.update(sd["metadata"])
            ids.append(svc.service_id)
        return ids

    def check_service_health(self, service_id: str) -> dict[str, Any]:
        svc = self.services.get(service_id)
        if not svc:
            return {"error": "Service not found"}
        checks = {
            "has_owner": bool(svc.owner),
            "has_documentation": bool(svc.documentation_url),
            "has_repository": bool(svc.repository_url),
            "has_monitoring": bool(svc.monitoring_dashboard),
            "has_on_call": bool(svc.on_call_channel),
            "has_api_spec": bool(svc.api_spec_url),
            "has_health_check": bool(svc.health_check_url),
            "has_sla": svc.sla_target > 0,
        }
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        return {
            "service_id": service_id,
            "name": svc.name,
            "health_score": round(passed / total * 100, 1),
            "checks": checks,
            "passed_checks": passed,
            "total_checks": total,
        }

    def get_services_by_owner(self, owner: str) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.owner == owner]

    def send_notifications(self, service_id: str, message: str, channel: str = "slack") -> bool:
        svc = self.services.get(service_id)
        if not svc:
            return False
        logger.info("Notification sent for %s via %s: %s", svc.name, channel, message)
        if "notifications" not in svc.metadata:
            svc.metadata["notifications"] = []
        svc.metadata["notifications"].append({
            "channel": channel,
            "message": message,
            "sent_at": datetime.utcnow().isoformat(),
        })
        return True

    def search_services(self, query: str) -> list[ServiceEntry]:
        q = query.lower()
        return [s for s in self.services.values()
                if q in s.name.lower() or q in s.description.lower() or q in s.owner.lower()
                or any(q in tag.lower() for tag in s.tags)]

    def get_catalog_analytics(self) -> dict[str, Any]:
        total = len(self.services)
        if total == 0:
            return {"total_services": 0}
        owners = len(set(s.owner for s in self.services.values()))
        languages = len(set(s.language for s in self.services.values()))
        avg_score = round(sum(s.production_readiness_score for s in self.services.values()) / total, 1)
        return {
            "total_services": total,
            "unique_owners": owners,
            "unique_languages": languages,
            "avg_readiness_score": avg_score,
            "services_above_80": len([s for s in self.services.values() if s.production_readiness_score >= 80]),
            "services_below_50": len([s for s in self.services.values() if s.production_readiness_score < 50]),
            "tier_distribution": {
                tier: len([s for s in self.services.values() if s.tier.value == tier])
                for tier in ["t1", "t2", "t3", "t4", "t5"]
            },
        }

    def export_catalog(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.services.values()]

    def get_services_by_tier(self, tier: ServiceTier) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.tier == tier]

    def get_services_by_language(self, language: str) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.language == language]

    def get_category_services(self, category_id: str) -> list[ServiceEntry]:
        return [s for s in self.services.values()
                if category_id in s.metadata.get("categories", [])]

    def bulk_update_scores(self) -> int:
        count = 0
        for sid in self.services:
            self._calculate_score(sid)
            count += 1
        return count

    def delete_category(self, category_id: str) -> bool:
        if category_id in self.categories:
            del self.categories[category_id]
            return True
        return False

    def run_compliance_check(self, service_id: str) -> dict[str, Any]:
        svc = self.services.get(service_id)
        if not svc:
            return {"error": "Service not found"}
        checks = {
            "has_owner": bool(svc.owner),
            "has_repo": bool(svc.repository),
            "has_description": bool(svc.description),
            "has_language": bool(svc.language),
            "has_tier": svc.tier is not None,
            "has_sla": "sla_hours" in svc.metadata,
        }
        passed = sum(1 for v in checks.values() if v)
        return {"service_id": service_id, "name": svc.name,
                "compliance_score": round(passed / len(checks) * 100, 1),
                "checks": checks, "passed": passed, "total": len(checks)}

    def bulk_compliance_check(self) -> list[dict[str, Any]]:
        return [self.run_compliance_check(sid) for sid in self.services]

    def add_cost_data(self, service_id: str, monthly_cost: float, currency: str = "USD") -> bool:
        svc = self.services.get(service_id)
        if not svc:
            return False
        svc.metadata["monthly_cost"] = monthly_cost
        svc.metadata["cost_currency"] = currency
        svc.updated_at = datetime.utcnow()
        return True

    def get_cost_summary(self) -> dict[str, Any]:
        total = 0.0
        by_tier: dict[str, float] = {}
        for svc in self.services.values():
            cost = svc.metadata.get("monthly_cost", 0)
            total += cost
            tier_key = svc.tier.value if svc.tier else "unknown"
            by_tier[tier_key] = by_tier.get(tier_key, 0) + cost
        return {"total_monthly_cost": round(total, 2), "by_tier": by_tier,
                "service_count": len(self.services)}

    def build_dependency_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for sid, svc in self.services.items():
            deps = svc.metadata.get("dependencies", [])
            graph[sid] = deps
        return graph

    def get_dependency_chain(self, service_id: str, max_depth: int = 5) -> list[str]:
        chain = []
        visited = set()
        graph = self.build_dependency_graph()

        def traverse(sid: str, depth: int) -> None:
            if sid in visited or depth > max_depth:
                return
            visited.add(sid)
            chain.append(sid)
            for dep in graph.get(sid, []):
                if dep in self.services:
                    traverse(dep, depth + 1)

        traverse(service_id, 0)
        return chain

    def find_orphan_services(self) -> list[dict[str, Any]]:
        all_deps: set[str] = set()
        for svc in self.services.values():
            for dep in svc.metadata.get("dependencies", []):
                all_deps.add(dep)
        orphans = [{"service_id": sid, "name": svc.name}
                    for sid, svc in self.services.items() if sid not in all_deps]
        return orphans

    def add_service_metadata(self, service_id: str, key: str, value: Any) -> bool:
        svc = self.services.get(service_id)
        if not svc:
            return False
        svc.metadata[key] = value
        svc.updated_at = datetime.utcnow()
        return True

    def get_services_by_owner(self, owner: str) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.owner == owner]

    def bulk_set_tier(self, service_ids: list[str], tier: ServiceTier) -> int:
        count = 0
        for sid in service_ids:
            svc = self.services.get(sid)
            if svc:
                svc.tier = tier
                svc.updated_at = datetime.utcnow()
                count += 1
        return count

    def get_category_hierarchy(self) -> dict[str, Any]:
        hierarchy: dict[str, list[dict[str, Any]]] = {}
        for cid, cat in self.categories.items():
            children = [{"service_id": sid, "name": svc.name}
                        for sid, svc in self.services.items()
                        if cat.name in svc.metadata.get("categories", [])]
            hierarchy[cid] = {"name": cat.name, "description": cat.description, "children": children}
        return hierarchy

    def search_services_by_metadata(self, key: str, value: Any) -> list[ServiceEntry]:
        return [s for s in self.services.values() if s.metadata.get(key) == value]

    def get_duplicate_services(self) -> list[dict[str, Any]]:
        seen: dict[str, list[str]] = {}
        for sid, svc in self.services.items():
            key = f"{svc.name}:{svc.language}"
            if key not in seen:
                seen[key] = []
            seen[key].append(sid)
        return [{"name": name, "service_ids": ids, "count": len(ids)}
                for name, ids in seen.items() if len(ids) > 1]

    def compute_maturity_score(self, service_id: str) -> dict[str, Any]:
        svc = self.services.get(service_id)
        if not svc:
            return {"error": "Service not found"}
        score = 0
        if svc.owner:
            score += 20
        if svc.repository:
            score += 20
        if svc.description:
            score += 15
        if svc.language:
            score += 10
        if svc.tier:
            score += 15
        if svc.metadata.get("sla_hours"):
            score += 10
        if svc.metadata.get("monthly_cost"):
            score += 10
        return {"service_id": service_id, "name": svc.name,
                "maturity_score": score, "max_score": 100,
                "level": "bronze" if score < 40 else "silver" if score < 70 else "gold" if score < 90 else "platinum"}

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
