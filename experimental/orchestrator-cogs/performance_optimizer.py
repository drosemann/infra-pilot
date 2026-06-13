import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Dict, List

from config import config
from vps_manager import VPSManager, VPSConfig


class PerformanceOptimizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    def _analyze_usage(self, stats: Dict, history: List[Dict], instance: Dict) -> List[str]:
        suggestions = []
        cfg = instance["config"]

        if history and len(history) > 10:
            avg_cpu = sum(r.get("cpu_usage", 0) for r in history) / len(history)
            avg_memory = sum(r.get("memory_usage", 0) for r in history) / len(history)
            peak_cpu = max(r.get("cpu_usage", 0) for r in history)
            peak_memory = max(r.get("memory_usage", 0) for r in history)

            if avg_cpu < 20 and cfg["cpu_limit"] > config.RESOURCE_LIMITS["min_cpu"]:
                suggestions.append(f"CPU overallocation: avg {avg_cpu:.1f}% with {cfg['cpu_limit']} cores. Consider reducing to {max(cfg['cpu_limit'] * 0.5, config.RESOURCE_LIMITS['min_cpu']):.1f} cores.")
            if peak_cpu > 85:
                suggestions.append(f"CPU throttling risk: peak at {peak_cpu:.1f}%. Consider increasing CPU from {cfg['cpu_limit']} to {cfg['cpu_limit'] * 1.5:.1f} cores.")

            if avg_memory < 30 and cfg["memory_limit"] > config.RESOURCE_LIMITS["min_memory_mb"]:
                suggested_mem = int(cfg["memory_limit"] * 0.75)
                suggestions.append(f"Memory overallocation: avg {avg_memory:.1f}% of {cfg['memory_limit']}MB. Consider reducing to {suggested_mem}MB.")
            if peak_memory > 85:
                suggested_mem = int(cfg["memory_limit"] * 1.5)
                suggestions.append(f"Memory pressure: peak at {peak_memory:.1f}%. Consider increasing RAM from {cfg['memory_limit']}MB to {suggested_mem}MB.")

            if avg_cpu < 30 and avg_memory < 30:
                suggestions.append("Consider using a smaller instance to reduce costs.")
            if avg_cpu > 70 and avg_memory > 70:
                suggestions.append("Consider upgrading to a larger instance for better performance.")

        if "swap" in str(stats.get("memory_usage", 0)):
            suggestions.append("Swap usage detected. Consider increasing RAM allocation.")

        return suggestions

    @app_commands.command(name="optimize", description="Get performance optimization suggestions")
    @app_commands.describe(vps_id="VPS ID")
    async def optimize(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        stats = await self.vps_manager.get_vps_stats(vps_id)
        history = await self.vps_manager.get_usage_history(vps_id, hours=168)

        suggestions = self._analyze_usage(stats or {}, history or [], instance)

        embed = discord.Embed(title=f"Optimization: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        cfg = instance["config"]
        embed.add_field(name="Current CPU", value=f"{cfg['cpu_limit']} cores", inline=True)
        embed.add_field(name="Current RAM", value=f"{cfg['memory_limit']}MB", inline=True)
        embed.add_field(name="Current Storage", value=f"{cfg['storage_limit']}GB", inline=True)

        if stats:
            embed.add_field(name="CPU Usage", value=f"{stats.get('cpu_usage', 0)}%", inline=True)
            embed.add_field(name="Memory Usage", value=f"{stats.get('memory_usage', 0)}%", inline=True)

        if suggestions:
            embed.add_field(name="Suggestions", value="\n".join(f"• {s}" for s in suggestions), inline=False)
        else:
            embed.add_field(name="Suggestions", value="No optimization needed.", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="optimizeapply", description="Apply optimization suggestion")
    @app_commands.describe(vps_id="VPS ID", suggestion="Suggestion number to apply")
    async def optimize_apply(self, interaction: discord.Interaction, vps_id: str, suggestion: int):
        await interaction.response.defer()
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        history = await self.vps_manager.get_usage_history(vps_id, hours=168)
        stats = await self.vps_manager.get_vps_stats(vps_id)
        suggestions = self._analyze_usage(stats or {}, history or [], instance)

        if suggestion < 1 or suggestion > len(suggestions):
            await interaction.followup.send(embed=discord.Embed(description="Invalid suggestion number.", color=0xFF0000))
            return

        cfg = instance["config"]
        new_config = VPSConfig(
            cpu_limit=cfg["cpu_limit"],
            memory_limit=cfg["memory_limit"],
            storage_limit=cfg["storage_limit"],
            image=cfg["image"],
            ports=cfg["ports"],
            env_vars={},
        )

        if "reduce" in suggestions[suggestion - 1].lower() and "cpu" in suggestions[suggestion - 1].lower():
            new_config.cpu_limit = max(cfg["cpu_limit"] * 0.5, config.RESOURCE_LIMITS["min_cpu"])
        elif "increase" in suggestions[suggestion - 1].lower() and "cpu" in suggestions[suggestion - 1].lower():
            new_config.cpu_limit = min(cfg["cpu_limit"] * 1.5, config.RESOURCE_LIMITS["max_cpu"])
        elif "reduce" in suggestions[suggestion - 1].lower() and "ram" in suggestions[suggestion - 1].lower():
            new_config.memory_limit = int(max(cfg["memory_limit"] * 0.75, config.RESOURCE_LIMITS["min_memory_mb"]))
        elif "increase" in suggestions[suggestion - 1].lower() and "ram" in suggestions[suggestion - 1].lower():
            new_config.memory_limit = int(min(cfg["memory_limit"] * 1.5, config.RESOURCE_LIMITS["max_memory_mb"]))

        if await self.vps_manager.update_vps_config(vps_id, new_config):
            await interaction.followup.send(embed=discord.Embed(description=f"Suggestion applied. New CPU: {new_config.cpu_limit}, RAM: {new_config.memory_limit}MB", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to apply suggestion.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(PerformanceOptimizer(bot))
