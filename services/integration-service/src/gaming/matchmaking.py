"""Matchmaking integration module."""
import asyncio
import json
import logging
import math
import random
import statistics
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    WAITING = "waiting"
    MATCHING = "matching"
    CONFIRMING = "confirming"
    IN_GAME = "in_game"
    CANCELLED = "cancelled"


class MatchResult(Enum):
    TEAM_A_WIN = "team_a_win"
    TEAM_B_WIN = "team_b_win"
    DRAW = "draw"
    CANCELLED = "cancelled"


class Region(Enum):
    NA_EAST = "NA-East"
    NA_WEST = "NA-West"
    EU_WEST = "EU-West"
    EU_EAST = "EU-East"
    ASIA_EAST = "Asia-East"
    ASIA_SE = "Asia-SE"
    OCEANIA = "Oceania"
    SOUTH_AMERICA = "South-America"


@dataclass
class Player:
    player_id: str
    name: str
    elo: int
    mmr: int
    region: Region
    wins: int
    losses: int
    games_played: int
    win_rate: float
    rank: str
    tier: str
    party_id: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "elo": self.elo,
            "mmr": self.mmr,
            "region": self.region.value,
            "wins": self.wins,
            "losses": self.losses,
            "games_played": self.games_played,
            "win_rate": round(self.win_rate, 1),
            "rank": self.rank,
            "tier": self.tier,
            "party_id": self.party_id,
        }


@dataclass
class QueueEntry:
    queue_id: str
    player: Player
    joined_at: str
    desired_mode: str
    party_size: int
    region: Region
    elo_range: Tuple[int, int]
    status: QueueStatus

    def waiting_time_seconds(self) -> float:
        joined = datetime.fromisoformat(self.joined_at)
        return (datetime.utcnow() - joined).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "player": self.player.to_dict(),
            "joined_at": self.joined_at,
            "desired_mode": self.desired_mode,
            "party_size": self.party_size,
            "region": self.region.value,
            "elo_lower": self.elo_range[0],
            "elo_upper": self.elo_range[1],
            "status": self.status.value,
            "waiting_seconds": round(self.waiting_time_seconds(), 1),
        }


@dataclass
class Match:
    match_id: str
    mode: str
    region: Region
    team_a: List[Player]
    team_b: List[Player]
    team_a_avg_elo: int
    team_b_avg_elo: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[MatchResult]
    elo_delta_a: int
    elo_delta_b: int
    spectator_count: int
    duration_seconds: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "mode": self.mode,
            "region": self.region.value,
            "team_a": [p.to_dict() for p in self.team_a],
            "team_b": [p.to_dict() for p in self.team_b],
            "team_a_avg_elo": self.team_a_avg_elo,
            "team_b_avg_elo": self.team_b_avg_elo,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result.value if self.result else None,
            "elo_delta_a": self.elo_delta_a,
            "elo_delta_b": self.elo_delta_b,
            "spectator_count": self.spectator_count,
            "duration_seconds": self.duration_seconds,
            "balance_score": self._calculate_balance(),
        }

    def _calculate_balance(self) -> float:
        diff = abs(self.team_a_avg_elo - self.team_b_avg_elo)
        if diff < 50:
            return 1.0
        elif diff < 100:
            return 0.8
        elif diff < 200:
            return 0.5
        else:
            return 0.2


