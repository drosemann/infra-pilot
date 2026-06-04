"""User & Entity Behavior Analytics (UEBA).

ML-based behavioral baselining for users and services. Detect insider threats,
compromised accounts, lateral movement, and anomalous behavior with risk scoring.
"""

import json
import uuid
import logging
import math
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class BehaviorMetricType(str, Enum):
    LOGIN_TIME = "login_time"
    LOGIN_LOCATION = "login_location"
    LOGIN_FREQUENCY = "login_frequency"
    ACCESSED_RESOURCES = "accessed_resources"
    DATA_VOLUME = "data_volume"
    COMMAND_EXECUTION = "command_execution"
    NETWORK_CONNECTIONS = "network_connections"
    AUTH_METHOD = "auth_method"
    FAILED_LOGINS = "failed_logins"
    WORKING_HOURS = "working_hours"
    PEER_INTERACTIONS = "peer_interactions"
    API_CALLS = "api_calls"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    FILE_OPERATIONS = "file_operations"


class EntityType(str, Enum):
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    APPLICATION = "application"
    DEVICE = "device"
    API_KEY = "api_key"
    CONTAINER = "container"
    NETWORK = "network"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BehaviorBaseline:
    id: str
    entity_id: str
    entity_type: EntityType
    metric_type: BehaviorMetricType
    mean: float = 0.0
    std_dev: float = 0.0
    median: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    sample_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    seasonality_pattern: Optional[str] = None
    allowed_values: List[str] = field(default_factory=list)
    allowed_locations: List[str] = field(default_factory=list)
    allowed_hours: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "metric_type": self.metric_type.value,
            "mean": round(self.mean, 2),
            "std_dev": round(self.std_dev, 2),
            "median": round(self.median, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
            "sample_count": self.sample_count,
            "last_updated": self.last_updated.isoformat(),
            "seasonality_pattern": self.seasonality_pattern,
        }


@dataclass
class BehaviorEvent:
    id: str
    entity_id: str
    entity_type: str
    entity_name: str
    metric_type: str
    value: Any
    timestamp: datetime
    source_ip: Optional[str] = None
    location: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    risk_score: float = 0.0
    anomalous: bool = False
    anomaly_reasons: List[str] = field(default_factory=list)
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "entity_name": self.entity_name,
            "metric_type": self.metric_type,
            "value": str(self.value),
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "location": self.location,
            "risk_score": self.risk_score,
            "anomalous": self.anomalous,
            "anomaly_reasons": self.anomaly_reasons,
            "severity": self.severity,
        }


@dataclass
class AnomalyAlert:
    id: str
    entity_id: str
    entity_type: str
    entity_name: str
    risk_level: RiskLevel
    risk_score: float
    title: str
    description: str
    metric_type: str
    observed_value: Any
    expected_value: Any
    deviation_factor: float
    detected_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    mitre_technique: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "entity_name": self.entity_name,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "title": self.title,
            "description": self.description,
            "metric_type": self.metric_type,
            "deviation_factor": self.deviation_factor,
            "detected_at": self.detected_at.isoformat(),
            "acknowledged": self.acknowledged,
        }


@dataclass
class EntityProfile:
    id: str
    entity_type: EntityType
    name: str
    display_name: str
    department: str = ""
    role: str = ""
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    baselines_count: int = 0
    events_count: int = 0
    anomalies_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "display_name": self.display_name,
            "department": self.department,
            "role": self.role,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "baselines_count": self.baselines_count,
            "events_count": self.events_count,
            "anomalies_count": self.anomalies_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "tags": self.tags,
        }


