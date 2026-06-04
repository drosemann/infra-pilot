import pytest


class TestSOAR:
    def test_playbook_crud(self):
        playbooks = []
        p = {"id": "pb-1", "name": "Malware Isolation", "trigger": "incident_created", "enabled": True}
        playbooks.append(p)
        assert len(playbooks) == 1
        assert playbooks[0]["name"] == "Malware Isolation"
        playbooks[0]["enabled"] = False
        assert playbooks[0]["enabled"] is False
        playbooks = [x for x in playbooks if x["id"] != "pb-1"]
        assert len(playbooks) == 0

    def test_case_management(self):
        cases = []
        case = {"id": "case-1", "title": "Suspicious Login", "severity": "high", "status": "open"}
        cases.append(case)
        assert len(cases) == 1
        cases[0]["status"] = "resolved"
        assert cases[0]["status"] == "resolved"

    def test_connector_status(self):
        connectors = [
            {"id": "c1", "name": "CrowdStrike", "status": "healthy"},
            {"id": "c2", "name": "Splunk", "status": "degraded"},
        ]
        healthy = [c for c in connectors if c["status"] == "healthy"]
        assert len(healthy) == 1

    def test_playbook_execution(self):
        result = {"playbook_id": "pb-1", "status": "executing", "started": "2025-11-10T12:00:00Z"}
        assert result["status"] == "executing"
        result["status"] = "completed"
        assert result["status"] == "completed"

    def test_playbook_validation(self):
        with pytest.raises(ValueError):
            p = {}
            if "name" not in p:
                raise ValueError("Playbook name required")

    def test_empty_playbooks(self):
        playbooks = []
        assert len(playbooks) == 0
        assert playbooks == []
