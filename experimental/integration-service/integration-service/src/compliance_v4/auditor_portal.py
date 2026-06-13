import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AuditScope(Enum):
    FULL = "full"
    LIMITED = "limited"
    READ_ONLY = "read_only"
    CUSTOM = "custom"


class FindingSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_REMEDIATION = "in_remediation"
    REMEDIATED = "remediated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class AuditStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class AuditorSession:
    session_id: str
    auditor_name: str
    auditor_email: str
    auditor_organization: str
    scope: AuditScope
    frameworks: List[str]
    access_granted_at: datetime
    access_expires_at: datetime
    status: str
    permissions: Dict[str, bool]
    last_active: Optional[datetime]
    ip_address: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "auditor_name": self.auditor_name,
            "auditor_email": self.auditor_email,
            "auditor_organization": self.auditor_organization,
            "scope": self.scope.value,
            "frameworks": self.frameworks,
            "access_granted_at": self.access_granted_at.isoformat(),
            "access_expires_at": self.access_expires_at.isoformat(),
            "status": self.status,
            "permissions": self.permissions,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "ip_address": self.ip_address,
        }


@dataclass
class EvidenceAccess:
    access_id: str
    evidence_id: str
    evidence_description: str
    framework: str
    control_id: str
    accessed_by: str
    accessed_at: datetime
    access_type: str
    session_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_id": self.access_id,
            "evidence_id": self.evidence_id,
            "evidence_description": self.evidence_description,
            "framework": self.framework,
            "control_id": self.control_id,
            "accessed_by": self.accessed_by,
            "accessed_at": self.accessed_at.isoformat(),
            "access_type": self.access_type,
            "session_id": self.session_id,
        }


@dataclass
class AuditFinding:
    finding_id: str
    audit_id: str
    control_id: str
    framework: str
    title: str
    description: str
    severity: FindingSeverity
    status: FindingStatus
    evidence_refs: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    remediation_notes: str
    closed_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "audit_id": self.audit_id,
            "control_id": self.control_id,
            "framework": self.framework,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "evidence_refs": self.evidence_refs,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "remediation_notes": self.remediation_notes,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


@dataclass
class AuditEngagement:
    audit_id: str
    auditor_organization: str
    auditor_name: str
    auditor_email: str
    framework: str
    scope: AuditScope
    scope_description: str
    period_start: datetime
    period_end: datetime
    status: AuditStatus
    findings: List[str]
    evidence_packages: List[str]
    created_at: datetime
    completed_at: Optional[datetime]
    report_url: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "auditor_organization": self.auditor_organization,
            "auditor_name": self.auditor_name,
            "auditor_email": self.auditor_email,
            "framework": self.framework,
            "scope": self.scope.value,
            "scope_description": self.scope_description,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status.value,
            "findings_count": len(self.findings),
            "findings": self.findings,
            "evidence_packages": self.evidence_packages,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "report_url": self.report_url,
        }


EVIDENCE_LIBRARY = [
    {"id": "ev_policy_001", "description": "Information Security Policy v4.2", "framework": "SOC_2", "control_id": "SOC2-CC1"},
    {"id": "ev_risk_001", "description": "Annual Risk Assessment Report 2025", "framework": "SOC_2", "control_id": "SOC2-CC2"},
    {"id": "ev_access_001", "description": "Access Control Policy and Procedures", "framework": "SOC_2", "control_id": "SOC2-CC5"},
    {"id": "ev_hipaa_001", "description": "HIPAA Security Rule Compliance Matrix", "framework": "HIPAA", "control_id": "HIPAA-164.308"},
    {"id": "ev_pci_001", "description": "PCI DSS v4.0 Self-Assessment Questionnaire", "framework": "PCI_DSS", "control_id": "PCI-1.1"},
    {"id": "ev_iso_001", "description": "ISO 27001:2022 Statement of Applicability", "framework": "ISO_27001", "control_id": "ISO-5.1"},
    {"id": "ev_gdpr_001", "description": "GDPR Data Processing Register", "framework": "GDPR", "control_id": "GDPR-ART5"},
    {"id": "ev_network_001", "description": "Network Segmentation Diagram", "framework": "PCI_DSS", "control_id": "PCI-1.1"},
    {"id": "ev_encrypt_001", "description": "Encryption Key Management Policy", "framework": "SOC_2", "control_id": "SOC2-C1"},
    {"id": "ev_backup_001", "description": "Backup Verification Logs - Q1 2025", "framework": "SOC_2", "control_id": "SOC2-A1"},
    {"id": "ev_training_001", "description": "Security Awareness Training Records", "framework": "HIPAA", "control_id": "HIPAA-164.308"},
    {"id": "ev_incident_001", "description": "Incident Response Test Results", "framework": "SOC_2", "control_id": "SOC2-CC4"},
    {"id": "ev_pen_test_001", "description": "Penetration Test Report - March 2025", "framework": "PCI_DSS", "control_id": "PCI-6.1"},
    {"id": "ev_vuln_001", "description": "Vulnerability Scan Results - Weekly", "framework": "PCI_DSS", "control_id": "PCI-6.1"},
    {"id": "ev_bcp_001", "description": "Business Continuity Plan v3.1", "framework": "ISO_27001", "control_id": "ISO-11.1"},
]


class AuditorPortalEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, AuditorSession] = {}
        self.evidence_access_log: List[EvidenceAccess] = []
        self.findings: Dict[str, AuditFinding] = {}
        self.engagements: Dict[str, AuditEngagement] = {}
        self.evidence_library = EVIDENCE_LIBRARY
        self.data_file = config.get("auditor_data_file", "data/auditor_portal.json")
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.sessions = {k: AuditorSession(**s) if isinstance(s, dict) else s for k, s in data.get("sessions", {}).items()}
                    self.evidence_access_log = [EvidenceAccess(**e) if isinstance(e, dict) else e for e in data.get("evidence_access_log", [])]
                    self.findings = {k: AuditFinding(**f) if isinstance(f, dict) else f for k, f in data.get("findings", {}).items()}
                    self.engagements = {k: AuditEngagement(**e) if isinstance(e, dict) else e for k, e in data.get("engagements", {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load auditor data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "sessions": {k: v.to_dict() for k, v in self.sessions.items()},
                    "evidence_access_log": [e.to_dict() for e in self.evidence_access_log[-500:]],
                    "findings": {k: v.to_dict() for k, v in self.findings.items()},
                    "engagements": {k: v.to_dict() for k, v in self.engagements.items()},
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save auditor data: {e}")

    def create_engagement(self, auditor_org: str, auditor_name: str, auditor_email: str,
                          framework: str, scope: str, scope_description: str,
                          period_start: datetime, period_end: datetime) -> AuditEngagement:
        scope_enum = AuditScope(scope) if scope in [s.value for s in AuditScope] else AuditScope.READ_ONLY
        engagement = AuditEngagement(
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            auditor_organization=auditor_org,
            auditor_name=auditor_name,
            auditor_email=auditor_email,
            framework=framework,
            scope=scope_enum,
            scope_description=scope_description,
            period_start=period_start,
            period_end=period_end,
            status=AuditStatus.SCHEDULED,
            findings=[],
            evidence_packages=[],
            created_at=datetime.utcnow(),
            completed_at=None,
            report_url=None,
        )
        self.engagements[engagement.audit_id] = engagement
        self._save()
        return engagement

    def create_session(self, auditor_name: str, auditor_email: str, auditor_org: str,
                       scope: str, frameworks: List[str], duration_hours: int = 48) -> AuditorSession:
        scope_enum = AuditScope(scope) if scope in [s.value for s in AuditScope] else AuditScope.READ_ONLY
        session = AuditorSession(
            session_id=f"as_{uuid.uuid4().hex[:12]}",
            auditor_name=auditor_name,
            auditor_email=auditor_email,
            auditor_organization=auditor_org,
            scope=scope_enum,
            frameworks=frameworks,
            access_granted_at=datetime.utcnow(),
            access_expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
            status="active",
            permissions={
                "view_evidence": True,
                "view_findings": True,
                "view_remediation": True,
                "create_findings": scope in ["full", "custom"],
                "export_reports": True,
            },
            last_active=None,
            ip_address=None,
        )
        self.sessions[session.session_id] = session
        self._save()
        return session

    def access_evidence(self, session_id: str, evidence_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        if session.status != "active" or session.access_expires_at < datetime.utcnow():
            return None
        if not session.permissions.get("view_evidence", False):
            return None

        evidence = next((e for e in self.evidence_library if e["id"] == evidence_id), None)
        if not evidence:
            return None

        access = EvidenceAccess(
            access_id=f"ea_{uuid.uuid4().hex[:12]}",
            evidence_id=evidence_id,
            evidence_description=evidence["description"],
            framework=evidence["framework"],
            control_id=evidence["control_id"],
            accessed_by=session.auditor_name,
            accessed_at=datetime.utcnow(),
            access_type="view",
            session_id=session_id,
        )
        self.evidence_access_log.append(access)
        session.last_active = datetime.utcnow()
        self._save()
        return {**evidence, "access_record": access.to_dict(), "content": f"Evidence content for {evidence['id']}: This is a read-only copy of the evidence document. All access is logged for audit purposes."}

    def get_evidence_by_control(self, control_id: str, framework: Optional[str] = None) -> List[Dict[str, Any]]:
        results = [e for e in self.evidence_library if e["control_id"] == control_id]
        if framework:
            results = [e for e in results if e["framework"] == framework]
        return results

    def get_all_evidence(self, framework: Optional[str] = None) -> List[Dict[str, Any]]:
        if framework:
            return [e for e in self.evidence_library if e["framework"] == framework]
        return self.evidence_library

    def control_mapping_by_framework(self, framework: str) -> Dict[str, Any]:
        evidence = [e for e in self.evidence_library if e["framework"] == framework]
        controls = {}
        for e in evidence:
            if e["control_id"] not in controls:
                controls[e["control_id"]] = []
            controls[e["control_id"]].append(e)
        return {"framework": framework, "controls": controls, "evidence_count": len(evidence), "control_count": len(controls)}

    def create_finding(self, session_id: str, audit_id: str, control_id: str,
                       framework: str, title: str, description: str, severity: str,
                       evidence_refs: Optional[List[str]] = None) -> Optional[AuditFinding]:

        session = self.sessions.get(session_id)
        if not session or not session.permissions.get("create_findings", False):
            return None

        engagement = next((e for e in self.engagements.values() if e.audit_id == audit_id), None)
        severity_enum = FindingSeverity(severity) if severity in [s.value for s in FindingSeverity] else FindingSeverity.MEDIUM

        finding = AuditFinding(
            finding_id=f"find_{uuid.uuid4().hex[:12]}",
            audit_id=audit_id,
            control_id=control_id,
            framework=framework,
            title=title,
            description=description,
            severity=severity_enum,
            status=FindingStatus.OPEN,
            evidence_refs=evidence_refs or [],
            created_by=session.auditor_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            remediation_notes="",
            closed_at=None,
        )
        self.findings[finding.finding_id] = finding
        if engagement:
            engagement.findings.append(finding.finding_id)
        self._save()
        return finding

    def update_finding_status(self, finding_id: str, status: str,
                              remediation_notes: str = "") -> Optional[AuditFinding]:
        finding = self.findings.get(finding_id)
        if not finding:
            return None
        try:
            finding.status = FindingStatus(status)
            finding.updated_at = datetime.utcnow()
            if remediation_notes:
                finding.remediation_notes = remediation_notes
            if finding.status == FindingStatus.CLOSED:
                finding.closed_at = datetime.utcnow()
            self._save()
        except ValueError:
            raise ValueError(f"Invalid status: {status}")
        return finding

    def get_findings(self, audit_id: Optional[str] = None,
                     framework: Optional[str] = None,
                     severity: Optional[str] = None,
                     status: Optional[str] = None) -> List[AuditFinding]:
        results = list(self.findings.values())
        if audit_id:
            results = [f for f in results if f.audit_id == audit_id]
        if framework:
            results = [f for f in results if f.framework == framework]
        if severity:
            results = [f for f in results if f.severity.value == severity]
        if status:
            results = [f for f in results if f.status.value == status]
        return sorted(results, key=lambda f: f.created_at, reverse=True)

    def get_engagements(self, status: Optional[str] = None,
                        framework: Optional[str] = None) -> List[AuditEngagement]:
        results = list(self.engagements.values())
        if status:
            results = [e for e in results if e.status.value == status]
        if framework:
            results = [e for e in results if e.framework == framework]
        return sorted(results, key=lambda e: e.created_at, reverse=True)

    def get_session(self, session_id: str) -> Optional[AuditorSession]:
        return self.sessions.get(session_id)

    def expire_session(self, session_id: str) -> Optional[AuditorSession]:
        session = self.sessions.get(session_id)
        if session:
            session.status = "expired"
            session.access_expires_at = datetime.utcnow()
            self._save()
        return session

    def get_evidence_access_log(self, session_id: Optional[str] = None,
                                evidence_id: Optional[str] = None,
                                days: int = 30) -> List[EvidenceAccess]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = [a for a in self.evidence_access_log if a.accessed_at >= cutoff]
        if session_id:
            results = [a for a in results if a.session_id == session_id]
        if evidence_id:
            results = [a for a in results if a.evidence_id == evidence_id]
        return sorted(results, key=lambda a: a.accessed_at, reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        by_framework = {}
        by_severity = {}
        by_status = {}
        for f in self.findings.values():
            by_framework[f.framework] = by_framework.get(f.framework, 0) + 1
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
            by_status[f.status.value] = by_status.get(f.status.value, 0) + 1
        return {
            "active_sessions": sum(1 for s in self.sessions.values() if s.status == "active"),
            "total_engagements": len(self.engagements),
            "active_engagements": sum(1 for e in self.engagements.values() if e.status.value in ("scheduled", "in_progress")),
            "total_findings": len(self.findings),
            "open_findings": sum(1 for f in self.findings.values() if f.status.value in ("open", "acknowledged", "in_remediation")),
            "findings_by_framework": by_framework,
            "findings_by_severity": by_severity,
            "findings_by_status": by_status,
            "evidence_items_available": len(self.evidence_library),
            "evidence_access_log_count": len(self.evidence_access_log),
        }

    def complete_engagement(self, audit_id: str, report_url: Optional[str] = None) -> Optional[AuditEngagement]:
        engagement = self.engagements.get(audit_id)
        if engagement:
            engagement.status = AuditStatus.COMPLETED
            engagement.completed_at = datetime.utcnow()
            engagement.report_url = report_url
            self._save()
        return engagement

    def get_engagement_details(self, audit_id: str) -> Dict[str, Any]:
        engagement = self.engagements.get(audit_id)
        if not engagement:
            return {"error": "Engagement not found"}
        fw_findings = [f for f in self.findings.values() if f.audit_id == audit_id]
        return {
            "engagement": engagement.to_dict(),
            "findings_summary": {
                "total": len(fw_findings),
                "open": sum(1 for f in fw_findings if f.status in (FindingStatus.OPEN, FindingStatus.ACKNOWLEDGED)),
                "remediated": sum(1 for f in fw_findings if f.status in (FindingStatus.REMEDIATED, FindingStatus.CLOSED)),
                "by_severity": {s.value: sum(1 for f in fw_findings if f.severity == s) for s in FindingSeverity},
            },
        }

    def revoke_session(self, session_id: str) -> Optional[AuditorSession]:
        session = self.sessions.get(session_id)
        if session:
            session.status = "revoked"
            session.access_expires_at = datetime.utcnow()
            self._save()
        return session

    def extend_session(self, session_id: str, hours: int = 24) -> Optional[AuditorSession]:
        session = self.sessions.get(session_id)
        if session and session.status == "active":
            session.access_expires_at = session.access_expires_at + timedelta(hours=hours)
            self._save()
        return session

    def search_findings(self, query: str) -> List[AuditFinding]:
        q = query.lower()
        return [f for f in self.findings.values()
                if q in f.title.lower() or q in f.description.lower() or q in f.control_id.lower()]

    def batch_update_findings(self, finding_ids: List[str], status: str,
                               remediation_notes: str = "") -> Dict[str, Any]:
        results = {}
        for fid in finding_ids:
            try:
                finding = self.update_finding_status(fid, status, remediation_notes)
                results[fid] = {"success": finding is not None}
            except Exception as e:
                results[fid] = {"success": False, "error": str(e)}
        return results

    def get_auditor_activity(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        access_logs = [a for a in self.evidence_access_log if a.session_id == session_id]
        findings_created = [f for f in self.findings.values() if f.created_by == session.auditor_name]
        return {
            "session": session.to_dict(),
            "evidence_accessed": len(access_logs),
            "findings_created": len(findings_created),
            "last_active": session.last_active.isoformat() if session.last_active else None,
            "activity_summary": f"{len(access_logs)} evidence items accessed, {len(findings_created)} findings created",
        }

    def add_evidence_to_library(self, evidence_def: Dict[str, Any]) -> Dict[str, Any]:
        new_id = f"ev_{uuid.uuid4().hex[:12]}"
        entry = {
            "id": new_id,
            "description": evidence_def.get("description", ""),
            "framework": evidence_def.get("framework", ""),
            "control_id": evidence_def.get("control_id", ""),
        }
        self.evidence_library.append(entry)
        return entry


def validate_auditor_session(session: AuditorSession) -> List[str]:
    issues = []
    if session.access_expires_at < datetime.utcnow():
        issues.append("Session has expired")
    if session.status != "active":
        issues.append(f"Session status is {session.status}")
    return issues


def categorize_findings_by_severity(findings: List[AuditFinding]) -> Dict[str, List[AuditFinding]]:
    categories = {}
    for f in findings:
        categories.setdefault(f.severity.value, []).append(f)
    return categories


def compute_remediation_progress(findings: List[AuditFinding]) -> Dict[str, Any]:
    total = len(findings)
    closed = sum(1 for f in findings if f.status == FindingStatus.CLOSED)
    in_progress = sum(1 for f in findings if f.status == FindingStatus.IN_REMEDIATION)
    open_findings = total - closed - in_progress
    return {
        "total": total,
        "closed": closed,
        "in_progress": in_progress,
        "open": open_findings,
        "progress_percentage": round((closed / total) * 100, 1) if total else 0,
    }


def search_evidence_library(library: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = query.lower()
    return [e for e in library if q in e["description"].lower() or q in e["framework"].lower() or q in e["control_id"].lower()]


def group_engagements_by_framework(engagements: List[AuditEngagement]) -> Dict[str, List[AuditEngagement]]:
    groups = {}
    for e in engagements:
        groups.setdefault(e.framework, []).append(e)
    return groups


def filter_engagements_by_date(engagements: List[AuditEngagement], start: datetime, end: datetime) -> List[AuditEngagement]:
    return [e for e in engagements if start <= e.created_at <= end]


class AuditorBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_findings(self, findings_data: List[Dict[str, Any]]) -> List[AuditFinding]:
        results = []
        for data in findings_data:
            try:
                finding = AuditFinding(
                    finding_id=f"find_{uuid.uuid4().hex[:12]}",
                    engagement_id=data["engagement_id"],
                    title=data["title"],
                    severity=FindingSeverity(data.get("severity", "medium")),
                    description=data.get("description", ""),
                    control_id=data.get("control_id"),
                    status=FindingStatus.OPEN,
                    created_by=data.get("created_by", "system"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                results.append(finding)
                self.batch_log.append({"action": "create_finding", "finding_id": finding.finding_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "create_finding", "title": data.get("title"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log


async def paginate_engagements(engagements: List[AuditEngagement], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(engagements)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [e.to_dict() for e in engagements[start:end]],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


async def paginate_findings(findings: List[AuditFinding], page: int = 1, page_size: int = 20, severity: Optional[str] = None) -> Dict[str, Any]:
    filtered = [f for f in findings if severity is None or f.severity.value == severity]
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [f.to_dict() for f in filtered[start:end]],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


def export_auditor_data(engagements: List[AuditEngagement], findings: List[AuditFinding], sessions: List[AuditorSession]) -> Dict[str, Any]:
    export_id = f"aud_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id,
        "exported_at": datetime.utcnow().isoformat(),
        "engagements": [e.to_dict() for e in engagements],
        "findings": [f.to_dict() for f in findings],
        "sessions": [s.to_dict() for s in sessions],
        "summary": {"total_engagements": len(engagements), "total_findings": len(findings), "total_sessions": len(sessions)},
    }


def import_findings_from_external(portal: AuditorPortal, external_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    import_id = f"ext_find_{uuid.uuid4().hex[:8]}"
    imported = 0
    for ext in external_findings:
        try:
            portal.create_finding(
                engagement_id=ext.get("engagement_id", "unknown"),
                title=ext.get("title", "Imported Finding"),
                severity=ext.get("severity", "medium"),
                description=ext.get("description", ""),
                control_id=ext.get("control_id"),
                created_by=ext.get("source", "external"),
            )
            imported += 1
        except Exception as e:
            pass
    return {"import_id": import_id, "imported_at": datetime.utcnow().isoformat(), "imported": imported}


def compute_finding_statistics(findings: List[AuditFinding]) -> Dict[str, Any]:
    by_severity: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for f in findings:
        sev = f.severity.value
        by_severity[sev] = by_severity.get(sev, 0) + 1
        st = f.status.value
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_status": by_status,
        "open_critical": sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL and f.status == FindingStatus.OPEN),
        "closed_count": sum(1 for f in findings if f.status == FindingStatus.CLOSED),
        "resolution_rate": round(sum(1 for f in findings if f.status in (FindingStatus.CLOSED, FindingStatus.IN_REMEDIATION)) / len(findings) * 100, 1) if findings else 0,
    }


def compute_engagement_performance(engagements: List[AuditEngagement]) -> Dict[str, Any]:
    completed = [e for e in engagements if e.status == "completed"]
    active = [e for e in engagements if e.status in ("active", "in_progress")]
    total_duration = 0
    for e in completed:
        if e.start_date and e.end_date:
            total_duration += (e.end_date - e.start_date).days
    return {
        "total_engagements": len(engagements),
        "completed_count": len(completed),
        "active_count": len(active),
        "completion_rate": round(len(completed) / len(engagements) * 100, 1) if engagements else 0,
        "avg_duration_days": round(total_duration / len(completed), 1) if completed else 0,
    }


class AuditorConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        max_sessions = self.config.get("max_parallel_sessions")
        if max_sessions is not None and max_sessions < 1:
            self.errors.append("max_parallel_sessions must be >= 1")
        session_timeout = self.config.get("session_timeout_hours")
        if session_timeout is not None and session_timeout < 1:
            self.errors.append("session_timeout_hours must be >= 1")
        if not self.config.get("auditor_data_file"):
            self.errors.append("auditor_data_file is required")
        return len(self.errors) == 0


class FindingSeverityClassifier:
    def classify(self, description: str) -> str:
        critical_kw = ["pii", "phi", "cardholder", "password", "credential", "bypass", "remote code execution"]
        high_kw = ["encryption", "access control", "vulnerability", "misconfiguration", "patch"]
        medium_kw = ["logging", "monitoring", "documentation", "policy", "training"]
        desc_lower = description.lower()
        for kw in critical_kw:
            if kw in desc_lower:
                return "critical"
        for kw in high_kw:
            if kw in desc_lower:
                return "high"
        for kw in medium_kw:
            if kw in desc_lower:
                return "medium"
        return "low"


def generate_auditor_report(engagements: List[AuditEngagement], findings: List[AuditFinding]) -> Dict[str, Any]:
    report_id = f"aud_report_{uuid.uuid4().hex[:12]}"
    return {
        "report_id": report_id,
        "generated_at": datetime.utcnow().isoformat(),
        "engagement_summary": compute_engagement_performance(engagements),
        "finding_summary": compute_finding_statistics(findings),
        "critical_findings": [f.to_dict() for f in findings if f.severity == FindingSeverity.CRITICAL],
        "open_findings": [f.to_dict() for f in findings if f.status == FindingStatus.OPEN],
    }


def score_auditor_performance(sessions: List[AuditorSession], findings: List[AuditFinding]) -> Dict[str, Any]:
    by_auditor: Dict[str, Dict[str, Any]] = {}
    for session in sessions:
        auditor = session.auditor_name
        if auditor not in by_auditor:
            by_auditor[auditor] = {"session_count": 0, "findings_created": 0, "evidence_accessed": 0}
        by_auditor[auditor]["session_count"] += 1
    for finding in findings:
        auditor = finding.created_by
        if auditor in by_auditor:
            by_auditor[auditor]["findings_created"] += 1
    scored = {}
    for auditor, data in by_auditor.items():
        efficiency = round(data["findings_created"] / data["session_count"], 1) if data["session_count"] else 0
        scored[auditor] = {**data, "efficiency_score": efficiency}
    return scored

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class auditor_portal_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class auditor_portal_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class auditor_portal_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class auditor_portal_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class auditor_portal_Cache:
    def __init__(self, ttl=300):
        self._store = {}; self._ttl = ttl
    def get(self, key: str):
        e = self._store.get(key)
        if e and (datetime.utcnow() - e["ts"]).seconds < self._ttl:
            return e["val"]
        return None
    def set(self, key: str, val: Any):
        self._store[key] = {"val": val, "ts": datetime.utcnow()}
    def invalidate(self, key: str):
        self._store.pop(key, None)

class auditor_portal_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class auditor_portal_Queue:
    def __init__(self):
        self._items = []
    def push(self, item: Any):
        self._items.append(item)
    def pop(self):
        return self._items.pop(0) if self._items else None
    def size(self):
        return len(self._items)
    def drain(self):
        items = list(self._items); self._items.clear(); return items

class auditor_portal_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class auditor_portal_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_portal_engagements_store: Dict[str, AuditEngagement] = {}
_portal_findings_store: Dict[str, AuditFinding] = {}


def search_auditor_engagements(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for e in _portal_engagements_store.values():
        if query.lower() in e.title.lower() or query.lower() in e.customer.lower():
            results.append({"id": e.engagement_id, "title": e.title, "customer": e.customer, "status": e.status.value})
            if len(results) >= limit:
                break
    return results


def recommend_auditor_cleanup(days_threshold: int = 180) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    stale = []
    for e in _portal_engagements_store.values():
        created = datetime.fromisoformat(e.created_at.replace("Z", ""))
        if created < cutoff and e.status in (AuditStatus.COMPLETED, AuditStatus.CANCELLED):
            stale.append({"id": e.engagement_id, "title": e.title, "created": e.created_at, "status": e.status.value})
    return stale


def batch_close_engagements(engagement_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "close", "succeeded": [], "failed": [], "total": len(engagement_ids)}
    for eid in engagement_ids:
        e = _portal_engagements_store.get(eid)
        if e:
            e.status = AuditStatus.COMPLETED
            e.completed_at = datetime.utcnow().isoformat()
            op["succeeded"].append(eid)
        else:
            op["failed"].append(eid)
    return op


def get_auditor_summary() -> Dict[str, Any]:
    total = len(_portal_engagements_store)
    scheduled = sum(1 for e in _portal_engagements_store.values() if e.status == AuditStatus.SCHEDULED)
    in_progress = sum(1 for e in _portal_engagements_store.values() if e.status == AuditStatus.IN_PROGRESS)
    completed = sum(1 for e in _portal_engagements_store.values() if e.status == AuditStatus.COMPLETED)
    critical_findings = sum(1 for f in _portal_findings_store.values() if f.severity == FindingSeverity.CRITICAL and f.status != FindingStatus.CLOSED)
    return {"total": total, "scheduled": scheduled, "in_progress": in_progress, "completed": completed, "critical_findings": critical_findings}


class AuditorSessionManager:
    def __init__(self):
        self._sessions = _portal_engagements_store
        self._findings = _portal_findings_store

    def revoke_session(self, session_id: str) -> bool:
        s = self._sessions.get(session_id)
        if s:
            s.status = AuditStatus.COMPLETED
            return True
        return False

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        return [{"id": e.engagement_id, "auditor": e.auditor_name, "org": e.auditor_org, "scope": e.scope.value if hasattr(e.scope, 'value') else e.scope, "expires": e.access_expires_at.isoformat() if hasattr(e.access_expires_at, 'isoformat') else e.access_expires_at} for e in self._sessions.values() if e.status in (AuditStatus.SCHEDULED, AuditStatus.IN_PROGRESS)]

    def get_findings_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        return [{"id": f.finding_id, "title": f.title, "status": f.status.value if hasattr(f.status, 'value') else f.status, "severity": f.severity.value} for f in self._findings.values() if f.severity.value == severity]

    def resolve_finding(self, finding_id: str, resolution: str = "") -> bool:
        f = self._findings.get(finding_id)
        if f:
            f.status = FindingStatus.CLOSED
            return True
        return False

    def batch_resolve_findings(self, finding_ids: List[str]) -> Dict[str, Any]:
        op: Dict[str, Any] = {"operation": "batch_resolve", "succeeded": [], "failed": [], "total": len(finding_ids)}
        for fid in finding_ids:
            if self.resolve_finding(fid):
                op["succeeded"].append(fid)
            else:
                op["failed"].append(fid)
        return op


class AuditorReportGenerator:
    def __init__(self):
        self._sessions = _portal_engagements_store
        self._findings = _portal_findings_store

    def generate_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self._sessions.get(session_id)
        if not s:
            return None
        findings = [f for f in self._findings.values() if f.engagement_id == session_id]
        return {
            "session_id": s.engagement_id, "auditor": s.auditor_name, "org": s.auditor_org,
            "scope": s.scope.value if hasattr(s.scope, 'value') else s.scope,
            "status": s.status.value if hasattr(s.status, 'value') else s.status,
            "total_findings": len(findings),
            "open_findings": sum(1 for f in findings if f.status != FindingStatus.CLOSED),
            "critical": sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL),
            "high": sum(1 for f in findings if f.severity == FindingSeverity.HIGH),
            "medium": sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM),
            "low": sum(1 for f in findings if f.severity == FindingSeverity.LOW),
        }

    def export_findings_csv(self, session_id: Optional[str] = None) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["finding_id", "title", "severity", "status", "engagement_id"])
        findings = [f for f in self._findings.values() if not session_id or f.engagement_id == session_id]
        for f in findings:
            writer.writerow([f.finding_id, f.title, f.severity.value, f.status.value if hasattr(f.status, 'value') else f.status, f.engagement_id])
        return output.getvalue()


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
        return {"total_checks": 0, "passed": 0, "failed": 0, "waived": 0, "compliance_score": 100.0}

    def validate_framework(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "framework_version": "v4"}

class ComplianceResult(BaseModel):
    success: bool = True
    operation: str = ""
    control_id: Optional[str] = None
    status: str = Field(default="compliant")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    framework: str = Field(default="generic")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    passed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_pass(self) -> None:
        self.passed += 1

    def record_fail(self) -> None:
        self.failed += 1

    def complete(self) -> None:
        self.status = "completed"

class ControlCheck(BaseModel):
    control_id: str
    name: str
    category: str = Field(default="general")
    severity: str = Field(default="medium")
    status: str = Field(default="compliant")
    tested_at: datetime = Field(default_factory=datetime.utcnow)
    evidence: Optional[str] = None
    notes: str = ""

class ComplianceScanner:
    def __init__(self) -> None:
        self._controls: Dict[str, ControlCheck] = {}

    def register_control(self, control: ControlCheck) -> None:
        self._controls[control.control_id] = control

    def run_check(self, control_id: str) -> ControlCheck:
        control = self._controls.get(control_id)
        if not control:
            raise ValueError(f"Control {control_id} not found")
        control.tested_at = datetime.utcnow()
        control.status = "compliant" if random.random() > 0.1 else "non_compliant"
        return control

    def run_all(self) -> Dict[str, Any]:
        results = {}
        for cid in self._controls:
            results[cid] = self.run_check(cid)
        compliant = sum(1 for r in results.values() if r.status == "compliant")
        return {"total": len(results), "compliant": compliant,
                "non_compliant": len(results) - compliant,
                "score": round(compliant / max(len(results), 1) * 100, 1)}

    def get_controls_by_severity(self, severity: str) -> List[ControlCheck]:
        return [c for c in self._controls.values() if c.severity == severity]

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str
    file_path: str = ""
    content_hash: str = ""
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collected_by: str = Field(default="system")
    valid: bool = True
    expires_at: Optional[datetime] = None

class EvidenceStore:
    def __init__(self) -> None:
        self._items: List[EvidenceItem] = []

    def add(self, control_id: str, file_path: str, content_hash: str, collected_by: str = "system") -> EvidenceItem:
        item = EvidenceItem(control_id=control_id, file_path=file_path,
                            content_hash=content_hash, collected_by=collected_by)
        self._items.append(item)
        return item

    def get_for_control(self, control_id: str) -> List[EvidenceItem]:
        return [i for i in self._items if i.control_id == control_id]

    def invalidate_expired(self) -> int:
        now = datetime.utcnow()
        count = 0
        for item in self._items:
            if item.expires_at and now > item.expires_at:
                item.valid = False
                count += 1
        return count

    def get_summary(self) -> Dict[str, Any]:
        return {"total": len(self._items), "valid": sum(1 for i in self._items if i.valid),
                "invalid": sum(1 for i in self._items if not i.valid)}

class AuditSchedule(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework: str
    scope: List[str] = Field(default_factory=list)
    scheduled_date: datetime
    completed_date: Optional[datetime] = None
    status: str = Field(default="scheduled")
    assigned_auditor: str = ""
    findings_count: int = Field(default=0)

class AuditPlanner:
    def __init__(self) -> None:
        self._audits: List[AuditSchedule] = []

    def schedule(self, framework: str, scheduled_date: datetime, scope: List[str],
                 auditor: str = "") -> AuditSchedule:
        audit = AuditSchedule(framework=framework, scheduled_date=scheduled_date,
                              scope=scope, assigned_auditor=auditor)
        self._audits.append(audit)
        return audit

    def complete(self, audit_id: str, findings: int = 0) -> bool:
        for a in self._audits:
            if a.audit_id == audit_id and a.status == "scheduled":
                a.status = "completed"
                a.completed_date = datetime.utcnow()
                a.findings_count = findings
                return True
        return False

    def get_upcoming(self, days: int = 30) -> List[AuditSchedule]:
        cutoff = datetime.utcnow() + timedelta(days=days)
        return [a for a in self._audits if a.status == "scheduled" and a.scheduled_date <= cutoff]

    def get_overdue(self) -> List[AuditSchedule]:
        now = datetime.utcnow()
        return [a for a in self._audits if a.status == "scheduled" and a.scheduled_date < now]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._audits)
        scheduled = sum(1 for a in self._audits if a.status == "scheduled")
        completed = sum(1 for a in self._audits if a.status == "completed")
        return {"total": total, "scheduled": scheduled, "completed": completed,
                "overdue": len(self.get_overdue()),
                "completion_rate": round(completed / max(total, 1) * 100, 1)}

class PolicyRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    category: str = Field(default="general")
    severity: str = Field(default="medium")
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyEngine:
    def __init__(self) -> None:
        self._rules: Dict[str, PolicyRule] = {}

    def add_rule(self, rule: PolicyRule) -> None:
        self._rules[rule.rule_id] = rule

    def evaluate(self, rule_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        rule = self._rules.get(rule_id)
        if not rule:
            return {"rule_id": rule_id, "status": "error", "message": "Rule not found"}
        if not rule.enabled:
            return {"rule_id": rule_id, "status": "disabled"}
        passed = random.random() > 0.2
        return {"rule_id": rule_id, "name": rule.name, "status": "passed" if passed else "failed",
                "severity": rule.severity}

    def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = [self.evaluate(rid, context) for rid in self._rules]
        passed = sum(1 for r in results if r.get("status") == "passed")
        return {"total": len(results), "passed": passed, "failed": len(results) - passed,
                "results": results}

    def get_rules_by_category(self, category: str) -> List[PolicyRule]:
        return [r for r in self._rules.values() if r.category == category]

class RemediationPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str
    action: str
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""

class RemediationTracker:
    def __init__(self) -> None:
        self._plans: List[RemediationPlan] = []

    def create(self, finding_id: str, action: str, priority: str = "medium", assignee: str = "") -> RemediationPlan:
        plan = RemediationPlan(finding_id=finding_id, action=action, priority=priority, assigned_to=assignee)
        self._plans.append(plan)
        return plan

    def resolve(self, plan_id: str) -> bool:
        for p in self._plans:
            if p.plan_id == plan_id and p.status == "open":
                p.status = "resolved"
                p.resolved_at = datetime.utcnow()
                return True
        return False

    def get_open(self) -> List[RemediationPlan]:
        return [p for p in self._plans if p.status == "open"]

    def get_by_priority(self, priority: str) -> List[RemediationPlan]:
        return [p for p in self._plans if p.priority == priority]

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._plans), "open": len(self.get_open()),
                "resolved": sum(1 for p in self._plans if p.status == "resolved"),
                "by_priority": {p: sum(1 for x in self._plans if x.priority == p) for p in set(x.priority for x in self._plans)}}
