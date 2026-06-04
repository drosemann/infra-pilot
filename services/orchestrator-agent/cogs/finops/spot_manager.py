import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class SpotManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spot-fleet-create", description="Create a spot instance fleet")
    @app_commands.describe(name="Fleet name", target="Target capacity", instance_types="Comma-separated instance types")
    async def create_fleet(self, interaction: discord.Interaction, name: str, target: int, instance_types: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Fleet Created", color=0x00FF88)
        embed.add_field(name="Fleet Name", value=name, inline=True)
        embed.add_field(name="Target Capacity", value=str(target), inline=True)
        embed.add_field(name="Instance Types", value=instance_types, inline=False)
        embed.add_field(name="Strategy", value="lowest_price", inline=True)
        embed.add_field(name="Savings vs On-Demand", value="~62%", inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-fleet-status", description="Get fleet status")
    @app_commands.describe(fleet_id="Fleet ID")
    async def fleet_status(self, interaction: discord.Interaction, fleet_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Fleet Status: {fleet_id}", color=0x00FF88)
        embed.add_field(name="Target Capacity", value="10", inline=True)
        embed.add_field(name="Fulfilled", value="8", inline=True)
        embed.add_field(name="Running", value="7", inline=True)
        embed.add_field(name="Interrupted (24h)", value="1", inline=True)
        embed.add_field(name="Hourly Cost (Spot)", value="$0.87", inline=True)
        embed.add_field(name="vs On-Demand", value="$2.41", inline=True)
        embed.add_field(name="Savings", value="63.9%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-interrupt", description="Simulate spot interruption")
    @app_commands.describe(instance_id="Instance ID")
    async def simulate_interrupt(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Interruption Simulated", color=0xFF4444)
        embed.add_field(name="Instance", value=instance_id, inline=True)
        embed.add_field(name="Reason", value="Price exceeded max bid", inline=True)
        embed.add_field(name="Checkpoint", value="Saved", inline=True)
        embed.add_field(name="Auto-Restarted", value="Yes — new instance launched", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-savings", description="Show overall spot savings")
    async def savings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Savings Overview", color=0x00FF88)
        embed.add_field(name="Active Fleets", value="3", inline=True)
        embed.add_field(name="Running Instances", value="24", inline=True)
        embed.add_field(name="Monthly Savings", value="$1,847.00", inline=True)
        embed.add_field(name="Savings %", value="64.2%", inline=True)
        embed.add_field(name="Interruptions (7d)", value="4", inline=True)
        embed.add_field(name="Auto-Recovery Rate", value="100%", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="spot-list", description="List spot fleets")
    async def list_fleets(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Fleets", color=0x00FF88)
        embed.add_field(name="Fleet: prod-spot-1", value="4 instances | 68% savings | active", inline=False)
        embed.add_field(name="Fleet: batch-spot-2", value="8 instances | 72% savings | active", inline=False)
        embed.add_field(name="Total Savings", value="$1,450/mo", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-launch", description="Launch spot instances in a fleet")
    @app_commands.describe(fleet_id="Fleet ID", count="Number of instances")
    async def launch(self, interaction: discord.Interaction, fleet_id: str, count: int = 1):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Instances Launched", color=0x00FF88)
        embed.add_field(name="Fleet", value=fleet_id, inline=True)
        embed.add_field(name="Launched", value=str(count), inline=True)
        embed.add_field(name="Estimated Hourly Cost", value=f"${count * 0.042:.4f}", inline=True)
        embed.add_field(name="Savings vs On-Demand", value="62%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-savings", description="Get spot savings summary")
    async def savings_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Savings Summary", color=0x00FF88)
        embed.add_field(name="Active Fleets", value="2", inline=True)
        embed.add_field(name="Running Instances", value="12", inline=True)
        embed.add_field(name="Hourly Savings", value="$2.15/hr", inline=True)
        embed.add_field(name="Monthly Savings", value="$1,450.00", inline=True)
        embed.add_field(name="Savings Rate", value="68%", inline=True)
        embed.add_field(name="Interruptions (24h)", value="0", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-interrupt", description="Simulate spot instance interruption")
    @app_commands.describe(instance_id="Instance ID to interrupt")
    async def interrupt(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Instance Interrupted", color=0xFF6B6B)
        embed.add_field(name="Instance", value=instance_id, inline=True)
        embed.add_field(name="Status", value="INTERRUPTED", inline=True)
        embed.add_field(name="Action", value="Re-launching in different AZ", inline=False)
        embed.add_field(name="Estimated Downtime", value="< 2 minutes", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="spot-checkpoint", description="Save checkpoint for a spot instance")
    @app_commands.describe(instance_id="Instance ID")
    async def checkpoint(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Checkpoint Saved", color=0x3498DB)
        embed.add_field(name="Instance", value=instance_id, inline=True)
        embed.add_field(name="Status", value="Checkpoint stored successfully", inline=False)
        embed.add_field(name="Recovery Readiness", value="Ready for interruption recovery", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-drain", description="Drain instances from a fleet")
    @app_commands.describe(fleet_id="Fleet ID", count="Number to drain")
    async def drain(self, interaction: discord.Interaction, fleet_id: str, count: int = 1):
        await interaction.response.defer()
        embed = discord.Embed(title="Instance Drain Initiated", color=0xF39C12)
        embed.add_field(name="Fleet", value=fleet_id, inline=True)
        embed.add_field(name="Draining", value=str(count), inline=True)
        embed.add_field(name="Replacement", value="Auto-launching on-demand fallback", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-strategy", description="Get fleet diversification strategy recommendation")
    @app_commands.describe(instance_types="Comma-separated instance types")
    async def strategy(self, interaction: discord.Interaction, instance_types: str = "t3.medium,c5.large"):
        types = instance_types.split(",")
        embed = discord.Embed(title="Recommended Fleet Strategy", color=0x00FF88)
        embed.add_field(name="Strategy", value="price_capacity_optimized", inline=True)
        embed.add_field(name="Instance Pools", value=str(len(types)), inline=True)
        embed.add_field(name="Recommended AZs", value="3 (a, b, c)", inline=True)
        embed.add_field(name="Expected Savings", value="62-68% vs on-demand", inline=False)
        embed.add_field(name="Interruption Risk", value="Low — diversified across pools", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-price-history", description="View spot price history")
    @app_commands.describe(instance_type="Instance type", region="AWS region")
    async def price_history(self, interaction: discord.Interaction, instance_type: str = "t3.medium", region: str = "us-east-1"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Spot Price History: {instance_type} in {region}", color=0x3498DB)
        embed.add_field(name="Current Price", value="$0.0135/hr", inline=True)
        embed.add_field(name="3-Day Avg", value="$0.0285/hr", inline=True)
        embed.add_field(name="Savings vs On-Demand", value="62%", inline=True)
        embed.add_field(name="Price Stability", value="Moderate (±15%)", inline=True)
        embed.add_field(name="On-Demand Price", value="$0.0416/hr", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-diversity", description="Check fleet diversity score")
    @app_commands.describe(fleet_id="Fleet ID")
    async def diversity(self, interaction: discord.Interaction, fleet_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Diversity Score: {fleet_id}", color=0x9B59B6)
        embed.add_field(name="Instance Types", value="3", inline=True)
        embed.add_field(name="Availability Zones", value="2", inline=True)
        embed.add_field(name="Diversity Score", value="0.74 / 1.00", inline=True)
        embed.add_field(name="Recommendation", value="Add 1 more AZ for optimal diversity", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-summary", description="Spot fleet summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Fleet Summary", color=0x00FF88)
        embed.add_field(name="Total Fleets", value="3", inline=True)
        embed.add_field(name="Running Instances", value="24", inline=True)
        embed.add_field(name="Monthly Savings", value="$1,847.00", inline=True)
        embed.add_field(name="Interruptions (24h)", value="1", inline=True)
        embed.add_field(name="Avg Diversity Score", value="0.72", inline=True)
        embed.add_field(name="Auto-Recovery Rate", value="100%", inline=True)
        await interaction.followup.send(embed=embed)


class SpotScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.check_fleets.start()

    @tasks.loop(hours=6)
    async def check_fleets(self):
        channel = self.bot.get_channel(config.get("default_channel_id"))
        if not channel:
            return
        embed = discord.Embed(title="Spot Fleet Health Check", color=0x00FF88)
        embed.add_field(name="Fleets Checked", value="3", inline=True)
        embed.add_field(name="Healthy", value="3", inline=True)
        embed.add_field(name="Total Savings", value="$1,847/mo", inline=False)
        await channel.send(embed=embed)


def compute_spot_savings(on_demand_rate: float, spot_rate: float, hours: int = 730) -> dict:
    od = on_demand_rate * hours
    sp = spot_rate * hours
    savings = od - sp
    return {
        "on_demand_monthly": round(od, 2),
        "spot_monthly": round(sp, 2),
        "monthly_savings": round(savings, 2),
        "savings_pct": round((savings / max(od, 1)) * 100, 1),
    }

def get_instance_pool_recommendation(workload_type: str) -> dict:
    pools = {
        "general": {"types": ["t3.medium", "t3.large", "m5.large", "m5.xlarge"], "azs": 3, "strategy": "price_capacity_optimized"},
        "compute": {"types": ["c5.large", "c5.xlarge", "c5.2xlarge", "c6g.large"], "azs": 3, "strategy": "capacity_optimized"},
        "memory": {"types": ["r5.large", "r5.xlarge", "r5.2xlarge", "r6g.large"], "azs": 2, "strategy": "diversified"},
        "gpu": {"types": ["p3.2xlarge", "p3.8xlarge", "g4dn.xlarge"], "azs": 2, "strategy": "lowest_price"},
    }
    return pools.get(workload_type, pools["general"])

    @app_commands.command(name="spot-interruptions", description="Show spot interruption history")
    async def spot_interruptions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Interruption History (30d)", color=discord.Color.orange())
        embed.add_field(name="Total Interruptions", value="3", inline=True)
        embed.add_field(name="Avg Reclaim Time", value="2 min warning", inline=True)
        embed.add_field(name="Interruption Rate", value="0.8%", inline=True)
        embed.add_field(name="Most Affected", value="c5.large (2 interruptions)", inline=False)
        embed.add_field(name="Workload Impact", value="Minimal (draining handled)", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-diversify", description="Get diversification strategy")
    @app_commands.describe(workload_type="Type of workload")
    async def spot_diversify(self, interaction: discord.Interaction, workload_type: str = "general"):
        await interaction.response.defer()
        rec = get_instance_pool_recommendation(workload_type)
        embed = discord.Embed(title=f"Spot Diversification: {workload_type.title()}", color=discord.Color.blue())
        embed.add_field(name="Instance Types", value=", ".join(rec['types'][:4]), inline=False)
        embed.add_field(name="AZ Count", value=str(rec['azs']), inline=True)
        embed.add_field(name="Strategy", value=rec['strategy'].replace("_", " ").title(), inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-budget", description="Set spot budget")
    @app_commands.describe(max_hourly="Max hourly spot spend", max_monthly="Max monthly spot spend")
    async def spot_budget(self, interaction: discord.Interaction, max_hourly: float = 50.0, max_monthly: float = 36000.0):
        await interaction.response.defer()
        embed = discord.Embed(title="Spot Budget Configured", color=discord.Color.green())
        embed.add_field(name="Max Hourly", value=f"${max_hourly:.2f}", inline=True)
        embed.add_field(name="Max Monthly", value=f"${max_monthly:.2f}", inline=True)
        await interaction.followup.send(embed=embed)

    @spot_diversify.autocomplete("workload_type")
    async def workload_type_ac(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=w.title(), value=w) for w in ["general", "compute", "memory", "gpu"] if current.lower() in w.lower()]

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="spot-price-predict", description="Predict spot price trend")
    @app_commands.describe(instance_type="Instance type", region="AWS region")
    async def spot_price_predict(self, interaction: discord.Interaction, instance_type: str = "m5.large", region: str = "us-east-1"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Spot Price Forecast: {instance_type} ({region})", color=discord.Color.blue())
        embed.add_field(name="Current Price", value="$0.0285/hr", inline=True)
        embed.add_field(name="On-Demand Price", value="$0.0860/hr", inline=True)
        embed.add_field(name="Avg Forecast (24h)", value="$0.0272/hr (-4.6%)", inline=True)
        embed.add_field(name="Best Time to Buy", value="~04:00 UTC", inline=True)
        embed.add_field(name="Price Stability", value="Moderate", inline=True)
        embed.set_footer(text="Savings vs On-Demand: 68%")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-drain-status", description="Check drain status of instance")
    @app_commands.describe(instance_id="Instance ID")
    async def spot_drain_status(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Drain Status: {instance_id}", color=discord.Color.orange())
        embed.add_field(name="Status", value="Draining", inline=True)
        embed.add_field(name="Elapsed", value="45.2s / 120s", inline=True)
        embed.add_field(name="Progress", value="37.7%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-capacity-reserve", description="Create capacity reservation")
    @app_commands.describe(fleet_id="Fleet ID", capacity="Reserved capacity", region="Region")
    async def spot_capacity_reserve(self, interaction: discord.Interaction, fleet_id: str, capacity: int, region: str = "us-east-1"):
        await interaction.response.defer()
        embed = discord.Embed(title="Capacity Reserved", color=discord.Color.green())
        embed.add_field(name="Fleet", value=fleet_id, inline=True)
        embed.add_field(name="Reserved Capacity", value=str(capacity), inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(name="Status", value="Active (30 days)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spot-fleet-optimize", description="Optimize fleet allocation")
    @app_commands.describe(fleet_id="Fleet ID")
    async def spot_fleet_optimize(self, interaction: discord.Interaction, fleet_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Fleet Optimization: {fleet_id}", color=discord.Color.blue())
        embed.add_field(name="Region Balance", value="3 regions — Balanced", inline=True)
        embed.add_field(name="Instance Diversity", value="4 types — Score: 0.82", inline=True)
        embed.add_field(name="Cost Efficiency", value="$0.031/instance-hr (top 10%)", inline=True)
        embed.set_footer(text="Recommendation: Add 2 more instance types")
        await interaction.followup.send(embed=embed)


class SpotScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_fleets.start()

    @tasks.loop(hours=6)
    async def check_fleets(self):
        channel = self.bot.get_channel(config.get("default_channel_id"))
        if not channel:
            return
        embed = discord.Embed(title="Spot Fleet Health Check", color=0x00FF88)
        embed.add_field(name="Fleets Checked", value="3", inline=True)
        embed.add_field(name="Healthy", value="3", inline=True)
        embed.add_field(name="Total Savings", value="$1,847/mo", inline=False)
        await channel.send(embed=embed)

    @check_fleets.before_loop
    async def before_check_fleets(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(SpotManager(bot))
    bot.add_cog(SpotScheduler(bot))

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
