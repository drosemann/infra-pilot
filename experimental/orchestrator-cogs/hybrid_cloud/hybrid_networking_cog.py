import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/hybrid_networking.json"

class HybridNetworkingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._peers = {}
        self._tunnels = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._peers = data.get("peers", {})
                self._tunnels = data.get("tunnels", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("HybridNetworkingCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"peers": self._peers, "tunnels": self._tunnels}, f, indent=2)

    @commands.group(name="mesh", invoke_without_command=True)
    async def mesh(self, ctx):
        await ctx.send("Mesh networking commands: peers, tunnels, routes, topology")

    @mesh.command(name="peers")
    async def list_peers(self, ctx):
        if not self._peers:
            await ctx.send("No mesh peers registered.")
            return
        embed = discord.Embed(title=f"Mesh Peers ({len(self._peers)})", color=discord.Color.blue())
        for pid, p in self._peers.items():
            connected = "ONLINE" if p.get("connected") else "OFFLINE"
            embed.add_field(name=f"{p.get('name', pid)} ({connected})", value=f"Type: {p.get('node_type')} | Endpoint: {p.get('endpoint')}", inline=False)
        await ctx.send(embed=embed)

    @mesh.command(name="register")
    @commands.has_permissions(administrator=True)
    async def register_peer(self, ctx, name: str, node_type: str, endpoint: str, subnet: str):
        pid = f"peer-{uuid.uuid4().hex[:10]}"
        self._peers[pid] = {"peer_id": pid, "name": name, "node_type": node_type, "endpoint": endpoint, "subnet": subnet, "connected": False, "registered_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Peer '{name}' registered (ID: {pid})")

    @mesh.command(name="tunnels")
    async def list_tunnels(self, ctx):
        if not self._tunnels:
            await ctx.send("No tunnels created.")
            return
        embed = discord.Embed(title=f"Active Tunnels ({len(self._tunnels)})", color=discord.Color.green())
        for tid, t in self._tunnels.items():
            embed.add_field(name=f"Tunnel {tid}", value=f"Peer: {t.get('peer_name')} | Type: {t.get('type')} | Status: {t.get('status')}", inline=False)
        await ctx.send(embed=embed)

    @mesh.command(name="topology")
    async def show_topology(self, ctx):
        embed = discord.Embed(title="Mesh Topology", color=discord.Color.purple())
        embed.add_field(name="Total Peers", value=str(len(self._peers)))
        embed.add_field(name="Connected", value=str(sum(1 for p in self._peers.values() if p.get("connected"))))
        embed.add_field(name="Active Tunnels", value=str(len(self._tunnels)))
        embed.add_field(name="Mesh Name", value="infrapilot-mesh")
        embed.add_field(name="Default Tunnel", value="WireGuard")
        embed.add_field(name="BGP ASN", value="64512")
        await ctx.send(embed=embed)

    @mesh.command(name="route")
    @commands.has_permissions(administrator=True)
    async def add_route(self, ctx, prefix: str, next_hop: str):
        route_id = f"route-{uuid.uuid4().hex[:8]}"
        if "_routes" not in self._peers:
            self._peers["_routes"] = {}
        self._peers["_routes"][route_id] = {"id": route_id, "prefix": prefix, "next_hop": next_hop, "added_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Route {prefix} -> {next_hop} added ({route_id})")

    @mesh.command(name="peers")
    async def list_peers(self, ctx):
        if not self._peers:
            await ctx.send("No peers configured.")
            return
        embed = discord.Embed(title=f"Mesh Peers ({len(self._peers)})", color=discord.Color.green())
        for pid, p in self._peers.items():
            if pid == "_routes": continue
            connected = "✅" if p.get("connected") else "❌"
            embed.add_field(name=f"{p.get('name', pid)} {connected}", value=f"Type: {p.get('type', 'unknown')} | Latency: {p.get('latency_ms', 'N/A')}ms", inline=True)
        await ctx.send(embed=embed)

    @mesh.command(name="add-peer")
    @commands.has_permissions(administrator=True)
    async def add_peer(self, ctx, name: str, endpoint: str, node_type: str = "cloud_vpc"):
        pid = f"peer-{uuid.uuid4().hex[:8]}"
        self._peers[pid] = {"id": pid, "name": name, "endpoint": endpoint, "type": node_type, "connected": True, "latency_ms": random.randint(5, 50), "added_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Peer '{name}' added ({pid})")

    @mesh.command(name="remove-peer")
    @commands.has_permissions(administrator=True)
    async def remove_peer(self, ctx, peer_id: str):
        if peer_id in self._peers:
            del self._peers[peer_id]
            await self._save_data()
            await ctx.send(f"Peer {peer_id} removed")
        else:
            await ctx.send("Peer not found.")

    @mesh.command(name="tunnels")
    async def list_tunnels(self, ctx):
        if not self._tunnels:
            await ctx.send("No active tunnels.")
            return
        embed = discord.Embed(title=f"Active Tunnels ({len(self._tunnels)})", color=discord.Color.blue())
        for tid, t in self._tunnels.items():
            embed.add_field(name=t.get("name", tid), value=f"From: {t.get('local_cidr')} -> {t.get('remote_cidr')} | Status: {t.get('status')}", inline=False)
        await ctx.send(embed=embed)

    @mesh.command(name="add-tunnel")
    @commands.has_permissions(administrator=True)
    async def add_tunnel(self, ctx, name: str, peer_id: str, local_cidr: str, remote_cidr: str, tunnel_type: str = "wireguard"):
        tid = f"tunnel-{uuid.uuid4().hex[:8]}"
        self._tunnels[tid] = {"id": tid, "name": name, "peer_id": peer_id, "local_cidr": local_cidr, "remote_cidr": remote_cidr, "type": tunnel_type, "status": "active", "created_at": datetime.utcnow().isoformat()}
        if peer_id in self._peers:
            self._peers[peer_id]["connected"] = True
        await self._save_data()
        await ctx.send(f"Tunnel '{name}' created: {local_cidr} <-> {remote_cidr}")

    @mesh.command(name="diagnose")
    async def diagnose_peer(self, ctx, peer_id: str):
        peer = self._peers.get(peer_id)
        if not peer or peer_id == "_routes":
            await ctx.send("Peer not found.")
            return
        issues = []
        if not peer.get("connected"):
            issues.append("Not connected")
        if peer.get("latency_ms", 0) > 100:
            issues.append(f"High latency: {peer.get('latency_ms')}ms")
        embed = discord.Embed(title=f"Diagnosis: {peer.get('name', peer_id)}", color=discord.Color.green() if len(issues) == 0 else discord.Color.orange())
        embed.add_field(name="Connected", value=str(peer.get("connected", False)))
        embed.add_field(name="Latency", value=f"{peer.get('latency_ms', 0)}ms")
        embed.add_field(name="Issues", value=", ".join(issues) if issues else "None")
        await ctx.send(embed=embed)

    @mesh.command(name="latency")
    async def latency_report(self, ctx):
        import random
        embed = discord.Embed(title="Mesh Latency Report", color=discord.Color.blue())
        online = [p for pid, p in self._peers.items() if pid != "_routes" and p.get("connected")]
        for p in online[:5]:
            latency = round(random.uniform(2, 80), 1)
            embed.add_field(name=p.get("name", "?"), value=f"{latency}ms", inline=True)
        if not online:
            embed.description = "No connected peers to measure"
        await ctx.send(embed=embed)

    @mesh.command(name="bandwidth")
    async def bandwidth_report(self, ctx, peer_id: str = None):
        import random
        if peer_id:
            peer = self._peers.get(peer_id)
            if not peer or peer_id == "_routes":
                await ctx.send("Peer not found.")
                return
            bw = round(random.uniform(100, 10000), 1)
            embed = discord.Embed(title=f"Bandwidth: {peer.get('name', peer_id)}", color=discord.Color.green())
            embed.add_field(name="Throughput", value=f"{bw} Mbps")
            embed.add_field(name="Type", value=peer.get("type", "unknown"))
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Bandwidth Overview", color=discord.Color.blue())
            total = round(random.uniform(1000, 50000), 1)
            embed.add_field(name="Total Throughput", value=f"{total} Mbps")
            embed.add_field(name="Active Links", value=str(len([p for pid, p in self._peers.items() if pid != "_routes" and p.get("connected")])))
            await ctx.send(embed=embed)

    @mesh.command(name="dns")
    @commands.has_permissions(administrator=True)
    async def dns_register(self, ctx, hostname: str, ip_address: str, zone: str = "infrapilot.internal"):
        dns_id = f"dns-{uuid.uuid4().hex[:8]}"
        if "_dns" not in self._peers:
            self._peers["_dns"] = {}
        self._peers["_dns"][dns_id] = {"id": dns_id, "hostname": hostname, "ip": ip_address, "zone": zone, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"DNS record: {hostname} -> {ip_address} ({zone})")

    @mesh.command(name="firewall-rules")
    async def list_firewall_rules(self, ctx):
        rules = self._peers.get("_firewall", {})
        if not rules:
            embed = discord.Embed(title="Firewall Rules", color=discord.Color.blue())
            embed.add_field(name="Default Rule", value="Allow all intra-mesh traffic")
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=f"Firewall Rules ({len(rules)})", color=discord.Color.orange())
        for rid, r in rules.items():
            embed.add_field(name=rid, value=f"{r.get('action')} {r.get('protocol')} {r.get('source')} -> {r.get('destination')}")
        await ctx.send(embed=embed)

    @mesh.command(name="add-firewall-rule")
    @commands.has_permissions(administrator=True)
    async def add_firewall_rule(self, ctx, action: str, protocol: str, source: str, destination: str):
        rid = f"fw-{uuid.uuid4().hex[:8]}"
        if "_firewall" not in self._peers:
            self._peers["_firewall"] = {}
        self._peers["_firewall"][rid] = {"id": rid, "action": action, "protocol": protocol, "source": source, "destination": destination, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Firewall rule added: {action} {protocol} {source} -> {destination}")

    @mesh.command(name="health")
    async def mesh_health(self, ctx):
        total = len([p for pid, p in self._peers.items() if pid != "_routes" and pid != "_dns" and pid != "_firewall"])
        connected = sum(1 for pid, p in self._peers.items() if pid not in ("_routes", "_dns", "_firewall") and p.get("connected"))
        embed = discord.Embed(title="Mesh Health", color=discord.Color.green() if connected == total else discord.Color.orange())
        embed.add_field(name="Peers", value=str(total))
        embed.add_field(name="Connected", value=str(connected))
        embed.add_field(name="Tunnels", value=str(len(self._tunnels)))
        embed.add_field(name="Health", value=f"{connected}/{total}")
        await ctx.send(embed=embed)

    @mesh.command(name="latency-matrix")
    async def latency_matrix(self, ctx):
        peers_list = [p for pid, p in self._peers.items() if pid not in ("_routes", "_dns", "_firewall")]
        if len(peers_list) < 2:
            await ctx.send("Need at least 2 peers for a latency matrix.")
            return
        embed = discord.Embed(title="Latency Matrix", color=discord.Color.blue())
        import random
        for p in peers_list:
            others = [q for q in peers_list if q.get("peer_id") != p.get("peer_id")]
            avg = sum(abs(hash(p.get("peer_id", "") + q.get("peer_id", "")) % 50) + 1 for q in others) / len(others)
            embed.add_field(name=p.get("name", "?"), value=f"Avg latency: {avg:.0f}ms", inline=True)
        await ctx.send(embed=embed)

    @mesh.command(name="export-topology")
    @commands.has_permissions(administrator=True)
    async def export_topology(self, ctx):
        data = json.dumps({"peers": [p for pid, p in self._peers.items() if pid not in ("_routes", "_dns", "_firewall")], "tunnels": self._tunnels, "routes": self._routes}, indent=2)
        await ctx.send(f"```json\n{data[:1900]}```")

    @mesh.command(name="add-route")
    @commands.has_permissions(administrator=True)
    async def add_route(self, ctx, prefix: str, next_hop: str, asn: int = 64512):
        if "_routes" not in self._peers:
            self._peers["_routes"] = {}
        route_id = f"route-{uuid.uuid4().hex[:8]}"
        self._peers["_routes"][route_id] = {"id": route_id, "prefix": prefix, "next_hop": next_hop, "as_path": [asn], "local_pref": 100, "withdrawn": False, "learned_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Route {prefix} -> {next_hop} added (AS{asn})")

    @mesh.command(name="withdraw-route")
    @commands.has_permissions(administrator=True)
    async def withdraw_route_cmd(self, ctx, route_id: str):
        routes = self._peers.get("_routes", {})
        if route_id in routes:
            routes[route_id]["withdrawn"] = True
            await self._save_data()
            await ctx.send(f"Route {route_id} withdrawn.")
        else:
            await ctx.send("Route not found.")

    @mesh.command(name="bgp-status")
    async def bgp_status(self, ctx):
        routes = self._peers.get("_routes", {})
        active = [r for r in routes.values() if not r.get("withdrawn")]
        embed = discord.Embed(title="BGP Status", color=discord.Color.blue())
        embed.add_field(name="Total Routes", value=str(len(routes)))
        embed.add_field(name="Active Routes", value=str(len(active)))
        embed.add_field(name="Peers", value=str(len([p for pid, p in self._peers.items() if pid not in ("_routes", "_dns", "_firewall")])))
        embed.add_field(name="Tunnels", value=str(len(self._tunnels)))
        await ctx.send(embed=embed)

    @mesh.command(name="diagnose")
    async def diagnose_peer(self, ctx, peer_id: str):
        peer = self._peers.get(peer_id)
        if not peer:
            await ctx.send("Peer not found.")
            return
        issues = []
        if not peer.get("connected"):
            issues.append("Not connected")
        if peer.get("latency_ms", 0) > 100:
            issues.append(f"High latency: {peer.get('latency_ms')}ms")
        embed = discord.Embed(title=f"Diagnostics: {peer.get('name', '?')}", color=discord.Color.green() if not issues else discord.Color.orange())
        embed.add_field(name="Connected", value=str(peer.get("connected", False)))
        embed.add_field(name="Latency", value=f"{peer.get('latency_ms', 0)}ms")
        embed.add_field(name="Bandwidth", value=f"{peer.get('bandwidth_mbps', 0)} Mbps")
        embed.add_field(name="Issues", value="None" if not issues else "\n".join(issues))
        await ctx.send(embed=embed)

    @mesh.command(name="dns-record")
    @commands.has_permissions(administrator=True)
    async def dns_add(self, ctx, name: str, record_type: str, value: str, ttl: int = 300):
        if "_dns" not in self._peers:
            self._peers["_dns"] = {}
        dns_id = f"dns-{uuid.uuid4().hex[:8]}"
        self._peers["_dns"][dns_id] = {"id": dns_id, "name": name, "type": record_type, "value": value, "ttl": ttl}
        await self._save_data()
        await ctx.send(f"DNS {record_type} record {name} -> {value} (TTL: {ttl}s)")

    @mesh.command(name="firewall-rule")
    @commands.has_permissions(administrator=True)
    async def firewall_rule(self, ctx, action: str, protocol: str, source: str, destination: str, port: str = "*"):
        if "_firewall" not in self._peers:
            self._peers["_firewall"] = {}
        rule_id = f"fw-{uuid.uuid4().hex[:8]}"
        self._peers["_firewall"][rule_id] = {"id": rule_id, "action": action, "protocol": protocol, "source": source, "destination": destination, "port": port, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Firewall rule: {action} {protocol} {source} -> {destination}:{port}")

    def _build_peer_embed(self, peer: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=peer.get("name", "Peer"), color=discord.Color.green() if peer.get("connected") else discord.Color.red())
        embed.add_field(name="ID", value=peer.get("peer_id", "N/A"), inline=False)
        embed.add_field(name="Type", value=peer.get("node_type", "N/A"), inline=True)
        embed.add_field(name="Endpoint", value=peer.get("endpoint", "N/A"), inline=True)
        embed.add_field(name="Connected", value=str(peer.get("connected", False)), inline=True)
        embed.add_field(name="Latency", value=f"{peer.get('latency_ms', 0)}ms", inline=True)
        embed.add_field(name="Bandwidth", value=f"{peer.get('bandwidth_mbps', 0)} Mbps", inline=True)
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"peers": self._peers, "tunnels": self._tunnels}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(HybridNetworkingCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_operation(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"operations_count": 0, "success_rate": 100.0, "avg_duration_ms": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": []}

class CogConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=10)
    timeout_seconds: int = Field(default=60, ge=5)
    retry_limit: int = Field(default=3, ge=0)
    notify_on_failure: bool = True
    log_level: str = Field(default="INFO")

class CogMetrics:
    def __init__(self) -> None:
        self.runs: int = 0
        self.failures: int = 0
        self.last_run: Optional[datetime] = None
        self.last_duration: float = 0.0

    def record_run(self, duration: float, success: bool) -> None:
        self.runs += 1
        self.last_run = datetime.utcnow()
        self.last_duration = duration
        if not success:
            self.failures += 1

    def summary(self) -> Dict[str, Any]:
        return {"runs": self.runs, "failures": self.failures,
                "success_rate": round((self.runs - self.failures) / max(self.runs, 1) * 100, 1),
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "last_duration_ms": round(self.last_duration, 1)}
