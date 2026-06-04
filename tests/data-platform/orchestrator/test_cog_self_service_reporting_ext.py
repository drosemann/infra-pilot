"""Tests for cog_self_service_reporting module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_self_service_reporting import CogSelfServiceReporting

@pytest.fixture
def cog():
    return CogSelfServiceReporting()

class TestCogReporting:
    def test_list(self, cog):
        result = cog.list()
        assert isinstance(result, list)

    def test_create(self, cog):
        result = cog.create(name="monthly-sales", description="Monthly sales report", mode="visual")
        assert result["name"] == "monthly-sales"

    def test_execute(self, cog):
        r = cog.create(name="exec-test", description="test", mode="visual")
        result = cog.execute(r["report_id"])
        assert result["status"] == "executed"

    def test_export(self, cog):
        r = cog.create(name="export-test", description="test", mode="visual")
        result = cog.export(r["report_id"], format="pdf")
        assert result["format"] == "pdf"

    def test_schedule(self, cog):
        r = cog.create(name="sched-test", description="test", mode="visual")
        result = cog.schedule(r["report_id"], frequency="daily", recipients=["admin@co.com"], format="pdf")
        assert result["frequency"] == "daily"

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-report", description="Deployed report", mode="sql", schedule="weekly", recipients="team@co.com")
        assert result["name"] == "dep-report"

    def test_monitor(self, cog):
        r = cog.create(name="mon-report", description="test", mode="visual")
        result = cog.monitor(r["report_id"])
        assert result["report_id"] == r["report_id"]
