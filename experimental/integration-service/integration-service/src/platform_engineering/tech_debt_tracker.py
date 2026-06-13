"""Technical Debt Tracker — Automated tech debt detection and remediation tracking."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DebtCategory(str, Enum):
    OUTDATED_DEPENDENCIES = "outdated_dependencies"
    DEPRECATED_APIS = "deprecated_apis"
    CODE_SMELLS = "code_smells"
    SECURITY_VULNERABILITIES = "security_vulnerabilities"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION_GAPS = "documentation_gaps"
    ARCHITECTURAL_DEBT = "architectural_debt"
    CONFIGURATION_DRIFT = "configuration_drift"
    PERFORMANCE_ISSUES = "performance_issues"
    MANUAL_PROCESSES = "manual_processes"


class DebtSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DebtStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    ACCEPTED = "accepted"


SEVERITY_WEIGHTS = {
    "critical": 10,
    "high": 5,
    "medium": 3,
    "low": 1,
    "info": 0.5,
}


class TechDebtItem:
    def __init__(self, item_id: str, service_id: str, category: DebtCategory, severity: DebtSeverity, title: str):
        self.item_id = item_id
        self.service_id = service_id
        self.category = category
        self.severity = severity
        self.title = title
        self.description: str = ""
        self.status: DebtStatus = DebtStatus.OPEN
        self.assigned_to: str = ""
        self.effort_hours: float = 0.0
        self.business_impact: str = ""
        self.remediation_steps: list[str] = []
        self.detected_by: str = "automated_scan"
        self.detected_at: datetime = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None
        self.due_date: Optional[datetime] = None
        self.tags: list[str] = []
        self.links: list[dict[str, str]] = []
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "service_id": self.service_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "effort_hours": self.effort_hours,
            "business_impact": self.business_impact,
            "remediation_steps": self.remediation_steps,
            "detected_by": self.detected_by,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "links": self.links,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TechDebtItem":
        item = cls(
            data["item_id"], data["service_id"],
            DebtCategory(data["category"]),
            DebtSeverity(data["severity"]),
            data["title"],
        )
        item.description = data.get("description", "")
        item.status = DebtStatus(data.get("status", "open"))
        item.assigned_to = data.get("assigned_to", "")
        item.effort_hours = data.get("effort_hours", 0.0)
        item.business_impact = data.get("business_impact", "")
        item.remediation_steps = data.get("remediation_steps", [])
        item.detected_by = data.get("detected_by", "automated_scan")
        if data.get("detected_at"):
            item.detected_at = datetime.fromisoformat(data["detected_at"])
        if data.get("resolved_at"):
            item.resolved_at = datetime.fromisoformat(data["resolved_at"])
        if data.get("due_date"):
            item.due_date = datetime.fromisoformat(data["due_date"])
        item.tags = data.get("tags", [])
        item.links = data.get("links", [])
        item.metadata = data.get("metadata", {})
        return item


TECH_DEBT_DETECTORS = {
    "outdated_dependencies": {"pattern": "dependency_version_check", "weight": 4},
    "deprecated_apis": {"pattern": "api_usage_scan", "weight": 3},
    "code_smells": {"pattern": "static_analysis", "weight": 2},
    "security_vulnerabilities": {"pattern": "cve_scan", "weight": 5},
    "test_coverage": {"pattern": "coverage_report", "weight": 3},
    "documentation_gaps": {"pattern": "doc_scan", "weight": 1},
    "architectural_debt": {"pattern": "architecture_review", "weight": 3},
    "configuration_drift": {"pattern": "config_diff", "weight": 2},
    "manual_processes": {"pattern": "automation_audit", "weight": 2},
}


class TechDebtTracker:
    def __init__(self):
        self.items: dict[str, TechDebtItem] = {}
        self.detector_configs: dict[str, Any] = dict(TECH_DEBT_DETECTORS)
        self.remediation_history: list[dict[str, Any]] = []

    def detect_debt(self, service_id: str, category: DebtCategory, severity: DebtSeverity,
                    title: str, description: str = "", detected_by: str = "automated_scan") -> TechDebtItem:
        item_id = str(uuid.uuid4())
        item = TechDebtItem(item_id, service_id, category, severity, title)
        item.description = description
        item.detected_by = detected_by
        self.items[item_id] = item
        logger.info("Detected tech debt [%s] on %s: %s", severity.value, service_id, title)
        return item

    def get_item(self, item_id: str) -> Optional[TechDebtItem]:
        return self.items.get(item_id)

    def update_item(self, item_id: str, updates: dict[str, Any]) -> Optional[TechDebtItem]:
        item = self.items.get(item_id)
        if not item:
            return None
        for key, value in updates.items():
            if key == "status" and isinstance(value, str):
                old_status = item.status.value
                item.status = DebtStatus(value)
                if value == "resolved" and not item.resolved_at:
                    item.resolved_at = datetime.utcnow()
                    self.remediation_history.append({
                        "item_id": item_id,
                        "service_id": item.service_id,
                        "title": item.title,
                        "category": item.category.value,
                        "old_status": old_status,
                        "new_status": value,
                        "resolved_at": item.resolved_at.isoformat(),
                    })
            elif key == "severity" and isinstance(value, str):
                setattr(item, key, DebtSeverity(value))
            elif key == "category" and isinstance(value, str):
                setattr(item, key, DebtCategory(value))
            elif hasattr(item, key):
                setattr(item, key, value)
        return item

    def list_items(self, service_id: str = "", category: str = "", severity: str = "",
                   status: str = "", assigned_to: str = "") -> list[TechDebtItem]:
        results = list(self.items.values())
        if service_id:
            results = [i for i in results if i.service_id == service_id]
        if category:
            results = [i for i in results if i.category.value == category]
        if severity:
            results = [i for i in results if i.severity.value == severity]
        if status:
            results = [i for i in results if i.status.value == status]
        if assigned_to:
            results = [i for i in results if i.assigned_to == assigned_to]
        return sorted(results, key=lambda i: (SEVERITY_WEIGHTS.get(i.severity.value, 0), i.detected_at), reverse=True)

    def get_service_debt_summary(self, service_id: str) -> dict[str, Any]:
        svc_items = [i for i in self.items.values() if i.service_id == service_id]
        total = len(svc_items)
        if total == 0:
            return {"service_id": service_id, "total_items": 0, "debt_score": 0}
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}
        total_weight = 0
        for item in svc_items:
            by_category[item.category.value] = by_category.get(item.category.value, 0) + 1
            by_severity[item.severity.value] = by_severity.get(item.severity.value, 0) + 1
            by_status[item.status.value] = by_status.get(item.status.value, 0) + 1
            if item.status == DebtStatus.OPEN or item.status == DebtStatus.IN_PROGRESS:
                total_weight += SEVERITY_WEIGHTS.get(item.severity.value, 0)
        return {
            "service_id": service_id,
            "total_items": total,
            "open_items": by_status.get("open", 0),
            "in_progress_items": by_status.get("in_progress", 0),
            "resolved_items": by_status.get("resolved", 0),
            "debt_score": round(total_weight, 1),
            "by_category": by_category,
            "by_severity": by_severity,
            "critical_items": by_severity.get("critical", 0),
            "high_items": by_severity.get("high", 0),
        }

    def get_organization_summary(self) -> dict[str, Any]:
        total = len(self.items)
        if total == 0:
            return {"total_items": 0, "debt_score": 0}
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        total_weight = 0
        for item in self.items.values():
            by_severity[item.severity.value] = by_severity.get(item.severity.value, 0) + 1
            by_status[item.status.value] = by_status.get(item.status.value, 0) + 1
            by_category[item.category.value] = by_category.get(item.category.value, 0) + 1
            if item.status == DebtStatus.OPEN or item.status == DebtStatus.IN_PROGRESS:
                total_weight += SEVERITY_WEIGHTS.get(item.severity.value, 0)
        return {
            "total_items": total,
            "open_items": by_status.get("open", 0),
            "in_progress_items": by_status.get("in_progress", 0),
            "resolved_items": by_status.get("resolved", 0),
            "debt_score": round(total_weight, 1),
            "by_severity": by_severity,
            "by_category": by_category,
            "critical_count": by_severity.get("critical", 0),
            "high_count": by_severity.get("high", 0),
            "unique_services": len(set(i.service_id for i in self.items.values())),
        }

    def run_automated_scan(self, service_id: str) -> list[TechDebtItem]:
        detected = []
        for category_name, config in self.detector_configs.items():
            item = self.detect_debt(
                service_id=service_id,
                category=DebtCategory(category_name),
                severity=DebtSeverity.HIGH if config["weight"] >= 4 else DebtSeverity.MEDIUM,
                title=f"{category_name.replace('_', ' ').title()} detected by {config['pattern']}",
                description=f"Automated {category_name.replace('_', ' ')} scan found potential issues. Run full analysis for details.",
                detected_by=f"auto_scanner_{config['pattern']}",
            )
            detected.append(item)
        logger.info("Auto-scan for service %s found %d items", service_id, len(detected))
        return detected

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": {iid: item.to_dict() for iid, item in self.items.items()},
            "detector_configs": self.detector_configs,
            "remediation_history": self.remediation_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TechDebtTracker":
        tracker = cls()
        for iid, idata in data.get("items", {}).items():
            tracker.items[iid] = TechDebtItem.from_dict(idata)
        tracker.detector_configs = data.get("detector_configs", dict(TECH_DEBT_DETECTORS))
        tracker.remediation_history = data.get("remediation_history", [])
        return tracker

    def bulk_update_items(self, item_ids: list[str], updates: dict[str, Any]) -> int:
        count = 0
        for iid in item_ids:
            if self.update_item(iid, updates):
                count += 1
        return count

    def get_sla_report(self) -> dict[str, Any]:
        overdue = []
        for item in self.items.values():
            if item.due_date and item.due_date < datetime.utcnow() and item.status in (DebtStatus.OPEN, DebtStatus.IN_PROGRESS):
                overdue.append({
                    "item_id": item.item_id,
                    "title": item.title,
                    "service_id": item.service_id,
                    "severity": item.severity.value,
                    "due_date": item.due_date.isoformat(),
                    "days_overdue": (datetime.utcnow() - item.due_date).days,
                })
        return {
            "total_overdue": len(overdue),
            "overdue_items": sorted(overdue, key=lambda x: x["days_overdue"], reverse=True)[:20],
            "avg_resolution_time_hours": round(
                sum((item.resolved_at - item.detected_at).total_seconds() / 3600
                    for item in self.items.values() if item.resolved_at) / max(
                    len([i for i in self.items.values() if i.resolved_at]), 1), 1
            ),
        }

    def assign_items_bulk(self, item_ids: list[str], assignee: str) -> int:
        count = 0
        for iid in item_ids:
            item = self.items.get(iid)
            if item:
                item.assigned_to = assignee
                count += 1
        return count

    def export_debt_report(self, service_id: str = "") -> dict[str, Any]:
        items_data = [i.to_dict() for i in self.list_items(service_id=service_id)] if service_id else [i.to_dict() for i in self.items.values()]
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_items": len(items_data),
            "items": items_data,
            "organization_summary": self.get_organization_summary(),
            "remediation_history": self.remediation_history[-50:],
        }

    def detect_from_dependency_scan(self, service_id: str, outdated_deps: list[dict[str, Any]]) -> list[TechDebtItem]:
        detected = []
        for dep in outdated_deps:
            item = self.detect_debt(
                service_id=service_id,
                category=DebtCategory.OUTDATED_DEPENDENCIES,
                severity=DebtSeverity.HIGH if dep.get("severity", "medium") == "critical" else DebtSeverity.MEDIUM,
                title=f"Outdated dependency: {dep.get('name', 'unknown')} ({dep.get('current', '?')} -> {dep.get('latest', '?')})",
                description=dep.get("description", ""),
                detected_by="dependency_scanner",
            )
            item.effort_hours = dep.get("effort_hours", 1.0)
            item.links = dep.get("links", [])
            detected.append(item)
        return detected

    def get_items_by_assignee(self, assignee: str) -> list[TechDebtItem]:
        return [i for i in self.items.values() if i.assigned_to == assignee]

    def get_service_debt_breakdown(self, service_id: str) -> dict[str, Any]:
        svc_items = [i for i in self.items.values() if i.service_id == service_id]
        return {
            "service_id": service_id,
            "total": len(svc_items),
            "by_severity": {s: len([i for i in svc_items if i.severity.value == s]) for s in DebtSeverity},
            "by_category": {c: len([i for i in svc_items if i.category.value == c]) for c in DebtCategory},
            "by_status": {s: len([i for i in svc_items if i.status.value == s]) for s in DebtStatus},
        }

    def get_items_by_severity(self, severity: DebtSeverity) -> list[TechDebtItem]:
        return [i for i in self.items.values() if i.severity == severity]

    def resolve_item(self, item_id: str, resolution_notes: str = "") -> bool:
        return self.update_item(item_id, {"status": "resolved", "metadata": {"resolution_notes": resolution_notes}}) is not None

    def reopen_item(self, item_id: str) -> bool:
        return self.update_item(item_id, {"status": "open"}) is not None

    def get_trend_analysis(self, days: int = 90) -> dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        created = 0
        resolved = 0
        by_month: dict[str, int] = {}
        for item in self.items.values():
            if item.created_at >= cutoff:
                created += 1
                month_key = item.created_at.strftime("%Y-%m")
                by_month[month_key] = by_month.get(month_key, 0) + 1
            if item.status == DebtStatus.RESOLVED and item.updated_at >= cutoff:
                resolved += 1
        return {"days": days, "created": created, "resolved": resolved,
                "net_change": created - resolved, "by_month": by_month}

    def schedule_scan(self, service_id: str, scan_type: str = "full", interval_hours: int = 24) -> dict[str, Any]:
        scan_id = str(uuid.uuid4())
        next_run = datetime.utcnow() + timedelta(hours=interval_hours)
        scan_def = {"scan_id": scan_id, "service_id": service_id, "scan_type": scan_type,
                     "interval_hours": interval_hours, "next_run": next_run.isoformat(),
                     "created_at": datetime.utcnow().isoformat(), "status": "active"}
        if not hasattr(self, "_scheduled_scans"):
            self._scheduled_scans: list[dict[str, Any]] = []
        self._scheduled_scans.append(scan_def)
        return scan_def

    def get_scheduled_scans(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_scheduled_scans", []))

    def cancel_scheduled_scan(self, scan_id: str) -> bool:
        scans = getattr(self, "_scheduled_scans", [])
        for s in scans:
            if s["scan_id"] == scan_id:
                s["status"] = "cancelled"
                return True
        return False

    def auto_remediate_item(self, item_id: str, strategy: str = "auto") -> dict[str, Any]:
        item = self.items.get(item_id)
        if not item:
            return {"error": "Item not found"}
        if strategy == "auto":
            return self.update_item(item_id, {"status": "resolved", "metadata": {"remediated_by": "auto_remediation"}}) or {}
        return {"error": f"Unknown strategy: {strategy}"}

    def bulk_remediate_items(self, item_ids: list[str], strategy: str = "auto") -> dict[str, Any]:
        succeeded = 0
        failed = 0
        for iid in item_ids:
            result = self.auto_remediate_item(iid, strategy)
            if "error" not in result:
                succeeded += 1
            else:
                failed += 1
        return {"total": len(item_ids), "succeeded": succeeded, "failed": failed}

    def get_debt_report(self, service_id: str = "") -> dict[str, Any]:
        items = [i for i in self.items.values() if not service_id or i.service_id == service_id]
        aging_critical = [i for i in items if i.severity == DebtSeverity.CRITICAL
                          and (datetime.utcnow() - i.created_at).days > 30]
        return {
            "service_id": service_id or "all",
            "total_items": len(items),
            "critical_open": len([i for i in items if i.severity == DebtSeverity.CRITICAL and i.status == DebtStatus.OPEN]),
            "high_open": len([i for i in items if i.severity == DebtSeverity.HIGH and i.status == DebtStatus.OPEN]),
            "aging_critical": len(aging_critical),
            "avg_effort_hours": round(sum(i.effort_hours or 0 for i in items) / max(len(items), 1), 1),
            "resolution_rate": round(
                sum(1 for i in items if i.status == DebtStatus.RESOLVED) / max(len(items), 1) * 100, 1),
        }

    def export_debt_csv(self, service_id: str = "") -> str:
        items = [i for i in self.items.values() if not service_id or i.service_id == service_id]
        lines = ["id,title,severity,category,status,service_id,assignee,created_at,effort_hours"]
        for item in items:
            lines.append(f"{item.item_id},{item.title},{item.severity.value},{item.category.value},"
                         f"{item.status.value},{item.service_id},{item.assigned_to or ''},"
                         f"{item.created_at.isoformat()},{item.effort_hours or 0}")
        return "\n".join(lines)

    def get_service_rankings(self) -> list[dict[str, Any]]:
        rankings: dict[str, dict[str, Any]] = {}
        for item in self.items.values():
            if item.service_id not in rankings:
                rankings[item.service_id] = {"service_id": item.service_id, "total": 0,
                                              "critical": 0, "high": 0, "medium": 0, "low": 0}
            rankings[item.service_id]["total"] += 1
            if item.severity == DebtSeverity.CRITICAL:
                rankings[item.service_id]["critical"] += 1
            elif item.severity == DebtSeverity.HIGH:
                rankings[item.service_id]["high"] += 1
            elif item.severity == DebtSeverity.MEDIUM:
                rankings[item.service_id]["medium"] += 1
            else:
                rankings[item.service_id]["low"] += 1
        return sorted(rankings.values(), key=lambda x: x["critical"], reverse=True)

    def batch_update_effort(self, item_ids: list[str], effort_hours: float) -> int:
        count = 0
        for iid in item_ids:
            item = self.items.get(iid)
            if item:
                item.effort_hours = effort_hours
                count += 1
        return count

    def add_dependency_link(self, item_id: str, linked_item_id: str) -> bool:
        if item_id not in self.items or linked_item_id not in self.items:
            return False
        if not hasattr(self, "_dependency_links"):
            self._dependency_links: dict[str, list[str]] = {}
        if item_id not in self._dependency_links:
            self._dependency_links[item_id] = []
        if linked_item_id not in self._dependency_links[item_id]:
            self._dependency_links[item_id].append(linked_item_id)
        return True

    def get_dependency_chain(self, item_id: str) -> list[str]:
        chain = []
        visited = set()
        def traverse(iid: str) -> None:
            if iid in visited:
                return
            visited.add(iid)
            chain.append(iid)
            links = getattr(self, "_dependency_links", {}).get(iid, [])
            for lid in links:
                traverse(lid)
        traverse(item_id)
        return chain

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
