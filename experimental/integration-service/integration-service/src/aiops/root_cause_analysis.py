"""Feature 51: AI Root Cause Analysis — ML correlation of metrics, logs, traces to identify root cause."""

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


class EventType(Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    ALERT = "alert"
    DEPLOYMENT = "deployment"
    CONFIG_CHANGE = "config_change"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrelationMethod(Enum):
    TIME_PROXIMITY = "time_proximity"
    METRIC_CORRELATION = "metric_correlation"
    LOG_PATTERN = "log_pattern"
    TRACE_ANCESTOR = "trace_ancestor"
    GRAPH_PROPAGATION = "graph_propagation"
    ML_CLASSIFIER = "ml_classifier"
    SERVICE_DEPENDENCY = "service_dependency"


class RootCauseAnalyzer:
    """Correlate events from multiple observability sources to identify incident root cause."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.correlation_window = config.get("correlation_window_seconds", 300)
        self.min_confidence = config.get("min_confidence", 0.6)
        self.max_candidates = config.get("max_candidates", 20)
        self.graph_propagation_depth = config.get("graph_propagation_depth", 5)
        self.events_file = _data_file('rca_events.json')
        self.incidents_file = _data_file('rca_incidents.json')
        self.dependency_file = _data_file('rca_dependencies.json')
        self.events: List[Dict[str, Any]] = []
        self.incidents: List[Dict[str, Any]] = []
        self.dependency_graph: Dict[str, List[str]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.events_file, "events"),
            (self.incidents_file, "incidents"),
            (self.dependency_file, "deps")
        ]:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if target == "events":
                    self.events = data
                elif target == "incidents":
                    self.incidents = data
                elif target == "deps":
                    self.dependency_graph = data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _save_events(self):
        with open(self.events_file, 'w') as f:
            json.dump(self.events[-10000:], f, default=str)

    def _save_incidents(self):
        with open(self.incidents_file, 'w') as f:
            json.dump(self.incidents[-5000:], f, default=str)

    def _save_dependencies(self):
        with open(self.dependency_file, 'w') as f:
            json.dump(self.dependency_graph, f, default=str)

    def ingest_event(self, event_type: str, source: str, title: str, description: str,
                     metadata: Dict[str, Any] = None, severity: str = "medium",
                     timestamp: str = None) -> Dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "source": source,
            "title": title,
            "description": description,
            "metadata": metadata or {},
            "severity": severity,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.events.append(event)
        self._save_events()
        return event

    def set_dependency(self, service: str, depends_on: List[str]):
        self.dependency_graph[service] = depends_on
        self._save_dependencies()

    def remove_dependency(self, service: str):
        self.dependency_graph.pop(service, None)
        self._save_dependencies()

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        return dict(self.dependency_graph)

    def _find_time_proximal_events(self, incident_time: datetime, window: int = None) -> List[Dict[str, Any]]:
        if window is None:
            window = self.correlation_window
        candidates = []
        for e in self.events:
            try:
                et = datetime.fromisoformat(e["timestamp"])
                if abs((et - incident_time).total_seconds()) <= window:
                    candidates.append(e)
            except (ValueError, TypeError):
                continue
        return candidates

    def _compute_metric_correlation(self, events: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        scored = []
        metric_events = [e for e in events if e.get("event_type") == EventType.METRIC.value and "value" in e.get("metadata", {})]
        if len(metric_events) < 2:
            return [(e, 0.5) for e in events]
        values = [e["metadata"]["value"] for e in metric_events if isinstance(e["metadata"].get("value"), (int, float))]
        if not values:
            return [(e, 0.5) for e in events]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 1.0
        for e in metric_events:
            v = e["metadata"].get("value", 0)
            if isinstance(v, (int, float)) and stdev > 0:
                z = abs(v - mean) / stdev
                score = min(1.0, z / 5.0)
                scored.append((e, score))
            else:
                scored.append((e, 0.5))
        non_metric = [e for e in events if e.get("event_type") != EventType.METRIC.value]
        for e in non_metric:
            scored.append((e, 0.6))
        return scored

    def _compute_log_pattern_score(self, events: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        scored = []
        log_events = [e for e in events if e.get("event_type") == EventType.LOG.value]
        keywords = {"error": 0.9, "fail": 0.85, "crash": 0.95, "timeout": 0.8,
                    "exception": 0.85, "oom": 0.9, "panic": 0.95, "down": 0.8,
                    "unreachable": 0.85, "degraded": 0.75, "throttl": 0.7,
                    "backoff": 0.7, "retry": 0.6, "warn": 0.5, "slow": 0.6}
        for e in events:
            score = 0.5
            text = f"{e.get('title', '')} {e.get('description', '')}".lower()
            for kw, s in keywords.items():
                if kw in text:
                    score = max(score, s)
            if e.get("severity") == "critical":
                score = max(score, 0.9)
            elif e.get("severity") == "high":
                score = max(score, 0.75)
            scored.append((e, score))
        return scored

    def _propagate_through_graph(self, source_service: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(source_service, 0)]
        while queue:
            service, depth = queue.pop(0)
            if service in visited or depth > self.graph_propagation_depth:
                continue
            visited.add(service)
            if depth == 0:
                scores[service] = 1.0
            else:
                scores[service] = max(0.1, 1.0 - (depth * 0.25))
            for dep, deps in self.dependency_graph.items():
                if service in deps and dep not in visited:
                    queue.append((dep, depth + 1))
            for dep in self.dependency_graph.get(service, []):
                if dep not in visited:
                    queue.append((dep, depth + 1))
        return scores

    def _ml_classifier_rank(self, candidates: List[Dict[str, Any]], incident: Dict[str, Any]) -> List[Tuple[Dict[str, Any], float]]:
        scored = []
        incident_text = f"{incident.get('title', '')} {incident.get('description', '')}".lower()
        incident_words = set(incident_text.split())
        for c in candidates:
            score = 0.5
            c_text = f"{c.get('title', '')} {c.get('description', '')}".lower()
            c_words = set(c_text.split())
            if incident_words and c_words:
                overlap = len(incident_words & c_words) / len(incident_words | c_words)
                score += overlap * 0.3
            if c.get("source") == incident.get("source"):
                score += 0.1
            if c.get("event_type") == EventType.CONFIG_CHANGE.value:
                score += 0.15
            if c.get("event_type") == EventType.DEPLOYMENT.value:
                score += 0.1
            if c.get("severity") == "critical":
                score += 0.1
            elif c.get("severity") == "high":
                score += 0.05
            scored.append((c, min(1.0, score)))
        return scored

    def analyze(self, incident_id: str = None, incident_title: str = None,
                incident_description: str = None, incident_source: str = None,
                incident_time: str = None) -> Dict[str, Any]:
        if incident_id:
            incident = next((i for i in self.incidents if i["id"] == incident_id), None)
            if not incident:
                return {"error": f"Incident {incident_id} not found"}
        else:
            incident = {
                "id": str(uuid.uuid4()),
                "title": incident_title or "Unknown Incident",
                "description": incident_description or "",
                "source": incident_source or "unknown",
                "timestamp": incident_time or datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
            self.incidents.append(incident)
            self._save_incidents()

        try:
            incident_dt = datetime.fromisoformat(incident["timestamp"])
        except (ValueError, TypeError):
            incident_dt = datetime.utcnow()

        candidates = self._find_time_proximal_events(incident_dt)
        if not candidates:
            return {
                "incident_id": incident["id"],
                "root_cause": None,
                "confidence": 0.0,
                "explanation": "No correlated events found in the time window.",
                "correlated_events": [],
                "recommendations": ["Enable more comprehensive monitoring to improve root cause detection."]
            }

        methods = [
            ("time_proximity", self._compute_metric_correlation),
            ("log_pattern", self._compute_log_pattern_score),
            ("ml_classifier", lambda c: self._ml_classifier_rank(c, incident)),
        ]

        all_scores: Dict[str, List[float]] = defaultdict(list)
        for method_name, scorer in methods:
            try:
                scored = scorer(candidates)
                for event, score in scored:
                    all_scores[event["id"]].append(score)
            except Exception as e:
                logger.warning(f"Correlation method {method_name} failed: {e}")

        aggregated = []
        for event_id, scores in all_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score >= self.min_confidence:
                event = next((e for e in candidates if e["id"] == event_id), None)
                if event:
                    aggregated.append((event, avg_score))

        aggregated.sort(key=lambda x: x[1], reverse=True)
        aggregated = aggregated[:self.max_candidates]

        source_counter = Counter(e.get("source", "unknown") for e, _ in aggregated)
        type_counter = Counter(e.get("event_type", "unknown") for e, _ in aggregated)

        top_source = source_counter.most_common(1)
        top_type = type_counter.most_common(1)

        propagation_scores = {}
        if aggregated:
            top_source_name = aggregated[0][0].get("source", "unknown")
            propagation_scores = self._propagate_through_graph(top_source_name)

        top_3 = aggregated[:3]
        explanation_parts = []
        for event, score in top_3:
            source = event.get("source", "unknown")
            etype = event.get("event_type", "unknown")
            title = event.get("title", "unknown")
            explanation_parts.append(f"{source} [{etype}]: {title} (confidence: {score:.2f})")

        propagation_lines = []
        for svc, sc in sorted(propagation_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
            propagation_lines.append(f"{svc} (impact: {sc:.2f})")

        recommendations = []
        if top_type[0][0] == EventType.LOG.value:
            recommendations.append("Investigate log patterns — errors detected in correlated events.")
        if top_type[0][0] == EventType.METRIC.value:
            recommendations.append("Review metric anomalies — metrics show deviation in correlated events.")
        if top_source[0][0] != incident.get("source"):
            recommendations.append(f"Root cause may be in {top_source[0][0]} rather than {incident.get('source')}.")
        if aggregated and aggregated[0][1] < 0.7:
            recommendations.append("Low confidence correlation — manual investigation recommended.")
        if propagation_scores:
            recommendations.append(f"Potential blast radius: {', '.join(list(propagation_scores.keys())[:5])}.")

        root_cause = None
        if aggregated:
            best = aggregated[0]
            root_cause = {
                "event_id": best[0]["id"],
                "source": best[0].get("source"),
                "event_type": best[0].get("event_type"),
                "title": best[0].get("title"),
                "description": best[0].get("description"),
                "timestamp": best[0].get("timestamp"),
                "confidence": round(best[1], 4),
            }

        return {
            "incident_id": incident["id"],
            "root_cause": root_cause,
            "confidence": round(best[1], 4) if aggregated else 0.0,
            "explanation": "\n".join(explanation_parts) if explanation_parts else "No clear root cause identified.",
            "correlated_events": [
                {"id": e["id"], "source": e.get("source"), "type": e.get("event_type"),
                 "title": e.get("title"), "severity": e.get("severity"),
                 "timestamp": e.get("timestamp"), "confidence": round(s, 4)}
                for e, s in aggregated[:10]
            ],
            "propagation_impact": propagation_scores,
            "event_statistics": {
                "total_candidates": len(candidates),
                "top_source": top_source[0][0] if top_source else None,
                "top_event_type": top_type[0][0] if top_type else None,
                "sources_distribution": dict(source_counter.most_common(10)),
                "type_distribution": dict(type_counter.most_common(10)),
            },
            "recommendations": recommendations,
            "analysis_time": datetime.utcnow().isoformat(),
        }

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return next((i for i in self.incidents if i["id"] == incident_id), None)

    def list_incidents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return self.incidents[-limit - offset:len(self.incidents) - offset] if self.incidents else []

    def get_events(self, source: str = None, event_type: str = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        filtered = self.events
        if source:
            filtered = [e for e in filtered if e.get("source") == source]
        if event_type:
            filtered = [e for e in filtered if e.get("event_type") == event_type]
        return filtered[-limit:]

    def clear_events(self):
        self.events = []
        self._save_events()

    def clear_incidents(self):
        self.incidents = []
        self._save_incidents()

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_events(self, offset: int = 0, limit: int = 50, event_type: str = None,
                         source: str = None, severity: str = None) -> dict:
        results = self.events
        if event_type:
            results = [e for e in results if e.get("event_type") == event_type]
        if source:
            results = [e for e in results if e.get("source") == source]
        if severity:
            results = [e for e in results if e.get("severity") == severity]
        total = len(results)
        results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_incidents(self, offset: int = 0, limit: int = 50, source: str = None) -> dict:
        results = self.incidents
        if source:
            results = [i for i in results if i.get("source") == source]
        total = len(results)
        results.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_delete_events(self, event_ids: list[str]) -> dict:
        count = 0
        remaining = []
        for e in self.events:
            if e["id"] in event_ids:
                count += 1
            else:
                remaining.append(e)
        self.events = remaining
        self._save_events()
        return {"deleted": count, "total_requested": len(event_ids)}

    def batch_analyze_incidents(self, incident_ids: list[str]) -> list[dict]:
        results = []
        for iid in incident_ids:
            inc = self.get_incident(iid)
            if inc:
                analysis = self.analyze(incident_id=iid)
                results.append(analysis)
        return results

    def export_events(self, event_type: str = None, source: str = None) -> list[dict]:
        results = self.events
        if event_type:
            results = [e for e in results if e.get("event_type") == event_type]
        if source:
            results = [e for e in results if e.get("source") == source]
        return [{
            "id": e["id"], "event_type": e.get("event_type"), "source": e.get("source"),
            "title": e.get("title"), "description": e.get("description"),
            "severity": e.get("severity"), "timestamp": e.get("timestamp"),
            "metadata": e.get("metadata"),
        } for e in results]

    def import_events(self, events: list[dict]) -> dict:
        imported = 0
        for ev in events:
            event = {
                "id": str(uuid.uuid4()),
                "event_type": ev.get("event_type", "unknown"),
                "source": ev.get("source", "unknown"),
                "title": ev.get("title", ""),
                "description": ev.get("description", ""),
                "metadata": ev.get("metadata", {}),
                "severity": ev.get("severity", "medium"),
                "timestamp": ev.get("timestamp", datetime.utcnow().isoformat()),
                "created_at": datetime.utcnow().isoformat(),
            }
            self.events.append(event)
            imported += 1
        self._save_events()
        return {"imported": imported}

    def export_dependency_graph(self) -> dict:
        return dict(self.dependency_graph)

    def import_dependency_graph(self, graph: dict) -> dict:
        imported = 0
        for service, deps in graph.items():
            self.dependency_graph[service] = deps
            imported += 1
        self._save_dependencies()
        return {"imported": imported}

    def get_analytics(self) -> dict:
        type_dist = Counter(e.get("event_type", "unknown") for e in self.events)
        source_dist = Counter(e.get("source", "unknown") for e in self.events)
        severity_dist = Counter(e.get("severity", "unknown") for e in self.events)
        events_by_hour = {}
        for e in self.events:
            try:
                hour = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%dT%H:00:00")
                events_by_hour[hour] = events_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        avg_confidence = []
        for inc in self.incidents:
            try:
                analysis = self.analyze(incident_id=inc["id"])
                if analysis.get("root_cause"):
                    avg_confidence.append(analysis["confidence"])
            except Exception:
                pass
        return {
            "total_events": len(self.events),
            "total_incidents": len(self.incidents),
            "type_distribution": dict(type_dist),
            "source_distribution": dict(source_dist.most_common(15)),
            "severity_distribution": dict(severity_dist),
            "events_by_hour": dict(sorted(events_by_hour.items())[-24:]),
            "avg_confidence": round(statistics.mean(avg_confidence), 4) if avg_confidence else 0,
            "dependencies_count": len(self.dependency_graph),
        }

    def enrich_event(self, event_id: str, enrichment: dict) -> Optional[dict]:
        for e in self.events:
            if e["id"] == event_id:
                e.setdefault("metadata", {}).update(enrichment)
                self._save_events()
                return e
        return None

    def search_events(self, query: str) -> list[dict]:
        q = query.lower()
        return [e for e in self.events if q in e.get("title", "").lower()
                or q in e.get("description", "").lower() or q in e.get("source", "").lower()]

    def get_event_timeline(self, event_id: str) -> list[dict]:
        event = next((e for e in self.events if e["id"] == event_id), None)
        if not event:
            return []
        timeline = [{"event": "ingested", "timestamp": event.get("created_at")}]
        related = [e for e in self.events if e.get("source") == event.get("source")
                   and e["id"] != event_id]
        for rel in related[:10]:
            timeline.append({"event": "related_event", "related_id": rel["id"],
                             "type": rel.get("event_type"), "timestamp": rel.get("timestamp")})
        return sorted(timeline, key=lambda x: x.get("timestamp", ""))

    def get_top_sources(self) -> list[dict]:
        counter = Counter(e.get("source", "unknown") for e in self.events)
        return [{"source": s, "count": c} for s, c in counter.most_common(20)]

    def simulate_event_stream(self, count: int = 10, interval_sec: float = 0.5) -> list[dict]:
        import random, time
        types = [t.value for t in EventType]
        sources = ["web-server", "api-gateway", "database", "cache", "worker", "load-balancer"]
        severities = ["low", "medium", "high", "critical"]
        titles = ["CPU Spike", "Memory Pressure", "Latency Increase", "Error Rate Spike",
                  "Connection Pool Exhaustion", "Disk I/O Saturation", "Service Restart",
                  "Configuration Change", "Deployment Started", "Health Check Failure"]
        generated = []
        for _ in range(count):
            event = self.ingest_event(
                event_type=random.choice(types),
                source=random.choice(sources),
                title=random.choice(titles),
                description=f"Simulated {random.choice(types)} event at {datetime.utcnow().isoformat()}",
                severity=random.choice(severities),
                metadata={
                    "simulation": True,
                    "run_id": str(uuid.uuid4())[:8],
                    "value": random.uniform(0, 100),
                    "threshold": 80,
                },
            )
            generated.append(event)
            time.sleep(interval_sec)
        return generated

    # ===== APPENDED BATCH 2: State machine, routing, reports, SLO, dedup, escalation =====

    def _event_lifecycle_state(self, event_id: str) -> Optional[dict]:
        for e in self.events:
            if e["id"] == event_id:
                state = {"id": e["id"], "status": "active", "type": e.get("event_type")}
                related = [x for x in self.events if x.get("source") == e.get("source") and x["id"] != event_id]
                state["related_events"] = len(related)
                state["severity"] = e.get("severity", "unknown")
                return state
        return None

    def batch_analyze_events(self, event_ids: list[str]) -> list[dict]:
        results = []
        for eid in event_ids:
            event = next((e for e in self.events if e["id"] == eid), None)
            if event:
                analysis = self.analyze(
                    incident_title=event.get("title"),
                    incident_description=event.get("description"),
                    incident_source=event.get("source"),
                    incident_time=event.get("timestamp"),
                )
                results.append(analysis)
        return results

    def get_event_clusters(self, time_window_minutes: int = 10) -> list[dict]:
        sorted_events = sorted(self.events, key=lambda e: e.get("timestamp", ""))
        clusters = []
        used = set()
        for i, e in enumerate(sorted_events):
            if i in used:
                continue
            cluster = [e]
            used.add(i)
            try:
                base = datetime.fromisoformat(e["timestamp"])
            except (ValueError, TypeError):
                continue
            for j in range(i + 1, min(i + 50, len(sorted_events))):
                if j in used:
                    continue
                try:
                    other_ts = datetime.fromisoformat(sorted_events[j]["timestamp"])
                except (ValueError, TypeError):
                    continue
                if abs((other_ts - base).total_seconds()) <= time_window_minutes * 60:
                    cluster.append(sorted_events[j])
                    used.add(j)
            if len(cluster) > 1:
                sources = list(set(c.get("source", "") for c in cluster))
                types = list(set(c.get("event_type", "") for c in cluster))
                clusters.append({
                    "size": len(cluster),
                    "sources": sources,
                    "types": types,
                    "time_window_minutes": time_window_minutes,
                    "first_event": min(c.get("timestamp", "") for c in cluster),
                    "last_event": max(c.get("timestamp", "") for c in cluster),
                })
        return clusters

    def check_anomaly(self, source: str, event_type: str = None) -> dict:
        filtered = [e for e in self.events if e.get("source") == source]
        if event_type:
            filtered = [e for e in filtered if e.get("event_type") == event_type]
        if len(filtered) < 5:
            return {"source": source, "anomaly_detected": False, "reason": "insufficient_data"}
        hourly = Counter()
        for e in filtered:
            try:
                h = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%dT%H:00:00")
                hourly[h] += 1
            except (ValueError, TypeError):
                pass
        values = list(hourly.values())
        avg = statistics.mean(values) if values else 0
        stdev = statistics.stdev(values) if len(values) > 1 else 0.001
        current_count = values[-1] if values else 0
        z_score = (current_count - avg) / stdev if stdev > 0 else 0
        threshold = 2.0
        return {
            "source": source,
            "event_type": event_type or "all",
            "anomaly_detected": z_score > threshold,
            "z_score": round(z_score, 4),
            "current_rate": current_count,
            "avg_rate": round(avg, 2),
            "threshold": threshold,
            "severity": "high" if z_score > 3 else "medium" if z_score > 2 else "low",
        }

    def merge_incidents(self, incident_ids: list[str]) -> Optional[dict]:
        incidents = [self.get_incident(iid) for iid in incident_ids]
        incidents = [i for i in incidents if i]
        if len(incidents) < 2:
            return None
        merged = dict(incidents[0])
        merged["id"] = str(uuid.uuid4())
        merged["title"] = f"Merged: {' + '.join(i['id'][:8] for i in incidents)}"
        all_alerts = []
        for inc in incidents:
            all_alerts.extend(inc.get("alerts", []))
            inc["status"] = "merged"
        merged["alerts"] = list(set(all_alerts))
        merged["alert_count"] = len(merged["alerts"])
        merged["merged_from"] = incident_ids
        merged["created_at"] = datetime.utcnow().isoformat()
        self.incidents.append(merged)
        self._save_incidents()
        return merged

    def export_full_state(self) -> dict:
        return {
            "events_count": len(self.events),
            "incidents_count": len(self.incidents),
            "dependencies": dict(self.dependency_graph),
            "analytics": self.get_analytics(),
        }

    def import_full_state(self, state: dict) -> dict:
        imported = 0
        for service, deps in state.get("dependencies", {}).items():
            self.dependency_graph[service] = deps
            imported += 1
        self._save_dependencies()
        return {"dependencies_imported": imported}

    def generate_report(self, hours: int = 48) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [e for e in self.events if datetime.fromisoformat(e["timestamp"]) > cutoff]
        recent_incidents = [i for i in self.incidents if datetime.fromisoformat(i["created_at"]) > cutoff]
        by_type = Counter(e.get("event_type", "unknown") for e in recent_events)
        by_source = Counter(e.get("source", "unknown") for e in recent_events)
        root_causes = []
        for inc in recent_incidents[:10]:
            a = self.analyze(incident_id=inc["id"])
            if a.get("root_cause"):
                root_causes.append(a["root_cause"])
        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "total_incidents": len(recent_incidents),
            "event_type_distribution": dict(by_type),
            "top_sources": dict(by_source.most_common(10)),
            "root_causes_found": len(root_causes),
            "sample_root_causes": root_causes[:5],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def route_event_to_analyzer(self, event_id: str, analyzer: str) -> Optional[dict]:
        for e in self.events:
            if e["id"] == event_id:
                e.setdefault("routing", {})
                e["routing"]["assigned_analyzer"] = analyzer
                e["routing"]["routed_at"] = datetime.utcnow().isoformat()
                self._save_events()
                return e
        return None

    def get_incident_similarity(self, incident_id_a: str, incident_id_b: str) -> dict:
        ia = self.get_incident(incident_id_a)
        ib = self.get_incident(incident_id_b)
        if not ia or not ib:
            return {"error": "One or both incidents not found"}
        words_a = set(f"{ia.get('title', '')} {ia.get('description', '')}".lower().split())
        words_b = set(f"{ib.get('title', '')} {ib.get('description', '')}".lower().split())
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return {
            "incident_a": incident_id_a,
            "incident_b": incident_id_b,
            "similarity_score": round(overlap, 4),
            "recommendation": "merge" if overlap > 0.5 else "keep_separate",
        }

    def check_slo_compliance(self, target_pct: float = 99.5, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        critical_events = [e for e in self.events if e.get("severity") in ("critical", "high")
                           and datetime.fromisoformat(e["timestamp"]) > cutoff]
        total_minutes = window_hours * 60
        impact_minutes = len(critical_events)
        effective = max(0, total_minutes - impact_minutes)
        actual_pct = round((effective / total_minutes) * 100, 4) if total_minutes > 0 else 100.0
        return {
            "slo_target_pct": target_pct,
            "actual_pct": actual_pct,
            "compliant": actual_pct >= target_pct,
            "window_hours": window_hours,
            "impactful_events": impact_minutes,
        }

    def get_top_event_types(self, limit: int = 10) -> list[dict]:
        counter = Counter(e.get("event_type", "unknown") for e in self.events)
        return [{"event_type": et, "count": c} for et, c in counter.most_common(limit)]

    def get_top_sources(self, limit: int = 10) -> list[dict]:
        counter = Counter(e.get("source", "unknown") for e in self.events)
        return [{"source": s, "count": c} for s, c in counter.most_common(limit)]

    def get_event_timeline(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [e for e in self.events if datetime.fromisoformat(e["timestamp"]) > cutoff]
        hourly: dict[str, int] = defaultdict(int)
        for e in recent:
            try:
                hour = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%dT%H:00")
                hourly[hour] += 1
            except (ValueError, TypeError):
                pass
        return [{"hour": h, "count": c} for h, c in sorted(hourly.items())]

    def find_correlation_patterns(self) -> list[dict]:
        patterns = []
        for inc in self.incidents:
            alerts = inc.get("alerts", [])
            if len(alerts) >= 3:
                event_types = [a.get("event_type", "") for a in alerts]
                common = Counter(event_types).most_common(3)
                patterns.append({"incident_id": inc["id"], "title": inc.get("title"), "common_event_types": [{"type": t, "count": c} for t, c in common], "total_alerts": len(alerts)})
        return patterns

    def get_affected_services(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_incidents = [i for i in self.incidents if datetime.fromisoformat(i["created_at"]) > cutoff]
        service_count: dict[str, int] = defaultdict(int)
        for inc in recent_incidents:
            for alert in inc.get("alerts", []):
                svc = alert.get("service", "unknown")
                service_count[svc] += 1
        return [{"service": svc, "incidents_involved": cnt} for svc, cnt in sorted(service_count.items(), key=lambda x: x[1], reverse=True)]

    def suggest_auto_remediation(self, incident_id: str) -> list[dict]:
        inc = self.get_incident(incident_id)
        if not inc:
            return []
        root_cause = self.analyze(incident_id=incident_id)
        suggestions = []
        rc = root_cause.get("root_cause", {})
        event_type = rc.get("event_type", "")
        if "timeout" in event_type or "latency" in event_type:
            suggestions.append({"action": "Increase timeout limits", "confidence": 0.7, "type": "config_change"})
            suggestions.append({"action": "Scale up affected service", "confidence": 0.6, "type": "scaling"})
        if "error" in event_type or "exception" in event_type:
            suggestions.append({"action": "Restart service", "confidence": 0.8, "type": "restart"})
            suggestions.append({"action": "Rollback last deployment", "confidence": 0.5, "type": "rollback"})
        if "disk" in event_type or "storage" in event_type:
            suggestions.append({"action": "Increase disk capacity", "confidence": 0.75, "type": "scaling"})
            suggestions.append({"action": "Run cleanup job", "confidence": 0.9, "type": "maintenance"})
        return suggestions


class EventImpactScorer:
    def __init__(self, engine: RootCauseAnalysisEngine):
        self.engine = engine

    def score_event(self, event_id: str) -> dict:
        event = next((e for e in self.engine.events if e["id"] == event_id), None)
        if not event:
            return {"error": "Event not found"}
        severity_scores = {"critical": 10, "high": 7, "medium": 4, "low": 1}
        severity = event.get("severity", "low").lower()
        base = severity_scores.get(severity, 1)
        related_incidents = [i for i in self.engine.incidents if event_id in [a.get("id") for a in i.get("alerts", [])]]
        impact_multiplier = min(1 + len(related_incidents) * 0.5, 5)
        services_affected = len(set(a.get("service", "") for i in related_incidents for a in i.get("alerts", [])))
        return {"event_id": event_id, "event_type": event.get("event_type"), "severity": severity, "base_score": base, "impact_multiplier": impact_multiplier, "services_affected": services_affected, "total_score": round(base * impact_multiplier, 1), "priority": "critical" if base * impact_multiplier > 20 else "high" if base * impact_multiplier > 10 else "medium"}

    def get_high_impact_events(self, limit: int = 10) -> list[dict]:
        scored = [self.score_event(e["id"]) for e in self.engine.events]
        scored = [s for s in scored if "error" not in s]
        return sorted(scored, key=lambda x: x["total_score"], reverse=True)[:limit]

    def get_impact_summary(self, hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [e for e in self.engine.events if datetime.fromisoformat(e["timestamp"]) > cutoff]
        scored = [self.score_event(e["id"]) for e in recent]
        scored = [s for s in scored if "error" not in s]
        total_impact = sum(s["total_score"] for s in scored)
        return {"period_hours": hours, "total_events": len(scored), "total_impact_score": round(total_impact, 1), "avg_impact": round(total_impact / max(len(scored), 1), 1), "critical_count": sum(1 for s in scored if s.get("priority") == "critical")}

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
