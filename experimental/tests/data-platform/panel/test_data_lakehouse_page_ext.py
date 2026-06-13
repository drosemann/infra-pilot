"""Tests for DataLakehousePage component."""
import pytest
from unittest.mock import patch

class TestDataLakehousePage:
    def test_page_render(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        assert DataLakehousePage is not None

    def test_cluster_state(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        page = DataLakehousePage()
        assert hasattr(page, "clusters")
        assert isinstance(page.clusters, list)

    def test_create_cluster(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        page = DataLakehousePage()
        initial = len(page.clusters)
        page.create_cluster("test", "spark", "us-east-1")
        assert len(page.clusters) == initial + 1

    def test_delete_cluster(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        page = DataLakehousePage()
        page.create_cluster("del", "trino", "eu-west-1")
        cluster_id = page.clusters[0]["cluster_id"]
        page.delete_cluster(cluster_id)
        ids = [c["cluster_id"] for c in page.clusters]
        assert cluster_id not in ids

    def test_compact_table(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        page = DataLakehousePage()
        result = page.compact_table("tbl-001")
        assert result["status"] == "compacted"

    def test_vacuum_table(self):
        from services.management_panel.src.pages.data_platform.DataLakehousePage import DataLakehousePage
        page = DataLakehousePage()
        result = page.vacuum_table("tbl-001", 168)
        assert result["retention_hours"] == 168
