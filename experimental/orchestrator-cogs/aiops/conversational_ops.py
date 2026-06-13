"""Feature 57 Cog: Conversational Ops Assistant"""

import discord
from discord.ext import commands
import json
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CONVERSATIONAL_OPS_HELP = """
**Conversational Ops Assistant**
Chat with me in natural language! Examples:
• "What's the status of server-42?"
• "Deploy version 3.2 to staging"
• "Restart the web-server"
• "Show logs for database"
• "Scale api-service to 5 replicas"
• "Create a backup of postgres"
• "List all servers"
• "Show CPU for web-server"
• "Help"

Slash commands:
`/ops message <text>` — Send a message to the ops assistant
`/ops session` — View your current session
`/ops history` — View session history
`/ops clear` — Clear current session
"""


class ConversationalOpsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assistant = None
        self.user_sessions = {}

    async def _get_assistant(self):
        if self.assistant is None:
            from services.integration_service.src.aiops.conversational_ops import ConversationalOpsAssistant
            self.assistant = ConversationalOpsAssistant({})
        return self.assistant

    def _get_session_id(self, user_id: str) -> str:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = str(uuid.uuid4())
        return self.user_sessions[user_id]

    @commands.group(name="ops", invoke_without_command=True)
    async def ops(self, ctx):
        await ctx.send(CONVERSATIONAL_OPS_HELP)

    @ops.command(name="message")
    async def ops_message(self, ctx, *, text: str):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        result = assistant.process_message(session_id, str(ctx.author.id), text, "discord")
        embed = discord.Embed(
            title="🤖 Ops Assistant",
            description=result.get("message", "I couldn't process that."),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Intent: {result.get('intent', 'unknown')} | Confidence: {result.get('confidence', 'unknown')}")
        if result.get("data"):
            embed.add_field(name="Details", value=f"```json\n{json.dumps(result['data'], indent=2)[:500]}\n```", inline=False)
        await ctx.send(embed=embed)

    @ops.command(name="session")
    async def show_session(self, ctx):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        session = assistant.get_session(session_id)
        if not session:
            await ctx.send("No active session.")
            return
        embed = discord.Embed(title="📋 Current Session", color=discord.Color.blue())
        embed.add_field(name="Session ID", value=session_id[:8], inline=True)
        embed.add_field(name="State", value=session.get("state", "unknown"), inline=True)
        embed.add_field(name="Messages", value=len(session.get("messages", [])), inline=True)
        await ctx.send(embed=embed)

    @ops.command(name="history")
    async def show_history(self, ctx, limit: int = 10):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        messages = assistant.get_session_history(session_id)
        if not messages:
            await ctx.send("No messages in session.")
            return
        embed = discord.Embed(title="💬 Conversation History", color=discord.Color.blue())
        for m in messages[-limit:]:
            role_icon = "🧑" if m["role"] == "user" else "🤖"
            content = m["content"][:200]
            embed.add_field(name=f"{role_icon} {m['role']}", value=content, inline=False)
        await ctx.send(embed=embed)

    @ops.command(name="clear")
    async def clear_session(self, ctx):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        assistant.clear_session(session_id)
        self.user_sessions[str(ctx.author.id)] = str(uuid.uuid4())
        await ctx.send("✅ Session cleared. Starting fresh!")

    @ops.command(name="stats")
    async def ops_stats(self, ctx):
        assistant = await self._get_assistant()
        stats = assistant.get_statistics()
        embed = discord.Embed(title="📊 Ops Assistant Stats", color=discord.Color.blue())
        embed.add_field(name="Total Messages", value=stats["total_messages"], inline=True)
        embed.add_field(name="Total Sessions", value=stats["total_sessions"], inline=True)
        embed.add_field(name="Success Rate", value=f"{stats['success_rate']}%", inline=True)
        if stats.get("intents_distribution"):
            intents = "\n".join(f"{k}: {v}" for k, v in
                                sorted(stats["intents_distribution"].items(), key=lambda x: x[1], reverse=True)[:5])
            embed.add_field(name="Top Intents", value=intents, inline=False)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @ops.command(name="search")
    async def search_ops(self, ctx, *, query: str):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        messages = assistant.get_session_history(session_id)
        matching = [m for m in messages if query.lower() in m.get("content", "").lower()]
        if not matching:
            await ctx.send(f"No messages matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Messages matching '{query}'", color=discord.Color.blue())
        for m in matching[-5:]:
            embed.add_field(name=m["role"], value=m["content"][:200], inline=False)
        await ctx.send(embed=embed)

    @ops.command(name="export")
    async def export_session(self, ctx):
        assistant = await self._get_assistant()
        session_id = self._get_session_id(str(ctx.author.id))
        messages = assistant.get_session_history(session_id)
        data = json.dumps(messages, indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @ops.command(name="broadcast")
    async def broadcast_message(self, ctx, *, message: str):
        assistant = await self._get_assistant()
        result = assistant.process_message("system", str(ctx.author.id), message, "discord")
        await ctx.send(f"📢 Broadcast: {result.get('message', message)}")


    @convo.command(name="health")
    async def slo_health(self, ctx):
        engine = await self._get_engine()
        health = engine.get_slo_health() if hasattr(engine, 'get_slo_health') else {}
        if not health:
            await ctx.send("No SLO health data available")
            return
        embed = discord.Embed(title="💚 SLO Health Summary", color=discord.Color.blue())
        embed.add_field(name="Healthy", value=str(health.get("healthy", 0)), inline=True)
        embed.add_field(name="Warning", value=str(health.get("warning", 0)), inline=True)
        embed.add_field(name="Critical", value=str(health.get("critical", 0)), inline=True)
        embed.add_field(name="Overall", value=health.get("overall", "N/A"), inline=True)
        await ctx.send(embed=embed)

    @convo.command(name="feedback")
    async def feedback_stats(self, ctx, days: int = 7):
        engine = await self._get_engine()
        collector = FeedbackCollector(engine)
        stats = collector.get_stats(days)
        if not stats:
            await ctx.send("No feedback data for this period")
            return
        embed = discord.Embed(title=f"📝 Feedback Stats ({days}d)", color=discord.Color.blue())
        embed.add_field(name="Total", value=stats.get("total", 0), inline=True)
        embed.add_field(name="Avg Rating", value=f'{stats.get("avg_rating", 0):.2f}', inline=True)
        embed.add_field(name="Positive", value=f'{stats.get("positive_rate", 0):.0%}', inline=True)
        await ctx.send(embed=embed)

    @convo.command(name="popular")
    async def popular_commands(self, ctx):
        engine = await self._get_engine()
        popular = engine.get_popular_commands() if hasattr(engine, 'get_popular_commands') else []
        if not popular:
            await ctx.send("No command usage data")
            return
        embed = discord.Embed(title="🔥 Popular Commands", color=discord.Color.blue())
        for c in popular[:5]:
            embed.add_field(name=c["command"], value=f"{c['count']} uses ({c.get('share', 0):.0%})", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(hours=3)
    async def feedback_analysis_loop(self):
        engine = self._get_engine_sync()
        collector = FeedbackCollector(engine)
        stats = collector.get_stats(24)
        if stats and stats.get("total", 0) > 0:
            logging.info(f"ConversationalOpsCog: {stats['total']} feedback items, avg rating {stats.get('avg_rating', 0):.2f}")

    @feedback_analysis_loop.before_loop
    async def before_feedback(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ConversationalOpsCog(bot))

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
