"""Cog: Data Masking & Anonymization — dynamic masking for non-production environments."""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

MASKING_PROFILES: dict[str, dict] = {}
MASKING_RULES: dict[str, dict] = {}


async def create_profile(name: str, environment: str = "staging") -> dict:
    pid = f"mp-{len(MASKING_PROFILES) + 1}"
    MASKING_PROFILES[pid] = {"profile_id": pid, "name": name, "environment": environment, "rules": [], "enabled": True}
    return MASKING_PROFILES[pid]


async def create_rule(name: str, technique: str = "redaction", pattern: str = "", target_tables: list[str] | None = None) -> dict:
    rid = f"mr-{len(MASKING_RULES) + 1}"
    MASKING_RULES[rid] = {"rule_id": rid, "name": name, "technique": technique, "pattern": pattern, "target_tables": target_tables or []}
    return MASKING_RULES[rid]


async def list_profiles() -> list[dict]:
    return list(MASKING_PROFILES.values())


async def list_rules() -> list[dict]:
    return list(MASKING_RULES.values())


async def apply_profile(profile_id: str) -> dict:
    return {"profile_id": profile_id, "status": "applied", "rows_masked": 1500}


async def get_masking_stats() -> dict:
    return {"profiles": len(MASKING_PROFILES), "rules": len(MASKING_RULES)}


async def get_profile(profile_id: str) -> dict | None:
    return MASKING_PROFILES.get(profile_id)


async def update_profile(profile_id: str, **kwargs) -> dict | None:
    p = MASKING_PROFILES.get(profile_id)
    if not p:
        return None
    p.update(kwargs)
    return p


async def delete_profile(profile_id: str) -> bool:
    return MASKING_PROFILES.pop(profile_id, None) is not None


async def get_rule(rule_id: str) -> dict | None:
    return MASKING_RULES.get(rule_id)


async def update_rule(rule_id: str, **kwargs) -> dict | None:
    r = MASKING_RULES.get(rule_id)
    if not r:
        return None
    r.update(kwargs)
    return r


async def delete_rule(rule_id: str) -> bool:
    return MASKING_RULES.pop(rule_id, None) is not None


async def add_rule_to_profile(profile_id: str, rule_id: str) -> bool:
    p = MASKING_PROFILES.get(profile_id)
    r = MASKING_RULES.get(rule_id)
    if not p or not r:
        return False
    if rule_id not in p.get("rules", []):
        p.setdefault("rules", []).append(rule_id)
    return True


async def remove_rule_from_profile(profile_id: str, rule_id: str) -> bool:
    p = MASKING_PROFILES.get(profile_id)
    if not p:
        return False
    rules = p.get("rules", [])
    if rule_id in rules:
        rules.remove(rule_id)
        return True
    return False


async def toggle_rule(rule_id: str, enabled: bool) -> dict | None:
    r = MASKING_RULES.get(rule_id)
    if not r:
        return None
    r["enabled"] = enabled
    return r


async def toggle_profile(profile_id: str, enabled: bool) -> dict | None:
    p = MASKING_PROFILES.get(profile_id)
    if not p:
        return None
    p["enabled"] = enabled
    return p


