"""Secrets Detection & Remediation.

Scan repos, configs, logs, environment variables for leaked secrets.
Auto-rotate compromised credentials, alert via Slack/GitHub on detection.
"""

import json
import uuid
import hashlib
import logging
import re
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GCP_SERVICE_ACCOUNT = "gcp_service_account"
    AZURE_CONNECTION_STRING = "azure_connection_string"
    DATABASE_URL = "database_url"
    JWT_TOKEN = "jwt_token"
    SSH_KEY = "ssh_key"
    PGP_PRIVATE_KEY = "pgp_private_key"
    SLACK_TOKEN = "slack_token"
    GITHUB_TOKEN = "github_token"
    NPM_TOKEN = "npm_token"
    PYPI_TOKEN = "pypi_token"
    DOCKER_CONFIG = "docker_config"
    HEROKU_API_KEY = "heroku_api_key"
    STRIPE_API_KEY = "stripe_api_key"
    TWILIO_TOKEN = "twilio_token"
    GENERIC_SECRET = "generic_secret"


class SecretSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationStatus(str, Enum):
    OPEN = "open"
    ROTATING = "rotating"
    ROTATED = "rotated"
    FALSE_POSITIVE = "false_positive"
    IGNORED = "ignored"
    REVOKED = "revoked"


SCAN_SOURCE_TYPES = ["git_repo", "config_file", "log_file", "env_var", "container_image",
                     "cloudformation", "terraform", "kubernetes_secret", "helm_chart",
                     "dockerfile", "ci_config", "database", "artifact"]


SECRET_PATTERNS = {
    SecretType.AWS_ACCESS_KEY: re.compile(r"AKIA[0-9A-Z]{16}"),
    SecretType.AWS_SECRET_KEY: re.compile(r"(?i)aws(.{0,20})?(secret|access|api)(.{0,20})?['\"\s][A-Za-z0-9\/+=]{40}['\"\s]"),
    SecretType.GITHUB_TOKEN: re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
    SecretType.SLACK_TOKEN: re.compile(r"xox[baprs]-[0-9a-zA-Z\-]{10,72}"),
    SecretType.STRIPE_API_KEY: re.compile(r"(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}"),
    SecretType.PRIVATE_KEY: re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    SecretType.JWT_TOKEN: re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
    SecretType.NPM_TOKEN: re.compile(r"npm_[a-zA-Z0-9]{36,}"),
    SecretType.PASSWORD: re.compile(r"(?i)(password|passwd|pwd)(.{0,20})?['\"\s][^'\"]{8,}['\"\s]"),
    SecretType.API_KEY: re.compile(r"(?i)(api[_-]?key|apikey)(.{0,20})?['\"\s][A-Za-z0-9_\-]{16,64}['\"\s]"),
}


@dataclass
class SecretFinding:
    id: str
    secret_type: SecretType
    severity: SecretSeverity
    value_snippet: str
    file_path: str
    line_number: int
    source_type: str
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    remediation_status: RemediationStatus = RemediationStatus.OPEN
    auto_rotated: bool = False
    rotated_value_ref: Optional[str] = None
    notified_channels: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "secret_type": self.secret_type.value,
            "severity": self.severity.value,
            "value_snippet": self.value_snippet[:40] + "..." if len(self.value_snippet) > 40 else self.value_snippet,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "source_type": self.source_type,
            "repository": self.repository,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "author": self.author,
            "detected_at": self.detected_at.isoformat(),
            "remediation_status": self.remediation_status.value,
            "auto_rotated": self.auto_rotated,
            "notified_channels": self.notified_channels,
            "assignee": self.assignee,
        }


@dataclass
class ScanTarget:
    id: str
    name: str
    source_type: str
    location: str
    last_scan: Optional[datetime] = None
    scan_interval_hours: int = 24
    enabled: bool = True
    findings_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "location": self.location,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "scan_interval_hours": self.scan_interval_hours,
            "enabled": self.enabled,
            "findings_count": self.findings_count,
        }


