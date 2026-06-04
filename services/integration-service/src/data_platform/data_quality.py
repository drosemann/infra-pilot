"""Data Quality Framework — define rules, automated monitoring, scorecards."""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class RuleType(Enum):
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    CUSTOM = "custom"


class RuleSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ViolationStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class QualityRule:
    rule_id: str
    name: str
    rule_type: RuleType
    target_table: str
    target_column: str = ""
    severity: RuleSeverity = RuleSeverity.MEDIUM
    threshold: float = 0.0
    expression: str = ""
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    owner: str = ""


@dataclass
class QualityCheckResult:
    check_id: str
    rule_id: str
    status: str
    actual_value: float
    passed: bool
    checked_at: str = ""


@dataclass
class Violation:
    violation_id: str
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    status: ViolationStatus
    message: str
    actual_value: float
    threshold: float
    detected_at: str
    acknowledged_by: str = ""
    resolved_at: str = ""


@dataclass
class DatasetScorecard:
    scorecard_id: str
    dataset_name: str
    overall_score: float
    rule_count: int
    passing_rules: int
    failing_rules: int
    last_checked: str = ""
    dimension_scores: dict = field(default_factory=dict)


_rules: dict[str, QualityRule] = {}
_results: dict[str, list[QualityCheckResult]] = {}
_violations: dict[str, Violation] = {}
_scorecards: dict[str, DatasetScorecard] = {}


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def create_rule(
    name: str,
    rule_type: RuleType,
    target_table: str,
    target_column: str = "",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    threshold: float = 0.0,
    expression: str = "",
    owner: str = "",
) -> QualityRule:
    rule = QualityRule(
        rule_id=str(uuid4()),
        name=name,
        rule_type=rule_type,
        target_table=target_table,
        target_column=target_column,
        severity=severity,
        threshold=threshold,
        expression=expression,
        created_at=_ts(),
        updated_at=_ts(),
        owner=owner,
    )
    _rules[rule.rule_id] = rule
    logger.info("Quality rule created: %s (%s)", rule.rule_id, rule_type.value)
    return rule


async def list_rules(target_table: str | None = None) -> list[QualityRule]:
    if target_table:
        return [r for r in _rules.values() if r.target_table == target_table]
    return list(_rules.values())


async def get_rule(rule_id: str) -> Optional[QualityRule]:
    return _rules.get(rule_id)


async def update_rule(rule_id: str, **kwargs) -> Optional[QualityRule]:
    rule = _rules.get(rule_id)
    if not rule:
        return None
    for k, v in kwargs.items():
        if hasattr(rule, k):
            setattr(rule, k, v)
    rule.updated_at = _ts()
    return rule


async def delete_rule(rule_id: str) -> bool:
    rule = _rules.pop(rule_id, None)
    if rule:
        _violations = {k: v for k, v in _violations.items() if v.rule_id != rule_id}
        return True
    return False


async def run_check(rule_id: str) -> QualityCheckResult:
    rule = _rules.get(rule_id)
    if not rule:
        raise ValueError(f"Rule {rule_id} not found")
    await asyncio.sleep(0.2)
    import random
    passed = random.random() > 0.2
    actual = rule.threshold * (0.8 + 0.4 * random.random())
    if passed and rule.rule_type == RuleType.COMPLETENESS:
        actual = min(actual, 100.0)
    elif not passed:
        actual = max(0, rule.threshold - random.uniform(5, 20))
    result = QualityCheckResult(
        check_id=str(uuid4()),
        rule_id=rule_id,
        status="passed" if passed else "failed",
        actual_value=round(actual, 2),
        passed=passed,
        checked_at=_ts(),
    )
    _results.setdefault(rule_id, []).append(result)
    if not passed:
        violation = Violation(
            violation_id=str(uuid4()),
            rule_id=rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=ViolationStatus.OPEN,
            message=f"{rule.name}: expected >= {rule.threshold}, got {round(actual, 2)}",
            actual_value=round(actual, 2),
            threshold=rule.threshold,
            detected_at=_ts(),
        )
        _violations[violation.violation_id] = violation
    return result


