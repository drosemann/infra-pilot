import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class PayPerUseBilling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="ppu_usage", description="Show pay-per-use usage")
    async def ppu_usage(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.get("/api/marketplace/ppu/usage")
        embed = discord.Embed(title="Pay-Per-Use Usage", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Period", value=f"${result.get('current_period', 0):.4f}", inline=True)
        embed.add_field(name="CPU Seconds", value=f"{result.get('cpu_seconds', 0):.2f}", inline=True)
        embed.add_field(name="RAM GB-Hours", value=f"{result.get('ram_gb_hours', 0):.2f}", inline=True)
        embed.add_field(name="Storage GB-Hours", value=f"{result.get('storage_gb_hours', 0):.2f}", inline=True)
        embed.add_field(name="Bandwidth GB", value=f"{result.get('bandwidth_gb', 0):.2f}", inline=True)
        embed.add_field(name="Rate", value=f"${result.get('rate_per_second', 0):.6f}/sec", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ppu_invoices", description="List pay-per-use invoices")
    async def ppu_invoices(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/ppu/invoices")
        invoices = data if isinstance(data, list) else data.get("invoices", [])
        if not invoices:
            await interaction.followup.send(embed=discord.Embed(description="No invoices.", color=0xFFFF00))
            return
        embed = discord.Embed(title="PPU Invoices", color=discord.Color.blue(), timestamp=datetime.now())
        for inv in invoices[:10]:
            paid_icon = "✅" if inv.get("paid") else "⏳"
            embed.add_field(name=f"{paid_icon} {inv.get('period', 'N/A')}", value=f"Amount: ${inv.get('amount', 0):.2f} | Due: {inv.get('due_date', 'N/A')} | Status: {inv.get('status', 'unknown')}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ppu_rates", description="Show current pay-per-use rates")
    async def ppu_rates(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.get("/api/marketplace/ppu/rates")
        embed = discord.Embed(title="Pay-Per-Use Rates", color=discord.Color.blue(), timestamp=datetime.now())
        rates = result.get("rates", {})
        for k, v in rates.items():
            embed.add_field(name=k.replace("_", " ").title(), value=f"${v:.6f}/unit", inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PayPerUseBilling(bot))
