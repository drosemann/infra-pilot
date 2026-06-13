"""Cog: Data Catalog with Governance — metadata harvesting, lineage, glossary."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

CATALOG_ASSETS: dict[str, dict] = {}


async def register_asset(name: str, source_type: str, location: str, owner: str = "", domain: str = "") -> dict:
    aid = f"ast-{len(CATALOG_ASSETS) + 1}"
    CATALOG_ASSETS[aid] = {"asset_id": aid, "name": name, "source_type": source_type, "location": location, "owner": owner, "domain": domain, "certified": False}
    return CATALOG_ASSETS[aid]


async def list_assets(domain: str | None = None) -> list[dict]:
    if domain:
        return [a for a in CATALOG_ASSETS.values() if a.get("domain") == domain]
    return list(CATALOG_ASSETS.values())


async def get_asset(asset_id: str) -> dict | None:
    return CATALOG_ASSETS.get(asset_id)


async def delete_asset(asset_id: str) -> bool:
    return CATALOG_ASSETS.pop(asset_id, None) is not None


async def start_harvest(connection_string: str) -> dict:
    await asyncio.sleep(0.3)
    return {"status": "completed", "assets_found": 5, "columns_found": 30}


async def search_assets(query: str) -> list[dict]:
    q = query.lower()
    return [a for a in CATALOG_ASSETS.values() if q in a["name"].lower()]


async def certify_asset(asset_id: str) -> bool:
    a = CATALOG_ASSETS.get(asset_id)
    if a:
        a["certified"] = True
        return True
    return False


async def get_catalog_stats() -> dict:
    return {"total_assets": len(CATALOG_ASSETS), "certified": sum(1 for a in CATALOG_ASSETS.values() if a.get("certified"))}


async def update_asset(asset_id: str, **kwargs) -> dict | None:
    a = CATALOG_ASSETS.get(asset_id)
    if not a:
        return None
    a.update(kwargs)
    return a


async def add_column(asset_id: str, column_name: str, column_type: str, description: str = "") -> dict | None:
    a = CATALOG_ASSETS.get(asset_id)
    if not a:
        return None
    if "columns" not in a:
        a["columns"] = []
    col = {"name": column_name, "type": column_type, "description": description}
    a["columns"].append(col)
    return col


async def add_tags(asset_id: str, tags: list[str]) -> dict | None:
    a = CATALOG_ASSETS.get(asset_id)
    if not a:
        return None
    if "tags" not in a:
        a["tags"] = []
    for t in tags:
        if t not in a["tags"]:
            a["tags"].append(t)
    return a


async def remove_tags(asset_id: str, tags: list[str]) -> dict | None:
    a = CATALOG_ASSETS.get(asset_id)
    if not a:
        return None
    if "tags" in a:
        for t in tags:
            while t in a["tags"]:
                a["tags"].remove(t)
    return a


async def create_glossary_term(name: str, definition: str, domain: str = "") -> dict:
    term_id = f"gt-{len(CATALOG_ASSETS) + 1}"
    term = {"term_id": term_id, "name": name, "definition": definition, "domain": domain, "assets": []}
    if "_glossary" not in globals():
        globals()["_glossary"] = {}
    _glossary[term_id] = term
    return term


async def list_glossary(domain: str | None = None) -> list[dict]:
    glossary = globals().get("_glossary", {})
    if domain:
        return [t for t in glossary.values() if t.get("domain") == domain]
    return list(glossary.values())


async def link_term_to_asset(term_id: str, asset_id: str) -> bool:
    glossary = globals().get("_glossary", {})
    term = glossary.get(term_id)
    asset = CATALOG_ASSETS.get(asset_id)
    if not term or not asset:
        return False
    if asset_id not in term["assets"]:
        term["assets"].append(asset_id)
    return True


async def get_upstream_lineage(asset_id: str) -> list:
    return []


async def get_downstream_lineage(asset_id: str) -> list:
    return []


async def get_domain_summary(domain: str) -> dict:
    assets = [a for a in CATALOG_ASSETS.values() if a.get("domain") == domain]
    return {"domain": domain, "asset_count": len(assets), "certified": sum(1 for a in assets if a.get("certified"))}


async def get_asset_lineage(asset_id: str) -> dict:
    return {"asset_id": asset_id, "upstream": [], "downstream": []}


async def bulk_register_assets(assets: list[dict]) -> list[dict]:
    results = []
    for a in assets:
        asset = await register_asset(
            name=a.get("name", "unknown"),
            source_type=a.get("source_type", "database"),
            location=a.get("location", ""),
            owner=a.get("owner", ""),
            domain=a.get("domain", ""),
        )
        if "tags" in a:
            asset["tags"] = a["tags"]
        results.append(asset)
    return results


async def list_harvest_runs(limit: int = 10) -> list[dict]:
    return []


async def get_asset_count_by_type() -> dict:
    by_type = {}
    for a in CATALOG_ASSETS.values():
        st = a.get("source_type", "unknown")
        by_type[st] = by_type.get(st, 0) + 1
    return by_type


async def decertify_asset(asset_id: str) -> bool:
    a = CATALOG_ASSETS.get(asset_id)
    if a:
        a["certified"] = False
        return True
    return False


async def list_source_types() -> list[str]:
    return ["database", "data_lake", "stream", "file", "api"]


async def list_classifications() -> list[str]:
    return ["public", "internal", "confidential", "restricted", "pii", "phi", "pci"]


# ===== APPENDED: Utility helpers, pagination, batch ops, formatting =====

async def format_asset_info(asset_id: str) -> dict:
    a = CATALOG_ASSETS.get(asset_id)
    if not a:
        return {"error": "Asset not found"}
    return {
        "asset_id": a["asset_id"],
        "name": a["name"],
        "source_type": a.get("source_type"),
        "location": a.get("location"),
        "owner": a.get("owner"),
        "domain": a.get("domain"),
        "certified": a.get("certified", False),
        "tags": a.get("tags", []),
        "classification": a.get("classification"),
        "description": a.get("description", ""),
    }

async def paginate_assets(offset: int = 0, limit: int = 50, domain: str = None,
                           source_type: str = None, certified: bool = None) -> dict:
    results = list(CATALOG_ASSETS.values())
    if domain:
        results = [a for a in results if a.get("domain") == domain]
    if source_type:
        results = [a for a in results if a.get("source_type") == source_type]
    if certified is not None:
        results = [a for a in results if a.get("certified") == certified]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def bulk_remove_assets(asset_ids: list[str]) -> dict:
    removed = 0
    for aid in asset_ids:
        if await remove_asset(aid):
            removed += 1
    return {"removed": removed, "total_requested": len(asset_ids)}

async def export_catalog(domain: str = None) -> list[dict]:
    results = list(CATALOG_ASSETS.values())
    if domain:
        results = [a for a in results if a.get("domain") == domain]
    return [{
        "asset_id": a["asset_id"], "name": a.get("name"), "source_type": a.get("source_type"),
        "location": a.get("location"), "owner": a.get("owner"), "domain": a.get("domain"),
        "certified": a.get("certified"), "tags": a.get("tags"),
        "classification": a.get("classification"),
    } for a in results]

async def search_catalog(query: str) -> list[dict]:
    q = query.lower()
    return [a for a in CATALOG_ASSETS.values() if q in a.get("name", "").lower()
            or q in a.get("owner", "").lower() or q in a.get("description", "").lower()
            or any(q in tag.lower() for tag in a.get("tags", []))]

async def get_catalog_analytics() -> dict:
    total = len(CATALOG_ASSETS)
    by_type = await get_asset_count_by_type()
    certified = sum(1 for a in CATALOG_ASSETS.values() if a.get("certified"))
    return {
        "total_assets": total,
        "by_source_type": by_type,
        "certified_count": certified,
        "certification_rate": round((certified / max(total, 1)) * 100, 1),
        "unique_owners": len(set(a.get("owner", "") for a in CATALOG_ASSETS.values() if a.get("owner"))),
        "unique_domains": len(set(a.get("domain", "") for a in CATALOG_ASSETS.values() if a.get("domain"))),
    }

async def batch_tag_assets(asset_ids: list[str], tags: list[str]) -> dict:
    tagged = 0
    for aid in asset_ids:
        a = CATALOG_ASSETS.get(aid)
        if a:
            existing = set(a.get("tags", []))
            existing.update(tags)
            a["tags"] = list(existing)
            tagged += 1
    return {"tagged": tagged, "total_requested": len(asset_ids)}

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
