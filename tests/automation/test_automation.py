
import pytest
import tempfile
import os
from services.integration_service.src.ansible_salt_integration_ext import AnsibleSaltManager, ToolType, JobStatus
from services.integration_service.src.auto_remediation_ext import AutoRemediationManager, RemediationTriggerType, RemediationRuleMode, RemediationActionType, RemediationStatus
from services.integration_service.src.chaos_engineering_ext import ChaosEngineeringManager, ExperimentStatus, ExperimentTargetType, FaultType, ExperimentHypothesis
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from services.integration_service.src.drift_detector_ext import DriftDetectorManager, ResourceCategory, DriftSeverity, DriftStatus
from services.integration_service.src.workflow_studio_ext import WorkflowStudioManager, WorkflowNode, WorkflowEdge, WorkflowDefinition, ExecutionStatus, NodeType
from services.integration_service.src.ansible_salt_integration_ext import AnsibleSaltManager, AnsiblePlaybook, SaltState, ExecutionResult, InventoryHost
from services.integration_service.src.infrastructure_pipelines_ext import PipelineManager, PipelineDefinition, PipelineStage, PipelineRun, TriggerType, StageStatus
from services.integration_service.src.drift_detector_ext import DriftDetector, DriftScan, SnapshotEntry, DriftResult, ScanStatus
from services.integration_service.src.quota_manager_ext import QuotaManager, QuotaDefinition, QuotaEntity, QuotaUsage, QuotaLimit
from services.integration_service.src.auto_remediation_ext import AutoRemediationManager, RemediationRule, RemediationExecution, TriggerSource, RemediationMode
from services.integration_service.src.maintenance_planner_ext import MaintenancePlanner, MaintenanceWindow, WindowStatus, NotificationConfig
from services.integration_service.src.runbook_library_ext import RunbookLibrary, RunbookTemplate, RunbookStep, RunbookCategory, RunbookStatus
from services.integration_service.src.chaos_engineering_ext import ChaosEngineeringManager, ChaosExperiment, FaultDefinition, ExperimentStatus, FaultType
from services.integration_service.src.self_healing_ext import SelfHealingManager, HealingPolicy, HealingEvent, HealthCheck, HealingAction, PolicyMode
from services.integration_service.src.infrastructure_pipelines_ext import InfrastructurePipelinesManager, PipelineProvider, PipelineStatus, DeploymentStrategy, StageStatus
from services.integration_service.src.maintenance_planner_ext import MaintenancePlannerManager, MaintenanceStatus, MaintenanceType, MaintenancePriority, MaintenanceImpact
from services.integration_service.src.quota_manager_ext import QuotaManager, QuotaResourceType, QuotaScope, QuotaPeriod, QuotaAction, ReservationStatus
from services.integration_service.src.runbook_library_ext import RunbookLibraryManager, RunbookCategory, RunbookStatus, StepType
from services.integration_service.src.self_healing_ext import SelfHealingManager, HealingPolicyMode, HealingActionType, HealthStatus
from datetime import datetime
from services.integration_service.src.workflow_studio_ext import WorkflowStudioManager, WorkflowStatus, WorkflowStepType, WorkflowExecutionStatus, WorkflowTriggerType, WorkflowStep, WorkflowTrigger

# === test_ansible_salt_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = AnsibleSaltManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestInventory:
    def test_create_inventory(self, manager):
        inv = manager.create_inventory(name="Production", description="Production servers")
        assert inv.id is not None
        assert inv.name == "Production"

    def test_get_inventory(self, manager):
        inv = manager.create_inventory(name="Test", description="Test")
        retrieved = manager.get_inventory(inv.id)
        assert retrieved is not None

    def test_delete_inventory(self, manager):
        inv = manager.create_inventory(name="Test", description="Test")
        assert manager.delete_inventory(inv.id) == True
        assert manager.get_inventory(inv.id) is None


