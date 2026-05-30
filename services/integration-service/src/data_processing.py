"""Data processing pipelines for Edge & IoT and Green Computing.

This module provides data transformation, aggregation, and reporting
pipelines that process telemetry data from edge devices and IoT sensors.
"""

import json
import logging
import time
import math
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Generator
from collections import defaultdict, deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProcessedReading:
    device_id: str
    timestamp: datetime
    raw_value: float
    scaled_value: float
    unit: str
    quality_score: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    metric_name: str
    device_id: str
    period_start: datetime
    period_end: datetime
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    std_dev: float
    sum_value: float


class DataNormalizer:
    """Normalizes raw sensor data to standardized units."""

    CONVERSIONS = {
        "celsius_to_fahrenheit": lambda c: c * 9/5 + 32,
        "fahrenheit_to_celsius": lambda f: (f - 32) * 5/9,
        "kpa_to_psi": lambda k: k * 0.145038,
        "psi_to_kpa": lambda p: p / 0.145038,
        "percent_to_decimal": lambda p: p / 100.0,
        "decimal_to_percent": lambda d: d * 100.0,
        "watts_to_kw": lambda w: w / 1000.0,
        "kw_to_watts": lambda kw: kw * 1000.0,
        "kwh_to_mwh": lambda k: k / 1000.0,
        "mwh_to_kwh": lambda m: m * 1000.0,
        "grams_to_kg": lambda g: g / 1000.0,
        "kg_to_tonnes": lambda k: k / 1000.0,
    }

    def __init__(self):
        self.conversion_cache: Dict[str, Any] = {}

    def normalize_temperature(self, value: float, from_unit: str = "celsius") -> ProcessedReading:
        if from_unit == "fahrenheit":
            celsius = self.CONVERSIONS["fahrenheit_to_celsius"](value)
        else:
            celsius = value
        return ProcessedReading(
            device_id="",
            timestamp=datetime.utcnow(),
            raw_value=value,
            scaled_value=round(celsius, 2),
            unit="celsius",
            quality_score=1.0
        )

    def normalize_power(self, value: float, from_unit: str = "watts") -> ProcessedReading:
        if from_unit == "watts":
            kw = self.CONVERSIONS["watts_to_kw"](value)
        else:
            kw = value
        return ProcessedReading(
            device_id="",
            timestamp=datetime.utcnow(),
            raw_value=value,
            scaled_value=round(kw, 4),
            unit="kw",
            quality_score=1.0
        )

    def normalize_energy(self, value: float, from_unit: str = "kwh") -> ProcessedReading:
        if from_unit == "kwh":
            scaled = value
        elif from_unit == "mwh":
            scaled = self.CONVERSIONS["mwh_to_kwh"](value)
        elif from_unit == "wh":
            scaled = value / 1000.0
        else:
            scaled = value
        return ProcessedReading(
            device_id="",
            timestamp=datetime.utcnow(),
            raw_value=value,
            scaled_value=round(scaled, 2),
            unit="kwh",
            quality_score=1.0
        )

    def normalize_co2(self, value: float, from_unit: str = "kg") -> ProcessedReading:
        if from_unit == "kg":
            scaled = value
        elif from_unit == "tonnes":
            scaled = self.CONVERSIONS["kg_to_tonnes"](value) * 1000
        elif from_unit == "grams":
            scaled = self.CONVERSIONS["grams_to_kg"](value)
        else:
            scaled = value
        return ProcessedReading(
            device_id="",
            timestamp=datetime.utcnow(),
            raw_value=value,
            scaled_value=round(scaled, 2),
            unit="kg",
            quality_score=1.0
        )


