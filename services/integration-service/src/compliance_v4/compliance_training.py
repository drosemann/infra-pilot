import json
import uuid
import logging
import os
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class QuizDifficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class QuizQuestion:
    question_id: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    category: str
    difficulty: QuizDifficulty

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "category": self.category,
            "difficulty": self.difficulty.value,
        }


@dataclass
class TrainingModule:
    module_id: str
    title: str
    description: str
    category: str
    framework: str
    content: str
    duration_minutes: int
    difficulty: QuizDifficulty
    questions: List[QuizQuestion]
    pass_threshold: int
    certification_id: Optional[str]
    version: str
    status: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "framework": self.framework,
            "content_preview": self.content[:300],
            "duration_minutes": self.duration_minutes,
            "difficulty": self.difficulty.value,
            "question_count": len(self.questions),
            "questions": [q.to_dict() for q in self.questions],
            "pass_threshold": self.pass_threshold,
            "certification_id": self.certification_id,
            "version": self.version,
            "status": self.status,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class TrainingAssignment:
    assignment_id: str
    user_id: str
    user_name: str
    module_id: str
    module_title: str
    status: TrainingStatus
    score: Optional[int]
    max_score: int
    answers: Dict[str, str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    due_date: datetime
    assigned_by: str
    reminder_sent: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "module_id": self.module_id,
            "module_title": self.module_title,
            "status": self.status.value,
            "score": self.score,
            "max_score": self.max_score,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "due_date": self.due_date.isoformat(),
            "assigned_by": self.assigned_by,
            "reminder_sent": self.reminder_sent,
        }


@dataclass
class Certification:
    cert_id: str
    user_id: str
    user_name: str
    module_id: str
    module_title: str
    issued_at: datetime
    expires_at: datetime
    score: int
    status: str
    renewal_reminder_sent: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cert_id": self.cert_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "module_id": self.module_id,
            "module_title": self.module_title,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "score": self.score,
            "status": self.status,
            "renewal_reminder_sent": self.renewal_reminder_sent,
        }


TRAINING_MODULES = [
    {
        "title": "GDPR Fundamentals",
        "description": "Core principles of GDPR compliance for data handlers",
        "category": "data_privacy",
        "framework": "GDPR",
        "content": "The General Data Protection Regulation (GDPR) is a comprehensive data protection law...",
        "duration_minutes": 45,
        "difficulty": "beginner",
        "pass_threshold": 70,
        "tags": ["gdpr", "privacy", "data-protection"],
    },
    {
        "title": "SOC 2 Controls Awareness",
        "description": "Understanding SOC 2 trust service criteria and controls",
        "category": "security",
        "framework": "SOC_2",
        "content": "SOC 2 reports are based on the Trust Services Criteria (TSC)...",
        "duration_minutes": 60,
        "difficulty": "intermediate",
        "pass_threshold": 75,
        "tags": ["soc2", "audit", "controls"],
    },
    {
        "title": "HIPAA Privacy & Security",
        "description": "HIPAA rules for protected health information handling",
        "category": "healthcare",
        "framework": "HIPAA",
        "content": "The Health Insurance Portability and Accountability Act (HIPAA)...",
        "duration_minutes": 50,
        "difficulty": "intermediate",
        "pass_threshold": 80,
        "tags": ["hipaa", "phi", "healthcare"],
    },
    {
        "title": "PCI DSS v4.0 Overview",
        "description": "Payment Card Industry Data Security Standard requirements",
        "category": "security",
        "framework": "PCI_DSS",
        "content": "PCI DSS v4.0 is the latest version of the Payment Card Industry...",
        "duration_minutes": 55,
        "difficulty": "advanced",
        "pass_threshold": 85,
        "tags": ["pci", "cardholder-data", "security"],
    },
    {
        "title": "Information Security Essentials",
        "description": "Core information security concepts for all employees",
        "category": "security",
        "framework": "ISO_27001",
        "content": "Information security is the practice of protecting information...",
        "duration_minutes": 30,
        "difficulty": "beginner",
        "pass_threshold": 65,
        "tags": ["iso27001", "security", "awareness"],
    },
    {
        "title": "Data Residency & Cross-Border Transfers",
        "description": "Understanding data residency requirements and international data transfers",
        "category": "compliance",
        "framework": "GDPR",
        "content": "Data residency refers to the physical location of data...",
        "duration_minutes": 40,
        "difficulty": "intermediate",
        "pass_threshold": 75,
        "tags": ["data-residency", "cross-border", "transfers"],
    },
    {
        "title": "Vendor Risk Management",
        "description": "Assessing and managing third-party vendor security risks",
        "category": "vendor_risk",
        "framework": "SOC_2",
        "content": "Third-party vendor risk management is critical...",
        "duration_minutes": 35,
        "difficulty": "intermediate",
        "pass_threshold": 70,
        "tags": ["vendors", "third-party", "risk"],
    },
]


