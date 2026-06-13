"""Tests for cog_data_masking module."""
import pytest
from services.orchestrator_agent.cogs.data_platform.cog_data_masking import CogDataMasking

@pytest.fixture
def cog():
    return CogDataMasking()

class TestCogMasking:
    def test_list_rules(self, cog):
        result = cog.list_rules()
        assert isinstance(result, list)

    def test_create_rule(self, cog):
        result = cog.create_rule(name="hide-ssn", column_pattern="ssn", method="hash", severity="critical")
        assert result["name"] == "hide-ssn"

    def test_list_profiles(self, cog):
        result = cog.list_profiles()
        assert isinstance(result, list)

    def test_create_profile(self, cog):
        r = cog.create_rule(name="email-rule", column_pattern="email", method="redact", severity="high")
        result = cog.create_profile(name="pii", targets=["users", "customers"], rule_ids=[r["rule_id"]])
        assert result["name"] == "pii"

    def test_apply(self, cog):
        r = cog.create_rule(name="apply-rule", column_pattern="email", method="redact", severity="high")
        p = cog.create_profile(name="apply-profile", targets=["users"], rule_ids=[r["rule_id"]])
        result = cog.apply(p["profile_id"])
        assert result["status"] == "applied"

    def test_deploy(self, cog):
        result = cog.deploy(name="dep-profile", targets="users,orders", rules="email,ssn", methods="redact,hash")
        assert result["name"] == "dep-profile"

    def test_monitor(self, cog):
        result = cog.monitor(target="users")
        assert "total_rows_masked" in result
