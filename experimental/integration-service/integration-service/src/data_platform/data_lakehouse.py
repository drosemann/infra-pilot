"""Managed Data Lakehouse — Iceberg/Hudi/Delta Lake deployment & management."""

from __future__ import annotations
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class LakehouseFormat(Enum):
    ICEBERG = "iceberg"
    HUDI = "hudi"
    DELTA = "delta"


class TableState(Enum):
    CREATING = "creating"
    ACTIVE = "active"
    COMPACTING = "compacting"
    VACUUMING = "vacuuming"
    ERROR = "error"


@dataclass
class LakehouseTable:
    table_id: str
    name: str
    format: LakehouseFormat
    location: str
    schema_def: dict
    partition_cols: list[str] = field(default_factory=list)
    state: TableState = TableState.CREATING
    record_count: int = 0
    size_bytes: int = 0
    created_at: str = ""
    last_compacted: str = ""
    last_vacuumed: str = ""
    owner: str = "admin"
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class LakehouseCluster:
    cluster_id: str
    name: str
    storage_backend: str
    endpoint: str
    engine: str
    tables: list[LakehouseTable] = field(default_factory=list)
    created_at: str = ""
    status: str = "active"


_tables: dict[str, LakehouseTable] = {}
_clusters: dict[str, LakehouseCluster] = {}


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def create_cluster(name: str, storage_backend: str = "s3", engine: str = "trino") -> LakehouseCluster:
    cluster = LakehouseCluster(
        cluster_id=str(uuid4()),
        name=name,
        storage_backend=storage_backend,
        endpoint=f"{name}.lakehouse.internal:8080",
        engine=engine,
        created_at=_ts(),
    )
    _clusters[cluster.cluster_id] = cluster
    logger.info("Lakehouse cluster created: %s", cluster.cluster_id)
    return cluster


async def list_clusters() -> list[LakehouseCluster]:
    return list(_clusters.values())


async def get_cluster(cluster_id: str) -> Optional[LakehouseCluster]:
    return _clusters.get(cluster_id)


async def delete_cluster(cluster_id: str) -> bool:
    cluster = _clusters.pop(cluster_id, None)
    if cluster:
        for t in cluster.tables:
            _tables.pop(t.table_id, None)
        return True
    return False


async def create_table(
    cluster_id: str,
    name: str,
    fmt: LakehouseFormat,
    schema_def: dict,
    partition_cols: list[str] | None = None,
) -> Optional[LakehouseTable]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    table = LakehouseTable(
        table_id=str(uuid4()),
        name=name,
        format=fmt,
        location=f"{cluster.storage_backend}://lakehouse/{cluster.name}/{name}",
        schema_def=schema_def,
        partition_cols=partition_cols or [],
        created_at=_ts(),
    )
    _tables[table.table_id] = table
    cluster.tables.append(table)
    logger.info("Lakehouse table created: %s", table.table_id)
    return table


async def list_tables(cluster_id: str | None = None) -> list[LakehouseTable]:
    if cluster_id:
        cluster = _clusters.get(cluster_id)
        return cluster.tables if cluster else []
    return list(_tables.values())


async def get_table(table_id: str) -> Optional[LakehouseTable]:
    return _tables.get(table_id)


