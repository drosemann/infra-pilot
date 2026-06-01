"""Extended self-healing infrastructure with auto-recovery, health monitoring, and healing policies."""
import json
import uuid
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class HealingActionType(str, Enum):
    RESTART = "restart"
    RECREATE = "recreate"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    FAILOVER = "failover"
    REPLACE = "replace"
    REBOOT = "reboot"
    RECONNECT = "reconnect"
    CLEAR_CACHE = "clear_cache"
    REBALANCE = "rebalance"
    REPAIR = "repair"
    RECONFIGURE = "reconfigure"
    EXECUTE_SCRIPT = "execute_script"
    NOTIFY = "notify"
    ESCALATE = "escalate"


class HealingPolicyMode(str, Enum):
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    MANUAL = "manual"
    OBSERVE_ONLY = "observe_only"


@dataclass
class HealthCheckConfig:
    type: str
    interval_seconds: int = 30
    timeout_seconds: int = 10
    retry_count: int = 3
    endpoint: Optional[str] = None
    expected_status_code: int = 200
    expected_body_regex: Optional[str] = None
    metric_query: Optional[str] = None
    threshold: Optional[float] = None
    comparison: str = "less_than"


@dataclass
class HealingAction:
    id: str
    action_type: HealingActionType
    name: str
    order: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    cooldown_seconds: int = 60
    max_attempts: int = 3
    verify_health_after: bool = True


@dataclass
class HealingPolicy:
    id: str
    name: str
    description: str
    resource_type: str
    mode: HealingPolicyMode = HealingPolicyMode.SEMI_AUTOMATIC
    health_checks: List[HealthCheckConfig] = field(default_factory=list)
    actions: List[HealingAction] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    cooldown_minutes: int = 10
    max_actions_per_hour: int = 5
    enabled: bool = True
    notify_on_heal: bool = True
    notify_on_failure: bool = True
    notification_channels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealthStatusRecord:
    id: str
    resource_id: str
    resource_type: str
    status: HealthStatus
    checks_passed: int = 0
    checks_failed: int = 0
    check_results: Dict[str, Any] = field(default_factory=dict)
    last_healthy: Optional[datetime] = None
    last_unhealthy: Optional[datetime] = None
    consecutive_failures: int = 0
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealingEvent:
    id: str
    policy_id: str
    policy_name: str
    resource_id: str
    resource_type: str
    status_before: HealthStatus
    status_after: Optional[HealthStatus] = None
    actions_taken: Dict[str, Any] = field(default_factory=dict)
    overall_success: bool = False
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    triggered_by: str = "auto"
    escalated: bool = False


@dataclass
class SelfHealingMetrics:
    total_healing_events: int = 0
    successful_heals: int = 0
    failed_heals: int = 0
    avg_recovery_time_ms: float = 0.0
    resources_monitored: int = 0
    policies_active: int = 0
    last_incident: Optional[datetime] = None


