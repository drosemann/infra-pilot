import pytest


class TestEndpoint:
    def test_device_inventory(self):
        devices = [
            {"id": "d1", "os": "Windows", "status": "online"},
            {"id": "d2", "os": "macOS", "status": "offline"},
            {"id": "d3", "os": "Linux", "status": "online"},
        ]
        online = [d for d in devices if d["status"] == "online"]
        assert len(online) == 2

    def test_policy_assignment(self):
        device = {"id": "d1", "policy_id": "p1", "compliant": True}
        assert device["compliant"] is True
        device["compliant"] = False
        assert device["compliant"] is False

    def test_alert_classification(self):
        alerts = [
            {"type": "malware", "severity": "high"},
            {"type": "policy_violation", "severity": "medium"},
            {"type": "suspicious_process", "severity": "high"},
        ]
        high = [a for a in alerts if a["severity"] == "high"]
        assert len(high) == 2

    def test_scan_execution(self):
        result = {"device_id": "d1", "scan": "started", "type": "quick"}
        assert result["scan"] == "started"
