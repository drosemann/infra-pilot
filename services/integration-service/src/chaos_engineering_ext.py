"""Extended chaos engineering toolkit with experiments, scenarios, and fault injection."""
import json
import uuid
import logging
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class ExperimentTargetType(str, Enum):
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    VIRTUAL_MACHINE = "virtual_machine"
    NETWORK = "network"
    STORAGE = "storage"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"
    DNS = "dns"
    API = "api"
    MICROSERVICE = "microservice"
    SERVERLESS = "serverless"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"


class FaultType(str, Enum):
    POD_KILL = "pod_kill"
    NODE_FAILURE = "node_failure"
    NETWORK_LATENCY = "network_latency"
    NETWORK_PARTITION = "network_partition"
    PACKET_LOSS = "packet_loss"
    DNS_FAILURE = "dns_failure"
    DISK_FILL = "disk_fill"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    IO_STRESS = "io_stress"
    SERVICE_DOWN = "service_down"
    DATABASE_FAILOVER = "database_failover"
    CERTIFICATE_EXPIRY = "certificate_expiry"
    RATE_LIMITING = "rate_limiting"
    AUTHENTICATION_FAILURE = "authentication_failure"
    CONFIGURATION_CHANGE = "configuration_change"
    PROCESS_KILL = "process_kill"
    CONTAINER_KILL = "container_kill"
    NETWORK_BLACKHOLE = "network_blackhole"
    CLOCK_SKEW = "clock_skew"


class ExperimentHypothesis(str, Enum):
    STEADY_STATE = "steady_state"
    DEGRADED_PERFORMANCE = "degraded_performance"
    PARTIAL_OUTAGE = "partial_outage"
    FULL_RECOVERY = "full_recovery"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class SteadyStateCheck:
    metric: str
    query: str
    expected_value: Any
    comparison: str = "equals"
    tolerance_percent: float = 10.0
    duration_seconds: int = 30


@dataclass
class FaultInjection:
    id: str
    fault_type: FaultType
    target_type: ExperimentTargetType
    target_selector: Dict[str, str] = field(default_factory=dict)
    duration_seconds: int = 60
    intensity: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    rollback_action: Optional[str] = None


@dataclass
class ChaosScenario:
    id: str
    name: str
    description: str
    faults: List[FaultInjection] = field(default_factory=list)
    steady_state_checks: List[SteadyStateCheck] = field(default_factory=list)
    rollback_strategy: str = "auto"
    tags: List[str] = field(default_factory=list)


@dataclass
class ExperimentDefinition:
    id: str
    name: str
    description: str
    hypothesis: ExperimentHypothesis = ExperimentHypothesis.STEADY_STATE
    status: ExperimentStatus = ExperimentStatus.DRAFT
    scenarios: List[ChaosScenario] = field(default_factory=list)
    steady_state_checks: List[SteadyStateCheck] = field(default_factory=list)
    target_type: ExperimentTargetType = ExperimentTargetType.KUBERNETES
    target_selector: Dict[str, str] = field(default_factory=dict)
    blast_radius: str = "targeted"
    duration_minutes: int = 30
    scheduled_start: Optional[datetime] = None
    auto_rollback: bool = True
    alert_thresholds: Dict[str, Any] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExperimentRun:
    id: str
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus = ExperimentStatus.RUNNING
    scenario_id: Optional[str] = None
    faults_executed: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    steady_state_before: Dict[str, Any] = field(default_factory=dict)
    steady_state_after: Dict[str, Any] = field(default_factory=dict)
    hypothesis_result: Optional[str] = None
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    alerts_triggered: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    executed_by: Optional[str] = None
    rollback_status: str = "not_required"
    notes: Optional[str] = None


