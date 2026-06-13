import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class Rightsizing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rightsize-analyze", description="Analyze resource utilization")
    @app_commands.describe(resource_id="Resource ID or name")
    async def analyze(self, interaction: discord.Interaction, resource_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Rightsizing Analysis: {resource_id}", color=0x00AAFF)
        embed.add_field(name="Current Size", value="t3.large (2 vCPU, 8 GB)", inline=True)
        embed.add_field(name="Monthly Cost", value="$68.64", inline=True)
        embed.add_field(name="Avg CPU", value="22.3%", inline=True)
        embed.add_field(name="Avg Memory", value="35.7%", inline=True)
        embed.add_field(name="P95 CPU", value="41.2%", inline=True)
        embed.add_field(name="Assessment", value="Over-provisioned by ~60%", inline=False)
        embed.add_field(name="Recommended", value="t3.medium — save $34.32/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-recommendations", description="List rightsizing recommendations")
    async def recommendations(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Recommendations", color=0x00AAFF)
        embed.add_field(name="CRITICAL", value="db-primary-01: db.r5.large → db.r5.medium (save $87.60/mo)", inline=False)
        embed.add_field(name="HIGH", value="web-server-01: t3.large → t3.medium (save $34.32/mo)", inline=False)
        embed.add_field(name="HIGH", value="cache-cluster: r5.large → r5.small (save $65.00/mo)", inline=False)
        embed.add_field(name="MEDIUM", value="batch-worker: m5.xlarge → m5.large (save $81.00/mo)", inline=False)
        embed.set_footer(text="Total potential savings: $267.92/mo")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-approve", description="Approve a recommendation")
    @app_commands.describe(rec_id="Recommendation ID")
    async def approve(self, interaction: discord.Interaction, rec_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Recommendation Approved", color=0x00FF88)
        embed.add_field(name="ID", value=rec_id, inline=True)
        embed.add_field(name="Status", value="Approved — pending implementation", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-implement", description="Implement a recommendation")
    @app_commands.describe(rec_id="Recommendation ID")
    async def implement(self, interaction: discord.Interaction, rec_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Recommendation Implemented", color=0x00FF88)
        embed.add_field(name="ID", value=rec_id, inline=True)
        embed.add_field(name="New Size", value="t3.medium", inline=True)
        embed.add_field(name="Monthly Savings", value="$34.32", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-summary", description="Rightsizing summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Summary", color=0x00AAFF)
        embed.add_field(name="Resources Analyzed", value="18", inline=True)
        embed.add_field(name="Recommendations", value="7", inline=True)
        embed.add_field(name="Potential Monthly Savings", value="$3,240.00", inline=True)
        embed.add_field(name="Potential Annual Savings", value="$38,880.00", inline=True)
        embed.add_field(name="Implemented", value="3 of 7", inline=True)
        embed.add_field(name="Realized Savings", value="$892.00/mo", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="rightsize-list", description="List rightsizing recommendations")
    @app_commands.describe(severity="Filter by severity")
    async def list_recs(self, interaction: discord.Interaction, severity: str = None):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Recommendations", color=0x00AAFF)
        embed.add_field(name="i-0abc (EC2)", value="m5.xlarge → m5.large | Save $34/mo | Critical", inline=False)
        embed.add_field(name="rds-prod (RDS)", value="db.r5.2xl → db.r5.xl | Save $128/mo | High", inline=False)
        embed.add_field(name="vol-0def (EBS)", value="gp3:500GB → gp3:200GB | Save $18/mo | Medium", inline=False)
        embed.add_field(name="Total Potential", value="$3,240.00/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-approve", description="Approve a recommendation")
    @app_commands.describe(rec_id="Recommendation ID")
    async def approve(self, interaction: discord.Interaction, rec_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Recommendation Approved", color=0x00FF88)
        embed.add_field(name="ID", value=rec_id, inline=True)
        embed.add_field(name="Status", value="Approved — pending implementation", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-dismiss", description="Dismiss a recommendation")
    @app_commands.describe(rec_id="Recommendation ID", reason="Dismiss reason")
    async def dismiss(self, interaction: discord.Interaction, rec_id: str, reason: str = "Not applicable"):
        await interaction.response.defer()
        embed = discord.Embed(title="Recommendation Dismissed", color=0xFFAA00)
        embed.add_field(name="ID", value=rec_id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-register", description="Register a resource for analysis")
    @app_commands.describe(name="Resource name", resource_type="Type (compute/database/storage)", size="Current size", monthly_cost="Monthly cost")
    async def register(self, interaction: discord.Interaction, name: str, resource_type: str, size: str, monthly_cost: float = 100):
        await interaction.response.defer()
        embed = discord.Embed(title="Resource Registered", color=0x00FF88)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Type", value=resource_type, inline=True)
        embed.add_field(name="Size", value=size, inline=True)
        embed.add_field(name="Monthly Cost", value=f"${monthly_cost:.2f}", inline=True)
        embed.add_field(name="Status", value="Pending analysis", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="rightsize-report", description="Generate rightsizing report")
    async def report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Report", color=0x00AAFF)
        embed.add_field(name="Total Recommendations", value="7", inline=True)
        embed.add_field(name="Pending", value="4", inline=True)
        embed.add_field(name="Implemented", value="3", inline=True)
        embed.add_field(name="Potential Annual Savings", value="$38,880.00", inline=True)
        embed.add_field(name="Implemented Savings", value="$10,704.00/yr", inline=True)
        embed.add_field(name="Recommendation", value="Focus on critical RDS downsizing first", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-batch", description="Batch approve recommendations")
    @app_commands.describe(priority="Minimum priority to approve (critical/high/medium)")
    async def batch_approve(self, interaction: discord.Interaction, priority: str = "high"):
        await interaction.response.defer()
        embed = discord.Embed(title="Batch Approval Complete", color=0x00FF88)
        embed.add_field(name="Priority", value=priority, inline=True)
        embed.add_field(name="Approved", value="3 recommendations", inline=True)
        embed.add_field(name="Estimated Savings", value="$187.00/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-simulate", description="Simulate resize of a resource")
    @app_commands.describe(current_size="Current instance size", target_size="Target instance size", monthly_cost="Current monthly cost")
    async def simulate(self, interaction: discord.Interaction, current_size: str, target_size: str, monthly_cost: float):
        await interaction.response.defer()
        savings_map = {"t3.large->t3.medium": 0.5, "t3.xlarge->t3.large": 0.5, "m5.xlarge->m5.large": 0.5}
        key = f"{current_size}->{target_size}"
        savings_pct = savings_map.get(key, 0.4)
        savings = monthly_cost * savings_pct
        embed = discord.Embed(title="Resize Simulation", color=0x3498DB)
        embed.add_field(name="Current", value=current_size, inline=True)
        embed.add_field(name="Target", value=target_size, inline=True)
        embed.add_field(name="Current Cost", value=f"${monthly_cost:.2f}/mo", inline=True)
        embed.add_field(name="Estimated New Cost", value=f"${monthly_cost - savings:.2f}/mo", inline=True)
        embed.add_field(name="Monthly Savings", value=f"${savings:.2f} ({savings_pct*100:.0f}%)", inline=True)
        embed.add_field(name="Annual Savings", value=f"${savings * 12:.2f}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-summary", description="Full rightsizing summary")
    async def full_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Summary", color=0x00AAFF)
        embed.add_field(name="Resources", value="18 analyzed", inline=True)
        embed.add_field(name="Over-Provisioned", value="5 (28%)", inline=True)
        embed.add_field(name="Under-Provisioned", value="2 (11%)", inline=True)
        embed.add_field(name="Right-Sized", value="11 (61%)", inline=True)
        embed.add_field(name="Total Potential Savings", value="$267.92/mo", inline=True)
        embed.add_field(name="Avg Savings/Resource", value="$53.58/mo", inline=True)
        await interaction.followup.send(embed=embed)


def compute_size_savings(current_cost: float, pct_reduction: float) -> dict:
    savings = current_cost * pct_reduction
    return {
        "current_cost": round(current_cost, 2),
        "new_cost": round(current_cost - savings, 2),
        "monthly_savings": round(savings, 2),
        "annual_savings": round(savings * 12, 2),
        "reduction_pct": round(pct_reduction * 100, 1),
    }

def get_recommended_size(current: str, workload_type: str) -> str:
    downsizing = {
        "t3.large": "t3.medium", "t3.xlarge": "t3.large", "t3.2xlarge": "t3.xlarge",
        "m5.large": "m5.medium", "m5.xlarge": "m5.large", "m5.2xlarge": "m5.xlarge",
        "r5.large": "r5.medium", "r5.xlarge": "r5.large",
        "db.r5.large": "db.r5.medium", "db.r5.xlarge": "db.r5.large",
    }
    return downsizing.get(current, f"{current}-rightsized")

    @app_commands.command(name="rightsize-history", description="Rightsizing history for a resource")
    @app_commands.describe(resource_id="Resource ID")
    async def rightsize_history(self, interaction: discord.Interaction, resource_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Rightsizing History: {resource_id}", color=discord.Color.blue())
        embed.add_field(name="Current Size", value="m5.large", inline=True)
        embed.add_field(name="CPU Avg", value="12.4%", inline=True)
        embed.add_field(name="Memory Avg", value="34.2%", inline=True)
        embed.add_field(name="Recommended", value="m5.medium ($17.52/mo savings)", inline=True)
        embed.add_field(name="Last Evaluated", value="2025-03-15", inline=True)
        embed.add_field(name="Confidence", value="High (90 days of data)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-bulk", description="Bulk rightsizing recommendations")
    async def rightsize_bulk(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Bulk Rightsizing Recommendations", color=discord.Color.blue())
        embed.add_field(name="i-0a1b2c3d (web-01)", value="m5.xlarge → m5.large — Save $34.56/mo", inline=False)
        embed.add_field(name="i-0e4f5g6h (worker-02)", value="t3.large → t3.medium — Save $17.28/mo", inline=False)
        embed.add_field(name="i-0i7j8k9l (db-01)", value="db.r5.xlarge → db.r5.large — Save $86.40/mo", inline=False)
        embed.add_field(name="Total Savings", value="$138.24/mo ($1,658.88/yr)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-automation", description="Configure auto-rightsizing")
    @app_commands.describe(enabled="Enable/disable", schedule="Cron schedule")
    async def rightsize_automation(self, interaction: discord.Interaction, enabled: bool = True, schedule: str = "0 2 * * 0"):
        await interaction.response.defer()
        embed = discord.Embed(title="Auto-Rightsizing Configured", color=discord.Color.green())
        embed.add_field(name="Enabled", value=str(enabled), inline=True)
        embed.add_field(name="Schedule", value=schedule, inline=True)
        embed.add_field(name="Next Run", value="Sunday 02:00 UTC", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-analysis", description="Detailed rightsizing analysis")
    @app_commands.describe(resource_id="Resource ID")
    async def rightsize_analysis(self, interaction: discord.Interaction, resource_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Detailed Analysis: {resource_id}", color=discord.Color.blue())
        embed.add_field(name="Instance Type", value="m5.xlarge (4 vCPU, 16 GB)", inline=True)
        embed.add_field(name="CPU (P95)", value="24.5% — Over-provisioned", inline=True)
        embed.add_field(name="Memory (P95)", value="38.2% — Over-provisioned", inline=True)
        embed.add_field(name="Network (P95)", value="125 Mbps — Adequate", inline=True)
        embed.add_field(name="Recommended", value="m5.large (Save $34.56/mo)", inline=True)
        embed.add_field(name="Confidence", value="High (90d data)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-savings-report", description="Savings report from rightsizing")
    async def rightsize_savings_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Rightsizing Savings Report", color=discord.Color.green())
        embed.add_field(name="Resources Analyzed", value="42", inline=True)
        embed.add_field(name="Downsize Recommendations", value="12 ($346/mo)", inline=True)
        embed.add_field(name="Upsize Recommendations", value="3 ($84/mo)", inline=True)
        embed.add_field(name="Net Savings", value="$262/mo ($3,144/yr)", inline=True)
        embed.add_field(name="Implementation", value="8 applied, 4 pending", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-exclude", description="Exclude resource from rightsizing")
    @app_commands.describe(resource_id="Resource ID", reason="Reason for exclusion")
    async def rightsize_exclude(self, interaction: discord.Interaction, resource_id: str, reason: str = "Pinned by policy"):
        await interaction.response.defer()
        embed = discord.Embed(title="Resource Excluded", color=discord.Color.orange())
        embed.add_field(name="Resource", value=resource_id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=48)
    async def rightsizing_scan(self):
        logging.info("Rightsizing: running resource scan")

    @rightsizing_scan.before_loop
    async def before_rightsizing_scan(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rightsize-simulate", description="Simulate rightsizing change")
    @app_commands.describe(resource_id="Resource ID", target_size="Target instance size")
    async def rightsize_simulate(self, interaction: discord.Interaction, resource_id: str, target_size: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Resize Simulation: {resource_id}", color=discord.Color.blue())
        embed.add_field(name="Current Size", value="t3.large", inline=True)
        embed.add_field(name="Target Size", value=target_size, inline=True)
        embed.add_field(name="Current Cost", value="$68.64/mo", inline=True)
        embed.add_field(name="New Cost", value="$34.32/mo", inline=True)
        embed.add_field(name="Monthly Savings", value="$34.32/mo (50%)", inline=True)
        embed.add_field(name="Annual Savings", value="$411.84/yr", inline=True)
        embed.add_field(name="Risk Level", value="Low", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-schedule", description="Schedule a resize action")
    @app_commands.describe(rec_id="Recommendation ID", execute_at="Execution time (YYYY-MM-DD HH:MM)")
    async def rightsize_schedule(self, interaction: discord.Interaction, rec_id: str, execute_at: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Resize Scheduled", color=discord.Color.green())
        embed.add_field(name="Recommendation", value=rec_id[:12], inline=True)
        embed.add_field(name="Scheduled For", value=execute_at, inline=True)
        embed.add_field(name="Status", value="Pending execution", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-approve-all", description="Approve all pending recommendations")
    async def rightsize_approve_all(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Bulk Approval", color=discord.Color.green())
        embed.add_field(name="Approved", value="12 recommendations", inline=True)
        embed.add_field(name="Estimated Savings", value="$346/mo ($4,152/yr)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rightsize-capacity-plan", description="Plan capacity with growth")
    @app_commands.describe(resource_ids="Comma-separated resource IDs", growth_pct="Expected growth %")
    async def rightsize_capacity_plan(self, interaction: discord.Interaction, resource_ids: str, growth_pct: float = 20.0):
        await interaction.response.defer()
        ids = resource_ids.split(",")
        embed = discord.Embed(title=f"Capacity Plan ({len(ids)} resources)", color=discord.Color.blue())
        embed.add_field(name="Current Total", value="$12,450/mo", inline=True)
        embed.add_field(name="Growth Projection", value=f"+{growth_pct}%", inline=True)
        embed.add_field(name="Projected Cost", value=f"${12450 * (1 + growth_pct/100):.0f}/mo", inline=True)
        embed.set_footer(text="Recommendation: Auto-scale with rightsizing")
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def rightsizing_scan_daily(self):
        logging.info("Rightsizing: daily resource analysis")

    @rightsizing_scan_daily.before_loop
    async def before_rightsizing_daily(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Rightsizing(bot))

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
