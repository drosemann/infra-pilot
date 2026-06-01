import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class SubscriptionPlan:
    id: str
    name: str
    slug: str
    description: str
    tagline: str
    status: str
    visibility: str
    sort_order: int
    is_featured: bool
    resources: Dict[str, Any]
    features: Dict[str, Any]
    pricing: Dict[str, Any]
    max_servers: int
    max_backups: int
    max_databases: int
    created_at: str
    updated_at: str

@dataclass
class PlanAddon:
    id: str
    plan_id: str
    name: str
    slug: str
    description: str
    resource_changes: Dict[str, Any]
    feature_changes: Dict[str, Any]
    pricing: Dict[str, Any]
    max_qty: int
    is_available: bool

class PlanBuilderManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.plans_file = os.path.join(self.data_path, 'subscription_plans.json')
        self.addons_file = os.path.join(self.data_path, 'plan_addons.json')
        self.plans: Dict[str, SubscriptionPlan] = {}
        self.addons: Dict[str, PlanAddon] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.plans_file, 'plans', SubscriptionPlan),
            (self.addons_file, 'addons', PlanAddon),
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
        for file_key, attr in [(self.plans_file, 'plans'), (self.addons_file, 'addons')]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("PlanBuilderManager initialized")
        if not self.plans:
            await self._seed_default_plans()

    async def close(self):
        self._save_data()

    async def _seed_default_plans(self):
        plans = [
            {'name': 'Starter', 'description': 'Perfect for personal projects and small websites', 'tagline': 'Get started for free', 'sort_order': 1, 'resources': {'cpu': 1, 'ram_gb': 1, 'disk_gb': 25, 'bandwidth_tb': 1, 'gpu': None}, 'features': {'backups': True, 'ssl': True, 'priority_support': False, 'monitoring': True, 'firewall': True}, 'pricing': {'monthly': 9.99, 'yearly': 99.99, 'setup_fee': 0}, 'max_servers': 1, 'max_backups': 3, 'max_databases': 1},
            {'name': 'Pro', 'description': 'For growing businesses and professional applications', 'tagline': 'More power, more control', 'sort_order': 2, 'resources': {'cpu': 4, 'ram_gb': 8, 'disk_gb': 100, 'bandwidth_tb': 5, 'gpu': None}, 'features': {'backups': True, 'ssl': True, 'priority_support': True, 'monitoring': True, 'firewall': True, 'dns_management': True, 'cdn': True}, 'pricing': {'monthly': 39.99, 'yearly': 399.99, 'setup_fee': 0}, 'max_servers': 5, 'max_backups': 10, 'max_databases': 5},
            {'name': 'Business', 'description': 'For teams with advanced infrastructure needs', 'tagline': 'Scale with confidence', 'sort_order': 3, 'resources': {'cpu': 8, 'ram_gb': 32, 'disk_gb': 500, 'bandwidth_tb': 20, 'gpu': None}, 'features': {'backups': True, 'ssl': True, 'priority_support': True, 'monitoring': True, 'firewall': True, 'dns_management': True, 'cdn': True, 'vpn': True, 'sla': True}, 'pricing': {'monthly': 149.99, 'yearly': 1499.99, 'setup_fee': 0}, 'max_servers': 20, 'max_backups': 50, 'max_databases': 20},
            {'name': 'Enterprise', 'description': 'For mission-critical infrastructure at scale', 'tagline': 'Maximum performance, maximum reliability', 'sort_order': 4, 'resources': {'cpu': 32, 'ram_gb': 128, 'disk_gb': 2000, 'bandwidth_tb': 100, 'gpu': '1x NVIDIA A100'}, 'features': {'backups': True, 'ssl': True, 'priority_support': True, 'monitoring': True, 'firewall': True, 'dns_management': True, 'cdn': True, 'vpn': True, 'sla': True, 'dedicated_ip': True, 'custom_domain': True}, 'pricing': {'monthly': 499.99, 'yearly': 4999.99, 'setup_fee': 99}, 'max_servers': 100, 'max_backups': 200, 'max_databases': 100},
        ]
        for i, pdata in enumerate(plans):
            pid = str(uuid.uuid4())
            slug = pdata['name'].lower().replace(' ', '-')
            plan = SubscriptionPlan(
                id=pid, name=pdata['name'], slug=slug,
                description=pdata['description'], tagline=pdata['tagline'],
                status='active', visibility='public',
                sort_order=pdata['sort_order'], is_featured=i == 1,
                resources=pdata['resources'], features=pdata['features'],
                pricing=pdata['pricing'],
                max_servers=pdata['max_servers'], max_backups=pdata['max_backups'],
                max_databases=pdata['max_databases'],
                created_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat(),
            )
            self.plans[pid] = plan
        self._save_data()
        logger.info(f"Seeded {len(plans)} subscription plans")

    async def list_plans(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in sorted(self.plans.values(), key=lambda x: x.sort_order)]

    async def create_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pid = str(uuid.uuid4())
        slug = data['name'].lower().replace(' ', '-')
        plan = SubscriptionPlan(
            id=pid, name=data['name'], slug=slug,
            description=data.get('description', ''),
            tagline=data.get('tagline', ''),
            status='draft', visibility=data.get('visibility', 'public'),
            sort_order=data.get('sort_order', len(self.plans) + 1),
            is_featured=data.get('is_featured', False),
            resources=data.get('resources', {'cpu': 1, 'ram_gb': 1, 'disk_gb': 25, 'bandwidth_tb': 1, 'gpu': None}),
            features=data.get('features', {}),
            pricing=data.get('pricing', {'monthly': 9.99, 'yearly': 99.99, 'setup_fee': 0}),
            max_servers=data.get('max_servers', 1),
            max_backups=data.get('max_backups', 3),
            max_databases=data.get('max_databases', 1),
            created_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat(),
        )
        self.plans[pid] = plan
        self._save_data()
        return asdict(plan)

    async def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        plan = self.plans.get(plan_id)
        return asdict(plan) if plan else None

    async def update_plan(self, plan_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        for key in ['name', 'description', 'tagline', 'status', 'visibility', 'sort_order', 'is_featured', 'resources', 'features', 'pricing', 'max_servers', 'max_backups', 'max_databases']:
            if key in data:
                setattr(plan, key, data[key])
        if 'name' in data:
            plan.slug = data['name'].lower().replace(' ', '-')
        plan.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(plan)

    async def delete_plan(self, plan_id: str) -> bool:
        if plan_id in self.plans:
            addons_to_del = [aid for aid, a in self.addons.items() if a.plan_id == plan_id]
            for aid in addons_to_del:
                del self.addons[aid]
            del self.plans[plan_id]
            self._save_data()
            return True
        return False

    async def publish_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        plan.status = 'active'
        plan.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(plan)

    async def unpublish_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        plan.status = 'draft'
        plan.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(plan)

    async def list_addons(self, plan_id: str) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self.addons.values() if a.plan_id == plan_id]

    async def create_addon(self, plan_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        plan = self.plans.get(plan_id)
        if not plan:
            return None
        aid = str(uuid.uuid4())
        slug = data['name'].lower().replace(' ', '-')
        addon = PlanAddon(
            id=aid, plan_id=plan_id, name=data['name'], slug=slug,
            description=data.get('description', ''),
            resource_changes=data.get('resource_changes', {'ram_gb': 2, 'disk_gb': 25}),
            feature_changes=data.get('feature_changes', {}),
            pricing=data.get('pricing', {'monthly': 5, 'yearly': 50}),
            max_qty=data.get('max_qty', 1), is_available=data.get('is_available', True),
        )
        self.addons[aid] = addon
        self._save_data()
        return asdict(addon)

    async def update_addon(self, plan_id: str, addon_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        addon = self.addons.get(addon_id)
        if not addon or addon.plan_id != plan_id:
            return None
        for key in ['name', 'description', 'resource_changes', 'feature_changes', 'pricing', 'max_qty', 'is_available']:
            if key in data:
                setattr(addon, key, data[key])
        self._save_data()
        return asdict(addon)

    async def delete_addon(self, plan_id: str, addon_id: str) -> bool:
        addon = self.addons.get(addon_id)
        if not addon or addon.plan_id != plan_id:
            return False
        del self.addons[addon_id]
        self._save_data()
        return True

    async def compare_plans(self, plan_ids: List[str]) -> List[Dict[str, Any]]:
        return [asdict(self.plans[pid]) for pid in plan_ids if pid in self.plans]

    async def simulate_switch(self, from_plan_id: str, to_plan_id: str) -> Dict[str, Any]:
        from_plan = self.plans.get(from_plan_id)
        to_plan = self.plans.get(to_plan_id)
        if not from_plan or not to_plan:
            return {'error': 'One or both plans not found'}
        from_monthly = from_plan.pricing.get('monthly', 0)
        to_monthly = to_plan.pricing.get('monthly', 0)
        price_diff = to_monthly - from_monthly
        days_remaining = 15
        total_days = 30
        proration = round(price_diff * days_remaining / total_days, 2)
        switch_type = 'upgrade' if price_diff > 0 else 'downgrade'
        if price_diff == 0:
            switch_type = 'crossgrade'
        return {
            'from_plan': asdict(from_plan),
            'to_plan': asdict(to_plan),
            'price_difference_monthly': round(price_diff, 2),
            'switch_type': switch_type,
            'proration_amount': proration if proration > 0 else 0,
            'refund_amount': abs(proration) if proration < 0 else 0,
            'effective_immediately': True,
        }
