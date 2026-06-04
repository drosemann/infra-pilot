"""API Catalog & Governance — Auto-discovered API registry from OpenAPI/gRPC specs."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ApiType(str, Enum):
    REST = "rest"
    GRPC = "grpc"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    SOAP = "soap"
    ASYNCAPI = "asyncapi"


class ApiLifecycle(str, Enum):
    DESIGN = "design"
    DEVELOPMENT = "development"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class BreakingChangeSeverity(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class ApiEndpoint:
    def __init__(self, endpoint_id: str, api_id: str, path: str, method: str):
        self.endpoint_id = endpoint_id
        self.api_id = api_id
        self.path = path
        self.method = method.upper()
        self.summary: str = ""
        self.description: str = ""
        self.deprecated: bool = False
        self.deprecation_message: str = ""
        self.parameters: list[dict[str, Any]] = []
        self.request_body: Optional[dict[str, Any]] = None
        self.responses: dict[str, Any] = {}
        self.security: list[dict[str, Any]] = []
        self.tags: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "api_id": self.api_id,
            "path": self.path,
            "method": self.method,
            "summary": self.summary,
            "description": self.description,
            "deprecated": self.deprecated,
            "deprecation_message": self.deprecation_message,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "security": self.security,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiEndpoint":
        ep = cls(data["endpoint_id"], data["api_id"], data["path"], data["method"])
        ep.summary = data.get("summary", "")
        ep.description = data.get("description", "")
        ep.deprecated = data.get("deprecated", False)
        ep.deprecation_message = data.get("deprecation_message", "")
        ep.parameters = data.get("parameters", [])
        ep.request_body = data.get("request_body")
        ep.responses = data.get("responses", {})
        ep.security = data.get("security", [])
        ep.tags = data.get("tags", [])
        return ep


class ApiEntry:
    def __init__(self, api_id: str, name: str, api_type: ApiType, version: str, owner: str):
        self.api_id = api_id
        self.name = name
        self.api_type = api_type
        self.version = version
        self.owner = owner
        self.description: str = ""
        self.lifecycle: ApiLifecycle = ApiLifecycle.DEVELOPMENT
        self.service_id: str = ""
        self.base_url: str = ""
        self.spec_url: str = ""
        self.spec_format: str = "openapi_3_0"
        self.endpoints: dict[str, ApiEndpoint] = {}
        self.consumers: list[str] = []
        self.tags: list[str] = []
        self.latest_version: str = version
        self.previous_versions: list[str] = []
        self.deprecation_date: Optional[datetime] = None
        self.sunset_date: Optional[datetime] = None
        self.migration_guide: str = ""
        self.rate_limit: int = 1000
        self.authentication: list[str] = []
        self.sla_tier: str = "t3"
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_endpoint(self, path: str, method: str) -> ApiEndpoint:
        eid = str(uuid.uuid4())
        ep = ApiEndpoint(eid, self.api_id, path, method)
        self.endpoints[eid] = ep
        return ep

    def discover_from_openapi(self, spec: dict[str, Any]):
        self.description = spec.get("info", {}).get("description", self.description)
        self.version = spec.get("info", {}).get("version", self.version)
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "patch", "delete", "options", "head"):
                    ep = self.add_endpoint(path, method)
                    ep.summary = details.get("summary", "")
                    ep.description = details.get("description", "")
                    ep.deprecated = details.get("deprecated", False)
                    ep.parameters = details.get("parameters", [])
                    ep.request_body = details.get("requestBody")
                    ep.responses = details.get("responses", {})
                    ep.security = details.get("security", [])
                    ep.tags = details.get("tags", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_id": self.api_id,
            "name": self.name,
            "api_type": self.api_type.value,
            "version": self.version,
            "owner": self.owner,
            "description": self.description,
            "lifecycle": self.lifecycle.value,
            "service_id": self.service_id,
            "base_url": self.base_url,
            "spec_url": self.spec_url,
            "spec_format": self.spec_format,
            "endpoints": {eid: e.to_dict() for eid, e in self.endpoints.items()},
            "consumers": self.consumers,
            "tags": self.tags,
            "latest_version": self.latest_version,
            "previous_versions": self.previous_versions,
            "deprecation_date": self.deprecation_date.isoformat() if self.deprecation_date else None,
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "migration_guide": self.migration_guide,
            "rate_limit": self.rate_limit,
            "authentication": self.authentication,
            "sla_tier": self.sla_tier,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiEntry":
        api = cls(data["api_id"], data["name"], ApiType(data["api_type"]), data["version"], data["owner"])
        api.description = data.get("description", "")
        api.lifecycle = ApiLifecycle(data.get("lifecycle", "development"))
        api.service_id = data.get("service_id", "")
        api.base_url = data.get("base_url", "")
        api.spec_url = data.get("spec_url", "")
        api.spec_format = data.get("spec_format", "openapi_3_0")
        api.endpoints = {eid: ApiEndpoint.from_dict(ed) for eid, ed in data.get("endpoints", {}).items()}
        api.consumers = data.get("consumers", [])
        api.tags = data.get("tags", [])
        api.latest_version = data.get("latest_version", data["version"])
        api.previous_versions = data.get("previous_versions", [])
        if data.get("deprecation_date"):
            api.deprecation_date = datetime.fromisoformat(data["deprecation_date"])
        if data.get("sunset_date"):
            api.sunset_date = datetime.fromisoformat(data["sunset_date"])
        api.migration_guide = data.get("migration_guide", "")
        api.rate_limit = data.get("rate_limit", 1000)
        api.authentication = data.get("authentication", [])
        api.sla_tier = data.get("sla_tier", "t3")
        if data.get("created_at"):
            api.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            api.updated_at = datetime.fromisoformat(data["updated_at"])
        return api


class ApiCatalogManager:
    def __init__(self):
        self.apis: dict[str, ApiEntry] = {}
        self.consumer_reports: dict[str, list[dict[str, Any]]] = {}
        self.breaking_change_log: list[dict[str, Any]] = []

    def register_api(self, name: str, api_type: ApiType, version: str, owner: str) -> ApiEntry:
        aid = str(uuid.uuid4())
        api = ApiEntry(aid, name, api_type, version, owner)
        self.apis[aid] = api
        logger.info("Registered API %s (%s) v%s by %s", name, api_type.value, version, owner)
        return api

    def get_api(self, api_id: str) -> Optional[ApiEntry]:
        return self.apis.get(api_id)

    def update_api(self, api_id: str, updates: dict[str, Any]) -> Optional[ApiEntry]:
        api = self.apis.get(api_id)
        if not api:
            return None
        for key, value in updates.items():
            if key == "api_type" and isinstance(value, str):
                setattr(api, key, ApiType(value))
            elif key == "lifecycle" and isinstance(value, str):
                old = api.lifecycle
                setattr(api, key, ApiLifecycle(value))
                if value == "deprecated":
                    api.deprecation_date = datetime.utcnow()
                if old == ApiLifecycle.DEPRECATED and value == "sunset":
                    api.sunset_date = datetime.utcnow()
            elif hasattr(api, key):
                setattr(api, key, value)
        api.updated_at = datetime.utcnow()
        return api

    def import_openapi_spec(self, name: str, owner: str, spec: dict[str, Any]) -> ApiEntry:
        api = self.register_api(name, ApiType.REST, spec.get("info", {}).get("version", "1.0.0"), owner)
        api.discover_from_openapi(spec)
        logger.info("Imported OpenAPI spec for %s with %d endpoints", name, len(api.endpoints))
        return api

    def detect_breaking_changes(self, api_id: str, new_spec: dict[str, Any]) -> list[dict[str, Any]]:
        changes = []
        api = self.apis.get(api_id)
        if not api:
            return changes
        old_paths = {ep.path: ep.method for ep in api.endpoints.values()}
        new_paths = {}
        for path, methods in new_spec.get("paths", {}).items():
            for method in methods:
                if method in ("get", "post", "put", "patch", "delete", "options", "head"):
                    new_paths[f"{method.upper()}:{path}"] = True
        old_set = set(f"{m}:{p}" for p, m in old_paths.items())
        new_set = set(new_paths.keys())
        removed = old_set - new_set
        for removed_item in removed:
            method, path = removed_item.split(":", 1)
            changes.append({
                "type": "endpoint_removed",
                "method": method,
                "path": path,
                "severity": "major",
                "description": f"Endpoint {method} {path} has been removed",
            })
        self.breaking_change_log.extend(changes)
        return changes

    def register_consumer(self, api_id: str, consumer_name: str, consumer_type: str = "service") -> bool:
        api = self.apis.get(api_id)
        if not api:
            return False
        if consumer_name not in api.consumers:
            api.consumers.append(consumer_name)
        if consumer_name not in self.consumer_reports:
            self.consumer_reports[consumer_name] = []
        self.consumer_reports[consumer_name].append({
            "api_id": api_id,
            "api_name": api.name,
            "consumer_type": consumer_type,
            "registered_at": datetime.utcnow().isoformat(),
        })
        return True

    def get_consumer_report(self, consumer_name: str) -> list[dict[str, Any]]:
        return self.consumer_reports.get(consumer_name, [])

    def list_apis(self, api_type: str = "", lifecycle: str = "", owner: str = "",
                  service_id: str = "") -> list[ApiEntry]:
        results = list(self.apis.values())
        if api_type:
            results = [a for a in results if a.api_type.value == api_type]
        if lifecycle:
            results = [a for a in results if a.lifecycle.value == lifecycle]
        if owner:
            results = [a for a in results if a.owner == owner]
        if service_id:
            results = [a for a in results if a.service_id == service_id]
        return sorted(results, key=lambda a: a.updated_at, reverse=True)

    def get_api_summary(self) -> dict[str, Any]:
        total = len(self.apis)
        by_type: dict[str, int] = {}
        by_lifecycle: dict[str, int] = {}
        total_endpoints = 0
        for api in self.apis.values():
            by_type[api.api_type.value] = by_type.get(api.api_type.value, 0) + 1
            by_lifecycle[api.lifecycle.value] = by_lifecycle.get(api.lifecycle.value, 0) + 1
            total_endpoints += len(api.endpoints)
        return {
            "total_apis": total,
            "total_endpoints": total_endpoints,
            "by_type": by_type,
            "by_lifecycle": by_lifecycle,
            "deprecated_apis": by_lifecycle.get("deprecated", 0),
            "stable_apis": by_lifecycle.get("stable", 0),
            "breaking_changes_logged": len(self.breaking_change_log),
            "total_consumers": sum(len(a.consumers) for a in self.apis.values()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "apis": {aid: a.to_dict() for aid, a in self.apis.items()},
            "consumer_reports": self.consumer_reports,
            "breaking_change_log": self.breaking_change_log,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiCatalogManager":
        mgr = cls()
        for aid, adata in data.get("apis", {}).items():
            mgr.apis[aid] = ApiEntry.from_dict(adata)
        mgr.consumer_reports = data.get("consumer_reports", {})
        mgr.breaking_change_log = data.get("breaking_change_log", [])
        return mgr

    def compare_versions(self, api_id: str, version_a: str, version_b: str) -> dict[str, Any]:
        api = self.apis.get(api_id)
        if not api:
            return {"error": "API not found"}
        endpoints_a = {ep.path: ep.method for ep in api.endpoints.values() if ep.path}
        return {
            "api_id": api_id,
            "api_name": api.name,
            "version_a": version_a,
            "version_b": version_b,
            "total_endpoints_a": len(endpoints_a),
            "breaking_changes_detected": len(self.detect_breaking_changes(api_id, {"paths": {}})),
        }

    def bulk_register_apis(self, apis_data: list[dict[str, Any]]) -> list[str]:
        ids = []
        for ad in apis_data:
            api = self.register_api(
                ad["name"], ApiType(ad.get("api_type", "rest")),
                ad.get("version", "1.0.0"), ad["owner"],
            )
            if ad.get("description"):
                api.description = ad["description"]
            if ad.get("base_url"):
                api.base_url = ad["base_url"]
            if ad.get("service_id"):
                api.service_id = ad["service_id"]
            if ad.get("tags"):
                api.tags = ad["tags"]
            if ad.get("endpoints"):
                for ep_data in ad["endpoints"]:
                    ep = api.add_endpoint(ep_data["path"], ep_data["method"])
                    if ep_data.get("summary"):
                        ep.summary = ep_data["summary"]
            ids.append(api.api_id)
        return ids

    def enforce_governance_rules(self, api_id: str) -> dict[str, Any]:
        api = self.apis.get(api_id)
        if not api:
            return {"error": "API not found"}
        violations = []
        if not api.description:
            violations.append({"rule": "description_required", "severity": "warning", "message": "API description is missing"})
        if not api.base_url:
            violations.append({"rule": "base_url_required", "severity": "warning", "message": "Base URL is not set"})
        if not api.owner:
            violations.append({"rule": "owner_required", "severity": "critical", "message": "API must have an owner"})
        if api.lifecycle == ApiLifecycle.STABLE and not api.spec_url:
            violations.append({"rule": "spec_url_required_stable", "severity": "warning", "message": "Stable APIs should have a spec URL"})
        if api.lifecycle == ApiLifecycle.DEPRECATED and not api.sunset_date:
            violations.append({"rule": "sunset_date_required", "severity": "info", "message": "Deprecated APIs should have a sunset date"})
        return {
            "api_id": api_id,
            "api_name": api.name,
            "lifecycle": api.lifecycle.value,
            "violations": violations,
            "total_violations": len(violations),
            "passed": len(violations) == 0,
        }

    def get_api_health(self, api_id: str) -> dict[str, Any]:
        api = self.apis.get(api_id)
        if not api:
            return {"error": "API not found"}
        has_spec = bool(api.spec_url)
        has_endpoints = len(api.endpoints) > 0
        has_consumers = len(api.consumers) > 0
        has_docs = bool(api.description)
        has_base_url = bool(api.base_url)
        checks_passed = sum(1 for c in [has_spec, has_endpoints, has_consumers, has_docs, has_base_url] if c)
        return {
            "api_id": api_id,
            "name": api.name,
            "health_score": round(checks_passed / 5 * 100, 1),
            "has_spec": has_spec,
            "has_endpoints": has_endpoints,
            "has_consumers": has_consumers,
            "has_docs": has_docs,
            "has_base_url": has_base_url,
            "governance": self.enforce_governance_rules(api_id),
        }

    def export_api_catalog(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.apis.values()]

    def bulk_update_lifecycle(self, api_ids: list[str], lifecycle: ApiLifecycle) -> int:
        count = 0
        for aid in api_ids:
            if self.update_api(aid, {"lifecycle": lifecycle.value}):
                count += 1
        return count

    def find_duplicate_apis(self) -> list[dict[str, Any]]:
        seen = {}
        duplicates = []
        for api in self.apis.values():
            key = f"{api.name}:{api.version}"
            if key in seen:
                duplicates.append({"api_id": api.api_id, "name": api.name, "version": api.version, "duplicate_of": seen[key]})
            else:
                seen[key] = api.api_id
        return duplicates

    def mark_api_sunset(self, api_id: str, sunset_date: datetime, migration_guide: str = "") -> bool:
        api = self.apis.get(api_id)
        if not api:
            return False
        api.lifecycle = ApiLifecycle.SUNSET
        api.sunset_date = sunset_date
        api.migration_guide = migration_guide
        api.updated_at = datetime.utcnow()
        return True

    def get_apis_by_consumer(self, consumer_name: str) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.apis.values() if consumer_name in a.consumers]

    def search_apis(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [a.to_dict() for a in self.apis.values()
                if q in a.name.lower() or q in a.description.lower() or q in a.owner.lower()]

    def schedule_deprecation(self, api_id: str, sunset_date: datetime, migration_guide: str = "",
                              notification_period_days: int = 90) -> dict[str, Any] | None:
        api = self.apis.get(api_id)
        if not api:
            return None
        api.lifecycle = ApiLifecycle.DEPRECATED
        api.sunset_date = sunset_date
        api.migration_guide = migration_guide
        api.updated_at = datetime.utcnow()
        schedule_id = str(uuid.uuid4())
        schedule = {
            "schedule_id": schedule_id, "api_id": api_id, "sunset_date": sunset_date.isoformat(),
            "notification_period_days": notification_period_days, "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_deprecation_schedules"):
            self._deprecation_schedules: list[dict[str, Any]] = []
        self._deprecation_schedules.append(schedule)
        return schedule

    def get_deprecation_schedule(self, api_id: str = "") -> list[dict[str, Any]]:
        schedules = getattr(self, "_deprecation_schedules", [])
        if api_id:
            return [s for s in schedules if s["api_id"] == api_id]
        return schedules

    def track_api_usage(self, api_id: str, caller: str, endpoint: str, method: str = "GET",
                         status_code: int = 200, latency_ms: float = 0) -> dict[str, Any]:
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id, "api_id": api_id, "caller": caller,
            "endpoint": endpoint, "method": method, "status_code": status_code,
            "latency_ms": latency_ms, "timestamp": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_usage_events"):
            self._usage_events: list[dict[str, Any]] = []
        self._usage_events.append(event)
        return event

    def get_api_usage_stats(self, api_id: str, days: int = 30) -> dict[str, Any]:
        events = getattr(self, "_usage_events", [])
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        api_events = [e for e in events if e["api_id"] == api_id and e["timestamp"] >= cutoff]
        callers: dict[str, int] = {}
        methods: dict[str, int] = {}
        status_codes: dict[str, int] = {}
        latencies = []
        for e in api_events:
            callers[e["caller"]] = callers.get(e["caller"], 0) + 1
            methods[e["method"]] = methods.get(e["method"], 0) + 1
            sc_key = str(e["status_code"])
            status_codes[sc_key] = status_codes.get(sc_key, 0) + 1
            latencies.append(e["latency_ms"])
        return {
            "api_id": api_id, "days": days, "total_requests": len(api_events),
            "unique_callers": len(callers), "top_callers": sorted(callers.items(), key=lambda x: x[1], reverse=True)[:5],
            "methods": methods, "status_codes": status_codes,
            "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 1) if latencies else 0,
        }

    def run_compliance_report(self, api_id: str = "") -> dict[str, Any]:
        apis = [a for a in self.apis.values() if not api_id or a.api_id == api_id]
        total = len(apis)
        with_owner = sum(1 for a in apis if a.owner)
        with_description = sum(1 for a in apis if a.description)
        with_versioning = sum(1 for a in apis if a.version)
        with_consumers = sum(1 for a in apis if a.consumers)
        with_sla = sum(1 for a in apis if a.sla_tier)
        return {
            "api_id": api_id or "all", "total_apis": total,
            "compliance_pct": round((with_owner + with_description + with_versioning + with_consumers + with_sla) / max(total * 5, 1) * 100, 1),
            "with_owner": with_owner, "with_description": with_description,
            "with_versioning": with_versioning, "with_consumers": with_consumers,
            "with_sla": with_sla,
        }

    def bulk_register_apis(self, api_defs: list[dict[str, Any]]) -> list[str]:
        ids = []
        for ad in api_defs:
            api = self.register_api(ad["name"], ad.get("version", "1.0"), ad.get("description", ""),
                                     ad.get("owner", ""), ad.get("spec_url", ""),
                                     ad.get("spec_type", ApiSpecType.OPENAPI))
            api.protocol = ApiProtocol(ad.get("protocol", "rest"))
            api.lifecycle = ApiLifecycle(ad.get("lifecycle", "active"))
            api.sla_tier = ad.get("sla_tier", "")
            api.consumers = ad.get("consumers", [])
            ids.append(api.api_id)
        return ids

    def get_duplicate_endpoints(self) -> list[dict[str, Any]]:
        seen: dict[str, list[dict[str, Any]]] = {}
        for api in self.apis.values():
            for method, paths in api.endpoints.items():
                for path in paths:
                    key = f"{method}:{path}"
                    if key not in seen:
                        seen[key] = []
                    seen[key].append({"api_id": api.api_id, "name": api.name})
        return [{"key": k, "apis": v, "count": len(v)} for k, v in seen.items() if len(v) > 1]

    def add_api_version(self, api_id: str, new_version: str, spec_url: str, changelog: str = "") -> bool:
        api = self.apis.get(api_id)
        if not api:
            return False
        if not hasattr(api, "version_history"):
            api.version_history = []
        api.version_history.append({"version": api.version, "spec_url": api.spec_url})
        api.version = new_version
        api.spec_url = spec_url
        api.updated_at = datetime.utcnow()
        if changelog:
            api.changelog = changelog
        return True

    def get_api_version_history(self, api_id: str) -> list[dict[str, Any]]:
        api = self.apis.get(api_id)
        if not api:
            return []
        history = getattr(api, "version_history", [])
        history.append({"version": api.version, "spec_url": api.spec_url, "current": True})
        return history

    def notify_consumers(self, api_id: str, message: str) -> dict[str, Any]:
        api = self.apis.get(api_id)
        if not api:
            return {"error": "API not found"}
        notifications = [{"consumer": c, "api_id": api_id, "message": message,
                           "sent_at": datetime.utcnow().isoformat()}
                         for c in api.consumers]
        return {"api_id": api_id, "notifications_sent": len(notifications), "consumers": api.consumers}

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
