import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class CloneSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="clone", description="Clone a VPS instance")
    @app_commands.describe(vps_id="VPS ID to clone", new_name="Name for the clone")
    async def clone(self, interaction: discord.Interaction, vps_id: str, new_name: str):
        await interaction.response.defer()

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        new_id = await self.vps_manager.clone_vps(vps_id, new_name)
        if new_id:
            embed = discord.Embed(title="VPS Cloned", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Source", value=vps_id[:12], inline=True)
            embed.add_field(name="Clone ID", value=new_id[:12], inline=True)
            embed.add_field(name="Name", value=new_name, inline=True)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to clone VPS.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(CloneSystem(bot))
