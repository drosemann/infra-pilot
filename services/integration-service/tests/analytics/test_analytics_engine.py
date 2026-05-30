import pytest
import asyncio
from datetime import datetime, timedelta
from services.integration_service.src.analytics.engine import (
    AnalyticsEngine, AnalyticsPipeline, DataAggregator, AnomalyDetector,
    PredictiveAnalytics, ReportGenerator, MetricsExporter, DashboardBuilder,
    AggregatedMetric, TimeSeriesPoint,
)


class TestDataAggregator:
    def test_add_and_aggregate(self):
        agg = DataAggregator(window_size=3600)
        agg.add_point("test.metric", 10.0)
        agg.add_point("test.metric", 20.0)
        agg.add_point("test.metric", 30.0)
        result = agg.aggregate("test.metric")
        assert result is not None
        assert result.avg_value == 20.0
        assert result.min_value == 10.0
        assert result.max_value == 30.0
        assert result.count == 3

    def test_aggregate_empty(self):
        agg = DataAggregator()
        result = agg.aggregate("nonexistent")
        assert result is None

    def test_aggregate_single_point(self):
        agg = DataAggregator()
        agg.add_point("single", 42.0)
        result = agg.aggregate("single")
        assert result is not None
        assert result.avg_value == 42.0
        assert result.median_value == 42.0
        assert result.std_dev == 0.0

    def test_aggregate_with_time_filter(self):
        agg = DataAggregator(window_size=3600)
        old = datetime.utcnow() - timedelta(hours=2)
        agg.add_point("test.metric", 10.0, timestamp=old)
        agg.add_point("test.metric", 20.0)
        recent = datetime.utcnow() - timedelta(minutes=30)
        result = agg.aggregate("test.metric", since=recent)
        assert result is not None
        assert result.count == 1
        assert result.avg_value == 20.0

    def test_window_pruning(self):
        agg = DataAggregator(window_size=60)
        agg.add_point("test.metric", 100.0)
        assert len(agg._data_buckets["test.metric"]) == 1
        old = datetime.utcnow() - timedelta(seconds=120)
        agg.add_point("test.metric", 200.0, timestamp=old)
        agg.add_point("test.metric", 300.0)
        assert len(agg._data_buckets["test.metric"]) == 2

    def test_trend_daily(self):
        agg = DataAggregator(window_size=86400 * 7)
        for i in range(7):
            ts = datetime.utcnow() - timedelta(days=i)
            agg.add_point("daily.metric", float(i * 10), timestamp=ts)
        trend = agg.trend("daily.metric", window=86400)
        assert len(trend) >= 1

    def test_trend_no_data(self):
        agg = DataAggregator()
        assert agg.trend("nonexistent") == []

    def test_top_n(self):
        agg = DataAggregator()
        for i in range(20):
            agg.add_point(f"test.metric.{i}", float(i * 5))
        top = agg.top_n("test.metric", n=5)
        assert len(top) == 5
        assert top[0][1] >= top[-1][1]

    def test_top_n_empty_prefix(self):
        agg = DataAggregator()
        assert agg.top_n("nonexistent") == []

    def test_multiple_metrics(self):
        agg = DataAggregator()
        agg.add_point("cpu", 50.0)
        agg.add_point("memory", 70.0)
        agg.add_point("disk", 80.0)
        assert agg.aggregate("cpu") is not None
        assert agg.aggregate("memory") is not None
        assert agg.aggregate("disk") is not None


class TestAnomalyDetector:
    def test_detect_anomaly(self):
        detector = AnomalyDetector(std_dev_threshold=2.0)
        detector.set_baseline("test.metric", 100.0, 10.0)
        result = detector.detect("test.metric", 1000.0)
        assert result is not None
        assert result["severity"] == "critical"
        assert result["z_score"] > 2.0

    def test_no_anomaly(self):
        detector = AnomalyDetector()
        detector.set_baseline("test.metric", 100.0, 10.0)
        result = detector.detect("test.metric", 105.0)
        assert result is None

    def test_no_baseline(self):
        detector = AnomalyDetector()
        result = detector.detect("unknown", 50.0)
        assert result is None

    def test_zero_std(self):
        detector = AnomalyDetector()
        detector.set_baseline("test.metric", 100.0, 0.0)
        result = detector.detect("test.metric", 200.0)
        assert result is None

    def test_warning_vs_critical(self):
        detector = AnomalyDetector(std_dev_threshold=2.0)
        detector.set_baseline("test.metric", 100.0, 10.0)
        warning_val = 100.0 + 2.5 * 10.0
        result = detector.detect("test.metric", warning_val)
        assert result is not None
        assert result["severity"] == "warning"


