"""Customer onboarding wizard with step-by-step guided setup and progress tracking."""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class StepType(str, Enum):
    SETUP = "setup"
    TOUR = "tour"
    TASK = "task"
    VIDEO = "video"
    DOCS = "docs"
    INTEGRATION = "integration"
    VERIFICATION = "verification"


@dataclass
class OnboardingStep:
    step_id: str
    title: str
    description: str
    step_type: StepType
    order: int
    required: bool = True
    estimated_minutes: int = 5
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    completed_at: Optional[str] = None
    started_at: Optional[str] = None
    skipped_at: Optional[str] = None
    progress_pct: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None
    video_url: Optional[str] = None
    guide_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingMilestone:
    milestone_id: str
    name: str
    description: str
    required_steps: List[str]
    achieved: bool = False
    achieved_at: Optional[str] = None
    progress_pct: float = 0.0
    reward_badge: Optional[str] = None
    celebration_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingSession:
    session_id: str
    customer_id: str
    customer_name: str
    product_tier: str = "standard"
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    steps: List[OnboardingStep] = field(default_factory=list)
    milestones: List[OnboardingMilestone] = field(default_factory=list)
    overall_progress: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    time_to_value_days: Optional[float] = None
    current_step_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "product_tier": self.product_tier,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "milestones": [m.to_dict() for m in self.milestones],
            "overall_progress": self.overall_progress,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "time_to_value_days": self.time_to_value_days,
            "current_step_id": self.current_step_id,
            "preferences": self.preferences,
            "tags": self.tags,
            "version": self.version,
        }


TEMPLATE_STEPS = [
    OnboardingStep("step-welcome", "Welcome & Introduction", "Quick overview of the platform and what you can achieve", StepType.TOUR, 1, estimated_minutes=3),
    OnboardingStep("step-profile", "Complete Your Profile", "Add your company details, team name, and preferences", StepType.SETUP, 2, estimated_minutes=5),
    OnboardingStep("step-first-resource", "Create Your First Resource", "Deploy your first server, database, or application", StepType.TASK, 3, estimated_minutes=10),
    OnboardingStep("step-team", "Invite Team Members", "Collaborate with your team by inviting members", StepType.SETUP, 4, estimated_minutes=3),
    OnboardingStep("step-monitoring", "Set Up Monitoring", "Configure alerts, health checks, and notifications", StepType.SETUP, 5, estimated_minutes=8),
    OnboardingStep("step-backup", "Configure Backup", "Set up automated backups for your resources", StepType.SETUP, 6, estimated_minutes=5),
    OnboardingStep("step-integration", "Connect Integrations", "Link your tools: Slack, GitHub, PagerDuty, etc.", StepType.INTEGRATION, 7, estimated_minutes=10),
    OnboardingStep("step-api", "API Access Setup", "Generate API keys and explore our API documentation", StepType.SETUP, 8, estimated_minutes=5),
    OnboardingStep("step-video-tour", "Video Walkthrough", "Watch a guided tour of advanced features", StepType.VIDEO, 9, required=False, estimated_minutes=8),
    OnboardingStep("step-first-deploy", "First Deployment", "Deploy a real project or application end-to-end", StepType.TASK, 10, estimated_minutes=15),
    OnboardingStep("step-billing", "Billing Setup", "Configure payment method and review your plan", StepType.SETUP, 11, estimated_minutes=5),
    OnboardingStep("step-final-review", "Final Review & Complete", "Review your setup and mark onboarding as complete", StepType.VERIFICATION, 12, estimated_minutes=2),
]

MILESTONE_DEFS = [
    OnboardingMilestone("milestone-started", "First Steps", "Complete your profile and create first resource", ["step-welcome", "step-profile", "step-first-resource"], reward_badge="🚀", celebration_message="You're off to a great start!"),
    OnboardingMilestone("milestone-collaboration", "Team Player", "Invite team members and set up integrations", ["step-team", "step-integration"], reward_badge="🤝", celebration_message="Teamwork makes the dream work!"),
    OnboardingMilestone("milestone-production", "Production Ready", "Set up monitoring, backups, and billing", ["step-monitoring", "step-backup", "step-billing"], reward_badge="🛡️", celebration_message="Your infrastructure is production-ready!"),
    OnboardingMilestone("milestone-complete", "Onboarding Complete", "Finish all required onboarding steps", ["step-final-review"], reward_badge="🏆", celebration_message="Congratulations! Onboarding complete!"),
]


