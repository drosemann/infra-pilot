import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedResourceTracker:
    """Resource Coordination - Unified resource tracking with cost, trends, forecasting"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8000')
        self.dashboard_url = config.get('dashboard_url', 'http://localhost:5173')
        self.history_file = config.get('resource_history_file', 'resource_history.json')
        self.history: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load resource history: {e}")

    def _save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save resource history: {e}")

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("UnifiedResourceTracker initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def get_all_resources(self) -> Dict[str, Any]:
        resources = {'timestamp': datetime.now().isoformat(), 'total': {'servers': 0, 'cpu_cores': 0, 'memory_mb': 0, 'storage_gb': 0}, 'by_service': {}}
        services = {'service_core': self.service_core_url, 'orchestrator': self.orchestrator_url, 'dashboard': self.dashboard_url}
        for service_name, base_url in services.items():
            try:
                async with self.session.get(f"{base_url}/api/resources") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        resources['by_service'][service_name] = data
                        resources['total']['servers'] += data.get('servers', 0)
                        resources['total']['cpu_cores'] += data.get('cpu_cores', 0)
                        resources['total']['memory_mb'] += data.get('memory_mb', 0)
                        resources['total']['storage_gb'] += data.get('storage_gb', 0)
            except Exception as e:
                logger.warning(f"Failed to get {service_name} resources: {e}")
        self.history.append({'timestamp': resources['timestamp'], 'total': resources['total']})
        self._save_history()
        return resources

    async def allocate_resource(self, service: str, resource_type: str, amount: int) -> Dict[str, Any]:
        resources = await self.get_all_resources()
        available = resources['total'].get(resource_type, 0)
        if available >= amount:
            return {'allocated': True, 'service': service, 'resource': resource_type, 'amount': amount}
        return {'allocated': False, 'reason': f'Insufficient {resource_type}. Available: {available}, Requested: {amount}'}

    async def get_resource_usage(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        usage = {'users': {}}
        services = {'service_core': f"{self.service_core_url}/api/usage", 'orchestrator': f"{self.orchestrator_url}/api/usage"}
        for service_name, endpoint in services.items():
            try:
                url = endpoint if not user_id else f"{endpoint}/{user_id}"
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        usage['users'][service_name] = await resp.json()
            except Exception as e:
                logger.warning(f"Failed to get {service_name} usage: {e}")
        return usage

    async def get_cost_allocation(self, period_start: str, period_end: str) -> Dict[str, Any]:
        resources = await self.get_all_resources()
        cost_per_cpu_hour = self.config.get('cost_per_cpu_hour', 0.01)
        cost_per_mb_hour = self.config.get('cost_per_mb_hour', 0.0001)
        cost_per_gb_month = self.config.get('cost_per_gb_month', 0.10)
        total_cpu = resources['total']['cpu_cores']
        total_memory = resources['total']['memory_mb']
        total_storage = resources['total']['storage_gb']
        return {
            'period': {'start': period_start, 'end': period_end},
            'cpu_cost_estimate': total_cpu * cost_per_cpu_hour * 730,
            'memory_cost_estimate': total_memory * cost_per_mb_hour * 730,
            'storage_cost_estimate': total_storage * cost_per_gb_month,
            'total_estimated_cost': total_cpu * cost_per_cpu_hour * 730 + total_memory * cost_per_mb_hour * 730 + total_storage * cost_per_gb_month,
            'by_service': resources['by_service']
        }

    async def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [h for h in self.history if datetime.fromisoformat(h['timestamp']) >= cutoff]
        if not relevant:
            return {'error': 'Insufficient historical data', 'days': days}
        first = relevant[0]['total']
        last = relevant[-1]['total']
        trends = {}
        for key in first:
            if isinstance(first[key], (int, float)) and isinstance(last[key], (int, float)):
                diff = last[key] - first[key]
                pct = (diff / first[key] * 100) if first[key] != 0 else 0
                trends[key] = {'start': first[key], 'end': last[key], 'change': diff, 'percent_change': round(pct, 2)}
        return {'days': days, 'data_points': len(relevant), 'trends': trends}

    async def get_forecast(self, days_ahead: int = 30) -> Dict[str, Any]:
        if len(self.history) < 2:
            return {'error': 'Insufficient data for forecasting', 'days_ahead': days_ahead}
        recent = self.history[-min(30, len(self.history)):]
        forecasts = {}
        for key in ['cpu_cores', 'memory_mb', 'storage_gb']:
            values = [h['total'].get(key, 0) for h in recent]
            if len(values) >= 2:
                avg_change = sum(values[i] - values[i-1] for i in range(1, len(values))) / len(values)
                forecasted = values[-1] + avg_change * days_ahead
                forecasts[key] = {'current': values[-1], 'forecasted': round(max(0, forecasted), 1), 'daily_avg_change': round(avg_change, 2)}
        return {'days_ahead': days_ahead, 'forecast': forecasts}


class SharedResourcePoolManager:
    """Shared resource pools - Pool CPU/RAM/storage across VPS with fair scheduling"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pools_file = config.get('resource_pools_file', 'resource_pools.json')
        self.pools: Dict[str, Dict[str, Any]] = {}
        self._load_pools()

    def _load_pools(self):
        if os.path.exists(self.pools_file):
            try:
                with open(self.pools_file, 'r') as f:
                    self.pools = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load pools: {e}")

    def _save_pools(self):
        try:
            with open(self.pools_file, 'w') as f:
                json.dump(self.pools, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pools: {e}")

    async def create_pool(self, name: str, cpu_cores: int, memory_mb: int, storage_gb: int) -> Dict[str, Any]:
        self.pools[name] = {
            'name': name,
            'total': {'cpu_cores': cpu_cores, 'memory_mb': memory_mb, 'storage_gb': storage_gb},
            'allocated': {'cpu_cores': 0, 'memory_mb': 0, 'storage_gb': 0},
            'services': [],
            'created_at': datetime.now().isoformat()
        }
        self._save_pools()
        return self.pools[name]

    async def get_pools(self) -> Dict[str, Any]:
        return self.pools

    async def allocate_from_pool(self, pool_name: str, service: str, cpu_cores: int = 0, memory_mb: int = 0, storage_gb: int = 0) -> Dict[str, Any]:
        pool = self.pools.get(pool_name)
        if not pool:
            return {'success': False, 'error': f'Pool {pool_name} not found'}
        available = {
            'cpu_cores': pool['total']['cpu_cores'] - pool['allocated']['cpu_cores'],
            'memory_mb': pool['total']['memory_mb'] - pool['allocated']['memory_mb'],
            'storage_gb': pool['total']['storage_gb'] - pool['allocated']['storage_gb']
        }
        if cpu_cores > available['cpu_cores'] or memory_mb > available['memory_mb'] or storage_gb > available['storage_gb']:
            return {'success': False, 'error': f'Insufficient pool resources. Available: {available}', 'available': available}
        pool['allocated']['cpu_cores'] += cpu_cores
        pool['allocated']['memory_mb'] += memory_mb
        pool['allocated']['storage_gb'] += storage_gb
        if service not in pool['services']:
            pool['services'].append(service)
        self._save_pools()
        return {'success': True, 'pool': pool_name, 'service': service, 'allocated': {'cpu_cores': cpu_cores, 'memory_mb': memory_mb, 'storage_gb': storage_gb}}

    async def release_from_pool(self, pool_name: str, service: str, cpu_cores: int = 0, memory_mb: int = 0, storage_gb: int = 0) -> bool:
        pool = self.pools.get(pool_name)
        if not pool:
            return False
        pool['allocated']['cpu_cores'] = max(0, pool['allocated']['cpu_cores'] - cpu_cores)
        pool['allocated']['memory_mb'] = max(0, pool['allocated']['memory_mb'] - memory_mb)
        pool['allocated']['storage_gb'] = max(0, pool['allocated']['storage_gb'] - storage_gb)
        self._save_pools()
        return True


class ResourceSynchronizer:
    """Resource synchronization - sync allocations across services, propagate pool updates"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8000')
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def sync_allocations(self, allocations: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for service, url in [('service_core', self.service_core_url), ('orchestrator', self.orchestrator_url)]:
            try:
                async with self.session.post(f"{url}/api/resources/allocate", json=allocations) as resp:
                    results[service] = resp.status == 200
            except Exception as e:
                logger.warning(f"Sync to {service} failed: {e}")
                results[service] = False
        return results

    async def propagate_pool_update(self, pool_name: str, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for service, url in [('service_core', self.service_core_url), ('orchestrator', self.orchestrator_url)]:
            try:
                async with self.session.post(f"{url}/api/resources/pools", json={'name': pool_name, **pool_data}) as resp:
                    results[service] = resp.status == 200
            except Exception as e:
                logger.warning(f"Pool propagation to {service} failed: {e}")
                results[service] = False
        return results


class ResourceAllocationManager:
    """Resource allocation management - unified view, rebalance suggestions"""

    def __init__(self, config: Dict[str, Any], tracker: UnifiedResourceTracker):
        self.config = config
        self.tracker = tracker

    async def get_allocation_vs_usage(self) -> Dict[str, Any]:
        resources = await self.tracker.get_all_resources()
        usage = await self.tracker.get_resource_usage()
        allocation = resources['total']
        comparison = {}
        for resource_type in ['cpu_cores', 'memory_mb', 'storage_gb']:
            allocated = allocation.get(resource_type, 0)
            used = 0
            for svc_data in usage.get('users', {}).values():
                if isinstance(svc_data, dict):
                    used += svc_data.get(resource_type, 0) or svc_data.get(resource_type.replace('_', '_'), 0)
            comparison[resource_type] = {'allocated': allocated, 'used': used, 'utilization': round(used / allocated * 100, 2) if allocated > 0 else 0}
        return {'comparison': comparison, 'by_service': resources['by_service']}

    async def get_rebalance_suggestions(self) -> List[Dict[str, Any]]:
        avu = await self.get_allocation_vs_usage()
        suggestions = []
        for resource_type, data in avu.get('comparison', {}).items():
            util = data.get('utilization', 0)
            if util > 90:
                suggestions.append({'type': 'scale_up', 'resource': resource_type, 'reason': f'Utilization at {util}% - consider increasing allocation'})
            elif util < 30:
                suggestions.append({'type': 'scale_down', 'resource': resource_type, 'reason': f'Utilization at {util}% - consider reducing allocation'})
        return suggestions

    async def get_unified_view(self) -> Dict[str, Any]:
        resources = await self.tracker.get_all_resources()
        avu = await self.get_allocation_vs_usage()
        suggestions = await self.get_rebalance_suggestions()
        return {'resources': resources, 'allocation_vs_usage': avu, 'suggestions': suggestions}


class ResourceSchedulingCoordinator:
    """Resource scheduling coordination - maintenance, backups, scaling, conflict detection"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schedule_file = config.get('schedule_file', 'resource_schedule.json')
        self.schedule: List[Dict[str, Any]] = []
        self._load_schedule()

    def _load_schedule(self):
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r') as f:
                    self.schedule = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load schedule: {e}")

    def _save_schedule(self):
        try:
            with open(self.schedule_file, 'w') as f:
                json.dump(self.schedule[-500:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save schedule: {e}")

    async def add_event(self, event_type: str, service: str, scheduled_at: str, duration_minutes: int, description: str = '') -> Dict[str, Any]:
        event = {
            'id': f'sched_{len(self.schedule)}_{int(datetime.now().timestamp())}',
            'event_type': event_type,
            'service': service,
            'scheduled_at': scheduled_at,
            'duration_minutes': duration_minutes,
            'description': description,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat()
        }
        conflicts = await self.detect_conflicts(event)
        if conflicts:
            event['conflicts'] = conflicts
        self.schedule.append(event)
        self._save_schedule()
        return event

    async def detect_conflicts(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        conflicts = []
        event_time = datetime.fromisoformat(event['scheduled_at'])
        event_end = event_time + timedelta(minutes=event.get('duration_minutes', 60))
        for existing in self.schedule:
            if existing.get('status') != 'scheduled':
                continue
            existing_time = datetime.fromisoformat(existing['scheduled_at'])
            existing_end = existing_time + timedelta(minutes=existing.get('duration_minutes', 60))
            if event_time < existing_end and event_end > existing_time:
                if existing['service'] == event['service']:
                    conflicts.append({'conflict_with': existing['id'], 'type': existing['event_type'], 'service': existing['service'], 'scheduled_at': existing['scheduled_at']})
        return conflicts

    async def get_schedule(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        if service:
            return [e for e in self.schedule if e.get('service') == service]
        return self.schedule


class ResourceOptimizationCoordinator:
    """Resource optimization coordination - cross-service optimization, idle resource identification"""

    def __init__(self, config: Dict[str, Any], tracker: UnifiedResourceTracker):
        self.config = config
        self.tracker = tracker

    async def analyze_optimization(self) -> Dict[str, Any]:
        resources = await self.tracker.get_all_resources()
        idle_resources = await self._identify_idle_resources(resources)
        recommendations = await self._generate_recommendations(resources, idle_resources)
        return {'idle_resources': idle_resources, 'recommendations': recommendations, 'timestamp': datetime.now().isoformat()}

    async def _identify_idle_resources(self, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        idle = []
        for service, data in resources.get('by_service', {}).items():
            if isinstance(data, dict):
                cpu = data.get('cpu_percent', 100)
                memory = data.get('memory_percent', 100)
                if cpu < 10:
                    idle.append({'service': service, 'resource': 'cpu', 'usage_percent': cpu, 'severity': 'high' if cpu < 5 else 'medium'})
                if memory < 10:
                    idle.append({'service': service, 'resource': 'memory', 'usage_percent': memory, 'severity': 'high' if memory < 5 else 'medium'})
        return idle

    async def _generate_recommendations(self, resources: Dict[str, Any], idle: List[Dict[str, Any]]) -> List[str]:
        recs = []
        if idle:
            recs.append(f"Found {len(idle)} idle resource(s). Consider reallocating or scaling down.")
        total = resources.get('total', {})
        if total.get('cpu_cores', 0) > 0 and total.get('memory_mb', 0) > 0:
            recs.append(f"Current ratio: {total['cpu_cores']} CPU cores / {total['memory_mb']} MB memory")
        return recs


async def main():
    config = {}
    tracker = UnifiedResourceTracker(config)
    await tracker.initialize()
    print("Fetching unified resources...")
    resources = await tracker.get_all_resources()
    print(json.dumps(resources, indent=2))
    await tracker.close()


if __name__ == '__main__':
    asyncio.run(main())
