"""Feature 54 Cog: Intelligent Alert Correlation"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ALERT_CORRELATION_HELP = """
**Alert Correlation Commands**
`!alerts list [status]` — List alerts
`!alerts ingest [name] [source] [severity] [message]` — Ingest an alert
`!alerts incidents` — List correlated incidents
`!alerts acknowledge [alert_id]` — Acknowledge an alert
`!alerts resolve [alert_id]` — Resolve an alert
`!alerts suppress [name] [duration_mins]` — Add suppression rule
`!alerts stats` — Correlation statistics
"""


class AlertCorrelationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = None

    async def _get_engine(self):
        if self.engine is None:
            from services.integration_service.src.aiops.alert_correlation import AlertCorrelationEngine
            self.engine = AlertCorrelationEngine({})
        return self.engine

    @commands.group(name="alerts", invoke_without_command=True)
    async def alerts(self, ctx):
        await ctx.send(ALERT_CORRELATION_HELP)

    @alerts.command(name="list")
    async def list_alerts(self, ctx, status: str = None, limit: int = 10):
        engine = await self._get_engine()
        all_alerts = engine.list_alerts(status=status, limit=limit)
        if not all_alerts:
            await ctx.send("No alerts found.")
            return
        embed = discord.Embed(title="🔔 Alerts", color=discord.Color.blue())
        for a in all_alerts[-limit:]:
            sev_emoji = "🔴" if a["severity"] == "critical" else "🟡" if a["severity"] == "warning" else "🔵"
            embed.add_field(
                name=f"{sev_emoji} {a['name']} ({a['source']})",
                value=f"Status: {a['status']} | Severity: {a['severity']} | Count: {a.get('count', 1)}",
                inline=False
            )
        await ctx.send(embed=embed)

    @alerts.command(name="ingest")
    async def ingest_alert(self, ctx, name: str, source: str, severity: str, *, message: str):
        engine = await self._get_engine()
        alert = engine.ingest_alert(name, source, severity, message)
        embed = discord.Embed(title="📥 Alert Ingested", color=discord.Color.green())
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Source", value=source, inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Status", value=alert["status"], inline=True)
        embed.add_field(name="ID", value=alert["id"][:8], inline=False)
        await ctx.send(embed=embed)

    @alerts.command(name="incidents")
    async def list_incidents(self, ctx, limit: int = 10):
        engine = await self._get_engine()
        incidents = engine.list_incidents(limit=limit)
        if not incidents:
            await ctx.send("No incidents found.")
            return
        embed = discord.Embed(title="🚨 Correlated Incidents", color=discord.Color.red())
        for i in incidents[-limit:]:
            priority_emoji = "🔥" if i["priority"] in ("p0", "p1") else "⚠️"
            embed.add_field(
                name=f"{priority_emoji} {i['title']}",
                value=f"Priority: {i['priority']} | Alerts: {i['alert_count']} | Status: {i['status']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @alerts.command(name="acknowledge")
    async def acknowledge_alert(self, ctx, alert_id: str):
        engine = await self._get_engine()
        result = engine.acknowledge_alert(alert_id)
        if result:
            await ctx.send(f"✅ Alert `{alert_id[:8]}` acknowledged")
        else:
            await ctx.send(f"❌ Alert `{alert_id[:8]}` not found")

    @alerts.command(name="resolve")
    async def resolve_alert(self, ctx, alert_id: str):
        engine = await self._get_engine()
        result = engine.resolve_alert(alert_id)
        if result:
            await ctx.send(f"✅ Alert `{alert_id[:8]}` resolved")
        else:
            await ctx.send(f"❌ Alert `{alert_id[:8]}` not found")

    @alerts.command(name="suppress")
    async def suppress_alert(self, ctx, name: str, duration_minutes: int = 60):
        engine = await self._get_engine()
        rule = engine.add_suppression_rule(name, match_name=name, duration_minutes=duration_minutes)
        embed = discord.Embed(title="🔇 Suppression Rule Added", color=discord.Color.orange())
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Duration", value=f"{duration_minutes}m", inline=True)
        embed.add_field(name="Rule ID", value=rule["id"][:8], inline=False)
        await ctx.send(embed=embed)

    @alerts.command(name="stats")
    async def correlation_stats(self, ctx):
        engine = await self._get_engine()
        stats = engine.get_statistics()
        embed = discord.Embed(title="📊 Alert Correlation Stats", color=discord.Color.blue())
        embed.add_field(name="Total Alerts", value=stats["total_alerts"], inline=True)
        embed.add_field(name="Firing", value=stats["firing"], inline=True)
        embed.add_field(name="Suppressed", value=stats["suppressed"], inline=True)
        embed.add_field(name="Active Incidents", value=stats["active_incidents"], inline=True)
        embed.add_field(name="Duplicates", value=stats["duplicates_detected"], inline=True)
        embed.add_field(name="Noise Reduction", value=f"{stats['noise_reduction_percentage']}%", inline=True)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @alerts.command(name="search")
    async def search_alerts(self, ctx, *, query: str):
        engine = await self._get_engine()
        all_alerts = engine.list_alerts(limit=100)
        matching = [a for a in all_alerts if query.lower() in a.get("name", "").lower() or query.lower() in a.get("source", "").lower()]
        if not matching:
            await ctx.send(f"No alerts matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Alerts matching '{query}'", color=discord.Color.blue())
        for a in matching[:5]:
            embed.add_field(name=f"{a['name']} ({a['source']})", value=f"Severity: {a['severity']} | Status: {a['status']}", inline=False)
        await ctx.send(embed=embed)

    @alerts.command(name="export")
    async def export_alerts(self, ctx, status: str = None):
        engine = await self._get_engine()
        alerts = engine.list_alerts(status=status, limit=100)
        data = json.dumps([{"id": a["id"][:8], "name": a["name"], "source": a["source"], "severity": a["severity"], "status": a["status"]} for a in alerts], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @alerts.command(name="purge")
    async def purge_alerts(self, ctx, status: str = "resolved"):
        engine = await self._get_engine()
        count = engine.purge_alerts(status)
        await ctx.send(f"✅ Purged {count} alerts with status `{status}`")

    @alerts.command(name="timeline")
    async def alert_timeline(self, ctx, limit: int = 10):
        engine = await self._get_engine()
        incidents = engine.list_incidents(limit=limit)
        if not incidents:
            await ctx.send("No incidents to show")
            return
        embed = discord.Embed(title="📅 Incident Timeline", color=discord.Color.blue())
        for i in incidents[-limit:]:
            embed.add_field(name=i["title"], value=f"Priority: {i['priority']} | Alerts: {i['alert_count']} | Status: {i['status']}", inline=False)
        await ctx.send(embed=embed)


    @alerts.command(name="stats")
    async def alert_stats(self, ctx):
        engine = await self._get_engine()
        stats = engine.get_correlation_stats() if hasattr(engine, 'get_correlation_stats') else {}
        if not stats:
            await ctx.send("No correlation stats available")
            return
        embed = discord.Embed(title="📊 Alert Correlation Stats", color=discord.Color.blue())
        embed.add_field(name="Total Alerts", value=stats.get("total_alerts", 0), inline=True)
        embed.add_field(name="Correlated", value=stats.get("correlated_alerts", 0), inline=True)
        embed.add_field(name="Rate", value=f"{stats.get('correlation_rate', 0)}%", inline=True)
        embed.add_field(name="Clusters", value=stats.get("total_clusters", 0), inline=True)
        await ctx.send(embed=embed)

    @alerts.command(name="sources")
    async def alert_sources(self, ctx):
        engine = await self._get_engine()
        sources = engine.get_alert_source_breakdown() if hasattr(engine, 'get_alert_source_breakdown') else {}
        if not sources:
            await ctx.send("No source data available")
            return
        embed = discord.Embed(title="📡 Alert Sources", color=discord.Color.blue())
        for src, count in sources.get("by_source", {}).items():
            embed.add_field(name=src, value=str(count), inline=True)
        await ctx.send(embed=embed)

    @alerts.command(name="suppress")
    async def suppress_dupes(self, ctx, window_minutes: int = 2):
        engine = await self._get_engine()
        result = engine.suppress_duplicates(window_minutes) if hasattr(engine, 'suppress_duplicates') else {"duplicate_groups_found": 0, "alerts_suppressed": 0}
        await ctx.send(f"✅ Found {result['duplicate_groups_found']} groups, suppressed {result['alerts_suppressed']} alerts")

    @tasks.loop(minutes=30)
    async def alert_suppression_loop(self):
        engine = self._get_engine_sync()
        if hasattr(engine, 'suppress_duplicates'):
            result = engine.suppress_duplicates(2)
            if result["alerts_suppressed"] > 0:
                logging.info(f"AlertCorrelationCog: suppressed {result['alerts_suppressed']} duplicates")

    @alert_suppression_loop.before_loop
    async def before_alert_suppression(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AlertCorrelationCog(bot))

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
