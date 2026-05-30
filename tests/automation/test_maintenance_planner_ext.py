"""Tests for maintenance_planner_ext module."""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.maintenance_planner_ext import MaintenancePlannerManager, MaintenanceStatus, MaintenanceType, MaintenancePriority, MaintenanceImpact


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = MaintenancePlannerManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestWindowCRUD:
    def test_create_window(self, manager):
        start = datetime.utcnow() + timedelta(days=1)
        w = manager.create_window(name="Server Upgrade", description="Upgrade database servers", start_time=start, duration_minutes=120, timezone="UTC", maintenance_type=MaintenanceType.SCHEDULED, priority=MaintenancePriority.HIGH, impact=MaintenanceImpact.DOWNTIME, affected_services=["database", "api"], created_by="admin")
        assert w.id is not None
        assert w.name == "Server Upgrade"
        assert w.duration_minutes == 120
        assert w.status == MaintenanceStatus.DRAFT

    def test_get_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        retrieved = manager.get_window(w.id)
        assert retrieved is not None

    def test_update_window(self, manager):
        w = manager.create_window(name="Original", description="Original", start_time=datetime.utcnow())
        updated = manager.update_window(w.id, {"name": "Updated", "priority": MaintenancePriority.CRITICAL})
        assert updated.name == "Updated"
        assert updated.priority == MaintenancePriority.CRITICAL

    def test_delete_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        assert manager.delete_window(w.id) == True


class TestTasks:
    def test_add_task(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        task = manager.add_task(w.id, "Stop Service", "Stop the web server", order=1, estimated_duration_minutes=15, steps=["systemctl stop nginx", "verify stopped"], rollback_steps=["systemctl start nginx"], requires_approval=True)
        assert task is not None
        assert task.name == "Stop Service"
        assert task.requires_approval == True

    def test_update_task_status(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        task = manager.add_task(w.id, "Task1", "Test task", order=1)
        assert manager.update_task_status(w.id, task.id, "completed") == True


class TestApprovals:
    def test_approve_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow(), created_by="user1")
        w.required_approvers = ["admin"]
        approval = manager.approve_window(w.id, "admin", "Looks good")
        assert approval is not None
        assert approval.status.value == "approved"

    def test_reject_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        rejection = manager.reject_window(w.id, "admin", "Not ready")
        assert rejection is not None
        assert rejection.status.value == "rejected"


class TestWindowLifecycle:
    def test_execute_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        w.status = MaintenanceStatus.APPROVED
        result = manager.execute_window(w.id)
        assert result is not None

    def test_cancel_window(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        w.status = MaintenanceStatus.SCHEDULED
        assert manager.cancel_window(w.id, "Postponed") == True
        assert w.status == MaintenanceStatus.CANCELLED


class TestResources:
    def test_add_affected_resource(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        assert manager.add_affected_resource(w.id, "server-01", "vm", "primary") == True
        assert len(w.affected_resources) == 1


class TestTemplates:
    def test_create_template(self, manager):
        tmpl = manager.create_template(name="Standard Deploy", description="Standard deployment", category="deployment", tasks=[{"name": "Backup", "order": 1, "steps": ["backup db"]}], estimated_duration_minutes=60, default_impact=MaintenanceImpact.MINIMAL, required_approvers=["ops-lead"], tags=["deploy"])
        assert tmpl.id is not None
        assert tmpl.name == "Standard Deploy"

    def test_apply_template(self, manager):
        tmpl = manager.create_template(name="Deploy", description="Standard deploy", category="deployment")
        w = manager.apply_template(tmpl.id, "My Window", "My deployment", datetime.utcnow() + timedelta(days=1), created_by="admin")
        assert w is not None
        assert w.name == "My Window"


class TestQueries:
    def test_get_upcoming(self, manager):
        manager.create_window(name="Future", description="Future", start_time=datetime.utcnow() + timedelta(days=2))
        manager.create_window(name="Past", description="Past", start_time=datetime.utcnow() - timedelta(days=2))
        upcoming = manager.get_upcoming(days=7)
        assert len(upcoming) >= 1

    def test_check_conflicts(self, manager):
        w1 = manager.create_window(name="W1", description="Test", start_time=datetime.utcnow() + timedelta(hours=1))
        w1.status = MaintenanceStatus.SCHEDULED
        w2_start = datetime.utcnow() + timedelta(hours=2)
        w2_end = w2_start + timedelta(hours=3)
        conflicts = manager.check_conflicts(w2_start, w2_end, exclude_window_id=None)
        assert conflicts is not None

    def test_get_calendar_events(self, manager):
        w = manager.create_window(name="Event", description="Event", start_time=datetime.utcnow())
        w.status = MaintenanceStatus.SCHEDULED
        events = manager.get_calendar_events(datetime.utcnow() - timedelta(days=1), datetime.utcnow() + timedelta(days=7))
        assert len(events) >= 1


class TestTimeline:
    def test_get_window_timeline(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        timeline = manager.get_window_timeline(w.id)
        assert len(timeline) >= 1
        assert timeline[0]["window_id"] == w.id


class TestSearch:
    def test_search_windows(self, manager):
        manager.create_window(name="Database Upgrade", description="Upgrade DB", start_time=datetime.utcnow())
        results = manager.search_windows("database")
        assert len(results) >= 1


class TestReport:
    def test_generate_report(self, manager):
        manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        report = manager.generate_report(days_back=30)
        assert report["period_days"] == 30
        assert report["total_windows"] >= 0


class TestStatistics:
    def test_get_statistics(self, manager):
        w = manager.create_window(name="Test", description="Test", start_time=datetime.utcnow())
        stats = manager.get_statistics()
        assert stats["total_windows"] >= 1
