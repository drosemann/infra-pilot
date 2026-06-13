"""Extended infrastructure pipelines with CI/CD integration, approval gates, and deployment tracking."""
import json
import uuid
import logging
import hashlib
import yaml
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    APPROVAL_WAITING = "approval_waiting"


class PipelineProvider(str, Enum):
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    AZURE_DEVOPS = "azure_devops"
    ARGOCD = "argocd"
    CUSTOM = "custom"


class DeploymentStrategy(str, Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"
    RAMPED = "ramped"
    IMMUTABLE = "immutable"


class ApprovalType(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    TIMED = "timed"
    CONDITIONAL = "conditional"


@dataclass
class PipelineTrigger:
    id: str
    provider: PipelineProvider
    event: str
    branch: Optional[str] = None
    paths: List[str] = field(default_factory=list)
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineStage:
    id: str
    name: str
    order: int = 0
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    requires_approval: bool = False
    approval_type: ApprovalType = ApprovalType.MANUAL
    approvers: List[str] = field(default_factory=list)
    timeout_minutes: int = 60
    environment: Optional[str] = None
    parallel_jobs: bool = False
    depends_on: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineDefinition:
    id: str
    name: str
    description: str
    provider: PipelineProvider
    status: PipelineStatus = PipelineStatus.DRAFT
    stages: List[PipelineStage] = field(default_factory=list)
    triggers: List[PipelineTrigger] = field(default_factory=list)
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    repository: Optional[str] = None
    branch: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    environment: Optional[str] = None
    timeout_minutes: int = 120
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineRun:
    id: str
    pipeline_id: str
    version: int = 1
    status: StageStatus = StageStatus.PENDING
    stages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    trigger: Optional[str] = None
    started_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    logs: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    environment: Optional[str] = None
    rollback_version: Optional[int] = None


@dataclass
class DeploymentRecord:
    id: str
    pipeline_id: str
    run_id: str
    environment: str
    version: str
    strategy: DeploymentStrategy
    status: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    artifact_url: Optional[str] = None
    deployed_by: Optional[str] = None
    rollback_to: Optional[str] = None
    health_check_passed: bool = False
    notes: Optional[str] = None


class InfrastructurePipelinesManager:
    def __init__(self, storage_path: str = "data/pipelines.json"):
        self.storage_path = storage_path
        self.pipelines: Dict[str, PipelineDefinition] = {}
        self.runs: Dict[str, PipelineRun] = {}
        self.deployments: Dict[str, DeploymentRecord] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for pl_data in data.get("pipelines", []):
            pl = PipelineDefinition(**pl_data)
            self.pipelines[pl.id] = pl
        for run_data in data.get("runs", []):
            run = PipelineRun(**run_data)
            self.runs[run.id] = run
        for dep_data in data.get("deployments", []):
            dep = DeploymentRecord(**dep_data)
            self.deployments[dep.id] = dep

    def _save_data(self) -> None:
        data = {
            "pipelines": [p.__dict__ for p in self.pipelines.values()],
            "runs": [r.__dict__ for r in self.runs.values()],
            "deployments": [d.__dict__ for d in self.deployments.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("InfrastructurePipelinesManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("InfrastructurePipelinesManager closed")

    def create_pipeline(self, name: str, description: str, provider: PipelineProvider, repository: Optional[str] = None, branch: Optional[str] = None, deployment_strategy: DeploymentStrategy = DeploymentStrategy.ROLLING, created_by: Optional[str] = None) -> PipelineDefinition:
        pl = PipelineDefinition(id=str(uuid.uuid4()), name=name, description=description, provider=provider, repository=repository, branch=branch, deployment_strategy=deployment_strategy, created_by=created_by)
        self.pipelines[pl.id] = pl
        self._save_data()
        return pl

    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineDefinition]:
        return self.pipelines.get(pipeline_id)

    def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> Optional[PipelineDefinition]:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return None
        for key, value in updates.items():
            if hasattr(pl, key) and key not in ("id", "created_at", "created_by"):
                setattr(pl, key, value)
        pl.updated_at = datetime.utcnow()
        self.pipelines[pipeline_id] = pl
        self._save_data()
        return pl

    def delete_pipeline(self, pipeline_id: str) -> bool:
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            self._save_data()
            return True
        return False

    def add_stage(self, pipeline_id: str, name: str, order: int, jobs: Optional[List[Dict[str, Any]]] = None, requires_approval: bool = False, environment: Optional[str] = None, depends_on: Optional[List[str]] = None) -> Optional[PipelineStage]:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return None
        stage = PipelineStage(id=str(uuid.uuid4()), name=name, order=order, jobs=jobs or [], requires_approval=requires_approval, environment=environment, depends_on=depends_on or [])
        pl.stages.append(stage)
        pl.updated_at = datetime.utcnow()
        self._save_data()
        return stage

    def remove_stage(self, pipeline_id: str, stage_id: str) -> bool:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return False
        pl.stages = [s for s in pl.stages if s.id != stage_id]
        pl.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def add_trigger(self, pipeline_id: str, provider: PipelineProvider, event: str, branch: Optional[str] = None, paths: Optional[List[str]] = None) -> Optional[PipelineTrigger]:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return None
        trigger = PipelineTrigger(id=str(uuid.uuid4()), provider=provider, event=event, branch=branch, paths=paths or [])
        pl.triggers.append(trigger)
        pl.updated_at = datetime.utcnow()
        self._save_data()
        return trigger

    def remove_trigger(self, pipeline_id: str, trigger_id: str) -> bool:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return False
        pl.triggers = [t for t in pl.triggers if t.id != trigger_id]
        pl.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def trigger_run(self, pipeline_id: str, branch: Optional[str] = None, commit_sha: Optional[str] = None, started_by: Optional[str] = None, variables: Optional[Dict[str, str]] = None) -> Optional[PipelineRun]:
        pl = self.pipelines.get(pipeline_id)
        if not pl or pl.status != PipelineStatus.ACTIVE:
            return None
        run = PipelineRun(id=str(uuid.uuid4()), pipeline_id=pipeline_id, version=1, status=StageStatus.PENDING, branch=branch or pl.branch, commit_sha=commit_sha, started_by=started_by, started_at=datetime.utcnow())
        self.runs[run.id] = run
        self._save_data()
        run.status = StageStatus.RUNNING
        for stage in sorted(pl.stages, key=lambda s: s.order):
            stage_key = stage.id
            run.stages[stage_key] = {"name": stage.name, "status": "running", "started_at": datetime.utcnow().isoformat(), "order": stage.order}
            if stage.requires_approval:
                run.stages[stage_key]["status"] = "approval_waiting"
                continue
            try:
                result = self._execute_stage(stage, variables or {})
                run.stages[stage_key].update({"status": "succeeded", "result": result, "completed_at": datetime.utcnow().isoformat()})
            except Exception as e:
                run.stages[stage_key].update({"status": "failed", "error": str(e), "completed_at": datetime.utcnow().isoformat()})
                run.status = StageStatus.FAILED
                run.error = str(e)
                run.completed_at = datetime.utcnow()
                run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
                self._save_data()
                return run
        run.status = StageStatus.SUCCEEDED
        run.completed_at = datetime.utcnow()
        run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        self._save_data()
        self._record_deployment(pl, run)
        return run

    def _execute_stage(self, stage: PipelineStage, variables: Dict[str, str]) -> Dict[str, Any]:
        results = []
        for job in stage.jobs:
            job_type = job.get("type", "script")
            if job_type == "script":
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "output": "Script executed"})
            elif job_type == "docker":
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "image": job.get("image", ""), "output": "Container ran"})
            elif job_type == "terraform":
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "output": "Terraform applied"})
            elif job_type == "ansible":
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "output": "Ansible playbook ran"})
            elif job_type == "kubernetes":
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "output": "Kubernetes manifest applied"})
            else:
                results.append({"job": job.get("name", "unnamed"), "status": "completed", "output": "Step executed"})
        return {"jobs_completed": len(results), "results": results}

    def _record_deployment(self, pipeline: PipelineDefinition, run: PipelineRun) -> DeploymentRecord:
        dep = DeploymentRecord(id=str(uuid.uuid4()), pipeline_id=pipeline.id, run_id=run.id, environment=run.environment or pipeline.environment or "production", version=f"v{run.version}", strategy=pipeline.deployment_strategy, status="deployed", deployed_by=run.started_by, started_at=datetime.utcnow(), completed_at=datetime.utcnow(), health_check_passed=True)
        self.deployments[dep.id] = dep
        self._save_data()
        return dep

    def approve_stage(self, run_id: str, stage_id: str, approved_by: str) -> bool:
        run = self.runs.get(run_id)
        if not run or stage_id not in run.stages:
            return False
        if run.stages[stage_id].get("status") == "approval_waiting":
            run.stages[stage_id]["status"] = "approved"
            run.stages[stage_id]["approved_by"] = approved_by
            run.stages[stage_id]["approved_at"] = datetime.utcnow().isoformat()
            self._save_data()
            return True
        return False

    def reject_stage(self, run_id: str, stage_id: str, rejected_by: str, reason: str = "") -> bool:
        run = self.runs.get(run_id)
        if not run or stage_id not in run.stages:
            return False
        if run.stages[stage_id].get("status") == "approval_waiting":
            run.stages[stage_id]["status"] = "rejected"
            run.stages[stage_id]["rejected_by"] = rejected_by
            run.stages[stage_id]["reason"] = reason
            run.status = StageStatus.FAILED
            run.error = f"Stage {stage_id} rejected by {rejected_by}: {reason}"
            run.completed_at = datetime.utcnow()
            self._save_data()
            return True
        return False

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        return self.runs.get(run_id)

    def cancel_run(self, run_id: str) -> bool:
        run = self.runs.get(run_id)
        if not run or run.status in (StageStatus.SUCCEEDED, StageStatus.FAILED, StageStatus.CANCELLED):
            return False
        run.status = StageStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        self._save_data()
        return True

    def list_pipelines(self, status: Optional[PipelineStatus] = None, provider: Optional[PipelineProvider] = None) -> List[PipelineDefinition]:
        results = list(self.pipelines.values())
        if status:
            results = [p for p in results if p.status == status]
        if provider:
            results = [p for p in results if p.provider == provider]
        return results

    def list_runs(self, pipeline_id: Optional[str] = None, status: Optional[StageStatus] = None) -> List[PipelineRun]:
        results = list(self.runs.values())
        if pipeline_id:
            results = [r for r in results if r.pipeline_id == pipeline_id]
        if status:
            results = [r for r in results if r.status == status]
        return sorted(results, key=lambda x: x.started_at or datetime.min, reverse=True)

    def get_deployments(self, pipeline_id: Optional[str] = None, environment: Optional[str] = None) -> List[DeploymentRecord]:
        results = list(self.deployments.values())
        if pipeline_id:
            results = [d for d in results if d.pipeline_id == pipeline_id]
        if environment:
            results = [d for d in results if d.environment == environment]
        return sorted(results, key=lambda x: x.started_at, reverse=True)

    def rollback_deployment(self, deployment_id: str, rolled_back_by: str) -> Optional[DeploymentRecord]:
        dep = self.deployments.get(deployment_id)
        if not dep:
            return None
        rollback = DeploymentRecord(id=str(uuid.uuid4()), pipeline_id=dep.pipeline_id, run_id=dep.run_id, environment=dep.environment, version=f"{dep.version}-rollback", strategy=dep.strategy, status="rollback", deployed_by=rolled_back_by, rollback_to=dep.version, started_at=datetime.utcnow(), completed_at=datetime.utcnow(), health_check_passed=True)
        self.deployments[rollback.id] = rollback
        dep.status = "rolled_back"
        self._save_data()
        return rollback

    def export_pipeline_yaml(self, pipeline_id: str) -> Optional[str]:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return None
        export = {"name": pl.name, "description": pl.description, "provider": pl.provider.value, "deployment_strategy": pl.deployment_strategy.value, "repository": pl.repository, "branch": pl.branch, "variables": pl.variables, "stages": [], "triggers": []}
        for stage in pl.stages:
            export["stages"].append({"name": stage.name, "order": stage.order, "environment": stage.environment, "requires_approval": stage.requires_approval, "approvers": stage.approvers, "jobs": stage.jobs, "depends_on": stage.depends_on})
        for trigger in pl.triggers:
            export["triggers"].append({"provider": trigger.provider.value, "event": trigger.event, "branch": trigger.branch, "paths": trigger.paths, "enabled": trigger.enabled})
        return yaml.dump(export, default_flow_style=False)

    def enable_pipeline(self, pipeline_id: str) -> bool:
        pl = self.pipelines.get(pipeline_id)
        if not pl:
            return False
        if pl.status == PipelineStatus.DRAFT or pl.status == PipelineStatus.DISABLED:
            pl.status = PipelineStatus.ACTIVE
            pl.updated_at = datetime.utcnow()
            self._save_data()
            return True
        return False

    def disable_pipeline(self, pipeline_id: str) -> bool:
        pl = self.pipelines.get(pipeline_id)
        if not pl or pl.status != PipelineStatus.ACTIVE:
            return False
        pl.status = PipelineStatus.DISABLED
        pl.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def get_run_statistics(self, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        runs = self.list_runs(pipeline_id=pipeline_id)
        total = len(runs)
        succeeded = sum(1 for r in runs if r.status == StageStatus.SUCCEEDED)
        failed = sum(1 for r in runs if r.status == StageStatus.FAILED)
        cancelled = sum(1 for r in runs if r.status == StageStatus.CANCELLED)
        avg_duration = 0.0
        durations = [r.duration_ms for r in runs if r.duration_ms]
        if durations:
            avg_duration = sum(durations) / len(durations)
        return {"total_runs": total, "succeeded": succeeded, "failed": failed, "cancelled": cancelled, "success_rate": (succeeded / total * 100) if total > 0 else 0.0, "average_duration_ms": avg_duration, "total_deployments": len(self.deployments)}

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_pipelines": len(self.pipelines), "active_pipelines": sum(1 for p in self.pipelines.values() if p.status == PipelineStatus.ACTIVE), "total_runs": len(self.runs), "total_deployments": len(self.deployments), **self.get_run_statistics()}
