import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class WindowStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"
    EXTENDED = "extended"


class MaintenancePlanner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._windows: Dict[str, Dict] = {}
        self._blackout_periods: List[Dict] = []
        self._calendar_events: Dict[str, List[Dict]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("MaintenancePlanner initialized")

    async def close(self) -> None:
        self._windows.clear()
        self._blackout_periods.clear()
        logger.info("MaintenancePlanner closed")

    def create_window(self, name: str, description: str, start_time: str,
                      end_time: str, affected_resources: List[str],
                      action_plan: str, rollback_plan: str,
                      assigned_team: str = "ops",
                      requires_approval: bool = True,
                      notification_channels: Optional[List[str]] = None,
                      tags: Optional[List[str]] = None) -> Dict:
        window_id = str(uuid.uuid4())
        window = {
            "window_id": window_id,
            "name": name,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "affected_resources": affected_resources,
            "action_plan": action_plan,
            "rollback_plan": rollback_plan,
            "assigned_team": assigned_team,
            "status": WindowStatus.SCHEDULED.value,
            "requires_approval": requires_approval,
            "approved_by": None,
            "approved_at": None,
            "notification_channels": notification_channels or ["discord"],
            "tags": tags or [],
            "actual_start_time": None,
            "actual_end_time": None,
            "completion_notes": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if self._check_blackout_conflict(start_time, end_time):
            raise ValueError("Window conflicts with blackout period")

        self._windows[window_id] = window
        self._sync_to_calendar(window)
        logger.info(f"Maintenance window {window_id} created: {name}")
        return window

    def get_window(self, window_id: str) -> Optional[Dict]:
        return self._windows.get(window_id)

    def update_window(self, window_id: str, updates: Dict) -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window:
            return None
        if window["status"] not in (WindowStatus.SCHEDULED.value, WindowStatus.EXTENDED.value):
            raise ValueError(f"Cannot update window in status: {window['status']}")
        for key, value in updates.items():
            if key not in ("window_id", "created_at"):
                window[key] = value
        window["updated_at"] = datetime.utcnow().isoformat()
        self._sync_to_calendar(window)
        return window

    def delete_window(self, window_id: str) -> bool:
        if window_id not in self._windows:
            return False
        del self._windows[window_id]
        return True

    def approve_window(self, window_id: str, approved_by: str) -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window:
            return None
        window["approved_by"] = approved_by
        window["approved_at"] = datetime.utcnow().isoformat()
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Window {window_id} approved by {approved_by}")
        return window

    def start_window(self, window_id: str) -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window or window["status"] != WindowStatus.SCHEDULED.value:
            return None
        window["status"] = WindowStatus.IN_PROGRESS.value
        window["actual_start_time"] = datetime.utcnow().isoformat()
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Maintenance window {window_id} started")
        return window

    def complete_window(self, window_id: str, notes: str = "") -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window or window["status"] != WindowStatus.IN_PROGRESS.value:
            return None
        window["status"] = WindowStatus.COMPLETED.value
        window["actual_end_time"] = datetime.utcnow().isoformat()
        window["completion_notes"] = notes
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Maintenance window {window_id} completed")
        return window

    def fail_window(self, window_id: str, reason: str) -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window or window["status"] not in (WindowStatus.IN_PROGRESS.value, WindowStatus.SCHEDULED.value):
            return None
        window["status"] = WindowStatus.FAILED.value
        window["actual_end_time"] = datetime.utcnow().isoformat()
        window["completion_notes"] = f"FAILED: {reason}"
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.warning(f"Maintenance window {window_id} failed: {reason}")
        return window

    def cancel_window(self, window_id: str, reason: str = "") -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window:
            return None
        window["status"] = WindowStatus.CANCELLED.value
        window["completion_notes"] = reason or "Cancelled"
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Maintenance window {window_id} cancelled")
        return window

    def extend_window(self, window_id: str, new_end_time: str, reason: str) -> Optional[Dict]:
        window = self._windows.get(window_id)
        if not window or window["status"] != WindowStatus.IN_PROGRESS.value:
            return None
        window["status"] = WindowStatus.EXTENDED.value
        window["end_time"] = new_end_time
        window["completion_notes"] = f"Extended: {reason}"
        window["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Maintenance window {window_id} extended to {new_end_time}")
        return window

    def list_windows(self, status: Optional[str] = None, team: Optional[str] = None,
                     date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        windows = list(self._windows.values())
        if status:
            windows = [w for w in windows if w["status"] == status]
        if team:
            windows = [w for w in windows if w["assigned_team"] == team]
        if date_from:
            windows = [w for w in windows if w.get("start_time", "") >= date_from]
        if date_to:
            windows = [w for w in windows if w.get("end_time", "") <= date_to]
        return sorted(windows, key=lambda w: w.get("start_time", ""))

    def add_blackout_period(self, name: str, start_time: str, end_time: str,
                            reason: str) -> Dict:
        period = {
            "blackout_id": str(uuid.uuid4()),
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._blackout_periods.append(period)
        logger.info(f"Blackout period added: {name}")
        return period

    def list_blackout_periods(self) -> List[Dict]:
        return sorted(self._blackout_periods, key=lambda p: p.get("start_time", ""))

    def remove_blackout_period(self, blackout_id: str) -> bool:
        for i, p in enumerate(self._blackout_periods):
            if p["blackout_id"] == blackout_id:
                self._blackout_periods.pop(i)
                return True
        return False

    def _check_blackout_conflict(self, start_time: str, end_time: str) -> bool:
        for period in self._blackout_periods:
            if start_time < period["end_time"] and end_time > period["start_time"]:
                return True
        return False

    def get_calendar_data(self, date_from: str, date_to: str) -> List[Dict]:
        events = []
        for window in self._windows.values():
            if window.get("start_time", "") <= date_to and window.get("end_time", "") >= date_from:
                events.append({
                    "id": window["window_id"],
                    "title": window["name"],
                    "start": window["start_time"],
                    "end": window["end_time"],
                    "status": window["status"],
                    "allDay": False,
                    "className": f"status-{window['status']}",
                })
        return events

    def _sync_to_calendar(self, window: Dict) -> None:
        pass

    def get_upcoming_schedule(self, days: int = 30) -> Dict:
        now = datetime.utcnow()
        end = now + timedelta(days=days)
        upcoming = []
        for window in self._windows.values():
            try:
                w_start = datetime.fromisoformat(window["start_time"])
                if now <= w_start <= end and window["status"] in (
                    WindowStatus.SCHEDULED.value, WindowStatus.APPROVED.value
                ):
                    upcoming.append(window)
            except (ValueError, TypeError):
                continue
        upcoming.sort(key=lambda w: w.get("start_time", ""))
        return {
            "period_days": days,
            "upcoming_count": len(upcoming),
            "windows": upcoming,
            "blackout_periods": self._blackout_periods,
        }

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._windows)
        by_status = {}
        for w in self._windows.values():
            by_status[w["status"]] = by_status.get(w["status"], 0) + 1
        completed = sum(1 for w in self._windows.values() if w["status"] == WindowStatus.COMPLETED.value)
        failed = sum(1 for w in self._windows.values() if w["status"] == WindowStatus.FAILED.value)
        return {
            "total_windows": total,
            "by_status": by_status,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) > 0 else 0,
            "blackout_periods": len(self._blackout_periods),
        }
