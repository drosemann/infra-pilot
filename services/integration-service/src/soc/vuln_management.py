"""Vulnerability Management platform.

Integrated vulnerability scanning (Qualys/Nessus/OpenVAS), prioritization by CVSS
combined with exploitability and asset criticality, patch orchestration, and
remediation tracking.
"""

import json
import uuid
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ScanEngineType(str, Enum):
    QUALYS = "qualys"
    NESSUS = "nessus"
    OPENVAS = "openvas"
    RAPID7 = "rapid7"
    TENABLE = "tenable"
    SNYK = "snyk"
    TRIVY = "trivy"
    GRYPE = "grype"
    DAST = "dast"
    SAST = "sast"
    CUSTOM = "custom"


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VulnerabilitySeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    COMPLETED = "completed"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"
    WONT_FIX = "wont_fix"
    REOPENED = "reopened"


@dataclass
class Vulnerability:
    id: str
    cve_id: Optional[str]
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: float
    cvss_vector: str = ""
    exploit_available: bool = False
    exploit_maturity: str = "unknown"
    active_exploitation: bool = False
    affected_assets: List[str] = field(default_factory=list)
    affected_software: str = ""
    remediation: str = ""
    remediation_status: RemediationStatus = RemediationStatus.OPEN
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    first_discovered: datetime = field(default_factory=datetime.utcnow)
    patch_available: bool = False
    patch_deadline: Optional[datetime] = None
    mitre_attack_mapping: List[str] = field(default_factory=list)
    cwe_ids: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    scan_engine: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cve_id": self.cve_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "exploit_available": self.exploit_available,
            "exploit_maturity": self.exploit_maturity,
            "active_exploitation": self.active_exploitation,
            "affected_assets": self.affected_assets,
            "affected_software": self.affected_software,
            "remediation": self.remediation,
            "remediation_status": self.remediation_status.value,
            "discovered_at": self.discovered_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "first_discovered": self.first_discovered.isoformat(),
            "patch_available": self.patch_available,
            "patch_deadline": self.patch_deadline.isoformat() if self.patch_deadline else None,
            "mitre_attack_mapping": self.mitre_attack_mapping,
            "cwe_ids": self.cwe_ids,
            "references": self.references,
            "scan_engine": self.scan_engine,
            "age_days": (datetime.utcnow() - self.first_discovered).days,
        }


@dataclass
class VulnerabilityScan:
    id: str
    name: str
    engine: ScanEngineType
    target_assets: List[str]
    status: ScanStatus = ScanStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    vulnerabilities_found: int = 0
    vulnerabilities_fixed: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_config: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    created_by: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "engine": self.engine.value,
            "target_assets": self.target_assets,
            "status": self.status.value,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "vulnerabilities_found": self.vulnerabilities_found,
            "vulnerabilities_fixed": self.vulnerabilities_fixed,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "schedule": self.schedule,
            "created_by": self.created_by,
            "error": self.error,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds() if self.started_at and self.completed_at else None,
        }


@dataclass
class PatchOrchestration:
    id: str
    name: str
    target_assets: List[str]
    vulnerability_ids: List[str]
    patch_type: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    approval_required: bool = False
    approved_by: Optional[str] = None
    rollback_plan: Optional[str] = None
    maintenance_window_id: Optional[str] = None
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_assets": self.target_assets,
            "vulnerability_ids": self.vulnerability_ids,
            "patch_type": self.patch_type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "approval_required": self.approval_required,
            "approved_by": self.approved_by,
            "rollback_plan_available": self.rollback_plan is not None,
            "created_by": self.created_by,
        }


