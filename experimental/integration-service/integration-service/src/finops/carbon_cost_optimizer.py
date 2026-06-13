"""Feature 28: Carbon-Aware Cost Optimization - Combine cost and carbon data"""

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


class CarbonIntensityLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class OptimizationStrategy(Enum):
    COST_FIRST = "cost_first"
    CARBON_FIRST = "carbon_first"
    BALANCED = "balanced"
    GREEN_CHEAP = "green_cheap"


class RecommendationType(Enum):
    REGION_SHIFT = "region_shift"
    TIME_SHIFT = "time_shift"
    PROVIDER_SHIFT = "provider_shift"
    INSTANCE_CHANGE = "instance_change"


REGION_CARBON_MAP = {
    "us-east-1": 0.42, "us-west-1": 0.35, "us-west-2": 0.28,
    "eu-west-1": 0.25, "eu-west-2": 0.26, "eu-central-1": 0.32,
    "eu-north-1": 0.12, "eu-south-1": 0.38,
    "ap-southeast-1": 0.48, "ap-southeast-2": 0.72,
    "ap-northeast-1": 0.45, "ap-south-1": 0.62,
    "sa-east-1": 0.38, "ca-central-1": 0.29,
    "us-gov-west-1": 0.33,
}

REGION_COST_MULTIPLIER = {
    "us-east-1": 1.0, "us-west-1": 1.08, "us-west-2": 1.04,
    "eu-west-1": 1.12, "eu-west-2": 1.10, "eu-central-1": 1.14,
    "eu-north-1": 1.09, "eu-south-1": 1.15,
    "ap-southeast-1": 1.22, "ap-southeast-2": 1.28,
    "ap-northeast-1": 1.25, "ap-south-1": 1.18,
    "sa-east-1": 1.35, "ca-central-1": 1.05,
}


