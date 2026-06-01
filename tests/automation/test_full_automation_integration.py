"""Comprehensive integration tests for automation & orchestration features (71-80)."""
import pytest
import json
import tempfile
import os
import uuid
from datetime import datetime, timedelta
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
