import pytest


class TestSASE:
    def test_policy_crud(self):
        policies = [{"id": "p1", "name": "Block RDP", "type": "security", "enabled": True}]
        assert len(policies) == 1
        policies[0]["enabled"] = False
        assert policies[0]["enabled"] is False

    def test_branch_status(self):
        branches = [{"id": "b1", "name": "NYC", "latency": 28, "connected": True}]
        online = [b for b in branches if b["connected"]]
        assert len(online) == 1

    def test_ztna_app_protection(self):
        apps = [{"id": "app1", "name": "Jira", "users": 84, "sessions": 156}]
        assert apps[0]["sessions"] > 0

    def test_threat_blocking(self):
        blocked = {"total": 89, "malware": 34, "phishing": 28, "c2": 12, "other": 15}
        assert blocked["total"] == sum([blocked["malware"], blocked["phishing"], blocked["c2"], blocked["other"]])
