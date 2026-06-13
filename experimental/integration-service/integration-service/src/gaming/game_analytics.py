"""Game Analytics integration module."""
import asyncio
import json
import logging
import math
import statistics
import time
import uuid
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class MetricType(Enum):
    PLAYER_COUNT = "player_count"
    SESSION_DURATION = "session_duration"
    REVENUE = "revenue"
    GAMES_PLAYED = "games_played"
    NEW_PLAYERS = "new_players"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    CONCURRENCY = "concurrency"


@dataclass
class PlayerSession:
    session_id: str
    player_id: str
    player_name: str
    game: str
    server_id: str
    start_time: str
    end_time: Optional[str]
    duration_minutes: Optional[int]
    revenue_generated: float
    events_count: int
    kills: int
    deaths: int
    score: int
    region: str
    client_version: str
    device_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "game": self.game,
            "server_id": self.server_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "revenue_generated": self.revenue_generated,
            "events_count": self.events_count,
            "kills": self.kills,
            "deaths": self.deaths,
            "score": self.score,
            "region": self.region,
            "client_version": self.client_version,
            "device_type": self.device_type,
        }


@dataclass
class RevenueRecord:
    revenue_id: str
    timestamp: str
    amount: float
    currency: str
    source: str
    player_id: str
    player_name: str
    game: str
    description: str
    payment_method: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revenue_id": self.revenue_id,
            "timestamp": self.timestamp,
            "amount": self.amount,
            "currency": self.currency,
            "source": self.source,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "game": self.game,
            "description": self.description,
            "payment_method": self.payment_method,
            "status": self.status,
        }


@dataclass
class MetricSnapshot:
    snapshot_id: str
    timestamp: str
    metric: MetricType
    game: str
    value: float
    label: str
    tags: Dict[str, str]
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "metric": self.metric.value,
            "game": self.game,
            "value": self.value,
            "label": self.label,
            "tags": self.tags,
            "source": self.source,
        }


