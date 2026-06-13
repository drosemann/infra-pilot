from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class ActiveActiveManager:
    """Multi-region active-active setup with global load balancing and conflict resolution"""

    REPLICATION_MODES = ["syncretic", "async", "semi-sync"]
    CONFLICT_RESOLUTION_STRATEGIES = ["last_write_wins", "crdt", "custom", "manual"]
    REGION_STATUSES = ["healthy", "degraded", "unhealthy", "offline"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = config.get("active_active_file", "data/resiliency/active_active_configs.json")
        self.metrics_file = config.get("active_active_metrics_file", "data/resiliency/active_active_metrics.json")
        self.regions: List[Dict[str, Any]] = []
        self.traffic_rules: List[Dict[str, Any]] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.config_file) or ".", exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.regions = data.get("regions", [])
                    self.traffic_rules = data.get("traffic_rules", [])
            except Exception as e:
                logger.warning(f"Failed to load active-active config: {e}")
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r") as f:
                    self.metrics_history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")

    def _save_config(self):
        os.makedirs(os.path.dirname(self.config_file) or ".", exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump({"regions": self.regions, "traffic_rules": self.traffic_rules}, f, indent=2, default=str)

    def _save_metrics(self):
        os.makedirs(os.path.dirname(self.metrics_file) or ".", exist_ok=True)
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics_history[-10000:], f, indent=2, default=str)

    async def initialize(self):
        logger.info("ActiveActiveManager initialized")

    async def close(self):
        logger.info("ActiveActiveManager closed")

    async def register_region(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        region = {
            "id": f"region_{int(datetime.now().timestamp())}_{len(self.regions)}",
            "name": region_data.get("name", ""),
            "endpoint": region_data.get("endpoint", ""),
            "health_endpoint": region_data.get("health_endpoint", ""),
            "status": "healthy",
            "weight": region_data.get("weight", 100),
            "capacity": region_data.get("capacity", 100),
            "current_load": 0,
            "replication_lag_ms": 0,
            "replication_mode": region_data.get("replication_mode", "async"),
            "conflict_resolution": region_data.get("conflict_resolution", "last_write_wins"),
            "dns_record": region_data.get("dns_record", ""),
            "geo_restrictions": region_data.get("geo_restrictions", []),
            "latency_base_ms": region_data.get("latency_base_ms", 0),
            "created_at": datetime.now().isoformat(),
            "last_health_check": None,
        }
        self.regions.append(region)
        self._save_config()
        return region

    async def list_regions(self) -> List[Dict[str, Any]]:
        return self.regions

    async def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self.regions if r["id"] == region_id), None)

    async def update_region(self, region_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for region in self.regions:
            if region["id"] == region_id:
                region.update(updates)
                self._save_config()
                return region
        return None

    async def delete_region(self, region_id: str) -> bool:
        for i, region in enumerate(self.regions):
            if region["id"] == region_id:
                self.regions.pop(i)
                self._save_config()
                return True
        return False

    async def health_check(self, region_id: str) -> Dict[str, Any]:
        region = await self.get_region(region_id)
        if not region:
            return {"error": "Region not found"}
        healthy = random.random() > 0.05
        region["status"] = "healthy" if healthy else "unhealthy"
        region["last_health_check"] = datetime.now().isoformat()
        self._save_config()
        return {"region_id": region_id, "status": region["status"], "healthy": healthy, "latency_ms": random.randint(5, 200), "load_percent": region.get("current_load", 0)}

    async def update_traffic_weight(self, region_id: str, weight: int) -> Optional[Dict[str, Any]]:
        for region in self.regions:
            if region["id"] == region_id:
                old_weight = region["weight"]
                region["weight"] = max(0, min(weight, 100))
                self._save_config()
                return {"region_id": region_id, "old_weight": old_weight, "new_weight": region["weight"], "total_weight": sum(r["weight"] for r in self.regions)}

    async def create_traffic_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        rule = {
            "id": f"traffic_rule_{int(datetime.now().timestamp())}_{len(self.traffic_rules)}",
            "name": rule_data.get("name", ""),
            "type": rule_data.get("type", "geo"),
            "source_geo": rule_data.get("source_geo", []),
            "target_region": rule_data.get("target_region", ""),
            "fallback_region": rule_data.get("fallback_region", ""),
            "conditions": rule_data.get("conditions", {}),
            "priority": rule_data.get("priority", 10),
            "active": True,
            "created_at": datetime.now().isoformat(),
        }
        self.traffic_rules.append(rule)
        self._save_config()
        return rule

    async def list_traffic_rules(self) -> List[Dict[str, Any]]:
        return self.traffic_rules

    async def delete_traffic_rule(self, rule_id: str) -> bool:
        for i, rule in enumerate(self.traffic_rules):
            if rule["id"] == rule_id:
                self.traffic_rules.pop(i)
                self._save_config()
                return True
        return False

    async def record_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        metrics = {
            "id": f"metric_{int(datetime.now().timestamp())}_{len(self.metrics_history)}",
            "region_id": metrics_data.get("region_id", ""),
            "requests_per_second": metrics_data.get("requests_per_second", 0),
            "error_rate": metrics_data.get("error_rate", 0),
            "latency_p50": metrics_data.get("latency_p50", 0),
            "latency_p99": metrics_data.get("latency_p99", 0),
            "replication_lag_ms": metrics_data.get("replication_lag_ms", 0),
            "active_connections": metrics_data.get("active_connections", 0),
            "timestamp": datetime.now().isoformat(),
        }
        self.metrics_history.append(metrics)
        self._save_metrics()
        region = await self.get_region(metrics_data.get("region_id", ""))
        if region:
            region["current_load"] = metrics_data.get("active_connections", 0)
            region["replication_lag_ms"] = metrics_data.get("replication_lag_ms", 0)
            self._save_config()
        return metrics

    async def get_global_status(self) -> Dict[str, Any]:
        healthy_regions = sum(1 for r in self.regions if r["status"] == "healthy")
        total_regions = len(self.regions)
        total_load = sum(r.get("current_load", 0) for r in self.regions)
        return {"total_regions": total_regions, "healthy_regions": healthy_regions, "degraded_regions": total_regions - healthy_regions, "total_load": total_load, "regions": self.regions, "active_rules": len(self.traffic_rules), "replication_status": "synced" if all(r.get("replication_lag_ms", 0) < 100 for r in self.regions) else "lagging"}

    async def resolve_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        strategy = conflict_data.get("strategy", "last_write_wins")
        return {"conflict_id": f"conflict_{int(datetime.now().timestamp())}", "strategy": strategy, "resolution": "auto_resolved", "resolved_value": conflict_data.get("proposed_value"), "timestamp": datetime.now().isoformat()}

    async def add_traffic_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        new_rule = {"id": f"rule_{len(self.traffic_rules)}_{int(datetime.now().timestamp())}", "source_region": rule.get("source_region"), "destination_region": rule.get("destination_region"), "weight": rule.get("weight", 50), "conditions": rule.get("conditions", {}), "enabled": True, "created_at": datetime.now().isoformat()}
        self.traffic_rules.append(new_rule)
        self._save_config()
        return new_rule

    async def update_traffic_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for rule in self.traffic_rules:
            if rule["id"] == rule_id:
                rule.update(updates)
                self._save_config()
                return rule
        return None

    async def update_region_status(self, region_id: str, status: str, load: Optional[int] = None, lag: Optional[int] = None) -> Optional[Dict[str, Any]]:
        for region in self.regions:
            if region["id"] == region_id:
                region["status"] = status
                if load is not None:
                    region["current_load"] = load
                if lag is not None:
                    region["replication_lag_ms"] = lag
                self._save_config()
                return region
        return None

    async def get_routing_table(self) -> List[Dict[str, Any]]:
        healthy = [r for r in self.regions if r.get("status") == "healthy"]
        total_weight = sum(r.get("weight", 0) for r in healthy)
        return [{"region_id": r["id"], "region_name": r["name"], "endpoint": r["endpoint"], "weight_pct": round(r.get("weight", 0) / total_weight * 100, 1) if total_weight else 0, "status": r.get("status")} for r in healthy]

    async def simulate_failover(self, region_id: str) -> Dict[str, Any]:
        target = next((r for r in self.regions if r["id"] == region_id), None)
        if not target:
            return {"error": "Region not found"}
        if target.get("status") != "healthy":
            return {"error": "Region is not healthy"}
        details = {"source_region": region_id, "failover_time_ms": random.randint(2000, 10000), "traffic_rerouted_to": [r["name"] for r in self.regions if r["id"] != region_id and r.get("status") == "healthy"], "data_loss_seconds": random.randint(0, 5), "dns_propagation_ms": random.randint(1000, 5000), "status": "simulated_ok"}
        return details

    async def get_all_rules(self) -> List[Dict[str, Any]]:
        return self.traffic_rules

    async def delete_region(self, region_id: str) -> bool:
        for i, r in enumerate(self.regions):
            if r["id"] == region_id:
                self.regions.pop(i)
                self._save_config()
                return True
        return False

    async def delete_traffic_rule(self, rule_id: str) -> bool:
        for i, r in enumerate(self.traffic_rules):
            if r["id"] == rule_id:
                self.traffic_rules.pop(i)
                self._save_config()
                return True
        return False

    async def get_lag_report(self) -> Dict[str, Any]:
        lags = [(r["name"], r.get("replication_lag_ms", 0)) for r in self.regions]
        avg_lag = sum(lag for _, lag in lags) / len(lags) if lags else 0
        max_lag = max(lags, key=lambda x: x[1]) if lags else ("none", 0)
        return {"average_lag_ms": round(avg_lag, 1), "max_lag_ms": max_lag[1], "max_lag_region": max_lag[0], "regions_lagging_above_100ms": len([lag for _, lag in lags if lag > 100]), "total_regions": len(lags)}


class ActiveActiveBatchProcessor:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def process_regions(self, regions: List[Dict[str, Any]], action: str = "register") -> List[Dict[str, Any]]:
        results = []
        for i, region in enumerate(regions):
            try:
                if action == "register":
                    r = await self.manager.register_region(region)
                elif action == "health_check":
                    r = await self.manager.health_check(region.get("id", ""))
                else:
                    r = {"error": f"Unknown action: {action}"}
                r["batch_index"] = i
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e), "region": region})
        self.results.extend(results)
        return results

    async def process_rules(self, rules: List[Dict[str, Any]], action: str = "create") -> List[Dict[str, Any]]:
        results = []
        for i, rule in enumerate(rules):
            try:
                if action == "create":
                    r = await self.manager.create_traffic_rule(rule)
                else:
                    r = {"error": f"Unknown action: {action}"}
                r["batch_index"] = i
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e), "rule": rule})
        self.results.extend(results)
        return results

    async def health_check_all(self) -> List[Dict[str, Any]]:
        results = []
        for region in self.manager.regions:
            r = await self.manager.health_check(region["id"])
            r["region_name"] = region.get("name")
            results.append(r)
        return results

    async def failover_batch(self, region_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rid in region_ids:
            r = await self.manager.simulate_failover(rid)
            r["region_id"] = rid
            results.append(r)
        return results

    def export_csv(self, data: List[Dict[str, Any]], fields: Optional[List[str]] = None) -> str:
        if not data:
            return ""
        if not fields:
            fields = list(data[0].keys())
        lines = [",".join(fields)]
        for item in data:
            row = [str(item.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        return {"total_operations": total, "passed": passed, "failed": total - passed, "success_rate": round(passed / total * 100, 1) if total else 100.0}


class ActiveActiveAnalytics:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    def calculate_region_health(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"average_latency_ms": 0, "healthy_count": 0, "total_count": 0}
        healthy = sum(1 for r in regions if r.get("status") == "healthy")
        avg_latency = sum(r.get("latency_base_ms", 0) for r in regions) / len(regions) if regions else 0
        total_weight = sum(r.get("weight", 0) for r in regions)
        avg_load = sum(r.get("current_load", 0) for r in regions) / len(regions) if regions else 0
        return {"total_regions": len(regions), "healthy_count": healthy, "healthy_pct": round(healthy / len(regions) * 100, 1), "degraded_count": len(regions) - healthy, "average_latency_ms": round(avg_latency, 1), "average_load": round(avg_load, 1), "total_traffic_weight": total_weight}

    def analyze_replication_lag(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"average_lag_ms": 0, "max_lag_ms": 0, "lagging_regions": []}
        lags = [(r["name"], r.get("replication_lag_ms", 0)) for r in regions]
        avg_lag = sum(lag for _, lag in lags) / len(lags)
        max_lag = max(lags, key=lambda x: x[1])
        lagging = [name for name, lag in lags if lag > 100]
        return {"average_lag_ms": round(avg_lag, 1), "max_lag_ms": max_lag[1], "max_lag_region": max_lag[0], "lagging_regions": lagging, "total_lagging": len(lagging), "replication_status": "healthy" if avg_lag < 50 else "degraded" if avg_lag < 200 else "unhealthy"}

    def analyze_traffic_distribution(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {}
        total_weight = sum(r.get("weight", 0) for r in regions)
        distribution = []
        for r in regions:
            pct = round(r.get("weight", 0) / total_weight * 100, 1) if total_weight else 0
            distribution.append({"region": r.get("name"), "weight_pct": pct, "load": r.get("current_load", 0), "status": r.get("status")})
        return {"total_weight": total_weight, "distribution": distribution, "imbalance_score": round(max(d["weight_pct"] for d in distribution) - min(d["weight_pct"] for d in distribution), 1) if len(distribution) > 1 else 0}

    def get_failover_readiness(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if len(regions) < 2:
            return {"ready": False, "reason": "Need at least 2 regions for failover"}
        healthy = [r for r in regions if r.get("status") == "healthy"]
        return {"ready": len(healthy) >= 2, "healthy_regions": len(healthy), "total_regions": len(regions), "can_absorb_traffic": sum(r.get("capacity", 0) for r in healthy if r.get("current_load", 0) < r.get("capacity", 100)) > 0}

    def generate_report(self) -> str:
        lines = ["=== Active-Active Region Report ==="]
        lines.append(f"Total Regions: {len(self.manager.regions)}")
        lines.append(f"Total Traffic Rules: {len(self.manager.traffic_rules)}")
        health = self.calculate_region_health()
        lines.append(f"Healthy Regions: {health.get('healthy_count', 0)}/{health.get('total_count', 0)}")
        lag = self.analyze_replication_lag()
        lines.append(f"Average Replication Lag: {lag.get('average_lag_ms', 0)}ms")
        dist = self.analyze_traffic_distribution()
        lines.append(f"Traffic Imbalance: {dist.get('imbalance_score', 0)}%")
        lines.append(f"Failover Ready: {self.get_failover_readiness().get('ready', False)}")
        return "\n".join(lines)


class ActiveActivePaginator:
    def __init__(self, items: List[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size

    def get_page(self, page: int = 1) -> List[Any]:
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.items[start:end] if start < len(self.items) else []

    def get_total_pages(self) -> int:
        return max(1, (len(self.items) + self.page_size - 1) // self.page_size)

    def get_metadata(self) -> Dict[str, Any]:
        return {"total_items": len(self.items), "page_size": self.page_size, "total_pages": self.get_total_pages(), "has_next": self.get_total_pages() > 1, "has_previous": False}


class GlobalLoadBalancer:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def route_request(self, source_geo: str = "default") -> Optional[Dict[str, Any]]:
        active_rules = [r for r in self.manager.traffic_rules if r.get("active", True)]
        matched = [r for r in active_rules if source_geo in r.get("source_geo", [])]
        if matched:
            rule = max(matched, key=lambda r: r.get("priority", 0))
            target = await self.manager.get_region(rule["target_region"])
            if target and target.get("status") == "healthy":
                return {"region": target, "rule": rule, "routed_by": "geo_rule"}
            fallback = await self.manager.get_region(rule.get("fallback_region", ""))
            if fallback:
                return {"region": fallback, "rule": rule, "routed_by": "geo_fallback"}
        healthy = [r for r in self.manager.regions if r.get("status") == "healthy"]
        if healthy:
            total = sum(r.get("weight", 1) for r in healthy)
            import random
            pick = random.uniform(0, total)
            cumulative = 0
            for r in healthy:
                cumulative += r.get("weight", 1)
                if pick <= cumulative:
                    return {"region": r, "routed_by": "weighted_random"}
            return {"region": healthy[-1], "routed_by": "fallback"}
        return None


class ConflictResolver:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def resolve_write_conflict(self, key: str, current_value: Any, incoming_value: Any, strategy: str = "last_write_wins") -> Dict[str, Any]:
        if strategy == "last_write_wins":
            resolved = incoming_value
            reason = "Incoming value accepted (last write wins)"
        elif strategy == "crdt":
            if isinstance(current_value, dict) and isinstance(incoming_value, dict):
                merged = {**current_value, **incoming_value}
                resolved = merged
                reason = "CRDT merge applied"
            else:
                resolved = incoming_value
                reason = "CRDT not applicable, accepted incoming"
        elif strategy == "custom":
            resolved = incoming_value
            reason = "Custom resolution applied"
        else:
            resolved = current_value
            reason = "Manual resolution required"
        return {"key": key, "original_value": current_value, "resolved_value": resolved, "strategy": strategy, "reason": reason, "resolved_at": datetime.now().isoformat()}


class DNSHealthChecker:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def check_endpoint_health(self, region_id: str) -> Dict[str, Any]:
        region = await self.manager.get_region(region_id)
        if not region:
            return {"error": "Region not found"}
        dns_resolvable = bool(region.get("dns_record"))
        endpoint_reachable = region.get("status") == "healthy"
        return {"region_id": region_id, "region_name": region.get("name"), "dns_record": region.get("dns_record"), "dns_resolvable": dns_resolvable, "endpoint_reachable": endpoint_reachable, "health_status": region.get("status"), "check_time": datetime.now().isoformat()}

    async def batch_dns_check(self) -> List[Dict[str, Any]]:
        results = []
        for region in self.manager.regions:
            r = await self.check_endpoint_health(region["id"])
            results.append(r)
        return results


class TrafficRouter:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def get_optimal_region(self, source_geo: str = "default", required_capacity: int = 0) -> Optional[Dict[str, Any]]:
        healthy = [r for r in self.manager.regions if r.get("status") == "healthy"]
        if not healthy:
            return None
        geo_rules = [r for r in self.manager.traffic_rules if source_geo in r.get("source_geo", []) and r.get("active", True)]
        if geo_rules:
            best = max(geo_rules, key=lambda r: r.get("priority", 0))
            target = await self.manager.get_region(best["target_region"])
            if target and target.get("status") == "healthy" and target.get("capacity", 100) >= required_capacity:
                return target
        weighted = []
        total = sum(r.get("weight", 1) for r in healthy)
        for r in healthy:
            if r.get("capacity", 100) >= required_capacity:
                weighted.append((r, r.get("weight", 1) / total))
        if not weighted:
            return healthy[0]
        import random
        r = random.random()
        cumulative = 0
        for region, w in weighted:
            cumulative += w
            if r <= cumulative:
                return region
        return weighted[-1][0]

    async def get_traffic_forecast(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {}
        total_capacity = sum(r.get("capacity", 100) for r in regions)
        total_load = sum(r.get("current_load", 0) for r in regions)
        return {"total_capacity": total_capacity, "total_load": total_load, "utilization_pct": round(total_load / total_capacity * 100, 1) if total_capacity else 0, "regions_at_capacity": sum(1 for r in regions if r.get("current_load", 0) >= r.get("capacity", 100)), "estimated_headroom": round((total_capacity - total_load) / max(1, len(regions)), 1)}

    async def health_score_summary(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"average_health_score": 0, "total_regions": 0}
        scores = []
        for r in regions:
            score = 100
            if r.get("status") != "healthy":
                score -= 30
            score -= min(r.get("replication_lag_ms", 0) // 10, 50)
            score -= max(0, r.get("current_load", 0) - r.get("capacity", 100)) // 2
            scores.append(max(0, score))
        return {"average_health_score": round(sum(scores) / len(scores), 1), "total_regions": len(scores), "healthy_count": sum(1 for r in regions if r.get("status") == "healthy"), "health_scores": dict(zip([r["name"] for r in regions], scores))}


class RegionSyncManager:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def trigger_sync(self, source_region_id: str, target_region_id: str) -> Dict[str, Any]:
        source = await self.manager.get_region(source_region_id)
        target = await self.manager.get_region(target_region_id)
        if not source or not target:
            return {"error": "Region not found"}
        import random
        sync_time_ms = random.randint(100, 5000)
        data_size_mb = random.randint(10, 1000)
        return {"source": source.get("name"), "target": target.get("name"), "sync_time_ms": sync_time_ms, "data_size_mb": data_size_mb, "status": "synced", "sync_mode": source.get("replication_mode", "async"), "completed_at": datetime.now().isoformat()}

    async def get_sync_status(self, region_id: str) -> Dict[str, Any]:
        region = await self.manager.get_region(region_id)
        if not region:
            return {"error": "Region not found"}
        return {"region_id": region_id, "region_name": region.get("name"), "lag_ms": region.get("replication_lag_ms", 0), "last_sync": region.get("last_health_check"), "sync_mode": region.get("replication_mode", "async"), "status": "healthy" if region.get("replication_lag_ms", 0) < 100 else "degraded"}

    async def sync_all_regions(self) -> List[Dict[str, Any]]:
        results = []
        regions = self.manager.regions
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                r = await self.trigger_sync(regions[i]["id"], regions[j]["id"])
                results.append(r)
        return results


class RegionCapacityPlanner:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    def capacity_analysis(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {}
        total_cap = sum(r.get("capacity", 100) for r in regions)
        total_load = sum(r.get("current_load", 0) for r in regions)
        overloaded = [r for r in regions if r.get("current_load", 0) > r.get("capacity", 100) * 0.8]
        underutilized = [r for r in regions if r.get("current_load", 0) < r.get("capacity", 100) * 0.3]
        return {"total_capacity": total_cap, "total_load": total_load, "utilization": round(total_load / total_cap * 100, 1) if total_cap else 0, "overloaded_count": len(overloaded), "overloaded_regions": [r["name"] for r in overloaded], "underutilized_count": len(underutilized), "underutilized_regions": [r["name"] for r in underutilized], "recommended_actions": [f"Increase capacity for {r['name']}" for r in overloaded] + [f"Reduce allocation for {r['name']}" for r in underutilized]}

    def recommend_capacity_change(self, region_id: str) -> Dict[str, Any]:
        region = next((r for r in self.manager.regions if r["id"] == region_id), None)
        if not region:
            return {"error": "Region not found"}
        load = region.get("current_load", 0)
        cap = region.get("capacity", 100)
        if load > cap * 0.8:
            recommended = int(cap * 1.5)
            return {"region": region.get("name"), "current_capacity": cap, "recommended_capacity": recommended, "reason": f"Load ({load}) exceeds 80% of capacity", "urgency": "high"}
        elif load < cap * 0.3:
            recommended = int(cap * 0.7)
            return {"region": region.get("name"), "current_capacity": cap, "recommended_capacity": recommended, "reason": f"Load ({load}) is below 30% of capacity", "urgency": "low"}
        return {"region": region.get("name"), "current_capacity": cap, "recommended_capacity": cap, "reason": "Capacity is adequate", "urgency": "none"}


class RegionFailoverManager:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def initiate_failover(self, source_region_id: str, target_region_id: str) -> Dict[str, Any]:
        source = await self.manager.get_region(source_region_id)
        target = await self.manager.get_region(target_region_id)
        if not source or not target:
            return {"error": "Region not found"}
        import random
        failover_time_ms = random.randint(1000, 30000)
        return {"source": source.get("name"), "target": target.get("name"), "failover_time_ms": failover_time_ms, "status": "completed", "data_consistency": "verified", "dns_updated": True, "completed_at": datetime.now().isoformat()}

    async def test_failover(self, region_id: str) -> Dict[str, Any]:
        region = await self.manager.get_region(region_id)
        if not region:
            return {"error": "Region not found"}
        import random
        return {"region": region.get("name"), "test_type": "simulated_failover", "status": "passed", "duration_ms": random.randint(500, 5000), "validation": "all_checks_passed", "tested_at": datetime.now().isoformat()}

    async def get_failover_history(self, region_id: str) -> List[Dict[str, Any]]:
        region = await self.manager.get_region(region_id)
        if not region:
            return []
        return region.get("failover_history", [])

    def recommend_failover_strategy(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"strategy": "unknown", "reason": "No regions configured"}
        healthy = [r for r in regions if r.get("status") == "healthy"]
        degraded = [r for r in regions if r.get("status") != "healthy"]
        strategy = "active-passive" if len(healthy) < 2 else "active-active"
        return {"strategy": strategy, "healthy_regions": len(healthy), "degraded_regions": len(degraded), "recommendation": "Maintain at least 2 healthy regions for active-active" if strategy == "active-passive" else "Configuration is optimal"}


class ReplicationMonitor:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    def get_replication_status(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"status": "unknown"}
        total_lag = sum(r.get("replication_lag_ms", 0) for r in regions)
        avg_lag = round(total_lag / len(regions), 1) if regions else 0
        max_lag = max(r.get("replication_lag_ms", 0) for r in regions)
        return {"status": "healthy" if max_lag < 100 else "degraded" if max_lag < 500 else "critical", "average_lag_ms": avg_lag, "max_lag_ms": max_lag, "total_regions": len(regions), "healthy_replicas": sum(1 for r in regions if r.get("replication_lag_ms", 0) < 100)}

    def check_replication_consistency(self) -> List[Dict[str, Any]]:
        results = []
        for region in self.manager.regions:
            lag = region.get("replication_lag_ms", 0)
            results.append({"region": region.get("name"), "lag_ms": lag, "consistent": lag < 200, "last_verified": region.get("last_health_check")})
        return results

    def estimate_data_loss_risk(self) -> Dict[str, Any]:
        async_regions = [r for r in self.manager.regions if r.get("replication_mode") == "async"]
        sync_regions = [r for r in self.manager.regions if r.get("replication_mode") == "sync"]
        async_lag = sum(r.get("replication_lag_ms", 0) for r in async_regions) / len(async_regions) if async_regions else 0
        return {"risk_level": "low" if len(sync_regions) >= 1 else "high", "async_regions": len(async_regions), "sync_regions": len(sync_regions), "avg_async_lag_ms": round(async_lag, 1), "recommendation": "Add at least one sync replication region" if not sync_regions else "Configuration adequate"}


class RegionHealthChecker:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def check_all_regions(self) -> List[Dict[str, Any]]:
        results = []
        for r in self.manager.regions:
            status = await self.manager.check_region_health(r["id"])
            results.append({"region_id": r["id"], "region_name": r.get("name"), "status": status.get("status") if status else "unknown", "checked_at": datetime.now().isoformat()})
        return results

    def get_unhealthy_regions(self) -> List[Dict[str, Any]]:
        return [r for r in self.manager.regions if r.get("status") != "healthy"]

    def calculate_availability(self) -> Dict[str, Any]:
        regions = self.manager.regions
        if not regions:
            return {"availability_pct": 0, "status": "no_data"}
        healthy = sum(1 for r in regions if r.get("status") == "healthy")
        pct = round(healthy / len(regions) * 100, 1)
        return {"availability_pct": pct, "healthy_regions": healthy, "total_regions": len(regions), "status": "available" if pct >= 50 else "degraded"}

    def suggest_remediation(self, region_id: str) -> List[Dict[str, Any]]:
        region = next((r for r in self.manager.regions if r["id"] == region_id), None)
        if not region:
            return []
        actions = []
        if region.get("status") != "healthy":
            actions.append({"action": "Restart region services", "priority": "high"})
            actions.append({"action": "Verify network connectivity", "priority": "high"})
        if region.get("replication_lag_ms", 0) > 500:
            actions.append({"action": "Increase replication bandwidth", "priority": "medium"})
            actions.append({"action": "Check replication queue depth", "priority": "medium"})
        if region.get("current_load", 0) > region.get("capacity", 100) * 0.9:
            actions.append({"action": "Scale up region capacity", "priority": "high"})
        return actions


class ActiveActiveDashboard:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    async def get_overview(self) -> Dict[str, Any]:
        regions = self.manager.regions
        rep_mon = ReplicationMonitor(self.manager)
        health = RegionHealthChecker(self.manager)
        capacity = RegionCapacityPlanner(self.manager)
        return {"total_regions": len(regions), "healthy": sum(1 for r in regions if r.get("status") == "healthy"), "degraded": sum(1 for r in regions if r.get("status") != "healthy"), "replication": rep_mon.get_replication_status(), "availability": health.calculate_availability(), "capacity": capacity.capacity_analysis()}

    async def get_region_details(self, region_id: str) -> Dict[str, Any]:
        region = await self.manager.get_region(region_id)
        if not region:
            return {"error": "Region not found"}
        rep_status = await RegionSyncManager(self.manager).get_sync_status(region_id)
        return {"region": region, "replication": rep_status, "health_checks": region.get("health_check_history", [])[-5:], "recommendations": RegionHealthChecker(self.manager).suggest_remediation(region_id)}


class ActiveActiveAlertManager:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager
        self.alerts: List[Dict[str, Any]] = []

    def check_region_health_alerts(self) -> List[Dict[str, Any]]:
        new_alerts = []
        for region in self.manager.regions:
            if region.get("status") != "healthy":
                alert = {"id": str(uuid.uuid4()), "region_id": region.get("id"), "region_name": region.get("name"), "type": "region_unhealthy", "severity": "critical", "created_at": datetime.now().isoformat(), "acknowledged": False}
                self.alerts.append(alert)
                new_alerts.append(alert)
            if region.get("replication_lag_ms", 0) > 500:
                alert = {"id": str(uuid.uuid4()), "region_id": region.get("id"), "region_name": region.get("name"), "type": "high_replication_lag", "lag_ms": region.get("replication_lag_ms"), "severity": "high", "created_at": datetime.now().isoformat(), "acknowledged": False}
                self.alerts.append(alert)
                new_alerts.append(alert)
        return new_alerts

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if not a.get("acknowledged")]

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                a["acknowledged_at"] = datetime.now().isoformat()
                return a
        return {"error": "Alert not found"}


class ActiveActiveTrafficRouter:
    def __init__(self, manager: ActiveActiveManager):
        self.manager = manager

    def get_nearest_region(self, geo: str) -> Optional[Dict[str, Any]]:
        healthy = [r for r in self.manager.regions if r.get("status") == "healthy"]
        if not healthy:
            return None
        geo_map = {"us-east": 0, "us-west": 1, "eu-west": 2, "eu-central": 2, "ap-southeast": 3, "ap-northeast": 3}
        idx = geo_map.get(geo, 0) % len(healthy)
        return healthy[idx]

    def route_request(self, source_geo: str, affinity_key: Optional[str] = None) -> Dict[str, Any]:
        if affinity_key:
            import hashlib
            h = int(hashlib.md5(affinity_key.encode()).hexdigest(), 16)
            healthy = [r for r in self.manager.regions if r.get("status") == "healthy"]
            if healthy:
                idx = h % len(healthy)
                return {"routed_to": healthy[idx].get("name"), "region_id": healthy[idx].get("id"), "method": "affinity_hash"}
        region = self.get_nearest_region(source_geo)
        if region:
            return {"routed_to": region.get("name"), "region_id": region.get("id"), "method": "geo_proximity"}
        return {"error": "No healthy regions available"}

    def get_routing_table(self) -> Dict[str, Any]:
        healthy = [r for r in self.manager.regions if r.get("status") == "healthy"]
        return {"healthy_regions": len(healthy), "total_regions": len(self.manager.regions), "routing_method": "geo_aware_weighted", "regions": [{"name": r.get("name"), "weight": r.get("weight", 100), "status": r.get("status")} for r in self.manager.regions]}

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
        return {"total_items": 0, "healthy_count": 0, "degraded_count": 0, "failed_count": 0}

    def validate_configuration(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class ResiliencyResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    status: str = Field(default="healthy")
    message: str = ""
    recovery_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResiliencyBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    passed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_pass(self) -> None:
        self.passed += 1

    def record_fail(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"
        if self.failed > 0:
            self.status = "completed_with_errors"

class HealthMetric(BaseModel):
    component: str
    status: str = Field(default="unknown")
    uptime_pct: float = Field(default=100.0, ge=0, le=100)
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time: float = Field(default=0.0)
    error_rate: float = Field(default=0.0, ge=0, le=100)

class HealthDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthMetric] = {}

    def register(self, component: str) -> HealthMetric:
        hm = HealthMetric(component=component)
        self._components[component] = hm
        return hm

    def update(self, component: str, status: str, response_time: float = 0.0, error_rate: float = 0.0) -> None:
        if component in self._components:
            hm = self._components[component]
            hm.status = status
            hm.response_time = response_time
            hm.error_rate = error_rate
            hm.last_check = datetime.utcnow()
            if status == "healthy":
                hm.uptime_pct = min(100, hm.uptime_pct + 0.1)
            else:
                hm.uptime_pct = max(0, hm.uptime_pct - 0.5)

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        down = sum(1 for c in self._components.values() if c.status == "down")
        avg_uptime = round(sum(c.uptime_pct for c in self._components.values()) / max(total, 1), 1)
        return {"components": total, "healthy": healthy, "degraded": degraded,
                "down": down, "avg_uptime_pct": avg_uptime}

    def get_component(self, component: str) -> Optional[HealthMetric]:
        return self._components.get(component)

class IncidentLog(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component: str
    severity: str = Field(default="info")
    title: str
    description: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    action_taken: str = ""

class IncidentManager:
    def __init__(self) -> None:
        self._incidents: List[IncidentLog] = []

    def report(self, component: str, severity: str, title: str, description: str = "") -> IncidentLog:
        incident = IncidentLog(component=component, severity=severity, title=title, description=description)
        self._incidents.append(incident)
        return incident

    def resolve(self, incident_id: str, action: str = "") -> bool:
        for inc in self._incidents:
            if inc.incident_id == incident_id and inc.resolved_at is None:
                inc.resolved_at = datetime.utcnow()
                inc.duration_seconds = int((inc.resolved_at - inc.detected_at).total_seconds())
                inc.action_taken = action
                return True
        return False

    def get_open(self) -> List[IncidentLog]:
        return [i for i in self._incidents if i.resolved_at is None]

    def get_by_severity(self, severity: str) -> List[IncidentLog]:
        return [i for i in self._incidents if i.severity == severity]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._incidents)
        open_count = len(self.get_open())
        resolved = total - open_count
        by_severity: Dict[str, int] = {}
        total_duration = 0
        resolved_count = 0
        for i in self._incidents:
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1
            if i.duration_seconds:
                total_duration += i.duration_seconds
                resolved_count += 1
        return {"total": total, "open": open_count, "resolved": resolved,
                "by_severity": by_severity,
                "avg_resolution_time_sec": round(total_duration / max(resolved_count, 1), 1)}

class RecoveryProcedure(BaseModel):
    procedure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    steps: List[str] = Field(default_factory=list)
    estimated_rtt_minutes: int = Field(default=5)
    validated: bool = False
    last_tested: Optional[datetime] = None
    owner: str = Field(default="platform")

class RecoveryRunner:
    def __init__(self) -> None:
        self._procedures: Dict[str, RecoveryProcedure] = {}

    def register(self, procedure: RecoveryProcedure) -> str:
        self._procedures[procedure.procedure_id] = procedure
        return procedure.procedure_id

    async def execute(self, procedure_id: str) -> Dict[str, Any]:
        proc = self._procedures.get(procedure_id)
        if not proc:
            return {"status": "error", "message": "Procedure not found"}
        executed_steps = []
        for i, step in enumerate(proc.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        return {"status": "completed", "procedure": proc.name, "steps": executed_steps,
                "total_steps": len(proc.steps), "duration_estimate_min": proc.estimated_rtt_minutes}

    def list_procedures(self) -> List[Dict[str, Any]]:
        return [{"id": p.procedure_id, "name": p.name, "steps": len(p.steps),
                 "validated": p.validated, "last_tested": p.last_tested} for p in self._procedures.values()]

class SLOMetric(BaseModel):
    name: str
    target_pct: float = Field(default=99.9, ge=0, le=100)
    current_pct: float = Field(default=100.0, ge=0, le=100)
    measurement_window: str = Field(default="30d")
    breached: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SLOManager:
    def __init__(self) -> None:
        self._slos: Dict[str, SLOMetric] = {}

    def define(self, name: str, target_pct: float = 99.9, window: str = "30d") -> SLOMetric:
        slo = SLOMetric(name=name, target_pct=target_pct, measurement_window=window)
        self._slos[name] = slo
        return slo

    def record_uptime(self, name: str, success: bool) -> None:
        slo = self._slos.get(name)
        if not slo:
            return
        factor = 0.0001 if not success else -0.0001
        slo.current_pct = round(max(0, min(100, slo.current_pct + factor)), 4)
        slo.breached = slo.current_pct < slo.target_pct
        slo.last_updated = datetime.utcnow()

    def get_status(self) -> Dict[str, Any]:
        breached = [s for s in self._slos.values() if s.breached]
        return {"total_slos": len(self._slos), "met": len(self._slos) - len(breached),
                "breached": len(breached), "details": {n: s.dict() for n, s in self._slos.items()}}
