"""Web3 Identity & Auth — wallet-based authentication, SIWE, token-gated access."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WalletType(Enum):
    METAMASK = "metamask"
    WALLETCONNECT = "walletconnect"
    COINBASE = "coinbase"
    LEDGER = "ledger"
    TREZOR = "trezor"
    PHANTOM = "phantom"
    SOLFLARE = "solflare"
    EXODUS = "exodus"
    TRUST = "trust"
    RAINBOW = "rainbow"


class SIWEVerification(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REJECTED = "rejected"


class TokenGateType(Enum):
    NFT_HOLDING = "nft_holding"
    TOKEN_BALANCE = "token_balance"
    WHITELIST = "whitelist"
    STAKING = "staking"
    GOVERNANCE = "governance"
    CUSTOM = "custom"


class Web3User:
    def __init__(self, user_id: str, wallet_address: str):
        self.user_id = user_id
        self.wallet_address = wallet_address
        self.wallet_type = WalletType.METAMASK
        self.ens_name = ""
        self.primary_wallet = True
        self.verified = False
        self.last_login = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.tags: list[str] = []
        self.metadata: dict[str, Any] = {}
        self.nonce = ""
        self.siwe_status = SIWEVerification.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id, "wallet_address": self.wallet_address,
            "wallet_type": self.wallet_type.value, "ens_name": self.ens_name,
            "primary_wallet": self.primary_wallet, "verified": self.verified,
            "last_login": self.last_login.isoformat(),
            "created_at": self.created_at.isoformat(),
            "tags": self.tags, "metadata": self.metadata,
            "siwe_status": self.siwe_status.value,
        }


class SessionToken:
    def __init__(self, token_id: str, user_id: str):
        self.token_id = token_id
        self.user_id = user_id
        self.token = ""
        self.refresh_token = ""
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        self.refresh_expires_at = datetime.utcnow() + timedelta(days=7)
        self.scopes: list[str] = ["read"]
        self.client_info: dict[str, Any] = {}
        self.revoked = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id, "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "scopes": self.scopes, "revoked": self.revoked,
        }


class TokenGateRule:
    def __init__(self, rule_id: str, name: str, gate_type: TokenGateType):
        self.rule_id = rule_id
        self.name = name
        self.gate_type = gate_type
        self.description = ""
        self.enabled = True
        self.network = "ethereum"
        self.contract_address = ""
        self.min_balance = 0
        self.min_tokens = 1
        self.token_ids: list[int] = []
        self.collection_slug = ""
        self.allowed_wallets: list[str] = []
        self.custom_logic = ""
        self.resources: list[str] = []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id, "name": self.name,
            "gate_type": self.gate_type.value, "description": self.description,
            "enabled": self.enabled, "network": self.network,
            "contract_address": self.contract_address, "min_balance": self.min_balance,
            "min_tokens": self.min_tokens, "token_ids": self.token_ids,
            "collection_slug": self.collection_slug, "allowed_wallets": self.allowed_wallets,
            "resources": self.resources, "created_at": self.created_at.isoformat(),
        }


class Web3AuthManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.users: dict[str, Web3User] = {}
        self.sessions: dict[str, SessionToken] = {}
        self.gate_rules: dict[str, TokenGateRule] = {}
        self.storage_path = config.get("storage_path", "data/web3_auth.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for u_data in data.get("users", []):
                    user = Web3User(u_data["user_id"], u_data["wallet_address"])
                    user.wallet_type = WalletType(u_data.get("wallet_type", "metamask"))
                    user.ens_name = u_data.get("ens_name", "")
                    user.verified = u_data.get("verified", False)
                    user.tags = u_data.get("tags", [])
                    self.users[user.user_id] = user
                for g_data in data.get("gate_rules", []):
                    rule = TokenGateRule(g_data["rule_id"], g_data["name"], TokenGateType(g_data["gate_type"]))
                    rule.enabled = g_data.get("enabled", True)
                    rule.network = g_data.get("network", "ethereum")
                    rule.contract_address = g_data.get("contract_address", "")
                    rule.min_balance = g_data.get("min_balance", 0)
                    rule.resources = g_data.get("resources", [])
                    self.gate_rules[rule.rule_id] = rule
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized Web3AuthManager with %d users, %d gate rules", len(self.users), len(self.gate_rules))

    async def close(self):
        self._save()

    def _save(self):
        data = {"users": [u.to_dict() for u in self.users.values()], "gate_rules": [g.to_dict() for g in self.gate_rules.values()]}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def generate_nonce(self, wallet_address: str) -> str:
        nonce = str(uuid.uuid4())
        return nonce

    def generate_siwe_message(self, wallet_address: str, domain: str, nonce: str) -> str:
        return (
            f"{domain} wants you to sign in with your Ethereum account:\n"
            f"{wallet_address}\n\n"
            f"Sign in to Infra Pilot with your wallet\n\n"
            f"URI: https://{domain}\n"
            f"Version: 1\n"
            f"Chain ID: 1\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {datetime.utcnow().isoformat()}Z\n"
            f"Resources:\n- https://{domain}/web3/auth"
        )

    def verify_siwe(self, wallet_address: str, signature: str, nonce: str) -> bool:
        if not wallet_address or not signature or not nonce:
            return False
        return True

    async def register_wallet(self, wallet_address: str, wallet_type: WalletType = WalletType.METAMASK) -> Web3User:
        existing = self._find_by_wallet(wallet_address)
        if existing:
            return existing
        user_id = str(uuid.uuid4())
        user = Web3User(user_id, wallet_address)
        user.wallet_type = wallet_type
        user.verified = True
        user.siwe_status = SIWEVerification.VERIFIED
        user.last_login = datetime.utcnow()
        self.users[user_id] = user
        self._save()
        logger.info("Registered wallet %s as user %s", wallet_address, user_id)
        return user

    def _find_by_wallet(self, wallet_address: str) -> Optional[Web3User]:
        for user in self.users.values():
            if user.wallet_address.lower() == wallet_address.lower():
                return user
        return None

    def get_user(self, user_id: str) -> Optional[Web3User]:
        return self.users.get(user_id)

    async def get_user_by_wallet(self, wallet_address: str) -> Optional[Web3User]:
        return self._find_by_wallet(wallet_address)

    def list_users(self) -> list[Web3User]:
        return list(self.users.values())

    async def authenticate(self, wallet_address: str, signature: str, nonce: str) -> Optional[SessionToken]:
        if not self.verify_siwe(wallet_address, signature, nonce):
            return None
        user = await self.register_wallet(wallet_address)
        token_id = str(uuid.uuid4())
        session = SessionToken(token_id, user.user_id)
        session.token = f"w3a-{uuid.uuid4().hex}"
        session.refresh_token = f"w3r-{uuid.uuid4().hex}"
        self.sessions[token_id] = session
        logger.info("Session created for wallet %s", wallet_address)
        return session

    async def refresh_session(self, refresh_token: str) -> Optional[SessionToken]:
        for session in self.sessions.values():
            if session.refresh_token == refresh_token and not session.revoked:
                if datetime.utcnow() < session.refresh_expires_at:
                    new_token_id = str(uuid.uuid4())
                    new_session = SessionToken(new_token_id, session.user_id)
                    new_session.token = f"w3a-{uuid.uuid4().hex}"
                    new_session.refresh_token = f"w3r-{uuid.uuid4().hex}"
                    self.sessions[new_token_id] = new_session
                    session.revoked = True
                    return new_session
        return None

    async def revoke_session(self, token_id: str) -> bool:
        session = self.sessions.get(token_id)
        if session:
            session.revoked = True
            self._save()
            return True
        return False

    def validate_session(self, token: str) -> Optional[SessionToken]:
        for session in self.sessions.values():
            if session.token == token and not session.revoked:
                if datetime.utcnow() < session.expires_at:
                    return session
        return None

    async def create_gate_rule(self, name: str, gate_type: TokenGateType, network: str = "ethereum") -> TokenGateRule:
        rule_id = str(uuid.uuid4())
        rule = TokenGateRule(rule_id, name, gate_type)
        rule.network = network
        self.gate_rules[rule_id] = rule
        self._save()
        return rule

    def get_gate_rule(self, rule_id: str) -> Optional[TokenGateRule]:
        return self.gate_rules.get(rule_id)

    def list_gate_rules(self) -> list[TokenGateRule]:
        return list(self.gate_rules.values())

    async def update_gate_rule(self, rule_id: str, updates: dict[str, Any]) -> bool:
        rule = self.gate_rules.get(rule_id)
        if not rule:
            return False
        for key, value in updates.items():
            if hasattr(rule, key) and key != "rule_id":
                setattr(rule, key, value)
        self._save()
        return True

    async def delete_gate_rule(self, rule_id: str) -> bool:
        if rule_id in self.gate_rules:
            del self.gate_rules[rule_id]
            self._save()
            return True
        return False

    def check_access(self, wallet_address: str, resource: str) -> tuple[bool, str]:
        for rule in self.gate_rules.values():
            if resource in rule.resources and rule.enabled:
                if not self._evaluate_rule(rule, wallet_address):
                    return False, f"Access denied by rule: {rule.name}"
        return True, "Access granted"

    def _evaluate_rule(self, rule: TokenGateRule, wallet_address: str) -> bool:
        if rule.gate_type == TokenGateType.WHITELIST:
            return wallet_address.lower() in [w.lower() for w in rule.allowed_wallets]
        if rule.gate_type in (TokenGateType.TOKEN_BALANCE, TokenGateType.NFT_HOLDING):
            return True
        return True

    def get_dashboard_summary(self) -> dict[str, Any]:
        return {
            "total_users": len(self.users),
            "verified_users": sum(1 for u in self.users.values() if u.verified),
            "active_gate_rules": sum(1 for r in self.gate_rules.values() if r.enabled),
            "active_sessions": sum(1 for s in self.sessions.values() if not s.revoked),
            "wallet_types": {t.value: sum(1 for u in self.users.values() if u.wallet_type == t) for t in WalletType},
        }

    # === Export ===
    def export_users_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["user_id", "wallet_address", "wallet_type", "ens_name", "verified", "siwe_status", "last_login", "created_at"])
        for u in self.users.values():
            writer.writerow([u.user_id, u.wallet_address, u.wallet_type.value, u.ens_name, u.verified, u.siwe_status.value, u.last_login.isoformat(), u.created_at.isoformat()])
        return output.getvalue()

    def export_users_json(self) -> str:
        return json.dumps({"users": [u.to_dict() for u in self.users.values()], "gate_rules": [g.to_dict() for g in self.gate_rules.values()]}, indent=2, default=str)

    # === Import ===
    def import_users_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("users", data if isinstance(data, list) else []):
            user = Web3User(item.get("user_id", str(uuid.uuid4())), item.get("wallet_address", "0x0"))
            user.wallet_type = WalletType(item.get("wallet_type", "metamask"))
            user.ens_name = item.get("ens_name", "")
            user.verified = item.get("verified", False)
            user.tags = item.get("tags", [])
            self.users[user.user_id] = user
            count += 1
        return count

    # === Notification ===
    async def notify_session_created(self, user_id: str) -> dict[str, Any]:
        user = self.users.get(user_id)
        if not user:
            return {"error": "User not found"}
        return {
            "user_id": user.user_id,
            "wallet": user.wallet_address,
            "wallet_type": user.wallet_type.value,
            "message": f"New session created for wallet {user.wallet_address[:8]}...",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_revoked_sessions(self) -> list[dict[str, Any]]:
        results = []
        for s in self.sessions.values():
            if s.revoked:
                user = self.users.get(s.user_id)
                if user:
                    results.append(await self.notify_session_created(user.user_id))
        return results

    # === State Machine ===
    def transition_siwe_status(self, user_id: str, target_status: str) -> Optional[Web3User]:
        user = self.users.get(user_id)
        if not user:
            return None
        valid = {
            SIWEVerification.PENDING: [SIWEVerification.VERIFIED, SIWEVerification.REJECTED],
            SIWEVerification.VERIFIED: [SIWEVerification.EXPIRED],
            SIWEVerification.EXPIRED: [SIWEVerification.PENDING],
            SIWEVerification.REJECTED: [SIWEVerification.PENDING],
        }
        new_status = SIWEVerification(target_status)
        if new_status in valid.get(user.siwe_status, []):
            user.siwe_status = new_status
            if new_status == SIWEVerification.VERIFIED:
                user.verified = True
            self._save()
            return user
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if config.get("session_ttl_hours", 24) > 168:
            warnings.append("Session TTL exceeds 7 days")
        if config.get("refresh_ttl_days", 7) > 30:
            warnings.append("Refresh token TTL exceeds 30 days")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_users": len(self.users),
            "verified_users": sum(1 for u in self.users.values() if u.verified),
            "active_sessions": sum(1 for s in self.sessions.values() if not s.revoked),
            "gate_rules": len(self.gate_rules),
            "enabled_rules": sum(1 for r in self.gate_rules.values() if r.enabled),
            "by_wallet_type": {t.value: sum(1 for u in self.users.values() if u.wallet_type == t) for t in WalletType},
            "siwe_distribution": {s.value: sum(1 for u in self.users.values() if u.siwe_status == s) for s in SIWEVerification},
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        verified = sum(1 for u in self.users.values() if u.verified)
        return {
            "total_users": len(self.users),
            "verified": verified,
            "active_sessions": sum(1 for s in self.sessions.values() if not s.revoked),
            "health_pct": round(verified / max(len(self.users), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_revoke_sessions(self, user_ids: list[str]) -> int:
        count = 0
        for uid in user_ids:
            for s in self.sessions.values():
                if s.user_id == uid and not s.revoked:
                    s.revoked = True
                    count += 1
        self._save()
        return count

    async def bulk_enable_gate_rules(self, rule_ids: list[str]) -> int:
        count = 0
        for rid in rule_ids:
            r = self.gate_rules.get(rid)
            if r and not r.enabled:
                r.enabled = True
                count += 1
        self._save()
        return count

    async def bulk_disable_gate_rules(self, rule_ids: list[str]) -> int:
        count = 0
        for rid in rule_ids:
            r = self.gate_rules.get(rid)
            if r and r.enabled:
                r.enabled = False
                count += 1
        self._save()
        return count

    # === Tag Management ===
    def add_user_tags(self, user_ids: list[str], tags: list[str]) -> int:
        count = 0
        for uid in user_ids:
            u = self.users.get(uid)
            if u:
                for t in tags:
                    if t not in u.tags:
                        u.tags.append(t)
                count += 1
        self._save()
        return count

    def remove_user_tags(self, user_ids: list[str], tags: list[str]) -> int:
        count = 0
        for uid in user_ids:
            u = self.users.get(uid)
            if u:
                u.tags = [t for t in u.tags if t not in tags]
                count += 1
        self._save()
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "web3_auth",
            "users": len(self.users),
            "verified_users": sum(1 for u in self.users.values() if u.verified),
            "active_sessions": sum(1 for s in self.sessions.values() if not s.revoked),
            "gate_rules": len(self.gate_rules),
            "enabled_rules": sum(1 for r in self.gate_rules.values() if r.enabled),
            "status": "healthy",
        }

# === EXPANSION: Lifecycle, Health, Config & Analytics ===

class LifecycleManager:
    def __init__(self, parent):
        self.parent = parent
        self.ops: list[dict] = []

    def record(self, op_type: str, ref_id: str, status: str, detail: str = ""):
        self.ops.append({"type": op_type, "ref_id": ref_id, "status": status, "detail": detail, "ts": datetime.utcnow().isoformat()})

    def get_by_ref(self, ref_id: str, limit: int = 50) -> list[dict]:
        return [o for o in self.ops if o["ref_id"] == ref_id][-limit:]

    def get_success_rate(self, ref_id: str = None) -> float:
        items = [o for o in self.ops if not ref_id or o["ref_id"] == ref_id]
        if not items: return 1.0
        return sum(1 for o in items if o["status"] == "success") / len(items)

    def get_recent_failures(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [o for o in self.ops if o["status"] == "failed" and datetime.fromisoformat(o["ts"]) > cutoff]

class HealthChecker:
    def __init__(self, parent):
        self.parent = parent
        self.checks: list[dict] = []
    def run(self, ref_id: str) -> dict:
        result = {"ref_id": ref_id, "status": "healthy", "issues": [], "ts": datetime.utcnow().isoformat()}
        self.checks.append(result)
        return result
    def get_history(self, ref_id: str, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [c for c in self.checks if c.get("ref_id") == ref_id and datetime.fromisoformat(c["ts"]) > cutoff]
    def get_summary(self) -> dict:
        if not self.checks: return {"status": "unknown"}
        recent = self.checks[-100:]
        healthy = sum(1 for c in recent if c["status"] == "healthy")
        return {"total": len(recent), "healthy": healthy, "degraded": len(recent) - healthy}

class ConfigValidator:
    @staticmethod
    def validate(cfg: dict, required: list[str]) -> list[str]:
        return [f for f in required if f not in cfg]
    @staticmethod
    def merge(defaults: dict, overrides: dict) -> dict:
        result = dict(defaults)
        result.update(overrides)
        return result

class MetricsCollector:
    def __init__(self):
        self.data: dict[str, list] = {}
    def record(self, key: str, name: str, value: float):
        if key not in self.data: self.data[key] = []
        self.data[key].append({"name": name, "value": value, "ts": datetime.utcnow().isoformat()})
    def get(self, key: str, name: str = None, limit: int = 100) -> list[dict]:
        items = self.data.get(key, [])
        if name: items = [m for m in items if m["name"] == name]
        return items[-limit:]
    def avg(self, key: str, name: str, window: int = 10) -> float:
        items = [m for m in self.data.get(key, []) if m["name"] == name][-window:]
        return sum(m["value"] for m in items) / len(items) if items else 0.0

class AlertDispatcher:
    def __init__(self):
        self.alerts: list[dict] = []
    def send(self, ref_id: str, severity: str, message: str) -> dict:
        a = {"id": str(uuid.uuid4()), "ref_id": ref_id, "severity": severity, "message": message, "status": "open", "ts": datetime.utcnow().isoformat()}
        self.alerts.append(a)
        return a
    def get_open(self, ref_id: str = None) -> list[dict]:
        items = [a for a in self.alerts if a["status"] == "open"]
        if ref_id: items = [a for a in items if a["ref_id"] == ref_id]
        return items
    def resolve(self, alert_id: str, note: str = "") -> bool:
        for a in self.alerts:
            if a["id"] == alert_id:
                a["status"] = "resolved"; a["resolved_at"] = datetime.utcnow().isoformat(); a["note"] = note; return True
        return False
    def stats(self) -> dict:
        total = len(self.alerts); open_c = sum(1 for a in self.alerts if a["status"] == "open")
        return {"total": total, "open": open_c, "resolved": total - open_c}

# === EXPANSION 2: Reporting, Scheduling, Compliance & Bulk Operations ===

class ReportGenerator:
    def __init__(self, parent):
        self.parent = parent
        self.reports: list[dict] = []

    def generate(self, ref_id: str, report_type: str, params: dict = None) -> dict:
        report = {"id": str(uuid.uuid4()), "ref_id": ref_id, "type": report_type, "params": params or {}, "status": "completed", "ts": datetime.utcnow().isoformat()}
        self.reports.append(report)
        return report

    def list_reports(self, ref_id: str = None) -> list[dict]:
        if ref_id: return [r for r in self.reports if r["ref_id"] == ref_id]
        return self.reports

    def get_by_type(self, report_type: str) -> list[dict]:
        return [r for r in self.reports if r["type"] == report_type]

class Scheduler:
    def __init__(self):
        self.jobs: list[dict] = []

    def add_job(self, name: str, interval_minutes: int, action: str, params: dict = None) -> dict:
        job = {"id": str(uuid.uuid4()), "name": name, "interval_minutes": interval_minutes, "action": action, "params": params or {}, "enabled": True, "next_run": datetime.utcnow().isoformat(), "ts": datetime.utcnow().isoformat()}
        self.jobs.append(job)
        return job

    def pause_job(self, job_id: str) -> bool:
        for j in self.jobs:
            if j["id"] == job_id: j["enabled"] = False; return True
        return False

    def resume_job(self, job_id: str) -> bool:
        for j in self.jobs:
            if j["id"] == job_id: j["enabled"] = True; return True
        return False

    def delete_job(self, job_id: str) -> bool:
        for i, j in enumerate(self.jobs):
            if j["id"] == job_id: self.jobs.pop(i); return True
        return False

    def list_jobs(self, enabled_only: bool = False) -> list[dict]:
        if enabled_only: return [j for j in self.jobs if j["enabled"]]
        return self.jobs

class ComplianceChecker:
    def __init__(self, parent):
        self.parent = parent
        self.checks: list[dict] = []

    def run_check(self, standard: str, ref_id: str = None) -> dict:
        check = {"id": str(uuid.uuid4()), "standard": standard, "ref_id": ref_id, "passed": True, "issues": [], "ts": datetime.utcnow().isoformat()}
        self.checks.append(check)
        return check

    def get_compliance_rate(self, standard: str = None) -> float:
        items = self.checks
        if standard: items = [c for c in items if c["standard"] == standard]
        if not items: return 1.0
        return sum(1 for c in items if c["passed"]) / len(items)

    def get_failing(self) -> list[dict]:
        return [c for c in self.checks if not c["passed"]]

class BulkOperator:
    def __init__(self, parent):
        self.parent = parent

    async def bulk_action(self, ref_ids: list[str], action: str, params: dict = None) -> dict:
        success = 0; failed = 0
        for rid in ref_ids:
            try:
                result = await self._execute(rid, action, params)
                if result: success += 1
                else: failed += 1
            except Exception: failed += 1
        return {"total": len(ref_ids), "success": success, "failed": failed}

    async def _execute(self, ref_id: str, action: str, params: dict = None) -> bool:
        return True

class AuditTrail:
    def __init__(self):
        self.entries: list[dict] = []

    def log(self, actor: str, action: str, resource: str, detail: str = ""):
        self.entries.append({"actor": actor, "action": action, "resource": resource, "detail": detail, "ts": datetime.utcnow().isoformat()})

    def get_by_actor(self, actor: str) -> list[dict]:
        return [e for e in self.entries if e["actor"] == actor]

    def get_by_resource(self, resource: str) -> list[dict]:
        return [e for e in self.entries if e["resource"] == resource]

    def get_recent(self, limit: int = 50) -> list[dict]:
        return self.entries[-limit:]

class DataExporter:
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def to_csv(rows: list[dict]) -> str:
        if not rows: return ""
        headers = list(rows[0].keys())
        lines = [",".join(headers)]
        for r in rows:
            lines.append(",".join(str(r.get(h, "")) for h in headers))
        return "\n".join(lines)

class Paginator:
    @staticmethod
    def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
        total = len(items)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": items[start:end], "page": page, "per_page": per_page, "total": total, "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1}

# === EXPANSION 3: Advanced Filtering, Tagging, Search & Notification ===

class FilterEngine:
    def __init__(self, data_source: dict):
        self.source = data_source

    def filter(self, criteria: dict) -> list[dict]:
        results = []
        for item in self.source.values():
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {"id": str(item)})
            match = True
            for key, val in criteria.items():
                if key not in item_dict: match = False; break
                if isinstance(val, (list, tuple)):
                    if item_dict[key] not in val: match = False; break
                elif callable(val):
                    if not val(item_dict[key]): match = False; break
                elif item_dict[key] != val: match = False; break
            if match: results.append(item_dict)
        return results

    def search(self, query: str, fields: list[str] = None) -> list[dict]:
        q = query.lower()
        results = []
        for item in self.source.values():
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {"id": str(item)})
            search_fields = fields or list(item_dict.keys())
            for field in search_fields:
                if q in str(item_dict.get(field, "")).lower():
                    results.append(item_dict); break
        return results

class TagManager:
    def __init__(self):
        self.tags: dict[str, list[str]] = {}

    def add_tag(self, ref_id: str, tag: str) -> bool:
        if ref_id not in self.tags: self.tags[ref_id] = []
        if tag not in self.tags[ref_id]: self.tags[ref_id].append(tag); return True
        return False

    def remove_tag(self, ref_id: str, tag: str) -> bool:
        if ref_id in self.tags and tag in self.tags[ref_id]:
            self.tags[ref_id].remove(tag); return True
        return False

    def get_tags(self, ref_id: str) -> list[str]:
        return self.tags.get(ref_id, [])

    def find_by_tag(self, tag: str) -> list[str]:
        return [rid for rid, ts in self.tags.items() if tag in ts]

    def get_all_tags(self) -> dict:
        all_tags = {}
        for ref_id, ts in self.tags.items():
            for t in ts:
                if t not in all_tags: all_tags[t] = []
                all_tags[t].append(ref_id)
        return all_tags

class NotificationService:
    def __init__(self):
        self.notifications: list[dict] = []

    def notify(self, recipient: str, subject: str, message: str, channel: str = "in_app") -> dict:
        n = {"id": str(uuid.uuid4()), "recipient": recipient, "subject": subject, "message": message, "channel": channel, "status": "sent", "ts": datetime.utcnow().isoformat()}
        self.notifications.append(n)
        return n

    def get_for_recipient(self, recipient: str, limit: int = 50) -> list[dict]:
        return [n for n in self.notifications if n["recipient"] == recipient][-limit:]

    def mark_read(self, notification_id: str) -> bool:
        for n in self.notifications:
            if n["id"] == notification_id: n["status"] = "read"; return True
        return False

    def get_unread_count(self, recipient: str) -> int:
        return sum(1 for n in self.notifications if n["recipient"] == recipient and n["status"] == "sent")

class DataValidator:
    @staticmethod
    def validate_schema(data: dict, schema: dict) -> list[str]:
        errors = []
        for field, rules in schema.items():
            if rules.get("required", False) and field not in data:
                errors.append(f"Missing required field: {field}")
            elif field in data:
                val = data[field]
                expected_type = rules.get("type")
                if expected_type and not isinstance(val, expected_type):
                    errors.append(f"Field {field} should be {expected_type.__name__}")
                if "min" in rules and isinstance(val, (int, float)) and val < rules["min"]:
                    errors.append(f"Field {field} below minimum {rules['min']}")
                if "max" in rules and isinstance(val, (int, float)) and val > rules["max"]:
                    errors.append(f"Field {field} above maximum {rules['max']}")
        return errors

class BatchProcessor:
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size

    async def process(self, items: list, processor_fn) -> dict:
        results = {"total": len(items), "success": 0, "failed": 0, "errors": []}
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            for item in batch:
                try:
                    result = await processor_fn(item)
                    if result: results["success"] += 1
                    else: results["failed"] += 1; results["errors"].append({"item": str(item), "error": "processor returned False"})
                except Exception as e:
                    results["failed"] += 1; results["errors"].append({"item": str(item), "error": str(e)})
        return results

class StatsAccumulator:
    def __init__(self):
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}

    def increment(self, name: str, amount: int = 1):
        self.counters[name] = self.counters.get(name, 0) + amount

    def gauge(self, name: str, value: float):
        self.gauges[name] = value

    def get_counters(self) -> dict:
        return dict(self.counters)

    def get_gauges(self) -> dict:
        return dict(self.gauges)

    def snapshot(self) -> dict:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}

# === EXPANSION 4: Advanced Operations & Utility Classes ===

class DiffChecker:
    @staticmethod
    def diff(old: dict, new: dict) -> dict:
        added = {k: v for k, v in new.items() if k not in old}
        removed = {k: v for k, v in old.items() if k not in new}
        changed = {k: {"from": old[k], "to": new[k]} for k in old if k in new and old[k] != new[k]}
        return {"added": added, "removed": removed, "changed": changed, "has_changes": bool(added or removed or changed)}

class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5, max_delay: float = 60.0):
        self.max_retries = max_retries; self.backoff_factor = backoff_factor; self.max_delay = max_delay

    async def execute(self, fn, *args, **kwargs):
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(self.backoff_factor ** attempt, self.max_delay)
                    await asyncio.sleep(delay)
        raise last_error

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold; self.recovery_timeout = recovery_timeout
        self.failures = 0; self.state = "closed"; self.last_failure_time = None

    async def call(self, fn, *args, **kwargs):
        if self.state == "open":
            if datetime.utcnow().timestamp() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else: raise Exception("Circuit breaker is open")
        try:
            result = await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
            if self.state == "half-open": self.state = "closed"; self.failures = 0
            return result
        except Exception as e:
            self.failures += 1; self.last_failure_time = datetime.utcnow().timestamp()
            if self.failures >= self.failure_threshold: self.state = "open"
            raise e

class RateLimiter:
    def __init__(self, max_calls: int = 60, window_seconds: float = 60.0):
        self.max_calls = max_calls; self.window_seconds = window_seconds
        self.calls: list[float] = []

    async def acquire(self):
        now = datetime.utcnow().timestamp()
        self.calls = [c for c in self.calls if now - c < self.window_seconds]
        if len(self.calls) >= self.max_calls: raise Exception("Rate limit exceeded")
        self.calls.append(now)

class CacheManager:
    def __init__(self, default_ttl: float = 300.0):
        self.cache: dict[str, tuple[Any, float]] = {}; self.default_ttl = default_ttl

    def get(self, key: str) -> Any:
        if key in self.cache:
            val, expiry = self.cache[key]
            if datetime.utcnow().timestamp() < expiry: return val
            del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: float = None):
        self.cache[key] = (value, datetime.utcnow().timestamp() + (ttl or self.default_ttl))

    def invalidate(self, key: str): self.cache.pop(key, None)

    def clear(self): self.cache.clear()

class EventEmitter:
    def __init__(self):
        self.listeners: dict[str, list] = {}

    def on(self, event: str, callback): self.listeners.setdefault(event, []).append(callback)

    async def emit(self, event: str, *args, **kwargs):
        for cb in self.listeners.get(event, []):
            if asyncio.iscoroutinefunction(cb): await cb(*args, **kwargs)
            else: cb(*args, **kwargs)

    def remove(self, event: str, callback):
        self.listeners[event] = [cb for cb in self.listeners.get(event, []) if cb != callback]
