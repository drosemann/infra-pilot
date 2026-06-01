import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class BGPRouteManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="bgp_sessions", description="List BGP sessions")
    async def bgp_sessions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/bgp/sessions")
        sessions = data if isinstance(data, list) else data.get("sessions", [])
        if not sessions:
            await interaction.followup.send(embed=discord.Embed(description="No BGP sessions.", color=0xFFFF00))
            return
        embed = discord.Embed(title="BGP Sessions", color=discord.Color.blue(), timestamp=datetime.now())
        for s in sessions[:10]:
            state = s.get("state", "unknown")
            color_icon = "🟢" if state == "established" else "🟡" if state == "active" else "🔴"
            embed.add_field(name=f"{color_icon} AS{s.get('remote_as', '?')}", value=f"Peer: {s.get('peer_ip', 'N/A')} | State: {state} | Routes: {s.get('routes_received', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bgp_announce", description="Announce a BGP prefix")
    @app_commands.describe(prefix="Prefix to announce (e.g. 10.0.0.0/24)", next_hop="Next hop IP", community="BGP community (optional)")
    async def bgp_announce(self, interaction: discord.Interaction, prefix: str, next_hop: str, community: str = ""):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/bgp/announce", {"prefix": prefix, "next_hop": next_hop, "community": community})
        if result.get("status") == "announced":
            await interaction.followup.send(embed=discord.Embed(description=f"Prefix {prefix} announced via {next_hop}.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="bgp_withdraw", description="Withdraw a BGP prefix")
    @app_commands.describe(prefix="Prefix to withdraw")
    async def bgp_withdraw(self, interaction: discord.Interaction, prefix: str):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/bgp/withdraw", {"prefix": prefix})
        if result.get("status") == "withdrawn":
            await interaction.followup.send(embed=discord.Embed(description=f"Prefix {prefix} withdrawn.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))


async def setup(bot):
    await bot.add_cog(BGPRouteManager(bot))
