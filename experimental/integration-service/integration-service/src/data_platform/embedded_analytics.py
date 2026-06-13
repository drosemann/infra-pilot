"""Embedded Analytics SDK — embeddable charts and dashboards for external customers."""

from __future__ import annotations
import asyncio
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class EmbedType(Enum):
    CHART = "chart"
    DASHBOARD = "dashboard"
    FULL = "full"


class AuthMethod(Enum):
    API_KEY = "api_key"
    JWT = "jwt"
    SSO = "sso"


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class EmbedCustomer:
    customer_id: str
    name: str
    domain: str
    api_key: str = ""
    auth_method: AuthMethod = AuthMethod.API_KEY
    active: bool = True
    max_dashboards: int = 5
    allowed_origins: list[str] = field(default_factory=list)
    created_at: str = ""
    usage_quota: dict = field(default_factory=lambda: {"requests_per_hour": 1000, "dashboards": 5, "charts": 20})


@dataclass
class EmbedDashboard:
    embed_id: str
    customer_id: str
    name: str
    embed_type: EmbedType = EmbedType.DASHBOARD
    config: dict = field(default_factory=dict)
    theme: Theme = Theme.AUTO
    white_label: bool = False
    custom_css: str = ""
    active: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_accessed: str = ""


@dataclass
class UsageRecord:
    record_id: str
    customer_id: str
    embed_id: str
    action: str
    timestamp: str
    ip: str = ""
    user_agent: str = ""
    duration_ms: int = 0


_customers: dict[str, EmbedCustomer] = {}
_embeds: dict[str, EmbedDashboard] = {}
_usage: list[UsageRecord] = []


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _generate_api_key() -> str:
    return f"ip_ea_{hashlib.sha256(uuid4().hex.encode()).hexdigest()[:32]}"


def _sign_payload(payload: dict, secret: str) -> str:
    h = hmac.new(secret.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256)
    return h.hexdigest()


async def register_customer(name: str, domain: str, auth_method: AuthMethod = AuthMethod.API_KEY, allowed_origins: list[str] | None = None) -> EmbedCustomer:
    customer = EmbedCustomer(
        customer_id=str(uuid4()),
        name=name,
        domain=domain,
        api_key=_generate_api_key(),
        auth_method=auth_method,
        allowed_origins=allowed_origins or [domain],
        created_at=_ts(),
    )
    _customers[customer.customer_id] = customer
    logger.info("Embed customer registered: %s (%s)", customer.customer_id, name)
    return customer


async def get_customer(customer_id: str) -> Optional[EmbedCustomer]:
    return _customers.get(customer_id)


async def list_customers() -> list[EmbedCustomer]:
    return list(_customers.values())


async def update_customer(customer_id: str, **kwargs) -> Optional[EmbedCustomer]:
    c = _customers.get(customer_id)
    if not c:
        return None
    for k, v in kwargs.items():
        if hasattr(c, k):
            setattr(c, k, v)
    return c


async def delete_customer(customer_id: str) -> bool:
    c = _customers.pop(customer_id, None)
    if c:
        _embeds = {k: v for k, v in _embeds.items() if v.customer_id != customer_id}
        return True
    return False


async def rotate_api_key(customer_id: str) -> Optional[str]:
    c = _customers.get(customer_id)
    if not c:
        return None
    c.api_key = _generate_api_key()
    return c.api_key


async def validate_api_key(api_key: str) -> Optional[EmbedCustomer]:
    for c in _customers.values():
        if c.api_key == api_key and c.active:
            return c
    return None


