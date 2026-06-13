import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class SLAManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="sla_list", description="List SLA agreements")
    async def sla_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/sla/templates")
        templates = data if isinstance(data, list) else data.get("templates", [])
        if not templates:
            await interaction.followup.send(embed=discord.Embed(description="No SLA templates.", color=0xFFFF00))
            return
        embed = discord.Embed(title="SLA Templates", color=discord.Color.blue(), timestamp=datetime.now())
        for t in templates[:10]:
            embed.add_field(name=t.get("name", "Unknown"), value=f"Uptime: {t.get('uptime_target', 0)}% | Response: {t.get('response_time_mins', 0)}min | Credit: {t.get('credit_percent', 0)}%/incident", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sla_create", description="Create an SLA agreement")
    @app_commands.describe(name="SLA name", uptime="Uptime target %", response_mins="Response time in minutes", credit_percent="Credit percentage per incident", max_credit="Max monthly credit %", price_monthly="Monthly price")
    async def sla_create(self, interaction: discord.Interaction, name: str, uptime: float = 99.9, response_mins: int = 15, credit_percent: float = 5.0, max_credit: float = 100.0, price_monthly: float = 0):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/sla/templates", {"name": name, "uptime_target": uptime, "response_time_mins": response_mins, "credit_percent": credit_percent, "max_monthly_credit_percent": max_credit, "price_monthly": price_monthly})
        if "id" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"SLA {name} created ({uptime}% uptime target).", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="sla_status", description="Check SLA status")
    @app_commands.describe(sla_id="SLA ID")
    async def sla_status(self, interaction: discord.Interaction, sla_id: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/marketplace/sla/status/{sla_id}")
        embed = discord.Embed(title=f"SLA Status: {sla_id}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Uptime", value=f"{result.get('current_uptime', 0):.4f}%", inline=True)
        embed.add_field(name="Target", value=f"{result.get('uptime_target', 0)}%", inline=True)
        embed.add_field(name="Status", value=result.get("status", "unknown"), inline=True)
        embed.add_field(name="Credits Issued", value=f"${result.get('credits_issued', 0):.2f}", inline=True)
        embed.add_field(name="Monthly Credits", value=f"${result.get('monthly_credits', 0):.2f}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sla_credits", description="View SLA credits history")
    async def sla_credits(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/sla/credits")
        credits = data if isinstance(data, list) else data.get("credits", [])
        if not credits:
            await interaction.followup.send(embed=discord.Embed(description="No SLA credits issued.", color=0xFFFF00))
            return
        embed = discord.Embed(title="SLA Credits", color=discord.Color.blue(), timestamp=datetime.now())
        for c in credits[:10]:
            embed.add_field(name=f"${c.get('amount', 0):.2f} - {c.get('reason', 'N/A')}", value=f"Issued: {c.get('issued_at', 'N/A')} | Status: {c.get('status', 'unknown')}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SLAManagement(bot))
