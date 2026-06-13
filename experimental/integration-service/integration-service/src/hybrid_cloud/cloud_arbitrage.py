import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class Provider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HETZNER = "hetzner"
    OVH = "ovh"
    DIGITALOCEAN = "digitalocean"


class InstanceType(Enum):
    SPOT = "spot"
    PREEMPTIBLE = "preemptible"
    ON_DEMAND = "on_demand"
    RESERVED = "reserved"


class ArbitrageState(Enum):
    MONITORING = "monitoring"
    OPPORTUNITY_FOUND = "opportunity_found"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class PricingSnapshot:
    def __init__(self, provider: Provider, instance_type: InstanceType,
                 region: str, hourly_price: float, vcpu: int, memory_gb: int,
                 os: str = "linux"):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.instance_type = instance_type
        self.region = region
        self.hourly_price = hourly_price
        self.vcpu = vcpu
        self.memory_gb = memory_gb
        self.os = os
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "provider": self.provider.value,
                "instance_type": self.instance_type.value, "region": self.region,
                "hourly_price": self.hourly_price, "vcpu": self.vcpu,
                "memory_gb": self.memory_gb, "os": self.os,
                "timestamp": self.timestamp.isoformat()}


class ArbitrageOpportunity:
    def __init__(self, source_provider: Provider, target_provider: Provider,
                 source_price: float, target_price: float, savings_per_hour: float,
                 region: str, resource_id: str):
        self.id = str(uuid.uuid4())
        self.source_provider = source_provider
        self.target_provider = target_provider
        self.source_price = source_price
        self.target_price = target_price
        self.savings_per_hour = savings_per_hour
        self.savings_percentage = ((source_price - target_price) / source_price) * 100 if source_price > 0 else 0
        self.region = region
        self.resource_id = resource_id
        self.state = ArbitrageState.OPPORTUNITY_FOUND
        self.discovered_at = datetime.utcnow()
        self.migrated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "source_provider": self.source_provider.value,
                "target_provider": self.target_provider.value,
                "source_price": self.source_price, "target_price": self.target_price,
                "savings_per_hour": self.savings_per_hour,
                "savings_percentage": round(self.savings_percentage, 2),
                "region": self.region, "resource_id": self.resource_id,
                "state": self.state.value,
                "discovered_at": self.discovered_at.isoformat(),
                "migrated_at": self.migrated_at.isoformat() if self.migrated_at else None}


class CloudArbitrageEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_savings_percentage = config.get("min_savings_percentage", 15)
        self.min_savings_per_hour = config.get("min_savings_per_hour", 0.10)
        self.migration_cooldown_hours = config.get("migration_cooldown_hours", 24)
        self.max_concurrent_migrations = config.get("max_concurrent_migrations", 5)
        self.auto_migrate = config.get("auto_migrate", False)
        self.preferred_providers = config.get("preferred_providers", ["aws", "gcp", "azure"])
        self.pricing_cache_ttl = config.get("pricing_cache_ttl", 300)
        self._pricing_snapshots: List[PricingSnapshot] = []
        self._opportunities: Dict[str, ArbitrageOpportunity] = {}
        self._migrations_in_progress: Dict[str, Dict[str, Any]] = {}
        self._migration_history: List[Dict[str, Any]] = []
        self._savings_tracking: Dict[str, float] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("CloudArbitrageEngine initialized")

    async def close(self) -> None:
        self._pricing_snapshots.clear()
        self._opportunities.clear()
        self._migrations_in_progress.clear()
        logger.info("CloudArbitrageEngine closed")

    def record_pricing(self, provider: Provider, instance_type: InstanceType,
                       region: str, hourly_price: float, vcpu: int,
                       memory_gb: int, os: str = "linux") -> PricingSnapshot:
        snap = PricingSnapshot(provider, instance_type, region, hourly_price,
                               vcpu, memory_gb, os)
        self._pricing_snapshots.append(snap)
        return snap

    def get_latest_pricing(self, provider: Optional[Provider] = None,
                           region: Optional[str] = None) -> List[Dict[str, Any]]:
        window = datetime.utcnow() - timedelta(seconds=self.pricing_cache_ttl)
        recent = [s for s in self._pricing_snapshots if s.timestamp >= window]
        results = []
        for s in recent:
            if provider and s.provider != provider:
                continue
            if region and s.region != region:
                continue
            results.append(s.to_dict())
        return results

    def find_opportunities(self, workload_specs: Dict[str, Any]) -> List[ArbitrageOpportunity]:
        vcpu = workload_specs.get("vcpu", 2)
        memory = workload_specs.get("memory_gb", 4)
        current_provider = workload_specs.get("current_provider")
        current_region = workload_specs.get("region", "us-east-1")
        current_price = workload_specs.get("current_hourly_price", 0.0)
        resource_id = workload_specs.get("resource_id", "unknown")

        window = datetime.utcnow() - timedelta(seconds=self.pricing_cache_ttl)
        candidates = [s for s in self._pricing_snapshots if s.timestamp >= window]

        opportunities = []
        for snap in candidates:
            if snap.provider.value == current_provider and snap.region == current_region:
                continue
            if snap.vcpu < vcpu or snap.memory_gb < memory:
                continue
            if current_price > 0 and snap.hourly_price >= current_price:
                continue
            savings = current_price - snap.hourly_price
            savings_pct = ((current_price - snap.hourly_price) / current_price) * 100 if current_price > 0 else 0
            if savings_pct >= self.min_savings_percentage and savings >= self.min_savings_per_hour:
                opp = ArbitrageOpportunity(
                    Provider(current_provider) if current_provider else Provider.AWS,
                    snap.provider, current_price, snap.hourly_price,
                    savings, snap.region, resource_id)
                self._opportunities[opp.id] = opp
                opportunities.append(opp)
        opportunities.sort(key=lambda o: o.savings_per_hour, reverse=True)
        return opportunities

    def get_opportunity(self, opportunity_id: str) -> Optional[ArbitrageOpportunity]:
        return self._opportunities.get(opportunity_id)

    def list_opportunities(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        if state:
            return [o.to_dict() for o in self._opportunities.values() if o.state.value == state]
        return [o.to_dict() for o in self._opportunities.values()]

    def dismiss_opportunity(self, opportunity_id: str) -> bool:
        if opportunity_id in self._opportunities:
            del self._opportunities[opportunity_id]
            return True
        return False

    async def execute_migration(self, opportunity_id: str) -> Dict[str, Any]:
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            return {"status": "error", "message": "Opportunity not found"}
        if len(self._migrations_in_progress) >= self.max_concurrent_migrations:
            return {"status": "error", "message": "Max concurrent migrations reached"}

        opp.state = ArbitrageState.MIGRATING
        migration_id = f"migr-{uuid.uuid4().hex[:12]}"
        migration = {
            "migration_id": migration_id, "opportunity_id": opportunity_id,
            "source_provider": opp.source_provider.value,
            "target_provider": opp.target_provider.value,
            "source_price": opp.source_price, "target_price": opp.target_price,
            "expected_savings_per_hour": opp.savings_per_hour,
            "region": opp.region, "resource_id": opp.resource_id,
            "started_at": datetime.utcnow().isoformat(),
            "state": "in_progress"
        }
        self._migrations_in_progress[migration_id] = migration
        logger.info(f"Migration {migration_id} started: {opp.source_provider.value} -> {opp.target_provider.value}")
        return migration

    def complete_migration(self, migration_id: str) -> Dict[str, Any]:
        migration = self._migrations_in_progress.get(migration_id)
        if not migration:
            return {"status": "error", "message": "Migration not found"}
        opp = self._opportunities.get(migration["opportunity_id"])
        if opp:
            opp.state = ArbitrageState.COMPLETED
            opp.migrated_at = datetime.utcnow()
        migration["state"] = "completed"
        migration["completed_at"] = datetime.utcnow().isoformat()
        savings_key = f"{migration['source_provider']}->{migration['target_provider']}"
        self._savings_tracking[savings_key] = self._savings_tracking.get(savings_key, 0) + migration["expected_savings_per_hour"]
        self._migration_history.append(migration)
        del self._migrations_in_progress[migration_id]
        return migration

    def fail_migration(self, migration_id: str, reason: str) -> Dict[str, Any]:
        migration = self._migrations_in_progress.get(migration_id)
        if not migration:
            return {"status": "error", "message": "Migration not found"}
        opp = self._opportunities.get(migration["opportunity_id"])
        if opp:
            opp.state = ArbitrageState.FAILED
        migration["state"] = "failed"
        migration["failure_reason"] = reason
        self._migration_history.append(migration)
        del self._migrations_in_progress[migration_id]
        return migration

    def rollback_migration(self, migration_id: str) -> Dict[str, Any]:
        migration = None
        for m in self._migration_history:
            if m["migration_id"] == migration_id:
                migration = m
                break
        if not migration:
            return {"status": "error", "message": "Migration not found in history"}
        opp = self._opportunities.get(migration.get("opportunity_id", ""))
        if opp:
            opp.state = ArbitrageState.ROLLED_BACK
        migration["rolled_back_at"] = datetime.utcnow().isoformat()
        logger.info(f"Migration {migration_id} rolled back")
        return {"migration_id": migration_id, "status": "rolled_back"}

    def get_migration_status(self, migration_id: str) -> Optional[Dict[str, Any]]:
        mig = self._migrations_in_progress.get(migration_id)
        if mig:
            return mig
        for m in self._migration_history:
            if m["migration_id"] == migration_id:
                return m
        return None

    def get_total_savings(self) -> Dict[str, Any]:
        total = sum(self._savings_tracking.values())
        return {"total_savings_per_hour": round(total, 4),
                "total_savings_per_day": round(total * 24, 2),
                "total_savings_per_month": round(total * 24 * 30, 2),
                "by_route": self._savings_tracking}

    def get_statistics(self) -> Dict[str, Any]:
        completed = sum(1 for m in self._migration_history if m.get("state") == "completed")
        failed = sum(1 for m in self._migration_history if m.get("state") == "failed")
        return {"total_opportunities": len(self._opportunities),
                "open_opportunities": sum(1 for o in self._opportunities.values() if o.state == ArbitrageState.OPPORTUNITY_FOUND),
                "migrations_in_progress": len(self._migrations_in_progress),
                "completed_migrations": completed,
                "failed_migrations": failed,
                "total_migrations": len(self._migration_history)}

    def compare_pricing(self, vcpu: int, memory_gb: int,
                        region: str, os: str = "linux") -> List[Dict[str, Any]]:
        results = []
        for snap in self._pricing_snapshots:
            if snap.vcpu != vcpu or snap.memory_gb != memory_gb:
                continue
            if region and snap.region != region:
                continue
            results.append(snap.to_dict())
        results.sort(key=lambda x: x["hourly_price"])
        return results

    def get_opportunities_by_region(self, region: str) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._opportunities.values()
                if o.source_region == region or o.target_region == region]

    def get_opportunities_by_state(self, state: ArbitrageState) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._opportunities.values() if o.state == state]

    async def execute_arbitrage_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            return {"status": "error", "message": "Opportunity not found"}
        if opp.state != ArbitrageState.OPPORTUNITY_FOUND:
            return {"status": "error", "message": f"Opportunity in state {opp.state.value}, expected OPPORTUNITY_FOUND"}
        opp.state = ArbitrageState.MIGRATING
        mig = {
            "migration_id": str(uuid.uuid4()),
            "opportunity_id": opp.opportunity_id,
            "source": opp.source_provider,
            "target": opp.target_provider,
            "workload": opp.workload_description,
            "state": "migrating",
            "started_at": datetime.utcnow().isoformat(),
            "estimated_savings_per_hour": round(opp.savings_per_hour, 4)
        }
        self._migrations_in_progress[mig["migration_id"]] = mig
        self._migration_history.append(mig)
        self._savings_tracking[f"{opp.source_provider}->{opp.target_provider}"] = \
            self._savings_tracking.get(f"{opp.source_provider}->{opp.target_provider}", 0) + opp.savings_per_hour
        opp.state = ArbitrageState.COMPLETED
        logger.info(f"Arbitrage executed: {opp.source_provider} -> {opp.target_provider}")
        return mig

    def create_pricing_alert(self, provider: str, threshold: float,
                              region: str) -> Dict[str, Any]:
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        alert = {"id": alert_id, "provider": provider, "threshold": threshold,
                 "region": region, "created_at": datetime.utcnow().isoformat(),
                 "triggered": False}
        if "alerts" not in self.config:
            self.config["alerts"] = []
        self.config["alerts"].append(alert)
        return alert

    def list_alerts(self) -> List[Dict[str, Any]]:
        return self.config.get("alerts", [])

    def delete_alert(self, alert_id: str) -> bool:
        alerts = self.config.get("alerts", [])
        for i, a in enumerate(alerts):
            if a.get("id") == alert_id:
                alerts.pop(i)
                return True
        return False

    def analyze_spot_prices(self, provider: str, region: str,
                            instance_type: str) -> Dict[str, Any]:
        savings_vs_on_demand = random.uniform(0.3, 0.7)
        interruption_rate = random.uniform(0.05, 0.3)
        return {"provider": provider, "region": region, "instance_type": instance_type,
                "savings_vs_on_demand": round(savings_vs_on_demand * 100, 1),
                "interruption_rate": round(interruption_rate * 100, 1),
                "recommended": savings_vs_on_demand > 0.4 and interruption_rate < 0.2,
                "spot_price": round(random.uniform(0.01, 0.50), 4),
                "on_demand_price": round(random.uniform(0.05, 1.0), 4)}

    def get_arbitrage_summary(self) -> Dict[str, Any]:
        completed = sum(1 for m in self._migration_history if m.get("state") == "completed")
        active = len(self._migrations_in_progress)
        savings = self.get_total_savings()
        return {"total_opportunities": len(self._opportunities),
                "completed_migrations": completed,
                "active_migrations": active,
                "open_opportunities": sum(1 for o in self._opportunities.values()
                                          if o.state == ArbitrageState.OPPORTUNITY_FOUND),
                "total_savings_per_hour": savings.get("total_savings_per_hour", 0),
                "total_savings_per_month": savings.get("total_savings_per_month", 0),
                "providers_monitored": len(set(o.source_provider for o in self._opportunities.values()))}

    def export_opportunities(self) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._opportunities.values()]

    def clear_completed_migrations(self) -> int:
        count = len(self._migration_history)
        self._migration_history.clear()
        self._migrations_in_progress.clear()
        return count

    def get_savings_by_provider_pair(self) -> Dict[str, float]:
        return dict(self._savings_tracking)

    def recommend_provider(self, workload_specs: Dict[str, Any]) -> Dict[str, Any]:
        opportunities = self.find_opportunities(workload_specs)
        if not opportunities:
            return {"recommendation": "stay", "current_provider": workload_specs.get("current_provider"),
                    "reason": "No suitable alternative found"}
        best = opportunities[0]
        return {"recommendation": "migrate", "from": best.source_provider.value,
                "to": best.target_provider.value, "savings_per_hour": best.savings_per_hour,
                "savings_percentage": best.savings_percentage,
                "reason": f"Save ${best.savings_per_hour:.4f}/h ({best.savings_percentage:.1f}%)"}

    def set_pricing_cache_ttl(self, ttl_seconds: int) -> None:
        self.pricing_cache_ttl = ttl_seconds

    def get_migration_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return sorted(self._migration_history, key=lambda m: m.get("started_at", ""), reverse=True)[:limit]

    def import_pricing_csv(self, rows: List[Dict[str, Any]]) -> int:
        count = 0
        for row in rows:
            try:
                prov = Provider(row.get("provider", "aws"))
                it = InstanceType(row.get("instance_type", "on_demand"))
                self.record_pricing(prov, it, row.get("region", "us-east-1"),
                                    float(row.get("hourly_price", 0)), int(row.get("vcpu", 2)),
                                    int(row.get("memory_gb", 4)), row.get("os", "linux"))
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class ProviderPricingProfile:
    provider: Provider
    region: str
    spot_discount_pct: float
    reserved_discount_pct: float
    commitment_options: List[str] = field(default_factory=list)

