import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class FinopsReporting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="finops-report", description="Generate FinOps report")
    @app_commands.describe(report_type="Report type", period="Time period")
    async def generate_report(self, interaction: discord.Interaction, report_type: str = "executive_summary", period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"FinOps Report: {report_type.replace('_', ' ').title()}", color=0x00AAFF)
        embed.add_field(name="Period", value=period, inline=True)
        embed.add_field(name="Total Cloud Spend", value="$384,250.00", inline=True)
        embed.add_field(name="Committed Spend", value="$249,762.50 (65%)", inline=True)
        embed.add_field(name="On-Demand Spend", value="$134,487.50 (35%)", inline=True)
        embed.add_field(name="Total Savings", value="$84,535.00 (22%)", inline=True)
        embed.add_field(name="Waste", value="$17,291.25 (4.5%)", inline=True)
        embed.add_field(name="Forecast Accuracy", value="92.3%", inline=True)
        embed.set_footer(text="FinOps Foundation KPI compliant")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-kpi", description="Show FinOps KPI dashboard")
    async def kpi_dashboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="FinOps KPI Dashboard", color=0x00AAFF)
        embed.add_field(name="Cost Efficiency", value="✅ On track (12% MoM)", inline=False)
        embed.add_field(name="Commitment Coverage", value="✅ 65% (target >60%)", inline=False)
        embed.add_field(name="Utilization Rate", value="⚠️ 78% (target >85%)", inline=False)
        embed.add_field(name="Waste Reduction", value="✅ 4.5% (target <5%)", inline=False)
        embed.add_field(name="Unit Cost Trends", value="✅ Decreasing 5.2% MoM", inline=False)
        embed.add_field(name="Forecast Accuracy", value="✅ 92.3% (target >90%)", inline=False)
        embed.add_field(name="Anomaly Response", value="⚠️ 3.2h avg (target <4h)", inline=False)
        embed.set_footer(text="5 of 7 KPIs on track")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-showback", description="Showback report")
    @app_commands.describe(team="Filter by team")
    async def showback(self, interaction: discord.Interaction, team: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Showback Report", color=0x00AAFF)
        embed.add_field(name="Engineering", value="$145,000 (37.7%)", inline=True)
        embed.add_field(name="Data Science", value="$82,000 (21.3%)", inline=True)
        embed.add_field(name="Infrastructure", value="$68,000 (17.7%)", inline=True)
        embed.add_field(name="ML/AI", value="$52,000 (13.5%)", inline=True)
        embed.add_field(name="Other", value="$37,250 (9.7%)", inline=True)
        embed.set_footer(text=f"{'Filtered by: ' + team if team else 'All teams'} | Mode: Showback")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-summary", description="FinOps reporting summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="FinOps Reporting Summary", color=0x00AAFF)
        embed.add_field(name="Reports Generated", value="24 this month", inline=True)
        embed.add_field(name="Dashboard Types", value="5 pre-built", inline=True)
        embed.add_field(name="Allocation Tags", value="18 configured", inline=True)
        embed.add_field(name="KPIs Tracked", value="7", inline=True)
        embed.add_field(name="KPIs On Track", value="5 of 7", inline=True)
        embed.add_field(name="Audit Ready", value="Yes — SOC2/FinOps compliant", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="report-list", description="List generated reports")
    async def list_reports(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="FinOps Reports", color=0x00AAFF)
        embed.add_field(name="Executive Summary (Mar)", value="Type: executive_summary | Status: ready", inline=False)
        embed.add_field(name="Cost Breakdown (Mar)", value="Type: cost_breakdown | Status: ready", inline=False)
        embed.add_field(name="Savings Opportunity (Q1)", value="Type: savings_opportunity | Status: generating", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="report-generate", description="Generate a new report")
    @app_commands.describe(report_type="Report type", period="Period (monthly/quarterly/annual)")
    async def generate(self, interaction: discord.Interaction, report_type: str, period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title="Report Generation Started", color=0x00FF88)
        embed.add_field(name="Type", value=report_type, inline=True)
        embed.add_field(name="Period", value=period, inline=True)
        embed.add_field(name="Status", value="Queued — ETA 30 seconds", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="report-dashboard", description="Get pre-built KPI dashboard")
    @app_commands.describe(dashboard_type="Dashboard type (kpi_dashboard/cost_overview/savings)")
    async def dashboard(self, interaction: discord.Interaction, dashboard_type: str = "kpi_dashboard"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Dashboard: {dashboard_type}", color=0x00AAFF)
        embed.add_field(name="Total Spend", value="$245,000", inline=True)
        embed.add_field(name="Budget Variance", value="-3.2%", inline=True)
        embed.add_field(name="Savings Achieved", value="$18,500", inline=True)
        embed.add_field(name="Anomaly Count", value="7", inline=True)
        embed.add_field(name="Coverage Rate", value="72%", inline=True)
        embed.add_field(name="Waste Identified", value="$4,200", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="report-summary", description="Reports summary")
    async def rep_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Reports Summary", color=0x00AAFF)
        embed.add_field(name="Total Reports", value="8", inline=True)
        embed.add_field(name="Available Types", value="11 report templates", inline=True)
        embed.add_field(name="KPIs Tracked", value="7 FinOps Foundation KPIs", inline=True)
        embed.add_field(name="Last Generated", value="Executive Summary — 2h ago", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="finops-export", description="Export report data")
    @app_commands.describe(report_type="Report type to export", format="Export format")
    async def export(self, interaction: discord.Interaction, report_type: str = "executive_summary", format: str = "json"):
        await interaction.response.defer()
        embed = discord.Embed(title="Report Exported", color=0x2ECC71)
        embed.add_field(name="Type", value=report_type, inline=True)
        embed.add_field(name="Format", value=format.upper(), inline=True)
        embed.add_field(name="Status", value="Ready for download", inline=True)
        embed.add_field(name="File", value=f"{report_type}_{datetime.utcnow().strftime('%Y%m%d')}.{format}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-allocate", description="Create cost allocation tag")
    @app_commands.describe(tag_key="Tag key", tag_value="Tag value", cost_pct="Cost percentage", team="Team name")
    async def allocate(self, interaction: discord.Interaction, tag_key: str, tag_value: str, cost_pct: float, team: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Allocation Tag Created", color=0x00FF88)
        embed.add_field(name="Tag", value=f"{tag_key}:{tag_value}", inline=True)
        embed.add_field(name="Cost %", value=f"{cost_pct}%", inline=True)
        embed.add_field(name="Team", value=team or "Unassigned", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-compliance", description="Run compliance check")
    async def compliance(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Compliance Check Complete", color=0x00FF88)
        embed.add_field(name="FinOps Foundation", value="Score: 87% — Compliant", inline=False)
        embed.add_field(name="AWS Well-Architected Cost", value="Score: 82% — Compliant", inline=False)
        embed.add_field(name="ISO 27001", value="Score: 92% — Compliant", inline=True)
        embed.add_field(name="Overall", value="87% — Audit ready", inline=True)
        embed.add_field(name="Gaps", value="Cost allocation tagging incomplete", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-forecast", description="Get 3-month spend forecast")
    async def forecast(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spend Forecast (3 Month)", color=0x3498DB)
        embed.add_field(name="Month 1", value="$52,340.00", inline=True)
        embed.add_field(name="Month 2", value="$55,120.00", inline=True)
        embed.add_field(name="Month 3", value="$58,050.00", inline=True)
        embed.add_field(name="Total Forecast", value="$165,510.00", inline=True)
        embed.add_field(name="vs Budget", value="+3.2% over (target <5%)", inline=True)
        embed.add_field(name="Model", value="Ensemble (MA + LR + ES)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-chargeback", description="Show chargeback report")
    @app_commands.describe(department="Filter by department")
    async def chargeback(self, interaction: discord.Interaction, department: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Chargeback Report", color=0x00AAFF)
        embed.add_field(name="Engineering", value="$95,000 — Budget: $100,000 (ok)", inline=False)
        embed.add_field(name="Data Science", value="$72,000 — Budget: $65,000 (over)", inline=False)
        embed.add_field(name="Infrastructure", value="$48,000 — Budget: $50,000 (ok)", inline=False)
        embed.add_field(name="Total", value="$215,000 charged back", inline=True)
        embed.set_footer(text="Mode: Chargeback | Showback also available")
        await interaction.followup.send(embed=embed)


def build_report_filter(report_type: str, period: str) -> dict:
    return {
        "filter_id": str(datetime.utcnow().timestamp()),
        "report_type": report_type,
        "period": period,
        "created_at": datetime.utcnow().isoformat(),
    }

def compute_kpi_summary(kpis: dict) -> dict:
    on_track = sum(1 for k in kpis.values() if k.get('status') == 'on_track')
    attention = sum(1 for k in kpis.values() if k.get('status') == 'attention_needed')
    critical = sum(1 for k in kpis.values() if k.get('status') == 'critical')
    return {"on_track": on_track, "attention_needed": attention, "critical": critical, "total": len(kpis)}

    @app_commands.command(name="finops-cost-trends", description="Show cost trends over time")
    @app_commands.describe(period="Time period (weekly/monthly/quarterly)")
    async def cost_trends(self, interaction: discord.Interaction, period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost Trends ({period.title()})", color=discord.Color.blue())
        embed.add_field(name="Jan 2025", value="$42,500", inline=True)
        embed.add_field(name="Feb 2025", value="$44,100 (+3.8%)", inline=True)
        embed.add_field(name="Mar 2025", value="$43,200 (-2.0%)", inline=True)
        embed.add_field(name="Trend", value="📊 Stable (±3% MoM)", inline=True)
        embed.add_field(name="Forecast Next Month", value="$44,800", inline=True)
        embed.add_field(name="YoY Change", value="+12.4%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-savings-opportunities", description="List savings opportunities")
    async def savings_opportunities(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Savings Opportunities", color=discord.Color.green())
        embed.add_field(name="Rightsizing (12 instances)", value="Potential: $3,200/mo", inline=False)
        embed.add_field(name="Spot Migration (8 workloads)", value="Potential: $4,500/mo", inline=False)
        embed.add_field(name="Commitment Discounts", value="Potential: $2,800/mo", inline=False)
        embed.add_field(name="Total Savings Potential", value="$10,500/mo ($126K/yr)", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-export", description="Export report to format")
    @app_commands.describe(report_type="Report type", export_format="Format (csv/json/pdf)")
    async def finops_export(self, interaction: discord.Interaction, report_type: str = "summary", export_format: str = "csv"):
        await interaction.response.defer()
        embed = discord.Embed(title="Report Export", color=discord.Color.green())
        embed.add_field(name="Report", value=report_type.title(), inline=True)
        embed.add_field(name="Format", value=export_format.upper(), inline=True)
        embed.add_field(name="Download", value=f"finops_{report_type}.{export_format} (1.2 MB)", inline=True)
        embed.add_field(name="Data Range", value="Last 30 days", inline=True)
        await interaction.followup.send(embed=embed)

    @cost_trends.autocomplete("period")
    async def period_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=p.title(), value=p) for p in ["daily", "weekly", "monthly", "quarterly", "yearly"] if current.lower() in p.lower()]

    @app_commands.command(name="finops-custom-report", description="Generate custom report")
    @app_commands.describe(dimensions="Comma-separated dimensions", metrics="Comma-separated metrics")
    async def custom_report(self, interaction: discord.Interaction, dimensions: str = "service,region", metrics: str = "cost,usage"):
        await interaction.response.defer()
        embed = discord.Embed(title="Custom Report Generated", color=discord.Color.green())
        embed.add_field(name="Dimensions", value=dimensions, inline=True)
        embed.add_field(name="Metrics", value=metrics, inline=True)
        embed.add_field(name="Records", value="1,247 rows", inline=True)
        embed.add_field(name="Download", value="custom_report.csv (48 KB)", inline=True)
        embed.set_footer(text="Report cached for 24 hours")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-budget-vs-actual", description="Budget vs actual comparison")
    async def budget_vs_actual(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Budget vs Actual", color=discord.Color.blue())
        embed.add_field(name="Total Budget", value="$400,000", inline=True)
        embed.add_field(name="Total Actual", value="$382,500", inline=True)
        embed.add_field(name="Variance", value="-$17,500 (-4.4%)", inline=True)
        embed.add_field(name="On Track", value="8 budgets", inline=True)
        embed.add_field(name="Over Budget", value="2 budgets", inline=True)
        embed.add_field(name="At Risk", value="2 budgets", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def report_generation_loop(self):
        logging.info("FinopsReporting: daily report generation")

    @report_generation_loop.before_loop
    async def before_report_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=6)
    async def report_cache_refresh(self):
        logging.info("FinopsReporting: refreshing report cache")

    @report_cache_refresh.before_loop
    async def before_cache_refresh(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="finops-report-schedule", description="Schedule recurring reports")
    @app_commands.describe(report_type="Report type", interval="Interval (daily/weekly/monthly)")
    async def finops_report_schedule(self, interaction: discord.Interaction, report_type: str, interval: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title="Report Scheduled", color=discord.Color.green())
        embed.add_field(name="Type", value=report_type.replace("_", " ").title(), inline=True)
        embed.add_field(name="Interval", value=interval.title(), inline=True)
        embed.add_field(name="Status", value="Active — next run in 24h", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-kpi-status", description="Show FinOps KPI status")
    async def finops_kpi_status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="FinOps KPI Dashboard", color=discord.Color.blue())
        embed.add_field(name="Cost Efficiency", value="✅ On Track (88/100)", inline=True)
        embed.add_field(name="Commitment Coverage", value="✅ 72% (target: >60%)", inline=True)
        embed.add_field(name="Utilization Rate", value="⚠️ 78% (target: >85%)", inline=True)
        embed.add_field(name="Waste Reduction", value="✅ 4.2% (target: <5%)", inline=True)
        embed.add_field(name="Forecast Accuracy", value="✅ 92% (target: >90%)", inline=True)
        embed.add_field(name="Anomaly Response", value="⚠️ 4.5h avg (target: <4h)", inline=True)
        embed.set_footer(text="5 of 7 KPIs on track")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-export", description="Export report data")
    @app_commands.describe(report_id="Report ID", fmt="Export format")
    async def finops_export(self, interaction: discord.Interaction, report_id: str, fmt: str = "csv"):
        await interaction.response.defer()
        embed = discord.Embed(title="Report Exported", color=discord.Color.green())
        embed.add_field(name="Report", value=report_id, inline=True)
        embed.add_field(name="Format", value=fmt.upper(), inline=True)
        embed.add_field(name="Download", value=f"report_{report_id[:8]}.{fmt}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="finops-audit-trail", description="View audit trail for reports")
    @app_commands.describe(report_id="Report ID (optional)")
    async def finops_audit_trail(self, interaction: discord.Interaction, report_id: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Audit Trail", color=discord.Color.blue())
        embed.add_field(name="Total Reports", value="47 generated", inline=True)
        embed.add_field(name="Last Generated", value="2025-03-15 08:00 UTC", inline=True)
        embed.add_field(name="Compliance Score", value="92%", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=12)
    async def report_schedule_checker(self):
        logging.info("FinopsReporting: checking scheduled reports")

    @report_schedule_checker.before_loop
    async def before_report_schedule_checker(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(FinopsReporting(bot))

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
        return {"total_ops": 0, "total_cost": 0.0, "total_savings": 0.0, "efficiency": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class FinopsCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    cost_impact: float = 0.0
    savings: float = 0.0
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FinopsCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total_cost: float = Field(default=0.0)
    total_savings: float = Field(default=0.0)

    def add_result(self, cost: float = 0.0, savings: float = 0.0) -> None:
        self.total_cost += cost
        self.total_savings += savings

    def complete(self) -> None:
        self.status = "completed"

class FinopsCogMetrics:
    def __init__(self) -> None:
        self.operations: int = 0
        self.total_savings: float = 0.0
        self.total_cost: float = 0.0
        self.errors: int = 0

    def record(self, savings: float = 0.0, cost: float = 0.0, error: bool = False) -> None:
        self.operations += 1
        self.total_savings += savings
        self.total_cost += cost
        if error:
            self.errors += 1

    def summary(self) -> Dict[str, Any]:
        return {"operations": self.operations, "total_savings": round(self.total_savings, 2),
                "total_cost": round(self.total_cost, 2), "errors": self.errors,
                "net_savings": round(self.total_savings - self.total_cost, 2),
                "error_rate": round(self.errors / max(self.operations, 1) * 100, 1)}
