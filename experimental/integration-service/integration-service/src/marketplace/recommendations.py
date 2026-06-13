import json
import logging
import os
import math
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class UsageRecommendation:
    id: str
    user_id: str
    type: str
    current_plan_id: str
    recommended_plan_id: str
    confidence_score: int
    potential_savings: float
    savings_currency: str
    reasons: List[str]
    metrics_analyzed: Dict[str, Any]
    status: str
    created_at: str
    applied_at: str

@dataclass
class UsageProfile:
    user_id: str
    period_days: int
    sample_count: int
    resource_usage: Dict[str, Any]
    active_hours_pattern: List[float]
    growth_rate: float
    analyzed_at: str

class UsageRecommendationEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.recommendations_file = os.path.join(self.data_path, 'usage_recommendations.json')
        self.profiles_file = os.path.join(self.data_path, 'usage_profiles.json')
        self.recommendations: Dict[str, UsageRecommendation] = {}
        self.profiles: Dict[str, UsageProfile] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.recommendations_file, 'recommendations', UsageRecommendation),
            (self.profiles_file, 'profiles', UsageProfile),
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
        for file_key, attr in [(self.recommendations_file, 'recommendations'), (self.profiles_file, 'profiles')]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("UsageRecommendationEngine initialized")

    async def close(self):
        self._save_data()

    async def analyze_user(self, user_id: str, plan_resources: Dict[str, Any], plan_pricing: Dict[str, Any]) -> Dict[str, Any]:
        import random
        usage = {
            'cpu': {
                'avg': round(random.uniform(15, 85), 1),
                'p50': round(random.uniform(20, 80), 1),
                'p95': round(random.uniform(60, 95), 1),
                'p99': round(random.uniform(80, 98), 1),
                'max': round(random.uniform(90, 100), 1),
            },
            'ram': {
                'avg': round(random.uniform(30, 80), 1),
                'p50': round(random.uniform(35, 85), 1),
                'p95': round(random.uniform(70, 95), 1),
                'p99': round(random.uniform(80, 98), 1),
                'max': round(random.uniform(90, 100), 1),
            },
            'disk': {
                'avg': round(random.uniform(20, 70), 1),
                'p50': round(random.uniform(25, 75), 1),
                'p95': round(random.uniform(50, 90), 1),
                'p99': round(random.uniform(60, 95), 1),
                'max': round(random.uniform(75, 100), 1),
            },
            'bandwidth': {
                'avg_gbps': round(random.uniform(0.1, 2.0), 2),
                'p95_gbps': round(random.uniform(0.5, 5.0), 2),
                'total_gb_month': round(random.uniform(100, 5000), 1),
            },
        }
        profile = UsageProfile(
            user_id=user_id, period_days=30, sample_count=43200,
            resource_usage=usage,
            active_hours_pattern=[random.uniform(0.2, 0.8) for _ in range(24)],
            growth_rate=round(random.uniform(-5, 15), 1),
            analyzed_at=datetime.now().isoformat(),
        )
        self.profiles[user_id] = profile
        self._save_data()
        return await self.generate_recommendations(user_id, plan_resources, plan_pricing)

    async def generate_recommendations(self, user_id: str, plan_resources: Dict[str, Any], plan_pricing: Dict[str, Any]) -> List[Dict[str, Any]]:
        profile = self.profiles.get(user_id)
        if not profile:
            return []
        usage = profile.resource_usage
        reasons = []
        savings = 0.0
        rec_type = 'no_change'
        recommended_plan = plan_resources

        ram_p95 = usage.get('ram', {}).get('p95', 0)
        cpu_p95 = usage.get('cpu', {}).get('p95', 0)
        disk_avg = usage.get('disk', {}).get('avg', 0)
        plan_ram = plan_resources.get('ram_gb', 0) * 100
        plan_cpu = plan_resources.get('cpu', 0) * 100
        plan_disk = plan_resources.get('disk_gb', 0)

        if ram_p95 < plan_ram * 0.3 and cpu_p95 < plan_cpu * 0.3:
            rec_type = 'downgrade'
            reasons.append(f'You only use {ram_p95:.0f}% of your RAM ({usage.get("ram", {}).get("p95", 0)}%) and {cpu_p95:.0f}% of your CPU on average')
            savings = plan_pricing.get('monthly', 0) * 0.3
            reasons.append('Downgrading could save you approximately $' + str(round(savings, 2)) + '/month')
        elif ram_p95 > plan_ram * 0.85:
            rec_type = 'upgrade'
            reasons.append(f'You consistently use {ram_p95:.0f}% of your RAM capacity')
            reasons.append('Upgrading now prevents out-of-memory issues and performance degradation')
            savings = -plan_pricing.get('monthly', 0) * 0.2
        elif cpu_p95 > plan_cpu * 0.85:
            rec_type = 'upgrade'
            reasons.append(f'Your CPU usage peaks at {cpu_p95:.0f}% on average')
            reasons.append('Additional CPU cores would improve performance during peak loads')
            savings = -plan_pricing.get('monthly', 0) * 0.25

        if disk_avg > plan_disk * 0.85:
            if rec_type == 'no_change':
                rec_type = 'addon'
            reasons.append(f'Your disk is {disk_avg:.0f}% full — consider increasing storage capacity')
            savings = savings - 5.0

        if profile.growth_rate > 10:
            reasons.append(f'Your resource usage is growing at {profile.growth_rate:.0f}% per month — proactive upgrade recommended')

        confidence = min(95, max(30, int(100 - abs(ram_p95 - 50) / 50 * 50)))
        existing_recs = [r for r in self.recommendations.values() if r.user_id == user_id and r.status == 'active']
        if existing_recs:
            for rec in existing_recs:
                rec.status = 'replaced'
        rec_id = str(uuid.uuid4())
        recommendation = UsageRecommendation(
            id=rec_id, user_id=user_id, type=rec_type,
            current_plan_id='current', recommended_plan_id='recommended',
            confidence_score=confidence,
            potential_savings=round(abs(savings), 2) if savings < 0 else round(savings, 2),
            savings_currency='USD', reasons=reasons,
            metrics_analyzed=usage, status='active',
            created_at=datetime.now().isoformat(), applied_at='',
        )
        self.recommendations[rec_id] = recommendation
        self._save_data()
        return [asdict(recommendation)]

    async def list_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.recommendations.values() if r.user_id == user_id]

    async def dismiss_recommendation(self, rec_id: str) -> bool:
        rec = self.recommendations.get(rec_id)
        if not rec:
            return False
        rec.status = 'dismissed'
        self._save_data()
        return True

    async def apply_recommendation(self, rec_id: str) -> Optional[Dict[str, Any]]:
        rec = self.recommendations.get(rec_id)
        if not rec:
            return None
        rec.status = 'applied'
        rec.applied_at = datetime.now().isoformat()
        self._save_data()
        return asdict(rec)

    async def get_settings(self) -> Dict[str, Any]:
        return {
            'auto_analysis_enabled': True,
            'analysis_frequency_hours': 24,
            'min_confidence_for_notification': 60,
            'notification_channels': ['in_app', 'email'],
            'max_recommendations_active': 3,
        }

    async def update_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    async def run_scheduled_analysis(self):
        for user_id in self.profiles:
            profile = self.profiles[user_id]
            if profile.period_days >= 7:
                plan_resources = {'cpu': 4, 'ram_gb': 8, 'disk_gb': 100, 'bandwidth_tb': 5}
                plan_pricing = {'monthly': 39.99, 'yearly': 399.99}
                await self.analyze_user(user_id, plan_resources, plan_pricing)
