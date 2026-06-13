"""Tests for PipelineObservabilityPage component."""
import pytest
from services.management_panel.src.pages.data_platform.PipelineObservabilityPage import PipelineObservabilityPage

class TestPipelineObservabilityPage:
    def test_page_render(self):
        assert PipelineObservabilityPage is not None

    def test_pipelines_state(self):
        page = PipelineObservabilityPage()
        assert hasattr(page, "pipelines")

    def test_create_pipeline(self):
        page = PipelineObservabilityPage()
        n = len(page.pipelines)
        page.create_pipeline("etl-users", "0 */6 * * *")
        assert len(page.pipelines) == n + 1

    def test_start_stop(self):
        page = PipelineObservabilityPage()
        page.create_pipeline("test", "0 * * * *")
        pid = page.pipelines[0]["pipeline_id"]
        start_result = page.start_pipeline(pid)
        assert start_result["status"] == "running"
        stop_result = page.stop_pipeline(pid)
        assert stop_result["status"] == "stopped"

    def test_health(self):
        page = PipelineObservabilityPage()
        page.create_pipeline("health-test", "0 * * * *")
        result = page.get_health(page.pipelines[0]["pipeline_id"])
        assert "health" in result

    def test_rca(self):
        page = PipelineObservabilityPage()
        page.create_pipeline("rca-test", "0 * * * *")
        result = page.get_rca(page.pipelines[0]["pipeline_id"])
        assert len(result["root_causes"]) > 0