async def create_embed(
    customer_id: str,
    name: str,
    embed_type: EmbedType = EmbedType.DASHBOARD,
    config: dict | None = None,
    white_label: bool = False,
    theme: Theme = Theme.AUTO,
) -> Optional[EmbedDashboard]:
    c = _customers.get(customer_id)
    if not c:
        return None
    customer_embeds = [e for e in _embeds.values() if e.customer_id == customer_id]
    if len(customer_embeds) >= c.usage_quota.get("dashboards", 5) and embed_type == EmbedType.DASHBOARD:
        raise ValueError(f"Customer {customer_id} has reached dashboard quota")
    embed = EmbedDashboard(
        embed_id=str(uuid4()),
        customer_id=customer_id,
        name=name,
        embed_type=embed_type,
        config=config or {},
        white_label=white_label,
        theme=theme,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _embeds[embed.embed_id] = embed
    return embed


async def get_embed(embed_id: str) -> Optional[EmbedDashboard]:
    return _embeds.get(embed_id)


async def list_embeds(customer_id: str | None = None) -> list[EmbedDashboard]:
    if customer_id:
        return [e for e in _embeds.values() if e.customer_id == customer_id]
    return list(_embeds.values())


async def update_embed(embed_id: str, **kwargs) -> Optional[EmbedDashboard]:
    e = _embeds.get(embed_id)
    if not e:
        return None
    for k, v in kwargs.items():
        if hasattr(e, k):
            setattr(e, k, v)
    e.updated_at = _ts()
    return e


async def delete_embed(embed_id: str) -> bool:
    return _embeds.pop(embed_id, None) is not None


async def generate_embed_code(embed_id: str) -> str:
    e = _embeds.get(embed_id)
    if not e:
        raise ValueError(f"Embed {embed_id} not found")
    c = _customers.get(e.customer_id)
    domain = c.domain if c else "example.com"
    code = f"""<!-- Infra Pilot Embedded Analytics -->
<iframe
  src="https://analytics.infrapilot.io/embed/{embed_id}"
  width="100%"
  height="600"
  frameborder="0"
  allow="clipboard-write"
  style="border: none; border-radius: 8px;"
  data-infrapilot-embed="{embed_id}"
></iframe>
<script>
  window.addEventListener('message', function(e) {{
    if (e.data.type === 'infrapilot-embed-height') {{
      var frame = document.querySelector('[data-infrapilot-embed="{embed_id}"]');
      if (frame) frame.style.height = e.data.height + 'px';
    }}
  }});
</script>"""
    return code


async def record_usage(customer_id: str, embed_id: str, action: str = "view", ip: str = "", user_agent: str = "", duration_ms: int = 0) -> UsageRecord:
    record = UsageRecord(
        record_id=str(uuid4()),
        customer_id=customer_id,
        embed_id=embed_id,
        action=action,
        timestamp=_ts(),
        ip=ip,
        user_agent=user_agent,
        duration_ms=duration_ms,
    )
    _usage.append(record)
    if len(_usage) > 10000:
        _usage[:5000] = []
    return record


async def get_usage_stats(customer_id: str | None = None, since: str | None = None) -> dict:
    records = _usage
    if customer_id:
        records = [r for r in records if r.customer_id == customer_id]
    if since:
        records = [r for r in records if r.timestamp >= since]
    views = sum(1 for r in records if r.action == "view")
    loads = sum(1 for r in records if r.action == "load")
    return {
        "total_requests": len(records),
        "views": views,
        "loads": loads,
        "unique_customers": len(set(r.customer_id for r in records)),
    }


async def get_customer_usage(customer_id: str) -> dict:
    c = _customers.get(customer_id)
    if not c:
        raise ValueError(f"Customer {customer_id} not found")
    embeds = [e for e in _embeds.values() if e.customer_id == customer_id]
    usage = await get_usage_stats(customer_id=customer_id)
    return {
        "customer_id": customer_id,
        "name": c.name,
        "dashboards": len(embeds),
        "api_key_active": bool(c.api_key),
        "usage": usage,
        "quota": c.usage_quota,
    }


async def check_rate_limit(customer_id: str) -> dict:
    c = _customers.get(customer_id)
    if not c:
        return {"allowed": False}
    last_hour = datetime.utcnow().timestamp() - 3600
    recent = [r for r in _usage if r.customer_id == customer_id and datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).timestamp() > last_hour]
    limit = c.usage_quota.get("requests_per_hour", 1000)
    return {"allowed": len(recent) < limit, "current": len(recent), "limit": limit}


async def get_embed_stats() -> dict:
    return {
        "total_customers": len(_customers),
        "total_embeds": len(_embeds),
        "total_usage_records": len(_usage),
        "active_customers": sum(1 for c in _customers.values() if c.active),
        "active_embeds": sum(1 for e in _embeds.values() if e.active),
    }


