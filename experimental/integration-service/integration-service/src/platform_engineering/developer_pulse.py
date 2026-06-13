"""Developer Feedback & Pulse — Periodic NPS/internal surveys with sentiment tracking."""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SurveyType(str, Enum):
    NPS = "nps"
    SATISFACTION = "satisfaction"
    WELLBEING = "wellbeing"
    PLATFORM = "platform"
    TOOLING = "tooling"
    PROCESS = "process"
    CUSTOM = "custom"


class SurveyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


NPS_QUESTION = "How likely are you to recommend this platform to a colleague?"

SATISFACTION_QUESTIONS = [
    "How satisfied are you with the developer experience?",
    "How satisfied are you with the CI/CD pipeline?",
    "How satisfied are you with the infrastructure provisioning?",
    "How satisfied are you with the monitoring and observability?",
    "How satisfied are you with the documentation quality?",
    "How satisfied are you with the on-call experience?",
    "How satisfied are you with team collaboration?",
]


class SurveyResponse:
    def __init__(self, response_id: str, survey_id: str, respondent_id: str):
        self.response_id = response_id
        self.survey_id = survey_id
        self.respondent_id = respondent_id
        self.answers: dict[str, Any] = {}
        self.nps_score: Optional[int] = None
        self.comments: str = ""
        self.submitted_at: datetime = datetime.utcnow()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "survey_id": self.survey_id,
            "respondent_id": self.respondent_id,
            "answers": self.answers,
            "nps_score": self.nps_score,
            "comments": self.comments,
            "submitted_at": self.submitted_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SurveyResponse":
        sr = cls(data["response_id"], data["survey_id"], data["respondent_id"])
        sr.answers = data.get("answers", {})
        sr.nps_score = data.get("nps_score")
        sr.comments = data.get("comments", "")
        if data.get("submitted_at"):
            sr.submitted_at = datetime.fromisoformat(data["submitted_at"])
        sr.metadata = data.get("metadata", {})
        return sr


