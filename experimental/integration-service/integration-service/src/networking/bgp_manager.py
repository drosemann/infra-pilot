import asyncio
import json
import logging
import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class BGPSession:
    id: str
    name: str
    local_asn: int
    remote_asn: int
    neighbor_ip: str
    type: str
    multihop_ttl: int
    source_interface: str
    source_ip: str
    password_encrypted: str
    hold_time: int
    keepalive_interval: int
    status: str
    address_families: List[str]
    error_count: int
    last_error: str
    uptime_seconds: int
    created_at: str

@dataclass
class BGPAnnouncement:
    id: str
    session_id: str
    prefix: str
    description: str
    as_path_prepend: List[int]
    communities: List[str]
    large_communities: List[str]
    rpki_status: str
    enabled: bool
    created_at: str

@dataclass
class CommunityTag:
    id: str
    name: str
    community: str
    description: str
    type: str
    session_ids: List[str]

class BGPRouteManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.sessions_file = os.path.join(self.data_path, 'bgp_sessions.json')
        self.prefixes_file = os.path.join(self.data_path, 'bgp_prefixes.json')
        self.communities_file = os.path.join(self.data_path, 'bgp_communities.json')
        self.sessions: Dict[str, BGPSession] = {}
        self.prefixes: Dict[str, BGPAnnouncement] = {}
        self.communities: Dict[str, CommunityTag] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.sessions_file, 'sessions', BGPSession),
            (self.prefixes_file, 'prefixes', BGPAnnouncement),
            (self.communities_file, 'communities', CommunityTag),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        storage[item['id']] = cls(**item)
            except Exception as e:
                logger.warning(f"Failed to load {attr}: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.sessions_file, 'sessions'),
            (self.prefixes_file, 'prefixes'),
            (self.communities_file, 'communities'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("BGPRouteManager initialized")

    async def close(self):
        self._save_data()

    def _validate_prefix(self, prefix: str) -> bool:
        pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(pattern, prefix):
            return False
        ip_part, mask = prefix.split('/')
        mask = int(mask)
        if mask < 8 or mask > 32:
            return False
        octets = [int(x) for x in ip_part.split('.')]
        if any(o < 0 or o > 255 for o in octets):
            return False
        return True

    async def list_sessions(self) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.sessions.values()]

    async def create_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        session = BGPSession(
            id=session_id,
            name=data['name'],
            local_asn=data.get('local_asn', 64512),
            remote_asn=data['remote_asn'],
            neighbor_ip=data['neighbor_ip'],
            type=data.get('type', 'ebgp'),
            multihop_ttl=data.get('multihop_ttl', 1),
            source_interface=data.get('source_interface', ''),
            source_ip=data.get('source_ip', ''),
            password_encrypted=self._encrypt(data.get('password', '')),
            hold_time=data.get('hold_time', 180),
            keepalive_interval=data.get('keepalive_interval', 60),
            status='idle',
            address_families=data.get('address_families', ['ipv4']),
            error_count=0,
            last_error='',
            uptime_seconds=0,
            created_at=datetime.now().isoformat(),
        )
        self.sessions[session.id] = session
        self._save_data()
        return asdict(session)

    def _encrypt(self, value: str) -> str:
        import base64
        return base64.b64encode(value.encode()).decode('ascii')

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        return asdict(session) if session else None

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        for key in ['name', 'remote_asn', 'neighbor_ip', 'multihop_ttl', 'source_interface', 'source_ip', 'hold_time', 'keepalive_interval', 'address_families']:
            if key in data:
                setattr(session, key, data[key])
        if 'password' in data:
            session.password_encrypted = self._encrypt(data['password'])
        self._save_data()
        return asdict(session)

    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            prefixes_to_delete = [pid for pid, p in self.prefixes.items() if p.session_id == session_id]
            for pid in prefixes_to_delete:
                del self.prefixes[pid]
            del self.sessions[session_id]
            self._save_data()
            return True
        return False

    async def reset_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.status = 'idle'
        session.error_count = 0
        session.last_error = ''
        session.uptime_seconds = 0
        self._save_data()
        return asdict(session)

    async def list_prefixes(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.prefixes.values()]

    async def announce_prefix(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(data.get('session_id', ''))
        if not session:
            return None
        prefix = data['prefix']
        if not self._validate_prefix(prefix):
            raise ValueError(f"Invalid prefix: {prefix}")
        prefix_id = str(uuid.uuid4())
        announcement = BGPAnnouncement(
            id=prefix_id,
            session_id=session.id,
            prefix=prefix,
            description=data.get('description', ''),
            as_path_prepend=data.get('as_path_prepend', []),
            communities=data.get('communities', []),
            large_communities=data.get('large_communities', []),
            rpki_status='unknown',
            enabled=data.get('enabled', True),
            created_at=datetime.now().isoformat(),
        )
        self.prefixes[announcement.id] = announcement
        self._save_data()
        return asdict(announcement)

    async def withdraw_prefix(self, prefix_id: str) -> bool:
        if prefix_id in self.prefixes:
            prefix = self.prefixes[prefix_id]
            prefix.enabled = False
            self._save_data()
            return True
        return False

    async def list_communities(self) -> List[Dict[str, Any]]:
        return [asdict(c) for c in self.communities.values()]

    async def create_community(self, data: Dict[str, Any]) -> Dict[str, Any]:
        comm_id = str(uuid.uuid4())
        community = CommunityTag(
            id=comm_id,
            name=data['name'],
            community=data['community'],
            description=data.get('description', ''),
            type=data.get('type', 'standard'),
            session_ids=data.get('session_ids', []),
        )
        self.communities[community.id] = community
        self._save_data()
        return asdict(community)

    async def get_routing_table(self) -> Dict[str, Any]:
        routes = []
        for prefix in self.prefixes.values():
            if not prefix.enabled:
                continue
            session = self.sessions.get(prefix.session_id)
            routes.append({
                'prefix': prefix.prefix,
                'next_hop': session.neighbor_ip if session else 'unknown',
                'local_asn': session.local_asn if session else 0,
                'remote_asn': session.remote_asn if session else 0,
                'as_path': prefix.as_path_prepend,
                'communities': prefix.communities,
                'rpki_status': prefix.rpki_status,
                'session_status': session.status if session else 'unknown',
            })
        return {
            'total_routes': len(routes),
            'routes': routes,
            'timestamp': datetime.now().isoformat(),
        }

    async def simulate_session_state(self, session_id: str, target_state: str) -> Optional[Dict[str, Any]]:
        valid_states = ['idle', 'connect', 'active', 'opensent', 'openconfirm', 'established']
        session = self.sessions.get(session_id)
        if not session:
            return None
        if target_state not in valid_states:
            return {'error': f'Invalid state: {target_state}. Valid: {valid_states}'}
        session.status = target_state
        if target_state == 'established':
            session.uptime_seconds = int((datetime.now() - datetime.fromisoformat(session.created_at)).total_seconds())
        elif target_state == 'idle':
            session.uptime_seconds = 0
        self._save_data()
        return asdict(session)

    async def generate_bird_config(self) -> str:
        config_lines = ['# BIRD configuration generated by Infra Pilot BGP Route Manager', f'# Generated at {datetime.now().isoformat()}', '', 'router id {self_ip};', '', 'protocol device {', '  scan time 10;', '}', '']
        for session in self.sessions.values():
            config_lines.append(f'protocol bgp "{session.name}" {{')
            config_lines.append(f'  local as {session.local_asn};')
            config_lines.append(f'  neighbor {session.neighbor_ip} as {session.remote_asn};')
            if session.type == 'ebgp':
                config_lines.append('  ebgp;')
            if session.multihop_ttl > 1:
                config_lines.append(f'  multihop {session.multihop_ttl};')
            config_lines.append(f'  hold time {session.hold_time};')
            config_lines.append(f'  keepalive time {session.keepalive_interval};')
            config_lines.append('  ipv4 {')
            config_lines.append('    import all;')
            config_lines.append('    export all;')
            config_lines.append('  };')
            config_lines.append('}', '')
        for prefix in self.prefixes.values():
            if prefix.enabled:
                community_str = ', '.join(prefix.communities) if prefix.communities else ''
                config_lines.append(f'protocol static "{prefix.prefix}" {{')
                config_lines.append(f'  route {prefix.prefix} via "lo";')
                if community_str:
                    config_lines.append(f'  preference 100;')
                config_lines.append('}', '')
        return '\n'.join(config_lines)

    async def generate_frr_config(self) -> str:
        config_lines = ['! FRR configuration generated by Infra Pilot BGP Route Manager', f'! Generated at {datetime.now().isoformat()}', '!', 'router bgp {local_asn}', ' bgp router-id {self_ip}', '']
        for session in self.sessions.values():
            config_lines.append(f' neighbor {session.neighbor_ip} remote-as {session.remote_asn}')
            config_lines.append(f' neighbor {session.neighbor_ip} description {session.name}')
            if session.source_ip:
                config_lines.append(f' neighbor {session.neighbor_ip} update-source {session.source_ip}')
            config_lines.append(f' neighbor {session.neighbor_ip} timers {session.keepalive_interval} {session.hold_time}')
            if session.type == 'ebgp':
                config_lines.append(f' neighbor {session.neighbor_ip} ebgp-multihop {session.multihop_ttl}')
            config_lines.append(f' address-family ipv4 unicast')
            config_lines.append(f'  neighbor {session.neighbor_ip} activate')
            config_lines.append(f'  neighbor {session.neighbor_ip} route-map RM-IN in')
            config_lines.append(f'  neighbor {session.neighbor_ip} route-map RM-OUT out')
            config_lines.append(f' exit-address-family')
        config_lines.append('!')
        for prefix in self.prefixes.values():
            if prefix.enabled:
                config_lines.append(f'ip route {prefix.prefix} Null0')
        config_lines.append('!')
        config_lines.append('route-map RM-IN permit 10')
        config_lines.append(' set community 64512:100')
        config_lines.append('!')
        config_lines.append('route-map RM-OUT permit 10')
        config_lines.append('!')
        return '\n'.join(config_lines)
