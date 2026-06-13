from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class ResiliencePipelineManager:
    """Resilience Testing Pipeline — CI/CD integration with chaos/resilience tests"""

    PIPELINE_STATUSES = ["created", "queued", "running", "passed", "failed", "cancelled"]
    TEST_TYPES = ["chaos_experiment", "dependency_simulation", "data_integrity", "failover_test", "load_test", "circuit_breaker_test"]
    GATE_STRATEGIES = ["all_pass", "critical_only", "score_threshold", "manual_review"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pipelines_file = config.get("resilience_pipelines_file", "data/resiliency/resilience_pipelines.json")
        self.runs_file = config.get("resilience_pipeline_runs_file", "data/resiliency/resilience_pipeline_runs.json")
        self.pipelines: List[Dict[str, Any]] = []
        self.runs: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.pipelines_file) or ".", exist_ok=True)
        for path, attr in [(self.pipelines_file, "pipelines"), (self.runs_file, "runs")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_pipelines(self):
        with open(self.pipelines_file, "w") as f:
            json.dump(self.pipelines, f, indent=2, default=str)

    def _save_runs(self):
        with open(self.runs_file, "w") as f:
            json.dump(self.runs[-1000:], f, indent=2, default=str)

    async def create_pipeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = {
            "id": f"rp_{int(datetime.now().timestamp())}_{len(self.pipelines)}",
            "name": data.get("name", "Unnamed Resilience Pipeline"),
            "description": data.get("description", ""),
            "repository": data.get("repository", ""),
            "branch": data.get("branch", "main"),
            "trigger_events": data.get("trigger_events", ["push", "pull_request"]),
            "tests": data.get("tests", []),
            "gate_strategy": data.get("gate_strategy", "all_pass"),
            "score_threshold": data.get("score_threshold", 75),
            "environment": data.get("environment", "staging"),
            "timeout_minutes": data.get("timeout_minutes", 30),
            "notifications": data.get("notifications", {}),
            "active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_run": None,
        }
        self.pipelines.append(pipeline)
        self._save_pipelines()
        return pipeline

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        return self.pipelines

    async def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        return next((p for p in self.pipelines if p["id"] == pipeline_id), None)

    async def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for p in self.pipelines:
            if p["id"] == pipeline_id:
                p.update(updates)
                p["updated_at"] = datetime.now().isoformat()
                self._save_pipelines()
                return p
        return None

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        for i, p in enumerate(self.pipelines):
            if p["id"] == pipeline_id:
                self.pipelines.pop(i)
                self._save_pipelines()
                return True
        return False

    async def trigger_pipeline(self, pipeline_id: str, event_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pipeline = await self.get_pipeline(pipeline_id)
        if not pipeline:
            return {"error": "Pipeline not found"}
        run = {
            "id": f"rp_run_{int(datetime.now().timestamp())}_{len(self.runs)}",
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.get("name"),
            "status": "running",
            "environment": pipeline.get("environment", "staging"),
            "tests": [],
            "gate_decisions": [],
            "overall_score": 0,
            "commit_sha": event_data.get("commit_sha", "") if event_data else "",
            "branch": event_data.get("branch", pipeline.get("branch", "main")) if event_data else pipeline.get("branch", "main"),
            "trigger_event": event_data.get("event", "manual") if event_data else "manual",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        self.runs.append(run)
        self._save_runs()
        asyncio.create_task(self._execute_pipeline(run, pipeline))
        return run

    async def _execute_pipeline(self, run: Dict[str, Any], pipeline: Dict[str, Any]):
        test_results = []
        all_passed = True
        for test in pipeline.get("tests", []):
            if run["status"] != "running":
                break
            test_type = test.get("type", "chaos_experiment")
            test_name = test.get("name", "Unnamed Test")
            test_config = test.get("config", {})
            result = await self._run_test(test_type, test_name, test_config)
            test_results.append(result)
            if result.get("status") == "failed":
                all_passed = False
                if pipeline.get("gate_strategy") == "all_pass":
                    break
            run["tests"] = test_results
            self._save_runs()
        resilience_score = await self._calculate_resilience_score(test_results)
        gate_result = await self._evaluate_gates(pipeline, test_results, resilience_score)
        run["gate_decisions"] = gate_result
        run["overall_score"] = resilience_score
        strategy = pipeline.get("gate_strategy", "all_pass")
        if strategy == "all_pass":
            run["status"] = "passed" if all_passed else "failed"
        elif strategy == "score_threshold":
            threshold = pipeline.get("score_threshold", 75)
            run["status"] = "passed" if resilience_score >= threshold else "failed"
        elif strategy == "critical_only":
            critical_failed = any(r.get("status") == "failed" and r.get("critical", False) for r in test_results)
            run["status"] = "failed" if critical_failed else "passed"
        else:
            run["status"] = "passed"
        run["completed_at"] = datetime.now().isoformat()
        self._save_runs()
        pipeline["last_run"] = datetime.now().isoformat()
        self._save_pipelines()

    async def _run_test(self, test_type: str, test_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        passed = random.random() > 0.15
        return {"type": test_type, "name": test_name, "status": "passed" if passed else "failed", "duration_ms": random.randint(1000, 15000), "critical": config.get("critical", False), "details": f"Completed {test_type}: {test_name}", "started_at": datetime.now().isoformat(), "completed_at": (datetime.now() + timedelta(seconds=2)).isoformat()}

    async def _calculate_resilience_score(self, test_results: List[Dict[str, Any]]) -> float:
        if not test_results:
            return 0
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        return round(passed / len(test_results) * 100, 1)

    async def _evaluate_gates(self, pipeline: Dict[str, Any], test_results: List[Dict[str, Any]], score: float) -> List[Dict[str, Any]]:
        return [{"gate": "resilience_score", "threshold": pipeline.get("score_threshold", 75), "actual": score, "passed": score >= pipeline.get("score_threshold", 75)}]

    async def get_runs(self, pipeline_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if pipeline_id:
            return [r for r in self.runs if r["pipeline_id"] == pipeline_id]
        return self.runs

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self.runs if r["id"] == run_id), None)

    async def get_summary(self) -> Dict[str, Any]:
        total_pipelines = len(self.pipelines)
        total_runs = len(self.runs)
        passed_runs = sum(1 for r in self.runs if r["status"] == "passed")
        return {"total_pipelines": total_pipelines, "active_pipelines": sum(1 for p in self.pipelines if p.get("active")), "total_runs": total_runs, "passed_runs": passed_runs, "failed_runs": total_runs - passed_runs, "pass_rate": round(passed_runs / total_runs * 100, 2) if total_runs else 100}

    async def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = {"id": f"pipeline_{len(self.pipelines)}_{int(datetime.now().timestamp())}", "name": pipeline_data.get("name", "Unnamed Pipeline"), "description": pipeline_data.get("description", ""), "test_groups": pipeline_data.get("test_groups", []), "strategy": pipeline_data.get("strategy", "all_pass"), "score_threshold": pipeline_data.get("score_threshold", 75), "schedule": pipeline_data.get("schedule", "manual"), "active": True, "gates": pipeline_data.get("gates", []), "notifications": pipeline_data.get("notifications", {}), "created_at": datetime.now().isoformat(), "last_run": None, "total_runs": 0, "pass_count": 0}
        self.pipelines.append(pipeline)
        self._save_pipelines()
        return pipeline

    async def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for p in self.pipelines:
            if p["id"] == pipeline_id:
                p.update(updates)
                self._save_pipelines()
                return p
        return None

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        for i, p in enumerate(self.pipelines):
            if p["id"] == pipeline_id:
                self.pipelines.pop(i)
                self._save_pipelines()
                return True
        return False

    async def get_all_pipelines(self) -> List[Dict[str, Any]]:
        return self.pipelines

    async def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        return next((p for p in self.pipelines if p["id"] == pipeline_id), None)

    async def get_pipeline_templates(self) -> List[Dict[str, Any]]:
        return [{"id": "template_quick_check", "name": "Quick Health Check", "test_groups": ["latency", "availability"], "strategy": "all_pass", "score_threshold": 80}, {"id": "template_full_validation", "name": "Full Validation", "test_groups": ["latency", "availability", "failover", "data_integrity"], "strategy": "weighted", "score_threshold": 85}, {"id": "template_critical_path", "name": "Critical Path Focus", "test_groups": ["failover", "data_integrity"], "strategy": "critical_only", "score_threshold": 90}]

    async def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return sorted(self.runs, key=lambda r: r.get("started_at", ""), reverse=True)[:limit]

    async def get_pipeline_stats(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [r for r in self.runs if r.get("started_at") and datetime.fromisoformat(r["started_at"]) > cutoff]
        return {"period_days": days, "total_runs": len(recent), "passed": sum(1 for r in recent if r["status"] == "passed"), "failed": sum(1 for r in recent if r["status"] == "failed"), "avg_score": round(sum(r.get("resilience_score", 0) for r in recent) / len(recent), 1) if recent else 0, "pipelines_active": sum(1 for p in self.pipelines if p.get("active"))}


class ResiliencePipelineBatchProcessor:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_create_pipelines(self, pipelines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(pipelines):
            try:
                p = await self.manager.create_pipeline(data)
                p["batch_index"] = i
                p["success"] = True
                results.append(p)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_trigger_pipelines(self, pipeline_ids: List[str], event_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = []
        for pid in pipeline_ids:
            try:
                r = await self.manager.trigger_pipeline(pid, event_data)
                r["pipeline_id"] = pid
                r["success"] = "error" not in r
                results.append(r)
            except Exception as e:
                results.append({"pipeline_id": pid, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    async def batch_delete_pipelines(self, pipeline_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for pid in pipeline_ids:
            ok = await self.manager.delete_pipeline(pid)
            results.append({"pipeline_id": pid, "deleted": ok})
        return results

    def export_csv(self, runs: List[Dict[str, Any]]) -> str:
        if not runs:
            return ""
        fields = ["id", "pipeline_name", "status", "overall_score", "branch", "trigger_event", "started_at", "completed_at"]
        lines = [",".join(fields)]
        for r in runs:
            row = [str(r.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        return {"total_operations": total, "passed": passed, "failed": total - passed, "rate": round(passed / total * 100, 1) if total else 100}


class ResiliencePipelineAnalytics:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def pass_rate_by_strategy(self) -> Dict[str, Any]:
        breakdown: Dict[str, Dict[str, int]] = {}
        for run in self.manager.runs:
            pipeline = next((p for p in self.manager.pipelines if p["id"] == run["pipeline_id"]), None)
            strategy = pipeline.get("gate_strategy", "unknown") if pipeline else "unknown"
            breakdown.setdefault(strategy, {"total": 0, "passed": 0})
            breakdown[strategy]["total"] += 1
            if run.get("status") == "passed":
                breakdown[strategy]["passed"] += 1
        for s in breakdown:
            t = breakdown[s]["total"]
            p = breakdown[s]["passed"]
            breakdown[s]["rate_pct"] = round(p / t * 100, 1) if t else 0
        return breakdown

    def score_distribution(self) -> Dict[str, Any]:
        scores = [r.get("overall_score", 0) for r in self.manager.runs]
        if not scores:
            return {"average": 0, "median": 0, "min": 0, "max": 0}
        sorted_scores = sorted(scores)
        mid = len(sorted_scores) // 2
        median = sorted_scores[mid] if len(sorted_scores) % 2 else (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
        return {"average": round(sum(scores) / len(scores), 1), "median": round(median, 1), "min": min(scores), "max": max(scores), "runs_analyzed": len(scores)}

    def pipeline_effectiveness(self) -> List[Dict[str, Any]]:
        results = []
        for p in self.manager.pipelines:
            runs = [r for r in self.manager.runs if r["pipeline_id"] == p["id"]]
            passed = sum(1 for r in runs if r.get("status") == "passed")
            results.append({"pipeline_id": p["id"], "name": p.get("name"), "total_runs": len(runs), "passed": passed, "pass_rate": round(passed / len(runs) * 100, 1) if runs else 0, "avg_score": round(sum(r.get("overall_score", 0) for r in runs) / len(runs), 1) if runs else 0})
        return sorted(results, key=lambda x: x["pass_rate"], reverse=True)

    def generate_report(self) -> str:
        lines = ["=== Resilience Pipeline Report ==="]
        lines.append(f"Total Pipelines: {len(self.manager.pipelines)}")
        lines.append(f"Total Runs: {len(self.manager.runs)}")
        sd = self.score_distribution()
        lines.append(f"Score Distribution: avg={sd.get('average')}, median={sd.get('median')}, range={sd.get('min')}-{sd.get('max')}")
        by_strat = self.pass_rate_by_strategy()
        for s, stats in by_strat.items():
            lines.append(f"  Strategy '{s}': {stats.get('rate_pct', 0)}% pass ({stats.get('passed', 0)}/{stats.get('total', 0)})")
        return "\n".join(lines)


class ResiliencePipelinePaginator:
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


class PipelineGateManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    async def evaluate_custom_gate(self, pipeline_id: str, gate_name: str, threshold: float) -> Dict[str, Any]:
        pipeline = await self.manager.get_pipeline(pipeline_id)
        if not pipeline:
            return {"error": "Pipeline not found"}
        recent_runs = [r for r in self.manager.runs if r["pipeline_id"] == pipeline_id][-5:]
        if not recent_runs:
            return {"gate": gate_name, "status": "no_data", "passed": False}
        avg_score = sum(r.get("overall_score", 0) for r in recent_runs) / len(recent_runs)
        return {"gate": gate_name, "threshold": threshold, "actual_score": round(avg_score, 1), "passed": avg_score >= threshold, "runs_evaluated": len(recent_runs)}

    async def get_gate_status(self, pipeline_id: str) -> List[Dict[str, Any]]:
        pipeline = await self.manager.get_pipeline(pipeline_id)
        if not pipeline:
            return []
        return [{"gate": "resilience_score", "type": "threshold", "threshold": pipeline.get("score_threshold", 75), "status": "active"}]


class PipelineNotifier:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    async def notify_run_result(self, run_id: str) -> Dict[str, Any]:
        run = await self.manager.get_run(run_id)
        if not run:
            return {"error": "Run not found"}
        pipeline = await self.manager.get_pipeline(run["pipeline_id"])
        notifications = pipeline.get("notifications", {}) if pipeline else {}
        return {"run_id": run_id, "status": run.get("status"), "notifications_sent": bool(notifications), "channels": notifications.get("channels", []), "message": f"Pipeline {run.get('pipeline_name')} completed with status: {run.get('status')}"}


class PipelineRunComparer:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def compare_runs(self, run_id_1: str, run_id_2: str) -> Dict[str, Any]:
        run1 = next((r for r in self.manager.runs if r["id"] == run_id_1), None)
        run2 = next((r for r in self.manager.runs if r["id"] == run_id_2), None)
        if not run1 or not run2:
            return {"error": "Run not found"}
        return {"run_1": {"id": run1["id"], "status": run1.get("status"), "score": run1.get("overall_score"), "date": run1.get("started_at")}, "run_2": {"id": run2["id"], "status": run2.get("status"), "score": run2.get("overall_score"), "date": run2.get("started_at")}, "score_change": round(run2.get("overall_score", 0) - run1.get("overall_score", 0), 1), "status_change": f"{run1.get('status')} -> {run2.get('status')}"}

    def regression_detection(self, pipeline_id: str, threshold: float = 10.0) -> Optional[Dict[str, Any]]:
        runs = [r for r in self.manager.runs if r["pipeline_id"] == pipeline_id and r.get("overall_score") is not None]
        if len(runs) < 3:
            return None
        sorted_runs = sorted(runs, key=lambda r: r.get("started_at", ""))
        recent_3 = sorted_runs[-3:]
        scores = [r.get("overall_score", 0) for r in recent_3]
        if all(s < scores[0] - threshold for s in scores[1:]):
            return {"pipeline_id": pipeline_id, "regression_detected": True, "scores": scores, "threshold": threshold, "drop": round(scores[0] - scores[-1], 1), "recommendation": "Investigate recent changes"}
        return {"pipeline_id": pipeline_id, "regression_detected": False, "scores": scores, "threshold": threshold}


class TestResultAnalyzer:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def analyze_test_results(self, pipeline_id: str) -> Dict[str, Any]:
        runs = [r for r in self.manager.runs if r["pipeline_id"] == pipeline_id]
        if not runs:
            return {"total_runs": 0}
        all_tests: Dict[str, Dict[str, int]] = {}
        for run in runs:
            for test in run.get("tests", []):
                name = test.get("name", "unknown")
                all_tests.setdefault(name, {"total": 0, "passed": 0, "failed": 0})
                all_tests[name]["total"] += 1
                if test.get("status") == "passed":
                    all_tests[name]["passed"] += 1
                else:
                    all_tests[name]["failed"] += 1
        return {"pipeline_id": pipeline_id, "total_runs": len(runs), "tests": {name: {**stats, "pass_rate": round(stats["passed"] / stats["total"] * 100, 1)} for name, stats in all_tests.items()}}

    def find_flaky_tests(self, pipeline_id: str) -> List[Dict[str, Any]]:
        analysis = self.analyze_test_results(pipeline_id)
        flaky = []
        for name, stats in analysis.get("tests", {}).items():
            if stats["total"] >= 3 and 20 < stats["pass_rate"] < 80:
                flaky.append({"test_name": name, "pass_rate": stats["pass_rate"], "total_runs": stats["total"], "passed": stats["passed"], "failed": stats["failed"]})
        return flaky


class PipelineStepManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def add_step(self, pipeline_id: str, step_name: str, step_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        step = {"id": str(uuid.uuid4()), "name": step_name, "type": step_type, "config": config or {}, "order": len(pipeline.get("steps", [])), "status": "pending"}
        pipeline.setdefault("steps", []).append(step)
        self.manager._save_pipelines()
        return step

    def remove_step(self, pipeline_id: str, step_id: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        steps = pipeline.get("steps", [])
        pipeline["steps"] = [s for s in steps if s["id"] != step_id]
        for i, s in enumerate(pipeline["steps"]):
            s["order"] = i
        self.manager._save_pipelines()
        return {"status": "removed", "step_id": step_id}

    def reorder_steps(self, pipeline_id: str, step_ids: List[str]) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        step_map = {s["id"]: s for s in pipeline.get("steps", [])}
        reordered = []
        for sid in step_ids:
            if sid in step_map:
                reordered.append(step_map[sid])
        for i, s in enumerate(reordered):
            s["order"] = i
        pipeline["steps"] = reordered
        self.manager._save_pipelines()
        return {"status": "reordered"}

    def get_step_details(self, pipeline_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return None
        return next((s for s in pipeline.get("steps", []) if s["id"] == step_id), None)


class PipelineEnvManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def set_environment_variable(self, pipeline_id: str, key: str, value: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        pipeline.setdefault("env_vars", {})[key] = value
        self.manager._save_pipelines()
        return {"pipeline_id": pipeline_id, "key": key, "set": True}

    def get_environment_variables(self, pipeline_id: str) -> Dict[str, str]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {}
        return pipeline.get("env_vars", {})

    def delete_environment_variable(self, pipeline_id: str, key: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        env_vars = pipeline.get("env_vars", {})
        if key in env_vars:
            del env_vars[key]
            self.manager._save_pipelines()
            return {"pipeline_id": pipeline_id, "key": key, "deleted": True}
        return {"error": "Variable not found"}


class PipelineWebhookManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def register_webhook(self, pipeline_id: str, url: str, events: List[str]) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        wh = {"id": str(uuid.uuid4()), "url": url, "events": events, "created_at": datetime.now().isoformat(), "status": "active"}
        pipeline.setdefault("webhooks", []).append(wh)
        self.manager._save_pipelines()
        return wh

    def list_webhooks(self, pipeline_id: str) -> List[Dict[str, Any]]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return []
        return pipeline.get("webhooks", [])

    def delete_webhook(self, pipeline_id: str, webhook_id: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        webhooks = pipeline.get("webhooks", [])
        pipeline["webhooks"] = [w for w in webhooks if w["id"] != webhook_id]
        self.manager._save_pipelines()
        return {"status": "deleted", "webhook_id": webhook_id}


class PipelineExportImport:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def export_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return None
        export = {k: v for k, v in pipeline.items() if k in ("name", "description", "steps", "score_threshold", "env_vars", "webhooks")}
        export["exported_at"] = datetime.now().isoformat()
        export["version"] = pipeline.get("version", 1)
        return export

    def import_pipeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = {"id": str(uuid.uuid4()), "name": data.get("name", "imported"), "description": data.get("description", ""), "steps": data.get("steps", []), "score_threshold": data.get("score_threshold", 75), "env_vars": data.get("env_vars", {}), "webhooks": data.get("webhooks", []), "status": "inactive", "version": 1, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
        self.manager.pipelines.append(pipeline)
        self.manager._save_pipelines()
        return {"id": pipeline["id"], "name": pipeline["name"]}

    def clone_pipeline(self, pipeline_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        export = self.export_pipeline(pipeline_id)
        if not export:
            return None
        export["name"] = new_name
        return self.import_pipeline(export)


class PipelineTriggerManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def create_schedule_trigger(self, pipeline_id: str, cron: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        trigger = {"id": str(uuid.uuid4()), "type": "schedule", "cron": cron, "pipeline_id": pipeline_id, "status": "active", "created_at": datetime.now().isoformat()}
        pipeline.setdefault("triggers", []).append(trigger)
        self.manager._save_pipelines()
        return trigger

    def create_event_trigger(self, pipeline_id: str, event_type: str, condition: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        trigger = {"id": str(uuid.uuid4()), "type": "event", "event_type": event_type, "condition": condition or {}, "pipeline_id": pipeline_id, "status": "active", "created_at": datetime.now().isoformat()}
        pipeline.setdefault("triggers", []).append(trigger)
        self.manager._save_pipelines()
        return trigger

    def list_triggers(self, pipeline_id: str) -> List[Dict[str, Any]]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return []
        return pipeline.get("triggers", [])

    def disable_trigger(self, pipeline_id: str, trigger_id: str) -> Dict[str, Any]:
        pipeline = next((p for p in self.manager.pipelines if p["id"] == pipeline_id), None)
        if not pipeline:
            return {"error": "Pipeline not found"}
        for t in pipeline.get("triggers", []):
            if t["id"] == trigger_id:
                t["status"] = "disabled"
                self.manager._save_pipelines()
                return {"trigger_id": trigger_id, "status": "disabled"}
        return {"error": "Trigger not found"}


class PipelineAnalytics:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def get_overall_stats(self) -> Dict[str, Any]:
        total_pipelines = len(self.manager.pipelines)
        total_runs = len(self.manager.runs)
        active = sum(1 for p in self.manager.pipelines if p.get("status") == "active")
        completed = sum(1 for r in self.manager.runs if r.get("status") == "completed")
        failed = sum(1 for r in self.manager.runs if r.get("status") == "failed")
        avg_duration = None
        durations = []
        for r in self.manager.runs:
            if r.get("started_at") and r.get("completed_at"):
                start = datetime.fromisoformat(r["started_at"])
                end = datetime.fromisoformat(r["completed_at"])
                durations.append((end - start).total_seconds())
        if durations:
            avg_duration = round(sum(durations) / len(durations), 1)
        return {"total_pipelines": total_pipelines, "active_pipelines": active, "total_runs": total_runs, "completed_runs": completed, "failed_runs": failed, "avg_duration_seconds": avg_duration, "success_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0}

    def pipeline_performance(self, pipeline_id: str) -> Dict[str, Any]:
        runs = [r for r in self.manager.runs if r["pipeline_id"] == pipeline_id]
        if not runs:
            return {"pipeline_id": pipeline_id, "total_runs": 0}
        scores = [r.get("overall_score") for r in runs if r.get("overall_score") is not None]
        return {"pipeline_id": pipeline_id, "total_runs": len(runs), "avg_score": round(sum(scores) / len(scores), 1) if scores else None, "max_score": max(scores) if scores else None, "min_score": min(scores) if scores else None, "completed": sum(1 for r in runs if r.get("status") == "completed"), "failed": sum(1 for r in runs if r.get("status") == "failed")}

    def run_duration_histogram(self, pipeline_id: str, bins: int = 5) -> Dict[str, Any]:
        runs = [r for r in self.manager.runs if r["pipeline_id"] == pipeline_id and r.get("started_at") and r.get("completed_at")]
        if not runs:
            return {"pipeline_id": pipeline_id, "histogram": []}
        durations = [(datetime.fromisoformat(r["completed_at"]) - datetime.fromisoformat(r["started_at"])).total_seconds() for r in runs]
        min_d, max_d = min(durations), max(durations)
        bin_width = (max_d - min_d) / bins if bins > 0 else 1
        histogram = []
        for i in range(bins):
            lower = min_d + i * bin_width
            upper = lower + bin_width
            count = sum(1 for d in durations if lower <= d < upper)
            histogram.append({"range_seconds": f"{round(lower)}-{round(upper)}", "count": count})
        return {"pipeline_id": pipeline_id, "total_runs": len(runs), "histogram": histogram}


class PipelineNotificationManager:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager
        self.notifications: List[Dict[str, Any]] = []

    def send_notification(self, pipeline_id: str, event: str, message: str, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        notification = {"id": str(uuid.uuid4()), "pipeline_id": pipeline_id, "event": event, "message": message, "channels": channels or ["log"], "sent_at": datetime.now().isoformat(), "status": "delivered"}
        self.notifications.append(notification)
        return notification

    def get_pipeline_notifications(self, pipeline_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return [n for n in self.notifications if n.get("pipeline_id") == pipeline_id][-limit:]

    def notify_on_failure(self, pipeline_id: str, run_id: str, error: str) -> Dict[str, Any]:
        return self.send_notification(pipeline_id, "run_failed", f"Pipeline run {run_id} failed: {error}", channels=["log", "webhook"])

    def notify_on_completion(self, pipeline_id: str, run_id: str, score: float) -> Dict[str, Any]:
        return self.send_notification(pipeline_id, "run_completed", f"Pipeline run {run_id} completed with score {score}", channels=["log"])


class PipelineMetricsExporter:
    def __init__(self, manager: ResiliencePipelineManager):
        self.manager = manager

    def export_summary(self) -> Dict[str, Any]:
        analytics = PipelineAnalytics(self.manager)
        stats = analytics.get_overall_stats()
        return {"statistics": stats, "pipelines": len(self.manager.pipelines), "runs": len(self.manager.runs), "exported_at": datetime.now().isoformat()}

    def export_prometheus(self) -> str:
        lines = ["# HELP pipeline_success_rate Pipeline run success rate", "# TYPE pipeline_success_rate gauge"]
        for p in self.manager.pipelines:
            name = p.get("name", "unknown").replace(" ", "_").lower()
            runs = [r for r in self.manager.runs if r["pipeline_id"] == p["id"]]
            completed = sum(1 for r in runs if r.get("status") == "completed")
            failed = sum(1 for r in runs if r.get("status") == "failed")
            rate = round(completed / (completed + failed) * 100, 1) if (completed + failed) else 100
            lines.append(f'pipeline_success_rate{{pipeline="{name}"}} {rate}')
        return "\n".join(lines)

    def export_run_history(self, pipeline_id: str) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["run_id", "status", "score", "started", "completed", "duration_seconds"])
        for r in self.manager.runs:
            if r["pipeline_id"] == pipeline_id:
                dur = ""
                if r.get("started_at") and r.get("completed_at"):
                    dur = round((datetime.fromisoformat(r["completed_at"]) - datetime.fromisoformat(r["started_at"])).total_seconds(), 1)
                writer.writerow([r["id"], r.get("status"), r.get("overall_score"), r.get("started_at"), r.get("completed_at"), dur])
        return output.getvalue()

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
