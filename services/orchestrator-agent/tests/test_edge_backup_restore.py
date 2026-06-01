"""Tests for Edge Backup & Restore."""

import pytest
from datetime import datetime, timedelta
from cogs.edge_backup_restore import (
    EdgeBackupRestore, BackupJob, BackupTarget, RestoreJob,
    BackupStatus, BackupType, BackupSchedule
)


@pytest.fixture
def backup():
    return EdgeBackupRestore({})


class TestBackupJob:
    def test_create(self):
        job = BackupJob("b-001", "dev-001", BackupType.FULL, "s3://bucket")
        assert job.job_id == "b-001"
        assert job.status == BackupStatus.PENDING

    def test_to_dict(self):
        job = BackupJob("b-001", "dev-001", BackupType.FULL, "s3://bucket")
        d = job.to_dict()
        assert d["job_id"] == "b-001"
        assert d["type"] == "full"


class TestBackupTarget:
    def test_create(self):
        t = BackupTarget("s3://bucket", "AWS", region="us-east-1")
        assert t.uri == "s3://bucket"

    def test_to_dict(self):
        t = BackupTarget("s3://bucket", "AWS")
        d = t.to_dict()
        assert d["uri"] == "s3://bucket"


class TestEdgeBackupRestore:
    def test_initialization(self, backup):
        assert len(backup.jobs) > 0
        assert len(backup.schedules) > 0
        assert len(backup.snapshots) > 0

    def test_create_backup(self, backup):
        job = backup.create_backup("dev-001", BackupType.FULL, "s3://bucket")
        assert job.job_id is not None
        assert job.status == BackupStatus.PENDING

    def test_get_backup(self, backup):
        job_id = list(backup.jobs.keys())[0]
        assert backup.get_backup(job_id) is not None

    def test_get_backup_not_found(self, backup):
        assert backup.get_backup("nonexistent") is None

    def test_list_backups(self, backup):
        jobs = backup.list_backups()
        assert len(jobs) > 0

    def test_list_backups_by_device(self, backup):
        first = list(backup.jobs.values())[0]
        filtered = backup.list_backups(device_id=first.device_id)
        assert all(j.device_id == first.device_id for j in filtered)

    def test_create_schedule(self, backup):
        schedule = backup.create_schedule("dev-001", "0 */6 * * *", BackupType.INCREMENTAL,
                                           "s3://bucket", retention_days=30)
        assert schedule.schedule_id is not None
        assert schedule.cron_expression == "0 */6 * * *"

    def test_list_schedules(self, backup):
        schedules = backup.list_schedules()
        assert len(schedules) > 0

    def test_get_schedule(self, backup):
        sid = list(backup.schedules.keys())[0]
        assert backup.get_schedule(sid) is not None

    def test_delete_schedule(self, backup):
        sid = list(backup.schedules.keys())[0]
        assert backup.delete_schedule(sid) is True

    def test_create_restore(self, backup):
        job_id = list(backup.jobs.keys())[0]
        restore = backup.create_restore(job_id, "dev-001")
        assert restore.restore_id is not None
        assert restore.status == BackupStatus.PENDING

    def test_get_restore(self, backup):
        job_id = list(backup.jobs.keys())[0]
        restore = backup.create_restore(job_id, "dev-001")
        assert backup.get_restore(restore.restore_id) is not None

    def test_get_restore_not_found(self, backup):
        assert backup.get_restore("nonexistent") is None

    def test_list_restores(self, backup):
        job_id = list(backup.jobs.keys())[0]
        backup.create_restore(job_id, "dev-001")
        restores = backup.list_restores()
        assert len(restores) > 0

    def test_create_snapshot(self, backup):
        snap = backup.create_snapshot("dev-001")
        assert snap["snapshot_id"] is not None
        assert snap["device_id"] == "dev-001"

    def test_get_snapshot(self, backup):
        snap = backup.create_snapshot("dev-001")
        assert backup.get_snapshot(snap["snapshot_id"]) is not None

    def test_get_snapshot_not_found(self, backup):
        assert backup.get_snapshot("nonexistent") is None

    def test_list_snapshots(self, backup):
        backup.create_snapshot("dev-001")
        snaps = backup.list_snapshots()
        assert len(snaps) > 0

    def test_get_backup_summary(self, backup):
        summary = backup.get_backup_summary()
        assert "total_backups" in summary
        assert "active_schedules" in summary
        assert "total_snapshots" in summary
        assert "last_backup" in summary

    def test_delete_backup(self, backup):
        job = backup.create_backup("dev-002", BackupType.FULL, "s3://bucket")
        assert backup.delete_backup(job.job_id) is True
        assert backup.get_backup(job.job_id).status == BackupStatus.FAILED

    def test_validate_backup(self, backup):
        job = backup.create_backup("dev-001", BackupType.FULL, "s3://bucket")
        valid = backup.validate_backup(job.job_id)
        assert valid is True
