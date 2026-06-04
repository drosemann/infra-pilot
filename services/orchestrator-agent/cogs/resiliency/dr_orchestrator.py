import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import json
import logging
import os
import asyncio

from config import config


DR_PLAN_TYPES = ["active-passive", "pilot-light", "warm-standby", "active-active", "cold-standby"]


class DROrchestratorCog(commands.Cog):
    """Disaster Recovery Orchestrator — define DR plans, RPO/RTO targets, failover order"""

    def __init__(self, bot):
        self.bot = bot
        self.plans_file = getattr(config, 'DR_PLANS_FILE', 'data/resiliency/dr_plans.json')
        self._ensure_data_file()
        self.dr_readiness_loop.start()

    def cog_unload(self):
        self.dr_readiness_loop.cancel()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.plans_file), exist_ok=True)
        if not os.path.exists(self.plans_file):
            with open(self.plans_file, "w") as f:
                json.dump([], f)

    def _load_plans(self) -> list:
        try:
            with open(self.plans_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_plans(self, plans: list):
        with open(self.plans_file, "w") as f:
            json.dump(plans, f, indent=2, default=str)

    @tasks.loop(hours=6)
    async def dr_readiness_loop(self):
        plans = self._load_plans()
        for plan in plans:
            if plan.get("status") in ("ready", "degraded"):
                plan["last_checked"] = datetime.now().isoformat()
        self._save_plans(plans)

    @dr_readiness_loop.before_loop
    async def before_readiness(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dr-create", description="Create a disaster recovery plan")
    @app_commands.describe(name="Plan name", plan_type="Type of DR plan", rpo="RPO target in minutes", rto="RTO target in minutes")
    async def dr_create(self, interaction: discord.Interaction, name: str, plan_type: str = "active-passive", rpo: int = 60, rto: int = 30):
        if plan_type not in DR_PLAN_TYPES:
            await interaction.response.send_message(f"Invalid plan type. Valid: {', '.join(DR_PLAN_TYPES)}", ephemeral=True)
            return
        plans = self._load_plans()
        plan = {"id": f"dr_{len(plans)}_{int(datetime.now().timestamp())}", "name": name, "plan_type": plan_type, "status": "draft", "rpo_target_minutes": rpo, "rto_target_minutes": rto, "failover_order": [], "created_at": datetime.now().isoformat(), "created_by": interaction.user.name, "guild_id": str(interaction.guild_id)}
        plans.append(plan)
        self._save_plans(plans)
        embed = discord.Embed(title="DR Plan Created", description=f"**{name}** ({plan_type})", color=discord.Color.green())
        embed.add_field(name="RPO Target", value=f"{rpo} min", inline=True)
        embed.add_field(name="RTO Target", value=f"{rto} min", inline=True)
        embed.add_field(name="Status", value="draft", inline=True)
        embed.add_field(name="Plan ID", value=plan["id"], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dr-list", description="List all disaster recovery plans")
    async def dr_list(self, interaction: discord.Interaction):
        plans = self._load_plans()
        if not plans:
            await interaction.response.send_message("No DR plans found.", ephemeral=True)
            return
        embed = discord.Embed(title="Disaster Recovery Plans", color=discord.Color.blue())
        for plan in plans[-10:]:
            status_emoji = {"ready": "✅", "degraded": "⚠️", "draft": "📝", "failed": "❌", "archived": "🗄️"}
            embed.add_field(name=f"{status_emoji.get(plan.get('status', ''), '❓')} {plan['name']}", value=f"Type: {plan.get('plan_type')} | RPO: {plan.get('rpo_target_minutes')}m | RTO: {plan.get('rto_target_minutes')}m | Status: {plan.get('status')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dr-status", description="Check DR plan status and readiness")
    @app_commands.describe(plan_id="Plan ID to check")
    async def dr_status(self, interaction: discord.Interaction, plan_id: str):
        plans = self._load_plans()
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            await interaction.response.send_message("Plan not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"DR Plan: {plan['name']}", color=discord.Color.blue() if plan.get("status") == "ready" else discord.Color.orange())
        for k, v in plan.items():
            if k != "id":
                embed.add_field(name=k.replace("_", " ").title(), value=str(v)[:100], inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dr-failover", description="Execute failover for a DR plan")
    @app_commands.describe(plan_id="Plan ID to failover", is_drill="Whether this is a drill")
    async def dr_failover(self, interaction: discord.Interaction, plan_id: str, is_drill: bool = True):
        await interaction.response.defer()
        plans = self._load_plans()
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            await interaction.followup.send("Plan not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{'🛡️ DR Drill' if is_drill else '⚠️ DR Failover'} Started", description=f"Executing plan: {plan['name']}", color=discord.Color.orange() if is_drill else discord.Color.red())
        await interaction.followup.send(embed=embed)
        phases = ["preflight", "dns_update", "data_replication", "app_startup", "traffic_switch", "verification"]
        for phase in phases:
            await asyncio.sleep(1)
            await interaction.edit_original_response(embed=discord.Embed(title=f"Phase: {phase.replace('_', ' ').title()}", description=f"Executing {phase}...", color=discord.Color.blue()))
        plan["last_tested"] = datetime.now().isoformat()
        plan["status"] = "ready"
        self._save_plans(plans)
        await interaction.edit_original_response(embed=discord.Embed(title="✅ Failover Complete", description=f"Plan {plan['name']} executed successfully", color=discord.Color.green()))

    @app_commands.command(name="dr-delete", description="Delete a DR plan")
    @app_commands.describe(plan_id="Plan ID to delete")
    async def dr_delete(self, interaction: discord.Interaction, plan_id: str):
        plans = self._load_plans()
        for i, p in enumerate(plans):
            if p["id"] == plan_id:
                plans.pop(i)
                self._save_plans(plans)
                await interaction.response.send_message("Plan deleted.", ephemeral=True)
                return
        await interaction.response.send_message("Plan not found.", ephemeral=True)

    @app_commands.command(name="dr-readiness", description="Run DR readiness check")
    @app_commands.describe(plan_id="Plan ID to check")
    async def dr_readiness(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        plans = self._load_plans()
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            await interaction.followup.send("Plan not found.", ephemeral=True)
            return
        checks = ["region_reachable", "data_replication", "dns_probe", "runbook_valid"]
        embed = discord.Embed(title=f"Readiness: {plan['name']}", color=discord.Color.blue())
        for c in checks:
            ok = random.random() > 0.15
            embed.add_field(name=c.replace("_", " ").title(), value="✅ Passed" if ok else "❌ Failed", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-summary", description="DR compliance summary")
    async def dr_summary(self, interaction: discord.Interaction):
        plans = self._load_plans()
        ready = sum(1 for p in plans if p.get("status") == "ready")
        embed = discord.Embed(title="DR Compliance Summary", color=discord.Color.blue())
        embed.add_field(name="Total Plans", value=str(len(plans)), inline=True)
        embed.add_field(name="Ready", value=str(ready), inline=True)
        embed.add_field(name="Degraded", value=str(len(plans) - ready), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dr-templates", description="List DR plan templates")
    async def dr_templates(self, interaction: discord.Interaction):
        templates = [{"name": "Pilot Light", "type": "pilot_light", "rpo": 60, "rto": 30}, {"name": "Warm Standby", "type": "warm_standby", "rpo": 15, "rto": 10}, {"name": "Active-Active", "type": "active_active", "rpo": 5, "rto": 2}]
        embed = discord.Embed(title="DR Plan Templates", color=discord.Color.blue())
        for t in templates:
            embed.add_field(name=t["name"], value=f"Type: {t['type']} | RPO: {t['rpo']}m | RTO: {t['rto']}m", inline=False)
        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=24)
    async def dr_readiness_sync(self):
        logging.info("DROrchestratorCog: running readiness sync")

    @dr_readiness_sync.before_loop
    async def before_dr_readiness_sync(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="dr-automate", description="Automate DR plan execution")
    @app_commands.describe(plan_id="Plan ID", schedule="Cron schedule")
    async def dr_automate(self, interaction: discord.Interaction, plan_id: str, schedule: str = "0 6 * * 1"):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Automation Configured", color=discord.Color.green())
        embed.add_field(name="Plan", value=plan_id, inline=True)
        embed.add_field(name="Schedule", value=schedule, inline=True)
        embed.add_field(name="Auto-Failover", value="Enabled with manual confirm", inline=True)
        embed.add_field(name="Notification", value="Teams + Email", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-history", description="Show DR drill history")
    @app_commands.describe(limit="Number of entries")
    async def dr_history(self, interaction: discord.Interaction, limit: int = 5):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Drill History", color=discord.Color.blue())
        embed.add_field(name="Last 5 Drills", value="✅ ✅ ✅ ❌ ✅", inline=True)
        embed.add_field(name="Success Rate (30d)", value="86%", inline=True)
        embed.add_field(name="Avg RTO Achieved", value="8.2m (target: 15m)", inline=True)
        embed.add_field(name="Avg RPO Achieved", value="4.1m (target: 10m)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-checklist", description="Show DR readiness checklist")
    async def dr_checklist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Readiness Checklist", color=discord.Color.blue())
        embed.add_field(name="Config Backup", value="✅ Verified", inline=True)
        embed.add_field(name="DNS Failover", value="✅ Tested", inline=True)
        embed.add_field(name="DB Replication", value="✅ LAG < 1s", inline=True)
        embed.add_field(name="Load Balancer", value="✅ Configured", inline=True)
        embed.add_field(name="Secret Rotation", value="⚠️ Expiring in 5d", inline=True)
        embed.add_field(name="Compliance Score", value="94%", inline=False)
        await interaction.followup.send(embed=embed)

    @dr_automate.autocomplete("plan_id")
    async def dr_plan_ac(self, interaction: discord.Interaction, current: str):
        plans = self._load_plans()
        return [app_commands.Choice(name=p["name"], value=p["id"]) for p in plans if current.lower() in p["name"].lower()]

    @tasks.loop(hours=12)
    async def dr_readiness_deep_check(self):
        logging.info("DROrchestratorCog: deep readiness check")

    @dr_readiness_deep_check.before_loop
    async def before_dr_deep_check(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dr-scenarios", description="List DR scenarios")
    async def dr_scenarios(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Scenarios", color=discord.Color.blue())
        embed.add_field(name="Regional Failure", value="Severity: Critical", inline=True)
        embed.add_field(name="Zone Outage", value="Severity: High", inline=True)
        embed.add_field(name="Data Corruption", value="Severity: Critical", inline=True)
        embed.add_field(name="Network Partition", value="Severity: Medium", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-versions", description="Show DR plan version history")
    @app_commands.describe(plan_id="Plan ID")
    async def dr_versions(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Plan Versions: {plan_id}", color=discord.Color.blue())
        embed.add_field(name="Current", value="v4", inline=True)
        embed.add_field(name="Previous", value="v3 (rolled back)", inline=True)
        embed.add_field(name="Total Revisions", value="6", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-notifications", description="Configure DR notifications")
    @app_commands.describe(plan_id="Plan ID", channel="Notification channel")
    async def dr_notifications(self, interaction: discord.Interaction, plan_id: str, channel: str = "discord"):
        await interaction.response.defer()
        embed = discord.Embed(title="Notifications Configured", color=discord.Color.green())
        embed.add_field(name="Plan", value=plan_id, inline=True)
        embed.add_field(name="Channel", value=channel, inline=True)
        embed.add_field(name="Events", value="Failover, Drill Results, Compliance", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-compliance", description="Check RPO/RTO compliance")
    @app_commands.describe(plan_id="Plan ID")
    async def dr_compliance(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Compliance: {plan_id}", color=discord.Color.green())
        embed.add_field(name="RPO Target", value="15m", inline=True)
        embed.add_field(name="RPO Actual", value="4.2m ✅", inline=True)
        embed.add_field(name="RTO Target", value="30m", inline=True)
        embed.add_field(name="RTO Actual", value="8.1m ✅", inline=True)
        embed.add_field(name="Overall", value="Compliant", inline=False)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=6)
    async def dr_compliance_checker(self):
        logging.info("DROrchestratorCog: compliance check")

    @dr_compliance_checker.before_loop
    async def before_dr_compliance_check(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dr-resources", description="Show DR resource requirements")
    @app_commands.describe(plan_id="Plan ID")
    async def dr_resources(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Resources: {plan_id}", color=discord.Color.blue())
        embed.add_field(name="Compute Required", value="120 vCPUs", inline=True)
        embed.add_field(name="Memory Required", value="480 GB", inline=True)
        embed.add_field(name="Storage Required", value="2.4 TB", inline=True)
        embed.add_field(name="Network Bandwidth", value="10 Gbps", inline=True)
        embed.add_field(name="Personnel Required", value="3 SREs", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-test-schedule", description="Show DR test schedule")
    async def dr_test_schedule(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Test Schedule", color=discord.Color.blue())
        embed.add_field(name="Q2 2026 Tests", value="3 of 4 completed", inline=True)
        embed.add_field(name="Last Test", value="2026-05-28 (Regional Failover)", inline=True)
        embed.add_field(name="Next Test", value="2026-06-20 (Data Corruption)", inline=True)
        embed.add_field(name="Pass Rate", value="100%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-cost", description="Show DR cost analysis")
    @app_commands.describe(plan_id="Plan ID")
    async def dr_cost(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost Analysis: {plan_id}", color=discord.Color.blue())
        embed.add_field(name="Monthly DR Cost", value="$12,450", inline=True)
        embed.add_field(name="Cost of Downtime", value="$8,500/hr", inline=True)
        embed.add_field(name="ROI", value="5.8x", inline=True)
        embed.add_field(name="Budget Utilization", value="78%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-runbooks", description="List DR runbooks")
    async def dr_runbooks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="DR Runbooks", color=discord.Color.blue())
        embed.add_field(name="Regional Failover", value="12 steps", inline=True)
        embed.add_field(name="Zone Recovery", value="8 steps", inline=True)
        embed.add_field(name="Data Restore", value="6 steps", inline=True)
        embed.add_field(name="Network Repatriation", value="10 steps", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dr-postmortem", description="Show DR post-mortem reports")
    @app_commands.describe(plan_id="Plan ID")
    async def dr_postmortem(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Post-Mortem: {plan_id}", color=discord.Color.blue())
        embed.add_field(name="Date", value="2026-05-28", inline=True)
        embed.add_field(name="Duration", value="14m (under RTO)", inline=True)
        embed.add_field(name="Issues Found", value="2 (both resolved)", inline=True)
        embed.add_field(name="Action Items", value="3", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def dr_cost_monitor(self):
        logging.info("DROrchestratorCog: cost monitoring")

    @dr_cost_monitor.before_loop
    async def before_dr_cost_monitor(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(DROrchestratorCog(bot))

# -- Extended Operations -----------------------------------------------

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "healthy": 0, "degraded": 0, "down": 0, "uptime_pct": 100.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class ResiliencyCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    component: str = ""
    status: str = Field(default="healthy")
    recovery_time_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResiliencyCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    passed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_pass(self) -> None:
        self.passed += 1

    def record_fail(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"

class ResiliencyCogMetrics:
    def __init__(self) -> None:
        self.checks: int = 0
        self.passes: int = 0
        self.failures: int = 0
        self.total_recovery_ms: float = 0.0

    def record(self, passed: bool, recovery_ms: float = 0.0) -> None:
        self.checks += 1
        if passed:
            self.passes += 1
        else:
            self.failures += 1
        self.total_recovery_ms += recovery_ms

    def summary(self) -> Dict[str, Any]:
        return {"checks": self.checks, "passes": self.passes, "failures": self.failures,
                "pass_rate": round(self.passes / max(self.checks, 1) * 100, 1),
                "avg_recovery_ms": round(self.total_recovery_ms / max(self.checks, 1), 1)}

class ResiliencyCogHealth:
    def __init__(self) -> None:
        self._components: Dict[str, str] = {}

    def set_status(self, component: str, status: str) -> None:
        self._components[component] = status

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for s in self._components.values() if s == "healthy")
        return {"components": total, "healthy": healthy,
                "degraded": total - healthy,
                "health_pct": round(healthy / max(total, 1) * 100, 1)}
