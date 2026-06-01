"""Tests for runbook_library_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.runbook_library_ext import RunbookLibraryManager, RunbookCategory, RunbookStatus, StepType


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = RunbookLibraryManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestRunbookCRUD:
    def test_create_runbook(self, manager):
        rb = manager.create_runbook(name="Incident Response", description="Standard incident response procedure", category=RunbookCategory.INCIDENT_RESPONSE, author="security-team", tags=["incident", "security"], severity="high", estimated_duration_minutes=45)
        assert rb.id is not None
        assert rb.name == "Incident Response"
        assert rb.category == RunbookCategory.INCIDENT_RESPONSE
        assert rb.status == RunbookStatus.DRAFT

    def test_get_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.TROUBLESHOOTING)
        retrieved = manager.get_runbook(rb.id)
        assert retrieved is not None

    def test_update_runbook(self, manager):
        rb = manager.create_runbook(name="Original", description="Original", category=RunbookCategory.MANUAL)
        updated = manager.update_runbook(rb.id, {"name": "Updated", "severity": "critical"})
        assert updated.name == "Updated"
        assert updated.severity == "critical"

    def test_delete_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        assert manager.delete_runbook(rb.id) == True


class TestSteps:
    def test_add_step(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.TROUBLESHOOTING)
        step = manager.add_step(rb.id, "Check Logs", StepType.SCRIPT, order=1, description="Check application logs", command="journalctl -u app", critical=True, timeout_seconds=60)
        assert step is not None
        assert step.name == "Check Logs"
        assert step.critical == True
        assert step.timeout_seconds == 60

    def test_remove_step(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        step = manager.add_step(rb.id, "Step1", StepType.MANUAL, order=1)
        assert manager.remove_step(rb.id, step.id) == True


class TestParameters:
    def test_add_parameter(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.AUTOMATION)
        param = manager.add_parameter(rb.id, "hostname", "string", "Target hostname", required=True, default_value="localhost", validation_regex="^[a-z0-9-]+$")
        assert param is not None
        assert param.name == "hostname"
        assert param.required == True
        assert param.validation_regex == "^[a-z0-9-]+$"


class TestVersioning:
    def test_create_version(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        version = manager.create_version(rb.id, changelog="Initial version", created_by="admin")
        assert version is not None
        assert version.version > 0

    def test_get_versions(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.create_version(rb.id, changelog="v1")
        versions = manager.get_versions(rb.id)
        assert len(versions) >= 1


class TestLifecycle:
    def test_publish_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        assert manager.publish_runbook(rb.id) == True
        assert rb.status == RunbookStatus.PUBLISHED

    def test_deprecate_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.publish_runbook(rb.id)
        assert manager.deprecate_runbook(rb.id) == True
        assert rb.status == RunbookStatus.DEPRECATED


class TestSearch:
    def test_search_runbooks(self, manager):
        manager.create_runbook(name="Database Backup", description="DB backup procedure", category=RunbookCategory.BACKUP)
        manager.create_runbook(name="Server Deploy", description="Server deployment", category=RunbookCategory.DEPLOYMENT)
        results = manager.search_runbooks("backup")
        assert len(results) >= 1

    def test_list_runbooks(self, manager):
        manager.create_runbook(name="R1", description="Test", category=RunbookCategory.MONITORING)
        manager.create_runbook(name="R2", description="Test", category=RunbookCategory.SECURITY)
        runbooks = manager.list_runbooks()
        assert len(runbooks) >= 2

    def test_list_by_category(self, manager):
        manager.create_runbook(name="R1", description="Test", category=RunbookCategory.BACKUP)
        runbooks = manager.list_runbooks(category=RunbookCategory.BACKUP)
        assert len(runbooks) >= 1


class TestExecution:
    def test_execute_runbook(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.AUTOMATION)
        manager.publish_runbook(rb.id)
        manager.add_step(rb.id, "Echo", StepType.SCRIPT, order=1, command="result = 'hello'")
        execution = manager.execute_runbook(rb.id, parameters={}, executed_by="admin", triggered_by="manual")
        assert execution is not None
        assert execution.status in ("completed", "failed")

    def test_get_executions(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        manager.publish_runbook(rb.id)
        executions = manager.get_executions(runbook_id=rb.id)
        assert executions is not None


class TestExportImport:
    def test_export_yaml(self, manager):
        rb = manager.create_runbook(name="Test Runbook", description="Test", category=RunbookCategory.GENERAL)
        yaml_out = manager.export_runbook_yaml(rb.id)
        assert yaml_out is not None
        assert "name: Test Runbook" in yaml_out

    def test_import_yaml(self, manager):
        yaml_content = "name: Imported RB\ndescription: Imported\ncategory: troubleshooting\nversion: 1\nparameters: []\nsteps: []"
        rb = manager.import_runbook_yaml(yaml_content, author="admin")
        assert rb is not None
        assert rb.name == "Imported RB"


class TestClone:
    def test_clone_runbook(self, manager):
        rb = manager.create_runbook(name="Original", description="Original RB", category=RunbookCategory.GENERAL)
        clone = manager.clone_runbook(rb.id, "Clone RB")
        assert clone is not None
        assert clone.name == "Clone RB"
        assert clone.id != rb.id


class TestBulkPublish:
    def test_bulk_publish(self, manager):
        r1 = manager.create_runbook(name="R1", description="T1", category=RunbookCategory.GENERAL)
        r2 = manager.create_runbook(name="R2", description="T2", category=RunbookCategory.GENERAL)
        count = manager.bulk_publish([r1.id, r2.id])
        assert count == 2


class TestStatistics:
    def test_get_statistics(self, manager):
        rb = manager.create_runbook(name="Test", description="Test", category=RunbookCategory.GENERAL)
        stats = manager.get_statistics()
        assert stats["total_runbooks"] >= 1
