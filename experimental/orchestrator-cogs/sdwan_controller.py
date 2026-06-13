import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class SDWANController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="sdwan_list", description="List SD-WAN uplinks")
    async def sdwan_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/sdwan/uplinks")
        uplinks = data if isinstance(data, list) else data.get("uplinks", [])
        if not uplinks:
            await interaction.followup.send(embed=discord.Embed(description="No SD-WAN uplinks configured.", color=0xFFFF00))
            return
        embed = discord.Embed(title="SD-WAN Uplinks", color=discord.Color.blue(), timestamp=datetime.now())
        for uplink in uplinks[:10]:
            status_icon = "🟢" if uplink.get("status") == "active" else "🔴"
            embed.add_field(name=f"{status_icon} {uplink.get('name', 'Unknown')}", value=f"Provider: {uplink.get('provider', 'N/A')} | BW: {uplink.get('bandwidth', 0)}Mbps | Load: {uplink.get('load_percent', 0)}%", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sdwan_failover", description="Trigger failover for an SD-WAN uplink")
    @app_commands.describe(uplink_id="Uplink ID")
    async def sdwan_failover(self, interaction: discord.Interaction, uplink_id: str):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/sdwan/uplinks/{uplink_id}/failover", {})
        if result.get("status") == "ok":
            await interaction.followup.send(embed=discord.Embed(description=f"Failover triggered for {uplink_id}", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failover failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))


async def setup(bot):
    await bot.add_cog(SDWANController(bot))
