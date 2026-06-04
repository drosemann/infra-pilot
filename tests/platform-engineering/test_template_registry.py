"""Tests for Template Registry manager."""
import pytest
from services.integration_service.src.platform_engineering.template_registry import TemplateRegistry


class TestTemplateRegistry:
    def setup_method(self):
        self.mgr = TemplateRegistry()

    def test_create_template(self):
        t = self.mgr.create_template("blueprint", "infra", {"region": "string"})
        assert t.id is not None
        assert t.name == "blueprint"

    def test_get_template(self):
        t = self.mgr.create_template("tmpl-1", "app", {})
        found = self.mgr.get_template(t.id)
        assert found.id == t.id

    def test_list_templates(self):
        self.mgr.create_template("t1", "infra", {})
        self.mgr.create_template("t2", "app", {})
        assert len(self.mgr.list_templates()) == 2

    def test_use_template_increments_count(self):
        t = self.mgr.create_template("popular", "infra", {})
        assert t.usage_count == 0
        self.mgr.use_template(t.id)
        assert self.mgr.get_template(t.id).usage_count == 1

    def test_version_starts_at_1(self):
        t = self.mgr.create_template("v-test", "app", {})
        assert t.version == 1

    def test_get_summary(self):
        t = self.mgr.create_template("s1", "infra", {})
        self.mgr.use_template(t.id)
        self.mgr.use_template(t.id)
        s = self.mgr.get_summary()
        assert s["total_templates"] == 1
        assert s["total_usage"] == 2

    def test_to_dict_from_dict(self):
        t = self.mgr.create_template("roundtrip", "app", {"name": "string"})
        d = t.to_dict()
        from services.integration_service.src.platform_engineering.template_registry import Template
        restored = Template.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.params_schema == {"name": "string"}

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_templates"] == 0
        assert s["total_usage"] == 0

    def test_bulk_create_templates(self):
        ids = self.mgr.bulk_import_blueprints([
            {"name": "bulk1", "blueprint_type": "infrastructure", "owner": "team-a"},
            {"name": "bulk2", "blueprint_type": "application", "owner": "team-b"},
        ])
        assert len(ids) == 2
        assert self.mgr.get_blueprint_statistics()["total_blueprints"] >= 2

    def test_search_blueprints(self):
        self.mgr.create_blueprint("search-me", "infrastructure", "tester")
        results = self.mgr.search_blueprints("search")
        assert any("search" in b.name.lower() for b in results)

    def test_tag_blueprint(self):
        bp = self.mgr.create_blueprint("tag-test", "infrastructure", "owner")
        self.mgr.tag_blueprint(bp.blueprint_id, ["alpha", "beta"])
        bp2 = self.mgr.blueprints[bp.blueprint_id]
        assert "alpha" in bp2.tags
        assert "beta" in bp2.tags

    def test_blueprint_health_missing_fields(self):
        bp = self.mgr.create_blueprint("health-test", "infrastructure", "")
        health = self.mgr.get_blueprint_health(bp.blueprint_id)
        assert health["health_score"] < 100

    def test_archive_old_versions(self):
        bp = self.mgr.create_blueprint("archive-test", "infrastructure", "owner")
        for i in range(5):
            bp.add_version(f"v{i}", f"content-{i}", "owner", "")
        removed = self.mgr.archive_old_versions(bp.blueprint_id, keep=2)
        assert removed > 0
        assert len(bp.versions) <= 2

    def test_version_diff(self):
        bp = self.mgr.create_blueprint("diff-test", "infrastructure", "owner")
        bp.add_version("v1", "line1\nline2\nline3", "owner", "")
        bp.add_version("v2", "line1\nline4\nline3", "owner", "")
        diff = self.mgr.get_version_diff(bp.blueprint_id, "v1", "v2")
        assert diff["added"] > 0 or diff["removed"] > 0

    def test_popular_templates_empty(self):
        popular = self.mgr.get_popular_templates()
        assert isinstance(popular, list)

    def test_recommend_no_context(self):
        recs = self.mgr.recommend_blueprint({})
        assert isinstance(recs, list)
