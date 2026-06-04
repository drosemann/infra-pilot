import discord
from discord.ext import commands
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.compliance_training import ComplianceTrainingManager

class ComplianceTrainingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = ComplianceTrainingManager(config={"training_data_file": "data/compliance_training.json"})

    @commands.command(name="training-modules")
    async def training_modules(self, ctx, framework: str = None):
        modules = self.manager.get_modules(framework=framework)
        if not modules:
            await ctx.send("No training modules found")
            return
        embed = discord.Embed(title=f"Training Modules ({len(modules)})", color=discord.Color.blue())
        for m in modules[:10]:
            embed.add_field(name=m.title, value=f"{m.framework} - {m.duration_minutes}min ({m.difficulty.value})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="training-assign")
    @commands.has_permissions(administrator=True)
    async def training_assign(self, ctx, user_id: str, module_id: str, user_name: str = None):
        if not user_name:
            user_name = user_id
        assignment = self.manager.assign_training(user_id=user_id, user_name=user_name, module_id=module_id,
                                                  assigned_by=ctx.author.name)
        embed = discord.Embed(title="Training Assigned", color=discord.Color.green())
        embed.add_field(name="Assignment ID", value=assignment.assignment_id, inline=True)
        embed.add_field(name="Module", value=assignment.module_title, inline=True)
        embed.add_field(name="Due", value=assignment.due_date.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="training-status")
    async def training_status(self, ctx, user_id: str = None):
        assignments = self.manager.get_assignments(user_id=user_id)
        if not assignments:
            await ctx.send("No assignments found")
            return
        embed = discord.Embed(title=f"Training Assignments ({len(assignments)})", color=discord.Color.blue())
        for a in assignments[:10]:
            status_emoji = {"completed": "✅", "in_progress": "🔄", "not_started": "⏳", "failed": "❌", "expired": "⌛"}
            embed.add_field(name=f"{status_emoji.get(a.status.value, '❓')} {a.module_title}", value=f"{a.user_name} - {a.status.value}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="training-stats")
    async def training_stats(self, ctx):
        stats = self.manager.get_statistics()
        embed = discord.Embed(title="Training Statistics", color=discord.Color.blue())
        for k, v in stats.items():
            if not isinstance(v, (dict, list)):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="training-certifications")
    async def training_certifications(self, ctx, user_id: str = None):
        certs = self.manager.get_certifications(user_id=user_id)
        if not certs:
            await ctx.send("No certifications found")
            return
        embed = discord.Embed(title=f"Certifications ({len(certs)})", color=discord.Color.blue())
        for c in certs[:10]:
            status_emoji = "✅" if c.status == "active" else "⌛"
            embed.add_field(name=f"{status_emoji} {c.module_title}", value=f"{c.user_name} - Expires: {c.expires_at.strftime('%Y-%m-%d')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="training-expiring")
    async def training_expiring(self, ctx, days: int = 30):
        expiring = self.manager.get_expiring_soon(days)
        if not expiring:
            await ctx.send(f"No certificates expiring within {days} days")
            return
        embed = discord.Embed(title=f"Expiring Certificates ({len(expiring)})", color=discord.Color.orange())
        for c in expiring[:10]:
            embed.add_field(name=c.module_title, value=f"{c.user_name} - Expires {c.expires_at.strftime('%Y-%m-%d')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="training-search")
    async def training_search(self, ctx, *, query: str):
        results = self.manager.search_modules(query)
        if not results:
            await ctx.send(f"No modules found for '{query}'")
            return
        embed = discord.Embed(title=f"Training Modules ({len(results)})", color=discord.Color.blue())
        for m in results[:10]:
            embed.add_field(name=m.title, value=f"{m.framework} - {m.difficulty.value} ({m.duration_minutes}min)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="training-report")
    @commands.has_permissions(administrator=True)
    async def training_report(self, ctx, framework: str = None):
        report = self.manager.get_training_report(framework)
        embed = discord.Embed(title="Training Report", color=discord.Color.blue())
        for k, v in report.items():
            if not isinstance(v, (dict, list)):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="training-progress")
    async def training_progress(self, ctx, user_id: str):
        progress = self.manager.get_learner_progress(user_id)
        embed = discord.Embed(title=f"Learner Progress: {user_id[:8]}", color=discord.Color.blue())
        embed.add_field(name="Total", value=str(progress["total_assignments"]), inline=True)
        embed.add_field(name="Completed", value=str(progress["completed"]), inline=True)
        embed.add_field(name="In Progress", value=str(progress["in_progress"]), inline=True)
        embed.add_field(name="Not Started", value=str(progress["not_started"]), inline=True)
        embed.add_field(name="Avg Score", value=str(progress["average_score"]), inline=True)
        embed.add_field(name="Active Certs", value=str(progress["active_certifications"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="training-batch-assign")
    @commands.has_permissions(administrator=True)
    async def training_batch_assign(self, ctx, module_id: str, user_ids: str):
        uid_list = [u.strip() for u in user_ids.split(",")]
        assignments = self.manager.batch_assign(uid_list, module_id, assigned_by=ctx.author.name)
        await ctx.send(f"Assigned {len(assignments)} users to module {module_id}")


async def setup(bot):
    await bot.add_cog(ComplianceTrainingCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class compliance_training_CogExtension:
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

async def setup_compliance_training_handlers(bot):
    @bot.command(name="compliance_training")
    async def compliance_training_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"compliance_training {action} command received")
        if action == "status":
            await ctx.send("compliance_training Cog: Active")
        elif action == "list":
            await ctx.send("compliance_training listing not yet implemented")

def register_compliance_training_routes(bot):
    @bot.command(name="compliance_training_help")
    async def compliance_training_help(ctx):
        await ctx.send("compliance_training Commands: status, list, report")


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
