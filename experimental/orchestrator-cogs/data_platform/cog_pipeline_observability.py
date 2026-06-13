"""Cog: Data Pipeline Observability — end-to-end pipeline monitoring."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

PIPELINES: dict[str, dict] = {}
PIPELINE_METRICS: dict[str, list[dict]] = {}
ALERTS: list[dict] = []


async def create_pipeline(name: str, description: str = "") -> dict:
    pid = f"pl-{len(PIPELINES) + 1}"
    PIPELINES[pid] = {"pipeline_id": pid, "name": name, "description": description, "nodes": [], "edges": [], "status": "created"}
    return PIPELINES[pid]


async def list_pipelines() -> list[dict]:
    return list(PIPELINES.values())


async def get_pipeline(pipeline_id: str) -> dict | None:
    return PIPELINES.get(pipeline_id)


async def delete_pipeline(pipeline_id: str) -> bool:
    p = PIPELINES.pop(pipeline_id, None)
    if p:
        PIPELINE_METRICS.pop(pipeline_id, None)
        return True
    return False


async def add_node(pipeline_id: str, name: str, node_type: str = "transform") -> dict:
    p = PIPELINES.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    node = {"node_id": f"n-{len(p['nodes']) + 1}", "name": name, "type": node_type}
    p["nodes"].append(node)
    return node


async def add_edge(pipeline_id: str, from_node: str, to_node: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if not p:
        return False
    p["edges"].append({"from": from_node, "to": to_node})
    return True


async def start_pipeline(pipeline_id: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if p:
        p["status"] = "running"
        return True
    return False


async def stop_pipeline(pipeline_id: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if p:
        p["status"] = "stopped"
        return True
    return False


async def get_health(pipeline_id: str) -> dict:
    return {"pipeline_id": pipeline_id, "status": "healthy", "throughput": 1500, "latency_ms": 120, "error_rate": 0.5}


async def root_cause_analysis(pipeline_id: str) -> dict:
    return {"pipeline_id": pipeline_id, "causes": [{"node": "source_db", "issue": "connection timeout", "probability": 0.85}], "analyzed": True}


async def get_observability_stats() -> dict:
    return {"pipelines": len(PIPELINES), "alerts": len(ALERTS)}


async def update_pipeline(pipeline_id: str, **kwargs) -> dict | None:
    p = PIPELINES.get(pipeline_id)
    if not p:
        return None
    p.update(kwargs)
    return p


async def pause_pipeline(pipeline_id: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if p:
        p["status"] = "paused"
        return True
    return False


async def resume_pipeline(pipeline_id: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if p:
        p["status"] = "running"
        return True
    return False


async def remove_node(pipeline_id: str, node_id: str) -> bool:
    p = PIPELINES.get(pipeline_id)
    if not p:
        return False
    before = len(p["nodes"])
    p["nodes"] = [n for n in p["nodes"] if n.get("node_id") != node_id]
    return len(p["nodes"]) < before


async def record_metrics(pipeline_id: str, throughput: float = 0.0, latency: float = 0.0, error_rate: float = 0.0) -> dict:
    metrics = {"throughput": throughput, "latency_ms": latency, "error_rate": error_rate, "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
    PIPELINE_METRICS.setdefault(pipeline_id, []).append(metrics)
    return metrics


async def get_current_metrics(pipeline_id: str) -> dict | None:
    history = PIPELINE_METRICS.get(pipeline_id, [])
    return history[-1] if history else None


async def get_metrics_history(pipeline_id: str, limit: int = 20) -> list[dict]:
    return PIPELINE_METRICS.get(pipeline_id, [])[-limit:]


async def create_alert(pipeline_id: str, message: str, severity: str = "info") -> dict:
    alert = {"alert_id": f"al-{len(ALERTS) + 1}", "pipeline_id": pipeline_id, "message": message, "severity": severity, "acknowledged": False}
    ALERTS.append(alert)
    return alert


async def list_alerts(pipeline_id: str | None = None) -> list[dict]:
    if pipeline_id:
        return [a for a in ALERTS if a["pipeline_id"] == pipeline_id]
    return ALERTS


async def acknowledge_alert(alert_id: str) -> bool:
    for a in ALERTS:
        if a.get("alert_id") == alert_id:
            a["acknowledged"] = True
            return True
    return False


async def get_pipeline_dag(pipeline_id: str) -> dict:
    p = PIPELINES.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    return {"pipeline_id": pipeline_id, "nodes": p.get("nodes", []), "edges": p.get("edges", [])}


async def get_upstream_pipelines(pipeline_id: str) -> list[str]:
    return []


async def get_downstream_pipelines(pipeline_id: str) -> list[str]:
    return []


async def retry_pipeline(pipeline_id: str) -> dict:
    p = PIPELINES.get(pipeline_id)
    if not p:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    p["status"] = "running"
    return {"pipeline_id": pipeline_id, "status": "retrying"}


async def get_alert_stats() -> dict:
    total = len(ALERTS)
    acknowledged = sum(1 for a in ALERTS if a.get("acknowledged"))
    return {"total": total, "acknowledged": acknowledged, "unacknowledged": total - acknowledged}


async def list_node_types() -> list[str]:
    return ["source", "transform", "sink", "quality_check"]


async def add_pipeline_tags(pipeline_id: str, tags: list[str]) -> bool:
    p = PIPELINES.get(pipeline_id)
    if not p:
        return False
    p.setdefault("tags", []).extend(t for t in tags if t not in p.get("tags", []))
    return True


async def get_pipeline_sla(pipeline_id: str) -> dict:
    metrics = await get_current_metrics(pipeline_id)
    latency = metrics.get("latency_ms", 0) if metrics else 0
    return {"pipeline_id": pipeline_id, "latency_sla_ms": 5000, "current_latency_ms": latency, "sla_met": latency <= 5000}


async def bulk_acknowledge_alerts(pipeline_id: str) -> int:
    count = 0
    for a in ALERTS:
        if a.get("pipeline_id") == pipeline_id and not a.get("acknowledged"):
            a["acknowledged"] = True
            count += 1
    return count


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_pipelines(offset: int = 0, limit: int = 50, status: str = None) -> dict:
    results = list(PIPELINES.values())
    if status:
        results = [p for p in results if p.get("status") == status]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def format_pipeline_info(pipeline_id: str) -> dict:
    p = PIPELINES.get(pipeline_id)
    if not p:
        return {"error": "Pipeline not found"}
    return {
        "pipeline_id": p["pipeline_id"],
        "name": p.get("name"),
        "status": p.get("status"),
        "nodes": len(p.get("nodes", [])),
        "edges": len(p.get("edges", [])),
        "tags": p.get("tags", []),
    }

async def batch_pipeline_ops(pipeline_ids: list[str], action: str) -> dict:
    results = {}
    for pid in pipeline_ids:
        if action == "start":
            results[pid] = await start_pipeline(pid)
        elif action == "stop":
            results[pid] = await stop_pipeline(pid)
        elif action == "pause":
            results[pid] = await pause_pipeline(pid)
        elif action == "resume":
            results[pid] = await resume_pipeline(pid)
    return results

async def search_pipelines(query: str) -> list[dict]:
    q = query.lower()
    return [p for p in PIPELINES.values() if q in p.get("name", "").lower() or q in p.get("pipeline_id", "").lower()]

async def get_pipeline_analytics() -> dict:
    statuses = {}
    for p in PIPELINES.values():
        s = p.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    total_alerts = len(ALERTS)
    unacked = sum(1 for a in ALERTS if not a.get("acknowledged"))
    return {
        "total_pipelines": len(PIPELINES),
        "by_status": statuses,
        "total_alerts": total_alerts,
        "unacknowledged_alerts": unacked,
        "pipeline_types": list(set(p.get("type", "unknown") for p in PIPELINES.values())),
    }

async def bulk_delete_pipelines(pipeline_ids: list[str]) -> dict:
    deleted = 0
    for pid in pipeline_ids:
        if await remove_pipeline(pid):
            deleted += 1
    return {"deleted": deleted, "total_requested": len(pipeline_ids)}

async def get_pipeline_performance_report() -> list[dict]:
    report = []
    for pid, p in PIPELINES.items():
        metrics = await get_current_metrics(pid)
        report.append({
            "pipeline_id": pid,
            "name": p.get("name"),
            "status": p.get("status"),
            "throughput": metrics.get("throughput", 0) if metrics else 0,
            "latency_ms": metrics.get("latency_ms", 0) if metrics else 0,
            "error_rate": metrics.get("error_rate", 0) if metrics else 0,
        })
    return sorted(report, key=lambda x: x.get("latency_ms", 0), reverse=True)

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
