"""Data Pipeline Observability — end-to-end monitoring, lineage-based root cause analysis."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


class NodeType(Enum):
    SOURCE = "source"
    TRANSFORM = "transform"
    SINK = "sink"
    QUALITY_CHECK = "quality_check"


@dataclass
class PipelineNode:
    node_id: str
    name: str
    node_type: NodeType
    source: str = ""
    sink: str = ""
    query: str = ""
    config: dict = field(default_factory=dict)


@dataclass
class Pipeline:
    pipeline_id: str
    name: str
    description: str
    nodes: list[PipelineNode] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.UNKNOWN
    created_at: str = ""
    updated_at: str = ""
    owner: str = ""


@dataclass
class PipelineMetrics:
    metrics_id: str
    pipeline_id: str
    throughput_records_sec: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    data_freshness_sec: float = 0.0
    records_processed: int = 0
    bytes_processed: int = 0
    timestamp: str = ""


@dataclass
class PipelineAlert:
    alert_id: str
    pipeline_id: str
    node_id: str = ""
    severity: str = "info"
    message: str = ""
    metric: str = ""
    threshold: float = 0.0
    actual: float = 0.0
    triggered_at: str = ""
    acknowledged: bool = False


_pipelines: dict[str, Pipeline] = {}
_metrics_history: dict[str, list[PipelineMetrics]] = {}
_alerts: list[PipelineAlert] = []


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def create_pipeline(name: str, description: str = "", owner: str = "") -> Pipeline:
    p = Pipeline(
        pipeline_id=str(uuid4()),
        name=name,
        description=description,
        status=PipelineStatus.UNKNOWN,
        created_at=_ts(),
        updated_at=_ts(),
        owner=owner,
    )
    _pipelines[p.pipeline_id] = p
    return p


async def list_pipelines() -> list[Pipeline]:
    return list(_pipelines.values())


async def get_pipeline(pipeline_id: str) -> Optional[Pipeline]:
    return _pipelines.get(pipeline_id)


async def update_pipeline(pipeline_id: str, **kwargs) -> Optional[Pipeline]:
    p = _pipelines.get(pipeline_id)
    if not p:
        return None
    for k, v in kwargs.items():
        if hasattr(p, k):
            setattr(p, k, v)
    p.updated_at = _ts()
    return p


async def delete_pipeline(pipeline_id: str) -> bool:
    p = _pipelines.pop(pipeline_id, None)
    if p:
        _metrics_history.pop(pipeline_id, None)
        return True
    return False


async def add_node(
    pipeline_id: str,
    name: str,
    node_type: NodeType,
    source: str = "",
    sink: str = "",
    query: str = "",
    config: dict | None = None,
) -> Optional[PipelineNode]:
    p = _pipelines.get(pipeline_id)
    if not p:
        return None
    node = PipelineNode(
        node_id=str(uuid4()),
        name=name,
        node_type=node_type,
        source=source,
        sink=sink,
        query=query,
        config=config or {},
    )
    p.nodes.append(node)
    return node


async def remove_node(pipeline_id: str, node_id: str) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    before = len(p.nodes)
    p.nodes = [n for n in p.nodes if n.node_id != node_id]
    p.edges = [e for e in p.edges if e.get("from") != node_id and e.get("to") != node_id]
    return len(p.nodes) < before


async def add_edge(pipeline_id: str, from_node: str, to_node: str) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    p.edges.append({"from": from_node, "to": to_node})
    return True


async def start_pipeline(pipeline_id: str) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    p.status = PipelineStatus.RUNNING
    return True


async def pause_pipeline(pipeline_id: str) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    p.status = PipelineStatus.PAUSED
    return True


async def stop_pipeline(pipeline_id: str) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    p.status = PipelineStatus.COMPLETED
    return True


async def record_metrics(pipeline_id: str, throughput: float = 0.0, latency: float = 0.0, error_rate: float = 0.0, freshness: float = 0.0, records: int = 0, bytes_: int = 0) -> PipelineMetrics:
    m = PipelineMetrics(
        metrics_id=str(uuid4()),
        pipeline_id=pipeline_id,
        throughput_records_sec=throughput,
        latency_ms=latency,
        error_rate=error_rate,
        data_freshness_sec=freshness,
        records_processed=records,
        bytes_processed=bytes_,
        timestamp=_ts(),
    )
    _metrics_history.setdefault(pipeline_id, []).append(m)
    if len(_metrics_history[pipeline_id]) > 1000:
        _metrics_history[pipeline_id] = _metrics_history[pipeline_id][-500:]
    return m


async def get_metrics(pipeline_id: str, limit: int = 100) -> list[PipelineMetrics]:
    history = _metrics_history.get(pipeline_id, [])
    return history[-limit:]


async def get_current_metrics(pipeline_id: str) -> Optional[PipelineMetrics]:
    history = _metrics_history.get(pipeline_id, [])
    return history[-1] if history else None


async def get_pipeline_health(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    metrics = await get_current_metrics(pipeline_id)
    status = "healthy"
    issues = []
    if metrics:
        if metrics.error_rate > 5:
            status = "degraded"
            issues.append(f"High error rate: {metrics.error_rate:.1f}%")
        if metrics.latency_ms > 10000:
            status = "degraded"
            issues.append(f"High latency: {metrics.latency_ms:.0f}ms")
        if metrics.data_freshness_sec > 3600:
            status = "critical"
            issues.append(f"Data stale: {metrics.data_freshness_sec:.0f}s behind")
    return {
        "pipeline_id": pipeline_id,
        "name": p.name,
        "status": p.status.value,
        "health": status,
        "issues": issues,
        "metrics": {
            "throughput": metrics.throughput_records_sec if metrics else 0,
            "latency_ms": metrics.latency_ms if metrics else 0,
            "error_rate": metrics.error_rate if metrics else 0,
            "freshness_sec": metrics.data_freshness_sec if metrics else 0,
            "records_processed": metrics.records_processed if metrics else 0,
        } if metrics else {},
    }


async def root_cause_analysis(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    await asyncio.sleep(0.2)
    metrics = await get_current_metrics(pipeline_id)
    causes = []
    if metrics:
        if metrics.error_rate > 5:
            for node in p.nodes:
                if node.node_type == NodeType.SOURCE:
                    causes.append({"node": node.name, "issue": "source connectivity", "probability": 0.7})
                elif node.node_type == NodeType.TRANSFORM:
                    causes.append({"node": node.name, "issue": "transformation error", "probability": 0.5})
    return {
        "pipeline_id": pipeline_id,
        "analysis_time": _ts(),
        "root_causes": causes or [{"node": "unknown", "issue": "no issues detected", "probability": 0.0}],
    }


async def create_alert(
    pipeline_id: str,
    message: str,
    severity: str = "info",
    node_id: str = "",
    metric: str = "",
    threshold: float = 0.0,
    actual: float = 0.0,
) -> PipelineAlert:
    alert = PipelineAlert(
        alert_id=str(uuid4()),
        pipeline_id=pipeline_id,
        node_id=node_id,
        severity=severity,
        message=message,
        metric=metric,
        threshold=threshold,
        actual=actual,
        triggered_at=_ts(),
    )
    _alerts.append(alert)
    return alert


async def list_alerts(pipeline_id: str | None = None, severity: str | None = None) -> list[PipelineAlert]:
    results = _alerts
    if pipeline_id:
        results = [a for a in results if a.pipeline_id == pipeline_id]
    if severity:
        results = [a for a in results if a.severity == severity]
    return results[::-1]


async def acknowledge_alert(alert_id: str) -> bool:
    for a in _alerts:
        if a.alert_id == alert_id:
            a.acknowledged = True
            return True
    return False


async def get_upstream_pipelines(pipeline_id: str) -> list[str]:
    p = _pipelines.get(pipeline_id)
    if not p:
        return []
    upstream = []
    for edge in p.edges:
        for node in p.nodes:
            if node.node_id == edge.get("from") and node.node_type == NodeType.SOURCE:
                upstream.append(node.source)
    return upstream


async def get_downstream_pipelines(pipeline_id: str) -> list[str]:
    p = _pipelines.get(pipeline_id)
    if not p:
        return []
    downstream = []
    for edge in p.edges:
        for node in p.nodes:
            if node.node_id == edge.get("to") and node.node_type == NodeType.SINK:
                downstream.append(node.sink)
    return downstream


async def get_observability_summary() -> dict:
    total = len(_pipelines)
    running = sum(1 for p in _pipelines.values() if p.status == PipelineStatus.RUNNING)
    failed = sum(1 for p in _pipelines.values() if p.status == PipelineStatus.FAILED)
    return {
        "total_pipelines": total,
        "running": running,
        "paused": sum(1 for p in _pipelines.values() if p.status == PipelineStatus.PAUSED),
        "failed": failed,
        "completed": sum(1 for p in _pipelines.values() if p.status == PipelineStatus.COMPLETED),
        "total_alerts": len(_alerts),
        "unacknowledged_alerts": sum(1 for a in _alerts if not a.acknowledged),
    }


async def add_pipeline_tags(pipeline_id: str, tags: list[str]) -> bool:
    p = _pipelines.get(pipeline_id)
    if not p:
        return False
    if not hasattr(p, "tags"):
        p.tags = []
    for t in tags:
        if t not in p.tags:
            p.tags.append(t)
    return True


async def get_pipeline_dag(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    nodes_data = [{"id": n.node_id, "name": n.name, "type": n.node_type.value} for n in p.nodes]
    return {"pipeline_id": pipeline_id, "nodes": nodes_data, "edges": p.edges}


async def get_pipeline_sla(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    metrics = await get_current_metrics(pipeline_id)
    return {
        "pipeline_id": pipeline_id,
        "latency_sla_ms": 5000,
        "current_latency_ms": metrics.latency_ms if metrics else 0,
        "throughput_sla": 1000,
        "current_throughput": metrics.throughput_records_sec if metrics else 0,
        "sla_met": (metrics.latency_ms <= 5000 and metrics.throughput_records_sec >= 1000) if metrics else True,
    }


async def list_node_types() -> list[str]:
    return [n.value for n in NodeType]


async def retry_pipeline(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    p.status = PipelineStatus.RUNNING
    await asyncio.sleep(0.1)
    return {"pipeline_id": pipeline_id, "status": "retrying", "timestamp": _ts()}


async def get_alert_stats() -> dict:
    return {
        "total": len(_alerts),
        "critical": sum(1 for a in _alerts if a.severity == "critical"),
        "warning": sum(1 for a in _alerts if a.severity == "warning"),
        "info": sum(1 for a in _alerts if a.severity == "info"),
        "acknowledged": sum(1 for a in _alerts if a.acknowledged),
        "unacknowledged": sum(1 for a in _alerts if not a.acknowledged),
    }


async def bulk_acknowledge_alerts(pipeline_id: str) -> int:
    count = 0
    for a in _alerts:
        if a.pipeline_id == pipeline_id and not a.acknowledged:
            a.acknowledged = True
            count += 1
    return count


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class PipelineBatchOperation:
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
class PipelinePaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    status_filter: str | None = None


@dataclass
class PipelinePaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class PipelineStateTransition:
    from_state: str
    to_state: str
    trigger: str
    pipeline_id: str
    timestamp: str = ""
    actor: str = "system"


_pipeline_batch_ops: dict[str, PipelineBatchOperation] = {}
_pipeline_state_history: dict[str, list[PipelineStateTransition]] = {}


async def paginate_pipelines(params: PipelinePaginationParams | None = None) -> PipelinePaginatedResult:
    p = params or PipelinePaginationParams()
    results = list(_pipelines.values())
    if p.status_filter:
        results = [pipe for pipe in results if pipe.status.value == p.status_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda pipe: pipe.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda pipe: pipe.created_at, reverse=p.sort_order == "desc")
    elif p.sort_by == "updated_at":
        results.sort(key=lambda pipe: pipe.updated_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return PipelinePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def paginate_alerts(params: PipelinePaginationParams | None = None) -> PipelinePaginatedResult:
    p = params or PipelinePaginationParams()
    results = list(_alerts)
    if p.status_filter:
        results = [a for a in results if a.severity == p.status_filter]
    total = len(results)
    results.sort(key=lambda a: a.triggered_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return PipelinePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def paginate_metrics(pipeline_id: str, params: PipelinePaginationParams | None = None) -> PipelinePaginatedResult:
    p = params or PipelinePaginationParams()
    results = _metrics_history.get(pipeline_id, [])
    total = len(results)
    results.sort(key=lambda m: m.timestamp, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return PipelinePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                    has_more=(p.offset + p.limit < total))


async def batch_start_pipelines(pipeline_ids: list[str]) -> PipelineBatchOperation:
    op = PipelineBatchOperation(batch_id=str(uuid4()), operation="start", item_ids=[], created_at=_ts())
    for pid in pipeline_ids:
        if await start_pipeline(pid):
            op.item_ids.append(pid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"pipeline_id": pid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _pipeline_batch_ops[op.batch_id] = op
    return op


async def batch_pause_pipelines(pipeline_ids: list[str]) -> PipelineBatchOperation:
    op = PipelineBatchOperation(batch_id=str(uuid4()), operation="pause", item_ids=[], created_at=_ts())
    for pid in pipeline_ids:
        if await pause_pipeline(pid):
            op.item_ids.append(pid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"pipeline_id": pid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _pipeline_batch_ops[op.batch_id] = op
    return op


async def batch_stop_pipelines(pipeline_ids: list[str]) -> PipelineBatchOperation:
    op = PipelineBatchOperation(batch_id=str(uuid4()), operation="stop", item_ids=[], created_at=_ts())
    for pid in pipeline_ids:
        if await stop_pipeline(pid):
            op.item_ids.append(pid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"pipeline_id": pid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _pipeline_batch_ops[op.batch_id] = op
    return op


async def batch_delete_pipelines(pipeline_ids: list[str]) -> PipelineBatchOperation:
    op = PipelineBatchOperation(batch_id=str(uuid4()), operation="delete", item_ids=[], created_at=_ts())
    for pid in pipeline_ids:
        if await delete_pipeline(pid):
            op.item_ids.append(pid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"pipeline_id": pid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _pipeline_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[PipelineBatchOperation]:
    return _pipeline_batch_ops.get(batch_id)


async def export_pipeline_dag(pipeline_id: str) -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    return {
        "pipeline": {"name": p.name, "description": p.description, "owner": p.owner},
        "nodes": [{"name": n.name, "node_type": n.node_type.value, "source": n.source,
                     "sink": n.sink, "query": n.query, "config": n.config} for n in p.nodes],
        "edges": p.edges,
    }


async def import_pipeline_dag(data: dict) -> Pipeline:
    p = await create_pipeline(data["pipeline"]["name"], data["pipeline"].get("description", ""),
                               data["pipeline"].get("owner", ""))
    node_map = {}
    for nd in data.get("nodes", []):
        node = await add_node(p.pipeline_id, nd["name"], NodeType(nd["node_type"]),
                               nd.get("source", ""), nd.get("sink", ""), nd.get("query", ""), nd.get("config"))
        if node:
            node_map[nd["name"]] = node.node_id
    for edge in data.get("edges", []):
        from_id = node_map.get(edge.get("from"))
        to_id = node_map.get(edge.get("to"))
        if from_id and to_id:
            p.edges.append({"from": from_id, "to": to_id})
    return p


async def get_observability_analytics() -> dict:
    total = len(_pipelines)
    if total == 0:
        return {"total_pipelines": 0, "avg_throughput": 0, "avg_latency": 0, "avg_error_rate": 0}
    total_metrics = sum(len(m) for m in _metrics_history.values())
    latest_metrics = []
    for metrics_list in _metrics_history.values():
        if metrics_list:
            latest_metrics.append(metrics_list[-1])
    avg_throughput = sum(m.throughput_records_sec for m in latest_metrics) / max(len(latest_metrics), 1)
    avg_latency = sum(m.latency_ms for m in latest_metrics) / max(len(latest_metrics), 1)
    avg_error = sum(m.error_rate for m in latest_metrics) / max(len(latest_metrics), 1)
    return {
        "total_pipelines": total,
        "total_metrics_points": total_metrics,
        "total_alerts": len(_alerts),
        "running": sum(1 for p in _pipelines.values() if p.status == PipelineStatus.RUNNING),
        "failed": sum(1 for p in _pipelines.values() if p.status == PipelineStatus.FAILED),
        "avg_throughput_records_sec": round(avg_throughput, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_error_rate_pct": round(avg_error, 2),
        "healthy_pct": round(sum(1 for p in _pipelines.values() if p.status == PipelineStatus.RUNNING) / total * 100, 1),
    }


async def transition_pipeline_state(pipeline_id: str, trigger: str, actor: str = "system") -> dict:
    p = _pipelines.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    from_state = p.status.value
    valid_transitions = {
        "unknown": {"start"},
        "running": {"pause", "stop", "fail"},
        "paused": {"resume", "stop"},
        "completed": {"restart"},
        "failed": {"retry", "stop"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"pipeline_id": pipeline_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {
        "start": PipelineStatus.RUNNING, "pause": PipelineStatus.PAUSED,
        "stop": PipelineStatus.COMPLETED, "resume": PipelineStatus.RUNNING,
        "fail": PipelineStatus.FAILED, "retry": PipelineStatus.RUNNING,
        "restart": PipelineStatus.RUNNING,
    }
    new_status = to_state_map.get(trigger, p.status)
    p.status = new_status
    transition = PipelineStateTransition(from_state=from_state, to_state=new_status.value, trigger=trigger,
                                          pipeline_id=pipeline_id, timestamp=_ts(), actor=actor)
    _pipeline_state_history.setdefault(pipeline_id, []).append(transition)
    return {"pipeline_id": pipeline_id, "success": True, "from_state": from_state, "to_state": new_status.value}


async def get_pipeline_state_history(pipeline_id: str) -> list[PipelineStateTransition]:
    return _pipeline_state_history.get(pipeline_id, [])


async def validate_pipeline_config(pipe: Pipeline) -> dict:
    issues = []
    if not pipe.name:
        issues.append("Pipeline name is required")
    if not pipe.nodes:
        issues.append("Pipeline has no nodes")
    else:
        names = [n.name for n in pipe.nodes]
        if len(names) != len(set(names)):
            issues.append("Duplicate node names detected")
        has_source = any(n.node_type == NodeType.SOURCE for n in pipe.nodes)
        has_sink = any(n.node_type == NodeType.SINK for n in pipe.nodes)
        if not has_source:
            issues.append("Pipeline has no source node")
        if not has_sink:
            issues.append("Pipeline has no sink node")
    if pipe.edges:
        node_ids = set(n.node_id for n in pipe.nodes)
        for edge in pipe.edges:
            if edge.get("from") not in node_ids:
                issues.append(f"Edge references unknown source node: {edge.get('from')}")
            if edge.get("to") not in node_ids:
                issues.append(f"Edge references unknown target node: {edge.get('to')}")
    return {"pipeline_id": pipe.pipeline_id, "valid": len(issues) == 0, "issues": issues}


async def search_pipelines(query: str) -> list[Pipeline]:
    q = query.lower()
    return [p for p in _pipelines.values() if q in p.name.lower() or q in p.description.lower() or q in p.owner.lower()]


async def get_alert_trend(days: int = 7) -> list[dict]:
    from collections import defaultdict
    daily = defaultdict(int)
    cutoff = datetime.utcnow().timestamp() - days * 86400
    for a in _alerts:
        try:
            ts = datetime.fromisoformat(a.triggered_at.replace("Z", "+00:00")).timestamp()
            if ts > cutoff:
                day_key = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                daily[day_key] += 1
        except Exception:
            pass
    return [{"date": k, "count": v} for k, v in sorted(daily.items())]


async def get_metrics_summary() -> dict:
    all_metrics = []
    for mlist in _metrics_history.values():
        if mlist:
            all_metrics.append(mlist[-1])
    if not all_metrics:
        return {"pipelines_with_metrics": 0}
    return {
        "pipelines_with_metrics": len(all_metrics),
        "total_throughput": round(sum(m.throughput_records_sec for m in all_metrics), 2),
        "avg_latency_ms": round(sum(m.latency_ms for m in all_metrics) / len(all_metrics), 2),
        "avg_error_rate": round(sum(m.error_rate for m in all_metrics) / len(all_metrics), 2),
        "total_records_processed": sum(m.records_processed for m in all_metrics),
        "total_bytes_processed": sum(m.bytes_processed for m in all_metrics),
    }


async def bulk_retry_pipelines(pipeline_ids: list[str]) -> PipelineBatchOperation:
    op = PipelineBatchOperation(batch_id=str(uuid4()), operation="retry", item_ids=[], created_at=_ts())
    for pid in pipeline_ids:
        try:
            await retry_pipeline(pid)
            op.item_ids.append(pid)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"pipeline_id": pid, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _pipeline_batch_ops[op.batch_id] = op
    return op


class PipelineMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class PipelineCache:
    def __init__(self, ttl: int = 300):
        self._store: dict[str, dict] = {}
        self._ttl = ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry:
            from datetime import datetime
            age = (datetime.utcnow() - entry["ts"]).total_seconds()
            if age < self._ttl:
                return entry["val"]
        return None

    def set(self, key: str, val: Any):
        from datetime import datetime
        self._store[key] = {"val": val, "ts": datetime.utcnow()}

    def invalidate(self, key: str):
        self._store.pop(key, None)


class PipelineAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, detail: str = "") -> dict:
        from datetime import datetime
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


class PipelineTaskScheduler:
    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def schedule(self, pipeline_id: str, cron_expr: str) -> dict:
        entry = {"pipeline_id": pipeline_id, "cron": cron_expr, "active": True, "id": str(uuid4())}
        self._tasks[entry["id"]] = entry
        return entry

    def cancel(self, schedule_id: str) -> bool:
        entry = self._tasks.get(schedule_id)
        if entry:
            entry["active"] = False
            return True
        return False

    def list_active(self) -> list[dict]:
        return [t for t in self._tasks.values() if t["active"]]


async def get_pipeline_lineage(pipeline_id: str, depth: int = 3) -> dict:
    pipeline = _pipelines.get(pipeline_id)
    if not pipeline:
        return {"error": "pipeline not found"}
    nodes = []
    seen = set()

    async def walk(node_id: str, level: int):
        if level > depth or node_id in seen:
            return
        seen.add(node_id)
        for dep in _pipeline_lineage_map.get(node_id, []):
            nodes.append({"from": node_id, "to": dep, "level": level})
            await walk(dep, level + 1)

    await walk(pipeline_id, 0)
    return {"pipeline_id": pipeline_id, "lineage": nodes, "node_count": len(nodes)}


async def set_pipeline_alert(pipeline_id: str, metric: str, threshold: float) -> dict:
    alert = {"pipeline_id": pipeline_id, "metric": metric, "threshold": threshold, "id": str(uuid4())}
    _pipeline_alerts[alert["id"]] = alert
    return alert


async def list_pipeline_alerts() -> list[dict]:
    return list(_pipeline_alerts.values())

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
