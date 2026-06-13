import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BreachEvent:
    breach_id: str
    status: str
    severity: str
    discovery_date: datetime
    description: str
    data_types_affected: List[str]
    affected_users: int
    root_cause: Optional[str]
    containment_date: Optional[datetime]
    resolution_date: Optional[datetime]
    regulatory_deadline: datetime
    notifications_sent: bool
    created_at: datetime
    updated_at: datetime
    reported_by: str
    affected_systems: List[str]
    remediation_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breach_id": self.breach_id,
            "status": self.status,
            "severity": self.severity,
            "discovery_date": self.discovery_date.isoformat(),
            "description": self.description,
            "data_types_affected": self.data_types_affected,
            "affected_users": self.affected_users,
            "root_cause": self.root_cause,
            "containment_date": self.containment_date.isoformat() if self.containment_date else None,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "regulatory_deadline": self.regulatory_deadline.isoformat(),
            "notifications_sent": self.notifications_sent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "reported_by": self.reported_by,
            "affected_systems": self.affected_systems,
            "remediation_actions": self.remediation_actions,
            "hours_until_deadline": round(
                (self.regulatory_deadline - datetime.utcnow()).total_seconds() / 3600, 1
            ),
        }


NOTIFICATION_TEMPLATES = {
    "data_subject_gdpr": {
        "name": "Data Subject Notification (Art. 34 GDPR)",
        "fields": ["company_name", "dpo_name", "dpo_email", "breach_description",
                   "data_affected", "risks", "mitigation_actions", "regulatory_body"],
        "template": """Subject: Data Breach Notification - {company_name}

Dear Data Subject,

We are writing to inform you of a personal data breach that may affect your personal data.

Date of Discovery: {discovery_date}
Description: {breach_description}
Categories of Data Affected: {data_affected}

Potential Risks: {risks}

Actions Taken: {mitigation_actions}

We recommend you take the following steps:
1. Monitor your accounts for unusual activity
2. Change passwords and enable MFA where available
3. Be alert for phishing attempts

For further information, please contact our Data Protection Officer:
{regulatory_body}
{dpo_name}
{dpo_email}

We sincerely apologize for any inconvenience caused.

{company_name} Data Protection Team""",
    },
    "regulatory_authority_gdpr": {
        "name": "Supervisory Authority Notification (Art. 33 GDPR)",
        "fields": ["company_name", "dpo_name", "dpo_email", "regulatory_name",
                   "breach_description", "data_affected", "affected_count",
                   "likely_consequences", "measures_taken", "regulatory_body"],
        "template": """Subject: Personal Data Breach Notification - {company_name}

To the {regulatory_name},

Pursuant to Article 33 of the General Data Protection Regulation, we hereby notify you of a personal data breach.

1. Description of the Breach:
{breach_description}

2. Categories and Approximate Number of Data Subjects:
Approximately {affected_count} data subjects affected

3. Categories of Personal Data Affected:
{data_affected}

4. Likely Consequences:
{likely_consequences}

5. Measures Taken or Proposed:
{measures_taken}

6. Data Protection Officer:
Name: {dpo_name}
Email: {dpo_email}

This notification is made within 72 hours of becoming aware of the breach.

{company_name}
{regulatory_body}""",
    },
    "internal_incident_report": {
        "name": "Internal Incident Report",
        "fields": ["reporter", "incident_date", "severity", "description",
                   "affected_systems", "impact", "root_cause", "action_items",
                   "lessons_learned"],
        "template": """INTERNAL INCIDENT REPORT

Incident ID: {incident_id}
Reported by: {reporter}
Date: {incident_date}
Severity: {severity}

1. Description:
{description}

2. Affected Systems:
{affected_systems}

3. Business Impact:
{impact}

4. Root Cause Analysis:
{root_cause}

5. Action Items:
{action_items}

6. Lessons Learned:
{lessons_learned}

--- CONFIDENTIAL - INTERNAL USE ONLY ---""",
    },
}


class BreachManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._breaches: Dict[str, BreachEvent] = {}
        self._timelines: Dict[str, List[Dict[str, Any]]] = {}
        self._notifications: Dict[str, List[Dict[str, Any]]] = {}
        self._auto_escalation_config = config.get("auto_escalation", {})
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("BreachManager initialized")

    async def close(self) -> None:
        self._breaches.clear()
        self._timelines.clear()
        self._notifications.clear()
        logger.info("BreachManager closed")

    def report_breach(self, description: str, data_types_affected: List[str],
                      affected_users: int, severity: str = "medium",
                      reported_by: str = "system",
                      affected_systems: Optional[List[str]] = None) -> Dict[str, Any]:
        breach_id = str(uuid.uuid4())
        now = datetime.utcnow()
        deadline_hours = {
            "critical": 24,
            "high": 48,
            "medium": 72,
            "low": 96,
        }
        deadline_hour = deadline_hours.get(severity, 72)

        breach = BreachEvent(
            breach_id=breach_id,
            status="detected",
            severity=severity,
            discovery_date=now,
            description=description,
            data_types_affected=data_types_affected,
            affected_users=affected_users,
            root_cause=None,
            containment_date=None,
            resolution_date=None,
            regulatory_deadline=now + timedelta(hours=deadline_hour),
            notifications_sent=False,
            created_at=now,
            updated_at=now,
            reported_by=reported_by,
            affected_systems=affected_systems or [],
            remediation_actions=[],
        )
        self._breaches[breach_id] = breach
        self._add_timeline_entry(breach_id, "breach_reported", {
            "severity": severity,
            "affected_users": affected_users,
            "data_types": data_types_affected,
        })
        logger.warning(f"Breach {breach_id} reported: {description[:100]}")
        return breach.to_dict()

    def get_breach(self, breach_id: str) -> Optional[BreachEvent]:
        return self._breaches.get(breach_id)

    def update_breach(self, breach_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        breach = self._breaches.get(breach_id)
        if not breach:
            return None
        for key, value in updates.items():
            if hasattr(breach, key) and key not in ("breach_id", "created_at", "regulatory_deadline"):
                setattr(breach, key, value)
        breach.updated_at = datetime.utcnow()
        if "status" in updates:
            self._add_timeline_entry(breach_id, f"status_changed_to_{updates['status']}", updates)
        return breach.to_dict()

    def list_breaches(self, status: Optional[str] = None, severity: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        breaches = list(self._breaches.values())
        if status:
            breaches = [b for b in breaches if b.status == status]
        if severity:
            breaches = [b for b in breaches if b.severity == severity]
        breaches.sort(key=lambda b: b.created_at, reverse=True)
        return [b.to_dict() for b in breaches[offset:offset + limit]]

    def contain_breach(self, breach_id: str, containment_actions: List[str]) -> Optional[Dict[str, Any]]:
        breach = self._breaches.get(breach_id)
        if not breach:
            return None
        breach.status = "contained"
        breach.containment_date = datetime.utcnow()
        breach.remediation_actions = containment_actions
        breach.updated_at = datetime.utcnow()
        self._add_timeline_entry(breach_id, "breach_contained", {
            "containment_date": breach.containment_date.isoformat(),
            "actions": containment_actions,
        })
        logger.info(f"Breach {breach_id} contained")
        return breach.to_dict()

    def resolve_breach(self, breach_id: str, root_cause: str,
                       remediation_completed: List[str]) -> Optional[Dict[str, Any]]:
        breach = self._breaches.get(breach_id)
        if not breach:
            return None
        breach.status = "resolved"
        breach.resolution_date = datetime.utcnow()
        breach.root_cause = root_cause
        breach.remediation_actions = list(set(breach.remediation_actions + remediation_completed))
        breach.updated_at = datetime.utcnow()
        self._add_timeline_entry(breach_id, "breach_resolved", {
            "root_cause": root_cause,
            "resolution_date": breach.resolution_date.isoformat(),
        })
        logger.info(f"Breach {breach_id} resolved. Root cause: {root_cause[:100]}")
        return breach.to_dict()

    def send_notification(self, breach_id: str, template_type: str,
                          template_fields: Dict[str, str]) -> Dict[str, Any]:
        breach = self._breaches.get(breach_id)
        if not breach:
            raise ValueError(f"Breach {breach_id} not found")

        template = NOTIFICATION_TEMPLATES.get(template_type)
        if not template:
            raise ValueError(f"Unknown template type: {template_type}")

        notification_body = template["template"]
        all_fields = dict(template_fields)
        all_fields["discovery_date"] = breach.discovery_date.strftime("%Y-%m-%d %H:%M UTC")
        all_fields["incident_id"] = breach_id

        try:
            notification_body = notification_body.format(**all_fields)
        except KeyError as e:
            logger.error(f"Missing template field: {e}")
            raise ValueError(f"Missing required field: {e}")

        notification = {
            "notification_id": str(uuid.uuid4()),
            "breach_id": breach_id,
            "template_type": template_type,
            "template_name": template["name"],
            "sent_at": datetime.utcnow().isoformat(),
            "recipient_fields": list(template_fields.keys()),
            "body_preview": notification_body[:200],
        }

        if breach_id not in self._notifications:
            self._notifications[breach_id] = []
        self._notifications[breach_id].append(notification)

        self._add_timeline_entry(breach_id, f"notification_sent:{template_type}", {
            "template": template_type,
            "fields": list(template_fields.keys()),
        })

        breach.notifications_sent = True
        breach.updated_at = datetime.utcnow()
        logger.info(f"Notification sent for breach {breach_id}: {template_type}")
        return notification

    def get_timeline(self, breach_id: str) -> List[Dict[str, Any]]:
        return self._timelines.get(breach_id, [])

    def _add_timeline_entry(self, breach_id: str, event_type: str,
                            data: Dict[str, Any]) -> None:
        if breach_id not in self._timelines:
            self._timelines[breach_id] = []
        self._timelines[breach_id].append({
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        })

    def get_notifications(self, breach_id: str) -> List[Dict[str, Any]]:
        return self._notifications.get(breach_id, [])

    def generate_report(self, breach_id: str) -> Dict[str, Any]:
        breach = self._breaches.get(breach_id)
        if not breach:
            raise ValueError(f"Breach {breach_id} not found")
        timeline = self.get_timeline(breach_id)
        notifications = self.get_notifications(breach_id)
        total_time_hours = (
            (breach.resolution_date - breach.discovery_date).total_seconds() / 3600
            if breach.resolution_date else None
        )
        report_data = {
            "report_id": str(uuid.uuid4()),
            "breach_id": breach_id,
            "generated_at": datetime.utcnow().isoformat(),
            "breach_summary": breach.to_dict(),
            "timeline": timeline,
            "notifications_sent": notifications,
            "metrics": {
                "time_to_contain_hours": round(
                    (breach.containment_date - breach.discovery_date).total_seconds() / 3600, 2
                ) if breach.containment_date else None,
                "time_to_resolve_hours": round(total_time_hours, 2) if total_time_hours else None,
                "hours_until_deadline": round(
                    (breach.regulatory_deadline - datetime.utcnow()).total_seconds() / 3600, 1
                ),
                "deadline_met": datetime.utcnow() <= breach.regulatory_deadline,
            },
        }
        return report_data

    def check_escalation(self, breach_id: str) -> Optional[Dict[str, Any]]:
        breach = self._breaches.get(breach_id)
        if not breach:
            return None
        now = datetime.utcnow()
        hours_remaining = (breach.regulatory_deadline - now).total_seconds() / 3600
        if hours_remaining < 0:
            self.update_breach(breach_id, {"status": "overdue"})
            return {"action": "escalate_to_management", "reason": "Regulatory deadline passed"}
        if hours_remaining < 12 and breach.status not in ("contained", "resolved"):
            return {"action": "escalate_to_executive", "reason": f"Only {hours_remaining:.1f}h until deadline"}
        if breach.severity == "critical" and breach.status == "detected" and isinstance(breach.discovery_date, datetime):
            hours_since = (now - breach.discovery_date).total_seconds() / 3600
            if hours_since > 4:
                return {"action": "escalate_to_ciso", "reason": f"Critical breach unresolved after {hours_since:.1f}h"}
        return None

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._breaches)
        status_counts = {}
        severity_counts = {}
        for b in self._breaches.values():
            status_counts[b.status] = status_counts.get(b.status, 0) + 1
            severity_counts[b.severity] = severity_counts.get(b.severity, 0) + 1
        overdue = sum(1 for b in self._breaches.values()
                      if datetime.utcnow() > b.regulatory_deadline and b.status != "resolved")
        total_affected = sum(b.affected_users for b in self._breaches.values())
        avg_resolution_hours = statistics.mean(
            [(b.resolution_date - b.discovery_date).total_seconds() / 3600
             for b in self._breaches.values() if b.resolution_date]
        ) if any(b.resolution_date for b in self._breaches.values()) else None
        return {
            "total_breaches": total,
            "by_status": status_counts,
            "by_severity": severity_counts,
            "overdue_notifications": overdue,
            "total_affected_users": total_affected,
            "avg_resolution_hours": round(avg_resolution_hours, 1) if avg_resolution_hours else None,
            "data_types_tracked": list(set(
                dt for b in self._breaches.values() for dt in b.data_types_affected
            )),
        }
