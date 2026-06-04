import discord
from discord.ext import commands
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.vendor_compliance import VendorComplianceManager

class VendorComplianceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = VendorComplianceManager(config={"vendor_compliance_file": "data/vendor_compliance.json"})

    @commands.command(name="vendor-list")
    async def vendor_list(self, ctx, risk_tier: str = None):
        vendors = self.manager.get_vendors(risk_tier=risk_tier)
        if not vendors:
            await ctx.send("No vendors found")
            return
        embed = discord.Embed(title=f"Vendors ({len(vendors)})", color=discord.Color.blue())
        for v in vendors[:10]:
            embed.add_field(name=v.name, value=f"{v.domain} - Risk: {v.risk_tier.value} ({v.risk_score:.1f})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-register")
    @commands.has_permissions(administrator=True)
    async def vendor_register(self, ctx, name: str, domain: str, contact_email: str, risk_tier: str = "medium"):
        vendor = self.manager.register_vendor(name=name, domain=domain, category="saas", contact_email=contact_email, risk_tier=risk_tier)
        embed = discord.Embed(title="Vendor Registered", color=discord.Color.green())
        embed.add_field(name="ID", value=vendor.vendor_id, inline=True)
        embed.add_field(name="Name", value=vendor.name, inline=True)
        embed.add_field(name="Risk Score", value=f"{vendor.risk_score:.1f}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-assess")
    @commands.has_permissions(administrator=True)
    async def vendor_assess(self, ctx, vendor_id: str):
        assessment = self.manager.create_assessment(vendor_id)
        if not assessment:
            await ctx.send("Vendor not found")
            return
        embed = discord.Embed(title="Assessment Created", color=discord.Color.blue())
        embed.add_field(name="ID", value=assessment.assessment_id, inline=True)
        embed.add_field(name="Questions", value=str(len(assessment.questions)), inline=True)
        embed.add_field(name="Status", value=assessment.status.value, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-risk")
    async def vendor_risk(self, ctx):
        summary = self.manager.get_risk_summary()
        embed = discord.Embed(title="Vendor Risk Summary", color=discord.Color.blue())
        for k, v in summary.items():
            if not isinstance(v, dict):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-scorecard")
    async def vendor_scorecard(self, ctx, vendor_id: str):
        scorecard = self.manager.get_scorecard(vendor_id)
        if "error" in scorecard:
            await ctx.send(f"Error: {scorecard['error']}")
            return
        embed = discord.Embed(title=f"Scorecard: {scorecard['vendor']['name']}", color=discord.Color.blue())
        embed.add_field(name="Avg Score", value=str(scorecard.get("average_score", "N/A")), inline=True)
        embed.add_field(name="Latest Score", value=str(scorecard.get("latest_score", "N/A")), inline=True)
        embed.add_field(name="Trend", value=scorecard.get("score_trend", "stable"), inline=True)
        embed.add_field(name="Findings", value=str(scorecard.get("total_findings", 0)), inline=True)
        embed.add_field(name="Critical", value=str(scorecard.get("critical_findings", 0)), inline=True)
        embed.add_field(name="Risk", value=scorecard.get("risk_assessment", "unknown"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-assessments")
    async def vendor_assessments(self, ctx, vendor_id: str):
        assessments = self.manager.get_assessments(vendor_id=vendor_id)
        if not assessments:
            await ctx.send("No assessments found for this vendor")
            return
        embed = discord.Embed(title=f"Assessments ({len(assessments)})", color=discord.Color.blue())
        for a in assessments[:5]:
            embed.add_field(name=a.assessment_id, value=f"Score: {a.overall_score:.1f} - {a.status.value} ({a.completed_at.strftime('%Y-%m-%d') if a.completed_at else 'N/A'})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-migrate-tier")
    @commands.has_permissions(administrator=True)
    async def vendor_migrate_tier(self, ctx, vendor_id: str, new_tier: str, *, reason: str = ""):
        vendor = self.manager.migrate_tier(vendor_id, new_tier, reason)
        if not vendor:
            await ctx.send("Vendor not found")
            return
        embed = discord.Embed(title="Vendor Tier Migrated", color=discord.Color.green())
        embed.add_field(name="Vendor", value=vendor.name, inline=True)
        embed.add_field(name="New Tier", value=vendor.risk_tier.value, inline=True)
        embed.add_field(name="Risk Score", value=f"{vendor.risk_score:.1f}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-categories")
    async def vendor_categories(self, ctx):
        categories = self.manager.categorize_vendors()
        embed = discord.Embed(title="Vendor Categories", color=discord.Color.blue())
        for cat, count in categories.get("vendor_counts", {}).items():
            embed.add_field(name=cat, value=str(count), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-discover")
    @commands.has_permissions(administrator=True)
    async def vendor_discover(self, ctx, *, domains: str):
        domain_list = [d.strip() for d in domains.split(",")]
        discovered = self.manager.discover_vendors(domain_list)
        if not discovered:
            await ctx.send("No new vendors discovered")
            return
        embed = discord.Embed(title=f"Discovered {len(discovered)} Vendors", color=discord.Color.green())
        for v in discovered[:5]:
            embed.add_field(name=v.name, value=f"{v.domain} - {v.risk_tier.value}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="vendor-remediation")
    async def vendor_remediation(self, ctx, vendor_id: str):
        plan = self.manager.get_remediation_plan(vendor_id)
        if "error" in plan:
            await ctx.send(f"Error: {plan['error']}")
            return
        embed = discord.Embed(title=f"Remediation Plan: {plan['vendor_name']}", color=discord.Color.orange())
        embed.add_field(name="Total Findings", value=str(plan["total_findings"]), inline=True)
        for find in plan["findings"][:5]:
            sev_emoji = "🔴" if find["severity"] == "critical" else "🟡" if find["severity"] == "high" else "🟢"
            embed.add_field(name=f"{sev_emoji} {find['category']}", value=find["finding"][:80], inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VendorComplianceCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class vendor_compliance_CogExtension:
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

async def setup_vendor_compliance_handlers(bot):
    @bot.command(name="vendor_compliance")
    async def vendor_compliance_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"vendor_compliance {action} command received")
        if action == "status":
            await ctx.send("vendor_compliance Cog: Active")
        elif action == "list":
            await ctx.send("vendor_compliance listing not yet implemented")

def register_vendor_compliance_routes(bot):
    @bot.command(name="vendor_compliance_help")
    async def vendor_compliance_help(ctx):
        await ctx.send("vendor_compliance Commands: status, list, report")


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
