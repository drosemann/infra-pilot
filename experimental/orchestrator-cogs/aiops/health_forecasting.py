"""Feature 56 Cog: Service Health Forecasting"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

HEALTH_FORECASTING_HELP = """
**Service Health Forecasting Commands**
`!health register [service_id] [name]` — Register a service
`!health snapshot [service_id] [dimensions:json]` — Record health snapshot
`!health forecast [service_id]` — Forecast future health
`!health status [service_id]` — Current service health
`!health list` — List all registered services
`!health dashboard` — Health summary dashboard
"""


class HealthForecastingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.forecaster = None

    async def _get_forecaster(self):
        if self.forecaster is None:
            from services.integration_service.src.aiops.health_forecasting import ServiceHealthForecaster
            self.forecaster = ServiceHealthForecaster({})
        return self.forecaster

    @commands.group(name="health", invoke_without_command=True)
    async def health(self, ctx):
        await ctx.send(HEALTH_FORECASTING_HELP)

    @health.command(name="register")
    async def register_service(self, ctx, service_id: str, name: str):
        forecaster = await self._get_forecaster()
        service = forecaster.register_service(service_id, name)
        embed = discord.Embed(title="✅ Service Registered", color=discord.Color.green())
        embed.add_field(name="Service ID", value=service_id, inline=True)
        embed.add_field(name="Name", value=name, inline=True)
        await ctx.send(embed=embed)

    @health.command(name="snapshot")
    async def record_snapshot(self, ctx, service_id: str, *, dimensions_json: str):
        forecaster = await self._get_forecaster()
        try:
            dimensions = json.loads(dimensions_json)
        except json.JSONDecodeError:
            await ctx.send("❌ Invalid JSON for dimensions")
            return
        result = forecaster.record_snapshot(service_id, dimensions)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        health_emoji = "🟢" if result.get("overall_score", 1) >= 0.7 else "🟡" if result.get("overall_score", 1) >= 0.4 else "🔴"
        await ctx.send(f"{health_emoji} Snapshot recorded for **{service_id}** — Score: {result['overall_score']:.2%}")

    @health.command(name="forecast")
    async def forecast_health(self, ctx, service_id: str, hours: int = 24):
        forecaster = await self._get_forecaster()
        result = forecaster.forecast(service_id, hours)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        embed = discord.Embed(title=f"🔮 Health Forecast: {result['service_name']}", color=discord.Color.blue())
        embed.add_field(name="Current Score", value=f"{result['current_score']:.1%}", inline=True)
        embed.add_field(name="Current Health", value=result["current_health"], inline=True)
        embed.add_field(name="Forecast Trend", value=result["trend"], inline=True)
        embed.add_field(name="Final Score ({hours}h)", value=f"{result['final_score']:.1%}", inline=True)
        embed.add_field(name="Final Health", value=result["final_health"], inline=True)
        embed.add_field(name="Slope", value=f"{result['slope']:.4f}/hr", inline=True)
        if result.get("probability_degradation"):
            embed.add_field(name="Degradation Risk", value=f"{result['probability_degradation']:.1%}", inline=True)
        if result.get("time_to_degradation_hours"):
            embed.add_field(name="Time to Degradation", value=f"~{result['time_to_degradation_hours']}h", inline=True)
        if result.get("recommendations"):
            recs = "\n".join(f"• {r}" for r in result["recommendations"][:3])
            embed.add_field(name="Recommendations", value=recs, inline=False)
        await ctx.send(embed=embed)

    @health.command(name="status")
    async def health_status(self, ctx, service_id: str):
        forecaster = await self._get_forecaster()
        service = forecaster.get_service(service_id)
        if not service:
            await ctx.send(f"❌ Service {service_id} not found")
            return
        health_emoji = "🟢" if service["current_health"] == "healthy" else "🟡" if service["current_health"] == "degraded" else "🔴"
        embed = discord.Embed(title=f"{health_emoji} {service['name']} Health", color=discord.Color.blue())
        embed.add_field(name="Status", value=service["current_health"], inline=True)
        embed.add_field(name="Score", value=f"{service['current_score']:.1%}", inline=True)
        embed.add_field(name="Trend", value=service["trend"], inline=True)
        if service.get("dependencies"):
            embed.add_field(name="Dependencies", value=", ".join(service["dependencies"]), inline=False)
        await ctx.send(embed=embed)

    @health.command(name="list")
    async def list_services(self, ctx):
        forecaster = await self._get_forecaster()
        services = forecaster.list_services()
        if not services:
            await ctx.send("No registered services.")
            return
        embed = discord.Embed(title="📋 Registered Services", color=discord.Color.blue())
        for s in services:
            emoji = "🟢" if s["current_health"] == "healthy" else "🟡" if s["current_health"] == "degraded" else "🔴"
            embed.add_field(
                name=f"{emoji} {s['name']}",
                value=f"Score: {s['current_score']:.1%} | Trend: {s['trend']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @health.command(name="dashboard")
    async def health_dashboard(self, ctx):
        forecaster = await self._get_forecaster()
        dashboard = forecaster.get_dashboard()
        embed = discord.Embed(title="📊 Health Dashboard", color=discord.Color.blue())
        embed.add_field(name="Total Services", value=dashboard["total_services"], inline=True)
        embed.add_field(name="Healthy", value=dashboard["healthy"], inline=True)
        embed.add_field(name="Degraded", value=dashboard["degraded"], inline=True)
        embed.add_field(name="Critical", value=dashboard["critical"], inline=True)
        embed.add_field(name="Improving", value=dashboard["improving"], inline=True)
        embed.add_field(name="Degrading", value=dashboard["degrading"], inline=True)
        embed.add_field(name="Avg Health Score", value=f"{dashboard['average_health_score']:.1%}", inline=True)
        if dashboard["at_risk_services"]:
            at_risk = "\n".join(f"• {s['name']} ({s['health']})" for s in dashboard["at_risk_services"][:5])
            embed.add_field(name="At-Risk Services", value=at_risk, inline=False)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @health.command(name="search")
    async def search_health(self, ctx, *, query: str):
        forecaster = await self._get_forecaster()
        services = forecaster.list_services()
        matching = [s for s in services if query.lower() in s.get("name", "").lower() or query.lower() in s.get("service_id", "").lower()]
        if not matching:
            await ctx.send(f"No services matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Services matching '{query}'", color=discord.Color.blue())
        for s in matching[:5]:
            emoji = "🟢" if s["current_health"] == "healthy" else "🟡"
            embed.add_field(name=f"{emoji} {s['name']}", value=f"Score: {s['current_score']:.1%} | Trend: {s['trend']}", inline=False)
        await ctx.send(embed=embed)

    @health.command(name="export")
    async def export_health(self, ctx):
        forecaster = await self._get_forecaster()
        services = forecaster.list_services()
        data = json.dumps([{"service_id": s["service_id"], "name": s["name"], "health": s["current_health"], "score": s["current_score"]} for s in services], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @health.command(name="reset")
    async def reset_health(self, ctx):
        forecaster = await self._get_forecaster()
        forecaster.services.clear()
        await ctx.send("✅ Health forecasting data reset")


    @health_f.command(name="alerts")
    async def health_alerts(self, ctx, days: int = 3):
        engine = await self._get_engine()
        alert_mgr = HealthAlertManager(engine)
        alerts = alert_mgr.get_active_alerts(days)
        if not alerts:
            await ctx.send(f"✅ No health alerts in the last {days}d")
            return
        embed = discord.Embed(title=f"🔔 Health Alerts ({days}d)", color=discord.Color.red())
        for a in alerts[:5]:
            embed.add_field(name=a.get("service", "?"), value=f"Severity: {a.get('severity', '?')} | Predicted: {a.get('predicted_health', 0):.2f}", inline=False)
        await ctx.send(embed=embed)

    @health_f.command(name="errors")
    async def forecast_errors(self, ctx, days: int = 7):
        engine = await self._get_engine()
        errors = engine.get_forecast_errors(days) if hasattr(engine, 'get_forecast_errors') else {}
        if not errors:
            await ctx.send("No forecast error data")
            return
        embed = discord.Embed(title=f"📊 Forecast Errors ({days}d)", color=discord.Color.blue())
        embed.add_field(name="MAE", value=f'{errors.get("mae", 0):.4f}', inline=True)
        embed.add_field(name="RMSE", value=f'{errors.get("rmse", 0):.4f}', inline=True)
        embed.add_field(name="MAPE", value=f'{errors.get("mape", 0):.2f}%', inline=True)
        await ctx.send(embed=embed)

    @health_f.command(name="timeline")
    async def health_timeline(self, ctx, days: int = 14):
        engine = await self._get_engine()
        timeline = engine.get_health_timeline(days) if hasattr(engine, 'get_health_timeline') else []
        if not timeline:
            await ctx.send("No health timeline data")
            return
        embed = discord.Embed(title=f"📅 Health Timeline ({days}d)", color=discord.Color.blue())
        for t in timeline[-10:]:
            embed.add_field(name=t.get("date", "?"), value=f"Health: {t.get('avg_health', 0):.2f} ({t.get('samples', 0)} samples)", inline=True)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2)
    async def health_alert_scan(self):
        engine = self._get_engine_sync()
        alert_mgr = HealthAlertManager(engine)
        alerts = alert_mgr.check_deteriorating_services()
        if alerts:
            logging.info(f"HealthForecastingCog: {len(alerts)} deteriorating services detected")

    @health_alert_scan.before_loop
    async def before_health_alerts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(HealthForecastingCog(bot))

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
