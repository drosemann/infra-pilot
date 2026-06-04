"""Tests for cog_pipeline_observability module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_pipeline_observability import CogPipelineObservability

@pytest.fixture
def cog():
    return CogPipelineObservability()

class TestCogPipeline:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_create(self, cog):
        result = cog.create(name="etl-users", schedule="0 */6 * * *")
        assert result["name"] == "etl-users"

    def test_start(self, cog):
        p = cog.create(name="start-test", schedule="0 * * * *")
        result = cog.start(p["pipeline_id"])
        assert result["status"] == "running"

    def test_stop(self, cog):
        p = cog.create(name="stop-test", schedule="0 * * * *")
        cog.start(p["pipeline_id"])
        result = cog.stop(p["pipeline_id"])
        assert result["status"] == "stopped"

    def test_health(self, cog):
        p = cog.create(name="health-test", schedule="0 * * * *")
        result = cog.health(p["pipeline_id"])
        assert "health" in result

    def test_rca(self, cog):
        p = cog.create(name="rca-test", schedule="0 * * * *")
        result = cog.rca(p["pipeline_id"])
        assert len(result["root_causes"]) > 0

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-pipeline", schedule="0 */12 * * *", nodes="source_db,transform,sink_warehouse")
        assert result["name"] == "dep-pipeline"

    def test_monitor(self, cog):
        p = cog.create(name="mon-pipeline", schedule="0 * * * *")
        result = cog.monitor(p["pipeline_id"])
        assert result["pipeline_id"] == p["pipeline_id"]
