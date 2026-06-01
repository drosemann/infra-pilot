"""Tests for Policy as Code Engine."""
import pytest
import json
from policy_engine import PolicyEngine, PolicyRule, PolicyResult, RegoEvaluator


@pytest.fixture
def engine():
    return PolicyEngine({
        "policies_dir": "/tmp/policies",
        "default_decision": "allow",
        "max_evaluation_depth": 10,
        "cache_ttl": 300
    })


class TestPolicyLifecycle:
    def test_create_policy(self, engine):
        policy = engine.create_policy(
            name="require_mfa",
            description="Require MFA for all admin actions",
            category="security",
            enabled=True,
            rules=[
                {"id": "mfa-1", "effect": "require", "resource": "admin:*", "condition": {"action": "delete"}}
            ]
        )
        assert policy.policy_id is not None
        assert policy.name == "require_mfa"
        assert policy.enabled is True

    def test_get_policy(self, engine):
        original = engine.create_policy("test_policy", "Test", "general", True, [])
        retrieved = engine.get_policy(original.policy_id)
        assert retrieved.policy_id == original.policy_id

    def test_get_missing_policy(self, engine):
        assert engine.get_policy("nonexistent") is None

    def test_update_policy(self, engine):
        policy = engine.create_policy("update_test", "Original desc", "security", True, [])
        engine.update_policy(policy.policy_id, {"description": "Updated description", "enabled": False})
        assert policy.description == "Updated description"
        assert policy.enabled is False

    def test_delete_policy(self, engine):
        policy = engine.create_policy("delete_test", "To be deleted", "general", True, [])
        assert engine.delete_policy(policy.policy_id) is True
        assert engine.get_policy(policy.policy_id) is None

    def test_list_policies(self, engine):
        engine.create_policy("policy_1", "First", "security", True, [])
        engine.create_policy("policy_2", "Second", "compliance", True, [])
        engine.create_policy("policy_3", "Third", "security", False, [])
        all_policies = engine.list_policies()
        assert len(all_policies) >= 3
        security_policies = engine.list_policies(category="security")
        assert len(security_policies) >= 2
        enabled = engine.list_policies(enabled_only=True)
        assert all(p.enabled for p in enabled)


class TestPolicyEvaluation:
    def test_evaluate_allow(self, engine):
        engine.create_policy("allow_test", "Allow test", "security", True, [
            {"id": "rule-1", "effect": "allow", "resource": "server:*", "condition": {"action": "read"}}
        ])
        result = engine.evaluate("server:web-01", "read", {"user": "alice", "role": "viewer"})
        assert result.decision == "allow"

    def test_evaluate_deny(self, engine):
        engine.create_policy("deny_test", "Deny test", "security", True, [
            {"id": "rule-2", "effect": "deny", "resource": "server:*", "condition": {"action": "delete"}}
        ])
        result = engine.evaluate("server:db-01", "delete", {"user": "bob", "role": "viewer"})
        assert result.decision == "deny"

    def test_evaluate_require_mfa(self, engine):
        engine.create_policy("mfa_policy", "MFA required", "security", True, [
            {"id": "mfa-1", "effect": "require_mfa", "resource": "admin:*", "condition": {}}
        ])
        result = engine.evaluate("admin:users", "delete", {"user": "admin", "mfa_verified": False})
        assert result.decision == "require_mfa"

    def test_deny_overrides_allow(self, engine):
        engine.create_policy("mixed", "Mixed rules - deny wins", "security", True, [
            {"id": "allow-all", "effect": "allow", "resource": "*", "condition": {}},
            {"id": "deny-prod", "effect": "deny", "resource": "server:prod-*", "condition": {"action": "delete"}}
        ])
        result = engine.evaluate("server:prod-db", "delete", {"user": "admin"})
        assert result.decision == "deny"

    def test_evaluate_multiple_matching_policies(self, engine):
        engine.create_policy("security_rules", "Security", "security", True, [
            {"id": "block-night", "effect": "deny", "resource": "server:*", "condition": {"time": "night"}}
        ])
        engine.create_policy("compliance_rules", "Compliance", "compliance", True, [
            {"id": "require-logging", "effect": "require", "resource": "server:*", "condition": {}}
        ])
        result = engine.evaluate("server:web-01", "write", {"user": "deploy", "time": "night"})
        assert result.decision in ("deny", "require")

    def test_evaluate_no_matching_policy(self, engine):
        result = engine.evaluate("unknown:resource", "action", {"user": "test"})
        assert result.decision == "allow"
        assert len(result.matched_rules) == 0

    def test_evaluate_single_rule(self, engine):
        result = engine.evaluate_single_rule(
            {"id": "test-rule", "effect": "deny", "resource": "server:*", "condition": {"env": "production"}},
            "server:web-01", "stop", {"env": "production"}
        )
        assert result.matched is True
        assert result.decision == "deny"

    def test_evaluate_single_rule_no_match(self, engine):
        result = engine.evaluate_single_rule(
            {"id": "test-rule", "effect": "deny", "resource": "server:*", "condition": {"env": "production"}},
            "server:web-01", "start", {"env": "staging"}
        )
        assert result.matched is False


