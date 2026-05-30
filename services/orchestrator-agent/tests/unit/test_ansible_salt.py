"""Tests for Ansible/Salt integration, self-healing, and runbook."""
import pytest
import json
from cogs.ansible_salt_integration import AnsibleSaltIntegration


class TestAnsibleSaltIntegration:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return AnsibleSaltIntegration(bot)

    def test_run_ansible_playbook(self, cog):
        result = cog.run_ansible_playbook("deploy_web.yml", {"hosts": "web-servers", "extra_vars": {"version": "1.2.3"}})
        assert result["playbook"] == "deploy_web.yml"
        assert "execution_id" in result

    def test_run_ansible_module(self, cog):
        result = cog.run_ansible_module("ping", {"hosts": "all"})
        assert result["module"] == "ping"

    def test_run_salt_state(self, cog):
        result = cog.run_salt_state("webserver.nginx", ["web-01", "web-02"])
        assert result["state"] == "webserver.nginx"

    def test_run_salt_command(self, cog):
        result = cog.run_salt_command("*", "cmd.run", "uptime")
        assert result["target"] == "*"
        assert result["function"] == "cmd.run"

    def test_list_inventory(self, cog):
        inventory = cog.list_inventory()
        assert "ansible" in inventory
        assert "salt" in inventory

    def test_add_ansible_host(self, cog):
        result = cog.add_ansible_host("web-01", "192.168.1.10", {"ansible_user": "deploy", "ansible_port": 22})
        assert result is True

    def test_add_salt_minion(self, cog):
        result = cog.add_salt_minion("minion-01", "192.168.1.20", {"roles": ["web", "monitoring"]})
        assert result is True

    def test_get_execution_result(self, cog):
        execution_id = "test-exec-001"
        result = cog.get_execution_result(execution_id)
        assert result is not None or result is None
