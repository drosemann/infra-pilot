"""Tests for Service Catalog manager."""
import pytest
from services.integration_service.src.platform_engineering.service_catalog import ServiceCatalogManager


class TestServiceCatalogManager:
    def setup_method(self):
        self.mgr = ServiceCatalogManager()

    def test_register_service(self):
        s = self.mgr.register_service("my-svc", "backend", "test", "team-a")
        assert s.id is not None
        assert s.name == "my-svc"

    def test_get_service(self):
        s = self.mgr.register_service("svc-1", "frontend", "desc", "team-b")
        found = self.mgr.get_service(s.id)
        assert found.id == s.id

    def test_list_services(self):
        self.mgr.register_service("a", "backend", "", "t1")
        self.mgr.register_service("b", "frontend", "", "t2")
        assert len(self.mgr.list_services()) == 2

    def test_score_service(self):
        s = self.mgr.register_service("score-test", "backend", "desc", "t1")
        s.description = "full description"
        s.owner = "team-a"
        s.domain = "backend"
        s.sla = "99.9"
        s.has_documentation = True
        s.has_ci_cd = True
        s.has_monitoring = True
        s.has_oncall = True
        score = self.mgr.score_service(s.id)
        assert score["readiness_score"] > 0
        assert score["total_checks"] == 15

    def test_get_summary(self):
        self.mgr.register_service("s1", "backend", "", "t1")
        s = self.mgr.get_summary()
        assert s["total_services"] == 1

    def test_to_dict_from_dict(self):
        s = self.mgr.register_service("roundtrip", "backend", "desc", "t1")
        d = s.to_dict()
        from services.integration_service.src.platform_engineering.service_catalog import CatalogService
        restored = CatalogService.from_dict(d)
        assert restored.name == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_services"] == 0
        assert s["avg_readiness_score"] == 0

    def test_score_zero_when_no_checks(self):
        s = self.mgr.register_service("bare", "", "", "")
        score = self.mgr.score_service(s.id)
        assert score["readiness_score"] == 0

    def test_compliance_check(self):
        s = self.mgr.register_service("compliance-test", "team-a", "python", "t1")
        result = self.mgr.run_compliance_check(s.id)
        assert result["compliance_score"] > 0

    def test_bulk_compliance(self):
        self.mgr.register_service("c1", "team", "py", "t1")
        results = self.mgr.bulk_compliance_check()
        assert len(results) >= 1

    def test_add_cost_data(self):
        s = self.mgr.register_service("cost-test", "fin", "go", "t2")
        self.mgr.add_cost_data(s.id, 1500.50)
        summary = self.mgr.get_cost_summary()
        assert summary["total_monthly_cost"] > 0

    def test_dependency_graph(self):
        s1 = self.mgr.register_service("core", "team-a", "py", "t1")
        s2 = self.mgr.register_service("dependent", "team-b", "ts", "t2")
        self.mgr.add_service_metadata(s2.id, "dependencies", [s1.id])
        chain = self.mgr.get_dependency_chain(s2.id)
        assert len(chain) >= 2

    def test_find_orphan_services(self):
        self.mgr.register_service("orphan-test", "orphan", "py", "t1")
        orphans = self.mgr.find_orphan_services()
        assert len(orphans) >= 1

    def test_compute_maturity_levels(self):
        s = self.mgr.register_service("maturity", "team", "py", "t1")
        score = self.mgr.compute_maturity_score(s.id)
        assert score["level"] in ("bronze", "silver", "gold", "platinum")

    def test_bulk_set_tier(self):
        s1 = self.mgr.register_service("tier-test-1", "t", "py", "t3")
        s2 = self.mgr.register_service("tier-test-2", "t", "go", "t3")
        count = self.mgr.bulk_set_tier([s1.id, s2.id], "t1")
        assert count == 2
        assert s1.tier == "t1"
