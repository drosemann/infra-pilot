import asyncio
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AnalyticsResult:
    timestamp: datetime
    metric: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    dimensions: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: float
    label: Optional[str] = None


@dataclass
class AggregatedMetric:
    metric_name: str
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    std_dev: float
    count: int
    time_range: Tuple[datetime, datetime]


class DataAggregator:
    def __init__(self, window_size: int = 3600):
        self.window_size = window_size
        self._data_buckets: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)

    def add_point(self, metric: str, value: float, timestamp: Optional[datetime] = None, label: Optional[str] = None):
        ts = timestamp or datetime.utcnow()
        self._data_buckets[metric].append(TimeSeriesPoint(timestamp=ts, value=value, label=label))
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_size)
        self._data_buckets[metric] = [p for p in self._data_buckets[metric] if p.timestamp >= cutoff]

    def aggregate(self, metric: str, since: Optional[datetime] = None) -> Optional[AggregatedMetric]:
        points = self._data_buckets.get(metric, [])
        if since:
            points = [p for p in points if p.timestamp >= since]
        if not points:
            return None
        values = [p.value for p in points]
        sorted_v = sorted(values)
        n = len(sorted_v)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        return AggregatedMetric(
            metric_name=metric,
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=statistics.median(values) if n > 1 else values[0],
            p95_value=sorted_v[p95_idx] if p95_idx < n else sorted_v[-1],
            p99_value=sorted_v[p99_idx] if p99_idx < n else sorted_v[-1],
            std_dev=statistics.stdev(values) if n > 1 else 0.0,
            count=n,
            time_range=(points[0].timestamp, points[-1].timestamp),
        )

    def trend(self, metric: str, window: int = 300) -> List[TimeSeriesPoint]:
        points = self._data_buckets.get(metric, [])
        if not points:
            return []
        bucketed: Dict[str, List[float]] = defaultdict(list)
        for p in points:
            bucket_key = p.timestamp.strftime("%Y-%m-%dT%H:%M")
            if window >= 86400:
                bucket_key = p.timestamp.strftime("%Y-%m-%d")
            elif window >= 3600:
                bucket_key = p.timestamp.strftime("%Y-%m-%dT%H:00")
            elif window >= 60:
                bucket_key = p.timestamp.strftime("%Y-%m-%dT%H:%M")
            bucketed[bucket_key].append(p.value)
        result = []
        for bucket_key, vals in sorted(bucketed.items()):
            result.append(TimeSeriesPoint(
                timestamp=datetime.strptime(bucket_key, "%Y-%m-%dT%H:%M") if ":" in bucket_key else datetime.strptime(bucket_key, "%Y-%m-%d"),
                value=statistics.mean(vals),
            ))
        return result

    def top_n(self, metric_prefix: str, n: int = 10) -> List[Tuple[str, float]]:
        candidates = []
        for metric, points in self._data_buckets.items():
            if metric.startswith(metric_prefix) and points:
                avg_val = statistics.mean([p.value for p in points])
                candidates.append((metric, avg_val))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:n]


class AnomalyDetector:
    def __init__(self, std_dev_threshold: float = 3.0):
        self.threshold = std_dev_threshold
        self._baselines: Dict[str, Tuple[float, float]] = {}

    def set_baseline(self, metric: str, mean: float, std: float):
        self._baselines[metric] = (mean, std)

    def detect(self, metric: str, value: float) -> Optional[Dict[str, Any]]:
        if metric not in self._baselines:
            return None
        mean, std = self._baselines[metric]
        if std == 0:
            return None
        z_score = abs(value - mean) / std
        if z_score > self.threshold:
            return {
                "metric": metric,
                "value": value,
                "z_score": round(z_score, 2),
                "threshold": self.threshold,
                "severity": "critical" if z_score > self.threshold * 1.5 else "warning",
                "mean": round(mean, 2),
                "std": round(std, 2),
            }
        return None


