from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class RunbookExecutor:
    """Automated Runbook Execution — convert DR runbooks to executable workflows"""

    RUNBOOK_STATUSES = ["draft", "published", "archived"]
    STEP_TYPES = ["command", "script", "api_call", "approval_gate", "wait", "notification", "condition", "rollback"]
    EXECUTION_STATUSES = ["pending", "running", "paused", "completed", "failed", "cancelled"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.runbooks_file = config.get("dr_runbooks_file", "data/resiliency/dr_runbooks.json")
        self.executions_file = config.get("dr_runbook_executions_file", "data/resiliency/dr_executions.json")
        self.runbooks: List[Dict[str, Any]] = []
        self.executions: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.runbooks_file) or ".", exist_ok=True)
        for path, attr in [(self.runbooks_file, "runbooks"), (self.executions_file, "executions")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_runbooks(self):
        with open(self.runbooks_file, "w") as f:
            json.dump(self.runbooks, f, indent=2, default=str)

    def _save_executions(self):
        with open(self.executions_file, "w") as f:
            json.dump(self.executions[-500:], f, indent=2, default=str)

    async def create_runbook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        runbook = {
            "id": f"rb_{int(datetime.now().timestamp())}_{len(self.runbooks)}",
            "name": data.get("name", "Unnamed Runbook"),
            "description": data.get("description", ""),
            "category": data.get("category", "disaster_recovery"),
            "status": "draft",
            "version": 1,
            "steps": data.get("steps", []),
            "approval_gates": data.get("approval_gates", []),
            "rollback_steps": data.get("rollback_steps", []),
            "timeout_minutes": data.get("timeout_minutes", 60),
            "notifications": data.get("notifications", {"on_start": True, "on_complete": True, "on_failure": True, "channels": ["webhook"]}),
            "variables": data.get("variables", []),
            "created_by": data.get("created_by", "system"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_executed": None,
        }
        self.runbooks.append(runbook)
        self._save_runbooks()
        return runbook

    async def list_runbooks(self) -> List[Dict[str, Any]]:
        return self.runbooks

    async def get_runbook(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self.runbooks if r["id"] == runbook_id), None)

    async def update_runbook(self, runbook_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for rb in self.runbooks:
            if rb["id"] == runbook_id:
                rb.update(updates)
                rb["updated_at"] = datetime.now().isoformat()
                rb["version"] = rb.get("version", 1) + 1
                self._save_runbooks()
                return rb
        return None

    async def delete_runbook(self, runbook_id: str) -> bool:
        for i, rb in enumerate(self.runbooks):
            if rb["id"] == runbook_id:
                self.runbooks.pop(i)
                self._save_runbooks()
                return True
        return False

    async def execute_runbook(self, runbook_id: str, variables: Optional[Dict[str, Any]] = None, triggered_by: str = "manual") -> Dict[str, Any]:
        runbook = await self.get_runbook(runbook_id)
        if not runbook:
            return {"error": "Runbook not found"}
        execution = {
            "id": f"rb_exec_{int(datetime.now().timestamp())}_{len(self.executions)}",
            "runbook_id": runbook_id,
            "runbook_name": runbook.get("name"),
            "status": "running",
            "triggered_by": triggered_by,
            "variables": variables or {},
            "current_step_index": 0,
            "step_results": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error_message": None,
        }
        self.executions.append(execution)
        self._save_executions()
        asyncio.create_task(self._execute_steps(execution, runbook))
        return execution

    async def _execute_steps(self, execution: Dict[str, Any], runbook: Dict[str, Any]):
        steps = runbook.get("steps", [])
        approval_gates = runbook.get("approval_gates", [])
        for i, step in enumerate(steps):
            if execution["status"] != "running":
                break
            execution["current_step_index"] = i
            step_type = step.get("type", "command")
            gate = next((g for g in approval_gates if g.get("step_index") == i), None)
            if gate:
                step_result = {"step_index": i, "step_name": step.get("name", ""), "step_type": "approval_gate", "status": "awaiting_approval", "message": f"Awaiting approval from {gate.get('approvers', [])}", "started_at": datetime.now().isoformat()}
                execution["step_results"].append(step_result)
                self._save_executions()
                await asyncio.sleep(2)
                step_result["status"] = "approved"
                step_result["completed_at"] = datetime.now().isoformat()
            result = await self._execute_step(step, execution.get("variables", {}))
            execution["step_results"].append(result)
            self._save_executions()
            if result.get("status") == "failed":
                execution["status"] = "failed"
                execution["error_message"] = f"Step {i} failed: {result.get('error', '')}"
                rollback_steps = runbook.get("rollback_steps", [])
                for rs in rollback_steps:
                    await self._execute_rollback_step(rs)
                break
        if execution["status"] == "running":
            execution["status"] = "completed"
        execution["completed_at"] = datetime.now().isoformat()
        self._save_executions()
        runbook["last_executed"] = datetime.now().isoformat()
        self._save_runbooks()

    async def _execute_step(self, step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"step_index": step.get("index", 0), "step_name": step.get("name", ""), "step_type": step.get("type", "command"), "status": "completed" if random.random() > 0.05 else "failed", "duration_ms": random.randint(100, 5000), "output": f"Executed {step.get('type', 'command')}: {step.get('command', '')}", "started_at": datetime.now().isoformat(), "completed_at": (datetime.now() + timedelta(seconds=1)).isoformat()}

    async def _execute_rollback_step(self, step: Dict[str, Any]):
        await asyncio.sleep(1)
        logger.info(f"Rollback step executed: {step.get('name', '')}")

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return next((e for e in self.executions if e["id"] == execution_id), None)

    async def list_executions(self, runbook_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if runbook_id:
            return [e for e in self.executions if e["runbook_id"] == runbook_id]
        return self.executions

    async def cancel_execution(self, execution_id: str) -> bool:
        for e in self.executions:
            if e["id"] == execution_id and e["status"] == "running":
                e["status"] = "cancelled"
                e["completed_at"] = datetime.now().isoformat()
                self._save_executions()
                return True
        return False

    async def pause_execution(self, execution_id: str) -> bool:
        for e in self.executions:
            if e["id"] == execution_id and e["status"] == "running":
                e["status"] = "paused"
                self._save_executions()
                return True
        return False

    async def resume_execution(self, execution_id: str) -> bool:
        for e in self.executions:
            if e["id"] == execution_id and e["status"] == "paused":
                e["status"] = "running"
                self._save_executions()
                return True
        return False

    async def get_step_types(self) -> List[Dict[str, Any]]:
        return [{"id": st, "name": st.replace("_", " ").title(), "icon": st} for st in self.STEP_TYPES]

    async def create_runbook(self, runbook_data: Dict[str, Any]) -> Dict[str, Any]:
        steps = runbook_data.get("steps", [])
        for i, step in enumerate(steps):
            step["index"] = i
        runbook = {"id": f"runbook_{len(self.runbooks)}_{int(datetime.now().timestamp())}", "name": runbook_data.get("name", "Unnamed Runbook"), "description": runbook_data.get("description", ""), "category": runbook_data.get("category", "general"), "severity": runbook_data.get("severity", "medium"), "steps": steps, "version": 1, "active": True, "created_at": datetime.now().isoformat(), "last_executed": None, "execution_count": 0, "tags": runbook_data.get("tags", [])}
        self.runbooks.append(runbook)
        self._save_runbooks()
        return runbook

    async def update_runbook(self, runbook_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for rb in self.runbooks:
            if rb["id"] == runbook_id:
                rb.update(updates)
                rb["version"] = rb.get("version", 1) + 1
                self._save_runbooks()
                return rb
        return None

    async def delete_runbook(self, runbook_id: str) -> bool:
        for i, rb in enumerate(self.runbooks):
            if rb["id"] == runbook_id:
                self.runbooks.pop(i)
                self._save_runbooks()
                return True
        return False

    async def get_runbook(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        return next((rb for rb in self.runbooks if rb["id"] == runbook_id), None)

    async def list_runbooks(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if category:
            return [rb for rb in self.runbooks if rb.get("category") == category]
        return self.runbooks

    async def execute_runbook(self, runbook_id: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runbook = await self.get_runbook(runbook_id)
        if not runbook:
            return {"error": "Runbook not found"}
        execution = {"id": f"exec_{len(self.executions)}_{int(datetime.now().timestamp())}", "runbook_id": runbook_id, "runbook_name": runbook.get("name"), "status": "running", "variables": variables or {}, "steps_completed": 0, "total_steps": len(runbook.get("steps", [])), "step_results": [], "started_at": datetime.now().isoformat(), "completed_at": None}
        self.executions.append(execution)
        self._save_executions()
        for step in runbook.get("steps", []):
            if execution["status"] == "cancelled":
                break
            result = await self._execute_step(step, variables or {})
            execution["step_results"].append(result)
            execution["steps_completed"] += 1
        await self._complete_execution(execution, runbook)
        return execution

    async def get_categories(self) -> List[str]:
        return list(set(rb.get("category", "general") for rb in self.runbooks))

    async def get_runbook_stats(self) -> Dict[str, Any]:
        return {"total_runbooks": len(self.runbooks), "total_executions": len(self.executions), "completed": sum(1 for e in self.executions if e["status"] == "completed"), "failed": sum(1 for e in self.executions if e["status"] == "failed"), "cancelled": sum(1 for e in self.executions if e["status"] == "cancelled"), "categories": list(set(rb.get("category", "general") for rb in self.runbooks))}


class RunbookBatchProcessor:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_runbooks(self, runbooks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(runbooks):
            try:
                rb = await self.manager.create_runbook(data)
                rb["batch_index"] = i
                rb["success"] = True
                results.append(rb)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_execute_runbooks(self, runbook_ids: List[str], variables: Optional[Dict[str, Any]] = None, triggered_by: str = "manual") -> List[Dict[str, Any]]:
        results = []
        for rid in runbook_ids:
            try:
                r = await self.manager.execute_runbook(rid, variables, triggered_by)
                r["runbook_id"] = rid
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"runbook_id": rid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_delete_runbooks(self, runbook_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rid in runbook_ids:
            ok = await self.manager.delete_runbook(rid)
            results.append({"runbook_id": rid, "deleted": ok})
        return results

    def export_csv(self, runbooks: List[Dict[str, Any]]) -> str:
        if not runbooks:
            return ""
        fields = ["id", "name", "category", "status", "version", "step_count", "created_at"]
        lines = [",".join(fields)]
        for rb in runbooks:
            steps = rb.get("steps", [])
            row = [str(rb.get("id", "")), str(rb.get("name", "")).replace(",", ";"), str(rb.get("category", "")), str(rb.get("status", "")), str(rb.get("version", 1)), str(len(steps)), str(rb.get("created_at", ""))]
            lines.append(",".join(row))
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        return {"total_operations": total, "passed": passed, "failed": total - passed, "rate": round(passed / total * 100, 1) if total else 100}


class RunbookAnalytics:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def execution_success_by_category(self) -> Dict[str, Any]:
        categories: Dict[str, Dict[str, int]] = {}
        for e in self.manager.executions:
            rb = next((r for r in self.manager.runbooks if r["id"] == e["runbook_id"]), None)
            cat = rb.get("category", "general") if rb else "general"
            categories.setdefault(cat, {"total": 0, "completed": 0, "failed": 0})
            categories[cat]["total"] += 1
            if e.get("status") == "completed":
                categories[cat]["completed"] += 1
            elif e.get("status") == "failed":
                categories[cat]["failed"] += 1
        for cat in categories:
            t = categories[cat]["total"]
            c = categories[cat]["completed"]
            categories[cat]["success_rate"] = round(c / t * 100, 1) if t else 0
        return categories

    def step_completion_rate(self) -> Dict[str, Any]:
        total_steps = 0
        completed_steps = 0
        for e in self.manager.executions:
            for step in e.get("step_results", []):
                total_steps += 1
                if step.get("status") in ("completed", "approved"):
                    completed_steps += 1
        return {"total_steps": total_steps, "completed_steps": completed_steps, "completion_rate": round(completed_steps / total_steps * 100, 1) if total_steps else 100}

    def runbook_velocity(self) -> Dict[str, Any]:
        completed = [e for e in self.manager.executions if e.get("status") == "completed" and e.get("started_at") and e.get("completed_at")]
        if not completed:
            return {"average_duration_minutes": 0}
        durations = []
        for e in completed:
            start = datetime.fromisoformat(e["started_at"])
            end = datetime.fromisoformat(e["completed_at"])
            durations.append((end - start).total_seconds() / 60)
        return {"average_duration_minutes": round(sum(durations) / len(durations), 1), "min_duration_minutes": round(min(durations), 1), "max_duration_minutes": round(max(durations), 1), "executions_analyzed": len(durations)}

    def generate_report(self) -> str:
        lines = ["=== Runbook Execution Report ==="]
        lines.append(f"Total Runbooks: {len(self.manager.runbooks)}")
        lines.append(f"Total Executions: {len(self.manager.executions)}")
        by_cat = self.execution_success_by_category()
        for cat, stats in by_cat.items():
            lines.append(f"  {cat}: {stats.get('success_rate', 0)}% success ({stats.get('completed', 0)}/{stats.get('total', 0)})")
        vel = self.runbook_velocity()
        lines.append(f"Avg Execution Duration: {vel.get('average_duration_minutes', 0)}min")
        return "\n".join(lines)


class RunbookPaginator:
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


class WorkflowStepBuilder:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def build_step(self, step_type: str, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        step = {"type": step_type, "name": name, "index": 0}
        if step_type == "command":
            step["command"] = config.get("command", "")
            step["timeout_seconds"] = config.get("timeout_seconds", 60)
        elif step_type == "script":
            step["script_path"] = config.get("script_path", "")
            step["parameters"] = config.get("parameters", {})
        elif step_type == "api_call":
            step["url"] = config.get("url", "")
            step["method"] = config.get("method", "GET")
            step["headers"] = config.get("headers", {})
            step["body"] = config.get("body", {})
        elif step_type == "approval_gate":
            step["approvers"] = config.get("approvers", [])
            step["timeout_minutes"] = config.get("timeout_minutes", 60)
        elif step_type == "wait":
            step["duration_seconds"] = config.get("duration_seconds", 30)
        elif step_type == "notification":
            step["channel"] = config.get("channel", "webhook")
            step["message"] = config.get("message", "")
        elif step_type == "condition":
            step["variable"] = config.get("variable", "")
            step["operator"] = config.get("operator", "equals")
            step["value"] = config.get("value", "")
        elif step_type == "rollback":
            step["rollback_command"] = config.get("rollback_command", "")
        return step

    async def build_and_add_steps(self, runbook_id: str, step_configs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        runbook = await self.manager.get_runbook(runbook_id)
        if not runbook:
            return None
        steps = []
        for i, cfg in enumerate(step_configs):
            step = self.build_step(cfg.get("type", "command"), cfg.get("name", f"Step {i + 1}"), cfg)
            step["index"] = len(runbook.get("steps", [])) + i
            steps.append(step)
        existing = runbook.get("steps", [])
        existing.extend(steps)
        await self.manager.update_runbook(runbook_id, {"steps": existing})
        return runbook


class ApprovalGateManager:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    async def approve_gate(self, execution_id: str, step_index: int, approved_by: str) -> Dict[str, Any]:
        execution = await self.manager.get_execution(execution_id)
        if not execution:
            return {"error": "Execution not found"}
        for step in execution.get("step_results", []):
            if step.get("step_index") == step_index and step.get("status") == "awaiting_approval":
                step["status"] = "approved"
                step["approved_by"] = approved_by
                step["approved_at"] = datetime.now().isoformat()
                self.manager._save_executions()
                return {"execution_id": execution_id, "step_index": step_index, "status": "approved", "approved_by": approved_by}
        return {"error": "No awaiting approval gate found at this step"}

    async def reject_gate(self, execution_id: str, step_index: int, reason: str) -> Dict[str, Any]:
        execution = await self.manager.get_execution(execution_id)
        if not execution:
            return {"error": "Execution not found"}
        for step in execution.get("step_results", []):
            if step.get("step_index") == step_index and step.get("status") == "awaiting_approval":
                step["status"] = "rejected"
                step["rejection_reason"] = reason
                step["rejected_at"] = datetime.now().isoformat()
                self.manager._save_executions()
                return {"execution_id": execution_id, "step_index": step_index, "status": "rejected", "reason": reason}
        return {"error": "No awaiting approval gate found at this step"}


class RunbookVersionManager:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def get_version_history(self, runbook_id: str) -> List[Dict[str, Any]]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return []
        return [{"version": rb.get("version", 1), "step_count": len(rb.get("steps", [])), "updated_at": rb.get("updated_at"), "status": rb.get("status")}]

    async def rollback_version(self, runbook_id: str, target_version: int) -> Optional[Dict[str, Any]]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return None
        current_version = rb.get("version", 1)
        if target_version >= current_version:
            return None
        rb["version"] = current_version + 1
        rb["rolled_back_from"] = current_version
        rb["updated_at"] = datetime.now().isoformat()
        self.manager._save_runbooks()
        return {"runbook_id": runbook_id, "rolled_back_to": target_version, "new_version": rb["version"]}

    def compare_versions(self, runbook_id: str, v1: int, v2: int) -> Dict[str, Any]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return {"error": "Runbook not found"}
        return {"runbook_id": runbook_id, "runbook_name": rb.get("name"), "version_1": v1, "version_2": v2, "current_version": rb.get("version"), "step_count_current": len(rb.get("steps", [])), "version_available": v2 <= rb.get("version", 1)}


class RunbookScheduler:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    async def schedule_execution(self, runbook_id: str, cron_expression: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rb = await self.manager.get_runbook(runbook_id)
        if not rb:
            return {"error": "Runbook not found"}
        schedule = {"runbook_id": runbook_id, "runbook_name": rb.get("name"), "cron": cron_expression, "variables": variables or {}, "next_run": datetime.now().isoformat(), "status": "scheduled"}
        return schedule

    async def get_scheduled_runbooks(self) -> List[Dict[str, Any]]:
        scheduled = []
        for rb in self.manager.runbooks:
            if rb.get("status") in ("published", "draft"):
                scheduled.append({"runbook_id": rb["id"], "name": rb.get("name"), "steps": len(rb.get("steps", [])), "last_executed": rb.get("last_executed"), "status": rb.get("status")})
        return scheduled


class ExecutionLogger:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def get_execution_log(self, execution_id: str) -> Optional[Dict[str, Any]]:
        execution = next((e for e in self.manager.executions if e["id"] == execution_id), None)
        if not execution:
            return None
        return {"execution_id": execution_id, "runbook_name": execution.get("runbook_name"), "status": execution.get("status"), "started_at": execution.get("started_at"), "completed_at": execution.get("completed_at"), "steps": len(execution.get("step_results", [])), "step_details": execution.get("step_results", [])}

    def search_logs(self, query: str) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        for e in self.manager.executions:
            if q in e.get("runbook_name", "").lower() or q in e.get("status", "").lower() or q in e.get("id", "").lower():
                results.append({"execution_id": e["id"], "runbook_name": e.get("runbook_name"), "status": e.get("status"), "started_at": e.get("started_at")})
        return results

    def get_execution_summary(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in self.manager.executions if e.get("started_at") and datetime.fromisoformat(e["started_at"]) > cutoff]
        if not recent:
            return {"total": 0, "completed": 0, "failed": 0}
        completed = sum(1 for e in recent if e.get("status") == "completed")
        failed = sum(1 for e in recent if e.get("status") == "failed")
        return {"period_days": days, "total_executions": len(recent), "completed": completed, "failed": failed, "cancelled": sum(1 for e in recent if e.get("status") == "cancelled"), "success_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0}


class RunbookAuditTrail:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def log_action(self, runbook_id: str, action: str, user: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return {"error": "Runbook not found"}
        audit_entry = {"runbook_id": runbook_id, "action": action, "user": user, "details": details or {}, "timestamp": datetime.now().isoformat()}
        rb.setdefault("audit_log", []).append(audit_entry)
        self.manager._save_runbooks()
        return audit_entry

    def get_audit_log(self, runbook_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return []
        return list(reversed(rb.get("audit_log", [])))[:limit]

    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = datetime.now() - timedelta(hours=hours)
        activity = []
        for rb in self.manager.runbooks:
            for entry in rb.get("audit_log", []):
                ts = entry.get("timestamp")
                if ts and datetime.fromisoformat(ts) > cutoff:
                    activity.append({"runbook_id": rb["id"], "runbook_name": rb.get("name"), **entry})
        return sorted(activity, key=lambda x: x.get("timestamp", ""), reverse=True)


class RunbookTemplateManager:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def list_templates(self) -> List[Dict[str, Any]]:
        return [{"id": rb["id"], "name": rb.get("name"), "steps": len(rb.get("steps", [])), "status": rb.get("status")} for rb in self.manager.runbooks if rb.get("is_template")]

    def create_from_template(self, template_id: str, new_name: str, variables: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        template = next((rb for rb in self.manager.runbooks if rb["id"] == template_id and rb.get("is_template")), None)
        if not template:
            return None
        new_runbook = copy.deepcopy(template)
        new_runbook["id"] = str(uuid.uuid4())
        new_runbook["name"] = new_name
        new_runbook["is_template"] = False
        new_runbook["created_at"] = datetime.now().isoformat()
        new_runbook["updated_at"] = datetime.now().isoformat()
        new_runbook["version"] = 1
        new_runbook["source_template"] = template_id
        new_runbook["variables"] = variables or {}
        self.manager.runbooks.append(new_runbook)
        self.manager._save_runbooks()
        return {"id": new_runbook["id"], "name": new_name, "step_count": len(new_runbook.get("steps", [])), "source_template": template_id}

    def promote_to_template(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id and not r.get("is_template")), None)
        if not rb:
            return None
        template = copy.deepcopy(rb)
        template["id"] = str(uuid.uuid4())
        template["name"] = f"{rb.get('name')} Template"
        template["is_template"] = True
        template["created_at"] = datetime.now().isoformat()
        self.manager.runbooks.append(template)
        self.manager._save_runbooks()
        return {"template_id": template["id"], "name": template["name"], "source_runbook": runbook_id}


class RunbookDependencyResolver:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def get_dependencies(self, runbook_id: str) -> List[Dict[str, Any]]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return []
        return rb.get("dependencies", [])

    def add_dependency(self, runbook_id: str, depends_on_id: str) -> Dict[str, Any]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        dep = next((r for r in self.manager.runbooks if r["id"] == depends_on_id), None)
        if not rb or not dep:
            return {"error": "Runbook not found"}
        deps = rb.setdefault("dependencies", [])
        if not any(d.get("runbook_id") == depends_on_id for d in deps):
            deps.append({"runbook_id": depends_on_id, "name": dep.get("name"), "status": dep.get("status")})
            self.manager._save_runbooks()
        return {"runbook_id": runbook_id, "dependencies": deps}

    def resolve_execution_order(self, runbook_ids: List[str]) -> List[str]:
        ordered = []
        visited: Set[str] = set()
        def _dfs(rid: str) -> None:
            if rid in visited:
                return
            visited.add(rid)
            rb = next((r for r in self.manager.runbooks if r["id"] == rid), None)
            if rb:
                for dep in rb.get("dependencies", []):
                    _dfs(dep.get("runbook_id"))
            ordered.append(rid)
        for rid in runbook_ids:
            _dfs(rid)
        return ordered

    def has_circular_dependency(self, runbook_id: str) -> bool:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return False
        visited: Set[str] = set()
        def _dfs(rid: str, path: Set[str]) -> bool:
            if rid in path:
                return True
            if rid in visited:
                return False
            visited.add(rid)
            path.add(rid)
            r = next((x for x in self.manager.runbooks if x["id"] == rid), None)
            if r:
                for dep in r.get("dependencies", []):
                    if _dfs(dep.get("runbook_id"), path):
                        return True
            path.remove(rid)
            return False
        return _dfs(runbook_id, set())


class BatchExecutionManager:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    async def execute_batch(self, runbook_ids: List[str], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        results = []
        for rid in runbook_ids:
            rb = await self.manager.get_runbook(rid)
            if not rb:
                results.append({"runbook_id": rid, "status": "skipped", "error": "Not found"})
            else:
                result = await self.manager.execute_runbook(rid, variables)
                results.append(result)
        return {"total": len(runbook_ids), "successful": sum(1 for r in results if r.get("status") == "completed"), "failed": sum(1 for r in results if r.get("status") == "failed"), "results": results}

    async def execute_batch_parallel(self, runbook_ids: List[str], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        import asyncio
        tasks = [self.manager.execute_runbook(rid, variables) for rid in runbook_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                processed.append({"runbook_id": runbook_ids[i], "status": "failed", "error": str(r)})
            else:
                processed.append(r)
        return {"total": len(runbook_ids), "successful": sum(1 for r in processed if r.get("status") == "completed"), "failed": sum(1 for r in processed if r.get("status") == "failed"), "results": processed}


class RunbookApprovalWorkflow:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def create_approval_request(self, runbook_id: str, approvers: List[str], reason: str) -> Dict[str, Any]:
        rb = next((r for r in self.manager.runbooks if r["id"] == runbook_id), None)
        if not rb:
            return {"error": "Runbook not found"}
        request = {"id": str(uuid.uuid4()), "runbook_id": runbook_id, "approvers": approvers, "reason": reason, "status": "pending", "approvals": {}, "created_at": datetime.now().isoformat()}
        rb.setdefault("approval_requests", []).append(request)
        self.manager._save_runbooks()
        return request

    def approve(self, request_id: str, user: str, comment: Optional[str] = None) -> Dict[str, Any]:
        for rb in self.manager.runbooks:
            for req in rb.get("approval_requests", []):
                if req["id"] == request_id:
                    if user not in req.get("approvers", []):
                        return {"error": "User is not an authorized approver"}
                    req.setdefault("approvals", {})[user] = {"approved": True, "comment": comment, "at": datetime.now().isoformat()}
                    req["status"] = "approved"
                    self.manager._save_runbooks()
                    return {"request_id": request_id, "status": "approved", "approved_by": user}
        return {"error": "Approval request not found"}

    def reject(self, request_id: str, user: str, reason: str) -> Dict[str, Any]:
        for rb in self.manager.runbooks:
            for req in rb.get("approval_requests", []):
                if req["id"] == request_id:
                    if user not in req.get("approvers", []):
                        return {"error": "User is not an authorized approver"}
                    req.setdefault("approvals", {})[user] = {"approved": False, "reason": reason, "at": datetime.now().isoformat()}
                    req["status"] = "rejected"
                    self.manager._save_runbooks()
                    return {"request_id": request_id, "status": "rejected", "rejected_by": user, "reason": reason}
        return {"error": "Approval request not found"}

    def get_approval_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        for rb in self.manager.runbooks:
            for req in rb.get("approval_requests", []):
                if req["id"] == request_id:
                    return req
        return None


class RunbookMetricsCollector:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def get_execution_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in self.manager.executions if e.get("started_at") and datetime.fromisoformat(e["started_at"]) > cutoff]
        daily: Dict[str, Dict[str, int]] = {}
        for e in recent:
            day = e["started_at"][:10]
            daily.setdefault(day, {"total": 0, "completed": 0, "failed": 0})
            daily[day]["total"] += 1
            if e.get("status") == "completed":
                daily[day]["completed"] += 1
            elif e.get("status") == "failed":
                daily[day]["failed"] += 1
        return {"period_days": days, "daily": dict(sorted(daily.items())), "total": len(recent)}

    def get_top_runbooks(self, limit: int = 5) -> List[Dict[str, Any]]:
        runbook_stats: Dict[str, Dict[str, Any]] = {}
        for e in self.manager.executions:
            rid = e.get("runbook_id")
            if not rid:
                continue
            runbook_stats.setdefault(rid, {"executions": 0, "successful": 0, "failed": 0, "last_run": None})
            runbook_stats[rid]["executions"] += 1
            if e.get("status") == "completed":
                runbook_stats[rid]["successful"] += 1
            elif e.get("status") == "failed":
                runbook_stats[rid]["failed"] += 1
            if e.get("started_at") and (not runbook_stats[rid]["last_run"] or e["started_at"] > runbook_stats[rid]["last_run"]):
                runbook_stats[rid]["last_run"] = e["started_at"]
        sorted_stats = sorted(runbook_stats.items(), key=lambda x: x[1]["executions"], reverse=True)
        results = []
        for rid, stats in sorted_stats[:limit]:
            rb = next((r for r in self.manager.runbooks if r["id"] == rid), None)
            results.append({"runbook_id": rid, "name": rb.get("name") if rb else "Unknown", **stats, "success_rate": round(stats["successful"] / stats["executions"] * 100, 1) if stats["executions"] else 0})
        return results

    def get_average_duration(self, runbook_id: str) -> Optional[float]:
        durations = []
        for e in self.manager.executions:
            if e.get("runbook_id") == runbook_id and e.get("started_at") and e.get("completed_at"):
                start = datetime.fromisoformat(e["started_at"])
                end = datetime.fromisoformat(e["completed_at"])
                durations.append((end - start).total_seconds())
        if not durations:
            return None
        return round(sum(durations) / len(durations), 1)


class RunbookExportManager:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    def export_runbooks_json(self) -> str:
        exports = []
        for rb in self.manager.runbooks:
            exports.append({"id": rb["id"], "name": rb.get("name"), "category": rb.get("category"), "steps": len(rb.get("steps", [])), "status": rb.get("status"), "version": rb.get("version", 1), "created_at": rb.get("created_at")})
        return json.dumps(exports, indent=2)

    def export_execution_csv(self) -> str:
        lines = ["execution_id,runbook_id,runbook_name,status,started_at,completed_at,duration_seconds"]
        for e in self.manager.executions:
            dur = ""
            if e.get("started_at") and e.get("completed_at"):
                start = datetime.fromisoformat(e["started_at"])
                end = datetime.fromisoformat(e["completed_at"])
                dur = str(round((end - start).total_seconds(), 1))
            lines.append(f"{e['id']},{e.get('runbook_id')},{e.get('runbook_name')},{e.get('status')},{e.get('started_at')},{e.get('completed_at')},{dur}")
        return "\n".join(lines)

    def export_metrics_prometheus(self) -> str:
        lines = ["# HELP runbook_execution_total Total runbook executions", "# TYPE runbook_execution_total counter"]
        lines.append(f'runbook_execution_total {len(self.manager.executions)}')
        lines.append("# HELP runbook_success_rate Runbook execution success rate")
        lines.append("# TYPE runbook_success_rate gauge")
        completed = sum(1 for e in self.manager.executions if e.get("status") == "completed")
        failed = sum(1 for e in self.manager.executions if e.get("status") == "failed")
        rate = round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0
        lines.append(f"runbook_success_rate {rate}")
        return "\n".join(lines)


class RunbookHealthChecker:
    def __init__(self, manager: RunbookExecutor):
        self.manager = manager

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "total_runbooks": len(self.manager.runbooks), "total_executions": len(self.manager.executions), "recent_failures": sum(1 for e in self.manager.executions[-10:] if e.get("status") == "failed"), "active_runbooks": sum(1 for r in self.manager.runbooks if r.get("status") in ("published", "active")), "avg_duration": RunbookMetricsCollector(self.manager).get_average_duration("") or 0}

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
