import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class Cleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    async def _collect_cleanup_data(self, vps_id: str = None) -> dict:
        data = {"docker_images": 0, "dangling_images": 0, "volumes": 0, "container_logs": 0}

        try:
            if vps_id:
                container = self.vps_manager.client.containers.get(vps_id)
                exit_code, output = container.exec_run("du -sh /var/log/ 2>/dev/null | cut -f1")
                if exit_code == 0:
                    data["container_logs"] = output.decode().strip() or 0
            else:
                # System-wide cleanup data
                images = self.vps_manager.client.images.list(all=True)
                data["docker_images"] = len(images)
                dangling = self.vps_manager.client.images.list(filters={"dangling": True})
                data["dangling_images"] = len(dangling)

                volumes = self.vps_manager.client.volumes.list()
                data["volumes"] = len(volumes)
        except Exception:
            pass

        return data

    @app_commands.command(name="cleanupdryrun", description="Show what would be cleaned up")
    async def cleanup_dry_run(self, interaction: discord.Interaction, vps_id: str = None):
        await interaction.response.defer()
        data = await self._collect_cleanup_data(vps_id)

        embed = discord.Embed(title="Cleanup Dry Run", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Dangling Images", value=str(data.get("dangling_images", 0)), inline=True)
        embed.add_field(name="Total Images", value=str(data.get("docker_images", 0)), inline=True)
        embed.add_field(name="Volumes", value=str(data.get("volumes", 0)), inline=True)

        if vps_id:
            embed.add_field(name="Container Logs", value=str(data.get("container_logs", 0)), inline=True)

        embed.add_field(name="Would Clean", value="Dangling images, unused volumes, package cache", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cleanuprun", description="Run resource cleanup")
    @app_commands.describe(vps_id="VPS ID (optional - cleans all if omitted)")
    async def cleanup_run(self, interaction: discord.Interaction, vps_id: str = None):
        await interaction.response.defer()

        results = []
        try:
            if vps_id:
                container = self.vps_manager.client.containers.get(vps_id)
                exit_code, output = container.exec_run("apt clean -qq 2>&1")
                results.append(f"Package cache: {'cleaned' if exit_code == 0 else 'failed'}")

                exit_code, output = container.exec_run("rm -rf /var/log/*.log 2>&1")
                results.append(f"Logs: {'cleaned' if exit_code == 0 else 'failed'}")
            else:
                # System-wide cleanup
                deleted_images = self.vps_manager.client.images.prune(filters={"dangling": True})
                results.append(f"Dangling images: {len(deleted_images.get('ImagesDeleted', []))} removed")

                deleted_volumes = self.vps_manager.client.volumes.prune()
                results.append(f"Unused volumes: {len(deleted_volumes.get('VolumesDeleted', []))} removed")

        except Exception as e:
            results.append(f"Error: {str(e)}")

        embed = discord.Embed(title="Cleanup Complete", color=discord.Color.green(), timestamp=datetime.now())
        embed.add_field(name="Results", value="\n".join(f"• {r}" for r in results), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Cleanup(bot))
