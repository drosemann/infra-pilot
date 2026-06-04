import json
import uuid
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HETZNER = "hetzner"
    OVH = "ovh"
    DIGITALOCEAN = "digitalocean"


class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    GPU = "gpu"


class ResourceStatus(Enum):
    PROVISIONING = "provisioning"
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    FAILED = "failed"


class ProviderCredentials:
    def __init__(self, provider: CloudProvider, api_key: str, api_secret: str,
                 region: str, account_id: str):
        self.provider = provider
        self.api_key = api_key
        self.api_secret = api_secret
        self.region = region
        self.account_id = account_id
        self.validated = False

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider.value, "api_key": "***",
                "api_secret": "***", "region": self.region, "account_id": self.account_id,
                "validated": self.validated}


class ResourceProvisioningRequest:
    def __init__(self, resource_type: ResourceType, provider: CloudProvider,
                 specs: Dict[str, Any], region: str, count: int = 1,
                 tags: Optional[Dict[str, str]] = None,
                 timeout_seconds: int = 600):
        self.id = str(uuid.uuid4())
        self.resource_type = resource_type
        self.provider = provider
        self.specs = specs
        self.region = region
        self.count = count
        self.tags = tags or {}
        self.timeout_seconds = timeout_seconds
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "resource_type": self.resource_type.value,
                "provider": self.provider.value, "specs": self.specs,
                "region": self.region, "count": self.count, "tags": self.tags,
                "timeout_seconds": self.timeout_seconds,
                "created_at": self.created_at.isoformat()}


class ProviderScore:
    def __init__(self, provider: CloudProvider, cost_score: float,
                 latency_score: float, region_score: float,
                 availability_score: float, overall: float):
        self.provider = provider
        self.cost_score = cost_score
        self.latency_score = latency_score
        self.region_score = region_score
        self.availability_score = availability_score
        self.overall = overall

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider.value, "cost_score": self.cost_score,
                "latency_score": self.latency_score, "region_score": self.region_score,
                "availability_score": self.availability_score, "overall": self.overall}