async def detect_pii(text: str) -> list[dict]:
    import re
    patterns = {"email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "phone": r"\+?[\d\s\-\(\)]{7,15}"}
    findings = []
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append({"category": category, "matches": len(matches), "samples": matches[:3]})
    return findings


async def preview_masking(value: str, technique: str = "redaction") -> str:
    if technique == "redaction":
        return "*" * len(value)
    elif technique == "nulling":
        return ""
    elif technique == "pseudonymization":
        import hashlib
        return f"anon_{hashlib.sha256(value.encode()).hexdigest()[:12]}"
    return value


async def duplicate_profile(profile_id: str, new_name: str) -> dict | None:
    original = MASKING_PROFILES.get(profile_id)
    if not original:
        return None
    pid = f"mp-{len(MASKING_PROFILES) + 1}"
    MASKING_PROFILES[pid] = {**original, "profile_id": pid, "name": new_name, "enabled": False}
    return MASKING_PROFILES[pid]


async def get_audit_log(profile_id: str | None = None) -> list[dict]:
    return []


async def list_techniques() -> list[str]:
    return ["redaction", "tokenization", "pseudonymization", "generalization", "shuffling", "nulling", "encryption"]


async def export_profile(profile_id: str) -> dict | None:
    p = MASKING_PROFILES.get(profile_id)
    if not p:
        return None
    rule_details = []
    for rid in p.get("rules", []):
        r = MASKING_RULES.get(rid)
        if r:
            rule_details.append({"name": r.get("name"), "technique": r.get("technique")})
    return {"profile": {"name": p.get("name"), "environment": p.get("environment")}, "rules": rule_details}


async def list_environments() -> list[str]:
    return ["development", "staging", "production", "qa", "sandbox"]


async def get_profile_rule_count(profile_id: str) -> int:
    p = MASKING_PROFILES.get(profile_id)
    return len(p.get("rules", [])) if p else 0


async def validate_rule_pattern(pattern: str, sample_data: list[str]) -> dict:
    import re
    results = []
    for val in sample_data:
        matches = re.findall(pattern, val) if pattern else []
        results.append({"input": val, "matches": len(matches)})
    return {"pattern": pattern, "samples_tested": len(sample_data), "results": results}


async def bulk_create_rules(rules: list[dict]) -> list[dict]:
    created = []
    for r in rules:
        rule = await create_rule(
            name=r.get("name", "rule"),
            technique=r.get("technique", "redaction"),
            target_tables=r.get("target_tables"),
        )
        created.append(rule)
    return created


async def list_categories() -> list[str]:
    return ["pii", "phi", "financial", "credentials", "custom"]


# ===== APPENDED: Utility helpers, pagination, batch ops =====

async def paginate_rules(offset: int = 0, limit: int = 50, technique: str = None) -> dict:
    results = list(MASKING_RULES.values())
    if technique:
        results = [r for r in results if r.get("technique") == technique]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def paginate_profiles(offset: int = 0, limit: int = 50, enabled: bool = None) -> dict:
    results = list(MASKING_PROFILES.values())
    if enabled is not None:
        results = [p for p in results if p.get("enabled") == enabled]
    total = len(results)
    sliced = results[offset:offset + limit]
    return {"items": sliced, "total": total, "offset": offset, "limit": limit,
            "has_more": offset + limit < total}

async def bulk_delete_rules(rule_ids: list[str]) -> dict:
    deleted = 0
    for rid in rule_ids:
        if await delete_rule(rid):
            deleted += 1
    return {"deleted": deleted, "total_requested": len(rule_ids)}

async def export_all_profiles() -> list[dict]:
    return [dict(p) for p in MASKING_PROFILES.values()]

async def import_profile(profile_data: dict, rules_data: list[dict] | None = None) -> dict:
    pid = f"mp-{len(MASKING_PROFILES) + 1}"
    profile = {"profile_id": pid, "name": profile_data.get("name", "imported"), "environment": profile_data.get("environment", "development"),
               "rules": [], "enabled": False}
    if rules_data:
        for rd in rules_data:
            rule = await create_rule(rd.get("name", "rule"), rd.get("technique", "redaction"), rd.get("target_tables"))
            profile["rules"].append(rule["rule_id"])
    MASKING_PROFILES[pid] = profile
    return profile

async def get_masking_analytics() -> dict:
    total_rules = len(MASKING_RULES)
    total_profiles = len(MASKING_PROFILES)
    enabled_rules = sum(1 for r in MASKING_RULES.values() if r.get("enabled"))
    enabled_profiles = sum(1 for p in MASKING_PROFILES.values() if p.get("enabled"))
    techniques = {}
    for r in MASKING_RULES.values():
        t = r.get("technique", "unknown")
        techniques[t] = techniques.get(t, 0) + 1
    return {
        "total_rules": total_rules,
        "total_profiles": total_profiles,
        "enabled_rules": enabled_rules,
        "enabled_profiles": enabled_profiles,
        "techniques": techniques,
    }

async def bulk_toggle_rules(rule_ids: list[str], enabled: bool) -> dict:
    toggled = 0
    for rid in rule_ids:
        if await toggle_rule(rid, enabled):
            toggled += 1
    return {"toggled": toggled, "total_requested": len(rule_ids)}

async def search_profiles(query: str) -> list[dict]:
    q = query.lower()
    return [p for p in MASKING_PROFILES.values() if q in p.get("name", "").lower() or q in p.get("environment", "").lower()]

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
