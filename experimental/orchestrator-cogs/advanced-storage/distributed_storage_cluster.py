"""Distributed Storage Cluster cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List, Optional
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
CLUSTER_MODES = ["minio", "ceph", "glusterfs", "rook_ceph", "longhorn", "mayastor"]
REPLICATION_FACTORS = [1, 2, 3, 5]
class Node:
    def __init__(self, node_id: str, name: str, host: str, port: int, role: str = "storage", storage_gb: int = 1024):
        self.node_id = node_id; self.name = name; self.host = host; self.port = port; self.role = role
        self.storage_gb = storage_gb; self.used_gb = 0; self.status = "online"; self.cpu_percent = 0.0
        self.ram_percent = 0.0; self.io_iops = 0; self.network_mbps = 0; self.uptime = "0d 0h"
        self.last_heartbeat = datetime.datetime.utcnow().isoformat(); self.latency_ms = 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "name": self.name, "host": self.host, "port": self.port, "role": self.role, "storage_gb": self.storage_gb, "used_gb": self.used_gb, "status": self.status, "cpu_percent": round(self.cpu_percent, 1), "ram_percent": round(self.ram_percent, 1), "io_iops": self.io_iops, "network_mbps": self.network_mbps, "uptime": self.uptime, "last_heartbeat": self.last_heartbeat, "latency_ms": self.latency_ms, "usage_percent": round(self.used_gb / max(self.storage_gb, 1) * 100, 1)}

class Cluster:
    def __init__(self, cluster_id: str, name: str, mode: str, nodes: Optional[List[Node]] = None):
        self.cluster_id = cluster_id; self.name = name; self.mode = mode; self.nodes = nodes or []
        self.status = "active"; self.healthy = True; self.total_storage_gb = 0; self.total_used_gb = 0
        self.created_at = datetime.datetime.utcnow().isoformat(); self.replication_factor = 3
    def to_dict(self) -> Dict[str, Any]:
        self.total_storage_gb = sum(n.storage_gb for n in self.nodes); self.total_used_gb = sum(n.used_gb for n in self.nodes)
        return {"cluster_id": self.cluster_id, "name": self.name, "mode": self.mode, "status": self.status, "healthy": self.healthy, "node_count": len(self.nodes), "online_nodes": sum(1 for n in self.nodes if n.status == "online"), "total_storage_gb": self.total_storage_gb, "total_used_gb": self.total_used_gb, "usage_percent": round(self.total_used_gb / max(self.total_storage_gb, 1) * 100, 1), "replication_factor": self.replication_factor, "created_at": self.created_at, "nodes": [n.to_dict() for n in self.nodes]}

class DistributedStorageCluster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.clusters: Dict[str, Cluster] = {}
        self.health_check_loop.start()
    def cog_unload(self): self.health_check_loop.cancel()
    @tasks.loop(seconds=60)
    async def health_check_loop(self):
        for cid, cluster in list(self.clusters.items()):
            for node in cluster.nodes:
                node.cpu_percent = random.uniform(10, 80)
                node.ram_percent = random.uniform(20, 70)
                node.io_iops = random.randint(100, 5000)
                node.network_mbps = random.uniform(100, 10000)
                node.latency_ms = random.uniform(0.5, 5.0)
                node.last_heartbeat = datetime.datetime.utcnow().isoformat()
                if random.random() < 0.02: node.status = "offline"
                else: node.status = "online"
            cluster.healthy = all(n.status == "online" for n in cluster.nodes)
            cluster.status = "healthy" if cluster.healthy else "degraded"
            logger.debug(f"Health check for cluster {cid}: {cluster.status}")
    @commands.group(name="cluster")
    async def cluster_group(self, ctx): pass
    @cluster_group.command(name="create")
    async def create_cluster(self, ctx, name: str, mode: str = "minio", node_count: int = 3):
        cid = f"cl-{random.randint(10000, 99999)}"
        cluster = Cluster(cluster_id=cid, name=name, mode=mode)
        for i in range(node_count):
            cluster.nodes.append(Node(node_id=f"node-{cid}-{i}", name=f"{name}-node-{i}", host=f"10.0.{i}.{random.randint(1, 254)}", port=9000, storage_gb=random.choice([1024, 2048, 4096, 8192])))
        self.clusters[cid] = cluster
        await ctx.send(f"? Created cluster '{name}' ({mode}) with {node_count} nodes (ID: {cid})")
    @cluster_group.command(name="list")
    async def list_clusters(self, ctx):
        if not self.clusters: await ctx.send("No clusters configured"); return
        lines = ["**Storage Clusters:**"]
        for cid, c in self.clusters.items(): lines.append(f"• {c.name} ({c.mode}) - {len(c.nodes)} nodes - {c.status} - {c.total_used_gb}/{c.total_storage_gb}GB")
        await ctx.send("\n".join(lines))
    @cluster_group.command(name="status")
    async def cluster_status(self, ctx, cluster_id: str):
        c = self.clusters.get(cluster_id)
        if not c: await ctx.send(f"Cluster '{cluster_id}' not found"); return
        lines = [f"**{c.name}** ({c.mode})", f"Status: {c.status} | Healthy: {c.healthy}", f"Nodes: {len(c.nodes)} | Storage: {c.total_used_gb}/{c.total_storage_gb}GB ({c.to_dict()['usage_percent']}%)"]
        for n in c.nodes: lines.append(f"  • {n.name} @ {n.host}:{n.port} - {n.status} - CPU:{n.cpu_percent:.0f}% RAM:{n.ram_percent:.0f}%")
        await ctx.send("\n".join(lines))
    @cluster_group.command(name="add-node")
    async def add_node(self, ctx, cluster_id: str, name: str, host: str, storage_gb: int = 1024):
        c = self.clusters.get(cluster_id)
        if not c: await ctx.send("Cluster not found"); return
        node = Node(node_id=f"node-{random.randint(10000, 99999)}", name=name, host=host, port=9000, storage_gb=storage_gb)
        c.nodes.append(node); await ctx.send(f"? Added node '{name}' to cluster '{c.name}'")
    @cluster_group.command(name="remove-node")
    async def remove_node(self, ctx, cluster_id: str, node_id: str):
        c = self.clusters.get(cluster_id)
        if not c: await ctx.send("Cluster not found"); return
        c.nodes = [n for n in c.nodes if n.node_id != node_id]; await ctx.send(f"? Removed node '{node_id}'")
    @cluster_group.command(name="delete")
    async def delete_cluster(self, ctx, cluster_id: str):
        if cluster_id in self.clusters: del self.clusters[cluster_id]; await ctx.send(f"? Deleted cluster '{cluster_id}'")
        else: await ctx.send("Cluster not found")
    @commands.command(name="cluster-health")
    async def cluster_health(self, ctx):
        total = len(self.clusters); healthy = sum(1 for c in self.clusters.values() if c.healthy)
        await ctx.send(f"**Cluster Health:** {healthy}/{total} healthy | {total - healthy} degraded")
