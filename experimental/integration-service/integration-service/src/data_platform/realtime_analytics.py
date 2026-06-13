"""Real-Time Analytics Dashboard — live streaming dashboards for operational metrics."""

from __future__ import annotations
import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    RATE = "rate"


class AlertCondition(Enum):
    ABOVE = "above"
    BELOW = "below"
    EQUAL = "equal"
    CHANGE_PERCENT = "change_percent"


class DashboardRefresh(Enum):
    REALTIME = 0
    SEC_1 = 1
    SEC_5 = 5
    SEC_10 = 10
    SEC_30 = 30
    MIN_1 = 60


@dataclass
class MetricDefinition:
    metric_id: str
    name: str
    metric_type: MetricType
    unit: str
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    aggregation: str = "avg"


@dataclass
class AlertRule:
    alert_id: str
    name: str
    metric_id: str
    condition: AlertCondition
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    cooldown_seconds: int = 300
    last_triggered: str = ""


@dataclass
class DashboardPanel:
    panel_id: str
    title: str
    metric_ids: list[str]
    chart_type: str
    width: int = 6
    height: int = 4
    refresh: int = 5
    alert_overlay: bool = True


@dataclass
class LiveDashboard:
    dashboard_id: str
    name: str
    description: str
    panels: list[DashboardPanel] = field(default_factory=list)
    refresh: DashboardRefresh = DashboardRefresh.SEC_5
    created_at: str = ""
    created_by: str = ""


@dataclass
class DataPoint:
    timestamp: str
    metric_id: str
    value: float
    tags: dict = field(default_factory=dict)


_metrics: dict[str, MetricDefinition] = {}
_alerts: dict[str, AlertRule] = {}
_dashboards: dict[str, LiveDashboard] = {}
_subscribers: dict[str, list[Callable]] = {}
_realtime_buffer: list[DataPoint] = []


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _current_ms() -> int:
    return int(datetime.utcnow().timestamp() * 1000)


async def register_metric(name: str, metric_type: MetricType, unit: str, description: str = "", aggregation: str = "avg") -> MetricDefinition:
    metric = MetricDefinition(
        metric_id=str(uuid4()),
        name=name,
        metric_type=metric_type,
        unit=unit,
        description=description,
        aggregation=aggregation,
    )
    _metrics[metric.metric_id] = metric
    return metric


async def list_metrics() -> list[MetricDefinition]:
    return list(_metrics.values())


async def get_metric(metric_id: str) -> Optional[MetricDefinition]:
    return _metrics.get(metric_id)


async def ingest_metric(metric_id: str, value: float, tags: dict | None = None) -> dict:
    metric = _metrics.get(metric_id)
    if not metric:
        raise ValueError(f"Metric {metric_id} not found")
    dp = DataPoint(timestamp=_ts(), metric_id=metric_id, value=value, tags=tags or {})
    _realtime_buffer.append(dp)
    if len(_realtime_buffer) > 10000:
        _realtime_buffer[:5000] = []
    for cb in _subscribers.get(metric_id, []):
        try:
            cb(dp)
        except Exception:
            pass
    for alert in _alerts.values():
        if alert.metric_id == metric_id and alert.enabled:
            _evaluate_alert(alert, value)
    return {"metric_id": metric_id, "value": value, "timestamp": dp.timestamp}


async def subscribe(metric_id: str, callback: Callable) -> bool:
    _subscribers.setdefault(metric_id, []).append(callback)
    return True


async def unsubscribe(metric_id: str, callback: Callable) -> bool:
    subs = _subscribers.get(metric_id, [])
    if callback in subs:
        subs.remove(callback)
        return True
    return False


