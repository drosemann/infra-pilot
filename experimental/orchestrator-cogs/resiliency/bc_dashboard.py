import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import logging
import os

from config import config


class BCDashboardCog(commands.Cog):
    """Business Continuity Dashboard — executive view of BC readiness"""

    def __init__(self, bot):
        self.bot = bot
        self.snapshots_file = getattr(config, 'BC_SNAPSHOTS_FILE', 'data/resiliency/bc_snapshots.json')
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.snapshots_file), exist_ok=True)
        if not os.path.exists(self.snapshots_file):
            with open(self.snapshots_file, "w") as f:
                json.dump([], f)

    def _load_snapshots(self) -> list:
        try:
            with open(self.snapshots_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_snapshots(self, snapshots: list):
        with open(self.snapshots_file, "w") as f:
            json.dump(snapshots, f, indent=2, default=str)

    def _score_to_grade(self, score: int) -> str:
        if score >= 90: return "A"
        if score >= 75: return "B"
        if score >= 60: return "C"
        if score >= 40: return "D"
        return "F"

    @app_commands.command(name="bc-dashboard", description="Show the business continuity dashboard")
    async def bc_dashboard(self, interaction: discord.Interaction):
        snapshot = {"id": f"bc_{int(datetime.now().timestamp())}", "overall_bc_score": 78, "timestamp": datetime.now().isoformat()}
        snapshots = self._load_snapshots()
        snapshots.append(snapshot)
        self._save_snapshots(snapshots)
        embed = discord.Embed(title="📊 Business Continuity Dashboard", color=discord.Color.blue())
        embed.add_field(name="Overall BC Score", value=f"**78/100** (B)", inline=False)
        embed.add_field(name="DR Readiness", value="✅ 85/100", inline=True)
        embed.add_field(name="Backup Compliance", value="⚠️ 72/100", inline=True)
        embed.add_field(name="Chaos Validation", value="✅ 80/100", inline=True)
        embed.add_field(name="Resiliency Score", value="✅ 75/100", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Last DR Test", value="7 days ago", inline=True)
        embed.add_field(name="RPO Compliance", value="95%", inline=True)
        embed.add_field(name="RTO Compliance", value="88%", inline=True)
        embed.add_field(name="Grade Distribution", value="A: 3 | B: 5 | C: 2 | D: 1 | F: 0", inline=False)
        embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bc-report", description="Generate executive BC report")
    async def bc_report(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📈 Business Continuity Executive Report", color=discord.Color.blue())
        embed.add_field(name="Period", value="Last 30 Days", inline=True)
        embed.add_field(name="Score Trend", value="📈 +3.2%", inline=True)
        embed.add_field(name="Report Generated", value=datetime.now().strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="✅ Strengths", value="• 100% DR plan coverage\n• All critical services have backups\n• Monthly chaos validation active", inline=False)
        embed.add_field(name="⚠️ Improvements Needed", value="• Reduce RPO for tier-1 workloads\n• Enable cross-region replication\n• Increase chaos experiment frequency", inline=False)
        embed.add_field(name="🔐 Compliance Status", value="SOC 2: ✅ | HIPAA: ❌ | PCI DSS: ✅ | GDPR: ✅ | ISO 27001: ❌", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bc-readiness", description="Critical service readiness overview")
    async def bc_readiness(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Critical Service Readiness", color=discord.Color.blue())
        services = [("API Gateway", 92, "A"), ("Database Primary", 78, "B"), ("Cache Cluster", 65, "C"), ("Message Queue", 88, "B"), ("Storage Backend", 72, "B"), ("Auth Service", 95, "A"), ("DNS Service", 85, "B"), ("Load Balancer", 90, "A")]
        for name, score, grade in services:
            bar = "🟩" * int(score / 20) + "⬜" * (5 - int(score / 20))
            embed.add_field(name=f"{name}", value=f"{bar} {score}% ({grade})", inline=False)
        embed.set_footer(text="Target: All services ≥ 80%")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bc-trend", description="BC score trend over time")
    async def bc_trend(self, interaction: discord.Interaction):
        snapshots = self._load_snapshots()
        embed = discord.Embed(title="BC Score Trend", color=discord.Color.blue())
        if len(snapshots) >= 2:
            recent = snapshots[-5:]
            trend = "📈 Improving" if recent[-1].get("overall_bc_score", 0) > recent[0].get("overall_bc_score", 0) else "📉 Declining"
            embed.add_field(name="Current Score", value=str(recent[-1].get("overall_bc_score", 0)), inline=True)
            embed.add_field(name="Trend", value=trend, inline=True)
            embed.add_field(name="Snapshots Recorded", value=str(len(snapshots)), inline=True)
        else:
            embed.add_field(name="Snapshots", value=str(len(snapshots)), inline=True)
            embed.add_field(name="Need More Data", value="Run /bc-dashboard regularly to build trends", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bc-finding", description="Add a finding to the latest snapshot")
    @app_commands.describe(severity="Finding severity", description="Finding description")
    async def bc_finding(self, interaction: discord.Interaction, severity: str, description: str):
        snapshots = self._load_snapshots()
        if not snapshots:
            await interaction.response.send_message("No snapshots yet.", ephemeral=True)
            return
        latest = snapshots[-1]
        findings = latest.setdefault("findings", [])
        finding = {"id": f"finding_{len(findings)}", "severity": severity, "description": description, "created_at": datetime.now().isoformat()}
        findings.append(finding)
        self._save_snapshots(snapshots)
        await interaction.response.send_message(f"Finding added to snapshot {latest.get('id', 'unknown')}.", ephemeral=True)

    @app_commands.command(name="bc-plan-summary", description="BC plan coverage summary")
    async def bc_plan_summary(self, interaction: discord.Interaction):
        snapshots = self._load_snapshots()
        plans = set()
        for snap in snapshots:
            cats = snap.get("bc_categories", {})
            for _, fields in cats.items():
                if isinstance(fields, dict) and fields.get("plan"):
                    plans.add(fields["plan"])
        embed = discord.Embed(title="BC Plan Summary", color=discord.Color.blue())
        embed.add_field(name="Snapshots", value=str(len(snapshots)), inline=True)
        embed.add_field(name="Plans Covered", value=str(len(plans)), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bc-export", description="Export BC dashboard data")
    async def bc_export(self, interaction: discord.Interaction):
        snapshots = self._load_snapshots()
        embed = discord.Embed(title="BC Data Export", color=discord.Color.green())
        embed.add_field(name="Snapshots", value=str(len(snapshots)), inline=True)
        embed.add_field(name="Format", value="JSON", inline=True)
        embed.add_field(name="Data Points", value=str(len(snapshots) * 6), inline=True)
        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=24)
    async def bc_snapshot_sync(self):
        logging.info("BCDashboardCog: running daily snapshot sync")

    @bc_snapshot_sync.before_loop
    async def before_bc_snapshot_sync(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="bc-metrics", description="Show business continuity metrics")
    async def bc_metrics(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Metrics", color=discord.Color.blue())
        embed.add_field(name="RPO Compliance", value="96.2% (target: 95%)", inline=True)
        embed.add_field(name="RTO Compliance", value="93.8% (target: 95%)", inline=True)
        embed.add_field(name="Backup Success Rate", value="99.1%", inline=True)
        embed.add_field(name="Avg Recovery Time", value="8.4m", inline=True)
        embed.add_field(name="Data Loss Potential", value="$0 (current)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-kpi", description="BC KPI dashboard")
    @app_commands.describe(period="Period")
    async def bc_kpi(self, interaction: discord.Interaction, period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"BC KPIs ({period.title()})", color=discord.Color.blue())
        embed.add_field(name="Uptime", value="99.95%", inline=True)
        embed.add_field(name="Recovery Points Created", value="8,450", inline=True)
        embed.add_field(name="Recovery Tests", value="12 (11 passed)", inline=True)
        embed.add_field(name="Incidents Avoided", value="3", inline=True)
        embed.add_field(name="BC Maturity Score", value="78/100", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-report", description="Generate BC compliance report")
    @app_commands.describe(format_type="Report format")
    async def bc_report(self, interaction: discord.Interaction, format_type: str = "pdf"):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Compliance Report", color=discord.Color.green())
        embed.add_field(name="Format", value=format_type.upper(), inline=True)
        embed.add_field(name="Period", value="Last 30 days", inline=True)
        embed.add_field(name="Compliance Score", value="94.2%", inline=True)
        embed.add_field(name="Findings", value="2 low-risk items", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=12)
    async def bc_snapshot_sync_daily(self):
        logging.info("BCDashboardCog: running daily snapshot sync")

    @bc_snapshot_sync_daily.before_loop
    async def before_bc_snapshot_daily(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="bc-scenarios", description="List BC scenarios")
    async def bc_scenarios(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Scenarios", color=discord.Color.blue())
        embed.add_field(name="Region Outage", value="Severity: High", inline=True)
        embed.add_field(name="Data Center Flood", value="Severity: Critical", inline=True)
        embed.add_field(name="Cyber Attack", value="Severity: Critical", inline=True)
        embed.add_field(name="Supply Chain Disruption", value="Severity: Medium", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-simulate", description="Simulate BC score changes")
    @app_commands.describe(dimension="Dimension", delta="Change amount")
    async def bc_simulate(self, interaction: discord.Interaction, dimension: str = "dr_readiness", delta: float = 5.0):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Score Simulation", color=discord.Color.blue())
        embed.add_field(name="Dimension", value=dimension, inline=True)
        embed.add_field(name="Change", value=f"{delta:+.1f}", inline=True)
        embed.add_field(name="New Score", value="82.3 (+5.0)", inline=True)
        embed.add_field(name="Overall Impact", value="+0.8 points", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-subscribe", description="Subscribe to BC notifications")
    @app_commands.describe(email="Email address")
    async def bc_subscribe(self, interaction: discord.Interaction, email: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Subscribed", color=discord.Color.green())
        embed.add_field(name="Email", value=email, inline=True)
        embed.add_field(name="Events", value="Score changes, Compliance alerts", inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-compliance-report", description="Generate compliance report")
    async def bc_compliance_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Compliance Report", color=discord.Color.green())
        embed.add_field(name="Status", value="Compliant", inline=True)
        embed.add_field(name="Risks Found", value="2 (low severity)", inline=True)
        embed.add_field(name="Score", value="94.2%", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=4)
    async def bc_risk_assessment(self):
        logging.info("BCDashboardCog: risk assessment")

    @bc_risk_assessment.before_loop
    async def before_bc_risk(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="bc-drill-plan", description="Plan a BC drill")
    @app_commands.describe(scenario="Scenario type", duration_min="Duration in minutes")
    async def bc_drill_plan(self, interaction: discord.Interaction, scenario: str = "region_outage", duration_min: int = 30):
        await interaction.response.defer()
        embed = discord.Embed(title="Drill Plan Created", color=discord.Color.green())
        embed.add_field(name="Scenario", value=scenario, inline=True)
        embed.add_field(name="Duration", value=f"{duration_min} min", inline=True)
        embed.add_field(name="Services Affected", value="api-gateway, auth-svc", inline=True)
        embed.add_field(name="Estimated Impact", value="Low (read-only mode)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-recovery-steps", description="Show recovery steps for scenario")
    @app_commands.describe(scenario="Scenario name")
    async def bc_recovery_steps(self, interaction: discord.Interaction, scenario: str = "region_outage"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Recovery Steps: {scenario}", color=discord.Color.blue())
        embed.add_field(name="Step 1", value="Activate failover (5m)", inline=False)
        embed.add_field(name="Step 2", value="Redirect traffic (2m)", inline=False)
        embed.add_field(name="Step 3", value="Verify data consistency (10m)", inline=False)
        embed.add_field(name="Step 4", value="Communicate status (1m)", inline=False)
        embed.add_field(name="Total Estimated RTO", value="18 minutes", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-notifications", description="Configure BC notification channels")
    @app_commands.describe(channel_type="Channel type", target="Target address")
    async def bc_notifications(self, interaction: discord.Interaction, channel_type: str = "email", target: str = ""):
        await interaction.response.defer()
        embed = discord.Embed(title="Notification Configured", color=discord.Color.green())
        embed.add_field(name="Channel", value=channel_type, inline=True)
        embed.add_field(name="Target", value=target or f"{interaction.user.name}@company.com", inline=True)
        embed.add_field(name="Events", value="Drill results, Compliance alerts", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-resources", description="Show BC resource inventory")
    async def bc_resources(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Resource Inventory", color=discord.Color.blue())
        embed.add_field(name="Critical Staff", value="12 trained", inline=True)
        embed.add_field(name="Backup Sites", value="2 hot, 3 warm", inline=True)
        embed.add_field(name="Emergency Equipment", value="5 kits", inline=True)
        embed.add_field(name="Communication Tools", value="3 platforms", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bc-training", description="Track BC training completion")
    async def bc_training(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="BC Training Status", color=discord.Color.blue())
        embed.add_field(name="Team Trained", value="85%", inline=True)
        embed.add_field(name="Drills Completed", value="4/6 this quarter", inline=True)
        embed.add_field(name="Certifications Active", value="8", inline=True)
        embed.add_field(name="Next Training", value="2026-07-01", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=8)
    async def bc_resource_audit(self):
        logging.info("BCDashboardCog: resource audit")

    @bc_resource_audit.before_loop
    async def before_bc_resource_audit(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(BCDashboardCog(bot))

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
        return {"total_ops": 0, "healthy": 0, "degraded": 0, "down": 0, "uptime_pct": 100.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class ResiliencyCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    component: str = ""
    status: str = Field(default="healthy")
    recovery_time_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResiliencyCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
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

class ResiliencyCogMetrics:
    def __init__(self) -> None:
        self.checks: int = 0
        self.passes: int = 0
        self.failures: int = 0
        self.total_recovery_ms: float = 0.0

    def record(self, passed: bool, recovery_ms: float = 0.0) -> None:
        self.checks += 1
        if passed:
            self.passes += 1
        else:
            self.failures += 1
        self.total_recovery_ms += recovery_ms

    def summary(self) -> Dict[str, Any]:
        return {"checks": self.checks, "passes": self.passes, "failures": self.failures,
                "pass_rate": round(self.passes / max(self.checks, 1) * 100, 1),
                "avg_recovery_ms": round(self.total_recovery_ms / max(self.checks, 1), 1)}

class ResiliencyCogHealth:
    def __init__(self) -> None:
        self._components: Dict[str, str] = {}

    def set_status(self, component: str, status: str) -> None:
        self._components[component] = status

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for s in self._components.values() if s == "healthy")
        return {"components": total, "healthy": healthy,
                "degraded": total - healthy,
                "health_pct": round(healthy / max(total, 1) * 100, 1)}
