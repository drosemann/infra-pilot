"""Tests for drift_detector_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.drift_detector_ext import DriftDetectorManager, ResourceCategory, DriftSeverity, DriftStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = DriftDetectorManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestBaselines:
    def test_create_baseline(self, manager):
        config = {"port": 8080, "protocol": "http", "timeout": 30, "health_check": {"endpoint": "/health", "interval": 10}}
        bl = manager.create_baseline(name="Web Server Config", description="Baseline for web servers", resource_category=ResourceCategory.CONFIG, resource_type="nginx", resource_id="web-01", baseline_config=config, created_by="admin")
        assert bl.id is not None
        assert bl.name == "Web Server Config"
        assert bl.checksum is not None

    def test_get_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        retrieved = manager.get_baseline(bl.id)
        assert retrieved is not None

    def test_update_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "old"})
        updated = manager.update_baseline(bl.id, {"key": "new", "extra": "value"})
        assert updated.version > 1
        assert updated.baseline_config["key"] == "new"

    def test_delete_baseline(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        assert manager.delete_baseline(bl.id) == True


class TestDriftChecks:
    def test_add_check(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        check = manager.add_check(bl.id, "Port Check", "port", expected_value=8080, comparison_type="exact", severity=DriftSeverity.HIGH, auto_remediate=True)
        assert check is not None
        assert check.name == "Port Check"
        assert check.config_path == "port"
        assert check.severity == DriftSeverity.HIGH
        assert check.auto_remediate == True

    def test_remove_check(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={})
        check = manager.add_check(bl.id, "Check", "path")
        assert manager.remove_check(check.id) == True


class TestDriftDetection:
    def test_detect_drift_match(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {"port": 8080})
        assert len(events) == 0

    def test_detect_drift_mismatch(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {"port": 9090})
        assert len(events) >= 1
        assert events[0].severity == DriftSeverity.MEDIUM

    def test_detect_missing_key(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        manager.add_check(bl.id, "Port", "port", expected_value=8080)
        events = manager.check_for_drift(bl.id, {})
        assert len(events) >= 1


class TestEvents:
    def test_acknowledge_event(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.acknowledge_event(events[0].id, "admin") == True

    def test_suppress_event(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.suppress_event(events[0].id, until_hours=48) == True

    def test_false_positive(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.check_for_drift(bl.id, {"key": "changed"})
        if events:
            assert manager.mark_false_positive(events[0].id) == True


class TestPolicies:
    def test_create_policy(self, manager):
        policy = manager.create_policy(name="Hourly Check", description="Check every hour", resource_categories=[ResourceCategory.CONFIG, ResourceCategory.NETWORK], auto_remediate=True)
        assert policy.id is not None
        assert policy.name == "Hourly Check"
        assert policy.auto_remediate == True

    def test_update_policy(self, manager):
        policy = manager.create_policy(name="Original", description="Original")
        updated = manager.update_policy(policy.id, {"name": "Updated", "auto_remediate": True})
        assert updated.name == "Updated"

    def test_delete_policy(self, manager):
        policy = manager.create_policy(name="Test", description="Test")
        assert manager.delete_policy(policy.id) == True


class TestExportImport:
    def test_export_baseline_yaml(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        yaml_out = manager.export_baseline_yaml(bl.id)
        assert yaml_out is not None
        assert "name: Test" in yaml_out

    def test_import_baseline_yaml(self, manager):
        yaml_content = "name: Imported\nresource_category: config\nresource_type: nginx\nconfig:\n  port: 8080\nchecks: []"
        bl = manager.import_baseline_yaml(yaml_content, resource_id="web-02", created_by="admin")
        assert bl is not None
        assert bl.name == "Imported"


class TestBaselineComparison:
    def test_compare_baselines(self, manager):
        bl1 = manager.create_baseline(name="BL1", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"port": 8080})
        bl2 = manager.create_baseline(name="BL2", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r2", baseline_config={"port": 9090})
        result = manager.compare_baselines(bl1.id, bl2.id)
        assert result["has_differences"] == True
        assert result["diff"] is not None


class TestScheduledChecks:
    def test_run_scheduled_checks(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        manager.add_check(bl.id, "Check", "key", expected_value="val")
        events = manager.run_scheduled_checks()
        assert events is not None


class TestStatistics:
    def test_get_statistics(self, manager):
        bl = manager.create_baseline(name="Test", description="Test", resource_category=ResourceCategory.CONFIG, resource_type="generic", resource_id="r1", baseline_config={"key": "val"})
        stats = manager.get_statistics()
        assert stats["total_baselines"] >= 1
