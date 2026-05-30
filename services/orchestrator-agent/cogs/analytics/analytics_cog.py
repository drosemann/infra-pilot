import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

from services.integration_service.src.analytics.engine import (
    AnalyticsEngine, AnalyticsPipeline, AggregatedMetric, TimeSeriesPoint, AnomalyDetector,
)

logger = logging.getLogger("infra-pilot.analytics")


class AnalyticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.engine = AnalyticsEngine()
        self.pipeline = AnalyticsPipeline(self.engine)
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._alert_channels: Dict[str, int] = {}

    async def cog_load(self):
        self.engine.register_alert_callback(self._on_anomaly)
        self.engine.start(interval=30)
        self._running = True
        self._tasks.append(asyncio.create_task(self._generate_sample_data()))
        logger.info("AnalyticsCog loaded")

    async def cog_unload(self):
        self._running = False
        self.engine.stop()
        for task in self._tasks:
            task.cancel()
        logger.info("AnalyticsCog unloaded")

    async def _on_anomaly(self, anomaly: Dict[str, Any]):
        logger.warning(f"Anomaly detected: {anomaly}")
        for channel_name, channel_id in self._alert_channels.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Analytics Anomaly Alert",
                    description=f"Metric: {anomaly['metric']}",
                    color=discord.Color.red() if anomaly.get("severity") == "critical" else discord.Color.orange(),
                )
                embed.add_field(name="Value", value=str(anomaly.get("value", "N/A")))
                embed.add_field(name="Z-Score", value=str(anomaly.get("z_score", "N/A")))
                embed.add_field(name="Severity", value=anomaly.get("severity", "unknown"))
                embed.add_field(name="Threshold", value=str(anomaly.get("threshold", "N/A")))
                await channel.send(embed=embed)

    async def _generate_sample_data(self):
        iot_metrics = [
            "iot.temperature", "iot.humidity", "iot.pressure", "iot.vibration",
            "iot.power_consumption", "iot.signal_strength", "iot.data_rate",
            "iot.packet_loss", "iot.latency", "iot.battery_level",
        ]
        edge_metrics = [
            "edge.cpu_usage", "edge.memory_usage", "edge.disk_usage", "edge.network_throughput",
            "edge.request_count", "edge.error_rate", "edge.response_time",
            "edge.active_connections", "edge.container_count", "edge.function_invocations",
        ]
        green_metrics = [
            "green.power_usage", "green.carbon_emission", "green.pue", "green.energy_cost",
            "green.renewable_percentage", "green.cooling_efficiency", "green.server_utilization",
            "green.water_usage", "green.recycling_rate", "green.sustainability_score",
        ]
        while self._running:
            for metric in iot_metrics:
                base = {
                    "iot.temperature": 25, "iot.humidity": 60, "iot.pressure": 1013,
                    "iot.vibration": 0.5, "iot.power_consumption": 100, "iot.signal_strength": -60,
                    "iot.data_rate": 1000, "iot.packet_loss": 0.1, "iot.latency": 50, "iot.battery_level": 85,
                }
                val = base.get(metric, 50) + random.gauss(0, base.get(metric, 50) * 0.1)
                await self.engine.collect_metric(metric, round(val, 2))
            for metric in edge_metrics:
                base = {
                    "edge.cpu_usage": 45, "edge.memory_usage": 60, "edge.disk_usage": 55,
                    "edge.network_throughput": 800, "edge.request_count": 1500, "edge.error_rate": 0.5,
                    "edge.response_time": 120, "edge.active_connections": 200, "edge.container_count": 15,
                    "edge.function_invocations": 500,
                }
                val = base.get(metric, 50) + random.gauss(0, base.get(metric, 50) * 0.15)
                await self.engine.collect_metric(metric, round(val, 2))
            for metric in green_metrics:
                base = {
                    "green.power_usage": 350, "green.carbon_emission": 150, "green.pue": 1.4,
                    "green.energy_cost": 1200, "green.renewable_percentage": 45, "green.cooling_efficiency": 0.75,
                    "green.server_utilization": 65, "green.water_usage": 500, "green.recycling_rate": 60,
                    "green.sustainability_score": 72,
                }
                val = base.get(metric, 50) + random.gauss(0, base.get(metric, 50) * 0.1)
                await self.engine.collect_metric(metric, round(val, 2))
            await asyncio.sleep(60)

    @commands.group(name="analytics", invoke_without_command=True)
    async def analytics_group(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @analytics_group.command(name="status")
    async def analytics_status(self, ctx: commands.Context):
        health = await self.engine.health_check()
        embed = discord.Embed(title="Analytics Engine Status", color=discord.Color.blue())
        embed.add_field(name="Status", value=health["status"])
        embed.add_field(name="Metrics Tracked", value=str(health["metrics_tracked"]))
        embed.add_field(name="Data Points", value=str(health["total_data_points"]))
        embed.add_field(name="Alert Callbacks", value=str(health["alert_callbacks"]))
        await ctx.send(embed=embed)

    @analytics_group.command(name="metric")
    async def get_metric(self, ctx: commands.Context, metric_name: str):
        agg = self.engine.get_aggregated(metric_name)
        if not agg:
            await ctx.send(f"No data for metric: {metric_name}")
            return
        embed = discord.Embed(title=f"Metric: {metric_name}", color=discord.Color.green())
        embed.add_field(name="Avg", value=f"{agg.avg_value:.2f}")
        embed.add_field(name="Min", value=f"{agg.min_value:.2f}")
        embed.add_field(name="Max", value=f"{agg.max_value:.2f}")
        embed.add_field(name="P95", value=f"{agg.p95_value:.2f}")
        embed.add_field(name="P99", value=f"{agg.p99_value:.2f}")
        embed.add_field(name="Std Dev", value=f"{agg.std_dev:.2f}")
        embed.add_field(name="Samples", value=str(agg.count))
        await ctx.send(embed=embed)

    @analytics_group.command(name="trend")
    async def show_trend(self, ctx: commands.Context, metric_name: str, window: int = 3600):
        points = self.engine.get_trend(metric_name, window=window)
        if not points:
            await ctx.send(f"No trend data for: {metric_name}")
            return
        lines = [f"**{metric_name}** trend (last {window}s):"]
        for p in points[-10:]:
            lines.append(f"  {p.timestamp.strftime('%H:%M')}: {p.value:.2f}")
        await ctx.send("\n".join(lines))

    @analytics_group.command(name="top")
    async def top_metrics(self, ctx: commands.Context, prefix: str = "", n: int = 10):
        items = self.engine.get_top_metrics(prefix, n=n)
        if not items:
            await ctx.send(f"No metrics found with prefix '{prefix}'")
            return
        lines = [f"**Top {n} metrics** (prefix: '{prefix}'):"]
        for i, (name, val) in enumerate(items, 1):
            lines.append(f"  {i}. {name}: {val:.2f}")
        await ctx.send("\n".join(lines))

    @analytics_group.command(name="forecast")
    async def forecast_metric(self, ctx: commands.Context, metric_name: str, horizon: int = 10):
        forecasts = self.engine.forecast(metric_name, horizon=horizon)
        if not forecasts:
            await ctx.send(f"Cannot forecast: {metric_name}")
            return
        lines = [f"**Forecast** for {metric_name} (next {horizon} periods):"]
        for p in forecasts:
            lines.append(f"  {p.timestamp.strftime('%H:%M')}: {p.value:.2f}")
        await ctx.send("\n".join(lines))

    @analytics_group.command(name="report")
    async def generate_report(self, ctx: commands.Context):
        report = self.engine.generate_report()
        embed = discord.Embed(
            title="Analytics Report",
            description=f"Status: {report['overall_status']}",
            color=discord.Color.green() if report['overall_status'] == 'healthy' else discord.Color.orange(),
        )
        for mname, summary in list(report["metrics_summary"].items())[:10]:
            embed.add_field(name=mname, value=f"Avg: {summary['avg']:.1f}, P95: {summary['p95']:.1f}", inline=False)
        if report.get("alerts"):
            embed.add_field(name="Alerts", value="\n".join(report["alerts"][:5]), inline=False)
        await ctx.send(embed=embed)

    @analytics_group.command(name="export")
    async def export_metrics(self, ctx: commands.Context, format: str = "json"):
        if format == "json":
            data = self.engine.export_csv(list(self.engine.aggregator._data_buckets.keys())[:5])
            await ctx.send(f"```json\n{data[:1900]}\n```")
        elif format == "html":
            html = self.engine.export_html()
            if len(html) > 1900:
                await ctx.send("HTML dashboard too large for Discord. Use /analytics export-html-link")
            else:
                await ctx.send(f"```html\n{html}\n```")
        else:
            await ctx.send(f"Unknown format: {format}")

    @analytics_group.command(name="set-baseline")
    @commands.has_permissions(administrator=True)
    async def set_baseline(self, ctx: commands.Context, metric: str, mean: float, std: float):
        self.engine.anomaly_detector.set_baseline(metric, mean, std)
        await ctx.send(f"Set baseline for {metric}: mean={mean}, std={std}")

    @analytics_group.command(name="set-threshold")
    @commands.has_permissions(administrator=True)
    async def set_threshold(self, ctx: commands.Context, threshold: float):
        self.engine.anomaly_detector.threshold = threshold
        await ctx.send(f"Anomaly detection threshold set to {threshold}")

    @analytics_group.command(name="pipeline-status")
    async def pipeline_status(self, ctx: commands.Context):
        await ctx.send(f"Pipeline processors: {len(self.pipeline._processors)}, outputs: {len(self.pipeline._outputs)}")

    @analytics_group.command(name="sla")
    async def sla_check(self, ctx: commands.Context, metric: str, threshold: float):
        sla = self.pipeline.compute_sla(metric, threshold)
        embed = discord.Embed(title=f"SLA for {metric}", color=discord.Color.blue())
        embed.add_field(name="Compliance", value=f"{sla['sla_compliance'] * 100:.2f}%")
        embed.add_field(name="Breaches", value=str(sla["breaches"]))
        embed.add_field(name="Total Samples", value=str(sla["total"]))
        embed.add_field(name="Threshold", value=str(sla.get("threshold", "N/A")))
        await ctx.send(embed=embed)

    @analytics_group.command(name="correlate")
    async def correlate(self, ctx: commands.Context, metric_a: str, metric_b: str):
        corr = self.pipeline.correlation(metric_a, metric_b)
        await ctx.send(f"Correlation between **{metric_a}** and **{metric_b}**: {corr}")

    @analytics_group.command(name="register-collector")
    @commands.has_permissions(administrator=True)
    async def register_collector(self, ctx: commands.Context, pattern: str):
        async def sample_collector():
            return {pattern: random.uniform(0, 100)}
        self.engine.register_metric_route(pattern, sample_collector)
        await ctx.send(f"Registered metric collector for `{pattern}`")

    @analytics_group.command(name="alert-channel")
    @commands.has_permissions(administrator=True)
    async def set_alert_channel(self, ctx: commands.Context, channel_name: str):
        self._alert_channels[channel_name] = ctx.channel.id
        await ctx.send(f"Alert channel set to #{channel_name} (ID: {ctx.channel.id})")


async def setup(bot: commands.Bot):
    await bot.add_cog(AnalyticsCog(bot))
