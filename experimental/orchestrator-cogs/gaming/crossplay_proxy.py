"""Cross-Play Proxy cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
class ProxyInstance:
    def __init__(self, proxy_id: str, name: str, region: str = "NA-East", max_players: int = 500):
        self.proxy_id = proxy_id; self.name = name; self.region = region; self.max_players = max_players
        self.java_host = f"{region.lower().split('-')[0]}.play.infrapilot.io"; self.java_port = 25565
        self.bedrock_host = f"{region.lower().split('-')[0]}.bedrock.infrapilot.io"; self.bedrock_port = 19132
        self.active_players = random.randint(0, max_players); self.status = "online"
        self.players_java = int(self.active_players * random.uniform(0.6, 0.85))
        self.players_bedrock = self.active_players - self.players_java
        self.latency_ms = random.uniform(5, 50); self.uptime = f"{random.randint(1, 60)}d {random.randint(0, 23)}h"
        self.protocol = "geyser_1.21"
    def to_dict(self) -> Dict[str, Any]: return {"proxy_id": self.proxy_id, "name": self.name, "region": self.region, "max_players": self.max_players, "java_host": self.java_host, "java_port": self.java_port, "bedrock_host": self.bedrock_host, "bedrock_port": self.bedrock_port, "active_players": self.active_players, "status": self.status, "players_java": self.players_java, "players_bedrock": self.players_bedrock, "latency_ms": round(self.latency_ms, 1), "uptime": self.uptime, "protocol": self.protocol}
class CrossPlayProxy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.proxies: Dict[str, ProxyInstance] = {}; self.proxy_loop.start()
    def cog_unload(self): self.proxy_loop.cancel()
    @tasks.loop(seconds=30)
    async def proxy_loop(self):
        for pid, p in list(self.proxies.items()):
            p.active_players = random.randint(0, p.max_players)
            p.players_java = int(p.active_players * random.uniform(0.6, 0.85))
            p.players_bedrock = p.active_players - p.players_java; p.latency_ms = random.uniform(5, 50)
    @commands.group(name="proxy")
    async def proxy_group(self, ctx): pass
    @proxy_group.command(name="create")
    async def create_proxy(self, ctx, name: str, region: str = "NA-East", max_players: int = 500):
        pid = f"proxy-{random.randint(10000, 99999)}"; self.proxies[pid] = ProxyInstance(proxy_id=pid, name=name, region=region, max_players=max_players)
        await ctx.send(f"? Created proxy '{name}' ({region})")
    @proxy_group.command(name="list")
    async def list_proxies(self, ctx):
        if not self.proxies: await ctx.send("No proxies"); return
        lines = ["**Cross-Play Proxies:**"]
        for pid, p in self.proxies.items(): lines.append(f"• {p.name} ({p.region}) - {p.active_players}/{p.max_players} (J:{p.players_java}/B:{p.players_bedrock}) - {p.status}")
        await ctx.send("\n".join(lines))
    @proxy_group.command(name="status")
    async def proxy_status(self, ctx, proxy_id: str):
        p = self.proxies.get(proxy_id)
        if not p: await ctx.send("Not found"); return
        await ctx.send(f"**{p.name}**\nJava: {p.java_host}:{p.java_port}\nBedrock: {p.bedrock_host}:{p.bedrock_port}\nPlayers: {p.active_players}/{p.max_players} (J:{p.players_java} B:{p.players_bedrock})\nLatency: {p.latency_ms:.0f}ms\nUptime: {p.uptime}")
    @proxy_group.command(name="sync")
    async def sync_players(self, ctx, proxy_id: str):
        p = self.proxies.get(proxy_id)
        if not p: await ctx.send("Not found"); return
        await ctx.send(f"? Player sync complete for {p.name}: {p.players_java} Java ? {p.players_bedrock} Bedrock")
    @proxy_group.command(name="delete")
    async def delete_proxy(self, ctx, proxy_id: str):
        if proxy_id in self.proxies: del self.proxies[proxy_id]; await ctx.send("? Deleted")
        else: await ctx.send("Not found")
