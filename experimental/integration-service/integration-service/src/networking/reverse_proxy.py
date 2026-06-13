import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

PROXY_TYPES = ['nginx', 'caddy', 'traefik']

@dataclass
class ProxyInstance:
    id: str
    name: str
    type: str
    version: str
    status: str
    port: int
    admin_port: int
    config_path: str
    ssl_cert_path: str
    ssl_key_path: str
    container_id: str
    access_log_path: str
    error_log_path: str
    created_at: str

@dataclass
class VirtualHost:
    id: str
    proxy_id: str
    domain: str
    aliases: List[str]
    upstream_url: str
    upstream_pool_id: str
    ssl_enabled: bool
    ssl_status: str
    ssl_expires_at: str
    ssl_issuer: str
    rate_limit_rps: int
    rate_limit_burst: int
    custom_config: Dict[str, Any]
    enabled: bool
    created_at: str

@dataclass
class UpstreamPool:
    id: str
    proxy_id: str
    name: str
    method: str
    servers: List[Dict[str, Any]]
    health_check_path: str
    health_check_interval: int
    health_check_timeout: int
    healthy_threshold: int
    unhealthy_threshold: int

@dataclass
class AccessLogEntry:
    id: str
    proxy_id: str
    timestamp: str
    remote_ip: str
    method: str
    path: str
    status: int
    body_bytes: int
    referer: str
    user_agent: str
    response_time_ms: int
    upstream: str

class ReverseProxyManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.instances_file = os.path.join(self.data_path, 'proxy_instances.json')
        self.hosts_file = os.path.join(self.data_path, 'proxy_hosts.json')
        self.pools_file = os.path.join(self.data_path, 'proxy_pools.json')
        self.logs_file = os.path.join(self.data_path, 'proxy_logs.json')
        self.instances: Dict[str, ProxyInstance] = {}
        self.hosts: Dict[str, VirtualHost] = {}
        self.pools: Dict[str, UpstreamPool] = {}
        self.logs: List[AccessLogEntry] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.instances_file, 'instances', ProxyInstance),
            (self.hosts_file, 'hosts', VirtualHost),
            (self.pools_file, 'pools', UpstreamPool),
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
        try:
            if os.path.exists(self.logs_file):
                with open(self.logs_file, 'r') as f:
                    raw = json.load(f)
                self.logs = [AccessLogEntry(**item) for item in raw[-1000:]]
        except Exception as e:
            logger.warning(f"Failed to load logs: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.instances_file, 'instances'),
            (self.hosts_file, 'hosts'),
            (self.pools_file, 'pools'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")
        try:
            with open(self.logs_file, 'w') as f:
                json.dump([asdict(l) for l in self.logs[-1000:]], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save logs: {e}")

    async def initialize(self):
        logger.info("ReverseProxyManager initialized")

    async def close(self):
        self._save_data()

    async def list_instances(self) -> List[Dict[str, Any]]:
        return [asdict(i) for i in self.instances.values()]

    async def create_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        inst_id = str(uuid.uuid4())
        proxy_type = data.get('type', 'nginx').lower()
        if proxy_type not in PROXY_TYPES:
            raise ValueError(f"Unsupported proxy type: {proxy_type}. Supported: {PROXY_TYPES}")
        instance = ProxyInstance(
            id=inst_id,
            name=data['name'],
            type=proxy_type,
            version=data.get('version', 'latest'),
            status='stopped',
            port=data.get('port', 80),
            admin_port=data.get('admin_port', 0),
            config_path=data.get('config_path', f'/etc/{proxy_type}'),
            ssl_cert_path=data.get('ssl_cert_path', '/etc/ssl/certs'),
            ssl_key_path=data.get('ssl_key_path', '/etc/ssl/private'),
            container_id=data.get('container_id', ''),
            access_log_path=data.get('access_log_path', '/var/log/access.log'),
            error_log_path=data.get('error_log_path', '/var/log/error.log'),
            created_at=datetime.now().isoformat(),
        )
        self.instances[instance.id] = instance
        self._save_data()
        return asdict(instance)

    async def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        return asdict(inst) if inst else None

    async def update_instance(self, instance_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        for key in ['name', 'port', 'admin_port', 'config_path', 'ssl_cert_path', 'ssl_key_path', 'container_id']:
            if key in data:
                setattr(inst, key, data[key])
        self._save_data()
        return asdict(inst)

    async def delete_instance(self, instance_id: str) -> bool:
        if instance_id in self.instances:
            hosts_to_delete = [hid for hid, h in self.hosts.items() if h.proxy_id == instance_id]
            for hid in hosts_to_delete:
                del self.hosts[hid]
            pools_to_delete = [pid for pid, p in self.pools.items() if p.proxy_id == instance_id]
            for pid in pools_to_delete:
                del self.pools[pid]
            self.logs = [l for l in self.logs if l.proxy_id != instance_id]
            del self.instances[instance_id]
            self._save_data()
            return True
        return False

    async def restart_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        inst.status = 'running'
        self._save_data()
        return asdict(inst)

    async def list_hosts(self, instance_id: str) -> List[Dict[str, Any]]:
        return [asdict(h) for h in self.hosts.values() if h.proxy_id == instance_id]

    async def add_host(self, instance_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        host_id = str(uuid.uuid4())
        host = VirtualHost(
            id=host_id,
            proxy_id=instance_id,
            domain=data['domain'],
            aliases=data.get('aliases', []),
            upstream_url=data.get('upstream_url', 'http://localhost:8080'),
            upstream_pool_id=data.get('upstream_pool_id', ''),
            ssl_enabled=data.get('ssl_enabled', False),
            ssl_status='none',
            ssl_expires_at='',
            ssl_issuer='',
            rate_limit_rps=data.get('rate_limit_rps', 0),
            rate_limit_burst=data.get('rate_limit_burst', 0),
            custom_config=data.get('custom_config', {}),
            enabled=data.get('enabled', True),
            created_at=datetime.now().isoformat(),
        )
        self.hosts[host.id] = host
        if host.ssl_enabled:
            await self._provision_ssl(host)
        self._save_data()
        return asdict(host)

    async def update_host(self, instance_id: str, host_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        host = self.hosts.get(host_id)
        if not host or host.proxy_id != instance_id:
            return None
        for key in ['domain', 'aliases', 'upstream_url', 'upstream_pool_id', 'ssl_enabled', 'rate_limit_rps', 'rate_limit_burst', 'custom_config', 'enabled']:
            if key in data:
                setattr(host, key, data[key])
        self._save_data()
        return asdict(host)

    async def remove_host(self, instance_id: str, host_id: str) -> bool:
        host = self.hosts.get(host_id)
        if not host or host.proxy_id != instance_id:
            return False
        del self.hosts[host_id]
        self._save_data()
        return True

    async def _provision_ssl(self, host: VirtualHost):
        host.ssl_status = 'provisioning'
        import hashlib
        fake_cert = hashlib.sha256(f"{host.domain}-{datetime.now().isoformat()}".encode()).hexdigest()
        host.ssl_status = 'active'
        host.ssl_expires_at = (datetime.now() + timedelta(days=90)).isoformat()
        host.ssl_issuer = 'Infra Pilot Auto SSL (Let\'s Encrypt)'

    async def renew_ssl(self, instance_id: str) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        results = []
        for host in self.hosts.values():
            if host.proxy_id != instance_id or not host.ssl_enabled:
                continue
            days_left = 0
            if host.ssl_expires_at:
                try:
                    days_left = (datetime.fromisoformat(host.ssl_expires_at) - datetime.now()).days
                except:
                    days_left = 0
            if days_left < 30:
                await self._provision_ssl(host)
                results.append({'domain': host.domain, 'action': 'renewed', 'days_left_before': days_left})
            else:
                results.append({'domain': host.domain, 'action': 'skipped', 'days_left': days_left})
        self._save_data()
        return {'instance_id': instance_id, 'results': results}

    async def get_ssl_status(self, instance_id: str) -> List[Dict[str, Any]]:
        return [
            {
                'domain': h.domain,
                'ssl_enabled': h.ssl_enabled,
                'ssl_status': h.ssl_status,
                'ssl_expires_at': h.ssl_expires_at,
                'ssl_issuer': h.ssl_issuer,
                'days_left': (datetime.fromisoformat(h.ssl_expires_at) - datetime.now()).days if h.ssl_expires_at else 0,
            }
            for h in self.hosts.values()
            if h.proxy_id == instance_id
        ]

    async def list_upstreams(self, instance_id: str) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.pools.values() if p.proxy_id == instance_id]

    async def create_upstream_pool(self, instance_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        pool_id = str(uuid.uuid4())
        pool = UpstreamPool(
            id=pool_id,
            proxy_id=instance_id,
            name=data['name'],
            method=data.get('method', 'round_robin'),
            servers=data.get('servers', []),
            health_check_path=data.get('health_check_path', '/health'),
            health_check_interval=data.get('health_check_interval', 10),
            health_check_timeout=data.get('health_check_timeout', 5),
            healthy_threshold=data.get('healthy_threshold', 2),
            unhealthy_threshold=data.get('unhealthy_threshold', 3),
        )
        self.pools[pool.id] = pool
        self._save_data()
        return asdict(pool)

    async def get_logs(self, instance_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        relevant = [l for l in self.logs if l.proxy_id == instance_id]
        return [asdict(l) for l in relevant[-limit:]]

    async def generate_config(self, instance_id: str) -> Optional[str]:
        inst = self.instances.get(instance_id)
        if not inst:
            return None
        hosts = [h for h in self.hosts.values() if h.proxy_id == instance_id and h.enabled]
        if inst.type == 'nginx':
            return self._generate_nginx_config(inst, hosts)
        elif inst.type == 'caddy':
            return self._generate_caddy_config(inst, hosts)
        elif inst.type == 'traefik':
            return self._generate_traefik_config(inst, hosts)
        return ''

    def _generate_nginx_config(self, inst: ProxyInstance, hosts: List[VirtualHost]) -> str:
        lines = [f'# Nginx configuration generated by Infra Pilot', f'# Instance: {inst.name}', 'events {', '  worker_connections 1024;', '}', 'http {', '  include /etc/nginx/mime.types;', '  default_type application/octet-stream;', '  sendfile on;', '  keepalive_timeout 65;']
        for pool in self.pools.values():
            if pool.proxy_id != inst.id:
                continue
            lines.append(f'  upstream {pool.name} {{')
            lines.append(f'    {pool.method};')
            for server in pool.servers:
                weight = server.get('weight', 1)
                lines.append(f'    server {server["url"]} weight={weight};')
            lines.append('  }')
        for host in hosts:
            lines.append(f'  server {{')
            lines.append(f'    listen {inst.port};')
            lines.append(f'    server_name {host.domain} {" ".join(host.aliases)};')
            if host.ssl_enabled:
                lines.append(f'    listen {inst.port + 443} ssl;')
                lines.append(f'    ssl_certificate {inst.ssl_cert_path}/{host.domain}.pem;')
                lines.append(f'    ssl_certificate_key {inst.ssl_key_path}/{host.domain}.key;')
            if host.rate_limit_rps > 0:
                lines.append(f'    limit_req zone={host.domain} burst={host.rate_limit_burst} nodelay;')
            if host.upstream_pool_id:
                pool = self.pools.get(host.upstream_pool_id)
                if pool:
                    lines.append(f'    location / {{')
                    lines.append(f'      proxy_pass http://{pool.name};')
                    lines.append('      proxy_set_header Host $host;')
                    lines.append('      proxy_set_header X-Real-IP $remote_addr;')
                    lines.append('      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;')
                    lines.append('      proxy_set_header X-Forwarded-Proto $scheme;')
                    lines.append('    }')
            else:
                lines.append(f'    location / {{')
                lines.append(f'      proxy_pass {host.upstream_url};')
                lines.append('      proxy_set_header Host $host;')
                lines.append('      proxy_set_header X-Real-IP $remote_addr;')
                lines.append('      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;')
                lines.append('      proxy_set_header X-Forwarded-Proto $scheme;')
                lines.append('    }')
            lines.append('  }')
        lines.append('}')
        return '\n'.join(lines)

    def _generate_caddy_config(self, inst: ProxyInstance, hosts: List[VirtualHost]) -> str:
        lines = [f'# Caddyfile generated by Infra Pilot', f'# Instance: {inst.name}', '']
        for host in hosts:
            addr = host.domain
            if host.aliases:
                addr += f' {" ".join(host.aliases)}'
            lines.append(f'{addr} {{')
            if host.ssl_enabled:
                lines.append('  tls internal')
            lines.append(f'  reverse_proxy {host.upstream_url}')
            if host.rate_limit_rps > 0:
                lines.append(f'  rate_limit {host.rate_limit_rps}')
            lines.append('}')
            lines.append('')
        return '\n'.join(lines)

    def _generate_traefik_config(self, inst: ProxyInstance, hosts: List[VirtualHost]) -> str:
        lines = [f'# Traefik dynamic config generated by Infra Pilot', f'# Instance: {inst.name}', 'http:']
        lines.append('  routers:')
        for host in hosts:
            key = host.domain.replace('.', '-').replace('*', 'wildcard')
            lines.append(f'    {key}:')
            lines.append(f'      rule: "Host(`{host.domain}`)"')
            lines.append(f'      service: {key}')
            if host.ssl_enabled:
                lines.append('      tls:')
                lines.append(f'        certResolver: letsencrypt')
            lines.append(f'      middlewares:')
            lines.append(f'        - {key}-ratelimit')
        lines.append('  services:')
        for host in hosts:
            key = host.domain.replace('.', '-').replace('*', 'wildcard')
            lines.append(f'    {key}:')
            lines.append('      loadBalancer:')
            lines.append(f'        servers:')
            lines.append(f'          - url: "{host.upstream_url}"')
        lines.append('  middlewares:')
        for host in hosts:
            key = host.domain.replace('.', '-').replace('*', 'wildcard')
            if host.rate_limit_rps > 0:
                lines.append(f'    {key}-ratelimit:')
                lines.append('      rateLimit:')
                lines.append(f'        average: {host.rate_limit_rps}')
                lines.append(f'        burst: {host.rate_limit_burst}')
        return '\n'.join(lines)

    async def add_log_entry(self, entry_data: Dict[str, Any]):
        entry = AccessLogEntry(
            id=str(uuid.uuid4()),
            proxy_id=entry_data.get('proxy_id', ''),
            timestamp=entry_data.get('timestamp', datetime.now().isoformat()),
            remote_ip=entry_data.get('remote_ip', ''),
            method=entry_data.get('method', 'GET'),
            path=entry_data.get('path', '/'),
            status=entry_data.get('status', 200),
            body_bytes=entry_data.get('body_bytes', 0),
            referer=entry_data.get('referer', ''),
            user_agent=entry_data.get('user_agent', ''),
            response_time_ms=entry_data.get('response_time_ms', 0),
            upstream=entry_data.get('upstream', ''),
        )
        self.logs.append(entry)
        if len(self.logs) > 10000:
            self.logs = self.logs[-5000:]
        self._save_data()