class TestPredictiveAnalytics:
    def test_linear_regression(self):
        pa = PredictiveAnalytics()
        points = [TimeSeriesPoint(timestamp=datetime.utcnow() - timedelta(hours=i), value=float(i * 10)) for i in range(10, 0, -1)]
        forecasts = pa.linear_regression(points, forecast_horizon=5)
        assert len(forecasts) == 5
        assert forecasts[0].value > 0

    def test_linear_regression_insufficient_data(self):
        pa = PredictiveAnalytics()
        points = [TimeSeriesPoint(timestamp=datetime.utcnow(), value=10.0)]
        assert pa.linear_regression(points) == []

    def test_moving_average(self):
        pa = PredictiveAnalytics()
        points = [TimeSeriesPoint(timestamp=datetime.utcnow() + timedelta(minutes=i), value=float(i)) for i in range(10)]
        sma = pa.moving_average(points, window=3)
        assert len(sma) == 8

    def test_moving_average_insufficient(self):
        pa = PredictiveAnalytics()
        points = [TimeSeriesPoint(timestamp=datetime.utcnow(), value=1.0)]
        assert pa.moving_average(points, window=5) == []

    def test_exponential_smoothing(self):
        pa = PredictiveAnalytics()
        points = [TimeSeriesPoint(timestamp=datetime.utcnow() + timedelta(minutes=i), value=float(i)) for i in range(5)]
        ses = pa.exponential_smoothing(points, alpha=0.3)
        assert len(ses) == 5
        assert ses[0].value == 0.0

    def test_exponential_smoothing_empty(self):
        pa = PredictiveAnalytics()
        assert pa.exponential_smoothing([]) == []


class TestReportGenerator:
    def test_generate_summary(self):
        rg = ReportGenerator()
        now = datetime.utcnow()
        metrics = {
            "cpu": AggregatedMetric(metric_name="cpu", min_value=10, max_value=90, avg_value=50, median_value=50, p95_value=85, p99_value=90, std_dev=20, count=100, time_range=(now - timedelta(hours=1), now)),
        }
        report = rg.generate_summary(metrics, (now - timedelta(hours=1), now))
        assert report["overall_status"] == "healthy"
        assert "cpu" in report["metrics_summary"]

    def test_generate_summary_with_alert(self):
        rg = ReportGenerator()
        now = datetime.utcnow()
        metrics = {
            "volatile": AggregatedMetric(metric_name="volatile", min_value=0, max_value=100, avg_value=30, median_value=20, p95_value=95, p99_value=99, std_dev=40, count=50, time_range=(now - timedelta(hours=1), now)),
        }
        report = rg.generate_summary(metrics, (now - timedelta(hours=1), now))
        assert report["overall_status"] == "degraded"
        assert len(report["alerts"]) > 0

    def test_generate_csv(self):
        rg = ReportGenerator()
        points = {
            "cpu": [TimeSeriesPoint(timestamp=datetime.utcnow(), value=50.0)],
            "memory": [TimeSeriesPoint(timestamp=datetime.utcnow(), value=70.0)],
        }
        csv = rg.generate_csv(points)
        assert "timestamp" in csv
        assert "cpu" in csv
        assert "memory" in csv

    def test_generate_html_dashboard(self):
        rg = ReportGenerator()
        now = datetime.utcnow()
        metrics = {
            "cpu": AggregatedMetric(metric_name="cpu", min_value=0, max_value=100, avg_value=50, median_value=50, p95_value=90, p99_value=95, std_dev=20, count=100, time_range=(now - timedelta(hours=1), now)),
        }
        html = rg.generate_html_dashboard(metrics)
        assert "<html>" in html
        assert "cpu" in html
        assert "Infra-pilot" in html


