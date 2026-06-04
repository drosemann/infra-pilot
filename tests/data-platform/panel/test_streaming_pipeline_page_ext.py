"""Tests for StreamingPipelinePage component."""
import pytest
from services.management_panel.src.pages.data_platform.StreamingPipelinePage import StreamingPipelinePage

class TestStreamingPipelinePage:
    def test_page_render(self):
        assert StreamingPipelinePage is not None

    def test_cluster_state(self):
        page = StreamingPipelinePage()
        assert hasattr(page, "clusters")

    def test_create_cluster(self):
        page = StreamingPipelinePage()
        n = len(page.clusters)
        page.create_cluster("test", "kafka", 3)
        assert len(page.clusters) == n + 1

    def test_delete_cluster(self):
        page = StreamingPipelinePage()
        page.create_cluster("del", "kafka", 1)
        cid = page.clusters[0]["cluster_id"]
        page.delete_cluster(cid)
        assert cid not in [c["cluster_id"] for c in page.clusters]

    def test_create_topic(self):
        page = StreamingPipelinePage()
        page.create_cluster("tc", "kafka", 3)
        cid = page.clusters[0]["cluster_id"]
        result = page.create_topic(cid, "events", 6, 3)
        assert result["topic"] == "events"

    def test_scale_cluster(self):
        page = StreamingPipelinePage()
        page.create_cluster("sc", "kafka", 3)
        cid = page.clusters[0]["cluster_id"]
        result = page.scale_cluster(cid, 5)
        assert result["nodes"] == 5
