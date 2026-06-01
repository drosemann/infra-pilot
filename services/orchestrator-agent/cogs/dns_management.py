import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class DNSManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="dns_zones", description="List DNS zones")
    async def dns_zones(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/dns/zones")
        zones = data if isinstance(data, list) else data.get("zones", [])
        if not zones:
            await interaction.followup.send(embed=discord.Embed(description="No DNS zones configured.", color=0xFFFF00))
            return
        embed = discord.Embed(title="DNS Zones", color=discord.Color.blue(), timestamp=datetime.now())
        for z in zones[:10]:
            sec_icon = "🔒" if z.get("dnssec_enabled") else "🔓"
            embed.add_field(name=f"{sec_icon} {z.get('zone_name', 'Unknown')}", value=f"Records: {z.get('record_count', 0)} | Serial: {z.get('serial', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dns_add_record", description="Add a DNS record")
    @app_commands.describe(zone="Zone name", name="Record name", rtype="Record type (A/AAAA/CNAME/MX/TXT)", value="Record value", ttl="TTL in seconds")
    async def dns_add_record(self, interaction: discord.Interaction, zone: str, name: str, rtype: str, value: str, ttl: int = 300):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/dns/zones/{zone}/records", {"name": name, "type": rtype.upper(), "value": value, "ttl": ttl})
        if result.get("status") == "created":
            await interaction.followup.send(embed=discord.Embed(description=f"DNS record {name} ({rtype}) added to {zone}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="dns_delete_record", description="Delete a DNS record")
    @app_commands.describe(zone="Zone name", record_id="Record ID")
    async def dns_delete_record(self, interaction: discord.Interaction, zone: str, record_id: str):
        await interaction.response.defer()
        result = await self.api.delete(f"/api/networking/dns/zones/{zone}/records/{record_id}")
        if result.get("success"):
            await interaction.followup.send(embed=discord.Embed(description=f"DNS record {record_id} deleted.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="dns_export", description="Export DNS zone file")
    @app_commands.describe(zone="Zone name")
    async def dns_export(self, interaction: discord.Interaction, zone: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/networking/dns/zones/{zone}/export")
        zonefile = result.get("zone_file", "No data")
        if len(zonefile) > 1900:
            zonefile = zonefile[:1900] + "..."
        embed = discord.Embed(title=f"Zone File: {zone}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Content", value=f"```bind\n{zonefile}\n```", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DNSManagement(bot))
