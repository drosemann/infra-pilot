import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class InvoiceTaxAutomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="tax_rates", description="List tax rates by country")
    @app_commands.describe(country="Country code (e.g. US, DE, GB)")
    async def tax_rates(self, interaction: discord.Interaction, country: str = ""):
        await interaction.response.defer()
        params = f"?country={country}" if country else ""
        data = await self.api.get(f"/api/marketplace/tax/rates{params}")
        rates = data if isinstance(data, list) else data.get("rates", [])
        if not rates:
            await interaction.followup.send(embed=discord.Embed(description="No tax rates found.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Tax Rates", color=discord.Color.blue(), timestamp=datetime.now())
        for r in rates[:10]:
            embed.add_field(name=f"{r.get('country_code', '??')} - {r.get('region', 'N/A')}", value=f"Rate: {r.get('rate_percent', 0):.2f}% | Type: {r.get('tax_type', 'vat')} | Apply to: {r.get('applies_to', 'all')}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="invoice_list", description="List invoices")
    async def invoice_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/tax/invoices")
        invoices = data if isinstance(data, list) else data.get("invoices", [])
        if not invoices:
            await interaction.followup.send(embed=discord.Embed(description="No invoices.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Invoices", color=discord.Color.blue(), timestamp=datetime.now())
        for inv in invoices[:10]:
            paid_icon = "✅" if inv.get("paid") else "⏳"
            embed.add_field(name=f"{paid_icon} {inv.get('invoice_number', 'N/A')}", value=f"Amount: ${inv.get('total', 0):.2f} | Tax: ${inv.get('tax_amount', 0):.2f} | Status: {inv.get('status', 'unknown')} | Due: {inv.get('due_date', 'N/A')}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="invoice_generate", description="Generate an invoice")
    @app_commands.describe(amount="Amount", description="Invoice description", customer="Customer name/ID")
    async def invoice_generate(self, interaction: discord.Interaction, amount: float, description: str = "", customer: str = ""):
        await interaction.response.defer()
        result = await self.api.post("/api/marketplace/tax/invoices", {"amount": amount, "description": description, "customer": customer})
        if "id" in result:
            embed = discord.Embed(title="Invoice Generated", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Invoice #", value=result.get("invoice_number", "N/A"))
            embed.add_field(name="Amount", value=f"${result.get('total', amount):.2f}")
            embed.add_field(name="Tax", value=f"${result.get('tax_amount', 0):.2f}")
            embed.add_field(name="Status", value=result.get("status", "draft"))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="invoice_export", description="Export invoice as XRechnung/ZUGFeRD")
    @app_commands.describe(invoice_id="Invoice ID", format_="Export format (xrechnung/zugferd)")
    async def invoice_export(self, interaction: discord.Interaction, invoice_id: str, format_: str = "xrechnung"):
        await interaction.response.defer()
        result = await self.api.get(f"/api/marketplace/tax/invoices/{invoice_id}/export/{format_}")
        xml_data = result.get("xml", "No data")
        if len(xml_data) > 1900:
            xml_data = xml_data[:1900] + "..."
        embed = discord.Embed(title=f"Invoice {invoice_id} ({format_})", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="XML", value=f"```xml\n{xml_data}\n```", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(InvoiceTaxAutomation(bot))
