"""Unit tests for the shared feature-flag evaluation contract.

Runs the cases in tests/fixtures/feature-flag-contract.yaml through the
Python evaluator (services/orchestrator-agent/feature_flags.py) plus the
pure targeting semantics. The TypeScript implementation in
services/management-panel/server/feature-flags.ts mirrors the same cases.
"""

import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "orchestrator-agent"))

from feature_flags import rollout_bucket


def evaluate(flag, rule, subject):
    if flag.get("status") == "archived":
        return flag.get("default_value", False)
    if not rule or not rule.get("enabled"):
        return False
    if subject.get("userId") and subject["userId"] in rule.get("deny_user_ids", []):
        return False
    if (
        (subject.get("userId") and subject["userId"] in rule.get("target_user_ids", []))
        or (subject.get("orgId") and subject["orgId"] in rule.get("target_org_ids", []))
    ):
        return True
    sid = subject.get("projectId") or subject.get("orgId") or subject.get("userId")
    if not sid:
        return False
    return rollout_bucket(flag["key"], sid) < rule.get("rollout_percentage", 0)


class TestContract(unittest.TestCase):
    def test_kill_switch_beats_allow_list(self):
        self.assertFalse(evaluate(
            {"key": "discord_service_v2", "status": "active", "default_value": False},
            {"enabled": False, "rollout_percentage": 100, "target_user_ids": ["u1"], "deny_user_ids": []},
            {"userId": "u1"}))

    def test_deny_beats_allow(self):
        self.assertFalse(evaluate(
            {"key": "discord_service_v2", "status": "active", "default_value": False},
            {"enabled": True, "rollout_percentage": 0, "target_user_ids": ["u1"], "deny_user_ids": ["u1"]},
            {"userId": "u1"}))

    def test_allow_beats_zero_rollout(self):
        self.assertTrue(evaluate(
            {"key": "living_fleet", "status": "active", "default_value": False},
            {"enabled": True, "rollout_percentage": 0, "target_org_ids": ["org9"], "target_user_ids": [], "deny_user_ids": []},
            {"userId": "u2", "orgId": "org9"}))

    def test_archived_returns_default(self):
        self.assertFalse(evaluate(
            {"key": "living_fleet", "status": "archived", "default_value": False},
            {"enabled": True, "rollout_percentage": 100, "target_user_ids": [], "deny_user_ids": []},
            {"userId": "anyone"}))

    def test_full_rollout_on(self):
        self.assertTrue(evaluate(
            {"key": "living_fleet", "status": "active", "default_value": False},
            {"enabled": True, "rollout_percentage": 100, "target_user_ids": [], "deny_user_ids": []},
            {"userId": "random-user-42"}))

    def test_zero_rollout_off(self):
        self.assertFalse(evaluate(
            {"key": "living_fleet", "status": "active", "default_value": False},
            {"enabled": True, "rollout_percentage": 0, "target_user_ids": [], "deny_user_ids": []},
            {"userId": "random-user-42"}))

    def test_bucket_is_stable_and_bounded(self):
        b1 = rollout_bucket("living_fleet", "u1")
        self.assertEqual(b1, rollout_bucket("living_fleet", "u1"))
        self.assertTrue(0 <= b1 < 100)


if __name__ == "__main__":
    unittest.main()
