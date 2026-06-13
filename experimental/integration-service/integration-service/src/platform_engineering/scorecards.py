"""Developer Scorecards — DORA metrics, team benchmarks, productivity tracking."""

import json
import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


def calculate_dora_score(deploy_frequency: float, lead_time_hours: float, mttr_hours: float, change_failure_rate: float) -> dict[str, Any]:
    df_score = min(deploy_frequency / 10.0, 1.0) * 25
    lt_score = max(0, 1.0 - (lead_time_hours / 168.0)) * 25
    mr_score = max(0, 1.0 - (mttr_hours / 24.0)) * 25
    cf_score = max(0, 1.0 - change_failure_rate) * 25
    total = round(df_score + lt_score + mr_score + cf_score, 1)
    return {
        "deploy_frequency_score": round(df_score, 1),
        "lead_time_score": round(lt_score, 1),
        "mttr_score": round(mr_score, 1),
        "change_failure_score": round(cf_score, 1),
        "total_score": total,
        "rating": _dora_rating(total),
    }


def _dora_rating(score: float) -> str:
    if score >= 90:
        return "elite"
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


DORA_BENCHMARKS = {
    "elite": {"deploy_frequency": "multiple per day", "lead_time": "< 1 hour", "mttr": "< 1 hour", "change_failure_rate": "0-5%"},
    "high": {"deploy_frequency": "daily to weekly", "lead_time": "1 day to 1 week", "mttr": "< 1 day", "change_failure_rate": "6-10%"},
    "medium": {"deploy_frequency": "weekly to monthly", "lead_time": "1 week to 1 month", "mttr": "< 1 week", "change_failure_rate": "11-15%"},
    "low": {"deploy_frequency": "monthly or less", "lead_time": "> 1 month", "mttr": "> 1 week", "change_failure_rate": "16%+"},
}


class DeveloperTeam:
    def __init__(self, team_id: str, name: str, organization: str):
        self.team_id = team_id
        self.name = name
        self.organization = organization
        self.members: list[str] = []
        self.services: list[str] = []
        self.created_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "organization": self.organization,
            "members": self.members,
            "services": self.services,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeveloperTeam":
        dt = cls(data["team_id"], data["name"], data["organization"])
        dt.members = data.get("members", [])
        dt.services = data.get("services", [])
        if data.get("created_at"):
            dt.created_at = datetime.fromisoformat(data["created_at"])
        return dt


