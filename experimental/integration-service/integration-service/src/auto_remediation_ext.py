"""Extended auto-remediation engine with rule-based triggers, actions, and runbooks."""
import json
import uuid
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RemediationTriggerType(str, Enum):
    METRIC = "metric"
    EVENT = "event"
    LOG_PATTERN = "log_pattern"
    HEALTH_CHECK = "health_check"
    ALERT = "alert"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    ANOMALY = "anomaly"
    COMPLIANCE = "compliance"
    DRIFT = "drift"
    QUOTA = "quota"


class RemediationActionType(str, Enum):
    RESTART = "restart"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    RECREATE = "recreate"
    EXECUTE_SCRIPT = "execute_script"
    ANSIBLE_PLAYBOOK = "ansible_playbook"
    TERRAFORM_APPLY = "terraform_apply"
    KUBERNETES_CMD = "kubernetes_cmd"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    NOTIFICATION = "notification"
    SNAPSHOT = "snapshot"
    DNS_UPDATE = "dns_update"
    LB_UPDATE = "lb_update"
    TAG_UPDATE = "tag_update"
    RESIZE = "resize"
    MIGRATE = "migrate"
    BACKUP = "backup"
    CLEANUP = "cleanup"


class RemediationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RemediationRuleMode(str, Enum):
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    MANUAL = "manual"


@dataclass
class RemediationCondition:
    field: str
    operator: str
    value: Any
    duration_minutes: Optional[int] = None


