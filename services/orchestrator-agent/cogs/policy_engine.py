import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PolicySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    AUDIT = "audit"
    REQUIRE_MFA = "require_mfa"

class EvaluationResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    NOT_APPLICABLE = "na"

DATA_FILE = "data/policies.json"

BUILTIN_POLICIES = [
    {"policy_id": "deny_root_ssh", "name": "Deny Root SSH Access",
     "description": "Deny SSH access for root user", "category": "security",
     "severity": PolicySeverity.HIGH.value, "effect": PolicyEffect.DENY.value,
     "rego": 'deny { input.action == "ssh"; input.user == "root" }',
     "rules": [{"resource_pattern": "server:*", "action": "ssh", "conditions": [
         {"field": "user", "operator": "eq", "value": "root"}]}]},
    {"policy_id": "require_mfa_admin", "name": "Require MFA for Admin Actions",
     "description": "Multi-factor authentication required for admin operations",
     "category": "security", "severity": PolicySeverity.CRITICAL.value,
     "effect": PolicyEffect.REQUIRE_MFA.value,
     "rego": 'require_mfa { input.role == "admin"; input.action == "delete" }',
     "rules": [{"resource_pattern": "*", "action": "delete", "conditions": [
         {"field": "role", "operator": "eq", "value": "admin"}]}]},
    {"policy_id": "data_classification", "name": "Data Classification Enforcement",
     "description": "Enforce data handling based on classification level",
     "category": "compliance", "severity": PolicySeverity.HIGH.value,
     "effect": PolicyEffect.AUDIT.value,
     "rego": 'audit { input.data_classification == "restricted" }',
     "rules": [{"resource_pattern": "data:*", "action": "read", "conditions": [
         {"field": "data_classification", "operator": "eq", "value": "restricted"}]}]},
    {"policy_id": "network_segmentation", "name": "Network Segmentation Policy",
     "description": "Enforce network isolation between environments",
     "category": "network", "severity": PolicySeverity.HIGH.value,
     "effect": PolicyEffect.DENY.value,
     "rego": 'deny { input.source_env != input.target_env; input.protocol == "ssh" }',
     "rules": [{"resource_pattern": "network:segment:*", "action": "connect", "conditions": [
         {"field": "source_env", "operator": "neq", "value": "target_env"}]}]},
    {"policy_id": "backup_compliance", "name": "Backup Compliance Policy",
     "description": "All production resources must have backups enabled",
     "category": "compliance", "severity": PolicySeverity.MEDIUM.value,
     "effect": PolicyEffect.WARN.value,
     "rego": 'warn { input.env == "production"; not input.backup_enabled }',
     "rules": [{"resource_pattern": "server:production:*", "action": "deploy", "conditions": [
         {"field": "backup_enabled", "operator": "eq", "value": False}]}]},
    {"policy_id": "cost_governance", "name": "Cost Governance Policy",
     "description": "Prevent deployment of oversized resources",
     "category": "governance", "severity": PolicySeverity.MEDIUM.value,
     "effect": PolicyEffect.DENY.value,
     "rego": 'deny { input.resource_type == "server"; input.cpu > 16 }',
     "rules": [{"resource_pattern": "compute:*", "action": "create", "conditions": [
         {"field": "cpu", "operator": "gt", "value": 16}]}]},
    {"policy_id": "geo_restriction", "name": "Geographic Restriction Policy",
     "description": "Restrict access from specific geographic regions",
     "category": "security", "severity": PolicySeverity.HIGH.value,
     "effect": PolicyEffect.DENY.value,
     "rego": 'deny { input.geo_region in ["restricted_region_a", "restricted_region_b"] }',
     "rules": [{"resource_pattern": "api:*", "action": "access", "conditions": [
         {"field": "geo_region", "operator": "in", "value": ["restricted_region_a", "restricted_region_b"]}]}]},
    {"policy_id": "encryption_required", "name": "Encryption Required Policy",
     "description": "All data at rest and in transit must be encrypted",
     "category": "security", "severity": PolicySeverity.CRITICAL.value,
     "effect": PolicyEffect.DENY.value,
     "rego": 'deny { input.encryption_at_rest != true }',
     "rules": [{"resource_pattern": "storage:*", "action": "create", "conditions": [
         {"field": "encryption_at_rest", "operator": "eq", "value": False}]}]},
]


class PolicyRule:
    def __init__(self, rule_id: str, policy_id: str, resource_pattern: str,
                 action: str, conditions: List[Dict[str, Any]],
                 effect: str = "deny"):
        self.rule_id = rule_id
        self.policy_id = policy_id
        self.resource_pattern = resource_pattern
        self.action = action
        self.conditions = conditions
        self.effect = effect

    def to_dict(self) -> Dict[str, Any]:
        return {"rule_id": self.rule_id, "policy_id": self.policy_id,
                "resource_pattern": self.resource_pattern, "action": self.action,
                "conditions": self.conditions, "effect": self.effect}


