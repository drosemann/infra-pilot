import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class ResourceTrading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="trade_list", description="List resource trade listings")
    @app_commands.describe(category="cpu/ram/storage/bandwidth")
    async def trade_list(self, interaction: discord.Interaction, category: str = ""):
        await interaction.response.defer()
        params = f"?category={category}" if category else ""
        data = await self.api.get(f"/api/marketplace/trading/listings{params}")
        listings = data if isinstance(data, list) else data.get("listings", [])
        if not listings:
            await interaction.followup.send(embed=discord.Embed(description="No listings available.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Resource Trade Listings", color=discord.Color.blue(), timestamp=datetime.now())
        for l in listings[:10]:
            type_icon = "💰" if l.get("listing_type") == "sell" else "🛒"
            embed.add_field(name=f"{type_icon} {l.get('resource_type', 'Unknown')} x{l.get('quantity', 0)}", value=f"Price: ${l.get('price', 0):.4f}/unit | Seller: {l.get('seller', 'N/A')[:8]}... | Status: {l.get('status', 'unknown')}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="trade_create", description="Create a resource listing")
    @app_commands.describe(resource_type="cpu/ram/storage/bandwidth", quantity="Amount", price="Price per unit", listing_type="sell/buy")
    async def trade_create(self, interaction: discord.Interaction, resource_type: str, quantity: float, price: float, listing_type: str = "sell"):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/trading/listings", {"resource_type": resource_type, "quantity": quantity, "price": price, "listing_type": listing_type})
        if "id" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"Listing created: {quantity}x {resource_type} @ ${price:.4f}", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="trade_buy", description="Buy from a listing")
    @app_commands.describe(listing_id="Listing ID", quantity="Quantity to buy")
    async def trade_buy(self, interaction: discord.Interaction, listing_id: str, quantity: float = 1):
        await interaction.response.defer()
        result = await self.api.post(f"/api/marketplace/trading/listings/{listing_id}/buy", {"quantity": quantity})
        if result.get("status") == "completed":
            await interaction.followup.send(embed=discord.Embed(description=f"Purchase completed: {quantity} units.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="trade_reputation", description="Check user reputation")
    @app_commands.describe(user_id="User ID")
    async def trade_reputation(self, interaction: discord.Interaction, user_id: str = ""):
        await interaction.response.defer()
        target = user_id or interaction.user.id
        result = await self.api.get(f"/api/marketplace/trading/reputation/{target}")
        embed = discord.Embed(title="Trader Reputation", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Rating", value=f"{result.get('rating', 0):.1f}/5.0", inline=True)
        embed.add_field(name="Total Trades", value=str(result.get("total_trades", 0)), inline=True)
        embed.add_field(name="Completion Rate", value=f"{result.get('completion_rate', 0)*100:.1f}%", inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ResourceTrading(bot))