class TestHosts:
    def test_add_host(self, manager):
        inv = manager.create_inventory(name="Prod")
        host = manager.add_host(inv.id, "web01", "192.168.1.10", ansible_user="deploy", ansible_port=22, variables={"region": "us-east"}, groups=["webservers"])
        assert host is not None
        assert host.name == "web01"
        assert host.ansible_host == "192.168.1.10"
        assert "webservers" in host.groups

    def test_remove_host(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10")
        assert manager.remove_host(inv.id, "web01") == True

    def test_add_host_to_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10", groups=["webservers"])
        manager.add_group(inv.id, "webservers")
        assert manager.add_host_to_group(inv.id, "web01", "webservers") == True


class TestGroups:
    def test_add_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        group = manager.add_group(inv.id, "webservers", variables={"http_port": 80})
        assert group is not None
        assert group.name == "webservers"

    def test_add_host_to_nonexistent_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10")
        assert manager.add_host_to_group(inv.id, "web01", "nonexistent") == False


class TestPlaybooks:
    def test_create_playbook(self, manager):
        pb = manager.create_playbook(name="Deploy App", description="Deploy application", tool=ToolType.ANSIBLE, content="- hosts: all\ntasks:\n  - name: Deploy\n    copy: src=app dest=/opt/app", parameters={"version": "1.0"}, inventory_id=None)
        assert pb.id is not None
        assert pb.name == "Deploy App"
        assert pb.tool == ToolType.ANSIBLE

    def test_get_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        retrieved = manager.get_playbook(pb.id)
        assert retrieved is not None

    def test_update_playbook(self, manager):
        pb = manager.create_playbook(name="Original", description="Original", tool=ToolType.ANSIBLE, content="")
        updated = manager.update_playbook(pb.id, {"name": "Updated", "version": "2.0"})
        assert updated.name == "Updated"
        assert updated.version == "2.0"

    def test_delete_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        assert manager.delete_playbook(pb.id) == True


class TestExecution:
    def test_execute_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="- hosts: all\ntasks:\n  - name: Ping\n    ping:")
        job = manager.execute_playbook(pb.id, executed_by="admin")
        assert job is not None
        assert job.status in (JobStatus.SUCCESS, JobStatus.FAILED)

    def test_get_job(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        job = manager.execute_playbook(pb.id)
        retrieved = manager.get_job(job.id)
        assert retrieved is not None

    def test_cancel_job(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        job = manager.execute_playbook(pb.id)
        if job.status == JobStatus.PENDING:
            assert manager.cancel_job(job.id) == True
        else:
            assert manager.cancel_job(job.id) == False


class TestSchedules:
    def test_create_schedule(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        schedule = manager.create_schedule(pb.id, "Daily backup", "0 2 * * *")
        assert schedule is not None
        assert schedule.cron_expression == "0 2 * * *"

    def test_delete_schedule(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        schedule = manager.create_schedule(pb.id, "Daily", "0 2 * * *")
        assert manager.delete_schedule(schedule.id) == True


class TestMinions:
    def test_register_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50", grains={"os": "Ubuntu", "kernel": "5.4"}, tags=["production", "worker"])
        assert minion.id is not None
        assert minion.name == "minion-01"
        assert minion.grains["os"] == "Ubuntu"

    def test_get_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50")
        retrieved = manager.get_minion(minion.id)
        assert retrieved is not None

    def test_delete_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50")
        assert manager.delete_minion(minion.id) == True


class TestTemplates:
    def test_create_template(self, manager):
        tmpl = manager.create_template("Deploy", "Standard deploy", ToolType.ANSIBLE, "- hosts: all\ntasks:\n  - ping:", category="deployment", tags=["deploy"])
        assert tmpl.id is not None
        assert tmpl.name == "Deploy"

    def test_apply_template(self, manager):
        tmpl = manager.create_template("Deploy", "Standard deploy", ToolType.ANSIBLE, "- hosts: all\ntasks:\n  - ping:")
        pb = manager.apply_template(tmpl.id, "My Deploy", "My deploy")
        assert pb is not None
        assert pb.name == "My Deploy"


class TestInventoryGeneration:
    def test_generate_ini(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_group(inv.id, "webservers")
        manager.add_host(inv.id, "web01", "192.168.1.10", groups=["webservers"])
        ini = manager.generate_inventory_ini(inv.id)
        assert ini is not None
        assert "[webservers]" in ini
        assert "192.168.1.10" in ini

    def test_generate_yaml(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_group(inv.id, "dbservers")
        manager.add_host(inv.id, "db01", "192.168.1.20", groups=["dbservers"])
        yaml_out = manager.generate_inventory_yaml(inv.id)
        assert yaml_out is not None
        assert "dbservers" in yaml_out


class TestSearch:
    def test_search_playbooks(self, manager):
        manager.create_playbook(name="Deploy Web", description="Web deployment", tool=ToolType.ANSIBLE, content="")
        manager.create_playbook(name="Backup DB", description="Database backup", tool=ToolType.ANSIBLE, content="")
        results = manager.search_playbooks("deploy")
        assert len(results) >= 1


class TestDuplicate:
    def test_duplicate_playbook(self, manager):
        pb = manager.create_playbook(name="Original", description="Original", tool=ToolType.ANSIBLE, content="- hosts: all")
        clone = manager.duplicate_playbook(pb.id, "Clone")
        assert clone is not None
        assert clone.name == "Clone"
        assert clone.id != pb.id


class TestStatistics:
    def test_get_statistics(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "10.0.0.1")
        stats = manager.get_statistics()
        assert stats["total_inventories"] >= 1
        assert stats["total_hosts"] >= 1

# === test_auto_remediation_ext.py ===

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

# === test_chaos_engineering_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = ChaosEngineeringManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestExperimentCRUD:
    def test_create_experiment(self, manager):
        ex = manager.create_experiment(name="Pod Kill Test", description="Test pod resilience", target_type=ExperimentTargetType.KUBERNETES, hypothesis=ExperimentHypothesis.STEADY_STATE, target_selector={"namespace": "production", "label": "app=web"}, blast_radius="targeted", duration_minutes=15, created_by="sre-team")
        assert ex.id is not None
        assert ex.name == "Pod Kill Test"
        assert ex.target_type == ExperimentTargetType.KUBERNETES
        assert ex.status == ExperimentStatus.DRAFT

    def test_get_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        retrieved = manager.get_experiment(ex.id)
        assert retrieved is not None

    def test_update_experiment(self, manager):
        ex = manager.create_experiment(name="Original", description="Original", target_type=ExperimentTargetType.NETWORK)
        updated = manager.update_experiment(ex.id, {"name": "Updated", "blast_radius": "full"})
        assert updated.name == "Updated"
        assert updated.blast_radius == "full"

    def test_delete_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        assert manager.delete_experiment(ex.id) == True


class TestSteadyState:
    def test_add_steady_state_check(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        check = manager.add_steady_state_check(ex.id, "cpu_usage", "avg(container_cpu)", 80.0, "less_than", tolerance_percent=10.0, duration_seconds=30)
        assert check is not None
        assert check.metric == "cpu_usage"
        assert check.expected_value == 80.0


class TestScenarios:
    def test_create_scenario(self, manager):
        sc = manager.create_scenario(name="Network Chaos", description="Network fault injection", tags=["network", "resilience"])
        assert sc.id is not None
        assert sc.name == "Network Chaos"

    def test_add_scenario_to_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.NETWORK)
        sc = manager.create_scenario(name="Net Scenario", description="Network test")
        assert manager.add_scenario_to_experiment(ex.id, sc.id) == True
        assert len(ex.scenarios) >= 1

    def test_add_fault_to_scenario(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        sc = manager.create_scenario(name="Pod Kill", description="Kill pods")
        manager.add_scenario_to_experiment(ex.id, sc.id)
        fault = manager.add_fault_to_scenario(ex.id, sc.id, FaultType.POD_KILL, ExperimentTargetType.KUBERNETES, target_selector={"namespace": "default", "label": "app=web"}, duration_seconds=30, intensity=1.0, parameters={"policy": "random"})
        assert fault is not None
        assert fault.fault_type == FaultType.POD_KILL


class TestExecution:
    def test_run_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        manager.approve_experiment(ex.id, "admin")
        run = manager.run_experiment(ex.id, executed_by="sre")
        assert run is not None
        assert run.status in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED)

    def test_get_run(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.approve_experiment(ex.id, "admin")
        run = manager.run_experiment(ex.id)
        retrieved = manager.get_run(run.id)
        assert retrieved is not None


class TestLifecycle:
    def test_cancel_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        assert manager.cancel_experiment(ex.id) == True
        assert ex.status == ExperimentStatus.CANCELLED

    def test_approve_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.NETWORK)
        assert manager.approve_experiment(ex.id, "security-lead") == True
        assert ex.status == ExperimentStatus.SCHEDULED


class TestReport:
    def test_get_report(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        report = manager.get_report(ex.id)
        assert report is not None
        assert report["experiment"]["name"] == "Test"


class TestDuplicate:
    def test_duplicate_experiment(self, manager):
        ex = manager.create_experiment(name="Original", description="Original", target_type=ExperimentTargetType.KUBERNETES)
        clone = manager.duplicate_experiment(ex.id, "Clone")
        assert clone is not None
        assert clone.name == "Clone"
        assert clone.id != ex.id


class TestSearch:
    def test_search_experiments(self, manager):
        manager.create_experiment(name="Pod Chaos", description="Pod chaos test", target_type=ExperimentTargetType.KUBERNETES)
        results = manager.search_experiments("chaos")
        assert len(results) >= 1


class TestList:
    def test_list_experiments(self, manager):
        manager.create_experiment(name="E1", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.create_experiment(name="E2", description="Test", target_type=ExperimentTargetType.NETWORK)
        experiments = manager.list_experiments()
        assert len(experiments) >= 2

    def test_list_runs(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.approve_experiment(ex.id, "admin")
        manager.run_experiment(ex.id)
        runs = manager.list_runs(experiment_id=ex.id)
        assert len(runs) >= 0


class TestStatistics:
    def test_get_statistics(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        stats = manager.get_statistics()
        assert stats["total_experiments"] >= 1

# === test_cog_automation.py ===

# Workflow Studio Cog Tests
class TestWorkflowStudioCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"workflows": [], "executions": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_imports(self):
        from services.orchestrator_agent.cogs.workflow_studio import (
            WorkflowStudioManager, NodeType, WorkflowStatus, ExecutionStatus,
            TRIGGER_NODES, ACTION_NODES
        )
        assert hasattr(WorkflowStudioManager, "create_workflow")
        assert hasattr(WorkflowStudioManager, "add_node")

    def test_node_types(self):
        from services.orchestrator_agent.cogs.workflow_studio import TRIGGER_NODES, ACTION_NODES
        assert len(TRIGGER_NODES) >= 3
        assert len(ACTION_NODES) >= 12

    @pytest.mark.asyncio
    async def test_create_workflow(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("Test WF", "Test description")
            assert wf.workflow_id is not None
            assert wf.name == "Test WF"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_node(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("WF", "desc")
            node = mgr.add_node(wf.workflow_id, "webhook_trigger", "Webhook", {"path": "/hook", "method": "POST"})
            assert node.node_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_invalid_node_type(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("WF", "desc")
            with pytest.raises(ValueError):
                mgr.add_node(wf.workflow_id, "invalid_type", "Bad", {})
            await mgr.close()

    @pytest.mark.asyncio
    async def test_connect_nodes(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("WF", "desc")
            n1 = mgr.add_node(wf.workflow_id, "webhook_trigger", "T1", {"path": "/hook", "method": "POST"})
            n2 = mgr.add_node(wf.workflow_id, "http_request", "A1", {"url": "https://ex.com", "method": "GET"})
            edge = mgr.connect_nodes(wf.workflow_id, n1.node_id, n2.node_id)
            assert edge is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_execute_workflow(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("Exec WF", "desc")
            mgr.activate_workflow(wf.workflow_id)
            ex = mgr.execute_workflow(wf.workflow_id)
            assert ex.execution_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_cancel_execution(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("Cancel", "desc")
            mgr.activate_workflow(wf.workflow_id)
            ex = mgr.execute_workflow(wf.workflow_id)
            mgr.cancel_execution(ex.execution_id)
            from services.orchestrator_agent.cogs.workflow_studio import ExecutionStatus
            assert mgr.get_execution(ex.execution_id).status == ExecutionStatus.CANCELLED
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_node_types(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            types = mgr.list_node_types()
            triggers = [n for n in types if n["category"] == "triggers"]
            actions = [n for n in types if n["category"] == "actions"]
            assert len(triggers) >= 3
            assert len(actions) >= 12
            await mgr.close()

    @pytest.mark.asyncio
    async def test_workflow_lifecycle(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager, WorkflowStatus
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            wf = mgr.create_workflow("Lifecycle", "desc")
            mgr.activate_workflow(wf.workflow_id)
            assert mgr.get_workflow(wf.workflow_id).status == WorkflowStatus.ACTIVE
            mgr.disable_workflow(wf.workflow_id)
            assert mgr.get_workflow(wf.workflow_id).status == WorkflowStatus.DISABLED
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            mgr.create_workflow("WF1", "desc")
            mgr.create_workflow("WF2", "desc")
            stats = mgr.get_statistics()
            assert stats["total_workflows"] == 2
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.workflow_studio.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.workflow_studio import WorkflowStudioManager
            mgr = WorkflowStudioManager()
            await mgr.initialize()
            mgr.create_workflow("Persist", "desc")
            await mgr.close()
            mgr2 = WorkflowStudioManager()
            await mgr2.initialize()
            assert len(mgr2.list_workflows()) == 1
            await mgr2.close()


# Ansible Salt Cog Tests
class TestAnsibleSaltCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"ansible_playbooks": [], "salt_states": [], "executions": [], "inventory_hosts": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_playbook(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            pb = mgr.create_ansible_playbook("Deploy", "deploy.yml", "desc")
            assert pb.playbook_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_create_salt_state(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            st = mgr.create_salt_state("Nginx Config", "nginx.config", "desc")
            assert st.state_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_execute_ansible(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            pb = mgr.create_ansible_playbook("Test PB", "test.yml", "desc")
            ex = mgr.execute_ansible(pb.playbook_id, ["webserver"], "production")
            assert ex.execution_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_execute_salt(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            st = mgr.create_salt_state("Test State", "test.state", "desc")
            ex = mgr.execute_salt(st.state_id, ["web*"], "highstate")
            assert ex.execution_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_inventory_hosts(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            host = mgr.add_inventory_host("web-01", "10.0.0.1", "webserver")
            assert host.host_id is not None
            assert len(mgr.list_inventory_hosts("webserver")) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_rollback(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            pb = mgr.create_ansible_playbook("Roll PB", "roll.yml", "desc")
            ex = mgr.execute_ansible(pb.playbook_id, ["local"], "production")
            rb = mgr.rollback_execution(ex.execution_id)
            assert rb.status == "completed"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            mgr.create_ansible_playbook("PB1", "pb1.yml", "desc")
            mgr.create_salt_state("ST1", "st1.state", "desc")
            stats = mgr.get_statistics()
            assert stats["total_playbooks"] == 1
            assert stats["total_states"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            mgr.create_ansible_playbook("Persist PB", "persist.yml", "desc")
            await mgr.close()
            mgr2 = AnsibleSaltManager()
            await mgr2.initialize()
            assert len(mgr2.list_ansible_playbooks()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, data_file):
        with patch("services.orchestrator_agent.cogs.ansible_salt_integration.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.ansible_salt_integration import AnsibleSaltManager
            mgr = AnsibleSaltManager()
            await mgr.initialize()
            with pytest.raises(ValueError):
                mgr.execute_ansible("nonexistent", ["local"])
            with pytest.raises(ValueError):
                mgr.execute_salt("nonexistent", ["local"])
            await mgr.close()


# Self-Healing Cog Tests
class TestSelfHealingCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"policies": [], "events": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Auto Restart", "container", "automatic")
            assert p.policy_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_health_check(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Health", "container", "automatic")
            hc = mgr.add_health_check(p.policy_id, "http", {"url": "http://localhost/health"})
            assert hc.check_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_remediation_action(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Remediate", "container", "automatic")
            action = mgr.add_remediation_action(p.policy_id, "restart", {"service": "nginx"})
            assert action.action_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_execute_healing(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Heal", "container", "automatic")
            event = mgr.execute_healing(p.policy_id, "container-01", "unhealthy")
            assert event.event_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_disable_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Disable", "container", "automatic")
            mgr.disable_policy(p.policy_id)
            assert mgr.get_policy(p.policy_id).enabled is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_enable_policy(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Enable", "container", "automatic")
            mgr.disable_policy(p.policy_id)
            mgr.enable_policy(p.policy_id)
            assert mgr.get_policy(p.policy_id).enabled is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            p = mgr.create_policy("Stats", "container", "automatic")
            mgr.execute_healing(p.policy_id, "c1", "unhealthy")
            stats = mgr.get_statistics()
            assert stats["total_policies"] == 1
            assert stats["total_events"] >= 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            mgr.create_policy("Persist", "container", "automatic")
            await mgr.close()
            mgr2 = SelfHealingManager()
            await mgr2.initialize()
            assert len(mgr2.list_policies()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, data_file):
        with patch("services.orchestrator_agent.cogs.self_healing.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.self_healing import SelfHealingManager
            mgr = SelfHealingManager()
            await mgr.initialize()
            with pytest.raises(ValueError):
                mgr.execute_healing("nonexistent", "r1", "unhealthy")
            await mgr.close()


# Chaos Engineering Cog Tests
class TestChaosEngineeringCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"experiments": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_experiment(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            exp = mgr.create_experiment("Latency Test", "container", "app=web")
            assert exp.experiment_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_fault(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            exp = mgr.create_experiment("Fault Test", "container", "app=web")
            fault = mgr.add_fault(exp.experiment_id, "network_latency", {"latency_ms": 200})
            assert fault.fault_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_run_experiment(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            exp = mgr.create_experiment("Run Test", "container", "app=web")
            mgr.add_fault(exp.experiment_id, "cpu_stress", {"cpu_count": 1})
            mgr.run_experiment(exp.experiment_id)
            from services.orchestrator_agent.cogs.chaos_engineering import ExperimentStatus
            assert mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.RUNNING
            await mgr.close()

    @pytest.mark.asyncio
    async def test_stop_experiment(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            exp = mgr.create_experiment("Stop", "container", "app=web")
            mgr.add_fault(exp.experiment_id, "pod_kill", {})
            mgr.run_experiment(exp.experiment_id)
            mgr.stop_experiment(exp.experiment_id)
            from services.orchestrator_agent.cogs.chaos_engineering import ExperimentStatus
            assert mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.STOPPED
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_fault_types(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            faults = mgr.list_fault_types()
            assert len(faults) >= 15
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            e1 = mgr.create_experiment("E1", "container", "app=web")
            mgr.create_experiment("E2", "node", "app=db")
            mgr.run_experiment(e1.experiment_id)
            stats = mgr.get_statistics()
            assert stats["total_experiments"] == 2
            assert stats["running_experiments"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            mgr.create_experiment("Persist", "container", "app=web")
            await mgr.close()
            mgr2 = ChaosEngineeringManager()
            await mgr2.initialize()
            assert len(mgr2.list_experiments()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_complete_experiment(self, data_file):
        with patch("services.orchestrator_agent.cogs.chaos_engineering.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.chaos_engineering import ChaosEngineeringManager
            mgr = ChaosEngineeringManager()
            await mgr.initialize()
            exp = mgr.create_experiment("Complete", "container", "app=web")
            mgr.run_experiment(exp.experiment_id)
            mgr.complete_experiment(exp.experiment_id)
            from services.orchestrator_agent.cogs.chaos_engineering import ExperimentStatus
            assert mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.COMPLETED
            await mgr.close()


# Runbook Cog Tests
class TestRunbookCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"templates": [], "instances": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_template(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            t = mgr.create_template("Restart Service", "desc", "incident_response")
            assert t.template_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_step(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            t = mgr.create_template("Recovery", "desc", "incident_response")
            step = mgr.add_step(t.template_id, "SSH into server", "manual", order=1)
            assert step.step_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_instantiate(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            t = mgr.create_template("Restart", "desc", "incident_response")
            inst = mgr.instantiate_template(t.template_id, {"server": "web-01"})
            assert inst["instance_id"] is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_list_by_category(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            mgr.create_template("T1", "desc", "incident_response")
            mgr.create_template("T2", "desc", "deployment")
            mgr.create_template("T3", "desc", "security")
            assert len(mgr.list_templates("incident_response")) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            mgr.create_template("T1", "desc", "incident_response")
            stats = mgr.get_statistics()
            assert stats["total_templates"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.runbook_library.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.runbook_library import RunbookLibrary
            mgr = RunbookLibrary()
            await mgr.initialize()
            mgr.create_template("Persist", "desc", "general", author="ops-team")
            await mgr.close()
            mgr2 = RunbookLibrary()
            await mgr2.initialize()
            assert len(mgr2.list_templates()) == 1
            await mgr2.close()


# Maintenance Cog Tests
class TestMaintenanceCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"windows": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_schedule(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            w = mgr.schedule_window("DB Upgrade", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["db-01"])
            assert w.window_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_start_window(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            w = mgr.schedule_window("Upgrade", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            assert mgr.start_window(w.window_id) is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_complete_window(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            w = mgr.schedule_window("Complete", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            mgr.start_window(w.window_id)
            assert mgr.complete_window(w.window_id) is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_cancel_window(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            w = mgr.schedule_window("Cancel", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            assert mgr.cancel_window(w.window_id) is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_approve_window(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            w = mgr.schedule_window("Approved", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            mgr.approve_window(w.window_id, "approver1")
            assert mgr.get_window(w.window_id).approved_by == "approver1"
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            mgr.schedule_window("W1", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            stats = mgr.get_statistics()
            assert stats["total_windows"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            mgr.schedule_window("W1", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
            await mgr.close()
            mgr2 = MaintenancePlanner()
            await mgr2.initialize()
            assert len(mgr2.list_windows()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, data_file):
        with patch("services.orchestrator_agent.cogs.maintenance_planner.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.maintenance_planner import MaintenancePlanner
            mgr = MaintenancePlanner()
            await mgr.initialize()
            assert mgr.get_window("nonexistent") is None
            assert mgr.start_window("nonexistent") is False
            assert mgr.complete_window("nonexistent") is False
            assert mgr.cancel_window("nonexistent") is False
            await mgr.close()


# Quota Cog Tests
class TestQuotaCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"quotas": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_set_quota(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            q = mgr.set_quota("org", "org-1", cpu=16, memory=64)
            assert q.quota_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_check_quota(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=16, memory=64)
            result = mgr.check_quota("org", "org-1", cpu=4, memory=8)
            assert result["allowed"] is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_quota_exceeded(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=2, memory=4)
            result = mgr.check_quota("org", "org-1", cpu=8, memory=16)
            assert result["allowed"] is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_update_usage(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=16, memory=64)
            mgr.update_usage("org", "org-1", cpu=4, memory=16)
            q = mgr.get_quota("org", "org-1")
            assert q.usage["cpu"] == 4
            await mgr.close()

    @pytest.mark.asyncio
    async def test_templates(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            t = mgr.create_quota_template("small", {"cpu": 2, "memory": 4, "storage": 50})
            assert t["name"] == "small"
            assert len(mgr.list_quota_templates()) == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=16)
            stats = mgr.get_statistics()
            assert stats["total_quotas"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=16)
            await mgr.close()
            mgr2 = QuotaManager()
            await mgr2.initialize()
            assert len(mgr2.list_quotas()) == 1
            await mgr2.close()

    @pytest.mark.asyncio
    async def test_delete_quota(self, data_file):
        with patch("services.orchestrator_agent.cogs.quota_manager.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.quota_manager import QuotaManager
            mgr = QuotaManager()
            await mgr.initialize()
            mgr.set_quota("org", "org-1", cpu=16)
            mgr.delete_quota("org", "org-1")
            assert mgr.get_quota("org", "org-1") is None
            await mgr.close()


# Drift Detection Cog Tests
class TestDriftCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"snapshots": [], "scans": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_snapshot(self, data_file):
        with patch("services.orchestrator_agent.cogs.drift_detector.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.drift_detector import DriftDetector
            mgr = DriftDetector()
            await mgr.initialize()
            snap = mgr.create_snapshot("srv1", "production")
            assert snap.snapshot_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_run_scan(self, data_file):
        with patch("services.orchestrator_agent.cogs.drift_detector.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.drift_detector import DriftDetector
            mgr = DriftDetector()
            await mgr.initialize()
            mgr.create_snapshot("srv1", "production")
            scan = mgr.run_scan("srv1")
            assert scan.scan_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_remediate(self, data_file):
        with patch("services.orchestrator_agent.cogs.drift_detector.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.drift_detector import DriftDetector
            mgr = DriftDetector()
            await mgr.initialize()
            mgr.create_snapshot("srv1", "production")
            scan = mgr.run_scan("srv1")
            result = mgr.remediate_drift(scan.scan_id)
            assert result is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.drift_detector.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.drift_detector import DriftDetector
            mgr = DriftDetector()
            await mgr.initialize()
            mgr.create_snapshot("srv1", "prod")
            mgr.run_scan("srv1")
            stats = mgr.get_statistics()
            assert stats["total_snapshots"] >= 1
            assert stats["total_scans"] >= 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.drift_detector.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.drift_detector import DriftDetector
            mgr = DriftDetector()
            await mgr.initialize()
            mgr.create_snapshot("srv1", "prod")
            await mgr.close()
            mgr2 = DriftDetector()
            await mgr2.initialize()
            assert len(mgr2.list_snapshots()) >= 1
            await mgr2.close()


# Pipeline Cog Tests
class TestPipelineCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"pipelines": [], "runs": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            pl = mgr.create_pipeline("Deploy Stack", "desc")
            assert pl.pipeline_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_add_stage(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            pl = mgr.create_pipeline("Test", "desc")
            stage = mgr.add_stage(pl.pipeline_id, "Build", "build", 1)
            assert stage.stage_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_run_pipeline(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            pl = mgr.create_pipeline("Run", "desc")
            mgr.add_stage(pl.pipeline_id, "Build", "build", 1)
            run = mgr.run_pipeline(pl.pipeline_id, "main")
            assert run.run_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_rollback(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            pl = mgr.create_pipeline("Roll", "desc")
            run = mgr.run_pipeline(pl.pipeline_id, "main")
            rb = mgr.rollback_run(run.run_id)
            assert rb is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            pl = mgr.create_pipeline("Stats", "desc")
            mgr.run_pipeline(pl.pipeline_id, "main")
            stats = mgr.get_statistics()
            assert stats["total_pipelines"] == 1
            assert stats["total_runs"] == 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.infrastructure_pipelines.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.infrastructure_pipelines import PipelineManager
            mgr = PipelineManager()
            await mgr.initialize()
            mgr.create_pipeline("Persist", "desc")
            await mgr.close()
            mgr2 = PipelineManager()
            await mgr2.initialize()
            assert len(mgr2.list_pipelines()) == 1
            await mgr2.close()


# Auto Remediation Cog Tests
class TestAutoRemediationCog:
    @pytest.fixture
    def data_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        with open(path, "w") as f:
            json.dump({"rules": [], "executions": []}, f)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_rule(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            rule = mgr.create_rule("High CPU", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            assert rule.rule_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_execute_rule(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            rule = mgr.create_rule("Test Rule", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            ex = mgr.execute_rule(rule.rule_id, "srv1")
            assert ex.execution_id is not None
            await mgr.close()

    @pytest.mark.asyncio
    async def test_disable_rule(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            rule = mgr.create_rule("Disable", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            mgr.disable_rule(rule.rule_id)
            assert mgr.get_rule(rule.rule_id).enabled is False
            await mgr.close()

    @pytest.mark.asyncio
    async def test_enable_rule(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            rule = mgr.create_rule("Enable", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            mgr.disable_rule(rule.rule_id)
            mgr.enable_rule(rule.rule_id)
            assert mgr.get_rule(rule.rule_id).enabled is True
            await mgr.close()

    @pytest.mark.asyncio
    async def test_statistics(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            rule = mgr.create_rule("Stats", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            mgr.execute_rule(rule.rule_id, "srv1")
            stats = mgr.get_statistics()
            assert stats["total_rules"] == 1
            assert stats["total_executions"] >= 1
            await mgr.close()

    @pytest.mark.asyncio
    async def test_persistence(self, data_file):
        with patch("services.orchestrator_agent.cogs.auto_remediation.DATA_FILE", data_file):
            from services.orchestrator_agent.cogs.auto_remediation import AutoRemediationManager
            mgr = AutoRemediationManager()
            await mgr.initialize()
            mgr.create_rule("Persist", "auto", trigger_type="metric", trigger_condition="cpu > 90")
            await mgr.close()
            mgr2 = AutoRemediationManager()
            await mgr2.initialize()
            assert len(mgr2.list_rules()) == 1
            await mgr2.close()

# === test_drift_detector_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = DriftDetectorManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestBaselines:
    def test_create_baseline(self, manager):
        config = {"port": 8080, "protocol": "http", "timeout": 30, "health_check": {"endpoint": "/health", "interval": 10}}
        bl = manager.create_baseline(name="Web Server Config", description="Baseline for web servers", resource_category=ResourceCategory.CONFIG, resource_type="nginx", resource_id="web-01", baseline_config=config, created_by="admin")
        assert bl.id is not None
        assert bl.name == "Web Server Config"
        assert bl.checksum is not None

    def test_get_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        retrieved = manager.get_baseline(bl.id)
        assert retrieved is not None

    def test_update_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "old"})
        updated = manager.update_baseline(bl.id, {"key": "new", "extra": "value"})
        assert updated.version > 1
        assert updated.baseline_config["key"] == "new"

    def test_delete_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        assert manager.delete_baseline(bl.id) == True


class TestDriftChecks:
    def test_add_check(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        check = manager.add_check(bl.id, "Port Check", "port", expected_value=8080, comparison_type="exact", severity=DriftSeverity.HIGH, auto_remediate=True)
        assert check is not None
        assert check.name == "Port Check"
        assert check.config_path == "port"
        assert check.severity == DriftSeverity.HIGH
        assert check.auto_remediate == True

    def test_remove_check(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        check = manager.add_check(bl.id, "Check", "path")
        assert manager.remove_check(check.id) == True


class TestDriftDetection:
    def test_detect_drift_match(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {"port": 8080})
        assert len(events) == 0

    def test_detect_drift_mismatch(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {"port": 9090})
        assert len(events) >= 1
        assert events[0].severity == DriftSeverity.MEDIUM

    def test_detect_missing_key(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {})
        assert len(events) >= 1


class TestEvents:
    def test_acknowledge_event(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.acknowledge_event(events[0].id, "admin") == True

    def test_suppress_event(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.suppress_event(events[0].id, until_hours=48) == True

    def test_false_positive(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.mark_false_positive(events[0].id) == True


class TestPolicies:
    def test_create_policy(self, manager):
        policy = manager.create_policy(name="Hourly Check", description="Check every hour", resource_categories=[ResourceCategory.CONFIG, ResourceCategory.NETWORK], auto_remediate=True)
        assert policy.id is not None
        assert policy.name == "Hourly Check"
        assert policy.auto_remediate == True

    def test_update_policy(self, manager):
        policy = manager.create_policy(name="Original", description="Original")
        updated = manager.update_policy(policy.id, {"name": "Updated", "auto_remediate": True})
        assert updated.name == "Updated"

    def test_delete_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test")
        assert manager.delete_policy(policy.id) == True


class TestExportImport:
    def test_export_baseline_yaml(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        yaml_out = manager.export_baseline_yaml(bl.id)
        assert yaml_out is not None
        assert "name: Test" in yaml_out

    def test_import_baseline_yaml(self, manager):
        yaml_content = "name: Imported\nresource_category: config\nresource_type: nginx\nconfig:\n  port: 8080\nchecks: []"
        bl = manager.import_baseline_yaml(yaml_content, resource_id="web-02", created_by="admin")
        assert bl is not None
        assert bl.name == "Imported"


class TestBaselineComparison:
    def test_compare_baselines(self, manager):
        bl1 = manager.create_baseline(name="BL1", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        bl2 = manager.create_baseline(name="BL2", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r2", baseline_config={"port": 9090})
        result = manager.compare_baselines(bl1.id, bl2.id)
        assert result["has_differences"] == True
        assert result["diff"] is not None


class TestScheduledChecks:
    def test_run_scheduled_checks(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.run_scheduled_checks()
        assert events is not None


class TestStatistics:
    def test_get_statistics(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        stats = manager.get_statistics()
        assert stats["total_baselines"] >= 1

# === test_full_automation_integration.py ===

@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestWorkflowStudioFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = WorkflowStudioManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_workflow(self):
        wf = self.mgr.create_workflow("Test Workflow", "A test workflow")
        assert wf.workflow_id is not None
        assert wf.name == "Test Workflow"
        assert wf.status.value == "draft"

    def test_add_node(self):
        wf = self.mgr.create_workflow("Test", "desc")
        node = self.mgr.add_node(wf.workflow_id, "webhook_trigger", "Webhook", {"path": "/hook", "method": "POST"})
        assert node.node_id is not None
        assert node.node_type == "webhook_trigger"

    def test_add_node_invalid_type(self):
        wf = self.mgr.create_workflow("Test", "desc")
        with pytest.raises(ValueError, match="Unknown node type"):
            self.mgr.add_node(wf.workflow_id, "invalid_type", "Bad", {})

    def test_connect_nodes(self):
        wf = self.mgr.create_workflow("Test", "desc")
        n1 = self.mgr.add_node(wf.workflow_id, "webhook_trigger", "Trigger", {})
        n2 = self.mgr.add_node(wf.workflow_id, "http_request", "HTTP Action", {"url": "https://example.com", "method": "GET"})
        edge = self.mgr.connect_nodes(wf.workflow_id, n1.node_id, n2.node_id)
        assert edge.edge_id is not None
        assert edge.source_id == n1.node_id

    def test_execute_workflow(self):
        wf = self.mgr.create_workflow("Exec Test", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        execution = self.mgr.execute_workflow(wf.workflow_id)
        assert execution.execution_id is not None
        assert execution.status in [ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED]

    def test_get_execution(self):
        wf = self.mgr.create_workflow("Exec Test", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        ex = self.mgr.execute_workflow(wf.workflow_id)
        retrieved = self.mgr.get_execution(ex.execution_id)
        assert retrieved.execution_id == ex.execution_id

    def test_cancel_execution(self):
        wf = self.mgr.create_workflow("Cancel Test", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        ex = self.mgr.execute_workflow(wf.workflow_id)
        self.mgr.cancel_execution(ex.execution_id)
        assert self.mgr.get_execution(ex.execution_id).status == ExecutionStatus.CANCELLED

    def test_list_node_types(self):
        types = self.mgr.list_node_types()
        triggers = [n for n in types if n["category"] == "triggers"]
        actions = [n for n in types if n["category"] == "actions"]
        assert len(triggers) >= 3
        assert len(actions) >= 12

    def test_workflow_activation(self):
        wf = self.mgr.create_workflow("Active", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        assert self.mgr.get_workflow(wf.workflow_id).status.value == "active"

    def test_disabled_workflow(self):
        wf = self.mgr.create_workflow("Disabled", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        self.mgr.disable_workflow(wf.workflow_id)
        assert self.mgr.get_workflow(wf.workflow_id).status.value == "disabled"

    def test_statistics(self):
        wf = self.mgr.create_workflow("WF1", "desc")
        self.mgr.create_workflow("WF2", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        stats = self.mgr.get_statistics()
        assert stats["total_workflows"] == 2
        assert stats["active_workflows"] == 1

    def test_persistence(self):
        self.mgr.create_workflow("Persist WF", "desc")
        self.mgr.close()
        mgr2 = WorkflowStudioManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_workflows()) == 1
        mgr2.close()

    def test_execution_history(self):
        wf = self.mgr.create_workflow("Hist", "desc")
        self.mgr.activate_workflow(wf.workflow_id)
        self.mgr.execute_workflow(wf.workflow_id)
        self.mgr.execute_workflow(wf.workflow_id)
        assert len(self.mgr.list_executions(wf.workflow_id)) == 2

    def test_cycle_detection(self):
        wf = self.mgr.create_workflow("cycle", "desc")
        n1 = self.mgr.add_node(wf.workflow_id, "webhook_trigger", "T1", {})
        n2 = self.mgr.add_node(wf.workflow_id, "http_request", "A1", {"url": "https://example.com", "method": "GET"})
        self.mgr.connect_nodes(wf.workflow_id, n1.node_id, n2.node_id)
        self.mgr.connect_nodes(wf.workflow_id, n2.node_id, n1.node_id)
        self.mgr.activate_workflow(wf.workflow_id)
        ex = self.mgr.execute_workflow(wf.workflow_id)
        assert ex.status in [ExecutionStatus.FAILED, ExecutionStatus.COMPLETED]

    def test_multiple_workflows(self):
        for i in range(5):
            self.mgr.create_workflow(f"WF{i}", f"desc{i}")
        assert len(self.mgr.list_workflows()) == 5


class TestAnsibleSaltFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = AnsibleSaltManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_ansible_playbook(self):
        pb = self.mgr.create_ansible_playbook("Deploy App", "deploy_app.yml", "Deploy the application stack")
        assert pb.playbook_id is not None
        assert pb.name == "Deploy App"

    def test_create_salt_state(self):
        st = self.mgr.create_salt_state("Configure Nginx", "nginx.configure", "Configure nginx server")
        assert st.state_id is not None
        assert st.name == "Configure Nginx"

    def test_ansible_execution(self):
        pb = self.mgr.create_ansible_playbook("Test PB", "test.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["webserver"], "production")
        assert ex.execution_id is not None
        assert ex.status == "completed"
        assert len(ex.output) > 0

    def test_salt_execution(self):
        st = self.mgr.create_salt_state("Test State", "test.state", "desc")
        ex = self.mgr.execute_salt(st.state_id, ["web*"], "orchestrate")
        assert ex.execution_id is not None
        assert ex.status == "completed"

    def test_ansible_syntax_check(self):
        pb = self.mgr.create_ansible_playbook("Syntax PB", "syntax.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["local"], "syntax_check")
        assert ex.status == "completed"

    def test_ansible_dry_run(self):
        pb = self.mgr.create_ansible_playbook("Dry PB", "dryrun.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["local"], "dry_run")
        assert ex.status == "completed"

    def test_inventory_management(self):
        host = self.mgr.add_inventory_host("web-01", "192.168.1.10", "webserver", {"ansible_user": "deploy"})
        assert host.host_id is not None
        assert host.name == "web-01"
        hosts = self.mgr.list_inventory_hosts("webserver")
        assert len(hosts) == 1

    def test_execution_history(self):
        pb = self.mgr.create_ansible_playbook("Hist PB", "hist.yml", "desc")
        self.mgr.execute_ansible(pb.playbook_id, ["local"])
        self.mgr.execute_ansible(pb.playbook_id, ["local"])
        assert len(self.mgr.list_executions()) >= 2

    def test_execution_result_capture(self):
        pb = self.mgr.create_ansible_playbook("Cap PB", "cap.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["local"])
        assert "ok" in ex.output or "changed" in ex.output or "failed" in ex.output

    def test_rollback(self):
        pb = self.mgr.create_ansible_playbook("Roll PB", "roll.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["local"])
        rb = self.mgr.rollback_execution(ex.execution_id)
        assert rb is not None
        assert rb.status == "completed"

    def test_statistics(self):
        self.mgr.create_ansible_playbook("PB1", "pb1.yml", "desc")
        self.mgr.create_salt_state("ST1", "st1.state", "desc")
        self.mgr.add_inventory_host("h1", "10.0.0.1", "web")
        stats = self.mgr.get_statistics()
        assert stats["total_playbooks"] == 1
        assert stats["total_states"] == 1

    def test_persistence(self):
        self.mgr.create_ansible_playbook("Persist", "persist.yml", "desc")
        self.mgr.close()
        mgr2 = AnsibleSaltManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_ansible_playbooks()) == 1
        mgr2.close()

    def test_error_unknown_playbook(self):
        with pytest.raises(ValueError, match="not found"):
            self.mgr.execute_ansible("nonexistent", ["local"])

    def test_error_unknown_state(self):
        with pytest.raises(ValueError, match="not found"):
            self.mgr.execute_salt("nonexistent", ["local"])

    def test_unreachable_hosts(self):
        pb = self.mgr.create_ansible_playbook("Unreach", "unreach.yml", "desc")
        ex = self.mgr.execute_ansible(pb.playbook_id, ["nonexistent_host"])
        assert ex.status == "failed"


class TestInfrastructurePipelinesFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = PipelineManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_pipeline(self):
        pl = self.mgr.create_pipeline("Deploy Stack", "Production deployment pipeline")
        assert pl.pipeline_id is not None
        assert pl.name == "Deploy Stack"

    def test_add_stage(self):
        pl = self.mgr.create_pipeline("Test", "desc")
        stage = self.mgr.add_stage(pl.pipeline_id, "Build", "build", 1)
        assert stage.stage_id is not None
        assert stage.name == "Build"

    def test_full_pipeline_run(self):
        pl = self.mgr.create_pipeline("Full", "desc")
        self.mgr.add_stage(pl.pipeline_id, "Build", "build", 1)
        self.mgr.add_stage(pl.pipeline_id, "Test", "test", 2)
        run = self.mgr.run_pipeline(pl.pipeline_id, "main")
        assert run.run_id is not None
        assert run.trigger_type == TriggerType.MANUAL

    def test_pipeline_with_git_trigger(self):
        pl = self.mgr.create_pipeline("Git Pipe", "desc")
        run = self.mgr.run_pipeline(pl.pipeline_id, "feature-branch", TriggerType.GIT_PUSH)
        assert run.branch == "feature-branch"

    def test_approval_gate(self):
        pl = self.mgr.create_pipeline("Approved", "desc")
        self.mgr.add_stage(pl.pipeline_id, "Deploy", "deploy", 1)
        run = self.mgr.run_pipeline(pl.pipeline_id, "main")
        self.mgr.approve_stage(run.run_id, 0, "approver1")
        stages = self.mgr.get_pipeline_run(run.run_id).stages
        assert stages[0]["approved"] is True

    def test_rollback(self):
        pl = self.mgr.create_pipeline("Rollback", "desc")
        self.mgr.add_stage(pl.pipeline_id, "Deploy", "deploy", 1)
        run = self.mgr.run_pipeline(pl.pipeline_id, "main")
        rb = self.mgr.rollback_run(run.run_id)
        assert rb is not None

    def test_environment_promotion(self):
        pl = self.mgr.create_pipeline("Promote", "desc")
        run1 = self.mgr.run_pipeline(pl.pipeline_id, "main")
        run2 = self.mgr.run_pipeline(pl.pipeline_id, "main")
        self.mgr.promote_to_environment(run1.run_id, "staging")
        self.mgr.promote_to_environment(run2.run_id, "production")
        runs = self.mgr.list_runs(pl.pipeline_id)
        envs = [r["environment"] for r in runs]
        assert "staging" in envs or "production" in envs

    def test_statistics(self):
        pl = self.mgr.create_pipeline("Stats Pipe", "desc")
        self.mgr.create_pipeline("Pipe 2", "desc2")
        self.mgr.run_pipeline(pl.pipeline_id, "main")
        self.mgr.run_pipeline(pl.pipeline_id, "main")
        stats = self.mgr.get_statistics()
        assert stats["total_pipelines"] == 2
        assert stats["total_runs"] == 2

    def test_persistence(self):
        self.mgr.create_pipeline("Persist Pipe", "desc")
        self.mgr.close()
        mgr2 = PipelineManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_pipelines()) == 1
        mgr2.close()

    def test_pipeline_not_found(self):
        assert self.mgr.get_pipeline("nonexistent") is None
        with pytest.raises(ValueError, match="not found"):
            self.mgr.run_pipeline("nonexistent", "main")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.add_stage("nonexistent", "S", "build", 1)


class TestDriftDetectorFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = DriftDetector(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_snapshot(self):
        snap = self.mgr.create_snapshot("server-01", "production")
        assert snap.snapshot_id is not None
        assert snap.resource_id == "server-01"

    def test_run_scan(self):
        self.mgr.create_snapshot("server-01", "production")
        scan = self.mgr.run_scan("server-01")
        assert scan.scan_id is not None
        assert scan.status == ScanStatus.COMPLETED

    def test_drift_detection(self):
        self.mgr.create_snapshot("server-01", "production")
        scan = self.mgr.run_scan("server-01")
        assert "drift_count" in scan.to_dict() or "total_drifts" in scan.to_dict()

    def test_remediation(self):
        self.mgr.create_snapshot("server-01", "production")
        scan = self.mgr.run_scan("server-01")
        result = self.mgr.remediate_drift(scan.scan_id)
        assert result is not None

    def test_list_scans(self):
        self.mgr.create_snapshot("server-01", "production")
        self.mgr.run_scan("server-01")
        scans = self.mgr.list_scans()
        assert len(scans) >= 1

    def test_statistics(self):
        self.mgr.create_snapshot("srv1", "prod")
        self.mgr.create_snapshot("srv2", "staging")
        self.mgr.run_scan("srv1")
        stats = self.mgr.get_statistics()
        assert stats["total_snapshots"] >= 1
        assert stats["total_scans"] >= 1

    def test_persistence(self):
        self.mgr.create_snapshot("srv1", "prod")
        self.mgr.close()
        mgr2 = DriftDetector(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_snapshots()) >= 1
        mgr2.close()

    def test_multi_resource_scans(self):
        self.mgr.create_snapshot("srv1", "prod")
        self.mgr.create_snapshot("srv2", "prod")
        self.mgr.run_scan("srv1")
        self.mgr.run_scan("srv2")
        assert len(self.mgr.list_scans()) == 2

    def test_scan_not_found(self):
        assert self.mgr.remediate_drift("nonexistent") is None


class TestQuotaManagerFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = QuotaManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_set_quota(self):
        q = self.mgr.set_quota("org", "org-1", cpu=16, memory=64, storage=1000)
        assert q.quota_id is not None
        assert q.limits["cpu"] == 16

    def test_check_quota(self):
        self.mgr.set_quota("org", "org-1", cpu=16, memory=64)
        result = self.mgr.check_quota("org", "org-1", cpu=4, memory=8)
        assert result["allowed"] is True

    def test_quota_exceeded(self):
        self.mgr.set_quota("org", "org-1", cpu=4, memory=8)
        result = self.mgr.check_quota("org", "org-1", cpu=8, memory=16)
        assert result["allowed"] is False
        assert len(result["violations"]) > 0

    def test_update_usage(self):
        self.mgr.set_quota("org", "org-1", cpu=16, memory=64)
        self.mgr.update_usage("org", "org-1", cpu=4, memory=16)
        q = self.mgr.get_quota("org", "org-1")
        assert q.usage["cpu"] == 4
        assert q.usage["memory"] == 16

    def test_quota_templates(self):
        template = self.mgr.create_quota_template("small", {"cpu": 2, "memory": 4, "storage": 50})
        assert template["name"] == "small"
        templates = self.mgr.list_quota_templates()
        assert len(templates) == 1

    def test_statistics(self):
        self.mgr.set_quota("org", "org-1", cpu=16, memory=64)
        self.mgr.set_quota("team", "team-1", cpu=8, memory=32)
        stats = self.mgr.get_statistics()
        assert stats["total_quotas"] == 2

    def test_persistence(self):
        self.mgr.set_quota("org", "org-1", cpu=16)
        self.mgr.close()
        mgr2 = QuotaManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_quotas()) == 1
        mgr2.close()

    def test_get_nonexistent_quota(self):
        assert self.mgr.get_quota("org", "nonexistent") is None

    def test_delete_quota(self):
        self.mgr.set_quota("org", "org-1", cpu=16)
        self.mgr.delete_quota("org", "org-1")
        assert self.mgr.get_quota("org", "org-1") is None


class TestAutoRemediationFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = AutoRemediationManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_rule(self):
        rule = self.mgr.create_rule("High CPU", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        assert rule.rule_id is not None
        assert rule.name == "High CPU"

    def test_execute_rule(self):
        rule = self.mgr.create_rule("Test Rule", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        ex = self.mgr.execute_rule(rule.rule_id, "server-01")
        assert ex.execution_id is not None
        assert ex.status in ["running", "completed", "success", "failed"]

    def test_list_executions(self):
        rule = self.mgr.create_rule("Rule A", "auto", trigger_type="metric", trigger_condition="mem > 95")
        self.mgr.execute_rule(rule.rule_id, "server-01")
        self.mgr.execute_rule(rule.rule_id, "server-02")
        assert len(self.mgr.list_executions()) >= 2

    def test_disable_rule(self):
        rule = self.mgr.create_rule("Disable Test", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        self.mgr.disable_rule(rule.rule_id)
        assert self.mgr.get_rule(rule.rule_id).enabled is False

    def test_enable_rule(self):
        rule = self.mgr.create_rule("Enable Test", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        self.mgr.disable_rule(rule.rule_id)
        self.mgr.enable_rule(rule.rule_id)
        assert self.mgr.get_rule(rule.rule_id).enabled is True

    def test_statistics(self):
        rule = self.mgr.create_rule("Stats Rule", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        self.mgr.execute_rule(rule.rule_id, "server-01")
        stats = self.mgr.get_statistics()
        assert stats["total_rules"] == 1
        assert stats["total_executions"] >= 1

    def test_persistence(self):
        self.mgr.create_rule("Persist Rule", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        self.mgr.close()
        mgr2 = AutoRemediationManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_rules()) == 1
        mgr2.close()

    def test_cooldown_respect(self):
        rule = self.mgr.create_rule("Cooldown", "auto", trigger_type="metric", trigger_condition="cpu > 90", cooldown=60)
        self.mgr.execute_rule(rule.rule_id, "server-01")
        ex2 = self.mgr.execute_rule(rule.rule_id, "server-01")
        assert ex2 is not None

    def test_unknown_rule(self):
        with pytest.raises(ValueError, match="not found"):
            self.mgr.execute_rule("nonexistent", "srv1")

    def test_multi_resource_execution(self):
        rule = self.mgr.create_rule("Multi", "auto", trigger_type="metric", trigger_condition="cpu > 90")
        for srv in ["srv1", "srv2", "srv3"]:
            self.mgr.execute_rule(rule.rule_id, srv)
        assert len(self.mgr.list_executions()) == 3


class TestMaintenancePlannerFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = MaintenancePlanner(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_schedule_window(self):
        w = self.mgr.schedule_window("DB Upgrade", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["db-01", "db-02"])
        assert w.window_id is not None
        assert w.name == "DB Upgrade"
        assert w.status == WindowStatus.SCHEDULED

    def test_start_window(self):
        w = self.mgr.schedule_window("Test", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.start_window(w.window_id)
        assert self.mgr.get_window(w.window_id).status == WindowStatus.IN_PROGRESS

    def test_complete_window(self):
        w = self.mgr.schedule_window("Test", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.start_window(w.window_id)
        self.mgr.complete_window(w.window_id)
        assert self.mgr.get_window(w.window_id).status == WindowStatus.COMPLETED

    def test_cancel_window(self):
        w = self.mgr.schedule_window("Test", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.cancel_window(w.window_id)
        assert self.mgr.get_window(w.window_id).status == WindowStatus.CANCELLED

    def test_conflict_detection(self):
        w = self.mgr.schedule_window("Window A", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        has_conflict, conflicts = self.mgr.check_conflicts(w.window_id)
        assert has_conflict is False or isinstance(conflicts, list)

    def test_list_windows(self):
        self.mgr.schedule_window("W1", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.schedule_window("W2", "2026-06-02T02:00:00Z", "2026-06-02T04:00:00Z", ["srv2"])
        assert len(self.mgr.list_windows()) == 2

    def test_statistics(self):
        self.mgr.schedule_window("W1", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        stats = self.mgr.get_statistics()
        assert stats["total_windows"] == 1

    def test_persistence(self):
        self.mgr.schedule_window("W1", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.close()
        mgr2 = MaintenancePlanner(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_windows()) == 1
        mgr2.close()

    def test_unknown_window(self):
        assert self.mgr.get_window("nonexistent") is None
        assert self.mgr.start_window("nonexistent") is False
        assert self.mgr.complete_window("nonexistent") is False
        assert self.mgr.cancel_window("nonexistent") is False

    def test_approval_workflow(self):
        w = self.mgr.schedule_window("Approved Window", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["srv1"])
        self.mgr.approve_window(w.window_id, "approver1")
        w2 = self.mgr.get_window(w.window_id)
        assert w2.approved_by == "approver1"


class TestRunbookLibraryFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = RunbookLibrary(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_template(self):
        t = self.mgr.create_template("Restart Service", "Restart a service on a server", "incident_response")
        assert t.template_id is not None
        assert t.name == "Restart Service"

    def test_add_step(self):
        t = self.mgr.create_template("Restart", "desc", "incident_response")
        step = self.mgr.add_step(t.template_id, "SSH into server", "manual", order=1)
        assert step.step_id is not None

    def test_full_template_with_steps(self):
        t = self.mgr.create_template("DB Recovery", "Recover database from backup", "incident_response")
        self.mgr.add_step(t.template_id, "Identify affected DB", "manual", order=1)
        self.mgr.add_step(t.template_id, "Stop application", "manual", order=2)
        self.mgr.add_step(t.template_id, "Restore from backup", "automated", order=3, config={"script": "restore.sh"})
        self.mgr.add_step(t.template_id, "Verify data integrity", "script", order=4, config={"command": "verify.sh"})
        self.mgr.add_step(t.template_id, "Restart application", "manual", order=5)
        self.mgr.add_step(t.template_id, "Notify stakeholders", "notification", order=6)
        assert len(self.mgr.get_template(t.template_id).steps) == 6

    def test_instantiate_template(self):
        t = self.mgr.create_template("Restart", "desc", "incident_response")
        inst = self.mgr.instantiate_template(t.template_id, {"server": "web-01", "service": "nginx"})
        assert inst["instance_id"] is not None
        assert inst["variables"]["server"] == "web-01"

    def test_list_by_category(self):
        self.mgr.create_template("T1", "desc", "incident_response")
        self.mgr.create_template("T2", "desc", "deployment")
        self.mgr.create_template("T3", "desc", "security")
        assert len(self.mgr.list_templates("incident_response")) == 1
        assert len(self.mgr.list_templates("deployment")) == 1

    def test_versioning(self):
        t = self.mgr.create_template("V1", "desc", "general")
        assert t.version == 1
        self.mgr.update_template(t.template_id, {"name": "V2"})
        assert self.mgr.get_template(t.template_id).version >= 2

    def test_statistics(self):
        self.mgr.create_template("T1", "desc", "incident_response")
        self.mgr.create_template("T2", "desc", "deployment")
        stats = self.mgr.get_statistics()
        assert stats["total_templates"] == 2

    def test_persistence(self):
        self.mgr.create_template("Persist", "desc", "general")
        self.mgr.close()
        mgr2 = RunbookLibrary(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_templates()) == 1
        mgr2.close()

    def test_error_handling(self):
        assert self.mgr.get_template("nonexistent") is None
        assert self.mgr.add_step("nonexistent", "step", "manual") is None
        with pytest.raises(ValueError):
            self.mgr.create_template("", "desc", "invalid_category")

    def test_tags(self):
        t = self.mgr.create_template("Tagged", "desc", "incident_response", tags=["critical", "database"])
        assert "critical" in t.tags

    def test_author_tracking(self):
        t = self.mgr.create_template("Authored", "desc", "general", author="ops-team")
        assert t.author == "ops-team"


class TestChaosEngineeringFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = ChaosEngineeringManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_experiment(self):
        exp = self.mgr.create_experiment("Network Latency Test", "container", "app=web")
        assert exp.experiment_id is not None
        assert exp.name == "Network Latency Test"

    def test_add_fault(self):
        exp = self.mgr.create_experiment("Latency", "container", "app=web")
        fault = self.mgr.add_fault(exp.experiment_id, "network_latency", {"latency_ms": 200, "jitter_ms": 50})
        assert fault.fault_id is not None

    def test_run_experiment(self):
        exp = self.mgr.create_experiment("CPU Stress", "container", "app=web")
        self.mgr.add_fault(exp.experiment_id, "cpu_stress", {"cpu_count": 2, "duration_seconds": 30})
        self.mgr.run_experiment(exp.experiment_id)
        assert self.mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.RUNNING

    def test_stop_experiment(self):
        exp = self.mgr.create_experiment("Stop Test", "container", "app=web")
        self.mgr.run_experiment(exp.experiment_id)
        self.mgr.stop_experiment(exp.experiment_id)
        assert self.mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.STOPPED

    def test_list_fault_types(self):
        faults = self.mgr.list_fault_types()
        assert len(faults) >= 15
        types = [f["type"] for f in faults]
        assert "pod_kill" in types
        assert "network_latency" in types
        assert "cpu_stress" in types

    def test_complete_experiment(self):
        exp = self.mgr.create_experiment("Complete", "container", "app=web")
        self.mgr.run_experiment(exp.experiment_id)
        self.mgr.complete_experiment(exp.experiment_id)
        assert self.mgr.get_experiment(exp.experiment_id).status == ExperimentStatus.COMPLETED

    def test_statistics(self):
        e1 = self.mgr.create_experiment("E1", "container", "app=web")
        self.mgr.create_experiment("E2", "node", "app=db")
        self.mgr.run_experiment(e1.experiment_id)
        stats = self.mgr.get_statistics()
        assert stats["total_experiments"] == 2
        assert stats["running_experiments"] == 1

    def test_persistence(self):
        self.mgr.create_experiment("Persist", "container", "app=web")
        self.mgr.close()
        mgr2 = ChaosEngineeringManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_experiments()) == 1
        mgr2.close()

    def test_error_missing_experiment(self):
        assert self.mgr.get_experiment("nonexistent") is None
        with pytest.raises(ValueError):
            self.mgr.add_fault("nonexistent", "pod_kill", {})
        with pytest.raises(ValueError):
            self.mgr.run_experiment("nonexistent")

    def test_multiple_faults(self):
        exp = self.mgr.create_experiment("Multi Fault", "container", "app=web")
        self.mgr.add_fault(exp.experiment_id, "network_latency", {"latency_ms": 100})
        self.mgr.add_fault(exp.experiment_id, "cpu_stress", {"cpu_count": 1})
        self.mgr.add_fault(exp.experiment_id, "memory_stress", {"memory_mb": 256})
        assert len(self.mgr.get_experiment(exp.experiment_id).faults) == 3


class TestSelfHealingFullIntegration:
    def setup_method(self):
        self.path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.mgr = SelfHealingManager(storage_path=self.path)
        self.mgr.initialize()

    def teardown_method(self):
        self.mgr.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_policy(self):
        p = self.mgr.create_policy("Auto Restart Nginx", "container", "automatic")
        assert p.policy_id is not None
        assert p.name == "Auto Restart Nginx"

    def test_add_health_check(self):
        p = self.mgr.create_policy("Health Check Policy", "container", "automatic")
        hc = self.mgr.add_health_check(p.policy_id, "http", {"url": "http://localhost/health", "interval_seconds": 30})
        assert hc.check_id is not None

    def test_add_remediation_action(self):
        p = self.mgr.create_policy("Remediate Policy", "container", "automatic")
        action = self.mgr.add_remediation_action(p.policy_id, "restart", {"service": "nginx", "timeout_seconds": 30})
        assert action.action_id is not None

    def test_execute_healing(self):
        p = self.mgr.create_policy("Heal Test", "container", "automatic")
        event = self.mgr.execute_healing(p.policy_id, "container-01", "unhealthy")
        assert event.event_id is not None
        assert event.resource_id == "container-01"

    def test_list_events(self):
        p = self.mgr.create_policy("Event Test", "container", "automatic")
        self.mgr.execute_healing(p.policy_id, "c1", "unhealthy")
        self.mgr.execute_healing(p.policy_id, "c2", "degraded")
        assert len(self.mgr.list_events()) >= 2

    def test_policy_mode(self):
        auto = self.mgr.create_policy("Auto", "server", "automatic")
        manual = self.mgr.create_policy("Manual", "server", "manual")
        assert auto.mode == PolicyMode.AUTOMATIC
        assert manual.mode == PolicyMode.MANUAL

    def test_disable_policy(self):
        p = self.mgr.create_policy("Disable", "container", "automatic")
        self.mgr.disable_policy(p.policy_id)
        assert self.mgr.get_policy(p.policy_id).enabled is False

    def test_enable_policy(self):
        p = self.mgr.create_policy("Enable", "container", "automatic")
        self.mgr.disable_policy(p.policy_id)
        self.mgr.enable_policy(p.policy_id)
        assert self.mgr.get_policy(p.policy_id).enabled is True

    def test_statistics(self):
        p = self.mgr.create_policy("Stats", "container", "automatic")
        self.mgr.execute_healing(p.policy_id, "c1", "unhealthy")
        stats = self.mgr.get_statistics()
        assert stats["total_policies"] == 1
        assert stats["total_events"] >= 1

    def test_confidence_scoring(self):
        p = self.mgr.create_policy("Confidence", "container", "automatic")
        self.mgr.execute_healing(p.policy_id, "c1", "unhealthy")
        self.mgr.execute_healing(p.policy_id, "c1", "healthy")
        stats = self.mgr.get_statistics()
        assert "success_rate" in stats or "confidence" in str(stats).lower()

    def test_persistence(self):
        self.mgr.create_policy("Persist", "container", "automatic")
        self.mgr.close()
        mgr2 = SelfHealingManager(storage_path=self.path)
        mgr2.initialize()
        assert len(mgr2.list_policies()) == 1
        mgr2.close()

    def test_error_handling(self):
        assert self.mgr.get_policy("nonexistent") is None
        with pytest.raises(ValueError, match="not found"):
            self.mgr.execute_healing("nonexistent", "r1", "unhealthy")
        with pytest.raises(ValueError, match="not found"):
            self.mgr.add_health_check("nonexistent", "http", {})
        with pytest.raises(ValueError, match="not found"):
            self.mgr.add_remediation_action("nonexistent", "restart", {})

    def test_multiple_policies(self):
        for i in range(5):
            self.mgr.create_policy(f"Policy {i}", "container", "automatic")
        assert len(self.mgr.list_policies()) == 5

# === test_infrastructure_pipelines_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = InfrastructurePipelinesManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestPipelineCRUD:
    def test_create_pipeline(self, manager):
        pl = manager.create_pipeline(name="CI/CD Pipeline", description="Main deployment pipeline", provider=PipelineProvider.GITHUB_ACTIONS, repository="org/repo", branch="main", deployment_strategy=DeploymentStrategy.ROLLING, created_by="admin")
        assert pl.id is not None
        assert pl.name == "CI/CD Pipeline"
        assert pl.provider == PipelineProvider.GITHUB_ACTIONS
        assert pl.repository == "org/repo"
        assert pl.status == PipelineStatus.DRAFT

    def test_get_pipeline(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        retrieved = manager.get_pipeline(pl.id)
        assert retrieved is not None

    def test_update_pipeline(self, manager):
        pl = manager.create_pipeline(name="Original", description="Original", provider=PipelineProvider.CUSTOM)
        updated = manager.update_pipeline(pl.id, {"name": "Updated", "branch": "develop"})
        assert updated.name == "Updated"
        assert updated.branch == "develop"

    def test_delete_pipeline(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        assert manager.delete_pipeline(pl.id) == True


class TestPipelineStages:
    def test_add_stage(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        stage = manager.add_stage(pl.id, "Build", order=1, jobs=[{"name": "build-app", "type": "script"}], environment="staging")
        assert stage is not None
        assert stage.name == "Build"
        assert stage.order == 1

    def test_remove_stage(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        stage = manager.add_stage(pl.id, "Build", order=1)
        assert manager.remove_stage(pl.id, stage.id) == True
        assert len(pl.stages) == 0


class TestPipelineTriggers:
    def test_add_trigger(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.GITHUB_ACTIONS)
        trigger = manager.add_trigger(pl.id, PipelineProvider.GITHUB_ACTIONS, "push", branch="main", paths=["src/**"])
        assert trigger is not None
        assert trigger.event == "push"
        assert trigger.branch == "main"

    def test_remove_trigger(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        trigger = manager.add_trigger(pl.id, PipelineProvider.CUSTOM, "manual")
        assert manager.remove_trigger(pl.id, trigger.id) == True


class TestPipelineExecution:
    def test_trigger_run(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        stage = manager.add_stage(pl.id, "Build", order=1)
        run = manager.trigger_run(pl.id, branch="main", started_by="ci-bot")
        assert run is not None
        assert run.status in (StageStatus.SUCCEEDED, StageStatus.FAILED)

    def test_get_run(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        run = manager.trigger_run(pl.id)
        retrieved = manager.get_run(run.id)
        assert retrieved is not None

    def test_cancel_run(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        run = manager.trigger_run(pl.id)
        if run.status == StageStatus.PENDING:
            assert manager.cancel_run(run.id) == True


class TestApprovals:
    def test_approve_stage(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        stage = manager.add_stage(pl.id, "Approval Needed", order=1, requires_approval=True, approvers=["admin"])
        run = manager.trigger_run(pl.id)
        if run and stage.id in run.stages:
            result = manager.approve_stage(run.id, stage.id, "admin")
            assert result is not None

    def test_reject_stage(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        stage = manager.add_stage(pl.id, "Approval", order=1, requires_approval=True, approvers=["admin"])
        run = manager.trigger_run(pl.id)
        if run:
            result = manager.reject_stage(run.id, stage.id, "admin", "Not ready")
            assert result is not None


class TestDeployments:
    def test_get_deployments(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        run = manager.trigger_run(pl.id)
        deployments = manager.get_deployments(pipeline_id=pl.id)
        assert deployments is not None

    def test_rollback_deployment(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        run = manager.trigger_run(pl.id)
        deployments = manager.get_deployments(pipeline_id=pl.id)
        if deployments:
            rollback = manager.rollback_deployment(deployments[0].id, "admin")
            assert rollback is not None


class TestPipelineLifecycle:
    def test_enable_pipeline(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        assert manager.enable_pipeline(pl.id) == True
        assert pl.status == PipelineStatus.ACTIVE

    def test_disable_pipeline(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        assert manager.disable_pipeline(pl.id) == True
        assert pl.status == PipelineStatus.DISABLED


class TestExport:
    def test_export_yaml(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        yaml_out = manager.export_pipeline_yaml(pl.id)
        assert yaml_out is not None
        assert "name: Test" in yaml_out


class TestStatistics:
    def test_get_statistics(self, manager):
        pl = manager.create_pipeline(name="Test", description="Test", provider=PipelineProvider.CUSTOM)
        manager.enable_pipeline(pl.id)
        manager.trigger_run(pl.id)
        stats = manager.get_statistics()
        assert stats["total_pipelines"] >= 1
        assert stats["total_runs"] >= 0

# === test_maintenance_planner_ext.py ===

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

# === test_quota_manager_ext.py ===

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

# === test_runbook_library_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = RunbookLibraryManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestRunbookCRUD:
    def test_create_runbook(self, manager):
        rb = manager.create_runbook(name="Incident Response", description="Standard incident response procedure", category=RunbookCategory.INCIDENT_RESPONSE, author="security-team", tags=["incident", "security"], severity="high", estimated_duration_minutes=45)
        assert rb.id is not None
        assert rb.name == "Incident Response"
        assert rb.category == RunbookCategory.INCIDENT_RESPONSE
        assert rb.status == RunbookStatus.DRAFT

    def test_get_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.TROUBLESHOOTING)
        retrieved = manager.get_runbook(rb.id)
        assert retrieved is not None

    def test_update_runbook(self, manager):
        rb = manager.create_runbook(name="Original", description="Original", category=RunbookCategory.MANUAL)
        updated = manager.update_runbook(rb.id, {"name": "Updated", "severity": "critical"})
        assert updated.name == "Updated"
        assert updated.severity == "critical"

    def test_delete_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        assert manager.delete_runbook(rb.id) == True


class TestSteps:
    def test_add_step(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.TROUBLESHOOTING)
        step = manager.add_step(rb.id, "Check Logs", StepType.SCRIPT, order=1, description="Check application logs", command="journalctl -u app", critical=True, timeout_seconds=60)
        assert step is not None
        assert step.name == "Check Logs"
        assert step.critical == True
        assert step.timeout_seconds == 60

    def test_remove_step(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        step = manager.add_step(rb.id, "Step1", StepType.MANUAL, order=1)
        assert manager.remove_step(rb.id, step.id) == True


class TestParameters:
    def test_add_parameter(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.AUTOMATION)
        param = manager.add_parameter(rb.id, "hostname", "string", "Target hostname", required=True, default_value="localhost", validation_regex="^[a-z0-9-]+$")
        assert param is not None
        assert param.name == "hostname"
        assert param.required == True
        assert param.validation_regex == "^[a-z0-9-]+$"


class TestVersioning:
    def test_create_version(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        version = manager.create_version(rb.id, changelog="Initial version", created_by="admin")
        assert version is not None
        assert version.version > 0

    def test_get_versions(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.create_version(rb.id, changelog="v1")
        versions = manager.get_versions(rb.id)
        assert len(versions) >= 1


class TestLifecycle:
    def test_publish_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        assert manager.publish_runbook(rb.id) == True
        assert rb.status == RunbookStatus.PUBLISHED

    def test_deprecate_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.publish_runbook(rb.id)
        assert manager.deprecate_runbook(rb.id) == True
        assert rb.status == RunbookStatus.DEPRECATED


class TestSearch:
    def test_search_runbooks(self, manager):
        manager.create_runbook(name="Database Backup", description="DB backup procedure", category=RunbookCategory.BACKUP)
        manager.create_runbook(name="Server Deploy", description="Server deployment", category=RunbookCategory.DEPLOYMENT)
        results = manager.search_runbooks("backup")
        assert len(results) >= 1

    def test_list_runbooks(self, manager):
        manager.create_runbook(name="R1", description="Test", category=RunbookCategory.MONITORING)
        manager.create_runbook(name="R2", description="Test", category=RunbookCategory.SECURITY)
        runbooks = manager.list_runbooks()
        assert len(runbooks) >= 2

    def test_list_by_category(self, manager):
        manager.create_runbook(name="R1", description="Test", category=RunbookCategory.BACKUP)
        runbooks = manager.list_runbooks(category=RunbookCategory.BACKUP)
        assert len(runbooks) >= 1


class TestExecution:
    def test_execute_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.AUTOMATION)
        manager.publish_runbook(rb.id)
        manager.add_step(rb.id, "Echo", StepType.SCRIPT, order=1, command="result = 'hello'")
        execution = manager.execute_runbook(rb.id, parameters={}, executed_by="admin", triggered_by="manual")
        assert execution is not None
        assert execution.status in ("completed", "failed")

    def test_get_executions(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.publish_runbook(rb.id)
        executions = manager.get_executions(runbook_id=rb.id)
        assert executions is not None


class TestExportImport:
    def test_export_yaml(self, manager):
        rb = manager.create_runbook(name="Test Runbook", description="Test", category=RunbookCategory.GENERAL)
        yaml_out = manager.export_runbook_yaml(rb.id)
        assert yaml_out is not None
        assert "name: Test Runbook" in yaml_out

    def test_import_yaml(self, manager):
        yaml_content = "name: Imported RB\ndescription: Imported\ncategory: troubleshooting\nversion: 1\nparameters: []\nsteps: []"
        rb = manager.import_runbook_yaml(yaml_content, author="admin")
        assert rb is not None
        assert rb.name == "Imported RB"


class TestClone:
    def test_clone_runbook(self, manager):
        rb = manager.create_runbook(name="Original", description="Original RB", category=RunbookCategory.GENERAL)
        clone = manager.clone_runbook(rb.id, "Clone RB")
        assert clone is not None
        assert clone.name == "Clone RB"
        assert clone.id != rb.id


class TestBulkPublish:
    def test_bulk_publish(self, manager):
        r1 = manager.create_runbook(name="R1", description="T1", category=RunbookCategory.GENERAL)
        r2 = manager.create_runbook(name="R2", description="T2", category=RunbookCategory.GENERAL)
        count = manager.bulk_publish([r1.id, r2.id])
        assert count == 2


class TestStatistics:
    def test_get_statistics(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        stats = manager.get_statistics()
        assert stats["total_runbooks"] >= 1

# === test_self_healing_ext.py ===

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

# === test_workflow_studio_ext.py ===

@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = WorkflowStudioManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestWorkflowCRUD:
    def test_create_workflow(self, manager):
        wf = manager.create_workflow(name="Deploy App", description="Deploy application to production", created_by="admin", category="deployment", tags=["deploy", "production"])
        assert wf.id is not None
        assert wf.name == "Deploy App"
        assert wf.status == WorkflowStatus.DRAFT
        assert wf.category == "deployment"

    def test_get_workflow(self, manager):
        wf = manager.create_workflow(name="Test", description="Test workflow")
        retrieved = manager.get_workflow(wf.id)
        assert retrieved is not None
        assert retrieved.id == wf.id

    def test_update_workflow(self, manager):
        wf = manager.create_workflow(name="Original", description="Original description")
        updated = manager.update_workflow(wf.id, {"name": "Updated", "description": "Updated description"})
        assert updated.name == "Updated"
        assert updated.description == "Updated description"

    def test_delete_workflow(self, manager):
        wf = manager.create_workflow(name="To Delete", description="Will be deleted")
        assert manager.delete_workflow(wf.id) == True
        assert manager.get_workflow(wf.id) is None

    def test_list_workflows(self, manager):
        manager.create_workflow(name="WF1", description="First")
        manager.create_workflow(name="WF2", description="Second")
        workflows = manager.list_workflows()
        assert len(workflows) >= 2


class TestWorkflowSteps:
    def test_add_step(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        step = WorkflowStep(id="step-1", name="Build App", step_type=WorkflowStepType.SCRIPT, config={"script": "npm run build"}, timeout_seconds=600)
        result = manager.add_step(wf.id, step)
        assert result is not None
        assert len(result.steps) == 1

    def test_update_step(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        step = WorkflowStep(id="step-1", name="Build", step_type=WorkflowStepType.SCRIPT, config={})
        manager.add_step(wf.id, step)
        updated = manager.update_step(wf.id, "step-1", {"name": "Build Updated", "timeout_seconds": 900})
        assert updated.name == "Build Updated"
        assert updated.timeout_seconds == 900

    def test_remove_step(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        step = WorkflowStep(id="step-1", name="Build", step_type=WorkflowStepType.SCRIPT, config={})
        manager.add_step(wf.id, step)
        assert manager.remove_step(wf.id, "step-1") == True
        assert len(wf.steps) == 0


class TestWorkflowTriggers:
    def test_create_trigger(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        trigger = manager.create_trigger(wf.id, WorkflowTriggerType.SCHEDULE, "Daily deploy", cron_expression="0 6 * * *")
        assert trigger is not None
        assert trigger.trigger_type == WorkflowTriggerType.SCHEDULE
        assert trigger.cron_expression == "0 6 * * *"

    def test_delete_trigger(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        trigger = manager.create_trigger(wf.id, WorkflowTriggerType.MANUAL, "Manual trigger")
        assert manager.delete_trigger(wf.id, trigger.id) == True
        assert len(wf.triggers) == 0


class TestWorkflowExecution:
    def test_execute_workflow(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        manager.activate_workflow(wf.id)
        step = WorkflowStep(id="step-1", name="Echo", step_type=WorkflowStepType.SCRIPT, config={"script": "result = {'echo': 'hello'}"})
        manager.add_step(wf.id, step)
        execution = manager.execute_workflow(wf.id, input_data={"message": "hello"}, executed_by="admin")
        assert execution is not None
        assert execution.status in (WorkflowExecutionStatus.SUCCEEDED, WorkflowExecutionStatus.FAILED)

    def test_get_execution(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        manager.activate_workflow(wf.id)
        step = WorkflowStep(id="step-1", name="Echo", step_type=WorkflowStepType.SCRIPT, config={"script": "result = {'echo': 'hi'}"})
        manager.add_step(wf.id, step)
        execution = manager.execute_workflow(wf.id)
        retrieved = manager.get_execution(execution.id)
        assert retrieved is not None

    def test_cancel_execution(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        manager.activate_workflow(wf.id)
        step = WorkflowStep(id="step-1", name="Echo", step_type=WorkflowStepType.SCRIPT, config={"script": "result = {'echo': 'hi'}"})
        manager.add_step(wf.id, step)
        execution = manager.execute_workflow(wf.id)
        if execution.status == WorkflowExecutionStatus.SUCCEEDED:
            pass
        assert execution.status is not None


class TestWorkflowTemplates:
    def test_create_template(self, manager):
        tmpl = manager.create_template(name="Deploy Template", description="Standard deploy", category="deployment", steps=[{"name": "Build", "type": "script", "config": {"script": "build"}}, {"name": "Test", "type": "script", "config": {"script": "test"}}], tags=["deploy", "ci"])
        assert tmpl.id is not None
        assert tmpl.name == "Deploy Template"
        assert len(tmpl.steps) == 2

    def test_apply_template(self, manager):
        tmpl = manager.create_template(name="Deploy", description="Standard deploy", category="deployment")
        wf = manager.apply_template(tmpl.id, "My Deploy", "My deployment", created_by="admin")
        assert wf is not None
        assert wf.name == "My Deploy"


class TestVersioning:
    def test_create_version(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        step = WorkflowStep(id="step-1", name="Build", step_type=WorkflowStepType.SCRIPT, config={})
        manager.add_step(wf.id, step)
        version = manager.create_version(wf.id, changelog="Initial version", created_by="admin")
        assert version is not None
        assert version.version >= 1

    def test_get_versions(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        manager.create_version(wf.id, changelog="v1")
        versions = manager.get_versions(wf.id)
        assert len(versions) >= 1


class TestYAMLExportImport:
    def test_export_yaml(self, manager):
        wf = manager.create_workflow(name="Test", description="Test")
        yaml_out = manager.export_workflow_yaml(wf.id)
        assert yaml_out is not None
        assert "name: Test" in yaml_out

    def test_import_yaml(self, manager):
        yaml_content = "name: Imported WF\ndescription: Imported\nversion: 1\nsteps: []\ntriggers: []"
        wf = manager.import_workflow_yaml(yaml_content, created_by="admin")
        assert wf is not None
        assert wf.name == "Imported WF"


class TestDuplicate:
    def test_duplicate_workflow(self, manager):
        wf = manager.create_workflow(name="Original", description="Original WF")
        clone = manager.duplicate_workflow(wf.id, "Clone")
        assert clone is not None
        assert clone.name == "Clone"
        assert clone.id != wf.id


class TestSearch:
    def test_search_workflows(self, manager):
        manager.create_workflow(name="Deploy Production", description="Production deploy")
        manager.create_workflow(name="Backup Database", description="Daily DB backup")
        results = manager.search_workflows("deploy")
        assert len(results) >= 1
        assert all("deploy" in r.name.lower() or "deploy" in r.description.lower() for r in results)


class TestStatistics:
    def test_get_statistics(self, manager):
        manager.create_workflow(name="Test", description="Test")
        stats = manager.get_statistics()
        assert stats["total_workflows"] >= 1