@dataclass
class ArbitrageSimulation:
    simulation_id: str
    workload_specs: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    best_savings: float
    generated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MigrationBatch:
    batch_id: str
    opportunity_ids: List[str]
    target_provider: Provider
    total_expected_savings: float
    status: str = "pending"

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_execute_migrations(self, opportunity_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for oid in opportunity_ids:
            r = await self.execute_migration(oid)
            results[oid] = r
        return {"results": results, "total": len(opportunity_ids),
                "in_progress": len(self._migrations_in_progress)}

    async def batch_dismiss_opportunities(self, opportunity_ids: List[str]) -> Dict[str, Any]:
        dismissed = 0; not_found = 0
        for oid in opportunity_ids:
            if self.dismiss_opportunity(oid):
                dismissed += 1
            else:
                not_found += 1
        return {"dismissed": dismissed, "not_found": not_found}

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_opportunities(self, page: int = 1, page_size: int = 20,
                                sort_by: str = "savings_per_hour", sort_desc: bool = True,
                                state_filter: Optional[str] = None,
                                provider_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._opportunities.values())
        if state_filter:
            items = [o for o in items if o.state.value == state_filter]
        if provider_filter:
            items = [o for o in items if o.source_provider.value == provider_filter or o.target_provider.value == provider_filter]
        items.sort(key=lambda o: getattr(o, sort_by, 0), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [o.to_dict() for o in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_migration_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = sorted(self._migration_history, key=lambda m: m.get("started_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_opportunities_report(self) -> str:
        return json.dumps({
            "total_opportunities": len(self._opportunities),
            "total_savings": self.get_total_savings(),
            "opportunities": [o.to_dict() for o in self._opportunities.values()],
            "migration_history": self._migration_history,
            "generated_at": datetime.utcnow().isoformat(),
        }, indent=2)

    def import_pricing_from_api(self, pricing_data: List[Dict[str, Any]]) -> int:
        count = 0
        for p in pricing_data:
            try:
                self.record_pricing(Provider(p["provider"]), InstanceType(p.get("instance_type", "on_demand")),
                                    p.get("region", "us-east-1"), float(p["hourly_price"]),
                                    int(p.get("vcpu", 2)), int(p.get("memory_gb", 4)),
                                    p.get("os", "linux"))
                count += 1
            except (ValueError, KeyError):
                continue
        return count

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_savings_optimization_score(self) -> Dict[str, Any]:
        total_opportunities = len(self._opportunities)
        open_opps = sum(1 for o in self._opportunities.values() if o.state == ArbitrageState.OPPORTUNITY_FOUND)
        completed = sum(1 for m in self._migration_history if m.get("state") == "completed")
        total_savings = self.get_total_savings()
        return {
            "optimization_score": round(completed / max(total_opportunities, 1) * 100, 1),
            "open_opportunities": open_opps,
            "completed_migrations": completed,
            "total_potential_savings_per_hour": round(sum(o.savings_per_hour for o in self._opportunities.values() if o.state == ArbitrageState.OPPORTUNITY_FOUND), 4),
            "realized_savings_per_hour": total_savings.get("total_savings_per_hour", 0),
        }

    def get_provider_price_trends(self, provider: str, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        relevant = [s for s in self._pricing_snapshots if s.provider.value == provider and s.timestamp >= cutoff]
        if not relevant:
            return {"provider": provider, "message": "No data for period"}
        prices = [s.hourly_price for s in relevant]
        return {
            "provider": provider, "samples": len(relevant),
            "min_price": round(min(prices), 4), "max_price": round(max(prices), 4),
            "avg_price": round(sum(prices) / len(prices), 4),
            "volatility": round((max(prices) - min(prices)) / max(min(prices), 0.001) * 100, 1),
        }

    def get_region_arbitrage_opportunities(self, region: str) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._opportunities.values()
                if o.region == region and o.state == ArbitrageState.OPPORTUNITY_FOUND]

# ── State Machine / Workflow ─────────────────────────────────────────

    async def arbitrage_lifecycle_workflow(self, opportunity_id: str, action: str) -> Dict[str, Any]:
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            return {"status": "error", "message": "Opportunity not found"}
        if action == "execute":
            return await self.execute_arbitrage_opportunity(opportunity_id)
        elif action == "dismiss":
            self.dismiss_opportunity(opportunity_id)
            return {"status": "dismissed", "opportunity_id": opportunity_id}
        elif action == "analyze":
            return {
                "opportunity_id": opportunity_id,
                "source": opp.source_provider.value,
                "target": opp.target_provider.value,
                "savings_per_hour": opp.savings_per_hour,
                "savings_pct": opp.savings_percentage,
                "state": opp.state.value,
            }
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_pricing_refresh_workflow(self) -> Dict[str, Any]:
        providers = [Provider.AWS, Provider.AZURE, Provider.GCP]
        refreshed = 0
        for p in providers:
            for region in ["us-east-1", "eu-west-1", "ap-southeast-1"]:
                self.record_pricing(p, InstanceType.ON_DEMAND, region,
                                    round(random.uniform(0.05, 1.0), 4), 2, 4)
                refreshed += 1
        return {"pricing_snapshots_refreshed": refreshed}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_arbitrage_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.min_savings_percentage < 1:
            warnings.append("min_savings_percentage is very low")
        if self.migration_cooldown_hours < 1:
            errors.append("migration_cooldown_hours must be >= 1")
        if not self.preferred_providers:
            errors.append("At least one preferred provider must be configured")
        if self.auto_migrate and not self.config.get("approval_required", True):
            warnings.append("auto_migrate enabled without approval gate")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                "provider_count": len(self.preferred_providers)}

# -- Advanced Data Models ----------------------------------------------

class ArbitrageWindow(BaseModel):
    source_provider: Provider
    target_provider: Provider
    instance_type: InstanceType
    region: str
    current_price: float
    target_price: float
    savings_per_unit: float
    savings_percentage: float
    window_open: datetime = Field(default_factory=datetime.utcnow)
    window_close: Optional[datetime] = None
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    risk_level: str = Field(default="low")

    def is_active(self) -> bool:
        now = datetime.utcnow()
        if self.window_close and now > self.window_close:
            return False
        return True

class PriceForecast(BaseModel):
    provider: Provider
    region: str
    instance_type: InstanceType
    predicted_price: float
    confidence_interval_low: float
    confidence_interval_high: float
    forecast_date: datetime
    model_version: str = Field(default="v1")

# -- Batch Arbitrage Operations ----------------------------------------

    async def batch_evaluate_opportunities(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for res in resources:
            provider = Provider(res.get("provider", "aws"))
            instance = InstanceType(res.get("instance_type", "on_demand"))
            region = res.get("region", "us-east-1")
            price = float(res.get("hourly_price", 0))
            candidates = [p for p in Provider if p != provider]
            best = None
            best_savings = 0
            for candidate in candidates:
                target_price = self.current_prices.get((candidate, instance, region), price)
                if target_price < price and (price - target_price) > 0:
                    savings = price - target_price
                    if savings > best_savings:
                        best_savings = savings
                        best = candidate
            if best:
                opp_id = self._discover_arbitrage(provider, best, instance, region, price, self.current_prices.get((best, instance, region), price))
                results.append({"resource": res.get("name"), "opportunity_id": opp_id, "from": provider.value, "to": best.value, "savings": round(best_savings, 4)})
        return results

    async def batch_execute_opportunities(self, opportunity_ids: List[str]) -> Dict[str, Any]:
        results = []
        for oid in opportunity_ids:
            try:
                result = await self.execute_arbitrage_opportunity(oid)
                results.append({"opportunity_id": oid, "status": result.get("status")})
            except Exception as e:
                results.append({"opportunity_id": oid, "status": "failed", "error": str(e)})
        return {"results": results, "total": len(results), "succeeded": sum(1 for r in results if r["status"] == "executed")}

# -- Analytics / Aggregation -------------------------------------------

    def get_arbitrage_summary(self) -> Dict[str, Any]:
        total_opps = len(self._opportunities)
        open_opps = sum(1 for o in self._opportunities.values() if o.state == ArbitrageState.OPPORTUNITY_FOUND)
        executed = sum(1 for o in self._opportunities.values() if o.state == ArbitrageState.EXECUTED)
        dismissed = sum(1 for o in self._opportunities.values() if o.state == ArbitrageState.DISMISSED)
        total_savings = sum(o.savings_per_hour for o in self._opportunities.values() if o.state == ArbitrageState.EXECUTED)
        return {"total_opportunities": total_opps, "open": open_opps, "executed": executed,
                "dismissed": dismissed, "total_realized_savings_per_hour": round(total_savings, 4),
                "conversion_rate": round(executed / max(total_opps, 1) * 100, 1)}

    def get_provider_pair_analysis(self) -> Dict[str, Any]:
        pairs: Dict[str, Dict[str, int]] = {}
        for opp in self._opportunities.values():
            key = f"{opp.source_provider.value}->{opp.target_provider.value}"
            if key not in pairs:
                pairs[key] = {"count": 0, "total_savings": 0.0, "avg_savings_pct": 0.0}
            pairs[key]["count"] += 1
            pairs[key]["total_savings"] += opp.savings_per_hour
        for p in pairs.values():
            p["avg_savings_pct"] = round(p["total_savings"] / max(p["count"], 1), 4)
        return {"provider_pairs": pairs, "total_pairs": len(pairs)}

    def get_savings_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend: Dict[str, float] = {}
        for m in self._migration_history:
            timestamp = m.get("timestamp", "")
            if timestamp >= cutoff.isoformat():
                day = timestamp[:10]
                savings = m.get("savings", 0)
                trend[day] = trend.get(day, 0) + savings
        return {"trend": trend, "days": days, "total_savings_period": round(sum(trend.values()), 4)}

# -- Configuration Manager ---------------------------------------------

class ArbitrageConfigManager:
    def __init__(self) -> None:
        self._configs: Dict[str, Dict[str, Any]] = {}

    def set_config(self, key: str, value: Any) -> None:
        self._configs[key] = {"value": value, "updated_at": datetime.utcnow().isoformat()}

    def get_config(self, key: str, default: Any = None) -> Any:
        entry = self._configs.get(key)
        return entry["value"] if entry else default

    def get_all_configs(self) -> Dict[str, Any]:
        return {k: v["value"] for k, v in self._configs.items()}

    def validate_all(self) -> Dict[str, Any]:
        errors = []
        for key, entry in self._configs.items():
            if entry["value"] is None:
                errors.append(f"Config {key} is None")
        return {"valid": len(errors) == 0, "errors": errors, "config_count": len(self._configs)}

# -- Risk Assessment ---------------------------------------------------

class RiskAssessment(BaseModel):
    opportunity_id: str
    risk_score: float = Field(default=0.0, ge=0, le=1)
    factors: List[str] = Field(default_factory=list)
    recommendation: str = Field(default="proceed")
    assessed_at: datetime = Field(default_factory=datetime.utcnow)

class RiskAssessor:
    def __init__(self) -> None:
        self._assessments: Dict[str, RiskAssessment] = {}

    def assess(self, opportunity: "ArbitrageOpportunity") -> RiskAssessment:
        score = 0.0
        factors = []
        if opportunity.savings_percentage > 40:
            score += 0.3
            factors.append("high_savings_percentage")
        if opportunity.target_provider not in [Provider.AWS, Provider.AZURE, Provider.GCP]:
            score += 0.2
            factors.append("non_major_provider")
        if score > 0.5:
            recommendation = "caution"
        elif score > 0.3:
            recommendation = "review"
        else:
            recommendation = "proceed"
        assessment = RiskAssessment(opportunity_id=opportunity.opportunity_id, risk_score=round(score, 2), factors=factors, recommendation=recommendation)
        self._assessments[opportunity.opportunity_id] = assessment
        return assessment

    def get_assessment(self, opportunity_id: str) -> Optional[RiskAssessment]:
        return self._assessments.get(opportunity_id)

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
