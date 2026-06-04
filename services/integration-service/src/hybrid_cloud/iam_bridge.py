import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"


class SyncDirection(Enum):
    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"


class RoleDefinition:
    def __init__(self, name: str, description: str, provider: CloudProvider,
                 policies: List[str], trust_policy: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.provider = provider
        self.policies = policies
        self.trust_policy = trust_policy or {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "description": self.description,
                "provider": self.provider.value, "policies": self.policies,
                "trust_policy": self.trust_policy, "created_at": self.created_at.isoformat()}


class PolicyDocument:
    def __init__(self, name: str, statements: List[Dict[str, Any]],
                 version: str = "2012-10-17"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.statements = statements
        self.version = version
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "statements": self.statements,
                "version": self.version, "created_at": self.created_at.isoformat()}


class BridgeMapping:
    def __init__(self, source_role: str, source_provider: CloudProvider,
                 target_role: str, target_provider: CloudProvider):
        self.id = str(uuid.uuid4())
        self.source_role = source_role
        self.source_provider = source_provider
        self.target_role = target_role
        self.target_provider = target_provider
        self.last_synced: Optional[datetime] = None
        self.sync_direction = SyncDirection.BIDIRECTIONAL
        self.active = True

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "source_role": self.source_role,
                "source_provider": self.source_provider.value,
                "target_role": self.target_role,
                "target_provider": self.target_provider.value,
                "last_synced": self.last_synced.isoformat() if self.last_synced else None,
                "sync_direction": self.sync_direction.value, "active": self.active}


