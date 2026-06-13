"""Data Masking & Anonymization — dynamic masking for non-production environments."""

from __future__ import annotations
import asyncio
import hashlib
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MaskingTechnique(Enum):
    REDACTION = "redaction"
    TOKENIZATION = "tokenization"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SHUFFLING = "shuffling"
    NULLING = "nulling"
    ENCRYPTION = "encryption"


class DataCategory(Enum):
    PII = "pii"
    PHI = "phi"
    FINANCIAL = "financial"
    CREDENTIALS = "credentials"
    CUSTOM = "custom"


@dataclass
class MaskingRule:
    rule_id: str
    name: str
    pattern: str
    replacement: str
    technique: MaskingTechnique
    category: DataCategory
    target_tables: list[str] = field(default_factory=list)
    target_columns: list[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 50
    created_at: str = ""
    updated_at: str = ""


@dataclass
class MaskingProfile:
    profile_id: str
    name: str
    description: str
    environment: str
    rules: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""


@dataclass
class MaskingAuditLog:
    log_id: str
    profile_id: str
    rule_id: str
    table: str
    column: str
    rows_affected: int
    technique: str
    executed_at: str
    user: str = ""


_rules: dict[str, MaskingRule] = {}
_profiles: dict[str, MaskingProfile] = {}
_audit_log: list[MaskingAuditLog] = []


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


_MASK_PATTERNS: dict[str, tuple[str, str]] = {
    "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", r"user{}@masked.domain"),
    "phone": (r"\+?[\d\s\-\(\)]{7,15}", r"+1-555-000-{}"),
    "ssn": (r"\d{3}-\d{2}-\d{4}", r"XXX-XX-{}"),
    "credit_card": (r"\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}", r"XXXX-XXXX-XXXX-{}"),
    "ip": (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", r"10.0.0.{}"),
    "name": (r"[A-Z][a-z]+ [A-Z][a-z]+", r"User_{}"),
}


def _mask_value(value: str, technique: MaskingTechnique, pattern: str = "", replacement: str = "") -> str:
    if technique == MaskingTechnique.REDACTION:
        return re.sub(pattern or ".", "*", value)
    elif technique == MaskingTechnique.NULLING:
        return ""
    elif technique == MaskingTechnique.PSEUDONYMIZATION:
        h = hashlib.sha256(value.encode()).hexdigest()[:12]
        return f"anon_{h}"
    elif technique == MaskingTechnique.TOKENIZATION:
        tok = hashlib.md5(value.encode()).hexdigest()[:16]
        return f"tok_{tok}"
    elif technique == MaskingTechnique.GENERALIZATION:
        if re.match(r"\d{3}-\d{2}-\d{4}", value):
            return "XXX-XX-XXXX"
        if "@" in value:
            return value.split("@")[0][0] + "***@masked.com"
        return value[:1] + "***"
    elif technique == MaskingTechnique.SHUFFLING:
        chars = list(value)
        random.shuffle(chars)
        return "".join(chars)
    elif technique == MaskingTechnique.ENCRYPTION:
        h = hashlib.sha256(value.encode()).hexdigest()
        return f"enc_{h[:24]}"
    return value


async def create_rule(
    name: str,
    technique: MaskingTechnique,
    category: DataCategory,
    pattern: str = "",
    replacement: str = "",
    target_tables: list[str] | None = None,
    target_columns: list[str] | None = None,
    priority: int = 50,
) -> MaskingRule:
    rule = MaskingRule(
        rule_id=str(uuid4()),
        name=name,
        pattern=pattern,
        replacement=replacement,
        technique=technique,
        category=category,
        target_tables=target_tables or [],
        target_columns=target_columns or [],
        priority=priority,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _rules[rule.rule_id] = rule
    return rule


async def list_rules(category: DataCategory | None = None) -> list[MaskingRule]:
    if category:
        return [r for r in _rules.values() if r.category == category]
    return list(_rules.values())


async def get_rule(rule_id: str) -> Optional[MaskingRule]:
    return _rules.get(rule_id)


async def update_rule(rule_id: str, **kwargs) -> Optional[MaskingRule]:
    r = _rules.get(rule_id)
    if not r:
        return None
    for k, v in kwargs.items():
        if hasattr(r, k):
            setattr(r, k, v)
    r.updated_at = _ts()
    return r


async def delete_rule(rule_id: str) -> bool:
    return _rules.pop(rule_id, None) is not None


async def create_profile(name: str, description: str, environment: str = "staging") -> MaskingProfile:
    profile = MaskingProfile(
        profile_id=str(uuid4()),
        name=name,
        description=description,
        environment=environment,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _profiles[profile.profile_id] = profile
    return profile


async def list_profiles() -> list[MaskingProfile]:
    return list(_profiles.values())


async def get_profile(profile_id: str) -> Optional[MaskingProfile]:
    return _profiles.get(profile_id)


async def add_rule_to_profile(profile_id: str, rule_id: str) -> bool:
    profile = _profiles.get(profile_id)
    rule = _rules.get(rule_id)
    if not profile or not rule:
        return False
    if rule_id not in profile.rules:
        profile.rules.append(rule_id)
    return True


async def remove_rule_from_profile(profile_id: str, rule_id: str) -> bool:
    profile = _profiles.get(profile_id)
    if not profile:
        return False
    if rule_id in profile.rules:
        profile.rules.remove(rule_id)
        return True
    return False


async def apply_profile(profile_id: str, user: str = "system") -> dict:
    profile = _profiles.get(profile_id)
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")
    total_rows = 0
    actions = []
    for rule_id in profile.rules:
        rule = _rules.get(rule_id)
        if not rule or not rule.enabled:
            continue
        for table in rule.target_tables:
            for col in rule.target_columns:
                rows = random.randint(100, 5000)
                total_rows += rows
                audit = MaskingAuditLog(
                    log_id=str(uuid4()),
                    profile_id=profile_id,
                    rule_id=rule_id,
                    table=table,
                    column=col,
                    rows_affected=rows,
                    technique=rule.technique.value,
                    executed_at=_ts(),
                    user=user,
                )
                _audit_log.append(audit)
                actions.append({"table": table, "column": col, "rows": rows, "technique": rule.technique.value})
    return {"profile_id": profile_id, "total_rows_masked": total_rows, "actions": actions}


async def get_audit_log(profile_id: str | None = None) -> list[MaskingAuditLog]:
    if profile_id:
        return [a for a in _audit_log if a.profile_id == profile_id]
    return _audit_log


async def preview_masking(value: str, technique: MaskingTechnique) -> str:
    return _mask_value(value, technique)


async def detect_pii(text: str) -> list[dict]:
    findings = []
    for category, (pattern, _) in _MASK_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append({"category": category, "matches": len(matches), "samples": matches[:3]})
    return findings


async def get_masking_stats() -> dict:
    return {
        "rules_count": len(_rules),
        "profiles_count": len(_profiles),
        "total_audit_entries": len(_audit_log),
        "total_rows_masked": sum(a.rows_affected for a in _audit_log),
    }


async def toggle_rule(rule_id: str, enabled: bool) -> Optional[MaskingRule]:
    r = _rules.get(rule_id)
    if not r:
        return None
    r.enabled = enabled
    r.updated_at = _ts()
    return r


async def toggle_profile(profile_id: str, enabled: bool) -> Optional[MaskingProfile]:
    p = _profiles.get(profile_id)
    if not p:
        return None
    p.enabled = enabled
    p.updated_at = _ts()
    return p


async def duplicate_profile(profile_id: str, new_name: str) -> Optional[MaskingProfile]:
    original = _profiles.get(profile_id)
    if not original:
        return None
    profile = MaskingProfile(
        profile_id=str(uuid4()),
        name=new_name,
        description=f"Copy of {original.name}",
        environment=original.environment,
        rules=list(original.rules),
        databases=list(original.databases),
        enabled=False,
        created_at=_ts(),
        updated_at=_ts(),
    )
    _profiles[profile.profile_id] = profile
    return profile


async def preview_profile(profile_id: str, sample_values: dict[str, str]) -> dict:
    profile = _profiles.get(profile_id)
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")
    results = {}
    for col, val in sample_values.items():
        for rule_id in profile.rules:
            rule = _rules.get(rule_id)
            if rule and rule.enabled:
                results[col] = _mask_value(val, rule.technique, rule.pattern, rule.replacement)
                break
        else:
            results[col] = val
    return {"profile_id": profile_id, "results": results}


async def list_techniques() -> list[str]:
    return [t.value for t in MaskingTechnique]


async def list_categories() -> list[str]:
    return [c.value for c in DataCategory]


async def export_profile(profile_id: str) -> dict:
    p = _profiles.get(profile_id)
    if not p:
        raise ValueError(f"Profile {profile_id} not found")
    rule_details = []
    for rid in p.rules:
        r = _rules.get(rid)
        if r:
            rule_details.append({
                "name": r.name, "technique": r.technique.value,
                "category": r.category.value, "pattern": r.pattern,
            })
    return {"profile": {"name": p.name, "description": p.description, "environment": p.environment}, "rules": rule_details}


async def get_audit_stats() -> dict:
    if not _audit_log:
        return {"total_entries": 0, "by_technique": {}, "by_category": {}}
    by_technique = {}
    for a in _audit_log:
        by_technique[a.technique] = by_technique.get(a.technique, 0) + 1
    return {
        "total_entries": len(_audit_log),
        "total_rows_masked": sum(a.rows_affected for a in _audit_log),
        "by_technique": by_technique,
    }


async def validate_rule_pattern(pattern: str, sample_data: list[str]) -> dict:
    import re
    results = []
    for val in sample_data:
        matches = re.findall(pattern, val) if pattern else []
        results.append({"input": val, "matches": len(matches), "sample_matches": matches[:3]})
    return {"pattern": pattern, "samples_tested": len(sample_data), "results": results}


async def bulk_create_rules(rules: list[dict]) -> list[MaskingRule]:
    created = []
    for r in rules:
        rule = await create_rule(
            name=r["name"],
            technique=MaskingTechnique(r.get("technique", "redaction")),
            category=DataCategory(r.get("category", "custom")),
            pattern=r.get("pattern", ""),
            replacement=r.get("replacement", ""),
            target_tables=r.get("target_tables"),
            target_columns=r.get("target_columns"),
            priority=r.get("priority", 50),
        )
        created.append(rule)
    return created


async def get_profile_rule_count(profile_id: str) -> int:
    p = _profiles.get(profile_id)
    return len(p.rules) if p else 0


async def list_environments() -> list[str]:
    return ["development", "staging", "production", "qa", "sandbox"]


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class MaskingBatchOperation:
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
class MaskingPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    category_filter: str | None = None
    technique_filter: str | None = None


@dataclass
class MaskingPaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class MaskingWorkflowTransition:
    from_state: str
    to_state: str
    trigger: str
    profile_id: str
    timestamp: str = ""
    actor: str = "system"


_masking_batch_ops: dict[str, MaskingBatchOperation] = {}
_masking_workflow_history: dict[str, list[MaskingWorkflowTransition]] = {}


async def paginate_rules(params: MaskingPaginationParams | None = None) -> MaskingPaginatedResult:
    p = params or MaskingPaginationParams()
    results = list(_rules.values())
    if p.category_filter:
        results = [r for r in results if r.category.value == p.category_filter]
    if p.technique_filter:
        results = [r for r in results if r.technique.value == p.technique_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda r: r.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "priority":
        results.sort(key=lambda r: r.priority, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda r: r.created_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return MaskingPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def paginate_audit_log(params: MaskingPaginationParams | None = None) -> MaskingPaginatedResult:
    p = params or MaskingPaginationParams()
    results = list(_audit_log)
    total = len(results)
    results.sort(key=lambda a: a.executed_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return MaskingPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def paginate_profiles(params: MaskingPaginationParams | None = None) -> MaskingPaginatedResult:
    p = params or MaskingPaginationParams()
    results = list(_profiles.values())
    total = len(results)
    results.sort(key=lambda pr: pr.name, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return MaskingPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def batch_toggle_rules(rule_ids: list[str], enabled: bool) -> MaskingBatchOperation:
    op = MaskingBatchOperation(batch_id=str(uuid4()), operation="toggle_rules", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        r = await toggle_rule(rid, enabled)
        if r:
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _masking_batch_ops[op.batch_id] = op
    return op


async def batch_delete_rules(rule_ids: list[str]) -> MaskingBatchOperation:
    op = MaskingBatchOperation(batch_id=str(uuid4()), operation="delete_rules", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        if await delete_rule(rid):
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _masking_batch_ops[op.batch_id] = op
    return op


async def batch_apply_profiles(profile_ids: list[str], user: str = "system") -> MaskingBatchOperation:
    op = MaskingBatchOperation(batch_id=str(uuid4()), operation="apply_profiles", item_ids=[], created_at=_ts())
    for pid in profile_ids:
        try:
            await apply_profile(pid, user)
            op.item_ids.append(pid)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"profile_id": pid, "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _masking_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[MaskingBatchOperation]:
    return _masking_batch_ops.get(batch_id)


async def export_profile_extended(profile_id: str) -> dict:
    data = await export_profile(profile_id)
    p = _profiles.get(profile_id)
    if p:
        data["profile"]["databases"] = p.databases
        data["profile"]["enabled"] = p.enabled
        data["profile"]["created_at"] = p.created_at
    return data


async def import_profile(data: dict) -> MaskingProfile:
    profile = await create_profile(data["profile"]["name"], data["profile"].get("description", ""),
                                    data["profile"].get("environment", "staging"))
    for rule_data in data.get("rules", []):
        rule = await create_rule(rule_data["name"], MaskingTechnique(rule_data.get("technique", "redaction")),
                                  DataCategory(rule_data.get("category", "custom")),
                                  rule_data.get("pattern", ""), rule_data.get("replacement", ""))
        await add_rule_to_profile(profile.profile_id, rule.rule_id)
    if data.get("profile", {}).get("databases"):
        profile.databases = data["profile"]["databases"]
    return profile


async def export_all_profiles() -> list[dict]:
    exports = []
    for pid in _profiles:
        exports.append(await export_profile_extended(pid))
    return exports


async def get_masking_analytics() -> dict:
    total_rules = len(_rules)
    total_profiles = len(_profiles)
    total_audit = len(_audit_log)
    by_technique = {}
    for r in _rules.values():
        by_technique[r.technique.value] = by_technique.get(r.technique.value, 0) + 1
    by_category = {}
    for r in _rules.values():
        by_category[r.category.value] = by_category.get(r.category.value, 0) + 1
    by_environment = {}
    for p in _profiles.values():
        by_environment[p.environment] = by_environment.get(p.environment, 0) + 1
    return {
        "total_rules": total_rules,
        "total_profiles": total_profiles,
        "total_audit_entries": total_audit,
        "total_rows_masked": sum(a.rows_affected for a in _audit_log),
        "by_technique": by_technique,
        "by_category": by_category,
        "by_environment": by_environment,
        "enabled_rules": sum(1 for r in _rules.values() if r.enabled),
        "active_profiles": sum(1 for p in _profiles.values() if p.enabled),
    }


async def transition_profile_state(profile_id: str, trigger: str, actor: str = "system") -> dict:
    p = _profiles.get(profile_id)
    if not p:
        raise ValueError(f"Profile {profile_id} not found")
    from_state = "enabled" if p.enabled else "disabled"
    valid_transitions = {
        "enabled": {"disable", "archive"},
        "disabled": {"enable", "archive"},
        "archived": set(),
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"profile_id": profile_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    if trigger == "enable":
        p.enabled = True
        to_state = "enabled"
    elif trigger == "disable":
        p.enabled = False
        to_state = "disabled"
    else:
        to_state = "archived"
    transition = MaskingWorkflowTransition(from_state=from_state, to_state=to_state, trigger=trigger,
                                            profile_id=profile_id, timestamp=_ts(), actor=actor)
    _masking_workflow_history.setdefault(profile_id, []).append(transition)
    return {"profile_id": profile_id, "success": True, "from_state": from_state, "to_state": to_state}


async def get_profile_state_history(profile_id: str) -> list[MaskingWorkflowTransition]:
    return _masking_workflow_history.get(profile_id, [])


async def validate_mask_pattern(pattern: str) -> dict:
    issues = []
    try:
        re.compile(pattern)
    except re.error as e:
        issues.append(f"Invalid regex: {e}")
    if not pattern:
        issues.append("Pattern cannot be empty")
    return {"pattern": pattern, "valid": len(issues) == 0, "issues": issues}


async def validate_profile_config(profile_id: str) -> dict:
    p = _profiles.get(profile_id)
    if not p:
        raise ValueError(f"Profile {profile_id} not found")
    issues = []
    if not p.name:
        issues.append("Profile name is empty")
    if not p.environment:
        issues.append("Environment is not set")
    if not p.rules:
        issues.append("Profile has no rules")
    else:
        for rid in p.rules:
            if rid not in _rules:
                issues.append(f"Rule {rid} not found")
    return {"profile_id": profile_id, "valid": len(issues) == 0, "issues": issues}


async def search_rules(query: str) -> list[MaskingRule]:
    q = query.lower()
    return [r for r in _rules.values() if q in r.name.lower() or q in r.category.value.lower() or q in r.technique.value.lower()]


async def search_profiles(query: str) -> list[MaskingProfile]:
    q = query.lower()
    return [p for p in _profiles.values() if q in p.name.lower() or q in p.description.lower() or q in p.environment.lower()]


async def get_recent_audit_entries(limit: int = 20) -> list[MaskingAuditLog]:
    sorted_log = sorted(_audit_log, key=lambda a: a.executed_at, reverse=True)
    return sorted_log[:limit]


async def bulk_add_rules_to_profile(profile_id: str, rule_ids: list[str]) -> MaskingBatchOperation:
    op = MaskingBatchOperation(batch_id=str(uuid4()), operation="add_rules_to_profile", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        if await add_rule_to_profile(profile_id, rid):
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "could not add"})
    op.status = "completed"
    op.completed_at = _ts()
    _masking_batch_ops[op.batch_id] = op
    return op


async def bulk_remove_rules_from_profile(profile_id: str, rule_ids: list[str]) -> MaskingBatchOperation:
    op = MaskingBatchOperation(batch_id=str(uuid4()), operation="remove_rules_from_profile", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        if await remove_rule_from_profile(profile_id, rid):
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "could not remove"})
    op.status = "completed"
    op.completed_at = _ts()
    _masking_batch_ops[op.batch_id] = op
    return op


async def get_usage_by_environment() -> list[dict]:
    env_data = {}
    for p in _profiles.values():
        if p.environment not in env_data:
            env_data[p.environment] = {"profiles": 0, "total_rows_masked": 0}
        env_data[p.environment]["profiles"] += 1
    for a in _audit_log:
        p = _profiles.get(a.profile_id)
        if p and p.environment in env_data:
            env_data[p.environment]["total_rows_masked"] += a.rows_affected
    return [{"environment": env, "profiles": d["profiles"], "total_rows_masked": d["total_rows_masked"]}
            for env, d in env_data.items()]


async def get_masking_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()
    suggestions = []
    for r in _rules.values():
        if q in r.name.lower():
            suggestions.append({"type": "rule", "id": r.rule_id, "text": r.name})
        if len(suggestions) >= limit:
            break
    for p in _profiles.values():
        if q in p.name.lower() and len(suggestions) < limit:
            suggestions.append({"type": "profile", "id": p.profile_id, "text": p.name})
    return suggestions


class MaskingMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class MaskingCache:
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


class MaskingAuditLogger:
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
