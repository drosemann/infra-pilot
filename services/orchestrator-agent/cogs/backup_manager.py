import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional
import logging

from config import config
from vps_manager import VPSManager


class BackupManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.backup_loop.start()

    def cog_unload(self):
        self.backup_loop.cancel()

    @tasks.loop(hours=24)
    async def backup_loop(self):
        try:
            now = datetime.now()
            for container_id in self.vps_manager.vps_instances:
                retention = "daily"
                if now.weekday() == 0:
                    retention = "weekly"
                if now.day == 1:
                    retention = "monthly"
                await self.vps_manager.create_backup(container_id, retention)
                logging.info(f"Auto-backup created for {container_id[:12]} ({retention})")
        except Exception as e:
            logging.error(f"Backup loop error: {e}")

    @app_commands.command(name="backup", description="Create a VPS backup")
    @app_commands.describe(container_id="Container ID", retention="daily/weekly/monthly")
    async def backup(self, interaction: discord.Interaction, container_id: str, retention: str = "daily"):
        await interaction.response.defer()
        if retention not in config.BACKUP_RETENTION:
            await interaction.followup.send(embed=discord.Embed(description="Retention must be daily/weekly/monthly", color=0xFF0000))
            return

        backup_id = await self.vps_manager.create_backup(container_id, retention)
        if backup_id:
            embed = discord.Embed(title="Backup Created", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Container", value=container_id[:12], inline=True)
            embed.add_field(name="Backup ID", value=backup_id[:12], inline=True)
            embed.add_field(name="Retention", value=retention, inline=True)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to create backup.", color=0xFF0000))

    @app_commands.command(name="backuplist", description="List backups for a VPS")
    @app_commands.describe(container_id="Container ID")
    async def backup_list(self, interaction: discord.Interaction, container_id: str):
        await interaction.response.defer()
        backups = await self.vps_manager.list_backups(container_id)
        if not backups:
            await interaction.followup.send(embed=discord.Embed(description="No backups found.", color=0xFFFF00))
            return

        embed = discord.Embed(title=f"Backups: {container_id[:12]}", color=discord.Color.blue())
        for b in backups[:10]:
            embed.add_field(
                name=b.get("name", b.get("image_id", "unknown")[:20]),
                value=f"Type: {b.get('retention_type', 'manual')}\nDate: {b.get('created_at', 'N/A')}\nID: `{b.get('image_id', 'N/A')[:12]}`",
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="restore", description="Restore a VPS from backup")
    @app_commands.describe(container_id="Container ID", backup_id="Backup image ID")
    async def restore(self, interaction: discord.Interaction, container_id: str, backup_id: str):
        await interaction.response.defer()
        if await self.vps_manager.restore_backup(container_id, backup_id):
            await interaction.followup.send(embed=discord.Embed(description=f"VPS restored from backup.", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to restore backup.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(BackupManager(bot))
