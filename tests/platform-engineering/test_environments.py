"""Tests for Environment Orchestrator manager."""
import pytest
from services.integration_service.src.platform_engineering.environment_orchestrator import EnvironmentOrchestrator


class TestEnvironmentOrchestrator:
    def setup_method(self):
        self.mgr = EnvironmentOrchestrator()

    def test_create_environment(self):
        e = self.mgr.create_environment("pr-42", "microservice", 24, "feature-x")
        assert e.id is not None
        assert e.name == "pr-42"
        assert e.status == "creating"

    def test_get_environment(self):
        e = self.mgr.create_environment("test-env", "api-gateway", 12, "main")
        found = self.mgr.get_environment(e.id)
        assert found.id == e.id

    def test_list_environments(self):
        self.mgr.create_environment("e1", "t1", 24, "main")
        self.mgr.create_environment("e2", "t2", 48, "dev")
        assert len(self.mgr.list_environments()) == 2

    def test_delete_environment(self):
        e = self.mgr.create_environment("to-delete", "t1", 24, "main")
        self.mgr.delete_environment(e.id)
        found = self.mgr.get_environment(e.id)
        assert found.status == "deleted"

    def test_extend_ttl(self):
        e = self.mgr.create_environment("extend-me", "t1", 24, "main")
        self.mgr.extend_ttl(e.id, 12)
        updated = self.mgr.get_environment(e.id)
        assert updated.ttl_hours > 24

    def test_get_summary(self):
        self.mgr.create_environment("a", "t1", 24, "main")
        self.mgr.create_environment("b", "t2", 48, "dev")
        s = self.mgr.get_summary()
        assert s["total_environments"] == 2

    def test_to_dict_from_dict(self):
        e = self.mgr.create_environment("roundtrip", "t1", 24, "main")
        d = e.to_dict()
        from services.integration_service.src.platform_engineering.environment_orchestrator import Environment
        restored = Environment.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.template == "t1"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_environments"] == 0

    def test_environment_lifecycle(self):
        e = self.mgr.create_environment("lifecycle", "t1", 1, "main")
        assert e.status == "creating"
        self.mgr.transition_status(e.id, "running")
        assert self.mgr.get_environment(e.id).status == "running"
        self.mgr.transition_status(e.id, "expired")
        assert self.mgr.get_environment(e.id).status == "expired"

    def test_set_cleanup_policy(self):
        policy = self.mgr.set_cleanup_policy("test-project", 48, True, 12)
        assert policy["project"] == "test-project"
        assert policy["max_age_hours"] == 48

    def test_set_resource_quota(self):
        quota = self.mgr.set_resource_quota("test-project", 4, 16, 3)
        assert quota["max_cpu"] == 4
        assert quota["max_memory_gb"] == 16

    def test_check_resource_quota(self):
        self.mgr.set_resource_quota("quota-project", 8, 32, 5)
        check = self.mgr.check_resource_quota("quota-project")
        assert "cpu_pct" in check
        assert "memory_pct" in check

    def test_backup_and_restore(self):
        e = self.mgr.create_environment("backup-test", "t1", 1, "main")
        backup = self.mgr.backup_environment(e.env_id)
        assert backup is not None
        restored = self.mgr.restore_environment(backup["backup_id"])
        assert restored is not None
        assert restored["status"] == "restored"

    def test_list_backups(self):
        e = self.mgr.create_environment("bk-list", "t1", 1, "main")
        self.mgr.backup_environment(e.env_id)
        backups = self.mgr.list_backups(e.env_id)
        assert len(backups) >= 1

    def test_environment_health(self):
        e = self.mgr.create_environment("health-test", "t1", 1, "main")
        health = self.mgr.get_environment_health(e.env_id)
        assert "age_hours" in health
        assert health["is_expired"] is False

    def test_extend_ttl(self):
        e = self.mgr.create_environment("ttl-test", "t1", 1, "main", ttl_hours=24)
        self.mgr.extend_environment_ttl(e.env_id, 12)
        assert e.ttl_hours == 36

    def test_bulk_delete_expired(self):
        e = self.mgr.create_environment("expired-test", "t1", 1, "main", ttl_hours=-1)
        count = self.mgr.bulk_delete_expired()
        assert count >= 1

    def test_batch_set_template(self):
        e1 = self.mgr.create_environment("batch-1", "t1", 1, "main")
        e2 = self.mgr.create_environment("batch-2", "t1", 1, "main")
        count = self.mgr.batch_set_template([e1.env_id, e2.env_id], "t2")
        assert count == 2