class OnboardingWizardService:
    def __init__(self, storage_path: str = "onboarding_data.json"):
        self.storage_path = storage_path
        self.sessions: Dict[str, OnboardingSession] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for sdata in data.get("sessions", []):
                        session = self._dict_to_session(sdata)
                        self.sessions[session.session_id] = session
            except Exception as e:
                logger.warning(f"Failed to load onboarding data: {e}")

    def _save_data(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump({"sessions": [s.to_dict() for s in self.sessions.values()]}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save onboarding data: {e}")

    def _dict_to_session(self, data: Dict[str, Any]) -> OnboardingSession:
        steps = [OnboardingStep(**s) for s in data.get("steps", [])]
        milestones = [OnboardingMilestone(**m) for m in data.get("milestones", [])]
        return OnboardingSession(
            session_id=data["session_id"],
            customer_id=data["customer_id"],
            customer_name=data.get("customer_name", ""),
            product_tier=data.get("product_tier", "standard"),
            status=OnboardingStatus(data.get("status", "not_started")),
            steps=steps,
            milestones=milestones,
            overall_progress=data.get("overall_progress", 0),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            time_to_value_days=data.get("time_to_value_days"),
            current_step_id=data.get("current_step_id"),
            preferences=data.get("preferences", {}),
            tags=data.get("tags", []),
            version=data.get("version", 1),
        )

    def start_onboarding(self, customer_id: str, customer_name: str = "", product_tier: str = "standard") -> OnboardingSession:
        session_id = f"OB-{uuid.uuid4().hex[:8].upper()}"
        steps = []
        for i, template in enumerate(TEMPLATE_STEPS):
            steps.append(OnboardingStep(
                step_id=template.step_id,
                title=template.title,
                description=template.description,
                step_type=template.step_type,
                order=i + 1,
                required=template.required,
                estimated_minutes=template.estimated_minutes,
                action_url=template.action_url,
                video_url=template.video_url,
                guide_text=template.guide_text,
            ))
        milestones = []
        for md in MILESTONE_DEFS:
            milestones.append(OnboardingMilestone(
                milestone_id=md.milestone_id,
                name=md.name,
                description=md.description,
                required_steps=list(md.required_steps),
                reward_badge=md.reward_badge,
                celebration_message=md.celebration_message,
            ))
        session = OnboardingSession(
            session_id=session_id,
            customer_id=customer_id,
            customer_name=customer_name,
            product_tier=product_tier,
            status=OnboardingStatus.IN_PROGRESS,
            steps=steps,
            milestones=milestones,
            started_at=datetime.utcnow().isoformat(),
            current_step_id=steps[0].step_id if steps else None,
        )
        if steps:
            steps[0].status = OnboardingStatus.IN_PROGRESS
            steps[0].started_at = datetime.utcnow().isoformat()
        self.sessions[session_id] = session
        self._save_data()
        return session

    def get_session(self, identifier: str) -> Optional[OnboardingSession]:
        if identifier in self.sessions:
            return self.sessions[identifier]
        for session in self.sessions.values():
            if session.customer_id == identifier:
                return session
        return None

    def update_step(self, session_id: str, step_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[OnboardingStep]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        step = next((s for s in session.steps if s.step_id == step_id), None)
        if not step:
            return None
        new_status = OnboardingStatus(status)
        now = datetime.utcnow().isoformat()
        step.status = new_status
        if new_status == OnboardingStatus.COMPLETED:
            step.completed_at = now
            if not step.started_at:
                step.started_at = now
            step.progress_pct = 100.0
        elif new_status == OnboardingStatus.IN_PROGRESS:
            step.started_at = step.started_at or now
            step.progress_pct = metadata.get("progress", step.progress_pct) if metadata else step.progress_pct
        elif new_status == OnboardingStatus.SKIPPED:
            step.skipped_at = now
        if metadata:
            step.metadata.update(metadata)
        session.current_step_id = self._get_next_step(session)
        self._recalculate_progress(session)
        self._check_milestones(session)
        self._check_completion(session)
        self._save_data()
        return step

    def _get_next_step(self, session: OnboardingSession) -> Optional[str]:
        for step in session.steps:
            if step.status == OnboardingStatus.NOT_STARTED:
                return step.step_id
            if step.status == OnboardingStatus.IN_PROGRESS:
                return step.step_id
        return None

    def _recalculate_progress(self, session: OnboardingSession):
        required_steps = [s for s in session.steps if s.required]
        completed = sum(1 for s in required_steps if s.status == OnboardingStatus.COMPLETED)
        in_progress = sum(0.5 for s in required_steps if s.status == OnboardingStatus.IN_PROGRESS)
        total = len(required_steps)
        session.overall_progress = round((completed + in_progress) / total * 100, 1) if total > 0 else 0

    def _check_milestones(self, session: OnboardingSession):
        for milestone in session.milestones:
            if milestone.achieved:
                continue
            step_ids = {s.step_id for s in session.steps if s.status == OnboardingStatus.COMPLETED}
            required = set(milestone.required_steps)
            if required.issubset(step_ids):
                milestone.achieved = True
                milestone.achieved_at = datetime.utcnow().isoformat()
                milestone.progress_pct = 100.0

    def _check_completion(self, session: OnboardingSession):
        required = [s for s in session.steps if s.required]
        all_completed = all(s.status == OnboardingStatus.COMPLETED for s in required)
        if all_completed and session.status != OnboardingStatus.COMPLETED:
            session.status = OnboardingStatus.COMPLETED
            session.completed_at = datetime.utcnow().isoformat()
            started = datetime.fromisoformat(session.started_at) if session.started_at else datetime.utcnow()
            completed = datetime.fromisoformat(session.completed_at)
            session.time_to_value_days = round((completed - started).total_seconds() / 86400, 1)

    def advance_step(self, session_id: str, step_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[OnboardingStep]:
        return self.update_step(session_id, step_id, "completed", metadata)

    def update_preferences(self, session_id: str, preferences: Dict[str, Any]) -> Optional[OnboardingSession]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.preferences.update(preferences)
        self._save_data()
        return session

    def get_onboarding_stats(self) -> Dict[str, Any]:
        total = len(self.sessions)
        if not total:
            return {"total_sessions": 0, "completion_rate": 0}
        completed = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.COMPLETED)
        in_progress = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.IN_PROGRESS)
        not_started = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.NOT_STARTED)
        avg_ttv = None
        ttvs = [s.time_to_value_days for s in self.sessions.values() if s.time_to_value_days is not None]
        if ttvs:
            avg_ttv = round(sum(ttvs) / len(ttvs), 1)
        avg_progress = round(sum(s.overall_progress for s in self.sessions.values()) / total, 1)
        steps_completed = Counter()
        step_abandon = Counter()
        for s in self.sessions.values():
            for step in s.steps:
                if step.status == OnboardingStatus.COMPLETED:
                    steps_completed[step.step_id] += 1
                if step.status == OnboardingStatus.IN_PROGRESS:
                    step_abandon[step.step_id] += 1
        return {
            "total_sessions": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "completion_rate": round(completed / total, 3),
            "avg_progress_pct": avg_progress,
            "avg_time_to_value_days": avg_ttv,
        }

    def list_sessions(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        results = list(self.sessions.values())
        if status:
            results = [s for s in results if s.status.value == status]
        results.sort(key=lambda s: s.overall_progress)
        return [s.to_dict() for s in results[:limit]]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        return s.to_dict() if s else None

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_data()
            return True
        return False

    def complete_step(self, session_id: str, step_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s: return False
        for step in s.steps:
            if step.step_id == step_id and step.status != StepStatus.COMPLETED:
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow()
                break
        s.overall_progress = s.calculate_progress()
        if s.overall_progress >= 100:
            s.status = SessionStatus.COMPLETED
        self._save_data()
        return True

    def skip_step(self, session_id: str, step_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s: return False
        for step in s.steps:
            if step.step_id == step_id:
                step.status = StepStatus.SKIPPED
                break
        s.overall_progress = s.calculate_progress()
        self._save_data()
        return True

    def get_stuck_sessions(self, threshold_hours: int = 48) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
        stuck = [s for s in self.sessions.values() if s.last_activity < cutoff and s.status == SessionStatus.IN_PROGRESS and s.overall_progress < 100]
        return [s.to_dict() for s in sorted(stuck, key=lambda x: x.last_activity)[:20]]

    def get_step_completion_stats(self) -> Dict[str, Any]:
        step_stats = defaultdict(lambda: {"total": 0, "completed": 0, "skipped": 0})
        for s in self.sessions.values():
            for step in s.steps:
                step_stats[step.step_id]["total"] += 1
                if step.status == StepStatus.COMPLETED: step_stats[step.step_id]["completed"] += 1
                elif step.status == StepStatus.SKIPPED: step_stats[step.step_id]["skipped"] += 1
        return {k: {**v, "completion_rate": round(v["completed"] / max(v["total"], 1) * 100, 1)} for k, v in step_stats.items()}

    def get_abandonment_analysis(self) -> Dict[str, Any]:
        abandoned = [s for s in self.sessions.values() if s.status == SessionStatus.ABANDONED]
        step_breakdown = defaultdict(int)
        for s in abandoned:
            last_completed = max([step.step_id for step in s.steps if step.status == StepStatus.COMPLETED], default=None)
            if last_completed:
                step_breakdown[last_completed] += 1
        return {"total_abandoned": len(abandoned), "abandonment_rate": round(len(abandoned) / max(len(self.sessions), 1) * 100, 1), "last_step_before_abandon": dict(step_breakdown)}

    def get_time_to_complete(self) -> Dict[str, Any]:
        completed = [s for s in self.sessions.values() if s.status == SessionStatus.COMPLETED and s.completed_at and s.created_at]
        if not completed:
            return {"average_minutes": 0, "median_minutes": 0, "samples": 0}
        durations = [(s.completed_at - s.created_at).total_seconds() / 60 for s in completed]
        avg = sum(durations) / len(durations)
        sorted_durs = sorted(durations)
        median = sorted_durs[len(sorted_durs) // 2]
        return {"average_minutes": round(avg, 1), "median_minutes": round(median, 1), "min_minutes": round(min(durations), 1), "max_minutes": round(max(durations), 1), "samples": len(durations)}

    def get_onboarding_summary(self) -> Dict[str, Any]:
        total = len(self.sessions)
        completed = sum(1 for s in self.sessions.values() if s.status == SessionStatus.COMPLETED)
        in_progress = sum(1 for s in self.sessions.values() if s.status == SessionStatus.IN_PROGRESS)
        abandoned = sum(1 for s in self.sessions.values() if s.status == SessionStatus.ABANDONED)
        avg_progress = round(sum(s.overall_progress for s in self.sessions.values()) / max(total, 1), 1)
        return {"total_sessions": total, "completed": completed, "in_progress": in_progress, "abandoned": abandoned, "completion_rate": round(completed / max(total, 1) * 100, 1), "average_progress": avg_progress}

    def batch_create_sessions(self, customer_ids: List[str], template_id: Optional[str] = None) -> Dict[str, Any]:
        created = []
        errors = []
        for cid in customer_ids:
            try:
                s = self.create_session(customer_id=cid)
                created.append(s.get("session_id"))
            except Exception as e:
                errors.append({"customer_id": cid, "error": str(e)})
        return {"created": len(created), "session_ids": created, "errors": len(errors), "error_details": errors[:5]}

    def reorder_steps(self, session_id: str, step_ids: List[str]) -> bool:
        s = self.sessions.get(session_id)
        if not s: return False
        existing = {step.step_id: step for step in s.steps}
        reordered = []
        for sid in step_ids:
            if sid in existing:
                reordered.append(existing[sid])
        remaining = [step for step in s.steps if step.step_id not in step_ids]
        s.steps = reordered + remaining
        self._save_data()
        return True

    def estimate_completion(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s: return None
        completed_steps = sum(1 for step in s.steps if step.status == StepStatus.COMPLETED)
        total_steps = len(s.steps)
        if completed_steps == 0:
            return {"estimated_minutes_remaining": None, "progress": s.overall_progress}
        avg_time_per_step = ((datetime.utcnow() - s.created_at).total_seconds() / 60) / completed_steps
        remaining = total_steps - completed_steps
        return {"estimated_minutes_remaining": round(avg_time_per_step * remaining, 1), "progress": s.overall_progress, "avg_time_per_step_min": round(avg_time_per_step, 1)}

    def export_onboarding_report(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "sessions": [s.to_dict() for s in self.sessions.values()], "summary": self.get_onboarding_summary(), "step_stats": self.get_step_completion_stats(), "time_to_complete": self.get_time_to_complete()}

    def get_session_by_customer(self, customer_id: str) -> Optional[OnboardingSession]:
        return self.get_session(customer_id)

    def get_onboarding_flow(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        s = self.sessions.get(session_id)
        if not s:
            return None
        return [{"step_id": step.step_id, "title": step.title, "status": step.status.value, "order": step.order, "required": step.required, "estimated_minutes": step.estimated_minutes} for step in sorted(s.steps, key=lambda x: x.order)]

    def get_current_step(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s or not s.current_step_id:
            return None
        step = next((st for st in s.steps if st.step_id == s.current_step_id), None)
        return step.to_dict() if step else None

    def skip_step(self, session_id: str, step_id: str) -> Optional[OnboardingStep]:
        return self.update_step(session_id, step_id, "skipped")

    def get_completion_percentage(self, session_id: str) -> float:
        s = self.sessions.get(session_id)
        return s.overall_progress if s else 0.0

    def get_onboarding_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return []
        timeline = []
        for step in s.steps:
            entry = {"step_id": step.step_id, "title": step.title, "status": step.status.value, "order": step.order}
            if step.completed_at:
                entry["completed_at"] = step.completed_at
            if step.started_at:
                entry["started_at"] = step.started_at
            timeline.append(entry)
        timeline.sort(key=lambda x: x["order"])
        return timeline

    def get_milestone_progress(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return []
        return [{"milestone_id": m.milestone_id, "name": m.name, "achieved": m.achieved, "progress_pct": m.progress_pct, "celebration_message": m.celebration_message} for m in s.milestones]

    def get_stuck_sessions(self, threshold_hours: int = 48) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
        stuck = []
        for s in self.sessions.values():
            if s.status != OnboardingStatus.IN_PROGRESS:
                continue
            last_active = s.updated_at if hasattr(s, 'updated_at') else s.started_at
            if last_active and datetime.fromisoformat(last_active) < cutoff:
                stuck.append(s.to_dict())
        stuck.sort(key=lambda x: x.get("overall_progress", 0))
        return stuck[:20]

    def get_abandonment_rate(self) -> Dict[str, Any]:
        total = len(self.sessions)
        if not total:
            return {"rate": 0, "abandoned": 0, "total": 0}
        abandoned = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.NOT_STARTED and s.started_at)
        in_progress_old = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.IN_PROGRESS and s.started_at and datetime.fromisoformat(s.started_at) < datetime.utcnow() - timedelta(days=7))
        return {"abandonment_rate": round((abandoned + in_progress_old) / total * 100, 1), "abandoned": abandoned, "stale": in_progress_old, "total": total}

    def get_step_drop_off_rates(self) -> List[Dict[str, Any]]:
        step_stats = defaultdict(lambda: {"entered": 0, "completed": 0, "skipped": 0})
        for s in self.sessions.values():
            for step in s.steps:
                step_stats[step.step_id]["entered"] += 1
                if step.status == OnboardingStatus.COMPLETED:
                    step_stats[step.step_id]["completed"] += 1
                elif step.status == OnboardingStatus.SKIPPED:
                    step_stats[step.step_id]["skipped"] += 1
        return [
            {"step_id": sid, "entered": st["entered"], "completed": st["completed"], "drop_off_rate": round(1 - st["completed"] / max(st["entered"], 1), 3)}
            for sid, st in sorted(step_stats.items())
        ]

    def get_time_to_value_report(self) -> Dict[str, Any]:
        ttvs = [s.time_to_value_days for s in self.sessions.values() if s.time_to_value_days is not None]
        if not ttvs:
            return {"avg_ttv_days": 0, "median_ttv_days": 0, "min_ttv_days": 0, "max_ttv_days": 0, "samples": 0}
        return {
            "avg_ttv_days": round(sum(ttvs) / len(ttvs), 1),
            "median_ttv_days": sorted(ttvs)[len(ttvs) // 2],
            "min_ttv_days": min(ttvs),
            "max_ttv_days": max(ttvs),
            "samples": len(ttvs),
        }

    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        return s.preferences if s else {}

    def set_preferences(self, session_id: str, preferences: Dict[str, Any]) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        s.preferences.update(preferences)
        self._save_data()
        return True

    def get_session_notes(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return []
        return s.metadata.get("notes", [])

    def add_session_note(self, session_id: str, note: str, author: str = "system") -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        if "notes" not in s.metadata:
            s.metadata["notes"] = []
        s.metadata["notes"].append({"note": note, "author": author, "timestamp": datetime.utcnow().isoformat()})
        self._save_data()
        return True

    def batch_update_steps(self, session_id: str, step_updates: List[Dict[str, Any]]) -> int:
        count = 0
        for update in step_updates:
            result = self.update_step(session_id, update["step_id"], update.get("status", "completed"), update.get("metadata"))
            if result:
                count += 1
        return count

    def get_onboarding_effectiveness(self) -> Dict[str, Any]:
        total = len(self.sessions)
        completed = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.COMPLETED)
        avg_progress = round(sum(s.overall_progress for s in self.sessions.values()) / max(total, 1), 1)
        ttvs = [s.time_to_value_days for s in self.sessions.values() if s.time_to_value_days is not None]
        avg_ttv = round(sum(ttvs) / max(len(ttvs), 1), 1) if ttvs else None
        return {
            "total_sessions": total,
            "completion_rate": round(completed / max(total, 1) * 100, 1),
            "average_progress": avg_progress,
            "average_time_to_value_days": avg_ttv,
            "stuck_sessions": len(self.get_stuck_sessions()),
        }

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return None
        completed_steps = sum(1 for step in s.steps if step.status == OnboardingStatus.COMPLETED)
        total_steps = len(s.steps)
        required_steps = sum(1 for step in s.steps if step.required)
        completed_required = sum(1 for step in s.steps if step.required and step.status == OnboardingStatus.COMPLETED)
        return {
            "session_id": session_id,
            "customer_id": s.customer_id,
            "status": s.status.value,
            "progress": s.overall_progress,
            "steps_completed": f"{completed_steps}/{total_steps}",
            "required_completed": f"{completed_required}/{required_steps}",
            "milestones_achieved": sum(1 for m in s.milestones if m.achieved),
            "time_to_value_days": s.time_to_value_days,
            "current_step": self.get_current_step(session_id),
        }

    def reset_session(self, session_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        for step in s.steps:
            step.status = OnboardingStatus.NOT_STARTED
            step.completed_at = None
            step.started_at = None
            step.progress_pct = 0.0
        s.overall_progress = 0.0
        s.status = OnboardingStatus.IN_PROGRESS
        s.current_step_id = s.steps[0].step_id if s.steps else None
        if s.steps:
            s.steps[0].status = OnboardingStatus.IN_PROGRESS
            s.steps[0].started_at = datetime.utcnow().isoformat()
        s.started_at = datetime.utcnow().isoformat()
        for m in s.milestones:
            m.achieved = False
            m.achieved_at = None
            m.progress_pct = 0.0
        self._save_data()
        return True

    def get_customer_onboarding_status(self, customer_id: str) -> Dict[str, Any]:
        for s in self.sessions.values():
            if s.customer_id == customer_id:
                return self.get_session_summary(s.session_id) or {}
        return {"customer_id": customer_id, "status": "not_started"}

    def batch_start_onboarding(self, customer_ids: List[str], product_tier: str = "standard") -> Dict[str, Any]:
        created = []
        for cid in customer_ids:
            existing = any(s.customer_id == cid for s in self.sessions.values())
            if not existing:
                session = self.start_onboarding(cid, product_tier=product_tier)
                created.append(session.session_id)
        return {"created": len(created), "session_ids": created}

    def get_onboarding_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return []
        recs = []
        for step in s.steps:
            if step.status == OnboardingStatus.NOT_STARTED and step.order <= 5:
                recs.append({"step_id": step.step_id, "title": step.title, "reason": "Complete early steps to unlock full platform value", "action_url": step.action_url})
        stalled_steps = [step for step in s.steps if step.status == OnboardingStatus.IN_PROGRESS and step.started_at and datetime.fromisoformat(step.started_at) < datetime.utcnow() - timedelta(hours=24)]
        for step in stalled_steps:
            recs.append({"step_id": step.step_id, "title": step.title, "reason": "You appear stuck on this step", "guide_text": step.guide_text})
        return recs

    def get_session_tags(self, session_id: str) -> List[str]:
        s = self.sessions.get(session_id)
        return s.tags if s else []

    def add_session_tag(self, session_id: str, tag: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        if tag not in s.tags:
            s.tags.append(tag)
            self._save_data()
        return True

    def remove_session_tag(self, session_id: str, tag: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        if tag in s.tags:
            s.tags.remove(tag)
            self._save_data()
        return True

    def get_all_sessions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = list(self.sessions.values())
        if status:
            sessions = [s for s in sessions if s.status.value == status]
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return [s.to_dict() for s in sessions]

    def get_stalled_sessions(self, hours: int = 48) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        stalled = []
        for s in self.sessions.values():
            if s.status == OnboardingStatus.IN_PROGRESS and s.updated_at < cutoff:
                stalled.append(s.to_dict())
        stalled.sort(key=lambda x: x.get("updated_at", ""))
        return stalled[:20]

    def get_onboarding_analytics(self) -> Dict[str, Any]:
        total = len(self.sessions)
        if not total:
            return {"total_sessions": 0}
        completed = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.COMPLETED)
        in_progress = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.IN_PROGRESS)
        abandoned = sum(1 for s in self.sessions.values() if s.status == OnboardingStatus.ABANDONED)
        ttv_values = [s.time_to_value_days for s in self.sessions.values() if s.time_to_value_days is not None]
        return {
            "total_sessions": total,
            "completed": completed,
            "completion_rate": round(completed / total, 3),
            "in_progress": in_progress,
            "abandoned": abandoned,
            "abandonment_rate": round(abandoned / total, 3),
            "avg_time_to_value_days": round(sum(ttv_values) / max(len(ttv_values), 1), 1) if ttv_values else None,
        }

    def get_customer_journey_sessions(self, customer_id: str) -> Dict[str, Any]:
        sessions = [s.to_dict() for s in self.sessions.values() if s.customer_id == customer_id]
        sessions.sort(key=lambda s: s.get("created_at", ""))
        return {
            "customer_id": customer_id,
            "total_sessions": len(sessions),
            "sessions": sessions,
            "latest_progress": sessions[-1].get("overall_progress", 0) if sessions else 0,
        }

    def batch_abandon_stale(self, hours: int = 168) -> int:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        count = 0
        for s in self.sessions.values():
            if s.status == OnboardingStatus.IN_PROGRESS and s.updated_at < cutoff:
                s.status = OnboardingStatus.ABANDONED
                s.updated_at = datetime.utcnow().isoformat()
                count += 1
        if count:
            self._save_data()
        return count

    def get_onboarding_milestones(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return []
        return [{"milestone_id": m.milestone_id, "name": m.name, "description": m.description, "achieved": m.achieved, "achieved_at": m.achieved_at, "progress_pct": m.progress_pct} for m in s.milestones]

    def update_milestone_progress(self, session_id: str, milestone_id: str, progress: float) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        for m in s.milestones:
            if m.milestone_id == milestone_id:
                m.progress_pct = min(1.0, max(0.0, progress))
                if m.progress_pct >= 1.0:
                    m.achieved = True
                    m.achieved_at = datetime.utcnow().isoformat()
                s.updated_at = datetime.utcnow().isoformat()
                self._save_data()
                return True
        return False

    def complete_all_milestones(self, session_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        for m in s.milestones:
            m.achieved = True
            m.achieved_at = datetime.utcnow().isoformat()
            m.progress_pct = 1.0
        s.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_step_details(self, session_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(session_id)
        if not s:
            return None
        for step in s.steps:
            if step.step_id == step_id:
                return {"step_id": step.step_id, "title": step.title, "status": step.status.value, "order": step.order, "required": step.required, "guide_text": step.guide_text, "action_url": step.action_url, "progress_pct": step.progress_pct, "started_at": step.started_at, "completed_at": step.completed_at}
        return None

    def skip_step(self, session_id: str, step_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        for step in s.steps:
            if step.step_id == step_id and not step.required:
                step.status = OnboardingStatus.SKIPPED
                step.updated_at = datetime.utcnow().isoformat()
                self._advance_session(s)
                s.updated_at = datetime.utcnow().isoformat()
                self._save_data()
                return True
        return False

    def _advance_session(self, session: OnboardingSession) -> None:
        steps = sorted(session.steps, key=lambda s: s.order)
        for i, step in enumerate(steps):
            if step.status in (OnboardingStatus.NOT_STARTED, OnboardingStatus.IN_PROGRESS):
                session.current_step_id = step.step_id
                if step.status == OnboardingStatus.NOT_STARTED:
                    step.status = OnboardingStatus.IN_PROGRESS
                    step.started_at = datetime.utcnow().isoformat()
                return
        session.current_step_id = steps[-1].step_id if steps else None

    def export_onboarding_data(self, format: str = "json") -> Any:
        if format == "csv":
            lines = ["session_id,customer_id,status,progress,time_to_value_days,created_at"]
            for s in self.sessions.values():
                lines.append(f"{s.session_id},{s.customer_id},{s.status.value},{s.overall_progress},{s.time_to_value_days or ''},{s.created_at}")
            return "\n".join(lines)
        return {"sessions": [s.to_dict() for s in self.sessions.values()]}


class OnboardingBatchProcessor:
    def __init__(self, service: OnboardingWizardService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_sessions(self, sessions_data: List[Dict[str, Any]]) -> List[OnboardingSession]:
        results = []
        for data in sessions_data:
            try:
                session = self.service.create_session(
                    customer_id=data["customer_id"], customer_name=data.get("customer_name", ""),
                    template_id=data.get("template_id"),
                    created_by=data.get("created_by", ""),
                )
                results.append(session)
                self.batch_log.append({"action": "create_session", "session_id": session.session_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "create_session", "customer_id": data.get("customer_id"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_onboarding_sessions(sessions: List[OnboardingSession], page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
    filtered = [s for s in sessions if s.status.value == status] if status else sessions
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [s.to_dict() for s in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_onboarding_analytics(service: OnboardingWizardService) -> Dict[str, Any]:
    sessions = list(service.sessions.values())
    if not sessions:
        return {"total": 0}
    completed = [s for s in sessions if s.status == OnboardingStatus.COMPLETED]
    abandoned = [s for s in sessions if s.status == OnboardingStatus.ABANDONED]
    ttv_values = [s.time_to_value_days for s in completed if s.time_to_value_days is not None]
    return {
        "total": len(sessions),
        "completed": len(completed),
        "abandoned": len(abandoned),
        "in_progress": sum(1 for s in sessions if s.status == OnboardingStatus.IN_PROGRESS),
        "completion_rate": round(len(completed) / max(len(sessions), 1), 3),
        "abandonment_rate": round(len(abandoned) / max(len(sessions), 1), 3),
        "avg_time_to_value_days": round(sum(ttv_values) / max(len(ttv_values), 1), 1) if ttv_values else None,
        "avg_overall_progress": round(sum(s.overall_progress for s in sessions) / max(len(sessions), 1), 1),
    }


class OnboardingAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_onboarding_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    return errors


def merge_onboarding_customers(service: OnboardingWizardService, source: str, target: str) -> int:
    count = 0
    for s in service.sessions.values():
        if s.customer_id == source:
            s.customer_id = target
            count += 1
    if count:
        service._save_data()
    return count


def get_onboarding_bottleneck_analysis(service: OnboardingWizardService) -> List[Dict[str, Any]]:
    step_breakdown: Dict[str, Dict[str, int]] = {}
    for s in service.sessions.values():
        for step in s.steps:
            if step.title not in step_breakdown:
                step_breakdown[step.title] = {"total": 0, "completed": 0, "skipped": 0, "in_progress": 0}
            step_breakdown[step.title]["total"] += 1
            if step.status == OnboardingStatus.COMPLETED:
                step_breakdown[step.title]["completed"] += 1
            elif step.status == OnboardingStatus.SKIPPED:
                step_breakdown[step.title]["skipped"] += 1
            elif step.status == OnboardingStatus.IN_PROGRESS:
                step_breakdown[step.title]["in_progress"] += 1
    bottlenecks = []
    for step_name, stats in step_breakdown.items():
        completion_rate = stats["completed"] / max(stats["total"], 1)
        if completion_rate < 0.6:
            bottlenecks.append({"step": step_name, "completion_rate": round(completion_rate, 3), "total": stats["total"]})
    return sorted(bottlenecks, key=lambda b: b["completion_rate"])

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
        return {"total_customers": 0, "active_users": 0, "nps_score": 0.0, "satisfaction_rate": 0.0}

    def validate_engagement(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class CXResult(BaseModel):
    success: bool = True
    operation: str = ""
    customer_id: Optional[str] = None
    interaction_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CXBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    campaign: str = Field(default="general")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    responded: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_response(self) -> None:
        self.responded += 1

    def complete(self) -> None:
        self.status = "completed"

class CustomerProfile(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    tier: str = Field(default="standard")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    total_spend: float = Field(default=0.0)
    interaction_count: int = Field(default=0)
    nps_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

class CustomerRepository:
    def __init__(self) -> None:
        self._customers: Dict[str, CustomerProfile] = {}

    def create(self, name: str, email: str, tier: str = "standard") -> CustomerProfile:
        customer = CustomerProfile(name=name, email=email, tier=tier)
        self._customers[customer.customer_id] = customer
        return customer

    def get(self, customer_id: str) -> Optional[CustomerProfile]:
        return self._customers.get(customer_id)

    def update_last_active(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if customer:
            customer.last_active = datetime.utcnow()
            customer.interaction_count += 1
            return True
        return False

    def get_by_tier(self, tier: str) -> List[CustomerProfile]:
        return [c for c in self._customers.values() if c.tier == tier]

    def get_at_risk(self, days_inactive: int = 30) -> List[CustomerProfile]:
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)
        return [c for c in self._customers.values() if c.last_active and c.last_active < cutoff]

    def get_statistics(self) -> Dict[str, Any]:
        customers = list(self._customers.values())
        return {"total": len(customers), "avg_spend": round(sum(c.total_spend for c in customers) / max(len(customers), 1), 2),
                "by_tier": {t: sum(1 for c in customers if c.tier == t) for t in set(c.tier for c in customers)},
                "at_risk": len(self.get_at_risk())}

class NPSRecord(BaseModel):
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    score: int = Field(default=0, ge=0, le=10)
    comment: str = ""
    category: str = Field(default="general")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    def is_promoter(self) -> bool:
        return self.score >= 9

    def is_passive(self) -> bool:
        return 7 <= self.score <= 8

    def is_detractor(self) -> bool:
        return self.score <= 6

class NPSTracker:
    def __init__(self) -> None:
        self._surveys: List[NPSRecord] = []

    def record(self, customer_id: str, score: int, comment: str = "", category: str = "general") -> NPSRecord:
        survey = NPSRecord(customer_id=customer_id, score=score, comment=comment, category=category)
        self._surveys.append(survey)
        return survey

    def get_score(self) -> float:
        total = len(self._surveys)
        if total == 0:
            return 0.0
        promoters = sum(1 for s in self._surveys if s.is_promoter())
        detractors = sum(1 for s in self._surveys if s.is_detractor())
        return round((promoters - detractors) / total * 100, 1)

    def get_by_category(self, category: str) -> List[NPSRecord]:
        return [s for s in self._surveys if s.category == category]

    def get_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [s for s in self._surveys if s.submitted_at >= cutoff]
        return {"period_days": days, "surveys": len(recent),
                "score": round((sum(1 for s in recent if s.is_promoter()) - sum(1 for s in recent if s.is_detractor())) / max(len(recent), 1) * 100, 1),
                "promoters": sum(1 for s in recent if s.is_promoter()),
                "passives": sum(1 for s in recent if s.is_passive()),
                "detractors": sum(1 for s in recent if s.is_detractor())}

class TicketRecord(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    subject: str
    description: str = ""
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    satisfaction_score: Optional[int] = None

class TicketSystem:
    def __init__(self) -> None:
        self._tickets: Dict[str, TicketRecord] = {}

    def create(self, customer_id: str, subject: str, description: str = "", priority: str = "medium") -> TicketRecord:
        ticket = TicketRecord(customer_id=customer_id, subject=subject, description=description, priority=priority)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve(self, ticket_id: str, satisfaction: Optional[int] = None) -> bool:
        ticket = self._tickets.get(ticket_id)
        if ticket and ticket.status == "open":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            ticket.satisfaction_score = satisfaction
            return True
        return False

    def get_open(self) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.status == "open"]

    def get_by_priority(self, priority: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_by_customer(self, customer_id: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.customer_id == customer_id]

    def get_statistics(self) -> Dict[str, Any]:
        tickets = list(self._tickets.values())
        open_tickets = self.get_open()
        resolved = [t for t in tickets if t.status == "resolved"]
        avg_resolution = 0.0
        if resolved:
            durations = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved if t.resolved_at]
            avg_resolution = round(sum(durations) / len(durations), 1) if durations else 0.0
        return {"total": len(tickets), "open": len(open_tickets), "resolved": len(resolved),
                "avg_resolution_hours": avg_resolution,
                "by_priority": {p: sum(1 for t in tickets if t.priority == p) for p in set(t.priority for t in tickets)},
                "avg_satisfaction": round(sum(t.satisfaction_score for t in resolved if t.satisfaction_score) / max(len([t for t in resolved if t.satisfaction_score]), 1), 1)}

class OnboardingStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    step_name: str
    status: str = Field(default="pending")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class OnboardingWorkflow:
    def __init__(self) -> None:
        self._steps: Dict[str, OnboardingStep] = {}

    def add_step(self, customer_id: str, step_name: str) -> OnboardingStep:
        step = OnboardingStep(customer_id=customer_id, step_name=step_name)
        self._steps[step.step_id] = step
        return step

    def start_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "pending":
            step.status = "in_progress"
            step.started_at = datetime.utcnow()
            return True
        return False

    def complete_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "in_progress":
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_minutes = int((step.completed_at - step.started_at).total_seconds() / 60) if step.started_at else 0
            return True
        return False

    def get_progress(self, customer_id: str) -> Dict[str, Any]:
        steps = [s for s in self._steps.values() if s.customer_id == customer_id]
        completed = sum(1 for s in steps if s.status == "completed")
        return {"customer_id": customer_id, "total_steps": len(steps),
                "completed": completed, "in_progress": sum(1 for s in steps if s.status == "in_progress"),
                "pending": sum(1 for s in steps if s.status == "pending"),
                "progress_pct": round(completed / max(len(steps), 1) * 100, 1)}
