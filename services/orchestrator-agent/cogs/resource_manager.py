import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class ResourceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.resource_pools = {}

    @app_commands.command(name="resourcepoolcreate", description="Create a resource pool")
    @app_commands.describe(name="Pool name", cpu_ratio="CPU oversubscription ratio", mem_ratio="Memory oversubscription ratio")
    async def pool_create(self, interaction: discord.Interaction, name: str, cpu_ratio: float = 4.0, mem_ratio: float = 2.0):
        if name in self.resource_pools:
            await interaction.response.send_message(embed=discord.Embed(description="Pool already exists.", color=0xFF0000))
            return
        self.resource_pools[name] = {
            "name": name,
            "cpu_ratio": cpu_ratio,
            "mem_ratio": mem_ratio,
            "members": [],
            "created_at": datetime.now().isoformat(),
        }
        await interaction.response.send_message(embed=discord.Embed(description=f"Pool '{name}' created (CPU ratio: {cpu_ratio}x, Mem ratio: {mem_ratio}x)", color=0x00FF00))

    @app_commands.command(name="resourcepooldelete", description="Delete a resource pool")
    @app_commands.describe(name="Pool name")
    async def pool_delete(self, interaction: discord.Interaction, name: str):
        if name not in self.resource_pools:
            await interaction.response.send_message(embed=discord.Embed(description="Pool not found.", color=0xFF0000))
            return
        del self.resource_pools[name]
        await interaction.response.send_message(embed=discord.Embed(description=f"Pool '{name}' deleted.", color=0x00FF00))

    @app_commands.command(name="resourcepoollist", description="List resource pools")
    async def pool_list(self, interaction: discord.Interaction):
        if not self.resource_pools:
            await interaction.response.send_message(embed=discord.Embed(description="No resource pools.", color=0xFFFF00))
            return

        embed = discord.Embed(title="Resource Pools", color=discord.Color.blue())
        for name, pool in self.resource_pools.items():
            total_cpu = sum(
                self.vps_manager.vps_instances.get(m, {}).get("config", {}).get("cpu_limit", 0)
                for m in pool["members"]
            )
            total_mem = sum(
                self.vps_manager.vps_instances.get(m, {}).get("config", {}).get("memory_limit", 0)
                for m in pool["members"]
            )
            embed.add_field(
                name=name,
                value=f"Members: {len(pool['members'])}\nCPU ratio: {pool['cpu_ratio']}x\nMem ratio: {pool['mem_ratio']}x\nAllocated CPU: {total_cpu}\nAllocated Mem: {total_mem}MB",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resourcepooladd", description="Add VPS to a pool")
    @app_commands.describe(pool_name="Pool name", vps_id="VPS ID")
    async def pool_add(self, interaction: discord.Interaction, pool_name: str, vps_id: str):
        if pool_name not in self.resource_pools:
            await interaction.response.send_message(embed=discord.Embed(description="Pool not found.", color=0xFF0000))
            return
        if vps_id not in self.vps_manager.vps_instances:
            await interaction.response.send_message(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return
        if vps_id in self.resource_pools[pool_name]["members"]:
            await interaction.response.send_message(embed=discord.Embed(description="Already in pool.", color=0xFFFF00))
            return
        self.resource_pools[pool_name]["members"].append(vps_id)
        await interaction.response.send_message(embed=discord.Embed(description=f"VPS {vps_id[:12]} added to pool '{pool_name}'.", color=0x00FF00))


async def setup(bot):
    await bot.add_cog(ResourceManager(bot))
