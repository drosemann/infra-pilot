import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class ServerMigration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="migrate", description="Migrate a VPS to a target host")
    @app_commands.describe(vps_id="VPS ID to migrate", target_host="Target hostname or IP", migration_type="live or cold")
    async def migrate(self, interaction: discord.Interaction, vps_id: str, target_host: str, migration_type: str = "cold"):
        await interaction.response.defer()

        if migration_type not in ("live", "cold"):
            await interaction.followup.send(embed=discord.Embed(description="Migration type must be 'live' or 'cold'.", color=0xFF0000))
            return

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        embed = discord.Embed(title=f"Migration: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Target Host", value=target_host, inline=True)
        embed.add_field(name="Type", value=migration_type.capitalize(), inline=True)
        embed.add_field(name="Status", value="In progress...", inline=False)

        status_msg = await interaction.followup.send(embed=embed)

        if migration_type == "cold":
            await self.vps_manager.stop_vps(vps_id)

        success = await self.vps_manager.migrate_vps(vps_id, target_host)

        if success:
            embed.set_field_at(2, name="Status", value="Completed - image saved for transfer", inline=False)
        else:
            embed.set_field_at(2, name="Status", value="Failed", inline=False)
            if migration_type == "cold":
                await self.vps_manager.start_vps(vps_id)

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="migratestatus", description="Check migration status")
    @app_commands.describe(vps_id="VPS ID")
    async def migrate_status(self, interaction: discord.Interaction, vps_id: str):
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.response.send_message(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        embed = discord.Embed(title=f"Migration Status: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current Host", value=instance.get("host", "unknown"), inline=True)
        embed.add_field(name="Status", value=instance.get("status", "unknown"), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerMigration(bot))