class ChaosEngineeringManager:
    def __init__(self, storage_path: str = "data/chaos_engineering.json"):
        self.storage_path = storage_path
        self.experiments: Dict[str, ExperimentDefinition] = {}
        self.runs: Dict[str, ExperimentRun] = {}
        self.scenarios: Dict[str, ChaosScenario] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for ex_data in data.get("experiments", []):
            ex = ExperimentDefinition(**ex_data)
            self.experiments[ex.id] = ex
        for run_data in data.get("runs", []):
            run = ExperimentRun(**run_data)
            self.runs[run.id] = run
        for sc_data in data.get("scenarios", []):
            sc = ChaosScenario(**sc_data)
            self.scenarios[sc.id] = sc

    def _save_data(self) -> None:
        data = {
            "experiments": [e.__dict__ for e in self.experiments.values()],
            "runs": [r.__dict__ for r in self.runs.values()],
            "scenarios": [s.__dict__ for s in self.scenarios.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("ChaosEngineeringManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("ChaosEngineeringManager closed")

    def create_experiment(self, name: str, description: str, target_type: ExperimentTargetType, hypothesis: ExperimentHypothesis = ExperimentHypothesis.STEADY_STATE, target_selector: Optional[Dict[str, str]] = None, blast_radius: str = "targeted", duration_minutes: int = 30, created_by: Optional[str] = None) -> ExperimentDefinition:
        ex = ExperimentDefinition(id=str(uuid.uuid4()), name=name, description=description, target_type=target_type, hypothesis=hypothesis, target_selector=target_selector or {}, blast_radius=blast_radius, duration_minutes=duration_minutes, created_by=created_by)
        self.experiments[ex.id] = ex
        self._save_data()
        return ex

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentDefinition]:
        return self.experiments.get(experiment_id)

    def update_experiment(self, experiment_id: str, updates: Dict[str, Any]) -> Optional[ExperimentDefinition]:
        ex = self.experiments.get(experiment_id)
        if not ex:
            return None
        for key, value in updates.items():
            if hasattr(ex, key) and key not in ("id", "created_at", "created_by"):
                setattr(ex, key, value)
        ex.updated_at = datetime.utcnow()
        self.experiments[experiment_id] = ex
        self._save_data()
        return ex

    def delete_experiment(self, experiment_id: str) -> bool:
        if experiment_id in self.experiments:
            del self.experiments[experiment_id]
            self._save_data()
            return True
        return False

    def add_steady_state_check(self, experiment_id: str, metric: str, query: str, expected_value: Any, comparison: str = "equals", tolerance_percent: float = 10.0, duration_seconds: int = 30) -> Optional[SteadyStateCheck]:
        ex = self.experiments.get(experiment_id)
        if not ex:
            return None
        check = SteadyStateCheck(metric=metric, query=query, expected_value=expected_value, comparison=comparison, tolerance_percent=tolerance_percent, duration_seconds=duration_seconds)
        ex.steady_state_checks.append(check)
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return check

    def add_fault_to_scenario(self, experiment_id: str, scenario_id: str, fault_type: FaultType, target_type: ExperimentTargetType, target_selector: Optional[Dict[str, str]] = None, duration_seconds: int = 60, intensity: float = 1.0, parameters: Optional[Dict[str, Any]] = None) -> Optional[FaultInjection]:
        ex = self.experiments.get(experiment_id)
        if not ex:
            return None
        scenario = next((s for s in ex.scenarios if s.id == scenario_id), None)
        if not scenario:
            scenario = next((s for s in self.scenarios.values() if s.id == scenario_id), None)
            if scenario:
                ex.scenarios.append(scenario)
                ex.updated_at = datetime.utcnow()
                scenario = next((s for s in ex.scenarios if s.id == scenario_id), None)
        if not scenario:
            return None
        fault = FaultInjection(id=str(uuid.uuid4()), fault_type=fault_type, target_type=target_type, target_selector=target_selector or {}, duration_seconds=duration_seconds, intensity=intensity, parameters=parameters or {})
        scenario.faults.append(fault)
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return fault

    def create_scenario(self, name: str, description: str, tags: Optional[List[str]] = None) -> ChaosScenario:
        sc = ChaosScenario(id=str(uuid.uuid4()), name=name, description=description, tags=tags or [])
        self.scenarios[sc.id] = sc
        self._save_data()
        return sc

    def add_scenario_to_experiment(self, experiment_id: str, scenario_id: str) -> bool:
        ex = self.experiments.get(experiment_id)
        sc = self.scenarios.get(scenario_id)
        if not ex or not sc:
            return False
        ex.scenarios.append(sc)
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def run_experiment(self, experiment_id: str, executed_by: Optional[str] = None, scenario_id: Optional[str] = None) -> Optional[ExperimentRun]:
        ex = self.experiments.get(experiment_id)
        if not ex or ex.status not in (ExperimentStatus.DRAFT, ExperimentStatus.SCHEDULED):
            return None
        ex.status = ExperimentStatus.RUNNING
        run = ExperimentRun(id=str(uuid.uuid4()), experiment_id=experiment_id, experiment_name=ex.name, status=ExperimentStatus.RUNNING, executed_by=executed_by, scenario_id=scenario_id)
        self.runs[run.id] = run
        self._save_data()
        try:
            run.steady_state_before = self._check_steady_state(ex.steady_state_checks)
            scenarios_to_run = [s for s in ex.scenarios if s.id == scenario_id] if scenario_id else ex.scenarios
            for scenario in scenarios_to_run:
                for fault in scenario.faults:
                    self._inject_fault(fault, run)
                    run.faults_executed[fault.id] = {"fault_type": fault.fault_type.value, "status": "injected", "duration_seconds": fault.duration_seconds}
            if ex.duration_minutes > 0:
                time.sleep(min(ex.duration_minutes, 1))
            run.steady_state_after = self._check_steady_state(ex.steady_state_checks)
            run.hypothesis_result = self._evaluate_hypothesis(run.steady_state_before, run.steady_state_after, ex.hypothesis)
            if ex.auto_rollback:
                self._rollback_experiment(run)
                run.rollback_status = "completed"
            run.status = ExperimentStatus.COMPLETED
        except Exception as e:
            run.status = ExperimentStatus.FAILED
            run.error = str(e)
            if ex.auto_rollback:
                self._rollback_experiment(run)
                run.rollback_status = "completed"
        ex.status = ExperimentStatus.COMPLETED if run.status == ExperimentStatus.COMPLETED else ExperimentStatus.FAILED
        run.completed_at = datetime.utcnow()
        run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return run

    def _check_steady_state(self, checks: List[SteadyStateCheck]) -> Dict[str, Any]:
        results = {}
        for check in checks:
            actual_value = self._query_metric(check.query)
            expected = check.expected_value
            if check.comparison == "equals":
                passed = actual_value == expected
            elif check.comparison == "less_than":
                passed = actual_value < expected
            elif check.comparison == "greater_than":
                passed = actual_value > expected
            elif check.comparison == "within_tolerance":
                if isinstance(actual_value, (int, float)) and isinstance(expected, (int, float)):
                    tolerance = expected * (check.tolerance_percent / 100)
                    passed = abs(actual_value - expected) <= tolerance
                else:
                    passed = str(actual_value) == str(expected)
            else:
                passed = str(actual_value) == str(expected)
            results[check.metric] = {"metric": check.metric, "expected": expected, "actual": actual_value, "passed": passed}
        return results

    def _query_metric(self, query: str) -> Any:
        return random.uniform(0.5, 1.5)

    def _inject_fault(self, fault: FaultInjection, run: ExperimentRun) -> None:
        logger.info(f"Injecting fault {fault.fault_type.value} on {fault.target_type.value}")
        if fault.fault_type == FaultType.POD_KILL:
            self._fault_pod_kill(fault)
        elif fault.fault_type == FaultType.NETWORK_LATENCY:
            self._fault_network_latency(fault)
        elif fault.fault_type == FaultType.CPU_STRESS:
            self._fault_cpu_stress(fault)
        elif fault.fault_type == FaultType.MEMORY_STRESS:
            self._fault_memory_stress(fault)
        elif fault.fault_type == FaultType.DISK_FILL:
            self._fault_disk_fill(fault)
        elif fault.fault_type == FaultType.SERVICE_DOWN:
            self._fault_service_down(fault)
        elif fault.fault_type == FaultType.PACKET_LOSS:
            self._fault_packet_loss(fault)
        elif fault.fault_type == FaultType.DNS_FAILURE:
            self._fault_dns_failure(fault)
        else:
            self._fault_generic(fault)
        run.metrics.setdefault(fault.fault_type.value, []).append(random.uniform(0, 100))

    def _fault_pod_kill(self, fault: FaultInjection) -> None:
        namespace = fault.target_selector.get("namespace", "default")
        label = fault.target_selector.get("label", "app=test")
        logger.info(f"Killing pods matching {label} in namespace {namespace}")

    def _fault_network_latency(self, fault: FaultInjection) -> None:
        latency_ms = fault.parameters.get("latency_ms", 1000)
        jitter_ms = fault.parameters.get("jitter_ms", 100)
        logger.info(f"Adding {latency_ms}ms latency ±{jitter_ms}ms")

    def _fault_cpu_stress(self, fault: FaultInjection) -> None:
        cores = fault.parameters.get("cores", 1)
        load_percent = fault.parameters.get("load_percent", 80)
        logger.info(f"Stressing {cores} cores to {load_percent}%")

    def _fault_memory_stress(self, fault: FaultInjection) -> None:
        mb = fault.parameters.get("memory_mb", 512)
        logger.info(f"Allocating {mb}MB of memory")

    def _fault_disk_fill(self, fault: FaultInjection) -> None:
        mb = fault.parameters.get("size_mb", 1000)
        path = fault.parameters.get("path", "/tmp")
        logger.info(f"Filling {mb}MB on {path}")

    def _fault_service_down(self, fault: FaultInjection) -> None:
        service = fault.target_selector.get("service", "unknown")
        logger.info(f"Taking down service: {service}")

    def _fault_packet_loss(self, fault: FaultInjection) -> None:
        loss_percent = fault.parameters.get("loss_percent", 50)
        logger.info(f"Introducing {loss_percent}% packet loss")

    def _fault_dns_failure(self, fault: FaultInjection) -> None:
        domain = fault.parameters.get("domain", "example.com")
        logger.info(f"Failing DNS resolution for {domain}")

    def _fault_generic(self, fault: FaultInjection) -> None:
        logger.info(f"Generic fault injection: {fault.fault_type.value}")

    def _evaluate_hypothesis(self, before: Dict[str, Any], after: Dict[str, Any], hypothesis: ExperimentHypothesis) -> str:
        all_passed_before = all(v.get("passed", True) for v in before.values()) if before else True
        all_passed_after = all(v.get("passed", True) for v in after.values()) if after else True
        if hypothesis == ExperimentHypothesis.STEADY_STATE:
            return "proved" if all_passed_after else "refuted"
        elif hypothesis == ExperimentHypothesis.DEGRADED_PERFORMANCE:
            return "proved" if not all_passed_after else "refuted"
        elif hypothesis == ExperimentHypothesis.FULL_RECOVERY:
            return "proved" if all_passed_before == all_passed_after else "refuted"
        return "inconclusive"

    def _rollback_experiment(self, run: ExperimentRun) -> None:
        logger.info(f"Rolling back experiment {run.experiment_name}")
        run.rollback_status = "completed"

    def cancel_experiment(self, experiment_id: str) -> bool:
        ex = self.experiments.get(experiment_id)
        if not ex or ex.status not in (ExperimentStatus.DRAFT, ExperimentStatus.SCHEDULED, ExperimentStatus.RUNNING):
            return False
        ex.status = ExperimentStatus.CANCELLED
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def approve_experiment(self, experiment_id: str, approved_by: str) -> bool:
        ex = self.experiments.get(experiment_id)
        if not ex or ex.status != ExperimentStatus.DRAFT:
            return False
        ex.approved_by = approved_by
        ex.status = ExperimentStatus.SCHEDULED
        ex.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        return self.runs.get(run_id)

    def list_experiments(self, status: Optional[ExperimentStatus] = None, target_type: Optional[ExperimentTargetType] = None) -> List[ExperimentDefinition]:
        results = list(self.experiments.values())
        if status:
            results = [e for e in results if e.status == status]
        if target_type:
            results = [e for e in results if e.target_type == target_type]
        return results

    def list_runs(self, experiment_id: Optional[str] = None) -> List[ExperimentRun]:
        results = list(self.runs.values())
        if experiment_id:
            results = [r for r in results if r.experiment_id == experiment_id]
        return sorted(results, key=lambda x: x.started_at, reverse=True)

    def search_experiments(self, query: str) -> List[ExperimentDefinition]:
        query = query.lower()
        return [e for e in self.experiments.values() if query in e.name.lower() or query in e.description.lower() or any(query in t.lower() for t in e.tags)]

    def get_report(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        ex = self.experiments.get(experiment_id)
        if not ex:
            return None
        runs = self.list_runs(experiment_id=experiment_id)
        return {"experiment": {"id": ex.id, "name": ex.name, "status": ex.status.value, "hypothesis": ex.hypothesis.value, "target_type": ex.target_type.value, "blast_radius": ex.blast_radius, "duration_minutes": ex.duration_minutes, "created_by": ex.created_by}, "runs": [{"id": r.id, "status": r.status.value, "hypothesis_result": r.hypothesis_result, "duration_ms": r.duration_ms, "rollback_status": r.rollback_status, "error": r.error, "started_at": r.started_at.isoformat()} for r in runs], "total_runs": len(runs), "successful_runs": sum(1 for r in runs if r.status == ExperimentStatus.COMPLETED), "failed_runs": sum(1 for r in runs if r.status == ExperimentStatus.FAILED)}

    def get_statistics(self) -> Dict[str, Any]:
        total_experiments = len(self.experiments)
        total_runs = len(self.runs)
        completed_runs = sum(1 for r in self.runs.values() if r.status == ExperimentStatus.COMPLETED)
        failed_runs = sum(1 for r in self.runs.values() if r.status == ExperimentStatus.FAILED)
        by_type = {}
        for e in self.experiments.values():
            by_type[e.target_type.value] = by_type.get(e.target_type.value, 0) + 1
        return {"total_experiments": total_experiments, "total_runs": total_runs, "completed_runs": completed_runs, "failed_runs": failed_runs, "experiments_by_target_type": by_type, "total_scenarios": len(self.scenarios), "success_rate": (completed_runs / total_runs * 100) if total_runs > 0 else 0.0}

    def duplicate_experiment(self, experiment_id: str, new_name: str) -> Optional[ExperimentDefinition]:
        ex = self.experiments.get(experiment_id)
        if not ex:
            return None
        clone = self.create_experiment(name=new_name, description=ex.description, target_type=ex.target_type, hypothesis=ex.hypothesis, target_selector=ex.target_selector.copy(), blast_radius=ex.blast_radius, duration_minutes=ex.duration_minutes, created_by=ex.created_by)
        for check in ex.steady_state_checks:
            self.add_steady_state_check(clone.id, check.metric, check.query, check.expected_value, check.comparison, check.tolerance_percent, check.duration_seconds)
        for scenario in ex.scenarios:
            self.add_scenario_to_experiment(clone.id, scenario.id)
        return clone
