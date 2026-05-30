"""Voice Server cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
class VoiceServerInstance:
    def __init__(self, server_id: str, name: str, server_type: str = "teamspeak3", region: str = "NA-East", max_slots: int = 50):
        self.server_id = server_id; self.name = name; self.type = server_type; self.region = region
        self.host = f"{name.lower().replace(' ', '-')}.voice.infrapilot.io"; self.port = 9987 if server_type == "teamspeak3" else 64738
        self.max_slots = max_slots; self.used_slots = random.randint(0, max_slots); self.status = "online"
        self.bitrate = random.choice([32, 48, 64, 96, 128]); self.version = "3.13.7" if server_type == "teamspeak3" else "1.4.287"
        self.uptime = f"{random.randint(1, 90)}d {random.randint(0, 23)}h"; self.monthly_cost = round(max_slots * 0.15 + 1.99, 2)
        self.created_at = datetime.datetime.utcnow().isoformat()
    def to_dict(self) -> Dict[str, Any]: return {"server_id": self.server_id, "name": self.name, "type": self.type, "region": self.region, "host": self.host, "port": self.port, "max_slots": self.max_slots, "used_slots": self.used_slots, "status": self.status, "bitrate": self.bitrate, "version": self.version, "uptime": self.uptime, "monthly_cost": self.monthly_cost}
class VoiceServerProvisioning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.servers: Dict[str, VoiceServerInstance] = {}; self.monitor_loop.start()
    def cog_unload(self): self.monitor_loop.cancel()
    @tasks.loop(minutes=5)
    async def monitor_loop(self):
        for sid, sv in list(self.servers.items()): sv.used_slots = random.randint(0, sv.max_slots); sv.status = "online" if random.random() > 0.05 else "offline"
    @commands.group(name="voice")
    async def voice_group(self, ctx): pass
    @voice_group.command(name="create")
    async def create_server(self, ctx, name: str, server_type: str = "teamspeak3", max_slots: int = 50, region: str = "NA-East"):
        sid = f"sv-{random.randint(10000, 99999)}"; self.servers[sid] = VoiceServerInstance(server_id=sid, name=name, server_type=server_type, region=region, max_slots=max_slots)
        await ctx.send(f"? Created {server_type} server '{name}' ({max_slots} slots, {region})")
    @voice_group.command(name="list")
    async def list_servers(self, ctx):
        if not self.servers: await ctx.send("No voice servers"); return
        lines = ["**Voice Servers:**"]
        for sid, sv in self.servers.items(): lines.append(f"• {sv.name} ({sv.type}) - {sv.used_slots}/{sv.max_slots} - ${sv.monthly_cost}/mo - {sv.status}")
        await ctx.send("\n".join(lines))
    @voice_group.command(name="status")
    async def server_status(self, ctx, server_id: str):
        sv = self.servers.get(server_id)
        if not sv: await ctx.send("Server not found"); return
        await ctx.send(f"**{sv.name}**\nType: {sv.type} | Host: {sv.host}:{sv.port}\nSlots: {sv.used_slots}/{sv.max_slots} | Bitrate: {sv.bitrate}kbps\nRegion: {sv.region} | Uptime: {sv.uptime}\nCost: ${sv.monthly_cost}/mo | Status: {sv.status}")
    @voice_group.command(name="slots")
    async def update_slots(self, ctx, server_id: str, max_slots: int):
        sv = self.servers.get(server_id)
        if not sv: await ctx.send("Server not found"); return
        sv.max_slots = max_slots; sv.monthly_cost = round(max_slots * 0.15 + 1.99, 2); await ctx.send(f"? Updated slots to {max_slots}")
    @voice_group.command(name="restart")
    async def restart_server(self, ctx, server_id: str):
        sv = self.servers.get(server_id)
        if not sv: await ctx.send("Server not found"); return
        sv.status = "restarting"; await ctx.send(f"?? Restarting {sv.name}...")
        await asyncio.sleep(2); sv.status = "online"; await ctx.send(f"? {sv.name} restarted")
    @voice_group.command(name="delete")
    async def delete_server(self, ctx, server_id: str):
        if server_id in self.servers: del self.servers[server_id]; await ctx.send("? Deleted")
        else: await ctx.send("Not found")
