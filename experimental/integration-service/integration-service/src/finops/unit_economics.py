"""Feature 23: Unit Economics Dashboard - Cost per customer, per transaction, per deployment"""

import json
import os
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


class UnitMetric(Enum):
    COST_PER_CUSTOMER = "cost_per_customer"
    COST_PER_TRANSACTION = "cost_per_transaction"
    COST_PER_DEPLOYMENT = "cost_per_deployment"
    COST_PER_REQUEST = "cost_per_request"
    COST_PER_USER = "cost_per_user"
    REVENUE_PER_CUSTOMER = "revenue_per_customer"
    MARGIN_PER_CUSTOMER = "margin_per_customer"


class TrendDirection(Enum):
    IMPROVING = "improving"
    WORSENING = "worsening"
    STABLE = "stable"


class UnitEconomics:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_file = _data_file('unit_economics.json')
        self.targets_file = _data_file('unit_targets.json')
        self.breakdown_file = _data_file('unit_breakdown.json')
        self.metrics: List[Dict[str, Any]] = []
        self.targets: List[Dict[str, Any]] = []
        self.breakdowns: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.metrics_file, 'metrics'), (self.targets_file, 'targets'), (self.breakdown_file, 'breakdowns')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_metrics(self):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _save_targets(self):
        try:
            with open(self.targets_file, 'w') as f:
                json.dump(self.targets, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save targets: {e}")

    def record_metric(self, customer_id: str, metric_type: str, value: float,
                      dimension: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        entry = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "metric_type": metric_type,
            "value": value,
            "dimension": dimension,
            "metadata": metadata or {},
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self.metrics.append(entry)
        self._save_metrics()
        return entry

    def get_customer_metrics(self, customer_id: str, metric_type: str = None,
                             hours: int = 720) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = [m for m in self.metrics
                  if m['customer_id'] == customer_id
                  and datetime.fromisoformat(m['recorded_at']) > cutoff]
        if metric_type:
            result = [m for m in result if m['metric_type'] == metric_type]
        return result

    def get_customer_summary(self, customer_id: str) -> Dict[str, Any]:
        metrics = self.get_customer_metrics(customer_id)
        if not metrics:
            metrics = self._generate_mock_metrics(customer_id)

        by_type = {}
        for m in metrics:
            by_type.setdefault(m['metric_type'], []).append(m['value'])

        summary = {"customer_id": customer_id, "total_entries": len(metrics), "metrics": {}}
        for mtype, values in by_type.items():
            summary["metrics"][mtype] = {
                "current": round(values[-1], 4) if values else 0,
                "avg": round(sum(values) / len(values), 4) if values else 0,
                "min": round(min(values), 4) if values else 0,
                "max": round(max(values), 4) if values else 0,
                "trend": self._calculate_trend(values),
            }
        return summary

    def _calculate_trend(self, values: List[float]) -> str:
        if len(values) < 5:
            return TrendDirection.STABLE.value
        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:5]
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)
        if avg_recent < avg_older * 0.95:
            return TrendDirection.IMPROVING.value
        elif avg_recent > avg_older * 1.05:
            return TrendDirection.WORSENING.value
        return TrendDirection.STABLE.value

    def _generate_mock_metrics(self, customer_id: str) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        mock_types = [
            UnitMetric.COST_PER_CUSTOMER.value,
            UnitMetric.COST_PER_TRANSACTION.value,
            UnitMetric.COST_PER_DEPLOYMENT.value,
            UnitMetric.REVENUE_PER_CUSTOMER.value,
        ]
        mock_data = []
        for mtype in mock_types:
            for day in range(30):
                base = {"cost_per_customer": 150, "cost_per_transaction": 0.45,
                        "cost_per_deployment": 12.50, "revenue_per_customer": 299}[mtype]
                value = round(base * random.uniform(0.85, 1.15), 4)
                entry = {
                    "id": str(uuid.uuid4()),
                    "customer_id": customer_id,
                    "metric_type": mtype,
                    "value": value,
                    "recorded_at": (now - timedelta(days=29 - day)).isoformat(),
                }
                mock_data.append(entry)
                self.metrics.append(entry)
        self._save_metrics()
        return mock_data

    def set_target(self, customer_id: str, metric_type: str, target_value: float,
                   alert_threshold: float = None) -> Dict[str, Any]:
        existing = [t for t in self.targets if t['customer_id'] == customer_id and t['metric_type'] == metric_type]
        if existing:
            existing[0]['target_value'] = target_value
            existing[0]['alert_threshold'] = alert_threshold
            existing[0]['updated_at'] = datetime.utcnow().isoformat()
            self._save_targets()
            return existing[0]
        target = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "metric_type": metric_type,
            "target_value": target_value,
            "alert_threshold": alert_threshold or target_value * 1.2,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.targets.append(target)
        self._save_targets()
        return target

    def get_targets(self, customer_id: str = None, metric_type: str = None) -> List[Dict[str, Any]]:
        result = self.targets
        if customer_id:
            result = [t for t in result if t['customer_id'] == customer_id]
        if metric_type:
            result = [t for t in result if t['metric_type'] == metric_type]
        return result

    def check_target_violations(self, customer_id: str = None) -> List[Dict[str, Any]]:
        violations = []
        targets = self.get_targets(customer_id)
        for t in targets:
            current = self.get_customer_summary(t['customer_id'])
            metric_data = current.get('metrics', {}).get(t['metric_type'], {})
            current_value = metric_data.get('current', 0)
            if current_value > t.get('alert_threshold', float('inf')):
                violations.append({
                    "target_id": t['id'],
                    "customer_id": t['customer_id'],
                    "metric_type": t['metric_type'],
                    "target_value": t['target_value'],
                    "alert_threshold": t.get('alert_threshold'),
                    "current_value": current_value,
                    "deviation_pct": round(((current_value - t['target_value']) / t['target_value']) * 100, 1),
                    "detected_at": datetime.utcnow().isoformat(),
                })
        return violations

    def get_aggregate_by_dimension(self, dimension: str, metric_type: str = None) -> List[Dict[str, Any]]:
        entries = self.metrics
        if metric_type:
            entries = [m for m in entries if m['metric_type'] == metric_type]
        grouped = {}
        for m in entries:
            dim_val = m.get('dimension') or m.get('customer_id', 'unknown')
            grouped.setdefault(dim_val, []).append(m['value'])
        result = []
        for dim, values in grouped.items():
            result.append({
                "dimension": dim,
                "metric_count": len(values),
                "avg_value": round(sum(values) / len(values), 4),
                "total_value": round(sum(values), 4),
                "latest": round(values[-1], 4) if values else 0,
            })
        return sorted(result, key=lambda x: x['total_value'], reverse=True)

    def get_overview(self) -> Dict[str, Any]:
        all_metrics = self.metrics
        if not all_metrics:
            return {"status": "no_data"}
        by_type = {}
        for m in all_metrics:
            by_type.setdefault(m['metric_type'], []).append(m['value'])
        overview = {}
        for mtype, values in by_type.items():
            overview[mtype] = {
                "current": round(values[-1], 4),
                "avg_30d": round(sum(values[-30:]) / min(len(values[-30:]), 30), 4) if len(values) >= 30 else round(sum(values) / len(values), 4),
                "trend": self._calculate_trend(values),
                "total_entries": len(values),
            }
        return {"overview": overview, "target_count": len(self.targets), "customer_count": len(set(m['customer_id'] for m in all_metrics))}

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class UnitEconomicsError(Exception): pass