class Policy:
    def __init__(self, policy_id: str, name: str, description: str,
                 category: str = "general",
                 severity: str = "medium", effect: str = "deny"):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.category = category
        self.severity = PolicySeverity(severity)
        self.effect = PolicyEffect(effect)
        self.enabled = True
        self.rules: List[PolicyRule] = []
        self.rego = ""
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.version = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "name": self.name,
                "description": self.description, "category": self.category,
                "severity": self.severity.value, "effect": self.effect.value,
                "enabled": self.enabled, "rules": [r.to_dict() for r in self.rules],
                "rego": self.rego, "created_at": self.created_at,
                "updated_at": self.updated_at, "version": self.version}


class PolicyEngine:
    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._evaluation_log: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self):
        for bp in BUILTIN_POLICIES:
            policy = Policy(bp["policy_id"], bp["name"], bp["description"],
                            bp.get("category", "general"), bp["severity"], bp["effect"])
            policy.rego = bp.get("rego", "")
            for r in bp.get("rules", []):
                rule = PolicyRule(uuid.uuid4().hex[:12], bp["policy_id"],
                                  r["resource_pattern"], r["action"],
                                  r.get("conditions", []), r.get("effect", "deny"))
                policy.rules.append(rule)
            self._policies[bp["policy_id"]] = policy
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"policies": [], "evaluation_log": []}
        for p in data.get("policies", []):
            policy = Policy(p["policy_id"], p["name"], p["description"],
                            p.get("category", "general"), p.get("severity", "medium"),
                            p.get("effect", "deny"))
            policy.enabled = p.get("enabled", True)
            policy.rego = p.get("rego", "")
            policy.created_at = p.get("created_at", policy.created_at)
            policy.updated_at = p.get("updated_at", policy.updated_at)
            policy.version = p.get("version", 1)
            for r in p.get("rules", []):
                rule = PolicyRule(r.get("rule_id", uuid.uuid4().hex[:12]),
                                  p["policy_id"], r["resource_pattern"],
                                  r["action"], r.get("conditions", []),
                                  r.get("effect", "deny"))
                policy.rules.append(rule)
            if p["policy_id"] not in self._policies:
                self._policies[p["policy_id"]] = policy
        self._evaluation_log = data.get("evaluation_log", [])
        self._initialized = True
        logger.info(f"PolicyEngine initialized with {len(self._policies)} policies")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"policies": [p.to_dict() for p in self._policies.values()],
                "evaluation_log": self._evaluation_log[-500:]}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def list_policies(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        policies = self._policies.values()
        if category:
            policies = [p for p in policies if p.category == category]
        return [p.to_dict() for p in policies]

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        p = self._policies.get(policy_id)
        return p.to_dict() if p else None

    def create_policy(self, name: str, description: str, category: str = "general",
                      severity: str = "medium", effect: str = "deny") -> Dict[str, Any]:
        pid = uuid.uuid4().hex[:16]
        policy = Policy(pid, name, description, category, severity, effect)
        self._policies[pid] = policy
        return policy.to_dict()

    def add_rule(self, policy_id: str, resource_pattern: str, action: str,
                 conditions: List[Dict[str, Any]], effect: str = "deny") -> bool:
        p = self._policies.get(policy_id)
        if not p:
            return False
        rule = PolicyRule(uuid.uuid4().hex[:12], policy_id, resource_pattern,
                          action, conditions, effect)
        p.rules.append(rule)
        p.updated_at = datetime.utcnow().isoformat()
        p.version += 1
        return True

    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        p = self._policies.get(policy_id)
        if not p:
            return False
        if "name" in updates: p.name = updates["name"]
        if "description" in updates: p.description = updates["description"]
        if "category" in updates: p.category = updates["category"]
        if "severity" in updates: p.severity = PolicySeverity(updates["severity"])
        if "effect" in updates: p.effect = PolicyEffect(updates["effect"])
        if "enabled" in updates: p.enabled = updates["enabled"]
        p.updated_at = datetime.utcnow().isoformat()
        p.version += 1
        return True

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def evaluate(self, resource: str, action: str,
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {"resource": resource, "action": action, "context": context or {},
                  "decisions": [], "overall": "allow",
                  "timestamp": datetime.utcnow().isoformat()}
        ctx = context or {}
        for p in self._policies.values():
            if not p.enabled:
                continue
            for rule in p.rules:
                matched = True
                for cond in rule.conditions:
                    field_val = ctx.get(cond["field"])
                    op = cond.get("operator", "eq")
                    target = cond.get("value")
                    if op == "eq" and field_val != target:
                        matched = False
                    elif op == "neq" and field_val == target:
                        matched = False
                    elif op == "gt" and (field_val is None or not (field_val > target)):
                        matched = False
                    elif op == "lt" and (field_val is None or not (field_val < target)):
                        matched = False
                    elif op == "in" and (field_val not in target):
                        matched = False
                if matched and rule.action == action:
                    result["decisions"].append({
                        "policy_id": p.policy_id, "rule_effect": rule.effect,
                        "policy_effect": p.effect.value, "policy_name": p.name,
                        "severity": p.severity.value,
                    })
                    if rule.effect in ("deny", "require_mfa"):
                        result["overall"] = "deny"
                    elif rule.effect == "audit":
                        pass
        self._evaluation_log.append(result)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_policies": len(self._policies),
                "enabled_policies": sum(1 for p in self._policies.values() if p.enabled),
                "total_rules": sum(len(p.rules) for p in self._policies.values()),
                "evaluations_logged": len(self._evaluation_log),
                "categories": list(set(p.category for p in self._policies.values()))}
