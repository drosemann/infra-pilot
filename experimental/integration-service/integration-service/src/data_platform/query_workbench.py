"""Analytics Query Workbench — SQL editor, schema browser, query history."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class QueryStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SavedQuery:
    query_id: str
    name: str
    sql: str
    database: str
    status: QueryStatus = QueryStatus.PENDING
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    execution_time_ms: float = 0.0
    row_count: int = 0
    is_shared: bool = False
    share_url: str = ""


@dataclass
class QueryResult:
    result_id: str
    query_id: str
    columns: list[dict]
    rows: list[list]
    row_count: int
    execution_time_ms: float
    completed_at: str = ""


@dataclass
class ScheduledReport:
    schedule_id: str
    query_id: str
    cron: str
    recipients: list[str]
    format: str
    enabled: bool = True
    last_run: str = ""
    next_run: str = ""


@dataclass
class SchemaObject:
    name: str
    object_type: str
    database: str
    schema_name: str
    columns: list[dict] = field(default_factory=list)
    row_count: int = 0
    size_bytes: int = 0


_queries: dict[str, SavedQuery] = {}
_results: dict[str, QueryResult] = {}
_schedules: dict[str, ScheduledReport] = {}
_schema_objects: dict[str, SchemaObject] = {}


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def execute_query(sql: str, database: str = "default", user: str = "anonymous") -> QueryResult:
    q = SavedQuery(
        query_id=str(uuid4()),
        name=f"Query {len(_queries) + 1}",
        sql=sql,
        database=database,
        created_by=user,
        created_at=_ts(),
    )
    _queries[q.query_id] = q
    q.status = QueryStatus.RUNNING
    await asyncio.sleep(0.2)
    import random
    row_count = random.randint(10, 1000)
    elapsed = round(random.uniform(0.05, 2.0), 2)
    columns = [{"name": "id", "type": "int"}, {"name": "name", "type": "varchar"}, {"name": "value", "type": "float"}]
    rows = [[i, f"row-{i}", round(random.random() * 100, 2)] for i in range(min(row_count, 20))]
    q.status = QueryStatus.COMPLETED
    q.execution_time_ms = elapsed * 1000
    q.row_count = row_count
    result = QueryResult(
        result_id=str(uuid4()),
        query_id=q.query_id,
        columns=columns,
        rows=rows,
        row_count=row_count,
        execution_time_ms=elapsed * 1000,
        completed_at=_ts(),
    )
    _results[q.query_id] = result
    return result


async def get_query(query_id: str) -> Optional[SavedQuery]:
    return _queries.get(query_id)


async def list_queries(user: str | None = None, database: str | None = None) -> list[SavedQuery]:
    results = list(_queries.values())
    if user:
        results = [q for q in results if q.created_by == user]
    if database:
        results = [q for q in results if q.database == database]
    return sorted(results, key=lambda q: q.created_at, reverse=True)[:100]


async def save_query(name: str, sql: str, database: str, created_by: str = "", tags: list[str] | None = None, description: str = "") -> SavedQuery:
    q = SavedQuery(
        query_id=str(uuid4()),
        name=name,
        sql=sql,
        database=database,
        created_by=created_by,
        tags=tags or [],
        description=description,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _queries[q.query_id] = q
    return q


async def update_query(query_id: str, **kwargs) -> Optional[SavedQuery]:
    q = _queries.get(query_id)
    if not q:
        return None
    for k, v in kwargs.items():
        if hasattr(q, k):
            setattr(q, k, v)
    q.updated_at = _ts()
    return q


async def delete_query(query_id: str) -> bool:
    q = _queries.pop(query_id, None)
    if q:
        _results.pop(query_id, None)
        return True
    return False


async def share_query(query_id: str) -> str:
    q = _queries.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    q.is_shared = True
    q.share_url = f"/shared/queries/{query_id}"
    return q.share_url


async def get_result(result_id: str) -> Optional[QueryResult]:
    for qid, r in _results.items():
        if r.result_id == result_id:
            return r
    return None


async def get_query_result(query_id: str) -> Optional[QueryResult]:
    return _results.get(query_id)


async def create_schedule(query_id: str, cron: str, recipients: list[str], format: str = "csv") -> ScheduledReport:
    q = _queries.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    schedule = ScheduledReport(
        schedule_id=str(uuid4()),
        query_id=query_id,
        cron=cron,
        recipients=recipients,
        format=format,
    )
    _schedules[schedule.schedule_id] = schedule
    return schedule


async def list_schedules() -> list[ScheduledReport]:
    return list(_schedules.values())


async def delete_schedule(schedule_id: str) -> bool:
    return _schedules.pop(schedule_id, None) is not None


async def refresh_schema(database: str) -> list[SchemaObject]:
    await asyncio.sleep(0.1)
    objects = [
        SchemaObject(name="users", object_type="table", database=database, schema_name="public",
                     columns=[{"name": "id", "type": "integer"}, {"name": "name", "type": "varchar"}, {"name": "email", "type": "varchar"}]),
        SchemaObject(name="orders", object_type="table", database=database, schema_name="public",
                     columns=[{"name": "id", "type": "integer"}, {"name": "user_id", "type": "integer"}, {"name": "amount", "type": "decimal"}, {"name": "created_at", "type": "timestamp"}]),
        SchemaObject(name="get_user_stats", object_type="function", database=database, schema_name="public",
                     columns=[{"name": "user_id", "type": "integer"}]),
    ]
    for o in objects:
        _schema_objects[f"{database}.{o.schema_name}.{o.name}"] = o
    return objects


async def get_schema(database: str) -> list[SchemaObject]:
    return [o for o in _schema_objects.values() if o.database == database]


async def cancel_query(query_id: str) -> bool:
    q = _queries.get(query_id)
    if not q or q.status == QueryStatus.COMPLETED:
        return False
    q.status = QueryStatus.CANCELLED
    return True


async def get_query_stats() -> dict:
    total = len(_queries)
    completed = sum(1 for q in _queries.values() if q.status == QueryStatus.COMPLETED)
    failed = sum(1 for q in _queries.values() if q.status == QueryStatus.FAILED)
    running = sum(1 for q in _queries.values() if q.status == QueryStatus.RUNNING)
    return {"total_queries": total, "completed": completed, "failed": failed, "running": running}


async def format_query(sql: str) -> str:
    await asyncio.sleep(0.05)
    return sql.strip()


async def validate_sql(sql: str) -> dict:
    await asyncio.sleep(0.1)
    errors = []
    sql_upper = sql.upper().strip()
    if not sql_upper:
        errors.append({"line": 0, "message": "Empty query"})
    if "SELECT" not in sql_upper and "WITH" not in sql_upper:
        errors.append({"line": 0, "message": "Query must contain SELECT or WITH"})
    return {"valid": len(errors) == 0, "errors": errors, "query_length": len(sql)}


async def share_query_by_email(query_id: str, emails: list[str]) -> dict:
    q = _queries.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    q.is_shared = True
    q.share_url = f"/shared/queries/{query_id}"
    return {"query_id": query_id, "shared_with": emails, "share_url": q.share_url, "status": "shared"}


async def fork_query(query_id: str, new_name: str, user: str = "anonymous") -> Optional[SavedQuery]:
    original = _queries.get(query_id)
    if not original:
        return None
    forked = SavedQuery(
        query_id=str(uuid4()),
        name=new_name,
        sql=original.sql,
        database=original.database,
        created_by=user,
        tags=list(original.tags),
        description=f"Forked from {original.name}",
        created_at=_ts(),
        updated_at=_ts(),
    )
    _queries[forked.query_id] = forked
    return forked


async def export_results(result_id: str, format: str = "csv") -> str:
    result = await get_result(result_id)
    if not result:
        raise ValueError(f"Result {result_id} not found")
    filename = f"/exports/queries/{result_id}.{format}"
    return filename


async def get_schema_object(key: str) -> Optional[SchemaObject]:
    return _schema_objects.get(key)


async def search_schema(query: str) -> list[SchemaObject]:
    q = query.lower()
    return [o for o in _schema_objects.values() if q in o.name.lower() or q in o.database.lower()]


async def get_query_suggestions(sql_fragment: str) -> list[str]:
    await asyncio.sleep(0.05)
    fragment = sql_fragment.upper().strip()
    suggestions = []
    if fragment.startswith("SEL"):
        suggestions.append("SELECT * FROM table_name")
        suggestions.append("SELECT column1, column2 FROM table_name WHERE condition")
    elif fragment.startswith("FROM"):
        suggestions.append("FROM users u JOIN orders o ON u.id = o.user_id")
    elif fragment.startswith("WHERE"):
        suggestions.append("WHERE status = 'active' AND created_at > NOW() - INTERVAL '7 days'")
    else:
        suggestions.append("SELECT ... FROM ... WHERE ...")
        suggestions.append("WITH cte AS (SELECT ...) SELECT ...")
    return suggestions


async def get_recent_queries(user: str | None = None, limit: int = 10) -> list[SavedQuery]:
    results = list(_queries.values())
    if user:
        results = [q for q in results if q.created_by == user]
    return sorted(results, key=lambda q: q.created_at, reverse=True)[:limit]


async def tag_query(query_id: str, tags: list[str]) -> Optional[SavedQuery]:
    q = _queries.get(query_id)
    if not q:
        return None
    for t in tags:
        if t not in q.tags:
            q.tags.append(t)
    return q


async def untag_query(query_id: str, tags: list[str]) -> Optional[SavedQuery]:
    q = _queries.get(query_id)
    if not q:
        return None
    for t in tags:
        while t in q.tags:
            q.tags.remove(t)
    return q


async def list_databases() -> list[str]:
    databases = set(o.database for o in _schema_objects.values())
    if not databases:
        return ["default", "analytics", "reporting"]
    return list(databases)


async def autocomplete_sql(prefix: str) -> list[str]:
    await asyncio.sleep(0.05)
    p = prefix.upper()
    suggestions = []
    if "SELECT" in p:
        suggestions.append("SELECT column1, column2")
    if "FROM" in p:
        suggestions.append("FROM table_name")
    if "WHERE" in p:
        suggestions.append("WHERE condition = value")
    if "JOIN" in p:
        suggestions.append("JOIN other_table ON key = foreign_key")
    if "GROUP BY" in p:
        suggestions.append("GROUP BY column1")
    if "ORDER BY" in p:
        suggestions.append("ORDER BY column1 DESC")
    if "LIMIT" in p:
        suggestions.append("LIMIT 100")
    return suggestions


async def get_popular_queries(limit: int = 5) -> list[SavedQuery]:
    sorted_queries = sorted(_queries.values(), key=lambda q: q.execution_time_ms, reverse=True)
    return sorted_queries[:limit]


async def explain_query(sql: str) -> dict:
    await asyncio.sleep(0.1)
    return {
        "query_type": "SELECT",
        "estimated_cost": "medium",
        "tables_involved": ["users", "orders"],
        "indexes_used": ["users_pkey", "orders_user_id_idx"],
        "estimated_rows": 1500,
    }


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class QueryBatchOperation:
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
class QueryPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"
    status_filter: str | None = None
    database_filter: str | None = None
    user_filter: str | None = None


@dataclass
class QueryPaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class QueryStateTransition:
    from_state: str
    to_state: str
    trigger: str
    query_id: str
    timestamp: str = ""
    actor: str = "system"


_query_batch_ops: dict[str, QueryBatchOperation] = {}
_query_state_history: dict[str, list[QueryStateTransition]] = {}


async def paginate_queries(params: QueryPaginationParams | None = None) -> QueryPaginatedResult:
    p = params or QueryPaginationParams()
    results = list(_queries.values())
    if p.status_filter:
        results = [q for q in results if q.status.value == p.status_filter]
    if p.database_filter:
        results = [q for q in results if q.database == p.database_filter]
    if p.user_filter:
        results = [q for q in results if q.created_by == p.user_filter]
    total = len(results)
    if p.sort_by == "created_at":
        results.sort(key=lambda q: q.created_at, reverse=p.sort_order == "desc")
    elif p.sort_by == "execution_time_ms":
        results.sort(key=lambda q: q.execution_time_ms, reverse=p.sort_order == "desc")
    elif p.sort_by == "name":
        results.sort(key=lambda q: q.name, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return QueryPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total))


async def paginate_schedules(params: QueryPaginationParams | None = None) -> QueryPaginatedResult:
    p = params or QueryPaginationParams()
    results = list(_schedules.values())
    total = len(results)
    results.sort(key=lambda s: s.next_run or "", reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return QueryPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total))


async def batch_delete_queries(query_ids: list[str]) -> QueryBatchOperation:
    op = QueryBatchOperation(batch_id=str(uuid4()), operation="delete", item_ids=[], created_at=_ts())
    for qid in query_ids:
        if await delete_query(qid):
            op.item_ids.append(qid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"query_id": qid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _query_batch_ops[op.batch_id] = op
    return op


async def batch_tag_queries(query_ids: list[str], tags: list[str]) -> QueryBatchOperation:
    op = QueryBatchOperation(batch_id=str(uuid4()), operation="tag", item_ids=[], created_at=_ts())
    for qid in query_ids:
        q = _queries.get(qid)
        if q:
            for t in tags:
                if t not in q.tags:
                    q.tags.append(t)
            op.item_ids.append(qid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"query_id": qid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _query_batch_ops[op.batch_id] = op
    return op


async def batch_execute_queries(queries: list[dict]) -> QueryBatchOperation:
    op = QueryBatchOperation(batch_id=str(uuid4()), operation="execute", item_ids=[], created_at=_ts())
    for qdef in queries:
        try:
            result = await execute_query(qdef["sql"], qdef.get("database", "default"), qdef.get("user", "anonymous"))
            op.item_ids.append(result.result_id)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"sql": qdef.get("sql", "")[:50], "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _query_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[QueryBatchOperation]:
    return _query_batch_ops.get(batch_id)


async def export_query(query_id: str) -> dict:
    q = _queries.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    return {
        "name": q.name, "sql": q.sql, "database": q.database,
        "description": q.description, "tags": q.tags, "created_by": q.created_by,
    }


async def import_query(data: dict) -> SavedQuery:
    return await save_query(data["name"], data["sql"], data.get("database", "default"),
                             data.get("created_by", ""), data.get("tags"), data.get("description", ""))


async def export_queries_by_user(user: str) -> list[dict]:
    user_queries = [q for q in _queries.values() if q.created_by == user]
    return [await export_query(q.query_id) for q in user_queries]


async def get_query_analytics() -> dict:
    total = len(_queries)
    completed = sum(1 for q in _queries.values() if q.status == QueryStatus.COMPLETED)
    failed = sum(1 for q in _queries.values() if q.status == QueryStatus.FAILED)
    running = sum(1 for q in _queries.values() if q.status == QueryStatus.RUNNING)
    total_exec_time = sum(q.execution_time_ms for q in _queries.values())
    total_rows = sum(q.row_count for q in _queries.values())
    by_database = {}
    for q in _queries.values():
        by_database[q.database] = by_database.get(q.database, 0) + 1
    return {
        "total_queries": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "total_execution_time_ms": total_exec_time,
        "total_rows_returned": total_rows,
        "avg_execution_time_ms": round(total_exec_time / max(total, 1), 2),
        "avg_rows": total_rows // max(total, 1),
        "by_database": by_database,
        "shared_queries": sum(1 for q in _queries.values() if q.is_shared),
        "scheduled_queries": len(_schedules),
    }


async def transition_query_state(query_id: str, trigger: str, actor: str = "system") -> dict:
    q = _queries.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    from_state = q.status.value
    valid_transitions = {
        "pending": {"execute", "cancel"},
        "running": {"complete", "fail", "cancel"},
        "completed": {"re_run", "archive"},
        "failed": {"retry", "archive"},
        "cancelled": {"re_run"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"query_id": query_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {
        "execute": QueryStatus.RUNNING, "complete": QueryStatus.COMPLETED,
        "fail": QueryStatus.FAILED, "cancel": QueryStatus.CANCELLED,
        "re_run": QueryStatus.PENDING, "retry": QueryStatus.RUNNING,
        "archive": QueryStatus.COMPLETED,
    }
    new_status = to_state_map.get(trigger, q.status)
    q.status = new_status
    transition = QueryStateTransition(from_state=from_state, to_state=new_status.value, trigger=trigger,
                                       query_id=query_id, timestamp=_ts(), actor=actor)
    _query_state_history.setdefault(query_id, []).append(transition)
    return {"query_id": query_id, "success": True, "from_state": from_state, "to_state": new_status.value}


async def get_query_state_history(query_id: str) -> list[QueryStateTransition]:
    return _query_state_history.get(query_id, [])


async def validate_sql_safe(sql: str) -> dict:
    forbidden = ["DROP", "TRUNCATE", "ALTER", "DELETE", "INSERT", "UPDATE", "CREATE"]
    issues = []
    sql_upper = sql.upper().strip()
    for keyword in forbidden:
        if keyword in sql_upper:
            issues.append(f"Query contains forbidden keyword: {keyword}")
    if not sql_upper:
        issues.append("Query is empty")
    return {"safe": len(issues) == 0, "issues": issues}


async def search_queries_advanced(filters: dict) -> list[SavedQuery]:
    results = list(_queries.values())
    if "user" in filters:
        results = [q for q in results if q.created_by == filters["user"]]
    if "database" in filters:
        results = [q for q in results if q.database == filters["database"]]
    if "tag" in filters:
        results = [q for q in results if filters["tag"] in q.tags]
    if "shared" in filters:
        results = [q for q in results if q.is_shared == filters["shared"]]
    if "query" in filters:
        qs = filters["query"].lower()
        results = [q for q in results if qs in q.sql.lower() or qs in q.name.lower()]
    return results


async def get_performance_stats() -> dict:
    if not _queries:
        return {"avg_execution_time_ms": 0, "max_execution_time_ms": 0, "min_execution_time_ms": 0}
    exec_times = [q.execution_time_ms for q in _queries.values() if q.execution_time_ms > 0]
    if not exec_times:
        return {"avg_execution_time_ms": 0, "max_execution_time_ms": 0, "min_execution_time_ms": 0}
    return {
        "avg_execution_time_ms": round(sum(exec_times) / len(exec_times), 2),
        "max_execution_time_ms": max(exec_times),
        "min_execution_time_ms": min(exec_times),
        "p95_execution_time_ms": sorted(exec_times)[int(len(exec_times) * 0.95)],
    }


async def get_slowest_queries(limit: int = 10) -> list[SavedQuery]:
    with_time = [q for q in _queries.values() if q.execution_time_ms > 0]
    return sorted(with_time, key=lambda q: q.execution_time_ms, reverse=True)[:limit]


async def bulk_share_queries(query_ids: list[str]) -> QueryBatchOperation:
    op = QueryBatchOperation(batch_id=str(uuid4()), operation="share", item_ids=[], created_at=_ts())
    for qid in query_ids:
        try:
            await share_query(qid)
            op.item_ids.append(qid)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"query_id": qid, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _query_batch_ops[op.batch_id] = op
    return op


async def bulk_cancel_queries(query_ids: list[str]) -> QueryBatchOperation:
    op = QueryBatchOperation(batch_id=str(uuid4()), operation="cancel", item_ids=[], created_at=_ts())
    for qid in query_ids:
        if await cancel_query(qid):
            op.item_ids.append(qid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"query_id": qid, "error": "cannot cancel"})
    op.status = "completed"
    op.completed_at = _ts()
    _query_batch_ops[op.batch_id] = op
    return op


class QueryMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}
        self._latencies: list[float] = []

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def record_latency(self, ms: float):
        self._latencies.append(ms)

    def avg_latency(self) -> float:
        if not self._latencies:
            return 0.0
        return round(sum(self._latencies) / len(self._latencies), 2)

    def snapshot(self) -> dict:
        return {"counts": dict(self._counts), "avg_latency_ms": self.avg_latency(), "total_queries": len(self._latencies)}


class QueryCache:
    def __init__(self, ttl: int = 60):
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


class QueryAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, query_id: str = "", detail: str = "") -> dict:
        entry = {"action": action, "query_id": query_id, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_query_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    results = []
    for q in _queries.values():
        if query.lower() in q.name.lower() or query.lower() in q.sql.lower():
            results.append({"query_id": q.query_id, "name": q.name, "database": q.database})
            if len(results) >= limit:
                break
    return results


async def recommend_query_cleanup(days_threshold: int = 90) -> list[dict]:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    stale = []
    for q in _queries.values():
        created = datetime.fromisoformat(q.created_at.replace("Z", "+00:00"))
        if created < cutoff and q.status == QueryStatus.COMPLETED:
            stale.append({"query_id": q.query_id, "name": q.name, "last_used": q.created_at})
    return stale


async def get_popular_queries(limit: int = 10) -> list[dict]:
    sorted_queries = sorted(_queries.values(), key=lambda x: getattr(x, "run_count", 0), reverse=True)
    return [{"query_id": q.query_id, "name": q.name, "database": q.database, "run_count": getattr(q, "run_count", 0)} for q in sorted_queries[:limit]]

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
