"""NPS & survey engine with automated surveys, response analytics, and closed-loop feedback."""

import json
import logging
import math
import os
import uuid
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SurveyType(str, Enum):
    NPS = "nps"
    CSAT = "csat"
    CES = "ces"
    CUSTOM = "custom"


class SurveyTrigger(str, Enum):
    AFTER_ONBOARDING = "after_onboarding"
    AFTER_TICKET_RESOLUTION = "after_ticket_resolution"
    AFTER_PURCHASE = "after_purchase"
    AFTER_RENEWAL = "after_renewal"
    PERIODIC = "periodic"
    AFTER_FEATURE_USE = "after_feature_use"
    MANUAL = "manual"


class SurveyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResponseStatus(str, Enum):
    SENT = "sent"
    OPENED = "opened"
    STARTED = "started"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class NPSLabel(str, Enum):
    DETRACTOR = "detractor"
    PASSIVE = "passive"
    PROMOTER = "promoter"


@dataclass
class SurveyQuestion:
    question_id: str
    text: str
    question_type: str
    required: bool = True
    options: List[str] = field(default_factory=list)
    max_rating: int = 5
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SurveyDefinition:
    survey_id: str
    title: str
    description: str
    survey_type: SurveyType
    trigger: SurveyTrigger
    status: SurveyStatus = SurveyStatus.DRAFT
    questions: List[SurveyQuestion] = field(default_factory=list)
    target_segment: str = "all"
    frequency_days: Optional[int] = None
    max_responses_per_user: int = 1
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    response_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SurveyResponse:
    response_id: str
    survey_id: str
    customer_id: str
    customer_name: str = ""
    answers: Dict[str, Any] = field(default_factory=dict)
    nps_score: Optional[int] = None
    nps_label: Optional[str] = None
    csat_score: Optional[int] = None
    ces_score: Optional[int] = None
    comments: Optional[str] = None
    status: ResponseStatus = ResponseStatus.SENT
    sent_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    time_to_complete_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NPSSurveyService:
    def __init__(self, storage_path: str = "nps_survey_data.json"):
        self.storage_path = storage_path
        self.surveys: Dict[str, SurveyDefinition] = {}
        self.responses: Dict[str, SurveyResponse] = {}
        self.trigger_history: Dict[str, List[str]] = defaultdict(list)
        self._init_default_surveys()
        self._load_data()

    def _init_default_surveys(self):
        nps_q = SurveyQuestion("q-nps", "How likely are you to recommend Infra Pilot to a friend or colleague?", "nps", max_rating=10, order=1)
        feedback_q = SurveyQuestion("q-feedback", "What is the primary reason for your score?", "text", order=2)
        followup_q = SurveyQuestion("q-followup", "What can we do to improve your experience?", "text", required=False, order=3)

        default_surveys = [
            SurveyDefinition(
                survey_id="svy-nps-onboarding", title="Onboarding NPS", description="How was your onboarding experience?",
                survey_type=SurveyType.NPS, trigger=SurveyTrigger.AFTER_ONBOARDING,
                questions=[nps_q, feedback_q, followup_q],
                email_subject="How was your onboarding experience?",
                email_body="We'd love to hear about your onboarding experience with Infra Pilot.",
            ),
            SurveyDefinition(
                survey_id="svy-nps-ticket", title="Support Experience", description="How was your support experience?",
                survey_type=SurveyType.NPS, trigger=SurveyTrigger.AFTER_TICKET_RESOLUTION,
                questions=[nps_q, SurveyQuestion("q-ticket-rating", "How satisfied are you with the support you received?", "rating", max_rating=5, order=2), feedback_q],
                email_subject="How was your support experience?",
                email_body="We'd love to hear about your recent support experience.",
            ),
            SurveyDefinition(
                survey_id="svy-csat-general", title="Customer Satisfaction", description="Help us improve by sharing your feedback",
                survey_type=SurveyType.CSAT, trigger=SurveyTrigger.PERIODIC, frequency_days=90,
                questions=[
                    SurveyQuestion("q-csat", "How satisfied are you with Infra Pilot?", "rating", max_rating=5, order=1),
                    SurveyQuestion("q-improve", "What should we improve?", "text", required=False, order=2),
                    SurveyQuestion("q-features", "Which features do you find most valuable?", "text", required=False, order=3),
                ],
                email_subject="How satisfied are you with Infra Pilot?",
                email_body="Your feedback helps us build a better platform.",
            ),
            SurveyDefinition(
                survey_id="svy-ces-task", title="Task Ease", description="How easy was it to complete your task?",
                survey_type=SurveyType.CES, trigger=SurveyTrigger.AFTER_FEATURE_USE,
                questions=[
                    SurveyQuestion("q-ces", "How easy was it to complete your task today?", "rating", max_rating=7, order=1),
                    SurveyQuestion("q-ces-feedback", "What could make it easier?", "text", required=False, order=2),
                ],
            ),
        ]
        for svy in default_surveys:
            svy.status = SurveyStatus.ACTIVE
            self.surveys[svy.survey_id] = svy

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for sdata in data.get("surveys", []):
                        questions = [SurveyQuestion(**q) for q in sdata.get("questions", [])]
                        sdata["questions"] = questions
                        self.surveys[sdata["survey_id"]] = SurveyDefinition(**sdata)
                    for rdata in data.get("responses", []):
                        self.responses[rdata["response_id"]] = SurveyResponse(**rdata)
                    self.trigger_history = defaultdict(list, data.get("trigger_history", {}))
            except Exception as e:
                logger.warning(f"Failed to load survey data: {e}")

    def _save_data(self):
        try:
            data = {
                "surveys": [s.to_dict() for s in self.surveys.values()],
                "responses": [r.to_dict() for r in self.responses.values()],
                "trigger_history": dict(self.trigger_history),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save survey data: {e}")

    def create_survey(
        self, title: str, description: str, survey_type: str,
        trigger: str, questions: List[Dict[str, Any]],
        target_segment: str = "all", frequency_days: Optional[int] = None,
    ) -> SurveyDefinition:
        survey_id = f"SVY-{uuid.uuid4().hex[:6].upper()}"
        survey_questions = []
        for i, qdata in enumerate(questions):
            survey_questions.append(SurveyQuestion(
                question_id=f"q-{uuid.uuid4().hex[:6]}",
                text=qdata["text"],
                question_type=qdata.get("type", "text"),
                required=qdata.get("required", True),
                options=qdata.get("options", []),
                max_rating=qdata.get("max_rating", 5),
                order=i + 1,
            ))
        survey = SurveyDefinition(
            survey_id=survey_id, title=title, description=description,
            survey_type=SurveyType(survey_type), trigger=SurveyTrigger(trigger),
            target_segment=target_segment, frequency_days=frequency_days,
            questions=survey_questions,
        )
        self.surveys[survey_id] = survey
        self._save_data()
        return survey

    def send_survey(self, survey_id: str, customer_id: str, customer_name: str = "") -> Optional[SurveyResponse]:
        survey = self.surveys.get(survey_id)
        if not survey or survey.status != SurveyStatus.ACTIVE:
            return None
        recent = self.trigger_history.get(f"{survey_id}:{customer_id}", [])
        if len(recent) >= survey.max_responses_per_user:
            return None
        if survey.frequency_days:
            if recent:
                last = datetime.fromisoformat(recent[-1])
                if datetime.utcnow() - last < timedelta(days=survey.frequency_days):
                    return None
        response_id = f"RSP-{uuid.uuid4().hex[:8].upper()}"
        resp = SurveyResponse(
            response_id=response_id, survey_id=survey_id,
            customer_id=customer_id, customer_name=customer_name,
            status=ResponseStatus.SENT, sent_at=datetime.utcnow().isoformat(),
        )
        self.responses[response_id] = resp
        self.trigger_history[f"{survey_id}:{customer_id}"].append(datetime.utcnow().isoformat())
        survey.response_count += 1
        self._save_data()
        return resp

    def submit_response(
        self, response_id: str, answers: Dict[str, Any],
        comments: Optional[str] = None,
    ) -> Optional[SurveyResponse]:
        resp = self.responses.get(response_id)
        if not resp:
            return None
        resp.answers = answers
        resp.comments = comments
        resp.status = ResponseStatus.COMPLETED
        resp.completed_at = datetime.utcnow().isoformat()
        if resp.sent_at:
            sent = datetime.fromisoformat(resp.sent_at)
            completed = datetime.fromisoformat(resp.completed_at)
            resp.time_to_complete_seconds = round((completed - sent).total_seconds(), 1)
        survey = self.surveys.get(resp.survey_id)
        if survey:
            if survey.survey_type == SurveyType.NPS:
                nps_val = answers.get("q-nps") or answers.get("nps")
                if nps_val is not None:
                    nps_int = int(nps_val)
                    resp.nps_score = nps_int
                    if nps_int >= 9:
                        resp.nps_label = NPSLabel.PROMOTER.value
                    elif nps_int >= 7:
                        resp.nps_label = NPSLabel.PASSIVE.value
                    else:
                        resp.nps_label = NPSLabel.DETRACTOR.value
            elif survey.survey_type == SurveyType.CSAT:
                csat_val = answers.get("q-csat") or answers.get("csat")
                if csat_val is not None:
                    resp.csat_score = int(csat_val)
            elif survey.survey_type == SurveyType.CES:
                ces_val = answers.get("q-ces") or answers.get("ces")
                if ces_val is not None:
                    resp.ces_score = int(ces_val)
        self._save_data()
        return resp

    def get_nps_score(self) -> Dict[str, Any]:
        nps_responses = [r for r in self.responses.values() if r.nps_score is not None]
        total = len(nps_responses)
        if total == 0:
            return {"nps_score": 0, "total_responses": 0, "promoters": 0, "passives": 0, "detractors": 0}
        promoters = sum(1 for r in nps_responses if r.nps_label == NPSLabel.PROMOTER.value)
        passives = sum(1 for r in nps_responses if r.nps_label == NPSLabel.PASSIVE.value)
        detractors = sum(1 for r in nps_responses if r.nps_label == NPSLabel.DETRACTOR.value)
        pct_promoters = promoters / total
        pct_detractors = detractors / total
        nps = round((pct_promoters - pct_detractors) * 100, 1)
        return {
            "nps_score": nps,
            "total_responses": total,
            "promoters": promoters,
            "promoter_pct": round(pct_promoters * 100, 1),
            "passives": passives,
            "passive_pct": round(passives / total * 100, 1),
            "detractors": detractors,
            "detractor_pct": round(pct_detractors * 100, 1),
        }

    def get_survey_responses(self, survey_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        results = [r for r in self.responses.values() if r.survey_id == survey_id]
        results.sort(key=lambda r: r.sent_at or "", reverse=True)
        return [r.to_dict() for r in results[:limit]]

    def get_customer_responses(self, customer_id: str) -> List[Dict[str, Any]]:
        results = [r for r in self.responses.values() if r.customer_id == customer_id]
        results.sort(key=lambda r: r.sent_at or "", reverse=True)
        return [r.to_dict() for r in results]

    def get_surveys(self, trigger: Optional[str] = None, survey_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.surveys.values())
        if trigger:
            results = [s for s in results if s.trigger.value == trigger]
        if survey_type:
            results = [s for s in results if s.survey_type.value == survey_type]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return [s.to_dict() for s in results]

    def get_survey(self, survey_id: str) -> Optional[Dict[str, Any]]:
        survey = self.surveys.get(survey_id)
        return survey.to_dict() if survey else None

    def get_nps_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        responses = [r for r in self.responses.values() if r.nps_score is not None and (r.completed_at or "") >= cutoff]
        if not responses:
            return {"trend": [], "monthly_scores": {}}
        monthly: Dict[str, List[int]] = defaultdict(list)
        for r in responses:
            month_key = (r.completed_at or r.sent_at or "")[:7]
            monthly[month_key].append(r.nps_score)
        monthly_scores = {}
        for month, scores in sorted(monthly.items()):
            promoters = sum(1 for s in scores if s >= 9)
            detractors = sum(1 for s in scores if s <= 6)
            total = len(scores)
            nps = round((promoters / total - detractors / total) * 100, 1)
            monthly_scores[month] = {"nps": nps, "responses": total}
        return {
            "period_days": days,
            "monthly_scores": monthly_scores,
            "trend": list(monthly_scores.values()),
        }

    def get_detractor_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        detractors = [
            r for r in self.responses.values()
            if r.nps_label == NPSLabel.DETRACTOR.value and r.comments
        ]
        detractors.sort(key=lambda r: r.completed_at or "", reverse=True)
        results = []
        for r in detractors[:limit]:
            results.append({
                "response_id": r.response_id,
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "nps_score": r.nps_score,
                "comments": r.comments,
                "completed_at": r.completed_at,
            })
        return results

    def get_stats(self) -> Dict[str, Any]:
        total_surveys = len(self.surveys)
        active_surveys = sum(1 for s in self.surveys.values() if s.status == SurveyStatus.ACTIVE)
        total_responses = len(self.responses)
        completed = sum(1 for r in self.responses.values() if r.status == ResponseStatus.COMPLETED)
        response_rate = round(completed / max(total_responses, 1), 3)
        nps_info = self.get_nps_score()
        return {
            "total_surveys": total_surveys,
            "active_surveys": active_surveys,
            "total_sent": total_responses,
            "completed": completed,
            "response_rate": response_rate,
            "nps_score": nps_info["nps_score"],
            "total_nps_responses": nps_info["total_responses"],
            "detractor_count": nps_info["detractors"],
        }

    def get_survey(self, survey_id: str) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        return s.to_dict() if s else None

    def update_survey(self, survey_id: str, updates: Dict[str, Any]) -> bool:
        s = self.surveys.get(survey_id)
        if not s: return False
        if "title" in updates: s.title = updates["title"]
        if "questions" in updates: s.questions = updates["questions"]
        if "target_segment" in updates: s.target_segment = updates["target_segment"]
        if "active" in updates: s.active = updates["active"]
        self._save_data()
        return True

    def delete_survey(self, survey_id: str) -> bool:
        if survey_id in self.surveys:
            del self.surveys[survey_id]
            self._save_data()
            return True
        return False

    def send_survey(self, survey_id: str, customer_ids: List[str]) -> Dict[str, Any]:
        s = self.surveys.get(survey_id)
        if not s: return {"error": "Survey not found"}
        sent = 0
        for cid in customer_ids:
            try:
                resp = SurveyResponse(response_id=str(uuid.uuid4())[:8], survey_id=survey_id, customer_id=cid, answers={}, status="sent")
                self.responses.append(resp)
                sent += 1
            except Exception:
                continue
        self._save_data()
        return {"survey_id": survey_id, "sent": sent, "total_targeted": len(customer_ids)}

    def get_survey_responses(self, survey_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        responses = [r.to_dict() for r in self.responses if r.survey_id == survey_id]
        return responses[:limit]

    def submit_response(self, survey_id: str, customer_id: str, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        if not s: return None
        for r in self.responses:
            if r.survey_id == survey_id and r.customer_id == customer_id and r.status == "sent":
                r.answers = answers
                r.submitted_at = datetime.utcnow()
                r.status = "completed"
                s.response_count += 1
                self._save_data()
                if "nps_score" in answers:
                    self._record_nps(customer_id, int(answers["nps_score"]), survey_id)
                return r.to_dict()
        return None

    def get_nps_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        monthly = defaultdict(list)
        for entry in self.nps_history:
            if entry.timestamp >= cutoff:
                key = entry.timestamp.strftime("%Y-%m")
                monthly[key].append(entry.score)
        return [{"month": k, "avg_score": round(sum(v) / len(v), 1), "responses": len(v)} for k, v in sorted(monthly.items())]

    def get_segment_nps(self) -> Dict[str, Any]:
        segment_scores = defaultdict(list)
        for entry in self.nps_history:
            segment_scores[entry.segment or "unknown"].append(entry.score)
        return {seg: {"avg_score": round(sum(scores) / len(scores), 1), "count": len(scores)} for seg, scores in segment_scores.items()}

    def get_detractor_feedback(self, limit: int = 20) -> List[Dict[str, Any]]:
        detractors = [r for r in self.responses if r.status == "completed" and r.answers.get("nps_score") and int(r.answers["nps_score"]) <= 6]
        return [{"customer_id": r.customer_id, "score": int(r.answers["nps_score"]), "answers": {k: v for k, v in r.answers.items() if k != "nps_score"}, "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None} for r in detractors[:limit]]

    def get_promoter_feedback(self, limit: int = 20) -> List[Dict[str, Any]]:
        promoters = [r for r in self.responses if r.status == "completed" and r.answers.get("nps_score") and int(r.answers["nps_score"]) >= 9]
        return [{"customer_id": r.customer_id, "score": int(r.answers["nps_score"]), "answers": {k: v for k, v in r.answers.items() if k != "nps_score"}, "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None} for r in promoters[:limit]]

    def export_nps_report(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "overall_nps": self.calculate_nps(), "trend": self.get_nps_trend(), "segment_breakdown": self.get_segment_nps(), "total_responses": sum(1 for r in self.responses if r.status == "completed"), "surveys": [s.to_dict() for s in self.surveys.values()]}

    def get_response_rate_analysis(self) -> Dict[str, Any]:
        total_sent = sum(1 for r in self.responses if r.status == "sent" or r.status == "completed")
        total_completed = sum(1 for r in self.responses if r.status == "completed")
        return {"total_sent": total_sent, "total_completed": total_completed, "response_rate": round(total_completed / max(total_sent, 1) * 100, 1), "surveys_analyzed": len(self.surveys)}

    def clone_survey(self, survey_id: str, new_title: str) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        if not s: return None
        new_id = str(uuid.uuid4())[:8]
        cloned = Survey(survey_id=new_id, title=new_title, questions=[{"id": q["id"], "text": q["text"], "type": q["type"]} for q in s.questions], target_segment=s.target_segment, active=False)
        self.surveys[new_id] = cloned
        self._save_data()
        return cloned.to_dict()

    def get_survey_completion_stats(self, survey_id: str) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        if not s: return None
        responses = [r for r in self.responses if r.survey_id == survey_id]
        completed = [r for r in responses if r.status == "completed"]
        return {"survey_id": survey_id, "title": s.title, "total_sent": len(responses), "completed": len(completed), "completion_rate": round(len(completed) / max(len(responses), 1) * 100, 1), "avg_completion_time_min": None}

    def prune_old_responses(self, days: int = 365) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        before = len(self.responses)
        self.responses = [r for r in self.responses if r.submitted_at is None or r.submitted_at >= cutoff]
        return before - len(self.responses)

    def get_survey_analytics(self, survey_id: str) -> Optional[Dict[str, Any]]:
        survey = self.surveys.get(survey_id)
        if not survey:
            return None
        responses = [r for r in self.responses.values() if r.survey_id == survey_id]
        completed = [r for r in responses if r.status == ResponseStatus.COMPLETED]
        if not completed:
            return {"survey_id": survey_id, "title": survey.title, "total_sent": len(responses), "completed": 0, "response_rate": 0}
        nps_scores = [r.nps_score for r in completed if r.nps_score is not None]
        csat_scores = [r.csat_score for r in completed if r.csat_score is not None]
        ces_scores = [r.ces_score for r in completed if r.ces_score is not None]
        return {
            "survey_id": survey_id,
            "title": survey.title,
            "survey_type": survey.survey_type.value,
            "total_sent": len(responses),
            "completed": len(completed),
            "response_rate": round(len(completed) / max(len(responses), 1), 3),
            "avg_nps": round(sum(nps_scores) / max(len(nps_scores), 1), 1) if nps_scores else None,
            "avg_csat": round(sum(csat_scores) / max(len(csat_scores), 1), 1) if csat_scores else None,
            "avg_ces": round(sum(ces_scores) / max(len(ces_scores), 1), 1) if ces_scores else None,
            "nps_distribution": self._get_nps_distribution(completed),
            "segment_breakdown": self._get_segment_breakdown(completed),
        }

    def _get_nps_distribution(self, responses: List[SurveyResponse]) -> Dict[str, int]:
        promoters = sum(1 for r in responses if r.nps_label == NPSLabel.PROMOTER.value)
        passives = sum(1 for r in responses if r.nps_label == NPSLabel.PASSIVE.value)
        detractors = sum(1 for r in responses if r.nps_label == NPSLabel.DETRACTOR.value)
        return {"promoters": promoters, "passives": passives, "detractors": detractors}

    def _get_segment_breakdown(self, responses: List[SurveyResponse]) -> Dict[str, Any]:
        segments = defaultdict(lambda: {"count": 0, "scores": []})
        for r in responses:
            seg = r.metadata.get("segment", "unknown")
            segments[seg]["count"] += 1
            if r.nps_score is not None:
                segments[seg]["scores"].append(r.nps_score)
        return {
            seg: {
                "count": data["count"],
                "avg_nps": round(sum(data["scores"]) / max(len(data["scores"]), 1), 1) if data["scores"] else None,
            }
            for seg, data in segments.items()
        }

    def get_customer_nps_history(self, customer_id: str) -> List[Dict[str, Any]]:
        results = []
        for r in self.responses.values():
            if r.customer_id == customer_id and r.nps_score is not None:
                survey = self.surveys.get(r.survey_id)
                results.append({
                    "response_id": r.response_id,
                    "survey_title": survey.title if survey else "",
                    "nps_score": r.nps_score,
                    "nps_label": r.nps_label,
                    "completed_at": r.completed_at,
                    "comments": r.comments,
                })
        results.sort(key=lambda x: x["completed_at"] or "", reverse=True)
        return results

    def get_nps_benchmark(self) -> Dict[str, Any]:
        all_nps = [r.nps_score for r in self.responses.values() if r.nps_score is not None]
        if not all_nps:
            return {"avg_nps": 0, "median_nps": 0, "std_dev": 0, "sample_size": 0}
        avg = sum(all_nps) / len(all_nps)
        sorted_scores = sorted(all_nps)
        median = sorted_scores[len(sorted_scores) // 2]
        variance = sum((s - avg) ** 2 for s in all_nps) / len(all_nps)
        return {
            "avg_nps": round(avg, 1),
            "median_nps": median,
            "std_dev": round(variance ** 0.5, 1),
            "sample_size": len(all_nps),
            "min": min(all_nps),
            "max": max(all_nps),
        }

    def get_survey_comparison(self, survey_ids: List[str]) -> List[Dict[str, Any]]:
        return [self.get_survey_analytics(sid) for sid in survey_ids if sid in self.surveys]

    def get_feedback_themes(self, limit: int = 20) -> List[Dict[str, Any]]:
        all_comments = [r.comments for r in self.responses.values() if r.comments and r.nps_score is not None and r.nps_score <= 6]
        themes = Counter()
        for comment in all_comments:
            words = comment.lower().split()
            for phrase in ["support", "pricing", "bug", "slow", "confusing", "missing", "crash", "difficult", "expensive", "interface"]:
                if phrase in comment.lower():
                    themes[phrase] += 1
        return [{"theme": theme, "count": count} for theme, count in themes.most_common(limit)]

    def get_response_rate_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        responses = [r for r in self.responses.values() if (r.sent_at or "") >= cutoff]
        monthly = defaultdict(lambda: {"sent": 0, "completed": 0})
        for r in responses:
            month = (r.sent_at or r.created_at)[:7]
            monthly[month]["sent"] += 1
            if r.status == ResponseStatus.COMPLETED:
                monthly[month]["completed"] += 1
        return {
            "monthly": {
                m: {
                    "sent": d["sent"],
                    "completed": d["completed"],
                    "rate": round(d["completed"] / max(d["sent"], 1), 3),
                }
                for m, d in sorted(monthly.items())
            },
            "overall_rate": round(
                sum(1 for r in responses if r.status == ResponseStatus.COMPLETED) / max(len(responses), 1), 3
            ),
        }

    def get_csat_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        responses = [r for r in self.responses.values() if r.csat_score is not None and (r.completed_at or "") >= cutoff]
        monthly = defaultdict(list)
        for r in responses:
            month = (r.completed_at or r.sent_at)[:7]
            monthly[month].append(r.csat_score)
        return {
            "monthly": {m: {"avg": round(sum(s) / len(s), 1), "count": len(s)} for m, s in sorted(monthly.items())},
            "overall_avg": round(sum(r.csat_score for r in responses) / max(len(responses), 1), 1) if responses else 0,
        }

    def get_ces_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        responses = [r for r in self.responses.values() if r.ces_score is not None and (r.completed_at or "") >= cutoff]
        monthly = defaultdict(list)
        for r in responses:
            month = (r.completed_at or r.sent_at)[:7]
            monthly[month].append(r.ces_score)
        return {
            "monthly": {m: {"avg": round(sum(s) / len(s), 1), "count": len(s)} for m, s in sorted(monthly.items())},
            "overall_avg": round(sum(r.ces_score for r in responses) / max(len(responses), 1), 1) if responses else 0,
        }

    def get_open_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        feedback = []
        for r in self.responses.values():
            if r.comments:
                feedback.append({
                    "response_id": r.response_id,
                    "customer_id": r.customer_id,
                    "survey_id": r.survey_id,
                    "comments": r.comments,
                    "nps_score": r.nps_score,
                    "completed_at": r.completed_at,
                })
        feedback.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
        return feedback[:limit]

    def get_survey_status(self, survey_id: str) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        if not s:
            return None
        return {
            "survey_id": survey_id,
            "title": s.title,
            "status": s.status.value,
            "active": s.status == SurveyStatus.ACTIVE,
            "response_count": s.response_count,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }

    def pause_survey(self, survey_id: str) -> bool:
        s = self.surveys.get(survey_id)
        if not s:
            return False
        s.status = SurveyStatus.PAUSED
        s.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def resume_survey(self, survey_id: str) -> bool:
        s = self.surveys.get(survey_id)
        if not s:
            return False
        s.status = SurveyStatus.ACTIVE
        s.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def archive_survey(self, survey_id: str) -> bool:
        s = self.surveys.get(survey_id)
        if not s:
            return False
        s.status = SurveyStatus.ARCHIVED
        s.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_survey_preview(self, survey_id: str) -> Optional[Dict[str, Any]]:
        s = self.surveys.get(survey_id)
        if not s:
            return None
        return {
            "survey_id": s.survey_id,
            "title": s.title,
            "description": s.description,
            "survey_type": s.survey_type.value,
            "questions": [{"id": q.question_id, "text": q.text, "type": q.question_type, "required": q.required, "options": q.options} for q in s.questions],
            "estimated_minutes": len(s.questions),
        }

    def duplicate_survey(self, survey_id: str, new_title: str) -> Optional[Dict[str, Any]]:
        return self.clone_survey(survey_id, new_title)

    def get_nps_report(self) -> Dict[str, Any]:
        return self.export_nps_report()

    def get_response_comments(self, survey_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        responses = [r for r in self.responses.values() if r.survey_id == survey_id and r.comments]
        responses.sort(key=lambda r: r.completed_at or "", reverse=True)
        return [{"response_id": r.response_id, "customer_id": r.customer_id, "nps_score": r.nps_score, "comments": r.comments, "completed_at": r.completed_at} for r in responses[:limit]]

    def get_survey_response_trend(self, survey_id: str) -> Dict[str, Any]:
        responses = [r for r in self.responses.values() if r.survey_id == survey_id]
        daily = defaultdict(list)
        for r in responses:
            if r.completed_at:
                day = r.completed_at[:10]
                daily[day].append(r.nps_score if r.nps_score is not None else 0)
        trend = {day: {"avg": round(sum(scores) / len(scores), 1), "count": len(scores)} for day, scores in sorted(daily.items())}
        scores = [r.nps_score for r in responses if r.nps_score is not None]
        return {"trend": trend, "overall_avg": round(sum(scores) / max(len(scores), 1), 1) if scores else 0, "total_responses": len(responses)}

    def get_survey_completion_rate(self, survey_id: str) -> Dict[str, Any]:
        s = self.surveys.get(survey_id)
        if not s:
            return {}
        sent = max(s.response_count, 1)
        started = sum(1 for r in self.responses.values() if r.survey_id == survey_id)
        completed = sum(1 for r in self.responses.values() if r.survey_id == survey_id and r.completed_at)
        return {"survey_id": survey_id, "sent": sent, "started": started, "completed": completed, "completion_rate": round(completed / sent, 3), "drop_off_rate": round(1 - completed / max(started, 1), 3)}

    def get_detractor_feedback(self, survey_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        responses = [r for r in self.responses.values() if r.survey_id == survey_id and r.nps_score is not None and r.nps_score <= 6 and r.comments]
        responses.sort(key=lambda r: r.nps_score)
        return [{"response_id": r.response_id, "customer_id": r.customer_id, "nps_score": r.nps_score, "comments": r.comments, "completed_at": r.completed_at} for r in responses[:limit]]

    def get_promoter_feedback(self, survey_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        responses = [r for r in self.responses.values() if r.survey_id == survey_id and r.nps_score is not None and r.nps_score >= 9 and r.comments]
        responses.sort(key=lambda r: r.nps_score, reverse=True)
        return [{"response_id": r.response_id, "customer_id": r.customer_id, "nps_score": r.nps_score, "comments": r.comments, "completed_at": r.completed_at} for r in responses[:limit]]

    def get_nps_trend(self, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        responses = [r for r in self.responses.values() if r.completed_at and r.completed_at >= cutoff and r.nps_score is not None]
        monthly = defaultdict(list)
        for r in responses:
            month = r.completed_at[:7]
            monthly[month].append(r.nps_score)
        return {m: {"avg": round(sum(s) / len(s), 1), "count": len(s)} for m, s in sorted(monthly.items())}

    def get_survey_participants(self, survey_id: str) -> List[Dict[str, Any]]:
        participants = defaultdict(lambda: {"responded": False, "nps_score": None, "completed_at": None})
        for r in self.responses.values():
            if r.survey_id == survey_id:
                participants[r.customer_id] = {"responded": True, "nps_score": r.nps_score, "completed_at": r.completed_at}
        return [{"customer_id": cid, **info} for cid, info in participants.items()]

    def export_survey_data(self, survey_id: str, format: str = "json") -> Any:
        survey = self.surveys.get(survey_id)
        if not survey:
            return None
        if format == "csv":
            lines = ["customer_id,nps_score,csat_score,ces_score,comments,completed_at"]
            for r in self.responses.values():
                if r.survey_id == survey_id:
                    lines.append(f"{r.customer_id},{r.nps_score},{r.csat_score},{r.ces_score},{r.comments or ''},{r.completed_at or ''}")
            return "\n".join(lines)
        return {"survey": survey.to_dict(), "responses": [r.to_dict() for r in self.responses.values() if r.survey_id == survey_id]}

    def get_nps_benchmark_by_segment(self) -> Dict[str, Any]:
        segments = defaultdict(list)
        for r in self.responses.values():
            if r.nps_score is not None:
                key = r.metadata.get("segment", "general") if r.metadata else "general"
                segments[key].append(r.nps_score)
        return {seg: {"avg": round(sum(scores) / len(scores), 1), "count": len(scores), "min": min(scores), "max": max(scores)} for seg, scores in segments.items()}

    def delete_response(self, response_id: str) -> bool:
        if response_id in self.responses:
            del self.responses[response_id]
            self._save_data()
            return True
        return False

    def get_survey_schedule(self) -> List[Dict[str, Any]]:
        active = [s.to_dict() for s in self.surveys.values() if s.status == SurveyStatus.ACTIVE or s.status == SurveyStatus.PAUSED]
        active.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return active

    def update_survey_question(self, survey_id: str, question_id: str, updates: Dict[str, Any]) -> bool:
        s = self.surveys.get(survey_id)
        if not s:
            return False
        for q in s.questions:
            if q.question_id == question_id:
                if "text" in updates:
                    q.text = updates["text"]
                if "required" in updates:
                    q.required = updates["required"]
                if "options" in updates:
                    q.options = updates["options"]
                s.updated_at = datetime.utcnow().isoformat()
                self._save_data()
                return True
        return False


class NpsBatchProcessor:
    def __init__(self, service: NPSSurveyService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_surveys(self, surveys_data: List[Dict[str, Any]]) -> List[Survey]:
        results = []
        for data in surveys_data:
            try:
                survey = self.service.create_survey(
                    title=data["title"], description=data.get("description", ""),
                    survey_type=data.get("survey_type", "nps"),
                    questions=data.get("questions", []),
                    target_segment=data.get("target_segment", "all"),
                    created_by=data.get("created_by", ""),
                )
                results.append(survey)
                self.batch_log.append({"action": "create_survey", "survey_id": survey.survey_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "create_survey", "title": data.get("title"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_survey_responses(responses: List[SurveyResponse], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(responses)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [r.to_dict() for r in responses[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_nps_summary(service: NPSSurveyService, survey_id: str) -> Dict[str, Any]:
    responses = [r for r in service.responses.values() if r.survey_id == survey_id and r.nps_score is not None]
    if not responses:
        return {"survey_id": survey_id, "total_responses": 0}
    promoters = sum(1 for r in responses if r.nps_score >= 9)
    passives = sum(1 for r in responses if 7 <= r.nps_score <= 8)
    detractors = sum(1 for r in responses if r.nps_score <= 6)
    total = len(responses)
    nps = round((promoters - detractors) / total * 100, 1)
    return {
        "survey_id": survey_id,
        "total": total,
        "promoters": promoters, "promoter_pct": round(promoters / total * 100, 1),
        "passives": passives, "passive_pct": round(passives / total * 100, 1),
        "detractors": detractors, "detractor_pct": round(detractors / total * 100, 1),
        "nps_score": nps,
    }


class NpsAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_survey_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    return errors


def merge_survey_customers(service: NPSSurveyService, source: str, target: str) -> int:
    count = 0
    for r in service.responses.values():
        if r.customer_id == source:
            r.customer_id = target
            count += 1
    if count:
        service._save_data()
    return count


def get_detractor_insights(service: NPSSurveyService, survey_id: str) -> List[Dict[str, Any]]:
    responses = [r for r in service.responses.values() if r.survey_id == survey_id and r.nps_score is not None and r.nps_score <= 6 and r.comments]
    common_words: Dict[str, int] = {}
    for r in responses:
        if r.comments:
            for word in r.comments.lower().split():
                if len(word) > 3:
                    common_words[word] = common_words.get(word, 0) + 1
    top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"theme": word, "frequency": count, "sentiment": "negative"} for word, count in top_themes]

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