class PredictiveAnalytics:
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}

    def linear_regression(self, points: List[TimeSeriesPoint], forecast_horizon: int = 10) -> List[TimeSeriesPoint]:
        if len(points) < 2:
            return []
        n = len(points)
        x_vals = list(range(n))
        y_vals = [p.value for p in points]
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(y_vals)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        last_ts = points[-1].timestamp
        interval = (last_ts - points[0].timestamp) / n if n > 1 else timedelta(minutes=5)
        forecasts = []
        for i in range(1, forecast_horizon + 1):
            x_pred = n + i - 1
            y_pred = slope * x_pred + intercept
            forecasts.append(TimeSeriesPoint(
                timestamp=last_ts + interval * i,
                value=round(y_pred, 2),
                label="forecast",
            ))
        return forecasts

    def moving_average(self, points: List[TimeSeriesPoint], window: int = 5) -> List[TimeSeriesPoint]:
        if len(points) < window:
            return []
        result = []
        for i in range(len(points) - window + 1):
            window_vals = [points[j].value for j in range(i, i + window)]
            result.append(TimeSeriesPoint(
                timestamp=points[i + window - 1].timestamp,
                value=round(statistics.mean(window_vals), 2),
                label="sma",
            ))
        return result

    def exponential_smoothing(self, points: List[TimeSeriesPoint], alpha: float = 0.3) -> List[TimeSeriesPoint]:
        if not points:
            return []
        result = [TimeSeriesPoint(timestamp=points[0].timestamp, value=points[0].value, label="ses")]
        for i in range(1, len(points)):
            smoothed = alpha * points[i].value + (1 - alpha) * result[-1].value
            result.append(TimeSeriesPoint(timestamp=points[i].timestamp, value=round(smoothed, 2), label="ses"))
        return result


class ReportGenerator:
    def __init__(self):
        self._templates: Dict[str, str] = {}

    def register_template(self, name: str, template: str):
        self._templates[name] = template

    def generate_summary(self, metrics: Dict[str, AggregatedMetric],
                         time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "time_range": {
                "start": time_range[0].isoformat(),
                "end": time_range[1].isoformat(),
            },
            "metrics_summary": {},
            "overall_status": "healthy",
            "alerts": [],
        }
        for mname, metric in metrics.items():
            report["metrics_summary"][mname] = {
                "avg": metric.avg_value,
                "max": metric.max_value,
                "min": metric.min_value,
                "p95": metric.p95_value,
                "p99": metric.p99_value,
                "samples": metric.count,
            }
            if metric.p95_value > metric.avg_value * 1.5:
                report["alerts"].append(f"High variance detected in {mname}: p95={metric.p95_value:.2f}, avg={metric.avg_value:.2f}")
                report["overall_status"] = "degraded"
        return report

    def generate_csv(self, points: Dict[str, List[TimeSeriesPoint]]) -> str:
        all_timestamps = set()
        metric_keys = list(points.keys())
        for metric, pts in points.items():
            for p in pts:
                all_timestamps.add(p.timestamp.isoformat())
        sorted_ts = sorted(all_timestamps)
        lines = ["timestamp," + ",".join(metric_keys)]
        ts_to_vals: Dict[str, Dict[str, float]] = defaultdict(dict)
        for metric, pts in points.items():
            for p in pts:
                ts_str = p.timestamp.isoformat()
                ts_to_vals[ts_str][metric] = p.value
        for ts in sorted_ts:
            row = [ts]
            for metric in metric_keys:
                row.append(str(ts_to_vals[ts].get(metric, "")))
            lines.append(",".join(row))
        return "\n".join(lines)

    def generate_html_dashboard(self, metrics: Dict[str, AggregatedMetric]) -> str:
        rows_html = ""
        for mname, metric in metrics.items():
            rows_html += f"""
            <tr>
                <td>{mname}</td>
                <td>{metric.avg_value:.2f}</td>
                <td>{metric.min_value:.2f}</td>
                <td>{metric.max_value:.2f}</td>
                <td>{metric.p95_value:.2f}</td>
                <td>{metric.p99_value:.2f}</td>
                <td>{metric.count}</td>
            </tr>"""
        return f"""<!DOCTYPE html>
<html><head><title>Infra-pilot Analytics Dashboard</title>
<style>
body {{ font-family: Arial; margin: 20px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #4CAF50; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
h1 {{ color: #333; }}
</style></head><body>
<h1>Infra-pilot Analytics Dashboard</h1>
<p>Generated: {datetime.utcnow().isoformat()}</p>
<table>
<tr><th>Metric</th><th>Avg</th><th>Min</th><th>Max</th><th>P95</th><th>P99</th><th>Count</th></tr>
{rows_html}
</table></body></html>"""


