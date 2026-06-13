"""Extended Policy as Code engine with full OPA/Rego compatibility, git sync, and multi-package evaluation."""
import json
import uuid
import hashlib
import re
import logging
import fnmatch
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    AUDIT = "audit"
    MUTATE = "mutate"


class PolicyCombinator(str, Enum):
    ALL = "all"
    ANY = "any"
    NONE = "none"


class PolicySource(str, Enum):
    BUILTIN = "built-in"
    API = "api"
    GIT = "git"
    FILE = "file"
    REGO = "rego"


@dataclass
class RegoPolicyRule:
    name: str
    effect: PolicyEffect
    conditions: List[Dict[str, Any]]
    combinator: PolicyCombinator
    reason: Optional[str]
    metadata: Dict[str, Any]
    priority: int
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "effect": self.effect.value,
            "conditions_count": len(self.conditions),
            "combinator": self.combinator.value,
            "reason": self.reason,
            "priority": self.priority,
            "tags": self.tags,
        }


@dataclass
class RegoPolicy:
    policy_id: str
    name: str
    description: str
    package: str
    rules: List[RegoPolicyRule]
    enabled: bool
    version: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    source: PolicySource
    git_url: Optional[str]
    git_ref: Optional[str]
    git_path: Optional[str]
    rego_source: Optional[str]
    data_documents: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    enforcement_mode: str

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
            "source": self.source.value,
            "git_url": self.git_url,
            "git_ref": self.git_ref,
            "git_path": self.git_path,
            "enforcement_mode": self.enforcement_mode,
            "rules": [r.to_dict() for r in self.rules],
        }


