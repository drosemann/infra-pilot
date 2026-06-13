import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class SubscriptionPlans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="plan_list", description="List subscription plans")
    async def plan_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/plans")
        plans = data if isinstance(data, list) else data.get("plans", [])
        if not plans:
            await interaction.followup.send(embed=discord.Embed(description="No plans.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Subscription Plans", color=discord.Color.blue(), timestamp=datetime.now())
        for p in plans:
            embed.add_field(name=f"{p.get('name', 'Unknown')} - ${p.get('price_monthly', 0):.2f}/mo", value=f"CPU: {p.get('cpu_cores', 0)} cores | RAM: {p.get('ram_gb', 0)}GB | Storage: {p.get('storage_gb', 0)}GB | BW: {p.get('bandwidth_tb', 0)}TB/mo", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="plan_subscribe", description="Subscribe to a plan")
    @app_commands.describe(plan_id="Plan ID")
    async def plan_subscribe(self, interaction: discord.Interaction, plan_id: str):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/plans/subscribe", {"plan_id": plan_id})
        if result.get("status") == "active":
            embed = discord.Embed(title="Subscribed", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Plan", value=result.get("plan_name", plan_id))
            embed.add_field(name="Next Billing", value=result.get("next_billing", "N/A"))
            embed.add_field(name="Status", value=result.get("status", "active"))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="plan_switch", description="Switch subscription plan")
    @app_commands.describe(new_plan_id="New plan ID")
    async def plan_switch(self, interaction: discord.Interaction, new_plan_id: str):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/plans/switch", {"new_plan_id": new_plan_id})
        if result.get("status") == "switched":
            embed = discord.Embed(title="Plan Switched", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="New Plan", value=result.get("new_plan", new_plan_id))
            embed.add_field(name="Prorated Credit", value=f"${result.get('prorated_credit', 0):.2f}")
            embed.add_field(name="Next Billing", value=result.get("next_billing", "N/A"))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="plan_cancel", description="Cancel subscription")
    async def plan_cancel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/plans/cancel", {})
        if result.get("status") == "cancelled":
            await interaction.followup.send(embed=discord.Embed(description=f"Subscription cancelled. Active until {result.get('active_until', 'N/A')}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="plan_addons", description="List available addons")
    async def plan_addons(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/plans/addons")
        addons = data if isinstance(data, list) else data.get("addons", [])
        if not addons:
            await interaction.followup.send(embed=discord.Embed(description="No addons available.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Plan Addons", color=discord.Color.blue(), timestamp=datetime.now())
        for a in addons:
            embed.add_field(name=f"{a.get('name', 'Unknown')} - ${a.get('price_monthly', 0):.2f}/mo", value=a.get("description", ""), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SubscriptionPlans(bot))
