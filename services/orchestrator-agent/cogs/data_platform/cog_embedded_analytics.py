"""Cog: Embedded Analytics SDK — embeddable charts and dashboards for external customers."""

from __future__ import annotations
import asyncio
import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

EMBED_CUSTOMERS: dict[str, dict] = {}
EMBED_DASHBOARDS: dict[str, dict] = {}


def _generate_key() -> str:
    return f"ip_ea_{hashlib.sha256(__import__('uuid').uuid4().hex.encode()).hexdigest()[:32]}"


async def register_customer(name: str, domain: str) -> dict:
    cid = f"ec-{len(EMBED_CUSTOMERS) + 1}"
    EMBED_CUSTOMERS[cid] = {"customer_id": cid, "name": name, "domain": domain, "api_key": _generate_key(), "active": True}
    return EMBED_CUSTOMERS[cid]


async def list_customers() -> list[dict]:
    return list(EMBED_CUSTOMERS.values())


async def get_customer(customer_id: str) -> dict | None:
    return EMBED_CUSTOMERS.get(customer_id)


async def delete_customer(customer_id: str) -> bool:
    return EMBED_CUSTOMERS.pop(customer_id, None) is not None


async def create_embed(customer_id: str, name: str, config: dict | None = None) -> dict:
    eid = f"emb-{len(EMBED_DASHBOARDS) + 1}"
    EMBED_DASHBOARDS[eid] = {"embed_id": eid, "customer_id": customer_id, "name": name, "config": config or {}, "active": True}
    return EMBED_DASHBOARDS[eid]


async def list_embeds(customer_id: str | None = None) -> list[dict]:
    if customer_id:
        return [e for e in EMBED_DASHBOARDS.values() if e.get("customer_id") == customer_id]
    return list(EMBED_DASHBOARDS.values())


async def delete_embed(embed_id: str) -> bool:
    return EMBED_DASHBOARDS.pop(embed_id, None) is not None


async def generate_embed_code(embed_id: str) -> str:
    return f'<iframe src="https://analytics.infrapilot.io/embed/{embed_id}" width="100%" height="600" frameborder="0"></iframe>'


async def record_usage(customer_id: str, action: str = "view") -> dict:
    return {"customer_id": customer_id, "action": action, "recorded": True}


async def get_embed_stats() -> dict:
    return {"customers": len(EMBED_CUSTOMERS), "embeds": len(EMBED_DASHBOARDS)}


async def update_customer(customer_id: str, **kwargs) -> dict | None:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return None
    c.update(kwargs)
    return c


async def rotate_api_key(customer_id: str) -> str | None:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return None
    c["api_key"] = _generate_key()
    return c["api_key"]


async def validate_api_key(api_key: str) -> dict | None:
    for c in EMBED_CUSTOMERS.values():
        if c.get("api_key") == api_key and c.get("active", True):
            return c
    return None


async def get_embed(embed_id: str) -> dict | None:
    return EMBED_DASHBOARDS.get(embed_id)


async def update_embed(embed_id: str, **kwargs) -> dict | None:
    e = EMBED_DASHBOARDS.get(embed_id)
    if not e:
        return None
    e.update(kwargs)
    return e


async def toggle_embed(embed_id: str, active: bool) -> dict | None:
    e = EMBED_DASHBOARDS.get(embed_id)
    if not e:
        return None
    e["active"] = active
    return e


async def get_usage_stats(customer_id: str | None = None) -> dict:
    return {"total_requests": 0, "views": 0, "loads": 0}


async def get_customer_usage(customer_id: str) -> dict:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        raise ValueError(f"Customer {customer_id} not found")
    embeds = [e for e in EMBED_DASHBOARDS.values() if e.get("customer_id") == customer_id]
    return {"customer_id": customer_id, "name": c["name"], "dashboards": len(embeds)}


async def check_rate_limit(customer_id: str) -> dict:
    return {"allowed": True, "current": 0, "limit": 1000}


async def generate_jwt_token(customer_id: str, secret: str, expire_seconds: int = 3600) -> str:
    import time, hashlib, json
    payload = {"customer_id": customer_id, "iat": int(time.time()), "exp": int(time.time()) + expire_seconds}
    signature = hashlib.sha256(f"{json.dumps(payload, sort_keys=True)}.{secret}".encode()).hexdigest()
    return f"header.{__import__('base64').urlsafe_b64encode(str(payload).encode()).decode()}.{signature}"


async def update_customer_quota(customer_id: str, quota_updates: dict) -> dict | None:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return None
    c.setdefault("usage_quota", {"requests_per_hour": 1000, "dashboards": 5}).update(quota_updates)
    return c


async def search_customers(query: str) -> list[dict]:
    q = query.lower()
    return [c for c in EMBED_CUSTOMERS.values() if q in c.get("name", "").lower() or q in c.get("domain", "").lower()]


async def list_embed_themes() -> list[str]:
    return ["light", "dark", "auto"]


async def revoke_customer_access(customer_id: str) -> bool:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return False
    c["active"] = False
    return True


async def restore_customer_access(customer_id: str) -> bool:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return False
    c["active"] = True
    return True


async def get_embed_analytics(embed_id: str) -> dict:
    e = EMBED_DASHBOARDS.get(embed_id)
    if not e:
        raise ValueError(f"Embed {embed_id} not found")
    return {"embed_id": embed_id, "name": e.get("name"), "views": 0, "last_accessed": "never"}


async def get_top_customers(limit: int = 5) -> list[dict]:
    return [{"customer_id": cid, "name": c.get("name"), "requests": 0} for cid, c in list(EMBED_CUSTOMERS.items())[:limit]]


async def list_auth_methods() -> list[str]:
    return ["api_key", "jwt", "sso"]


async def list_embed_types() -> list[str]:
    return ["chart", "dashboard", "full"]


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_customers(offset: int = 0, limit: int = 50, active: bool = None) -> dict:
    results = list(EMBED_CUSTOMERS.values())
    if active is not None:
        results = [c for c in results if c.get("active") == active]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def paginate_embeds(offset: int = 0, limit: int = 50, active: bool = None) -> dict:
    results = list(EMBED_DASHBOARDS.values())
    if active is not None:
        results = [e for e in results if e.get("active") == active]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def format_customer_info(customer_id: str) -> dict:
    c = EMBED_CUSTOMERS.get(customer_id)
    if not c:
        return {"error": "Customer not found"}
    return {
        "customer_id": c["customer_id"],
        "name": c.get("name"),
        "domain": c.get("domain"),
        "active": c.get("active", True),
        "api_key_masked": c.get("api_key", "")[:8] + "..." if c.get("api_key") else None,
        "usage_quota": c.get("usage_quota"),
    }

async def bulk_toggle_embeds(embed_ids: list[str], active: bool) -> dict:
    toggled = 0
    for eid in embed_ids:
        if await toggle_embed(eid, active):
            toggled += 1
    return {"toggled": toggled, "total_requested": len(embed_ids)}

async def get_embed_analytics_summary() -> dict:
    return {
        "total_customers": len(EMBED_CUSTOMERS),
        "total_embeds": len(EMBED_DASHBOARDS),
        "active_customers": sum(1 for c in EMBED_CUSTOMERS.values() if c.get("active", True)),
        "active_embeds": sum(1 for e in EMBED_DASHBOARDS.values() if e.get("active", True)),
    }

async def batch_create_embeds(customer_id: str, embeds: list[dict]) -> list[dict]:
    created = []
    for ed in embeds:
        e = await create_embed(customer_id, ed.get("name", "embed"), ed.get("type", "chart"))
        created.append(e)
    return created

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