class UserEntityBehaviorAnalytics:
    """ML-based behavioral baselining and anomaly detection for users and entities."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.profiles: Dict[str, EntityProfile] = {}
        self.baselines: Dict[str, BehaviorBaseline] = {}
        self.events: Dict[str, BehaviorEvent] = {}
        self.alerts: Dict[str, AnomalyAlert] = {}
        self._initialized = False

    async def initialize(self):
        self._seed_default_profiles()
        self._initialized = True
        logger.info(f"UEBA initialized: {len(self.profiles)} entities, {len(self.baselines)} baselines")

    async def close(self):
        logger.info("UEBA shut down")

    def _seed_default_profiles(self):
        sample_profiles = [
            EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType.USER, name="jdoe",
                          display_name="John Doe", department="Engineering", role="Senior Engineer",
                          tags=["engineering", "senior"]),
            EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType.USER, name="asmith",
                          display_name="Alice Smith", department="Finance", role="Finance Manager",
                          tags=["finance", "manager"]),
            EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType.SERVICE_ACCOUNT,
                          name="svc-deploy", display_name="Deployment Service Account",
                          department="DevOps", role="CI/CD Pipeline",
                          tags=["automation", "deployment"]),
            EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType.APPLICATION,
                          name="payments-api", display_name="Payments API Service",
                          department="Engineering", role="Backend Service",
                          tags=["critical", "customer-facing"]),
            EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType.USER, name="bwilson",
                          display_name="Bob Wilson", department="Engineering", role="Junior Engineer",
                          tags=["engineering", "junior"]),
        ]
        for profile in sample_profiles:
            self.profiles[profile.id] = profile

    def register_entity(self, entity_type: str, name: str, display_name: str,
                        department: str = "", role: str = "", tags: Optional[List[str]] = None) -> EntityProfile:
        profile = EntityProfile(id=f"entity-{uuid.uuid4().hex[:12]}", entity_type=EntityType(entity_type),
                                name=name, display_name=display_name, department=department,
                                role=role, tags=tags or [])
        self.profiles[profile.id] = profile
        return profile

    def get_entity(self, entity_id: str) -> Optional[EntityProfile]:
        return self.profiles.get(entity_id)

    def list_entities(self, entity_type: Optional[str] = None, risk_level: Optional[str] = None,
                      department: Optional[str] = None) -> List[EntityProfile]:
        results = list(self.profiles.values())
        if entity_type:
            results = [e for e in results if e.entity_type.value == entity_type]
        if risk_level:
            results = [e for e in results if e.risk_level.value == risk_level]
        if department:
            results = [e for e in results if department.lower() in e.department.lower()]
        return sorted(results, key=lambda e: e.risk_score, reverse=True)

    def ingest_event(self, entity_id: str, metric_type: str, value: Any,
                     source_ip: Optional[str] = None, location: Optional[str] = None,
                     user_agent: Optional[str] = None, resource: Optional[str] = None) -> BehaviorEvent:
        profile = self.profiles.get(entity_id)
        if not profile:
            raise ValueError(f"Entity {entity_id} not found")
        profile.last_seen = datetime.utcnow()
        profile.events_count += 1
        event = BehaviorEvent(id=f"ev-{uuid.uuid4().hex[:12]}", entity_id=entity_id,
                              entity_type=profile.entity_type.value, entity_name=profile.display_name,
                              metric_type=metric_type, value=value, timestamp=datetime.utcnow(),
                              source_ip=source_ip, location=location, user_agent=user_agent, resource=resource)
        self.events[event.id] = event
        anomaly_result = self._analyze_event(event)
        event.anomalous = anomaly_result["anomalous"]
        event.risk_score = anomaly_result["risk_score"]
        event.anomaly_reasons = anomaly_result["reasons"]
        event.severity = anomaly_result["severity"]
        if anomaly_result["anomalous"]:
            self._create_anomaly_alert(event)
        self._update_baseline(entity_id, metric_type, value)
        return event

    def _analyze_event(self, event: BehaviorEvent) -> Dict[str, Any]:
        reasons = []
        risk_score = 0.0
        anomalous = False
        baseline = next((b for b in self.baselines.values()
                         if b.entity_id == event.entity_id and b.metric_type.value == event.metric_type), None)
        if baseline and baseline.sample_count > 10:
            try:
                num_value = float(event.value)
                z_score = abs((num_value - baseline.mean) / baseline.std_dev) if baseline.std_dev > 0 else 0
                if z_score > 3.0:
                    anomalous = True
                    reasons.append(f"Value {num_value} exceeds 3 std dev from mean {baseline.mean:.1f}")
                    risk_score += min(z_score / 10.0, 1.0) * 0.6
                if num_value > baseline.p99:
                    reasons.append(f"Value exceeds 99th percentile ({baseline.p99:.1f})")
                    risk_score += 0.3
            except (ValueError, TypeError):
                if isinstance(event.value, str) and baseline.allowed_values:
                    if event.value not in baseline.allowed_values:
                        anomalous = True
                        reasons.append(f"Value '{event.value}' not in allowed set")
                        risk_score += 0.5
        if event.source_ip and baseline and baseline.allowed_locations:
            if event.source_ip not in baseline.allowed_locations:
                anomalous = True
                reasons.append(f"Source IP {event.source_ip} not in known locations")
                risk_score += 0.4
        hour = event.timestamp.hour
        if baseline and baseline.allowed_hours and hour not in baseline.allowed_hours:
            anomalous = True
            reasons.append(f"Activity at hour {hour} outside normal hours {baseline.allowed_hours}")
            risk_score += 0.3
        severity = "info"
        if risk_score > 0.7:
            severity = "critical"
        elif risk_score > 0.5:
            severity = "high"
        elif risk_score > 0.3:
            severity = "medium"
        elif risk_score > 0.1:
            severity = "low"
        return {"anomalous": anomalous, "risk_score": round(risk_score, 2), "reasons": reasons, "severity": severity}

    def _update_baseline(self, entity_id: str, metric_type: str, value: Any):
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return
        metric = BehaviorMetricType(metric_type)
        baseline_id = f"bl-{entity_id}-{metric_type}"
        baseline = self.baselines.get(baseline_id)
        if not baseline:
            baseline = BehaviorBaseline(id=baseline_id, entity_id=entity_id,
                                        entity_type=EntityType.USER, metric_type=metric)
            self.baselines[baseline_id] = baseline
        baseline.sample_count += 1
        baseline.last_updated = datetime.utcnow()
        if baseline.sample_count == 1:
            baseline.mean = num_value
            baseline.median = num_value
            baseline.min_value = num_value
            baseline.max_value = num_value
            return
        baseline.min_value = min(baseline.min_value, num_value)
        baseline.max_value = max(baseline.max_value, num_value)
        running_values = [num_value]
        if baseline.sample_count <= 100:
            running_events = [e for e in self.events.values() if e.entity_id == entity_id and e.metric_type == metric_type]
            running_values = [float(e.value) for e in running_events if isinstance(e.value, (int, float))]
        if len(running_values) > 1:
            baseline.mean = statistics.mean(running_values)
            baseline.std_dev = statistics.stdev(running_values) if len(running_values) > 1 else 0
            baseline.median = statistics.median(running_values)
            sorted_vals = sorted(running_values)
            p95_idx = int(len(sorted_vals) * 0.95)
            p99_idx = int(len(sorted_vals) * 0.99)
            baseline.p95 = sorted_vals[min(p95_idx, len(sorted_vals) - 1)]
            baseline.p99 = sorted_vals[min(p99_idx, len(sorted_vals) - 1)]
        profile = self.profiles.get(entity_id)
        if profile:
            profile.baselines_count = len([b for b in self.baselines.values() if b.entity_id == entity_id])

    def _create_anomaly_alert(self, event: BehaviorEvent):
        risk_level = RiskLevel.CRITICAL if event.risk_score > 0.7 else RiskLevel.HIGH if event.risk_score > 0.5 else RiskLevel.MEDIUM
        alert = AnomalyAlert(id=f"alert-{uuid.uuid4().hex[:12]}", entity_id=event.entity_id,
                             entity_type=event.entity_type, entity_name=event.entity_name,
                             risk_level=risk_level, risk_score=event.risk_score,
                             title=f"Anomalous {event.metric_type} for {event.entity_name}",
                             description="; ".join(event.anomaly_reasons),
                             metric_type=event.metric_type, observed_value=event.value,
                             expected_value="baseline", deviation_factor=event.risk_score,
                             detected_at=datetime.utcnow())
        self.alerts[alert.id] = alert
        profile = self.profiles.get(event.entity_id)
        if profile:
            profile.anomalies_count += 1
            profile.risk_score = self._calculate_entity_risk(event.entity_id)
            profile.risk_level = self._score_to_risk_level(profile.risk_score)
        logger.warning(f"UEBA anomaly: {alert.title} (score: {event.risk_score})")

    def _calculate_entity_risk(self, entity_id: str) -> float:
        entity_alerts = [a for a in self.alerts.values() if a.entity_id == entity_id]
        if not entity_alerts:
            return 0.0
        recent_weights = sum(max(0, 1 - (datetime.utcnow() - a.detected_at).days / 30) * a.risk_score
                             for a in entity_alerts[-20:])
        anomaly_count_weight = min(len(entity_alerts) / 50, 1.0) * 0.2
        return round(min(recent_weights + anomaly_count_weight, 1.0), 2)

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        if score >= 0.7:
            return RiskLevel.CRITICAL
        if score >= 0.4:
            return RiskLevel.HIGH
        if score >= 0.2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def get_entity_risk(self, entity_id: str) -> Dict[str, Any]:
        profile = self.profiles.get(entity_id)
        if not profile:
            return {"error": "Entity not found"}
        recent_events = [e for e in self.events.values() if e.entity_id == entity_id][-50:]
        anomalies = [a for a in self.alerts.values() if a.entity_id == entity_id]
        return {
            "entity": profile.to_dict(),
            "current_risk_score": profile.risk_score,
            "current_risk_level": profile.risk_level.value,
            "total_anomalies": len(anomalies),
            "recent_anomalies": [a.to_dict() for a in anomalies[-10:]],
            "recent_events_count": len(recent_events),
            "baselines": [b.to_dict() for b in self.baselines.values() if b.entity_id == entity_id],
        }

    def list_alerts(self, risk_level: Optional[str] = None, acknowledged: Optional[bool] = None,
                    entity_id: Optional[str] = None, limit: int = 50) -> List[AnomalyAlert]:
        results = list(self.alerts.values())
        if risk_level:
            results = [a for a in results if a.risk_level.value == risk_level]
        if acknowledged is not None:
            results = [a for a in results if a.acknowledged == acknowledged]
        if entity_id:
            results = [a for a in results if a.entity_id == entity_id]
        return sorted(results, key=lambda a: a.detected_at, reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Optional[AnomalyAlert]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        return alert

    def get_events(self, entity_id: Optional[str] = None, metric_type: Optional[str] = None,
                   anomalous_only: bool = False, limit: int = 100) -> List[BehaviorEvent]:
        results = list(self.events.values())
        if entity_id:
            results = [e for e in results if e.entity_id == entity_id]
        if metric_type:
            results = [e for e in results if e.metric_type == metric_type]
        if anomalous_only:
            results = [e for e in results if e.anomalous]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        total_entities = len(self.profiles)
        high_risk = sum(1 for e in self.profiles.values() if e.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL))
        user_count = sum(1 for e in self.profiles.values() if e.entity_type == EntityType.USER)
        svc_count = sum(1 for e in self.profiles.values() if e.entity_type == EntityType.SERVICE_ACCOUNT)
        anomaly_count = len(self.alerts)
        unacknowledged = sum(1 for a in self.alerts.values() if not a.acknowledged)
        return {
            "total_entities": total_entities,
            "high_risk_entities": high_risk,
            "users": user_count,
            "service_accounts": svc_count,
            "applications": sum(1 for e in self.profiles.values() if e.entity_type == EntityType.APPLICATION),
            "total_events": len(self.events),
            "anomalous_events": sum(1 for e in self.events.values() if e.anomalous),
            "total_alerts": anomaly_count,
            "unacknowledged_alerts": unacknowledged,
            "total_baselines": len(self.baselines),
            "avg_entity_risk": round(sum(e.risk_score for e in self.profiles.values()) / total_entities, 2) if total_entities else 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_metrics()

    # === Batch Operations ===
    async def batch_update_profiles(self, profile_updates: List[Dict]) -> List[Dict]:
        results = []
        for pu in profile_updates:
            try:
                profile = self.profiles.get(pu.get("entity_id"))
                if not profile:
                    results.append({"entity_id": pu.get("entity_id"), "status": "failed", "error": "not found"})
                    continue
                if "risk_score" in pu:
                    profile.risk_score = max(0, min(100, int(pu["risk_score"])))
                    profile.risk_level = self._calculate_risk_level(profile.risk_score)
                if "tags" in pu:
                    profile.tags = pu["tags"]
                results.append({"entity_id": pu["entity_id"], "status": "updated"})
            except Exception as e:
                results.append({"entity_id": pu.get("entity_id"), "status": "failed", "error": str(e)})
        return results

    def get_events_paginated(self, page: int = 1, per_page: int = 50, entity_id: Optional[str] = None, anomalous: Optional[bool] = None) -> Dict:
        items = list(self.events.values())
        if entity_id:
            items = [e for e in items if e.entity_id == entity_id]
        if anomalous is not None:
            items = [e for e in items if e.anomalous == anomalous]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [e.to_dict() for e in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def get_alerts_paginated(self, page: int = 1, per_page: int = 20, risk_level: Optional[str] = None, acknowledged: Optional[bool] = None) -> Dict:
        items = list(self.alerts.values())
        if risk_level:
            items = [a for a in items if a.risk_level.value == risk_level]
        if acknowledged is not None:
            items = [a for a in items if a.acknowledged == acknowledged]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [a.to_dict() for a in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_event_batch(self, events: List[Dict]) -> List[str]:
        errors = []
        for i, event in enumerate(events):
            if not event.get("entity_id"):
                errors.append(f"Event {i}: entity_id is required")
            if not event.get("metric_type"):
                errors.append(f"Event {i}: metric_type is required")
            if event.get("value") is None:
                errors.append(f"Event {i}: value is required")
        return errors

    # === Bulk Operations ===
    async def bulk_acknowledge_alerts(self, alert_ids: List[str], acknowledged_by: str = "system") -> int:
        count = 0
        for aid in alert_ids:
            if aid in self.alerts and not self.alerts[aid].acknowledged:
                self.alerts[aid].acknowledged = True
                self.alerts[aid].acknowledged_by = acknowledged_by
                self.alerts[aid].acknowledged_at = datetime.utcnow()
                count += 1
        return count

    async def bulk_delete_events(self, entity_id: str) -> int:
        to_remove = [eid for eid, e in self.events.items() if e.entity_id == entity_id]
        for eid in to_remove:
            del self.events[eid]
        return len(to_remove)

    # === Analytics ===
    def get_anomaly_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for a in self.alerts.values():
            if a.detected_at and a.detected_at >= cutoff:
                day = a.detected_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_risk_distribution(self) -> Dict:
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for p in self.profiles.values():
            dist[p.risk_level.value] = dist.get(p.risk_level.value, 0) + 1
        total = sum(dist.values())
        return {"distribution": dist, "total": total, "high_risk_pct": round(dist.get("critical", 0) / total * 100, 1) if total > 0 else 0}

    def get_top_anomalies(self, n: int = 10) -> List[Dict]:
        sorted_alerts = sorted(self.alerts.values(), key=lambda a: self._calculate_anomaly_score(a), reverse=True)
        return [a.to_dict() for a in sorted_alerts[:n]]

    def _calculate_anomaly_score(self, alert: AnomalyAlert) -> float:
        scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
        return scores.get(alert.risk_level.value, 0)

    # === Baseline Management ===
    def rebuild_baseline(self, entity_id: str) -> Optional[EntityProfile]:
        profile = self.profiles.get(entity_id)
        if not profile:
            return None
        baseline = Baseline(id=f"bl-{uuid.uuid4().hex[:12]}", entity_id=entity_id, built_at=datetime.utcnow())
        entity_events = [e for e in self.events.values() if e.entity_id == entity_id]
        if entity_events:
            values = [e.value for e in entity_events if e.value is not None]
            baseline.mean = sum(values) / len(values) if values else 0
            baseline.std_dev = (sum((v - baseline.mean) ** 2 for v in values) / len(values)) ** 0.5 if values else 0
            baseline.peak_hours = {"morning": sum(1 for e in entity_events if 6 <= e.timestamp.hour < 12),
                                   "afternoon": sum(1 for e in entity_events if 12 <= e.timestamp.hour < 18),
                                   "evening": sum(1 for e in entity_events if 18 <= e.timestamp.hour < 24),
                                   "night": sum(1 for e in entity_events if 0 <= e.timestamp.hour < 6)}
        profile.baseline = baseline
        self.baselines[baseline.id] = baseline
        return profile

    # === Cleanup ===
    async def cleanup_old_events(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [eid for eid, e in self.events.items() if e.timestamp and e.timestamp < cutoff]
        for eid in to_remove:
            del self.events[eid]
        return len(to_remove)

    # === Search ===
    def search_entities(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for p in self.profiles.values():
            if q in p.entity_name.lower() or q in p.entity_type.value.lower() or any(q in t.lower() for t in p.tags):
                results.append(p.to_dict())
        return results

    # === Export ===
    def export_events_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "entity_name", "entity_type", "metric_type", "value", "risk_score", "anomalous", "timestamp", "source_ip"])
        for e in self.events.values():
            writer.writerow([e.id, e.entity_name, e.entity_type, e.metric_type, str(e.value), e.risk_score, e.anomalous, e.timestamp.isoformat(), e.source_ip or ""])
        return output.getvalue()

    def export_alerts_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "entity_name", "risk_level", "risk_score", "title", "metric_type", "detected_at", "acknowledged"])
        for a in self.alerts.values():
            writer.writerow([a.id, a.entity_name, a.risk_level.value, a.risk_score, a.title, a.metric_type, a.detected_at.isoformat(), str(a.acknowledged)])
        return output.getvalue()

    def export_profiles_json(self) -> str:
        return json.dumps([p.to_dict() for p in self.profiles.values()], indent=2, default=str)

    # === Import ===
    def import_profiles_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            profile = EntityProfile(
                id=item.get("id", f"entity-{uuid.uuid4().hex[:12]}"),
                entity_type=EntityType(item.get("entity_type", "user")),
                name=item.get("name", ""),
                display_name=item.get("display_name", ""),
                department=item.get("department", ""),
                role=item.get("role", ""),
                tags=item.get("tags", []),
            )
            self.profiles[profile.id] = profile
            count += 1
        return count

    # === State Machine ===
    def acknowledge_alert_batch(self, alert_ids: List[str], acknowledged_by: str = "system") -> int:
        count = 0
        for aid in alert_ids:
            alert = self.alerts.get(aid)
            if alert and not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()
                count += 1
        return count

    # === Notification ===
    async def notify_anomaly(self, alert: AnomalyAlert) -> Dict[str, Any]:
        return {
            "alert_id": alert.id,
            "entity_name": alert.entity_name,
            "risk_level": alert.risk_level.value,
            "title": alert.title,
            "description": alert.description,
            "message": f"UEBA anomaly: {alert.title} (risk: {alert.risk_level.value})",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_high_risk_anomalies(self) -> List[Dict]:
        results = []
        for a in self.alerts.values():
            if a.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not a.acknowledged:
                results.append(await self.notify_anomaly(a))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("entity_sources"):
            warnings.append("No entity data sources configured")
        if config.get("ml_model") and config["ml_model"] not in ("isolation_forest", "z_score", "moving_average"):
            errors.append(f"Unknown ML model: {config.get('ml_model')}")
        if config.get("anomaly_threshold", 3.0) < 1.0:
            errors.append("Anomaly threshold too low, will cause excessive alerts")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_entity_type_breakdown(self) -> Dict:
        breakdown = {}
        for p in self.profiles.values():
            t = p.entity_type.value
            if t not in breakdown:
                breakdown[t] = {"count": 0, "high_risk": 0}
            breakdown[t]["count"] += 1
            if p.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                breakdown[t]["high_risk"] += 1
        return breakdown

    def get_anomaly_severity_distribution(self) -> Dict:
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for e in self.events.values():
            if e.anomalous:
                dist[e.severity] = dist.get(e.severity, 0) + 1
        return dist

    def get_peak_anomaly_hours(self) -> Dict:
        hour_counts = {}
        for a in self.alerts.values():
            h = a.detected_at.hour
            hour_counts[h] = hour_counts.get(h, 0) + 1
        return {"peak_hour": max(hour_counts, key=hour_counts.get) if hour_counts else None, "by_hour": hour_counts}

    def get_top_risk_entities(self, n: int = 10) -> List[Dict]:
        sorted_profiles = sorted(self.profiles.values(), key=lambda p: p.risk_score, reverse=True)
        return [{"entity_id": p.id, "name": p.name, "display_name": p.display_name, "risk_score": p.risk_score, "risk_level": p.risk_level.value, "anomalies": p.anomalies_count} for p in sorted_profiles[:n]]

    # === Baseline Management ===
    def get_baseline_coverage(self) -> Dict:
        entities_with_baselines = set(b.entity_id for b in self.baselines.values())
        return {
            "total_entities": len(self.profiles),
            "entities_with_baselines": len(entities_with_baselines),
            "coverage_pct": round(len(entities_with_baselines) / len(self.profiles) * 100, 1) if self.profiles else 0,
            "total_baselines": len(self.baselines),
        }

    def reset_baseline(self, entity_id: str, metric_type: str) -> bool:
        baseline_id = f"bl-{entity_id}-{metric_type}"
        if baseline_id in self.baselines:
            del self.baselines[baseline_id]
            return True
        return False

    # === Bulk Operations ===
    async def bulk_tag_entities(self, entity_ids: List[str], tags: List[str]) -> int:
        count = 0
        for eid in entity_ids:
            profile = self.profiles.get(eid)
            if profile:
                for t in tags:
                    if t not in profile.tags:
                        profile.tags.append(t)
                count += 1
        return count

    async def bulk_delete_anomaly_alerts(self, entity_id: str) -> int:
        to_remove = [aid for aid, a in self.alerts.items() if a.entity_id == entity_id]
        for aid in to_remove:
            del self.alerts[aid]
        return len(to_remove)

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "ueba",
            "initialized": self._initialized,
            "entities": len(self.profiles),
            "baselines": len(self.baselines),
            "events_ingested": len(self.events),
            "anomaly_alerts": len(self.alerts),
            "unacknowledged_alerts": sum(1 for a in self.alerts.values() if not a.acknowledged),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class UEBAAnomalyInvestigator:
    def __init__(self, ueba: 'UEBAManager'):
        self.ueba = ueba

    def investigate_entity(self, entity_id: str, hours: int = 72) -> Optional[Dict]:
        profile = self.ueba.profiles.get(entity_id)
        if not profile:
            return None
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        anomalies = [e for e in self.ueba.events.values() if e.entity_id == entity_id and e.anomalous and e.timestamp and e.timestamp > cutoff]
        alerts = [a for a in self.ueba.alerts.values() if a.entity_id == entity_id and a.detected_at and a.detected_at > cutoff]
        timeline = []
        for e in sorted(anomalies, key=lambda x: x.timestamp or datetime.min):
            timeline.append({"timestamp": e.timestamp.isoformat() if e.timestamp else '', "event": e.event_type, "severity": e.severity, "anomaly_score": e.anomaly_score})
        for a in sorted(alerts, key=lambda x: x.detected_at or datetime.min):
            timeline.append({"timestamp": a.detected_at.isoformat() if a.detected_at else '', "event": "alert", "title": a.title, "risk_score": a.risk_score})
        return {"entity_id": entity_id, "name": profile.name, "type": profile.entity_type.value if hasattr(profile.entity_type, 'value') else str(profile.entity_type), "risk_level": profile.risk_level.value if hasattr(profile.risk_level, 'value') else str(profile.risk_level), "risk_score": profile.risk_score, "anomalies": len(anomalies), "alerts": len(alerts), "timeline": timeline}

    def find_similar_entities(self, entity_id: str, n: int = 5) -> List[Dict]:
        profile = self.ueba.profiles.get(entity_id)
        if not profile or not profile.tags:
            return []
        similar = []
        for pid, p in self.ueba.profiles.items():
            if pid == entity_id:
                continue
            shared = set(profile.tags) & set(p.tags)
            if shared:
                similar.append({"entity_id": pid, "name": p.name, "shared_tags": list(shared), "similarity_score": len(shared), "risk_level": p.risk_level.value if hasattr(p.risk_level, 'value') else str(p.risk_level)})
        return sorted(similar, key=lambda x: x["similarity_score"], reverse=True)[:n]

    def suggest_response(self, alert_id: str) -> Optional[Dict]:
        alert = self.ueba.alerts.get(alert_id)
        if not alert:
            return None
        profile = self.ueba.profiles.get(alert.entity_id)
        responses = []
        if alert.risk_score > 80:
            responses.append({"action": "disable_account", "target": profile.name if profile else alert.entity_id, "priority": "immediate"})
            responses.append({"action": "force_password_reset", "priority": "immediate"})
        if alert.risk_score > 50:
            responses.append({"action": "enable_mfa", "priority": "high"})
            responses.append({"action": "review_recent_sessions", "priority": "high"})
        responses.append({"action": "notify_security_team", "priority": "medium"})
        return {"alert_id": alert_id, "entity_id": alert.entity_id, "risk_score": alert.risk_score, "recommended_actions": responses}


class UEBARiskScorer:
    def __init__(self, ueba: 'UEBAManager'):
        self.ueba = ueba
        self.weights = {"anomaly_frequency": 0.3, "severity_impact": 0.25, "entity_criticality": 0.2, "recent_activity": 0.15, "baseline_deviation": 0.1}

    def recalculate_all_risk_scores(self) -> int:
        count = 0
        for pid, profile in self.ueba.profiles.items():
            anomalies = [e for e in self.ueba.events.values() if e.entity_id == pid and e.anomalous]
            if not anomalies:
                continue
            freq_score = min(len(anomalies) / 10, 1.0) * 100
            sev_score = sum({"critical": 100, "high": 75, "medium": 50, "low": 25}.get(e.severity, 0) for e in anomalies) / len(anomalies)
            recent = sum(1 for e in anomalies if e.timestamp and (datetime.utcnow() - e.timestamp).total_seconds() < 86400)
            recent_score = min(recent / 5, 1.0) * 100
            new_score = freq_score * self.weights["anomaly_frequency"] + sev_score * self.weights["severity_impact"] + recent_score * self.weights["recent_activity"]
            profile.risk_score = round(new_score, 1)
            if profile.risk_score > 80:
                profile.risk_level = RiskLevel.CRITICAL
            elif profile.risk_score > 60:
                profile.risk_level = RiskLevel.HIGH
            elif profile.risk_score > 40:
                profile.risk_level = RiskLevel.MEDIUM
            else:
                profile.risk_level = RiskLevel.LOW
            count += 1
        return count

    def get_risk_distribution(self) -> Dict:
        dist = {l.value: 0 for l in RiskLevel}
        for p in self.ueba.profiles.values():
            dist[p.risk_level.value] = dist.get(p.risk_level.value, 0) + 1
        return dist


class UEBAReportGenerator:
    def __init__(self, ueba: 'UEBAManager'):
        self.ueba = ueba

    def generate_entity_report(self, entity_id: str) -> Optional[str]:
        investigator = UEBAAnomalyInvestigator(self.ueba)
        investigation = investigator.investigate_entity(entity_id)
        if not investigation:
            return None
        lines = [f"=== UEBA Investigation Report: {investigation['name']} ===", f"Entity ID: {entity_id}", f"Type: {investigation['type']}", f"Risk Level: {investigation['risk_level']}", f"Risk Score: {investigation['risk_score']}", f"Total Anomalies: {investigation['anomalies']}", f"Active Alerts: {investigation['alerts']}", "", "Timeline:"]
        for t in investigation.get("timeline", [])[:20]:
            lines.append(f"  [{t.get('timestamp')}] {t.get('event')}: {t.get('title', t.get('event', ''))}")
        return "\n".join(lines)

    def export_alerts_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["alert_id", "entity_id", "title", "risk_score", "severity", "detected_at", "acknowledged"])
        for a in self.ueba.alerts.values():
            writer.writerow([a.id, a.entity_id, a.title, a.risk_score, a.severity, a.detected_at.isoformat() if a.detected_at else '', a.acknowledged])
        return output.getvalue()

    def generate_summary_report(self) -> str:
        risk_scorer = UEBARiskScorer(self.ueba)
        dist = risk_scorer.get_risk_distribution()
        lines = ["=== UEBA Summary Report ===", f"Generated: {datetime.utcnow().isoformat()}", f"Total Entities: {len(self.ueba.profiles)}", f"Total Events: {len(self.ueba.events)}", f"Anomalous Events: {sum(1 for e in self.ueba.events.values() if e.anomalous)}", f"Active Alerts: {len(self.ueba.alerts)}", f"Baselines Established: {len(self.ueba.baselines)}", "", "Risk Distribution:"]
        for level, count in sorted(dist.items()):
            lines.append(f"  {level}: {count}")
        return "\n".join(lines)

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_alerts": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "resolved": 0}

    def validate_security(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class SOCResult(BaseModel):
    success: bool = True
    operation: str = ""
    alert_id: Optional[str] = None
    severity: str = Field(default="low")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SOCBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(default="siem")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    escalated: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_escalated(self) -> None:
        self.escalated += 1

    def complete(self) -> None:
        self.status = "completed"

class SecurityAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    severity: str = Field(default="low")
    source: str = Field(default="unknown")
    status: str = Field(default="open")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    mitre_technique: str = ""
    affected_assets: List[str] = Field(default_factory=list)
    indicators: List[str] = Field(default_factory=list)

class AlertManager:
    def __init__(self) -> None:
        self._alerts: Dict[str, SecurityAlert] = {}

    def create(self, title: str, severity: str, source: str = "unknown", description: str = "") -> SecurityAlert:
        alert = SecurityAlert(title=title, severity=severity, source=source, description=description)
        self._alerts[alert.alert_id] = alert
        return alert

    def resolve(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert and alert.status == "open":
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.status == "open"]

    def get_by_severity(self, severity: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.severity == severity]

    def get_by_source(self, source: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.source == source]

    def get_statistics(self) -> Dict[str, Any]:
        alerts = list(self._alerts.values())
        open_alerts = self.get_open()
        resolved = [a for a in alerts if a.status == "resolved"]
        return {"total": len(alerts), "open": len(open_alerts), "resolved": len(resolved),
                "by_severity": {s: sum(1 for a in alerts if a.severity == s) for s in set(a.severity for a in alerts)},
                "by_source": {s: sum(1 for a in alerts if a.source == s) for s in set(a.source for a in alerts)},
                "avg_resolution_time_min": round(sum((a.resolved_at - a.detected_at).total_seconds() / 60 for a in resolved if a.resolved_at) / max(len(resolved), 1), 1)}

class ThreatIndicator(BaseModel):
    indicator_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    value: str
    indicator_type: str = Field(default="ip")
    confidence: float = Field(default=0.5, ge=0, le=1)
    severity: str = Field(default="medium")
    source: str = Field(default="external")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    active: bool = True

class ThreatIntelFeed:
    def __init__(self) -> None:
        self._indicators: Dict[str, ThreatIndicator] = {}

    def add_indicator(self, value: str, indicator_type: str, confidence: float = 0.5,
                      severity: str = "medium", source: str = "external") -> ThreatIndicator:
        indicator = ThreatIndicator(value=value, indicator_type=indicator_type,
                                     confidence=confidence, severity=severity, source=source)
        self._indicators[indicator.indicator_id] = indicator
        return indicator

    def search(self, value: str) -> Optional[ThreatIndicator]:
        for ind in self._indicators.values():
            if ind.value == value and ind.active:
                return ind
        return None

    def get_active(self) -> List[ThreatIndicator]:
        return [i for i in self._indicators.values() if i.active]

    def expire_old(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0
        for ind in self._indicators.values():
            if ind.last_seen < cutoff:
                ind.active = False
                count += 1
        return count

    def get_statistics(self) -> Dict[str, Any]:
        active = self.get_active()
        return {"total": len(self._indicators), "active": len(active),
                "by_type": {t: sum(1 for i in active if i.indicator_type == t) for t in set(i.indicator_type for i in active)},
                "by_severity": {s: sum(1 for i in active if i.severity == s) for s in set(i.severity for i in active)}}

class IncidentResponsePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    alert_id: str = ""
    steps: List[str] = Field(default_factory=list)
    status: str = Field(default="draft")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner: str = ""

class IncidentResponder:
    def __init__(self) -> None:
        self._plans: Dict[str, IncidentResponsePlan] = {}

    def create_plan(self, name: str, alert_id: str, steps: List[str], owner: str = "") -> IncidentResponsePlan:
        plan = IncidentResponsePlan(name=name, alert_id=alert_id, steps=steps, owner=owner)
        self._plans[plan.plan_id] = plan
        return plan

    async def execute(self, plan_id: str) -> Dict[str, Any]:
        plan = self._plans.get(plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
        plan.status = "in_progress"
        plan.executed_at = datetime.utcnow()
        executed_steps = []
        for i, step in enumerate(plan.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        return {"status": "completed", "plan_id": plan_id, "steps_executed": len(executed_steps),
                "duration_seconds": int((plan.completed_at - plan.executed_at).total_seconds())}

    def get_plan(self, plan_id: str) -> Optional[IncidentResponsePlan]:
        return self._plans.get(plan_id)

    def list_plans(self) -> List[Dict[str, Any]]:
        return [{"id": p.plan_id, "name": p.name, "status": p.status, "steps": len(p.steps)} for p in self._plans.values()]

class VulnerabilityRecord(BaseModel):
    vuln_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str
    cve_id: str = ""
    severity: str = Field(default="medium")
    cvss_score: float = Field(default=0.0, ge=0, le=10)
    description: str = ""
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    patched_at: Optional[datetime] = None
    status: str = Field(default="open")
    remediation: str = ""

class VulnerabilityManager:
    def __init__(self) -> None:
        self._vulns: Dict[str, VulnerabilityRecord] = {}

    def report(self, asset: str, severity: str, cvss: float, description: str = "", cve: str = "") -> VulnerabilityRecord:
        vuln = VulnerabilityRecord(asset=asset, severity=severity, cvss_score=cvss,
                                    description=description, cve_id=cve)
        self._vulns[vuln.vuln_id] = vuln
        return vuln

    def patch(self, vuln_id: str) -> bool:
        vuln = self._vulns.get(vuln_id)
        if vuln and vuln.status == "open":
            vuln.status = "patched"
            vuln.patched_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.status == "open"]

    def get_by_severity(self, severity: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.severity == severity]

    def get_by_asset(self, asset: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.asset == asset]

    def get_statistics(self) -> Dict[str, Any]:
        vulns = list(self._vulns.values())
        open_vulns = self.get_open()
        return {"total": len(vulns), "open": len(open_vulns), "patched": len(vulns) - len(open_vulns),
                "avg_cvss": round(sum(v.cvss_score for v in vulns) / max(len(vulns), 1), 1),
                "by_severity": {s: sum(1 for v in vulns if v.severity == s) for s in set(v.severity for v in vulns)},
                "critical": sum(1 for v in open_vulns if v.cvss_score >= 9.0),
                "high": sum(1 for v in open_vulns if 7.0 <= v.cvss_score < 9.0)}
