from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)


class DNSProvider:
    """Abstract DNS provider for health-based failover"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def update_record(self, record_name: str, value: str, ttl: int = 60) -> bool:
        raise NotImplementedError

    async def health_check(self, endpoint: str) -> bool:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as resp:
                    return resp.status < 500
        except Exception:
            return False


class Route53Provider(DNSProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.hosted_zone_id = config.get('route53_zone_id', '')

    async def update_record(self, record_name: str, value: str, ttl: int = 60) -> bool:
        logger.info(f"Route53: updating {record_name} -> {value} (TTL={ttl})")
        return True

    async def health_check(self, endpoint: str) -> bool:
        return await super().health_check(endpoint)


class CloudflareProvider(DNSProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.zone_id = config.get('cloudflare_zone_id', '')
        self.api_token = config.get('cloudflare_api_token', '')

    async def update_record(self, record_name: str, value: str, ttl: int = 60) -> bool:
        logger.info(f"Cloudflare: updating {record_name} -> {value} (TTL={ttl})")
        return True

    async def health_check(self, endpoint: str) -> bool:
        return await super().health_check(endpoint)


class MultiRegionManager:
    """Active-passive region setup with health-based DNS failover"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = config.get('region_config_file', 'data/region_configs.json')
        self.events_file = config.get('failover_events_file', 'data/failover_events.json')
        self.regions: List[Dict[str, Any]] = []
        self.failover_events: List[Dict[str, Any]] = []
        self.dns_provider: Optional[DNSProvider] = None
        self._load_data()
        self._init_dns_provider()

    def _init_dns_provider(self):
        provider_type = self.config.get('dns_provider', 'route53')
        if provider_type == 'cloudflare':
            self.dns_provider = CloudflareProvider(self.config)
        else:
            self.dns_provider = Route53Provider(self.config)

    def _load_data(self):
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.regions = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load region configs: {e}")
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    self.failover_events = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load failover events: {e}")

    def _save_regions(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.regions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save region configs: {e}")

    def _save_events(self):
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.failover_events[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save failover events: {e}")

    async def initialize(self):
        logger.info("MultiRegionManager initialized")

    async def close(self):
        logger.info("MultiRegionManager closed")

    async def create_region(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        region = {
            'id': f"region_{len(self.regions)}_{int(datetime.now().timestamp())}",
            'name': region_data.get('name', ''),
            'endpoint': region_data.get('endpoint', ''),
            'health_endpoint': region_data.get('health_endpoint', ''),
            'role': region_data.get('role', 'passive'),
            'active': region_data.get('role', 'passive') == 'active',
            'status': 'healthy',
            'replication_lag_ms': 0,
            'dns_record': region_data.get('dns_record', ''),
            'created_at': datetime.now().isoformat()
        }
        self.regions.append(region)
        self._save_regions()
        return region

    async def list_regions(self) -> List[Dict[str, Any]]:
        return self.regions

    async def update_region(self, region_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, r in enumerate(self.regions):
            if r['id'] == region_id:
                self.regions[i].update(updates)
                self._save_regions()
                return self.regions[i]
        return None

    async def delete_region(self, region_id: str) -> bool:
        for i, r in enumerate(self.regions):
            if r['id'] == region_id:
                self.regions.pop(i)
                self._save_regions()
                return True
        return False

    async def perform_failover(self, region_id: str) -> Dict[str, Any]:
        target = None
        for r in self.regions:
            if r['id'] == region_id:
                target = r
                break
        if not target:
            return {'error': 'Region not found'}

        active = [r for r in self.regions if r.get('active')]
        if not active:
            target['active'] = True
            target['role'] = 'active'
            self._save_regions()
            event = {
                'id': f"failover_{int(datetime.now().timestamp())}",
                'region_id': region_id,
                'from_region': None,
                'to_region': region_id,
                'reason': 'initial_activation',
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
            self.failover_events.append(event)
            self._save_events()
            return {'success': True, 'event': event}

        current_active = active[0]
        event = {
            'id': f"failover_{int(datetime.now().timestamp())}",
            'region_id': region_id,
            'from_region': current_active['id'],
            'to_region': region_id,
            'reason': 'manual_failover',
            'status': 'in_progress',
            'timestamp': datetime.now().isoformat()
        }
        self.failover_events.append(event)

        success = False
        if self.dns_provider:
            if await self.dns_provider.health_check(target.get('health_endpoint', target['endpoint'])):
                if await self.dns_provider.update_record(target.get('dns_record', ''), target['endpoint']):
                    success = True

        current_active['active'] = False
        current_active['role'] = 'passive'
        target['active'] = True
        target['role'] = 'active'
        self._save_regions()

        event['status'] = 'completed' if success else 'failed'
        event['completed_at'] = datetime.now().isoformat()
        self._save_events()

        return {'success': success, 'event': event}

    async def get_region_status(self, region_id: str) -> Optional[Dict[str, Any]]:
        for r in self.regions:
            if r['id'] == region_id:
                if self.dns_provider:
                    healthy = await self.dns_provider.health_check(r.get('health_endpoint', r['endpoint']))
                    r['status'] = 'healthy' if healthy else 'unhealthy'
                region_events = [e for e in self.failover_events if e.get('region_id') == region_id]
                return {**r, 'failover_history': region_events[-10:]}
        return None