class MetricsAggregator:
    """Aggregates raw readings into time-bucketed metrics."""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.buckets: Dict[str, List[float]] = defaultdict(list)
        self.timestamps: Dict[str, List[datetime]] = defaultdict(list)

    def add_reading(self, device_id: str, value: float, timestamp: Optional[datetime] = None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        bucket_key = self._get_bucket_key(device_id, timestamp)
        self.buckets[bucket_key].append(value)
        self.timestamps[bucket_key].append(timestamp)

    def _get_bucket_key(self, device_id: str, timestamp: datetime) -> str:
        bucket_minutes = (timestamp.minute // self.window_minutes) * self.window_minutes
        bucket_time = timestamp.replace(minute=bucket_minutes, second=0, microsecond=0)
        return f"{device_id}:{bucket_time.isoformat()}"

    def get_aggregated_metric(self, device_id: str, period_start: datetime, period_end: datetime) -> Optional[AggregatedMetric]:
        relevant_values = []
        for bucket_key, values in self.buckets.items():
            if bucket_key.startswith(device_id):
                relevant_values.extend(values)
        if not relevant_values:
            return None
        sorted_vals = sorted(relevant_values)
        n = len(sorted_vals)
        p95_idx = min(int(n * 0.95), n - 1)
        return AggregatedMetric(
            metric_name="aggregated",
            device_id=device_id,
            period_start=period_start,
            period_end=period_end,
            count=n,
            min_value=min(sorted_vals),
            max_value=max(sorted_vals),
            avg_value=statistics.mean(sorted_vals),
            median_value=statistics.median(sorted_vals),
            p95_value=sorted_vals[p95_idx],
            std_dev=statistics.stdev(sorted_vals) if n > 1 else 0,
            sum_value=sum(sorted_vals)
        )

    def clear_old_data(self, retention_hours: int = 24):
        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        keys_to_delete = []
        for bucket_key, timestamps in self.timestamps.items():
            if all(t < cutoff for t in timestamps):
                keys_to_delete.append(bucket_key)
        for key in keys_to_delete:
            self.buckets.pop(key, None)
            self.timestamps.pop(key, None)


class AnomalyDetector:
    """Detects anomalies in time-series data streams."""

    def __init__(self, z_score_threshold: float = 3.0):
        self.z_score_threshold = z_score_threshold
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.anomalies: List[Dict[str, Any]] = []

    def check_value(self, device_id: str, value: float, metric: str = "default") -> Dict[str, Any]:
        self.history[device_id].append(value)
        if len(self.history[device_id]) > 1000:
            self.history[device_id] = self.history[device_id][-1000:]
        if len(self.history[device_id]) < 10:
            return {"is_anomaly": False, "reason": "insufficient_data"}
        recent = self.history[device_id][-50:]
        mean = statistics.mean(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else 1.0
        z_score = abs(value - mean) / stdev if stdev > 0 else 0
        is_anomaly = z_score > self.z_score_threshold
        result = {
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 2),
            "value": value,
            "mean": round(mean, 2),
            "std_dev": round(stdev, 2),
            "metric": metric,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        if is_anomaly:
            self.anomalies.append(result)
            logger.warning(f"Anomaly detected: device={device_id} metric={metric} value={value} z={z_score:.2f}")
        return result

    def get_recent_anomalies(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.anomalies[-limit:]

    def clear_anomalies(self):
        self.anomalies.clear()


class DataEnricher:
    """Enriches raw data with additional context and metadata."""

    def __init__(self):
        self.device_registry: Dict[str, Dict[str, Any]] = {}

    def register_device_metadata(self, device_id: str, metadata: Dict[str, Any]):
        self.device_registry[device_id] = metadata

    def enrich(self, device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        metadata = self.device_registry.get(device_id, {})
        enriched = dict(payload)
        enriched["_enriched_at"] = datetime.utcnow().isoformat()
        enriched["_device_id"] = device_id
        if metadata:
            enriched["_device_type"] = metadata.get("type", "unknown")
            enriched["_device_location"] = metadata.get("location", "unknown")
            enriched["_device_firmware"] = metadata.get("firmware", "unknown")
        enriched["_ingestion_timestamp"] = datetime.utcnow().isoformat()
        enriched["_data_version"] = "2.0"
        enriched["_pipeline_stage"] = "enrichment"
        return enriched


class DataValidator:
    """Validates incoming data against defined schemas."""

    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def register_schema(self, data_type: str, schema: Dict[str, Any]):
        self.schemas[data_type] = schema

    def validate(self, data_type: str, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        schema = self.schemas.get(data_type)
        if not schema:
            return True, []
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        field_types = schema.get("types", {})
        for field, expected_type in field_types.items():
            if field in payload:
                value = payload[field]
                if expected_type == "number":
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field {field} must be a number")
                elif expected_type == "string":
                    if not isinstance(value, str):
                        errors.append(f"Field {field} must be a string")
                elif expected_type == "boolean":
                    if not isinstance(value, bool):
                        errors.append(f"Field {field} must be a boolean")
                elif expected_type == "array":
                    if not isinstance(value, list):
                        errors.append(f"Field {field} must be an array")
        field_ranges = schema.get("ranges", {})
        for field, (min_val, max_val) in field_ranges.items():
            if field in payload and isinstance(payload[field], (int, float)):
                if payload[field] < min_val or payload[field] > max_val:
                    errors.append(f"Field {field} out of range [{min_val}, {max_val}]")
        return len(errors) == 0, errors


class StreamProcessor:
    """Processes streaming data from edge devices in real-time."""

    def __init__(self):
        self.normalizer = DataNormalizer()
        self.aggregator = MetricsAggregator()
        self.anomaly_detector = AnomalyDetector()
        self.enricher = DataEnricher()
        self.validator = DataValidator()
        self.processed_count = 0
        self.error_count = 0

    def process_telemetry(self, device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            valid, errors = self.validator.validate("telemetry", payload)
            if not valid:
                self.error_count += 1
                return {"success": False, "errors": errors}
            enriched = self.enricher.enrich(device_id, payload)
            results = {"success": True, "enriched": enriched, "normalized": {}, "anomalies": []}
            if "temperature" in payload:
                normalized = self.normalizer.normalize_temperature(payload["temperature"])
                self.aggregator.add_reading(device_id, normalized.scaled_value)
                anomaly = self.anomaly_detector.check_value(device_id, normalized.scaled_value, "temperature")
                results["normalized"]["temperature"] = normalized.__dict__
                if anomaly["is_anomaly"]:
                    results["anomalies"].append(anomaly)
            if "power_watts" in payload:
                normalized = self.normalizer.normalize_power(payload["power_watts"])
                self.aggregator.add_reading(f"{device_id}:power", normalized.scaled_value)
                results["normalized"]["power_kw"] = normalized.__dict__
            if "energy_kwh" in payload:
                normalized = self.normalizer.normalize_energy(payload["energy_kwh"])
                self.aggregator.add_reading(f"{device_id}:energy", normalized.scaled_value)
                results["normalized"]["energy_kwh"] = normalized.__dict__
            self.processed_count += 1
            return results
        except Exception as e:
            self.error_count += 1
            logger.error(f"Stream processing error for {device_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "processed": self.processed_count,
            "errors": self.error_count,
            "anomalies_detected": len(self.anomaly_detector.anomalies),
            "uptime_seconds": 0
        }


class ReportGenerator:
    """Generates reports from aggregated metrics."""

    def __init__(self):
        self.report_templates: Dict[str, str] = {}

    def generate_energy_report(self, metrics: Dict[str, Any], period_days: int = 30) -> Dict[str, Any]:
        return {
            "report_type": "energy_consumption",
            "period_days": period_days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_kwh": metrics.get("total_kwh", 0),
                "avg_daily_kwh": metrics.get("total_kwh", 0) / max(period_days, 1),
                "peak_kw": metrics.get("peak_kw", 0),
                "avg_kw": metrics.get("avg_kw", 0),
                "total_cost": metrics.get("total_kwh", 0) * 0.12,
                "renewable_pct": metrics.get("renewable_pct", 0),
            },
            "breakdown": {
                "computing": metrics.get("total_kwh", 0) * 0.45,
                "cooling": metrics.get("total_kwh", 0) * 0.30,
                "networking": metrics.get("total_kwh", 0) * 0.15,
                "other": metrics.get("total_kwh", 0) * 0.10,
            },
            "trends": {
                "vs_last_period_pct": -5.2,
                "projected_next_period_kwh": metrics.get("total_kwh", 0) * 1.03,
            }
        }

    def generate_carbon_report(self, total_kwh: float, carbon_intensity: float = 0.294) -> Dict[str, Any]:
        total_co2 = total_kwh * carbon_intensity
        return {
            "report_type": "carbon_footprint",
            "generated_at": datetime.utcnow().isoformat(),
            "total_kwh": total_kwh,
            "carbon_intensity_g_per_kwh": carbon_intensity * 1000,
            "total_co2_kg": round(total_co2, 2),
            "total_co2_tonnes": round(total_co2 / 1000, 4),
            "equivalents": {
                "trees_needed": round(total_co2 / 21.7),
                "cars_equivalent": round(total_co2 / 4600, 1),
                "homes_energy": round(total_co2 / 7260, 1),
            },
            "recommendations": [
                {"action": "Increase renewable energy mix", "potential_reduction_pct": 35},
                {"action": "Optimize cooling efficiency", "potential_reduction_pct": 15},
                {"action": "Consolidate idle workloads", "potential_reduction_pct": 10},
            ]
        }

    def generate_pue_report(self, facilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        pue_values = [f.get("pue", 1.5) for f in facilities]
        avg_pue = statistics.mean(pue_values) if pue_values else 1.5
        best_pue = min(pue_values) if pue_values else 1.0
        return {
            "report_type": "pue_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "average_pue": round(avg_pue, 2),
            "best_pue": round(best_pue, 2),
            "facility_count": len(facilities),
            "efficiency_score": round((1.0 / avg_pue) * 100, 1),
            "potential_savings_kwh": self._estimate_pue_savings(avg_pue, facilities),
            "recommendations": [
                "Upgrade to hot/cold aisle containment",
                "Implement variable speed cooling fans",
                "Increase operating temperature setpoint",
                "Install blanking panels in empty rack slots",
            ]
        }

    def _estimate_pue_savings(self, current_pue: float, facilities: List[Dict[str, Any]]) -> float:
        target_pue = 1.15
        if current_pue <= target_pue:
            return 0
        total_it_load = sum(f.get("it_load_kw", 100) for f in facilities)
        improvement = current_pue - target_pue
        savings_kw = total_it_load * improvement
        return round(savings_kw * 8760 * 0.5)

    def generate_compliance_report(self, checklist: Dict[str, bool]) -> Dict[str, Any]:
        total = len(checklist)
        passed = sum(1 for v in checklist.values() if v)
        return {
            "report_type": "compliance_checklist",
            "generated_at": datetime.utcnow().isoformat(),
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "compliance_pct": round((passed / total) * 100, 1) if total > 0 else 0,
            "details": checklist
        }
