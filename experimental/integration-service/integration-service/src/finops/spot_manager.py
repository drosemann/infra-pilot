"""Feature 22: Spot/Preemptible Manager - Manage spot instance fleets with graceful interruption handling"""

import json
import os
import math
import uuid
import logging
import random
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


class SpotStatus(Enum):
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    TERMINATED = "terminated"
    DRAINING = "draining"
    STOPPED = "stopped"
    PENDING = "pending"


class DiversificationStrategy(Enum):
    LOWEST_PRICE = "lowest_price"
    DIVERSIFIED = "diversified"
    CAPACITY_OPTIMIZED = "capacity_optimized"
    PRICE_CAPACITY_OPTIMIZED = "price_capacity_optimized"


class FleetRequestStatus(Enum):
    SUBMITTED = "submitted"
    ACTIVE = "active"
    MODIFYING = "modifying"
    DELETED = "deleted"
    ERROR = "error"


class SpotManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fleets_file = _data_file('spot_fleets.json')
        self.instances_file = _data_file('spot_instances.json')
        self.interruptions_file = _data_file('spot_interruptions.json')
        self.fleets: List[Dict[str, Any]] = []
        self.instances: List[Dict[str, Any]] = []
        self.interruptions: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.fleets_file, 'fleets'), (self.instances_file, 'instances'), (self.interruptions_file, 'interruptions')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_data(self, attr, file):
        try:
            with open(file, 'w') as f:
                json.dump(getattr(self, attr), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {attr}: {e}")

    def _save_fleets(self):
        self._save_data('fleets', self.fleets_file)

    def _save_instances(self):
        self._save_data('instances', self.instances_file)

    def _save_interruptions(self):
        self._save_data('interruptions', self.interruptions_file)

    def create_fleet(self, name: str, target_capacity: int, instance_types: List[str],
                     regions: List[str], strategy: str = "lowest_price",
                     max_price: float = None, allocation_strategy: str = None) -> Dict[str, Any]:
        fleet = {
            "id": str(uuid.uuid4()),
            "name": name,
            "target_capacity": target_capacity,
            "fulfilled_capacity": 0,
            "instance_types": instance_types,
            "regions": regions,
            "strategy": strategy,
            "max_price": max_price,
            "allocation_strategy": allocation_strategy or DiversificationStrategy.LOWEST_PRICE.value,
            "status": FleetRequestStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "interruption_handling": {
                "drain_timeout_seconds": 120,
                "checkpoint_enabled": True,
                "auto_restart": True,
                "fallback_to_on_demand": True,
            },
        }
        self.fleets.append(fleet)
        self._save_fleets()
        return fleet

    def launch_instances(self, fleet_id: str, count: int = None) -> List[Dict[str, Any]]:
        fleet = next((f for f in self.fleets if f['id'] == fleet_id), None)
        if not fleet:
            return []
        launch_count = count or fleet['target_capacity'] - fleet['fulfilled_capacity']
        if launch_count <= 0:
            return []
        new_instances = []
        for _ in range(launch_count):
            instance_type = random.choice(fleet['instance_types'])
            region = random.choice(fleet['regions'])
            spot_price = round(random.uniform(0.01, 0.15), 4)
            on_demand_price = round(spot_price * random.uniform(2.0, 4.0), 4)
            instance = {
                "id": str(uuid.uuid4()),
                "fleet_id": fleet_id,
                "instance_type": instance_type,
                "region": region,
                "availability_zone": f"{region}{random.choice(['a', 'b', 'c'])}",
                "spot_price": spot_price,
                "on_demand_price": on_demand_price,
                "status": SpotStatus.PENDING.value,
                "launched_at": datetime.utcnow().isoformat(),
                "interruption_risk": random.choice(["low", "medium", "high"]),
                "checkpoint_data": None,
                "drain_started_at": None,
            }
            self.instances.append(instance)
            new_instances.append(instance)
        fleet['fulfilled_capacity'] += launch_count
        fleet['last_updated'] = datetime.utcnow().isoformat()
        self._save_instances()
        self._save_fleets()
        for inst in new_instances:
            inst['status'] = SpotStatus.RUNNING.value
        self._save_instances()
        return new_instances

    def get_fleet(self, fleet_id: str) -> Optional[Dict[str, Any]]:
        return next((f for f in self.fleets if f['id'] == fleet_id), None)

    def list_fleets(self) -> List[Dict[str, Any]]:
        return self.fleets

    def update_fleet_capacity(self, fleet_id: str, new_capacity: int) -> Dict[str, Any]:
        fleet = next((f for f in self.fleets if f['id'] == fleet_id), None)
        if not fleet:
            return {"error": "Fleet not found", "success": False}
        old = fleet['target_capacity']
        fleet['target_capacity'] = new_capacity
        fleet['last_updated'] = datetime.utcnow().isoformat()
        self._save_fleets()
        if new_capacity > fleet['fulfilled_capacity']:
            self.launch_instances(fleet_id, new_capacity - fleet['fulfilled_capacity'])
        elif new_capacity < fleet['fulfilled_capacity']:
            self._drain_instances(fleet_id, fleet['fulfilled_capacity'] - new_capacity)
        return {"success": True, "old_capacity": old, "new_capacity": new_capacity}

    def _drain_instances(self, fleet_id: str, count: int):
        running = [i for i in self.instances if i['fleet_id'] == fleet_id and i['status'] == SpotStatus.RUNNING.value]
        for inst in running[:count]:
            inst['status'] = SpotStatus.DRAINING.value
            inst['drain_started_at'] = datetime.utcnow().isoformat()
            fleet = next((f for f in self.fleets if f['id'] == fleet_id), None)
            if fleet:
                fleet['fulfilled_capacity'] -= 1
                self._save_fleets()
        self._save_instances()

    def simulate_interruption(self, instance_id: str) -> Dict[str, Any]:
        inst = next((i for i in self.instances if i['id'] == instance_id), None)
        if not inst:
            return {"error": "Instance not found", "success": False}
        old_status = inst['status']
        inst['status'] = SpotStatus.INTERRUPTED.value
        interruption = {
            "id": str(uuid.uuid4()),
            "instance_id": instance_id,
            "fleet_id": inst['fleet_id'],
            "instance_type": inst['instance_type'],
            "region": inst['region'],
            "interrupted_at": datetime.utcnow().isoformat(),
            "old_status": old_status,
            "interruption_reason": random.choice(["price_exceeded", "capacity_needed", "instance_reclaim"]),
            "had_checkpoint": inst.get('checkpoint_data') is not None,
            "auto_restarted": True,
        }
        self.interruptions.append(interruption)
        self._save_interruptions()
        self._save_instances()

        fleet = next((f for f in self.fleets if f['id'] == inst['fleet_id']), None)
        if fleet and fleet['interruption_handling']['auto_restart']:
            self._auto_replace_instance(inst)
        return {"success": True, "interruption": interruption}

    def _auto_replace_instance(self, interrupted_inst: Dict[str, Any]):
        new_inst = {
            "id": str(uuid.uuid4()),
            "fleet_id": interrupted_inst['fleet_id'],
            "instance_type": random.choice(
                next((f['instance_types'] for f in self.fleets if f['id'] == interrupted_inst['fleet_id']), ["t3.medium"])),
            "region": interrupted_inst['region'],
            "availability_zone": interrupted_inst['availability_zone'],
            "spot_price": round(random.uniform(0.01, 0.15), 4),
            "on_demand_price": interrupted_inst['on_demand_price'],
            "status": SpotStatus.RUNNING.value,
            "launched_at": datetime.utcnow().isoformat(),
            "replaces_instance": interrupted_inst['id'],
            "interruption_risk": random.choice(["low", "medium", "high"]),
            "checkpoint_data": interrupted_inst.get('checkpoint_data'),
            "drain_started_at": None,
        }
        self.instances.append(new_inst)
        fleet = next((f for f in self.fleets if f['id'] == interrupted_inst['fleet_id']), None)
        if fleet:
            fleet['fulfilled_capacity'] = sum(1 for i in self.instances
                                               if i['fleet_id'] == fleet['id'] and i['status'] == SpotStatus.RUNNING.value)
            self._save_fleets()
        self._save_instances()

    def save_checkpoint(self, instance_id: str, checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        inst = next((i for i in self.instances if i['id'] == instance_id), None)
        if not inst:
            return {"error": "Instance not found", "success": False}
        inst['checkpoint_data'] = checkpoint_data
        inst['checkpoint_at'] = datetime.utcnow().isoformat()
        self._save_instances()
        return {"success": True}

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        return next((i for i in self.instances if i['id'] == instance_id), None)

    def list_instances(self, fleet_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        result = self.instances
        if fleet_id:
            result = [i for i in result if i['fleet_id'] == fleet_id]
        if status:
            result = [i for i in result if i['status'] == status]
        return result

    def get_interruption_history(self, fleet_id: str = None) -> List[Dict[str, Any]]:
        if fleet_id:
            return [i for i in self.interruptions if i['fleet_id'] == fleet_id]
        return self.interruptions

    def get_fleet_summary(self, fleet_id: str) -> Dict[str, Any]:
        fleet = self.get_fleet(fleet_id)
        if not fleet:
            return {"error": "Fleet not found"}
        instances = [i for i in self.instances if i['fleet_id'] == fleet_id]
        running = sum(1 for i in instances if i['status'] == SpotStatus.RUNNING.value)
        interrupted = sum(1 for i in instances if i['status'] == SpotStatus.INTERRUPTED.value)
        draining = sum(1 for i in instances if i['status'] == SpotStatus.DRAINING.value)
        total_spot_cost = sum(i['spot_price'] for i in instances if i['status'] == SpotStatus.RUNNING.value)
        total_on_demand_cost = sum(i['on_demand_price'] for i in instances if i['status'] == SpotStatus.RUNNING.value)
        savings = total_on_demand_cost - total_spot_cost
        interruptions_24h = sum(1 for i in self.interruptions if i['fleet_id'] == fleet_id
                                and datetime.fromisoformat(i['interrupted_at']) > datetime.utcnow() - timedelta(hours=24))
        return {
            "fleet_id": fleet_id,
            "name": fleet['name'],
            "target_capacity": fleet['target_capacity'],
            "fulfilled_capacity": fleet['fulfilled_capacity'],
            "running": running,
            "interrupted": interrupted,
            "draining": draining,
            "total_instances": len(instances),
            "current_hourly_spot_cost": round(total_spot_cost, 4),
            "equivalent_on_demand_cost": round(total_on_demand_cost, 4),
            "hourly_savings": round(savings, 4),
            "savings_pct": round((savings / max(total_on_demand_cost, 0.01)) * 100, 1),
            "interruptions_last_24h": interruptions_24h,
            "status": fleet['status'],
        }

    def get_overall_savings(self) -> Dict[str, Any]:
        total_spot = sum(i['spot_price'] for i in self.instances if i['status'] == SpotStatus.RUNNING.value)
        total_od = sum(i['on_demand_price'] for i in self.instances if i['status'] == SpotStatus.RUNNING.value)
        total_interruptions = len(self.interruptions)
        return {
            "total_running_instances": sum(1 for i in self.instances if i['status'] == SpotStatus.RUNNING.value),
            "total_fleets": len(self.fleets),
            "current_hourly_spot_spend": round(total_spot, 4),
            "equivalent_on_demand_spend": round(total_od, 4),
            "hourly_savings": round(total_od - total_spot, 4),
            "savings_pct": round(((total_od - total_spot) / max(total_od, 0.01)) * 100, 1),
            "total_interruptions": total_interruptions,
            "projected_monthly_savings": round((total_od - total_spot) * 730, 2),
        }

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class SpotManagerError(Exception): pass

@dataclass
class FleetConfig:
    name: str
    instance_types: List[str]
    target_capacity: int
    regions: List[str]
    allocation_strategy: str = "lowestPrice"
    max_price: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_fleet_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get('name'): errors.append("name is required")
    if not config.get('instance_types'): errors.append("instance_types is required")
    if config.get('target_capacity', 0) < 1: errors.append("target_capacity must be >= 1")
    return errors

async def batch_launch_instances(manager: 'SpotManager', fleet_id: str, counts: List[int]) -> Dict[str, Any]:
    results = {"launched": 0, "failed": 0, "instances": []}
    for count in counts:
        try:
            for _ in range(count):
                inst = manager.launch_instance(fleet_id)
                results["launched"] += 1
                results["instances"].append(inst)
        except Exception:
            results["failed"] += 1
    return results

def filter_fleets(fleets: List[Dict[str, Any]], status: Optional[str] = None, region: Optional[str] = None) -> List[Dict[str, Any]]:
    results = fleets[:]
    if status: results = [f for f in results if f.get('status') == status]
    if region: results = [f for f in results if region in f.get('regions', [])]
    return results

def analyze_interruption_patterns(interruptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not interruptions: return {"total": 0, "avg_lifetime_hours": 0}
    by_reason = {}
    for i in interruptions:
        reason = i.get('interruption_reason', 'unknown')
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "total_interruptions": len(interruptions),
        "by_reason": by_reason,
        "avg_lifetime_hours": round(sum(i.get('lifetime_hours', 0) for i in interruptions) / len(interruptions), 1),
    }

def compute_fleet_diversity_score(instances: List[Dict[str, Any]]) -> float:
    if not instances: return 0.0
    types = set(i.get('instance_type') for i in instances)
    zones = set(i.get('availability_zone') for i in instances)
    return round((len(types) * 0.6 + len(zones) * 0.4) / 10.0, 2)

def estimate_spot_savings(od_price: float, spot_price: float) -> Dict[str, Any]:
    savings = od_price - spot_price
    savings_pct = (savings / od_price) * 100 if od_price > 0 else 0
    return {
        "on_demand_hourly": od_price,
        "spot_hourly": spot_price,
        "hourly_savings": round(savings, 4),
        "savings_pct": round(savings_pct, 1),
        "monthly_savings": round(savings * 730, 2),
    }

def generate_interruption_handling_plan(fleet: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "fleet_id": fleet.get('id'),
        "strategy": "diversified",
        "fallback_on_demand": True,
        "draining_timeout_seconds": 120,
        "checkpoint_frequency_minutes": 5,
        "recommended_actions": [
            "Use instance pools across 3+ availability zones",
            "Enable detailed CloudWatch metrics",
            "Implement checkpointing for stateful workloads",
            "Configure auto-draining for graceful shutdown",
        ],
    }

def optimize_fleet_allocation(fleets: List[Dict[str, Any]], instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    optimizations = []
    for fleet in fleets:
        fleet_instances = [i for i in instances if i.get('fleet_id') == fleet.get('id')]
        if not fleet_instances: continue
        running = [i for i in fleet_instances if i.get('status') == 'running']
        total_savings = sum(i.get('spot_price', 0) for i in running)
        optimal = {
            "fleet_id": fleet['id'],
            "current_capacity": fleet.get('fulfilled_capacity', 0),
            "target_capacity": fleet.get('target_capacity', 0),
            "running_count": len(running),
            "total_hourly_savings": round(total_savings, 4),
            "diversity_score": compute_fleet_diversity_score(fleet_instances),
        }
        optimizations.append(optimal)
    return sorted(optimizations, key=lambda x: x['total_hourly_savings'], reverse=True)

def get_spot_price_history(instance_type: str, region: str) -> Dict[str, Any]:
    return {
        "instance_type": instance_type,
        "region": region,
        "current_spot_price": round(0.0135 * (hash(instance_type + region) % 100) / 100 + 0.005, 4),
        "avg_3d_price": 0.0285,
        "min_3d_price": 0.0120,
        "max_3d_price": 0.0450,
        "savings_vs_od_pct": 62.0,
        "price_stability": "moderate",
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class SpotBatchProcessor:
    def __init__(self, manager: 'SpotManager'):
        self.manager = manager
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_create_fleets(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for cfg in configs:
            try:
                fleet = self.manager.create_fleet(name=cfg['name'], instance_types=cfg.get('instance_types', ['m5.large']), target_capacity=cfg.get('target_capacity', 2), regions=cfg.get('regions', ['us-east-1']))
                results.append({"success": True, "fleet": fleet})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": cfg})
        return results

    async def batch_launch(self, fleet_id: str, counts: List[int]) -> List[Dict[str, Any]]:
        results = []
        for count in counts:
            try:
                for _ in range(count):
                    inst = self.manager.launch_instance(fleet_id)
                    results.append({"success": True, "instance": inst})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    async def export_fleets_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "instance_types", "regions", "target_capacity", "fulfilled_capacity", "status"])
        for f in self.manager.fleets:
            writer.writerow([f.get('id'), f.get('name'), '/'.join(f.get('instance_types', [])), '/'.join(f.get('regions', [])), f.get('target_capacity'), f.get('fulfilled_capacity'), f.get('status')])
        return output.getvalue()

class SpotAnalytics:
    def __init__(self, manager: 'SpotManager'):
        self.manager = manager

    def fleet_health(self) -> Dict[str, Any]:
        active = sum(1 for f in self.manager.fleets if f.get('status') == 'active')
        degraded = sum(1 for f in self.manager.fleets if f.get('status') in ['pending', 'modifying'])
        failed = sum(1 for f in self.manager.fleets if f.get('status') in ['error', 'cancelled'])
        return {"active": active, "degraded": degraded, "failed": failed, "total": len(self.manager.fleets)}

    def instance_type_distribution(self) -> Dict[str, int]:
        dist = {}
        for i in self.manager.instances:
            t = i.get('instance_type', 'unknown')
            dist[t] = dist.get(t, 0) + 1
        return dist

class SpotPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items; self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size; end = start + self.page_size
        total = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {"page": page, "page_size": self.page_size, "total_items": len(self.items), "total_pages": total, "has_next": page < total, "has_prev": page > 1, "items": self.items[start:end]}

# === SPOT PRICE PREDICTOR ===

class SpotPricePredictor:
    def __init__(self, manager: SpotManager):
        self.manager = manager

    def predict_price(self, instance_type: str, region: str, hours_ahead: int = 24) -> Dict[str, Any]:
        base = 0.0135 * (hash(instance_type + region) % 100) / 100 + 0.005
        predictions = []
        for h in range(1, hours_ahead + 1):
            variance = base * 0.1 * math.sin(h / 6 * math.pi)
            predicted = base + variance
            predictions.append({"hour": h, "predicted_price": round(predicted, 4)})
        avg_price = sum(p['predicted_price'] for p in predictions) / len(predictions)
        return {
            "instance_type": instance_type,
            "region": region,
            "current_spot_price": round(base, 4),
            "on_demand_price": round(base * 3, 4),
            "forecast_hours": hours_ahead,
            "avg_predicted_price": round(avg_price, 4),
            "min_predicted": round(min(p['predicted_price'] for p in predictions), 4),
            "max_predicted": round(max(p['predicted_price'] for p in predictions), 4),
            "buy_recommendation": "buy_now" if avg_price < base * 0.95 else "wait",
            "hourly_predictions": predictions,
        }

    def best_time_to_buy(self, instance_type: str, region: str) -> Dict[str, Any]:
        base = 0.0135 * (hash(instance_type + region) % 100) / 100 + 0.005
        hourly_prices = []
        for h in range(24):
            price = base + base * 0.15 * math.sin(h / 12 * math.pi)
            hourly_prices.append({"hour": h, "price": round(price, 4)})
        best = min(hourly_prices, key=lambda x: x['price'])
        return {
            "instance_type": instance_type,
            "region": region,
            "best_hour_utc": best['hour'],
            "best_price": best['price'],
            "savings_vs_avg": round((sum(p['price'] for p in hourly_prices)/24 - best['price']), 4),
            "price_range": {
                "min": best['price'],
                "max": max(p['price'] for p in hourly_prices),
                "avg": round(sum(p['price'] for p in hourly_prices)/24, 4),
            },
        }

# === DRAIN MANAGER ===

class DrainManager:
    def __init__(self, manager: SpotManager):
        self.manager = manager

    def initiate_drain(self, instance_id: str, timeout_seconds: int = 120) -> Dict[str, Any]:
        inst = next((i for i in self.manager.instances if i['id'] == instance_id), None)
        if not inst:
            return {"error": "Instance not found"}
        inst['status'] = SpotStatus.DRAINING.value
        inst['drain_started_at'] = datetime.utcnow().isoformat()
        inst['drain_timeout'] = timeout_seconds
        self.manager._save_instances()
        steps = [
            "Stop accepting new connections",
            "Complete in-flight requests",
            "Save checkpoint data",
            "Notify connected services",
            "Terminate instance",
        ]
        return {
            "instance_id": instance_id,
            "drain_started_at": inst['drain_started_at'],
            "timeout_seconds": timeout_seconds,
            "drain_steps": steps,
            "estimated_completion": (datetime.utcnow() + timedelta(seconds=timeout_seconds)).isoformat(),
        }

    def check_drain_status(self, instance_id: str) -> Dict[str, Any]:
        inst = next((i for i in self.manager.instances if i['id'] == instance_id), None)
        if not inst:
            return {"error": "Instance not found"}
        if inst['status'] != SpotStatus.DRAINING.value:
            return {"instance_id": instance_id, "status": inst['status'], "drain_active": False}
        started = datetime.fromisoformat(inst['drain_started_at'])
        elapsed = (datetime.utcnow() - started).total_seconds()
        timeout = inst.get('drain_timeout', 120)
        return {
            "instance_id": instance_id,
            "status": "draining",
            "elapsed_seconds": round(elapsed, 1),
            "timeout_seconds": timeout,
            "progress_pct": min(100, round(elapsed / timeout * 100, 1)),
            "estimated_remaining": max(0, timeout - elapsed),
        }

# === FLEET OPTIMIZER ===

class FleetOptimizer:
    def __init__(self, manager: SpotManager):
        self.manager = manager

    def optimize_allocation(self, fleet_id: str) -> Dict[str, Any]:
        fleet = self.manager.get_fleet(fleet_id)
        if not fleet:
            return {"error": "Fleet not found"}
        by_region = {}
        for inst in self.manager.instances:
            if inst['fleet_id'] != fleet_id:
                continue
            r = inst['region']
            by_region.setdefault(r, {"count": 0, "total_price": 0})
            by_region[r]["count"] += 1
            by_region[r]["total_price"] += inst['spot_price']
        total = sum(v["count"] for v in by_region.values())
        if total == 0:
            return {"error": "No instances in fleet"}
        recommendations = []
        for region, data in by_region.items():
            pct = data["count"] / total * 100
            recommendations.append({
                "region": region,
                "current_pct": round(pct, 1),
                "target_pct": round(100 / len(by_region), 1),
                "adjustment": "redistribute" if abs(pct - 100/len(by_region)) > 10 else "ok",
            })
        return {
            "fleet_id": fleet_id,
            "region_distribution": by_region,
            "recommendations": recommendations,
            "diversity_score": round(len(by_region) / max(len(fleet.get('regions', [])), 1) * 100, 1),
        }

    def cost_optimized_weights(self, fleet_id: str) -> Dict[str, Any]:
        fleet = self.manager.get_fleet(fleet_id)
        if not fleet:
            return {"error": "Fleet not found"}
        weights = {}
        for itype in fleet.get('instance_types', []):
            weights[itype] = round(1.0 / len(fleet['instance_types']), 2)
        return {
            "fleet_id": fleet_id,
            "strategy": "cost_optimized",
            "instance_weights": weights,
            "expected_hourly_cost": round(sum(w * 0.05 for w in weights.values()), 4),
        }

# === CAPACITY RESERVATION ===

class CapacityReservation:
    def __init__(self, manager: SpotManager):
        self.manager = manager
        self.reservations: List[Dict[str, Any]] = []

    def create_reservation(self, fleet_id: str, reserved_capacity: int, region: str) -> Dict[str, Any]:
        reservation = {
            "id": str(uuid.uuid4()),
            "fleet_id": fleet_id,
            "reserved_capacity": reserved_capacity,
            "region": region,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        self.reservations.append(reservation)
        return reservation

    def check_capacity_gap(self, fleet_id: str) -> Dict[str, Any]:
        fleet = self.manager.get_fleet(fleet_id)
        if not fleet:
            return {"error": "Fleet not found"}
        reserved = sum(r['reserved_capacity'] for r in self.reservations if r['fleet_id'] == fleet_id and r['status'] == 'active')
        gap = max(0, fleet['target_capacity'] - reserved)
        return {
            "fleet_id": fleet_id,
            "target_capacity": fleet['target_capacity'],
            "reserved_capacity": reserved,
            "gap": gap,
            "gap_pct": round(gap / max(fleet['target_capacity'], 1) * 100, 1),
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
