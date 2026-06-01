"""Tournament API integration module."""
import asyncio, json, logging, time, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
logger = logging.getLogger(__name__)
class TournamentFormat(Enum): SINGLE_ELIM = "single_elimination"; DOUBLE_ELIM = "double_elimination"; SWISS = "swiss"; ROUND_ROBIN = "round_robin"
class TournamentStatus(Enum): REGISTRATION = "registration"; IN_PROGRESS = "in_progress"; COMPLETED = "completed"; CANCELLED = "cancelled"
class MatchStatus(Enum): SCHEDULED = "scheduled"; LIVE = "live"; COMPLETED = "completed"; FORFEIT = "forfeit"
@dataclass
class Tournament:
    tournament_id: str; name: str; game: str; format: TournamentFormat; team_size: int; max_teams: int
    registered_teams: int; status: TournamentStatus; start_date: str; end_date: Optional[str]
    prize_pool: str; region: str; current_round: int; total_rounds: int; description: str; rules: str
    created_by: str; created_at: str; check_in_required: bool; check_in_hours_before: int
    def to_dict(self) -> Dict[str, Any]: return {
        "tournament_id": self.tournament_id, "name": self.name, "game": self.game, "format": self.format.value,
        "team_size": self.team_size, "max_teams": self.max_teams, "registered_teams": self.registered_teams,
        "status": self.status.value, "start_date": self.start_date, "end_date": self.end_date,
        "prize_pool": self.prize_pool, "region": self.region, "current_round": self.current_round,
        "total_rounds": self.total_rounds, "description": self.description, "created_by": self.created_by,
        "check_in_required": self.check_in_required,
    }
@dataclass
class Match:
    match_id: str; tournament_id: str; round_number: int; team_a: str; team_b: str; score_a: int; score_b: int
    status: MatchStatus; scheduled_time: str; completed_time: Optional[str]; winner: Optional[str]
    duration_minutes: Optional[int]; stream_url: Optional[str]; referee: Optional[str]; notes: str
    def to_dict(self) -> Dict[str, Any]: return {
        "match_id": self.match_id, "tournament_id": self.tournament_id, "round_number": self.round_number,
        "team_a": self.team_a, "team_b": self.team_b, "score_a": self.score_a, "score_b": self.score_b,
        "status": self.status.value, "scheduled_time": self.scheduled_time, "completed_time": self.completed_time,
        "winner": self.winner, "duration_minutes": self.duration_minutes, "stream_url": self.stream_url,
        "referee": self.referee, "notes": self.notes,
    }
class TournamentManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config; self.tournaments: Dict[str, Tournament] = {}; self.matches: Dict[str, Match] = {}
        self._running = False; self._total_matches = 0
    async def initialize(self) -> None: self._running = True; logger.info("Tournament Manager initialized")
    async def close(self) -> None: self._running = False; logger.info("Tournament Manager shut down")
    async def create_tournament(self, name: str, game: str = "minecraft", format: str = "single_elimination", team_size: int = 4, max_teams: int = 16, prize_pool: str = "$0", region: str = "NA", description: str = "", check_in_required: bool = True, check_in_hours_before: int = 1) -> Tournament:
        total_rounds = int(math.ceil(math.log2(max_teams))) if format != "swiss" else 7
        t = Tournament(tournament_id=f"trn-{uuid.uuid4().hex[:8]}", name=name, game=game, format=TournamentFormat(format), team_size=team_size, max_teams=max_teams, registered_teams=0, status=TournamentStatus.REGISTRATION, start_date=(datetime.utcnow() + timedelta(days=7)).isoformat(), end_date=None, prize_pool=prize_pool, region=region, current_round=0, total_rounds=total_rounds, description=description, rules="Standard tournament rules apply.", created_by="admin", created_at=datetime.utcnow().isoformat(), check_in_required=check_in_required, check_in_hours_before=check_in_hours_before)
        self.tournaments[t.tournament_id] = t; return t
    async def register_team(self, tournament_id: str, team_name: str) -> bool:
        t = self.tournaments.get(tournament_id)
        if not t or t.status != TournamentStatus.REGISTRATION: return False
        if t.registered_teams >= t.max_teams: return False
        t.registered_teams += 1; return True
    async def start_tournament(self, tournament_id: str) -> bool:
        t = self.tournaments.get(tournament_id)
        if not t or t.status != TournamentStatus.REGISTRATION: return False
        t.status = TournamentStatus.IN_PROGRESS; t.current_round = 1
        for i in range(max(1, t.registered_teams // 4)):
            match = Match(match_id=f"mch-{uuid.uuid4().hex[:8]}", tournament_id=tournament_id, round_number=1, team_a=f"Team {2*i+1}", team_b=f"Team {2*i+2}", score_a=0, score_b=0, status=MatchStatus.SCHEDULED, scheduled_time=t.start_date, completed_time=None, winner=None, duration_minutes=None, stream_url=None, referee=None, notes="")
            self.matches[match.match_id] = match; self._total_matches += 1
        return True
    async def report_match_result(self, match_id: str, score_a: int, score_b: int) -> bool:
        m = self.matches.get(match_id)
        if not m: return False
        m.score_a = score_a; m.score_b = score_b; m.status = MatchStatus.COMPLETED
        m.completed_time = datetime.utcnow().isoformat()
        m.winner = m.team_a if score_a > score_b else m.team_b
        m.duration_minutes = 30; return True
    async def get_bracket(self, tournament_id: str) -> Dict[str, Any]:
        t = self.tournaments.get(tournament_id)
        if not t: return {}
        bracket_matches = [m for m in self.matches.values() if m.tournament_id == tournament_id]
        rounds = defaultdict(list)
        for m in bracket_matches: rounds[m.round_number].append(m.to_dict())
        return {"tournament": t.to_dict(), "rounds": {r: sorted(matches, key=lambda x: x["scheduled_time"]) for r, matches in rounds.items()}}
    async def get_stats(self) -> Dict[str, Any]:
        return {"total_tournaments": len(self.tournaments), "active": sum(1 for t in self.tournaments.values() if t.status == TournamentStatus.IN_PROGRESS), "completed": sum(1 for t in self.tournaments.values() if t.status == TournamentStatus.COMPLETED), "total_matches": self._total_matches}
    async def health_check(self) -> Dict[str, Any]: return {"status": "healthy" if self._running else "unhealthy", "tournaments": len(self.tournaments)}
