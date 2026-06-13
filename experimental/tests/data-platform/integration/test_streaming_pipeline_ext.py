"""Tests for streaming_pipeline module."""
import pytest
from services.integration_service.src.data_platform.streaming_pipeline import (
    StreamingManager, StreamingCluster, Topic, ScaleResult
)

@pytest.fixture
def manager():
    mgr = StreamingManager()
    yield mgr
    mgr._clusters.clear()

class TestClusterCRUD:
    def test_create_cluster(self, manager):
        c = manager.create_cluster(name="prod-stream", provider="kafka", nodes=3)
        assert c.cluster_id is not None
        assert c.name == "prod-stream"
        assert c.provider == "kafka"
        assert c.nodes == 3

    def test_get_cluster(self, manager):
        c = manager.create_cluster(name="test", provider="redpanda", nodes=5)
        retrieved = manager.get_cluster(c.cluster_id)
        assert retrieved is not None

    def test_delete_cluster(self, manager):
        c = manager.create_cluster(name="del", provider="kafka", nodes=1)
        assert manager.delete_cluster(c.cluster_id) is True

    def test_list_clusters(self, manager):
        manager.create_cluster(name="c1", provider="kafka", nodes=3)
        manager.create_cluster(name="c2", provider="redpanda", nodes=5)
        assert len(manager.list_clusters()) >= 2

class TestTopicOperations:
    def test_create_topic(self, manager):
        c = manager.create_cluster(name="t", provider="kafka", nodes=3)
        topic = manager.create_topic(c.cluster_id, name="events", partitions=6, replication=3)
        assert topic.name == "events"
        assert topic.partitions == 6

    def test_delete_topic(self, manager):
        c = manager.create_cluster(name="t", provider="kafka", nodes=3)
        topic = manager.create_topic(c.cluster_id, name="del-topic", partitions=3, replication=1)
        assert manager.delete_topic(c.cluster_id, topic.name) is True

class TestClusterOps:
    def test_scale_cluster(self, manager):
        c = manager.create_cluster(name="s", provider="kafka", nodes=3)
        result = manager.scale_cluster(c.cluster_id, nodes=5)
        assert result.nodes == 5
        assert result.status == "scaled"
