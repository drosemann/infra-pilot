import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class VPNService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="vpn_list", description="List VPN servers")
    async def vpn_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/vpn/servers")
        servers = data if isinstance(data, list) else data.get("servers", [])
        if not servers:
            await interaction.followup.send(embed=discord.Embed(description="No VPN servers configured.", color=0xFFFF00))
            return
        embed = discord.Embed(title="VPN Servers", color=discord.Color.blue(), timestamp=datetime.now())
        for s in servers[:10]:
            status_icon = "🟢" if s.get("status") == "running" else "🔴"
            embed.add_field(name=f"{status_icon} {s.get('name', 'Unknown')}", value=f"Type: {s.get('vpn_type', 'N/A')} | Port: {s.get('port', 0)} | Clients: {s.get('active_clients', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="vpn_create", description="Create a new VPN server")
    @app_commands.describe(name="VPN server name", vpn_type="VPN type (wireguard/openip/pptp)", port="Listen port")
    async def vpn_create(self, interaction: discord.Interaction, name: str, vpn_type: str = "wireguard", port: int = 51820):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/vpn/servers", {"name": name, "vpn_type": vpn_type, "port": port})
        if "id" in result:
            embed = discord.Embed(title="VPN Server Created", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Name", value=result.get("name", name))
            embed.add_field(name="Type", value=result.get("vpn_type", vpn_type))
            embed.add_field(name="Port", value=str(result.get("port", port)))
            embed.add_field(name="ID", value=result.get("id", ""))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="vpn_delete", description="Delete a VPN server")
    @app_commands.describe(server_id="VPN server ID")
    async def vpn_delete(self, interaction: discord.Interaction, server_id: str):
        await interaction.response.defer()
        result = await self.api.delete(f"/api/networking/vpn/servers/{server_id}")
        if result.get("success"):
            await interaction.followup.send(embed=discord.Embed(description=f"VPN server {server_id} deleted.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))


async def setup(bot):
    await bot.add_cog(VPNService(bot))
