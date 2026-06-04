"""Feature 29: Multi-Cloud Discount Arbitrage - Compare effective pricing after committed discounts"""

import json
import os
import math
import uuid
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class Provider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HETZNER = "hetzner"
    OVH = "ovh"
    DIGITAL_OCEAN = "digitalocean"


PROVIDER_BASE_PRICING = {
    "aws": {"name": "AWS", "compute_mult": 1.0, "storage_gb_cost": 0.023, "data_egress_gb": 0.09,
            "ri_discount_1yr": 0.30, "ri_discount_3yr": 0.50, "savings_plan_discount": 0.20},
    "azure": {"name": "Azure", "compute_mult": 1.12, "storage_gb_cost": 0.0208, "data_egress_gb": 0.087,
              "ri_discount_1yr": 0.35, "ri_discount_3yr": 0.55, "savings_plan_discount": 0.25},
    "gcp": {"name": "GCP", "compute_mult": 0.95, "storage_gb_cost": 0.020, "data_egress_gb": 0.12,
            "ri_discount_1yr": 0.25, "ri_discount_3yr": 0.45, "savings_plan_discount": 0.15},
    "hetzner": {"name": "Hetzner", "compute_mult": 0.45, "storage_gb_cost": 0.01, "data_egress_gb": 0.05,
                "ri_discount_1yr": 0.0, "ri_discount_3yr": 0.0, "savings_plan_discount": 0.0},
    "ovh": {"name": "OVH", "compute_mult": 0.55, "storage_gb_cost": 0.012, "data_egress_gb": 0.04,
            "ri_discount_1yr": 0.0, "ri_discount_3yr": 0.0, "savings_plan_discount": 0.0},
    "digitalocean": {"name": "DigitalOcean", "compute_mult": 0.80, "storage_gb_cost": 0.015, "data_egress_gb": 0.01,
                     "ri_discount_1yr": 0.0, "ri_discount_3yr": 0.0, "savings_plan_discount": 0.0},
}


class DiscountType(Enum):
    RESERVED_INSTANCE = "reserved_instance"
    SAVINGS_PLAN = "savings_plan"
    COMMITTED_USE = "committed_use"
    SPOT = "spot"
    SUSTAINED_USE = "sustained_use"
    VOLUME_DISCOUNT = "volume_discount"
    NO_COMMITMENT = "no_commitment"


