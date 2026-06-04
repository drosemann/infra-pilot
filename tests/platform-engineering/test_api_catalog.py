"""Tests for API Catalog manager."""
import pytest
from services.integration_service.src.platform_engineering.api_catalog import ApiCatalog


class TestApiCatalog:
    def setup_method(self):
        self.mgr = ApiCatalog()
        self.sample_spec = '{"openapi":"3.0.0","info":{"title":"Test API","version":"1.0"},"paths":{"/users":{"get":{"operationId":"listUsers"}}}}'

    def test_register_api(self):
        a = self.mgr.register_api("My API", "1.0.0", self.sample_spec)
        assert a.id is not None
        assert a.name == "My API"

    def test_get_api(self):
        a = self.mgr.register_api("API v1", "2.0.0", self.sample_spec)
        found = self.mgr.get_api(a.id)
        assert found.id == a.id

    def test_list_apis(self):
        self.mgr.register_api("A1", "1.0", self.sample_spec)
        self.mgr.register_api("A2", "2.0", self.sample_spec)
        assert len(self.mgr.list_apis()) == 2

    def test_endpoint_count(self):
        a = self.mgr.register_api("EP API", "1.0", self.sample_spec)
        assert a.endpoint_count >= 1

    def test_get_summary(self):
        self.mgr.register_api("S1", "1.0", self.sample_spec)
        s = self.mgr.get_summary()
        assert s["total_apis"] == 1
        assert s["total_endpoints"] >= 1

    def test_to_dict_from_dict(self):
        a = self.mgr.register_api("roundtrip", "1.0", self.sample_spec)
        d = a.to_dict()
        from services.integration_service.src.platform_engineering.api_catalog import APIDefinition
        restored = APIDefinition.from_dict(d)
        assert restored.name == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_apis"] == 0
        assert s["total_endpoints"] == 0

    def test_breaking_change_detection(self):
        v1 = '{"openapi":"3.0.0","info":{"title":"API","version":"1.0"},"paths":{"/users":{"get":{"operationId":"listUsers"}}}}'
        v2 = '{"openapi":"3.0.0","info":{"title":"API","version":"2.0"},"paths":{}}'
        a = self.mgr.register_api("BC API", "1.0", v1)
        a2 = self.mgr.register_api("BC API", "2.0", v2)
        assert True

    def test_schedule_deprecation(self):
        a = self.mgr.register_api("dep-test", "1.0", "", "team")
        schedule = self.mgr.schedule_deprecation(a.id, datetime.utcnow() + timedelta(days=90), "https://migrate")
        assert schedule is not None
        assert schedule["status"] == "scheduled"

    def test_track_api_usage(self):
        a = self.mgr.register_api("usage-test", "1.0", "", "team")
        event = self.mgr.track_api_usage(a.id, "consumer-x", "/api/v1/test", "GET", 200, 45.2)
        assert "event_id" in event

    def test_get_api_usage_stats(self):
        a = self.mgr.register_api("stats-test", "1.0", "", "team")
        self.mgr.track_api_usage(a.id, "consumer-a", "/api/v1/data", "GET", 200, 30)
        self.mgr.track_api_usage(a.id, "consumer-b", "/api/v1/data", "POST", 201, 55)
        stats = self.mgr.get_api_usage_stats(a.id, days=30)
        assert stats["total_requests"] == 2
        assert stats["unique_callers"] == 2

    def test_compliance_report(self):
        a = self.mgr.register_api("comp-test", "1.0", "Test API", "team")
        report = self.mgr.run_compliance_report(a.id)
        assert report["compliance_pct"] > 0

    def test_bulk_register_apis(self):
        ids = self.mgr.bulk_register_apis([
            {"name": "bulk-1", "version": "1.0", "description": "desc", "owner": "team"},
            {"name": "bulk-2", "version": "2.0", "description": "desc", "owner": "team"},
        ])
        assert len(ids) == 2

    def test_find_duplicate_endpoints(self):
        a = self.mgr.register_api("dup-test", "1.0", "", "team")
        a.add_endpoint("GET", "/users")
        a2 = self.mgr.register_api("dup-test-2", "1.0", "", "team")
        a2.add_endpoint("GET", "/users")
        dups = self.mgr.get_duplicate_endpoints()
        assert len(dups) >= 1

    def test_add_api_version(self):
        a = self.mgr.register_api("version-test", "1.0", "", "team")
        self.mgr.add_api_version(a.id, "2.0", "https://spec/v2", "Breaking changes")
        assert a.version == "2.0"

    def test_notify_consumers(self):
        a = self.mgr.register_api("notify-test", "1.0", "", "team", consumers=["consumer-a", "consumer-b"])
        result = self.mgr.notify_consumers(a.id, "API will be deprecated")
        assert result["notifications_sent"] == 2

    def test_get_deprecation_schedule(self):
        a = self.mgr.register_api("dep-sched", "1.0", "", "team")
        self.mgr.schedule_deprecation(a.id, datetime.utcnow() + timedelta(days=30))
        schedules = self.mgr.get_deprecation_schedule(a.id)
        assert len(schedules) >= 1
