"""Edge computing resource optimization and scaling utilities."""

import math
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ResourceSpec:
    cpu_cores: int = 4
    ram_gb: int = 8
    disk_gb: int = 100
    gpu_count: int = 0
    network_bandwidth_mbps: int = 1000
    max_power_watts: int = 250


@dataclass
class ResourceUsage:
    cpu_pct: float = 0.0
    ram_pct: float = 0.0
    disk_pct: float = 0.0
    gpu_pct: float = 0.0
    network_rx_mbps: float = 0.0
    network_tx_mbps: float = 0.0
    power_watts: float = 0.0
    temperature_celsius: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class ResourceOptimizer:
    """Optimizes resource allocation for edge nodes."""

    def __init__(self, spec: ResourceSpec):
        self.spec = spec
        self.usage_history: List[ResourceUsage] = []

    def record_usage(self, usage: ResourceUsage):
        self.usage_history.append(usage)
        if len(self.usage_history) > 1000:
            self.usage_history.pop(0)

    def get_current_efficiency(self) -> float:
        if not self.usage_history:
            return 1.0
        latest = self.usage_history[-1]
        cpu_eff = 1.0 - abs(0.6 - latest.cpu_pct / 100.0)
        ram_eff = 1.0 - abs(0.7 - latest.ram_pct / 100.0)
        return max(0.0, min(1.0, (cpu_eff + ram_eff) / 2.0))

    def get_rightsizing_recommendation(self) -> Dict[str, Any]:
        if len(self.usage_history) < 10:
            return {"recommendation": "insufficient_data"}
        recent = self.usage_history[-10:]
        avg_cpu = sum(u.cpu_pct for u in recent) / len(recent)
        avg_ram = sum(u.ram_pct for u in recent) / len(recent)
        avg_disk = sum(u.disk_pct for u in recent) / len(recent)
        recommendations = []
        if avg_cpu < 20 and self.spec.cpu_cores > 2:
            recommendations.append(f"Downsize CPU from {self.spec.cpu_cores} to {self.spec.cpu_cores // 2} cores")
        if avg_cpu > 80:
            recommendations.append(f"Upgrade CPU from {self.spec.cpu_cores} to {self.spec.cpu_cores * 2} cores")
        if avg_ram < 25 and self.spec.ram_gb > 4:
            recommendations.append(f"Reduce RAM from {self.spec.ram_gb}GB to {self.spec.ram_gb // 2}GB")
        if avg_ram > 85:
            recommendations.append(f"Increase RAM from {self.spec.ram_gb}GB to {self.spec.ram_gb * 2}GB")
        if avg_disk > 85:
            recommendations.append(f"Expand storage from {self.spec.disk_gb}GB")
        return {
            "avg_cpu_pct": round(avg_cpu, 1),
            "avg_ram_pct": round(avg_ram, 1),
            "avg_disk_pct": round(avg_disk, 1),
            "recommendations": recommendations,
            "efficiency_score": round(self.get_current_efficiency() * 100, 1),
        }

    def estimate_power_savings(self, target_usage: ResourceUsage) -> Dict[str, Any]:
        if not self.usage_history:
            return {"savings_watts": 0}
        current = self.usage_history[-1]
        power_saved = current.power_watts - target_usage.power_watts
        return {
            "current_power_watts": current.power_watts,
            "target_power_watts": target_usage.power_watts,
            "savings_watts": max(0, power_saved),
            "savings_kwh_daily": round(max(0, power_saved) * 24 / 1000, 2),
            "savings_usd_monthly": round(max(0, power_saved) * 24 * 30 * 0.12 / 1000, 2),
        }


