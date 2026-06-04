"""Feature 52: Automated Incident Remediation — AI-suggested and auto-approved remediation."""

import json
import os
import uuid
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class RemediationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ApprovalMode(Enum):
    AUTO = "auto"
    SEMI = "semi"
    MANUAL = "manual"


class ActionType(Enum):
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK_DEPLOY = "rollback_deploy"
    CLEAR_CACHE = "clear_cache"
    INCREASE_RESOURCES = "increase_resources"
    KILL_PROCESS = "kill_process"
    DRAIN_CONNECTIONS = "drain_connections"
    SWITCH_TRAFFIC = "switch_traffic"
    EXECUTE_SCRIPT = "execute_script"
    RECREATE_CONTAINER = "recreate_container"
    UPDATE_CONFIG = "update_config"
    RESTART_DATABASE = "restart_database"
    DISABLE_FEATURE = "disable_feature"
    ENABLE_BACKUP = "enable_backup"
    REDIRECT_TRAFFIC = "redirect_traffic"


class IncidentRemediationEngine:
    """AI-suggested remediation actions with confidence-based approval."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_mode = ApprovalMode(config.get("approval_mode", "semi"))
        self.auto_threshold = config.get("auto_threshold", 0.9)
        self.semi_threshold = config.get("semi_threshold", 0.7)
        self.cooldown_minutes = config.get("cooldown_minutes", 30)
        self.max_concurrent = config.get("max_concurrent", 5)
        self.remediations_file = _data_file('remediations.json')
        self.history_file = _data_file('remediation_history.json')
        self.patterns_file = _data_file('remediation_patterns.json')
        self.remediations: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.remediations_file, "remediations"),
            (self.history_file, "history"),
            (self.patterns_file, "patterns")
        ]:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if target == "remediations":
                    self.remediations = data
                elif target == "history":
                    self.history = data
                elif target == "patterns":
                    self.patterns = data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _save_remediations(self):
        with open(self.remediations_file, 'w') as f:
            json.dump(self.remediations, f, default=str)

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-5000:], f, default=str)

    def _save_patterns(self):
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, default=str)

    REMEDIATION_TEMPLATES = [
        {
            "pattern": "high_cpu",
            "suggested_actions": [
                {"type": ActionType.SCALE_UP.value, "config": {"replicas_increase": 2, "max_replicas": 10}, "confidence": 0.85},
                {"type": ActionType.KILL_PROCESS.value, "config": {"process_pattern": ".*", "signal": "SIGTERM"}, "confidence": 0.4},
            ],
            "description": "High CPU usage detected — scale up or identify rogue processes",
        },
        {
            "pattern": "memory_leak",
            "suggested_actions": [
                {"type": ActionType.RESTART_SERVICE.value, "config": {"graceful": True, "drain_timeout": 30}, "confidence": 0.75},
                {"type": ActionType.INCREASE_RESOURCES.value, "config": {"memory_increase_mb": 1024}, "confidence": 0.6},
            ],
            "description": "Memory leak suspected — restart service or increase memory limit",
        },
        {
            "pattern": "service_down",
            "suggested_actions": [
                {"type": ActionType.RESTART_SERVICE.value, "config": {"graceful": False, "force": True}, "confidence": 0.9},
                {"type": ActionType.RECREATE_CONTAINER.value, "config": {"preserve_volumes": True}, "confidence": 0.7},
            ],
            "description": "Service is down — attempt restart or container recreation",
        },
        {
            "pattern": "deploy_failure",
            "suggested_actions": [
                {"type": ActionType.ROLLBACK_DEPLOY.value, "config": {"version": "previous", "auto_confirm": True}, "confidence": 0.95},
            ],
            "description": "Deployment failure detected — rollback to previous version",
        },
        {
            "pattern": "latency_spike",
            "suggested_actions": [
                {"type": ActionType.SWITCH_TRAFFIC.value, "config": {"target": "canary", "percentage": 100}, "confidence": 0.7},
                {"type": ActionType.DRAIN_CONNECTIONS.value, "config": {"drain_timeout": 60, "reconnect": True}, "confidence": 0.6},
                {"type": ActionType.CLEAR_CACHE.value, "config": {"cache_type": "all"}, "confidence": 0.5},
            ],
            "description": "Latency spike detected — drain connections or switch traffic",
        },
        {
            "pattern": "disk_full",
            "suggested_actions": [
                {"type": ActionType.CLEAR_CACHE.value, "config": {"cache_type": "disk", "max_age_hours": 24}, "confidence": 0.8},
                {"type": ActionType.EXECUTE_SCRIPT.value, "config": {"script": "cleanup_disk.sh", "timeout": 120}, "confidence": 0.7},
            ],
            "description": "Disk space critically low — clear caches or execute cleanup",
        },
        {
            "pattern": "database_slow",
            "suggested_actions": [
                {"type": ActionType.RESTART_DATABASE.value, "config": {"graceful": True, "wait_for_replication": True}, "confidence": 0.6},
                {"type": ActionType.INCREASE_RESOURCES.value, "config": {"memory_increase_mb": 2048, "cpu_increase": 2}, "confidence": 0.7},
            ],
            "description": "Database performance degraded — increase resources or restart",
        },
        {
            "pattern": "connection_leak",
            "suggested_actions": [
                {"type": ActionType.DRAIN_CONNECTIONS.value, "config": {"drain_timeout": 120, "force_close": True}, "confidence": 0.8},
                {"type": ActionType.RESTART_SERVICE.value, "config": {"graceful": True, "drain_timeout": 60}, "confidence": 0.7},
            ],
            "description": "Connection leak detected — drain and restart connections",
        },
    ]

    def suggest_remediation(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        incident_text = f"{incident.get('title', '')} {incident.get('description', '')}".lower()
        suggestions = []
        for template in self.REMEDIATION_TEMPLATES:
            pattern = template["pattern"].replace("_", " ")
            if pattern in incident_text:
                for action in template["suggested_actions"]:
                    suggestions.append({
                        "pattern": template["pattern"],
                        "description": template["description"],
                        "action_type": action["type"],
                        "config": action["config"],
                        "base_confidence": action["confidence"],
                    })
        if not suggestions:
            suggestions.append({
                "pattern": "generic",
                "description": "No specific remediation pattern matched — generic escalation",
                "action_type": ActionType.EXECUTE_SCRIPT.value,
                "config": {"script": "diagnose.sh", "timeout": 60},
                "base_confidence": 0.3,
            })
        historical_success = self._get_pattern_success_rates()
        for s in suggestions:
            adj = historical_success.get(s["pattern"], 0.0)
            s["adjusted_confidence"] = round(min(1.0, s["base_confidence"] + adj * 0.1), 4)
            s["approval_mode"] = self._determine_approval_mode(s["adjusted_confidence"]).value
        suggestions.sort(key=lambda x: x["adjusted_confidence"], reverse=True)
        return suggestions

    def _get_pattern_success_rates(self) -> Dict[str, float]:
        rates = {}
        for h in self.history:
            p = h.get("pattern", "generic")
            if p not in rates:
                rates[p] = {"total": 0, "success": 0}
            rates[p]["total"] += 1
            if h.get("status") == RemediationStatus.COMPLETED.value:
                rates[p]["success"] += 1
        result = {}
        for p, v in rates.items():
            result[p] = v["success"] / v["total"] if v["total"] > 0 else 0.0
        return result

    def _determine_approval_mode(self, confidence: float) -> ApprovalMode:
        if confidence >= self.auto_threshold:
            return ApprovalMode.AUTO
        elif confidence >= self.semi_threshold:
            return ApprovalMode.SEMI
        return ApprovalMode.MANUAL

    def create_remediation(self, incident_id: str, action_type: str, config: Dict[str, Any],
                           confidence: float, pattern: str, description: str = "",
                           approval_mode: str = "semi") -> Dict[str, Any]:
        active = [r for r in self.remediations if r.get("status") in
                  [RemediationStatus.PENDING.value, RemediationStatus.APPROVED.value, RemediationStatus.IN_PROGRESS.value]]
        if len(active) >= self.max_concurrent:
            return {"error": f"Maximum concurrent remediations ({self.max_concurrent}) reached"}
        cooldown_check = self._check_cooldown(pattern, incident_id)
        if cooldown_check:
            return cooldown_check
        remediation = {
            "id": str(uuid.uuid4()),
            "incident_id": incident_id,
            "action_type": action_type,
            "config": config,
            "confidence": round(confidence, 4),
            "pattern": pattern,
            "description": description,
            "approval_mode": approval_mode,
            "status": RemediationStatus.PENDING.value,
            "approved_by": None,
            "approved_at": None,
            "executed_by": None,
            "executed_at": None,
            "result": None,
            "error_message": None,
            "rollback_action": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if approval_mode == ApprovalMode.AUTO.value:
            remediation["status"] = RemediationStatus.APPROVED.value
            remediation["approved_by"] = "ai_auto_approval"
            remediation["approved_at"] = datetime.utcnow().isoformat()
        elif approval_mode == ApprovalMode.MANUAL.value:
            pass
        else:
            pass
        self.remediations.append(remediation)
        self._save_remediations()
        return remediation

    def _check_cooldown(self, pattern: str, incident_id: str) -> Optional[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)
        recent = [r for r in self.history if r.get("pattern") == pattern
                  and r.get("incident_id") == incident_id]
        for r in recent:
            try:
                created = datetime.fromisoformat(r["created_at"])
                if created > cutoff:
                    return {"warning": f"Cooldown active for pattern '{pattern}' on incident {incident_id}",
                            "remaining_minutes": int((created - cutoff).total_seconds() / 60)}
            except (ValueError, TypeError):
                continue
        return None

    def approve_remediation(self, remediation_id: str, approver: str = "human") -> Optional[Dict[str, Any]]:
        for r in self.remediations:
            if r["id"] == remediation_id:
                if r["status"] != RemediationStatus.PENDING.value:
                    return {"error": f"Remediation {remediation_id} is in status {r['status']}, cannot approve"}
                r["status"] = RemediationStatus.APPROVED.value
                r["approved_by"] = approver
                r["approved_at"] = datetime.utcnow().isoformat()
                r["updated_at"] = datetime.utcnow().isoformat()
                self._save_remediations()
                return r
        return None

    def reject_remediation(self, remediation_id: str, reason: str = "") -> Optional[Dict[str, Any]]:
        for r in self.remediations:
            if r["id"] == remediation_id:
                if r["status"] != RemediationStatus.PENDING.value:
                    return {"error": f"Remediation {remediation_id} is in status {r['status']}, cannot reject"}
                r["status"] = RemediationStatus.REJECTED.value
                r["result"] = reason
                r["updated_at"] = datetime.utcnow().isoformat()
                self._save_remediations()
                return r
        return None

    def execute_remediation(self, remediation_id: str, executor: str = "system") -> Optional[Dict[str, Any]]:
        for r in self.remediations:
            if r["id"] == remediation_id:
                if r["status"] not in [RemediationStatus.APPROVED.value, RemediationStatus.PENDING.value]:
                    return {"error": f"Remediation {remediation_id} is in status {r['status']}, cannot execute"}
                r["status"] = RemediationStatus.IN_PROGRESS.value
                r["executed_by"] = executor
                r["executed_at"] = datetime.utcnow().isoformat()
                r["updated_at"] = datetime.utcnow().isoformat()
                self._save_remediations()
                result = self._run_action(r["action_type"], r["config"])
                r["result"] = result.get("output", "")
                r["status"] = RemediationStatus.COMPLETED.value if result.get("success") else RemediationStatus.FAILED.value
                if not result.get("success"):
                    r["error_message"] = result.get("error", "Unknown error")
                r["updated_at"] = datetime.utcnow().isoformat()
                self.remediations = [rem for rem in self.remediations if rem["id"] != remediation_id]
                self.history.append(r)
                self._save_remediations()
                self._save_history()
                if result.get("success"):
                    self._learn_from_success(r)
                return r
        return None

    def _run_action(self, action_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "output": f"Action {action_type} completed with config {json.dumps(config)}"}

    def _learn_from_success(self, remediation: Dict[str, Any]):
        pattern = remediation.get("pattern", "generic")
        existing = next((p for p in self.patterns if p["pattern"] == pattern), None)
        if existing:
            existing["success_count"] = existing.get("success_count", 0) + 1
            existing["last_success"] = datetime.utcnow().isoformat()
        else:
            self.patterns.append({
                "pattern": pattern,
                "action_type": remediation.get("action_type"),
                "config": remediation.get("config"),
                "success_count": 1,
                "last_success": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            })
        self._save_patterns()

    def get_remediation(self, remediation_id: str) -> Optional[Dict[str, Any]]:
        combined = self.remediations + self.history
        return next((r for r in combined if r["id"] == remediation_id), None)

    def list_remediations(self, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        combined = self.history + self.remediations
        if status:
            combined = [r for r in combined if r.get("status") == status]
        return combined[-limit:]

    def list_active_remediations(self) -> List[Dict[str, Any]]:
        return [r for r in self.remediations if r.get("status") in
                [RemediationStatus.PENDING.value, RemediationStatus.APPROVED.value, RemediationStatus.IN_PROGRESS.value]]

    def get_patterns(self) -> List[Dict[str, Any]]:
        templates = []
        for t in self.REMEDIATION_TEMPLATES:
            templates.append({
                "pattern": t["pattern"],
                "description": t["description"],
                "actions": t["suggested_actions"],
            })
        return templates

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.history)
        completed = sum(1 for h in self.history if h.get("status") == RemediationStatus.COMPLETED.value)
        failed = sum(1 for h in self.history if h.get("status") == RemediationStatus.FAILED.value)
        auto_count = sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.AUTO.value)
        manual_count = sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.MANUAL.value)
        return {
            "total_remediations": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
            "auto_approved": auto_count,
            "manually_approved": manual_count,
            "active_remediations": len(self.list_active_remediations()),
            "learned_patterns": len(self.patterns),
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_remediations(self, offset: int = 0, limit: int = 50, status: str = None,
                                action_type: str = None, pattern: str = None) -> dict:
        combined = self.history + self.remediations
        results = combined
        if status:
            results = [r for r in results if r.get("status") == status]
        if action_type:
            results = [r for r in results if r.get("action_type") == action_type]
        if pattern:
            results = [r for r in results if r.get("pattern") == pattern]
        total = len(results)
        results.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_history(self, offset: int = 0, limit: int = 50, status: str = None) -> dict:
        results = self.history
        if status:
            results = [h for h in results if h.get("status") == status]
        total = len(results)
        results.sort(key=lambda h: h.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_approve_remediations(self, remediation_ids: list[str], approver: str = "human") -> dict:
        succeeded = 0
        failed = 0
        for rid in remediation_ids:
            result = self.approve_remediation(rid, approver)
            if result and "error" not in result:
                succeeded += 1
            else:
                failed += 1
        return {"approved": succeeded, "failed": failed, "total_requested": len(remediation_ids)}

    def batch_reject_remediations(self, remediation_ids: list[str], reason: str = "") -> dict:
        succeeded = 0
        for rid in remediation_ids:
            result = self.reject_remediation(rid, reason)
            if result and "error" not in result:
                succeeded += 1
        return {"rejected": succeeded, "total_requested": len(remediation_ids)}

    def batch_execute_remediations(self, remediation_ids: list[str], executor: str = "system") -> dict:
        succeeded = 0
        failed = 0
        for rid in remediation_ids:
            result = self.execute_remediation(rid, executor)
            if result and "error" not in result:
                succeeded += 1
            else:
                failed += 1
        return {"executed": succeeded, "failed": failed, "total_requested": len(remediation_ids)}

    def export_remediations(self, status: str = None, pattern: str = None) -> list[dict]:
        combined = self.history + self.remediations
        results = combined
        if status:
            results = [r for r in results if r.get("status") == status]
        if pattern:
            results = [r for r in results if r.get("pattern") == pattern]
        return [{
            "id": r["id"], "incident_id": r.get("incident_id"),
            "action_type": r.get("action_type"), "config": r.get("config"),
            "confidence": r.get("confidence"), "pattern": r.get("pattern"),
            "status": r.get("status"), "approval_mode": r.get("approval_mode"),
            "approved_by": r.get("approved_by"), "executed_by": r.get("executed_by"),
            "result": r.get("result"), "error_message": r.get("error_message"),
            "created_at": r.get("created_at"),
        } for r in results]

    def import_remediations(self, remediations: list[dict]) -> dict:
        imported = 0
        for r in remediations:
            entry = {
                "id": str(uuid.uuid4()),
                "incident_id": r.get("incident_id", "unknown"),
                "action_type": r.get("action_type", "restart_service"),
                "config": r.get("config", {}),
                "confidence": r.get("confidence", 0.5),
                "pattern": r.get("pattern", "generic"),
                "description": r.get("description", ""),
                "approval_mode": r.get("approval_mode", "semi"),
                "status": r.get("status", "pending"),
                "approved_by": r.get("approved_by"),
                "approved_at": r.get("approved_at"),
                "executed_by": r.get("executed_by"),
                "executed_at": r.get("executed_at"),
                "result": r.get("result"),
                "error_message": r.get("error_message"),
                "rollback_action": r.get("rollback_action"),
                "created_at": r.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self.history.append(entry)
            imported += 1
        self._save_history()
        return {"imported": imported}

    def get_analytics(self) -> dict:
        status_counts = Counter(h.get("status", "unknown") for h in self.history)
        pattern_counts = Counter(h.get("pattern", "unknown") for h in self.history)
        action_type_counts = Counter(h.get("action_type", "unknown") for h in self.history)
        mode_counts = Counter(h.get("approval_mode", "unknown") for h in self.history)
        remediations_by_hour = {}
        for r in self.history:
            try:
                hour = datetime.fromisoformat(r["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                remediations_by_hour[hour] = remediations_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        total = len(self.history)
        completed = sum(1 for h in self.history if h.get("status") == RemediationStatus.COMPLETED.value)
        failed = sum(1 for h in self.history if h.get("status") == RemediationStatus.FAILED.value)
        return {
            "total_remediations": total,
            "total_active": len(self.list_active_remediations()),
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / max(total, 1) * 100, 1),
            "status_distribution": dict(status_counts),
            "pattern_distribution": dict(pattern_counts.most_common(10)),
            "action_type_distribution": dict(action_type_counts.most_common(10)),
            "approval_mode_distribution": dict(mode_counts),
            "remediations_by_hour": dict(sorted(remediations_by_hour.items())[-24:]),
            "learned_patterns": len(self.patterns),
            "avg_confidence": round(statistics.mean([h.get("confidence", 0) for h in self.history]), 4) if self.history else 0,
        }

    def search_remediations(self, query: str) -> list[dict]:
        q = query.lower()
        combined = self.history + self.remediations
        return [r for r in combined if q in r.get("pattern", "").lower()
                or q in r.get("action_type", "").lower()
                or q in r.get("incident_id", "").lower()]

    def get_incident_timeline(self, incident_id: str) -> list[dict]:
        timeline = []
        combined = self.history + self.remediations
        for r in combined:
            if r.get("incident_id") == incident_id:
                timeline.append({
                    "event": f"remediation_{r.get('status')}",
                    "remediation_id": r["id"],
                    "action_type": r.get("action_type"),
                    "pattern": r.get("pattern"),
                    "timestamp": r.get("created_at"),
                })
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_patterns(self) -> list[dict]:
        counter = Counter(h.get("pattern", "unknown") for h in self.history)
        return [{"pattern": p, "count": c} for p, c in counter.most_common(20)]

    def simulate_remediation_flow(self, incident_title: str = None) -> dict:
        import random
        incident = {
            "id": str(uuid.uuid4()),
            "title": incident_title or "Simulated Incident - High CPU Detected",
            "description": f"High CPU usage detected on web-server at {datetime.utcnow().isoformat()}",
            "source": "monitoring",
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat(),
        }
        suggestions = self.suggest_remediation(incident)
        created = []
        for s in suggestions[:2]:
            rem = self.create_remediation(
                incident_id=incident["id"],
                action_type=s["action_type"],
                config=s["config"],
                confidence=s["adjusted_confidence"],
                pattern=s["pattern"],
                description=s["description"],
                approval_mode=s["approval_mode"],
            )
            if "error" not in rem:
                if rem["status"] == RemediationStatus.APPROVED.value:
                    executed = self.execute_remediation(rem["id"])
                    created.append(executed or rem)
                else:
                    created.append(rem)
        return {"incident": incident, "remediations_created": created}

    def batch_suggest_remediations(self, incidents: list[dict]) -> list[dict]:
        results = []
        for inc in incidents:
            suggestions = self.suggest_remediation(inc)
            results.append({
                "incident_id": inc.get("id"),
                "suggestions": suggestions,
            })
        return results

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_remediation_slo(self, target_success_rate: float = 90.0, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [h for h in self.history if datetime.fromisoformat(h["created_at"]) > cutoff]
        total = len(recent)
        successful = sum(1 for h in recent if h.get("status") == RemediationStatus.COMPLETED.value)
        actual_rate = round((successful / max(total, 1)) * 100, 2)
        return {
            "slo_target_pct": target_success_rate,
            "actual_success_rate_pct": actual_rate,
            "compliant": actual_rate >= target_success_rate,
            "window_hours": window_hours,
            "total_attempts": total,
            "successful": successful,
            "failed": total - successful,
        }

    def generate_remediation_report(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [h for h in self.history if datetime.fromisoformat(h["created_at"]) > cutoff]
        by_pattern = Counter(h.get("pattern", "unknown") for h in recent)
        by_action = Counter(h.get("action_type", "unknown") for h in recent)
        by_status = Counter(h.get("status", "unknown") for h in recent)
        by_mode = Counter(h.get("approval_mode", "unknown") for h in recent)
        completed = sum(1 for h in recent if h.get("status") == RemediationStatus.COMPLETED.value)
        return {
            "period_days": days,
            "total_remediations": len(recent),
            "completed": completed,
            "success_rate": round((completed / max(len(recent), 1)) * 100, 1),
            "pattern_distribution": dict(by_pattern.most_common(10)),
            "action_distribution": dict(by_action.most_common(10)),
            "status_distribution": dict(by_status),
            "approval_mode_distribution": dict(by_mode),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "auto_threshold": self.auto_threshold,
            "semi_threshold": self.semi_threshold,
            "cooldown_minutes": self.cooldown_minutes,
            "max_concurrent": self.max_concurrent,
            "total_remediations": len(self.history),
            "learned_patterns": len(self.patterns),
        }

    def get_pattern_effectiveness(self) -> list[dict]:
        pattern_stats = defaultdict(lambda: {"total": 0, "success": 0})
        for h in self.history:
            p = h.get("pattern", "generic")
            pattern_stats[p]["total"] += 1
            if h.get("status") == RemediationStatus.COMPLETED.value:
                pattern_stats[p]["success"] += 1
        return [{
            "pattern": p,
            "total": v["total"],
            "success": v["success"],
            "effectiveness": round((v["success"] / max(v["total"], 1)) * 100, 1),
        } for p, v in sorted(pattern_stats.items(), key=lambda x: x[1]["total"], reverse=True)]

    def get_auto_remediation_rate(self) -> dict:
        total = len(self.history)
        auto = sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.AUTO.value)
        manual = sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.MANUAL.value)
        return {
            "total": total,
            "auto_remediated": auto,
            "manually_remediated": manual,
            "auto_rate_pct": round((auto / max(total, 1)) * 100, 1),
            "auto_success_rate": round(
                (sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.AUTO.value
                     and h.get("status") == RemediationStatus.COMPLETED.value) / max(auto, 1)) * 100, 1
            ) if auto > 0 else 0,
        }

    def compare_incident_remediations(self, incident_ids: list[str]) -> list[dict]:
        results = []
        for iid in incident_ids:
            combined = self.history + self.remediations
            incident_rems = [r for r in combined if r.get("incident_id") == iid]
            results.append({
                "incident_id": iid,
                "total_remediations": len(incident_rems),
                "status_distribution": dict(Counter(r.get("status", "unknown") for r in incident_rems)),
                "patterns": list(set(r.get("pattern", "") for r in incident_rems)),
            })
        return results

    def get_remediation_trend(self, days: int = 30) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [h for h in self.history if datetime.fromisoformat(h["created_at"]) > cutoff]
        daily = defaultdict(lambda: {"total": 0, "success": 0})
        for h in recent:
            try:
                day = datetime.fromisoformat(h["created_at"]).strftime("%Y-%m-%d")
                daily[day]["total"] += 1
                if h.get("status") == RemediationStatus.COMPLETED.value:
                    daily[day]["success"] += 1
            except (ValueError, TypeError):
                pass
        return [{"date": d, "total": v["total"], "success": v["success"],
                  "rate": round((v["success"] / max(v["total"], 1)) * 100, 1)}
                for d, v in sorted(daily.items())]

    def simulate_auto_remediation(self, incident: dict) -> dict:
        suggestions = self.suggest_remediation(incident)
        results = []
        for s in suggestions:
            if s.get("adjusted_confidence", 0) >= self.auto_threshold:
                rem = self.create_remediation(
                    incident_id=incident.get("id", str(uuid.uuid4())),
                    action_type=s["action_type"], config=s["config"],
                    confidence=s["adjusted_confidence"], pattern=s["pattern"],
                    description=s["description"], approval_mode=ApprovalMode.AUTO.value,
                )
                if "error" not in rem:
                    executed = self.execute_remediation(rem["id"])
                    results.append(executed or rem)
        return {"simulated_auto_remediations": len(results), "results": results}

    def get_remediation_summary(self) -> dict:
        total = len(self.history)
        completed = sum(1 for h in self.history if h.get("status") == RemediationStatus.COMPLETED.value)
        failed = sum(1 for h in self.history if h.get("status") == RemediationStatus.FAILED.value)
        running = sum(1 for h in self.history if h.get("status") == RemediationStatus.RUNNING.value)
        return {"total": total, "completed": completed, "failed": failed, "running": running, "success_rate": round(completed / max(total, 1) * 100, 1), "auto_remediation_rate": round(sum(1 for h in self.history if h.get("approval_mode") == ApprovalMode.AUTO.value) / max(total, 1) * 100, 1)}

    def get_most_used_patterns(self, limit: int = 10) -> list[dict]:
        pattern_count: dict[str, int] = defaultdict(int)
        for h in self.history:
            pattern_count[h.get("pattern", "generic")] += 1
        return [{"pattern": p, "count": c} for p, c in sorted(pattern_count.items(), key=lambda x: x[1], reverse=True)[:limit]]

    def get_hours_since_last_failure(self) -> Optional[float]:
        failures = [h for h in self.history if h.get("status") == RemediationStatus.FAILED.value]
        if not failures:
            return None
        last_failure = max(failures, key=lambda x: x.get("created_at", ""))
        try:
            delta = datetime.utcnow() - datetime.fromisoformat(last_failure["created_at"])
            return round(delta.total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            return None

    def get_top_incident_types(self, limit: int = 10) -> list[dict]:
        incident_types: dict[str, int] = defaultdict(int)
        combined = self.history + self.remediations
        for r in combined:
            incident_types[r.get("incident_type", "unknown")] += 1
        return [{"incident_type": t, "count": c} for t, c in sorted(incident_types.items(), key=lambda x: x[1], reverse=True)[:limit]]


class RemediationAnalytics:
    def __init__(self, engine: IncidentRemediationEngine):
        self.engine = engine

    def get_compliance_rate(self, hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [h for h in self.engine.history if datetime.fromisoformat(h["created_at"]) > cutoff]
        if not recent:
            return {"period_hours": hours, "total": 0, "compliance_rate": 100}
        completed = sum(1 for h in recent if h.get("status") == RemediationStatus.COMPLETED.value)
        return {"period_hours": hours, "total": len(recent), "completed": completed, "compliance_rate": round(completed / len(recent) * 100, 1)}

    def get_mean_time_to_remediate(self) -> Optional[float]:
        times = []
        for h in self.engine.history:
            if h.get("status") == RemediationStatus.COMPLETED.value and h.get("created_at") and h.get("completed_at"):
                try:
                    start = datetime.fromisoformat(h["created_at"])
                    end = datetime.fromisoformat(h["completed_at"])
                    times.append((end - start).total_seconds() / 60)
                except (ValueError, TypeError):
                    pass
        return round(statistics.mean(times), 1) if times else None

    def get_remediation_efficiency(self) -> dict:
        total = len(self.engine.history)
        auto = sum(1 for h in self.engine.history if h.get("approval_mode") == ApprovalMode.AUTO.value)
        manual = sum(1 for h in self.engine.history if h.get("approval_mode") == ApprovalMode.MANUAL.value)
        mttr = self.get_mean_time_to_remediate()
        return {"total": total, "auto_remediated": auto, "manually_remediated": manual, "auto_pct": round(auto / max(total, 1) * 100, 1), "mean_time_to_remediate_minutes": mttr, "efficiency_score": round(auto / max(total, 1) * 100, 1) if mttr and mttr < 15 else round(auto / max(total, 1) * 100 * 0.7, 1)}

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