class MultiCloudBroker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_region = config.get("default_region", "us-east-1")
        self.provisioning_timeout = config.get("provisioning_timeout", 600)
        self.max_resources_per_request = config.get("max_resources_per_request", 100)
        self.failover_enabled = config.get("failover_enabled", True)
        self.failover_threshold = config.get("failover_threshold", 0.7)
        self.scoring_weights = config.get("scoring_weights", {
            "cost": 0.4, "latency": 0.3, "region": 0.15, "availability": 0.15
        })
        self._credentials: Dict[str, ProviderCredentials] = {}
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._provisioning_requests: Dict[str, ResourceProvisioningRequest] = {}
        self._initialized = False

    async def initialize(self) -> None:
        for prov in CloudProvider:
            cred_config = self.config.get(prov.value, {})
            if cred_config:
                creds = ProviderCredentials(
                    prov, cred_config.get("api_key", ""),
                    cred_config.get("api_secret", ""),
                    cred_config.get("region", self.default_region),
                    cred_config.get("account_id", "")
                )
                self._credentials[prov.value] = creds
        self._initialized = True
        logger.info(f"MultiCloudBroker initialized with {len(self._credentials)} providers")

    async def close(self) -> None:
        self._credentials.clear()
        self._resources.clear()
        self._provisioning_requests.clear()
        logger.info("MultiCloudBroker closed")

    def add_credentials(self, creds: ProviderCredentials) -> None:
        self._credentials[creds.provider.value] = creds

    def get_credentials(self, provider: CloudProvider) -> Optional[ProviderCredentials]:
        return self._credentials.get(provider.value)

    def list_providers(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._credentials.values()]

    def create_provisioning_request(self, resource_type: ResourceType,
                                    provider: CloudProvider, specs: Dict[str, Any],
                                    region: str, count: int = 1,
                                    tags: Optional[Dict[str, str]] = None) -> ResourceProvisioningRequest:
        req = ResourceProvisioningRequest(resource_type, provider, specs, region, count, tags)
        self._provisioning_requests[req.id] = req
        return req

    def get_provisioning_request(self, req_id: str) -> Optional[ResourceProvisioningRequest]:
        return self._provisioning_requests.get(req_id)

    def cancel_provisioning_request(self, req_id: str) -> bool:
        if req_id in self._provisioning_requests:
            del self._provisioning_requests[req_id]
            return True
        return False

    async def provision_resources(self, req: ResourceProvisioningRequest) -> Dict[str, Any]:
        creds = self._credentials.get(req.provider.value)
        if not creds:
            raise ValueError(f"No credentials configured for {req.provider.value}")
        resource_ids = []
        for i in range(req.count):
            rid = f"{req.provider.value}-{req.resource_type.value}-{uuid.uuid4().hex[:8]}"
            resource = {
                "id": rid, "request_id": req.id, "provider": req.provider.value,
                "resource_type": req.resource_type.value, "region": req.region,
                "specs": req.specs, "status": ResourceStatus.PROVISIONING.value,
                "tags": req.tags, "created_at": datetime.utcnow().isoformat(),
                "provisioned_at": None, "cost_per_hour": self._estimate_cost(req)
            }
            self._resources[rid] = resource
            resource_ids.append(rid)
        result = {"request_id": req.id, "provider": req.provider.value,
                  "resource_ids": resource_ids, "count": req.count,
                  "status": "provisioning_started"}
        logger.info(f"Provisioning {req.count} {req.resource_type.value} on {req.provider.value}")
        return result

    def _estimate_cost(self, req: ResourceProvisioningRequest) -> float:
        base_cost = self.config.get("pricing", {}).get(req.provider.value, {}).get(
            req.resource_type.value, {}).get("base_cost_per_hour", 0.05)
        return base_cost * req.count

    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        return self._resources.get(resource_id)

    def list_resources(self, provider: Optional[str] = None,
                       resource_type: Optional[str] = None,
                       status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for r in self._resources.values():
            if provider and r["provider"] != provider:
                continue
            if resource_type and r["resource_type"] != resource_type:
                continue
            if status and r["status"] != status:
                continue
            results.append(r)
        return results

    def update_resource_status(self, resource_id: str, status: ResourceStatus) -> bool:
        r = self._resources.get(resource_id)
        if not r:
            return False
        r["status"] = status.value
        if status == ResourceStatus.RUNNING and not r["provisioned_at"]:
            r["provisioned_at"] = datetime.utcnow().isoformat()
        return True

    def delete_resource(self, resource_id: str) -> bool:
        if resource_id in self._resources:
            del self._resources[resource_id]
            return True
        return False

    def score_providers(self, requirements: Dict[str, Any]) -> List[ProviderScore]:
        scores = []
        for prov in CloudProvider:
            if prov.value not in self._credentials:
                continue
            cost_score = self._calculate_cost_score(prov, requirements)
            latency_score = self._calculate_latency_score(prov, requirements)
            region_score = self._calculate_region_score(prov, requirements)
            availability_score = self._calculate_availability_score(prov)
            overall = (
                cost_score * self.scoring_weights["cost"] +
                latency_score * self.scoring_weights["latency"] +
                region_score * self.scoring_weights["region"] +
                availability_score * self.scoring_weights["availability"]
            )
            scores.append(ProviderScore(prov, cost_score, latency_score,
                                        region_score, availability_score, overall))
        scores.sort(key=lambda s: s.overall, reverse=True)
        return scores

    def _calculate_cost_score(self, provider: CloudProvider,
                               requirements: Dict[str, Any]) -> float:
        pricing = self.config.get("pricing", {}).get(provider.value, {})
        base = pricing.get("base_hourly_rate", 0.10)
        req_cost = requirements.get("max_budget_per_hour", 1.0)
        if base == 0:
            return 1.0
        return max(0.0, min(1.0, (req_cost - base) / req_cost))

    def _calculate_latency_score(self, provider: CloudProvider,
                                   requirements: Dict[str, Any]) -> float:
        latency_map = {"aws": 0.9, "azure": 0.85, "gcp": 0.8,
                       "hetzner": 0.7, "ovh": 0.65, "digitalocean": 0.75}
        return latency_map.get(provider.value, 0.5)

    def _calculate_region_score(self, provider: CloudProvider,
                                  requirements: Dict[str, Any]) -> float:
        desired_region = requirements.get("region", self.default_region)
        provider_regions = self.config.get("regions", {}).get(provider.value, [])
        for pr in provider_regions:
            if desired_region in pr:
                return 1.0
        return 0.3

    def _calculate_availability_score(self, provider: CloudProvider) -> float:
        avail_map = {"aws": 0.999, "azure": 0.995, "gcp": 0.99,
                     "hetzner": 0.97, "ovh": 0.95, "digitalocean": 0.98}
        return avail_map.get(provider.value, 0.9)

    async def auto_failover(self, failed_resource_id: str) -> Optional[Dict[str, Any]]:
        if not self.failover_enabled:
            return None
        failed = self._resources.get(failed_resource_id)
        if not failed:
            return None
        failed_provider = failed["provider"]
        scores = self.score_providers({"region": failed.get("region")})
        for s in scores:
            if s.provider.value != failed_provider and s.overall >= self.failover_threshold:
                new_req = ResourceProvisioningRequest(
                    ResourceType(failed["resource_type"]),
                    s.provider, failed["specs"], failed.get("region", self.default_region),
                    1, failed.get("tags"))
                result = await self.provision_resources(new_req)
                logger.info(f"Auto-failover from {failed_provider} to {s.provider.value}")
                return result
        return None

    def get_statistics(self) -> Dict[str, Any]:
        provider_counts = {}
        for r in self._resources.values():
            p = r["provider"]
            provider_counts[p] = provider_counts.get(p, 0) + 1
        return {"total_resources": len(self._resources),
                "resources_by_provider": provider_counts,
                "configured_providers": len(self._credentials),
                "pending_requests": len(self._provisioning_requests)}

    def get_pricing_models(self) -> Dict[str, Any]:
        return self.config.get("pricing", {})

    async def batch_provision(self, requests: List[ResourceProvisioningRequest]) -> List[Dict[str, Any]]:
        results = []
        for req in requests:
            try:
                result = await self.provision_resources(req)
                results.append(result)
            except ValueError as e:
                results.append({"request_id": req.id, "status": "error", "message": str(e)})
        logger.info(f"Batch provisioned {len(results)} resources")
        return results

    async def batch_delete(self, resource_ids: List[str]) -> Dict[str, Any]:
        deleted = []
        failed = []
        for rid in resource_ids:
            if self.delete_resource(rid):
                deleted.append(rid)
            else:
                failed.append(rid)
        return {"deleted": deleted, "failed": failed, "total": len(resource_ids)}

    def find_resources_by_tag(self, key: str, value: str) -> List[Dict[str, Any]]:
        return [r for r in self._resources.values()
                if r.get("tags", {}).get(key) == value]

    def get_resources_by_provider(self, provider: CloudProvider) -> List[Dict[str, Any]]:
        return self.list_resources(provider=provider.value)

    async def export_resources(self, format: str = "json") -> Dict[str, Any]:
        export = {
            "exported_at": datetime.utcnow().isoformat(),
            "provider_count": len(self._credentials),
            "resource_count": len(self._resources),
            "providers": [c.to_dict() for c in self._credentials.values()],
            "resources": list(self._resources.values()),
            "pending_requests": [r.to_dict() for r in self._provisioning_requests.values()]
        }
        return export

    def validate_credentials(self, provider: CloudProvider) -> Dict[str, Any]:
        creds = self._credentials.get(provider.value)
        if not creds:
            return {"valid": False, "message": "No credentials configured"}
        has_key = bool(creds.api_key) and len(creds.api_key) > 10
        has_secret = bool(creds.api_secret) and len(creds.api_secret) > 10
        creds.validated = has_key and has_secret
        return {"valid": creds.validated, "provider": provider.value,
                "has_api_key": has_key, "has_api_secret": has_secret}

    def calculate_cost_summary(self) -> Dict[str, Any]:
        total_cost = sum(r.get("cost_per_hour", 0) for r in self._resources.values())
        by_provider = {}
        for r in self._resources.values():
            p = r.get("provider", "unknown")
            by_provider[p] = by_provider.get(p, 0) + r.get("cost_per_hour", 0)
        return {"total_cost_per_hour": round(total_cost, 4),
                "total_cost_per_day": round(total_cost * 24, 2),
                "total_cost_per_month": round(total_cost * 24 * 30, 2),
                "by_provider": {k: round(v, 4) for k, v in by_provider.items()},
                "resource_count": len(self._resources)}

    async def cross_provider_migration(self, resource_id: str,
                                        target_provider: CloudProvider) -> Dict[str, Any]:
        resource = self._resources.get(resource_id)
        if not resource:
            return {"status": "error", "message": "Resource not found"}
        scores = self.score_providers({"region": resource.get("region", self.default_region)})
        target_ok = any(s.provider == target_provider and s.overall >= 0.5 for s in scores)
        if not target_ok:
            return {"status": "error", "message": f"{target_provider.value} not suitable"}
        new_req = ResourceProvisioningRequest(
            ResourceType(resource["resource_type"]),
            target_provider, resource["specs"],
            resource.get("region", self.default_region), 1, resource.get("tags"))
        result = await self.provision_resources(new_req)
        self.delete_resource(resource_id)
        return {"status": "migrated", "from": resource.get("provider"),
                "to": target_provider.value, "new_resource_ids": result.get("resource_ids", [])}

    def bulk_update_tags(self, resource_ids: List[str],
                         tags: Dict[str, str]) -> Dict[str, Any]:
        updated = 0
        for rid in resource_ids:
            r = self._resources.get(rid)
            if r:
                r["tags"].update(tags)
                updated += 1
        return {"updated": updated, "total": len(resource_ids)}

    async def monitor_resources_health(self) -> Dict[str, Any]:
        healthy = 0
        warning = 0
        critical = 0
        for r in self._resources.values():
            if r.get("status") == ResourceStatus.RUNNING.value:
                healthy += 1
            elif r.get("status") == ResourceStatus.FAILED.value:
                critical += 1
            else:
                warning += 1
        return {"healthy": healthy, "warning": warning, "critical": critical,
                "total": len(self._resources),
                "health_score": round(healthy / max(len(self._resources), 1) * 100, 2)}

    def get_resource_counts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self._resources.values():
            rt = r.get("resource_type", "unknown")
            counts[rt] = counts.get(rt, 0) + 1
        return counts

    def get_cost_by_resource_type(self) -> Dict[str, float]:
        costs: Dict[str, float] = {}
        for r in self._resources.values():
            rt = r.get("resource_type", "unknown")
            costs[rt] = costs.get(rt, 0) + r.get("cost_per_hour", 0)
        return {k: round(v, 4) for k, v in costs.items()}

    async def provision_with_retry(self, req: ResourceProvisioningRequest, max_retries: int = 3) -> Dict[str, Any]:
        for attempt in range(max_retries):
            try:
                return await self.provision_resources(req)
            except ValueError as e:
                if attempt == max_retries - 1:
                    return {"request_id": req.id, "status": "failed", "error": str(e), "attempts": attempt + 1}
        return {"request_id": req.id, "status": "failed", "error": "Max retries exceeded"}

    def get_available_regions(self, provider: CloudProvider) -> List[str]:
        return self.config.get("regions", {}).get(provider.value, [])

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import csv, io, random

@dataclass
class CloudProviderConfig:
    provider: CloudProvider
    endpoint: str = ""
    api_version: str = "latest"
    max_retries: int = 3
    timeout_seconds: int = 30
    rate_limit_rps: int = 10
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ResourceReservation:
    reservation_id: str
    resource_id: str
    reserved_by: str
    purpose: str
    start_time: datetime
    end_time: datetime
    status: str = "active"

@dataclass
class ProviderHealthStatus:
    provider: CloudProvider
    reachable: bool
    latency_ms: float
    last_checked: datetime
    error_message: str = ""

# ── Batch Operation Methods ──────────────────────────────────────────

    async def batch_update_status(self, resource_ids: List[str], status: ResourceStatus) -> Dict[str, Any]:
        updated = 0; failed = 0
        for rid in resource_ids:
            if self.update_resource_status(rid, status):
                updated += 1
            else:
                failed += 1
        return {"updated": updated, "failed": failed, "total": len(resource_ids)}

    async def batch_update_tags(self, updates: List[Tuple[str, Dict[str, str]]]) -> Dict[str, Any]:
        results = []
        for rid, tags in updates:
            r = self._resources.get(rid)
            if r:
                r["tags"].update(tags)
                results.append({"resource_id": rid, "status": "updated"})
            else:
                results.append({"resource_id": rid, "status": "not_found"})
        return {"results": results, "total": len(updates)}

    async def bulk_provision_multi_provider(self, requests: List[ResourceProvisioningRequest]) -> Dict[str, Any]:
        results = {}
        for req in requests:
            prov_name = req.provider.value
            if prov_name not in results:
                results[prov_name] = []
            try:
                res = await self.provision_resources(req)
                results[prov_name].append(res)
            except ValueError as e:
                results[prov_name].append({"request_id": req.id, "error": str(e)})
        return {"by_provider": results, "total_requests": len(requests)}

# ── Async Pagination / Sorting ───────────────────────────────────────

    async def paginate_resources(self, page: int = 1, page_size: int = 20,
                                  sort_by: str = "created_at", sort_desc: bool = True,
                                  provider_filter: Optional[str] = None,
                                  type_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._resources.values())
        if provider_filter:
            items = [r for r in items if r.get("provider") == provider_filter]
        if type_filter:
            items = [r for r in items if r.get("resource_type") == type_filter]
        reverse = sort_desc
        items.sort(key=lambda r: r.get(sort_by, ""), reverse=reverse)
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": items[start:end],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
            "sort_by": sort_by,
            "sort_desc": sort_desc,
        }

    async def paginate_provisioning_requests(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        reqs = list(self._provisioning_requests.values())
        reqs.sort(key=lambda r: r.created_at, reverse=True)
        total = len(reqs)
        start = (page - 1) * page_size
        return {
            "items": [r.to_dict() for r in reqs[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import Functionality ────────────────────────────────────

    async def export_to_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "provider", "resource_type", "region", "status", "cost_per_hour", "created_at"])
        for r in self._resources.values():
            writer.writerow([r.get("id"), r.get("provider"), r.get("resource_type"),
                            r.get("region"), r.get("status"), r.get("cost_per_hour", 0),
                            r.get("created_at")])
        return output.getvalue()

    async def import_from_csv(self, csv_content: str) -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0; errors = 0
        for row in reader:
            try:
                req = ResourceProvisioningRequest(
                    ResourceType(row.get("resource_type", "compute")),
                    CloudProvider(row.get("provider", "aws")),
                    {"vcpu": int(row.get("vcpu", 2)), "memory_gb": int(row.get("memory_gb", 4))},
                    row.get("region", "us-east-1"), int(row.get("count", 1))
                )
                await self.provision_resources(req)
                imported += 1
            except Exception:
                errors += 1
        return {"imported": imported, "errors": errors, "total_rows": imported + errors}

    def export_provider_config(self) -> List[Dict[str, Any]]:
        return [{"provider": p, "region": c.region, "validated": c.validated,
                 "account_id": c.account_id} for p, c in self._credentials.items()]

    def import_provider_config(self, configs: List[Dict[str, Any]]) -> int:
        count = 0
        for cfg in configs:
            try:
                prov = CloudProvider(cfg["provider"])
                creds = ProviderCredentials(prov, cfg.get("api_key", ""), cfg.get("api_secret", ""),
                                            cfg.get("region", "us-east-1"), cfg.get("account_id", ""))
                self._credentials[prov.value] = creds
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_cost_anomalies(self, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        anomalies = []
        provider_costs: Dict[str, List[float]] = {}
        for r in self._resources.values():
            p = r.get("provider", "unknown")
            if p not in provider_costs:
                provider_costs[p] = []
            provider_costs[p].append(r.get("cost_per_hour", 0))
        for p, costs in provider_costs.items():
            if len(costs) < 3:
                continue
            avg = sum(costs) / len(costs)
            for r in self._resources.values():
                if r.get("provider") == p:
                    cost = r.get("cost_per_hour", 0)
                    if avg > 0 and cost > avg * threshold_multiplier:
                        anomalies.append({"resource_id": r["id"], "provider": p,
                                          "cost": cost, "average": round(avg, 4),
                                          "ratio": round(cost / avg, 2)})
        return anomalies

    def get_provider_utilization_heatmap(self) -> Dict[str, Any]:
        heatmap: Dict[str, Dict[str, int]] = {}
        for r in self._resources.values():
            p = r.get("provider", "unknown")
            rt = r.get("resource_type", "unknown")
            if p not in heatmap:
                heatmap[p] = {}
            heatmap[p][rt] = heatmap[p].get(rt, 0) + 1
        return {"heatmap": heatmap, "total_resources": len(self._resources)}

    def get_spending_forecast(self, days: int = 30) -> Dict[str, Any]:
        total_per_hour = sum(r.get("cost_per_hour", 0) for r in self._resources.values())
        daily = total_per_hour * 24
        return {
            "current_hourly": round(total_per_hour, 4),
            "forecast_daily": round(daily, 2),
            "forecast_weekly": round(daily * 7, 2),
            "forecast_monthly": round(daily * 30, 2),
            "forecast_quarterly": round(daily * 90, 2),
            "forecast_days": days,
            "confidence": "medium",
        }

    def get_resource_lifecycle_analysis(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        young = old = 0
        for r in self._resources.values():
            created = r.get("created_at")
            if created:
                age = now - datetime.fromisoformat(created)
                if age.days < 7:
                    young += 1
                elif age.days > 90:
                    old += 1
        return {"young_resources_7d": young, "old_resources_90d": old,
                "total": len(self._resources),
                "turnover_rate": round(young / max(len(self._resources), 1) * 100, 1)}

# ── State Machine / Workflow Logic ───────────────────────────────────

    async def resource_lifecycle_workflow(self, resource_id: str, target_action: str) -> Dict[str, Any]:
        workflow_states = {
            "provision": [ResourceStatus.PROVISIONING, ResourceStatus.RUNNING],
            "stop": [ResourceStatus.RUNNING, ResourceStatus.STOPPED],
            "start": [ResourceStatus.STOPPED, ResourceStatus.RUNNING],
            "terminate": [ResourceStatus.RUNNING, ResourceStatus.STOPPED, ResourceStatus.TERMINATED],
            "failover": [ResourceStatus.RUNNING, ResourceStatus.FAILED, ResourceStatus.PROVISIONING],
        }
        if target_action not in workflow_states:
            return {"status": "error", "message": f"Unknown action: {target_action}"}
        resource = self._resources.get(resource_id)
        if not resource:
            return {"status": "error", "message": "Resource not found"}
        current = ResourceStatus(resource["status"])
        valid_states = workflow_states[target_action]
        if current not in valid_states:
            return {"status": "error", "message": f"Resource in state {current.value} cannot perform {target_action}"}
        resource["status"] = valid_states[-1].value if target_action != "failover" else ResourceStatus.PROVISIONING.value
        return {"status": "completed", "action": target_action, "resource_id": resource_id,
                "new_state": resource["status"]}

    async def scheduled_cleanup_workflow(self, max_age_days: int = 90) -> Dict[str, Any]:
        now = datetime.utcnow()
        terminated = 0
        for rid, r in list(self._resources.items()):
            created = r.get("created_at")
            if created:
                age = now - datetime.fromisoformat(created)
                if age.days > max_age_days and r.get("status") != ResourceStatus.TERMINATED.value:
                    r["status"] = ResourceStatus.TERMINATED.value
                    terminated += 1
        return {"resources_terminated": terminated, "max_age_days": max_age_days}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_config(self) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not self.config.get("default_region"):
            errors.append("default_region is required")
        if not self.config.get("provisioning_timeout"):
            warnings.append("provisioning_timeout not set, using default 600")
        weights = self.config.get("scoring_weights", {})
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            warnings.append(f"scoring_weights sum to {total_weight}, expected 1.0")
        pricing = self.config.get("pricing", {})
        for prov in CloudProvider:
            if prov.value in self._credentials and prov.value not in pricing:
                warnings.append(f"No pricing config for {prov.value}")
        if not self._credentials:
            errors.append("No provider credentials configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                "provider_count": len(self._credentials)}

# -- Batch Operations ---------------------------------------------------

    async def batch_deploy_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for res in resources:
            try:
                result = await self.deploy_resource(res.get("provider", "aws"), res)
                results.append({"resource_id": result.get("id"), "status": "deployed"})
            except Exception as e:
                results.append({"resource": res.get("name"), "status": "failed", "error": str(e)})
        return {"batch_results": results, "total": len(results), "successful": sum(1 for r in results if r["status"] == "deployed")}

    async def batch_terminate_resources(self, resource_ids: List[str]) -> Dict[str, Any]:
        results = []
        for rid in resource_ids:
            try:
                await self.terminate_resource(rid)
                results.append({"resource_id": rid, "status": "terminated"})
            except Exception as e:
                results.append({"resource_id": rid, "status": "failed", "error": str(e)})
        return {"batch_results": results, "total": len(results), "successful": sum(1 for r in results if r["status"] == "terminated")}

# -- Analytics / Aggregation --------------------------------------------

    def get_provider_summary_stats(self) -> Dict[str, Any]:
        providers = {}
        for r in self._resources.values():
            p = r.get("provider", "unknown")
            if p not in providers:
                providers[p] = {"count": 0, "total_cost": 0.0, "types": set()}
            providers[p]["count"] += 1
            providers[p]["total_cost"] += r.get("cost_per_hour", 0)
            providers[p]["types"].add(r.get("resource_type", "unknown"))
        for p in providers:
            providers[p]["types"] = list(providers[p]["types"])
        return {"providers": providers, "total_resources": len(self._resources),
                "total_hourly_cost": sum(p["total_cost"] for p in providers.values())}

    def get_cost_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        now = datetime.utcnow()
        daily_costs: Dict[str, float] = {}
        for r in self._resources.values():
            created = r.get("created_at")
            if created:
                age = now - datetime.fromisoformat(created)
                if age.days <= days:
                    day_key = created[:10]
                    daily_costs[day_key] = daily_costs.get(day_key, 0) + r.get("cost_per_hour", 0) * 24
        costs = list(daily_costs.values())
        return {"daily_costs": daily_costs, "days_analyzed": days,
                "avg_daily": round(sum(costs) / max(len(costs), 1), 2),
                "max_daily": round(max(costs), 2) if costs else 0,
                "min_daily": round(min(costs), 2) if costs else 0,
                "total_cost_period": round(sum(costs), 2)}

    def get_resource_type_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for r in self._resources.values():
            rt = r.get("resource_type", "unknown")
            dist[rt] = dist.get(rt, 0) + 1
        return {"distribution": dist, "total": len(self._resources)}

# -- Data Models / Schema ----------------------------------------------

class ProviderCredentials(BaseModel):
    provider: CloudProvider
    api_key: str = Field(default="")
    secret_key: str = Field(default="")
    region: str = Field(default="us-east-1")
    account_id: str = Field(default="")
    enabled: bool = Field(default=True)
    rate_limit: int = Field(default=100, ge=1)
    retry_count: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=30, ge=1)

class ResourceDeploymentRequest(BaseModel):
    provider: str
    resource_type: str
    name: str
    region: str = Field(default="us-east-1")
    specs: Dict[str, Any] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)
    cost_limit: Optional[float] = Field(default=None, ge=0)
    ttl_hours: Optional[int] = Field(default=None, ge=1)
    depends_on: List[str] = Field(default_factory=list)

class BatchDeploymentResult(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resources: List[ResourceDeploymentRequest] = Field(default_factory=list)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)

    def record_success(self) -> None:
        self.success_count += 1

    def record_failure(self, error: str) -> None:
        self.failure_count += 1
        self.errors.append(error)

    def complete(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.utcnow()

# -- Provider Health / Status ------------------------------------------

class ProviderHealthCheck(BaseModel):
    provider: CloudProvider
    region: str
    status: str = Field(default="unknown")
    latency_ms: float = Field(default=0.0)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    services_available: List[str] = Field(default_factory=list)
    services_degraded: List[str] = Field(default_factory=list)

class ProviderHealthManager:
    def __init__(self) -> None:
        self._checks: Dict[str, ProviderHealthCheck] = {}

    async def run_health_check(self, provider: CloudProvider, region: str) -> ProviderHealthCheck:
        start = datetime.utcnow()
        latency = random.uniform(5, 200)
        status = "healthy" if latency < 150 else "degraded" if latency < 300 else "unhealthy"
        check = ProviderHealthCheck(
            provider=provider, region=region, status=status,
            latency_ms=round(latency, 1), last_checked=start,
            services_available=["compute", "storage"] if status != "unhealthy" else [],
            services_degraded=["network"] if status == "degraded" else [],
        )
        key = f"{provider.value}:{region}"
        self._checks[key] = check
        return check

    def get_aggregate_health(self) -> Dict[str, Any]:
        healthy = sum(1 for c in self._checks.values() if c.status == "healthy")
        degraded = sum(1 for c in self._checks.values() if c.status == "degraded")
        unhealthy = sum(1 for c in self._checks.values() if c.status == "unhealthy")
        return {"total_checks": len(self._checks), "healthy": healthy,
                "degraded": degraded, "unhealthy": unhealthy,
                "health_score": round(healthy / max(len(self._checks), 1) * 100, 1)}

    def get_provider_health(self, provider: CloudProvider) -> List[ProviderHealthCheck]:
        return [c for c in self._checks.values() if c.provider == provider]

# -- Resource Tagging / Metadata ---------------------------------------

class ResourceTag(BaseModel):
    key: str
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="manual")

class ResourceMetadataManager:
    def __init__(self) -> None:
        self._tags: Dict[str, List[ResourceTag]] = {}

    def add_tag(self, resource_id: str, key: str, value: str, source: str = "manual") -> ResourceTag:
        tag = ResourceTag(key=key, value=value, source=source)
        if resource_id not in self._tags:
            self._tags[resource_id] = []
        self._tags[resource_id].append(tag)
        return tag

    def get_tags(self, resource_id: str) -> List[ResourceTag]:
        return self._tags.get(resource_id, [])

    def get_resources_by_tag(self, key: str, value: str) -> List[str]:
        return [rid for rid, tags in self._tags.items()
                for t in tags if t.key == key and t.value == value]

    def remove_tag(self, resource_id: str, key: str, value: str) -> bool:
        if resource_id in self._tags:
            before = len(self._tags[resource_id])
            self._tags[resource_id] = [t for t in self._tags[resource_id] if not (t.key == key and t.value == value)]
            return len(self._tags[resource_id]) < before
        return False

    def get_tag_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for tags in self._tags.values():
            for t in tags:
                summary[t.key] = summary.get(t.key, 0) + 1
        return summary

# -- Cross-Provider Migration Orchestration ----------------------------

class MigrationPlan(BaseModel):
    source_provider: CloudProvider
    target_provider: CloudProvider
    resource_ids: List[str] = Field(default_factory=list)
    strategy: str = Field(default="lift-and-shift")
    scheduled_at: Optional[datetime] = None
    estimated_downtime_seconds: int = Field(default=300)
    validation_required: bool = Field(default=True)
    rollback_plan: Optional[str] = None

class MigrationOrchestrator:
    def __init__(self, broker: "MultiCloudBroker") -> None:
        self.broker = broker
        self._plans: Dict[str, MigrationPlan] = {}
        self._execution_log: List[Dict[str, Any]] = []

    def create_plan(self, plan: MigrationPlan) -> str:
        plan_id = str(uuid.uuid4())
        self._plans[plan_id] = plan
        return plan_id

    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        plan = self._plans.get(plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
        results = []
        for rid in plan.resource_ids:
            resource = self.broker._resources.get(rid)
            if not resource:
                results.append({"resource_id": rid, "status": "skipped", "reason": "not found"})
                continue
            try:
                resource["provider"] = plan.target_provider.value
                results.append({"resource_id": rid, "status": "migrated"})
            except Exception as e:
                results.append({"resource_id": rid, "status": "failed", "error": str(e)})
        log_entry = {"plan_id": plan_id, "executed_at": datetime.utcnow().isoformat(),
                     "results": results, "success_rate": round(sum(1 for r in results if r["status"] == "migrated") / max(len(results), 1) * 100, 1)}
        self._execution_log.append(log_entry)
        return log_entry

    def get_plan_status(self, plan_id: str) -> Optional[MigrationPlan]:
        return self._plans.get(plan_id)

# -- Batch Operations ---------------------------------------------------

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

# -- Analytics / Aggregation -------------------------------------------

    def get_summary_stats(self) -> Dict[str, Any]:
        return {"total_items": 0, "active_items": 0, "inactive_items": 0}

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        return {"period_days": days, "data_points": 0, "trend": "stable"}

# -- Data Models -------------------------------------------------------

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
