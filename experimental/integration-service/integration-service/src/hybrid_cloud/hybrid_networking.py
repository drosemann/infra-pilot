import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TunnelType(Enum):
    VPN = "vpn"
    GRE = "gre"
    VXLAN = "vxlan"
    WIREGUARD = "wireguard"
    IPSEC = "ipsec"


class MeshNodeType(Enum):
    ON_PREM = "on_prem"
    CLOUD_VPC = "cloud_vpc"
    EDGE = "edge"
    REMOTE_SITE = "remote_site"


class RouteProtocol(Enum):
    STATIC = "static"
    BGP = "bgp"
    OSPF = "ospf"


class MeshPeer:
    def __init__(self, peer_id: str, name: str, node_type: MeshNodeType,
                 endpoint: str, public_key: str, subnet: str,
                 tunnel_type: TunnelType = TunnelType.WIREGUARD):
        self.peer_id = peer_id
        self.name = name
        self.node_type = node_type
        self.endpoint = endpoint
        self.public_key = public_key
        self.subnet = subnet
        self.tunnel_type = tunnel_type
        self.connected = False
        self.latency_ms = 0
        self.bandwidth_mbps = 0
        self.last_seen = None
        self.registered_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"peer_id": self.peer_id, "name": self.name,
                "node_type": self.node_type.value, "endpoint": self.endpoint,
                "public_key": self.public_key, "subnet": self.subnet,
                "tunnel_type": self.tunnel_type.value, "connected": self.connected,
                "latency_ms": self.latency_ms, "bandwidth_mbps": self.bandwidth_mbps,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "registered_at": self.registered_at.isoformat()}


class BGPRoute:
    def __init__(self, prefix: str, next_hop: str, as_path: List[int],
                 local_pref: int = 100, med: int = 0,
                 communities: Optional[List[str]] = None):
        self.id = str(uuid.uuid4())
        self.prefix = prefix
        self.next_hop = next_hop
        self.as_path = as_path
        self.local_pref = local_pref
        self.med = med
        self.communities = communities or []
        self.learned_at = datetime.utcnow()
        self.withdrawn = False

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "prefix": self.prefix, "next_hop": self.next_hop,
                "as_path": self.as_path, "local_pref": self.local_pref,
                "med": self.med, "communities": self.communities,
                "learned_at": self.learned_at.isoformat(), "withdrawn": self.withdrawn}


