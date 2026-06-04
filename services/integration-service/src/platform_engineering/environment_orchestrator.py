"""Environment Orchestrator — Self-service ephemeral environments per PR/branch."""

import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnvironmentStatus(str, Enum):
    PROVISIONING = "provisioning"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED = "failed"


class EnvironmentType(str, Enum):
    PR = "pr"
    BRANCH = "branch"
    FEATURE = "feature"
    REVIEW_APP = "review_app"
    EPHEMERAL = "ephemeral"


class EnvironmentTemplate:
    def __init__(self, template_id: str, name: str, description: str):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.services: list[dict[str, Any]] = []
        self.resources: dict[str, Any] = {
            "cpu_limit": "1.0",
            "memory_limit": "1Gi",
            "storage_limit": "10Gi",
            "replicas": 1,
        }
        self.network_policies: list[str] = []
        self.env_variables: dict[str, str] = {}
        self.secrets: list[str] = []
        self.data_seeding: dict[str, Any] = {}
        self.test_data_config: dict[str, Any] = {}
        self.ttl_hours: int = 24
        self.created_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "services": self.services,
            "resources": self.resources,
            "network_policies": self.network_policies,
            "env_variables": self.env_variables,
            "secrets": self.secrets,
            "data_seeding": self.data_seeding,
            "test_data_config": self.test_data_config,
            "ttl_hours": self.ttl_hours,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentTemplate":
        et = cls(data["template_id"], data["name"], data["description"])
        et.services = data.get("services", [])
        et.resources = data.get("resources", et.resources)
        et.network_policies = data.get("network_policies", [])
        et.env_variables = data.get("env_variables", {})
        et.secrets = data.get("secrets", [])
        et.data_seeding = data.get("data_seeding", {})
        et.test_data_config = data.get("test_data_config", {})
        et.ttl_hours = data.get("ttl_hours", 24)
        if data.get("created_at"):
            et.created_at = datetime.fromisoformat(data["created_at"])
        return et