def _evaluate_alert(alert: AlertRule, value: float) -> None:
    triggered = False
    if alert.condition == AlertCondition.ABOVE and value > alert.threshold:
        triggered = True
    elif alert.condition == AlertCondition.BELOW and value < alert.threshold:
        triggered = True
    elif alert.condition == AlertCondition.EQUAL and value == alert.threshold:
        triggered = True
    if triggered:
        alert.last_triggered = _ts()
        logger.warning("Alert triggered: %s (value=%.2f, threshold=%.2f)", alert.name, value, alert.threshold)


async def create_alert_rule(
    name: str,
    metric_id: str,
    condition: AlertCondition,
    threshold: float,
    severity: str = "warning",
    cooldown_seconds: int = 300,
) -> AlertRule:
    alert = AlertRule(
        alert_id=str(uuid4()),
        name=name,
        metric_id=metric_id,
        condition=condition,
        threshold=threshold,
        severity=severity,
        cooldown_seconds=cooldown_seconds,
    )
    _alerts[alert.alert_id] = alert
    return alert


async def list_alert_rules() -> list[AlertRule]:
    return list(_alerts.values())


async def update_alert_rule(alert_id: str, **kwargs) -> Optional[AlertRule]:
    a = _alerts.get(alert_id)
    if not a:
        return None
    for k, v in kwargs.items():
        if hasattr(a, k):
            setattr(a, k, v)
    return a


async def delete_alert_rule(alert_id: str) -> bool:
    return _alerts.pop(alert_id, None) is not None


async def create_dashboard(name: str, description: str = "", refresh: DashboardRefresh = DashboardRefresh.SEC_5, created_by: str = "") -> LiveDashboard:
    db = LiveDashboard(
        dashboard_id=str(uuid4()),
        name=name,
        description=description,
        refresh=refresh,
        created_at=_ts(),
        created_by=created_by,
    )
    _dashboards[db.dashboard_id] = db
    return db


async def list_dashboards() -> list[LiveDashboard]:
    return list(_dashboards.values())


async def get_dashboard(dashboard_id: str) -> Optional[LiveDashboard]:
    return _dashboards.get(dashboard_id)


async def delete_dashboard(dashboard_id: str) -> bool:
    return _dashboards.pop(dashboard_id, None) is not None


async def add_panel(
    dashboard_id: str,
    title: str,
    metric_ids: list[str],
    chart_type: str = "line",
    width: int = 6,
    height: int = 4,
    refresh: int = 5,
) -> Optional[DashboardPanel]:
    db = _dashboards.get(dashboard_id)
    if not db:
        return None
    panel = DashboardPanel(
        panel_id=str(uuid4()),
        title=title,
        metric_ids=metric_ids,
        chart_type=chart_type,
        width=width,
        height=height,
        refresh=refresh,
    )
    db.panels.append(panel)
    return panel


async def remove_panel(dashboard_id: str, panel_id: str) -> bool:
    db = _dashboards.get(dashboard_id)
    if not db:
        return False
    before = len(db.panels)
    db.panels = [p for p in db.panels if p.panel_id != panel_id]
    return len(db.panels) < before


async def get_live_data(dashboard_id: str) -> dict:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    panel_data = {}
    for panel in db.panels:
        data = {}
        for mid in panel.metric_ids:
            points = [dp for dp in _realtime_buffer if dp.metric_id == mid][-50:]
            data[mid] = [{"t": p.timestamp, "v": p.value} for p in points]
        panel_data[panel.panel_id] = {"title": panel.title, "data": data}
    return {"dashboard_id": dashboard_id, "panels": panel_data, "ts": _current_ms()}


async def get_metric_history(metric_id: str, duration_seconds: int = 300) -> list[dict]:
    cutoff = datetime.utcnow().timestamp() - duration_seconds
    return [
        {"t": p.timestamp, "v": p.value}
        for p in _realtime_buffer
        if p.metric_id == metric_id and datetime.fromisoformat(p.timestamp.replace("Z", "+00:00")).timestamp() > cutoff
    ]