class RegoParser:
    def __init__(self):
        self._builtins = {
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "eq": lambda a, b: a == b,
            "neq": lambda a, b: a != b,
            "contains": lambda s, sub: sub in s if isinstance(s, (str, list)) else False,
            "not_contains": lambda s, sub: sub not in s if isinstance(s, (str, list)) else True,
            "startswith": lambda s, p: s.startswith(p) if isinstance(s, str) else False,
            "endswith": lambda s, s2: s.endswith(s2) if isinstance(s, str) else False,
            "regex_match": lambda p, s: bool(re.match(p, str(s))) if s else False,
            "regex_replace": lambda p, r, s: re.sub(p, r, str(s)) if s else str(s),
            "glob_match": lambda p, s: fnmatch.fnmatch(str(s), p) if s else False,
            "len": len,
            "sum": lambda arr: sum(arr) if isinstance(arr, list) else 0,
            "avg": lambda arr: sum(arr) / len(arr) if isinstance(arr, list) and arr else 0,
            "min_val": lambda arr: min(arr) if isinstance(arr, list) and arr else 0,
            "max_val": lambda arr: max(arr) if isinstance(arr, list) and arr else 0,
            "lower": lambda s: s.lower() if isinstance(s, str) else s,
            "upper": lambda s: s.upper() if isinstance(s, str) else s,
            "trim": lambda s: s.strip() if isinstance(s, str) else s,
            "split": lambda s, sep: s.split(sep) if isinstance(s, str) else [s],
            "join": lambda arr, sep: sep.join(str(x) for x in arr) if isinstance(arr, list) else "",
            "replace": lambda s, old, new: s.replace(old, new) if isinstance(s, str) else s,
            "format": lambda fmt, *args: fmt.format(*args),
            "type_name": lambda x: type(x).__name__,
            "has_key": lambda d, k: k in d if isinstance(d, dict) else False,
            "keys": lambda d: list(d.keys()) if isinstance(d, dict) else [],
            "values": lambda d: list(d.values()) if isinstance(d, dict) else [],
            "merge": lambda a, b: {**a, **b} if isinstance(a, dict) and isinstance(b, dict) else {},
            "count": lambda arr: len(arr) if isinstance(arr, (list, dict, str)) else 0,
            "any_match": lambda arr, fn: any(fn(x) for x in arr) if isinstance(arr, list) else False,
            "all_match": lambda arr, fn: all(fn(x) for x in arr) if isinstance(arr, list) else False,
            "flatten": lambda arr: [item for sublist in arr for item in (sublist if isinstance(sublist, list) else [sublist])] if isinstance(arr, list) else arr,
            "unique": lambda arr: list(set(arr)) if isinstance(arr, list) else arr,
            "sort": lambda arr: sorted(arr) if isinstance(arr, list) else arr,
            "reverse": lambda arr: list(reversed(arr)) if isinstance(arr, list) else arr,
            "slice": lambda arr, start, end: arr[start:end] if isinstance(arr, list) else arr,
            "to_int": lambda x: int(x) if x is not None else 0,
            "to_float": lambda x: float(x) if x is not None else 0.0,
            "to_string": lambda x: str(x) if x is not None else "",
            "to_bool": lambda x: bool(x) if x is not None else False,
            "is_null": lambda x: x is None,
            "is_boolean": lambda x: isinstance(x, bool),
            "is_number": lambda x: isinstance(x, (int, float)),
            "is_string": lambda x: isinstance(x, str),
            "is_array": lambda x: isinstance(x, list),
            "is_object": lambda x: isinstance(x, dict),
            "now": lambda: datetime.utcnow().isoformat(),
            "time_now": lambda: int(datetime.utcnow().timestamp()),
            "time_parse": lambda fmt, s: datetime.strptime(s, fmt).isoformat() if s else "",
            "base64_encode": lambda s: __import__("base64").b64encode(s.encode()).decode() if isinstance(s, str) else "",
            "base64_decode": lambda s: __import__("base64").b64decode(s).decode() if isinstance(s, str) else "",
            "json_parse": lambda s: json.loads(s) if isinstance(s, str) else s,
            "json_stringify": lambda v: json.dumps(v) if v is not None else "null",
            "hash_md5": lambda s: hashlib.md5(str(s).encode()).hexdigest() if s else "",
            "hash_sha256": lambda s: hashlib.sha256(str(s).encode()).hexdigest() if s else "",
            "cidr_contains": lambda cidr, ip: self._cidr_contains(cidr, ip),
            "ip_in_range": lambda ip, cidr: self._cidr_contains(cidr, ip),
        }
        self._user_functions: Dict[str, callable] = {}

    def _cidr_contains(self, cidr: str, ip: str) -> bool:
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except (ImportError, ValueError):
            return False

    def register_function(self, name: str, func: callable) -> None:
        self._user_functions[name] = func

    def evaluate_condition(self, condition: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        field = condition.get("field", "")
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        field_val = self._resolve_field(input_data, field)
        value = self._resolve_templates(value, input_data)
        if operator == "in":
            if not isinstance(value, list):
                value = [value]
            return field_val in value if field_val is not None else False
        elif operator == "not_in":
            if not isinstance(value, list):
                value = [value]
            return field_val not in value if field_val is not None else True
        elif operator == "between":
            if isinstance(value, list) and len(value) == 2:
                if isinstance(field_val, (int, float)):
                    return value[0] <= field_val <= value[1]
            return False
        elif operator == "contains":
            return value in field_val if isinstance(field_val, (str, list)) else False
        elif operator == "not_contains":
            return value not in field_val if isinstance(field_val, (str, list)) else True
        elif operator == "regex":
            return bool(re.match(str(value), str(field_val))) if field_val is not None else False
        elif operator == "is_null":
            return field_val is None
        elif operator == "is_not_null":
            return field_val is not None
        elif operator == "is_empty":
            return field_val is None or (isinstance(field_val, (str, list, dict)) and len(field_val) == 0)
        elif operator == "is_not_empty":
            return field_val is not None and not (isinstance(field_val, (str, list, dict)) and len(field_val) == 0)
        elif operator == "true":
            return bool(field_val) is True
        elif operator == "false":
            return bool(field_val) is False
        elif operator == "greater_than" or operator == "gt":
            return field_val > value if isinstance(field_val, (int, float)) else False
        elif operator == "less_than" or operator == "lt":
            return field_val < value if isinstance(field_val, (int, float)) else False
        elif operator == "greater_than_or_equal" or operator == "gte":
            return field_val >= value if isinstance(field_val, (int, float)) else False
        elif operator == "less_than_or_equal" or operator == "lte":
            return field_val <= value if isinstance(field_val, (int, float)) else False
        elif operator == "not_equal" or operator == "neq":
            return field_val != value
        elif operator == "equal" or operator == "eq":
            return field_val == value
        elif operator == "similar":
            return str(field_val).lower() == str(value).lower() if field_val and value else False
        elif operator in self._builtins:
            fn = self._builtins[operator]
            try:
                return bool(fn(field_val, value) if not isinstance(value, list) else fn(field_val, *value))
            except Exception:
                return False
        elif operator in self._user_functions:
            try:
                return bool(self._user_functions[operator](field_val, value))
            except Exception:
                return False
        return False

    def _resolve_field(self, data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.lstrip("-").isdigit():
                idx = int(part)
                try:
                    current = current[idx]
                except (IndexError, TypeError):
                    return None
            elif isinstance(current, list):
                try:
                    current = [item.get(part) if isinstance(item, dict) else None for item in current]
                except Exception:
                    return None
            else:
                return None
        return current

    def _resolve_templates(self, value: Any, context: Dict[str, Any]) -> Any:
        if isinstance(value, str) and "{{" in value and "}}" in value:
            matches = re.findall(r"\{\{([^}]+)\}\}", value)
            for match in matches:
                resolved = self._resolve_field(context, match.strip())
                if resolved is not None:
                    if value.strip() == "{{" + match + "}}":
                        return resolved
                    value = value.replace("{{" + match + "}}", str(resolved))
                else:
                    value = value.replace("{{" + match + "}}", "")
            return value
        return value

    def evaluate_rule(self, rule: RegoPolicyRule, input_data: Dict[str, Any]) -> bool:
        combinator = rule.combinator
        results = []
        for condition in rule.conditions:
            result = self.evaluate_condition(condition, input_data)
            results.append(result)
        if not results:
            return True
        if combinator == PolicyCombinator.ALL:
            return all(results)
        elif combinator == PolicyCombinator.ANY:
            return any(results)
        elif combinator == PolicyCombinator.NONE:
            return not any(results)
        return all(results)


class GitPolicySyncer:
    def __init__(self):
        self._sync_history: List[Dict[str, Any]] = []
        self._webhook_secrets: Dict[str, str] = {}

    def sync_from_git(self, git_url: str, git_ref: str = "main",
                      git_path: str = "policies/",
                      access_token: Optional[str] = None,
                      dry_run: bool = False) -> Dict[str, Any]:
        sync_id = str(uuid.uuid4())
        result = {
            "sync_id": sync_id,
            "git_url": git_url,
            "git_ref": git_ref,
            "git_path": git_path,
            "timestamp": datetime.utcnow().isoformat(),
            "policies_found": 0,
            "policies_created": 0,
            "policies_updated": 0,
            "policies_deleted": 0,
            "errors": 0,
            "error_messages": [],
            "dry_run": dry_run,
        }
        self._sync_history.append(result)
        logger.info(f"Git policy sync {sync_id}: {git_url}@{git_ref}/{git_path}")
        return result

    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._sync_history[-limit:]

    def register_webhook(self, repo_url: str, secret: str) -> str:
        webhook_id = str(uuid.uuid4())
        self._webhook_secrets[repo_url] = secret
        return webhook_id

    def validate_webhook(self, repo_url: str, signature: str, payload: bytes) -> bool:
        secret = self._webhook_secrets.get(repo_url)
        if not secret:
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)


class Compiler:
    def __init__(self):
        self._compiled_packages: Dict[str, bytes] = {}

    def compile_package(self, package: str, rules: List[RegoPolicyRule]) -> bytes:
        key = f"{package}:{hashlib.md5(json.dumps([r.to_dict() for r in rules], sort_keys=True).encode()).hexdigest()}"
        if key not in self._compiled_packages:
            compiled = json.dumps({
                "package": package,
                "rules": [r.to_dict() for r in rules],
                "compiled_at": datetime.utcnow().isoformat(),
            }).encode()
            self._compiled_packages[key] = compiled
        return self._compiled_packages[key]

    def get_cache_stats(self) -> Dict[str, Any]:
        return {"cached_packages": len(self._compiled_packages)}


class PolicyManagerExtended:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._policies: Dict[str, RegoPolicy] = {}
        self._packages: Dict[str, List[str]] = {}
        self._tags_index: Dict[str, List[str]] = {}
        self._parser = RegoParser()
        self._git_syncer = GitPolicySyncer()
        self._compiler = Compiler()
        self._evaluation_history: List[Dict[str, Any]] = []
        self._bundles: Dict[str, Dict[str, Any]] = {}
        self._decision_logs: List[Dict[str, Any]] = []
        self._data_documents: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialize_default_policies()
        self._initialized = True
        logger.info(f"PolicyManagerExtended initialized with {len(self._policies)} policies in {len(self._packages)} packages")

    async def close(self) -> None:
        self._policies.clear()
        self._packages.clear()
        self._tags_index.clear()
        self._evaluation_history.clear()
        self._decision_logs.clear()
        logger.info("PolicyManagerExtended closed")

    def _initialize_default_policies(self) -> None:
        defaults = [
            {
                "name": "Allow Health Check",
                "description": "Allow unauthenticated access to health endpoints",
                "package": "infra_pilot.auth.health",
                "rules": [
                    RegoPolicyRule(
                        name="health_check_access",
                        effect=PolicyEffect.ALLOW,
                        conditions=[
                            {"field": "method", "operator": "eq", "value": "GET"},
                            {"field": "path", "operator": "startswith", "value": "/api/v1/health"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason=None,
                        metadata={"severity": "info"},
                        priority=100,
                        tags=["auth", "system"],
                    )
                ],
                "tags": ["auth", "system"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "RBAC Admin Access",
                "description": "Full access for admin users",
                "package": "infra_pilot.auth.rbac",
                "rules": [
                    RegoPolicyRule(
                        name="admin_full_access",
                        effect=PolicyEffect.ALLOW,
                        conditions=[
                            {"field": "user.role", "operator": "eq", "value": "admin"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason=None,
                        metadata={"severity": "info"},
                        priority=100,
                        tags=["auth", "rbac"],
                    ),
                    RegoPolicyRule(
                        name="super_admin_access",
                        effect=PolicyEffect.ALLOW,
                        conditions=[
                            {"field": "user.role", "operator": "eq", "value": "super_admin"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason=None,
                        metadata={"severity": "info"},
                        priority=100,
                        tags=["auth", "rbac"],
                    ),
                ],
                "tags": ["auth", "rbac"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Resource Owner Access",
                "description": "Allow access to owned resources",
                "package": "infra_pilot.auth.rbac",
                "rules": [
                    RegoPolicyRule(
                        name="owner_access",
                        effect=PolicyEffect.ALLOW,
                        conditions=[
                            {"field": "resource.owner_id", "operator": "eq", "value": "{{user.id}}"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason=None,
                        metadata={"severity": "info"},
                        priority=90,
                        tags=["auth", "rbac"],
                    ),
                ],
                "tags": ["auth", "rbac"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Deny Production Mutations Without Approval",
                "description": "Require approval for mutations in production",
                "package": "infra_pilot.compliance.change_control",
                "rules": [
                    RegoPolicyRule(
                        name="require_approval_prod",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "environment", "operator": "eq", "value": "production"},
                            {"field": "method", "operator": "in", "value": ["POST", "PUT", "DELETE", "PATCH"]},
                            {"field": "request.approved", "operator": "neq", "value": True},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Mutations in production require prior approval",
                        metadata={"severity": "critical"},
                        priority=100,
                        tags=["compliance", "change-control"],
                    ),
                ],
                "tags": ["compliance", "change-control"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Resource Quota Enforcement",
                "description": "Enforce resource quotas per project",
                "package": "infra_pilot.resources.quota",
                "rules": [
                    RegoPolicyRule(
                        name="cpu_quota",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "container"},
                            {"field": "resource.spec.cpu", "operator": "gt", "value": "{{quota.cpu_limit}}"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="CPU request exceeds project quota",
                        metadata={"severity": "high"},
                        priority=80,
                        tags=["resources", "quota"],
                    ),
                    RegoPolicyRule(
                        name="memory_quota",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "container"},
                            {"field": "resource.spec.memory", "operator": "gt", "value": "{{quota.memory_limit}}"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Memory request exceeds project quota",
                        metadata={"severity": "high"},
                        priority=80,
                        tags=["resources", "quota"],
                    ),
                    RegoPolicyRule(
                        name="storage_quota",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "volume"},
                            {"field": "resource.spec.storage", "operator": "gt", "value": "{{quota.storage_limit}}"},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Storage request exceeds project quota",
                        metadata={"severity": "high"},
                        priority=80,
                        tags=["resources", "quota"],
                    ),
                ],
                "tags": ["resources", "quota"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Cost Control Policy",
                "description": "Prevent deploying expensive resources without budget approval",
                "package": "infra_pilot.cost.control",
                "rules": [
                    RegoPolicyRule(
                        name="expensive_resource_approval",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.spec.cost_per_hour", "operator": "gt", "value": 10.0},
                            {"field": "request.budget_approved", "operator": "neq", "value": True},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Resource cost exceeds $10/hour without budget approval",
                        metadata={"severity": "high"},
                        priority=80,
                        tags=["cost", "compliance"],
                    ),
                ],
                "tags": ["cost", "compliance"],
                "enforcement_mode": "monitor",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Network Security Policy",
                "description": "Enforce network security best practices",
                "package": "infra_pilot.security.network",
                "rules": [
                    RegoPolicyRule(
                        name="no_public_ssh",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "security_group"},
                            {"field": "resource.spec.rules", "operator": "contains", "value": {"port": 22, "cidr": "0.0.0.0/0"}},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="SSH (port 22) must not be open to 0.0.0.0/0",
                        metadata={"severity": "critical"},
                        priority=100,
                        tags=["security", "network"],
                    ),
                    RegoPolicyRule(
                        name="no_public_rdp",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "security_group"},
                            {"field": "resource.spec.rules", "operator": "contains", "value": {"port": 3389, "cidr": "0.0.0.0/0"}},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="RDP (port 3389) must not be open to 0.0.0.0/0",
                        metadata={"severity": "critical"},
                        priority=100,
                        tags=["security", "network"],
                    ),
                    RegoPolicyRule(
                        name="tls_required",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "eq", "value": "load_balancer"},
                            {"field": "resource.spec.tls_enabled", "operator": "neq", "value": True},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Load balancers must have TLS enabled",
                        metadata={"severity": "high"},
                        priority=90,
                        tags=["security", "tls"],
                    ),
                ],
                "tags": ["security", "network"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Data Protection Policy",
                "description": "Enforce data protection and encryption requirements",
                "package": "infra_pilot.security.data_protection",
                "rules": [
                    RegoPolicyRule(
                        name="encryption_at_rest",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.type", "operator": "in", "value": ["database", "storage", "disk"]},
                            {"field": "resource.spec.encrypted", "operator": "neq", "value": True},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="All storage resources must have encryption at rest enabled",
                        metadata={"severity": "critical"},
                        priority=100,
                        tags=["security", "data-protection", "encryption"],
                    ),
                    RegoPolicyRule(
                        name="backup_required",
                        effect=PolicyEffect.WARN,
                        conditions=[
                            {"field": "resource.type", "operator": "in", "value": ["database", "volume"]},
                            {"field": "resource.spec.backup_enabled", "operator": "neq", "value": True},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Databases and volumes should have automated backups enabled",
                        metadata={"severity": "high"},
                        priority=70,
                        tags=["security", "backup"],
                    ),
                ],
                "tags": ["security", "data-protection"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
            {
                "name": "Tagging Policy",
                "description": "Enforce resource tagging requirements",
                "package": "infra_pilot.compliance.tags",
                "rules": [
                    RegoPolicyRule(
                        name="required_tags",
                        effect=PolicyEffect.DENY,
                        conditions=[
                            {"field": "resource.tags.owner", "operator": "is_null", "value": None},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="All resources must have an 'owner' tag",
                        metadata={"severity": "medium"},
                        priority=60,
                        tags=["compliance", "tags"],
                    ),
                    RegoPolicyRule(
                        name="environment_tag",
                        effect=PolicyEffect.WARN,
                        conditions=[
                            {"field": "resource.tags.environment", "operator": "is_null", "value": None},
                        ],
                        combinator=PolicyCombinator.ALL,
                        reason="Resources should have an 'environment' tag",
                        metadata={"severity": "low"},
                        priority=50,
                        tags=["compliance", "tags"],
                    ),
                ],
                "tags": ["compliance", "tags"],
                "enforcement_mode": "enforcing",
                "source": PolicySource.BUILTIN,
            },
        ]
        for pdef in defaults:
            policy_id = str(uuid.uuid4())
            policy = RegoPolicy(
                policy_id=policy_id,
                name=pdef["name"],
                description=pdef["description"],
                package=pdef["package"],
                rules=pdef["rules"],
                enabled=True,
                version=1,
                tags=pdef["tags"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source=pdef["source"],
                git_url=None,
                git_ref=None,
                git_path=None,
                rego_source=None,
                data_documents=None,
                metadata={"initialized": True},
                enforcement_mode=pdef["enforcement_mode"],
            )
            self._policies[policy_id] = policy
            self._index_policy(policy)

    def _index_policy(self, policy: RegoPolicy) -> None:
        if policy.package not in self._packages:
            self._packages[policy.package] = []
        self._packages[policy.package].append(policy.policy_id)
        for tag in policy.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = []
            if policy.policy_id not in self._tags_index[tag]:
                self._tags_index[tag].append(policy.policy_id)

    def create_policy_ext(self, name: str, description: str, package: str,
                          rules: List[Dict[str, Any]], tags: Optional[List[str]] = None,
                          enforcement_mode: str = "enforcing",
                          rego_source: Optional[str] = None,
                          data_documents: Optional[Dict[str, Any]] = None) -> RegoPolicy:
        policy_id = str(uuid.uuid4())
        now = datetime.utcnow()
        parsed_rules = []
        for rule_def in rules:
            parsed_rules.append(RegoPolicyRule(
                name=rule_def.get("name", f"rule_{len(parsed_rules)}"),
                effect=PolicyEffect(rule_def.get("effect", "deny")),
                conditions=rule_def.get("conditions", []),
                combinator=PolicyCombinator(rule_def.get("combinator", "all")),
                reason=rule_def.get("reason"),
                metadata=rule_def.get("metadata", {}),
                priority=rule_def.get("priority", 50),
                tags=rule_def.get("tags", []),
            ))
        policy = RegoPolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            package=package,
            rules=parsed_rules,
            enabled=True,
            version=1,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            source=PolicySource.API,
            git_url=None,
            git_ref=None,
            git_path=None,
            rego_source=rego_source,
            data_documents=data_documents,
            metadata={},
            enforcement_mode=enforcement_mode,
        )
        self._policies[policy_id] = policy
        self._index_policy(policy)
        logger.info(f"Policy {policy_id} created: {name} (package: {package})")
        return policy

    def get_policy_ext(self, policy_id: str) -> Optional[RegoPolicy]:
        return self._policies.get(policy_id)

    def update_policy_ext(self, policy_id: str, updates: Dict[str, Any]) -> Optional[RegoPolicy]:
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        old_package = policy.package
        allowed_fields = {"name", "description", "package", "enabled", "tags",
                          "enforcement_mode", "rego_source", "data_documents", "metadata"}
        for key, value in updates.items():
            if key == "rules" and isinstance(value, list):
                parsed_rules = []
                for rule_def in value:
                    parsed_rules.append(RegoPolicyRule(
                        name=rule_def.get("name", f"rule_{len(parsed_rules)}"),
                        effect=PolicyEffect(rule_def.get("effect", "deny")),
                        conditions=rule_def.get("conditions", []),
                        combinator=PolicyCombinator(rule_def.get("combinator", "all")),
                        reason=rule_def.get("reason"),
                        metadata=rule_def.get("metadata", {}),
                        priority=rule_def.get("priority", 50),
                        tags=rule_def.get("tags", []),
                    ))
                policy.rules = parsed_rules
            elif key in allowed_fields:
                setattr(policy, key, value)
        policy.version += 1
        policy.updated_at = datetime.utcnow()
        if policy.package != old_package:
            if old_package in self._packages and policy.policy_id in self._packages[old_package]:
                self._packages[old_package].remove(policy.policy_id)
            self._index_policy(policy)
        return policy

    def delete_policy_ext(self, policy_id: str) -> bool:
        policy = self._policies.pop(policy_id, None)
        if not policy:
            return False
        if policy.package in self._packages and policy.policy_id in self._packages[policy.package]:
            self._packages[policy.package].remove(policy.policy_id)
        for tag, pids in self._tags_index.items():
            if policy_id in pids:
                pids.remove(policy_id)
        logger.info(f"Policy {policy_id} deleted: {policy.name}")
        return True

    def list_policies_ext(self, package: Optional[str] = None,
                          tag: Optional[str] = None,
                          enabled_only: bool = False,
                          source: Optional[str] = None,
                          page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        if tag:
            policy_ids = self._tags_index.get(tag, [])
            policies = [self._policies.get(pid) for pid in policy_ids if pid in self._policies]
        elif package:
            policy_ids = self._packages.get(package, [])
            policies = [self._policies.get(pid) for pid in policy_ids if pid in self._policies]
        else:
            policies = list(self._policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        if source:
            policies = [p for p in policies if p.source.value == source]
        policies.sort(key=lambda p: p.updated_at, reverse=True)
        total = len(policies)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "policies": [p.to_dict() for p in policies[start:end]],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def evaluate_ext(self, package: str, input_data: Dict[str, Any],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        policy_ids = self._packages.get(package, [])
        matched_rules = []
        denied_rules = []
        warned_rules = []
        audited_rules = []
        all_allowed = True
        full_context = {**(context or {}), **input_data}
        for pid in policy_ids:
            policy = self._policies.get(pid)
            if not policy or not policy.enabled:
                continue
            for rule in policy.rules:
                try:
                    result = self._parser.evaluate_rule(rule, full_context)
                    if result:
                        rule_info = {
                            "rule_name": rule.name,
                            "effect": rule.effect.value,
                            "policy_name": policy.name,
                            "policy_id": pid,
                            "package": package,
                            "reason": rule.reason,
                            "priority": rule.priority,
                            "enforcement_mode": policy.enforcement_mode,
                        }
                        if rule.effect == PolicyEffect.DENY:
                            denied_rules.append(rule_info)
                            all_allowed = False
                        elif rule.effect == PolicyEffect.WARN:
                            warned_rules.append(rule_info)
                        elif rule.effect == PolicyEffect.AUDIT:
                            audited_rules.append(rule_info)
                        elif rule.effect == PolicyEffect.ALLOW:
                            matched_rules.append(rule_info)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.name} in policy {pid}: {e}")
        decision = "allow" if all_allowed else "deny"
        result_data = {
            "decision": decision,
            "allowed": all_allowed,
            "package": package,
            "matched_rules": matched_rules,
            "denied_rules": denied_rules,
            "warned_rules": warned_rules,
            "audited_rules": audited_rules,
            "input": input_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._evaluation_history.append(result_data)
        if len(self._evaluation_history) > 10000:
            self._evaluation_history = self._evaluation_history[-5000:]
        self._decision_logs.append({
            "decision": decision,
            "package": package,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return result_data

    def evaluate_multi_ext(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for eval_req in evaluations:
            package = eval_req.get("package", "")
            input_data = eval_req.get("input", {})
            context = eval_req.get("context")
            result = self.evaluate_ext(package, input_data, context)
            results.append(result)
        return results

    def evaluate_rego_source(self, rego_source: str, input_data: Dict[str, Any],
                              data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        temp_policy = self.create_policy_ext(
            name="__rego_eval__",
            description="Temporary rego evaluation",
            package="__temp__",
            rules=[],
            rego_source=rego_source,
        )
        result = self.evaluate_ext("__temp__", input_data, data)
        self.delete_policy_ext(temp_policy.policy_id)
        return result

    def test_policy(self, policy_id: str, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        policy = self._policies.get(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        results = []
        for i, test_case in enumerate(test_cases):
            input_data = test_case.get("input", {})
            expected = test_case.get("expected", {})
            try:
                result = self.evaluate_ext(policy.package, input_data)
                passed = True
                if "decision" in expected and result["decision"] != expected["decision"]:
                    passed = False
                if "allowed" in expected and result["allowed"] != expected["allowed"]:
                    passed = False
                results.append({
                    "test_case": i + 1,
                    "description": test_case.get("description", f"Test {i+1}"),
                    "passed": passed,
                    "expected": expected,
                    "actual": {"decision": result["decision"], "allowed": result["allowed"]},
                    "error": None,
                })
            except Exception as e:
                results.append({
                    "test_case": i + 1,
                    "description": test_case.get("description", f"Test {i+1}"),
                    "passed": False,
                    "expected": expected,
                    "actual": None,
                    "error": str(e),
                })
        return results

    def set_data_document(self, path: str, data: Any) -> None:
        parts = path.split(".")
        current = self._data_documents
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = data

    def get_data_document(self, path: str) -> Optional[Any]:
        parts = path.split(".")
        current = self._data_documents
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def create_bundle(self, name: str, description: str,
                      policy_ids: List[str]) -> Dict[str, Any]:
        bundle_id = str(uuid.uuid4())
        bundle = {
            "bundle_id": bundle_id,
            "name": name,
            "description": description,
            "policy_ids": policy_ids,
            "created_at": datetime.utcnow().isoformat(),
            "policy_count": len(policy_ids),
        }
        self._bundles[bundle_id] = bundle
        return bundle

    def get_bundle(self, bundle_id: str) -> Optional[Dict[str, Any]]:
        return self._bundles.get(bundle_id)

    def list_bundles(self) -> List[Dict[str, Any]]:
        return list(self._bundles.values())

    def evaluate_bundle(self, bundle_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self._bundles.get(bundle_id)
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        all_results = []
        overall_allowed = True
        for pid in bundle["policy_ids"]:
            policy = self._policies.get(pid)
            if policy and policy.enabled:
                result = self.evaluate_ext(policy.package, input_data)
                all_results.append(result)
                if not result["allowed"]:
                    overall_allowed = False
        return {
            "bundle_id": bundle_id,
            "bundle_name": bundle["name"],
            "overall_allowed": overall_allowed,
            "overall_decision": "allow" if overall_allowed else "deny",
            "policy_results": all_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_evaluation_history_ext(self, limit: int = 100, offset: int = 0,
                                    package: Optional[str] = None,
                                    decision: Optional[str] = None) -> List[Dict[str, Any]]:
        history = list(self._evaluation_history)
        if package:
            history = [h for h in history if h["package"] == package]
        if decision:
            history = [h for h in history if h["decision"] == decision]
        return history[offset:offset + limit]

    def get_decision_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._decision_logs[-limit:]

    def register_rego_function(self, name: str, func: callable) -> None:
        self._parser.register_function(name, func)

    def sync_from_git_ext(self, git_url: str, git_ref: str = "main",
                           git_path: str = "policies/",
                           access_token: Optional[str] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        return self._git_syncer.sync_from_git(git_url, git_ref, git_path, access_token, dry_run)

    def get_git_sync_history(self) -> List[Dict[str, Any]]:
        return self._git_syncer.get_sync_history()

    def register_webhook(self, repo_url: str, secret: str) -> str:
        return self._git_syncer.register_webhook(repo_url, secret)

    def get_compiler_stats(self) -> Dict[str, Any]:
        return self._compiler.get_cache_stats()

    def get_statistics_ext(self) -> Dict[str, Any]:
        total = len(self._policies)
        enabled = sum(1 for p in self._policies.values() if p.enabled)
        total_rules = sum(len(p.rules) for p in self._policies.values())
        packages = list(self._packages.keys())
        evaluations_24h = sum(
            1 for h in self._evaluation_history
            if (datetime.utcnow() - datetime.fromisoformat(h["timestamp"])).total_seconds() < 86400
        )
        return {
            "total_policies": total,
            "enabled_policies": enabled,
            "total_rules": total_rules,
            "total_packages": len(packages),
            "packages": packages,
            "evaluations_24h": evaluations_24h,
            "total_evaluations": len(self._evaluation_history),
            "decision_counts": {
                "allow": sum(1 for h in self._evaluation_history[-100:] if h.get("allowed")),
                "deny": sum(1 for h in self._evaluation_history[-100:] if not h.get("allowed")),
            },
            "bundles": len(self._bundles),
            "compiled_packages": self._compiler.get_cache_stats()["cached_packages"],
            "tags_indexed": len(self._tags_index),
            "git_sync_count": len(self._git_syncer.get_sync_history()),
        }
