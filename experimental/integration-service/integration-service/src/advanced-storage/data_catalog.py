"""Data Catalog integration module."""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    TIMESCALEDB = "timescaledb"
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"
    AVRO = "avro"
    KAFKA = "kafka"
    ICEBERG = "iceberg"
    DELTA = "delta"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"


@dataclass
class DataAsset:
    asset_id: str
    name: str
    description: str
    type: DataSourceType
    location: str
    schema_definition: str
    size_bytes: int
    record_count: int
    partition_count: int
    owner: str
    team: str
    created_at: str
    last_updated: str
    quality_score: float
    freshness_score: float
    completeness_score: float
    tags: List[str]
    classification: str
    pii: bool
    encrypted: bool
    backup_frequency: str
    retention_days: int
    lineage: List[str]
    upstream_dependencies: List[str]
    downstream_consumers: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "location": self.location,
            "schema_definition": self.schema_definition,
            "size_bytes": self.size_bytes,
            "size_display": self._format_size(),
            "record_count": self.record_count,
            "partition_count": self.partition_count,
            "owner": self.owner,
            "team": self.team,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "quality_score": round(self.quality_score, 1),
            "freshness_score": round(self.freshness_score, 1),
            "completeness_score": round(self.completeness_score, 1),
            "tags": self.tags,
            "classification": self.classification,
            "pii": self.pii,
            "encrypted": self.encrypted,
            "backup_frequency": self.backup_frequency,
            "retention_days": self.retention_days,
            "lineage": self.lineage,
            "upstream_dependencies": self.upstream_dependencies,
            "downstream_consumers": self.downstream_consumers,
        }

    def _format_size(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 ** 2:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 ** 3:
            return f"{self.size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{self.size_bytes / 1024 ** 3:.2f} GB"


@dataclass
class DiscoveryResult:
    discovery_id: str
    asset_id: str
    discovered_at: str
    schema_snapshot: str
    record_sample: List[Dict[str, Any]]
    anomalies: List[str]
    quality_issues: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discovery_id": self.discovery_id,
            "asset_id": self.asset_id,
            "discovered_at": self.discovered_at,
            "anomalies": self.anomalies,
            "quality_issues": self.quality_issues,
            "recommendations": self.recommendations,
        }


@dataclass
class LineageNode:
    node_id: str
    asset_id: str
    asset_name: str
    asset_type: str
    parents: List[str]
    children: List[str]
    transformation: str
    last_run: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "parents": self.parents,
            "children": self.children,
            "transformation": self.transformation,
            "last_run": self.last_run,
        }


