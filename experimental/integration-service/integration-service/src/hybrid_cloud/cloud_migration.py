import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DiscoveryMethod(Enum):
    AGENTLESS = "agentless"
    SSH = "ssh"
    WINRM = "winrm"
    SNMP = "snmp"
    API = "api"


class MigrationState(Enum):
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    MAPPED = "mapped"
    PLANNED = "planned"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class Workload:
    def __init__(self, name: str, hostname: str, os_type: str,
                 vcpu: int, memory_gb: int, storage_gb: int,
                 discovery_method: DiscoveryMethod = DiscoveryMethod.SSH):
        self.id = str(uuid.uuid4())
        self.name = name
        self.hostname = hostname
        self.os_type = os_type
        self.vcpu = vcpu
        self.memory_gb = memory_gb
        self.storage_gb = storage_gb
        self.discovery_method = discovery_method
        self.state = MigrationState.DISCOVERED
        self.dependencies: List[str] = []
        self.tags: Dict[str, str] = {}
        self.discovered_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "hostname": self.hostname,
                "os_type": self.os_type, "vcpu": self.vcpu,
                "memory_gb": self.memory_gb, "storage_gb": self.storage_gb,
                "discovery_method": self.discovery_method.value,
                "state": self.state.value, "dependencies": self.dependencies,
                "tags": self.tags, "discovered_at": self.discovered_at.isoformat()}


class MigrationWave:
    def __init__(self, name: str, workload_ids: List[str],
                 target_provider: str, target_region: str,
                 scheduled_start: Optional[datetime] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.workload_ids = workload_ids
        self.target_provider = target_provider
        self.target_region = target_region
        self.scheduled_start = scheduled_start
        self.state = MigrationState.PLANNED
        self.cutover_window_minutes = 60
        self.rollback_plan: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "workload_ids": self.workload_ids,
                "target_provider": self.target_provider,
                "target_region": self.target_region,
                "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
                "state": self.state.value, "created_at": self.created_at.isoformat()}


