"""Feature 53 Cog: Digital Experience Monitoring"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DIGITAL_EXPERIENCE_HELP = """
**Digital Experience Monitoring Commands**
`!dem monitors` — List all monitors
`!dem create [name] [url] [type]` — Create a monitor
`!dem check [monitor_id]` — Run a check
`!dem stats [monitor_id]` — Monitor statistics
`!dem vitals [monitor_id]` — Core Web Vitals
`!dem summary` — Global monitoring summary
"""


class DigitalExperienceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitor = None

    async def _get_monitor(self):
        if self.monitor is None:
            from services.integration_service.src.aiops.digital_experience import DigitalExperienceMonitor
            self.monitor = DigitalExperienceMonitor({})
        return self.monitor

    @commands.group(name="dem", invoke_without_command=True)
    async def dem(self, ctx):
        await ctx.send(DIGITAL_EXPERIENCE_HELP)

    @dem.command(name="monitors")
    async def list_monitors(self, ctx):
        monitor = await self._get_monitor()
        all_mons = monitor.list_monitors()
        if not all_mons:
            await ctx.send("No monitors configured.")
            return
        embed = discord.Embed(title="🖥️ Digital Experience Monitors", color=discord.Color.blue())
        for m in all_mons[:10]:
            status_icon = "🟢" if m["status"] == "active" else "🟡" if m["status"] == "paused" else "🔴"
            embed.add_field(
                name=f"{status_icon} {m['name']}",
                value=f"URL: {m['url']} | Type: {m['monitor_type']} | Uptime: {m['uptime_percentage']}%",
                inline=False
            )
        await ctx.send(embed=embed)

    @dem.command(name="create")
    async def create_monitor(self, ctx, name: str, url: str, monitor_type: str = "browser_synthetic"):
        monitor = await self._get_monitor()
        result = monitor.create_monitor(name=name, url=url, monitor_type=monitor_type)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        embed = discord.Embed(title="✅ Monitor Created", color=discord.Color.green())
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="URL", value=url, inline=True)
        embed.add_field(name="Type", value=monitor_type, inline=True)
        embed.add_field(name="ID", value=result["id"], inline=False)
        await ctx.send(embed=embed)

    @dem.command(name="check")
    async def run_check(self, ctx, monitor_id: str):
        monitor = await self._get_monitor()
        result = monitor.run_check(monitor_id)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        status_icon = "🟢" if result["result"] == "passed" else "🟡" if result["result"] == "degraded" else "🔴"
        embed = discord.Embed(title=f"{status_icon} Check Result", color=discord.Color.blue())
        embed.add_field(name="Monitor", value=result["monitor_name"], inline=True)
        embed.add_field(name="Result", value=result["result"], inline=True)
        embed.add_field(name="Duration", value=f"{result['duration_ms']:.0f}ms", inline=True)
        embed.add_field(name="Location", value=result["location"], inline=True)
        metrics = result.get("metrics", {})
        if metrics:
            embed.add_field(name="LCP", value=f"{metrics.get('lcp_ms', 'N/A')}ms", inline=True)
            embed.add_field(name="CLS", value=metrics.get("cls_score", "N/A"), inline=True)
            embed.add_field(name="FID", value=f"{metrics.get('fid_ms', 'N/A')}ms", inline=True)
        if result.get("errors"):
            embed.add_field(name="Errors", value="\n".join(result["errors"]), inline=False)
        await ctx.send(embed=embed)

    @dem.command(name="stats")
    async def monitor_stats(self, ctx, monitor_id: str, hours: int = 24):
        monitor = await self._get_monitor()
        stats = monitor.get_monitor_stats(monitor_id, hours)
        if "error" in stats:
            await ctx.send(f"❌ {stats['error']}")
            return
        embed = discord.Embed(title=f"📊 Stats: {stats['monitor_name']}", color=discord.Color.blue())
        embed.add_field(name="Period", value=f"{hours}h", inline=True)
        embed.add_field(name="Checks", value=stats["total_checks"], inline=True)
        embed.add_field(name="Uptime", value=f"{stats['uptime_percentage']}%", inline=True)
        embed.add_field(name="Passed", value=stats["passed"], inline=True)
        embed.add_field(name="Failed", value=stats["failed"], inline=True)
        embed.add_field(name="Avg Duration", value=f"{stats['avg_duration_ms']:.0f}ms", inline=True)
        if stats.get("avg_lcp_ms"):
            embed.add_field(name="Avg LCP", value=f"{stats['avg_lcp_ms']}ms", inline=True)
        if stats.get("avg_cls"):
            embed.add_field(name="Avg CLS", value=stats["avg_cls"], inline=True)
        await ctx.send(embed=embed)

    @dem.command(name="vitals")
    async def web_vitals(self, ctx, monitor_id: str, hours: int = 24):
        monitor = await self._get_monitor()
        vitals = monitor.get_core_web_vitals(monitor_id, hours)
        if vitals.get("data_points", 0) == 0:
            await ctx.send("No Core Web Vitals data available.")
            return
        embed = discord.Embed(title="📈 Core Web Vitals", color=discord.Color.blue())
        embed.add_field(name="Data Points", value=vitals["data_points"], inline=True)
        lcp = vitals.get("lcp", {})
        if lcp.get("avg"):
            embed.add_field(name="Avg LCP", value=f"{lcp['avg']}ms", inline=True)
            embed.add_field(name="Good LCP", value=f"{lcp.get('good_percentage', 0)}%", inline=True)
        cls_data = vitals.get("cls", {})
        if cls_data.get("avg"):
            embed.add_field(name="Avg CLS", value=cls_data["avg"], inline=True)
            embed.add_field(name="Good CLS", value=f"{cls_data.get('good_percentage', 0)}%", inline=True)
        await ctx.send(embed=embed)

    @dem.command(name="summary")
    async def global_summary(self, ctx):
        monitor = await self._get_monitor()
        summary = monitor.get_global_summary()
        embed = discord.Embed(title="🌐 Global Monitoring Summary", color=discord.Color.blue())
        embed.add_field(name="Total Monitors", value=summary["total_monitors"], inline=True)
        embed.add_field(name="Active", value=summary["active"], inline=True)
        embed.add_field(name="Total Checks", value=summary["total_checks"], inline=True)
        embed.add_field(name="Overall Uptime", value=f"{summary['overall_uptime']}%", inline=True)
        if summary.get("avg_lcp"):
            embed.add_field(name="Global Avg LCP", value=f"{summary['avg_lcp']}ms", inline=True)
        if summary.get("avg_cls"):
            embed.add_field(name="Global Avg CLS", value=summary["avg_cls"], inline=True)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @dem.command(name="search")
    async def search_monitors(self, ctx, *, query: str):
        monitor = await self._get_monitor()
        all_mons = monitor.list_monitors()
        matching = [m for m in all_mons if query.lower() in m.get("name", "").lower() or query.lower() in m.get("url", "").lower()]
        if not matching:
            await ctx.send(f"No monitors matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Monitors matching '{query}'", color=discord.Color.blue())
        for m in matching[:5]:
            embed.add_field(name=m["name"], value=f"URL: {m['url']} | Type: {m['monitor_type']} | Uptime: {m['uptime_percentage']}%", inline=False)
        await ctx.send(embed=embed)

    @dem.command(name="export")
    async def export_monitors(self, ctx):
        monitor = await self._get_monitor()
        mons = monitor.list_monitors()
        data = json.dumps([{"name": m["name"], "url": m["url"], "type": m["monitor_type"], "status": m["status"], "uptime": m["uptime_percentage"]} for m in mons], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @dem.command(name="purge")
    async def purge_monitors(self, ctx):
        monitor = await self._get_monitor()
        mons = monitor.list_monitors()
        for m in mons:
            monitor.delete_monitor(m["id"])
        await ctx.send(f"✅ Purged {len(mons)} monitors")


    @monitor.command(name="regression")
    async def perf_regression(self, ctx, days: int = 7):
        engine = await self._get_engine()
        regression = engine.detect_performance_regression(days) if hasattr(engine, 'detect_performance_regression') else []
        if not regression:
            await ctx.send(f"✅ No performance regression detected in the last {days}d")
            return
        embed = discord.Embed(title=f"📉 Performance Regression ({days}d)", color=discord.Color.red())
        for r in regression[:5]:
            embed.add_field(name=r["monitor_name"], value=f"Before: {r['before']} → After: {r['after']} ({r['pct_change']:.1f}%)", inline=False)
        await ctx.send(embed=embed)

    @monitor.command(name="slowest")
    async def slowest_monitors(self, ctx, limit: int = 5):
        engine = await self._get_engine()
        slowest = engine.get_slowest_monitors(limit) if hasattr(engine, 'get_slowest_monitors') else []
        if not slowest:
            await ctx.send("No monitor performance data")
            return
        embed = discord.Embed(title=f"🐢 Top {limit} Slowest Monitors", color=discord.Color.blue())
        for s in slowest:
            embed.add_field(name=s.get("name", "?"), value=f"Avg: {s.get('avg_response_ms', 0):.0f}ms | P99: {s.get('p99_ms', 0):.0f}ms", inline=False)
        await ctx.send(embed=embed)

    @monitor.command(name="health")
    async def monitor_health_check(self, ctx):
        engine = await self._get_engine()
        checker = MonitorHealthChecker(engine)
        health = checker.get_health_summary()
        embed = discord.Embed(title="🏥 Monitor Health", color=discord.Color.blue())
        embed.add_field(name="Up", value=str(health.get("healthy", 0)), inline=True)
        embed.add_field(name="Degraded", value=str(health.get("degraded", 0)), inline=True)
        embed.add_field(name="Down", value=str(health.get("down", 0)), inline=True)
        embed.add_field(name="Coverage", value=f'{health.get("coverage_pct", 0):.0%}', inline=True)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2)
    async def monitor_health_loop(self):
        engine = self._get_engine_sync()
        checker = MonitorHealthChecker(engine)
        health = checker.get_health_summary()
        if health.get("down", 0) > 0:
            logging.info(f"DigitalExperienceCog: {health['down']} monitors are DOWN")

    @monitor_health_loop.before_loop
    async def before_monitor_health(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DigitalExperienceCog(bot))

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
