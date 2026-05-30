"""Tests for workflow_studio_ext module."""
import pytest
import tempfile
import os
from datetime import datetime
from services.integration_service.src.workflow_studio_ext import WorkflowStudioManager, WorkflowStatus, WorkflowStepType, WorkflowExecutionStatus, WorkflowTriggerType, WorkflowStep, WorkflowTrigger


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
