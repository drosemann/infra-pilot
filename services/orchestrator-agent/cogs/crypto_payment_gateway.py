import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class CryptoPaymentGateway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="crypto_wallets", description="List crypto wallets")
    async def crypto_wallets(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/crypto/wallets")
        wallets = data if isinstance(data, list) else data.get("wallets", [])
        if not wallets:
            await interaction.followup.send(embed=discord.Embed(description="No wallets.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Crypto Wallets", color=discord.Color.blue(), timestamp=datetime.now())
        for w in wallets[:10]:
            embed.add_field(name=f"{w.get('currency', 'Unknown').upper()} Wallet", value=f"Address: {w.get('address', 'N/A')[:16]}... | Balance: {w.get('balance', 0)} {w.get('currency', '').upper()}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="crypto_invoice", description="Create a crypto invoice")
    @app_commands.describe(amount_usd="Amount in USD", currency="btc/eth/sol/usdc")
    async def crypto_invoice(self, interaction: discord.Interaction, amount_usd: float, currency: str = "usdc"):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/crypto/invoices", {"amount_usd": amount_usd, "currency": currency.lower()})
        if "id" in result:
            embed = discord.Embed(title="Crypto Invoice Created", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Amount", value=f"${amount_usd:.2f} USD")
            embed.add_field(name="Currency", value=currency.upper())
            embed.add_field(name="Address", value=result.get("address", "N/A"))
            embed.add_field(name="Invoice ID", value=result.get("id", ""))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="crypto_rates", description="Show crypto exchange rates")
    async def crypto_rates(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.get("/api/marketplace/crypto/rates")
        embed = discord.Embed(title="Crypto Exchange Rates", color=discord.Color.blue(), timestamp=datetime.now())
        rates = result.get("rates", {})
        for k, v in rates.items():
            embed.add_field(name=k.upper(), value=f"${v:.2f} USD", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="crypto_transactions", description="List crypto transactions")
    async def crypto_transactions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/crypto/transactions")
        txs = data if isinstance(data, list) else data.get("transactions", [])
        if not txs:
            await interaction.followup.send(embed=discord.Embed(description="No transactions.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Crypto Transactions", color=discord.Color.blue(), timestamp=datetime.now())
        for tx in txs[:10]:
            status_icon = "✅" if tx.get("status") == "confirmed" else "⏳" if tx.get("status") == "pending" else "❌"
            embed.add_field(name=f"{status_icon} {tx.get('txid', 'N/A')[:12]}...", value=f"Amount: {tx.get('amount', 0)} {tx.get('currency', '').upper()} | From: {tx.get('from_address', 'N/A')[:10]}... | Confirmations: {tx.get('confirmations', 0)}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CryptoPaymentGateway(bot))
