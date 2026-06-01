import json
import math
import uuid
import statistics
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvent:
    anomaly_id: str
    event_type: str
    severity: str
    title: str
    description: str
    detected_at: datetime
    source: str
    score: float
    related_events: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "source": self.source,
            "score": round(self.score, 3),
            "related_events": self.related_events,
            "metadata": self.metadata,
        }


@dataclass
class UserBaseline:
    user_id: str
    avg_login_frequency: float
    avg_session_duration: float
    typical_access_hours: List[int]
    typical_locations: List[str]
    typical_actions: Counter
    total_events: int
    established_since: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "avg_login_frequency": round(self.avg_login_frequency, 2),
            "avg_session_duration": round(self.avg_session_duration, 2),
            "typical_access_hours": self.typical_access_hours,
            "typical_locations": self.typical_locations,
            "typical_actions": dict(self.typical_actions.most_common(10)),
            "total_events": self.total_events,
            "established_since": self.established_since.isoformat(),
        }


class IsolationForest:
    def __init__(self, n_trees: int = 100, sample_size: int = 256):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.trees = []
        self._fitted = False

    def fit(self, data: List[Dict[str, float]]) -> None:
        self.trees = []
        for _ in range(self.n_trees):
            sample = data[:self.sample_size] if len(data) > self.sample_size else data
            tree = self._build_tree(sample, 0, 8)
            self.trees.append(tree)
        self._fitted = True

    def _build_tree(self, data: List[Dict[str, float]], depth: int, max_depth: int) -> Dict[str, Any]:
        if len(data) <= 1 or depth >= max_depth:
            return {"type": "leaf", "size": len(data), "depth": depth}
        dims = list(data[0].keys()) if data else ["value"]
        split_dim = dims[depth % len(dims)]
        values = [d.get(split_dim, 0.0) for d in data]
        if len(set(values)) < 2:
            return {"type": "leaf", "size": len(data), "depth": depth}
        split_val = (min(values) + max(values)) / 2
        left = [d for d in data if d.get(split_dim, 0.0) < split_val]
        right = [d for d in data if d.get(split_dim, 0.0) >= split_val]
        return {
            "type": "node",
            "split_dim": split_dim,
            "split_val": split_val,
            "left": self._build_tree(left, depth + 1, max_depth),
            "right": self._build_tree(right, depth + 1, max_depth),
        }

    def anomaly_score(self, point: Dict[str, float]) -> float:
        if not self._fitted:
            return 0.5
        depths = [self._depth(t, point, 0) for t in self.trees]
        avg_depth = statistics.mean(depths) if depths else 0
        c = 2 * (math.log(self.sample_size - 1) + 0.5772156649) - (2 * (self.sample_size - 1) / self.sample_size) if self.sample_size > 2 else 1
        return 2 ** (-avg_depth / c) if c > 0 else 0.5

    def _depth(self, tree: Dict[str, Any], point: Dict[str, float], current_depth: int) -> int:
        if tree.get("type") == "leaf":
            return current_depth + tree.get("depth", current_depth)
        split_dim = tree.get("split_dim", "value")
        split_val = tree.get("split_val", 0)
        if point.get(split_dim, 0) < split_val:
            return self._depth(tree["left"], point, current_depth + 1)
        else:
            return self._depth(tree["right"], point, current_depth + 1)


class AuditAnalyticsManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._anomalies: List[AnomalyEvent] = []
        self._baselines: Dict[str, UserBaseline] = {}
        self._event_log: List[Dict[str, Any]] = []
        self._anomaly_detector = IsolationForest(n_trees=50, sample_size=128)
        self._detection_threshold = config.get("anomaly_threshold", 0.7)
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("AuditAnalyticsManager initialized")

    async def close(self) -> None:
        self._anomalies.clear()
        self._baselines.clear()
        self._event_log.clear()
        logger.info("AuditAnalyticsManager closed")

    def ingest_event(self, event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        self._event_log.append(event)
        if len(self._event_log) > 100000:
            self._event_log = self._event_log[-50000:]

        anomaly = self._analyze_event(event)
        if anomaly:
            self._anomalies.append(anomaly)
            if len(self._anomalies) > 10000:
                self._anomalies = self._anomalies[-5000:]
            return anomaly
        return None

    def _analyze_event(self, event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        user_id = event.get("user_id", "anonymous")
        action = event.get("action", "")
        timestamp_str = event.get("timestamp", datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        location = event.get("location", {}).get("country", "unknown")
        ip = event.get("ip_address", "")

        anomalies_found = []

        if self._is_unusual_access_time(user_id, hour, day_of_week):
            anomalies_found.append({
                "type": "unusual_access_time",
                "severity": "medium",
                "score": 0.6,
                "description": f"Unusual access at hour {hour} on day {day_of_week}",
            })

        if self._is_new_location(user_id, location):
            anomalies_found.append({
                "type": "new_location",
                "severity": "medium",
                "score": 0.65,
                "description": f"Access from new location: {location}",
            })

        if self._is_impossible_travel(user_id, timestamp, ip, location):
            anomalies_found.append({
                "type": "impossible_travel",
                "severity": "high",
                "score": 0.85,
                "description": f"Impossible travel detected from {location}",
            })

        if self._is_failed_login_spike(user_id):
            anomalies_found.append({
                "type": "failed_login_spike",
                "severity": "high",
                "score": 0.8,
                "description": "Spike in failed login attempts detected",
            })

        if self._is_privilege_escalation_suspicious(event):
            anomalies_found.append({
                "type": "suspicious_privilege_escalation",
                "severity": "critical",
                "score": 0.9,
                "description": "Suspicious privilege escalation detected",
            })

        if not anomalies_found:
            self._update_baseline(user_id, event)
            return None

        best_anomaly = max(anomalies_found, key=lambda a: a["score"])
        if best_anomaly["score"] < self._detection_threshold:
            self._update_baseline(user_id, event)
            return None

        return AnomalyEvent(
            anomaly_id=str(uuid.uuid4()),
            event_type=best_anomaly["type"],
            severity=best_anomaly["severity"],
            title=best_anomaly["description"],
            description=best_anomaly["description"],
            detected_at=datetime.utcnow(),
            source="audit_analytics",
            score=best_anomaly["score"],
            related_events=[],
            metadata={
                "user_id": user_id,
                "action": action,
                "timestamp": timestamp_str,
                "location": location,
                "ip": ip,
                "anomalies_considered": anomalies_found,
            },
        )

    def _is_unusual_access_time(self, user_id: str, hour: int, day_of_week: int) -> bool:
        baseline = self._baselines.get(user_id)
        if not baseline:
            return False
        if not baseline.typical_access_hours:
            return False
        day_start = day_of_week * 24
        if hour not in baseline.typical_access_hours:
            if len(baseline.typical_access_hours) >= 3:
                deviation_score = 1 - (abs(hour - statistics.median(baseline.typical_access_hours)) / 12)
                return deviation_score < 0.3
            return True
        return False

    def _is_new_location(self, user_id: str, location: str) -> bool:
        baseline = self._baselines.get(user_id)
        if not baseline or location == "unknown":
            return False
        if baseline.total_events < 5:
            return False
        return location not in baseline.typical_locations

    def _is_impossible_travel(self, user_id: str, current_time: datetime,
                              ip: str, location: str) -> bool:
        if not self._event_log:
            return False
        user_events = [e for e in self._event_log[-50:] if e.get("user_id") == user_id]
        if len(user_events) < 2:
            return False
        last_event = user_events[-2]
        try:
            last_time = datetime.fromisoformat(last_event.get("timestamp", current_time.isoformat()))
        except (ValueError, TypeError):
            return False
        last_location = last_event.get("location", {}).get("country", "")
        if not last_location or location == last_location:
            return False
        time_diff = abs((current_time - last_time).total_seconds())
        return time_diff < 3600

    def _is_failed_login_spike(self, user_id: str) -> bool:
        recent = [e for e in self._event_log[-200:]
                  if e.get("user_id") == user_id and e.get("action") == "login_failed"]
        if len(recent) < 5:
            return False
        time_window = len(set(e.get("timestamp", "")[:10] for e in recent))
        return len(recent) >= 10 and time_window <= 2

    def _is_privilege_escalation_suspicious(self, event: Dict[str, Any]) -> bool:
        action = event.get("action", "")
        if "role_change" in action.lower() or "permission" in action.lower():
            if event.get("metadata", {}).get("escalated_by") != event.get("user_id"):
                return True
        return False

    def _update_baseline(self, user_id: str, event: Dict[str, Any]) -> None:
        timestamp_str = event.get("timestamp", datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        if user_id not in self._baselines:
            self._baselines[user_id] = UserBaseline(
                user_id=user_id,
                avg_login_frequency=0.0,
                avg_session_duration=0.0,
                typical_access_hours=[timestamp.hour],
                typical_locations=[event.get("location", {}).get("country", "unknown")],
                typical_actions=Counter([event.get("action", "unknown")]),
                total_events=1,
                established_since=timestamp,
            )
        else:
            baseline = self._baselines[user_id]
            baseline.total_events += 1
            baseline.typical_access_hours.append(timestamp.hour)
            if len(baseline.typical_access_hours) > 100:
                baseline.typical_access_hours = baseline.typical_access_hours[-100:]
            location = event.get("location", {}).get("country", "unknown")
            if location not in baseline.typical_locations and len(baseline.typical_locations) < 10:
                baseline.typical_locations.append(location)
            baseline.typical_actions.update([event.get("action", "unknown")])

    def get_anomalies(self, severity: Optional[str] = None, event_type: Optional[str] = None,
                      limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        anomalies = list(self._anomalies)
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        if event_type:
            anomalies = [a for a in anomalies if a.event_type == event_type]
        anomalies.sort(key=lambda a: a.detected_at, reverse=True)
        return [a.to_dict() for a in anomalies[offset:offset + limit]]

    def get_anomaly(self, anomaly_id: str) -> Optional[AnomalyEvent]:
        for a in self._anomalies:
            if a.anomaly_id == anomaly_id:
                return a
        return None

    def run_analysis(self) -> Dict[str, Any]:
        if len(self._event_log) < 10:
            return {"status": "insufficient_data", "events_analyzed": len(self._event_log)}

        features = []
        for event in self._event_log[-1000:]:
            timestamp_str = event.get("timestamp", datetime.utcnow().isoformat())
            try:
                ts = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                continue
            features.append({
                "hour": ts.hour,
                "day": ts.weekday(),
                "action_freq": 1,
            })

        if len(features) >= 10:
            self._anomaly_detector.fit(features)
            new_anomalies = 0
            for event, feat in zip(self._event_log[-1000:], features):
                score = self._anomaly_detector.anomaly_score(feat)
                if score > self._detection_threshold:
                    anomaly = self.ingest_event(dict(event))
                    if anomaly:
                        new_anomalies += 1

        return {
            "status": "completed",
            "events_analyzed": len(self._event_log),
            "new_anomalies_detected": len(self._anomalies),
            "model_trained": self._anomaly_detector._fitted,
        }

    def get_trends(self, metric: str = "events", days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        relevant = [e for e in self._event_log
                    if datetime.fromisoformat(e.get("timestamp", cutoff.isoformat())) >= cutoff]
        daily_counts = defaultdict(int)
        daily_anomalies = defaultdict(int)
        severity_counts = Counter()
        type_counts = Counter()

        for event in relevant:
            day = event.get("timestamp", "")[:10]
            daily_counts[day] += 1
            for anomaly in self._anomalies:
                if anomaly.detected_at.strftime("%Y-%m-%d") == day:
                    daily_anomalies[day] += 1
                    severity_counts[anomaly.severity] += 1
                    type_counts[anomaly.event_type] += 1

        return {
            "period_days": days,
            "total_events": len(relevant),
            "total_anomalies": sum(daily_anomalies.values()),
            "daily_events": dict(sorted(daily_counts.items())),
            "daily_anomalies": dict(sorted(daily_anomalies.items())),
            "severity_distribution": dict(severity_counts),
            "type_distribution": dict(type_counts),
            "avg_events_per_day": round(len(relevant) / max(days, 1), 1),
        }

    def get_correlations(self) -> List[Dict[str, Any]]:
        if len(self._anomalies) < 3:
            return []
        correlations = []
        type_pairs = Counter()
        for i, a1 in enumerate(self._anomalies):
            for a2 in self._anomalies[i + 1:]:
                time_diff = abs((a1.detected_at - a2.detected_at).total_seconds())
                if time_diff < 300:
                    pair = tuple(sorted([a1.event_type, a2.event_type]))
                    type_pairs[pair] += 1
        for pair, count in type_pairs.most_common(5):
            correlations.append({
                "event_types": list(pair),
                "correlation_count": count,
                "description": f"{pair[0]} frequently occurs near {pair[1]}",
            })
        return correlations

    def get_user_baseline(self, user_id: str) -> Optional[Dict[str, Any]]:
        baseline = self._baselines.get(user_id)
        return baseline.to_dict() if baseline else None

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_events_ingested": len(self._event_log),
            "total_anomalies_detected": len(self._anomalies),
            "users_tracked": len(self._baselines),
            "detection_threshold": self._detection_threshold,
            "severity_breakdown": dict(Counter(a.severity for a in self._anomalies)),
            "type_breakdown": dict(Counter(a.event_type for a in self._anomalies)),
        }
