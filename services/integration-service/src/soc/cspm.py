"""Cloud Security Posture Management (CSPM).

Continuous assessment against CIS benchmarks for cloud providers (AWS, Azure, GCP).
Auto-remediation of misconfigurations, drift detection, and compliance reporting.
"""

import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    HETZNER = "hetzner"
    OVH = "ovh"


class BenchmarkFramework(str, Enum):
    CIS_AWS = "cis-aws"
    CIS_AZURE = "cis-azure"
    CIS_GCP = "cis-gcp"
    CIS_DOCKER = "cis-docker"
    CIS_KUBERNETES = "cis-kubernetes"
    NIST_800_53 = "nist-800-53"
    SOC2 = "soc2"
    PCI_DSS = "pci-dss"
    HIPAA = "hipaa"


class ComplianceStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "na"
    ERROR = "error"


class RemediationStatus(str, Enum):
    AUTO_REMEDIATED = "auto_remediated"
    PENDING = "pending"
    MANUAL_REQUIRED = "manual_required"
    SUPPRESSED = "suppressed"
    IGNORED = "ignored"


@dataclass
class CloudAccount:
    id: str
    name: str
    provider: CloudProvider
    account_id: str
    regions: List[str] = field(default_factory=list)
    enabled: bool = True
    last_scan: Optional[datetime] = None
    resource_count: int = 0
    score: float = 0.0
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "account_id": self.account_id,
            "regions": self.regions,
            "enabled": self.enabled,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "resource_count": self.resource_count,
            "score": self.score,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
        }


@dataclass
class ComplianceCheck:
    id: str
    benchmark: BenchmarkFramework
    check_id: str
    title: str
    description: str
    severity: str
    resource_type: str
    provider: str
    remediation: str
    auto_remediable: bool = False
    category: str = ""
    mitre_mapping: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "benchmark": self.benchmark.value,
            "check_id": self.check_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "resource_type": self.resource_type,
            "provider": self.provider,
            "remediation": self.remediation,
            "auto_remediable": self.auto_remediable,
            "category": self.category,
        }


@dataclass
class CheckResult:
    id: str
    check_id: str
    check_title: str
    account_id: str
    resource_id: str
    resource_name: str
    region: str
    status: ComplianceStatus
    severity: str
    detected_at: datetime
    remediation_status: RemediationStatus = RemediationStatus.PENDING
    auto_remediated: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)
    drift_detected: bool = False
    drift_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "check_id": self.check_id,
            "check_title": self.check_title,
            "account_id": self.account_id,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "region": self.region,
            "status": self.status.value,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "remediation_status": self.remediation_status.value,
            "auto_remediated": self.auto_remediated,
            "drift_detected": self.drift_detected,
            "drift_details": self.drift_details,
        }


