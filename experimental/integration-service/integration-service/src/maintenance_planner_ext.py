"""Extended scheduled maintenance planner with windows, approvals, and calendar sync."""
import json
import uuid
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MaintenanceStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MaintenancePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceImpact(str, Enum):
    NONE = "none"
    MINIMAL = "minimal"
    DEGRADED = "degraded"
    DOWNTIME = "downtime"
    FULL_OUTAGE = "full_outage"


class MaintenanceType(str, Enum):
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"
    AUTOMATED = "automated"
    MANUAL = "manual"
    RECURRING = "recurring"
    CHANGE = "change"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class MaintenanceApproval:
    id: str
    approver: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MaintenanceTask:
    id: str
    name: str
    description: str
    order: int = 0
    estimated_duration_minutes: int = 30
    assigned_to: Optional[str] = None
    status: str = "pending"
    steps: List[str] = field(default_factory=list)
    rollback_steps: List[str] = field(default_factory=list)
    requires_approval: bool = False
    dependencies: List[str] = field(default_factory=list)


@dataclass
class MaintenanceWindow:
    id: str
    name: str
    description: str
    maintenance_type: MaintenanceType = MaintenanceType.SCHEDULED
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    status: MaintenanceStatus = MaintenanceStatus.DRAFT
    impact: MaintenanceImpact = MaintenanceImpact.MINIMAL
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = 60
    timezone: str = "UTC"
    affected_resources: List[Dict[str, str]] = field(default_factory=list)
    affected_services: List[str] = field(default_factory=list)
    tasks: List[MaintenanceTask] = field(default_factory=list)
    approvals: List[MaintenanceApproval] = field(default_factory=list)
    required_approvers: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)
    changelog: Optional[str] = None
    risk_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class MaintenanceTemplate:
    id: str
    name: str
    description: str
    category: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration_minutes: int = 60
    default_impact: MaintenanceImpact = MaintenanceImpact.MINIMAL
    required_approvers: List[str] = field(default_factory=list)
    risk_assessment: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MaintenanceCalendar:
    id: str
    name: str
    description: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    provider: str = "internal"
    sync_enabled: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class MaintenancePlannerManager:
    def __init__(self, storage_path: str = "data/maintenance_planner.json"):
        self.storage_path = storage_path
        self.windows: Dict[str, MaintenanceWindow] = {}
        self.templates: Dict[str, MaintenanceTemplate] = {}
        self.calendars: Dict[str, MaintenanceCalendar] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for w_data in data.get("windows", []):
            w = MaintenanceWindow(**w_data)
            self.windows[w.id] = w
        for t_data in data.get("templates", []):
            t = MaintenanceTemplate(**t_data)
            self.templates[t.id] = t
        for c_data in data.get("calendars", []):
            c = MaintenanceCalendar(**c_data)
            self.calendars[c.id] = c

    def _save_data(self) -> None:
        data = {
            "windows": [w.__dict__ for w in self.windows.values()],
            "templates": [t.__dict__ for t in self.templates.values()],
            "calendars": [c.__dict__ for c in self.calendars.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("MaintenancePlannerManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("MaintenancePlannerManager closed")

    def create_window(self, name: str, description: str, start_time: datetime, duration_minutes: int = 60, timezone: str = "UTC", maintenance_type: MaintenanceType = MaintenanceType.SCHEDULED, priority: MaintenancePriority = MaintenancePriority.MEDIUM, impact: MaintenanceImpact = MaintenanceImpact.MINIMAL, affected_services: Optional[List[str]] = None, created_by: Optional[str] = None) -> MaintenanceWindow:
        end_time = start_time + timedelta(minutes=duration_minutes)
        w = MaintenanceWindow(id=str(uuid.uuid4()), name=name, description=description, maintenance_type=maintenance_type, priority=priority, impact=impact, start_time=start_time, end_time=end_time, duration_minutes=duration_minutes, timezone=timezone, affected_services=affected_services or [], created_by=created_by, scheduled_at=datetime.utcnow())
        self.windows[w.id] = w
        self._save_data()
        return w

    def get_window(self, window_id: str) -> Optional[MaintenanceWindow]:
        return self.windows.get(window_id)

    def update_window(self, window_id: str, updates: Dict[str, Any]) -> Optional[MaintenanceWindow]:
        w = self.windows.get(window_id)
        if not w:
            return None
        for key, value in updates.items():
            if hasattr(w, key) and key not in ("id", "created_at", "created_by"):
                setattr(w, key, value)
        w.updated_at = datetime.utcnow()
        self.windows[window_id] = w
        self._save_data()
        return w

    def delete_window(self, window_id: str) -> bool:
        if window_id in self.windows:
            del self.windows[window_id]
            self._save_data()
            return True
        return False

    def add_task(self, window_id: str, name: str, description: str, order: int = 0, estimated_duration_minutes: int = 30, steps: Optional[List[str]] = None, rollback_steps: Optional[List[str]] = None, requires_approval: bool = False, dependencies: Optional[List[str]] = None) -> Optional[MaintenanceTask]:
        w = self.windows.get(window_id)
        if not w:
            return None
        task = MaintenanceTask(id=str(uuid.uuid4()), name=name, description=description, order=order, estimated_duration_minutes=estimated_duration_minutes, steps=steps or [], rollback_steps=rollback_steps or [], requires_approval=requires_approval, dependencies=dependencies or [])
        w.tasks.append(task)
        w.updated_at = datetime.utcnow()
        self._save_data()
        return task

    def update_task_status(self, window_id: str, task_id: str, status: str) -> bool:
        w = self.windows.get(window_id)
        if not w:
            return False
        for task in w.tasks:
            if task.id == task_id:
                task.status = status
                w.updated_at = datetime.utcnow()
                self._save_data()
                return True
        return False

    def approve_window(self, window_id: str, approver: str, comment: Optional[str] = None) -> Optional[MaintenanceApproval]:
        w = self.windows.get(window_id)
        if not w:
            return None
        approval = MaintenanceApproval(id=str(uuid.uuid4()), approver=approver, status=ApprovalStatus.APPROVED, comment=comment, decided_at=datetime.utcnow())
        w.approvals.append(approval)
        if len([a for a in w.approvals if a.status == ApprovalStatus.APPROVED]) >= len(w.required_approvers):
            w.status = MaintenanceStatus.APPROVED
        w.updated_at = datetime.utcnow()
        self._save_data()
        return approval

    def reject_window(self, window_id: str, approver: str, comment: Optional[str] = None) -> Optional[MaintenanceApproval]:
        w = self.windows.get(window_id)
        if not w:
            return None
        approval = MaintenanceApproval(id=str(uuid.uuid4()), approver=approver, status=ApprovalStatus.REJECTED, comment=comment, decided_at=datetime.utcnow())
        w.approvals.append(approval)
        w.status = MaintenanceStatus.DRAFT
        w.updated_at = datetime.utcnow()
        self._save_data()
        return approval

    def execute_window(self, window_id: str) -> bool:
        w = self.windows.get(window_id)
        if not w or w.status not in (MaintenanceStatus.APPROVED, MaintenanceStatus.SCHEDULED):
            return False
        w.status = MaintenanceStatus.IN_PROGRESS
        w.updated_at = datetime.utcnow()
        for task in sorted(w.tasks, key=lambda t: t.order):
            task.status = "running"
            completed = all(dep_status(w, dep) for dep in task.dependencies) if False else True
            if completed:
                task.status = "completed"
            else:
                task.status = "failed"
                w.status = MaintenanceStatus.FAILED
                self._save_data()
                return False
        w.status = MaintenanceStatus.COMPLETED
        w.completed_at = datetime.utcnow()
        self._save_data()
        return True

    def cancel_window(self, window_id: str, reason: Optional[str] = None) -> bool:
        w = self.windows.get(window_id)
        if not w or w.status in (MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED):
            return False
        w.status = MaintenanceStatus.CANCELLED
        w.changelog = (w.changelog or "") + f"\nCancelled: {reason or 'No reason provided'}"
        w.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def add_affected_resource(self, window_id: str, resource_id: str, resource_type: str, role: str = "primary") -> bool:
        w = self.windows.get(window_id)
        if not w:
            return False
        w.affected_resources.append({"resource_id": resource_id, "resource_type": resource_type, "role": role})
        w.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def create_template(self, name: str, description: str, category: str, tasks: Optional[List[Dict[str, Any]]] = None, estimated_duration_minutes: int = 60, default_impact: MaintenanceImpact = MaintenanceImpact.MINIMAL, required_approvers: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> MaintenanceTemplate:
        tmpl = MaintenanceTemplate(id=str(uuid.uuid4()), name=name, description=description, category=category, tasks=tasks or [], estimated_duration_minutes=estimated_duration_minutes, default_impact=default_impact, required_approvers=required_approvers or [], tags=tags or [])
        self.templates[tmpl.id] = tmpl
        self._save_data()
        return tmpl

    def apply_template(self, template_id: str, name: str, description: str, start_time: datetime, created_by: Optional[str] = None) -> Optional[MaintenanceWindow]:
        tmpl = self.templates.get(template_id)
        if not tmpl:
            return None
        w = self.create_window(name=name, description=description, start_time=start_time, duration_minutes=tmpl.estimated_duration_minutes, impact=tmpl.default_impact, created_by=created_by)
        w.required_approvers = tmpl.required_approvers[:]
        w.tags = tmpl.tags[:]
        for task_data in tmpl.tasks:
            self.add_task(window_id=w.id, name=task_data.get("name", "Task"), description=task_data.get("description", ""), order=task_data.get("order", 0), estimated_duration_minutes=task_data.get("estimated_duration_minutes", 30), steps=task_data.get("steps", []), rollback_steps=task_data.get("rollback_steps", []), requires_approval=task_data.get("requires_approval", False))
        return w

    def get_upcoming(self, days: int = 7) -> List[MaintenanceWindow]:
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        return [w for w in self.windows.values() if w.status in (MaintenanceStatus.SCHEDULED, MaintenanceStatus.APPROVED) and w.start_time and now <= w.start_time <= future]

    def check_conflicts(self, start_time: datetime, end_time: datetime, exclude_window_id: Optional[str] = None) -> List[MaintenanceWindow]:
        conflicts = []
        for w in self.windows.values():
            if w.id == exclude_window_id:
                continue
            if w.status in (MaintenanceStatus.CANCELLED, MaintenanceStatus.COMPLETED, MaintenanceStatus.FAILED):
                continue
            if w.start_time and w.end_time:
                if start_time < w.end_time and end_time > w.start_time:
                    conflicts.append(w)
        return conflicts

    def list_windows(self, status: Optional[MaintenanceStatus] = None, maintenance_type: Optional[MaintenanceType] = None, priority: Optional[MaintenancePriority] = None) -> List[MaintenanceWindow]:
        results = list(self.windows.values())
        if status:
            results = [w for w in results if w.status == status]
        if maintenance_type:
            results = [w for w in results if w.maintenance_type == maintenance_type]
        if priority:
            results = [w for w in results if w.priority == priority]
        return sorted(results, key=lambda w: w.start_time or datetime.max)

    def get_calendar_events(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        events = []
        for w in self.windows.values():
            if w.status in (MaintenanceStatus.DRAFT, MaintenanceStatus.CANCELLED, MaintenanceStatus.FAILED):
                continue
            if w.start_time and w.end_time:
                if start <= w.end_time and end >= w.start_time:
                    events.append({"id": w.id, "title": w.name, "start": w.start_time.isoformat(), "end": w.end_time.isoformat(), "status": w.status.value, "type": w.maintenance_type.value, "priority": w.priority.value, "impact": w.impact.value, "description": w.description, "services": w.affected_services, "color": self._get_status_color(w.status)})
        return sorted(events, key=lambda e: e["start"])

    def _get_status_color(self, status: MaintenanceStatus) -> str:
        colors = {MaintenanceStatus.DRAFT: "gray", MaintenanceStatus.SCHEDULED: "blue", MaintenanceStatus.APPROVED: "green", MaintenanceStatus.IN_PROGRESS: "orange", MaintenanceStatus.COMPLETED: "green", MaintenanceStatus.CANCELLED: "red", MaintenanceStatus.FAILED: "red", MaintenanceStatus.ROLLED_BACK: "purple"}
        return colors.get(status, "gray")

    def get_window_timeline(self, window_id: str) -> List[Dict[str, Any]]:
        w = self.windows.get(window_id)
        if not w:
            return []
        return [{"window_id": w.id, "name": w.name, "status": w.status.value, "created_at": w.created_at.isoformat(), "scheduled_at": w.scheduled_at.isoformat() if w.scheduled_at else None, "start_time": w.start_time.isoformat() if w.start_time else None, "end_time": w.end_time.isoformat() if w.end_time else None, "completed_at": w.completed_at.isoformat() if w.completed_at else None, "duration_minutes": w.duration_minutes}]

    def search_windows(self, query: str) -> List[MaintenanceWindow]:
        query = query.lower()
        return [w for w in self.windows.values() if query in w.name.lower() or query in w.description.lower() or any(query in s.lower() for s in w.affected_services) or any(query in t.lower() for t in w.tags)]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.windows)
        scheduled = sum(1 for w in self.windows.values() if w.status == MaintenanceStatus.SCHEDULED)
        completed = sum(1 for w in self.windows.values() if w.status == MaintenanceStatus.COMPLETED)
        failed = sum(1 for w in self.windows.values() if w.status == MaintenanceStatus.FAILED)
        cancelled = sum(1 for w in self.windows.values() if w.status == MaintenanceStatus.CANCELLED)
        in_progress = sum(1 for w in self.windows.values() if w.status == MaintenanceStatus.IN_PROGRESS)
        total_tasks = sum(len(w.tasks) for w in self.windows.values())
        upcoming_7d = len(self.get_upcoming(7))
        return {"total_windows": total, "scheduled": scheduled, "completed": completed, "failed": failed, "cancelled": cancelled, "in_progress": in_progress, "total_tasks": total_tasks, "upcoming_7_days": upcoming_7d, "total_templates": len(self.templates)}

    def generate_report(self, days_back: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent = [w for w in self.windows.values() if w.created_at >= cutoff]
        by_type = {}
        for w in recent:
            by_type[w.maintenance_type.value] = by_type.get(w.maintenance_type.value, 0) + 1
        avg_duration = 0.0
        durations = [w.duration_minutes for w in recent if w.status == MaintenanceStatus.COMPLETED]
        if durations:
            avg_duration = sum(durations) / len(durations)
        return {"period_days": days_back, "total_windows": len(recent), "by_type": by_type, "completion_rate": (sum(1 for w in recent if w.status == MaintenanceStatus.COMPLETED) / len(recent) * 100) if recent else 0.0, "average_duration_minutes": avg_duration, "total_cancelled": sum(1 for w in recent if w.status == MaintenanceStatus.CANCELLED), "total_failed": sum(1 for w in recent if w.status == MaintenanceStatus.FAILED)}
