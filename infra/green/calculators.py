"""Green computing calculation engines and carbon models."""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


CARBON_INTENSITY_DEFAULTS = {
    "us-east": 0.294,
    "us-west": 0.201,
    "eu-central": 0.251,
    "eu-west": 0.182,
    "ap-southeast": 0.408,
    "ap-northeast": 0.378,
    "sa-east": 0.185,
    "au-east": 0.412,
}

ELECTRICITY_PRICES = {
    "us-east": 0.12,
    "us-west": 0.14,
    "eu-central": 0.22,
    "eu-west": 0.18,
    "ap-southeast": 0.15,
    "ap-northeast": 0.16,
    "sa-east": 0.10,
    "au-east": 0.20,
}


@dataclass
class CarbonCalculation:
    total_energy_kwh: float
    carbon_intensity: float
    total_co2_kg: float
    scope_1_kg: float
    scope_2_kg: float
    scope_3_kg: float
    renewable_pct: float
    offsets_purchased: float
    net_co2_kg: float
    carbon_neutral: bool


class CarbonCalculator:
    """Calculates carbon emissions from energy consumption."""

    def __init__(self, region: str = "us-east"):
        self.region = region
        self.intensity = CARBON_INTENSITY_DEFAULTS.get(region, 0.3)

    def calculate(self, energy_kwh: float, renewable_pct: float = 0.0,
                  scope_1_kg: float = 0.0, scope_3_kg: float = 0.0,
                  offsets_kg: float = 0.0) -> CarbonCalculation:
        grid_kwh = energy_kwh * (1 - renewable_pct / 100.0)
        scope_2_kg = grid_kwh * self.intensity
        total = scope_1_kg + scope_2_kg + scope_3_kg
        net = max(0, total - offsets_kg)
        return CarbonCalculation(
            total_energy_kwh=energy_kwh,
            carbon_intensity=self.intensity,
            total_co2_kg=round(total, 2),
            scope_1_kg=round(scope_1_kg, 2),
            scope_2_kg=round(scope_2_kg, 2),
            scope_3_kg=round(scope_3_kg, 2),
            renewable_pct=renewable_pct,
            offsets_purchased=offsets_kg,
            net_co2_kg=round(net, 2),
            carbon_neutral=net <= 0,
        )

    def with_region(self, region: str) -> "CarbonCalculator":
        return CarbonCalculator(region)


class EnergyCostCalculator:
    """Calculates energy costs."""

    def __init__(self, region: str = "us-east"):
        self.rate_per_kwh = ELECTRICITY_PRICES.get(region, 0.12)

    def calculate_cost(self, energy_kwh: float) -> float:
        return round(energy_kwh * self.rate_per_kwh, 2)

    def calculate_monthly(self, avg_daily_kwh: float) -> Dict[str, float]:
        monthly_kwh = avg_daily_kwh * 30
        return {
            "monthly_kwh": round(monthly_kwh, 2),
            "monthly_cost": round(monthly_kwh * self.rate_per_kwh, 2),
            "annual_cost": round(monthly_kwh * 12 * self.rate_per_kwh, 2),
        }

    def project_savings(self, current_kwh: float, target_kwh: float) -> Dict[str, Any]:
        savings_kwh = current_kwh - target_kwh
        savings_usd = savings_kwh * self.rate_per_kwh
        return {
            "current_kwh": current_kwh,
            "target_kwh": target_kwh,
            "savings_kwh": round(savings_kwh, 2),
            "savings_pct": round((savings_kwh / current_kwh) * 100, 1) if current_kwh > 0 else 0,
            "savings_usd": round(savings_usd, 2),
            "savings_usd_annual": round(savings_usd * 365, 2),
        }


class PUECalculator:
    """Calculates Power Usage Effectiveness metrics."""

    def calculate_pue(self, total_power_kw: float, it_load_kw: float) -> float:
        if it_load_kw <= 0:
            return 0.0
        return round(total_power_kw / it_load_kw, 2)

    def calculate_cooling_load(self, total_power_kw: float, it_load_kw: float) -> float:
        return round(total_power_kw - it_load_kw, 2)

    def calculate_efficiency_score(self, pue: float) -> float:
        if pue <= 0:
            return 0
        ideal_pue = 1.0
        score = max(0, min(100, (1.0 / pue) * 100))
        return round(score, 1)

    def estimate_savings(self, current_pue: float, target_pue: float,
                         it_load_kw: float) -> Dict[str, Any]:
        current_total = current_pue * it_load_kw
        target_total = target_pue * it_load_kw
        savings_kw = current_total - target_total
        return {
            "current_total_power_kw": round(current_total, 2),
            "target_total_power_kw": round(target_total, 2),
            "savings_kw": round(savings_kw, 2),
            "savings_kwh_daily": round(savings_kw * 24, 2),
            "savings_kwh_annual": round(savings_kw * 8760, 2),
        }

    def get_efficiency_rating(self, pue: float) -> str:
        if pue <= 1.1:
            return "excellent"
        elif pue <= 1.2:
            return "good"
        elif pue <= 1.4:
            return "average"
        elif pue <= 1.6:
            return "poor"
        else:
            return "critical"


