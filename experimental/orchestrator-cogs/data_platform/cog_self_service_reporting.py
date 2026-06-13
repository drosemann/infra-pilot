"""Cog: Self-Service Reporting — drag-and-drop report builder, SQL/visual modes."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

REPORTS: dict[str, dict] = {}


async def create_report(name: str, description: str = "") -> dict:
    rid = f"rpt-{len(REPORTS) + 1}"
    REPORTS[rid] = {"report_id": rid, "name": name, "description": description, "widgets": [], "parameters": []}
    return REPORTS[rid]


async def list_reports() -> list[dict]:
    return list(REPORTS.values())


async def get_report(report_id: str) -> dict | None:
    return REPORTS.get(report_id)


async def delete_report(report_id: str) -> bool:
    return REPORTS.pop(report_id, None) is not None


async def add_widget(report_id: str, title: str, chart_type: str = "bar") -> dict:
    r = REPORTS.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    widget = {"widget_id": f"w-{len(r['widgets']) + 1}", "title": title, "chart_type": chart_type}
    r["widgets"].append(widget)
    return widget


async def add_parameter(report_id: str, name: str, param_type: str = "text") -> bool:
    r = REPORTS.get(report_id)
    if not r:
        return False
    r["parameters"].append({"name": name, "type": param_type})
    return True


async def execute_report(report_id: str) -> dict:
    r = REPORTS.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    return {"report_id": report_id, "name": r["name"], "status": "generated", "widgets": len(r["widgets"])}


async def get_reporting_stats() -> dict:
    return {"total_reports": len(REPORTS)}


async def update_report(report_id: str, **kwargs) -> dict | None:
    r = REPORTS.get(report_id)
    if not r:
        return None
    r.update(kwargs)
    return r


async def remove_widget(report_id: str, widget_id: str) -> bool:
    r = REPORTS.get(report_id)
    if not r:
        return False
    before = len(r.get("widgets", []))
    r["widgets"] = [w for w in r.get("widgets", []) if w.get("widget_id") != widget_id]
    return len(r["widgets"]) < before


async def update_widget(report_id: str, widget_id: str, **kwargs) -> dict | None:
    r = REPORTS.get(report_id)
    if not r:
        return None
    for w in r.get("widgets", []):
        if w.get("widget_id") == widget_id:
            w.update(kwargs)
            return w
    return None


async def get_widget_data(report_id: str, widget_id: str) -> list[dict]:
    import random
    return [{"x": f"cat{i}", "y": round(random.random() * 100, 1)} for i in range(10)]


async def create_schedule(report_id: str, cron: str, format: str = "pdf", recipients: list[str] | None = None) -> dict:
    r = REPORTS.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    schedule = {"schedule_id": f"sch-{len(REPORTS) + 1}", "report_id": report_id, "cron": cron, "format": format, "recipients": recipients or [], "enabled": True}
    if "_schedules" not in globals():
        globals()["_schedules"] = {}
    globals()["_schedules"][schedule["schedule_id"]] = schedule
    return schedule


async def list_schedules() -> list[dict]:
    return list(globals().get("_schedules", {}).values())


async def delete_schedule(schedule_id: str) -> bool:
    schedules = globals().get("_schedules", {})
    return schedules.pop(schedule_id, None) is not None


async def trigger_delivery(schedule_id: str) -> dict | None:
    schedules = globals().get("_schedules", {})
    s = schedules.get(schedule_id)
    if not s or not s.get("enabled"):
        return None
    delivery = {"delivery_id": f"del-{len(REPORTS)}", "schedule_id": schedule_id, "report_id": s["report_id"], "status": "delivered"}
    if "_deliveries" not in globals():
        globals()["_deliveries"] = []
    globals()["_deliveries"].append(delivery)
    return delivery


async def list_deliveries(report_id: str | None = None) -> list[dict]:
    deliveries = globals().get("_deliveries", [])
    if report_id:
        return [d for d in deliveries if d.get("report_id") == report_id]
    return deliveries


async def duplicate_report(report_id: str, new_name: str) -> dict | None:
    original = REPORTS.get(report_id)
    if not original:
        return None
    rid = f"rpt-{len(REPORTS) + 1}"
    REPORTS[rid] = {**original, "report_id": rid, "name": new_name, "widgets": [dict(w) for w in original.get("widgets", [])], "parameters": [dict(p) for p in original.get("parameters", [])]}
    return REPORTS[rid]


async def export_report(report_id: str, fmt: str = "pdf") -> str:
    return f"/exports/reports/{report_id}.{fmt}"


async def enable_schedule(schedule_id: str, enabled: bool) -> dict | None:
    schedules = globals().get("_schedules", {})
    s = schedules.get(schedule_id)
    if not s:
        return None
    s["enabled"] = enabled
    return s


async def list_chart_types() -> list[str]:
    return ["bar", "line", "pie", "area", "table", "scatter", "heatmap", "funnel", "metric"]


async def list_delivery_formats() -> list[str]:
    return ["pdf", "csv", "excel", "png"]


async def save_as_template(report_id: str) -> dict | None:
    r = REPORTS.get(report_id)
    if not r:
        return None
    r["is_template"] = True
    return r


async def list_templates() -> list[dict]:
    return [r for r in REPORTS.values() if r.get("is_template")]


async def reorder_widgets(report_id: str, widget_ids: list[str]) -> bool:
    r = REPORTS.get(report_id)
    if not r:
        return False
    widget_map = {w.get("widget_id"): w for w in r.get("widgets", [])}
    reordered = [widget_map[wid] for wid in widget_ids if wid in widget_map]
    remaining = [w for w in r.get("widgets", []) if w.get("widget_id") not in widget_ids]
    r["widgets"] = reordered + remaining
    return True


async def get_delivery_status(delivery_id: str) -> dict | None:
    for d in globals().get("_deliveries", []):
        if d.get("delivery_id") == delivery_id:
            return d
    return None


async def retry_delivery(delivery_id: str) -> dict | None:
    for d in globals().get("_deliveries", []):
        if d.get("delivery_id") == delivery_id and d.get("status") == "failed":
            d["status"] = "delivered"
            return d
    return None


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_reports(offset: int = 0, limit: int = 50, is_template: bool = None) -> dict:
    results = list(REPORTS.values())
    if is_template is not None:
        results = [r for r in results if r.get("is_template") == is_template]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def format_report_info(report_id: str) -> dict:
    r = REPORTS.get(report_id)
    if not r:
        return {"error": "Report not found"}
    return {
        "report_id": r["report_id"],
        "name": r.get("name"),
        "widgets": len(r.get("widgets", [])),
        "parameters": len(r.get("parameters", [])),
        "is_template": r.get("is_template", False),
    }

async def bulk_duplicate_reports(report_ids: list[str], suffix: str = "_copy") -> dict:
    duplicated = []
    for rid in report_ids:
        r = REPORTS.get(rid)
        if r:
            new = await duplicate_report(rid, f"{r.get('name', 'report')}{suffix}")
            if new:
                duplicated.append(new)
    return {"duplicated": len(duplicated), "total_requested": len(report_ids)}

async def batch_create_widgets(report_id: str, widgets: list[dict]) -> list[dict]:
    created = []
    for w in widgets:
        wid = await add_widget(report_id, w.get("type", "bar"), w.get("title", "Widget"),
                                w.get("config", {}), w.get("size", "medium"))
        created.append(wid)
    return created

async def search_reports(query: str) -> list[dict]:
    q = query.lower()
    return [r for r in REPORTS.values() if q in r.get("name", "").lower() or q in r.get("report_id", "").lower()]

async def get_reporting_analytics() -> dict:
    return {
        "total_reports": len(REPORTS),
        "templates": sum(1 for r in REPORTS.values() if r.get("is_template")),
        "total_schedules": len(globals().get("_schedules", {})),
        "total_deliveries": len(globals().get("_deliveries", [])),
        "enabled_schedules": sum(1 for s in globals().get("_schedules", {}).values() if s.get("enabled")),
        "avg_widgets_per_report": round(
            sum(len(r.get("widgets", [])) for r in REPORTS.values()) / max(len(REPORTS), 1), 1
        ),
    }

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