class Survey:
    def __init__(self, survey_id: str, title: str, survey_type: SurveyType, created_by: str):
        self.survey_id = survey_id
        self.title = title
        self.survey_type = survey_type
        self.created_by = created_by
        self.description: str = ""
        self.status: SurveyStatus = SurveyStatus.DRAFT
        self.questions: list[dict[str, Any]] = []
        self.target_audience: list[str] = []
        self.team_ids: list[str] = []
        self.anonymous: bool = True
        self.allow_comments: bool = True
        self.periodic: str = "once"
        self.periodic_interval_days: int = 0
        self.open_at: Optional[datetime] = None
        self.close_at: Optional[datetime] = None
        self.reminder_days: int = 3
        self.max_responses: int = 0
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_question(self, question_text: str, question_type: str = "rating",
                     required: bool = True, options: list[str] = None,
                     scale_min: int = 0, scale_max: int = 10) -> dict[str, Any]:
        q = {
            "question_id": str(uuid.uuid4()),
            "text": question_text,
            "type": question_type,
            "required": required,
            "options": options or [],
            "scale_min": scale_min,
            "scale_max": scale_max,
        }
        self.questions.append(q)
        return q

    def to_dict(self) -> dict[str, Any]:
        return {
            "survey_id": self.survey_id,
            "title": self.title,
            "survey_type": self.survey_type.value,
            "created_by": self.created_by,
            "description": self.description,
            "status": self.status.value,
            "questions": self.questions,
            "target_audience": self.target_audience,
            "team_ids": self.team_ids,
            "anonymous": self.anonymous,
            "allow_comments": self.allow_comments,
            "periodic": self.periodic,
            "periodic_interval_days": self.periodic_interval_days,
            "open_at": self.open_at.isoformat() if self.open_at else None,
            "close_at": self.close_at.isoformat() if self.close_at else None,
            "reminder_days": self.reminder_days,
            "max_responses": self.max_responses,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Survey":
        s = cls(data["survey_id"], data["title"], SurveyType(data["survey_type"]), data["created_by"])
        s.description = data.get("description", "")
        s.status = SurveyStatus(data.get("status", "draft"))
        s.questions = data.get("questions", [])
        s.target_audience = data.get("target_audience", [])
        s.team_ids = data.get("team_ids", [])
        s.anonymous = data.get("anonymous", True)
        s.allow_comments = data.get("allow_comments", True)
        s.periodic = data.get("periodic", "once")
        s.periodic_interval_days = data.get("periodic_interval_days", 0)
        if data.get("open_at"):
            s.open_at = datetime.fromisoformat(data["open_at"])
        if data.get("close_at"):
            s.close_at = datetime.fromisoformat(data["close_at"])
        s.reminder_days = data.get("reminder_days", 3)
        s.max_responses = data.get("max_responses", 0)
        if data.get("created_at"):
            s.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            s.updated_at = datetime.fromisoformat(data["updated_at"])
        return s


class DeveloperPulseManager:
    def __init__(self):
        self.surveys: dict[str, Survey] = {}
        self.responses: dict[str, SurveyResponse] = {}
        self.sentiment_history: list[dict[str, Any]] = []

    def create_survey(self, title: str, survey_type: SurveyType, created_by: str) -> Survey:
        sid = str(uuid.uuid4())
        s = Survey(sid, title, survey_type, created_by)
        if survey_type == SurveyType.NPS:
            s.add_question(NPS_QUESTION, "nps", True, scale_min=0, scale_max=10)
            s.description = "How likely are you to recommend our platform?"
        elif survey_type == SurveyType.SATISFACTION:
            for q in SATISFACTION_QUESTIONS:
                s.add_question(q, "rating", True, scale_min=1, scale_max=5)
            s.description = "Rate your satisfaction across key areas."
        self.surveys[sid] = s
        logger.info("Created %s survey: %s by %s", survey_type.value, title, created_by)
        return s

    def get_survey(self, survey_id: str) -> Optional[Survey]:
        return self.surveys.get(survey_id)

    def update_survey(self, survey_id: str, updates: dict[str, Any]) -> Optional[Survey]:
        s = self.surveys.get(survey_id)
        if not s:
            return None
        for k, v in updates.items():
            if k == "status" and isinstance(v, str):
                setattr(s, k, SurveyStatus(v))
            elif k == "survey_type" and isinstance(v, str):
                setattr(s, k, SurveyType(v))
            elif hasattr(s, k):
                setattr(s, k, v)
        s.updated_at = datetime.utcnow()
        return s

    def launch_survey(self, survey_id: str) -> Optional[Survey]:
        s = self.surveys.get(survey_id)
        if not s:
            return None
        s.status = SurveyStatus.ACTIVE
        s.open_at = datetime.utcnow()
        s.updated_at = datetime.utcnow()
        return s

    def close_survey(self, survey_id: str) -> Optional[Survey]:
        s = self.surveys.get(survey_id)
        if not s:
            return None
        s.status = SurveyStatus.CLOSED
        s.close_at = datetime.utcnow()
        s.updated_at = datetime.utcnow()
        return s

    def submit_response(self, survey_id: str, respondent_id: str, answers: dict[str, Any],
                        nps_score: int = None, comments: str = "") -> Optional[SurveyResponse]:
        s = self.surveys.get(survey_id)
        if not s or s.status != SurveyStatus.ACTIVE:
            return None
        existing = [r for r in self.responses.values()
                    if r.survey_id == survey_id and r.respondent_id == respondent_id]
        if existing:
            return None
        rid = str(uuid.uuid4())
        r = SurveyResponse(rid, survey_id, respondent_id)
        r.answers = answers
        r.nps_score = nps_score
        r.comments = comments
        self.responses[rid] = r
        if nps_score is not None:
            self.sentiment_history.append({
                "survey_id": survey_id,
                "nps_score": nps_score,
                "comments_snippet": comments[:200] if comments else "",
                "recorded_at": datetime.utcnow().isoformat(),
            })
        return r

    def get_survey_responses(self, survey_id: str) -> list[SurveyResponse]:
        return [r for r in self.responses.values() if r.survey_id == survey_id]

    def calculate_nps(self, survey_id: str) -> Optional[dict[str, Any]]:
        responses = self.get_survey_responses(survey_id)
        if not responses:
            return None
        scores = [r.nps_score for r in responses if r.nps_score is not None]
        if not scores:
            return None
        promoters = sum(1 for s in scores if s >= 9)
        passives = sum(1 for s in scores if 7 <= s <= 8)
        detractors = sum(1 for s in scores if s <= 6)
        total = len(scores)
        nps_value = round(((promoters - detractors) / total) * 100, 1)
        return {
            "survey_id": survey_id,
            "nps_score": nps_value,
            "promoters": promoters,
            "promoters_pct": round(promoters / total * 100, 1),
            "detractors": detractors,
            "detractors_pct": round(detractors / total * 100, 1),
            "passives": passives,
            "total_responses": total,
            "response_rate": round(total / max(len(s.target_audience), 1) * 100, 1),
        }

    def calculate_average_nps(self) -> Optional[dict[str, Any]]:
        nps_values = []
        for sid in self.surveys:
            nps = self.calculate_nps(sid)
            if nps and nps["nps_score"] is not None:
                nps_values.append(nps["nps_score"])
        if not nps_values:
            return None
        return {
            "average_nps": round(sum(nps_values) / len(nps_values), 1),
            "min_nps": min(nps_values),
            "max_nps": max(nps_values),
            "surveys_analyzed": len(nps_values),
        }

    def get_sentiment_trend(self, days: int = 90) -> list[dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [h for h in self.sentiment_history
                if datetime.fromisoformat(h["recorded_at"]) >= cutoff]

    def get_pulse_summary(self) -> dict[str, Any]:
        total_surveys = len(self.surveys)
        active = len([s for s in self.surveys.values() if s.status == SurveyStatus.ACTIVE])
        avg_nps = self.calculate_average_nps()
        return {
            "total_surveys": total_surveys,
            "active_surveys": active,
            "total_responses": len(self.responses),
            "average_nps": avg_nps["average_nps"] if avg_nps else None,
            "sentiment_records": len(self.sentiment_history),
            "by_type": {
                t.value: len([s for s in self.surveys.values() if s.survey_type.value == t.value])
                for t in SurveyType
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "surveys": {sid: s.to_dict() for sid, s in self.surveys.items()},
            "responses": {rid: r.to_dict() for rid, r in self.responses.items()},
            "sentiment_history": self.sentiment_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeveloperPulseManager":
        mgr = cls()
        for sid, sdata in data.get("surveys", {}).items():
            mgr.surveys[sid] = Survey.from_dict(sdata)
        for rid, rdata in data.get("responses", {}).items():
            mgr.responses[rid] = SurveyResponse.from_dict(rdata)
        mgr.sentiment_history = data.get("sentiment_history", [])
        return mgr

    def get_detailed_nps_breakdown(self, survey_id: str) -> dict[str, Any]:
        nps = self.calculate_nps(survey_id)
        if not nps:
            return {}
        responses = self.get_survey_responses(survey_id)
        comments = [r.comments for r in responses if r.comments.strip()]
        return {
            **nps,
            "comments_count": len(comments),
            "comments_snippets": comments[:10],
            "score_distribution": {
                str(s): len([r for r in responses if r.nps_score == s])
                for s in range(0, 11)
            },
        }

    def export_survey_results(self, survey_id: str, format: str = "json") -> Any:
        survey = self.surveys.get(survey_id)
        if not survey:
            return None
        responses = self.get_survey_responses(survey_id)
        if format == "json":
            return {
                "survey": survey.to_dict(),
                "responses": [r.to_dict() for r in responses],
                "nps": self.calculate_nps(survey_id),
            }
        return None

    def segment_analysis(self, survey_id: str, segment_by: str = "team") -> dict[str, Any]:
        responses = self.get_survey_responses(survey_id)
        if not responses:
            return {}
        segments: dict[str, list[int]] = {}
        for r in responses:
            segment = r.metadata.get(segment_by, "unknown")
            if segment not in segments:
                segments[segment] = []
            if r.nps_score is not None:
                segments[segment].append(r.nps_score)
        return {
            "segment_by": segment_by,
            "segments": {
                seg: {
                    "count": len(scores),
                    "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
                    "promoters": sum(1 for s in scores if s >= 9),
                    "detractors": sum(1 for s in scores if s <= 6),
                }
                for seg, scores in segments.items()
            },
        }

    def clone_survey(self, survey_id: str, new_title: str, created_by: str) -> Optional[Survey]:
        source = self.surveys.get(survey_id)
        if not source:
            return None
        s = self.create_survey(new_title, source.survey_type, created_by)
        s.description = source.description
        s.questions = [dict(q) for q in source.questions]
        s.target_audience = list(source.target_audience)
        s.team_ids = list(source.team_ids)
        s.anonymous = source.anonymous
        s.allow_comments = source.allow_comments
        s.periodic = source.periodic
        s.periodic_interval_days = source.periodic_interval_days
        return s

    def get_analytics_overview(self) -> dict[str, Any]:
        total_responses = len(self.responses)
        surveys_with_responses = len(set(r.survey_id for r in self.responses.values()))
        avg_nps = self.calculate_average_nps()
        response_rate = round(total_responses / max(sum(len(s.target_audience) for s in self.surveys.values()), 1) * 100, 1)
        return {
            "total_surveys": len(self.surveys),
            "surveys_with_responses": surveys_with_responses,
            "total_responses": total_responses,
            "response_rate_pct": response_rate,
            "average_nps": avg_nps["average_nps"] if avg_nps else None,
            "sentiment_trend": self.get_sentiment_trend(90),
        }

    def batch_create_surveys(self, survey_defs: list[dict[str, Any]]) -> list[str]:
        ids = []
        for sd in survey_defs:
            s = self.create_survey(sd["title"], SurveyType(sd.get("survey_type", "custom")), sd["created_by"])
            if sd.get("questions"):
                s.questions = sd["questions"]
            if sd.get("target_audience"):
                s.target_audience = sd["target_audience"]
            if sd.get("team_ids"):
                s.team_ids = sd["team_ids"]
            if sd.get("periodic"):
                s.periodic = sd["periodic"]
            ids.append(s.survey_id)
        return ids

    def get_response_rate(self, survey_id: str) -> dict[str, Any]:
        survey = self.surveys.get(survey_id)
        if not survey:
            return {"error": "Survey not found"}
        total_invited = len(survey.target_audience)
        total_responses = len(self.get_survey_responses(survey_id))
        return {"survey_id": survey_id, "title": survey.title,
                "total_invited": total_invited, "total_responses": total_responses,
                "response_rate": round(total_responses / max(total_invited, 1) * 100, 1)}

    def get_surveys_by_type(self, survey_type: SurveyType) -> list[Survey]:
        return [s for s in self.surveys.values() if s.survey_type == survey_type]

    def archive_survey(self, survey_id: str) -> bool:
        survey = self.surveys.get(survey_id)
        if not survey:
            return False
        survey.status = SurveyStatus.ARCHIVED
        survey.updated_at = datetime.utcnow()
        return True

    def get_anonymized_responses(self, survey_id: str) -> list[dict[str, Any]]:
        responses = self.get_survey_responses(survey_id)
        anonymized = []
        for r in responses:
            anon = {
                "response_id": r.response_id, "survey_id": r.survey_id,
                "answers": r.answers, "submitted_at": r.submitted_at.isoformat(),
            }
            anonymized.append(anon)
        return anonymized

    def aggregate_survey_results(self, survey_id: str) -> dict[str, Any]:
        responses = self.get_survey_responses(survey_id)
        survey = self.surveys.get(survey_id)
        if not responses or not survey:
            return {"error": "No data"}
        question_aggs: dict[str, dict[str, Any]] = {}
        for r in responses:
            for q, a in r.answers.items():
                if q not in question_aggs:
                    question_aggs[q] = {"values": [], "count": 0}
                question_aggs[q]["values"].append(a)
                question_aggs[q]["count"] += 1
        aggregated = {}
        for q, data in question_aggs.items():
            numeric = [v for v in data["values"] if isinstance(v, (int, float))]
            text = [v for v in data["values"] if isinstance(v, str)]
            agg: dict[str, Any] = {"total_responses": data["count"]}
            if numeric:
                agg["avg"] = round(sum(numeric) / len(numeric), 2)
                agg["min"] = min(numeric)
                agg["max"] = max(numeric)
            if text:
                from collections import Counter
                words = [w.lower() for t in text for w in t.split() if len(w) > 3]
                agg["common_words"] = Counter(words).most_common(10)
                agg["response_count"] = len(text)
            aggregated[q] = agg
        return {"survey_id": survey_id, "title": survey.title, "total_responses": len(responses),
                "aggregated": aggregated}

    def get_sentiment_trend(self, survey_type: SurveyType = SurveyType.NPS, months: int = 6) -> dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        surveys = [s for s in self.surveys.values()
                   if s.survey_type == survey_type and s.created_at >= cutoff]
        monthly: dict[str, list[float]] = {}
        for s in surveys:
            month_key = s.created_at.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = []
            for r in self.get_survey_responses(s.survey_id):
                for v in r.answers.values():
                    if isinstance(v, (int, float)):
                        monthly[month_key].append(v)
        trend = {}
        for month, scores in sorted(monthly.items()):
            trend[month] = {"avg": round(sum(scores) / len(scores), 2), "count": len(scores)}
        return {"survey_type": survey_type.value, "months": months, "trend": trend}

    def export_survey_data(self, survey_id: str, format: str = "json") -> Any:
        survey = self.surveys.get(survey_id)
        if not survey:
            return {"error": "Survey not found"}
        responses = self.get_survey_responses(survey_id)
        if format == "csv":
            lines = ["response_id,submitted_at"]
            if responses:
                for q in responses[0].answers:
                    lines[0] += f",{q}"
            for r in responses:
                line = f"{r.response_id},{r.submitted_at.isoformat()}"
                for v in r.answers.values():
                    line += f",{v}"
                lines.append(line)
            return "\n".join(lines)
        return {
            "survey_id": survey_id, "title": survey.title, "responses": [
                {"response_id": r.response_id, "answers": r.answers, "submitted_at": r.submitted_at.isoformat()}
                for r in responses
            ]
        }

    def schedule_survey(self, title: str, questions: list[str], survey_type: SurveyType = SurveyType.NPS,
                         target_audience: list[str] | None = None, cron_expression: str = "0 0 1 * *") -> dict[str, Any]:
        survey = self.create_survey(title, questions, survey_type, target_audience or [])
        schedule_id = str(uuid.uuid4())
        schedule = {
            "schedule_id": schedule_id, "survey_id": survey.survey_id,
            "cron_expression": cron_expression, "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_schedules"):
            self._schedules: list[dict[str, Any]] = []
        self._schedules.append(schedule)
        return {"survey": survey.to_dict(), "schedule": schedule}

    def get_schedules(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_schedules", []))

    def pause_schedule(self, schedule_id: str) -> bool:
        for s in getattr(self, "_schedules", []):
            if s["schedule_id"] == schedule_id:
                s["status"] = "paused"
                return True
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        for s in getattr(self, "_schedules", []):
            if s["schedule_id"] == schedule_id:
                s["status"] = "active"
                return True
        return False

    def get_response_insights(self, survey_id: str) -> dict[str, Any]:
        responses = self.get_survey_responses(survey_id)
        if not responses:
            return {"error": "No responses"}
        nps_score = 0
        promoters = 0
        detractors = 0
        passives = 0
        for r in responses:
            nps_val = r.answers.get("nps_score") or r.answers.get("rating") or r.answers.get("score")
            if isinstance(nps_val, (int, float)):
                if nps_val >= 9:
                    promoters += 1
                elif nps_val <= 6:
                    detractors += 1
                else:
                    passives += 1
        total = promoters + detractors + passives
        if total > 0:
            nps_score = round((promoters - detractors) / total * 100, 1)
        return {
            "survey_id": survey_id, "total_responses": len(responses),
            "promoters": promoters, "passives": passives, "detractors": detractors,
            "nps_score": nps_score,
            "response_rate": round(len(responses) / max(len(self.surveys.get(survey_id, Survey).target_audience if hasattr(self.surveys.get(survey_id, Survey), 'target_audience') else []), 1) * 100, 1),
        }

    def bulk_send_reminders(self, survey_id: str) -> dict[str, Any]:
        survey = self.surveys.get(survey_id)
        if not survey:
            return {"error": "Survey not found"}
        responded = {r.user_id for r in self.get_survey_responses(survey_id) if r.user_id}
        pending = [uid for uid in survey.target_audience if uid not in responded]
        return {"survey_id": survey_id, "reminders_sent": len(pending),
                "pending_users": pending[:10], "total_pending": len(pending)}

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
        return {"total_items": 0, "avg_score": 0.0, "completion_rate": 0.0}

    def validate_operation(self) -> Dict[str, Any]:
        return {"valid": True, "checks_passed": 0, "checks_failed": 0}

class PlatformOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PlatformBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="parallel")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)

    def update_progress(self, pct: int) -> None:
        self.progress = min(pct, 100)
        if self.progress >= 100:
            self.status = "completed"

class PlatformMetrics(BaseModel):
    metric_name: str
    value: float
    unit: str = Field(default="count")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: List[PlatformMetrics] = []

    def record(self, name: str, value: float, unit: str = "count", labels: Optional[Dict[str, str]] = None) -> None:
        self._metrics.append(PlatformMetrics(metric_name=name, value=value, unit=unit, labels=labels or {}))

    def query(self, name: str, since: Optional[datetime] = None) -> List[PlatformMetrics]:
        filtered = [m for m in self._metrics if m.metric_name == name]
        if since:
            filtered = [m for m in filtered if m.timestamp >= since]
        return filtered

    def aggregate(self, name: str, operation: str = "avg") -> float:
        values = [m.value for m in self._metrics if m.metric_name == name]
        if not values:
            return 0.0
        if operation == "avg":
            return round(sum(values) / len(values), 4)
        elif operation == "sum":
            return round(sum(values), 4)
        elif operation == "max":
            return round(max(values), 4)
        elif operation == "min":
            return round(min(values), 4)
        return 0.0

    def get_all_summary(self) -> Dict[str, Any]:
        names = set(m.metric_name for m in self._metrics)
        return {n: {"count": sum(1 for m in self._metrics if m.metric_name == n),
                     "avg": self.aggregate(n, "avg")} for n in names}

class ConfigManager:
    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = defaults or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def update(self, config: Dict[str, Any]) -> None:
        self._config.update(config)

    def export(self) -> Dict[str, Any]:
        return dict(self._config)

    def validate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        for key, rules in schema.items():
            value = self._config.get(key)
            if rules.get("required") and value is None:
                errors.append(f"Missing: {key}")
            if rules.get("type") and value is not None and not isinstance(value, rules["type"]):
                errors.append(f"Type mismatch: {key}")
        return {"valid": len(errors) == 0, "errors": errors}

class AuditTrail:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, user: str, action: str, resource: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({"user": user, "action": action, "resource": resource,
                               "details": details or {}, "timestamp": datetime.utcnow().isoformat()})

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def search(self, user: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._entries
        if user:
            results = [e for e in results if e["user"] == user]
        if action:
            results = [e for e in results if e["action"] == action]
        return results

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class HealthChecker:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_result": None, "last_run": None}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name, check in self._checks.items():
            try:
                result = await check["fn"]()
                check["last_result"] = result
                check["last_run"] = datetime.utcnow()
                results[name] = result
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_result": c["last_result"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
