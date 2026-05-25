import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import logging

from config import config
from vps_manager import VPSManager, VPSConfig


class AutoScaling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.scale_cooldowns = {}
        self.scale_check_loop.start()

    def cog_unload(self):
        self.scale_check_loop.cancel()

    @tasks.loop(minutes=1)
    async def scale_check_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM scaling_rules WHERE enabled = 1")
            rules = cursor.fetchall()
            cursor.close()
            conn.close()

            for rule in rules:
                await self._evaluate_rule(rule)
        except Exception as e:
            logging.error(f"Scale check error: {e}")

    async def _evaluate_rule(self, rule: dict):
        container_id = rule["container_id"]
        metric = rule["metric"]
        threshold = rule["threshold"]
        action = rule["action"]

        if container_id in self.scale_cooldowns:
            if datetime.now() < self.scale_cooldowns[container_id]:
                return

        stats = await self.vps_manager.get_vps_stats(container_id)
        if not stats:
            return

        current_value = stats.get(metric, 0)
        if current_value > threshold and action == "scale_up":
            await self._scale_up(container_id)
            self.scale_cooldowns[container_id] = datetime.now() + timedelta(minutes=config.AUTO_SCALE_COOLDOWN_MINUTES)

    async def _scale_up(self, container_id: str):
        try:
            instance = self.vps_manager.vps_instances.get(container_id)
            if not instance:
                return

            cfg = instance["config"]
            new_cpu = min(cfg["cpu_limit"] * 1.5, config.RESOURCE_LIMITS["max_cpu"])
            new_memory = min(int(cfg["memory_limit"] * 1.25), config.RESOURCE_LIMITS["max_memory_mb"])

            new_config = VPSConfig(
                cpu_limit=new_cpu,
                memory_limit=new_memory,
                storage_limit=cfg["storage_limit"],
                image=cfg["image"],
                ports=cfg["ports"],
                env_vars={},
            )
            await self.vps_manager.update_vps_config(container_id, new_config)
            logging.info(f"Scaled up {container_id[:12]}: CPU {cfg['cpu_limit']}->{new_cpu}, RAM {cfg['memory_limit']}->{new_memory}")
        except Exception as e:
            logging.error(f"Scale up error: {e}")

    @app_commands.command(name="scalerule", description="Set a scaling rule")
    @app_commands.describe(vps_id="VPS ID", metric="cpu_usage/memory_usage", threshold="Threshold percentage", action="scale_up/scale_down")
    async def set_scale_rule(self, interaction: discord.Interaction, vps_id: str, metric: str, threshold: float, action: str = "scale_up"):
        if metric not in ("cpu_usage", "memory_usage"):
            await interaction.response.send_message(embed=discord.Embed(description="Metric must be cpu_usage or memory_usage", color=0xFF0000))
            return
        if action not in ("scale_up", "scale_down"):
            await interaction.response.send_message(embed=discord.Embed(description="Action must be scale_up or scale_down", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scaling_rules (container_id, metric, threshold, duration_minutes, action) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE threshold = VALUES(threshold), action = VALUES(action)",
                (vps_id, metric, threshold, config.AUTO_SCALE_COOLDOWN_MINUTES, action),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Scale rule set: {metric} > {threshold}% -> {action}", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="scaleset", description="Manually set resource limits")
    @app_commands.describe(vps_id="VPS ID", resource="cpu/memory", limit="New limit value")
    async def scale_set(self, interaction: discord.Interaction, vps_id: str, resource: str, limit: float):
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.response.send_message(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        cfg = instance["config"]
        new_cpu = cfg["cpu_limit"]
        new_memory = cfg["memory_limit"]

        if resource == "cpu":
            new_cpu = limit
        elif resource == "memory":
            new_memory = int(limit)
        else:
            await interaction.response.send_message(embed=discord.Embed(description="Resource must be cpu or memory", color=0xFF0000))
            return

        new_config = VPSConfig(
            cpu_limit=new_cpu,
            memory_limit=new_memory,
            storage_limit=cfg["storage_limit"],
            image=cfg["image"],
            ports=cfg["ports"],
            env_vars={},
        )

        if await self.vps_manager.update_vps_config(vps_id, new_config):
            await interaction.response.send_message(embed=discord.Embed(description=f"{resource} limit set to {limit}", color=0x00FF00))
        else:
            await interaction.response.send_message(embed=discord.Embed(description="Failed to update.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(AutoScaling(bot))
