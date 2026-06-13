import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CostCategory(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    GPU = "gpu"
    LICENSE = "license"
    SUPPORT = "support"
    OTHER = "other"


class AllocationSource(Enum):
    ON_PREM = "on_prem"
    EDGE = "edge"
    CLOUD = "cloud"


class ChargebackMethod(Enum):
    DIRECT = "direct"
    PRO_RATA = "pro_rata"
    FIXED = "fixed"
    USAGE_BASED = "usage_based"


class CostTag:
    def __init__(self, key: str, value: str,
                 source: AllocationSource = AllocationSource.CLOUD):
        self.id = str(uuid.uuid4())
        self.key = key
        self.value = value
        self.source = source
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "key": self.key, "value": self.value,
                "source": self.source.value, "created_at": self.created_at.isoformat()}


class CostAllocation:
    def __init__(self, name: str, amount: float, category: CostCategory,
                 source: AllocationSource, tags: Dict[str, str],
                 team: str = "unallocated", project: str = "unallocated",
                 environment: str = "production"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.amount = amount
        self.category = category
        self.source = source
        self.tags = tags
        self.team = team
        self.project = project
        self.environment = environment
        self.period_start: Optional[datetime] = None
        self.period_end: Optional[datetime] = None
        self.created_at = datetime.utcnow()
        self.allocated = False

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "amount": self.amount,
                "category": self.category.value, "source": self.source.value,
                "tags": self.tags, "team": self.team, "project": self.project,
                "environment": self.environment,
                "period_start": self.period_start.isoformat() if self.period_start else None,
                "period_end": self.period_end.isoformat() if self.period_end else None,
                "created_at": self.created_at.isoformat(), "allocated": self.allocated}


class ChargebackEntry:
    def __init__(self, team: str, project: str, amount: float,
                 method: ChargebackMethod, period: str):
        self.id = str(uuid.uuid4())
        self.team = team
        self.project = project
        self.amount = amount
        self.method = method
        self.period = period
        self.created_at = datetime.utcnow()
        self.invoiced = False

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "team": self.team, "project": self.project,
                "amount": self.amount, "method": self.method.value,
                "period": self.period, "created_at": self.created_at.isoformat(),
                "invoiced": self.invoiced}


