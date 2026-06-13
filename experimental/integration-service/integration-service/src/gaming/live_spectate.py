"""Live Spectate integration module."""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
logger = logging.getLogger(__name__)
class SpectateStatus(Enum): IDLE = "idle"; LIVE = "live"; RECORDING = "recording"; OFFLINE = "offline"
class SceneType(Enum): OVERVIEW = "overview"; PLAYER_FOLLOW = "player_follow"; ARENA = "arena"; STAGE = "stage"; CUSTOM = "custom"
@dataclass
class SpectateSession:
    session_id: str; server_id: str; server_name: str; game: str; status: SpectateStatus
    scene: str; spectator_count: int; max_spectators: int; resolution: str; fps: int
    obs_connected: bool; started_at: str; duration: str; viewer_peak: int; current_scene: str
    def to_dict(self) -> Dict[str, Any]: return {
        "session_id": self.session_id, "server_id": self.server_id, "server_name": self.server_name,
        "game": self.game, "status": self.status.value, "scene": self.scene,
        "spectator_count": self.spectator_count, "max_spectators": self.max_spectators,
        "resolution": self.resolution, "fps": self.fps, "obs_connected": self.obs_connected,
        "started_at": self.started_at, "duration": self.duration, "viewer_peak": self.viewer_peak,
        "current_scene": self.current_scene,
    }
@dataclass
class Scene: scene_id: str; name: str; type: SceneType; sources: List[str]; transitions: List[str]; enabled: bool
    def to_dict(self) -> Dict[str, Any]: return {"scene_id": self.scene_id, "name": self.name, "type": self.type.value, "sources": self.sources, "transitions": self.transitions, "enabled": self.enabled}
class LiveSpectateManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config; self.sessions: Dict[str, SpectateSession] = {}; self.scenes: Dict[str, Scene] = {}
        self._running = False; self._total_viewers = 0; self._peak_viewers = 0
    async def initialize(self) -> None: self._running = True; logger.info("Live Spectate initialized")
    async def close(self) -> None: self._running = False; logger.info("Live Spectate shut down")
    async def create_session(self, server_id: str, server_name: str, game: str = "minecraft", max_spectators: int = 50, resolution: str = "1920x1080", fps: int = 60) -> SpectateSession:
        session = SpectateSession(session_id=f"spec-{uuid.uuid4().hex[:8]}", server_id=server_id, server_name=server_name, game=game, status=SpectateStatus.LIVE, scene=SceneType.OVERVIEW.value, spectator_count=0, max_spectators=max_spectators, resolution=resolution, fps=fps, obs_connected=True, started_at=datetime.utcnow().isoformat(), duration="0h 0m", viewer_peak=0, current_scene="Overview")
        self.sessions[session.session_id] = session; return session
    async def update_spectator_count(self, session_id: str, count: int) -> bool:
        s = self.sessions.get(session_id); 
        if not s: return False
        s.spectator_count = count; s.viewer_peak = max(s.viewer_peak, count); self._peak_viewers = max(self._peak_viewers, count); return True
    async def switch_scene(self, session_id: str, scene_name: str) -> bool:
        s = self.sessions.get(session_id); 
        if not s: return False
        s.current_scene = scene_name; return True
    async def list_sessions(self) -> List[Dict[str, Any]]: return [s.to_dict() for s in self.sessions.values()]
    async def get_stats(self) -> Dict[str, Any]: return {"total_sessions": len(self.sessions), "live": sum(1 for s in self.sessions.values() if s.status == SpectateStatus.LIVE), "total_viewers": sum(s.spectator_count for s in self.sessions.values()), "peak_viewers": self._peak_viewers}
    async def health_check(self) -> Dict[str, Any]: return {"status": "healthy" if self._running else "unhealthy", "live_sessions": sum(1 for s in self.sessions.values() if s.status == SpectateStatus.LIVE)}
