import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class NetworkCostAnalyzer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="netcost_summary", description="Show network cost summary")
    async def netcost_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.get("/api/networking/cost/summary")
        embed = discord.Embed(title="Network Cost Summary", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Month", value=f"${result.get('current_month', 0):.2f}", inline=True)
        embed.add_field(name="Previous Month", value=f"${result.get('previous_month', 0):.2f}", inline=True)
        embed.add_field(name="Trend", value=result.get("trend", "stable"), inline=True)
        embed.add_field(name="Forecast (Next Month)", value=f"${result.get('forecast', 0):.2f}", inline=True)
        embed.add_field(name="95th Percentile", value=f"{result.get('percentile_95', 0):.2f} Mbps", inline=True)
        embed.add_field(name="Total Transfer", value=f"{result.get('total_transfer_gb', 0):.2f} GB", inline=True)
        providers = result.get("provider_breakdown", {})
        if providers:
            embed.add_field(name="Provider Breakdown", value="\n".join(f"{k}: ${v:.2f}" for k, v in providers.items()), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="netcost_providers", description="List provider pricing")
    async def netcost_providers(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/cost/providers")
        providers = data if isinstance(data, list) else data.get("providers", [])
        if not providers:
            await interaction.followup.send(embed=discord.Embed(description="No providers configured.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Provider Pricing", color=discord.Color.blue(), timestamp=datetime.now())
        for p in providers[:10]:
            embed.add_field(name=p.get("name", "Unknown"), value=f"Per GB: ${p.get('price_per_gb', 0):.4f} | Monthly: ${p.get('monthly_fee', 0):.2f} | BW: {p.get('included_bandwidth_gb', 0)}GB", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="netcost_alerts", description="List cost alerts")
    async def netcost_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/cost/alerts")
        alerts = data if isinstance(data, list) else data.get("alerts", [])
        if not alerts:
            await interaction.followup.send(embed=discord.Embed(description="No cost alerts.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Network Cost Alerts", color=discord.Color.blue(), timestamp=datetime.now())
        for a in alerts[:10]:
            severity_icon = "🔴" if a.get("severity") == "critical" else "🟡" if a.get("severity") == "warning" else "🔵"
            embed.add_field(name=f"{severity_icon} {a.get('name', 'Alert')}", value=f"Threshold: ${a.get('threshold', 0):.2f} | Current: ${a.get('current', 0):.2f} | Status: {a.get('status', 'unknown')}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NetworkCostAnalyzer(bot))