class EphemeralEnvironment:
    def __init__(self, env_id: str, name: str, env_type: EnvironmentType,
                 template_id: str, project: str, created_by: str):
        self.env_id = env_id
        self.name = name
        self.env_type = env_type
        self.template_id = template_id
        self.project = project
        self.created_by = created_by
        self.status: EnvironmentStatus = EnvironmentStatus.PROVISIONING
        self.branch: str = ""
        self.pr_number: int = 0
        self.pr_url: str = ""
        self.commit_sha: str = ""
        self.services: dict[str, dict[str, Any]] = {}
        self.endpoints: dict[str, str] = {}
        self.resources: dict[str, Any] = {}
        self.data_snapshot_id: str = ""
        self.ttl_hours: int = 24
        self.expires_at: Optional[datetime] = None
        self.auto_cleanup: bool = True
        self.labels: dict[str, str] = {}
        self.events: list[dict[str, Any]] = []
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.terminated_at: Optional[datetime] = None

    def add_event(self, event_type: str, message: str, metadata: dict[str, Any] = None):
        self.events.append({
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "env_id": self.env_id,
            "name": self.name,
            "env_type": self.env_type.value,
            "template_id": self.template_id,
            "project": self.project,
            "created_by": self.created_by,
            "status": self.status.value,
            "branch": self.branch,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "commit_sha": self.commit_sha,
            "services": self.services,
            "endpoints": self.endpoints,
            "resources": self.resources,
            "data_snapshot_id": self.data_snapshot_id,
            "ttl_hours": self.ttl_hours,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_cleanup": self.auto_cleanup,
            "labels": self.labels,
            "events": self.events,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "terminated_at": self.terminated_at.isoformat() if self.terminated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EphemeralEnvironment":
        env = cls(
            data["env_id"], data["name"],
            EnvironmentType(data["env_type"]),
            data["template_id"], data["project"], data["created_by"],
        )
        env.status = EnvironmentStatus(data.get("status", "provisioning"))
        env.branch = data.get("branch", "")
        env.pr_number = data.get("pr_number", 0)
        env.pr_url = data.get("pr_url", "")
        env.commit_sha = data.get("commit_sha", "")
        env.services = data.get("services", {})
        env.endpoints = data.get("endpoints", {})
        env.resources = data.get("resources", {})
        env.data_snapshot_id = data.get("data_snapshot_id", "")
        env.ttl_hours = data.get("ttl_hours", 24)
        if data.get("expires_at"):
            env.expires_at = datetime.fromisoformat(data["expires_at"])
        env.auto_cleanup = data.get("auto_cleanup", True)
        env.labels = data.get("labels", {})
        env.events = data.get("events", [])
        if data.get("created_at"):
            env.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            env.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("terminated_at"):
            env.terminated_at = datetime.fromisoformat(data["terminated_at"])
        return env


class EnvironmentOrchestrator:
    def __init__(self):
        self.environments: dict[str, EphemeralEnvironment] = {}
        self.templates: dict[str, EnvironmentTemplate] = {}
        self.provisioning_queue: list[dict[str, Any]] = []

    def create_template(self, name: str, description: str) -> EnvironmentTemplate:
        tid = str(uuid.uuid4())
        tmpl = EnvironmentTemplate(tid, name, description)
        self.templates[tid] = tmpl
        return tmpl

    def get_template(self, template_id: str) -> Optional[EnvironmentTemplate]:
        return self.templates.get(template_id)

    def list_templates(self) -> list[EnvironmentTemplate]:
        return list(self.templates.values())

    def provision_environment(self, name: str, env_type: EnvironmentType,
                               template_id: str, project: str, created_by: str,
                               branch: str = "", pr_number: int = 0,
                               pr_url: str = "", ttl_hours: int = 24) -> Optional[EphemeralEnvironment]:
        tmpl = self.templates.get(template_id)
        if not tmpl:
            logger.warning("Template %s not found", template_id)
            return None
        env_id = str(uuid.uuid4())
        env = EphemeralEnvironment(env_id, name, env_type, template_id, project, created_by)
        env.branch = branch
        env.pr_number = pr_number
        env.pr_url = pr_url
        env.ttl_hours = ttl_hours
        env.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        env.resources = dict(tmpl.resources)
        env.add_event("provisioning_started", f"Environment {name} provisioning started", {
            "template": tmpl.name, "type": env_type.value, "branch": branch,
        })
        self.environments[env_id] = env
        self.provisioning_queue.append({
            "env_id": env_id,
            "template_id": template_id,
            "queued_at": datetime.utcnow().isoformat(),
        })
        logger.info("Provisioning environment %s for %s/%s using template %s", name, project, branch, template_id)
        return env

    def get_environment(self, env_id: str) -> Optional[EphemeralEnvironment]:
        return self.environments.get(env_id)

    def update_environment_status(self, env_id: str, status: EnvironmentStatus) -> Optional[EphemeralEnvironment]:
        env = self.environments.get(env_id)
        if not env:
            return None
        env.status = status
        env.updated_at = datetime.utcnow()
        env.add_event("status_changed", f"Status changed to {status.value}")
        return env

    def register_endpoint(self, env_id: str, service_name: str, endpoint_url: str) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.endpoints[service_name] = endpoint_url
        env.add_event("endpoint_registered", f"Endpoint for {service_name}: {endpoint_url}")
        return True

    def terminate_environment(self, env_id: str) -> Optional[EphemeralEnvironment]:
        env = self.environments.get(env_id)
        if not env:
            return None
        env.status = EnvironmentStatus.TERMINATING
        env.updated_at = datetime.utcnow()
        env.add_event("termination_started", f"Environment termination initiated")
        return env

    def complete_termination(self, env_id: str) -> Optional[EphemeralEnvironment]:
        env = self.environments.get(env_id)
        if not env:
            return None
        env.status = EnvironmentStatus.TERMINATED
        env.terminated_at = datetime.utcnow()
        env.add_event("terminated", "Environment terminated and cleaned up")
        return env

    def list_environments(self, project: str = "", created_by: str = "", status: str = "",
                          env_type: str = "") -> list[EphemeralEnvironment]:
        results = list(self.environments.values())
        if project:
            results = [e for e in results if e.project == project]
        if created_by:
            results = [e for e in results if e.created_by == created_by]
        if status:
            results = [e for e in results if e.status.value == status]
        if env_type:
            results = [e for e in results if e.env_type.value == env_type]
        return sorted(results, key=lambda e: e.created_at, reverse=True)

    def find_by_pr(self, pr_number: int, project: str) -> list[EphemeralEnvironment]:
        return [
            e for e in self.environments.values()
            if e.pr_number == pr_number and e.project == project and e.status != EnvironmentStatus.TERMINATED
        ]

    def find_by_branch(self, branch: str, project: str) -> list[EphemeralEnvironment]:
        return [
            e for e in self.environments.values()
            if e.branch == branch and e.project == project and e.status != EnvironmentStatus.TERMINATED
        ]

    def cleanup_expired(self) -> list[str]:
        now = datetime.utcnow()
        expired = []
        for env_id, env in self.environments.items():
            if env.expires_at and now >= env.expires_at and env.status not in (
                EnvironmentStatus.TERMINATED, EnvironmentStatus.TERMINATING, EnvironmentStatus.FAILED
            ):
                self.terminate_environment(env_id)
                expired.append(env_id)
        if expired:
            logger.info("Auto-cleanup: terminating %d expired environments", len(expired))
        return expired

    def get_environments_summary(self) -> dict[str, Any]:
        total = len(self.environments)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_project: dict[str, int] = {}
        for env in self.environments.values():
            by_status[env.status.value] = by_status.get(env.status.value, 0) + 1
            by_type[env.env_type.value] = by_type.get(env.env_type.value, 0) + 1
            by_project[env.project] = by_project.get(env.project, 0) + 1
        running = by_status.get("running", 0)
        return {
            "total_environments": total,
            "running": running,
            "provisioning": by_status.get("provisioning", 0),
            "terminated": by_status.get("terminated", 0),
            "by_type": by_type,
            "by_project": by_project,
            "total_templates": len(self.templates),
            "expired_this_cycle": len(self.cleanup_expired()),
            "average_ttl": round(
                sum((e.expires_at - e.created_at).total_seconds() for e in self.environments.values()
                    if e.expires_at) / max(total, 1) / 3600, 1
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "environments": {eid: e.to_dict() for eid, e in self.environments.items()},
            "templates": {tid: t.to_dict() for tid, t in self.templates.items()},
            "provisioning_queue": self.provisioning_queue,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentOrchestrator":
        orch = cls()
        for eid, edata in data.get("environments", {}).items():
            orch.environments[eid] = EphemeralEnvironment.from_dict(edata)
        for tid, tdata in data.get("templates", {}).items():
            orch.templates[tid] = EnvironmentTemplate.from_dict(tdata)
        orch.provisioning_queue = data.get("provisioning_queue", [])
        return orch

    def bulk_terminate_environments(self, env_ids: list[str]) -> int:
        count = 0
        for eid in env_ids:
            if self.terminate_environment(eid):
                count += 1
        return count

    def schedule_environment(self, name: str, template_id: str, project: str, created_by: str,
                              scheduled_start: datetime, ttl_hours: int = 24,
                              env_type: EnvironmentType = EnvironmentType.EPHEMERAL) -> Optional[EphemeralEnvironment]:
        env = self.provision_environment(name, env_type, template_id, project, created_by, ttl_hours=ttl_hours)
        if env:
            env.status = EnvironmentStatus.PROVISIONING
            env.add_event("scheduled", f"Scheduled for {scheduled_start.isoformat()}")
            env.metadata["scheduled_start"] = scheduled_start.isoformat()
            env.metadata["scheduled"] = True
        return env

    def get_resource_utilization(self) -> dict[str, Any]:
        running = [e for e in self.environments.values() if e.status == EnvironmentStatus.RUNNING]
        total_cpu = sum(float(e.resources.get("cpu_limit", 1.0)) for e in running) if running else 0
        total_memory = sum(int(e.resources.get("memory_limit", "1Gi").rstrip("Gi")) for e in running if "memory_limit" in e.resources) if running else 0
        total_storage = sum(int(e.resources.get("storage_limit", "10Gi").rstrip("Gi")) for e in running if "storage_limit" in e.resources) if running else 0
        return {
            "running_count": len(running),
            "total_cpu_allocated": total_cpu,
            "total_memory_gb": total_memory,
            "total_storage_gb": total_storage,
            "avg_ttl_hours": round(
                sum(e.ttl_hours for e in self.environments.values()) / max(len(self.environments), 1), 1
            ),
            "expired_count": len(self.cleanup_expired()),
        }

    def provision_from_template_name(self, name: str, template_name: str, project: str, created_by: str,
                                      branch: str = "", ttl_hours: int = 24) -> Optional[EphemeralEnvironment]:
        tmpl = next((t for t in self.templates.values() if t.name == template_name), None)
        if not tmpl:
            return None
        return self.provision_environment(name, EnvironmentType.EPHEMERAL, tmpl.template_id,
                                           project, created_by, branch=branch, ttl_hours=ttl_hours)

    def batch_provision(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for req in requests:
            try:
                env = self.provision_environment(
                    req["name"], EnvironmentType(req.get("env_type", "ephemeral")),
                    req["template_id"], req["project"], req["created_by"],
                    branch=req.get("branch", ""), pr_number=req.get("pr_number", 0),
                    ttl_hours=req.get("ttl_hours", 24),
                )
                if env:
                    results.append({"env_id": env.env_id, "name": req["name"], "status": "provisioned"})
                else:
                    results.append({"name": req["name"], "status": "failed", "error": "Template not found"})
            except Exception as e:
                results.append({"name": req.get("name", "unknown"), "status": "error", "error": str(e)})
        return results

    def export_environments(self, project: str = "") -> list[dict[str, Any]]:
        envs = self.list_environments(project=project) if project else list(self.environments.values())
        return [e.to_dict() for e in envs]

    def get_environment_events(self, env_id: str) -> list[dict[str, Any]]:
        env = self.environments.get(env_id)
        if not env:
            return []
        return env.events

    def set_environment_ttl(self, env_id: str, ttl_hours: int) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.ttl_hours = ttl_hours
        env.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        return True

    def get_provisioning_queue_status(self) -> list[dict[str, Any]]:
        return self.provisioning_queue

    def delete_template(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def set_cleanup_policy(self, project: str, max_age_hours: int = 72,
                            auto_delete: bool = True, notify_before_hours: int = 24) -> dict[str, Any]:
        policy_id = str(uuid.uuid4())
        policy = {
            "policy_id": policy_id, "project": project, "max_age_hours": max_age_hours,
            "auto_delete": auto_delete, "notify_before_hours": notify_before_hours,
            "created_at": datetime.utcnow().isoformat(), "status": "active",
        }
        if not hasattr(self, "_cleanup_policies"):
            self._cleanup_policies: list[dict[str, Any]] = []
        self._cleanup_policies.append(policy)
        return policy

    def get_cleanup_policies(self, project: str = "") -> list[dict[str, Any]]:
        policies = getattr(self, "_cleanup_policies", [])
        if project:
            return [p for p in policies if p["project"] == project]
        return policies

    def apply_cleanup_policies(self) -> dict[str, Any]:
        now = datetime.utcnow()
        deleted = 0
        warned = 0
        for policy in getattr(self, "_cleanup_policies", []):
            if policy["status"] != "active":
                continue
            for env in self.environments.values():
                if env.project != policy["project"]:
                    continue
                age_hours = (now - env.created_at).total_seconds() / 3600
                if age_hours > policy["max_age_hours"]:
                    if policy["auto_delete"]:
                        if env.env_id in self.environments:
                            del self.environments[env.env_id]
                            deleted += 1
                    else:
                        warned += 1
        return {"deleted": deleted, "warned": warned}

    def set_resource_quota(self, project: str, max_cpu: int = 8, max_memory_gb: int = 32,
                            max_environments: int = 5) -> dict[str, Any]:
        quota_id = str(uuid.uuid4())
        quota = {
            "quota_id": quota_id, "project": project,
            "max_cpu": max_cpu, "max_memory_gb": max_memory_gb,
            "max_environments": max_environments,
            "created_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_resource_quotas"):
            self._resource_quotas: list[dict[str, Any]] = []
        self._resource_quotas.append(quota)
        return quota

    def check_resource_quota(self, project: str) -> dict[str, Any]:
        quotas = [q for q in getattr(self, "_resource_quotas", []) if q["project"] == project]
        if not quotas:
            return {"error": "No quota defined for project"}
        quota = quotas[0]
        envs = [e for e in self.environments.values() if e.project == project]
        total_cpu = sum(e.template.get("cpu", 1) if isinstance(e.template, dict) else 1 for e in envs)
        total_mem = sum(e.template.get("memory_gb", 2) if isinstance(e.template, dict) else 2 for e in envs)
        return {
            "project": project, "environments": len(envs),
            "cpu_used": total_cpu, "cpu_limit": quota["max_cpu"],
            "memory_used_gb": total_mem, "memory_limit_gb": quota["max_memory_gb"],
            "env_limit": quota["max_environments"],
            "cpu_pct": round(total_cpu / max(quota["max_cpu"], 1) * 100, 1),
            "memory_pct": round(total_mem / max(quota["max_memory_gb"], 1) * 100, 1),
            "env_pct": round(len(envs) / max(quota["max_environments"], 1) * 100, 1),
        }

    def backup_environment(self, env_id: str) -> dict[str, Any] | None:
        env = self.environments.get(env_id)
        if not env:
            return None
        backup_id = str(uuid.uuid4())
        backup = {
            "backup_id": backup_id, "env_id": env_id, "project": env.project,
            "template": env.template, "created_at": datetime.utcnow().isoformat(),
            "events": list(env.events),
        }
        if not hasattr(self, "_backups"):
            self._backups: dict[str, list[dict[str, Any]]] = {}
        if env_id not in self._backups:
            self._backups[env_id] = []
        self._backups[env_id].append(backup)
        return backup

    def restore_environment(self, backup_id: str) -> dict[str, Any] | None:
        backups = getattr(self, "_backups", {})
        for env_id, env_backups in backups.items():
            for b in env_backups:
                if b["backup_id"] == backup_id:
                    env = EnvironmentOrchestrator.Environment(env_id, b["project"], b["template"])
                    env.events = list(b["events"])
                    self.environments[env_id] = env
                    return {"env_id": env_id, "restored_from": backup_id, "status": "restored"}
        return None

    def list_backups(self, env_id: str = "") -> list[dict[str, Any]]:
        backups = getattr(self, "_backups", {})
        if env_id:
            return backups.get(env_id, [])
        result = []
        for env_bk in backups.values():
            result.extend(env_bk)
        return result

    def get_environment_health(self, env_id: str) -> dict[str, Any]:
        env = self.environments.get(env_id)
        if not env:
            return {"error": "Environment not found"}
        now = datetime.utcnow()
        is_expired = env.expires_at and now > env.expires_at
        age_hours = (now - env.created_at).total_seconds() / 3600
        return {
            "env_id": env_id, "name": env.name, "status": env.status,
            "age_hours": round(age_hours, 1), "is_expired": bool(is_expired),
            "ttl_hours": env.ttl_hours, "events_count": len(env.events),
            "provisioning_status": env.provisioning_status,
        }

    def bulk_delete_expired(self) -> int:
        now = datetime.utcnow()
        to_delete = [eid for eid, env in self.environments.items()
                     if env.expires_at and now > env.expires_at]
        for eid in to_delete:
            del self.environments[eid]
        return len(to_delete)

    def get_project_summary(self, project: str) -> dict[str, Any]:
        envs = [e for e in self.environments.values() if e.project == project]
        return {
            "project": project, "total_environments": len(envs),
            "active": len([e for e in envs if e.status == "active"]),
            "provisioning": len([e for e in envs if e.provisioning_status == "provisioning"]),
            "expired": len([e for e in envs if e.expires_at and datetime.utcnow() > e.expires_at]),
        }

    def extend_environment_ttl(self, env_id: str, extra_hours: int) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.ttl_hours = (env.ttl_hours or 0) + extra_hours
        if env.expires_at:
            env.expires_at = env.expires_at + timedelta(hours=extra_hours)
        else:
            env.expires_at = datetime.utcnow() + timedelta(hours=env.ttl_hours)
        return True

    def batch_set_template(self, env_ids: list[str], template_id: str) -> int:
        count = 0
        for eid in env_ids:
            env = self.environments.get(eid)
            if env and template_id in self.templates:
                env.template = template_id
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