class DiscountArbitrage:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workloads_file = _data_file('arbitrage_workloads.json')
        self.comparisons_file = _data_file('arbitrage_comparisons.json')
        self.workloads: List[Dict[str, Any]] = []
        self.comparisons: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.workloads_file, 'workloads'), (self.comparisons_file, 'comparisons')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_workloads(self):
        try:
            with open(self.workloads_file, 'w') as f:
                json.dump(self.workloads, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workloads: {e}")

    def _save_comparisons(self):
        try:
            with open(self.comparisons_file, 'w') as f:
                json.dump(self.comparisons, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save comparisons: {e}")

    def register_workload(self, name: str, cpu_cores: int, memory_gb: int,
                          storage_gb: int, data_transfer_gb: int,
                          current_provider: str, current_cost: float) -> Dict[str, Any]:
        workload = {
            "id": str(uuid.uuid4()),
            "name": name,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "storage_gb": storage_gb,
            "data_transfer_gb": data_transfer_gb,
            "current_provider": current_provider,
            "current_monthly_cost": current_cost,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.workloads.append(workload)
        self._save_workloads()
        return workload

    def _calculate_effective_cost(self, provider: str, cpu_cores: int, memory_gb: int,
                                   storage_gb: int, data_transfer_gb: int,
                                   discount_type: str = None) -> Dict[str, Any]:
        pricing = PROVIDER_BASE_PRICING.get(provider, PROVIDER_BASE_PRICING["aws"])
        base_compute = (cpu_cores * 30 + memory_gb * 10) * pricing["compute_mult"]
        base_storage = storage_gb * pricing["storage_gb_cost"]
        base_transfer = data_transfer_gb * pricing["data_egress_gb"]
        base_monthly = base_compute + base_storage + base_transfer

        discount_rate = 0
        discount_label = DiscountType.NO_COMMITMENT.value
        if discount_type == DiscountType.RESERVED_INSTANCE.value:
            discount_rate = pricing["ri_discount_3yr"] if random.random() > 0.5 else pricing["ri_discount_1yr"]
            discount_label = DiscountType.RESERVED_INSTANCE.value
        elif discount_type == DiscountType.SAVINGS_PLAN.value:
            discount_rate = pricing["savings_plan_discount"]
            discount_label = DiscountType.SAVINGS_PLAN.value
        elif discount_type == DiscountType.SUSTAINED_USE.value:
            discount_rate = 0.15 if pricing["compute_mult"] < 1.0 else 0.0
            discount_label = DiscountType.SUSTAINED_USE.value
        elif discount_type == DiscountType.SPOT.value:
            discount_rate = 0.60
            discount_label = DiscountType.SPOT.value
        elif discount_type == DiscountType.COMMITTED_USE.value:
            discount_rate = 0.20
            discount_label = DiscountType.COMMITTED_USE.value

        effective_monthly = base_monthly * (1 - discount_rate)
        return {
            "provider": provider,
            "provider_name": pricing["name"],
            "discount_type": discount_label,
            "discount_rate": discount_rate,
            "base_compute_cost": round(base_compute, 2),
            "base_storage_cost": round(base_storage, 2),
            "base_transfer_cost": round(base_transfer, 2),
            "base_monthly_cost": round(base_monthly, 2),
            "effective_monthly_cost": round(effective_monthly, 2),
            "monthly_savings_vs_on_demand": round(base_monthly - effective_monthly, 2),
        }

    def compare_providers(self, workload_id: str) -> Dict[str, Any]:
        workload = next((w for w in self.workloads if w['id'] == workload_id), None)
        if not workload:
            return {"error": "Workload not found"}
        comparisons = []
        for provider in Provider:
            pv = provider.value
            for disc_type in [DiscountType.NO_COMMITMENT, DiscountType.RESERVED_INSTANCE,
                              DiscountType.SAVINGS_PLAN, DiscountType.SPOT]:
                if PROVIDER_BASE_PRICING[pv]["ri_discount_1yr"] == 0 and disc_type in [
                    DiscountType.RESERVED_INSTANCE, DiscountType.SAVINGS_PLAN, DiscountType.SUSTAINED_USE]:
                    continue
                comp = self._calculate_effective_cost(
                    pv, workload['cpu_cores'], workload['memory_gb'],
                    workload['storage_gb'], workload['data_transfer_gb'],
                    disc_type.value if disc_type != DiscountType.NO_COMMITMENT else None
                )
                comp['workload_id'] = workload_id
                comp['comparison_id'] = str(uuid.uuid4())
                comparisons.append(comp)

        best_overall = min(comparisons, key=lambda c: c['effective_monthly_cost'])
        current_on_demand = self._calculate_effective_cost(
            workload['current_provider'], workload['cpu_cores'], workload['memory_gb'],
            workload['storage_gb'], workload['data_transfer_gb']
        )
        savings_vs_current = round(current_on_demand['effective_monthly_cost'] - best_overall['effective_monthly_cost'], 2)
        savings_pct = round((savings_vs_current / max(current_on_demand['effective_monthly_cost'], 0.01)) * 100, 1) if savings_vs_current > 0 else 0

        result = {
            "workload_id": workload_id,
            "workload_name": workload['name'],
            "current_provider": workload['current_provider'],
            "current_monthly_cost": workload['current_monthly_cost'],
            "comparisons": comparisons,
            "best_option": best_overall,
            "potential_monthly_savings": savings_vs_current,
            "potential_savings_pct": savings_pct,
            "potential_annual_savings": round(savings_vs_current * 12, 2),
            "compared_at": datetime.utcnow().isoformat(),
        }
        self.comparisons.append(result)
        self._save_comparisons()
        return result

    def get_workload(self, workload_id: str) -> Optional[Dict[str, Any]]:
        return next((w for w in self.workloads if w['id'] == workload_id), None)

    def list_workloads(self) -> List[Dict[str, Any]]:
        return self.workloads

    def get_comparison(self, workload_id: str) -> Optional[Dict[str, Any]]:
        return next((c for c in self.comparisons if c['workload_id'] == workload_id), None)

    def get_all_comparisons(self) -> List[Dict[str, Any]]:
        return self.comparisons

    def get_aggregate_savings(self) -> Dict[str, Any]:
        total_current = sum(w['current_monthly_cost'] for w in self.workloads)
        total_optimized = 0
        for c in self.comparisons:
            best = c.get('best_option', {})
            total_optimized += best.get('effective_monthly_cost', 0)
        monthly_savings = total_current - total_optimized
        return {
            "total_workloads": len(self.workloads),
            "total_current_monthly": round(total_current, 2),
            "total_optimized_monthly": round(total_optimized, 2),
            "total_potential_monthly_savings": round(monthly_savings, 2),
            "total_potential_annual_savings": round(monthly_savings * 12, 2),
            "savings_pct": round((monthly_savings / max(total_current, 0.01)) * 100, 1),
            "avg_savings_per_workload": round(monthly_savings / max(len(self.workloads), 1), 2),
        }

    def auto_migrate_recommendation(self, workload_id: str) -> Dict[str, Any]:
        comparison = self.get_comparison(workload_id)
        if not comparison:
            comparison = self.compare_providers(workload_id)
        best = comparison['best_option']
        return {
            "workload_id": workload_id,
            "workload_name": comparison['workload_name'],
            "current_provider": comparison['current_provider'],
            "recommended_provider": best['provider'],
            "recommended_discount_type": best['discount_type'],
            "current_cost": comparison['current_monthly_cost'],
            "new_cost": best['effective_monthly_cost'],
            "monthly_savings": comparison['potential_monthly_savings'],
            "annual_savings": comparison['potential_annual_savings'],
            "savings_pct": comparison['potential_savings_pct'],
            "confidence": "high" if comparison['potential_savings_pct'] > 30 else "medium",
            "migration_effort": "complex" if best['provider'] != comparison['current_provider'] else "simple",
            "risks": ["Provider lock-in migration", "Data transfer costs"] if best['provider'] != comparison['current_provider'] else ["Commitment lock-in"],
        }

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class DiscountArbitrageError(Exception): pass

@dataclass
class WorkloadSpec:
    name: str
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    data_transfer_gb: int
    current_provider: str
    current_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_workload(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('name'): errors.append("name is required")
    if data.get('cpu_cores', 0) <= 0: errors.append("cpu_cores must be positive")
    if data.get('memory_gb', 0) <= 0: errors.append("memory_gb must be positive")
    if data.get('current_cost', 0) <= 0: errors.append("current_cost must be positive")
    return errors

def compute_cross_provider_cost(workload: Dict[str, Any], provider: str) -> Dict[str, Any]:
    base_cost = workload.get('current_cost', 1000)
    multipliers = {'aws': 1.0, 'azure': 1.05, 'gcp': 0.92, 'hetzner': 0.60, 'ovh': 0.70, 'digitalocean': 0.80}
    mult = multipliers.get(provider, 1.0)
    estimated = base_cost * mult
    return {
        "provider": provider,
        "estimated_monthly_cost": round(estimated, 2),
        "savings_vs_current": round(base_cost - estimated, 2),
        "savings_pct": round(((base_cost - estimated) / max(base_cost, 0.01)) * 100, 1),
        "discount_types_available": ["reserved_instance", "savings_plan", "spot", "committed_use"] if provider in ['aws', 'azure', 'gcp'] else ["simple"],
    }

def compare_all_providers(workload: Dict[str, Any]) -> List[Dict[str, Any]]:
    providers = ['aws', 'azure', 'gcp', 'hetzner', 'ovh', 'digitalocean']
    results = []
    for p in providers:
        if p == workload.get('current_provider'):
            continue
        results.append(compute_cross_provider_cost(workload, p))
    return sorted(results, key=lambda r: r.get('estimated_monthly_cost', 0))

def evaluate_migration_risk(source: str, target: str, workload: Dict[str, Any]) -> Dict[str, Any]:
    risk_factors = []
    if source != target:
        risk_factors.append({"factor": "provider_lock_in", "severity": "medium", "mitigation": "Use multi-cloud deployment as intermediate step"})
        if workload.get('data_transfer_gb', 0) > 100:
            risk_factors.append({"factor": "data_egress_cost", "severity": "high", "mitigation": "Compress data, use direct connect"})
    return {
        "risk_level": "low" if len(risk_factors) == 0 else ("medium" if len(risk_factors) <= 1 else "high"),
        "risk_factors": risk_factors,
        "migration_effort": "complex" if len(risk_factors) > 1 else ("medium" if len(risk_factors) == 1 else "simple"),
        "estimated_duration_hours": 8 if len(risk_factors) > 1 else 4,
    }

def find_best_provider(comparisons: List[Dict[str, Any]], weight_cost: float = 0.6, weight_features: float = 0.4) -> Dict[str, Any]:
    if not comparisons: return {}
    best = min(comparisons, key=lambda c: c.get('estimated_monthly_cost', float('inf')))
    return {
        "best_provider": best.get('provider'),
        "best_monthly_cost": best.get('estimated_monthly_cost'),
        "monthly_savings": best.get('savings_vs_current', 0),
        "annual_savings": round(best.get('savings_vs_current', 0) * 12, 2),
        "savings_pct": best.get('savings_pct', 0),
        "confidence": "high" if best.get('savings_pct', 0) > 20 else "medium",
    }

def generate_arbitrage_report(workloads: List[Dict[str, Any]], comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_current = sum(w.get('current_cost', 0) for w in workloads)
    best_provider = find_best_provider(comparisons) if comparisons else None
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_workloads": len(workloads),
        "total_current_monthly": round(total_current, 2),
        "best_alternative_monthly": round(best_provider.get('best_monthly_cost', total_current), 2) if best_provider else total_current,
        "total_potential_savings": round(best_provider.get('monthly_savings', 0) * len(workloads), 2) if best_provider else 0,
        "recommended_provider": best_provider.get('best_provider', 'N/A') if best_provider else 'N/A',
        "recommendations": [
            "Migrate high-cost workloads to recommended provider",
            "Use reserved instances for stable workloads",
            "Consider multi-cloud strategy for resilience",
        ],
    }

def simulate_spot_vs_on_demand(workload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "workload_name": workload.get('name'),
        "on_demand_monthly": workload.get('current_cost', 1000),
        "spot_monthly": round(workload.get('current_cost', 1000) * 0.35, 2),
        "monthly_savings": round(workload.get('current_cost', 1000) * 0.65, 2),
        "interruption_risk": "medium",
        "suitable_for_spot": workload.get('cpu_cores', 2) <= 8 and workload.get('storage_gb', 50) <= 500,
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class ArbitrageBatchProcessor:
    def __init__(self, arbitrage: 'DiscountArbitrage'):
        self.arbitrage = arbitrage
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_register_workloads(self, workloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for w in workloads:
            try:
                result = self.arbitrage.register_workload(name=w['name'], cpu_cores=w.get('cpu_cores', 4), memory_gb=w.get('memory_gb', 16), storage_gb=w.get('storage_gb', 100), data_transfer_gb=w.get('data_transfer_gb', 50), current_provider=w.get('current_provider', 'aws'), current_cost=w.get('current_cost', 1000))
                results.append({"success": True, "workload": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": w})
        return results

    async def batch_compare(self, workload_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for wid in workload_ids:
            try:
                result = self.arbitrage.get_comparisons(wid)
                results.append({"workload_id": wid, "comparisons": result})
            except Exception as e:
                results.append({"workload_id": wid, "error": str(e)})
        return results

    async def export_workloads_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "current_provider", "current_cost", "cpu_cores", "memory_gb"])
        for w in self.arbitrage.workloads:
            writer.writerow([w.get('id'), w.get('name'), w.get('current_provider'), w.get('current_cost'), w.get('cpu_cores'), w.get('memory_gb')])
        return output.getvalue()

class ArbitrageAnalytics:
    def __init__(self, arbitrage: 'DiscountArbitrage'):
        self.arbitrage = arbitrage

    def savings_by_provider(self) -> Dict[str, float]:
        by_provider = {}
        for w in self.arbitrage.workloads:
            comparisons = self.arbitrage.get_comparisons(w.get('id'))
            for comp in comparisons:
                p = comp.get('provider', 'unknown')
                by_provider[p] = by_provider.get(p, 0) + comp.get('savings_vs_current', 0)
        return {k: round(v, 2) for k, v in by_provider.items()}

    def workload_risk_profile(self) -> Dict[str, Any]:
        low = sum(1 for w in self.arbitrage.workloads if w.get('current_cost', 0) < 1000)
        medium = sum(1 for w in self.arbitrage.workloads if 1000 <= w.get('current_cost', 0) < 10000)
        high = sum(1 for w in self.arbitrage.workloads if w.get('current_cost', 0) >= 10000)
        return {"low_value": low, "medium_value": medium, "high_value": high, "total": len(self.arbitrage.workloads)}

class ArbitragePaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === ADVANCED ARBITRAGE ANALYSIS ===

class ArbitrageDeepAnalyzer:
    def __init__(self, arbitrage: DiscountArbitrage):
        self.arbitrage = arbitrage

    def provider_ranking(self, workload_id: str) -> Dict[str, Any]:
        workload = self.arbitrage.get_workload(workload_id)
        if not workload:
            return {"error": "Workload not found"}
        comparison = self.arbitrage.compare_providers(workload_id)
        ranked = sorted(comparison['comparisons'], key=lambda c: c['effective_monthly_cost'])
        return {
            "workload_id": workload_id,
            "workload_name": workload['name'],
            "ranked_providers": [
                {"rank": i+1, "provider": r['provider'], "discount": r['discount_type'],
                 "effective_cost": r['effective_monthly_cost'], "savings_vs_current": round(workload['current_monthly_cost'] - r['effective_monthly_cost'], 2)}
                for i, r in enumerate(ranked[:5])
            ],
        }

    def optimal_blend(self, workload_ids: List[str]) -> Dict[str, Any]:
        total_current = 0
        total_optimized = 0
        provider_allocation = {}
        for wid in workload_ids:
            w = self.arbitrage.get_workload(wid)
            if not w:
                continue
            total_current += w['current_monthly_cost']
            comp = self.arbitrage.compare_providers(wid)
            best = comp['best_option']
            total_optimized += best['effective_monthly_cost']
            p = best['provider']
            provider_allocation[p] = provider_allocation.get(p, 0) + 1
        return {
            "workloads_analyzed": len(workload_ids),
            "total_current_monthly": round(total_current, 2),
            "total_optimized_monthly": round(total_optimized, 2),
            "monthly_savings": round(total_current - total_optimized, 2),
            "savings_pct": round(((total_current - total_optimized) / max(total_current, 0.01)) * 100, 1),
            "provider_distribution": provider_allocation,
            "recommended_strategy": "multi_cloud" if len(provider_allocation) > 1 else "single_provider",
        }

# === CONTRACT NEGOTIATION ===

class ContractNegotiator:
    def __init__(self):
        self.contracts: List[Dict[str, Any]] = []

    def create_contract(self, provider: str, term_months: int, monthly_spend: float, discount_pct: float) -> Dict[str, Any]:
        contract = {
            "id": str(uuid.uuid4()),
            "provider": provider,
            "term_months": term_months,
            "monthly_spend": monthly_spend,
            "discount_pct": discount_pct,
            "effective_monthly": round(monthly_spend * (1 - discount_pct / 100), 2),
            "total_commitment": round(monthly_spend * (1 - discount_pct / 100) * term_months, 2),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.contracts.append(contract)
        return contract

    def benchmark(self, monthly_spend: float) -> Dict[str, Any]:
        benchmarks = {
            "aws": {"typical_discount": 25, "max_discount": 45},
            "azure": {"typical_discount": 28, "max_discount": 50},
            "gcp": {"typical_discount": 22, "max_discount": 40},
        }
        results = []
        for provider, bm in benchmarks.items():
            results.append({
                "provider": provider,
                "typical_discount_pct": bm["typical_discount"],
                "max_discount_pct": bm["max_discount"],
                "estimated_typical_monthly": round(monthly_spend * (1 - bm["typical_discount"] / 100), 2),
                "estimated_best_monthly": round(monthly_spend * (1 - bm["max_discount"] / 100), 2),
            })
        return {"monthly_spend": monthly_spend, "benchmarks": results}

    def negotiate(self, contract_id: str, target_discount: float) -> Dict[str, Any]:
        contract = next((c for c in self.contracts if c['id'] == contract_id), None)
        if not contract:
            return {"error": "Contract not found"}
        current = contract['discount_pct']
        feasible = target_discount <= current + 10
        return {
            "contract_id": contract_id,
            "provider": contract['provider'],
            "current_discount": current,
            "target_discount": target_discount,
            "feasible": feasible,
            "expected_outcome": "approved" if feasible else "rejected",
            "recommendation": "Proceed with negotiation" if feasible else "Adjust target or explore alternative providers",
        }

# === BULK PRICE COMPARISON ===

class BulkPriceComparator:
    def __init__(self):
        self.price_cache: Dict[str, Dict] = {}

    def compare_instance_pricing(self, instance_type: str, regions: List[str]) -> List[Dict[str, Any]]:
        results = []
        for region in regions:
            base_price = 0.05 + (hash(instance_type + region) % 1000) / 10000
            results.append({
                "instance_type": instance_type,
                "region": region,
                "on_demand_hourly": round(base_price, 4),
                "spot_hourly": round(base_price * 0.35, 4),
                "ri_1yr_hourly": round(base_price * 0.70, 4),
                "ri_3yr_hourly": round(base_price * 0.55, 4),
                "savings_plan_hourly": round(base_price * 0.80, 4),
                "cheapest_option": "spot" if base_price * 0.35 < base_price * 0.55 else "ri_3yr",
            })
        return sorted(results, key=lambda r: r['on_demand_hourly'])

    def find_cheapest(self, instance_type: str, required_count: int = 1) -> Dict[str, Any]:
        regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"]
        results = self.compare_instance_pricing(instance_type, regions)
        cheapest = min(results, key=lambda r: r['spot_hourly'])
        return {
            "instance_type": instance_type,
            "required_count": required_count,
            "cheapest_region": cheapest['region'],
            "cheapest_option": cheapest['cheapest_option'],
            "hourly_cost": round(cheapest[cheapest['cheapest_option'] + '_hourly'] * required_count, 4),
            "monthly_cost": round(cheapest[cheapest['cheapest_option'] + '_hourly'] * required_count * 730, 2),
        }

# === HISTORICAL TREND ===

class ArbitrageTrend:
    def __init__(self, arbitrage: DiscountArbitrage):
        self.arbitrage = arbitrage

    def savings_over_time(self, months: int = 6) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        trends = []
        for m in range(months):
            month_start = (now.replace(day=1) - timedelta(days=30 * m)).isoformat()
            total_current = sum(w['current_monthly_cost'] for w in self.arbitrage.workloads)
            total_optimized = total_current * (1 - 0.05 * m)
            trends.append({
                "month": (now - timedelta(days=30 * m)).strftime("%Y-%m"),
                "current_spend": round(total_current, 2),
                "optimized_spend": round(total_optimized, 2),
                "savings": round(total_current - total_optimized, 2),
            })
        return sorted(trends, key=lambda x: x['month'])

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_count": 0, "total_value": 0.0, "avg_value": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class FinopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    amount: float = 0.0
    currency: str = Field(default="USD")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FinopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total_cost: float = Field(default=0.0)
    estimated_savings: float = Field(default=0.0)

    def add_item(self, item: Dict[str, Any], cost: float = 0.0, savings: float = 0.0) -> None:
        self.items.append(item)
        self.total_cost += cost
        self.estimated_savings += savings

    def complete(self) -> None:
        self.status = "completed"

class CostMetrics(BaseModel):
    category: str
    amount: float
    currency: str = Field(default="USD")
    period: str = Field(default="monthly")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)

class CostTracker:
    def __init__(self) -> None:
        self._entries: List[CostMetrics] = []

    def record(self, category: str, amount: float, tags: Optional[Dict[str, str]] = None) -> None:
        self._entries.append(CostMetrics(category=category, amount=amount, tags=tags or {}))

    def total_by_category(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._entries:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals

    def total(self) -> float:
        return round(sum(e.amount for e in self._entries), 2)

    def average(self) -> float:
        return round(self.total() / max(len(self._entries), 1), 2)

    def get_by_period(self, period: str) -> List[CostMetrics]:
        return [e for e in self._entries if e.period == period]

    def summary(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries), "total_cost": self.total(),
                "avg_per_entry": self.average(),
                "by_category": self.total_by_category(),
                "latest": self._entries[-1].dict() if self._entries else None}

class SavingsCalculator:
    @staticmethod
    def compute(original_cost: float, new_cost: float) -> Dict[str, Any]:
        savings = original_cost - new_cost
        pct = (savings / original_cost * 100) if original_cost > 0 else 0
        return {"original": round(original_cost, 2), "new": round(new_cost, 2),
                "savings": round(savings, 2), "savings_pct": round(pct, 1)}

    @staticmethod
    def project_monthly(daily_savings: float, days: int = 30) -> float:
        return round(daily_savings * days, 2)

    @staticmethod
    def project_annual(daily_savings: float) -> float:
        return round(daily_savings * 365, 2)

    @staticmethod
    def roi(investment: float, savings_per_month: float, months: int = 12) -> Dict[str, Any]:
        total_savings = savings_per_month * months
        roi_value = ((total_savings - investment) / investment * 100) if investment > 0 else 0
        return {"investment": round(investment, 2), "total_savings": round(total_savings, 2),
                "months": months, "roi_pct": round(roi_value, 1),
                "payback_months": round(investment / max(savings_per_month, 0.01), 1)}

class BudgetAlert(BaseModel):
    budget_name: str
    threshold: float
    current_spend: float
    percentage: float
    severity: str = Field(default="info")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = False

    def should_alert(self) -> bool:
        return self.percentage >= self.threshold and not self.notified

class BudgetMonitor:
    def __init__(self) -> None:
        self._budgets: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[BudgetAlert] = []

    def set_budget(self, name: str, limit: float, warning_threshold: float = 80.0) -> None:
        self._budgets[name] = {"limit": limit, "warning_threshold": warning_threshold, "spend": 0.0}

    def record_spend(self, name: str, amount: float) -> Optional[BudgetAlert]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        budget["spend"] += amount
        pct = (budget["spend"] / budget["limit"]) * 100
        if pct >= budget["warning_threshold"]:
            alert = BudgetAlert(budget_name=name, threshold=budget["warning_threshold"],
                                current_spend=round(budget["spend"], 2),
                                percentage=round(pct, 1),
                                severity="warning" if pct < 100 else "critical")
            self._alerts.append(alert)
            return alert
        return None

    def get_budget_status(self, name: str) -> Optional[Dict[str, Any]]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        pct = (budget["spend"] / budget["limit"]) * 100 if budget["limit"] > 0 else 0
        return {"name": name, "limit": budget["limit"], "spend": round(budget["spend"], 2),
                "remaining": round(budget["limit"] - budget["spend"], 2),
                "usage_pct": round(pct, 1)}

    def get_all_status(self) -> Dict[str, Any]:
        return {name: self.get_budget_status(name) for name in self._budgets}

    def get_alerts(self, severity: Optional[str] = None) -> List[BudgetAlert]:
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return self._alerts

class ReportingSchedule(BaseModel):
    report_type: str
    frequency: str = Field(default="daily")
    recipients: List[str] = Field(default_factory=list)
    format: str = Field(default="pdf")
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None

# -- Advanced FinOps Analytics -----------------------------------------

class CostEfficiencyIndex:
    def __init__(self) -> None:
        self._indices: Dict[str, float] = {}

    def calculate(self, department: str, total_cost: float, output_value: float) -> float:
        if total_cost <= 0:
            return 0.0
        index = round(output_value / total_cost, 4)
        self._indices[department] = index
        return index

    def get_index(self, department: str) -> Optional[float]:
        return self._indices.get(department)

    def get_ranking(self) -> List[Dict[str, Any]]:
        ranked = sorted(self._indices.items(), key=lambda x: x[1], reverse=True)
        return [{"department": d, "efficiency_index": v, "rank": i + 1} for i, (d, v) in enumerate(ranked)]

class AnomalyThresholdConfig(BaseModel):
    metric: str
    warning_pct: float = Field(default=20.0, ge=0)
    critical_pct: float = Field(default=50.0, ge=0)
    cooldown_minutes: int = Field(default=60)
    enabled: bool = True

class AnomalyConfigManager:
    def __init__(self) -> None:
        self._configs: Dict[str, AnomalyThresholdConfig] = {}

    def set_config(self, config: AnomalyThresholdConfig) -> None:
        self._configs[config.metric] = config

    def get_config(self, metric: str) -> Optional[AnomalyThresholdConfig]:
        return self._configs.get(metric)

    def evaluate(self, metric: str, current: float, baseline: float) -> Dict[str, Any]:
        config = self._configs.get(metric)
        if not config or not config.enabled or baseline <= 0:
            return {"level": "ok", "deviation_pct": 0.0}
        deviation = abs(current - baseline) / baseline * 100
        if deviation >= config.critical_pct:
            return {"level": "critical", "deviation_pct": round(deviation, 1), "threshold": config.critical_pct}
        if deviation >= config.warning_pct:
            return {"level": "warning", "deviation_pct": round(deviation, 1), "threshold": config.warning_pct}
        return {"level": "ok", "deviation_pct": round(deviation, 1)}

class CommitmentPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    commitment_type: str = Field(default="1yr")
    hourly_commitment: float = Field(default=0.0)
    upfront_cost: float = Field(default=0.0)
    effective_rate: float = Field(default=0.0)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: str = Field(default="active")
    estimated_savings_pct: float = Field(default=0.0)

class CommitmentOptimizer:
    def __init__(self) -> None:
        self._plans: Dict[str, CommitmentPlan] = {}

    def create_plan(self, provider: str, commitment_type: str, hourly: float,
                    upfront: float, effective_rate: float, savings_pct: float) -> CommitmentPlan:
        plan = CommitmentPlan(provider=provider, commitment_type=commitment_type,
                              hourly_commitment=hourly, upfront_cost=upfront,
                              effective_rate=effective_rate, estimated_savings_pct=savings_pct)
        self._plans[plan.plan_id] = plan
        return plan

    def get_active(self) -> List[CommitmentPlan]:
        return [p for p in self._plans.values() if p.status == "active"]

    def get_coverage_pct(self, total_hourly_spend: float) -> float:
        committed = sum(p.hourly_commitment for p in self.get_active())
        return round(committed / max(total_hourly_spend, 0.01) * 100, 1)

    def get_savings_projection(self) -> Dict[str, Any]:
        active = self.get_active()
        total_original = sum(p.hourly_commitment for p in active)
        total_effective = sum(p.effective_rate for p in active)
        monthly_savings = (total_original - total_effective) * 730
        return {"monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(monthly_savings * 12, 2),
                "coverage_pct": round(total_original / max(total_original + 0.01, 1) * 100, 1)}

class WasteCategory(BaseModel):
    category: str
    amount: float
    resources: int
    recommendation: str = ""
    potential_savings: float = 0.0

class WasteAnalyzer:
    def __init__(self) -> None:
        self._categories: Dict[str, WasteCategory] = {}

    def add_category(self, category: str, amount: float, resources: int,
                     recommendation: str = "", savings: float = 0.0) -> WasteCategory:
        wc = WasteCategory(category=category, amount=amount, resources=resources,
                           recommendation=recommendation, potential_savings=savings)
        self._categories[category] = wc
        return wc

    def total_waste(self) -> float:
        return round(sum(c.amount for c in self._categories.values()), 2)

    def total_potential_savings(self) -> float:
        return round(sum(c.potential_savings for c in self._categories.values()), 2)

    def get_by_category(self, category: str) -> Optional[WasteCategory]:
        return self._categories.get(category)

    def get_summary(self) -> Dict[str, Any]:
        return {"categories": [c.dict() for c in self._categories.values()],
                "total_waste": self.total_waste(),
                "total_potential_savings": self.total_potential_savings(),
                "waste_pct": round(self.total_waste() / max(self.total_waste() + self.total_potential_savings(), 0.01) * 100, 1)}

class CostForecastPoint(BaseModel):
    date: str
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float

class CostForecaster:
    def __init__(self) -> None:
        self._forecasts: List[CostForecastPoint] = []

    def generate(self, days: int = 90, base_cost: float = 1000.0, volatility: float = 0.1) -> List[CostForecastPoint]:
        self._forecasts = []
        current = base_cost
        for i in range(days):
            change = current * volatility * (random.random() * 2 - 1)
            predicted = round(current + change, 2)
            ci = current * 0.05
            point = CostForecastPoint(
                date=(datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d"),
                predicted_cost=predicted, lower_bound=round(predicted - ci, 2),
                upper_bound=round(predicted + ci, 2),
                confidence=max(0.5, 1.0 - i / days * 0.4),
            )
            self._forecasts.append(point)
            current = predicted
        return self._forecasts

    def get_forecast(self) -> List[CostForecastPoint]:
        return self._forecasts

    def get_aggregate(self) -> Dict[str, Any]:
        if not self._forecasts:
            return {"total_forecast": 0, "avg_daily": 0}
        total = sum(p.predicted_cost for p in self._forecasts)
        return {"total_forecast": round(total, 2),
                "avg_daily": round(total / len(self._forecasts), 2),
                "days": len(self._forecasts),
                "last_prediction": self._forecasts[-1].predicted_cost}
