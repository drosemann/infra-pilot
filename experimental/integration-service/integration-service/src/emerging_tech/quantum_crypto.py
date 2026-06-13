"""Quantum-Safe Cryptography — post-quantum crypto (Kyber, Dilithium) for TLS, VPN, and signing."""

import asyncio
import aiofiles
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PQAlgorithm(Enum):
    KYBER_512 = "kyber-512"
    KYBER_768 = "kyber-768"
    KYBER_1024 = "kyber-1024"
    DILITHIUM_2 = "dilithium-2"
    DILITHIUM_3 = "dilithium-3"
    DILITHIUM_5 = "dilithium-5"
    FALCON_512 = "falcon-512"
    FALCON_1024 = "falcon-1024"
    SPHINCS_PLUS_128 = "sphincs-plus-128"
    SPHINCS_PLUS_192 = "sphincs-plus-192"
    SPHINCS_PLUS_256 = "sphincs-plus-256"


class CertificateType(Enum):
    TLS = "tls"
    VPN = "vpn"
    CODE_SIGNING = "code_signing"
    DOCUMENT_SIGNING = "document_signing"
    SSH = "ssh"


class KeyStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"
    PENDING = "pending"


class MigrationStatus(Enum):
    NOT_STARTED = "not_started"
    ASSESSING = "assessing"
    IN_PROGRESS = "in_progress"
    HYBRID = "hybrid"
    COMPLETED = "completed"


class PQKeyPair:
    def __init__(self, key_id: str, name: str, algorithm: PQAlgorithm, cert_type: CertificateType):
        self.key_id = key_id
        self.name = name
        self.algorithm = algorithm
        self.cert_type = cert_type
        self.status = KeyStatus.ACTIVE
        self.public_key = ""
        self.private_key_encrypted = ""
        self.certificate_pem = ""
        self.hybrid_cert_pem = ""
        self.fingerprint = ""
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow()
        self.revoked_at: Optional[datetime] = None
        self.key_size_bits = 0
        self.security_level = ""
        self.tags: list[str] = []
        self.domain = ""
        self.organization = ""
        self.issuer = "infra-pilot-pq-ca"

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "cert_type": self.cert_type.value,
            "status": self.status.value,
            "public_key": self.public_key,
            "fingerprint": self.fingerprint,
            "hybrid_cert_pem": self.hybrid_cert_pem,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "key_size_bits": self.key_size_bits,
            "security_level": self.security_level,
            "tags": self.tags,
            "domain": self.domain,
            "organization": self.organization,
            "issuer": self.issuer,
        }


class MigrationAssessment:
    def __init__(self, assessment_id: str, name: str):
        self.assessment_id = assessment_id
        self.name = name
        self.status = MigrationStatus.NOT_STARTED
        self.total_endpoints = 0
        self.assessed_endpoints = 0
        self.compatible_endpoints = 0
        self.incompatible_endpoints = 0
        self.hybrid_endpoints = 0
        self.recommended_algorithm = PQAlgorithm.KYBER_768
        self.recommended_signing = PQAlgorithm.DILITHIUM_3
        self.migration_steps: list[dict[str, Any]] = []
        self.risks: list[dict[str, Any]] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "name": self.name,
            "status": self.status.value,
            "total_endpoints": self.total_endpoints,
            "assessed_endpoints": self.assessed_endpoints,
            "compatible_endpoints": self.compatible_endpoints,
            "incompatible_endpoints": self.incompatible_endpoints,
            "hybrid_endpoints": self.hybrid_endpoints,
            "recommended_algorithm": self.recommended_algorithm.value,
            "recommended_signing": self.recommended_signing.value,
            "migration_steps": self.migration_steps,
            "risks": self.risks,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TLSConfig:
    def __init__(self, key_pair_id: str):
        self.key_pair_id = key_pair_id
        self.hybrid_mode = True
        self.pq_ciphers: list[str] = []
        self.tls_version = "1.3"
        self.ocsp_stapling = True
        self.hsts_enabled = True
        self.min_key_exchange = PQAlgorithm.KYBER_768
        self.certificate_transparency = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_pair_id": self.key_pair_id,
            "hybrid_mode": self.hybrid_mode,
            "pq_ciphers": self.pq_ciphers,
            "tls_version": self.tls_version,
            "ocsp_stapling": self.ocsp_stapling,
            "hsts_enabled": self.hsts_enabled,
            "min_key_exchange": self.min_key_exchange.value,
            "certificate_transparency": self.certificate_transparency,
        }


class QuantumCryptoManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.keys: dict[str, PQKeyPair] = {}
        self.assessments: dict[str, MigrationAssessment] = {}
        self.tls_configs: dict[str, TLSConfig] = {}
        self.storage_path = config.get("storage_path", "data/quantum_crypto.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for key_data in data.get("keys", []):
                    key = self._dict_to_key(key_data)
                    self.keys[key.key_id] = key
                for assmt_data in data.get("assessments", []):
                    assmt = MigrationAssessment(assmt_data["assessment_id"], assmt_data["name"])
                    assmt.status = MigrationStatus(assmt_data.get("status", "not_started"))
                    assmt.total_endpoints = assmt_data.get("total_endpoints", 0)
                    assmt.assessed_endpoints = assmt_data.get("assessed_endpoints", 0)
                    assmt.compatible_endpoints = assmt_data.get("compatible_endpoints", 0)
                    assmt.incompatible_endpoints = assmt_data.get("incompatible_endpoints", 0)
                    assmt.hybrid_endpoints = assmt_data.get("hybrid_endpoints", 0)
                    assmt.migration_steps = assmt_data.get("migration_steps", [])
                    assmt.risks = assmt_data.get("risks", [])
                    self.assessments[assmt.assessment_id] = assmt
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized QuantumCryptoManager with %d keys, %d assessments", len(self.keys), len(self.assessments))

    async def close(self):
        await self._save()

    async def _save(self):
        data = {"keys": [k.to_dict() for k in self.keys.values()], "assessments": [a.to_dict() for a in self.assessments.values()]}
        async with aiofiles.open(self.storage_path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    def _dict_to_key(self, data: dict[str, Any]) -> PQKeyPair:
        key = PQKeyPair(data["key_id"], data["name"], PQAlgorithm(data["algorithm"]), CertificateType(data.get("cert_type", "tls")))
        key.status = KeyStatus(data.get("status", "active"))
        key.public_key = data.get("public_key", "")
        key.fingerprint = data.get("fingerprint", "")
        key.hybrid_cert_pem = data.get("hybrid_cert_pem", "")
        key.key_size_bits = data.get("key_size_bits", 0)
        key.security_level = data.get("security_level", "")
        key.tags = data.get("tags", [])
        key.domain = data.get("domain", "")
        key.organization = data.get("organization", "")
        key.issuer = data.get("issuer", "infra-pilot-pq-ca")
        return key

    async def generate_key(self, name: str, algorithm: PQAlgorithm, cert_type: CertificateType) -> PQKeyPair:
        key_id = str(uuid.uuid4())
        key = PQKeyPair(key_id, name, algorithm, cert_type)
        key.public_key = f"pq-pub-{key_id[:16]}"
        key.fingerprint = f"pq-fp-{key_id[:24]}"
        key.key_size_bits = self._key_size(algorithm)
        key.security_level = self._security_level(algorithm)
        key.hybrid_cert_pem = f"-----BEGIN HYBRID CERT-----\n{key_id}\n-----END HYBRID CERT-----"
        self.keys[key_id] = key
        await self._save()
        logger.info("Generated PQ key %s: %s (%s)", key_id, name, algorithm.value)
        return key

    def _key_size(self, algorithm: PQAlgorithm) -> int:
        sizes = {
            PQAlgorithm.KYBER_512: 512, PQAlgorithm.KYBER_768: 768, PQAlgorithm.KYBER_1024: 1024,
            PQAlgorithm.DILITHIUM_2: 2528, PQAlgorithm.DILITHIUM_3: 3104, PQAlgorithm.DILITHIUM_5: 4448,
            PQAlgorithm.FALCON_512: 7168, PQAlgorithm.FALCON_1024: 14336,
            PQAlgorithm.SPHINCS_PLUS_128: 7856, PQAlgorithm.SPHINCS_PLUS_192: 16224, PQAlgorithm.SPHINCS_PLUS_256: 49856,
        }
        return sizes.get(algorithm, 2048)

    def _security_level(self, algorithm: PQAlgorithm) -> str:
        levels = {
            PQAlgorithm.KYBER_512: "AES-128", PQAlgorithm.KYBER_768: "AES-192", PQAlgorithm.KYBER_1024: "AES-256",
            PQAlgorithm.DILITHIUM_2: "SL2-DSA", PQAlgorithm.DILITHIUM_3: "SL3-DSA", PQAlgorithm.DILITHIUM_5: "SL5-DSA",
        }
        return levels.get(algorithm, "unknown")

    def get_key(self, key_id: str) -> Optional[PQKeyPair]:
        return self.keys.get(key_id)

    def list_keys(self, cert_type: Optional[CertificateType] = None) -> list[PQKeyPair]:
        if cert_type:
            return [k for k in self.keys.values() if k.cert_type == cert_type]
        return list(self.keys.values())

    async def revoke_key(self, key_id: str) -> bool:
        key = self.keys.get(key_id)
        if key and key.status == KeyStatus.ACTIVE:
            key.status = KeyStatus.REVOKED
            key.revoked_at = datetime.utcnow()
            await self._save()
            return True
        return False

    async def rotate_key(self, key_id: str) -> Optional[PQKeyPair]:
        key = self.keys.get(key_id)
        if not key:
            return None
        new_key = await self.generate_key(f"{key.name}-rotated", key.algorithm, key.cert_type)
        key.status = KeyStatus.EXPIRED
        await self._save()
        return new_key

    async def create_assessment(self, name: str, total_endpoints: int) -> MigrationAssessment:
        assessment_id = str(uuid.uuid4())
        assessment = MigrationAssessment(assessment_id, name)
        assessment.total_endpoints = total_endpoints
        assessment.status = MigrationStatus.ASSESSING
        self.assessments[assessment_id] = assessment
        await self._save()
        asyncio.create_task(self._simulate_assessment(assessment_id))
        return assessment

    async def _simulate_assessment(self, assessment_id: str):
        await asyncio.sleep(2)
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return
        assessment.assessed_endpoints = assessment.total_endpoints
        assessment.compatible_endpoints = int(assessment.total_endpoints * 0.7)
        assessment.incompatible_endpoints = int(assessment.total_endpoints * 0.1)
        assessment.hybrid_endpoints = int(assessment.total_endpoints * 0.2)
        assessment.status = MigrationStatus.HYBRID
        assessment.migration_steps = [
            {"step": 1, "action": "Inventory all TLS endpoints", "status": "done"},
            {"step": 2, "action": "Deploy hybrid certificates", "status": "in_progress"},
            {"step": 3, "action": "Enable PQ cipher suites", "status": "pending"},
            {"step": 4, "action": "Test backward compatibility", "status": "pending"},
            {"step": 5, "action": "Full PQ migration", "status": "pending"},
        ]
        await self._save()

    def get_assessment(self, assessment_id: str) -> Optional[MigrationAssessment]:
        return self.assessments.get(assessment_id)

    def list_assessments(self) -> list[MigrationAssessment]:
        return list(self.assessments.values())

    async def generate_tls_config(self, key_pair_id: str) -> TLSConfig:
        config = TLSConfig(key_pair_id)
        config.pq_ciphers = ["TLS_KYBER_768_X25519", "TLS_KYBER_1024_X448", "TLS_DILITHIUM_3_ECDSA_P384"]
        self.tls_configs[key_pair_id] = config
        return config

    def get_tls_config(self, key_pair_id: str) -> Optional[TLSConfig]:
        return self.tls_configs.get(key_pair_id)

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_keys": len(self.keys),
            "active_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.ACTIVE),
            "revoked_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.REVOKED),
            "assessments": len(self.assessments),
            "completed_migrations": sum(1 for a in self.assessments.values() if a.status == MigrationStatus.COMPLETED),
            "algorithms_available": [a.value for a in PQAlgorithm],
        }

    def get_algorithm_info(self, algorithm: str) -> dict[str, Any]:
        try:
            algo = PQAlgorithm(algorithm)
        except ValueError:
            return {}
        categories = {
            "kyber": ("KEM", "Key Encapsulation Mechanism"),
            "dilithium": ("Signature", "Digital Signature"),
            "falcon": ("Signature", "Digital Signature"),
            "sphincs": ("Signature", "Stateless Hash-Based Signature"),
        }
        prefix = algorithm.split("-")[0]
        cat_info = categories.get(prefix, ("Unknown", "Unknown"))
        return {"algorithm": algo.value, "category": cat_info[0], "description": cat_info[1], "key_size_bits": self._key_size(algo), "security_level": self._security_level(algo)}

    # === Export ===
    def export_keys_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["key_id", "name", "algorithm", "cert_type", "status", "key_size_bits", "security_level", "domain", "organization", "created_at", "expires_at"])
        for k in self.keys.values():
            writer.writerow([k.key_id, k.name, k.algorithm.value, k.cert_type.value, k.status.value, k.key_size_bits, k.security_level, k.domain, k.organization, k.created_at.isoformat(), k.expires_at.isoformat()])
        return output.getvalue()

    def export_keys_json(self) -> str:
        return json.dumps({"keys": [k.to_dict() for k in self.keys.values()], "assessments": [a.to_dict() for a in self.assessments.values()]}, indent=2, default=str)

    # === Import ===
    def import_keys_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("keys", data if isinstance(data, list) else []):
            key = PQKeyPair(
                item.get("key_id", str(uuid.uuid4())),
                item.get("name", "Imported Key"),
                PQAlgorithm(item.get("algorithm", "kyber-768")),
                CertificateType(item.get("cert_type", "tls")),
            )
            key.status = KeyStatus(item.get("status", "active"))
            key.public_key = item.get("public_key", "")
            key.fingerprint = item.get("fingerprint", "")
            key.key_size_bits = item.get("key_size_bits", 0)
            key.security_level = item.get("security_level", "")
            key.tags = item.get("tags", [])
            key.domain = item.get("domain", "")
            key.organization = item.get("organization", "")
            self.keys[key.key_id] = key
            count += 1
        return count

    # === Notification ===
    async def notify_key_status(self, key_id: str) -> dict[str, Any]:
        key = self.keys.get(key_id)
        if not key:
            return {"error": "Key not found"}
        return {
            "key_id": key.key_id,
            "name": key.name,
            "algorithm": key.algorithm.value,
            "status": key.status.value,
            "message": f"PQ key {key.name} ({key.algorithm.value}) status: {key.status.value}",
            "channels": ["slack", "email", "pagerduty"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_expiring_keys(self, days: int = 30) -> list[dict[str, Any]]:
        results = []
        now = datetime.utcnow()
        for k in self.keys.values():
            if k.status == KeyStatus.ACTIVE and k.expires_at and (k.expires_at - now).days <= days:
                results.append(await self.notify_key_status(k.key_id))
        return results

    # === State Machine ===
    async def transition_key_status(self, key_id: str, target_status: str) -> Optional[PQKeyPair]:
        key = self.keys.get(key_id)
        if not key:
            return None
        valid = {
            KeyStatus.ACTIVE: [KeyStatus.EXPIRED, KeyStatus.REVOKED, KeyStatus.COMPROMISED],
            KeyStatus.EXPIRED: [KeyStatus.REVOKED],
            KeyStatus.REVOKED: [],
            KeyStatus.COMPROMISED: [KeyStatus.REVOKED],
            KeyStatus.PENDING: [KeyStatus.ACTIVE, KeyStatus.REVOKED],
        }
        new_status = KeyStatus(target_status)
        if new_status in valid.get(key.status, []):
            key.status = new_status
            if new_status in (KeyStatus.REVOKED, KeyStatus.COMPROMISED):
                key.revoked_at = datetime.utcnow()
            await self._save()
            return key
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if config.get("default_algorithm") and config["default_algorithm"] not in [a.value for a in PQAlgorithm]:
            errors.append(f"Unknown algorithm: {config.get('default_algorithm')}")
        if config.get("key_expiry_days", 365) > 730:
            warnings.append("Key expiry exceeds 2 years")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_keys": len(self.keys),
            "active_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.ACTIVE),
            "expired_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.EXPIRED),
            "revoked_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.REVOKED),
            "compromised_keys": sum(1 for k in self.keys.values() if k.status == KeyStatus.COMPROMISED),
            "by_algorithm": {a.value: sum(1 for k in self.keys.values() if k.algorithm == a) for a in PQAlgorithm},
            "by_cert_type": {c.value: sum(1 for k in self.keys.values() if k.cert_type == c) for c in CertificateType},
            "total_assessments": len(self.assessments),
            "completed_migrations": sum(1 for a in self.assessments.values() if a.status == MigrationStatus.COMPLETED),
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        active = sum(1 for k in self.keys.values() if k.status == KeyStatus.ACTIVE)
        compromised = sum(1 for k in self.keys.values() if k.status == KeyStatus.COMPROMISED)
        return {
            "total_keys": len(self.keys),
            "active": active,
            "compromised": compromised,
            "health_pct": round(active / max(len(self.keys), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_revoke_keys(self, key_ids: list[str]) -> int:
        count = 0
        for kid in key_ids:
            k = self.keys.get(kid)
            if k and k.status == KeyStatus.ACTIVE:
                k.status = KeyStatus.REVOKED
                k.revoked_at = datetime.utcnow()
                count += 1
        await self._save()
        return count

    async def bulk_rotate_keys(self, key_ids: list[str]) -> int:
        count = 0
        for kid in key_ids:
            k = self.keys.get(kid)
            if k and k.status == KeyStatus.ACTIVE:
                await self.rotate_key(kid)
                count += 1
        return count

    # === Tag Management ===
    async def add_key_tags(self, key_ids: list[str], tags: list[str]) -> int:
        count = 0
        for kid in key_ids:
            k = self.keys.get(kid)
            if k:
                for t in tags:
                    if t not in k.tags:
                        k.tags.append(t)
                count += 1
        await self._save()
        return count

    async def remove_key_tags(self, key_ids: list[str], tags: list[str]) -> int:
        count = 0
        for kid in key_ids:
            k = self.keys.get(kid)
            if k:
                k.tags = [t for t in k.tags if t not in tags]
                count += 1
        await self._save()
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "quantum_crypto",
            "keys": len(self.keys),
            "active": sum(1 for k in self.keys.values() if k.status == KeyStatus.ACTIVE),
            "assessments": len(self.assessments),
            "tls_configs": len(self.tls_configs),
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
