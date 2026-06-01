"""Extended configuration drift detector with real-time monitoring, baselines, and remediation."""
import json
import uuid
import logging
import hashlib
import difflib
import yaml
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DriftSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftStatus(str, Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    REMEDIATING = "remediating"
    REMEDIATED = "remediated"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"


class CheckInterval(str, Enum):
    REALTIME = "realtime"
    EVERY_5_MIN = "5m"
    EVERY_15_MIN = "15m"
    EVERY_30_MIN = "30m"
    HOURLY = "1h"
    EVERY_6_HOURS = "6h"
    DAILY = "24h"
    CUSTOM = "custom"


class ResourceCategory(str, Enum):
    NETWORK = "network"
    STORAGE = "storage"
    COMPUTE = "compute"
    SECURITY = "security"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    DNS = "dns"
    LOAD_BALANCER = "load_balancer"
    CERTIFICATE = "certificate"
    IAM = "iam"
    CONFIG = "config"


@dataclass
class DriftBaseline:
    id: str
    name: str
    description: str
    resource_category: ResourceCategory
    resource_type: str
    resource_id: str
    baseline_config: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    checksum: str = ""


@dataclass
class DriftCheck:
    id: str
    baseline_id: str
    name: str
    config_path: str
    expected_value: Any = None
    comparison_type: str = "exact"
    severity: DriftSeverity = DriftSeverity.MEDIUM
    enabled: bool = True
    remediation_script: Optional[str] = None
    auto_remediate: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DriftEvent:
    id: str
    baseline_id: str
    check_id: str
    resource_id: str
    resource_type: str
    severity: DriftSeverity
    status: DriftStatus = DriftStatus.DETECTED
    expected_value: Any = None
    actual_value: Any = None
    diff: str = ""
    config_path: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    remediated_at: Optional[datetime] = None
    remediation_result: Optional[str] = None
    suppressed_until: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class DriftPolicy:
    id: str
    name: str
    description: str
    resource_categories: List[ResourceCategory] = field(default_factory=list)
    check_interval: CheckInterval = CheckInterval.HOURLY
    auto_remediate: bool = False
    notify_on_drift: bool = True
    notification_channels: List[str] = field(default_factory=list)
    severity_threshold: DriftSeverity = DriftSeverity.LOW
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RemediationAction:
    id: str
    event_id: str
    action_type: str
    status: str = "pending"
    script: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    initiated_by: Optional[str] = None


class DriftDetectorManager:
    def __init__(self, storage_path: str = "data/drift_detector.json"):
        self.storage_path = storage_path
        self.baselines: Dict[str, DriftBaseline] = {}
        self.checks: Dict[str, DriftCheck] = {}
        self.events: Dict[str, DriftEvent] = {}
        self.policies: Dict[str, DriftPolicy] = {}
        self.remediations: Dict[str, RemediationAction] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for bl_data in data.get("baselines", []):
            bl = DriftBaseline(**bl_data)
            self.baselines[bl.id] = bl
        for ck_data in data.get("checks", []):
            ck = DriftCheck(**ck_data)
            self.checks[ck.id] = ck
        for ev_data in data.get("events", []):
            ev = DriftEvent(**ev_data)
            self.events[ev.id] = ev
        for pl_data in data.get("policies", []):
            pl = DriftPolicy(**pl_data)
            self.policies[pl.id] = pl
        for rm_data in data.get("remediations", []):
            rm = RemediationAction(**rm_data)
            self.remediations[rm.id] = rm

    def _save_data(self) -> None:
        data = {
            "baselines": [b.__dict__ for b in self.baselines.values()],
            "checks": [c.__dict__ for c in self.checks.values()],
            "events": [e.__dict__ for e in self.events.values()],
            "policies": [p.__dict__ for p in self.policies.values()],
            "remediations": [r.__dict__ for r in self.remediations.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("DriftDetectorManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("DriftDetectorManager closed")

    def create_baseline(self, name: str, description: str, resource_category: ResourceCategory, resource_type: str, resource_id: str, baseline_config: Dict[str, Any], created_by: Optional[str] = None) -> DriftBaseline:
        config_str = json.dumps(baseline_config, sort_keys=True)
        bl = DriftBaseline(id=str(uuid.uuid4()), name=name, description=description, resource_category=resource_category, resource_type=resource_type, resource_id=resource_id, baseline_config=baseline_config, created_by=created_by, checksum=hashlib.sha256(config_str.encode()).hexdigest())
        self.baselines[bl.id] = bl
        self._save_data()
        return bl

    def get_baseline(self, baseline_id: str) -> Optional[DriftBaseline]:
        return self.baselines.get(baseline_id)

    def update_baseline(self, baseline_id: str, config: Dict[str, Any]) -> Optional[DriftBaseline]:
        bl = self.baselines.get(baseline_id)
        if not bl:
            return None
        bl.baseline_config = config
        bl.version += 1
        config_str = json.dumps(config, sort_keys=True)
        bl.checksum = hashlib.sha256(config_str.encode()).hexdigest()
        bl.updated_at = datetime.utcnow()
        self._save_data()
        return bl

    def delete_baseline(self, baseline_id: str) -> bool:
        if baseline_id in self.baselines:
            del self.baselines[baseline_id]
            self.checks = {k: v for k, v in self.checks.items() if v.baseline_id != baseline_id}
            self._save_data()
            return True
        return False

    def add_check(self, baseline_id: str, name: str, config_path: str, expected_value: Any = None, comparison_type: str = "exact", severity: DriftSeverity = DriftSeverity.MEDIUM, auto_remediate: bool = False, remediation_script: Optional[str] = None) -> Optional[DriftCheck]:
        bl = self.baselines.get(baseline_id)
        if not bl:
            return None
        ck = DriftCheck(id=str(uuid.uuid4()), baseline_id=baseline_id, name=name, config_path=config_path, expected_value=expected_value, comparison_type=comparison_type, severity=severity, auto_remediate=auto_remediate, remediation_script=remediation_script)
        self.checks[ck.id] = ck
        self._save_data()
        return ck

    def remove_check(self, check_id: str) -> bool:
        if check_id in self.checks:
            del self.checks[check_id]
            self._save_data()
            return True
        return False

    def check_for_drift(self, baseline_id: str, current_config: Dict[str, Any]) -> List[DriftEvent]:
        bl = self.baselines.get(baseline_id)
        if not bl:
            return []
        events = []
        for ck in self.checks.values():
            if ck.baseline_id != baseline_id or not ck.enabled:
                continue
            actual_value = self._resolve_path(current_config, ck.config_path)
            expected_value = ck.expected_value if ck.expected_value is not None else self._resolve_path(bl.baseline_config, ck.config_path)
            drift = self._compare_values(expected_value, actual_value, ck.comparison_type)
            if drift:
                ev = DriftEvent(id=str(uuid.uuid4()), baseline_id=baseline_id, check_id=ck.id, resource_id=bl.resource_id, resource_type=bl.resource_type, severity=ck.severity, config_path=ck.config_path, expected_value=expected_value, actual_value=actual_value, diff=self._generate_diff(expected_value, actual_value))
                self.events[ev.id] = ev
                events.append(ev)
                if ck.auto_remediate and ck.remediation_script:
                    self._run_remediation(ev, ck.remediation_script)
        self._save_data()
        return events

    def _resolve_path(self, config: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        value = config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, None)
            elif isinstance(value, list):
                try:
                    idx = int(part)
                    value = value[idx] if 0 <= idx < len(value) else None
                except (ValueError, IndexError):
                    value = None
            else:
                value = None
                break
        return value

    def _compare_values(self, expected: Any, actual: Any, comparison_type: str) -> bool:
        if comparison_type == "exact":
            return expected != actual
        elif comparison_type == "contains":
            return expected not in (actual if isinstance(actual, (str, list)) else str(actual))
        elif comparison_type == "regex":
            import re
            if isinstance(expected, str) and isinstance(actual, str):
                return not bool(re.match(expected, actual))
            return True
        elif comparison_type == "range":
            if isinstance(expected, dict) and isinstance(actual, (int, float)):
                lo = expected.get("min", float("-inf"))
                hi = expected.get("max", float("inf"))
                return not (lo <= actual <= hi)
            return True
        elif comparison_type == "exists":
            return actual is None
        return True

    def _generate_diff(self, expected: Any, actual: Any) -> str:
        expected_str = json.dumps(expected, indent=2) if not isinstance(expected, str) else str(expected)
        actual_str = json.dumps(actual, indent=2) if not isinstance(actual, str) else str(actual)
        diff = difflib.unified_diff(expected_str.splitlines(), actual_str.splitlines(), fromfile="expected", tofile="actual", lineterm="")
        return "\n".join(diff)

    def _run_remediation(self, event: DriftEvent, script: str) -> Optional[RemediationAction]:
        remediation = RemediationAction(id=str(uuid.uuid4()), event_id=event.id, action_type="script", script=script)
        self.remediations[remediation.id] = remediation
        event.status = DriftStatus.REMEDIATING
        try:
            local_vars = {"config_path": event.config_path, "expected_value": event.expected_value, "actual_value": event.actual_value}
            exec(script, {}, local_vars)
            remediation.status = "completed"
            remediation.result = local_vars.get("result", "Remediation executed")
            remediation.completed_at = datetime.utcnow()
            event.status = DriftStatus.REMEDIATED
            event.remediated_at = datetime.utcnow()
            event.remediation_result = remediation.result
        except Exception as e:
            remediation.status = "failed"
            remediation.result = str(e)
            remediation.completed_at = datetime.utcnow()
        self._save_data()
        return remediation

    def acknowledge_event(self, event_id: str, acknowledged_by: str) -> bool:
        ev = self.events.get(event_id)
        if not ev:
            return False
        ev.status = DriftStatus.ACKNOWLEDGED
        ev.acknowledged_at = datetime.utcnow()
        ev.acknowledged_by = acknowledged_by
        self._save_data()
        return True

    def suppress_event(self, event_id: str, until_hours: int = 24) -> bool:
        ev = self.events.get(event_id)
        if not ev:
            return False
        ev.status = DriftStatus.SUPPRESSED
        ev.suppressed_until = datetime.utcnow() + timedelta(hours=until_hours)
        self._save_data()
        return True

    def mark_false_positive(self, event_id: str) -> bool:
        ev = self.events.get(event_id)
        if not ev:
            return False
        ev.status = DriftStatus.FALSE_POSITIVE
        self._save_data()
        return True

    def create_policy(self, name: str, description: str, resource_categories: Optional[List[ResourceCategory]] = None, check_interval: CheckInterval = CheckInterval.HOURLY, auto_remediate: bool = False, notify_on_drift: bool = True) -> DriftPolicy:
        pl = DriftPolicy(id=str(uuid.uuid4()), name=name, description=description, resource_categories=resource_categories or [], check_interval=check_interval, auto_remediate=auto_remediate, notify_on_drift=notify_on_drift)
        self.policies[pl.id] = pl
        self._save_data()
        return pl

    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> Optional[DriftPolicy]:
        pl = self.policies.get(policy_id)
        if not pl:
            return None
        for key, value in updates.items():
            if hasattr(pl, key) and key not in ("id", "created_at"):
                setattr(pl, key, value)
        pl.updated_at = datetime.utcnow()
        self.policies[policy_id] = pl
        self._save_data()
        return pl

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self.policies:
            del self.policies[policy_id]
            self._save_data()
            return True
        return False

    def list_events(self, severity: Optional[DriftSeverity] = None, status: Optional[DriftStatus] = None, resource_id: Optional[str] = None, hours_back: Optional[int] = None) -> List[DriftEvent]:
        results = list(self.events.values())
        if severity:
            results = [e for e in results if e.severity == severity]
        if status:
            results = [e for e in results if e.status == status]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        if hours_back:
            cutoff = datetime.utcnow() - timedelta(hours=hours_back)
            results = [e for e in results if e.detected_at >= cutoff]
        return sorted(results, key=lambda x: x.detected_at, reverse=True)

    def get_event(self, event_id: str) -> Optional[DriftEvent]:
        return self.events.get(event_id)

    def get_baseline_checks(self, baseline_id: str) -> List[DriftCheck]:
        return [c for c in self.checks.values() if c.baseline_id == baseline_id]

    def export_baseline_yaml(self, baseline_id: str) -> Optional[str]:
        bl = self.baselines.get(baseline_id)
        if not bl:
            return None
        export = {"name": bl.name, "description": bl.description, "resource_category": bl.resource_category.value, "resource_type": bl.resource_type, "resource_id": bl.resource_id, "version": bl.version, "config": bl.baseline_config, "checks": []}
        for ck in self.get_baseline_checks(baseline_id):
            export["checks"].append({"name": ck.name, "config_path": ck.config_path, "expected_value": ck.expected_value, "comparison_type": ck.comparison_type, "severity": ck.severity.value, "auto_remediate": ck.auto_remediate})
        return yaml.dump(export, default_flow_style=False)

    def import_baseline_yaml(self, yaml_content: str, resource_id: str, created_by: Optional[str] = None) -> Optional[DriftBaseline]:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return None
        bl = self.create_baseline(name=data.get("name", "Imported Baseline"), description=data.get("description", ""), resource_category=ResourceCategory(data.get("resource_category", "config")), resource_type=data.get("resource_type", "unknown"), resource_id=resource_id, baseline_config=data.get("config", {}), created_by=created_by)
        for ck_data in data.get("checks", []):
            self.add_check(baseline_id=bl.id, name=ck_data.get("name", "Check"), config_path=ck_data.get("config_path", ""), expected_value=ck_data.get("expected_value"), comparison_type=ck_data.get("comparison_type", "exact"), severity=DriftSeverity(ck_data.get("severity", "medium")), auto_remediate=ck_data.get("auto_remediate", False))
        return bl

    def compare_baselines(self, baseline_id_1: str, baseline_id_2: str) -> Dict[str, Any]:
        bl1 = self.baselines.get(baseline_id_1)
        bl2 = self.baselines.get(baseline_id_2)
        if not bl1 or not bl2:
            return {"error": "One or both baselines not found"}
        diff = self._generate_diff(bl1.baseline_config, bl2.baseline_config)
        return {"baseline_1": bl1.name, "baseline_2": bl2.name, "has_differences": len(diff) > 0, "diff": diff}

    def get_drift_summary(self) -> Dict[str, Any]:
        total_events = len(self.events)
        by_severity = {}
        by_status = {}
        for ev in self.events.values():
            by_severity[ev.severity.value] = by_severity.get(ev.severity.value, 0) + 1
            by_status[ev.status.value] = by_status.get(ev.status.value, 0) + 1
        return {"total_events": total_events, "by_severity": by_severity, "by_status": by_status, "total_baselines": len(self.baselines), "total_checks": len(self.checks), "total_policies": len(self.policies), "total_remediations": len(self.remediations), "unresolved": sum(1 for e in self.events.values() if e.status in (DriftStatus.DETECTED, DriftStatus.ACKNOWLEDGED))}

    def get_statistics(self) -> Dict[str, Any]:
        return self.get_drift_summary()

    def bulk_acknowledge(self, event_ids: List[str], acknowledged_by: str) -> int:
        count = 0
        for eid in event_ids:
            if self.acknowledge_event(eid, acknowledged_by):
                count += 1
        return count

    def run_scheduled_checks(self) -> List[DriftEvent]:
        all_events = []
        for bl in self.baselines.values():
            import random
            simulated_config = bl.baseline_config.copy()
            for ck in self.get_baseline_checks(bl.id):
                if random.random() < 0.05:
                    path_parts = ck.config_path.split(".")
                    target = simulated_config
                    for part in path_parts[:-1]:
                        if isinstance(target, dict) and part in target:
                            target = target[part]
                        else:
                            break
                    else:
                        if isinstance(target, dict) and path_parts[-1] in target:
                            target[path_parts[-1]] = f"DRIFTED_{target[path_parts[-1]]}"
            events = self.check_for_drift(bl.id, simulated_config)
            all_events.extend(events)
        return all_events
