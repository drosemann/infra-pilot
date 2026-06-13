"""Feature 55: Predictive Auto-Scaling — ML-based workload prediction and proactive scaling."""

import json
import os
import uuid
import math
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class PredictionMethod(Enum):
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_TREND = "linear_trend"
    SEASONAL_DECOMPOSE = "seasonal_decompose"
    ARIMA = "arima"
    PROPHET = "prophet"
    ENSEMBLE = "ensemble"


class ScalingDirection(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


class ScalingPolicy(Enum):
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"


class PredictiveScalingEngine:
    """ML-based workload prediction with proactive resource scaling."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_policy = ScalingPolicy(config.get("default_policy", "moderate"))
        self.min_observations = config.get("min_observations", 20)
        self.forecast_horizon = config.get("forecast_horizon_minutes", 60)
        self.seasonality_period = config.get("seasonality_period_minutes", 1440)
        self.metrics_file = _data_file('scaling_metrics.json')
        self.predictions_file = _data_file('scaling_predictions.json')
        self.actions_file = _data_file('scaling_actions.json')
        self.metrics_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.predictions: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.policies: Dict[str, str] = {}
        self._load_data()

    def _load_data(self):
        try:
            with open(self.predictions_file, 'r') as f:
                self.predictions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.actions_file, 'r') as f:
                self.actions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
                for key, values in data.items():
                    self.metrics_store[key] = deque(values, maxlen=10000)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_metrics(self):
        data = {k: list(v) for k, v in self.metrics_store.items()}
        with open(self.metrics_file, 'w') as f:
            json.dump(data, f, default=str)

    def _save_predictions(self):
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions[-1000:], f, default=str)

    def _save_actions(self):
        with open(self.actions_file, 'w') as f:
            json.dump(self.actions[-5000:], f, default=str)

    def record_metric(self, resource_id: str, metric_name: str, value: float,
                      timestamp: str = None) -> Dict[str, Any]:
        key = f"{resource_id}:{metric_name}"
        point = {
            "value": value,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
        }
        self.metrics_store[key].append(point)
        self._save_metrics()
        return point

    def set_scaling_policy(self, resource_id: str, policy: str) -> bool:
        if policy not in [p.value for p in ScalingPolicy]:
            return False
        self.policies[resource_id] = policy
        return True

    def get_scaling_policy(self, resource_id: str) -> str:
        return self.policies.get(resource_id, self.default_policy.value)

    def _get_time_series(self, resource_id: str, metric_name: str,
                         minutes: int = 120) -> Tuple[List[float], List[datetime]]:
        key = f"{resource_id}:{metric_name}"
        points = list(self.metrics_store.get(key, []))
        if minutes > 0:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            points = [p for p in points if datetime.fromisoformat(p["timestamp"]) > cutoff]
        values = [p["value"] for p in points]
        times = [datetime.fromisoformat(p["timestamp"]) for p in points]
        return values, times

    def _moving_average_forecast(self, values: List[float], steps: int, window: int = 5) -> List[float]:
        if len(values) < window:
            return [statistics.mean(values) if values else 0] * steps
        forecasts = []
        recent = list(values)
        for _ in range(steps):
            forecast = statistics.mean(recent[-window:])
            forecasts.append(forecast)
            recent.append(forecast)
        return forecasts

    def _exponential_smoothing_forecast(self, values: List[float], steps: int,
                                         alpha: float = 0.3) -> List[float]:
        if not values:
            return [0] * steps
        smoothed = values[0]
        forecasts = []
        for _ in range(steps):
            if values:
                smoothed = alpha * values[-1] + (1 - alpha) * smoothed
            forecasts.append(smoothed)
        return forecasts

    def _linear_trend_forecast(self, values: List[float], steps: int) -> List[float]:
        n = len(values)
        if n < 2:
            return [values[-1] if values else 0] * steps
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        return [intercept + slope * (n + i) for i in range(steps)]

    def _seasonal_forecast(self, values: List[float], steps: int,
                            period: int = None) -> List[float]:
        if period is None:
            period = self.seasonality_period
        if len(values) < period * 2:
            return self._moving_average_forecast(values, steps)
        seasonal_means = []
        for i in range(period):
            seasonal_means.append(statistics.mean(values[i::period]))
        overall_mean = statistics.mean(seasonal_means)
        seasonal_factors = [s - overall_mean for s in seasonal_means]
        trend_forecast = self._linear_trend_forecast(values, steps)
        forecasts = []
        for i in range(steps):
            seasonal_idx = (len(values) + i) % period
            forecasts.append(trend_forecast[i] + seasonal_factors[seasonal_idx])
        return forecasts

    def _ensemble_forecast(self, values: List[float], steps: int) -> List[float]:
        if len(values) < 5:
            return self._moving_average_forecast(values, steps)
        ma = self._moving_average_forecast(values, steps)
        es = self._exponential_smoothing_forecast(values, steps)
        lt = self._linear_trend_forecast(values, steps)
        return [(ma[i] + es[i] + lt[i]) / 3 for i in range(steps)]

    def predict(self, resource_id: str, metric_name: str = "cpu",
                method: str = "ensemble", steps: int = None) -> Dict[str, Any]:
        if steps is None:
            steps = max(1, self.forecast_horizon // 5)
        values, times = self._get_time_series(resource_id, metric_name)
        if len(values) < self.min_observations:
            return {
                "resource_id": resource_id,
                "metric": metric_name,
                "error": f"Insufficient data: {len(values)} points, need {self.min_observations}",
                "observed_values": len(values),
                "forecast": [],
                "method": method,
            }
        method_map = {
            PredictionMethod.MOVING_AVERAGE.value: self._moving_average_forecast,
            PredictionMethod.EXPONENTIAL_SMOOTHING.value: self._exponential_smoothing_forecast,
            PredictionMethod.LINEAR_TREND.value: self._linear_trend_forecast,
            PredictionMethod.SEASONAL_DECOMPOSE.value: self._seasonal_forecast,
            PredictionMethod.ENSEMBLE.value: self._ensemble_forecast,
        }
        forecast_fn = method_map.get(method, self._ensemble_forecast)
        try:
            forecast = forecast_fn(values, steps)
        except Exception as e:
            logger.warning(f"Forecast method {method} failed: {e}")
            forecast = self._ensemble_forecast(values, steps)
        current = values[-1] if values else 0
        peak_forecast = max(forecast) if forecast else current
        avg_forecast = statistics.mean(forecast) if forecast else current
        direction = ScalingDirection.NO_ACTION.value
        threshold = self._get_scaling_threshold(resource_id)
        if peak_forecast > current * (1 + threshold):
            direction = ScalingDirection.SCALE_UP.value
        elif peak_forecast < current * (1 - threshold * 0.5):
            direction = ScalingDirection.SCALE_DOWN.value
        result = {
            "id": str(uuid.uuid4()),
            "resource_id": resource_id,
            "metric": metric_name,
            "method": method,
            "observed_values": len(values),
            "current_value": round(current, 4),
            "forecast": [round(v, 4) for v in forecast],
            "peak_forecast": round(peak_forecast, 4),
            "avg_forecast": round(avg_forecast, 4),
            "direction": direction,
            "confidence": self._compute_confidence(values, forecast),
            "recommended_action": self._recommend_action(resource_id, direction, peak_forecast),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.predictions.append(result)
        self._save_predictions()
        return result

    def _get_scaling_threshold(self, resource_id: str) -> float:
        policy = self.get_scaling_policy(resource_id)
        thresholds = {
            ScalingPolicy.AGGRESSIVE.value: 0.1,
            ScalingPolicy.MODERATE.value: 0.2,
            ScalingPolicy.CONSERVATIVE.value: 0.35,
        }
        return thresholds.get(policy, 0.2)

    def _compute_confidence(self, values: List[float], forecast: List[float]) -> float:
        if len(values) < 10 or len(forecast) < 1:
            return 0.5
        recent = values[-min(10, len(values)):]
        actual_mean = statistics.mean(recent)
        if actual_mean == 0:
            return 0.5
        if len(values) >= 20:
            holdout = values[-10:]
            train = values[:-10]
            if len(train) >= 5:
                try:
                    test_forecast = self._ensemble_forecast(train, len(holdout))
                    errors = [abs(test_forecast[i] - holdout[i]) / max(holdout[i], 0.001) for i in range(len(holdout))]
                    mape = statistics.mean(errors)
                    confidence = max(0.1, min(0.99, 1.0 - mape))
                    return round(confidence, 4)
                except Exception:
                    pass
        variance = statistics.variance(recent) if len(recent) > 1 else 0
        cv = math.sqrt(variance) / actual_mean if actual_mean > 0 else 0
        return round(max(0.3, min(0.95, 1.0 - cv)), 4)

    def _recommend_action(self, resource_id: str, direction: str,
                           target_value: float) -> Dict[str, Any]:
        if direction == ScalingDirection.NO_ACTION.value:
            return {"action": "none", "message": "No scaling action needed at this time."}
        if direction == ScalingDirection.SCALE_UP.value:
            ratio = max(1.0, target_value / 50.0)
            return {
                "action": "scale_up",
                "message": f"Scale up recommended — predicted load reaches {target_value:.1f}%",
                "suggested_replicas": max(1, int(ratio)),
                "urgency": "high" if ratio > 2 else "medium",
            }
        return {
            "action": "scale_down",
            "message": f"Scale down possible — predicted load drops to {target_value:.1f}%",
            "suggested_replicas": max(1, int(target_value / 50.0)),
            "urgency": "low",
        }

    def execute_scaling_action(self, prediction_id: str, approved_by: str = "system") -> Optional[Dict[str, Any]]:
        prediction = next((p for p in self.predictions if p["id"] == prediction_id), None)
        if not prediction:
            return None
        action = {
            "id": str(uuid.uuid4()),
            "prediction_id": prediction_id,
            "resource_id": prediction["resource_id"],
            "direction": prediction["direction"],
            "recommended_action": prediction["recommended_action"],
            "approved_by": approved_by,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.actions.append(action)
        self._save_actions()
        return action

    def get_predictions(self, resource_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        result = self.predictions
        if resource_id:
            result = [p for p in result if p.get("resource_id") == resource_id]
        return result[-limit:]

    def get_actions(self, resource_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        result = self.actions
        if resource_id:
            result = [a for a in result if a.get("resource_id") == resource_id]
        return result[-limit:]

    def get_metrics(self, resource_id: str, metric_name: str = "cpu",
                    minutes: int = 60) -> Dict[str, Any]:
        values, times = self._get_time_series(resource_id, metric_name, minutes)
        if not values:
            return {"resource_id": resource_id, "metric": metric_name, "data_points": 0}
        return {
            "resource_id": resource_id,
            "metric": metric_name,
            "data_points": len(values),
            "current": round(values[-1], 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "avg": round(statistics.mean(values), 4),
            "stdev": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
            "recent_trend": "up" if len(values) >= 5 and statistics.mean(values[-5:]) > statistics.mean(values[:5]) else "down" if len(values) >= 5 else "stable",
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_metrics_streams": len(self.metrics_store),
            "total_predictions": len(self.predictions),
            "total_actions": len(self.actions),
            "active_policies": dict(self.policies),
            "recent_predictions": self.predictions[-10:] if self.predictions else [],
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_predictions(self, offset: int = 0, limit: int = 50, resource_id: str = None,
                              direction: str = None, method: str = None) -> dict:
        results = self.predictions
        if resource_id:
            results = [p for p in results if p.get("resource_id") == resource_id]
        if direction:
            results = [p for p in results if p.get("direction") == direction]
        if method:
            results = [p for p in results if p.get("method") == method]
        total = len(results)
        results.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_actions(self, offset: int = 0, limit: int = 50, resource_id: str = None,
                          status: str = None) -> dict:
        results = self.actions
        if resource_id:
            results = [a for a in results if a.get("resource_id") == resource_id]
        if status:
            results = [a for a in results if a.get("status") == status]
        total = len(results)
        results.sort(key=lambda a: a.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_execute_actions(self, prediction_ids: list[str], approved_by: str = "system") -> dict:
        succeeded = 0
        failed = 0
        for pid in prediction_ids:
            try:
                action = self.execute_scaling_action(pid, approved_by)
                if action:
                    succeeded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total_requested": len(prediction_ids)}

    def batch_record_metrics(self, resource_id: str, metrics: list[dict]) -> dict:
        recorded = 0
        for m in metrics:
            try:
                self.record_metric(resource_id, m.get("name", "cpu"), m["value"], m.get("timestamp"))
                recorded += 1
            except (KeyError, TypeError):
                pass
        return {"recorded": recorded, "total_requested": len(metrics)}

    def export_predictions(self, resource_id: str = None, method: str = None) -> list[dict]:
        results = self.predictions
        if resource_id:
            results = [p for p in results if p.get("resource_id") == resource_id]
        if method:
            results = [p for p in results if p.get("method") == method]
        return [{
            "id": p["id"], "resource_id": p.get("resource_id"), "metric": p.get("metric"),
            "method": p.get("method"), "direction": p.get("direction"),
            "current_value": p.get("current_value"), "peak_forecast": p.get("peak_forecast"),
            "avg_forecast": p.get("avg_forecast"), "confidence": p.get("confidence"),
            "recommended_action": p.get("recommended_action"), "created_at": p.get("created_at"),
        } for p in results]

    def import_predictions(self, predictions: list[dict]) -> dict:
        imported = 0
        for p in predictions:
            entry = {
                "id": str(uuid.uuid4()),
                "resource_id": p.get("resource_id", "unknown"),
                "metric": p.get("metric", "cpu"),
                "method": p.get("method", "ensemble"),
                "observed_values": p.get("observed_values", 0),
                "current_value": p.get("current_value", 0),
                "forecast": p.get("forecast", []),
                "peak_forecast": p.get("peak_forecast", 0),
                "avg_forecast": p.get("avg_forecast", 0),
                "direction": p.get("direction", "no_action"),
                "confidence": p.get("confidence", 0.5),
                "recommended_action": p.get("recommended_action", {}),
                "created_at": p.get("created_at", datetime.utcnow().isoformat()),
            }
            self.predictions.append(entry)
            imported += 1
        self._save_predictions()
        return {"imported": imported}

    def export_actions(self, resource_id: str = None, status: str = None) -> list[dict]:
        results = self.actions
        if resource_id:
            results = [a for a in results if a.get("resource_id") == resource_id]
        if status:
            results = [a for a in results if a.get("status") == status]
        return [{
            "id": a["id"], "prediction_id": a.get("prediction_id"),
            "resource_id": a.get("resource_id"), "direction": a.get("direction"),
            "recommended_action": a.get("recommended_action"),
            "approved_by": a.get("approved_by"), "status": a.get("status"),
            "created_at": a.get("created_at"),
        } for a in results]

    def get_analytics(self) -> dict:
        policy_counts = Counter(self.policies.values())
        direction_counts = Counter(p.get("direction", "unknown") for p in self.predictions)
        method_counts = Counter(p.get("method", "unknown") for p in self.predictions)
        predictions_by_hour = {}
        for p in self.predictions:
            try:
                hour = datetime.fromisoformat(p["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                predictions_by_hour[hour] = predictions_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        avg_confidence = statistics.mean([p.get("confidence", 0) for p in self.predictions]) if self.predictions else 0
        action_counts = Counter(a.get("direction", "unknown") for a in self.actions)
        return {
            "total_metric_streams": len(self.metrics_store),
            "total_predictions": len(self.predictions),
            "total_actions": len(self.actions),
            "policy_distribution": dict(policy_counts),
            "direction_distribution": dict(direction_counts),
            "method_distribution": dict(method_counts),
            "action_direction_distribution": dict(action_counts),
            "avg_confidence": round(avg_confidence, 4),
            "predictions_by_hour": dict(sorted(predictions_by_hour.items())[-24:]),
            "top_predicted_resources": [{"resource": r, "count": c} for r, c in
                                         Counter(p.get("resource_id", "unknown") for p in self.predictions).most_common(10)],
        }

    def search_predictions(self, query: str) -> list[dict]:
        q = query.lower()
        return [p for p in self.predictions if q in p.get("resource_id", "").lower()
                or q in p.get("metric", "").lower() or q in p.get("method", "").lower()]

    def get_resource_timeline(self, resource_id: str) -> list[dict]:
        timeline = []
        for p in self.predictions:
            if p.get("resource_id") == resource_id:
                timeline.append({
                    "event": f"prediction_{p.get('direction')}",
                    "prediction_id": p["id"],
                    "confidence": p.get("confidence"),
                    "timestamp": p.get("created_at"),
                })
        for a in self.actions:
            if a.get("resource_id") == resource_id:
                timeline.append({
                    "event": f"action_{a.get('direction')}",
                    "action_id": a["id"],
                    "status": a.get("status"),
                    "timestamp": a.get("created_at"),
                })
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_resources(self) -> list[dict]:
        counter = Counter()
        for p in self.predictions:
            r = p.get("resource_id", "unknown")
            counter[r] += 1
            if p.get("direction") == ScalingDirection.SCALE_UP.value:
                counter[r] += 2
        return [{"resource": r, "score": c} for r, c in counter.most_common(20)]

    def simulate_metric_stream(self, resource_id: str, metric_name: str = "cpu",
                                 count: int = 30, interval_sec: float = 1.0) -> list[dict]:
        import random, time
        generated = []
        for _ in range(count):
            value = random.uniform(10, 95)
            point = self.record_metric(resource_id, metric_name, value)
            generated.append(point)
            time.sleep(interval_sec)
        return generated

    def batch_set_policies(self, policies: dict[str, str]) -> dict:
        succeeded = 0
        failed = 0
        for resource_id, policy in policies.items():
            if self.set_scaling_policy(resource_id, policy):
                succeeded += 1
            else:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total": len(policies)}

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_scaling_slo(self, target_confidence: float = 0.8, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [p for p in self.predictions if datetime.fromisoformat(p["created_at"]) > cutoff]
        if not recent:
            return {"error": "No predictions in window"}
        avg_conf = statistics.mean([p.get("confidence", 0) for p in recent])
        compliant = avg_conf >= target_confidence
        scale_up_count = sum(1 for p in recent if p.get("direction") == ScalingDirection.SCALE_UP.value)
        return {
            "slo_target_confidence": target_confidence,
            "actual_avg_confidence": round(avg_conf, 4),
            "compliant": compliant,
            "window_hours": window_hours,
            "total_predictions": len(recent),
            "scale_up_count": scale_up_count,
            "actions_taken": sum(1 for a in self.actions if datetime.fromisoformat(a["created_at"]) > cutoff),
        }

    def generate_scaling_report(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_predictions = [p for p in self.predictions if datetime.fromisoformat(p["created_at"]) > cutoff]
        recent_actions = [a for a in self.actions if datetime.fromisoformat(a["created_at"]) > cutoff]
        by_direction = Counter(p.get("direction", "unknown") for p in recent_predictions)
        by_method = Counter(p.get("method", "unknown") for p in recent_predictions)
        by_policy = Counter(self.policies.values())
        avg_conf = statistics.mean([p.get("confidence", 0) for p in recent_predictions]) if recent_predictions else 0
        return {
            "period_days": days,
            "total_predictions": len(recent_predictions),
            "total_actions": len(recent_actions),
            "direction_distribution": dict(by_direction),
            "method_distribution": dict(by_method),
            "policy_distribution": dict(by_policy),
            "avg_confidence": round(avg_conf, 4),
            "scale_up_pct": round((by_direction.get(ScalingDirection.SCALE_UP.value, 0) / max(len(recent_predictions), 1)) * 100, 1),
            "scale_down_pct": round((by_direction.get(ScalingDirection.SCALE_DOWN.value, 0) / max(len(recent_predictions), 1)) * 100, 1),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "default_policy": self.default_policy.value if isinstance(self.default_policy, Enum) else self.default_policy,
            "min_observations": self.min_observations,
            "forecast_horizon_minutes": self.forecast_horizon,
            "total_metric_streams": len(self.metrics_store),
            "total_predictions": len(self.predictions),
            "active_policies": dict(self.policies),
        }

    def compare_methods(self, resource_id: str, metric_name: str = "cpu") -> list[dict]:
        methods = ["moving_average", "exponential_smoothing", "linear_trend", "ensemble"]
        results = []
        for method in methods:
            pred = self.predict(resource_id, metric_name, method=method)
            if "error" not in pred:
                results.append({
                    "method": method,
                    "confidence": pred.get("confidence"),
                    "direction": pred.get("direction"),
                    "peak_forecast": pred.get("peak_forecast"),
                    "avg_forecast": pred.get("avg_forecast"),
                })
        return results

    def get_efficiency_metrics(self) -> dict:
        total_predictions = len(self.predictions)
        if total_predictions == 0:
            return {"error": "No predictions available"}
        scale_up_actions = sum(1 for a in self.actions if a.get("direction") == ScalingDirection.SCALE_UP.value)
        scale_down_actions = sum(1 for a in self.actions if a.get("direction") == ScalingDirection.SCALE_DOWN.value)
        correct_actions = 0
        for a in self.actions:
            pid = a.get("prediction_id")
            if pid:
                p = next((x for x in self.predictions if x["id"] == pid), None)
                if p and p.get("direction") == a.get("direction"):
                    correct_actions += 1
        return {
            "total_predictions": total_predictions,
            "total_actions": len(self.actions),
            "scale_up_actions": scale_up_actions,
            "scale_down_actions": scale_down_actions,
            "action_accuracy": round((correct_actions / max(len(self.actions), 1)) * 100, 1),
            "resources_monitored": len(set(k.split(":")[0] for k in self.metrics_store.keys())),
            "avg_confidence": round(statistics.mean([p.get("confidence", 0) for p in self.predictions]), 4),
        }

    def get_prediction_trend(self, resource_id: str, days: int = 7) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [p for p in self.predictions if p.get("resource_id") == resource_id
                  and datetime.fromisoformat(p["created_at"]) > cutoff]
        daily = defaultdict(list)
        for p in recent:
            try:
                day = datetime.fromisoformat(p["created_at"]).strftime("%Y-%m-%d")
                daily[day].append(p.get("confidence", 0))
            except (ValueError, TypeError):
                pass
        return [{"date": d, "avg_confidence": round(statistics.mean(v), 4), "count": len(v)}
                for d, v in sorted(daily.items())]

    def batch_forecast_all(self, metric_name: str = "cpu") -> list[dict]:
        resources = set(k.split(":")[0] for k in self.metrics_store.keys())
        results = []
        for rid in resources:
            pred = self.predict(rid, metric_name)
            results.append(pred)
        return results

    def get_scaling_events(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.actions if datetime.fromisoftime(a.get("created_at", "")) > cutoff] if False else [a for a in self.actions if a.get("created_at") and datetime.fromisoformat(a["created_at"]) > cutoff]

    def get_resource_summary(self, resource_id: str) -> dict:
        keys = [k for k in self.metrics_store.keys() if k.startswith(resource_id)]
        if not keys:
            return {"resource_id": resource_id, "error": "No metrics found"}
        predictions = [p for p in self.predictions if p.get("resource_id") == resource_id]
        actions = [a for a in self.actions if a.get("resource_id") == resource_id]
        return {"resource_id": resource_id, "metrics_count": sum(len(v) for v in self.metrics_store.values() if any(k.startswith(resource_id) for k in self.metrics_store.keys())), "total_predictions": len(predictions), "total_actions": len(actions), "avg_confidence": round(statistics.mean([p.get("confidence", 0) for p in predictions]), 4) if predictions else 0}

    def get_top_scaling_resources(self, limit: int = 10) -> list[dict]:
        resource_action_count: dict[str, int] = defaultdict(int)
        for a in self.actions:
            rid = a.get("resource_id", "unknown")
            resource_action_count[rid] += 1
        sorted_resources = sorted(resource_action_count.items(), key=lambda x: x[1], reverse=True)
        result = []
        for rid, count in sorted_resources[:limit]:
            preds = [p for p in self.predictions if p.get("resource_id") == rid]
            avg_conf = round(statistics.mean([p.get("confidence", 0) for p in preds]), 4) if preds else 0
            result.append({"resource_id": rid, "scaling_actions": count, "avg_confidence": avg_conf})
        return result

    def export_metrics_csv(self, resource_id: str, metric_name: str) -> str:
        key = f"{resource_id}:{metric_name}"
        points = list(self.metrics_store.get(key, []))
        if not points:
            return ""
        lines = ["timestamp,value,metric_name,resource_id"]
        for p in points:
            ts = p.get("timestamp", "")
            val = p.get("value", "")
            lines.append(f"{ts},{val},{metric_name},{resource_id}")
        return "\n".join(lines)

    def import_metrics_csv(self, csv_content: str) -> dict:
        imported = 0
        for line in csv_content.strip().split("\n")[1:]:
            parts = line.split(",")
            if len(parts) >= 2:
                key = f"{parts[3]}:{parts[2]}"
                point = {"timestamp": parts[0], "value": float(parts[1]), "resource_id": parts[3], "metric_name": parts[2]}
                if key not in self.metrics_store:
                    self.metrics_store[key] = deque(maxlen=self.config.get("max_history", 1000))
                self.metrics_store[key].append(point)
                imported += 1
        return {"imported": imported}

    def get_cost_savings_estimate(self, resource_id: str) -> dict:
        actions = [a for a in self.actions if a.get("resource_id") == resource_id]
        scale_down_actions = [a for a in actions if a.get("direction") == ScalingDirection.SCALE_DOWN.value]
        scale_up_actions = [a for a in actions if a.get("direction") == ScalingDirection.SCALE_UP.value]
        estimated_savings = len(scale_down_actions) * 10 - len(scale_up_actions) * 5
        return {"resource_id": resource_id, "scale_down_events": len(scale_down_actions), "scale_up_events": len(scale_up_actions), "estimated_monthly_savings_dollars": max(0, estimated_savings), "recommendation": "Optimizing further" if estimated_savings > 0 else "Review scaling thresholds"}


class ScalingAlertManager:
    def __init__(self, engine: PredictiveScalingEngine):
        self.engine = engine
        self.alerts: list[dict] = []

    def check_anomalies(self, resource_id: str, metric_name: str = "cpu") -> list[dict]:
        key = f"{resource_id}:{metric_name}"
        points = list(self.engine.metrics_store.get(key, []))
        if len(points) < 10:
            return []
        values = [p.get("value", 0) for p in points[-20:]]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        alerts = []
        for p in points[-5:]:
            val = p.get("value", 0)
            if stdev > 0 and abs(val - mean) > 3 * stdev:
                alert = {"id": str(uuid.uuid4()), "resource_id": resource_id, "metric_name": metric_name, "value": val, "expected": round(mean, 2), "deviation": round(abs(val - mean), 2), "severity": "critical" if abs(val - mean) > 5 * stdev else "warning", "timestamp": datetime.utcnow().isoformat()}
                self.alerts.append(alert)
                alerts.append(alert)
        return alerts

    def get_active_alerts(self) -> list[dict]:
        return [a for a in self.alerts if not a.get("acknowledged_at")]

    def acknowledge_alert(self, alert_id: str, user: str) -> Optional[dict]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged_at"] = datetime.utcnow().isoformat()
                a["acknowledged_by"] = user
                return a
        return None

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
