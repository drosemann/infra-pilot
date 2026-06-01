"""Feature 84: Time-Series Anomaly Detection - Automated metric anomaly detection"""

import json
import os
import math
import uuid
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionMethod(Enum):
    ZSCORE = "zscore"
    MAD = "mad"
    IQR = "iqr"
    STL = "stl"
    ISOLATION_FOREST = "isolation_forest"
    DBSCAN = "dbscan"
    PELT = "pelt"
    PREDICTION_INTERVAL = "prediction_interval"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    MOVING_AVERAGE = "moving_average"
    GRUBBS = "grubbs"
    ESD = "esd"
    CUSUM = "cusum"
    EWMA = "ewma"


class TimeSeriesAnomalyDetector:
    """Automated anomaly detection on time-series metrics using multiple methods"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.window_size = config.get("window_size", 100)
        self.seasonality_period = config.get("seasonality_period", 24)
        self.zscore_threshold = config.get("zscore_threshold", 3.0)
        self.mad_threshold = config.get("mad_threshold", 3.5)
        self.iqr_multiplier = config.get("iqr_multiplier", 1.5)
        self.adaptive_sensitivity = config.get("adaptive_sensitivity", 0.05)

        self.metrics_file = _data_file('anomaly_metrics.json')
        self.events_file = _data_file('anomaly_events.json')
        self.models_file = _data_file('anomaly_models.json')

        self.metric_store: Dict[str, deque] = {}
        self.anomaly_events: List[Dict[str, Any]] = []
        self.models: Dict[str, Dict[str, Any]] = {}
        self.detection_methods: Dict[str, List[DetectionMethod]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.metrics_file, "metrics"),
            (self.events_file, "events"),
            (self.models_file, "models")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "metrics":
                        self.metric_store = {k: deque(v, maxlen=self.window_size) for k, v in data.items()}
                    elif target == "events":
                        self.anomaly_events = data[-10000:]
                    elif target == "models":
                        self.models = data
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_metrics(self):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump({k: list(v) for k, v in self.metric_store.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _save_events(self):
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.anomaly_events[-10000:], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save events: {e}")

    def _save_models(self):
        try:
            with open(self.models_file, 'w') as f:
                json.dump(self.models, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _zscore(self, values: List[float]) -> List[float]:
        if len(values) < 3:
            return [0.0] * len(values)
        mean = statistics.mean(values)
        std = statistics.pstdev(values) or 1e-10
        return [(v - mean) / std for v in values]

    def _modified_zscore(self, values: List[float]) -> List[float]:
        if len(values) < 3:
            return [0.0] * len(values)
        median = statistics.median(values)
        mad = statistics.median([abs(v - median) for v in values]) or 1e-10
        return [0.6745 * (v - median) / mad for v in values]

    def _iqr_bounds(self, values: List[float]) -> Tuple[float, float, float, float]:
        if len(values) < 4:
            return (0, 0, 0, 0)
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        lower = q1 - self.iqr_multiplier * iqr
        upper = q3 + self.iqr_multiplier * iqr
        return (q1, q3, lower, upper)

    def _moving_average(self, values: List[float], period: int = 5) -> List[float]:
        if len(values) < period:
            return values[:]
        result = []
        for i in range(len(values)):
            start = max(0, i - period + 1)
            window = values[start:i + 1]
            result.append(statistics.mean(window))
        return result

    def _exponential_smoothing(self, values: List[float], alpha: float = 0.3) -> List[float]:
        if not values:
            return []
        result = [values[0]]
        for v in values[1:]:
            result.append(alpha * v + (1 - alpha) * result[-1])
        return result

    def _seasonal_decompose(self, values: List[float], period: int = 24) -> Tuple[List[float], List[float], List[float]]:
        if len(values) < period * 2:
            trend = self._moving_average(values, period)
            return (trend, [0] * len(values), [v - t for v, t in zip(values, trend)])
        trend = self._moving_average(values, period)
        detrended = [v - t for v, t in zip(values, trend)]
        seasonal = [0.0] * len(values)
        for i in range(period):
            indices = list(range(i, len(values), period))
            if indices:
                season_val = statistics.mean([detrended[j] for j in indices if j < len(detrended)])
                for j in indices:
                    if j < len(seasonal):
                        seasonal[j] = season_val
        residual = [v - t - s for v, t, s in zip(values, trend, seasonal)]
        return (trend, seasonal, residual)

    def _cusum(self, values: List[float], threshold: float = 5.0, drift: float = 0.5) -> List[float]:
        if not values:
            return []
        mean = statistics.mean(values)
        cusum_upper = [0.0]
        cusum_lower = [0.0]
        for v in values[1:]:
            u = max(0, cusum_upper[-1] + (v - mean) - drift)
            cusum_upper.append(u)
            l_val = max(0, cusum_lower[-1] - (v - mean) - drift)
            cusum_lower.append(l_val)
        return [max(u, l) for u, l in zip(cusum_upper, cusum_lower)]

    def _grubbs_test(self, values: List[float], alpha: float = 0.05) -> Tuple[Optional[int], float]:
        if len(values) < 3:
            return (None, 0.0)
        mean = statistics.mean(values)
        std = statistics.pstdev(values) or 1e-10
        n = len(values)
        t_critical = 2.776  # approximate for n=5 at alpha=0.05, simplified
        g_critical = (n - 1) / math.sqrt(n) * math.sqrt(t_critical ** 2 / (n - 2 + t_critical ** 2))
        max_dev = 0
        max_idx = None
        for i, v in enumerate(values):
            g = abs(v - mean) / std
            if g > max_dev:
                max_dev = g
                max_idx = i
        if max_dev > g_critical:
            return (max_idx, max_dev)
        return (None, max_dev)

    def _detect_anomalies_zscore(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        zscores = self._zscore(values)
        for i, z in enumerate(zscores):
            if abs(z) > self.zscore_threshold:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.ZSCORE.value,
                    "index": i,
                    "value": values[i],
                    "zscore": z,
                    "severity": AnomalySeverity.HIGH.value if abs(z) > self.zscore_threshold * 1.5 else AnomalySeverity.MEDIUM.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_mad(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        mzscores = self._modified_zscore(values)
        for i, mz in enumerate(mzscores):
            if abs(mz) > self.mad_threshold:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.MAD.value,
                    "index": i,
                    "value": values[i],
                    "mad_score": mz,
                    "severity": AnomalySeverity.HIGH.value if abs(mz) > self.mad_threshold * 1.5 else AnomalySeverity.MEDIUM.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_iqr(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        if len(values) < 4:
            return anomalies
        q1, q3, lower, upper = self._iqr_bounds(values)
        for i, v in enumerate(values):
            if v < lower or v > upper:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.IQR.value,
                    "index": i,
                    "value": v,
                    "q1": q1,
                    "q3": q3,
                    "lower_bound": lower,
                    "upper_bound": upper,
                    "severity": AnomalySeverity.MEDIUM.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_stl(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        if len(values) < self.seasonality_period * 2:
            return anomalies
        trend, seasonal, residual = self._seasonal_decompose(values, self.seasonality_period)
        if len(residual) < 3:
            return anomalies
        residual_std = statistics.pstdev(residual) or 1e-10
        for i, r in enumerate(residual):
            if abs(r) > 3 * residual_std:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.STL.value,
                    "index": i,
                    "value": values[i],
                    "trend": trend[i] if i < len(trend) else 0,
                    "seasonal": seasonal[i] if i < len(seasonal) else 0,
                    "residual": r,
                    "severity": AnomalySeverity.HIGH.value if abs(r) > 5 * residual_std else AnomalySeverity.MEDIUM.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_moving_average(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        if len(values) < 6:
            return anomalies
        ma = self._moving_average(values, 5)
        residuals = [v - m for v, m in zip(values, ma)]
        if len(residuals) < 3:
            return anomalies
        std = statistics.pstdev(residuals) or 1e-10
        for i, r in enumerate(residuals):
            if abs(r) > 2 * std:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.MOVING_AVERAGE.value,
                    "index": i,
                    "value": values[i],
                    "expected": ma[i] if i < len(ma) else 0,
                    "deviation": r,
                    "severity": AnomalySeverity.LOW.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_cusum(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        if len(values) < 10:
            return anomalies
        cusum_vals = self._cusum(values)
        threshold = 5.0
        for i, cv in enumerate(cusum_vals):
            if cv > threshold:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.CUSUM.value,
                    "index": i,
                    "value": values[i],
                    "cusum_value": cv,
                    "severity": AnomalySeverity.HIGH.value if cv > threshold * 2 else AnomalySeverity.MEDIUM.value,
                    "timestamp": timestamp
                })
        return anomalies

    def _detect_anomalies_adaptive_threshold(self, metric_id: str, values: List[float], timestamp: str) -> List[Dict[str, Any]]:
        anomalies = []
        if len(values) < 20:
            return anomalies
        recent = values[-20:]
        mean = statistics.mean(recent)
        std = statistics.pstdev(recent) or 1e-10
        threshold = self.adaptive_sensitivity
        dynamic_threshold = std * (3.0 + threshold * 10.0)
        for i, v in enumerate(values):
            if abs(v - mean) > dynamic_threshold:
                anomalies.append({
                    "metric_id": metric_id,
                    "method": DetectionMethod.ADAPTIVE_THRESHOLD.value,
                    "index": i,
                    "value": v,
                    "mean": mean,
                    "dynamic_threshold": dynamic_threshold,
                    "severity": AnomalySeverity.LOW.value,
                    "timestamp": timestamp
                })
        return anomalies

    async def ingest_metric(self, metric_id: str, value: float,
                             timestamp: Optional[str] = None,
                             labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        ts = timestamp or self._now()
        if metric_id not in self.metric_store:
            self.metric_store[metric_id] = deque(maxlen=self.window_size)
        self.metric_store[metric_id].append(value)
        self._save_metrics()

        return {
            "metric_id": metric_id,
            "value": value,
            "timestamp": ts,
            "window_size": len(self.metric_store[metric_id]),
            "labels": labels or {}
        }

    async def detect_anomalies(self, metric_id: Optional[str] = None,
                                 methods: Optional[List[str]] = None) -> Dict[str, Any]:
        if methods is None:
            methods = [m.value for m in DetectionMethod]

        if metric_id:
            metric_keys = [metric_id]
        else:
            metric_keys = list(self.metric_store.keys())

        all_anomalies = []
        per_metric = {}

        for mid in metric_keys:
            values = list(self.metric_store.get(mid, []))
            if len(values) < 5:
                continue

            metric_anomalies = []
            ts = self._now()

            if DetectionMethod.ZSCORE.value in methods:
                metric_anomalies.extend(self._detect_anomalies_zscore(mid, values, ts))
            if DetectionMethod.MAD.value in methods:
                metric_anomalies.extend(self._detect_anomalies_mad(mid, values, ts))
            if DetectionMethod.IQR.value in methods:
                metric_anomalies.extend(self._detect_anomalies_iqr(mid, values, ts))
            if DetectionMethod.STL.value in methods:
                metric_anomalies.extend(self._detect_anomalies_stl(mid, values, ts))
            if DetectionMethod.MOVING_AVERAGE.value in methods:
                metric_anomalies.extend(self._detect_anomalies_moving_average(mid, values, ts))
            if DetectionMethod.CUSUM.value in methods:
                metric_anomalies.extend(self._detect_anomalies_cusum(mid, values, ts))
            if DetectionMethod.ADAPTIVE_THRESHOLD.value in methods:
                metric_anomalies.extend(self._detect_anomalies_adaptive_threshold(mid, values, ts))

            if metric_anomalies:
                per_metric[mid] = metric_anomalies
                all_anomalies.extend(metric_anomalies)

        merged_anomalies = self._merge_anomalies(all_anomalies)
        for anomaly in merged_anomalies:
            anomaly["id"] = self._generate_id()
            anomaly["detected_at"] = self._now()
            self.anomaly_events.append(anomaly)
        self._save_events()

        return {
            "total_anomalies": len(merged_anomalies),
            "metrics_analyzed": len(metric_keys),
            "per_metric": {k: len(v) for k, v in per_metric.items()},
            "anomalies": merged_anomalies[-50:],
            "detected_at": self._now()
        }

    def _merge_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not anomalies:
            return []

        grouped = {}
        for a in anomalies:
            key = f"{a['metric_id']}:{a['value']}"
            if key not in grouped:
                grouped[key] = a
                grouped[key]["methods"] = [a["method"]]
                grouped[key]["severity_scores"] = [{"method": a["method"], "severity": a["severity"]}]
            else:
                if a["method"] not in grouped[key]["methods"]:
                    grouped[key]["methods"].append(a["method"])
                    grouped[key]["severity_scores"].append({"method": a["method"], "severity": a["severity"]})

        result = list(grouped.values())
        for r in result:
            severities = [s["severity"] for s in r.get("severity_scores", [])]
            if AnomalySeverity.HIGH.value in severities:
                r["severity"] = AnomalySeverity.HIGH.value
            elif AnomalySeverity.MEDIUM.value in severities:
                r["severity"] = AnomalySeverity.MEDIUM.value
            else:
                r["severity"] = AnomalySeverity.LOW.value
        return result

    async def get_anomaly_events(self, metric_id: Optional[str] = None,
                                   severity: Optional[str] = None,
                                   limit: int = 100,
                                   since: Optional[str] = None) -> List[Dict[str, Any]]:
        events = list(reversed(self.anomaly_events))
        if metric_id:
            events = [e for e in events if e.get("metric_id") == metric_id]
        if severity:
            events = [e for e in events if e.get("severity") == severity]
        if since:
            events = [e for e in events if e.get("detected_at", "") >= since]
        return events[:limit]

    async def provide_feedback(self, anomaly_id: str, is_false_positive: bool,
                                 feedback: Optional[str] = None) -> bool:
        for event in self.anomaly_events:
            if event.get("id") == anomaly_id:
                event["feedback"] = {
                    "is_false_positive": is_false_positive,
                    "feedback": feedback,
                    "provided_at": self._now()
                }
                self._save_events()
                return True
        return False

    async def train_model(self, metric_id: str, model_type: str = "baseline",
                           training_data: Optional[List[float]] = None) -> Dict[str, Any]:
        values = training_data or list(self.metric_store.get(metric_id, []))
        if len(values) < 10:
            raise ValueError(f"Need at least 10 data points for {metric_id}, got {len(values)}")

        mean = statistics.mean(values)
        std = statistics.pstdev(values) or 1e-10
        sorted_vals = sorted(values)
        n = len(sorted_vals)

        model = {
            "id": self._generate_id(),
            "metric_id": metric_id,
            "model_type": model_type,
            "created_at": self._now(),
            "parameters": {
                "mean": mean,
                "std": std,
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
                "q1": sorted_vals[n // 4] if n >= 4 else mean,
                "q3": sorted_vals[3 * n // 4] if n >= 4 else mean,
                "n_samples": len(values),
                "seasonality_period": self.seasonality_period
            },
            "metrics": {
                "mean_absolute_deviation": statistics.mean([abs(v - mean) for v in values]),
                "coefficient_variation": std / mean if mean != 0 else 0,
                "skewness": self._calculate_skewness(values, mean, std)
            }
        }
        self.models[metric_id] = model
        self._save_models()
        return model

    def _calculate_skewness(self, values: List[float], mean: float, std: float) -> float:
        if std == 0 or len(values) < 3:
            return 0.0
        n = len(values)
        m3 = sum((v - mean) ** 3 for v in values) / n
        return m3 / (std ** 3) if std ** 3 != 0 else 0.0

    async def get_model(self, metric_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(metric_id)

    async def list_models(self) -> List[Dict[str, Any]]:
        return list(self.models.values())

    async def get_settings(self) -> Dict[str, Any]:
        return {
            "window_size": self.window_size,
            "seasonality_period": self.seasonality_period,
            "zscore_threshold": self.zscore_threshold,
            "mad_threshold": self.mad_threshold,
            "iqr_multiplier": self.iqr_multiplier,
            "adaptive_sensitivity": self.adaptive_sensitivity,
            "available_methods": [m.value for m in DetectionMethod],
            "stored_metrics": len(self.metric_store),
            "total_anomaly_events": len(self.anomaly_events),
            "trained_models": len(self.models)
        }

    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        if "window_size" in settings:
            self.window_size = settings["window_size"]
        if "seasonality_period" in settings:
            self.seasonality_period = settings["seasonality_period"]
        if "zscore_threshold" in settings:
            self.zscore_threshold = settings["zscore_threshold"]
        if "mad_threshold" in settings:
            self.mad_threshold = settings["mad_threshold"]
        if "iqr_multiplier" in settings:
            self.iqr_multiplier = settings["iqr_multiplier"]
        if "adaptive_sensitivity" in settings:
            self.adaptive_sensitivity = settings["adaptive_sensitivity"]
        return await self.get_settings()

    async def initialize(self):
        logger.info("TimeSeriesAnomalyDetector initialized with %d metrics, %d events",
                     len(self.metric_store), len(self.anomaly_events))

    async def close(self):
        self._save_metrics()
        self._save_events()
        self._save_models()
        logger.info("TimeSeriesAnomalyDetector closed")
