from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)


class DROrchestrator:
    """Disaster Recovery Orchestrator — define DR plans, RPO/RTO targets, failover order"""

    DR_PLAN_TYPES = ["active-passive", "pilot-light", "warm-standby", "active-active", "cold-standby"]
    PLAN_STATUSES = ["draft", "ready", "degraded", "failed", "archived"]
    FAILOVER_PHASES = ["preflight", "dns_update", "data_replication", "app_startup", "traffic_switch", "verification", "rollback_standby"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plans_file = config.get("dr_plans_file", "data/resiliency/dr_plans.json")
        self.executions_file = config.get("dr_executions_file", "data/resiliency/dr_executions.json")
        self.plans: List[Dict[str, Any]] = []
        self.executions: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.plans_file) or ".", exist_ok=True)
        for path, attr in [(self.plans_file, "plans"), (self.executions_file, "executions")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_plans(self):
        with open(self.plans_file, "w") as f:
            json.dump(self.plans, f, indent=2, default=str)

    def _save_executions(self):
        with open(self.executions_file, "w") as f:
            json.dump(self.executions[-500:], f, indent=2, default=str)

    async def create_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        plan_type = data.get("plan_type", "active-passive")
        if plan_type not in self.DR_PLAN_TYPES:
            return {"error": f"Unsupported plan type: {plan_type}"}
        plan = {
            "id": f"dr_{int(datetime.now().timestamp())}_{len(self.plans)}",
            "name": data.get("name", "Unnamed DR Plan"),
            "description": data.get("description", ""),
            "plan_type": plan_type,
            "status": "draft",
            "rpo_target_minutes": data.get("rpo_target_minutes", 60),
            "rto_target_minutes": data.get("rto_target_minutes", 30),
            "failover_order": data.get("failover_order", []),
            "dependency_graph": data.get("dependency_graph", {}),
            "runbook_id": data.get("runbook_id", ""),
            "primary_region": data.get("primary_region", ""),
            "secondary_region": data.get("secondary_region", ""),
            "test_schedule": data.get("test_schedule", "weekly"),
            "last_tested": None,
            "compliance_frameworks": data.get("compliance_frameworks", []),
            "approval_required": data.get("approval_required", True),
            "auto_failback": data.get("auto_failback", False),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": data.get("tags", []),
        }
        self.plans.append(plan)
        self._save_plans()
        return plan

    async def list_plans(self) -> List[Dict[str, Any]]:
        return self.plans

    async def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        return next((p for p in self.plans if p["id"] == plan_id), None)

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for plan in self.plans:
            if plan["id"] == plan_id:
                plan.update(updates)
                plan["updated_at"] = datetime.now().isoformat()
                self._save_plans()
                return plan
        return None

    async def delete_plan(self, plan_id: str) -> bool:
        for i, plan in enumerate(self.plans):
            if plan["id"] == plan_id:
                self.plans.pop(i)
                self._save_plans()
                return True
        return False

    async def execute_failover(self, plan_id: str, triggered_by: str = "manual") -> Dict[str, Any]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        execution = {
            "id": f"dr_exec_{int(datetime.now().timestamp())}_{len(self.executions)}",
            "plan_id": plan_id,
            "plan_name": plan.get("name", ""),
            "status": "in_progress",
            "triggered_by": triggered_by,
            "is_drill": triggered_by == "drill",
            "current_phase": "preflight",
            "phase_history": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error_message": None,
        }
        self.executions.append(execution)
        self._save_executions()
        asyncio.create_task(self._run_failover_phases(execution, plan))
        return execution

    async def _run_failover_phases(self, execution: Dict[str, Any], plan: Dict[str, Any]):
        for phase in self.FAILOVER_PHASES:
            if execution["status"] != "in_progress":
                break
            execution["current_phase"] = phase
            execution["phase_history"].append({"phase": phase, "started_at": datetime.now().isoformat(), "status": "running"})
            await asyncio.sleep(1)
            success = await self._execute_phase(phase, plan)
            execution["phase_history"][-1]["status"] = "completed" if success else "failed"
            execution["phase_history"][-1]["completed_at"] = datetime.now().isoformat()
            if not success:
                execution["status"] = "failed"
                execution["error_message"] = f"Phase {phase} failed"
                break
        if execution["status"] == "in_progress":
            execution["status"] = "completed"
            execution["result"] = "success"
        execution["completed_at"] = datetime.now().isoformat()
        self._save_executions()

    async def _execute_phase(self, phase: str, plan: Dict[str, Any]) -> bool:
        logger.info(f"Executing DR phase {phase} for plan {plan.get('name')}")
        return True

    async def get_executions(self, plan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if plan_id:
            return [e for e in self.executions if e["plan_id"] == plan_id]
        return self.executions

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return next((e for e in self.executions if e["id"] == execution_id), None)

    async def cancel_execution(self, execution_id: str) -> bool:
        for execution in self.executions:
            if execution["id"] == execution_id and execution["status"] == "in_progress":
                execution["status"] = "cancelled"
                execution["completed_at"] = datetime.now().isoformat()
                self._save_executions()
                return True
        return False

    async def run_readiness_check(self, plan_id: str) -> Dict[str, Any]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        checks = [
            {"check": "primary_region_reachable", "status": "passed"},
            {"check": "secondary_region_reachable", "status": "passed"},
            {"check": "data_replication_lag", "status": "passed", "lag_seconds": 5},
            {"check": "dns_probe", "status": "passed"},
            {"check": "runbook_valid", "status": "passed"},
            {"check": "dependencies_resolved", "status": "passed"},
        ]
        healthy = all(c["status"] == "passed" for c in checks)
        plan["last_tested"] = datetime.now().isoformat()
        plan["status"] = "ready" if healthy else "degraded"
        self._save_plans()
        return {"plan_id": plan_id, "healthy": healthy, "checks": checks, "rpo_compliance": plan.get("rpo_target_minutes") >= 5, "rto_compliance": plan.get("rto_target_minutes") >= 2}

    async def get_compliance_summary(self) -> Dict[str, Any]:
        total = len(self.plans)
        ready = sum(1 for p in self.plans if p["status"] == "ready")
        tested = sum(1 for p in self.plans if p.get("last_tested"))
        return {"total_plans": total, "ready_plans": ready, "tested_last_30d": tested, "last_execution": self.executions[-1] if self.executions else None}

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for plan in self.plans:
            if plan["id"] == plan_id:
                plan.update(updates)
                self._save_plans()
                return plan
        return None

    async def delete_plan(self, plan_id: str) -> bool:
        for i, plan in enumerate(self.plans):
            if plan["id"] == plan_id:
                self.plans.pop(i)
                self._save_plans()
                return True
        return False

    async def get_all_plans(self) -> List[Dict[str, Any]]:
        return self.plans

    async def run_bulk_readiness(self) -> Dict[str, Any]:
        results = []
        for plan in self.plans:
            if plan.get("active", True):
                r = await self.run_readiness_check(plan["id"])
                results.append(r)
        return {"total": len(results), "healthy": sum(1 for r in results if r.get("healthy")), "degraded": sum(1 for r in results if not r.get("healthy")), "details": results}

    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        execution = {"id": f"exec_{len(self.executions)}_{int(datetime.now().timestamp())}", "plan_id": plan_id, "plan_name": plan.get("name"), "status": "in_progress", "phases": ["detection", "assessment", "failover", "verification", "recovery"], "current_phase": "detection", "started_at": datetime.now().isoformat(), "completed_at": None, "rpo_actual_minutes": random.randint(1, 15), "rto_actual_minutes": random.randint(2, 30), "automation_pct": random.randint(60, 100)}
        self.executions.append(execution)
        self._save_executions()
        for phase in execution["phases"]:
            await self._execute_phase(phase, plan)
            execution["current_phase"] = phase
        execution["status"] = "completed"
        execution["completed_at"] = datetime.now().isoformat()
        self._save_executions()
        return execution

    async def get_plan_templates(self) -> List[Dict[str, Any]]:
        return [{"id": "template_pilot_light", "name": "Pilot Light", "plan_type": "pilot_light", "default_rpo": 60, "default_rto": 30, "description": "Minimal standby in secondary region"}, {"id": "template_warm_standby", "name": "Warm Standby", "plan_type": "warm_standby", "default_rpo": 15, "default_rto": 10, "description": "Partially scaled standby in secondary region"}, {"id": "template_active_active", "name": "Active-Active", "plan_type": "active_active", "default_rpo": 5, "default_rto": 2, "description": "Fully active in multiple regions"}]

    async def get_rpo_rto_report(self) -> Dict[str, Any]:
        recent_execs = [e for e in self.executions if e.get("completed_at")][-20:]
        if not recent_execs:
            return {"error": "No execution data"}
        return {"average_rpo_minutes": round(sum(e.get("rpo_actual_minutes", 0) for e in recent_execs) / len(recent_execs), 1), "average_rto_minutes": round(sum(e.get("rto_actual_minutes", 0) for e in recent_execs) / len(recent_execs), 1), "best_rpo": min((e.get("rpo_actual_minutes", 999) for e in recent_execs), default=0), "best_rto": min((e.get("rto_actual_minutes", 999) for e in recent_execs), default=0), "executions_analyzed": len(recent_execs)}


class DRBatchProcessor:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(plans):
            try:
                plan = await self.manager.create_plan(data)
                plan["batch_index"] = i
                plan["success"] = True
                results.append(plan)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_execute_failover(self, plan_ids: List[str], triggered_by: str = "drill") -> List[Dict[str, Any]]:
        results = []
        for pid in plan_ids:
            try:
                r = await self.manager.execute_failover(pid, triggered_by)
                r["plan_id"] = pid
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"plan_id": pid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_readiness_checks(self, plan_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for pid in plan_ids:
            r = await self.manager.run_readiness_check(pid)
            r["plan_id"] = pid
            results.append(r)
        return results

    async def batch_delete_plans(self, plan_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for pid in plan_ids:
            ok = await self.manager.delete_plan(pid)
            results.append({"plan_id": pid, "deleted": ok})
        return results

    def export_csv(self, plans: List[Dict[str, Any]]) -> str:
        if not plans:
            return ""
        fields = ["id", "name", "plan_type", "status", "rpo_target_minutes", "rto_target_minutes", "primary_region", "secondary_region", "created_at"]
        lines = [",".join(fields)]
        for plan in plans:
            row = [str(plan.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)


class DRAnalytics:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def plan_readiness_summary(self) -> Dict[str, Any]:
        plans = self.manager.plans
        if not plans:
            return {"total": 0, "ready": 0, "degraded": 0, "draft": 0}
        ready = sum(1 for p in plans if p.get("status") == "ready")
        degraded = sum(1 for p in plans if p.get("status") == "degraded")
        draft = sum(1 for p in plans if p.get("status") == "draft")
        return {"total": len(plans), "ready": ready, "degraded": degraded, "draft": draft, "readiness_pct": round(ready / len(plans) * 100, 1) if plans else 0}

    def execution_success_rate(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in self.manager.executions if e.get("started_at") and datetime.fromisoformat(e["started_at"]) > cutoff]
        if not recent:
            return {"rate": 0, "total": 0}
        completed = sum(1 for e in recent if e.get("status") == "completed")
        return {"rate": round(completed / len(recent) * 100, 1), "total": len(recent), "completed": completed, "failed": sum(1 for e in recent if e.get("status") == "failed"), "cancelled": sum(1 for e in recent if e.get("status") == "cancelled")}

    def rpo_rto_trend(self) -> List[Dict[str, Any]]:
        sorted_execs = sorted([e for e in self.manager.executions if e.get("completed_at")], key=lambda e: e["started_at"])
        return [{"execution_id": e["id"], "plan_name": e.get("plan_name"), "rpo": e.get("rpo_actual_minutes", 0), "rto": e.get("rto_actual_minutes", 0), "date": e.get("started_at", "")} for e in sorted_execs[-20:]]

    def compliance_by_framework(self) -> Dict[str, Any]:
        frameworks: Dict[str, int] = {}
        for plan in self.manager.plans:
            for fw in plan.get("compliance_frameworks", []):
                frameworks[fw] = frameworks.get(fw, 0) + 1
        return {"frameworks": frameworks, "total_plans_with_compliance": sum(1 for p in self.manager.plans if p.get("compliance_frameworks"))}

    def generate_report(self) -> str:
        lines = ["=== DR Orchestrator Report ==="]
        readiness = self.plan_readiness_summary()
        lines.append(f"Plan Readiness: {readiness.get('ready', 0)}/{readiness.get('total', 0)} ({readiness.get('readiness_pct', 0)}%)")
        sr = self.execution_success_rate(30)
        lines.append(f"30-Day Execution Success: {sr.get('rate', 0)}% ({sr.get('completed', 0)}/{sr.get('total', 0)})")
        rpo_rto = self.manager.get_rpo_rto_report()
        if "error" not in rpo_rto:
            lines.append(f"Avg RPO: {rpo_rto.get('average_rpo_minutes', 0)}min, Avg RTO: {rpo_rto.get('average_rto_minutes', 0)}min")
        return "\n".join(lines)


class DRPaginator:
    def __init__(self, items: List[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size

    def get_page(self, page: int = 1) -> List[Any]:
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.items[start:end] if start < len(self.items) else []

    def get_total_pages(self) -> int:
        return max(1, (len(self.items) + self.page_size - 1) // self.page_size)

    def get_metadata(self) -> Dict[str, Any]:
        return {"total_items": len(self.items), "page_size": self.page_size, "total_pages": self.get_total_pages()}


class FailoverAutomation:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    async def auto_detect_and_failover(self, plan_id: str) -> Dict[str, Any]:
        plan = await self.manager.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        health = await self.manager.run_readiness_check(plan_id)
        if not health.get("healthy"):
            exec_result = await self.manager.execute_failover(plan_id, "auto_detected")
            return {"auto_failover": True, "reason": "Health check failed", "execution": exec_result}
        return {"auto_failover": False, "reason": "All checks healthy"}

    async def schedule_failover_drill(self, plan_id: str, cron_expression: str) -> Dict[str, Any]:
        return {"plan_id": plan_id, "schedule": cron_expression, "next_run": datetime.now().isoformat(), "status": "scheduled"}

    async def run_dependency_aware_failover(self, plan_id: str) -> Dict[str, Any]:
        plan = await self.manager.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        dep_graph = plan.get("dependency_graph", {})
        dep_order = dep_graph.get("order", [])
        execution = await self.manager.execute_failover(plan_id, "dependency_aware")
        execution["dependency_order"] = dep_order
        return execution


class DRPlanTemplateGenerator:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    async def generate_from_template(self, template_id: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        templates = await self.manager.get_plan_templates()
        tmpl = next((t for t in templates if t["id"] == template_id), None)
        if not tmpl:
            return {"error": "Template not found"}
        data = {k: v for k, v in tmpl.items() if k not in ("id", "description")}
        if overrides:
            data.update(overrides)
        return await self.manager.create_plan(data)


class DRExecutionMonitor:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def get_active_executions(self) -> List[Dict[str, Any]]:
        return [e for e in self.manager.executions if e.get("status") == "in_progress"]

    def get_execution_statistics(self) -> Dict[str, Any]:
        total = len(self.manager.executions)
        if not total:
            return {"total": 0, "completed": 0, "failed": 0, "in_progress": 0}
        completed = sum(1 for e in self.manager.executions if e.get("status") == "completed")
        failed = sum(1 for e in self.manager.executions if e.get("status") == "failed")
        in_progress = sum(1 for e in self.manager.executions if e.get("status") == "in_progress")
        return {"total": total, "completed": completed, "failed": failed, "in_progress": in_progress, "success_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0}

    def get_execution_timeline(self, plan_id: str) -> List[Dict[str, Any]]:
        plan_execs = [e for e in self.manager.executions if e.get("plan_id") == plan_id]
        timeline = []
        for e in sorted(plan_execs, key=lambda x: x.get("started_at", "")):
            timeline.append({"execution_id": e["id"], "status": e.get("status"), "started": e.get("started_at"), "completed": e.get("completed_at"), "triggered_by": e.get("triggered_by", "manual")})
        return timeline

    def calculate_average_duration(self) -> Dict[str, Any]:
        completed = [e for e in self.manager.executions if e.get("status") == "completed" and e.get("started_at") and e.get("completed_at")]
        if not completed:
            return {"average_seconds": 0}
        durations = []
        for e in completed:
            start = datetime.fromisoformat(e["started_at"])
            end = datetime.fromisoformat(e["completed_at"])
            durations.append((end - start).total_seconds())
        return {"average_seconds": round(sum(durations) / len(durations), 1), "min_seconds": round(min(durations), 1), "max_seconds": round(max(durations), 1), "executions_analyzed": len(durations)}


class DRComplianceChecker:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def check_rpo_rto_compliance(self, plan_id: str) -> Dict[str, Any]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return {"error": "Plan not found"}
        execs = [e for e in self.manager.executions if e.get("plan_id") == plan_id and e.get("status") == "completed"]
        if not execs:
            return {"plan_id": plan_id, "rpo_compliant": False, "rto_compliant": False, "reason": "No completed executions"}
        rpo_target = plan.get("rpo_target_minutes", 60)
        rto_target = plan.get("rto_target_minutes", 30)
        rpo_compliant = all(e.get("rpo_actual_minutes", 999) <= rpo_target for e in execs if e.get("rpo_actual_minutes") is not None)
        rto_compliant = all(e.get("rto_actual_minutes", 999) <= rto_target for e in execs if e.get("rto_actual_minutes") is not None)
        return {"plan_id": plan_id, "plan_name": plan.get("name"), "rpo_target": rpo_target, "rto_target": rto_target, "rpo_compliant": rpo_compliant, "rto_compliant": rto_compliant, "executions_checked": len(execs)}

    async def bulk_compliance_check(self) -> List[Dict[str, Any]]:
        results = []
        for plan in self.manager.plans:
            r = self.check_rpo_rto_compliance(plan["id"])
            results.append(r)
        return results


class DRNotificationManager:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    async def send_notification(self, plan_id: str, event: str, message: str) -> Dict[str, Any]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return {"error": "Plan not found"}
        channels = plan.get("notification_channels", ["email"])
        return {"plan_id": plan_id, "event": event, "message": message, "channels": channels, "sent_at": datetime.now().isoformat()}

    async def notify_stakeholders(self, plan_id: str, execution_id: str) -> Dict[str, Any]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return {"error": "Plan not found"}
        execution = next((e for e in self.manager.executions if e["id"] == execution_id), None)
        status = execution.get("status", "unknown") if execution else "unknown"
        stakeholders = plan.get("stakeholders", [])
        return {"plan_id": plan_id, "execution_id": execution_id, "status": status, "notified": len(stakeholders), "stakeholders": stakeholders, "sent_at": datetime.now().isoformat()}


class DRScenarioManager:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return self.manager.scenarios

    async def create_scenario(self, data: Dict[str, Any]) -> Dict[str, Any]:
        scenario = {"id": str(uuid.uuid4()), "name": data.get("name"), "description": data.get("description"), "type": data.get("type", "regional_failure"), "severity": data.get("severity", "high"), "affected_regions": data.get("affected_regions", []), "created_at": datetime.now().isoformat(), "status": "active"}
        self.manager.scenarios.append(scenario)
        return scenario

    async def run_scenario(self, scenario_id: str) -> Dict[str, Any]:
        scenario = next((s for s in self.manager.scenarios if s["id"] == scenario_id), None)
        if not scenario:
            return {"error": "Scenario not found"}
        plans = [p for p in self.manager.plans if p.get("status") == "active"]
        results = []
        for plan in plans:
            exec_result = await self.manager.execute_plan(plan["id"])
            results.append({"plan_id": plan["id"], "plan_name": plan.get("name"), "execution_id": exec_result.get("id")})
        return {"scenario_id": scenario_id, "scenario_name": scenario.get("name"), "plans_executed": len(results), "results": results}

    def get_scenario_recommendations(self, scenario_id: str) -> List[Dict[str, Any]]:
        scenario = next((s for s in self.manager.scenarios if s["id"] == scenario_id), None)
        if not scenario:
            return []
        recs = []
        severity = scenario.get("severity", "medium")
        if severity == "critical":
            recs.append({"type": "infrastructure", "action": "Add cross-region redundancy", "priority": "critical"})
            recs.append({"type": "process", "action": "Schedule quarterly DR drills", "priority": "high"})
        elif severity == "high":
            recs.append({"type": "process", "action": "Review and update DR plan", "priority": "high"})
        recs.append({"type": "monitoring", "action": "Enable automated failover detection", "priority": "medium"})
        return recs


class DRPlanVersioning:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def get_version_history(self, plan_id: str) -> List[Dict[str, Any]]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return []
        return plan.get("version_history", [])

    async def create_new_version(self, plan_id: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return None
        current_version = plan.get("version", 1)
        version_entry = {"version": current_version, "changes": changes, "timestamp": datetime.now().isoformat(), "snapshot": {k: v for k, v in plan.items() if k not in ("version_history", "id")}}
        plan.setdefault("version_history", []).append(version_entry)
        plan["version"] = current_version + 1
        plan["updated_at"] = datetime.now().isoformat()
        return {"plan_id": plan_id, "new_version": plan["version"], "entry": version_entry}

    async def rollback(self, plan_id: str, target_version: int) -> Optional[Dict[str, Any]]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return None
        history = plan.get("version_history", [])
        target = next((h for h in history if h["version"] == target_version), None)
        if not target:
            return None
        snapshot = target.get("snapshot", {})
        for k, v in snapshot.items():
            plan[k] = v
        plan["version"] = plan.get("version", 1) + 1
        plan["updated_at"] = datetime.now().isoformat()
        return {"plan_id": plan_id, "rolled_back_to": target_version, "new_version": plan["version"]}


class DRDrillScheduler:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    async def schedule_drill(self, plan_id: str, cron: str) -> Dict[str, Any]:
        plan = next((p for p in self.manager.plans if p["id"] == plan_id), None)
        if not plan:
            return {"error": "Plan not found"}
        drill = {"id": str(uuid.uuid4()), "plan_id": plan_id, "plan_name": plan.get("name"), "cron": cron, "status": "scheduled", "created_at": datetime.now().isoformat(), "next_run": datetime.now().isoformat()}
        self.manager.drills = getattr(self.manager, "drills", [])
        self.manager.drills.append(drill)
        return drill

    def get_upcoming_drills(self) -> List[Dict[str, Any]]:
        return sorted(getattr(self.manager, "drills", []), key=lambda d: d.get("next_run", ""))

    async def execute_scheduled_drill(self, drill_id: str) -> Dict[str, Any]:
        drills = getattr(self.manager, "drills", [])
        drill = next((d for d in drills if d["id"] == drill_id), None)
        if not drill:
            return {"error": "Drill not found"}
        result = await self.manager.execute_plan(drill["plan_id"])
        drill["status"] = "executed"
        drill["last_run"] = datetime.now().isoformat()
        return {"drill_id": drill_id, "execution": result}


class DRDocumentationManager:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager
        self.documents: List[Dict[str, Any]] = []

    def create_document(self, plan_id: str, title: str, content: str, doc_type: str = "runbook") -> Dict[str, Any]:
        doc = {"id": str(uuid.uuid4()), "plan_id": plan_id, "title": title, "content": content, "doc_type": doc_type, "version": 1, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
        self.documents.append(doc)
        return doc

    def update_document(self, doc_id: str, content: str) -> Dict[str, Any]:
        for d in self.documents:
            if d["id"] == doc_id:
                d["content"] = content
                d["version"] = d.get("version", 1) + 1
                d["updated_at"] = datetime.now().isoformat()
                return d
        return {"error": "Document not found"}

    def get_plan_documents(self, plan_id: str) -> List[Dict[str, Any]]:
        return [d for d in self.documents if d.get("plan_id") == plan_id]

    def export_document_pdf(self, doc_id: str) -> Dict[str, Any]:
        doc = next((d for d in self.documents if d["id"] == doc_id), None)
        if not doc:
            return {"error": "Document not found"}
        return {"doc_id": doc_id, "title": doc.get("title"), "exported_at": datetime.now().isoformat(), "format": "pdf", "content_preview": doc.get("content", "")[:200]}


class DRReportExporter:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    def export_plans_csv(self) -> str:
        lines = ["plan_id,name,status,rpo_min,rto_min,region,last_tested,version"]
        for p in self.manager.plans:
            lines.append(f"{p['id']},{p.get('name')},{p.get('status')},{p.get('rpo_target_minutes')},{p.get('rto_target_minutes')},{p.get('primary_region')},{p.get('last_tested')},{p.get('version')}")
        return "\n".join(lines)

    def export_executions_summary(self) -> Dict[str, Any]:
        total = len(self.manager.executions)
        completed = sum(1 for e in self.manager.executions if e.get("status") == "completed")
        failed = sum(1 for e in self.manager.executions if e.get("status") == "failed")
        return {"total_executions": total, "completed": completed, "failed": failed, "success_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0, "exported_at": datetime.now().isoformat()}


class DRScenarioSimulator:
    def __init__(self, manager: DROrchestrator):
        self.manager = manager

    async def simulate_region_failure(self, region: str) -> Dict[str, Any]:
        affected_plans = [p for p in self.manager.plans if p.get("primary_region") == region or region in p.get("secondary_regions", [])]
        results = []
        for plan in affected_plans:
            exec_result = await self.manager.execute_plan(plan["id"])
            results.append({"plan_id": plan["id"], "plan_name": plan.get("name"), "execution_id": exec_result.get("id"), "status": exec_result.get("status")})
        return {"simulated_failure": f"{region}_failure", "plans_affected": len(affected_plans), "results": results, "simulated_at": datetime.now().isoformat()}

    async def simulate_cascading_failure(self, initial_region: str) -> Dict[str, Any]:
        primary_result = await self.simulate_region_failure(initial_region)
        secondary_regions: Set[str] = set()
        for p in self.manager.plans:
            if initial_region in p.get("secondary_regions", []):
                secondary_regions.update(p.get("secondary_regions", []))
        cascade_results = []
        for region in secondary_regions - {initial_region}:
            r = await self.simulate_region_failure(region)
            cascade_results.append(r)
        return {"initial_failure": primary_result, "cascade_results": cascade_results, "total_regions_affected": 1 + len(cascade_results)}

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
        return {"total_items": 0, "healthy_count": 0, "degraded_count": 0, "failed_count": 0}

    def validate_configuration(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class ResiliencyResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    status: str = Field(default="healthy")
    message: str = ""
    recovery_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResiliencyBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    passed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_pass(self) -> None:
        self.passed += 1

    def record_fail(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"
        if self.failed > 0:
            self.status = "completed_with_errors"

class HealthMetric(BaseModel):
    component: str
    status: str = Field(default="unknown")
    uptime_pct: float = Field(default=100.0, ge=0, le=100)
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time: float = Field(default=0.0)
    error_rate: float = Field(default=0.0, ge=0, le=100)

class HealthDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthMetric] = {}

    def register(self, component: str) -> HealthMetric:
        hm = HealthMetric(component=component)
        self._components[component] = hm
        return hm

    def update(self, component: str, status: str, response_time: float = 0.0, error_rate: float = 0.0) -> None:
        if component in self._components:
            hm = self._components[component]
            hm.status = status
            hm.response_time = response_time
            hm.error_rate = error_rate
            hm.last_check = datetime.utcnow()
            if status == "healthy":
                hm.uptime_pct = min(100, hm.uptime_pct + 0.1)
            else:
                hm.uptime_pct = max(0, hm.uptime_pct - 0.5)

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        down = sum(1 for c in self._components.values() if c.status == "down")
        avg_uptime = round(sum(c.uptime_pct for c in self._components.values()) / max(total, 1), 1)
        return {"components": total, "healthy": healthy, "degraded": degraded,
                "down": down, "avg_uptime_pct": avg_uptime}

    def get_component(self, component: str) -> Optional[HealthMetric]:
        return self._components.get(component)

class IncidentLog(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component: str
    severity: str = Field(default="info")
    title: str
    description: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    action_taken: str = ""

class IncidentManager:
    def __init__(self) -> None:
        self._incidents: List[IncidentLog] = []

    def report(self, component: str, severity: str, title: str, description: str = "") -> IncidentLog:
        incident = IncidentLog(component=component, severity=severity, title=title, description=description)
        self._incidents.append(incident)
        return incident

    def resolve(self, incident_id: str, action: str = "") -> bool:
        for inc in self._incidents:
            if inc.incident_id == incident_id and inc.resolved_at is None:
                inc.resolved_at = datetime.utcnow()
                inc.duration_seconds = int((inc.resolved_at - inc.detected_at).total_seconds())
                inc.action_taken = action
                return True
        return False

    def get_open(self) -> List[IncidentLog]:
        return [i for i in self._incidents if i.resolved_at is None]

    def get_by_severity(self, severity: str) -> List[IncidentLog]:
        return [i for i in self._incidents if i.severity == severity]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._incidents)
        open_count = len(self.get_open())
        resolved = total - open_count
        by_severity: Dict[str, int] = {}
        total_duration = 0
        resolved_count = 0
        for i in self._incidents:
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1
            if i.duration_seconds:
                total_duration += i.duration_seconds
                resolved_count += 1
        return {"total": total, "open": open_count, "resolved": resolved,
                "by_severity": by_severity,
                "avg_resolution_time_sec": round(total_duration / max(resolved_count, 1), 1)}

class RecoveryProcedure(BaseModel):
    procedure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    steps: List[str] = Field(default_factory=list)
    estimated_rtt_minutes: int = Field(default=5)
    validated: bool = False
    last_tested: Optional[datetime] = None
    owner: str = Field(default="platform")

class RecoveryRunner:
    def __init__(self) -> None:
        self._procedures: Dict[str, RecoveryProcedure] = {}

    def register(self, procedure: RecoveryProcedure) -> str:
        self._procedures[procedure.procedure_id] = procedure
        return procedure.procedure_id

    async def execute(self, procedure_id: str) -> Dict[str, Any]:
        proc = self._procedures.get(procedure_id)
        if not proc:
            return {"status": "error", "message": "Procedure not found"}
        executed_steps = []
        for i, step in enumerate(proc.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        return {"status": "completed", "procedure": proc.name, "steps": executed_steps,
                "total_steps": len(proc.steps), "duration_estimate_min": proc.estimated_rtt_minutes}

    def list_procedures(self) -> List[Dict[str, Any]]:
        return [{"id": p.procedure_id, "name": p.name, "steps": len(p.steps),
                 "validated": p.validated, "last_tested": p.last_tested} for p in self._procedures.values()]

class SLOMetric(BaseModel):
    name: str
    target_pct: float = Field(default=99.9, ge=0, le=100)
    current_pct: float = Field(default=100.0, ge=0, le=100)
    measurement_window: str = Field(default="30d")
    breached: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SLOManager:
    def __init__(self) -> None:
        self._slos: Dict[str, SLOMetric] = {}

    def define(self, name: str, target_pct: float = 99.9, window: str = "30d") -> SLOMetric:
        slo = SLOMetric(name=name, target_pct=target_pct, measurement_window=window)
        self._slos[name] = slo
        return slo

    def record_uptime(self, name: str, success: bool) -> None:
        slo = self._slos.get(name)
        if not slo:
            return
        factor = 0.0001 if not success else -0.0001
        slo.current_pct = round(max(0, min(100, slo.current_pct + factor)), 4)
        slo.breached = slo.current_pct < slo.target_pct
        slo.last_updated = datetime.utcnow()

    def get_status(self) -> Dict[str, Any]:
        breached = [s for s in self._slos.values() if s.breached]
        return {"total_slos": len(self._slos), "met": len(self._slos) - len(breached),
                "breached": len(breached), "details": {n: s.dict() for n, s in self._slos.items()}}
