"""Unit tests for the deployment freeze gate (deploy_freeze)."""

import os
import unittest
from datetime import datetime

import deploy_freeze


class DeployFreezeTest(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        os.environ.pop("DEPLOY_FREEZE", None)
        os.environ.pop("DEPLOY_FREEZE_WINDOWS", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_no_freeze_by_default(self):
        frozen, _ = deploy_freeze.freeze_active(datetime(2026, 11, 2, 12, 0))
        self.assertFalse(frozen)

    def test_manual_freeze_blocks_but_dry_run_passes(self):
        os.environ["DEPLOY_FREEZE"] = "true"
        frozen, reason = deploy_freeze.freeze_active()
        self.assertTrue(frozen)
        self.assertTrue(reason)
        allowed, _ = deploy_freeze.check_deploy_allowed({}, dry_run=False)
        self.assertFalse(allowed)
        allowed, _ = deploy_freeze.check_deploy_allowed({}, dry_run=True)
        self.assertTrue(allowed)

    def test_window_freeze_matches_weekday(self):
        # 2026-11-07 is a Saturday.
        os.environ["DEPLOY_FREEZE_WINDOWS"] = "sat:00:00-sun:23:59"
        frozen, _ = deploy_freeze.freeze_active(datetime(2026, 11, 7, 10, 0))
        self.assertTrue(frozen)
        frozen, _ = deploy_freeze.freeze_active(datetime(2026, 11, 4, 10, 0))
        self.assertFalse(frozen)

    def test_override_requires_reason(self):
        os.environ["DEPLOY_FREEZE"] = "1"
        allowed, _ = deploy_freeze.check_deploy_allowed({"freeze_override": True})
        self.assertFalse(allowed)
        allowed, _ = deploy_freeze.check_deploy_allowed(
            {"freeze_override": True, "freeze_reason": "hotfix INC-123"}
        )
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
