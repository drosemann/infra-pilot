import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class AppMarketplace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="marketplace_search", description="Search one-click apps")
    @app_commands.describe(query="Search query", category="App category")
    async def marketplace_search(self, interaction: discord.Interaction, query: str = "", category: str = ""):
        await interaction.response.defer()
        params = f"?q={query}" if query else ""
        params += f"&category={category}" if category else ""
        data = await self.api.get(f"/api/marketplace/apps{params}")
        apps = data if isinstance(data, list) else data.get("apps", [])
        if not apps:
            await interaction.followup.send(embed=discord.Embed(description="No apps found.", color=0xFFFF00))
            return
        embed = discord.Embed(title="One-Click App Marketplace", color=discord.Color.blue(), timestamp=datetime.now())
        for app in apps[:10]:
            embed.add_field(name=f"{app.get('name', 'Unknown')} v{app.get('version', '?')}", value=f"{app.get('description', '')[:80]}... | Installs: {app.get('install_count', 0)} | Price: ${app.get('price', 0):.2f}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="marketplace_install", description="Install a one-click app")
    @app_commands.describe(app_id="App ID", target_server="Target server ID")
    async def marketplace_install(self, interaction: discord.Interaction, app_id: str, target_server: str = ""):
        await interaction.response.defer()
        result = await self.api.post(f"/api/marketplace/apps/{app_id}/install", {"target_server": target_server})
        if result.get("status") == "deploying":
            embed = discord.Embed(title="App Deploying", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="App", value=result.get("app_name", app_id))
            embed.add_field(name="Deployment ID", value=result.get("deployment_id", ""))
            embed.add_field(name="Status", value=result.get("status", "unknown"))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="marketplace_deployments", description="List app deployments")
    async def marketplace_deployments(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/apps/deployments")
        deployments = data if isinstance(data, list) else data.get("deployments", [])
        if not deployments:
            await interaction.followup.send(embed=discord.Embed(description="No deployments.", color=0xFFFF00))
            return
        embed = discord.Embed(title="App Deployments", color=discord.Color.blue(), timestamp=datetime.now())
        for d in deployments[:10]:
            status_icon = "🟢" if d.get("status") == "running" else "🟡" if d.get("status") == "deploying" else "🔴"
            embed.add_field(name=f"{status_icon} {d.get('app_name', 'Unknown')}", value=f"Server: {d.get('server_id', 'N/A')} | URL: {d.get('url', 'N/A')} | Deployed: {d.get('deployed_at', 'N/A')}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AppMarketplace(bot))
