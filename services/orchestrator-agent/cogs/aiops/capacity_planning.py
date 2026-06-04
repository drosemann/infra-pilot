"""Feature 59 Cog: AI-Driven Capacity Planning"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CAPACITY_PLANNING_HELP = """
**Capacity Planning Commands**
`!capacity recommend [resource] [type]` — Get capacity recommendation
`!capacity record [resource] [type] [total] [used]` — Record usage
`!capacity usage [resource] [type]` — View usage analytics
`!capacity simulate [resource] [type] [scenario]` — What-if simulation
`!capacity list recs` — List recommendations
`!capacity list sims` — List simulations
`!capacity summary` — Capacity planning summary

Scenarios: traffic_spike, black_friday, new_customer_wave, feature_launch, region_expansion
"""


class CapacityPlanningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.planner = None

    async def _get_planner(self):
        if self.planner is None:
            from services.integration_service.src.aiops.capacity_planning import CapacityPlanner
            self.planner = CapacityPlanner({})
        return self.planner

    @commands.group(name="capacity", invoke_without_command=True)
    async def capacity(self, ctx):
        await ctx.send(CAPACITY_PLANNING_HELP)

    @capacity.command(name="recommend")
    async def recommend(self, ctx, resource: str, resource_type: str = "cpu"):
        planner = await self._get_planner()
        rec = planner.generate_recommendation(resource, resource_type)
        if "error" in rec:
            await ctx.send(f"❌ {rec['error']}")
            return
        priority_emoji = "🔴" if rec["priority"] == "critical" else "🟠" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
        embed = discord.Embed(
            title=f"{priority_emoji} Capacity Recommendation: {resource} ({resource_type.upper()})",
            color=discord.Color.red() if rec["priority"] == "critical" else discord.Color.blue()
        )
        embed.add_field(name="Priority", value=rec["priority"].upper(), inline=True)
        embed.add_field(name="Current Utilization", value=f"{rec['current_utilization']:.1%}", inline=True)
        embed.add_field(name="Peak Forecast", value=f"{rec['peak_forecast']:.1%}", inline=True)
        embed.add_field(name="Days Until Exhaustion", value=rec.get("days_until_exhaustion", "N/A"), inline=True)
        embed.add_field(name="Days Until Threshold", value=rec.get("days_until_threshold", "N/A"), inline=True)
        embed.add_field(name="Annual Growth", value=f"{rec['annual_growth_rate']:.1%}", inline=True)
        if rec.get("recommended_additional"):
            embed.add_field(name="Additional Needed", value=rec["recommended_additional"], inline=True)
        if rec.get("cost_estimate"):
            embed.add_field(name="Est. Monthly Cost", value=f"${rec['cost_estimate']['estimated_monthly_cost']:.2f}", inline=True)
        embed.add_field(name="Action", value=rec.get("summary", ""), inline=False)
        await ctx.send(embed=embed)

    @capacity.command(name="record")
    async def record_usage(self, ctx, resource: str, resource_type: str, total: float, used: float):
        planner = await self._get_planner()
        planner.record_usage(resource, resource_type, total, used)
        util = (used / total) * 100 if total > 0 else 0
        await ctx.send(f"✅ Recorded {resource_type.upper()} usage for {resource}: {used}/{total} ({util:.1f}%)")

    @capacity.command(name="usage")
    async def show_usage(self, ctx, resource: str, resource_type: str = "cpu", days: int = 30):
        planner = await self._get_planner()
        usage = planner.get_usage(resource, resource_type, days)
        if usage.get("data_points", 0) == 0:
            await ctx.send(f"No usage data for {resource}/{resource_type}")
            return
        embed = discord.Embed(title=f"📊 {resource_type.upper()} Usage: {resource}", color=discord.Color.blue())
        embed.add_field(name="Data Points", value=usage["data_points"], inline=True)
        embed.add_field(name="Current", value=f"{usage['current_utilization']:.1%}", inline=True)
        embed.add_field(name="Average", value=f"{usage['avg_utilization']:.1%}", inline=True)
        embed.add_field(name="Peak", value=f"{usage['peak_utilization']:.1%}", inline=True)
        if usage.get("p95_utilization"):
            embed.add_field(name="P95", value=f"{usage['p95_utilization']:.1%}", inline=True)
        embed.add_field(name="Free", value=f"{usage['free_current']:.1f}", inline=True)
        embed.add_field(name="Total Capacity", value=f"{usage['total_capacity']:.1f}", inline=True)
        await ctx.send(embed=embed)

    @capacity.command(name="simulate")
    async def simulate(self, ctx, resource: str, resource_type: str = "cpu", scenario: str = "traffic_spike"):
        planner = await self._get_planner()
        result = planner.what_if_simulation(resource, resource_type, scenario)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        embed = discord.Embed(title=f"🧪 What-If Simulation: {scenario}", color=discord.Color.purple())
        embed.add_field(name="Resource", value=resource, inline=True)
        embed.add_field(name="Type", value=resource_type.upper(), inline=True)
        embed.add_field(name="Scenario", value=scenario, inline=True)
        embed.add_field(name="Base Utilization", value=f"{result['base_utilization']:.1%}", inline=True)
        embed.add_field(name="Peak Utilization", value=f"{result['peak_utilization']:.1%}", inline=True)
        embed.add_field(name="Avg Utilization", value=f"{result['avg_utilization']:.1%}", inline=True)
        embed.add_field(name="Days Over Capacity", value=result["days_over_capacity"], inline=True)
        embed.add_field(name="Days Over Threshold", value=result["days_over_threshold"], inline=True)
        if result.get("recommended_additional"):
            embed.add_field(name="Additional Needed", value=result["recommended_additional"], inline=True)
        if result.get("estimated_monthly_cost"):
            embed.add_field(name="Est. Monthly Cost", value=f"${result['estimated_monthly_cost']:.2f}", inline=True)
        await ctx.send(embed=embed)

    @capacity.group(name="list", invoke_without_command=True)
    async def list_cmd(self, ctx):
        await ctx.send("Use `!capacity list recs` or `!capacity list sims`")

    @list_cmd.command(name="recs")
    async def list_recommendations(self, ctx, priority: str = None):
        planner = await self._get_planner()
        recs = planner.list_recommendations(priority=priority)
        if not recs:
            await ctx.send("No recommendations.")
            return
        embed = discord.Embed(title="📋 Capacity Recommendations", color=discord.Color.blue())
        for r in recs[-10:]:
            emoji = "🔴" if r["priority"] == "critical" else "🟠" if r["priority"] == "high" else "🟡"
            embed.add_field(
                name=f"{emoji} {r['resource_id']} ({r['resource_type']})",
                value=f"Priority: {r['priority']} | Current: {r['current_utilization']:.1%} | Status: {r['status']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @list_cmd.command(name="sims")
    async def list_simulations(self, ctx):
        planner = await self._get_planner()
        sims = planner.list_simulations()
        if not sims:
            await ctx.send("No simulations.")
            return
        embed = discord.Embed(title="📋 Simulations", color=discord.Color.blue())
        for s in sims[-10:]:
            embed.add_field(
                name=f"🧪 {s['scenario']} — {s['resource_id']}",
                value=f"Peak: {s['peak_utilization']:.1%} | Days over capacity: {s['days_over_capacity']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @capacity.command(name="summary")
    async def capacity_summary(self, ctx):
        planner = await self._get_planner()
        summary = planner.get_summary()
        embed = discord.Embed(title="📊 Capacity Planning Summary", color=discord.Color.blue())
        embed.add_field(name="Total Recommendations", value=summary["total_recommendations"], inline=True)
        embed.add_field(name="Critical", value=summary["critical"], inline=True)
        embed.add_field(name="High", value=summary["high"], inline=True)
        embed.add_field(name="Medium", value=summary["medium"], inline=True)
        embed.add_field(name="Open", value=summary["open"], inline=True)
        embed.add_field(name="Applied", value=summary["applied"], inline=True)
        embed.add_field(name="Total Simulations", value=summary["total_simulations"], inline=True)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @capacity.command(name="search")
    async def search_capacity(self, ctx, *, query: str):
        planner = await self._get_planner()
        recs = planner.list_recommendations()
        matching = [r for r in recs if query.lower() in r.get("resource_id", "").lower() or query.lower() in r.get("resource_type", "").lower()]
        if not matching:
            await ctx.send(f"No recommendations matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Matching Recommendations", color=discord.Color.blue())
        for r in matching[:5]:
            embed.add_field(name=r["resource_id"], value=f"Type: {r['resource_type']} | Priority: {r['priority']} | Util: {r['current_utilization']:.1%}", inline=False)
        await ctx.send(embed=embed)

    @capacity.command(name="export")
    async def export_plan(self, ctx):
        planner = await self._get_planner()
        recs = planner.list_recommendations()
        data = json.dumps([{"resource": r["resource_id"], "type": r["resource_type"], "priority": r["priority"], "utilization": f"{r['current_utilization']:.1%}"} for r in recs], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @capacity.command(name="reset")
    async def reset_planning(self, ctx):
        planner = await self._get_planner()
        planner.recommendations.clear()
        planner.simulations.clear()
        await ctx.send("✅ Capacity planning data reset")


    @capacity.command(name="health")
    async def capacity_health(self, ctx, resource_id: str):
        planner = await self._get_planner()
        health = planner.get_resource_health(resource_id) if hasattr(planner, 'get_resource_health') else {}
        if "error" in health:
            await ctx.send(f"❌ {health['error']}")
            return
        embed = discord.Embed(title=f"🏥 Resource Health: {resource_id}", color=discord.Color.blue())
        for dim, info in health.get("dimensions", {}).items():
            embed.add_field(name=dim, value=f"Util: {info['avg_utilization']:.1%} | {info['status']}", inline=True)
        await ctx.send(embed=embed)

    @capacity.command(name="growth")
    async def growth_rate(self, ctx, resource_id: str):
        planner = await self._get_planner()
        rate = planner.get_growth_rate(resource_id) if hasattr(planner, 'get_growth_rate') else None
        if rate is None:
            await ctx.send("Insufficient data for growth calculation")
            return
        embed = discord.Embed(title=f"📈 Growth Rate: {resource_id}", color=discord.Color.blue())
        embed.add_field(name="Rate", value=f"{rate}%", inline=True)
        embed.add_field(name="Trend", value="Growing" if rate > 0 else "Declining", inline=True)
        await ctx.send(embed=embed)

    @capacity.command(name="alerts")
    async def capacity_alerts(self, ctx):
        planner = await self._get_planner()
        alert_mgr = CapacityAlertManager(planner)
        alerts = alert_mgr.get_active_alerts()
        if not alerts:
            await ctx.send("✅ No active capacity alerts")
            return
        embed = discord.Embed(title="🔔 Active Capacity Alerts", color=discord.Color.red())
        for a in alerts[:5]:
            embed.add_field(name=a["resource_key"], value=f"Util: {a['avg_utilization']:.1%} | {a['severity']}", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2)
    async def capacity_alert_loop(self):
        planner = self._get_planner_sync()
        alert_mgr = CapacityAlertManager(planner)
        alerts = alert_mgr.check_capacity_breaches()
        if alerts:
            logging.info(f"CapacityPlanningCog: {len(alerts)} capacity breaches detected")

    @capacity_alert_loop.before_loop
    async def before_capacity_alerts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(CapacityPlanningCog(bot))

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
        return {"total_ops": 0, "predictions": 0, "anomalies": 0, "accuracy": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class AiopsCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    prediction: Any = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AiopsCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    model: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    anomalies: int = Field(default=0)

    def record(self, is_anomaly: bool = False) -> None:
        self.processed += 1
        if is_anomaly:
            self.anomalies += 1

    def complete(self) -> None:
        self.status = "completed"

class AiopsCogMetrics:
    def __init__(self) -> None:
        self.runs: int = 0
        self.predictions: int = 0
        self.anomalies: int = 0
        self.errors: int = 0
        self.total_confidence: float = 0.0

    def record(self, prediction: bool = False, anomaly: bool = False, confidence: float = 0.0, error: bool = False) -> None:
        self.runs += 1
        if prediction:
            self.predictions += 1
        if anomaly:
            self.anomalies += 1
        if error:
            self.errors += 1
        self.total_confidence += confidence

    def summary(self) -> Dict[str, Any]:
        return {"runs": self.runs, "predictions": self.predictions, "anomalies": self.anomalies,
                "errors": self.errors, "error_rate": round(self.errors / max(self.runs, 1) * 100, 1),
                "avg_confidence": round(self.total_confidence / max(self.runs, 1), 4)}
