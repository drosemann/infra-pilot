import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class NetworkMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.baseline_latency = {}

    def _format_bytes(self, b: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.2f} {unit}"
            b /= 1024
        return f"{b:.2f} PB"

    @app_commands.command(name="networkstats", description="Show network statistics for a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def network_stats(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        stats = await self.vps_manager.get_network_stats(vps_id)
        if not stats:
            await interaction.followup.send(embed=discord.Embed(description="No network data available.", color=0xFFFF00))
            return

        embed = discord.Embed(title=f"Network Stats: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Avg Download", value=self._format_bytes(stats.get("avg_rx", 0)), inline=True)
        embed.add_field(name="Avg Upload", value=self._format_bytes(stats.get("avg_tx", 0)), inline=True)
        embed.add_field(name="Peak Download", value=self._format_bytes(stats.get("peak_rx", 0)), inline=True)
        embed.add_field(name="Peak Upload", value=self._format_bytes(stats.get("peak_tx", 0)), inline=True)
        embed.add_field(name="Total Traffic (24h)", value=self._format_bytes(stats.get("total_traffic", 0)), inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="networklatency", description="Check latency to a VPS")
    @app_commands.describe(vps_id="VPS ID", target="Target host (default: 8.8.8.8)")
    async def network_latency(self, interaction: discord.Interaction, vps_id: str, target: str = "8.8.8.8"):
        await interaction.response.defer()
        result = await self.vps_manager.run_health_check(vps_id, "ping", target)

        embed = discord.Embed(title=f"Latency Check: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Target", value=target, inline=True)
        embed.add_field(name="Status", value=result["status"], inline=True)
        embed.add_field(name="Response Time", value=f"{result['response_time_ms']}ms", inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NetworkMonitor(bot))
