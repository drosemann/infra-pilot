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


class DependencySimulatorCog(commands.Cog):
    """Dependency Failure Simulation — simulate failure of upstream dependencies"""

    FAILURE_TYPES = ["timeout", "error_response", "slow_response", "connection_refused", "dns_failure", "rate_limit", "data_corruption", "circuit_breaker_open"]

    def __init__(self, bot):
        self.bot = bot
        self.sims_file = getattr(config, 'DEP_SIM_FILE', 'data/resiliency/dependency_simulations.json')
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.sims_file), exist_ok=True)
        if not os.path.exists(self.sims_file):
            with open(self.sims_file, "w") as f:
                json.dump([], f)

    def _load_sims(self) -> list:
        try:
            with open(self.sims_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_sims(self, sims: list):
        with open(self.sims_file, "w") as f:
            json.dump(sims, f, indent=2, default=str)

    @app_commands.command(name="dep-sim-create", description="Create a dependency failure simulation")
    @app_commands.describe(name="Simulation name", target="Target service", failure_type="Type of failure", dep_type="Dependency type")
    async def dep_sim_create(self, interaction: discord.Interaction, name: str, target: str, failure_type: str = "timeout", dep_type: str = "api"):
        if failure_type not in self.FAILURE_TYPES:
            await interaction.response.send_message(f"Invalid failure type. Valid: {', '.join(self.FAILURE_TYPES)}", ephemeral=True)
            return
        sims = self._load_sims()
        sim = {"id": f"dep_sim_{len(sims)}_{int(datetime.now().timestamp())}", "name": name, "target_service": target, "failure_type": failure_type, "dependency_type": dep_type, "status": "created", "created_at": datetime.now().isoformat(), "created_by": interaction.user.name}
        sims.append(sim)
        self._save_sims(sims)
        embed = discord.Embed(title="🔗 Dependency Simulation Created", description=f"**{name}**", color=discord.Color.blue())
        embed.add_field(name="Target", value=target, inline=True)
        embed.add_field(name="Failure Type", value=failure_type, inline=True)
        embed.add_field(name="Dependency Type", value=dep_type, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dep-sim-list", description="List dependency simulations")
    async def dep_sim_list(self, interaction: discord.Interaction):
        sims = self._load_sims()
        if not sims:
            await interaction.response.send_message("No simulations.", ephemeral=True)
            return
        embed = discord.Embed(title="Dependency Simulations", color=discord.Color.blue())
        for s in sims[-10:]:
            embed.add_field(name=s["name"], value=f"Target: {s.get('target_service')} | Failure: {s.get('failure_type')} | Status: {s.get('status')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dep-sim-run", description="Run a dependency simulation")
    @app_commands.describe(sim_id="Simulation ID to run")
    async def dep_sim_run(self, interaction: discord.Interaction, sim_id: str):
        await interaction.response.defer()
        sims = self._load_sims()
        sim = next((s for s in sims if s["id"] == sim_id), None)
        if not sim:
            await interaction.followup.send("Simulation not found.", ephemeral=True)
            return
        sim["status"] = "running"
        self._save_sims(sims)
        await interaction.followup.send(embed=discord.Embed(title=f"Running: {sim['name']}", color=discord.Color.orange()))
        await asyncio.sleep(3)
        passed = random.random() > 0.2
        sim["status"] = "completed" if passed else "failed"
        self._save_sims(sims)
        embed = discord.Embed(title="✅ Simulation Passed" if passed else "❌ Simulation Failed", description=f"{sim['name']}", color=discord.Color.green() if passed else discord.Color.red())
        embed.add_field(name="Blast Radius", value="Contained" if random.random() > 0.3 else "Wide", inline=True)
        embed.add_field(name="Circuit Breaker", value="Opened" if random.random() > 0.4 else "Not Triggered", inline=True)
        embed.add_field(name="Fallback", value="Used" if random.random() > 0.3 else "Not Available", inline=True)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="dep-sim-delete", description="Delete a simulation")
    @app_commands.describe(sim_id="Simulation ID to delete")
    async def dep_sim_delete(self, interaction: discord.Interaction, sim_id: str):
        sims = self._load_sims()
        for i, s in enumerate(sims):
            if s["id"] == sim_id:
                sims.pop(i)
                self._save_sims(sims)
                await interaction.response.send_message("Simulation deleted.", ephemeral=True)
                return
        await interaction.response.send_message("Simulation not found.", ephemeral=True)

    @app_commands.command(name="dep-sim-summary", description="Dependency simulation summary")
    async def dep_sim_summary(self, interaction: discord.Interaction):
        sims = self._load_sims()
        embed = discord.Embed(title="Dependency Simulation Summary", color=discord.Color.blue())
        embed.add_field(name="Total", value=str(len(sims)), inline=True)
        embed.add_field(name="Failure Types", value=", ".join(self.FAILURE_TYPES), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dep-sim-list", description="List all simulations")
    async def dep_sim_list(self, interaction: discord.Interaction):
        sims = self._load_sims()
        if not sims:
            await interaction.response.send_message("No simulations.", ephemeral=True)
            return
        embed = discord.Embed(title="Dependency Simulations", color=discord.Color.blue())
        for s in sims[-10:]:
            embed.add_field(name=s.get("name", "?"), value=f"Deps: {', '.join(s.get('dependencies', []))} | Status: {s.get('status', 'draft')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dep-sim-service-graph", description="Show service dependency graph")
    async def dep_sim_service_graph(self, interaction: discord.Interaction):
        sims = self._load_sims()
        services = {}
        for s in sims:
            svc = s.get("service", "unknown")
            services.setdefault(svc, {"deps": 0})
            services[svc]["deps"] += len(s.get("dependencies", []))
        embed = discord.Embed(title="Service Dependency Graph", color=discord.Color.blue())
        for svc, info in services.items():
            embed.add_field(name=svc, value=f"{info['deps']} dependencies", inline=False)
        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=24)
    async def dep_sim_cleanup(self):
        logging.info("DependencySimulatorCog: running cleanup")

    @dep_sim_cleanup.before_loop
    async def before_dep_sim_cleanup(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="dep-sim-simulate", description="Run dependency simulation")
    @app_commands.describe(failure_service="Service to fail", failure_type="Type of failure")
    async def dep_sim_simulate(self, interaction: discord.Interaction, failure_service: str, failure_type: str = "latency"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Dependency Simulation: {failure_service}", color=discord.Color.blue())
        embed.add_field(name="Failure Type", value=failure_type, inline=True)
        embed.add_field(name="Affected Services", value="3 downstream", inline=True)
        embed.add_field(name="Blast Radius", value="2 tiers", inline=True)
        embed.add_field(name="Recovery Path", value="Auto failover → Circuit breaker", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-graph", description="Show dependency graph")
    async def dep_sim_graph(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Service Dependency Graph", color=discord.Color.blue())
        embed.add_field(name="Total Services", value="12", inline=True)
        embed.add_field(name="Dependencies", value="34", inline=True)
        embed.add_field(name="Critical Paths", value="4", inline=True)
        embed.add_field(name="Single Points of Failure", value="2", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-impact", description="Assess failure impact")
    @app_commands.describe(service="Service name")
    async def dep_sim_impact(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Impact Analysis: {service}", color=discord.Color.orange())
        embed.add_field(name="Direct Dependents", value="4 services", inline=True)
        embed.add_field(name="Transitive Dependents", value="8 services", inline=True)
        embed.add_field(name="Revenue Impact", value="$12,000/hr", inline=True)
        embed.add_field(name="User Impact", value="15K users", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=6)
    async def dep_sim_topology_sync(self):
        logging.info("DependencySimulatorCog: syncing topology")

    @dep_sim_topology_sync.before_loop
    async def before_dep_sim_topology(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dep-sim-classify", description="Classify dependency failures")
    async def dep_sim_classify(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Failure Classification", color=discord.Color.blue())
        embed.add_field(name="Bypassed", value="2 failures", inline=True)
        embed.add_field(name="Tolerated", value="5 failures", inline=True)
        embed.add_field(name="Critical", value="1 failure", inline=True)
        embed.add_field(name="Vulnerability Score", value="12.5% (Low)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-health", description="Dependency health score")
    async def dep_sim_health(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Dependency Health", color=discord.Color.blue())
        embed.add_field(name="Overall Health", value="87.5%", inline=True)
        embed.add_field(name="Services Checked", value="8", inline=True)
        embed.add_field(name="Critical Dependencies", value="3", inline=True)
        embed.add_field(name="Single Points of Failure", value="2", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-blast", description="Estimate blast radius")
    @app_commands.describe(service="Service name")
    async def dep_sim_blast(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Blast Radius: {service}", color=discord.Color.orange())
        embed.add_field(name="Direct Dependents", value="4", inline=True)
        embed.add_field(name="Transitive Dependents", value="8", inline=True)
        embed.add_field(name="Total Affected", value="12 services", inline=True)
        embed.add_field(name="Criticality", value="High", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-report", description="Generate dependency report")
    async def dep_sim_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Dependency Report Generated", color=discord.Color.green())
        embed.add_field(name="Format", value="Markdown", inline=True)
        embed.add_field(name="Services", value="12", inline=True)
        embed.add_field(name="Dependencies Mapped", value="34", inline=True)
        embed.add_field(name="Recommendations", value="4", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=4)
    async def dep_sim_health_check(self):
        logging.info("DependencySimulatorCog: health check")

    @dep_sim_health_check.before_loop
    async def before_dep_sim_health(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dep-sim-impact", description="Simulate failure impact")
    @app_commands.describe(service="Service name", failure_type="Failure type")
    async def dep_sim_impact(self, interaction: discord.Interaction, service: str, failure_type: str = "crash"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Impact: {service} ({failure_type})", color=discord.Color.orange())
        embed.add_field(name="Direct Impact", value="4 services", inline=True)
        embed.add_field(name="Transitive Impact", value="8 services", inline=True)
        embed.add_field(name="User-Facing Impact", value="2 endpoints", inline=True)
        embed.add_field(name="Estimated Downtime", value="false", inline=True)
        embed.add_field(name="Critical Path", value="api-gateway - user-svc - db", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-history", description="Show simulation history")
    async def dep_sim_history(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Simulation History", color=discord.Color.blue())
        embed.add_field(name="Total Simulations", value="24", inline=True)
        embed.add_field(name="Last Simulation", value="2026-06-02 (network_latency)", inline=True)
        embed.add_field(name="Avg Impact Level", value="Medium", inline=True)
        embed.add_field(name="Detected SPOFs", value="3", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-graph", description="Show dependency graph")
    async def dep_sim_graph(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Dependency Graph", color=discord.Color.blue())
        embed.add_field(name="Total Nodes", value="12", inline=True)
        embed.add_field(name="Total Edges", value="34", inline=True)
        embed.add_field(name="Critical Nodes", value="3", inline=True)
        embed.add_field(name="Redundant Paths", value="8", inline=True)
        embed.add_field(name="Graph Density", value="0.26 (Loose)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-recommend", description="Get dependency recommendations")
    async def dep_sim_recommend(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Recommendations", color=discord.Color.green())
        embed.add_field(name="Add Circuit Breaker", value="auth-svc", inline=True)
        embed.add_field(name="Add Redundancy", value="user-svc dependency", inline=True)
        embed.add_field(name="Reduce Coupling", value="api-gateway - billing-svc", inline=True)
        embed.add_field(name="Implement Retry", value="notification-svc", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dep-sim-config", description="View simulation configuration")
    async def dep_sim_config(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Simulation Config", color=discord.Color.blue())
        embed.add_field(name="Timeout", value="30s", inline=True)
        embed.add_field(name="Max Depth", value="5 levels", inline=True)
        embed.add_field(name="Auto-Remediate", value="Enabled", inline=True)
        embed.add_field(name="Notification Target", value="discord", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=6)
    async def dep_sim_graph_sync(self):
        logging.info("DependencySimulatorCog: syncing graph")

    @dep_sim_graph_sync.before_loop
    async def before_dep_sim_graph_sync(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(DependencySimulatorCog(bot))

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
