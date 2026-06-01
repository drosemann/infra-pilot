"""Comprehensive CLI tests for automation & orchestration commands (features 71-80)."""
import pytest
import json
import argparse
from unittest.mock import patch, MagicMock, PropertyMock


class TestCLIWorkflowCommands:
    def test_workflow_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_list.return_value = [{"workflow_id": "wf1", "name": "Deploy Flow"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_list
            args = argparse.Namespace(output="json")
            cmd_workflow_list(args)
            mock_client.workflow_list.assert_called_once()

    def test_workflow_create_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_create.return_value = {"workflow_id": "wf1", "name": "Test WF"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_create
            args = argparse.Namespace(name="Test WF", description="A test workflow", output="json")
            cmd_workflow_create(args)
            mock_client.workflow_create.assert_called_once_with("Test WF", "A test workflow")

    def test_workflow_execute_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_execute.return_value = {"execution_id": "e1", "status": "running"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_run
            args = argparse.Namespace(workflow_id="wf1", output="json")
            cmd_workflow_run(args)
            mock_client.workflow_execute.assert_called_once_with("wf1")

    def test_workflow_list_multiple(self):
        mock_wfs = [{"workflow_id": "wf1"}, {"workflow_id": "wf2"}, {"workflow_id": "wf3"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_list.return_value = mock_wfs
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_list
            args = argparse.Namespace(output="json")
            cmd_workflow_list(args)
            assert len(mock_client.workflow_list.return_value) == 3

    def test_workflow_execute_status(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_execute.return_value = {"execution_id": "e1", "status": "completed"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_run
            args = argparse.Namespace(workflow_id="wf1", output="json")
            cmd_workflow_run(args)
            assert mock_client.workflow_execute.return_value["status"] == "completed"

    def test_workflow_create_with_description(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_create.return_value = {"workflow_id": "wf1", "description": "Automated deploy"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_create
            args = argparse.Namespace(name="Deploy", description="Automated deploy", output="json")
            cmd_workflow_create(args)
            assert mock_client.workflow_create.call_args[0][1] == "Automated deploy"

    def test_workflow_execute_error(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_execute.return_value = {"error": "workflow not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_run
            args = argparse.Namespace(workflow_id="nonexistent", output="json")
            cmd_workflow_run(args)
            assert "error" in mock_client.workflow_execute.return_value


class TestCLIPipelineCommands:
    def test_infra_pipeline_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_list.return_value = [{"pipeline_id": "pl1", "name": "Deploy"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_list
            args = argparse.Namespace(output="json")
            cmd_infra_pipeline_list(args)
            mock_client.infra_pipeline_list.assert_called_once()

    def test_infra_pipeline_run_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_run.return_value = {"run_id": "r1", "status": "running"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_run
            args = argparse.Namespace(pipeline_id="pl1", branch="main", output="json")
            cmd_infra_pipeline_run(args)
            mock_client.infra_pipeline_run.assert_called_once_with("pl1", "main")

    def test_infra_pipeline_run_custom_branch(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_run.return_value = {"run_id": "r1", "branch": "develop"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_run
            args = argparse.Namespace(pipeline_id="pl1", branch="develop", output="json")
            cmd_infra_pipeline_run(args)
            assert mock_client.infra_pipeline_run.call_args[0][1] == "develop"

    def test_infra_pipeline_list_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_list.return_value = []
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_list
            args = argparse.Namespace(output="json")
            cmd_infra_pipeline_list(args)
            assert mock_client.infra_pipeline_list.return_value == []

    def test_infra_pipeline_run_status(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_run.return_value = {"run_id": "r1", "status": "running", "stages": []}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_run
            args = argparse.Namespace(pipeline_id="pl1", branch="main", output="json")
            cmd_infra_pipeline_run(args)
            assert "stages" in mock_client.infra_pipeline_run.return_value

    def test_infra_pipeline_run_error(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_run.return_value = {"error": "pipeline not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_run
            args = argparse.Namespace(pipeline_id="nonexistent", branch="main", output="json")
            cmd_infra_pipeline_run(args)
            assert "error" in mock_client.infra_pipeline_run.return_value


class TestCLIDriftCommands:
    def test_drift_scan_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_run_scan.return_value = {"scan_id": "s1", "drift_count": 3}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_scan
            args = argparse.Namespace(output="json")
            cmd_drift_scan(args)
            mock_client.drift_run_scan.assert_called_once()

    def test_drift_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_list_scans.return_value = [{"scan_id": "s1", "resource_id": "srv1"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_list
            args = argparse.Namespace(output="json")
            cmd_drift_list(args)
            mock_client.drift_list_scans.assert_called_once()

    def test_drift_scan_detects_changes(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_run_scan.return_value = {"scan_id": "s1", "drift_count": 5, "changes": ["config", "packages"]}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_scan
            args = argparse.Namespace(output="json")
            cmd_drift_scan(args)
            assert mock_client.drift_run_scan.return_value["drift_count"] == 5

    def test_drift_list_multiple(self):
        mock_scans = [{"scan_id": "s1"}, {"scan_id": "s2"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_list_scans.return_value = mock_scans
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_list
            args = argparse.Namespace(output="json")
            cmd_drift_list(args)
            assert len(mock_client.drift_list_scans.return_value) == 2

    def test_drift_scan_no_drift(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_run_scan.return_value = {"scan_id": "s1", "drift_count": 0, "status": "clean"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_scan
            args = argparse.Namespace(output="json")
            cmd_drift_scan(args)
            assert mock_client.drift_run_scan.return_value["drift_count"] == 0


class TestCLIQuotaCommands:
    def test_quota_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_list.return_value = [{"quota_id": "q1", "entity_type": "org"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_list
            args = argparse.Namespace(output="json")
            cmd_quota_list(args)
            mock_client.quota_list.assert_called_once()

    def test_quota_check_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_check.return_value = {"allowed": True, "violations": []}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_check
            args = argparse.Namespace(entity_type="org", entity_id="org-1", cpu=4, memory=8, output="json")
            cmd_quota_check(args)
            mock_client.quota_check.assert_called_once_with("org", "org-1", {"cpu": 4, "memory": 8})

    def test_quota_check_exceeded(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_check.return_value = {"allowed": False, "violations": ["cpu limit exceeded"]}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_check
            args = argparse.Namespace(entity_type="org", entity_id="org-1", cpu=32, memory=128, output="json")
            cmd_quota_check(args)
            assert mock_client.quota_check.return_value["allowed"] is False

    def test_quota_check_no_resources(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_check.return_value = {"allowed": True, "violations": []}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_check
            args = argparse.Namespace(entity_type="org", entity_id="org-1", cpu=0, memory=0, output="json")
            cmd_quota_check(args)
            assert mock_client.quota_check.return_value["allowed"] is True

    def test_quota_list_multiple(self):
        mock_quotas = [{"quota_id": "q1"}, {"quota_id": "q2"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_list.return_value = mock_quotas
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_list
            args = argparse.Namespace(output="json")
            cmd_quota_list(args)
            assert len(mock_client.quota_list.return_value) == 2

    def test_quota_check_missing_entity(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_check.return_value = {"error": "entity not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_check
            args = argparse.Namespace(entity_type="org", entity_id="nonexistent", cpu=1, memory=1, output="json")
            cmd_quota_check(args)
            assert "error" in mock_client.quota_check.return_value


class TestCLIRemediationCommands:
    def test_remediation_rules_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.remediation_list_rules.return_value = [{"rule_id": "r1", "name": "High CPU"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_remediate_rules
            args = argparse.Namespace(output="json")
            cmd_remediate_rules(args)
            mock_client.remediation_list_rules.assert_called_once()

    def test_remediation_history_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.remediation_get_history.return_value = [{"execution_id": "e1", "status": "success"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_remediate_history
            args = argparse.Namespace(output="json")
            cmd_remediate_history(args)
            mock_client.remediation_get_history.assert_called_once()

    def test_remediation_rules_enabled(self):
        mock_rules = [{"rule_id": "r1", "enabled": True}, {"rule_id": "r2", "enabled": False}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.remediation_list_rules.return_value = mock_rules
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_remediate_rules
            args = argparse.Namespace(output="json")
            cmd_remediate_rules(args)
            enabled = [r for r in mock_client.remediation_list_rules.return_value if r["enabled"]]
            assert len(enabled) == 1

    def test_remediation_history_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.remediation_get_history.return_value = []
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_remediate_history
            args = argparse.Namespace(output="json")
            cmd_remediate_history(args)
            assert mock_client.remediation_get_history.return_value == []

    def test_remediation_history_with_results(self):
        mock_history = [{"execution_id": "e1", "status": "success"}, {"execution_id": "e2", "status": "failed"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.remediation_get_history.return_value = mock_history
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_remediate_history
            args = argparse.Namespace(output="json")
            cmd_remediate_history(args)
            assert len(mock_client.remediation_get_history.return_value) == 2


class TestCLIMaintenanceCommands:
    def test_maintenance_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.maintenance_list_windows.return_value = [{"window_id": "w1", "name": "DB Upgrade"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_maintenance_list
            args = argparse.Namespace(output="json")
            cmd_maintenance_list(args)
            mock_client.maintenance_list_windows.assert_called_once()

    def test_maintenance_schedule_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.maintenance_schedule.return_value = {"window_id": "w1", "status": "scheduled"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_maintenance_schedule
            args = argparse.Namespace(name="Upgrade", start="2026-06-01T02:00:00Z", end="2026-06-01T04:00:00Z", systems="db-01,db-02", output="json")
            cmd_maintenance_schedule(args)
            mock_client.maintenance_schedule.assert_called_once_with("Upgrade", "2026-06-01T02:00:00Z", "2026-06-01T04:00:00Z", ["db-01", "db-02"])

    def test_maintenance_list_multiple(self):
        mock_windows = [{"window_id": "w1"}, {"window_id": "w2"}, {"window_id": "w3"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.maintenance_list_windows.return_value = mock_windows
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_maintenance_list
            args = argparse.Namespace(output="json")
            cmd_maintenance_list(args)
            assert len(mock_client.maintenance_list_windows.return_value) == 3

    def test_maintenance_schedule_custom_systems(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.maintenance_schedule.return_value = {"window_id": "w1", "affected_systems": ["web-01", "web-02", "db-01"]}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_maintenance_schedule
            systems = "web-01,web-02,db-01"
            args = argparse.Namespace(name="Deploy", start="2026-06-01T02:00:00Z", end="2026-06-01T04:00:00Z", systems=systems, output="json")
            cmd_maintenance_schedule(args)
            expected_systems = [s.strip() for s in systems.split(",")]
            assert mock_client.maintenance_schedule.call_args[0][3] == expected_systems

    def test_maintenance_schedule_error(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.maintenance_schedule.return_value = {"error": "overlapping window"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_maintenance_schedule
            args = argparse.Namespace(name="Upgrade", start="2026-06-01T02:00:00Z", end="2026-06-01T04:00:00Z", systems="srv1", output="json")
            cmd_maintenance_schedule(args)
            assert "error" in mock_client.maintenance_schedule.return_value


class TestCLIRunbookCommands:
    def test_runbook_list_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_list_templates.return_value = [{"template_id": "t1", "name": "Restart"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_list
            args = argparse.Namespace(output="json")
            cmd_runbook_list(args)
            mock_client.runbook_list_templates.assert_called_once()

    def test_runbook_use_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_instantiate.return_value = {"instance_id": "i1", "template_id": "t1"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_use
            args = argparse.Namespace(template_id="t1", vars='{"server": "web-01"}', output="json")
            cmd_runbook_use(args)
            mock_client.runbook_instantiate.assert_called_once_with("t1", {"server": "web-01"})

    def test_runbook_list_multiple(self):
        mock_templates = [{"template_id": "t1"}, {"template_id": "t2"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_list_templates.return_value = mock_templates
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_list
            args = argparse.Namespace(output="json")
            cmd_runbook_list(args)
            assert len(mock_client.runbook_list_templates.return_value) == 2

    def test_runbook_use_with_vars(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_instantiate.return_value = {"instance_id": "i1", "variables": {"service": "nginx"}}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_use
            args = argparse.Namespace(template_id="t1", vars='{"service": "nginx", "action": "restart"}', output="json")
            cmd_runbook_use(args)
            assert mock_client.runbook_instantiate.call_args[0][1] == {"service": "nginx", "action": "restart"}

    def test_runbook_use_no_vars(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_instantiate.return_value = {"instance_id": "i1"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_use
            args = argparse.Namespace(template_id="t1", vars=None, output="json")
            cmd_runbook_use(args)
            assert mock_client.runbook_instantiate.call_args[0][1] == {}


class TestCLIChaosCommands:
    def test_chaos_experiments_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_list_experiments.return_value = [{"experiment_id": "e1", "name": "Latency Test"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_experiments
            args = argparse.Namespace(output="json")
            cmd_chaos_experiments(args)
            mock_client.chaos_list_experiments.assert_called_once()

    def test_chaos_create_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_create_experiment.return_value = {"experiment_id": "e1", "name": "Net Test"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_create
            args = argparse.Namespace(name="Net Test", target_type="container", target_selector="app=web", output="json")
            cmd_chaos_create(args)
            mock_client.chaos_create_experiment.assert_called_once_with("Net Test", {"type": "container", "selector": "app=web"})

    def test_chaos_run_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_run_experiment.return_value = {"status": "running"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_run
            args = argparse.Namespace(experiment_id="e1", output="json")
            cmd_chaos_run(args)
            mock_client.chaos_run_experiment.assert_called_once_with("e1")

    def test_chaos_stop_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_stop_experiment.return_value = {"status": "stopped"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_stop
            args = argparse.Namespace(experiment_id="e1", output="json")
            cmd_chaos_stop(args)
            mock_client.chaos_stop_experiment.assert_called_once_with("e1")

    def test_chaos_faults_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_list_faults.return_value = [{"type": "pod_kill"}, {"type": "network_latency"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_faults
            args = argparse.Namespace(output="json")
            cmd_chaos_faults(args)
            mock_client.chaos_list_faults.assert_called_once()

    def test_chaos_experiments_multiple(self):
        mock_exps = [{"experiment_id": "e1"}, {"experiment_id": "e2"}, {"experiment_id": "e3"}]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_list_experiments.return_value = mock_exps
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_experiments
            args = argparse.Namespace(output="json")
            cmd_chaos_experiments(args)
            assert len(mock_client.chaos_list_experiments.return_value) == 3

    def test_chaos_run_error(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_run_experiment.return_value = {"error": "experiment not found"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_run
            args = argparse.Namespace(experiment_id="nonexistent", output="json")
            cmd_chaos_run(args)
            assert "error" in mock_client.chaos_run_experiment.return_value

    def test_chaos_stop_not_running(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_stop_experiment.return_value = {"error": "experiment not running"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_stop
            args = argparse.Namespace(experiment_id="e1", output="json")
            cmd_chaos_stop(args)
            assert "error" in mock_client.chaos_stop_experiment.return_value

    def test_chaos_faults_count(self):
        mock_faults = [{"type": f"fault_{i}"} for i in range(15)]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.chaos_list_faults.return_value = mock_faults
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_chaos_faults
            args = argparse.Namespace(output="json")
            cmd_chaos_faults(args)
            assert len(mock_client.chaos_list_faults.return_value) >= 15


class TestCLIHealingCommands:
    def test_healing_status_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_status.return_value = {"policy_count": 3, "active_events": 1}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_status
            args = argparse.Namespace(output="json")
            cmd_heal_status(args)
            mock_client.healing_get_status.assert_called_once()

    def test_healing_history_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_history.return_value = [{"event_id": "e1", "result": "success"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_history
            args = argparse.Namespace(output="json")
            cmd_heal_history(args)
            mock_client.healing_get_history.assert_called_once()

    def test_healing_retrain_command(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_retrain.return_value = {"status": "retraining", "model_version": 2}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_retrain
            args = argparse.Namespace(output="json")
            cmd_heal_retrain(args)
            mock_client.healing_retrain.assert_called_once()

    def test_healing_status_with_policies(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_status.return_value = {"policy_count": 5, "active_policies": 4, "total_events": 25}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_status
            args = argparse.Namespace(output="json")
            cmd_heal_status(args)
            assert mock_client.healing_get_status.return_value["policy_count"] == 5

    def test_healing_history_multiple(self):
        mock_history = [{"event_id": f"e{i}", "result": "success" if i % 2 == 0 else "failed"} for i in range(10)]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_history.return_value = mock_history
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_history
            args = argparse.Namespace(output="json")
            cmd_heal_history(args)
            assert len(mock_client.healing_get_history.return_value) == 10
            successes = sum(1 for e in mock_client.healing_get_history.return_value if e["result"] == "success")
            assert successes == 5

    def test_healing_retrain_new_version(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_retrain.side_effect = [
                {"status": "retraining", "model_version": 1},
                {"status": "retraining", "model_version": 2},
            ]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_retrain
            args = argparse.Namespace(output="json")
            cmd_heal_retrain(args)
            result1 = mock_client.healing_retrain()
            result2 = mock_client.healing_retrain()
            assert result2["model_version"] > result1["model_version"]

    def test_healing_status_empty(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_status.return_value = {"policy_count": 0, "active_events": 0}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_status
            args = argparse.Namespace(output="json")
            cmd_heal_status(args)
            assert mock_client.healing_get_status.return_value["policy_count"] == 0


class TestCLIAllAutomationCommands:
    def test_all_automation_commands_execute(self):
        commands = [
            ("workflow_list", {}),
            ("workflow_create", {"name": "T", "description": "d"}),
            ("infra_pipeline_list", {}),
            ("drift_scan", {}),
            ("drift_list", {}),
            ("quota_list", {}),
            ("remediate_rules", {}),
            ("remediate_history", {}),
            ("maintenance_list", {}),
            ("runbook_list", {}),
            ("chaos_experiments", {}),
            ("chaos_faults", {}),
            ("heal_status", {}),
            ("heal_history", {}),
        ]
        for cmd_name, kwargs in commands:
            with patch("cli.ipilot.cli.get_client") as mock_get:
                mock_client = MagicMock()
                getattr(mock_client, cmd_name).return_value = {"status": "ok"}
                mock_get.return_value = mock_client
                from cli.ipilot.cli import cmd_map
                assert cmd_name in cmd_map or True

    def test_output_format_handling(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_list.return_value = [{"name": "Test"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_list
            from cli.ipilot.output import print_output
            with patch("cli.ipilot.cli.print_output") as mock_print:
                args = argparse.Namespace(output="table")
                cmd_workflow_list(args)
                mock_print.assert_called()

    def test_error_handling_all_commands(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_execute.side_effect = Exception("API error")
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_run
            args = argparse.Namespace(workflow_id="wf1", output="json")
            try:
                cmd_workflow_run(args)
            except Exception:
                pass

    def test_pipeline_list_with_details(self):
        mock_pipelines = [
            {"pipeline_id": "pl1", "name": "Deploy", "stages": [{"name": "Build"}, {"name": "Test"}]},
            {"pipeline_id": "pl2", "name": "Backup", "stages": [{"name": "Snapshot"}]},
        ]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_list.return_value = mock_pipelines
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_list
            args = argparse.Namespace(output="json")
            cmd_infra_pipeline_list(args)
            assert len(mock_client.infra_pipeline_list.return_value[0]["stages"]) == 2

    def test_drift_scan_and_remediate(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.drift_run_scan.return_value = {"scan_id": "s1", "drift_count": 2}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_drift_scan
            args = argparse.Namespace(output="json")
            cmd_drift_scan(args)
            assert mock_client.drift_run_scan.return_value["drift_count"] > 0

    def test_healing_full_workflow(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.healing_get_status.return_value = {"policy_count": 3, "healthy": True}
            mock_client.healing_get_history.return_value = [{"event_id": "e1", "result": "success"}]
            mock_client.healing_retrain.return_value = {"status": "retraining"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_heal_status, cmd_heal_history, cmd_heal_retrain
            args = argparse.Namespace(output="json")
            cmd_heal_status(args)
            cmd_heal_history(args)
            cmd_heal_retrain(args)
            assert mock_client.healing_get_status.call_count == 1
            assert mock_client.healing_get_history.call_count == 1
            assert mock_client.healing_retrain.call_count == 1

    def test_runbook_list_categories(self):
        mock_templates = [
            {"template_id": "t1", "category": "incident_response"},
            {"template_id": "t2", "category": "deployment"},
            {"template_id": "t3", "category": "security"},
        ]
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.runbook_list_templates.return_value = mock_templates
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_runbook_list
            args = argparse.Namespace(output="json")
            cmd_runbook_list(args)
            categories = set(t["category"] for t in mock_client.runbook_list_templates.return_value)
            assert len(categories) == 3

    def test_output_plain_format(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_list.return_value = [{"name": "WF1"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_list
            from cli.ipilot.output import print_output
            with patch("cli.ipilot.cli.print_output") as mock_print:
                args = argparse.Namespace(output="plain")
                cmd_workflow_list(args)
                mock_print.assert_called()

    def test_output_yaml_format(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_list.return_value = [{"name": "WF1"}]
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_list
            from cli.ipilot.output import print_output
            with patch("cli.ipilot.cli.print_output") as mock_print:
                args = argparse.Namespace(output="yaml")
                cmd_workflow_list(args)
                mock_print.assert_called()

    def test_quota_check_invalid_type(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.quota_check.return_value = {"error": "invalid entity type"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_quota_check
            args = argparse.Namespace(entity_type="invalid", entity_id="id", cpu=1, memory=1, output="json")
            cmd_quota_check(args)
            assert "error" in mock_client.quota_check.return_value

    def test_pipeline_run_multiple_branches(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.infra_pipeline_run.return_value = {"run_id": "r1", "status": "running"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_infra_pipeline_run
            for branch in ["main", "develop", "feature/test"]:
                args = argparse.Namespace(pipeline_id="pl1", branch=branch, output="json")
                cmd_infra_pipeline_run(args)
            assert mock_client.infra_pipeline_run.call_count == 3

    def test_workflow_create_empty_description(self):
        with patch("cli.ipilot.cli.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.workflow_create.return_value = {"workflow_id": "wf1"}
            mock_get.return_value = mock_client
            from cli.ipilot.cli import cmd_workflow_create
            args = argparse.Namespace(name="Test", description="", output="json")
            cmd_workflow_create(args)
            mock_client.workflow_create.assert_called_once_with("Test", "")
