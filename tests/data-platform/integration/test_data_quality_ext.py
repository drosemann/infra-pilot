"""Tests for data_quality module."""
import pytest
from services.integration_service.src.data_platform.data_quality import (
    QualityManager, QualityRule, Violation, Scorecard
)

@pytest.fixture
def manager():
    mgr = QualityManager()
    yield mgr
    mgr._rules.clear()
    mgr._violations.clear()

class TestRuleCRUD:
    def test_create_rule(self, manager):
        r = manager.create_rule(name="non-null-check", dataset="users", column="email", check_type="not_null", severity="high")
        assert r.rule_id is not None
        assert r.name == "non-null-check"

    def test_list_rules(self, manager):
        manager.create_rule(name="r1", dataset="users", column="email", check_type="not_null")
        manager.create_rule(name="r2", dataset="orders", column="amount", check_type="range")
        assert len(manager.list_rules()) >= 2

class TestValidation:
    def test_run_validation(self, manager):
        manager.create_rule(name="check", dataset="users", column="email", check_type="not_null", severity="high")
        result = manager.run_validation()
        assert result.total >= 1
        assert result.passed + result.failed == result.total

    def test_get_violations(self, manager):
        manager.create_rule(name="check", dataset="users", column="email", check_type="not_null", severity="high")
        manager.run_validation()
        violations = manager.get_violations()
        assert isinstance(violations, list)

class TestScorecard:
    def test_get_scorecard(self, manager):
        manager.create_rule(name="r1", dataset="users", column="email", check_type="not_null")
        scorecard = manager.get_scorecard("users")
        assert scorecard.dataset == "users"
        assert 0 <= scorecard.overall_score <= 100
