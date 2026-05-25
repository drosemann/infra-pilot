import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class CostOptimizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    def _calculate_cost(self, cpu: float, memory: int, storage: int) -> float:
        cpu_cost = cpu * config.PRICING["cpu_per_core"]
        memory_cost = (memory / 1024) * config.PRICING["memory_per_gb"]
        storage_cost = storage * config.PRICING["storage_per_gb"]
        return cpu_cost + memory_cost + storage_cost

    @app_commands.command(name="costoptimize", description="Get cost optimization suggestions")
    @app_commands.describe(vps_id="VPS ID")
    async def cost_optimize(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        cfg = instance["config"]
        current_cost = self._calculate_cost(cfg["cpu_limit"], cfg["memory_limit"], cfg["storage_limit"])

        suggestions = []
        total_savings = 0.0

        # Analyze usage vs allocation
        history = await self.vps_manager.get_usage_history(vps_id, hours=168)
        if history and len(history) > 10:
            avg_cpu = sum(r.get("cpu_usage", 0) for r in history) / len(history)
            avg_memory = sum(r.get("memory_usage", 0) for r in history) / len(history)

            # CPU optimization
            cpu_utilization = avg_cpu / (cfg["cpu_limit"] * 100) * 100
            if cpu_utilization < 30 and cfg["cpu_limit"] > config.RESOURCE_LIMITS["min_cpu"]:
                recommended_cpu = max(cfg["cpu_limit"] / 2, config.RESOURCE_LIMITS["min_cpu"])
                new_cost = self._calculate_cost(recommended_cpu, cfg["memory_limit"], cfg["storage_limit"])
                savings = current_cost - new_cost
                suggestions.append(f"CPU overallocation: avg {avg_cpu:.1f}% of {cfg['cpu_limit']} cores. "
                                   f"Reduce to {recommended_cpu:.1f} cores (save ${savings:.2f}/mo)")
                total_savings += savings

            # Memory optimization
            if avg_memory < 30 and cfg["memory_limit"] > config.RESOURCE_LIMITS["min_memory_mb"]:
                recommended_mem = int(cfg["memory_limit"] * 0.75)
                new_cost = self._calculate_cost(cfg["cpu_limit"], recommended_mem, cfg["storage_limit"])
                savings = current_cost - new_cost
                suggestions.append(f"Memory overallocation: avg {avg_memory:.1f}% of {cfg['memory_limit']}MB. "
                                   f"Reduce to {recommended_mem}MB (save ${savings:.2f}/mo)")
                total_savings += savings

        # Storage optimization
        if cfg["storage_limit"] > config.RESOURCE_LIMITS["min_storage_gb"]:
            try:
                container = self.vps_manager.client.containers.get(vps_id)
                exit_code, output = container.exec_run("df -h / | tail -1")
                if exit_code == 0:
                    parts = output.decode().split()
                    if len(parts) >= 5:
                        used_pct = float(parts[4].strip("%"))
                        if used_pct < 30:
                            suggested_storage = max(int(cfg["storage_limit"] * 0.5), config.RESOURCE_LIMITS["min_storage_gb"])
                            new_cost = self._calculate_cost(cfg["cpu_limit"], cfg["memory_limit"], suggested_storage)
                            savings = current_cost - new_cost
                            suggestions.append(f"Storage overallocation: {used_pct:.0f}% used of {cfg['storage_limit']}GB. "
                                               f"Reduce to {suggested_storage}GB (save ${savings:.2f}/mo)")
                            total_savings += savings
            except Exception:
                pass

        if not suggestions:
            suggestions.append("Your VPS is well-optimized. No cost savings identified.")

        embed = discord.Embed(title=f"Cost Optimization: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Monthly Cost", value=f"${current_cost:.2f}", inline=True)
        embed.add_field(name="CPU", value=f"{cfg['cpu_limit']} cores", inline=True)
        embed.add_field(name="RAM", value=f"{cfg['memory_limit']}MB", inline=True)
        embed.add_field(name="Storage", value=f"{cfg['storage_limit']}GB", inline=True)
        embed.add_field(name="Potential Savings", value=f"${total_savings:.2f}/mo" if total_savings > 0 else "None", inline=True)
        embed.add_field(name="Suggestions", value="\n".join(f"• {s}" for s in suggestions), inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CostOptimizer(bot))