class MatchmakingService:
    """ELO/MMR matchmaking with skill-based balancing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.players: Dict[str, Player] = {}
        self.queues: Dict[str, QueueEntry] = {}
        self.matches: Dict[str, Match] = {}
        self.parties: Dict[str, List[str]] = {}
        self._running = False
        self._total_matches = 0
        self._total_players_matched = 0
        self._cancelled_queues = 0
        self._avg_wait_time: List[float] = []

    async def initialize(self) -> None:
        self._running = True
        logger.info("Matchmaking Service initialized")

    async def close(self) -> None:
        self._running = False
        for qid in list(self.queues.keys()):
            self.queues[qid].status = QueueStatus.CANCELLED
        logger.info("Matchmaking Service shut down")

    async def register_player(
        self,
        name: str,
        region: str = "NA-East",
        initial_elo: int = 1000,
    ) -> Player:
        player = Player(
            player_id=f"p-{uuid.uuid4().hex[:8]}",
            name=name,
            elo=initial_elo,
            mmr=initial_elo,
            region=Region(region),
            wins=0,
            losses=0,
            games_played=0,
            win_rate=0.0,
            rank=self._calculate_rank(initial_elo),
            tier=self._calculate_tier(initial_elo),
            party_id=None,
        )
        self.players[player.player_id] = player
        return player

    async def join_queue(
        self,
        player_id: str,
        mode: str = "solo_arena",
        region: Optional[str] = None,
    ) -> QueueEntry:
        player = self.players.get(player_id)
        if not player:
            raise ValueError(f"Player '{player_id}' not found")

        if any(q.player.player_id == player_id for q in self.queues.values() if q.status == QueueStatus.WAITING):
            raise ValueError("Player already in queue")

        region_enum = Region(region) if region else player.region
        elo_range = (
            max(0, player.elo - 200),
            player.elo + 200,
        )

        entry = QueueEntry(
            queue_id=f"q-{uuid.uuid4().hex[:8]}",
            player=player,
            joined_at=datetime.utcnow().isoformat(),
            desired_mode=mode,
            party_size=1,
            region=region_enum,
            elo_range=elo_range,
            status=QueueStatus.WAITING,
        )
        self.queues[entry.queue_id] = entry
        return entry

    async def leave_queue(self, player_id: str) -> bool:
        for qid, entry in list(self.queues.items()):
            if entry.player.player_id == player_id and entry.status == QueueStatus.WAITING:
                entry.status = QueueStatus.CANCELLED
                del self.queues[qid]
                self._cancelled_queues += 1
                return True
        return False

    async def find_match(self, mode: str = "solo_arena") -> Optional[Match]:
        candidates = [
            q for q in self.queues.values()
            if q.desired_mode == mode and q.status == QueueStatus.WAITING
        ]

        if len(candidates) < 2:
            return None

        candidates.sort(key=lambda q: q.waiting_time_seconds(), reverse=True)
        player_a = candidates[0]
        player_b = None

        for candidate in candidates[1:]:
            if abs(candidate.player.elo - player_a.player.elo) <= 200:
                player_b = candidate
                break

        if not player_b:
            return None

        player_a.status = QueueStatus.MATCHING
        player_b.status = QueueStatus.MATCHING

        avg_elo = (player_a.player.elo + player_b.player.elo) // 2
        match = Match(
            match_id=f"mch-{uuid.uuid4().hex[:8]}",
            mode=mode,
            region=player_a.region,
            team_a=[player_a.player],
            team_b=[player_b.player],
            team_a_avg_elo=player_a.player.elo,
            team_b_avg_elo=player_b.player.elo,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            completed_at=None,
            result=None,
            elo_delta_a=self._calculate_elo_delta(player_a.player.elo, player_b.player.elo),
            elo_delta_b=self._calculate_elo_delta(player_b.player.elo, player_a.player.elo),
            spectator_count=0,
            duration_seconds=None,
        )
        self.matches[match.match_id] = match
        self._total_matches += 1
        self._total_players_matched += 2
        self._avg_wait_time.append((player_a.waiting_time_seconds() + player_b.waiting_time_seconds()) / 2)

        del self.queues[player_a.queue_id]
        del self.queues[player_b.queue_id]

        return match

    async def complete_match(
        self,
        match_id: str,
        result: str,
        duration_seconds: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        match = self.matches.get(match_id)
        if not match:
            return None

        match.result = MatchResult(result)
        match.completed_at = datetime.utcnow().isoformat()
        match.duration_seconds = duration_seconds

        for player in match.team_a + match.team_b:
            player.games_played += 1

        if result == "team_a_win":
            for player in match.team_a:
                player.wins += 1
                player.elo += match.elo_delta_a
            for player in match.team_b:
                player.losses += 1
                player.elo -= match.elo_delta_b
        elif result == "team_b_win":
            for player in match.team_b:
                player.wins += 1
                player.elo += match.elo_delta_b
            for player in match.team_a:
                player.losses += 1
                player.elo -= match.elo_delta_a

        for player in match.team_a + match.team_b:
            player.mmr = player.elo
            player.win_rate = (player.wins / max(player.games_played, 1)) * 100
            player.rank = self._calculate_rank(player.elo)
            player.tier = self._calculate_tier(player.elo)

        return match.to_dict()

    async def get_queue_status(self) -> List[Dict[str, Any]]:
        return [q.to_dict() for q in self.queues.values()]

    async def get_leaderboard(
        self,
        region: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        players = list(self.players.values())
        if region:
            players = [p for p in players if p.region.value == region]
        players.sort(key=lambda p: p.elo, reverse=True)
        return [p.to_dict() for p in players[:limit]]

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_players": len(self.players),
            "players_in_queue": sum(1 for q in self.queues.values() if q.status == QueueStatus.WAITING),
            "total_matches": self._total_matches,
            "total_players_matched": self._total_players_matched,
            "cancelled_queues": self._cancelled_queues,
            "avg_wait_time": round(statistics.mean(self._avg_wait_time[-100:]), 1) if self._avg_wait_time else 0,
            "active_matches": len(self.matches),
            "avg_elo": round(statistics.mean([p.elo for p in self.players.values()]), 1) if self.players else 0,
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "players": len(self.players),
            "queued": sum(1 for q in self.queues.values() if q.status == QueueStatus.WAITING),
            "matches": len(self.matches),
        }

    def _calculate_elo_delta(self, winner_elo: int, loser_elo: int) -> int:
        expected = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
        k_factor = 32
        return round(k_factor * (1 - expected))

    def _calculate_rank(self, elo: int) -> str:
        if elo >= 2800: return "Grandmaster"
        elif elo >= 2500: return "Master"
        elif elo >= 2200: return "Diamond"
        elif elo >= 1900: return "Platinum"
        elif elo >= 1600: return "Gold"
        elif elo >= 1300: return "Silver"
        elif elo >= 1000: return "Bronze"
        else: return "Iron"

    def _calculate_tier(self, elo: int) -> str:
        if elo >= 2500: return "S"
        elif elo >= 2000: return "A"
        elif elo >= 1500: return "B"
        elif elo >= 1000: return "C"
        else: return "D"
