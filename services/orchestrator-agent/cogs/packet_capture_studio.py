import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class PacketCaptureStudio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="capture_list", description="List capture sessions")
    async def capture_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/networking/capture/sessions")
        sessions = data if isinstance(data, list) else data.get("sessions", [])
        if not sessions:
            await interaction.followup.send(embed=discord.Embed(description="No capture sessions.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Capture Sessions", color=discord.Color.blue(), timestamp=datetime.now())
        for s in sessions[:10]:
            status_icon = "🟢" if s.get("status") == "active" else "⏹️" if s.get("status") == "completed" else "🔴"
            embed.add_field(name=f"{status_icon} {s.get('name', 'Unknown')}", value=f"Interface: {s.get('interface', 'N/A')} | Filter: {s.get('filter', 'none')} | Packets: {s.get('packet_count', 0)}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="capture_start", description="Start a packet capture")
    @app_commands.describe(name="Session name", interface="Network interface", filter_expr="BPF filter expression", duration="Capture duration in seconds")
    async def capture_start(self, interaction: discord.Interaction, name: str, interface: str = "eth0", filter_expr: str = "", duration: int = 60):
        await interaction.response.defer()
        result = await self.api.post("/api/networking/capture/sessions", {"name": name, "interface": interface, "filter": filter_expr, "duration": duration})
        if "id" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"Capture {name} started on {interface}. Session ID: {result.get('id', '')}", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="capture_stop", description="Stop a capture session")
    @app_commands.describe(session_id="Session ID")
    async def capture_stop(self, interaction: discord.Interaction, session_id: str):
        await interaction.response.defer()
        result = await self.api.post(f"/api/networking/capture/sessions/{session_id}/stop", {})
        if result.get("status") == "stopped":
            await interaction.followup.send(embed=discord.Embed(description=f"Capture {session_id} stopped.", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="capture_analyze", description="Analyze captured packets")
    @app_commands.describe(session_id="Session ID")
    async def capture_analyze(self, interaction: discord.Interaction, session_id: str):
        await interaction.response.defer()
        result = await self.api.get(f"/api/networking/capture/sessions/{session_id}/analysis")
        embed = discord.Embed(title=f"Capture Analysis: {session_id}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Total Packets", value=str(result.get("total_packets", 0)), inline=True)
        embed.add_field(name="Protocols", value=result.get("protocol_summary", "N/A"), inline=True)
        embed.add_field(name="Top Talkers", value=result.get("top_talkers", "N/A"), inline=False)
        if result.get("anomalies"):
            embed.add_field(name="Anomalies", value="\n".join(f"• {a}" for a in result["anomalies"][:5]), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PacketCaptureStudio(bot))
