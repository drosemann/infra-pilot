"""Tests for cog_streaming_pipeline module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_streaming_pipeline import CogStreamingPipeline

@pytest.fixture
def cog():
    return CogStreamingPipeline()

class TestCogStreaming:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_create(self, cog):
        result = cog.create(name="prod-stream", provider="kafka", nodes=3)
        assert result["name"] == "prod-stream"
        assert result["nodes"] == 3

    def test_get(self, cog):
        created = cog.create(name="get-test", provider="redpanda", nodes=5)
        result = cog.get(created["cluster_id"])
        assert result["cluster_id"] == created["cluster_id"]

    def test_delete(self, cog):
        created = cog.create(name="del-test", provider="kafka", nodes=1)
        assert cog.delete(created["cluster_id"]) is True

    def test_create_topic(self, cog):
        created = cog.create(name="topic-test", provider="kafka", nodes=3)
        result = cog.create_topic(created["cluster_id"], "events", partitions=6, replication=3)
        assert result["topic"] == "events"

    def test_delete_topic(self, cog):
        created = cog.create(name="dt-test", provider="kafka", nodes=3)
        cog.create_topic(created["cluster_id"], "to-del", partitions=3, replication=1)
        assert cog.delete_topic(created["cluster_id"], "to-del") is True

    def test_scale(self, cog):
        created = cog.create(name="s-test", provider="kafka", nodes=3)
        result = cog.scale(created["cluster_id"], nodes=5)
        assert result["nodes"] == 5

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-test", provider="kafka", nodes=3, topics=5, partitions_per_topic=6)
        assert result["name"] == "dep-test"

    def test_monitor(self, cog):
        created = cog.create(name="mon-test", provider="kafka", nodes=3)
        result = cog.monitor(created["cluster_id"])
        assert result["cluster_id"] == created["cluster_id"]
