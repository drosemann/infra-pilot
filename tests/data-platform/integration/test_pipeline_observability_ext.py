"""Tests for pipeline_observability module."""
import pytest
from services.integration_service.src.data_platform.pipeline_observability import (
    PipelineManager, Pipeline, PipelineNode, PipelineHealth, PipelineRCA
)

@pytest.fixture
def manager():
    mgr = PipelineManager()
    yield mgr
    mgr._pipelines.clear()

class TestPipelineCRUD:
    def test_create_pipeline(self, manager):
        p = manager.create_pipeline(name="etl-users", schedule="0 */6 * * *")
        assert p.pipeline_id is not None
        assert p.name == "etl-users"
        assert p.status == "created"

    def test_get_pipeline(self, manager):
        p = manager.create_pipeline(name="test", schedule="0 0 * * *")
        retrieved = manager.get_pipeline(p.pipeline_id)
        assert retrieved is not None

    def test_list_pipelines(self, manager):
        manager.create_pipeline(name="p1", schedule="0 * * * *")
        manager.create_pipeline(name="p2", schedule="*/30 * * * *")
        assert len(manager.list_pipelines()) >= 2

class TestLifecycle:
    def test_start_pipeline(self, manager):
        p = manager.create_pipeline(name="start-test", schedule="0 * * * *")
        result = manager.start_pipeline(p.pipeline_id)
        assert result.status == "running"

    def test_stop_pipeline(self, manager):
        p = manager.create_pipeline(name="stop-test", schedule="0 * * * *")
        manager.start_pipeline(p.pipeline_id)
        result = manager.stop_pipeline(p.pipeline_id)
        assert result.status == "stopped"

class TestHealth:
    def test_get_health(self, manager):
        p = manager.create_pipeline(name="health-test", schedule="0 * * * *")
        health = manager.get_health(p.pipeline_id)
        assert isinstance(health, PipelineHealth)
        assert health.health in ("healthy", "degraded", "down")

    def test_health_metrics(self, manager):
        p = manager.create_pipeline(name="metrics-test", schedule="0 * * * *")
        health = manager.get_health(p.pipeline_id)
        assert health.throughput > 0
        assert health.latency_ms >= 0

class TestRCA:
    def test_get_rca(self, manager):
        p = manager.create_pipeline(name="rca-test", schedule="0 * * * *")
        rca = manager.get_rca(p.pipeline_id)
        assert isinstance(rca, PipelineRCA)
        assert len(rca.root_causes) > 0
