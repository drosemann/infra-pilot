"""Tests for cog_data_quality module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_data_quality import CogDataQuality

@pytest.fixture
def cog():
    return CogDataQuality()

class TestCogQuality:
    def test_list(self, cog):
        result = cog.list_rules()
        assert isinstance(result, list)

    def test_create_rule(self, cog):
        result = cog.create_rule(name="non-null-email", dataset="users", column="email", check_type="not_null", severity="high")
        assert result["name"] == "non-null-email"

    def test_run(self, cog):
        cog.create_rule(name="test-rule", dataset="users", column="email", check_type="not_null", severity="high")
        result = cog.run()
        assert result["total"] >= 1

    def test_violations(self, cog):
        cog.create_rule(name="v-test", dataset="users", column="email", check_type="not_null", severity="high")
        cog.run()
        result = cog.get_violations()
        assert isinstance(result, list)

    def test_scorecard(self, cog):
        cog.create_rule(name="s-test", dataset="users", column="email", check_type="not_null")
        result = cog.get_scorecard("users")
        assert result["dataset"] == "users"

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-test", dataset="orders", column="amount", check_type="range", severity="medium", schedule="hourly")
        assert result["name"] == "dep-test"

    def test_monitor(self, cog):
        cog.create_rule(name="mon-test", dataset="users", column="email", check_type="not_null", severity="high")
        result = cog.monitor("users")
        assert result["dataset"] == "users"
