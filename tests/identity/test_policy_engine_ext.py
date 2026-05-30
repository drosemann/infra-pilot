"""Tests for policy_engine_ext module."""
import pytest
import tempfile
import os
from datetime import datetime
from services.integration_service.src.policy_engine_ext import PolicyEngine, PolicyDefinition, PolicyMode, PolicyDecision


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = PolicyEngine(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestPolicyManagement:
    def test_create_policy(self, manager):
        policy = manager.create_policy(
            name="require_mfa",
            description="Require MFA for all cloud console access",
            mode=PolicyMode.ENFORCING,
            rego_policy="package auth\n\ndefault allow = false\n\nallow { input.mfa_verified == true }",
        )
        assert policy.policy_id is not None
        assert policy.name == "require_mfa"
        assert policy.mode == PolicyMode.ENFORCING
        assert policy.enabled == True

    def test_get_policy(self, manager):
        policy = manager.create_policy(name="test", description="test", mode=PolicyMode.ENFORCING, rego_policy="package test\nallow = true")
        retrieved = manager.get_policy(policy.policy_id)
        assert retrieved is not None
        assert retrieved.policy_id == policy.policy_id

    def test_update_policy(self, manager):
        policy = manager.create_policy(name="test", description="test", mode=PolicyMode.MONITOR, rego_policy="package test")
        updated = manager.update_policy(policy.policy_id, {"name": "updated", "mode": PolicyMode.ENFORCING})
        assert updated.name == "updated"
        assert updated.mode == PolicyMode.ENFORCING

    def test_delete_policy(self, manager):
        policy = manager.create_policy(name="test", description="test", mode=PolicyMode.ENFORCING, rego_policy="package test")
        assert manager.delete_policy(policy.policy_id) == True
        assert manager.get_policy(policy.policy_id) is None

    def test_list_policies(self, manager):
        manager.create_policy(name="p1", description="d1", mode=PolicyMode.ENFORCING, rego_policy="package p1")
        manager.create_policy(name="p2", description="d2", mode=PolicyMode.MONITOR, rego_policy="package p2")
        policies = manager.list_policies()
        assert len(policies) >= 2


class TestRegoEvaluation:
    def test_evaluate_rego_allow(self, manager):
        policy = manager.create_policy(name="mfa_check", description="MFA required", mode=PolicyMode.ENFORCING, rego_policy="package auth\n\ndefault allow = false\n\nallow { input.mfa_verified == true }")
        input_data = {"user": "user1", "action": "console_login", "resource": "aws:console", "mfa_verified": True}
        result = manager.evaluate_rego(policy.policy_id, input_data)
        assert result["allow"] == True

    def test_evaluate_rego_deny(self, manager):
        policy = manager.create_policy(name="mfa_check", description="MFA required", mode=PolicyMode.ENFORCING, rego_policy="package auth\n\ndefault allow = false\n\nallow { input.mfa_verified == true }")
        input_data = {"user": "user1", "action": "console_login", "resource": "aws:console", "mfa_verified": False}
        result = manager.evaluate_rego(policy.policy_id, input_data)
        assert result["allow"] == False

    def test_evaluate_rego_admin_only(self, manager):
        policy = manager.create_policy(name="admin_only", description="Only admins can delete", mode=PolicyMode.ENFORCING, rego_policy="package admin\n\ndefault allow = false\n\nallow { input.role == \"admin\" }")
        input_admin = {"user": "admin1", "action": "delete", "resource": "server-01", "role": "admin"}
        input_user = {"user": "user1", "action": "delete", "resource": "server-01", "role": "user"}
        assert manager.evaluate_rego(policy.policy_id, input_admin)["allow"] == True
        assert manager.evaluate_rego(policy.policy_id, input_user)["allow"] == False


class TestPolicyDecisions:
    def test_make_decision_allow(self, manager):
        policy = manager.create_policy(name="test", description="test", mode=PolicyMode.ENFORCING, rego_policy="package test\nallow = true")
        decision = manager.make_decision("user1", "view", "resource:server", {"role": "viewer"})
        assert decision is not None
        assert decision.decision in ("allow", "deny")

    def test_get_decision_history(self, manager):
        manager.make_decision("u1", "view", "resource:r1", {"role": "viewer"})
        manager.make_decision("u1", "delete", "resource:r1", {"role": "admin"})
        history = manager.get_decision_history(user_id="u1")
        assert len(history) >= 2


class TestBundleManagement:
    def test_create_bundle(self, manager):
        bundle = manager.create_bundle(
            name="security_baseline",
            description="Baseline security policies",
            policy_ids=[],
        )
        assert bundle.bundle_id is not None
        assert bundle.name == "security_baseline"

    def test_add_policy_to_bundle(self, manager):
        policy = manager.create_policy(name="test", description="test", mode=PolicyMode.ENFORCING, rego_policy="package test")
        bundle = manager.create_bundle(name="bundle1", description="b1", policy_ids=[])
        updated = manager.add_policy_to_bundle(bundle.bundle_id, policy.policy_id)
        assert updated is not None
        assert policy.policy_id in updated.policy_ids


class TestEdgeCases:
    def test_evaluate_nonexistent_policy(self, manager):
        with pytest.raises(ValueError):
            manager.evaluate_rego("nonexistent", {})

    def test_make_decision_no_policies(self, manager):
        decision = manager.make_decision("user1", "view", "resource:server", {})
        assert decision is not None

    def test_statistics(self, manager):
        stats = manager.get_statistics()
        assert stats["total_policies"] >= 0
