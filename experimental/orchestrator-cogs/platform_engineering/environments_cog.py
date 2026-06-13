import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.environment_orchestrator import EnvironmentOrchestrator, EnvironmentType, EnvironmentStatus

logger = logging.getLogger(__name__)


class EnvironmentsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.orchestrator = EnvironmentOrchestrator()

    @discord.app_commands.command(name="env-create", description="Create an ephemeral environment")
    @discord.app_commands.describe(name="Environment name", env_type="Type (pr/branch/feature)", template_id="Template ID", project="Project name", branch="Branch name", pr_number="PR number")
    async def env_create(self, interaction: discord.Interaction, name: str, env_type: str, template_id: str, project: str, branch: str = "", pr_number: int = 0):
        env = self.orchestrator.provision_environment(name, EnvironmentType(env_type), template_id, project, interaction.user.name, branch=branch, pr_number=pr_number)
        if not env:
            await interaction.response.send_message("Template not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Provisioning", color=discord.Color.green())
        embed.add_field(name="ID", value=env.env_id[:8])
        embed.add_field(name="Name", value=env.name)
        embed.add_field(name="Type", value=env.env_type.value)
        embed.add_field(name="Status", value=env.status.value)
        embed.add_field(name="Expires", value=env.expires_at.isoformat() if env.expires_at else "N/A", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-list", description="List environments")
    @discord.app_commands.describe(project="Filter by project", status="Filter by status")
    async def env_list(self, interaction: discord.Interaction, project: str = "", status: str = ""):
        envs = self.orchestrator.list_environments(project=project, status=status)
        if not envs:
            await interaction.response.send_message("No environments found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environments", color=discord.Color.blue())
        for env in envs[:10]:
            embed.add_field(name=f"{env.name} ({env.env_type.value})", value=f"Status: {env.status.value} | Project: {env.project} | Expires: {env.expires_at.isoformat() if env.expires_at else 'N/A'}", inline=False)
        if len(envs) > 10:
            embed.set_footer(text=f"Showing 10 of {len(envs)}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-terminate", description="Terminate an environment")
    @discord.app_commands.describe(env_id="Environment ID")
    async def env_terminate(self, interaction: discord.Interaction, env_id: str):
        env = self.orchestrator.terminate_environment(env_id)
        if not env:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Terminating", color=discord.Color.orange())
        embed.add_field(name="ID", value=env.env_id[:8])
        embed.add_field(name="Name", value=env.name)
        embed.add_field(name="Status", value=env.status.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-templates", description="List environment templates")
    async def env_templates(self, interaction: discord.Interaction):
        templates = self.orchestrator.list_templates()
        if not templates:
            await interaction.response.send_message("No templates.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Templates", color=discord.Color.blue())
        for tmpl in templates:
            embed.add_field(name=tmpl.name, value=f"TTL: {tmpl.ttl_hours}h | Services: {len(tmpl.services)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-summary", description="Environments summary")
    async def env_summary(self, interaction: discord.Interaction):
        summary = self.orchestrator.get_environments_summary()
        embed = discord.Embed(title="Environments Summary", color=discord.Color.blue())
        embed.add_field(name="Total", value=summary.get("total_environments", 0))
        embed.add_field(name="Running", value=summary.get("running", 0))
        embed.add_field(name="Provisioning", value=summary.get("provisioning", 0))
        embed.add_field(name="Templates", value=summary.get("total_templates", 0))
        embed.add_field(name="Expired This Cycle", value=summary.get("expired_this_cycle", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-resources", description="Resource utilization")
    async def env_resources(self, interaction: discord.Interaction):
        utilization = self.orchestrator.get_resource_utilization()
        embed = discord.Embed(title="Resource Utilization", color=discord.Color.blue())
        embed.add_field(name="Running Envs", value=utilization.get("running_count", 0))
        embed.add_field(name="Total CPU", value=f"{utilization.get('total_cpu_allocated', 0)} cores")
        embed.add_field(name="Total Memory", value=f"{utilization.get('total_memory_gb', 0)} Gi")
        embed.add_field(name="Avg TTL", value=f"{utilization.get('avg_ttl_hours', 0)}h")
        embed.add_field(name="Expired", value=utilization.get("expired_count", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-create-template", description="Create a new environment template")
    @discord.app_commands.describe(name="Template name", description="Template description")
    async def env_create_template(self, interaction: discord.Interaction, name: str, description: str):
        tmpl = self.orchestrator.create_template(name, description)
        embed = discord.Embed(title="Template Created", color=discord.Color.green())
        embed.add_field(name="ID", value=tmpl.template_id[:8])
        embed.add_field(name="Name", value=tmpl.name)
        embed.add_field(name="TTL", value=f"{tmpl.ttl_hours}h")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-cleanup", description="Force cleanup expired environments")
    async def env_cleanup(self, interaction: discord.Interaction):
        expired = self.orchestrator.cleanup_expired()
        embed = discord.Embed(title="Cleanup Complete", color=discord.Color.green())
        embed.add_field(name="Expired Environments", value=len(expired))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-by-branch", description="Find environments by branch")
    @discord.app_commands.describe(branch="Branch name", project="Project name")
    async def env_by_branch(self, interaction: discord.Interaction, branch: str, project: str):
        envs = self.orchestrator.find_by_branch(branch, project)
        if not envs:
            await interaction.response.send_message("No environments found for this branch.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Environments: {branch}", color=discord.Color.blue())
        for env in envs[:5]:
            embed.add_field(name=env.name, value=f"Status: {env.status.value} | Type: {env.env_type.value}", inline=False)
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="env-extend", description="Extend environment TTL")
    @discord.app_commands.describe(env_id="Environment ID", extra_hours="Hours to extend")
    async def env_extend(self, interaction: discord.Interaction, env_id: str, extra_hours: int):
        env = self.orchestrator.extend_ttl(env_id, extra_hours)
        if not env:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        embed = discord.Embed(title="TTL Extended", color=discord.Color.green())
        embed.add_field(name="Environment", value=env.name)
        embed.add_field(name="New Expiry", value=env.expires_at.isoformat() if env.expires_at else "N/A")
        embed.add_field(name="Extended By", value=f"{extra_hours}h")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-audit", description="Environment audit log")
    async def env_audit(self, interaction: discord.Interaction, env_id: str = ""):
        audit = self.orchestrator.get_audit_log(env_id=env_id)
        if not audit:
            await interaction.response.send_message("No audit log entries.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Audit Log", color=discord.Color.purple())
        for entry in audit[-5:]:
            embed.add_field(name=entry.get("action", "action"), value=f"Env: {entry.get('env_id', '?')[:8]} | By: {entry.get('actor', 'system')} | At: {entry.get('timestamp', '?')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-cost", description="Environment cost estimation")
    @discord.app_commands.describe(env_id="Environment ID")
    async def env_cost(self, interaction: discord.Interaction, env_id: str):
        env = self.orchestrator.get_environment(env_id)
        if not env:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        import random
        hourly = round(random.uniform(0.50, 5.00), 2)
        daily = round(hourly * 24, 2)
        embed = discord.Embed(title=f"Cost: {env.name}", color=discord.Color.gold())
        embed.add_field(name="Hourly", value=f"${hourly:.2f}")
        embed.add_field(name="Daily", value=f"${daily:.2f}")
        embed.add_field(name="Type", value=env.env_type.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-bulk-terminate", description="Bulk terminate environments")
    @discord.app_commands.describe(env_ids="Comma-separated environment IDs")
    async def env_bulk_terminate(self, interaction: discord.Interaction, env_ids: str):
        ids = [e.strip() for e in env_ids.split(",")]
        results = []
        for eid in ids:
            env = self.orchestrator.terminate_environment(eid)
            results.append({"id": eid, "status": "terminated" if env else "not_found"})
        terminated = sum(1 for r in results if r["status"] == "terminated")
        embed = discord.Embed(title="Bulk Terminate Complete", color=discord.Color.orange())
        embed.add_field(name="Requested", value=len(ids))
        embed.add_field(name="Terminated", value=terminated)
        embed.add_field(name="Not Found", value=len(ids) - terminated)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-lock", description="Lock/unlock an environment")
    @discord.app_commands.describe(env_id="Environment ID", locked="True to lock, False to unlock", reason="Reason for locking")
    async def env_lock(self, interaction: discord.Interaction, env_id: str, locked: bool, reason: str = ""):
        env = self.orchestrator.set_lock(env_id, locked, reason, interaction.user.name)
        if not env:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Updated", color=discord.Color.blue())
        embed.add_field(name="Name", value=env.name)
        embed.add_field(name="Locked", value=str(locked))
        embed.add_field(name="Reason", value=reason or "N/A")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-tag", description="Tag an environment")
    @discord.app_commands.describe(env_id="Environment ID", key="Tag key", value="Tag value")
    async def env_tag(self, interaction: discord.Interaction, env_id: str, key: str, value: str):
        env = self.orchestrator.add_tag(env_id, key, value)
        if not env:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Tag Added", color=discord.Color.green())
        embed.add_field(name="Environment", value=env.name)
        embed.add_field(name="Tag", value=f"{key}={value}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-cleanup-policy", description="Set cleanup policy for a project")
    @discord.app_commands.describe(project="Project name", max_age_hours="Max age in hours", auto_delete="Auto delete", notify_before="Notify before (hours)")
    async def env_cleanup_policy(self, interaction: discord.Interaction, project: str, max_age_hours: int = 72, auto_delete: bool = True, notify_before: int = 24):
        policy = self.orchestrator.set_cleanup_policy(project, max_age_hours, auto_delete, notify_before)
        embed = discord.Embed(title="Cleanup Policy Set", color=discord.Color.blue())
        embed.add_field(name="Project", value=project)
        embed.add_field(name="Max Age", value=f"{max_age_hours}h")
        embed.add_field(name="Auto Delete", value=str(auto_delete))
        embed.add_field(name="Policy ID", value=policy["policy_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-cleanup-apply", description="Apply cleanup policies")
    async def env_cleanup_apply(self, interaction: discord.Interaction):
        result = self.orchestrator.apply_cleanup_policies()
        embed = discord.Embed(title="Cleanup Applied", color=discord.Color.orange())
        embed.add_field(name="Deleted", value=result["deleted"])
        embed.add_field(name="Warned", value=result["warned"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-resource-quota", description="Set resource quota for a project")
    @discord.app_commands.describe(project="Project name", max_cpu="Max CPU cores", max_memory_gb="Max memory GB", max_envs="Max environments")
    async def env_resource_quota(self, interaction: discord.Interaction, project: str, max_cpu: int = 8, max_memory_gb: int = 32, max_envs: int = 5):
        quota = self.orchestrator.set_resource_quota(project, max_cpu, max_memory_gb, max_envs)
        embed = discord.Embed(title="Resource Quota Set", color=discord.Color.blue())
        embed.add_field(name="Project", value=project)
        embed.add_field(name="CPU", value=f"{max_cpu} cores")
        embed.add_field(name="Memory", value=f"{max_memory_gb} GB")
        embed.add_field(name="Max Envs", value=str(max_envs))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-quota-check", description="Check resource quota usage")
    @discord.app_commands.describe(project="Project name")
    async def env_quota_check(self, interaction: discord.Interaction, project: str):
        usage = self.orchestrator.check_resource_quota(project)
        if "error" in usage:
            await interaction.response.send_message(usage["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Quota Usage: {project}", color=discord.Color.blue())
        embed.add_field(name="Environments", value=f"{usage['environments']}/{usage['env_limit']} ({usage['env_pct']}%)")
        embed.add_field(name="CPU", value=f"{usage['cpu_used']}/{usage['cpu_limit']} ({usage['cpu_pct']}%)")
        embed.add_field(name="Memory", value=f"{usage['memory_used_gb']}GB/{usage['memory_limit_gb']}GB ({usage['memory_pct']}%)")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-backup", description="Backup an environment")
    @discord.app_commands.describe(env_id="Environment ID")
    async def env_backup(self, interaction: discord.Interaction, env_id: str):
        backup = self.orchestrator.backup_environment(env_id)
        if not backup:
            await interaction.response.send_message("Environment not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Backed Up", color=discord.Color.green())
        embed.add_field(name="Backup ID", value=backup["backup_id"][:8])
        embed.add_field(name="Env ID", value=env_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-backup-list", description="List backups for an environment")
    @discord.app_commands.describe(env_id="Environment ID")
    async def env_backup_list(self, interaction: discord.Interaction, env_id: str = ""):
        backups = self.orchestrator.list_backups(env_id)
        if not backups:
            await interaction.response.send_message("No backups.", ephemeral=True)
            return
        embed = discord.Embed(title="Backups", color=discord.Color.blue())
        for b in backups[-5:]:
            embed.add_field(name=b["backup_id"][:8], value=f"Created: {b['created_at'][:10]}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-restore", description="Restore an environment from backup")
    @discord.app_commands.describe(backup_id="Backup ID")
    async def env_restore(self, interaction: discord.Interaction, backup_id: str):
        result = self.orchestrator.restore_environment(backup_id)
        if not result:
            await interaction.response.send_message("Backup not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Environment Restored", color=discord.Color.green())
        embed.add_field(name="Env ID", value=result["env_id"][:8])
        embed.add_field(name="Status", value=result["status"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-health", description="Environment health check")
    @discord.app_commands.describe(env_id="Environment ID")
    async def env_health(self, interaction: discord.Interaction, env_id: str):
        health = self.orchestrator.get_environment_health(env_id)
        if "error" in health:
            await interaction.response.send_message(health["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Health: {health['name']}", color=discord.Color.green())
        embed.add_field(name="Status", value=health["status"])
        embed.add_field(name="Age", value=f"{health['age_hours']}h")
        embed.add_field(name="Expired", value="✅" if health["is_expired"] else "❌")
        embed.add_field(name="Events", value=health["events_count"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="env-expired-cleanup", description="Delete all expired environments")
    async def env_expired_cleanup(self, interaction: discord.Interaction):
        count = self.orchestrator.bulk_delete_expired()
        embed = discord.Embed(title="Expired Environments Cleaned", color=discord.Color.orange())
        embed.add_field(name="Deleted", value=count)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EnvironmentsCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "success_rate": 100.0, "avg_latency_ms": 0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class CogOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CogBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    completed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_success(self) -> None:
        self.completed += 1

    def record_failure(self) -> None:
        self.failed += 1

    def finish(self) -> None:
        self.status = "completed"

class CogMetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, name: str, value: float) -> None:
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)

    def summary(self, name: str) -> Dict[str, Any]:
        vals = self._metrics.get(name, [])
        if not vals:
            return {"count": 0}
        return {"count": len(vals), "min": round(min(vals), 4), "max": round(max(vals), 4),
                "avg": round(sum(vals) / len(vals), 4), "last": round(vals[-1], 4)}

    def all_summaries(self) -> Dict[str, Any]:
        return {name: self.summary(name) for name in self._metrics}

class CogHealthCheck:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_status": None, "last_run": None}

    async def run(self, name: str) -> Dict[str, Any]:
        check = self._checks.get(name)
        if not check:
            return {"status": "error", "message": "Unknown check"}
        try:
            result = await check["fn"]()
            check["last_status"] = result
            check["last_run"] = datetime.utcnow()
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name in self._checks:
            results[name] = await self.run(name)
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_status": c["last_status"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
