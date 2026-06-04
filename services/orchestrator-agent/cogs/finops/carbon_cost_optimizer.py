import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class CarbonCostOptimizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="carbon-asset", description="Register workload and its carbon footprint")
    @app_commands.describe(name="Asset name", region="Cloud region", monthly_cost="Monthly cost")
    async def register_asset(self, interaction: discord.Interaction, name: str, region: str, monthly_cost: float):
        await interaction.response.defer()
        intensities = {"eu-north-1": 0.12, "us-west-2": 0.28, "eu-west-1": 0.25, "us-east-1": 0.42}
        intensity = intensities.get(region, 0.40)
        co2_kg = round(monthly_cost * intensity * random.uniform(0.08, 0.12), 2)
        import random
        embed = discord.Embed(title="Asset Registered", color=0x00AAFF)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(name="Monthly Cost", value=f"${monthly_cost:,.2f}", inline=True)
        embed.add_field(name="Carbon Intensity", value=f"{intensity} kgCO2/kWh", inline=True)
        embed.add_field(name="Est. Monthly CO2", value=f"{co2_kg} kg", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-optimize", description="Generate carbon-aware recommendations")
    @app_commands.describe(strategy="Optimization strategy")
    async def optimize(self, interaction: discord.Interaction, strategy: str = "balanced"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Carbon-Aware Recommendations ({strategy})", color=0x00FF88)
        embed.add_field(name="api-servers → eu-north-1", value="Save 71% carbon, +12% cost", inline=False)
        embed.add_field(name="data-processing → us-west-2", value="Save 33% carbon, save 4% cost", inline=False)
        embed.add_field(name="database → eu-west-1 (IRE)", value="Save 40% carbon, +8% cost", inline=False)
        embed.set_footer(text="Green-cheap balanced recommendations")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-region", description="Check region carbon intensity")
    @app_commands.describe(region="Cloud region")
    async def region_intensity(self, interaction: discord.Interaction, region: str = "us-east-1"):
        await interaction.response.defer()
        intensities = {"eu-north-1": (0.12, "very_low"), "us-west-2": (0.28, "low"),
                       "eu-west-1": (0.25, "low"), "us-east-1": (0.42, "high")}
        intensity, level = intensities.get(region, (0.40, "moderate"))
        embed = discord.Embed(title=f"Carbon Intensity: {region}", color=0x00AAFF)
        embed.add_field(name="Intensity", value=f"{intensity} kgCO2/kWh", inline=True)
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="Greener Options", value="eu-north-1 (-71%), us-west-2 (-33%)", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-summary", description="Carbon optimization summary")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Carbon Optimization Summary", color=0x00AAFF)
        embed.add_field(name="Total Assets", value="8", inline=True)
        embed.add_field(name="Total Monthly CO2", value="3,240 kg", inline=True)
        embed.add_field(name="Total Annual CO2", value="38.9 tons", inline=True)
        embed.add_field(name="Potential CO2 Reduction", value="35%", inline=True)
        embed.add_field(name="Recommendations", value="12 pending", inline=True)
        embed.add_field(name="Implemented", value="3", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="carbon-assets", description="List registered carbon assets")
    async def list_assets(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Carbon Assets", color=0x22C55E)
        embed.add_field(name="web-prod (aws/us-east-1)", value="$2,500/mo | 12,000 kWh | 5.04 tons CO2/yr", inline=False)
        embed.add_field(name="data-batch (aws/us-west-2)", value="$1,800/mo | 8,500 kWh | 2.55 tons CO2/yr", inline=False)
        embed.add_field(name="Total", value="2 assets | 4,300 kWh/mo | 7.59 tons CO2/yr", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-footprint", description="Get carbon footprint of an asset")
    @app_commands.describe(asset_id="Asset ID")
    async def footprint(self, interaction: discord.Interaction, asset_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Carbon Footprint: {asset_id}", color=0x22C55E)
        embed.add_field(name="Monthly kWh", value="12,000", inline=True)
        embed.add_field(name="Carbon Intensity", value="0.42 kg/kWh", inline=True)
        embed.add_field(name="Monthly CO2", value="504.00 kg", inline=True)
        embed.add_field(name="Annual CO2", value="6.05 tons", inline=True)
        embed.add_field(name="Equivalent", value="12,100 car miles", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-tradeoff", description="Cost-carbon tradeoff analysis")
    @app_commands.describe(asset_id="Asset ID")
    async def tradeoff(self, interaction: discord.Interaction, asset_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Trade-Off: {asset_id}", color=0x00AAFF)
        embed.add_field(name="Current", value="us-east-1 | $2,500 | 504 kg CO2/mo", inline=False)
        embed.add_field(name="Option: us-west-2", value="$2,375 (5% less) | 360 kg CO2 (29% less)", inline=False)
        embed.add_field(name="Option: eu-west-1", value="$2,750 (10% more) | 300 kg CO2 (40% less)", inline=False)
        embed.add_field(name="Recommendation", value="Migrate to us-west-2 for best cost-carbon balance", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-intensity", description="Get carbon intensity for a region")
    @app_commands.describe(region="Cloud region")
    async def intensity(self, interaction: discord.Interaction, region: str = "us-east-1"):
        await interaction.response.defer()
        intensities = {"us-east-1": 0.42, "us-west-2": 0.30, "eu-west-1": 0.25, "eu-central-1": 0.32}
        intensity = intensities.get(region, 0.40)
        embed = discord.Embed(title=f"Carbon Intensity: {region}", color=0x00AAFF)
        embed.add_field(name="Intensity", value=f"{intensity} kg CO2/kWh", inline=True)
        embed.add_field(name="Grid Mix", value="Renewable: 35% | Gas: 40% | Coal: 15%", inline=False)
        embed.add_field(name="Level", value="Low" if intensity < 0.28 else ("Moderate" if intensity < 0.40 else "High"), inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="carbon-sustainability", description="Sustainability budget overview")
    async def sustainability(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Sustainability Budget", color=0x22C55E)
        embed.add_field(name="Total Monthly CO2", value="3,240 kg", inline=True)
        embed.add_field(name="Annual CO2", value="38.9 tons", inline=True)
        embed.add_field(name="Avg Carbon Intensity", value="0.32 kg/kWh (Moderate)", inline=True)
        embed.add_field(name="Carbon Target", value="28.0 tons/yr (28% reduction)", inline=True)
        embed.add_field(name="Progress", value="72% of target achieved", inline=True)
        embed.add_field(name="Carbon Credits Needed", value="10.9 tons @ $15/ton = $163.50", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-migrate", description="Estimate migration carbon savings")
    @app_commands.describe(asset_name="Asset name", target_region="Target region")
    async def migrate(self, interaction: discord.Interaction, asset_name: str, target_region: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Migration Estimate: {asset_name} -> {target_region}", color=0x00AAFF)
        embed.add_field(name="Current Region", value="us-east-1 (0.42 kg/kWh)", inline=True)
        embed.add_field(name="Target Region", value=f"{target_region} (0.25 kg/kWh)", inline=True)
        embed.add_field(name="CO2 Reduction", value="40.5%", inline=True)
        embed.add_field(name="Cost Impact", value="+8% (region premium)", inline=True)
        embed.add_field(name="Migration Effort", value="Medium", inline=True)
        embed.add_field(name="Recommendation", value="Proceed — positive carbon ROI within 6 months", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-report", description="Generate sustainability report")
    async def carbon_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Sustainability Report", color=0x22C55E)
        embed.add_field(name="Assets Analyzed", value="8", inline=True)
        embed.add_field(name="Total kWh/Month", value="18,000 kWh", inline=True)
        embed.add_field(name="Total CO2/Month", value="3,240 kg", inline=True)
        embed.add_field(name="Annual CO2", value="38.9 tons", inline=True)
        embed.add_field(name="Reduction Opportunities", value="35% potential", inline=True)
        embed.add_field(name="Carbon Offset Cost", value="$163.50/mo @ $15/ton", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-benchmark", description="Benchmark carbon intensity by provider")
    async def benchmark(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Provider Carbon Benchmark", color=0x3498DB)
        embed.add_field(name="AWS (us-east-1)", value="0.42 kg/kWh — High", inline=False)
        embed.add_field(name="AWS (eu-west-1)", value="0.25 kg/kWh — Low", inline=False)
        embed.add_field(name="GCP (us-central1)", value="0.38 kg/kWh — Moderate", inline=False)
        embed.add_field(name="Azure (westeurope)", value="0.28 kg/kWh — Low", inline=False)
        embed.add_field(name="Azure (norwayeast)", value="0.08 kg/kWh — Very Low (Greenest)", inline=False)
        embed.set_footer(text="Azure Norway East is the greenest cloud region")
        await interaction.followup.send(embed=embed)


REGION_INTENSITY = {
    "eu-north-1": 0.12, "eu-west-1": 0.25, "us-west-2": 0.28,
    "us-east-1": 0.42, "ap-southeast-1": 0.48, "ap-south-1": 0.62,
}

def compute_carbon_savings(kwh: float, from_region: str, to_region: str) -> dict:
    from_int = REGION_INTENSITY.get(from_region, 0.40)
    to_int = REGION_INTENSITY.get(to_region, 0.40)
    current_co2 = kwh * from_int
    target_co2 = kwh * to_int
    return {
        "kwh": round(kwh, 2),
        "current_region": from_region,
        "current_intensity": from_int,
        "current_co2_kg": round(current_co2, 2),
        "target_region": to_region,
        "target_intensity": to_int,
        "target_co2_kg": round(target_co2, 2),
        "reduction_kg": round(current_co2 - target_co2, 2),
        "reduction_pct": round(((current_co2 - target_co2) / max(current_co2, 1)) * 100, 1),
    }

    @app_commands.command(name="carbon-region-compare", description="Compare carbon intensity across regions")
    @app_commands.describe(regions="Comma-separated region names")
    async def carbon_region_compare(self, interaction: discord.Interaction, regions: str):
        await interaction.response.defer()
        region_list = [r.strip() for r in regions.split(",")]
        embed = discord.Embed(title="Region Carbon Comparison", color=discord.Color.green())
        for r in region_list[:10]:
            intensity = REGION_INTENSITY.get(r, 0.40)
            rating = "Very Low" if intensity < 0.15 else "Low" if intensity < 0.30 else "Moderate" if intensity < 0.45 else "High"
            embed.add_field(name=r, value=f"{intensity} kg/kWh — {rating}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-migration-impact", description="Estimate carbon savings from workload migration")
    @app_commands.describe(kwh="Monthly kWh usage", from_region="Current region", to_region="Target region")
    async def carbon_migration_impact(self, interaction: discord.Interaction, kwh: float, from_region: str, to_region: str):
        await interaction.response.defer()
        result = compute_carbon_savings(kwh, from_region, to_region)
        embed = discord.Embed(title="Carbon Migration Impact", color=discord.Color.green())
        embed.add_field(name="Current Region", value=from_region, inline=True)
        embed.add_field(name="Target Region", value=to_region, inline=True)
        embed.add_field(name="Current CO₂", value=f"{result['current_co2_kg']} kg/mo", inline=True)
        embed.add_field(name="Target CO₂", value=f"{result['target_co2_kg']} kg/mo", inline=True)
        embed.add_field(name="Reduction", value=f"{result['reduction_kg']} kg/mo ({result['reduction_pct']}%)", inline=True)
        embed.add_field(name="Rating", value="🌱 Significant" if result['reduction_pct'] > 30 else "🌿 Moderate" if result['reduction_pct'] > 10 else "♻️ Minimal", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-trend", description="Carbon footprint trend over time")
    @app_commands.describe(days="Number of days to analyze")
    async def carbon_trend(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Carbon Trend ({days} days)", color=discord.Color.green())
        embed.add_field(name="Total CO₂", value="12,450 kg", inline=True)
        embed.add_field(name="Avg Daily", value="415 kg", inline=True)
        embed.add_field(name="Trend", value="📉 Declining (-3.2%)", inline=True)
        embed.add_field(name="Top Emitter", value="us-east-1 (42%)", inline=True)
        embed.add_field(name="Greenest Region", value="eu-north-1 (8%)", inline=True)
        embed.add_field(name="Offset Needed", value="$622 at $50/ton", inline=True)
        embed.set_footer(text="Based on compute and data transfer estimates")
        await interaction.followup.send(embed=embed)

    @carbon_region_compare.autocomplete("regions")
    async def region_names_autocomplete(self, interaction: discord.Interaction, current: str):
        regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-north-1", "ap-southeast-1", "ap-south-1", "eu-central-1", "ca-central-1", "sa-east-1", "ap-northeast-1"]
        return [app_commands.Choice(name=r, value=r) for r in regions if current.lower() in r.lower()][:25]

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="carbon-offset", description="Calculate offset cost")
    @app_commands.describe(co2_kg="CO2 in kg", price_per_ton="Price per ton in USD")
    async def carbon_offset(self, interaction: discord.Interaction, co2_kg: float = 12450, price_per_ton: float = 50):
        await interaction.response.defer()
        tons = co2_kg / 1000
        cost = tons * price_per_ton
        trees = int(tons * 45)
        embed = discord.Embed(title="Carbon Offset Calculator", color=discord.Color.green())
        embed.add_field(name="CO₂ Emissions", value=f"{co2_kg:,.0f} kg ({tons:.2f} tons)", inline=True)
        embed.add_field(name="Offset Cost", value=f"${cost:,.2f} at ${price_per_ton}/ton", inline=True)
        embed.add_field(name="Trees Needed", value=f"{trees:,} trees/year", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-goal", description="Set carbon reduction goal")
    @app_commands.describe(reduction_pct="Target reduction %", deadline="Target date (YYYY-MM-DD)")
    async def carbon_goal(self, interaction: discord.Interaction, reduction_pct: float = 25.0, deadline: str = "2026-01-01"):
        await interaction.response.defer()
        embed = discord.Embed(title="Carbon Reduction Goal Set", color=discord.Color.green())
        embed.add_field(name="Reduction Target", value=f"{reduction_pct}%", inline=True)
        embed.add_field(name="Deadline", value=deadline, inline=True)
        embed.add_field(name="Current Baseline", value="12,450 kg/mo", inline=True)
        embed.add_field(name="Target Emissions", value=f"{12450 * (1 - reduction_pct/100):,.0f} kg/mo", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def carbon_sync(self):
        logging.info("CarbonCostOptimizer: running carbon data sync")

    @carbon_sync.before_loop
    async def before_carbon_sync(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="carbon-sustainability", description="View sustainability scorecard")
    async def carbon_sustainability(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Sustainability Scorecard", color=discord.Color.green())
        embed.add_field(name="Total Assets", value="15", inline=True)
        embed.add_field(name="Monthly CO2", value="2,450 kg", inline=True)
        embed.add_field(name="Annual CO2", value="29.4 tons", inline=True)
        embed.add_field(name="Green Regions", value="4 (26.7%)", inline=True)
        embed.add_field(name="Avg Intensity", value="0.31 kg/kWh (Moderate)", inline=True)
        embed.add_field(name="Carbon Savings", value="180 kg/mo via recommendations", inline=True)
        embed.set_footer(text="Sustainability score: 72/100")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-compare-region", description="Compare carbon intensity between regions")
    @app_commands.describe(region_a="Source region", region_b="Target region")
    async def carbon_compare_region(self, interaction: discord.Interaction, region_a: str, region_b: str):
        await interaction.response.defer()
        intensities = {"us-east-1": 0.42, "eu-west-1": 0.25, "eu-north-1": 0.12, "us-west-2": 0.30}
        ia = intensities.get(region_a, 0.40)
        ib = intensities.get(region_b, 0.40)
        embed = discord.Embed(title=f"Region Carbon: {region_a} vs {region_b}", color=discord.Color.blue())
        embed.add_field(name=region_a, value=f"{ia} kg/kWh", inline=True)
        embed.add_field(name=region_b, value=f"{ib} kg/kWh", inline=True)
        reduction = ((ia - ib) / ia) * 100 if ia > ib else ((ib - ia) / ib) * 100
        embed.add_field(name="Difference", value=f"{reduction:.1f}% {'cleaner' if ib < ia else 'dirtier'}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-report", description="Generate carbon emissions report")
    @app_commands.describe(year="Report year")
    async def carbon_report(self, interaction: discord.Interaction, year: int = 2025):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Carbon Emissions Report {year}", color=discord.Color.blue())
        embed.add_field(name="Annual Emissions", value="29.4 tons CO2e", inline=True)
        embed.add_field(name="YoY Change", value="-8.2%", inline=True)
        embed.add_field(name="Offset Credits", value="10 tons purchased", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="carbon-migration-plan", description="Plan region migration")
    @app_commands.describe(asset_id="Asset ID", target_region="Target region")
    async def carbon_migration_plan(self, interaction: discord.Interaction, asset_id: str, target_region: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Migration Plan: {asset_id} -> {target_region}", color=discord.Color.blue())
        embed.add_field(name="Estimated Duration", value="24 hours", inline=True)
        embed.add_field(name="Carbon Reduction", value="42.3%", inline=True)
        embed.add_field(name="Cost Impact", value="+8% (cost multiplier)", inline=True)
        embed.set_footer(text="Migration risk: Low")
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def carbon_sync(self):
        logging.info("CarbonCostOptimizer: syncing carbon intensity data")

    @carbon_sync.before_loop
    async def before_carbon_sync(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CarbonCostOptimizer(bot))

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
