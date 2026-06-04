"""Feature 60 Cog: Self-Service Operations Chatbot"""

import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

OPS_CHATBOT_HELP = """
**Self-Service Operations Chatbot**
Ask me to perform operations tasks! Examples:
• "restart nginx" — Restart a service
• "logs api-server" — View service logs
• "backup postgres" — Create a backup
• "status web-server" — Check service status
• "list services" — List all services
• "scale api-service 5" — Scale a service
• "deploy v3.2 staging" — Deploy a version
• "clear cache cdn" — Clear service cache
• "diagnostic database" — Run diagnostics
• "metrics gateway" — Show service metrics
• "help" — Show all commands
"""


class OpsChatbotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = None

    async def _get_chatbot(self):
        if self.chatbot is None:
            from services.integration_service.src.aiops.ops_chatbot import OpsChatbot
            self.chatbot = OpsChatbot({})
        return self.chatbot

    @commands.group(name="bot", invoke_without_command=True)
    async def bot_cmd(self, ctx, *, message: str = None):
        if message is None:
            await ctx.send(OPS_CHATBOT_HELP)
            return
        chatbot = await self._get_chatbot()
        result = chatbot.process_message(str(ctx.author.id), message, ["user"])
        embed = discord.Embed(
            title="🤖 Ops Bot",
            description=result.get("text", "I couldn't process that."),
            color=discord.Color.green() if result.get("type") == "success" else discord.Color.red()
        )
        if result.get("quick_replies"):
            qr = " | ".join(result["quick_replies"][:5])
            embed.add_field(name="Quick Replies", value=qr, inline=False)
        await ctx.send(embed=embed)

    @bot_cmd.command(name="restart")
    async def bot_restart(self, ctx, *, service: str):
        chatbot = await self._get_chatbot()
        result = chatbot.process_message(str(ctx.author.id), f"restart {service}", ["user"])
        embed = discord.Embed(title="🔄 Restart Service", description=result.get("text", ""), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @bot_cmd.command(name="logs")
    async def bot_logs(self, ctx, *, service: str):
        chatbot = await self._get_chatbot()
        result = chatbot.process_message(str(ctx.author.id), f"logs {service}", ["user"])
        embed = discord.Embed(title="📋 Service Logs", description=result.get("text", ""), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @bot_cmd.command(name="status")
    async def bot_status(self, ctx, *, service: str = None):
        chatbot = await self._get_chatbot()
        msg = f"status {service}" if service else "list services"
        result = chatbot.process_message(str(ctx.author.id), msg, ["user"])
        embed = discord.Embed(title="🔍 Service Status", description=result.get("text", ""), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @bot_cmd.command(name="backup")
    async def bot_backup(self, ctx, *, service: str):
        chatbot = await self._get_chatbot()
        result = chatbot.process_message(str(ctx.author.id), f"backup {service}", ["user"])
        embed = discord.Embed(title="💾 Backup", description=result.get("text", ""), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @bot_cmd.command(name="list")
    async def bot_list(self, ctx):
        chatbot = await self._get_chatbot()
        result = chatbot.process_message(str(ctx.author.id), "list services", ["user"])
        embed = discord.Embed(title="📋 Services", description=result.get("text", ""), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @bot_cmd.command(name="help")
    async def bot_help(self, ctx):
        await ctx.send(OPS_CHATBOT_HELP)

    @bot_cmd.command(name="history")
    async def bot_history(self, ctx, limit: int = 10):
        chatbot = await self._get_chatbot()
        tasks = chatbot.list_tasks(user_id=str(ctx.author.id), limit=limit)
        if not tasks:
            await ctx.send("No task history.")
            return
        embed = discord.Embed(title="📜 Task History", color=discord.Color.blue())
        for t in tasks[-limit:]:
            emoji = "✅" if t.get("result", {}).get("success") else "❌"
            embed.add_field(
                name=f"{emoji} {t['task_type']}",
                value=f"Target: {t['params'].get('target', 'N/A')} | Status: {t['status']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @bot_cmd.command(name="stats")
    async def bot_stats(self, ctx):
        chatbot = await self._get_chatbot()
        analytics = chatbot.get_analytics()
        embed = discord.Embed(title="📊 Chatbot Analytics", color=discord.Color.blue())
        embed.add_field(name="Total Messages", value=analytics["total_messages"], inline=True)
        embed.add_field(name="Completed Tasks", value=analytics["tasks_completed"], inline=True)
        embed.add_field(name="Failed Tasks", value=analytics["tasks_failed"], inline=True)
        embed.add_field(name="Success Rate", value=f"{analytics['success_rate']}%", inline=True)
        embed.add_field(name="Active Conversations", value=analytics["active_conversations"], inline=True)
        if analytics.get("popular_commands"):
            popular = "\n".join(f"• {k}: {v}" for k, v in list(analytics["popular_commands"].items())[:5])
            embed.add_field(name="Popular Commands", value=popular, inline=False)
        await ctx.send(embed=embed)


    # ===== APPENDED: Permission checks, background tasks, additional commands =====

    @bot_cmd.command(name="search")
    async def search_bot(self, ctx, *, query: str):
        chatbot = await self._get_chatbot()
        tasks = chatbot.list_tasks(limit=100)
        matching = [t for t in tasks if query.lower() in t.get("task_type", "").lower() or query.lower() in str(t.get("params", {})).lower()]
        if not matching:
            await ctx.send(f"No tasks matching `{query}`")
            return
        embed = discord.Embed(title=f"🔍 Tasks matching '{query}'", color=discord.Color.blue())
        for t in matching[-5:]:
            emoji = "✅" if t.get("result", {}).get("success") else "❌"
            embed.add_field(name=f"{emoji} {t['task_type']}", value=f"Target: {t['params'].get('target', 'N/A')}", inline=False)
        await ctx.send(embed=embed)

    @bot_cmd.command(name="export")
    async def export_tasks(self, ctx):
        chatbot = await self._get_chatbot()
        tasks = chatbot.list_tasks(limit=100)
        data = json.dumps([{"type": t["task_type"], "status": t["status"], "target": t["params"].get("target")} for t in tasks], indent=2)
        await ctx.send(f"```json\n{data[:1900]}\n```")

    @commands.is_owner()
    @bot_cmd.command(name="reset")
    async def reset_bot(self, ctx):
        chatbot = await self._get_chatbot()
        chatbot.conversations.clear()
        chatbot.task_queue.clear()
        await ctx.send("✅ Chatbot data reset")


    @ops.command(name="summary")
    async def conversation_summary(self, ctx, hours: int = 24):
        engine = await self._get_engine()
        summary = engine.get_conversation_summary(hours) if hasattr(engine, 'get_conversation_summary') else {}
        if not summary:
            await ctx.send("No conversation data for this period")
            return
        embed = discord.Embed(title=f"💬 Conversation Summary ({hours}h)", color=discord.Color.blue())
        embed.add_field(name="Total", value=summary.get("total", 0), inline=True)
        embed.add_field(name="Avg Sentiment", value=f'{summary.get("avg_sentiment", 0):.2f}', inline=True)
        embed.add_field(name="Resolution Rate", value=f'{summary.get("resolution_rate", 0):.0%}', inline=True)
        await ctx.send(embed=embed)

    @ops.command(name="popular")
    async def popular_ops_commands(self, ctx):
        engine = await self._get_engine()
        popular = engine.get_popular_ops_commands() if hasattr(engine, 'get_popular_ops_commands') else []
        if not popular:
            await ctx.send("No command usage data")
            return
        embed = discord.Embed(title="🔥 Popular Ops Commands", color=discord.Color.blue())
        for c in popular[:6]:
            embed.add_field(name=c.get("command", "?"), value=f"{c.get('count', 0)} uses ({c.get('share', 0):.0%})", inline=False)
        await ctx.send(embed=embed)

    @ops.command(name="priorities")
    async def task_priorities(self, ctx):
        engine = await self._get_engine()
        prioritizer = TaskPrioritizer(engine)
        priorities = prioritizer.get_priorities()
        if not priorities:
            await ctx.send("No pending tasks")
            return
        embed = discord.Embed(title="📋 Task Priorities", color=discord.Color.blue())
        for p in priorities[:5]:
            embed.add_field(name=f"[{p.get('priority', '?')}] {p.get('title', '?')}", value=f"Impact: {p.get('impact', 0):.2f} | Urgency: {p.get('urgency', 0):.2f}", inline=False)
        await ctx.send(embed=embed)

    @ops.command(name="dash")
    async def ops_dashboard(self, ctx):
        engine = await self._get_engine()
        dash = engine.get_ops_dashboard() if hasattr(engine, 'get_ops_dashboard') else {}
        if not dash:
            await ctx.send("No dashboard data available")
            return
        embed = discord.Embed(title="📊 Ops Dashboard", color=discord.Color.blue())
        embed.add_field(name="Active Conv", value=str(dash.get("active_conversations", 0)), inline=True)
        embed.add_field(name="Pending Tasks", value=str(dash.get("pending_tasks", 0)), inline=True)
        embed.add_field(name="Avg Response", value=f'{dash.get("avg_response_time_s", 0):.1f}s', inline=True)
        embed.add_field(name="SLA", value=f'{dash.get("sla_achievement", 0):.0%}', inline=True)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2)
    async def ops_analytics_loop(self):
        engine = self._get_engine_sync()
        if hasattr(engine, 'get_conversation_summary'):
            summary = engine.get_conversation_summary(24)
            if summary:
                logging.info(f"OpsChatbotCog: {summary.get('total', 0)} conv in 24h, sentiment {summary.get('avg_sentiment', 0):.2f}")

    @ops_analytics_loop.before_loop
    async def before_ops_analytics(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(OpsChatbotCog(bot))

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
