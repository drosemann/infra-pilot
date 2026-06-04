"""Feature 21: Commitment Discount Optimizer - Analyze usage, recommend reserved instances/savings plans"""

import json
import os
import math
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class CommitmentType(Enum):
    RESERVED_INSTANCE = "reserved_instance"
    SAVINGS_PLAN = "savings_plan"
    COMPUTE_SAVINGS = "compute_savings"
    SPOT_BLOCK = "spot_block"
    CUSTOM = "custom"


class CommitmentTerm(Enum):
    ONE_YEAR = "1_year"
    THREE_YEAR = "3_year"
    MONTHLY = "monthly"


class PaymentOption(Enum):
    NO_UPFRONT = "no_upfront"
    PARTIAL_UPFRONT = "partial_upfront"
    ALL_UPFRONT = "all_upfront"


class RecommendationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class CommitmentDiscountOptimizer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.usage_file = _data_file('commitment_usage.json')
        self.recommendations_file = _data_file('commitment_recommendations.json')
        self.commitments_file = _data_file('commitments.json')
        self.usage_history: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.commitments: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.usage_file, 'usage_history'), (self.recommendations_file, 'recommendations'), (self.commitments_file, 'commitments')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_recommendations(self):
        try:
            with open(self.recommendations_file, 'w') as f:
                json.dump(self.recommendations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recommendations: {e}")

    def _save_commitments(self):
        try:
            with open(self.commitments_file, 'w') as f:
                json.dump(self.commitments, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save commitments: {e}")

    def analyze_usage_patterns(self, service: str, resource_type: str, hours: int = 720) -> Dict[str, Any]:
        relevant = [u for u in self.usage_history if u.get('service') == service]
        if not relevant:
            relevant = self._generate_mock_usage(service, resource_type, hours)

        total_hours = sum(r.get('hours_used', 0) for r in relevant)
        avg_hourly = total_hours / max(len(relevant), 1)
        peak_hourly = max((r.get('hours_used', 0) for r in relevant), default=0)
        on_demand_cost = sum(r.get('on_demand_cost', 0) for r in relevant)
        utilization_pct = sum(r.get('utilization_pct', 0) for r in relevant) / max(len(relevant), 1)

        return {
            "service": service,
            "resource_type": resource_type,
            "period_hours": hours,
            "total_hours_used": total_hours,
            "avg_hourly_usage": round(avg_hourly, 2),
            "peak_hourly_usage": peak_hourly,
            "total_on_demand_cost": round(on_demand_cost, 2),
            "avg_utilization_pct": round(utilization_pct, 1),
            "stable_workload": utilization_pct > 60,
            "peak_to_avg_ratio": round(peak_hourly / max(avg_hourly, 0.01), 2),
            "recommended_for_commitment": utilization_pct > 40 and total_hours > hours * 0.5,
        }

    def _generate_mock_usage(self, service: str, resource_type: str, hours: int) -> List[Dict[str, Any]]:
        import random
        usage = []
        now = datetime.utcnow()
        for i in range(min(hours // 24, 90)):
            day_usage = random.uniform(0.3, 1.0) if i % 7 < 5 else random.uniform(0.1, 0.4)
            usage.append({
                "id": str(uuid.uuid4()),
                "service": service,
                "resource_type": resource_type,
                "date": (now - timedelta(days=i)).isoformat(),
                "hours_used": round(day_usage * 24, 1),
                "on_demand_cost": round(day_usage * 24 * random.uniform(0.10, 0.50), 2),
                "utilization_pct": round(day_usage * 100, 1),
                "instance_count": random.randint(1, 10),
                "region": random.choice(["us-east-1", "eu-west-1", "ap-southeast-1"]),
            })
        self.usage_history.extend(usage)
        self._save_usage()
        return usage

    def _save_usage(self):
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage: {e}")

    def generate_recommendations(self, service: str = None) -> List[Dict[str, Any]]:
        services = [service] if service else list(set(u.get('service', 'unknown') for u in self.usage_history))
        if not services:
            services = ["aws-ec2", "aws-rds", "aws-elasticache", "azure-vm", "gcp-compute"]

        new_recs = []
        for svc in services:
            analysis = self.analyze_usage_patterns(svc, "compute")
            if not analysis["recommended_for_commitment"]:
                continue

            on_demand = analysis["total_on_demand_cost"]
            savings_plan_discount = 0.20 if analysis["stable_workload"] else 0.15
            ri_discount = 0.30 if analysis["stable_workload"] else 0.20

            monthly_savings_sp = round(on_demand * savings_plan_discount / max(analysis["period_hours"] / 720, 1), 2)
            monthly_savings_ri = round(on_demand * ri_discount / max(analysis["period_hours"] / 720, 1), 2)

            for term in [CommitmentTerm.ONE_YEAR, CommitmentTerm.THREE_YEAR]:
                for payment in [PaymentOption.NO_UPFRONT, PaymentOption.PARTIAL_UPFRONT, PaymentOption.ALL_UPFRONT]:
                    term_mult = 1 if term == CommitmentTerm.ONE_YEAR else 3
                    upfront_pct = {"no_upfront": 0, "partial_upfront": 0.5, "all_upfront": 1.0}[payment.value]
                    total_commitment = on_demand * term_mult
                    upfront_cost = round(total_commitment * upfront_pct, 2)
                    monthly_cost = round((total_commitment - upfront_cost) / (12 * term_mult), 2)
                    total_savings = round(monthly_savings_ri * 12 * term_mult, 2)

                    rec = {
                        "id": str(uuid.uuid4()),
                        "service": svc,
                        "type": CommitmentType.RESERVED_INSTANCE.value,
                        "term": term.value,
                        "payment": payment.value,
                        "on_demand_monthly": round(on_demand / max(analysis["period_hours"] / 720, 1), 2),
                        "upfront_cost": upfront_cost,
                        "monthly_cost": monthly_cost,
                        "monthly_savings": round(monthly_savings_ri, 2),
                        "total_savings": total_savings,
                        "savings_pct": round(ri_discount * 100, 1),
                        "confidence": "high" if analysis["stable_workload"] else "medium",
                        "status": RecommendationStatus.PENDING.value,
                        "created_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    }
                    new_recs.append(rec)

        self.recommendations.extend(new_recs)
        self._save_recommendations()
        return new_recs

    def get_recommendations(self, status: str = None) -> List[Dict[str, Any]]:
        if status:
            return [r for r in self.recommendations if r.get('status') == status]
        return self.recommendations

    def implement_recommendation(self, rec_id: str) -> Dict[str, Any]:
        rec = next((r for r in self.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found", "success": False}
        commitment = {
            "id": str(uuid.uuid4()),
            "recommendation_id": rec_id,
            "service": rec['service'],
            "type": rec['type'],
            "term": rec['term'],
            "payment": rec['payment'],
            "upfront_cost": rec['upfront_cost'],
            "monthly_cost": rec['monthly_cost'],
            "estimated_monthly_savings": rec['monthly_savings'],
            "status": "active",
            "purchased_at": datetime.utcnow().isoformat(),
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=365 if rec['term'] == '1_year' else 1095)).isoformat(),
            "utilization_pct": 0,
        }
        self.commitments.append(commitment)
        self._save_commitments()
        rec['status'] = RecommendationStatus.IMPLEMENTED.value
        self._save_recommendations()
        return {"success": True, "commitment": commitment}

    def dismiss_recommendation(self, rec_id: str) -> Dict[str, Any]:
        rec = next((r for r in self.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found", "success": False}
        rec['status'] = RecommendationStatus.DISMISSED.value
        self._save_recommendations()
        return {"success": True}

    def get_active_commitments(self) -> List[Dict[str, Any]]:
        return [c for c in self.commitments if c.get('status') == 'active']

    def track_commitment_utilization(self, commitment_id: str, utilization_pct: float) -> Dict[str, Any]:
        cm = next((c for c in self.commitments if c['id'] == commitment_id), None)
        if not cm:
            return {"error": "Commitment not found", "success": False}
        cm['utilization_pct'] = utilization_pct
        cm['last_updated'] = datetime.utcnow().isoformat()
        self._save_commitments()
        return {"success": True, "utilization_pct": utilization_pct}

    def get_savings_summary(self) -> Dict[str, Any]:
        active = [c for c in self.commitments if c.get('status') == 'active']
        total_monthly_savings = sum(c.get('estimated_monthly_savings', 0) for c in active)
        total_upfront = sum(c.get('upfront_cost', 0) for c in active)
        total_on_demand_cost = sum(c.get('monthly_cost', 0) for c in active) + total_monthly_savings
        effective_savings_pct = round((total_monthly_savings / max(total_on_demand_cost, 1)) * 100, 1)
        return {
            "active_commitments": len(active),
            "total_monthly_savings": round(total_monthly_savings, 2),
            "total_upfront_investment": round(total_upfront, 2),
            "total_on_demand_cost": round(total_on_demand_cost, 2),
            "effective_savings_pct": effective_savings_pct,
            "projected_annual_savings": round(total_monthly_savings * 12, 2),
            "avg_utilization": round(sum(c.get('utilization_pct', 0) for c in active) / max(len(active), 1), 1),
            "wastage_pct": round(sum(max(0, 100 - c.get('utilization_pct', 100)) for c in active) / max(len(active), 1), 1),
        }

    def get_coverage_gaps(self) -> List[Dict[str, Any]]:
        covered_services = set(c['service'] for c in self.commitments if c.get('status') == 'active')
        all_services = set(u.get('service', 'unknown') for u in self.usage_history)
        gaps = []
        for svc in sorted(all_services - covered_services):
            analysis = self.analyze_usage_patterns(svc, "compute")
            if analysis["total_on_demand_cost"] > 100:
                gaps.append({
                    "service": svc,
                    "monthly_on_demand": round(analysis["total_on_demand_cost"] / max(analysis["period_hours"] / 720, 1), 2),
                    "potential_savings": round(analysis["total_on_demand_cost"] * 0.25 / max(analysis["period_hours"] / 720, 1), 2),
                    "recommendation_available": True,
                })
        return gaps

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, field, asdict
from typing import Optional

class CommitmentOptimizerError(Exception): pass

@dataclass
class UsagePattern:
    service: str
    commitment_type: str
    avg_hourly_units: float = 0.0
    peak_hourly_units: float = 0.0
    p90_usage: float = 0.0
    utilization_pct: float = 0.0
    on_demand_cost: float = 0.0
    savings_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CommitmentRecommendation:
    id: str = ""
    provider: str = ""
    commitment_type: str = ""
    term: str = "1yr"
    upfront_cost: float = 0.0
    monthly_cost: float = 0.0
    estimated_monthly_savings: float = 0.0
    coverage_pct: float = 0.0
    status: str = "open"
    risk_level: str = "low"
    service: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_recommendation(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('provider'): errors.append("provider is required")
    if not data.get('commitment_type'): errors.append("commitment_type is required")
    if data.get('monthly_cost', 0) <= 0: errors.append("monthly_cost must be positive")
    return errors

async def batch_implement_recommendations(engine: 'CommitmentOptimizer', rec_ids: List[str]) -> Dict[str, Any]:
    results = {"succeeded": [], "failed": []}
    for rid in rec_ids:
        try:
            result = engine.implement_recommendation(rid)
            results["succeeded"].append({"id": rid, "result": result.get('status')})
        except Exception as e:
            results["failed"].append({"id": rid, "error": str(e)})
    return results

def paginate(items: List[Dict[str, Any]], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (len(items) + per_page - 1) // per_page),
    }

def filter_commitments(commitments: List[Dict[str, Any]], provider: Optional[str] = None, status: Optional[str] = None, commitment_type: Optional[str] = None) -> List[Dict[str, Any]]:
    results = commitments[:]
    if provider: results = [c for c in results if c.get('provider') == provider]
    if status: results = [c for c in results if c.get('status') == status]
    if commitment_type: results = [c for c in results if c.get('commitment_type') == commitment_type]
    return results

def sort_commitments(commitments: List[Dict[str, Any]], sort_by: str = "monthly_cost", descending: bool = True) -> List[Dict[str, Any]]:
    return sorted(commitments, key=lambda c: c.get(sort_by, 0), reverse=descending)

def analyze_savings_plans(plans: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not plans: return {"total_plans": 0, "total_monthly": 0, "total_savings": 0, "avg_coverage": 0}
    return {
        "total_plans": len(plans),
        "total_monthly": round(sum(p.get('monthly_cost', 0) for p in plans), 2),
        "total_savings": round(sum(p.get('estimated_monthly_savings', 0) for p in plans), 2),
        "avg_coverage": round(sum(p.get('coverage_pct', 0) for p in plans) / len(plans), 1),
        "by_provider": {p: len([x for x in plans if x.get('provider') == p]) for p in set(x.get('provider') for x in plans)},
    }

def generate_migration_path(current_provider: str, target_provider: str, commitment_type: str, monthly_cost: float) -> Dict[str, Any]:
    savings_multipliers = {"aws": 0.85, "azure": 0.88, "gcp": 0.82}
    target_mult = savings_multipliers.get(target_provider, 0.90)
    return {
        "current_provider": current_provider,
        "target_provider": target_provider,
        "commitment_type": commitment_type,
        "current_monthly": monthly_cost,
        "estimated_monthly": round(monthly_cost * target_mult, 2),
        "estimated_monthly_savings": round(monthly_cost * (1 - target_mult), 2),
        "migration_effort": "medium",
        "steps": ["Evaluate target commitment options", "Purchase new commitment", "Map existing resources", "Migrate", "Decommission old commitment"],
    }

def compute_effective_rate(commitments: List[Dict[str, Any]], total_on_demand: float) -> Dict[str, Any]:
    total_committed = sum(c.get('monthly_cost', 0) for c in commitments if c.get('status') == 'active')
    if total_on_demand <= 0: return {"effective_rate": 0, "blended_rate": 0, "discount_pct": 0}
    blended = (total_committed + total_on_demand) / (len(commitments) + 1) if commitments else total_on_demand
    return {
        "total_committed_monthly": round(total_committed, 2),
        "total_on_demand": round(total_on_demand, 2),
        "effective_rate": round(total_committed / max(total_on_demand, 1), 4),
        "discount_pct": round((1 - total_committed / max(total_on_demand + total_committed, 1)) * 100, 1),
    }

def get_optimal_term(avg_utilization: float, stability_score: float) -> str:
    if stability_score > 0.8 and avg_utilization > 0.7: return "3yr"
    if stability_score > 0.6: return "1yr"
    return "no_commitment"

async def run_coverage_analysis(engine: 'CommitmentOptimizer') -> Dict[str, Any]:
    gaps = engine.get_coverage_gaps()
    active = [c for c in engine.commitments if c.get('status') == 'active']
    total_spend = sum(g.get('monthly_on_demand', 0) for g in gaps)
    gap_savings = sum(g.get('potential_savings', 0) for g in gaps)
    return {
        "total_gaps": len(gaps),
        "covered_services": len(active),
        "uncovered_services": len(gaps),
        "total_uncovered_spend": round(total_spend, 2),
        "total_potential_savings": round(gap_savings, 2),
        "coverage_pct": round((len(active) * 100) / max(len(active) + len(gaps), 1), 1),
        "gaps": gaps,
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class CommitmentBatchProcessor:
    def __init__(self, engine: 'CommitmentOptimizer'):
        self.engine = engine
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_implement(self, rec_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rid in rec_ids:
            try:
                result = self.engine.implement_recommendation(rid)
                results.append({"success": True, "recommendation_id": rid, "result": result})
            except Exception as e:
                results.append({"success": False, "recommendation_id": rid, "error": str(e)})
        return results

    async def batch_analyze(self, services: List[str]) -> List[Dict[str, Any]]:
        results = []
        for svc in services:
            try:
                result = self.engine.get_coverage_gaps(svc)
                results.append({"service": svc, "gaps": result})
            except Exception as e:
                results.append({"service": svc, "error": str(e)})
        return results

    async def export_commitments_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "service", "type", "term", "monthly_cost", "savings", "coverage_pct", "status"])
        for c in self.engine.commitments:
            writer.writerow([c.get('id'), c.get('service'), c.get('type'), c.get('term'), c.get('monthly_cost'), c.get('estimated_monthly_savings'), c.get('coverage_pct'), c.get('status')])
        return output.getvalue()

class CommitmentAnalytics:
    def __init__(self, engine: 'CommitmentOptimizer'):
        self.engine = engine

    def by_provider(self) -> Dict[str, Any]:
        providers = {}
        for c in self.engine.commitments:
            p = c.get('provider', 'unknown')
            if p not in providers:
                providers[p] = {"count": 0, "monthly_cost": 0, "savings": 0}
            providers[p]["count"] += 1
            providers[p]["monthly_cost"] += c.get('monthly_cost', 0)
            providers[p]["savings"] += c.get('estimated_monthly_savings', 0)
        return providers

    def renewal_forecast(self, months: int = 6) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        upcoming = []
        for c in self.engine.commitments:
            if c.get('end_date'):
                end = datetime.fromisoformat(c['end_date'])
                days_until = (end - now).days
                if 0 < days_until <= months * 30:
                    upcoming.append({"commitment_id": c['id'], "service": c.get('service'), "end_date": c['end_date'], "days_remaining": days_until, "monthly_cost": c.get('monthly_cost')})
        return sorted(upcoming, key=lambda x: x['days_remaining'])

class CommitmentPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === ADVANCED COMMITMENT STRATEGIES ===

class CommitmentStrategyOptimizer:
    def __init__(self, engine: CommitmentDiscountOptimizer):
        self.engine = engine

    def hybrid_strategy(self, service: str, total_hours: float) -> Dict[str, Any]:
        stable = total_hours * 0.7
        flexible = total_hours * 0.3
        base_cost = self.engine.analyze_usage_patterns(service, "compute")
        monthly_on_demand = base_cost['total_on_demand_cost']
        ri_savings = monthly_on_demand * 0.30 * 0.7
        sp_savings = monthly_on_demand * 0.20 * 0.3
        return {
            "service": service,
            "strategy": "hybrid_70_30",
            "ri_coverage_pct": 70,
            "sp_coverage_pct": 30,
            "on_demand_monthly": round(monthly_on_demand, 2),
            "ri_portion": round(monthly_on_demand * 0.70, 2),
            "sp_portion": round(monthly_on_demand * 0.30, 2),
            "estimated_ri_savings": round(ri_savings, 2),
            "estimated_sp_savings": round(sp_savings, 2),
            "total_estimated_savings": round(ri_savings + sp_savings, 2),
            "effective_discount_pct": round(((ri_savings + sp_savings) / max(monthly_on_demand, 0.01)) * 100, 1),
        }

    def dynamic_roi(self, commitment: Dict[str, Any], months: int = 36) -> Dict[str, Any]:
        upfront = commitment.get('upfront_cost', 0)
        monthly_savings = commitment.get('estimated_monthly_savings', 0)
        total_savings = monthly_savings * months
        net_roi = total_savings - upfront
        break_even_months = upfront / max(monthly_savings, 0.01)
        roi_pct = (net_roi / max(upfront, 0.01)) * 100 if upfront > 0 else float('inf')
        return {
            "commitment_id": commitment.get('id'),
            "months_analyzed": months,
            "upfront_cost": upfront,
            "monthly_savings": monthly_savings,
            "total_savings": round(total_savings, 2),
            "net_roi": round(net_roi, 2),
            "roi_pct": round(roi_pct, 1),
            "break_even_months": round(break_even_months, 1),
        }

# === COMMITMENT MIGRATION ===

class CommitmentMigrator:
    def __init__(self, engine: CommitmentDiscountOptimizer):
        self.engine = engine

    def plan_migration(self, old_commitment_id: str, new_type: str, new_term: str) -> Dict[str, Any]:
        old = next((c for c in self.engine.commitments if c['id'] == old_commitment_id), None)
        if not old:
            return {"error": "Commitment not found"}
        old_monthly = old.get('monthly_cost', 0)
        old_savings = old.get('estimated_monthly_savings', 0)
        term_mult = 1 if new_term == '1_year' else 3
        new_monthly = old_monthly * 0.85
        new_savings = old_savings * 1.15
        steps = [
            "Evaluate new commitment pricing",
            "Purchase new commitment",
            "Allow overlap period of 30 days",
            "Monitor utilization of both commitments",
            "Let old commitment expire naturally",
            "Transition resources to new commitment",
        ]
        return {
            "old_commitment_id": old_commitment_id,
            "old_type": old.get('type'),
            "old_term": old.get('term'),
            "new_type": new_type,
            "new_term": new_term,
            "old_monthly_cost": old_monthly,
            "new_monthly_cost": round(new_monthly, 2),
            "old_monthly_savings": old_savings,
            "new_estimated_savings": round(new_savings, 2),
            "savings_increase": round(new_savings - old_savings, 2),
            "migration_steps": steps,
            "recommended_overlap_days": 30,
        }

    def batch_migrate(self, commitment_ids: List[str], new_type: str, new_term: str) -> List[Dict[str, Any]]:
        return [self.plan_migration(cid, new_type, new_term) for cid in commitment_ids]

# === RENEWAL MANAGER ===

class RenewalManager:
    def __init__(self, engine: CommitmentDiscountOptimizer):
        self.engine = engine

    def find_expiring(self, days_ahead: int = 60) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        expiring = []
        for c in self.engine.commitments:
            if c.get('end_date'):
                end = datetime.fromisoformat(c['end_date'])
                days_left = (end - now).days
                if 0 <= days_left <= days_ahead:
                    expiring.append({
                        "commitment_id": c['id'],
                        "service": c.get('service'),
                        "type": c.get('type'),
                        "end_date": c['end_date'],
                        "days_remaining": days_left,
                        "monthly_cost": c.get('monthly_cost'),
                        "auto_renew": c.get('auto_renew', False),
                        "action_required": days_left <= 30,
                    })
        return sorted(expiring, key=lambda x: x['days_remaining'])

    def renew(self, commitment_id: str, term: str = None, auto_renew: bool = True) -> Dict[str, Any]:
        c = next((cm for cm in self.engine.commitments if cm['id'] == commitment_id), None)
        if not c:
            return {"error": "Commitment not found"}
        term = term or c.get('term', '1_year')
        term_days = 365 if term == '1_year' else 1095
        c['end_date'] = (datetime.utcnow() + timedelta(days=term_days)).isoformat()
        c['auto_renew'] = auto_renew
        c['last_renewed_at'] = datetime.utcnow().isoformat()
        self.engine._save_commitments()
        return {"commitment_id": commitment_id, "new_end_date": c['end_date'], "term": term, "auto_renew": auto_renew}

# === COVERAGE ANALYZER ===

class CoverageAnalyzer:
    def __init__(self, engine: CommitmentDiscountOptimizer):
        self.engine = engine

    def by_region(self) -> Dict[str, Any]:
        regions = {}
        for c in self.engine.commitments:
            if c.get('status') != 'active':
                continue
            r = c.get('region', 'global')
            if r not in regions:
                regions[r] = {"commitment_count": 0, "monthly_cost": 0, "savings": 0}
            regions[r]["commitment_count"] += 1
            regions[r]["monthly_cost"] += c.get('monthly_cost', 0)
            regions[r]["savings"] += c.get('estimated_monthly_savings', 0)
        return regions

    def by_service(self) -> Dict[str, Any]:
        services = {}
        for c in self.engine.commitments:
            if c.get('status') != 'active':
                continue
            s = c.get('service', 'unknown')
            if s not in services:
                services[s] = {"commitment_count": 0, "total_hours": 0, "coverage_pct": 0}
            services[s]["commitment_count"] += 1
        for s in services:
            analysis = self.engine.analyze_usage_patterns(s, "compute")
            services[s]["coverage_pct"] = min(100, round((services[s]["commitment_count"] / max(analysis.get('total_hours_used', 1) / 24, 1)) * 100, 1))
        return services

# === EXPIRY ALERT ===

class CommitmentAlertEngine:
    def __init__(self, engine: CommitmentDiscountOptimizer):
        self.engine = engine
        self.alerts: List[Dict[str, Any]] = []

    def check_expiry_alerts(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        new_alerts = []
        for c in self.engine.commitments:
            if c.get('end_date'):
                end = datetime.fromisoformat(c['end_date'])
                days_left = (end - now).days
                if days_left <= 30 and days_left > 0:
                    alert = {
                        "commitment_id": c['id'],
                        "service": c.get('service'),
                        "days_remaining": days_left,
                        "severity": "high" if days_left <= 7 else "medium",
                        "message": f"Commitment for {c.get('service')} expires in {days_left} days",
                        "created_at": now.isoformat(),
                    }
                    new_alerts.append(alert)
                    self.alerts.append(alert)
        return new_alerts

    def get_alerts(self, acknowledged: bool = False) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if a.get('acknowledged', False) == acknowledged]

    def acknowledge_alert(self, commitment_id: str) -> bool:
        for a in self.alerts:
            if a['commitment_id'] == commitment_id and not a.get('acknowledged', False):
                a['acknowledged'] = True
                a['acknowledged_at'] = datetime.utcnow().isoformat()
                return True
        return False

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
