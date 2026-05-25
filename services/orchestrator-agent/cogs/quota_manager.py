import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class QuotaManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="quotaset", description="Set resource quota for a user (Admin)")
    @app_commands.describe(user_id="Discord user ID", resource="cpu_cores/memory_mb/storage_gb/bandwidth_gb/vps_count", limit="Limit value")
    async def quota_set(self, interaction: discord.Interaction, user_id: str, resource: str, limit: int):
        if str(interaction.user.id) not in config.WHITELIST_IDS:
            await interaction.response.send_message(embed=discord.Embed(description="Admin only.", color=0xFF0000), ephemeral=True)
            return

        valid_resources = ("cpu_cores", "memory_mb", "storage_gb", "bandwidth_gb", "vps_count")
        if resource not in valid_resources:
            await interaction.response.send_message(embed=discord.Embed(description=f"Resource must be one of: {', '.join(valid_resources)}", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO resource_quotas (user_id, resource_type, soft_limit, hard_limit) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE soft_limit = VALUES(soft_limit), hard_limit = VALUES(hard_limit)",
                (user_id, resource, limit, limit),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Quota set: {resource} = {limit} for user {user_id}", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="quotaget", description="Get quotas for a user (Admin)")
    @app_commands.describe(user_id="Discord user ID")
    async def quota_get(self, interaction: discord.Interaction, user_id: str):
        if str(interaction.user.id) not in config.WHITELIST_IDS:
            await interaction.response.send_message(embed=discord.Embed(description="Admin only.", color=0xFF0000), ephemeral=True)
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM resource_quotas WHERE user_id = %s", (user_id,))
            quotas = cursor.fetchall()
            cursor.close()
            conn.close()

            embed = discord.Embed(title=f"Quotas: {user_id}", color=discord.Color.blue())
            if not quotas:
                embed.description = "No custom quotas set. Using defaults."
                for k, v in config.QUOTA_DEFAULTS.items():
                    embed.add_field(name=k, value=str(v), inline=True)
            else:
                for q in quotas:
                    embed.add_field(name=q["resource_type"], value=f"Soft: {q['soft_limit']} | Hard: {q['hard_limit']} | Used: {q.get('usage', 0)}", inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(QuotaManager(bot))