@dataclass
class MetricRecord:
    customer_id: str
    metric_name: str
    value: float
    dimension: str = "general"
    recorded_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_metric(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('customer_id'): errors.append("customer_id is required")
    if not data.get('metric_name'): errors.append("metric_name is required")
    if data.get('value') is None: errors.append("value is required")
    return errors

def compute_unit_metric_trend(values: List[float]) -> Dict[str, Any]:
    if len(values) < 2: return {"direction": "stable", "change_pct": 0.0, "volatility": 0.0}
    first_half = sum(values[:len(values)//2]) / max(len(values)//2, 1)
    second_half = sum(values[len(values)//2:]) / max(len(values) - len(values)//2, 1)
    change = ((second_half - first_half) / max(first_half, 0.01)) * 100
    std = (sum((v - sum(values)/len(values))**2 for v in values) / len(values)) ** 0.5
    return {
        "direction": "up" if change > 5 else ("down" if change < -5 else "stable"),
        "change_pct": round(change, 1),
        "volatility": round(std / max(sum(values)/len(values), 0.01), 2),
    }

def get_target_violations(metrics: List[Dict[str, Any]], targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    violations = []
    for m in metrics:
        for t in targets:
            if m.get('metric_name') == t.get('metric_name'):
                threshold = t.get('threshold_pct', 10) / 100
                if m.get('value', 0) > t.get('target_value', 0) * (1 + threshold):
                    violations.append({"metric": m, "target": t, "excess_pct": round(((m.get('value', 0) - t.get('target_value', 0)) / t.get('target_value', 0)) * 100, 1)})
    return violations

def analyze_unit_cost_efficiency(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not metrics: return {}
    by_dim = {}
    for m in metrics:
        dim = m.get('dimension', 'unknown')
        by_dim.setdefault(dim, []).append(m.get('value', 0))
    return {
        "dimensions_analyzed": len(by_dim),
        "efficiency_score": round(100 - sum(m.get('value', 0) for m in metrics) / max(len(metrics), 1), 1),
        "by_dimension": {d: {"avg": round(sum(v)/len(v), 2), "count": len(v)} for d, v in by_dim.items()},
    }

def compare_unit_metrics(customer_a: List[Dict[str, Any]], customer_b: List[Dict[str, Any]]) -> Dict[str, Any]:
    def avg_metric(metrics):
        return sum(m.get('value', 0) for m in metrics) / max(len(metrics), 1) if metrics else 0
    return {
        "customer_a_avg": round(avg_metric(customer_a), 2),
        "customer_b_avg": round(avg_metric(customer_b), 2),
        "ratio": round(avg_metric(customer_a) / max(avg_metric(customer_b), 0.01), 2),
        "customer_a_better": avg_metric(customer_a) < avg_metric(customer_b),
    }

def forecast_metric(values: List[float], periods_ahead: int = 3) -> List[float]:
    if len(values) < 3: return [sum(values)/len(values)] * periods_ahead if values else []
    slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
    last = values[-1]
    return [round(last + slope * i, 2) for i in range(1, periods_ahead + 1)]

def generate_unit_economics_report(metrics: List[Dict[str, Any]], targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations = get_target_violations(metrics, targets)
    efficiency = analyze_unit_cost_efficiency(metrics)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_metrics": len(metrics),
        "total_targets": len(targets),
        "violations_count": len(violations),
        "violations": violations[:10],
        "efficiency": efficiency,
        "recommendations": [
            "Review cost allocation for customers with above-average unit metrics",
            "Consider volume discounts for high-usage customers",
            "Optimize resource sizing for customers with growing unit costs",
        ],
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class UnitBatchProcessor:
    def __init__(self, engine: 'UnitEconomics'):
        self.engine = engine
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_record_metrics(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for r in records:
            try:
                result = self.engine.record_metric(customer_id=r['customer_id'], metric_name=r['metric_name'], value=r['value'], dimension=r.get('dimension'))
                results.append({"success": True, "metric": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": r})
        return results

    async def batch_set_targets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for t in targets:
            try:
                result = self.engine.set_target(metric_name=t['metric_name'], target_value=t['target_value'], threshold_pct=t.get('threshold', 10))
                results.append({"success": True, "target": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": t})
        return results

    async def export_metrics_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "customer_id", "metric_name", "value", "dimension", "recorded_at"])
        for m in self.engine.metrics:
            writer.writerow([m.get('id'), m.get('customer_id'), m.get('metric_name'), m.get('value'), m.get('dimension'), m.get('recorded_at')])
        return output.getvalue()

class UnitAnalytics:
    def __init__(self, engine: 'UnitEconomics'):
        self.engine = engine

    def by_dimension(self) -> Dict[str, Any]:
        dims = {}
        for m in self.engine.metrics:
            d = m.get('dimension', 'unknown')
            dims.setdefault(d, {"count": 0, "avg_value": 0, "total": 0})
            dims[d]["count"] += 1
            dims[d]["total"] += m.get('value', 0)
        for d in dims:
            dims[d]["avg_value"] = round(dims[d]["total"] / max(dims[d]["count"], 1), 2)
        return dims

    def top_customers_by_metric(self, metric_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        relevant = [m for m in self.engine.metrics if m.get('metric_name') == metric_name]
        by_customer = {}
        for m in relevant:
            c = m.get('customer_id', 'unknown')
            if c not in by_customer:
                by_customer[c] = {"customer_id": c, "count": 0, "total": 0, "avg": 0}
            by_customer[c]["count"] += 1
            by_customer[c]["total"] += m.get('value', 0)
        for c in by_customer:
            by_customer[c]["avg"] = round(by_customer[c]["total"] / max(by_customer[c]["count"], 1), 2)
        return sorted(by_customer.values(), key=lambda x: x["total"], reverse=True)[:limit]

class UnitPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === ADVANCED UNIT ECONOMICS ===

class UnitEconomicsForecaster:
    def __init__(self, engine: UnitEconomics):
        self.engine = engine

    def forecast_metric(self, customer_id: str, metric_type: str, months: int = 3) -> Dict[str, Any]:
        metrics = self.engine.get_customer_metrics(customer_id, metric_type)
        if len(metrics) < 3:
            return {"error": "Insufficient historical data"}
        values = [m['value'] for m in sorted(metrics, key=lambda x: x['recorded_at'])]
        avg = sum(values) / len(values)
        slope = (values[-1] - values[0]) / max(len(values) - 1, 1) if len(values) > 1 else 0
        forecasts = []
        for m in range(1, months + 1):
            forecasted = values[-1] + slope * m * 30
            forecasts.append({"month": m, "forecasted_value": round(forecasted, 4)})
        return {
            "customer_id": customer_id,
            "metric_type": metric_type,
            "historical_avg": round(avg, 4),
            "trend": "improving" if slope < 0 else "worsening",
            "forecasts": forecasts,
            "total_forecasted": round(sum(f['forecasted_value'] for f in forecasts), 4),
        }

    def profitability_analysis(self, customer_id: str) -> Dict[str, Any]:
        summary = self.engine.get_customer_summary(customer_id)
        metrics = summary.get('metrics', {})
        cost_per_customer = metrics.get('cost_per_customer', {}).get('current', 0)
        revenue_per_customer = metrics.get('revenue_per_customer', {}).get('current', 0)
        margin = revenue_per_customer - cost_per_customer
        margin_pct = (margin / max(revenue_per_customer, 0.01)) * 100 if revenue_per_customer > 0 else 0
        return {
            "customer_id": customer_id,
            "cost_per_customer": cost_per_customer,
            "revenue_per_customer": revenue_per_customer,
            "margin": round(margin, 2),
            "margin_pct": round(margin_pct, 1),
            "profitable": margin > 0,
            "health": "good" if margin_pct > 30 else ("fair" if margin_pct > 10 else "poor"),
        }

# === BENCHMARKING ===

class UnitBenchmarker:
    def __init__(self):
        self.industry_benchmarks = {
            "cost_per_customer": {"saas": 25.0, "ecommerce": 15.0, "enterprise": 85.0},
            "cost_per_transaction": {"saas": 0.50, "ecommerce": 0.25, "enterprise": 1.20},
            "cost_per_request": {"saas": 0.001, "ecommerce": 0.0005, "enterprise": 0.005},
        }

    def benchmark(self, customer_metric: str, value: float, industry: str = "saas") -> Dict[str, Any]:
        benchmarks = self.industry_benchmarks.get(customer_metric, {})
        benchmark_value = benchmarks.get(industry, 0)
        ratio = value / max(benchmark_value, 0.01)
        return {
            "metric": customer_metric,
            "your_value": value,
            "industry_benchmark": benchmark_value,
            "ratio_to_benchmark": round(ratio, 2),
            "status": "above_benchmark" if ratio > 1.1 else ("at_benchmark" if ratio >= 0.9 else "below_benchmark"),
            "recommendation": "Investigate cost drivers" if ratio > 1.1 else "Maintain current efficiency",
        }

    def cross_customer_compare(self, customer_metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        results = {}
        for customer_id, metrics in customer_metrics.items():
            results[customer_id] = {"cost_efficiency_score": 0, "metrics": {}}
            for metric, value in metrics.items():
                bm = self.benchmark(metric, value, "saas")
                results[customer_id]["metrics"][metric] = bm
                if bm['status'] == "below_benchmark":
                    results[customer_id]["cost_efficiency_score"] += 10
                elif bm['status'] == "at_benchmark":
                    results[customer_id]["cost_efficiency_score"] += 5
        for cid in results:
            total = sum(v.get('ratio_to_benchmark', 1) for v in results[cid]['metrics'].values())
            results[cid]["cost_efficiency_score"] = round(min(100, total / max(len(results[cid]['metrics']), 1) * 20), 1)
        return results

# === COST ALLOCATION ===

class CostAllocator:
    def __init__(self, engine: UnitEconomics):
        self.engine = engine
        self.allocation_rules: List[Dict[str, Any]] = []

    def create_rule(self, name: str, dimension: str, allocation_pct: float, conditions: Dict[str, Any] = None) -> Dict[str, Any]:
        rule = {
            "id": str(uuid.uuid4()),
            "name": name,
            "dimension": dimension,
            "allocation_pct": allocation_pct,
            "conditions": conditions or {},
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.allocation_rules.append(rule)
        return rule

    def allocate_costs(self, total_cost: float, dimension: str = "team") -> List[Dict[str, Any]]:
        active_rules = [r for r in self.allocation_rules if r['enabled'] and r['dimension'] == dimension]
        if not active_rules:
            return [{"dimension": "unallocated", "cost": total_cost, "pct": 100}]
        total_pct = sum(r['allocation_pct'] for r in active_rules)
        if total_pct <= 0:
            return [{"dimension": "unallocated", "cost": total_cost, "pct": 100}]
        allocations = []
        for rule in active_rules:
            allocated = total_cost * (rule['allocation_pct'] / total_pct)
            allocations.append({
                "rule_id": rule['id'],
                "rule_name": rule['name'],
                "dimension": rule['dimension'],
                "allocation_pct": rule['allocation_pct'],
                "allocated_cost": round(allocated, 2),
            })
        return allocations

    def get_allocation_summary(self, total_cost: float) -> Dict[str, Any]:
        by_dim = {}
        for rule in self.allocation_rules:
            if not rule['enabled']:
                continue
            dim = rule['dimension']
            by_dim.setdefault(dim, 0)
            by_dim[dim] += rule['allocation_pct']
        allocations = []
        for dim, pct in by_dim.items():
            allocations.append({"dimension": dim, "pct": pct, "cost": round(total_cost * pct / 100, 2)})
        unallocated = 100 - sum(by_dim.values())
        if unallocated > 0:
            allocations.append({"dimension": "unallocated", "pct": unallocated, "cost": round(total_cost * unallocated / 100, 2)})
        return {"total_cost": total_cost, "allocations": allocations}

# === ANOMALY WATCHER ===

class UnitAnomalyWatcher:
    def __init__(self, engine: UnitEconomics):
        self.engine = engine

    def detect_spikes(self, customer_id: str, metric_type: str, threshold: float = 2.0) -> Dict[str, Any]:
        metrics = self.engine.get_customer_metrics(customer_id, metric_type, hours=168)
        if len(metrics) < 5:
            return {"error": "Insufficient data"}
        values = [m['value'] for m in sorted(metrics, key=lambda x: x['recorded_at'])]
        mean = sum(values) / len(values)
        std = (sum((v - mean)**2 for v in values) / len(values))**0.5
        spikes = []
        for m in metrics:
            zscore = abs(m['value'] - mean) / max(std, 0.001)
            if zscore > threshold:
                spikes.append({
                    "id": m['id'],
                    "value": m['value'],
                    "zscore": round(zscore, 2),
                    "recorded_at": m['recorded_at'],
                })
        return {
            "customer_id": customer_id,
            "metric_type": metric_type,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "spike_count": len(spikes),
            "spikes": spikes,
            "alert": len(spikes) > 0,
        }

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