async def drill_down(metric_id: str, tags: dict[str, str] | None = None) -> list[dict]:
    points = [dp for dp in _realtime_buffer if dp.metric_id == metric_id]
    if tags:
        points = [dp for dp in points if all(dp.tags.get(k) == v for k, v in tags.items())]
    return [{"t": p.timestamp, "v": p.value, "tags": p.tags} for p in points[-100:]]


async def get_realtime_stats() -> dict:
    return {
        "metrics": len(_metrics),
        "alerts": len(_alerts),
        "dashboards": len(_dashboards),
        "buffer_size": len(_realtime_buffer),
        "subscribers": sum(len(s) for s in _subscribers.values()),
    }


async def simulate_stream(dashboard_id: str, interval_sec: float = 1.0, count: int = 10) -> list[dict]:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    generated = []
    for _ in range(count):
        for panel in db.panels:
            for mid in panel.metric_ids:
                val = round(random.uniform(0, 100), 1)
                await ingest_metric(mid, val, {"panel": panel.panel_id, "source": "simulation"})
                generated.append({"metric_id": mid, "value": val, "panel_id": panel.panel_id})
        await asyncio.sleep(interval_sec)
    return generated


async def update_dashboard(dashboard_id: str, **kwargs) -> Optional[LiveDashboard]:
    db = _dashboards.get(dashboard_id)
    if not db:
        return None
    for k, v in kwargs.items():
        if hasattr(db, k):
            setattr(db, k, v)
    return db


async def update_panel(dashboard_id: str, panel_id: str, **kwargs) -> Optional[DashboardPanel]:
    db = _dashboards.get(dashboard_id)
    if not db:
        return None
    for p in db.panels:
        if p.panel_id == panel_id:
            for k, v in kwargs.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            return p
    return None


async def aggregate_metric(metric_id: str, window_seconds: int = 60, agg: str = "avg") -> dict:
    points = [dp for dp in _realtime_buffer if dp.metric_id == metric_id]
    cutoff = datetime.utcnow().timestamp() - window_seconds
    windowed = [p for p in points if datetime.fromisoformat(p.timestamp.replace("Z", "+00:00")).timestamp() > cutoff]
    if not windowed:
        return {"metric_id": metric_id, "value": 0, "count": 0}
    values = [p.value for p in windowed]
    if agg == "avg":
        result = sum(values) / len(values)
    elif agg == "sum":
        result = sum(values)
    elif agg == "max":
        result = max(values)
    elif agg == "min":
        result = min(values)
    else:
        result = sum(values) / len(values)
    return {"metric_id": metric_id, f"{agg}_value": round(result, 2), "count": len(values), "window_seconds": window_seconds}


async def clear_buffer() -> dict:
    global _realtime_buffer
    count = len(_realtime_buffer)
    _realtime_buffer = []
    return {"cleared": count}


async def get_dashboard_share_url(dashboard_id: str) -> str:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    return f"/shared/dashboards/{dashboard_id}"


async def list_chart_types() -> list[str]:
    return ["line", "bar", "area", "pie", "scatter", "heatmap", "gauge", "stat"]


async def duplicate_dashboard(dashboard_id: str, new_name: str) -> Optional[LiveDashboard]:
    original = _dashboards.get(dashboard_id)
    if not original:
        return None
    db = LiveDashboard(
        dashboard_id=str(uuid4()),
        name=new_name,
        description=f"Copy of {original.name}",
        panels=[],
        refresh=original.refresh,
        created_at=_ts(),
    )
    for p in original.panels:
        db.panels.append(DashboardPanel(
            panel_id=str(uuid4()),
            title=p.title,
            metric_ids=list(p.metric_ids),
            chart_type=p.chart_type,
            width=p.width,
            height=p.height,
            refresh=p.refresh,
        ))
    _dashboards[db.dashboard_id] = db
    return db


async def get_alert_history(metric_id: str) -> list[AlertRule]:
    return [a for a in _alerts.values() if a.metric_id == metric_id]


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class RealtimeBatchOperation:
    batch_id: str
    operation: str
    item_ids: list[str]
    status: str = "pending"
    success_count: int = 0
    failure_count: int = 0
    errors: list[dict] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""


