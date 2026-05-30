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
class SLATemplate:
    id: str
    name: str
    description: str
    tier: str
    uptime_percentage: float
    max_response_time_minutes: int
    max_resolution_time_minutes: int
    credit_percentage: float
    credit_cap_percentage: float
    credit_cap_amount: float
    exclusions: List[str]

@dataclass
class SLACompliance:
    id: str
    service_id: str
    sla_template_id: str
    period_start: str
    period_end: str
    uptime_percentage_actual: float
    uptime_percentage_target: float
    total_downtime_seconds: int
    total_period_seconds: int
    breaches_count: int
    status: str

@dataclass
class ServiceCredit:
    id: str
    service_id: str
    sla_compliance_id: str
    user_id: str
    amount: float
    currency: str
    reason: str
    status: str
    issued_at: str
    applied_to_invoice: str

class SLAManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.templates_file = os.path.join(self.data_path, 'sla_templates.json')
        self.compliance_file = os.path.join(self.data_path, 'sla_compliance.json')
        self.credits_file = os.path.join(self.data_path, 'sla_credits.json')
        self.templates: Dict[str, SLATemplate] = {}
        self.compliance: Dict[str, SLACompliance] = {}
        self.credits: Dict[str, ServiceCredit] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.templates_file, 'templates', SLATemplate),
            (self.compliance_file, 'compliance', SLACompliance),
            (self.credits_file, 'credits', ServiceCredit),
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
            (self.templates_file, 'templates'),
            (self.compliance_file, 'compliance'),
            (self.credits_file, 'credits'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("SLAManager initialized")
        if not self.templates:
            await self._seed_default_templates()

    async def close(self):
        self._save_data()

    async def _seed_default_templates(self):
        templates = [
            {'name': 'Basic SLA', 'description': 'Standard uptime guarantee for personal projects', 'tier': 'basic', 'uptime_percentage': 99.5, 'max_response_time_minutes': 60, 'max_resolution_time_minutes': 480, 'credit_percentage': 5.0, 'credit_cap_percentage': 25.0, 'credit_cap_amount': 50.0, 'exclusions': ['Scheduled maintenance', 'Force majeure']},
            {'name': 'Business SLA', 'description': 'Enhanced SLA for business-critical workloads', 'tier': 'business', 'uptime_percentage': 99.9, 'max_response_time_minutes': 15, 'max_resolution_time_minutes': 120, 'credit_percentage': 10.0, 'credit_cap_percentage': 50.0, 'credit_cap_amount': 200.0, 'exclusions': ['Scheduled maintenance']},
            {'name': 'Enterprise SLA', 'description': 'Premium SLA for mission-critical infrastructure', 'tier': 'enterprise', 'uptime_percentage': 99.99, 'max_response_time_minutes': 5, 'max_resolution_time_minutes': 30, 'credit_percentage': 20.0, 'credit_cap_percentage': 100.0, 'credit_cap_amount': 1000.0, 'exclusions': []},
        ]
        for tpl in templates:
            tid = str(uuid.uuid4())
            template = SLATemplate(id=tid, **tpl)
            self.templates[tid] = template
        self._save_data()

    async def list_templates(self) -> List[Dict[str, Any]]:
        return [asdict(t) for t in self.templates.values()]

    async def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tid = str(uuid.uuid4())
        template = SLATemplate(
            id=tid, name=data['name'], description=data.get('description', ''),
            tier=data.get('tier', 'basic'), uptime_percentage=data['uptime_percentage'],
            max_response_time_minutes=data.get('max_response_time_minutes', 60),
            max_resolution_time_minutes=data.get('max_resolution_time_minutes', 480),
            credit_percentage=data.get('credit_percentage', 5.0),
            credit_cap_percentage=data.get('credit_cap_percentage', 25.0),
            credit_cap_amount=data.get('credit_cap_amount', 50.0),
            exclusions=data.get('exclusions', []),
        )
        self.templates[tid] = template
        self._save_data()
        return asdict(template)

    async def update_template(self, template_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        template = self.templates.get(template_id)
        if not template:
            return None
        for key in ['name', 'description', 'tier', 'uptime_percentage', 'max_response_time_minutes', 'max_resolution_time_minutes', 'credit_percentage', 'credit_cap_percentage', 'credit_cap_amount', 'exclusions']:
            if key in data:
                setattr(template, key, data[key])
        self._save_data()
        return asdict(template)

    async def delete_template(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_data()
            return True
        return False

    async def calculate_uptime(self, service_id: str, period_start: str, period_end: str) -> Dict[str, Any]:
        import random, time
        total_seconds = (datetime.fromisoformat(period_end) - datetime.fromisoformat(period_start)).total_seconds()
        simulated_uptime = 99.9 + (random.random() * 0.09)
        simulated_downtime = total_seconds * (1 - simulated_uptime / 100)
        return {
            'service_id': service_id,
            'period_start': period_start,
            'period_end': period_end,
            'total_seconds': int(total_seconds),
            'uptime_seconds': int(total_seconds - simulated_downtime),
            'downtime_seconds': int(simulated_downtime),
            'uptime_percentage': round(simulated_uptime, 4),
            'status': 'compliant' if simulated_uptime >= 99.9 else 'breached',
        }

    async def get_service_sla(self, service_id: str) -> Dict[str, Any]:
        template = next(iter(self.templates.values()), None)
        if not template:
            return {'error': 'No SLA templates configured'}
        uptime_data = await self.calculate_uptime(service_id, (datetime.now() - timedelta(days=30)).isoformat(), datetime.now().isoformat())
        return {
            'service_id': service_id,
            'sla_template': asdict(template),
            'current_period': uptime_data,
            'breaches': [asdict(c) for c in self.compliance.values() if c.service_id == service_id and c.status == 'breached'][-10:],
        }

    async def calculate_credits(self, service_id: str, period_start: str, period_end: str) -> Dict[str, Any]:
        template = next(iter(self.templates.values()), None)
        if not template:
            return {'error': 'No SLA template found'}
        uptime = await self.calculate_uptime(service_id, period_start, period_end)
        if uptime['uptime_percentage'] >= template.uptime_percentage:
            return {'eligible': False, 'reason': 'Uptime meets SLA target', 'uptime': uptime['uptime_percentage'], 'target': template.uptime_percentage}
        breach_pct = template.uptime_percentage - uptime['uptime_percentage']
        credit_pct = min(breach_pct * template.credit_percentage / 0.1, template.credit_cap_percentage)
        monthly_cost = 100.0
        credit_amount = min(monthly_cost * credit_pct / 100, template.credit_cap_amount)
        return {
            'eligible': True,
            'breach_percentage': round(breach_pct, 4),
            'credit_percentage': round(credit_pct, 2),
            'credit_amount': round(credit_amount, 2),
            'currency': 'USD',
            'uptime_percentage': uptime['uptime_percentage'],
            'target_percentage': template.uptime_percentage,
            'downtime_seconds': uptime['downtime_seconds'],
        }

    async def list_credits(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if service_id:
            return [asdict(c) for c in self.credits.values() if c.service_id == service_id]
        return [asdict(c) for c in self.credits.values()]

    async def issue_credit(self, data: Dict[str, Any]) -> ServiceCredit:
        credit = ServiceCredit(
            id=str(uuid.uuid4()),
            service_id=data['service_id'],
            sla_compliance_id=data.get('sla_compliance_id', ''),
            user_id=data['user_id'],
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            reason=data.get('reason', 'SLA breach'),
            status='pending',
            issued_at='',
            applied_to_invoice='',
        )
        self.credits[credit.id] = credit
        self._save_data()
        return credit

    async def approve_credit(self, credit_id: str) -> Optional[ServiceCredit]:
        credit = self.credits.get(credit_id)
        if not credit:
            return None
        credit.status = 'approved'
        credit.issued_at = datetime.now().isoformat()
        self._save_data()
        return credit

    async def generate_report(self, period_start: str, period_end: str) -> Dict[str, Any]:
        period_compliance = [c for c in self.compliance.values() if c.period_start >= period_start and c.period_end <= period_end]
        total_services = len(set(c.service_id for c in period_compliance))
        compliant = sum(1 for c in period_compliance if c.status == 'compliant')
        breached = sum(1 for c in period_compliance if c.status == 'breached')
        total_credits = sum(c.amount for c in self.credits.values() if c.issued_at >= period_start and c.issued_at <= period_end)
        return {
            'period_start': period_start,
            'period_end': period_end,
            'total_services': total_services,
            'compliant_services': compliant,
            'breached_services': breached,
            'compliance_rate': round(compliant / max(total_services, 1) * 100, 2),
            'total_credits_issued': round(total_credits, 2),
            'credits_count': len([c for c in self.credits.values() if c.issued_at >= period_start and c.issued_at <= period_end]),
        }
