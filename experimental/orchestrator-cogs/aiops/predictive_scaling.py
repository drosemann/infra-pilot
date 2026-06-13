"""Feature 55 Cog: Predictive Auto-Scaling"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PREDICTIVE_SCALING_HELP = """
**Predictive Auto-Scaling Commands**
`!scale predict [resource] [metric]` — Get workload prediction
`!scale record [resource] [metric] [value]` — Record a metric
`!scale policy [resource] [policy]` — Set scaling policy (aggressive/moderate/conservative)
`!scale actions [resource]` — View scaling actions
`!scale metrics [resource] [metric]` — View metric analytics
`!scale summary` — View scaling summary
"""


class PredictiveScalingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = None

    async def _get_engine(self):
        if self.engine is None:
            from services.integration_service.src.aiops.predictive_scaling import PredictiveScalingEngine
            self.engine = PredictiveScalingEngine({})
        return self.engine

    @commands.group(name="scale", invoke_without_command=True)
    async def scale(self, ctx):
        await ctx.send(PREDICTIVE_SCALING_HELP)

    @scale.command(name="predict")
    async def predict(self, ctx, resource: str, metric: str = "cpu", method: str = "ensemble"):
        engine = await self._get_engine()
        result = engine.predict(resource, metric, method)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        direction_emoji = "📈" if result["direction"] == "scale_up" else "📉" if result["direction"] == "scale_down" else "➡️"
        embed = discord.Embed(title=f"{direction_emoji} Prediction: {resource}", color=discord.Color.blue())
        embed.add_field(name="Metric", value=metric, inline=True)
        embed.add_field(name="Current", value=f"{result['current_value']:.1f}%", inline=True)
        embed.add_field(name="Peak Forecast", value=f"{result['peak_forecast']:.1f}%", inline=True)
        embed.add_field(name="Direction", value=result["direction"], inline=True)
        embed.add_field(name="Confidence", value=f"{result['confidence']:.1%}", inline=True)
        embed.add_field(name="Method", value=method, inline=True)
        forecast_str = ", ".join(f"{v:.0f}%" for v in result["forecast"][:6])
        embed.add_field(name="Forecast (next steps)", value=forecast_str, inline=False)
        if result.get("recommended_action"):
            embed.add_field(name="Recommendation", value=result["recommended_action"]["message"], inline=False)
        await ctx.send(embed=embed)

    @scale.command(name="record")
    async def record_metric(self, ctx, resource: str, metric: str, value: float):
        engine = await self._get_engine()
        engine.record_metric(resource, metric, value)
        await ctx.send(f"✅ Recorded {metric}={value} for {resource}")

    @scale.command(name="policy")
    async def set_policy(self, ctx, resource: str, policy: str):
        engine = await self._get_engine()
        if engine.set_scaling_policy(resource, policy):
            await ctx.send(f"✅ Scaling policy for {resource} set to **{policy}**")
        else:
            await ctx.send(f"❌ Invalid policy. Use: aggressive, moderate, or conservative")

    @scale.command(name="actions")
    async def list_actions(self, ctx, resource: str = None, limit: int = 10):
        engine = await self._get_engine()
        actions = engine.get_actions(resource, limit)
        if not actions:
            await ctx.send("No scaling actions recorded.")
            return
        embed = discord.Embed(title="📋 Scaling Actions", color=discord.Color.blue())
        for a in actions[-limit:]:
            embed.add_field(
                name=f"{a['direction']} — {a['resource_id']}",
                value=f"Status: {a['status']} | By: {a.get('approved_by', 'system')}",
                inline=False
            )
        await ctx.send(embed=embed)

    @scale.command(name="metrics")
    async def get_metrics(self, ctx, resource: str, metric: str = "cpu", minutes: int = 60):
        engine = await self._get_engine()
        metrics = engine.get_metrics(resource, metric, minutes)
        if metrics.get("data_points", 0) == 0:
            await ctx.send(f"No metrics data for {resource}/{metric}")
            return
        embed = discord.Embed(title=f"📊 {metric.upper()} Metrics: {resource}", color=discord.Color.blue())
        embed.add_field(name="Current", value=f"{metrics['current']:.1f}%", inline=True)
        embed.add_field(name="Avg", value=f"{metrics['avg']:.1f}%", inline=True)
        embed.add_field(name="Max", value=f"{metrics['max']:.1f}%", inline=True)
        embed.add_field(name="Min", value=f"{metrics['min']:.1f}%", inline=True)
        embed.add_field(name="Trend", value=metrics.get("recent_trend", "stable"), inline=True)
        embed.add_field(name="Data Points", value=metrics["data_points"], inline=True)
        await ctx.send(embed=embed)

    @scale.command(name="summary")
    async def scaling_summary(self, ctx):
        engine = await self._get_engine()
        summary = engine.get_summary()
        embed = discord.Embed(title="📈 Scaling Summary", color=discord.Color.blue())
        embed.add_field(name="Metrics Streams", value=summary["total_metrics_streams"], inline=True)
        embed.add_field(name="Predictions", value=summary["total_predictions"], inline=True)
        embed.add_field(name="Actions Taken", value=summary["total_actions"], inline=True)
        if summary.get("active_policies"):
            policies = "\n".join(f"{k}: {v}" for k, v in summary["active_policies"].items())
            embed.add_field(name="Active Policies", value=policies or "None", inline=False)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @scale.command(name="search")
    async def search_scaling(self, ctx, *, query: str):
        engine = await self._get_engine()
        actions = engine.get_actions(limit=100)
        matching = [a for a in actions if query.lower() in a.get("resource_id", "").lower()]
        if not matching:
            await ctx.send(f"No scaling actions matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Scaling actions for '{query}'", color=discord.Color.blue())
        for a in matching[-5:]:
            embed.add_field(name=f"{a['direction']} — {a['resource_id']}", value=f"Status: {a['status']} | By: {a.get('approved_by', 'system')}", inline=False)
        await ctx.send(embed=embed)

    @scale.command(name="export")
    async def export_scaling(self, ctx):
        engine = await self._get_engine()
        actions = engine.get_actions(limit=100)
        data = json.dumps([{"resource": a["resource_id"], "direction": a["direction"], "status": a["status"]} for a in actions], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @scale.command(name="reset")
    async def reset_scaling(self, ctx):
        engine = await self._get_engine()
        engine.actions.clear()
        engine.predictions.clear()
        await ctx.send("✅ Scaling data reset")


    @scale.command(name="forecast", aliases=["predict"])
    async def forecast_scaling(self, ctx, resource_id: str, metric: str = "cpu"):
        engine = await self._get_engine()
        pred = engine.predict(resource_id, metric)
        if "error" in pred:
            await ctx.send(f"❌ {pred['error']}")
            return
        embed = discord.Embed(title=f"📈 Forecast for {resource_id} ({metric})", color=discord.Color.blue())
        embed.add_field(name="Direction", value=pred.get("direction", "N/A"), inline=True)
        embed.add_field(name="Confidence", value=f"{pred.get('confidence', 0):.0%}", inline=True)
        embed.add_field(name="Peak Forecast", value=str(pred.get("peak_forecast", "N/A")), inline=True)
        embed.add_field(name="Avg Forecast", value=str(pred.get("avg_forecast", "N/A")), inline=True)
        await ctx.send(embed=embed)

    @scale.command(name="alerts")
    async def scaling_alerts(self, ctx):
        engine = await self._get_engine()
        alert_mgr = ScalingAlertManager(engine)
        alerts = alert_mgr.get_active_alerts()
        if not alerts:
            await ctx.send("✅ No active scaling alerts")
            return
        embed = discord.Embed(title="🔔 Active Scaling Alerts", color=discord.Color.red())
        for a in alerts[:5]:
            embed.add_field(name=f"{a['resource_id']} - {a['severity']}", value=f"Deviation: {a.get('deviation', 0):.1f}", inline=False)
        await ctx.send(embed=embed)

    @scale.command(name="top")
    async def top_scaling(self, ctx, limit: int = 5):
        engine = await self._get_engine()
        top = engine.get_top_scaling_resources(limit)
        if not top:
            await ctx.send("No scaling data available")
            return
        embed = discord.Embed(title=f"🏆 Top {limit} Scaling Resources", color=discord.Color.gold())
        for r in top:
            embed.add_field(name=r["resource_id"], value=f"Actions: {r['scaling_actions']} | Confidence: {r['avg_confidence']:.0%}", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def scaling_alert_check(self):
        engine = self._get_engine_sync()
        alert_mgr = ScalingAlertManager(engine)
        alerts = alert_mgr.check_anomalies("all", "cpu")
        if alerts:
            logging.info(f"PredictiveScalingCog: {len(alerts)} anomalies detected")

    @scaling_alert_check.before_loop
    async def before_scaling_alert_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(PredictiveScalingCog(bot))

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
