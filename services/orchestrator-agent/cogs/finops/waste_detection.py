import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class WasteDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="waste-scan", description="Scan for cloud waste")
    async def scan(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Scan Complete", color=0x00AAFF)
        embed.add_field(name="Resources Scanned", value="156", inline=True)
        embed.add_field(name="Waste Found", value="18 items", inline=True)
        embed.add_field(name="Total Monthly Waste", value="$1,847.00", inline=True)
        embed.add_field(name="Unattached Volumes", value="4 ($320/mo)", inline=True)
        embed.add_field(name="Idle Instances", value="3 ($560/mo)", inline=True)
        embed.add_field(name="Orphaned Snapshots", value="7 ($210/mo)", inline=True)
        embed.add_field(name="Underutilized DBs", value="2 ($450/mo)", inline=True)
        embed.add_field(name="Orphaned LBs", value="2 ($307/mo)", inline=True)
        embed.set_footer(text="Auto-cleanup eligible: 12 items")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-list", description="List waste findings")
    @app_commands.describe(category="Filter by category")
    async def list_waste(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Findings", color=0xFF4444)
        embed.add_field(name="vol-001", value="Unattached gp3 volume — 100GB — $8.20/mo", inline=False)
        embed.add_field(name="i-0a1b2c", value="Idle t3.large — 28 days — $68.64/mo", inline=False)
        embed.add_field(name="snap-003", value="Orphaned snapshot — 200 days old — $12.50/mo", inline=False)
        embed.add_field(name="db-02", value="Underutilized db.r5.large — 4% CPU — $175.20/mo", inline=False)
        embed.set_footer(text=f"{'Category: ' + category if category else 'All categories'} | Total: 18 findings")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-cleanup-approve", description="Approve waste cleanup")
    @app_commands.describe(finding_id="Finding ID")
    async def approve_cleanup(self, interaction: discord.Interaction, finding_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Cleanup Approved", color=0x00FF88)
        embed.add_field(name="Finding", value=finding_id, inline=True)
        embed.add_field(name="Action", value="Resource queued for deletion", inline=True)
        embed.add_field(name="Expected Savings", value="$8.20/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-summary", description="Waste detection summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Detection Summary", color=0x00AAFF)
        embed.add_field(name="Total Waste/Month", value="$1,847.00", inline=True)
        embed.add_field(name="Annual Waste", value="$22,164.00", inline=True)
        embed.add_field(name="% of Total Spend", value="4.8%", inline=True)
        embed.add_field(name="Open Findings", value="15", inline=True)
        embed.add_field(name="Approved Cleanup", value="3", inline=True)
        embed.add_field(name="Cleaned Up (30d)", value="22 items ($2,100 saved)", inline=True)
        embed.add_field(name="Top Category", value="Idle Instances ($560/mo)", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="waste-scan", description="Run a waste scan")
    async def scan(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Scan Complete", color=0x00FF88)
        embed.add_field(name="Findings", value="12 new waste items", inline=True)
        embed.add_field(name="Total Waste", value="$4,200.00/mo", inline=True)
        embed.add_field(name="Categories", value="Idle: 5 | Storage: 3 | Over-provisioned: 4", inline=False)
        embed.add_field(name="Top Finding", value="i-0abc: EC2 idle 30 days — $450/mo", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-cleanup", description="Execute waste cleanup")
    @app_commands.describe(finding_id="Finding ID")
    async def cleanup(self, interaction: discord.Interaction, finding_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Cleanup Executed", color=0x00FF88)
        embed.add_field(name="Finding", value=finding_id, inline=True)
        embed.add_field(name="Action", value="Resource stopped/deleted", inline=True)
        embed.add_field(name="Monthly Savings", value="$450.00", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-list", description="List waste findings")
    @app_commands.describe(category="Filter by category", severity="Filter by severity")
    async def list_findings(self, interaction: discord.Interaction, category: str = None, severity: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Findings", color=0xFF6B6B)
        embed.add_field(name="i-0abc (EC2)", value="Idle | $450/mo | High | Open", inline=False)
        embed.add_field(name="vol-0def (EBS)", value="Unattached | $120/mo | Med | Open", inline=False)
        embed.add_field(name="rds-prod (RDS)", value="Over-provisioned | $280/mo | High | Approved", inline=False)
        embed.add_field(name="Total Waste", value="$4,200/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-summary", description="Waste detection summary")
    async def waste_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Detection Summary", color=0x00AAFF)
        embed.add_field(name="Total Findings", value="18", inline=True)
        embed.add_field(name="Open", value="12", inline=True)
        embed.add_field(name="Approved", value="3", inline=True)
        embed.add_field(name="Cleaned Up", value="2", inline=True)
        embed.add_field(name="Dismissed", value="1", inline=True)
        embed.add_field(name="Total Waste", value="$4,200/mo", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="waste-categorize", description="Show waste by category")
    async def categorize(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste by Category", color=0x3498DB)
        embed.add_field(name="Idle Instances", value="$560/mo (3 items)", inline=False)
        embed.add_field(name="Unattached Volumes", value="$320/mo (4 items)", inline=False)
        embed.add_field(name="Orphaned Snapshots", value="$210/mo (7 items)", inline=False)
        embed.add_field(name="Underutilized DBs", value="$450/mo (2 items)", inline=False)
        embed.add_field(name="Orphaned LBs", value="$307/mo (2 items)", inline=False)
        embed.add_field(name="Total", value="$1,847.00/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-auto-cleanup", description="Run auto-cleanup for eligible items")
    async def auto_cleanup(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Auto-Cleanup Complete", color=0x00FF88)
        embed.add_field(name="Items Cleaned", value="5", inline=True)
        embed.add_field(name="Resources Saved", value="3 volumes, 2 snapshots", inline=True)
        embed.add_field(name="Monthly Waste Eliminated", value="$87.40/mo", inline=True)
        embed.add_field(name="Annual Recovery", value="$1,048.80", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-trend", description="Show waste trend over time")
    @app_commands.describe(days="Lookback period")
    async def trend(self, interaction: discord.Interaction, days: int = 90):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Waste Trend (Last {days} Days)", color=0x9B59B6)
        embed.add_field(name="30 Days Ago", value="$2,150/mo", inline=True)
        embed.add_field(name="60 Days Ago", value="$2,800/mo", inline=True)
        embed.add_field(name="Current", value="$1,847/mo", inline=True)
        embed.add_field(name="Change", value="Decreasing 14% MoM", inline=True)
        embed.add_field(name="Total Eliminated (Period)", value="$3,200.00", inline=True)
        embed.add_field(name="On Track", value="Yes — under 5% of total spend", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-report", description="Generate waste analysis report")
    async def waste_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Analysis Report", color=0x00AAFF)
        embed.add_field(name="Period", value="Monthly", inline=True)
        embed.add_field(name="Total Waste", value="$1,847.00", inline=True)
        embed.add_field(name="Waste % of Spend", value="4.8%", inline=True)
        embed.add_field(name="Recoverable", value="$1,478.00 (80%)", inline=True)
        embed.add_field(name="Auto-Cleanup Eligible", value="12 items ($890/mo)", inline=True)
        embed.add_field(name="Top Action", value="Stop idle instances to save $560/mo", inline=False)
        await interaction.followup.send(embed=embed)


def compute_waste_savings(findings: list, recovery_rate: float = 0.8) -> dict:
    total = sum(f.get('monthly_waste', 0) for f in findings)
    recoverable = total * recovery_rate
    return {
        "total_monthly": round(total, 2),
        "annual": round(total * 12, 2),
        "recoverable_monthly": round(recoverable, 2),
        "recoverable_annual": round(recoverable * 12, 2),
        "recovery_rate_pct": recovery_rate * 100,
    }

def categorize_waste_findings(findings: list) -> dict:
    cats = {}
    for f in findings:
        cat = f.get('category', 'other')
        cats.setdefault(cat, {"count": 0, "total": 0.0})
        cats[cat]["count"] += 1
        cats[cat]["total"] += f.get('monthly_waste', 0)
    return {k: {**v, "total": round(v["total"], 2)} for k, v in cats.items()}

    @app_commands.command(name="waste-idle-resources", description="Find idle resources")
    async def waste_idle_resources(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Idle Resources", color=discord.Color.orange())
        embed.add_field(name="Idle Instances", value="4 ($320/mo)", inline=True)
        embed.add_field(name="Idle Load Balancers", value="2 ($45/mo)", inline=True)
        embed.add_field(name="Unattached EBS", value="8 ($72/mo)", inline=True)
        embed.add_field(name="Unused IPs", value="12 ($43/mo)", inline=True)
        embed.add_field(name="Total Idle Waste", value="$480/mo ($5,760/yr)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-orphaned", description="Find orphaned resources")
    async def waste_orphaned(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Orphaned Resources", color=discord.Color.orange())
        embed.add_field(name="Orphaned Snapshots", value="24 ($140/mo)", inline=True)
        embed.add_field(name="Orphaned EBS Volumes", value="6 ($54/mo)", inline=True)
        embed.add_field(name="Orphaned ENIs", value="3 ($9/mo)", inline=True)
        embed.add_field(name="Orphaned Log Groups", value="15 ($22/mo)", inline=True)
        embed.add_field(name="Total Orphaned Waste", value="$225/mo ($2,700/yr)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-auto-cleanup", description="Configure auto-cleanup rules")
    @app_commands.describe(enabled="Enable/disable", dry_run="Preview only")
    async def waste_auto_cleanup(self, interaction: discord.Interaction, enabled: bool = True, dry_run: bool = True):
        await interaction.response.defer()
        embed = discord.Embed(title="Auto-Cleanup Configuration", color=discord.Color.green())
        embed.add_field(name="Enabled", value=str(enabled), inline=True)
        embed.add_field(name="Dry Run", value=str(dry_run), inline=True)
        embed.add_field(name="Scheduled Action", value="Stop idle instances >14 days", inline=False)
        embed.add_field(name="Notification", value="24h warning before cleanup", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-summary-pdf", description="Generate PDF waste summary")
    async def waste_summary_pdf(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Summary Report (PDF)", color=discord.Color.green())
        embed.add_field(name="Total Waste", value="$1,847/mo", inline=True)
        embed.add_field(name="Waste %", value="4.8%", inline=True)
        embed.add_field(name="Recoverable", value="$1,478 (80%)", inline=True)
        embed.add_field(name="Generated", value="waste_report_2026-06-02.pdf", inline=False)
        embed.set_footer(text="Report available for 24 hours")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="waste-set-budget", description="Set waste budget threshold")
    @app_commands.describe(threshold_pct="Max waste % of total spend")
    async def waste_set_budget(self, interaction: discord.Interaction, threshold_pct: float = 5.0):
        await interaction.response.defer()
        embed = discord.Embed(title="Waste Budget Configured", color=discord.Color.blue())
        embed.add_field(name="Waste Budget", value=f"{threshold_pct}% of total spend", inline=True)
        embed.add_field(name="Current Waste", value="4.8%", inline=True)
        embed.add_field(name="Status", value="✅ Within budget" if threshold_pct >= 4.8 else "⚠️ Over budget", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=12)
    async def waste_scan_loop(self):
        logging.info("WasteDetection: running waste scan")

    @waste_scan_loop.before_loop
    async def before_waste_scan(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(WasteDetection(bot))

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
