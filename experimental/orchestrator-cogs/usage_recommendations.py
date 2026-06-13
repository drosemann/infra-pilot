import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class UsageRecommendations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="recommend_analyze", description="Analyze usage and get recommendations")
    @app_commands.describe(server_id="Server ID to analyze")
    async def recommend_analyze(self, interaction: discord.Interaction, server_id: str = ""):
        await interaction.response.defer()
        params = f"?server_id={server_id}" if server_id else ""
        result = await self.api.get(f"/api/marketplace/recommendations/analyze{params}")
        embed = discord.Embed(title="Usage Analysis", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="CPU Usage Avg", value=f"{result.get('cpu_avg', 0):.1f}%", inline=True)
        embed.add_field(name="RAM Usage Avg", value=f"{result.get('ram_avg', 0):.1f}%", inline=True)
        embed.add_field(name="Storage Usage", value=f"{result.get('storage_used_gb', 0):.1f}GB", inline=True)
        embed.add_field(name="Efficiency Score", value=f"{result.get('efficiency_score', 0):.1f}/100", inline=True)
        embed.add_field(name="Wasted Resources", value=f"${result.get('wasted_cost', 0):.2f}/mo", inline=True)
        suggestions = result.get("recommendations", [])
        if suggestions:
            embed.add_field(name="Recommendations", value="\n".join(f"• {s}" for s in suggestions[:5]), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="recommend_upgrade", description="Check if you should upgrade")
    @app_commands.describe(server_id="Server ID")
    async def recommend_upgrade(self, interaction: discord.Interaction, server_id: str = ""):
        await interaction.response.defer()
        params = f"?server_id={server_id}" if server_id else ""
        result = await self.api.get(f"/api/marketplace/recommendations/upgrade{params}")
        embed = discord.Embed(title="Upgrade Recommendation", color=discord.Color.blue(), timestamp=datetime.now())
        if result.get("should_upgrade"):
            embed.add_field(name="Recommended Plan", value=result.get("recommended_plan", "N/A"), inline=True)
            embed.add_field(name="Reason", value=result.get("reason", "N/A"), inline=True)
            embed.add_field(name="Cost Increase", value=f"${result.get('cost_increase', 0):.2f}/mo", inline=True)
        else:
            embed.add_field(name="Verdict", value=result.get("message", "No upgrade needed"), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="recommend_downgrade", description="Check if you should downgrade")
    @app_commands.describe(server_id="Server ID")
    async def recommend_downgrade(self, interaction: discord.Interaction, server_id: str = ""):
        await interaction.response.defer()
        params = f"?server_id={server_id}" if server_id else ""
        result = await self.api.get(f"/api/marketplace/recommendations/downgrade{params}")
        embed = discord.Embed(title="Downgrade Recommendation", color=discord.Color.blue(), timestamp=datetime.now())
        if result.get("should_downgrade"):
            embed.add_field(name="Recommended Plan", value=result.get("recommended_plan", "N/A"), inline=True)
            embed.add_field(name="Savings", value=f"${result.get('savings', 0):.2f}/mo", inline=True)
            embed.add_field(name="Reason", value=result.get("reason", "N/A"), inline=False)
        else:
            embed.add_field(name="Verdict", value=result.get("message", "No downgrade needed"), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UsageRecommendations(bot))