class AnalyticsEngine:
    def __init__(self):
        self.aggregator = DataAggregator()
        self.anomaly_detector = AnomalyDetector()
        self.predictive = PredictiveAnalytics()
        self.reporter = ReportGenerator()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._alert_callbacks: List[callable] = []
        self._metric_routes: Dict[str, callable] = {}

    def register_alert_callback(self, cb: callable):
        self._alert_callbacks.append(cb)

    def register_metric_route(self, metric_pattern: str, collector: callable):
        self._metric_routes[metric_pattern] = collector

    async def collect_metric(self, metric: str, value: float, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        self.aggregator.add_point(metric, value, timestamp=timestamp)
        anomaly = self.anomaly_detector.detect(metric, value)
        if anomaly:
            for cb in self._alert_callbacks:
                try:
                    await cb(anomaly)
                except Exception:
                    pass
            return AnalyticsResult(
                timestamp=timestamp or datetime.utcnow(),
                metric=metric,
                value=value,
                tags=tags or {},
                dimensions={"anomaly": anomaly["severity"]},
            )
        return AnalyticsResult(
            timestamp=timestamp or datetime.utcnow(),
            metric=metric,
            value=value,
            tags=tags or {},
        )

    async def collect_batch(self, items: List[Tuple[str, float, Optional[Dict[str, str]], Optional[datetime]]]):
        results = []
        for metric, value, tags, timestamp in items:
            result = await self.collect_metric(metric, value, tags, timestamp)
            results.append(result)
        return results

    async def run_metric_collectors(self, interval: int = 60):
        while self._running:
            for pattern, collector in self._metric_routes.items():
                try:
                    if asyncio.iscoroutinefunction(collector):
                        result = await collector()
                    else:
                        result = collector()
                    if isinstance(result, list):
                        for metric, value in result:
                            await self.collect_metric(metric, value)
                    elif isinstance(result, dict):
                        for metric, value in result.items():
                            await self.collect_metric(metric, value)
                except Exception as e:
                    await self.collect_metric(f"collector.error.{pattern}", 1, tags={"error": str(e)})
            await asyncio.sleep(interval)

    def start(self, interval: int = 60):
        self._running = True
        task = asyncio.create_task(self.run_metric_collectors(interval))
        self._tasks.append(task)

    def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    def get_aggregated(self, metric: str, since: Optional[datetime] = None) -> Optional[AggregatedMetric]:
        return self.aggregator.aggregate(metric, since=since)

    def get_trend(self, metric: str, window: int = 300) -> List[TimeSeriesPoint]:
        return self.aggregator.trend(metric, window=window)

    def forecast(self, metric: str, horizon: int = 10) -> List[TimeSeriesPoint]:
        points = self.aggregator._data_buckets.get(metric, [])
        return self.predictive.linear_regression(points, forecast_horizon=horizon)

    def get_top_metrics(self, prefix: str, n: int = 10) -> List[Tuple[str, float]]:
        return self.aggregator.top_n(prefix, n=n)

    def generate_report(self, metrics_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        all_metrics: Dict[str, AggregatedMetric] = {}
        now = datetime.utcnow()
        for metric in list(self.aggregator._data_buckets.keys()):
            if metrics_filter and metric not in metrics_filter:
                continue
            agg = self.aggregator.aggregate(metric, since=now - timedelta(hours=24))
            if agg:
                all_metrics[metric] = agg
        return self.reporter.generate_summary(all_metrics, (now - timedelta(hours=24), now))

    def export_csv(self, metrics: List[str]) -> str:
        points: Dict[str, List[TimeSeriesPoint]] = {}
        for metric in metrics:
            data = self.aggregator._data_buckets.get(metric, [])
            if data:
                points[metric] = data
        return self.reporter.generate_csv(points)

    def export_html(self) -> str:
        all_metrics: Dict[str, AggregatedMetric] = {}
        now = datetime.utcnow()
        for metric in list(self.aggregator._data_buckets.keys()):
            agg = self.aggregator.aggregate(metric, since=now - timedelta(hours=24))
            if agg:
                all_metrics[metric] = agg
        return self.reporter.generate_html_dashboard(all_metrics)

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "stopped",
            "metrics_tracked": len(self.aggregator._data_buckets),
            "total_data_points": sum(len(v) for v in self.aggregator._data_buckets.values()),
            "alert_callbacks": len(self._alert_callbacks),
            "metric_collectors": len(self._metric_routes),
            "uptime": None,
        }


class AnalyticsPipeline:
    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
        self._processors: List[callable] = []
        self._outputs: List[callable] = []

    def add_processor(self, processor: callable):
        self._processors.append(processor)

    def add_output(self, output: callable):
        self._outputs.append(output)

    async def process(self, metric: str, value: float, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        result = await self.engine.collect_metric(metric, value, tags, timestamp)
        for processor in self._processors:
            try:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(result)
                else:
                    result = processor(result)
            except Exception:
                pass
        for output in self._outputs:
            try:
                if asyncio.iscoroutinefunction(output):
                    await output(result)
                else:
                    output(result)
            except Exception:
                pass
        return result

    def compute_sla(self, metric: str, threshold: float, since: Optional[datetime] = None) -> Dict[str, Any]:
        agg = self.engine.aggregator.aggregate(metric, since=since)
        if not agg:
            return {"sla_compliance": 1.0, "breaches": 0, "total": 0}
        points = [p for p in self.engine.aggregator._data_buckets.get(metric, []) if not since or p.timestamp >= since]
        total = len(points)
        breaches = sum(1 for p in points if p.value > threshold)
        return {
            "sla_compliance": round((total - breaches) / total, 4) if total > 0 else 1.0,
            "breaches": breaches,
            "total": total,
            "threshold": threshold,
        }

    def correlation(self, metric_a: str, metric_b: str, since: Optional[datetime] = None) -> float:
        points_a = self.engine.aggregator._data_buckets.get(metric_a, [])
        points_b = self.engine.aggregator._data_buckets.get(metric_b, [])
        if since:
            points_a = [p for p in points_a if p.timestamp >= since]
            points_b = [p for p in points_b if p.timestamp >= since]
        ts_to_a = {p.timestamp: p.value for p in points_a}
        ts_to_b = {p.timestamp: p.value for p in points_b}
        common_ts = sorted(set(ts_to_a.keys()) & set(ts_to_b.keys()))
        if len(common_ts) < 2:
            return 0.0
        vals_a = [ts_to_a[ts] for ts in common_ts]
        vals_b = [ts_to_b[ts] for ts in common_ts]
        n = len(vals_a)
        mean_a = statistics.mean(vals_a)
        mean_b = statistics.mean(vals_b)
        cov = sum((vals_a[i] - mean_a) * (vals_b[i] - mean_b) for i in range(n)) / n
        std_a = statistics.stdev(vals_a) if n > 1 else 1
        std_b = statistics.stdev(vals_b) if n > 1 else 1
        if std_a == 0 or std_b == 0:
            return 0.0
        return round(cov / (std_a * std_b), 4)


class DashboardBuilder:
    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
        self._widgets: List[Dict[str, Any]] = []

    def add_widget(self, widget_type: str, metric: str, title: str, config: Optional[Dict[str, Any]] = None):
        self._widgets.append({
            "type": widget_type,
            "metric": metric,
            "title": title,
            "config": config or {},
        })

    def add_gauge(self, metric: str, title: str, min_val: float = 0, max_val: float = 100, thresholds: Optional[Dict[str, float]] = None):
        self.add_widget("gauge", metric, title, {"min": min_val, "max": max_val, "thresholds": thresholds or {}})

    def add_timeseries(self, metric: str, title: str, window: int = 3600):
        self.add_widget("timeseries", metric, title, {"window": window})

    def add_table(self, metric_prefix: str, title: str, top_n: int = 10):
        self.add_widget("table", metric_prefix, title, {"top_n": top_n})

    def add_heatmap(self, metric: str, title: str):
        self.add_widget("heatmap", metric, title, {})

    def render_config(self) -> Dict[str, Any]:
        return {
            "dashboard": {
                "widgets": self._widgets,
                "refresh_interval": 30,
                "auto_refresh": True,
            }
        }

    def render_summary(self) -> Dict[str, Any]:
        summary = {
            "widgets": [],
            "generated_at": datetime.utcnow().isoformat(),
        }
        for widget in self._widgets:
            widget_data = {**widget}
            if widget["type"] == "gauge":
                agg = self.engine.aggregator.aggregate(widget["metric"])
                if agg:
                    widget_data["current_value"] = agg.avg_value
                    pct = (agg.avg_value - widget["config"].get("min", 0)) / (widget["config"].get("max", 100) - widget["config"].get("min", 0)) * 100
                    widget_data["percentage"] = round(max(0, min(100, pct)), 1)
            elif widget["type"] == "timeseries":
                widget_data["points"] = [
                    {"timestamp": p.timestamp.isoformat(), "value": p.value}
                    for p in self.engine.aggregator.trend(widget["metric"], window=widget["config"].get("window", 3600))
                ]
            elif widget["type"] == "table":
                widget_data["items"] = [
                    {"name": name, "value": val}
                    for name, val in self.engine.aggregator.top_n(widget["metric"], n=widget["config"].get("top_n", 10))
                ]
            summary["widgets"].append(widget_data)
        return summary


class MetricsExporter:
    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine

    def export_prometheus(self) -> str:
        lines = []
        now = datetime.utcnow().timestamp()
        for metric, points in self.engine.aggregator._data_buckets.items():
            safe_name = metric.replace(".", "_").replace("-", "_")
            for point in points[-10:]:
                lines.append(f"# HELP {safe_name} {metric}")
                lines.append(f"# TYPE {safe_name} gauge")
                lines.append(f"{safe_name} {point.value} {int(now)}")
        return "\n".join(lines)

    def export_json(self, metrics_filter: Optional[List[str]] = None) -> str:
        data = {}
        for metric, points in self.engine.aggregator._data_buckets.items():
            if metrics_filter and metric not in metrics_filter:
                continue
            data[metric] = [
                {"timestamp": p.timestamp.isoformat(), "value": p.value, "label": p.label}
                for p in points
            ]
        return json.dumps(data, indent=2, default=str)

    def export_datadog(self) -> List[Dict[str, Any]]:
        series = []
        for metric, points in self.engine.aggregator._data_buckets.items():
            for point in points[-20:]:
                series.append({
                    "metric": metric,
                    "points": [{"timestamp": int(point.timestamp.timestamp()), "value": point.value}],
                    "type": "gauge",
                    "tags": [f"label:{point.label}"] if point.label else [],
                })
        return {"series": series}
