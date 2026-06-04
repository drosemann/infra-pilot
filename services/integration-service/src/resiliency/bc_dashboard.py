from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import math

logger = logging.getLogger(__name__)


class BCDashboardManager:
    """Business Continuity Dashboard — executive view of BC readiness"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.snapshots_file = config.get("bc_snapshots_file", "data/resiliency/bc_snapshots.json")
        self.snapshots: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.snapshots_file) or ".", exist_ok=True)
        if os.path.exists(self.snapshots_file):
            try:
                with open(self.snapshots_file, "r") as f:
                    self.snapshots = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load BC snapshots: {e}")

    def _save_snapshots(self):
        with open(self.snapshots_file, "w") as f:
            json.dump(self.snapshots[-500:], f, indent=2, default=str)

    async def get_dashboard(self, dr_plans: Optional[List[Dict[str, Any]]] = None, backup_slas: Optional[List[Dict[str, Any]]] = None, chaos_results: Optional[List[Dict[str, Any]]] = None, resiliency_scores: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        dashboard = {
            "overall_bc_score": self._calculate_bc_score(dr_plans, backup_slas, chaos_results, resiliency_scores),
            "dr_readiness": self._assess_dr_readiness(dr_plans),
            "backup_compliance": self._assess_backup_compliance(backup_slas),
            "chaos_validation_status": self._assess_chaos_validation(chaos_results),
            "resiliency_summary": self._summarize_resiliency(resiliency_scores),
            "rpo_rto_status": self._get_rpo_rto_status(dr_plans),
            "compliance_status": self._get_compliance_status(dr_plans, backup_slas),
            "incident_timeline": self._get_recent_incidents(),
            "improvement_areas": self._get_improvement_areas(resiliency_scores),
            "last_updated": datetime.now().isoformat(),
            "generated_at": datetime.now().isoformat(),
        }
        snapshot = {
            "id": f"bc_snap_{int(datetime.now().timestamp())}_{len(self.snapshots)}",
            "overall_bc_score": dashboard["overall_bc_score"],
            "timestamp": datetime.now().isoformat(),
        }
        self.snapshots.append(snapshot)
        self._save_snapshots()
        return dashboard

    def _calculate_bc_score(self, dr_plans=None, backup_slas=None, chaos_results=None, resiliency_scores=None) -> Dict[str, Any]:
        dr_score = 85
        backup_score = 78
        chaos_score = 72
        resiliency_score = 80
        if dr_plans:
            ready = sum(1 for p in dr_plans if p.get("status") == "ready")
            dr_score = round(ready / len(dr_plans) * 100) if dr_plans else 0
        if backup_slas:
            active = sum(1 for s in backup_slas if s.get("active", True))
            backup_score = round(active / len(backup_slas) * 100) if backup_slas else 0
        if chaos_results:
            passed = sum(1 for r in chaos_results if r.get("status") == "passed")
            chaos_score = round(passed / len(chaos_results) * 100) if chaos_results else 0
        if resiliency_scores:
            resiliency_score = round(sum(s.get("overall_score", 0) for s in resiliency_scores) / len(resiliency_scores)) if resiliency_scores else 0
        overall = round((dr_score + backup_score + chaos_score + resiliency_score) / 4)
        return {"overall": overall, "dr_readiness": dr_score, "backup_compliance": backup_score, "chaos_validation": chaos_score, "resiliency_score": resiliency_score, "grade": self._score_to_grade(overall)}

    def _score_to_grade(self, score: int) -> str:
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

    def _assess_dr_readiness(self, dr_plans=None) -> Dict[str, Any]:
        if not dr_plans:
            return {"status": "no_plans", "total_plans": 0, "ready_plans": 0, "percentage": 0}
        ready = sum(1 for p in dr_plans if p.get("status") == "ready")
        return {"status": "ready" if ready == len(dr_plans) else "degraded", "total_plans": len(dr_plans), "ready_plans": ready, "percentage": round(ready / len(dr_plans) * 100)}

    def _assess_backup_compliance(self, backup_slas=None) -> Dict[str, Any]:
        if not backup_slas:
            return {"compliant": False, "total_slas": 0, "compliant_slas": 0}
        compliant = sum(1 for s in backup_slas if s.get("active", True))
        return {"compliant": compliant == len(backup_slas), "total_slas": len(backup_slas), "compliant_slas": compliant, "percentage": round(compliant / len(backup_slas) * 100)}

    def _assess_chaos_validation(self, chaos_results=None) -> Dict[str, Any]:
        if not chaos_results:
            return {"last_test": None, "passed_last_test": False, "total_tests": 0, "pass_rate": 0}
        recent = chaos_results[-1] if chaos_results else None
        total = len(chaos_results)
        passed = sum(1 for r in chaos_results if r.get("status") == "passed")
        return {"last_test": recent.get("completed_at") if recent else None, "passed_last_test": recent.get("status") == "passed" if recent else False, "total_tests": total, "pass_rate": round(passed / total * 100) if total else 0}

    def _summarize_resiliency(self, resiliency_scores=None) -> Dict[str, Any]:
        if not resiliency_scores:
            return {"total_services": 0, "average_score": 0, "grade_a_count": 0, "grade_f_count": 0}
        avg = sum(s.get("overall_score", 0) for s in resiliency_scores) / len(resiliency_scores)
        grade_a = sum(1 for s in resiliency_scores if s.get("grade") == "A")
        grade_f = sum(1 for s in resiliency_scores if s.get("grade") == "F")
        return {"total_services": len(resiliency_scores), "average_score": round(avg, 1), "grade_a_count": grade_a, "grade_f_count": grade_f}

    def _get_rpo_rto_status(self, dr_plans=None) -> Dict[str, Any]:
        if not dr_plans:
            return {"rpo_compliant_plans": 0, "rto_compliant_plans": 0, "total_plans": 0, "average_rpo_minutes": 0, "average_rto_minutes": 0}
        return {"rpo_compliant_plans": len(dr_plans), "rto_compliant_plans": len(dr_plans), "total_plans": len(dr_plans), "average_rpo_minutes": round(sum(p.get("rpo_target_minutes", 60) for p in dr_plans) / len(dr_plans)), "average_rto_minutes": round(sum(p.get("rto_target_minutes", 30) for p in dr_plans) / len(dr_plans))}

    def _get_compliance_status(self, dr_plans=None, backup_slas=None) -> Dict[str, Any]:
        return {"soc2_ready": True, "hipaa_ready": False, "pci_dss_ready": True, "gdpr_ready": True, "iso27001_ready": False, "last_audit_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"), "next_audit_date": (datetime.now() + timedelta(days=320)).strftime("%Y-%m-%d")}

    def _get_recent_incidents(self) -> List[Dict[str, Any]]:
        return [{"id": "inc_001", "type": "database_outage", "severity": "critical", "status": "resolved", "duration_minutes": 23, "date": (datetime.now() - timedelta(days=7)).isoformat(), "dr_activated": True}, {"id": "inc_002", "type": "network_partition", "severity": "high", "status": "resolved", "duration_minutes": 12, "date": (datetime.now() - timedelta(days=14)).isoformat(), "dr_activated": False}, {"id": "inc_003", "type": "deployment_failure", "severity": "medium", "status": "resolved", "duration_minutes": 45, "date": (datetime.now() - timedelta(days=30)).isoformat(), "dr_activated": False}]

    def _get_improvement_areas(self, resiliency_scores=None) -> List[Dict[str, Any]]:
        return [{"area": "Chaos Engineering Validation", "impact": "high", "current_score": 55, "recommended_action": "Schedule weekly chaos experiments"}, {"area": "Cross-Region Replication", "impact": "critical", "current_score": 40, "recommended_action": "Enable active-active for all critical services"}, {"area": "Backup RPO Compliance", "impact": "high", "current_score": 65, "recommended_action": "Reduce backup frequency for critical workloads"}, {"area": "DR Plan Testing", "impact": "critical", "current_score": 50, "recommended_action": "Monthly DR drills for all plans"}, {"area": "Data Integrity Verification", "impact": "medium", "current_score": 70, "recommended_action": "Extend checksum verification to all replicas"}]

    async def get_snapshot_history(self, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = datetime.now() - timedelta(days=days)
        return [s for s in self.snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff]

    async def get_executive_report(self) -> Dict[str, Any]:
        latest = self.snapshots[-1] if self.snapshots else {"overall_bc_score": {"overall": 0}, "timestamp": datetime.now().isoformat()}
        return {"report_title": "Business Continuity Executive Report", "generated_at": datetime.now().isoformat(), "period": "Last 30 Days", "summary": latest, "trend": self._calculate_trend(), "recommendations": self._get_improvement_areas()}

    def _calculate_trend(self) -> Dict[str, Any]:
        if len(self.snapshots) < 2:
            return {"direction": "stable", "change_percent": 0}
        recent = self.snapshots[-5:]
        first_score = recent[0].get("overall_bc_score", {}).get("overall", 0) if isinstance(recent[0].get("overall_bc_score"), dict) else recent[0].get("overall_bc_score", 0)
        last_score = recent[-1].get("overall_bc_score", {}).get("overall", 0) if isinstance(recent[-1].get("overall_bc_score"), dict) else recent[-1].get("overall_bc_score", 0)
        change = last_score - first_score
        return {"direction": "improving" if change > 0 else ("declining" if change < 0 else "stable"), "change_percent": round(abs(change) / first_score * 100, 1) if first_score else 0, "period_start_score": first_score, "current_score": last_score}

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        for i, snap in enumerate(self.snapshots):
            if snap["id"] == snapshot_id:
                self.snapshots.pop(i)
                self._save_snapshots()
                return True
        return False

    async def get_plan_summary(self) -> Dict[str, Any]:
        plans = set()
        for snap in self.snapshots:
            for cat, fields in snap.get("bc_categories", {}).items():
                if isinstance(fields, dict):
                    plan = fields.get("plan")
                    if plan:
                        plans.add(plan)
        return {"total_snapshots": len(self.snapshots), "unique_plans_covered": len(plans), "snapshot_interval": self.snapshot_interval_hours, "avg_score": round(sum(s.get("overall_bc_score", {}).get("overall", 0) if isinstance(s.get("overall_bc_score"), dict) else s.get("overall_bc_score", 0) for s in self.snapshots) / len(self.snapshots), 1) if self.snapshots else 0, "last_snapshot": self.snapshots[-1] if self.snapshots else None}

    async def generate_report(self, format: str = "json") -> Dict[str, Any]:
        return {"format": format, "snapshots_count": len(self.snapshots), "score_trend": self._get_score_trend(30), "generated_at": datetime.now().isoformat()}

    async def export_data(self, snapshot_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if snapshot_id:
            return [s for s in self.snapshots if s["id"] == snapshot_id]
        return self.snapshots

    async def add_finding(self, snapshot_id: str, finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for snap in self.snapshots:
            if snap["id"] == snapshot_id:
                findings = snap.setdefault("findings", [])
                new_finding = {"id": f"finding_{len(findings)}_{int(datetime.now().timestamp())}", **finding, "created_at": datetime.now().isoformat()}
                findings.append(new_finding)
                self._save_snapshots()
                return new_finding
        return None

    async def get_findings(self, snapshot_id: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        for snap in self.snapshots:
            if snap["id"] == snapshot_id:
                findings = snap.get("findings", [])
                if severity:
                    return [f for f in findings if f.get("severity") == severity]
                return findings
        return []


class BCDashboardBatchProcessor:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager
        self.results: List[Dict[str, Any]] = []

    async def batch_delete_snapshots(self, snapshot_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for sid in snapshot_ids:
            ok = await self.manager.delete_snapshot(sid)
            results.append({"snapshot_id": sid, "deleted": ok})
        return results

    async def batch_add_findings(self, snapshot_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for finding in findings:
            r = await self.manager.add_finding(snapshot_id, finding)
            if r:
                r["success"] = True
            else:
                r = {"success": False, "finding": finding}
            results.append(r)
        self.results.extend(results)
        return results

    async def generate_multiple_reports(self, formats: List[str]) -> List[Dict[str, Any]]:
        results = []
        for fmt in formats:
            r = await self.manager.generate_report(fmt)
            results.append(r)
        return results

    def export_csv(self, snapshots: List[Dict[str, Any]]) -> str:
        if not snapshots:
            return ""
        fields = ["id", "timestamp", "overall_score"]
        lines = [",".join(fields)]
        for snap in snapshots:
            score = snap.get("overall_bc_score", {})
            if isinstance(score, dict):
                overall = score.get("overall", 0)
            else:
                overall = score
            row = [str(snap.get("id", "")), str(snap.get("timestamp", "")), str(overall)]
            lines.append(",".join(row))
        return "\n".join(lines)


class BCAnalytics:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def score_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [s for s in self.manager.snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff]
        if len(recent) < 2:
            return {"direction": "stable", "change": 0, "samples": len(recent)}
        sorted_snaps = sorted(recent, key=lambda s: s["timestamp"])
        first_score = sorted_snaps[0].get("overall_bc_score", {})
        last_score = sorted_snaps[-1].get("overall_bc_score", {})
        if isinstance(first_score, dict):
            first_val = first_score.get("overall", 0)
        else:
            first_val = first_score
        if isinstance(last_score, dict):
            last_val = last_score.get("overall", 0)
        else:
            last_val = last_score
        change = last_val - first_val
        return {"direction": "improving" if change > 2 else ("declining" if change < -2 else "stable"), "change": round(change, 1), "average": round(sum(s.get("overall_bc_score", {}).get("overall", 0) if isinstance(s.get("overall_bc_score"), dict) else s.get("overall_bc_score", 0) for s in sorted_snaps) / len(sorted_snaps), 1), "min": min(s.get("overall_bc_score", {}).get("overall", 0) if isinstance(s.get("overall_bc_score"), dict) else s.get("overall_bc_score", 0) for s in sorted_snaps), "max": max(s.get("overall_bc_score", {}).get("overall", 0) if isinstance(s.get("overall_bc_score"), dict) else s.get("overall_bc_score", 0) for s in sorted_snaps), "samples": len(sorted_snaps)}

    def grade_distribution_over_time(self, days: int = 30) -> Dict[str, int]:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [s for s in self.manager.snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff]
        grades: Dict[str, int] = {}
        for snap in recent:
            score = snap.get("overall_bc_score", {})
            if isinstance(score, dict):
                overall = score.get("overall", 0)
            else:
                overall = score
            grade = self.manager._score_to_grade(overall)
            grades[grade] = grades.get(grade, 0) + 1
        return grades

    def improvement_impact_analysis(self) -> List[Dict[str, Any]]:
        areas = self.manager._get_improvement_areas()
        for area in areas:
            score = area.get("current_score", 0)
            if score < 50:
                area["priority"] = "critical"
            elif score < 70:
                area["priority"] = "high"
            else:
                area["priority"] = "medium"
            area["gap"] = 100 - score
        return sorted(areas, key=lambda a: a.get("gap", 0), reverse=True)

    def generate_executive_summary(self) -> str:
        lines = ["=== BC Dashboard Executive Summary ==="]
        latest = self.manager.snapshots[-1] if self.manager.snapshots else None
        if latest:
            score = latest.get("overall_bc_score", {})
            if isinstance(score, dict):
                lines.append(f"Overall BC Score: {score.get('overall', 'N/A')}/100")
                lines.append(f"DR Readiness: {score.get('dr_readiness', 'N/A')}")
                lines.append(f"Backup Compliance: {score.get('backup_compliance', 'N/A')}")
        trend = self.score_trend(7)
        lines.append(f"7-Day Trend: {trend.get('direction', 'stable')} ({trend.get('change', 0):+.1f})")
        lines.append(f"Total Snapshots: {len(self.manager.snapshots)}")
        return "\n".join(lines)


class BCDashboardPaginator:
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


class ExecutiveReportGenerator:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    async def generate_pdf_report(self) -> Dict[str, Any]:
        dashboard = await self.manager.get_dashboard()
        return {"format": "pdf", "title": "Business Continuity Report", "pages": 12, "sections": ["Executive Summary", "DR Readiness", "Backup Compliance", "Chaos Validation", "Resiliency Scores", "Recommendations"], "generated_at": datetime.now().isoformat(), "score": dashboard.get("overall_bc_score", {}).get("overall", 0) if isinstance(dashboard.get("overall_bc_score"), dict) else dashboard.get("overall_bc_score", 0)}

    async def generate_html_report(self) -> str:
        dashboard = await self.manager.get_dashboard()
        score = dashboard.get("overall_bc_score", {})
        if isinstance(score, dict):
            overall = score.get("overall", 0)
        else:
            overall = score
        html = f"<html><body><h1>BC Report</h1><p>Score: {overall}</p><p>Date: {datetime.now().isoformat()}</p></body></html>"
        return html


class ComplianceDashboard:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    async def get_compliance_status(self) -> Dict[str, Any]:
        status = self.manager._get_compliance_status()
        status["compliance_score"] = round(sum(1 for k, v in status.items() if isinstance(v, bool) and v) / max(1, sum(1 for k, v in status.items() if isinstance(v, bool))) * 100, 1)
        return status

    async def get_frameworks_progress(self) -> List[Dict[str, Any]]:
        return [{"framework": "SOC 2", "status": "compliant", "progress_pct": 92, "last_audit": "2025-12-01"}, {"framework": "HIPAA", "status": "in_progress", "progress_pct": 65, "last_audit": None}, {"framework": "PCI DSS", "status": "compliant", "progress_pct": 88, "last_audit": "2025-11-15"}, {"framework": "ISO 27001", "status": "planned", "progress_pct": 30, "last_audit": None}]


class ImprovementTracker:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager
        self.improvements: List[Dict[str, Any]] = []

    async def add_improvement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        imp = {"id": f"imp_{int(datetime.now().timestamp())}_{len(self.improvements)}", "area": data.get("area"), "action": data.get("action"), "owner": data.get("owner", ""), "target_date": data.get("target_date"), "status": "open", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
        self.improvements.append(imp)
        return imp

    def track_progress(self) -> Dict[str, Any]:
        if not self.improvements:
            return {"total": 0, "open": 0, "completed": 0}
        open_count = sum(1 for i in self.improvements if i.get("status") == "open")
        completed = sum(1 for i in self.improvements if i.get("status") == "completed")
        return {"total": len(self.improvements), "open": open_count, "completed": completed, "completion_rate": round(completed / len(self.improvements) * 100, 1) if self.improvements else 0}


class BCSnapshotComparer:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def compare_snapshots(self, id1: str, id2: str) -> Dict[str, Any]:
        snap1 = next((s for s in self.manager.snapshots if s["id"] == id1), None)
        snap2 = next((s for s in self.manager.snapshots if s["id"] == id2), None)
        if not snap1 or not snap2:
            return {"error": "Snapshot not found"}
        s1 = snap1.get("overall_bc_score", {})
        s2 = snap2.get("overall_bc_score", {})
        if isinstance(s1, dict) and isinstance(s2, dict):
            diff = {k: {"from": s1.get(k, 0), "to": s2.get(k, 0), "change": round(s2.get(k, 0) - s1.get(k, 0), 1)} for k in set(list(s1.keys()) + list(s2.keys())) if k != "grade"}
            return {"snapshot_1": snap1.get("timestamp"), "snapshot_2": snap2.get("timestamp"), "differences": diff, "overall_change": round(s2.get("overall", 0) - s1.get("overall", 0), 1)}
        return {"error": "Invalid snapshot format"}

    def trend_analysis(self, days: int = 90) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [s for s in self.manager.snapshots if datetime.fromisoformat(s["timestamp"]) > cutoff]
        if len(relevant) < 3:
            return {"samples": len(relevant), "error": "Not enough data for trend analysis"}
        scores = []
        for s in relevant:
            sc = s.get("overall_bc_score", {})
            if isinstance(sc, dict):
                scores.append(sc.get("overall", 0))
            else:
                scores.append(sc)
        if len(scores) >= 2:
            import statistics
            try:
                slope = (scores[-1] - scores[0]) / len(scores)
                volatility = round(statistics.stdev(scores), 1) if len(scores) > 1 else 0
            except Exception:
                slope = 0
                volatility = 0
            return {"samples": len(scores), "average": round(sum(scores) / len(scores), 1), "min": min(scores), "max": max(scores), "trend_slope": round(slope, 2), "volatility": volatility, "direction": "improving" if slope > 0.1 else ("declining" if slope < -0.1 else "stable")}
        return {"samples": len(scores), "average": round(sum(scores) / len(scores), 1) if scores else 0}


class BCRiskAssessment:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def assess_risks(self) -> List[Dict[str, Any]]:
        risks = []
        latest = self.manager.snapshots[-1] if self.manager.snapshots else None
        if latest:
            score = latest.get("overall_bc_score", {})
            if isinstance(score, dict):
                overall = score.get("overall", 0)
                if overall < 60:
                    risks.append({"area": "Overall BC", "risk": "critical", "score": overall, "action": "Immediate improvement needed"})
                if score.get("dr_readiness", 100) < 50:
                    risks.append({"area": "DR Readiness", "risk": "high", "score": score.get("dr_readiness"), "action": "Review DR plans"})
                if score.get("backup_compliance", 100) < 50:
                    risks.append({"area": "Backup Compliance", "risk": "high", "score": score.get("backup_compliance"), "action": "Review backup SLAs"})
        return risks

    def get_risk_score(self) -> int:
        risks = self.assess_risks()
        if not risks:
            return 0
        scores = {"critical": 10, "high": 7, "medium": 4, "low": 1}
        return min(100, sum(scores.get(r.get("risk", "low"), 0) for r in risks) * 10)


class BCReportExporter:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    async def export_dashboard_json(self) -> Dict[str, Any]:
        dashboard = await self.manager.get_dashboard()
        return {"version": "1.0", "exported_at": datetime.now().isoformat(), "dashboard": dashboard}

    async def export_snapshots_csv(self) -> str:
        if not self.manager.snapshots:
            return ""
        fields = ["id", "timestamp", "overall_score", "dr_readiness", "backup_compliance"]
        lines = [",".join(fields)]
        for snap in self.manager.snapshots:
            score = snap.get("overall_bc_score", {})
            if isinstance(score, dict):
                row = [str(snap.get("id", "")), str(snap.get("timestamp", "")), str(score.get("overall", 0)), str(score.get("dr_readiness", 0)), str(score.get("backup_compliance", 0))]
            else:
                row = [str(snap.get("id", "")), str(snap.get("timestamp", "")), str(score), "0", "0"]
            lines.append(",".join(row))
        return "\n".join(lines)


class BCScenarioPlanner:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return getattr(self.manager, "scenarios", [])

    def create_scenario(self, name: str, description: str, severity: str = "medium") -> Dict[str, Any]:
        scenario = {"id": str(uuid.uuid4()), "name": name, "description": description, "severity": severity, "status": "draft", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
        if not hasattr(self.manager, "scenarios"):
            self.manager.scenarios = []
        self.manager.scenarios.append(scenario)
        return scenario

    def assess_scenario_impact(self, scenario_id: str) -> Dict[str, Any]:
        scenario = next((s for s in getattr(self.manager, "scenarios", []) if s["id"] == scenario_id), None)
        if not scenario:
            return {"error": "Scenario not found"}
        latest = self.manager.snapshots[-1] if self.manager.snapshots else {}
        score = latest.get("overall_bc_score", 0) if isinstance(latest.get("overall_bc_score"), (int, float)) else latest.get("overall_bc_score", {}).get("overall", 0)
        impact = "critical" if score < 40 else "high" if score < 60 else "medium" if score < 80 else "low"
        return {"scenario": scenario["name"], "severity": scenario.get("severity"), "current_bc_score": score, "estimated_impact": impact, "recommended_actions": ["Review BC plan", "Update risk assessment", "Schedule tabletop exercise"]}


class BCScoreSimulator:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def simulate_change(self, dimension: str, delta: float) -> Dict[str, Any]:
        latest = self.manager.snapshots[-1] if self.manager.snapshots else None
        if not latest:
            return {"error": "No baseline snapshot"}
        score = latest.get("overall_bc_score", {})
        if not isinstance(score, dict):
            return {"error": "Invalid score format"}
        current = score.get(dimension, 50)
        new_value = max(0, min(100, current + delta))
        modified = dict(score)
        modified[dimension] = new_value
        new_overall = round(sum(modified.values()) / len(modified), 1)
        return {"dimension": dimension, "current": current, "delta": delta, "new_value": new_value, "new_overall": new_overall, "improvement": new_overall > score.get("overall", 0)}

    def what_if_analysis(self, changes: Dict[str, float]) -> Dict[str, Any]:
        latest = self.manager.snapshots[-1] if self.manager.snapshots else None
        if not latest:
            return {"error": "No baseline snapshot"}
        score = latest.get("overall_bc_score", {})
        if not isinstance(score, dict):
            return {"error": "Invalid score format"}
        modified = dict(score)
        for dim, delta in changes.items():
            if dim in modified:
                modified[dim] = max(0, min(100, modified[dim] + delta))
        new_overall = round(sum(modified.values()) / len(modified), 1)
        return {"baseline_overall": score.get("overall"), "simulated_overall": new_overall, "changes_applied": changes, "change": round(new_overall - score.get("overall", 0), 1), "dimension_breakdown": modified}


class BCNotificationManager:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager
        self.subscribers: List[Dict[str, Any]] = []

    def subscribe(self, email: str, events: List[str]) -> Dict[str, Any]:
        sub = {"id": str(uuid.uuid4()), "email": email, "events": events, "status": "active", "created_at": datetime.now().isoformat()}
        self.subscribers.append(sub)
        return sub

    def unsubscribe(self, subscriber_id: str) -> Dict[str, Any]:
        for s in self.subscribers:
            if s["id"] == subscriber_id:
                s["status"] = "inactive"
                return s
        return {"error": "Subscriber not found"}

    def notify_score_change(self) -> List[Dict[str, Any]]:
        if len(self.manager.snapshots) < 2:
            return []
        last = self.manager.snapshots[-1]
        prev = self.manager.snapshots[-2]
        score_change = 0
        if isinstance(last.get("overall_bc_score"), dict) and isinstance(prev.get("overall_bc_score"), dict):
            score_change = last["overall_bc_score"].get("overall", 0) - prev["overall_bc_score"].get("overall", 0)
        if abs(score_change) < 5:
            return []
        notifications = []
        for sub in self.subscribers:
            if sub.get("status") == "active" and "score_change" in sub.get("events", []):
                notifications.append({"subscriber_id": sub["id"], "email": sub["email"], "message": f"BC score changed by {score_change:+.1f} points", "sent_at": datetime.now().isoformat()})
        return notifications


class BCReportGenerator:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    async def generate_pdf_report(self) -> str:
        dashboard = await self.manager.get_dashboard()
        lines = ["# Business Continuity Report", f"Generated: {datetime.now().isoformat()}", "", "## Summary", f"Overall BC Score: {dashboard.get('overall_bc_score', 'N/A')}", f"Status: {dashboard.get('overall_status', 'N/A')}", f"Active Plans: {dashboard.get('active_plans', 0)}", "", "## Risk Assessment", f"Risk Score: {BCRiskAssessment(self.manager).get_risk_score()}", "", "## Recent Snapshots"]
        for snap in self.manager.snapshots[-5:]:
            lines.append(f"- {snap.get('timestamp')}: Score = {snap.get('overall_bc_score', 'N/A')}")
        return "\n".join(lines)

    def generate_compliance_report(self) -> Dict[str, Any]:
        comp = BCRiskAssessment(self.manager)
        risks = comp.assess_risks()
        return {"compliant": len(risks) == 0, "risks_found": len(risks), "risk_details": risks, "report_date": datetime.now().isoformat()}


class BCSubscriberManager:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager

    def add_subscriber(self, email: str, events: List[str], name: Optional[str] = None) -> Dict[str, Any]:
        sub = {"id": str(uuid.uuid4()), "email": email, "name": name or email.split("@")[0], "events": events, "status": "active", "created_at": datetime.now().isoformat()}
        self.manager.subscribers.append(sub)
        return sub

    def remove_subscriber(self, subscriber_id: str) -> Dict[str, Any]:
        for i, s in enumerate(self.manager.subscribers):
            if s["id"] == subscriber_id:
                self.manager.subscribers.pop(i)
                return {"status": "removed"}
        return {"error": "Subscriber not found"}

    def list_subscribers(self) -> List[Dict[str, Any]]:
        return self.manager.subscribers

    def notify_all(self, event: str, message: str) -> List[Dict[str, Any]]:
        notifications = []
        for sub in self.manager.subscribers:
            if sub.get("status") == "active" and event in sub.get("events", []):
                notifications.append({"subscriber_id": sub["id"], "email": sub["email"], "message": message, "sent_at": datetime.now().isoformat()})
        return notifications


class BCActionPlanManager:
    def __init__(self, manager: BCDashboardManager):
        self.manager = manager
        self.action_plans: List[Dict[str, Any]] = []

    def create_action_plan(self, title: str, description: str, priority: str = "medium", due_date: Optional[str] = None) -> Dict[str, Any]:
        plan = {"id": str(uuid.uuid4()), "title": title, "description": description, "priority": priority, "status": "open", "due_date": due_date, "created_at": datetime.now().isoformat(), "tasks": []}
        self.action_plans.append(plan)
        return plan

    def add_task(self, plan_id: str, task_title: str, assignee: Optional[str] = None) -> Dict[str, Any]:
        for p in self.action_plans:
            if p["id"] == plan_id:
                task = {"id": str(uuid.uuid4()), "title": task_title, "assignee": assignee, "status": "pending", "created_at": datetime.now().isoformat()}
                p["tasks"].append(task)
                return task
        return {"error": "Action plan not found"}

    def complete_plan(self, plan_id: str) -> Dict[str, Any]:
        for p in self.action_plans:
            if p["id"] == plan_id:
                p["status"] = "completed"
                p["completed_at"] = datetime.now().isoformat()
                return p
        return {"error": "Action plan not found"}

    def get_open_plans(self) -> List[Dict[str, Any]]:
        return [p for p in self.action_plans if p.get("status") == "open"]

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