class HybridCostAllocation:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_currency = config.get("default_currency", "USD")
        self.chargeback_enabled = config.get("chargeback_enabled", True)
        self.allocation_method = ChargebackMethod(config.get("allocation_method", "usage_based"))
        self.erp_export_enabled = config.get("erp_export_enabled", False)
        self.default_team = config.get("default_team", "unallocated")
        self._tags: Dict[str, CostTag] = {}
        self._allocations: Dict[str, CostAllocation] = {}
        self._chargebacks: Dict[str, ChargebackEntry] = {}
        self._team_budgets: Dict[str, float] = {}
        self._export_history: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("HybridCostAllocation initialized")

    async def close(self) -> None:
        self._tags.clear()
        self._allocations.clear()
        self._chargebacks.clear()
        logger.info("HybridCostAllocation closed")

    def create_tag(self, key: str, value: str,
                   source: AllocationSource = AllocationSource.CLOUD) -> CostTag:
        tag = CostTag(key, value, source)
        self._tags[tag.id] = tag
        return tag

    def get_tag(self, tag_id: str) -> Optional[CostTag]:
        return self._tags.get(tag_id)

    def list_tags(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        if source:
            return [t.to_dict() for t in self._tags.values() if t.source.value == source]
        return [t.to_dict() for t in self._tags.values()]

    def delete_tag(self, tag_id: str) -> bool:
        if tag_id in self._tags:
            del self._tags[tag_id]
            return True
        return False

    def allocate_cost(self, name: str, amount: float, category: CostCategory,
                      source: AllocationSource, tags: Dict[str, str],
                      team: str = "unallocated", project: str = "unallocated",
                      environment: str = "production") -> CostAllocation:
        alloc = CostAllocation(name, amount, category, source, tags,
                               team, project, environment)
        alloc.allocated = True
        self._allocations[alloc.id] = alloc
        logger.info(f"Cost allocated: {name} ({amount}) to {team}/{project}")
        return alloc

    def get_allocation(self, allocation_id: str) -> Optional[CostAllocation]:
        return self._allocations.get(allocation_id)

    def list_allocations(self, team: Optional[str] = None,
                         project: Optional[str] = None,
                         source: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for a in self._allocations.values():
            if team and a.team != team:
                continue
            if project and a.project != project:
                continue
            if source and a.source.value != source:
                continue
            results.append(a.to_dict())
        return results

    def get_team_spend(self, team: str) -> Dict[str, Any]:
        team_allocs = [a for a in self._allocations.values()
                       if a.team == team and a.allocated]
        total = sum(a.amount for a in team_allocs)
        by_category: Dict[str, float] = {}
        for a in team_allocs:
            cat = a.category.value
            by_category[cat] = by_category.get(cat, 0) + a.amount
        by_source: Dict[str, float] = {}
        for a in team_allocs:
            src = a.source.value
            by_source[src] = by_source.get(src, 0) + a.amount
        return {"team": team, "total_spend": round(total, 2),
                "by_category": {k: round(v, 2) for k, v in by_category.items()},
                "by_source": {k: round(v, 2) for k, v in by_source.items()},
                "allocation_count": len(team_allocs)}

    def get_project_spend(self, project: str) -> Dict[str, Any]:
        proj_allocs = [a for a in self._allocations.values()
                       if a.project == project and a.allocated]
        total = sum(a.amount for a in proj_allocs)
        return {"project": project, "total_spend": round(total, 2),
                "allocation_count": len(proj_allocs)}

    def get_environment_spend(self, environment: str) -> Dict[str, Any]:
        env_allocs = [a for a in self._allocations.values()
                      if a.environment == environment and a.allocated]
        total = sum(a.amount for a in env_allocs)
        return {"environment": environment, "total_spend": round(total, 2),
                "allocation_count": len(env_allocs)}

    def create_chargeback(self, team: str, project: str, amount: float,
                          method: ChargebackMethod = ChargebackMethod.USAGE_BASED,
                          period: Optional[str] = None) -> ChargebackEntry:
        period = period or datetime.utcnow().strftime("%Y-%m")
        entry = ChargebackEntry(team, project, amount, method, period)
        self._chargebacks[entry.id] = entry
        logger.info(f"Chargeback created: {team}/{project} = {amount} ({period})")
        return entry

    def list_chargebacks(self, team: Optional[str] = None,
                         period: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for c in self._chargebacks.values():
            if team and c.team != team:
                continue
            if period and c.period != period:
                continue
            results.append(c.to_dict())
        return results

    def mark_chargeback_invoiced(self, chargeback_id: str) -> bool:
        entry = self._chargebacks.get(chargeback_id)
        if not entry:
            return False
        entry.invoiced = True
        return True

    def set_team_budget(self, team: str, budget: float) -> None:
        self._team_budgets[team] = budget

    def get_team_budget(self, team: str) -> Optional[float]:
        return self._team_budgets.get(team)

    def check_budget_compliance(self, team: str) -> Dict[str, Any]:
        budget = self._team_budgets.get(team)
        if budget is None:
            return {"team": team, "budget": None, "message": "No budget set"}
        spend = self.get_team_spend(team)["total_spend"]
        utilization = (spend / budget) * 100 if budget > 0 else 0
        return {"team": team, "budget": budget, "spend": spend,
                "utilization": round(utilization, 2),
                "compliant": spend <= budget}

    def export_to_erp(self, period: str) -> Dict[str, Any]:
        export = {"export_id": str(uuid.uuid4()), "period": period,
                  "generated_at": datetime.utcnow().isoformat(),
                  "total_allocations": len(self._allocations),
                  "total_chargebacks": len(self._chargebacks),
                  "entries": [a.to_dict() for a in self._allocations.values()]}
        self._export_history.append(export)
        logger.info(f"ERP export generated for {period}")
        return export

    def get_export_history(self) -> List[Dict[str, Any]]:
        return self._export_history

    def get_summary(self) -> Dict[str, Any]:
        total_allocation = sum(a.amount for a in self._allocations.values() if a.allocated)
        total_chargeback = sum(c.amount for c in self._chargebacks.values())
        teams = set(a.team for a in self._allocations.values())
        projects = set(a.project for a in self._allocations.values())
        return {"total_allocated": round(total_allocation, 2),
                "total_chargeback": round(total_chargeback, 2),
                "total_tags": len(self._tags),
                "active_teams": len(teams),
                "active_projects": len(projects),
                "team_budgets": len(self._team_budgets),
                "erp_exports": len(self._export_history)}

    def get_statistics(self) -> Dict[str, Any]:
        on_prem = sum(a.amount for a in self._allocations.values() if a.source == AllocationSource.ON_PREM)
        edge = sum(a.amount for a in self._allocations.values() if a.source == AllocationSource.EDGE)
        cloud_total = sum(a.amount for a in self._allocations.values() if a.source == AllocationSource.CLOUD)
        return {"total_tags": len(self._tags), "total_allocations": len(self._allocations),
                "total_chargebacks": len(self._chargebacks),
                "on_prem_spend": round(on_prem, 2), "edge_spend": round(edge, 2),
                "cloud_spend": round(cloud_total, 2),
                "teams_tracked": len(self._team_budgets)}

    def create_allocation_tag(self, key: str, value: str,
                               source: AllocationSource = AllocationSource.CLOUD) -> AllocationTag:
        tag = AllocationTag(key, value, source)
        self._tags[tag.id] = tag
        return tag

    def delete_allocation_tag(self, tag_id: str) -> bool:
        if tag_id in self._tags:
            del self._tags[tag_id]
            return True
        return False

    def list_tags(self, source: Optional[AllocationSource] = None) -> List[Dict[str, Any]]:
        if source:
            return [t.to_dict() for t in self._tags.values() if t.source == source]
        return [t.to_dict() for t in self._tags.values()]

    def allocate_cost(self, amount: float, team: str, project: str,
                       source: AllocationSource = AllocationSource.CLOUD,
                       description: str = "") -> CostAllocation:
        allocation = CostAllocation(amount, team, project, source, self.default_currency, description)
        self._allocations[allocation.id] = allocation
        return allocation

    def get_allocation(self, allocation_id: str) -> Optional[Dict[str, Any]]:
        a = self._allocations.get(allocation_id)
        return a.to_dict() if a else None

    def list_allocations(self, team: Optional[str] = None,
                          project: Optional[str] = None,
                          source: Optional[AllocationSource] = None) -> List[Dict[str, Any]]:
        results = list(self._allocations.values())
        if team:
            results = [a for a in results if a.team == team]
        if project:
            results = [a for a in results if a.project == project]
        if source:
            results = [a for a in results if a.source == source]
        return [a.to_dict() for a in results]

    def get_team_spend(self, team: str) -> Dict[str, Any]:
        team_allocations = [a for a in self._allocations.values()
                            if a.team == team and a.allocated]
        total = sum(a.amount for a in team_allocations)
        by_project = {}
        for a in team_allocations:
            by_project[a.project] = by_project.get(a.project, 0) + a.amount
        return {"team": team, "total_spend": round(total, 2),
                "by_project": {k: round(v, 2) for k, v in by_project.items()},
                "allocation_count": len(team_allocations)}

    def get_project_spend(self, project: str) -> Dict[str, Any]:
        project_allocations = [a for a in self._allocations.values()
                                if a.project == project and a.allocated]
        total = sum(a.amount for a in project_allocations)
        return {"project": project, "total_spend": round(total, 2),
                "allocation_count": len(project_allocations)}

    def create_chargeback(self, allocation_id: str, amount: float,
                           team: str, description: str = "") -> ChargebackEntry:
        chargeback = ChargebackEntry(allocation_id, amount, team, description)
        self._chargebacks[chargeback.id] = chargeback
        return chargeback

    def list_chargebacks(self, team: Optional[str] = None) -> List[Dict[str, Any]]:
        if team:
            return [c.to_dict() for c in self._chargebacks.values() if c.team == team]
        return [c.to_dict() for c in self._chargebacks.values()]

    def mark_invoiced(self, chargeback_id: str) -> bool:
        cb = self._chargebacks.get(chargeback_id)
        if not cb:
            return False
        cb.invoiced = True
        return True

    def get_cost_by_source(self) -> Dict[str, Any]:
        sources = {}
        for a in self._allocations.values():
            if a.allocated:
                key = a.source.value
                sources[key] = sources.get(key, 0) + a.amount
        return {k: round(v, 2) for k, v in sources.items()}

    def get_showback_report(self, period: str = "monthly") -> Dict[str, Any]:
        teams = set(a.team for a in self._allocations.values() if a.allocated)
        report = {}
        for t in teams:
            report[t] = self.get_team_spend(t)
        return {"period": period, "generated_at": datetime.utcnow().isoformat(),
                "teams": report, "total_allocations": len(self._allocations)}

    def get_allocation_efficiency(self) -> Dict[str, Any]:
        total = sum(a.amount for a in self._allocations.values())
        allocated = sum(a.amount for a in self._allocations.values() if a.allocated)
        return {"total_amount": round(total, 2),
                "allocated_amount": round(allocated, 2),
                "unallocated_amount": round(total - allocated, 2),
                "efficiency_pct": round(allocated / total * 100, 1) if total > 0 else 100}

    def bulk_tag_allocation(self, allocation_ids: List[str],
                             tag_key: str, tag_value: str) -> Dict[str, Any]:
        updated = 0
        for aid in allocation_ids:
            tag = self.create_allocation_tag(tag_key, tag_value)
            updated += 1
        return {"tag_key": tag_key, "tag_value": tag_value,
                "allocations_tagged": updated, "total": len(allocation_ids)}

    def allocate_cost_bulk(self, entries: List[Dict[str, Any]]) -> int:
        count = 0
        for e in entries:
            self.allocate_cost(e.get("name", "bulk"), e.get("amount", 0),
                               CostCategory(e.get("category", "other")),
                               AllocationSource(e.get("source", "cloud")),
                               e.get("tags", {}), e.get("team", "unallocated"),
                               e.get("project", "unallocated"),
                               e.get("environment", "production"))
            count += 1
        return count

    def get_unallocated_costs(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._allocations.values() if not a.allocated]

    def get_chargeback_by_period(self, period: str) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._chargebacks.values() if c.period == period]

    def get_team_budget_compliance(self) -> Dict[str, Any]:
        results = {}
        for team in self._team_budgets:
            results[team] = self.check_budget_compliance(team)
        return results

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class CostForecast:
    forecast_id: str
    team: str
    projected_amount: float
    confidence_interval_low: float
    confidence_interval_high: float
    period: str
    generated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SavingsRecommendation:
    recommendation_id: str
    team: str
    resource: str
    current_cost: float
    proposed_cost: float
    savings: float
    effort: str = "medium"

@dataclass
class BudgetAlertThreshold:
    team: str
    warning_pct: float = 80.0
    critical_pct: float = 95.0
    enabled: bool = True

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_allocate_costs(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        allocated = 0; errors = 0
        for e in entries:
            try:
                self.allocate_cost(e.get("name", "bulk"), e.get("amount", 0),
                                   CostCategory(e.get("category", "other")),
                                   AllocationSource(e.get("source", "cloud")),
                                   e.get("tags", {}), e.get("team", "unallocated"),
                                   e.get("project", "unallocated"),
                                   e.get("environment", "production"))
                allocated += 1
            except (ValueError, KeyError):
                errors += 1
        return {"allocated": allocated, "errors": errors, "total": len(entries)}

    async def batch_create_chargebacks(self, items: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for item in items:
            cb = self.create_chargeback(item.get("team", "unknown"), item.get("project", "unknown"),
                                        item.get("amount", 0), ChargebackMethod(item.get("method", "usage_based")),
                                        item.get("period"))
            ids.append(cb.id)
        return ids

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_allocations(self, page: int = 1, page_size: int = 20,
                              sort_by: str = "created_at", sort_desc: bool = True,
                              team_filter: Optional[str] = None,
                              source_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._allocations.values())
        if team_filter:
            items = [a for a in items if a.team == team_filter]
        if source_filter:
            items = [a for a in items if a.source.value == source_filter]
        items.sort(key=lambda a: getattr(a, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [a.to_dict() for a in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_chargebacks(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = sorted([c.to_dict() for c in self._chargebacks.values()], key=lambda c: c.get("created_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_cost_report(self, period: str = "monthly") -> str:
        return json.dumps({
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "allocations": [a.to_dict() for a in self._allocations.values()],
            "chargebacks": [c.to_dict() for c in self._chargebacks.values()],
            "team_budgets": {k: v for k, v in self._team_budgets.items()},
            "summary": self.get_summary(),
        }, indent=2)

    def export_team_spend_csv(self, team: str) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "category", "source", "amount", "project", "environment", "created_at"])
        for a in self._allocations.values():
            if a.team == team:
                writer.writerow([a.id, a.name, a.category.value, a.source.value, a.amount, a.project, a.environment, a.created_at.isoformat()])
        return output.getvalue()

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_cost_trend_analysis(self, months: int = 6) -> Dict[str, Any]:
        monthly_totals: Dict[str, float] = {}
        for a in self._allocations.values():
            if a.created_at:
                month_key = a.created_at.strftime("%Y-%m")
                monthly_totals[month_key] = monthly_totals.get(month_key, 0) + a.amount
        sorted_months = sorted(monthly_totals.keys())[-months:]
        trend = "stable"
        if len(sorted_months) >= 2:
            values = [monthly_totals[m] for m in sorted_months]
            if values[-1] > values[0] * 1.15:
                trend = "increasing"
            elif values[-1] < values[0] * 0.85:
                trend = "decreasing"
        return {
            "monthly_totals": {m: round(monthly_totals[m], 2) for m in sorted_months},
            "trend": trend, "months_analyzed": len(sorted_months),
            "average_monthly": round(sum(monthly_totals.get(m, 0) for m in sorted_months) / max(len(sorted_months), 1), 2),
        }

    def get_showback_savings_analysis(self) -> Dict[str, Any]:
        cloud_costs = sum(a.amount for a in self._allocations.values() if a.source == AllocationSource.CLOUD and a.allocated)
        on_prem_costs = sum(a.amount for a in self._allocations.values() if a.source == AllocationSource.ON_PREM and a.allocated)
        savings = on_prem_costs - cloud_costs
        return {
            "cloud_spend": round(cloud_costs, 2), "on_prem_spend": round(on_prem_costs, 2),
            "estimated_savings": round(max(0, savings), 2),
            "savings_pct": round(max(0, savings) / max(on_prem_costs, 1) * 100, 1),
        }

    def get_chargeback_collection_analysis(self) -> Dict[str, Any]:
        invoiced = sum(c.amount for c in self._chargebacks.values() if c.invoiced)
        pending = sum(c.amount for c in self._chargebacks.values() if not c.invoiced)
        return {
            "invoiced": round(invoiced, 2), "pending": round(pending, 2),
            "total": round(invoiced + pending, 2),
            "collection_rate": round(invoiced / max(invoiced + pending, 1) * 100, 1),
        }

# ── State Machine / Workflow ─────────────────────────────────────────

    async def budget_enforcement_workflow(self) -> Dict[str, Any]:
        actions = []
        for team in self._team_budgets:
            compliance = self.check_budget_compliance(team)
            if not compliance.get("compliant", True):
                actions.append({"team": team, "action": "alert",
                                "utilization": compliance["utilization"]})
        return {"enforcement_actions": actions, "total_over_budget": len(actions)}

    async def monthly_close_workflow(self, period: str) -> Dict[str, Any]:
        chargebacks = self.list_chargebacks(period=period)
        export = self.export_to_erp(period)
        return {
            "period": period, "chargebacks_created": len(chargebacks),
            "erp_export_id": export.get("export_id"),
            "total_allocations": len(self._allocations),
            "completed": True,
        }

# ── Configuration Validation ─────────────────────────────────────────

    def validate_cost_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if not self._team_budgets:
            warnings.append("No team budgets configured")
        if not self._tags:
            warnings.append("No cost tags defined, allocations may be untracked")
        if self.chargeback_enabled and not self._chargebacks:
            warnings.append("Chargeback enabled but no chargeback entries exist")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

# ── Batch Operations ───────────────────────────────────────────────────

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

# ── Analytics / Aggregation ───────────────────────────────────────────

    def get_summary_stats(self) -> Dict[str, Any]:
        return {"total_items": 0, "active_items": 0, "inactive_items": 0}

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        return {"period_days": days, "data_points": 0, "trend": "stable"}

# ── Data Models ───────────────────────────────────────────────────────

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
