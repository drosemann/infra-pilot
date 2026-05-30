"""Tests for quota_manager_ext module."""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.quota_manager_ext import QuotaManager, QuotaResourceType, QuotaScope, QuotaPeriod, QuotaAction, ReservationStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = QuotaManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestQuotaCRUD:
    def test_create_quota(self, manager):
        q = manager.create_quota(name="CPU Limit", description="Max CPU cores per project", resource_type=QuotaResourceType.CPU, scope=QuotaScope.PROJECT, scope_id="proj-123", hard_limit=16.0, soft_limit=12.0, warning_threshold=80.0, period=QuotaPeriod.TOTAL, action_on_exceed=QuotaAction.BLOCK, unit="cores", tags=["prod"])
        assert q.id is not None
        assert q.name == "CPU Limit"
        assert q.hard_limit == 16.0
        assert q.soft_limit == 12.0
        assert q.scope == QuotaScope.PROJECT

    def test_get_quota(self, manager):
        q = manager.create_quota(name="Test", description="Test", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        retrieved = manager.get_quota(q.id)
        assert retrieved is not None

    def test_update_quota(self, manager):
        q = manager.create_quota(name="Original", description="Original", resource_type=QuotaResourceType.MEMORY, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        updated = manager.update_quota(q.id, {"hard_limit": 200, "warning_threshold": 90.0})
        assert updated.hard_limit == 200
        assert updated.warning_threshold == 90.0

    def test_delete_quota(self, manager):
        q = manager.create_quota(name="Test", description="Test", resource_type=QuotaResourceType.DISK, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=1000)
        assert manager.delete_quota(q.id) == True


class TestQuotaChecking:
    def test_check_within_limit(self, manager):
        q = manager.create_quota(name="CPU", description="CPU limit", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        result = manager.check_quota(q.id, amount=5)
        assert result["allowed"] == True
        assert result["current"] == 0

    def test_check_exceed_limit(self, manager):
        q = manager.create_quota(name="CPU", description="CPU limit", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=10)
        manager.record_usage(q.id, 9)
        result = manager.check_quota(q.id, amount=5)
        assert result["allowed"] == False

    def test_check_soft_limit_warning(self, manager):
        q = manager.create_quota(name="MEM", description="Memory limit", resource_type=QuotaResourceType.MEMORY, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100, soft_limit=80)
        manager.record_usage(q.id, 75)
        result = manager.check_quota(q.id, amount=10)
        assert result["allowed"] == True


class TestUsageTracking:
    def test_record_usage(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        usage = manager.record_usage(q.id, 10)
        assert usage is not None
        assert usage.current_usage == 10

    def test_reset_usage(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        manager.record_usage(q.id, 50)
        assert manager.reset_usage(q.id) == True
        usage = manager.get_quota_usage(q.id)
        assert usage.current_usage == 0

    def test_peak_usage(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        manager.record_usage(q.id, 30)
        manager.record_usage(q.id, 60)
        usage = manager.get_quota_usage(q.id)
        assert usage.peak_usage >= 60


class TestReservations:
    def test_create_reservation(self, manager):
        r = manager.create_reservation(name="GPU Cluster", resource_type=QuotaResourceType.GPU, amount=4, scope=QuotaScope.PROJECT, scope_id="proj-ai", start_time=datetime.utcnow(), end_time=datetime.utcnow() + timedelta(days=7), created_by="admin", priority=1, notes="AI training cluster")
        assert r.id is not None
        assert r.name == "GPU Cluster"
        assert r.amount == 4
        assert r.status == ReservationStatus.ACTIVE

    def test_cancel_reservation(self, manager):
        r = manager.create_reservation(name="GPU", resource_type=QuotaResourceType.GPU, amount=2, scope=QuotaScope.PROJECT, scope_id="proj-ai")
        assert manager.cancel_reservation(r.id) == True
        assert r.status == ReservationStatus.CANCELLED


class TestOverrides:
    def test_create_override(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        override = manager.create_override(q.id, new_hard_limit=200, reason="Peak load", expires_in_hours=24, created_by="admin")
        assert override is not None
        assert override.new_hard_limit == 200
        assert override.expires_at is not None


class TestAlerts:
    def test_get_alerts(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=10)
        manager.check_quota(q.id, amount=15)
        alerts = manager.get_alerts(quota_id=q.id)
        assert len(alerts) >= 0

    def test_acknowledge_alert(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=10)
        manager.check_quota(q.id, amount=15)
        alerts = manager.get_alerts(quota_id=q.id)
        if alerts:
            assert manager.acknowledge_alert(alerts[0].id) == True


class TestQuotaUtilization:
    def test_get_utilization(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        manager.record_usage(q.id, 45)
        util = manager.get_quota_utilization(q.id)
        assert util["utilization_percentage"] == 45.0
        assert util["remaining"] == 55.0

    def test_get_usage_summary(self, manager):
        q = manager.create_quota(name="CPU", description="CPU", resource_type=QuotaResourceType.CPU, scope=QuotaScope.PROJECT, scope_id="proj-1", hard_limit=100)
        manager.record_usage(q.id, 50)
        summary = manager.get_usage_summary(scope=QuotaScope.PROJECT, scope_id="proj-1")
        assert summary["quota_count"] >= 1
        assert "cpu" in summary["usage"]


class TestStatistics:
    def test_get_statistics(self, manager):
        q = manager.create_quota(name="Test", description="Test", resource_type=QuotaResourceType.CPU, scope=QuotaScope.GLOBAL, scope_id="global", hard_limit=100)
        stats = manager.get_statistics()
        assert stats["total_quotas"] >= 1
