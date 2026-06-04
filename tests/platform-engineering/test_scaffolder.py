"""Tests for Golden Path Scaffolder manager."""
import pytest
from services.integration_service.src.platform_engineering.golden_path_scaffolder import (
    GoldenPathScaffolder, GoldenPathTemplate, ScaffoldGeneration
)


class TestGoldenPathScaffolder:
    def setup_method(self):
        self.mgr = GoldenPathScaffolder()

    def test_list_templates(self):
        templates = self.mgr.list_templates()
        assert len(templates) >= 4

    def test_get_template(self):
        t = self.mgr.get_template("microservice")
        assert t is not None
        assert t.name == "microservice"

    def test_generate_project(self):
        gen = self.mgr.generate_project("microservice", "my-project", {"port": 8080})
        assert gen.id is not None
        assert gen.project_name == "my-project"
        assert gen.status == "in_progress"

    def test_generation_status(self):
        gen = self.mgr.generate_project("api-gateway", "gw-project", {})
        status = self.mgr.get_generation_status(gen.id)
        assert status.id == gen.id
        assert status.status == "in_progress"

    def test_complete_step(self):
        gen = self.mgr.generate_project("microservice", "test-proj", {})
        result = self.mgr.complete_step(gen.id, "create-repo", {"repo_url": "https://github.com/test"})
        assert result is not None
        updated = self.mgr.get_generation_status(gen.id)
        assert updated.current_step == 1

    def test_all_templates_have_steps(self):
        for t in self.mgr.list_templates():
            assert len(t.steps) > 0

    def test_invalid_template_returns_none(self):
        t = self.mgr.get_template("nonexistent")
        assert t is None

    def test_generation_progress_pct(self):
        gen = self.mgr.generate_project("data-pipeline", "pipe-proj", {})
        self.mgr.complete_step(gen.id, "create-repo", {})
        status = self.mgr.get_generation_status(gen.id)
        assert status.current_step >= 0

    def test_add_custom_step(self):
        step = self.mgr.add_custom_step("microservice", "deploy-canary", "automated", "Canary deploy")
        assert step is not None
        assert step["name"] == "deploy-canary"

    def test_add_approval_flow(self):
        flow = self.mgr.add_approval_flow("microservice", ["lead-dev", "architect"])
        assert flow is not None
        assert "lead-dev" in flow["required_approvers"]

    def test_submit_approval(self):
        flow = self.mgr.add_approval_flow("microservice", ["reviewer"])
        gen = self.mgr.generate_project("microservice", "approve-test", {})
        result = self.mgr.submit_approval(gen.instance_id, "reviewer", "approved")
        assert result

    def test_post_scaffold_hook(self):
        hook = self.mgr.add_post_scaffold_hook("microservice", "webhook", {"url": "https://example.com/hook"})
        assert hook is not None
        assert hook["type"] == "webhook"

    def test_scaffold_analytics(self):
        self.mgr.generate_project("microservice", "analytics-test", {})
        analytics = self.mgr.get_scaffold_analytics()
        assert analytics["total_instances"] >= 1

    def test_validate_template(self):
        result = self.mgr.validate_template("microservice")
        assert "valid" in result

    def test_estimate_template_duration(self):
        est = self.mgr.estimate_template_duration("microservice")
        assert est["estimated_minutes"] > 0

    def test_clone_template(self):
        cloned = self.mgr.clone_template("microservice", "cloned-service")
        assert cloned is not None
        assert cloned["name"] == "cloned-service"

    def test_batch_retire_instances(self):
        g1 = self.mgr.generate_project("microservice", "retire-1", {})
        g2 = self.mgr.generate_project("microservice", "retire-2", {})
        count = self.mgr.batch_retire_instances([g1.instance_id, g2.instance_id])
        assert count == 2
