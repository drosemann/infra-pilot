import pytest


class TestSIEM:
    def test_source_management(self):
        sources = [{"id": "s1", "name": "Web Server", "type": "apache", "status": "online"}]
        online = [s for s in sources if s["status"] == "online"]
        assert len(online) == 1

    def test_alert_severity(self):
        alerts = [
            {"id": "a1", "severity": "critical", "message": "Ransomware detected"},
            {"id": "a2", "severity": "low", "message": "Failed login"},
        ]
        critical = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical) == 1

    def test_correlation_rule_enable_disable(self):
        rules = [{"id": "r1", "name": "Multiple Failed Logins", "enabled": True}]
        assert rules[0]["enabled"] is True
        rules[0]["enabled"] = False
        assert rules[0]["enabled"] is False

    def test_search_execution(self):
        result = {"query": "malware", "took_ms": 2400, "total": 42}
        assert result["took_ms"] > 0
        assert result["total"] >= 0
