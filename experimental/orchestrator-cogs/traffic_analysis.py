import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class TrafficAnalysis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    def _format_bytes(self, b: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.2f} {unit}"
            b /= 1024
        return f"{b:.2f} PB"

    @app_commands.command(name="traffic", description="Analyze traffic patterns for a VPS")
    @app_commands.describe(vps_id="VPS ID", period="Analysis period: 24h/7d/30d")
    async def traffic(self, interaction: discord.Interaction, vps_id: str, period: str = "24h"):
        await interaction.response.defer()

        if period not in config.TRAFFIC_ANALYSIS_PERIODS:
            await interaction.followup.send(embed=discord.Embed(description="Period must be 24h, 7d, or 30d", color=0xFF0000))
            return

        hours = config.TRAFFIC_ANALYSIS_PERIODS[period]
        history = await self.vps_manager.get_usage_history(vps_id, hours=hours)

        if not history:
            await interaction.followup.send(embed=discord.Embed(description="No traffic data available.", color=0xFFFF00))
            return

        # Calculate traffic metrics
        total_rx = sum(r.get("network_rx", 0) for r in history)
        total_tx = sum(r.get("network_tx", 0) for r in history)
        total_traffic = total_rx + total_tx

        if len(history) > 1:
            peak_rx = max(r.get("network_rx", 0) for r in history)
            peak_tx = max(r.get("network_tx", 0) for r in history)
        else:
            peak_rx = total_rx
            peak_tx = total_tx

        avg_rx = total_rx / len(history) if history else 0
        avg_tx = total_tx / len(history) if history else 0

        # Find peak hours
        hourly_traffic = {}
        for r in history:
            ts = r.get("timestamp", "")
            hour_key = str(ts)[:13] if hasattr(ts, "strftime") else str(ts)[:13]
            net = (r.get("network_rx", 0) + r.get("network_tx", 0))
            hourly_traffic[hour_key] = hourly_traffic.get(hour_key, 0) + net

        peak_hour = max(hourly_traffic, key=hourly_traffic.get) if hourly_traffic else "N/A"
        peak_hour_value = hourly_traffic.get(peak_hour, 0)

        embed = discord.Embed(title=f"Traffic Analysis: {vps_id[:12]} ({period})", color=discord.Color.blue(), timestamp=datetime.now())

        embed.add_field(name="Total Traffic", value=self._format_bytes(total_traffic), inline=True)
        embed.add_field(name="Total Download", value=self._format_bytes(total_rx), inline=True)
        embed.add_field(name="Total Upload", value=self._format_bytes(total_tx), inline=True)

        embed.add_field(name="Avg Download Rate", value=f"{self._format_bytes(avg_rx)}/sample", inline=True)
        embed.add_field(name="Avg Upload Rate", value=f"{self._format_bytes(avg_tx)}/sample", inline=True)
        embed.add_field(name="Data Points", value=str(len(history)), inline=True)

        embed.add_field(name="Peak Download", value=self._format_bytes(peak_rx), inline=True)
        embed.add_field(name="Peak Upload", value=self._format_bytes(peak_tx), inline=True)
        embed.add_field(name="Peak Hour", value=f"{peak_hour} ({self._format_bytes(peak_hour_value)})", inline=True)

        # Ratio analysis
        if total_traffic > 0:
            rx_ratio = (total_rx / total_traffic) * 100
            embed.add_field(name="Traffic Ratio", value=f"↓ {rx_ratio:.1f}% / ↑ {100 - rx_ratio:.1f}%", inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TrafficAnalysis(bot))
