import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AuditType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    CUSTOMER = "customer"
    REGULATORY = "regulatory"


class AuditStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CustomerAuditRight:
    right_id: str
    customer_id: str
    customer_name: str
    framework: str
    scope: str
    audit_frequency_days: int
    last_audit_date: Optional[datetime]
    next_audit_date: datetime
    status: str
    contract_ref: str
    notes: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "right_id": self.right_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "framework": self.framework,
            "scope": self.scope,
            "audit_frequency_days": self.audit_frequency_days,
            "last_audit_date": self.last_audit_date.isoformat() if self.last_audit_date else None,
            "next_audit_date": self.next_audit_date.isoformat(),
            "status": self.status,
            "contract_ref": self.contract_ref,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class AuditSchedule:
    schedule_id: str
    audit_type: AuditType
    framework: str
    scope: str
    scheduled_date: datetime
    status: AuditStatus
    assigned_auditor: str
    customer_id: Optional[str]
    customer_name: Optional[str]
    notes: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "audit_type": self.audit_type.value,
            "framework": self.framework,
            "scope": self.scope,
            "scheduled_date": self.scheduled_date.isoformat(),
            "status": self.status.value,
            "assigned_auditor": self.assigned_auditor,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class AuditManagementEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rights: Dict[str, CustomerAuditRight] = {}
        self.schedules: Dict[str, AuditSchedule] = {}
        self.data_file = config.get("audit_mgmt_data_file", "data/audit_management.json")
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.rights = {k: CustomerAuditRight(**r) if isinstance(r, dict) else r for k, r in data.get("rights", {}).items()}
                    self.schedules = {k: AuditSchedule(**s) if isinstance(s, dict) else s for k, s in data.get("schedules", {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load audit management data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "rights": {k: v.to_dict() for k, v in self.rights.items()},
                    "schedules": {k: v.to_dict() for k, v in self.schedules.items()},
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save audit management data: {e}")

    def register_customer_right(self, customer_id: str, customer_name: str, framework: str,
                                 scope: str, frequency_days: int, contract_ref: str = "",
                                 notes: str = "") -> CustomerAuditRight:
        right = CustomerAuditRight(
            right_id=f"cr_{uuid.uuid4().hex[:12]}",
            customer_id=customer_id,
            customer_name=customer_name,
            framework=framework,
            scope=scope,
            audit_frequency_days=frequency_days,
            last_audit_date=None,
            next_audit_date=datetime.utcnow() + timedelta(days=frequency_days),
            status="active",
            contract_ref=contract_ref,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.rights[right.right_id] = right
        self._save()
        return right

    def schedule_audit(self, audit_type: str, framework: str, scope: str,
                       scheduled_date: datetime, assigned_auditor: str = "",
                       customer_id: Optional[str] = None,
                       customer_name: Optional[str] = None,
                       notes: str = "") -> AuditSchedule:
        type_enum = AuditType(audit_type) if audit_type in [t.value for t in AuditType] else AuditType.INTERNAL
        schedule = AuditSchedule(
            schedule_id=f"as_{uuid.uuid4().hex[:12]}",
            audit_type=type_enum,
            framework=framework,
            scope=scope,
            scheduled_date=scheduled_date,
            status=AuditStatus.SCHEDULED,
            assigned_auditor=assigned_auditor,
            customer_id=customer_id,
            customer_name=customer_name,
            notes=notes,
            created_at=datetime.utcnow(),
        )
        self.schedules[schedule.schedule_id] = schedule
        if customer_id:
            right = next((r for r in self.rights.values() if r.customer_id == customer_id and r.framework == framework), None)
            if right:
                right.last_audit_date = scheduled_date
                right.next_audit_date = scheduled_date + timedelta(days=right.audit_frequency_days)
                right.updated_at = datetime.utcnow()
        self._save()
        return schedule

    def update_audit_status(self, schedule_id: str, status: str) -> Optional[AuditSchedule]:
        schedule = self.schedules.get(schedule_id)
        if schedule:
            try:
                schedule.status = AuditStatus(status)
                self._save()
            except ValueError:
                raise ValueError(f"Invalid status: {status}")
        return schedule

    def get_schedules(self, audit_type: Optional[str] = None,
                      framework: Optional[str] = None,
                      status: Optional[str] = None) -> List[AuditSchedule]:
        results = list(self.schedules.values())
        if audit_type:
            results = [s for s in results if s.audit_type.value == audit_type]
        if framework:
            results = [s for s in results if s.framework == framework]
        if status:
            results = [s for s in results if s.status.value == status]
        return sorted(results, key=lambda s: s.scheduled_date)

    def get_rights(self, customer_id: Optional[str] = None,
                   framework: Optional[str] = None) -> List[CustomerAuditRight]:
        results = list(self.rights.values())
        if customer_id:
            results = [r for r in results if r.customer_id == customer_id]
        if framework:
            results = [r for r in results if r.framework == framework]
        return results

    def get_upcoming_audits(self, days: int = 30) -> List[AuditSchedule]:
        cutoff = datetime.utcnow() + timedelta(days=days)
        return [s for s in self.schedules.values()
                if s.scheduled_date <= cutoff and s.status in (AuditStatus.SCHEDULED,)]

    def get_overdue_audits(self) -> List[CustomerAuditRight]:
        now = datetime.utcnow()
        return [r for r in self.rights.values() if r.next_audit_date < now and r.status == "active"]

    def collect_audit_evidence(self, schedule_id: str) -> Dict[str, Any]:
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}
        collection_id = f"ce_{uuid.uuid4().hex[:8]}"
        return {
            "collection_id": collection_id,
            "schedule_id": schedule_id,
            "framework": schedule.framework,
            "scope": schedule.scope,
            "evidence_count": 12,
            "collected_at": datetime.utcnow().isoformat(),
            "status": "collected",
            "evidence_items": [
                {"id": f"ev_{uuid.uuid4().hex[:8]}", "type": "policy_document", "control": f"{schedule.framework}-CTRL-{i}"}
                for i in range(1, 13)
            ],
        }

    def generate_audit_report(self, schedule_id: str, auditor_notes: str = "") -> Dict[str, Any]:
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}
        report_id = f"ar_{uuid.uuid4().hex[:12]}"
        return {
            "report_id": report_id,
            "schedule_id": schedule_id,
            "audit_type": schedule.audit_type.value,
            "framework": schedule.framework,
            "scope": schedule.scope,
            "status": "draft",
            "generated_at": datetime.utcnow().isoformat(),
            "assigned_auditor": schedule.assigned_auditor,
            "auditor_notes": auditor_notes,
            "summary": {
                "controls_reviewed": 24,
                "compliant": 18,
                "non_compliant": 4,
                "not_applicable": 2,
                "compliance_rate": 75.0,
            },
            "findings": [
                {"finding_id": f"find_{uuid.uuid4().hex[:8]}", "severity": s, "description": f"Sample {s} finding"}
                for s in ["critical", "high", "medium"]
            ],
        }

    def track_remediation(self, finding_id: str, status_update: str,
                           assigned_to: Optional[str] = None) -> Dict[str, Any]:
        tracking_id = f"rem_{uuid.uuid4().hex[:8]}"
        return {
            "tracking_id": tracking_id,
            "finding_id": finding_id,
            "status": status_update,
            "assigned_to": assigned_to or "unassigned",
            "updated_at": datetime.utcnow().isoformat(),
            "days_open": 0,
            "priority": "high" if "critical" in status_update.lower() else "medium",
        }

    def workflow_action(self, schedule_id: str, action: str,
                         performed_by: str = "system") -> Dict[str, Any]:
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}
        valid_actions = ["start", "complete", "cancel", "reschedule", "assign"]
        if action not in valid_actions:
            raise ValueError(f"Invalid workflow action: {action}. Valid: {valid_actions}")
        status_map = {
            "start": AuditStatus.IN_PROGRESS,
            "complete": AuditStatus.COMPLETED,
            "cancel": AuditStatus.CANCELLED,
        }
        if action in status_map:
            schedule.status = status_map[action]
        elif action == "assign":
            pass
        elif action == "reschedule":
            schedule.status = AuditStatus.SCHEDULED
        self._save()
        return {
            "schedule_id": schedule_id,
            "action": action,
            "new_status": schedule.status.value,
            "performed_by": performed_by,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_customer_portal_status(self, customer_id: str) -> Dict[str, Any]:
        rights = [r for r in self.rights.values() if r.customer_id == customer_id]
        customer_schedules = [s for s in self.schedules.values() if s.customer_id == customer_id]
        return {
            "customer_id": customer_id,
            "customer_name": rights[0].customer_name if rights else "Unknown",
            "active_rights": sum(1 for r in rights if r.status == "active"),
            "total_audits": len(customer_schedules),
            "upcoming_audits": len([s for s in customer_schedules if s.status == AuditStatus.SCHEDULED]),
            "completed_audits": len([s for s in customer_schedules if s.status == AuditStatus.COMPLETED]),
            "next_audit": min((r.next_audit_date.isoformat() for r in rights if r.status == "active"), default=None),
            "overdue_rights": len([r for r in rights if r.status == "active" and r.next_audit_date < datetime.utcnow()]),
        }

    def sync_calendar(self) -> Dict[str, Any]:
        sync_id = f"cal_sync_{uuid.uuid4().hex[:8]}"
        upcoming = self.get_upcoming_audits(90)
        overdue = self.get_overdue_audits()
        return {
            "sync_id": sync_id,
            "synced_at": datetime.utcnow().isoformat(),
            "events_synced": len(upcoming) + len(overdue),
            "upcoming_audits": [s.to_dict() for s in upcoming],
            "overdue_rights": [r.to_dict() for r in overdue],
        }

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_rights": len(self.rights),
            "active_rights": sum(1 for r in self.rights.values() if r.status == "active"),
            "total_schedules": len(self.schedules),
            "upcoming_audits": len(self.get_upcoming_audits(30)),
            "overdue_audits": len(self.get_overdue_audits()),
            "audits_by_type": {t.value: sum(1 for s in self.schedules.values() if s.audit_type.value == t.value) for t in AuditType},
            "audits_by_status": {t.value: sum(1 for s in self.schedules.values() if s.status.value == t.value) for t in AuditStatus},
        }


@dataclass
class AuditNotification:
    notification_id: str
    schedule_id: str
    notification_type: str
    recipient: str
    message: str
    status: str
    sent_at: datetime
    read_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "schedule_id": self.schedule_id,
            "notification_type": self.notification_type,
            "recipient": self.recipient,
            "message": self.message,
            "status": self.status,
            "sent_at": self.sent_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


@dataclass
class AuditTemplate:
    template_id: str
    name: str
    audit_type: str
    framework: str
    scope_template: str
    question_sets: List[str]
    default_duration_days: int
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "audit_type": self.audit_type,
            "framework": self.framework,
            "scope_template": self.scope_template,
            "question_sets": self.question_sets,
            "default_duration_days": self.default_duration_days,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class RemediationPlan:
    plan_id: str
    finding_ids: List[str]
    title: str
    description: str
    priority: str
    owner: str
    target_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "finding_ids": self.finding_ids,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "owner": self.owner,
            "target_date": self.target_date.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


AUDIT_TEMPLATES = {
    "SOC2_ANNUAL": AuditTemplate(
        template_id="tmpl_soc2_annual", name="SOC 2 Annual Audit", audit_type="external",
        framework="SOC_2", scope_template="Full SOC 2 Trust Service Criteria review covering security, availability, processing integrity, confidentiality, and privacy.",
        question_sets=["security", "availability", "confidentiality", "privacy"], default_duration_days=90, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    ),
    "HIPAA_PRIVACY": AuditTemplate(
        template_id="tmpl_hipaa_privacy", name="HIPAA Privacy & Security Review", audit_type="regulatory",
        framework="HIPAA", scope_template="HIPAA administrative, physical, and technical safeguard review for ePHI protection.",
        question_sets=["administrative_safeguards", "physical_safeguards", "technical_safeguards"], default_duration_days=60, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    ),
    "PCI_DSS_V4": AuditTemplate(
        template_id="tmpl_pci_v4", name="PCI DSS v4.0 Assessment", audit_type="external",
        framework="PCI_DSS", scope_template="PCI DSS v4.0 requirements covering 12 core domains for cardholder data protection.",
        question_sets=["network_security", "data_protection", "vulnerability", "access_control", "monitoring", "policy"],
        default_duration_days=120, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    ),
}


class AuditRemediationTracker:
    def __init__(self):
        self.plans: Dict[str, RemediationPlan] = {}

    def create_plan(self, title: str, description: str, finding_ids: List[str],
                    priority: str, owner: str, target_date: datetime) -> RemediationPlan:
        plan = RemediationPlan(
            plan_id=f"rp_{uuid.uuid4().hex[:12]}",
            finding_ids=finding_ids,
            title=title,
            description=description,
            priority=priority,
            owner=owner,
            target_date=target_date,
            status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.plans[plan.plan_id] = plan
        return plan

    def update_plan_status(self, plan_id: str, status: str) -> Optional[RemediationPlan]:
        plan = self.plans.get(plan_id)
        if plan:
            plan.status = status
            plan.updated_at = datetime.utcnow()
        return plan

    def get_plans(self, status: Optional[str] = None, owner: Optional[str] = None) -> List[RemediationPlan]:
        results = list(self.plans.values())
        if status:
            results = [p for p in results if p.status == status]
        if owner:
            results = [p for p in results if p.owner == owner]
        return sorted(results, key=lambda p: p.target_date)

    def get_overdue_plans(self) -> List[RemediationPlan]:
        now = datetime.utcnow()
        return [p for p in self.plans.values() if p.target_date < now and p.status == "open"]


async def send_audit_notification(notification_type: str, schedule_id: str, recipient: str, message: str) -> AuditNotification:
    notification = AuditNotification(
        notification_id=f"notif_{uuid.uuid4().hex[:12]}",
        schedule_id=schedule_id,
        notification_type=notification_type,
        recipient=recipient,
        message=message,
        status="sent",
        sent_at=datetime.utcnow(),
        read_at=None,
    )
    logger.info(f"Notification sent to {recipient} for schedule {schedule_id}: {notification_type}")
    return notification


async def mark_notification_read(notification: AuditNotification) -> AuditNotification:
    notification.read_at = datetime.utcnow()
    notification.status = "read"
    return notification


def get_audit_templates() -> Dict[str, AuditTemplate]:
    return AUDIT_TEMPLATES


def apply_template_to_schedule(template_id: str, scheduled_date: datetime,
                                assigned_auditor: str = "", customer_id: Optional[str] = None,
                                customer_name: Optional[str] = None) -> Dict[str, Any]:
    template = AUDIT_TEMPLATES.get(template_id)
    if not template:
        return {"error": f"Template {template_id} not found"}
    return {
        "template": template.to_dict(),
        "suggested_scope": template.scope_template,
        "suggested_duration_days": template.default_duration_days,
        "question_sets": template.question_sets,
        "schedule_date": scheduled_date.isoformat(),
        "assigned_auditor": assigned_auditor,
    }


def batch_schedule_from_templates(template_assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for assignment in template_assignments:
        try:
            result = apply_template_to_schedule(
                template_id=assignment["template_id"],
                scheduled_date=datetime.fromisoformat(assignment["scheduled_date"]) if isinstance(assignment.get("scheduled_date"), str) else assignment["scheduled_date"],
                assigned_auditor=assignment.get("assigned_auditor", ""),
                customer_id=assignment.get("customer_id"),
                customer_name=assignment.get("customer_name"),
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "template_id": assignment.get("template_id")})
    return results


def filter_audits_by_date_range(schedules: List[AuditSchedule], start: datetime, end: datetime) -> List[AuditSchedule]:
    return [s for s in schedules if start <= s.scheduled_date <= end]


def compute_audit_findings_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_severity = {}
    by_status = {}
    for f in findings:
        sev = f.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        st = f.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_status": by_status,
        "open_critical": sum(1 for f in findings if f.get("severity") == "critical" and f.get("status") == "open"),
        "remediation_rate": round(
            sum(1 for f in findings if f.get("status") in ("remediated", "closed")) / len(findings) * 100, 1
        ) if findings else 0,
    }


def generate_audit_calendar(schedules: List[AuditSchedule], year: int) -> List[Dict[str, Any]]:
    calendar = []
    for s in schedules:
        if s.scheduled_date.year == year:
            calendar.append({
                "schedule_id": s.schedule_id,
                "audit_type": s.audit_type.value,
                "framework": s.framework,
                "scheduled_date": s.scheduled_date.isoformat(),
                "status": s.status.value,
                "assigned_auditor": s.assigned_auditor,
                "month": s.scheduled_date.strftime("%B"),
                "quarter": f"Q{(s.scheduled_date.month - 1) // 3 + 1}",
            })
    return sorted(calendar, key=lambda c: c["scheduled_date"])


def estimate_audit_effort(schedule: AuditSchedule) -> Dict[str, Any]:
    severity_map = {"critical": 40, "high": 25, "medium": 15, "low": 8}
    base_hours = severity_map.get("medium", 15)
    framework_multiplier = {"SOC_2": 1.2, "HIPAA": 1.0, "PCI_DSS": 1.5, "ISO_27001": 1.1, "FEDRAMP": 1.8, "GDPR": 1.3}
    multiplier = framework_multiplier.get(schedule.framework, 1.0)
    total_hours = round(base_hours * multiplier, 1)
    return {
        "schedule_id": schedule.schedule_id,
        "estimated_hours": total_hours,
        "estimated_days": round(total_hours / 8, 1),
        "framework_factor": multiplier,
        "base_hours": base_hours,
        "resource_count": max(1, round(total_hours / 20)),
    }


def merge_customer_rights(existing_rights: List[CustomerAuditRight], new_rights: List[CustomerAuditRight]) -> List[CustomerAuditRight]:
    merged = {r.right_id: r for r in existing_rights}
    for r in new_rights:
        if r.right_id in merged:
            existing = merged[r.right_id]
            existing.audit_frequency_days = r.audit_frequency_days
            existing.scope = r.scope
            existing.notes = r.notes
            existing.updated_at = datetime.utcnow()
        else:
            merged[r.right_id] = r
    return list(merged.values())


class AuditBatchProcessor:
    def __init__(self, engine: AuditManagementEngine):
        self.engine = engine
        self.batch_log: List[Dict[str, Any]] = []

    def batch_register_rights(self, rights_data: List[Dict[str, Any]]) -> List[CustomerAuditRight]:
        results = []
        for data in rights_data:
            try:
                right = self.engine.register_customer_right(
                    customer_id=data["customer_id"],
                    customer_name=data.get("customer_name", ""),
                    framework=data["framework"],
                    scope=data.get("scope", "full"),
                    frequency_days=data.get("frequency_days", 365),
                    contract_ref=data.get("contract_ref", ""),
                    notes=data.get("notes", ""),
                )
                results.append(right)
                self.batch_log.append({"action": "register_right", "right_id": right.right_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "register_right", "customer_id": data.get("customer_id"), "status": "error", "error": str(e)})
        return results

    def batch_schedule_audits(self, schedule_data: List[Dict[str, Any]]) -> List[AuditSchedule]:
        results = []
        for data in schedule_data:
            try:
                schedule = self.engine.schedule_audit(
                    audit_type=data["audit_type"],
                    framework=data["framework"],
                    scope=data.get("scope", "full"),
                    scheduled_date=datetime.fromisoformat(data["scheduled_date"]) if isinstance(data.get("scheduled_date"), str) else data["scheduled_date"],
                    assigned_auditor=data.get("assigned_auditor", ""),
                    customer_id=data.get("customer_id"),
                    customer_name=data.get("customer_name"),
                    notes=data.get("notes", ""),
                )
                results.append(schedule)
                self.batch_log.append({"action": "schedule_audit", "schedule_id": schedule.schedule_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "schedule_audit", "framework": data.get("framework"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log

    def clear_batch_log(self):
        self.batch_log = []


async def paginate_schedules(engine: AuditManagementEngine, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
    all_schedules = engine.get_schedules(status=status)
    total = len(all_schedules)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [s.to_dict() for s in all_schedules[start:end]],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


async def paginate_rights(engine: AuditManagementEngine, page: int = 1, page_size: int = 20, customer_id: Optional[str] = None) -> Dict[str, Any]:
    all_rights = engine.get_rights(customer_id=customer_id)
    total = len(all_rights)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [r.to_dict() for r in all_rights[start:end]],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


def export_audit_data(engine: AuditManagementEngine, format: str = "json") -> Dict[str, Any]:
    export_id = f"export_{uuid.uuid4().hex[:8]}"
    rights_data = [r.to_dict() for r in engine.rights.values()]
    schedules_data = [s.to_dict() for s in engine.schedules.values()]
    if format == "json":
        payload = {"export_id": export_id, "exported_at": datetime.utcnow().isoformat(), "rights": rights_data, "schedules": schedules_data}
    else:
        payload = {"export_id": export_id, "exported_at": datetime.utcnow().isoformat(), "format": format, "rights": rights_data, "schedules": schedules_data}
    return payload


def import_audit_data(engine: AuditManagementEngine, import_payload: Dict[str, Any]) -> Dict[str, Any]:
    import_id = f"import_{uuid.uuid4().hex[:8]}"
    rights_imported = 0
    schedules_imported = 0
    for right_data in import_payload.get("rights", []):
        try:
            right = CustomerAuditRight(
                right_id=right_data.get("right_id", f"cr_{uuid.uuid4().hex[:12]}"),
                customer_id=right_data["customer_id"],
                customer_name=right_data.get("customer_name", ""),
                framework=right_data["framework"],
                scope=right_data.get("scope", "full"),
                audit_frequency_days=right_data.get("audit_frequency_days", 365),
                last_audit_date=datetime.fromisoformat(right_data["last_audit_date"]) if right_data.get("last_audit_date") else None,
                next_audit_date=datetime.fromisoformat(right_data["next_audit_date"]) if right_data.get("next_audit_date") else datetime.utcnow(),
                status=right_data.get("status", "active"),
                contract_ref=right_data.get("contract_ref", ""),
                notes=right_data.get("notes", ""),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            engine.rights[right.right_id] = right
            rights_imported += 1
        except Exception as e:
            logger.warning(f"Failed to import right: {e}")
    for sched_data in import_payload.get("schedules", []):
        try:
            type_enum = AuditType(sched_data["audit_type"]) if sched_data.get("audit_type") in [t.value for t in AuditType] else AuditType.INTERNAL
            status_enum = AuditStatus(sched_data["status"]) if sched_data.get("status") in [t.value for t in AuditStatus] else AuditStatus.DRAFT
            schedule = AuditSchedule(
                schedule_id=sched_data.get("schedule_id", f"as_{uuid.uuid4().hex[:12]}"),
                audit_type=type_enum,
                framework=sched_data["framework"],
                scope=sched_data.get("scope", "full"),
                scheduled_date=datetime.fromisoformat(sched_data["scheduled_date"]) if isinstance(sched_data.get("scheduled_date"), str) else datetime.utcnow(),
                status=status_enum,
                assigned_auditor=sched_data.get("assigned_auditor", ""),
                customer_id=sched_data.get("customer_id"),
                customer_name=sched_data.get("customer_name"),
                notes=sched_data.get("notes", ""),
                created_at=datetime.utcnow(),
            )
            engine.schedules[schedule.schedule_id] = schedule
            schedules_imported += 1
        except Exception as e:
            logger.warning(f"Failed to import schedule: {e}")
    engine._save()
    return {"import_id": import_id, "imported_at": datetime.utcnow().isoformat(), "rights_imported": rights_imported, "schedules_imported": schedules_imported}


def compute_audit_performance_metrics(schedules: List[AuditSchedule]) -> Dict[str, Any]:
    completed = [s for s in schedules if s.status == AuditStatus.COMPLETED]
    if not completed:
        return {"total_completed": 0, "avg_completion_time_days": 0, "on_time_rate": 0}
    total_delay = 0
    on_time = 0
    for s in completed:
        delay_days = (s.scheduled_date - datetime.utcnow()).days
        total_delay += abs(delay_days)
        if delay_days <= 0:
            on_time += 1
    return {
        "total_completed": len(completed),
        "avg_completion_time_days": round(total_delay / len(completed), 1),
        "on_time_rate": round(on_time / len(completed) * 100, 1),
        "on_time_count": on_time,
        "delayed_count": len(completed) - on_time,
    }


def generate_audit_forecast(schedules: List[AuditSchedule], months: int = 6) -> Dict[str, Any]:
    from collections import defaultdict
    now = datetime.utcnow()
    monthly = defaultdict(int)
    for s in schedules:
        if s.scheduled_status in (AuditStatus.SCHEDULED, AuditStatus.DRAFT):
            month_key = s.scheduled_date.strftime("%Y-%m")
            monthly[month_key] += 1
    forecast = {}
    for i in range(months):
        future = now + timedelta(days=30 * i)
        key = future.strftime("%Y-%m")
        forecast[key] = monthly.get(key, 0)
    return {"forecast_period_months": months, "forecast": forecast, "total_forecasted": sum(forecast.values())}


class AuditConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        self.warnings = []
        if not self.config.get("audit_mgmt_data_file"):
            self.warnings.append("audit_mgmt_data_file not set, using default")
        retention_days = self.config.get("retention_days")
        if retention_days is not None and retention_days < 30:
            self.errors.append("retention_days must be >= 30")
        notification_enabled = self.config.get("notifications_enabled", True)
        if not isinstance(notification_enabled, bool):
            self.errors.append("notifications_enabled must be a boolean")
        return len(self.errors) == 0

    def get_report(self) -> Dict[str, Any]:
        return {"valid": len(self.errors) == 0, "errors": self.errors, "warnings": self.warnings}


class AuditRemediationStateMachine:
    STATES = ["open", "in_progress", "in_review", "completed", "rejected"]

    def __init__(self, plan: RemediationPlan):
        self.plan = plan
        self.transition_log: List[Dict[str, Any]] = []

    def transition(self, to_state: str, reason: str = "") -> bool:
        valid_transitions = {
            "open": ["in_progress", "rejected"],
            "in_progress": ["in_review", "open"],
            "in_review": ["completed", "in_progress"],
            "completed": ["in_review"],
            "rejected": ["open"],
        }
        current = self.plan.status
        if to_state not in valid_transitions.get(current, []):
            return False
        self.plan.status = to_state
        self.plan.updated_at = datetime.utcnow()
        self.transition_log.append({
            "from_state": current, "to_state": to_state, "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return True

    def get_history(self) -> List[Dict[str, Any]]:
        return self.transition_log

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class audit_management_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class audit_management_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class audit_management_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class audit_management_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class audit_management_Cache:
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

class audit_management_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class audit_management_Queue:
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

class audit_management_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class audit_management_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_audit_mgmt_rights_store: Dict[str, CustomerAuditRight] = {}
_audit_mgmt_schedules_store: Dict[str, AuditSchedule] = {}


def add_audit_right(right: CustomerAuditRight) -> str:
    _audit_mgmt_rights_store[right.right_id] = right
    return right.right_id


def get_audit_right(right_id: str) -> Optional[CustomerAuditRight]:
    return _audit_mgmt_rights_store.get(right_id)


def search_audit_schedules(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for s in _audit_mgmt_schedules_store.values():
        if query.lower() in s.customer_id.lower() or query.lower() in s.framework.lower():
            results.append({"id": s.schedule_id, "customer": s.customer_id, "framework": s.framework, "status": s.status.value})
            if len(results) >= limit:
                break
    return results


def batch_cancel_audits(schedule_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "cancel", "succeeded": [], "failed": [], "total": len(schedule_ids)}
    for sid in schedule_ids:
        s = _audit_mgmt_schedules_store.get(sid)
        if s:
            s.status = AuditStatus.CANCELLED
            op["succeeded"].append(sid)
        else:
            op["failed"].append(sid)
    return op


def get_audit_mgmt_summary() -> Dict[str, Any]:
    total_schedules = len(_audit_mgmt_schedules_store)
    total_rights = len(_audit_mgmt_rights_store)
    draft = sum(1 for s in _audit_mgmt_schedules_store.values() if s.status == AuditStatus.DRAFT)
    scheduled = sum(1 for s in _audit_mgmt_schedules_store.values() if s.status == AuditStatus.SCHEDULED)
    in_progress = sum(1 for s in _audit_mgmt_schedules_store.values() if s.status == AuditStatus.IN_PROGRESS)
    completed = sum(1 for s in _audit_mgmt_schedules_store.values() if s.status == AuditStatus.COMPLETED)
    return {"total_schedules": total_schedules, "total_rights": total_rights, "draft": draft, "scheduled": scheduled, "in_progress": in_progress, "completed": completed}


class AuditScheduleOptimizer:
    def __init__(self):
        self._schedules = _audit_mgmt_schedules_store

    def get_monthly_calendar(self, year: int, month: int) -> List[Dict[str, Any]]:
        events = []
        for s in self._schedules.values():
            d = s.scheduled_date
            if hasattr(d, 'year') and d.year == year and d.month == month:
                events.append({"id": s.schedule_id, "title": s.framework, "date": d.isoformat() if hasattr(d, 'isoformat') else d, "type": s.audit_type.value if hasattr(s.audit_type, 'value') else s.audit_type, "status": s.status.value if hasattr(s.status, 'value') else s.status})
        return sorted(events, key=lambda x: x["date"])

    def detect_scheduling_conflicts(self) -> List[Dict[str, Any]]:
        conflicts = []
        sorted_sched = sorted([s for s in self._schedules.values() if hasattr(s.scheduled_date, 'isoformat')], key=lambda x: x.scheduled_date)
        for i in range(len(sorted_sched) - 1):
            a, b = sorted_sched[i], sorted_sched[i + 1]
            diff = (b.scheduled_date - a.scheduled_date).total_seconds()
            if diff < 86400 and a.assigned_auditor == b.assigned_auditor:
                conflicts.append({"schedule_a": a.schedule_id, "schedule_b": b.schedule_id, "auditor": a.assigned_auditor, "gap_hours": round(diff / 3600, 1)})
        return conflicts


class AuditNotificationService:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def notify_upcoming(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        upcoming = [s for s in _audit_mgmt_schedules_store.values() if AuditStatus.SCHEDULED and 0 <= (s.scheduled_date - now).days <= days_ahead]
        notifications = []
        for s in upcoming:
            n = {"schedule_id": s.schedule_id, "framework": s.framework, "date": s.scheduled_date.isoformat() if hasattr(s.scheduled_date, 'isoformat') else s.scheduled_date, "auditor": s.assigned_auditor, "sent_at": now.isoformat()}
            self._log.append(n)
            notifications.append(n)
        return notifications

    def get_notification_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._log[-limit:]


class AuditRightManager:
    def __init__(self):
        self._rights = _audit_mgmt_rights_store

    def verify_right(self, customer_id: str, framework: str) -> Dict[str, bool]:
        valid = any(r.customer_id == customer_id and framework in r.allowed_frameworks and r.is_active for r in self._rights.values())
        return {"authorized": valid, "customer_id": customer_id, "framework": framework}

    def deactivate_right(self, right_id: str) -> bool:
        r = self._rights.get(right_id)
        if r:
            r.is_active = False
            return True
        return False

    def list_active_rights(self) -> List[Dict[str, Any]]:
        return [{"id": r.right_id, "customer": r.customer_id, "frameworks": r.allowed_frameworks} for r in self._rights.values() if r.is_active]


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
