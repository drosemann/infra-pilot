import discord
from discord.ext import commands
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'integration-service', 'src'))
from compliance_v4.continuous_compliance import ContinuousComplianceMonitor

class ContinuousComplianceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitor = ContinuousComplianceMonitor(config={"compliance_data_file": "data/continuous_compliance.json"})

    @commands.command(name="compliance-status")
    @commands.has_permissions(administrator=True)
    async def compliance_status(self, ctx, framework: str = None):
        summary = self.monitor.get_summary()
        if framework:
            posture = self.monitor.get_posture(framework)
            if not posture:
                await ctx.send(f"Framework {framework} not found. Available: {', '.join(self.monitor.frameworks.keys())}")
                return
            embed = discord.Embed(title=f"{framework} Posture", color=discord.Color.green() if posture.status == "compliant" else discord.Color.red())
            embed.add_field(name="Score", value=f"{posture.overall_score:.1f}%", inline=True)
            embed.add_field(name="Status", value=posture.status, inline=True)
            embed.add_field(name="Controls", value=f"{posture.passed}/{posture.control_count} passed", inline=True)
            embed.add_field(name="Failed", value=str(posture.failed), inline=True)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Compliance Summary", color=discord.Color.blue())
            embed.add_field(name="Frameworks Assessed", value=str(summary["frameworks_assessed"]), inline=True)
            embed.add_field(name="Compliant", value=str(summary["compliant_frameworks"]), inline=True)
            embed.add_field(name="Overall Rate", value=f"{summary['overall_compliance_rate']}%", inline=True)
            embed.add_field(name="Total Controls", value=str(summary["total_controls"]), inline=True)
            embed.add_field(name="Passed", value=str(summary["total_passed"]), inline=True)
            embed.add_field(name="Failed", value=str(summary["total_failed"]), inline=True)
            await ctx.send(embed=embed)

    @commands.command(name="compliance-scan")
    @commands.has_permissions(administrator=True)
    async def compliance_scan(self, ctx, framework: str = None):
        await ctx.send(f"Scanning compliance posture...")
        if framework:
            self.monitor.assess_framework(framework.upper())
            await ctx.send(f"Scan complete for {framework.upper()}")
        else:
            self.monitor.assess_all_frameworks()
            await ctx.send("Scan complete for all frameworks")

    @commands.command(name="compliance-alerts")
    @commands.has_permissions(administrator=True)
    async def compliance_alerts(self, ctx):
        alerts = self.monitor.get_alerts()
        if not alerts:
            await ctx.send("No compliance alerts")
            return
        embed = discord.Embed(title=f"Compliance Alerts ({len(alerts)})", color=discord.Color.red())
        for a in alerts[:10]:
            embed.add_field(name=f"{a['severity'].upper()}: {a.get('framework', a.get('control_id', 'N/A'))}", value=a["message"], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-frameworks")
    async def compliance_frameworks(self, ctx):
        frameworks = list(self.monitor.frameworks.keys())
        embed = discord.Embed(title="Supported Frameworks", color=discord.Color.blue())
        for fw in frameworks:
            fw_def = self.monitor.frameworks[fw]
            embed.add_field(name=fw, value=f"v{fw_def['version']} - {len(fw_def['controls'])} controls", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-trend")
    @commands.has_permissions(administrator=True)
    async def compliance_trend(self, ctx, framework: str, days: int = 30):
        trend = self.monitor.get_trend(framework.upper(), days)
        if not trend:
            await ctx.send(f"No trend data for {framework}")
            return
        scores = [t["score"] for t in trend]
        avg = sum(scores) / len(scores)
        embed = discord.Embed(title=f"{framework} Trend ({days}d)", color=discord.Color.blue())
        embed.add_field(name="Data Points", value=str(len(trend)), inline=True)
        embed.add_field(name="Average Score", value=f"{avg:.1f}%", inline=True)
        embed.add_field(name="Latest Score", value=f"{trend[0]['score']:.1f}%", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-remediate")
    @commands.has_permissions(administrator=True)
    async def compliance_remediate(self, ctx, framework: str, control_id: str):
        result = self.monitor.bulk_remediate([control_id], framework.upper())
        if control_id in result and "error" in result[control_id]:
            await ctx.send(f"Error: {result[control_id]['error']}")
            return
        embed = discord.Embed(title="Control Remediated", color=discord.Color.green())
        embed.add_field(name="Framework", value=framework.upper(), inline=True)
        embed.add_field(name="Control", value=control_id, inline=True)
        embed.add_field(name="Status", value=result.get(control_id, {}).get("status", "remediated"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-drift")
    @commands.has_permissions(administrator=True)
    async def compliance_drift(self, ctx, framework: str):
        drift = self.monitor.detect_drift(framework.upper())
        if not drift:
            await ctx.send(f"No drift detected for {framework.upper()}")
            return
        embed = discord.Embed(title=f"Drift Detected: {framework.upper()} ({len(drift)})", color=discord.Color.orange())
        for d in drift[:10]:
            emoji = "📈" if d["drift_type"] == "improvement" else "📉"
            embed.add_field(name=f"{emoji} {d['control_id']}", value=f"{d['previous_score']:.2f} -> {d['current_score']:.2f} ({d['drift_type']})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-compare")
    async def compliance_compare(self, ctx):
        comparison = self.monitor.compare_frameworks()
        embed = discord.Embed(title="Framework Comparison", color=discord.Color.blue())
        embed.add_field(name="Highest", value=str(comparison.get("highest", "N/A")), inline=True)
        embed.add_field(name="Lowest", value=str(comparison.get("lowest", "N/A")), inline=True)
        embed.add_field(name="Average", value=f"{comparison.get('average', 0):.1f}%", inline=True)
        embed.add_field(name="Variance", value=f"{comparison.get('variance', 0):.1f}%", inline=True)
        for fw, score in comparison.get("comparison", {}).items():
            embed.add_field(name=fw, value=f"{score:.1f}%", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-report")
    @commands.has_permissions(administrator=True)
    async def compliance_report(self, ctx, framework: str):
        report = self.monitor.generate_report(framework.upper())
        if "error" in report:
            await ctx.send(f"Error: {report['error']}")
            return
        embed = discord.Embed(title=f"Compliance Report: {framework.upper()}", color=discord.Color.blue())
        embed.add_field(name="Score", value=f"{report['overall_score']:.1f}%", inline=True)
        embed.add_field(name="Status", value=report["status"], inline=True)
        embed.add_field(name="Controls", value=f"{report['control_summary']['passed']}/{report['control_summary']['total']} passed", inline=True)
        embed.add_field(name="Failed", value=str(report['control_summary']['failed']), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-schedule")
    @commands.has_permissions(administrator=True)
    async def compliance_schedule(self, ctx, interval_minutes: int = 60):
        schedule = self.monitor.schedule_scans(interval_minutes)
        embed = discord.Embed(title="Scan Schedule Set", color=discord.Color.green())
        embed.add_field(name="Interval", value=f"{interval_minutes} min", inline=True)
        embed.add_field(name="Status", value=schedule["status"], inline=True)
        embed.add_field(name="Next Scan", value=schedule["next_scan"][:19], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="compliance-weakest")
    async def compliance_weakest(self, ctx, framework: str, limit: int = 5):
        weakest = self.monitor.find_weakest_controls(framework.upper(), limit)
        if not weakest:
            await ctx.send(f"No failed controls for {framework.upper()}")
            return
        embed = discord.Embed(title=f"Weakest Controls: {framework.upper()}", color=discord.Color.red())
        for c in weakest:
            embed.add_field(name=c.control_id, value=f"Score: {c.score:.2f} - {c.title}", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ContinuousComplianceCog(bot))

import uuid, json
from datetime import datetime
from typing import List, Dict, Any, Optional

class continuous_compliance_CogExtension:
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

async def setup_continuous_compliance_handlers(bot):
    @bot.command(name="continuous_compliance")
    async def continuous_compliance_cmd(ctx, action: str = "status", *args):
        await ctx.send(f"continuous_compliance {action} command received")
        if action == "status":
            await ctx.send("continuous_compliance Cog: Active")
        elif action == "list":
            await ctx.send("continuous_compliance listing not yet implemented")

def register_continuous_compliance_routes(bot):
    @bot.command(name="continuous_compliance_help")
    async def continuous_compliance_help(ctx):
        await ctx.send("continuous_compliance Commands: status, list, report")


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
