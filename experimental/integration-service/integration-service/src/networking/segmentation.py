import json
import logging
import os
import uuid
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

COMPLIANCE_FRAMEWORKS = {
    'pci_dss': {
        'description': 'PCI DSS v4.0 - Cardholder data isolation',
        'rules': ['segment_isolation', 'no_public_access_to_cdh', 'encryption_in_transit'],
    },
    'hipaa': {
        'description': 'HIPAA - Health information protection',
        'rules': ['segment_isolation', 'audit_logging', 'encryption_in_transit'],
    },
    'soc2': {
        'description': 'SOC 2 - Security, availability, processing integrity',
        'rules': ['segment_isolation', 'access_controls', 'monitoring'],
    },
}

@dataclass
class NetworkSegment:
    id: str
    name: str
    description: str
    vlan_id: int
    cidr: str
    gateway: str
    netmask: str
    segment_type: str
    color: str
    tags: List[str]
    parent_segment_id: str
    dhcp_range_start: str
    dhcp_range_end: str
    created_at: str

@dataclass
class TopologyNode:
    id: str
    segment_id: str
    type: str
    label: str
    position_x: float
    position_y: float
    config: Dict[str, Any]

@dataclass
class TopologyEdge:
    id: str
    source_node: str
    target_node: str
    type: str
    firewall_rules: List[Dict[str, Any]]
    bandwidth: int
    latency: float

@dataclass
class FirewallRule:
    id: str
    segment_pair_id: str
    direction: str
    protocol: str
    source_cidr: str
    dest_cidr: str
    port_range: str
    action: str
    log: bool
    description: str

@dataclass
class IPReservation:
    id: str
    segment_id: str
    ip_address: str
    hostname: str
    mac_address: str
    description: str
    reserved_by: str
    created_at: str

class NetworkSegmentationManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.segments_file = os.path.join(self.data_path, 'segments.json')
        self.nodes_file = os.path.join(self.data_path, 'topology_nodes.json')
        self.edges_file = os.path.join(self.data_path, 'topology_edges.json')
        self.rules_file = os.path.join(self.data_path, 'firewall_rules.json')
        self.ipam_file = os.path.join(self.data_path, 'ipam.json')
        self.segments: Dict[str, NetworkSegment] = {}
        self.nodes: Dict[str, TopologyNode] = {}
        self.edges: Dict[str, TopologyEdge] = {}
        self.rules: Dict[str, FirewallRule] = {}
        self.ipam: Dict[str, IPReservation] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.segments_file, 'segments', NetworkSegment),
            (self.nodes_file, 'nodes', TopologyNode),
            (self.edges_file, 'edges', TopologyEdge),
            (self.rules_file, 'rules', FirewallRule),
            (self.ipam_file, 'ipam', IPReservation),
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
            (self.segments_file, 'segments'),
            (self.nodes_file, 'nodes'),
            (self.edges_file, 'edges'),
            (self.rules_file, 'rules'),
            (self.ipam_file, 'ipam'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("NetworkSegmentationManager initialized")

    async def close(self):
        self._save_data()

    def _cidr_to_netmask(self, prefix: str) -> str:
        try:
            cidr = int(prefix.split('/')[1])
            mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
            return '.'.join([str((mask >> (8 * i)) & 0xFF) for i in range(3, -1, -1)])
        except:
            return '255.255.255.0'

    def _cidr_to_gateway(self, cidr: str) -> str:
        try:
            ip = cidr.split('/')[0]
            parts = ip.split('.')
            parts[3] = '1'
            return '.'.join(parts)
        except:
            return cidr.split('/')[0]

    async def list_segments(self) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.segments.values()]

    async def create_segment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cidr = data['cidr']
        seg_id = str(uuid.uuid4())
        segment = NetworkSegment(
            id=seg_id,
            name=data['name'],
            description=data.get('description', ''),
            vlan_id=data.get('vlan_id', len(self.segments) + 1),
            cidr=cidr,
            gateway=self._cidr_to_gateway(cidr),
            netmask=self._cidr_to_netmask(cidr),
            segment_type=data.get('segment_type', 'private'),
            color=data.get('color', '#3498db'),
            tags=data.get('tags', []),
            parent_segment_id=data.get('parent_segment_id', ''),
            dhcp_range_start=data.get('dhcp_range_start', ''),
            dhcp_range_end=data.get('dhcp_range_end', ''),
            created_at=datetime.now().isoformat(),
        )
        self.segments[segment.id] = segment
        self._save_data()
        return asdict(segment)

    async def get_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        seg = self.segments.get(segment_id)
        return asdict(seg) if seg else None

    async def update_segment(self, segment_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        seg = self.segments.get(segment_id)
        if not seg:
            return None
        for key in ['name', 'description', 'vlan_id', 'cidr', 'gateway', 'netmask', 'segment_type', 'color', 'tags', 'parent_segment_id', 'dhcp_range_start', 'dhcp_range_end']:
            if key in data:
                setattr(seg, key, data[key])
        self._save_data()
        return asdict(seg)

    async def delete_segment(self, segment_id: str) -> bool:
        if segment_id in self.segments:
            nodes_to_del = [nid for nid, n in self.nodes.items() if n.segment_id == segment_id]
            for nid in nodes_to_del:
                del self.nodes[nid]
            edges_to_del = [eid for eid, e in self.edges.items() if e.source_node in nodes_to_del or e.target_node in nodes_to_del]
            for eid in edges_to_del:
                del self.edges[eid]
            ipam_to_del = [iid for iid, i in self.ipam.items() if i.segment_id == segment_id]
            for iid in ipam_to_del:
                del self.ipam[iid]
            del self.segments[segment_id]
            self._save_data()
            return True
        return False

    async def get_topology(self, segment_id: str) -> Dict[str, Any]:
        seg_nodes = [n for n in self.nodes.values() if n.segment_id == segment_id]
        node_ids = set(n.id for n in seg_nodes)
        seg_edges = [e for e in self.edges.values() if e.source_node in node_ids or e.target_node in node_ids]
        return {
            'segment_id': segment_id,
            'nodes': [asdict(n) for n in seg_nodes],
            'edges': [asdict(e) for e in seg_edges],
        }

    async def update_topology(self, segment_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        new_nodes = data.get('nodes', [])
        new_edges = data.get('edges', [])
        nodes_to_del = [nid for nid, n in self.nodes.items() if n.segment_id == segment_id]
        for nid in nodes_to_del:
            del self.nodes[nid]
        edges_to_del = [eid for eid, e in self.edges.items() if e.source_node in nodes_to_del or e.target_node in nodes_to_del]
        for eid in edges_to_del:
            del self.edges[eid]
        for ndata in new_nodes:
            node = TopologyNode(
                id=ndata.get('id', str(uuid.uuid4())),
                segment_id=segment_id,
                type=ndata.get('type', 'segment'),
                label=ndata.get('label', ''),
                position_x=ndata.get('position_x', 0),
                position_y=ndata.get('position_y', 0),
                config=ndata.get('config', {}),
            )
            self.nodes[node.id] = node
        for edata in new_edges:
            edge = TopologyEdge(
                id=edata.get('id', str(uuid.uuid4())),
                source_node=edata.get('source_node', ''),
                target_node=edata.get('target_node', ''),
                type=edata.get('type', 'trunk'),
                firewall_rules=edata.get('firewall_rules', []),
                bandwidth=edata.get('bandwidth', 1000),
                latency=edata.get('latency', 1.0),
            )
            self.edges[edge.id] = edge
        self._save_data()
        return await self.get_topology(segment_id)

    async def connect_segments(self, seg_a_id: str, seg_b_id: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        seg_a = self.segments.get(seg_a_id)
        seg_b = self.segments.get(seg_b_id)
        if not seg_a or not seg_b:
            return {'error': 'One or both segments not found'}
        edge = TopologyEdge(
            id=str(uuid.uuid4()),
            source_node='', target_node='',
            type='routed',
            firewall_rules=rules,
            bandwidth=1000,
            latency=1.0,
        )
        self.edges[edge.id] = edge
        for rule_data in rules:
            rule = FirewallRule(
                id=str(uuid.uuid4()),
                segment_pair_id=edge.id,
                direction=rule_data.get('direction', 'ingress'),
                protocol=rule_data.get('protocol', 'any'),
                source_cidr=rule_data.get('source_cidr', seg_a.cidr),
                dest_cidr=rule_data.get('dest_cidr', seg_b.cidr),
                port_range=rule_data.get('port_range', 'any'),
                action=rule_data.get('action', 'allow'),
                log=rule_data.get('log', False),
                description=rule_data.get('description', ''),
            )
            self.rules[rule.id] = rule
        self._save_data()
        return {'seg_a': asdict(seg_a), 'seg_b': asdict(seg_b), 'edge': asdict(edge), 'rules': [asdict(r) for r in self.rules.values() if r.segment_pair_id == edge.id]}

    async def disconnect_segments(self, seg_a_id: str, seg_b_id: str) -> bool:
        seg_a = self.segments.get(seg_a_id)
        seg_b = self.segments.get(seg_b_id)
        if not seg_a or not seg_b:
            return False
        rules_to_del = [rid for rid, r in self.rules.items() if (r.source_cidr == seg_a.cidr and r.dest_cidr == seg_b.cidr) or (r.source_cidr == seg_b.cidr and r.dest_cidr == seg_a.cidr)]
        for rid in rules_to_del:
            del self.rules[rid]
        self._save_data()
        return True

    async def get_firewall_rules(self, segment_id: str) -> List[Dict[str, Any]]:
        seg = self.segments.get(segment_id)
        if not seg:
            return []
        relevant = [r for r in self.rules.values() if r.source_cidr == seg.cidr or r.dest_cidr == seg.cidr]
        return [asdict(r) for r in relevant]

    async def check_compliance(self, segment_id: str, framework: str) -> Dict[str, Any]:
        seg = self.segments.get(segment_id)
        if not seg:
            return {'error': 'Segment not found'}
        fw_info = COMPLIANCE_FRAMEWORKS.get(framework)
        if not fw_info:
            return {'error': f'Unknown framework: {framework}. Known: {list(COMPLIANCE_FRAMEWORKS.keys())}'}
        results = {}
        all_pass = True
        if 'segment_isolation' in fw_info['rules']:
            isolated = seg.segment_type in ('dmz', 'pci', 'iot')
            results['segment_isolation'] = isolated
            all_pass = all_pass and isolated
        if 'encryption_in_transit' in fw_info['rules']:
            has_encryption = any(getattr(r, 'protocol', 'any') in ('tls', 'ipsec', 'ssh') for r in self.rules.values())
            results['encryption_in_transit'] = has_encryption
            all_pass = all_pass and has_encryption
        if 'audit_logging' in fw_info['rules']:
            results['audit_logging'] = True
        if 'no_public_access_to_cdh' in fw_info['rules']:
            results['no_public_access_to_cdh'] = seg.segment_type != 'public' or seg.name.lower().find('cdh') < 0
            all_pass = all_pass and results['no_public_access_to_cdh']
        return {
            'segment_id': segment_id,
            'framework': framework,
            'framework_description': fw_info['description'],
            'results': results,
            'compliant': all_pass,
            'checked_at': datetime.now().isoformat(),
        }

    async def list_ipam(self, segment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if segment_id:
            return [asdict(i) for i in self.ipam.values() if i.segment_id == segment_id]
        return [asdict(i) for i in self.ipam.values()]

    async def reserve_ip(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        seg = self.segments.get(data.get('segment_id', ''))
        if not seg:
            return None
        ip = data.get('ip_address', '')
        if not ip:
            base_ip = '.'.join(seg.cidr.split('/')[0].split('.')[:3])
            used_ips = set(i.ip_address for i in self.ipam.values() if i.segment_id == seg.id)
            for last_octet in range(2, 254):
                candidate = f'{base_ip}.{last_octet}'
                if candidate not in used_ips:
                    ip = candidate
                    break
            if not ip:
                return None
        reservation = IPReservation(
            id=str(uuid.uuid4()),
            segment_id=seg.id,
            ip_address=ip,
            hostname=data.get('hostname', ''),
            mac_address=data.get('mac_address', ''),
            description=data.get('description', ''),
            reserved_by=data.get('reserved_by', 'system'),
            created_at=datetime.now().isoformat(),
        )
        self.ipam[reservation.id] = reservation
        self._save_data()
        return asdict(reservation)

    async def get_usage_stats(self) -> Dict[str, Any]:
        total_ips = 0
        used_ips = len(self.ipam)
        segment_stats = []
        for seg in self.segments.values():
            try:
                prefix_len = int(seg.cidr.split('/')[1])
                seg_ips = 2 ** (32 - prefix_len) - 2
                seg_used = sum(1 for i in self.ipam.values() if i.segment_id == seg.id)
                total_ips += seg_ips
                segment_stats.append({
                    'id': seg.id,
                    'name': seg.name,
                    'cidr': seg.cidr,
                    'total_ips': seg_ips,
                    'used_ips': seg_used,
                    'utilization_pct': round(seg_used / seg_ips * 100, 2) if seg_ips > 0 else 0,
                })
            except:
                segment_stats.append({'id': seg.id, 'name': seg.name, 'error': 'Invalid CIDR'})
        return {
            'total_segments': len(self.segments),
            'total_ip_capacity': total_ips,
            'total_reserved_ips': used_ips,
            'overall_utilization_pct': round(used_ips / total_ips * 100, 2) if total_ips > 0 else 0,
            'segments': segment_stats,
        }
