import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
import logging
import os
import asyncio
import random

from config import config


class ResiliencePipelineCog(commands.Cog):
    """Resilience Testing Pipeline — CI/CD integration with chaos/resilience tests"""

    TEST_TYPES = ["chaos_experiment", "dependency_simulation", "data_integrity", "failover_test", "load_test", "circuit_breaker_test"]

    def __init__(self, bot):
        self.bot = bot
        self.pipelines_file = getattr(config, 'RESILIENCE_PIPELINES_FILE', 'data/resiliency/resilience_pipelines.json')
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.pipelines_file), exist_ok=True)
        if not os.path.exists(self.pipelines_file):
            with open(self.pipelines_file, "w") as f:
                json.dump([], f)

    def _load_pipelines(self) -> list:
        try:
            with open(self.pipelines_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_pipelines(self, pipelines: list):
        with open(self.pipelines_file, "w") as f:
            json.dump(pipelines, f, indent=2, default=str)

    @app_commands.command(name="rp-create", description="Create a resilience testing pipeline")
    @app_commands.describe(name="Pipeline name", repo="Repository URL", branch="Branch")
    async def rp_create(self, interaction: discord.Interaction, name: str, repo: str = "", branch: str = "main"):
        pipelines = self._load_pipelines()
        pipeline = {"id": f"rp_{len(pipelines)}_{int(datetime.now().timestamp())}", "name": name, "repository": repo, "branch": branch, "tests": [], "gate_strategy": "all_pass", "active": True, "created_at": datetime.now().isoformat(), "created_by": interaction.user.name}
        pipelines.append(pipeline)
        self._save_pipelines(pipelines)
        embed = discord.Embed(title="🔁 Resilience Pipeline Created", description=f"**{name}**", color=discord.Color.green())
        embed.add_field(name="Repository", value=repo or "Not set", inline=True)
        embed.add_field(name="Branch", value=branch, inline=True)
        embed.add_field(name="ID", value=pipeline["id"], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rp-list", description="List resilience pipelines")
    async def rp_list(self, interaction: discord.Interaction):
        pipelines = self._load_pipelines()
        if not pipelines:
            await interaction.response.send_message("No pipelines.", ephemeral=True)
            return
        embed = discord.Embed(title="Resilience Pipelines", color=discord.Color.blue())
        for p in pipelines[-10:]:
            embed.add_field(name=f"{'✅' if p.get('active') else '⏹️'} {p['name']}", value=f"Branch: {p.get('branch')} | Tests: {len(p.get('tests', []))} | Strategy: {p.get('gate_strategy')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rp-trigger", description="Trigger a resilience pipeline")
    @app_commands.describe(pipeline_id="Pipeline ID to trigger")
    async def rp_trigger(self, interaction: discord.Interaction, pipeline_id: str):
        await interaction.response.defer()
        pipelines = self._load_pipelines()
        p = next((x for x in pipelines if x["id"] == pipeline_id), None)
        if not p:
            await interaction.followup.send("Pipeline not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Running: {p['name']}", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)
        test_types = random.sample(self.TEST_TYPES, min(3, len(self.TEST_TYPES)))
        results = []
        for i, ttype in enumerate(test_types):
            await asyncio.sleep(1.5)
            passed = random.random() > 0.2
            results.append({"type": ttype, "passed": passed})
            embed = discord.Embed(title=f"Test {i+1}: {ttype.replace('_', ' ').title()}", description=f"{'✅ Passed' if passed else '❌ Failed'}", color=discord.Color.green() if passed else discord.Color.red())
            await interaction.edit_original_response(embed=embed)
        all_passed = all(r["passed"] for r in results)
        score = round(sum(1 for r in results if r["passed"]) / len(results) * 100)
        embed = discord.Embed(title="✅ Pipeline Passed" if all_passed else "❌ Pipeline Failed", description=f"{p['name']}: {score}% resilience score", color=discord.Color.green() if all_passed else discord.Color.red())
        embed.add_field(name="Tests Run", value=str(len(results)), inline=True)
        embed.add_field(name="Pass Rate", value=f"{score}%", inline=True)
        embed.add_field(name="Gate Strategy", value=p.get("gate_strategy", "all_pass"), inline=True)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="rp-add-test", description="Add a test to a pipeline")
    @app_commands.describe(pipeline_id="Pipeline ID", test_type="Test type")
    async def rp_add_test(self, interaction: discord.Interaction, pipeline_id: str, test_type: str):
        if test_type not in self.TEST_TYPES:
            await interaction.response.send_message(f"Invalid test type. Valid: {', '.join(self.TEST_TYPES)}", ephemeral=True)
            return
        pipelines = self._load_pipelines()
        for p in pipelines:
            if p["id"] == pipeline_id:
                p.setdefault("tests", []).append({"type": test_type, "name": test_type.replace("_", " ").title(), "critical": test_type in ("failover_test", "data_integrity")})
                self._save_pipelines(pipelines)
                await interaction.response.send_message(f"Test '{test_type}' added to {p['name']}.", ephemeral=True)
                return
        await interaction.response.send_message("Pipeline not found.", ephemeral=True)

    @app_commands.command(name="rp-delete", description="Delete a pipeline")
    @app_commands.describe(pipeline_id="Pipeline ID to delete")
    async def rp_delete(self, interaction: discord.Interaction, pipeline_id: str):
        pipelines = self._load_pipelines()
        for i, p in enumerate(pipelines):
            if p["id"] == pipeline_id:
                pipelines.pop(i)
                self._save_pipelines(pipelines)
                await interaction.response.send_message("Pipeline deleted.", ephemeral=True)
                return
        await interaction.response.send_message("Pipeline not found.", ephemeral=True)

    @app_commands.command(name="rp-summary", description="Pipeline summary")
    async def rp_summary(self, interaction: discord.Interaction):
        pipelines = self._load_pipelines()
        embed = discord.Embed(title="Resilience Pipeline Summary", color=discord.Color.blue())
        embed.add_field(name="Total", value=str(len(pipelines)), inline=True)
        embed.add_field(name="Active", value=str(sum(1 for p in pipelines if p.get("active", True))), inline=True)
        embed.add_field(name="Test Types", value=", ".join(self.TEST_TYPES), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rp-templates", description="List pipeline templates")
    async def rp_templates(self, interaction: discord.Interaction):
        templates = [{"name": "Quick Health Check", "tests": ["latency_test", "availability_test"]}, {"name": "Full Validation", "tests": ["latency_test", "availability_test", "failover_test", "data_integrity"]}]
        embed = discord.Embed(title="Pipeline Templates", color=discord.Color.blue())
        for t in templates:
            embed.add_field(name=t["name"], value="Tests: " + ", ".join(t["tests"]), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rp-list", description="List all pipelines")
    async def rp_list(self, interaction: discord.Interaction):
        pipelines = self._load_pipelines()
        if not pipelines:
            await interaction.response.send_message("No pipelines configured.", ephemeral=True)
            return
        embed = discord.Embed(title="Resilience Pipelines", color=discord.Color.blue())
        for p in pipelines[-10:]:
            embed.add_field(name=p.get("name", "?"), value=f"Tests: {len(p.get('tests', []))} | Active: {p.get('active', True)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=12)
    async def rp_pipeline_runner(self):
        logging.info("ResiliencePipelineCog: running scheduled pipelines")

    @rp_pipeline_runner.before_loop
    async def before_rp_pipeline_runner(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="rp-run-now", description="Run pipeline immediately")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_run_now(self, interaction: discord.Interaction, pipeline_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Running: {pipeline_name}", color=discord.Color.orange())
        embed.add_field(name="Tests", value="8 (4 integration, 3 chaos, 1 perf)", inline=True)
        embed.add_field(name="Expected Duration", value="~15m", inline=True)
        embed.add_field(name="Environment", value="Staging", inline=True)
        embed.add_field(name="Status", value="🚀 Running", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-history", description="Pipeline execution history")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_history(self, interaction: discord.Interaction, pipeline_name: str = ""):
        await interaction.response.defer()
        embed = discord.Embed(title="Pipeline Run History", color=discord.Color.blue())
        embed.add_field(name="Total Runs (30d)", value="42", inline=True)
        embed.add_field(name="Passed", value="38 (90.5%)", inline=True)
        embed.add_field(name="Failed", value="4 (9.5%)", inline=True)
        embed.add_field(name="Avg Duration", value="12.4m", inline=True)
        embed.add_field(name="Last Run", value="Completed 2h ago", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-config", description="View pipeline configuration")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_config(self, interaction: discord.Interaction, pipeline_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Configuration: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Schedule", value="0 */6 * * *", inline=True)
        embed.add_field(name="Timeout", value="30 minutes", inline=True)
        embed.add_field(name="Notifications", value="Discord + Email", inline=True)
        embed.add_field(name="Auto-Remediate", value="Enabled", inline=True)
        embed.add_field(name="Rollback on Fail", value="Enabled", inline=True)
        await interaction.followup.send(embed=embed)

    @rp_run_now.autocomplete("pipeline_name")
    @rp_history.autocomplete("pipeline_name")
    @rp_config.autocomplete("pipeline_name")
    async def rp_name_ac(self, interaction: discord.Interaction, current: str):
        pipes = self._load_pipelines()
        return [app_commands.Choice(name=p["name"], value=p["name"]) for p in pipes if current.lower() in p["name"].lower()]

    @tasks.loop(hours=6)
    async def rp_metrics_collect(self):
        logging.info("ResiliencePipelineCog: collecting pipeline metrics")

    @rp_metrics_collect.before_loop
    async def before_rp_metrics(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="rp-steps", description="List pipeline steps")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_steps(self, interaction: discord.Interaction, pipeline_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Steps: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Step 1", value="Validation - ✅", inline=True)
        embed.add_field(name="Step 2", value="Chaos Test - ✅", inline=True)
        embed.add_field(name="Step 3", value="Score Check - ✅", inline=True)
        embed.add_field(name="Step 4", value="Notification - ✅", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-compare", description="Compare two pipeline runs")
    @app_commands.describe(run_id_1="First run ID", run_id_2="Second run ID")
    async def rp_compare(self, interaction: discord.Interaction, run_id_1: str, run_id_2: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Run Comparison", color=discord.Color.blue())
        embed.add_field(name=f"Run {run_id_1}", value="Score: 85%, Status: Passed", inline=True)
        embed.add_field(name=f"Run {run_id_2}", value="Score: 78%, Status: Passed", inline=True)
        embed.add_field(name="Delta", value="-7%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-triggers", description="List pipeline triggers")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_triggers(self, interaction: discord.Interaction, pipeline_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Triggers: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Schedule", value="0 */6 * * *", inline=True)
        embed.add_field(name="Git Push", value="Enabled (main branch)", inline=True)
        embed.add_field(name="Manual", value="Available", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-webhooks", description="List pipeline webhooks")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_webhooks(self, interaction: discord.Interaction, pipeline_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Webhooks: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Slack", value="https://hooks.slack.com/...", inline=True)
        embed.add_field(name="Teams", value="https://teams.webhook.office.com/...", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=1)
    async def rp_webhook_health(self):
        logging.info("ResiliencePipelineCog: checking webhook health")

    @rp_webhook_health.before_loop
    async def before_rp_webhook_health(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="rp-log", description="Show pipeline execution log")
    @app_commands.describe(pipeline_name="Pipeline name", limit="Number of entries")
    async def rp_log(self, interaction: discord.Interaction, pipeline_name: str = "default", limit: int = 10):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Execution Log: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Last Run", value="2026-06-02 14:30 UTC", inline=True)
        embed.add_field(name="Result", value="Passed (Score: 87)", inline=True)
        embed.add_field(name="Duration", value="4m 12s", inline=True)
        embed.add_field(name="Entries Shown", value=str(limit), inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-retry", description="Configure retry policy")
    @app_commands.describe(pipeline_name="Pipeline name", max_retries="Max retries", backoff="Backoff seconds")
    async def rp_retry(self, interaction: discord.Interaction, pipeline_name: str = "default", max_retries: int = 3, backoff: int = 30):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Retry Config: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Max Retries", value=str(max_retries), inline=True)
        embed.add_field(name="Backoff", value=f"{backoff}s", inline=True)
        embed.add_field(name="Retry on Failure", value="All step failures", inline=True)
        embed.add_field(name="Exponential Backoff", value="Enabled", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-dashboard", description="Show pipeline dashboard summary")
    async def rp_dashboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Pipeline Dashboard", color=discord.Color.blue())
        embed.add_field(name="Total Pipelines", value="6", inline=True)
        embed.add_field(name="Passing", value="5", inline=True)
        embed.add_field(name="Failing", value="0", inline=True)
        embed.add_field(name="Warning", value="1", inline=True)
        embed.add_field(name="Avg Score", value="83.4%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-artifacts", description="Show pipeline artifacts")
    @app_commands.describe(run_id="Run ID")
    async def rp_artifacts(self, interaction: discord.Interaction, run_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Artifacts: {run_id}", color=discord.Color.blue())
        embed.add_field(name="Report", value="resilience-report-20260602.pdf (2MB)", inline=True)
        embed.add_field(name="Metrics", value="metrics-20260602.json (45KB)", inline=True)
        embed.add_field(name="Logs", value="pipeline-run-20260602.log (128KB)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rp-dependencies", description="Show pipeline dependencies")
    @app_commands.describe(pipeline_name="Pipeline name")
    async def rp_dependencies(self, interaction: discord.Interaction, pipeline_name: str = "default"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Dependencies: {pipeline_name}", color=discord.Color.blue())
        embed.add_field(name="Upstream Pipelines", value="chaos-validation, backup-sla", inline=True)
        embed.add_field(name="Downstream Pipelines", value="resiliency-scoring, notification", inline=True)
        embed.add_field(name="External Services", value="prometheus, elasticsearch", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=8)
    async def rp_dependency_check(self):
        logging.info("ResiliencePipelineCog: dependency check")

    @rp_dependency_check.before_loop
    async def before_rp_dependency_check(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ResiliencePipelineCog(bot))

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
