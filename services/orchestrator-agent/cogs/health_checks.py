import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, Dict
from datetime import datetime
import logging

from config import config
from vps_manager import VPSManager


class HealthChecks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.check_types = {"ping", "port", "process", "api"}
        self.health_check_loop.start()

    def cog_unload(self):
        self.health_check_loop.cancel()

    @tasks.loop(seconds=config.HEALTH_CHECK_INTERVAL_SECONDS)
    async def health_check_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM health_checks WHERE enabled = 1")
            checks = cursor.fetchall()
            cursor.close()
            conn.close()

            for check in checks:
                result = await self.vps_manager.run_health_check(
                    check["container_id"], check["check_type"], check["target"]
                )
                self._update_check_status(check["id"], result["status"])
                if result["status"] == "failed":
                    await self._notify_failure(check, result)
        except Exception as e:
            logging.error(f"Health check loop error: {e}")

    def _update_check_status(self, check_id: int, status: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE health_checks SET last_check = NOW(), last_status = %s WHERE id = %s",
                (status, check_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error updating check status: {e}")

    async def _notify_failure(self, check: Dict, result: Dict):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM vps_containers WHERE container_id = %s", (check["container_id"],))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                user = await self.bot.fetch_user(int(row[0]))
                if user:
                    embed = discord.Embed(title="Health Check Failed", color=discord.Color.red())
                    embed.add_field(name="Container", value=check["container_id"][:12], inline=True)
                    embed.add_field(name="Check Type", value=check["check_type"], inline=True)
                    embed.add_field(name="Response", value=f"{result['response_time_ms']}ms", inline=True)
                    embed.add_field(name="Error", value=result.get("error", "Unknown"), inline=False)
                    await user.send(embed=embed)
        except Exception as e:
            logging.error(f"Error notifying failure: {e}")

    @app_commands.command(name="health", description="Run health check on a VPS")
    @app_commands.describe(container_id="Container ID")
    async def health_check(self, interaction: discord.Interaction, container_id: str):
        await interaction.response.defer()
        results = []
        for check_type in self.check_types:
            result = await self.vps_manager.run_health_check(container_id, check_type)
            results.append(result)

        embed = discord.Embed(title=f"Health Check: {container_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        for r in results:
            status_emoji = "✅" if r["status"] == "passed" else "❌"
            embed.add_field(
                name=r.get("type", "check"),
                value=f"{status_emoji} {r['status']} ({r['response_time_ms']}ms)",
                inline=True,
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="healthcreate", description="Create a health check")
    @app_commands.describe(container_id="Container ID", check_type="ping/port/process/api", target="Target (host:port, process name, URL)")
    async def health_create(self, interaction: discord.Interaction, container_id: str, check_type: str, target: str = None):
        if check_type not in self.check_types:
            await interaction.response.send_message(embed=discord.Embed(description=f"Invalid type. Options: {', '.join(self.check_types)}", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO health_checks (container_id, check_type, target, interval_seconds) VALUES (%s, %s, %s, %s)",
                (container_id, check_type, target, config.HEALTH_CHECK_INTERVAL_SECONDS),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Health check created: {check_type} on {container_id[:12]}", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="healthlist", description="List active health checks")
    async def health_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM health_checks ORDER BY created_at DESC")
            checks = cursor.fetchall()
            cursor.close()
            conn.close()

            if not checks:
                await interaction.response.send_message(embed=discord.Embed(description="No health checks configured.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Health Checks", color=discord.Color.blue())
            for c in checks:
                embed.add_field(
                    name=f"{c['check_type']} - {c['container_id'][:12]}",
                    value=f"Status: {c.get('last_status', 'pending')}\nTarget: {c.get('target', 'N/A')}\nInterval: {c['interval_seconds']}s",
                    inline=False,
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(HealthChecks(bot))