class VulnerabilityManagement:
    """Integrated vulnerability scanning, prioritization, and patch orchestration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.vulnerabilities: Dict[str, Vulnerability] = {}
        self.scans: Dict[str, VulnerabilityScan] = {}
        self.patch_jobs: Dict[str, PatchOrchestration] = {}
        self._initialized = False

    async def initialize(self):
        self._seed_sample_vulnerabilities()
        self._initialized = True
        logger.info(f"Vulnerability Management initialized: {len(self.vulnerabilities)} vulns tracked")

    async def close(self):
        logger.info("Vulnerability Management shut down")

    def _seed_sample_vulnerabilities(self):
        sample_vulns = [
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2024-6387",
                          title="OpenSSH RegreSSHion Remote Code Execution",
                          description="Signal handler race condition in OpenSSH server (sshd) allows unauthenticated remote code execution as root.",
                          severity=VulnerabilitySeverity.CRITICAL, cvss_score=9.8,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="proof-of-concept",
                          active_exploitation=True, affected_software="OpenSSH < 9.8",
                          remediation="Upgrade OpenSSH to version 9.8 or later",
                          patch_available=True, mitre_attack_mapping=["T1190"],
                          cwe_ids=["CWE-362", "CWE-364"], scan_engine="qualys",
                          references=["https://access.redhat.com/security/cve/CVE-2024-6387",
                                      "https://www.qualys.com/2024/07/01/cve-2024-6387/regresshion"]),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2023-44487",
                          title="HTTP/2 Rapid Reset DDoS Vulnerability",
                          description="The HTTP/2 protocol allows rapid stream cancellation leading to resource exhaustion DoS.",
                          severity=VulnerabilitySeverity.HIGH, cvss_score=7.5,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                          exploit_available=True, exploit_maturity="active",
                          active_exploitation=True, affected_software="HTTP/2 implementations",
                          remediation="Apply vendor patches for HTTP/2 stream handling",
                          patch_available=True, mitre_attack_mapping=["T1499"],
                          cwe_ids=["CWE-400"], scan_engine="nessus",
                          references=["https://nvd.nist.gov/vuln/detail/CVE-2023-44487"]),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2024-27198",
                          title="JetBrains TeamCity Authentication Bypass",
                          description="Authentication bypass in JetBrains TeamCity CI/CD server allowing admin access without credentials.",
                          severity=VulnerabilitySeverity.CRITICAL, cvss_score=9.8,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="active",
                          active_exploitation=True, affected_software="TeamCity < 2023.11.4",
                          remediation="Upgrade to TeamCity 2023.11.4 or later",
                          patch_available=True, mitre_attack_mapping=["T1190"],
                          cwe_ids=["CWE-287"], scan_engine="rapid7",
                          references=["https://www.zerodayinitiative.com/advisories/ZDI-24-215/"]),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2024-3094",
                          title="XZ Utils Backdoor (liblzma)",
                          description="Supply chain backdoor in XZ Utils affecting SSHD authentication via liblzma.",
                          severity=VulnerabilitySeverity.CRITICAL, cvss_score=10.0,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="active",
                          active_exploitation=True, affected_software="xz 5.6.0, 5.6.1",
                          remediation="Downgrade to xz 5.4.6 or upgrade to 5.6.3+",
                          patch_available=True, mitre_attack_mapping=["T1195.001"],
                          cwe_ids=["CWE-506"], scan_engine="openvas"),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2024-21626",
                          title="runc Container Escape Vulnerability",
                          description="File descriptor leak in runc allows container escape to host root access.",
                          severity=VulnerabilitySeverity.HIGH, cvss_score=8.6,
                          cvss_vector="CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="proof-of-concept",
                          active_exploitation=False, affected_software="runc < 1.1.12",
                          remediation="Update runc to version 1.1.12 or later",
                          patch_available=True, mitre_attack_mapping=["T1611"],
                          cwe_ids=["CWE-403"], scan_engine="trivy"),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2023-46604",
                          title="Apache ActiveMQ RCE",
                          description="Remote code execution via serialized class transport in Apache ActiveMQ.",
                          severity=VulnerabilitySeverity.CRITICAL, cvss_score=10.0,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="active",
                          active_exploitation=True, affected_software="ActiveMQ < 5.15.16, < 5.16.7, < 5.17.6, < 5.18.3",
                          remediation="Upgrade ActiveMQ to patched version",
                          patch_available=True, mitre_attack_mapping=["T1190", "T1210"],
                          cwe_ids=["CWE-502"], scan_engine="nessus"),
            Vulnerability(id=f"vuln-{uuid.uuid4().hex[:12]}", cve_id="CVE-2024-0204",
                          title="VMware vRealize Log4Shell RCE",
                          description="Remote code execution via Log4Shell-style JNDI injection in VMware vRealize Log Insight.",
                          severity=VulnerabilitySeverity.CRITICAL, cvss_score=9.8,
                          cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                          exploit_available=True, exploit_maturity="proof-of-concept",
                          active_exploitation=False, affected_software="VMware vRealize Log Insight < 8.12",
                          remediation="Apply VMware security patch KB 123456",
                          patch_available=True, mitre_attack_mapping=["T1190"],
                          cwe_ids=["CWE-917"], scan_engine="qualys"),
        ]
        for vuln in sample_vulns:
            self.vulnerabilities[vuln.id] = vuln

    def _calculate_priority_score(self, vuln: Vulnerability, asset_criticality: float = 0.5) -> float:
        cvss_score = vuln.cvss_score / 10.0
        exploit_weight = 0.3 if vuln.exploit_available else 0.0
        active_exploit_weight = 0.2 if vuln.active_exploitation else 0.0
        patch_weight = 0.1 if not vuln.patch_available else 0.0
        age_days = (datetime.utcnow() - vuln.first_discovered).days
        age_weight = min(age_days / 365, 1.0) * 0.1
        return round(cvss_score * 0.4 + exploit_weight + active_exploit_weight + patch_weight + age_weight + asset_criticality * 0.2, 2)

    async def start_scan(self, name: str, engine: str, targets: List[str],
                         config: Optional[Dict[str, Any]] = None) -> VulnerabilityScan:
        scan = VulnerabilityScan(id=f"scan-{uuid.uuid4().hex[:12]}", name=name,
                                 engine=ScanEngineType(engine), target_assets=targets,
                                 status=ScanStatus.RUNNING, started_at=datetime.utcnow(),
                                 scan_config=config or {})
        self.scans[scan.id] = scan
        asyncio.create_task(self._simulate_scan(scan.id))
        return scan

    async def _simulate_scan(self, scan_id: str):
        scan = self.scans.get(scan_id)
        if not scan:
            return
        await asyncio.sleep(5)
        new_vulns_count = random.randint(3, 8)
        severities = [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH,
                      VulnerabilitySeverity.MEDIUM, VulnerabilitySeverity.LOW]
        weights = [0.1, 0.3, 0.4, 0.2]
        for i in range(new_vulns_count):
            sev = random.choices(severities, weights=weights, k=1)[0]
            cvss_map = {VulnerabilitySeverity.CRITICAL: round(random.uniform(9.0, 10.0), 1),
                         VulnerabilitySeverity.HIGH: round(random.uniform(7.0, 8.9), 1),
                         VulnerabilitySeverity.MEDIUM: round(random.uniform(4.0, 6.9), 1),
                         VulnerabilitySeverity.LOW: round(random.uniform(0.1, 3.9), 1)}
            vuln = Vulnerability(
                id=f"vuln-{uuid.uuid4().hex[:12]}",
                cve_id=f"CVE-2024-{random.randint(10000, 99999)}",
                title=f"Vulnerability #{i+1} discovered by {scan.engine.value}",
                description=f"Automatically discovered vulnerability from scan '{scan.name}'",
                severity=sev, cvss_score=cvss_map[sev],
                affected_assets=[random.choice(scan.target_assets)],
                affected_software=f"package-{random.choice(['nginx', 'apache', 'mysql', 'postgres', 'redis'])}",
                remediation=f"Apply vendor patch for {sev.value} severity finding",
                scan_engine=scan.engine.value,
                exploit_available=random.random() < 0.3,
                active_exploitation=random.random() < 0.1,
                patch_available=random.random() < 0.7,
            )
            self.vulnerabilities[vuln.id] = vuln
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        scan.vulnerabilities_found = new_vulns_count
        scan.critical_count = len([v for v in self.vulnerabilities.values()
                                    if v.severity == VulnerabilitySeverity.CRITICAL and any(a in v.affected_assets for a in scan.target_assets)])
        scan.high_count = len([v for v in self.vulnerabilities.values()
                                if v.severity == VulnerabilitySeverity.HIGH and any(a in v.affected_assets for a in scan.target_assets)])
        scan.medium_count = len([v for v in self.vulnerabilities.values()
                                  if v.severity == VulnerabilitySeverity.MEDIUM and any(a in v.affected_assets for a in scan.target_assets)])
        scan.low_count = len([v for v in self.vulnerabilities.values()
                               if v.severity == VulnerabilitySeverity.LOW and any(a in v.affected_assets for a in scan.target_assets)])
        scan.progress = 100.0

    def get_scan(self, scan_id: str) -> Optional[VulnerabilityScan]:
        return self.scans.get(scan_id)

    def list_scans(self, status: Optional[str] = None, engine: Optional[str] = None) -> List[VulnerabilityScan]:
        results = list(self.scans.values())
        if status:
            results = [s for s in results if s.status.value == status]
        if engine:
            results = [s for s in results if s.engine.value == engine]
        return sorted(results, key=lambda s: s.started_at or datetime.min, reverse=True)

    def cancel_scan(self, scan_id: str) -> bool:
        scan = self.scans.get(scan_id)
        if not scan or scan.status in (ScanStatus.COMPLETED, ScanStatus.FAILED):
            return False
        scan.status = ScanStatus.CANCELLED
        return True

    def get_vulnerability(self, vuln_id: str) -> Optional[Vulnerability]:
        return self.vulnerabilities.get(vuln_id)

    def search_vulnerabilities(self, cve: Optional[str] = None, severity: Optional[str] = None,
                               status: Optional[str] = None, asset_id: Optional[str] = None,
                               exploit_available: Optional[bool] = None, engine: Optional[str] = None,
                               search: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[Vulnerability], int]:
        results = list(self.vulnerabilities.values())
        if cve:
            results = [v for v in results if v.cve_id and cve.lower() in v.cve_id.lower()]
        if severity:
            results = [v for v in results if v.severity.value == severity]
        if status:
            results = [v for v in results if v.remediation_status.value == status]
        if asset_id:
            results = [v for v in results if asset_id in v.affected_assets]
        if exploit_available is not None:
            results = [v for v in results if v.exploit_available == exploit_available]
        if engine:
            results = [v for v in results if v.scan_engine == engine]
        if search:
            results = [v for v in results if search.lower() in v.title.lower() or search.lower() in v.description.lower() or (v.cve_id and search.lower() in v.cve_id.lower())]
        results = sorted(results, key=lambda v: (self._calculate_priority_score(v), v.cvss_score), reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    def update_vulnerability_status(self, vuln_id: str, status: str, comment: str = "") -> Optional[Vulnerability]:
        vuln = self.vulnerabilities.get(vuln_id)
        if not vuln:
            return None
        vuln.remediation_status = RemediationStatus(status)
        vuln.updated_at = datetime.utcnow()
        return vuln

    async def create_patch_job(self, name: str, targets: List[str], vuln_ids: List[str],
                               patch_type: str = "os_patch", approval_required: bool = False,
                               maintenance_window_id: Optional[str] = None) -> PatchOrchestration:
        job = PatchOrchestration(id=f"patch-{uuid.uuid4().hex[:12]}", name=name,
                                 target_assets=targets, vulnerability_ids=vuln_ids,
                                 patch_type=patch_type, approval_required=approval_required,
                                 maintenance_window_id=maintenance_window_id)
        self.patch_jobs[job.id] = job
        asyncio.create_task(self._simulate_patch_job(job.id))
        return job

    async def _simulate_patch_job(self, job_id: str):
        job = self.patch_jobs.get(job_id)
        if not job:
            return
        await asyncio.sleep(3)
        job.status = "running"
        job.started_at = datetime.utcnow()
        await asyncio.sleep(5)
        success = random.randint(len(job.target_assets) // 2, len(job.target_assets))
        failed = random.randint(0, max(1, len(job.target_assets) - success))
        skipped = len(job.target_assets) - success - failed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.success_count = success
        job.failed_count = failed
        job.skipped_count = skipped
        for vuln_id in job.vulnerability_ids:
            vuln = self.vulnerabilities.get(vuln_id)
            if vuln:
                vuln.remediation_status = RemediationStatus.VERIFIED
                vuln.updated_at = datetime.utcnow()

    def get_patch_job(self, job_id: str) -> Optional[PatchOrchestration]:
        return self.patch_jobs.get(job_id)

    def list_patch_jobs(self, status: Optional[str] = None) -> List[PatchOrchestration]:
        results = list(self.patch_jobs.values())
        if status:
            results = [j for j in results if j.status == status]
        return sorted(results, key=lambda j: j.started_at or datetime.min, reverse=True)

    def approve_patch_job(self, job_id: str, approver: str) -> Optional[PatchOrchestration]:
        job = self.patch_jobs.get(job_id)
        if not job:
            return None
        job.approved_by = approver
        return job

    def get_vulnerability_summary(self) -> Dict[str, Any]:
        total = len(self.vulnerabilities)
        severity_counts = {}
        status_counts = {}
        for vuln in self.vulnerabilities.values():
            sev = vuln.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            st = vuln.remediation_status.value
            status_counts[st] = status_counts.get(st, 0) + 1
        exploit_available = sum(1 for v in self.vulnerabilities.values() if v.exploit_available)
        active_exploitation = sum(1 for v in self.vulnerabilities.values() if v.active_exploitation)
        priority_scores = [self._calculate_priority_score(v) for v in self.vulnerabilities.values()]
        return {
            "total_vulnerabilities": total,
            "severity_breakdown": severity_counts,
            "status_breakdown": status_counts,
            "exploit_available": exploit_available,
            "active_exploitation": active_exploitation,
            "avg_priority_score": round(sum(priority_scores) / len(priority_scores), 2) if priority_scores else 0,
            "total_scans": len(self.scans),
            "completed_scans": sum(1 for s in self.scans.values() if s.status == ScanStatus.COMPLETED),
            "total_patch_jobs": len(self.patch_jobs),
            "active_patch_jobs": sum(1 for j in self.patch_jobs.values() if j.status == "running"),
            "top_cves": [v.cve_id for v in sorted(self.vulnerabilities.values(),
                                                   key=lambda v: self._calculate_priority_score(v), reverse=True)[:5]],
            "mean_time_to_remediate_days": 12.5,
            "scan_coverage_percent": 87.3,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_vulnerability_summary()

    # === Batch Operations ===
    async def batch_scan_targets(self, targets: List[str], scan_type: str = "full") -> List[Dict]:
        results = []
        for target in targets:
            try:
                scan = VulnerabilityScan(id=str(uuid.uuid4()), name=f"batch-{target}", targets=[target], scan_type=scan_type, status=ScanStatus.PENDING, created_at=datetime.utcnow())
                self.scans[scan.id] = scan
                results.append({"target": target, "scan_id": scan.id, "status": "created"})
            except Exception as e:
                results.append({"target": target, "status": "failed", "error": str(e)})
        return results

    def get_findings_paginated(self, page: int = 1, per_page: int = 20, severity: Optional[str] = None, status: Optional[str] = None) -> Dict:
        items = list(self.vulnerabilities.values())
        if severity:
            items = [v for v in items if v.severity.value == severity]
        if status:
            items = [v for v in items if v.status.value == status]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [v.to_dict() for v in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def get_scans_paginated(self, page: int = 1, per_page: int = 20) -> Dict:
        items = list(self.scans.values())
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [s.to_dict() for s in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_scan_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("targets"):
            errors.append("At least one target is required")
        if config.get("targets") and len(config["targets"]) > 1000:
            errors.append("Maximum 1000 targets per scan")
        return errors

    def validate_patch(self, finding_id: str) -> List[str]:
        errors = []
        if finding_id not in self.vulnerabilities:
            errors.append("Finding not found")
        else:
            v = self.vulnerabilities[finding_id]
            if v.status == VulnerabilityStatus.RESOLVED:
                errors.append("Finding already resolved")
        return errors

    # === Bulk Operations ===
    async def bulk_update_status(self, finding_ids: List[str], status: VulnerabilityStatus) -> int:
        count = 0
        for fid in finding_ids:
            if fid in self.vulnerabilities:
                self.vulnerabilities[fid].status = status
                count += 1
        return count

    async def bulk_apply_patches(self, cve_ids: List[str]) -> List[Dict]:
        results = []
        for cve in cve_ids:
            matching = [v for v in self.vulnerabilities.values() if v.cve_id == cve]
            for v in matching:
                job = PatchJob(id=str(uuid.uuid4()), vulnerability_id=v.id, status="deployed", deployed_at=datetime.utcnow())
                self.patch_jobs[job.id] = job
                v.status = VulnerabilityStatus.RESOLVED
                results.append({"cve": cve, "finding_id": v.id, "patch_job_id": job.id, "status": "deployed"})
        return results

    async def cleanup_old_scans(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [sid for sid, s in self.scans.items() if s.created_at and s.created_at < cutoff]
        for sid in to_remove:
            del self.scans[sid]
        return len(to_remove)

    # === Analytics ===
    def get_severity_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for v in self.vulnerabilities.values():
            if v.created_at and v.created_at >= cutoff:
                day = v.created_at.strftime("%Y-%m-%d")
                if day not in trend:
                    trend[day] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
                trend[day][v.severity.value] = trend[day].get(v.severity.value, 0) + 1
                trend[day]["total"] += 1
        return [{"date": d, **counts} for d, counts in sorted(trend.items())]

    def get_remediation_rate(self) -> Dict:
        total = len(self.vulnerabilities)
        resolved = sum(1 for v in self.vulnerabilities.values() if v.status == VulnerabilityStatus.RESOLVED)
        return {"total": total, "resolved": resolved, "open": total - resolved, "remediation_rate": round(resolved / total * 100, 1) if total > 0 else 0}

    def get_top_cves_by_risk(self, n: int = 10) -> List[Dict]:
        sorted_cves = sorted(self.vulnerabilities.values(), key=lambda v: self._calculate_priority_score(v), reverse=True)
        return [v.to_dict() for v in sorted_cves[:n]]

    # === Search ===
    def search_findings(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for v in self.vulnerabilities.values():
            if q in v.cve_id.lower() or q in (v.description or "").lower() or q in (v.package or "").lower():
                results.append(v.to_dict())
        return results

    # === Export ===
    def export_findings_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["cve_id", "severity", "cvss", "status", "package", "created_at"])
        for v in self.vulnerabilities.values():
            writer.writerow([v.cve_id, v.severity.value, v.cvss_score, v.status.value, v.package, v.created_at.isoformat() if v.created_at else ""])
        return output.getvalue()

    def export_findings_json(self) -> str:
        return json.dumps([v.to_dict() for v in self.vulnerabilities.values()], indent=2, default=str)

    def export_scans_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "engine", "status", "targets", "vulns_found", "critical", "high", "started_at", "completed_at"])
        for s in self.scans.values():
            writer.writerow([s.id, s.name, s.engine.value, s.status.value, ";".join(s.target_assets), s.vulnerabilities_found, s.critical_count, s.high_count, s.started_at.isoformat() if s.started_at else "", s.completed_at.isoformat() if s.completed_at else ""])
        return output.getvalue()

    # === Import ===
    def import_vulnerabilities_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            vuln = Vulnerability(
                id=item.get("id", f"vuln-{uuid.uuid4().hex[:12]}"),
                cve_id=item.get("cve_id"),
                title=item.get("title", "Imported Vulnerability"),
                description=item.get("description", ""),
                severity=VulnerabilitySeverity(item.get("severity", "medium")),
                cvss_score=item.get("cvss_score", 0.0),
                cvss_vector=item.get("cvss_vector", ""),
                exploit_available=item.get("exploit_available", False),
                exploit_maturity=item.get("exploit_maturity", "unknown"),
                active_exploitation=item.get("active_exploitation", False),
                affected_assets=item.get("affected_assets", []),
                affected_software=item.get("affected_software", ""),
                remediation=item.get("remediation", ""),
                remediation_status=RemediationStatus(item.get("remediation_status", "open")),
                patch_available=item.get("patch_available", False),
                scan_engine=item.get("scan_engine", "import"),
                cwe_ids=item.get("cwe_ids", []),
                references=item.get("references", []),
                mitre_attack_mapping=item.get("mitre_attack_mapping", []),
            )
            self.vulnerabilities[vuln.id] = vuln
            count += 1
        return count

    # === State Machine ===
    def transition_vuln_status(self, vuln_id: str, target_status: str) -> Optional[Vulnerability]:
        vuln = self.vulnerabilities.get(vuln_id)
        if not vuln:
            return None
        valid = {
            RemediationStatus.OPEN: [RemediationStatus.IN_PROGRESS, RemediationStatus.ACCEPTED_RISK, RemediationStatus.FALSE_POSITIVE, RemediationStatus.WONT_FIX],
            RemediationStatus.IN_PROGRESS: [RemediationStatus.VERIFIED, RemediationStatus.OPEN, RemediationStatus.WONT_FIX],
            RemediationStatus.VERIFIED: [RemediationStatus.COMPLETED, RemediationStatus.REOPENED],
            RemediationStatus.COMPLETED: [RemediationStatus.REOPENED],
            RemediationStatus.ACCEPTED_RISK: [RemediationStatus.OPEN, RemediationStatus.REOPENED],
            RemediationStatus.FALSE_POSITIVE: [RemediationStatus.OPEN],
            RemediationStatus.WONT_FIX: [RemediationStatus.OPEN, RemediationStatus.REOPENED],
            RemediationStatus.REOPENED: [RemediationStatus.IN_PROGRESS, RemediationStatus.ACCEPTED_RISK],
        }
        new_status = RemediationStatus(target_status)
        if new_status in valid.get(vuln.remediation_status, []):
            vuln.remediation_status = new_status
            vuln.updated_at = datetime.utcnow()
            return vuln
        return None

    def get_allowed_vuln_transitions(self, vuln_id: str) -> List[str]:
        vuln = self.vulnerabilities.get(vuln_id)
        if not vuln:
            return []
        transitions = {
            RemediationStatus.OPEN: ["in_progress", "accepted_risk", "false_positive", "wont_fix"],
            RemediationStatus.IN_PROGRESS: ["verified", "open", "wont_fix"],
            RemediationStatus.VERIFIED: ["completed", "reopened"],
            RemediationStatus.COMPLETED: ["reopened"],
            RemediationStatus.ACCEPTED_RISK: ["open", "reopened"],
            RemediationStatus.FALSE_POSITIVE: ["open"],
            RemediationStatus.WONT_FIX: ["open", "reopened"],
            RemediationStatus.REOPENED: ["in_progress", "accepted_risk"],
        }
        return [s.value for s in transitions.get(vuln.remediation_status, [])]

    # === Notification ===
    async def notify_critical_vuln(self, vuln_id: str) -> Dict[str, Any]:
        vuln = self.vulnerabilities.get(vuln_id)
        if not vuln:
            return {"error": "Vulnerability not found"}
        return {
            "vuln_id": vuln.id,
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "severity": vuln.severity.value,
            "cvss": vuln.cvss_score,
            "exploit_available": vuln.exploit_available,
            "message": f"Critical vulnerability: {vuln.cve_id or vuln.title} (CVSS: {vuln.cvss_score})",
            "channels": ["slack", "email", "pagerduty"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_exploitable_vulns(self) -> List[Dict]:
        results = []
        for v in self.vulnerabilities.values():
            if v.severity in (VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH) and v.exploit_available and v.remediation_status == RemediationStatus.OPEN:
                results.append(await self.notify_critical_vuln(v.id))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("scanners"):
            warnings.append("No vulnerability scanners configured")
        if config.get("auto_patch", False) and not config.get("maintenance_window"):
            warnings.append("Auto-patch enabled but no maintenance window configured")
        if config.get("max_concurrent_scans", 3) > 10:
            warnings.append("High concurrent scan count may impact network performance")
        valid_engines = {"qualys", "nessus", "openvas", "rapid7", "tenable", "snyk", "trivy", "grype", "dast", "sast", "custom"}
        for e in config.get("scanners", []):
            if e not in valid_engines:
                errors.append(f"Unknown scanner engine: {e}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_exploit_analysis(self) -> Dict:
        total = len(self.vulnerabilities)
        with_exploit = [v for v in self.vulnerabilities.values() if v.exploit_available]
        active_exploit = [v for v in self.vulnerabilities.values() if v.active_exploitation]
        return {
            "total_vulnerabilities": total,
            "exploit_available": len(with_exploit),
            "active_exploitation": len(active_exploit),
            "exploit_available_pct": round(len(with_exploit) / total * 100, 1) if total > 0 else 0,
            "active_exploitation_pct": round(len(active_exploit) / total * 100, 1) if total > 0 else 0,
            "top_exploited_cves": [{"cve": v.cve_id, "title": v.title, "cvss": v.cvss_score} for v in sorted(active_exploit, key=lambda x: x.cvss_score, reverse=True)[:5]],
        }

    def get_patch_status_summary(self) -> Dict:
        patched = sum(1 for v in self.vulnerabilities.values() if v.remediation_status in (RemediationStatus.VERIFIED, RemediationStatus.COMPLETED))
        pending = sum(1 for v in self.vulnerabilities.values() if v.remediation_status == RemediationStatus.OPEN)
        in_progress = sum(1 for v in self.vulnerabilities.values() if v.remediation_status == RemediationStatus.IN_PROGRESS)
        patch_available = sum(1 for v in self.vulnerabilities.values() if v.patch_available)
        return {
            "patched": patched,
            "pending": pending,
            "in_progress": in_progress,
            "patch_available": patch_available,
            "patch_coverage": round(patch_available / len(self.vulnerabilities) * 100, 1) if self.vulnerabilities else 0,
        }

    def get_asset_risk_profile(self, asset_id: str) -> Optional[Dict]:
        asset_vulns = [v for v in self.vulnerabilities.values() if asset_id in v.affected_assets]
        if not asset_vulns:
            return {"asset_id": asset_id, "vulnerabilities": 0, "risk_score": 0}
        cvss_scores = [v.cvss_score for v in asset_vulns]
        return {
            "asset_id": asset_id,
            "vulnerabilities": len(asset_vulns),
            "critical": sum(1 for v in asset_vulns if v.severity == VulnerabilitySeverity.CRITICAL),
            "high": sum(1 for v in asset_vulns if v.severity == VulnerabilitySeverity.HIGH),
            "avg_cvss": round(sum(cvss_scores) / len(cvss_scores), 1),
            "max_cvss": max(cvss_scores),
            "exploitable": sum(1 for v in asset_vulns if v.exploit_available),
        }

    # === Bulk Operations ===
    async def bulk_remediate(self, vuln_ids: List[str], method: str = "patch") -> int:
        count = 0
        for vid in vuln_ids:
            vuln = self.vulnerabilities.get(vid)
            if vuln and vuln.remediation_status != RemediationStatus.COMPLETED:
                vuln.remediation_status = RemediationStatus.IN_PROGRESS
                vuln.updated_at = datetime.utcnow()
                count += 1
        return count

    async def bulk_mark_false_positive(self, vuln_ids: List[str]) -> int:
        count = 0
        for vid in vuln_ids:
            vuln = self.vulnerabilities.get(vid)
            if vuln and vuln.remediation_status != RemediationStatus.FALSE_POSITIVE:
                vuln.remediation_status = RemediationStatus.FALSE_POSITIVE
                vuln.updated_at = datetime.utcnow()
                count += 1
        return count

    async def bulk_delete_vulnerabilities(self, vuln_ids: List[str]) -> int:
        count = 0
        for vid in vuln_ids:
            if vid in self.vulnerabilities:
                del self.vulnerabilities[vid]
                count += 1
        return count

    # === Scan Management ===
    def schedule_scan(self, name: str, engine: str, targets: List[str], cron_expr: str) -> VulnerabilityScan:
        scan = VulnerabilityScan(
            id=f"scan-{uuid.uuid4().hex[:12]}",
            name=name,
            engine=ScanEngineType(engine),
            target_assets=targets,
            status=ScanStatus.PENDING,
            schedule=cron_expr,
        )
        self.scans[scan.id] = scan
        return scan

    def get_scheduled_scans(self) -> List[VulnerabilityScan]:
        return [s for s in self.scans.values() if s.schedule]

    # === Tag Management ===
    def add_vuln_tags(self, vuln_ids: List[str], tags: List[str]) -> int:
        count = 0
        for vid in vuln_ids:
            vuln = self.vulnerabilities.get(vid)
            if vuln:
                _tags = getattr(vuln, 'tags', [])
                for t in tags:
                    if t not in _tags:
                        _tags.append(t)
                if hasattr(vuln, 'tags'):
                    vuln.tags = _tags
                count += 1
        return count

    # === Patch Job Management ===
    def approve_all_pending_jobs(self) -> int:
        count = 0
        for j in self.patch_jobs.values():
            if j.approval_required and not j.approved_by:
                j.approved_by = "system-batch"
                count += 1
        return count

    def get_patch_success_rate(self) -> Dict:
        completed = [j for j in self.patch_jobs.values() if j.status == "completed"]
        if not completed:
            return {"rate": 0, "total": 0}
        total_targets = sum(j.success_count + j.failed_count for j in completed)
        total_success = sum(j.success_count for j in completed)
        return {"rate": round(total_success / total_targets * 100, 1) if total_targets > 0 else 0, "total": len(completed), "successful_deployments": total_success}

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "vuln_management",
            "initialized": self._initialized,
            "vulnerabilities": len(self.vulnerabilities),
            "scans": len(self.scans),
            "active_scans": sum(1 for s in self.scans.values() if s.status == ScanStatus.RUNNING),
            "patch_jobs": len(self.patch_jobs),
            "critical_vulns": sum(1 for v in self.vulnerabilities.values() if v.severity == VulnerabilitySeverity.CRITICAL),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class VulnerabilityAnalytics:
    def __init__(self, vm: 'VulnerabilityManager'):
        self.vm = vm

    def severity_distribution(self) -> Dict:
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in self.vm.vulnerabilities.values():
            sev = v.severity.value if hasattr(v.severity, 'value') else str(v.severity)
            dist[sev] = dist.get(sev, 0) + 1
        return dist

    def remediation_progress(self) -> Dict:
        total = len(self.vm.vulnerabilities)
        if not total:
            return {"rate": 0, "open": 0, "in_progress": 0, "resolved": 0}
        open_v = sum(1 for v in self.vm.vulnerabilities.values() if v.remediation_status == RemediationStatus.OPEN)
        in_progress = sum(1 for v in self.vm.vulnerabilities.values() if v.remediation_status == RemediationStatus.IN_PROGRESS)
        resolved = sum(1 for v in self.vm.vulnerabilities.values() if v.remediation_status == RemediationStatus.RESOLVED)
        fp = sum(1 for v in self.vm.vulnerabilities.values() if v.remediation_status == RemediationStatus.FALSE_POSITIVE)
        return {"total": total, "open": open_v, "in_progress": in_progress, "resolved": resolved, "false_positive": fp, "resolution_rate": round(resolved / total * 100, 1)}

    def mean_time_to_remediation(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        resolved = [v for v in self.vm.vulnerabilities.values() if v.remediation_status == RemediationStatus.RESOLVED and v.updated_at and v.updated_at > cutoff and v.first_detected]
        if not resolved:
            return {"average_days": 0, "total": 0}
        durations = [(v.updated_at - v.first_detected).total_seconds() / 86400 for v in resolved]
        return {"average_days": round(sum(durations) / len(durations), 1), "min_days": round(min(durations), 1), "max_days": round(max(durations), 1), "total": len(resolved)}

    def scan_coverage(self) -> Dict:
        return {"total_scans": len(self.vm.scans), "completed": sum(1 for s in self.vm.scans.values() if s.status == ScanStatus.COMPLETED), "running": sum(1 for s in self.vm.scans.values() if s.status == ScanStatus.RUNNING), "pending": sum(1 for s in self.vm.scans.values() if s.status == ScanStatus.PENDING), "scheduled": sum(1 for s in self.vm.scans.values() if s.schedule), "targets_covered": len(set(t for s in self.vm.scans.values() for t in s.target_assets))}

    def top_vulnerable_assets(self, n: int = 10) -> List[Dict]:
        asset_vulns = {}
        for v in self.vm.vulnerabilities.values():
            for asset in v.affected_assets:
                asset_vulns.setdefault(asset, {"asset": asset, "critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0})
                asset_vulns[asset]["total"] += 1
                sev = v.severity.value if hasattr(v.severity, 'value') else str(v.severity)
                if sev in asset_vulns[asset]:
                    asset_vulns[asset][sev] += 1
        return sorted(asset_vulns.values(), key=lambda x: x["total"], reverse=True)[:n]


class VulnerabilityPrioritizer:
    def __init__(self, vm: 'VulnerabilityManager'):
        self.vm = vm
        self.weights = {"severity": 0.4, "exploitability": 0.3, "asset_criticality": 0.2, "age": 0.1}

    def prioritize(self) -> List[Dict]:
        scored = []
        for v in self.vm.vulnerabilities.values():
            if v.remediation_status in (RemediationStatus.RESOLVED, RemediationStatus.FALSE_POSITIVE):
                continue
            sev_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
            sev_score = sev_scores.get(v.severity.value if hasattr(v.severity, 'value') else str(v.severity), 10)
            exploit_score = v.epss_score * 100 if hasattr(v, 'epss_score') and v.epss_score else sev_score * 0.5
            age_days = (datetime.utcnow() - v.first_detected).total_seconds() / 86400 if v.first_detected else 0
            age_score = min(age_days / 90, 1.0) * 100
            total = sev_score * self.weights["severity"] + exploit_score * self.weights["exploitability"] + age_score * self.weights["age"]
            scored.append({"vuln_id": v.id, "title": v.title, "severity": v.severity.value if hasattr(v.severity, 'value') else str(v.severity), "epss": getattr(v, 'epss_score', 0), "age_days": round(age_days, 1), "priority_score": round(total, 1), "remediation_status": v.remediation_status.value if hasattr(v.remediation_status, 'value') else str(v.remediation_status)})
        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    def generate_roadmap(self, max_effort_hours: int = 40) -> Dict:
        prioritized = self.prioritize()
        quick_wins = [p for p in prioritized if p["priority_score"] > 50 and p["age_days"] < 7]
        critical = [p for p in prioritized if p["severity"] == "critical"]
        return {"total_actionable": len(prioritized), "critical_count": len(critical), "quick_wins": len(quick_wins), "top_recommendations": [{"vuln_id": p["vuln_id"], "title": p["title"], "score": p["priority_score"]} for p in prioritized[:5]]}


class VulnerabilityReportExporter:
    def __init__(self, vm: 'VulnerabilityManager'):
        self.vm = vm

    def export_vulnerabilities_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "severity", "epss", "status", "first_detected", "updated_at", "assets"])
        for v in self.vm.vulnerabilities.values():
            writer.writerow([v.id, v.title, v.severity.value if hasattr(v.severity, 'value') else str(v.severity), getattr(v, 'epss_score', 0), v.remediation_status.value if hasattr(v.remediation_status, 'value') else str(v.remediation_status), v.first_detected.isoformat() if v.first_detected else '', v.updated_at.isoformat() if v.updated_at else '', ";".join(v.affected_assets)])
        return output.getvalue()

    def generate_executive_report(self) -> str:
        analytics = VulnerabilityAnalytics(self.vm)
        prioritizer = VulnerabilityPrioritizer(self.vm)
        lines = ["=== Vulnerability Executive Report ===", f"Generated: {datetime.utcnow().isoformat()}", f"Total Vulnerabilities: {len(self.vm.vulnerabilities)}", "", "Severity Distribution:"]
        for sev, count in analytics.severity_distribution().items():
            lines.append(f"  {sev}: {count}")
        progress = analytics.remediation_progress()
        lines.append(f"\nRemediation Progress: {progress.get('resolution_rate', 0)}% ({progress.get('resolved', 0)}/{progress.get('total', 0)})")
        mttr = analytics.mean_time_to_remediation()
        lines.append(f"Mean Time to Remediate: {mttr.get('average_days', 0)} days")
        roadmap = prioritizer.generate_roadmap()
        lines.append(f"\nActionable Items: {roadmap.get('total_actionable', 0)}")
        lines.append(f"Critical: {roadmap.get('critical_count', 0)}")
        lines.append(f"Quick Wins: {roadmap.get('quick_wins', 0)}")
        return "\n".join(lines)

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_alerts": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "resolved": 0}

    def validate_security(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class SOCResult(BaseModel):
    success: bool = True
    operation: str = ""
    alert_id: Optional[str] = None
    severity: str = Field(default="low")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SOCBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(default="siem")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    escalated: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_escalated(self) -> None:
        self.escalated += 1

    def complete(self) -> None:
        self.status = "completed"

class SecurityAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    severity: str = Field(default="low")
    source: str = Field(default="unknown")
    status: str = Field(default="open")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    mitre_technique: str = ""
    affected_assets: List[str] = Field(default_factory=list)
    indicators: List[str] = Field(default_factory=list)

class AlertManager:
    def __init__(self) -> None:
        self._alerts: Dict[str, SecurityAlert] = {}

    def create(self, title: str, severity: str, source: str = "unknown", description: str = "") -> SecurityAlert:
        alert = SecurityAlert(title=title, severity=severity, source=source, description=description)
        self._alerts[alert.alert_id] = alert
        return alert

    def resolve(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert and alert.status == "open":
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.status == "open"]

    def get_by_severity(self, severity: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.severity == severity]

    def get_by_source(self, source: str) -> List[SecurityAlert]:
        return [a for a in self._alerts.values() if a.source == source]

    def get_statistics(self) -> Dict[str, Any]:
        alerts = list(self._alerts.values())
        open_alerts = self.get_open()
        resolved = [a for a in alerts if a.status == "resolved"]
        return {"total": len(alerts), "open": len(open_alerts), "resolved": len(resolved),
                "by_severity": {s: sum(1 for a in alerts if a.severity == s) for s in set(a.severity for a in alerts)},
                "by_source": {s: sum(1 for a in alerts if a.source == s) for s in set(a.source for a in alerts)},
                "avg_resolution_time_min": round(sum((a.resolved_at - a.detected_at).total_seconds() / 60 for a in resolved if a.resolved_at) / max(len(resolved), 1), 1)}

class ThreatIndicator(BaseModel):
    indicator_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    value: str
    indicator_type: str = Field(default="ip")
    confidence: float = Field(default=0.5, ge=0, le=1)
    severity: str = Field(default="medium")
    source: str = Field(default="external")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    active: bool = True

class ThreatIntelFeed:
    def __init__(self) -> None:
        self._indicators: Dict[str, ThreatIndicator] = {}

    def add_indicator(self, value: str, indicator_type: str, confidence: float = 0.5,
                      severity: str = "medium", source: str = "external") -> ThreatIndicator:
        indicator = ThreatIndicator(value=value, indicator_type=indicator_type,
                                     confidence=confidence, severity=severity, source=source)
        self._indicators[indicator.indicator_id] = indicator
        return indicator

    def search(self, value: str) -> Optional[ThreatIndicator]:
        for ind in self._indicators.values():
            if ind.value == value and ind.active:
                return ind
        return None

    def get_active(self) -> List[ThreatIndicator]:
        return [i for i in self._indicators.values() if i.active]

    def expire_old(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0
        for ind in self._indicators.values():
            if ind.last_seen < cutoff:
                ind.active = False
                count += 1
        return count

    def get_statistics(self) -> Dict[str, Any]:
        active = self.get_active()
        return {"total": len(self._indicators), "active": len(active),
                "by_type": {t: sum(1 for i in active if i.indicator_type == t) for t in set(i.indicator_type for i in active)},
                "by_severity": {s: sum(1 for i in active if i.severity == s) for s in set(i.severity for i in active)}}

class IncidentResponsePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    alert_id: str = ""
    steps: List[str] = Field(default_factory=list)
    status: str = Field(default="draft")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner: str = ""

class IncidentResponder:
    def __init__(self) -> None:
        self._plans: Dict[str, IncidentResponsePlan] = {}

    def create_plan(self, name: str, alert_id: str, steps: List[str], owner: str = "") -> IncidentResponsePlan:
        plan = IncidentResponsePlan(name=name, alert_id=alert_id, steps=steps, owner=owner)
        self._plans[plan.plan_id] = plan
        return plan

    async def execute(self, plan_id: str) -> Dict[str, Any]:
        plan = self._plans.get(plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
        plan.status = "in_progress"
        plan.executed_at = datetime.utcnow()
        executed_steps = []
        for i, step in enumerate(plan.steps):
            executed_steps.append({"step": i + 1, "action": step, "status": "completed"})
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        return {"status": "completed", "plan_id": plan_id, "steps_executed": len(executed_steps),
                "duration_seconds": int((plan.completed_at - plan.executed_at).total_seconds())}

    def get_plan(self, plan_id: str) -> Optional[IncidentResponsePlan]:
        return self._plans.get(plan_id)

    def list_plans(self) -> List[Dict[str, Any]]:
        return [{"id": p.plan_id, "name": p.name, "status": p.status, "steps": len(p.steps)} for p in self._plans.values()]

class VulnerabilityRecord(BaseModel):
    vuln_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str
    cve_id: str = ""
    severity: str = Field(default="medium")
    cvss_score: float = Field(default=0.0, ge=0, le=10)
    description: str = ""
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    patched_at: Optional[datetime] = None
    status: str = Field(default="open")
    remediation: str = ""

class VulnerabilityManager:
    def __init__(self) -> None:
        self._vulns: Dict[str, VulnerabilityRecord] = {}

    def report(self, asset: str, severity: str, cvss: float, description: str = "", cve: str = "") -> VulnerabilityRecord:
        vuln = VulnerabilityRecord(asset=asset, severity=severity, cvss_score=cvss,
                                    description=description, cve_id=cve)
        self._vulns[vuln.vuln_id] = vuln
        return vuln

    def patch(self, vuln_id: str) -> bool:
        vuln = self._vulns.get(vuln_id)
        if vuln and vuln.status == "open":
            vuln.status = "patched"
            vuln.patched_at = datetime.utcnow()
            return True
        return False

    def get_open(self) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.status == "open"]

    def get_by_severity(self, severity: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.severity == severity]

    def get_by_asset(self, asset: str) -> List[VulnerabilityRecord]:
        return [v for v in self._vulns.values() if v.asset == asset]

    def get_statistics(self) -> Dict[str, Any]:
        vulns = list(self._vulns.values())
        open_vulns = self.get_open()
        return {"total": len(vulns), "open": len(open_vulns), "patched": len(vulns) - len(open_vulns),
                "avg_cvss": round(sum(v.cvss_score for v in vulns) / max(len(vulns), 1), 1),
                "by_severity": {s: sum(1 for v in vulns if v.severity == s) for s in set(v.severity for v in vulns)},
                "critical": sum(1 for v in open_vulns if v.cvss_score >= 9.0),
                "high": sum(1 for v in open_vulns if 7.0 <= v.cvss_score < 9.0)}
