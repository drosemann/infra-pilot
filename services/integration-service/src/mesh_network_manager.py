"""Mesh Network Manager - WireGuard/Tinc mesh VPN management across edge nodes."""

import asyncio
import ipaddress
import json
import logging
import os
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MeshType(Enum):
    WIREGUARD = "wireguard"
    TINC = "tinc"


class RoutingType(Enum):
    FULL_MESH = "full_mesh"
    HUB_AND_SPOKE = "hub_and_spoke"
    PARTIAL = "partial"


class PeerStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    PROVISIONING = "provisioning"


class MeshNetwork:
    """Represents a mesh VPN network."""

    def __init__(self, network_id: str, name: str, mesh_type: MeshType,
                 subnet: str):
        self.network_id = network_id
        self.name = name
        self.mesh_type = mesh_type
        self.subnet = subnet
        self.routing_type = RoutingType.FULL_MESH
        self.mtu: int = 1420
        self.port: int = 51820 if mesh_type == MeshType.WIREGUARD else 655
        self.peers: dict[str, MeshPeer] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.enabled: bool = True
        self.metadata: dict = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "network_id": self.network_id,
            "name": self.name,
            "mesh_type": self.mesh_type.value,
            "subnet": self.subnet,
            "routing_type": self.routing_type.value,
            "mtu": self.mtu,
            "port": self.port,
            "peers_count": len(self.peers),
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MeshPeer:
    """A peer in a mesh network."""

    def __init__(self, peer_id: str, node_id: str, address: str):
        self.peer_id = peer_id
        self.node_id = node_id
        self.address = address
        self.endpoint: Optional[str] = None
        self.public_key: str = ""
        self.private_key: str = ""
        self.preshared_key: Optional[str] = None
        self.allowed_ips: list[str] = []
        self.persistent_keepalive: int = 25
        self.status: PeerStatus = PeerStatus.PROVISIONING
        self.last_handshake: Optional[datetime] = None
        self.transfer_rx: int = 0
        self.transfer_tx: int = 0
        self.latency_ms: float = 0.0
        self.joined_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "node_id": self.node_id,
            "address": self.address,
            "endpoint": self.endpoint,
            "public_key": self.public_key[:20] + "...",
            "allowed_ips": self.allowed_ips,
            "persistent_keepalive": self.persistent_keepalive,
            "status": self.status.value,
            "last_handshake": self.last_handshake.isoformat() if self.last_handshake else None,
            "transfer_rx_mb": round(self.transfer_rx / (1024 * 1024), 2),
            "transfer_tx_mb": round(self.transfer_tx / (1024 * 1024), 2),
            "latency_ms": self.latency_ms,
            "joined_at": self.joined_at.isoformat(),
        }


class TopologyLink:
    """A network link between two peers for topology visualization."""

    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target
        self.latency_ms: float = 0.0
        self.bandwidth_mbps: float = 0.0
        self.packet_loss: float = 0.0
        self.status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "latency_ms": self.latency_ms,
            "bandwidth_mbps": self.bandwidth_mbps,
            "packet_loss": self.packet_loss,
            "status": self.status,
        }


