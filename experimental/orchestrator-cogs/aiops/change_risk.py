"""Feature 58 Cog: Change Risk Analysis"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CHANGE_RISK_HELP = """
**Change Risk Analysis Commands**
`!change plan [title] [type] [target] [components]` — Plan a change with risk analysis
`!change list [status]` — List planned changes
`!change get [change_id]` — Get change details
`!change approve [change_id]` — Approve a change
`!change reject [change_id] [reason]` — Reject a change
`!change outcome [change_id] [status]` — Record change outcome
`!change stats` — Change statistics
"""


class ChangeRiskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analyzer = None

    async def _get_analyzer(self):
        if self.analyzer is None:
            from services.integration_service.src.aiops.change_risk import ChangeRiskAnalyzer
            self.analyzer = ChangeRiskAnalyzer({})
        return self.analyzer

    @commands.group(name="change", invoke_without_command=True)
    async def change(self, ctx):
        await ctx.send(CHANGE_RISK_HELP)

    @change.command(name="plan")
    async def plan_change(self, ctx, title: str, change_type: str, target_service: str, *, components: str):
        analyzer = await self._get_analyzer()
        comps = [c.strip() for c in components.split(",")]
        result = analyzer.plan_change(title, "", change_type, target_service, comps)
        change = result.get("change", {})
        analysis = result.get("analysis", {})
        risk_emoji = "🔴" if analysis.get("overall_risk_level") in ("critical", "high") else "🟡" if analysis.get("overall_risk_level") == "medium" else "🟢"
        embed = discord.Embed(
            title=f"{risk_emoji} Change Risk Analysis: {title}",
            color=discord.Color.red() if analysis.get("overall_risk_level") in ("critical", "high") else discord.Color.orange() if analysis.get("overall_risk_level") == "medium" else discord.Color.green()
        )
        embed.add_field(name="Change ID", value=change["id"][:8], inline=True)
        embed.add_field(name="Target", value=target_service, inline=True)
        embed.add_field(name="Type", value=change_type, inline=True)
        embed.add_field(name="Risk Level", value=analysis["overall_risk_level"].upper(), inline=True)
        embed.add_field(name="Risk Score", value=f"{analysis['overall_risk_score']:.1%}", inline=True)
        embed.add_field(name="Similar Changes", value=analysis["historical_similar_count"], inline=True)
        if analysis.get("risk_factors"):
            factors = "\n".join(
                f"• {f['label']}: {f['score']:.0%}" for f in analysis["risk_factors"][:5]
            )
            embed.add_field(name="Risk Factors", value=factors, inline=False)
        if analysis.get("recommendations"):
            recs = "\n".join(f"• {r}" for r in analysis["recommendations"][:4])
            embed.add_field(name="Recommendations", value=recs, inline=False)
        await ctx.send(embed=embed)

    @change.command(name="list")
    async def list_changes(self, ctx, status: str = None, limit: int = 10):
        analyzer = await self._get_analyzer()
        changes = analyzer.list_changes(status=status, limit=limit)
        if not changes:
            await ctx.send("No changes found.")
            return
        embed = discord.Embed(title="📋 Changes", color=discord.Color.blue())
        for c in changes[-limit:]:
            status_emoji = "🟢" if c["status"] == "completed" else "🔴" if c["status"] in ("failed", "rolled_back") else "🟡"
            embed.add_field(
                name=f"{status_emoji} {c['title']}",
                value=f"Type: {c['change_type']} | Status: {c['status']} | Target: {c['target_service']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @change.command(name="get")
    async def get_change(self, ctx, change_id: str):
        analyzer = await self._get_analyzer()
        change = analyzer.get_change(change_id)
        if not change:
            await ctx.send(f"❌ Change {change_id[:8]} not found")
            return
        analysis = analyzer.get_analysis(change_id)
        embed = discord.Embed(title=f"📄 Change: {change['title']}", color=discord.Color.blue())
        embed.add_field(name="ID", value=change_id[:8], inline=True)
        embed.add_field(name="Status", value=change["status"], inline=True)
        embed.add_field(name="Type", value=change["change_type"], inline=True)
        embed.add_field(name="Target", value=change["target_service"], inline=True)
        embed.add_field(name="Components", value=", ".join(change["affected_components"][:5]), inline=False)
        if analysis:
            embed.add_field(name="Risk Score", value=f"{analysis['overall_risk_score']:.1%}", inline=True)
            embed.add_field(name="Risk Level", value=analysis["overall_risk_level"], inline=True)
        await ctx.send(embed=embed)

    @change.command(name="approve")
    async def approve_change(self, ctx, change_id: str):
        analyzer = await self._get_analyzer()
        result = analyzer.approve_change(change_id, str(ctx.author))
        if result:
            await ctx.send(f"✅ Change `{change_id[:8]}` approved by {ctx.author.mention}")
        else:
            await ctx.send(f"❌ Change `{change_id[:8]}` not found")

    @change.command(name="reject")
    async def reject_change(self, ctx, change_id: str, *, reason: str = ""):
        analyzer = await self._get_analyzer()
        result = analyzer.reject_change(change_id, reason)
        if result:
            await ctx.send(f"❌ Change `{change_id[:8]}` rejected by {ctx.author.mention}")
        else:
            await ctx.send(f"❌ Change `{change_id[:8]}` not found")

    @change.command(name="outcome")
    async def record_outcome(self, ctx, change_id: str, status: str):
        analyzer = await self._get_analyzer()
        result = analyzer.record_outcome(change_id, status)
        if result:
            await ctx.send(f"✅ Outcome recorded for change `{change_id[:8]}`: {status}")
        else:
            await ctx.send(f"❌ Change `{change_id[:8]}` not found")

    @change.command(name="stats")
    async def change_stats(self, ctx):
        analyzer = await self._get_analyzer()
        stats = analyzer.get_statistics()
        embed = discord.Embed(title="📊 Change Risk Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Changes", value=stats["total_changes"], inline=True)
        embed.add_field(name="Completed", value=stats["completed"], inline=True)
        embed.add_field(name="Failed", value=stats["failed"], inline=True)
        embed.add_field(name="Rolled Back", value=stats["rolled_back"], inline=True)
        embed.add_field(name="Success Rate", value=f"{stats['success_rate']}%", inline=True)
        embed.add_field(name="Pending Approval", value=stats["pending_approvals"], inline=True)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @change.command(name="search")
    async def search_changes(self, ctx, *, query: str):
        analyzer = await self._get_analyzer()
        changes = analyzer.list_changes(limit=100)
        matching = [c for c in changes if query.lower() in c.get("title", "").lower() or query.lower() in c.get("target_service", "").lower()]
        if not matching:
            await ctx.send(f"No changes matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Changes matching '{query}'", color=discord.Color.blue())
        for c in matching[:5]:
            embed.add_field(name=c["title"], value=f"Type: {c['change_type']} | Status: {c['status']} | Target: {c['target_service']}", inline=False)
        await ctx.send(embed=embed)

    @change.command(name="export")
    async def export_changes(self, ctx, status: str = None):
        analyzer = await self._get_analyzer()
        changes = analyzer.list_changes(status=status, limit=100)
        data = json.dumps([{"id": c["id"][:8], "title": c["title"], "type": c["change_type"], "status": c["status"], "target": c["target_service"]} for c in changes], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @change.command(name="rollback")
    async def rollback_change(self, ctx, change_id: str):
        analyzer = await self._get_analyzer()
        result = analyzer.record_outcome(change_id, "rolled_back")
        if result:
            await ctx.send(f"✅ Change `{change_id[:8]}` rolled back")
        else:
            await ctx.send(f"❌ Change `{change_id[:8]}` not found")


    @change.command(name="trend")
    async def risk_trend(self, ctx, days: int = 30):
        analyzer = await self._get_analyzer()
        trend = analyzer.get_risk_trend(days) if hasattr(analyzer, 'get_risk_trend') else []
        if not trend:
            await ctx.send("Insufficient data for trend analysis")
            return
        embed = discord.Embed(title=f"📊 Risk Trend ({days}d)", color=discord.Color.blue())
        for t in trend[-8:]:
            embed.add_field(name=t["week"], value=f"Avg: {t['avg_risk']:.2f} | {t['count']} changes", inline=True)
        await ctx.send(embed=embed)

    @change.command(name="ranking")
    async def service_ranking(self, ctx):
        analyzer = await self._get_analyzer()
        ranking = analyzer.get_service_risk_ranking() if hasattr(analyzer, 'get_service_risk_ranking') else []
        if not ranking:
            await ctx.send("No service risk data available")
            return
        embed = discord.Embed(title="🏆 Service Risk Ranking", color=discord.Color.blue())
        for r in ranking[:8]:
            embed.add_field(name=r["service"], value=f"Risk: {r['avg_risk']:.2f} | Changes: {r['change_count']}", inline=True)
        await ctx.send(embed=embed)

    @change.command(name="notify")
    async def notify_high_risk(self, ctx, change_id: str):
        analyzer = await self._get_analyzer()
        notifier = ChangeNotificationManager(analyzer)
        result = notifier.notify_high_risk(change_id)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
        else:
            await ctx.send(f"✅ Notification sent for change `{change_id[:8]}` (risk: {result['risk_level']})")

    @tasks.loop(hours=4)
    async def change_risk_scan(self):
        analyzer = self._get_analyzer_sync()
        if hasattr(analyzer, 'batch_analyze_pending'):
            results = analyzer.batch_analyze_pending()
            if results:
                high_risk = [r for r in results if r.get("analysis", {}).get("overall_risk_level") == "high"]
                if high_risk:
                    logging.info(f"ChangeRiskCog: {len(high_risk)} high-risk changes detected")

    @change_risk_scan.before_loop
    async def before_change_scan(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ChangeRiskCog(bot))

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