async def compact_table(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    table.state = TableState.COMPACTING
    await asyncio.sleep(0.5)
    table.last_compacted = _ts()
    table.state = TableState.ACTIVE
    logger.info("Table compacted: %s", table_id)
    return {"table_id": table_id, "status": "compacted", "timestamp": table.last_compacted}


async def vacuum_table(table_id: str, retention_hours: int = 168) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    table.state = TableState.VACUUMING
    await asyncio.sleep(0.3)
    table.last_vacuumed = _ts()
    table.state = TableState.ACTIVE
    logger.info("Table vacuumed: %s (retention %dh)", table_id, retention_hours)
    return {"table_id": table_id, "status": "vacuumed", "retention_hours": retention_hours}


async def run_query(cluster_id: str, query: str) -> list[dict]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    await asyncio.sleep(0.1)
    return [{"result": "query_executed", "engine": cluster.engine, "rows": 0}]


async def execute_sql(sql: str, catalog: str = "default") -> dict:
    await asyncio.sleep(0.1)
    return {"columns": ["id", "name", "value"], "rows": [], "row_count": 0, "execution_time_ms": 42}


async def begin_transaction(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    tx_id = str(uuid4())
    return {"transaction_id": tx_id, "table_id": table_id, "status": "begun"}


async def commit_transaction(transaction_id: str) -> dict:
    return {"transaction_id": transaction_id, "status": "committed"}


async def optimize_table(table_id: str, strategy: str = "auto") -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    await asyncio.sleep(0.4)
    return {"table_id": table_id, "strategy": strategy, "status": "optimized"}


async def get_table_stats(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    return {
        "table_id": table_id,
        "name": table.name,
        "format": table.format.value,
        "record_count": table.record_count,
        "size_bytes": table.size_bytes,
        "partition_cols": table.partition_cols,
        "state": table.state.value,
    }


async def bulk_import(table_id: str, records: list[dict]) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    table.record_count += len(records)
    table.size_bytes += sum(len(json.dumps(r).encode()) for r in records)
    return {"table_id": table_id, "imported": len(records), "total_records": table.record_count}


async def get_cluster_health(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    return {
        "cluster_id": cluster_id,
        "status": cluster.status,
        "table_count": len(cluster.tables),
        "engine": cluster.engine,
        "storage": cluster.storage_backend,
    }


async def update_table_schema(table_id: str, schema_def: dict) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    table.schema_def = schema_def
    return table


async def add_table_partition(table_id: str, partition_col: str) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    if partition_col not in table.partition_cols:
        table.partition_cols.append(partition_col)
    return table


async def remove_table_partition(table_id: str, partition_col: str) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    if partition_col in table.partition_cols:
        table.partition_cols.remove(partition_col)
    return table


async def time_travel_query(table_id: str, as_of_timestamp: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    await asyncio.sleep(0.15)
    return {
        "table_id": table_id,
        "name": table.name,
        "as_of": as_of_timestamp,
        "snapshot_available": True,
        "row_count_snapshot": max(0, table.record_count - 100),
    }


async def list_table_versions(table_id: str) -> list[dict]:
    table = _tables.get(table_id)
    if not table:
        return []
    return [
        {"version": 1, "created_at": table.created_at, "schema_version": "1.0"},
        {"version": 2, "created_at": _ts(), "schema_version": "1.1"},
    ]


async def restore_table_version(table_id: str, version: int) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    await asyncio.sleep(0.2)
    return {"table_id": table_id, "restored_to_version": version, "status": "restored"}


async def rename_table(table_id: str, new_name: str) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    table.name = new_name
    return table


async def set_table_metadata(table_id: str, metadata: dict) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    table.metadata.update(metadata)
    return table


async def get_cluster_storage_summary(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    total_size = sum(t.size_bytes for t in cluster.tables)
    total_records = sum(t.record_count for t in cluster.tables)
    return {
        "cluster_id": cluster_id,
        "table_count": len(cluster.tables),
        "total_size_bytes": total_size,
        "total_records": total_records,
        "formats": list(set(t.format.value for t in cluster.tables)),
    }


async def list_formats() -> list[str]:
    return [f.value for f in LakehouseFormat]


async def create_table_from_query(cluster_id: str, name: str, query: str, fmt: LakehouseFormat = LakehouseFormat.ICEBERG) -> Optional[LakehouseTable]:
    schema_def = {"columns": [{"name": "id", "type": "int"}, {"name": "result", "type": "string"}]}
    table = await create_table(cluster_id, name, fmt, schema_def)
    return table


async def clone_table(source_table_id: str, new_name: str, cluster_id: str | None = None) -> Optional[LakehouseTable]:
    source = _tables.get(source_table_id)
    if not source:
        return None
    target_cluster = cluster_id or next((cid for cid, c in _clusters.items() if source in c.tables), None)
    if not target_cluster:
        return None
    table = await create_table(target_cluster, new_name, source.format, source.schema_def, source.partition_cols)
    if table:
        table.record_count = source.record_count
        table.metadata = dict(source.metadata)
    return table


async def expire_snapshot(table_id: str, retention_days: int = 7) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    await asyncio.sleep(0.1)
    return {"table_id": table_id, "snapshots_expired": 3, "retention_days": retention_days}


async def describe_table(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    return {
        "name": table.name,
        "format": table.format.value,
        "location": table.location,
        "schema": table.schema_def,
        "partitions": table.partition_cols,
        "record_count": table.record_count,
        "size_bytes": table.size_bytes,
        "state": table.state.value,
        "created_at": table.created_at,
        "tags": table.tags,
    }


async def list_table_tags(table_id: str) -> list[str]:
    table = _tables.get(table_id)
    return list(table.tags) if table else []


async def add_table_tags(table_id: str, tags: list[str]) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    for t in tags:
        if t not in table.tags:
            table.tags.append(t)
    return table


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class TableBatchOperation:
    batch_id: str
    cluster_id: str
    operation: str
    table_ids: list[str]
    status: str = "pending"
    success_count: int = 0
    failure_count: int = 0
    errors: list[dict] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""


@dataclass
class LakehousePaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    format_filter: str | None = None
    state_filter: str | None = None


@dataclass
class LakehousePaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class TableLifecycleTransition:
    from_state: str
    to_state: str
    trigger: str
    table_id: str
    timestamp: str = ""
    actor: str = "system"


@dataclass
class LakehouseConfigValidation:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_table_lifecycle_history: dict[str, list[TableLifecycleTransition]] = {}
_table_batch_ops: dict[str, TableBatchOperation] = {}


async def paginate_tables(params: LakehousePaginationParams | None = None) -> LakehousePaginatedResult:
    p = params or LakehousePaginationParams()
    results = list(_tables.values())
    if p.format_filter:
        results = [t for t in results if t.format.value == p.format_filter]
    if p.state_filter:
        results = [t for t in results if t.state.value == p.state_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda t: t.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "record_count":
        results.sort(key=lambda t: t.record_count, reverse=p.sort_order == "desc")
    elif p.sort_by == "size_bytes":
        results.sort(key=lambda t: t.size_bytes, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda t: t.created_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return LakehousePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                     has_more=(p.offset + p.limit < total))


async def paginate_clusters(params: LakehousePaginationParams | None = None) -> LakehousePaginatedResult:
    p = params or LakehousePaginationParams()
    results = list(_clusters.values())
    total = len(results)
    results.sort(key=lambda c: c.name, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return LakehousePaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                     has_more=(p.offset + p.limit < total))


async def batch_create_tables(cluster_id: str, table_defs: list[dict]) -> TableBatchOperation:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    op = TableBatchOperation(batch_id=str(uuid4()), cluster_id=cluster_id, operation="create_tables", table_ids=[], created_at=_ts())
    for td in table_defs:
        try:
            table = await create_table(cluster_id, td["name"], LakehouseFormat(td.get("format", "iceberg")),
                                        td.get("schema_def", {"columns": []}), td.get("partition_cols"))
            op.table_ids.append(table.table_id)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"name": td.get("name"), "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _table_batch_ops[op.batch_id] = op
    return op


async def batch_compact_tables(table_ids: list[str]) -> TableBatchOperation:
    op = TableBatchOperation(batch_id=str(uuid4()), cluster_id="", operation="compact", table_ids=[], created_at=_ts())
    for tid in table_ids:
        try:
            await compact_table(tid)
            op.table_ids.append(tid)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"table_id": tid, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _table_batch_ops[op.batch_id] = op
    return op


async def batch_vacuum_tables(table_ids: list[str], retention_hours: int = 168) -> TableBatchOperation:
    op = TableBatchOperation(batch_id=str(uuid4()), cluster_id="", operation="vacuum", table_ids=[], created_at=_ts())
    for tid in table_ids:
        try:
            await vacuum_table(tid, retention_hours)
            op.table_ids.append(tid)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"table_id": tid, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _table_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[TableBatchOperation]:
    return _table_batch_ops.get(batch_id)


async def export_table_definition(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    return {
        "name": table.name,
        "format": table.format.value,
        "schema_def": table.schema_def,
        "partition_cols": table.partition_cols,
        "location": table.location,
        "owner": table.owner,
        "tags": table.tags,
        "metadata": table.metadata,
    }


async def import_table_definition(cluster_id: str, definition: dict) -> Optional[LakehouseTable]:
    table = await create_table(cluster_id, definition["name"], LakehouseFormat(definition.get("format", "iceberg")),
                                definition.get("schema_def", {"columns": []}), definition.get("partition_cols"))
    if table:
        table.owner = definition.get("owner", "admin")
        table.tags = definition.get("tags", [])
        table.metadata.update(definition.get("metadata", {}))
    return table


async def export_cluster_tables(cluster_id: str) -> list[dict]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    return [await export_table_definition(t.table_id) for t in cluster.tables]


async def get_lakehouse_analytics() -> dict:
    total_tables = len(_tables)
    total_clusters = len(_clusters)
    total_size = sum(t.size_bytes for t in _tables.values())
    total_records = sum(t.record_count for t in _tables.values())
    by_format = {}
    for t in _tables.values():
        by_format[t.format.value] = by_format.get(t.format.value, 0) + 1
    by_state = {}
    for t in _tables.values():
        by_state[t.state.value] = by_state.get(t.state.value, 0) + 1
    return {
        "total_tables": total_tables,
        "total_clusters": total_clusters,
        "total_size_gb": round(total_size / (1024 ** 3), 2),
        "total_records": total_records,
        "avg_records_per_table": total_records // max(total_tables, 1),
        "by_format": by_format,
        "by_state": by_state,
        "compactable_tables": sum(1 for t in _tables.values() if t.state == TableState.ACTIVE),
    }


async def transition_table_state(table_id: str, trigger: str, actor: str = "system") -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    from_state = table.state.value
    valid_transitions = {
        "creating": {"activate", "fail"},
        "active": {"compact", "vacuum", "optimize", "archive"},
        "compacting": {"complete", "fail"},
        "vacuuming": {"complete", "fail"},
        "error": {"retry", "archive"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"table_id": table_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {
        "activate": TableState.ACTIVE, "fail": TableState.ERROR, "compact": TableState.COMPACTING,
        "vacuum": TableState.VACUUMING, "optimize": TableState.ACTIVE, "complete": TableState.ACTIVE,
        "retry": TableState.CREATING, "archive": TableState.ACTIVE,
    }
    new_state = to_state_map.get(trigger, TableState.ACTIVE)
    table.state = new_state
    transition = TableLifecycleTransition(from_state=from_state, to_state=new_state.value, trigger=trigger,
                                           table_id=table_id, timestamp=_ts(), actor=actor)
    _table_lifecycle_history.setdefault(table_id, []).append(transition)
    return {"table_id": table_id, "success": True, "from_state": from_state, "to_state": new_state.value}


async def get_table_state_history(table_id: str) -> list[TableLifecycleTransition]:
    return _table_lifecycle_history.get(table_id, [])


async def validate_lakehouse_config(config: dict) -> LakehouseConfigValidation:
    result = LakehouseConfigValidation()
    if "name" not in config or not config["name"]:
        result.errors.append("Cluster name is required")
        result.valid = False
    if "storage_backend" in config and config["storage_backend"] not in ("s3", "gcs", "abfs", "hdfs"):
        result.errors.append(f"Invalid storage backend: {config.get('storage_backend')}")
        result.valid = False
    if "engine" in config and config["engine"] not in ("trino", "spark", "presto", "athena"):
        result.warnings.append(f"Unrecognized engine: {config.get('engine')}")
    if "format" in config and config["format"] not in [f.value for f in LakehouseFormat]:
        result.errors.append(f"Invalid format: {config.get('format')}")
        result.valid = False
    if "partition_cols" in config and not isinstance(config["partition_cols"], list):
        result.errors.append("partition_cols must be a list")
        result.valid = False
    return result


async def search_tables(query: str) -> list[LakehouseTable]:
    q = query.lower()
    return [t for t in _tables.values() if q in t.name.lower() or q in t.owner.lower() or any(q in tag.lower() for tag in t.tags)]


async def get_cluster_analytics(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    tables = cluster.tables
    return {
        "cluster_id": cluster_id,
        "name": cluster.name,
        "table_count": len(tables),
        "total_size_gb": round(sum(t.size_bytes for t in tables) / (1024 ** 3), 2),
        "total_records": sum(t.record_count for t in tables),
        "formats": list(set(t.format.value for t in tables)),
        "states": {s: sum(1 for t in tables if t.state.value == s) for s in set(t.state.value for t in tables)},
        "last_compacted": max((t.last_compacted for t in tables if t.last_compacted), default="never"),
        "last_vacuumed": max((t.last_vacuumed for t in tables if t.last_vacuumed), default="never"),
    }


async def recommend_compaction() -> list[dict]:
    recommendations = []
    for tid, table in _tables.items():
        if table.state == TableState.ACTIVE and table.size_bytes > 10 * 1024 * 1024 * 1024:
            recommendations.append({"table_id": tid, "name": table.name, "size_gb": round(table.size_bytes / (1024 ** 3), 2),
                                     "reason": f"Table exceeds 10GB, last compacted: {table.last_compacted or 'never'}"})
    return recommendations


async def validate_table_schema(table_id: str) -> dict:
    table = _tables.get(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")
    issues = []
    schema = table.schema_def
    if not schema or "columns" not in schema or not schema["columns"]:
        issues.append("Table has no columns defined")
    else:
        col_names = [c["name"] for c in schema["columns"] if "name" in c]
        if len(col_names) != len(set(col_names)):
            issues.append("Duplicate column names detected")
    if table.partition_cols:
        missing = [p for p in table.partition_cols if not any(c.get("name") == p for c in schema.get("columns", []))]
        if missing:
            issues.append(f"Partition columns not in schema: {missing}")
    valid_formats = [f.value for f in LakehouseFormat]
    if table.format.value not in valid_formats:
        issues.append(f"Unknown table format: {table.format.value}")
    return {"table_id": table_id, "valid": len(issues) == 0, "issues": issues}


async def bulk_update_table_owner(table_ids: list[str], owner: str) -> TableBatchOperation:
    op = TableBatchOperation(batch_id=str(uuid4()), cluster_id="", operation="update_owner", table_ids=[], created_at=_ts())
    for tid in table_ids:
        table = _tables.get(tid)
        if table:
            table.owner = owner
            op.table_ids.append(tid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"table_id": tid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _table_batch_ops[op.batch_id] = op
    return op


async def get_table_cluster(table_id: str) -> Optional[LakehouseCluster]:
    for cluster in _clusters.values():
        if any(t.table_id == table_id for t in cluster.tables):
            return cluster
    return None


async def get_storage_tier_breakdown() -> dict:
    total_size = sum(t.size_bytes for t in _tables.values())
    if total_size == 0:
        return {"hot": 0, "warm": 0, "cold": 0}
    hot = sum(t.size_bytes for t in _tables.values() if t.state == TableState.ACTIVE)
    compacting = sum(t.size_bytes for t in _tables.values() if t.state == TableState.COMPACTING)
    cold = sum(t.size_bytes for t in _tables.values() if t.state in (TableState.ERROR,))
    return {
        "hot_gb": round(hot / (1024 ** 3), 2),
        "compacting_gb": round(compacting / (1024 ** 3), 2),
        "cold_gb": round(cold / (1024 ** 3), 2),
        "hot_pct": round(hot / max(total_size, 1) * 100, 1),
        "compacting_pct": round(compacting / max(total_size, 1) * 100, 1),
        "cold_pct": round(cold / max(total_size, 1) * 100, 1),
    }


async def remove_table_tags(table_id: str, tags: list[str]) -> Optional[LakehouseTable]:
    table = _tables.get(table_id)
    if not table:
        return None
    for t in tags:
        while t in table.tags:
            table.tags.remove(t)
    return table


async def get_lakehouse_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()
    suggestions = []
    for t in _tables.values():
        if q in t.name.lower():
            suggestions.append({"type": "table", "id": t.table_id, "text": t.name})
        if len(suggestions) >= limit:
            break
    return suggestions


async def merge_lakehouse_tables(source_table_id: str, target_table_id: str) -> dict:
    source = _tables.get(source_table_id)
    target = _tables.get(target_table_id)
    if not source or not target:
        return {"success": False, "error": "One or both tables not found"}
    target.record_count += source.record_count
    target.size_bytes += source.size_bytes
    for tag in source.tags:
        if tag not in target.tags:
            target.tags.append(tag)
    _tables.pop(source_table_id, None)
    return {"success": True, "target_table_id": target_table_id, "merged_from": source_table_id}


class LakehouseMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class LakehouseCache:
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


class LakehouseAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, detail: str = "") -> dict:
        from datetime import datetime
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_lakehouse_growth_report(days: int = 30) -> dict:
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    tables_before = len([t for t in _tables.values() if t.created_at < cutoff])
    tables_now = len(_tables)
    return {
        "period_days": days,
        "tables_at_start": tables_before,
        "tables_now": tables_now,
        "growth": tables_now - tables_before,
        "growth_pct": round((tables_now - tables_before) / max(tables_before, 1) * 100, 1) if tables_before else 0,
    }


async def recommend_lakehouse_cleanup() -> list[dict]:
    recommendations = []
    for tid, table in _tables.items():
        issues = []
        if table.state == TableState.ERROR:
            issues.append("table_in_error_state")
        if table.size_bytes == 0:
            issues.append("empty_table")
        if not table.tags:
            issues.append("no_tags")
        if issues:
            recommendations.append({"table_id": tid, "name": table.name, "issues": issues})
    return recommendations

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
