"""Extended resource quota management with limits, reservations, and usage tracking."""
import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuotaResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    CONTAINERS = "containers"
    VMS = "virtual_machines"
    DATABASES = "databases"
    FUNCTIONS = "functions"
    SECRETS = "secrets"
    CERTIFICATES = "certificates"
    DNS_RECORDS = "dns_records"
    LOAD_BALANCERS = "load_balancers"
    NETWORKS = "networks"
    SUBNETS = "subnets"
    PUBLIC_IPS = "public_ips"
    API_CALLS = "api_calls"
    STORAGE_OBJECTS = "storage_objects"


class QuotaPeriod(str, Enum):
    TOTAL = "total"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    HOURLY = "hourly"


class QuotaScope(str, Enum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    USER = "user"
    TEAM = "team"


class QuotaAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    THROTTLE = "throttle"
    NOTIFY = "notify"


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class QuotaDefinition:
    id: str
    name: str
    description: str
    resource_type: QuotaResourceType
    scope: QuotaScope
    scope_id: str
    hard_limit: float
    soft_limit: Optional[float] = None
    warning_threshold: float = 80.0
    period: QuotaPeriod = QuotaPeriod.TOTAL
    action_on_exceed: QuotaAction = QuotaAction.BLOCK
    unit: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuotaUsage:
    id: str
    quota_id: str
    current_usage: float = 0.0
    peak_usage: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    usage_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceReservation:
    id: str
    name: str
    resource_type: QuotaResourceType
    amount: float
    scope: QuotaScope
    scope_id: str
    status: ReservationStatus = ReservationStatus.ACTIVE
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    created_by: Optional[str] = None
    priority: int = 0
    notes: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuotaAlert:
    id: str
    quota_id: str
    usage: float
    threshold: float
    message: str
    severity: str = "warning"
    acknowledged: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None


@dataclass
class QuotaOverride:
    id: str
    quota_id: str
    new_hard_limit: Optional[float] = None
    new_soft_limit: Optional[float] = None
    reason: str = ""
    expires_at: Optional[datetime] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


class QuotaManager:
    def __init__(self, storage_path: str = "data/quota_manager.json"):
        self.storage_path = storage_path
        self.quotas: Dict[str, QuotaDefinition] = {}
        self.usages: Dict[str, QuotaUsage] = {}
        self.reservations: Dict[str, ResourceReservation] = {}
        self.alerts: Dict[str, QuotaAlert] = {}
        self.overrides: Dict[str, QuotaOverride] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for q_data in data.get("quotas", []):
            q = QuotaDefinition(**q_data)
            self.quotas[q.id] = q
        for u_data in data.get("usages", []):
            u = QuotaUsage(**u_data)
            self.usages[u.id] = u
        for r_data in data.get("reservations", []):
            r = ResourceReservation(**r_data)
            self.reservations[r.id] = r
        for a_data in data.get("alerts", []):
            a = QuotaAlert(**a_data)
            self.alerts[a.id] = a
        for o_data in data.get("overrides", []):
            o = QuotaOverride(**o_data)
            self.overrides[o.id] = o

    def _save_data(self) -> None:
        data = {
            "quotas": [q.__dict__ for q in self.quotas.values()],
            "usages": [u.__dict__ for u in self.usages.values()],
            "reservations": [r.__dict__ for r in self.reservations.values()],
            "alerts": [a.__dict__ for a in self.alerts.values()],
            "overrides": [o.__dict__ for o in self.overrides.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("QuotaManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("QuotaManager closed")

    def create_quota(self, name: str, description: str, resource_type: QuotaResourceType, scope: QuotaScope, scope_id: str, hard_limit: float, soft_limit: Optional[float] = None, warning_threshold: float = 80.0, period: QuotaPeriod = QuotaPeriod.TOTAL, action_on_exceed: QuotaAction = QuotaAction.BLOCK, unit: str = "", tags: Optional[List[str]] = None) -> QuotaDefinition:
        q = QuotaDefinition(id=str(uuid.uuid4()), name=name, description=description, resource_type=resource_type, scope=scope, scope_id=scope_id, hard_limit=hard_limit, soft_limit=soft_limit, warning_threshold=warning_threshold, period=period, action_on_exceed=action_on_exceed, unit=unit, tags=tags or [])
        self.quotas[q.id] = q
        usage = QuotaUsage(id=str(uuid.uuid4()), quota_id=q.id)
        self.usages[usage.id] = usage
        self._save_data()
        return q

    def get_quota(self, quota_id: str) -> Optional[QuotaDefinition]:
        return self.quotas.get(quota_id)

    def update_quota(self, quota_id: str, updates: Dict[str, Any]) -> Optional[QuotaDefinition]:
        q = self.quotas.get(quota_id)
        if not q:
            return None
        for key, value in updates.items():
            if hasattr(q, key) and key not in ("id", "created_at"):
                setattr(q, key, value)
        q.updated_at = datetime.utcnow()
        self.quotas[quota_id] = q
        self._save_data()
        return q

    def delete_quota(self, quota_id: str) -> bool:
        if quota_id in self.quotas:
            del self.quotas[quota_id]
            self.usages = {k: v for k, v in self.usages.items() if v.quota_id != quota_id}
            self.alerts = {k: v for k, v in self.alerts.items() if v.quota_id != quota_id}
            self._save_data()
            return True
        return False

    def check_quota(self, quota_id: str, amount: float = 1.0) -> Dict[str, Any]:
        q = self.quotas.get(quota_id)
        if not q:
            return {"allowed": False, "reason": "Quota not found"}
        usage = next((u for u in self.usages.values() if u.quota_id == quota_id), None)
        current = usage.current_usage if usage else 0.0
        effective_limit = q.hard_limit
        for o in self.overrides.values():
            if o.quota_id == quota_id and (o.expires_at is None or o.expires_at > datetime.utcnow()):
                if o.new_hard_limit is not None:
                    effective_limit = o.new_hard_limit
        projected = current + amount
        if projected > effective_limit:
            self._create_alert(quota_id, projected, effective_limit, f"Quota {q.name} exceeded: {projected}/{effective_limit} {q.unit}")
            return {"allowed": False, "reason": f"Quota limit exceeded: {projected} > {effective_limit}", "current": current, "requested": amount, "limit": effective_limit, "action": q.action_on_exceed.value}
        if q.soft_limit and projected > q.soft_limit:
            return {"allowed": True, "warning": f"Soft limit exceeded: {projected} > {q.soft_limit}", "current": current, "requested": amount, "soft_limit": q.soft_limit, "hard_limit": effective_limit, "action": "warn"}
        usage_pct = (projected / effective_limit) * 100 if effective_limit > 0 else 0
        if usage_pct >= q.warning_threshold:
            self._create_alert(quota_id, projected, effective_limit, f"Quota {q.name} at {usage_pct:.1f}% of limit")
        return {"allowed": True, "current": current, "requested": amount, "limit": effective_limit, "usage_percentage": usage_pct}

    def record_usage(self, quota_id: str, amount: float) -> Optional[QuotaUsage]:
        usage = next((u for u in self.usages.values() if u.quota_id == quota_id), None)
        if not usage:
            return None
        usage.current_usage += amount
        usage.peak_usage = max(usage.peak_usage, usage.current_usage)
        usage.last_updated = datetime.utcnow()
        usage.usage_history.append({"timestamp": datetime.utcnow().isoformat(), "amount": amount, "total": usage.current_usage})
        if len(usage.usage_history) > 1000:
            usage.usage_history = usage.usage_history[-1000:]
        self._save_data()
        return usage

    def reset_usage(self, quota_id: str) -> bool:
        usage = next((u for u in self.usages.values() if u.quota_id == quota_id), None)
        if not usage:
            return False
        usage.current_usage = 0.0
        usage.peak_usage = 0.0
        usage.last_updated = datetime.utcnow()
        self._save_data()
        return True

    def create_reservation(self, name: str, resource_type: QuotaResourceType, amount: float, scope: QuotaScope, scope_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, created_by: Optional[str] = None, priority: int = 0, notes: Optional[str] = None) -> ResourceReservation:
        r = ResourceReservation(id=str(uuid.uuid4()), name=name, resource_type=resource_type, amount=amount, scope=scope, scope_id=scope_id, start_time=start_time or datetime.utcnow(), end_time=end_time, created_by=created_by, priority=priority, notes=notes)
        self.reservations[r.id] = r
        self._save_data()
        return r

    def cancel_reservation(self, reservation_id: str) -> bool:
        r = self.reservations.get(reservation_id)
        if not r:
            return False
        r.status = ReservationStatus.CANCELLED
        self._save_data()
        return True

    def get_quotas_by_scope(self, scope: QuotaScope, scope_id: str) -> List[QuotaDefinition]:
        return [q for q in self.quotas.values() if q.scope == scope and q.scope_id == scope_id]

    def get_quota_usage(self, quota_id: str) -> Optional[QuotaUsage]:
        return next((u for u in self.usages.values() if u.quota_id == quota_id), None)

    def create_override(self, quota_id: str, new_hard_limit: Optional[float] = None, new_soft_limit: Optional[float] = None, reason: str = "", expires_in_hours: Optional[int] = None, created_by: str = "") -> Optional[QuotaOverride]:
        q = self.quotas.get(quota_id)
        if not q:
            return None
        o = QuotaOverride(id=str(uuid.uuid4()), quota_id=quota_id, new_hard_limit=new_hard_limit, new_soft_limit=new_soft_limit, reason=reason, expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None, created_by=created_by)
        self.overrides[o.id] = o
        self._save_data()
        return o

    def get_alerts(self, quota_id: Optional[str] = None, acknowledged: Optional[bool] = None) -> List[QuotaAlert]:
        results = list(self.alerts.values())
        if quota_id:
            results = [a for a in results if a.quota_id == quota_id]
        if acknowledged is not None:
            results = [a for a in results if a.acknowledged == acknowledged]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        self._save_data()
        return True

    def _create_alert(self, quota_id: str, usage: float, threshold: float, message: str) -> QuotaAlert:
        alert = QuotaAlert(id=str(uuid.uuid4()), quota_id=quota_id, usage=usage, threshold=threshold, message=message, severity="critical" if usage >= threshold else "warning")
        self.alerts[alert.id] = alert
        self._save_data()
        return alert

    def get_usage_summary(self, scope: Optional[QuotaScope] = None, scope_id: Optional[str] = None) -> Dict[str, Any]:
        target_quotas = list(self.quotas.values())
        if scope and scope_id:
            target_quotas = [q for q in target_quotas if q.scope == scope and q.scope_id == scope_id]
        total_usage = {}
        for q in target_quotas:
            usage = next((u for u in self.usages.values() if u.quota_id == q.id), None)
            if usage:
                pct = (usage.current_usage / q.hard_limit * 100) if q.hard_limit > 0 else 0
                total_usage[q.resource_type.value] = {"limit": q.hard_limit, "current": usage.current_usage, "peak": usage.peak_usage, "percentage": round(pct, 2), "unit": q.unit, "quota_name": q.name}
        return {"scope": scope.value if scope else "all", "scope_id": scope_id or "all", "quota_count": len(target_quotas), "usage": total_usage}

    def get_statistics(self) -> Dict[str, Any]:
        total_quotas = len(self.quotas)
        total_reservations = len(self.reservations)
        active_reservations = sum(1 for r in self.reservations.values() if r.status == ReservationStatus.ACTIVE)
        total_alerts = len(self.alerts)
        unacknowledged_alerts = sum(1 for a in self.alerts.values() if not a.acknowledged)
        total_overrides = len(self.overrides)
        quotas_near_limit = 0
        for q in self.quotas.values():
            usage = next((u for u in self.usages.values() if u.quota_id == q.id), None)
            if usage and q.hard_limit > 0 and (usage.current_usage / q.hard_limit * 100) >= 80:
                quotas_near_limit += 1
        return {"total_quotas": total_quotas, "total_reservations": total_reservations, "active_reservations": active_reservations, "total_alerts": total_alerts, "unacknowledged_alerts": unacknowledged_alerts, "total_overrides": total_overrides, "quotas_near_limit": quotas_near_limit}

    def get_quota_utilization(self, quota_id: str) -> Dict[str, Any]:
        q = self.quotas.get(quota_id)
        usage = next((u for u in self.usages.values() if u.quota_id == quota_id), None)
        if not q or not usage:
            return {"error": "Quota or usage not found"}
        utilization_pct = (usage.current_usage / q.hard_limit * 100) if q.hard_limit > 0 else 0
        return {"quota_name": q.name, "resource_type": q.resource_type.value, "hard_limit": q.hard_limit, "soft_limit": q.soft_limit, "current_usage": usage.current_usage, "peak_usage": usage.peak_usage, "utilization_percentage": round(utilization_pct, 2), "remaining": max(0, q.hard_limit - usage.current_usage), "unit": q.unit, "scope": q.scope.value, "scope_id": q.scope_id}

    def list_quotas(self, resource_type: Optional[QuotaResourceType] = None, scope: Optional[QuotaScope] = None) -> List[QuotaDefinition]:
        results = list(self.quotas.values())
        if resource_type:
            results = [q for q in results if q.resource_type == resource_type]
        if scope:
            results = [q for q in results if q.scope == scope]
        return results
