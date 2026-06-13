import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from backup_federation import BackupFederation

@pytest.fixture
def bf():
    b = BackupFederation({})
    b.initialize()
    yield b
    b.close()

class TestBackupFederation:
    def test_list_backups_empty(self, bf):
        assert bf.list_backups() == []

    def test_create_backup(self, bf):
        bk = bf.create_backup(name="daily-db", workload_id="wl-1", source_provider="on_prem")
        assert bk.id is not None
        assert bk.state == "pending"

    def test_execute_backup(self, bf):
        bk = bf.create_backup("daily-db", "wl-1", "on_prem")
        result = bf.execute_backup(bk.id)
        assert result["status"] == "completed"
        assert result["size_gb"] > 0

    def test_execute_nonexistent(self, bf):
        result = bf.execute_backup("nonexistent")
        assert result.get("error") == "Not found"

    def test_create_restore(self, bf):
        bk = bf.create_backup("test-bk", "wl-1", "on_prem")
        bf.execute_backup(bk.id)
        rj = bf.create_restore(backup_id=bk.id, target_provider="aws")
        assert rj.id is not None
        assert rj.state == "restoring"

    def test_list_restores(self, bf):
        bk = bf.create_backup("test-bk", "wl-1", "on_prem")
        bf.execute_backup(bk.id)
        bf.create_restore(bk.id, "aws")
        assert len(bf.list_restores()) == 1

    def test_list_vaults(self, bf):
        vaults = bf.list_vaults()
        assert len(vaults) > 0
        assert any(v["provider"] == "aws_s3" for v in vaults)
