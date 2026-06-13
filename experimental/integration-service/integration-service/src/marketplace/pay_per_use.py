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
class UsageMetering:
    id: str
    user_id: str
    resource_type: str
    quantity: float
    meter_type: str
    start_time: str
    end_time: str
    cost: float
    invoice_id: str

@dataclass
class PricingRate:
    id: str
    resource_type: str
    meter_type: str
    unit_price: float
    currency: str
    tier_min: float
    tier_max: float
    tier_price: float
    region: str
    effective_from: str
    effective_to: str
    is_active: bool

@dataclass
class Invoice:
    id: str
    user_id: str
    invoice_number: str
    period_start: str
    period_end: str
    issue_date: str
    due_date: str
    line_items: List[Dict[str, Any]]
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    status: str
    stripe_invoice_id: str
    paid_at: str

class PayPerUseBillingManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.usage_file = os.path.join(self.data_path, 'billing_usage.json')
        self.rates_file = os.path.join(self.data_path, 'billing_rates.json')
        self.invoices_file = os.path.join(self.data_path, 'billing_invoices.json')
        self.usages: Dict[str, UsageMetering] = {}
        self.rates: Dict[str, PricingRate] = {}
        self.invoices: Dict[str, Invoice] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.usage_file, 'usages', UsageMetering),
            (self.rates_file, 'rates', PricingRate),
            (self.invoices_file, 'invoices', Invoice),
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
            (self.usage_file, 'usages'),
            (self.rates_file, 'rates'),
            (self.invoices_file, 'invoices'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("PayPerUseBillingManager initialized")
        if not self.rates:
            await self._seed_default_rates()

    async def close(self):
        self._save_data()

    async def _seed_default_rates(self):
        default_rates = [
            {'resource_type': 'cpu', 'meter_type': 'per_second', 'unit_price': 0.000001, 'region': 'global'},
            {'resource_type': 'ram', 'meter_type': 'per_gb_hour', 'unit_price': 0.007, 'region': 'global'},
            {'resource_type': 'disk', 'meter_type': 'per_gb_hour', 'unit_price': 0.0001, 'region': 'global'},
            {'resource_type': 'network', 'meter_type': 'per_gb', 'unit_price': 0.01, 'region': 'global'},
            {'resource_type': 'backup', 'meter_type': 'per_gb_hour', 'unit_price': 0.0005, 'region': 'global'},
            {'resource_type': 'snapshot', 'meter_type': 'per_gb_hour', 'unit_price': 0.0003, 'region': 'global'},
        ]
        for rd in default_rates:
            rid = str(uuid.uuid4())
            rate = PricingRate(
                id=rid, resource_type=rd['resource_type'], meter_type=rd['meter_type'],
                unit_price=rd['unit_price'], currency='USD',
                tier_min=0, tier_max=999999, tier_price=rd['unit_price'],
                region=rd['region'], effective_from='2024-01-01T00:00:00',
                effective_to='2099-12-31T23:59:59', is_active=True,
            )
            self.rates[rid] = rate
        self._save_data()

    async def get_usage(self, user_id: str, period: str = 'current') -> Dict[str, Any]:
        user_usages = [u for u in self.usages.values() if u.user_id == user_id]
        if period == 'current':
            start = datetime.now().replace(day=1).isoformat()
            user_usages = [u for u in user_usages if u.start_time >= start]
        total_cost = sum(u.cost for u in user_usages)
        by_resource: Dict[str, Dict[str, Any]] = {}
        for u in user_usages:
            if u.resource_type not in by_resource:
                by_resource[u.resource_type] = {'quantity': 0, 'cost': 0, 'count': 0}
            by_resource[u.resource_type]['quantity'] += u.quantity
            by_resource[u.resource_type]['cost'] += u.cost
            by_resource[u.resource_type]['count'] += 1
        return {
            'user_id': user_id,
            'period': period,
            'total_cost': round(total_cost, 6),
            'total_usage_events': len(user_usages),
            'by_resource': {k: {**v, 'cost': round(v['cost'], 6)} for k, v in by_resource.items()},
            'usage_records': [asdict(u) for u in user_usages[-100:]],
        }

    async def record_usage(self, data: Dict[str, Any]) -> UsageMetering:
        resource_type = data['resource_type']
        quantity = data['quantity']
        rate = None
        for r in self.rates.values():
            if r.resource_type == resource_type and r.is_active and r.tier_min <= quantity <= r.tier_max:
                rate = r
                break
        if not rate:
            for r in self.rates.values():
                if r.resource_type == resource_type and r.is_active:
                    rate = r
                    break
        if not rate:
            raise ValueError(f"No active rate found for {resource_type}")
        unit_price = rate.unit_price
        if rate.tier_price != rate.unit_price:
            unit_price = rate.tier_price
        cost = quantity * unit_price
        meter = UsageMetering(
            id=str(uuid.uuid4()),
            user_id=data.get('user_id', ''),
            resource_type=resource_type,
            quantity=quantity,
            meter_type=rate.meter_type,
            start_time=data.get('start_time', datetime.now().isoformat()),
            end_time=data.get('end_time', datetime.now().isoformat()),
            cost=round(cost, 10),
            invoice_id='',
        )
        self.usages[meter.id] = meter
        if len(self.usages) > 100000:
            old_ids = sorted(self.usages.keys(), key=lambda x: self.usages[x].start_time)[:10000]
            for oid in old_ids:
                del self.usages[oid]
        self._save_data()
        return meter

    async def estimate_cost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cpu = data.get('cpu', 1)
        ram_gb = data.get('ram_gb', 1)
        disk_gb = data.get('disk_gb', 10)
        hours = data.get('hours', 720)
        cpu_cost = cpu * hours * 3600 * 0.000001
        ram_cost = ram_gb * hours * 0.007
        disk_cost = disk_gb * hours * 0.0001
        total = cpu_cost + ram_cost + disk_cost
        return {
            'breakdown': {
                'cpu': {'hours': cpu * hours * 3600, 'rate': '$0.000001/sec', 'cost': round(cpu_cost, 6)},
                'ram': {'gb_hours': ram_gb * hours, 'rate': '$0.007/GB-hr', 'cost': round(ram_cost, 6)},
                'disk': {'gb_hours': disk_gb * hours, 'rate': '$0.0001/GB-hr', 'cost': round(disk_cost, 6)},
            },
            'hourly': round(total / hours, 6),
            'daily': round(total / hours * 24, 6),
            'monthly': round(total, 6),
            'currency': 'USD',
        }

    async def get_rates(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.rates.values() if r.is_active]

    async def update_rates(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if 'rates' in data:
            for rate_data in data['rates']:
                existing = None
                for r in self.rates.values():
                    if r.resource_type == rate_data.get('resource_type', '') and r.region == rate_data.get('region', 'global'):
                        existing = r
                        break
                if existing:
                    for key in ['unit_price', 'is_active', 'tier_min', 'tier_max', 'tier_price']:
                        if key in rate_data:
                            setattr(existing, key, rate_data[key])
                else:
                    rid = str(uuid.uuid4())
                    rate = PricingRate(
                        id=rid, resource_type=rate_data['resource_type'],
                        meter_type=rate_data.get('meter_type', 'per_unit'),
                        unit_price=rate_data['unit_price'], currency='USD',
                        tier_min=rate_data.get('tier_min', 0), tier_max=rate_data.get('tier_max', 999999),
                        tier_price=rate_data.get('tier_price', rate_data['unit_price']),
                        region=rate_data.get('region', 'global'),
                        effective_from=datetime.now().isoformat(), effective_to='2099-12-31T23:59:59',
                        is_active=rate_data.get('is_active', True),
                    )
                    self.rates[rid] = rate
        self._save_data()
        return [asdict(r) for r in self.rates.values() if r.is_active]

    async def get_invoices(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(i) for i in self.invoices.values() if i.user_id == user_id]

    async def generate_invoice(self, user_id: str, period_start: str, period_end: str) -> Invoice:
        relevant = [u for u in self.usages.values() if u.user_id == user_id and u.start_time >= period_start and u.end_time <= period_end and not u.invoice_id]
        if not relevant:
            raise ValueError('No unbilled usage found')
        by_resource: Dict[str, Dict[str, Any]] = {}
        for u in relevant:
            if u.resource_type not in by_resource:
                by_resource[u.resource_type] = {'quantity': 0, 'cost': 0}
            by_resource[u.resource_type]['quantity'] += u.quantity
            by_resource[u.resource_type]['cost'] += u.cost
        line_items = [{'description': rt, 'quantity': round(v['quantity'], 4), 'unit_price': round(v['cost'] / max(v['quantity'], 0.0001), 10), 'total': round(v['cost'], 6)} for rt, v in by_resource.items()]
        subtotal = sum(item['total'] for item in line_items)
        tax = subtotal * 0.0
        inv_id = str(uuid.uuid4())
        inv_num = f'INV-{datetime.now().strftime("%Y%m")}-{str(uuid.uuid4())[:8].upper()}'
        invoice = Invoice(
            id=inv_id, user_id=user_id, invoice_number=inv_num,
            period_start=period_start, period_end=period_end,
            issue_date=datetime.now().isoformat(),
            due_date=(datetime.now() + timedelta(days=14)).isoformat(),
            line_items=line_items, subtotal=round(subtotal, 2),
            tax_amount=round(tax, 2), total_amount=round(subtotal + tax, 2),
            currency='USD', status='draft', stripe_invoice_id='', paid_at='',
        )
        self.invoices[invoice.id] = invoice
        for u in relevant:
            u.invoice_id = invoice.id
        self._save_data()
        return invoice

    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        total_usage = sum(u.cost for u in self.usages.values() if u.user_id == user_id)
        total_invoiced = sum(i.total_amount for i in self.invoices.values() if i.user_id == user_id and i.status in ('paid', 'open'))
        unpaid = sum(i.total_amount for i in self.invoices.values() if i.user_id == user_id and i.status in ('draft', 'open'))
        return {
            'user_id': user_id,
            'total_usage': round(total_usage, 2),
            'total_invoiced': round(total_invoiced, 2),
            'unpaid_balance': round(unpaid, 2),
            'current_month_usage': round(sum(u.cost for u in self.usages.values() if u.user_id == user_id and u.start_time >= datetime.now().replace(day=1).isoformat()), 2),
        }

    async def add_payment_method(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': data.get('type', 'card'),
            'last4': data.get('last4', '4242'),
            'exp_month': data.get('exp_month', 12),
            'exp_year': data.get('exp_year', 2028),
            'is_default': data.get('is_default', True),
            'created_at': datetime.now().isoformat(),
        }

    async def top_up_balance(self, user_id: str, amount: float) -> Dict[str, Any]:
        return {
            'user_id': user_id,
            'amount': amount,
            'currency': 'USD',
            'new_balance': amount,
            'transaction_id': str(uuid.uuid4()),
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
        }
