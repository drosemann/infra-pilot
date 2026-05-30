"""Tests for Workflow Studio and related orchestration modules."""
import pytest
import json
from datetime import datetime
from cogs.workflow_studio import WorkflowStudio, WorkflowNode, WorkflowEdge, WorkflowExecution
from cogs.infrastructure_pipelines import InfrastructurePipelines, Pipeline, PipelineStage, PipelineRun
from cogs.drift_detector import DriftDetector, DriftResult, DriftScan
from cogs.quota_manager import QuotaManager, Quota, QuotaIncreaseRequest


@pytest.fixture
def workflow_cog(tmp_path):
    from discord.ext import commands
    bot = commands.Bot(command_prefix="!", intents=None)
    data_file = tmp_path / "workflows.json"
    data_file.write_text("[]")
    cog = WorkflowStudio(bot)
    cog.data_file = str(data_file)
    return cog


@pytest.fixture
def pipeline_cog(tmp_path):
    from discord.ext import commands
    bot = commands.Bot(command_prefix="!", intents=None)
    cog = InfrastructurePipelines(bot)
    return cog


@pytest.fixture
def drift_cog(tmp_path):
    from discord.ext import commands
    bot = commands.Bot(command_prefix="!", intents=None)
    cog = DriftDetector(bot)
    return cog


@pytest.fixture
def quota_cog(tmp_path):
    from discord.ext import commands
    bot = commands.Bot(command_prefix="!", intents=None)
    cog = QuotaManager(bot)
    return cog


class TestWorkflowStudio:
    def test_create_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Test Automation", "A test workflow", [], [])
        assert wf["workflow_id"] is not None
        assert wf["name"] == "Test Automation"
        assert wf["status"] == "draft"

    def test_get_workflow(self, workflow_cog):
        original = workflow_cog.create_workflow("Get Test", "Get test", [], [])
        retrieved = workflow_cog.get_workflow(original["workflow_id"])
        assert retrieved["workflow_id"] == original["workflow_id"]

    def test_list_workflows(self, workflow_cog):
        workflow_cog.create_workflow("WF 1", "First", [], [])
        workflow_cog.create_workflow("WF 2", "Second", [], [])
        wfs = workflow_cog.list_workflows()
        assert len(wfs) >= 2

    def test_update_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Original", "Original desc", [], [])
        updated = workflow_cog.update_workflow(wf["workflow_id"], {"name": "Updated", "description": "Updated desc"})
        assert updated["name"] == "Updated"

    def test_delete_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Delete me", "To delete", [], [])
        assert workflow_cog.delete_workflow(wf["workflow_id"]) is True

    def test_activate_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Activate test", "Test", [], [])
        activated = workflow_cog.activate_workflow(wf["workflow_id"])
        assert activated["status"] == "active"

    def test_deactivate_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Deactivate test", "Test", [], [])
        workflow_cog.activate_workflow(wf["workflow_id"])
        deactivated = workflow_cog.deactivate_workflow(wf["workflow_id"])
        assert deactivated["status"] == "inactive"

    def test_execute_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Exec test", "Test execution", [
            {"node_id": "n1", "type": "trigger", "config": {"trigger_type": "manual"}, "position": {"x": 100, "y": 100}},
            {"node_id": "n2", "type": "action", "config": {"action_type": "webhook", "url": "https://example.com/hook"}, "position": {"x": 300, "y": 100}}
        ], [{"edge_id": "e1", "source": "n1", "target": "n2"}])
        workflow_cog.activate_workflow(wf["workflow_id"])
        execution = workflow_cog.execute_workflow(wf["workflow_id"], {"trigger": "manual", "ts": datetime.utcnow().isoformat()})
        assert execution["execution_id"] is not None
        assert execution["status"] in ("running", "completed")

    def test_execute_non_active_workflow(self, workflow_cog):
        wf = workflow_cog.create_workflow("Inactive", "Should not execute", [], [])
        execution = workflow_cog.execute_workflow(wf["workflow_id"], {})
        assert execution is None

    def test_get_node_types(self, workflow_cog):
        types = workflow_cog.get_node_types()
        assert len(types) > 10
        type_names = [t["type"] for t in types]
        assert "trigger" in type_names
        assert "action_webhook" in type_names
        assert "condition" in type_names

    def test_get_execution_history(self, workflow_cog):
        wf = workflow_cog.create_workflow("History test", "Test", [], [])
        workflow_cog.activate_workflow(wf["workflow_id"])
        workflow_cog.execute_workflow(wf["workflow_id"], {})
        history = workflow_cog.get_execution_history(wf["workflow_id"])
        assert len(history) >= 1