class IAMBridge:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sync_interval = config.get("sync_interval", 300)
        self.auto_remediate = config.get("auto_remediate", False)
        self.default_policy_version = config.get("default_policy_version", "2012-10-17")
        self.conflict_resolution = config.get("conflict_resolution", "source_wins")
        self._roles: Dict[str, RoleDefinition] = {}
        self._policies: Dict[str, PolicyDocument] = {}
        self._mappings: Dict[str, BridgeMapping] = {}
        self._sync_history: List[Dict[str, Any]] = []
        self._provider_credentials: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        for provider in CloudProvider:
            creds = self.config.get(provider.value, {})
            if creds:
                self._provider_credentials[provider.value] = creds
        self._initialized = True
        logger.info(f"IAMBridge initialized with {len(self._provider_credentials)} providers")

    async def close(self) -> None:
        self._roles.clear()
        self._policies.clear()
        self._mappings.clear()
        logger.info("IAMBridge closed")

    def create_role(self, name: str, description: str,
                    provider: CloudProvider, policies: Optional[List[str]] = None,
                    trust_policy: Optional[Dict[str, Any]] = None) -> RoleDefinition:
        role = RoleDefinition(name, description, provider, policies or [], trust_policy)
        self._roles[role.id] = role
        return role

    def get_role(self, role_id: str) -> Optional[RoleDefinition]:
        return self._roles.get(role_id)

    def list_roles(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        if provider:
            return [r.to_dict() for r in self._roles.values() if r.provider.value == provider]
        return [r.to_dict() for r in self._roles.values()]

    def delete_role(self, role_id: str) -> bool:
        if role_id in self._roles:
            del self._roles[role_id]
            return True
        return False

    def create_policy(self, name: str, statements: List[Dict[str, Any]]) -> PolicyDocument:
        policy = PolicyDocument(name, statements, self.default_policy_version)
        self._policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Optional[PolicyDocument]:
        return self._policies.get(policy_id)

    def list_policies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._policies.values()]

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def compile_to_aws(self, policy: PolicyDocument) -> Dict[str, Any]:
        return {"PolicyName": policy.name, "PolicyDocument": {
            "Version": policy.version,
            "Statement": policy.statements
        }}

    def compile_to_azure(self, policy: PolicyDocument) -> Dict[str, Any]:
        actions = []
        for stmt in policy.statements:
            if isinstance(stmt.get("Action"), list):
                actions.extend(stmt["Action"])
        return {"roleName": policy.name, "type": "CustomRole",
                "assignableScopes": ["/"],
                "permissions": [{"actions": actions, "notActions": []}]}

    def compile_to_gcp(self, policy: PolicyDocument) -> Dict[str, Any]:
        return {"name": f"projects/_/roles/{policy.name}",
                "title": policy.name, "includedPermissions": policy.statements[0].get("Action", [])}

    def create_mapping(self, source_role: str, source_provider: CloudProvider,
                       target_role: str, target_provider: CloudProvider) -> BridgeMapping:
        mapping = BridgeMapping(source_role, source_provider, target_role, target_provider)
        self._mappings[mapping.id] = mapping
        return mapping

    def get_mapping(self, mapping_id: str) -> Optional[BridgeMapping]:
        return self._mappings.get(mapping_id)

    def list_mappings(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._mappings.values()]

    def delete_mapping(self, mapping_id: str) -> bool:
        if mapping_id in self._mappings:
            del self._mappings[mapping_id]
            return True
        return False

    async def sync_mapping(self, mapping_id: str) -> Dict[str, Any]:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return {"status": "error", "message": "Mapping not found"}
        mapping.last_synced = datetime.utcnow()
        log_entry = {"mapping_id": mapping_id, "source_role": mapping.source_role,
                     "target_role": mapping.target_role, "synced_at": mapping.last_synced.isoformat(),
                     "direction": mapping.sync_direction.value, "status": "success"}
        self._sync_history.append(log_entry)
        return log_entry

    async def sync_all(self) -> List[Dict[str, Any]]:
        results = []
        for mid in list(self._mappings.keys()):
            result = await self.sync_mapping(mid)
            results.append(result)
        logger.info(f"Synced {len(results)} mappings")
        return results

    def get_sync_history(self) -> List[Dict[str, Any]]:
        return self._sync_history

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_roles": len(self._roles),
                "total_policies": len(self._policies),
                "total_mappings": len(self._mappings),
                "providers_connected": list(self._provider_credentials.keys()),
                "last_sync": self._sync_history[-1]["synced_at"] if self._sync_history else None}

    def add_role(self, role_name: str, provider: CloudProvider,
                  permissions: List[str]) -> Role:
        role = Role(role_name, provider, permissions)
        self._roles[role.id] = role
        return role

    def delete_role(self, role_id: str) -> bool:
        if role_id in self._roles:
            del self._roles[role_id]
            return True
        return False

    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        role = self._roles.get(role_id)
        return role.to_dict() if role else None

    def list_roles(self, provider: Optional[CloudProvider] = None) -> List[Dict[str, Any]]:
        if provider:
            return [r.to_dict() for r in self._roles.values() if r.provider == provider]
        return [r.to_dict() for r in self._roles.values()]

    def add_policy(self, name: str, statements: List[Dict[str, Any]],
                    provider: CloudProvider) -> PolicyDocument:
        policy = PolicyDocument(name, statements, provider)
        self._policies[policy.id] = policy
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        policy = self._policies.get(policy_id)
        return policy.to_dict() if policy else None

    def list_policies(self, provider: Optional[CloudProvider] = None) -> List[Dict[str, Any]]:
        if provider:
            return [p.to_dict() for p in self._policies.values() if p.provider == provider]
        return [p.to_dict() for p in self._policies.values()]

    def test_mapping(self, source_role: str, source_provider: CloudProvider,
                      target_provider: CloudProvider) -> Dict[str, Any]:
        compatible = False
        for m in self._mappings.values():
            if m.source_role == source_role and m.source_provider == source_provider:
                compatible = True
                break
        return {"source_role": source_role, "source_provider": source_provider.value,
                "target_provider": target_provider.value, "compatible": compatible}

    def create_access_review(self, role_id: str, reviewer: str) -> Dict[str, Any]:
        review_id = f"review-{uuid.uuid4().hex[:8]}"
        review = {"id": review_id, "role_id": role_id, "reviewer": reviewer,
                  "status": "pending", "created_at": datetime.utcnow().isoformat()}
        if "access_reviews" not in self.config:
            self.config["access_reviews"] = []
        self.config["access_reviews"].append(review)
        return review

    def get_access_reviews(self) -> List[Dict[str, Any]]:
        return self.config.get("access_reviews", [])

    def complete_access_review(self, review_id: str, approved: bool) -> bool:
        reviews = self.config.get("access_reviews", [])
        for r in reviews:
            if r.get("id") == review_id:
                r["status"] = "approved" if approved else "denied"
                r["completed_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def export_policies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._policies.values()]

    def export_roles_and_mappings(self) -> Dict[str, Any]:
        return {"roles": [r.to_dict() for r in self._roles.values()],
                "mappings": [m.to_dict() for m in self._mappings.values()],
                "exported_at": datetime.utcnow().isoformat()}

    def assess_policy_compliance(self, policy_id: str, framework: str = "soc2") -> Dict[str, Any]:
        policy = self._policies.get(policy_id)
        if not policy:
            return {"status": "error", "message": "Policy not found"}
        compliant = len(policy.statements) > 0
        return {"policy_id": policy_id, "policy_name": policy.name,
                "framework": framework, "compliant": compliant,
                "issues": [] if compliant else ["No statements defined"],
                "score": 100 if compliant else 0}

    def get_role_usage(self, role_id: str) -> Dict[str, Any]:
        role = self._roles.get(role_id)
        if not role:
            return {"status": "error", "message": "Role not found"}
        mappings_count = sum(1 for m in self._mappings.values() if m.source_role == role.name)
        return {"role_id": role_id, "role_name": role.name,
                "provider": role.provider.value,
                "permission_count": len(role.permissions),
                "mappings_count": mappings_count,
                "synced": role.synced}

    def batch_create_roles(self, roles: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for r in roles:
            role = self.create_role(r.get("name", "unnamed"), r.get("description", ""),
                                     CloudProvider(r.get("provider", "aws")),
                                     r.get("policies"), r.get("trust_policy"))
            ids.append(role.id)
        return ids

    def batch_create_mappings(self, mappings: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for m in mappings:
            mapping = self.create_mapping(m["source_role"], CloudProvider(m["source_provider"]),
                                           m["target_role"], CloudProvider(m["target_provider"]))
            ids.append(mapping.id)
        return ids

    def translate_policy_across_providers(self, policy_id: str, target_provider: CloudProvider) -> Dict[str, Any]:
        policy = self._policies.get(policy_id)
        if not policy:
            return {"status": "error", "message": "Policy not found"}
        if target_provider == CloudProvider.AWS:
            return self.compile_to_aws(policy)
        elif target_provider == CloudProvider.AZURE:
            return self.compile_to_azure(policy)
        elif target_provider == CloudProvider.GCP:
            return self.compile_to_gcp(policy)
        return {"status": "error", "message": "Unsupported provider"}

    def set_sync_direction(self, mapping_id: str, direction: SyncDirection) -> bool:
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return False
        mapping.sync_direction = direction
        return True

    def get_provider_count(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self._roles.values():
            counts[r.provider.value] = counts.get(r.provider.value, 0) + 1
        return counts

# ── New Data Models ──────────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class IdentityProviderConfig:
    provider: CloudProvider
    issuer_url: str
    client_id: str
    scopes: List[str] = field(default_factory=lambda: ["openid", "profile", "email"])
    enabled: bool = True

@dataclass
class PermissionAuditEntry:
    role_id: str
    role_name: str
    action: str
    resource: str
    effect: PolicyEffect
    audited_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FederationTrust:
    trust_id: str
    source_provider: CloudProvider
    target_provider: CloudProvider
    trust_type: str = "cross_account"
    active: bool = True

# ── Batch Operations ────────────────────────────────────────────────

    async def batch_sync_mappings(self, mapping_ids: List[str]) -> Dict[str, Any]:
        results = {}
        for mid in mapping_ids:
            r = await self.sync_mapping(mid)
            results[mid] = r
        return {"results": results, "total": len(mapping_ids)}

    async def batch_delete_roles(self, role_ids: List[str]) -> Dict[str, Any]:
        deleted = 0; not_found = 0
        for rid in role_ids:
            if self.delete_role(rid):
                deleted += 1
            else:
                not_found += 1
        return {"deleted": deleted, "not_found": not_found, "total": len(role_ids)}

    async def batch_create_policies(self, policies: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for p in policies:
            pol = self.create_policy(p.get("name", "unnamed"), p.get("statements", []))
            ids.append(pol.id)
        return ids

# ── Pagination / Sorting ─────────────────────────────────────────────

    def paginate_roles(self, page: int = 1, page_size: int = 20,
                        sort_by: str = "created_at", sort_desc: bool = True,
                        provider_filter: Optional[str] = None) -> Dict[str, Any]:
        items = list(self._roles.values())
        if provider_filter:
            items = [r for r in items if r.provider.value == provider_filter]
        items.sort(key=lambda r: getattr(r, sort_by, datetime.min), reverse=sort_desc)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": [r.to_dict() for r in items[start:start + page_size]],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def paginate_sync_history(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        items = sorted(self._sync_history, key=lambda h: h.get("synced_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

# ── Export / Import ──────────────────────────────────────────────────

    def export_iam_state(self) -> str:
        return json.dumps({
            "roles": [r.to_dict() for r in self._roles.values()],
            "policies": [p.to_dict() for p in self._policies.values()],
            "mappings": [m.to_dict() for m in self._mappings.values()],
            "exported_at": datetime.utcnow().isoformat(),
        }, indent=2)

    def import_iam_state(self, json_str: str) -> Dict[str, Any]:
        data = json.loads(json_str)
        imported = {"roles": 0, "policies": 0, "mappings": 0}
        for r in data.get("roles", []):
            try:
                self.create_role(r["name"], r.get("description", ""), CloudProvider(r["provider"]), r.get("policies", []), r.get("trust_policy"))
                imported["roles"] += 1
            except (ValueError, KeyError):
                continue
        for p in data.get("policies", []):
            try:
                self.create_policy(p["name"], p.get("statements", []))
                imported["policies"] += 1
            except (ValueError, KeyError):
                continue
        for m in data.get("mappings", []):
            try:
                self.create_mapping(m["source_role"], CloudProvider(m["source_provider"]), m["target_role"], CloudProvider(m["target_provider"]))
                imported["mappings"] += 1
            except (ValueError, KeyError):
                continue
        return imported

# ── Complex Analytic Queries ─────────────────────────────────────────

    def get_permission_coverage_analysis(self) -> Dict[str, Any]:
        all_perms: Set[str] = set()
        mapped_perms: Set[str] = set()
        for r in self._roles.values():
            for p in r.policies:
                all_perms.add(p)
        for m in self._mappings.values():
            source_role = next((r for r in self._roles.values() if r.name == m.source_role), None)
            if source_role:
                for p in source_role.policies:
                    mapped_perms.add(p)
        return {
            "total_permissions": len(all_perms),
            "mapped_permissions": len(mapped_perms),
            "unmapped_permissions": len(all_perms - mapped_perms),
            "coverage_pct": round(len(mapped_perms) / max(len(all_perms), 1) * 100, 1),
        }

    def get_cross_provider_role_equivalence(self) -> Dict[str, Any]:
        equivalents = []
        for m in self._mappings.values():
            equivalents.append({
                "source": f"{m.source_provider.value}:{m.source_role}",
                "target": f"{m.target_provider.value}:{m.target_role}",
                "direction": m.sync_direction.value, "active": m.active,
            })
        return {"equivalences": equivalents, "total": len(equivalents)}

    def get_provider_trust_analytics(self) -> Dict[str, Any]:
        by_provider: Dict[str, int] = {}
        for m in self._mappings.values():
            by_provider[m.source_provider.value] = by_provider.get(m.source_provider.value, 0) + 1
        return {"trust_relationships": by_provider, "total": len(self._mappings)}

# ── State Machine / Workflow ─────────────────────────────────────────

    async def role_lifecycle_workflow(self, role_id: str, action: str) -> Dict[str, Any]:
        role = self._roles.get(role_id)
        if not role:
            return {"status": "error", "message": "Role not found"}
        if action == "sync":
            related_mappings = [m for m in self._mappings.values() if m.source_role == role.name]
            results = []
            for m in related_mappings:
                r = await self.sync_mapping(m.id)
                results.append(r)
            return {"action": "sync", "role_id": role_id, "mappings_synced": len(results)}
        elif action == "audit":
            return {"action": "audit", "role_id": role_id, "role_name": role.name,
                    "policy_count": len(role.policies), "provider": role.provider.value}
        elif action == "delete":
            self.delete_role(role_id)
            return {"action": "delete", "role_id": role_id, "status": "deleted"}
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def scheduled_sync_workflow(self) -> Dict[str, Any]:
        synced = 0; failed = 0
        for mid in list(self._mappings.keys()):
            try:
                await self.sync_mapping(mid)
                synced += 1
            except Exception:
                failed += 1
        return {"mappings_synced": synced, "failed": failed}

# ── Configuration Validation ─────────────────────────────────────────

    def validate_iam_config(self) -> Dict[str, Any]:
        errors = []; warnings = []
        if self.sync_interval < 60:
            warnings.append("sync_interval is very low (< 60s)")
        if not self._provider_credentials:
            errors.append("No provider credentials configured")
        if self.auto_remediate and not self.config.get("remediation_plan"):
            warnings.append("auto_remediate enabled but no remediation_plan configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                "provider_count": len(self._provider_credentials)}

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