class DoraMetricsSnapshot:
    def __init__(self, snapshot_id: str, team_id: str, period_start: datetime, period_end: datetime):
        self.snapshot_id = snapshot_id
        self.team_id = team_id
        self.period_start = period_start
        self.period_end = period_end
        self.deploy_count: int = 0
        self.lead_time_total_hours: float = 0.0
        self.incident_count: int = 0
        self.mttr_total_hours: float = 0.0
        self.change_failure_count: int = 0
        self.change_total_count: int = 0
        self.deploy_frequency: float = 0.0
        self.avg_lead_time_hours: float = 0.0
        self.avg_mttr_hours: float = 0.0
        self.change_failure_rate: float = 0.0
        self.dora_score: dict[str, Any] = {}
        self.created_at: datetime = datetime.utcnow()

    def calculate(self):
        days = max((self.period_end - self.period_start).days, 1)
        self.deploy_frequency = round(self.deploy_count / days, 2)
        self.avg_lead_time_hours = round(self.lead_time_total_hours / max(self.deploy_count, 1), 1)
        self.avg_mttr_hours = round(self.mttr_total_hours / max(self.incident_count, 1), 1)
        self.change_failure_rate = round(
            self.change_failure_count / max(self.change_total_count, 1), 3
        )
        self.dora_score = calculate_dora_score(
            self.deploy_frequency, self.avg_lead_time_hours,
            self.avg_mttr_hours, self.change_failure_rate,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "team_id": self.team_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "deploy_count": self.deploy_count,
            "lead_time_total_hours": self.lead_time_total_hours,
            "incident_count": self.incident_count,
            "mttr_total_hours": self.mttr_total_hours,
            "change_failure_count": self.change_failure_count,
            "change_total_count": self.change_total_count,
            "deploy_frequency": self.deploy_frequency,
            "avg_lead_time_hours": self.avg_lead_time_hours,
            "avg_mttr_hours": self.avg_mttr_hours,
            "change_failure_rate": self.change_failure_rate,
            "dora_score": self.dora_score,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DoraMetricsSnapshot":
        snap = cls(
            data["snapshot_id"], data["team_id"],
            datetime.fromisoformat(data["period_start"]),
            datetime.fromisoformat(data["period_end"]),
        )
        snap.deploy_count = data.get("deploy_count", 0)
        snap.lead_time_total_hours = data.get("lead_time_total_hours", 0.0)
        snap.incident_count = data.get("incident_count", 0)
        snap.mttr_total_hours = data.get("mttr_total_hours", 0.0)
        snap.change_failure_count = data.get("change_failure_count", 0)
        snap.change_total_count = data.get("change_total_count", 0)
        snap.deploy_frequency = data.get("deploy_frequency", 0.0)
        snap.avg_lead_time_hours = data.get("avg_lead_time_hours", 0.0)
        snap.avg_mttr_hours = data.get("avg_mttr_hours", 0.0)
        snap.change_failure_rate = data.get("change_failure_rate", 0.0)
        snap.dora_score = data.get("dora_score", {})
        if data.get("created_at"):
            snap.created_at = datetime.fromisoformat(data["created_at"])
        return snap


class ScorecardsManager:
    def __init__(self):
        self.teams: dict[str, DeveloperTeam] = {}
        self.snapshots: dict[str, DoraMetricsSnapshot] = {}
        self.individual_scores: dict[str, list[dict[str, Any]]] = {}

    def create_team(self, name: str, organization: str) -> DeveloperTeam:
        tid = str(uuid.uuid4())
        team = DeveloperTeam(tid, name, organization)
        self.teams[tid] = team
        logger.info("Created developer team %s (%s)", name, organization)
        return team

    def get_team(self, team_id: str) -> Optional[DeveloperTeam]:
        return self.teams.get(team_id)

    def add_team_member(self, team_id: str, user_id: str) -> bool:
        team = self.teams.get(team_id)
        if not team:
            return False
        if user_id not in team.members:
            team.members.append(user_id)
        return True

    def create_snapshot(self, team_id: str, period_start: datetime, period_end: datetime,
                        deploy_count: int, lead_time_total: float,
                        incident_count: int, mttr_total: float,
                        change_failure: int, change_total: int) -> Optional[DoraMetricsSnapshot]:
        if team_id not in self.teams:
            return None
        sid = str(uuid.uuid4())
        snap = DoraMetricsSnapshot(sid, team_id, period_start, period_end)
        snap.deploy_count = deploy_count
        snap.lead_time_total_hours = lead_time_total
        snap.incident_count = incident_count
        snap.mttr_total_hours = mttr_total
        snap.change_failure_count = change_failure
        snap.change_total_count = change_total
        snap.calculate()
        self.snapshots[sid] = snap
        return snap

    def get_team_snapshots(self, team_id: str, limit: int = 12) -> list[DoraMetricsSnapshot]:
        snaps = [s for s in self.snapshots.values() if s.team_id == team_id]
        return sorted(snaps, key=lambda s: s.period_start, reverse=True)[:limit]

    def get_latest_snapshot(self, team_id: str) -> Optional[DoraMetricsSnapshot]:
        snaps = self.get_team_snapshots(team_id, limit=1)
        return snaps[0] if snaps else None

    def get_team_benchmarks(self) -> dict[str, Any]:
        all_scores = []
        for snap in self.snapshots.values():
            if snap.dora_score:
                all_scores.append({"team_id": snap.team_id, "score": snap.dora_score["total_score"]})
        if not all_scores:
            return {}
        scores = [s["score"] for s in all_scores]
        return {
            "average": round(sum(scores) / len(scores), 1),
            "median": round(sorted(scores)[len(scores) // 2], 1),
            "min": min(scores),
            "max": max(scores),
            "team_count": len(set(s["team_id"] for s in all_scores)),
        }

    def record_individual_score(self, user_id: str, metric: str, value: float, period: str = "weekly"):
        if user_id not in self.individual_scores:
            self.individual_scores[user_id] = []
        entry = {
            "user_id": user_id,
            "metric": metric,
            "value": value,
            "period": period,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self.individual_scores[user_id].append(entry)
        return entry

    def get_individual_scores(self, user_id: str, metric: str = "", limit: int = 50) -> list[dict[str, Any]]:
        scores = self.individual_scores.get(user_id, [])
        if metric:
            scores = [s for s in scores if s["metric"] == metric]
        return sorted(scores, key=lambda s: s["recorded_at"], reverse=True)[:limit]

    def get_dora_leaderboard(self) -> list[dict[str, Any]]:
        leaderboard = []
        for team_id in self.teams:
            snap = self.get_latest_snapshot(team_id)
            if snap and snap.dora_score:
                team = self.teams[team_id]
                leaderboard.append({
                    "team_id": team_id,
                    "team_name": team.name,
                    "organization": team.organization,
                    "total_score": snap.dora_score["total_score"],
                    "rating": snap.dora_score["rating"],
                    "deploy_frequency": snap.deploy_frequency,
                    "avg_lead_time_hours": snap.avg_lead_time_hours,
                    "change_failure_rate": snap.change_failure_rate,
                })
        return sorted(leaderboard, key=lambda x: x["total_score"], reverse=True)

    def get_scorecards_summary(self) -> dict[str, Any]:
        return {
            "total_teams": len(self.teams),
            "total_snapshots": len(self.snapshots),
            "benchmarks": self.get_team_benchmarks(),
            "leaderboard": self.get_dora_leaderboard()[:5],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "teams": {tid: t.to_dict() for tid, t in self.teams.items()},
            "snapshots": {sid: s.to_dict() for sid, s in self.snapshots.items()},
            "individual_scores": self.individual_scores,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScorecardsManager":
        mgr = cls()
        for tid, tdata in data.get("teams", {}).items():
            mgr.teams[tid] = DeveloperTeam.from_dict(tdata)
        for sid, sdata in data.get("snapshots", {}).items():
            mgr.snapshots[sid] = DoraMetricsSnapshot.from_dict(sdata)
        mgr.individual_scores = data.get("individual_scores", {})
        return mgr

    def get_trend_analysis(self, team_id: str, metric: str = "total_score", periods: int = 6) -> list[dict[str, Any]]:
        snaps = self.get_team_snapshots(team_id, limit=periods)
        trend = []
        for snap in reversed(snaps):
            if snap.dora_score:
                trend.append({
                    "period_start": snap.period_start.isoformat(),
                    "period_end": snap.period_end.isoformat(),
                    "metric": metric,
                    "value": snap.dora_score.get(metric, snap.dora_score.get("total_score", 0)),
                })
        return trend

    def export_team_scores(self, team_id: str, format: str = "json") -> Any:
        team = self.teams.get(team_id)
        if not team:
            return None
        snaps = self.get_team_snapshots(team_id)
        if format == "json":
            return {
                "team": team.to_dict(),
                "snapshots": [s.to_dict() for s in snaps],
                "benchmarks": self.get_team_benchmarks(),
            }
        return None

    def compare_teams(self, team_ids: list[str]) -> list[dict[str, Any]]:
        comparison = []
        for tid in team_ids:
            snap = self.get_latest_snapshot(tid)
            team = self.teams.get(tid)
            if snap and team:
                comparison.append({
                    "team_id": tid,
                    "team_name": team.name,
                    "total_score": snap.dora_score.get("total_score", 0),
                    "rating": snap.dora_score.get("rating", ""),
                    "deploy_frequency": snap.deploy_frequency,
                    "avg_lead_time_hours": snap.avg_lead_time_hours,
                    "change_failure_rate": snap.change_failure_rate,
                })
        return sorted(comparison, key=lambda x: x["total_score"], reverse=True)

    def bulk_create_teams(self, teams_data: list[dict[str, Any]]) -> list[str]:
        ids = []
        for td in teams_data:
            team = self.create_team(td["name"], td.get("organization", ""))
            if td.get("members"):
                team.members = td["members"]
            if td.get("services"):
                team.services = td["services"]
            ids.append(team.team_id)
        return ids

    def get_period_summary(self, period_start: datetime, period_end: datetime) -> dict[str, Any]:
        period_snaps = [s for s in self.snapshots.values()
                        if s.period_start >= period_start and s.period_end <= period_end]
        if not period_snaps:
            return {"period": f"{period_start.isoformat()}/{period_end.isoformat()}", "snapshots": 0}
        scores = [s.dora_score.get("total_score", 0) for s in period_snaps if s.dora_score]
        return {
            "period": f"{period_start.isoformat()}/{period_end.isoformat()}",
            "snapshots": len(period_snaps),
            "teams_analyzed": len(set(s.team_id for s in period_snaps)),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "ratings": {
                r: len([s for s in period_snaps if s.dora_score and s.dora_score.get("rating") == r])
                for r in ["elite", "high", "medium", "low"]
            },
        }

    def aggregate_all_snapshots(self) -> list[dict[str, Any]]:
        aggregated = []
        for team_id in self.teams:
            team = self.teams[team_id]
            snaps = self.get_team_snapshots(team_id, limit=12)
            if snaps:
                latest = snaps[0]
                aggregated.append({
                    "team_id": team_id,
                    "team_name": team.name,
                    "latest_score": latest.dora_score,
                    "trend": self.get_trend_analysis(team_id),
                    "snapshot_count": len(snaps),
                })
        return aggregated

    def get_team_members(self, team_id: str) -> list[str]:
        team = self.teams.get(team_id)
        return list(team.members) if team else []

    def remove_team_member(self, team_id: str, user_id: str) -> bool:
        team = self.teams.get(team_id)
        if not team or user_id not in team.members:
            return False
        team.members.remove(user_id)
        return True

    def get_teams_by_organization(self, organization: str) -> list[DeveloperTeam]:
        return [t for t in self.teams.values() if t.organization == organization]

    def delete_team(self, team_id: str) -> bool:
        if team_id in self.teams:
            del self.teams[team_id]
            return True
        return False

    def compare_teams(self, team_ids: list[str]) -> list[dict[str, Any]]:
        results = []
        for tid in team_ids:
            team = self.teams.get(tid)
            if not team:
                continue
            snap = self.get_team_snapshots(tid, limit=1)
            results.append({
                "team_id": tid,
                "team_name": team.name,
                "latest_dora_score": snap[0].dora_score if snap else 0,
                "snapshots_count": len(self.get_team_snapshots(tid)),
                "member_count": len(team.members),
            })
        results.sort(key=lambda x: x["latest_dora_score"], reverse=True)
        return results

    def set_goal(self, team_id: str, metric: str, target_value: float, deadline: datetime) -> dict[str, Any]:
        goal_id = str(uuid.uuid4())
        goal = {
            "goal_id": goal_id,
            "team_id": team_id,
            "metric": metric,
            "target_value": target_value,
            "deadline": deadline.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        if not hasattr(self, "_goals"):
            self._goals: list[dict[str, Any]] = []
        self._goals.append(goal)
        return goal

    def get_team_goals(self, team_id: str) -> list[dict[str, Any]]:
        return [g for g in getattr(self, "_goals", []) if g["team_id"] == team_id]

    def check_goal_progress(self, goal_id: str) -> dict[str, Any]:
        goals = getattr(self, "_goals", [])
        goal = next((g for g in goals if g["goal_id"] == goal_id), None)
        if not goal:
            return {"error": "Goal not found"}
        team = self.teams.get(goal["team_id"])
        if not team:
            return {"error": "Team not found"}
        snap = self.get_team_snapshots(goal["team_id"], limit=1)
        current_value = snap[0].dora_score if snap else 0
        progress = round(current_value / max(goal["target_value"], 1) * 100, 1)
        return {"goal_id": goal_id, "metric": goal["metric"], "target": goal["target_value"],
                "current": current_value, "progress_pct": progress, "deadline": goal["deadline"]}

    def close_goal(self, goal_id: str) -> bool:
        goals = getattr(self, "_goals", [])
        for g in goals:
            if g["goal_id"] == goal_id:
                g["status"] = "completed"
                return True
        return False

    def ingest_dora_data(self, team_id: str, data: dict[str, Any]) -> bool:
        team = self.teams.get(team_id)
        if not team:
            return False
        score = self.create_snapshot(team_id)
        score.deployment_frequency = data.get("deployment_frequency", score.deployment_frequency)
        score.lead_time = data.get("lead_time", score.lead_time)
        score.mttr = data.get("mttr", score.mttr)
        score.change_failure_rate = data.get("change_failure_rate", score.change_failure_rate)
        score._calculate_dora_score()
        return True

    def bulk_ingest_dora(self, data_list: list[dict[str, Any]]) -> dict[str, Any]:
        succeeded = 0
        failed = 0
        for entry in data_list:
            if self.ingest_dora_data(entry.get("team_id"), entry):
                succeeded += 1
            else:
                failed += 1
        return {"total": len(data_list), "succeeded": succeeded, "failed": failed}

    def get_team_history(self, team_id: str, days: int = 180) -> list[dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots = self.get_team_snapshots(team_id)
        return [
            {"snapshot_id": s.snapshot_id, "date": s.created_at.isoformat(), "dora_score": s.dora_score,
             "deployment_frequency": s.deployment_frequency, "lead_time": s.lead_time,
             "mttr": s.mttr, "change_failure_rate": s.change_failure_rate}
            for s in snapshots if s.created_at >= cutoff
        ]

    def export_team_scores(self, organization: str = "") -> list[dict[str, Any]]:
        teams = [t for t in self.teams.values() if not organization or t.organization == organization]
        results = []
        for t in teams:
            snap = self.get_team_snapshots(t.team_id, limit=1)
            results.append({
                "team_id": t.team_id, "name": t.name, "organization": t.organization,
                "current_score": snap[0].dora_score if snap else 0,
                "member_count": len(t.members),
            })
        return results

    def get_organization_summary(self, organization: str) -> dict[str, Any]:
        teams = [t for t in self.teams.values() if t.organization == organization]
        scores = []
        for t in teams:
            snap = self.get_team_snapshots(t.team_id, limit=1)
            if snap:
                scores.append(snap[0].dora_score)
        return {
            "organization": organization,
            "team_count": len(teams),
            "avg_dora_score": round(sum(scores) / max(len(scores), 1), 1) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

    def predict_trend(self, team_id: str, weeks_ahead: int = 4) -> dict[str, Any]:
        snaps = self.get_team_snapshots(team_id, limit=12)
        if len(snaps) < 2:
            return {"error": "Not enough data points"}
        recent = [s.dora_score for s in snaps[:weeks_ahead]]
        avg_change = 0
        for i in range(1, len(recent)):
            avg_change += recent[i - 1] - recent[i]
        avg_change /= max(len(recent) - 1, 1)
        predicted = recent[-1] + avg_change * weeks_ahead
        return {"team_id": team_id, "current_score": recent[-1],
                "predicted_score": round(max(0, min(100, predicted)), 1),
                "confidence": "high" if len(snaps) > 8 else "medium" if len(snaps) > 4 else "low"}

    def add_team_tag(self, team_id: str, tag: str) -> bool:
        team = self.teams.get(team_id)
        if not team:
            return False
        if not hasattr(team, "tags"):
            setattr(team, "tags", [])
        if tag not in team.tags:
            team.tags.append(tag)
        return True

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
