"""Cog: Real-Time Analytics Dashboard — live streaming dashboards for operational metrics."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

DASHBOARDS: dict[str, dict] = {}


async def create_dashboard(name: str, description: str = "") -> dict:
    did = f"db-{len(DASHBOARDS) + 1}"
    DASHBOARDS[did] = {"dashboard_id": did, "name": name, "description": description, "panels": [], "refresh": 5}
    return DASHBOARDS[did]


async def list_dashboards() -> list[dict]:
    return list(DASHBOARDS.values())


async def get_dashboard(dashboard_id: str) -> dict | None:
    return DASHBOARDS.get(dashboard_id)


async def delete_dashboard(dashboard_id: str) -> bool:
    return DASHBOARDS.pop(dashboard_id, None) is not None


async def add_panel(dashboard_id: str, title: str, metric: str, chart_type: str = "line") -> dict:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    panel = {"panel_id": f"p-{len(db['panels']) + 1}", "title": title, "metric": metric, "chart_type": chart_type}
    db["panels"].append(panel)
    return panel


async def remove_panel(dashboard_id: str, panel_id: str) -> bool:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        return False
    before = len(db["panels"])
    db["panels"] = [p for p in db["panels"] if p["panel_id"] != panel_id]
    return len(db["panels"]) < before


async def get_live_data(dashboard_id: str) -> dict:
    import random
    return {"dashboard_id": dashboard_id, "panels": {p["panel_id"]: {"value": round(random.random() * 100, 1)} for p in DASHBOARDS.get(dashboard_id, {}).get("panels", [])}}


async def ingest_metric(name: str, value: float) -> dict:
    return {"metric": name, "value": value, "ingested": True}


async def get_analytics_stats() -> dict:
    return {"dashboards": len(DASHBOARDS)}


async def update_dashboard(dashboard_id: str, **kwargs) -> dict | None:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        return None
    db.update(kwargs)
    return db


async def update_panel(dashboard_id: str, panel_id: str, **kwargs) -> dict | None:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        return None
    for p in db.get("panels", []):
        if p.get("panel_id") == panel_id:
            p.update(kwargs)
            return p
    return None


async def register_metric(name: str, unit: str = "count") -> dict:
    metric_id = f"m-{len(DASHBOARDS) + 1}"
    if "_metrics" not in globals():
        globals()["_metrics"] = {}
    globals()["_metrics"][metric_id] = {"metric_id": metric_id, "name": name, "unit": unit}
    return globals()["_metrics"][metric_id]


async def list_metrics() -> list[dict]:
    return list(globals().get("_metrics", {}).values())


async def create_alert_rule(name: str, metric_id: str, condition: str = "above", threshold: float = 0.0) -> dict:
    alert_id = f"ar-{len(DASHBOARDS) + 1}"
    if "_alerts" not in globals():
        globals()["_alerts"] = {}
    alert = {"alert_id": alert_id, "name": name, "metric_id": metric_id, "condition": condition, "threshold": threshold, "enabled": True}
    globals()["_alerts"][alert_id] = alert
    return alert


async def list_alert_rules() -> list[dict]:
    return list(globals().get("_alerts", {}).values())


async def delete_alert_rule(alert_id: str) -> bool:
    alerts = globals().get("_alerts", {})
    return alerts.pop(alert_id, None) is not None


async def get_metric_history(metric_id: str, duration_seconds: int = 300) -> list[dict]:
    import random
    return [{"t": f"2026-01-01T00:00:{i:02d}Z", "v": round(random.random() * 100, 1)} for i in range(10)]


async def drill_down(metric_id: str, tags: dict[str, str] | None = None) -> list[dict]:
    import random
    return [{"t": "2026-01-01T00:00:00Z", "v": round(random.random() * 100, 1), "tags": tags or {}}]


async def aggregate_metric(metric_id: str, window_seconds: int = 60, agg: str = "avg") -> dict:
    import random
    values = [random.random() * 100 for _ in range(10)]
    if agg == "avg":
        result = sum(values) / len(values)
    elif agg == "sum":
        result = sum(values)
    elif agg == "max":
        result = max(values)
    else:
        result = sum(values) / len(values)
    return {"metric_id": metric_id, f"{agg}_value": round(result, 2), "count": len(values)}


async def simulate_stream(dashboard_id: str, interval: float = 1.0, count: int = 5) -> list[dict]:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        raise ValueError(f"Dashboard {dashboard_id} not found")
    import random
    generated = []
    for _ in range(count):
        for panel in db.get("panels", []):
            val = round(random.random() * 100, 1)
            generated.append({"metric": panel.get("metric"), "value": val, "panel_id": panel.get("panel_id")})
        await asyncio.sleep(interval)
    return generated


async def get_dashboard_share_url(dashboard_id: str) -> str:
    return f"/shared/dashboards/{dashboard_id}"


async def duplicate_dashboard(dashboard_id: str, new_name: str) -> dict | None:
    original = DASHBOARDS.get(dashboard_id)
    if not original:
        return None
    did = f"db-{len(DASHBOARDS) + 1}"
    DASHBOARDS[did] = {**original, "dashboard_id": did, "name": new_name, "panels": [dict(p) for p in original.get("panels", [])]}
    return DASHBOARDS[did]


async def list_chart_types() -> list[str]:
    return ["line", "bar", "area", "pie", "scatter", "heatmap", "gauge", "stat"]


async def clear_buffer() -> dict:
    return {"cleared": 0}


async def get_dashboard_refresh_rates() -> list[dict]:
    return [{"label": "Real-time", "value": 0}, {"label": "1s", "value": 1}, {"label": "5s", "value": 5}, {"label": "10s", "value": 10}, {"label": "30s", "value": 30}, {"label": "1min", "value": 60}]


async def update_alert_rule(alert_id: str, **kwargs) -> dict | None:
    alerts = globals().get("_alerts", {})
    a = alerts.get(alert_id)
    if not a:
        return None
    a.update(kwargs)
    return a


async def get_alert_history(metric_id: str) -> list[dict]:
    alerts = globals().get("_alerts", {})
    return [a for a in alerts.values() if a.get("metric_id") == metric_id]


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_dashboards(offset: int = 0, limit: int = 50) -> dict:
    results = list(DASHBOARDS.values())
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def format_dashboard_info(dashboard_id: str) -> dict:
    db = DASHBOARDS.get(dashboard_id)
    if not db:
        return {"error": "Dashboard not found"}
    return {
        "dashboard_id": db["dashboard_id"],
        "name": db.get("name"),
        "refresh_rate": db.get("refresh_rate", 0),
        "panels": len(db.get("panels", [])),
    }

async def batch_create_dashboards(dashboards: list[dict]) -> list[dict]:
    created = []
    for d in dashboards:
        db = await create_dashboard(d.get("name", "dashboard"), d.get("refresh_rate", 0))
        created.append(db)
    return created

async def search_dashboards(query: str) -> list[dict]:
    q = query.lower()
    return [db for db in DASHBOARDS.values() if q in db.get("name", "").lower()]

async def get_realtime_analytics_summary() -> dict:
    return {
        "total_dashboards": len(DASHBOARDS),
        "total_metrics": len(globals().get("_metrics", {})),
        "total_alert_rules": len(globals().get("_alerts", {})),
        "enabled_alert_rules": sum(1 for a in globals().get("_alerts", {}).values() if a.get("enabled")),
    }

async def bulk_update_dashboards(dashboard_ids: list[str], **kwargs) -> dict:
    updated = 0
    for did in dashboard_ids:
        if await update_dashboard(did, **kwargs):
            updated += 1
    return {"updated": updated, "total_requested": len(dashboard_ids)}

async def get_metric_names() -> list[str]:
    return [m.get("name") for m in globals().get("_metrics", {}).values()]

async def get_anomalies(metric_id: str, window: int = 60) -> list[dict]:
    history = await get_metric_history(metric_id, window)
    values = [h.get("v", 0) for h in history]
    avg = sum(values) / max(len(values), 1)
    return [h for h in history if h.get("v", 0) > avg * 1.5 or h.get("v", 0) < avg * 0.5]

# -- Extended Operations -----------------------------------------------

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "records_processed": 0, "throughput": 0.0, "error_rate": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class DataCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    records_affected: int = Field(default=0)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
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

class DataCogMetrics:
    def __init__(self) -> None:
        self.batches: int = 0
        self.records: int = 0
        self.errors: int = 0
        self.total_duration_ms: float = 0.0

    def record(self, records: int = 0, duration_ms: float = 0.0, error: bool = False) -> None:
        self.batches += 1
        self.records += records
        self.total_duration_ms += duration_ms
        if error:
            self.errors += 1

    def summary(self) -> Dict[str, Any]:
        return {"batches": self.batches, "records": self.records, "errors": self.errors,
                "avg_records_per_batch": round(self.records / max(self.batches, 1), 1),
                "avg_duration_ms": round(self.total_duration_ms / max(self.batches, 1), 1),
                "error_rate": round(self.errors / max(self.batches, 1) * 100, 1)}
