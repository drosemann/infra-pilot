import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import logging
import uuid

from config import config
from vps_manager import VPSManager

logger = logging.getLogger(__name__)


class AICapacityForecaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.forecasts_file = 'data/capacity_forecasts.json'
        self._ensure_data_dir()
        self._load_forecasts()
        self.forecast_loop.start()

    def cog_unload(self):
        self.forecast_loop.cancel()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_forecasts(self):
        if os.path.exists(self.forecasts_file):
            with open(self.forecasts_file) as f:
                self.forecasts = json.load(f)
        else:
            self.forecasts = []

    def _save_forecasts(self):
        with open(self.forecasts_file, 'w') as f:
            json.dump(self.forecasts, f, indent=2)

    def _linear_trend(self, values: List[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        x_avg = (n - 1) / 2.0
        y_avg = sum(values) / n
        num = sum((i - x_avg) * (v - y_avg) for i, v in enumerate(values))
        den = sum((i - x_avg) ** 2 for i in range(n))
        return num / den if den != 0 else 0.0

    def _predict(self, history: List[Dict], metric: str, days_ahead: int) -> float:
        values = [r.get(metric, 0) for r in history if r.get(metric) is not None]
        if len(values) < 10:
            return sum(values) / len(values) if values else 0.0
        slope = self._linear_trend(values)
        last_avg = sum(values[-10:]) / 10
        predicted = last_avg + slope * days_ahead
        return max(0, min(predicted, 100))

    def _generate_forecast(self, vps_id: str, instance: Dict) -> Optional[Dict]:
        cfg = instance["config"]
        try:
            import asyncio
            history = asyncio.run_coroutine_threadsafe(
                self.vps_manager.get_usage_history(vps_id, hours=720),
                self.bot.loop
            ).result()
        except Exception:
            history = None

        if not history or len(history) < 10:
            return None

        cpu_30 = self._predict(history, "cpu_usage", 30)
        cpu_60 = self._predict(history, "cpu_usage", 60)
        cpu_90 = self._predict(history, "cpu_usage", 90)
        mem_30 = self._predict(history, "memory_usage", 30)
        mem_60 = self._predict(history, "memory_usage", 60)
        mem_90 = self._predict(history, "memory_usage", 90)

        recommendations = []
        if cpu_90 > 80:
            recommended_cpu = min(cfg["cpu_limit"] * 2, config.RESOURCE_LIMITS["max_cpu"])
            recommendations.append(f"CPU may reach {cpu_90:.0f}% in 90 days. Consider upgrading to {recommended_cpu} cores.")
        if mem_90 > 80:
            recommended_mem = int(min(cfg["memory_limit"] * 1.5, config.RESOURCE_LIMITS["max_memory_mb"]))
            recommendations.append(f"Memory may reach {mem_90:.0f}% in 90 days. Consider upgrading to {recommended_mem}MB.")

        return {
            "cpu_forecast": {"30d": round(cpu_30, 1), "60d": round(cpu_60, 1), "90d": round(cpu_90, 1)},
            "memory_forecast": {"30d": round(mem_30, 1), "60d": round(mem_60, 1), "90d": round(mem_90, 1)},
            "recommendations": recommendations,
        }

    @tasks.loop(hours=6)
    async def forecast_loop(self):
        try:
            for vps_id, instance in self.vps_manager.vps_instances.items():
                forecast = self._generate_forecast(vps_id, instance)
                if forecast:
                    self.forecasts.append({
                        "id": str(uuid.uuid4())[:8],
                        "vps_id": vps_id,
                        "created_at": datetime.now().isoformat(),
                        "forecast": forecast,
                    })
            self._save_forecasts()
            if len(self.forecasts) > 1000:
                self.forecasts = self.forecasts[-500:]
                self._save_forecasts()
        except Exception as e:
            logger.error(f"Forecast loop error: {e}")

    @forecast_loop.before_loop
    async def before_forecast_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="capacity_forecast", description="Get 30/60/90 day capacity forecast for a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def capacity_forecast(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        forecast = self._generate_forecast(vps_id, instance)
        if not forecast:
            await interaction.followup.send(embed=discord.Embed(description="Insufficient data for forecast. Need at least 10 data points.", color=0xFFFF00))
            return

        embed = discord.Embed(title=f"Capacity Forecast: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        cpu_f = forecast["cpu_forecast"]
        mem_f = forecast["memory_forecast"]
        embed.add_field(name="CPU 30d", value=f"{cpu_f['30d']}%", inline=True)
        embed.add_field(name="CPU 60d", value=f"{cpu_f['60d']}%", inline=True)
        embed.add_field(name="CPU 90d", value=f"{cpu_f['90d']}%", inline=True)
        embed.add_field(name="Memory 30d", value=f"{mem_f['30d']}%", inline=True)
        embed.add_field(name="Memory 60d", value=f"{mem_f['60d']}%", inline=True)
        embed.add_field(name="Memory 90d", value=f"{mem_f['90d']}%", inline=True)

        if forecast["recommendations"]:
            embed.add_field(name="Recommendations", value="\n".join(f"• {r}" for r in forecast["recommendations"]), inline=False)
        else:
            embed.add_field(name="Recommendations", value="No upgrades needed based on current trends.", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="capacity_recommend", description="Get provisioning recommendations based on forecasts")
    async def capacity_recommend(self, interaction: discord.Interaction):
        await interaction.response.defer()

        recommendations = []
        for vps_id, instance in self.vps_manager.vps_instances.items():
            forecast = self._generate_forecast(vps_id, instance)
            if forecast and forecast["recommendations"]:
                recommendations.append((vps_id, forecast))

        if not recommendations:
            await interaction.followup.send(embed=discord.Embed(description="No provisioning recommendations at this time.", color=0x00FF00))
            return

        embed = discord.Embed(title="Provisioning Recommendations", color=discord.Color.blue(), timestamp=datetime.now())
        for vps_id, forecast in recommendations[:5]:
            text = "\n".join(f"• {r}" for r in forecast["recommendations"])
            embed.add_field(name=vps_id[:12], value=text, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="capacity_history", description="View forecast history")
    async def capacity_history(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.forecasts:
            await interaction.followup.send(embed=discord.Embed(description="No forecast history available.", color=0xFFFF00))
            return

        recent = sorted(self.forecasts, key=lambda x: x["created_at"], reverse=True)[:10]
        embed = discord.Embed(title="Forecast History", color=discord.Color.blue(), timestamp=datetime.now())
        for f_rec in recent:
            f = f_rec["forecast"]
            embed.add_field(
                name=f"{f_rec['vps_id'][:12]} - {f_rec['created_at'][:19]}",
                value=f"CPU 90d: {f['cpu_forecast']['90d']}% | Mem 90d: {f['memory_forecast']['90d']}% | Recs: {len(f['recommendations'])}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AICapacityForecaster(bot))
