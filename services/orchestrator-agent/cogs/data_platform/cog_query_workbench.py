"""Cog: Analytics Query Workbench — SQL editor, schema browser, query history."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

SAVED_QUERIES: dict[str, dict] = {}


async def execute_query(sql: str, database: str = "default") -> dict:
    qid = f"q-{len(SAVED_QUERIES) + 1}"
    import random
    SAVED_QUERIES[qid] = {"query_id": qid, "sql": sql, "database": database, "status": "completed", "rows": random.randint(10, 500)}
    return SAVED_QUERIES[qid]


async def save_query(name: str, sql: str, database: str = "default") -> dict:
    qid = f"q-{len(SAVED_QUERIES) + 1}"
    SAVED_QUERIES[qid] = {"query_id": qid, "name": name, "sql": sql, "database": database, "status": "saved"}
    return SAVED_QUERIES[qid]


async def list_queries() -> list[dict]:
    return list(SAVED_QUERIES.values())


async def get_query(query_id: str) -> dict | None:
    return SAVED_QUERIES.get(query_id)


async def delete_query(query_id: str) -> bool:
    return SAVED_QUERIES.pop(query_id, None) is not None


async def refresh_schema(database: str) -> list[dict]:
    return [{"name": "users", "type": "table", "columns": ["id", "name", "email"]}]


async def get_workbench_stats() -> dict:
    return {"total_queries": len(SAVED_QUERIES)}


async def update_query(query_id: str, **kwargs) -> dict | None:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        return None
    q.update(kwargs)
    return q


async def share_query(query_id: str) -> str:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        raise ValueError(f"Query {query_id} not found")
    q["shared"] = True
    q["share_url"] = f"/shared/queries/{query_id}"
    return q["share_url"]


async def get_query_result(query_id: str) -> dict | None:
    q = SAVED_QUERIES.get(query_id)
    if q and "result" in q:
        return q["result"]
    return None


async def cancel_query(query_id: str) -> bool:
    q = SAVED_QUERIES.get(query_id)
    if not q or q.get("status") == "completed":
        return False
    q["status"] = "cancelled"
    return True


async def validate_sql(sql: str) -> dict:
    sql_upper = sql.upper().strip()
    errors = []
    if not sql_upper:
        errors.append({"line": 0, "message": "Empty query"})
    if "SELECT" not in sql_upper and "WITH" not in sql_upper:
        errors.append({"line": 0, "message": "Query must contain SELECT or WITH"})
    return {"valid": len(errors) == 0, "errors": errors}


async def get_schema(database: str) -> list[dict]:
    return [{"name": "users", "type": "table", "columns": ["id", "name", "email"]}]


async def search_schema(query: str) -> list[dict]:
    q = query.lower()
    return [{"name": "users", "type": "table", "database": "default"}]


async def fork_query(query_id: str, new_name: str) -> dict | None:
    original = SAVED_QUERIES.get(query_id)
    if not original:
        return None
    qid = f"q-{len(SAVED_QUERIES) + 1}"
    SAVED_QUERIES[qid] = {**original, "query_id": qid, "name": new_name, "forked_from": query_id}
    return SAVED_QUERIES[qid]


async def tag_query(query_id: str, tags: list[str]) -> dict | None:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        return None
    if "tags" not in q:
        q["tags"] = []
    for t in tags:
        if t not in q["tags"]:
            q["tags"].append(t)
    return q


async def untag_query(query_id: str, tags: list[str]) -> dict | None:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        return None
    if "tags" in q:
        for t in tags:
            while t in q["tags"]:
                q["tags"].remove(t)
    return q


async def get_popular_queries(limit: int = 5) -> list[dict]:
    sorted_queries = sorted(SAVED_QUERIES.values(), key=lambda q: q.get("execution_time_ms", 0), reverse=True)
    return sorted_queries[:limit]


async def format_query(sql: str) -> str:
    return sql.strip()


async def autocomplete(prefix: str) -> list[str]:
    p = prefix.upper()
    if "SEL" in p:
        return ["SELECT column1, column2 FROM table_name"]
    if "FRO" in p:
        return ["FROM table_name"]
    if "WHE" in p:
        return ["WHERE condition = value"]
    return ["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "LIMIT"]


async def create_schedule(query_id: str, cron: str, recipients: list[str]) -> dict:
    return {"schedule_id": f"sch-{len(SAVED_QUERIES)}", "query_id": query_id, "cron": cron, "recipients": recipients, "enabled": True}


async def delete_schedule(schedule_id: str) -> bool:
    return True


async def export_results(query_id: str, format: str = "csv") -> str:
    return f"/exports/queries/{query_id}.{format}"


async def get_recent_queries(user: str | None = None, limit: int = 10) -> list[dict]:
    results = list(SAVED_QUERIES.values())
    if user:
        results = [q for q in results if q.get("created_by") == user]
    return sorted(results, key=lambda q: q.get("created_at", ""), reverse=True)[:limit]


async def list_databases() -> list[str]:
    return ["default", "analytics", "reporting", "staging"]


async def explain_query(sql: str) -> dict:
    return {"query_type": "SELECT", "estimated_cost": "medium", "tables_involved": ["users", "orders"], "estimated_rows": 1500}


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_queries(offset: int = 0, limit: int = 50, status: str = None) -> dict:
    results = list(SAVED_QUERIES.values())
    if status:
        results = [q for q in results if q.get("status") == status]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def format_query_info(query_id: str) -> dict:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        return {"error": "Query not found"}
    return {
        "query_id": q["query_id"],
        "name": q.get("name"),
        "sql": q.get("sql"),
        "database": q.get("database"),
        "status": q.get("status"),
        "created_by": q.get("created_by"),
        "created_at": q.get("created_at"),
        "execution_time_ms": q.get("execution_time_ms"),
        "tags": q.get("tags", []),
    }

async def bulk_cancel_queries(query_ids: list[str]) -> dict:
    cancelled = 0
    for qid in query_ids:
        if await cancel_query(qid):
            cancelled += 1
    return {"cancelled": cancelled, "total_requested": len(query_ids)}

async def batch_execute(sqls: list[str], database: str = "default") -> list[dict]:
    results = []
    for sql in sqls:
        r = await execute_query(sql, database)
        results.append(r)
    return results

async def search_queries(query: str) -> list[dict]:
    q = query.lower()
    return [sv for sv in SAVED_QUERIES.values() if q in sv.get("name", "").lower() or q in sv.get("sql", "").lower()]

async def get_workbench_analytics() -> dict:
    return {
        "total_queries": len(SAVED_QUERIES),
        "completed": sum(1 for q in SAVED_QUERIES.values() if q.get("status") == "completed"),
        "running": sum(1 for q in SAVED_QUERIES.values() if q.get("status") == "running"),
        "failed": sum(1 for q in SAVED_QUERIES.values() if q.get("status") == "failed"),
        "avg_execution_ms": round(
            sum(q.get("execution_time_ms", 0) for q in SAVED_QUERIES.values()) / max(len(SAVED_QUERIES), 1), 1
        ),
        "unique_users": len(set(q.get("created_by", "") for q in SAVED_QUERIES.values() if q.get("created_by"))),
    }

async def bulk_tag_queries(query_ids: list[str], tags: list[str]) -> dict:
    tagged = 0
    for qid in query_ids:
        if await tag_query(qid, tags):
            tagged += 1
    return {"tagged": tagged, "total_requested": len(query_ids)}

async def export_query_results(query_id: str, format: str = "csv") -> dict:
    q = SAVED_QUERIES.get(query_id)
    if not q:
        return {"error": "Query not found"}
    return {"query_id": query_id, "format": format, "url": f"/exports/{query_id}.{format}", "status": "ready"}

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
