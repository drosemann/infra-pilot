"""Self-Service Reporting — drag-and-drop report builder, SQL/visual modes, scheduled delivery."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReportMode(Enum):
    SQL = "sql"
    VISUAL = "visual"
    HYBRID = "hybrid"


class ChartType(Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    TABLE = "table"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    METRIC = "metric"


class DeliveryFormat(Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    PNG = "png"


@dataclass
class ReportWidget:
    widget_id: str
    title: str
    chart_type: ChartType
    sql: str = ""
    dataset: str = ""
    x_axis: str = ""
    y_axis: str = ""
    group_by: str = ""
    filters: list[dict] = field(default_factory=list)
    width: int = 6
    height: int = 4
    position_x: int = 0
    position_y: int = 0


@dataclass
class ReportDesign:
    report_id: str
    name: str
    description: str
    mode: ReportMode = ReportMode.VISUAL
    widgets: list[ReportWidget] = field(default_factory=list)
    parameters: list[dict] = field(default_factory=list)
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: list[str] = field(default_factory=list)
    is_template: bool = False


@dataclass
class ReportSchedule:
    schedule_id: str
    report_id: str
    cron: str
    format: DeliveryFormat
    recipients: list[str] = field(default_factory=list)
    include_attachments: bool = True
    enabled: bool = True
    last_run: str = ""
    next_run: str = ""
    created_at: str = ""


@dataclass
class ReportDelivery:
    delivery_id: str
    schedule_id: str
    report_id: str
    format: str
    status: str
    delivered_to: list[str]
    delivered_at: str = ""
    error: str = ""


_reports: dict[str, ReportDesign] = {}
_schedules: dict[str, ReportSchedule] = {}
_deliveries: list[ReportDelivery] = []
_widget_results: dict[str, list[dict]] = {}


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def create_report(name: str, description: str, mode: ReportMode = ReportMode.VISUAL, created_by: str = "") -> ReportDesign:
    report = ReportDesign(
        report_id=str(uuid4()),
        name=name,
        description=description,
        mode=mode,
        created_by=created_by,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _reports[report.report_id] = report
    return report


async def list_reports() -> list[ReportDesign]:
    return list(_reports.values())


async def get_report(report_id: str) -> Optional[ReportDesign]:
    return _reports.get(report_id)


async def update_report(report_id: str, **kwargs) -> Optional[ReportDesign]:
    r = _reports.get(report_id)
    if not r:
        return None
    for k, v in kwargs.items():
        if hasattr(r, k):
            setattr(r, k, v)
    r.updated_at = _ts()
    return r


async def delete_report(report_id: str) -> bool:
    report = _reports.pop(report_id, None)
    if report:
        _schedules = {k: v for k, v in _schedules.items() if v.report_id != report_id}
        return True
    return False


async def add_widget(
    report_id: str,
    title: str,
    chart_type: ChartType,
    sql: str = "",
    dataset: str = "",
    x_axis: str = "",
    y_axis: str = "",
    width: int = 6,
    height: int = 4,
    filters: list[dict] | None = None,
) -> Optional[ReportWidget]:
    r = _reports.get(report_id)
    if not r:
        return None
    widget = ReportWidget(
        widget_id=str(uuid4()),
        title=title,
        chart_type=chart_type,
        sql=sql,
        dataset=dataset,
        x_axis=x_axis,
        y_axis=y_axis,
        filters=filters or [],
        width=width,
        height=height,
        position_x=len(r.widgets) % 2 * 6,
        position_y=len(r.widgets) // 2 * 4,
    )
    r.widgets.append(widget)
    return widget


async def update_widget(report_id: str, widget_id: str, **kwargs) -> Optional[ReportWidget]:
    r = _reports.get(report_id)
    if not r:
        return None
    for w in r.widgets:
        if w.widget_id == widget_id:
            for k, v in kwargs.items():
                if hasattr(w, k):
                    setattr(w, k, v)
            return w
    return None


async def remove_widget(report_id: str, widget_id: str) -> bool:
    r = _reports.get(report_id)
    if not r:
        return False
    before = len(r.widgets)
    r.widgets = [w for w in r.widgets if w.widget_id != widget_id]
    return len(r.widgets) < before


async def execute_widget(report_id: str, widget_id: str) -> list[dict]:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    w = next((x for x in r.widgets if x.widget_id == widget_id), None)
    if not w:
        raise ValueError(f"Widget {widget_id} not found")
    await asyncio.sleep(0.15)
    import random
    results = [{w.x_axis or "x": f"cat{i}", w.y_axis or "y": round(random.random() * 100, 1)} for i in range(10)]
    _widget_results[widget_id] = results
    return results


async def get_widget_data(widget_id: str) -> list[dict]:
    return _widget_results.get(widget_id, [])


async def add_parameter(report_id: str, name: str, param_type: str = "text", default_value: Any = "", options: list[str] | None = None) -> bool:
    r = _reports.get(report_id)
    if not r:
        return False
    r.parameters.append({"name": name, "type": param_type, "default": default_value, "options": options or []})
    return True


async def execute_report(report_id: str, params: dict | None = None) -> dict:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    widget_results = {}
    for w in r.widgets:
        data = await execute_widget(report_id, w.widget_id)
        widget_results[w.widget_id] = data
    return {"report_id": report_id, "name": r.name, "widgets": len(r.widgets), "results": widget_results}


async def create_schedule(report_id: str, cron: str, fmt: DeliveryFormat, recipients: list[str]) -> ReportSchedule:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    s = ReportSchedule(
        schedule_id=str(uuid4()),
        report_id=report_id,
        cron=cron,
        format=fmt,
        recipients=recipients,
        created_at=_ts(),
    )
    _schedules[s.schedule_id] = s
    return s


async def list_schedules() -> list[ReportSchedule]:
    return list(_schedules.values())


async def delete_schedule(schedule_id: str) -> bool:
    return _schedules.pop(schedule_id, None) is not None


async def trigger_delivery(schedule_id: str) -> Optional[ReportDelivery]:
    s = _schedules.get(schedule_id)
    if not s or not s.enabled:
        return None
    delivery = ReportDelivery(
        delivery_id=str(uuid4()),
        schedule_id=schedule_id,
        report_id=s.report_id,
        format=s.format.value,
        status="delivered",
        delivered_to=s.recipients,
        delivered_at=_ts(),
    )
    _deliveries.append(delivery)
    s.last_run = _ts()
    return delivery


async def list_deliveries(report_id: str | None = None) -> list[ReportDelivery]:
    if report_id:
        return [d for d in _deliveries if d.report_id == report_id]
    return _deliveries


async def export_report(report_id: str, fmt: DeliveryFormat) -> str:
    await asyncio.sleep(0.2)
    return f"/exports/reports/{report_id}.{fmt.value}"


async def get_report_stats() -> dict:
    return {
        "total_reports": len(_reports),
        "total_widgets": sum(len(r.widgets) for r in _reports.values()),
        "total_schedules": len(_schedules),
        "total_deliveries": len(_deliveries),
    }


async def duplicate_report(report_id: str, new_name: str) -> Optional[ReportDesign]:
    original = _reports.get(report_id)
    if not original:
        return None
    report = ReportDesign(
        report_id=str(uuid4()),
        name=new_name,
        description=f"Copy of {original.name}",
        mode=original.mode,
        created_by=original.created_by,
        created_at=_ts(),
        updated_at=_ts(),
        tags=list(original.tags),
        is_template=False,
    )
    for w in original.widgets:
        report.widgets.append(ReportWidget(
            widget_id=str(uuid4()),
            title=w.title,
            chart_type=w.chart_type,
            sql=w.sql,
            dataset=w.dataset,
            x_axis=w.x_axis,
            y_axis=w.y_axis,
            group_by=w.group_by,
            filters=list(w.filters),
            width=w.width,
            height=w.height,
            position_x=w.position_x,
            position_y=w.position_y,
        ))
    for p in original.parameters:
        report.parameters.append(dict(p))
    _reports[report.report_id] = report
    return report


async def save_as_template(report_id: str) -> Optional[ReportDesign]:
    r = _reports.get(report_id)
    if not r:
        return None
    r.is_template = True
    return r


async def list_templates() -> list[ReportDesign]:
    return [r for r in _reports.values() if r.is_template]


async def reorder_widgets(report_id: str, widget_ids: list[str]) -> bool:
    r = _reports.get(report_id)
    if not r:
        return False
    widget_map = {w.widget_id: w for w in r.widgets}
    reordered = []
    for wid in widget_ids:
        if wid in widget_map:
            reordered.append(widget_map[wid])
    for w in r.widgets:
        if w.widget_id not in widget_ids:
            reordered.append(w)
    r.widgets = reordered
    return True


async def get_delivery_status(delivery_id: str) -> Optional[ReportDelivery]:
    for d in _deliveries:
        if d.delivery_id == delivery_id:
            return d
    return None


async def retry_delivery(delivery_id: str) -> Optional[ReportDelivery]:
    for d in _deliveries:
        if d.delivery_id == delivery_id and d.status == "failed":
            d.status = "retrying"
            await asyncio.sleep(0.1)
            d.status = "delivered"
            d.delivered_at = _ts()
            return d
    return None


async def list_chart_types() -> list[str]:
    return [c.value for c in ChartType]


async def list_delivery_formats() -> list[str]:
    return [f.value for f in DeliveryFormat]


async def enable_schedule(schedule_id: str, enabled: bool) -> Optional[ReportSchedule]:
    s = _schedules.get(schedule_id)
    if not s:
        return None
    s.enabled = enabled
    return s


async def get_report_preview(report_id: str) -> dict:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    return {
        "report_id": report_id,
        "name": r.name,
        "mode": r.mode.value,
        "widgets": [{"title": w.title, "chart_type": w.chart_type.value, "dataset": w.dataset} for w in r.widgets],
        "parameters": r.parameters,
    }


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class ReportBatchOperation:
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
class ReportPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    mode_filter: str | None = None
    template_filter: bool | None = None


@dataclass
class ReportPaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class ReportLifecycleTransition:
    from_state: str
    to_state: str
    trigger: str
    report_id: str
    timestamp: str = ""
    actor: str = "system"


_report_batch_ops: dict[str, ReportBatchOperation] = {}
_report_lifecycle_history: dict[str, list[ReportLifecycleTransition]] = {}


async def paginate_reports(params: ReportPaginationParams | None = None) -> ReportPaginatedResult:
    p = params or ReportPaginationParams()
    results = list(_reports.values())
    if p.mode_filter:
        results = [r for r in results if r.mode.value == p.mode_filter]
    if p.template_filter is not None:
        results = [r for r in results if r.is_template == p.template_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda r: r.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda r: r.created_at, reverse=p.sort_order == "desc")
    elif p.sort_by == "updated_at":
        results.sort(key=lambda r: r.updated_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return ReportPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                  has_more=(p.offset + p.limit < total))


async def paginate_schedules(params: ReportPaginationParams | None = None) -> ReportPaginatedResult:
    p = params or ReportPaginationParams()
    results = list(_schedules.values())
    total = len(results)
    results.sort(key=lambda s: s.next_run or "", reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return ReportPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                  has_more=(p.offset + p.limit < total))


async def paginate_deliveries(params: ReportPaginationParams | None = None) -> ReportPaginatedResult:
    p = params or ReportPaginationParams()
    results = list(_deliveries)
    total = len(results)
    results.sort(key=lambda d: d.delivered_at or "", reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return ReportPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                  has_more=(p.offset + p.limit < total))


async def batch_delete_reports(report_ids: list[str]) -> ReportBatchOperation:
    op = ReportBatchOperation(batch_id=str(uuid4()), operation="delete", item_ids=[], created_at=_ts())
    for rid in report_ids:
        if await delete_report(rid):
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"report_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _report_batch_ops[op.batch_id] = op
    return op


async def batch_duplicate_reports(report_ids: list[str]) -> ReportBatchOperation:
    op = ReportBatchOperation(batch_id=str(uuid4()), operation="duplicate", item_ids=[], created_at=_ts())
    for rid in report_ids:
        r = _reports.get(rid)
        if r:
            dup = await duplicate_report(rid, f"{r.name} (Copy)")
            if dup:
                op.item_ids.append(dup.report_id)
                op.success_count += 1
            else:
                op.failure_count += 1
                op.errors.append({"report_id": rid, "error": "duplication failed"})
        else:
            op.failure_count += 1
            op.errors.append({"report_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _report_batch_ops[op.batch_id] = op
    return op


async def batch_enable_schedules(schedule_ids: list[str], enabled: bool) -> ReportBatchOperation:
    op = ReportBatchOperation(batch_id=str(uuid4()), operation="toggle_schedules", item_ids=[], created_at=_ts())
    for sid in schedule_ids:
        s = _schedules.get(sid)
        if s:
            s.enabled = enabled
            op.item_ids.append(sid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"schedule_id": sid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _report_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[ReportBatchOperation]:
    return _report_batch_ops.get(batch_id)


async def export_report_template(report_id: str) -> dict:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    return {
        "name": r.name, "description": r.description, "mode": r.mode.value,
        "parameters": r.parameters,
        "widgets": [{"title": w.title, "chart_type": w.chart_type.value, "sql": w.sql,
                      "dataset": w.dataset, "x_axis": w.x_axis, "y_axis": w.y_axis,
                      "group_by": w.group_by, "filters": w.filters} for w in r.widgets],
        "tags": r.tags,
        "exported_at": _ts(),
    }


async def import_report_template(data: dict) -> ReportDesign:
    r = await create_report(data["name"], data.get("description", ""),
                             ReportMode(data.get("mode", "visual")), data.get("created_by", ""))
    for wd in data.get("widgets", []):
        await add_widget(r.report_id, wd["title"], ChartType(wd.get("chart_type", "bar")),
                          wd.get("sql", ""), wd.get("dataset", ""),
                          wd.get("x_axis", ""), wd.get("y_axis", ""),
                          wd.get("width", 6), wd.get("height", 4), wd.get("filters"))
    for pd in data.get("parameters", []):
        await add_parameter(r.report_id, pd["name"], pd.get("type", "text"), pd.get("default", ""), pd.get("options"))
    r.tags = data.get("tags", [])
    return r


async def get_reporting_analytics() -> dict:
    total_reports = len(_reports)
    total_widgets = sum(len(r.widgets) for r in _reports.values())
    total_schedules = len(_schedules)
    total_deliveries = len(_deliveries)
    by_mode = {}
    for r in _reports.values():
        by_mode[r.mode.value] = by_mode.get(r.mode.value, 0) + 1
    by_chart = {}
    for r in _reports.values():
        for w in r.widgets:
            by_chart[w.chart_type.value] = by_chart.get(w.chart_type.value, 0) + 1
    templates = sum(1 for r in _reports.values() if r.is_template)
    return {
        "total_reports": total_reports,
        "total_widgets": total_widgets,
        "total_schedules": total_schedules,
        "total_deliveries": total_deliveries,
        "by_mode": by_mode,
        "by_chart_type": by_chart,
        "templates": templates,
        "avg_widgets_per_report": round(total_widgets / max(total_reports, 1), 1),
        "delivery_success_rate": round(sum(1 for d in _deliveries if d.status == "delivered") / max(total_deliveries, 1) * 100, 1),
    }


async def transition_report_state(report_id: str, trigger: str, actor: str = "system") -> dict:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    from_state = "draft" if not r.widgets else "published"
    valid_transitions = {
        "draft": {"publish", "archive"},
        "published": {"archive", "draft", "template"},
        "archived": {"restore"},
        "template": {"publish", "archive"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"report_id": report_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {"publish": "published", "archive": "archived", "restore": "draft", "template": "template", "draft": "draft"}
    to_state = to_state_map.get(trigger, from_state)
    if trigger == "template":
        await save_as_template(report_id)
    transition = ReportLifecycleTransition(from_state=from_state, to_state=to_state, trigger=trigger,
                                            report_id=report_id, timestamp=_ts(), actor=actor)
    _report_lifecycle_history.setdefault(report_id, []).append(transition)
    return {"report_id": report_id, "success": True, "from_state": from_state, "to_state": to_state}


async def get_report_state_history(report_id: str) -> list[ReportLifecycleTransition]:
    return _report_lifecycle_history.get(report_id, [])


async def validate_report_config(report_id: str) -> dict:
    r = _reports.get(report_id)
    if not r:
        raise ValueError(f"Report {report_id} not found")
    issues = []
    if not r.name:
        issues.append("Report name is required")
    if not r.widgets:
        issues.append("Report has no widgets")
    for w in r.widgets:
        if not w.title:
            issues.append(f"Widget {w.widget_id} has no title")
        if w.chart_type == ChartType.TABLE and not w.sql and not w.dataset:
            issues.append(f"Table widget '{w.title}' has no SQL or dataset defined")
    if r.parameters:
        param_names = [p["name"] for p in r.parameters]
        if len(param_names) != len(set(param_names)):
            issues.append("Duplicate parameter names detected")
    return {"report_id": report_id, "valid": len(issues) == 0, "issues": issues}


async def search_reports(query: str) -> list[ReportDesign]:
    q = query.lower()
    return [r for r in _reports.values() if q in r.name.lower() or q in r.description.lower() or any(q in t.lower() for t in r.tags)]


async def get_delivery_stats(days: int = 7) -> dict:
    cutoff = datetime.utcnow().timestamp() - days * 86400
    recent = [d for d in _deliveries if d.delivered_at and
               datetime.fromisoformat(d.delivered_at.replace("Z", "+00:00")).timestamp() > cutoff]
    return {
        "period_days": days,
        "total_deliveries": len(recent),
        "successful": sum(1 for d in recent if d.status == "delivered"),
        "failed": sum(1 for d in recent if d.status == "failed"),
        "by_format": {fmt: sum(1 for d in recent if d.format == fmt) for fmt in set(d.format for d in recent)},
    }


async def bulk_save_as_templates(report_ids: list[str]) -> ReportBatchOperation:
    op = ReportBatchOperation(batch_id=str(uuid4()), operation="save_as_template", item_ids=[], created_at=_ts())
    for rid in report_ids:
        r = await save_as_template(rid)
        if r:
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"report_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _report_batch_ops[op.batch_id] = op
    return op


async def bulk_trigger_deliveries(schedule_ids: list[str]) -> ReportBatchOperation:
    op = ReportBatchOperation(batch_id=str(uuid4()), operation="trigger_delivery", item_ids=[], created_at=_ts())
    for sid in schedule_ids:
        d = await trigger_delivery(sid)
        if d:
            op.item_ids.append(d.delivery_id)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"schedule_id": sid, "error": "delivery failed"})
    op.status = "completed"
    op.completed_at = _ts()
    _report_batch_ops[op.batch_id] = op
    return op


async def get_widget_stats() -> dict:
    all_widgets = [w for r in _reports.values() for w in r.widgets]
    by_chart = {}
    for w in all_widgets:
        by_chart[w.chart_type.value] = by_chart.get(w.chart_type.value, 0) + 1
    return {
        "total_widgets": len(all_widgets),
        "by_chart_type": by_chart,
        "avg_width": round(sum(w.width for w in all_widgets) / max(len(all_widgets), 1), 1),
        "avg_height": round(sum(w.height for w in all_widgets) / max(len(all_widgets), 1), 1),
    }


class ReportMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class ReportCache:
    def __init__(self, ttl: int = 120):
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


class ReportAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, report_id: str = "", detail: str = "") -> dict:
        entry = {"action": action, "report_id": report_id, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_report_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    results = []
    for r in _reports.values():
        if query.lower() in r.name.lower():
            results.append({"report_id": r.report_id, "name": r.name, "mode": r.mode.value})
            if len(results) >= limit:
                break
    return results


async def recommend_report_cleanup(days_threshold: int = 90) -> list[dict]:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    stale = []
    for r in _reports.values():
        created = datetime.fromisoformat(r.created_at.replace("Z", "+00:00"))
        if created < cutoff:
            stale.append({"report_id": r.report_id, "name": r.name, "created": r.created_at})
    return stale


async def merge_report_entities(report_ids: list[str]) -> Report:
    target_id = report_ids[0]
    target = _reports.get(target_id)
    if not target:
        raise ValueError(f"Report {target_id} not found")
    for rid in report_ids[1:]:
        source = _reports.get(rid)
        if source:
            for w in source.widgets:
                if not any(ex.name == w.name for ex in target.widgets):
                    target.widgets.append(w)
            del _reports[rid]
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
