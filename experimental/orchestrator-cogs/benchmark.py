import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class Benchmark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="benchmark", description="Run a performance benchmark on a VPS")
    @app_commands.describe(vps_id="VPS ID", benchmark_type="cpu/disk/network")
    async def benchmark(self, interaction: discord.Interaction, vps_id: str, benchmark_type: str = "cpu"):
        await interaction.response.defer()

        if benchmark_type not in ("cpu", "disk", "network"):
            await interaction.followup.send(embed=discord.Embed(description="Type must be cpu, disk, or network", color=0xFF0000))
            return

        if not self.vps_manager.vps_instances.get(vps_id):
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        embed = discord.Embed(title=f"{benchmark_type.upper()} Benchmark: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Status", value="Running...", inline=False)
        await interaction.followup.send(embed=embed)

        if benchmark_type == "cpu":
            result = await self.vps_manager.benchmark_cpu(vps_id)
        elif benchmark_type == "disk":
            result = await self.vps_manager.benchmark_disk(vps_id)
        else:
            result = await self.vps_manager.benchmark_network(vps_id)

        embed.set_field_at(0, name="Status", value="Complete", inline=False)
        embed.add_field(name="Score", value=f"{result.get('score', 0):.2f}", inline=True)

        if benchmark_type == "cpu":
            embed.add_field(name="Unit", value="events/sec", inline=True)
        elif benchmark_type == "disk":
            embed.add_field(name="Unit", value="MB/s", inline=True)
        else:
            embed.add_field(name="Unit", value="Mbps", inline=True)

        if result.get("error"):
            embed.add_field(name="Error", value=result["error"], inline=False)
            embed.color = discord.Color.red()

        await interaction.edit_original_response(embed=embed)


async def setup(bot):
    await bot.add_cog(Benchmark(bot))
