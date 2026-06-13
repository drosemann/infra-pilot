import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.auditor_portal import AuditorPortalEngine

class AuditorPortalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = AuditorPortalEngine(config={"auditor_data_file": "data/auditor_portal.json"})

    @commands.command(name="auditor-session")
    @commands.has_permissions(administrator=True)
    async def auditor_session(self, ctx, auditor_name: str, auditor_email: str, org: str, frameworks: str):
        session = self.engine.create_session(auditor_name=auditor_name, auditor_email=auditor_email, auditor_org=org,
                                             scope="read_only", frameworks=[f.strip() for f in frameworks.split(",")])
        embed = discord.Embed(title="Auditor Session Created", color=discord.Color.green())
        embed.add_field(name="Session ID", value=session.session_id, inline=True)
        embed.add_field(name="Expires", value=session.access_expires_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="Auditor", value=auditor_name, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-evidence")
    @commands.has_permissions(administrator=True)
    async def auditor_evidence(self, ctx, framework: str = None):
        evidence = self.engine.get_all_evidence(framework=framework)
        embed = discord.Embed(title=f"Available Evidence ({len(evidence)})", color=discord.Color.blue())
        for e in evidence[:10]:
            embed.add_field(name=e["id"], value=f"{e['description']} ({e['framework']})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-findings")
    async def auditor_findings(self, ctx, framework: str = None):
        findings = self.engine.get_findings(framework=framework)
        if not findings:
            await ctx.send("No findings found")
            return
        embed = discord.Embed(title=f"Audit Findings ({len(findings)})", color=discord.Color.orange())
        for f in findings[:10]:
            embed.add_field(name=f"{f.title} ({f.severity.value})", value=f"{f.status.value} - {f.framework}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-stats")
    async def auditor_stats(self, ctx):
        stats = self.engine.get_statistics()
        embed = discord.Embed(title="Auditor Portal Stats", color=discord.Color.blue())
        for k, v in stats.items():
            if not isinstance(v, dict):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-engagement-create")
    @commands.has_permissions(administrator=True)
    async def auditor_engagement_create(self, ctx, org: str, auditor_name: str, auditor_email: str, framework: str):
        from datetime import datetime, timedelta
        engagement = self.engine.create_engagement(auditor_org=org, auditor_name=auditor_name,
                                                    auditor_email=auditor_email, framework=framework,
                                                    scope="full", scope_description="Full audit engagement",
                                                    period_start=datetime.utcnow(),
                                                    period_end=datetime.utcnow() + timedelta(days=90))
        embed = discord.Embed(title="Audit Engagement Created", color=discord.Color.green())
        embed.add_field(name="Audit ID", value=engagement.audit_id, inline=True)
        embed.add_field(name="Framework", value=framework, inline=True)
        embed.add_field(name="Status", value=engagement.status.value, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-engagement-complete")
    @commands.has_permissions(administrator=True)
    async def auditor_engagement_complete(self, ctx, audit_id: str):
        engagement = self.engine.complete_engagement(audit_id)
        if not engagement:
            await ctx.send("Engagement not found")
            return
        embed = discord.Embed(title="Engagement Completed", color=discord.Color.green())
        embed.add_field(name="Audit ID", value=audit_id, inline=True)
        embed.add_field(name="Completed At", value=engagement.completed_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-finding-create")
    @commands.has_permissions(administrator=True)
    async def auditor_finding_create(self, ctx, session_id: str, audit_id: str, control_id: str,
                                      framework: str, severity: str, *, title: str):
        finding = self.engine.create_finding(session_id=session_id, audit_id=audit_id, control_id=control_id,
                                              framework=framework, title=title, description=title, severity=severity)
        if not finding:
            await ctx.send("Failed to create finding - invalid session or permissions")
            return
        embed = discord.Embed(title="Finding Created", color=discord.Color.orange())
        embed.add_field(name="Finding ID", value=finding.finding_id, inline=True)
        embed.add_field(name="Severity", value=finding.severity.value, inline=True)
        embed.add_field(name="Status", value=finding.status.value, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-session-revoke")
    @commands.has_permissions(administrator=True)
    async def auditor_session_revoke(self, ctx, session_id: str):
        session = self.engine.revoke_session(session_id)
        if not session:
            await ctx.send("Session not found")
            return
        embed = discord.Embed(title="Session Revoked", color=discord.Color.orange())
        embed.add_field(name="Session ID", value=session_id, inline=True)
        embed.add_field(name="Status", value=session.status, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-session-extend")
    @commands.has_permissions(administrator=True)
    async def auditor_session_extend(self, ctx, session_id: str, hours: int = 24):
        session = self.engine.extend_session(session_id, hours)
        if not session:
            await ctx.send("Session not found or not active")
            return
        embed = discord.Embed(title="Session Extended", color=discord.Color.green())
        embed.add_field(name="Expires", value=session.access_expires_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="auditor-finding-update")
    @commands.has_permissions(administrator=True)
    async def auditor_finding_update(self, ctx, finding_id: str, status: str, *, notes: str = ""):
        finding = self.engine.update_finding_status(finding_id, status, notes)
        if not finding:
            await ctx.send("Finding not found")
            return
        embed = discord.Embed(title="Finding Updated", color=discord.Color.blue())
        embed.add_field(name="Finding ID", value=finding_id, inline=True)
        embed.add_field(name="New Status", value=finding.status.value, inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AuditorPortalCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class auditor_portal_CogExtension:
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

async def setup_auditor_portal_handlers(bot):
    @bot.command(name="auditor_portal")
    async def auditor_portal_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"auditor_portal {action} command received")
        if action == "status":
            await ctx.send("auditor_portal Cog: Active")
        elif action == "list":
            await ctx.send("auditor_portal listing not yet implemented")

def register_auditor_portal_routes(bot):
    @bot.command(name="auditor_portal_help")
    async def auditor_portal_help(ctx):
        await ctx.send("auditor_portal Commands: status, list, report")


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
