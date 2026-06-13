"""Golden Path Scaffolder — Guided service creation from approved templates."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ScaffoldStep(str, Enum):
    REPO_CREATION = "repo_creation"
    CI_CD_SETUP = "ci_cd_setup"
    CLOUD_RESOURCES = "cloud_resources"
    MONITORING = "monitoring"
    ON_CALL_CONFIG = "on_call_config"
    DOCUMENTATION = "documentation"
    COMPLETED = "completed"


GOLDEN_TEMPLATES = {
    "microservice-fastapi": {
        "name": "Microservice (FastAPI)",
        "description": "Production-ready FastAPI microservice with CI/CD, monitoring, and docs",
        "language": "python",
        "framework": "fastapi",
        "steps": [
            ScaffoldStep.REPO_CREATION,
            ScaffoldStep.CI_CD_SETUP,
            ScaffoldStep.CLOUD_RESOURCES,
            ScaffoldStep.MONITORING,
            ScaffoldStep.ON_CALL_CONFIG,
            ScaffoldStep.DOCUMENTATION,
        ],
        "repo_template": "gh:infrapilot/fastapi-template",
        "ci_template": "github-actions",
        "cloud_template": "terraform-aws-ecs",
        "monitoring_template": "grafana-mixin-fastapi",
        "default_resources": {"cpu": "0.5", "memory": "512Mi", "replicas": 2},
    },
    "service-node-express": {
        "name": "Node.js Express Service",
        "description": "Node.js/Express REST API service with TypeScript, CI/CD, and monitoring",
        "language": "typescript",
        "framework": "express",
        "steps": [
            ScaffoldStep.REPO_CREATION,
            ScaffoldStep.CI_CD_SETUP,
            ScaffoldStep.CLOUD_RESOURCES,
            ScaffoldStep.MONITORING,
            ScaffoldStep.ON_CALL_CONFIG,
        ],
        "repo_template": "gh:infrapilot/express-template",
        "ci_template": "github-actions-node",
        "cloud_template": "terraform-gcp-cloud-run",
        "monitoring_template": "grafana-mixin-node",
        "default_resources": {"cpu": "1.0", "memory": "1Gi", "replicas": 2},
    },
    "event-processor-go": {
        "name": "Event Processor (Go)",
        "description": "Go event processor with Kafka integration, tracing, and dashboards",
        "language": "go",
        "framework": "none",
        "steps": [
            ScaffoldStep.REPO_CREATION,
            ScaffoldStep.CI_CD_SETUP,
            ScaffoldStep.CLOUD_RESOURCES,
            ScaffoldStep.MONITORING,
        ],
        "repo_template": "gh:infrapilot/go-processor-template",
        "ci_template": "github-actions-go",
        "cloud_template": "terraform-aws-lambda",
        "monitoring_template": "grafana-mixin-go",
        "default_resources": {"memory": "256Mi", "timeout": "30s"},
    },
    "data-pipeline-python": {
        "name": "Data Pipeline (Python)",
        "description": "Python data pipeline with Airflow, dbt, and data quality checks",
        "language": "python",
        "framework": "airflow",
        "steps": [
            ScaffoldStep.REPO_CREATION,
            ScaffoldStep.CI_CD_SETUP,
            ScaffoldStep.CLOUD_RESOURCES,
            ScaffoldStep.DOCUMENTATION,
        ],
        "repo_template": "gh:infrapilot/data-pipeline-template",
        "ci_template": "github-actions",
        "cloud_template": "terraform-gcp-composer",
        "monitoring_template": "",
        "default_resources": {"cpu": "2.0", "memory": "4Gi"},
    },
}


class ScaffoldInstance:
    def __init__(self, instance_id: str, template_name: str, service_name: str, owner: str):
        self.instance_id = instance_id
        self.template_name = template_name
        self.service_name = service_name
        self.owner = owner
        self.current_step: ScaffoldStep = ScaffoldStep.REPO_CREATION
        self.completed_steps: list[str] = []
        self.status: str = "in_progress"
        self.repo_url: str = ""
        self.ci_config: dict[str, Any] = {}
        self.cloud_resources: dict[str, Any] = {}
        self.monitoring_config: dict[str, Any] = {}
        self.on_call_config: dict[str, Any] = {}
        self.doc_url: str = ""
        self.scorecard_pr_url: str = ""
        self.errors: list[str] = []
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "template_name": self.template_name,
            "service_name": self.service_name,
            "owner": self.owner,
            "current_step": self.current_step.value,
            "completed_steps": self.completed_steps,
            "status": self.status,
            "repo_url": self.repo_url,
            "ci_config": self.ci_config,
            "cloud_resources": self.cloud_resources,
            "monitoring_config": self.monitoring_config,
            "on_call_config": self.on_call_config,
            "doc_url": self.doc_url,
            "scorecard_pr_url": self.scorecard_pr_url,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScaffoldInstance":
        inst = cls(data["instance_id"], data["template_name"], data["service_name"], data["owner"])
        inst.current_step = ScaffoldStep(data.get("current_step", "repo_creation"))
        inst.completed_steps = data.get("completed_steps", [])
        inst.status = data.get("status", "in_progress")
        inst.repo_url = data.get("repo_url", "")
        inst.ci_config = data.get("ci_config", {})
        inst.cloud_resources = data.get("cloud_resources", {})
        inst.monitoring_config = data.get("monitoring_config", {})
        inst.on_call_config = data.get("on_call_config", {})
        inst.doc_url = data.get("doc_url", "")
        inst.scorecard_pr_url = data.get("scorecard_pr_url", "")
        inst.errors = data.get("errors", [])
        if data.get("created_at"):
            inst.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            inst.updated_at = datetime.fromisoformat(data["updated_at"])
        inst.metadata = data.get("metadata", {})
        return inst


class GoldenPathScaffolder:
    def __init__(self):
        self.instances: dict[str, ScaffoldInstance] = {}
        self.templates = dict(GOLDEN_TEMPLATES)

    def list_templates(self) -> list[dict[str, Any]]:
        return [
            {"name": k, **{kk: vv for kk, vv in v.items() if kk != "steps"}}
            for k, v in self.templates.items()
        ]

    def get_template(self, name: str) -> Optional[dict[str, Any]]:
        return self.templates.get(name)

    def start_scaffold(self, template_name: str, service_name: str, owner: str) -> Optional[ScaffoldInstance]:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            logger.warning("Unknown template: %s", template_name)
            return None
        instance_id = str(uuid.uuid4())
        instance = ScaffoldInstance(instance_id, template_name, service_name, owner)
        instance.metadata["template_info"] = {k: v for k, v in tmpl.items() if k != "steps"}
        self.instances[instance_id] = instance
        logger.info("Started scaffold %s for service %s using template %s", instance_id, service_name, template_name)
        return instance

    def get_instance(self, instance_id: str) -> Optional[ScaffoldInstance]:
        return self.instances.get(instance_id)

    def advance_step(self, instance_id: str, step_result: dict[str, Any]) -> Optional[ScaffoldInstance]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        tmpl = self.templates.get(inst.template_name)
        if not tmpl:
            return None
        steps = tmpl["steps"]
        current_idx = next((i for i, s in enumerate(steps) if s == inst.current_step), -1)
        if current_idx < 0:
            return None
        inst.completed_steps.append(inst.current_step.value)
        if step_result.get("error"):
            inst.errors.append(step_result["error"])
            inst.status = "failed"
            inst.updated_at = datetime.utcnow()
            return inst
        if inst.current_step == ScaffoldStep.REPO_CREATION and step_result.get("repo_url"):
            inst.repo_url = step_result["repo_url"]
        elif inst.current_step == ScaffoldStep.CI_CD_SETUP and step_result.get("ci_config"):
            inst.ci_config = step_result["ci_config"]
        elif inst.current_step == ScaffoldStep.CLOUD_RESOURCES and step_result.get("resources"):
            inst.cloud_resources = step_result["resources"]
        elif inst.current_step == ScaffoldStep.MONITORING and step_result.get("monitoring"):
            inst.monitoring_config = step_result["monitoring"]
        elif inst.current_step == ScaffoldStep.ON_CALL_CONFIG and step_result.get("on_call"):
            inst.on_call_config = step_result["on_call"]
        elif inst.current_step == ScaffoldStep.DOCUMENTATION and step_result.get("doc_url"):
            inst.doc_url = step_result["doc_url"]
        if current_idx + 1 < len(steps):
            inst.current_step = steps[current_idx + 1]
        else:
            inst.current_step = ScaffoldStep.COMPLETED
            inst.status = "completed"
            inst.scorecard_pr_url = step_result.get("scorecard_pr_url", "")
        inst.updated_at = datetime.utcnow()
        return inst

    def fail_instance(self, instance_id: str, error: str) -> Optional[ScaffoldInstance]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        inst.status = "failed"
        inst.errors.append(error)
        inst.updated_at = datetime.utcnow()
        return inst

    def list_instances(self, owner: str = "", status: str = "") -> list[ScaffoldInstance]:
        results = list(self.instances.values())
        if owner:
            results = [i for i in results if i.owner == owner]
        if status:
            results = [i for i in results if i.status == status]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def get_scaffold_summary(self) -> dict[str, Any]:
        total = len(self.instances)
        by_status: dict[str, int] = {}
        by_template: dict[str, int] = {}
        for inst in self.instances.values():
            by_status[inst.status] = by_status.get(inst.status, 0) + 1
            by_template[inst.template_name] = by_template.get(inst.template_name, 0) + 1
        return {
            "total_scaffolds": total,
            "by_status": by_status,
            "by_template": by_template,
            "completion_rate": round(
                by_status.get("completed", 0) / total * 100, 1
            ) if total > 0 else 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "templates": self.list_templates(),
            "instances": {iid: inst.to_dict() for iid, inst in self.instances.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoldenPathScaffolder":
        scaff = cls()
        for iid, idata in data.get("instances", {}).items():
            scaff.instances[iid] = ScaffoldInstance.from_dict(idata)
        return scaff

    def register_template(self, name: str, template_data: dict[str, Any]) -> bool:
        if name in self.templates:
            return False
        steps = [ScaffoldStep(s) if isinstance(s, str) else s for s in template_data.get("steps", [])]
        template_data["steps"] = steps
        self.templates[name] = template_data
        return True

    def review_instance(self, instance_id: str, approved: bool, reviewer: str = "", notes: str = "") -> Optional[ScaffoldInstance]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        if approved:
            inst.status = "approved"
        else:
            inst.status = "rejected"
            if notes:
                inst.errors.append(f"Rejected by {reviewer}: {notes}")
        inst.metadata["reviewed_by"] = reviewer
        inst.metadata["review_notes"] = notes
        inst.updated_at = datetime.utcnow()
        return inst

    def get_progress_report(self) -> dict[str, Any]:
        total = len(self.instances)
        if total == 0:
            return {"total": 0}
        completed = len([i for i in self.instances.values() if i.status == "completed"])
        failed = len([i for i in self.instances.values() if i.status == "failed"])
        in_progress = len([i for i in self.instances.values() if i.status == "in_progress"])
        avg_steps = sum(len(i.completed_steps) for i in self.instances.values()) / max(total, 1)
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "avg_steps_completed": round(avg_steps, 1),
            "by_template": {
                name: len([i for i in self.instances.values() if i.template_name == name])
                for name in set(i.template_name for i in self.instances.values())
            },
        }

    def batch_start_scaffolds(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for req in requests:
            inst = self.start_scaffold(req["template_name"], req["service_name"], req["owner"])
            if inst:
                if req.get("metadata"):
                    inst.metadata.update(req["metadata"])
                results.append({"instance_id": inst.instance_id, "status": "started", "service_name": req["service_name"]})
            else:
                results.append({"status": "failed", "service_name": req.get("service_name", "unknown"), "error": "Template not found"})
        return results

    def export_scaffolds(self, status: str = "") -> list[dict[str, Any]]:
        insts = self.list_instances(status=status) if status else list(self.instances.values())
        return [i.to_dict() for i in insts]

    def get_scaffolds_by_template(self, template_name: str) -> list[ScaffoldInstance]:
        return [i for i in self.instances.values() if i.template_name == template_name]

    def retire_template(self, template_name: str) -> bool:
        if template_name in self.templates:
            del self.templates[template_name]
            return True
        return False

    def get_template_popularity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for i in self.instances.values():
            counts[i.template_name] = counts.get(i.template_name, 0) + 1
        return counts

    def bulk_advance_steps(self, results: list[dict[str, Any]]) -> int:
        count = 0
        for r in results:
            if self.advance_step(r.get("instance_id"), r):
                count += 1
        return count

    def add_custom_step(self, template_name: str, step_name: str, step_type: str = "manual",
                         description: str = "", depends_on: list[str] | None = None) -> dict[str, Any] | None:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            return None
        step_id = str(uuid.uuid4())
        step = {"step_id": step_id, "name": step_name, "step_type": step_type,
                "description": description, "depends_on": depends_on or [],
                "status": "pending", "created_at": datetime.utcnow().isoformat()}
        tmpl["steps"].append(step)
        return step

    def add_approval_flow(self, template_name: str, required_approvers: list[str]) -> dict[str, Any] | None:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            return None
        flow_id = str(uuid.uuid4())
        flow = {"flow_id": flow_id, "template_name": template_name,
                "required_approvers": required_approvers, "status": "active",
                "pending_approvals": [], "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_approval_flows"):
            self._approval_flows: list[dict[str, Any]] = []
        self._approval_flows.append(flow)
        return flow

    def submit_approval(self, instance_id: str, approver: str, decision: str, comment: str = "") -> bool:
        inst = self.instances.get(instance_id)
        if not inst:
            return False
        flows = getattr(self, "_approval_flows", [])
        flow = next((f for f in flows if f["template_name"] == inst.template_name), None)
        if not flow or approver not in flow["required_approvers"]:
            return False
        flow["pending_approvals"].append({
            "instance_id": instance_id, "approver": approver,
            "decision": decision, "comment": comment, "timestamp": datetime.utcnow().isoformat()
        })
        if decision == "approved" and len([a for a in flow["pending_approvals"]
                                            if a["instance_id"] == instance_id and a["decision"] == "approved"]) == len(flow["required_approvers"]):
            inst.metadata["approved"] = True
            inst.metadata["approved_at"] = datetime.utcnow().isoformat()
        return True

    def add_post_scaffold_hook(self, template_name: str, hook_type: str, hook_config: dict[str, Any]) -> dict[str, Any] | None:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            return None
        hook_id = str(uuid.uuid4())
        hook = {"hook_id": hook_id, "type": hook_type, "config": hook_config,
                "created_at": datetime.utcnow().isoformat()}
        if "post_hooks" not in tmpl:
            tmpl["post_hooks"] = []
        tmpl["post_hooks"].append(hook)
        return hook

    def execute_post_hooks(self, instance_id: str) -> list[dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return []
        tmpl = self.templates.get(inst.template_name)
        if not tmpl:
            return []
        results = []
        for hook in tmpl.get("post_hooks", []):
            result = {"hook_id": hook["hook_id"], "type": hook["type"], "status": "executed",
                       "executed_at": datetime.utcnow().isoformat()}
            if hook["type"] == "webhook":
                result["url"] = hook["config"].get("url", "")
            elif hook["type"] == "notification":
                result["channel"] = hook["config"].get("channel", "")
            elif hook["type"] == "pipeline_trigger":
                result["pipeline"] = hook["config"].get("pipeline", "")
            results.append(result)
        inst.metadata["post_hooks_executed"] = len(results)
        return results

    def get_scaffold_analytics(self) -> dict[str, Any]:
        total = len(self.instances)
        by_template: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for inst in self.instances.values():
            by_template[inst.template_name] = by_template.get(inst.template_name, 0) + 1
            by_status[inst.status] = by_status.get(inst.status, 0) + 1
        avg_steps = 0
        if self.instances:
            steps_total = sum(len(inst.current_step) for inst in self.instances.values())
            avg_steps = round(steps_total / len(self.instances), 1)
        return {"total_instances": total, "by_template": by_template,
                "by_status": by_status, "avg_steps": avg_steps}

    def validate_template(self, template_name: str) -> dict[str, Any]:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            return {"valid": False, "error": "Template not found"}
        issues = []
        if not tmpl.get("steps"):
            issues.append("No steps defined")
        for i, step in enumerate(tmpl["steps"]):
            if not step.get("name"):
                issues.append(f"Step {i} has no name")
        return {"valid": len(issues) == 0, "issues": issues, "step_count": len(tmpl.get("steps", []))}

    def estimate_template_duration(self, template_name: str) -> dict[str, Any]:
        tmpl = self.templates.get(template_name)
        if not tmpl:
            return {"error": "Template not found"}
        total_minutes = 0
        for step in tmpl.get("steps", []):
            if step.get("step_type") == "automated":
                total_minutes += 2
            elif step.get("step_type") == "manual":
                total_minutes += 30
            else:
                total_minutes += 10
        return {"template_name": template_name, "estimated_minutes": total_minutes,
                "estimated_hours": round(total_minutes / 60, 1)}

    def clone_template(self, source_name: str, new_name: str) -> dict[str, Any] | None:
        src = self.templates.get(source_name)
        if not src:
            return None
        import copy
        tmpl = copy.deepcopy(src)
        tmpl["name"] = new_name
        tmpl["created_at"] = datetime.utcnow().isoformat()
        self.templates[new_name] = tmpl
        return tmpl

    def get_instance_timeline(self, instance_id: str) -> list[dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return []
        timeline = [
            {"event": "created", "step": inst.status, "timestamp": inst.created_at.isoformat() if hasattr(inst.created_at, 'isoformat') else str(inst.created_at)}
        ]
        for step_name, step_data in inst.current_step.items() if isinstance(inst.current_step, dict) else []:
            timeline.append({"event": "step_progress", "step": step_name, "detail": str(step_data)})
        return timeline

    def batch_retire_instances(self, instance_ids: list[str]) -> int:
        count = 0
        for iid in instance_ids:
            if iid in self.instances:
                self.instances[iid].status = "retired"
                count += 1
        return count

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
