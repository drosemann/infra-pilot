import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional

from config import config
from vps_manager import VPSManager


class CostPrediction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    def _calculate_cost(self, cpu: float, memory: int, storage: int) -> float:
        cpu_cost = cpu * config.PRICING["cpu_per_core"]
        memory_cost = (memory / 1024) * config.PRICING["memory_per_gb"]
        storage_cost = storage * config.PRICING["storage_per_gb"]
        return cpu_cost + memory_cost + storage_cost

    @app_commands.command(name="costpredict", description="Predict next month's cost for a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def cost_predict(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        cfg = instance["config"]
        current_cost = self._calculate_cost(cfg["cpu_limit"], cfg["memory_limit"], cfg["storage_limit"])

        history = await self.vps_manager.get_usage_history(vps_id, hours=720)
        if history and len(history) > 10:
            avg_cpu = sum(r.get("cpu_usage", 0) for r in history) / len(history)
            avg_memory = sum(r.get("memory_usage", 0) for r in history) / len(history)

            cpu_trend = avg_cpu / 100.0
            mem_trend = avg_memory / 100.0

            predicted_cpu = max(cfg["cpu_limit"] * cpu_trend, cfg["cpu_limit"] * 0.5)
            predicted_memory = max(int(cfg["memory_limit"] * mem_trend), int(cfg["memory_limit"] * 0.5))

            predicted_cost = self._calculate_cost(predicted_cpu, predicted_memory, cfg["storage_limit"])
        else:
            predicted_cost = current_cost
            avg_cpu = 0
            avg_memory = 0

        embed = discord.Embed(title=f"Cost Prediction: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Monthly", value=f"${current_cost:.2f}", inline=True)
        embed.add_field(name="Predicted Next Month", value=f"${predicted_cost:.2f}", inline=True)
        embed.add_field(name="Avg CPU (30d)", value=f"{avg_cpu:.1f}%", inline=True)
        embed.add_field(name="Avg Memory (30d)", value=f"{avg_memory:.1f}%", inline=True)
        embed.add_field(name="Current CPU", value=f"{cfg['cpu_limit']} cores", inline=True)
        embed.add_field(name="Current RAM", value=f"{cfg['memory_limit']}MB", inline=True)

        change = predicted_cost - current_cost
        if change > 0:
            embed.add_field(name="Change", value=f"+${change:.2f} (increase expected)", inline=False)
        elif change < 0:
            embed.add_field(name="Change", value=f"-${abs(change):.2f} (decrease expected)", inline=False)
        else:
            embed.add_field(name="Change", value="Stable", inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CostPrediction(bot))