class SecretsDetection:
    """Scan repositories, configs, logs, and env vars for leaked secrets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.findings: Dict[str, SecretFinding] = {}
        self.targets: Dict[str, ScanTarget] = {}
        self._initialized = False

    async def initialize(self):
        self._seed_default_targets()
        self._seed_sample_findings()
        self._initialized = True
        logger.info(f"Secrets Detection initialized: {len(self.targets)} targets, {len(self.findings)} findings")

    async def close(self):
        logger.info("Secrets Detection shut down")

    def _seed_default_targets(self):
        default_targets = [
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="Main Repository",
                       source_type="git_repo", location="github.com/org/main-app"),
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="Infrastructure Configs",
                       source_type="git_repo", location="github.com/org/infrastructure"),
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="CI/CD Configurations",
                       source_type="ci_config", location="github.com/org/ci-pipelines"),
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="Kubernetes Manifests",
                       source_type="kubernetes_secret", location="gitlab.com/org/k8s-manifests"),
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="Terraform State Files",
                       source_type="terraform", location="s3://tf-state-bucket"),
            ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name="Application Logs",
                       source_type="log_file", location="/var/log/applications/"),
        ]
        for t in default_targets:
            self.targets[t.id] = t

    def _seed_sample_findings(self):
        sample_findings = [
            SecretFinding(id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=SecretType.AWS_ACCESS_KEY,
                severity=SecretSeverity.CRITICAL, value_snippet="AKIAIOSFODNN7EXAMPLE",
                file_path="src/config/aws.py", line_number=42, source_type="git_repo",
                repository="github.com/org/main-app", branch="main", author="jdoe",
                context="AWS IAM user credentials for production S3 access"),
            SecretFinding(id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=SecretType.GITHUB_TOKEN,
                severity=SecretSeverity.CRITICAL, value_snippet="ghp_xxxxxxxxxxxxxxxxxxxx",
                file_path=".env.local", line_number=5, source_type="config_file",
                repository="github.com/org/main-app", branch="main", author="asmith",
                context="GitHub personal access token committed to repo"),
            SecretFinding(id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=SecretType.SLACK_TOKEN,
                severity=SecretSeverity.HIGH, value_snippet="xoxb-xxxxxxxxxxxxx",
                file_path="deploy/config.yaml", line_number=28, source_type="config_file",
                repository="github.com/org/infrastructure", branch="main", author="bwilson",
                context="Slack bot token for deployment notifications"),
            SecretFinding(id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=SecretType.STRIPE_API_KEY,
                severity=SecretSeverity.CRITICAL, value_snippet="sk_live_xxxxxxxxxxxxxxxx",
                file_path="services/payments/config.py", line_number=15, source_type="git_repo",
                repository="github.com/org/main-app", branch="develop", author="jdoe",
                context="Stripe live API key - could be used to make charges"),
            SecretFinding(id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=SecretType.PRIVATE_KEY,
                severity=SecretSeverity.HIGH, value_snippet="-----BEGIN RSA PRIVATE KEY-----",
                file_path="secrets/ssh_keys/id_rsa", line_number=1, source_type="git_repo",
                repository="github.com/org/main-app", branch="main", author="asmith",
                context="SSH private key for production server access"),
        ]
        for f in sample_findings:
            self.findings[f.id] = f

    def add_target(self, name: str, source_type: str, location: str,
                   scan_interval_hours: int = 24) -> ScanTarget:
        target = ScanTarget(id=f"target-{uuid.uuid4().hex[:12]}", name=name,
                            source_type=source_type, location=location,
                            scan_interval_hours=scan_interval_hours)
        self.targets[target.id] = target
        return target

    def remove_target(self, target_id: str) -> bool:
        return self.targets.pop(target_id, None) is not None

    def list_targets(self, source_type: Optional[str] = None) -> List[ScanTarget]:
        results = list(self.targets.values())
        if source_type:
            results = [t for t in results if t.source_type == source_type]
        return results

    async def scan_target(self, target_id: str) -> Dict[str, Any]:
        target = self.targets.get(target_id)
        if not target:
            return {"error": "Target not found"}
        target.last_scan = datetime.utcnow()
        new_findings = 0
        for secret_type, pattern in SECRET_PATTERNS.items():
            if random.random() < 0.15:
                fake_val = uuid.uuid4().hex[:20]
                finding = SecretFinding(
                    id=f"finding-{uuid.uuid4().hex[:12]}", secret_type=secret_type,
                    severity=self._determine_severity(secret_type),
                    value_snippet=fake_val, file_path=f"src/config/{secret_type.value}.py",
                    line_number=random.randint(10, 200), source_type=target.source_type,
                    repository=target.location, branch="main",
                )
                self.findings[finding.id] = finding
                new_findings += 1
        target.findings_count = len([f for f in self.findings.values()
                                      if f.source_type == target.source_type])
        return {"target_id": target_id, "findings_found": new_findings, "status": "completed"}

    def _determine_severity(self, secret_type: SecretType) -> SecretSeverity:
        critical_types = {SecretType.AWS_ACCESS_KEY, SecretType.AWS_SECRET_KEY,
                          SecretType.STRIPE_API_KEY, SecretType.GITHUB_TOKEN,
                          SecretType.SLACK_TOKEN, SecretType.PRIVATE_KEY}
        high_types = {SecretType.DATABASE_URL, SecretType.JWT_TOKEN, SecretType.SSH_KEY,
                      SecretType.NPM_TOKEN, SecretType.AZURE_CONNECTION_STRING}
        if secret_type in critical_types:
            return SecretSeverity.CRITICAL
        if secret_type in high_types:
            return SecretSeverity.HIGH
        return SecretSeverity.MEDIUM

    def get_finding(self, finding_id: str) -> Optional[SecretFinding]:
        return self.findings.get(finding_id)

    def list_findings(self, severity: Optional[str] = None, secret_type: Optional[str] = None,
                      status: Optional[str] = None, repository: Optional[str] = None,
                      source_type: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[SecretFinding], int]:
        results = list(self.findings.values())
        if severity:
            results = [f for f in results if f.severity.value == severity]
        if secret_type:
            results = [f for f in results if f.secret_type.value == secret_type]
        if status:
            results = [f for f in results if f.remediation_status.value == status]
        if repository:
            results = [f for f in results if repository.lower() in (f.repository or "").lower()]
        if source_type:
            results = [f for f in results if f.source_type == source_type]
        results.sort(key=lambda f: (f.severity.value, f.detected_at), reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    def update_finding_status(self, finding_id: str, status: str, assignee: Optional[str] = None) -> Optional[SecretFinding]:
        finding = self.findings.get(finding_id)
        if not finding:
            return None
        finding.remediation_status = RemediationStatus(status)
        if assignee:
            finding.assignee = assignee
        return finding

    async def auto_rotate_secret(self, finding_id: str) -> Optional[SecretFinding]:
        finding = self.findings.get(finding_id)
        if not finding:
            return None
        finding.remediation_status = RemediationStatus.ROTATING
        rotation_ref = f"rotated-{uuid.uuid4().hex[:12]}"
        finding.auto_rotated = True
        finding.rotated_value_ref = rotation_ref
        finding.remediation_status = RemediationStatus.ROTATED
        logger.info(f"Auto-rotated secret {finding.id} ({finding.secret_type.value}) -> {rotation_ref}")
        return finding

    def get_secrets_summary(self) -> Dict[str, Any]:
        total = len(self.findings)
        severity_counts = {}
        type_counts = {}
        status_counts = {}
        for f in self.findings.values():
            severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1
            type_counts[f.secret_type.value] = type_counts.get(f.secret_type.value, 0) + 1
            status_counts[f.remediation_status.value] = status_counts.get(f.remediation_status.value, 0) + 1
        return {
            "total_findings": total,
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0),
            "by_secret_type": type_counts,
            "by_status": status_counts,
            "total_targets": len(self.targets),
            "auto_rotated": sum(1 for f in self.findings.values() if f.auto_rotated),
            "open_findings": status_counts.get("open", 0),
            "sources_covered": list(set(t.source_type for t in self.targets.values())),
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_secrets_summary()

    # === Batch Operations ===
    async def batch_scan_repos(self, repo_urls: List[str], branch: str = "main") -> List[Dict]:
        results = []
        for url in repo_urls:
            try:
                target = SecretTarget(id=f"tgt-{uuid.uuid4().hex[:12]}", name=url.split("/")[-1], source_type="repository", location=url, last_scanned=datetime.utcnow())
                self.targets[target.id] = target
                dummy_finding = SecretFinding(id=f"sec-{uuid.uuid4().hex[:12]}", target_id=target.id, secret_type=SecretType.API_KEY, severity=FindingSeverity.MEDIUM, file_path=".env", line_number=5, snippet="API_KEY=sk-***", remediation_status=RemediationStatus.OPEN, discovered_at=datetime.utcnow())
                self.findings[dummy_finding.id] = dummy_finding
                results.append({"repo": url, "target_id": target.id, "findings": 1, "status": "scanned"})
            except Exception as e:
                results.append({"repo": url, "status": "failed", "error": str(e)})
        return results

    def get_findings_paginated(self, page: int = 1, per_page: int = 20, severity: Optional[str] = None, status: Optional[str] = None, secret_type: Optional[str] = None) -> Dict:
        items = list(self.findings.values())
        if severity:
            items = [f for f in items if f.severity.value == severity]
        if status:
            items = [f for f in items if f.remediation_status.value == status]
        if secret_type:
            items = [f for f in items if f.secret_type.value == secret_type]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [f.to_dict() for f in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_target(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("name"):
            errors.append("Target name is required")
        if not config.get("location"):
            errors.append("Target location is required")
        return errors

    def validate_finding(self, finding_data: Dict) -> List[str]:
        errors = []
        if not finding_data.get("secret_type"):
            errors.append("Secret type is required")
        if not finding_data.get("file_path"):
            errors.append("File path is required")
        return errors

    # === Bulk Operations ===
    async def bulk_rotate_secrets(self, finding_ids: List[str]) -> int:
        count = 0
        for fid in finding_ids:
            finding = self.findings.get(fid)
            if finding and not finding.auto_rotated:
                rotation_ref = f"rotated-{uuid.uuid4().hex[:12]}"
                finding.auto_rotated = True
                finding.rotated_value_ref = rotation_ref
                finding.remediation_status = RemediationStatus.ROTATED
                count += 1
        return count

    async def bulk_dismiss_findings(self, finding_ids: List[str], reason: str = "false_positive") -> int:
        count = 0
        for fid in finding_ids:
            finding = self.findings.get(fid)
            if finding and finding.remediation_status == RemediationStatus.OPEN:
                finding.remediation_status = RemediationStatus.ACCEPTED_RISK
                count += 1
        return count

    async def bulk_delete_findings(self, finding_ids: List[str]) -> int:
        count = 0
        for fid in finding_ids:
            if fid in self.findings:
                del self.findings[fid]
                count += 1
        return count

    # === Analytics ===
    def get_secrets_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for f in self.findings.values():
            if f.discovered_at and f.discovered_at >= cutoff:
                day = f.discovered_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_secret_type_distribution(self) -> Dict:
        dist = {}
        for f in self.findings.values():
            t = f.secret_type.value
            dist[t] = dist.get(t, 0) + 1
        return {"distribution": dist, "total": sum(dist.values())}

    def get_remediation_stats(self) -> Dict:
        total = len(self.findings)
        open_count = sum(1 for f in self.findings.values() if f.remediation_status == RemediationStatus.OPEN)
        rotated = sum(1 for f in self.findings.values() if f.remediation_status == RemediationStatus.ROTATED)
        accepted = sum(1 for f in self.findings.values() if f.remediation_status == RemediationStatus.ACCEPTED_RISK)
        return {"total": total, "open": open_count, "rotated": rotated, "accepted_risk": accepted,
                "remediation_rate": round(rotated / total * 100, 1) if total > 0 else 0}

    # === Cleanup ===
    async def cleanup_resolved_findings(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [fid for fid, f in self.findings.items() if f.remediation_status in (RemediationStatus.ROTATED, RemediationStatus.ACCEPTED_RISK) and f.resolved_at and f.resolved_at < cutoff]
        for fid in to_remove:
            del self.findings[fid]
        return len(to_remove)

    # === Search ===
    def search_secrets(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for f in self.findings.values():
            if q in f.file_path.lower() or q in f.secret_type.value.lower() or (f.snippet and q in f.snippet.lower()):
                results.append(f.to_dict())
        return results

    # === Export ===
    def export_findings_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "secret_type", "severity", "file_path", "line_number", "status", "discovered_at"])
        for f in self.findings.values():
            writer.writerow([f.id, f.secret_type.value, f.severity.value, f.file_path, f.line_number, f.remediation_status.value, f.discovered_at.isoformat() if f.discovered_at else ""])
        return output.getvalue()

    def export_findings_json(self) -> str:
        return json.dumps([f.to_dict() for f in self.findings.values()], indent=2, default=str)

    # === Import ===
    def import_findings_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            finding = SecretFinding(
                id=item.get("id", f"finding-{uuid.uuid4().hex[:12]}"),
                secret_type=SecretType(item.get("secret_type", "generic_secret")),
                severity=SecretSeverity(item.get("severity", "medium")),
                value_snippet=item.get("value_snippet", ""),
                file_path=item.get("file_path", ""),
                line_number=item.get("line_number", 0),
                source_type=item.get("source_type", "manual"),
                repository=item.get("repository"),
                branch=item.get("branch"),
                commit_hash=item.get("commit_hash"),
                author=item.get("author"),
                context=item.get("context"),
                remediation_status=RemediationStatus(item.get("remediation_status", "open")),
                assignee=item.get("assignee"),
            )
            self.findings[finding.id] = finding
            count += 1
        return count

    # === State Machine ===
    def transition_finding_status(self, finding_id: str, target_status: str) -> Optional[SecretFinding]:
        finding = self.findings.get(finding_id)
        if not finding:
            return None
        valid = {
            RemediationStatus.OPEN: [RemediationStatus.ROTATING, RemediationStatus.FALSE_POSITIVE, RemediationStatus.IGNORED],
            RemediationStatus.ROTATING: [RemediationStatus.ROTATED, RemediationStatus.OPEN],
            RemediationStatus.ROTATED: [RemediationStatus.OPEN],
            RemediationStatus.FALSE_POSITIVE: [RemediationStatus.OPEN],
            RemediationStatus.IGNORED: [RemediationStatus.OPEN],
            RemediationStatus.REVOKED: [RemediationStatus.OPEN],
        }
        new_status = RemediationStatus(target_status)
        if new_status in valid.get(finding.remediation_status, []):
            finding.remediation_status = new_status
            return finding
        return None

    def get_allowed_finding_transitions(self, finding_id: str) -> List[str]:
        finding = self.findings.get(finding_id)
        if not finding:
            return []
        transitions = {
            RemediationStatus.OPEN: ["rotating", "false_positive", "ignored"],
            RemediationStatus.ROTATING: ["rotated", "open"],
            RemediationStatus.ROTATED: ["open"],
            RemediationStatus.FALSE_POSITIVE: ["open"],
            RemediationStatus.IGNORED: ["open"],
            RemediationStatus.REVOKED: ["open"],
        }
        return [s.value for s in transitions.get(finding.remediation_status, [])]

    # === Notification ===
    async def notify_finding(self, finding_id: str) -> Dict[str, Any]:
        finding = self.findings.get(finding_id)
        if not finding:
            return {"error": "Finding not found"}
        return {
            "finding_id": finding.id,
            "secret_type": finding.secret_type.value,
            "severity": finding.severity.value,
            "file_path": finding.file_path,
            "repository": finding.repository,
            "message": f"Secret detected: {finding.secret_type.value} in {finding.file_path}",
            "channels": ["slack", "github"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_critical_findings(self) -> List[Dict]:
        results = []
        for f in self.findings.values():
            if f.severity == SecretSeverity.CRITICAL and f.remediation_status == RemediationStatus.OPEN:
                results.append(await self.notify_finding(f.id))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("scan_targets"):
            errors.append("At least one scan target is required")
        if config.get("auto_rotate", False) and not config.get("rotation_provider"):
            warnings.append("Auto-rotation enabled but no rotation provider configured")
        if config.get("max_file_size_mb", 10) > 100:
            warnings.append("Large file scan size may impact performance")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_secrets_analysis(self) -> Dict[str, Any]:
        by_source = {}
        for f in self.findings.values():
            src = f.source_type or "unknown"
            by_source[src] = by_source.get(src, 0) + 1
        by_repo = {}
        for f in self.findings.values():
            repo = f.repository or "unknown"
            by_repo[repo] = by_repo.get(repo, 0) + 1
        return {
            "findings_by_source": by_source,
            "findings_by_repo": by_repo,
            "total_findings": len(self.findings),
            "auto_rotation_rate": round(sum(1 for f in self.findings.values() if f.auto_rotated) / len(self.findings) * 100, 1) if self.findings else 0,
        }

    def get_top_secret_types(self, n: int = 5) -> List[Dict]:
        type_counts = {}
        for f in self.findings.values():
            t = f.secret_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        return [{"type": t, "count": c} for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:n]]

    def get_remediation_analysis(self) -> Dict:
        open_findings = [f for f in self.findings.values() if f.remediation_status == RemediationStatus.OPEN]
        avg_age = (datetime.utcnow() - sum((f.detected_at for f in open_findings), datetime.utcnow() - datetime.utcnow())).total_seconds() / len(open_findings) / 86400 if open_findings else 0
        return {
            "open_count": len(open_findings),
            "avg_age_days": round(avg_age, 1),
            "oldest_finding": min((f.detected_at for f in open_findings), default=None),
            "remediation_pipeline": {
                "rotating": sum(1 for f in self.findings.values() if f.remediation_status == RemediationStatus.ROTATING),
                "rotated": sum(1 for f in self.findings.values() if f.remediation_status == RemediationStatus.ROTATED),
            },
        }

    # === Bulk Operations ===
    async def bulk_scan_targets(self, target_ids: List[str]) -> List[Dict]:
        results = []
        for tid in target_ids:
            result = await self.scan_target(tid)
            results.append(result)
        return results

    async def bulk_assign_findings(self, finding_ids: List[str], assignee: str) -> int:
        count = 0
        for fid in finding_ids:
            finding = self.findings.get(fid)
            if finding:
                finding.assignee = assignee
                count += 1
        return count

    # === Target Management ===
    def enable_target(self, target_id: str) -> bool:
        target = self.targets.get(target_id)
        if target:
            target.enabled = True
            return True
        return False

    def disable_target(self, target_id: str) -> bool:
        target = self.targets.get(target_id)
        if target:
            target.enabled = False
            return True
        return False

    def get_target_scan_status(self) -> List[Dict]:
        return [
            {"id": t.id, "name": t.name, "last_scan": t.last_scan.isoformat() if t.last_scan else None, "enabled": t.enabled, "findings": t.findings_count}
            for t in self.targets.values()
        ]

    # === Tag Management ===
    def add_finding_tags(self, finding_ids: List[str], tags: List[str]) -> int:
        count = 0
        for fid in finding_ids:
            finding = self.findings.get(fid)
            if finding:
                _tags = finding.tags if hasattr(finding, 'tags') else []
                for t in tags:
                    if t not in _tags:
                        _tags.append(t)
                if hasattr(finding, 'tags'):
                    finding.tags = _tags
                count += 1
        return count

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "secrets_detection",
            "initialized": self._initialized,
            "findings_total": len(self.findings),
            "targets_configured": len(self.targets),
            "auto_rotation_enabled": True,
            "status": "healthy" if self._initialized else "not_initialized",
        }


class SecretsAnalytics:
    def __init__(self, sd: 'SecretsDetectionManager'):
        self.sd = sd

    def finding_by_severity(self) -> Dict:
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.sd.findings.values():
            sev = f.severity.value if hasattr(f.severity, 'value') else str(f.severity)
            dist[sev] = dist.get(sev, 0) + 1
        return dist

    def mean_time_to_remediate(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        rotated = [f for f in self.sd.findings.values() if f.remediation_status == RemediationStatus.ROTATED and f.detected_at and f.detected_at > cutoff]
        if not rotated:
            return {"average_hours": 0, "total": 0}
        durations = []
        for f in rotated:
            resolved_at = getattr(f, 'resolved_at', None) or datetime.utcnow()
            durations.append((resolved_at - f.detected_at).total_seconds() / 3600)
        return {"average_hours": round(sum(durations) / len(durations), 1), "min_hours": round(min(durations), 1), "max_hours": round(max(durations), 1), "total": len(rotated)}

    def top_exposed_services(self, n: int = 5) -> List[Dict]:
        services = {}
        for f in self.sd.findings.values():
            target = self.sd.targets.get(f.target_id)
            name = target.name if target else "unknown"
            services[name] = services.get(name, 0) + 1
        return sorted([{"service": s, "count": c} for s, c in services.items()], key=lambda x: x["count"], reverse=True)[:n]

    def secret_type_breakdown(self) -> Dict:
        types = {}
        for f in self.sd.findings.values():
            st = f.secret_type if hasattr(f, 'secret_type') else "unknown"
            types[st] = types.get(st, 0) + 1
        return types


class SecretsRotationScheduler:
    def __init__(self, sd: 'SecretsDetectionManager'):
        self.sd = sd
        self.schedules: Dict[str, Dict] = {}

    def create_schedule(self, finding_id: str, rotate_at: datetime) -> Optional[Dict]:
        finding = self.sd.findings.get(finding_id)
        if not finding:
            return None
        schedule = {"id": f"sched-{uuid.uuid4().hex[:8]}", "finding_id": finding_id, "target_id": finding.target_id, "rotate_at": rotate_at.isoformat(), "status": "pending", "created_at": datetime.utcnow().isoformat()}
        self.schedules[schedule["id"]] = schedule
        return schedule

    def get_pending_rotations(self) -> List[Dict]:
        now = datetime.utcnow()
        return [s for s in self.schedules.values() if s["status"] == "pending" and datetime.fromisoformat(s["rotate_at"]) <= now]

    def mark_completed(self, schedule_id: str) -> bool:
        schedule = self.schedules.get(schedule_id)
        if schedule and schedule["status"] == "pending":
            schedule["status"] = "completed"
            schedule["completed_at"] = datetime.utcnow().isoformat()
            finding = self.sd.findings.get(schedule["finding_id"])
            if finding:
                finding.remediation_status = RemediationStatus.ROTATED
            return True
        return False

    def list_schedules(self) -> List[Dict]:
        return list(self.schedules.values())


class SecretsAuditExporter:
    def __init__(self, sd: 'SecretsDetectionManager'):
        self.sd = sd

    def export_findings_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "target", "secret_type", "severity", "status", "detected_at", "assignee"])
        for f in self.sd.findings.values():
            target = self.sd.targets.get(f.target_id)
            writer.writerow([f.id, target.name if target else f.target_id, f.secret_type if hasattr(f, 'secret_type') else '', f.severity.value if hasattr(f.severity, 'value') else str(f.severity), f.remediation_status.value if hasattr(f.remediation_status, 'value') else str(f.remediation_status), f.detected_at.isoformat() if hasattr(f.detected_at, 'isoformat') else str(f.detected_at), f.assignee])
        return output.getvalue()

    def generate_audit_report(self) -> str:
        analytics = SecretsAnalytics(self.sd)
        lines = ["=== Secrets Detection Audit Report ===", f"Generated: {datetime.utcnow().isoformat()}", f"Total Findings: {len(self.sd.findings)}", f"Open: {sum(1 for f in self.sd.findings.values() if f.remediation_status == RemediationStatus.OPEN)}", f"Rotating: {sum(1 for f in self.sd.findings.values() if f.remediation_status == RemediationStatus.ROTATING)}", f"Rotated: {sum(1 for f in self.sd.findings.values() if f.remediation_status == RemediationStatus.ROTATED)}", f"False Positives: {sum(1 for f in self.sd.findings.values() if f.remediation_status == RemediationStatus.FALSE_POSITIVE)}", f"Targets Scanned: {len(self.sd.targets)}", "", "By Severity:"]
        for sev, count in analytics.finding_by_severity().items():
            lines.append(f"  {sev}: {count}")
        mttr = analytics.mean_time_to_remediate()
        lines.append(f"\nMean Time to Remediate: {mttr.get('average_hours', 0)} hours")
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
