"""Extended workflow studio with drag-drop designer, versioning, triggers, and templates."""
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


class WorkflowTriggerType(str, Enum):
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"
    MANUAL = "manual"
    API = "api"
    FILE_WATCH = "file_watch"
    CONDITION = "condition"
    SLA = "sla"


class WorkflowStepType(str, Enum):
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SUB_WORKFLOW = "sub_workflow"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    TRANSFORM = "transform"
    WEBHOOK_CALL = "webhook_call"
    SCRIPT = "script"
    ANSIBLE_PLAYBOOK = "ansible_playbook"
    SALT_STATE = "salt_state"
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    JIRA = "jira"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class WorkflowExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    id: str
    name: str
    step_type: WorkflowStepType
    config: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 3600
    retry_count: int = 0
    retry_delay_seconds: int = 60
    depends_on: List[str] = field(default_factory=list)
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    run_after: List[str] = field(default_factory=list)
    on_failure: str = "fail"
    on_success: List[str] = field(default_factory=list)
    condition_expression: Optional[str] = None
    loop_over: Optional[str] = None
    max_parallel: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowTrigger:
    id: str
    trigger_type: WorkflowTriggerType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    event_filter: Optional[Dict[str, Any]] = None
    webhook_secret: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    category: str
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowVersion:
    id: str
    workflow_id: str
    version: int
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    changelog: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    version: int
    status: WorkflowExecutionStatus
    trigger_id: Optional[str] = None
    trigger_type: Optional[str] = None
    input: Dict[str, Any] = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    executed_by: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    status: WorkflowStatus
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    current_version: int = 1
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timeout_seconds: int = 86400
    max_concurrent_executions: int = 10
    preserve_execution_logs_days: int = 90
    error_handling: Dict[str, Any] = field(default_factory=lambda: {"default_on_failure": "fail", "max_retries": 3})
    notifications: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class WorkflowStudioManager:
    def __init__(self, storage_path: str = "data/workflow_studio.json"):
        self.storage_path = storage_path
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.versions: Dict[str, List[WorkflowVersion]] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for wf_data in data.get("workflows", []):
            wf = WorkflowDefinition(**wf_data)
            self.workflows[wf.id] = wf
        for exec_data in data.get("executions", []):
            exec_obj = WorkflowExecution(**exec_data)
            self.executions[exec_obj.id] = exec_obj
        for tmpl_data in data.get("templates", []):
            tmpl = WorkflowTemplate(**tmpl_data)
            self.templates[tmpl.id] = tmpl
        for ver_data in data.get("versions", []):
            ver = WorkflowVersion(**ver_data)
            if ver.workflow_id not in self.versions:
                self.versions[ver.workflow_id] = []
            self.versions[ver.workflow_id].append(ver)

    def _save_data(self) -> None:
        data = {
            "workflows": [wf.__dict__ for wf in self.workflows.values()],
            "executions": [e.__dict__ for e in self.executions.values()],
            "templates": [t.__dict__ for t in self.templates.values()],
            "versions": [v.__dict__ for vl in self.versions.values() for v in vl],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("WorkflowStudioManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("WorkflowStudioManager closed")

    def create_workflow(self, name: str, description: str, created_by: Optional[str] = None, category: Optional[str] = None, tags: Optional[List[str]] = None) -> WorkflowDefinition:
        wf = WorkflowDefinition(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            status=WorkflowStatus.DRAFT,
            tags=tags or [],
            category=category,
            created_by=created_by,
        )
        self.workflows[wf.id] = wf
        self._save_data()
        logger.info(f"Created workflow {wf.id}: {name}")
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self.workflows.get(workflow_id)

    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[WorkflowDefinition]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        for key, value in updates.items():
            if hasattr(wf, key) and key not in ("id", "created_at", "current_version", "created_by"):
                setattr(wf, key, value)
        wf.updated_at = datetime.utcnow()
        self.workflows[workflow_id] = wf
        self._save_data()
        logger.info(f"Updated workflow {workflow_id}")
        return wf

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            self._save_data()
            logger.info(f"Deleted workflow {workflow_id}")
            return True
        return False

    def add_step(self, workflow_id: str, step: WorkflowStep) -> Optional[WorkflowDefinition]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        wf.steps.append(step)
        wf.updated_at = datetime.utcnow()
        wf.current_version += 1
        self._save_data()
        return wf

    def update_step(self, workflow_id: str, step_id: str, updates: Dict[str, Any]) -> Optional[WorkflowStep]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        for step in wf.steps:
            if step.id == step_id:
                for key, value in updates.items():
                    if hasattr(step, key) and key != "id":
                        setattr(step, key, value)
                step.updated_at = datetime.utcnow()
                wf.updated_at = datetime.utcnow()
                self._save_data()
                return step
        return None

    def remove_step(self, workflow_id: str, step_id: str) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        wf.steps = [s for s in wf.steps if s.id != step_id]
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def reorder_steps(self, workflow_id: str, step_ids: List[str]) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        step_map = {s.id: s for s in wf.steps}
        wf.steps = [step_map[sid] for sid in step_ids if sid in step_map]
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def create_trigger(self, workflow_id: str, trigger_type: WorkflowTriggerType, name: str, config: Optional[Dict[str, Any]] = None, cron_expression: Optional[str] = None) -> Optional[WorkflowTrigger]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        trigger = WorkflowTrigger(
            id=str(uuid.uuid4()),
            trigger_type=trigger_type,
            name=name,
            config=config or {},
            cron_expression=cron_expression,
            webhook_secret=secrets.token_hex(32) if trigger_type == WorkflowTriggerType.WEBHOOK else None,
        )
        wf.triggers.append(trigger)
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return trigger

    def delete_trigger(self, workflow_id: str, trigger_id: str) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        wf.triggers = [t for t in wf.triggers if t.id != trigger_id]
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def create_version(self, workflow_id: str, changelog: Optional[str] = None, created_by: Optional[str] = None) -> Optional[WorkflowVersion]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        wf.current_version += 1
        version = WorkflowVersion(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            version=wf.current_version,
            steps=wf.steps[:],
            triggers=wf.triggers[:],
            variables=wf.variables.copy(),
            changelog=changelog,
            created_by=created_by,
        )
        if workflow_id not in self.versions:
            self.versions[workflow_id] = []
        self.versions[workflow_id].append(version)
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return version

    def get_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        return self.versions.get(workflow_id, [])

    def rollback_to_version(self, workflow_id: str, version: int) -> Optional[WorkflowDefinition]:
        versions = self.versions.get(workflow_id, [])
        target = next((v for v in versions if v.version == version), None)
        if not target:
            return None
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        wf.steps = target.steps[:]
        wf.triggers = target.triggers[:]
        wf.variables = target.variables.copy()
        wf.current_version += 1
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return wf

    def execute_workflow(self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None, executed_by: Optional[str] = None) -> Optional[WorkflowExecution]:
        wf = self.workflows.get(workflow_id)
        if not wf or wf.status != WorkflowStatus.ACTIVE:
            return None
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            version=wf.current_version,
            status=WorkflowExecutionStatus.PENDING,
            input=input_data or {},
            executed_by=executed_by,
            started_at=datetime.utcnow(),
        )
        self.executions[execution.id] = execution
        self._save_data()
        execution.status = WorkflowExecutionStatus.RUNNING
        for step in wf.steps:
            execution.current_step = step.id
            execution.step_results[step.id] = {"status": "running", "started_at": datetime.utcnow().isoformat()}
            try:
                result = self._execute_step(step, execution.input)
                execution.step_results[step.id] = {"status": "completed", "result": result, "completed_at": datetime.utcnow().isoformat()}
            except Exception as e:
                execution.step_results[step.id] = {"status": "failed", "error": str(e), "failed_at": datetime.utcnow().isoformat()}
                execution.status = WorkflowExecutionStatus.FAILED
                execution.error = str(e)
                execution.completed_at = datetime.utcnow()
                execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
                self._save_data()
                return execution
        execution.status = WorkflowExecutionStatus.SUCCEEDED
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        self._save_data()
        return execution

    def _execute_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if step.step_type == WorkflowStepType.HTTP_REQUEST:
            return self._execute_http_step(step, input_data)
        elif step.step_type == WorkflowStepType.SCRIPT:
            return self._execute_script_step(step, input_data)
        elif step.step_type == WorkflowStepType.NOTIFICATION:
            return self._execute_notification_step(step, input_data)
        elif step.step_type == WorkflowStepType.TRANSFORM:
            return self._execute_transform_step(step, input_data)
        elif step.step_type == WorkflowStepType.APPROVAL:
            return {"approved": True, "approved_by": None}
        elif step.step_type == WorkflowStepType.CONDITION:
            return self._execute_condition_step(step, input_data)
        return {"executed": True, "step_type": step.step_type.value}

    def _execute_http_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import requests
        method = step.config.get("method", "GET")
        url = step.config.get("url", "")
        headers = step.config.get("headers", {})
        body = step.config.get("body", input_data)
        timeout = step.config.get("timeout", 30)
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=body, timeout=timeout)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=timeout)
        else:
            resp = requests.get(url, headers=headers, timeout=timeout)
        return {"status_code": resp.status_code, "body": resp.text, "headers": dict(resp.headers)}

    def _execute_script_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        script = step.config.get("script", "")
        language = step.config.get("language", "python")
        local_vars = {"input": input_data, "result": {}}
        try:
            exec(script, {}, local_vars)
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {e}")
        return local_vars.get("result", {"executed": True})

    def _execute_notification_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        channel = step.config.get("channel", "log")
        message = step.config.get("message", "Workflow step executed")
        level = step.config.get("level", "info")
        if channel == "log":
            getattr(logger, level, logger.info)(f"Notification: {message}")
        return {"channel": channel, "message": message, "sent": True}

    def _execute_transform_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        mapping = step.config.get("mapping", {})
        result = {}
        for target_key, source_expr in mapping.items():
            if isinstance(source_expr, str) and source_expr.startswith("$."):
                path = source_expr[2:].split(".")
                value = input_data
                for key in path:
                    if isinstance(value, dict):
                        value = value.get(key, None)
                    else:
                        value = None
                        break
                result[target_key] = value
            else:
                result[target_key] = source_expr
        return {"transformed": result}

    def _execute_condition_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        field_path = step.config.get("field", "")
        operator = step.config.get("operator", "equals")
        expected_value = step.config.get("value", None)
        path_parts = field_path.split(".")
        actual_value = input_data
        for part in path_parts:
            if isinstance(actual_value, dict):
                actual_value = actual_value.get(part, None)
            else:
                actual_value = None
                break
        if operator == "equals":
            result = actual_value == expected_value
        elif operator == "not_equals":
            result = actual_value != expected_value
        elif operator == "contains":
            result = expected_value in (actual_value if isinstance(actual_value, (str, list)) else str(actual_value))
        elif operator == "greater_than":
            result = (actual_value or 0) > (expected_value or 0)
        elif operator == "less_than":
            result = (actual_value or 0) < (expected_value or 0)
        elif operator == "exists":
            result = actual_value is not None
        elif operator == "not_exists":
            result = actual_value is None
        else:
            result = actual_value == expected_value
        return {"condition_result": result, "field": field_path, "operator": operator, "expected": expected_value, "actual": actual_value}

    def create_template(self, name: str, description: str, category: str, steps: Optional[List[Dict[str, Any]]] = None, icon: Optional[str] = None, tags: Optional[List[str]] = None) -> WorkflowTemplate:
        template_steps = []
        if steps:
            for s in steps:
                template_steps.append(WorkflowStep(id=str(uuid.uuid4()), name=s.get("name", "Step"), step_type=WorkflowStepType(s.get("type", "task")), config=s.get("config", {})))
        tmpl = WorkflowTemplate(id=str(uuid.uuid4()), name=name, description=description, category=category, steps=template_steps, tags=tags or [], icon=icon)
        self.templates[tmpl.id] = tmpl
        self._save_data()
        return tmpl

    def get_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        return self.templates.get(template_id)

    def apply_template(self, template_id: str, name: str, description: str, created_by: Optional[str] = None) -> Optional[WorkflowDefinition]:
        tmpl = self.templates.get(template_id)
        if not tmpl:
            return None
        wf = self.create_workflow(name=name, description=description, created_by=created_by, category=tmpl.category)
        wf.steps = [WorkflowStep(id=str(uuid.uuid4()), name=s.name, step_type=s.step_type, config=s.config.copy()) for s in tmpl.steps]
        wf.variables = {k: {"default": v.get("default"), "type": v.get("type", "string"), "required": v.get("required", False)} for k, v in tmpl.variables.items()}
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return wf

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self.executions.get(execution_id)

    def cancel_execution(self, execution_id: str) -> bool:
        exec_obj = self.executions.get(execution_id)
        if not exec_obj or exec_obj.status in (WorkflowExecutionStatus.SUCCEEDED, WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.CANCELLED):
            return False
        exec_obj.status = WorkflowExecutionStatus.CANCELLED
        exec_obj.completed_at = datetime.utcnow()
        exec_obj.duration_ms = int((exec_obj.completed_at - exec_obj.started_at).total_seconds() * 1000)
        self._save_data()
        return True

    def list_workflows(self, status: Optional[WorkflowStatus] = None, category: Optional[str] = None) -> List[WorkflowDefinition]:
        results = list(self.workflows.values())
        if status:
            results = [w for w in results if w.status == status]
        if category:
            results = [w for w in results if w.category == category]
        return results

    def list_executions(self, workflow_id: Optional[str] = None, status: Optional[WorkflowExecutionStatus] = None) -> List[WorkflowExecution]:
        results = list(self.executions.values())
        if workflow_id:
            results = [e for e in results if e.workflow_id == workflow_id]
        if status:
            results = [e for e in results if e.status == status]
        return sorted(results, key=lambda x: x.started_at or datetime.min, reverse=True)

    def get_execution_statistics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        executions = self.list_executions(workflow_id=workflow_id)
        total = len(executions)
        succeeded = sum(1 for e in executions if e.status == WorkflowExecutionStatus.SUCCEEDED)
        failed = sum(1 for e in executions if e.status == WorkflowExecutionStatus.FAILED)
        running = sum(1 for e in executions if e.status == WorkflowExecutionStatus.RUNNING)
        cancelled = sum(1 for e in executions if e.status == WorkflowExecutionStatus.CANCELLED)
        avg_duration = 0.0
        durations = [e.duration_ms for e in executions if e.duration_ms]
        if durations:
            avg_duration = sum(durations) / len(durations)
        return {"total_executions": total, "succeeded": succeeded, "failed": failed, "running": running, "cancelled": cancelled, "success_rate": (succeeded / total * 100) if total > 0 else 0.0, "average_duration_ms": avg_duration}

    def export_workflow_yaml(self, workflow_id: str) -> Optional[str]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        export = {"name": wf.name, "description": wf.description, "version": wf.current_version, "steps": [], "triggers": [], "variables": wf.variables}
        for step in wf.steps:
            export["steps"].append({"id": step.id, "name": step.name, "type": step.step_type.value, "config": step.config, "depends_on": step.depends_on, "timeout_seconds": step.timeout_seconds})
        for trigger in wf.triggers:
            export["triggers"].append({"id": trigger.id, "type": trigger.trigger_type.value, "name": trigger.name, "config": trigger.config, "cron": trigger.cron_expression})
        return yaml.dump(export, default_flow_style=False)

    def import_workflow_yaml(self, yaml_content: str, created_by: Optional[str] = None) -> Optional[WorkflowDefinition]:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {e}")
            return None
        wf = self.create_workflow(name=data.get("name", "Imported Workflow"), description=data.get("description", ""), created_by=created_by)
        for step_data in data.get("steps", []):
            step = WorkflowStep(id=str(uuid.uuid4()), name=step_data.get("name", "Step"), step_type=WorkflowStepType(step_data.get("type", "task")), config=step_data.get("config", {}), depends_on=step_data.get("depends_on", []), timeout_seconds=step_data.get("timeout_seconds", 3600))
            wf.steps.append(step)
        for trigger_data in data.get("triggers", []):
            trigger = WorkflowTrigger(id=str(uuid.uuid4()), trigger_type=WorkflowTriggerType(trigger_data.get("type", "manual")), name=trigger_data.get("name", "Trigger"), config=trigger_data.get("config", {}), cron_expression=trigger_data.get("cron"))
            wf.triggers.append(trigger)
        wf.variables = data.get("variables", {})
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return wf

    def activate_workflow(self, workflow_id: str) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        if wf.status == WorkflowStatus.DRAFT:
            wf.status = WorkflowStatus.ACTIVE
            wf.updated_at = datetime.utcnow()
            self._save_data()
            return True
        return False

    def pause_workflow(self, workflow_id: str) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf or wf.status != WorkflowStatus.ACTIVE:
            return False
        wf.status = WorkflowStatus.PAUSED
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def search_workflows(self, query: str) -> List[WorkflowDefinition]:
        query = query.lower()
        results = []
        for wf in self.workflows.values():
            if query in wf.name.lower() or query in wf.description.lower() or any(query in tag.lower() for tag in wf.tags):
                results.append(wf)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        total_workflows = len(self.workflows)
        active = sum(1 for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE)
        draft = sum(1 for w in self.workflows.values() if w.status == WorkflowStatus.DRAFT)
        paused = sum(1 for w in self.workflows.values() if w.status == WorkflowStatus.PAUSED)
        total_executions = len(self.executions)
        total_templates = len(self.templates)
        total_steps = sum(len(w.steps) for w in self.workflows.values())
        total_triggers = sum(len(w.triggers) for w in self.workflows.values())
        return {"total_workflows": total_workflows, "active": active, "draft": draft, "paused": paused, "total_executions": total_executions, "total_templates": total_templates, "total_steps": total_steps, "total_triggers": total_triggers}

    def bulk_delete_workflows(self, workflow_ids: List[str]) -> int:
        count = 0
        for wf_id in workflow_ids:
            if self.delete_workflow(wf_id):
                count += 1
        return count

    def duplicate_workflow(self, workflow_id: str, new_name: str) -> Optional[WorkflowDefinition]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        clone = WorkflowDefinition(
            id=str(uuid.uuid4()),
            name=new_name,
            description=wf.description,
            status=WorkflowStatus.DRAFT,
            tags=wf.tags[:],
            category=wf.category,
            steps=[WorkflowStep(id=str(uuid.uuid4()), name=s.name, step_type=s.step_type, config=s.config.copy(), depends_on=s.depends_on[:], timeout_seconds=s.timeout_seconds, retry_count=s.retry_count, retry_delay_seconds=s.retry_delay_seconds) for s in wf.steps],
            triggers=[WorkflowTrigger(id=str(uuid.uuid4()), trigger_type=t.trigger_type, name=t.name, config=t.config.copy(), cron_expression=t.cron_expression) for t in wf.triggers],
            variables=wf.variables.copy(),
        )
        self.workflows[clone.id] = clone
        self._save_data()
        return clone

    def set_variables(self, workflow_id: str, variables: Dict[str, Dict[str, Any]]) -> bool:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return False
        wf.variables = variables
        wf.updated_at = datetime.utcnow()
        self._save_data()
        return True
