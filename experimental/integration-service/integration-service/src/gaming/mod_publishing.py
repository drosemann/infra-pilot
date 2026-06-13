"""Mod Publishing integration module."""
import asyncio, json, logging, time, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
logger = logging.getLogger(__name__)
class ModStatus(Enum): DRAFT = "draft"; PUBLISHED = "published"; ARCHIVED = "archived"; REJECTED = "rejected"
class ModPlatform(Enum): CURSEFORGE = "curseforge"; MODRINTH = "modrinth"; HANGBUILDER = "hangbuilder"
@dataclass
class ModVersion:
    version_id: str; mod_name: str; mod_id: str; version: str; game: str; game_version: str
    downloads: int; downloads_total: int; size_bytes: int; created_at: str; updated_at: str
    status: ModStatus; dependencies: List[str]; conflicts: List[str]; rating: float; description: str
    changelog: str; license: str; author: str; supported_platforms: List[str]; tags: List[str]
    def to_dict(self) -> Dict[str, Any]: return {
        "version_id": self.version_id, "mod_name": self.mod_name, "mod_id": self.mod_id,
        "version": self.version, "game": self.game, "game_version": self.game_version,
        "downloads": self.downloads, "downloads_total": self.downloads_total,
        "size_bytes": self.size_bytes, "created_at": self.created_at, "updated_at": self.updated_at,
        "status": self.status.value, "dependencies": self.dependencies, "conflicts": self.conflicts,
        "rating": self.rating, "description": self.description, "changelog": self.changelog,
        "license": self.license, "author": self.author, "supported_platforms": self.supported_platforms,
        "tags": self.tags, "size_display": self._fmt_size(),
    }
    def _fmt_size(self) -> str:
        if self.size_bytes < 1024**2: return f"{self.size_bytes/1024:.1f} KB"
        else: return f"{self.size_bytes/1024**2:.1f} MB"
class ModPublishingManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config; self.versions: Dict[str, ModVersion] = {}; self._running = False; self._total_downloads = 0
    async def initialize(self) -> None: self._running = True; logger.info("Mod Publishing initialized")
    async def close(self) -> None: self._running = False; logger.info("Mod Publishing shut down")
    async def publish_version(self, mod_name: str, mod_id: str, version: str, game: str = "minecraft", game_version: str = "1.21", description: str = "", changelog: str = "", dependencies: Optional[List[str]] = None, conflicts: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> ModVersion:
        mv = ModVersion(version_id=f"mod-{uuid.uuid4().hex[:8]}", mod_name=mod_name, mod_id=mod_id, version=version, game=game, game_version=game_version, downloads=0, downloads_total=0, size_bytes=1024*1024, created_at=datetime.utcnow().isoformat(), updated_at=datetime.utcnow().isoformat(), status=ModStatus.DRAFT, dependencies=dependencies or [], conflicts=conflicts or [], rating=0.0, description=description, changelog=changelog, license="MIT", author="admin", supported_platforms=["curseforge", "modrinth"], tags=tags or [])
        self.versions[mv.version_id] = mv; return mv
    async def publish(self, version_id: str) -> bool:
        v = self.versions.get(version_id); 
        if not v: return False
        v.status = ModStatus.PUBLISHED; v.updated_at = datetime.utcnow().isoformat(); return True
    async def record_download(self, version_id: str) -> bool:
        v = self.versions.get(version_id); 
        if not v: return False
        v.downloads += 1; v.downloads_total += 1; self._total_downloads += 1; return True
    async def search_mods(self, query: str, game: Optional[str] = None) -> List[Dict[str, Any]]:
        results = [v for v in self.versions.values() if query.lower() in v.mod_name.lower() or query.lower() in v.description.lower()]
        if game: results = [r for r in results if r.game == game]
        return [r.to_dict() for r in results]
    async def get_dependency_graph(self, version_id: str) -> Dict[str, Any]:
        v = self.versions.get(version_id); 
        if not v: return {"mod": None, "dependencies": [], "conflicts": []}
        deps = [self.versions.get(d).to_dict() if self.versions.get(d) else {"id": d, "not_found": True} for d in v.dependencies]
        confs = [self.versions.get(c).to_dict() if self.versions.get(c) else {"id": c, "not_found": True} for c in v.conflicts]
        return {"mod": v.to_dict(), "dependencies": deps, "conflicts": confs}
    async def get_stats(self) -> Dict[str, Any]:
        return {"total_mods": len(set(v.mod_id for v in self.versions.values())), "total_versions": len(self.versions), "total_downloads": self._total_downloads, "published": sum(1 for v in self.versions.values() if v.status == ModStatus.PUBLISHED), "avg_rating": round(sum(v.rating for v in self.versions.values() if v.rating > 0) / max(sum(1 for v in self.versions.values() if v.rating > 0), 1), 1)}
    async def health_check(self) -> Dict[str, Any]: return {"status": "healthy" if self._running else "unhealthy", "versions": len(self.versions)}
