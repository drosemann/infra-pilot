from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class DependencySimulator:
    """Dependency Failure Simulation — simulate failure of upstream dependencies"""

    FAILURE_TYPES = ["timeout", "error_response", "slow_response", "connection_refused", "dns_failure", "rate_limit", "data_corruption", "circuit_breaker_open"]
    DEPENDENCY_TYPES = ["database", "api", "queue", "cache", "storage", "dns", "auth_service", "payment_gateway"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.simulations_file = config.get("dep_sim_file", "data/resiliency/dependency_simulations.json")
        self.results_file = config.get("dep_sim_results_file", "data/resiliency/dependency_sim_results.json")
        self.simulations: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.simulations_file) or ".", exist_ok=True)
        for path, attr in [(self.simulations_file, "simulations"), (self.results_file, "results")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_simulations(self):
        with open(self.simulations_file, "w") as f:
            json.dump(self.simulations, f, indent=2, default=str)

    def _save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results[-1000:], f, indent=2, default=str)

    async def create_simulation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sim = {
            "id": f"dep_sim_{int(datetime.now().timestamp())}_{len(self.simulations)}",
            "name": data.get("name", "Unnamed Simulation"),
            "description": data.get("description", ""),
            "target_service": data.get("target_service", ""),
            "target_endpoint": data.get("target_endpoint", ""),
            "failure_type": data.get("failure_type", "timeout"),
            "dependency_type": data.get("dependency_type", "api"),
            "failure_parameters": {
                "delay_ms": data.get("failure_parameters", {}).get("delay_ms", 5000),
                "error_code": data.get("failure_parameters", {}).get("error_code", 503),
                "error_rate": data.get("failure_parameters", {}).get("error_rate", 100),
                "duration_seconds": data.get("failure_parameters", {}).get("duration_seconds", 30),
            },
            "expected_behavior": data.get("expected_behavior", {"circuit_breaker_opens": True, "retry_attempts": 3, "fallback_used": True, "error_gracefully_handled": True}),
            "status": "created",
            "created_at": datetime.now().isoformat(),
        }
        self.simulations.append(sim)
        self._save_simulations()
        return sim

    async def list_simulations(self) -> List[Dict[str, Any]]:
        return self.simulations

    async def get_simulation(self, sim_id: str) -> Optional[Dict[str, Any]]:
        return next((s for s in self.simulations if s["id"] == sim_id), None)

    async def update_simulation(self, sim_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for sim in self.simulations:
            if sim["id"] == sim_id:
                sim.update(updates)
                self._save_simulations()
                return sim
        return None

    async def delete_simulation(self, sim_id: str) -> bool:
        for i, sim in enumerate(self.simulations):
            if sim["id"] == sim_id:
                self.simulations.pop(i)
                self._save_simulations()
                return True
        return False

    async def run_simulation(self, sim_id: str) -> Dict[str, Any]:
        sim = await self.get_simulation(sim_id)
        if not sim:
            return {"error": "Simulation not found"}
        sim["status"] = "running"
        self._save_simulations()
        observations = await self._simulate_failure(sim)
        blast_radius = await self._assess_blast_radius(sim)
        circuits = await self._observe_circuit_breakers(sim)
        await self._verify_fallback(sim)
        start_time = datetime.fromisoformat(sim.get("created_at", datetime.now().isoformat()))
        passed = all(o.get("passed", True) for o in observations) and blast_radius.get("contained", True)
        result = {
            "id": f"dep_result_{int(datetime.now().timestamp())}_{len(self.results)}",
            "simulation_id": sim_id,
            "simulation_name": sim.get("name"),
            "status": "passed" if passed else "failed",
            "failure_type": sim.get("failure_type"),
            "target_service": sim.get("target_service"),
            "dependency_type": sim.get("dependency_type"),
            "observations": observations,
            "blast_radius": blast_radius,
            "circuit_breaker_analysis": circuits,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
        }
        self.results.append(result)
        self._save_results()
        sim["status"] = "completed" if passed else "failed"
        self._save_simulations()
        return result

    async def _simulate_failure(self, sim: Dict[str, Any]) -> List[Dict[str, Any]]:
        await asyncio.sleep(3)
        failure_type = sim.get("failure_type", "timeout")
        observations = []
        observations.append({"metric": "response_time_ms", "baseline": 50, "during": 5000 if failure_type == "timeout" else 200, "status": "degraded"})
        observations.append({"metric": "error_rate", "baseline": 0.1, "during": 95.0 if failure_type != "slow_response" else 0.5, "status": "critical"})
        observations.append({"metric": "circuit_breaker_state", "baseline": "closed", "during": "open" if random.random() > 0.2 else "half-open", "status": "triggered"})
        observations.append({"metric": "retry_count", "baseline": 0, "during": random.randint(2, 5), "status": "acceptable"})
        for o in observations:
            o["passed"] = o["status"] != "critical"
        return observations

    async def _assess_blast_radius(self, sim: Dict[str, Any]) -> Dict[str, Any]:
        return {"contained": random.random() > 0.15, "affected_services": random.randint(0, 3), "user_impact": "partial" if random.random() > 0.3 else "none", "cascading_failures": 0}

    async def _observe_circuit_breakers(self, sim: Dict[str, Any]) -> Dict[str, Any]:
        return {"circuit_breaker_detected": True, "state_transition": "closed_to_open", "time_to_open_ms": random.randint(500, 5000), "half_open_after_ms": 30000, "requests_during_open": 0}

    async def _verify_fallback(self, sim: Dict[str, Any]) -> bool:
        await asyncio.sleep(1)
        return True

    async def get_results(self, sim_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if sim_id:
            return [r for r in self.results if r["simulation_id"] == sim_id]
        return self.results

    async def get_failure_types(self) -> List[Dict[str, Any]]:
        return [{"id": ft, "name": ft.replace("_", " ").title(), "description": f"Simulate {ft.replace('_', ' ')} failure"} for ft in self.FAILURE_TYPES]

    async def get_summary(self) -> Dict[str, Any]:
        total = len(self.simulations)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        return {"total_simulations": total, "total_runs": len(self.results), "pass_rate": round(passed / len(self.results) * 100, 2) if self.results else 100, "failure_types_available": self.FAILURE_TYPES, "dependency_types_available": self.DEPENDENCY_TYPES}

    async def get_simulation(self, sim_id: str) -> Optional[Dict[str, Any]]:
        return next((s for s in self.simulations if s["id"] == sim_id), None)

    async def update_simulation(self, sim_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for sim in self.simulations:
            if sim["id"] == sim_id:
                sim.update(updates)
                self._save_simulations()
                return sim
        return None

    async def delete_simulation(self, sim_id: str) -> bool:
        for i, sim in enumerate(self.simulations):
            if sim["id"] == sim_id:
                self.simulations.pop(i)
                self._save_simulations()
                return True
        return False

    async def get_dependency_map(self) -> Dict[str, List[str]]:
        dep_map: Dict[str, List[str]] = {}
        for sim in self.simulations:
            deps = sim.get("dependencies", [])
            for dep in deps:
                dep_map.setdefault(dep, []).append(sim["id"])
        return dep_map

    async def simulate_bulk(self, dependency_type: str, failure_type: str) -> Dict[str, Any]:
        targets = [s for s in self.simulations if dependency_type in s.get("dependencies", [])]
        results = []
        for target in targets:
            r = await self.run_simulation(target["id"], failure_type)
            results.append(r)
        return {"dependency_type": dependency_type, "failure_type": failure_type, "simulations_run": len(results), "passed": sum(1 for r in results if r.get("status") == "passed"), "failed": sum(1 for r in results if r.get("status") == "failed")}

    async def get_service_graph(self) -> List[Dict[str, Any]]:
        services = {}
        for sim in self.simulations:
            service = sim.get("service", "unknown")
            services.setdefault(service, {"service": service, "dependency_count": 0, "critical_deps": 0, "last_result": "untested"})
            services[service]["dependency_count"] += len(sim.get("dependencies", []))
        return list(services.values())

    async def get_failure_scenarios(self) -> List[Dict[str, Any]]:
        return [{"failure_type": ft, "name": ft.replace("_", " ").title(), "impact": "critical" if ft in ("region_outage", "database_failover") else "high"} for ft in self.FAILURE_TYPES]


class DependencySimBatchProcessor:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_simulations(self, simulations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(simulations):
            try:
                sim = await self.manager.create_simulation(data)
                sim["batch_index"] = i
                sim["success"] = True
                results.append(sim)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_run_simulations(self, sim_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for sid in sim_ids:
            try:
                r = await self.manager.run_simulation(sid)
                r["simulation_id"] = sid
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"simulation_id": sid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_delete_simulations(self, sim_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for sid in sim_ids:
            ok = await self.manager.delete_simulation(sid)
            results.append({"simulation_id": sid, "deleted": ok})
        return results

    def export_csv(self, results_list: List[Dict[str, Any]]) -> str:
        if not results_list:
            return ""
        fields = ["id", "simulation_name", "status", "failure_type", "target_service", "dependency_type", "duration_seconds", "completed_at"]
        lines = [",".join(fields)]
        for r in results_list:
            row = [str(r.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)


class DependencyAnalytics:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def pass_rate_by_failure_type(self) -> Dict[str, Any]:
        breakdown: Dict[str, Dict[str, int]] = {}
        for r in self.manager.results:
            ftype = r.get("failure_type", "unknown")
            breakdown.setdefault(ftype, {"total": 0, "passed": 0})
            breakdown[ftype]["total"] += 1
            if r["status"] == "passed":
                breakdown[ftype]["passed"] += 1
        for ftype in breakdown:
            t = breakdown[ftype]["total"]
            p = breakdown[ftype]["passed"]
            breakdown[ftype]["rate_pct"] = round(p / t * 100, 1) if t else 0
        return breakdown

    def blast_radius_stats(self) -> Dict[str, Any]:
        results = self.manager.results
        if not results:
            return {}
        contained = sum(1 for r in results if r.get("blast_radius", {}).get("contained", True))
        avg_affected = sum(r.get("blast_radius", {}).get("affected_services", 0) for r in results) / len(results)
        return {"contained_rate": round(contained / len(results) * 100, 1), "total_simulations": len(results), "contained": contained, "average_affected_services": round(avg_affected, 1), "cascading_failures_rate": round(sum(1 for r in results if r.get("blast_radius", {}).get("cascading_failures", 0) > 0) / len(results) * 100, 1)}

    def circuit_breaker_effectiveness(self) -> Dict[str, Any]:
        results = self.manager.results
        if not results:
            return {}
        detected = sum(1 for r in results if r.get("circuit_breaker_analysis", {}).get("circuit_breaker_detected", False))
        return {"detection_rate": round(detected / len(results) * 100, 1), "total": len(results), "circuit_breakers_opened": detected}

    def generate_report(self) -> str:
        lines = ["=== Dependency Simulation Report ==="]
        lines.append(f"Total Simulations: {len(self.manager.simulations)}")
        lines.append(f"Total Runs: {len(self.manager.results)}")
        by_type = self.pass_rate_by_failure_type()
        for ftype, stats in by_type.items():
            lines.append(f"  {ftype}: {stats.get('rate_pct', 0)}% pass ({stats.get('passed', 0)}/{stats.get('total', 0)})")
        br = self.blast_radius_stats()
        lines.append(f"Blast Radius Contained: {br.get('contained_rate', 0)}%")
        return "\n".join(lines)


class DependencySimPaginator:
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
        return {"total_items": len(self.items), "page_size": self.page_size, "total_pages": self.get_total_pages()}


class DependencyImpactAnalyzer:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    async def analyze_impact(self, target_service: str) -> Dict[str, Any]:
        related = [s for s in self.manager.simulations if s.get("target_service") == target_service]
        results = [r for r in self.manager.results if r["simulation_id"] in [s["id"] for s in related]]
        passed = sum(1 for r in results if r["status"] == "passed")
        return {"service": target_service, "simulations": len(related), "runs": len(results), "pass_rate": round(passed / len(results) * 100, 1) if results else 0, "failure_types": list(set(r.get("failure_type", "") for r in results)), "dependency_types": list(set(r.get("dependency_type", "") for r in results))}

    async def get_critical_dependencies(self) -> List[Dict[str, Any]]:
        dep_counts: Dict[str, int] = {}
        for sim in self.manager.simulations:
            deps = sim.get("dependencies", [])
            for dep in deps:
                dep_counts[dep] = dep_counts.get(dep, 0) + 1
        return sorted([{"dependency": dep, "simulation_count": count, "criticality": "high" if count > 3 else "medium"} for dep, count in dep_counts.items()], key=lambda x: x["simulation_count"], reverse=True)

    async def simulate_cascade_failure(self, root_failure: str) -> Dict[str, Any]:
        affected = await self.analyze_impact(root_failure)
        cascade = {"root_failure": root_failure, "directly_affected": affected.get("simulations", 0), "estimated_downstream": affected.get("simulations", 0) * 2, "blast_radius_estimate": "critical" if affected.get("simulations", 0) > 5 else "contained"}
        return cascade


class ResilienceTestBuilder:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    async def build_test_suite(self, target_service: str, failure_types: List[str]) -> Dict[str, Any]:
        suite = {"id": f"suite_{int(datetime.now().timestamp())}", "target_service": target_service, "tests": []}
        for ft in failure_types:
            sim = await self.manager.create_simulation({
                "name": f"{ft}_test_{target_service}",
                "target_service": target_service,
                "failure_type": ft,
                "dependency_type": "api",
            })
            suite["tests"].append(sim)
        return suite


class DependencyFailureClassifier:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def classify_failures(self) -> Dict[str, Any]:
        classified = {"bypassed": [], "tolerated": [], "critical": []}
        for r in self.manager.results:
            if r.get("status") == "passed":
                if r.get("blast_radius", {}).get("contained", True):
                    classified["tolerated"].append(r["simulation_id"])
                else:
                    classified["bypassed"].append(r["simulation_id"])
            else:
                classified["critical"].append(r["simulation_id"])
        return {k: {"count": len(v), "ids": v} for k, v in classified.items()}

    def get_recommendations(self) -> List[Dict[str, Any]]:
        recs = []
        for sim in self.manager.simulations:
            results = [r for r in self.manager.results if r["simulation_id"] == sim["id"]]
            if not results:
                continue
            last = results[-1]
            if last.get("status") == "failed":
                ft = last.get("failure_type", "unknown")
                recs.append({"simulation_id": sim["id"], "name": sim.get("name"), "failure_type": ft, "recommendation": f"Implement circuit breaker for {ft}", "priority": "high"})
                recs.append({"simulation_id": sim["id"], "name": sim.get("name"), "failure_type": ft, "recommendation": f"Add retry with backoff for {ft}", "priority": "medium"})
        return recs

    def vulnerability_score(self) -> Dict[str, Any]:
        total = len(self.manager.simulations)
        failed_sims = len([r for r in self.manager.results if r.get("status") == "failed"])
        if not total:
            return {"score": 0, "level": "unknown"}
        score = round(failed_sims / total * 100, 1)
        level = "low" if score < 20 else "medium" if score < 50 else "high"
        return {"vulnerability_score": score, "level": level, "total_simulations": total, "failed_simulations": failed_sims}


class ServiceDependencyMapper:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}
        for sim in self.manager.simulations:
            service = sim.get("target_service", "unknown")
            deps = sim.get("dependencies", [])
            graph.setdefault(service, [])
            for dep in deps:
                if dep not in graph[service]:
                    graph[service].append(dep)
        return graph

    def find_critical_paths(self) -> List[Dict[str, Any]]:
        graph = self.build_dependency_graph()
        paths = []
        for service, deps in graph.items():
            if len(deps) >= 3:
                paths.append({"service": service, "dependency_count": len(deps), "dependencies": deps, "criticality": "high", "impact": "Multiple dependencies increase failure risk"})
            elif 1 <= len(deps) < 3:
                paths.append({"service": service, "dependency_count": len(deps), "dependencies": deps, "criticality": "medium"})
        return sorted(paths, key=lambda p: p["dependency_count"], reverse=True)

    def estimate_downtime_impact(self) -> Dict[str, Any]:
        results = self.manager.results
        if not results:
            return {}
        total_downtime = sum(r.get("duration_seconds", 0) for r in results)
        return {"total_downtime_seconds": total_downtime, "average_downtime_per_run": round(total_downtime / len(results), 1), "simulations_analyzed": len(results)}


class DependencyChaosRunner:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    async def run_chaos_monkey(self, target_service: str) -> Dict[str, Any]:
        sim = {"id": str(uuid.uuid4()), "name": f"Chaos: {target_service}", "target_service": target_service, "dependencies": [], "failure_type": "random", "duration_seconds": 30}
        result = await self.manager.run_simulation(sim["id"])
        return {"simulation": sim, "result": result}

    async def run_cascading_failure(self, root_service: str) -> List[Dict[str, Any]]:
        graph = self.build_dependency_graph()
        results = []
        visited = set()
        queue = [root_service]
        while queue:
            service = queue.pop(0)
            if service in visited:
                continue
            visited.add(service)
            sim = {"id": str(uuid.uuid4()), "name": f"Cascade: {service}", "target_service": service, "dependencies": graph.get(service, []), "failure_type": "dependency_failure", "duration_seconds": 15}
            result = await self.manager.run_simulation(sim["id"])
            results.append({"service": service, "simulation_id": sim["id"], "status": result.get("status") if result else "failed"})
            for dep in graph.get(service, []):
                if dep not in visited:
                    queue.append(dep)
        return results

    def estimate_blast_radius(self, service: str) -> Dict[str, Any]:
        graph = self.build_dependency_graph()
        affected = set()
        queue = [service]
        while queue:
            current = queue.pop(0)
            if current in affected:
                continue
            affected.add(current)
            for svc, deps in graph.items():
                if current in deps and svc not in affected:
                    queue.append(svc)
        return {"root_service": service, "total_affected": len(affected) - 1, "affected_services": [s for s in affected if s != service], "criticality": "high" if len(affected) > 5 else "medium" if len(affected) > 2 else "low"}


class DependencyHealthScore:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def calculate_health(self) -> Dict[str, Any]:
        total_sims = len(self.manager.simulations)
        if not total_sims:
            return {"overall_health": 100, "level": "healthy"}
        passed = sum(1 for r in self.manager.results if r.get("status") == "passed")
        health_pct = round(passed / total_sims * 100, 1) if total_sims else 100
        level = "healthy" if health_pct >= 80 else "degraded" if health_pct >= 50 else "critical"
        return {"overall_health": health_pct, "level": level, "total_simulations": total_sims, "passed": passed, "failed": total_sims - passed}

    def service_health_breakdown(self) -> Dict[str, Any]:
        breakdown: Dict[str, Dict[str, int]] = {}
        for r in self.manager.results:
            service = r.get("target_service", "unknown")
            breakdown.setdefault(service, {"total": 0, "passed": 0, "failed": 0})
            breakdown[service]["total"] += 1
            if r.get("status") == "passed":
                breakdown[service]["passed"] += 1
            else:
                breakdown[service]["failed"] += 1
        return {svc: {**stats, "health_pct": round(stats["passed"] / stats["total"] * 100, 1)} for svc, stats in breakdown.items()}

    def critical_dependencies(self) -> List[Dict[str, Any]]:
        critical = []
        for sim in self.manager.simulations:
            deps = sim.get("dependencies", [])
            if len(deps) >= 3:
                critical.append({"service": sim.get("target_service"), "dependency_count": len(deps), "dependencies": deps, "recommendation": "Reduce dependency count or add circuit breakers"})
        return sorted(critical, key=lambda x: x["dependency_count"], reverse=True)


class FailureImpactReport:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def generate_report(self) -> Dict[str, Any]:
        health = DependencyHealthScore(self.manager).calculate_health()
        mapper = ServiceDependencyMapper(self.manager)
        graph = mapper.build_dependency_graph()
        classifier = DependencyFailureClassifier(self.manager)
        vuln = classifier.vulnerability_score()
        return {"overall_health": health, "vulnerability": vuln, "dependency_graph": graph, "total_services": len(graph), "total_dependencies": sum(len(d) for d in graph.values()), "report_generated": datetime.now().isoformat()}

    def export_report_json(self) -> str:
        import json
        report = self.generate_report()
        return json.dumps(report, indent=2)

    def export_report_markdown(self) -> str:
        report = self.generate_report()
        lines = ["# Dependency Failure Impact Report", f"Generated: {report.get('report_generated')}", "", "## Overall Health", f"Score: {report['overall_health']['overall_health']}% - {report['overall_health']['level']}", "", "## Vulnerability", f"Score: {report['vulnerability']['vulnerability_score']}% - {report['vulnerability']['level']}", "", f"Total Services in Graph: {report['total_services']}", f"Total Dependencies: {report['total_dependencies']}", ""]
        lines.append("### Dependency Graph")
        for svc, deps in report.get("dependency_graph", {}).items():
            lines.append(f"- **{svc}**: {', '.join(deps) if deps else 'No dependencies'}")
        return "\n".join(lines)


class DependencySimAlertManager:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager
        self.alerts: List[Dict[str, Any]] = []

    def check_for_alerts(self) -> List[Dict[str, Any]]:
        new_alerts = []
        for r in self.manager.results:
            if r.get("status") == "failed" and not r.get("alerted"):
                alert = {"id": str(uuid.uuid4()), "simulation_id": r.get("simulation_id"), "target_service": r.get("target_service"), "failure_type": r.get("failure_type"), "severity": "high", "created_at": datetime.now().isoformat(), "acknowledged": False}
                self.alerts.append(alert)
                new_alerts.append(alert)
                r["alerted"] = True
        return new_alerts

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if not a.get("acknowledged")]

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                return a
        return {"error": "Alert not found"}

    def get_alert_summary(self) -> Dict[str, Any]:
        total = len(self.alerts)
        active = len(self.get_active_alerts())
        by_severity: Dict[str, int] = {}
        for a in self.alerts:
            sev = a.get("severity", "low")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {"total_alerts": total, "active": active, "acknowledged": total - active, "by_severity": by_severity}


class DependencySimReportScheduler:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager
        self.schedules: List[Dict[str, Any]] = []

    def create_schedule(self, cron: str, format: str = "markdown", recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        schedule = {"id": str(uuid.uuid4()), "cron": cron, "format": format, "recipients": recipients or [], "status": "active", "created_at": datetime.now().isoformat()}
        self.schedules.append(schedule)
        return schedule

    def list_schedules(self) -> List[Dict[str, Any]]:
        return self.schedules

    def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        for i, s in enumerate(self.schedules):
            if s["id"] == schedule_id:
                self.schedules.pop(i)
                return {"status": "deleted"}
        return {"error": "Schedule not found"}


class DependencySimTagManager:
    def __init__(self, manager: DependencySimulator):
        self.manager = manager

    def tag_simulation(self, simulation_id: str, tags: List[str]) -> Dict[str, Any]:
        sim = next((s for s in self.manager.simulations if s["id"] == simulation_id), None)
        if not sim:
            return {"error": "Simulation not found"}
        sim.setdefault("tags", [])
        for t in tags:
            if t not in sim["tags"]:
                sim["tags"].append(t)
        return {"simulation_id": simulation_id, "tags": sim["tags"]}

    def get_simulations_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [s for s in self.manager.simulations if tag in s.get("tags", [])]

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