class TestAnalyticsEngine:
    @pytest.mark.asyncio
    async def test_collect_metric(self):
        engine = AnalyticsEngine()
        result = await engine.collect_metric("test.metric", 42.0)
        assert result.metric == "test.metric"
        assert result.value == 42.0

    @pytest.mark.asyncio
    async def test_collect_batch(self):
        engine = AnalyticsEngine()
        items = [("a", 1.0, None, None), ("b", 2.0, None, None), ("c", 3.0, None, None)]
        results = await engine.collect_batch(items)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_engine_health(self):
        engine = AnalyticsEngine()
        health = await engine.health_check()
        assert health["status"] == "stopped"
        assert health["metrics_tracked"] == 0

    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        engine = AnalyticsEngine()
        engine.start(interval=10)
        health = await engine.health_check()
        assert health["status"] == "healthy"
        engine.stop()
        health = await engine.health_check()
        assert health["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_anomaly_alert_callback(self):
        engine = AnalyticsEngine()
        alerts = []
        async def alert_cb(anomaly):
            alerts.append(anomaly)
        engine.register_alert_callback(alert_cb)
        engine.anomaly_detector.set_baseline("test.spike", 100.0, 5.0)
        await engine.collect_metric("test.spike", 500.0)
        await asyncio.sleep(0.1)
        assert len(alerts) > 0

    def test_aggregated(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("metric", 10.0)
        engine.aggregator.add_point("metric", 20.0)
        agg = engine.get_aggregated("metric")
        assert agg is not None
        assert agg.avg_value == 15.0

    def test_forecast(self):
        engine = AnalyticsEngine()
        for i in range(10):
            engine.aggregator.add_point("linear", float(i * 5), timestamp=datetime.utcnow() + timedelta(minutes=i))
        forecasts = engine.forecast("linear", horizon=3)
        assert len(forecasts) == 3

    def test_top_metrics(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("group.a", 10.0)
        engine.aggregator.add_point("group.b", 20.0)
        engine.aggregator.add_point("group.c", 30.0)
        top = engine.get_top_metrics("group", n=2)
        assert len(top) == 2

    def test_generate_report(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("test.m1", 50.0)
        engine.aggregator.add_point("test.m2", 60.0)
        report = engine.generate_report()
        assert "metrics_summary" in report
        assert "overall_status" in report

    def test_export_csv(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("export.me", 100.0)
        csv = engine.export_csv(["export.me"])
        assert "export.me" in csv or "timestamp" in csv

    def test_export_html(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("html.metric", 75.0)
        html = engine.export_html()
        assert "<html>" in html


class TestAnalyticsPipeline:
    @pytest.mark.asyncio
    async def test_process(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        result = await pipeline.process("pipeline.test", 99.0)
        assert result.metric == "pipeline.test"

    @pytest.mark.asyncio
    async def test_processors(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        processed = []
        def processor(result):
            processed.append(result)
            return result
        pipeline.add_processor(processor)
        await pipeline.process("proc.test", 50.0)
        assert len(processed) == 1

    @pytest.mark.asyncio
    async def test_outputs(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        outputs = []
        async def output(result):
            outputs.append(result)
        pipeline.add_output(output)
        await pipeline.process("out.test", 25.0)
        assert len(outputs) == 1

    def test_compute_sla(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        for v in [10, 20, 30, 40, 50]:
            engine.aggregator.add_point("sla.test", float(v))
        sla = pipeline.compute_sla("sla.test", threshold=35)
        assert 0 <= sla["sla_compliance"] <= 1

    def test_correlation(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        ts = datetime.utcnow()
        for i in range(10):
            engine.aggregator.add_point("corr.a", float(i), timestamp=ts + timedelta(minutes=i))
            engine.aggregator.add_point("corr.b", float(i * 2), timestamp=ts + timedelta(minutes=i))
        corr = pipeline.correlation("corr.a", "corr.b")
        assert corr > 0.5

    def test_correlation_no_data(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        assert pipeline.correlation("none.a", "none.b") == 0.0

    def test_correlation_insufficient(self):
        engine = AnalyticsEngine()
        pipeline = AnalyticsPipeline(engine)
        engine.aggregator.add_point("single.a", 1.0)
        engine.aggregator.add_point("single.b", 2.0)
        assert pipeline.correlation("single.a", "single.b") == 0.0


class TestDashboardBuilder:
    def test_add_widget(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_widget("gauge", "cpu", "CPU Usage")
        assert len(db._widgets) == 1

    def test_add_gauge(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_gauge("memory", "Memory", 0, 100, {"warning": 80, "critical": 95})
        assert db._widgets[0]["type"] == "gauge"

    def test_add_timeseries(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_timeseries("network", "Network Throughput", window=1800)
        assert db._widgets[0]["config"]["window"] == 1800

    def test_add_table(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_table("iot.", "Top IoT Metrics", top_n=5)
        assert db._widgets[0]["type"] == "table"

    def test_add_heatmap(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_heatmap("temperature", "Temperature Heatmap")
        assert db._widgets[0]["type"] == "heatmap"

    def test_render_config(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_gauge("cpu", "CPU")
        config = db.render_config()
        assert "dashboard" in config
        assert "widgets" in config["dashboard"]

    def test_render_summary(self):
        engine = AnalyticsEngine()
        db = DashboardBuilder(engine)
        db.add_gauge("test", "Test", 0, 100)
        engine.aggregator.add_point("test", 50.0)
        summary = db.render_summary()
        assert "widgets" in summary


class TestMetricsExporter:
    def test_export_prometheus(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("cpu_usage", 45.0)
        exporter = MetricsExporter(engine)
        output = exporter.export_prometheus()
        assert "cpu_usage" in output

    def test_export_json(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("json.test", 123.0)
        exporter = MetricsExporter(engine)
        output = exporter.export_json(["json.test"])
        assert "json.test" in output

    def test_export_datadog(self):
        engine = AnalyticsEngine()
        engine.aggregator.add_point("dd.test", 77.0)
        exporter = MetricsExporter(engine)
        output = exporter.export_datadog()
        assert "series" in output
        assert len(output["series"]) > 0
