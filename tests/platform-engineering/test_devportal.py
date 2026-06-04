"""Tests for Developer Portal manager."""
import pytest
from services.integration_service.src.platform_engineering.developer_portal import DeveloperPortalManager


class TestDeveloperPortalManager:
    def setup_method(self):
        self.mgr = DeveloperPortalManager()

    def test_register_component(self):
        c = self.mgr.register_component("my-service", "backend", "desc", "team-a")
        assert c.id is not None
        assert c.name == "my-service"

    def test_get_component(self):
        c = self.mgr.register_component("test-svc", "frontend", "desc", "team-b")
        found = self.mgr.get_component(c.id)
        assert found.id == c.id
        assert found.domain == "frontend"

    def test_list_components(self):
        self.mgr.register_component("a", "backend", "", "team-x")
        self.mgr.register_component("b", "frontend", "", "team-y")
        all_c = self.mgr.list_components()
        assert len(all_c) == 2

    def test_list_components_filter_domain(self):
        self.mgr.register_component("c1", "backend", "", "t1")
        self.mgr.register_component("c2", "frontend", "", "t2")
        backend = self.mgr.list_components(domain="backend")
        assert len(backend) == 1
        assert backend[0].domain == "backend"

    def test_get_summary(self):
        self.mgr.register_component("s1", "backend", "", "t1")
        self.mgr.register_component("s2", "backend", "", "t2")
        s = self.mgr.get_summary()
        assert s["total_components"] == 2
        assert "avg_maturity_level" in s

    def test_add_dependency(self):
        c1 = self.mgr.register_component("svc-a", "backend", "", "t1")
        c2 = self.mgr.register_component("svc-b", "backend", "", "t2")
        c1.add_dependency(c2.id)
        assert c2.id in c1.dependencies

    def test_to_dict_from_dict(self):
        c = self.mgr.register_component("roundtrip", "backend", "desc", "t1")
        d = c.to_dict()
        from services.integration_service.src.platform_engineering.developer_portal import Component
        restored = Component.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.domain == "backend"

    def test_maturity_upgrade(self):
        c = self.mgr.register_component("maturity-test", "backend", "", "t1")
        assert c.maturity_level == 0
        c.maturity_level = 3
        assert c.maturity_level == 3

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_components"] == 0

    def test_dependency_chain_visualization(self):
        c1 = self.mgr.register_component("viz-a", "backend", "desc", "t1")
        c2 = self.mgr.register_component("viz-b", "backend", "desc", "t1")
        self.mgr.add_component_dependency(c1.id, c2.id)
        viz = self.mgr.get_dependency_chain_visualization(c1.id)
        assert "nodes" in viz
        assert len(viz["edges"]) >= 1

    def test_health_trend(self):
        c = self.mgr.register_component("health-trend", "backend", "desc", "t1")
        trend = self.mgr.get_health_trend(c.id)
        assert len(trend) >= 1

    def test_portal_scorecard(self):
        c = self.mgr.register_component("scorecard-test", "backend", "desc", "t1")
        scorecard = self.mgr.get_portal_scorecard()
        assert scorecard["component_count"] >= 1

    def test_search_portal(self):
        self.mgr.register_component("search-target", "data", "desc", "t1")
        results = self.mgr.search_portal("search")
        assert results["total_matches"] >= 1

    def test_bulk_update_component_owner(self):
        c1 = self.mgr.register_component("bulk-owner-1", "backend", "desc", "t1")
        c2 = self.mgr.register_component("bulk-owner-2", "backend", "desc", "t1")
        count = self.mgr.bulk_update_component_owner([c1.id, c2.id], "new-team")
        assert count == 2
        assert c1.owner == "new-team"

    def test_system_dependency_map(self):
        sys = self.mgr.create_system("DepMapSys", "System for deps", "platform")
        c1 = self.mgr.register_component("dep-map-1", "backend", "", "t1")
        c2 = self.mgr.register_component("dep-map-2", "backend", "", "t1")
        self.mgr.add_component_to_system(sys["id"], c1.id)
        self.mgr.add_component_to_system(sys["id"], c2.id)
        dep_map = self.mgr.get_system_dependency_map(sys["id"])
        assert len(dep_map["nodes"]) == 2

    def test_calculate_system_maturity(self):
        sys = self.mgr.create_system("MatSys", "Maturity test", "platform")
        c = self.mgr.register_component("mat-comp", "backend", "desc", "t1")
        self.mgr.add_component_to_system(sys["id"], c.id)
        maturity = self.mgr.calculate_system_maturity(sys["id"])
        assert maturity["score"] >= 0
        assert maturity["level"] in ("bronze", "silver", "gold", "platinum")

    def test_add_system_tag(self):
        sys = self.mgr.create_system("TagSys", "Tag test", "platform")
        self.mgr.add_system_tag(sys["id"], "critical")
        assert "critical" in sys["tags"]
