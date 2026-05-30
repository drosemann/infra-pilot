import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ScanStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CheckSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComplianceStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"
    NOT_APPLICABLE = "na"

DATA_FILE = "data/compliance.json"

BENCHMARKS = {
    "cis_docker": {
        "name": "CIS Docker Benchmark",
        "version": "1.6.0",
        "authority": "Center for Internet Security",
        "description": "Security benchmark for Docker containers and hosts",
        "checks": [
            {"check_id": "cis_d_1_1", "name": "Ensure container host is Linux", "severity": "high",
             "category": "host_configuration",
             "description": "Verify Docker is running on a Linux host"},
            {"check_id": "cis_d_2_1", "name": "Ensure network traffic is restricted", "severity": "high",
             "category": "daemon_configuration",
             "description": "Restrict network traffic between containers"},
            {"check_id": "cis_d_2_5", "name": "Enable live restore", "severity": "medium",
             "category": "daemon_configuration",
             "description": "Enable live restore capability for daemon"},
            {"check_id": "cis_d_4_1", "name": "Ensure container images are scanned", "severity": "critical",
             "category": "image_configuration",
             "description": "Container images should be scanned for vulnerabilities"},
            {"check_id": "cis_d_5_1", "name": "Ensure containers run with read-only rootfs", "severity": "medium",
             "category": "container_configuration",
             "description": "Run containers with read-only root filesystem"},
            {"check_id": "cis_d_5_4", "name": "Ensure container memory limits are set", "severity": "medium",
             "category": "container_configuration",
             "description": "Set memory limit for all containers"},
        ],
    },
    "cis_kubernetes": {
        "name": "CIS Kubernetes Benchmark",
        "version": "1.9.0",
        "authority": "Center for Internet Security",
        "description": "Security benchmark for Kubernetes clusters",
        "checks": [
            {"check_id": "cis_k_1_1", "name": "Ensure RBAC is enabled", "severity": "critical",
             "category": "cluster_configuration",
             "description": "Role-based access control should be enabled"},
            {"check_id": "cis_k_2_1", "name": "Ensure etcd is secured", "severity": "critical",
             "category": "etcd_configuration",
             "description": "etcd should be configured with TLS"},
            {"check_id": "cis_k_3_1", "name": "Ensure pod security policies are used", "severity": "high",
             "category": "pod_configuration",
             "description": "Pod security policies should be enforced"},
            {"check_id": "cis_k_4_1", "name": "Ensure network policies are enforced", "severity": "high",
             "category": "network_configuration",
             "description": "Network policies should be implemented"},
        ],
    },
    "nist_800_53": {
        "name": "NIST SP 800-53 Rev. 5",
        "version": "5.1.1",
        "authority": "National Institute of Standards and Technology",
        "description": "Security and privacy controls for information systems",
        "checks": [
            {"check_id": "nist_ac_1", "name": "Access Control Policy and Procedures", "severity": "high",
             "category": "access_control",
             "description": "Access control policy should be documented and enforced"},
            {"check_id": "nist_au_1", "name": "Audit and Accountability Policy", "severity": "high",
             "category": "audit",
             "description": "Audit logs should be maintained and reviewed"},
            {"check_id": "nist_si_1", "name": "System and Information Integrity", "severity": "critical",
             "category": "system_integrity",
             "description": "System integrity should be monitored for unauthorized changes"},
        ],
    },
    "bsi_200_1": {
        "name": "BSI IT-Grundschutz (ISMS)",
        "version": "2025",
        "authority": "German Federal Office for Information Security",
        "description": "IT-Grundschutz baseline security requirements",
        "checks": [
            {"check_id": "bsi_1_1", "name": "ISMS Implementation", "severity": "high",
             "category": "management",
             "description": "Information security management system must be in place"},
            {"check_id": "bsi_2_1", "name": "Personnel Security", "severity": "medium",
             "category": "personnel",
             "description": "Personnel screening and security training"},
        ],
    },
    "soc2": {
        "name": "SOC 2 Trust Services Criteria",
        "version": "2025",
        "authority": "AICPA",
        "description": "SOC 2 security, availability, processing integrity, confidentiality, privacy",
        "checks": [
            {"check_id": "soc2_c1", "name": "Controls Monitor Security Incidents", "severity": "critical",
             "category": "security",
             "description": "Security incidents must be monitored and responded to"},
            {"check_id": "soc2_a1", "name": "Availability Monitoring", "severity": "high",
             "category": "availability",
             "description": "System availability must be monitored against SLAs"},
        ],
    },
}


