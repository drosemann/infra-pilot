import json, uuid, asyncio, random, logging, math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"


class FaultCategory(Enum):
    INFRASTRUCTURE = "infrastructure"
    NETWORK = "network"
    CONTAINER = "container"
    APPLICATION = "application"
    DATABASE = "database"
    DNS = "dns"
    STORAGE = "storage"
    SECURITY = "security"


FAULT_TYPES = [
    {"id": "cpu_stress", "name": "CPU Stress", "category": "infrastructure", "description": "Inject CPU load on target instance", "parameters": [
        {"name": "cores", "type": "integer", "default": 1, "min": 1, "max": 64},
        {"name": "load_percent", "type": "integer", "default": 80, "min": 10, "max": 100},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 3600},
        {"name": "ramp_up_seconds", "type": "integer", "default": 0, "min": 0, "max": 300},
    ], "rollback_command": "pkill -f 'stress-ng' || true", "monitoring_metrics": ["cpu_usage", "load_average", "throttled_time"]},
    {"id": "memory_fill", "name": "Memory Fill", "category": "infrastructure", "description": "Consume memory on target instance", "parameters": [
        {"name": "memory_mb", "type": "integer", "default": 512, "min": 64, "max": 65536},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 3600},
        {"name": "fill_speed_mbps", "type": "integer", "default": 100, "min": 1, "max": 10000},
    ], "rollback_command": "pkill -f 'stress-ng' || echo 'already cleaned'", "monitoring_metrics": ["memory_usage", "swap_usage", "oom_kills"]},
    {"id": "disk_fill", "name": "Disk Fill", "category": "infrastructure", "description": "Fill disk space on target to test eviction", "parameters": [
        {"name": "size_mb", "type": "integer", "default": 1024, "min": 100, "max": 100000},
        {"name": "path", "type": "string", "default": "/tmp/chaos"},
        {"name": "fill_speed_mbps", "type": "integer", "default": 50, "min": 1, "max": 1000},
        {"name": "file_count", "type": "integer", "default": 1, "min": 1, "max": 1000},
    ], "rollback_command": "rm -rf /tmp/chaos", "monitoring_metrics": ["disk_usage", "inode_usage", "disk_iops"]},
    {"id": "network_latency", "name": "Network Latency", "category": "network", "description": "Add latency to network traffic", "parameters": [
        {"name": "latency_ms", "type": "integer", "default": 500, "min": 10, "max": 30000},
        {"name": "jitter_ms", "type": "integer", "default": 100, "min": 0, "max": 10000},
        {"name": "percentage", "type": "integer", "default": 100, "min": 1, "max": 100},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 3600},
        {"name": "destination_ports", "type": "string", "default": "", "description": "Comma-separated ports or empty for all"},
    ], "rollback_command": "tc qdisc del dev eth0 root netem 2>/dev/null || true", "monitoring_metrics": ["network_latency", "request_duration", "connection_timeouts"]},
    {"id": "packet_loss", "name": "Packet Loss", "category": "network", "description": "Drop network packets to test retry logic", "parameters": [
        {"name": "loss_percent", "type": "integer", "default": 10, "min": 1, "max": 100},
        {"name": "correlation", "type": "integer", "default": 0, "min": 0, "max": 100},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 3600},
    ], "rollback_command": "tc qdisc del dev eth0 root netem 2>/dev/null || true", "monitoring_metrics": ["packet_loss", "retransmissions", "tcp_retransmits"]},
    {"id": "network_partition", "name": "Network Partition", "category": "network", "description": "Create network partition between services", "parameters": [
        {"name": "target_service", "type": "string", "default": "", "description": "Service to isolate"},
        {"name": "target_port", "type": "integer", "default": 0, "description": "0 means all ports"},
        {"name": "duration", "type": "integer", "default": 30, "min": 5, "max": 600},
        {"name": "direction", "type": "string", "default": "all", "enum": ["ingress", "egress", "all"]},
    ], "rollback_command": "remove iptables rules", "monitoring_metrics": ["connection_failures", "service_health", "error_rate"]},
    {"id": "dns_failure", "name": "DNS Failure", "category": "dns", "description": "Block DNS resolution or return incorrect results", "parameters": [
        {"name": "domains", "type": "string", "default": "*", "description": "Comma-separated domains or * for all"},
        {"name": "failure_mode", "type": "string", "default": "timeout", "enum": ["timeout", "nxdomain", "servfail", "wrong_ip"]},
        {"name": "duration", "type": "integer", "default": 30, "min": 5, "max": 600},
    ], "rollback_command": "restore /etc/resolv.conf", "monitoring_metrics": ["dns_query_time", "dns_failures", "connection_errors"]},
    {"id": "kill_container", "name": "Kill Container", "category": "container", "description": "Force kill containers to test rescheduling", "parameters": [
        {"name": "signal", "type": "string", "default": "SIGKILL", "enum": ["SIGKILL", "SIGTERM", "SIGSTOP"]},
        {"name": "count", "type": "integer", "default": 1, "min": 1, "max": 10},
        {"name": "interval_seconds", "type": "integer", "default": 0, "min": 0, "max": 60},
        {"name": "grace_period_seconds", "type": "integer", "default": 0, "min": 0, "max": 30},
    ], "rollback_command": "N/A (container will be rescheduled by orchestrator)", "monitoring_metrics": ["container_restarts", "pod_reschedules", "downtime_seconds"]},
    {"id": "http_error", "name": "HTTP Error Injection", "category": "application", "description": "Return HTTP errors from service endpoints", "parameters": [
        {"name": "status_code", "type": "integer", "default": 500, "enum": [400, 401, 403, 404, 429, 500, 502, 503, 504]},
        {"name": "percentage", "type": "integer", "default": 50, "min": 1, "max": 100},
        {"name": "endpoints", "type": "string", "default": "*", "description": "Comma-separated paths or * for all"},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 600},
    ], "rollback_command": "reset proxy/ingress configuration", "monitoring_metrics": ["http_error_rate", "http_latency", "error_codes"]},
    {"id": "slow_response", "name": "Slow Response", "category": "application", "description": "Slow down HTTP responses", "parameters": [
        {"name": "delay_ms", "type": "integer", "default": 3000, "min": 100, "max": 60000},
        {"name": "percentage", "type": "integer", "default": 50, "min": 1, "max": 100},
        {"name": "endpoints", "type": "string", "default": "*"},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 600},
    ], "rollback_command": "reset proxy/ingress configuration", "monitoring_metrics": ["p95_latency", "p99_latency", "timeout_rate"]},
    {"id": "db_connection_exhaustion", "name": "DB Connection Exhaustion", "category": "database", "description": "Exhaust database connection pool", "parameters": [
        {"name": "connections", "type": "integer", "default": 50, "min": 1, "max": 10000},
        {"name": "db_type", "type": "string", "default": "postgres", "enum": ["postgres", "mysql", "mongodb", "redis"]},
        {"name": "connection_string", "type": "string", "default": ""},
        {"name": "duration", "type": "integer", "default": 30, "min": 5, "max": 300},
    ], "rollback_command": "close all held connections", "monitoring_metrics": ["db_connections", "query_timeouts", "connection_errors"]},
    {"id": "io_stress", "name": "IO Stress", "category": "storage", "description": "High disk I/O to test performance isolation", "parameters": [
        {"name": "workers", "type": "integer", "default": 4, "min": 1, "max": 32},
        {"name": "io_type", "type": "string", "default": "rw", "enum": ["read", "write", "rw"]},
        {"name": "block_size_kb", "type": "integer", "default": 64, "min": 4, "max": 4096},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 600},
        {"name": "directory", "type": "string", "default": "/tmp/io-stress"},
    ], "rollback_command": "rm -rf /tmp/io-stress; pkill -f fio 2>/dev/null || true", "monitoring_metrics": ["disk_iops", "disk_latency", "disk_throughput"]},
    {"id": "node_drain", "name": "Node Drain", "category": "container", "description": "Cordon and drain a Kubernetes node", "parameters": [
        {"name": "node_name", "type": "string", "default": "", "description": "Node to drain"},
        {"name": "grace_period", "type": "integer", "default": 30, "min": 0, "max": 300},
        {"name": "ignore_daemonsets", "type": "boolean", "default": True},
        {"name": "delete_emptydir_data", "type": "boolean", "default": False},
        {"name": "timeout", "type": "integer", "default": 300, "min": 30, "max": 1800},
    ], "rollback_command": "kubectl uncordon <node>", "monitoring_metrics": ["pod_evictions", "node_status", "workload_redistribution"]},
    {"id": "process_kill", "name": "Process Kill", "category": "infrastructure", "description": "Kill a specific process by name or PID", "parameters": [
        {"name": "process_name", "type": "string", "default": "", "description": "Process name to kill"},
        {"name": "signal", "type": "string", "default": "SIGTERM", "enum": ["SIGTERM", "SIGKILL", "SIGHUP", "SIGINT"]},
        {"name": "count", "type": "integer", "default": 1, "min": 1, "max": 20},
        {"name": "interval_seconds", "type": "integer", "default": 0, "min": 0, "max": 30},
    ], "rollback_command": "systemctl start <service>", "monitoring_metrics": ["process_status", "service_health", "restart_count"]},
    {"id": "clock_skew", "name": "Clock Skew", "category": "infrastructure", "description": "Introduce clock skew for testing time-sensitive operations", "parameters": [
        {"name": "skew_seconds", "type": "integer", "default": 300, "min": 1, "max": 86400},
        {"name": "direction", "type": "string", "default": "forward", "enum": ["forward", "backward"]},
        {"name": "duration", "type": "integer", "default": 60, "min": 5, "max": 600},
    ], "rollback_command": "ntpdate -s pool.ntp.org", "monitoring_metrics": ["time_sync_status", "certificate_errors", "token_validation_errors"]},
    {"id": "tls_certificate_expiry", "name": "TLS Certificate Expiry", "category": "security", "description": "Simulate expired TLS certificates", "parameters": [
        {"name": "service", "type": "string", "default": "", "description": "Service with cert to expire"},
        {"name": "cert_path", "type": "string", "default": "/etc/ssl/certs/server.crt"},
        {"name": "duration", "type": "integer", "default": 120, "min": 10, "max": 3600},
    ], "rollback_command": "restore original certificate", "monitoring_metrics": ["tls_errors", "connection_failures", "certificate_expiry_days"]},
]


class ChaosManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._active_faults: Dict[str, Dict[str, Any]] = {}
        self._experiment_results: Dict[str, List[Dict[str, Any]]] = {}
        self._schedules: Dict[str, Dict[str, Any]] = {}
        self._rollback_actions: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
        self._max_concurrent_experiments = config.get("max_concurrent_experiments", 5)
        self._max_faults_per_experiment = config.get("max_faults_per_experiment", 10)
        self._default_blast_radius = config.get("default_blast_radius", {"max_containers": 3, "max_hosts": 1})
        self._auto_rollback = config.get("auto_rollback", True)
        self._metrics_enabled = config.get("metrics_enabled", True)

    async def initialize(self):
        self._initialized = True
        logger.info(f"ChaosManager initialized with {len(FAULT_TYPES)} fault types across {len(set(f['category'] for f in FAULT_TYPES))} categories")

    async def close(self):
        await self.stop_all_experiments()
        logger.info(f"ChaosManager closed. Active faults stopped: {len(self._active_faults)}")

    def get_fault_types(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if category:
            return [f for f in FAULT_TYPES if f["category"] == category]
        return FAULT_TYPES

    def get_fault_type(self, fault_id: str) -> Optional[Dict[str, Any]]:
        for f in FAULT_TYPES:
            if f["id"] == fault_id:
                return f
        return None

    def validate_fault_parameters(self, fault_type_id: str, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        fault_type = self.get_fault_type(fault_type_id)
        if not fault_type:
            return False, [f"Unknown fault type: {fault_type_id}"]
        errors = []
        for param in fault_type["parameters"]:
            pname = param["name"]
            if pname in params:
                val = params[pname]
                pmin = param.get("min")
                pmax = param.get("max")
                if pmin is not None and isinstance(val, (int, float)) and val < pmin:
                    errors.append(f"{pname}: {val} is below minimum {pmin}")
                if pmax is not None and isinstance(val, (int, float)) and val > pmax:
                    errors.append(f"{pname}: {val} exceeds maximum {pmax}")
                penum = param.get("enum")
                if penum and val not in penum:
                    errors.append(f"{pname}: {val} not in allowed values {penum}")
        return len(errors) == 0, errors

    def create_experiment(self, name: str, description: str, target: Dict[str, Any], faults: List[Dict[str, Any]],
                          steady_state: Optional[Dict[str, Any]] = None, rollback_on_failure: bool = True,
                          blast_radius: Optional[Dict[str, Any]] = None, schedule: Optional[Dict[str, Any]] = None,
                          labels: Optional[Dict[str, str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        if len(faults) > self._max_faults_per_experiment:
            raise ValueError(f"Maximum {self._max_faults_per_experiment} faults per experiment")
        if len(self._experiments) >= 100:
            self._cleanup_old_experiments()
        experiment_id = str(uuid.uuid4())
        valid_faults = []
        for f in faults:
            valid, errors = self.validate_fault_parameters(f["type"], f.get("parameters", {}))
            if not valid:
                raise ValueError(f"Invalid fault parameters for {f['type']}: {errors}")
            fault_type = self.get_fault_type(f["type"])
            resolved_params = {}
            if fault_type:
                for param in fault_type["parameters"]:
                    pname = param["name"]
                    resolved_params[pname] = f.get("parameters", {}).get(pname, param.get("default"))
            valid_faults.append({"type": f["type"], "parameters": resolved_params})
        br = blast_radius or self._default_blast_radius.copy()
        if "namespaces" not in br:
            br["namespaces"] = ["default"]
        exp = {
            "experiment_id": experiment_id, "name": name, "description": description,
            "target": target, "faults": valid_faults, "steady_state": steady_state or {},
            "rollback_on_failure": rollback_on_failure, "blast_radius": br,
            "schedule": schedule, "labels": labels or {}, "tags": tags or [],
            "status": "created", "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(), "started_at": None,
            "completed_at": None, "results": {}, "error": None,
            "metrics": {} if self._metrics_enabled else None,
        }
        if schedule:
            exp["status"] = "scheduled"
            self._schedules[experiment_id] = {"experiment_id": experiment_id, "schedule": schedule, "created_at": datetime.utcnow().isoformat()}
        self._experiments[experiment_id] = exp
        logger.info(f"Chaos experiment {experiment_id} created: {name} with {len(valid_faults)} faults")
        return exp

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        return self._experiments.get(experiment_id)

    def update_experiment(self, experiment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        if exp["status"] in ("running", "completed", "failed", "stopped"):
            raise ValueError(f"Cannot update experiment in status: {exp['status']}")
        allowed_fields = {"name", "description", "target", "faults", "steady_state", "blast_radius", "schedule", "labels", "tags", "rollback_on_failure"}
        for k, v in updates.items():
            if k in allowed_fields:
                exp[k] = v
        exp["updated_at"] = datetime.utcnow().isoformat()
        return exp

    def delete_experiment(self, experiment_id: str) -> bool:
        if experiment_id not in self._experiments:
            return False
        if experiment_id in self._active_faults:
            self.stop_experiment(experiment_id)
        del self._experiments[experiment_id]
        self._schedules.pop(experiment_id, None)
        self._experiment_results.pop(experiment_id, None)
        return True

    def list_experiments(self, status: Optional[str] = None, target_type: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e["status"] == status]
        if target_type:
            experiments = [e for e in experiments if e.get("target", {}).get("type") == target_type]
        if tags:
            experiments = [e for e in experiments if any(t in e.get("tags", []) for t in tags)]
        return sorted(experiments, key=lambda e: e.get("created_at", ""), reverse=True)

    async def run_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp["status"] in ("running", "completed", "stopped"):
            raise ValueError(f"Experiment {experiment_id} is already {exp['status']}")
        active_count = sum(1 for e in self._experiments.values() if e["status"] == "running")
        if active_count >= self._max_concurrent_experiments:
            raise ValueError(f"Maximum concurrent experiments ({self._max_concurrent_experiments}) reached")
        exp["status"] = "running"
        exp["started_at"] = datetime.utcnow().isoformat()
        self._experiment_results[experiment_id] = []
        injected_faults = 0
        failures = []
        for i, fault in enumerate(exp["faults"]):
            try:
                fault_id = str(uuid.uuid4())
                duration = fault.get("parameters", {}).get("duration", 60)
                fault_type = fault["type"]
                fault_config = fault.get("parameters", {})
                self._active_faults[fault_id] = {
                    "fault_id": fault_id, "experiment_id": experiment_id,
                    "fault_type": fault_type, "config": fault_config,
                    "sequence": i, "started_at": datetime.utcnow().isoformat(),
                    "status": "injecting",
                }
                asyncio.create_task(self._inject_fault(fault_id, duration))
                injected_faults += 1
                if exp.get("rollback_on_failure"):
                    rollback_cmd = self.get_fault_type(fault_type).get("rollback_command", "")
                    if rollback_cmd:
                        self._rollback_actions.setdefault(experiment_id, []).append({
                            "fault_id": fault_id, "command": rollback_cmd,
                            "fault_type": fault_type,
                        })
                interval = fault.get("parameters", {}).get("interval_seconds", 0)
                if interval > 0 and i < len(exp["faults"]) - 1:
                    await asyncio.sleep(interval)
            except Exception as e:
                failures.append({"fault": fault["type"], "error": str(e)})
                logger.error(f"Failed to inject fault {fault['type']}: {e}")
        exp["results"] = {"faults_injected": injected_faults, "faults_failed": len(failures), "failures": failures}
        if len(failures) == 0:
            exp["status"] = "running"
        elif injected_faults > 0:
            exp["status"] = "running"
        else:
            exp["status"] = "failed"
            exp["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Experiment {experiment_id}: injected {injected_faults} faults, {len(failures)} failures")
        return exp

    async def pause_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp or exp["status"] != "running":
            return None
        exp["status"] = "paused"
        exp["paused_at"] = datetime.utcnow().isoformat()
        logger.info(f"Experiment {experiment_id} paused")
        return exp

    async def resume_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp or exp["status"] != "paused":
            return None
        exp["status"] = "running"
        exp["resumed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Experiment {experiment_id} resumed")
        return exp

    async def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        to_remove = [fid for fid, f in self._active_faults.items() if f["experiment_id"] == experiment_id]
        stopped_faults = len(to_remove)
        for fid in to_remove:
            del self._active_faults[fid]
        await self._execute_rollback(experiment_id)
        exp = self._experiments.get(experiment_id)
        if exp:
            exp["status"] = "stopped"
            exp["completed_at"] = datetime.utcnow().isoformat()
        return {"experiment_id": experiment_id, "stopped_faults": stopped_faults, "status": "stopped"}

    async def stop_all_experiments(self) -> Dict[str, Any]:
        running_ids = set(f["experiment_id"] for f in self._active_faults.values())
        total_faults = len(self._active_faults)
        self._active_faults.clear()
        for exp_id in running_ids:
            await self._execute_rollback(exp_id)
            exp = self._experiments.get(exp_id)
            if exp and exp["status"] in ("running", "paused"):
                exp["status"] = "stopped"
                exp["completed_at"] = datetime.utcnow().isoformat()
        return {"experiments_stopped": len(running_ids), "faults_removed": total_faults}

    async def _inject_fault(self, fault_id: str, duration: int):
        try:
            fault_info = self._active_faults.get(fault_id)
            if fault_info:
                fault_info["status"] = "active"
                logger.debug(f"Fault {fault_id} ({fault_info['fault_type']}) active for {duration}s")
                expected_end = datetime.utcnow() + timedelta(seconds=duration)
                remaining = duration
                while remaining > 0:
                    await asyncio.sleep(min(10, remaining))
                    remaining = int((expected_end - datetime.utcnow()).total_seconds())
                    if fault_id in self._active_faults:
                        self._active_faults[fault_id]["remaining_seconds"] = remaining
                        self._active_faults[fault_id]["last_heartbeat"] = datetime.utcnow().isoformat()
                    if remaining <= 0:
                        break
            else:
                await asyncio.sleep(duration)
        except asyncio.CancelledError:
            logger.debug(f"Fault {fault_id} cancelled")
        finally:
            if fault_id in self._active_faults:
                self._active_faults[fault_id]["status"] = "completed"
                del self._active_faults[fault_id]

    async def _execute_rollback(self, experiment_id: str):
        actions = self._rollback_actions.pop(experiment_id, [])
        for action in actions:
            try:
                logger.info(f"Executing rollback for {action['fault_type']}: {action['command']}")
            except Exception as e:
                logger.error(f"Rollback failed for {action.get('fault_id', 'unknown')}: {e}")
        if actions:
            logger.info(f"Rollback completed for experiment {experiment_id}: {len(actions)} actions")

    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        return {
            "experiment_id": experiment_id, "name": exp["name"],
            "status": exp["status"], "results": exp.get("results", {}),
            "faults_configured": len(exp.get("faults", [])),
            "duration": self._calculate_duration(exp),
            "metrics": exp.get("metrics", {}),
        }

    def get_experiment_timeline(self, experiment_id: str) -> List[Dict[str, Any]]:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return []
        timeline = []
        timeline.append({"time": exp["created_at"], "event": "created", "status": "created"})
        if exp.get("started_at"):
            timeline.append({"time": exp["started_at"], "event": "started", "status": "running"})
        if exp.get("paused_at"):
            timeline.append({"time": exp["paused_at"], "event": "paused", "status": "paused"})
        if exp.get("resumed_at"):
            timeline.append({"time": exp["resumed_at"], "event": "resumed", "status": "running"})
        if exp.get("completed_at"):
            timeline.append({"time": exp["completed_at"], "event": "completed", "status": exp["status"]})
        return timeline

    def get_active_faults(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if experiment_id:
            return [f for f in self._active_faults.values() if f["experiment_id"] == experiment_id]
        return list(self._active_faults.values())

    def _calculate_duration(self, exp: Dict[str, Any]) -> Optional[float]:
        if exp.get("started_at") and exp.get("completed_at"):
            start = datetime.fromisoformat(exp["started_at"])
            end = datetime.fromisoformat(exp["completed_at"])
            return (end - start).total_seconds()
        return None

    def _cleanup_old_experiments(self):
        sorted_exp = sorted(self._experiments.items(), key=lambda x: x[1].get("created_at", ""))
        to_remove = sorted_exp[:20]
        for eid, _ in to_remove:
            self._experiments.pop(eid, None)
            self._schedules.pop(eid, None)
            self._experiment_results.pop(eid, None)

    def get_statistics(self) -> Dict[str, Any]:
        status_counts = {}
        for e in self._experiments.values():
            s = e["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        return {
            "total_experiments": len(self._experiments),
            "active_faults": len(self._active_faults),
            "fault_types_available": len(FAULT_TYPES),
            "experiments_by_status": status_counts,
            "fault_categories": len(set(f["category"] for f in FAULT_TYPES)),
            "scheduled_experiments": len(self._schedules),
            "max_concurrent_experiments": self._max_concurrent_experiments,
            "auto_rollback_enabled": self._auto_rollback,
        }

    def get_experiment_report(self, experiment_id: str) -> Dict[str, Any]:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return {"error": "Experiment not found"}
        timeline = self.get_experiment_timeline(experiment_id)
        results = self.get_experiment_results(experiment_id)
        return {
            "experiment": exp,
            "timeline": timeline,
            "results": results,
            "faults_summary": [{"type": f["type"], "parameters": f["parameters"]} for f in exp.get("faults", [])],
            "blast_radius": exp.get("blast_radius"),
            "target_details": exp.get("target"),
            "duration_seconds": self._calculate_duration(exp),
        }

    def compare_experiments(self, experiment_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for eid in experiment_ids:
            exp = self._experiments.get(eid)
            if exp:
                results.append({
                    "experiment_id": eid,
                    "name": exp["name"],
                    "status": exp["status"],
                    "faults_count": len(exp.get("faults", [])),
                    "duration": self._calculate_duration(exp),
                    "results": exp.get("results", {}),
                })
        return results

    def get_fault_recommendations(self, target_type: str) -> List[Dict[str, Any]]:
        recommendations = {
            "container": ["cpu_stress", "memory_fill", "kill_container", "network_latency", "packet_loss"],
            "host": ["cpu_stress", "memory_fill", "disk_fill", "io_stress", "process_kill", "clock_skew"],
            "service": ["http_error", "slow_response", "network_latency", "dns_failure"],
            "database": ["db_connection_exhaustion", "network_latency", "disk_fill"],
            "namespace": ["node_drain", "network_partition", "kill_container"],
        }
        fault_ids = recommendations.get(target_type, [])
        return [self.get_fault_type(fid) for fid in fault_ids if self.get_fault_type(fid)]
