import json
import uuid
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class RunStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    LINTING = "linting"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    APPLYING = "applying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


STAGE_TYPES = {
    "validate": {"order": 1, "description": "Validate configuration syntax and structure"},
    "lint": {"order": 2, "description": "Lint for best practices and security issues"},
    "plan": {"order": 3, "description": "Preview infrastructure changes"},
    "approve": {"order": 4, "description": "Manual or auto-approval gate", "requires_intervention": True},
    "apply": {"order": 5, "description": "Execute infrastructure changes"},
    "verify": {"order": 6, "description": "Post-deployment verification"},
}


class PipelineManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._pipelines: Dict[str, Dict] = {}
        self._runs: Dict[str, Dict] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("PipelineManager initialized")

    async def close(self) -> None:
        self._pipelines.clear()
        self._runs.clear()
        logger.info("PipelineManager closed")

    def create_pipeline(self, name: str, description: str, repo_url: str,
                        branch: str = "main", stages: Optional[List[Dict]] = None,
                        triggers: Optional[List[Dict]] = None,
                        notifications: Optional[Dict] = None) -> Dict:
        pipeline_id = str(uuid.uuid4())
        pipeline = {
            "pipeline_id": pipeline_id,
            "name": name,
            "description": description,
            "repo_url": repo_url,
            "branch": branch,
            "stages": stages or [
                {"name": "validate", "enabled": True, "timeout": 120},
                {"name": "lint", "enabled": True, "timeout": 120},
                {"name": "plan", "enabled": True, "timeout": 300},
                {"name": "approve", "enabled": True, "approval_type": "manual", "approvers": []},
                {"name": "apply", "enabled": True, "timeout": 600},
                {"name": "verify", "enabled": True, "timeout": 120},
            ],
            "triggers": triggers or [
                {"type": "push", "branches": ["main", "develop"]},
            ],
            "notifications": notifications or {
                "on_success": ["discord"],
                "on_failure": ["discord", "email"],
            },
            "status": PipelineStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "run_count": 0,
            "last_run_status": None,
        }
        self._pipelines[pipeline_id] = pipeline
        logger.info(f"Pipeline {pipeline_id} created: {name}")
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Optional[Dict]:
        return self._pipelines.get(pipeline_id)

    def update_pipeline(self, pipeline_id: str, updates: Dict) -> Optional[Dict]:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return None
        for key, value in updates.items():
            if key not in ("pipeline_id", "created_at"):
                pipeline[key] = value
        pipeline["updated_at"] = datetime.utcnow().isoformat()
        return pipeline

    def delete_pipeline(self, pipeline_id: str) -> bool:
        if pipeline_id not in self._pipelines:
            return False
        del self._pipelines[pipeline_id]
        return True

    def list_pipelines(self, status: Optional[str] = None) -> List[Dict]:
        pipelines = list(self._pipelines.values())
        if status:
            pipelines = [p for p in pipelines if p["status"] == status]
        return sorted(pipelines, key=lambda p: p["updated_at"], reverse=True)

    async def run_pipeline(self, pipeline_id: str, triggered_by: str = "manual",
                            variables: Optional[Dict] = None) -> Dict:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        run_id = str(uuid.uuid4())
        run = {
            "run_id": run_id,
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline["name"],
            "status": RunStatus.PENDING.value,
            "stages": {},
            "current_stage": None,
            "triggered_by": triggered_by,
            "variables": variables or {},
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "artifacts": {},
        }
        self._runs[run_id] = run
        pipeline["run_count"] += 1

        asyncio.create_task(self._execute_pipeline_run(run_id, pipeline))
        logger.info(f"Pipeline run {run_id} started for {pipeline['name']}")
        return run

    async def _execute_pipeline_run(self, run_id: str, pipeline: Dict) -> None:
        run = self._runs[run_id]
        for stage in pipeline.get("stages", []):
            if not stage.get("enabled", True):
                run["stages"][stage["name"]] = {"status": "skipped"}
                continue

            run["current_stage"] = stage["name"]
            run["status"] = RunStatus[stage["name"].upper()].value if stage["name"] in RunStatus._member_names_ else RunStatus.PENDING.value
            run["stages"][stage["name"]] = {
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }

            try:
                if stage["name"] == "approve":
                    approval_type = stage.get("approval_type", "manual")
                    if approval_type == "auto":
                        run["stages"][stage["name"]] = {"status": "auto-approved"}
                        continue
                    run["status"] = RunStatus.AWAITING_APPROVAL.value
                    return

                success = await self._execute_stage(stage, run.get("variables", {}))
                run["stages"][stage["name"]]["status"] = "completed" if success else "failed"
                run["stages"][stage["name"]]["completed_at"] = datetime.utcnow().isoformat()

                if not success:
                    run["status"] = RunStatus.FAILED.value
                    run["error"] = f"Stage '{stage['name']}' failed"
                    run["completed_at"] = datetime.utcnow().isoformat()
                    pipeline["last_run_status"] = "failed"
                    return

            except asyncio.TimeoutError:
                run["stages"][stage["name"]]["status"] = "timeout"
                run["status"] = RunStatus.FAILED.value
                run["error"] = f"Stage '{stage['name']}' timed out"
                run["completed_at"] = datetime.utcnow().isoformat()
                return
            except Exception as e:
                run["stages"][stage["name"]]["status"] = "failed"
                run["stages"][stage["name"]]["error"] = str(e)
                run["status"] = RunStatus.FAILED.value
                run["error"] = str(e)
                run["completed_at"] = datetime.utcnow().isoformat()
                return

        run["status"] = RunStatus.COMPLETED.value
        run["completed_at"] = datetime.utcnow().isoformat()
        pipeline["last_run_status"] = "completed"
        logger.info(f"Pipeline run {run_id} completed successfully")

    async def _execute_stage(self, stage: Dict, variables: Dict) -> bool:
        stage_name = stage["name"]
        timeout = stage.get("timeout", 300)

        if stage_name == "validate":
            await asyncio.sleep(1)
            return True
        elif stage_name == "lint":
            await asyncio.sleep(1)
            return True
        elif stage_name == "plan":
            await asyncio.sleep(1)
            return True
        elif stage_name == "apply":
            await asyncio.sleep(1)
            return True
        elif stage_name == "verify":
            await asyncio.sleep(0.5)
            return True

        return True

    def approve_run(self, run_id: str, approved_by: str) -> bool:
        run = self._runs.get(run_id)
        if not run or run["status"] != RunStatus.AWAITING_APPROVAL.value:
            return False
        run["stages"]["approve"] = {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat(),
        }
        pipeline = self._pipelines.get(run["pipeline_id"])
        if pipeline:
            asyncio.create_task(self._execute_pipeline_run(run_id, pipeline))
        return True

    def deny_run(self, run_id: str, denied_by: str, reason: str = "") -> bool:
        run = self._runs.get(run_id)
        if not run or run["status"] != RunStatus.AWAITING_APPROVAL.value:
            return False
        run["status"] = RunStatus.FAILED.value
        run["error"] = f"Approval denied by {denied_by}: {reason}"
        run["completed_at"] = datetime.utcnow().isoformat()
        run["stages"]["approve"] = {
            "status": "denied",
            "denied_by": denied_by,
            "reason": reason,
            "denied_at": datetime.utcnow().isoformat(),
        }
        return True

    def cancel_run(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if not run or run["status"] in (RunStatus.COMPLETED.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value):
            return False
        run["status"] = RunStatus.CANCELLED.value
        run["error"] = "Cancelled by user"
        run["completed_at"] = datetime.utcnow().isoformat()
        return True

    def get_run(self, run_id: str) -> Optional[Dict]:
        return self._runs.get(run_id)

    def get_pipeline_runs(self, pipeline_id: str, limit: int = 50) -> List[Dict]:
        runs = [r for r in self._runs.values() if r["pipeline_id"] == pipeline_id]
        runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
        return runs[:limit]

    def get_run_logs(self, run_id: str) -> List[Dict]:
        run = self._runs.get(run_id)
        if not run:
            return []
        logs = []
        for stage_name, stage_data in run.get("stages", {}).items():
            logs.append({
                "stage": stage_name,
                "status": stage_data.get("status"),
                "started_at": stage_data.get("started_at"),
                "completed_at": stage_data.get("completed_at"),
            })
        return logs

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._pipelines)
        total_runs = len(self._runs)
        completed = sum(1 for r in self._runs.values() if r["status"] == RunStatus.COMPLETED.value)
        failed = sum(1 for r in self._runs.values() if r["status"] == RunStatus.FAILED.value)
        active = sum(1 for p in self._pipelines.values() if p["status"] == PipelineStatus.ACTIVE.value)
        return {
            "total_pipelines": total,
            "active_pipelines": active,
            "total_runs": total_runs,
            "completed_runs": completed,
            "failed_runs": failed,
            "success_rate": round(completed / total_runs * 100, 1) if total_runs > 0 else 0,
        }
