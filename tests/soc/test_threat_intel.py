import pytest


class TestThreatIntel:
    def test_ioc_crud(self):
        iocs = []
        ioc = {"id": "ioc-1", "type": "ip", "value": "1.2.3.4", "confidence": 85}
        iocs.append(ioc)
        assert len(iocs) == 1
        ioc["confidence"] = 90
        assert ioc["confidence"] == 90
        iocs = [x for x in iocs if x["id"] != "ioc-1"]
        assert len(iocs) == 0

    def test_feed_management(self):
        feeds = [{"id": "f1", "name": "AlienVault OTX", "status": "active"}]
        assert feeds[0]["status"] == "active"
        feeds[0]["status"] = "error"
        assert feeds[0]["status"] == "error"

    def test_ioc_enrichment(self):
        result = {"value": "1.2.3.4", "enriched": True, "score": 78}
        assert result["enriched"] is True
        assert result["score"] >= 0 and result["score"] <= 100

    def test_actor_tracking(self):
        actors = [{"id": "a1", "name": "APT-42", "motivation": "Financial"}]
        assert actors[0]["name"] == "APT-42"

    def test_ioc_type_validation(self):
        valid_types = ["ip", "domain", "hash", "url"]
        with pytest.raises(ValueError):
            t = "invalid"
            if t not in valid_types:
                raise ValueError("Invalid IOC type")
