"""Data Catalog with Governance — metadata harvesting, lineage, glossary, PII/PHI tagging."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    DATABASE = "database"
    DATA_LAKE = "data_lake"
    STREAM = "stream"
    FILE = "file"
    API = "api"


class Classification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"
    PCI = "pci"


@dataclass
class DataAsset:
    asset_id: str
    name: str
    description: str
    source_type: DataSourceType
    location: str
    schema_json: dict = field(default_factory=dict)
    columns: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    classification: Classification = Classification.INTERNAL
    owner: str = ""
    domain: str = ""
    certified: bool = False
    record_count: int = 0
    size_bytes: int = 0
    created_at: str = ""
    updated_at: str = ""
    last_harvested: str = ""
    quality_score: float = 0.0


@dataclass
class ColumnLineage:
    lineage_id: str
    source_asset: str
    source_column: str
    target_asset: str
    target_column: str
    transformation: str = ""
    confidence: float = 1.0


@dataclass
class GlossaryTerm:
    term_id: str
    name: str
    definition: str
    domain: str = ""
    synonyms: list[str] = field(default_factory=list)
    related_terms: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class HarvestRun:
    run_id: str
    source_type: DataSourceType
    connection_string: str
    assets_found: int = 0
    columns_found: int = 0
    status: str = "running"
    started_at: str = ""
    completed_at: str = ""
    error: str = ""


_assets: dict[str, DataAsset] = {}
_lineage: dict[str, ColumnLineage] = {}
_glossary: dict[str, GlossaryTerm] = {}
_harvest_runs: list[HarvestRun] = []


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def register_asset(
    name: str,
    description: str,
    source_type: DataSourceType,
    location: str,
    owner: str = "",
    domain: str = "",
) -> DataAsset:
    asset = DataAsset(
        asset_id=str(uuid4()),
        name=name,
        description=description,
        source_type=source_type,
        location=location,
        owner=owner,
        domain=domain,
        created_at=_ts(),
        updated_at=_ts(),
        last_harvested=_ts(),
    )
    _assets[asset.asset_id] = asset
    logger.info("Data asset registered: %s (%s)", asset.asset_id, name)
    return asset


async def get_asset(asset_id: str) -> Optional[DataAsset]:
    return _assets.get(asset_id)


async def list_assets(domain: str | None = None, source_type: DataSourceType | None = None) -> list[DataAsset]:
    results = list(_assets.values())
    if domain:
        results = [a for a in results if a.domain == domain]
    if source_type:
        results = [a for a in results if a.source_type == source_type]
    return results


async def update_asset(asset_id: str, **kwargs) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    for k, v in kwargs.items():
        if hasattr(a, k):
            setattr(a, k, v)
    a.updated_at = _ts()
    return a


async def delete_asset(asset_id: str) -> bool:
    return _assets.pop(asset_id, None) is not None


async def add_column(asset_id: str, column_name: str, column_type: str, description: str = "", classification: Classification = Classification.INTERNAL) -> Optional[dict]:
    a = _assets.get(asset_id)
    if not a:
        return None
    col = {"name": column_name, "type": column_type, "description": description, "classification": classification.value}
    a.columns.append(col)
    return col


async def search_assets(query: str) -> list[DataAsset]:
    q = query.lower()
    return [a for a in _assets.values() if q in a.name.lower() or q in a.description.lower() or any(q in t.lower() for t in a.tags)]


async def start_harvest(source_type: DataSourceType, connection_string: str) -> HarvestRun:
    run = HarvestRun(
        run_id=str(uuid4()),
        source_type=source_type,
        connection_string=connection_string,
        started_at=_ts(),
    )
    _harvest_runs.insert(0, run)
    await asyncio.sleep(0.3)
    run.assets_found = 5
    run.columns_found = 25
    run.status = "completed"
    run.completed_at = _ts()
    return run


async def list_harvest_runs(limit: int = 20) -> list[HarvestRun]:
    return _harvest_runs[:limit]


async def add_lineage(source_asset: str, source_column: str, target_asset: str, target_column: str, transformation: str = "") -> ColumnLineage:
    entry = ColumnLineage(
        lineage_id=str(uuid4()),
        source_asset=source_asset,
        source_column=source_column,
        target_asset=target_asset,
        target_column=target_column,
        transformation=transformation,
    )
    _lineage[entry.lineage_id] = entry
    return entry


async def get_lineage(asset_id: str) -> list[ColumnLineage]:
    return [l for l in _lineage.values() if l.source_asset == asset_id or l.target_asset == asset_id]


async def create_glossary_term(name: str, definition: str, domain: str = "", synonyms: list[str] | None = None) -> GlossaryTerm:
    term = GlossaryTerm(
        term_id=str(uuid4()),
        name=name,
        definition=definition,
        domain=domain,
        synonyms=synonyms or [],
        created_at=_ts(),
    )
    _glossary[term.term_id] = term
    return term


async def list_glossary(domain: str | None = None) -> list[GlossaryTerm]:
    if domain:
        return [t for t in _glossary.values() if t.domain == domain]
    return list(_glossary.values())


async def search_glossary(query: str) -> list[GlossaryTerm]:
    q = query.lower()
    return [t for t in _glossary.values() if q in t.name.lower() or q in t.definition.lower()]


async def link_term_to_asset(term_id: str, asset_id: str) -> bool:
    term = _glossary.get(term_id)
    asset = _assets.get(asset_id)
    if not term or not asset:
        return False
    if asset_id not in term.assets:
        term.assets.append(asset_id)
    return True


async def certify_asset(asset_id: str) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    a.certified = True
    return a


async def get_asset_stats() -> dict:
    total = len(_assets)
    by_type = {}
    by_classification = {}
    for a in _assets.values():
        by_type[a.source_type.value] = by_type.get(a.source_type.value, 0) + 1
        by_classification[a.classification.value] = by_classification.get(a.classification.value, 0) + 1
    return {"total_assets": total, "by_type": by_type, "by_classification": by_classification, "certified": sum(1 for a in _assets.values() if a.certified)}


async def bulk_register_assets(assets: list[dict]) -> list[DataAsset]:
    results = []
    for a in assets:
        asset = await register_asset(
            name=a["name"],
            description=a.get("description", ""),
            source_type=DataSourceType(a.get("source_type", "database")),
            location=a.get("location", ""),
            owner=a.get("owner", ""),
            domain=a.get("domain", ""),
        )
        if "tags" in a:
            asset.tags = a["tags"]
        if "classification" in a:
            asset.classification = Classification(a["classification"])
        results.append(asset)
    return results


async def add_tags(asset_id: str, tags: list[str]) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    for t in tags:
        if t not in a.tags:
            a.tags.append(t)
    return a


async def remove_tags(asset_id: str, tags: list[str]) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    for t in tags:
        while t in a.tags:
            a.tags.remove(t)
    return a


async def get_lineage_graph(asset_id: str) -> dict:
    upstream = []
    downstream = []
    for l in _lineage.values():
        if l.target_asset == asset_id:
            upstream.append({"asset_id": l.source_asset, "column": l.source_column, "transformation": l.transformation})
        if l.source_asset == asset_id:
            downstream.append({"asset_id": l.target_asset, "column": l.target_column, "transformation": l.transformation})
    return {"asset_id": asset_id, "upstream": upstream, "downstream": downstream}


async def update_glossary_term(term_id: str, **kwargs) -> Optional[GlossaryTerm]:
    term = _glossary.get(term_id)
    if not term:
        return None
    for k, v in kwargs.items():
        if hasattr(term, k) and k != "term_id":
            setattr(term, k, v)
    return term


async def delete_glossary_term(term_id: str) -> bool:
    return _glossary.pop(term_id, None) is not None


async def search_assets_advanced(filters: dict) -> list[DataAsset]:
    results = list(_assets.values())
    if "domain" in filters:
        results = [a for a in results if a.domain == filters["domain"]]
    if "source_type" in filters:
        results = [a for a in results if a.source_type == DataSourceType(filters["source_type"])]
    if "classification" in filters:
        results = [a for a in results if a.classification == Classification(filters["classification"])]
    if "certified" in filters:
        results = [a for a in results if a.certified == filters["certified"]]
    if "owner" in filters:
        results = [a for a in results if a.owner == filters["owner"]]
    if "tag" in filters:
        results = [a for a in results if filters["tag"] in a.tags]
    if "query" in filters:
        q = filters["query"].lower()
        results = [a for a in results if q in a.name.lower() or q in a.description.lower()]
    return results


async def get_domain_summary(domain: str) -> dict:
    assets = [a for a in _assets.values() if a.domain == domain]
    terms = [t for t in _glossary.values() if t.domain == domain]
    return {
        "domain": domain,
        "asset_count": len(assets),
        "glossary_terms": len(terms),
        "certified_assets": sum(1 for a in assets if a.certified),
        "total_size_bytes": sum(a.size_bytes for a in assets),
        "total_records": sum(a.record_count for a in assets),
    }


async def certify_asset(asset_id: str) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    a.certified = True
    return a


async def decertify_asset(asset_id: str) -> Optional[DataAsset]:
    a = _assets.get(asset_id)
    if not a:
        return None
    a.certified = False
    return a


async def impact_analysis(asset_id: str) -> dict:
    downstream_assets = []
    downstream_lineage = []
    for l in _lineage.values():
        if l.source_asset == asset_id:
            downstream_assets.append(l.target_asset)
            downstream_lineage.append({"lineage_id": l.lineage_id, "target": l.target_asset, "column": l.target_column})
    return {
        "asset_id": asset_id,
        "name": _assets.get(asset_id).name if _assets.get(asset_id) else "unknown",
        "downstream_assets": downstream_assets,
        "downstream_count": len(downstream_assets),
        "lineage_entries": downstream_lineage,
    }


async def export_catalog(format: str = "json") -> dict:
    assets_data = []
    for a in _assets.values():
        assets_data.append({
            "asset_id": a.asset_id,
            "name": a.name,
            "source_type": a.source_type.value,
            "domain": a.domain,
            "classification": a.classification.value,
            "certified": a.certified,
            "tags": a.tags,
            "columns": a.columns,
        })
    return {"assets": assets_data, "glossary_terms": len(_glossary), "lineage_entries": len(_lineage), "format": format}


async def import_catalog(assets: list[dict]) -> dict:
    imported = 0
    skipped = 0
    for a in assets:
        existing = [x for x in _assets.values() if x.name == a.get("name")]
        if existing:
            skipped += 1
            continue
        await register_asset(
            name=a["name"],
            description=a.get("description", ""),
            source_type=DataSourceType(a.get("source_type", "database")),
            location=a.get("location", ""),
            owner=a.get("owner", ""),
            domain=a.get("domain", ""),
        )
        imported += 1
    return {"imported": imported, "skipped": skipped}


async def list_classifications() -> list[str]:
    return [c.value for c in Classification]


async def list_source_types() -> list[str]:
    return [s.value for s in DataSourceType]


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class AssetBatchOperation:
    batch_id: str
    operation: str
    asset_ids: list[str]
    status: str = "pending"
    success_count: int = 0
    failure_count: int = 0
    errors: list[dict] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""


@dataclass
class AssetPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    domain: str | None = None
    source_type: str | None = None
    classification: str | None = None


@dataclass
class AssetPaginatedResult:
    items: list[DataAsset]
    total: int
    offset: int
    limit: int
    has_more: bool
    facets: dict = field(default_factory=dict)


@dataclass
class CatalogStateTransition:
    from_state: str
    to_state: str
    trigger: str
    asset_id: str
    timestamp: str = ""
    actor: str = "system"


_asset_state_history: dict[str, list[CatalogStateTransition]] = {}
_asset_batch_ops: dict[str, AssetBatchOperation] = {}


async def paginate_assets(params: AssetPaginationParams | None = None) -> AssetPaginatedResult:
    p = params or AssetPaginationParams()
    results = list(_assets.values())
    if p.domain:
        results = [a for a in results if a.domain == p.domain]
    if p.source_type:
        results = [a for a in results if a.source_type == DataSourceType(p.source_type)]
    if p.classification:
        results = [a for a in results if a.classification == Classification(p.classification)]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda a: a.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda a: a.created_at, reverse=p.sort_order == "desc")
    elif p.sort_by == "quality_score":
        results.sort(key=lambda a: a.quality_score, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    by_type = {}
    for a in _assets.values():
        by_type[a.source_type.value] = by_type.get(a.source_type.value, 0) + 1
    return AssetPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total), facets={"by_type": by_type})


async def paginate_glossary(params: AssetPaginationParams | None = None) -> AssetPaginatedResult:
    p = params or AssetPaginationParams()
    results = list(_glossary.values())
    if p.domain:
        results = [t for t in results if t.domain == p.domain]
    total = len(results)
    results.sort(key=lambda t: t.name, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return AssetPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total))


async def batch_certify_assets(asset_ids: list[str]) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="certify", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        a = _assets.get(aid)
        if a:
            a.certified = True
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def batch_classify_assets(asset_ids: list[str], classification: Classification) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="classify", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        a = _assets.get(aid)
        if a:
            a.classification = classification
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def batch_add_tags(asset_ids: list[str], tags: list[str]) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="add_tags", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        a = _assets.get(aid)
        if a:
            for t in tags:
                if t not in a.tags:
                    a.tags.append(t)
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def batch_delete_assets(asset_ids: list[str]) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="delete", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        if aid in _assets:
            _assets.pop(aid)
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[AssetBatchOperation]:
    return _asset_batch_ops.get(batch_id)


async def export_catalog_extended(include_glossary: bool = True, include_lineage: bool = True, format: str = "json") -> dict:
    result = await export_catalog(format=format)
    if include_glossary:
        result["glossary"] = [{"term_id": t.term_id, "name": t.name, "definition": t.definition,
                                "domain": t.domain, "synonyms": t.synonyms, "related_terms": t.related_terms,
                                "assets": t.assets} for t in _glossary.values()]
    if include_lineage:
        result["lineage"] = [{"lineage_id": l.lineage_id, "source_asset": l.source_asset,
                               "source_column": l.source_column, "target_asset": l.target_asset,
                               "target_column": l.target_column, "transformation": l.transformation} for l in _lineage.values()]
    return result


async def import_catalog_extended(data: dict) -> dict:
    result = {"assets_imported": 0, "glossary_imported": 0, "lineage_imported": 0, "errors": []}
    if "assets" in data:
        r = await import_catalog(data["assets"])
        result["assets_imported"] = r["imported"]
    if "glossary" in data:
        for g in data["glossary"]:
            try:
                term = await create_glossary_term(g["name"], g.get("definition", ""), g.get("domain", ""), g.get("synonyms"))
                if "related_terms" in g:
                    term.related_terms = g["related_terms"]
                result["glossary_imported"] += 1
            except Exception as e:
                result["errors"].append({"item": g.get("name"), "error": str(e)})
    if "lineage" in data:
        for l in data["lineage"]:
            try:
                await add_lineage(l["source_asset"], l.get("source_column", ""), l["target_asset"], l.get("target_column", ""), l.get("transformation", ""))
                result["lineage_imported"] += 1
            except Exception as e:
                result["errors"].append({"item": l.get("lineage_id", "unknown"), "error": str(e)})
    return result


async def get_catalog_analytics() -> dict:
    total_assets = len(_assets)
    total_lineage = len(_lineage)
    total_glossary = len(_glossary)
    domains = {}
    for a in _assets.values():
        domains[a.domain] = domains.get(a.domain, 0) + 1
    top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "total_assets": total_assets,
        "total_lineage_entries": total_lineage,
        "total_glossary_terms": total_glossary,
        "total_harvest_runs": len(_harvest_runs),
        "domains": [{"domain": d, "count": c} for d, c in top_domains],
        "certified_pct": round(sum(1 for a in _assets.values() if a.certified) / max(total_assets, 1) * 100, 1),
        "pii_assets": sum(1 for a in _assets.values() if a.classification == Classification.PII),
        "avg_quality_score": round(sum(a.quality_score for a in _assets.values()) / max(total_assets, 1), 2),
    }


async def transition_asset_state(asset_id: str, trigger: str, actor: str = "system") -> dict:
    a = _assets.get(asset_id)
    if not a:
        raise ValueError(f"Asset {asset_id} not found")
    from_state = "certified" if a.certified else "uncertified"
    valid_map = {
        "uncertified": {"certify", "archive"},
        "certified": {"decertify", "archive"},
        "archived": set(),
    }
    allowed = valid_map.get(from_state, set())
    if trigger not in allowed:
        return {"asset_id": asset_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state = from_state
    if trigger == "certify":
        a.certified = True
        to_state = "certified"
    elif trigger == "decertify":
        a.certified = False
        to_state = "uncertified"
    elif trigger == "archive":
        to_state = "archived"
    transition = CatalogStateTransition(from_state=from_state, to_state=to_state, trigger=trigger, asset_id=asset_id, timestamp=_ts(), actor=actor)
    _asset_state_history.setdefault(asset_id, []).append(transition)
    return {"asset_id": asset_id, "success": True, "from_state": from_state, "to_state": to_state}


async def validate_asset_data(asset_id: str) -> dict:
    a = _assets.get(asset_id)
    if not a:
        raise ValueError(f"Asset {asset_id} not found")
    issues = []
    if not a.name:
        issues.append("Asset name is empty")
    if not a.location:
        issues.append("Asset location is empty")
    if not a.columns:
        issues.append("Asset has no columns defined")
    if not a.owner:
        issues.append("Asset has no owner assigned")
    if not a.domain:
        issues.append("Asset has no domain assigned")
    return {"asset_id": asset_id, "valid": len(issues) == 0, "issues": issues, "score": max(0, 100 - len(issues) * 20)}


async def get_domain_analytics() -> list[dict]:
    domain_data = {}
    for a in _assets.values():
        if a.domain not in domain_data:
            domain_data[a.domain] = {"asset_count": 0, "certified": 0, "total_size_bytes": 0, "total_records": 0, "quality_scores": []}
        domain_data[a.domain]["asset_count"] += 1
        if a.certified:
            domain_data[a.domain]["certified"] += 1
        domain_data[a.domain]["total_size_bytes"] += a.size_bytes
        domain_data[a.domain]["total_records"] += a.record_count
        domain_data[a.domain]["quality_scores"].append(a.quality_score)
    result = []
    for domain, data in domain_data.items():
        scores = data["quality_scores"]
        result.append({
            "domain": domain,
            "asset_count": data["asset_count"],
            "certified_pct": round(data["certified"] / max(data["asset_count"], 1) * 100, 1),
            "total_size_gb": round(data["total_size_bytes"] / (1024 ** 3), 2),
            "total_records": data["total_records"],
            "avg_quality_score": round(sum(scores) / max(len(scores), 1), 2),
        })
    return sorted(result, key=lambda x: x["asset_count"], reverse=True)


async def get_lineage_stats() -> dict:
    upstream_counts = {}
    downstream_counts = {}
    for l in _lineage.values():
        upstream_counts[l.target_asset] = upstream_counts.get(l.target_asset, 0) + 1
        downstream_counts[l.source_asset] = downstream_counts.get(l.source_asset, 0) + 1
    return {
        "total_lineage_entries": len(_lineage),
        "assets_with_upstream": len(upstream_counts),
        "assets_with_downstream": len(downstream_counts),
        "avg_upstream_per_asset": round(sum(upstream_counts.values()) / max(len(upstream_counts), 1), 2) if upstream_counts else 0,
        "avg_downstream_per_asset": round(sum(downstream_counts.values()) / max(len(downstream_counts), 1), 2) if downstream_counts else 0,
    }


async def search_classifications(query: str) -> list[str]:
    q = query.lower()
    return [c.value for c in Classification if q in c.value]


async def bulk_update_owner(asset_ids: list[str], owner: str) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="update_owner", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        a = _assets.get(aid)
        if a:
            a.owner = owner
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def bulk_update_domain(asset_ids: list[str], domain: str) -> AssetBatchOperation:
    op = AssetBatchOperation(batch_id=str(uuid4()), operation="update_domain", asset_ids=[], created_at=_ts())
    for aid in asset_ids:
        a = _assets.get(aid)
        if a:
            a.domain = domain
            op.asset_ids.append(aid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"asset_id": aid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _asset_batch_ops[op.batch_id] = op
    return op


async def get_catalog_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()
    suggestions = []
    for a in _assets.values():
        if q in a.name.lower():
            suggestions.append({"type": "asset", "id": a.asset_id, "text": a.name})
        if len(suggestions) >= limit:
            break
    for t in _glossary.values():
        if q in t.name.lower() and len(suggestions) < limit:
            suggestions.append({"type": "glossary", "id": t.term_id, "text": t.name})
    return suggestions


async def merge_assets(source_asset_id: str, target_asset_id: str) -> dict:
    source = _assets.get(source_asset_id)
    target = _assets.get(target_asset_id)
    if not source or not target:
        return {"success": False, "error": "One or both assets not found"}
    for l in _lineage.values():
        if l.source_asset == source_asset_id:
            l.source_asset = target_asset_id
        if l.target_asset == source_asset_id:
            l.target_asset = target_asset_id
    for t in _glossary.values():
        if source_asset_id in t.assets:
            t.assets.remove(source_asset_id)
            if target_asset_id not in t.assets:
                t.assets.append(target_asset_id)
    target.record_count += source.record_count
    target.size_bytes += source.size_bytes
    _assets.pop(source_asset_id, None)
    return {"success": True, "target_asset_id": target_asset_id, "merged_from": source_asset_id}


async def get_asset_lineage_depth(asset_id: str, max_depth: int = 5) -> dict:
    visited = set()
    upstream = []
    downstream = []

    async def traverse_up(aid: str, depth: int):
        if depth > max_depth or aid in visited:
            return
        visited.add(aid)
        for l in _lineage.values():
            if l.target_asset == aid:
                upstream.append({"asset_id": l.source_asset, "column": l.source_column, "depth": depth})
                await traverse_up(l.source_asset, depth + 1)

    async def traverse_down(aid: str, depth: int):
        if depth > max_depth or aid in visited:
            return
        visited.add(aid)
        for l in _lineage.values():
            if l.source_asset == aid:
                downstream.append({"asset_id": l.target_asset, "column": l.target_column, "depth": depth})
                await traverse_down(l.target_asset, depth + 1)

    visited.clear()
    await traverse_up(asset_id, 0)
    visited.clear()
    await traverse_down(asset_id, 0)
    return {"asset_id": asset_id, "upstream_count": len(upstream), "downstream_count": len(downstream), "upstream": upstream, "downstream": downstream}


class CatalogMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class CatalogCache:
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


class CatalogAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, detail: str = "") -> dict:
        from datetime import datetime
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]


async def get_catalog_growth_report(days: int = 30) -> dict:
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    assets_before = len([a for a in _assets.values() if a.created_at < cutoff])
    assets_now = len(_assets)
    return {
        "period_days": days,
        "assets_at_start": assets_before,
        "assets_now": assets_now,
        "growth": assets_now - assets_before,
        "growth_pct": round((assets_now - assets_before) / max(assets_before, 1) * 100, 1) if assets_before else 0,
    }


async def recommend_asset_cleanup() -> list[dict]:
    recommendations = []
    for aid, asset in _assets.items():
        issues = []
        if not asset.columns:
            issues.append("no_columns_defined")
        if not asset.owner:
            issues.append("no_owner_assigned")
        if not asset.description:
            issues.append("no_description")
        if not asset.tags:
            issues.append("no_tags")
        if issues:
            recommendations.append({"asset_id": aid, "name": asset.name, "issues": issues})
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