@dataclass
class RealtimePaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    metric_type_filter: str | None = None


@dataclass
class RealtimePaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class DashboardStateTransition:
    from_state: str
    to_state: str
    trigger: str
    dashboard_id: str
    timestamp: str = ""
    actor: str = "system"


_realtime_batch_ops: dict[str, RealtimeBatchOperation] = {}
_dashboard_state_history: dict[str, list[DashboardStateTransition]] = {}
_dashboard_share_tokens: dict[str, str] = {}


async def paginate_metrics(params: RealtimePaginationParams | None = None) -> RealtimePaginatedResult:
    p = params or RealtimePaginationParams()
    results = list(_metrics.values())
    if p.metric_type_filter:
        results = [m for m in results if m.metric_type.value == p.metric_type_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda m: m.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "metric_type":
        results.sort(key=lambda m: m.metric_type.value, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return RealtimePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def paginate_dashboards(params: RealtimePaginationParams | None = None) -> RealtimePaginatedResult:
    p = params or RealtimePaginationParams()
    results = list(_dashboards.values())
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda d: d.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda d: d.created_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return RealtimePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def paginate_alerts(params: RealtimePaginationParams | None = None) -> RealtimePaginatedResult:
    p = params or RealtimePaginationParams()
    results = list(_alerts.values())
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda a: a.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "severity":
        results.sort(key=lambda a: a.severity, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return RealtimePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def batch_ingest_metrics(data: list[dict]) -> RealtimeBatchOperation:
    op = RealtimeBatchOperation(batch_id=str(uuid4()), operation="ingest", item_ids=[], created_at=_ts())
    for d in data:
        try:
            result = await ingest_metric(d["metric_id"], d["value"], d.get("tags"))
            op.item_ids.append(result["metric_id"])
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"metric_id": d.get("metric_id"), "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _realtime_batch_ops[op.batch_id] = op
    return op


async def batch_enable_alerts(alert_ids: list[str], enabled: bool) -> RealtimeBatchOperation:
    op = RealtimeBatchOperation(batch_id=str(uuid4()), operation="toggle_alerts", item_ids=[], created_at=_ts())
    for aid in alert_ids:
        a = _alerts.get(aid)
        if a:
            a.enabled = enabled
            op.item_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"alert_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _realtime_batch_ops[op.batch_id] = op
    return op


async def batch_delete_alerts(alert_ids: list[str]) -> RealtimeBatchOperation:
    op = RealtimeBatchOperation(batch_id=str(uuid4()), operation="delete_alerts", item_ids=[], created_at=_ts())
    for aid in alert_ids:
        if _alerts.pop(aid, None):
            op.item_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"alert_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _realtime_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[RealtimeBatchOperation]:
    return _realtime_batch_ops.get(batch_id)


async def export_dashboard(dashboard_id: str) -> dict:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    return {
        "name": db.name, "description": db.description, "refresh": db.refresh.value,
        "panels": [{"title": p.title, "metric_ids": p.metric_ids, "chart_type": p.chart_type,
                      "width": p.width, "height": p.height, "refresh": p.refresh} for p in db.panels],
        "exported_at": _ts(),
    }


async def import_dashboard(data: dict) -> LiveDashboard:
    db = await create_dashboard(data["name"], data.get("description", ""),
                                 DashboardRefresh(data.get("refresh", 5)), data.get("created_by", ""))
    for pd in data.get("panels", []):
        await add_panel(db.dashboard_id, pd["title"], pd.get("metric_ids", []),
                         pd.get("chart_type", "line"), pd.get("width", 6), pd.get("height", 4), pd.get("refresh", 5))
    return db


async def get_realtime_analytics_summary() -> dict:
    total_metrics = len(_metrics)
    total_alert_rules = len(_alerts)
    total_dashboards = len(_dashboards)
    buffer_size = len(_realtime_buffer)
    by_type = {}
    for m in _metrics.values():
        by_type[m.metric_type.value] = by_type.get(m.metric_type.value, 0) + 1
    triggered_alerts = sum(1 for a in _alerts.values() if a.last_triggered)
    return {
        "total_metrics": total_metrics,
        "total_alert_rules": total_alert_rules,
        "total_dashboards": total_dashboards,
        "buffer_size": buffer_size,
        "metrics_by_type": by_type,
        "enabled_alerts": sum(1 for a in _alerts.values() if a.enabled),
        "triggered_alerts": triggered_alerts,
        "subscribers_total": sum(len(s) for s in _subscribers.values()),
        "avg_buffer_per_metric": buffer_size // max(total_metrics, 1),
    }


async def get_metric_analytics(metric_id: str) -> dict:
    metric = _metrics.get(metric_id)
    if not metric:
        raise ValueError(f"Metric {metric_id} not found")
    points = [dp for dp in _realtime_buffer if dp.metric_id == metric_id]
    values = [p.value for p in points]
    if not values:
        return {"metric_id": metric_id, "data_points": 0, "avg": 0, "min": 0, "max": 0}
    return {
        "metric_id": metric_id,
        "name": metric.name,
        "type": metric.metric_type.value,
        "data_points": len(values),
        "avg": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values),
        "latest": values[-1],
        "unit": metric.unit,
    }


async def transition_dashboard_state(dashboard_id: str, trigger: str, actor: str = "system") -> dict:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    from_state = "active" if db.created_at else "draft"
    valid_transitions = {
        "draft": {"publish", "archive"},
        "active": {"archive", "disable"},
        "archived": {"restore"},
        "disabled": {"enable", "archive"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"dashboard_id": dashboard_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {"publish": "active", "archive": "archived", "disable": "disabled", "restore": "active", "enable": "active"}
    to_state = to_state_map.get(trigger, from_state)
    transition = DashboardStateTransition(from_state=from_state, to_state=to_state, trigger=trigger,
                                           dashboard_id=dashboard_id, timestamp=_ts(), actor=actor)
    _dashboard_state_history.setdefault(dashboard_id, []).append(transition)
    return {"dashboard_id": dashboard_id, "success": True, "from_state": from_state, "to_state": to_state}


async def get_dashboard_state_history(dashboard_id: str) -> list[DashboardStateTransition]:
    return _dashboard_state_history.get(dashboard_id, [])


async def validate_alert_rule_config(config: dict) -> dict:
    issues = []
    if "name" not in config or not config["name"]:
        issues.append("Alert rule name is required")
    if "metric_id" not in config:
        issues.append("Metric ID is required")
    elif config["metric_id"] not in _metrics:
        issues.append(f"Metric {config.get('metric_id')} not found")
    if "condition" in config and config["condition"] not in [c.value for c in AlertCondition]:
        issues.append(f"Invalid condition: {config.get('condition')}")
    if "threshold" in config and not isinstance(config["threshold"], (int, float)):
        issues.append("Threshold must be a number")
    if "severity" in config and config["severity"] not in ("info", "warning", "critical"):
        issues.append("Severity must be info, warning, or critical")
    return {"valid": len(issues) == 0, "issues": issues}


async def search_dashboards(query: str) -> list[LiveDashboard]:
    q = query.lower()
    return [d for d in _dashboards.values() if q in d.name.lower() or q in d.description.lower()]


async def get_dashboard_insights(dashboard_id: str) -> dict:
    db = _dashboards.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    all_metric_ids = set()
    for p in db.panels:
        all_metric_ids.update(p.metric_ids)
    panel_count = len(db.panels)
    metric_count = len(all_metric_ids)
    return {
        "dashboard_id": dashboard_id,
        "name": db.name,
        "panels": panel_count,
        "unique_metrics": metric_count,
        "refresh_seconds": db.refresh.value,
        "alerts_configured": sum(1 for a in _alerts.values() if a.metric_id in all_metric_ids),
        "data_points_available": sum(1 for dp in _realtime_buffer if dp.metric_id in all_metric_ids),
    }


async def set_dashboard_share_token(dashboard_id: str, token: str) -> bool:
    _dashboard_share_tokens[dashboard_id] = token
    return True


async def get_dashboard_by_share_token(token: str) -> Optional[LiveDashboard]:
    for did, t in _dashboard_share_tokens.items():
        if t == token:
            return _dashboards.get(did)
    return None


async def bulk_update_dashboard_refresh(dashboard_ids: list[str], refresh: DashboardRefresh) -> RealtimeBatchOperation:
    op = RealtimeBatchOperation(batch_id=str(uuid4()), operation="update_refresh", item_ids=[], created_at=_ts())
    for did in dashboard_ids:
        db = _dashboards.get(did)
        if db:
            db.refresh = refresh
            op.item_ids.append(did)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"dashboard_id": did, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _realtime_batch_ops[op.batch_id] = op
    return op


class RealtimeMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class RealtimeCache:
    def __init__(self, ttl: int = 30):
        self._store: dict[str, dict] = {}
        self._ttl = ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry:
            age = (datetime.utcnow() - entry["ts"]).total_seconds()
            if age < self._ttl:
                return entry["val"]
        return None

    def set(self, key: str, val: Any):
        self._store[key] = {"val": val, "ts": datetime.utcnow()}

    def invalidate(self, key: str):
        self._store.pop(key, None)


class RealtimeAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, detail: str = "") -> dict:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_realtime_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    results = []
    for db in _dashboards.values():
        if query.lower() in db.name.lower():
            results.append({"dashboard_id": db.dashboard_id, "name": db.name, "refresh": db.refresh.value})
            if len(results) >= limit:
                break
    return results


async def recommend_dashboard_cleanup(days_threshold: int = 180) -> list[dict]:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    stale = []
    for db in _dashboards.values():
        created = datetime.fromisoformat(db.created_at.replace("Z", "+00:00"))
        if created < cutoff:
            stale.append({"dashboard_id": db.dashboard_id, "name": db.name, "created": db.created_at})
    return stale


async def merge_realtime_entities(dashboard_ids: list[str]) -> LiveDashboard:
    target_id = dashboard_ids[0]
    target = _dashboards.get(target_id)
    if not target:
        raise ValueError(f"Dashboard {target_id} not found")
    for did in dashboard_ids[1:]:
        source = _dashboards.get(did)
        if source:
            for p in source.panels:
                if not any(ex.name == p.name for ex in target.panels):
                    target.panels.append(p)
            del _dashboards[did]
    return target

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
        return {"total_records": 0, "processed": 0, "failed": 0, "throughput": 0.0}

    def validate_pipeline(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class DataOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    record_id: Optional[str] = None
    records_affected: int = Field(default=0)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    pipeline: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_success(self) -> None:
        self.processed += 1

    def record_failure(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"

class DataQualityMetric(BaseModel):
    dataset: str
    metric_name: str
    value: float
    threshold: float
    passed: bool
    checked_at: datetime = Field(default_factory=datetime.utcnow)

class DataQualityChecker:
    def __init__(self) -> None:
        self._checks: List[DataQualityMetric] = []

    def check_completeness(self, dataset: str, total: int, non_null: int, threshold: float = 0.95) -> DataQualityMetric:
        rate = non_null / max(total, 1)
        metric = DataQualityMetric(dataset=dataset, metric_name="completeness",
                                    value=round(rate, 4), threshold=threshold, passed=rate >= threshold)
        self._checks.append(metric)
        return metric

    def check_uniqueness(self, dataset: str, total: int, unique: int, threshold: float = 0.9) -> DataQualityMetric:
        rate = unique / max(total, 1)
        metric = DataQualityMetric(dataset=dataset, metric_name="uniqueness",
                                    value=round(rate, 4), threshold=threshold, passed=rate >= threshold)
        self._checks.append(metric)
        return metric

    def check_timeliness(self, dataset: str, max_age_hours: float, threshold_hours: float = 24) -> DataQualityMetric:
        passed = max_age_hours <= threshold_hours
        metric = DataQualityMetric(dataset=dataset, metric_name="timeliness",
                                    value=round(max_age_hours, 2), threshold=threshold_hours, passed=passed)
        self._checks.append(metric)
        return metric

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._checks)
        passed = sum(1 for c in self._checks if c.passed)
        return {"total_checks": total, "passed": passed, "failed": total - passed,
                "pass_rate": round(passed / max(total, 1) * 100, 1)}

class DataLineageEntry(BaseModel):
    source: str
    target: str
    transformation: str = ""
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    records_moved: int = Field(default=0)
    success: bool = True

class DataLineageTracker:
    def __init__(self) -> None:
        self._entries: List[DataLineageEntry] = []

    def record(self, source: str, target: str, transformation: str = "", records: int = 0, success: bool = True) -> None:
        self._entries.append(DataLineageEntry(source=source, target=target,
                                               transformation=transformation,
                                               records_moved=records, success=success))

    def get_upstream(self, target: str) -> List[DataLineageEntry]:
        return [e for e in self._entries if e.target == target]

    def get_downstream(self, source: str) -> List[DataLineageEntry]:
        return [e for e in self._entries if e.source == source]

    def get_lineage(self, dataset: str) -> Dict[str, Any]:
        return {"upstream": [e.dict() for e in self.get_upstream(dataset)],
                "downstream": [e.dict() for e in self.get_downstream(dataset)]}

class PipelineSchedule(BaseModel):
    pipeline_name: str
    cron_expression: str = Field(default="0 */6 * * *")
    enabled: bool = True
    max_retries: int = Field(default=3)
    timeout_minutes: int = Field(default=60)
    notification_email: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class PipelineScheduler:
    def __init__(self) -> None:
        self._schedules: Dict[str, PipelineSchedule] = {}

    def register(self, schedule: PipelineSchedule) -> None:
        self._schedules[schedule.pipeline_name] = schedule

    def enable(self, pipeline_name: str) -> bool:
        if pipeline_name in self._schedules:
            self._schedules[pipeline_name].enabled = True
            return True
        return False

    def disable(self, pipeline_name: str) -> bool:
        if pipeline_name in self._schedules:
            self._schedules[pipeline_name].enabled = False
            return True
        return False

    def get_schedule(self, pipeline_name: str) -> Optional[PipelineSchedule]:
        return self._schedules.get(pipeline_name)

    def list_active(self) -> List[PipelineSchedule]:
        return [s for s in self._schedules.values() if s.enabled]

class SchemaField(BaseModel):
    name: str
    field_type: str
    nullable: bool = True
    description: str = ""
    default_value: Optional[Any] = None
    constraints: List[str] = Field(default_factory=list)

class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: Dict[str, List[SchemaField]] = {}

    def register(self, name: str, fields: List[SchemaField]) -> None:
        self._schemas[name] = fields

    def get(self, name: str) -> Optional[List[SchemaField]]:
        return self._schemas.get(name)

    def validate_record(self, schema_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        fields = self._schemas.get(schema_name)
        if not fields:
            return {"valid": False, "errors": ["Schema not found"]}
        errors = []
        for field in fields:
            if field.name not in record and not field.nullable:
                errors.append(f"Missing required field: {field.name}")
            if field.name in record and record[field.name] is None and not field.nullable:
                errors.append(f"Field {field.name} is null but not nullable")
        return {"valid": len(errors) == 0, "errors": errors}

    def list_schemas(self) -> List[str]:
        return list(self._schemas.keys())
