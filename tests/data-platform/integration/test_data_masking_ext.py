"""Tests for data_masking module."""
import pytest
from services.integration_service.src.data_platform.data_masking import (
    MaskingManager, MaskingRule, MaskingProfile, MaskingResult
)

@pytest.fixture
def manager():
    mgr = MaskingManager()
    yield mgr
    mgr._rules.clear()
    mgr._profiles.clear()

class TestRuleCRUD:
    def test_create_rule(self, manager):
        r = manager.create_rule(name="hide-email", column_pattern="email", method="redact", severity="high")
        assert r.rule_id is not None
        assert r.method == "redact"

    def test_list_rules(self, manager):
        manager.create_rule(name="r1", column_pattern="email", method="redact")
        manager.create_rule(name="r2", column_pattern="ssn", method="hash")
        assert len(manager.list_rules()) >= 2

class TestProfileCRUD:
    def test_create_profile(self, manager):
        r = manager.create_rule(name="email-rule", column_pattern="email", method="redact")
        p = manager.create_profile(name="pii-profile", targets=["users", "customers"], rule_ids=[r.rule_id])
        assert p.profile_id is not None
        assert p.name == "pii-profile"
        assert len(p.rule_ids) == 1

    def test_list_profiles(self, manager):
        manager.create_profile(name="p1", targets=["users"], rule_ids=[])
        manager.create_profile(name="p2", targets=["orders"], rule_ids=[])
        assert len(manager.list_profiles()) >= 2

class TestApplication:
    def test_apply_profile(self, manager):
        r = manager.create_rule(name="email-rule", column_pattern="email", method="redact")
        p = manager.create_profile(name="pii-profile", targets=["users"], rule_ids=[r.rule_id])
        result = manager.apply_profile(p.profile_id)
        assert isinstance(result, MaskingResult)
        assert result.total_rows_masked > 0
