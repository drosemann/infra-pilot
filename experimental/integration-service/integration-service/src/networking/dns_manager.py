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

RECORD_TYPES = {'A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'NS', 'PTR', 'SOA', 'CAA', 'DS', 'DNSKEY', 'NAPTR', 'SSHFP', 'TLSA'}

@dataclass
class DNSZone:
    id: str
    domain: str
    type: str
    master_servers: List[str]
    allowed_transfers: List[str]
    serial: int
    refresh: int
    retry: int
    expire: int
    ttl: int
    dnssec_status: str
    dnskey_record: str
    ds_record: str
    soa_record: Dict[str, Any]
    nameservers: List[str]
    created_at: str
    updated_at: str

@dataclass
class DNSRecord:
    id: str
    zone_id: str
    name: str
    type: str
    value: str
    priority: int
    weight: int
    port: int
    ttl: int
    enabled: bool
    notes: str
    created_at: str
    updated_at: str

class DNSZoneManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.zones_file = os.path.join(self.data_path, 'dns_zones.json')
        self.records_file = os.path.join(self.data_path, 'dns_records.json')
        self.zones: Dict[str, DNSZone] = {}
        self.records: Dict[str, DNSRecord] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        try:
            if os.path.exists(self.zones_file):
                with open(self.zones_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    zone = DNSZone(**item)
                    self.zones[zone.id] = zone
        except Exception as e:
            logger.warning(f"Failed to load zones: {e}")
        try:
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r') as f:
                    data = json.load(f)
                for item in data:
                    record = DNSRecord(**item)
                    self.records[record.id] = record
        except Exception as e:
            logger.warning(f"Failed to load records: {e}")

    def _save_data(self):
        for file_key, attr in [(self.zones_file, 'zones'), (self.records_file, 'records')]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("DNSZoneManager initialized")

    async def close(self):
        self._save_data()

    def _validate_domain(self, domain: str) -> bool:
        pattern = r'^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\.?)$'
        return bool(re.match(pattern, domain))

    def _validate_record(self, zone: DNSZone, name: str, rtype: str, value: str) -> Optional[str]:
        full_name = f"{name}.{zone.domain}" if name else zone.domain
        if rtype == 'A' and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
            return 'Invalid A record value (must be IPv4)'
        if rtype == 'AAAA' and not re.match(r'^[0-9a-fA-F:]+$', value):
            return 'Invalid AAAA record value (must be IPv6)'
        if rtype == 'CNAME' and not self._validate_domain(value):
            return 'Invalid CNAME target (must be a domain)'
        if rtype == 'MX' and not self._validate_domain(value.split()[-1] if ' ' in value else value):
            return 'Invalid MX target'
        return None

    async def list_zones(self) -> List[Dict[str, Any]]:
        return [asdict(z) for z in self.zones.values()]

    async def create_zone(self, data: Dict[str, Any]) -> Dict[str, Any]:
        domain = data.get('domain', '').lower().rstrip('.')
        if not self._validate_domain(domain):
            raise ValueError(f"Invalid domain name: {domain}")
        if any(z.domain == domain for z in self.zones.values()):
            raise ValueError(f"Zone already exists: {domain}")
        zone_id = str(uuid.uuid4())
        now = datetime.now()
        default_ns = data.get('nameservers', ['ns1.infrapilot.com', 'ns2.infrapilot.com'])
        zone = DNSZone(
            id=zone_id,
            domain=domain,
            type=data.get('type', 'primary'),
            master_servers=data.get('master_servers', []),
            allowed_transfers=data.get('allowed_transfers', []),
            serial=int(now.strftime('%Y%m%d%H%M%S')),
            refresh=data.get('refresh', 3600),
            retry=data.get('retry', 1800),
            expire=data.get('expire', 86400),
            ttl=data.get('ttl', 3600),
            dnssec_status='unsigned',
            dnskey_record='',
            ds_record='',
            soa_record={
                'mname': default_ns[0] if default_ns else 'ns1.infrapilot.com',
                'rname': f'admin.{domain}',
                'serial': int(now.strftime('%Y%m%d%H%M%S')),
                'refresh': 3600,
                'retry': 1800,
                'expire': 86400,
                'minimum_ttl': 3600,
            },
            nameservers=default_ns,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        self.zones[zone.id] = zone
        await self._add_default_records(zone)
        self._save_data()
        return asdict(zone)

    async def _add_default_records(self, zone: DNSZone):
        default_records = [
            {'name': '@', 'type': 'SOA', 'value': f"{zone.soa_record['mname']} {zone.soa_record['rname']} {zone.serial} {zone.refresh} {zone.retry} {zone.expire} {zone.ttl}", 'ttl': zone.ttl},
            {'name': '@', 'type': 'NS', 'value': zone.nameservers[0], 'ttl': zone.ttl},
        ]
        if len(zone.nameservers) > 1:
            default_records.append({'name': '@', 'type': 'NS', 'value': zone.nameservers[1], 'ttl': zone.ttl})
        for rec_data in default_records:
            record = DNSRecord(
                id=str(uuid.uuid4()),
                zone_id=zone.id,
                name=rec_data['name'],
                type=rec_data['type'],
                value=rec_data['value'],
                priority=0,
                weight=0,
                port=0,
                ttl=rec_data.get('ttl', zone.ttl),
                enabled=True,
                notes='Auto-created default record',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            self.records[record.id] = record

    async def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        return asdict(zone) if zone else None

    async def update_zone(self, zone_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        for key in ['refresh', 'retry', 'expire', 'ttl', 'allowed_transfers', 'nameservers', 'dnssec_status']:
            if key in data:
                setattr(zone, key, data[key])
        zone.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(zone)

    async def delete_zone(self, zone_id: str) -> bool:
        if zone_id in self.zones:
            records_to_delete = [rid for rid, r in self.records.items() if r.zone_id == zone_id]
            for rid in records_to_delete:
                del self.records[rid]
            del self.zones[zone_id]
            self._save_data()
            return True
        return False

    async def list_records(self, zone_id: str) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.records.values() if r.zone_id == zone_id]

    async def create_record(self, zone_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        record_type = data.get('type', 'A').upper()
        if record_type not in RECORD_TYPES:
            raise ValueError(f"Unsupported record type: {record_type}")
        name = data.get('name', '@')
        value = data.get('value', '')
        error = self._validate_record(zone, name, record_type, value)
        if error:
            raise ValueError(error)
        record = DNSRecord(
            id=str(uuid.uuid4()),
            zone_id=zone_id,
            name=name,
            type=record_type,
            value=value,
            priority=data.get('priority', 0),
            weight=data.get('weight', 0),
            port=data.get('port', 0),
            ttl=data.get('ttl', zone.ttl),
            enabled=data.get('enabled', True),
            notes=data.get('notes', ''),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self.records[record.id] = record
        zone.serial = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        zone.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(record)

    async def update_record(self, zone_id: str, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record = self.records.get(record_id)
        if not record or record.zone_id != zone_id:
            return None
        for key in ['name', 'type', 'value', 'priority', 'weight', 'port', 'ttl', 'enabled', 'notes']:
            if key in data:
                setattr(record, key, data[key])
        record.updated_at = datetime.now().isoformat()
        zone = self.zones.get(zone_id)
        if zone:
            zone.serial = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        self._save_data()
        return asdict(record)

    async def delete_record(self, zone_id: str, record_id: str) -> bool:
        record = self.records.get(record_id)
        if not record or record.zone_id != zone_id:
            return False
        del self.records[record_id]
        zone = self.zones.get(zone_id)
        if zone:
            zone.serial = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        self._save_data()
        return True

    async def sign_zone_dnssec(self, zone_id: str) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        zone.dnssec_status = 'signing'
        import hashlib
        fake_dnskey = f"{zone.domain} 257 3 13 {hashlib.sha256(f'{zone.domain}-key'.encode()).hexdigest()[:64].upper()}"
        fake_ds = f"{zone.domain} 13 2 {hashlib.sha256(fake_dnskey.encode()).hexdigest()[:64].upper()}"
        zone.dnskey_record = fake_dnskey
        zone.ds_record = fake_ds
        zone.dnssec_status = 'signed'
        zone.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(zone)

    async def get_dnssec_status(self, zone_id: str) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        return {
            'zone_id': zone_id,
            'domain': zone.domain,
            'status': zone.dnssec_status,
            'dnskey_record': zone.dnskey_record,
            'ds_record': zone.ds_record,
            'nameservers': zone.nameservers,
        }

    async def trigger_zone_transfer(self, zone_id: str) -> Optional[Dict[str, Any]]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        zone.serial = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        zone.updated_at = datetime.now().isoformat()
        self._save_data()
        return {
            'zone_id': zone_id,
            'domain': zone.domain,
            'serial': zone.serial,
            'transferred_to': zone.allowed_transfers,
            'status': 'initiated',
        }

    async def export_zone_file(self, zone_id: str) -> Optional[str]:
        zone = self.zones.get(zone_id)
        if not zone:
            return None
        lines = [f"; BIND zone file for {zone.domain}", f"; Generated by Infra Pilot DNS Manager", f"$TTL {zone.ttl}"]
        lines.append(f"@ IN SOA {zone.soa_record['mname']} {zone.soa_record['rname']} ( {zone.serial} {zone.refresh} {zone.retry} {zone.expire} {zone.ttl} )")
        for ns in zone.nameservers:
            lines.append(f"@ IN NS {ns}")
        for record in self.records.values():
            if record.zone_id != zone_id or not record.enabled:
                continue
            rname = record.name if record.name != '@' else '@'
            if record.type in ('SOA', 'NS'):
                continue
            extra = f" {record.priority}" if record.type == 'MX' else ''
            extra += f" {record.weight} {record.port}" if record.type == 'SRV' else ''
            lines.append(f"{rname} {record.ttl} IN {record.type}{extra} {record.value}")
        return '\n'.join(lines) + '\n'
