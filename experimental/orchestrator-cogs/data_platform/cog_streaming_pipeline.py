"""Cog: Streaming Data Pipeline — managed Kafka/Redpanda clusters."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

STREAMING_DEPLOYMENTS: dict[str, dict] = {}


async def deploy_cluster(name: str, cluster_type: str = "kafka", nodes: int = 3, version: str = "latest") -> dict:
    deployment_id = f"st-{name.lower().replace(' ', '-')}"
    STREAMING_DEPLOYMENTS[deployment_id] = {
        "deployment_id": deployment_id,
        "name": name,
        "type": cluster_type,
        "nodes": nodes,
        "version": version,
        "status": "deploying",
        "brokers": [f"{deployment_id}-broker-{i}.internal:9092" for i in range(nodes)],
    }
    await asyncio.sleep(0.5)
    STREAMING_DEPLOYMENTS[deployment_id]["status"] = "active"
    return STREAMING_DEPLOYMENTS[deployment_id]


async def get_cluster(deployment_id: str) -> dict | None:
    return STREAMING_DEPLOYMENTS.get(deployment_id)


async def list_clusters() -> list[dict]:
    return list(STREAMING_DEPLOYMENTS.values())


async def delete_cluster(deployment_id: str) -> bool:
    return STREAMING_DEPLOYMENTS.pop(deployment_id, None) is not None


async def scale_cluster(deployment_id: str, target_nodes: int) -> dict:
    dep = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not dep:
        raise ValueError(f"Deployment {deployment_id} not found")
    dep["nodes"] = target_nodes
    dep["brokers"] = [f"{deployment_id}-broker-{i}.internal:9092" for i in range(target_nodes)]
    return dep


async def create_topic(deployment_id: str, topic: str, partitions: int = 3) -> dict:
    return {"deployment_id": deployment_id, "topic": topic, "partitions": partitions, "status": "created"}


async def delete_topic(deployment_id: str, topic: str) -> bool:
    return True


async def list_topics(deployment_id: str) -> list[dict]:
    return [{"name": "events", "partitions": 3, "replication": 2}, {"name": "logs", "partitions": 2, "replication": 1}]


async def get_cluster_stats() -> dict:
    return {"total": len(STREAMING_DEPLOYMENTS), "active": sum(1 for d in STREAMING_DEPLOYMENTS.values() if d["status"] == "active")}


async def update_cluster(deployment_id: str, **kwargs) -> dict | None:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        return None
    d.update(kwargs)
    return d


async def produce_message(deployment_id: str, topic: str, key: str, value: str) -> dict:
    return {"deployment_id": deployment_id, "topic": topic, "offset": 1, "partition": 0}


async def consume_message(deployment_id: str, topic: str, group_id: str = "default") -> dict:
    return {"deployment_id": deployment_id, "topic": topic, "key": "sample-key", "value": "sample-value", "offset": 0}


async def register_schema(deployment_id: str, subject: str, schema_body: str, schema_type: str = "avro", compatibility: str = "backward") -> dict:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        raise ValueError(f"Deployment {deployment_id} not found")
    schema = {"subject": subject, "version": 1, "schema_body": schema_body, "schema_type": schema_type, "compatibility": compatibility}
    if "_schemas" not in globals():
        globals()["_schemas"] = []
    globals()["_schemas"].append(schema)
    return schema


async def list_schemas(deployment_id: str) -> list[dict]:
    return list(globals().get("_schemas", []))


async def create_connector(deployment_id: str, name: str, connector_type: str = "source", config: dict | None = None) -> dict:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        raise ValueError(f"Deployment {deployment_id} not found")
    connector = {"connector_id": f"c-{len(STREAMING_DEPLOYMENTS)}", "name": name, "type": connector_type, "config": config or {}, "status": "running"}
    if "_connectors" not in globals():
        globals()["_connectors"] = {}
    globals()["_connectors"][connector["connector_id"]] = connector
    return connector


async def list_connectors(deployment_id: str) -> list[dict]:
    return list(globals().get("_connectors", {}).values())


async def pause_connector(deployment_id: str, connector_id: str) -> bool:
    connectors = globals().get("_connectors", {})
    c = connectors.get(connector_id)
    if c:
        c["status"] = "paused"
        return True
    return False


async def resume_connector(deployment_id: str, connector_id: str) -> bool:
    connectors = globals().get("_connectors", {})
    c = connectors.get(connector_id)
    if c:
        c["status"] = "running"
        return True
    return False


async def delete_connector(deployment_id: str, connector_id: str) -> bool:
    connectors = globals().get("_connectors", {})
    return connectors.pop(connector_id, None) is not None


async def get_cluster_metrics(deployment_id: str) -> dict:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        raise ValueError(f"Deployment {deployment_id} not found")
    return {"deployment_id": deployment_id, "nodes": d.get("nodes"), "cpu_avg": 45.2, "throughput_bytes_sec": 1024000, "status": d.get("status")}


async def set_auto_scaling(deployment_id: str, enabled: bool) -> dict | None:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        return None
    d["auto_scaling_enabled"] = enabled
    return d


async def get_consumer_groups(deployment_id: str) -> list[dict]:
    return [{"group": "consumer-group-1", "topic": "events", "lag": 0, "members": 2}]


async def get_topic_metrics(deployment_id: str, topic: str) -> dict:
    return {"topic": topic, "partitions": 3, "replication_factor": 2, "size_bytes": 1048576, "message_count": 15000}


async def rebalance_cluster(deployment_id: str) -> dict:
    d = STREAMING_DEPLOYMENTS.get(deployment_id)
    if not d:
        raise ValueError(f"Deployment {deployment_id} not found")
    await asyncio.sleep(0.3)
    return {"deployment_id": deployment_id, "status": "rebalanced", "partitions_moved": 6}


async def list_cluster_types() -> list[str]:
    return ["kafka", "redpanda"]


async def validate_schema_compatibility(deployment_id: str, subject: str, schema_body: str) -> dict:
    return {"subject": subject, "compatible": True, "existing_versions": 0}


async def get_cluster_summary() -> dict:
    total = len(STREAMING_DEPLOYMENTS)
    active = sum(1 for d in STREAMING_DEPLOYMENTS.values() if d.get("status") == "active")
    return {"total": total, "active": active, "total_topics": total * 2, "total_connectors": total}


async def promote_partition(deployment_id: str, topic: str, partition: int) -> dict:
    return {"deployment_id": deployment_id, "topic": topic, "partition": partition, "status": "promoted"}


async def execute_ksql(deployment_id: str, ksql: str) -> dict:
    return {"deployment_id": deployment_id, "query": ksql, "status": "submitted", "result": []}


# ===== APPENDED: Utility & bridge helpers, batch ops, formatting =====

async def format_cluster_info(deployment_id: str) -> dict:
    d = await get_cluster(deployment_id)
    if not d:
        return {"error": f"Cluster {deployment_id} not found"}
    return {
        "deployment_id": d["deployment_id"],
        "name": d["name"],
        "type": d.get("type"),
        "nodes": d.get("nodes"),
        "version": d.get("version"),
        "status": d.get("status"),
        "brokers": d.get("brokers"),
        "auto_scaling": d.get("auto_scaling_enabled", False),
    }

async def list_clusters_detailed() -> list[dict]:
    clusters = await list_clusters()
    result = []
    for c in clusters:
        result.append({
            "deployment_id": c.get("deployment_id"),
            "name": c.get("name"),
            "type": c.get("type"),
            "nodes": c.get("nodes"),
            "status": c.get("status"),
        })
    return result

async def batch_create_topics(deployment_id: str, topics: list[str]) -> list[dict]:
    results = []
    for topic in topics:
        t = await create_topic(deployment_id, topic)
        results.append(t)
    return results

async def batch_delete_topics(deployment_id: str, topics: list[str]) -> dict:
    deleted = 0
    for topic in topics:
        if await delete_topic(deployment_id, topic):
            deleted += 1
    return {"deleted": deleted, "total_requested": len(topics)}

async def export_cluster_config(deployment_id: str) -> dict:
    d = await get_cluster(deployment_id)
    if not d:
        return {"error": "Not found"}
    schemas = await list_schemas(deployment_id)
    connectors = await list_connectors(deployment_id)
    topics = await list_topics(deployment_id)
    return {
        "cluster": d,
        "schemas": schemas,
        "connectors": connectors,
        "topics": topics,
    }

async def cluster_health_check(deployment_id: str) -> dict:
    d = await get_cluster(deployment_id)
    if not d:
        return {"error": "Not found"}
    metrics = await get_cluster_metrics(deployment_id)
    groups = await get_consumer_groups(deployment_id)
    total_lag = sum(g.get("lag", 0) for g in groups)
    issues = []
    if metrics.get("cpu_avg", 0) > 80:
        issues.append("High CPU usage")
    if total_lag > 1000:
        issues.append("Consumer lag exceeds threshold")
    return {
        "deployment_id": deployment_id,
        "status": d.get("status"),
        "cpu_avg": metrics.get("cpu_avg"),
        "throughput": metrics.get("throughput_bytes_sec"),
        "total_lag": total_lag,
        "healthy": len(issues) == 0,
        "issues": issues,
    }

async def paginate_topics(deployment_id: str, offset: int = 0, limit: int = 50) -> dict:
    topics = await list_topics(deployment_id)
    total = len(topics)
    sliced = topics[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def paginate_connectors(deployment_id: str, offset: int = 0, limit: int = 50) -> dict:
    connectors = await list_connectors(deployment_id)
    total = len(connectors)
    sliced = connectors[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def bulk_produce_messages(deployment_id: str, topic: str, messages: list[dict]) -> list[dict]:
    results = []
    for msg in messages:
        r = await produce_message(deployment_id, topic, msg.get("key", ""), msg.get("value", ""))
        results.append(r)
    return results

async def search_clusters(query: str) -> list[dict]:
    q = query.lower()
    clusters = await list_clusters()
    return [c for c in clusters if q in c.get("name", "").lower() or q in c.get("deployment_id", "").lower()]

async def get_cluster_analytics() -> dict:
    clusters = await list_clusters()
    stats = await get_cluster_stats()
    types = {}
    for c in clusters:
        t = c.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    return {
        "total": stats.get("total", 0),
        "active": stats.get("active", 0),
        "by_type": types,
        "total_brokers": sum(c.get("nodes", 0) for c in clusters),
    }

async def simulate_traffic(deployment_id: str, messages_count: int = 100) -> dict:
    import random
    topics = await list_topics(deployment_id)
    if not topics:
        return {"error": "No topics available"}
    topic = topics[0].get("name", "events")
    produced = 0
    for _ in range(min(messages_count, 50)):
        await produce_message(deployment_id, topic, f"key-{random.randint(1, 10)}", f"value-{random.randint(1, 1000)}")
        produced += 1
    return {"deployment_id": deployment_id, "topic": topic, "messages_produced": produced}

async def get_connector_logs(deployment_id: str, connector_id: str, lines: int = 20) -> dict:
    return {"connector_id": connector_id, "log_lines": [f"[INFO] Connector {connector_id} running" for _ in range(min(lines, 20))]}

async def validate_connector_config(config: dict) -> dict:
    errors = []
    if "connector.class" not in config:
        errors.append("Missing connector.class")
    if "tasks.max" not in config:
        errors.append("Missing tasks.max")
    return {"valid": len(errors) == 0, "errors": errors}

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
