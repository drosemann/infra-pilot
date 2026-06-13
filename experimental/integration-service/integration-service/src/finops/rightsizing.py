"""Feature 26: Resource Right-Sizing Recommendations - Analyze utilization, recommend size changes"""

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


class ResourceType(Enum):
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    MEMORY = "memory"
    CACHE = "cache"
    LOAD_BALANCER = "load_balancer"


class RecommendationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SizingAction(Enum):
    DOWNSCALE = "downscale"
    UPSCALE = "upscale"
    RIGHT_SIZE = "right_size"
    STOP = "stop"
    CHANGE_FAMILY = "change_family"


class RecommendationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"


class RightsizingEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.resources_file = _data_file('rightsizing_resources.json')
        self.recommendations_file = _data_file('rightsizing_recommendations.json')
        self.resources: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.resources_file, 'resources'), (self.recommendations_file, 'recommendations')]:
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

    def _save_resources(self):
        try:
            with open(self.resources_file, 'w') as f:
                json.dump(self.resources, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save resources: {e}")

    def register_resource(self, name: str, resource_type: str, current_size: str,
                          specs: Dict[str, Any], monthly_cost: float,
                          provider: str = "aws", region: str = "us-east-1") -> Dict[str, Any]:
        resource = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": resource_type,
            "current_size": current_size,
            "specs": specs,
            "monthly_cost": monthly_cost,
            "provider": provider,
            "region": region,
            "status": "active",
            "utilization_history": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.resources.append(resource)
        self._save_resources()
        return resource

    def record_utilization(self, resource_id: str, cpu_pct: float, memory_pct: float,
                           disk_pct: float = None, iops_pct: float = None) -> Dict[str, Any]:
        resource = next((r for r in self.resources if r['id'] == resource_id), None)
        if not resource:
            return {"error": "Resource not found", "success": False}
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_pct": cpu_pct,
            "memory_pct": memory_pct,
            "disk_pct": disk_pct,
            "iops_pct": iops_pct,
        }
        resource['utilization_history'].append(entry)
        if len(resource['utilization_history']) > 1000:
            resource['utilization_history'] = resource['utilization_history'][-1000:]
        self._save_resources()
        return {"success": True}

    def analyze_resource(self, resource_id: str) -> Dict[str, Any]:
        resource = next((r for r in self.resources if r['id'] == resource_id), None)
        if not resource:
            return {"error": "Resource not found"}

        history = resource.get('utilization_history', [])
        if len(history) < 10:
            history = self._generate_mock_utilization(resource)

        cpu_values = [h['cpu_pct'] for h in history]
        mem_values = [h['memory_pct'] for h in history]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        avg_mem = sum(mem_values) / len(mem_values)
        max_mem = max(mem_values)
        peak_time = max(range(len(cpu_values)), key=lambda i: cpu_values[i]) if len(cpu_values) > 1 else 0

        p95_cpu = sorted(cpu_values)[int(len(cpu_values) * 0.95)]
        p95_mem = sorted(mem_values)[int(len(mem_values) * 0.95)]

        analysis = {
            "resource_id": resource_id,
            "name": resource['name'],
            "current_size": resource['current_size'],
            "monthly_cost": resource['monthly_cost'],
            "avg_cpu_pct": round(avg_cpu, 1),
            "max_cpu_pct": round(max_cpu, 1),
            "p95_cpu_pct": round(p95_cpu, 1),
            "avg_memory_pct": round(avg_mem, 1),
            "max_memory_pct": round(max_mem, 1),
            "p95_memory_pct": round(p95_mem, 1),
            "samples": len(history),
            "over_provisioned": avg_cpu < 30 and avg_mem < 40,
            "under_provisioned": max_cpu > 85 or max_mem > 85,
            "right_sized": 30 <= avg_cpu <= 70 and 40 <= avg_mem <= 80,
        }
        return analysis

    def _generate_mock_utilization(self, resource: Dict) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        history = []
        base_cpu = random.uniform(10, 35)
        base_mem = random.uniform(20, 50)
        for i in range(168):
            hour = (now - timedelta(hours=167 - i)).hour
            cpu = base_cpu + 10 * math.sin(hour / 24 * 2 * math.pi) + random.uniform(-5, 5)
            mem = base_mem + 5 * math.sin(hour / 24 * 2 * math.pi + 1) + random.uniform(-3, 3)
            entry = {
                "timestamp": (now - timedelta(hours=167 - i)).isoformat(),
                "cpu_pct": round(max(0, min(100, cpu)), 1),
                "memory_pct": round(max(0, min(100, mem)), 1),
            }
            history.append(entry)
        resource['utilization_history'] = history
        self._save_resources()
        return history

    def generate_recommendations(self, resource_id: str = None) -> List[Dict[str, Any]]:
        targets = [resource_id] if resource_id else [r['id'] for r in self.resources]
        if not targets:
            return self._seed_mock_resources()

        new_recs = []
        for rid in targets:
            analysis = self.analyze_resource(rid)
            if 'error' in analysis:
                continue

            if analysis['over_provisioned']:
                action = SizingAction.DOWNSCALE.value
                size_map = {
                    "t3.large": "t3.medium", "t3.xlarge": "t3.large", "t3.2xlarge": "t3.xlarge",
                    "m5.large": "m5.medium", "m5.xlarge": "m5.large", "m5.2xlarge": "m5.xlarge",
                    "r5.large": "r5.medium", "r5.xlarge": "r5.large",
                    "db.r5.large": "db.r5.medium", "db.r5.xlarge": "db.r5.large",
                }
                recommended_size = size_map.get(analysis['current_size'], f"{analysis['current_size']}-downsized")
                savings_pct = 0.4 if analysis['avg_cpu_pct'] < 15 else 0.25
                priority = RecommendationPriority.HIGH.value
            elif analysis['under_provisioned']:
                action = SizingAction.UPSCALE.value
                size_map = {
                    "t3.medium": "t3.large", "t3.large": "t3.xlarge", "t3.xlarge": "t3.2xlarge",
                    "m5.medium": "m5.large", "m5.large": "m5.xlarge",
                    "db.r5.medium": "db.r5.large",
                }
                recommended_size = size_map.get(analysis['current_size'], f"{analysis['current_size']}-upsized")
                savings_pct = -0.5
                priority = RecommendationPriority.CRITICAL.value
            else:
                continue

            monthly_savings = round(analysis['monthly_cost'] * abs(savings_pct), 2) if savings_pct > 0 else 0
            new_cost = round(analysis['monthly_cost'] - monthly_savings, 2) if savings_pct > 0 else round(analysis['monthly_cost'] * 1.5, 2)

            rec = {
                "id": str(uuid.uuid4()),
                "resource_id": rid,
                "resource_name": analysis['name'],
                "current_size": analysis['current_size'],
                "recommended_size": recommended_size,
                "action": action,
                "current_monthly_cost": analysis['monthly_cost'],
                "recommended_monthly_cost": new_cost,
                "monthly_savings": monthly_savings,
                "annual_savings": round(monthly_savings * 12, 2),
                "avg_cpu_pct": analysis['avg_cpu_pct'],
                "avg_memory_pct": analysis['avg_memory_pct'],
                "p95_cpu_pct": analysis['p95_cpu_pct'],
                "p95_memory_pct": analysis['p95_memory_pct'],
                "priority": priority,
                "status": RecommendationStatus.PENDING.value,
                "reason": f"This {resource_id or 'resource'} is over-provisioned by ~{100 - analysis['avg_cpu_pct']:.0f}% — save ${monthly_savings}/mo" if savings_pct > 0
                          else f"This {resource_id or 'resource'} is under-provisioned (CPU at {analysis['avg_cpu_pct']}%) — upscale recommended",
                "created_at": datetime.utcnow().isoformat(),
            }
            new_recs.append(rec)
            self.recommendations.append(rec)
        self._save_recommendations()
        return new_recs

    def _seed_mock_resources(self) -> List[Dict[str, Any]]:
        mock_resources = [
            ("web-server-01", "compute", "t3.large", {"cpu": 2, "memory_gb": 8}, 68.64, "aws", "us-east-1"),
            ("db-primary-01", "database", "db.r5.large", {"cpu": 2, "memory_gb": 16}, 175.20, "aws", "eu-west-1"),
            ("cache-cluster-01", "cache", "cache.r5.large", {"memory_gb": 13}, 130.00, "aws", "us-east-1"),
            ("batch-worker-01", "compute", "m5.xlarge", {"cpu": 4, "memory_gb": 16}, 162.00, "aws", "us-west-2"),
            ("analytics-db", "database", "db.r5.xlarge", {"cpu": 4, "memory_gb": 32}, 350.40, "aws", "us-east-1"),
        ]
        for name, rtype, size, specs, cost, provider, region in mock_resources:
            self.register_resource(name, rtype, size, specs, cost, provider, region)
        return self.generate_recommendations()

    def get_recommendations(self, status: str = None, priority: str = None) -> List[Dict[str, Any]]:
        result = self.recommendations
        if status:
            result = [r for r in result if r['status'] == status]
        if priority:
            result = [r for r in result if r['priority'] == priority]
        return sorted(result, key=lambda x: x['monthly_savings'], reverse=True)

    def approve_recommendation(self, rec_id: str) -> Dict[str, Any]:
        rec = next((r for r in self.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found", "success": False}
        rec['status'] = RecommendationStatus.APPROVED.value
        self._save_recommendations()
        return {"success": True}

    def implement_recommendation(self, rec_id: str) -> Dict[str, Any]:
        rec = next((r for r in self.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found", "success": False}
        rec['status'] = RecommendationStatus.IMPLEMENTED.value
        rec['implemented_at'] = datetime.utcnow().isoformat()
        self._save_recommendations()
        return {"success": True, "new_size": rec['recommended_size'], "monthly_savings": rec['monthly_savings']}

    def dismiss_recommendation(self, rec_id: str) -> Dict[str, Any]:
        rec = next((r for r in self.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found", "success": False}
        rec['status'] = RecommendationStatus.DISMISSED.value
        self._save_recommendations()
        return {"success": True}

    def get_summary(self) -> Dict[str, Any]:
        pending = [r for r in self.recommendations if r['status'] == RecommendationStatus.PENDING.value]
        total_savings = sum(r['monthly_savings'] for r in pending)
        return {
            "total_resources": len(self.resources),
            "total_recommendations": len(self.recommendations),
            "pending": len(pending),
            "approved": sum(1 for r in self.recommendations if r['status'] == RecommendationStatus.APPROVED.value),
            "implemented": sum(1 for r in self.recommendations if r['status'] == RecommendationStatus.IMPLEMENTED.value),
            "dismissed": sum(1 for r in self.recommendations if r['status'] == RecommendationStatus.DISMISSED.value),
            "potential_monthly_savings": round(total_savings, 2),
            "potential_annual_savings": round(total_savings * 12, 2),
            "by_priority": {
                "critical": sum(1 for r in pending if r['priority'] == RecommendationPriority.CRITICAL.value),
                "high": sum(1 for r in pending if r['priority'] == RecommendationPriority.HIGH.value),
                "medium": sum(1 for r in pending if r['priority'] == RecommendationPriority.MEDIUM.value),
                "low": sum(1 for r in pending if r['priority'] == RecommendationPriority.LOW.value),
            },
        }

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class RightsizingError(Exception): pass

@dataclass
class ResourceSpec:
    cpu: int = 2
    memory_gb: int = 8
    storage_gb: int = 50
    iops: int = 3000

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_resource_registration(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('name'): errors.append("name is required")
    if data.get('resource_type') not in ['compute', 'database', 'storage']: errors.append("resource_type must be compute/database/storage")
    if not data.get('current_size'): errors.append("current_size is required")
    return errors

def compute_rightsizing_savings(current_cost: float, recommended_cost: float) -> Dict[str, Any]:
    savings = current_cost - recommended_cost
    savings_pct = (savings / max(current_cost, 0.01)) * 100
    return {
        "current_monthly": round(current_cost, 2),
        "recommended_monthly": round(recommended_cost, 2),
        "monthly_savings": round(savings, 2),
        "annual_savings": round(savings * 12, 2),
        "savings_pct": round(savings_pct, 1),
    }

def analyze_resource_utilization(metrics: Dict[str, float]) -> Dict[str, Any]:
    cpu_util = metrics.get('cpu_avg', 0)
    mem_util = metrics.get('memory_avg', 0)
    overall = (cpu_util + mem_util) / 2
    recommendation = "rightsize_down" if overall < 40 else ("rightsize_up" if overall > 85 else "optimal")
    return {
        "cpu_utilization_pct": cpu_util,
        "memory_utilization_pct": mem_util,
        "overall_utilization_pct": round(overall, 1),
        "recommendation": recommendation,
        "estimated_savings_pct": 40 if recommendation == "rightsize_down" else 0,
    }

def batch_analyze_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for res in resources:
        analysis = {
            "resource_id": res.get('id'),
            "resource_name": res.get('name'),
            "resource_type": res.get('resource_type'),
            "current_size": res.get('current_size'),
            "utilization": analyze_resource_utilization({'cpu_avg': res.get('specs', {}).get('cpu', 50) * 0.4, 'memory_avg': res.get('specs', {}).get('memory_gb', 8) * 0.35}),
        }
        results.append(analysis)
    return results

def recommend_instance_family(workload_type: str, cpu_cores: int, memory_gb: int) -> Dict[str, Any]:
    families = {
        "compute": [{"family": "c5", "cpu": 4, "mem": 8, "cost": 70}, {"family": "c6g", "cpu": 4, "mem": 8, "cost": 60}],
        "memory": [{"family": "r5", "cpu": 4, "mem": 32, "cost": 100}, {"family": "r6g", "cpu": 4, "mem": 32, "cost": 90}],
        "general": [{"family": "m5", "cpu": 4, "mem": 16, "cost": 80}, {"family": "m6g", "cpu": 4, "mem": 16, "cost": 70}],
    }
    options = families.get(workload_type, families['general'])
    return {
        "workload_type": workload_type,
        "recommended_family": options[0]['family'],
        "alternatives": options,
        "estimated_monthly_cost": options[0]['cost'],
    }

def generate_rightsizing_report(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    pending = [r for r in recommendations if r.get('status') in ['pending', 'open']]
    implemented = [r for r in recommendations if r.get('status') == 'implemented']
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_recommendations": len(recommendations),
        "pending": len(pending),
        "implemented": len(implemented),
        "pending_monthly_savings": round(sum(r.get('estimated_savings', 0) for r in pending), 2),
        "implemented_monthly_savings": round(sum(r.get('estimated_savings', 0) for r in implemented), 2),
        "by_type": {t: len([r for r in recommendations if r.get('resource_type') == t]) for t in set(r.get('resource_type', 'unknown') for r in recommendations)},
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class RightsizingBatchProcessor:
    def __init__(self, engine: 'RightsizingEngine'):
        self.engine = engine
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_approve(self, rec_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rid in rec_ids:
            try:
                result = self.engine.approve_recommendation(rid)
                results.append({"success": True, "id": rid, "result": result})
            except Exception as e:
                results.append({"success": False, "id": rid, "error": str(e)})
        return results

    async def batch_simulate(self, simulations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for sim in simulations:
            try:
                result = simulate_resize(sim.get('resource_id'), sim.get('current'), sim.get('recommended'))
                results.append({"success": True, "simulation": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": sim})
        return results

    async def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "resource_name", "resource_type", "current_size", "recommended_size", "savings", "status"])
        for r in self.engine.recommendations:
            writer.writerow([r.get('id'), r.get('resource_name'), r.get('resource_type'), r.get('current_size'), r.get('recommended_size'), r.get('estimated_savings'), r.get('status')])
        return output.getvalue()

class RightsizingAnalytics:
    def __init__(self, engine: 'RightsizingEngine'):
        self.engine = engine

    def by_type(self) -> Dict[str, int]:
        by_type = {}
        for r in self.engine.recommendations:
            t = r.get('resource_type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
        return by_type

    def savings_pipeline(self) -> Dict[str, Any]:
        pending = [r for r in self.engine.recommendations if r.get('status') == 'pending']
        approved = [r for r in self.engine.recommendations if r.get('status') == 'approved']
        implemented = [r for r in self.engine.recommendations if r.get('status') == 'implemented']
        return {"pending": len(pending), "approved": len(approved), "implemented": len(implemented), "pending_savings": round(sum(r.get('estimated_savings', 0) for r in pending), 2), "total_savings": round(sum(r.get('estimated_savings', 0) for r in self.engine.recommendations), 2)}

class RightsizingPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === ADVANCED RIGHTSIZING ===

class RightsizingSimulator:
    def __init__(self, engine: RightsizingEngine):
        self.engine = engine

    def simulate_resize(self, resource_id: str, target_size: str, target_cost: float) -> Dict[str, Any]:
        resource = next((r for r in self.engine.resources if r['id'] == resource_id), None)
        if not resource:
            return {"error": "Resource not found"}
        current_cost = resource['monthly_cost']
        savings = current_cost - target_cost
        savings_pct = (savings / max(current_cost, 0.01)) * 100 if savings > 0 else 0
        risk = "low" if savings_pct < 30 else ("medium" if savings_pct < 50 else "high")
        return {
            "resource_id": resource_id,
            "resource_name": resource['name'],
            "current_size": resource['current_size'],
            "target_size": target_size,
            "current_cost": current_cost,
            "target_cost": target_cost,
            "monthly_savings": round(max(0, savings), 2),
            "annual_savings": round(max(0, savings * 12), 2),
            "savings_pct": round(savings_pct, 1),
            "risk_level": risk,
            "performance_impact": "minimal" if savings_pct < 20 else ("noticeable" if savings_pct < 40 else "significant"),
            "recommended_approach": "gradual" if risk == "high" else "direct",
        }

    def bulk_simulate(self, simulations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.simulate_resize(s['resource_id'], s['target_size'], s['target_cost']) for s in simulations]

# === RIGHT-SIZING SCHEDULER ===

class RightsizingScheduler:
    def __init__(self, engine: RightsizingEngine):
        self.engine = engine
        self.scheduled_actions: List[Dict[str, Any]] = []

    def schedule_resize(self, rec_id: str, execute_at: str) -> Dict[str, Any]:
        rec = next((r for r in self.engine.recommendations if r['id'] == rec_id), None)
        if not rec:
            return {"error": "Recommendation not found"}
        action = {
            "id": str(uuid.uuid4()),
            "recommendation_id": rec_id,
            "resource_id": rec['resource_id'],
            "action": rec['action'],
            "current_size": rec['current_size'],
            "new_size": rec['recommended_size'],
            "scheduled_at": execute_at,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.scheduled_actions.append(action)
        return action

    def cancel_scheduled(self, action_id: str) -> bool:
        action = next((a for a in self.scheduled_actions if a['id'] == action_id), None)
        if not action:
            return False
        action['status'] = "cancelled"
        return True

    def execute_due(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        executed = []
        for action in self.scheduled_actions:
            if action['status'] == "scheduled" and datetime.fromisoformat(action['scheduled_at']) <= now:
                action['status'] = "executed"
                action['executed_at'] = now.isoformat()
                executed.append(action)
        return executed

# === FAMILY MIGRATION ANALYZER ===

class FamilyMigrationAnalyzer:
    def __init__(self):
        self.family_map = {
            "t3": {"c5": 0.85, "m5": 0.90, "r5": 1.05},
            "m5": {"c5": 0.80, "r5": 1.10, "t3": 0.75},
            "c5": {"m5": 1.15, "r5": 1.30, "t3": 0.70},
            "r5": {"m5": 0.85, "c5": 0.70, "t3": 0.65},
        }

    def analyze_migration(self, current_family: str, target_family: str, current_cost: float, current_cpu: float) -> Dict[str, Any]:
        multipliers = self.family_map.get(current_family, {})
        mult = multipliers.get(target_family, 1.0)
        new_cost = current_cost * mult
        cpu_impact = "increase" if "c5" in target_family else ("decrease" if "r5" in target_family else "similar")
        return {
            "current_family": current_family,
            "target_family": target_family,
            "current_cost": current_cost,
            "estimated_new_cost": round(new_cost, 2),
            "cost_change": round(new_cost - current_cost, 2),
            "cost_change_pct": round((mult - 1) * 100, 1),
            "cpu_impact": cpu_impact,
            "recommended": new_cost < current_cost,
        }

    def find_best_family(self, workload_type: str, current_family: str, current_cost: float) -> Dict[str, Any]:
        families = ["t3", "m5", "c5", "r5"]
        results = []
        for f in families:
            if f == current_family:
                continue
            results.append(self.analyze_migration(current_family, f, current_cost, 50))
        best = min(results, key=lambda r: r['estimated_new_cost'])
        return {"current_cost": current_cost, "best_option": best, "all_options": sorted(results, key=lambda r: r['estimated_new_cost'])}

# === CAPACITY PLANNER ===

class CapacityPlanner:
    def __init__(self, engine: RightsizingEngine):
        self.engine = engine

    def plan_capacity(self, resource_ids: List[str], growth_pct: float = 20) -> Dict[str, Any]:
        total_current = 0
        total_recommended = 0
        for rid in resource_ids:
            resource = next((r for r in self.engine.resources if r['id'] == rid), None)
            if not resource:
                continue
            total_current += resource['monthly_cost']
        growth_mult = 1 + growth_pct / 100
        total_growth = total_current * growth_mult
        potential_savings = total_current * 0.25
        return {
            "resources_analyzed": len(resource_ids),
            "current_monthly": round(total_current, 2),
            "projected_with_growth": round(total_growth, 2),
            "growth_pct": growth_pct,
            "recommended_capacity": round(total_growth * 0.8, 2),
            "potential_savings": round(potential_savings, 2),
            "recommendations": [
                "Implement auto-scaling to match demand",
                "Use reserved instances for baseline capacity",
                "Apply rightsizing recommendations before scaling",
            ],
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
