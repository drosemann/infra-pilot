"""Feature 58: Change Risk Analysis — Analyze planned changes against historical data."""

import json
import os
import uuid
import math
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class ChangeType(Enum):
    DEPLOYMENT = "deployment"
    CONFIG_CHANGE = "config_change"
    SCALE_CHANGE = "scale_change"
    MIGRATION = "migration"
    ROLLBACK = "rollback"
    DNS_CHANGE = "dns_change"
    FIREWALL_RULE = "firewall_rule"
    CERTIFICATE_UPDATE = "certificate_update"
    DATABASE_CHANGE = "database_change"
    OTHER = "other"


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class ChangeStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ChangeRiskAnalyzer:
    """Analyze planned changes against historical data to predict risk."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.similarity_lookback_days = config.get("similarity_lookback_days", 90)
        self.min_historical_samples = config.get("min_historical_samples", 5)
        self.high_risk_threshold = config.get("high_risk_threshold", 0.7)
        self.medium_risk_threshold = config.get("medium_risk_threshold", 0.4)
        self.changes_file = _data_file('change_risk_changes.json')
        self.analyses_file = _data_file('change_risk_analyses.json')
        self.history_file = _data_file('change_risk_history.json')
        self.changes: List[Dict[str, Any]] = []
        self.analyses: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.changes_file, "changes"),
            (self.analyses_file, "analyses"),
            (self.history_file, "history")
        ]:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if target == "changes":
                    self.changes = data
                elif target == "analyses":
                    self.analyses = data
                elif target == "history":
                    self.history = data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _save_changes(self):
        with open(self.changes_file, 'w') as f:
            json.dump(self.changes, f, default=str)

    def _save_analyses(self):
        with open(self.analyses_file, 'w') as f:
            json.dump(self.analyses[-5000:], f, default=str)

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, default=str)

    def plan_change(self, title: str, description: str, change_type: str,
                    target_service: str, affected_components: List[str],
                    metadata: Dict[str, Any] = None,
                    scheduled_time: str = None) -> Dict[str, Any]:
        change = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "change_type": change_type,
            "target_service": target_service,
            "affected_components": affected_components,
            "metadata": metadata or {},
            "status": ChangeStatus.PENDING.value,
            "scheduled_time": scheduled_time or datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.changes.append(change)
        self._save_changes()
        analysis = self.analyze(change["id"])
        return {"change": change, "analysis": analysis}

    def analyze(self, change_id: str) -> Dict[str, Any]:
        change = next((c for c in self.changes if c["id"] == change_id), None)
        if not change:
            return {"error": f"Change {change_id} not found"}
        historical = self._find_historical_similar(change)
        risk_factors = self._evaluate_risk_factors(change, historical)
        overall_risk = self._compute_overall_risk(risk_factors)
        recommendations = self._generate_recommendations(risk_factors, overall_risk, historical)
        historical_success_rate = self._compute_historical_success_rate(historical)
        similar_incidents = self._find_similar_incidents(historical)
        analysis = {
            "id": str(uuid.uuid4()),
            "change_id": change_id,
            "change_title": change["title"],
            "overall_risk_level": overall_risk["level"],
            "overall_risk_score": overall_risk["score"],
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "historical_similar_count": len(historical),
            "historical_success_rate": round(historical_success_rate, 4),
            "similar_incidents": similar_incidents[:5],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.analyses.append(analysis)
        self._save_analyses()
        return analysis

    def _find_historical_similar(self, change: Dict[str, Any]) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=self.similarity_lookback_days)
        candidates = []
        for h in self.history:
            try:
                h_time = datetime.fromisoformat(h.get("created_at", ""))
                if h_time < cutoff:
                    continue
            except (ValueError, TypeError):
                continue
            sim = self._compute_similarity(change, h)
            if sim >= 0.3:
                candidates.append((h, sim))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:20]]

    def _compute_similarity(self, change_a: Dict[str, Any], change_b: Dict[str, Any]) -> float:
        score = 0.0
        weights = {"type": 0.3, "service": 0.3, "components": 0.2, "title": 0.2}
        if change_a.get("change_type") == change_b.get("change_type"):
            score += weights["type"]
        if change_a.get("target_service") == change_b.get("target_service"):
            score += weights["service"]
        comps_a = set(change_a.get("affected_components", []))
        comps_b = set(change_b.get("affected_components", []))
        if comps_a and comps_b:
            overlap = len(comps_a & comps_b) / len(comps_a | comps_b)
            score += weights["components"] * overlap
        words_a = set(change_a.get("title", "").lower().split())
        words_b = set(change_b.get("title", "").lower().split())
        if words_a and words_b:
            text_sim = len(words_a & words_b) / len(words_a | words_b)
            score += weights["title"] * text_sim
        return score

    def _evaluate_risk_factors(self, change: Dict[str, Any],
                                 historical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        factors = []
        change_type = change.get("change_type", ChangeType.OTHER.value)
        target = change.get("target_service", "unknown")
        hour = datetime.utcnow().hour
        type_risk = {
            ChangeType.DEPLOYMENT.value: 0.4,
            ChangeType.CONFIG_CHANGE.value: 0.5,
            ChangeType.SCALE_CHANGE.value: 0.3,
            ChangeType.MIGRATION.value: 0.8,
            ChangeType.ROLLBACK.value: 0.6,
            ChangeType.DNS_CHANGE.value: 0.5,
            ChangeType.FIREWALL_RULE.value: 0.6,
            ChangeType.CERTIFICATE_UPDATE.value: 0.3,
            ChangeType.DATABASE_CHANGE.value: 0.7,
            ChangeType.OTHER.value: 0.5,
        }
        factors.append({
            "name": "change_type",
            "label": "Change Type Risk",
            "score": type_risk.get(change_type, 0.5),
            "details": f"Change type '{change_type}' has baseline risk of {type_risk.get(change_type, 0.5):.0%}",
        })
        if len(change.get("affected_components", [])) > 5:
            factors.append({
                "name": "blast_radius",
                "label": "Blast Radius",
                "score": 0.7,
                "details": f"Change affects {len(change['affected_components'])} components — large blast radius",
            })
        elif len(change.get("affected_components", [])) > 2:
            factors.append({
                "name": "blast_radius",
                "label": "Blast Radius",
                "score": 0.4,
                "details": f"Change affects {len(change['affected_components'])} components — moderate blast radius",
            })
        else:
            factors.append({
                "name": "blast_radius",
                "label": "Blast Radius",
                "score": 0.2,
                "details": "Change affects few components — small blast radius",
            })
        failed = sum(1 for h in historical if h.get("status") in
                     (ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value))
        total = len(historical)
        if total >= self.min_historical_samples:
            fail_rate = failed / total
            factors.append({
                "name": "historical_failure",
                "label": "Historical Failure Rate",
                "score": fail_rate,
                "details": f"{failed}/{total} similar changes failed ({fail_rate:.0%})",
            })
        else:
            factors.append({
                "name": "historical_failure",
                "label": "Historical Data",
                "score": 0.3,
                "details": f"Only {total} similar historical changes found — limited data",
            })
        if 22 <= hour or hour <= 5:
            factors.append({
                "name": "time_of_day",
                "label": "Time of Day Risk",
                "score": 0.6,
                "details": "Change scheduled during off-hours — reduced engineer availability",
            })
        else:
            factors.append({
                "name": "time_of_day",
                "label": "Time of Day Risk",
                "score": 0.2,
                "details": "Change scheduled during business hours — full team available",
            })
        if change_type in (ChangeType.DATABASE_CHANGE.value, ChangeType.MIGRATION.value):
            factors.append({
                "name": "data_risk",
                "label": "Data Integrity Risk",
                "score": 0.7,
                "details": "Database/migration changes carry inherent data integrity risk",
            })
        metadata = change.get("metadata", {})
        if metadata.get("rollback_plan"):
            factors.append({
                "name": "rollback_plan",
                "label": "Rollback Plan",
                "score": -0.2,
                "details": "Rollback plan is documented — reduces overall risk",
            })
        if metadata.get("tested_in_staging"):
            factors.append({
                "name": "pre_testing",
                "label": "Pre-testing",
                "score": -0.15,
                "details": "Change was tested in staging — reduces risk",
            })
        return factors

    def _compute_overall_risk(self, factors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not factors:
            return {"score": 0.0, "level": RiskLevel.NEGLIGIBLE.value}
        raw_score = sum(f["score"] for f in factors) / len(factors)
        score = max(0.0, min(1.0, raw_score))
        if score >= self.high_risk_threshold:
            level = RiskLevel.HIGH.value
        elif score >= self.medium_risk_threshold:
            level = RiskLevel.MEDIUM.value
        elif score >= 0.2:
            level = RiskLevel.LOW.value
        else:
            level = RiskLevel.NEGLIGIBLE.value
        if score >= 0.9:
            level = RiskLevel.CRITICAL.value
        return {"score": round(score, 4), "level": level}

    def _generate_recommendations(self, factors: List[Dict[str, Any]],
                                    overall: Dict[str, Any],
                                    historical: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        if overall["level"] in (RiskLevel.CRITICAL.value, RiskLevel.HIGH.value):
            recommendations.append("Require senior engineer approval before proceeding")
            recommendations.append("Schedule change during lowest traffic period")
            recommendations.append("Prepare detailed rollback plan and test it")
        if overall["level"] == RiskLevel.MEDIUM.value:
            recommendations.append("Consider peer review before implementation")
            recommendations.append("Monitor closely for 30 minutes after change")
        for f in factors:
            if f["name"] == "historical_failure" and f["score"] > 0.3:
                recommendations.append("High historical failure rate for similar changes — investigate root causes first")
            if f["name"] == "data_risk" and f["score"] > 0.5:
                recommendations.append("Take database snapshot before proceeding")
                recommendations.append("Test migration on staging environment first")
        if overall["score"] <= 0.2:
            recommendations.append("Low risk change — standard procedures apply")
        recommendations.append("Document change outcome for future risk analysis improvement")
        return recommendations[:8]

    def _compute_historical_success_rate(self, historical: List[Dict[str, Any]]) -> float:
        if not historical:
            return 1.0
        successful = sum(1 for h in historical if h.get("status") in
                        (ChangeStatus.COMPLETED.value,))
        return successful / len(historical)

    def _find_similar_incidents(self, historical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        incidents = []
        for h in historical:
            if h.get("status") in (ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value):
                incidents.append({
                    "change_id": h.get("id"),
                    "title": h.get("title", "Unknown"),
                    "failure_reason": h.get("metadata", {}).get("failure_reason", "Unknown"),
                    "impact": h.get("metadata", {}).get("impact", "Unknown"),
                    "timestamp": h.get("created_at", ""),
                })
        return incidents

    def approve_change(self, change_id: str, approver: str = "system",
                        notes: str = "") -> Optional[Dict[str, Any]]:
        change = next((c for c in self.changes if c["id"] == change_id), None)
        if not change:
            return None
        change["status"] = ChangeStatus.APPROVED.value
        change["approved_by"] = approver
        change["approval_notes"] = notes
        change["updated_at"] = datetime.utcnow().isoformat()
        self._save_changes()
        return change

    def reject_change(self, change_id: str, reason: str = "") -> Optional[Dict[str, Any]]:
        change = next((c for c in self.changes if c["id"] == change_id), None)
        if not change:
            return None
        change["status"] = ChangeStatus.REJECTED.value
        change["rejection_reason"] = reason
        change["updated_at"] = datetime.utcnow().isoformat()
        self._save_changes()
        return change

    def record_outcome(self, change_id: str, status: str,
                        metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        change = next((c for c in self.changes if c["id"] == change_id), None)
        if not change:
            return None
        change["status"] = status
        change["updated_at"] = datetime.utcnow().isoformat()
        if metadata:
            change["metadata"] = {**change.get("metadata", {}), **metadata}
        self._save_changes()
        history_entry = {
            "id": str(uuid.uuid4()),
            "original_change_id": change_id,
            "title": change["title"],
            "change_type": change["change_type"],
            "target_service": change["target_service"],
            "affected_components": change["affected_components"],
            "status": status,
            "metadata": change.get("metadata", {}),
            "created_at": change["created_at"],
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self.history.append(history_entry)
        self._save_history()
        return change

    def get_change(self, change_id: str) -> Optional[Dict[str, Any]]:
        return next((c for c in self.changes if c["id"] == change_id), None)

    def list_changes(self, status: str = None, change_type: str = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        result = self.changes
        if status:
            result = [c for c in result if c.get("status") == status]
        if change_type:
            result = [c for c in result if c.get("change_type") == change_type]
        return result[-limit:]

    def get_analysis(self, change_id: str) -> Optional[Dict[str, Any]]:
        return next((a for a in self.analyses if a.get("change_id") == change_id), None)

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.history) + len([c for c in self.changes if c.get("status") in
                                        (ChangeStatus.COMPLETED.value, ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value)])
        completed = sum(1 for c in self.changes if c.get("status") == ChangeStatus.COMPLETED.value) + \
                    sum(1 for h in self.history if h.get("status") == ChangeStatus.COMPLETED.value)
        failed = sum(1 for c in self.changes if c.get("status") == ChangeStatus.FAILED.value) + \
                 sum(1 for h in self.history if h.get("status") == ChangeStatus.FAILED.value)
        rolled_back = sum(1 for c in self.changes if c.get("status") == ChangeStatus.ROLLED_BACK.value) + \
                      sum(1 for h in self.history if h.get("status") == ChangeStatus.ROLLED_BACK.value)
        return {
            "total_changes": total,
            "completed": completed,
            "failed": failed,
            "rolled_back": rolled_back,
            "success_rate": round(completed / max(1, total) * 100, 1),
            "pending_approvals": sum(1 for c in self.changes if c.get("status") == ChangeStatus.PENDING.value),
            "historical_records": len(self.history),
            "total_analyses": len(self.analyses),
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_changes(self, offset: int = 0, limit: int = 50, status: str = None,
                          change_type: str = None, target_service: str = None) -> dict:
        results = self.changes
        if status:
            results = [c for c in results if c.get("status") == status]
        if change_type:
            results = [c for c in results if c.get("change_type") == change_type]
        if target_service:
            results = [c for c in results if c.get("target_service") == target_service]
        total = len(results)
        results.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_analyses(self, offset: int = 0, limit: int = 50, risk_level: str = None) -> dict:
        results = self.analyses
        if risk_level:
            results = [a for a in results if a.get("overall_risk_level") == risk_level]
        total = len(results)
        results.sort(key=lambda a: a.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_approve_changes(self, change_ids: list[str], approver: str = "system") -> dict:
        succeeded = 0
        for cid in change_ids:
            result = self.approve_change(cid, approver)
            if result:
                succeeded += 1
        return {"approved": succeeded, "total_requested": len(change_ids)}

    def batch_reject_changes(self, change_ids: list[str], reason: str = "") -> dict:
        succeeded = 0
        for cid in change_ids:
            result = self.reject_change(cid, reason)
            if result:
                succeeded += 1
        return {"rejected": succeeded, "total_requested": len(change_ids)}

    def batch_record_outcomes(self, outcomes: list[dict]) -> dict:
        succeeded = 0
        for o in outcomes:
            try:
                result = self.record_outcome(o["change_id"], o["status"], o.get("metadata"))
                if result:
                    succeeded += 1
            except (KeyError, TypeError):
                pass
        return {"recorded": succeeded, "total_requested": len(outcomes)}

    def export_changes(self, status: str = None, change_type: str = None) -> list[dict]:
        results = self.changes
        if status:
            results = [c for c in results if c.get("status") == status]
        if change_type:
            results = [c for c in results if c.get("change_type") == change_type]
        return [{
            "id": c["id"], "title": c.get("title"), "change_type": c.get("change_type"),
            "target_service": c.get("target_service"),
            "affected_components": c.get("affected_components"),
            "status": c.get("status"), "risk_level": c.get("risk_level"),
            "scheduled_time": c.get("scheduled_time"), "created_at": c.get("created_at"),
            "metadata": {k: v for k, v in c.get("metadata", {}).items()
                         if k not in ("rollback_plan",)},
        } for c in results]

    def import_changes(self, changes: list[dict]) -> dict:
        imported = 0
        for c in changes:
            entry = {
                "id": str(uuid.uuid4()),
                "title": c.get("title", "Imported Change"),
                "description": c.get("description", ""),
                "change_type": c.get("change_type", "other"),
                "target_service": c.get("target_service", "unknown"),
                "affected_components": c.get("affected_components", []),
                "metadata": c.get("metadata", {}),
                "status": c.get("status", "pending"),
                "scheduled_time": c.get("scheduled_time", datetime.utcnow().isoformat()),
                "created_at": c.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self.changes.append(entry)
            imported += 1
        self._save_changes()
        return {"imported": imported}

    def export_analyses(self, risk_level: str = None, min_score: float = None) -> list[dict]:
        results = self.analyses
        if risk_level:
            results = [a for a in results if a.get("overall_risk_level") == risk_level]
        if min_score is not None:
            results = [a for a in results if a.get("overall_risk_score", 0) >= min_score]
        return [{
            "id": a["id"], "change_id": a.get("change_id"),
            "change_title": a.get("change_title"),
            "overall_risk_level": a.get("overall_risk_level"),
            "overall_risk_score": a.get("overall_risk_score"),
            "risk_factors": a.get("risk_factors", []),
            "recommendations": a.get("recommendations", []),
            "historical_similar_count": a.get("historical_similar_count"),
            "historical_success_rate": a.get("historical_success_rate"),
            "created_at": a.get("created_at"),
        } for a in results]

    def get_analytics(self) -> dict:
        type_counts = Counter(c.get("change_type", "unknown") for c in self.changes)
        status_counts = Counter(c.get("status", "unknown") for c in self.changes)
        risk_level_counts = Counter(a.get("overall_risk_level", "unknown") for a in self.analyses)
        type_risk_avg = defaultdict(list)
        for a in self.analyses:
            c = next((ch for ch in self.changes if ch["id"] == a.get("change_id")), None)
            if c:
                type_risk_avg[c.get("change_type", "unknown")].append(a.get("overall_risk_score", 0))
        avg_risk_by_type = {t: round(statistics.mean(scores), 4) for t, scores in type_risk_avg.items()}
        analyses_by_hour = {}
        for a in self.analyses:
            try:
                hour = datetime.fromisoformat(a["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                analyses_by_hour[hour] = analyses_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        hist_status = Counter(h.get("status", "unknown") for h in self.history)
        return {
            "total_changes": len(self.changes),
            "total_analyses": len(self.analyses),
            "historical_records": len(self.history),
            "change_type_distribution": dict(type_counts),
            "change_status_distribution": dict(status_counts),
            "risk_level_distribution": dict(risk_level_counts),
            "average_risk_by_change_type": avg_risk_by_type,
            "historical_status_distribution": dict(hist_status),
            "analyses_by_hour": dict(sorted(analyses_by_hour.items())[-24:]),
        }

    def search_changes(self, query: str) -> list[dict]:
        q = query.lower()
        return [c for c in self.changes if q in c.get("title", "").lower()
                or q in c.get("target_service", "").lower()
                or q in c.get("description", "").lower()]

    def get_service_risk_profile(self, service: str) -> dict:
        service_changes = [c for c in self.changes if c.get("target_service") == service]
        service_analyses = [a for a in self.analyses
                            if any(c["id"] == a.get("change_id") for c in service_changes)]
        risk_scores = [a.get("overall_risk_score", 0) for a in service_analyses if a.get("overall_risk_score") is not None]
        type_counts = Counter(c.get("change_type", "unknown") for c in service_changes)
        status_counts = Counter(c.get("status", "unknown") for c in service_changes)
        return {
            "service": service,
            "total_changes": len(service_changes),
            "avg_risk_score": round(statistics.mean(risk_scores), 4) if risk_scores else 0,
            "max_risk_score": round(max(risk_scores), 4) if risk_scores else 0,
            "change_type_distribution": dict(type_counts),
            "status_distribution": dict(status_counts),
            "recommendation": self._generate_service_recommendation(risk_scores, status_counts),
        }

    def _generate_service_recommendation(self, risk_scores: list[float],
                                           status_counts: Counter) -> str:
        if not risk_scores:
            return "No change history for this service"
        avg = statistics.mean(risk_scores)
        fail_count = status_counts.get(ChangeStatus.FAILED.value, 0)
        if avg > 0.7 or fail_count > 3:
            return "High risk service — require additional approvals and pre-change testing"
        elif avg > 0.4 or fail_count > 1:
            return "Moderate risk — standard review process recommended"
        return "Low risk — normal change procedures apply"

    def simulate_bulk_analysis(self, change_ids: list[str]) -> list[dict]:
        results = []
        for cid in change_ids:
            c = self.get_change(cid)
            if c:
                analysis = self.analyze(cid)
                results.append({"change_id": cid, "analysis": analysis})
        return results

    def get_change_timeline(self, change_id: str) -> list[dict]:
        timeline = []
        c = self.get_change(change_id)
        if c:
            timeline.append({"event": "planned", "timestamp": c.get("created_at")})
            if c.get("status") in (ChangeStatus.APPROVED.value,):
                timeline.append({"event": "approved", "timestamp": c.get("updated_at")})
            if c.get("status") in (ChangeStatus.REJECTED.value,):
                timeline.append({"event": "rejected", "timestamp": c.get("updated_at")})
            if c.get("status") in (ChangeStatus.COMPLETED.value,):
                timeline.append({"event": "completed", "timestamp": c.get("updated_at")})
            if c.get("status") in (ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value):
                timeline.append({"event": c.get("status"), "timestamp": c.get("updated_at")})
            a = self.get_analysis(change_id)
            if a:
                timeline.append({"event": "analysis_completed", "risk_level": a.get("overall_risk_level"),
                                 "timestamp": a.get("created_at")})
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_services(self) -> list[dict]:
        counter = Counter()
        for c in self.changes:
            svc = c.get("target_service", "unknown")
            counter[svc] += 1
            if c.get("status") in (ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value):
                counter[svc] += 5
        return [{"service": s, "score": c} for s, c in counter.most_common(20)]

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_change_slo(self, target_success_rate: float = 99.5, window_days: int = 30) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        recent = [h for h in self.history if datetime.fromisoformat(h["created_at"]) > cutoff]
        total = len(recent)
        successful = sum(1 for h in recent if h.get("status") == ChangeStatus.COMPLETED.value)
        failed = sum(1 for h in recent if h.get("status") in (ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value))
        actual_rate = round((successful / max(total, 1)) * 100, 2)
        return {
            "slo_target_pct": target_success_rate,
            "actual_success_rate_pct": actual_rate,
            "compliant": actual_rate >= target_success_rate,
            "window_days": window_days,
            "total_changes": total,
            "successful": successful,
            "failed": failed,
            "change_failure_rate": round((failed / max(total, 1)) * 100, 2),
        }

    def generate_change_report(self, days: int = 30) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_changes = [c for c in self.changes if datetime.fromisoformat(c["created_at"]) > cutoff]
        recent_analyses = [a for a in self.analyses if datetime.fromisoformat(a["created_at"]) > cutoff]
        by_type = Counter(c.get("change_type", "unknown") for c in recent_changes)
        by_status = Counter(c.get("status", "unknown") for c in recent_changes)
        by_risk = Counter(a.get("overall_risk_level", "unknown") for a in recent_analyses)
        high_risk_changes = [a for a in recent_analyses if a.get("overall_risk_level") in
                             (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)]
        return {
            "period_days": days,
            "total_changes": len(recent_changes),
            "total_analyses": len(recent_analyses),
            "change_type_distribution": dict(by_type),
            "change_status_distribution": dict(by_status),
            "risk_level_distribution": dict(by_risk),
            "high_risk_changes": len(high_risk_changes),
            "high_risk_details": [{"change_id": a.get("change_id"), "score": a.get("overall_risk_score"),
                                   "level": a.get("overall_risk_level")} for a in high_risk_changes[:10]],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "total_changes": len(self.changes),
            "total_analyses": len(self.analyses),
            "historical_records": len(self.history),
            "similarity_lookback_days": self.similarity_lookback_days,
            "high_risk_threshold": self.high_risk_threshold,
            "medium_risk_threshold": self.medium_risk_threshold,
        }

    def get_risk_trend(self, days: int = 90) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [a for a in self.analyses if datetime.fromisoformat(a["created_at"]) > cutoff]
        weekly = defaultdict(list)
        for a in recent:
            try:
                week = datetime.fromisoformat(a["created_at"]).strftime("%Y-W%W")
                weekly[week].append(a.get("overall_risk_score", 0))
            except (ValueError, TypeError):
                pass
        return [{"week": w, "avg_risk": round(statistics.mean(scores), 4), "count": len(scores)}
                for w, scores in sorted(weekly.items())]

    def get_service_summary(self, service: str) -> dict:
        service_changes = [c for c in self.changes if c.get("target_service") == service]
        service_analyses = [a for a in self.analyses
                            if any(c["id"] == a.get("change_id") for c in service_changes)]
        return {
            "service": service,
            "total_changes": len(service_changes),
            "total_analyses": len(service_analyses),
            "avg_risk_score": round(statistics.mean([a.get("overall_risk_score", 0) for a in service_analyses]), 4) if service_analyses else 0,
            "change_types": dict(Counter(c.get("change_type", "unknown") for c in service_changes)),
            "status_summary": dict(Counter(c.get("status", "unknown") for c in service_changes)),
        }

    def compare_changes(self, change_ids: list[str]) -> list[dict]:
        results = []
        for cid in change_ids:
            c = self.get_change(cid)
            a = self.get_analysis(cid)
            if c:
                results.append({
                    "change_id": cid,
                    "title": c.get("title"),
                    "type": c.get("change_type"),
                    "service": c.get("target_service"),
                    "status": c.get("status"),
                    "risk_score": a.get("overall_risk_score") if a else None,
                    "risk_level": a.get("overall_risk_level") if a else None,
                })
        return results

    def batch_analyze_pending(self) -> list[dict]:
        pending = [c for c in self.changes if c.get("status") == ChangeStatus.PENDING.value]
        results = []
        for c in pending:
            analysis = self.analyze(c["id"])
            results.append({"change_id": c["id"], "analysis": analysis})
        return results

    def get_change_volume_forecast(self, days_ahead: int = 30) -> dict:
        daily_counts = Counter()
        for c in self.changes:
            try:
                day = datetime.fromisoformat(c["created_at"]).strftime("%Y-%m-%d")
                daily_counts[day] += 1
            except (ValueError, TypeError):
                pass
        values = list(daily_counts.values())
        if len(values) < 7:
            return {"error": "Insufficient data for forecast"}
        avg = statistics.mean(values[-14:]) if len(values) >= 14 else statistics.mean(values)
        return {
            "current_daily_avg": round(avg, 1),
            "forecast_days": days_ahead,
            "predicted_total": round(avg * days_ahead),
            "confidence": "high" if len(values) >= 30 else "medium" if len(values) >= 14 else "low",
        }

    def get_change_summary(self) -> dict:
        total = len(self.changes)
        analyzed = len(self.analyses)
        pending = sum(1 for c in self.changes if c.get("status") == ChangeStatus.PENDING.value)
        high_risk = sum(1 for a in self.analyses if a.get("overall_risk_level") == "high")
        return {"total_changes": total, "analyzed": analyzed, "pending_analysis": pending, "high_risk_count": high_risk, "services_affected": len(set(c.get("target_service", "") for c in self.changes)), "avg_risk_score": round(statistics.mean([a.get("overall_risk_score", 0) for a in self.analyses]), 4) if self.analyses else 0}

    def export_changes(self) -> list[dict]:
        return [{"change_id": c["id"], "title": c.get("title"), "type": c.get("change_type"), "service": c.get("target_service"), "status": c.get("status"), "created_at": c.get("created_at")} for c in self.changes]

    def find_high_risk_changes(self, threshold: float = 0.7) -> list[dict]:
        return [{"change_id": a.get("change_id"), "score": a.get("overall_risk_score"), "level": a.get("overall_risk_level"), "factors": a.get("risk_factors", [])} for a in self.analyses if a.get("overall_risk_score", 0) >= threshold]

    def get_service_risk_ranking(self) -> list[dict]:
        service_scores: dict[str, list[float]] = defaultdict(list)
        for a in self.analyses:
            change = self.get_change(a.get("change_id", ""))
            if change:
                svc = change.get("target_service", "unknown")
                service_scores[svc].append(a.get("overall_risk_score", 0))
        return [{"service": svc, "avg_risk": round(statistics.mean(scores), 4), "change_count": len(scores)} for svc, scores in sorted(service_scores.items(), key=lambda x: statistics.mean(x[1]), reverse=True)]


class ChangeNotificationManager:
    def __init__(self, engine: ChangeRiskEngine):
        self.engine = engine
        self.notifications: list[dict] = []

    def notify_high_risk(self, change_id: str, channels: list[str] = None) -> dict:
        channels = channels or ["slack"]
        analysis = self.engine.get_analysis(change_id)
        if not analysis:
            return {"error": "Analysis not found"}
        change = self.engine.get_change(change_id)
        notification = {"id": str(uuid.uuid4()), "change_id": change_id, "title": change.get("title") if change else "Unknown", "risk_score": analysis.get("overall_risk_score"), "risk_level": analysis.get("overall_risk_level"), "channels": channels, "sent_at": datetime.utcnow().isoformat()}
        self.notifications.append(notification)
        return notification

    def list_notifications(self, limit: int = 20) -> list[dict]:
        return self.notifications[-limit:]

    def get_pending_reviews(self) -> list[dict]:
        return [{"change_id": a.get("change_id"), "score": a.get("overall_risk_score"), "level": a.get("overall_risk_level"), "title": (self.engine.get_change(a.get("change_id", "")) or {}).get("title", "")} for a in self.engine.analyses if a.get("overall_risk_level") in ("high", "critical")]


class ChangeDashboardAggregator:
    def __init__(self, engine: ChangeRiskEngine):
        self.engine = engine

    def get_overview(self) -> dict:
        summary = self.engine.get_change_summary()
        pending_reviews = [a for a in self.engine.analyses if a.get("overall_risk_level") in ("high", "critical")]
        return {"summary": summary, "pending_reviews": len(pending_reviews), "recent_changes": self.engine.get_change_volume_forecast(7), "top_services": self.engine.get_service_risk_ranking()[:5]}

    def get_risk_distribution(self) -> dict:
        levels = Counter(a.get("overall_risk_level", "unknown") for a in self.engine.analyses)
        return dict(levels)

    def get_recent_high_risk_activities(self, days: int = 7) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [a for a in self.engine.analyses if a.get("overall_risk_level") in ("high", "critical") and datetime.fromisoformat(a["created_at"]) > cutoff]
        return [{"change_id": a.get("change_id"), "score": a.get("overall_risk_score"), "level": a.get("overall_risk_level"), "created_at": a.get("created_at")} for a in recent]

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
        return {"total_events": 0, "anomalies_detected": 0, "false_positives": 0, "avg_confidence": 0.0}

    def validate_model(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "model_version": "v1"}

class AiopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    prediction_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AiopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    model: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    anomalies_found: int = Field(default=0)

    def record_result(self, is_anomaly: bool) -> None:
        self.processed += 1
        if is_anomaly:
            self.anomalies_found += 1

    def complete(self) -> None:
        self.status = "completed"

class AnomalyScore(BaseModel):
    entity_id: str
    score: float = Field(default=0.0, ge=0, le=1)
    baseline: float = Field(default=0.0)
    deviation: float = Field(default=0.0)
    features: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: str = Field(default="info")

    def is_anomalous(self, threshold: float = 0.7) -> bool:
        return self.score >= threshold

class ModelMetrics(BaseModel):
    model_name: str
    version: str = Field(default="v1")
    accuracy: float = Field(default=0.0, ge=0, le=1)
    precision: float = Field(default=0.0, ge=0, le=1)
    recall: float = Field(default=0.0, ge=0, le=1)
    f1_score: float = Field(default=0.0, ge=0, le=1)
    training_date: Optional[datetime] = None
    total_predictions: int = Field(default=0)

class ModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, ModelMetrics] = {}

    def register(self, name: str, version: str = "v1") -> ModelMetrics:
        mm = ModelMetrics(model_name=name, version=version)
        self._models[name] = mm
        return mm

    def update_metrics(self, name: str, accuracy: float = 0.0, precision: float = 0.0,
                       recall: float = 0.0, f1: float = 0.0) -> None:
        model = self._models.get(name)
        if model:
            model.accuracy = accuracy
            model.precision = precision
            model.recall = recall
            model.f1_score = f1
            model.total_predictions += 1

    def get_best(self) -> Optional[ModelMetrics]:
        if not self._models:
            return None
        return max(self._models.values(), key=lambda m: m.f1_score)

    def summary(self) -> Dict[str, Any]:
        return {name: m.dict() for name, m in self._models.items()}

class FeatureStore(BaseModel):
    feature_name: str
    value: float
    entity_type: str = Field(default="generic")
    entity_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="inference")

class FeatureRepository:
    def __init__(self) -> None:
        self._features: List[FeatureStore] = []

    def store(self, feature: FeatureStore) -> None:
        self._features.append(feature)

    def get_latest(self, entity_id: str, feature_name: str) -> Optional[FeatureStore]:
        matches = [f for f in self._features if f.entity_id == entity_id and f.feature_name == feature_name]
        return max(matches, key=lambda f: f.timestamp) if matches else None

    def get_entity_features(self, entity_id: str) -> Dict[str, Any]:
        features = [f for f in self._features if f.entity_id == entity_id]
        return {f.feature_name: {"value": f.value, "timestamp": f.timestamp.isoformat()} for f in features}

    def get_time_series(self, feature_name: str, entity_id: str, limit: int = 100) -> List[FeatureStore]:
        matches = [f for f in self._features if f.feature_name == feature_name and f.entity_id == entity_id]
        return sorted(matches, key=lambda f: f.timestamp, reverse=True)[:limit]

class ThresholdConfig(BaseModel):
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    enabled: bool = True
    cooldown_minutes: int = Field(default=5)

class ThresholdManager:
    def __init__(self) -> None:
        self._thresholds: Dict[str, ThresholdConfig] = {}

    def define(self, config: ThresholdConfig) -> None:
        self._thresholds[config.metric_name] = config

    def check(self, metric_name: str, value: float) -> Dict[str, Any]:
        config = self._thresholds.get(metric_name)
        if not config or not config.enabled:
            return {"level": "ok", "message": "No threshold configured"}
        if value >= config.critical_threshold:
            return {"level": "critical", "value": value, "threshold": config.critical_threshold}
        if value >= config.warning_threshold:
            return {"level": "warning", "value": value, "threshold": config.warning_threshold}
        return {"level": "ok", "value": value}

    def get_all(self) -> Dict[str, ThresholdConfig]:
        return dict(self._thresholds)

class DriftMetric(BaseModel):
    feature_name: str
    training_mean: float
    production_mean: float
    drift_score: float = Field(default=0.0, ge=0)
    drifted: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class DriftDetector:
    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        self._metrics: List[DriftMetric] = []

    def compare(self, feature_name: str, training_mean: float, production_values: List[float]) -> DriftMetric:
        prod_mean = sum(production_values) / max(len(production_values), 1)
        drift = abs(prod_mean - training_mean) / max(abs(training_mean), 0.001)
        metric = DriftMetric(feature_name=feature_name, training_mean=training_mean,
                              production_mean=round(prod_mean, 4),
                              drift_score=round(drift, 4), drifted=drift > self.threshold)
        self._metrics.append(metric)
        return metric

    def get_recent_drifts(self) -> List[DriftMetric]:
        return [m for m in self._metrics if m.drifted]

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._metrics)
        drifted = len(self.get_recent_drifts())
        return {"total_features": total, "drifted": drifted, "stable": total - drifted,
                "drift_rate": round(drifted / max(total, 1) * 100, 1)}

class PredictionLog(BaseModel):
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    input_features: Dict[str, float] = Field(default_factory=dict)
    prediction: Any = None
    confidence: float = Field(default=0.0)
    actual: Optional[Any] = None
    correct: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float = Field(default=0.0)

class PredictionLogger:
    def __init__(self) -> None:
        self._logs: List[PredictionLog] = []

    def log_prediction(self, model_name: str, features: Dict[str, float], prediction: Any,
                       confidence: float, latency_ms: float = 0.0) -> PredictionLog:
        pl = PredictionLog(model_name=model_name, input_features=features,
                            prediction=prediction, confidence=confidence, latency_ms=latency_ms)
        self._logs.append(pl)
        return pl

    def record_actual(self, prediction_id: str, actual: Any) -> bool:
        for pl in self._logs:
            if pl.prediction_id == prediction_id:
                pl.actual = actual
                pl.correct = pl.prediction == actual
                return True
        return False

    def get_accuracy(self, model_name: Optional[str] = None) -> float:
        logs = [l for l in self._logs if l.correct is not None]
        if model_name:
            logs = [l for l in logs if l.model_name == model_name]
        if not logs:
            return 0.0
        return round(sum(1 for l in logs if l.correct) / len(logs), 4)
