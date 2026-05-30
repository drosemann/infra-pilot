import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class NetworkSegmentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="segment_list", description="List network segments")
    async def segment_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/segments")
        segments = data if isinstance(data, list) else data.get("segments", [])
        if not segments:
            await interaction.followup.send(embed=discord.Embed(description="No network segments.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Network Segments", color=discord.Color.blue(), timestamp=datetime.now())
        for seg in segments[:10]:
            compliance = seg.get("compliance_status", "unknown")
            c_icon = "✅" if compliance == "compliant" else "⚠️"
            embed.add_field(name=f"{c_icon} {seg.get('name', 'Unknown')}", value=f"CIDR: {seg.get('cidr', 'N/A')} | Type: {seg.get('segment_type', 'N/A')} | Devices: {seg.get('device_count', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="segment_create", description="Create a network segment")
    @app_commands.describe(name="Segment name", cidr="CIDR range", segment_type="private/public/dmz")
    async def segment_create(self, interaction: discord.Interaction, name: str, cidr: str, segment_type: str = "private"):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/segments", {"name": name, "cidr": cidr, "segment_type": segment_type})
        if "id" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"Segment {name} ({cidr}) created.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="segment_compliance", description="Check segment compliance")
    @app_commands.describe(segment_id="Segment ID")
    async def segment_compliance(self, interaction: discord.Interaction, segment_id: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/networking/segments/{segment_id}/compliance")
        embed = discord.Embed(title=f"Compliance: {segment_id}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Status", value=result.get("status", "unknown"), inline=True)
        embed.add_field(name="Checks Passed", value=str(result.get("checks_passed", 0)), inline=True)
        embed.add_field(name="Checks Failed", value=str(result.get("checks_failed", 0)), inline=True)
        findings = result.get("findings", [])
        if findings:
            embed.add_field(name="Findings", value="\n".join(f"• {f}" for f in findings[:5]), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NetworkSegmentation(bot))