class MeshNetworkManager:
    """Manager for mesh VPN networks."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.networks: dict[str, MeshNetwork] = {}
        self._seed_data()

    def _seed_data(self):
        net = self.create_network("production-edge", MeshType.WIREGUARD,
                                  "10.100.0.0/16")
        demo_peers = [
            ("node-edge-001", "10.100.0.1", "203.0.113.10:51820"),
            ("node-edge-002", "10.100.0.2", "203.0.113.20:51820"),
            ("node-edge-003", "10.100.0.3", "203.0.113.30:51820"),
            ("node-edge-004", "10.100.0.4", "203.0.113.40:51820"),
            ("node-edge-005", "10.100.0.5", "203.0.113.50:51820"),
        ]
        for node_id, addr, endpoint in demo_peers:
            peer = self.add_peer(net.network_id, node_id, addr)
            peer.endpoint = endpoint
            peer.public_key = f"WG{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=40))}"
            peer.allowed_ips = [str(ipaddress.IPv4Network(f"10.100.0.0/24", strict=False))]
            peer.status = PeerStatus.ONLINE
            peer.last_handshake = datetime.utcnow() - timedelta(seconds=random.randint(10, 300))
            peer.transfer_rx = random.randint(10**7, 10**9)
            peer.transfer_tx = random.randint(10**7, 10**9)
            peer.latency_ms = round(random.uniform(1, 50), 1)

        net2 = self.create_network("iot-sensors", MeshType.TINC, "10.200.0.0/16")
        net2.routing_type = RoutingType.HUB_AND_SPOKE

    async def initialize(self):
        logger.info("MeshNetworkManager initialized with %d networks", len(self.networks))

    async def close(self):
        logger.info("MeshNetworkManager closed")

    def _generate_keypair(self) -> tuple[str, str]:
        import secrets
        private = secrets.token_hex(32)
        public = secrets.token_hex(32)
        return private, public

    def create_network(self, name: str, mesh_type: MeshType,
                       subnet: str) -> MeshNetwork:
        network_id = f"net-{uuid.uuid4().hex[:8]}"
        net = MeshNetwork(network_id, name, mesh_type, subnet)
        self.networks[network_id] = net
        logger.info("Created mesh network: %s (%s)", name, subnet)
        return net

    def get_network(self, network_id: str) -> Optional[MeshNetwork]:
        return self.networks.get(network_id)

    def list_networks(self) -> list[MeshNetwork]:
        return list(self.networks.values())

    def delete_network(self, network_id: str) -> bool:
        if network_id in self.networks:
            del self.networks[network_id]
            return True
        return False

    def add_peer(self, network_id: str, node_id: str,
                 address: str) -> Optional[MeshPeer]:
        net = self.networks.get(network_id)
        if not net:
            return None
        peer_id = f"peer-{uuid.uuid4().hex[:8]}"
        peer = MeshPeer(peer_id, node_id, address)
        private, public = self._generate_keypair()
        peer.private_key = private
        peer.public_key = public
        net.peers[peer_id] = peer
        return peer

    def remove_peer(self, network_id: str, peer_id: str) -> bool:
        net = self.networks.get(network_id)
        if not net or peer_id not in net.peers:
            return False
        del net.peers[peer_id]
        return True

    def get_peer(self, network_id: str, peer_id: str) -> Optional[MeshPeer]:
        net = self.networks.get(network_id)
        if not net:
            return None
        return net.peers.get(peer_id)

    def update_peer_status(self, network_id: str, peer_id: str,
                           status: PeerStatus, **metrics) -> bool:
        peer = self.get_peer(network_id, peer_id)
        if not peer:
            return False
        peer.status = status
        if status == PeerStatus.ONLINE:
            peer.last_handshake = datetime.utcnow()
        if "latency_ms" in metrics:
            peer.latency_ms = metrics["latency_ms"]
        if "transfer_rx" in metrics:
            peer.transfer_rx = metrics["transfer_rx"]
        if "transfer_tx" in metrics:
            peer.transfer_tx = metrics["transfer_tx"]
        return True

    def get_topology(self, network_id: str) -> dict[str, Any]:
        net = self.networks.get(network_id)
        if not net:
            return {"error": "Network not found"}
        nodes = []
        for peer in net.peers.values():
            nodes.append({
                "id": peer.peer_id,
                "node_id": peer.node_id,
                "address": peer.address,
                "status": peer.status.value,
                "latency_ms": peer.latency_ms,
            })
        links = []
        peer_list = list(net.peers.values())
        for i in range(len(peer_list)):
            for j in range(i + 1, len(peer_list)):
                p1, p2 = peer_list[i], peer_list[j]
                link = TopologyLink(p1.peer_id, p2.peer_id)
                link.latency_ms = (p1.latency_ms + p2.latency_ms) / 2
                link.bandwidth_mbps = random.uniform(100, 1000)
                link.packet_loss = round(random.uniform(0, 0.5), 2)
                link.status = "active" if (p1.status == PeerStatus.ONLINE and
                                           p2.status == PeerStatus.ONLINE) else "degraded"
                links.append(link.to_dict())
        return {"network": net.to_dict(), "nodes": nodes, "links": links}

    def get_wireguard_config(self, network_id: str,
                             peer_id: str) -> Optional[str]:
        net = self.networks.get(network_id)
        if not net or net.mesh_type != MeshType.WIREGUARD:
            return None
        peer = net.peers.get(peer_id)
        if not peer:
            return None
        config_lines = ["[Interface]",
                       f"PrivateKey = {peer.private_key}",
                       f"Address = {peer.address}/{net.subnet.split('/')[1]}",
                       f"MTU = {net.mtu}",
                       "", "[Peer]"]
        for other in net.peers.values():
            if other.peer_id == peer_id:
                continue
            if other.status == PeerStatus.ONLINE:
                config_lines.extend([
                    f"# Peer: {other.node_id}",
                    f"PublicKey = {other.public_key}",
                    f"Endpoint = {other.endpoint}",
                    f"AllowedIPs = {','.join(other.allowed_ips)}",
                    f"PersistentKeepalive = {other.persistent_keepalive}",
                    ""
                ])
        return "\n".join(config_lines)

    def get_network_stats(self, network_id: str) -> dict[str, Any]:
        net = self.networks.get(network_id)
        if not net:
            return {}
        peers = list(net.peers.values())
        online = sum(1 for p in peers if p.status == PeerStatus.ONLINE)
        total_rx = sum(p.transfer_rx for p in peers)
        total_tx = sum(p.transfer_tx for p in peers)
        avg_latency = sum(p.latency_ms for p in peers) / max(len(peers), 1)
        return {
            "network_name": net.name,
            "mesh_type": net.mesh_type.value,
            "total_peers": len(peers),
            "online_peers": online,
            "offline_peers": len(peers) - online,
            "total_transfer_rx_gb": round(total_rx / (1024**3), 2),
            "total_transfer_tx_gb": round(total_tx / (1024**3), 2),
            "avg_latency_ms": round(avg_latency, 1),
            "subnet": net.subnet,
        }

    def restart_network(self, network_id: str) -> bool:
        net = self.networks.get(network_id)
        if not net:
            return False
        for peer in net.peers.values():
            peer.status = PeerStatus.PROVISIONING
        return True