class LoadBalancer:
    """Distributes workloads across edge nodes."""

    def __init__(self):
        self.nodes: Dict[str, ResourceUsage] = {}
        self.strategy = "least_loaded"

    def register_node(self, node_id: str, usage: Optional[ResourceUsage] = None):
        self.nodes[node_id] = usage or ResourceUsage()

    def update_node_usage(self, node_id: str, usage: ResourceUsage):
        self.nodes[node_id] = usage

    def select_node(self, required_cpu: float = 10.0, required_ram: float = 1.0) -> Optional[str]:
        candidates = []
        for node_id, usage in self.nodes.items():
            cpu_avail = 100.0 - usage.cpu_pct
            ram_avail = 100.0 - usage.ram_pct
            if cpu_avail >= required_cpu and ram_avail >= required_ram:
                if self.strategy == "least_loaded":
                    score = usage.cpu_pct + usage.ram_pct
                    candidates.append((score, node_id))
                elif self.strategy == "round_robin":
                    candidates.append((random.random(), node_id))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def get_load_distribution(self) -> Dict[str, float]:
        return {nid: u.cpu_pct for nid, u in self.nodes.items()}


class EdgeAutoScaler:
    """Auto-scales edge compute resources."""

    def __init__(self, min_nodes: int = 2, max_nodes: int = 20,
                 scale_up_threshold: float = 75.0,
                 scale_down_threshold: float = 30.0):
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.current_nodes = min_nodes
        self.scale_events: List[Dict[str, Any]] = []

    def evaluate(self, avg_cpu_usage: float) -> Dict[str, Any]:
        action = "none"
        reason = ""
        if avg_cpu_usage > self.scale_up_threshold and self.current_nodes < self.max_nodes:
            self.current_nodes += 1
            action = "scale_up"
            reason = f"CPU usage {avg_cpu_usage:.1f}% exceeds threshold {self.scale_up_threshold}%"
        elif avg_cpu_usage < self.scale_down_threshold and self.current_nodes > self.min_nodes:
            self.current_nodes -= 1
            action = "scale_down"
            reason = f"CPU usage {avg_cpu_usage:.1f}% below threshold {self.scale_down_threshold}%"
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "avg_cpu": round(avg_cpu_usage, 1),
            "nodes_before": self.current_nodes + (1 if action == "scale_up" else -1 if action == "scale_down" else 0),
            "nodes_after": self.current_nodes,
            "reason": reason,
        }
        if action != "none":
            self.scale_events.append(event)
        return event

    def get_history(self) -> List[Dict[str, Any]]:
        return self.scale_events[-50:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "current_nodes": self.current_nodes,
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            "scale_up_count": sum(1 for e in self.scale_events if e["action"] == "scale_up"),
            "scale_down_count": sum(1 for e in self.scale_events if e["action"] == "scale_down"),
            "last_event": self.scale_events[-1] if self.scale_events else None,
        }


class EdgeHealthChecker:
    """Performs health checks on edge nodes."""

    def __init__(self):
        self.check_results: Dict[str, List[Dict[str, Any]]] = {}

    def check_node(self, node_id: str, usage: ResourceUsage) -> Dict[str, Any]:
        issues = []
        if usage.cpu_pct > 90:
            issues.append({"severity": "warning", "check": "cpu", "message": f"CPU at {usage.cpu_pct:.1f}%"})
        if usage.ram_pct > 90:
            issues.append({"severity": "warning", "check": "memory", "message": f"RAM at {usage.ram_pct:.1f}%"})
        if usage.disk_pct > 90:
            issues.append({"severity": "critical", "check": "disk", "message": f"Disk at {usage.disk_pct:.1f}%"})
        if usage.temperature_celsius > 75:
            issues.append({"severity": "critical", "check": "temperature", "message": f"Temp {usage.temperature_celsius:.1f}°C"})
        if usage.power_watts > 500:
            issues.append({"severity": "warning", "check": "power", "message": f"Power draw {usage.power_watts}W"})
        status = "healthy"
        if any(i["severity"] == "critical" for i in issues):
            status = "critical"
        elif any(i["severity"] == "warning" for i in issues):
            status = "degraded"
        result = {
            "node_id": node_id,
            "status": status,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }
        if node_id not in self.check_results:
            self.check_results[node_id] = []
        self.check_results[node_id].append(result)
        return result

    def get_node_history(self, node_id: str) -> List[Dict[str, Any]]:
        return self.check_results.get(node_id, [])

    def get_unhealthy_nodes(self) -> List[str]:
        unhealthy = []
        for node_id, results in self.check_results.items():
            if results and results[-1]["status"] != "healthy":
                unhealthy.append(node_id)
        return unhealthy