@dataclass
class RemediationAction:
    id: str
    action_type: RemediationActionType
    name: str
    order: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 30
    continue_on_failure: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationRule:
    id: str
    name: str
    description: str
    trigger_type: RemediationTriggerType
    mode: RemediationRuleMode = RemediationRuleMode.SEMI_AUTOMATIC
    conditions: List[RemediationCondition] = field(default_factory=list)
    actions: List[RemediationAction] = field(default_factory=list)
    resource_types: List[str] = field(default_factory=list)
    cooldown_minutes: int = 60
    enabled: bool = True
    max_executions_per_hour: int = 10
    notify_on_failure: bool = True
    notify_channels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RemediationExecution:
    id: str
    rule_id: str
    rule_name: str
    trigger_type: str
    status: RemediationStatus
    target_resource: str
    target_resource_type: str
    conditions_matched: Dict[str, Any] = field(default_factory=dict)
    actions_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    executed_by: Optional[str] = None
    cooldown_expires: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationRunbook:
    id: str
    name: str
    description: str
    category: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class AutoRemediationManager:
    def __init__(self, storage_path: str = "data/auto_remediation.json"):
        self.storage_path = storage_path
        self.rules: Dict[str, RemediationRule] = {}
        self.executions: Dict[str, RemediationExecution] = {}
        self.runbooks: Dict[str, RemediationRunbook] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for r_data in data.get("rules", []):
            r = RemediationRule(**r_data)
            self.rules[r.id] = r
        for e_data in data.get("executions", []):
            e = RemediationExecution(**e_data)
            self.executions[e.id] = e
        for rb_data in data.get("runbooks", []):
            rb = RemediationRunbook(**rb_data)
            self.runbooks[rb.id] = rb

    def _save_data(self) -> None:
        data = {
            "rules": [r.__dict__ for r in self.rules.values()],
            "executions": [e.__dict__ for e in self.executions.values()],
            "runbooks": [r.__dict__ for r in self.runbooks.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("AutoRemediationManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("AutoRemediationManager closed")

    def create_rule(self, name: str, description: str, trigger_type: RemediationTriggerType, mode: RemediationRuleMode = RemediationRuleMode.SEMI_AUTOMATIC, resource_types: Optional[List[str]] = None, tags: Optional[List[str]] = None, created_by: Optional[str] = None) -> RemediationRule:
        rule = RemediationRule(id=str(uuid.uuid4()), name=name, description=description, trigger_type=trigger_type, mode=mode, resource_types=resource_types or [], tags=tags or [], created_by=created_by)
        self.rules[rule.id] = rule
        self._save_data()
        return rule

    def get_rule(self, rule_id: str) -> Optional[RemediationRule]:
        return self.rules.get(rule_id)

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[RemediationRule]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        for key, value in updates.items():
            if hasattr(rule, key) and key not in ("id", "created_at", "created_by"):
                setattr(rule, key, value)
        rule.updated_at = datetime.utcnow()
        self.rules[rule_id] = rule
        self._save_data()
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_data()
            return True
        return False

    def add_condition(self, rule_id: str, field: str, operator: str, value: Any, duration_minutes: Optional[int] = None) -> Optional[RemediationCondition]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        condition = RemediationCondition(field=field, operator=operator, value=value, duration_minutes=duration_minutes)
        rule.conditions.append(condition)
        rule.updated_at = datetime.utcnow()
        self._save_data()
        return condition

    def add_action(self, rule_id: str, action_type: RemediationActionType, name: str, config: Optional[Dict[str, Any]] = None, order: int = 0, timeout_seconds: int = 300, retry_count: int = 0, continue_on_failure: bool = False) -> Optional[RemediationAction]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        action = RemediationAction(id=str(uuid.uuid4()), action_type=action_type, name=name, order=order, config=config or {}, timeout_seconds=timeout_seconds, retry_count=retry_count, continue_on_failure=continue_on_failure)
        rule.actions.append(action)
        rule.updated_at = datetime.utcnow()
        self._save_data()
        return action

    def remove_action(self, rule_id: str, action_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        rule.actions = [a for a in rule.actions if a.id != action_id]
        rule.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def evaluate_and_execute(self, rule_id: str, target_resource: str, target_resource_type: str, context: Dict[str, Any], executed_by: Optional[str] = None) -> Optional[RemediationExecution]:
        rule = self.rules.get(rule_id)
        if not rule or not rule.enabled:
            return None
        recent = [e for e in self.executions.values() if e.rule_id == rule_id and e.started_at > datetime.utcnow() - timedelta(hours=1)]
        if len(recent) >= rule.max_executions_per_hour:
            logger.warning(f"Rate limit reached for rule {rule.name}")
            return None
        if rule.cooldown_minutes > 0:
            last_execution = max([e for e in self.executions.values() if e.rule_id == rule_id], key=lambda x: x.started_at, default=None)
            if last_execution and (datetime.utcnow() - last_execution.started_at).total_seconds() < rule.cooldown_minutes * 60:
                if last_execution.status == RemediationStatus.SUCCESS:
                    return None
        conditions_met = self._evaluate_conditions(rule.conditions, context)
        if not conditions_met:
            return None
        execution = RemediationExecution(id=str(uuid.uuid4()), rule_id=rule_id, rule_name=rule.name, trigger_type=rule.trigger_type.value, status=RemediationStatus.RUNNING, target_resource=target_resource, target_resource_type=target_resource_type, conditions_matched=conditions_met, executed_by=executed_by, cooldown_expires=datetime.utcnow() + timedelta(minutes=rule.cooldown_minutes))
        self.executions[execution.id] = execution
        self._save_data()
        for action in sorted(rule.actions, key=lambda a: a.order):
            try:
                result = self._execute_action(action, context)
                execution.actions_results[action.id] = {"status": "success", "result": result}
            except Exception as e:
                execution.actions_results[action.id] = {"status": "failed", "error": str(e)}
                if not action.continue_on_failure:
                    execution.status = RemediationStatus.FAILED
                    execution.error = str(e)
                    execution.completed_at = datetime.utcnow()
                    execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
                    self._save_data()
                    return execution
        execution.status = RemediationStatus.SUCCESS
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        self._save_data()
        return execution

    def _evaluate_conditions(self, conditions: List[RemediationCondition], context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for condition in conditions:
            actual_value = self._resolve_context_path(context, condition.field)
            if condition.operator == "equals":
                matched = str(actual_value) == str(condition.value)
            elif condition.operator == "not_equals":
                matched = str(actual_value) != str(condition.value)
            elif condition.operator == "greater_than":
                matched = float(actual_value or 0) > float(condition.value)
            elif condition.operator == "less_than":
                matched = float(actual_value or 0) < float(condition.value)
            elif condition.operator == "contains":
                matched = str(condition.value) in str(actual_value)
            elif condition.operator == "regex":
                matched = bool(re.search(str(condition.value), str(actual_value)))
            elif condition.operator == "exists":
                matched = actual_value is not None
            elif condition.operator == "not_exists":
                matched = actual_value is None
            else:
                matched = str(actual_value) == str(condition.value)
            results[condition.field] = {"field": condition.field, "operator": condition.operator, "expected": condition.value, "actual": actual_value, "matched": matched}
            if not matched:
                return {}
        return results

    def _resolve_context_path(self, context: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, None)
            else:
                return None
        return value

    def _execute_action(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        if action.action_type == RemediationActionType.RESTART:
            return self._action_restart(action, context)
        elif action.action_type == RemediationActionType.SCALE_UP:
            return self._action_scale(action, context, direction="up")
        elif action.action_type == RemediationActionType.SCALE_DOWN:
            return self._action_scale(action, context, direction="down")
        elif action.action_type == RemediationActionType.EXECUTE_SCRIPT:
            return self._action_execute_script(action, context)
        elif action.action_type == RemediationActionType.NOTIFICATION:
            return self._action_notification(action, context)
        elif action.action_type == RemediationActionType.API_CALL:
            return self._action_api_call(action, context)
        elif action.action_type == RemediationActionType.WEBHOOK:
            return self._action_webhook(action, context)
        elif action.action_type == RemediationActionType.SNAPSHOT:
            return {"snapshot_created": True, "resource": context.get("resource_id", "unknown")}
        elif action.action_type == RemediationActionType.CLEANUP:
            return self._action_cleanup(action, context)
        return {"executed": True, "action_type": action.action_type.value}

    def _action_restart(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        resource = context.get("resource_id", "unknown")
        logger.info(f"Restarting resource: {resource}")
        return {"action": "restart", "resource": resource, "status": "initiated"}

    def _action_scale(self, action: RemediationAction, context: Dict[str, Any], direction: str) -> Dict[str, Any]:
        amount = action.config.get("amount", 1)
        resource = context.get("resource_id", "unknown")
        logger.info(f"Scaling {direction} resource {resource} by {amount}")
        return {"action": f"scale_{direction}", "resource": resource, "amount": amount, "status": "initiated"}

    def _action_execute_script(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        script = action.config.get("script", "")
        local_vars = {"context": context, "result": {}}
        try:
            exec(script, {}, local_vars)
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {e}")
        return {"action": "execute_script", "result": local_vars.get("result", {}), "status": "completed"}

    def _action_notification(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        channel = action.config.get("channel", "log")
        message = action.config.get("message", "Remediation action triggered")
        if channel == "log":
            logger.info(f"Remediation notification: {message}")
        return {"channel": channel, "message": message, "sent": True}

    def _action_api_call(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        import requests
        url = action.config.get("url", "")
        method = action.config.get("method", "GET")
        headers = action.config.get("headers", {})
        body = action.config.get("body", context)
        timeout = action.config.get("timeout", 30)
        try:
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
            return {"status_code": resp.status_code, "body": resp.text[:500]}
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")

    def _action_webhook(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        return self._action_api_call(action, context)

    def _action_cleanup(self, action: RemediationAction, context: Dict[str, Any]) -> Dict[str, Any]:
        resource_type = action.config.get("resource_type", "unknown")
        age_hours = action.config.get("age_hours", 24)
        logger.info(f"Cleanup for {resource_type} older than {age_hours}h")
        return {"action": "cleanup", "resource_type": resource_type, "age_hours": age_hours, "status": "initiated"}

    def create_runbook(self, name: str, description: str, category: str, steps: Optional[List[Dict[str, Any]]] = None, tags: Optional[List[str]] = None) -> RemediationRunbook:
        rb = RemediationRunbook(id=str(uuid.uuid4()), name=name, description=description, category=category, steps=steps or [], tags=tags or [])
        self.runbooks[rb.id] = rb
        self._save_data()
        return rb

    def get_runbook(self, runbook_id: str) -> Optional[RemediationRunbook]:
        return self.runbooks.get(runbook_id)

    def delete_runbook(self, runbook_id: str) -> bool:
        if runbook_id in self.runbooks:
            del self.runbooks[runbook_id]
            self._save_data()
            return True
        return False

    def get_execution(self, execution_id: str) -> Optional[RemediationExecution]:
        return self.executions.get(execution_id)

    def cancel_execution(self, execution_id: str) -> bool:
        ex = self.executions.get(execution_id)
        if not ex or ex.status != RemediationStatus.RUNNING:
            return False
        ex.status = RemediationStatus.CANCELLED
        ex.completed_at = datetime.utcnow()
        ex.duration_ms = int((ex.completed_at - ex.started_at).total_seconds() * 1000)
        self._save_data()
        return True

    def list_rules(self, trigger_type: Optional[RemediationTriggerType] = None, enabled: Optional[bool] = None) -> List[RemediationRule]:
        results = list(self.rules.values())
        if trigger_type:
            results = [r for r in results if r.trigger_type == trigger_type]
        if enabled is not None:
            results = [r for r in results if r.enabled == enabled]
        return results

    def enable_rule(self, rule_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        rule.enabled = True
        rule.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def disable_rule(self, rule_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        rule.enabled = False
        rule.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def list_executions(self, rule_id: Optional[str] = None, status: Optional[RemediationStatus] = None, hours_back: int = 24) -> List[RemediationExecution]:
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        results = [e for e in self.executions.values() if e.started_at >= cutoff]
        if rule_id:
            results = [e for e in results if e.rule_id == rule_id]
        if status:
            results = [e for e in results if e.status == status]
        return sorted(results, key=lambda x: x.started_at, reverse=True)

    def search_rules(self, query: str) -> List[RemediationRule]:
        query = query.lower()
        return [r for r in self.rules.values() if query in r.name.lower() or query in r.description.lower() or any(query in t.lower() for t in r.tags)]

    def get_statistics(self) -> Dict[str, Any]:
        total_rules = len(self.rules)
        enabled_rules = sum(1 for r in self.rules.values() if r.enabled)
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.status == RemediationStatus.SUCCESS)
        failed = sum(1 for e in self.executions.values() if e.status == RemediationStatus.FAILED)
        total_runbooks = len(self.runbooks)
        avg_duration = 0.0
        durations = [e.duration_ms for e in self.executions.values() if e.duration_ms]
        if durations:
            avg_duration = sum(durations) / len(durations)
        return {"total_rules": total_rules, "enabled_rules": enabled_rules, "disabled_rules": total_rules - enabled_rules, "total_executions": total_executions, "successful": successful, "failed": failed, "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0.0, "average_duration_ms": avg_duration, "total_runbooks": total_runbooks}

    def bulk_enable_rules(self, rule_ids: List[str]) -> int:
        count = 0
        for rid in rule_ids:
            if self.enable_rule(rid):
                count += 1
        return count

    def bulk_disable_rules(self, rule_ids: List[str]) -> int:
        count = 0
        for rid in rule_ids:
            if self.disable_rule(rid):
                count += 1
        return count