async def run_all_checks() -> dict:
    results = []
    for rule_id in _rules:
        result = await run_check(rule_id)
        results.append({"rule_id": rule_id, "passed": result.passed})
    return {"total": len(results), "passed": sum(1 for r in results if r["passed"]), "failed": sum(1 for r in results if not r["passed"])}


async def list_violations(status: ViolationStatus | None = None) -> list[Violation]:
    if status:
        return [v for v in _violations.values() if v.status == status]
    return list(_violations.values())


async def acknowledge_violation(violation_id: str, user: str = "system") -> Optional[Violation]:
    v = _violations.get(violation_id)
    if not v:
        return None
    v.status = ViolationStatus.ACKNOWLEDGED
    v.acknowledged_by = user
    return v


async def resolve_violation(violation_id: str) -> Optional[Violation]:
    v = _violations.get(violation_id)
    if not v:
        return None
    v.status = ViolationStatus.RESOLVED
    v.resolved_at = _ts()
    return v


async def get_scorecard(dataset_name: str) -> Optional[DatasetScorecard]:
    return _scorecards.get(dataset_name)


async def compute_scorecard(dataset_name: str) -> DatasetScorecard:
    rules = [r for r in _rules.values() if r.target_table == dataset_name]
    if not rules:
        sc = DatasetScorecard(
            scorecard_id=str(uuid4()),
            dataset_name=dataset_name,
            overall_score=100.0,
            rule_count=0,
            passing_rules=0,
            failing_rules=0,
            last_checked=_ts(),
        )
        _scorecards[dataset_name] = sc
        return sc
    passing = 0
    failing = 0
    for r in rules:
        res_list = _results.get(r.rule_id, [])
        recent = res_list[-1] if res_list else None
        if recent and recent.passed:
            passing += 1
        else:
            failing += 1
    total = passing + failing
    score = (passing / total * 100) if total > 0 else 100
    sc = DatasetScorecard(
        scorecard_id=str(uuid4()),
        dataset_name=dataset_name,
        overall_score=round(score, 1),
        rule_count=total,
        passing_rules=passing,
        failing_rules=failing,
        last_checked=_ts(),
        dimension_scores={
            "freshness": round(score * (0.8 + 0.4 * (passing / max(total, 1))), 1),
            "completeness": round(score * (0.7 + 0.3 * (passing / max(total, 1))), 1),
            "uniqueness": round(score * (0.9 + 0.1 * (passing / max(total, 1))), 1),
        },
    )
    _scorecards[dataset_name] = sc
    return sc


async def get_violation_stats() -> dict:
    total = len(_violations)
    open_count = sum(1 for v in _violations.values() if v.status == ViolationStatus.OPEN)
    acknowledged = sum(1 for v in _violations.values() if v.status == ViolationStatus.ACKNOWLEDGED)
    resolved = sum(1 for v in _violations.values() if v.status == ViolationStatus.RESOLVED)
    return {"total": total, "open": open_count, "acknowledged": acknowledged, "resolved": resolved}


async def get_rule_history(rule_id: str) -> list[QualityCheckResult]:
    return _results.get(rule_id, [])


async def suppress_violation(violation_id: str, reason: str = "") -> Optional[Violation]:
    v = _violations.get(violation_id)
    if not v:
        return None
    v.status = ViolationStatus.SUPPRESSED
    return v


async def bulk_run_checks(target_table: str | None = None) -> dict:
    rules = list(_rules.values())
    if target_table:
        rules = [r for r in rules if r.target_table == target_table]
    results = []
    for rule in rules:
        result = await run_check(rule.rule_id)
        results.append({"rule_id": rule.rule_id, "name": rule.name, "passed": result.passed})
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    return {"total": len(results), "passed": passed, "failed": failed, "details": results}


