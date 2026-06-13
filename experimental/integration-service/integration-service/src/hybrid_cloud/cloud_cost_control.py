import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CostAnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BudgetPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class BudgetAction(Enum):
    WARN = "warn"
    ALERT = "alert"
    AUTO_SHUTDOWN = "auto_shutdown"
    BLOCK_PROVISIONING = "block_provisioning"


class CostRecord:
    def __init__(self, provider: str, service: str, region: str,
                 amount: float, currency: str = "USD",
                 tags: Optional[Dict[str, str]] = None):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.service = service
        self.region = region
        self.amount = amount
        self.currency = currency
        self.tags = tags or {}
        self.recorded_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "provider": self.provider, "service": self.service,
                "region": self.region, "amount": self.amount, "currency": self.currency,
                "tags": self.tags, "recorded_at": self.recorded_at.isoformat()}


class CostBudget:
    def __init__(self, name: str, amount: float, period: BudgetPeriod,
                 action: BudgetAction = BudgetAction.WARN,
                 scope: Optional[Dict[str, str]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.amount = amount
        self.period = period
        self.action = action
        self.scope = scope or {}
        self.spent = 0.0
        self.created_at = datetime.utcnow()
        self.last_reset_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "amount": self.amount,
                "period": self.period.value, "action": self.action.value,
                "scope": self.scope, "spent": self.spent,
                "created_at": self.created_at.isoformat(),
                "last_reset_at": self.last_reset_at.isoformat()}


class CostAnomaly:
    def __init__(self, provider: str, service: str, region: str,
                 amount: float, expected_amount: float, deviation: float,
                 severity: CostAnomalySeverity):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.service = service
        self.region = region
        self.amount = amount
        self.expected_amount = expected_amount
        self.deviation = deviation
        self.severity = severity
        self.detected_at = datetime.utcnow()
        self.resolved = False

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "provider": self.provider, "service": self.service,
                "region": self.region, "amount": self.amount,
                "expected_amount": self.expected_amount, "deviation": self.deviation,
                "severity": self.severity.value,
                "detected_at": self.detected_at.isoformat(), "resolved": self.resolved}


