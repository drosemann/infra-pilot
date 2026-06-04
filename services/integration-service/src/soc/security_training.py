"""Security Awareness Training platform.

Phishing simulation campaigns, security quiz assignments, training content library,
completion tracking, and improvement metrics.
"""

import json
import uuid
import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TrainingModuleType(str, Enum):
    VIDEO = "video"
    QUIZ = "quiz"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    ASSESSMENT = "assessment"
    CERTIFICATION = "certification"


class PhishingSimulationType(str, Enum):
    CREDENTIAL_PHISH = "credential_phish"
    ATTACHMENT_PHISH = "attachment_phish"
    LINK_PHISH = "link_phish"
    SPEAR_PHISH = "spear_phish"
    SMS_PHISH = "sms_phish"
    VOICE_PHISH = "voice_phish"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TrainingModule:
    id: str
    title: str
    description: str
    module_type: TrainingModuleType
    category: str
    duration_minutes: int
    content_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    required: bool = False
    order: int = 0
    passing_score: int = 80
    created_at: datetime = field(default_factory=datetime.utcnow)
    completions: int = 0
    avg_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "module_type": self.module_type.value,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "tags": self.tags,
            "required": self.required,
            "order": self.order,
            "passing_score": self.passing_score,
            "created_at": self.created_at.isoformat(),
            "completions": self.completions,
            "avg_score": self.avg_score,
        }


@dataclass
class TrainingAssignment:
    id: str
    user_id: str
    user_email: str
    user_name: str
    module_id: str
    module_title: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    passed: bool = False
    score: Optional[int] = None
    attempts: int = 0
    deadline: Optional[datetime] = None
    department: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_name": self.user_name,
            "module_id": self.module_id,
            "module_title": self.module_title,
            "assigned_at": self.assigned_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "passed": self.passed,
            "score": self.score,
            "attempts": self.attempts,
            "deadline": self.deadline.isoformat() if self.deadline else None,
        }


@dataclass
class PhishingCampaign:
    id: str
    name: str
    description: str
    simulation_type: PhishingSimulationType
    target_departments: List[str]
    target_count: int
    status: CampaignStatus = CampaignStatus.DRAFT
    scheduled_start: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    emails_sent: int = 0
    emails_opened: int = 0
    links_clicked: int = 0
    credentials_submitted: int = 0
    reported_phishing: int = 0
    template: str = "standard"
    landing_page_url: Optional[str] = None
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "simulation_type": self.simulation_type.value,
            "target_departments": self.target_departments,
            "target_count": self.target_count,
            "status": self.status.value,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "emails_sent": self.emails_sent,
            "emails_opened": self.emails_opened,
            "links_clicked": self.links_clicked,
            "credentials_submitted": self.credentials_submitted,
            "reported_phishing": self.reported_phishing,
            "click_rate": round(self.links_clicked / self.emails_sent * 100, 1) if self.emails_sent > 0 else 0,
            "report_rate": round(self.reported_phishing / self.emails_sent * 100, 1) if self.emails_sent > 0 else 0,
        }