async def list_scorecards() -> list[DatasetScorecard]:
    return list(_scorecards.values())


async def delete_scorecard(dataset_name: str) -> bool:
    return _scorecards.pop(dataset_name, None) is not None


async def get_quality_summary() -> dict:
    total_rules = len(_rules)
    if total_rules == 0:
        return {"total_rules": 0, "pass_rate": 100.0, "open_violations": 0}
    all_results = []
    for rule_results in _results.values():
        recent = rule_results[-1] if rule_results else None
        if recent:
            all_results.append(recent)
    passed = sum(1 for r in all_results if r.passed)
    pass_rate = round((passed / max(len(all_results), 1)) * 100, 1)
    open_violations = sum(1 for v in _violations.values() if v.status == ViolationStatus.OPEN)
    return {
        "total_rules": total_rules,
        "pass_rate": pass_rate,
        "checked_rules": len(all_results),
        "open_violations": open_violations,
        "scorecards": len(_scorecards),
    }


async def update_scorecard(dataset_name: str, dimension_scores: dict) -> Optional[DatasetScorecard]:
    sc = _scorecards.get(dataset_name)
    if not sc:
        return None
    sc.dimension_scores.update(dimension_scores)
    sc.overall_score = round(sum(sc.dimension_scores.values()) / max(len(sc.dimension_scores), 1), 1)
    return sc


async def list_rule_types() -> list[str]:
    return [r.value for r in RuleType]


async def list_severities() -> list[str]:
    return [s.value for s in RuleSeverity]


async def get_rule_results(rule_id: str, limit: int = 20) -> list[QualityCheckResult]:
    return _results.get(rule_id, [])[-limit:]


async def get_dataset_scorecards(dataset_name: str | None = None) -> list[DatasetScorecard]:
    if dataset_name:
        sc = _scorecards.get(dataset_name)
        return [sc] if sc else []
    return list(_scorecards.values())


async def get_open_violations_count() -> int:
    return sum(1 for v in _violations.values() if v.status == ViolationStatus.OPEN)


async def recheck_violation(violation_id: str) -> Optional[QualityCheckResult]:
    v = _violations.get(violation_id)
    if not v:
        return None
    result = await run_check(v.rule_id)
    if result.passed:
        v.status = ViolationStatus.RESOLVED
        v.resolved_at = _ts()
    return result


async def get_alert_thresholds() -> dict:
    return {
        "critical_violation_threshold": 5,
        "scorecard_degradation_threshold": 20.0,
        "consecutive_failures_threshold": 3,
    }


# ===== APPENDED: Batch ops, pagination, state machine, analytics, export/import =====

@dataclass
class QualityBatchOperation:
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
class QualityPaginationParams:
    offset: int = 0
    limit: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
    rule_type_filter: str | None = None
    severity_filter: str | None = None
    status_filter: str | None = None


@dataclass
class QualityPaginatedResult:
    items: list
    total: int
    offset: int
    limit: int
    has_more: bool


@dataclass
class QualityWorkflowTransition:
    from_state: str
    to_state: str
    trigger: str
    violation_id: str
    timestamp: str = ""
    actor: str = "system"


_quality_batch_ops: dict[str, QualityBatchOperation] = {}
_violation_workflow_history: dict[str, list[QualityWorkflowTransition]] = {}