class HybridNetworkingMesh:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mesh_name = config.get("mesh_name", "infrapilot-mesh")
        self.default_tunnel = TunnelType(config.get("default_tunnel", "wireguard"))
        self.bgp_asn = config.get("bgp_asn", 64512)
        self.bgp_router_id = config.get("bgp_router_id", "10.0.0.1")
        self.latency_based_routing = config.get("latency_based_routing", True)
        self.bandwidth_aggregation = config.get("bandwidth_aggregation", True)
        self.mtu = config.get("mtu", 1420)
        self._peers: Dict[str, MeshPeer] = {}
        self._routes: Dict[str, BGPRoute] = {}
        self._tunnels: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"HybridNetworkingMesh '{self.mesh_name}' initialized")

    async def close(self) -> None:
        self._peers.clear()
        self._routes.clear()
        self._tunnels.clear()
        logger.info("HybridNetworkingMesh closed")

    def register_peer(self, name: str, node_type: MeshNodeType,
                      endpoint: str, public_key: str, subnet: str,
                      tunnel_type: Optional[TunnelType] = None) -> MeshPeer:
        peer_id = f"peer-{uuid.uuid4().hex[:10]}"
        tt = tunnel_type or self.default_tunnel
        peer = MeshPeer(peer_id, name, node_type, endpoint, public_key, subnet, tt)
        self._peers[peer_id] = peer
        logger.info(f"Peer {name} ({node_type.value}) registered: {peer_id}")
        return peer

    def get_peer(self, peer_id: str) -> Optional[MeshPeer]:
        return self._peers.get(peer_id)

    def list_peers(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if node_type:
            return [p.to_dict() for p in self._peers.values() if p.node_type.value == node_type]
        return [p.to_dict() for p in self._peers.values()]

    def remove_peer(self, peer_id: str) -> bool:
        if peer_id in self._peers:
            del self._peers[peer_id]
            return True
        return False

    def update_peer_status(self, peer_id: str, connected: bool,
                           latency_ms: float = 0,
                           bandwidth_mbps: float = 0) -> bool:
        peer = self._peers.get(peer_id)
        if not peer:
            return False
        peer.connected = connected
        peer.latency_ms = latency_ms
        peer.bandwidth_mbps = bandwidth_mbps
        if connected:
            peer.last_seen = datetime.utcnow()
        return True

    async def create_tunnel(self, peer_id: str) -> Dict[str, Any]:
        peer = self._peers.get(peer_id)
        if not peer:
            return {"status": "error", "message": "Peer not found"}
        tunnel_id = f"tun-{uuid.uuid4().hex[:10]}"
        tunnel = {
            "tunnel_id": tunnel_id, "peer_id": peer_id,
            "peer_name": peer.name, "type": peer.tunnel_type.value,
            "endpoint": peer.endpoint, "subnet": peer.subnet,
            "mtu": self.mtu, "status": "established",
            "created_at": datetime.utcnow().isoformat()
        }
        self._tunnels[tunnel_id] = tunnel
        peer.connected = True
        peer.last_seen = datetime.utcnow()
        logger.info(f"Tunnel {tunnel_id} created to {peer.name}")
        return tunnel

    def get_tunnel(self, tunnel_id: str) -> Optional[Dict[str, Any]]:
        return self._tunnels.get(tunnel_id)

    def list_tunnels(self) -> List[Dict[str, Any]]:
        return list(self._tunnels.values())

    def remove_tunnel(self, tunnel_id: str) -> bool:
        tunnel = self._tunnels.get(tunnel_id)
        if tunnel:
            peer = self._peers.get(tunnel["peer_id"])
            if peer:
                peer.connected = False
            del self._tunnels[tunnel_id]
            return True
        return False

    def add_bgp_route(self, prefix: str, next_hop: str, as_path: Optional[List[int]] = None,
                      local_pref: int = 100, med: int = 0) -> BGPRoute:
        route = BGPRoute(prefix, next_hop, as_path or [self.bgp_asn], local_pref, med)
        self._routes[route.id] = route
        return route

    def withdraw_route(self, route_id: str) -> bool:
        route = self._routes.get(route_id)
        if not route:
            return False
        route.withdrawn = True
        return True

    def list_routes(self, withdrawn: Optional[bool] = None) -> List[Dict[str, Any]]:
        if withdrawn is not None:
            return [r.to_dict() for r in self._routes.values() if r.withdrawn == withdrawn]
        return [r.to_dict() for r in self._routes.values()]

    def get_mesh_topology(self) -> Dict[str, Any]:
        return {
            "mesh_name": self.mesh_name,
            "total_peers": len(self._peers),
            "connected_peers": sum(1 for p in self._peers.values() if p.connected),
            "active_tunnels": len(self._tunnels),
            "bgp_routes": len(self._routes),
            "peers_by_type": {"on_prem": sum(1 for p in self._peers.values() if p.node_type == MeshNodeType.ON_PREM),
                              "cloud_vpc": sum(1 for p in self._peers.values() if p.node_type == MeshNodeType.CLOUD_VPC),
                              "edge": sum(1 for p in self._peers.values() if p.node_type == MeshNodeType.EDGE)},
            "default_tunnel": self.default_tunnel.value,
            "bgp_asn": self.bgp_asn
        }

    def get_statistics(self) -> Dict[str, Any]:
        total_latency = sum(p.latency_ms for p in self._peers.values() if p.connected)
        connected = [p for p in self._peers.values() if p.connected]
        avg_latency = total_latency / len(connected) if connected else 0
        total_bw = sum(p.bandwidth_mbps for p in self._peers.values() if p.connected)
        return {"total_peers": len(self._peers), "connected_peers": len(connected),
                "active_tunnels": len(self._tunnels), "bgp_routes": len(self._routes),
                "avg_latency_ms": round(avg_latency, 2),
                "total_bandwidth_mbps": round(total_bw, 2)}

    def add_peer(self, name: str, endpoint: str, node_type: MeshNodeType,
                  region: str = "auto", bandwidth_mbps: int = 1000) -> MeshPeer:
        peer = MeshPeer(name, endpoint, node_type, region, bandwidth_mbps)
        self._peers[peer.id] = peer
        return peer

    def remove_peer(self, peer_id: str) -> bool:
        if peer_id in self._peers:
            self._peers[peer_id].connected = False
            del self._peers[peer_id]
            return True
        return False

    def get_peer(self, peer_id: str) -> Optional[Dict[str, Any]]:
        peer = self._peers.get(peer_id)
        return peer.to_dict() if peer else None

    def create_tunnel(self, name: str, peer_id: str, tunnel_type: TunnelType,
                       local_cidr: str, remote_cidr: str) -> Dict[str, Any]:
        tunnel_id = f"tunnel-{uuid.uuid4().hex[:8]}"
        tunnel = {"id": tunnel_id, "name": name, "peer_id": peer_id,
                  "type": tunnel_type.value, "local_cidr": local_cidr,
                  "remote_cidr": remote_cidr, "status": "active",
                  "created_at": datetime.utcnow().isoformat(),
                  "bandwidth_used_mbps": 0}
        if peer_id in self._peers:
            self._peers[peer_id].connected = True
        self._tunnels[tunnel_id] = tunnel
        return tunnel

    def update_tunnel_bandwidth(self, tunnel_id: str, bandwidth: float) -> bool:
        tunnel = self._tunnels.get(tunnel_id)
        if not tunnel:
            return False
        tunnel["bandwidth_used_mbps"] = bandwidth
        return True

    def find_route_by_prefix(self, prefix: str) -> Optional[Dict[str, Any]]:
        for r in self._routes.values():
            if r.prefix == prefix and not r.withdrawn:
                return r.to_dict()
        return None

    def calculate_path_cost(self, source: str, destination: str) -> Dict[str, Any]:
        hops = random.randint(2, 6)
        latency = random.uniform(5, 100)
        return {"source": source, "destination": destination,
                "hops": hops, "estimated_latency_ms": round(latency, 1),
                "path_cost": hops * 10 + latency}

    def get_routing_table(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._routes.values() if not r.withdrawn]

    def update_peer_latency(self, peer_id: str, latency_ms: float) -> bool:
        peer = self._peers.get(peer_id)
        if not peer:
            return False
        peer.latency_ms = latency_ms
        return True

    def list_peers(self, node_type: Optional[MeshNodeType] = None) -> List[Dict[str, Any]]:
        if node_type:
            return [p.to_dict() for p in self._peers.values() if p.node_type == node_type]
        return [p.to_dict() for p in self._peers.values()]

    def list_tunnels(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            return [t for t in self._tunnels.values() if t.get("status") == status]
        return list(self._tunnels.values())

    def diagnose_connectivity(self, peer_id: str) -> Dict[str, Any]:
        peer = self._peers.get(peer_id)
        if not peer:
            return {"status": "error", "message": "Peer not found"}
        issues = []
        if not peer.connected:
            issues.append("Not connected")
        if peer.latency_ms > 100:
            issues.append(f"High latency: {peer.latency_ms}ms")
        return {"peer_id": peer_id, "peer_name": peer.name,
                "connected": peer.connected, "latency_ms": peer.latency_ms,
                "issues": issues, "healthy": len(issues) == 0}

    def export_topology(self) -> Dict[str, Any]:
        return {"mesh_name": self.mesh_name,
                "peers": [p.to_dict() for p in self._peers.values()],
                "tunnels": list(self._tunnels.values()),
                "routes": [r.to_dict() for r in self._routes.values()],
                "exported_at": datetime.utcnow().isoformat()}

    def calculate_latency_matrix(self) -> Dict[str, Any]:
        matrix = {}
        for p1 in self._peers.values():
            if p1.connected:
                row = {}
                for p2 in self._peers.values():
                    if p2.connected and p1.peer_id != p2.peer_id:
                        simulated_latency = abs(hash(p1.peer_id + p2.peer_id) % 50) + 1
                        row[p2.name] = simulated_latency
                if row:
                    matrix[p1.name] = row
        return {"mesh_name": self.mesh_name, "latency_matrix": matrix}

    def configure_bgp(self, asn: int, router_id: str) -> None:
        self.bgp_asn = asn
        self.bgp_router_id = router_id

    def set_mtu(self, mtu: int) -> None:
        self.mtu = max(1280, min(9000, mtu))

    def get_connected_peers(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._peers.values() if p.connected]

    def find_peer_by_subnet(self, subnet: str) -> Optional[Dict[str, Any]]:
        for p in self._peers.values():
            if p.subnet == subnet:
                return p.to_dict()
        return None

    def batch_register_peers(self, peers: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for pdata in peers:
            peer = self.register_peer(pdata.get("name", "unknown"),
                                        MeshNodeType(pdata.get("node_type", "on_prem")),
                                        pdata.get("endpoint", ""), pdata.get("public_key", ""),
                                        pdata.get("subnet", ""))
            ids.append(peer.peer_id)
        return ids

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class NetworkSegment:
    segment_id: str
    cidr: str
    region: str
    provider: str
    vpc_id: str = ""
    subnet_ids: List[str] = field(default_factory=list)

@dataclass
class TrafficFlowRule:
    rule_id: str
    source_cidr: str
    dest_cidr: str
    protocol: str = "tcp"
    port_range: str = "1-65535"
    priority: int = 100
    action: str = "allow"

@dataclass
class LatencyProbeResult:
    source_peer: str
    dest_peer: str
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    probed_at: datetime = field(default_factory=datetime.utcnow)

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_create_tunnels(self, peer_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for pid in peer_ids:
            r = await self.create_tunnel(pid)
            results[pid] = r
        return {"results": results, "total": len(peer_ids)}

    async def batch_remove_peers(self, peer_ids: List[str]) -> Dict[str, Any]:
        removed = 0; not_found = 0
        for pid in peer_ids:
            if self.remove_peer(pid):
                removed += 1
            else:
                not_found += 1
        return {"removed": removed, "not_found": not_found}

    async def batch_withdraw_routes(self, route_ids: List[str]) -> Dict[str, Any]:
        withdrawn = 0; not_found = 0
        for rid in route_ids:
            if self.withdraw_route(rid):
                withdrawn += 1
            else:
                not_found += 1
        return {"withdrawn": withdrawn, "not_found": not_found}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_peers(self, page: int = 1, page_size: int = 20,
                        sort_by: str = "registered_at", sort_desc: bool = True,
                        node_type_filter: Optional[str] = None,
                        connected_filter: Optional[bool] = None) -> Dict[str, Any]:
        items = list(self._peers.values())
        if node_type_filter:
            items = [p for p in items if p.node_type.value == node_type_filter]
        if connected_filter is not None:
            items = [p for p in items if p.connected == connected_filter]
        items.sort(key=lambda p: getattr(p, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [p.to_dict() for p in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_routes(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = [r.to_dict() for r in self._routes.values() if not r.withdrawn]
        items.sort(key=lambda r: r.get("learned_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_network_state(self) -> str:
        return json.dumps({
            "mesh_name": self.mesh_name,
            "peers": [p.to_dict() for p in self._peers.values()],
            "tunnels": list(self._tunnels.values()),
            "routes": [r.to_dict() for r in self._routes.values()],
            "exported_at": datetime.utcnow().isoformat(),
        }, indent=2)

    def import_peers_from_json(self, json_str: str) -> int:
        data = json.loads(json_str)
        count = 0
        for entry in data.get("peers", []):
            try:
                self.register_peer(entry["name"], MeshNodeType(entry["node_type"]),
                                    entry["endpoint"], entry["public_key"], entry["subnet"])
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_network_utilization_analysis(self) -> Dict[str, Any]:
        connected = [p for p in self._peers.values() if p.connected]
        total_bw = sum(p.bandwidth_mbps for p in connected)
        avg_lat = sum(p.latency_ms for p in connected) / max(len(connected), 1)
        return {
            "total_peers": len(self._peers), "connected_peers": len(connected),
            "total_bandwidth_mbps": round(total_bw, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "bandwidth_utilization_pct": round(
                sum(p.bandwidth_mbps for p in connected) / max(len(connected) * 1000, 1) * 100, 1),
        }

    def get_path_redundancy_analysis(self) -> Dict[str, Any]:
        peer_connections: Dict[str, int] = {}
        for tunnel in self._tunnels.values():
            pid = tunnel.get("peer_id", "")
            peer_connections[pid] = peer_connections.get(pid, 0) + 1
        redundant = sum(1 for c in peer_connections.values() if c > 1)
        single = sum(1 for c in peer_connections.values() if c == 1)
        return {"peers_with_redundancy": redundant, "peers_single_path": single,
                "redundancy_ratio": round(redundant / max(len(peer_connections), 1), 2)}

    def get_traffic_flow_heatmap(self) -> Dict[str, Any]:
        flow: Dict[str, int] = {}
        for tunnel in self._tunnels.values():
            bw = tunnel.get("bandwidth_used_mbps", 0)
            pid = tunnel.get("peer_id", "unknown")
            peer = self._peers.get(pid)
            node = peer.node_type.value if peer else "unknown"
            flow[node] = flow.get(node, 0) + bw
        return {"traffic_by_node_type": flow, "total_bandwidth": sum(flow.values())}

# ── State Machine / Workflow ─────────────────────────────────────────

    async def network_lifecycle_workflow(self, peer_id: str, action: str) -> Dict[str, Any]:
        peer = self._peers.get(peer_id)
        if not peer:
            return {"status": "error", "message": "Peer not found"}
        if action == "connect":
            return await self.create_tunnel(peer_id)
        elif action == "disconnect":
            for tid, tunnel in list(self._tunnels.items()):
                if tunnel.get("peer_id") == peer_id:
                    self.remove_tunnel(tid)
            peer.connected = False
            return {"status": "disconnected", "peer_id": peer_id}
        elif action == "diagnose":
            return self.diagnose_connectivity(peer_id)
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_health_check_workflow(self) -> Dict[str, Any]:
        checked = 0; issues = 0
        for peer in self._peers.values():
            diag = self.diagnose_connectivity(peer.peer_id)
            if not diag.get("healthy", False):
                issues += 1
            checked += 1
        return {"peers_checked": checked, "peers_with_issues": issues}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_network_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.mtu < 1280 or self.mtu > 9000:
            errors.append("MTU must be between 1280 and 9000")
        if self.bgp_asn < 64512 or self.bgp_asn > 65534:
            warnings.append(f"ASN {self.bgp_asn} is in the private range, verify peering")
        if not self._peers:
            warnings.append("No peers registered")
        if self.latency_based_routing and not self._routes:
            warnings.append("latency_based_routing enabled but no routes configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# ── Batch Operations ───────────────────────────────────────────────────

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"results": results, "total": len(results),
                "successful": sum(1 for r in results if r["status"] == "processed")}

    async def batch_validate(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid = invalid = 0
        errors = []
        for item in items:
            if item.get("id"):
                valid += 1
            else:
                invalid += 1
                errors.append({"item": item, "reason": "missing id"})
        return {"valid": valid, "invalid": invalid, "errors": errors}

# ── Analytics / Aggregation ───────────────────────────────────────────

    def get_summary_stats(self) -> Dict[str, Any]:
        return {"total_items": 0, "active_items": 0, "inactive_items": 0}

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        return {"period_days": days, "data_points": 0, "trend": "stable"}

# ── Data Models ───────────────────────────────────────────────────────

class OperationResult(BaseModel):
    success: bool = True
    operation: str = "unknown"
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")

    def add_operation(self, op: Dict[str, Any]) -> None:
        self.operations.append(op)

    def complete(self) -> None:
        self.status = "completed"

class HealthStatus(BaseModel):
    component: str
    status: str = Field(default="healthy")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    error_count: int = Field(default=0)
    response_time_ms: float = Field(default=0.0)

class StatusDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthStatus] = {}

    def register(self, component: str) -> HealthStatus:
        hs = HealthStatus(component=component)
        self._components[component] = hs
        return hs

    def heartbeat(self, component: str, response_time_ms: float = 0.0) -> None:
        if component in self._components:
            self._components[component].last_heartbeat = datetime.utcnow()
            self._components[component].response_time_ms = response_time_ms
            self._components[component].status = "healthy"

    def record_error(self, component: str) -> None:
        if component in self._components:
            self._components[component].error_count += 1
            if self._components[component].error_count > 5:
                self._components[component].status = "degraded"

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        return {"total_components": total, "healthy": healthy, "degraded": degraded,
                "uptime_pct": round(healthy / max(total, 1) * 100, 1)}

    def get_component_status(self, component: str) -> Optional[HealthStatus]:
        return self._components.get(component)

class AuditLogger:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, action: str, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({
            "action": action, "resource_type": resource_type, "resource_id": resource_id,
            "details": details or {}, "timestamp": datetime.utcnow().isoformat(),
        })

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def get_by_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["resource_id"] == resource_id]

    def get_by_action(self, action: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["action"] == action]

    def count_by_action(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = []
        self._metrics[metric].append(value)

    def get_stats(self, metric: str) -> Dict[str, Any]:
        values = self._metrics.get(metric, [])
        if not values:
            return {"metric": metric, "count": 0}
        return {"metric": metric, "count": len(values), "min": round(min(values), 4),
                "max": round(max(values), 4), "avg": round(sum(values) / len(values), 4),
                "latest": round(values[-1], 4)}

    def get_all_stats(self) -> Dict[str, Any]:
        return {m: self.get_stats(m) for m in self._metrics}

    def reset(self, metric: Optional[str] = None) -> None:
        if metric:
            self._metrics[metric] = []
        else:
            self._metrics.clear()

class ConfigValidator:
    @staticmethod
    def validate(config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        for key, rules in schema.items():
            value = config.get(key)
            if rules.get("required", False) and value is None:
                errors.append(f"Missing required key: {key}")
            if value is not None and "type" in rules:
                if not isinstance(value, rules["type"]):
                    errors.append(f"Key {key} expected type {rules['type'].__name__}")
            if value is not None and "min" in rules and isinstance(value, (int, float)):
                if value < rules["min"]:
                    errors.append(f"Key {key} below minimum {rules['min']}")
            if value is not None and "max" in rules and isinstance(value, (int, float)):
                if value > rules["max"]:
                    errors.append(f"Key {key} above maximum {rules['max']}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def merge_with_defaults(config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(defaults)
        merged.update(config)
        return merged
