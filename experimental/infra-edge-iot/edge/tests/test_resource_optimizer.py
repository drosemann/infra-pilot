"""Resource optimization and edge utility tests."""

import pytest
from resource_optimizer import (
    ResourceSpec, ResourceUsage, ResourceOptimizer,
    LoadBalancer, EdgeAutoScaler, EdgeHealthChecker
)


class TestResourceOptimizer:
    def test_record_usage(self):
        opt = ResourceOptimizer(ResourceSpec())
        usage = ResourceUsage(cpu_pct=50, ram_pct=60)
        opt.record_usage(usage)
        assert len(opt.usage_history) == 1

    def test_get_current_efficiency(self):
        opt = ResourceOptimizer(ResourceSpec())
        usage = ResourceUsage(cpu_pct=60, ram_pct=70)
        opt.record_usage(usage)
        eff = opt.get_current_efficiency()
        assert 0 <= eff <= 1

    def test_rightsizing_no_data(self):
        opt = ResourceOptimizer(ResourceSpec())
        rec = opt.get_rightsizing_recommendation()
        assert rec["recommendation"] == "insufficient_data"

    def test_rightsizing_with_data(self):
        opt = ResourceOptimizer(ResourceSpec(cpu_cores=8, ram_gb=32))
        for _ in range(10):
            opt.record_usage(ResourceUsage(cpu_pct=10, ram_pct=15, disk_pct=20))
        rec = opt.get_rightsizing_recommendation()
        assert "recommendations" in rec
        assert len(rec["recommendations"]) > 0

    def test_estimate_power_savings(self):
        opt = ResourceOptimizer(ResourceSpec())
        opt.record_usage(ResourceUsage(power_watts=500))
        target = ResourceUsage(power_watts=300)
        savings = opt.estimate_power_savings(target)
        assert savings["savings_kwh_daily"] > 0


class TestLoadBalancer:
    def test_register_node(self):
        lb = LoadBalancer()
        lb.register_node("node-001")
        assert "node-001" in lb.nodes

    def test_select_node_least_loaded(self):
        lb = LoadBalancer()
        lb.register_node("node-001", ResourceUsage(cpu_pct=80, ram_pct=80))
        lb.register_node("node-002", ResourceUsage(cpu_pct=20, ram_pct=30))
        selected = lb.select_node(10, 5)
        assert selected == "node-002"

    def test_select_node_no_capacity(self):
        lb = LoadBalancer()
        lb.register_node("node-001", ResourceUsage(cpu_pct=95, ram_pct=95))
        selected = lb.select_node(20, 20)
        assert selected is None

    def test_get_load_distribution(self):
        lb = LoadBalancer()
        lb.register_node("node-001", ResourceUsage(cpu_pct=50))
        dist = lb.get_load_distribution()
        assert len(dist) == 1


class TestEdgeAutoScaler:
    def test_scale_up(self):
        scaler = EdgeAutoScaler(min_nodes=2, max_nodes=10, scale_up_threshold=50)
        result = scaler.evaluate(75)
        assert result["action"] == "scale_up"

    def test_scale_down(self):
        scaler = EdgeAutoScaler(min_nodes=2, max_nodes=10, scale_down_threshold=50)
        scaler.current_nodes = 5
        result = scaler.evaluate(20)
        assert result["action"] == "scale_down"

    def test_no_action(self):
        scaler = EdgeAutoScaler(scale_up_threshold=80, scale_down_threshold=20)
        result = scaler.evaluate(50)
        assert result["action"] == "none"

    def test_get_history(self):
        scaler = EdgeAutoScaler()
        scaler.evaluate(90)
        history = scaler.get_history()
        assert len(history) >= 1

    def test_get_stats(self):
        scaler = EdgeAutoScaler()
        stats = scaler.get_stats()
        assert "current_nodes" in stats


class TestEdgeHealthChecker:
    def test_check_healthy(self):
        hc = EdgeHealthChecker()
        result = hc.check_node("node-001", ResourceUsage(
            cpu_pct=50, ram_pct=60, disk_pct=40, temperature_celsius=45, power_watts=200))
        assert result["status"] == "healthy"

    def test_check_critical(self):
        hc = EdgeHealthChecker()
        result = hc.check_node("node-001", ResourceUsage(
            cpu_pct=95, ram_pct=50, disk_pct=98, temperature_celsius=80, power_watts=200))
        assert result["status"] == "critical"

    def test_get_unhealthy_nodes(self):
        hc = EdgeHealthChecker()
        hc.check_node("node-001", ResourceUsage(temperature_celsius=80))
        unhealthy = hc.get_unhealthy_nodes()
        assert len(unhealthy) >= 1

    def test_get_node_history(self):
        hc = EdgeHealthChecker()
        hc.check_node("node-001", ResourceUsage())
        history = hc.get_node_history("node-001")
        assert len(history) == 1
