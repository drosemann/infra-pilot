import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class ReverseProxyCatalog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="proxy_list", description="List reverse proxy instances")
    async def proxy_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/proxy/instances")
        instances = data if isinstance(data, list) else data.get("instances", [])
        if not instances:
            await interaction.followup.send(embed=discord.Embed(description="No proxy instances.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Reverse Proxy Instances", color=discord.Color.blue(), timestamp=datetime.now())
        for inst in instances[:10]:
            status_icon = "🟢" if inst.get("status") == "running" else "🔴"
            embed.add_field(name=f"{status_icon} {inst.get('name', 'Unknown')}", value=f"Type: {inst.get('proxy_type', 'N/A')} | Hosts: {inst.get('vhost_count', 0)} | Upstreams: {inst.get('upstream_count', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="proxy_create", description="Create a reverse proxy instance")
    @app_commands.describe(name="Proxy name", proxy_type="nginx/caddy/traefik")
    async def proxy_create(self, interaction: discord.Interaction, name: str, proxy_type: str = "nginx"):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/proxy/instances", {"name": name, "proxy_type": proxy_type})
        if "id" in result:
            embed = discord.Embed(title="Proxy Created", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Name", value=result.get("name", name))
            embed.add_field(name="Type", value=result.get("proxy_type", proxy_type))
            embed.add_field(name="ID", value=result.get("id", ""))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="proxy_delete", description="Delete a proxy instance")
    @app_commands.describe(instance_id="Instance ID")
    async def proxy_delete(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        result = await self.api.delete(f"/api/networking/proxy/instances/{instance_id}")
        if result.get("success"):
            await interaction.followup.send(embed=discord.Embed(description=f"Proxy {instance_id} deleted.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="proxy_config", description="Get proxy config")
    @app_commands.describe(instance_id="Instance ID")
    async def proxy_config(self, interaction: discord.Interaction, instance_id: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/networking/proxy/instances/{instance_id}/config")
        config_text = result.get("config", "No config")
        if len(config_text) > 1900:
            config_text = config_text[:1900] + "..."
        embed = discord.Embed(title=f"Proxy Config: {instance_id}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Configuration", value=f"```nginx\n{config_text}\n```", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ReverseProxyCatalog(bot))