class UnifiedCloudCostControl:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_currency = config.get("default_currency", "USD")
        self.anomaly_threshold = config.get("anomaly_threshold", 1.5)
        self.auto_shutdown_enabled = config.get("auto_shutdown_enabled", False)
        self.aggregation_interval = config.get("aggregation_interval", "hourly")
        self.budget_enforcement_enabled = config.get("budget_enforcement_enabled", True)
        self._cost_records: List[CostRecord] = []
        self._budgets: Dict[str, CostBudget] = {}
        self._anomalies: Dict[str, CostAnomaly] = {}
        self._provider_totals: Dict[str, float] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("UnifiedCloudCostControl initialized")

    async def close(self) -> None:
        self._cost_records.clear()
        self._budgets.clear()
        self._anomalies.clear()
        logger.info("UnifiedCloudCostControl closed")

    def record_cost(self, provider: str, service: str, region: str,
                    amount: float, currency: str = "USD",
                    tags: Optional[Dict[str, str]] = None) -> CostRecord:
        rec = CostRecord(provider, service, region, amount, currency, tags)
        self._cost_records.append(rec)
        self._provider_totals[provider] = self._provider_totals.get(provider, 0) + amount
        detection = self._detect_anomaly(rec)
        self._check_budgets(rec)
        return rec

    def _detect_anomaly(self, rec: CostRecord) -> Optional[CostAnomaly]:
        recent = [r for r in self._cost_records[-50:]
                  if r.provider == rec.provider and r.service == rec.service]
        if len(recent) < 5:
            return None
        amounts = [r.amount for r in recent[:-1]]
        mean = sum(amounts) / len(amounts)
        if mean == 0:
            return None
        deviation = abs(rec.amount - mean) / mean
        if deviation >= self.anomaly_threshold:
            severity = CostAnomalySeverity.LOW
            if deviation >= 3.0:
                severity = CostAnomalySeverity.CRITICAL
            elif deviation >= 2.5:
                severity = CostAnomalySeverity.HIGH
            elif deviation >= 2.0:
                severity = CostAnomalySeverity.MEDIUM
            anom = CostAnomaly(rec.provider, rec.service, rec.region,
                               rec.amount, mean, deviation, severity)
            self._anomalies[anom.id] = anom
            logger.warning(f"Cost anomaly detected: {rec.provider}/{rec.service} "
                          f"- actual={rec.amount}, expected={mean:.2f}, dev={deviation:.2f}")
            return anom
        return None

    def _check_budgets(self, rec: CostRecord) -> None:
        if not self.budget_enforcement_enabled:
            return
        for budget in self._budgets.values():
            if budget.scope:
                if budget.scope.get("provider") and budget.scope["provider"] != rec.provider:
                    continue
                if budget.scope.get("service") and budget.scope["service"] != rec.service:
                    continue
            budget.spent += rec.amount
            if budget.spent >= budget.amount and budget.action != BudgetAction.WARN:
                logger.warning(f"Budget '{budget.name}' exceeded ({budget.spent:.2f}/{budget.amount:.2f})")

    def create_budget(self, name: str, amount: float, period: BudgetPeriod,
                      action: BudgetAction = BudgetAction.WARN,
                      scope: Optional[Dict[str, str]] = None) -> CostBudget:
        budget = CostBudget(name, amount, period, action, scope)
        self._budgets[budget.id] = budget
        return budget

    def get_budget(self, budget_id: str) -> Optional[CostBudget]:
        return self._budgets.get(budget_id)

    def list_budgets(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self._budgets.values()]

    def update_budget(self, budget_id: str, amount: Optional[float] = None,
                      action: Optional[BudgetAction] = None) -> bool:
        budget = self._budgets.get(budget_id)
        if not budget:
            return False
        if amount is not None:
            budget.amount = amount
        if action is not None:
            budget.action = action
        return True

    def delete_budget(self, budget_id: str) -> bool:
        if budget_id in self._budgets:
            del self._budgets[budget_id]
            return True
        return False

    def get_aggregated_costs(self, group_by: str = "provider") -> Dict[str, Any]:
        result: Dict[str, float] = {}
        for rec in self._cost_records:
            key = getattr(rec, group_by, "unknown")
            result[key] = result.get(key, 0) + rec.amount
        return result

    def get_costs_by_timeframe(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._cost_records
                if start <= r.recorded_at <= end]

    def list_anomalies(self, resolved: Optional[bool] = None,
                       severity: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for anom in self._anomalies.values():
            if resolved is not None and anom.resolved != resolved:
                continue
            if severity and anom.severity.value != severity:
                continue
            results.append(anom.to_dict())
        return results

    def resolve_anomaly(self, anomaly_id: str) -> bool:
        anom = self._anomalies.get(anomaly_id)
        if not anom:
            return False
        anom.resolved = True
        return True

    def get_total_spend(self) -> Dict[str, Any]:
        total = sum(self._provider_totals.values())
        return {"total": round(total, 2),
                "by_provider": {k: round(v, 2) for k, v in self._provider_totals.items()},
                "currency": self.default_currency,
                "record_count": len(self._cost_records)}

    def get_forecast(self, days: int = 30) -> Dict[str, Any]:
        if len(self._cost_records) < 2:
            return {"forecast": 0, "confidence": 0}
        daily_averages: Dict[str, float] = {}
        for rec in self._cost_records:
            day_key = rec.recorded_at.strftime("%Y-%m-%d")
            daily_averages[day_key] = daily_averages.get(day_key, 0) + rec.amount
        avg_daily = sum(daily_averages.values()) / max(len(daily_averages), 1)
        forecast = avg_daily * days
        return {"forecast": round(forecast, 2), "daily_average": round(avg_daily, 2),
                "days_analyzed": len(daily_averages), "forecast_days": days}

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_records": len(self._cost_records),
                "total_budgets": len(self._budgets),
                "active_anomalies": sum(1 for a in self._anomalies.values() if not a.resolved),
                "total_anomalies": len(self._anomalies),
                "providers_tracked": len(self._provider_totals)}

    def create_budget(self, name: str, amount: float, provider: str,
                       period: str = "monthly") -> Budget:
        budget = Budget(name, amount, provider, period)
        self._budgets[name] = budget
        return budget

    def delete_budget(self, name: str) -> bool:
        if name in self._budgets:
            del self._budgets[name]
            return True
        return False

    def get_budget_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for b in self._budgets.values():
            spend = sum(r.amount for r in self._cost_records
                        if r.provider == b.provider and r.category == b.name)
            pct = (spend / b.amount) * 100 if b.amount > 0 else 0
            if pct >= 80:
                alerts.append({"budget": b.name, "provider": b.provider,
                               "spend": round(spend, 2), "budget": b.amount,
                               "utilization": round(pct, 1), "alert_level": "warning" if pct < 100 else "critical"})
        return alerts

    async def auto_shutdown(self, provider: str, threshold: float = 0.9) -> Dict[str, Any]:
        budget_alerts = self.get_budget_alerts()
        shutdown = []
        for alert in budget_alerts:
            if alert["alert_level"] == "critical" and alert.get("provider") == provider:
                shutdown.append({"provider": provider, "action": "shutdown",
                                 "reason": f"Budget utilization at {alert['utilization']}%"})
        return {"shutdown_actions": shutdown, "total": len(shutdown)}

    def record_costs(self, provider: str, category: str, amount: float,
                     description: str = "") -> CostRecord:
        record = CostRecord(provider, category, amount, self.default_currency, description)
        self._cost_records.append(record)
        self._provider_totals[provider] = self._provider_totals.get(provider, 0) + amount
        return record

    def get_cost_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._cost_records if r.provider == provider]

    def get_cost_by_category(self, category: str) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._cost_records if r.category == category]

    def get_top_spend_providers(self, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_providers = sorted(self._provider_totals.items(), key=lambda x: x[1], reverse=True)
        return [{"provider": p, "total": round(t, 2)} for p, t in sorted_providers[:limit]]

    def analyze_cost_trends(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [r for r in self._cost_records if r.recorded_at >= cutoff]
        if not recent:
            return {"period_days": days, "total": 0, "daily_avg": 0, "trend": "insufficient_data"}
        total = sum(r.amount for r in recent)
        daily_avg = total / max(days, 1)
        mid = len(recent) // 2
        first_half = sum(r.amount for r in recent[:mid]) / max(mid, 1)
        second_half = sum(r.amount for r in recent[mid:]) / max(len(recent) - mid, 1)
        trend = "increasing" if second_half > first_half * 1.1 else "decreasing" if second_half < first_half * 0.9 else "stable"
        return {"period_days": days, "total": round(total, 2),
                "daily_avg": round(daily_avg, 2), "trend": trend,
                "first_half_avg": round(first_half, 2),
                "second_half_avg": round(second_half, 2)}

    def export_cost_report(self, format: str = "json") -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(),
                "total_records": len(self._cost_records),
                "total_spend": sum(r.amount for r in self._cost_records),
                "budgets": len(self._budgets),
                "anomalies": len(self._anomalies),
                "records": [r.to_dict() for r in self._cost_records],
                "budget_details": [b.to_dict() for b in self._budgets.values()]}

    def run_budget_enforcement(self) -> List[Dict[str, Any]]:
        actions = []
        for b in self._budgets.values():
            spend = sum(r.amount for r in self._cost_records
                        if r.provider == b.provider and r.category == b.name)
            if spend > b.amount:
                actions.append({"budget": b.name, "action": "enforce",
                                "overspend": round(spend - b.amount, 2),
                                "provider": b.provider})
        return actions

    def reset_budget_period(self, budget_id: str) -> bool:
        budget = self._budgets.get(budget_id)
        if not budget:
            return False
        budget.spent = 0.0
        budget.last_reset_at = datetime.utcnow()
        return True

    def get_cost_breakdown(self, provider: str, period_days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        records = [r for r in self._cost_records if r.provider == provider and r.recorded_at >= cutoff]
        by_service: Dict[str, float] = {}
        by_region: Dict[str, float] = {}
        total = 0.0
        for r in records:
            by_service[r.service] = by_service.get(r.service, 0) + r.amount
            by_region[r.region] = by_region.get(r.region, 0) + r.amount
            total += r.amount
        return {"provider": provider, "period_days": period_days, "total": round(total, 2),
                "by_service": {k: round(v, 2) for k, v in by_service.items()},
                "by_region": {k: round(v, 2) for k, v in by_region.items()},
                "record_count": len(records)}

    def set_budget_alert_threshold(self, threshold_pct: float) -> None:
        self.anomaly_threshold = threshold_pct

    def get_budget_utilization(self, budget_id: str) -> Dict[str, Any]:
        budget = self._budgets.get(budget_id)
        if not budget:
            return {"status": "error", "message": "Budget not found"}
        pct = (budget.spent / budget.amount) * 100 if budget.amount > 0 else 0
        return {"budget_id": budget_id, "name": budget.name, "amount": budget.amount,
                "spent": round(budget.spent, 2), "remaining": round(budget.amount - budget.spent, 2),
                "utilization_pct": round(pct, 1)}

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class CostAlertRule:
    rule_id: str
    name: str
    metric: str
    operator: str = "gt"
    threshold: float = 100.0
    cooldown_minutes: int = 60
    enabled: bool = True

@dataclass
class SavingsPlan:
    plan_id: str
    name: str
    commitment_amount: float
    term_months: int = 12
    provider: str = "aws"
    estimated_savings_pct: float = 20.0

@dataclass
class CostOptimizationRecommendation:
    recommendation_id: str
    resource_id: str
    provider: str
    current_cost: float
    projected_cost: float
    action: str
    savings: float
    risk: str = "low"

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_record_costs(self, records: List[Dict[str, Any]]) -> int:
        count = 0
        for r in records:
            self.record_cost(r.get("provider", "unknown"), r.get("service", "general"),
                            r.get("region", "global"), r.get("amount", 0),
                            r.get("currency", "USD"), r.get("tags"))
            count += 1
        return count

    async def batch_resolve_anomalies(self, anomaly_ids: List[str]) -> Dict[str, Any]:
        resolved = 0; not_found = 0
        for aid in anomaly_ids:
            if self.resolve_anomaly(aid):
                resolved += 1
            else:
                not_found += 1
        return {"resolved": resolved, "not_found": not_found, "total": len(anomaly_ids)}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_cost_records(self, page: int = 1, page_size: int = 50,
                               sort_by: str = "recorded_at", sort_desc: bool = True,
                               provider_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._cost_records)
        if provider_filter:
            items = [r for r in items if r.provider == provider_filter]
        items.sort(key=lambda r: getattr(r, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [r.to_dict() for r in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_anomalies(self, page: int = 1, page_size: int = 20,
                            severity_filter: Optional[str] = None) -> Dict[str, Any]:
        items = [a.to_dict() for a in self._anomalies.values()]
        if severity_filter:
            items = [a for a in items if a.get("severity") == severity_filter]
        items.sort(key=lambda a: a.get("detected_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_cost_report_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "provider", "service", "region", "amount", "currency", "recorded_at"])
        for r in self._cost_records:
            writer.writerow([r.id, r.provider, r.service, r.region, r.amount, r.currency, r.recorded_at.isoformat()])
        return output.getvalue()

    def import_costs_from_csv(self, csv_content: str) -> int:
        import csv, io
        reader = csv.DictReader(io.StringIO(csv_content))
        count = 0
        for row in reader:
            try:
                self.record_cost(row.get("provider", "unknown"), row.get("service", "general"),
                                row.get("region", "global"), float(row.get("amount", 0)),
                                row.get("currency", "USD"))
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_cost_efficiency_score(self) -> Dict[str, Any]:
        if not self._cost_records:
            return {"score": 100, "message": "No data"}
        anomaly_cost = sum(a.amount for a in self._anomalies.values() if not a.resolved)
        total_cost = sum(r.amount for r in self._cost_records)
        efficiency = max(0, 100 - (anomaly_cost / max(total_cost, 1)) * 100)
        return {"efficiency_score": round(efficiency, 1),
                "anomaly_cost": round(anomaly_cost, 2),
                "total_cost": round(total_cost, 2),
                "budget_compliance_rate": round(
                    sum(1 for b in self._budgets.values() if b.spent <= b.amount) / max(len(self._budgets), 1) * 100, 1)}

    def provider_cost_comparison(self) -> Dict[str, Any]:
        comparison = {}
        for prov, total in self._provider_totals.items():
            records = [r for r in self._cost_records if r.provider == prov]
            avg = sum(r.amount for r in records) / max(len(records), 1)
            comparison[prov] = {"total": round(total, 2), "avg_per_record": round(avg, 4),
                                "record_count": len(records)}
        return {"comparison": comparison, "most_expensive": max(comparison, key=lambda k: comparison[k]["total"]) if comparison else None}

    def get_seasonality_analysis(self) -> Dict[str, Any]:
        day_of_week: Dict[str, float] = {}
        for r in self._cost_records:
            day = r.recorded_at.strftime("%A")
            day_of_week[day] = day_of_week.get(day, 0) + r.amount
        peak_day = max(day_of_week, key=day_of_week.get) if day_of_week else None
        return {"daily_totals": {k: round(v, 2) for k, v in day_of_week.items()},
                "peak_day": peak_day, "lowest_day": min(day_of_week, key=day_of_week.get) if day_of_week else None}

# ── State Machine / Workflow ─────────────────────────────────────────

    async def cost_control_workflow(self, action: str) -> Dict[str, Any]:
        if action == "enforce_budgets":
            return {"actions": self.run_budget_enforcement(), "action": "enforce_budgets"}
        elif action == "detect_anomalies":
            recent = self._cost_records[-10:] if self._cost_records else []
            detected = []
            for r in recent:
                a = self._detect_anomaly(r)
                if a:
                    detected.append(a.to_dict())
            return {"anomalies_detected": len(detected), "action": "detect_anomalies"}
        elif action == "forecast":
            return self.get_forecast(30)
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_budget_reset_workflow(self) -> Dict[str, Any]:
        reset = 0
        for bid, budget in list(self._budgets.items()):
            if budget.period == BudgetPeriod.DAILY:
                budget.spent = 0.0
                budget.last_reset_at = datetime.utcnow()
                reset += 1
        return {"budgets_reset": reset}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_cost_control_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.anomaly_threshold < 1.0:
            warnings.append("anomaly_threshold is very sensitive (< 1.0)")
        if not self._cost_records:
            warnings.append("No cost records ingested yet")
        if not self._budgets:
            warnings.append("No budgets configured")
        if self.auto_shutdown_enabled and not self._budgets:
            warnings.append("auto_shutdown_enabled but no budgets to enforce against")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# -- Batch Operations ---------------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"results": results, "total": len(results),
                "successful": sum(1 for r in results if r["status"] == "processed")}

    async def batch_validate(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid = invalid = 0
        errors = []
        for item in items:
            if item.get("id"):
                valid += 1
            else:
                invalid += 1
                errors.append({"item": item, "reason": "missing id"})
        return {"valid": valid, "invalid": invalid, "errors": errors}

# -- Analytics / Aggregation -------------------------------------------

    def get_summary_stats(self) -> Dict[str, Any]:
        return {"total_items": 0, "active_items": 0, "inactive_items": 0}

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        return {"period_days": days, "data_points": 0, "trend": "stable"}

# -- Data Models -------------------------------------------------------

class OperationResult(BaseModel):
    success: bool = True
    operation: str = "unknown"
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")

    def add_operation(self, op: Dict[str, Any]) -> None:
        self.operations.append(op)

    def complete(self) -> None:
        self.status = "completed"

class HealthStatus(BaseModel):
    component: str
    status: str = Field(default="healthy")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    error_count: int = Field(default=0)
    response_time_ms: float = Field(default=0.0)

class StatusDashboard:
    def __init__(self) -> None:
        self._components: Dict[str, HealthStatus] = {}

    def register(self, component: str) -> HealthStatus:
        hs = HealthStatus(component=component)
        self._components[component] = hs
        return hs

    def heartbeat(self, component: str, response_time_ms: float = 0.0) -> None:
        if component in self._components:
            self._components[component].last_heartbeat = datetime.utcnow()
            self._components[component].response_time_ms = response_time_ms
            self._components[component].status = "healthy"

    def record_error(self, component: str) -> None:
        if component in self._components:
            self._components[component].error_count += 1
            if self._components[component].error_count > 5:
                self._components[component].status = "degraded"

    def get_overview(self) -> Dict[str, Any]:
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == "healthy")
        degraded = sum(1 for c in self._components.values() if c.status == "degraded")
        return {"total_components": total, "healthy": healthy, "degraded": degraded,
                "uptime_pct": round(healthy / max(total, 1) * 100, 1)}

    def get_component_status(self, component: str) -> Optional[HealthStatus]:
        return self._components.get(component)

class AuditLogger:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, action: str, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({
            "action": action, "resource_type": resource_type, "resource_id": resource_id,
            "details": details or {}, "timestamp": datetime.utcnow().isoformat(),
        })

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def get_by_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["resource_id"] == resource_id]

    def get_by_action(self, action: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["action"] == action]

    def count_by_action(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = []
        self._metrics[metric].append(value)

    def get_stats(self, metric: str) -> Dict[str, Any]:
        values = self._metrics.get(metric, [])
        if not values:
            return {"metric": metric, "count": 0}
        return {"metric": metric, "count": len(values), "min": round(min(values), 4),
                "max": round(max(values), 4), "avg": round(sum(values) / len(values), 4),
                "latest": round(values[-1], 4)}

    def get_all_stats(self) -> Dict[str, Any]:
        return {m: self.get_stats(m) for m in self._metrics}

    def reset(self, metric: Optional[str] = None) -> None:
        if metric:
            self._metrics[metric] = []
        else:
            self._metrics.clear()

class ConfigValidator:
    @staticmethod
    def validate(config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        for key, rules in schema.items():
            value = config.get(key)
            if rules.get("required", False) and value is None:
                errors.append(f"Missing required key: {key}")
            if value is not None and "type" in rules:
                if not isinstance(value, rules["type"]):
                    errors.append(f"Key {key} expected type {rules['type'].__name__}")
            if value is not None and "min" in rules and isinstance(value, (int, float)):
                if value < rules["min"]:
                    errors.append(f"Key {key} below minimum {rules['min']}")
            if value is not None and "max" in rules and isinstance(value, (int, float)):
                if value > rules["max"]:
                    errors.append(f"Key {key} above maximum {rules['max']}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def merge_with_defaults(config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(defaults)
        merged.update(config)
        return merged
