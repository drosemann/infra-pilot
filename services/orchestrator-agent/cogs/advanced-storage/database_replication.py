"""Database Replication cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List, Optional
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
REPLICATION_MODES = ["async_stream", "sync", "log_shipping", "multi_master"]
class DatabaseNode:
    def __init__(self, node_id: str, name: str, host: str, role: str = "master"):
        self.node_id = node_id; self.name = name; self.host = host; self.role = role
        self.status = "online"; self.lag_bytes = 0; self.lag_seconds = 0.0
        self.connections = random.randint(10, 200); self.queries_per_sec = random.randint(100, 5000)
        self.cpu_percent = random.uniform(10, 70); self.ram_percent = random.uniform(20, 80)
        self.disk_usage_gb = random.uniform(10, 500); self.disk_total_gb = 1024
        self.last_heartbeat = datetime.datetime.utcnow().isoformat()
    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "name": self.name, "host": self.host, "role": self.role, "status": self.status, "lag_bytes": self.lag_bytes, "lag_seconds": round(self.lag_seconds, 2), "connections": self.connections, "queries_per_sec": self.queries_per_sec, "cpu_percent": round(self.cpu_percent, 1), "ram_percent": round(self.ram_percent, 1), "disk_used_gb": round(self.disk_usage_gb, 1), "disk_total_gb": self.disk_total_gb, "disk_percent": round(self.disk_usage_gb / self.disk_total_gb * 100, 1)}

class ReplicationSet:
    def __init__(self, set_id: str, name: str, mode: str):
        self.set_id = set_id; self.name = name; self.mode = mode; self.nodes: List[DatabaseNode] = []
        self.status = "healthy"; self.master_node: Optional[DatabaseNode] = None
        self.created_at = datetime.datetime.utcnow().isoformat()
    def to_dict(self) -> Dict[str, Any]:
        return {"set_id": self.set_id, "name": self.name, "mode": self.mode, "status": self.status, "node_count": len(self.nodes), "master": self.master_node.name if self.master_node else None, "created_at": self.created_at, "nodes": [n.to_dict() for n in self.nodes]}

class DatabaseReplication(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.sets: Dict[str, ReplicationSet] = {}
        self.replication_loop.start()
    def cog_unload(self): self.replication_loop.cancel()
    @tasks.loop(seconds=30)
    async def replication_loop(self):
        for sid, rs in list(self.sets.items()):
            for node in rs.nodes:
                node.lag_bytes = random.randint(0, 1024*1024); node.lag_seconds = random.uniform(0, 5)
                node.connections = random.randint(10, 200); node.queries_per_sec = random.randint(100, 5000)
                node.cpu_percent = random.uniform(10, 70); node.ram_percent = random.uniform(20, 80)
            if rs.master_node and random.random() < 0.05:
                logger.warning(f"Simulating failover for replication set {rs.name}")
    @commands.group(name="replication")
    async def repl_group(self, ctx): pass
    @repl_group.command(name="create")
    async def create_set(self, ctx, name: str, mode: str = "async_stream", node_count: int = 3):
        sid = f"rs-{random.randint(10000, 99999)}"; rs = ReplicationSet(set_id=sid, name=name, mode=mode)
        for i in range(node_count):
            node = DatabaseNode(node_id=f"db-{sid}-{i}", name=f"{name}-db-{i}", host=f"10.0.{random.randint(1,10)}.{i+1}", role="master" if i == 0 else "replica")
            rs.nodes.append(node)
        rs.master_node = rs.nodes[0]; self.sets[sid] = rs
        await ctx.send(f"? Created replication set '{name}' ({mode}) with {node_count} nodes")
    @repl_group.command(name="list")
    async def list_sets(self, ctx):
        if not self.sets: await ctx.send("No replication sets"); return
        lines = ["**Replication Sets:**"]
        for sid, rs in self.sets.items(): lines.append(f"• {rs.name} ({rs.mode}) - {len(rs.nodes)} nodes - {rs.status}")
        await ctx.send("\n".join(lines))
    @repl_group.command(name="status")
    async def set_status(self, ctx, set_id: str):
        rs = self.sets.get(set_id)
        if not rs: await ctx.send("Set not found"); return
        lines = [f"**{rs.name}** ({rs.mode})", f"Status: {rs.status}", f"Master: {rs.master_node.name if rs.master_node else 'None'}"]
        for n in rs.nodes:
            lines.append(f"  • {n.name} ({n.role}) @ {n.host} - {n.status} - Lag: {n.lag_seconds:.1f}s - QPS: {n.queries_per_sec}")
        await ctx.send("\n".join(lines))
    @repl_group.command(name="failover")
    async def manual_failover(self, ctx, set_id: str, target_node_id: str):
        rs = self.sets.get(set_id)
        if not rs: await ctx.send("Set not found"); return
        target = next((n for n in rs.nodes if n.node_id == target_node_id), None)
        if not target: await ctx.send("Target node not found"); return
        old_master = rs.master_node; old_master.role = "replica"
        target.role = "master"; rs.master_node = target
        await ctx.send(f"? Failover complete: {old_master.name} ? {target.name}")
    @repl_group.command(name="add-node")
    async def add_replica(self, ctx, set_id: str, name: str, host: str):
        rs = self.sets.get(set_id)
        if not rs: await ctx.send("Set not found"); return
        node = DatabaseNode(node_id=f"db-{random.randint(10000, 99999)}", name=name, host=host, role="replica")
        rs.nodes.append(node); await ctx.send(f"? Added replica '{name}' at {host}")
    @repl_group.command(name="health")
    async def replication_health(self, ctx):
        total = len(self.sets); healthy = sum(1 for rs in self.sets.values() if rs.status == "healthy")
        await ctx.send(f"**Replication Health:** {healthy}/{total} healthy | Latency OK")
