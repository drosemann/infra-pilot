import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class SnapshotSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="snapshotcreate", description="Create a VPS snapshot")
    @app_commands.describe(vps_id="VPS ID", name="Snapshot name (optional)")
    async def snapshot_create(self, interaction: discord.Interaction, vps_id: str, name: str = None):
        await interaction.response.defer()

        snapshot_id = await self.vps_manager.create_snapshot(vps_id, name)
        if snapshot_id:
            embed = discord.Embed(title="Snapshot Created", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="VPS", value=vps_id[:12], inline=True)
            embed.add_field(name="Snapshot ID", value=snapshot_id[:12], inline=True)
            embed.add_field(name="Name", value=name or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}", inline=True)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to create snapshot.", color=0xFF0000))

    @app_commands.command(name="snapshotlist", description="List snapshots for a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def snapshot_list(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()
        snapshots = await self.vps_manager.list_snapshots(vps_id)
        if not snapshots:
            await interaction.followup.send(embed=discord.Embed(description="No snapshots found.", color=0xFFFF00))
            return

        embed = discord.Embed(title=f"Snapshots: {vps_id[:12]}", color=discord.Color.blue())
        for s in snapshots[:10]:
            embed.add_field(
                name=s.get("name", "unnamed"),
                value=f"Date: {s.get('created_at', 'N/A')}\nType: {s.get('snapshot_type', 'manual')}\nID: `{s.get('image_id', 'N/A')[:12]}`",
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="snapshotrestore", description="Restore a VPS from a snapshot")
    @app_commands.describe(vps_id="VPS ID", snapshot_id="Snapshot image ID")
    async def snapshot_restore(self, interaction: discord.Interaction, vps_id: str, snapshot_id: str):
        await interaction.response.defer()
        if await self.vps_manager.restore_snapshot(vps_id, snapshot_id):
            await interaction.followup.send(embed=discord.Embed(description="VPS restored from snapshot.", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to restore snapshot.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(SnapshotSystem(bot))
