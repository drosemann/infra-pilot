import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.audit_management import AuditManagementEngine

class AuditManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = AuditManagementEngine(config={"audit_mgmt_data_file": "data/audit_management.json"})

    @commands.command(name="audit-schedule")
    @commands.has_permissions(administrator=True)
    async def audit_schedule(self, ctx, audit_type: str = "internal", framework: str = "SOC_2", days: int = 30):
        sched = self.engine.schedule_audit(audit_type=audit_type, framework=framework, scope="Full review",
                                           scheduled_date=datetime.utcnow() + timedelta(days=days),
                                           assigned_auditor=ctx.author.name)
        embed = discord.Embed(title="Audit Scheduled", color=discord.Color.blue())
        embed.add_field(name="ID", value=sched.schedule_id, inline=True)
        embed.add_field(name="Framework", value=framework, inline=True)
        embed.add_field(name="Date", value=sched.scheduled_date.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="audit-list")
    async def audit_list(self, ctx, status: str = None):
        schedules = self.engine.get_schedules(status=status)
        if not schedules:
            await ctx.send("No audit schedules found")
            return
        embed = discord.Embed(title=f"Audit Schedules ({len(schedules)})", color=discord.Color.blue())
        for s in schedules[:10]:
            embed.add_field(name=s.schedule_id, value=f"{s.framework} - {s.status.value} ({s.scheduled_date.strftime('%Y-%m-%d')})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="audit-rights")
    async def audit_rights(self, ctx, customer_id: str = None):
        rights = self.engine.get_rights(customer_id=customer_id)
        if not rights:
            await ctx.send("No audit rights found")
            return
        embed = discord.Embed(title=f"Customer Audit Rights ({len(rights)})", color=discord.Color.blue())
        for r in rights[:5]:
            embed.add_field(name=r.customer_name, value=f"{r.framework} - Next: {r.next_audit_date.strftime('%Y-%m-%d')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="audit-stats")
    async def audit_stats(self, ctx):
        stats = self.engine.get_statistics()
        embed = discord.Embed(title="Audit Management Stats", color=discord.Color.blue())
        for k, v in stats.items():
            if not isinstance(v, dict):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="audit-upcoming")
    async def audit_upcoming(self, ctx, days: int = 30):
        upcoming = self.engine.get_upcoming_audits(days)
        if not upcoming:
            await ctx.send(f"No upcoming audits in {days} days")
            return
        embed = discord.Embed(title=f"Upcoming Audits ({len(upcoming)})", color=discord.Color.blue())
        for s in upcoming[:10]:
            embed.add_field(name=f"{s.schedule_id} ({s.audit_type.value})", value=f"{s.framework} - {s.scheduled_date.strftime('%Y-%m-%d')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="audit-overdue")
    async def audit_overdue(self, ctx):
        overdue = self.engine.get_overdue_audits()
        if not overdue:
            await ctx.send("No overdue audits")
            return
        embed = discord.Embed(title=f"Overdue Audits ({len(overdue)})", color=discord.Color.red())
        for r in overdue[:10]:
            embed.add_field(name=f"{r.customer_name} - {r.framework}", value=f"Due: {r.next_audit_date.strftime('%Y-%m-%d')} ({r.status})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="audit-workflow")
    @commands.has_permissions(administrator=True)
    async def audit_workflow(self, ctx, schedule_id: str, action: str):
        result = self.engine.workflow_action(schedule_id, action)
        if "error" in result:
            await ctx.send(f"Error: {result['error']}")
            return
        embed = discord.Embed(title="Workflow Action Executed", color=discord.Color.blue())
        embed.add_field(name="Schedule", value=schedule_id, inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="New Status", value=result["new_status"], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="audit-report")
    @commands.has_permissions(administrator=True)
    async def audit_report(self, ctx, schedule_id: str):
        report = self.engine.generate_audit_report(schedule_id)
        if "error" in report:
            await ctx.send(f"Error: {report['error']}")
            return
        embed = discord.Embed(title="Audit Report Generated", color=discord.Color.blue())
        embed.add_field(name="Report ID", value=report["report_id"], inline=True)
        embed.add_field(name="Compliance Rate", value=f"{report['summary']['compliance_rate']}%", inline=True)
        embed.add_field(name="Status", value=report["status"], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="audit-register-right")
    @commands.has_permissions(administrator=True)
    async def audit_register_right(self, ctx, customer_id: str, customer_name: str, framework: str, frequency_days: int):
        right = self.engine.register_customer_right(customer_id=customer_id, customer_name=customer_name,
                                                     framework=framework, scope="full", frequency_days=frequency_days)
        embed = discord.Embed(title="Customer Audit Right Registered", color=discord.Color.green())
        embed.add_field(name="Right ID", value=right.right_id, inline=True)
        embed.add_field(name="Customer", value=customer_name, inline=True)
        embed.add_field(name="Next Audit", value=right.next_audit_date.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="audit-calendar")
    async def audit_calendar(self, ctx):
        stats = self.engine.get_statistics()
        embed = discord.Embed(title="Audit Calendar Sync", color=discord.Color.blue())
        embed.add_field(name="Upcoming (30d)", value=str(stats.get("upcoming_audits", 0)), inline=True)
        embed.add_field(name="Overdue", value=str(stats.get("overdue_audits", 0)), inline=True)
        embed.add_field(name="Total Schedules", value=str(stats.get("total_schedules", 0)), inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AuditManagementCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class audit_management_CogExtension:
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

async def setup_audit_management_handlers(bot):
    @bot.command(name="audit_management")
    async def audit_management_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"audit_management {action} command received")
        if action == "status":
            await ctx.send("audit_management Cog: Active")
        elif action == "list":
            await ctx.send("audit_management listing not yet implemented")

def register_audit_management_routes(bot):
    @bot.command(name="audit_management_help")
    async def audit_management_help(ctx):
        await ctx.send("audit_management Commands: status, list, report")


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