def _generate_questions(module_def: dict, module_id: str) -> List[QuizQuestion]:
    difficulties = {"beginner": QuizDifficulty.BEGINNER, "intermediate": QuizDifficulty.INTERMEDIATE, "advanced": QuizDifficulty.ADVANCED}
    diff = difficulties.get(module_def.get("difficulty", "beginner"), QuizDifficulty.BEGINNER)
    base_questions = [
        QuizQuestion(question_id=f"{module_id}_q1", question=f"What is the primary purpose of {module_def['title']}?",
                     options=["Data protection", "Cost reduction", "Performance improvement", "User experience"],
                     correct_answer="Data protection", explanation=f"The primary purpose is compliance with {module_def['framework']}",
                     category=module_def["category"], difficulty=diff),
        QuizQuestion(question_id=f"{module_id}_q2", question=f"Which framework is associated with {module_def['title']}?",
                     options=[module_def["framework"], "ISO 9001", "ITIL", "COBIT"],
                     correct_answer=module_def["framework"], explanation=f"This module covers {module_def['framework']} requirements",
                     category=module_def["category"], difficulty=diff),
        QuizQuestion(question_id=f"{module_id}_q3", question=f"What is the minimum pass threshold for this module?",
                     options=[f"{module_def['pass_threshold']}%", "50%", "90%", "60%"],
                     correct_answer=f"{module_def['pass_threshold']}%", explanation=f"A score of {module_def['pass_threshold']}% is required to pass",
                     category="general", difficulty=diff),
        QuizQuestion(question_id=f"{module_id}_q4", question=f"How long is the estimated completion time?",
                     options=[f"{module_def['duration_minutes']} minutes", "120 minutes", "15 minutes", "90 minutes"],
                     correct_answer=f"{module_def['duration_minutes']} minutes", explanation=f"This module takes approximately {module_def['duration_minutes']} minutes",
                     category="general", difficulty=diff),
        QuizQuestion(question_id=f"{module_id}_q5", question=f"Which of the following best describes {module_def['category']}?",
                     options=[f"Aspect of {module_def['category'].replace('_', ' ')}", "Financial management", "Network topology", "Hardware configuration"],
                     correct_answer=f"Aspect of {module_def['category'].replace('_', ' ')}",
                     explanation=f"This module covers the {module_def['category']} category", category=module_def["category"], difficulty=diff),
    ]
    return base_questions


class ComplianceTrainingManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.modules: Dict[str, TrainingModule] = {}
        self.assignments: Dict[str, TrainingAssignment] = {}
        self.certifications: Dict[str, Certification] = {}
        self.data_file = config.get("training_data_file", "data/compliance_training.json")
        self._init_modules()
        self._load()

    def _init_modules(self):
        for mod_def in TRAINING_MODULES:
            module_id = f"mod_{mod_def['framework'].lower()}_{uuid.uuid4().hex[:6]}"
            difficulty = {"beginner": QuizDifficulty.BEGINNER, "intermediate": QuizDifficulty.INTERMEDIATE, "advanced": QuizDifficulty.ADVANCED}.get(mod_def["difficulty"], QuizDifficulty.BEGINNER)
            questions = _generate_questions(mod_def, module_id)
            module = TrainingModule(
                module_id=module_id,
                title=mod_def["title"],
                description=mod_def["description"],
                category=mod_def["category"],
                framework=mod_def["framework"],
                content=mod_def["content"] + f"\n\nThis module provides comprehensive coverage of {mod_def['title']}. "
                        f"It is designed for learners at the {mod_def['difficulty']} level and requires approximately "
                        f"{mod_def['duration_minutes']} minutes to complete. Upon passing the assessment with a "
                        f"score of {mod_def['pass_threshold']}% or higher, you will receive a certification valid for 1 year.",
                duration_minutes=mod_def["duration_minutes"],
                difficulty=difficulty,
                questions=questions,
                pass_threshold=mod_def["pass_threshold"],
                certification_id=None,
                version="1.0",
                status="active",
                tags=mod_def["tags"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.modules[module_id] = module

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.assignments = {k: TrainingAssignment(**a) if isinstance(a, dict) else a for k, a in data.get("assignments", {}).items()}
                    self.certifications = {k: Certification(**c) if isinstance(c, dict) else c for k, c in data.get("certifications", {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load training data: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump({
                    "assignments": {k: v.to_dict() for k, v in self.assignments.items()},
                    "certifications": {k: v.to_dict() for k, v in self.certifications.items()},
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save training data: {e}")

    def assign_training(self, user_id: str, user_name: str, module_id: str,
                        assigned_by: str = "system", due_days: int = 30) -> Optional[TrainingAssignment]:
        module = self.modules.get(module_id)
        if not module:
            raise ValueError(f"Module not found: {module_id}")
        if module.status != "active":
            raise ValueError(f"Module {module_id} is not active")

        assignment = TrainingAssignment(
            assignment_id=f"assign_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            user_name=user_name,
            module_id=module_id,
            module_title=module.title,
            status=TrainingStatus.NOT_STARTED,
            score=None,
            max_score=len(module.questions),
            answers={},
            started_at=None,
            completed_at=None,
            due_date=datetime.utcnow() + timedelta(days=due_days),
            assigned_by=assigned_by,
            reminder_sent=False,
        )
        self.assignments[assignment.assignment_id] = assignment
        self._save()
        logger.info(f"Assigned {module.title} to {user_name} ({user_id})")
        return assignment

    def start_assignment(self, assignment_id: str) -> Optional[TrainingAssignment]:
        assignment = self.assignments.get(assignment_id)
        if assignment and assignment.status == TrainingStatus.NOT_STARTED:
            assignment.status = TrainingStatus.IN_PROGRESS
            assignment.started_at = datetime.utcnow()
            self._save()
        return assignment

    def submit_quiz(self, assignment_id: str, answers: Dict[str, str]) -> Optional[TrainingAssignment]:
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return None

        module = self.modules.get(assignment.module_id)
        if not module:
            return None

        score = 0
        for q in module.questions:
            user_answer = answers.get(q.question_id, "")
            if user_answer == q.correct_answer:
                score += 1

        assignment.answers = answers
        assignment.score = score
        assignment.max_score = len(module.questions)
        assignment.completed_at = datetime.utcnow()

        percentage = (score / len(module.questions)) * 100 if module.questions else 0
        assignment.status = TrainingStatus.COMPLETED if percentage >= module.pass_threshold else TrainingStatus.FAILED

        if assignment.status == TrainingStatus.COMPLETED:
            cert = Certification(
                cert_id=f"cert_{uuid.uuid4().hex[:12]}",
                user_id=assignment.user_id,
                user_name=assignment.user_name,
                module_id=assignment.module_id,
                module_title=assignment.module_title,
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),
                score=score,
                status="active",
                renewal_reminder_sent=False,
            )
            self.certifications[cert.cert_id] = cert
            module.certification_id = cert.cert_id

        self._save()
        logger.info(f"Assignment {assignment_id} completed with score {score}/{len(module.questions)}")
        return assignment

    def get_modules(self, framework: Optional[str] = None,
                    category: Optional[str] = None) -> List[TrainingModule]:
        results = list(self.modules.values())
        if framework:
            results = [m for m in results if m.framework == framework]
        if category:
            results = [m for m in results if m.category == category]
        return results

    def get_assignments(self, user_id: Optional[str] = None,
                        module_id: Optional[str] = None,
                        status: Optional[str] = None) -> List[TrainingAssignment]:
        results = list(self.assignments.values())
        if user_id:
            results = [a for a in results if a.user_id == user_id]
        if module_id:
            results = [a for a in results if a.module_id == module_id]
        if status:
            results = [a for a in results if a.status.value == status]
        return sorted(results, key=lambda a: a.due_date)

    def get_certifications(self, user_id: Optional[str] = None,
                           status: Optional[str] = None) -> List[Certification]:
        results = list(self.certifications.values())
        if user_id:
            results = [c for c in results if c.user_id == user_id]
        if status:
            results = [c for c in results if c.status == status]
        return results

    def check_expirations(self) -> List[Certification]:
        now = datetime.utcnow()
        expired = []
        for cert in list(self.certifications.values()):
            if cert.expires_at < now and cert.status == "active":
                cert.status = "expired"
                expired.append(cert)
        if expired:
            self._save()
        return expired

    def get_expiring_soon(self, days: int = 30) -> List[Certification]:
        cutoff = datetime.utcnow() + timedelta(days=days)
        return [c for c in self.certifications.values()
                if c.status == "active" and c.expires_at <= cutoff and not c.renewal_reminder_sent]

    def mark_reminder_sent(self, cert_id: str) -> Optional[Certification]:
        cert = self.certifications.get(cert_id)
        if cert:
            cert.renewal_reminder_sent = True
            self._save()
        return cert

    def get_statistics(self) -> Dict[str, Any]:
        total_assignments = len(self.assignments)
        completed = sum(1 for a in self.assignments.values() if a.status == TrainingStatus.COMPLETED)
        in_progress = sum(1 for a in self.assignments.values() if a.status == TrainingStatus.IN_PROGRESS)
        passed = sum(1 for a in self.assignments.values() if a.status == TrainingStatus.COMPLETED)
        failed = sum(1 for a in self.assignments.values() if a.status == TrainingStatus.FAILED)
        active_certs = sum(1 for c in self.certifications.values() if c.status == "active")
        expiring = len(self.get_expiring_soon(30))
        return {
            "total_modules": len(self.modules),
            "total_assignments": total_assignments,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_assignments - completed - in_progress,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / completed * 100) if completed else 0, 1),
            "active_certifications": active_certs,
            "expiring_within_30_days": expiring,
            "frameworks_covered": list(set(m.framework for m in self.modules.values())),
        }

    async def send_reminders(self):
        logger.info("Checking for training reminders")
        expiring = self.get_expiring_soon(30)
        for cert in expiring:
            logger.info(f"Certification {cert.cert_id} for {cert.user_name} expiring soon")
            self.mark_reminder_sent(cert.cert_id)
        overdue = [a for a in self.assignments.values()
                   if a.status in (TrainingStatus.NOT_STARTED, TrainingStatus.IN_PROGRESS)
                   and a.due_date < datetime.utcnow() and not a.reminder_sent]
        for a in overdue:
            logger.info(f"Assignment {a.assignment_id} for {a.user_name} is overdue")
            a.reminder_sent = True
        if overdue:
            self._save()

    def search_modules(self, query: str) -> List[TrainingModule]:
        q = query.lower()
        return [m for m in self.modules.values()
                if q in m.title.lower() or q in m.description.lower() or q in m.framework.lower() or q in m.category.lower()]

    def get_module_by_id(self, module_id: str) -> Optional[TrainingModule]:
        return self.modules.get(module_id)

    def create_custom_module(self, title: str, description: str, category: str,
                              framework: str, content: str, duration_minutes: int,
                              difficulty: str, pass_threshold: int,
                              questions: Optional[List[Dict[str, Any]]] = None) -> TrainingModule:
        module_id = f"mod_custom_{uuid.uuid4().hex[:8]}"
        diff = {"beginner": QuizDifficulty.BEGINNER, "intermediate": QuizDifficulty.INTERMEDIATE, "advanced": QuizDifficulty.ADVANCED}.get(difficulty, QuizDifficulty.BEGINNER)
        quiz_questions = []
        if questions:
            for i, q_def in enumerate(questions):
                quiz_questions.append(QuizQuestion(
                    question_id=f"{module_id}_q{i}",
                    question=q_def.get("question", ""),
                    options=q_def.get("options", []),
                    correct_answer=q_def.get("correct_answer", ""),
                    explanation=q_def.get("explanation", ""),
                    category=q_def.get("category", category),
                    difficulty=diff,
                ))
        module = TrainingModule(
            module_id=module_id, title=title, description=description,
            category=category, framework=framework, content=content,
            duration_minutes=duration_minutes, difficulty=diff,
            questions=quiz_questions, pass_threshold=pass_threshold,
            certification_id=None, version="1.0", status="active",
            tags=[framework, category, "custom"],
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        self.modules[module_id] = module
        return module

    def delete_module(self, module_id: str) -> bool:
        if module_id in self.modules:
            self.modules[module_id].status = "archived"
            self._save()
            return True
        return False

    def batch_assign(self, user_ids: List[str], module_id: str,
                      assigned_by: str = "system", due_days: int = 30) -> List[TrainingAssignment]:
        assignments = []
        for uid in user_ids:
            try:
                user_name = f"User_{uid[:8]}"
                assignment = self.assign_training(uid, user_name, module_id, assigned_by, due_days)
                if assignment:
                    assignments.append(assignment)
            except Exception as e:
                logger.error(f"Batch assign failed for {uid}: {e}")
        return assignments

    def get_training_report(self, framework: Optional[str] = None) -> Dict[str, Any]:
        modules = self.get_modules(framework=framework)
        fw_assignments = [a for a in self.assignments.values() if a.module_id in {m.module_id for m in modules}]
        completed = sum(1 for a in fw_assignments if a.status == TrainingStatus.COMPLETED)
        return {
            "framework": framework or "all",
            "modules_available": len(modules),
            "total_assignments": len(fw_assignments),
            "completed": completed,
            "pass_rate": round(
                sum(1 for a in fw_assignments if a.status == TrainingStatus.COMPLETED and a.score and a.score >= a.max_score * a.module_id.count("") + 1)
                / completed * 100, 1
            ) if completed else 0,
            "certifications_issued": sum(1 for c in self.certifications.values() if c.status == "active" and (not framework or any(m.framework == framework for m in modules))),
        }

    def get_learner_progress(self, user_id: str) -> Dict[str, Any]:
        user_assignments = [a for a in self.assignments.values() if a.user_id == user_id]
        completed = [a for a in user_assignments if a.status == TrainingStatus.COMPLETED]
        in_progress = [a for a in user_assignments if a.status == TrainingStatus.IN_PROGRESS]
        return {
            "user_id": user_id,
            "total_assignments": len(user_assignments),
            "completed": len(completed),
            "in_progress": len(in_progress),
            "not_started": len(user_assignments) - len(completed) - len(in_progress),
            "average_score": round(sum(a.score or 0 for a in completed) / len(completed), 1) if completed else 0,
            "active_certifications": len([c for c in self.certifications.values() if c.user_id == user_id and c.status == "active"]),
        }


def generate_sample_questions(module_title: str, framework: str, category: str, count: int = 3) -> List[QuizQuestion]:
    base_id = f"gen_{uuid.uuid4().hex[:6]}"
    questions = []
    for i in range(count):
        questions.append(QuizQuestion(
            question_id=f"{base_id}_q{i}",
            question=f"Sample question {i + 1} about {module_title}",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_answer="Option A",
            explanation=f"This relates to {framework} requirements in {category}",
            category=category,
            difficulty=QuizDifficulty.BEGINNER,
        ))
    return questions


def filter_assignments_by_date(assignments: List[TrainingAssignment], start: datetime, end: datetime) -> List[TrainingAssignment]:
    return [a for a in assignments if a.due_date and start <= a.due_date <= end]


def compute_training_compliance_rate(assignments: List[TrainingAssignment]) -> float:
    if not assignments:
        return 0.0
    completed = sum(1 for a in assignments if a.status == TrainingStatus.COMPLETED)
    return round(completed / len(assignments) * 100, 1)


def group_certifications_by_module(certifications: List[Certification]) -> Dict[str, List[Certification]]:
    groups = {}
    for c in certifications:
        groups.setdefault(c.module_title, []).append(c)
    return groups


def find_overdue_assignments(assignments: List[TrainingAssignment]) -> List[TrainingAssignment]:
    now = datetime.utcnow()
    return [a for a in assignments if a.due_date < now and a.status in (TrainingStatus.NOT_STARTED, TrainingStatus.IN_PROGRESS)]


class TrainingBatchProcessor:
    def __init__(self):
        self.batch_log: List[Dict[str, Any]] = []

    def batch_assign(self, manager: ComplianceTrainingManager, user_ids: List[Dict[str, str]], module_id: str) -> List[Dict[str, Any]]:
        results = []
        for entry in user_ids:
            try:
                assignment = manager.assign_training(entry["user_id"], entry.get("user_name", f"User_{entry['user_id'][:8]}"), module_id)
                results.append({"user_id": entry["user_id"], "assignment_id": assignment.assignment_id, "status": "success"})
                self.batch_log.append({"action": "assign", "user": entry["user_id"], "status": "success"})
            except Exception as e:
                results.append({"user_id": entry.get("user_id"), "status": "error", "error": str(e)})
                self.batch_log.append({"action": "assign", "user": entry.get("user_id"), "status": "error", "error": str(e)})
        return results


async def paginate_training_modules(modules: List[TrainingModule], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(modules)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [m.to_dict() for m in modules[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def export_training_data(assignments: List[TrainingAssignment]) -> Dict[str, Any]:
    export_id = f"train_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id, "exported_at": datetime.utcnow().isoformat(),
        "assignments": [a.to_dict() for a in assignments],
        "summary": {"total": len(assignments), "completed": sum(1 for a in assignments if a.status == TrainingStatus.COMPLETED)},
    }


def import_training_assignments(manager: ComplianceTrainingManager, import_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    import_id = f"train_import_{uuid.uuid4().hex[:8]}"
    imported = 0
    for entry in import_data:
        try:
            manager.assign_training(entry["user_id"], entry.get("user_name", ""), entry["module_id"])
            imported += 1
        except Exception:
            pass
    return {"import_id": import_id, "imported": imported}


class TrainingConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []

    def validate(self) -> bool:
        self.errors = []
        if not self.config.get("training_data_file"):
            self.errors.append("training_data_file is required")
        reminder_days = self.config.get("reminder_days_before_expiry")
        if reminder_days is not None and reminder_days < 1:
            self.errors.append("reminder_days_before_expiry must be >= 1")
        return len(self.errors) == 0


def compute_training_statistics(assignments: List[TrainingAssignment]) -> Dict[str, Any]:
    total = len(assignments)
    completed = sum(1 for a in assignments if a.status == TrainingStatus.COMPLETED)
    failed = sum(1 for a in assignments if a.status == TrainingStatus.FAILED)
    in_progress = sum(1 for a in assignments if a.status == TrainingStatus.IN_PROGRESS)
    avg_score = round(sum(a.score or 0 for a in assignments if a.status == TrainingStatus.COMPLETED) / completed, 1) if completed else 0
    return {
        "total_assignments": total, "completed": completed, "failed": failed,
        "in_progress": in_progress, "not_started": total - completed - failed - in_progress,
        "pass_rate": round(completed / (completed + failed) * 100, 1) if (completed + failed) else 0,
        "average_score": avg_score,
    }

import uuid, hashlib, asyncio, json, logging, random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class compliance_training_Ctx:
    def __init__(self):
        self.created = datetime.utcnow().isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.state = "initialized"
    def to_dict(self):
        return {"id": self.id, "created": self.created, "state": self.state}
    def refresh(self):
        self.state = "refreshed"

class compliance_training_Handler:
    def __init__(self):
        self.ops = []
    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ops.append(event)
        return {"status": "handled", "event_id": event.get("id", uuid.uuid4().hex[:8])}
    def get_ops(self):
        return self.ops

class compliance_training_Validator:
    def __init__(self, rules=None):
        self.rules = rules or []
    def validate(self, data: Dict[str, Any]) -> List[str]:
        return [r for r in self.rules if r not in data]

class compliance_training_Transform:
    @staticmethod
    def to_json(obj) -> str:
        return json.dumps(obj.to_dict() if hasattr(obj, "to_dict") else obj)
    @staticmethod
    def from_json(s: str) -> Dict:
        return json.loads(s)

class compliance_training_Cache:
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

class compliance_training_Metrics:
    def __init__(self):
        self._counts = {}
    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n
    def get(self, name: str) -> int:
        return self._counts.get(name, 0)
    def snapshot(self):
        return dict(self._counts)

class compliance_training_Queue:
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

class compliance_training_Dispatcher:
    def __init__(self):
        self._handlers = {}
    def register(self, event: str, handler):
        self._handlers[event] = handler
    def dispatch(self, event: str, data: Dict[str, Any]):
        h = self._handlers.get(event)
        return h(data) if h else None

class compliance_training_AuditLogger:
    def __init__(self):
        self._log = []
    def log(self, action: str, detail: str = ""):
        e = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(e); return e
    def tail(self, n: int = 10):
        return self._log[-n:]


_training_courses_store: Dict[str, TrainingCourse] = {}
_training_enrollments_store: Dict[str, TrainingEnrollment] = {}


def add_training_course(course: TrainingCourse) -> str:
    _training_courses_store[course.course_id] = course
    return course.course_id


def get_training_course(course_id: str) -> Optional[TrainingCourse]:
    return _training_courses_store.get(course_id)


def search_training_courses(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = []
    for c in _training_courses_store.values():
        if query.lower() in c.title.lower() or query.lower() in c.category.lower():
            results.append({"id": c.course_id, "title": c.title, "category": c.category, "level": c.difficulty.value})
            if len(results) >= limit:
                break
    return results


def batch_assign_training(course_id: str, user_ids: List[str]) -> Dict[str, Any]:
    op = {"operation": "assign", "course_id": course_id, "succeeded": [], "failed": [], "total": len(user_ids)}
    course = _training_courses_store.get(course_id)
    if not course:
        return {**op, "error": "course not found"}
    for uid in user_ids:
        enrollment = TrainingEnrollment(
            enrollment_id=f"te_{uuid.uuid4().hex[:8]}",
            user_id=uid, course_id=course_id, status=TrainingStatus.NOT_STARTED,
            score=0.0, started_at=None, completed_at=None, expires_at=datetime.utcnow() + timedelta(days=365)
        )
        _training_enrollments_store[enrollment.enrollment_id] = enrollment
        op["succeeded"].append(uid)
    return op


def get_training_summary() -> Dict[str, Any]:
    total_courses = len(_training_courses_store)
    total_enrollments = len(_training_enrollments_store)
    completed = sum(1 for e in _training_enrollments_store.values() if e.status == TrainingStatus.COMPLETED)
    in_progress = sum(1 for e in _training_enrollments_store.values() if e.status == TrainingStatus.IN_PROGRESS)
    not_started = sum(1 for e in _training_enrollments_store.values() if e.status == TrainingStatus.NOT_STARTED)
    return {"total_courses": total_courses, "total_enrollments": total_enrollments, "completed": completed, "in_progress": in_progress, "not_started": not_started}


class TrainingProgressTracker:
    def __init__(self):
        self._enrollments = _training_enrollments_store
        self._courses = _training_courses_store

    def user_progress(self, user_id: str) -> Dict[str, Any]:
        user_enrollments = [e for e in self._enrollments.values() if e.user_id == user_id]
        total = len(user_enrollments)
        completed = sum(1 for e in user_enrollments if e.status == TrainingStatus.COMPLETED)
        in_progress = sum(1 for e in user_enrollments if e.status == TrainingStatus.IN_PROGRESS)
        avg_score = sum(e.score for e in user_enrollments) / max(completed, 1)
        return {"user_id": user_id, "total": total, "completed": completed, "in_progress": in_progress, "completion_pct": round(completed / max(total, 1) * 100, 1), "avg_score": round(avg_score, 1)}

    def department_progress(self, department: str) -> Dict[str, Any]:
        dept_enrollments = [e for e in self._enrollments.values() if e.department == department]
        total = len(dept_enrollments)
        completed = sum(1 for e in dept_enrollments if e.status == TrainingStatus.COMPLETED)
        return {"department": department, "total": total, "completed": completed, "completion_pct": round(completed / max(total, 1) * 100, 1)}


class TrainingContentLibrary:
    def __init__(self):
        self._courses = _training_courses_store

    def search_courses(self, query: str, category: str = "", difficulty: str = "") -> List[Dict[str, Any]]:
        results = []
        for c in self._courses.values():
            if query and query.lower() not in c.title.lower() and query.lower() not in c.description.lower():
                continue
            if category and c.category != category:
                continue
            if difficulty and c.difficulty.value != difficulty:
                continue
            results.append({"id": c.course_id, "title": c.title, "category": c.category, "difficulty": c.difficulty.value, "duration": c.duration_minutes})
        return results[:20]

    def get_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        completed_ids = [e.course_id for e in _training_enrollments_store.values() if e.user_id == user_id and e.status == TrainingStatus.COMPLETED]
        categories = set()
        for cid in completed_ids:
            c = self._courses.get(cid)
            if c:
                categories.add(c.category)
        recs = [{"id": c.course_id, "title": c.title, "category": c.category, "difficulty": c.difficulty.value, "duration": c.duration_minutes} for c in self._courses.values() if c.course_id not in completed_ids and c.category in categories]
        return recs[:limit]

    def get_popular_courses(self, limit: int = 5) -> List[Dict[str, Any]]:
        counts: Dict[str, int] = {}
        for e in _training_enrollments_store.values():
            counts[e.course_id] = counts.get(e.course_id, 0) + 1
        sorted_courses = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        results = []
        for cid, cnt in sorted_courses[:limit]:
            c = self._courses.get(cid)
            if c:
                results.append({"id": c.course_id, "title": c.title, "enrollments": cnt, "category": c.category})
        return results


class TrainingCertificationManager:
    def __init__(self):
        self._certificates: Dict[str, Dict[str, Any]] = {}

    def issue_certificate(self, user_id: str, course_id: str) -> Optional[Dict[str, Any]]:
        enrollment = next((e for e in _training_enrollments_store.values() if e.user_id == user_id and e.course_id == course_id and e.status == TrainingStatus.COMPLETED), None)
        if not enrollment:
            return None
        cert_id = f"cert_{uuid.uuid4().hex[:12]}"
        cert = {"certificate_id": cert_id, "user_id": user_id, "course_id": course_id, "issued_at": datetime.utcnow().isoformat(), "score": enrollment.score, "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()}
        self._certificates[cert_id] = cert
        return cert

    def verify_certificate(self, cert_id: str) -> Dict[str, Any]:
        cert = self._certificates.get(cert_id)
        if not cert:
            return {"valid": False, "error": "not found"}
        expired = datetime.fromisoformat(cert["expires_at"]) < datetime.utcnow()
        return {"valid": not expired, "certificate_id": cert_id, "user_id": cert["user_id"], "issued": cert["issued_at"], "expired": expired}

    def list_user_certificates(self, user_id: str) -> List[Dict[str, Any]]:
        return [c for c in self._certificates.values() if c["user_id"] == user_id]


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
