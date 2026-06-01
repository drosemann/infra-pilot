import json
import logging
import os
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class BandwidthUsage:
    id: str
    server_id: str
    interface_name: str
    provider: str
    region: str
    timestamp: str
    bytes_in: int
    bytes_out: int
    bytes_total: int
    cost_in: float
    cost_out: float
    cost_total: float
    billing_period: str
    meter_type: str

@dataclass
class ProviderPricing:
    id: str
    provider_name: str
    region: str
    service_tier: str
    ingress_price_per_gb: float
    egress_price_per_gb: float
    committed_volume_gb: int
    committed_price: float
    percentile_95_commit: float
    percentile_95_price: float
    free_tier_gb: int
    currency: str

@dataclass
class CostAlert:
    id: str
    name: str
    metric: str
    threshold_value: float
    threshold_direction: str
    period: str
    enabled: bool
    notification_channels: List[str]
    last_fired: str

@dataclass
class CostOptimization:
    id: str
    type: str
    description: str
    estimated_savings_monthly: float
    implementation_cost: float
    roi_months: float
    status: str
    steps: List[str]

class NetworkCostAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.usage_file = os.path.join(self.data_path, 'netcost_usage.json')
        self.pricing_file = os.path.join(self.data_path, 'netcost_pricing.json')
        self.alerts_file = os.path.join(self.data_path, 'netcost_alerts.json')
        self.optimizations_file = os.path.join(self.data_path, 'netcost_optimizations.json')
        self.usages: Dict[str, BandwidthUsage] = {}
        self.pricings: Dict[str, ProviderPricing] = {}
        self.alerts: Dict[str, CostAlert] = {}
        self.optimizations: List[CostOptimization] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.usage_file, 'usages', BandwidthUsage),
            (self.pricing_file, 'pricings', ProviderPricing),
            (self.alerts_file, 'alerts', CostAlert),
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
            if os.path.exists(self.optimizations_file):
                with open(self.optimizations_file, 'r') as f:
                    raw = json.load(f)
                self.optimizations = [CostOptimization(**item) for item in raw]
        except Exception as e:
            logger.warning(f"Failed to load optimizations: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.usage_file, 'usages'),
            (self.pricing_file, 'pricings'),
            (self.alerts_file, 'alerts'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")
        try:
            with open(self.optimizations_file, 'w') as f:
                json.dump([asdict(o) for o in self.optimizations], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save optimizations: {e}")

    async def initialize(self):
        logger.info("NetworkCostAnalyzer initialized")
        if not self.pricings:
            await self._seed_default_pricing()

    async def close(self):
        self._save_data()

    async def _seed_default_pricing(self):
        defaults = [
            {'provider_name': 'AWS', 'region': 'us-east-1', 'egress_price_per_gb': 0.09, 'free_tier_gb': 100},
            {'provider_name': 'AWS', 'region': 'eu-west-1', 'egress_price_per_gb': 0.09, 'free_tier_gb': 100},
            {'provider_name': 'AWS', 'region': 'ap-southeast-1', 'egress_price_per_gb': 0.12, 'free_tier_gb': 100},
            {'provider_name': 'Azure', 'region': 'eastus', 'egress_price_per_gb': 0.087, 'free_tier_gb': 100},
            {'provider_name': 'Azure', 'region': 'westeurope', 'egress_price_per_gb': 0.087, 'free_tier_gb': 100},
            {'provider_name': 'GCP', 'region': 'us-central1', 'egress_price_per_gb': 0.12, 'free_tier_gb': 100},
            {'provider_name': 'GCP', 'region': 'europe-west1', 'egress_price_per_gb': 0.12, 'free_tier_gb': 100},
            {'provider_name': 'DigitalOcean', 'region': 'nyc1', 'egress_price_per_gb': 0.02, 'free_tier_gb': 1000},
            {'provider_name': 'DigitalOcean', 'region': 'fra1', 'egress_price_per_gb': 0.02, 'free_tier_gb': 1000},
            {'provider_name': 'Hetzner', 'region': 'fsn1', 'egress_price_per_gb': 0.01, 'free_tier_gb': 10000},
            {'provider_name': 'Hetzner', 'region': 'nbg1', 'egress_price_per_gb': 0.01, 'free_tier_gb': 10000},
            {'provider_name': 'Vultr', 'region': 'ewr', 'egress_price_per_gb': 0.01, 'free_tier_gb': 2000},
            {'provider_name': 'Vultr', 'region': 'fra', 'egress_price_per_gb': 0.01, 'free_tier_gb': 2000},
            {'provider_name': 'Linode', 'region': 'us-east', 'egress_price_per_gb': 0.02, 'free_tier_gb': 1000},
            {'provider_name': 'Linode', 'region': 'eu-west', 'egress_price_per_gb': 0.02, 'free_tier_gb': 1000},
            {'provider_name': 'OVH', 'region': 'gra', 'egress_price_per_gb': 0.01, 'free_tier_gb': 500},
        ]
        for d in defaults:
            pid = str(uuid.uuid4())
            pricing = ProviderPricing(
                id=pid, provider_name=d['provider_name'], region=d['region'],
                service_tier='standard', ingress_price_per_gb=0.0,
                egress_price_per_gb=d['egress_price_per_gb'],
                committed_volume_gb=0, committed_price=0.0,
                percentile_95_commit=0.0, percentile_95_price=0.0,
                free_tier_gb=d['free_tier_gb'], currency='USD',
            )
            self.pricings[pid] = pricing
        self._save_data()

    async def get_usage(self, period: str = 'monthly') -> List[Dict[str, Any]]:
        return [asdict(u) for u in self.usages.values()]

    async def get_breakdown(self) -> Dict[str, Any]:
        total_cost = sum(u.cost_total for u in self.usages.values())
        total_bytes = sum(u.bytes_total for u in self.usages.values())
        provider_breakdown: Dict[str, Dict[str, Any]] = {}
        region_breakdown: Dict[str, Dict[str, Any]] = {}
        server_breakdown: Dict[str, Dict[str, Any]] = {}
        for usage in self.usages.values():
            if usage.provider not in provider_breakdown:
                provider_breakdown[usage.provider] = {'cost': 0, 'bytes': 0, 'count': 0}
            provider_breakdown[usage.provider]['cost'] += usage.cost_total
            provider_breakdown[usage.provider]['bytes'] += usage.bytes_total
            provider_breakdown[usage.provider]['count'] += 1
            region_key = f"{usage.provider}/{usage.region}"
            if region_key not in region_breakdown:
                region_breakdown[region_key] = {'cost': 0, 'bytes': 0, 'count': 0}
            region_breakdown[region_key]['cost'] += usage.cost_total
            region_breakdown[region_key]['bytes'] += usage.bytes_total
            region_breakdown[region_key]['count'] += 1
            if usage.server_id not in server_breakdown:
                server_breakdown[usage.server_id] = {'cost': 0, 'bytes': 0, 'count': 0}
            server_breakdown[usage.server_id]['cost'] += usage.cost_total
            server_breakdown[usage.server_id]['bytes'] += usage.bytes_total
            server_breakdown[usage.server_id]['count'] += 1
        return {
            'total_cost': round(total_cost, 2),
            'total_bandwidth_gb': round(total_bytes / (1024**3), 2),
            'by_provider': {k: {**v, 'cost': round(v['cost'], 2), 'bytes_gb': round(v['bytes'] / (1024**3), 2)} for k, v in sorted(provider_breakdown.items(), key=lambda x: -x[1]['cost'])},
            'by_region': {k: {**v, 'cost': round(v['cost'], 2), 'bytes_gb': round(v['bytes'] / (1024**3), 2)} for k, v in sorted(region_breakdown.items(), key=lambda x: -x[1]['cost'])},
            'by_server': {k: {**v, 'cost': round(v['cost'], 2), 'bytes_gb': round(v['bytes'] / (1024**3), 2)} for k, v in sorted(server_breakdown.items(), key=lambda x: -x[1]['cost'])},
            'period': 'current_month',
        }

    async def get_forecast(self, days: int = 90) -> Dict[str, Any]:
        total_days = max(len(set(u.timestamp[:10] for u in self.usages.values())), 1)
        daily_avg_cost = sum(u.cost_total for u in self.usages.values()) / total_days if total_days > 0 else 0
        daily_avg_bytes = sum(u.bytes_total for u in self.usages.values()) / total_days if total_days > 0 else 0
        growth_factor = 1.05
        monthly_forecast = []
        for month in range(1, 4):
            factor = growth_factor ** month
            monthly_forecast.append({
                'month': month,
                'forecasted_cost': round(daily_avg_cost * 30 * factor, 2),
                'forecasted_bandwidth_gb': round(daily_avg_bytes * 30 * factor / (1024**3), 2),
            })
        return {
            'daily_avg_cost': round(daily_avg_cost, 2),
            'daily_avg_bandwidth_gb': round(daily_avg_bytes / (1024**3), 2),
            'growth_rate_pct': (growth_factor - 1) * 100,
            'forecast_days': days,
            'monthly_forecast': monthly_forecast,
            'total_forecast_cost_90d': round(sum(m['forecasted_cost'] for m in monthly_forecast), 2),
        }

    async def get_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for alert in self.alerts.values():
            current_value = 0
            if alert.metric == 'egress_cost':
                current_value = sum(u.cost_out for u in self.usages.values())
            elif alert.metric == 'total_cost':
                current_value = sum(u.cost_total for u in self.usages.values())
            elif alert.metric == 'bandwidth':
                current_value = sum(u.bytes_total for u in self.usages.values())
            triggered = False
            if alert.threshold_direction == 'above' and current_value > alert.threshold_value:
                triggered = True
            elif alert.threshold_direction == 'below' and current_value < alert.threshold_value:
                triggered = True
            alert_dict = asdict(alert)
            alert_dict['current_value'] = round(current_value, 2)
            alert_dict['triggered'] = triggered
            alerts.append(alert_dict)
        return alerts

    async def create_alert(self, data: Dict[str, Any]) -> CostAlert:
        alert = CostAlert(
            id=str(uuid.uuid4()),
            name=data['name'],
            metric=data['metric'],
            threshold_value=data['threshold_value'],
            threshold_direction=data.get('threshold_direction', 'above'),
            period=data.get('period', 'monthly'),
            enabled=data.get('enabled', True),
            notification_channels=data.get('notification_channels', []),
            last_fired='',
        )
        self.alerts[alert.id] = alert
        self._save_data()
        return alert

    async def get_providers(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.pricings.values()]

    async def add_provider(self, data: Dict[str, Any]) -> ProviderPricing:
        pid = str(uuid.uuid4())
        pricing = ProviderPricing(
            id=pid, provider_name=data['provider_name'], region=data['region'],
            service_tier=data.get('service_tier', 'standard'),
            ingress_price_per_gb=data.get('ingress_price_per_gb', 0.0),
            egress_price_per_gb=data['egress_price_per_gb'],
            committed_volume_gb=data.get('committed_volume_gb', 0),
            committed_price=data.get('committed_price', 0.0),
            percentile_95_commit=data.get('percentile_95_commit', 0.0),
            percentile_95_price=data.get('percentile_95_price', 0.0),
            free_tier_gb=data.get('free_tier_gb', 0), currency=data.get('currency', 'USD'),
        )
        self.pricings[pid] = pricing
        self._save_data()
        return pricing

    async def get_optimizations(self) -> List[Dict[str, Any]]:
        if not self.optimizations:
            await self._generate_optimizations()
        return [asdict(o) for o in self.optimizations]

    async def _generate_optimizations(self):
        providers = set(u.provider for u in self.usages.values())
        if 'Hetzner' not in providers:
            total_egress = sum(u.bytes_out for u in self.usages.values()) / (1024**3)
            if total_egress > 100:
                opt = CostOptimization(
                    id=str(uuid.uuid4()), type='provider_switch',
                    description='Switch to Hetzner for egress traffic to save up to 80% on bandwidth costs',
                    estimated_savings_monthly=round(total_egress * 0.08, 2),
                    implementation_cost=0, roi_months=0, status='identified',
                    steps=['Compare current egress costs with Hetzner pricing', 'Create Hetzner account', 'Migrate non-critical traffic', 'Update DNS for new endpoints'])
                self.optimizations.append(opt)
        has_compression = any('compression' in u.interface_name.lower() for u in self.usages.values())
        if not has_compression:
            opt = CostOptimization(
                id=str(uuid.uuid4()), type='compression',
                description='Enable gzip/brotli compression on web servers to reduce bandwidth by 60-80%',
                estimated_savings_monthly=round(sum(u.cost_out for u in self.usages.values()) * 0.6, 2),
                implementation_cost=50, roi_months=0.1, status='identified',
                steps=['Enable gzip in nginx/apache config', 'Enable brotli compression', 'Verify compression headers', 'Monitor bandwidth reduction'])
            self.optimizations.append(opt)
        opt_cache = CostOptimization(
            id=str(uuid.uuid4()), type='caching',
            description='Implement CDN caching to reduce origin bandwidth by up to 70%',
            estimated_savings_monthly=round(sum(u.cost_out for u in self.usages.values()) * 0.5, 2),
            implementation_cost=100, roi_months=0.3, status='identified',
            steps=['Choose CDN provider (Cloudflare/BunnyCDN/KeyCDN)', 'Configure CDN for static assets', 'Set cache-control headers', 'Implement cache invalidation strategy'])
        self.optimizations.append(opt_cache)
        self._save_data()

    async def record_usage(self, data: Dict[str, Any]) -> BandwidthUsage:
        uid = str(uuid.uuid4())
        gb_total = (data.get('bytes_in', 0) + data.get('bytes_out', 0)) / (1024**3)
        price_per_gb = 0.01
        for p in self.pricings.values():
            if p.provider_name == data.get('provider', '') and p.region == data.get('region', ''):
                price_per_gb = p.egress_price_per_gb
                gb_total = max(0, gb_total - p.free_tier_gb)
                break
        cost = max(0, gb_total * price_per_gb)
        cost_in = max(0, data.get('bytes_in', 0) / (1024**3) * price_per_gb)
        cost_out = max(0, data.get('bytes_out', 0) / (1024**3) * price_per_gb)
        usage = BandwidthUsage(
            id=uid, server_id=data.get('server_id', ''), interface_name=data.get('interface', ''),
            provider=data.get('provider', 'Unknown'), region=data.get('region', 'unknown'),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            bytes_in=data.get('bytes_in', 0), bytes_out=data.get('bytes_out', 0),
            bytes_total=data.get('bytes_in', 0) + data.get('bytes_out', 0),
            cost_in=round(cost_in, 6), cost_out=round(cost_out, 6), cost_total=round(cost, 6),
            billing_period='current', meter_type='per_gb',
        )
        self.usages[uid] = usage
        if len(self.usages) > 100000:
            old_ids = sorted(self.usages.keys(), key=lambda x: self.usages[x].timestamp)[:10000]
            for oid in old_ids:
                del self.usages[oid]
        self._save_data()
        await self._evaluate_alerts()
        return usage

    async def _evaluate_alerts(self):
        pass

    async def get_by_provider(self) -> List[Dict[str, Any]]:
        breakdown = await self.get_breakdown()
        return list(breakdown.get('by_provider', {}).values())

    async def get_by_region(self) -> List[Dict[str, Any]]:
        breakdown = await self.get_breakdown()
        return list(breakdown.get('by_region', {}).values())

    async def get_by_server(self) -> List[Dict[str, Any]]:
        breakdown = await self.get_breakdown()
        return list(breakdown.get('by_server', {}).values())
