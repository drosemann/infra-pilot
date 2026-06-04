import discord
from discord.ext import commands
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.regulatory_intel import RegulatoryIntelligenceEngine

class RegulatoryIntelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = RegulatoryIntelligenceEngine(config={"regulatory_data_file": "data/regulatory_intel.json"})

    @commands.command(name="reg-changes")
    async def reg_changes(self, ctx, impact: str = None):
        changes = self.engine.get_changes(impact_level=impact)
        if not changes:
            await ctx.send("No regulatory changes found")
            return
        embed = discord.Embed(title=f"Regulatory Changes ({len(changes)})", color=discord.Color.blue())
        for c in changes[:10]:
            embed.add_field(name=c.title, value=f"{c.impact_level.value} - {c.regulation} ({c.status})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="reg-detect")
    @commands.has_permissions(administrator=True)
    async def reg_detect(self, ctx, title: str, regulation: str, jurisdiction: str, impact: str = "medium"):
        change = self.engine.detect_change(title=title, source="news", change_type="guidance_update",
                                           description=title, regulation=regulation, jurisdiction=jurisdiction,
                                           impact_level=impact, action_required=True)
        embed = discord.Embed(title="Regulatory Change Detected", color=discord.Color.orange())
        embed.add_field(name="ID", value=change.change_id, inline=True)
        embed.add_field(name="Title", value=change.title, inline=True)
        embed.add_field(name="Impact", value=change.impact_level.value, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reg-sources")
    async def reg_sources(self, ctx):
        sources = self.engine.get_sources()
        embed = discord.Embed(title="Monitored Sources", color=discord.Color.blue())
        for s in sources:
            embed.add_field(name=s["name"], value=f"{s['jurisdiction']} - {s['source_type']}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reg-stats")
    async def reg_stats(self, ctx):
        stats = self.engine.get_statistics()
        embed = discord.Embed(title="Regulatory Intel Stats", color=discord.Color.blue())
        embed.add_field(name="Total Changes", value=str(stats["total_changes"]), inline=True)
        embed.add_field(name="Action Required", value=str(stats["action_required"]), inline=True)
        embed.add_field(name="Sources", value=str(stats["sources_monitored"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reg-impact")
    async def reg_impact(self, ctx, change_id: str):
        analysis = self.engine.get_impact_analysis(change_id)
        if "error" in analysis:
            await ctx.send(f"Error: {analysis['error']}")
            return
        embed = discord.Embed(title="Impact Analysis", color=discord.Color.orange())
        embed.add_field(name="Change", value=analysis["change"]["title"], inline=False)
        embed.add_field(name="Affected Frameworks", value=str(analysis["impact_summary"]["affected_frameworks"]), inline=True)
        embed.add_field(name="Action Required", value=str(analysis["impact_summary"]["action_required"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reg-matrix")
    async def reg_matrix(self, ctx):
        matrix = self.engine.impact_matrix()
        embed = discord.Embed(title="Impact Matrix", color=discord.Color.blue())
        embed.add_field(name="Total Changes", value=str(matrix["total_changes_tracked"]), inline=True)
        embed.add_field(name="Most Impacted", value=str(matrix["most_impacted"]), inline=True)
        for fw, data in list(matrix.get("matrix", {}).items())[:5]:
            embed.add_field(name=fw, value=f"Critical: {data['critical']}, High: {data['high']}, Action: {data['action_required']}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="reg-calendar")
    async def reg_calendar(self, ctx, year: int = None):
        import datetime
        yr = year or datetime.datetime.utcnow().year
        events = self.engine.get_calendar(yr)
        if not events:
            await ctx.send(f"No regulatory events for {yr}")
            return
        embed = discord.Embed(title=f"Regulatory Calendar {yr} ({len(events)} events)", color=discord.Color.blue())
        for e in events[:15]:
            emoji = "🔴" if e["impact"] == "critical" else "🟡" if e["impact"] == "high" else "🟢"
            embed.add_field(name=f"{emoji} {e['title'][:50]}", value=f"{e['date'][:10]} - {e['type']}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="reg-notify")
    @commands.has_permissions(administrator=True)
    async def reg_notify(self, ctx, change_id: str):
        result = self.engine.route_notification(change_id)
        if "error" in result:
            await ctx.send(f"Error: {result['error']}")
            return
        embed = discord.Embed(title="Notification Routed", color=discord.Color.green())
        embed.add_field(name="Notification ID", value=result["notification_id"], inline=True)
        embed.add_field(name="Channels", value=", ".join(result["channels"]), inline=True)
        embed.add_field(name="Status", value=result["status"], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reg-pending")
    async def reg_pending(self, ctx, days: int = 30):
        pending = self.engine.get_pending_actions(days)
        if not pending:
            await ctx.send(f"No pending actions in {days} days")
            return
        embed = discord.Embed(title=f"Pending Actions ({len(pending)})", color=discord.Color.orange())
        for p in pending[:10]:
            embed.add_field(name=f"{p['title'][:50]}", value=f"Deadline: {p['deadline'][:10]} ({p['days_remaining']}d left)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="reg-search")
    async def reg_search(self, ctx, *, query: str):
        results = self.engine.search_regulations(query)
        if not results:
            await ctx.send(f"No results for '{query}'")
            return
        embed = discord.Embed(title=f"Regulatory Search ({len(results)} matches)", color=discord.Color.blue())
        for r in results[:10]:
            embed.add_field(name=r["title"], value=f"{r['regulation']} - {r['jurisdiction']} ({r['impact_level']})", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RegulatoryIntelCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class regulatory_intel_CogExtension:
    def __init__(self, bot=None):
        self.bot = bot
        self.handlers = []
    def register(self, handler):
        self.handlers.append(handler)
    async def execute(self, ctx, *args):
        for h in self.handlers:
            try:
                await h(ctx, *args)
            except Exception as e:
                await ctx.send(f"Error in handler: {e}")

async def setup_regulatory_intel_handlers(bot):
    @bot.command(name="regulatory_intel")
    async def regulatory_intel_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"regulatory_intel {action} command received")
        if action == "status":
            await ctx.send("regulatory_intel Cog: Active")
        elif action == "list":
            await ctx.send("regulatory_intel listing not yet implemented")

def register_regulatory_intel_routes(bot):
    @bot.command(name="regulatory_intel_help")
    async def regulatory_intel_help(ctx):
        await ctx.send("regulatory_intel Commands: status, list, report")


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
        return {"total_ops": 0, "compliant": 0, "non_compliant": 0, "score": 100.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class ComplianceCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    control_id: str = ""
    status: str = Field(default="compliant")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    framework: str = Field(default="generic")
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

class ComplianceCogMetrics:
    def __init__(self) -> None:
        self.checks: int = 0
        self.passes: int = 0
        self.failures: int = 0
        self.total_duration_ms: float = 0.0

    def record(self, passed: bool, duration_ms: float = 0.0) -> None:
        self.checks += 1
        if passed:
            self.passes += 1
        else:
            self.failures += 1
        self.total_duration_ms += duration_ms

    def summary(self) -> Dict[str, Any]:
        return {"checks": self.checks, "passes": self.passes, "failures": self.failures,
                "pass_rate": round(self.passes / max(self.checks, 1) * 100, 1),
                "avg_duration_ms": round(self.total_duration_ms / max(self.checks, 1), 1)}
