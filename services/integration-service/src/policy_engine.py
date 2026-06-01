import json
import uuid
import hashlib
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class RegoRuntime:
    def __init__(self):
        self._builtins = {
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "eq": lambda a, b: a == b,
            "neq": lambda a, b: a != b,
            "contains": lambda s, sub: sub in s if isinstance(s, str) else False,
            "startswith": lambda s, prefix: s.startswith(prefix) if isinstance(s, str) else False,
            "endswith": lambda s, suffix: s.endswith(suffix) if isinstance(s, str) else False,
            "regex_match": lambda pattern, s: bool(re.match(pattern, str(s))) if s else False,
            "glob_match": lambda pattern, s: __import__("fnmatch").fnmatch(str(s), pattern) if s else False,
            "len": len,
            "lower": lambda s: s.lower() if isinstance(s, str) else s,
            "upper": lambda s: s.upper() if isinstance(s, str) else s,
            "split": lambda s, sep: s.split(sep) if isinstance(s, str) else [],
            "join": lambda arr, sep: sep.join(arr) if isinstance(arr, list) else "",
        }

    def evaluate_rule(self, rule: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        rule_type = rule.get("type", "allow")
        conditions = rule.get("conditions", [])
        result = True
        for cond in conditions:
            field_value = self._get_nested(input_data, cond.get("field", ""))
            operator = cond.get("operator", "eq")
            expected = cond.get("value")
            if operator == "in":
                if not isinstance(expected, list):
                    expected = [expected]
                result = result and (field_value in expected)
            elif operator == "contains":
                result = result and (expected in field_value if isinstance(field_value, (str, list)) else False)
            elif operator == "regex":
                result = result and bool(re.match(str(expected), str(field_value))) if field_value else False
            else:
                fn = self._builtins.get(operator)
                if fn:
                    try:
                        result = result and fn(field_value, expected)
                    except Exception:
                        result = False
            if not result and rule.get("combinator", "all") == "all":
                break
        return result

    def _get_nested(self, data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current


@dataclass
class Policy:
    policy_id: str
    name: str
    description: str
    package: str
    rules: List[Dict[str, Any]]
    enabled: bool
    version: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    source: str
    git_url: Optional[str]
    git_ref: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "rules_count": len(self.rules),
            "enabled": self.enabled,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source": self.source,
            "git_url": self.git_url,
            "git_ref": self.git_ref,
        }


@dataclass
class EvaluationResult:
    decision: str
    allowed: bool
    package: str
    matched_rules: List[Dict[str, Any]]
    denied_rules: List[Dict[str, Any]]
    input_data: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "allowed": self.allowed,
            "package": self.package,
            "matched_rules": [
                {"name": r.get("name", ""), "effect": r.get("effect", "allow")}
                for r in self.matched_rules
            ],
            "denied_rules": [
                {"name": r.get("name", ""), "reason": r.get("reason", "")}
                for r in self.denied_rules
            ],
            "timestamp": self.timestamp.isoformat(),
        }


class PolicyManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._policies: Dict[str, Policy] = {}
        self._packages: Dict[str, List[str]] = {}
        self._runtime = RegoRuntime()
        self._evaluation_history: List[EvaluationResult] = []
        self._git_sync_config = config.get("git_sync", {})
        self._initialized = False

    async def initialize(self) -> None:
        self._initialize_default_policies()
        self._initialized = True
        logger.info(f"PolicyManager initialized with {len(self._policies)} policies")

    async def close(self) -> None:
        self._policies.clear()
        self._packages.clear()
        self._evaluation_history.clear()
        logger.info("PolicyManager closed")

    def _initialize_default_policies(self) -> None:
        default_policies = [
            {
                "name": "Allow Health Check",
                "description": "Allow unauthenticated access to health endpoint",
                "package": "infra_pilot.auth.health",
                "rules": [
                    {
                        "name": "health_check_access",
                        "effect": "allow",
                        "type": "allow",
                        "combinator": "all",
                        "conditions": [
                            {"field": "method", "operator": "eq", "value": "GET"},
                            {"field": "path", "operator": "eq", "value": "/api/v1/health"},
                        ],
                    }
                ],
                "tags": ["auth", "system"],
                "enabled": True,
            },
            {
                "name": "RBAC Admin Access",
                "description": "Full access for admin users",
                "package": "infra_pilot.auth.rbac",
                "rules": [
                    {
                        "name": "admin_full_access",
                        "effect": "allow",
                        "type": "allow",
                        "combinator": "all",
                        "conditions": [
                            {"field": "user.role", "operator": "eq", "value": "admin"},
                        ],
                    }
                ],
                "tags": ["auth", "rbac"],
                "enabled": True,
            },
            {
                "name": "Resource Owner Access",
                "description": "Allow access to owned resources",
                "package": "infra_pilot.auth.rbac",
                "rules": [
                    {
                        "name": "owner_access",
                        "effect": "allow",
                        "type": "allow",
                        "combinator": "all",
                        "conditions": [
                            {"field": "resource.owner_id", "operator": "eq", "value": "{{user.id}}"},
                        ],
                    }
                ],
                "tags": ["auth", "rbac"],
                "enabled": True,
            },
            {
                "name": "Deny Production Mutations Without Approval",
                "description": "Require approval for mutations in production",
                "package": "infra_pilot.compliance.change_control",
                "rules": [
                    {
                        "name": "require_approval_prod",
                        "effect": "deny",
                        "type": "deny",
                        "combinator": "all",
                        "conditions": [
                            {"field": "environment", "operator": "eq", "value": "production"},
                            {"field": "method", "operator": "in", "value": ["POST", "PUT", "DELETE", "PATCH"]},
                            {"field": "request.approved", "operator": "neq", "value": True},
                        ],
                        "reason": "Mutations in production require prior approval",
                    }
                ],
                "tags": ["compliance", "change-control"],
                "enabled": True,
            },
            {
                "name": "Resource Quota Enforcement",
                "description": "Enforce CPU and memory quotas per project",
                "package": "infra_pilot.resources.quota",
                "rules": [
                    {
                        "name": "cpu_quota",
                        "effect": "deny",
                        "type": "deny",
                        "combinator": "all",
                        "conditions": [
                            {"field": "resource.type", "operator": "eq", "value": "container"},
                            {"field": "resource.spec.cpu", "operator": "gt", "value": "{{quota.cpu_limit}}"},
                        ],
                        "reason": "CPU request exceeds project quota",
                    },
                    {
                        "name": "memory_quota",
                        "effect": "deny",
                        "type": "deny",
                        "combinator": "all",
                        "conditions": [
                            {"field": "resource.type", "operator": "eq", "value": "container"},
                            {"field": "resource.spec.memory", "operator": "gt", "value": "{{quota.memory_limit}}"},
                        ],
                        "reason": "Memory request exceeds project quota",
                    },
                ],
                "tags": ["resources", "quota"],
                "enabled": True,
            },
            {
                "name": "Cost Control Policy",
                "description": "Prevent deploying expensive resources without budget approval",
                "package": "infra_pilot.cost.control",
                "rules": [
                    {
                        "name": "expensive_resource_approval",
                        "effect": "deny",
                        "type": "deny",
                        "combinator": "all",
                        "conditions": [
                            {"field": "resource.spec.cost_per_hour", "operator": "gt", "value": 10.0},
                            {"field": "request.budget_approved", "operator": "neq", "value": True},
                        ],
                        "reason": "Resource cost exceeds $10/hour without budget approval",
                    }
                ],
                "tags": ["cost", "compliance"],
                "enabled": True,
            },
        ]

        for policy_def in default_policies:
            policy_id = str(uuid.uuid4())
            policy = Policy(
                policy_id=policy_id,
                name=policy_def["name"],
                description=policy_def["description"],
                package=policy_def["package"],
                rules=policy_def["rules"],
                enabled=policy_def["enabled"],
                version=1,
                tags=policy_def["tags"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source="built-in",
                git_url=None,
                git_ref=None,
            )
            self._policies[policy_id] = policy
            if policy.package not in self._packages:
                self._packages[policy.package] = []
            self._packages[policy.package].append(policy_id)

    def create_policy(self, name: str, description: str, package: str,
                      rules: List[Dict[str, Any]], tags: Optional[List[str]] = None) -> Policy:
        policy_id = str(uuid.uuid4())
        now = datetime.utcnow()
        policy = Policy(
            policy_id=policy_id,
            name=name,
            description=description,
            package=package,
            rules=rules,
            enabled=True,
            version=1,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            source="api",
            git_url=None,
            git_ref=None,
        )
        self._policies[policy_id] = policy
        if package not in self._packages:
            self._packages[package] = []
        self._packages[package].append(policy_id)
        logger.info(f"Policy {policy_id} created: {name}")
        return policy

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self._policies.get(policy_id)

    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> Optional[Policy]:
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        for key, value in updates.items():
            if hasattr(policy, key) and key not in ("policy_id", "created_at", "version"):
                setattr(policy, key, value)
        policy.version += 1
        policy.updated_at = datetime.utcnow()
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        policy = self._policies.pop(policy_id, None)
        if not policy:
            return False
        package_policies = self._packages.get(policy.package, [])
        if policy_id in package_policies:
            package_policies.remove(policy_id)
        logger.info(f"Policy {policy_id} deleted")
        return True

    def list_policies(self, package: Optional[str] = None, enabled_only: bool = False,
                      tag: Optional[str] = None) -> List[Dict[str, Any]]:
        policies = list(self._policies.values())
        if package:
            policy_ids = self._packages.get(package, [])
            policies = [p for p in policies if p.policy_id in policy_ids]
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        if tag:
            policies = [p for p in policies if tag in p.tags]
        return [p.to_dict() for p in sorted(policies, key=lambda p: p.name)]

    def evaluate(self, package: str, input_data: Dict[str, Any]) -> EvaluationResult:
        policy_ids = self._packages.get(package, [])
        matched_rules = []
        denied_rules = []
        all_allowed = True

        for pid in policy_ids:
            policy = self._policies.get(pid)
            if not policy or not policy.enabled:
                continue
            for rule in policy.rules:
                try:
                    result = self._runtime.evaluate_rule(rule, input_data)
                    if result:
                        effect = rule.get("effect", "allow")
                        rule_info = {
                            "name": rule.get("name", ""),
                            "effect": effect,
                            "policy_id": pid,
                            "policy_name": policy.name,
                            "reason": rule.get("reason", ""),
                        }
                        if effect == "deny":
                            denied_rules.append(rule_info)
                            all_allowed = False
                        else:
                            matched_rules.append(rule_info)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.get('name')}: {e}")

        decision = "allow" if all_allowed else "deny"
        result = EvaluationResult(
            decision=decision,
            allowed=all_allowed,
            package=package,
            matched_rules=matched_rules,
            denied_rules=denied_rules,
            input_data=input_data,
            timestamp=datetime.utcnow(),
        )
        self._evaluation_history.append(result)
        if len(self._evaluation_history) > 10000:
            self._evaluation_history = self._evaluation_history[-5000:]
        return result

    def evaluate_multi(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for eval_req in evaluations:
            package = eval_req.get("package", "")
            input_data = eval_req.get("input", {})
            result = self.evaluate(package, input_data)
            results.append(result.to_dict())
        return results

    def get_evaluation_history(self, limit: int = 100, offset: int = 0,
                               package: Optional[str] = None) -> List[Dict[str, Any]]:
        history = list(self._evaluation_history)
        if package:
            history = [h for h in history if h.package == package]
        history.reverse()
        return [h.to_dict() for h in history[offset:offset + limit]]

    def sync_from_git(self, git_url: str, git_ref: str = "main") -> Dict[str, Any]:
        synced = 0
        errors = 0
        logger.info(f"Syncing policies from {git_url}@{git_ref}")
        return {
            "synced": synced,
            "errors": errors,
            "git_url": git_url,
            "git_ref": git_ref,
        }

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._policies)
        enabled = sum(1 for p in self._policies.values() if p.enabled)
        total_rules = sum(len(p.rules) for p in self._policies.values())
        packages = list(self._packages.keys())
        evaluations_24h = sum(
            1 for h in self._evaluation_history
            if (datetime.utcnow() - h.timestamp).total_seconds() < 86400
        )
        return {
            "total_policies": total,
            "enabled_policies": enabled,
            "total_rules": total_rules,
            "packages": len(packages),
            "evaluations_24h": evaluations_24h,
            "recent_decisions": {
                "allow": sum(1 for h in self._evaluation_history[-100:] if h.allowed),
                "deny": sum(1 for h in self._evaluation_history[-100:] if not h.allowed),
            },
        }