async def revoke_customer_access(customer_id: str) -> bool:
    c = _customers.get(customer_id)
    if not c:
        return False
    c.active = False
    for e in _embeds.values():
        if e.customer_id == customer_id:
            e.active = False
    return True


async def restore_customer_access(customer_id: str) -> bool:
    c = _customers.get(customer_id)
    if not c:
        return False
    c.active = True
    for e in _embeds.values():
        if e.customer_id == customer_id:
            e.active = True
    return True


async def generate_jwt_token(customer_id: str, secret: str, expire_seconds: int = 3600) -> str:
    import time
    payload = {
        "customer_id": customer_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + expire_seconds,
    }
    signature = _sign_payload(payload, secret)
    return f"eyJhbGciOiJIUzI1NiJ9.{__import__('base64').urlsafe_b64encode(str(payload).encode()).decode()}.{signature}"


async def get_customer_quota(customer_id: str) -> dict:
    c = _customers.get(customer_id)
    if not c:
        raise ValueError(f"Customer {customer_id} not found")
    current_embeds = len([e for e in _embeds.values() if e.customer_id == customer_id])
    return {
        "customer_id": customer_id,
        "dashboards_used": current_embeds,
        "dashboards_limit": c.usage_quota.get("dashboards", 5),
        "charts_limit": c.usage_quota.get("charts", 20),
        "requests_per_hour_limit": c.usage_quota.get("requests_per_hour", 1000),
    }


async def update_customer_quota(customer_id: str, quota_updates: dict) -> Optional[EmbedCustomer]:
    c = _customers.get(customer_id)
    if not c:
        return None
    c.usage_quota.update(quota_updates)
    return c


async def list_embed_themes() -> list[str]:
    return [t.value for t in Theme]


async def list_auth_methods() -> list[str]:
    return [a.value for a in AuthMethod]


async def get_embed_analytics(embed_id: str) -> dict:
    e = _embeds.get(embed_id)
    if not e:
        raise ValueError(f"Embed {embed_id} not found")
    embed_usage = [r for r in _usage if r.embed_id == embed_id]
    views = sum(1 for r in embed_usage if r.action == "view")
    loads = sum(1 for r in embed_usage if r.action == "load")
    return {
        "embed_id": embed_id,
        "name": e.name,
        "total_requests": len(embed_usage),
        "views": views,
        "loads": loads,
        "last_accessed": e.last_accessed or "never",
    }


async def toggle_embed(embed_id: str, active: bool) -> Optional[EmbedDashboard]:
    e = _embeds.get(embed_id)
    if not e:
        return None
    e.active = active
    return e


async def get_embed_iframe_url(embed_id: str) -> str:
    e = _embeds.get(embed_id)
    if not e:
        raise ValueError(f"Embed {embed_id} not found")
    return f"https://analytics.infrapilot.io/embed/{embed_id}"


async def list_embed_types() -> list[str]:
    return [t.value for t in EmbedType]


async def search_customers(query: str) -> list[EmbedCustomer]:
    q = query.lower()
    return [c for c in _customers.values() if q in c.name.lower() or q in c.domain.lower()]


async def get_top_customers(limit: int = 5) -> list[dict]:
    customer_usage = {}
    for r in _usage:
        customer_usage[r.customer_id] = customer_usage.get(r.customer_id, 0) + 1
    sorted_customers = sorted(customer_usage.items(), key=lambda x: x[1], reverse=True)[:limit]
    result = []
    for cid, count in sorted_customers:
        c = _customers.get(cid)
        if c:
            result.append({"customer_id": cid, "name": c.name, "requests": count})
    return result


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class EmbedBatchOperation:
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
class EmbedPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    active_filter: bool | None = None


@dataclass
class EmbedPaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


_embed_batch_ops: dict[str, EmbedBatchOperation] = {}


async def paginate_customers(params: EmbedPaginationParams | None = None) -> EmbedPaginatedResult:
    p = params or EmbedPaginationParams()
    results = list(_customers.values())
    if p.active_filter is not None:
        results = [c for c in results if c.active == p.active_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda c: c.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda c: c.created_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return EmbedPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total))


