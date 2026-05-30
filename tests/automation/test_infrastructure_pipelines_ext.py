"""Tests for infrastructure_pipelines_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.infrastructure_pipelines_ext import InfrastructurePipelinesManager, PipelineProvider, PipelineStatus, DeploymentStrategy, StageStatus


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
