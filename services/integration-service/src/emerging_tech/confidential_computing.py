"""Confidential Computing Enclave — manage Intel SGX/AMD SEV/ARM TrustZone enclaves."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnclaveTechnology(Enum):
    INTEL_SGX = "intel_sgx"
    AMD_SEV = "amd_sev"
    AMD_SEV_SNP = "amd_sev_snp"
    ARM_TRUSTZONE = "arm_trustzone"
    NVIDIA_GPU = "nvidia_gpu_tee"


class EnclaveStatus(Enum):
    CREATING = "creating"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    ERROR = "error"


class AttestationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class EnclaveMemoryEncryption(Enum):
    MKTME = "mktme"
    SME = "sme"
    SEV_ES = "sev_es"
    SEV_SNP = "sev_snp"
    NONE = "none"


class Enclave:
    def __init__(self, enclave_id: str, name: str, technology: EnclaveTechnology):
        self.enclave_id = enclave_id
        self.name = name
        self.technology = technology
        self.status = EnclaveStatus.CREATING
        self.memory_mb = 256
        self.cpu_cores = 2
        self.encrypted_memory = True
        self.memory_encryption = EnclaveMemoryEncryption.MKTME
        self.attestation_status = AttestationStatus.PENDING
        self.attestation_report = ""
        self.measurement_hash = ""
        self.signer_mrsigner = ""
        self.product_id = 0
        self.security_version = 1
        self.image = ""
        self.container_id = ""
        self.host_node = ""
        self.encryption_keys: list[str] = []
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "enclave_id": self.enclave_id, "name": self.name,
            "technology": self.technology.value, "status": self.status.value,
            "memory_mb": self.memory_mb, "cpu_cores": self.cpu_cores,
            "encrypted_memory": self.encrypted_memory,
            "memory_encryption": self.memory_encryption.value,
            "attestation_status": self.attestation_status.value,
            "attestation_report": self.attestation_report,
            "measurement_hash": self.measurement_hash,
            "signer_mrsigner": self.signer_mrsigner,
            "product_id": self.product_id, "security_version": self.security_version,
            "image": self.image, "container_id": self.container_id,
            "host_node": self.host_node, "encryption_keys": self.encryption_keys,
            "tags": self.tags, "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(), "metadata": self.metadata,
        }


class AttestationEvidence:
    def __init__(self, evidence_id: str, enclave_id: str):
        self.evidence_id = evidence_id
        self.enclave_id = enclave_id
        self.report = ""
        self.signature = ""
        self.signer_public_key = ""
        self.timestamp = datetime.utcnow()
        self.verified = False
        self.verifier = ""
        self.verification_result: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id, "enclave_id": self.enclave_id,
            "report": self.report[:64] + "...",
            "timestamp": self.timestamp.isoformat(),
            "verified": self.verified, "verifier": self.verifier,
            "verification_result": self.verification_result,
        }


class SecureDataProcessing:
    def __init__(self, processing_id: str, enclave_id: str, name: str):
        self.processing_id = processing_id
        self.enclave_id = enclave_id
        self.name = name
        self.input_data_hash = ""
        self.output_data_hash = ""
        self.processed_at = datetime.utcnow()
        self.duration_ms = 0
        self.status = "pending"
        self.error_message = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "processing_id": self.processing_id, "enclave_id": self.enclave_id,
            "name": self.name, "input_data_hash": self.input_data_hash,
            "output_data_hash": self.output_data_hash,
            "processed_at": self.processed_at.isoformat(),
            "duration_ms": self.duration_ms, "status": self.status,
            "error_message": self.error_message,
        }


class ConfidentialComputingManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enclaves: dict[str, Enclave] = {}
        self.evidences: dict[str, AttestationEvidence] = {}
        self.processings: dict[str, SecureDataProcessing] = {}
        self.storage_path = config.get("storage_path", "data/confidential_computing.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for e_data in data.get("enclaves", []):
                    e = self._dict_to_enclave(e_data)
                    self.enclaves[e.enclave_id] = e
                for ev_data in data.get("evidences", []):
                    ev = AttestationEvidence(ev_data["evidence_id"], ev_data["enclave_id"])
                    self.evidences[ev.evidence_id] = ev
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized ConfidentialComputingManager with %d enclaves", len(self.enclaves))

    async def close(self):
        self._save()

    def _save(self):
        data = {"enclaves": [e.to_dict() for e in self.enclaves.values()], "evidences": [ev.to_dict() for ev in self.evidences.values()]}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _dict_to_enclave(self, data: dict[str, Any]) -> Enclave:
        e = Enclave(data["enclave_id"], data["name"], EnclaveTechnology(data["technology"]))
        e.status = EnclaveStatus(data.get("status", "creating"))
        e.memory_mb = data.get("memory_mb", 256)
        e.cpu_cores = data.get("cpu_cores", 2)
        e.encrypted_memory = data.get("encrypted_memory", True)
        e.attestation_status = AttestationStatus(data.get("attestation_status", "pending"))
        e.measurement_hash = data.get("measurement_hash", "")
        e.image = data.get("image", "")
        e.container_id = data.get("container_id", "")
        e.host_node = data.get("host_node", "")
        e.tags = data.get("tags", [])
        e.metadata = data.get("metadata", {})
        return e

    async def create_enclave(self, name: str, technology: EnclaveTechnology, memory_mb: int = 256, cpu_cores: int = 2) -> Enclave:
        enclave_id = str(uuid.uuid4())
        enclave = Enclave(enclave_id, name, technology)
        enclave.memory_mb = memory_mb
        enclave.cpu_cores = cpu_cores
        enclave.measurement_hash = f"mr-enclave-{uuid.uuid4().hex[:32]}"
        enclave.signer_mrsigner = f"mr-signer-{uuid.uuid4().hex[:32]}"
        self.enclaves[enclave_id] = enclave
        self._save()
        asyncio.create_task(self._simulate_enclave_creation(enclave_id))
        logger.info("Creating %s enclave: %s (%d MB, %d cores)", technology.value, name, memory_mb, cpu_cores)
        return enclave

    async def _simulate_enclave_creation(self, enclave_id: str):
        await asyncio.sleep(2)
        enclave = self.enclaves.get(enclave_id)
        if not enclave:
            return
        enclave.status = EnclaveStatus.RUNNING
        enclave.attestation_status = AttestationStatus.VERIFIED
        enclave.attestation_report = f"attestation-{enclave_id[:16]}"
        self._save()

    def get_enclave(self, enclave_id: str) -> Optional[Enclave]:
        return self.enclaves.get(enclave_id)

    def list_enclaves(self, technology: Optional[EnclaveTechnology] = None) -> list[Enclave]:
        if technology:
            return [e for e in self.enclaves.values() if e.technology == technology]
        return list(self.enclaves.values())

    async def stop_enclave(self, enclave_id: str) -> bool:
        enclave = self.enclaves.get(enclave_id)
        if enclave and enclave.status in (EnclaveStatus.RUNNING, EnclaveStatus.INITIALIZING):
            enclave.status = EnclaveStatus.STOPPED
            self._save()
            return True
        return False

    async def start_enclave(self, enclave_id: str) -> bool:
        enclave = self.enclaves.get(enclave_id)
        if enclave and enclave.status == EnclaveStatus.STOPPED:
            enclave.status = EnclaveStatus.INITIALIZING
            self._save()
            asyncio.create_task(self._simulate_enclave_creation(enclave_id))
            return True
        return False

    async def terminate_enclave(self, enclave_id: str) -> bool:
        if enclave_id in self.enclaves:
            self.enclaves[enclave_id].status = EnclaveStatus.TERMINATED
            del self.enclaves[enclave_id]
            self._save()
            return True
        return False

    async def verify_attestation(self, enclave_id: str) -> Optional[AttestationEvidence]:
        enclave = self.enclaves.get(enclave_id)
        if not enclave:
            return None
        evidence_id = str(uuid.uuid4())
        evidence = AttestationEvidence(evidence_id, enclave_id)
        evidence.report = enclave.attestation_report
        evidence.verified = True
        evidence.verifier = "infra-pilot-attestation-service"
        evidence.verification_result = {
            "is_valid": True,
            "measurement_match": True,
            "signer_trusted": True,
            "security_version_ok": True,
            "timestamp_valid": True,
        }
        enclave.attestation_status = AttestationStatus.VERIFIED
        self.evidences[evidence_id] = evidence
        self._save()
        return evidence

    def get_attestation(self, evidence_id: str) -> Optional[AttestationEvidence]:
        return self.evidences.get(evidence_id)

    def list_attestations(self, enclave_id: Optional[str] = None) -> list[AttestationEvidence]:
        if enclave_id:
            return [ev for ev in self.evidences.values() if ev.enclave_id == enclave_id]
        return list(self.evidences.values())

    async def process_secure_data(self, enclave_id: str, name: str, input_hash: str) -> SecureDataProcessing:
        processing_id = str(uuid.uuid4())
        proc = SecureDataProcessing(processing_id, enclave_id, name)
        proc.input_data_hash = input_hash
        proc.status = "processing"
        self.processings[processing_id] = proc
        await asyncio.sleep(1)
        proc.status = "completed"
        proc.output_data_hash = f"output-{uuid.uuid4().hex[:32]}"
        proc.duration_ms = 1500
        return proc

    def get_secure_processings(self, enclave_id: Optional[str] = None) -> list[SecureDataProcessing]:
        if enclave_id:
            return [p for p in self.processings.values() if p.enclave_id == enclave_id]
        return list(self.processings.values())

    def get_platform_support(self, technology: str) -> dict[str, Any]:
        support_info = {
            "intel_sgx": {"hardware": "Intel Xeon E3/E5/E7, Core i5/i7/i9 (6th gen+)", "memory_max_mb": 512, "os": "Linux, Windows", "driver": "SGX DCAP"},
            "amd_sev": {"hardware": "AMD EPYC 7002+", "memory_max_mb": 81920, "os": "Linux", "driver": "SEV kernel module"},
            "amd_sev_snp": {"hardware": "AMD EPYC 9004+", "memory_max_mb": 524288, "os": "Linux 6.0+", "driver": "SEV-SNP kernel module"},
            "arm_trustzone": {"hardware": "ARM Cortex-A cores", "memory_max_mb": 32, "os": "OP-TEE, Trusty", "driver": "TrustZone driver"},
            "nvidia_gpu_tee": {"hardware": "NVIDIA H100, A100", "memory_max_mb": 81920, "os": "Linux", "driver": "NVIDIA Confidential Computing"},
        }
        return support_info.get(technology, {})

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_enclaves": len(self.enclaves),
            "running_enclaves": sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING),
            "verified_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED),
            "total_processings": len(self.processings),
            "by_technology": {t.value: sum(1 for e in self.enclaves.values() if e.technology == t) for t in EnclaveTechnology},
        }

    # === Export ===
    def export_enclaves_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "technology", "status", "attestation", "memory_mb", "cpu_cores", "created_at"])
        for e in self.enclaves.values():
            writer.writerow([e.id, e.name, e.technology.value, e.status.value, e.attestation_status.value, e.memory_mb, e.cpu_cores, e.created_at.isoformat()])
        return output.getvalue()

    def export_enclaves_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.enclaves.values()], indent=2, default=str)

    # === Import ===
    def import_enclaves_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            enclave = ConfidentialEnclave(
                id=item.get("id", str(uuid.uuid4())),
                name=item.get("name", "Imported Enclave"),
                technology=EnclaveTechnology(item.get("technology", "intel_sgx")),
                status=EnclaveStatus(item.get("status", "provisioning")),
                attestation_status=AttestationStatus(item.get("attestation_status", "pending")),
                memory_mb=item.get("memory_mb", 128),
                cpu_cores=item.get("cpu_cores", 2),
                enclave_measurement=item.get("enclave_measurement", ""),
                security_version_number=item.get("security_version_number", 1),
            )
            self.enclaves[enclave.id] = enclave
            count += 1
        return count

    # === Notification ===
    async def notify_attestation_status(self, enclave_id: str) -> Dict[str, Any]:
        enclave = self.enclaves.get(enclave_id)
        if not enclave:
            return {"error": "Enclave not found"}
        return {
            "enclave_id": enclave.id,
            "name": enclave.name,
            "technology": enclave.technology.value,
            "attestation": enclave.attestation_status.value,
            "message": f"Enclave {enclave.name} attestation: {enclave.attestation_status.value}",
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_failed_attestations(self) -> List[Dict]:
        results = []
        for e in self.enclaves.values():
            if e.attestation_status == AttestationStatus.FAILED:
                results.append(await self.notify_attestation_status(e.id))
        return results

    # === State Machine ===
    def transition_enclave_status(self, enclave_id: str, target_status: str) -> Optional[ConfidentialEnclave]:
        enclave = self.enclaves.get(enclave_id)
        if not enclave:
            return None
        valid = {
            EnclaveStatus.PROVISIONING: [EnclaveStatus.RUNNING, EnclaveStatus.FAILED],
            EnclaveStatus.RUNNING: [EnclaveStatus.STOPPED, EnclaveStatus.ATTESTING],
            EnclaveStatus.ATTESTING: [EnclaveStatus.RUNNING, EnclaveStatus.FAILED],
            EnclaveStatus.STOPPED: [EnclaveStatus.RUNNING],
            EnclaveStatus.FAILED: [EnclaveStatus.PROVISIONING],
        }
        new_status = EnclaveStatus(target_status)
        if new_status in valid.get(enclave.status, []):
            enclave.status = new_status
            return enclave
        return None

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("technology"):
            errors.append("Enclave technology is required")
        if config.get("technology") and config["technology"] not in [t.value for t in EnclaveTechnology]:
            errors.append(f"Unknown technology: {config.get('technology')}")
        if config.get("memory_mb", 128) > 524288:
            warnings.append("Memory allocation exceeds 512GB")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> Dict:
        total_memory = sum(e.memory_mb for e in self.enclaves.values())
        total_cores = sum(e.cpu_cores for e in self.enclaves.values())
        return {
            "total_memory_mb": total_memory,
            "total_cpu_cores": total_cores,
            "avg_memory_per_enclave": round(total_memory / len(self.enclaves), 1) if self.enclaves else 0,
            "verified_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED),
            "failed_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.FAILED),
            "by_technology": {t.value: sum(1 for e in self.enclaves.values() if e.technology == t) for t in EnclaveTechnology},
        }

    # === Bulk Operations ===
    async def bulk_start_enclaves(self, enclave_ids: List[str]) -> int:
        count = 0
        for eid in enclave_ids:
            e = self.enclaves.get(eid)
            if e and e.status == EnclaveStatus.STOPPED:
                e.status = EnclaveStatus.RUNNING
                count += 1
        return count

    async def bulk_stop_enclaves(self, enclave_ids: List[str]) -> int:
        count = 0
        for eid in enclave_ids:
            e = self.enclaves.get(eid)
            if e and e.status == EnclaveStatus.RUNNING:
                e.status = EnclaveStatus.STOPPED
                count += 1
        return count

    async def bulk_request_attestations(self, enclave_ids: List[str]) -> int:
        count = 0
        for eid in enclave_ids:
            e = self.enclaves.get(eid)
            if e and e.attestation_status != AttestationStatus.VERIFIED:
                e.attestation_status = AttestationStatus.VERIFIED
                count += 1
        return count

    # === Tag Management ===
    def add_enclave_tags(self, enclave_ids: List[str], tags: List[str]) -> int:
        count = 0
        for eid in enclave_ids:
            e = self.enclaves.get(eid)
            if e:
                for t in tags:
                    if t not in e.tags:
                        e.tags.append(t)
                count += 1
        return count

    def remove_enclave_tags(self, enclave_ids: List[str], tags: List[str]) -> int:
        count = 0
        for eid in enclave_ids:
            e = self.enclaves.get(eid)
            if e:
                e.tags = [t for t in e.tags if t not in tags]
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "confidential_computing",
            "initialized": self._initialized,
            "enclaves": len(self.enclaves),
            "running": sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING),
            "verified_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED),
            "total_processings": len(self.processings),
            "status": "healthy" if self._initialized else "not_initialized",
        }

    # === Alert Management ===
    def create_alert_rule(self, name: str, metric: str, threshold: float, severity: str = "warning") -> dict[str, Any]:
        rule_id = str(uuid.uuid4())
        rule = {"rule_id": rule_id, "name": name, "metric": metric, "threshold": threshold,
                "severity": severity, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_alert_rules"):
            self._alert_rules: dict[str, dict[str, Any]] = {}
        self._alert_rules[rule_id] = rule
        return rule

    def get_alert_rules(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_alert_rules", {}).values())

    def toggle_alert_rule(self, rule_id: str, enabled: bool) -> bool:
        rules = getattr(self, "_alert_rules", {})
        if rule_id in rules:
            rules[rule_id]["enabled"] = enabled
            return True
        return False

    def evaluate_alert_rules(self) -> list[dict[str, Any]]:
        triggered = []
        for rule in getattr(self, "_alert_rules", {}).values():
            if not rule["enabled"]:
                continue
            if rule["metric"] == "failed_attestations":
                value = sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.FAILED)
            elif rule["metric"] == "enclave_count":
                value = len(self.enclaves)
            elif rule["metric"] == "memory_usage":
                value = sum(e.memory_mb for e in self.enclaves.values())
            else:
                continue
            if value > rule["threshold"]:
                triggered.append({"rule_id": rule["rule_id"], "name": rule["name"],
                                  "current_value": value, "threshold": rule["threshold"],
                                  "triggered_at": datetime.utcnow().isoformat()})
        return triggered

    # === Lifecycle Management ===
    def set_lifecycle_policy(self, max_idle_hours: int = 72, auto_stop: bool = True) -> dict[str, Any]:
        policy_id = str(uuid.uuid4())
        policy = {"policy_id": policy_id, "max_idle_hours": max_idle_hours, "auto_stop": auto_stop,
                   "created_at": datetime.utcnow().isoformat(), "status": "active"}
        if not hasattr(self, "_lifecycle_policies"):
            self._lifecycle_policies: list[dict[str, Any]] = []
        self._lifecycle_policies.append(policy)
        return policy

    def get_lifecycle_policies(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_lifecycle_policies", []))

    def apply_lifecycle_policies(self) -> dict[str, Any]:
        stopped = 0
        for policy in getattr(self, "_lifecycle_policies", []):
            if policy["status"] != "active":
                continue
            for e in self.enclaves.values():
                if e.status == EnclaveStatus.RUNNING:
                    idle_hours = (datetime.utcnow() - e.created_at).total_seconds() / 3600
                    if idle_hours > policy["max_idle_hours"] and policy["auto_stop"]:
                        e.status = EnclaveStatus.STOPPED
                        stopped += 1
        return {"stopped": stopped}

    # === Backup ===
    def backup_enclave_config(self, enclave_id: str) -> dict[str, Any] | None:
        e = self.enclaves.get(enclave_id)
        if not e:
            return None
        backup_id = str(uuid.uuid4())
        backup = {"backup_id": backup_id, "enclave_id": enclave_id, "technology": e.technology.value,
                  "memory_mb": e.memory_mb, "cpu_cores": e.cpu_cores, "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_backups"):
            self._backups: dict[str, list[dict[str, Any]]] = {}
        if enclave_id not in self._backups:
            self._backups[enclave_id] = []
        self._backups[enclave_id].append(backup)
        return backup

    def list_backups(self, enclave_id: str = "") -> list[dict[str, Any]]:
        backups = getattr(self, "_backups", {})
        if enclave_id:
            return backups.get(enclave_id, [])
        result = []
        for bk_list in backups.values():
            result.extend(bk_list)
        return result

    # === Reporting ===
    def generate_report(self, report_type: str = "summary") -> dict[str, Any]:
        if report_type == "summary":
            return {"enclaves": len(self.enclaves), "running": sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING),
                    "total_memory_mb": sum(e.memory_mb for e in self.enclaves.values()),
                    "verified_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED),
                    "total_processings": len(self.processings)}
        elif report_type == "compliance":
            verified = sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED)
            total = len(self.enclaves)
            return {"compliance_pct": round(verified / max(total, 1) * 100, 1), "verified": verified, "total": total}
        return {}

    def export_enclave_data(self, format: str = "json") -> Any:
        if format == "csv":
            lines = ["id,technology,status,memory_mb,cpu_cores,attestation_status,created_at"]
            for e in self.enclaves.values():
                lines.append(f"{e.enclave_id},{e.technology.value},{e.status.value},{e.memory_mb},{e.cpu_cores},{e.attestation_status.value},{e.created_at.isoformat()}")
            return "\n".join(lines)
        return {"enclaves": [e.to_dict() for e in self.enclaves.values()]}

    # === Dashboard ===
    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "enclave_count": len(self.enclaves),
            "running_count": sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING),
            "total_memory_mb": sum(e.memory_mb for e in self.enclaves.values()),
            "total_cpu_cores": sum(e.cpu_cores for e in self.enclaves.values()),
            "verified_attestations": sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED),
            "total_processings": len(self.processings),
            "health_snapshot": self.get_analytics(),
        }

    # === Scheduling ===
    def schedule_attestation_check(self, enclave_ids: list[str], interval_hours: int = 24) -> dict[str, Any]:
        schedule_id = str(uuid.uuid4())
        schedule = {"schedule_id": schedule_id, "enclave_ids": enclave_ids, "interval_hours": interval_hours,
                    "next_run": (datetime.utcnow() + timedelta(hours=interval_hours)).isoformat(),
                    "status": "active", "created_at": datetime.utcnow().isoformat()}
        if not hasattr(self, "_schedules"):
            self._schedules: list[dict[str, Any]] = []
        self._schedules.append(schedule)
        return schedule

    def get_schedules(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_schedules", []))

    def cancel_schedule(self, schedule_id: str) -> bool:
        for s in getattr(self, "_schedules", []):
            if s["schedule_id"] == schedule_id:
                s["status"] = "cancelled"
                return True
        return False

    # === Compliance ===
    def run_compliance_check(self) -> dict[str, Any]:
        total = len(self.enclaves)
        attested = sum(1 for e in self.enclaves.values() if e.attestation_status == AttestationStatus.VERIFIED)
        running_attested = sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING and e.attestation_status == AttestationStatus.VERIFIED)
        return {"total_enclaves": total, "attested": attested, "running_attested": running_attested,
                "compliance_pct": round(attested / max(total, 1) * 100, 1),
                "secure_running_pct": round(running_attested / max(sum(1 for e in self.enclaves.values() if e.status == EnclaveStatus.RUNNING), 1) * 100, 1)}

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
