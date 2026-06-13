import asyncio
import json
import logging
import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class VPNServer:
    id: str
    name: str
    type: str
    status: str
    port: int
    protocol: str
    interface_name: str
    public_ip: str
    public_key: str
    private_key_encrypted: str
    dns_servers: List[str]
    allowed_ips: str
    mtu: int
    created_at: str
    expires_at: str
    client_count: int

@dataclass
class VPNClient:
    id: str
    server_id: str
    name: str
    enabled: bool
    public_key: str
    private_key_encrypted: str
    assigned_ip: str
    allowed_ips: str
    persistent_keepalive: int
    bytes_sent: int
    bytes_received: int
    connected: bool
    last_handshake: str
    created_at: str
    expires_at: str

class VPNServiceManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.servers_file = os.path.join(self.data_path, 'vpn_servers.json')
        self.clients_file = os.path.join(self.data_path, 'vpn_clients.json')
        self.servers: Dict[str, VPNServer] = {}
        self.clients: Dict[str, VPNClient] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        try:
            if os.path.exists(self.servers_file):
                with open(self.servers_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    srv = VPNServer(**item)
                    self.servers[srv.id] = srv
        except Exception as e:
            logger.warning(f"Failed to load VPN servers: {e}")
        try:
            if os.path.exists(self.clients_file):
                with open(self.clients_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    client = VPNClient(**item)
                    self.clients[client.id] = client
        except Exception as e:
            logger.warning(f"Failed to load VPN clients: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.servers_file, 'servers'),
            (self.clients_file, 'clients'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("VPNServiceManager initialized")

    async def close(self):
        self._save_data()

    async def list_servers(self) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.servers.values()]

    async def create_server(self, data: Dict[str, Any]) -> Dict[str, Any]:
        server_id = str(uuid.uuid4())
        server_type = data.get('type', 'wireguard')
        port = data.get('port', 51820 if server_type == 'wireguard' else 1194)
        now = datetime.now()
        expires = now + timedelta(days=data.get('expiry_days', 365))
        server = VPNServer(
            id=server_id,
            name=data['name'],
            type=server_type,
            status='stopped',
            port=port,
            protocol=data.get('protocol', 'udp'),
            interface_name=f"{server_type}_{data.get('name', server_id)[:8]}",
            public_ip=data.get('public_ip', '0.0.0.0'),
            public_key=self._generate_key(server_type, 'public'),
            private_key_encrypted=self._encrypt_key(self._generate_key(server_type, 'private')),
            dns_servers=data.get('dns_servers', ['1.1.1.1', '8.8.8.8']),
            allowed_ips=data.get('allowed_ips', '0.0.0.0/0, ::/0'),
            mtu=data.get('mtu', 1420),
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            client_count=0,
        )
        self.servers[server.id] = server
        self._save_data()
        return asdict(server)

    def _generate_key(self, key_type: str, key_part: str) -> str:
        raw = base64.b64encode(os.urandom(32)).decode('ascii')
        if key_type == 'wireguard':
            return raw
        return f"vpn_{key_part}_{raw[:16]}"

    def _encrypt_key(self, key: str) -> str:
        return base64.b64encode(key.encode()).decode('ascii')

    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_id)
        return asdict(server) if server else None

    async def delete_server(self, server_id: str) -> bool:
        if server_id in self.servers:
            deleted_clients = [cid for cid, c in self.clients.items() if c.server_id == server_id]
            for cid in deleted_clients:
                del self.clients[cid]
            del self.servers[server_id]
            self._save_data()
            return True
        return False

    async def start_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_id)
        if not server:
            return None
        server.status = 'running'
        self._save_data()
        return asdict(server)

    async def stop_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_id)
        if not server:
            return None
        server.status = 'stopped'
        for client in self.clients.values():
            if client.server_id == server_id:
                client.connected = False
        self._save_data()
        return asdict(server)

    async def restart_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_id)
        if not server:
            return None
        server.status = 'running'
        self._save_data()
        return asdict(server)

    async def list_clients(self, server_id: str) -> List[Dict[str, Any]]:
        return [asdict(c) for c in self.clients.values() if c.server_id == server_id]

    async def add_client(self, server_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        server = self.servers.get(server_id)
        if not server:
            return None
        client_id = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(days=data.get('expiry_days', 90))
        client = VPNClient(
            id=client_id,
            server_id=server_id,
            name=data['name'],
            enabled=True,
            public_key=self._generate_key(server.type, 'public'),
            private_key_encrypted=self._encrypt_key(self._generate_key(server.type, 'private')),
            assigned_ip=data.get('assigned_ip', f"10.0.0.{len([c for c in self.clients.values() if c.server_id == server_id]) + 2}"),
            allowed_ips=data.get('allowed_ips', '0.0.0.0/0'),
            persistent_keepalive=data.get('persistent_keepalive', 25),
            bytes_sent=0,
            bytes_received=0,
            connected=False,
            last_handshake='',
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        self.clients[client.id] = client
        server.client_count = len([c for c in self.clients.values() if c.server_id == server_id])
        self._save_data()
        return asdict(client)

    async def remove_client(self, server_id: str, client_id: str) -> bool:
        client = self.clients.get(client_id)
        if not client or client.server_id != server_id:
            return False
        del self.clients[client_id]
        server = self.servers.get(server_id)
        if server:
            server.client_count = len([c for c in self.clients.values() if c.server_id == server_id])
        self._save_data()
        return True

    async def get_client_config(self, server_id: str, client_id: str) -> Optional[str]:
        server = self.servers.get(server_id)
        client = self.clients.get(client_id)
        if not server or not client or client.server_id != server_id:
            return None
        if server.type == 'wireguard':
            private_key = base64.b64decode(client.private_key_encrypted.encode()).decode('ascii')
            server_pub_key = base64.b64decode(server.public_key.encode()).decode('ascii')
            config = f"""[Interface]
PrivateKey = {private_key}
Address = {client.assigned_ip}/24
DNS = {', '.join(server.dns_servers)}
MTU = {server.mtu}

[Peer]
PublicKey = {server_pub_key}
Endpoint = {server.public_ip}:{server.port}
AllowedIPs = {client.allowed_ips}
PersistentKeepalive = {client.persistent_keepalive}
"""
            return config
        else:
            return f"client\ndev tun\nproto {server.protocol}\nremote {server.public_ip} {server.port}\nresolv-retry infinite\nnobind\npersist-key\npersist-tun\nremote-cert-tls server\ncipher AES-256-GCM\ndev tun\nstatus /dev/null\nverb 3\n"

    async def get_usage(self, server_id: str) -> Dict[str, Any]:
        server = self.servers.get(server_id)
        if not server:
            return {}
        server_clients = [c for c in self.clients.values() if c.server_id == server_id]
        total_sent = sum(c.bytes_sent for c in server_clients)
        total_received = sum(c.bytes_received for c in server_clients)
        active_clients = sum(1 for c in server_clients if c.connected)
        return {
            'server_id': server_id,
            'server_name': server.name,
            'total_clients': len(server_clients),
            'active_clients': active_clients,
            'total_bytes_sent': total_sent,
            'total_bytes_received': total_received,
            'total_bytes': total_sent + total_received,
            'clients': [
                {
                    'name': c.name,
                    'connected': c.connected,
                    'bytes_sent': c.bytes_sent,
                    'bytes_received': c.bytes_received,
                    'last_handshake': c.last_handshake,
                }
                for c in server_clients
            ],
            'timestamp': datetime.now().isoformat(),
        }

    async def generate_qr_data(self, server_id: str, client_id: str) -> Optional[str]:
        config = await self.get_client_config(server_id, client_id)
        if not config:
            return None
        return base64.b64encode(config.encode()).decode('ascii')