class GameAnalytics:
    """Game analytics tracking for players, sessions, revenue, and engagement."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, PlayerSession] = {}
        self.revenue_records: List[RevenueRecord] = []
        self.metric_history: Dict[str, List[MetricSnapshot]] = defaultdict(list)
        self._running = False
        self._active_players: Set[str] = set()
        self._total_revenue = 0.0
        self._daily_stats: Dict[str, Dict[str, Any]] = {}
        self._peak_concurrent = 0

    async def initialize(self) -> None:
        self._running = True
        logger.info("Game Analytics initialized")

    async def close(self) -> None:
        self._running = False
        logger.info("Game Analytics shut down")

    async def track_session_start(
        self,
        player_id: str,
        player_name: str,
        game: str,
        server_id: str,
        region: str = "NA-East",
        client_version: str = "1.0.0",
        device_type: str = "pc",
    ) -> PlayerSession:
        session = PlayerSession(
            session_id=f"ses-{uuid.uuid4().hex[:12]}",
            player_id=player_id,
            player_name=player_name,
            game=game,
            server_id=server_id,
            start_time=datetime.utcnow().isoformat(),
            end_time=None,
            duration_minutes=None,
            revenue_generated=0.0,
            events_count=0,
            kills=0,
            deaths=0,
            score=0,
            region=region,
            client_version=client_version,
            device_type=device_type,
        )
        self.sessions[session.session_id] = session
        self._active_players.add(player_id)
        self._peak_concurrent = max(self._peak_concurrent, len(self._active_players))

        self._record_metric(MetricType.PLAYER_COUNT, game, len(self._active_players))
        self._record_metric(MetricType.CONCURRENCY, game, len(self._active_players))
        return session

    async def track_session_end(
        self,
        session_id: str,
        kills: int = 0,
        deaths: int = 0,
        score: int = 0,
        revenue: float = 0.0,
    ) -> Optional[PlayerSession]:
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.end_time = datetime.utcnow().isoformat()
        start = datetime.fromisoformat(session.start_time)
        session.duration_minutes = int((datetime.utcnow() - start).total_seconds() / 60)
        session.kills = kills
        session.deaths = deaths
        session.score = score
        session.revenue_generated = revenue
        session.events_count += 1

        self._active_players.discard(session.player_id)

        self._record_metric(MetricType.SESSION_DURATION, session.game, session.duration_minutes)
        self._record_metric(MetricType.PLAYER_COUNT, session.game, len(self._active_players))
        return session

    async def track_revenue(
        self,
        amount: float,
        currency: str = "USD",
        source: str = "server_rental",
        player_id: str = "unknown",
        player_name: str = "unknown",
        game: str = "minecraft",
        description: str = "",
        payment_method: str = "credit_card",
    ) -> RevenueRecord:
        record = RevenueRecord(
            revenue_id=f"rev-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            amount=amount,
            currency=currency,
            source=source,
            player_id=player_id,
            player_name=player_name,
            game=game,
            description=description,
            payment_method=payment_method,
            status="completed",
        )
        self.revenue_records.append(record)
        self._total_revenue += amount

        self._record_metric(MetricType.REVENUE, game, amount)
        return record

    async def get_active_players(
        self,
        game: Optional[str] = None,
        server_id: Optional[str] = None,
    ) -> int:
        return len(self._active_players)

    async def get_player_sessions(
        self,
        player_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        sessions = [
            s for s in self.sessions.values()
            if s.player_id == player_id
        ]
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        return [s.to_dict() for s in sessions[:limit]]

    async def get_revenue_report(
        self,
        game: Optional[str] = None,
        source: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        records = [r for r in self.revenue_records if r.timestamp >= cutoff]

        if game:
            records = [r for r in records if r.game == game]
        if source:
            records = [r for r in records if r.source == source]

        total = sum(r.amount for r in records)
        daily = defaultdict(float)
        for r in records:
            day = r.timestamp[:10]
            daily[day] += r.amount

        source_breakdown = defaultdict(float)
        for r in records:
            source_breakdown[r.source] += r.amount

        return {
            "period_days": days,
            "total_revenue": round(total, 2),
            "transaction_count": len(records),
            "avg_transaction": round(total / max(len(records), 1), 2),
            "revenue_by_day": dict(sorted(daily.items())),
            "revenue_by_source": {k: round(v, 2) for k, v in source_breakdown.items()},
        }

    async def get_engagement_metrics(
        self,
        game: str = "minecraft",
        days: int = 7,
    ) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent_sessions = [s for s in self.sessions.values() if s.start_time >= cutoff]
        game_sessions = [s for s in recent_sessions if s.game == game]

        durations = [s.duration_minutes for s in game_sessions if s.duration_minutes]
        unique_players = set(s.player_id for s in game_sessions)

        return {
            "game": game,
            "period_days": days,
            "total_sessions": len(game_sessions),
            "unique_players": len(unique_players),
            "avg_session_minutes": round(statistics.mean(durations), 1) if durations else 0,
            "median_session_minutes": round(statistics.median(durations), 1) if durations else 0,
            "total_playtime_hours": round(sum(durations or []) / 60, 1),
            "avg_player_score": round(statistics.mean([s.score for s in game_sessions]), 1) if game_sessions else 0,
            "peak_concurrent": self._peak_concurrent,
        }

    async def get_player_retention(
        self,
        cohort_date: str,
        game: str = "minecraft",
    ) -> Dict[str, Any]:
        cohort_start = datetime.fromisoformat(cohort_date)
        day1 = cohort_start + timedelta(days=1)
        day7 = cohort_start + timedelta(days=7)
        day30 = cohort_start + timedelta(days=30)

        new_players = set(
            s.player_id for s in self.sessions.values()
            if s.game == game and s.start_time[:10] == cohort_date[:10]
        )

        retained_day1 = set()
        retained_day7 = set()
        retained_day30 = set()

        for s in self.sessions.values():
            if s.player_id in new_players:
                if day1 <= datetime.fromisoformat(s.start_time) < day1 + timedelta(days=1):
                    retained_day1.add(s.player_id)
                if day7 <= datetime.fromisoformat(s.start_time) < day7 + timedelta(days=1):
                    retained_day7.add(s.player_id)
                if day30 <= datetime.fromisoformat(s.start_time) < day30 + timedelta(days=1):
                    retained_day30.add(s.player_id)

        total = len(new_players)
        return {
            "cohort_date": cohort_date,
            "game": game,
            "new_players": total,
            "retention_day_1": round(len(retained_day1) / max(total, 1) * 100, 1),
            "retention_day_7": round(len(retained_day7) / max(total, 1) * 100, 1),
            "retention_day_30": round(len(retained_day30) / max(total, 1) * 100, 1),
            "retained_day_1_count": len(retained_day1),
            "retained_day_7_count": len(retained_day7),
            "retained_day_30_count": len(retained_day30),
        }

    async def get_heatmap_data(
        self,
        game: str = "minecraft",
        days: int = 7,
    ) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        sessions = [
            s for s in self.sessions.values()
            if s.game == game and s.start_time >= cutoff
        ]

        hourly_activity = defaultdict(int)
        for s in sessions:
            hour = datetime.fromisoformat(s.start_time).hour
            hourly_activity[hour] += 1

        daily_activity = defaultdict(int)
        for s in sessions:
            day = s.start_time[:10]
            daily_activity[day] += 1

        return {
            "game": game,
            "days": days,
            "hourly_activity": dict(sorted(hourly_activity.items())),
            "daily_activity": dict(sorted(daily_activity.items())),
            "peak_hour": max(hourly_activity, key=hourly_activity.get) if hourly_activity else 0,
            "peak_day": max(daily_activity, key=daily_activity.get) if daily_activity else "",
        }

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_sessions": len(self.sessions),
            "active_players": len(self._active_players),
            "peak_concurrent": self._peak_concurrent,
            "total_revenue": round(self._total_revenue, 2),
            "revenue_records": len(self.revenue_records),
            "games_tracked": len(set(s.game for s in self.sessions.values())),
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "active_players": len(self._active_players),
        }

    def _record_metric(self, metric: MetricType, game: str, value: float) -> None:
        snapshot = MetricSnapshot(
            snapshot_id=f"ms-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat(),
            metric=metric,
            game=game,
            value=value,
            label=metric.value.replace("_", " ").title(),
            tags={"game": game},
            source="game_analytics",
        )
        self.metric_history[metric.value].append(snapshot)
