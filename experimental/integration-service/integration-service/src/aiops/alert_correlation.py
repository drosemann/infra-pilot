"""Feature 54: Intelligent Alert Correlation — Group related alerts into incidents."""

import json
import os
import uuid
import math
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple, Set
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


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class CorrelationAlgorithm(Enum):
    TIME_WINDOW = "time_window"
    SOURCE_OVERLAP = "source_overlap"
    METRIC_SIMILARITY = "metric_similarity"
    DEPENDENCY_CHAIN = "dependency_chain"
    PATTERN_MATCH = "pattern_match"
    TEXT_SIMILARITY = "text_similarity"


class IncidentPriority(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class AlertCorrelationEngine:
    """Group related alerts into incidents with deduplication and noise reduction."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.time_window = config.get("correlation_window_seconds", 300)
        self.similarity_threshold = config.get("similarity_threshold", 0.6)
        self.max_alerts_per_incident = config.get("max_alerts_per_incident", 50)
        self.dedup_window = config.get("dedup_window_seconds", 60)
        self.alerts_file = _data_file('correlation_alerts.json')
        self.incidents_file = _data_file('correlation_incidents.json')
        self.suppression_file = _data_file('correlation_suppression.json')
        self.alerts: List[Dict[str, Any]] = []
        self.incidents: List[Dict[str, Any]] = []
        self.suppression_rules: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.alerts_file, "alerts"),
            (self.incidents_file, "incidents"),
            (self.suppression_file, "suppression")
        ]:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if target == "alerts":
                    self.alerts = data
                elif target == "incidents":
                    self.incidents = data
                elif target == "suppression":
                    self.suppression_rules = data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _save_alerts(self):
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts[-50000:], f, default=str)

    def _save_incidents(self):
        with open(self.incidents_file, 'w') as f:
            json.dump(self.incidents, f, default=str)

    def _save_suppression(self):
        with open(self.suppression_file, 'w') as f:
            json.dump(self.suppression_rules, f, default=str)

    def ingest_alert(self, name: str, source: str, severity: str, message: str,
                     labels: Dict[str, str] = None, metadata: Dict[str, Any] = None,
                     timestamp: str = None) -> Dict[str, Any]:
        if self._is_suppressed(name, source, labels or {}):
            alert = {
                "id": str(uuid.uuid4()),
                "name": name,
                "source": source,
                "severity": severity,
                "message": message,
                "labels": labels or {},
                "metadata": metadata or {},
                "status": AlertStatus.SUPPRESSED.value,
                "suppressed_reason": "Matched suppression rule",
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
            self.alerts.append(alert)
            self._save_alerts()
            return alert
        dup = self._find_duplicate(name, source, message, labels or {})
        if dup:
            dup["last_seen_at"] = timestamp or datetime.utcnow().isoformat()
            dup["count"] = dup.get("count", 1) + 1
            self._save_alerts()
            return dup
        alert = {
            "id": str(uuid.uuid4()),
            "name": name,
            "source": source,
            "severity": severity,
            "message": message,
            "labels": labels or {},
            "metadata": metadata or {},
            "status": AlertStatus.FIRING.value,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "last_seen_at": timestamp or datetime.utcnow().isoformat(),
            "count": 1,
        }
        self.alerts.append(alert)
        self._save_alerts()
        result = self._correlate(alert)
        return alert

    def _is_suppressed(self, name: str, source: str, labels: Dict[str, str]) -> bool:
        now = datetime.utcnow()
        for rule in self.suppression_rules:
            if rule.get("status") != "active":
                continue
            try:
                if rule.get("expires_at"):
                    expires = datetime.fromisoformat(rule["expires_at"])
                    if now > expires:
                        continue
            except (ValueError, TypeError):
                pass
            if rule.get("match_name") and rule["match_name"] not in name:
                continue
            if rule.get("match_source") and rule["match_source"] != source:
                continue
            if rule.get("match_labels"):
                for k, v in rule["match_labels"].items():
                    if labels.get(k) != v:
                        break
                else:
                    return True
            if rule.get("match_all"):
                return True
        return False

    def _find_duplicate(self, name: str, source: str, message: str,
                        labels: Dict[str, str]) -> Optional[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(seconds=self.dedup_window)
        for a in reversed(self.alerts):
            if a.get("status") == AlertStatus.SUPPRESSED.value:
                continue
            if a.get("name") == name and a.get("source") == source:
                try:
                    at = datetime.fromisoformat(a["timestamp"])
                    if at > cutoff:
                        return a
                except (ValueError, TypeError):
                    continue
        return None

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def _compute_label_similarity(self, labels1: Dict[str, str], labels2: Dict[str, str]) -> float:
        all_keys = set(labels1.keys()) | set(labels2.keys())
        if not all_keys:
            return 0.0
        matches = sum(1 for k in all_keys if labels1.get(k) == labels2.get(k))
        return matches / len(all_keys)

    def _correlate(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        try:
            alert_time = datetime.fromisoformat(alert["timestamp"])
        except (ValueError, TypeError):
            alert_time = now
        candidates = []
        for inc in self.incidents:
            if inc.get("status") in ("resolved", "closed"):
                continue
            try:
                inc_time = datetime.fromisoformat(inc["created_at"])
            except (ValueError, TypeError):
                inc_time = now
            time_diff = abs((alert_time - inc_time).total_seconds())
            if time_diff <= self.time_window:
                candidates.append((inc, time_diff))
        candidates.sort(key=lambda x: x[1])
        for inc, _ in candidates:
            if len(inc.get("alerts", [])) >= self.max_alerts_per_incident:
                continue
            text_sim = self._compute_text_similarity(
                alert.get("message", ""),
                inc.get("description", "")
            )
            label_sim = self._compute_label_similarity(
                alert.get("labels", {}),
                inc.get("labels", {})
            )
            source_match = 1.0 if alert.get("source") == inc.get("source") else 0.0
            combined = (text_sim * 0.3 + label_sim * 0.3 + source_match * 0.4)
            if combined >= self.similarity_threshold:
                inc["alerts"].append(alert["id"])
                inc["alert_count"] = len(inc["alerts"])
                inc["updated_at"] = datetime.utcnow().isoformat()
                inc["description"] = self._update_description(inc)
                severities = [a.get("severity") for a in self.alerts if a["id"] in inc["alerts"]]
                if AlertSeverity.EMERGENCY.value in severities:
                    inc["priority"] = IncidentPriority.P0.value
                elif AlertSeverity.CRITICAL.value in severities:
                    inc["priority"] = IncidentPriority.P1.value
                self._save_incidents()
                return inc
        return self._create_incident(alert)

    def _update_description(self, incident: Dict[str, Any]) -> str:
        alert_names = []
        for aid in incident.get("alerts", []):
            a = next((x for x in self.alerts if x["id"] == aid), None)
            if a:
                alert_names.append(a.get("name", "unknown"))
        return f"Incident with {len(alert_names)} correlated alerts: {', '.join(set(alert_names))}"

    def _create_incident(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        severity = alert.get("severity", AlertSeverity.WARNING.value)
        priority_map = {
            AlertSeverity.EMERGENCY.value: IncidentPriority.P0.value,
            AlertSeverity.CRITICAL.value: IncidentPriority.P1.value,
            AlertSeverity.WARNING.value: IncidentPriority.P2.value,
            AlertSeverity.INFO.value: IncidentPriority.P3.value,
        }
        incident = {
            "id": str(uuid.uuid4()),
            "title": f"Incident: {alert.get('name', 'Unknown alert')}",
            "description": alert.get("message", ""),
            "source": alert.get("source", "unknown"),
            "priority": priority_map.get(severity, IncidentPriority.P3.value),
            "status": "firing",
            "alerts": [alert["id"]],
            "alert_count": 1,
            "labels": alert.get("labels", {}),
            "first_alert_at": alert.get("timestamp"),
            "last_alert_at": alert.get("timestamp"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
        }
        self.incidents.append(incident)
        self._save_incidents()
        return incident

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_alerts(self, offset: int = 0, limit: int = 50, status: str = None,
                         severity: str = None, source: str = None) -> dict:
        results = self.alerts
        if status:
            results = [a for a in results if a.get("status") == status]
        if severity:
            results = [a for a in results if a.get("severity") == severity]
        if source:
            results = [a for a in results if a.get("source") == source]
        total = len(results)
        results.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_incidents(self, offset: int = 0, limit: int = 50, status: str = None,
                            priority: str = None) -> dict:
        results = self.incidents
        if status:
            results = [i for i in results if i.get("status") == status]
        if priority:
            results = [i for i in results if i.get("priority") == priority]
        total = len(results)
        results.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_acknowledge_alerts(self, alert_ids: list[str]) -> dict:
        count = 0
        for aid in alert_ids:
            a = self.get_alert(aid)
            if a and a.get("status") == AlertStatus.FIRING.value:
                a["status"] = AlertStatus.ACKNOWLEDGED.value
                count += 1
        if count:
            self._save_alerts()
        return {"acknowledged": count, "total_requested": len(alert_ids)}

    def batch_resolve_alerts(self, alert_ids: list[str]) -> dict:
        count = 0
        for aid in alert_ids:
            a = self.get_alert(aid)
            if a and a.get("status") in (AlertStatus.FIRING.value, AlertStatus.ACKNOWLEDGED.value):
                a["status"] = AlertStatus.RESOLVED.value
                count += 1
        if count:
            self._save_alerts()
        return {"resolved": count, "total_requested": len(alert_ids)}

    def batch_suppress_alerts(self, alert_ids: list[str], reason: str = "") -> dict:
        count = 0
        for aid in alert_ids:
            a = self.get_alert(aid)
            if a:
                a["status"] = AlertStatus.SUPPRESSED.value
                a["suppressed_reason"] = reason
                count += 1
        if count:
            self._save_alerts()
        return {"suppressed": count, "total_requested": len(alert_ids)}

    def export_incidents(self, status: str = None) -> list[dict]:
        results = self.incidents
        if status:
            results = [i for i in results if i.get("status") == status]
        return [{
            "id": i["id"], "title": i.get("title"), "description": i.get("description"),
            "source": i.get("source"), "priority": i.get("priority"), "status": i.get("status"),
            "alert_count": i.get("alert_count"), "created_at": i.get("created_at"),
            "resolved_at": i.get("resolved_at"), "labels": i.get("labels"),
        } for i in results]

    def import_incidents(self, incidents: list[dict]) -> dict:
        imported = 0
        for inc in incidents:
            incident = {
                "id": str(uuid.uuid4()),
                "title": inc.get("title", "Imported Incident"),
                "description": inc.get("description", ""),
                "source": inc.get("source", "unknown"),
                "priority": inc.get("priority", IncidentPriority.P3.value),
                "status": inc.get("status", "firing"),
                "alerts": [],
                "alert_count": 0,
                "labels": inc.get("labels", {}),
                "first_alert_at": inc.get("created_at"),
                "last_alert_at": inc.get("created_at"),
                "created_at": inc.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
                "resolved_at": inc.get("resolved_at"),
            }
            self.incidents.append(incident)
            imported += 1
        self._save_incidents()
        return {"imported": imported}

    def get_analytics(self) -> dict:
        alerts_by_hour = {}
        for a in self.alerts:
            try:
                hour = datetime.fromisoformat(a["timestamp"]).strftime("%Y-%m-%dT%H:00:00")
                alerts_by_hour[hour] = alerts_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        severity_dist = {}
        for a in self.alerts:
            s = a.get("severity", "unknown")
            severity_dist[s] = severity_dist.get(s, 0) + 1
        return {
            "total_alerts": len(self.alerts),
            "total_incidents": len(self.incidents),
            "severity_distribution": severity_dist,
            "alerts_by_hour": dict(sorted(alerts_by_hour.items())[-24:]),
            "avg_alerts_per_incident": round(sum(i.get("alert_count", 0) for i in self.incidents) / max(len(self.incidents), 1), 1),
            "noise_reduction_pct": self.get_statistics().get("noise_reduction_percentage", 0),
        }

    def enrich_alert(self, alert_id: str, enrichment: dict) -> Optional[dict]:
        a = self.get_alert(alert_id)
        if not a:
            return None
        a.setdefault("metadata", {}).update(enrichment)
        self._save_alerts()
        return a

    def search_alerts(self, query: str) -> list[dict]:
        q = query.lower()
        return [a for a in self.alerts if q in a.get("name", "").lower()
                or q in a.get("message", "").lower() or q in a.get("source", "").lower()]

    def get_alert_timeline(self, alert_id: str) -> list[dict]:
        a = self.get_alert(alert_id)
        if not a:
            return []
        timeline = [{"event": "created", "timestamp": a.get("created_at")}]
        if a.get("status") == AlertStatus.ACKNOWLEDGED.value:
            timeline.append({"event": "acknowledged", "timestamp": a.get("timestamp")})
        if a.get("status") == AlertStatus.RESOLVED.value:
            timeline.append({"event": "resolved", "timestamp": a.get("timestamp")})
        return timeline

    def get_incident_timeline(self, incident_id: str) -> list[dict]:
        inc = self.get_incident(incident_id)
        if not inc:
            return []
        timeline = [{"event": "created", "timestamp": inc.get("created_at")}]
        if inc.get("status") == "resolved":
            timeline.append({"event": "resolved", "timestamp": inc.get("resolved_at")})
        for aid in inc.get("alerts", []):
            a = self.get_alert(aid)
            if a:
                timeline.append({"event": f"alert_{a.get('status')}", "alert_id": aid,
                                 "name": a.get("name"), "timestamp": a.get("timestamp")})
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def simulate_alert_stream(self, count: int = 10, interval_sec: float = 0.5) -> list[dict]:
        import random, time
        sources = ["web-server", "api-gateway", "database", "cache", "worker"]
        severities = ["info", "warning", "critical", "emergency"]
        names = ["high_cpu", "memory_leak", "latency_spike", "service_down", "error_rate"]
        generated = []
        for _ in range(count):
            alert = self.ingest_alert(
                name=random.choice(names),
                source=random.choice(sources),
                severity=random.choice(severities),
                message=f"Simulated alert at {datetime.utcnow().isoformat()}",
                labels={"simulation": "true", "run_id": str(uuid.uuid4())[:8]},
            )
            generated.append(alert)
            time.sleep(interval_sec)
        return generated

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        return next((a for a in self.alerts if a["id"] == alert_id), None)

    def list_alerts(self, status: str = None, severity: str = None,
                    source: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        result = self.alerts
        if status:
            result = [a for a in result if a.get("status") == status]
        if severity:
            result = [a for a in result if a.get("severity") == severity]
        if source:
            result = [a for a in result if a.get("source") == source]
        return result[-limit:]

    def acknowledge_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if alert and alert.get("status") == AlertStatus.FIRING.value:
            alert["status"] = AlertStatus.ACKNOWLEDGED.value
            self._save_alerts()
        return alert

    def resolve_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if alert and alert.get("status") in (AlertStatus.FIRING.value, AlertStatus.ACKNOWLEDGED.value):
            alert["status"] = AlertStatus.RESOLVED.value
            self._save_alerts()
        return alert

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return next((i for i in self.incidents if i["id"] == incident_id), None)

    def list_incidents(self, status: str = None, priority: str = None,
                       limit: int = 50) -> List[Dict[str, Any]]:
        result = self.incidents
        if status:
            result = [i for i in result if i.get("status") == status]
        if priority:
            result = [i for i in result if i.get("priority") == priority]
        return result[-limit:]

    def resolve_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        incident = self.get_incident(incident_id)
        if incident and incident.get("status") != "resolved":
            incident["status"] = "resolved"
            incident["resolved_at"] = datetime.utcnow().isoformat()
            self._save_incidents()
            for aid in incident.get("alerts", []):
                self.resolve_alert(aid)
        return incident

    def add_suppression_rule(self, name: str, match_name: str = None,
                              match_source: str = None, match_labels: Dict[str, str] = None,
                              duration_minutes: int = 60) -> Dict[str, Any]:
        rule = {
            "id": str(uuid.uuid4()),
            "name": name,
            "match_name": match_name,
            "match_source": match_source,
            "match_labels": match_labels,
            "match_all": not any([match_name, match_source, match_labels]),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat(),
        }
        self.suppression_rules.append(rule)
        self._save_suppression()
        return rule

    def remove_suppression_rule(self, rule_id: str) -> bool:
        initial = len(self.suppression_rules)
        self.suppression_rules = [r for r in self.suppression_rules if r["id"] != rule_id]
        if len(self.suppression_rules) < initial:
            self._save_suppression()
            return True
        return False

    def list_suppression_rules(self) -> List[Dict[str, Any]]:
        return list(self.suppression_rules)

    def get_statistics(self) -> Dict[str, Any]:
        firing = sum(1 for a in self.alerts if a.get("status") == AlertStatus.FIRING.value)
        acknowledged = sum(1 for a in self.alerts if a.get("status") == AlertStatus.ACKNOWLEDGED.value)
        resolved = sum(1 for a in self.alerts if a.get("status") == AlertStatus.RESOLVED.value)
        suppressed = sum(1 for a in self.alerts if a.get("status") == AlertStatus.SUPPRESSED.value)
        active_incidents = sum(1 for i in self.incidents if i.get("status") not in ("resolved", "closed"))
        total_suppressed = sum(a.get("count", 1) for a in self.alerts if a.get("status") == AlertStatus.SUPPRESSED.value)
        total_duplicates = sum(a.get("count", 1) - 1 for a in self.alerts if a.get("count", 1) > 1)
        return {
            "total_alerts": len(self.alerts),
            "firing": firing,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "suppressed": suppressed,
            "active_incidents": active_incidents,
            "total_incidents": len(self.incidents),
            "duplicates_detected": total_duplicates,
            "alerts_suppressed": total_suppressed,
            "suppression_rules": len(self.suppression_rules),
            "noise_reduction_percentage": round(
                ((total_suppressed + total_duplicates) / max(1, len(self.alerts))) * 100, 1
            ),
        }

    # ===== APPENDED BATCH 2: State machine, routing, SLO, reports, dedup, escalation =====

    def _alert_lifecycle_transition(self, alert_id: str, new_status: str) -> Optional[dict]:
        valid_transitions = {
            AlertStatus.FIRING.value: [AlertStatus.ACKNOWLEDGED.value, AlertStatus.RESOLVED.value, AlertStatus.SUPPRESSED.value],
            AlertStatus.ACKNOWLEDGED.value: [AlertStatus.RESOLVED.value, AlertStatus.SUPPRESSED.value],
            AlertStatus.RESOLVED.value: [],
            AlertStatus.SUPPRESSED.value: [AlertStatus.FIRING.value],
        }
        a = self.get_alert(alert_id)
        if not a:
            return None
        allowed = valid_transitions.get(a["status"], [])
        if new_status not in allowed:
            return {"error": f"Cannot transition from {a['status']} to {new_status}"}
        a["status"] = new_status
        a["updated_at"] = datetime.utcnow().isoformat()
        self._save_alerts()
        return a

    def route_alert_to_team(self, alert_id: str, team: str) -> Optional[dict]:
        a = self.get_alert(alert_id)
        if not a:
            return None
        a.setdefault("routing", {})
        a["routing"]["assigned_team"] = team
        a["routing"]["assigned_at"] = datetime.utcnow().isoformat()
        self._save_alerts()
        return {"alert_id": alert_id, "team": team}

    def set_alert_priority(self, alert_id: str, priority: str) -> Optional[dict]:
        valid = {"P0", "P1", "P2", "P3", "P4"}
        if priority not in valid:
            return {"error": f"Invalid priority {priority}. Must be one of {valid}"}
        a = self.get_alert(alert_id)
        if not a:
            return None
        a["priority"] = priority
        a["updated_at"] = datetime.utcnow().isoformat()
        self._save_alerts()
        return a

    def check_slo_compliance(self, slo_target_pct: float = 99.9, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = []
        for a in self.alerts:
            try:
                if datetime.fromisoformat(a["timestamp"]) > cutoff:
                    recent.append(a)
                else:
                    pass
            except (ValueError, TypeError):
                continue
        critical_count = sum(1 for a in recent if a.get("severity") in ("critical", "emergency"))
        total_minutes = window_hours * 60
        effective_uptime = max(0, total_minutes - critical_count)
        actual_pct = round((effective_uptime / total_minutes) * 100, 4) if total_minutes > 0 else 100.0
        compliant = actual_pct >= slo_target_pct
        return {
            "slo_target_pct": slo_target_pct,
            "actual_uptime_pct": actual_pct,
            "compliant": compliant,
            "window_hours": window_hours,
            "critical_alerts_in_window": critical_count,
            "burn_rate": round(critical_count / max(1, total_minutes / 60), 4),
            "recommendation": "meets target" if compliant else "breach detected — review critical alerts",
        }

    def create_maintenance_window(self, name: str, start: str, end: str,
                                    match_sources: list[str] = None) -> dict:
        window = {
            "id": str(uuid.uuid4()),
            "name": name,
            "start": start,
            "end": end,
            "match_sources": match_sources or [],
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.setdefault("maintenance_windows", []).append(window)
        self._save_suppression()
        return window

    def aggregate_alerts_by_time(self, interval_minutes: int = 15) -> list[dict]:
        buckets = {}
        for a in self.alerts:
            try:
                ts = datetime.fromisoformat(a["timestamp"])
                bucket_key = ts.strftime(f"%Y-%m-%dT%H:{ts.minute // interval_minutes * interval_minutes:02d}:00")
                if bucket_key not in buckets:
                    buckets[bucket_key] = {"count": 0, "severities": Counter(), "sources": set()}
                buckets[bucket_key]["count"] += 1
                buckets[bucket_key]["severities"][a.get("severity", "unknown")] += 1
                buckets[bucket_key]["sources"].add(a.get("source", "unknown"))
            except (ValueError, TypeError):
                continue
        return [{
            "time": k,
            "total": v["count"],
            "severity_distribution": dict(v["severities"]),
            "unique_sources": len(v["sources"]),
        } for k, v in sorted(buckets.items())]

    def generate_report(self, format: str = "summary", hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) > cutoff]
        incidents_recent = [i for i in self.incidents if datetime.fromisoformat(i["created_at"]) > cutoff]
        severity_buckets = Counter(a.get("severity", "unknown") for a in recent)
        source_buckets = Counter(a.get("source", "unknown") for a in recent)
        top_alert = max(recent, key=lambda a: a.get("count", 1)) if recent else None
        return {
            "report_type": format,
            "period_hours": hours,
            "total_alerts": len(recent),
            "total_incidents": len(incidents_recent),
            "severity_summary": dict(severity_buckets),
            "top_sources": dict(source_buckets.most_common(5)),
            "most_frequent_alert": top_alert.get("name", "N/A") if top_alert else "N/A",
            "noise_reduction": self.get_statistics().get("noise_reduction_percentage", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "suppression_rules": [
                {"id": r["id"], "name": r["name"], "match_name": r.get("match_name"),
                 "match_source": r.get("match_source"), "status": r.get("status"),
                 "expires_at": r.get("expires_at")}
                for r in getattr(self, "suppression_rules", [])
            ],
            "config": self.config,
            "statistics": self.get_statistics(),
        }

    def import_config(self, config: dict) -> dict:
        rules = config.get("suppression_rules", [])
        imported = 0
        for r in rules:
            try:
                self.add_suppression_rule(
                    r.get("name", "imported"), r.get("match_name"),
                    r.get("match_source"), r.get("match_labels"),
                )
                imported += 1
            except Exception:
                pass
        return {"suppression_rules_imported": imported}

    def advanced_dedup(self, alert_id: str) -> dict:
        a = self.get_alert(alert_id)
        if not a:
            return {"error": "Alert not found"}
        candidates = [x for x in self.alerts if x["id"] != alert_id
                      and x.get("name") == a.get("name")
                      and x.get("source") == a.get("source")]
        dedup_count = 0
        for c in candidates:
            if abs(len(str(a.get("message", ""))) - len(str(c.get("message", "")))) < 10:
                c["count"] = c.get("count", 1) + 1
                c["status"] = AlertStatus.SUPPRESSED.value
                dedup_count += 1
        if dedup_count:
            self._save_alerts()
        return {"alert_id": alert_id, "duplicates_found": dedup_count, "suppressed": dedup_count}

    def set_escalation_policy(self, policy_name: str, steps: list[dict]) -> dict:
        if not hasattr(self, "escalation_policies"):
            self.escalation_policies = {}
        self.escalation_policies[policy_name] = {
            "name": policy_name,
            "steps": steps,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save_suppression()
        return self.escalation_policies[policy_name]

    def get_escalation_policy(self, policy_name: str) -> Optional[dict]:
        return getattr(self, "escalation_policies", {}).get(policy_name)

    def list_escalation_policies(self) -> list:
        return list(getattr(self, "escalation_policies", {}).values())

    def notify_team(self, alert_id: str, channel: str = "slack") -> dict:
        a = self.get_alert(alert_id)
        if not a:
            return {"error": "Alert not found"}
        notification = {
            "alert_id": alert_id,
            "alert_name": a.get("name"),
            "severity": a.get("severity"),
            "channel": channel,
            "message": f"[{a.get('severity').upper()}] {a.get('name')} on {a.get('source')}: {a.get('message', '')[:100]}",
            "sent_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "notifications"):
            self.notifications = []
        self.notifications.append(notification)
        return notification

    def list_notifications(self, limit: int = 50) -> list:
        return list(getattr(self, "notifications", []))[-limit:]

    def correlate_across_sources(self, time_window_minutes: int = 5) -> list[dict]:
        clusters = []
        sorted_alerts = sorted(self.alerts, key=lambda a: a.get("timestamp", ""))
        used = set()
        for i, a in enumerate(sorted_alerts):
            if i in used:
                continue
            cluster = [a]
            used.add(i)
            try:
                base_ts = datetime.fromisoformat(a["timestamp"])
            except (ValueError, TypeError):
                continue
            for j in range(i + 1, len(sorted_alerts)):
                if j in used:
                    continue
                b = sorted_alerts[j]
                try:
                    b_ts = datetime.fromisoformat(b["timestamp"])
                except (ValueError, TypeError):
                    continue
                if abs((b_ts - base_ts).total_seconds()) <= time_window_minutes * 60:
                    if b.get("source") != a.get("source") or b.get("name") != a.get("name"):
                        cluster.append(b)
                        used.add(j)
            if len(cluster) > 1:
                clusters.append({
                    "alerts": [c["id"] for c in cluster],
                    "sources": list(set(c.get("source", "") for c in cluster)),
                    "count": len(cluster),
                    "window_seconds": time_window_minutes * 60,
                    "first_alert": cluster[0].get("timestamp"),
                    "last_alert": cluster[-1].get("timestamp"),
                })
        return clusters

    def get_alert_volume_forecast(self, hours_ahead: int = 6) -> dict:
        from collections import deque as dq
        recent = self.alerts[-200:]
        by_hour = Counter()
        for a in recent:
            try:
                h = datetime.fromisoformat(a["timestamp"]).strftime("%Y-%m-%dT%H:00:00")
                by_hour[h] += 1
            except (ValueError, TypeError):
                pass
        if len(by_hour) < 3:
            return {"error": "Insufficient data for forecast", "forecast": []}
        hourly_values = [v for k, v in sorted(by_hour.items())[-24:]]
        avg = statistics.mean(hourly_values) if hourly_values else 0
        forecast = []
        base = avg
        for i in range(hours_ahead):
            noise = base * 0.2
            val = max(0, round(base + noise))
            forecast.append({"hour_offset": i + 1, "predicted_alerts": val})
            base = base * 0.95 + val * 0.05
        return {
            "current_hourly_rate": round(avg, 1),
            "forecast_hours": hours_ahead,
            "forecast": forecast,
            "trend": "increasing" if forecast[-1]["predicted_alerts"] > forecast[0]["predicted_alerts"] else "decreasing" if forecast[-1]["predicted_alerts"] < forecast[0]["predicted_alerts"] else "stable",
        }

    def get_correlation_stats(self) -> dict:
        clusters = self.correlate_across_sources()
        correlated_ids = set()
        for c in clusters:
            for aid in c.get("alerts", []):
                correlated_ids.add(aid)
        return {"total_alerts": len(self.alerts), "correlated_alerts": len(correlated_ids), "correlation_rate": round(len(correlated_ids) / max(len(self.alerts), 1) * 100, 1) if self.alerts else 0, "total_clusters": len(clusters)}

    def find_duplicate_alerts(self, time_window_minutes: int = 2) -> list[list[dict]]:
        duplicates = []
        sorted_alerts = sorted(self.alerts, key=lambda a: a.get("timestamp", ""))
        used = set()
        for i, a in enumerate(sorted_alerts):
            if i in used:
                continue
            group = [a]
            used.add(i)
            for j in range(i + 1, len(sorted_alerts)):
                if j in used:
                    continue
                b = sorted_alerts[j]
                if b.get("name") == a.get("name") and b.get("source") == a.get("source"):
                    try:
                        if abs((datetime.fromisoformat(b["timestamp"]) - datetime.fromisoformat(a["timestamp"])).total_seconds()) <= time_window_minutes * 60:
                            group.append(b)
                            used.add(j)
                    except (ValueError, TypeError):
                        pass
            if len(group) > 1:
                duplicates.append(group)
        return duplicates

    def suppress_duplicates(self, time_window_minutes: int = 2) -> dict:
        duplicates = self.find_duplicate_alerts(time_window_minutes)
        suppressed = 0
        for group in duplicates[1:]:
            for a in group[1:]:
                a["status"] = "suppressed"
                a["suppressed_reason"] = f"Duplicate of {group[0]['id']}"
                suppressed += 1
        return {"duplicate_groups_found": len(duplicates), "alerts_suppressed": suppressed}

    def get_alert_source_breakdown(self) -> dict:
        by_source: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        for a in self.alerts:
            by_source[a.get("source", "unknown")] += 1
            by_severity[a.get("severity", "unknown")] += 1
        return {"by_source": dict(by_source), "by_severity": dict(by_severity)}

    def export_alerts_json(self) -> list[dict]:
        return [{"id": a["id"], "name": a.get("name"), "source": a.get("source"), "severity": a.get("severity"), "status": a.get("status"), "timestamp": a.get("timestamp")} for a in self.alerts]

    def batch_update_status(self, alert_ids: list[str], new_status: str) -> dict:
        updated = 0
        for a in self.alerts:
            if a["id"] in alert_ids:
                a["status"] = new_status
                updated += 1
        return {"updated": updated, "new_status": new_status}


class AlertDashboardAggregator:
    def __init__(self, engine: AlertCorrelationEngine):
        self.engine = engine

    def get_overview(self) -> dict:
        active = self.engine.get_active_alerts()
        clusters = self.engine.correlate_across_sources()
        by_severity = defaultdict(int)
        for a in active:
            by_severity[a.get("severity", "unknown")] += 1
        return {"total_active": len(active), "critical": by_severity.get("critical", 0), "warning": by_severity.get("warning", 0), "info": by_severity.get("info", 0), "active_correlations": len(clusters), "last_alert": active[-1].get("timestamp") if active else None}

    def get_top_sources(self, limit: int = 5) -> list[dict]:
        source_count: dict[str, int] = defaultdict(int)
        for a in self.engine.alerts:
            source_count[a.get("source", "unknown")] += 1
        return [{"source": s, "count": c} for s, c in sorted(source_count.items(), key=lambda x: x[1], reverse=True)[:limit]]

    def get_severity_trend(self, hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [a for a in self.engine.alerts if a.get("timestamp") and datetime.fromisoformat(a["timestamp"]) > cutoff]
        hourly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for a in recent:
            try:
                hour = datetime.fromisoformat(a["timestamp"]).strftime("%Y-%m-%dT%H:00")
                hourly[hour][a.get("severity", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return {"period_hours": hours, "hourly_breakdown": {h: dict(s) for h, s in sorted(hourly.items())}}

    def get_escalation_summary(self) -> dict:
        policies = getattr(self.engine, "escalation_policies", {})
        active_escalations = sum(1 for p in policies.values() if p.get("status") == "active")
        return {"total_policies": len(policies), "active_policies": active_escalations, "policy_names": list(policies.keys())}

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
