"""Game Server Stats cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
class GameServer:
    def __init__(self, server_id: str, name: str, game: str = "minecraft", version: str = "1.21", max_players: int = 100):
        self.server_id = server_id; self.name = name; self.game = game; self.version = version; self.max_players = max_players
        self.players = random.randint(0, max_players); self.tps = random.uniform(19.0, 20.0); self.mspt = random.uniform(10, 40)
        self.cpu_percent = random.uniform(10, 80); self.ram_percent = random.uniform(20, 75)
        self.ram_used_gb = random.uniform(1, 6); self.ram_total_gb = 8; self.uptime = f"{random.randint(1, 60)}d {random.randint(0, 23)}h"
        self.status = "online"; self.region = random.choice(["NA-East", "NA-West", "EU-West", "EU-East", "Asia-East"])
        self.entities = random.randint(100, 5000); self.chunks = random.randint(100, 1200); self.map = random.choice(["world", "arena_1", "hub", "events", "creative"])
    def to_dict(self) -> Dict[str, Any]: return {"server_id": self.server_id, "name": self.name, "game": self.game, "version": self.version, "map": self.map, "players": self.players, "max_players": self.max_players, "tps": round(self.tps, 1), "mspt": round(self.mspt, 1), "cpu_percent": round(self.cpu_percent, 1), "ram_percent": round(self.ram_percent, 1), "ram_used_gb": round(self.ram_used_gb, 1), "ram_total_gb": self.ram_total_gb, "uptime": self.uptime, "status": self.status, "region": self.region, "entities": self.entities, "chunks": self.chunks}
class GameServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.servers: Dict[str, GameServer] = {}; self.monitor_loop.start()
    def cog_unload(self): self.monitor_loop.cancel()
    @tasks.loop(seconds=10)
    async def monitor_loop(self):
        for sid, sv in list(self.servers.items()):
            sv.players = random.randint(0, sv.max_players); sv.tps = random.uniform(18.0, 20.0)
            sv.mspt = random.uniform(10, 45); sv.cpu_percent = random.uniform(10, 80); sv.ram_percent = random.uniform(20, 75)
            if random.random() < 0.02: sv.status = "offline"
            else: sv.status = "online"
    @commands.group(name="server")
    async def server_group(self, ctx): pass
    @server_group.command(name="add")
    async def add_server(self, ctx, name: str, game: str = "minecraft", max_players: int = 100):
        sid = f"gs-{random.randint(10000, 99999)}"; self.servers[sid] = GameServer(server_id=sid, name=name, game=game, max_players=max_players)
        await ctx.send(f"? Added server '{name}' ({game}, {max_players} slots)")
    @server_group.command(name="list")
    async def list_servers(self, ctx):
        if not self.servers: await ctx.send("No servers"); return
        total_players = sum(sv.players for sv in self.servers.values())
        lines = [f"**Game Servers ({total_players} total players):**"]
        for sid, sv in self.servers.items(): lines.append(f"• {sv.name} ({sv.game}) - {sv.players}/{sv.max_players} - TPS:{sv.tps} MSPT:{sv.mspt:.0f}ms - {sv.status}")
        await ctx.send("\n".join(lines))
    @server_group.command(name="status")
    async def server_status(self, ctx, server_id: str):
        sv = self.servers.get(server_id)
        if not sv: await ctx.send("Server not found"); return
        await ctx.send(f"**{sv.name}**\nGame: {sv.game} v{sv.version} | Map: {sv.map}\nPlayers: {sv.players}/{sv.max_players} | TPS: {sv.tps} | MSPT: {sv.mspt:.0f}ms\nCPU: {sv.cpu_percent:.0f}% | RAM: {sv.ram_used_gb:.1f}/{sv.ram_total_gb}GB ({sv.ram_percent:.0f}%)\nEntities: {sv.entities} | Chunks: {sv.chunks} | Uptime: {sv.uptime}\nRegion: {sv.region} | Status: {sv.status}")
    @server_group.command(name="top")
    async def top_servers(self, ctx):
        sorted_servers = sorted(self.servers.values(), key=lambda s: s.players, reverse=True)[:5]
        lines = ["**Top 5 Servers (by players):**"]
        for i, sv in enumerate(sorted_servers, 1): lines.append(f"{i}. {sv.name} - {sv.players} players - TPS: {sv.tps}")
        await ctx.send("\n".join(lines))
    @server_group.command(name="health")
    async def server_health(self, ctx):
        total = len(self.servers); online = sum(1 for sv in self.servers.values() if sv.status == "online")
        low_tps = sum(1 for sv in self.servers.values() if sv.tps < 19.5)
        await ctx.send(f"**Server Health:** {online}/{total} online | {low_tps} low TPS | Avg TPS: {sum(sv.tps for sv in self.servers.values()) / max(total, 1):.1f}")
    @server_group.command(name="execute")
    async def execute_command(self, ctx, server_id: str, *, command: str):
        sv = self.servers.get(server_id)
        if not sv: await ctx.send("Server not found"); return
        await ctx.send(f"? Executed '/{command}' on {sv.name}")