class OffsetCalculator:
    """Calculates carbon offset requirements."""

    TREES_PER_TONNE = 45
    SOLAR_KWH_PER_TONNE = 3400

    def calculate_required_offsets(self, total_co2_kg: float,
                                   target_neutral_pct: float = 100.0) -> Dict[str, Any]:
        required_tonnes = total_co2_kg / 1000.0 * (target_neutral_pct / 100.0)
        return {
            "total_co2_tonnes": round(total_co2_kg / 1000.0, 2),
            "required_offsets_tonnes": round(required_tonnes, 2),
            "trees_required": round(required_tonnes * self.TREES_PER_TONNE),
            "solar_kwh_equivalent": round(required_tonnes * self.SOLAR_KWH_PER_TONNE),
            "estimated_cost_usd": round(required_tonnes * 15.0, 2),
        }

    def calculate_project_impact(self, project_type: str,
                                 tonnes_per_year: float) -> Dict[str, Any]:
        factors = {
            "reforestation": {"co2_per_tonne": 1.0, "cost_per_tonne": 12.0},
            "renewable_energy": {"co2_per_tonne": 0.8, "cost_per_tonne": 8.0},
            "methane_capture": {"co2_per_tonne": 1.2, "cost_per_tonne": 10.0},
            "direct_air_capture": {"co2_per_tonne": 1.0, "cost_per_tonne": 250.0},
        }
        factor = factors.get(project_type, factors["reforestation"])
        return {
            "project_type": project_type,
            "tonnes_per_year": tonnes_per_year,
            "effective_co2_reduction": round(tonnes_per_year * factor["co2_per_tonne"], 2),
            "cost_per_tonne": factor["cost_per_tonne"],
            "annual_cost": round(tonnes_per_year * factor["cost_per_tonne"], 2),
            "trees_equivalent": round(tonnes_per_year * self.TREES_PER_TONNE),
        }


class SustainabilityScore:
    """Computes comprehensive sustainability scores."""

    def __init__(self):
        self.weights = {
            "energy_efficiency": 0.25,
            "renewable_energy": 0.20,
            "carbon_footprint": 0.25,
            "water_usage": 0.10,
            "waste_management": 0.10,
            "compliance": 0.10,
        }

    def compute(self, pue: float, renewable_pct: float,
                carbon_intensity: float, water_usage_l_per_kwh: float = 1.8,
                waste_recycling_pct: float = 60.0,
                compliance_score: float = 100.0) -> Dict[str, Any]:
        energy_score = max(0, min(100, (1.0 / pue) * 100)) if pue > 0 else 0
        renewable_score = renewable_pct
        carbon_score = max(0, min(100, 100 - (carbon_intensity / 5)))
        water_score = max(0, min(100, 100 - (water_usage_l_per_kwh * 20)))
        waste_score = waste_recycling_pct
        overall = (
            energy_score * self.weights["energy_efficiency"] +
            renewable_score * self.weights["renewable_energy"] +
            carbon_score * self.weights["carbon_footprint"] +
            water_score * self.weights["water_usage"] +
            waste_score * self.weights["waste_management"] +
            compliance_score * self.weights["compliance"]
        )
        return {
            "overall_score": round(overall, 1),
            "categories": {
                "energy_efficiency": round(energy_score, 1),
                "renewable_energy": round(renewable_score, 1),
                "carbon_footprint": round(carbon_score, 1),
                "water_usage": round(water_score, 1),
                "waste_management": round(waste_score, 1),
                "compliance": round(compliance_score, 1),
            },
            "rating": self._get_rating(overall),
        }

    def _get_rating(self, score: float) -> str:
        if score >= 90:
            return "platinum"
        elif score >= 75:
            return "gold"
        elif score >= 60:
            return "silver"
        elif score >= 40:
            return "bronze"
        else:
            return "standard"

    def compare(self, scores: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        ranked = sorted(scores, key=lambda s: s.get("overall", 0), reverse=True)
        return [
            {**s, "rank": i + 1, "rating": self._get_rating(s.get("overall", 0))}
            for i, s in enumerate(ranked)
        ]


class GreenReporter:
    """Generates comprehensive green computing reports."""

    def generate_sustainability_report(self, facilities: List[Dict[str, Any]],
                                       period_days: int = 30) -> Dict[str, Any]:
        total_power = sum(f.get("total_power_kw", 0) for f in facilities)
        total_it = sum(f.get("it_load_kw", 0) for f in facilities)
        avg_pue = total_power / total_it if total_it > 0 else 0
        energy_kwh = total_power * 24 * period_days
        co2_kg = energy_kwh * 0.294
        return {
            "report_type": "sustainability",
            "period_days": period_days,
            "facilities": len(facilities),
            "total_power_kw": round(total_power, 2),
            "total_it_kw": round(total_it, 2),
            "avg_pue": round(avg_pue, 2),
            "total_energy_kwh": round(energy_kwh, 2),
            "total_co2_kg": round(co2_kg, 2),
            "renewable_pct": 45,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def generate_comparison(self, current: Dict[str, float],
                            baseline: Dict[str, float]) -> Dict[str, Any]:
        changes = {}
        for key in current:
            if key in baseline and baseline[key] != 0:
                changes[key] = round(((current[key] - baseline[key]) / baseline[key]) * 100, 1)
        return {
            "current": current,
            "baseline": baseline,
            "changes_pct": changes,
            "improved": all(v <= 0 for v in changes.values() if isinstance(v, (int, float))),
        }
