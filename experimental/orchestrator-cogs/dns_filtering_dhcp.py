import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class DNSFilteringDHCP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="dnsfilter_list", description="List DNS filter instances")
    async def dnsfilter_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/dnsfilter/instances")
        instances = data if isinstance(data, list) else data.get("instances", [])
        if not instances:
            await interaction.followup.send(embed=discord.Embed(description="No DNS filter instances.", color=0xFFFF00))
            return
        embed = discord.Embed(title="DNS Filter Instances", color=discord.Color.blue(), timestamp=datetime.now())
        for inst in instances[:10]:
            status_icon = "🟢" if inst.get("status") == "active" else "🔴"
            embed.add_field(name=f"{status_icon} {inst.get('name', 'Unknown')}", value=f"Type: {inst.get('filter_type', 'N/A')} | Blocked: {inst.get('blocked_count', 0)} | Clients: {inst.get('client_count', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dnsfilter_block", description="Add a blocklist entry")
    @app_commands.describe(domain="Domain to block", category="Category (ads/malware/social/gambling)")
    async def dnsfilter_block(self, interaction: discord.Interaction, domain: str, category: str = "ads"):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/dnsfilter/blocklist", {"domain": domain, "category": category})
        if result.get("status") == "blocked":
            await interaction.followup.send(embed=discord.Embed(description=f"{domain} blocked ({category}).", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="dnsfilter_unblock", description="Remove a blocklist entry")
    @app_commands.describe(domain="Domain to unblock")
    async def dnsfilter_unblock(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer()
        result = await self.api.delete(f"/api/networking/dnsfilter/blocklist/{domain}")
        if result.get("success"):
            await interaction.followup.send(embed=discord.Embed(description=f"{domain} unblocked.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="dhcp_leases", description="List DHCP leases")
    async def dhcp_leases(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/dhcp/leases")
        leases = data if isinstance(data, list) else data.get("leases", [])
        if not leases:
            await interaction.followup.send(embed=discord.Embed(description="No DHCP leases.", color=0xFFFF00))
            return
        embed = discord.Embed(title="DHCP Leases", color=discord.Color.blue(), timestamp=datetime.now())
        for lease in leases[:10]:
            exp_icon = "✅" if lease.get("active") else "❌"
            embed.add_field(name=f"{exp_icon} {lease.get('hostname', 'Unknown')}", value=f"IP: {lease.get('ip', 'N/A')} | MAC: {lease.get('mac', 'N/A')} | Expires: {lease.get('expires_at', 'N/A')}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DNSFilteringDHCP(bot))
