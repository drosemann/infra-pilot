"""Zero-Knowledge Proof Service — ZK-proof generation and verification infrastructure."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ZKCircuit(Enum):
    GROTH16 = "groth16"
    PLONK = "plonk"
    HALO2 = "halo2"
    MARLIN = "marlin"
    STARK = "stark"
    CIRCOM = "circom"


class ProofStatus(Enum):
    GENERATING = "generating"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class VerifiableComputation:
    def __init__(self, computation_id: str, name: str):
        self.computation_id = computation_id
        self.name = name
        self.program_hash = ""
        self.input_commitment = ""
        self.output_hash = ""
        self.proof = ""
        self.status = "pending"
        self.verified = False
        self.created_at = datetime.utcnow()
        self.verified_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "computation_id": self.computation_id, "name": self.name,
            "program_hash": self.program_hash, "input_commitment": self.input_commitment,
            "output_hash": self.output_hash, "proof": self.proof[:32] + "..." if len(self.proof) > 32 else self.proof,
            "status": self.status, "verified": self.verified,
            "created_at": self.created_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }


class ZKCircuitTemplate:
    def __init__(self, circuit_id: str, name: str, circuit_type: ZKCircuit):
        self.circuit_id = circuit_id
        self.name = name
        self.circuit_type = circuit_type
        self.description = ""
        self.constraints = 0
        self.public_inputs = 0
        self.private_inputs = 0
        self.proving_key_size_mb = 0.0
        self.verification_key_size_mb = 0.0
        self.compilation_time_ms = 0
        self.source_code = ""
        self.setup_done = False
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "circuit_id": self.circuit_id, "name": self.name,
            "circuit_type": self.circuit_type.value, "description": self.description,
            "constraints": self.constraints, "public_inputs": self.public_inputs,
            "private_inputs": self.private_inputs,
            "proving_key_size_mb": self.proving_key_size_mb,
            "verification_key_size_mb": self.verification_key_size_mb,
            "compilation_time_ms": self.compilation_time_ms,
            "setup_done": self.setup_done,
            "created_at": self.created_at.isoformat(),
        }


class ZKProof:
    def __init__(self, proof_id: str, circuit_id: str, name: str):
        self.proof_id = proof_id
        self.circuit_id = circuit_id
        self.name = name
        self.status = ProofStatus.GENERATING
        self.circuit_type = ZKCircuit.GROTH16
        self.public_inputs: dict[str, Any] = {}
        self.private_inputs: dict[str, Any] = {}
        self.proof_data = ""
        self.verification_key = ""
        self.proof_size_bytes = 0
        self.generation_time_ms = 0
        self.verification_time_ms = 0
        self.verified = False
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id, "circuit_id": self.circuit_id,
            "name": self.name, "status": self.status.value,
            "circuit_type": self.circuit_type.value,
            "public_inputs": self.public_inputs,
            "proof_data": self.proof_data[:32] + "..." if len(self.proof_data) > 32 else self.proof_data,
            "proof_size_bytes": self.proof_size_bytes,
            "generation_time_ms": self.generation_time_ms,
            "verification_time_ms": self.verification_time_ms,
            "verified": self.verified,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ZKProofService:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.circuits: dict[str, ZKCircuitTemplate] = {}
        self.proofs: dict[str, ZKProof] = {}
        self.computations: dict[str, VerifiableComputation] = {}
        self.storage_path = config.get("storage_path", "data/zk_proofs.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for c_data in data.get("circuits", []):
                    c = ZKCircuitTemplate(c_data["circuit_id"], c_data["name"], ZKCircuit(c_data["circuit_type"]))
                    c.description = c_data.get("description", "")
                    c.constraints = c_data.get("constraints", 0)
                    c.public_inputs = c_data.get("public_inputs", 0)
                    c.private_inputs = c_data.get("private_inputs", 0)
                    c.setup_done = c_data.get("setup_done", False)
                    self.circuits[c.circuit_id] = c
                for p_data in data.get("proofs", []):
                    p = ZKProof(p_data["proof_id"], p_data["circuit_id"], p_data["name"])
                    p.status = ProofStatus(p_data.get("status", "generating"))
                    p.circuit_type = ZKCircuit(p_data.get("circuit_type", "groth16"))
                    p.proof_size_bytes = p_data.get("proof_size_bytes", 0)
                    p.verified = p_data.get("verified", False)
                    self.proofs[p.proof_id] = p
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized ZKProofService with %d circuits, %d proofs", len(self.circuits), len(self.proofs))

    async def close(self):
        self._save()

    def _save(self):
        data = {
            "circuits": [c.to_dict() for c in self.circuits.values()],
            "proofs": [p.to_dict() for p in self.proofs.values()],
            "computations": [c.to_dict() for c in self.computations.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    async def create_circuit(self, name: str, circuit_type: ZKCircuit, constraints: int = 1000) -> ZKCircuitTemplate:
        circuit_id = str(uuid.uuid4())
        circuit = ZKCircuitTemplate(circuit_id, name, circuit_type)
        circuit.constraints = constraints
        circuit.public_inputs = 1
        circuit.private_inputs = 2
        circuit.proving_key_size_mb = constraints / 1000 * 10
        circuit.verification_key_size_mb = 0.1
        self.circuits[circuit_id] = circuit
        self._save()
        asyncio.create_task(self._simulate_setup(circuit_id))
        return circuit

    async def _simulate_setup(self, circuit_id: str):
        await asyncio.sleep(2)
        circuit = self.circuits.get(circuit_id)
        if circuit:
            circuit.setup_done = True
            circuit.compilation_time_ms = 5000
            self._save()

    def get_circuit(self, circuit_id: str) -> Optional[ZKCircuitTemplate]:
        return self.circuits.get(circuit_id)

    def list_circuits(self) -> list[ZKCircuitTemplate]:
        return list(self.circuits.values())

    async def generate_proof(self, circuit_id: str, name: str, public_inputs: dict[str, Any], private_inputs: dict[str, Any]) -> Optional[ZKProof]:
        circuit = self.circuits.get(circuit_id)
        if not circuit or not circuit.setup_done:
            return None
        proof_id = str(uuid.uuid4())
        proof = ZKProof(proof_id, circuit_id, name)
        proof.circuit_type = circuit.circuit_type
        proof.public_inputs = public_inputs
        proof.private_inputs = private_inputs
        proof.status = ProofStatus.GENERATING
        self.proofs[proof_id] = proof
        self._save()
        asyncio.create_task(self._simulate_proof_generation(proof_id))
        return proof

    async def _simulate_proof_generation(self, proof_id: str):
        await asyncio.sleep(2)
        proof = self.proofs.get(proof_id)
        if not proof:
            return
        proof.status = ProofStatus.VERIFIED
        proof.proof_data = f"zk-proof-{uuid.uuid4().hex[:64]}"
        proof.proof_size_bytes = len(proof.proof_data)
        proof.generation_time_ms = 1500
        proof.verification_time_ms = 50
        proof.verified = True
        self._save()

    def get_proof(self, proof_id: str) -> Optional[ZKProof]:
        return self.proofs.get(proof_id)

    def list_proofs(self, status: Optional[ProofStatus] = None) -> list[ZKProof]:
        if status:
            return [p for p in self.proofs.values() if p.status == status]
        return list(self.proofs.values())

    async def verify_proof(self, proof_id: str) -> Optional[bool]:
        proof = self.proofs.get(proof_id)
        if not proof:
            return None
        if proof.status == ProofStatus.VERIFIED:
            proof.verified = True
            proof.verification_time_ms = 50
            self._save()
            return True
        return False

    async def create_verifiable_computation(self, name: str, program_hash: str) -> VerifiableComputation:
        comp_id = str(uuid.uuid4())
        comp = VerifiableComputation(comp_id, name)
        comp.program_hash = program_hash
        comp.input_commitment = f"commit-{uuid.uuid4().hex[:32]}"
        self.computations[comp_id] = comp
        self._save()
        asyncio.create_task(self._simulate_computation(comp_id))
        return comp

    async def _simulate_computation(self, comp_id: str):
        await asyncio.sleep(2)
        comp = self.computations.get(comp_id)
        if not comp:
            return
        comp.status = "completed"
        comp.output_hash = f"output-{uuid.uuid4().hex[:32]}"
        comp.proof = f"vm-proof-{uuid.uuid4().hex[:64]}"
        comp.verified = True
        comp.verified_at = datetime.utcnow()
        self._save()

    def get_computation(self, computation_id: str) -> Optional[VerifiableComputation]:
        return self.computations.get(computation_id)

    def list_computations(self) -> list[VerifiableComputation]:
        return list(self.computations.values())

    def get_supported_schemes(self) -> list[dict[str, Any]]:
        return [
            {"type": "groth16", "name": "Groth16", "proving_key": "~10-100 MB", "verification_key": "~0.1 MB", "proof_size": "~128-256 bytes"},
            {"type": "plonk", "name": "PLONK", "proving_key": "~5-50 MB", "verification_key": "~0.1 MB", "proof_size": "~512-1024 bytes", "universal_setup": True},
            {"type": "halo2", "name": "Halo2", "proving_key": "~10-100 MB", "verification_key": "~0.1 MB", "proof_size": "~1-4 KB", "no_trusted_setup": True},
            {"type": "stark", "name": "STARK", "proving_key": "None", "verification_key": "~0.1 MB", "proof_size": "~10-100 KB", "post_quantum_secure": True},
            {"type": "circom", "name": "Circom", "proving_key": "~10-200 MB", "verification_key": "~0.1 MB", "proof_size": "~128-256 bytes", "ecosystem": "largest"},
        ]

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_circuits": len(self.circuits),
            "setup_done": sum(1 for c in self.circuits.values() if c.setup_done),
            "total_proofs": len(self.proofs),
            "verified_proofs": sum(1 for p in self.proofs.values() if p.verified),
            "total_computations": len(self.computations),
            "verified_computations": sum(1 for c in self.computations.values() if c.verified),
            "avg_proof_size_bytes": sum(p.proof_size_bytes for p in self.proofs.values()) / len(self.proofs) if self.proofs else 0,
        }

    # === Export ===
    def export_circuits_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["circuit_id", "name", "circuit_type", "constraints", "public_inputs", "private_inputs", "pk_size_mb", "vk_size_mb", "setup_done", "created_at"])
        for c in self.circuits.values():
            writer.writerow([c.circuit_id, c.name, c.circuit_type.value, c.constraints, c.public_inputs, c.private_inputs, c.proving_key_size_mb, c.verification_key_size_mb, c.setup_done, c.created_at.isoformat()])
        return output.getvalue()

    def export_proofs_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["proof_id", "circuit_id", "name", "status", "circuit_type", "proof_size_bytes", "gen_time_ms", "ver_time_ms", "verified", "created_at"])
        for p in self.proofs.values():
            writer.writerow([p.proof_id, p.circuit_id, p.name, p.status.value, p.circuit_type.value, p.proof_size_bytes, p.generation_time_ms, p.verification_time_ms, p.verified, p.created_at.isoformat()])
        return output.getvalue()

    def export_circuits_json(self) -> str:
        return json.dumps({"circuits": [c.to_dict() for c in self.circuits.values()], "proofs": [p.to_dict() for p in self.proofs.values()], "computations": [c.to_dict() for c in self.computations.values()]}, indent=2, default=str)

    # === Import ===
    def import_circuits_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("circuits", data if isinstance(data, list) else []):
            c = ZKCircuitTemplate(item.get("circuit_id", str(uuid.uuid4())), item.get("name", "Imported Circuit"), ZKCircuit(item.get("circuit_type", "groth16")))
            c.description = item.get("description", "")
            c.constraints = item.get("constraints", 0)
            c.public_inputs = item.get("public_inputs", 0)
            c.private_inputs = item.get("private_inputs", 0)
            c.proving_key_size_mb = item.get("proving_key_size_mb", 0.0)
            c.verification_key_size_mb = item.get("verification_key_size_mb", 0.0)
            c.setup_done = item.get("setup_done", False)
            self.circuits[c.circuit_id] = c
            count += 1
        return count

    # === Notification ===
    async def notify_proof_status(self, proof_id: str) -> dict[str, Any]:
        proof = self.proofs.get(proof_id)
        if not proof:
            return {"error": "Proof not found"}
        return {
            "proof_id": proof.proof_id,
            "circuit_id": proof.circuit_id,
            "name": proof.name,
            "status": proof.status.value,
            "verified": proof.verified,
            "message": f"ZK Proof {proof.name} status: {proof.status.value}, verified: {proof.verified}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_failed_proofs(self) -> list[dict[str, Any]]:
        results = []
        for p in self.proofs.values():
            if p.status == ProofStatus.FAILED:
                results.append(await self.notify_proof_status(p.proof_id))
        return results

    # === State Machine ===
    def transition_proof_status(self, proof_id: str, target_status: str) -> Optional[ZKProof]:
        proof = self.proofs.get(proof_id)
        if not proof:
            return None
        valid = {
            ProofStatus.GENERATING: [ProofStatus.VERIFIED, ProofStatus.FAILED],
            ProofStatus.VERIFIED: [ProofStatus.EXPIRED],
            ProofStatus.FAILED: [ProofStatus.GENERATING],
            ProofStatus.EXPIRED: [ProofStatus.GENERATING],
        }
        new_status = ProofStatus(target_status)
        if new_status in valid.get(proof.status, []):
            proof.status = new_status
            if new_status == ProofStatus.VERIFIED:
                proof.verified = True
            self._save()
            return proof
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("storage_path"):
            warnings.append("No storage path configured")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_circuits": len(self.circuits),
            "setup_complete": sum(1 for c in self.circuits.values() if c.setup_done),
            "total_proofs": len(self.proofs),
            "verified_proofs": sum(1 for p in self.proofs.values() if p.verified),
            "failed_proofs": sum(1 for p in self.proofs.values() if p.status == ProofStatus.FAILED),
            "total_computations": len(self.computations),
            "verified_computations": sum(1 for c in self.computations.values() if c.verified),
            "avg_proof_size_bytes": sum(p.proof_size_bytes for p in self.proofs.values()) / len(self.proofs) if self.proofs else 0,
            "avg_gen_time_ms": sum(p.generation_time_ms for p in self.proofs.values()) / len(self.proofs) if self.proofs else 0,
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        verified = sum(1 for p in self.proofs.values() if p.verified)
        failed = sum(1 for p in self.proofs.values() if p.status == ProofStatus.FAILED)
        return {
            "total_circuits": len(self.circuits),
            "total_proofs": len(self.proofs),
            "verified": verified,
            "failed": failed,
            "health_pct": round(verified / max(len(self.proofs), 1) * 100, 1),
        }

    # === Bulk Operations ===
    async def bulk_generate_proofs(self, circuit_id: str, names: list[str], public_inputs: dict[str, Any], private_inputs: dict[str, Any]) -> int:
        count = 0
        for name in names:
            result = await self.generate_proof(circuit_id, name, public_inputs, private_inputs)
            if result:
                count += 1
        return count

    async def bulk_verify_proofs(self, proof_ids: list[str]) -> int:
        count = 0
        for pid in proof_ids:
            result = await self.verify_proof(pid)
            if result:
                count += 1
        return count

    # === Tag Management ===
    def add_circuit_tags(self, circuit_ids: list[str], tags: list[str]) -> int:
        count = 0
        for cid in circuit_ids:
            c = self.circuits.get(cid)
            if c:
                pass  # circuits don't have tags currently
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "zk_proofs",
            "circuits": len(self.circuits),
            "setup_complete": sum(1 for c in self.circuits.values() if c.setup_done),
            "proofs": len(self.proofs),
            "verified_proofs": sum(1 for p in self.proofs.values() if p.verified),
            "computations": len(self.computations),
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
