import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class BurstState(Enum):
    IDLE = "idle"
    BURSTING = "bursting"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    DRAINING = "draining"
    COMPLETED = "completed"
    FAILED = "failed"


class LoadDistributionStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LATENCY_BASED = "latency_based"
    WEIGHTED = "weighted"
    RANDOM = "random"


class NetworkStitchingMethod(Enum):
    VPN = "vpn"
    GRE = "gre"
    VXLAN = "vxlan"
    DIRECT_CONNECT = "direct_connect"
    WIREGUARD = "wireguard"


class BurstWorkload:
    def __init__(self, workload_id: str, name: str, target_capacity: int,
                 current_capacity: int = 0, priority: int = 5,
                 tags: Optional[Dict[str, str]] = None):
        self.workload_id = workload_id
        self.name = name
        self.target_capacity = target_capacity
        self.current_capacity = current_capacity
        self.priority = priority
        self.tags = tags or {}
        self.state = BurstState.IDLE
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {"workload_id": self.workload_id, "name": self.name,
                "target_capacity": self.target_capacity,
                "current_capacity": self.current_capacity, "priority": self.priority,
                "tags": self.tags, "state": self.state.value,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()}


class CloudBurstingGateway:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_burst_threshold = config.get("min_burst_threshold", 80)
        self.max_burst_capacity = config.get("max_burst_capacity", 500)
        self.default_strategy = LoadDistributionStrategy(
            config.get("default_strategy", "least_connections"))
        self.stitching_method = NetworkStitchingMethod(
            config.get("stitching_method", "wireguard"))
        self.burst_duration_minutes = config.get("burst_duration_minutes", 120)
        self.drain_timeout_seconds = config.get("drain_timeout_seconds", 300)
        self.on_prem_capacity = config.get("on_prem_capacity", {"cpu": 100, "memory_gb": 256, "storage_gb": 2000})
        self.cloud_capacity = config.get("cloud_capacity", {"cpu": 1000, "memory_gb": 4096, "storage_gb": 50000})
        self._workloads: Dict[str, BurstWorkload] = {}
        self._active_bursts: Dict[str, Dict[str, Any]] = {}
        self._network_stitches: Dict[str, Dict[str, Any]] = {}
        self._burst_history: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"CloudBurstingGateway initialized, strategy={self.default_strategy.value}")

    async def close(self) -> None:
        self._workloads.clear()
        self._active_bursts.clear()
        self._network_stitches.clear()
        logger.info("CloudBurstingGateway closed")

    def register_workload(self, name: str, target_capacity: int,
                          priority: int = 5,
                          tags: Optional[Dict[str, str]] = None) -> BurstWorkload:
        wid = f"wl-{uuid.uuid4().hex[:12]}"
        wl = BurstWorkload(wid, name, target_capacity, 0, priority, tags)
        self._workloads[wid] = wl
        return wl

    def get_workload(self, workload_id: str) -> Optional[BurstWorkload]:
        return self._workloads.get(workload_id)

    def list_workloads(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        if state:
            return [w.to_dict() for w in self._workloads.values() if w.state.value == state]
        return [w.to_dict() for w in self._workloads.values()]

    def delete_workload(self, workload_id: str) -> bool:
        if workload_id in self._workloads:
            del self._workloads[workload_id]
            return True
        return False

    def check_burst_needed(self) -> Dict[str, Any]:
        total_target = sum(w.target_capacity for w in self._workloads.values()
                          if w.state == BurstState.IDLE or w.state == BurstState.BURSTING)
        total_current = sum(w.current_capacity for w in self._workloads.values())
        if total_target == 0:
            return {"burst_needed": False, "utilization": 0}
        utilization = (total_current / total_target) * 100
        burst_needed = utilization >= self.min_burst_threshold
        return {"burst_needed": burst_needed, "utilization": utilization,
                "current_capacity": total_current, "target_capacity": total_target}

    async def initiate_burst(self, workload_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        targets = []
        if workload_ids:
            for wid in workload_ids:
                wl = self._workloads.get(wid)
                if wl:
                    targets.append(wl)
        else:
            check = self.check_burst_needed()
            if not check["burst_needed"]:
                return {"status": "burst_not_needed", "utilization": check["utilization"]}
            targets = [w for w in self._workloads.values()
                      if w.state == BurstState.IDLE]

        burst_id = f"burst-{uuid.uuid4().hex[:12]}"
        burst = {
            "burst_id": burst_id, "started_at": datetime.utcnow().isoformat(),
            "workloads": [w.workload_id for w in targets],
            "state": BurstState.BURSTING.value,
            "strategy": self.default_strategy.value,
            "cloud_resources_allocated": 0,
            "stitching_method": self.stitching_method.value,
        }
        self._active_bursts[burst_id] = burst
        for wl in targets:
            wl.state = BurstState.BURSTING
            wl.updated_at = datetime.utcnow()

        stitch = await self._create_network_stitch(burst_id)
        burst["network_stitch_id"] = stitch["stitch_id"]
        self._burst_history.append(burst)
        logger.info(f"Burst {burst_id} initiated with {len(targets)} workloads")
        return burst

    async def _create_network_stitch(self, burst_id: str) -> Dict[str, Any]:
        stitch_id = f"stitch-{uuid.uuid4().hex[:10]}"
        stitch = {
            "stitch_id": stitch_id, "burst_id": burst_id,
            "method": self.stitching_method.value,
            "status": "established", "created_at": datetime.utcnow().isoformat(),
            "on_prem_subnet": self.config.get("on_prem_subnet", "10.0.0.0/8"),
            "cloud_subnet": self.config.get("cloud_subnet", "172.16.0.0/12"),
            "peers": [], "latency_ms": 0, "throughput_mbps": 0
        }
        self._network_stitches[stitch_id] = stitch
        return stitch

    def get_network_stitch(self, stitch_id: str) -> Optional[Dict[str, Any]]:
        return self._network_stitches.get(stitch_id)

    def list_network_stitches(self) -> List[Dict[str, Any]]:
        return list(self._network_stitches.values())

    def update_burst_capacity(self, burst_id: str, allocated: int) -> bool:
        burst = self._active_bursts.get(burst_id)
        if not burst:
            return False
        burst["cloud_resources_allocated"] = allocated
        return True

    async def drain_burst(self, burst_id: str) -> Dict[str, Any]:
        burst = self._active_bursts.get(burst_id)
        if not burst:
            return {"status": "error", "message": "Burst not found"}
        burst["state"] = BurstState.DRAINING.value
        for wid in burst["workloads"]:
            wl = self._workloads.get(wid)
            if wl:
                wl.state = BurstState.DRAINING
                wl.updated_at = datetime.utcnow()
        stitch_id = burst.get("network_stitch_id")
        if stitch_id and stitch_id in self._network_stitches:
            self._network_stitches[stitch_id]["status"] = "tearing_down"
        burst["completed_at"] = datetime.utcnow().isoformat()
        burst["state"] = BurstState.COMPLETED.value
        for wid in burst["workloads"]:
            wl = self._workloads.get(wid)
            if wl:
                wl.state = BurstState.COMPLETED
                wl.updated_at = datetime.utcnow()
        del self._active_bursts[burst_id]
        logger.info(f"Burst {burst_id} drained and completed")
        return {"burst_id": burst_id, "status": "completed"}

    def get_active_bursts(self) -> List[Dict[str, Any]]:
        return list(self._active_bursts.values())

    def get_burst_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return sorted(self._burst_history, key=lambda x: x["started_at"], reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_workloads": len(self._workloads),
                "active_bursts": len(self._active_bursts),
                "total_bursts": len(self._burst_history),
                "network_stitches": len(self._network_stitches),
                "on_prem_utilization": self.check_burst_needed().get("utilization", 0)}

    def simulate_load_distribution(self, strategy: Optional[LoadDistributionStrategy] = None) -> Dict[str, Any]:
        s = strategy or self.default_strategy
        distribution = {}
        total = sum(w.target_capacity for w in self._workloads.values())
        if total == 0:
            return {"strategy": s.value, "distribution": {}}
        if s == LoadDistributionStrategy.ROUND_ROBIN:
            idx = 0
            for w in self._workloads.values():
                distribution[w.workload_id] = {"weight": 1, "ratio": 1 / len(self._workloads)}
        elif s == LoadDistributionStrategy.WEIGHTED:
            for w in self._workloads.values():
                weight = w.priority / 10
                distribution[w.workload_id] = {"weight": weight, "ratio": weight / total}
        else:
            for w in self._workloads.values():
                distribution[w.workload_id] = {"weight": 1, "ratio": w.target_capacity / total}
        return {"strategy": s.value, "distribution": distribution}

    def get_workload(self, workload_id: str) -> Optional[Dict[str, Any]]:
        wl = self._workloads.get(workload_id)
        return wl.to_dict() if wl else None

    def list_workloads(self, state: Optional[BurstState] = None) -> List[Dict[str, Any]]:
        if state:
            return [w.to_dict() for w in self._workloads.values() if w.state == state]
        return [w.to_dict() for w in self._workloads.values()]

    def create_network_stitch(self, on_prem_cidr: str, cloud_cidr: str,
                               provider: str, region: str) -> Dict[str, Any]:
        stitch_id = f"stitch-{uuid.uuid4().hex[:8]}"
        stitch = {"id": stitch_id, "on_prem_cidr": on_prem_cidr,
                  "cloud_cidr": cloud_cidr, "provider": provider,
                  "region": region, "status": "active",
                  "created_at": datetime.utcnow().isoformat()}
        self._network_stitches[stitch_id] = stitch
        return stitch

    def remove_network_stitch(self, stitch_id: str) -> bool:
        if stitch_id in self._network_stitches:
            self._network_stitches[stitch_id]["status"] = "removed"
            del self._network_stitches[stitch_id]
            return True
        return False

    async def burst_workload(self, workload_id: str) -> Dict[str, Any]:
        wl = self._workloads.get(workload_id)
        if not wl:
            return {"status": "error", "message": "Workload not found"}
        if self.check_burst_needed().get("burst_needed"):
            burst = self.create_burst("auto")
            burst["workloads"].append(workload_id)
            wl.state = BurstState.BURSTING
            wl.updated_at = datetime.utcnow()
            return {"status": "burst_initiated", "burst_id": burst["id"],
                    "workload": workload_id}
        return {"status": "no_burst_needed", "workload": workload_id}

    def set_load_strategy(self, strategy: LoadDistributionStrategy) -> None:
        self.default_strategy = strategy
        logger.info(f"Load distribution strategy set to {strategy.value}")

    def get_network_stitches(self) -> List[Dict[str, Any]]:
        return list(self._network_stitches.values())

    def update_workload_capacity(self, workload_id: str,
                                  target_capacity: int) -> bool:
        wl = self._workloads.get(workload_id)
        if not wl:
            return False
        wl.target_capacity = target_capacity
        wl.updated_at = datetime.utcnow()
        return True

    def add_workload(self, name: str, target_capacity: int, priority: int = 5,
                     cloud_provider: Optional[str] = None) -> Workload:
        wl = Workload(name, target_capacity, priority, cloud_provider)
        self._workloads[wl.workload_id] = wl
        return wl

    def remove_workload(self, workload_id: str) -> bool:
        if workload_id in self._workloads:
            wl = self._workloads[workload_id]
            wl.state = BurstState.DRAINING
            del self._workloads[workload_id]
            return True
        return False

    def get_cost_analysis(self) -> Dict[str, Any]:
        total_bursts = len(self._burst_history)
        if total_bursts == 0:
            return {"total_bursts": 0, "estimated_savings": 0}
        avg_duration = sum(b.get("duration_minutes", 0) for b in self._burst_history) / total_bursts
        on_prem_cost = sum(w.target_capacity * 0.50 for w in self._workloads.values())
        cloud_cost = sum(w.target_capacity * 0.35 for w in self._workloads.values())
        return {"total_bursts": total_bursts, "avg_duration_minutes": round(avg_duration, 1),
                "estimated_on_prem_cost": round(on_prem_cost, 2),
                "estimated_cloud_cost": round(cloud_cost, 2),
                "estimated_savings": round(on_prem_cost - cloud_cost, 2)}

    def get_burst_metrics(self, burst_id: str) -> Dict[str, Any]:
        burst = self._active_bursts.get(burst_id)
        if not burst:
            for b in self._burst_history:
                if b.get("burst_id") == burst_id:
                    burst = b
                    break
        if not burst:
            return {"status": "error", "message": "Burst not found"}
        return {"burst_id": burst_id, "state": burst.get("state"),
                "workload_count": len(burst.get("workloads", [])),
                "cloud_resources_allocated": burst.get("cloud_resources_allocated", 0),
                "stitching_method": burst.get("stitching_method", "unknown")}

    def set_burst_threshold(self, threshold_pct: int) -> None:
        self.min_burst_threshold = max(10, min(100, threshold_pct))

    def set_burst_duration(self, duration_minutes: int) -> None:
        self.burst_duration_minutes = duration_minutes

    def get_stitch_by_burst(self, burst_id: str) -> Optional[Dict[str, Any]]:
        for s in self._network_stitches.values():
            if s.get("burst_id") == burst_id:
                return s
        return None

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class BurstScheduleConfig:
    schedule_id: str
    workload_name: str
    cron_expression: str
    target_capacity: int
    ttl_minutes: int = 120
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class BurstMetricsSnapshot:
    burst_id: str
    cpu_util_pct: float
    memory_util_pct: float
    network_throughput_mbps: float
    active_connections: int
    recorded_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ProviderBurstCapacity:
    provider: str
    region: str
    total_capacity: int
    available_capacity: int
    reserved_capacity: int = 0

# ── Batch Operation Helpers ─────────────────────────────────────────

    async def batch_update_workloads(self, updates: List[Tuple[str, int]]) -> Dict[str, Any]:
        succeeded = 0; failed = 0
        for wid, capacity in updates:
            if self.update_workload_capacity(wid, capacity):
                succeeded += 1
            else:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total": len(updates)}

    async def batch_create_network_stitches(self, stitch_configs: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for cfg in stitch_configs:
            s = self.create_network_stitch(cfg.get("on_prem_cidr", "10.0.0.0/8"),
                                           cfg.get("cloud_cidr", "172.16.0.0/12"),
                                           cfg.get("provider", "aws"), cfg.get("region", "us-east-1"))
            ids.append(s["id"])
        return ids

    async def batch_drain_bursts(self, burst_ids: List[str]) -> Dict[str, Any]:
        results = []
        for bid in burst_ids:
            r = await self.drain_burst(bid)
            results.append(r)
        return {"results": results, "total": len(burst_ids)}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_workloads(self, page: int = 1, page_size: int = 20,
                            sort_by: str = "priority", sort_desc: bool = True,
                            state_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._workloads.values())
        if state_filter:
            items = [w for w in items if w.state.value == state_filter]
        items.sort(key=lambda w: getattr(w, sort_by, 0), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [w.to_dict() for w in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_burst_history(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        items = sorted(self._burst_history, key=lambda x: x.get("started_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_workloads_to_json(self) -> str:
        return json.dumps([w.to_dict() for w in self._workloads.values()], indent=2)

    def import_workloads_from_json(self, json_str: str) -> int:
        data = json.loads(json_str)
        count = 0
        for entry in data:
            try:
                wl = BurstWorkload(entry.get("workload_id", str(uuid.uuid4())),
                                   entry["name"], entry["target_capacity"],
                                   entry.get("current_capacity", 0),
                                   entry.get("priority", 5), entry.get("tags", {}))
                self._workloads[wl.workload_id] = wl
                count += 1
            except (KeyError, ValueError):
                continue
        return count

    def export_stitches_to_json(self) -> str:
        return json.dumps(list(self._network_stitches.values()), indent=2)

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_burst_efficiency_analysis(self) -> Dict[str, Any]:
        if not self._burst_history:
            return {"total_bursts": 0, "avg_efficiency": 0}
        efficiencies = []
        for b in self._burst_history:
            allocated = b.get("cloud_resources_allocated", 0)
            workloads = b.get("workloads", [])
            if workloads:
                efficiencies.append(allocated / len(workloads))
        avg_eff = sum(efficiencies) / len(efficiencies) if efficiencies else 0
        return {"total_bursts": len(self._burst_history),
                "avg_efficiency": round(avg_eff, 2),
                "peak_efficiency": round(max(efficiencies), 2) if efficiencies else 0,
                "low_efficiency_bursts": sum(1 for e in efficiencies if e < 0.5)}

    def get_workload_priority_distribution(self) -> Dict[str, Any]:
        dist: Dict[str, int] = {}
        for w in self._workloads.values():
            key = f"priority_{w.priority}"
            dist[key] = dist.get(key, 0) + 1
        return {"distribution": dist, "total_workloads": len(self._workloads)}

    def get_capacity_forecast(self, days: int = 30) -> Dict[str, Any]:
        total_target = sum(w.target_capacity for w in self._workloads.values())
        total_current = sum(w.current_capacity for w in self._workloads.values())
        gap = max(0, total_target - total_current)
        return {"current_capacity": total_current, "target_capacity": total_target,
                "gap": gap, "estimated_cloud_needed": gap,
                "forecast_days": days, "daily_growth_rate": 0.05}

# ── State Machine / Workflow Logic ───────────────────────────────────

    async def burst_lifecycle_workflow(self, burst_id: str, action: str) -> Dict[str, Any]:
        transitions = {
            "scale_up": [BurstState.BURSTING, BurstState.SCALING_UP],
            "scale_down": [BurstState.BURSTING, BurstState.SCALING_DOWN],
            "drain": [BurstState.BURSTING, BurstState.SCALING_DOWN, BurstState.DRAINING, BurstState.COMPLETED],
            "fail": [BurstState.BURSTING, BurstState.SCALING_UP, BurstState.SCALING_DOWN, BurstState.FAILED],
        }
        burst = self._active_bursts.get(burst_id)
        if not burst:
            return {"status": "error", "message": "Burst not found"}
        if action not in transitions:
            return {"status": "error", "message": f"Unknown action: {action}"}
        burst["state"] = transitions[action][-1].value if action != "fail" else BurstState.FAILED.value
        return {"burst_id": burst_id, "action": action, "new_state": burst["state"]}

    async def scheduled_workload_sync(self) -> Dict[str, Any]:
        results = {"synced": 0, "skipped": 0}
        for wl in self._workloads.values():
            if wl.state in (BurstState.IDLE, BurstState.BURSTING):
                wl.updated_at = datetime.utcnow()
                results["synced"] += 1
            else:
                results["skipped"] += 1
        return results

# ── Configuration Validation ─────────────────────────────────────────

    def validate_burst_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.min_burst_threshold < 10 or self.min_burst_threshold > 100:
            errors.append("min_burst_threshold must be between 10 and 100")
        if self.max_burst_capacity <= 0:
            errors.append("max_burst_capacity must be positive")
        if self.drain_timeout_seconds < 30:
            warnings.append("drain_timeout_seconds is very low")
        if not self.config.get("cloud_subnet"):
            warnings.append("cloud_subnet not configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# ── Alerting ─────────────────────────────────────────────────────────

    def create_burst_alert(self, name: str, threshold_pct: int, metric: str = "utilization") -> Dict[str, Any]:
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        alert = {"id": alert_id, "name": name, "metric": metric,
                 "threshold_pct": threshold_pct, "active": True,
                 "created_at": datetime.utcnow().isoformat()}
        if "alerts" not in self.config:
            self.config["alerts"] = []
        self.config["alerts"].append(alert)
        return alert

    def list_burst_alerts(self) -> List[Dict[str, Any]]:
        return self.config.get("alerts", [])

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
