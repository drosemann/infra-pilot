import asyncio
import json
import logging
import os
import time
import math
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class Uplink:
    id: str
    name: str
    type: str
    provider: str
    bandwidth_up_mbps: int
    bandwidth_down_mbps: int
    status: str
    ip_address: str
    gateway: str
    latency_ms: float
    packet_loss_pct: float
    jitter_ms: float
    cost_per_gb: float
    monthly_cap_gb: int
    priority: int
    is_active: bool
    last_checked: str
    metrics_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class FailoverPolicy:
    id: str
    name: str
    uplink_ids: List[str]
    condition_type: str
    threshold_ms: float
    threshold_loss_pct: float
    fallback_uplink_id: str
    auto_revert: bool
    revert_after_seconds: int
    enabled: bool

@dataclass
class QoSPolicy:
    id: str
    name: str
    application: str
    protocol: str
    port_range: str
    dscp_tag: int
    bandwidth_limit_kbps: int
    priority_queue: str
    uplink_affinity: str

@dataclass
class SteeringRule:
    id: str
    name: str
    source_ip: str
    destination_ip: str
    app_id: str
    uplink_id: str
    policy_id: str
    enabled: bool

class SDWANControllerManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.uplinks_file = os.path.join(self.data_path, 'sdwan_uplinks.json')
        self.policies_file = os.path.join(self.data_path, 'sdwan_policies.json')
        self.qos_file = os.path.join(self.data_path, 'sdwan_qos.json')
        self.steering_file = os.path.join(self.data_path, 'sdwan_steering.json')
        self.uplinks: Dict[str, Uplink] = {}
        self.policies: Dict[str, FailoverPolicy] = {}
        self.qos_policies: Dict[str, QoSPolicy] = {}
        self.steering_rules: Dict[str, SteeringRule] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.uplinks_file, 'uplinks', Uplink),
            (self.policies_file, 'policies', FailoverPolicy),
            (self.qos_file, 'qos_policies', QoSPolicy),
            (self.steering_file, 'steering_rules', SteeringRule),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        obj = cls(**item)
                        storage[obj.id] = obj
            except Exception as e:
                logger.warning(f"Failed to load {attr}: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.uplinks_file, 'uplinks'),
            (self.policies_file, 'policies'),
            (self.qos_file, 'qos_policies'),
            (self.steering_file, 'steering_rules'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("SDWANControllerManager initialized")

    async def close(self):
        if self._monitor_task:
            self._monitor_task.cancel()
        self._save_data()

    async def get_status(self) -> Dict[str, Any]:
        active_links = sum(1 for u in self.uplinks.values() if u.status == 'active')
        degraded_links = sum(1 for u in self.uplinks.values() if u.status == 'degraded')
        down_links = sum(1 for u in self.uplinks.values() if u.status == 'down')
        return {
            'total_uplinks': len(self.uplinks),
            'active_uplinks': active_links,
            'degraded_uplinks': degraded_links,
            'down_uplinks': down_links,
            'active_policies': sum(1 for p in self.policies.values() if p.enabled),
            'active_qos_policies': len(self.qos_policies),
            'active_steering_rules': sum(1 for r in self.steering_rules.values() if r.enabled),
            'overall_status': 'healthy' if active_links > 0 else 'critical',
            'timestamp': datetime.now().isoformat(),
        }

    async def list_uplinks(self) -> List[Dict[str, Any]]:
        return [asdict(u) for u in self.uplinks.values()]

    async def create_uplink(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import uuid
        uplink = Uplink(
            id=str(uuid.uuid4()),
            name=data['name'],
            type=data.get('type', 'fiber'),
            provider=data.get('provider', ''),
            bandwidth_up_mbps=data.get('bandwidth_up_mbps', 100),
            bandwidth_down_mbps=data.get('bandwidth_down_mbps', 100),
            status='active',
            ip_address=data.get('ip_address', ''),
            gateway=data.get('gateway', ''),
            latency_ms=data.get('latency_ms', 0.0),
            packet_loss_pct=data.get('packet_loss_pct', 0.0),
            jitter_ms=data.get('jitter_ms', 0.0),
            cost_per_gb=data.get('cost_per_gb', 0.0),
            monthly_cap_gb=data.get('monthly_cap_gb', 0),
            priority=data.get('priority', 10),
            is_active=True,
            last_checked=datetime.now().isoformat(),
        )
        self.uplinks[uplink.id] = uplink
        self._save_data()
        return asdict(uplink)

    async def update_uplink(self, uplink_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        uplink = self.uplinks.get(uplink_id)
        if not uplink:
            return None
        for key, value in data.items():
            if hasattr(uplink, key):
                setattr(uplink, key, value)
        uplink.last_checked = datetime.now().isoformat()
        self._save_data()
        return asdict(uplink)

    async def delete_uplink(self, uplink_id: str) -> bool:
        if uplink_id in self.uplinks:
            del self.uplinks[uplink_id]
            self._save_data()
            return True
        return False

    async def list_failover_policies(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.policies.values()]

    async def create_failover_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import uuid
        policy = FailoverPolicy(
            id=str(uuid.uuid4()),
            name=data['name'],
            uplink_ids=data.get('uplink_ids', []),
            condition_type=data.get('condition_type', 'latency'),
            threshold_ms=data.get('threshold_ms', 100.0),
            threshold_loss_pct=data.get('threshold_loss_pct', 5.0),
            fallback_uplink_id=data.get('fallback_uplink_id', ''),
            auto_revert=data.get('auto_revert', True),
            revert_after_seconds=data.get('revert_after_seconds', 300),
            enabled=data.get('enabled', True),
        )
        self.policies[policy.id] = policy
        self._save_data()
        return asdict(policy)

    async def delete_failover_policy(self, policy_id: str) -> bool:
        if policy_id in self.policies:
            del self.policies[policy_id]
            self._save_data()
            return True
        return False

    async def test_failover(self, policy_id: str) -> Dict[str, Any]:
        policy = self.policies.get(policy_id)
        if not policy:
            return {'error': 'Policy not found'}
        if not policy.enabled:
            return {'error': 'Policy is disabled'}
        results = []
        for uplink_id in policy.uplink_ids:
            uplink = self.uplinks.get(uplink_id)
            if not uplink:
                continue
            simulated_latency = uplink.latency_ms + (time.time() % 50)
            simulated_loss = uplink.packet_loss_pct + (time.time() % 3)
            triggered = False
            if policy.condition_type == 'latency' and simulated_latency > policy.threshold_ms:
                triggered = True
            elif policy.condition_type == 'packet_loss' and simulated_loss > policy.threshold_loss_pct:
                triggered = True
            results.append({
                'uplink_id': uplink_id,
                'uplink_name': uplink.name,
                'simulated_latency_ms': round(simulated_latency, 2),
                'simulated_loss_pct': round(simulated_loss, 2),
                'threshold_latency_ms': policy.threshold_ms,
                'threshold_loss_pct': policy.threshold_loss_pct,
                'triggered': triggered,
            })
        fallback = self.uplinks.get(policy.fallback_uplink_id)
        return {
            'policy_id': policy_id,
            'policy_name': policy.name,
            'results': results,
            'fallback_uplink': fallback.name if fallback else 'N/A',
            'simulated_failover_action': 'All matching uplinks would fail over' if any(r['triggered'] for r in results) else 'No failover needed',
            'timestamp': datetime.now().isoformat(),
        }

    async def list_qos_policies(self) -> List[Dict[str, Any]]:
        return [asdict(q) for q in self.qos_policies.values()]

    async def create_qos_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import uuid
        policy = QoSPolicy(
            id=str(uuid.uuid4()),
            name=data['name'],
            application=data.get('application', ''),
            protocol=data.get('protocol', 'any'),
            port_range=data.get('port_range', ''),
            dscp_tag=data.get('dscp_tag', 0),
            bandwidth_limit_kbps=data.get('bandwidth_limit_kbps', 0),
            priority_queue=data.get('priority_queue', 'best_effort'),
            uplink_affinity=data.get('uplink_affinity', ''),
        )
        self.qos_policies[policy.id] = policy
        self._save_data()
        return asdict(policy)

    async def list_steering_rules(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.steering_rules.values()]

    async def create_steering_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import uuid
        rule = SteeringRule(
            id=str(uuid.uuid4()),
            name=data['name'],
            source_ip=data.get('source_ip', ''),
            destination_ip=data.get('destination_ip', ''),
            app_id=data.get('app_id', ''),
            uplink_id=data.get('uplink_id', ''),
            policy_id=data.get('policy_id', ''),
            enabled=data.get('enabled', True),
        )
        self.steering_rules[rule.id] = rule
        self._save_data()
        return asdict(rule)

    async def get_metrics(self) -> Dict[str, Any]:
        uplink_metrics = []
        for uplink in self.uplinks.values():
            uplink_metrics.append({
                'id': uplink.id,
                'name': uplink.name,
                'latency_ms': uplink.latency_ms,
                'packet_loss_pct': uplink.packet_loss_pct,
                'jitter_ms': uplink.jitter_ms,
                'status': uplink.status,
                'bandwidth_up_mbps': uplink.bandwidth_up_mbps,
                'bandwidth_down_mbps': uplink.bandwidth_down_mbps,
            })
        return {
            'uplinks': uplink_metrics,
            'timestamp': datetime.now().isoformat(),
            'aggregate': {
                'avg_latency_ms': round(sum(u.latency_ms for u in self.uplinks.values()) / max(len(self.uplinks), 1), 2),
                'avg_loss_pct': round(sum(u.packet_loss_pct for u in self.uplinks.values()) / max(len(self.uplinks), 1), 2),
                'total_bandwidth_up_mbps': sum(u.bandwidth_up_mbps for u in self.uplinks.values()),
                'total_bandwidth_down_mbps': sum(u.bandwidth_down_mbps for u in self.uplinks.values()),
            }
        }

    async def simulate_uplink_failure(self, uplink_id: str) -> Dict[str, Any]:
        uplink = self.uplinks.get(uplink_id)
        if not uplink:
            return {'error': 'Uplink not found'}
        uplink.status = 'down'
        uplink.latency_ms = 9999
        uplink.packet_loss_pct = 100
        uplink.is_active = False
        self._save_data()
        # Check failover policies
        triggered_policies = []
        for pid, policy in self.policies.items():
            if uplink_id in policy.uplink_ids and policy.enabled:
                triggered_policies.append({
                    'policy_id': pid,
                    'policy_name': policy.name,
                    'fallback_uplink_id': policy.fallback_uplink_id,
                })
        return {
            'uplink_id': uplink_id,
            'uplink_name': uplink.name,
            'new_status': 'down',
            'failover_policies_triggered': triggered_policies,
            'timestamp': datetime.now().isoformat(),
        }

    async def recover_uplink(self, uplink_id: str) -> Dict[str, Any]:
        uplink = self.uplinks.get(uplink_id)
        if not uplink:
            return {'error': 'Uplink not found'}
        uplink.status = 'active'
        uplink.latency_ms = max(1, uplink.latency_ms / 10)
        uplink.packet_loss_pct = max(0.01, uplink.packet_loss_pct / 10)
        uplink.is_active = True
        self._save_data()
        return {
            'uplink_id': uplink_id,
            'uplink_name': uplink.name,
            'new_status': 'active',
            'timestamp': datetime.now().isoformat(),
        }