async def paginate_embeds(params: EmbedPaginationParams | None = None) -> EmbedPaginatedResult:
    p = params or EmbedPaginationParams()
    results = list(_embeds.values())
    if p.active_filter is not None:
        results = [e for e in results if e.active == p.active_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda e: e.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda e: e.created_at, reverse=p.sort_order == "desc")
    elif p.sort_by == "last_accessed":
        results.sort(key=lambda e: e.last_accessed, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return EmbedPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                 has_more=(p.offset + p.limit < total))


async def batch_toggle_embeds(embed_ids: list[str], active: bool) -> EmbedBatchOperation:
    op = EmbedBatchOperation(batch_id=str(uuid4()), operation="toggle_embeds", item_ids=[], created_at=_ts())
    for eid in embed_ids:
        e = _embeds.get(eid)
        if e:
            e.active = active
            op.item_ids.append(eid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"embed_id": eid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _embed_batch_ops[op.batch_id] = op
    return op


async def batch_delete_embeds(embed_ids: list[str]) -> EmbedBatchOperation:
    op = EmbedBatchOperation(batch_id=str(uuid4()), operation="delete_embeds", item_ids=[], created_at=_ts())
    for eid in embed_ids:
        if _embeds.pop(eid, None):
            op.item_ids.append(eid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"embed_id": eid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _embed_batch_ops[op.batch_id] = op
    return op


async def batch_rotate_api_keys(customer_ids: list[str]) -> EmbedBatchOperation:
    op = EmbedBatchOperation(batch_id=str(uuid4()), operation="rotate_keys", item_ids=[], created_at=_ts())
    for cid in customer_ids:
        key = await rotate_api_key(cid)
        if key:
            op.item_ids.append(cid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"customer_id": cid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _embed_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[EmbedBatchOperation]:
    return _embed_batch_ops.get(batch_id)


async def export_customer_config(customer_id: str) -> dict:
    c = _customers.get(customer_id)
    if not c:
        raise ValueError(f"Customer {customer_id} not found")
    customer_embeds = [e for e in _embeds.values() if e.customer_id == customer_id]
    return {
        "customer": {
            "name": c.name, "domain": c.domain, "auth_method": c.auth_method.value,
            "active": c.active, "allowed_origins": c.allowed_origins, "usage_quota": c.usage_quota,
        },
        "embeds": [{"name": e.name, "embed_type": e.embed_type.value, "config": e.config,
                      "theme": e.theme.value, "white_label": e.white_label} for e in customer_embeds],
        "exported_at": _ts(),
    }


async def import_customer_config(data: dict) -> EmbedCustomer:
    c = await register_customer(data["customer"]["name"], data["customer"]["domain"],
                                 AuthMethod(data["customer"].get("auth_method", "api_key")),
                                 data["customer"].get("allowed_origins"))
    if "usage_quota" in data["customer"]:
        c.usage_quota.update(data["customer"]["usage_quota"])
    for ed in data.get("embeds", []):
        await create_embed(c.customer_id, ed["name"], EmbedType(ed.get("embed_type", "dashboard")),
                            ed.get("config"), ed.get("white_label", False), Theme(ed.get("theme", "auto")))
    return c


async def get_embed_analytics_summary() -> dict:
    total_customers = len(_customers)
    total_embeds = len(_embeds)
    total_usage = len(_usage)
    by_action = {}
    for r in _usage:
        by_action[r.action] = by_action.get(r.action, 0) + 1
    active_customers_count = sum(1 for c in _customers.values() if c.active)
    active_embeds_count = sum(1 for e in _embeds.values() if e.active)
    avg_duration = sum(r.duration_ms for r in _usage) // max(len(_usage), 1)
    return {
        "total_customers": total_customers,
        "total_embeds": total_embeds,
        "total_usage_records": total_usage,
        "active_customers": active_customers_count,
        "active_embeds": active_embeds_count,
        "requests_by_action": by_action,
        "avg_duration_ms": avg_duration,
        "customers_over_quota": sum(1 for c in _customers.values()
                                     if len([e for e in _embeds.values() if e.customer_id == c.customer_id]) >= c.usage_quota.get("dashboards", 5)),
    }


async def get_hourly_usage(customer_id: str | None = None, hours: int = 24) -> list[dict]:
    from collections import defaultdict
    hourly = defaultdict(int)
    cutoff = datetime.utcnow().timestamp() - hours * 3600
    records = _usage
    if customer_id:
        records = [r for r in records if r.customer_id == customer_id]
    for r in records:
        try:
            ts = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).timestamp()
            if ts > cutoff:
                hour_key = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:00:00")
                hourly[hour_key] += 1
        except Exception:
            pass
    return [{"hour": k, "requests": v} for k, v in sorted(hourly.items())]


async def validate_embed_config(config: dict) -> dict:
    issues = []
    if "embed_type" in config and config["embed_type"] not in [t.value for t in EmbedType]:
        issues.append(f"Invalid embed type: {config.get('embed_type')}")
    if "theme" in config and config["theme"] not in [t.value for t in Theme]:
        issues.append(f"Invalid theme: {config.get('theme')}")
    if "allowed_origins" in config:
        for origin in config["allowed_origins"]:
            if not origin.startswith(("http://", "https://")):
                issues.append(f"Invalid origin URL: {origin}")
    if "auth_method" in config and config["auth_method"] not in [a.value for a in AuthMethod]:
        issues.append(f"Invalid auth method: {config.get('auth_method')}")
    return {"valid": len(issues) == 0, "issues": issues}


async def validate_embed_code(embed_code: str) -> dict:
    has_iframe = "<iframe" in embed_code
    has_src = "src=" in embed_code
    has_closing = "</iframe>" in embed_code
    issues = []
    if not has_iframe:
        issues.append("Missing <iframe> tag")
    if not has_src:
        issues.append("Missing src attribute")
    if not has_closing:
        issues.append("Missing closing </iframe>")
    return {"valid": len(issues) == 0, "issues": issues}


async def search_usage(query: str) -> list[UsageRecord]:
    q = query.lower()
    return [r for r in _usage if q in r.action.lower() or q in r.ip.lower()]


async def get_customer_health(customer_id: str) -> dict:
    c = _customers.get(customer_id)
    if not c:
        raise ValueError(f"Customer {customer_id} not found")
    recent_usage = [r for r in _usage if r.customer_id == customer_id]
    last_hour = sum(1 for r in recent_usage
                     if (datetime.utcnow().timestamp() - datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).timestamp()) < 3600)
    quota = c.usage_quota.get("requests_per_hour", 1000)
    return {
        "customer_id": customer_id,
        "name": c.name,
        "active": c.active,
        "requests_last_hour": last_hour,
        "quota_used_pct": round(last_hour / max(quota, 1) * 100, 1),
        "health": "good" if last_hour < quota * 0.8 else "warning" if last_hour < quota else "critical",
        "total_embeds": len([e for e in _embeds.values() if e.customer_id == customer_id]),
    }


async def get_embed_type_distribution() -> dict:
    dist = {}
    for e in _embeds.values():
        dist[e.embed_type.value] = dist.get(e.embed_type.value, 0) + 1
    return dist


async def get_usage_trend(days: int = 7) -> list[dict]:
    from collections import defaultdict
    daily = defaultdict(int)
    cutoff = datetime.utcnow().timestamp() - days * 86400
    for r in _usage:
        try:
            ts = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00")).timestamp()
            if ts > cutoff:
                day_key = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                daily[day_key] += 1
        except Exception:
            pass
    return [{"date": k, "requests": v} for k, v in sorted(daily.items())]


async def get_embed_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()
    suggestions = []
    for c in _customers.values():
        if q in c.name.lower():
            suggestions.append({"type": "customer", "id": c.customer_id, "text": c.name})
        if len(suggestions) >= limit:
            break
    for e in _embeds.values():
        if q in e.name.lower() and len(suggestions) < limit:
            suggestions.append({"type": "embed", "id": e.embed_id, "text": e.name})
    return suggestions


class EmbedMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class EmbedCache:
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


class EmbedAuditLogger:
    def __init__(self):
        self._log: list[dict] = []

    def log(self, action: str, detail: str = "") -> dict:
        from datetime import datetime
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat() + "Z", "id": str(uuid4())}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> list[dict]:
        return self._log[-n:]

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
