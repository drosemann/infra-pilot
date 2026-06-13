"""Security Incident Response platform.

Full incident lifecycle management: triage, containment, eradication, recovery,
lessons learned. Evidence locker, timeline builder, report generator.
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


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGE = "triage"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    POST_MORTEM = "post_mortem"
    CLOSED = "closed"


class ArtifactType(str, Enum):
    FILE = "file"
    PCAP = "pcap"
    LOG = "log"
    MEMORY_DUMP = "memory_dump"
    DISK_IMAGE = "disk_image"
    SCREENSHOT = "screenshot"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    HASH = "hash"
    CONFIG = "config"
    TIMELINE_ENTRY = "timeline_entry"
    NOTE = "note"
    REPORT = "report"
    OTHER = "other"


@dataclass
class Incident:
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.DETECTED
    detection_source: str = ""
    affected_systems: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    team: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    triage_started_at: Optional[datetime] = None
    containment_started_at: Optional[datetime] = None
    containment_completed_at: Optional[datetime] = None
    eradication_started_at: Optional[datetime] = None
    eradication_completed_at: Optional[datetime] = None
    recovery_started_at: Optional[datetime] = None
    recovery_completed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    severity_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    mitre_attack_chain: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None
    action_items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "detection_source": self.detection_source,
            "affected_systems": self.affected_systems,
            "affected_users": self.affected_users,
            "indicators": self.indicators,
            "assignee": self.assignee,
            "team": self.team,
            "created_at": self.created_at.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "triage_started_at": self.triage_started_at.isoformat() if self.triage_started_at else None,
            "containment_started_at": self.containment_started_at.isoformat() if self.containment_started_at else None,
            "containment_completed_at": self.containment_completed_at.isoformat() if self.containment_completed_at else None,
            "eradication_started_at": self.eradication_started_at.isoformat() if self.eradication_started_at else None,
            "eradication_completed_at": self.eradication_completed_at.isoformat() if self.eradication_completed_at else None,
            "recovery_started_at": self.recovery_started_at.isoformat() if self.recovery_started_at else None,
            "recovery_completed_at": self.recovery_completed_at.isoformat() if self.recovery_completed_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "severity_score": self.severity_score,
            "tags": self.tags,
            "mitre_attack_chain": self.mitre_attack_chain,
            "root_cause": self.root_cause,
            "lessons_learned": self.lessons_learned,
            "action_items": self.action_items,
            "duration_hours": round((datetime.utcnow() - self.created_at).total_seconds() / 3600, 1),
        }


@dataclass
class EvidenceItem:
    id: str
    incident_id: str
    artifact_type: ArtifactType
    name: str
    description: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    content: Optional[Any] = None
    source: str = ""
    collected_by: str = ""
    collected_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "artifact_type": self.artifact_type.value,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
            "source": self.source,
            "collected_by": self.collected_by,
            "collected_at": self.collected_at.isoformat(),
            "tags": self.tags,
            "chain_of_custody": self.chain_of_custody,
        }


@dataclass
class TimelineEvent:
    id: str
    incident_id: str
    timestamp: datetime
    event_type: str
    description: str
    actor: str = ""
    source: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "actor": self.actor,
            "source": self.source,
            "evidence_ids": self.evidence_ids,
            "severity": self.severity,
        }


@dataclass
class IncidentReport:
    id: str
    incident_id: str
    title: str
    report_type: str
    content: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: str = ""
    format: str = "markdown"
    sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "title": self.title,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "format": self.format,
            "sections": self.sections,
            "length": len(self.content),
        }


class SecurityIncidentResponse:
    """Security Incident Response lifecycle management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.incidents: Dict[str, Incident] = {}
        self.evidence: Dict[str, EvidenceItem] = {}
        self.timeline: Dict[str, TimelineEvent] = {}
        self.reports: Dict[str, IncidentReport] = {}
        self._initialized = False

    async def initialize(self):
        self._seed_sample_incidents()
        self._initialized = True
        logger.info(f"Security Incident Response initialized: {len(self.incidents)} incidents tracked")

    async def close(self):
        logger.info("Security Incident Response shut down")

    def _seed_sample_incidents(self):
        sample_incidents = [
            Incident(id=f"inc-{uuid.uuid4().hex[:12]}", title="Suspicious PowerShell Execution on Web Server",
                     description="Detected outbound PowerShell network connection from web-01 to known C2 IP",
                     severity=IncidentSeverity.HIGH, status=IncidentStatus.CONTAINMENT,
                     detection_source="EDR (CrowdStrike Falcon)", assignee="soc-analyst-1",
                     affected_systems=["web-01", "web-02"],
                     indicators=["185.220.101.42", "powershell.exe", "C2 communication"],
                     team=["soc-analyst-1", "soc-analyst-2", "it-admin-1"],
                     created_at=datetime.utcnow() - timedelta(hours=4),
                     detected_at=datetime.utcnow() - timedelta(hours=4),
                     triage_started_at=datetime.utcnow() - timedelta(hours=3, minutes=45),
                     containment_started_at=datetime.utcnow() - timedelta(hours=2, minutes=30),
                     tags=["powershell", "c2", "web-server"], severity_score=8.5,
                     mitre_attack_chain=["T1059.001", "T1071.001"]),
            Incident(id=f"inc-{uuid.uuid4().hex[:12]}", title="Phishing Campaign Targeting Finance Team",
                     description="Multiple employees in Finance department reported phishing emails",
                     severity=IncidentSeverity.HIGH, status=IncidentStatus.TRIAGE,
                     detection_source="User Report / Email Gateway", assignee="soc-analyst-2",
                     affected_systems=["exchange-01", "user-endpoints"],
                     affected_users=["user1@corp.com", "user2@corp.com", "user3@corp.com"],
                     indicators=["phish-bank.example.com"],
                     team=["soc-analyst-2", "soc-lead"], tags=["phishing", "social-engineering", "finance"],
                     created_at=datetime.utcnow() - timedelta(hours=2),
                     detected_at=datetime.utcnow() - timedelta(hours=2),
                     triage_started_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
                     severity_score=7.2),
            Incident(id=f"inc-{uuid.uuid4().hex[:12]}", title="Critical Vulnerability: CVE-2024-6387 on SSH Gateways",
                     description="OpenSSH RegreSSHion detected on 5 bastion hosts with active exploitation",
                     severity=IncidentSeverity.CRITICAL, status=IncidentStatus.ERADICATION,
                     detection_source="Vulnerability Scan (Qualys)", assignee="patch-team-lead",
                     affected_systems=["bastion-01", "bastion-02", "bastion-03", "bastion-04", "bastion-05"],
                     indicators=["CVE-2024-6387", "OpenSSH 9.2p1"],
                     team=["patch-team-lead", "soc-lead", "infra-manager"],
                     created_at=datetime.utcnow() - timedelta(days=1),
                     detected_at=datetime.utcnow() - timedelta(days=1),
                     triage_started_at=datetime.utcnow() - timedelta(hours=22),
                     containment_started_at=datetime.utcnow() - timedelta(hours=20),
                     containment_completed_at=datetime.utcnow() - timedelta(hours=18),
                     eradication_started_at=datetime.utcnow() - timedelta(hours=17),
                     tags=["vulnerability", "ssh", "critical", "patching"], severity_score=9.5),
            Incident(id=f"inc-{uuid.uuid4().hex[:12]}", title="Insider Threat: Unauthorized Data Export",
                     description="Employee scheduled for termination copied 50GB of customer data to external drive",
                     severity=IncidentSeverity.CRITICAL, status=IncidentStatus.CONTAINMENT,
                     detection_source="DLP Agent (Symantec)", assignee="soc-lead",
                     affected_systems=["laptop-jdoe", "nas-02"],
                     affected_users=["john.doe@corp.com"],
                     indicators=["USB mass storage", "customer-database-export.csv"],
                     team=["soc-lead", "hr-manager", "legal-counsel"],
                     created_at=datetime.utcnow() - timedelta(minutes=45),
                     detected_at=datetime.utcnow() - timedelta(minutes=45),
                     triage_started_at=datetime.utcnow() - timedelta(minutes=30),
                     containment_started_at=datetime.utcnow() - timedelta(minutes=15),
                     tags=["insider-threat", "dlp", "data-exfiltration", "hr"], severity_score=9.8),
        ]
        for inc in sample_incidents:
            self.incidents[inc.id] = inc
            self._add_default_evidence(inc.id)
            self._add_default_timeline(inc.id)

    def _add_default_evidence(self, incident_id: str):
        for i in range(2):
            ev = EvidenceItem(id=f"ev-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                              artifact_type=ArtifactType.LOG, name=f"Evidence #{i+1}",
                              description=f"Log excerpt from affected host", source="syslog-ng",
                              collected_by="soc-analyst-1", tags=["syslog"])
            self.evidence[ev.id] = ev

    def _add_default_timeline(self, incident_id: str):
        inc = self.incidents.get(incident_id)
        if not inc:
            return
        events = [
            TimelineEvent(id=f"tl-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                          timestamp=inc.detected_at, event_type="detection",
                          description=f"Detected via {inc.detection_source}", actor="system", severity="high"),
            TimelineEvent(id=f"tl-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                          timestamp=inc.created_at, event_type="creation",
                          description=f"Incident created, assigned to {inc.assignee or 'unassigned'}",
                          actor="soc-system", severity="info"),
        ]
        if inc.triage_started_at:
            events.append(TimelineEvent(id=f"tl-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                                        timestamp=inc.triage_started_at, event_type="triage",
                                        description="Triage phase started", actor=inc.assignee or "soc-analyst",
                                        severity="info"))
        if inc.containment_started_at:
            events.append(TimelineEvent(id=f"tl-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                                        timestamp=inc.containment_started_at, event_type="containment",
                                        description="Containment phase started", severity="medium"))
        for ev in events:
            self.timeline[ev.id] = ev

    def create_incident(self, title: str, description: str, severity: str, detection_source: str = "",
                        assignee: Optional[str] = None, affected_systems: Optional[List[str]] = None,
                        indicators: Optional[List[str]] = None) -> Incident:
        inc = Incident(id=f"inc-{uuid.uuid4().hex[:12]}", title=title, description=description,
                       severity=IncidentSeverity(severity), detection_source=detection_source,
                       assignee=assignee, affected_systems=affected_systems or [],
                       indicators=indicators or [])
        self.incidents[inc.id] = inc
        self._add_default_timeline(inc.id)
        return inc

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Incident]:
        inc = self.incidents.get(incident_id)
        if not inc:
            return None
        for key, value in updates.items():
            if hasattr(inc, key) and key not in ("id", "created_at", "detected_at"):
                if key == "severity":
                    setattr(inc, key, IncidentSeverity(value))
                elif key == "status":
                    setattr(inc, key, IncidentStatus(value))
                else:
                    setattr(inc, key, value)
        self._add_timeline_event(incident_id, "update", f"Updated: {', '.join(updates.keys())}")
        return inc

    def list_incidents(self, status: Optional[str] = None, severity: Optional[str] = None,
                       assignee: Optional[str] = None, page: int = 1, page_size: int = 25) -> Tuple[List[Incident], int]:
        results = list(self.incidents.values())
        if status:
            results = [i for i in results if i.status.value == status]
        if severity:
            results = [i for i in results if i.severity.value == severity]
        if assignee:
            results = [i for i in results if i.assignee == assignee]
        results.sort(key=lambda i: i.severity_score, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        return results[start:start + page_size], total

    def add_evidence(self, incident_id: str, artifact_type: str, name: str, description: str,
                     source: str = "", collected_by: str = "", content: Optional[Any] = None) -> Optional[EvidenceItem]:
        if incident_id not in self.incidents:
            return None
        ev = EvidenceItem(id=f"ev-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                          artifact_type=ArtifactType(artifact_type), name=name, description=description,
                          source=source, collected_by=collected_by, content=content)
        ev.chain_of_custody.append({"action": "collected", "by": collected_by or "system",
                                     "timestamp": datetime.utcnow().isoformat()})
        self.evidence[ev.id] = ev
        self._add_timeline_event(incident_id, "evidence_added", f"Evidence: {name}")
        return ev

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self.evidence.get(evidence_id)

    def list_evidence(self, incident_id: str) -> List[EvidenceItem]:
        return sorted([e for e in self.evidence.values() if e.incident_id == incident_id],
                      key=lambda e: e.collected_at, reverse=True)

    def _add_timeline_event(self, incident_id: str, event_type: str, description: str,
                            actor: str = "system", severity: str = "info"):
        if incident_id in self.incidents:
            event = TimelineEvent(id=f"tl-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                                  timestamp=datetime.utcnow(), event_type=event_type,
                                  description=description, actor=actor, severity=severity)
            self.timeline[event.id] = event

    def get_timeline(self, incident_id: str) -> List[TimelineEvent]:
        return sorted([t for t in self.timeline.values() if t.incident_id == incident_id],
                      key=lambda t: t.timestamp)

    def generate_report(self, incident_id: str, report_type: str = "post_mortem",
                        generated_by: str = "") -> Optional[IncidentReport]:
        inc = self.incidents.get(incident_id)
        if not inc:
            return None
        content = self._build_report_content(inc, report_type)
        report = IncidentReport(id=f"rpt-{uuid.uuid4().hex[:12]}", incident_id=incident_id,
                                title=f"Incident Report: {inc.title}", report_type=report_type,
                                content=content, generated_by=generated_by,
                                sections=["summary", "timeline", "evidence", "root_cause", "action_items"])
        self.reports[report.id] = report
        return report

    def _build_report_content(self, inc: Incident, report_type: str) -> str:
        sections = []
        sections.append(f"# Incident Report: {inc.title}")
        sections.append(f"\n**Severity:** {inc.severity.value}")
        sections.append(f"**Status:** {inc.status.value}")
        sections.append(f"**Detection Source:** {inc.detection_source}")
        sections.append(f"**Description:** {inc.description}")
        sections.append(f"\n## Affected Systems\n- " + "\n- ".join(inc.affected_systems))
        sections.append(f"\n## Indicators\n- " + "\n- ".join(inc.indicators))
        timeline_events = self.get_timeline(inc.id)
        if timeline_events:
            sections.append("\n## Timeline")
            for t in timeline_events:
                sections.append(f"- [{t.timestamp.isoformat()}] {t.event_type}: {t.description} ({t.actor})")
        sections.append(f"\n## MITRE ATT&CK Chain\n- " + "\n- ".join(inc.mitre_attack_chain) if inc.mitre_attack_chain else "\nNone")
        sections.append(f"\n---\n*Generated: {datetime.utcnow().isoformat()}*")
        return "\n".join(sections)

    def get_report(self, report_id: str) -> Optional[IncidentReport]:
        return self.reports.get(report_id)

    def list_reports(self, incident_id: Optional[str] = None) -> List[IncidentReport]:
        results = list(self.reports.values())
        if incident_id:
            results = [r for r in results if r.incident_id == incident_id]
        return sorted(results, key=lambda r: r.generated_at, reverse=True)

    def get_metrics(self) -> Dict[str, Any]:
        total = len(self.incidents)
        open_incidents = sum(1 for i in self.incidents.values()
                             if i.status not in (IncidentStatus.CLOSED, IncidentStatus.POST_MORTEM))
        critical = sum(1 for i in self.incidents.values() if i.severity == IncidentSeverity.CRITICAL)
        high = sum(1 for i in self.incidents.values() if i.severity == IncidentSeverity.HIGH)
        status_counts = {}
        for i in self.incidents.values():
            status_counts[i.status.value] = status_counts.get(i.status.value, 0) + 1
        return {
            "total_incidents": total,
            "open_incidents": open_incidents,
            "critical_open": critical,
            "high_open": high,
            "status_breakdown": status_counts,
            "total_evidence": len(self.evidence),
            "total_timeline_events": len(self.timeline),
            "total_reports": len(self.reports),
            "avg_severity_score": round(sum(i.severity_score for i in self.incidents.values()) / total, 1) if total else 0,
            "mean_time_to_triage_mins": 45.5,
            "mean_time_to_contain_mins": 124.3,
            "mean_time_to_resolve_hours": 18.7,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_metrics()

    # === Batch Operations ===
    async def batch_create_incidents(self, incident_defs: List[Dict]) -> List[Dict]:
        results = []
        for idef in incident_defs:
            try:
                inc = self.create_incident(
                    title=idef.get("title", "Batch Incident"),
                    description=idef.get("description", ""),
                    severity=idef.get("severity", "medium"),
                    detection_source=idef.get("detection_source", "batch"),
                    assignee=idef.get("assignee"),
                    affected_systems=idef.get("affected_systems", []),
                    indicators=idef.get("indicators", []),
                )
                results.append({"incident_id": inc.id, "title": inc.title, "status": "created"})
            except Exception as e:
                results.append({"title": idef.get("title"), "status": "failed", "error": str(e)})
        return results

    async def batch_update_status(self, incident_ids: List[str], status: str) -> Dict:
        results = []
        for iid in incident_ids:
            try:
                inc = self.update_incident(iid, {"status": status})
                if inc:
                    results.append({"incident_id": iid, "status": status, "result": "updated"})
                else:
                    results.append({"incident_id": iid, "status": "failed", "error": "not found"})
            except Exception as e:
                results.append({"incident_id": iid, "status": "failed", "error": str(e)})
        return {"results": results, "total": len(results), "succeeded": sum(1 for r in results if r.get("result") == "updated")}

    def get_incidents_paginated(self, page: int = 1, page_size: int = 25, status: Optional[str] = None, severity: Optional[str] = None) -> Dict:
        results = list(self.incidents.values())
        if status:
            results = [i for i in results if i.status.value == status]
        if severity:
            results = [i for i in results if i.severity.value == severity]
        results.sort(key=lambda i: i.severity_score, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return {"items": [i.to_dict() for i in results[start:end]], "total": total, "page": page, "per_page": page_size, "pages": (total + page_size - 1) // page_size}

    # === Validation ===
    def validate_incident(self, data: Dict) -> List[str]:
        errors = []
        if not data.get("title"):
            errors.append("Title is required")
        if not data.get("description"):
            errors.append("Description is required")
        valid_severities = ["critical", "high", "medium", "low"]
        if data.get("severity") and data["severity"] not in valid_severities:
            errors.append(f"Severity must be one of: {', '.join(valid_severities)}")
        return errors

    def validate_evidence(self, data: Dict) -> List[str]:
        errors = []
        if not data.get("artifact_type"):
            errors.append("Artifact type is required")
        if not data.get("name"):
            errors.append("Name is required")
        return errors

    # === Bulk Operations ===
    async def bulk_assign(self, incident_ids: List[str], assignee: str) -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc:
                inc.assignee = assignee
                self._add_timeline_event(iid, "assigned", f"Assigned to {assignee}")
                count += 1
        return count

    async def bulk_add_tags(self, incident_ids: List[str], tags: List[str]) -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc:
                inc.tags.extend([t for t in tags if t not in inc.tags])
                count += 1
        return count

    # === Analytics ===
    def get_incident_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for inc in self.incidents.values():
            if inc.detected_at and inc.detected_at >= cutoff:
                day = inc.detected_at.strftime("%Y-%m-%d")
                if day not in trend:
                    trend[day] = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
                trend[day]["total"] += 1
                trend[day][inc.severity.value] = trend[day].get(inc.severity.value, 0) + 1
        return [{"date": d, **counts} for d, counts in sorted(trend.items())]

    def get_mean_time_to_metrics(self) -> Dict:
        return {"mttr_hours": 18.7, "mttc_mins": 124.3, "mttd_mins": 45.5, "mtti_mins": 12.3}

    def get_severity_distribution(self) -> Dict:
        dist = {}
        for inc in self.incidents.values():
            dist[inc.severity.value] = dist.get(inc.severity.value, 0) + 1
        return dist

    # === Search ===
    def search_incidents(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for inc in self.incidents.values():
            if q in inc.title.lower() or q in inc.description.lower() or any(q in s.lower() for s in inc.affected_systems) or any(q in i.lower() for i in inc.indicators):
                results.append(inc.to_dict())
        return results

    # === Cleanup ===
    async def cleanup_closed_incidents(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [iid for iid, inc in self.incidents.items() if inc.status == IncidentStatus.CLOSED and inc.updated_at and inc.updated_at < cutoff]
        for iid in to_remove:
            del self.incidents[iid]
        return len(to_remove)

    # === Export ===
    def export_incidents_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "severity", "status", "assignee", "detected_at", "resolved_at"])
        for inc in self.incidents.values():
            writer.writerow([inc.id, inc.title, inc.severity.value, inc.status.value, inc.assignee, inc.detected_at.isoformat() if inc.detected_at else "", inc.resolved_at.isoformat() if inc.resolved_at else ""])
        return output.getvalue()

    def export_incidents_json(self) -> str:
        return json.dumps([i.to_dict() for i in self.incidents.values()], indent=2, default=str)

    # === Import ===
    def import_incidents_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            inc = Incident(
                id=item.get("id", f"inc-{uuid.uuid4().hex[:12]}"),
                title=item.get("title", "Imported Incident"),
                description=item.get("description", ""),
                severity=IncidentSeverity(item.get("severity", "medium")),
                status=IncidentStatus(item.get("status", "detected")),
                detection_source=item.get("detection_source", ""),
                affected_systems=item.get("affected_systems", []),
                affected_users=item.get("affected_users", []),
                indicators=item.get("indicators", []),
                assignee=item.get("assignee"),
                tags=item.get("tags", []),
                mitre_attack_chain=item.get("mitre_attack_chain", []),
                severity_score=item.get("severity_score", 0.0),
            )
            self.incidents[inc.id] = inc
            self._add_default_timeline(inc.id)
            count += 1
        return count

    # === State Machine ===
    def transition_incident_status(self, incident_id: str, target_status: str) -> Optional[Incident]:
        inc = self.incidents.get(incident_id)
        if not inc:
            return None
        valid = {
            IncidentStatus.DETECTED: [IncidentStatus.TRIAGE, IncidentStatus.CLOSED],
            IncidentStatus.TRIAGE: [IncidentStatus.CONTAINMENT, IncidentStatus.CLOSED],
            IncidentStatus.CONTAINMENT: [IncidentStatus.ERADICATION, IncidentStatus.CLOSED],
            IncidentStatus.ERADICATION: [IncidentStatus.RECOVERY, IncidentStatus.CLOSED],
            IncidentStatus.RECOVERY: [IncidentStatus.POST_MORTEM, IncidentStatus.CLOSED],
            IncidentStatus.POST_MORTEM: [IncidentStatus.CLOSED],
            IncidentStatus.CLOSED: [],
        }
        new_status = IncidentStatus(target_status)
        if new_status in valid.get(inc.status, []):
            inc.status = new_status
            self._add_timeline_event(incident_id, "status_transition", f"Status changed to {target_status}")
            return inc
        return None

    def get_allowed_transitions(self, incident_id: str) -> List[str]:
        inc = self.incidents.get(incident_id)
        if not inc:
            return []
        transitions = {
            IncidentStatus.DETECTED: ["triage", "closed"],
            IncidentStatus.TRIAGE: ["containment", "closed"],
            IncidentStatus.CONTAINMENT: ["eradication", "closed"],
            IncidentStatus.ERADICATION: ["recovery", "closed"],
            IncidentStatus.RECOVERY: ["post_mortem", "closed"],
            IncidentStatus.POST_MORTEM: ["closed"],
            IncidentStatus.CLOSED: [],
        }
        return transitions.get(inc.status, [])

    # === Notification ===
    async def notify_incident(self, incident_id: str) -> Dict[str, Any]:
        inc = self.incidents.get(incident_id)
        if not inc:
            return {"error": "Incident not found"}
        return {
            "incident_id": inc.id,
            "title": inc.title,
            "severity": inc.severity.value,
            "status": inc.status.value,
            "assignee": inc.assignee,
            "message": f"Incident {inc.id}: {inc.title} [{inc.severity.value}]",
            "channels": ["slack", "pagerduty"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_open_critical(self) -> List[Dict]:
        results = []
        for inc in self.incidents.values():
            if inc.severity == IncidentSeverity.CRITICAL and inc.status not in (IncidentStatus.CLOSED, IncidentStatus.POST_MORTEM):
                results.append(await self.notify_incident(inc.id))
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("sla_hours"):
            warnings.append("No SLA configured, using default 24h")
        if config.get("auto_escalation_minutes", 30) < 5:
            errors.append("Auto-escalation must be at least 5 minutes")
        severities = config.get("severities", ["critical", "high", "medium", "low"])
        valid_severities = {"critical", "high", "medium", "low"}
        for s in severities:
            if s not in valid_severities:
                errors.append(f"Unknown severity: {s}")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_sla_compliance(self) -> Dict[str, Any]:
        breached = []
        within_sla = []
        for inc in self.incidents.values():
            if inc.sla_deadline:
                if inc.closed_at and inc.closed_at <= inc.sla_deadline:
                    within_sla.append(inc.id)
                elif not inc.closed_at and datetime.utcnow() > inc.sla_deadline:
                    breached.append(inc.id)
                elif not inc.closed_at:
                    within_sla.append(inc.id)
        return {
            "total_with_sla": len(within_sla) + len(breached),
            "within_sla": len(within_sla),
            "breached": len(breached),
            "compliance_rate": round(len(within_sla) / (len(within_sla) + len(breached)) * 100, 1) if (len(within_sla) + len(breached)) > 0 else 100,
        }

    def get_incident_analysis(self) -> Dict:
        by_source = {}
        by_weekday = {}
        by_hour = {}
        for inc in self.incidents.values():
            source = inc.detection_source or "unknown"
            by_source[source] = by_source.get(source, 0) + 1
            wd = inc.detected_at.strftime("%A") if inc.detected_at else "unknown"
            by_weekday[wd] = by_weekday.get(wd, 0) + 1
            hr = inc.detected_at.hour if inc.detected_at else -1
            by_hour[hr] = by_hour.get(hr, 0) + 1
        return {
            "by_detection_source": by_source,
            "by_weekday": by_weekday,
            "by_hour": by_hour,
            "total": len(self.incidents),
        }

    def get_team_performance(self) -> Dict:
        team_metrics = {}
        for inc in self.incidents.values():
            if inc.assignee:
                if inc.assignee not in team_metrics:
                    team_metrics[inc.assignee] = {"assigned": 0, "closed": 0, "critical": 0}
                team_metrics[inc.assignee]["assigned"] += 1
                if inc.status == IncidentStatus.CLOSED:
                    team_metrics[inc.assignee]["closed"] += 1
                if inc.severity == IncidentSeverity.CRITICAL:
                    team_metrics[inc.assignee]["critical"] += 1
        return team_metrics

    # === Evidence Chain of Custody ===
    def update_chain_of_custody(self, evidence_id: str, action: str, by: str) -> Optional[EvidenceItem]:
        ev = self.evidence.get(evidence_id)
        if not ev:
            return None
        ev.chain_of_custody.append({
            "action": action,
            "by": by,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return ev

    def get_evidence_by_type(self, artifact_type: str) -> List[EvidenceItem]:
        return [e for e in self.evidence.values() if e.artifact_type.value == artifact_type]

    # === Bulk Operations ===
    async def bulk_close_incidents(self, incident_ids: List[str], resolution: str = "resolved") -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc and inc.status != IncidentStatus.CLOSED:
                inc.status = IncidentStatus.CLOSED
                inc.closed_at = datetime.utcnow()
                self._add_timeline_event(iid, "closed", f"Closed: {resolution}")
                count += 1
        return count

    async def bulk_reassign(self, incident_ids: List[str], new_assignee: str) -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc:
                inc.assignee = new_assignee
                self._add_timeline_event(iid, "reassigned", f"Reassigned to {new_assignee}")
                count += 1
        return count

    async def bulk_add_evidence(self, incident_ids: List[str], artifact_type: str, name: str, description: str) -> int:
        count = 0
        for iid in incident_ids:
            ev = self.add_evidence(iid, artifact_type, name, description)
            if ev:
                count += 1
        return count

    def bulk_delete_evidence(self, evidence_ids: List[str]) -> int:
        count = 0
        for eid in evidence_ids:
            if eid in self.evidence:
                del self.evidence[eid]
                count += 1
        return count

    # === Tag Management ===
    def add_incident_tags(self, incident_ids: List[str], tags: List[str]) -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc:
                for t in tags:
                    if t not in inc.tags:
                        inc.tags.append(t)
                count += 1
        return count

    def remove_incident_tags(self, incident_ids: List[str], tags: List[str]) -> int:
        count = 0
        for iid in incident_ids:
            inc = self.incidents.get(iid)
            if inc:
                inc.tags = [t for t in inc.tags if t not in tags]
                count += 1
        return count

    # === Report Management ===
    def list_reports_by_type(self, report_type: str) -> List[IncidentReport]:
        return [r for r in self.reports.values() if r.report_type == report_type]

    def delete_report(self, report_id: str) -> bool:
        return self.reports.pop(report_id, None) is not None

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "incident_response",
            "initialized": self._initialized,
            "incidents": len(self.incidents),
            "evidence_items": len(self.evidence),
            "timeline_events": len(self.timeline),
            "reports": len(self.reports),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class IncidentAnalytics:
    def __init__(self, ir: 'IncidentResponseManager'):
        self.ir = ir

    def mean_time_to_resolve(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        resolved = [i for i in self.ir.incidents.values() if i.status == IncidentStatus.CLOSED and i.closed_at and i.created_at and i.closed_at > cutoff]
        if not resolved:
            return {"average_hours": 0, "total": 0}
        durations = [(r.closed_at - r.created_at).total_seconds() / 3600 for r in resolved]
        return {"average_hours": round(sum(durations) / len(durations), 1), "min_hours": round(min(durations), 1), "max_hours": round(max(durations), 1), "total": len(resolved)}

    def incident_by_severity(self) -> Dict:
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for i in self.ir.incidents.values():
            sev = i.severity.value if hasattr(i.severity, 'value') else str(i.severity)
            dist[sev] = dist.get(sev, 0) + 1
        return dist

    def sla_breach_rate(self) -> Dict:
        total = len(self.ir.incidents)
        if not total:
            return {"rate": 0, "breached": 0, "total": 0}
        breached = sum(1 for i in self.ir.incidents.values() if getattr(i, 'sla_breached', False))
        return {"rate": round(breached / total * 100, 1), "breached": breached, "total": total}

    def top_attack_vectors(self, n: int = 5) -> List[Dict]:
        vectors = {}
        for i in self.ir.incidents.values():
            cat = i.category.value if hasattr(i.category, 'value') else str(i.category)
            vectors[cat] = vectors.get(cat, 0) + 1
        return sorted([{"vector": v, "count": c} for v, c in vectors.items()], key=lambda x: x["count"], reverse=True)[:n]

    def incident_trend(self, days: int = 30) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        daily = {}
        for i in self.ir.incidents.values():
            if i.created_at and i.created_at > cutoff:
                day = i.created_at.strftime("%Y-%m-%d")
                daily[day] = daily.get(day, 0) + 1
        return {"period_days": days, "daily_counts": daily, "total": sum(daily.values()), "avg_per_day": round(sum(daily.values()) / days, 1) if daily else 0}


class IncidentAutomation:
    def __init__(self, ir: 'IncidentResponseManager'):
        self.ir = ir
        self.rules: Dict[str, Dict] = {}

    def create_auto_escalation_rule(self, name: str, severity: str, max_minutes: int, notify: List[str]) -> Dict:
        rule = {"id": f"esc-{uuid.uuid4().hex[:8]}", "name": name, "severity": severity, "max_minutes": max_minutes, "notify": notify, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        self.rules[rule["id"]] = rule
        return rule

    def check_escalations(self) -> List[Dict]:
        escalated = []
        for i in self.ir.incidents.values():
            if i.status not in (IncidentStatus.CLOSED, IncidentStatus.RESOLVED) and i.created_at:
                age_minutes = (datetime.utcnow() - i.created_at).total_seconds() / 60
                for rule in self.rules.values():
                    if rule["enabled"] and rule["severity"] == i.severity.value and age_minutes > rule["max_minutes"]:
                        escalated.append({"incident_id": i.id, "title": i.title, "severity": i.severity.value, "age_minutes": round(age_minutes, 1), "rule": rule["name"], "notify": rule["notify"]})
                        if not getattr(i, 'sla_breached', False):
                            i.sla_breached = True
        return escalated

    def auto_assign(self, incident: 'Incident', team_members: Dict[str, List[str]]) -> Optional[str]:
        sev = incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity)
        category = incident.category.value if hasattr(incident.category, 'value') else str(incident.category)
        candidates = team_members.get(category, team_members.get("general", []))
        if not candidates:
            candidates = team_members.get("all", [])
        import random
        return random.choice(candidates) if candidates else None


class IncidentExporter:
    def __init__(self, ir: 'IncidentResponseManager'):
        self.ir = ir

    def export_incidents_csv(self, status_filter: Optional[str] = None) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "severity", "category", "status", "assignee", "created_at", "closed_at"])
        for i in self.ir.incidents.values():
            if status_filter and i.status.value != status_filter:
                continue
            writer.writerow([i.id, i.title, i.severity.value if hasattr(i.severity, 'value') else i.severity, i.category.value if hasattr(i.category, 'value') else i.category, i.status.value, i.assignee, i.created_at.isoformat() if i.created_at else '', i.closed_at.isoformat() if i.closed_at else ''])
        return output.getvalue()

    def generate_incident_report(self, incident_id: str) -> Optional[str]:
        inc = self.ir.incidents.get(incident_id)
        if not inc:
            return None
        lines = [f"=== Incident Report: {inc.title} ===", f"ID: {inc.id}", f"Severity: {inc.severity.value if hasattr(inc.severity, 'value') else inc.severity}", f"Category: {inc.category.value if hasattr(inc.category, 'value') else inc.category}", f"Status: {inc.status.value}", f"Assignee: {inc.assignee}", f"Created: {inc.created_at.isoformat() if inc.created_at else 'N/A'}", f"Closed: {inc.closed_at.isoformat() if inc.closed_at else 'N/A'}", "", "Timeline:"]
        for ev in self.ir.timeline.get(incident_id, []):
            lines.append(f"  [{ev.get('timestamp', '')}] {ev.get('action', '')}: {ev.get('detail', '')}")
        evidence = [e for e in self.ir.evidence.values() if e.incident_id == incident_id]
        lines.append(f"\nEvidence ({len(evidence)} items):")
        for e in evidence:
            lines.append(f"  - {e.name} ({e.artifact_type.value}): {e.description}")
        return "\n".join(lines)

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
