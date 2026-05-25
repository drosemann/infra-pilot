import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class UpdateManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="updatecheck", description="Check for OS package updates on a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def update_check(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        try:
            container = self.vps_manager.client.containers.get(vps_id)
            exit_code, output = container.exec_run("apt list --upgradable 2>/dev/null | tail -n +2")

            if exit_code != 0:
                await interaction.followup.send(embed=discord.Embed(description="Failed to check updates.", color=0xFF0000))
                return

            lines = [l for l in output.decode().strip().split("\n") if l.strip()]
            embed = discord.Embed(title=f"Available Updates: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Updates Available", value=str(len(lines)), inline=True)

            if lines:
                update_list = "\n".join(lines[:10])
                if len(lines) > 10:
                    update_list += f"\n... and {len(lines) - 10} more"
                embed.add_field(name="Packages", value=update_list[:1024], inline=False)
            else:
                embed.add_field(name="Packages", value="All packages up to date", inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="updateapply", description="Apply OS package updates on a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def update_apply(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        try:
            container = self.vps_manager.client.containers.get(vps_id)
            exit_code, output = container.exec_run("apt update -qq && apt upgrade -y -qq 2>&1 | tail -5")

            result = output.decode().strip() if exit_code == 0 else "Update failed"
            embed = discord.Embed(title=f"Updates Applied: {vps_id[:12]}", color=discord.Color.green() if exit_code == 0 else discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Result", value=result[:1024], inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(UpdateManager(bot))
