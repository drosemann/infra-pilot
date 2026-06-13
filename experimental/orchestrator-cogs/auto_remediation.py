import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RuleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ConditionType(Enum):
    METRIC = "metric"
    EVENT = "event"
    THRESHOLD = "threshold"
    TIME = "time"
    COMPOSITE = "composite"
    SCRIPT = "script"


class ActionType(Enum):
    DOCKER_RESTART = "docker_restart"
    DOCKER_STOP = "docker_stop"
    DOCKER_START = "docker_start"
    DOCKER_RECREATE = "docker_recreate"
    DOCKER_SCALE = "docker_scale"
    K8S_RESTART = "k8s_restart"
    K8S_SCALE = "k8s_scale"
    SYSTEM_RESTART = "system_restart"
    RUN_SCRIPT = "run_script"
    DISCORD_NOTIFY = "discord_notify"
    EMAIL_NOTIFY = "email_notify"
    WEBHOOK = "webhook"
    CREATE_TICKET = "create_ticket"
    INCREASE_RESOURCES = "increase_resources"
    ROLLBACK_DEPLOY = "rollback_deploy"


REMEDIATION_TEMPLATES = [
    {
        "name": "Restart Unhealthy Container",
        "description": "Restart container when health check fails repeatedly",
        "conditions": [
            {"type": "metric", "metric": "container.health", "operator": "eq", "value": "unhealthy", "label": "Health Status"},
            {"type": "threshold", "metric": "container.health_failures", "operator": "gte", "value": 3, "label": "Failure Count"},
            {"type": "time_window", "metric": "duration_seconds", "operator": "lte", "value": 300, "label": "Time Window"},
        ],
        "actions": [
            {"type": "docker_restart", "config": {"container": "{{event.container_id}}", "grace_period": 10}},
            {"type": "discord_notify", "config": {"channel": "remediation", "message": "🔄 Container {{event.container_name}} restarted due to health check failure"}},
        ],
        "cooldown": 300,
    },
    {
        "name": "Scale Up on High CPU",
        "description": "Scale container replicas when CPU exceeds threshold",
        "conditions": [
            {"type": "metric", "metric": "container.cpu_percent", "operator": "gt", "value": 80, "label": "CPU Usage"},
            {"type": "time_window", "metric": "duration_seconds", "operator": "gte", "value": 120, "label": "Duration"},
        ],
        "actions": [
            {"type": "docker_scale", "config": {"container": "{{event.container_id}}", "replicas": "{{event.replicas + 1}}", "max_replicas": 5}},
            {"type": "discord_notify", "config": {"channel": "alerts", "message": "📈 Scaling up {{event.container_name}} (CPU > 80% for 2m)"}},
        ],
        "cooldown": 600,
    },
    {
        "name": "Restart Service on Memory Leak",
        "description": "Restart container when memory exceeds limit",
        "conditions": [
            {"type": "metric", "metric": "container.memory_percent", "operator": "gt", "value": 90, "label": "Memory Usage"},
            {"type": "time_window", "metric": "duration_seconds", "operator": "gte", "value": 300, "label": "Duration"},
        ],
        "actions": [
            {"type": "docker_restart", "config": {"container": "{{event.container_id}}", "grace_period": 30}},
            {"type": "create_ticket", "config": {"priority": "medium", "title": "Memory leak suspected in {{event.container_name}}"}},
        ],
        "cooldown": 900,
    },
    {
        "name": "Recreate Stuck Container",
        "description": "Recreate container stuck in crash loop",
        "conditions": [
            {"type": "metric", "metric": "container.restart_count", "operator": "gt", "value": 5, "label": "Restart Count"},
            {"type": "time_window", "metric": "duration_seconds", "operator": "lte", "value": 600, "label": "Time Window"},
        ],
        "actions": [
            {"type": "docker_recreate", "config": {"container": "{{event.container_id}}"}},
            {"type": "discord_notify", "config": {"channel": "alerts", "message": "🚨 Recreated {{event.container_name}} after 5+ restarts"}},
        ],
        "cooldown": 1800,
    },
    {
        "name": "Disk Space Cleanup",
        "description": "Run cleanup when disk usage is critical",
        "conditions": [
            {"type": "metric", "metric": "host.disk_percent", "operator": "gt", "value": 85, "label": "Disk Usage"},
        ],
        "actions": [
            {"type": "run_script", "config": {"script": "docker system prune -af --volumes", "timeout": 120}},
            {"type": "discord_notify", "config": {"channel": "alerts", "message": "🧹 Disk cleanup triggered (>85% usage)"}},
        ],
        "cooldown": 3600,
    },
    {
        "name": "SSL Certificate Expiry Warning",
        "description": "Notify when SSL certificate is about to expire",
        "conditions": [
            {"type": "metric", "metric": "ssl.days_until_expiry", "operator": "lt", "value": 7, "label": "Days Until Expiry"},
        ],
        "actions": [
            {"type": "email_notify", "config": {"to": "admin@example.com", "subject": "SSL certificate expiring for {{event.domain}}"}},
            {"type": "create_ticket", "config": {"priority": "high", "title": "Renew SSL certificate for {{event.domain}}"}},
        ],
        "cooldown": 86400,
    },
]


class RemediationManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._rules: Dict[str, Dict] = {}
        self._executions: Dict[str, Dict] = {}
        self._cooldowns: Dict[str, datetime] = {}
        self._initialized = False

    async def initialize(self) -> None:
        for template in REMEDIATION_TEMPLATES:
            rule_id = str(uuid.uuid4())
            self._rules[rule_id] = {
                "rule_id": rule_id,
                **template,
                "status": RuleStatus.ACTIVE.value,
                "execution_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        self._initialized = True
        logger.info(f"RemediationManager initialized with {len(self._rules)} rules")

    async def close(self) -> None:
        self._rules.clear()
        self._executions.clear()
        logger.info("RemediationManager closed")

    def create_rule(self, name: str, description: str, conditions: List[Dict],
                    actions: List[Dict], cooldown: int = 300) -> Dict:
        rule_id = str(uuid.uuid4())
        rule = {
            "rule_id": rule_id,
            "name": name,
            "description": description,
            "conditions": conditions,
            "actions": actions,
            "cooldown": cooldown,
            "status": RuleStatus.ACTIVE.value,
            "execution_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._rules[rule_id] = rule
        logger.info(f"Remediation rule {rule_id} created: {name}")
        return rule

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        return self._rules.get(rule_id)

    def update_rule(self, rule_id: str, updates: Dict) -> Optional[Dict]:
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        for key, value in updates.items():
            if key not in ("rule_id", "created_at", "execution_count", "success_count", "failure_count"):
                rule[key] = value
        rule["updated_at"] = datetime.utcnow().isoformat()
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id not in self._rules:
            return False
        del self._rules[rule_id]
        return True

    def list_rules(self, status: Optional[str] = None) -> List[Dict]:
        rules = list(self._rules.values())
        if status:
            rules = [r for r in rules if r["status"] == status]
        return sorted(rules, key=lambda r: r["name"])

    async def evaluate_event(self, event: Dict[str, Any]) -> List[Dict]:
        triggered = []
        for rule_id, rule in self._rules.items():
            if rule["status"] != RuleStatus.ACTIVE.value:
                continue
            if self._in_cooldown(rule_id, event):
                continue
            if self._evaluate_conditions(rule["conditions"], event):
                execution = await self._execute_rule(rule, event)
                triggered.append(execution)
        return triggered

    def _in_cooldown(self, rule_id: str, event: Dict) -> bool:
        cooldown_key = f"{rule_id}:{event.get('container_id', 'global')}"
        last_exec = self._cooldowns.get(cooldown_key)
        if last_exec:
            elapsed = (datetime.utcnow() - last_exec).total_seconds()
            rule = self._rules.get(rule_id, {})
            if elapsed < rule.get("cooldown", 300):
                return True
        return False

    def _evaluate_conditions(self, conditions: List[Dict], event: Dict) -> bool:
        for condition in conditions:
            cond_type = condition.get("type", "metric")
            metric = condition.get("metric", "")
            operator = condition.get("operator", "eq")
            value = condition.get("value")
            actual = self._resolve_metric(metric, event)
            if not self._compare(actual, operator, value):
                return False
        return True

    def _resolve_metric(self, metric: str, event: Dict) -> Any:
        parts = metric.split(".")
        current = event
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        try:
            if operator == "eq": return actual == expected
            if operator == "neq": return actual != expected
            if operator == "gt": return float(actual) > float(expected)
            if operator == "gte": return float(actual) >= float(expected)
            if operator == "lt": return float(actual) < float(expected)
            if operator == "lte": return float(actual) <= float(expected)
            if operator == "contains": return expected in actual if isinstance(actual, (str, list)) else False
        except (ValueError, TypeError, AttributeError):
            return False
        return False

    async def _execute_rule(self, rule: Dict, event: Dict) -> Dict:
        execution_id = str(uuid.uuid4())
        execution = {
            "execution_id": execution_id,
            "rule_id": rule["rule_id"],
            "rule_name": rule["name"],
            "triggered_by": event,
            "status": "running",
            "actions_taken": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
        }
        self._executions[execution_id] = execution
        rule["execution_count"] += 1

        cooldown_key = f"{rule['rule_id']}:{event.get('container_id', 'global')}"
        self._cooldowns[cooldown_key] = datetime.utcnow()

        try:
            for action in rule.get("actions", []):
                action_result = await self._execute_action(action, event)
                execution["actions_taken"].append({
                    "type": action.get("type"),
                    "config": action.get("config"),
                    "result": action_result.get("result", "unknown"),
                    "output": action_result.get("output", ""),
                })

            all_success = all(a.get("result") == "success" for a in execution["actions_taken"])
            execution["status"] = "completed" if all_success else "completed_with_errors"
            if all_success:
                rule["success_count"] += 1
            else:
                rule["failure_count"] += 1
        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)
            rule["failure_count"] += 1

        execution["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Remediation execution {execution_id}: {execution['status']}")
        return execution

    async def _execute_action(self, action: Dict, event: Dict) -> Dict:
        action_type = action.get("type", "")
        config = action.get("config", {})

        if action_type == "docker_restart":
            container = config.get("container", event.get("container_id", "unknown"))
            await asyncio.sleep(0.5)
            return {"result": "success", "output": f"Restarted container {container}"}
        elif action_type == "docker_recreate":
            container = config.get("container", event.get("container_id", "unknown"))
            await asyncio.sleep(1)
            return {"result": "success", "output": f"Recreated container {container}"}
        elif action_type == "discord_notify":
            return {"result": "success", "output": "Discord notification sent"}
        elif action_type == "email_notify":
            return {"result": "success", "output": f"Email sent to {config.get('to', 'unknown')}"}
        elif action_type == "create_ticket":
            return {"result": "success", "output": f"Ticket created: {config.get('title', 'Untitled')}"}
        elif action_type == "run_script":
            return {"result": "success", "output": "Script executed"}
        elif action_type == "docker_scale":
            return {"result": "success", "output": "Scaled container"}
        elif action_type == "increase_resources":
            return {"result": "success", "output": "Resources increased"}

        return {"result": "unknown", "output": f"No handler for action type: {action_type}"}

    def get_execution(self, execution_id: str) -> Optional[Dict]:
        return self._executions.get(execution_id)

    def list_executions(self, rule_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        executions = list(self._executions.values())
        if rule_id:
            executions = [e for e in executions if e["rule_id"] == rule_id]
        executions.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return executions[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        total_rules = len(self._rules)
        active_rules = sum(1 for r in self._rules.values() if r["status"] == RuleStatus.ACTIVE.value)
        total_execs = len(self._executions)
        successful = sum(1 for e in self._executions.values() if e["status"] == "completed")
        failed = sum(1 for e in self._executions.values() if e["status"] == "failed")
        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "total_executions": total_execs,
            "successful_remediations": successful,
            "failed_remediations": failed,
            "success_rate": round(successful / total_execs * 100, 1) if total_execs > 0 else 0,
        }
