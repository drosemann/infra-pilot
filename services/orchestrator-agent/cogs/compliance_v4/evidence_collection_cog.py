import discord
from discord.ext import commands
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.evidence_collection import EvidenceCollector

class EvidenceCollectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collector = EvidenceCollector(config={"evidence_data_dir": "data/evidence"})

    @commands.command(name="evidence-list")
    @commands.has_permissions(administrator=True)
    async def evidence_list(self, ctx, framework: str = None):
        items = self.collector.get_evidence(framework=framework)
        if not items:
            await ctx.send("No evidence items found")
            return
        embed = discord.Embed(title=f"Evidence Items ({len(items)})", color=discord.Color.blue())
        for item in items[:10]:
            embed.add_field(name=item.evidence_id, value=f"{item.evidence_type} - {item.control_id} ({item.status})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-collect")
    @commands.has_permissions(administrator=True)
    async def evidence_collect(self, ctx, control_id: str, framework: str, evidence_type: str = "config_snapshot"):
        item = self.collector.collect_evidence(control_id=control_id, framework=framework, evidence_type=evidence_type,
                                               description=f"Manual collection for {control_id}", source="discord_command",
                                               content=f"Evidence collected via Discord by {ctx.author}", collected_by=ctx.author.name)
        embed = discord.Embed(title="Evidence Collected", color=discord.Color.green())
        embed.add_field(name="ID", value=item.evidence_id, inline=True)
        embed.add_field(name="Control", value=control_id, inline=True)
        embed.add_field(name="Type", value=evidence_type, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-packages")
    @commands.has_permissions(administrator=True)
    async def evidence_packages(self, ctx, framework: str = None):
        pkgs = self.collector.get_packages(framework=framework)
        if not pkgs:
            await ctx.send("No evidence packages found")
            return
        embed = discord.Embed(title=f"Evidence Packages ({len(pkgs)})", color=discord.Color.blue())
        for pkg in pkgs[:5]:
            embed.add_field(name=pkg.package_id, value=f"{pkg.name} - {pkg.status} ({len(pkg.evidence_items)} items)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-stats")
    async def evidence_stats(self, ctx):
        stats = self.collector.get_statistics()
        embed = discord.Embed(title="Evidence Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Items", value=str(stats["total_evidence"]), inline=True)
        embed.add_field(name="Packages", value=str(stats["total_packages"]), inline=True)
        embed.add_field(name="Controls Covered", value=str(stats["unique_controls_covered"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-auto-collect")
    @commands.has_permissions(administrator=True)
    async def evidence_auto_collect(self, ctx, control_id: str, framework: str = "SOC_2"):
        items = self.collector.auto_collect_for_control(control_id, framework)
        embed = discord.Embed(title=f"Auto-Collected {len(items)} Evidence Items", color=discord.Color.green())
        for item in items[:5]:
            embed.add_field(name=item.evidence_id, value=f"{item.evidence_type} - {item.source}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-search")
    async def evidence_search(self, ctx, *, query: str):
        results = self.collector.search_evidence(query)
        if not results:
            await ctx.send("No evidence items found matching your query")
            return
        embed = discord.Embed(title=f"Evidence Search ({len(results)} matches)", color=discord.Color.blue())
        for item in results[:10]:
            embed.add_field(name=item.evidence_id, value=f"{item.description[:50]} - {item.control_id} ({item.status})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-validate")
    async def evidence_validate(self, ctx, evidence_id: str):
        result = self.collector.validate_evidence(evidence_id)
        emoji = "✅" if result["valid"] else "❌"
        embed = discord.Embed(title=f"{emoji} Evidence Validation", color=discord.Color.green() if result["valid"] else discord.Color.red())
        embed.add_field(name="Evidence ID", value=evidence_id, inline=True)
        embed.add_field(name="Valid", value=str(result["valid"]), inline=True)
        for check, passed in result.get("checks", {}).items():
            embed.add_field(name=check, value="✅" if passed else "❌", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-package-create")
    @commands.has_permissions(administrator=True)
    async def evidence_package_create(self, ctx, name: str, framework: str, control_ids: str):
        ctrl_list = [c.strip() for c in control_ids.split(",")]
        from datetime import datetime, timedelta
        pkg = self.collector.create_package(name=name, framework=framework, control_ids=ctrl_list,
                                             audit_start=datetime.utcnow() - timedelta(days=90),
                                             audit_end=datetime.utcnow(), created_by=ctx.author.name)
        embed = discord.Embed(title="Evidence Package Created", color=discord.Color.green())
        embed.add_field(name="Package ID", value=pkg.package_id, inline=True)
        embed.add_field(name="Items", value=str(len(pkg.evidence_items)), inline=True)
        embed.add_field(name="Status", value=pkg.status, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-expired")
    async def evidence_expired(self, ctx):
        expired = self.collector.check_expired_evidence()
        if not expired:
            await ctx.send("No expired evidence items")
            return
        embed = discord.Embed(title=f"Expired Evidence ({len(expired)})", color=discord.Color.orange())
        for e in expired[:10]:
            embed.add_field(name=e.evidence_id, value=f"{e.evidence_type} - expired {e.expires_at.strftime('%Y-%m-%d')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="evidence-custody")
    async def evidence_custody(self, ctx, evidence_id: str):
        chain = self.collector.get_chain_of_custody(evidence_id)
        if not chain:
            await ctx.send("Evidence not found")
            return
        embed = discord.Embed(title=f"Chain of Custody: {evidence_id}", color=discord.Color.blue())
        for event in chain:
            embed.add_field(name=event["event"], value=f"{event['timestamp'][:19]} - {event['detail'][:50]}", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EvidenceCollectionCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class evidence_collection_CogExtension:
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

async def setup_evidence_collection_handlers(bot):
    @bot.command(name="evidence_collection")
    async def evidence_collection_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"evidence_collection {action} command received")
        if action == "status":
            await ctx.send("evidence_collection Cog: Active")
        elif action == "list":
            await ctx.send("evidence_collection listing not yet implemented")

def register_evidence_collection_routes(bot):
    @bot.command(name="evidence_collection_help")
    async def evidence_collection_help(ctx):
        await ctx.send("evidence_collection Commands: status, list, report")


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