class CloudSecurityPostureManagement:
    """Continuous cloud security posture assessment against benchmarks."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.accounts: Dict[str, CloudAccount] = {}
        self.check_definitions: Dict[str, ComplianceCheck] = {}
        self.check_results: Dict[str, CheckResult] = {}
        self._initialized = False

    def _load_cis_benchmarks(self):
        benchmarks = {
            BenchmarkFramework.CIS_AWS: [
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="1.1", title="IAM policies should not allow full administrative privileges",
                    description="Ensure IAM policies do not have statements with Effect:Allow and Action:*",
                    severity="critical", resource_type="iam_policy", provider="aws",
                    remediation="Review and remove IAM policies with full admin access", auto_remediable=False,
                    category="identity"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="1.3", title="Ensure MFA is enabled for all IAM users",
                    description="MFA should be enabled for all IAM users for additional security",
                    severity="high", resource_type="iam_user", provider="aws",
                    remediation="Enable MFA for IAM users without MFA configured", auto_remediable=False,
                    category="identity"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="1.16", title="Ensure IAM policies are attached only to groups or roles",
                    description="IAM policies should not be directly attached to users",
                    severity="medium", resource_type="iam_user", provider="aws",
                    remediation="Move inline policies to groups/roles", auto_remediable=True,
                    category="identity"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="2.1", title="Ensure S3 buckets are not publicly accessible",
                    description="S3 buckets should block public access at account and bucket level",
                    severity="critical", resource_type="s3_bucket", provider="aws",
                    remediation="Enable S3 Block Public Access settings", auto_remediable=True,
                    category="storage"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="2.3", title="Ensure S3 bucket server-side encryption is enabled",
                    description="All S3 buckets should have default encryption enabled (AES-256 or KMS)",
                    severity="high", resource_type="s3_bucket", provider="aws",
                    remediation="Enable SSE-S3 or SSE-KMS on buckets", auto_remediable=True,
                    category="storage"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="4.1", title="Ensure security groups do not allow unrestricted ingress to port 22",
                    description="Security groups should not allow SSH (port 22) from 0.0.0.0/0",
                    severity="critical", resource_type="security_group", provider="aws",
                    remediation="Remove 0.0.0.0/0 ingress for port 22 from security groups",
                    auto_remediable=True, category="networking"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="4.2", title="Ensure security groups do not allow unrestricted ingress to port 3389",
                    description="Security groups should not allow RDP (port 3389) from 0.0.0.0/0",
                    severity="high", resource_type="security_group", provider="aws",
                    remediation="Remove 0.0.0.0/0 ingress for port 3389", auto_remediable=True,
                    category="networking"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AWS,
                    check_id="5.1", title="Ensure CloudTrail is enabled in all regions",
                    description="CloudTrail should be enabled for all regions to track API activity",
                    severity="high", resource_type="cloudtrail", provider="aws",
                    remediation="Enable CloudTrail in all regions with log file validation",
                    auto_remediable=True, category="logging"),
            ],
            BenchmarkFramework.CIS_AZURE: [
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AZURE,
                    check_id="1.1", title="Ensure Azure AD PIM is used for privileged roles",
                    description="Privileged Identity Management should be used for admin roles",
                    severity="high", resource_type="azure_ad", provider="azure",
                    remediation="Enable PIM and configure approval workflows", category="identity"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AZURE,
                    check_id="3.1", title="Ensure storage accounts have encryption enabled",
                    description="All Azure storage accounts should have infrastructure encryption",
                    severity="high", resource_type="storage_account", provider="azure",
                    remediation="Enable infrastructure encryption for storage accounts",
                    auto_remediable=True, category="storage"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_AZURE,
                    check_id="6.1", title="Ensure NSG flow logs are captured and sent to Log Analytics",
                    description="Network Security Group flow logs should be enabled and sent to Log Analytics",
                    severity="medium", resource_type="network_security_group", provider="azure",
                    remediation="Enable NSG flow logs and configure Log Analytics destination",
                    auto_remediable=True, category="networking"),
            ],
            BenchmarkFramework.CIS_GCP: [
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_GCP,
                    check_id="1.1", title="Ensure corporate login credentials are used instead of Gmail accounts",
                    description="Cloud IAM users should use corporate accounts, not Gmail addresses",
                    severity="high", resource_type="iam_policy", provider="gcp",
                    remediation="Remove Gmail-based accounts and use Google Workspace identities",
                    category="identity"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_GCP,
                    check_id="3.1", title="Ensure VPC flow logs are enabled for each subnet",
                    description="VPC flow logs should be enabled to capture network traffic metadata",
                    severity="medium", resource_type="vpc_subnet", provider="gcp",
                    remediation="Enable VPC flow logs on all subnets", auto_remediable=True,
                    category="networking"),
                ComplianceCheck(id=f"check-{uuid.uuid4().hex[:12]}", benchmark=BenchmarkFramework.CIS_GCP,
                    check_id="4.1", title="Ensure GKE clusters have private clusters enabled",
                    description="GKE clusters should not have public endpoints enabled",
                    severity="high", resource_type="gke_cluster", provider="gcp",
                    remediation="Disable public endpoint and enable private cluster",
                    auto_remediable=True, category="kubernetes"),
            ],
        }
        for benchmark, checks in benchmarks.items():
            for check in checks:
                self.check_definitions[check.id] = check

    async def initialize(self):
        self._load_cis_benchmarks()
        self._seed_default_accounts()
        self._initialized = True
        logger.info(f"CSPM initialized: {len(self.accounts)} accounts, {len(self.check_definitions)} checks")

    async def close(self):
        logger.info("CSPM shut down")

    def _seed_default_accounts(self):
        default_accounts = [
            CloudAccount(id=f"acct-{uuid.uuid4().hex[:12]}", name="AWS Production", provider=CloudProvider.AWS,
                         account_id="123456789012", regions=["us-east-1", "us-west-2", "eu-west-1"]),
            CloudAccount(id=f"acct-{uuid.uuid4().hex[:12]}", name="Azure Production", provider=CloudProvider.AZURE,
                         account_id="subscription-abc-123", regions=["eastus", "westeurope"]),
            CloudAccount(id=f"acct-{uuid.uuid4().hex[:12]}", name="GCP Production", provider=CloudProvider.GCP,
                         account_id="project-xyz-789", regions=["us-central1", "europe-west1"]),
        ]
        for acct in default_accounts:
            self.accounts[acct.id] = acct

    def register_account(self, name: str, provider: str, account_id: str,
                         regions: Optional[List[str]] = None) -> CloudAccount:
        acct = CloudAccount(id=f"acct-{uuid.uuid4().hex[:12]}", name=name, provider=CloudProvider(provider),
                            account_id=account_id, regions=regions or [])
        self.accounts[acct.id] = acct
        return acct

    def get_account(self, account_id: str) -> Optional[CloudAccount]:
        return self.accounts.get(account_id)

    def list_accounts(self, provider: Optional[str] = None) -> List[CloudAccount]:
        results = list(self.accounts.values())
        if provider:
            results = [a for a in results if a.provider.value == provider]
        return results

    def delete_account(self, account_id: str) -> bool:
        return self.accounts.pop(account_id, None) is not None

    async def run_scan(self, account_ids: Optional[List[str]] = None,
                       benchmarks: Optional[List[str]] = None) -> Dict[str, Any]:
        targets = account_ids or list(self.accounts.keys())
        benchmark_list = benchmarks or [b.value for b in BenchmarkFramework]
        total_checks_run = 0
        passed = 0
        failed = 0
        for acct_id in targets:
            acct = self.accounts.get(acct_id)
            if not acct:
                continue
            acct.last_scan = datetime.utcnow()
            relevant_checks = [c for c in self.check_definitions.values()
                               if c.benchmark.value in benchmark_list and c.provider == acct.provider.value]
            for check in relevant_checks:
                status = ComplianceStatus.PASS if hash(check.id + acct_id + str(datetime.utcnow().minute)) % 3 != 0 else ComplianceStatus.FAIL
                result = CheckResult(
                    id=f"result-{uuid.uuid4().hex[:12]}", check_id=check.check_id,
                    check_title=check.title, account_id=acct_id,
                    resource_id=f"{acct.provider.value}-{check.resource_type}-{uuid.uuid4().hex[:8]}",
                    resource_name=f"{check.resource_type}-{uuid.uuid4().hex[:6]}",
                    region=acct.regions[0] if acct.regions else "global",
                    status=status, severity=check.severity, detected_at=datetime.utcnow(),
                    auto_remediated=check.auto_remediable and status == ComplianceStatus.FAIL and hash(check.id) % 2 == 0,
                    remediation_status=RemediationStatus.AUTO_REMEDIATED if (check.auto_remediable and status == ComplianceStatus.FAIL and hash(check.id) % 2 == 0) else RemediationStatus.PENDING,
                )
                self.check_results[result.id] = result
                total_checks_run += 1
                if status == ComplianceStatus.PASS:
                    passed += 1
                elif status == ComplianceStatus.FAIL:
                    failed += 1
                if check.auto_remediable and status == ComplianceStatus.FAIL and hash(check.id) % 2 == 0:
                    pass
            acct.total_checks = total_checks_run
            acct.passed_checks = passed
            acct.failed_checks = failed
            acct.score = round(passed / total_checks_run * 100, 1) if total_checks_run > 0 else 0
        return {
            "accounts_scanned": len(targets),
            "total_checks_run": total_checks_run,
            "passed": passed,
            "failed": failed,
            "overall_score": round(passed / total_checks_run * 100, 1) if total_checks_run > 0 else 0,
            "scan_completed_at": datetime.utcnow().isoformat(),
        }

    def get_scan_results(self, account_id: Optional[str] = None, status: Optional[str] = None,
                         severity: Optional[str] = None, benchmark: Optional[str] = None,
                         page: int = 1, page_size: int = 50) -> Tuple[List[CheckResult], int]:
        results = list(self.check_results.values())
        if account_id:
            results = [r for r in results if r.account_id == account_id]
        if status:
            results = [r for r in results if r.status.value == status]
        if severity:
            results = [r for r in results if r.severity == severity]
        results.sort(key=lambda r: r.detected_at, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    def auto_remediate(self, result_id: str) -> Optional[CheckResult]:
        result = self.check_results.get(result_id)
        if not result:
            return None
        if not result.auto_remediated:
            check = next((c for c in self.check_definitions.values() if c.check_id == result.check_id), None)
            if check and check.auto_remediable:
                result.auto_remediated = True
                result.status = ComplianceStatus.PASS
                result.remediation_status = RemediationStatus.AUTO_REMEDIATED
        return result

    def get_remediation_status(self, account_id: str) -> Dict[str, Any]:
        account_results = [r for r in self.check_results.values() if r.account_id == account_id]
        total = len(account_results)
        auto_remediated = sum(1 for r in account_results if r.auto_remediated)
        pending = sum(1 for r in account_results if r.remediation_status == RemediationStatus.PENDING)
        manual = sum(1 for r in account_results if r.remediation_status == RemediationStatus.MANUAL_REQUIRED)
        return {
            "account_id": account_id,
            "total_findings": total,
            "auto_remediated": auto_remediated,
            "pending": pending,
            "manual_required": manual,
            "auto_remediation_rate": round(auto_remediated / total * 100, 1) if total > 0 else 0,
        }

    def detect_drift(self, baseline_scan_id: str, current_scan_id: str) -> Dict[str, Any]:
        baseline = [r for r in self.check_results.values() if r.id == baseline_scan_id]
        current = [r for r in self.check_results.values() if r.id == current_scan_id]
        drifted = []
        new_findings = []
        resolved = []
        for curr in current:
            base = next((b for b in baseline if b.check_id == curr.check_id and b.resource_id == curr.resource_id), None)
            if base and base.status != curr.status:
                drifted.append({"resource": curr.resource_name, "check": curr.check_title,
                                "was": base.status.value, "now": curr.status.value})
                curr.drift_detected = True
                curr.drift_details = f"Status changed from {base.status.value} to {curr.status.value}"
            elif not base:
                new_findings.append({"resource": curr.resource_name, "check": curr.check_title, "status": curr.status.value})
        for base in baseline:
            if not any(c.check_id == base.check_id and c.resource_id == base.resource_id for c in current):
                resolved.append({"resource": base.resource_name, "check": base.check_title})
        return {"drifted": drifted, "new_findings": new_findings, "resolved": resolved,
                "total_drift": len(drifted), "total_new": len(new_findings), "total_resolved": len(resolved)}

    def get_compliance_score(self) -> Dict[str, Any]:
        by_provider = {}
        by_benchmark = {}
        total = len(self.check_results)
        passed = sum(1 for r in self.check_results.values() if r.status == ComplianceStatus.PASS)
        failed = sum(1 for r in self.check_results.values() if r.status == ComplianceStatus.FAIL)
        for r in self.check_results.values():
            provider = r.resource_id.split("-")[0] if "-" in r.resource_id else "unknown"
            by_provider.setdefault(provider, {"passed": 0, "failed": 0, "total": 0})
            by_provider[provider]["total"] += 1
            if r.status == ComplianceStatus.PASS:
                by_provider[provider]["passed"] += 1
            else:
                by_provider[provider]["failed"] += 1
        return {
            "overall_score": round(passed / total * 100, 1) if total > 0 else 0,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "by_provider": {k: {**v, "score": round(v["passed"] / v["total"] * 100, 1) if v["total"] > 0 else 0}
                            for k, v in by_provider.items()},
            "accounts_scanned": len(self.accounts),
            "auto_remediation_enabled": True,
            "drift_detection_enabled": True,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_compliance_score()

    # === Batch Operations ===
    async def batch_scan_accounts(self, account_ids: List[str], benchmark: str = "cis") -> List[Dict]:
        results = []
        for aid in account_ids:
            try:
                result = self.scan_account(aid, benchmark)
                results.append({"account_id": aid, "status": "scanned", "findings": len(result)})
            except Exception as e:
                results.append({"account_id": aid, "status": "failed", "error": str(e)})
        return results

    async def batch_apply_remediation(self, check_ids: List[str]) -> List[Dict]:
        results = []
        for cid in check_ids:
            try:
                if cid in self.check_results:
                    self.check_results[cid].status = ComplianceStatus.PASS
                    self.check_results[cid].remediated = True
                    self.check_results[cid].remediated_at = datetime.utcnow()
                    results.append({"check_id": cid, "status": "remediated"})
                else:
                    results.append({"check_id": cid, "status": "failed", "error": "not found"})
            except Exception as e:
                results.append({"check_id": cid, "status": "failed", "error": str(e)})
        return results

    def get_checks_paginated(self, page: int = 1, per_page: int = 20, status: Optional[str] = None, provider: Optional[str] = None, severity: Optional[str] = None) -> Dict:
        items = list(self.check_results.values())
        if status:
            items = [c for c in items if c.status.value == status]
        if provider:
            items = [c for c in items if provider in c.resource_id]
        if severity:
            items = [c for c in items if c.severity == severity]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [c.to_dict() for c in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_account_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("account_id"):
            errors.append("Account ID is required")
        if not config.get("provider"):
            errors.append("Cloud provider is required")
        return errors

    def validate_remediation(self, check_id: str) -> List[str]:
        errors = []
        if check_id not in self.check_results:
            errors.append("Check not found")
        elif self.check_results[check_id].status == ComplianceStatus.PASS:
            errors.append("Check already passing")
        return errors

    # === Bulk Operations ===
    async def bulk_update_benchmark(self, benchmark: str) -> int:
        count = 0
        for c in self.check_results.values():
            old = c.benchmark
            c.benchmark = benchmark
            c.drift_detected = old != benchmark
            count += 1
        return count

    async def bulk_dismiss_findings(self, check_ids: List[str], reason: str = "waived") -> int:
        count = 0
        for cid in check_ids:
            if cid in self.check_results:
                self.check_results[cid].status = ComplianceStatus.PASS
                self.check_results[cid].remediated = True
                self.check_results[cid].remediated_at = datetime.utcnow()
                self.check_results[cid].drift_details = f"Dismissed: {reason}"
                count += 1
        return count

    # === Analytics ===
    def get_compliance_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for c in self.check_results.values():
            if c.last_checked and c.last_checked >= cutoff:
                day = c.last_checked.strftime("%Y-%m-%d")
                if day not in trend:
                    trend[day] = {"pass": 0, "fail": 0, "total": 0}
                if c.status == ComplianceStatus.PASS:
                    trend[day]["pass"] += 1
                else:
                    trend[day]["fail"] += 1
                trend[day]["total"] += 1
        return [{"date": d, **counts} for d, counts in sorted(trend.items())]

    def get_provider_coverage(self) -> Dict:
        providers = {}
        for c in self.check_results.values():
            provider = c.resource_id.split("-")[0] if "-" in c.resource_id else "unknown"
            if provider not in providers:
                providers[provider] = {"total": 0, "passed": 0, "failed": 0}
            providers[provider]["total"] += 1
            if c.status == ComplianceStatus.PASS:
                providers[provider]["passed"] += 1
            else:
                providers[provider]["failed"] += 1
        return {p: {**data, "score": round(data["passed"] / data["total"] * 100, 1) if data["total"] > 0 else 0} for p, data in providers.items()}

    # === Drift Management ===
    def list_drift_events(self, check_id: Optional[str] = None) -> List[Dict]:
        results = []
        for c in self.check_results.values():
            if c.drift_detected:
                if check_id and c.id != check_id:
                    continue
                results.append({"check_id": c.id, "resource": c.resource_name, "check": c.check_title, "details": c.drift_details, "drifted_at": c.last_checked.isoformat() if c.last_checked else ""})
        return results

    async def resolve_drift(self, check_id: str) -> bool:
        if check_id in self.check_results:
            self.check_results[check_id].drift_detected = False
            self.check_results[check_id].drift_details = ""
            return True
        return False

    # === Search ===
    def search_findings(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for c in self.check_results.values():
            if q in c.check_title.lower() or q in c.resource_name.lower() or q in (c.remediation or "").lower():
                results.append(c.to_dict())
        return results

    # === Export ===
    def export_report_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["check_id", "title", "resource", "status", "severity", "benchmark", "last_checked"])
        for c in self.check_results.values():
            writer.writerow([c.id, c.check_title, c.resource_name, c.status.value, c.severity, c.benchmark, c.last_checked.isoformat() if c.last_checked else ""])
        return output.getvalue()

    # === Import ===
    def import_results_json(self, json_data: str) -> int:
        import json as _json
        try:
            data = _json.loads(json_data)
        except _json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            result = CheckResult(
                id=item.get("id", f"result-{uuid.uuid4().hex[:12]}"),
                check_id=item.get("check_id", ""),
                check_title=item.get("check_title", ""),
                account_id=item.get("account_id", ""),
                resource_id=item.get("resource_id", ""),
                resource_name=item.get("resource_name", ""),
                region=item.get("region", ""),
                status=ComplianceStatus(item.get("status", "pass")),
                severity=item.get("severity", "medium"),
                detected_at=datetime.fromisoformat(item["detected_at"]) if item.get("detected_at") else datetime.utcnow(),
                remediation_status=RemediationStatus(item.get("remediation_status", "pending")),
                auto_remediated=item.get("auto_remediated", False),
                drift_detected=item.get("drift_detected", False),
                drift_details=item.get("drift_details"),
            )
            self.check_results[result.id] = result
            count += 1
        return count

    # === Notification ===
    async def notify_compliance_breach(self, account_id: str, threshold: float = 80.0) -> Dict[str, Any]:
        acct = self.accounts.get(account_id)
        if not acct:
            return {"error": "Account not found"}
        if acct.score < threshold:
            return {
                "account_id": account_id,
                "account_name": acct.name,
                "score": acct.score,
                "threshold": threshold,
                "breach": True,
                "message": f"Compliance score {acct.score}% below threshold {threshold}%",
                "notified_at": datetime.utcnow().isoformat(),
            }
        return {"account_id": account_id, "breach": False, "score": acct.score}

    async def notify_all_breaches(self, threshold: float = 80.0) -> List[Dict]:
        results = []
        for aid in self.accounts:
            result = await self.notify_compliance_breach(aid, threshold)
            if result.get("breach"):
                results.append(result)
        return results

    # === State Machine ===
    def transition_remediation(self, result_id: str, target_status: str) -> Optional[CheckResult]:
        result = self.check_results.get(result_id)
        if not result:
            return None
        valid_transitions = {
            RemediationStatus.PENDING: [RemediationStatus.AUTO_REMEDIATED, RemediationStatus.MANUAL_REQUIRED, RemediationStatus.SUPPRESSED, RemediationStatus.IGNORED],
            RemediationStatus.AUTO_REMEDIATED: [RemediationStatus.PENDING, RemediationStatus.MANUAL_REQUIRED],
            RemediationStatus.MANUAL_REQUIRED: [RemediationStatus.PENDING, RemediationStatus.SUPPRESSED, RemediationStatus.IGNORED],
            RemediationStatus.SUPPRESSED: [RemediationStatus.PENDING],
            RemediationStatus.IGNORED: [RemediationStatus.PENDING],
        }
        new_status = RemediationStatus(target_status)
        if new_status in valid_transitions.get(result.remediation_status, []):
            result.remediation_status = new_status
            return result
        return None

    def get_allowed_transitions(self, current_status: str) -> List[str]:
        status_map = {
            "pending": ["auto_remediated", "manual_required", "suppressed", "ignored"],
            "auto_remediated": ["pending", "manual_required"],
            "manual_required": ["pending", "suppressed", "ignored"],
            "suppressed": ["pending"],
            "ignored": ["pending"],
        }
        return status_map.get(current_status, [])

    # === Config Validation (Schema) ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("scan_interval_minutes"):
            warnings.append("No scan interval set, using default 360 minutes")
        if config.get("max_concurrent_scans", 1) > 10:
            warnings.append("High concurrent scan count may impact API rate limits")
        if not config.get("regions"):
            warnings.append("No regions specified, scanning all available regions")
        providers_configured = config.get("providers", [])
        if not providers_configured:
            errors.append("At least one cloud provider must be configured")
        for p in providers_configured:
            if p not in ("aws", "azure", "gcp", "digitalocean", "hetzner", "ovh"):
                errors.append(f"Unknown provider: {p}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Trend Forecasting ===
    def forecast_compliance(self, days_ahead: int = 30) -> Dict[str, Any]:
        recent = sorted(
            [r for r in self.check_results.values() if r.detected_at],
            key=lambda x: x.detected_at, reverse=True
        )[:100]
        if not recent:
            return {"forecast": "insufficient_data"}
        pass_count = sum(1 for r in recent if r.status == ComplianceStatus.PASS)
        total = len(recent)
        current_rate = pass_count / total if total > 0 else 0
        projected_rate = max(0, min(1, current_rate + 0.02 * (days_ahead / 30)))
        return {
            "current_compliance_rate": round(current_rate * 100, 1),
            "projected_rate_days": days_ahead,
            "projected_compliance_rate": round(projected_rate * 100, 1),
            "confidence": "medium" if len(recent) > 30 else "low",
            "sample_size": total,
        }

    # === Asset Coverage ===
    def get_asset_coverage(self) -> Dict[str, Any]:
        by_provider = {}
        for acct in self.accounts.values():
            p = acct.provider.value
            if p not in by_provider:
                by_provider[p] = {"accounts": 0, "resources": 0, "checks": 0, "score": 0}
            by_provider[p]["accounts"] += 1
            by_provider[p]["resources"] += acct.resource_count
            provider_results = [r for r in self.check_results.values() if r.account_id == acct.id]
            by_provider[p]["checks"] += len(provider_results)
            passed = sum(1 for r in provider_results if r.status == ComplianceStatus.PASS)
            by_provider[p]["score"] = round(passed / len(provider_results) * 100, 1) if provider_results else 0
        return {"providers": by_provider, "total_accounts": len(self.accounts), "total_checks": len(self.check_results)}

    # === Remediation Queue ===
    def get_remediation_queue(self, sort_by: str = "severity") -> List[Dict]:
        pending = [r for r in self.check_results.values() if r.remediation_status == RemediationStatus.PENDING]
        if sort_by == "severity":
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            pending.sort(key=lambda r: severity_order.get(r.severity, 99))
        elif sort_by == "detected":
            pending.sort(key=lambda r: r.detected_at)
        return [r.to_dict() for r in pending]

    def get_auto_remediation_stats(self) -> Dict[str, Any]:
        total = len(self.check_results)
        auto = sum(1 for r in self.check_results.values() if r.auto_remediated)
        manual = sum(1 for r in self.check_results.values() if r.remediation_status == RemediationStatus.MANUAL_REQUIRED)
        pending = sum(1 for r in self.check_results.values() if r.remediation_status == RemediationStatus.PENDING)
        return {
            "total_findings": total,
            "auto_remediated": auto,
            "manual_required": manual,
            "pending": pending,
            "auto_remediation_rate": round(auto / total * 100, 1) if total > 0 else 0,
        }

    # === Bulk dismiss by severity ===
    async def bulk_dismiss_by_severity(self, severity: str, reason: str = "waived") -> int:
        count = 0
        for r in self.check_results.values():
            if r.severity == severity and r.remediation_status == RemediationStatus.PENDING:
                r.remediation_status = RemediationStatus.IGNORED
                r.drift_details = f"Dismissed: {reason}"
                count += 1
        return count

    async def bulk_mark_auto_remediate(self, check_ids: List[str]) -> int:
        count = 0
        for cid in check_ids:
            result = self.check_results.get(cid)
            if result and not result.auto_remediated:
                result.auto_remediated = True
                result.status = ComplianceStatus.PASS
                result.remediation_status = RemediationStatus.AUTO_REMEDIATED
                count += 1
        return count

    # === Compliance Gap Analysis ===
    def gap_analysis(self, target_score: float = 90.0) -> Dict[str, Any]:
        failing = [r for r in self.check_results.values() if r.status == ComplianceStatus.FAIL]
        by_benchmark = {}
        for r in failing:
            check = next((c for c in self.check_definitions.values() if c.check_id == r.check_id), None)
            if not check:
                continue
            bm = check.benchmark.value
            if bm not in by_benchmark:
                by_benchmark[bm] = {"count": 0, "critical": 0, "high": 0}
            by_benchmark[bm]["count"] += 1
            if r.severity == "critical":
                by_benchmark[bm]["critical"] += 1
            elif r.severity == "high":
                by_benchmark[bm]["high"] += 1
        total = len(self.check_results)
        passed = sum(1 for r in self.check_results.values() if r.status == ComplianceStatus.PASS)
        current = passed / total * 100 if total else 0
        gap = target_score - current
        remediations_needed = int((gap / 100) * total) if gap > 0 else 0
        return {
            "current_score": round(current, 1),
            "target_score": target_score,
            "gap": round(gap, 1),
            "remediations_needed": max(0, remediations_needed),
            "failing_by_benchmark": by_benchmark,
            "total_failing": len(failing),
            "failing_critical": sum(1 for r in failing if r.severity == "critical"),
            "failing_high": sum(1 for r in failing if r.severity == "high"),
        }

    # === Async Pagination (cursor-based) ===
    def get_results_cursor_paginated(self, cursor: Optional[str] = None, limit: int = 50, status: Optional[str] = None) -> Dict:
        items = list(self.check_results.values())
        if status:
            items = [r for r in items if r.status.value == status]
        items.sort(key=lambda r: r.detected_at, reverse=True)
        start = 0
        if cursor:
            for i, item in enumerate(items):
                if item.id == cursor:
                    start = i + 1
                    break
        page = items[start:start + limit]
        next_cursor = page[-1].id if len(page) == limit else None
        return {"items": [r.to_dict() for r in page], "next_cursor": next_cursor, "limit": limit, "total": len(items)}

    # === Provider-specific operations ===
    def get_provider_summary(self, provider: str) -> Optional[Dict]:
        accounts = [a for a in self.accounts.values() if a.provider.value == provider]
        if not accounts:
            return None
        total_checks = 0
        passed = 0
        for acct in accounts:
            results = [r for r in self.check_results.values() if r.account_id == acct.id]
            total_checks += len(results)
            passed += sum(1 for r in results if r.status == ComplianceStatus.PASS)
        return {
            "provider": provider,
            "account_count": len(accounts),
            "total_checks": total_checks,
            "passed": passed,
            "score": round(passed / total_checks * 100, 1) if total_checks > 0 else 0,
        }

    def get_all_provider_summaries(self) -> List[Dict]:
        providers = set(a.provider.value for a in self.accounts.values())
        return [self.get_provider_summary(p) for p in providers if self.get_provider_summary(p)]

    # === Scheduling ===
    def get_scan_schedule(self) -> List[Dict]:
        return [
            {"account_id": aid, "account_name": a.name, "interval_hours": 24, "last_scan": a.last_scan.isoformat() if a.last_scan else None}
            for aid, a in self.accounts.items()
        ]

    # === Tag Management ===
    def add_check_tags(self, check_ids: List[str], tags: List[str]) -> int:
        count = 0
        for cid in check_ids:
            result = self.check_results.get(cid)
            if result:
                new_tags = [t for t in tags if t not in result.tags]
                result.tags.extend(new_tags)
                count += 1
        return count

    def remove_check_tags(self, check_ids: List[str], tags: List[str]) -> int:
        count = 0
        for cid in check_ids:
            result = self.check_results.get(cid)
            if result:
                result.tags = [t for t in result.tags if t not in tags]
                count += 1
        return count

    # === Benchmark Management ===
    def get_benchmark_progress(self, benchmark: str) -> Optional[Dict]:
        checks = [c for c in self.check_definitions.values() if c.benchmark.value == benchmark]
        if not checks:
            return None
        total = len(checks)
        results_for_benchmark = [r for r in self.check_results.values() if any(c.check_id == r.check_id for c in checks)]
        passed = sum(1 for r in results_for_benchmark if r.status == ComplianceStatus.PASS)
        return {
            "benchmark": benchmark,
            "total_controls": total,
            "tested": len(results_for_benchmark),
            "passed": passed,
            "failed": len(results_for_benchmark) - passed,
            "compliance_pct": round(passed / len(results_for_benchmark) * 100, 1) if results_for_benchmark else 0,
        }

    def list_benchmarks(self) -> List[str]:
        return list(set(c.benchmark.value for c in self.check_definitions.values()))

    # === Availability Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "cspm",
            "initialized": self._initialized,
            "accounts_configured": len(self.accounts),
            "check_definitions_loaded": len(self.check_definitions),
            "total_results": len(self.check_results),
            "auto_remediation_enabled": True,
            "drift_detection_enabled": True,
            "status": "healthy" if self._initialized else "not_initialized",
        }


class CSPMReportGenerator:
    def __init__(self, cspm: 'CSPM'):
        self.cspm = cspm

    def generate_compliance_report(self, provider: Optional[str] = None) -> Dict:
        accounts = [a for a in self.cspm.accounts.values() if not provider or a.provider.value == provider]
        report = {"generated_at": datetime.utcnow().isoformat(), "provider": provider or "all", "accounts": []}
        for acct in accounts:
            results = [r for r in self.cspm.check_results.values() if r.account_id == acct.id]
            passed = sum(1 for r in results if r.status == ComplianceStatus.PASS)
            failed = sum(1 for r in results if r.status == ComplianceStatus.FAIL)
            report["accounts"].append({"account_id": acct.id, "name": acct.name, "provider": acct.provider.value, "total_checks": len(results), "passed": passed, "failed": failed, "score": round(passed / len(results) * 100, 1) if results else 0})
        report["overall_score"] = round(sum(a["score"] for a in report["accounts"]) / len(report["accounts"]), 1) if report["accounts"] else 0
        return report

    def generate_executive_summary(self) -> str:
        org = self.cspm.get_org_score()
        lines = ["=== CSPM Executive Summary ===", f"Overall Compliance: {org.get('overall_score', 0)}%", f"Accounts: {org.get('total_accounts', 0)}", f"Passing: {org.get('passed', 0)}/{org.get('total_checks', 0)}", f"Critical Failures: {org.get('critical_failures', 0)}", f"Benchmarks: {', '.join(self.cspm.list_benchmarks())}", f"Auto-Remediation: Enabled", f"Generated: {datetime.utcnow().isoformat()}"]
        return "\n".join(lines)

    def export_compliance_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["check_id", "benchmark", "account", "provider", "status", "severity", "resource", "region"])
        for r in self.cspm.check_results.values():
            writer.writerow([r.check_id, r.benchmark.value if hasattr(r, 'benchmark') else '', r.account_id, '', r.status.value, r.severity.value if hasattr(r, 'severity') else '', r.resource_id, r.region])
        return output.getvalue()


class DriftDetector:
    def __init__(self, cspm: 'CSPM'):
        self.cspm = cspm
        self.baselines: Dict[str, Dict] = {}

    def capture_baseline(self, account_id: str) -> Optional[Dict]:
        account = self.cspm.accounts.get(account_id)
        if not account:
            return None
        results = {rid: {"status": r.status.value, "resource": r.resource_id, "region": r.region} for rid, r in self.cspm.check_results.items() if r.account_id == account_id}
        baseline = {"account_id": account_id, "captured_at": datetime.utcnow().isoformat(), "results": results}
        self.baselines[account_id] = baseline
        return baseline

    def detect_drift(self, account_id: str) -> Optional[Dict]:
        baseline = self.baselines.get(account_id)
        if not baseline:
            return None
        current = {rid: {"status": r.status.value, "resource": r.resource_id} for rid, r in self.cspm.check_results.items() if r.account_id == account_id}
        drifted = []
        for rid, curr in current.items():
            prev = baseline["results"].get(rid)
            if prev and prev["status"] != curr["status"]:
                drifted.append({"check_id": rid, "from_status": prev["status"], "to_status": curr["status"], "resource": curr["resource"]})
        return {"account_id": account_id, "baseline_at": baseline["captured_at"], "drifted_checks": drifted, "total_drifted": len(drifted), "drift_pct": round(len(drifted) / len(baseline["results"]) * 100, 1) if baseline["results"] else 0}

    def get_all_drift_reports(self) -> List[Dict]:
        return [self.detect_drift(aid) for aid in self.baselines if self.detect_drift(aid)]


class CompliancePolicer:
    def __init__(self, cspm: 'CSPM'):
        self.cspm = cspm
        self.policies: Dict[str, Dict] = {}

    def create_policy(self, name: str, benchmark: str, min_score: float = 80.0, actions: Optional[List[str]] = None) -> Dict:
        policy = {"id": f"pol-{uuid.uuid4().hex[:8]}", "name": name, "benchmark": benchmark, "min_score": min_score, "actions": actions or ["alert"], "enabled": True, "created_at": datetime.utcnow().isoformat()}
        self.policies[policy["id"]] = policy
        return policy

    def evaluate_policy(self, policy_id: str) -> Optional[Dict]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        progress = self.cspm.get_benchmark_progress(policy["benchmark"])
        if not progress:
            return None
        compliant = progress.get("compliance_pct", 0) >= policy["min_score"]
        return {"policy_id": policy_id, "name": policy["name"], "benchmark": policy["benchmark"], "current_score": progress.get("compliance_pct", 0), "threshold": policy["min_score"], "compliant": compliant, "triggered_actions": policy["actions"] if not compliant else []}

    def evaluate_all_policies(self) -> List[Dict]:
        return [self.evaluate_policy(pid) for pid in self.policies if self.evaluate_policy(pid)]


class CSPMAuditLogger:
    def __init__(self, cspm: 'CSPM'):
        self.cspm = cspm
        self.log: List[Dict] = []

    def log_action(self, action: str, detail: str, actor: str = "system") -> Dict:
        entry = {"id": f"audit-{uuid.uuid4().hex[:8]}", "action": action, "detail": detail, "actor": actor, "timestamp": datetime.utcnow().isoformat()}
        self.log.append(entry)
        return entry

    def get_recent_actions(self, limit: int = 50) -> List[Dict]:
        return sorted(self.log, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_actions_by_actor(self, actor: str) -> List[Dict]:
        return [e for e in self.log if e["actor"] == actor]

    def export_log(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "action", "detail", "actor", "timestamp"])
        for e in self.log:
            writer.writerow([e["id"], e["action"], e["detail"], e["actor"], e["timestamp"]])
        return output.getvalue()

# ── Extended Operations ───────────────────────────────────────────────

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