class CarbonCostOptimizer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.assets_file = _data_file('carbon_assets.json')
        self.recommendations_file = _data_file('carbon_recommendations.json')
        self.carbon_data_file = _data_file('carbon_intensity_data.json')
        self.assets: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.carbon_history: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.assets_file, 'assets'), (self.recommendations_file, 'recommendations'),
                           (self.carbon_data_file, 'carbon_history')]:
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

    def register_asset(self, name: str, provider: str, region: str,
                       monthly_cost: float, estimated_kwh: float = None) -> Dict[str, Any]:
        carbon_intensity = REGION_CARBON_MAP.get(region, 0.4)
        kwh = estimated_kwh or round(monthly_cost * random.uniform(5, 15), 2)
        monthly_co2 = round(kwh * carbon_intensity / 1000, 4)
        asset = {
            "id": str(uuid.uuid4()),
            "name": name,
            "provider": provider,
            "region": region,
            "monthly_cost": monthly_cost,
            "estimated_monthly_kwh": kwh,
            "carbon_intensity_kg_per_kwh": carbon_intensity,
            "estimated_monthly_co2_kg": monthly_co2,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.assets.append(asset)
        return asset

    def get_carbon_intensity(self, region: str) -> Dict[str, Any]:
        intensity = REGION_CARBON_MAP.get(region, 0.42)
        level = self._intensity_level(intensity)
        return {
            "region": region,
            "intensity_kg_per_kwh": intensity,
            "level": level.value,
            "grid_mix": "renewable_dominant" if level in [CarbonIntensityLevel.VERY_LOW, CarbonIntensityLevel.LOW] else "mixed",
        }

    def _intensity_level(self, intensity: float) -> CarbonIntensityLevel:
        if intensity <= 0.15:
            return CarbonIntensityLevel.VERY_LOW
        elif intensity <= 0.25:
            return CarbonIntensityLevel.LOW
        elif intensity <= 0.35:
            return CarbonIntensityLevel.MODERATE
        elif intensity <= 0.50:
            return CarbonIntensityLevel.HIGH
        return CarbonIntensityLevel.VERY_HIGH

    def get_asset_carbon_footprint(self, asset_id: str) -> Dict[str, Any]:
        asset = next((a for a in self.assets if a['id'] == asset_id), None)
        if not asset:
            return {"error": "Asset not found"}
        monthly_co2 = asset['estimated_monthly_co2_kg']
        annual_co2 = monthly_co2 * 12
        intensity = REGION_CARBON_MAP.get(asset['region'], 0.42)
        greener_regions = [(r, idx) for r, idx in REGION_CARBON_MAP.items() if idx < intensity * 0.8 and r != asset['region']]
        return {
            "asset_id": asset_id,
            "name": asset['name'],
            "provider": asset['provider'],
            "region": asset['region'],
            "monthly_cost": asset['monthly_cost'],
            "monthly_co2_kg": round(monthly_co2, 4),
            "annual_co2_kg": round(annual_co2, 4),
            "annual_co2_tons": round(annual_co2 / 1000, 3),
            "carbon_intensity_level": self._intensity_level(intensity).value,
            "greener_regions": [{"region": r, "carbon_reduction_pct": round((1 - idx / intensity) * 100, 1)} for r, idx in greener_regions[:3]],
        }

    def generate_recommendations(self, asset_id: str = None,
                                 strategy: str = "balanced") -> List[Dict[str, Any]]:
        targets = [asset_id] if asset_id else [a['id'] for a in self.assets]
        if not targets:
            self._seed_mock_assets()
            targets = [a['id'] for a in self.assets]

        new_recs = []
        for aid in targets:
            asset = next((a for a in self.assets if a['id'] == aid), None)
            if not asset:
                continue

            current_intensity = REGION_CARBON_MAP.get(asset['region'], 0.42)
            current_cost = asset['monthly_cost']
            current_co2 = asset['estimated_monthly_co2_kg']

            recs_for_asset = []
            for region, intensity in REGION_CARBON_MAP.items():
                if region == asset['region']:
                    continue
                cost_mult = REGION_COST_MULTIPLIER.get(region, 1.0)
                new_cost = round(current_cost * cost_mult, 2)
                carbon_reduction_pct = round((1 - intensity / max(current_intensity, 0.01)) * 100, 1)
                new_co2 = round(current_co2 * (intensity / max(current_intensity, 0.01)), 4)

                cost_change = new_cost - current_cost
                carbon_change = new_co2 - current_co2

                if strategy == OptimizationStrategy.COST_FIRST.value and cost_change > 0:
                    continue
                if strategy == OptimizationStrategy.CARBON_FIRST.value and carbon_change > 0:
                    continue
                if strategy == OptimizationStrategy.GREEN_CHEAP.value and (cost_change > 0 or carbon_change > 0):
                    continue

                score = self._calculate_optimization_score(cost_change, carbon_change, strategy)
                if score < 0:
                    continue

                rec = {
                    "id": str(uuid.uuid4()),
                    "asset_id": aid,
                    "asset_name": asset['name'],
                    "current_region": asset['region'],
                    "recommended_region": region,
                    "strategy": strategy,
                    "type": RecommendationType.REGION_SHIFT.value,
                    "current_monthly_cost": current_cost,
                    "new_monthly_cost": new_cost,
                    "monthly_cost_change": round(cost_change, 2),
                    "monthly_savings": round(max(0, -cost_change), 2),
                    "current_monthly_co2_kg": round(current_co2, 4),
                    "new_monthly_co2_kg": round(new_co2, 4),
                    "monthly_co2_reduction_kg": round(max(0, current_co2 - new_co2), 4),
                    "carbon_reduction_pct": max(0, carbon_reduction_pct),
                    "optimization_score": round(score, 2),
                    "created_at": datetime.utcnow().isoformat(),
                }
                recs_for_asset.append(rec)

            recs_for_asset.sort(key=lambda x: x['optimization_score'], reverse=True)
            new_recs.extend(recs_for_asset[:3])

        self.recommendations.extend(new_recs)
        self._save_recommendations()
        return new_recs

    def _calculate_optimization_score(self, cost_change: float, carbon_change: float, strategy: str) -> float:
        if strategy == OptimizationStrategy.COST_FIRST.value:
            return -cost_change - abs(carbon_change) * 0.3
        elif strategy == OptimizationStrategy.CARBON_FIRST.value:
            return -carbon_change * 2 - abs(cost_change) * 0.5
        elif strategy == OptimizationStrategy.GREEN_CHEAP.value:
            return (-cost_change * 1.5) + (-carbon_change * 1.5)
        else:
            return -cost_change - carbon_change

    def _seed_mock_assets(self):
        mock = [
            ("api-servers", "aws", "us-east-1", 4500, 22000),
            ("data-processing", "aws", "us-west-2", 8200, 41000),
            ("database-cluster", "aws", "eu-west-1", 3500, 14000),
            ("ml-training", "gcp", "us-central1", 12000, 60000),
            ("cdn-origin", "azure", "eastus", 2800, 11200),
        ]
        for name, provider, region, cost, kwh in mock:
            self.register_asset(name, provider, region, cost, kwh)

    def get_recommendations(self, asset_id: str = None, strategy: str = None) -> List[Dict[str, Any]]:
        result = self.recommendations
        if asset_id:
            result = [r for r in result if r['asset_id'] == asset_id]
        if strategy:
            result = [r for r in result if r['strategy'] == strategy]
        return sorted(result, key=lambda x: x['optimization_score'], reverse=True)

    def get_trade_off_analysis(self, asset_id: str) -> Dict[str, Any]:
        asset = next((a for a in self.assets if a['id'] == asset_id), None)
        if not asset:
            return {"error": "Asset not found"}
        recommendations = [r for r in self.recommendations if r['asset_id'] == asset_id]
        if not recommendations:
            recommendations = self.generate_recommendations(asset_id)

        best_cost = min(recommendations, key=lambda r: r['new_monthly_cost']) if recommendations else None
        best_carbon = min(recommendations, key=lambda r: r['new_monthly_co2_kg']) if recommendations else None
        best_balanced = max(recommendations, key=lambda r: r['optimization_score']) if recommendations else None

        return {
            "asset_id": asset_id,
            "asset_name": asset['name'],
            "current": {"region": asset['region'], "cost": asset['monthly_cost'], "co2_kg": asset['estimated_monthly_co2_kg']},
            "best_for_cost": best_cost,
            "best_for_carbon": best_carbon,
            "best_balanced": best_balanced,
            "recommendations_count": len(recommendations),
        }

    def get_sustainability_budget(self) -> Dict[str, Any]:
        total_co2 = sum(a['estimated_monthly_co2_kg'] for a in self.assets)
        total_cost = sum(a['monthly_cost'] for a in self.assets)
        avg_intensity = sum(REGION_CARBON_MAP.get(a['region'], 0.42) for a in self.assets) / max(len(self.assets), 1)
        implemented_savings = sum(
            r.get('monthly_savings', 0) for r in self.recommendations
            if r.get('implemented', False)
        )
        return {
            "total_assets": len(self.assets),
            "total_monthly_co2_kg": round(total_co2, 2),
            "total_annual_co2_tons": round(total_co2 * 12 / 1000, 3),
            "total_monthly_cost": round(total_cost, 2),
            "avg_carbon_intensity": round(avg_intensity, 3),
            "avg_intensity_level": self._intensity_level(avg_intensity).value,
            "implemented_monthly_savings": round(implemented_savings, 2),
            "recommendations_pending": len([r for r in self.recommendations if not r.get('implemented')]),
        }

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class CarbonOptimizerError(Exception): pass

@dataclass
class CarbonAsset:
    name: str
    provider: str
    region: str
    monthly_cost: float
    kwh: float = 0.0
    resource_type: str = "compute"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_carbon_asset(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('name'): errors.append("name is required")
    if data.get('provider') not in ['aws', 'azure', 'gcp']: errors.append("provider must be aws/azure/gcp")
    if not data.get('region'): errors.append("region is required")
    return errors

def compute_carbon_footprint(monthly_kwh: float, region_intensity: float) -> Dict[str, Any]:
    monthly_co2_kg = monthly_kwh * region_intensity
    annual_co2_tons = monthly_co2_kg * 12 / 1000
    return {
        "monthly_kwh": round(monthly_kwh, 2),
        "carbon_intensity_kg_per_kwh": region_intensity,
        "monthly_co2_kg": round(monthly_co2_kg, 2),
        "annual_co2_tons": round(annual_co2_tons, 3),
        "equivalent_car_miles": round(annual_co2_tons * 2500, 0),
    }

def evaluate_tradeoff(current_cost: float, current_co2: float, options: List[Dict[str, Any]]) -> Dict[str, Any]:
    best_cost = min(options, key=lambda o: o.get('new_cost', current_cost)) if options else None
    best_carbon = min(options, key=lambda o: o.get('new_co2', current_co2)) if options else None
    return {
        "current": {"monthly_cost": current_cost, "monthly_co2_kg": current_co2},
        "best_for_cost": best_cost,
        "best_for_carbon": best_carbon,
        "cost_carbon_tradeoff": best_cost and best_carbon and best_cost.get('new_cost') != best_carbon.get('new_cost'),
    }

def estimate_carbon_savings(asset: Dict[str, Any], target_region: str) -> Dict[str, Any]:
    carbon_map = {'us-east-1': 0.42, 'us-west-2': 0.30, 'eu-west-1': 0.25, 'eu-central-1': 0.32, 'ap-southeast-1': 0.55}
    current_intensity = carbon_map.get(asset.get('region', 'us-east-1'), 0.42)
    target_intensity = carbon_map.get(target_region, 0.40)
    kwh = asset.get('kwh', asset.get('monthly_cost', 1000) * 10)
    current_co2 = kwh * current_intensity
    target_co2 = kwh * target_intensity
    return {
        "asset_name": asset.get('name'),
        "current_region": asset.get('region'),
        "target_region": target_region,
        "current_monthly_co2_kg": round(current_co2, 2),
        "target_monthly_co2_kg": round(target_co2, 2),
        "co2_reduction_kg": round(current_co2 - target_co2, 2),
        "co2_reduction_pct": round(((current_co2 - target_co2) / max(current_co2, 0.01)) * 100, 1),
        "cost_multiplier": 0.95 if target_intensity < current_intensity else 1.10,
    }

def get_region_carbon_intensity(region: str) -> Dict[str, Any]:
    intensities = {'us-east-1': 0.42, 'us-west-1': 0.35, 'us-west-2': 0.30, 'eu-west-1': 0.25, 'eu-central-1': 0.32, 'eu-west-2': 0.28, 'eu-north-1': 0.20, 'ca-central-1': 0.22, 'ap-southeast-1': 0.55, 'ap-northeast-1': 0.48, 'ap-south-1': 0.60, 'sa-east-1': 0.38}
    intensity = intensities.get(region, 0.40)
    level = "low" if intensity < 0.28 else ("moderate" if intensity < 0.40 else "high")
    return {"region": region, "carbon_intensity_kg_per_kwh": intensity, "level": level, "grid_renewable_pct": round((1 - intensity / 0.60) * 100, 1)}

def optimize_carbon_region(assets: List[Dict[str, Any]], target_intensity_max: float = 0.30) -> List[Dict[str, Any]]:
    optimizations = []
    for asset in assets:
        current = get_region_carbon_intensity(asset.get('region', 'us-east-1'))
        if current['carbon_intensity_kg_per_kwh'] > target_intensity_max:
            for region, intensity in {'eu-west-1': 0.25, 'us-west-2': 0.30, 'eu-north-1': 0.20}.items():
                if intensity < current['carbon_intensity_kg_per_kwh']:
                    savings = estimate_carbon_savings(asset, region)
                    optimizations.append(savings)
                    break
    return sorted(optimizations, key=lambda x: x.get('co2_reduction_kg', 0), reverse=True)

def generate_sustainability_report(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_kwh = sum(a.get('kwh', a.get('monthly_cost', 1000) * 10) for a in assets)
    total_cost = sum(a.get('monthly_cost', 0) for a in assets)
    avg_intensity = sum(get_region_carbon_intensity(a.get('region', 'us-east-1'))['carbon_intensity_kg_per_kwh'] for a in assets) / max(len(assets), 1)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_assets": len(assets),
        "total_monthly_kwh": round(total_kwh, 2),
        "total_monthly_co2_kg": round(total_kwh * avg_intensity, 2),
        "total_annual_co2_tons": round(total_kwh * avg_intensity * 12 / 1000, 3),
        "total_monthly_cost": round(total_cost, 2),
        "avg_carbon_intensity": round(avg_intensity, 3),
        "recommendations": [
            "Migrate high-intensity workloads to low-carbon regions",
            "Increase spot instance usage to reduce embodied carbon",
            "Schedule batch jobs during renewable energy peaks",
        ],
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class CarbonBatchProcessor:
    def __init__(self, optimizer: CarbonCostOptimizer):
        self.optimizer = optimizer
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_register(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for a in assets:
            try:
                result = self.optimizer.register_asset(
                    name=a['name'], provider=a['provider'],
                    region=a['region'], monthly_cost=a.get('monthly_cost', 1000),
                    estimated_kwh=a.get('kwh')
                )
                results.append({"success": True, "asset": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": a})
        return results

    async def batch_generate_recs(self, asset_ids: List[str], strategy: str = "balanced") -> List[Dict[str, Any]]:
        tasks = [self.optimizer.generate_recommendations(aid, strategy) for aid in asset_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def export_assets_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "provider", "region", "monthly_cost", "monthly_co2_kg"])
        for a in self.optimizer.assets:
            writer.writerow([a['id'], a['name'], a['provider'], a['region'], a['monthly_cost'], a.get('estimated_monthly_co2_kg', 0)])
        return output.getvalue()

# === ANALYTICS ===

class CarbonAnalytics:
    def __init__(self, optimizer: CarbonCostOptimizer):
        self.optimizer = optimizer

    def regional_breakdown(self) -> Dict[str, Any]:
        regions = {}
        for a in self.optimizer.assets:
            r = a['region']
            if r not in regions:
                regions[r] = {"asset_count": 0, "total_cost": 0, "total_co2": 0}
            regions[r]["asset_count"] += 1
            regions[r]["total_cost"] += a['monthly_cost']
            regions[r]["total_co2"] += a.get('estimated_monthly_co2_kg', 0)
        return regions

    def provider_breakdown(self) -> Dict[str, Any]:
        providers = {}
        for a in self.optimizer.assets:
            p = a['provider']
            if p not in providers:
                providers[p] = {"asset_count": 0, "total_cost": 0, "avg_intensity": 0}
            providers[p]["asset_count"] += 1
            providers[p]["total_cost"] += a['monthly_cost']
        for p in providers:
            assets_p = [a for a in self.optimizer.assets if a['provider'] == p]
            intensities = [__import__('services.integration_service.src.finops.carbon_cost_optimizer', fromlist=['REGION_CARBON_MAP']).REGION_CARBON_MAP.get(a['region'], 0.42) for a in assets_p]
            providers[p]["avg_intensity"] = round(sum(intensities) / max(len(intensities), 1), 3)
        return providers

    def savings_potential(self) -> Dict[str, Any]:
        recs = self.optimizer.recommendations
        max_cost_saving = max((r.get('monthly_savings', 0) for r in recs), default=0)
        max_carbon_reduction = max((r.get('monthly_co2_reduction_kg', 0) for r in recs), default=0)
        return {
            "total_recs": len(recs),
            "max_monthly_cost_saving": round(max_cost_saving, 2),
            "max_monthly_co2_reduction": round(max_carbon_reduction, 4),
            "implemented_recs": sum(1 for r in recs if r.get('implemented', False)),
        }

class CarbonPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items
        self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size
        end = start + self.page_size
        total_pages = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {
            "page": page,
            "page_size": self.page_size,
            "total_items": len(self.items),
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "items": self.items[start:end],
        }

# === ADVANCED CARBON OPTIMIZATION ===

class CarbonForecaster:
    def __init__(self, optimizer: CarbonCostOptimizer):
        self.optimizer = optimizer

    def predict_carbon_trend(self, asset_id: str, months: int = 12) -> Dict[str, Any]:
        asset = next((a for a in self.optimizer.assets if a['id'] == asset_id), None)
        if not asset:
            return {"error": "Asset not found"}
        base_co2 = asset['estimated_monthly_co2_kg']
        projections = []
        for m in range(1, months + 1):
            projected = base_co2 * (1 - 0.02 * m) + base_co2 * 0.05 * (m / 12)
            projections.append({"month": m, "projected_co2_kg": round(max(0, projected), 4)})
        return {
            "asset_id": asset_id,
            "current_monthly_co2": base_co2,
            "annual_current": round(base_co2 * 12, 4),
            "projected_annual": round(sum(p['projected_co2_kg'] for p in projections), 4),
            "monthly_projections": projections,
        }

    def carbon_budget(self, asset_ids: List[str], max_co2_monthly: float) -> Dict[str, Any]:
        total_current = sum(
            next((a['estimated_monthly_co2_kg'] for a in self.optimizer.assets if a['id'] == aid), 0)
            for aid in asset_ids
        )
        is_over = total_current > max_co2_monthly
        reduction_needed = max(0, total_current - max_co2_monthly)
        return {
            "asset_count": len(asset_ids),
            "current_total_co2": round(total_current, 4),
            "budget_limit": round(max_co2_monthly, 4),
            "is_over_budget": is_over,
            "reduction_needed_kg": round(reduction_needed, 4),
            "reduction_pct": round((reduction_needed / max(total_current, 0.01)) * 100, 1),
        }

# === REGION MIGRATION PLANNER ===

class RegionMigrationPlanner:
    def __init__(self, optimizer: CarbonCostOptimizer):
        self.optimizer = optimizer

    def plan_migration(self, asset_id: str, target_region: str) -> Dict[str, Any]:
        asset = next((a for a in self.optimizer.assets if a['id'] == asset_id), None)
        if not asset:
            return {"error": "Asset not found"}
        current_intensity = REGION_CARBON_MAP.get(asset['region'], 0.42)
        target_intensity = REGION_CARBON_MAP.get(target_region, 0.40)
        carbon_reduction = max(0, current_intensity - target_intensity) / current_intensity * 100 if current_intensity > 0 else 0
        cost_mult = REGION_COST_MULTIPLIER.get(target_region, 1.0)
        new_cost = asset['monthly_cost'] * cost_mult
        steps = [
            "Provision resources in target region",
            "Replicate data and configurations",
            "Update DNS and routing",
            "Validate functionality in new region",
            "Migrate traffic gradually",
            "Decommission resources in source region",
        ]
        return {
            "asset_id": asset_id,
            "asset_name": asset['name'],
            "source_region": asset['region'],
            "target_region": target_region,
            "current_cost": asset['monthly_cost'],
            "new_cost": round(new_cost, 2),
            "cost_change": round(new_cost - asset['monthly_cost'], 2),
            "current_carbon_intensity": current_intensity,
            "target_carbon_intensity": target_intensity,
            "carbon_reduction_pct": round(carbon_reduction, 1),
            "estimated_duration_hours": 24,
            "migration_steps": steps,
            "risk_level": "low" if carbon_reduction > 20 else "medium",
        }

    def bulk_migration_plan(self, asset_ids: List[str], target_region: str) -> List[Dict[str, Any]]:
        return [self.plan_migration(aid, target_region) for aid in asset_ids]

# === ENERGY MIX ANALYZER ===

class EnergyMixAnalyzer:
    def __init__(self):
        self.regional_renewable_pct = {
            "eu-north-1": 0.95, "eu-west-1": 0.55, "eu-west-2": 0.48,
            "ca-central-1": 0.85, "us-west-2": 0.42, "us-east-1": 0.28,
            "us-west-1": 0.32,
        }

    def get_mix(self, region: str) -> Dict[str, Any]:
        renewable = self.regional_renewable_pct.get(region, 0.30)
        return {
            "region": region,
            "renewable_pct": renewable * 100,
            "non_renewable_pct": (1 - renewable) * 100,
            "primary_source": "hydro" if renewable > 0.7 else "wind" if renewable > 0.4 else "gas",
            "low_carbon_hours": ["09:00-15:00 UTC"] if renewable > 0.3 else ["Limited"],
        }

    def optimal_schedule(self, region: str) -> Dict[str, Any]:
        mix = self.get_mix(region)
        return {
            "region": region,
            "recommended_window": mix["low_carbon_hours"],
            "off_peak_renewable_pct": mix["renewable_pct"] * 1.1,
            "peak_renewable_pct": mix["renewable_pct"] * 0.85,
        }

# === CARBON CREDIT TRACKER ===

class CarbonCreditTracker:
    def __init__(self):
        self.credits: List[Dict[str, Any]] = []

    def purchase_credit(self, amount_tons: float, cost_per_ton: float, provider: str = "default") -> Dict[str, Any]:
        credit = {
            "id": str(uuid.uuid4()),
            "amount_tons": amount_tons,
            "cost_per_ton": cost_per_ton,
            "total_cost": round(amount_tons * cost_per_ton, 2),
            "provider": provider,
            "purchased_at": datetime.utcnow().isoformat(),
            "retired": False,
        }
        self.credits.append(credit)
        return credit

    def retire_credit(self, credit_id: str) -> Dict[str, Any]:
        credit = next((c for c in self.credits if c['id'] == credit_id), None)
        if not credit:
            return {"error": "Credit not found"}
        credit['retired'] = True
        credit['retired_at'] = datetime.utcnow().isoformat()
        return credit

    def offset_footprint(self, footprint_kg: float) -> Dict[str, Any]:
        footprint_tons = footprint_kg / 1000
        active = [c for c in self.credits if not c['retired']]
        total_active = sum(c['amount_tons'] for c in active)
        remaining = total_active - footprint_tons
        return {
            "footprint_tons": round(footprint_tons, 3),
            "available_credits_tons": round(total_active, 3),
            "offset_possible": total_active >= footprint_tons,
            "remaining_after_offset": round(remaining, 3),
        }

# === EMISSIONS REPORTING ===

class EmissionsReporter:
    def __init__(self, optimizer: CarbonCostOptimizer):
        self.optimizer = optimizer

    def generate_emissions_report(self, year: int = 2025) -> Dict[str, Any]:
        total_monthly = sum(a['estimated_monthly_co2_kg'] for a in self.optimizer.assets)
        annual = total_monthly * 12
        by_provider = {}
        for a in self.optimizer.assets:
            p = a.get('provider', 'unknown')
            by_provider[p] = by_provider.get(p, 0) + a['estimated_monthly_co2_kg'] * 12
        return {
            "year": year,
            "total_annual_emissions_kg": round(annual, 2),
            "total_annual_emissions_tons": round(annual / 1000, 3),
            "by_provider": {k: round(v, 2) for k, v in by_provider.items()},
            "asset_count": len(self.optimizer.assets),
            "recommendations": [
                "Migrate high-intensity workloads to low-carbon regions",
                "Increase usage of spot/preemptible instances",
                "Implement auto-scaling to match demand precisely",
                "Consider carbon offset purchases for unavoidable emissions",
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
