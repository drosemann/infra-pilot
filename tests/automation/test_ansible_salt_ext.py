"""Tests for ansible_salt_integration_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.ansible_salt_integration_ext import AnsibleSaltManager, ToolType, JobStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = AnsibleSaltManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestInventory:
    def test_create_inventory(self, manager):
        inv = manager.create_inventory(name="Production", description="Production servers")
        assert inv.id is not None
        assert inv.name == "Production"

    def test_get_inventory(self, manager):
        inv = manager.create_inventory(name="Test", description="Test")
        retrieved = manager.get_inventory(inv.id)
        assert retrieved is not None

    def test_delete_inventory(self, manager):
        inv = manager.create_inventory(name="Test", description="Test")
        assert manager.delete_inventory(inv.id) == True
        assert manager.get_inventory(inv.id) is None


class TestHosts:
    def test_add_host(self, manager):
        inv = manager.create_inventory(name="Prod")
        host = manager.add_host(inv.id, "web01", "192.168.1.10", ansible_user="deploy", ansible_port=22, variables={"region": "us-east"}, groups=["webservers"])
        assert host is not None
        assert host.name == "web01"
        assert host.ansible_host == "192.168.1.10"
        assert "webservers" in host.groups

    def test_remove_host(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10")
        assert manager.remove_host(inv.id, "web01") == True

    def test_add_host_to_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10", groups=["webservers"])
        manager.add_group(inv.id, "webservers")
        assert manager.add_host_to_group(inv.id, "web01", "webservers") == True


class TestGroups:
    def test_add_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        group = manager.add_group(inv.id, "webservers", variables={"http_port": 80})
        assert group is not None
        assert group.name == "webservers"

    def test_add_host_to_nonexistent_group(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "192.168.1.10")
        assert manager.add_host_to_group(inv.id, "web01", "nonexistent") == False


class TestPlaybooks:
    def test_create_playbook(self, manager):
        pb = manager.create_playbook(name="Deploy App", description="Deploy application", tool=ToolType.ANSIBLE, content="- hosts: all\ntasks:\n  - name: Deploy\n    copy: src=app dest=/opt/app", parameters={"version": "1.0"}, inventory_id=None)
        assert pb.id is not None
        assert pb.name == "Deploy App"
        assert pb.tool == ToolType.ANSIBLE

    def test_get_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        retrieved = manager.get_playbook(pb.id)
        assert retrieved is not None

    def test_update_playbook(self, manager):
        pb = manager.create_playbook(name="Original", description="Original", tool=ToolType.ANSIBLE, content="")
        updated = manager.update_playbook(pb.id, {"name": "Updated", "version": "2.0"})
        assert updated.name == "Updated"
        assert updated.version == "2.0"

    def test_delete_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        assert manager.delete_playbook(pb.id) == True


class TestExecution:
    def test_execute_playbook(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="- hosts: all\ntasks:\n  - name: Ping\n    ping:")
        job = manager.execute_playbook(pb.id, executed_by="admin")
        assert job is not None
        assert job.status in (JobStatus.SUCCESS, JobStatus.FAILED)

    def test_get_job(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        job = manager.execute_playbook(pb.id)
        retrieved = manager.get_job(job.id)
        assert retrieved is not None

    def test_cancel_job(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        job = manager.execute_playbook(pb.id)
        if job.status == JobStatus.PENDING:
            assert manager.cancel_job(job.id) == True
        else:
            assert manager.cancel_job(job.id) == False


class TestSchedules:
    def test_create_schedule(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        schedule = manager.create_schedule(pb.id, "Daily backup", "0 2 * * *")
        assert schedule is not None
        assert schedule.cron_expression == "0 2 * * *"

    def test_delete_schedule(self, manager):
        pb = manager.create_playbook(name="Test", description="Test", tool=ToolType.ANSIBLE, content="")
        schedule = manager.create_schedule(pb.id, "Daily", "0 2 * * *")
        assert manager.delete_schedule(schedule.id) == True


class TestMinions:
    def test_register_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50", grains={"os": "Ubuntu", "kernel": "5.4"}, tags=["production", "worker"])
        assert minion.id is not None
        assert minion.name == "minion-01"
        assert minion.grains["os"] == "Ubuntu"

    def test_get_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50")
        retrieved = manager.get_minion(minion.id)
        assert retrieved is not None

    def test_delete_minion(self, manager):
        minion = manager.register_minion("minion-01", "192.168.1.50")
        assert manager.delete_minion(minion.id) == True


class TestTemplates:
    def test_create_template(self, manager):
        tmpl = manager.create_template("Deploy", "Standard deploy", ToolType.ANSIBLE, "- hosts: all\ntasks:\n  - ping:", category="deployment", tags=["deploy"])
        assert tmpl.id is not None
        assert tmpl.name == "Deploy"

    def test_apply_template(self, manager):
        tmpl = manager.create_template("Deploy", "Standard deploy", ToolType.ANSIBLE, "- hosts: all\ntasks:\n  - ping:")
        pb = manager.apply_template(tmpl.id, "My Deploy", "My deploy")
        assert pb is not None
        assert pb.name == "My Deploy"


class TestInventoryGeneration:
    def test_generate_ini(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_group(inv.id, "webservers")
        manager.add_host(inv.id, "web01", "192.168.1.10", groups=["webservers"])
        ini = manager.generate_inventory_ini(inv.id)
        assert ini is not None
        assert "[webservers]" in ini
        assert "192.168.1.10" in ini

    def test_generate_yaml(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_group(inv.id, "dbservers")
        manager.add_host(inv.id, "db01", "192.168.1.20", groups=["dbservers"])
        yaml_out = manager.generate_inventory_yaml(inv.id)
        assert yaml_out is not None
        assert "dbservers" in yaml_out


class TestSearch:
    def test_search_playbooks(self, manager):
        manager.create_playbook(name="Deploy Web", description="Web deployment", tool=ToolType.ANSIBLE, content="")
        manager.create_playbook(name="Backup DB", description="Database backup", tool=ToolType.ANSIBLE, content="")
        results = manager.search_playbooks("deploy")
        assert len(results) >= 1


class TestDuplicate:
    def test_duplicate_playbook(self, manager):
        pb = manager.create_playbook(name="Original", description="Original", tool=ToolType.ANSIBLE, content="- hosts: all")
        clone = manager.duplicate_playbook(pb.id, "Clone")
        assert clone is not None
        assert clone.name == "Clone"
        assert clone.id != pb.id


class TestStatistics:
    def test_get_statistics(self, manager):
        inv = manager.create_inventory(name="Prod")
        manager.add_host(inv.id, "web01", "10.0.0.1")
        stats = manager.get_statistics()
        assert stats["total_inventories"] >= 1
        assert stats["total_hosts"] >= 1
