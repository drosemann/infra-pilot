import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class CellularIntegration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="cellular_modems", description="List cellular modems")
    async def cellular_modems(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/cellular/modems")
        modems = data if isinstance(data, list) else data.get("modems", [])
        if not modems:
            await interaction.followup.send(embed=discord.Embed(description="No cellular modems.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Cellular Modems", color=discord.Color.blue(), timestamp=datetime.now())
        for m in modems[:10]:
            status_icon = "🟢" if m.get("status") == "connected" else "🔴"
            embed.add_field(name=f"{status_icon} {m.get('name', 'Unknown')}", value=f"ICCID: {m.get('iccid', 'N/A')[:10]}... | Operator: {m.get('operator', 'N/A')} | Signal: {m.get('signal_quality', 0)}% | Data: {m.get('data_used_mb', 0)}MB", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cellular_apn", description="Configure APN")
    @app_commands.describe(modem_id="Modem ID", apn="APN name", username="APN username", password="APN password")
    async def cellular_apn(self, interaction: discord.Interaction, modem_id: str, apn: str, username: str = "", password: str = ""):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/cellular/modems/{modem_id}/apn", {"apn": apn, "username": username, "password": password})
        if result.get("status") == "configured":
            await interaction.followup.send(embed=discord.Embed(description=f"APN {apn} configured on {modem_id}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="cellular_sms", description=" Send SMS via modem")
    @app_commands.describe(modem_id="Modem ID", number="Destination number", message="Message text")
    async def cellular_sms(self, interaction: discord.Interaction, modem_id: str, number: str, message: str):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/cellular/modems/{modem_id}/sms", {"number": number, "message": message})
        if result.get("status") == "sent":
            await interaction.followup.send(embed=discord.Embed(description=f"SMS sent to {number}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="cellular_failover", description="Configure cellular failover")
    @app_commands.describe(modem_id="Modem ID", enabled="Enable failover", priority="Failover priority")
    async def cellular_failover(self, interaction: discord.Interaction, modem_id: str, enabled: bool = True, priority: int = 1):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/cellular/modems/{modem_id}/failover", {"enabled": enabled, "priority": priority})
        if result.get("status") == "configured":
            status = "enabled" if enabled else "disabled"
            await interaction.followup.send(embed=discord.Embed(description=f"Failover {status} for {modem_id} (priority {priority}).", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))


async def setup(bot):
    await bot.add_cog(CellularIntegration(bot))