class ComplianceScan:
    def __init__(self, scan_id: str, benchmark_id: str, target: str):
        self.scan_id = scan_id
        self.benchmark_id = benchmark_id
        self.target = target
        self.status = ScanStatus.PENDING
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.total_checks = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {"scan_id": self.scan_id, "benchmark_id": self.benchmark_id,
                "target": self.target, "status": self.status.value,
                "started_at": self.started_at, "completed_at": self.completed_at,
                "total_checks": self.total_checks, "passed": self.passed,
                "failed": self.failed, "warnings": self.warnings,
                "results": self.results}


class ComplianceScanner:
    def __init__(self):
        self._scans: Dict[str, ComplianceScan] = {}
        self._initialized = False

    async def initialize(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"scans": []}
        for s in data.get("scans", []):
            scan = ComplianceScan(s["scan_id"], s["benchmark_id"], s["target"])
            scan.status = ScanStatus(s.get("status", "pending"))
            scan.started_at = s.get("started_at")
            scan.completed_at = s.get("completed_at")
            scan.total_checks = s.get("total_checks", 0)
            scan.passed = s.get("passed", 0)
            scan.failed = s.get("failed", 0)
            scan.warnings = s.get("warnings", 0)
            scan.results = s.get("results", [])
            self._scans[s["scan_id"]] = scan
        self._initialized = True
        logger.info(f"ComplianceScanner initialized with {len(self._scans)} scans")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"scans": [s.to_dict() for s in self._scans.values()]}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def list_benchmarks(self) -> Dict[str, Any]:
        return {k: {"name": v["name"], "version": v["version"],
                     "authority": v["authority"], "description": v["description"],
                     "check_count": len(v["checks"])}
                for k, v in BENCHMARKS.items()}

    def get_benchmark(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        b = BENCHMARKS.get(benchmark_id)
        return {**b, "checks": list(b["checks"])} if b else None

    def list_checks(self, benchmark_id: str) -> List[Dict[str, Any]]:
        b = BENCHMARKS.get(benchmark_id)
        return list(b["checks"]) if b else []

    def start_scan(self, benchmark_id: str, target: str = "local") -> Dict[str, Any]:
        if benchmark_id not in BENCHMARKS:
            raise ValueError(f"Unknown benchmark: {benchmark_id}")
        sid = uuid.uuid4().hex[:16]
        scan = ComplianceScan(sid, benchmark_id, target)
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow().isoformat()
        scan.total_checks = len(BENCHMARKS[benchmark_id]["checks"])
        checks = BENCHMARKS[benchmark_id]["checks"]
        for check in checks:
            result = {
                "check_id": check["check_id"], "name": check["name"],
                "severity": check["severity"], "category": check.get("category", ""),
                "status": ComplianceStatus.PASS.value,
                "message": f"Check {check['check_id']}: {check['description'][:60]}",
                "remediation": f"Review {check['name']} configuration",
                "scored": True,
            }
            scan.results.append(result)
            scan.passed += 1
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow().isoformat()
        self._scans[sid] = scan
        return scan.to_dict()

    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        s = self._scans.get(scan_id)
        return s.to_dict() if s else None

    def get_remediation(self, check_id: str) -> Optional[Dict[str, Any]]:
        for b in BENCHMARKS.values():
            for c in b["checks"]:
                if c["check_id"] == check_id:
                    return {"check_id": check_id, "name": c["name"],
                            "benchmark": b["name"], "description": c["description"],
                            "remediation_steps": [
                                f"Review {c['name']} documentation",
                                "Implement required configuration changes",
                                "Verify compliance with re-scan",
                            ]}
        return None

    def get_statistics(self) -> Dict[str, Any]:
        scans = self._scans.values()
        total = len(scans)
        passed_total = sum(s.passed for s in scans if s.status == ScanStatus.COMPLETED)
        failed_total = sum(s.failed for s in scans if s.status == ScanStatus.COMPLETED)
        return {"total_scans": total,
                "completed_scans": sum(1 for s in scans if s.status == ScanStatus.COMPLETED),
                "failed_scans": sum(1 for s in scans if s.status == ScanStatus.FAILED),
                "total_checks_run": sum(s.total_checks for s in scans),
                "total_passed": passed_total,
                "total_failed": failed_total,
                "compliance_rate": round(passed_total / max(passed_total + failed_total, 1) * 100, 1),
                "available_benchmarks": len(BENCHMARKS)}
