import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class ResellerWhitelabel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="reseller_list", description="List resellers")
    async def reseller_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/resellers")
        resellers = data if isinstance(data, list) else data.get("resellers", [])
        if not resellers:
            await interaction.followup.send(embed=discord.Embed(description="No resellers.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Resellers", color=discord.Color.blue(), timestamp=datetime.now())
        for r in resellers[:10]:
            embed.add_field(name=r.get("name", "Unknown"), value=f"Email: {r.get('email', 'N/A')} | Margin: {r.get('margin_percent', 0)}% | Customers: {r.get('customer_count', 0)} | Status: {r.get('status', 'unknown')}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="reseller_create", description="Create a reseller")
    @app_commands.describe(name="Reseller name", email="Reseller email", margin="Margin percentage")
    async def reseller_create(self, interaction: discord.Interaction, name: str, email: str, margin: float = 10.0):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/resellers", {"name": name, "email": email, "margin_percent": margin})
        if "id" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"Reseller {name} created with {margin}% margin.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="reseller_branding", description="Update reseller branding")
    @app_commands.describe(reseller_id="Reseller ID", logo_url="Logo URL", primary_color="Primary color hex", company_name="Company name")
    async def reseller_branding(self, interaction: discord.Interaction, reseller_id: str, logo_url: str = "", primary_color: str = "", company_name: str = ""):
        await interaction.response.defer()
        result = await self.api.put(f"/api/marketplace/resellers/{reseller_id}/branding", {"logo_url": logo_url, "primary_color": primary_color, "company_name": company_name})
        if result.get("success"):
            await interaction.followup.send(embed=discord.Embed(description=f"Branding updated for {reseller_id}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="reseller_sales", description="View reseller sales report")
    @app_commands.describe(reseller_id="Reseller ID")
    async def reseller_sales(self, interaction: discord.Interaction, reseller_id: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/marketplace/resellers/{reseller_id}/sales")
        embed = discord.Embed(title=f"Reseller Sales: {reseller_id}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Total Revenue", value=f"${result.get('total_revenue', 0):.2f}", inline=True)
        embed.add_field(name="Your Earnings", value=f"${result.get('reseller_earnings', 0):.2f}", inline=True)
        embed.add_field(name="Transactions", value=str(result.get("transaction_count", 0)), inline=True)
        embed.add_field(name="Period", value=result.get("period", "N/A"), inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ResellerWhitelabel(bot))
