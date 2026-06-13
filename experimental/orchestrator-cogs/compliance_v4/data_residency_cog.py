import discord
from discord.ext import commands
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.data_residency import DataResidencyEnforcer

class DataResidencyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enforcer = DataResidencyEnforcer(config={"residency_data_file": "data/data_residency.json"})

    @commands.command(name="residency-list")
    async def residency_list(self, ctx, classification: str = None):
        assets = self.enforcer.get_assets(classification=classification)
        if not assets:
            await ctx.send("No data assets found")
            return
        embed = discord.Embed(title=f"Data Assets ({len(assets)})", color=discord.Color.blue())
        for a in assets[:10]:
            status_emoji = "✅" if a.status == "active" else "❌"
            embed.add_field(name=f"{status_emoji} {a.name}", value=f"{a.asset_type} - {a.current_region.value} ({a.classification.value})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="residency-register")
    @commands.has_permissions(administrator=True)
    async def residency_register(self, ctx, name: str, asset_type: str, classification: str, jurisdiction: str, region: str):
        asset = self.enforcer.register_asset(name=name, asset_type=asset_type, classification=classification,
                                             jurisdiction=jurisdiction, current_region=region)
        embed = discord.Embed(title="Asset Registered", color=discord.Color.green())
        embed.add_field(name="ID", value=asset.asset_id, inline=True)
        embed.add_field(name="Region", value=asset.current_region.value, inline=True)
        embed.add_field(name="Status", value=asset.status, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="residency-check")
    @commands.has_permissions(administrator=True)
    async def residency_check(self, ctx, asset_id: str, target_region: str, framework: str = "GDPR"):
        flow = self.enforcer.check_flow(asset_id=asset_id, target_region=target_region, framework=framework)
        emoji = "✅" if flow.status.value == "compliant" else "❌"
        embed = discord.Embed(title=f"{emoji} Cross-Border Flow Check", color=discord.Color.green() if flow.status.value == "compliant" else discord.Color.red())
        embed.add_field(name="Asset", value=asset_id, inline=True)
        embed.add_field(name="Target", value=target_region, inline=True)
        embed.add_field(name="Status", value=flow.status.value, inline=True)
        embed.add_field(name="Reason", value=flow.reason, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="residency-summary")
    async def residency_summary(self, ctx):
        summary = self.enforcer.get_summary()
        embed = discord.Embed(title="Data Residency Summary", color=discord.Color.blue())
        for k, v in summary.items():
            if not isinstance(v, dict):
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="residency-flows")
    async def residency_flows(self, ctx, status: str = None):
        flows = self.enforcer.get_flows(status=status)
        if not flows:
            await ctx.send("No cross-border flows found")
            return
        embed = discord.Embed(title=f"Cross-Border Flows ({len(flows)})", color=discord.Color.blue())
        for f in list(flows)[:10]:
            emoji = "✅" if f.status.value == "compliant" else "❌"
            embed.add_field(name=f"{emoji} {f.flow_id}", value=f"{f.source_region.value} -> {f.target_region.value} ({f.framework})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="residency-move")
    @commands.has_permissions(administrator=True)
    async def residency_move(self, ctx, asset_id: str, target_region: str):
        asset = self.enforcer.move_asset(asset_id, target_region, performed_by=ctx.author.name)
        embed = discord.Embed(title="Asset Moved", color=discord.Color.green())
        embed.add_field(name="Asset", value=asset.name, inline=True)
        embed.add_field(name="New Region", value=asset.current_region.value, inline=True)
        embed.add_field(name="Status", value=asset.status, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="residency-audit")
    async def residency_audit(self, ctx, asset_id: str = None, days: int = 90):
        trail = self.enforcer.get_audit_trail(asset_id=asset_id, days=days)
        if not trail:
            await ctx.send("No audit records found")
            return
        embed = discord.Embed(title=f"Residency Audit Trail ({len(trail)})", color=discord.Color.blue())
        for r in trail[:10]:
            embed.add_field(name=f"{r.timestamp.strftime('%Y-%m-%d %H:%M')} - {r.action}", value=f"{r.details[:60]} ({r.status.value})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="residency-violations")
    async def residency_violations(self, ctx, framework: str = None):
        violations = self.enforcer.get_violations(framework)
        if not violations:
            await ctx.send("No violations found")
            return
        embed = discord.Embed(title=f"Residency Violations ({len(violations)})", color=discord.Color.red())
        for v in violations[:10]:
            embed.add_field(name=v["name"], value=f"{v['current_region']} - {v['classification']}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="residency-compliance-report")
    async def residency_compliance_report(self, ctx, framework: str):
        report = self.enforcer.get_compliance_report(framework)
        if "error" in report:
            await ctx.send(f"Error: {report['error']}")
            return
        embed = discord.Embed(title=f"Residency Report: {framework}", color=discord.Color.blue())
        embed.add_field(name="Assets in Scope", value=str(report["assets_in_scope"]), inline=True)
        embed.add_field(name="Compliant", value=str(report["compliant"]), inline=True)
        embed.add_field(name="Violations", value=str(report["violations"]), inline=True)
        embed.add_field(name="Cross-Border Flows", value=str(report["cross_border_flows"]), inline=True)
        embed.add_field(name="Blocked Flows", value=str(report["blocked_flows"]), inline=True)
        embed.add_field(name="Requires SCC", value=str(report["requires_scc"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="residency-asset-search")
    async def residency_asset_search(self, ctx, *, query: str):
        results = self.enforcer.search_assets(query)
        if not results:
            await ctx.send(f"No assets found for '{query}'")
            return
        embed = discord.Embed(title=f"Asset Search ({len(results)})", color=discord.Color.blue())
        for a in results[:10]:
            embed.add_field(name=a.name, value=f"{a.asset_type} - {a.current_region.value} ({a.classification.value})", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DataResidencyCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class data_residency_CogExtension:
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

async def setup_data_residency_handlers(bot):
    @bot.command(name="data_residency")
    async def data_residency_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"data_residency {action} command received")
        if action == "status":
            await ctx.send("data_residency Cog: Active")
        elif action == "list":
            await ctx.send("data_residency listing not yet implemented")

def register_data_residency_routes(bot):
    @bot.command(name="data_residency_help")
    async def data_residency_help(ctx):
        await ctx.send("data_residency Commands: status, list, report")


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
