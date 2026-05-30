import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiohttp import web

from .engine import AnalyticsEngine, AnalyticsPipeline, DashboardBuilder, MetricsExporter

routes = web.RouteTableDef()
engine = AnalyticsEngine()
pipeline = AnalyticsPipeline(engine)
exporter = MetricsExporter(engine)


@routes.get("/api/v1/analytics/health")
async def analytics_health(request: web.Request) -> web.Response:
    health = await engine.health_check()
    return web.json_response(health)


@routes.post("/api/v1/analytics/metrics")
async def collect_metric(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    metric = body.get("metric")
    value = body.get("value")
    if not metric or value is None:
        return web.json_response({"error": "metric and value required"}, status=400)
    tags = body.get("tags", {})
    result = await engine.collect_metric(metric, float(value), tags=tags)
    return web.json_response({
        "status": "collected",
        "metric": result.metric,
        "value": result.value,
        "timestamp": result.timestamp.isoformat(),
    })


@routes.post("/api/v1/analytics/metrics/batch")
async def collect_batch(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    items = body.get("items", [])
    batch_items = []
    for item in items:
        metric = item.get("metric")
        value = item.get("value")
        if metric and value is not None:
            batch_items.append((metric, float(value), item.get("tags"), None))
    results = await engine.collect_batch(batch_items)
    return web.json_response({
        "status": "batch_collected",
        "count": len(results),
    })


@routes.get("/api/v1/analytics/metrics/{metric}")
async def get_metric(request: web.Request) -> web.Response:
    metric_name = request.match_info["metric"]
    since_str = request.query.get("since")
    since = datetime.fromisoformat(since_str) if since_str else None
    agg = engine.get_aggregated(metric_name, since=since)
    if not agg:
        return web.json_response({"error": "Metric not found"}, status=404)
    return web.json_response({
        "metric": agg.metric_name,
        "avg": agg.avg_value,
        "min": agg.min_value,
        "max": agg.max_value,
        "p95": agg.p95_value,
        "p99": agg.p99_value,
        "std_dev": agg.std_dev,
        "count": agg.count,
        "time_range": {
            "start": agg.time_range[0].isoformat(),
            "end": agg.time_range[1].isoformat(),
        },
    })


@routes.get("/api/v1/analytics/metrics/{metric}/trend")
async def get_trend(request: web.Request) -> web.Response:
    metric_name = request.match_info["metric"]
    window = int(request.query.get("window", 3600))
    points = engine.get_trend(metric_name, window=window)
    return web.json_response({
        "metric": metric_name,
        "points": [{"timestamp": p.timestamp.isoformat(), "value": p.value} for p in points],
    })


@routes.get("/api/v1/analytics/metrics/{metric}/forecast")
async def get_forecast(request: web.Request) -> web.Response:
    metric_name = request.match_info["metric"]
    horizon = int(request.query.get("horizon", 10))
    forecasts = engine.forecast(metric_name, horizon=horizon)
    return web.json_response({
        "metric": metric_name,
        "forecasts": [{"timestamp": p.timestamp.isoformat(), "value": p.value, "label": p.label} for p in forecasts],
    })


@routes.get("/api/v1/analytics/top")
async def get_top_metrics(request: web.Request) -> web.Response:
    prefix = request.query.get("prefix", "")
    n = int(request.query.get("n", 10))
    items = engine.get_top_metrics(prefix, n=n)
    return web.json_response({
        "prefix": prefix,
        "items": [{"metric": name, "value": val} for name, val in items],
    })


@routes.get("/api/v1/analytics/report")
async def get_report(request: web.Request) -> web.Response:
    metrics_filter = request.query.get("metrics")
    filter_list = metrics_filter.split(",") if metrics_filter else None
    report = engine.generate_report(metrics_filter=filter_list)
    return web.json_response(report)


@routes.get("/api/v1/analytics/export")
async def export_data(request: web.Request) -> web.Response:
    fmt = request.query.get("format", "json")
    metrics = request.query.get("metrics", "")
    metric_list = metrics.split(",") if metrics else []
    if fmt == "csv":
        csv_data = engine.export_csv(metric_list)
        return web.Response(text=csv_data, content_type="text/csv")
    elif fmt == "prometheus":
        prom_data = exporter.export_prometheus()
        return web.Response(text=prom_data, content_type="text/plain")
    elif fmt == "datadog":
        dd_data = exporter.export_datadog()
        return web.json_response(dd_data)
    else:
        json_data = exporter.export_json(metric_list)
        return web.Response(text=json_data, content_type="application/json")


@routes.post("/api/v1/analytics/anomalies/baseline")
async def set_baseline(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    metric = body.get("metric")
    mean = body.get("mean")
    std = body.get("std")
    if not metric or mean is None or std is None:
        return web.json_response({"error": "metric, mean, and std required"}, status=400)
    engine.anomaly_detector.set_baseline(metric, float(mean), float(std))
    return web.json_response({"status": "baseline_set", "metric": metric, "mean": mean, "std": std})


@routes.post("/api/v1/analytics/anomalies/threshold")
async def set_threshold(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    threshold = body.get("threshold", 3.0)
    engine.anomaly_detector.threshold = float(threshold)
    return web.json_response({"status": "threshold_set", "threshold": threshold})


@routes.get("/api/v1/analytics/sla")
async def compute_sla(request: web.Request) -> web.Response:
    metric = request.query.get("metric")
    threshold = float(request.query.get("threshold", 100))
    if not metric:
        return web.json_response({"error": "metric parameter required"}, status=400)
    sla = pipeline.compute_sla(metric, threshold)
    return web.json_response(sla)


@routes.get("/api/v1/analytics/correlate")
async def get_correlation(request: web.Request) -> web.Response:
    metric_a = request.query.get("metric_a")
    metric_b = request.query.get("metric_b")
    if not metric_a or not metric_b:
        return web.json_response({"error": "metric_a and metric_b required"}, status=400)
    corr = pipeline.correlation(metric_a, metric_b)
    return web.json_response({"metric_a": metric_a, "metric_b": metric_b, "correlation": corr})


@routes.post("/api/v1/analytics/process")
async def process_metric(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    metric = body.get("metric")
    value = body.get("value")
    if not metric or value is None:
        return web.json_response({"error": "metric and value required"}, status=400)
    tags = body.get("tags", {})
    result = await pipeline.process(metric, float(value), tags=tags)
    return web.json_response({
        "status": "processed",
        "metric": result.metric,
        "value": result.value,
        "timestamp": result.timestamp.isoformat(),
    })


@routes.get("/api/v1/analytics/dashboard/config")
async def dashboard_config(request: web.Request) -> web.Response:
    builder = DashboardBuilder(engine)
    builder.add_gauge("edge.cpu_usage", "CPU Usage", 0, 100, {"warning": 80, "critical": 95})
    builder.add_gauge("edge.memory_usage", "Memory Usage", 0, 100, {"warning": 85, "critical": 95})
    builder.add_timeseries("edge.network_throughput", "Network Throughput", window=3600)
    builder.add_timeseries("iot.temperature", "Temperature", window=3600)
    builder.add_table("iot.", "Top IoT Metrics", top_n=5)
    builder.add_table("edge.", "Top Edge Metrics", top_n=5)
    return web.json_response(builder.render_config())


@routes.get("/api/v1/analytics/dashboard/summary")
async def dashboard_summary(request: web.Request) -> web.Response:
    builder = DashboardBuilder(engine)
    builder.add_gauge("edge.cpu_usage", "CPU Usage", 0, 100)
    builder.add_gauge("edge.memory_usage", "Memory Usage", 0, 100)
    builder.add_timeseries("edge.network_throughput", "Network Throughput")
    builder.add_timeseries("iot.temperature", "Temperature")
    builder.add_table("iot.", "Top IoT Metrics")
    builder.add_table("green.", "Top Green Metrics")
    return web.json_response(builder.render_summary())


@routes.post("/api/v1/analytics/collectors/register")
async def register_collector(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    pattern = body.get("pattern")
    if not pattern:
        return web.json_response({"error": "pattern required"}, status=400)
    async def dynamic_collector():
        return {pattern: 0.0}
    engine.register_metric_route(pattern, dynamic_collector)
    return web.json_response({"status": "registered", "pattern": pattern})


@routes.get("/api/v1/analytics/start")
async def start_analytics(request: web.Request) -> web.Response:
    interval = int(request.query.get("interval", 60))
    engine.start(interval=interval)
    return web.json_response({"status": "started", "interval": interval})


@routes.get("/api/v1/analytics/stop")
async def stop_analytics(request: web.Request) -> web.Response:
    engine.stop()
    return web.json_response({"status": "stopped"})


@routes.post("/api/v1/analytics/alerts/callback")
async def register_alert_callback(request: web.Request) -> web.Response:
    return web.json_response({"status": "alert_callback_endpoint_registered"})


def setup_analytics_routes(app: web.Application):
    app.router.add_routes(routes)
    return engine, pipeline