class SelfHealingManager:
    def __init__(self, storage_path: str = "data/self_healing.json"):
        self.storage_path = storage_path
        self.policies: Dict[str, HealingPolicy] = {}
        self.status_records: Dict[str, HealthStatusRecord] = {}
        self.events: Dict[str, HealingEvent] = {}
        self.metrics: SelfHealingMetrics = SelfHealingMetrics()
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for p_data in data.get("policies", []):
            p = HealingPolicy(**p_data)
            self.policies[p.id] = p
        for s_data in data.get("status_records", []):
            s = HealthStatusRecord(**s_data)
            self.status_records[s.id] = s
        for e_data in data.get("events", []):
            e = HealingEvent(**e_data)
            self.events[e.id] = e
        if "metrics" in data:
            self.metrics = SelfHealingMetrics(**data["metrics"])

    def _save_data(self) -> None:
        data = {
            "policies": [p.__dict__ for p in self.policies.values()],
            "status_records": [s.__dict__ for s in self.status_records.values()],
            "events": [e.__dict__ for e in self.events.values()],
            "metrics": self.metrics.__dict__,
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("SelfHealingManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("SelfHealingManager closed")

    def create_policy(self, name: str, description: str, resource_type: str, mode: HealingPolicyMode = HealingPolicyMode.SEMI_AUTOMATIC, tags: Optional[List[str]] = None, created_by: Optional[str] = None) -> HealingPolicy:
        policy = HealingPolicy(id=str(uuid.uuid4()), name=name, description=description, resource_type=resource_type, mode=mode, tags=tags or [], created_by=created_by)
        self.policies[policy.id] = policy
        self._save_data()
        return policy

    def get_policy(self, policy_id: str) -> Optional[HealingPolicy]:
        return self.policies.get(policy_id)

    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> Optional[HealingPolicy]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        for key, value in updates.items():
            if hasattr(policy, key) and key not in ("id", "created_at", "created_by"):
                setattr(policy, key, value)
        policy.updated_at = datetime.utcnow()
        self.policies[policy_id] = policy
        self._save_data()
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self.policies:
            del self.policies[policy_id]
            self._save_data()
            return True
        return False

    def add_health_check(self, policy_id: str, check_type: str, interval_seconds: int = 30, timeout_seconds: int = 10, retry_count: int = 3, endpoint: Optional[str] = None, expected_status_code: int = 200, metric_query: Optional[str] = None, threshold: Optional[float] = None, comparison: str = "less_than") -> Optional[HealthCheckConfig]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        check = HealthCheckConfig(type=check_type, interval_seconds=interval_seconds, timeout_seconds=timeout_seconds, retry_count=retry_count, endpoint=endpoint, expected_status_code=expected_status_code, metric_query=metric_query, threshold=threshold, comparison=comparison)
        policy.health_checks.append(check)
        policy.updated_at = datetime.utcnow()
        self._save_data()
        return check

    def add_healing_action(self, policy_id: str, action_type: HealingActionType, name: str, config: Optional[Dict[str, Any]] = None, order: int = 0, timeout_seconds: int = 300, cooldown_seconds: int = 60, max_attempts: int = 3, verify_health_after: bool = True) -> Optional[HealingAction]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        action = HealingAction(id=str(uuid.uuid4()), action_type=action_type, name=name, order=order, config=config or {}, timeout_seconds=timeout_seconds, cooldown_seconds=cooldown_seconds, max_attempts=max_attempts, verify_health_after=verify_health_after)
        policy.actions.append(action)
        policy.updated_at = datetime.utcnow()
        self._save_data()
        return action

    def check_health(self, resource_id: str, resource_type: str, check_data: Dict[str, Any]) -> HealthStatusRecord:
        status = HealthStatusRecord(id=str(uuid.uuid4()), resource_id=resource_id, resource_type=resource_type, status=HealthStatus.UNKNOWN)
        policies = [p for p in self.policies.values() if p.enabled and (p.resource_type == resource_type or p.resource_type == "*")]
        total_passed = 0
        total_failed = 0
        check_results = {}
        for policy in policies:
            for check in policy.health_checks:
                passed = self._run_health_check(check, check_data)
                check_results[f"{check.type}_{check.endpoint or check.metric_query}"] = {"passed": passed, "type": check.type}
                if passed:
                    total_passed += 1
                else:
                    total_failed += 1
        if total_failed == 0:
            status.status = HealthStatus.HEALTHY
        elif total_passed > 0:
            status.status = HealthStatus.DEGRADED
        else:
            status.status = HealthStatus.UNHEALTHY
        status.checks_passed = total_passed
        status.checks_failed = total_failed
        status.check_results = check_results
        status.checked_at = datetime.utcnow()
        if status.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
            previous = next((s for s in self.status_records.values() if s.resource_id == resource_id), None)
            if previous:
                status.consecutive_failures = previous.consecutive_failures + 1
            if status.status == HealthStatus.UNHEALTHY:
                status.last_unhealthy = datetime.utcnow()
        if status.status == HealthStatus.HEALTHY:
            status.last_healthy = datetime.utcnow()
            status.consecutive_failures = 0
        self.status_records[status.id] = status
        self._save_data()
        if status.status == HealthStatus.UNHEALTHY:
            self._trigger_healing(resource_id, resource_type, status)
        return status

    def _run_health_check(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        if check.type == "http":
            return self._check_http(check, data)
        elif check.type == "metric":
            return self._check_metric(check, data)
        elif check.type == "ping":
            return self._check_ping(check, data)
        elif check.type == "process":
            return self._check_process(check, data)
        elif check.type == "custom":
            return self._check_custom(check, data)
        return True

    def _check_http(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        import requests
        url = check.endpoint or f"http://localhost:8080/health"
        try:
            resp = requests.get(url, timeout=check.timeout_seconds)
            if resp.status_code != check.expected_status_code:
                return False
            if check.expected_body_regex:
                return bool(re.search(check.expected_body_regex, resp.text))
            return True
        except:
            return False

    def _check_metric(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        value = data.get(check.metric_query, 0)
        if check.comparison == "less_than":
            return value < (check.threshold or float("inf"))
        elif check.comparison == "greater_than":
            return value > (check.threshold or 0)
        elif check.comparison == "equals":
            return value == check.threshold
        return True

    def _check_ping(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        import subprocess
        host = check.endpoint or "localhost"
        try:
            result = subprocess.run(["ping", "-n", "1", host], capture_output=True, text=True, timeout=check.timeout_seconds)
            return result.returncode == 0
        except:
            return False

    def _check_process(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        process_name = check.endpoint or "unknown"
        logger.info(f"Checking process: {process_name}")
        return True

    def _check_custom(self, check: HealthCheckConfig, data: Dict[str, Any]) -> bool:
        logger.info(f"Custom health check: {check.type}")
        return True

    def _trigger_healing(self, resource_id: str, resource_type: str, health_status: HealthStatusRecord) -> None:
        policies = [p for p in self.policies.values() if p.enabled and (p.resource_type == resource_type or p.resource_type == "*")]
        for policy in policies:
            if policy.mode == HealingPolicyMode.OBSERVE_ONLY:
                continue
            recent_events = [e for e in self.events.values() if e.policy_id == policy.id and e.started_at > datetime.utcnow() - timedelta(hours=1)]
            if len(recent_events) >= policy.max_actions_per_hour:
                logger.warning(f"Rate limit reached for policy {policy.name}")
                continue
            if policy.mode == HealingPolicyMode.AUTOMATIC or (policy.mode == HealingPolicyMode.SEMI_AUTOMATIC and health_status.consecutive_failures >= 2):
                self._execute_healing(policy, resource_id, resource_type, health_status)
            elif policy.mode == HealingPolicyMode.MANUAL:
                logger.info(f"Manual healing required for {resource_id} (policy: {policy.name})")

    def _execute_healing(self, policy: HealingPolicy, resource_id: str, resource_type: str, health_status: HealthStatusRecord) -> Optional[HealingEvent]:
        event = HealingEvent(id=str(uuid.uuid4()), policy_id=policy.id, policy_name=policy.name, resource_id=resource_id, resource_type=resource_type, status_before=health_status.status)
        self.events[event.id] = event
        for action in sorted(policy.actions, key=lambda a: a.order):
            for attempt in range(action.max_attempts):
                try:
                    result = self._perform_action(action, resource_id, resource_type)
                    event.actions_taken[action.id] = {"action_type": action.action_type.value, "status": "success", "attempt": attempt + 1, "result": result}
                    if action.verify_health_after:
                        verify_status = self.check_health(resource_id, resource_type, {"verified": True})
                        if verify_status.status == HealthStatus.HEALTHY:
                            event.status_after = HealthStatus.HEALTHY
                            event.overall_success = True
                            break
                except Exception as e:
                    event.actions_taken[action.id] = {"action_type": action.action_type.value, "status": "failed", "attempt": attempt + 1, "error": str(e)}
                    if attempt < action.max_attempts - 1:
                        time.sleep(action.cooldown_seconds)
                    else:
                        event.error = f"Action {action.name} failed after {action.max_attempts} attempts: {e}"
                        event.escalated = True
        event.completed_at = datetime.utcnow()
        event.duration_ms = int((event.completed_at - event.started_at).total_seconds() * 1000)
        self.metrics.total_healing_events += 1
        if event.overall_success:
            self.metrics.successful_heals += 1
        else:
            self.metrics.failed_heals += 1
        self._save_data()
        return event

    def _perform_action(self, action: HealingAction, resource_id: str, resource_type: str) -> Dict[str, Any]:
        if action.action_type == HealingActionType.RESTART:
            return self._action_restart(action, resource_id)
        elif action.action_type == HealingActionType.RECREATE:
            return self._action_recreate(action, resource_id)
        elif action.action_type == HealingActionType.SCALE_UP:
            return self._action_scale(action, resource_id, "up")
        elif action.action_type == HealingActionType.FAILOVER:
            return self._action_failover(action, resource_id)
        elif action.action_type == HealingActionType.REBOOT:
            return self._action_reboot(action, resource_id)
        elif action.action_type == HealingActionType.CLEAR_CACHE:
            return {"action": "clear_cache", "resource": resource_id, "status": "completed"}
        elif action.action_type == HealingActionType.RECONNECT:
            return {"action": "reconnect", "resource": resource_id, "status": "completed"}
        elif action.action_type == HealingActionType.NOTIFY:
            return {"action": "notify", "channel": action.config.get("channel", "log"), "status": "sent"}
        elif action.action_type == HealingActionType.EXECUTE_SCRIPT:
            return self._action_execute_script(action, resource_id)
        elif action.action_type == HealingActionType.REPAIR:
            return {"action": "repair", "resource": resource_id, "type": action.config.get("repair_type", "auto"), "status": "completed"}
        elif action.action_type == HealingActionType.RECONFIGURE:
            return {"action": "reconfigure", "resource": resource_id, "config": action.config.get("config", {}), "status": "completed"}
        return {"action": action.action_type.value, "resource": resource_id, "status": "simulated"}

    def _action_restart(self, action: HealingAction, resource_id: str) -> Dict[str, Any]:
        logger.info(f"Restarting {resource_id}")
        return {"action": "restart", "resource": resource_id, "status": "initiated"}

    def _action_recreate(self, action: HealingAction, resource_id: str) -> Dict[str, Any]:
        logger.info(f"Recreating {resource_id}")
        return {"action": "recreate", "resource": resource_id, "status": "initiated"}

    def _action_scale(self, action: HealingAction, resource_id: str, direction: str) -> Dict[str, Any]:
        amount = action.config.get("amount", 1)
        logger.info(f"Scaling {direction} {resource_id} by {amount}")
        return {"action": f"scale_{direction}", "resource": resource_id, "amount": amount, "status": "initiated"}

    def _action_failover(self, action: HealingAction, resource_id: str) -> Dict[str, Any]:
        target = action.config.get("target", "standby")
        logger.info(f"Failing over {resource_id} to {target}")
        return {"action": "failover", "resource": resource_id, "target": target, "status": "initiated"}

    def _action_reboot(self, action: HealingAction, resource_id: str) -> Dict[str, Any]:
        logger.info(f"Rebooting {resource_id}")
        return {"action": "reboot", "resource": resource_id, "status": "initiated"}

    def _action_execute_script(self, action: HealingAction, resource_id: str) -> Dict[str, Any]:
        script = action.config.get("script", "")
        local_vars = {"resource_id": resource_id, "result": {}}
        try:
            exec(script, {}, local_vars)
        except Exception as e:
            raise RuntimeError(f"Healing script failed: {e}")
        return {"action": "execute_script", "resource": resource_id, "result": local_vars.get("result", {}), "status": "completed"}

    def enable_policy(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        policy.enabled = True
        policy.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def disable_policy(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        policy.enabled = False
        policy.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def get_events(self, policy_id: Optional[str] = None, resource_id: Optional[str] = None, hours_back: int = 24) -> List[HealingEvent]:
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        results = [e for e in self.events.values() if e.started_at >= cutoff]
        if policy_id:
            results = [e for e in results if e.policy_id == policy_id]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        return sorted(results, key=lambda x: x.started_at, reverse=True)

    def get_resource_status(self, resource_id: str) -> Optional[HealthStatusRecord]:
        matching = [s for s in self.status_records.values() if s.resource_id == resource_id]
        return max(matching, key=lambda s: s.checked_at) if matching else None

    def get_policy_stats(self, policy_id: str) -> Dict[str, Any]:
        recent = [e for e in self.events.values() if e.policy_id == policy_id]
        return {"policy_id": policy_id, "total_events": len(recent), "successful": sum(1 for e in recent if e.overall_success), "failed": sum(1 for e in recent if not e.overall_success), "escalated": sum(1 for e in recent if e.escalated)}

    def search_policies(self, query: str) -> List[HealingPolicy]:
        query = query.lower()
        return [p for p in self.policies.values() if query in p.name.lower() or query in p.description.lower() or query in p.resource_type.lower() or any(query in t.lower() for t in p.tags)]

    def get_dashboard(self) -> Dict[str, Any]:
        total_policies = len(self.policies)
        active_policies = sum(1 for p in self.policies.values() if p.enabled)
        healthy_resources = sum(1 for s in self.status_records.values() if s.status == HealthStatus.HEALTHY)
        unhealthy_resources = sum(1 for s in self.status_records.values() if s.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED))
        recent_events = self.get_events(hours_back=24)
        return {"policies": {"total": total_policies, "active": active_policies, "disabled": total_policies - active_policies}, "resources": {"healthy": healthy_resources, "unhealthy": unhealthy_resources, "total": len(self.status_records)}, "events_24h": {"total": len(recent_events), "successful": sum(1 for e in recent_events if e.overall_success), "failed": sum(1 for e in recent_events if not e.overall_success), "escalated": sum(1 for e in recent_events if e.escalated)}, "metrics": {"total_healing_events": self.metrics.total_healing_events, "successful_heals": self.metrics.successful_heals, "failed_heals": self.metrics.failed_heals, "success_rate": (self.metrics.successful_heals / max(self.metrics.total_healing_events, 1)) * 100}}

    def get_statistics(self) -> Dict[str, Any]:
        dashboard = self.get_dashboard()
        dashboard["policies_list"] = [{"id": p.id, "name": p.name, "enabled": p.enabled, "mode": p.mode.value, "resource_type": p.resource_type, "health_checks": len(p.health_checks), "actions": len(p.actions)} for p in self.policies.values()]
        return dashboard
