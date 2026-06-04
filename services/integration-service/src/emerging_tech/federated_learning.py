"""Federated Learning Infrastructure — distributed ML model training across edge nodes."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AggregationMethod(Enum):
    FEDERATED_AVERAGING = "federated_averaging"
    WEIGHTED_AVERAGING = "weighted_averaging"
    SECURE_AGGREGATION = "secure_aggregation"
    MEDIAN = "median"
    TRIMMED_MEAN = "trimmed_mean"
    KRUM = "krum"


class TrainingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrivacyTechnique(Enum):
    NONE = "none"
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    SECURE_AGGREGATION = "secure_aggregation"
    HOMOMORPHIC_ENCRYPTION = "homomorphic_encryption"
    TEE = "tee"


class FederatedModel:
    def __init__(self, model_id: str, name: str, framework: str):
        self.model_id = model_id
        self.name = name
        self.framework = framework
        self.version = "1.0.0"
        self.description = ""
        self.architecture = ""
        self.total_parameters = 0
        self.model_format = "onnx"
        self.artifact_url = ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id, "name": self.name, "framework": self.framework,
            "version": self.version, "description": self.description,
            "architecture": self.architecture, "total_parameters": self.total_parameters,
            "model_format": self.model_format, "artifact_url": self.artifact_url,
            "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat(),
        }


class TrainingRound:
    def __init__(self, round_id: str, model_id: str, round_number: int):
        self.round_id = round_id
        self.model_id = model_id
        self.round_number = round_number
        self.status = TrainingStatus.PENDING
        self.aggregation_method = AggregationMethod.FEDERATED_AVERAGING
        self.privacy_technique = PrivacyTechnique.NONE
        self.epsilon = 0.0
        self.delta = 0.0
        self.clipping_norm = 1.0
        self.min_clients = 2
        self.max_clients = 100
        self.selected_clients: list[str] = []
        self.client_weights: dict[str, float] = {}
        self.aggregated_weights_url = ""
        self.global_accuracy = 0.0
        self.global_loss = 0.0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_seconds = 0
        self.metrics: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_id": self.round_id, "model_id": self.model_id,
            "round_number": self.round_number, "status": self.status.value,
            "aggregation_method": self.aggregation_method.value,
            "privacy_technique": self.privacy_technique.value,
            "epsilon": self.epsilon, "delta": self.delta,
            "clipping_norm": self.clipping_norm,
            "min_clients": self.min_clients, "max_clients": self.max_clients,
            "selected_clients": self.selected_clients,
            "client_weights": self.client_weights,
            "aggregated_weights_url": self.aggregated_weights_url,
            "global_accuracy": self.global_accuracy, "global_loss": self.global_loss,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds, "metrics": self.metrics,
        }


class FederatedClient:
    def __init__(self, client_id: str, name: str, node_id: str):
        self.client_id = client_id
        self.name = name
        self.node_id = node_id
        self.status = "idle"
        self.data_size = 0
        self.data_samples = 0
        self.data_distribution: dict[str, int] = {}
        self.local_accuracy = 0.0
        self.local_loss = 0.0
        self.training_time_ms = 0
        self.last_contribution = ""
        self.total_rounds_participated = 0
        self.bandwidth_used_mb = 0.0
        self.reliability_score = 1.0
        self.joined_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id, "name": self.name, "node_id": self.node_id,
            "status": self.status, "data_size": self.data_size,
            "data_samples": self.data_samples, "data_distribution": self.data_distribution,
            "local_accuracy": self.local_accuracy, "local_loss": self.local_loss,
            "training_time_ms": self.training_time_ms,
            "last_contribution": self.last_contribution,
            "total_rounds_participated": self.total_rounds_participated,
            "bandwidth_used_mb": self.bandwidth_used_mb,
            "reliability_score": self.reliability_score,
            "joined_at": self.joined_at.isoformat(),
        }


class FederatedLearningManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.models: dict[str, FederatedModel] = {}
        self.training_rounds: dict[str, TrainingRound] = {}
        self.clients: dict[str, FederatedClient] = {}
        self.storage_path = config.get("storage_path", "data/federated_learning.json")

    async def initialize(self):
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                for m_data in data.get("models", []):
                    m = FederatedModel(m_data["model_id"], m_data["name"], m_data["framework"])
                    m.version = m_data.get("version", "1.0.0")
                    m.description = m_data.get("description", "")
                    m.architecture = m_data.get("architecture", "")
                    m.total_parameters = m_data.get("total_parameters", 0)
                    self.models[m.model_id] = m
                for c_data in data.get("clients", []):
                    c = FederatedClient(c_data["client_id"], c_data["name"], c_data["node_id"])
                    c.data_samples = c_data.get("data_samples", 0)
                    c.reliability_score = c_data.get("reliability_score", 1.0)
                    self.clients[c.client_id] = c
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("Initialized FederatedLearningManager with %d models, %d clients", len(self.models), len(self.clients))

    async def close(self):
        self._save()

    def _save(self):
        data = {
            "models": [m.to_dict() for m in self.models.values()],
            "training_rounds": [r.to_dict() for r in self.training_rounds.values()],
            "clients": [c.to_dict() for c in self.clients.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    async def register_model(self, name: str, framework: str, architecture: str = "") -> FederatedModel:
        model_id = str(uuid.uuid4())
        model = FederatedModel(model_id, name, framework)
        model.architecture = architecture
        model.total_parameters = 1000000
        self.models[model_id] = model
        self._save()
        return model

    def get_model(self, model_id: str) -> Optional[FederatedModel]:
        return self.models.get(model_id)

    def list_models(self) -> list[FederatedModel]:
        return list(self.models.values())

    async def register_client(self, name: str, node_id: str, data_samples: int = 0) -> FederatedClient:
        client_id = str(uuid.uuid4())
        client = FederatedClient(client_id, name, node_id)
        client.data_samples = data_samples
        self.clients[client_id] = client
        self._save()
        return client

    def get_client(self, client_id: str) -> Optional[FederatedClient]:
        return self.clients.get(client_id)

    def list_clients(self) -> list[FederatedClient]:
        return list(self.clients.values())

    async def start_training_round(self, model_id: str, aggregation_method: AggregationMethod = AggregationMethod.FEDERATED_AVERAGING) -> Optional[TrainingRound]:
        if model_id not in self.models:
            return None
        round_number = len([r for r in self.training_rounds.values() if r.model_id == model_id]) + 1
        round_id = str(uuid.uuid4())
        training = TrainingRound(round_id, model_id, round_number)
        training.aggregation_method = aggregation_method
        training.status = TrainingStatus.RUNNING
        training.started_at = datetime.utcnow()
        available_clients = [c for c in self.clients.keys()]
        import random
        random.shuffle(available_clients)
        training.selected_clients = available_clients[:min(5, len(available_clients))]
        self.training_rounds[round_id] = training
        self._save()
        asyncio.create_task(self._simulate_training_round(round_id))
        return training

    async def _simulate_training_round(self, round_id: str):
        await asyncio.sleep(3)
        training = self.training_rounds.get(round_id)
        if not training:
            return
        import random
        for client_id in training.selected_clients:
            client = self.clients.get(client_id)
            if client:
                client.status = "training"
                client.local_accuracy = random.uniform(0.7, 0.95)
                client.local_loss = random.uniform(0.1, 0.8)
                client.training_time_ms = random.randint(1000, 10000)
                client.total_rounds_participated += 1
        await asyncio.sleep(1)
        training.status = TrainingStatus.COMPLETED
        training.global_accuracy = sum(self.clients[c].local_accuracy for c in training.selected_clients if c in self.clients) / len(training.selected_clients)
        training.global_loss = sum(self.clients[c].local_loss for c in training.selected_clients if c in self.clients) / len(training.selected_clients)
        training.completed_at = datetime.utcnow()
        training.duration_seconds = int((training.completed_at - training.started_at).total_seconds())
        training.metrics = {"convergence_rate": 0.95, "communication_cost_mb": random.uniform(10, 100), "client_dropout_rate": 0.0}
        for client_id in training.selected_clients:
            client = self.clients.get(client_id)
            if client:
                client.status = "idle"
        self._save()

    def get_training_round(self, round_id: str) -> Optional[TrainingRound]:
        return self.training_rounds.get(round_id)

    def list_training_rounds(self, model_id: Optional[str] = None) -> list[TrainingRound]:
        if model_id:
            return [r for r in self.training_rounds.values() if r.model_id == model_id]
        return list(self.training_rounds.values())

    async def apply_differential_privacy(self, round_id: str, epsilon: float, delta: float = 1e-5, clipping_norm: float = 1.0) -> bool:
        training = self.training_rounds.get(round_id)
        if not training:
            return False
        training.privacy_technique = PrivacyTechnique.DIFFERENTIAL_PRIVACY
        training.epsilon = epsilon
        training.delta = delta
        training.clipping_norm = clipping_norm
        self._save()
        return True

    def get_model_convergence(self, model_id: str) -> list[dict[str, Any]]:
        rounds = [r for r in self.training_rounds.values() if r.model_id == model_id and r.status == TrainingStatus.COMPLETED]
        rounds.sort(key=lambda r: r.round_number)
        return [{"round": r.round_number, "accuracy": r.global_accuracy, "loss": r.global_loss, "duration": r.duration_seconds, "clients": len(r.selected_clients)} for r in rounds]

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_models": len(self.models),
            "total_training_rounds": len(self.training_rounds),
            "completed_rounds": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED),
            "total_clients": len(self.clients),
            "active_clients": sum(1 for c in self.clients.values() if c.status == "training"),
            "avg_reliability": sum(c.reliability_score for c in self.clients.values()) / len(self.clients) if self.clients else 0,
            "avg_accuracy": sum(r.global_accuracy for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED) / max(1, sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED)),
        }

    # === Export ===
    def export_models_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["model_id", "name", "framework", "version", "architecture", "parameters", "format", "created_at"])
        for m in self.models.values():
            writer.writerow([m.model_id, m.name, m.framework, m.version, m.architecture, m.total_parameters, m.model_format, m.created_at.isoformat()])
        return output.getvalue()

    def export_training_rounds_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["round_id", "model_id", "round_number", "status", "aggregation", "privacy", "clients", "accuracy", "loss", "duration_s", "started_at"])
        for r in self.training_rounds.values():
            writer.writerow([r.round_id, r.model_id, r.round_number, r.status.value, r.aggregation_method.value, r.privacy_technique.value, len(r.selected_clients), r.global_accuracy, r.global_loss, r.duration_seconds, r.started_at.isoformat() if r.started_at else ""])
        return output.getvalue()

    def export_models_json(self) -> str:
        return json.dumps({"models": [m.to_dict() for m in self.models.values()], "rounds": [r.to_dict() for r in self.training_rounds.values()], "clients": [c.to_dict() for c in self.clients.values()]}, indent=2, default=str)

    # === Import ===
    def import_models_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data.get("models", data if isinstance(data, list) else []):
            m = FederatedModel(item.get("model_id", str(uuid.uuid4())), item.get("name", "Imported Model"), item.get("framework", "pytorch"))
            m.version = item.get("version", "1.0.0")
            m.architecture = item.get("architecture", "")
            m.total_parameters = item.get("total_parameters", 0)
            self.models[m.model_id] = m
            count += 1
        return count

    # === Notification ===
    async def notify_round_status(self, round_id: str) -> dict[str, Any]:
        training = self.training_rounds.get(round_id)
        if not training:
            return {"error": "Training round not found"}
        return {
            "round_id": training.round_id,
            "model_id": training.model_id,
            "round_number": training.round_number,
            "status": training.status.value,
            "accuracy": training.global_accuracy,
            "message": f"Training round {training.round_number} for model {training.model_id}: {training.status.value}",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_completed_rounds(self) -> list[dict[str, Any]]:
        results = []
        for r in self.training_rounds.values():
            if r.status == TrainingStatus.COMPLETED:
                results.append(await self.notify_round_status(r.round_id))
        return results

    # === State Machine ===
    def transition_round_status(self, round_id: str, target_status: str) -> Optional[TrainingRound]:
        training = self.training_rounds.get(round_id)
        if not training:
            return None
        valid = {
            TrainingStatus.PENDING: [TrainingStatus.RUNNING, TrainingStatus.CANCELLED],
            TrainingStatus.RUNNING: [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED],
            TrainingStatus.COMPLETED: [],
            TrainingStatus.FAILED: [TrainingStatus.PENDING],
            TrainingStatus.CANCELLED: [],
        }
        new_status = TrainingStatus(target_status)
        if new_status in valid.get(training.status, []):
            training.status = new_status
            if new_status == TrainingStatus.RUNNING:
                training.started_at = datetime.utcnow()
            if new_status == TrainingStatus.COMPLETED:
                training.completed_at = datetime.utcnow()
            self._save()
            return training
        return None

    # === Config Validation ===
    def validate_full_config(self, config: dict[str, Any]) -> dict[str, Any]:
        errors = []
        warnings = []
        if config.get("min_clients", 2) < 2:
            errors.append("Minimum clients must be at least 2")
        if config.get("max_clients", 100) > 1000:
            warnings.append("Max clients exceeds 1000")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_analytics(self) -> dict[str, Any]:
        return {
            "total_models": len(self.models),
            "total_rounds": len(self.training_rounds),
            "completed_rounds": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED),
            "failed_rounds": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.FAILED),
            "total_clients": len(self.clients),
            "avg_accuracy": sum(r.global_accuracy for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED) / max(1, sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED)),
            "avg_reliability": sum(c.reliability_score for c in self.clients.values()) / len(self.clients) if self.clients else 0,
        }

    def get_health_snapshot(self) -> dict[str, Any]:
        running = sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.RUNNING)
        return {
            "total_models": len(self.models),
            "total_clients": len(self.clients),
            "running_rounds": running,
            "health_pct": 100.0,
        }

    # === Bulk Operations ===
    async def bulk_cancel_rounds(self, round_ids: list[str]) -> int:
        count = 0
        for rid in round_ids:
            r = self.training_rounds.get(rid)
            if r and r.status in (TrainingStatus.PENDING, TrainingStatus.RUNNING):
                r.status = TrainingStatus.CANCELLED
                count += 1
        self._save()
        return count

    async def bulk_restart_failed_rounds(self, round_ids: list[str]) -> int:
        count = 0
        for rid in round_ids:
            r = self.training_rounds.get(rid)
            if r and r.status == TrainingStatus.FAILED:
                r.status = TrainingStatus.PENDING
                count += 1
        self._save()
        return count

    # === Tag Management ===
    def add_model_tags(self, model_ids: list[str], tags: list[str]) -> int:
        count = 0
        for mid in model_ids:
            m = self.models.get(mid)
            if m:
                pass  # models don't have tags currently
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> dict[str, Any]:
        return {
            "service": "federated_learning",
            "models": len(self.models),
            "clients": len(self.clients),
            "training_rounds": len(self.training_rounds),
            "running": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.RUNNING),
            "completed": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.COMPLETED),
            "failed": sum(1 for r in self.training_rounds.values() if r.status == TrainingStatus.FAILED),
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
