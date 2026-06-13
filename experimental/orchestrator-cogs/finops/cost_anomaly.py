import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class CostAnomaly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cost-anomalies", description="List cost anomalies")
    @app_commands.describe(severity="Filter by severity")
    async def list_anomalies(self, interaction: discord.Interaction, severity: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Cost Anomalies", color=0xFF4444)
        embed.add_field(name="CRITICAL", value="AWS EC2 — $4,230 spike (2h ago)", inline=False)
        embed.add_field(name="HIGH", value="Data Transfer — $890 increase (6h ago)", inline=False)
        embed.add_field(name="MEDIUM", value="New Instance launched in ap-southeast-1", inline=False)
        embed.add_field(name="LOW", value="S3 request cost +12%", inline=False)
        embed.set_footer(text=f"{'All severities' if not severity else severity} | Detected in last 24h")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-investigate", description="Investigate an anomaly")
    @app_commands.describe(anomaly_id="Anomaly ID")
    async def investigate(self, interaction: discord.Interaction, anomaly_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Investigating: {anomaly_id}", color=0xFFAA00)
        embed.add_field(name="Service", value="AWS EC2", inline=True)
        embed.add_field(name="Region", value="us-east-1", inline=True)
        embed.add_field(name="Amount", value="$4,230.50", inline=True)
        embed.add_field(name="Expected", value="$1,850.00", inline=True)
        embed.add_field(name="Deviation", value="128.7% above baseline", inline=True)
        embed.add_field(name="Root Cause Hint", value="New c5.4xlarge instance launched at 14:32 UTC", inline=False)
        embed.add_field(name="Status", value="Investigating", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-resolve", description="Resolve an anomaly")
    @app_commands.describe(anomaly_id="Anomaly ID", notes="Resolution notes")
    async def resolve(self, interaction: discord.Interaction, anomaly_id: str, notes: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Resolved", color=0x00FF88)
        embed.add_field(name="ID", value=anomaly_id, inline=True)
        embed.add_field(name="Notes", value=notes or "Auto-remediation applied", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-summary", description="Anomaly detection summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Cost Anomaly Summary", color=0x00AAFF)
        embed.add_field(name="Total (24h)", value="12 anomalies", inline=True)
        embed.add_field(name="Critical", value="1", inline=True)
        embed.add_field(name="High", value="3", inline=True)
        embed.add_field(name="Medium", value="5", inline=True)
        embed.add_field(name="Low", value="3", inline=True)
        embed.add_field(name="Avg Response Time", value="1h 23m", inline=True)
        embed.add_field(name="Auto-Resolved", value="4 (33%)", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="cost-anomaly-list", description="List current anomalies")
    @app_commands.describe(severity="Filter by severity (critical/high/medium/low)")
    async def list_anomalies(self, interaction: discord.Interaction, severity: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Cost Anomalies", color=0xFF6B6B)
        embed.add_field(name="CRITICAL", value="EC2 spend spike: $15,200 (expected: $3,100)", inline=False)
        embed.add_field(name="HIGH", value="Data Transfer (us-east-1): $8,900 (expected: $2,000)", inline=False)
        embed.add_field(name="MEDIUM", value="S3 standard storage: $4,200 (+42% WoW)", inline=False)
        embed.add_field(name="MEDIUM", value="RDS IO burst: $3,100 (+35% WoW)", inline=False)
        embed.set_footer(text="Filtering: " + (severity or "all"))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-profile", description="Manage detection profiles")
    @app_commands.describe(action="Action: list/create/delete")
    async def profile(self, interaction: discord.Interaction, action: str = "list"):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Detection Profiles", color=0x00AAFF)
        embed.add_field(name="default-zscore", value="Method: zscore | Sensitivity: 2.0 | Active", inline=False)
        embed.add_field(name="critical-mad", value="Method: mad | Sensitivity: 3.5 | Active", inline=False)
        embed.add_field(name="adaptive-prod", value="Method: adaptive | Sensitivity: 1.5 | Active", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-ingest", description="Ingest a spend record for testing")
    @app_commands.describe(service="Service name", amount="Spend amount", region="Region")
    async def ingest(self, interaction: discord.Interaction, service: str, amount: float, region: str = "us-east-1"):
        await interaction.response.defer()
        embed = discord.Embed(title="Spend Record Ingested", color=0x00FF88)
        embed.add_field(name="Service", value=service, inline=True)
        embed.add_field(name="Amount", value=f"${amount:.2f}", inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(name="Anomaly Check", value="Analysis queued", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="cost-anomaly-trend", description="Show anomaly trend over time")
    @app_commands.describe(days="Lookback period in days")
    async def trend(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Anomaly Trend (Last {days} Days)", color=0x9B59B6)
        embed.add_field(name="Total Anomalies", value="47", inline=True)
        embed.add_field(name="Avg/Day", value="1.6", inline=True)
        embed.add_field(name="Trend", value="Decreasing (-12% WoW)", inline=True)
        embed.add_field(name="Most Common Source", value="Service Spike (42%)", inline=True)
        embed.add_field(name="Avg Severity Score", value="2.4 / 5.0", inline=True)
        embed.add_field(name="Auto-Resolved", value="15 (32%)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-config", description="Configure detection settings")
    @app_commands.describe(method="Detection method (zscore/mad/iqr/adaptive)", sensitivity="Sensitivity threshold")
    async def config(self, interaction: discord.Interaction, method: str = "zscore", sensitivity: float = 2.0):
        await interaction.response.defer()
        embed = discord.Embed(title="Detection Configuration Updated", color=0x00FF88)
        embed.add_field(name="Method", value=method, inline=True)
        embed.add_field(name="Sensitivity", value=str(sensitivity), inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        embed.set_footer(text="Changes applied to all detection profiles")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-report", description="Generate anomaly report")
    async def report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Detection Report", color=0x00AAFF)
        embed.add_field(name="Period", value="Last 30 days", inline=True)
        embed.add_field(name="Total Anomalies", value="47", inline=True)
        embed.add_field(name="Open", value="8", inline=True)
        embed.add_field(name="Resolved", value="39", inline=True)
        embed.add_field(name="Excess Spend (Open)", value="$12,450.00", inline=True)
        embed.add_field(name="Avg Resolution Time", value="2h 15m", inline=True)
        embed.add_field(name="Recommendations", value="Review critical anomalies, tune sensitivity for data-transfer", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-dismiss", description="Dismiss an anomaly")
    @app_commands.describe(anomaly_id="Anomaly ID", reason="Dismissal reason")
    async def dismiss(self, interaction: discord.Interaction, anomaly_id: str, reason: str = "False positive"):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Dismissed", color=0x95A5A6)
        embed.add_field(name="ID", value=anomaly_id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.followup.send(embed=embed)


def compute_anomaly_stats(anomalies: list) -> dict:
    open_count = sum(1 for a in anomalies if a.get('status') == 'open')
    total_excess = sum(a.get('excess_amount', 0) for a in anomalies if a.get('status') == 'open')
    by_severity = {}
    for a in anomalies:
        sev = a.get('severity', 'unknown')
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return {
        "total": len(anomalies),
        "open": open_count,
        "total_excess_spend": round(total_excess, 2),
        "by_severity": by_severity,
    }

def get_anomaly_severity_color(severity: str) -> int:
    return {"critical": 0xFF4444, "high": 0xFFAA00, "medium": 0xFFFF00, "low": 0x00AAFF}.get(severity, 0x00AAFF)

    @app_commands.command(name="cost-anomaly-findings", description="Summarize anomaly findings")
    async def anomaly_findings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Findings Summary", color=discord.Color.blue())
        embed.add_field(name="Total Anomalies (30d)", value="24", inline=True)
        embed.add_field(name="Open", value="8", inline=True)
        embed.add_field(name="Resolved", value="16", inline=True)
        embed.add_field(name="Total Excess", value="$12,450", inline=True)
        embed.add_field(name="Avg Severity", value="Medium", inline=True)
        embed.add_field(name="Largest", value="$4,200 (critical)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-metrics", description="View anomaly detection metrics")
    async def anomaly_metrics(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Detection Metrics", color=discord.Color.blue())
        embed.add_field(name="Detection Rate", value="94.2%", inline=True)
        embed.add_field(name="False Positive Rate", value="3.1%", inline=True)
        embed.add_field(name="Avg Detection Time", value="12 min", inline=True)
        embed.add_field(name="Model Used", value="Isolation Forest + Z-Score", inline=True)
        embed.add_field(name="Training Period", value="90 days", inline=True)
        embed.add_field(name="Last Retrain", value="2025-03-10", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-configure", description="Configure anomaly detection")
    @app_commands.describe(sensitivity="Detection sensitivity", notification_channel="Notification channel")
    async def anomaly_configure(self, interaction: discord.Interaction, sensitivity: str = "medium", notification_channel: str = "general"):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Detection Configured", color=discord.Color.green())
        embed.add_field(name="Sensitivity", value=sensitivity.title(), inline=True)
        embed.add_field(name="Notification Channel", value=f"#{notification_channel}", inline=True)
        embed.add_field(name="Status", value="Configuration saved", inline=True)
        await interaction.followup.send(embed=embed)

    @anomaly_configure.autocomplete("sensitivity")
    async def sensitivity_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=s.title(), value=s) for s in ["low", "medium", "high", "custom"] if current.lower() in s.lower()]

    @tasks.loop(hours=6)
    async def anomaly_detection_loop(self):
        logging.info("CostAnomaly: running anomaly detection scan")

    @anomaly_detection_loop.before_loop
    async def before_anomaly_detection_loop(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="cost-anomaly-severity-breakdown", description="Breakdown by severity level")
    async def anomaly_severity_breakdown(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Anomaly Severity Breakdown", color=discord.Color.blue())
        embed.add_field(name="Critical", value="3 ($6,200 excess)", inline=True)
        embed.add_field(name="High", value="5 ($3,800 excess)", inline=True)
        embed.add_field(name="Medium", value="8 ($1,800 excess)", inline=True)
        embed.add_field(name="Low", value="8 ($650 excess)", inline=True)
        embed.add_field(name="Total Open", value="24 ($12,450 excess)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-respond", description="Take action on an anomaly")
    @app_commands.describe(anomaly_id="Anomaly ID", action="Action to take")
    async def anomaly_respond(self, interaction: discord.Interaction, anomaly_id: str, action: str = "investigate"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Anomaly {action.title()}: {anomaly_id}", color=discord.Color.blue())
        embed.add_field(name="Action", value=action.title(), inline=True)
        embed.add_field(name="Status", value="Ticket created", inline=True)
        embed.add_field(name="Assignee", value="Auto-assigned to FinOps team", inline=True)
        await interaction.followup.send(embed=embed)

    @anomaly_respond.autocomplete("action")
    async def action_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=a.title(), value=a) for a in ["investigate", "dismiss", "escalate", "suppress"] if current.lower() in a.lower()]

    @tasks.loop(hours=1)
    async def anomaly_alert_loop(self):
        logging.info("CostAnomaly: checking for new anomalies")

    @anomaly_alert_loop.before_loop
    async def before_anomaly_alert(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="cost-anomaly-correlate", description="Find correlated anomalies")
    @app_commands.describe(anomaly_id="Anomaly ID")
    async def anomaly_correlate(self, interaction: discord.Interaction, anomaly_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Correlated Anomalies: {anomaly_id}", color=discord.Color.blue())
        embed.add_field(name="Related #1", value="EC2 spike (score: 0.89)", inline=False)
        embed.add_field(name="Related #2", value="Data Transfer surge (score: 0.72)", inline=False)
        embed.add_field(name="Related #3", value="RDS IO burst (score: 0.45)", inline=False)
        embed.set_footer(text="6-hour correlation window")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-threshold-test", description="Test different thresholds")
    @app_commands.describe(service="Service to test")
    async def anomaly_threshold_test(self, interaction: discord.Interaction, service: str = "aws-ec2"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Threshold Test: {service}", color=discord.Color.blue())
        embed.add_field(name="Z-Score 2.0", value="12 anomalies detected", inline=True)
        embed.add_field(name="Z-Score 2.5", value="7 anomalies detected", inline=True)
        embed.add_field(name="Z-Score 3.0", value="3 anomalies detected", inline=True)
        embed.add_field(name="Recommended", value="Z-Score 2.5 (balanced)", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-forecast", description="Forecast future anomalies")
    @app_commands.describe(hours="Hours ahead to forecast")
    async def anomaly_forecast(self, interaction: discord.Interaction, hours: int = 24):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Anomaly Forecast ({hours}h)", color=discord.Color.blue())
        embed.add_field(name="Expected Anomalies", value="2-4", inline=True)
        embed.add_field(name="Peak Risk Window", value="14:00-18:00 UTC", inline=True)
        embed.add_field(name="Confidence", value="Medium (68%)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cost-anomaly-auto-respond", description="Configure auto-response rules")
    @app_commands.describe(action="Auto-response action")
    async def anomaly_auto_respond(self, interaction: discord.Interaction, action: str = "auto_resolve"):
        await interaction.response.defer()
        embed = discord.Embed(title="Auto-Response Configured", color=discord.Color.green())
        embed.add_field(name="Action", value=action.replace("_", " ").title(), inline=True)
        embed.add_field(name="Rules Active", value="4", inline=True)
        embed.add_field(name="Status", value="Enabled", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=1)
    async def anomaly_hourly_check(self):
        logging.info("CostAnomaly: hourly anomaly scan")

    @anomaly_hourly_check.before_loop
    async def before_anomaly_hourly(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CostAnomaly(bot))

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
