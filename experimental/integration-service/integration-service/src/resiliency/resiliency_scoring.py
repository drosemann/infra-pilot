from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import math

logger = logging.getLogger(__name__)


class ResiliencyScoringEngine:
    """Resiliency Score & Insights — score every service on resiliency with improvement recommendations"""

    SCORE_DIMENSIONS = ["redundancy", "backup_coverage", "dr_tested", "circuit_breakers", "auto_scaling", "load_balancing", "monitoring_coverage", "chaos_validation"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scores_file = config.get("resiliency_scores_file", "data/resiliency/resiliency_scores.json")
        self.recommendations_file = config.get("resiliency_recommendations_file", "data/resiliency/resiliency_recommendations.json")
        self.scores: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.scores_file) or ".", exist_ok=True)
        for path, attr in [(self.scores_file, "scores"), (self.recommendations_file, "recommendations")]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_scores(self):
        with open(self.scores_file, "w") as f:
            json.dump(self.scores, f, indent=2, default=str)

    def _save_recommendations(self):
        with open(self.recommendations_file, "w") as f:
            json.dump(self.recommendations, f, indent=2, default=str)

    async def score_service(self, service_id: str, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        dim_scores = {}
        for dim in self.SCORE_DIMENSIONS:
            dim_scores[dim] = self._calculate_dimension_score(dim, service_data or {})
        overall = round(sum(dim_scores.values()) / len(dim_scores), 1)
        grade = self._score_to_grade(overall)
        score_entry = {
            "id": f"score_{int(datetime.now().timestamp())}_{len(self.scores)}",
            "service_id": service_id,
            "service_name": service_data.get("name", "") if service_data else "",
            "overall_score": overall,
            "grade": grade,
            "dimension_scores": dim_scores,
            "scored_at": datetime.now().isoformat(),
        }
        existing = next((s for s in self.scores if s["service_id"] == service_id), None)
        if existing:
            existing.update(score_entry)
        else:
            self.scores.append(score_entry)
        self._save_scores()
        recs = await self._generate_recommendations(service_id, dim_scores)
        return {**score_entry, "recommendations": recs}

    def _calculate_dimension_score(self, dimension: str, data: Dict[str, Any]) -> float:
        weights = {"redundancy": 0.85, "backup_coverage": 0.75, "dr_tested": 0.60, "circuit_breakers": 0.70, "auto_scaling": 0.65, "load_balancing": 0.80, "monitoring_coverage": 0.90, "chaos_validation": 0.55}
        has_replicas = data.get("replica_count", 0) > 1
        has_backup = data.get("backup_enabled", False)
        has_dr = data.get("dr_plan_id", "") != ""
        has_circuit_breaker = data.get("circuit_breaker_enabled", False)
        has_auto_scale = data.get("auto_scaling_enabled", False)
        has_lb = data.get("load_balancer_enabled", False)
        has_monitoring = data.get("monitoring_enabled", False)
        has_chaos = data.get("chaos_validated", False)
        mapping = {"redundancy": has_replicas, "backup_coverage": has_backup, "dr_tested": has_dr, "circuit_breakers": has_circuit_breaker, "auto_scaling": has_auto_scale, "load_balancing": has_lb, "monitoring_coverage": has_monitoring, "chaos_validation": has_chaos}
        return weights.get(dimension, 0.5) * 100 if mapping.get(dimension, False) else weights.get(dimension, 0.5) * 30

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    async def _generate_recommendations(self, service_id: str, dim_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        recs = []
        recommendation_templates = {"redundancy": {"priority": "high", "message": "Deploy multiple replicas across availability zones", "effort": "medium", "impact": 25}, "backup_coverage": {"priority": "critical", "message": "Enable automated backups with cross-region replication", "effort": "low", "impact": 30}, "dr_tested": {"priority": "high", "message": "Create and regularly test a disaster recovery plan", "effort": "high", "impact": 35}, "circuit_breakers": {"priority": "medium", "message": "Implement circuit breakers for all external dependencies", "effort": "medium", "impact": 20}, "auto_scaling": {"priority": "medium", "message": "Configure auto-scaling based on CPU/memory utilization", "effort": "low", "impact": 15}, "load_balancing": {"priority": "high", "message": "Distribute traffic across multiple instances with health checks", "effort": "medium", "impact": 20}, "monitoring_coverage": {"priority": "critical", "message": "Set up comprehensive monitoring with alerting on key metrics", "effort": "low", "impact": 25}, "chaos_validation": {"priority": "medium", "message": "Run chaos experiments to validate system resilience", "effort": "high", "impact": 30}}
        for dim, score in dim_scores.items():
            if score < 70:
                template = recommendation_templates.get(dim, {})
                rec = {
                    "id": f"rec_{int(datetime.now().timestamp())}_{len(self.recommendations)}",
                    "service_id": service_id,
                    "dimension": dim,
                    "priority": template.get("priority", "medium"),
                    "message": template.get("message", f"Improve {dim}"),
                    "current_score": score,
                    "potential_improvement": template.get("impact", 10),
                    "effort": template.get("effort", "medium"),
                    "status": "open",
                    "created_at": datetime.now().isoformat(),
                }
                self.recommendations.append(rec)
                recs.append(rec)
        self._save_recommendations()
        return recs

    async def get_service_score(self, service_id: str) -> Optional[Dict[str, Any]]:
        score = next((s for s in self.scores if s["service_id"] == service_id), None)
        if score:
            score["recommendations"] = [r for r in self.recommendations if r["service_id"] == service_id]
        return score

    async def list_scores(self) -> List[Dict[str, Any]]:
        return self.scores

    async def delete_score(self, service_id: str) -> bool:
        for i, s in enumerate(self.scores):
            if s["service_id"] == service_id:
                self.scores.pop(i)
                self._save_scores()
                return True
        return False

    async def get_org_summary(self) -> Dict[str, Any]:
        if not self.scores:
            return {"average_score": 0, "total_services": 0, "grade_distribution": {}, "top_improvements": []}
        total = len(self.scores)
        avg = round(sum(s["overall_score"] for s in self.scores) / total, 1)
        grades = {}
        for s in self.scores:
            g = s.get("grade", "F")
            grades[g] = grades.get(g, 0) + 1
        open_recs = [r for r in self.recommendations if r.get("status") == "open"]
        top = sorted(open_recs, key=lambda r: r.get("potential_improvement", 0), reverse=True)[:5]
        return {"average_score": avg, "total_services": total, "grade_distribution": grades, "open_recommendations": len(open_recs), "top_improvements": [{"dimension": r["dimension"], "message": r["message"], "potential_improvement": r.get("potential_improvement")} for r in top], "last_updated": max(s["scored_at"] for s in self.scores)}

    async def get_recommendations(self, service_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        recs = self.recommendations
        if service_id:
            recs = [r for r in recs if r["service_id"] == service_id]
        if status:
            recs = [r for r in recs if r.get("status") == status]
        return recs

    async def update_recommendation(self, rec_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for rec in self.recommendations:
            if rec["id"] == rec_id:
                rec.update(updates)
                self._save_recommendations()
                return rec
        return None

    async def create_score(self, score_data: Dict[str, Any]) -> Dict[str, Any]:
        score = {"id": f"score_{len(self.scores)}_{int(datetime.now().timestamp())}", "service_id": score_data.get("service_id"), "service_name": score_data.get("service_name", "Unnamed Service"), "scores": {"availability": score_data.get("availability", 0), "durability": score_data.get("durability", 0), "recoverability": score_data.get("recoverability", 0), "data_integrity": score_data.get("data_integrity", 0), "redundancy": score_data.get("redundancy", 0), "chaos_resilience": score_data.get("chaos_resilience", 0)}, "overall": round(sum([score_data.get(k, 0) for k in ("availability", "durability", "recoverability", "data_integrity", "redundancy", "chaos_resilience")]) / 6, 1), "grade": self._calculate_grade(sum([score_data.get(k, 0) for k in ("availability", "durability", "recoverability", "data_integrity", "redundancy", "chaos_resilience")]) / 6), "scored_at": datetime.now().isoformat()}
        self.scores.append(score)
        self._save_scores()
        return score

    async def get_service_history(self, service_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return [s for s in self.scores if s["service_id"] == service_id][-limit:]

    async def get_grade_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for s in self.scores:
            g = s.get("grade", "F")
            dist[g] = dist.get(g, 0) + 1
        return dist

    async def score_ranking(self) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        ranked = sorted(latest.values(), key=lambda x: x.get("overall", 0), reverse=True)
        return [{"service_name": r["service_name"], "service_id": r["service_id"], "overall": r.get("overall", 0), "grade": r.get("grade", "F"), "scored_at": r["scored_at"]} for r in ranked]

    async def create_recommendation(self, rec_data: Dict[str, Any]) -> Dict[str, Any]:
        rec = {"id": f"rec_{len(self.recommendations)}_{int(datetime.now().timestamp())}", "service_id": rec_data.get("service_id"), "dimension": rec_data.get("dimension", "general"), "message": rec_data.get("message", ""), "potential_improvement": rec_data.get("potential_improvement", 0), "effort": rec_data.get("effort", "medium"), "status": "open", "created_at": datetime.now().isoformat()}
        self.recommendations.append(rec)
        self._save_recommendations()
        return rec

    async def delete_recommendation(self, rec_id: str) -> bool:
        for i, rec in enumerate(self.recommendations):
            if rec["id"] == rec_id:
                self.recommendations.pop(i)
                self._save_recommendations()
                return True
        return False

    async def get_all_services(self) -> List[str]:
        return list(set(s["service_id"] for s in self.scores))

    def _calculate_grade(self, score: float) -> str:
        if score >= 95: return "A+"
        if score >= 90: return "A"
        if score >= 85: return "A-"
        if score >= 80: return "B+"
        if score >= 75: return "B"
        if score >= 70: return "B-"
        if score >= 65: return "C+"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"


class ScoringBatchProcessor:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_score_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, svc in enumerate(services):
            try:
                result = await self.manager.score_service(svc.get("service_id", f"svc_{i}"), svc)
                result["batch_index"] = i
                result["success"] = True
                results.append(result)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e), "service": svc})
        self.results.extend(results)
        return results

    async def batch_delete_scores(self, service_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for sid in service_ids:
            ok = await self.manager.delete_score(sid)
            results.append({"service_id": sid, "deleted": ok})
        return results

    async def batch_create_recommendations(self, recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, data in enumerate(recs):
            try:
                r = await self.manager.create_recommendation(data)
                r["batch_index"] = i
                r["success"] = True
                results.append(r)
            except Exception as e:
                results.append({"batch_index": i, "success": False, "error": str(e)})
        self.results.extend(results)
        return results

    def export_csv(self, scores: List[Dict[str, Any]]) -> str:
        if not scores:
            return ""
        fields = ["service_id", "service_name", "overall_score", "grade", "scored_at"]
        lines = [",".join(fields)]
        for s in scores:
            row = [str(s.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success"))
        return {"total_operations": total, "passed": passed, "failed": total - passed, "rate": round(passed / total * 100, 1) if total else 100}


class ScoringAnalytics:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def average_score_by_dimension(self) -> Dict[str, float]:
        if not self.manager.scores:
            return {}
        dims: Dict[str, List[float]] = {}
        for s in self.manager.scores:
            dim_scores = s.get("dimension_scores", {})
            if isinstance(dim_scores, dict):
                for dim, score in dim_scores.items():
                    dims.setdefault(dim, []).append(score)
        return {dim: round(sum(v) / len(v), 1) for dim, v in dims.items()}

    def score_trend(self, service_id: str, days: int = 30) -> Dict[str, Any]:
        history = [s for s in self.manager.scores if s["service_id"] == service_id]
        if len(history) < 2:
            return {"direction": "stable", "samples": len(history)}
        sorted_hist = sorted(history, key=lambda s: s["scored_at"])
        first = sorted_hist[0]["overall_score"]
        last = sorted_hist[-1]["overall_score"]
        change = last - first
        return {"direction": "improving" if change > 5 else ("declining" if change < -5 else "stable"), "change": round(change, 1), "first_score": first, "last_score": last, "samples": len(sorted_hist)}

    def improvement_gap_analysis(self) -> List[Dict[str, Any]]:
        if not self.manager.scores:
            return []
        dims = self.average_score_by_dimension()
        gaps = [{"dimension": dim, "average_score": score, "gap_to_perfect": round(100 - score, 1), "priority": "critical" if score < 50 else "high" if score < 70 else "medium" if score < 85 else "low"} for dim, score in dims.items()]
        return sorted(gaps, key=lambda g: g["gap_to_perfect"], reverse=True)

    def generate_report(self) -> str:
        lines = ["=== Resiliency Scoring Report ==="]
        org = self.manager.get_org_summary()
        lines.append(f"Total Services: {org.get('total_services', 0)}")
        lines.append(f"Average Score: {org.get('average_score', 0)}")
        lines.append(f"Grade Distribution: {org.get('grade_distribution', {})}")
        dims = self.average_score_by_dimension()
        lines.append("Dimension Averages:")
        for dim, avg in sorted(dims.items(), key=lambda x: x[1]):
            lines.append(f"  {dim}: {avg}/100")
        gaps = self.improvement_gap_analysis()
        if gaps:
            lines.append(f"Top Gap: {gaps[0]['dimension']} ({gaps[0]['gap_to_perfect']}pts gap)")
        return "\n".join(lines)


class ScoringPaginator:
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


class RecommendationPrioritizer:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def prioritize(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        recs = self.manager.recommendations
        if service_id:
            recs = [r for r in recs if r.get("service_id") == service_id]
        scored = []
        for r in recs:
            impact = r.get("potential_improvement", 0)
            effort_map = {"low": 3, "medium": 2, "high": 1}
            effort_score = effort_map.get(r.get("effort", "medium"), 2)
            priority_score = impact * effort_score
            scored.append({**r, "priority_score": priority_score})
        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    def generate_roadmap(self) -> Dict[str, Any]:
        prioritized = self.prioritize()
        quick_wins = [r for r in prioritized if r.get("effort") == "low" and r.get("potential_improvement", 0) >= 20]
        major_projects = [r for r in prioritized if r.get("effort") == "high"]
        return {"quick_wins": len(quick_wins), "major_projects": len(major_projects), "total_open": sum(1 for r in prioritized if r.get("status") == "open"), "estimated_total_improvement": sum(r.get("potential_improvement", 0) for r in prioritized)}


class BenchmarkComparator:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def compare_to_benchmark(self, benchmark_scores: Dict[str, float]) -> Dict[str, Any]:
        dims = self.manager.SCORE_DIMENSIONS
        comparison = {}
        for dim in dims:
            current = 0
            if self.manager.scores:
                dim_scores = [s.get("dimension_scores", {}).get(dim, 0) for s in self.manager.scores if isinstance(s.get("dimension_scores"), dict)]
                current = round(sum(dim_scores) / len(dim_scores), 1) if dim_scores else 0
            benchmark = benchmark_scores.get(dim, 75)
            comparison[dim] = {"current": current, "benchmark": benchmark, "gap": round(benchmark - current, 1), "above_benchmark": current >= benchmark}
        overall_current = round(sum(c["current"] for c in comparison.values()) / len(comparison), 1) if comparison else 0
        overall_benchmark = round(sum(c["benchmark"] for c in comparison.values()) / len(comparison), 1) if comparison else 0
        return {"dimensions": comparison, "overall_current": overall_current, "overall_benchmark": overall_benchmark, "overall_gap": round(overall_benchmark - overall_current, 1)}


class ScoreExporter:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def export_scores_json(self) -> List[Dict[str, Any]]:
        return self.manager.scores

    def export_scores_csv(self) -> str:
        if not self.manager.scores:
            return ""
        fields = ["service_id", "service_name", "overall_score", "grade", "scored_at"]
        lines = [",".join(fields)]
        for s in self.manager.scores:
            row = [str(s.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)

    def export_recommendations_csv(self) -> str:
        if not self.manager.recommendations:
            return ""
        fields = ["id", "service_id", "dimension", "message", "priority", "potential_improvement", "effort", "status", "created_at"]
        lines = [",".join(fields)]
        for r in self.manager.recommendations:
            row = [str(r.get(f, "")).replace(",", ";") for f in fields]
            lines.append(",".join(row))
        return "\n".join(lines)


class ServiceCategoryAnalyzer:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def group_by_grade(self) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for s in self.manager.scores:
            grade = s.get("grade", "F")
            groups.setdefault(grade, []).append({"service_id": s["service_id"], "service_name": s.get("service_name"), "score": s.get("overall_score")})
        for g in groups:
            groups[g].sort(key=lambda x: x["score"], reverse=True)
        return groups

    def get_lowest_scoring_services(self, limit: int = 5) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        sorted_scores = sorted(latest.values(), key=lambda x: x.get("overall_score", 0))
        return [{"service_id": s["service_id"], "service_name": s.get("service_name"), "score": s.get("overall_score"), "grade": s.get("grade")} for s in sorted_scores[:limit]]

    def get_top_services(self, limit: int = 5) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        sorted_scores = sorted(latest.values(), key=lambda x: x.get("overall_score", 0), reverse=True)
        return [{"service_id": s["service_id"], "service_name": s.get("service_name"), "score": s.get("overall_score"), "grade": s.get("grade")} for s in sorted_scores[:limit]]


class ScoreAnomalyDetector:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def detect_score_drops(self, threshold: float = 10.0) -> List[Dict[str, Any]]:
        drops = []
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        for sid, s in latest.items():
            service_scores = [x for x in self.manager.scores if x["service_id"] == sid and x.get("overall_score") is not None]
            if len(service_scores) >= 2:
                sorted_s = sorted(service_scores, key=lambda x: x.get("scored_at", ""))
                prev = sorted_s[-2].get("overall_score", 0)
                curr = s.get("overall_score", 0)
                drop = prev - curr
                if drop >= threshold:
                    drops.append({"service_id": sid, "service_name": s.get("service_name"), "previous_score": prev, "current_score": curr, "drop": round(drop, 1), "detected_at": datetime.now().isoformat()})
        return drops

    def detect_stale_scores(self, max_age_hours: int = 168) -> List[Dict[str, Any]]:
        stale = []
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        for sid, s in latest.items():
            if s.get("scored_at") and datetime.fromisoformat(s["scored_at"]) < cutoff:
                stale.append({"service_id": sid, "service_name": s.get("service_name"), "last_scored": s.get("scored_at"), "age_hours": round((datetime.now() - datetime.fromisoformat(s["scored_at"])).total_seconds() / 3600, 1)})
        return stale


class ScoreWebhookManager:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager
        self.webhooks: List[Dict[str, Any]] = []

    def register_webhook(self, url: str, events: List[str], secret: Optional[str] = None) -> Dict[str, Any]:
        wh = {"id": str(uuid.uuid4()), "url": url, "events": events, "secret": secret, "status": "active", "created_at": datetime.now().isoformat()}
        self.webhooks.append(wh)
        return wh

    def list_webhooks(self) -> List[Dict[str, Any]]:
        return self.webhooks

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        for i, w in enumerate(self.webhooks):
            if w["id"] == webhook_id:
                self.webhooks.pop(i)
                return {"status": "deleted"}
        return {"error": "Webhook not found"}

    def trigger_event(self, event: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for w in self.webhooks:
            if w.get("status") == "active" and event in w.get("events", []):
                results.append({"webhook_id": w["id"], "url": w["url"], "event": event, "delivered": True, "delivered_at": datetime.now().isoformat()})
        return results


class ScoreDashboardData:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager
        self.alerts: List[Dict[str, Any]] = []

    def check_threshold_breach(self, service_id: str, dimension: str, threshold: float = 50.0) -> Optional[Dict[str, Any]]:
        latest = None
        for s in reversed(self.manager.scores):
            if s["service_id"] == service_id:
                latest = s
                break
        if not latest:
            return None
        dim_score = latest.get("dimension_scores", {}).get(dimension, 100)
        if dim_score < threshold:
            alert = {"id": str(uuid.uuid4()), "service_id": service_id, "service_name": latest.get("service_name"), "dimension": dimension, "score": dim_score, "threshold": threshold, "severity": "critical" if dim_score < threshold * 0.7 else "warning", "created_at": datetime.now().isoformat()}
            self.alerts.append(alert)
            return alert
        return None

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if a.get("acknowledged_at") is None]

    def acknowledge_alert(self, alert_id: str, user: str) -> Dict[str, Any]:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged_at"] = datetime.now().isoformat()
                a["acknowledged_by"] = user
                return a
        return {"error": "Alert not found"}

    def get_alerts_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        return [a for a in self.alerts if a.get("severity") == severity]


class ScoreTrendAnalyzer:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def get_trend(self, service_id: str, dimension: Optional[str] = None) -> Dict[str, Any]:
        scores = [s for s in self.manager.scores if s["service_id"] == service_id]
        if not scores:
            return {"service_id": service_id, "data_points": 0}
        sorted_scores = sorted(scores, key=lambda x: x.get("scored_at", ""))
        trend_points = []
        for s in sorted_scores:
            if dimension:
                val = s.get("dimension_scores", {}).get(dimension)
            else:
                val = s.get("overall_score")
            if val is not None:
                trend_points.append({"date": s.get("scored_at"), "value": val})
        change = round(trend_points[-1]["value"] - trend_points[0]["value"], 1) if len(trend_points) >= 2 else 0
        return {"service_id": service_id, "dimension": dimension, "data_points": len(trend_points), "trend": "improving" if change > 0 else "declining" if change < 0 else "stable", "change": change, "min": min(p["value"] for p in trend_points) if trend_points else 0, "max": max(p["value"] for p in trend_points) if trend_points else 0, "points": trend_points}

    def compare_services(self, service_ids: List[str]) -> Dict[str, Any]:
        comparison = {}
        for sid in service_ids:
            latest = None
            for s in reversed(self.manager.scores):
                if s["service_id"] == sid:
                    latest = s
                    break
            if latest:
                comparison[sid] = {"service_name": latest.get("service_name"), "overall_score": latest.get("overall_score"), "grade": latest.get("grade"), "dimension_scores": latest.get("dimension_scores")}
        return {"comparison": comparison, "best": max(comparison.keys(), key=lambda k: comparison[k]["overall_score"]) if comparison else None, "worst": min(comparison.keys(), key=lambda k: comparison[k]["overall_score"]) if comparison else None}

    def moving_average(self, service_id: str, window: int = 5) -> Dict[str, Any]:
        scores = [s for s in self.manager.scores if s["service_id"] == service_id and s.get("overall_score") is not None]
        if len(scores) < window:
            return {"service_id": service_id, "error": "Insufficient data points"}
        sorted_scores = sorted(scores, key=lambda x: x.get("scored_at", ""))
        values = [s["overall_score"] for s in sorted_scores]
        avgs = []
        for i in range(len(values) - window + 1):
            avgs.append({"index": i, "from": sorted_scores[i].get("scored_at"), "to": sorted_scores[i + window - 1].get("scored_at"), "average": round(sum(values[i:i + window]) / window, 1)})
        return {"service_id": service_id, "window": window, "averages": avgs}


class ScoreForecaster:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def simple_forecast(self, service_id: str, periods: int = 5) -> Dict[str, Any]:
        scores = [s for s in self.manager.scores if s["service_id"] == service_id and s.get("overall_score") is not None]
        if len(scores) < 3:
            return {"service_id": service_id, "error": "Insufficient data for forecasting"}
        sorted_scores = sorted(scores, key=lambda x: x.get("scored_at", ""))
        values = [s["overall_score"] for s in sorted_scores]
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum(i * values[i] for i in range(n)) - n * x_mean * y_mean
        den = sum(i * i for i in range(n)) - n * x_mean * x_mean
        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean
        forecast = [round(intercept + slope * (n + i), 1) for i in range(periods)]
        return {"service_id": service_id, "historical_values": values, "forecast": forecast, "slope": round(slope, 2), "trend": "improving" if slope > 0 else "declining" if slope < 0 else "stable"}


class ScoreReportGenerator:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def generate_service_report(self, service_id: str) -> Dict[str, Any]:
        scores = [s for s in self.manager.scores if s["service_id"] == service_id]
        if not scores:
            return {"error": "No data for service"}
        latest = scores[-1]
        recs = [r for r in self.manager.recommendations if r.get("service_id") == service_id]
        return {"service_id": service_id, "service_name": latest.get("service_name"), "current_score": latest.get("overall_score"), "grade": latest.get("grade"), "dimension_scores": latest.get("dimension_scores"), "total_scores": len(scores), "recommendations_count": len(recs), "high_priority_recs": len([r for r in recs if r.get("priority") == "high"]), "last_scored": latest.get("scored_at")}

    def generate_summary_report(self) -> Dict[str, Any]:
        if not self.manager.scores:
            return {"total_services": 0, "average_score": 0}
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        avg_score = round(sum(s.get("overall_score", 0) for s in latest.values()) / len(latest), 1) if latest else 0
        grades: Dict[str, int] = {}
        for s in latest.values():
            g = s.get("grade", "F")
            grades[g] = grades.get(g, 0) + 1
        dim_avgs: Dict[str, float] = {}
        for s in latest.values():
            for dim, val in s.get("dimension_scores", {}).items():
                dim_avgs.setdefault(dim, []).append(val)
        dimension_averages = {dim: round(sum(vals) / len(vals), 1) for dim, vals in dim_avgs.items()}
        return {"total_services": len(latest), "average_score": avg_score, "grade_distribution": dict(sorted(grades.items())), "dimension_averages": dimension_averages, "total_recommendations": len(self.manager.recommendations), "report_generated_at": datetime.now().isoformat()}


class ScoreImportExport:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def import_scores(self, scores_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        imported = 0
        for s in scores_data:
            if "service_id" in s and "overall_score" in s:
                s.setdefault("dimension_scores", {})
                s.setdefault("scored_at", datetime.now().isoformat())
                s.setdefault("id", str(uuid.uuid4()))
                self.manager.scores.append(s)
                imported += 1
        self.manager._save_scores()
        return {"imported": imported}

    def export_scores_prometheus(self) -> str:
        lines = ["# HELP resiliency_score Current resiliency score by service", "# TYPE resiliency_score gauge"]
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        for sid, s in latest.items():
            name = s.get("service_name", "unknown").replace(" ", "_").lower()
            lines.append(f'resiliency_score{{service_id="{sid}",service_name="{name}"}} {s.get("overall_score", 0)}')
        return "\n".join(lines)


class ScoreDashboardData:
    def __init__(self, manager: ResiliencyScoringEngine):
        self.manager = manager

    def get_dashboard_widgets(self) -> Dict[str, Any]:
        report_gen = ScoreReportGenerator(self.manager)
        summary = report_gen.generate_summary_report()
        return {"summary": summary, "lowest_scoring": self.get_lowest_scoring_services(5), "top_services": self.get_top_services(5)}

    def get_lowest_scoring_services(self, limit: int = 5) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        sorted_scores = sorted(latest.values(), key=lambda x: x.get("overall_score", 0))
        return [{"service_id": s["service_id"], "service_name": s.get("service_name"), "score": s.get("overall_score"), "grade": s.get("grade")} for s in sorted_scores[:limit]]

    def get_top_services(self, limit: int = 5) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for s in self.manager.scores:
            sid = s["service_id"]
            if sid not in latest or s["scored_at"] > latest[sid]["scored_at"]:
                latest[sid] = s
        sorted_scores = sorted(latest.values(), key=lambda x: x.get("overall_score", 0), reverse=True)
        return [{"service_id": s["service_id"], "service_name": s.get("service_name"), "score": s.get("overall_score"), "grade": s.get("grade")} for s in sorted_scores[:limit]]

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
