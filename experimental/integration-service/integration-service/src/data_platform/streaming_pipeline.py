"""Streaming Data Pipeline — managed Kafka/Redpanda clusters with auto-scaling."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ClusterType(Enum):
    KAFKA = "kafka"
    REDPANDA = "redpanda"


class ConnectorType(Enum):
    SOURCE = "source"
    SINK = "sink"


class ConnectorStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    CREATING = "creating"


@dataclass
class KafkaTopic:
    topic_id: str
    name: str
    partitions: int
    replication_factor: int
    retention_ms: int
    cleanup_policy: str
    size_bytes: int = 0
    message_count: int = 0
    created_at: str = ""


@dataclass
class SchemaRegistryEntry:
    subject: str
    version: int
    schema_body: str
    schema_type: str
    compatibility: str
    created_at: str = ""


@dataclass
class StreamingConnector:
    connector_id: str
    name: str
    connector_type: ConnectorType
    config: dict
    status: ConnectorStatus = ConnectorStatus.CREATING
    tasks_running: int = 0
    error_message: str = ""
    created_at: str = ""


@dataclass
class StreamingCluster:
    cluster_id: str
    name: str
    cluster_type: ClusterType
    nodes: int
    min_nodes: int
    max_nodes: int
    brokers: list[str] = field(default_factory=list)
    topics: list[KafkaTopic] = field(default_factory=list)
    connectors: list[StreamingConnector] = field(default_factory=list)
    schema_registry: list[SchemaRegistryEntry] = field(default_factory=list)
    auto_scaling_enabled: bool = True
    cpu_avg: float = 0.0
    throughput_bytes_sec: float = 0.0
    status: str = "active"
    created_at: str = ""
    version: str = ""


_clusters: dict[str, StreamingCluster] = {}


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def create_cluster(
    name: str,
    cluster_type: ClusterType = ClusterType.KAFKA,
    nodes: int = 3,
    min_nodes: int = 1,
    max_nodes: int = 10,
    version: str = "latest",
) -> StreamingCluster:
    cluster = StreamingCluster(
        cluster_id=str(uuid4()),
        name=name,
        cluster_type=cluster_type,
        nodes=nodes,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        brokers=[f"{name}-broker-{i}.internal:9092" for i in range(nodes)],
        auto_scaling_enabled=True,
        created_at=_ts(),
        version=version,
    )
    _clusters[cluster.cluster_id] = cluster
    logger.info("Streaming cluster created: %s (%s)", cluster.cluster_id, cluster_type.value)
    return cluster


async def list_clusters() -> list[StreamingCluster]:
    return list(_clusters.values())


async def get_cluster(cluster_id: str) -> Optional[StreamingCluster]:
    return _clusters.get(cluster_id)


async def delete_cluster(cluster_id: str) -> bool:
    return _clusters.pop(cluster_id, None) is not None


async def scale_cluster(cluster_id: str, target_nodes: int) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    if not (cluster.min_nodes <= target_nodes <= cluster.max_nodes):
        raise ValueError(f"Target nodes {target_nodes} out of range [{cluster.min_nodes}, {cluster.max_nodes}]")
    cluster.nodes = target_nodes
    cluster.brokers = [f"{cluster.name}-broker-{i}.internal:9092" for i in range(target_nodes)]
    logger.info("Cluster %s scaled to %d nodes", cluster_id, target_nodes)
    return {"cluster_id": cluster_id, "nodes": target_nodes}


async def auto_scale() -> dict:
    actions = []
    for cid, cluster in _clusters.items():
        if not cluster.auto_scaling_enabled:
            continue
        if cluster.cpu_avg > 80 and cluster.nodes < cluster.max_nodes:
            target = min(cluster.nodes + 2, cluster.max_nodes)
            await scale_cluster(cid, target)
            actions.append({"cluster_id": cid, "action": "scale_up", "from": cluster.nodes, "to": target})
        elif cluster.cpu_avg < 20 and cluster.nodes > cluster.min_nodes:
            target = max(cluster.nodes - 1, cluster.min_nodes)
            await scale_cluster(cid, target)
            actions.append({"cluster_id": cid, "action": "scale_down", "from": cluster.nodes, "to": target})
    return {"actions": actions, "timestamp": _ts()}


async def create_topic(
    cluster_id: str,
    name: str,
    partitions: int = 3,
    replication_factor: int = 2,
    retention_ms: int = 604800000,
    cleanup_policy: str = "delete",
) -> Optional[KafkaTopic]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    topic = KafkaTopic(
        topic_id=str(uuid4()),
        name=name,
        partitions=partitions,
        replication_factor=replication_factor,
        retention_ms=retention_ms,
        cleanup_policy=cleanup_policy,
        created_at=_ts(),
    )
    cluster.topics.append(topic)
    return topic


async def list_topics(cluster_id: str) -> list[KafkaTopic]:
    cluster = _clusters.get(cluster_id)
    return cluster.topics if cluster else []


async def delete_topic(cluster_id: str, topic_id: str) -> bool:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return False
    before = len(cluster.topics)
    cluster.topics = [t for t in cluster.topics if t.topic_id != topic_id]
    return len(cluster.topics) < before


async def produce_message(cluster_id: str, topic: str, key: str, value: str) -> dict:
    await asyncio.sleep(0.05)
    return {"cluster_id": cluster_id, "topic": topic, "offset": 1, "partition": 0, "timestamp": _ts()}


async def consume_message(cluster_id: str, topic: str, group_id: str = "default") -> dict:
    await asyncio.sleep(0.05)
    return {"cluster_id": cluster_id, "topic": topic, "key": "sample-key", "value": "sample-value", "offset": 0}


async def register_schema(cluster_id: str, subject: str, schema_body: str, schema_type: str = "avro", compatibility: str = "backward") -> SchemaRegistryEntry:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    entry = SchemaRegistryEntry(
        subject=subject,
        version=len([e for e in cluster.schema_registry if e.subject == subject]) + 1,
        schema_body=schema_body,
        schema_type=schema_type,
        compatibility=compatibility,
        created_at=_ts(),
    )
    cluster.schema_registry.append(entry)
    return entry


async def list_schemas(cluster_id: str) -> list[SchemaRegistryEntry]:
    cluster = _clusters.get(cluster_id)
    return cluster.schema_registry if cluster else []


async def create_connector(cluster_id: str, name: str, connector_type: ConnectorType, config: dict) -> StreamingConnector:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    connector = StreamingConnector(
        connector_id=str(uuid4()),
        name=name,
        connector_type=connector_type,
        config=config,
        created_at=_ts(),
    )
    cluster.connectors.append(connector)
    return connector


async def list_connectors(cluster_id: str) -> list[StreamingConnector]:
    cluster = _clusters.get(cluster_id)
    return cluster.connectors if cluster else []


async def pause_connector(cluster_id: str, connector_id: str) -> bool:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return False
    for c in cluster.connectors:
        if c.connector_id == connector_id:
            c.status = ConnectorStatus.PAUSED
            return True
    return False


async def resume_connector(cluster_id: str, connector_id: str) -> bool:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return False
    for c in cluster.connectors:
        if c.connector_id == connector_id:
            c.status = ConnectorStatus.RUNNING
            return True
    return False


async def delete_connector(cluster_id: str, connector_id: str) -> bool:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return False
    before = len(cluster.connectors)
    cluster.connectors = [c for c in cluster.connectors if c.connector_id != connector_id]
    return len(cluster.connectors) < before


async def get_cluster_metrics(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    return {
        "cluster_id": cluster_id,
        "nodes": cluster.nodes,
        "topics": len(cluster.topics),
        "connectors": len(cluster.connectors),
        "cpu_avg": cluster.cpu_avg,
        "throughput_bytes_sec": cluster.throughput_bytes_sec,
        "status": cluster.status,
    }


async def execute_ksql(cluster_id: str, ksql: str) -> dict:
    await asyncio.sleep(0.1)
    return {"cluster_id": cluster_id, "query": ksql, "status": "submitted", "result": []}


async def update_cluster(cluster_id: str, **kwargs) -> Optional[StreamingCluster]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return None
    for k, v in kwargs.items():
        if hasattr(cluster, k):
            setattr(cluster, k, v)
    return cluster


async def update_topic_config(cluster_id: str, topic_id: str, retention_ms: int | None = None, cleanup_policy: str | None = None) -> bool:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return False
    for t in cluster.topics:
        if t.topic_id == topic_id:
            if retention_ms is not None:
                t.retention_ms = retention_ms
            if cleanup_policy is not None:
                t.cleanup_policy = cleanup_policy
            return True
    return False


async def get_topic_metrics(cluster_id: str, topic_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    for t in cluster.topics:
        if t.topic_id == topic_id:
            return {
                "topic_id": topic_id,
                "name": t.name,
                "partitions": t.partitions,
                "replication_factor": t.replication_factor,
                "size_bytes": t.size_bytes,
                "message_count": t.message_count,
            }
    raise ValueError(f"Topic {topic_id} not found")


async def list_connector_statuses(cluster_id: str) -> list[dict]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return []
    return [{"name": c.name, "type": c.connector_type.value, "status": c.status.value, "tasks_running": c.tasks_running} for c in cluster.connectors]


async def get_cluster_summary() -> dict:
    total_clusters = len(_clusters)
    total_topics = sum(len(c.topics) for c in _clusters.values())
    total_connectors = sum(len(c.connectors) for c in _clusters.values())
    return {
        "total_clusters": total_clusters,
        "total_topics": total_topics,
        "total_connectors": total_connectors,
        "active_clusters": sum(1 for c in _clusters.values() if c.status == "active"),
    }


async def set_auto_scaling(cluster_id: str, enabled: bool) -> Optional[StreamingCluster]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return None
    cluster.auto_scaling_enabled = enabled
    return cluster


async def get_consumer_groups(cluster_id: str) -> list[dict]:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        return []
    return [
        {"group": f"consumer-group-{i}", "topic": t.name, "lag": 0, "members": 2}
        for i, t in enumerate(cluster.topics)
    ]


async def promote_partition(cluster_id: str, topic_id: str, partition: int) -> dict:
    await asyncio.sleep(0.05)
    return {"cluster_id": cluster_id, "topic_id": topic_id, "partition": partition, "status": "promoted", "new_leader": f"broker-{partition % 3 + 1}"}


async def rebalance_cluster(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    await asyncio.sleep(0.3)
    return {"cluster_id": cluster_id, "status": "rebalanced", "partitions_moved": len(cluster.topics) * 2}


async def list_cluster_types() -> list[str]:
    return [c.value for c in ClusterType]


async def validate_schema_compatibility(cluster_id: str, subject: str, schema_body: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    existing = [e for e in cluster.schema_registry if e.subject == subject]
    compatible = len(existing) == 0
    return {"subject": subject, "compatible": compatible, "existing_versions": len(existing)}


# ===== APPENDED: Batch operations, pagination, state machine, analytics, export/import =====

@dataclass
class BatchTopicOperation:
    batch_id: str
    cluster_id: str
    operation: str
    topic_ids: list[str]
    status: str = "pending"
    success_count: int = 0
    failure_count: int = 0
    errors: list[dict] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""


@dataclass
class PaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"


@dataclass
class PaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class ClusterConfigValidation:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ClusterStateTransition:
    from_state: str
    to_state: str
    trigger: str
    timestamp: str = ""
    actor: str = "system"


_cluster_state_machine: dict[str, list[ClusterStateTransition]] = {}
_batch_operations: dict[str, BatchTopicOperation] = {}


async def paginate_topics(cluster_id: str, params: PaginationParams | None = None) -> PaginatedResult:
    p = params or PaginationParams()
    cluster = _clusters.get(cluster_id)
    topics = list(cluster.topics) if cluster else []
    total = len(topics)
    if p.sort_by == "name":
        topics.sort(key=lambda t: t.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "partitions":
        topics.sort(key=lambda t: t.partitions, reverse=p.sort_order == "desc")
    elif p.sort_by == "size_bytes":
        topics.sort(key=lambda t: t.size_bytes, reverse=p.sort_order == "desc")
    sliced = topics[p.offset:p.offset + p.limit]
    return PaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit, has_more=(p.offset + p.limit < total))


async def paginate_connectors(cluster_id: str, params: PaginationParams | None = None) -> PaginatedResult:
    p = params or PaginationParams()
    cluster = _clusters.get(cluster_id)
    connectors = list(cluster.connectors) if cluster else []
    total = len(connectors)
    if p.sort_by == "name":
        connectors.sort(key=lambda c: c.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "status":
        connectors.sort(key=lambda c: c.status.value, reverse=p.sort_order == "desc")
    sliced = connectors[p.offset:p.offset + p.limit]
    return PaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit, has_more=(p.offset + p.limit < total))


async def paginate_schemas(cluster_id: str, params: PaginationParams | None = None) -> PaginatedResult:
    p = params or PaginationParams()
    cluster = _clusters.get(cluster_id)
    schemas = list(cluster.schema_registry) if cluster else []
    total = len(schemas)
    if p.sort_by == "subject":
        schemas.sort(key=lambda s: s.subject, reverse=p.sort_order == "desc")
    elif p.sort_by == "version":
        schemas.sort(key=lambda s: s.version, reverse=p.sort_order == "desc")
    sliced = schemas[p.offset:p.offset + p.limit]
    return PaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit, has_more=(p.offset + p.limit < total))


async def batch_create_topics(cluster_id: str, topic_defs: list[dict]) -> BatchTopicOperation:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    op = BatchTopicOperation(
        batch_id=str(uuid4()),
        cluster_id=cluster_id,
        operation="create_topics",
        topic_ids=[],
        created_at=_ts(),
    )
    for td in topic_defs:
        try:
            topic = await create_topic(
                cluster_id,
                td["name"],
                td.get("partitions", 3),
                td.get("replication_factor", 2),
                td.get("retention_ms", 604800000),
                td.get("cleanup_policy", "delete"),
            )
            op.topic_ids.append(topic.topic_id)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"name": td.get("name"), "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _batch_operations[op.batch_id] = op
    return op


async def batch_delete_topics(cluster_id: str, topic_names: list[str]) -> BatchTopicOperation:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    op = BatchTopicOperation(
        batch_id=str(uuid4()),
        cluster_id=cluster_id,
        operation="delete_topics",
        topic_ids=[],
        created_at=_ts(),
    )
    for topic in list(cluster.topics):
        if topic.name in topic_names:
            try:
                await delete_topic(cluster_id, topic.topic_id)
                op.topic_ids.append(topic.topic_id)
                op.success_count += 1
            except Exception as e:
                op.failure_count += 1
                op.errors.append({"name": topic.name, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _batch_operations[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[BatchTopicOperation]:
    return _batch_operations.get(batch_id)


async def export_cluster_config(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    return {
        "cluster": {
            "name": cluster.name,
            "cluster_type": cluster.cluster_type.value,
            "nodes": cluster.nodes,
            "min_nodes": cluster.min_nodes,
            "max_nodes": cluster.max_nodes,
            "auto_scaling_enabled": cluster.auto_scaling_enabled,
            "version": cluster.version,
        },
        "topics": [{"name": t.name, "partitions": t.partitions, "replication_factor": t.replication_factor,
                     "retention_ms": t.retention_ms, "cleanup_policy": t.cleanup_policy} for t in cluster.topics],
        "connectors": [{"name": c.name, "connector_type": c.connector_type.value, "config": c.config} for c in cluster.connectors],
        "schemas": [{"subject": s.subject, "schema_type": s.schema_type, "compatibility": s.compatibility,
                      "schema_body": s.schema_body} for s in cluster.schema_registry],
        "exported_at": _ts(),
    }


async def import_cluster_config(cluster_id: str, config: dict) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    imported = {"topics": 0, "connectors": 0, "schemas": 0}
    if "topics" in config:
        for td in config["topics"]:
            await create_topic(cluster_id, td["name"], td.get("partitions", 3),
                               td.get("replication_factor", 2), td.get("retention_ms", 604800000),
                               td.get("cleanup_policy", "delete"))
            imported["topics"] += 1
    if "connectors" in config:
        for cd in config["connectors"]:
            await create_connector(cluster_id, cd["name"], ConnectorType(cd.get("connector_type", "source")), cd.get("config", {}))
            imported["connectors"] += 1
    if "schemas" in config:
        for sd in config["schemas"]:
            await register_schema(cluster_id, sd["subject"], sd.get("schema_body", ""),
                                  sd.get("schema_type", "avro"), sd.get("compatibility", "backward"))
            imported["schemas"] += 1
    return {"cluster_id": cluster_id, "imported": imported, "timestamp": _ts()}


async def get_cluster_analytics(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    total_messages = sum(t.message_count for t in cluster.topics)
    total_size = sum(t.size_bytes for t in cluster.topics)
    topic_growth = [{"topic": t.name, "messages": t.message_count, "size_bytes": t.size_bytes} for t in cluster.topics]
    return {
        "cluster_id": cluster_id,
        "total_topics": len(cluster.topics),
        "total_connectors": len(cluster.connectors),
        "total_schemas": len(cluster.schema_registry),
        "total_messages": total_messages,
        "total_size_bytes": total_size,
        "avg_messages_per_topic": total_messages // max(len(cluster.topics), 1),
        "topic_growth": topic_growth,
        "throughput_bytes_sec": cluster.throughput_bytes_sec,
        "cpu_avg": cluster.cpu_avg,
        "nodes": cluster.nodes,
    }


async def get_cluster_state_history(cluster_id: str) -> list[ClusterStateTransition]:
    return _cluster_state_machine.get(cluster_id, [])


async def transition_cluster_state(cluster_id: str, trigger: str, actor: str = "system") -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    from_state = cluster.status
    valid_transitions = {
        "active": {"pause", "maintenance", "decommission"},
        "paused": {"resume", "decommission"},
        "maintenance": {"complete", "fail"},
        "decommissioned": set(),
        "failed": {"recover", "decommission"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"cluster_id": cluster_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {
        "pause": "paused", "resume": "active", "maintenance": "maintenance",
        "complete": "active", "fail": "failed", "recover": "active",
        "decommission": "decommissioned",
    }
    to_state = to_state_map.get(trigger, from_state)
    cluster.status = to_state
    transition = ClusterStateTransition(from_state=from_state, to_state=to_state, trigger=trigger, timestamp=_ts(), actor=actor)
    _cluster_state_machine.setdefault(cluster_id, []).append(transition)
    return {"cluster_id": cluster_id, "success": True, "from_state": from_state, "to_state": to_state, "trigger": trigger}


async def validate_cluster_config(config: dict) -> ClusterConfigValidation:
    result = ClusterConfigValidation()
    if "name" not in config or not config["name"]:
        result.errors.append("Cluster name is required")
        result.valid = False
    if "cluster_type" in config and config["cluster_type"] not in [c.value for c in ClusterType]:
        result.errors.append(f"Invalid cluster type: {config.get('cluster_type')}")
        result.valid = False
    if "nodes" in config:
        if not isinstance(config["nodes"], int) or config["nodes"] < 1:
            result.errors.append("Nodes must be a positive integer")
            result.valid = False
    if "min_nodes" in config and "max_nodes" in config:
        if config["min_nodes"] > config["max_nodes"]:
            result.errors.append("min_nodes cannot exceed max_nodes")
            result.valid = False
    if "retention_ms" in config and (not isinstance(config["retention_ms"], int) or config["retention_ms"] < 0):
        result.errors.append("retention_ms must be a non-negative integer")
        result.valid = False
    if "replication_factor" in config and config["replication_factor"] < 1:
        result.warnings.append("replication_factor should be at least 1")
    return result


async def get_cluster_utilization(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    total_capacity = cluster.max_nodes * 100
    current_usage = cluster.nodes * cluster.cpu_avg / 100 * 100
    return {
        "cluster_id": cluster_id,
        "nodes_used": cluster.nodes,
        "nodes_available": cluster.max_nodes - cluster.nodes,
        "cpu_utilization_pct": round(cluster.cpu_avg, 1),
        "throughput_utilization_pct": round(min(cluster.throughput_bytes_sec / 1000 * 100, 100), 1),
        "topic_utilization_pct": round(len(cluster.topics) / max(cluster.max_nodes * 10, 1) * 100, 1),
    }


async def search_clusters(query: str) -> list[StreamingCluster]:
    q = query.lower()
    return [c for c in _clusters.values() if q in c.name.lower() or q in c.cluster_type.value.lower() or q in c.status.lower()]


async def get_anomalous_clusters() -> list[dict]:
    anomalies = []
    for cid, cluster in _clusters.items():
        issues = []
        if cluster.cpu_avg > 90:
            issues.append("high_cpu")
        if cluster.status == "failed":
            issues.append("failed_state")
        if cluster.throughput_bytes_sec > 5000 and cluster.nodes == cluster.min_nodes:
            issues.append("potential_underprovisioning")
        if issues:
            anomalies.append({"cluster_id": cid, "name": cluster.name, "issues": issues})
    return anomalies


async def bulk_update_topic_config(cluster_id: str, topic_ids: list[str], retention_ms: int | None = None, cleanup_policy: str | None = None) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    updated = 0
    for topic in cluster.topics:
        if topic.topic_id in topic_ids:
            if retention_ms is not None:
                topic.retention_ms = retention_ms
            if cleanup_policy is not None:
                topic.cleanup_policy = cleanup_policy
            updated += 1
    return {"cluster_id": cluster_id, "updated": updated, "total_requested": len(topic_ids)}


async def get_cluster_replication_report(cluster_id: str) -> dict:
    cluster = _clusters.get(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster {cluster_id} not found")
    under_replicated = [t for t in cluster.topics if t.replication_factor < 2]
    return {
        "cluster_id": cluster_id,
        "total_topics": len(cluster.topics),
        "under_replicated_topics": len(under_replicated),
        "under_replicated_details": [{"name": t.name, "replication_factor": t.replication_factor} for t in under_replicated],
        "avg_replication_factor": round(sum(t.replication_factor for t in cluster.topics) / max(len(cluster.topics), 1), 2),
    }


class StreamingMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class StreamingCache:
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


class StreamingAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, cluster_id: str = "", detail: str = "") -> dict:
        entry = {"action": action, "cluster_id": cluster_id, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_streaming_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    results = []
    for c in _clusters.values():
        if query.lower() in c.name.lower():
            results.append({"cluster_id": c.cluster_id, "name": c.name, "type": c.cluster_type.value, "status": c.status})
            if len(results) >= limit:
                break
    return results


async def recommend_streaming_cleanup(days_threshold: int = 90) -> list[dict]:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    stale = []
    for c in _clusters.values():
        created = datetime.fromisoformat(c.created_at.replace("Z", "+00:00"))
        if created < cutoff and c.status == "completed":
            stale.append({"cluster_id": c.cluster_id, "name": c.name, "created": c.created_at})
    return stale


async def merge_streaming_entities(cluster_ids: list[str]) -> Cluster:
    target_id = cluster_ids[0]
    target = _clusters.get(target_id)
    if not target:
        raise ValueError(f"Cluster {target_id} not found")
    for cid in cluster_ids[1:]:
        source = _clusters.get(cid)
        if source:
            for t in source.topics:
                if not any(ex.name == t.name for ex in target.topics):
                    target.topics.append(t)
            del _clusters[cid]
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