class CloudMigrationToolkit:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_concurrent_migrations = config.get("max_concurrent_migrations", 3)
        self.default_target_provider = config.get("default_target_provider", "aws")
        self.default_target_region = config.get("default_target_region", "us-east-1")
        self.auto_rollback = config.get("auto_rollback", True)
        self.discovery_timeout = config.get("discovery_timeout", 300)
        self._workloads: Dict[str, Workload] = {}
        self._waves: Dict[str, MigrationWave] = {}
        self._migration_log: List[Dict[str, Any]] = []
        self._discovery_results: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("CloudMigrationToolkit initialized")

    async def close(self) -> None:
        self._workloads.clear()
        self._waves.clear()
        logger.info("CloudMigrationToolkit closed")

    def discover_workload(self, name: str, hostname: str, os_type: str,
                          vcpu: int, memory_gb: int, storage_gb: int,
                          method: DiscoveryMethod = DiscoveryMethod.SSH) -> Workload:
        wl = Workload(name, hostname, os_type, vcpu, memory_gb, storage_gb, method)
        self._workloads[wl.id] = wl
        logger.info(f"Discovered workload {name} on {hostname}")
        return wl

    def get_workload(self, workload_id: str) -> Optional[Workload]:
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

    def add_dependency(self, workload_id: str, dependency_id: str) -> bool:
        wl = self._workloads.get(workload_id)
        dep = self._workloads.get(dependency_id)
        if not wl or not dep:
            return False
        if dependency_id not in wl.dependencies:
            wl.dependencies.append(dependency_id)
        return True

    def remove_dependency(self, workload_id: str, dependency_id: str) -> bool:
        wl = self._workloads.get(workload_id)
        if not wl:
            return False
        if dependency_id in wl.dependencies:
            wl.dependencies.remove(dependency_id)
        return True

    def get_dependency_graph(self) -> Dict[str, Any]:
        nodes = []
        edges = []
        for wl in self._workloads.values():
            nodes.append({"id": wl.id, "name": wl.name, "type": wl.os_type})
            for dep_id in wl.dependencies:
                edges.append({"from": wl.id, "to": dep_id, "type": "depends_on"})
        return {"nodes": nodes, "edges": edges}

    def create_wave(self, name: str, workload_ids: List[str],
                    target_provider: Optional[str] = None,
                    target_region: Optional[str] = None,
                    scheduled_start: Optional[datetime] = None) -> MigrationWave:
        tp = target_provider or self.default_target_provider
        tr = target_region or self.default_target_region
        wave = MigrationWave(name, workload_ids, tp, tr, scheduled_start)
        self._waves[wave.id] = wave
        for wid in workload_ids:
            wl = self._workloads.get(wid)
            if wl:
                wl.state = MigrationState.PLANNED
        logger.info(f"Migration wave '{name}' created with {len(workload_ids)} workloads")
        return wave

    def get_wave(self, wave_id: str) -> Optional[MigrationWave]:
        return self._waves.get(wave_id)

    def list_waves(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self._waves.values()]

    def delete_wave(self, wave_id: str) -> bool:
        if wave_id in self._waves:
            del self._waves[wave_id]
            return True
        return False

    async def execute_wave(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        wave.state = MigrationState.MIGRATING
        results = []
        for wid in wave.workload_ids:
            wl = self._workloads.get(wid)
            if not wl:
                continue
            wl.state = MigrationState.MIGRATING
            result = self._migrate_workload(wl, wave)
            results.append(result)
        successes = sum(1 for r in results if r["status"] == "completed")
        failures = sum(1 for r in results if r["status"] == "failed")
        if failures > 0 and self.auto_rollback:
            await self.rollback_wave(wave_id)
        wave.state = MigrationState.COMPLETED if failures == 0 else MigrationState.FAILED
        log_entry = {"wave_id": wave_id, "wave_name": wave.name,
                     "successful": successes, "failed": failures,
                     "completed_at": datetime.utcnow().isoformat()}
        self._migration_log.append(log_entry)
        return {"wave_id": wave_id, "results": results, "successful": successes, "failed": failures}

    def _migrate_workload(self, wl: Workload, wave: MigrationWave) -> Dict[str, Any]:
        migration_id = f"mig-{uuid.uuid4().hex[:10]}"
        success = True
        result = {"migration_id": migration_id, "workload_id": wl.id,
                  "workload_name": wl.name, "target_provider": wave.target_provider,
                  "target_region": wave.target_region,
                  "status": "completed" if success else "failed"}
        wl.state = MigrationState.COMPLETED if success else MigrationState.FAILED
        return result

    async def rollback_wave(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        wave.state = MigrationState.ROLLED_BACK
        for wid in wave.workload_ids:
            wl = self._workloads.get(wid)
            if wl:
                wl.state = MigrationState.ROLLED_BACK
        logger.info(f"Wave {wave_id} rolled back")
        return {"wave_id": wave_id, "status": "rolled_back"}

    def assess_workload(self, workload_id: str) -> Dict[str, Any]:
        wl = self._workloads.get(workload_id)
        if not wl:
            return {"status": "error", "message": "Workload not found"}
        compatibility = self._check_compatibility(wl)
        wl.state = MigrationState.ASSESSED
        return {"workload_id": wl.id, "workload_name": wl.name,
                "compatibility": compatibility, "recommended_instance": compatibility.get("instance_type"),
                "estimated_monthly_cost": compatibility.get("estimated_cost")}

    def _check_compatibility(self, wl: Workload) -> Dict[str, Any]:
        return {"compatible": True, "instance_type": f"t3.{self._size_map(wl.vcpu)}",
                "estimated_cost": round(wl.vcpu * 10 + wl.memory_gb * 2 + wl.storage_gb * 0.1, 2),
                "os_support": wl.os_type.lower() in ["linux", "windows", "ubuntu", "centos", "rhel"]}

    def _size_map(self, vcpu: int) -> str:
        if vcpu <= 1: return "nano"
        if vcpu <= 2: return "small"
        if vcpu <= 4: return "medium"
        if vcpu <= 8: return "large"
        return "xlarge"

    def get_migration_log(self) -> List[Dict[str, Any]]:
        return self._migration_log

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_workloads": len(self._workloads),
                "discovered": sum(1 for w in self._workloads.values() if w.state == MigrationState.DISCOVERED),
                "assessed": sum(1 for w in self._workloads.values() if w.state == MigrationState.ASSESSED),
                "planned": sum(1 for w in self._workloads.values() if w.state == MigrationState.PLANNED),
                "migrated": sum(1 for w in self._workloads.values() if w.state == MigrationState.COMPLETED),
                "total_waves": len(self._waves),
                "total_migrations": len(self._migration_log)}

    def create_workload(self, name: str, vcpu: int, memory_gb: int,
                         storage_gb: int, os_type: str = "linux",
                         dependencies: Optional[List[str]] = None) -> Workload:
        wl = Workload(name, vcpu, memory_gb, storage_gb, os_type, dependencies)
        self._workloads[wl.id] = wl
        return wl

    def delete_workload(self, workload_id: str) -> bool:
        if workload_id in self._workloads:
            del self._workloads[workload_id]
            return True
        return False

    def plan_wave(self, name: str, workload_ids: List[str]) -> MigrationWave:
        wave = MigrationWave(name, workload_ids)
        for wid in workload_ids:
            wl = self._workloads.get(wid)
            if wl:
                wl.state = MigrationState.PLANNED
        self._waves[wave.id] = wave
        return wave

    def execute_wave_plan(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        wave.state = MigrationState.IN_PROGRESS
        results = []
        for wid in wave.workload_ids:
            result = self.assess_workload(wid)
            results.append(result)
        return {"wave_id": wave_id, "wave_name": wave.name,
                "workload_count": len(wave.workload_ids),
                "results": results, "status": "planned"}

    def get_wave_status(self, wave_id: str) -> Optional[Dict[str, Any]]:
        wave = self._waves.get(wave_id)
        return wave.to_dict() if wave else None

    def list_waves(self, state: Optional[MigrationState] = None) -> List[Dict[str, Any]]:
        if state:
            return [w.to_dict() for w in self._waves.values() if w.state == state]
        return [w.to_dict() for w in self._waves.values()]

    def dependency_map(self) -> Dict[str, Any]:
        deps = {}
        for wl_id, wl in self._workloads.items():
            deps[wl_id] = {"name": wl.name, "dependencies": wl.dependencies or []}
        return {"workloads": deps, "total_workloads": len(self._workloads)}

    def add_migration_log(self, workload_id: str, action: str,
                           status: str, details: str = "") -> None:
        entry = {"log_id": str(uuid.uuid4()), "workload_id": workload_id,
                 "action": action, "status": status, "details": details,
                 "timestamp": datetime.utcnow().isoformat()}
        self._migration_log.append(entry)

    def get_detected_workloads(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self._workloads.values()
                if w.state == MigrationState.DISCOVERED]

    def update_workload_specs(self, workload_id: str, vcpu: Optional[int] = None,
                               memory_gb: Optional[int] = None,
                               storage_gb: Optional[int] = None) -> bool:
        wl = self._workloads.get(workload_id)
        if not wl:
            return False
        if vcpu is not None: wl.vcpu = vcpu
        if memory_gb is not None: wl.memory_gb = memory_gb
        if storage_gb is not None: wl.storage_gb = storage_gb
        return True

    def export_migration_plan(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(),
                "total_workloads": len(self._workloads),
                "total_waves": len(self._waves),
                "workloads": [w.to_dict() for w in self._workloads.values()],
                "waves": [w.to_dict() for w in self._waves.values()],
                "migration_log_count": len(self._migration_log)}

    def get_cutover_readiness(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        assessed = sum(1 for wid in wave.workload_ids
                       if self._workloads.get(wid, None) and 
                       self._workloads[wid].state == MigrationState.ASSESSED)
        total = len(wave.workload_ids)
        return {"wave_id": wave_id, "wave_name": wave.name,
                "assessed": assessed, "total": total,
                "readiness_pct": round(assessed / total * 100, 1) if total > 0 else 0,
                "ready_for_cutover": assessed == total}

    def batch_discover_workloads(self, workloads: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for w in workloads:
            wl = self.discover_workload(w.get("name", "unknown"), w.get("hostname", "localhost"),
                                        w.get("os_type", "linux"), w.get("vcpu", 2),
                                        w.get("memory_gb", 4), w.get("storage_gb", 50),
                                        DiscoveryMethod(w.get("discovery_method", "ssh")))
            if w.get("tags"):
                wl.tags = w["tags"]
            ids.append(wl.id)
        return ids

    def estimate_migration_cost(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        total_cost = 0.0
        for wid in wave.workload_ids:
            wl = self._workloads.get(wid)
            if wl:
                total_cost += wl.vcpu * 10 + wl.memory_gb * 2 + wl.storage_gb * 0.1
        return {"wave_id": wave_id, "wave_name": wave.name,
                "estimated_cost": round(total_cost, 2),
                "workload_count": len(wave.workload_ids)}

    def get_migration_timeline(self, wave_id: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        estimated_hours = len(wave.workload_ids) * 2
        return {"wave_id": wave_id, "wave_name": wave.name,
                "estimated_hours": estimated_hours,
                "workload_count": len(wave.workload_ids),
                "parallel_batches": max(1, len(wave.workload_ids) // self.max_concurrent_migrations)}

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class MigrationChecklist:
    wave_id: str
    items: List[str] = field(default_factory=list)
    completed: List[str] = field(default_factory=list)

    def progress(self) -> float:
        return round(len(self.completed) / max(len(self.items), 1) * 100, 1)

@dataclass
class CutoverWindow:
    wave_id: str
    planned_start: datetime
    planned_end: datetime
    actual_start: Optional[datetime] = None
    status: str = "scheduled"

@dataclass
class MigrationValidationResult:
    workload_id: str
    validation_type: str
    passed: bool
    details: str = ""
    validated_at: datetime = field(default_factory=datetime.utcnow)

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_discover_workloads(self, workload_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        ids = []
        for w in workload_list:
            wl = self.discover_workload(w.get("name", "unknown"), w.get("hostname", "localhost"),
                                        w.get("os_type", "linux"), w.get("vcpu", 2),
                                        w.get("memory_gb", 4), w.get("storage_gb", 50),
                                        DiscoveryMethod(w.get("discovery_method", "ssh")))
            if w.get("tags"):
                wl.tags = w["tags"]
            ids.append(wl.id)
        return {"discovered": len(ids), "workload_ids": ids}

    async def batch_assess_workloads(self, workload_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for wid in workload_ids:
            results[wid] = self.assess_workload(wid)
        return {"results": results, "total": len(workload_ids)}

    async def batch_execute_waves(self, wave_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for wid in wave_ids:
            results[wid] = await self.execute_wave(wid)
        return {"results": results, "total": len(wave_ids)}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_workloads(self, page: int = 1, page_size: int = 20,
                            sort_by: str = "discovered_at", sort_desc: bool = True,
                            state_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._workloads.values())
        if state_filter:
            items = [w for w in items if w.state.value == state_filter]
        items.sort(key=lambda w: getattr(w, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [w.to_dict() for w in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_waves(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        items = sorted([w.to_dict() for w in self._waves.values()], key=lambda w: w.get("created_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_migration_readiness_report(self) -> str:
        return json.dumps({
            "generated_at": datetime.utcnow().isoformat(),
            "workloads": [w.to_dict() for w in self._workloads.values()],
            "waves": [w.to_dict() for w in self._waves.values()],
            "statistics": self.get_statistics(),
        }, indent=2)

    def export_wave_plan(self, wave_id: str) -> str:
        wave = self._waves.get(wave_id)
        if not wave:
            return json.dumps({"error": "Wave not found"})
        wave_workloads = [self._workloads.get(wid) for wid in wave.workload_ids if self._workloads.get(wid)]
        return json.dumps({
            "wave": wave.to_dict(),
            "workloads": [w.to_dict() for w in wave_workloads],
            "dependencies": self.get_dependency_graph(),
            "cutover_readiness": self.get_cutover_readiness(wave_id),
            "estimated_cost": self.estimate_migration_cost(wave_id),
        }, indent=2)

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_migration_readiness_score(self) -> Dict[str, Any]:
        total = len(self._workloads)
        assessed = sum(1 for w in self._workloads.values() if w.state == MigrationState.ASSESSED)
        planned = sum(1 for w in self._workloads.values() if w.state == MigrationState.PLANNED)
        return {
            "score": round((assessed + planned) / max(total, 1) * 100, 1),
            "total_workloads": total, "assessed": assessed,
            "planned": planned, "remaining": total - assessed - planned,
        }

    def get_dependency_risk_analysis(self) -> Dict[str, Any]:
        circular_deps = 0
        high_dep_workloads = 0
        for wl in self._workloads.values():
            if len(wl.dependencies) > 3:
                high_dep_workloads += 1
        for wl in self._workloads.values():
            visited = set()
            stack = list(wl.dependencies)
            while stack:
                dep_id = stack.pop()
                if dep_id == wl.id:
                    circular_deps += 1
                    break
                if dep_id in visited:
                    continue
                visited.add(dep_id)
                dep = self._workloads.get(dep_id)
                if dep:
                    stack.extend(dep.dependencies)
        return {
            "high_dependency_workloads": high_dep_workloads,
            "circular_dependencies": circular_deps,
            "workloads_with_deps": sum(1 for w in self._workloads.values() if w.dependencies),
        }

# ── State Machine / Workflow ─────────────────────────────────────────

    async def wave_lifecycle_workflow(self, wave_id: str, action: str) -> Dict[str, Any]:
        wave = self._waves.get(wave_id)
        if not wave:
            return {"status": "error", "message": "Wave not found"}
        if action == "start":
            return await self.execute_wave(wave_id)
        elif action == "assess":
            results = []
            for wid in wave.workload_ids:
                results.append(self.assess_workload(wid))
            return {"wave_id": wave_id, "action": "assess", "results": results}
        elif action == "rollback":
            return await self.rollback_wave(wave_id)
        elif action == "plan":
            return {"wave_id": wave_id, "action": "plan",
                    "estimated_cost": self.estimate_migration_cost(wave_id),
                    "timeline": self.get_migration_timeline(wave_id)}
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_discovery_workflow(self) -> Dict[str, Any]:
        return {"workloads_found": len(self._workloads), "status": "completed"}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_migration_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.max_concurrent_migrations < 1:
            errors.append("max_concurrent_migrations must be >= 1")
        if self.discovery_timeout < 30:
            warnings.append("discovery_timeout is very low")
        if not self._workloads:
            warnings.append("No workloads discovered yet")
        if self.auto_rollback and not any(w.state == MigrationState.PLANNED for w in self._workloads.values()):
            warnings.append("auto_rollback enabled but no planned migrations")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                "workload_count": len(self._workloads)}

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
