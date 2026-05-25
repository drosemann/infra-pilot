import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional
import logging

from config import config
from vps_manager import VPSManager


class AlertManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.alert_check_loop.start()

    def cog_unload(self):
        self.alert_check_loop.cancel()

    @tasks.loop(minutes=2)
    async def alert_check_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alerts WHERE enabled = 1")
            alerts = cursor.fetchall()
            cursor.close()
            conn.close()

            for alert in alerts:
                await self._evaluate_alert(alert)
        except Exception as e:
            logging.error(f"Alert check error: {e}")

    async def _evaluate_alert(self, alert: dict):
        container_id = alert.get("container_id")
        if not container_id:
            return

        stats = await self.vps_manager.get_vps_stats(container_id)
        if not stats:
            return

        alert_type = alert["alert_type"]
        threshold = alert["threshold"]
        current_value = stats.get(alert_type, 0)

        if current_value > threshold:
            await self._send_alert(alert, current_value)

    async def _send_alert(self, alert: dict, current_value: float):
        user_id = alert["user_id"]
        try:
            user = await self.bot.fetch_user(int(user_id))
            if user:
                embed = discord.Embed(title=f"Alert: {alert['alert_type'].upper()}", color=discord.Color.red(), timestamp=datetime.now())
                embed.add_field(name="Container", value=alert.get("container_id", "N/A")[:12], inline=True)
                embed.add_field(name="Metric", value=alert["alert_type"], inline=True)
                embed.add_field(name="Current Value", value=f"{current_value:.1f}", inline=True)
                embed.add_field(name="Threshold", value=str(alert["threshold"]), inline=True)
                embed.add_field(name="Channel", value=alert.get("channel", "dm"), inline=True)
                await user.send(embed=embed)
        except Exception as e:
            logging.error(f"Error sending alert: {e}")

    @app_commands.command(name="alertcreate", description="Create a resource usage alert")
    @app_commands.describe(threshold="Threshold percentage", alert_type="cpu_usage/memory_usage/disk_usage", vps_id="VPS ID (optional)", channel="dm/webhook")
    async def alert_create(self, interaction: discord.Interaction, threshold: float, alert_type: str = "cpu_usage", vps_id: str = None, channel: str = "dm"):
        if alert_type not in ("cpu_usage", "memory_usage", "disk_usage"):
            await interaction.response.send_message(embed=discord.Embed(description="Type must be cpu_usage/memory_usage/disk_usage", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO alerts (user_id, container_id, alert_type, threshold, channel) VALUES (%s, %s, %s, %s, %s)",
                (str(interaction.user.id), vps_id, alert_type, threshold, channel),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Alert created: {alert_type} > {threshold}%", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="alertlist", description="List your alerts")
    async def alert_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alerts WHERE user_id = %s ORDER BY created_at DESC", (str(interaction.user.id),))
            alerts = cursor.fetchall()
            cursor.close()
            conn.close()

            if not alerts:
                await interaction.response.send_message(embed=discord.Embed(description="No alerts configured.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Your Alerts", color=discord.Color.blue())
            for a in alerts:
                embed.add_field(
                    name=f"{'Enabled' if a['enabled'] else 'Disabled'} - {a['alert_type']}",
                    value=f"Threshold: {a['threshold']}%\nContainer: {a.get('container_id', 'all')[:12] if a.get('container_id') else 'all'}\nChannel: {a.get('channel', 'dm')}",
                    inline=False,
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(AlertManager(bot))