class TestRBACPolicies:
    def test_admin_can_do_anything(self, engine):
        engine.create_policy("rbac_admin", "Admin RBAC", "rbac", True, [
            {"id": "admin-all", "effect": "allow", "resource": "*", "condition": {"role": "admin"}}
        ])
        result = engine.evaluate("any:resource", "any_action", {"role": "admin"})
        assert result.decision == "allow"

    def test_viewer_read_only(self, engine):
        engine.create_policy("rbac_viewer", "Viewer RBAC", "rbac", True, [
            {"id": "viewer-read", "effect": "allow", "resource": "*", "condition": {"role": "viewer", "action": "read"}},
            {"id": "viewer-no-write", "effect": "deny", "resource": "*", "condition": {"role": "viewer", "action__in": ["write", "delete", "update"]}}
        ])
        read_result = engine.evaluate("server:web-01", "read", {"role": "viewer"})
        assert read_result.decision == "allow"
        write_result = engine.evaluate("server:web-01", "write", {"role": "viewer"})
        assert write_result.decision == "deny"

    def test_operator_limited_access(self, engine):
        engine.create_policy("rbac_operator", "Operator RBAC", "rbac", True, [
            {"id": "op-server", "effect": "allow", "resource": "server:*", "condition": {"role": "operator"}},
            {"id": "op-no-billing", "effect": "deny", "resource": "billing:*", "condition": {"role": "operator"}}
        ])
        assert engine.evaluate("server:web-01", "restart", {"role": "operator"}).decision == "allow"
        assert engine.evaluate("billing:invoice", "read", {"role": "operator"}).decision == "deny"


class TestQuotaPolicies:
    def test_enforce_cpu_quota(self, engine):
        engine.create_policy("cpu_quota", "CPU limits", "quota", True, [
            {"id": "cpu-limit", "effect": "deny", "resource": "compute:instance", "condition": {"usage.cpu": {"gt": 16}}}
        ])
        result = engine.evaluate("compute:instance", "create", {"usage": {"cpu": 20}, "user": "dev"})
        assert result.decision == "deny"

    def test_under_quota_allowed(self, engine):
        engine.create_policy("cpu_quota", "CPU limits", "quota", True, [
            {"id": "cpu-limit", "effect": "deny", "resource": "compute:instance", "condition": {"usage.cpu": {"gt": 16}}}
        ])
        result = engine.evaluate("compute:instance", "create", {"usage": {"cpu": 4}, "user": "dev"})
        assert result.decision == "allow"


class TestCostControlPolicies:
    def test_monthly_budget_exceeded(self, engine):
        engine.create_policy("cost_control", "Budget limits", "cost", True, [
            {"id": "budget-limit", "effect": "deny", "resource": "compute:*", "condition": {"budget.monthly_spend": {"gt": 10000}}}
        ])
        result = engine.evaluate("compute:instance", "create", {"budget": {"monthly_spend": 12000}, "team": "engineering"})
        assert result.decision == "deny"

    def test_within_budget_allowed(self, engine):
        engine.create_policy("cost_control", "Budget limits", "cost", True, [
            {"id": "budget-limit", "effect": "deny", "resource": "compute:*", "condition": {"budget.monthly_spend": {"gt": 10000}}}
        ])
        result = engine.evaluate("compute:instance", "create", {"budget": {"monthly_spend": 5000}, "team": "engineering"})
        assert result.decision == "allow"


class TestRegoEvaluator:
    def test_decompress_rule(self, engine):
        evaluator = RegoEvaluator({})
        rule = {"id": "test", "effect": "deny", "resource": "server:*", "condition": {"env": "production"}}
        decompressed = evaluator.decompress_conditions(rule)
        assert "condition" in decompressed

    def test_match_resource(self, engine):
        evaluator = RegoEvaluator({})
        assert evaluator.match_resource("server:*", "server:web-01") is True
        assert evaluator.match_resource("server:web-*", "server:web-01") is True
        assert evaluator.match_resource("server:web-01", "server:web-02") is False
        assert evaluator.match_resource("*", "anything:value") is True
        assert evaluator.match_resource("compute:*", "server:web-01") is False

    def test_match_condition(self, engine):
        evaluator = RegoEvaluator({})
        assert evaluator.match_condition({"env": "production"}, {"env": "production"}) is True
        assert evaluator.match_condition({"env": "production"}, {"env": "staging"}) is False
        assert evaluator.match_condition({}, {"anything": "value"}) is True

    def test_match_nested_condition(self, engine):
        evaluator = RegoEvaluator({})
        condition = {"usage.cpu": {"gt": 16}}
        context = {"usage": {"cpu": 20}}
        assert evaluator.match_condition(condition, context) is True
        context2 = {"usage": {"cpu": 8}}
        assert evaluator.match_condition(condition, context2) is False


class TestPolicySync:
    def test_export_policies(self, engine):
        engine.create_policy("policy_a", "Desc A", "security", True, [{"id": "r1", "effect": "allow", "resource": "*", "condition": {}}])
        engine.create_policy("policy_b", "Desc B", "compliance", False, [])
        exported = engine.export_policies()
        assert len(exported) >= 2

    def test_import_policies(self, engine):
        policies_data = [
            {"name": "imported_1", "description": "Imported", "category": "security", "enabled": True, "rules": []},
            {"name": "imported_2", "description": "Imported 2", "category": "cost", "enabled": True, "rules": [{"id": "ir1", "effect": "deny", "resource": "compute:*", "condition": {}}]}
        ]
        count = engine.import_policies(policies_data)
        assert count == 2
        assert engine.get_policy_by_name("imported_1") is not None
