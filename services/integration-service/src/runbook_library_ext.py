"""Extended runbook templates library with versioning, categories, and automation integration."""
import json
import uuid
import logging
import yaml
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RunbookCategory(str, Enum):
    INCIDENT_RESPONSE = "incident_response"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    MONITORING = "monitoring"
    BACKUP = "backup"
    RECOVERY = "recovery"
    COMPLIANCE = "compliance"
    ONBOARDING = "onboarding"
    OFFBOARDING = "offboarding"
    AUTOMATION = "automation"
    TROUBLESHOOTING = "troubleshooting"
    CHANGE_MANAGEMENT = "change_management"
    PERFORMANCE = "performance"
    COST_OPTIMIZATION = "cost_optimization"


class RunbookStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class StepType(str, Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    SCRIPT = "script"
    API_CALL = "api_call"
    ANSIBLE = "ansible"
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    WAIT = "wait"
    DECISION = "decision"
    PARALLEL = "parallel"
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    SUB_RUNBOOK = "sub_runbook"
    HTTP_REQUEST = "http_request"
    DATABASE = "database"
    SSH = "ssh"
    FILE_OPERATION = "file_operation"


@dataclass
class RunbookStep:
    id: str
    name: str
    step_type: StepType
    order: int = 0
    description: str = ""
    command: Optional[str] = None
    script: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_method: str = "GET"
    expected_output: Optional[str] = None
    timeout_seconds: int = 300
    critical: bool = False
    requires_approval: bool = False
    verification_steps: List[str] = field(default_factory=list)
    rollback_command: Optional[str] = None
    notes: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    on_failure: str = "stop"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RunbookVersion:
    id: str
    runbook_id: str
    version: int
    steps: List[RunbookStep] = field(default_factory=list)
    changelog: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RunbookParameter:
    name: str
    type: str
    description: str
    required: bool = False
    default_value: Any = None
    validation_regex: Optional[str] = None
    options: List[str] = field(default_factory=list)
    sensitive: bool = False


@dataclass
class RunbookDefinition:
    id: str
    name: str
    description: str
    category: RunbookCategory
    status: RunbookStatus = RunbookStatus.DRAFT
    steps: List[RunbookStep] = field(default_factory=list)
    parameters: List[RunbookParameter] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: int = 1
    author: Optional[str] = None
    estimated_duration_minutes: int = 30
    severity: str = "medium"
    prerequisites: List[str] = field(default_factory=list)
    related_runbooks: List[str] = field(default_factory=list)
    review_status: str = "pending"
    last_reviewed: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RunbookExecution:
    id: str
    runbook_id: str
    runbook_name: str
    version: int
    status: str = "pending"
    parameters: Dict[str, Any] = field(default_factory=dict)
    steps_status: Dict[str, str] = field(default_factory=dict)
    output: str = ""
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    executed_by: Optional[str] = None
    triggered_by: Optional[str] = None


class RunbookLibraryManager:
    def __init__(self, storage_path: str = "data/runbook_library.json"):
        self.storage_path = storage_path
        self.runbooks: Dict[str, RunbookDefinition] = {}
        self.executions: Dict[str, RunbookExecution] = {}
        self.versions: Dict[str, List[RunbookVersion]] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for rb_data in data.get("runbooks", []):
            rb = RunbookDefinition(**rb_data)
            self.runbooks[rb.id] = rb
        for ex_data in data.get("executions", []):
            ex = RunbookExecution(**ex_data)
            self.executions[ex.id] = ex
        for ver_data in data.get("versions", []):
            ver = RunbookVersion(**ver_data)
            if ver.runbook_id not in self.versions:
                self.versions[ver.runbook_id] = []
            self.versions[ver.runbook_id].append(ver)

    def _save_data(self) -> None:
        data = {
            "runbooks": [r.__dict__ for r in self.runbooks.values()],
            "executions": [e.__dict__ for e in self.executions.values()],
            "versions": [v.__dict__ for vl in self.versions.values() for v in vl],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("RunbookLibraryManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("RunbookLibraryManager closed")

    def create_runbook(self, name: str, description: str, category: RunbookCategory, author: Optional[str] = None, tags: Optional[List[str]] = None, severity: str = "medium", estimated_duration_minutes: int = 30) -> RunbookDefinition:
        rb = RunbookDefinition(id=str(uuid.uuid4()), name=name, description=description, category=category, author=author, tags=tags or [], severity=severity, estimated_duration_minutes=estimated_duration_minutes)
        self.runbooks[rb.id] = rb
        self._save_data()
        return rb

    def get_runbook(self, runbook_id: str) -> Optional[RunbookDefinition]:
        return self.runbooks.get(runbook_id)

    def update_runbook(self, runbook_id: str, updates: Dict[str, Any]) -> Optional[RunbookDefinition]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        for key, value in updates.items():
            if hasattr(rb, key) and key not in ("id", "created_at", "author", "version"):
                setattr(rb, key, value)
        rb.updated_at = datetime.utcnow()
        self.runbooks[runbook_id] = rb
        self._save_data()
        return rb

    def delete_runbook(self, runbook_id: str) -> bool:
        if runbook_id in self.runbooks:
            del self.runbooks[runbook_id]
            if runbook_id in self.versions:
                del self.versions[runbook_id]
            self._save_data()
            return True
        return False

    def add_step(self, runbook_id: str, name: str, step_type: StepType, order: int, description: str = "", command: Optional[str] = None, script: Optional[str] = None, critical: bool = False, requires_approval: bool = False, timeout_seconds: int = 300, on_failure: str = "stop", rollback_command: Optional[str] = None, verification_steps: Optional[List[str]] = None) -> Optional[RunbookStep]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        step = RunbookStep(id=str(uuid.uuid4()), name=name, step_type=step_type, order=order, description=description, command=command, script=script, critical=critical, requires_approval=requires_approval, timeout_seconds=timeout_seconds, on_failure=on_failure, rollback_command=rollback_command, verification_steps=verification_steps or [])
        rb.steps.append(step)
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return step

    def remove_step(self, runbook_id: str, step_id: str) -> bool:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return False
        rb.steps = [s for s in rb.steps if s.id != step_id]
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def add_parameter(self, runbook_id: str, name: str, type: str, description: str, required: bool = False, default_value: Any = None, validation_regex: Optional[str] = None, options: Optional[List[str]] = None, sensitive: bool = False) -> Optional[RunbookParameter]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        param = RunbookParameter(name=name, type=type, description=description, required=required, default_value=default_value, validation_regex=validation_regex, options=options or [], sensitive=sensitive)
        rb.parameters.append(param)
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return param

    def create_version(self, runbook_id: str, changelog: Optional[str] = None, created_by: Optional[str] = None) -> Optional[RunbookVersion]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        rb.version += 1
        version = RunbookVersion(id=str(uuid.uuid4()), runbook_id=runbook_id, version=rb.version, steps=rb.steps[:], changelog=changelog, created_by=created_by)
        if runbook_id not in self.versions:
            self.versions[runbook_id] = []
        self.versions[runbook_id].append(version)
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return version

    def get_versions(self, runbook_id: str) -> List[RunbookVersion]:
        return self.versions.get(runbook_id, [])

    def publish_runbook(self, runbook_id: str) -> bool:
        rb = self.runbooks.get(runbook_id)
        if not rb or rb.status != RunbookStatus.DRAFT:
            return False
        rb.status = RunbookStatus.PUBLISHED
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def deprecate_runbook(self, runbook_id: str) -> bool:
        rb = self.runbooks.get(runbook_id)
        if not rb or rb.status != RunbookStatus.PUBLISHED:
            return False
        rb.status = RunbookStatus.DEPRECATED
        rb.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def search_runbooks(self, query: str) -> List[RunbookDefinition]:
        query = query.lower()
        results = []
        for rb in self.runbooks.values():
            if query in rb.name.lower() or query in rb.description.lower() or query in rb.category.value.lower() or any(query in t.lower() for t in rb.tags):
                results.append(rb)
        return results

    def list_runbooks(self, category: Optional[RunbookCategory] = None, status: Optional[RunbookStatus] = None) -> List[RunbookDefinition]:
        results = list(self.runbooks.values())
        if category:
            results = [r for r in results if r.category == category]
        if status:
            results = [r for r in results if r.status == status]
        return results

    def execute_runbook(self, runbook_id: str, parameters: Optional[Dict[str, Any]] = None, executed_by: Optional[str] = None, triggered_by: Optional[str] = None) -> Optional[RunbookExecution]:
        rb = self.runbooks.get(runbook_id)
        if not rb or rb.status != RunbookStatus.PUBLISHED:
            return None
        resolved_params = {}
        for param in rb.parameters:
            if param.name in (parameters or {}):
                resolved_params[param.name] = parameters[param.name]
            elif param.default_value is not None:
                resolved_params[param.name] = param.default_value
            elif param.required:
                raise ValueError(f"Required parameter '{param.name}' not provided")
        execution = RunbookExecution(id=str(uuid.uuid4()), runbook_id=runbook_id, runbook_name=rb.name, version=rb.version, status="running", parameters=resolved_params, executed_by=executed_by, triggered_by=triggered_by)
        self.executions[execution.id] = execution
        for step in sorted(rb.steps, key=lambda s: s.order):
            step_key = step.id
            execution.steps_status[step_key] = "running"
            try:
                result = self._execute_step(step, resolved_params)
                execution.steps_status[step_key] = "completed"
                execution.output += f"\n[{step.name}] {result}"
            except Exception as e:
                execution.steps_status[step_key] = "failed"
                execution.error = f"Step '{step.name}' failed: {e}"
                execution.status = "failed"
                if step.on_failure == "stop":
                    break
        if execution.status != "failed":
            execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        self._save_data()
        return execution

    def _execute_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        if step.step_type == StepType.MANUAL:
            return f"Manual step: {step.description}"
        elif step.step_type == StepType.SCRIPT:
            return self._execute_script_step(step, parameters)
        elif step.step_type == StepType.API_CALL:
            return self._execute_api_step(step, parameters)
        elif step.step_type == StepType.HTTP_REQUEST:
            return self._execute_http_step(step, parameters)
        elif step.step_type == StepType.NOTIFICATION:
            return f"Notification: {step.description}"
        elif step.step_type == StepType.WAIT:
            import time
            time.sleep(min(step.timeout_seconds, 10))
            return f"Waited {step.timeout_seconds}s"
        elif step.step_type == StepType.SSH:
            return self._execute_ssh_step(step, parameters)
        elif step.step_type == StepType.FILE_OPERATION:
            return self._execute_file_step(step, parameters)
        elif step.step_type == StepType.DATABASE:
            return f"Database operation: {step.command}"
        return f"Step '{step.name}' executed (simulated)"

    def _execute_script_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        script = step.script or step.command or ""
        local_vars = {"params": parameters, "result": ""}
        try:
            exec(script, {}, local_vars)
        except Exception as e:
            raise RuntimeError(f"Script failed: {e}")
        return str(local_vars.get("result", "Script executed"))

    def _execute_api_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        import requests
        url = step.api_endpoint or ""
        method = step.api_method or "GET"
        headers = {"Content-Type": "application/json"}
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=step.timeout_seconds)
            elif method == "POST":
                resp = requests.post(url, headers=headers, json=parameters, timeout=step.timeout_seconds)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, json=parameters, timeout=step.timeout_seconds)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, timeout=step.timeout_seconds)
            else:
                resp = requests.get(url, headers=headers, timeout=step.timeout_seconds)
            if resp.status_code >= 400:
                raise RuntimeError(f"API returned {resp.status_code}: {resp.text[:200]}")
            return f"API call to {url} returned {resp.status_code}"
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")

    def _execute_http_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        return self._execute_api_step(step, parameters)

    def _execute_ssh_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        host = parameters.get("host", "localhost")
        command = step.command or "echo 'SSH step executed'"
        return f"SSH on {host}: {command} (simulated)"

    def _execute_file_step(self, step: RunbookStep, parameters: Dict[str, Any]) -> str:
        operation = step.command or "list"
        path = parameters.get("path", "/tmp")
        return f"File operation '{operation}' on {path} (simulated)"

    def get_execution(self, execution_id: str) -> Optional[RunbookExecution]:
        return self.executions.get(execution_id)

    def get_executions(self, runbook_id: Optional[str] = None, status: Optional[str] = None) -> List[RunbookExecution]:
        results = list(self.executions.values())
        if runbook_id:
            results = [e for e in results if e.runbook_id == runbook_id]
        if status:
            results = [e for e in results if e.status == status]
        return sorted(results, key=lambda x: x.started_at, reverse=True)

    def export_runbook_yaml(self, runbook_id: str) -> Optional[str]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        export = {"name": rb.name, "description": rb.description, "category": rb.category.value, "version": rb.version, "author": rb.author, "severity": rb.severity, "estimated_duration_minutes": rb.estimated_duration_minutes, "tags": rb.tags, "prerequisites": rb.prerequisites, "parameters": [], "steps": []}
        for param in rb.parameters:
            export["parameters"].append({"name": param.name, "type": param.type, "description": param.description, "required": param.required, "default_value": param.default_value})
        for step in rb.steps:
            export["steps"].append({"name": step.name, "type": step.step_type.value, "order": step.order, "description": step.description, "command": step.command, "critical": step.critical, "timeout_seconds": step.timeout_seconds, "on_failure": step.on_failure})
        return yaml.dump(export, default_flow_style=False)

    def import_runbook_yaml(self, yaml_content: str, author: Optional[str] = None) -> Optional[RunbookDefinition]:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return None
        rb = self.create_runbook(name=data.get("name", "Imported Runbook"), description=data.get("description", ""), category=RunbookCategory(data.get("category", "troubleshooting")), author=author, tags=data.get("tags", []), severity=data.get("severity", "medium"), estimated_duration_minutes=data.get("estimated_duration_minutes", 30))
        for param_data in data.get("parameters", []):
            self.add_parameter(runbook_id=rb.id, name=param_data.get("name", "param"), type=param_data.get("type", "string"), description=param_data.get("description", ""), required=param_data.get("required", False), default_value=param_data.get("default_value"))
        for step_data in data.get("steps", []):
            self.add_step(runbook_id=rb.id, name=step_data.get("name", "Step"), step_type=StepType(step_data.get("type", "manual")), order=step_data.get("order", 0), description=step_data.get("description", ""), command=step_data.get("command"), critical=step_data.get("critical", False), timeout_seconds=step_data.get("timeout_seconds", 300), on_failure=step_data.get("on_failure", "stop"))
        return rb

    def get_statistics(self) -> Dict[str, Any]:
        total_runbooks = len(self.runbooks)
        published = sum(1 for r in self.runbooks.values() if r.status == RunbookStatus.PUBLISHED)
        draft = sum(1 for r in self.runbooks.values() if r.status == RunbookStatus.DRAFT)
        deprecated = sum(1 for r in self.runbooks.values() if r.status == RunbookStatus.DEPRECATED)
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.status == "completed")
        failed = sum(1 for e in self.executions.values() if e.status == "failed")
        by_category = {}
        for r in self.runbooks.values():
            by_category[r.category.value] = by_category.get(r.category.value, 0) + 1
        return {"total_runbooks": total_runbooks, "published": published, "draft": draft, "deprecated": deprecated, "total_executions": total_executions, "successful_executions": successful, "failed_executions": failed, "by_category": by_category, "total_steps": sum(len(r.steps) for r in self.runbooks.values())}

    def bulk_publish(self, runbook_ids: List[str]) -> int:
        count = 0
        for rid in runbook_ids:
            if self.publish_runbook(rid):
                count += 1
        return count

    def clone_runbook(self, runbook_id: str, new_name: str) -> Optional[RunbookDefinition]:
        rb = self.runbooks.get(runbook_id)
        if not rb:
            return None
        clone = self.create_runbook(name=new_name, description=rb.description, category=rb.category, author=rb.author, tags=rb.tags[:], severity=rb.severity, estimated_duration_minutes=rb.estimated_duration_minutes)
        for step in rb.steps:
            self.add_step(runbook_id=clone.id, name=step.name, step_type=step.step_type, order=step.order, description=step.description, command=step.command, script=step.script, critical=step.critical, requires_approval=step.requires_approval, timeout_seconds=step.timeout_seconds, on_failure=step.on_failure, rollback_command=step.rollback_command, verification_steps=step.verification_steps)
        for param in rb.parameters:
            self.add_parameter(runbook_id=clone.id, name=param.name, type=param.type, description=param.description, required=param.required, default_value=param.default_value, validation_regex=param.validation_regex, options=param.options, sensitive=param.sensitive)
        return clone
