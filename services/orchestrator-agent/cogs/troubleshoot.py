import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class Troubleshoot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    async def _diagnose(self, vps_id: str, issue: str) -> list:
        findings = []
        stats = await self.vps_manager.get_vps_stats(vps_id)

        if not stats:
            findings.append(("Container", "Cannot access container - it may not exist or is unreachable"))
            return findings

        if issue == "connectivity":
            ping = await self.vps_manager.run_health_check(vps_id, "ping")
            findings.append(("Ping Check", ping["status"]))
            if ping["status"] != "passed":
                findings.append(("Suggestion", "Check if the container is running and network is configured"))

            port_check = await self.vps_manager.run_health_check(vps_id, "port", "localhost:22")
            findings.append(("SSH Port (22)", port_check["status"]))
            if port_check["status"] != "passed":
                findings.append(("Suggestion", "SSH service may not be running. Restart the container."))

        elif issue == "performance":
            findings.append(("CPU Usage", f"{stats.get('cpu_usage', 0)}%"))
            findings.append(("Memory Usage", f"{stats.get('memory_usage', 0)}%"))

            if stats.get("cpu_usage", 0) > 80:
                findings.append(("Suggestion", "High CPU - consider scaling up or checking running processes"))
            if stats.get("memory_usage", 0) > 80:
                findings.append(("Suggestion", "High memory - consider increasing RAM allocation"))

        elif issue == "connection_refused":
            findings.append(("Status", stats.get("status", "unknown")))
            if stats.get("status") != "running":
                findings.append(("Suggestion", "Container is not running. Use /start to start it."))
            else:
                findings.append(("Suggestion", "Check if the service inside the container is listening on the correct port"))

        elif issue == "high_latency":
            ping = await self.vps_manager.run_health_check(vps_id, "ping")
            findings.append(("Latency", f"{ping['response_time_ms']}ms"))
            if ping["response_time_ms"] > 200:
                findings.append(("Suggestion", "Network latency is high. Check host network or move to closer region"))

        else:
            findings.append(("Unknown Issue", f"No diagnostic data for '{issue}'"))
            findings.append(("Suggestion", "Try: connectivity, performance, connection_refused, high_latency"))

        return findings

    @app_commands.command(name="troubleshoot", description="Diagnose common issues on a VPS")
    @app_commands.describe(vps_id="VPS ID", issue="Issue type: connectivity/performance/connection_refused/high_latency")
    async def troubleshoot(self, interaction: discord.Interaction, vps_id: str, issue: str = "connectivity"):
        await interaction.response.defer()

        findings = await self._diagnose(vps_id, issue)

        embed = discord.Embed(title=f"Troubleshooting: {vps_id[:12]} - {issue}", color=discord.Color.blue(), timestamp=datetime.now())
        for title, detail in findings:
            emoji = "✅" if "passed" in str(detail).lower() or "suggestion" not in title.lower() else "💡"
            if "suggestion" in title.lower():
                emoji = "💡"
            embed.add_field(name=f"{emoji} {title}", value=detail, inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Troubleshoot(bot))
