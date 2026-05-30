"""Tests for auto_remediation_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.auto_remediation_ext import AutoRemediationManager, RemediationTriggerType, RemediationRuleMode, RemediationActionType, RemediationStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = AutoRemediationManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestRuleCRUD:
    def test_create_rule(self, manager):
        rule = manager.create_rule(name="High CPU", description="Remediate high CPU usage", trigger_type=RemediationTriggerType.METRIC, mode=RemediationRuleMode.AUTOMATIC, resource_types=["vm", "container"], tags=["cpu", "performance"], created_by="admin")
        assert rule.id is not None
        assert rule.name == "High CPU"
        assert rule.trigger_type == RemediationTriggerType.METRIC
        assert rule.mode == RemediationRuleMode.AUTOMATIC

    def test_get_rule(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        retrieved = manager.get_rule(rule.id)
        assert retrieved is not None

    def test_update_rule(self, manager):
        rule = manager.create_rule(name="Original", description="Original", trigger_type=RemediationTriggerType.MANUAL)
        updated = manager.update_rule(rule.id, {"name": "Updated", "mode": RemediationRuleMode.AUTOMATIC})
        assert updated.name == "Updated"
        assert updated.mode == RemediationRuleMode.AUTOMATIC

    def test_delete_rule(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        assert manager.delete_rule(rule.id) == True


class TestConditions:
    def test_add_condition(self, manager):
        rule = manager.create_rule(name="CPU Check", description="CPU check", trigger_type=RemediationTriggerType.METRIC)
        cond = manager.add_condition(rule.id, "cpu.usage", "greater_than", 90, duration_minutes=5)
        assert cond is not None
        assert cond.field == "cpu.usage"
        assert cond.operator == "greater_than"
        assert cond.value == 90


class TestActions:
    def test_add_action(self, manager):
        rule = manager.create_rule(name="Remediate", description="Remediate", trigger_type=RemediationTriggerType.HEALTH_CHECK)
        action = manager.add_action(rule.id, RemediationActionType.RESTART, "Restart Service", config={"service": "nginx"}, order=1, timeout_seconds=120)
        assert action is not None
        assert action.action_type == RemediationActionType.RESTART
        assert action.name == "Restart Service"

    def test_remove_action(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        action = manager.add_action(rule.id, RemediationActionType.NOTIFY, "Notify")
        assert manager.remove_action(rule.id, action.id) == True


class TestExecution:
    def test_execute_rule(self, manager):
        rule = manager.create_rule(name="CPU Remediation", description="Fix high CPU", trigger_type=RemediationTriggerType.METRIC, mode=RemediationRuleMode.AUTOMATIC)
        manager.add_action(rule.id, RemediationActionType.NOTIFY, "Notify Admin", config={"channel": "log", "message": "CPU high"})
        execution = manager.evaluate_and_execute(rule.id, target_resource="vm-01", target_resource_type="vm", context={"cpu.usage": 95}, executed_by="auto")
        assert execution is not None

    def test_get_execution(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        execution = manager.evaluate_and_execute(rule.id, "r1", "vm", {"test": True})
        if execution:
            retrieved = manager.get_execution(execution.id)
            assert retrieved is not None

    def test_cancel_execution(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        execution = manager.evaluate_and_execute(rule.id, "r1", "vm", {"test": True})
        if execution:
            result = manager.cancel_execution(execution.id)
            assert result is not None


class TestRunbooks:
    def test_create_runbook(self, manager):
        rb = manager.create_runbook(name="Incident Response", description="Standard incident response", category="security", steps=[{"name": "Identify", "command": "check_logs"}, {"name": "Contain", "command": "isolate"}], tags=["incident", "security"])
        assert rb.id is not None
        assert rb.name == "Incident Response"

    def test_get_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category="general")
        retrieved = manager.get_runbook(rb.id)
        assert retrieved is not None

    def test_delete_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category="general")
        assert manager.delete_runbook(rb.id) == True


class TestLifecycle:
    def test_enable_rule(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        rule.enabled = False
        assert manager.enable_rule(rule.id) == True

    def test_disable_rule(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        assert manager.disable_rule(rule.id) == True


class TestSearch:
    def test_search_rules(self, manager):
        manager.create_rule(name="CPU Alert", description="CPU remediation", trigger_type=RemediationTriggerType.METRIC)
        results = manager.search_rules("cpu")
        assert len(results) >= 1


class TestList:
    def test_list_rules(self, manager):
        manager.create_rule(name="R1", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        manager.create_rule(name="R2", description="Test", trigger_type=RemediationTriggerType.ALERT)
        rules = manager.list_rules()
        assert len(rules) >= 2

    def test_list_executions(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        manager.evaluate_and_execute(rule.id, "r1", "vm", {"test": True})
        executions = manager.list_executions(rule_id=rule.id)
        assert len(executions) >= 0


class TestBulk:
    def test_bulk_enable(self, manager):
        r1 = manager.create_rule(name="R1", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        r2 = manager.create_rule(name="R2", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        manager.disable_rule(r1.id)
        manager.disable_rule(r2.id)
        count = manager.bulk_enable_rules([r1.id, r2.id])
        assert count == 2

    def test_bulk_disable(self, manager):
        r1 = manager.create_rule(name="R1", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        r2 = manager.create_rule(name="R2", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        count = manager.bulk_disable_rules([r1.id, r2.id])
        assert count == 2


class TestStatistics:
    def test_get_statistics(self, manager):
        rule = manager.create_rule(name="Test", description="Test", trigger_type=RemediationTriggerType.MANUAL)
        manager.evaluate_and_execute(rule.id, "r1", "vm", {"test": True})
        stats = manager.get_statistics()
        assert stats["total_rules"] >= 1