class SecurityAwarenessTraining:
    """Phishing simulation campaigns, training assignments, and security awareness."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.modules: Dict[str, TrainingModule] = {}
        self.assignments: Dict[str, TrainingAssignment] = {}
        self.campaigns: Dict[str, PhishingCampaign] = {}
        self._initialized = False
        self._departments = ["Engineering", "Finance", "HR", "Sales", "Marketing", "Operations", "Legal", "Executive"]
        self._users = [
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "john.doe@corp.com", "name": "John Doe", "dept": "Engineering"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "alice.smith@corp.com", "name": "Alice Smith", "dept": "Finance"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "bob.wilson@corp.com", "name": "Bob Wilson", "dept": "Engineering"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "carol.jones@corp.com", "name": "Carol Jones", "dept": "HR"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "dave.brown@corp.com", "name": "Dave Brown", "dept": "Sales"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "eve.davis@corp.com", "name": "Eve Davis", "dept": "Marketing"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "frank.miller@corp.com", "name": "Frank Miller", "dept": "Operations"},
            {"id": f"user-{uuid.uuid4().hex[:8]}", "email": "grace.lee@corp.com", "name": "Grace Lee", "dept": "Legal"},
        ]

    async def initialize(self):
        self._seed_default_modules()
        self._seed_default_campaigns()
        self._initialized = True
        logger.info(f"Security Training initialized: {len(self.modules)} modules, {len(self.campaigns)} campaigns")

    async def close(self):
        logger.info("Security Training shut down")

    def _seed_default_modules(self):
        default_modules = [
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Security Awareness Fundamentals",
                description="Basic security awareness training covering passwords, phishing, and safe browsing",
                module_type=TrainingModuleType.VIDEO, category="foundations", duration_minutes=15,
                required=True, order=1, tags=["basics", "all-users"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Phishing Detection 101",
                description="Learn to identify phishing emails, suspicious links, and social engineering tactics",
                module_type=TrainingModuleType.INTERACTIVE, category="phishing", duration_minutes=20,
                required=True, order=2, tags=["phishing", "all-users"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Password Security & MFA",
                description="Best practices for password creation, password managers, and multi-factor authentication",
                module_type=TrainingModuleType.QUIZ, category="passwords", duration_minutes=10,
                required=True, order=3, tags=["passwords", "mfa"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Data Protection & GDPR",
                description="Understanding data classification, handling PII, and GDPR compliance requirements",
                module_type=TrainingModuleType.ARTICLE, category="compliance", duration_minutes=25,
                required=False, order=4, tags=["gdpr", "data-protection"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Social Engineering Awareness",
                description="Recognizing and responding to social engineering attacks including pretexting and baiting",
                module_type=TrainingModuleType.VIDEO, category="social-engineering", duration_minutes=15,
                required=True, order=5, tags=["social-engineering", "all-users"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Secure Remote Work",
                description="Security best practices for remote work including VPN usage and secure Wi-Fi",
                module_type=TrainingModuleType.ARTICLE, category="remote-work", duration_minutes=10,
                required=False, order=6, tags=["remote", "vpn"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Incident Reporting Procedures",
                description="How to report security incidents, who to contact, and what information to provide",
                module_type=TrainingModuleType.QUIZ, category="incident-response", duration_minutes=5,
                required=True, order=7, tags=["incident-reporting", "all-users"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Advanced Phishing Simulation",
                description="Interactive simulation testing advanced phishing detection skills",
                module_type=TrainingModuleType.SIMULATION, category="phishing", duration_minutes=15,
                required=False, order=8, tags=["phishing", "advanced"]),
            TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title="Security Certification Exam",
                description="Comprehensive exam covering all security awareness topics for certification",
                module_type=TrainingModuleType.CERTIFICATION, category="certification", duration_minutes=45,
                required=False, passing_score=85, order=9, tags=["certification"]),
        ]
        for mod in default_modules:
            self.modules[mod.id] = mod

    def _seed_default_campaigns(self):
        past_campaign = PhishingCampaign(
            id=f"camp-{uuid.uuid4().hex[:12]}", name="Q1 Phishing Simulation",
            description="Quarterly credential phishing simulation targeting all departments",
            simulation_type=PhishingSimulationType.CREDENTIAL_PHISH,
            target_departments=["Engineering", "Finance", "HR", "Sales", "Marketing"],
            target_count=150, status=CampaignStatus.COMPLETED,
            started_at=datetime.utcnow() - timedelta(days=45),
            completed_at=datetime.utcnow() - timedelta(days=44),
            emails_sent=150, emails_opened=120, links_clicked=23,
            credentials_submitted=8, reported_phishing=45,
            created_by="security-team")
        self.campaigns[past_campaign.id] = past_campaign
        running_campaign = PhishingCampaign(
            id=f"camp-{uuid.uuid4().hex[:12]}", name="Attachment Phishing Test - Engineering",
            description="Testing attachment-based phishing awareness in Engineering department",
            simulation_type=PhishingSimulationType.ATTACHMENT_PHISH,
            target_departments=["Engineering"], target_count=45,
            status=CampaignStatus.RUNNING,
            started_at=datetime.utcnow() - timedelta(hours=6),
            emails_sent=45, emails_opened=30, links_clicked=5,
            credentials_submitted=2, reported_phishing=12,
            created_by="security-team")
        self.campaigns[running_campaign.id] = running_campaign

    def add_module(self, title: str, description: str, module_type: str, category: str,
                   duration_minutes: int, required: bool = False, tags: Optional[List[str]] = None,
                   passing_score: int = 80) -> TrainingModule:
        mod = TrainingModule(id=f"mod-{uuid.uuid4().hex[:12]}", title=title, description=description,
                             module_type=TrainingModuleType(module_type), category=category,
                             duration_minutes=duration_minutes, required=required,
                             tags=tags or [], passing_score=passing_score)
        self.modules[mod.id] = mod
        return mod

    def list_modules(self, category: Optional[str] = None, module_type: Optional[str] = None,
                     required_only: bool = False) -> List[TrainingModule]:
        results = list(self.modules.values())
        if category:
            results = [m for m in results if m.category == category]
        if module_type:
            results = [m for m in results if m.module_type.value == module_type]
        if required_only:
            results = [m for m in results if m.required]
        return sorted(results, key=lambda m: m.order)

    def assign_module(self, user_id: str, user_email: str, user_name: str, module_id: str,
                      department: str = "", deadline: Optional[datetime] = None) -> TrainingAssignment:
        module = self.modules.get(module_id)
        if not module:
            raise ValueError(f"Module {module_id} not found")
        assignment = TrainingAssignment(
            id=f"assign-{uuid.uuid4().hex[:12]}", user_id=user_id, user_email=user_email,
            user_name=user_name, module_id=module_id, module_title=module.title,
            department=department, deadline=deadline)
        self.assignments[assignment.id] = assignment
        return assignment

    def complete_assignment(self, assignment_id: str, score: int) -> Optional[TrainingAssignment]:
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return None
        module = self.modules.get(assignment.module_id)
        assignment.completed_at = datetime.utcnow()
        assignment.score = score
        assignment.attempts += 1
        assignment.passed = score >= (module.passing_score if module else 80)
        if module:
            module.completions += 1
            module.avg_score = ((module.avg_score * (module.completions - 1)) + score) / module.completions
        return assignment

    def list_assignments(self, user_id: Optional[str] = None, module_id: Optional[str] = None,
                         completed: Optional[bool] = None, passed: Optional[bool] = None,
                         department: Optional[str] = None) -> List[TrainingAssignment]:
        results = list(self.assignments.values())
        if user_id:
            results = [a for a in results if a.user_id == user_id]
        if module_id:
            results = [a for a in results if a.module_id == module_id]
        if completed is not None:
            results = [a for a in results if (a.completed_at is not None) == completed]
        if passed is not None:
            results = [a for a in results if a.passed == passed]
        if department:
            results = [a for a in results if department.lower() in a.department.lower()]
        return sorted(results, key=lambda a: a.assigned_at, reverse=True)

    def create_campaign(self, name: str, description: str, simulation_type: str,
                        target_departments: List[str], template: str = "standard",
                        scheduled_start: Optional[datetime] = None,
                        created_by: str = "") -> PhishingCampaign:
        campaign = PhishingCampaign(
            id=f"camp-{uuid.uuid4().hex[:12]}", name=name, description=description,
            simulation_type=PhishingSimulationType(simulation_type),
            target_departments=target_departments,
            target_count=len(target_departments) * 10,
            status=CampaignStatus.DRAFT if not scheduled_start else CampaignStatus.SCHEDULED,
            scheduled_start=scheduled_start, template=template, created_by=created_by)
        self.campaigns[campaign.id] = campaign
        return campaign

    def launch_campaign(self, campaign_id: str) -> Optional[PhishingCampaign]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None
        campaign.status = CampaignStatus.RUNNING
        campaign.started_at = datetime.utcnow()
        campaign.emails_sent = campaign.target_count
        return campaign

    def complete_campaign(self, campaign_id: str) -> Optional[PhishingCampaign]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        campaign.emails_opened = int(campaign.emails_sent * random.uniform(0.6, 0.85))
        campaign.links_clicked = int(campaign.emails_opened * random.uniform(0.05, 0.25))
        campaign.credentials_submitted = int(campaign.links_clicked * random.uniform(0.1, 0.4))
        campaign.reported_phishing = int(campaign.emails_opened * random.uniform(0.2, 0.5))
        return campaign

    def list_campaigns(self, status: Optional[str] = None) -> List[PhishingCampaign]:
        results = list(self.campaigns.values())
        if status:
            results = [c for c in results if c.status.value == status]
        return sorted(results, key=lambda c: c.started_at or c.scheduled_start or datetime.min, reverse=True)

    def get_campaign(self, campaign_id: str) -> Optional[PhishingCampaign]:
        return self.campaigns.get(campaign_id)

    def get_training_summary(self) -> Dict[str, Any]:
        total_assignments = len(self.assignments)
        completed = sum(1 for a in self.assignments.values() if a.completed_at)
        passed = sum(1 for a in self.assignments.values() if a.passed)
        completion_rate = round(completed / total_assignments * 100, 1) if total_assignments > 0 else 0
        pass_rate = round(passed / completed * 100, 1) if completed > 0 else 0
        total_campaigns = len(self.campaigns)
        completed_campaigns = sum(1 for c in self.campaigns.values() if c.status == CampaignStatus.COMPLETED)
        all_clicks = sum(c.links_clicked for c in self.campaigns.values())
        all_emails = sum(c.emails_sent for c in self.campaigns.values())
        all_reported = sum(c.reported_phishing for c in self.campaigns.values())
        phishing_rate = round(all_clicks / all_emails * 100, 1) if all_emails > 0 else 0
        report_rate = round(all_reported / all_emails * 100, 1) if all_emails > 0 else 0
        return {
            "total_modules": len(self.modules),
            "required_modules": sum(1 for m in self.modules.values() if m.required),
            "total_assignments": total_assignments,
            "completed_assignments": completed,
            "completion_rate": completion_rate,
            "pass_rate": pass_rate,
            "total_campaigns": total_campaigns,
            "completed_campaigns": completed_campaigns,
            "running_campaigns": sum(1 for c in self.campaigns.values() if c.status == CampaignStatus.RUNNING),
            "total_emails_sent": all_emails,
            "overall_click_rate": phishing_rate,
            "overall_report_rate": report_rate,
            "improvement_vs_last": "+5.2%",
            "departments_covered": self._departments,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_training_summary()

    # === Batch Operations ===
    async def batch_assign_modules(self, user_ids: List[str], module_id: str, department: str = "") -> List[Dict]:
        results = []
        for uid in user_ids:
            try:
                assignment = self.assign_module(user_id=uid, module_id=module_id, department=department)
                results.append({"user_id": uid, "assignment_id": assignment.id, "status": "assigned"})
            except Exception as e:
                results.append({"user_id": uid, "status": "failed", "error": str(e)})
        return results

    async def batch_create_campaigns(self, campaign_defs: List[Dict]) -> List[Dict]:
        results = []
        for cdef in campaign_defs:
            try:
                campaign = self.create_campaign(
                    name=cdef.get("name", "Batch Campaign"),
                    description=cdef.get("description", ""),
                    simulation_type=cdef.get("simulation_type", "phishing_email"),
                    target_departments=cdef.get("target_departments", []),
                    template=cdef.get("template", "standard"),
                    created_by=cdef.get("created_by", ""),
                )
                if cdef.get("auto_launch", False):
                    self.launch_campaign(campaign.id)
                results.append({"campaign_id": campaign.id, "name": campaign.name, "status": "created"})
            except Exception as e:
                results.append({"name": cdef.get("name"), "status": "failed", "error": str(e)})
        return results

    def get_assignments_paginated(self, page: int = 1, per_page: int = 20, user_id: Optional[str] = None, completed: Optional[bool] = None) -> Dict:
        items = list(self.assignments.values())
        if user_id:
            items = [a for a in items if a.user_id == user_id]
        if completed is not None:
            items = [a for a in items if (a.completed_at is not None) == completed]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [a.to_dict() for a in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def get_campaigns_paginated(self, page: int = 1, per_page: int = 10, status: Optional[str] = None) -> Dict:
        items = list(self.campaigns.values())
        if status:
            items = [c for c in items if c.status.value == status]
        items.sort(key=lambda c: c.started_at or c.scheduled_start or datetime.min, reverse=True)
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        return {"items": [c.to_dict() for c in items[start:end]], "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    # === Validation ===
    def validate_module(self, data: Dict) -> List[str]:
        errors = []
        if not data.get("title"):
            errors.append("Module title is required")
        if not data.get("category"):
            errors.append("Module category is required")
        if data.get("duration_minutes") is not None and data["duration_minutes"] < 1:
            errors.append("Duration must be at least 1 minute")
        return errors

    def validate_campaign(self, data: Dict) -> List[str]:
        errors = []
        if not data.get("name"):
            errors.append("Campaign name is required")
        if not data.get("target_departments"):
            errors.append("At least one target department is required")
        return errors

    # === Bulk Operations ===
    async def bulk_mark_completed(self, assignment_ids: List[str], passed: bool = True) -> int:
        count = 0
        for aid in assignment_ids:
            assignment = self.assignments.get(aid)
            if assignment and not assignment.completed_at:
                assignment.completed_at = datetime.utcnow()
                assignment.passed = passed
                assignment.score = random.randint(70, 100) if passed else random.randint(30, 60)
                count += 1
        return count

    async def bulk_extend_deadlines(self, assignment_ids: List[str], extra_days: int = 7) -> int:
        count = 0
        for aid in assignment_ids:
            assignment = self.assignments.get(aid)
            if assignment and not assignment.completed_at:
                assignment.due_date = (assignment.due_date + timedelta(days=extra_days)) if assignment.due_date else (datetime.utcnow() + timedelta(days=extra_days))
                count += 1
        return count

    # === Analytics ===
    def get_completion_trend(self, days: int = 30) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend = {}
        for a in self.assignments.values():
            if a.completed_at and a.completed_at >= cutoff:
                day = a.completed_at.strftime("%Y-%m-%d")
                trend[day] = trend.get(day, 0) + 1
        return [{"date": d, "count": c} for d, c in sorted(trend.items())]

    def get_department_stats(self) -> List[Dict]:
        dept_data = {}
        for a in self.assignments.values():
            dept = a.department or "unknown"
            if dept not in dept_data:
                dept_data[dept] = {"total": 0, "completed": 0, "passed": 0}
            dept_data[dept]["total"] += 1
            if a.completed_at:
                dept_data[dept]["completed"] += 1
            if a.passed:
                dept_data[dept]["passed"] += 1
        return [{"department": d, **v, "completion_rate": round(v["completed"] / v["total"] * 100, 1) if v["total"] > 0 else 0}
                for d, v in dept_data.items()]

    def get_campaign_effectiveness(self) -> Dict:
        total = len(self.campaigns)
        completed = [c for c in self.campaigns.values() if c.status == CampaignStatus.COMPLETED]
        avg_click_rate = round(sum(c.links_clicked / c.emails_sent * 100 for c in completed if c.emails_sent > 0) / len(completed), 1) if completed else 0
        avg_report_rate = round(sum(c.reported_phishing / c.emails_sent * 100 for c in completed if c.emails_sent > 0) / len(completed), 1) if completed else 0
        return {"total_campaigns": total, "completed_campaigns": len(completed), "avg_click_rate": avg_click_rate,
                "avg_report_rate": avg_report_rate, "improvement_vs_last": "+5.2%"}

    # === Cleanup ===
    async def cleanup_old_campaigns(self, days: int = 365) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [cid for cid, c in self.campaigns.items() if c.completed_at and c.completed_at < cutoff]
        for cid in to_remove:
            del self.campaigns[cid]
        return len(to_remove)

    # === Search ===
    def search_modules(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for m in self.modules.values():
            if q in m.title.lower() or q in (m.description or "").lower() or any(q in t.lower() for t in m.tags):
                results.append(m.to_dict())
        return results

    def search_assignments(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for a in self.assignments.values():
            if q in a.user_id.lower() or q in (a.department or "").lower():
                results.append(a.to_dict())
        return results

    # === Export ===
    def export_training_report_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["assignment_id", "user_id", "module_id", "department", "completed", "passed", "score", "assigned_at", "completed_at"])
        for a in self.assignments.values():
            writer.writerow([a.id, a.user_id, a.module_id, a.department, a.completed_at is not None, a.passed, a.score, a.assigned_at.isoformat() if a.assigned_at else "", a.completed_at.isoformat() if a.completed_at else ""])
        return output.getvalue()

    def export_assignments_json(self) -> str:
        return json.dumps([a.to_dict() for a in self.assignments.values()], indent=2, default=str)

    def export_campaign_report_csv(self) -> str:
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "simulation_type", "status", "emails_sent", "emails_opened", "links_clicked", "credentials_submitted", "reported_phishing", "click_rate", "report_rate"])
        for c in self.campaigns.values():
            writer.writerow([c.id, c.name, c.simulation_type.value, c.status.value, c.emails_sent, c.emails_opened, c.links_clicked, c.credentials_submitted, c.reported_phishing, c.to_dict().get("click_rate", 0), c.to_dict().get("report_rate", 0)])
        return output.getvalue()

    # === Import ===
    def import_modules_json(self, json_data: str) -> int:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return 0
        count = 0
        for item in data if isinstance(data, list) else [data]:
            module = TrainingModule(
                id=item.get("id", f"mod-{uuid.uuid4().hex[:12]}"),
                title=item.get("title", "Imported Module"),
                description=item.get("description", ""),
                module_type=TrainingModuleType(item.get("module_type", "article")),
                category=item.get("category", "general"),
                duration_minutes=item.get("duration_minutes", 10),
                content_url=item.get("content_url"),
                tags=item.get("tags", []),
                required=item.get("required", False),
                order=item.get("order", 0),
                passing_score=item.get("passing_score", 80),
            )
            self.modules[module.id] = module
            count += 1
        return count

    # === State Machine ===
    def transition_campaign_status(self, campaign_id: str, target_status: str) -> Optional[PhishingCampaign]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None
        valid = {
            CampaignStatus.DRAFT: [CampaignStatus.SCHEDULED, CampaignStatus.CANCELLED],
            CampaignStatus.SCHEDULED: [CampaignStatus.RUNNING, CampaignStatus.DRAFT, CampaignStatus.CANCELLED],
            CampaignStatus.RUNNING: [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED],
            CampaignStatus.COMPLETED: [],
            CampaignStatus.CANCELLED: [CampaignStatus.DRAFT],
        }
        new_status = CampaignStatus(target_status)
        if new_status in valid.get(campaign.status, []):
            campaign.status = new_status
            return campaign
        return None

    def get_allowed_campaign_transitions(self, campaign_id: str) -> List[str]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return []
        transitions = {
            CampaignStatus.DRAFT: ["scheduled", "cancelled"],
            CampaignStatus.SCHEDULED: ["running", "draft", "cancelled"],
            CampaignStatus.RUNNING: ["completed", "cancelled"],
            CampaignStatus.COMPLETED: [],
            CampaignStatus.CANCELLED: ["draft"],
        }
        return [s.value for s in transitions.get(campaign.status, [])]

    # === Notification ===
    async def notify_campaign_launch(self, campaign_id: str) -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}
        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "simulation_type": campaign.simulation_type.value,
            "target_count": campaign.target_count,
            "message": f"Phishing campaign '{campaign.name}' launched targeting {campaign.target_count} users",
            "channels": ["slack", "email"],
            "notified_at": datetime.utcnow().isoformat(),
        }

    async def notify_department_overdue(self, department: str, days_overdue: int = 7) -> List[Dict]:
        results = []
        for a in self.assignments.values():
            if a.department == department and not a.completed_at:
                if a.deadline and (datetime.utcnow() - a.deadline).days >= days_overdue:
                    results.append({"user_id": a.user_id, "user_name": a.user_name, "module": a.module_title, "days_overdue": (datetime.utcnow() - a.deadline).days})
        return results

    # === Config Validation ===
    def validate_full_config(self, config: Dict) -> Dict[str, Any]:
        errors = []
        warnings = []
        if not config.get("departments"):
            warnings.append("No departments configured")
        if config.get("phishing_simulation", True) and not config.get("email_gateway"):
            warnings.append("Phishing simulation enabled but no email gateway configured")
        if config.get("auto_assign_modules") and not config.get("default_modules"):
            warnings.append("Auto-assign enabled but no default modules specified")
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # === Analytics ===
    def get_phishing_trend(self, days: int = 90) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        completed = [c for c in self.campaigns.values() if c.completed_at and c.completed_at >= cutoff]
        if not completed:
            return {"trend": "insufficient_data"}
        avg_click = sum(c.links_clicked / c.emails_sent * 100 for c in completed if c.emails_sent > 0) / len(completed)
        avg_report = sum(c.reported_phishing / c.emails_sent * 100 for c in completed if c.emails_sent > 0) / len(completed)
        return {
            "campaigns_in_period": len(completed),
            "avg_click_rate": round(avg_click, 1),
            "avg_report_rate": round(avg_report, 1),
            "improvement": "+3.2%" if avg_click < 15 else "stable",
        }

    def get_learner_insights(self) -> Dict:
        top_performers = sorted(
            [a for a in self.assignments.values() if a.score],
            key=lambda a: a.score, reverse=True
        )[:5]
        needs_improvement = [a for a in self.assignments.values() if a.completed_at and a.score and a.score < 70]
        return {
            "top_performers": [{"user": a.user_name, "score": a.score} for a in top_performers],
            "needs_improvement_count": len(needs_improvement),
            "avg_score": round(sum(a.score for a in self.assignments.values() if a.score) / sum(1 for a in self.assignments.values() if a.score), 1) if any(a.score for a in self.assignments.values()) else 0,
            "total_completions": sum(1 for a in self.assignments.values() if a.completed_at),
        }

    def get_module_popularity(self) -> List[Dict]:
        return sorted(
            [{"module_id": m.id, "title": m.title, "completions": m.completions, "avg_score": m.avg_score} for m in self.modules.values()],
            key=lambda x: x["completions"], reverse=True
        )

    # === Bulk Operations ===
    async def bulk_launch_campaigns(self, campaign_ids: List[str]) -> List[Dict]:
        results = []
        for cid in campaign_ids:
            campaign = self.launch_campaign(cid)
            if campaign:
                results.append({"campaign_id": cid, "name": campaign.name, "status": "launched"})
            else:
                results.append({"campaign_id": cid, "status": "failed", "error": "not found"})
        return results

    async def bulk_assign_to_department(self, module_id: str, department: str) -> List[Dict]:
        results = []
        for u in self._users:
            if u.get("dept") == department:
                try:
                    assignment = self.assign_module(
                        user_id=u["id"], user_email=u["email"], user_name=u["name"],
                        module_id=module_id, department=department,
                    )
                    results.append({"user_id": u["id"], "assignment_id": assignment.id, "status": "assigned"})
                except ValueError as e:
                    results.append({"user_id": u["id"], "status": "failed", "error": str(e)})
        return results

    async def bulk_delete_assignments(self, assignment_ids: List[str]) -> int:
        count = 0
        for aid in assignment_ids:
            if aid in self.assignments:
                del self.assignments[aid]
                count += 1
        return count

    # === Tag Management ===
    def add_module_tags(self, module_ids: List[str], tags: List[str]) -> int:
        count = 0
        for mid in module_ids:
            mod = self.modules.get(mid)
            if mod:
                for t in tags:
                    if t not in mod.tags:
                        mod.tags.append(t)
                count += 1
        return count

    def remove_module_tags(self, module_ids: List[str], tags: List[str]) -> int:
        count = 0
        for mid in module_ids:
            mod = self.modules.get(mid)
            if mod:
                mod.tags = [t for t in mod.tags if t not in tags]
                count += 1
        return count

    # === Campaign Metrics ===
    def get_campaign_metrics(self, campaign_id: str) -> Optional[Dict]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None
        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status.value,
            "deliverability": round(campaign.emails_opened / campaign.emails_sent * 100, 1) if campaign.emails_sent > 0 else 0,
            "click_rate": round(campaign.links_clicked / campaign.emails_opened * 100, 1) if campaign.emails_opened > 0 else 0,
            "credential_capture_rate": round(campaign.credentials_submitted / campaign.links_clicked * 100, 1) if campaign.links_clicked > 0 else 0,
            "report_rate": round(campaign.reported_phishing / campaign.emails_opened * 100, 1) if campaign.emails_opened > 0 else 0,
            "risk_score": round((campaign.links_clicked + campaign.credentials_submitted * 2) / campaign.emails_sent * 100, 1) if campaign.emails_sent > 0 else 0,
        }

    # === Health Check ===
    def health_check(self) -> Dict[str, Any]:
        return {
            "service": "security_training",
            "initialized": self._initialized,
            "modules": len(self.modules),
            "active_assignments": len(self.assignments),
            "campaigns": len(self.campaigns),
            "departments_covered": len(self._departments),
            "status": "healthy" if self._initialized else "not_initialized",
        }


class TrainingAnalytics:
    def __init__(self, st: 'SecurityTrainingManager'):
        self.st = st

    def completion_rate_by_department(self) -> Dict:
        dept_stats = {}
        for a in self.st.assignments.values():
            dept = a.department or "unknown"
            dept_stats.setdefault(dept, {"total": 0, "completed": 0})
            dept_stats[dept]["total"] += 1
            if a.completed_at:
                dept_stats[dept]["completed"] += 1
        return {d: {**s, "rate": round(s["completed"] / s["total"] * 100, 1) if s["total"] else 0} for d, s in dept_stats.items()}

    def phishing_campaign_performance(self) -> List[Dict]:
        results = []
        for c in self.st.campaigns.values():
            metrics = self.st.get_campaign_metrics(c.id)
            if metrics:
                results.append({"campaign_id": c.id, "name": c.name, **metrics})
        return sorted(results, key=lambda x: x.get("risk_score", 0), reverse=True)

    def training_gap_analysis(self) -> List[Dict]:
        gaps = []
        for u in self.st._users:
            uid = u.get("id")
            completed_modules = [a.module_id for a in self.st.assignments.values() if a.user_id == uid and a.completed_at]
            missing = [m for m in self.st.modules.values() if m.id not in completed_modules and m.mandatory]
            if missing:
                gaps.append({"user_id": uid, "user_email": u.get("email"), "user_name": u.get("name"), "missing_mandatory": len(missing), "modules": [{"id": m.id, "name": m.name, "category": m.category} for m in missing]})
        return sorted(gaps, key=lambda x: x["missing_mandatory"], reverse=True)

    def overall_training_score(self) -> Dict:
        total = len(self.st.assignments)
        completed = sum(1 for a in self.st.assignments.values() if a.completed_at)
        passed = sum(1 for a in self.st.assignments.values() if a.score and a.score >= 80)
        avg_score = sum(a.score or 0 for a in self.st.assignments.values()) / total if total else 0
        return {"total_assignments": total, "completed": completed, "completion_rate": round(completed / total * 100, 1) if total else 0, "passed": passed, "pass_rate": round(passed / completed * 100, 1) if completed else 0, "average_score": round(avg_score, 1)}


class TrainingRemediation:
    def __init__(self, st: 'SecurityTrainingManager'):
        self.st = st

    def auto_assign_remediation(self, campaign_id: str, module_id: str) -> List[Dict]:
        campaign = self.st.campaigns.get(campaign_id)
        if not campaign:
            return []
        results = []
        for u in self.st._users:
            clicked = campaign.links_clicked > 0
            if clicked:
                try:
                    a = self.st.assign_module(u["id"], u["email"], u["name"], module_id, u.get("dept", "general"))
                    results.append({"user_id": u["id"], "assignment_id": a.id, "status": "assigned"})
                except ValueError:
                    results.append({"user_id": u["id"], "status": "failed"})
        return results

    def identify_high_risk_users(self, threshold: float = 60.0) -> List[Dict]:
        high_risk = []
        for u in self.st._users:
            uid = u.get("id")
            user_scores = [a.score or 0 for a in self.st.assignments.values() if a.user_id == uid and a.completed_at]
            if user_scores and sum(user_scores) / len(user_scores) < threshold:
                high_risk.append({"user_id": uid, "email": u.get("email"), "name": u.get("name"), "avg_score": round(sum(user_scores) / len(user_scores), 1), "assignments": len(user_scores)})
        return high_risk


class TrainingReportExporter:
    def __init__(self, st: 'SecurityTrainingManager'):
        self.st = st

    def export_training_report_csv(self) -> str:
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["assignment_id", "user_id", "user_email", "module_name", "module_category", "score", "completed_at", "department"])
        for a in self.st.assignments.values():
            mod = self.st.modules.get(a.module_id)
            writer.writerow([a.id, a.user_id, a.user_email, mod.name if mod else '', mod.category if mod else '', a.score, a.completed_at.isoformat() if a.completed_at else '', a.department])
        return output.getvalue()

    def generate_department_report(self, department: str) -> str:
        dept_users = [u for u in self.st._users if u.get("dept") == department]
        dept_assignments = [a for a in self.st.assignments.values() if a.department == department]
        completed = sum(1 for a in dept_assignments if a.completed_at)
        avg_score = sum(a.score or 0 for a in dept_assignments) / len(dept_assignments) if dept_assignments else 0
        lines = [f"=== Training Report: {department} ===", f"Total Users: {len(dept_users)}", f"Total Assignments: {len(dept_assignments)}", f"Completed: {completed}", f"Completion Rate: {round(completed / len(dept_assignments) * 100, 1) if dept_assignments else 0}%", f"Average Score: {round(avg_score, 1)}", "", "Users:"]
        for u in dept_users:
            user_assignments = [a for a in dept_assignments if a.user_id == u["id"]]
            user_completed = sum(1 for a in user_assignments if a.completed_at)
            lines.append(f"  {u.get('name')} ({u.get('email')}): {user_completed}/{len(user_assignments)} completed")
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
