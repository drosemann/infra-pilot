import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class FilterInstance:
    id: str
    type: str
    status: str
    version: str
    port: int
    web_port: int
    dns_upstream: List[str]
    blocking_enabled: bool
    blocklist_count: int
    queries_today: int
    blocked_today: int
    percentage_blocked: float
    dhcp_enabled: bool
    dhcp_range_start: str
    dhcp_range_end: str

@dataclass
class BlocklistEntry:
    id: str
    domain: str
    type: str
    source: str
    list_name: str
    enabled: bool
    comment: str
    hit_count: int
    last_hit: str
    created_at: str

@dataclass
class DHCPLease:
    id: str
    mac_address: str
    ip_address: str
    hostname: str
    expires_at: str
    state: str
    vendor_class: str
    client_id: str

@dataclass
class ClientPolicy:
    mac_address: str
    ip_address: str
    client_name: str
    filtering_enabled: bool
    blocking_mode: str
    rate_limit: int
    query_log_enabled: bool
    groups: List[str]

@dataclass
class QueryLogEntry:
    id: str
    timestamp: str
    client_ip: str
    domain: str
    query_type: str
    response: str
    action: str
    duration_ms: int
    blocked: bool

class DNSFilterManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.instance_file = os.path.join(self.data_path, 'filter_instance.json')
        self.blocklist_file = os.path.join(self.data_path, 'filter_blocklist.json')
        self.allowlist_file = os.path.join(self.data_path, 'filter_allowlist.json')
        self.leases_file = os.path.join(self.data_path, 'filter_leases.json')
        self.policies_file = os.path.join(self.data_path, 'filter_policies.json')
        self.querylog_file = os.path.join(self.data_path, 'filter_querylog.json')
        self.instance: Optional[FilterInstance] = None
        self.blocklist: Dict[str, BlocklistEntry] = {}
        self.allowlist: Dict[str, BlocklistEntry] = {}
        self.leases: Dict[str, DHCPLease] = {}
        self.policies: Dict[str, ClientPolicy] = {}
        self.query_log: List[QueryLogEntry] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        try:
            if os.path.exists(self.instance_file):
                with open(self.instance_file, 'r') as f:
                    self.instance = FilterInstance(**json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load filter instance: {e}")
        for file_key, attr, cls in [
            (self.blocklist_file, 'blocklist', BlocklistEntry),
            (self.allowlist_file, 'allowlist', BlocklistEntry),
            (self.leases_file, 'leases', DHCPLease),
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
            if os.path.exists(self.policies_file):
                with open(self.policies_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    pol = ClientPolicy(**item)
                    self.policies[pol.mac_address] = pol
        except Exception as e:
            logger.warning(f"Failed to load policies: {e}")
        try:
            if os.path.exists(self.querylog_file):
                with open(self.querylog_file, 'r') as f:
                    raw = json.load(f)
                self.query_log = [QueryLogEntry(**item) for item in raw[-5000:]]
        except Exception as e:
            logger.warning(f"Failed to load query log: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.blocklist_file, 'blocklist'),
            (self.allowlist_file, 'allowlist'),
            (self.leases_file, 'leases'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")
        try:
            with open(self.policies_file, 'w') as f:
                data = [asdict(v) for v in self.policies.values()]
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")
        try:
            with open(self.querylog_file, 'w') as f:
                json.dump([asdict(l) for l in self.query_log[-5000:]], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save query log: {e}")
        if self.instance:
            try:
                with open(self.instance_file, 'w') as f:
                    json.dump(asdict(self.instance), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save instance: {e}")

    async def initialize(self):
        logger.info("DNSFilterManager initialized")
        if not self.instance:
            self.instance = FilterInstance(
                id=str(uuid.uuid4()),
                type='pihole',
                status='running',
                version='6.0',
                port=53,
                web_port=80,
                dns_upstream=['1.1.1.1', '8.8.8.8'],
                blocking_enabled=True,
                blocklist_count=0,
                queries_today=0,
                blocked_today=0,
                percentage_blocked=0.0,
                dhcp_enabled=False,
                dhcp_range_start='192.168.1.100',
                dhcp_range_end='192.168.1.200',
            )
            self._save_data()

    async def close(self):
        self._save_data()

    async def get_status(self) -> Dict[str, Any]:
        if not self.instance:
            return {'status': 'not_configured'}
        return asdict(self.instance)

    async def get_stats(self) -> Dict[str, Any]:
        if not self.instance:
            return {}
        total = self.instance.queries_today
        blocked = self.instance.blocked_today
        pct = round(blocked / total * 100, 2) if total > 0 else 0
        top_domains = {}
        top_clients = {}
        for log in self.query_log:
            top_domains[log.domain] = top_domains.get(log.domain, 0) + 1
            top_clients[log.client_ip] = top_clients.get(log.client_ip, 0) + 1
        return {
            'queries_today': total,
            'blocked_today': blocked,
            'percentage_blocked': pct,
            'total_clients': len(set(l.client_ip for l in self.query_log)),
            'unique_domains': len(set(l.domain for l in self.query_log)),
            'top_blocked_domains': dict(sorted({d: c for d, c in top_domains.items() if any(l.blocked for l in self.query_log if l.domain == d)}.items(), key=lambda x: -x[1])[:20]),
            'top_clients': dict(sorted(top_clients.items(), key=lambda x: -x[1])[:10]),
            'blocklist_count': len(self.blocklist),
            'allowlist_count': len(self.allowlist),
        }

    async def get_query_log(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return [asdict(l) for l in self.query_log[-limit-offset:len(self.query_log)-offset]] if self.query_log else []

    async def get_blocklist(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self.blocklist.values()]

    async def get_allowlist(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self.allowlist.values()]

    async def add_to_blocklist(self, data: Dict[str, Any]) -> BlocklistEntry:
        entry = BlocklistEntry(
            id=str(uuid.uuid4()),
            domain=data['domain'].lower(),
            type='blocked',
            source=data.get('source', 'manual'),
            list_name=data.get('list_name', 'manual'),
            enabled=data.get('enabled', True),
            comment=data.get('comment', ''),
            hit_count=0,
            last_hit='',
            created_at=datetime.now().isoformat(),
        )
        self.blocklist[entry.id] = entry
        if self.instance:
            self.instance.blocklist_count = len(self.blocklist)
        self._save_data()
        return entry

    async def remove_from_blocklist(self, entry_id: str) -> bool:
        if entry_id in self.blocklist:
            del self.blocklist[entry_id]
            if self.instance:
                self.instance.blocklist_count = len(self.blocklist)
            self._save_data()
            return True
        return False

    async def add_to_allowlist(self, data: Dict[str, Any]) -> BlocklistEntry:
        entry = BlocklistEntry(
            id=str(uuid.uuid4()),
            domain=data['domain'].lower(),
            type='allowed',
            source=data.get('source', 'manual'),
            list_name=data.get('list_name', 'manual'),
            enabled=data.get('enabled', True),
            comment=data.get('comment', ''),
            hit_count=0,
            last_hit='',
            created_at=datetime.now().isoformat(),
        )
        self.allowlist[entry.id] = entry
        self._save_data()
        return entry

    async def remove_from_allowlist(self, entry_id: str) -> bool:
        if entry_id in self.allowlist:
            del self.allowlist[entry_id]
            self._save_data()
            return True
        return False

    async def update_dhcp_config(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.instance:
            return None
        for key in ['dhcp_enabled', 'dhcp_range_start', 'dhcp_range_end']:
            if key in data:
                setattr(self.instance, key, data[key])
        self._save_data()
        return asdict(self.instance)

    async def get_dhcp_config(self) -> Optional[Dict[str, Any]]:
        if not self.instance:
            return None
        return {
            'enabled': self.instance.dhcp_enabled,
            'range_start': self.instance.dhcp_range_start,
            'range_end': self.instance.dhcp_range_end,
        }

    async def get_leases(self) -> List[Dict[str, Any]]:
        return [asdict(l) for l in self.leases.values()]

    async def add_lease(self, data: Dict[str, Any]) -> DHCPLease:
        lease = DHCPLease(
            id=str(uuid.uuid4()),
            mac_address=data['mac_address'].upper(),
            ip_address=data['ip_address'],
            hostname=data.get('hostname', ''),
            expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            state='active',
            vendor_class=data.get('vendor_class', ''),
            client_id=data.get('client_id', ''),
        )
        self.leases[lease.id] = lease
        self._save_data()
        return lease

    async def get_clients(self) -> List[Dict[str, Any]]:
        clients = {}
        for log in self.query_log:
            ip = log.client_ip
            if ip not in clients:
                clients[ip] = {
                    'ip_address': ip,
                    'hostname': '',
                    'total_queries': 0,
                    'blocked_queries': 0,
                    'last_query': '',
                }
            clients[ip]['total_queries'] += 1
            if log.blocked:
                clients[ip]['blocked_queries'] += 1
            clients[ip]['last_query'] = log.timestamp
        for pol in self.policies.values():
            if pol.ip_address not in clients:
                clients[pol.ip_address] = {
                    'ip_address': pol.ip_address,
                    'hostname': pol.client_name,
                    'total_queries': 0,
                    'blocked_queries': 0,
                    'last_query': '',
                }
            clients[pol.ip_address]['hostname'] = pol.client_name
        return list(clients.values())

    async def set_client_policy(self, ip_address: str, data: Dict[str, Any]) -> ClientPolicy:
        policy = self.policies.get(ip_address)
        if policy:
            for key in ['client_name', 'filtering_enabled', 'blocking_mode', 'rate_limit', 'query_log_enabled', 'groups']:
                if key in data:
                    setattr(policy, key, data[key])
        else:
            policy = ClientPolicy(
                mac_address=data.get('mac_address', ''),
                ip_address=ip_address,
                client_name=data.get('client_name', ''),
                filtering_enabled=data.get('filtering_enabled', True),
                blocking_mode=data.get('blocking_mode', 'default'),
                rate_limit=data.get('rate_limit', 0),
                query_log_enabled=data.get('query_log_enabled', True),
                groups=data.get('groups', []),
            )
        self.policies[ip_address] = policy
        self._save_data()
        return policy

    async def toggle_blocking(self, enabled: bool) -> Optional[Dict[str, Any]]:
        if not self.instance:
            return None
        self.instance.blocking_enabled = enabled
        self._save_data()
        return asdict(self.instance)

    async def simulate_query(self, domain: str, client_ip: str, query_type: str = 'A') -> QueryLogEntry:
        domain = domain.lower()
        is_blocked = False
        action = 'allowed'
        blocked_reason = ''
        for entry in self.blocklist.values():
            if entry.enabled and (entry.domain in domain or domain.endswith('.' + entry.domain)):
                is_blocked = True
                action = 'blocked'
                entry.hit_count += 1
                entry.last_hit = datetime.now().isoformat()
                blocked_reason = f'Blocklist: {entry.domain}'
                break
        for entry in self.allowlist.values():
            if entry.enabled and domain == entry.domain:
                is_blocked = False
                action = 'allowed'
                blocked_reason = ''
                break
        if self.instance and not self.instance.blocking_enabled:
            is_blocked = False
            action = 'allowed'
            blocked_reason = 'blocking_disabled'
        policy = self.policies.get(client_ip)
        if policy and not policy.filtering_enabled:
            is_blocked = False
            action = 'allowed'
            blocked_reason = 'client_policy'
        log_entry = QueryLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            client_ip=client_ip,
            domain=domain,
            query_type=query_type,
            response='0.0.0.0' if is_blocked else '1.2.3.4',
            action=action,
            duration_ms=5,
            blocked=is_blocked,
        )
        self.query_log.append(log_entry)
        if len(self.query_log) > 10000:
            self.query_log = self.query_log[-5000:]
        if self.instance:
            self.instance.queries_today += 1
            if is_blocked:
                self.instance.blocked_today += 1
            self.instance.percentage_blocked = round(self.instance.blocked_today / max(self.instance.queries_today, 1) * 100, 2)
        self._save_data()
        return log_entry

    async def update_upstream_dns(self, upstreams: List[str]) -> Optional[Dict[str, Any]]:
        if not self.instance:
            return None
        self.instance.dns_upstream = upstreams
        self._save_data()
        return asdict(self.instance)

    async def get_blocked_domains_top(self, limit: int = 20) -> List[Dict[str, Any]]:
        blocked_counts = {}
        for log in self.query_log:
            if log.blocked:
                blocked_counts[log.domain] = blocked_counts.get(log.domain, 0) + 1
        entries = [{'domain': d, 'count': c} for d, c in sorted(blocked_counts.items(), key=lambda x: -x[1])[:limit]]
        for entry in entries:
            for bl in self.blocklist.values():
                if bl.domain in entry['domain'] or entry['domain'].endswith('.' + bl.domain):
                    entry['source'] = bl.source
                    entry['list_name'] = bl.list_name
                    break
        return entries

    async def add_blocklist_url(self, url: str, name: str) -> Dict[str, Any]:
        import hashlib
        fake_domains = [
            'ads.example.com', 'tracker.example.org', 'malware.test.net',
            'spam.example.co', 'analytics.example.io', 'telemetry.example.dev',
            'doubleclick.net', 'googlesyndication.com', 'facebook.com/tr',
            'scorecardresearch.com', 'outbrain.com', 'taboola.com',
        ]
        added = 0
        for domain in fake_domains:
            entry = BlocklistEntry(
                id=str(uuid.uuid4()),
                domain=domain,
                type='blocked',
                source='adlist',
                list_name=name,
                enabled=True,
                comment=f'From: {url}',
                hit_count=0,
                last_hit='',
                created_at=datetime.now().isoformat(),
            )
            self.blocklist[entry.id] = entry
            added += 1
        if self.instance:
            self.instance.blocklist_count = len(self.blocklist)
        self._save_data()
        return {'url': url, 'name': name, 'domains_added': added, 'total_blocklist': len(self.blocklist)}