async def paginate_rules(params: QualityPaginationParams | None = None) -> QualityPaginatedResult:
    p = params or QualityPaginationParams()
    results = list(_rules.values())
    if p.rule_type_filter:
        results = [r for r in results if r.rule_type.value == p.rule_type_filter]
    if p.severity_filter:
        results = [r for r in results if r.severity.value == p.severity_filter]
    total = len(results)
    if p.sort_by == "name":
        results.sort(key=lambda r: r.name, reverse=p.sort_order == "desc")
    elif p.sort_by == "severity":
        results.sort(key=lambda r: r.severity.value, reverse=p.sort_order == "desc")
    elif p.sort_by == "created_at":
        results.sort(key=lambda r: r.created_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return QualityPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def paginate_violations(params: QualityPaginationParams | None = None) -> QualityPaginatedResult:
    p = params or QualityPaginationParams()
    results = list(_violations.values())
    if p.status_filter:
        results = [v for v in results if v.status.value == p.status_filter]
    if p.severity_filter:
        results = [v for v in results if v.severity.value == p.severity_filter]
    total = len(results)
    if p.sort_by == "severity":
        results.sort(key=lambda v: v.severity.value, reverse=p.sort_order == "desc")
    elif p.sort_by == "detected_at":
        results.sort(key=lambda v: v.detected_at, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return QualityPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def paginate_scorecards(params: QualityPaginationParams | None = None) -> QualityPaginatedResult:
    p = params or QualityPaginationParams()
    results = list(_scorecards.values())
    total = len(results)
    if p.sort_by == "overall_score":
        results.sort(key=lambda s: s.overall_score, reverse=p.sort_order == "desc")
    elif p.sort_by == "last_checked":
        results.sort(key=lambda s: s.last_checked, reverse=p.sort_order == "desc")
    sliced = results[p.offset:p.offset + p.limit]
    return QualityPaginatedResult(items=sliced, total=total, offset=p.offset, limit=p.limit,
                                   has_more=(p.offset + p.limit < total))


async def batch_create_rules(rules: list[dict]) -> QualityBatchOperation:
    op = QualityBatchOperation(batch_id=str(uuid4()), operation="create_rules", item_ids=[], created_at=_ts())
    for rd in rules:
        try:
            rule = await create_rule(
                name=rd["name"],
                rule_type=RuleType(rd.get("rule_type", "custom")),
                target_table=rd.get("target_table", ""),
                target_column=rd.get("target_column", ""),
                severity=RuleSeverity(rd.get("severity", "medium")),
                threshold=rd.get("threshold", 0.0),
                expression=rd.get("expression", ""),
                owner=rd.get("owner", ""),
            )
            op.item_ids.append(rule.rule_id)
            op.success_count += 1
        except Exception as e:
            op.failure_count += 1
            op.errors.append({"name": rd.get("name"), "error": str(e)})
    op.status = "completed"
    op.completed_at = _ts()
    _quality_batch_ops[op.batch_id] = op
    return op


async def batch_delete_rules(rule_ids: list[str]) -> QualityBatchOperation:
    op = QualityBatchOperation(batch_id=str(uuid4()), operation="delete_rules", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        if await delete_rule(rid):
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _quality_batch_ops[op.batch_id] = op
    return op


async def batch_acknowledge_violations(violation_ids: list[str], user: str = "system") -> QualityBatchOperation:
    op = QualityBatchOperation(batch_id=str(uuid4()), operation="acknowledge", item_ids=[], created_at=_ts())
    for vid in violation_ids:
        v = await acknowledge_violation(vid, user)
        if v:
            op.item_ids.append(vid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"violation_id": vid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _quality_batch_ops[op.batch_id] = op
    return op


async def batch_resolve_violations(violation_ids: list[str]) -> QualityBatchOperation:
    op = QualityBatchOperation(batch_id=str(uuid4()), operation="resolve", item_ids=[], created_at=_ts())
    for vid in violation_ids:
        v = await resolve_violation(vid)
        if v:
            op.item_ids.append(vid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"violation_id": vid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _quality_batch_ops[op.batch_id] = op
    return op


async def get_batch_operation(batch_id: str) -> Optional[QualityBatchOperation]:
    return _quality_batch_ops.get(batch_id)


async def export_quality_rules(target_table: str | None = None) -> list[dict]:
    rules = list(_rules.values())
    if target_table:
        rules = [r for r in rules if r.target_table == target_table]
    return [{"name": r.name, "rule_type": r.rule_type.value, "target_table": r.target_table,
              "target_column": r.target_column, "severity": r.severity.value, "threshold": r.threshold,
              "expression": r.expression, "enabled": r.enabled} for r in rules]


async def import_quality_rules(rules: list[dict]) -> dict:
    imported = 0
    skipped = 0
    for rd in rules:
        existing = [r for r in _rules.values() if r.name == rd.get("name") and r.target_table == rd.get("target_table")]
        if existing:
            skipped += 1
            continue
        try:
            await create_rule(rd["name"], RuleType(rd.get("rule_type", "custom")), rd.get("target_table", ""),
                               rd.get("target_column", ""), RuleSeverity(rd.get("severity", "medium")),
                               rd.get("threshold", 0.0), rd.get("expression", ""), rd.get("owner", ""))
            imported += 1
        except Exception:
            skipped += 1
    return {"imported": imported, "skipped": skipped}


async def get_quality_analytics() -> dict:
    total_rules = len(_rules)
    total_violations = len(_violations)
    total_scorecards = len(_scorecards)
    by_type = {}
    for r in _rules.values():
        by_type[r.rule_type.value] = by_type.get(r.rule_type.value, 0) + 1
    by_severity = {}
    for v in _violations.values():
        by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1
    by_status = {}
    for v in _violations.values():
        by_status[v.status.value] = by_status.get(v.status.value, 0) + 1
    all_results = []
    for rule_results in _results.values():
        recent = rule_results[-1] if rule_results else None
        if recent:
            all_results.append(recent)
    pass_rate = round(sum(1 for r in all_results if r.passed) / max(len(all_results), 1) * 100, 1)
    return {
        "total_rules": total_rules,
        "total_violations": total_violations,
        "total_scorecards": total_scorecards,
        "total_checks_run": len(all_results),
        "pass_rate": pass_rate,
        "by_rule_type": by_type,
        "by_severity": by_severity,
        "by_status": by_status,
        "avg_scorecard_score": round(sum(s.overall_score for s in _scorecards.values()) / max(total_scorecards, 1), 1),
    }


async def transition_violation_state(violation_id: str, trigger: str, actor: str = "system") -> dict:
    v = _violations.get(violation_id)
    if not v:
        raise ValueError(f"Violation {violation_id} not found")
    from_state = v.status.value
    valid_transitions = {
        "open": {"acknowledge", "suppress", "resolve"},
        "acknowledged": {"resolve", "reopen", "suppress"},
        "resolved": {"reopen"},
        "suppressed": {"reopen", "resolve"},
    }
    allowed = valid_transitions.get(from_state, set())
    if trigger not in allowed:
        return {"violation_id": violation_id, "success": False, "error": f"Cannot transition from {from_state} via {trigger}"}
    to_state_map = {
        "acknowledge": ViolationStatus.ACKNOWLEDGED,
        "resolve": ViolationStatus.RESOLVED,
        "suppress": ViolationStatus.SUPPRESSED,
        "reopen": ViolationStatus.OPEN,
    }
    new_status = to_state_map.get(trigger, v.status)
    v.status = new_status
    if trigger == "acknowledge":
        v.acknowledged_by = actor
    if trigger == "resolve":
        v.resolved_at = _ts()
    transition = QualityWorkflowTransition(from_state=from_state, to_state=new_status.value, trigger=trigger,
                                            violation_id=violation_id, timestamp=_ts(), actor=actor)
    _violation_workflow_history.setdefault(violation_id, []).append(transition)
    return {"violation_id": violation_id, "success": True, "from_state": from_state, "to_state": new_status.value}


async def get_violation_state_history(violation_id: str) -> list[QualityWorkflowTransition]:
    return _violation_workflow_history.get(violation_id, [])


async def validate_rule_config(rule_id: str) -> dict:
    r = _rules.get(rule_id)
    if not r:
        raise ValueError(f"Rule {rule_id} not found")
    issues = []
    if not r.name:
        issues.append("Rule name is empty")
    if not r.target_table:
        issues.append("Target table is not set")
    if r.rule_type == RuleType.FRESHNESS and not r.expression:
        issues.append("Freshness rule requires an expression")
    if r.threshold < 0:
        issues.append("Threshold cannot be negative")
    if r.rule_type == RuleType.COMPLETENESS and (r.threshold < 0 or r.threshold > 100):
        issues.append("Completeness threshold should be between 0 and 100")
    return {"rule_id": rule_id, "valid": len(issues) == 0, "issues": issues}


async def search_rules(query: str) -> list[QualityRule]:
    q = query.lower()
    return [r for r in _rules.values() if q in r.name.lower() or q in r.target_table.lower() or q in r.rule_type.value.lower()]


async def search_violations(query: str) -> list[Violation]:
    q = query.lower()
    return [v for v in _violations.values() if q in v.rule_name.lower() or q in v.message.lower()]


async def get_trend_data(rule_id: str, days: int = 7) -> dict:
    results = _results.get(rule_id, [])
    if not results:
        return {"rule_id": rule_id, "data_points": 0, "trend": "none"}
    recent = results[-min(len(results), days * 10):]
    pass_count = sum(1 for r in recent if r.passed)
    return {
        "rule_id": rule_id,
        "data_points": len(recent),
        "pass_rate": round(pass_count / max(len(recent), 1) * 100, 1),
        "trend": "improving" if pass_count > len(recent) * 0.8 else "degrading" if pass_count < len(recent) * 0.5 else "stable",
        "latest_value": recent[-1].actual_value if recent else 0,
    }


async def get_scorecard_trend(dataset_name: str) -> list[dict]:
    sc = _scorecards.get(dataset_name)
    if not sc:
        return []
    results = []
    for rule_id in [r.rule_id for r in _rules.values() if r.target_table == dataset_name]:
        rule_results = _results.get(rule_id, [])
        for res in rule_results[-10:]:
            results.append({"check_id": res.check_id, "passed": res.passed, "checked_at": res.checked_at, "actual_value": res.actual_value})
    return sorted(results, key=lambda x: x["checked_at"])[-50:]


async def bulk_enable_rules(rule_ids: list[str], enabled: bool) -> QualityBatchOperation:
    op = QualityBatchOperation(batch_id=str(uuid4()), operation="bulk_enable", item_ids=[], created_at=_ts())
    for rid in rule_ids:
        rule = _rules.get(rid)
        if rule:
            rule.enabled = enabled
            op.item_ids.append(rid)
            op.success_count += 1
        else:
            op.failure_count += 1
            op.errors.append({"rule_id": rid, "error": "not found"})
    op.status = "completed"
    op.completed_at = _ts()
    _quality_batch_ops[op.batch_id] = op
    return op


async def recompute_all_scorecards() -> dict:
    datasets = set(r.target_table for r in _rules.values())
    recomputed = 0
    for ds in datasets:
        await compute_scorecard(ds)
        recomputed += 1
    return {"datasets_recomputed": recomputed, "timestamp": _ts()}


async def get_quality_search_suggestions(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()
    suggestions = []
    for r in _rules.values():
        if q in r.name.lower():
            suggestions.append({"type": "rule", "id": r.rule_id, "text": r.name})
        if len(suggestions) >= limit:
            break
    for v in _violations.values():
        if q in v.message.lower() and len(suggestions) < limit:
            suggestions.append({"type": "violation", "id": v.violation_id, "text": v.message[:50]})
    return suggestions


class QualityMetricsCollector:
    def __init__(self):
        self._counts: dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class QualityCache:
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


class QualityAuditLogger:
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
