"""Feature 51 Cog: AI Root Cause Analysis"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

ROOT_CAUSE_ANALYSIS_HELP = """
**AI Root Cause Analysis Commands**
`!rca analyze [title] [description]` — Analyze an incident
`!rca events` — List recent events
`!rca ingest [type] [source] [title]` — Ingest an event
`!rca incidents` — List analyzed incidents
`!rca dependency [service] [dep1,dep2,...]` — Set service dependencies
"""


class RootCauseAnalysisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analyzer = None

    async def _get_analyzer(self):
        if self.analyzer is None:
            from services.integration_service.src.aiops.root_cause_analysis import RootCauseAnalyzer
            self.analyzer = RootCauseAnalyzer({})
        return self.analyzer

    @commands.group(name="rca", invoke_without_command=True)
    async def rca(self, ctx):
        await ctx.send(ROOT_CAUSE_ANALYSIS_HELP)

    @rca.command(name="analyze")
    async def analyze_incident(self, ctx, title: str, *, description: str = ""):
        analyzer = await self._get_analyzer()
        result = analyzer.analyze(incident_title=title, incident_description=description)
        embed = discord.Embed(title="🔍 Root Cause Analysis", color=discord.Color.blue())
        if result.get("root_cause"):
            rc = result["root_cause"]
            embed.add_field(name="Root Cause", value=f"**{rc['title']}** ({rc['source']})", inline=False)
            embed.add_field(name="Confidence", value=f"{result['confidence']:.1%}", inline=True)
            embed.add_field(name="Event Type", value=rc["event_type"], inline=True)
        else:
            embed.add_field(name="Result", value=result.get("explanation", "No root cause found"), inline=False)
        if result.get("recommendations"):
            recs = "\n".join(f"• {r}" for r in result["recommendations"][:3])
            embed.add_field(name="Recommendations", value=recs, inline=False)
        embed.set_footer(text=f"Incident ID: {result['incident_id']}")
        await ctx.send(embed=embed)

    @rca.command(name="events")
    async def list_events(self, ctx, limit: int = 10):
        analyzer = await self._get_analyzer()
        events = analyzer.get_events(limit=limit)
        if not events:
            await ctx.send("No events recorded.")
            return
        embed = discord.Embed(title="📋 Recent Events", color=discord.Color.blue())
        for e in events[-limit:]:
            embed.add_field(
                name=f"{e['event_type']} — {e['source']}",
                value=f"{e['title']} ({e['severity']})",
                inline=False
            )
        await ctx.send(embed=embed)

    @rca.command(name="ingest")
    async def ingest_event(self, ctx, event_type: str, source: str, *, title: str):
        analyzer = await self._get_analyzer()
        event = analyzer.ingest_event(event_type, source, title, "")
        embed = discord.Embed(title="📥 Event Ingested", color=discord.Color.green())
        embed.add_field(name="ID", value=event["id"], inline=False)
        embed.add_field(name="Type", value=event_type, inline=True)
        embed.add_field(name="Source", value=source, inline=True)
        await ctx.send(embed=embed)

    @rca.command(name="incidents")
    async def list_incidents(self, ctx, limit: int = 10):
        analyzer = await self._get_analyzer()
        incidents = analyzer.list_incidents(limit=limit)
        if not incidents:
            await ctx.send("No incidents recorded.")
            return
        embed = discord.Embed(title="🚨 Recent Incidents", color=discord.Color.red())
        for i in incidents[-limit:]:
            embed.add_field(name=i["title"], value=f"Source: {i.get('source', 'unknown')}", inline=False)
        await ctx.send(embed=embed)

    @rca.command(name="dependency")
    async def set_dependency(self, ctx, service: str, *, dependencies: str):
        analyzer = await self._get_analyzer()
        deps = [d.strip() for d in dependencies.split(",")]
        analyzer.set_dependency(service, deps)
        embed = discord.Embed(title="🔗 Dependencies Set", color=discord.Color.green())
        embed.add_field(name="Service", value=service, inline=True)
        embed.add_field(name="Depends On", value=", ".join(deps), inline=True)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @rca.command(name="search")
    async def search_events(self, ctx, *, query: str):
        analyzer = await self._get_analyzer()
        events = analyzer.get_events(limit=50)
        matching = [e for e in events if query.lower() in e.get("title", "").lower() or query.lower() in e.get("source", "").lower()]
        if not matching:
            await ctx.send(f"No events matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Events matching '{query}'", color=discord.Color.blue())
        for e in matching[:5]:
            embed.add_field(name=f"{e['event_type']} — {e['source']}", value=e['title'], inline=False)
        await ctx.send(embed=embed)

    @rca.command(name="export")
    async def export_analysis(self, ctx, incident_id: str):
        analyzer = await self._get_analyzer()
        incidents = analyzer.list_incidents(limit=100)
        target = next((i for i in incidents if i.get("incident_id") == incident_id), None)
        if not target:
            await ctx.send(f"Incident `{incident_id[:8]}` not found")
            return
        data = json.dumps(target, indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @rca.command(name="clear")
    async def clear_events(self, ctx):
        analyzer = await self._get_analyzer()
        analyzer.events.clear()
        analyzer.incidents.clear()
        await ctx.send("✅ All events and incidents cleared")

    @rca.command(name="topology")
    async def show_topology(self, ctx):
        analyzer = await self._get_analyzer()
        deps = analyzer.get_dependencies()
        if not deps:
            await ctx.send("No dependencies configured")
            return
        embed = discord.Embed(title="🔗 Service Topology", color=discord.Color.blue())
        for svc, depends in list(deps.items())[:8]:
            embed.add_field(name=svc, value=", ".join(depends), inline=False)
        await ctx.send(embed=embed)


    @rca.command(name="impact")
    async def impact_score(self, ctx, event_id: str):
        scorer = await self._get_analyzer()
        scorer_inst = EventImpactScorer(scorer) if hasattr(scorer, 'events') else None
        if not scorer_inst:
            await ctx.send("Impact scoring not available")
            return
        result = scorer_inst.score_event(event_id)
        if "error" in result:
            await ctx.send(f"❌ {result['error']}")
            return
        embed = discord.Embed(title=f"💥 Impact Score: {event_id[:8]}", color=discord.Color.red())
        embed.add_field(name="Event Type", value=result.get("event_type", "N/A"), inline=True)
        embed.add_field(name="Score", value=str(result.get("total_score", 0)), inline=True)
        embed.add_field(name="Priority", value=result.get("priority", "low"), inline=True)
        embed.add_field(name="Services Affected", value=str(result.get("services_affected", 0)), inline=True)
        await ctx.send(embed=embed)

    @rca.command(name="timeline")
    async def event_timeline(self, ctx, hours: int = 24):
        analyzer = await self._get_analyzer()
        timeline = analyzer.get_event_timeline(hours) if hasattr(analyzer, 'get_event_timeline') else []
        if not timeline:
            await ctx.send("No event data for this period")
            return
        embed = discord.Embed(title=f"📅 Event Timeline ({hours}h)", color=discord.Color.blue())
        for t in timeline[-12:]:
            embed.add_field(name=t["hour"], value=f"{t['count']} events", inline=True)
        await ctx.send(embed=embed)

    @rca.command(name="patterns")
    async def correlation_patterns(self, ctx):
        analyzer = await self._get_analyzer()
        patterns = analyzer.find_correlation_patterns() if hasattr(analyzer, 'find_correlation_patterns') else []
        if not patterns:
            await ctx.send("No correlation patterns found")
            return
        embed = discord.Embed(title="🧩 Correlation Patterns", color=discord.Color.blue())
        for p in patterns[:5]:
            types = ", ".join(t["type"] for t in p.get("common_event_types", []))
            embed.add_field(name=p.get("title", "Unknown"), value=f"Types: {types} | Alerts: {p.get('total_alerts', 0)}", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2)
    async def rca_pattern_miner(self):
        analyzer = self._get_analyzer_sync()
        if hasattr(analyzer, 'find_correlation_patterns'):
            patterns = analyzer.find_correlation_patterns()
            if patterns:
                logging.info(f"RootCauseAnalysisCog: {len(patterns)} patterns found")

    @rca_pattern_miner.before_loop
    async def before_rca_patterns(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RootCauseAnalysisCog(bot))

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