class TestInfrastructurePipelines:
    def test_create_pipeline(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("Test Pipe", "A test pipeline", "https://github.com/org/repo", "main")
        assert p["pipeline_id"] is not None
        assert p["name"] == "Test Pipe"
        assert p["status"] == "active"

    def test_get_pipeline(self, pipeline_cog):
        original = pipeline_cog.create_pipeline("Get Pipe", "Test", "https://github.com/org/repo2", "main")
        retrieved = pipeline_cog.get_pipeline(original["pipeline_id"])
        assert retrieved["pipeline_id"] == original["pipeline_id"]

    def test_run_pipeline(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("Run Pipe", "Test run", "https://github.com/org/repo3", "main")
        run = pipeline_cog.run_pipeline(p["pipeline_id"], {"triggered_by": "manual", "commit_sha": "abc123"})
        assert run["run_id"] is not None
        assert run["status"] == "running"
        assert run["stage"] == "validate"

    def test_get_run(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("Run Get", "Test", "https://github.com/org/repo4", "main")
        run = pipeline_cog.run_pipeline(p["pipeline_id"], {})
        retrieved = pipeline_cog.get_run(run["run_id"])
        assert retrieved["run_id"] == run["run_id"]

    def test_list_pipeline_runs(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("List Runs", "Test", "https://github.com/org/repo5", "main")
        pipeline_cog.run_pipeline(p["pipeline_id"], {})
        pipeline_cog.run_pipeline(p["pipeline_id"], {})
        runs = pipeline_cog.list_runs(p["pipeline_id"])
        assert len(runs) >= 2

    def test_pipeline_stages(self, pipeline_cog):
        stages = pipeline_cog.get_pipeline_stages()
        assert len(stages) >= 6
        stage_names = [s["name"] for s in stages]
        assert "validate" in stage_names
        assert "lint" in stage_names
        assert "plan" in stage_names
        assert "apply" in stage_names

    def test_approve_pipeline(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("Approve Pipe", "Test", "https://github.com/org/repo6", "main")
        run = pipeline_cog.run_pipeline(p["pipeline_id"], {})
        result = pipeline_cog.approve_run(run["run_id"], "approver-001")
        assert result["stage"] == "lint" or result["approved_by"] == "approver-001"

    def test_reject_pipeline(self, pipeline_cog):
        p = pipeline_cog.create_pipeline("Reject Pipe", "Test", "https://github.com/org/repo7", "main")
        run = pipeline_cog.run_pipeline(p["pipeline_id"], {})
        result = pipeline_cog.reject_run(run["run_id"], "approver-001", "Missing documentation")
        assert result["status"] == "rejected"


class TestDriftDetector:
    def test_run_scan(self, drift_cog):
        scan = drift_cog.run_scan()
        assert scan["scan_id"] is not None
        assert scan["total_resources"] > 0
        assert "drifted_resources" in scan
        assert "compliant_resources" in scan

    def test_get_scan(self, drift_cog):
        scan = drift_cog.run_scan()
        retrieved = drift_cog.get_scan(scan["scan_id"])
        assert retrieved["scan_id"] == scan["scan_id"]

    def test_list_scans(self, drift_cog):
        drift_cog.run_scan()
        drift_cog.run_scan()
        scans = drift_cog.list_scans()
        assert len(scans) >= 2

    def test_get_drift_details(self, drift_cog):
        scan = drift_cog.run_scan()
        details = drift_cog.get_drift_details(scan["scan_id"])
        if scan["drifted_resources"] > 0:
            assert len(details) > 0

    def test_drift_suppression(self, drift_cog):
        result = drift_cog.suppress_drift("resource-001", "Known issue, planned change")
        assert result is True

    def test_list_suppressions(self, drift_cog):
        drift_cog.suppress_drift("res-1", "Planned maintenance")
        drift_cog.suppress_drift("res-2", "Expected drift")
        suppressions = drift_cog.list_suppressions()
        assert len(suppressions) >= 2

    def test_unsuppress_drift(self, drift_cog):
        drift_cog.suppress_drift("res-3", "Temporary")
        result = drift_cog.unsuppress_drift("res-3")
        assert result is True


class TestQuotaManager:
    def test_create_quota(self, quota_cog):
        q = quota_cog.create_quota("team-engineering", "team", "eng-001", {
            "cpu_cores": 32, "memory_gb": 128, "containers": 50, "storage_gb": 2000
        })
        assert q["quota_id"] is not None
        assert q["entity_type"] == "team"
        assert q["limits"]["cpu_cores"] == 32

    def test_get_quota(self, quota_cog):
        original = quota_cog.create_quota("proj-web", "project", "proj-001", {"cpu_cores": 8, "memory_gb": 32})
        retrieved = quota_cog.get_quota(original["quota_id"])
        assert retrieved["quota_id"] == original["quota_id"]

    def test_get_quota_by_entity(self, quota_cog):
        quota_cog.create_quota("team-data", "team", "data-001", {"cpu_cores": 16, "memory_gb": 64})
        q = quota_cog.get_quota_by_entity("team", "data-001")
        assert q is not None
        assert q["entity_id"] == "data-001"

    def test_list_quotas(self, quota_cog):
        quota_cog.create_quota("Quota A", "team", "team-a", {"cpu_cores": 8})
        quota_cog.create_quota("Quota B", "project", "proj-b", {"cpu_cores": 4})
        quotas = quota_cog.list_quotas()
        assert len(quotas) >= 2

    def test_check_quota_within_limits(self, quota_cog):
        quota_cog.create_quota("Check Quota", "team", "check-team", {"cpu_cores": 10, "memory_gb": 40})
        result = quota_cog.check_quota("team", "check-team", {"cpu_cores": 4, "memory_gb": 16})
        assert result["allowed"] is True

    def test_check_quota_exceeded(self, quota_cog):
        quota_cog.create_quota("Limit Quota", "team", "limit-team", {"cpu_cores": 8, "memory_gb": 32})
        result = quota_cog.check_quota("team", "limit-team", {"cpu_cores": 16, "memory_gb": 64})
        assert result["allowed"] is False
        assert "cpu_cores" in result["exceeded"]

    def test_update_quota(self, quota_cog):
        q = quota_cog.create_quota("Update Quota", "team", "upd-team", {"cpu_cores": 8})
        quota_cog.update_quota(q["quota_id"], {"limits": {"cpu_cores": 16}})
        updated = quota_cog.get_quota(q["quota_id"])
        assert updated["limits"]["cpu_cores"] == 16

    def test_delete_quota(self, quota_cog):
        q = quota_cog.create_quota("Delete Quota", "team", "del-team", {"cpu_cores": 4})
        assert quota_cog.delete_quota(q["quota_id"]) is True

    def test_usage_tracking(self, quota_cog):
        q = quota_cog.create_quota("Usage Quota", "project", "usage-proj", {"cpu_cores": 10})
        quota_cog.track_usage("project", "usage-proj", {"cpu_cores": 3})
        quota_cog.track_usage("project", "usage-proj", {"cpu_cores": 2})
        assert q["usage"]["cpu_cores"] == 5

    def test_quota_increase_request(self, quota_cog):
        req = quota_cog.request_increase("team", "inc-team", {"cpu_cores": 24}, "Need more compute for ML workloads")
        assert req["request_id"] is not None
        assert req["status"] == "pending"
        assert req["reason"] == "Need more compute for ML workloads"

    def test_approve_increase(self, quota_cog):
        quota_cog.create_quota("Inc Base", "team", "inc-base", {"cpu_cores": 8})
        req = quota_cog.request_increase("team", "inc-base", {"cpu_cores": 32}, "Need more")
        result = quota_cog.approve_increase(req["request_id"], "admin-001")
        assert result is True
        updated = quota_cog.get_quota_by_entity("team", "inc-base")
        assert updated["limits"]["cpu_cores"] == 32

    def test_deny_increase(self, quota_cog):
        quota_cog.create_quota("Deny Inc", "team", "deny-inc", {"cpu_cores": 8})
        req = quota_cog.request_increase("team", "deny-inc", {"cpu_cores": 64}, "Overreach")
        result = quota_cog.deny_increase(req["request_id"], "admin-001", "Request too large")
        assert result is True
        assert req["status"] == "denied"
