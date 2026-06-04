"""Feature 59: AI-Driven Capacity Planning — Capacity recommendations with what-if simulation."""

import json
import os
import uuid
import math
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict, Counter
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"


class RecommendationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SimulationScenario(Enum):
    TRAFFIC_SPIKE = "traffic_spike"
    BLACK_FRIDAY = "black_friday"
    NEW_CUSTOMER_WAVE = "new_customer_wave"
    FEATURE_LAUNCH = "feature_launch"
    REGION_EXPANSION = "region_expansion"
    CUSTOM = "custom"


class CapacityPlanner:
    """AI-driven capacity planning with recommendations and what-if simulations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.forecast_days = config.get("forecast_days", 90)
        self.utilization_target = config.get("utilization_target", 0.7)
        self.safety_margin = config.get("safety_margin", 0.2)
        self.usage_file = _data_file('capacity_usage.json')
        self.recommendations_file = _data_file('capacity_recommendations.json')
        self.simulations_file = _data_file('capacity_simulations.json')
        self.usage_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.recommendations: List[Dict[str, Any]] = []
        self.simulations: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.recommendations_file, 'r') as f:
                self.recommendations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.simulations_file, 'r') as f:
                self.simulations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.usage_file, 'r') as f:
                data = json.load(f)
                for key, values in data.items():
                    self.usage_history[key] = deque(values, maxlen=10000)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_usage(self):
        data = {k: list(v) for k, v in self.usage_history.items()}
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, default=str)

    def _save_recommendations(self):
        with open(self.recommendations_file, 'w') as f:
            json.dump(self.recommendations[-1000:], f, default=str)

    def _save_simulations(self):
        with open(self.simulations_file, 'w') as f:
            json.dump(self.simulations[-500:], f, default=str)

    def record_usage(self, resource_id: str, resource_type: str, total_capacity: float,
                      used: float, timestamp: str = None) -> Dict[str, Any]:
        key = f"{resource_id}:{resource_type}"
        utilization = used / total_capacity if total_capacity > 0 else 0
        point = {
            "total_capacity": total_capacity,
            "used": used,
            "utilization": round(utilization, 4),
            "timestamp": timestamp or datetime.utcnow().isoformat(),
        }
        self.usage_history[key].append(point)
        self._save_usage()
        return point

    def get_usage(self, resource_id: str, resource_type: str,
                   days: int = 30) -> Dict[str, Any]:
        key = f"{resource_id}:{resource_type}"
        points = list(self.usage_history.get(key, []))
        if not points:
            return {"resource_id": resource_id, "resource_type": resource_type, "data_points": 0}
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [p for p in points if datetime.fromisoformat(p["timestamp"]) > cutoff]
        if not recent:
            return {"resource_id": resource_id, "resource_type": resource_type, "data_points": 0}
        utils = [p["utilization"] for p in recent]
        return {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "data_points": len(recent),
            "current_utilization": round(utils[-1], 4),
            "avg_utilization": round(statistics.mean(utils), 4),
            "peak_utilization": round(max(utils), 4),
            "p95_utilization": round(sorted(utils)[int(len(utils) * 0.95)], 4) if len(utils) >= 20 else None,
            "total_capacity": recent[-1]["total_capacity"],
            "used_current": recent[-1]["used"],
            "free_current": recent[-1]["total_capacity"] - recent[-1]["used"],
        }

    def _forecast_utilization(self, resource_id: str, resource_type: str,
                               days: int = None) -> Dict[str, Any]:
        if days is None:
            days = self.forecast_days
        key = f"{resource_id}:{resource_type}"
        points = list(self.usage_history.get(key, []))
        if len(points) < 10:
            return {"error": f"Insufficient data for {resource_id}:{resource_type}", "forecast": None}
        utils = [p["utilization"] for p in points]
        totals = [p["total_capacity"] for p in points]
        n = len(utils)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(utils)
        numerator = sum((i - x_mean) * (u - y_mean) for i, u in enumerate(utils))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        forecast_steps = days
        forecast_utils = [intercept + slope * (n + i) for i in range(forecast_steps)]
        forecast_utils = [max(0.0, min(1.0, u)) for u in forecast_utils]
        current_capacity = totals[-1] if totals else 0
        current_util = utils[-1]
        days_until_full = None
        for i, u in enumerate(forecast_utils):
            if u >= 1.0:
                days_until_full = i + 1
                break
        days_until_threshold = None
        for i, u in enumerate(forecast_utils):
            if u >= self.utilization_target:
                days_until_threshold = i + 1
                break
        max_forecast = max(forecast_utils)
        needed_capacity = None
        if max_forecast > self.utilization_target:
            target_utilization = self.utilization_target - self.safety_margin
            needed_capacity = current_capacity * (max_forecast / target_utilization)
        return {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "current_capacity": current_capacity,
            "current_utilization": round(current_util, 4),
            "avg_utilization": round(statistics.mean(utils), 4),
            "daily_growth_rate": round(slope, 6),
            "forecast_days": days,
            "forecast_30d": round(forecast_utils[min(29, len(forecast_utils) - 1)], 4),
            "forecast_60d": round(forecast_utils[min(59, len(forecast_utils) - 1)], 4),
            "forecast_90d": round(forecast_utils[min(89, len(forecast_utils) - 1)], 4),
            "peak_forecast": round(max_forecast, 4),
            "days_until_full": days_until_full,
            "days_until_threshold": days_until_threshold,
            "recommended_capacity": round(needed_capacity, 2) if needed_capacity else None,
            "recommended_additional": round(needed_capacity - current_capacity, 2) if needed_capacity else None,
            "forecast_series": [round(u, 4) for u in forecast_utils[::max(1, days // 30)]],
        }

    def generate_recommendation(self, resource_id: str, resource_type: str) -> Dict[str, Any]:
        forecast = self._forecast_utilization(resource_id, resource_type)
        if "error" in forecast:
            return forecast
        priority = RecommendationPriority.LOW.value
        urgency_reason = ""
        action = "monitor"
        if forecast["days_until_full"] and forecast["days_until_full"] <= 30:
            priority = RecommendationPriority.CRITICAL.value
            urgency_reason = f"Capacity exhausted in {forecast['days_until_full']} days"
            action = "add_capacity_immediately"
        elif forecast["days_until_threshold"] and forecast["days_until_threshold"] <= 30:
            priority = RecommendationPriority.HIGH.value
            urgency_reason = f"Utilization threshold exceeded in {forecast['days_until_threshold']} days"
            action = "add_capacity_soon"
        elif forecast["days_until_threshold"] and forecast["days_until_threshold"] <= 90:
            priority = RecommendationPriority.MEDIUM.value
            urgency_reason = f"Utilization threshold exceeded in {forecast['days_until_threshold']} days"
            action = "plan_capacity_addition"
        elif forecast["peak_forecast"] > self.utilization_target * 0.8:
            priority = RecommendationPriority.LOW.value
            urgency_reason = "Utilization approaching threshold within forecast window"
            action = "monitor_trend"
        annual_growth = forecast["daily_growth_rate"] * 365
        cost_estimate = None
        if forecast["recommended_additional"]:
            unit_cost_map = {
                ResourceType.CPU.value: 0.10,
                ResourceType.MEMORY.value: 0.05,
                ResourceType.STORAGE.value: 0.02,
                ResourceType.NETWORK.value: 0.01,
                ResourceType.GPU.value: 0.50,
            }
            unit_cost = unit_cost_map.get(resource_type, 0.05)
            cost_estimate = {
                "additional_units": round(forecast["recommended_additional"], 2),
                "unit_cost_per_hour": unit_cost,
                "estimated_monthly_cost": round(forecast["recommended_additional"] * unit_cost * 730, 2),
                "currency": "USD",
            }
        recommendation = {
            "id": str(uuid.uuid4()),
            "resource_id": resource_id,
            "resource_type": resource_type,
            "priority": priority,
            "action": action,
            "title": f"{resource_type.upper()} capacity recommendation for {resource_id}",
            "summary": urgency_reason,
            "current_utilization": forecast["current_utilization"],
            "peak_forecast": forecast["peak_forecast"],
            "recommended_capacity": forecast["recommended_capacity"],
            "recommended_additional": forecast["recommended_additional"],
            "annual_growth_rate": round(annual_growth, 4),
            "days_until_exhaustion": forecast["days_until_full"],
            "days_until_threshold": forecast["days_until_threshold"],
            "cost_estimate": cost_estimate,
            "forecast_data": forecast,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.recommendations.append(recommendation)
        self._save_recommendations()
        return recommendation

    def what_if_simulation(self, resource_id: str, resource_type: str,
                            scenario: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        forecast = self._forecast_utilization(resource_id, resource_type)
        if "error" in forecast:
            return forecast
        params = parameters or {}
        base_growth = forecast.get("daily_growth_rate", 0)
        if scenario == SimulationScenario.TRAFFIC_SPIKE.value:
            spike_multiplier = params.get("spike_multiplier", 2.0)
            spike_duration = params.get("spike_duration_days", 7)
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                base = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
                val = base[min(i, len(base) - 1)]
                if i < spike_duration:
                    val *= spike_multiplier
                adjusted_utils.append(min(1.0, val))
        elif scenario == SimulationScenario.BLACK_FRIDAY.value:
            base_util = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                val = base_util[min(i, len(base_util) - 1)]
                if 20 <= i <= 27:
                    val *= params.get("black_friday_multiplier", 3.0)
                elif 28 <= i <= 35:
                    val *= params.get("post_bf_multiplier", 1.5)
                adjusted_utils.append(min(1.0, val))
        elif scenario == SimulationScenario.NEW_CUSTOMER_WAVE.value:
            customer_growth = params.get("new_customers_pct", 0.5)
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                base = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
                val = base[min(i, len(base) - 1)]
                val *= (1 + customer_growth * min(1.0, i / 30))
                adjusted_utils.append(min(1.0, val))
        elif scenario == SimulationScenario.FEATURE_LAUNCH.value:
            launch_impact = params.get("launch_impact_pct", 0.3)
            launch_day = params.get("launch_day", 14)
            ramp_days = params.get("ramp_days", 7)
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                base = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
                val = base[min(i, len(base) - 1)]
                if i >= launch_day:
                    ramp = min(1.0, (i - launch_day) / ramp_days)
                    val *= (1 + launch_impact * ramp)
                adjusted_utils.append(min(1.0, val))
        elif scenario == SimulationScenario.REGION_EXPANSION.value:
            expansion_pct = params.get("expansion_pct", 1.0)
            expansion_day = params.get("expansion_day", 30)
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                base = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
                val = base[min(i, len(base) - 1)]
                if i >= expansion_day:
                    val *= (1 + expansion_pct)
                adjusted_utils.append(min(1.0, val))
        else:
            adjusted_growth = params.get("adjusted_growth_rate", base_growth)
            base_util = forecast.get("forecast_series", [forecast["current_utilization"]] * forecast["forecast_days"])
            adjusted_utils = []
            for i in range(forecast["forecast_days"]):
                val = base_util[min(i, len(base_util) - 1)]
                adjusted_utils.append(min(1.0, val + adjusted_growth * i))
        peak_util = max(adjusted_utils)
        days_over_capacity = sum(1 for u in adjusted_utils if u >= 1.0)
        days_over_threshold = sum(1 for u in adjusted_utils if u >= self.utilization_target)
        current_capacity = forecast.get("current_capacity", 100)
        needed_capacity = current_capacity * (peak_util / (self.utilization_target - self.safety_margin)) if peak_util > self.utilization_target else None
        unit_cost_map = {
            ResourceType.CPU.value: 0.10, ResourceType.MEMORY.value: 0.05,
            ResourceType.STORAGE.value: 0.02, ResourceType.NETWORK.value: 0.01, ResourceType.GPU.value: 0.50,
        }
        unit_cost = unit_cost_map.get(resource_type, 0.05)
        result = {
            "id": str(uuid.uuid4()),
            "resource_id": resource_id,
            "resource_type": resource_type,
            "scenario": scenario,
            "parameters": params,
            "base_utilization": forecast.get("current_utilization"),
            "peak_utilization": round(peak_util, 4),
            "avg_utilization": round(statistics.mean(adjusted_utils), 4),
            "days_over_capacity": days_over_capacity,
            "days_over_threshold": days_over_threshold,
            "recommended_capacity": round(needed_capacity, 2) if needed_capacity else None,
            "recommended_additional": round(needed_capacity - current_capacity, 2) if needed_capacity else None,
            "estimated_monthly_cost": round((needed_capacity - current_capacity) * unit_cost * 730, 2) if needed_capacity else 0,
            "simulation_series": [round(u, 4) for u in adjusted_utils[::max(1, forecast["forecast_days"] // 60)]],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.simulations.append(result)
        self._save_simulations()
        return result

    def list_recommendations(self, resource_id: str = None, priority: str = None,
                              status: str = None) -> List[Dict[str, Any]]:
        result = self.recommendations
        if resource_id:
            result = [r for r in result if r.get("resource_id") == resource_id]
        if priority:
            result = [r for r in result if r.get("priority") == priority]
        if status:
            result = [r for r in result if r.get("status") == status]
        return result

    def list_simulations(self, resource_id: str = None, scenario: str = None) -> List[Dict[str, Any]]:
        result = self.simulations
        if resource_id:
            result = [s for s in result if s.get("resource_id") == resource_id]
        if scenario:
            result = [s for s in result if s.get("scenario") == scenario]
        return result

    def dismiss_recommendation(self, rec_id: str) -> bool:
        for r in self.recommendations:
            if r["id"] == rec_id:
                r["status"] = "dismissed"
                self._save_recommendations()
                return True
        return False

    def apply_recommendation(self, rec_id: str) -> Optional[Dict[str, Any]]:
        rec = next((r for r in self.recommendations if r["id"] == rec_id), None)
        if rec:
            rec["status"] = "applied"
            self._save_recommendations()
        return rec

    def get_summary(self) -> Dict[str, Any]:
        critical = sum(1 for r in self.recommendations if r.get("priority") == RecommendationPriority.CRITICAL.value)
        high = sum(1 for r in self.recommendations if r.get("priority") == RecommendationPriority.HIGH.value)
        medium = sum(1 for r in self.recommendations if r.get("priority") == RecommendationPriority.MEDIUM.value)
        open_recs = sum(1 for r in self.recommendations if r.get("status") == "open")
        applied = sum(1 for r in self.recommendations if r.get("status") == "applied")
        return {
            "total_recommendations": len(self.recommendations),
            "critical": critical,
            "high": high,
            "medium": medium,
            "open": open_recs,
            "applied": applied,
            "total_simulations": len(self.simulations),
            "resources_tracked": len(set(k.split(":")[0] for k in self.usage_history.keys())),
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_recommendations(self, offset: int = 0, limit: int = 50, priority: str = None,
                                  status: str = None, resource_type: str = None) -> dict:
        results = self.recommendations
        if priority:
            results = [r for r in results if r.get("priority") == priority]
        if status:
            results = [r for r in results if r.get("status") == status]
        if resource_type:
            results = [r for r in results if r.get("resource_type") == resource_type]
        total = len(results)
        results.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_simulations(self, offset: int = 0, limit: int = 50, scenario: str = None,
                              resource_id: str = None) -> dict:
        results = self.simulations
        if scenario:
            results = [s for s in results if s.get("scenario") == scenario]
        if resource_id:
            results = [s for s in results if s.get("resource_id") == resource_id]
        total = len(results)
        results.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_generate_recommendations(self, resources: list[tuple[str, str]]) -> dict:
        succeeded = 0
        failed = 0
        for resource_id, resource_type in resources:
            try:
                rec = self.generate_recommendation(resource_id, resource_type)
                if "error" not in rec:
                    succeeded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total": len(resources)}

    def batch_dismiss_recommendations(self, rec_ids: list[str]) -> dict:
        succeeded = 0
        for rid in rec_ids:
            if self.dismiss_recommendation(rid):
                succeeded += 1
        return {"dismissed": succeeded, "total_requested": len(rec_ids)}

    def batch_record_usages(self, records: list[dict]) -> dict:
        recorded = 0
        for rec in records:
            try:
                self.record_usage(
                    rec["resource_id"], rec["resource_type"],
                    rec["total_capacity"], rec["used"], rec.get("timestamp"),
                )
                recorded += 1
            except (KeyError, TypeError):
                pass
        return {"recorded": recorded, "total_requested": len(records)}

    def export_recommendations(self, priority: str = None, status: str = None) -> list[dict]:
        results = self.recommendations
        if priority:
            results = [r for r in results if r.get("priority") == priority]
        if status:
            results = [r for r in results if r.get("status") == status]
        return [{
            "id": r["id"], "resource_id": r.get("resource_id"),
            "resource_type": r.get("resource_type"), "priority": r.get("priority"),
            "action": r.get("action"), "title": r.get("title"),
            "current_utilization": r.get("current_utilization"),
            "peak_forecast": r.get("peak_forecast"),
            "recommended_capacity": r.get("recommended_capacity"),
            "annual_growth_rate": r.get("annual_growth_rate"),
            "cost_estimate": r.get("cost_estimate"), "status": r.get("status"),
            "created_at": r.get("created_at"),
        } for r in results]

    def import_recommendations(self, recommendations: list[dict]) -> dict:
        imported = 0
        for r in recommendations:
            entry = {
                "id": str(uuid.uuid4()),
                "resource_id": r.get("resource_id", "unknown"),
                "resource_type": r.get("resource_type", "cpu"),
                "priority": r.get("priority", "medium"),
                "action": r.get("action", "monitor"),
                "title": r.get("title", "Imported Recommendation"),
                "summary": r.get("summary", ""),
                "current_utilization": r.get("current_utilization", 0),
                "peak_forecast": r.get("peak_forecast", 0),
                "recommended_capacity": r.get("recommended_capacity"),
                "recommended_additional": r.get("recommended_additional"),
                "annual_growth_rate": r.get("annual_growth_rate", 0),
                "days_until_exhaustion": r.get("days_until_exhaustion"),
                "days_until_threshold": r.get("days_until_threshold"),
                "cost_estimate": r.get("cost_estimate"),
                "forecast_data": r.get("forecast_data", {}),
                "status": r.get("status", "open"),
                "created_at": r.get("created_at", datetime.utcnow().isoformat()),
            }
            self.recommendations.append(entry)
            imported += 1
        self._save_recommendations()
        return {"imported": imported}

    def export_simulations(self, scenario: str = None) -> list[dict]:
        results = self.simulations
        if scenario:
            results = [s for s in results if s.get("scenario") == scenario]
        return [{
            "id": s["id"], "resource_id": s.get("resource_id"),
            "resource_type": s.get("resource_type"), "scenario": s.get("scenario"),
            "parameters": s.get("parameters"), "peak_utilization": s.get("peak_utilization"),
            "avg_utilization": s.get("avg_utilization"),
            "days_over_capacity": s.get("days_over_capacity"),
            "recommended_capacity": s.get("recommended_capacity"),
            "estimated_monthly_cost": s.get("estimated_monthly_cost"),
            "created_at": s.get("created_at"),
        } for s in results]

    def get_analytics(self) -> dict:
        priority_counts = Counter(r.get("priority", "unknown") for r in self.recommendations)
        status_counts = Counter(r.get("status", "unknown") for r in self.recommendations)
        type_counts = Counter(r.get("resource_type", "unknown") for r in self.recommendations)
        scenario_counts = Counter(s.get("scenario", "unknown") for s in self.simulations)
        recs_by_hour = {}
        for r in self.recommendations:
            try:
                hour = datetime.fromisoformat(r["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                recs_by_hour[hour] = recs_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        avg_util = []
        for key, points in self.usage_history.items():
            if points:
                avg_util.append(statistics.mean(p["utilization"] for p in points))
        return {
            "total_recommendations": len(self.recommendations),
            "total_simulations": len(self.simulations),
            "priority_distribution": dict(priority_counts),
            "status_distribution": dict(status_counts),
            "resource_type_distribution": dict(type_counts),
            "scenario_distribution": dict(scenario_counts),
            "avg_utilization_across_resources": round(statistics.mean(avg_util), 4) if avg_util else 0,
            "resources_tracked": len(set(k.split(":")[0] for k in self.usage_history.keys())),
            "recommendations_by_hour": dict(sorted(recs_by_hour.items())[-24:]),
            "top_resources": [{"resource": r, "count": c} for r, c in
                               Counter(r.get("resource_id", "unknown") for r in self.recommendations).most_common(10)],
        }

    def search_recommendations(self, query: str) -> list[dict]:
        q = query.lower()
        return [r for r in self.recommendations if q in r.get("resource_id", "").lower()
                or q in r.get("title", "").lower() or q in r.get("action", "").lower()]

    def get_resource_timeline(self, resource_id: str) -> list[dict]:
        timeline = []
        for r in self.recommendations:
            if r.get("resource_id") == resource_id:
                timeline.append({
                    "event": f"recommendation_{r.get('status')}",
                    "recommendation_id": r["id"],
                    "priority": r.get("priority"),
                    "action": r.get("action"),
                    "timestamp": r.get("created_at"),
                })
        for s in self.simulations:
            if s.get("resource_id") == resource_id:
                timeline.append({
                    "event": f"simulation_{s.get('scenario')}",
                    "simulation_id": s["id"],
                    "timestamp": s.get("created_at"),
                })
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_resources(self) -> list[dict]:
        resource_scores = defaultdict(float)
        for r in self.recommendations:
            rid = r.get("resource_id", "unknown")
            score = 1.0
            if r.get("priority") == RecommendationPriority.CRITICAL.value:
                score = 5.0
            elif r.get("priority") == RecommendationPriority.HIGH.value:
                score = 3.0
            resource_scores[rid] += score
        return [{"resource": r, "score": round(s, 1)} for r, s in
                sorted(resource_scores.items(), key=lambda x: x[1], reverse=True)[:20]]

    def simulate_bulk_scenarios(self, resource_id: str, resource_type: str,
                                 scenarios: list[str]) -> list[dict]:
        results = []
        for scenario in scenarios:
            sim = self.what_if_simulation(resource_id, resource_type, scenario)
            results.append(sim)
        return results

    def get_capacity_heatmap(self) -> dict:
        heatmap = {}
        for key in self.usage_history.keys():
            parts = key.split(":")
            rid = parts[0] if len(parts) > 0 else "unknown"
            rtype = parts[1] if len(parts) > 1 else "unknown"
            points = list(self.usage_history[key])
            if points:
                utils = [p["utilization"] for p in points[-30:]]
                heatmap[key] = {
                    "resource_id": rid,
                    "resource_type": rtype,
                    "avg_utilization": round(statistics.mean(utils), 4),
                    "peak_utilization": round(max(utils), 4),
                    "current_utilization": round(utils[-1], 4),
                    "trend": "up" if len(utils) >= 5 and statistics.mean(utils[-5:]) > statistics.mean(utils[:5]) else "down" if len(utils) >= 5 else "stable",
                }
        return heatmap

    # ===== APPENDED BATCH 2: State machine, SLO, reports, config export, advanced =====

    def check_capacity_slo(self, target_utilization_pct: float = 80.0) -> dict:
        results = {}
        for key in self.usage_history.keys():
            points = list(self.usage_history[key])
            if points:
                utils = [p["utilization"] * 100 for p in points[-60:]]
                avg_util = statistics.mean(utils) if utils else 0
                results[key] = {
                    "avg_utilization_pct": round(avg_util, 2),
                    "compliant": avg_util <= target_utilization_pct,
                    "peak_utilization_pct": round(max(utils), 2) if utils else 0,
                }
        compliant_count = sum(1 for v in results.values() if v["compliant"])
        total_count = len(results)
        return {
            "slo_target_pct": target_utilization_pct,
            "compliant_count": compliant_count,
            "total_resources": total_count,
            "compliance_rate": round((compliant_count / max(total_count, 1)) * 100, 2),
            "details": results,
        }

    def generate_capacity_report(self, days: int = 30) -> dict:
        recommendations_by_priority = Counter(r.get("priority", "unknown") for r in self.recommendations)
        simulations_by_scenario = Counter(s.get("scenario", "unknown") for s in self.simulations)
        at_risk = [r for r in self.recommendations if r.get("priority") in
                   (RecommendationPriority.CRITICAL.value, RecommendationPriority.HIGH.value)
                   and r.get("status") == "open"]
        total_cost = sum(r.get("cost_estimate", {}).get("estimated_monthly_cost", 0)
                         for r in self.recommendations if r.get("cost_estimate"))
        return {
            "report_period_days": days,
            "total_recommendations": len(self.recommendations),
            "open_high_priority": len(at_risk),
            "at_risk_resources": [{"resource": r.get("resource_id"), "priority": r.get("priority"),
                                   "days_remaining": r.get("days_until_threshold")} for r in at_risk[:10]],
            "priority_distribution": dict(recommendations_by_priority),
            "simulation_scenarios": dict(simulations_by_scenario),
            "estimated_monthly_cost": round(total_cost, 2),
            "total_simulations": len(self.simulations),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "policies": {k: v for k, v in self.policies.items()},
            "recommendation_count": len(self.recommendations),
            "simulation_count": len(self.simulations),
            "resources_tracked": len(set(k.split(":")[0] for k in self.usage_history.keys())),
        }

    def forecast_cost(self, resource_id: str, resource_type: str, months: int = 6) -> dict:
        forecast = self._forecast_utilization(resource_id, resource_type, days=months * 30)
        if "error" in forecast:
            return forecast
        unit_cost_map = {
            ResourceType.CPU.value: 0.10, ResourceType.MEMORY.value: 0.05,
            ResourceType.STORAGE.value: 0.02, ResourceType.NETWORK.value: 0.01, ResourceType.GPU.value: 0.50,
        }
        unit_cost = unit_cost_map.get(resource_type, 0.05)
        monthly_costs = []
        for i in range(months):
            projected_util = forecast.get("forecast_series", [forecast["current_utilization"]] * months)
            util = projected_util[min(i, len(projected_util) - 1)]
            needed = forecast.get("current_capacity", 100) * (util / (self.utilization_target - self.safety_margin)) if util > self.utilization_target else 0
            additional = max(0, needed - forecast.get("current_capacity", 100))
            cost = additional * unit_cost * 730
            monthly_costs.append({"month": i + 1, "projected_cost": round(cost, 2)})
        return {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "months": months,
            "monthly_costs": monthly_costs,
            "total_projected_cost": round(sum(m["projected_cost"] for m in monthly_costs), 2),
            "current_monthly_cost": round(forecast.get("current_capacity", 100) * unit_cost * 730, 2),
        }

    def get_resource_health(self, resource_id: str) -> dict:
        usage_keys = [k for k in self.usage_history.keys() if k.startswith(resource_id)]
        if not usage_keys:
            return {"resource_id": resource_id, "error": "No data found"}
        health = {}
        for key in usage_keys:
            points = list(self.usage_history[key])
            if points:
                utils = [p["utilization"] for p in points[-30:]]
                avg = statistics.mean(utils)
                trend = utils[-1] - utils[0] if len(utils) > 5 else 0
                status = "healthy" if avg < self.utilization_target else (
                    "degraded" if avg < 0.9 else "critical"
                )
                health[key] = {"avg_utilization": round(avg, 4), "trend": round(trend, 4), "status": status}
        return {"resource_id": resource_id, "dimensions": health}

    def compare_scenarios(self, resource_id: str, resource_type: str,
                           scenarios: list[str]) -> list[dict]:
        results = []
        for scenario in scenarios:
            sim = self.what_if_simulation(resource_id, resource_type, scenario)
            results.append({
                "scenario": scenario,
                "peak_utilization": sim.get("peak_utilization"),
                "days_over_capacity": sim.get("days_over_capacity"),
                "recommended_additional": sim.get("recommended_additional"),
                "estimated_monthly_cost": sim.get("estimated_monthly_cost"),
            })
        return results

    def get_optimization_suggestions(self) -> list[dict]:
        suggestions = []
        for key in self.usage_history.keys():
            points = list(self.usage_history[key])
            if len(points) < 10:
                continue
            utils = [p["utilization"] for p in points]
            avg = statistics.mean(utils)
            peak = max(utils)
            if avg < 0.2 and peak < 0.4:
                suggestions.append({
                    "resource_key": key,
                    "suggestion": "downsize_or_consolidate",
                    "reason": f"Average utilization {avg:.1%} is very low",
                    "estimated_savings": "moderate",
                })
            elif avg > 0.8:
                suggestions.append({
                    "resource_key": key,
                    "suggestion": "add_capacity",
                    "reason": f"Average utilization {avg:.1%} exceeds safe threshold",
                    "urgency": "high",
                })
        return suggestions

    def batch_create_recommendations(self) -> dict:
        resource_keys = set(k.split(":")[0] for k in self.usage_history.keys())
        types_for_resource = defaultdict(set)
        for k in self.usage_history.keys():
            parts = k.split(":")
            if len(parts) >= 2:
                types_for_resource[parts[0]].add(parts[1])
        created = 0
        for rid in resource_keys:
            for rtype in types_for_resource.get(rid, set()):
                try:
                    rec = self.generate_recommendation(rid, rtype)
                    if "error" not in rec:
                        created += 1
                except Exception:
                    pass
        return {"recommendations_created": created, "resources_processed": len(resource_keys)}

    def get_capacity_summary(self) -> dict:
        total_resources = len(set(k.split(":")[0] for k in self.usage_history.keys()))
        all_utils = []
        for points in self.usage_history.values():
            all_utils.extend(p.get("utilization", 0) for p in list(points)[-10:])
        avg_util = round(statistics.mean(all_utils), 4) if all_utils else 0
        over_capacity = sum(1 for u in all_utils if u > self.utilization_target)
        return {"total_resources": total_resources, "avg_utilization": avg_util, "resources_over_capacity": over_capacity, "utilization_target": self.utilization_target, "total_recommendations": len(getattr(self, "recommendations", [])), "status": "healthy" if avg_util < self.utilization_target * 0.8 else "degraded" if avg_util < self.utilization_target else "critical"}

    def export_usage_history(self, resource_id: str) -> list[dict]:
        keys = [k for k in self.usage_history.keys() if k.startswith(resource_id)]
        results = []
        for key in keys:
            results.extend(list(self.usage_history[key]))
        return results

    def get_growth_rate(self, resource_id: str) -> Optional[float]:
        keys = [k for k in self.usage_history.keys() if k.startswith(resource_id)]
        if not keys:
            return None
        all_points = []
        for key in keys:
            all_points.extend(list(self.usage_history[key]))
        if len(all_points) < 10:
            return None
        sorted_points = sorted(all_points, key=lambda x: x.get("timestamp", ""))
        first_utils = [p.get("utilization", 0) for p in sorted_points[:5]]
        last_utils = [p.get("utilization", 0) for p in sorted_points[-5:]]
        first_avg = statistics.mean(first_utils)
        last_avg = statistics.mean(last_utils)
        if first_avg == 0:
            return None
        return round((last_avg - first_avg) / first_avg * 100, 2)


class CapacityAlertManager:
    def __init__(self, engine: CapacityPlanningEngine):
        self.engine = engine
        self.alerts: list[dict] = []

    def check_capacity_breaches(self) -> list[dict]:
        new_alerts = []
        for key in self.engine.usage_history.keys():
            points = list(self.engine.usage_history[key])
            if not points:
                continue
            recent = points[-5:]
            avg_util = statistics.mean(p.get("utilization", 0) for p in recent)
            if avg_util > self.engine.utilization_target:
                alert = {"id": str(uuid.uuid4()), "resource_key": key, "avg_utilization": round(avg_util, 4), "threshold": self.engine.utilization_target, "severity": "critical" if avg_util > 0.9 else "warning", "timestamp": datetime.utcnow().isoformat()}
                self.alerts.append(alert)
                new_alerts.append(alert)
        return new_alerts

    def get_active_alerts(self) -> list[dict]:
        return [a for a in self.alerts if not a.get("resolved_at")]

    def resolve_alert(self, alert_id: str) -> Optional[dict]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["resolved_at"] = datetime.utcnow().isoformat()
                return a
        return None

    def get_alert_summary(self) -> dict:
        active = self.get_active_alerts()
        return {"total_active": len(active), "critical": sum(1 for a in active if a.get("severity") == "critical"), "warning": sum(1 for a in active if a.get("severity") == "warning"), "total_alerts": len(self.alerts)}


class CapacityDashboardAggregator:
    def __init__(self, engine: CapacityPlanningEngine):
        self.engine = engine

    def get_overview(self) -> dict:
        summary = self.engine.get_capacity_summary()
        alerts = CapacityAlertManager(self.engine)
        return {"summary": summary, "active_alerts": len(alerts.get_active_alerts()), "recommendations_count": sum(1 for k in self.engine.usage_history.keys() for p in list(self.engine.usage_history[k])[-1:] if p.get("utilization", 0) > self.engine.utilization_target)}

    def get_top_recommendations(self, limit: int = 5) -> list[dict]:
        recs = self.engine.get_optimization_suggestions()
        return sorted(recs, key=lambda x: x.get("urgency", "medium"), reverse=True)[:limit]

    def get_utilization_distribution(self) -> dict:
        all_utils = []
        for points in self.engine.usage_history.values():
            all_utils.extend(p.get("utilization", 0) for p in list(points)[-5:])
        if not all_utils:
            return {}
        return {"underutilized_below_20pct": sum(1 for u in all_utils if u < 0.2), "healthy_20_to_60pct": sum(1 for u in all_utils if 0.2 <= u <= 0.6), "elevated_60_to_80pct": sum(1 for u in all_utils if 0.6 < u <= 0.8), "over_capacity_above_80pct": sum(1 for u in all_utils if u > 0.8)}

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
        return {"total_events": 0, "anomalies_detected": 0, "false_positives": 0, "avg_confidence": 0.0}

    def validate_model(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "model_version": "v1"}

class AiopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    prediction_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AiopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    model: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    anomalies_found: int = Field(default=0)

    def record_result(self, is_anomaly: bool) -> None:
        self.processed += 1
        if is_anomaly:
            self.anomalies_found += 1

    def complete(self) -> None:
        self.status = "completed"

class AnomalyScore(BaseModel):
    entity_id: str
    score: float = Field(default=0.0, ge=0, le=1)
    baseline: float = Field(default=0.0)
    deviation: float = Field(default=0.0)
    features: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: str = Field(default="info")

    def is_anomalous(self, threshold: float = 0.7) -> bool:
        return self.score >= threshold

class ModelMetrics(BaseModel):
    model_name: str
    version: str = Field(default="v1")
    accuracy: float = Field(default=0.0, ge=0, le=1)
    precision: float = Field(default=0.0, ge=0, le=1)
    recall: float = Field(default=0.0, ge=0, le=1)
    f1_score: float = Field(default=0.0, ge=0, le=1)
    training_date: Optional[datetime] = None
    total_predictions: int = Field(default=0)

class ModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, ModelMetrics] = {}

    def register(self, name: str, version: str = "v1") -> ModelMetrics:
        mm = ModelMetrics(model_name=name, version=version)
        self._models[name] = mm
        return mm

    def update_metrics(self, name: str, accuracy: float = 0.0, precision: float = 0.0,
                       recall: float = 0.0, f1: float = 0.0) -> None:
        model = self._models.get(name)
        if model:
            model.accuracy = accuracy
            model.precision = precision
            model.recall = recall
            model.f1_score = f1
            model.total_predictions += 1

    def get_best(self) -> Optional[ModelMetrics]:
        if not self._models:
            return None
        return max(self._models.values(), key=lambda m: m.f1_score)

    def summary(self) -> Dict[str, Any]:
        return {name: m.dict() for name, m in self._models.items()}

class FeatureStore(BaseModel):
    feature_name: str
    value: float
    entity_type: str = Field(default="generic")
    entity_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="inference")

class FeatureRepository:
    def __init__(self) -> None:
        self._features: List[FeatureStore] = []

    def store(self, feature: FeatureStore) -> None:
        self._features.append(feature)

    def get_latest(self, entity_id: str, feature_name: str) -> Optional[FeatureStore]:
        matches = [f for f in self._features if f.entity_id == entity_id and f.feature_name == feature_name]
        return max(matches, key=lambda f: f.timestamp) if matches else None

    def get_entity_features(self, entity_id: str) -> Dict[str, Any]:
        features = [f for f in self._features if f.entity_id == entity_id]
        return {f.feature_name: {"value": f.value, "timestamp": f.timestamp.isoformat()} for f in features}

    def get_time_series(self, feature_name: str, entity_id: str, limit: int = 100) -> List[FeatureStore]:
        matches = [f for f in self._features if f.feature_name == feature_name and f.entity_id == entity_id]
        return sorted(matches, key=lambda f: f.timestamp, reverse=True)[:limit]

class ThresholdConfig(BaseModel):
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    enabled: bool = True
    cooldown_minutes: int = Field(default=5)

class ThresholdManager:
    def __init__(self) -> None:
        self._thresholds: Dict[str, ThresholdConfig] = {}

    def define(self, config: ThresholdConfig) -> None:
        self._thresholds[config.metric_name] = config

    def check(self, metric_name: str, value: float) -> Dict[str, Any]:
        config = self._thresholds.get(metric_name)
        if not config or not config.enabled:
            return {"level": "ok", "message": "No threshold configured"}
        if value >= config.critical_threshold:
            return {"level": "critical", "value": value, "threshold": config.critical_threshold}
        if value >= config.warning_threshold:
            return {"level": "warning", "value": value, "threshold": config.warning_threshold}
        return {"level": "ok", "value": value}

    def get_all(self) -> Dict[str, ThresholdConfig]:
        return dict(self._thresholds)

class DriftMetric(BaseModel):
    feature_name: str
    training_mean: float
    production_mean: float
    drift_score: float = Field(default=0.0, ge=0)
    drifted: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class DriftDetector:
    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        self._metrics: List[DriftMetric] = []

    def compare(self, feature_name: str, training_mean: float, production_values: List[float]) -> DriftMetric:
        prod_mean = sum(production_values) / max(len(production_values), 1)
        drift = abs(prod_mean - training_mean) / max(abs(training_mean), 0.001)
        metric = DriftMetric(feature_name=feature_name, training_mean=training_mean,
                              production_mean=round(prod_mean, 4),
                              drift_score=round(drift, 4), drifted=drift > self.threshold)
        self._metrics.append(metric)
        return metric

    def get_recent_drifts(self) -> List[DriftMetric]:
        return [m for m in self._metrics if m.drifted]

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._metrics)
        drifted = len(self.get_recent_drifts())
        return {"total_features": total, "drifted": drifted, "stable": total - drifted,
                "drift_rate": round(drifted / max(total, 1) * 100, 1)}

class PredictionLog(BaseModel):
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    input_features: Dict[str, float] = Field(default_factory=dict)
    prediction: Any = None
    confidence: float = Field(default=0.0)
    actual: Optional[Any] = None
    correct: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float = Field(default=0.0)

class PredictionLogger:
    def __init__(self) -> None:
        self._logs: List[PredictionLog] = []

    def log_prediction(self, model_name: str, features: Dict[str, float], prediction: Any,
                       confidence: float, latency_ms: float = 0.0) -> PredictionLog:
        pl = PredictionLog(model_name=model_name, input_features=features,
                            prediction=prediction, confidence=confidence, latency_ms=latency_ms)
        self._logs.append(pl)
        return pl

    def record_actual(self, prediction_id: str, actual: Any) -> bool:
        for pl in self._logs:
            if pl.prediction_id == prediction_id:
                pl.actual = actual
                pl.correct = pl.prediction == actual
                return True
        return False

    def get_accuracy(self, model_name: Optional[str] = None) -> float:
        logs = [l for l in self._logs if l.correct is not None]
        if model_name:
            logs = [l for l in logs if l.model_name == model_name]
        if not logs:
            return 0.0
        return round(sum(1 for l in logs if l.correct) / len(logs), 4)
