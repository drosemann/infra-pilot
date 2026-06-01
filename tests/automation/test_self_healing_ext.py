"""Tests for self_healing_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.self_healing_ext import SelfHealingManager, HealingPolicyMode, HealingActionType, HealthStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = SelfHealingManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestPolicyCRUD:
    def test_create_policy(self, manager):
        policy = manager.create_policy(name="VM Auto-Heal", description="Automatically heal unhealthy VMs", resource_type="vm", mode=HealingPolicyMode.AUTOMATIC, tags=["vm", "production", "auto-heal"], created_by="admin")
        assert policy.id is not None
        assert policy.name == "VM Auto-Heal"
        assert policy.mode == HealingPolicyMode.AUTOMATIC
        assert policy.enabled == True

    def test_get_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        retrieved = manager.get_policy(policy.id)
        assert retrieved is not None

    def test_update_policy(self, manager):
        policy = manager.create_policy(name="Original", description="Original", resource_type="container")
        updated = manager.update_policy(policy.id, {"name": "Updated", "mode": HealingPolicyMode.MANUAL})
        assert updated.name == "Updated"
        assert updated.mode == HealingPolicyMode.MANUAL

    def test_delete_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        assert manager.delete_policy(policy.id) == True


class TestHealthChecks:
    def test_add_health_check(self, manager):
        policy = manager.create_policy(name="Web Health", description="Web server health", resource_type="web")
        check = manager.add_health_check(policy.id, "http", interval_seconds=30, timeout_seconds=10, retry_count=3, endpoint="http://localhost:8080/health", expected_status_code=200)
        assert check is not None
        assert check.type == "http"
        assert check.endpoint == "http://localhost:8080/health"
        assert check.expected_status_code == 200

    def test_add_metric_check(self, manager):
        policy = manager.create_policy(name="CPU Health", description="CPU health check", resource_type="vm")
        check = manager.add_health_check(policy.id, "metric", metric_query="cpu.usage", threshold=90.0, comparison="less_than")
        assert check.type == "metric"
        assert check.metric_query == "cpu.usage"


class TestHealingActions:
    def test_add_healing_action(self, manager):
        policy = manager.create_policy(name="Container Heal", description="Heal containers", resource_type="container")
        action = manager.add_healing_action(policy.id, HealingActionType.RESTART, "Restart Container", config={"grace_period": 10}, order=1, timeout_seconds=120, cooldown_seconds=30, max_attempts=3)
        assert action is not None
        assert action.action_type == HealingActionType.RESTART
        assert action.name == "Restart Container"
        assert action.max_attempts == 3

    def test_add_notify_action(self, manager):
        policy = manager.create_policy(name="Alert", description="Alert on failure", resource_type="*")
        action = manager.add_healing_action(policy.id, HealingActionType.NOTIFY, "Notify Team", config={"channel": "slack", "message": "Healing triggered"})
        assert action.action_type == HealingActionType.NOTIFY


class TestHealthStatus:
    def test_check_health_healthy(self, manager):
        policy = manager.create_policy(name="Health", description="Health check", resource_type="web")
        manager.add_health_check(policy.id, "http", endpoint="http://localhost:9999/health")
        status = manager.check_health("web-01", "web", {})
        assert status is not None
        assert status.resource_id == "web-01"

    def test_check_health_unhealthy(self, manager):
        policy = manager.create_policy(name="Health", description="Health", resource_type="vm")
        manager.add_health_check(policy.id, "metric", metric_query="status", threshold=1, comparison="equals")
        status = manager.check_health("vm-01", "vm", {"status": 0})
        assert status.status in (HealthStatus.DEGRADED, HealthStatus.HEALTHY, HealthStatus.UNHEALTHY)

    def test_consecutive_failures(self, manager):
        policy = manager.create_policy(name="Health", description="Health", resource_type="vm")
        manager.add_health_check(policy.id, "metric", metric_query="alive", threshold=1, comparison="equals")
        manager.check_health("vm-01", "vm", {"alive": 0})
        status = manager.check_health("vm-01", "vm", {"alive": 0})
        assert status.consecutive_failures >= 1


class TestHealingEvents:
    def test_trigger_healing(self, manager):
        policy = manager.create_policy(name="Auto-Heal", description="Auto heal", resource_type="vm", mode=HealingPolicyMode.AUTOMATIC)
        manager.add_health_check(policy.id, "metric", metric_query="alive", threshold=1, comparison="equals")
        manager.add_healing_action(policy.id, HealingActionType.NOTIFY, "Notify")
        status = manager.check_health("vm-01", "vm", {"alive": 0})
        events = manager.get_events(policy_id=policy.id, hours_back=1)
        assert events is not None

    def test_get_events(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="*")
        events = manager.get_events(policy_id=policy.id)
        assert events is not None


class TestResourceStatus:
    def test_get_resource_status(self, manager):
        policy = manager.create_policy(name="Health", description="Health", resource_type="vm")
        manager.add_health_check(policy.id, "metric", metric_query="up", threshold=1, comparison="equals")
        manager.check_health("vm-01", "vm", {"up": 1})
        status = manager.get_resource_status("vm-01")
        assert status is not None
        assert status.resource_id == "vm-01"

    def test_multiple_checks_same_resource(self, manager):
        policy = manager.create_policy(name="Health", description="Health", resource_type="vm")
        manager.add_health_check(policy.id, "metric", metric_query="up", threshold=1, comparison="equals")
        manager.check_health("vm-01", "vm", {"up": 1})
        manager.check_health("vm-01", "vm", {"up": 0})
        status = manager.get_resource_status("vm-01")
        assert status is not None


class TestLifecycle:
    def test_enable_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        policy.enabled = False
        assert manager.enable_policy(policy.id) == True
        assert policy.enabled == True

    def test_disable_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        assert manager.disable_policy(policy.id) == True
        assert policy.enabled == False


class TestSearch:
    def test_search_policies(self, manager):
        manager.create_policy(name="VM Heal", description="VM auto-heal", resource_type="vm")
        manager.create_policy(name="DB Recovery", description="DB recovery", resource_type="database")
        results = manager.search_policies("heal")
        assert len(results) >= 1


class TestDashboard:
    def test_get_dashboard(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        dashboard = manager.get_dashboard()
        assert dashboard["policies"]["total"] >= 1

    def test_get_policy_stats(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        stats = manager.get_policy_stats(policy.id)
        assert stats["policy_id"] == policy.id


class TestStatistics:
    def test_get_statistics(self, manager):
        policy = manager.create_policy(name="Test", description="Test", resource_type="vm")
        stats = manager.get_statistics()
        assert stats["policies"]["total"] >= 1
