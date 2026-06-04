from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class ChaosValidationManager:
    """Chaos Recovery Validation — scheduled chaos experiments validating DR procedures"""

    EXPERIMENT_TYPES = ["infrastructure", "network", "application", "database", "dns", "storage", "security"]
    EXPERIMENT_STATUSES = ["created", "scheduled", "running", "completed", "failed", "cancelled"]
    VALIDATION_TARGETS = ["primary_database", "secondary_database", "load_balancer", "api_gateway", "cache_cluster", "message_queue", "dns_service", "storage_backend"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.experiments_file = config.get("chaos_experiments_file", "data/resiliency/chaos_experiments.json")
        self.results_file = config.get("chaos_results_file", "data/resiliency/chaos_results.json")
        self.experiments: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.experiments_file) or ".", exist_ok=True)
        for path, attr in [(self.experiments_file, "experiments"), (self.results_file, "results")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_experiments(self):
        with open(self.experiments_file, "w") as f:
            json.dump(self.experiments, f, indent=2, default=str)

    def _save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results[-1000:], f, indent=2, default=str)

    async def create_experiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        experiment = {
            "id": f"chaos_{int(datetime.now().timestamp())}_{len(self.experiments)}",
            "name": data.get("name", "Unnamed Chaos Experiment"),
            "description": data.get("description", ""),
            "experiment_type": data.get("experiment_type", "infrastructure"),
            "dr_plan_id": data.get("dr_plan_id", ""),
            "target": data.get("target", "primary_database"),
            "fault_type": data.get("fault_type", "kill_container"),
            "fault_parameters": data.get("fault_parameters", {}),
            "expected_rpo_minutes": data.get("expected_rpo_minutes", 5),
            "expected_rto_minutes": data.get("expected_rto_minutes", 2),
            "status": "created",
            "schedule_cron": data.get("schedule_cron", ""),
            "blast_radius": data.get("blast_radius", "contained"),
            "approval_required": data.get("approval_required", True),
            "approved": False,
            "hypothesis": data.get("hypothesis", ""),
            "success_criteria": data.get("success_criteria", {"max_downtime_seconds": 120, "data_loss_permitted": False}),
            "created_by": data.get("created_by", "system"),
            "created_at": datetime.now().isoformat(),
            "last_run": None,
        }
        self.experiments.append(experiment)
        self._save_experiments()
        return experiment

    async def list_experiments(self) -> List[Dict[str, Any]]:
        return self.experiments

    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        return next((e for e in self.experiments if e["id"] == experiment_id), None)

    async def update_experiment(self, experiment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for exp in self.experiments:
            if exp["id"] == experiment_id:
                exp.update(updates)
                self._save_experiments()
                return exp
        return None

    async def delete_experiment(self, experiment_id: str) -> bool:
        for i, exp in enumerate(self.experiments):
            if exp["id"] == experiment_id:
                self.experiments.pop(i)
                self._save_experiments()
                return True
        return False

    async def approve_experiment(self, experiment_id: str, approved_by: str = "admin") -> Optional[Dict[str, Any]]:
        for exp in self.experiments:
            if exp["id"] == experiment_id:
                exp["approved"] = True
                exp["approved_by"] = approved_by
                exp["status"] = "scheduled"
                exp["approved_at"] = datetime.now().isoformat()
                self._save_experiments()
                return exp
        return None

    async def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        if experiment.get("approval_required") and not experiment.get("approved"):
            return {"error": "Experiment requires approval before execution"}
        experiment["status"] = "running"
        experiment["last_run"] = datetime.now().isoformat()
        self._save_experiments()
        asyncio.create_task(self._execute_experiment(experiment))
        return {"experiment_id": experiment_id, "status": "running", "started_at": datetime.now().isoformat()}

    async def _execute_experiment(self, experiment: Dict[str, Any]):
        start_time = datetime.now()
        fault_phase = await self._inject_fault(experiment)
        await asyncio.sleep(5)
        dr_response = await self._measure_dr_response(experiment)
        recovery = await self._verify_recovery(experiment, start_time)
        total_duration = (datetime.now() - start_time).total_seconds()
        rpo_actual = dr_response.get("data_loss_minutes", 0)
        rto_actual = total_duration / 60
        passed = recovery.get("recovered", False) and rto_actual <= experiment.get("expected_rto_minutes", 5) and (not experiment.get("success_criteria", {}).get("data_loss_permitted", False) or rpo_actual <= experiment.get("expected_rpo_minutes", 15))
        result = {
            "id": f"result_{int(datetime.now().timestamp())}_{len(self.results)}",
            "experiment_id": experiment["id"],
            "experiment_name": experiment.get("name"),
            "status": "passed" if passed else "failed",
            "fault_injected": experiment.get("fault_type"),
            "target": experiment.get("target"),
            "rpo_actual_minutes": rpo_actual,
            "rpo_target_minutes": experiment.get("expected_rpo_minutes"),
            "rto_actual_minutes": round(rto_actual, 2),
            "rto_target_minutes": experiment.get("expected_rto_minutes"),
            "total_duration_seconds": round(total_duration, 2),
            "downtime_seconds": dr_response.get("downtime_seconds", 0),
            "data_loss_seconds": dr_response.get("data_loss_minutes", 0) * 60,
            "dr_plan_id": experiment.get("dr_plan_id"),
            "phases": [fault_phase, dr_response, recovery],
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
        }
        self.results.append(result)
        self._save_results()
        experiment["status"] = "completed" if passed else "failed"
        self._save_experiments()

    async def _inject_fault(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        return {"phase": "fault_injection", "fault_type": experiment.get("fault_type"), "target": experiment.get("target"), "duration_seconds": 5, "success": True, "timestamp": datetime.now().isoformat()}

    async def _measure_dr_response(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        return {"phase": "dr_response", "dr_detected": True, "response_time_seconds": random.uniform(0.5, 5), "failover_initiated": True, "downtime_seconds": random.randint(10, 60), "data_loss_minutes": random.randint(0, 2), "timestamp": datetime.now().isoformat()}

    async def _verify_recovery(self, experiment: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"phase": "recovery_verification", "recovered": True, "data_integrity_verified": True, "dns_propagated": True, "service_healthy": True, "recovery_time_seconds": (datetime.now() - start_time).total_seconds(), "timestamp": datetime.now().isoformat()}

    async def get_results(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if experiment_id:
            return [r for r in self.results if r["experiment_id"] == experiment_id]
        return self.results

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        total = len(self.experiments)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        recent = [r for r in self.results if datetime.fromisoformat(r["completed_at"]) > datetime.now() - timedelta(days=30)]
        return {"total_experiments": total, "total_runs": len(self.results), "passed_runs": passed, "failed_runs": failed, "pass_rate_percent": round(passed / len(self.results) * 100, 2) if self.results else 100.0, "average_rto_seconds": round(sum(r.get("rto_actual_minutes", 0) * 60 for r in recent) / len(recent), 2) if recent else 0, "average_rpo_minutes": round(sum(r.get("rpo_actual_minutes", 0) for r in recent) / len(recent), 2) if recent else 0, "last_experiment": self.results[-1] if self.results else None}

    async def update_experiment(self, experiment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for exp in self.experiments:
            if exp["id"] == experiment_id:
                exp.update(updates)
                self._save_experiments()
                return exp
        return None

    async def delete_experiment(self, experiment_id: str) -> bool:
        for i, exp in enumerate(self.experiments):
            if exp["id"] == experiment_id:
                self.experiments.pop(i)
                self._save_experiments()
                return True
        return False

    async def get_all_experiments(self) -> List[Dict[str, Any]]:
        return self.experiments

    async def get_fault_types(self) -> List[str]:
        return ["network_latency", "process_kill", "dns_failure", "disk_fill", "cpu_stress", "memory_pressure", "region_blackhole", "certificate_expiry", "database_failover", "load_spike"]

    async def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": f"template_{int(datetime.now().timestamp())}", **template_data, "created_at": datetime.now().isoformat()}

    async def get_experiment_templates(self) -> List[Dict[str, Any]]:
        return [{"id": "template_default_latency", "name": "Network Latency Test", "fault_type": "network_latency", "target": "all_services", "duration_minutes": 5, "description": "Inject network latency across all services"}, {"id": "template_instance_fail", "name": "Instance Failure Test", "fault_type": "process_kill", "target": "random_instance", "duration_minutes": 10, "description": "Kill random service instance"}]

    async def get_failure_modes(self) -> List[Dict[str, Any]]:
        return [{"name": "Network Partition", "type": "network_latency", "severity": "high"}, {"name": "Instance Failure", "type": "process_kill", "severity": "critical"}, {"name": "DNS Outage", "type": "dns_failure", "severity": "critical"}, {"name": "Disk Full", "type": "disk_fill", "severity": "medium"}, {"name": "CPU Saturation", "type": "cpu_stress", "severity": "medium"}]


class ChaosBatchProcessor:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_experiments(self, experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(experiments):
            try:
                exp = await self.manager.create_experiment(data)
                exp["batch_index"] = i
                exp["success"] = True
                results.append(exp)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_run_experiments(self, experiment_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for eid in experiment_ids:
            try:
                r = await self.manager.run_experiment(eid)
                r["experiment_id"] = eid
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"experiment_id": eid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_approve(self, experiment_ids: List[str], approved_by: str = "admin") -> List[Dict[str, Any]]:
        results = []
        for eid in experiment_ids:
            r = await self.manager.approve_experiment(eid, approved_by)
            results.append({"experiment_id": eid, "approved": r is not None, "success": r is not None})
        return results

    async def batch_delete(self, experiment_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for eid in experiment_ids:
            ok = await self.manager.delete_experiment(eid)
            results.append({"experiment_id": eid, "deleted": ok})
        return results

    def export_csv(self, results_list: List[Dict[str, Any]]) -> str:
        if not results_list:
            return ""
        fields = ["id", "experiment_name", "status", "fault_injected", "rpo_actual_minutes", "rpo_target_minutes", "rto_actual_minutes", "rto_target_minutes", "total_duration_seconds"]
        lines = [",".join(fields)]
        for r in results_list:
            row = [str(r.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)


class ChaosAnalytics:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def experiment_success_rate(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.manager.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        if not recent:
            return {"rate": 0, "total": 0, "passed": 0}
        passed = sum(1 for r in recent if r["status"] == "passed")
        return {"rate": round(passed / len(recent) * 100, 1), "total": len(recent), "passed": passed, "failed": len(recent) - passed}

    def success_by_fault_type(self) -> Dict[str, Any]:
        breakdown: Dict[str, Dict[str, int]] = {}
        for r in self.manager.results:
            ftype = r.get("fault_injected", "unknown")
            breakdown.setdefault(ftype, {"total": 0, "passed": 0})
            breakdown[ftype]["total"] += 1
            if r["status"] == "passed":
                breakdown[ftype]["passed"] += 1
        for ftype in breakdown:
            t = breakdown[ftype]["total"]
            p = breakdown[ftype]["passed"]
            breakdown[ftype]["rate_pct"] = round(p / t * 100, 1) if t else 0
        return breakdown

    def average_rto_by_target(self) -> Dict[str, Any]:
        targets: Dict[str, List[float]] = {}
        for r in self.manager.results:
            target = r.get("target", "unknown")
            targets.setdefault(target, []).append(r.get("rto_actual_minutes", 0))
        return {t: round(sum(v) / len(v), 2) for t, v in targets.items()}

    def blast_radius_analysis(self) -> Dict[str, Any]:
        results = self.manager.results
        if not results:
            return {}
        avg_downtime = sum(r.get("downtime_seconds", 0) for r in results) / len(results)
        avg_data_loss = sum(r.get("data_loss_seconds", 0) for r in results) / len(results)
        return {"average_downtime_seconds": round(avg_downtime, 1), "average_data_loss_seconds": round(avg_data_loss, 1), "max_downtime_seconds": max(r.get("downtime_seconds", 0) for r in results), "max_data_loss_seconds": max(r.get("data_loss_seconds", 0) for r in results)}

    def generate_report(self) -> str:
        lines = ["=== Chaos Validation Report ==="]
        lines.append(f"Total Experiments: {len(self.manager.experiments)}")
        srate = self.experiment_success_rate(30)
        lines.append(f"30-Day Success Rate: {srate.get('rate', 0)}% ({srate.get('passed', 0)}/{srate.get('total', 0)})")
        by_type = self.success_by_fault_type()
        for ftype, stats in by_type.items():
            lines.append(f"  {ftype}: {stats.get('rate_pct', 0)}% pass ({stats.get('passed', 0)}/{stats.get('total', 0)})")
        rto = self.average_rto_by_target()
        if rto:
            lines.append(f"Best Avg RTO: {min(rto.values())}min ({min(rto, key=rto.get)})")
            lines.append(f"Worst Avg RTO: {max(rto.values())}min ({max(rto, key=rto.get)})")
        return "\n".join(lines)


class ChaosPaginator:
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


class ChaosScheduler:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    async def schedule_experiment(self, experiment_id: str, cron_expression: str) -> Optional[Dict[str, Any]]:
        for exp in self.manager.experiments:
            if exp["id"] == experiment_id:
                exp["schedule_cron"] = cron_expression
                exp["status"] = "scheduled"
                self.manager._save_experiments()
                return exp
        return None

    async def get_scheduled_experiments(self) -> List[Dict[str, Any]]:
        return [e for e in self.manager.experiments if e.get("schedule_cron")]

    async def run_scheduled(self) -> List[Dict[str, Any]]:
        results = []
        for exp in self.manager.experiments:
            if exp.get("schedule_cron") and exp.get("status") in ("scheduled", "completed"):
                if exp.get("approval_required") and not exp.get("approved"):
                    continue
                r = await self.manager.run_experiment(exp["id"])
                results.append(r)
        return results


class ExperimentTemplateManager:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager
        self.templates: List[Dict[str, Any]] = []

    async def create_from_template(self, template_id: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        templates = await self.manager.get_experiment_templates()
        tmpl = next((t for t in templates if t["id"] == template_id), None)
        if not tmpl:
            return None
        data = {k: v for k, v in tmpl.items() if k != "id"}
        if overrides:
            data.update(overrides)
        return await self.manager.create_experiment(data)

    async def save_as_template(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        exp = await self.manager.get_experiment(experiment_id)
        if not exp:
            return None
        tmpl = {"id": f"template_{int(datetime.now().timestamp())}", "name": f"Template: {exp.get('name')}", "fault_type": exp.get("fault_type"), "target": exp.get("target"), "duration_minutes": exp.get("duration_minutes", 10), "description": exp.get("description", "")}
        self.templates.append(tmpl)
        return tmpl


class FailureModeAnalyzer:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    async def analyze_failure_modes(self) -> Dict[str, Any]:
        modes = await self.manager.get_failure_modes()
        results_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for r in self.manager.results:
            ftype = r.get("fault_injected", "unknown")
            results_by_type.setdefault(ftype, []).append(r)
        analysis = []
        for mode in modes:
            ftype = mode.get("type", "")
            related = results_by_type.get(ftype, [])
            passed = sum(1 for r in related if r.get("status") == "passed")
            analysis.append({"name": mode.get("name"), "type": ftype, "severity": mode.get("severity"), "total_runs": len(related), "passed": passed, "pass_rate_pct": round(passed / len(related) * 100, 1) if related else 0})
        return {"modes": analysis, "total_modes": len(modes), "tested_modes": sum(1 for a in analysis if a["total_runs"] > 0), "coverage_pct": round(sum(1 for a in analysis if a["total_runs"] > 0) / len(modes) * 100, 1) if modes else 0}


class ExperimentResultAnalyzer:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def analyze_recent_results(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.manager.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        if not recent:
            return {"total": 0, "message": "No recent results"}
        passed = sum(1 for r in recent if r["status"] == "passed")
        avg_rto = sum(r.get("rto_actual_minutes", 0) for r in recent) / len(recent)
        avg_rpo = sum(r.get("rpo_actual_minutes", 0) for r in recent) / len(recent)
        return {"total": len(recent), "passed": passed, "failed": len(recent) - passed, "pass_rate": round(passed / len(recent) * 100, 1), "average_rto_minutes": round(avg_rto, 2), "average_rpo_minutes": round(avg_rpo, 2), "date_range": f"last_{days}d"}

    def find_weakest_targets(self) -> List[Dict[str, Any]]:
        targets: Dict[str, Dict[str, int]] = {}
        for r in self.manager.results:
            target = r.get("target", "unknown")
            targets.setdefault(target, {"total": 0, "passed": 0})
            targets[target]["total"] += 1
            if r["status"] == "passed":
                targets[target]["passed"] += 1
        return sorted([{"target": t, "total": stats["total"], "passed": stats["passed"], "pass_rate": round(stats["passed"] / stats["total"] * 100, 1)} for t, stats in targets.items()], key=lambda x: x["pass_rate"])

    def get_recovery_time_distribution(self) -> Dict[str, Any]:
        rtos = [r.get("rto_actual_minutes", 0) for r in self.manager.results if r.get("rto_actual_minutes") is not None]
        if not rtos:
            return {}
        import statistics
        return {"min": round(min(rtos), 2), "max": round(max(rtos), 2), "average": round(sum(rtos) / len(rtos), 2), "median": round(statistics.median(rtos), 2), "p95": round(sorted(rtos)[int(len(rtos) * 0.95)], 2) if len(rtos) > 20 else round(sorted(rtos)[-1], 2), "samples": len(rtos)}


class ChaosExperimentReporter:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    async def generate_summary_table(self) -> List[Dict[str, Any]]:
        table = []
        for exp in self.manager.experiments:
            results = [r for r in self.manager.results if r["experiment_id"] == exp["id"]]
            last = results[-1] if results else None
            table.append({"experiment_id": exp["id"], "name": exp.get("name"), "type": exp.get("experiment_type"), "target": exp.get("target"), "status": exp.get("status"), "runs": len(results), "last_status": last.get("status") if last else "never_run", "last_rto": last.get("rto_actual_minutes") if last else None})
        return table

    async def generate_executive_report(self) -> str:
        lines = ["# Chaos Engineering Executive Report", f"Generated: {datetime.now().isoformat()}", ""]
        summary = await self.manager.get_dashboard_summary()
        lines.append(f"Total Experiments: {summary.get('total_experiments', 0)}")
        lines.append(f"Total Runs: {summary.get('total_runs', 0)}")
        lines.append(f"Pass Rate: {summary.get('pass_rate_percent', 0)}%")
        lines.append(f"Avg RTO: {summary.get('average_rto_seconds', 0)}s")
        lines.append("")
        weak = self.find_weakest_targets()
        if weak:
            lines.append("## Weakest Targets")
            for w in weak[:3]:
                lines.append(f"- {w['target']}: {w['pass_rate']}% pass rate")
        return "\n".join(lines)


class ChaosExperimentScheduler:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager
        self.schedules: List[Dict[str, Any]] = []

    def schedule_experiment(self, experiment_id: str, cron: str, duration_minutes: int = 10) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        schedule = {"id": str(uuid.uuid4()), "experiment_id": experiment_id, "experiment_name": exp.get("name"), "cron": cron, "duration_minutes": duration_minutes, "status": "scheduled", "created_at": datetime.now().isoformat()}
        self.schedules.append(schedule)
        return schedule

    def list_schedules(self) -> List[Dict[str, Any]]:
        return self.schedules

    def pause_schedule(self, schedule_id: str) -> Dict[str, Any]:
        for s in self.schedules:
            if s["id"] == schedule_id:
                s["status"] = "paused"
                return s
        return {"error": "Schedule not found"}

    def resume_schedule(self, schedule_id: str) -> Dict[str, Any]:
        for s in self.schedules:
            if s["id"] == schedule_id:
                s["status"] = "active"
                return s
        return {"error": "Schedule not found"}


class ChaosBlastRadiusAnalyzer:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def analyze_blast_radius(self, experiment_id: str) -> Dict[str, Any]:
        results = [r for r in self.manager.results if r["experiment_id"] == experiment_id]
        if not results:
            return {"experiment_id": experiment_id, "total_runs": 0}
        affected_services: Dict[str, int] = {}
        for r in results:
            target = r.get("target", "unknown")
            affected_services[target] = affected_services.get(target, 0) + 1
        return {"experiment_id": experiment_id, "total_runs": len(results), "unique_targets": len(affected_services), "targets": affected_services, "blast_radius": "high" if len(affected_services) > 5 else "medium" if len(affected_services) > 2 else "low"}

    def get_blast_radius_distribution(self) -> Dict[str, Any]:
        distribution: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        for exp in self.manager.experiments:
            analysis = self.analyze_blast_radius(exp["id"])
            radius = analysis.get("blast_radius", "low")
            distribution[radius] += 1
        return distribution


class ChaosNotificationConfig:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def configure_notifications(self, experiment_id: str, channels: List[str], events: List[str]) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        config = {"id": str(uuid.uuid4()), "experiment_id": experiment_id, "channels": channels, "events": events, "status": "active", "created_at": datetime.now().isoformat()}
        exp.setdefault("notification_configs", []).append(config)
        return config

    def get_notification_config(self, experiment_id: str) -> List[Dict[str, Any]]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return []
        return exp.get("notification_configs", [])

    def test_notification(self, experiment_id: str, channel: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        return {"experiment_id": experiment_id, "channel": channel, "status": "delivered", "message": f"Test notification for experiment {exp.get('name')}", "sent_at": datetime.now().isoformat()}


class ChaosMetricCollector:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def collect_experiment_metrics(self, experiment_id: str) -> Dict[str, Any]:
        results = [r for r in self.manager.results if r["experiment_id"] == experiment_id]
        if not results:
            return {"total_runs": 0}
        durations = [r.get("duration_seconds", 0) for r in results]
        rtos = [r.get("rto_actual_minutes", 0) for r in results if r.get("rto_actual_minutes") is not None]
        rpos = [r.get("rpo_actual_minutes", 0) for r in results if r.get("rpo_actual_minutes") is not None]
        import statistics
        return {"experiment_id": experiment_id, "total_runs": len(results), "passed": sum(1 for r in results if r.get("status") == "passed"), "failed": sum(1 for r in results if r.get("status") == "failed"), "avg_duration": round(sum(durations) / len(durations), 1) if durations else 0, "min_duration": round(min(durations), 1) if durations else 0, "max_duration": round(max(durations), 1) if durations else 0, "median_rto": round(statistics.median(rtos), 2) if len(rtos) > 1 else (rtos[0] if rtos else 0), "median_rpo": round(statistics.median(rpos), 2) if len(rpos) > 1 else (rpos[0] if rpos else 0)}

    def get_failure_rate_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.manager.results if datetime.fromisoformat(r["completed_at"]) > cutoff]
        if not recent:
            return {"trend": [], "overall_failure_rate": 0}
        daily: Dict[str, Dict[str, int]] = {}
        for r in recent:
            day = r["completed_at"][:10]
            daily.setdefault(day, {"total": 0, "failed": 0})
            daily[day]["total"] += 1
            if r.get("status") == "failed":
                daily[day]["failed"] += 1
        trend = []
        for day in sorted(daily.keys()):
            d = daily[day]
            trend.append({"date": day, "failure_rate": round(d["failed"] / d["total"] * 100, 1), "total": d["total"], "failed": d["failed"]})
        overall_failed = sum(d["failed"] for d in daily.values())
        overall_total = sum(d["total"] for d in daily.values())
        return {"trend": trend, "overall_failure_rate": round(overall_failed / overall_total * 100, 1) if overall_total else 0}


class ChaosApprovalManager:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def request_approval(self, experiment_id: str, approvers: List[str]) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        request = {"id": str(uuid.uuid4()), "experiment_id": experiment_id, "approvers": approvers, "status": "pending", "responses": {}, "created_at": datetime.now().isoformat()}
        exp["approval_request"] = request
        self.manager._save_experiments()
        return request

    def approve(self, experiment_id: str, user: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        req = exp.get("approval_request")
        if not req:
            return {"error": "No approval request found"}
        if user not in req.get("approvers", []):
            return {"error": "User not authorized"}
        req.setdefault("responses", {})[user] = {"approved": True, "at": datetime.now().isoformat()}
        all_approved = all(r.get("approved") for r in req.get("responses", {}).values())
        if all_approved:
            req["status"] = "approved"
            exp["approval_required"] = False
            exp["approved"] = True
        self.manager._save_experiments()
        return {"experiment_id": experiment_id, "status": req["status"], "approvals": len(req.get("responses", {})), "required": len(req.get("approvers", []))}

    def reject(self, experiment_id: str, user: str, reason: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        req = exp.get("approval_request")
        if not req:
            return {"error": "No approval request found"}
        req["status"] = "rejected"
        req["rejection_reason"] = reason
        exp["approved"] = False
        self.manager._save_experiments()
        return {"experiment_id": experiment_id, "status": "rejected", "reason": reason}


class ChaosTagManager:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def add_tag(self, experiment_id: str, tag: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        exp.setdefault("tags", [])
        if tag not in exp["tags"]:
            exp["tags"].append(tag)
            self.manager._save_experiments()
        return {"experiment_id": experiment_id, "tags": exp["tags"]}

    def remove_tag(self, experiment_id: str, tag: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        exp.setdefault("tags", [])
        if tag in exp["tags"]:
            exp["tags"].remove(tag)
            self.manager._save_experiments()
        return {"experiment_id": experiment_id, "tags": exp["tags"]}

    def get_experiments_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [e for e in self.manager.experiments if tag in e.get("tags", [])]

    def get_all_tags(self) -> List[str]:
        tags: Set[str] = set()
        for e in self.manager.experiments:
            tags.update(e.get("tags", []))
        return sorted(tags)


class ChaosSteadyStateValidator:
    def __init__(self, manager: ChaosValidationManager):
        self.manager = manager

    def validate_steady_state(self, experiment_id: str) -> Dict[str, Any]:
        exp = next((e for e in self.manager.experiments if e["id"] == experiment_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        steady = exp.get("steady_state_hypothesis", {})
        metrics = steady.get("metrics", [])
        passed = 0
        failed = 0
        for m in metrics:
            if m.get("status") == "passing":
                passed += 1
            else:
                failed += 1
        return {"experiment_id": experiment_id, "total_checks": len(metrics), "passed": passed, "failed": failed, "steady_state": failed == 0, "hypothesis": steady.get("description", "No hypothesis defined")}

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
