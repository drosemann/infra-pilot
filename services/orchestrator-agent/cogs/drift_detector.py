import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DriftSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftStatus(Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    REMEDIATED = "remediated"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


DESIRED_STATES = {
    "docker:container:nginx": {
        "image": "nginx:1.25-alpine",
        "restart_policy": "always",
        "ports": ["80:80", "443:443"],
        "volumes": ["/etc/nginx/conf.d:/etc/nginx/conf.d:ro"],
        "env": {"NGINX_HOST": "example.com"},
        "memory_limit": "512m",
        "cpu_limit": "0.5",
        "healthcheck": {"test": ["CMD", "curl", "-f", "http://localhost"], "interval": 30},
        "labels": {"app": "nginx", "managed_by": "infrapilot"},
    },
    "docker:container:postgres": {
        "image": "postgres:16-alpine",
        "restart_policy": "always",
        "ports": ["5432:5432"],
        "volumes": ["pgdata:/var/lib/postgresql/data"],
        "env": {"POSTGRES_DB": "infrapilot", "POSTGRES_USER": "admin"},
        "memory_limit": "2g",
        "cpu_limit": "2.0",
        "healthcheck": {"test": ["CMD-SHELL", "pg_isready"], "interval": 10},
    },
    "system:ssh:config": {
        "file_path": "/etc/ssh/sshd_config",
        "expected_lines": [
            "PermitRootLogin no",
            "PasswordAuthentication no",
            "PubkeyAuthentication yes",
            "Port 22",
            "Protocol 2",
            "X11Forwarding no",
            "MaxAuthTries 3",
            "ClientAliveInterval 300",
            "ClientAliveCountMax 2",
        ],
        "expected_hash": "sha256:abc123def456",
    },
    "system:nginx:config": {
        "file_path": "/etc/nginx/nginx.conf",
        "expected_content_hash": "sha256:xyz789",
        "expected_settings": {
            "worker_processes": "auto",
            "worker_connections": 1024,
            "gzip": "on",
            "ssl_protocols": "TLSv1.2 TLSv1.3",
        },
    },
}


class DriftDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._scans: Dict[str, Dict] = {}
        self._suppressions: Dict[str, Dict] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("DriftDetector initialized")

    async def close(self) -> None:
        self._scans.clear()
        self._suppressions.clear()
        logger.info("DriftDetector closed")

    def run_scan(self, target: Optional[str] = None, resource_types: Optional[List[str]] = None) -> Dict:
        scan_id = str(uuid.uuid4())
        scan = {
            "scan_id": scan_id,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "target": target or "all",
            "status": "running",
            "total_resources": 0,
            "drifted_resources": 0,
            "compliant_resources": 0,
            "errors": 0,
            "drifts": [],
            "resource_types_checked": resource_types or ["docker", "system"],
        }

        drifts = []
        total = 0
        drifted = 0
        compliant = 0
        errors = 0

        for resource_id, desired in DESIRED_STATES.items():
            if resource_types:
                resource_type = resource_id.split(":")[0]
                if resource_type not in resource_types:
                    continue
            if target and target not in resource_id:
                continue

            total += 1
            actual = self._collect_actual_state(resource_id)
            if actual is None:
                errors += 1
                continue

            resource_drifts = self._compare_states(resource_id, desired, actual)
            if resource_drifts:
                drifted += 1
                drifts.extend(resource_drifts)
            else:
                compliant += 1

        scan["completed_at"] = datetime.utcnow().isoformat()
        scan["status"] = "completed"
        scan["total_resources"] = total
        scan["drifted_resources"] = drifted
        scan["compliant_resources"] = compliant
        scan["errors"] = errors
        scan["drifts"] = drifts
        self._scans[scan_id] = scan

        logger.info(f"Drift scan {scan_id}: {drifted} drifted, {compliant} compliant, {errors} errors")
        return scan

    def _collect_actual_state(self, resource_id: str) -> Optional[Dict]:
        if resource_id == "docker:container:nginx":
            return {
                "image": "nginx:1.25-alpine",
                "restart_policy": "always",
                "ports": ["80:80"],
                "env": {"NGINX_HOST": "example.com"},
                "memory_limit": "256m",
                "labels": {"app": "nginx", "managed_by": "infrapilot"},
            }
        elif resource_id == "docker:container:postgres":
            return {
                "image": "postgres:16-alpine",
                "restart_policy": "always",
                "ports": ["5432:5432"],
                "memory_limit": "1g",
                "env": {"POSTGRES_DB": "infrapilot"},
            }
        elif resource_id == "system:ssh:config":
            return {
                "file_path": "/etc/ssh/sshd_config",
                "lines": [
                    "PermitRootLogin no",
                    "PasswordAuthentication no",
                    "PubkeyAuthentication yes",
                    "Port 2222",
                    "X11Forwarding yes",
                ],
            }
        return {"status": "unknown", "message": f"Resource {resource_id} not found"}

    def _compare_states(self, resource_id: str, desired: Dict, actual: Dict) -> List[Dict]:
        drifts = []
        for key, expected_value in desired.items():
            if key in ("expected_hash", "expected_lines", "expected_content_hash", "expected_settings"):
                continue
            actual_value = actual.get(key)
            if actual_value != expected_value:
                severity = self._determine_severity(key, resource_id)
                drifts.append({
                    "drift_id": str(uuid.uuid4()),
                    "resource_id": resource_id,
                    "field": key,
                    "expected": str(expected_value),
                    "actual": str(actual_value) if actual_value is not None else "NOT_SET",
                    "severity": severity,
                    "status": DriftStatus.DETECTED.value,
                    "detected_at": datetime.utcnow().isoformat(),
                    "remediation": f"Set {key} to {expected_value}",
                })
        return drifts

    def _determine_severity(self, field: str, resource_id: str) -> str:
        security_fields = {"memory_limit", "cpu_limit", "ports", "env"}
        if field in security_fields:
            return DriftSeverity.HIGH.value
        if field in ("image", "restart_policy"):
            return DriftSeverity.MEDIUM.value
        if field in ("labels", "healthcheck"):
            return DriftSeverity.LOW.value
        return DriftSeverity.MEDIUM.value

    def get_scan(self, scan_id: str) -> Optional[Dict]:
        scan = self._scans.get(scan_id)
        if not scan:
            return None
        filtered_drifts = [
            d for d in scan["drifts"]
            if not self._is_suppressed(d["drift_id"], d["resource_id"], d["field"])
        ]
        return {**scan, "drifts": filtered_drifts}

    def list_scans(self, limit: int = 50) -> List[Dict]:
        scans = list(self._scans.values())
        scans.sort(key=lambda s: s.get("started_at", ""), reverse=True)
        return [{
            "scan_id": s["scan_id"],
            "started_at": s["started_at"],
            "status": s["status"],
            "total_resources": s["total_resources"],
            "drifted_resources": s["drifted_resources"],
            "compliant_resources": s["compliant_resources"],
        } for s in scans[:limit]]

    def remediate_drift(self, drift_id: str) -> Dict:
        for scan in self._scans.values():
            for drift in scan["drifts"]:
                if drift["drift_id"] == drift_id:
                    drift["status"] = DriftStatus.REMEDIATED.value
                    drift["remediated_at"] = datetime.utcnow().isoformat()
                    return {"drift_id": drift_id, "status": "remediated", "remediation": drift["remediation"]}
        return {"error": "Drift not found"}

    def suppress_drift(self, resource_id: str, field: str, reason: str,
                        expires_at: Optional[str] = None) -> Dict:
        suppression_id = str(uuid.uuid4())
        suppression = {
            "suppression_id": suppression_id,
            "resource_id": resource_id,
            "field": field,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at,
            "created_by": "system",
        }
        key = f"{resource_id}:{field}"
        self._suppressions[key] = suppression
        logger.info(f"Drift suppression {suppression_id} for {resource_id}:{field}")
        return suppression

    def _is_suppressed(self, drift_id: str, resource_id: str, field: str) -> bool:
        key = f"{resource_id}:{field}"
        suppression = self._suppressions.get(key)
        if not suppression:
            return False
        if suppression.get("expires_at"):
            try:
                expiry = datetime.fromisoformat(suppression["expires_at"])
                if datetime.utcnow() > expiry:
                    del self._suppressions[key]
                    return False
            except (ValueError, TypeError):
                pass
        return True

    def list_suppressions(self) -> List[Dict]:
        return list(self._suppressions.values())

    def get_statistics(self) -> Dict[str, Any]:
        total_scans = len(self._scans)
        total_drifts = sum(len(s["drifts"]) for s in self._scans.values())
        severity_counts = {}
        for s in self._scans.values():
            for d in s["drifts"]:
                sev = d.get("severity", "medium")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
        return {
            "total_scans": total_scans,
            "total_drifts_detected": total_drifts,
            "active_suppressions": len(self._suppressions),
            "severity_breakdown": severity_counts,
            "resources_tracked": len(DESIRED_STATES),
        }
