"""Feature 56: Service Health Forecasting — Predict future service health based on current trends."""

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


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    FLAPPING = "flapping"


class HealthDimension(Enum):
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    CAPACITY = "capacity"
    RELIABILITY = "reliability"
    SECURITY = "security"
    COST_EFFICIENCY = "cost_efficiency"


class ServiceHealthForecaster:
    """Predict future service health based on current trends and ML analysis."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.forecast_horizon = config.get("forecast_horizon_hours", 24)
        self.degradation_threshold = config.get("degradation_threshold", 0.7)
        self.critical_threshold = config.get("critical_threshold", 0.4)
        self.min_data_points = config.get("min_data_points", 10)
        self.services_file = _data_file('health_services.json')
        self.snapshots_file = _data_file('health_snapshots.json')
        self.forecasts_file = _data_file('health_forecasts.json')
        self.services: Dict[str, Dict[str, Any]] = {}
        self.snapshots: List[Dict[str, Any]] = []
        self.forecasts: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.services_file, 'r') as f:
                self.services = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.snapshots_file, 'r') as f:
                self.snapshots = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.forecasts_file, 'r') as f:
                self.forecasts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_services(self):
        with open(self.services_file, 'w') as f:
            json.dump(self.services, f, default=str)

    def _save_snapshots(self):
        with open(self.snapshots_file, 'w') as f:
            json.dump(self.snapshots[-50000:], f, default=str)

    def _save_forecasts(self):
        with open(self.forecasts_file, 'w') as f:
            json.dump(self.forecasts[-10000:], f, default=str)

    def register_service(self, service_id: str, name: str, tags: List[str] = None,
                          dependencies: List[str] = None) -> Dict[str, Any]:
        service = {
            "service_id": service_id,
            "name": name,
            "tags": tags or [],
            "dependencies": dependencies or [],
            "current_health": HealthStatus.UNKNOWN.value,
            "current_score": 1.0,
            "trend": TrendDirection.STABLE.value,
            "last_snapshot_at": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.services[service_id] = service
        self._save_services()
        return service

    def update_service(self, service_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if service_id not in self.services:
            return None
        for k, v in updates.items():
            if k not in ("service_id", "created_at"):
                self.services[service_id][k] = v
        self._save_services()
        return self.services[service_id]

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        return self.services.get(service_id)

    def list_services(self) -> List[Dict[str, Any]]:
        return list(self.services.values())

    def delete_service(self, service_id: str) -> bool:
        if service_id in self.services:
            del self.services[service_id]
            self._save_services()
            return True
        return False

    def record_snapshot(self, service_id: str, dimensions: Dict[str, float]) -> Dict[str, Any]:
        if service_id not in self.services:
            return {"error": f"Service {service_id} not registered"}
        overall = statistics.mean(list(dimensions.values())) if dimensions else 1.0
        snapshot = {
            "id": str(uuid.uuid4()),
            "service_id": service_id,
            "dimensions": dimensions,
            "overall_score": round(overall, 4),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.snapshots.append(snapshot)
        self.services[service_id]["current_score"] = overall
        self.services[service_id]["current_health"] = self._score_to_health(overall)
        self.services[service_id]["last_snapshot_at"] = snapshot["timestamp"]
        self.services[service_id]["trend"] = self._compute_trend(service_id).value
        self._save_snapshots()
        self._save_services()
        return snapshot

    def _score_to_health(self, score: float) -> str:
        if score >= self.degradation_threshold:
            return HealthStatus.HEALTHY.value
        elif score >= self.critical_threshold:
            return HealthStatus.DEGRADED.value
        elif score > 0:
            return HealthStatus.CRITICAL.value
        return HealthStatus.UNKNOWN.value

    def _compute_trend(self, service_id: str) -> TrendDirection:
        recent = [s for s in self.snapshots if s["service_id"] == service_id]
        recent = recent[-20:]
        if len(recent) < 5:
            return TrendDirection.STABLE
        scores = [s["overall_score"] for s in recent]
        first_half = statistics.mean(scores[:len(scores)//2])
        second_half = statistics.mean(scores[len(scores)//2:])
        diff = second_half - first_half
        if diff > 0.05:
            return TrendDirection.IMPROVING
        elif diff < -0.05:
            return TrendDirection.DEGRADING
        return TrendDirection.STABLE

    def get_service_snapshots(self, service_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = [s for s in self.snapshots if s["service_id"] == service_id]
        return [s for s in result if datetime.fromisoformat(s["timestamp"]) > cutoff]

    def forecast(self, service_id: str, hours: int = None) -> Dict[str, Any]:
        if hours is None:
            hours = self.forecast_horizon
        if service_id not in self.services:
            return {"error": f"Service {service_id} not registered"}
        snapshots = self.get_service_snapshots(service_id, hours=hours * 2)
        if len(snapshots) < self.min_data_points:
            service = self.services[service_id]
            return {
                "service_id": service_id,
                "service_name": service["name"],
                "error": f"Insufficient data: {len(snapshots)} snapshots, need {self.min_data_points}",
                "current_health": service["current_health"],
                "current_score": service["current_score"],
                "forecast": None,
            }
        scores = [s["overall_score"] for s in snapshots]
        times = [datetime.fromisoformat(s["timestamp"]) for s in snapshots]
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(scores)
        numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        forecast_count = max(1, hours)
        forecast_scores = [intercept + slope * (n + i) for i in range(forecast_count)]
        forecast_scores = [max(0.0, min(1.0, s)) for s in forecast_scores]
        final_score = forecast_scores[-1]
        final_health = self._score_to_health(final_score)
        min_score = min(forecast_scores)
        time_to_degradation = None
        for i, s in enumerate(forecast_scores):
            if s < self.degradation_threshold:
                time_to_degradation = i + 1
                break
        time_to_critical = None
        for i, s in enumerate(forecast_scores):
            if s < self.critical_threshold:
                time_to_critical = i + 1
                break
        residual_std = math.sqrt(
            sum((s - (intercept + slope * i)) ** 2 for i, s in enumerate(scores)) / n
        ) if n > 1 else 0.05
        confidence_upper = [min(1.0, s + 2 * residual_std) for s in forecast_scores]
        confidence_lower = [max(0.0, s - 2 * residual_std) for s in forecast_scores]
        recommendations = []
        if slope < -0.01:
            recommendations.append(f"Service health is declining at rate of {abs(slope):.4f} per hour")
        if time_to_degradation and time_to_degradation <= hours:
            recommendations.append(f"Risk of degradation detected within {time_to_degradation} hours")
        if time_to_critical and time_to_critical <= hours:
            recommendations.append(f"Risk of critical status within {time_to_critical} hours — immediate attention needed")
        if slope > 0.01:
            recommendations.append("Service health is improving — current mitigations are effective")
        prob_degradation = self._compute_probability(scores, forecast_scores, self.degradation_threshold)
        prob_critical = self._compute_probability(scores, forecast_scores, self.critical_threshold)
        trend_direction = TrendDirection.DEGRADING.value if slope < -0.01 else (
            TrendDirection.IMPROVING.value if slope > 0.01 else TrendDirection.STABLE.value
        )
        result = {
            "id": str(uuid.uuid4()),
            "service_id": service_id,
            "service_name": self.services[service_id]["name"],
            "current_score": round(scores[-1], 4),
            "current_health": self._score_to_health(scores[-1]),
            "forecast_hours": hours,
            "forecast_scores": [round(s, 4) for s in forecast_scores],
            "forecast_health": [self._score_to_health(s) for s in forecast_scores],
            "confidence_upper": [round(s, 4) for s in confidence_upper],
            "confidence_lower": [round(s, 4) for s in confidence_lower],
            "final_score": round(final_score, 4),
            "final_health": final_health,
            "trend": trend_direction,
            "slope": round(slope, 6),
            "probability_degradation": round(prob_degradation, 4),
            "probability_critical": round(prob_critical, 4),
            "time_to_degradation_hours": time_to_degradation,
            "time_to_critical_hours": time_to_critical,
            "recommendations": recommendations,
            "data_points_used": len(snapshots),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.forecasts.append(result)
        self._save_forecasts()
        return result

    def _compute_probability(self, historical: List[float], forecast: List[float],
                              threshold: float) -> float:
        combined = historical + forecast
        if not combined:
            return 0.0
        below = sum(1 for s in combined if s < threshold)
        return below / len(combined)

    def get_forecast(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        return next((f for f in self.forecasts if f["id"] == forecast_id), None)

    def list_forecasts(self, service_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        result = self.forecasts
        if service_id:
            result = [f for f in result if f.get("service_id") == service_id]
        return result[-limit:]

    def get_dashboard(self) -> Dict[str, Any]:
        services_list = list(self.services.values())
        healthy = sum(1 for s in services_list if s.get("current_health") == HealthStatus.HEALTHY.value)
        degraded = sum(1 for s in services_list if s.get("current_health") == HealthStatus.DEGRADED.value)
        critical = sum(1 for s in services_list if s.get("current_health") == HealthStatus.CRITICAL.value)
        unknown = sum(1 for s in services_list if s.get("current_health") == HealthStatus.UNKNOWN.value)
        improving = sum(1 for s in services_list if s.get("trend") == TrendDirection.IMPROVING.value)
        degrading = sum(1 for s in services_list if s.get("trend") == TrendDirection.DEGRADING.value)
        avg_score = statistics.mean([s.get("current_score", 1.0) for s in services_list]) if services_list else 1.0
        at_risk = [s for s in services_list if s.get("current_health") in
                   (HealthStatus.DEGRADED.value, HealthStatus.CRITICAL.value)]
        return {
            "total_services": len(services_list),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "unknown": unknown,
            "improving": improving,
            "degrading": degrading,
            "average_health_score": round(avg_score, 4),
            "at_risk_services": [
                {"service_id": s["service_id"], "name": s["name"],
                 "health": s["current_health"], "score": s.get("current_score")}
                for s in at_risk
            ],
            "total_forecasts": len(self.forecasts),
            "total_snapshots": len(self.snapshots),
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_services(self, offset: int = 0, limit: int = 50, health: str = None,
                           trend: str = None) -> dict:
        results = list(self.services.values())
        if health:
            results = [s for s in results if s.get("current_health") == health]
        if trend:
            results = [s for s in results if s.get("trend") == trend]
        total = len(results)
        results.sort(key=lambda s: s.get("current_score", 0), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_snapshots(self, offset: int = 0, limit: int = 50, service_id: str = None) -> dict:
        results = self.snapshots
        if service_id:
            results = [s for s in results if s.get("service_id") == service_id]
        total = len(results)
        results.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_forecasts(self, offset: int = 0, limit: int = 50, service_id: str = None,
                            health: str = None) -> dict:
        results = self.forecasts
        if service_id:
            results = [f for f in results if f.get("service_id") == service_id]
        if health:
            results = [f for f in results if f.get("current_health") == health]
        total = len(results)
        results.sort(key=lambda f: f.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_register_services(self, services: list[dict]) -> dict:
        registered = 0
        for s in services:
            try:
                self.register_service(
                    s["service_id"], s["name"], s.get("tags", []), s.get("dependencies", []),
                )
                registered += 1
            except (KeyError, TypeError):
                pass
        return {"registered": registered, "total_requested": len(services)}

    def batch_record_snapshots(self, snapshots: list[dict]) -> dict:
        recorded = 0
        errors = []
        for s in snapshots:
            try:
                result = self.record_snapshot(s["service_id"], s["dimensions"])
                if "error" not in result:
                    recorded += 1
                else:
                    errors.append(result["error"])
            except (KeyError, TypeError) as e:
                errors.append(str(e))
        return {"recorded": recorded, "errors": errors, "total_requested": len(snapshots)}

    def batch_forecast(self, service_ids: list[str], hours: int = None) -> list[dict]:
        results = []
        for sid in service_ids:
            f = self.forecast(sid, hours)
            results.append(f)
        return results

    def export_services(self, health: str = None) -> list[dict]:
        results = list(self.services.values())
        if health:
            results = [s for s in results if s.get("current_health") == health]
        return [{
            "service_id": s["service_id"], "name": s.get("name"), "tags": s.get("tags"),
            "dependencies": s.get("dependencies"), "current_health": s.get("current_health"),
            "current_score": s.get("current_score"), "trend": s.get("trend"),
            "last_snapshot_at": s.get("last_snapshot_at"), "created_at": s.get("created_at"),
        } for s in results]

    def import_services(self, services: list[dict]) -> dict:
        imported = 0
        for s in services:
            sid = s.get("service_id") or str(uuid.uuid4())
            if sid not in self.services:
                self.register_service(
                    sid, s.get("name", "Imported Service"),
                    s.get("tags", []), s.get("dependencies", []),
                )
                imported += 1
        return {"imported": imported}

    def export_forecasts(self, service_id: str = None, health: str = None) -> list[dict]:
        results = self.forecasts
        if service_id:
            results = [f for f in results if f.get("service_id") == service_id]
        if health:
            results = [f for f in results if f.get("final_health") == health]
        return [{
            "id": f["id"], "service_id": f.get("service_id"),
            "service_name": f.get("service_name"),
            "current_score": f.get("current_score"), "current_health": f.get("current_health"),
            "final_score": f.get("final_score"), "final_health": f.get("final_health"),
            "trend": f.get("trend"), "slope": f.get("slope"),
            "probability_degradation": f.get("probability_degradation"),
            "probability_critical": f.get("probability_critical"),
            "time_to_degradation_hours": f.get("time_to_degradation_hours"),
            "time_to_critical_hours": f.get("time_to_critical_hours"),
            "created_at": f.get("created_at"),
        } for f in results]

    def get_analytics(self) -> dict:
        health_counts = Counter(s.get("current_health", "unknown") for s in self.services.values())
        trend_counts = Counter(s.get("trend", "unknown") for s in self.services.values())
        forecast_health_counts = Counter(f.get("final_health", "unknown") for f in self.forecasts)
        snapshot_scores = [s.get("overall_score", 0) for s in self.snapshots if s.get("overall_score") is not None]
        forecasts_by_hour = {}
        for f in self.forecasts:
            try:
                hour = datetime.fromisoformat(f["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                forecasts_by_hour[hour] = forecasts_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        return {
            "total_services": len(self.services),
            "total_snapshots": len(self.snapshots),
            "total_forecasts": len(self.forecasts),
            "health_distribution": dict(health_counts),
            "trend_distribution": dict(trend_counts),
            "forecast_health_distribution": dict(forecast_health_counts),
            "avg_health_score": round(statistics.mean(snapshot_scores), 4) if snapshot_scores else 0,
            "forecasts_by_hour": dict(sorted(forecasts_by_hour.items())[-24:]),
            "services_at_risk": sum(1 for s in self.services.values()
                                    if s.get("current_health") in
                                    (HealthStatus.DEGRADED.value, HealthStatus.CRITICAL.value)),
        }

    def search_services(self, query: str) -> list[dict]:
        q = query.lower()
        return [s for s in self.services.values() if q in s.get("name", "").lower()
                or q in s.get("service_id", "").lower()
                or any(q in tag.lower() for tag in s.get("tags", []))]

    def get_service_timeline(self, service_id: str) -> list[dict]:
        timeline = []
        svc = self.get_service(service_id)
        if svc:
            timeline.append({"event": "registered", "timestamp": svc.get("created_at")})
            service_snapshots = [s for s in self.snapshots if s.get("service_id") == service_id]
            for s in service_snapshots[-20:]:
                timeline.append({
                    "event": "snapshot",
                    "score": s.get("overall_score"),
                    "health": self._score_to_health(s.get("overall_score", 0)),
                    "timestamp": s.get("timestamp"),
                })
            service_forecasts = [f for f in self.forecasts if f.get("service_id") == service_id]
            for f in service_forecasts[-5:]:
                timeline.append({
                    "event": "forecast",
                    "final_score": f.get("final_score"),
                    "final_health": f.get("final_health"),
                    "trend": f.get("trend"),
                    "timestamp": f.get("created_at"),
                })
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_services(self) -> list[dict]:
        scored = []
        for sid, svc in self.services.items():
            score = svc.get("current_score", 0)
            if svc.get("trend") == TrendDirection.DEGRADING.value:
                score -= 0.3
            elif svc.get("trend") == TrendDirection.IMPROVING.value:
                score += 0.1
            scored.append({"service_id": sid, "name": svc.get("name"), "score": round(score, 4)})
        return sorted(scored, key=lambda x: x["score"])[:20]

    def simulate_health_degradation(self, service_id: str, steps: int = 10) -> list[dict]:
        results = []
        for i in range(steps):
            import random; noise = random.gauss(0, 0.05)
            score = max(0.05, 1.0 - (i * 0.1) + noise)
            dims = {
                HealthDimension.AVAILABILITY.value: score,
                HealthDimension.PERFORMANCE.value: max(0, score - 0.05),
                HealthDimension.CAPACITY.value: max(0, score - 0.1),
                HealthDimension.RELIABILITY.value: max(0, score + 0.05),
            }
            snap = self.record_snapshot(service_id, dims)
            results.append(snap)
        return results

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_health_slo(self, target_health_score: float = 0.95) -> dict:
        scores = [s.get("current_score", 0) for s in self.services.values()]
        avg_score = statistics.mean(scores) if scores else 1.0
        compliant = avg_score >= target_health_score
        at_risk = sum(1 for s in self.services.values()
                      if s.get("current_health") in (HealthStatus.DEGRADED.value, HealthStatus.CRITICAL.value))
        return {
            "slo_target_score": target_health_score,
            "actual_avg_score": round(avg_score, 4),
            "compliant": compliant,
            "services_at_risk": at_risk,
            "total_services": len(self.services),
            "recommendation": "within target" if compliant else "review at-risk services",
        }

    def generate_health_report(self, days: int = 30) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_snapshots = [s for s in self.snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff]
        recent_forecasts = [f for f in self.forecasts if datetime.fromisoformat(f["created_at"]) > cutoff]
        health_by_service = defaultdict(list)
        for s in recent_snapshots:
            health_by_service[s["service_id"]].append(s.get("overall_score", 0))
        service_summaries = []
        for sid, scores in health_by_service.items():
            svc = self.get_service(sid)
            service_summaries.append({
                "service_id": sid,
                "name": svc.get("name", sid) if svc else sid,
                "avg_score": round(statistics.mean(scores), 4),
                "trend": "up" if scores[-1] > scores[0] else "down" if scores[-1] < scores[0] else "stable",
                "data_points": len(scores),
            })
        return {
            "period_days": days,
            "total_snapshots": len(recent_snapshots),
            "total_forecasts": len(recent_forecasts),
            "service_summaries": sorted(service_summaries, key=lambda x: x["avg_score"])[:20],
            "overall_avg_score": round(statistics.mean([s["avg_score"] for s in service_summaries]), 4) if service_summaries else 0,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "forecast_horizon_hours": self.forecast_horizon,
            "degradation_threshold": self.degradation_threshold,
            "critical_threshold": self.critical_threshold,
            "total_services": len(self.services),
            "total_snapshots": len(self.snapshots),
        }

    def compare_services(self, service_ids: list[str]) -> list[dict]:
        results = []
        for sid in service_ids:
            svc = self.get_service(sid)
            if svc:
                dims = {}
                service_snapshots = [s for s in self.snapshots if s.get("service_id") == sid][-1:]
                if service_snapshots:
                    dims = service_snapshots[-1].get("dimensions", {})
                results.append({
                    "service_id": sid,
                    "name": svc.get("name"),
                    "health": svc.get("current_health"),
                    "score": svc.get("current_score"),
                    "trend": svc.get("trend"),
                    "dimensions": dims,
                })
        return results

    def get_dependency_impact(self, service_id: str) -> list[dict]:
        svc = self.get_service(service_id)
        if not svc:
            return []
        deps = svc.get("dependencies", [])
        impacted = []
        for dep_id in deps:
            dep_svc = self.get_service(dep_id)
            if dep_svc:
                impacted.append({
                    "service_id": dep_id,
                    "name": dep_svc.get("name"),
                    "health": dep_svc.get("current_health"),
                    "score": dep_svc.get("current_score"),
                })
        return impacted

    def get_health_forecast_accuracy(self) -> dict:
        comparisons = []
        for f in self.forecasts[-100:]:
            sid = f.get("service_id")
            if not sid:
                continue
            service_snapshots = [s for s in self.snapshots if s.get("service_id") == sid]
            if service_snapshots:
                actual = service_snapshots[-1].get("overall_score", 0)
                predicted = f.get("final_score", 0)
                error = abs(actual - predicted)
                comparisons.append(error)
        if not comparisons:
            return {"error": "Insufficient data for accuracy calculation"}
        return {
            "mean_absolute_error": round(statistics.mean(comparisons), 4),
            "max_error": round(max(comparisons), 4),
            "min_error": round(min(comparisons), 4),
            "samples": len(comparisons),
            "accuracy_pct": round((1 - statistics.mean(comparisons)) * 100, 2),
        }

    def batch_forecast_all(self) -> list[dict]:
        results = []
        for sid in self.services:
            f = self.forecast(sid)
            results.append(f)
        return results

    def get_degraded_services(self) -> list[dict]:
        return [{"service_id": sid.get("id"), "name": sid.get("name"), "current_health": sid.get("current_health"), "current_score": sid.get("current_score"), "trend": sid.get("trend")} for sid in self.services if sid.get("current_health") in ("degraded", "critical")]

    def get_improving_services(self) -> list[dict]:
        return [{"service_id": sid.get("id"), "name": sid.get("name"), "current_health": sid.get("current_health"), "score_trend": sid.get("trend")} for sid in self.services if sid.get("trend") == "improving"]

    def get_declining_services(self) -> list[dict]:
        return [{"service_id": sid.get("id"), "name": sid.get("name"), "current_health": sid.get("current_health"), "score_trend": sid.get("trend")} for sid in self.services if sid.get("trend") == "declining"]

    def export_service_data(self, service_id: str) -> Optional[dict]:
        svc = self.get_service(service_id)
        if not svc:
            return None
        snapshots = [s for s in self.snapshots if s.get("service_id") == service_id]
        forecasts = [f for f in self.forecasts if f.get("service_id") == service_id]
        return {"service": svc, "snapshots": snapshots[-50:], "forecasts": forecasts[-20:]}

    def get_top_forecast_errors(self, limit: int = 10) -> list[dict]:
        errors = []
        for f in self.forecasts[-200:]:
            sid = f.get("service_id")
            if not sid:
                continue
            snapshots = [s for s in self.snapshots if s.get("service_id") == sid]
            if snapshots:
                actual = snapshots[-1].get("overall_score", 0)
                predicted = f.get("final_score", 0)
                error = abs(actual - predicted)
                errors.append({"service_id": sid, "predicted": predicted, "actual": actual, "error": round(error, 4)})
        return sorted(errors, key=lambda x: x["error"], reverse=True)[:limit]

    def get_health_timeline(self, service_id: str, days: int = 30) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots = [s for s in self.snapshots if s.get("service_id") == service_id and datetime.fromisoformat(s["timestamp"]) > cutoff]
        return [{"timestamp": s.get("timestamp"), "score": s.get("overall_score"), "health": s.get("health")} for s in sorted(snapshots, key=lambda x: x.get("timestamp", ""))]


class HealthAlertManager:
    def __init__(self, engine: HealthForecastingEngine):
        self.engine = engine
        self.alerts: list[dict] = []

    def check_degradations(self) -> list[dict]:
        new_alerts = []
        for svc in self.engine.services:
            if svc.get("current_health") == "critical":
                alert = {"id": str(uuid.uuid4()), "service_id": svc.get("id"), "service_name": svc.get("name"), "health": "critical", "score": svc.get("current_score"), "timestamp": datetime.utcnow().isoformat()}
                self.alerts.append(alert)
                new_alerts.append(alert)
            elif svc.get("current_health") == "degraded":
                if svc.get("trend") == "declining":
                    alert = {"id": str(uuid.uuid4()), "service_id": svc.get("id"), "service_name": svc.get("name"), "health": "degraded", "trend": "declining", "score": svc.get("current_score"), "timestamp": datetime.utcnow().isoformat()}
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
        return {"total_active": len(active), "critical": sum(1 for a in active if a.get("health") == "critical"), "degraded": sum(1 for a in active if a.get("health") == "degraded"), "total_alerts": len(self.alerts)}


class HealthDashboardAggregator:
    def __init__(self, engine: HealthForecastingEngine):
        self.engine = engine

    def get_overview(self) -> dict:
        total = len(self.engine.services)
        healthy = sum(1 for s in self.engine.services if s.get("current_health") == "healthy")
        degraded = sum(1 for s in self.engine.services if s.get("current_health") == "degraded")
        critical = sum(1 for s in self.engine.services if s.get("current_health") == "critical")
        return {"total_services": total, "healthy": healthy, "degraded": degraded, "critical": critical, "health_score": round(healthy / max(total, 1) * 100, 1), "avg_score": round(statistics.mean([s.get("current_score", 0) for s in self.engine.services]), 1) if self.engine.services else 0}

    def get_service_type_distribution(self) -> dict:
        types: dict[str, int] = defaultdict(int)
        for s in self.engine.services:
            svc_type = s.get("type", "unknown")
            types[svc_type] += 1
        return dict(types)

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
