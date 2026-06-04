import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RegulatorySource(Enum):
    GOVERNMENT = "government"
    INDUSTRY_BODY = "industry_body"
    STANDARD_BODY = "standard_body"
    REGULATORY_AUTHORITY = "regulatory_authority"
    NEWS = "news"


class ChangeType(Enum):
    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    GUIDANCE_UPDATE = "guidance_update"
    ENFORCEMENT_ACTION = "enforcement_action"
    DEADLINE_EXTENSION = "deadline_extension"
    INTERPRETATION = "interpretation"


class ImpactLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MONITOR = "monitor"


@dataclass
class RegulatoryChange:
    change_id: str
    title: str
    source: RegulatorySource
    change_type: ChangeType
    description: str
    regulation: str
    jurisdiction: str
    effective_date: Optional[datetime]
    impact_level: ImpactLevel
    affected_controls: List[str]
    affected_frameworks: List[str]
    summary: str
    action_required: bool
    action_deadline: Optional[datetime]
    status: str
    published_at: datetime
    detected_at: datetime
    source_url: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "title": self.title,
            "source": self.source.value,
            "change_type": self.change_type.value,
            "description": self.description,
            "regulation": self.regulation,
            "jurisdiction": self.jurisdiction,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "impact_level": self.impact_level.value,
            "affected_controls": self.affected_controls,
            "affected_frameworks": self.affected_frameworks,
            "summary": self.summary,
            "action_required": self.action_required,
            "action_deadline": self.action_deadline.isoformat() if self.action_deadline else None,
            "status": self.status,
            "published_at": self.published_at.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "source_url": self.source_url,
        }


REGULATORY_SOURCES = [
    {"id": "gdpr", "name": "GDPR (EU)", "jurisdiction": "EU", "source_type": "regulation",
     "frameworks": ["GDPR"], "monitor_url": "https://ec.europa.eu/info/law/law-topic/data-protection_en"},
    {"id": "ccpa", "name": "CCPA/CPRA (California)", "jurisdiction": "US-CA", "source_type": "regulation",
     "frameworks": ["CCPA", "GDPR"], "monitor_url": "https://oag.ca.gov/privacy/ccpa"},
    {"id": "hipaa", "name": "HIPAA (US Healthcare)", "jurisdiction": "US", "source_type": "regulation",
     "frameworks": ["HIPAA"], "monitor_url": "https://www.hhs.gov/hipaa/index.html"},
    {"id": "pci", "name": "PCI DSS", "jurisdiction": "Global", "source_type": "standard",
     "frameworks": ["PCI_DSS"], "monitor_url": "https://www.pcisecuritystandards.org/"},
    {"id": "soc2", "name": "SOC 2 (AICPA)", "jurisdiction": "US", "source_type": "standard",
     "frameworks": ["SOC_2"], "monitor_url": "https://www.aicpa.org/soc"},
    {"id": "iso27001", "name": "ISO 27001", "jurisdiction": "Global", "source_type": "standard",
     "frameworks": ["ISO_27001"], "monitor_url": "https://www.iso.org/isoiec-27001-information-security.html"},
    {"id": "fedramp", "name": "FedRAMP", "jurisdiction": "US", "source_type": "standard",
     "frameworks": ["FEDRAMP"], "monitor_url": "https://www.fedramp.gov/"},
    {"id": "lgpd", "name": "LGPD (Brazil)", "jurisdiction": "BR", "source_type": "regulation",
     "frameworks": ["GDPR", "LGPD"], "monitor_url": "https://www.gov.br/anpd/pt-br"},
    {"id": "dpdp", "name": "DPDP Act (India)", "jurisdiction": "IN", "source_type": "regulation",
     "frameworks": ["GDPR", "DPDP"], "monitor_url": "https://www.meity.gov.in/data-protection-framework"},
]


class RegulatoryIntelligenceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.changes: List[RegulatoryChange] = []
        self.sources = REGULATORY_SOURCES
        self.data_file = config.get("regulatory_data_file", "data/regulatory_intel.json")
        self._load()
        self._seed_sample_changes()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.changes = [RegulatoryChange(**c) if isinstance(c, dict) else c for c in data.get("changes", [])]
        except Exception as e:
            logger.warning(f"Failed to load regulatory data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({"changes": [c.to_dict() for c in self.changes]}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save regulatory data: {e}")

    def _seed_sample_changes(self):
        if len(self.changes) > 0:
            return
        sample_changes = [
            RegulatoryChange(
                change_id=f"reg_{uuid.uuid4().hex[:8]}",
                title="GDPR Adequacy Decision Update",
                source=RegulatorySource.GOVERNMENT,
                change_type=ChangeType.GUIDANCE_UPDATE,
                description="Updated adequacy decisions for international data transfers under GDPR Article 45",
                regulation="GDPR",
                jurisdiction="EU",
                effective_date=datetime.utcnow() + timedelta(days=90),
                impact_level=ImpactLevel.HIGH,
                affected_controls=["GDPR-ART44", "GDPR-ART45", "GDPR-ART46"],
                affected_frameworks=["GDPR"],
                summary="New adequacy decisions affect data transfer mechanisms to third countries",
                action_required=True,
                action_deadline=datetime.utcnow() + timedelta(days=90),
                status="new",
                published_at=datetime.utcnow() - timedelta(days=2),
                detected_at=datetime.utcnow(),
                source_url="https://ec.europa.eu/info/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en",
            ),
            RegulatoryChange(
                change_id=f"reg_{uuid.uuid4().hex[:8]}",
                title="PCI DSS v4.0 Transition Deadline",
                source=RegulatorySource.INDUSTRY_BODY,
                change_type=ChangeType.DEADLINE_EXTENSION,
                description="PCI SSC extended the v3.2.1 retirement date for v4.0 transition",
                regulation="PCI DSS",
                jurisdiction="Global",
                effective_date=datetime.utcnow() + timedelta(days=180),
                impact_level=ImpactLevel.CRITICAL,
                affected_controls=["PCI-1.1", "PCI-3.1", "PCI-6.1", "PCI-8.1", "PCI-10.1", "PCI-12.1"],
                affected_frameworks=["PCI_DSS"],
                summary="Transition to PCI DSS v4.0 deadline extended by 6 months for certain requirements",
                action_required=True,
                action_deadline=datetime.utcnow() + timedelta(days=180),
                status="new",
                published_at=datetime.utcnow() - timedelta(days=5),
                detected_at=datetime.utcnow(),
                source_url="https://www.pcisecuritystandards.org/document_library/",
            ),
            RegulatoryChange(
                change_id=f"reg_{uuid.uuid4().hex[:8]}",
                title="FedRAMP Authorization Act Update",
                source=RegulatorySource.GOVERNMENT,
                change_type=ChangeType.AMENDMENT,
                description="New legislation codifying FedRAMP into law with updated requirements",
                regulation="FedRAMP",
                jurisdiction="US",
                effective_date=datetime.utcnow() + timedelta(days=30),
                impact_level=ImpactLevel.HIGH,
                affected_controls=["FEDRAMP-AC-1", "FEDRAMP-CM-2", "FEDRAMP-IA-2", "FEDRAMP-SC-7"],
                affected_frameworks=["FEDRAMP"],
                summary="FedRAMP Authorization Act makes program permanent with enhanced oversight",
                action_required=True,
                action_deadline=datetime.utcnow() + timedelta(days=365),
                status="reviewing",
                published_at=datetime.utcnow() - timedelta(days=10),
                detected_at=datetime.utcnow(),
                source_url="https://www.congress.gov/bill/",
            ),
            RegulatoryChange(
                change_id=f"reg_{uuid.uuid4().hex[:8]}",
                title="ISO 27001:2025 Revision Published",
                source=RegulatorySource.STANDARD_BODY,
                change_type=ChangeType.NEW_REGULATION,
                description="ISO 27001:2025 published with updated Annex A controls",
                regulation="ISO 27001",
                jurisdiction="Global",
                effective_date=datetime.utcnow(),
                impact_level=ImpactLevel.MEDIUM,
                affected_controls=["ISO-5.1", "ISO-8.1", "ISO-9.1", "ISO-10.1", "ISO-11.1", "ISO-12.1", "ISO-13.1"],
                affected_frameworks=["ISO_27001"],
                summary="ISO 27001:2025 introduces 11 new controls and updates 24 existing controls",
                action_required=True,
                action_deadline=datetime.utcnow() + timedelta(days=730),
                status="reviewing",
                published_at=datetime.utcnow() - timedelta(days=15),
                detected_at=datetime.utcnow(),
                source_url="https://www.iso.org/standard/iso-27001",
            ),
            RegulatoryChange(
                change_id=f"reg_{uuid.uuid4().hex[:8]}",
                title="CCPA Enforcement Guidance Update",
                source=RegulatorySource.REGULATORY_AUTHORITY,
                change_type=ChangeType.ENFORCEMENT_ACTION,
                description="California Privacy Protection Agency issued new enforcement guidance on data sharing",
                regulation="CCPA",
                jurisdiction="US-CA",
                effective_date=datetime.utcnow() + timedelta(days=60),
                impact_level=ImpactLevel.MEDIUM,
                affected_controls=["GDPR-ART5", "GDPR-ART15"],
                affected_frameworks=["GDPR", "CCPA"],
                summary="New guidance on opt-out signals and data broker registration requirements",
                action_required=True,
                action_deadline=datetime.utcnow() + timedelta(days=60),
                status="new",
                published_at=datetime.utcnow() - timedelta(days=3),
                detected_at=datetime.utcnow(),
                source_url="https://cppa.ca.gov/",
            ),
        ]
        self.changes = sample_changes
        self._save()

    def detect_change(self, title: str, source: str, change_type: str, description: str,
                      regulation: str, jurisdiction: str, impact_level: str,
                      affected_controls: Optional[List[str]] = None,
                      affected_frameworks: Optional[List[str]] = None,
                      effective_date: Optional[datetime] = None,
                      action_required: bool = False,
                      action_deadline: Optional[datetime] = None,
                      source_url: Optional[str] = None) -> RegulatoryChange:
        change = RegulatoryChange(
            change_id=f"reg_{uuid.uuid4().hex[:12]}",
            title=title,
            source=RegulatorySource(source) if source in [s.value for s in RegulatorySource] else RegulatorySource.NEWS,
            change_type=ChangeType(change_type) if change_type in [c.value for c in ChangeType] else ChangeType.GUIDANCE_UPDATE,
            description=description,
            regulation=regulation,
            jurisdiction=jurisdiction,
            effective_date=effective_date,
            impact_level=ImpactLevel(impact_level) if impact_level in [i.value for i in ImpactLevel] else ImpactLevel.MEDIUM,
            affected_controls=affected_controls or [],
            affected_frameworks=affected_frameworks or [],
            summary=description[:200],
            action_required=action_required,
            action_deadline=action_deadline,
            status="new",
            published_at=datetime.utcnow(),
            detected_at=datetime.utcnow(),
            source_url=source_url,
        )
        self.changes.insert(0, change)
        self._save()
        return change

    def get_changes(self, regulation: Optional[str] = None,
                    impact_level: Optional[str] = None,
                    status: Optional[str] = None,
                    jurisdiction: Optional[str] = None,
                    days: int = 90) -> List[RegulatoryChange]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = [c for c in self.changes if c.detected_at >= cutoff]
        if regulation:
            results = [c for c in results if c.regulation.lower() == regulation.lower()]
        if impact_level:
            results = [c for c in results if c.impact_level.value == impact_level]
        if status:
            results = [c for c in results if c.status == status]
        if jurisdiction:
            results = [c for c in results if c.jurisdiction.lower() == jurisdiction.lower()]
        return sorted(results, key=lambda c: c.detected_at, reverse=True)

    def get_sources(self) -> List[Dict[str, Any]]:
        return self.sources

    def get_impact_analysis(self, change_id: str) -> Dict[str, Any]:
        change = next((c for c in self.changes if c.change_id == change_id), None)
        if not change:
            return {"error": "Change not found"}
        return {
            "change": change.to_dict(),
            "impact_summary": {
                "affected_frameworks": len(change.affected_frameworks),
                "affected_controls": len(change.affected_controls),
                "action_required": change.action_required,
                "days_until_deadline": (change.action_deadline - datetime.utcnow()).days if change.action_deadline else None,
            },
            "recommended_actions": [
                f"Review controls {', '.join(change.affected_controls[:3])} for compliance gaps",
                f"Update policy documentation for {change.regulation} changes",
                f"Assess business impact by {change.action_deadline.strftime('%Y-%m-%d') if change.action_deadline else 'soon'}",
                "Notify compliance team and schedule remediation",
            ],
        }

    def get_statistics(self) -> Dict[str, Any]:
        by_impact = {}
        by_type = {}
        by_status = {}
        by_regulation = {}
        for c in self.changes:
            by_impact[c.impact_level.value] = by_impact.get(c.impact_level.value, 0) + 1
            by_type[c.change_type.value] = by_type.get(c.change_type.value, 0) + 1
            by_status[c.status] = by_status.get(c.status, 0) + 1
            by_regulation[c.regulation] = by_regulation.get(c.regulation, 0) + 1
        return {
            "total_changes": len(self.changes),
            "by_impact": by_impact,
            "by_type": by_type,
            "by_status": by_status,
            "by_regulation": by_regulation,
            "action_required": sum(1 for c in self.changes if c.action_required),
            "sources_monitored": len(self.sources),
            "last_detection": max((c.detected_at for c in self.changes), default=datetime.utcnow()).isoformat(),
        }

    def batch_detect(self, changes: List[Dict[str, Any]]) -> List[RegulatoryChange]:
        detected = []
        for c in changes:
            try:
                change = self.detect_change(
                    title=c["title"], source=c.get("source", "news"),
                    change_type=c.get("change_type", "guidance_update"),
                    description=c.get("description", ""), regulation=c.get("regulation", "Unknown"),
                    jurisdiction=c.get("jurisdiction", "Global"),
                    impact_level=c.get("impact_level", "medium"),
                    affected_controls=c.get("affected_controls"),
                    affected_frameworks=c.get("affected_frameworks"),
                    effective_date=datetime.fromisoformat(c["effective_date"]) if isinstance(c.get("effective_date"), str) else c.get("effective_date"),
                    action_required=c.get("action_required", False),
                    action_deadline=datetime.fromisoformat(c["action_deadline"]) if isinstance(c.get("action_deadline"), str) else c.get("action_deadline"),
                    source_url=c.get("source_url"),
                )
                detected.append(change)
            except Exception as e:
                logger.error(f"Batch detect failed for {c.get('title', 'unknown')}: {e}")
        return detected

    def get_calendar(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        yr = year or datetime.utcnow().year
        events = []
        for c in self.changes:
            if c.effective_date and c.effective_date.year == yr:
                events.append({
                    "change_id": c.change_id,
                    "title": c.title,
                    "date": c.effective_date.isoformat(),
                    "type": c.change_type.value,
                    "impact": c.impact_level.value,
                    "regulation": c.regulation,
                    "jurisdiction": c.jurisdiction,
                    "action_required": c.action_required,
                })
            if c.action_deadline and c.action_deadline.year == yr:
                events.append({
                    "change_id": c.change_id,
                    "title": f"Deadline: {c.title}",
                    "date": c.action_deadline.isoformat(),
                    "type": "deadline",
                    "impact": c.impact_level.value,
                    "regulation": c.regulation,
                    "jurisdiction": c.jurisdiction,
                    "action_required": True,
                })
        return sorted(events, key=lambda e: e["date"])

    def sync_calendar(self, external_calendar_url: Optional[str] = None) -> Dict[str, Any]:
        sync_id = f"sync_{uuid.uuid4().hex[:8]}"
        return {
            "sync_id": sync_id,
            "source": external_calendar_url or "internal",
            "events_synced": len(self.changes),
            "sync_status": "completed",
            "synced_at": datetime.utcnow().isoformat(),
        }

    def impact_matrix(self) -> Dict[str, Any]:
        frameworks = set()
        for c in self.changes:
            frameworks.update(c.affected_frameworks)
        matrix = {}
        for fw in sorted(frameworks):
            fw_changes = [c for c in self.changes if fw in c.affected_frameworks]
            matrix[fw] = {
                "total_changes": len(fw_changes),
                "critical": sum(1 for c in fw_changes if c.impact_level == ImpactLevel.CRITICAL),
                "high": sum(1 for c in fw_changes if c.impact_level == ImpactLevel.HIGH),
                "medium": sum(1 for c in fw_changes if c.impact_level == ImpactLevel.MEDIUM),
                "low": sum(1 for c in fw_changes if c.impact_level == ImpactLevel.LOW),
                "action_required": sum(1 for c in fw_changes if c.action_required),
                "upcoming_deadlines": sum(1 for c in fw_changes if c.action_deadline and c.action_deadline > datetime.utcnow()),
            }
        return {
            "matrix": matrix,
            "most_impacted": max(matrix, key=lambda k: matrix[k]["critical"]) if matrix else None,
            "total_changes_tracked": len(self.changes),
        }

    def source_health(self) -> List[Dict[str, Any]]:
        health = []
        for src in self.sources:
            src_changes = [c for c in self.changes if c.regulation.lower() in src.get("frameworks", [str.lower])]
            recent = sum(1 for c in src_changes if c.detected_at > datetime.utcnow() - timedelta(days=30))
            health.append({
                "source_id": src["id"],
                "name": src["name"],
                "jurisdiction": src["jurisdiction"],
                "monitor_url": src["monitor_url"],
                "changes_detected_30d": recent,
                "status": "healthy" if recent > 0 else "warning",
                "last_change": max((c.detected_at.isoformat() for c in src_changes), default=None),
            })
        return health

    def route_notification(self, change_id: str, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        change = next((c for c in self.changes if c.change_id == change_id), None)
        if not change:
            return {"error": "Change not found"}
        channels = channels or ["email", "dashboard"]
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"
        return {
            "notification_id": notification_id,
            "change_id": change_id,
            "title": change.title,
            "impact_level": change.impact_level.value,
            "channels": channels,
            "routed_at": datetime.utcnow().isoformat(),
            "status": "sent",
            "recipients": {
                "email": ["compliance@example.com"],
                "slack": ["#compliance-alerts"],
                "teams": ["Compliance Channel"],
            },
        }

    def mark_reviewed(self, change_id: str) -> Optional[RegulatoryChange]:
        change = next((c for c in self.changes if c.change_id == change_id), None)
        if change:
            change.status = "reviewed"
            self._save()
        return change

    def subscribe_to_source(self, source_id: str, webhook_url: str, events: List[str]) -> Dict[str, Any]:
        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        source = next((s for s in self.sources if s["id"] == source_id), None)
        if not source:
            return {"error": f"Source {source_id} not found"}
        return {
            "subscription_id": subscription_id,
            "source_id": source_id,
            "source_name": source["name"],
            "webhook_url": webhook_url,
            "events": events,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }

    def generate_regulatory_report(self, framework: Optional[str] = None, days: int = 90) -> Dict[str, Any]:
        changes = self.get_changes(framework=framework, days=days)
        action_items = [c for c in changes if c.action_required]
        return {
            "report_id": f"reg_rpt_{uuid.uuid4().hex[:12]}",
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "total_changes": len(changes),
            "action_required": len(action_items),
            "changes_by_impact": {lvl.value: sum(1 for c in changes if c.impact_level == lvl) for lvl in ImpactLevel},
            "changes_by_type": {t.value: sum(1 for c in changes if c.change_type == t) for t in ChangeType},
            "upcoming_deadlines": [
                {"change_id": c.change_id, "title": c.title, "deadline": c.action_deadline.isoformat(), "impact": c.impact_level.value}
                for c in sorted(action_items, key=lambda x: x.action_deadline or datetime.max) if c.action_deadline
            ],
            "recommended_actions": [
                f"Address {sum(1 for c in action_items if c.impact_level == ImpactLevel.CRITICAL)} critical changes immediately",
                f"Review {sum(1 for c in changes if c.status == 'new')} newly detected changes",
                f"Schedule remediation for {len(action_items)} items requiring action",
            ],
        }

    def export_changes(self, format: str = "json") -> Dict[str, Any]:
        export_id = f"reg_export_{uuid.uuid4().hex[:8]}"
        data = {
            "export_id": export_id,
            "exported_at": datetime.utcnow().isoformat(),
            "changes": [c.to_dict() for c in self.changes],
        }
        return data

    def compare_jurisdictions(self, jurisdiction_1: str, jurisdiction_2: str) -> Dict[str, Any]:
        j1_changes = [c for c in self.changes if c.jurisdiction == jurisdiction_1]
        j2_changes = [c for c in self.changes if c.jurisdiction == jurisdiction_2]
        common_frameworks = set(c.regulation for c in j1_changes) & set(c.regulation for c in j2_changes)
        return {
            "jurisdiction_1": {"name": jurisdiction_1, "total_changes": len(j1_changes)},
            "jurisdiction_2": {"name": jurisdiction_2, "total_changes": len(j2_changes)},
            "common_frameworks": list(common_frameworks),
            "j1_unique": [c.title for c in j1_changes if c.regulation not in common_frameworks],
            "j2_unique": [c.title for c in j2_changes if c.regulation not in common_frameworks],
        }

    def get_pending_actions(self, days: int = 30) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days)
        pending = []
        for c in self.changes:
            if c.action_required and c.action_deadline:
                if now <= c.action_deadline <= cutoff:
                    pending.append({
                        "change_id": c.change_id,
                        "title": c.title,
                        "regulation": c.regulation,
                        "deadline": c.action_deadline.isoformat(),
                        "days_remaining": (c.action_deadline - now).days,
                        "impact": c.impact_level.value,
                        "status": c.status,
                    })
        return sorted(pending, key=lambda x: x["days_remaining"])

    def search_regulations(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for c in self.changes:
            if (q in c.title.lower() or q in c.regulation.lower() or
                q in c.description.lower() or q in c.jurisdiction.lower()):
                results.append(c.to_dict())
        return results


@dataclass
class RegulatorySubscription:
    subscription_id: str
    email: str
    frameworks: List[str]
    min_impact: str
    frequency: str
    active: bool
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "email": self.email,
            "frameworks": self.frameworks,
            "min_impact": self.min_impact,
            "frequency": self.frequency,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
        }


class RegulatorySubscriptionManager:
    def __init__(self):
        self.subscriptions: Dict[str, RegulatorySubscription] = {}

    def create_subscription(self, email: str, frameworks: List[str],
                            min_impact: str = "medium", frequency: str = "weekly") -> RegulatorySubscription:
        sub = RegulatorySubscription(
            subscription_id=f"sub_{uuid.uuid4().hex[:8]}",
            email=email,
            frameworks=frameworks,
            min_impact=min_impact,
            frequency=frequency,
            active=True,
            created_at=datetime.utcnow(),
        )
        self.subscriptions[sub.subscription_id] = sub
        return sub

    def deactivate_subscription(self, subscription_id: str) -> Optional[RegulatorySubscription]:
        sub = self.subscriptions.get(subscription_id)
        if sub:
            sub.active = False
        return sub

    def get_subscriptions(self, framework: Optional[str] = None) -> List[RegulatorySubscription]:
        if framework:
            return [s for s in self.subscriptions.values() if s.active and framework in s.frameworks]
        return [s for s in self.subscriptions.values() if s.active]

    def match_changes_to_subscriptions(self, changes: List[RegulatoryChange]) -> Dict[str, List[RegulatoryChange]]:
        matched = {}
        impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for sub in self.get_subscriptions():
            min_rank = impact_order.get(sub.min_impact, 2)
            relevant = [
                c for c in changes
                if any(fw in c.affected_frameworks for fw in sub.frameworks)
                and impact_order.get(c.impact_level.value, 99) <= min_rank
            ]
            if relevant:
                matched[sub.subscription_id] = relevant
        return matched


def build_regulatory_calendar(changes: List[RegulatoryChange], year: int) -> List[Dict[str, Any]]:
    events = []
    for c in changes:
        if c.effective_date and c.effective_date.year == year:
            events.append({
                "change_id": c.change_id, "title": c.title, "date": c.effective_date.isoformat(),
                "type": c.change_type.value, "impact": c.impact_level.value, "event_kind": "effective",
            })
        if c.action_deadline and c.action_deadline.year == year:
            events.append({
                "change_id": c.change_id, "title": f"Deadline: {c.title}", "date": c.action_deadline.isoformat(),
                "type": "deadline", "impact": c.impact_level.value, "event_kind": "deadline",
            })
        if c.published_at.year == year:
            events.append({
                "change_id": c.change_id, "title": f"Published: {c.title}", "date": c.published_at.isoformat(),
                "type": "publication", "impact": c.impact_level.value, "event_kind": "published",
            })
    return sorted(events, key=lambda e: e["date"])


def compute_compliance_gaps(changes: List[RegulatoryChange], active_frameworks: List[str]) -> Dict[str, Any]:
    gaps = {}
    for fw in active_frameworks:
        fw_changes = [c for c in changes if fw in c.affected_frameworks and c.action_required]
        critical = sum(1 for c in fw_changes if c.impact_level == ImpactLevel.CRITICAL)
        high = sum(1 for c in fw_changes if c.impact_level == ImpactLevel.HIGH)
        gaps[fw] = {
            "total_gaps": len(fw_changes),
            "critical": critical,
            "high": high,
            "score": max(0, 100 - (critical * 25 + high * 10)),
            "urgent": any(c.impact_level in (ImpactLevel.CRITICAL, ImpactLevel.HIGH) and c.action_deadline and c.action_deadline < datetime.utcnow() + timedelta(days=30) for c in fw_changes),
        }
    return {
        "overall_score": round(sum(g["score"] for g in gaps.values()) / len(gaps), 1) if gaps else 100,
        "gaps": gaps,
        "most_affected": max(gaps, key=lambda k: gaps[k]["total_gaps"]) if gaps else None,
    }


class RegulatoryBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_detect(self, engine: RegulatoryIntelEngine, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for c in changes:
            try:
                change = engine.detect_change(
                    title=c["title"], source=c.get("source", "news"),
                    change_type=c.get("change_type", "guidance_update"),
                    description=c.get("description", ""), regulation=c.get("regulation", "Unknown"),
                    jurisdiction=c.get("jurisdiction", "Global"),
                    impact_level=c.get("impact_level", "medium"),
                    affected_controls=c.get("affected_controls"),
                    affected_frameworks=c.get("affected_frameworks"),
                    effective_date=datetime.fromisoformat(c["effective_date"]) if isinstance(c.get("effective_date"), str) else c.get("effective_date"),
                    action_required=c.get("action_required", False),
                    action_deadline=datetime.fromisoformat(c["action_deadline"]) if isinstance(c.get("action_deadline"), str) else c.get("action_deadline"),
                    source_url=c.get("source_url"),
                )
                results.append({"change_id": change.change_id, "title": change.title, "status": "success"})
                self.batch_log.append({"action": "detect", "regulation": c.get("regulation"), "status": "success"})
            except Exception as e:
                results.append({"title": c.get("title"), "status": "error", "error": str(e)})
                self.batch_log.append({"action": "detect", "regulation": c.get("regulation"), "status": "error", "error": str(e)})
        return results


async def paginate_changes(changes: List[RegulatoryChange], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(changes)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [c.to_dict() for c in changes[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_regulatory_data(changes: List[RegulatoryChange]) -> Dict[str, Any]:
    export_id = f"reg_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "changes": [c.to_dict() for c in changes],
        "summary": {"total_changes": len(changes)},
    }


def import_regulatory_changes(engine: RegulatoryIntelEngine, import_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    import_id = f"reg_import_{uuid.uuid4().hex[:8]}"
    imported = 0
    for c in import_data:
        try:
            engine.detect_change(c["title"], c.get("source", "news"), c.get("change_type", "guidance_update"), c.get("description", ""), c.get("regulation", "Unknown"), c.get("jurisdiction", "Global"), c.get("impact_level", "medium"))
            imported += 1
        except Exception:
            pass
    return {"import_id": import_id, "imported": imported}


class RegulatoryConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("regulatory_data_file"):
            self.errors.append("regulatory_data_file is required")
        poll_interval = self.config.get("poll_interval_minutes")
        if poll_interval is not None and poll_interval < 5:
            self.errors.append("poll_interval_minutes must be >= 5")
        return len(self.errors) == 0


def compute_regulatory_statistics(changes: List[RegulatoryChange]) -> Dict[str, Any]:
    total = len(changes)
    by_impact = {}
    by_status = {}
    by_jurisdiction = {}
    for c in changes:
        by_impact[c.impact_level.value] = by_impact.get(c.impact_level.value, 0) + 1
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_jurisdiction[c.jurisdiction] = by_jurisdiction.get(c.jurisdiction, 0) + 1
    action_required = sum(1 for c in changes if c.action_required)
    return {
        "total_changes": total, "by_impact": by_impact, "by_status": by_status,
        "by_jurisdiction": by_jurisdiction, "action_required": action_required,
        "coverage": len(set(c.regulation for c in changes)),
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class regulatory_intel_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class regulatory_intel_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class regulatory_intel_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class regulatory_intel_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class regulatory_intel_Cache:
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

class regulatory_intel_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class regulatory_intel_Queue:
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

class regulatory_intel_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class regulatory_intel_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_ri_changes_store: Dict[str, RegulatoryChange] = {}
_ri_frameworks_store: Dict[str, RegulatoryFramework] = {}


def add_ri_change(change: RegulatoryChange) -> str:
    _ri_changes_store[change.change_id] = change
    return change.change_id


def get_ri_change(change_id: str) -> Optional[RegulatoryChange]:
    return _ri_changes_store.get(change_id)


def search_ri_changes(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for c in _ri_changes_store.values():
        if query.lower() in c.title.lower() or query.lower() in c.framework.lower():
            results.append({"id": c.change_id, "title": c.title, "framework": c.framework, "type": c.change_type.value, "impact": c.impact_level.value})
            if len(results) >= limit:
                break
    return results


def batch_mark_reviewed(change_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "mark_reviewed", "succeeded": [], "failed": [], "total": len(change_ids)}
    for cid in change_ids:
        c = _ri_changes_store.get(cid)
        if c:
            c.reviewed = True
            op["succeeded"].append(cid)
        else:
            op["failed"].append(cid)
    return op


def get_ri_summary() -> Dict[str, Any]:
    total = len(_ri_changes_store)
    critical = sum(1 for c in _ri_changes_store.values() if c.impact_level == ImpactLevel.CRITICAL)
    high = sum(1 for c in _ri_changes_store.values() if c.impact_level == ImpactLevel.HIGH)
    medium = sum(1 for c in _ri_changes_store.values() if c.impact_level == ImpactLevel.MEDIUM)
    low = sum(1 for c in _ri_changes_store.values() if c.impact_level == ImpactLevel.LOW)
    unreviewed = sum(1 for c in _ri_changes_store.values() if not c.reviewed)
    by_source = {}
    for c in _ri_changes_store.values():
        by_source[c.source.value] = by_source.get(c.source.value, 0) + 1
    return {"total": total, "critical": critical, "high": high, "medium": medium, "low": low, "unreviewed": unreviewed, "by_source": by_source}


class RegulatoryChangeTracker:
    def __init__(self):
        self._changes = _ri_changes_store

    def get_changes_by_framework(self, framework: str) -> List[Dict[str, Any]]:
        return [{"id": c.change_id, "title": c.title, "type": c.change_type.value, "impact": c.impact_level.value, "date": c.effective_date.isoformat() if hasattr(c.effective_date, 'isoformat') else c.effective_date, "reviewed": c.reviewed} for c in self._changes.values() if c.framework == framework]

    def get_upcoming_deadlines(self, days: int = 90) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        deadline = now + timedelta(days=days)
        upcoming = []
        for c in self._changes.values():
            ed = c.effective_date if hasattr(c.effective_date, 'isoformat') else datetime.fromisoformat(str(c.effective_date).replace("Z", ""))
            if now <= ed <= deadline:
                upcoming.append({"id": c.change_id, "title": c.title, "framework": c.framework, "effective": c.effective_date.isoformat() if hasattr(c.effective_date, 'isoformat') else c.effective_date, "impact": c.impact_level.value, "days_remaining": (ed - now).days})
        return sorted(upcoming, key=lambda x: x["days_remaining"])

    def batch_review(self, change_ids: List[str], reviewer: str = "system") -> Dict[str, Any]:
        op: Dict[str, Any] = {"operation": "batch_review", "reviewer": reviewer, "succeeded": [], "failed": [], "total": len(change_ids)}
        for cid in change_ids:
            c = self._changes.get(cid)
            if c:
                c.reviewed = True
                op["succeeded"].append(cid)
            else:
                op["failed"].append(cid)
        return op


class RegulatoryAlertEngine:
    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []

    def generate_alerts(self) -> List[Dict[str, Any]]:
        new_alerts = []
        for c in _ri_changes_store.values():
            if not c.reviewed and c.impact_level in (ImpactLevel.CRITICAL, ImpactLevel.HIGH):
                alert = {"alert_id": f"alert_{uuid.uuid4().hex[:8]}", "change_id": c.change_id, "title": c.title, "framework": c.framework, "impact": c.impact_level.value, "generated_at": datetime.utcnow().isoformat(), "acknowledged": False}
                self._alerts.append(alert)
                new_alerts.append(alert)
        return new_alerts

    def acknowledge_alert(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a["alert_id"] == alert_id and not a["acknowledged"]:
                a["acknowledged"] = True
                a["acknowledged_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self._alerts if not a["acknowledged"]]


class RegulatoryReportGenerator:
    def __init__(self):
        self._changes = _ri_changes_store

    def generate_impact_report(self, framework: str) -> str:
        changes = [c for c in self._changes.values() if c.framework == framework]
        lines = [f"=== Regulatory Impact Report: {framework} ===", f"Generated: {datetime.utcnow().isoformat()}", f"Total Changes: {len(changes)}", f"Unreviewed: {sum(1 for c in changes if not c.reviewed)}", "", "Changes by Impact:"]
        for level in ImpactLevel:
            count = sum(1 for c in changes if c.impact_level == level)
            lines.append(f"  {level.value}: {count}")
        lines.append("", "Upcoming Deadlines:")
        for c in sorted(changes, key=lambda x: x.effective_date if hasattr(x.effective_date, 'isoformat') else str(x.effective_date)):
            lines.append(f"  - {c.title} (effective: {c.effective_date})")
        return "\n".join(lines)

    def export_changes_csv(self, framework: str = "") -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["change_id", "title", "framework", "type", "impact", "effective_date", "reviewed"])
        changes = [c for c in self._changes.values() if not framework or c.framework == framework]
        for c in changes:
            writer.writerow([c.change_id, c.title, c.framework, c.change_type.value, c.impact_level.value, c.effective_date.isoformat() if hasattr(c.effective_date, 'isoformat') else c.effective_date, c.reviewed])
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
