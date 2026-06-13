import discord
from discord.ext import commands
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.compliance_as_code import ComplianceAsCodeEngine

class ComplianceAsCodeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = ComplianceAsCodeEngine(config={"compliance_code_data_file": "data/compliance_as_code.json"})

    @commands.command(name="cac-list")
    @commands.has_permissions(administrator=True)
    async def cac_list(self, ctx, framework: str = None):
        controls = self.engine.get_controls(framework=framework)
        if not controls:
            await ctx.send("No controls found")
            return
        embed = discord.Embed(title=f"Compliance Controls ({len(controls)})", color=discord.Color.blue())
        for c in controls[:10]:
            embed.add_field(name=c.control_id, value=f"{c.name} - {c.status.value} ({c.severity.value})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="cac-evaluate")
    @commands.has_permissions(administrator=True)
    async def cac_evaluate(self, ctx, control_id: str, input_json: str):
        try:
            input_data = json.loads(input_json)
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON input")
            return
        result = self.engine.evaluate(control_id, input_data)
        embed = discord.Embed(title=f"Evaluation: {control_id}", color=discord.Color.green() if result["status"] == "compliant" else discord.Color.red())
        embed.add_field(name="Status", value=result["status"], inline=True)
        embed.add_field(name="Violations", value=str(result["violation_count"]), inline=True)
        if result["violations"]:
            for v in result["violations"][:3]:
                embed.add_field(name=f"Violation: {v['rule_name']}", value=v["message"], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="cac-templates")
    async def cac_templates(self, ctx):
        templates = self.engine.get_policy_templates()
        embed = discord.Embed(title="Policy Templates", color=discord.Color.blue())
        for name in templates:
            embed.add_field(name=name, value=f"REGO template ({len(templates[name])} chars)", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="cac-stats")
    async def cac_stats(self, ctx):
        stats = self.engine.get_statistics()
        embed = discord.Embed(title="Compliance-as-Code Stats", color=discord.Color.blue())
        for k, v in stats.items():
            if isinstance(v, dict):
                continue
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="cac-create")
    @commands.has_permissions(administrator=True)
    async def cac_create(self, ctx, framework: str, name: str, severity: str, category: str, *, description: str):
        control = self.engine.create_control(framework=framework, name=name, description=description,
                                              category=category, severity=severity,
                                              rego_expression=f"package custom.{framework}\ndefault allow = true")
        embed = discord.Embed(title="Control Created", color=discord.Color.green())
        embed.add_field(name="Control ID", value=control.control_id, inline=True)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Status", value=control.status.value, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="cac-gap")
    async def cac_gap(self, ctx, framework: str):
        gap = self.engine.gap_analysis(framework)
        embed = discord.Embed(title=f"Gap Analysis: {framework}", color=discord.Color.orange())
        embed.add_field(name="Total Controls", value=str(gap["total_controls"]), inline=True)
        embed.add_field(name="Active", value=str(gap["active"]), inline=True)
        embed.add_field(name="Coverage", value=f"{gap['policy_coverage']}%", inline=True)
        if gap["missing_policies"]:
            embed.add_field(name="Missing", value=", ".join(gap["missing_policies"][:5]), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="cac-test")
    @commands.has_permissions(administrator=True)
    async def cac_test(self, ctx, control_id: str, input_json: str):
        try:
            import json
            input_data = json.loads(input_json)
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON input")
            return
        result = self.engine.evaluate(control_id, input_data)
        embed = discord.Embed(title=f"Policy Test: {control_id}", color=discord.Color.green() if result["status"] == "compliant" else discord.Color.red())
        embed.add_field(name="Status", value=result["status"], inline=True)
        embed.add_field(name="Violations", value=str(result["violation_count"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="cac-dry-run")
    @commands.has_permissions(administrator=True)
    async def cac_dry_run(self, ctx, template_name: str, input_json: str):
        try:
            import json
            input_data = json.loads(input_json)
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON input")
            return
        template = self.engine.get_policy_templates().get(template_name)
        if not template:
            await ctx.send(f"Template {template_name} not found")
            return
        result = self.engine.dry_run_policy(template, input_data)
        embed = discord.Embed(title=f"Dry Run: {template_name}", color=discord.Color.blue())
        embed.add_field(name="Result", value=result["result"], inline=True)
        embed.add_field(name="Triggers", value=str(result["trigger_count"]), inline=True)
        for t in result["triggers"][:5]:
            embed.add_field(name=t["rule"], value=t["reason"], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="cac-version")
    @commands.has_permissions(administrator=True)
    async def cac_version(self, ctx, control_id: str, *, rego_expression: str):
        result = self.engine.create_policy_version(control_id=control_id, rego_expression=rego_expression)
        embed = discord.Embed(title="Policy Version Created", color=discord.Color.green())
        embed.add_field(name="Version ID", value=result["version_id"], inline=True)
        embed.add_field(name="New Version", value=result["new_version"], inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ComplianceAsCodeCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class compliance_as_code_CogExtension:
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

async def setup_compliance_as_code_handlers(bot):
    @bot.command(name="compliance_as_code")
    async def compliance_as_code_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"compliance_as_code {action} command received")
        if action == "status":
            await ctx.send("compliance_as_code Cog: Active")
        elif action == "list":
            await ctx.send("compliance_as_code listing not yet implemented")

def register_compliance_as_code_routes(bot):
    @bot.command(name="compliance_as_code_help")
    async def compliance_as_code_help(ctx):
        await ctx.send("compliance_as_code Commands: status, list, report")


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