class DataCatalog:
    """Automated data discovery, schema detection, and lineage tracking."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.assets: Dict[str, DataAsset] = {}
        self.discoveries: Dict[str, DiscoveryResult] = {}
        self.lineage_graph: Dict[str, LineageNode] = {}
        self._running = False
        self._discovery_count = 0
        self._total_records_cataloged = 0
        self._search_history: List[str] = []

    async def initialize(self) -> None:
        self._running = True
        logger.info("Data Catalog initialized")

    async def close(self) -> None:
        self._running = False
        logger.info("Data Catalog shut down")

    async def register_asset(
        self,
        name: str,
        description: str,
        type: str,
        location: str,
        schema_definition: str,
        owner: str = "data-team",
        team: str = "data",
        tags: Optional[List[str]] = None,
        classification: str = "internal",
        pii: bool = False,
        encrypted: bool = True,
        backup_frequency: str = "daily",
        retention_days: int = 365,
        record_count: int = 0,
        size_bytes: int = 0,
    ) -> DataAsset:
        asset = DataAsset(
            asset_id=f"ds-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            type=DataSourceType(type),
            location=location,
            schema_definition=schema_definition,
            size_bytes=size_bytes,
            record_count=record_count,
            partition_count=0,
            owner=owner,
            team=team,
            created_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            quality_score=100.0,
            freshness_score=100.0,
            completeness_score=100.0,
            tags=tags or [],
            classification=classification,
            pii=pii,
            encrypted=encrypted,
            backup_frequency=backup_frequency,
            retention_days=retention_days,
            lineage=[],
            upstream_dependencies=[],
            downstream_consumers=[],
        )
        self.assets[asset.asset_id] = asset
        self._total_records_cataloged += record_count
        logger.info(f"Registered asset '{name}' ({type})")
        return asset

    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        asset = self.assets.get(asset_id)
        return asset.to_dict() if asset else None

    async def list_assets(
        self,
        type: Optional[str] = None,
        owner: Optional[str] = None,
        tag: Optional[str] = None,
        classification: Optional[str] = None,
        pii_only: bool = False,
    ) -> List[Dict[str, Any]]:
        results = list(self.assets.values())
        if type:
            results = [a for a in results if a.type.value == type]
        if owner:
            results = [a for a in results if a.owner == owner]
        if tag:
            results = [a for a in results if tag in a.tags]
        if classification:
            results = [a for a in results if a.classification == classification]
        if pii_only:
            results = [a for a in results if a.pii]
        return [a.to_dict() for a in sorted(results, key=lambda x: x.last_updated, reverse=True)]

    async def search_assets(
        self,
        query: str,
        search_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for asset in self.assets.values():
            if query_lower in asset.name.lower():
                results.append(asset)
                continue
            if query_lower in asset.description.lower():
                results.append(asset)
                continue
            if any(query_lower in t.lower() for t in asset.tags):
                results.append(asset)
                continue
        self._search_history.append(query)
        return [a.to_dict() for a in results[:50]]

    async def update_asset(
        self,
        asset_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        asset.last_updated = datetime.utcnow().isoformat()
        return asset.to_dict()

    async def delete_asset(self, asset_id: str) -> bool:
        if asset_id not in self.assets:
            return False
        del self.assets[asset_id]
        return True

    async def add_lineage(
        self,
        asset_id: str,
        parent_ids: List[str],
        child_ids: List[str],
        transformation: str = "etl",
    ) -> LineageNode:
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")

        node = LineageNode(
            node_id=f"ln-{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            asset_name=asset.name,
            asset_type=asset.type.value,
            parents=parent_ids,
            children=child_ids,
            transformation=transformation,
            last_run=datetime.utcnow().isoformat(),
        )
        self.lineage_graph[asset_id] = node

        for parent_id in parent_ids:
            if parent_id in self.assets:
                if asset_id not in self.assets[parent_id].downstream_consumers:
                    self.assets[parent_id].downstream_consumers.append(asset_id)
                if parent_id not in asset.upstream_dependencies:
                    asset.upstream_dependencies.append(parent_id)

        for child_id in child_ids:
            if child_id in self.assets:
                if asset_id not in self.assets[child_id].upstream_dependencies:
                    self.assets[child_id].upstream_dependencies.append(asset_id)
                if child_id not in asset.downstream_consumers:
                    asset.downstream_consumers.append(child_id)

        asset.lineage.append(transformation)
        return node

    async def get_lineage_graph(self, asset_id: str) -> Dict[str, Any]:
        node = self.lineage_graph.get(asset_id)
        if not node:
            return {"node": None, "upstream": [], "downstream": []}

        upstream = [self.assets.get(pid).to_dict() if self.assets.get(pid) else pid for pid in node.parents]
        downstream = [self.assets.get(cid).to_dict() if self.assets.get(cid) else cid for cid in node.children]
        return {"node": node.to_dict(), "upstream": upstream, "downstream": downstream}

    async def run_discovery(self, asset_id: str) -> DiscoveryResult:
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")

        anomalies = []
        quality_issues = []
        recommendations = []

        if asset.record_count == 0:
            anomalies.append("Asset has zero records")
            recommendations.append("Verify data source connectivity")

        if asset.quality_score < 50:
            quality_issues.append("Quality score critically low")
            recommendations.append("Run data quality pipeline")

        result = DiscoveryResult(
            discovery_id=f"disc-{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            discovered_at=datetime.utcnow().isoformat(),
            schema_snapshot=asset.schema_definition,
            record_sample=[],
            anomalies=anomalies,
            quality_issues=quality_issues,
            recommendations=recommendations,
        )
        self.discoveries[result.discovery_id] = result
        self._discovery_count += 1
        return result

    async def get_quality_report(self, asset_id: str) -> Dict[str, Any]:
        asset = self.assets.get(asset_id)
        if not asset:
            return {}
        return {
            "asset_name": asset.name,
            "quality_score": asset.quality_score,
            "freshness_score": asset.freshness_score,
            "completeness_score": asset.completeness_score,
            "overall_health": round((asset.quality_score + asset.freshness_score + asset.completeness_score) / 3, 1),
            "pii_flagged": asset.pii,
            "encrypted": asset.encrypted,
            "last_updated": asset.last_updated,
            "classification": asset.classification,
        }

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_assets": len(self.assets),
            "total_records": self._total_records_cataloged,
            "total_size_bytes": sum(a.size_bytes for a in self.assets.values()),
            "total_size_display": self._format_bytes(sum(a.size_bytes for a in self.assets.values())),
            "discoveries_performed": self._discovery_count,
            "pii_assets": sum(1 for a in self.assets.values() if a.pii),
            "avg_quality": round(sum(a.quality_score for a in self.assets.values()) / max(len(self.assets), 1), 1),
            "asset_types": list(set(a.type.value for a in self.assets.values())),
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "assets_cataloged": len(self.assets),
        }

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"
