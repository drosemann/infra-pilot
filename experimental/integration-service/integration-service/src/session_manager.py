import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DeviceFingerprint:
    user_agent: str
    platform: str
    screen_resolution: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    canvas_hash: Optional[str]
    webgl_vendor: Optional[str]
    webgl_renderer: Optional[str]
    installed_fonts: List[str]
    ip_address: str
    accept_language: Optional[str]
    hardware_concurrency: Optional[int]
    device_memory: Optional[float]
    touch_support: bool
    color_depth: Optional[int]
    audio_fingerprint: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_agent": self.user_agent,
            "platform": self.platform,
            "screen_resolution": self.screen_resolution,
            "timezone": self.timezone,
            "language": self.language,
            "canvas_hash": self.canvas_hash,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
            "installed_fonts": self.installed_fonts[:20],
            "ip_address": self.ip_address,
            "accept_language": self.accept_language,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "touch_support": self.touch_support,
            "color_depth": self.color_depth,
            "audio_fingerprint": self.audio_fingerprint,
        }

    def compute_hash(self) -> str:
        data = f"{self.user_agent}|{self.platform}|{self.screen_resolution}|{self.canvas_hash}|{self.webgl_vendor}|{self.audio_fingerprint}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class Session:
    session_id: str
    user_id: str
    device_fingerprint: DeviceFingerprint
    location: Optional[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    is_current: bool
    auth_method: str
    ip_address: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_fingerprint": self.device_fingerprint.to_dict(),
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active,
            "is_current": self.is_current,
            "auth_method": self.auth_method,
            "ip_address": self.ip_address,
            "metadata": self.metadata,
        }


class GeoIPDatabase:
    def __init__(self):
        self._lookups: Dict[str, Dict[str, Any]] = {}

    def add_entry(self, ip_address: str, data: Dict[str, Any]) -> None:
        self._lookups[ip_address] = data

    def lookup(self, ip_address: str) -> Dict[str, Any]:
        if ip_address in self._lookups:
            return self._lookups[ip_address]
        if ip_address.startswith("10.") or ip_address.startswith("192.168.") or ip_address.startswith("172."):
            return {
                "country": "PRIVATE",
                "city": "Private Network",
                "lat": 0.0,
                "lon": 0.0,
                "isp": "Private Network",
            }
        return {
            "country": "UNKNOWN",
            "city": "Unknown",
            "lat": 0.0,
            "lon": 0.0,
            "isp": "Unknown",
        }


class SessionManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session_ttl = config.get("session_ttl", 3600)
        self.max_concurrent_sessions = config.get("max_concurrent_sessions", 10)
        self.suspicious_detection_enabled = config.get("suspicious_detection_enabled", True)
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, List[str]] = {}
        self._activity_log: List[Dict[str, Any]] = []
        self._geo_db = GeoIPDatabase()
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("SessionManager initialized")

    async def close(self) -> None:
        self._sessions.clear()
        self._user_sessions.clear()
        self._activity_log.clear()
        logger.info("SessionManager closed")

    def create_session(self, user_id: str, fingerprint_data: Dict[str, Any],
                       auth_method: str = "password", location: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Session:
        self._cleanup_expired_sessions()

        existing = self._user_sessions.get(user_id, [])
        if len(existing) >= self.max_concurrent_sessions:
            oldest = sorted(existing, key=lambda sid: self._sessions[sid].last_activity)[0]
            self.revoke_session(oldest)

        fingerprint = DeviceFingerprint(
            user_agent=fingerprint_data.get("user_agent", ""),
            platform=fingerprint_data.get("platform", ""),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            timezone=fingerprint_data.get("timezone"),
            language=fingerprint_data.get("language"),
            canvas_hash=fingerprint_data.get("canvas_hash"),
            webgl_vendor=fingerprint_data.get("webgl_vendor"),
            webgl_renderer=fingerprint_data.get("webgl_renderer"),
            installed_fonts=fingerprint_data.get("installed_fonts", []),
            ip_address=fingerprint_data.get("ip_address", ""),
            accept_language=fingerprint_data.get("accept_language"),
            hardware_concurrency=fingerprint_data.get("hardware_concurrency"),
            device_memory=fingerprint_data.get("device_memory"),
            touch_support=fingerprint_data.get("touch_support", False),
            color_depth=fingerprint_data.get("color_depth"),
            audio_fingerprint=fingerprint_data.get("audio_fingerprint"),
        )

        if location is None:
            location = self._geo_db.lookup(fingerprint.ip_address)

        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        session = Session(
            session_id=session_id,
            user_id=user_id,
            device_fingerprint=fingerprint,
            location=location,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(seconds=self.session_ttl),
            is_active=True,
            is_current=True,
            auth_method=auth_method,
            ip_address=fingerprint.ip_address,
            metadata=metadata or {},
        )

        self._sessions[session_id] = session
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)

        self._log_activity(user_id, "session_created", {"session_id": session_id, "fingerprint_hash": fingerprint.compute_hash()})
        logger.info(f"Session {session_id} created for user {user_id}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if not session or not session.is_active or datetime.utcnow() > session.expires_at:
            return None
        session.last_activity = datetime.utcnow()
        return session

    def revoke_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.is_active = False
        user_sessions = self._user_sessions.get(session.user_id, [])
        if session_id in user_sessions:
            user_sessions.remove(session_id)
        self._log_activity(session.user_id, "session_revoked", {"session_id": session_id})
        logger.info(f"Session {session_id} revoked for user {session.user_id}")
        return True

    def revoke_all_user_sessions(self, user_id: str, exclude_current: Optional[str] = None) -> int:
        count = 0
        session_ids = list(self._user_sessions.get(user_id, []))
        for sid in session_ids:
            if exclude_current and sid == exclude_current:
                continue
            if self.revoke_session(sid):
                count += 1
        logger.info(f"Revoked {count} sessions for user {user_id}")
        return count

    def get_user_sessions(self, user_id: str, current_session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self._cleanup_expired_sessions()
        sessions = []
        for sid in self._user_sessions.get(user_id, []):
            session = self._sessions.get(sid)
            if session and session.is_active:
                session_dict = session.to_dict()
                session_dict["is_current"] = (sid == current_session_id)
                sessions.append(session_dict)
        return sorted(sessions, key=lambda s: s["last_activity"], reverse=True)

    def refresh_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return False
        session.expires_at = datetime.utcnow() + timedelta(seconds=self.session_ttl)
        session.last_activity = datetime.utcnow()
        return True

    def detect_suspicious_activity(self, user_id: str, fingerprint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.suspicious_detection_enabled:
            return []

        alerts = []
        sessions = self.get_user_sessions(user_id)
        new_fp_hash = DeviceFingerprint(
            user_agent=fingerprint_data.get("user_agent", ""),
            platform=fingerprint_data.get("platform", ""),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            timezone=fingerprint_data.get("timezone"),
            language=fingerprint_data.get("language"),
            canvas_hash=fingerprint_data.get("canvas_hash"),
            webgl_vendor=None,
            webgl_renderer=None,
            installed_fonts=fingerprint_data.get("installed_fonts", []),
            ip_address=fingerprint_data.get("ip_address", ""),
            accept_language=None,
            hardware_concurrency=None,
            device_memory=None,
            touch_support=False,
            color_depth=None,
            audio_fingerprint=None,
        ).compute_hash()

        known_hashes = []
        known_ips = set()
        for s in sessions:
            known_hashes.append(s["device_fingerprint"].get("fingerprint_hash", s["device_fingerprint"].get("canvas_hash", "")))
            known_ips.add(s.get("ip_address", ""))

        if sessions and new_fp_hash not in known_hashes:
            alerts.append({
                "type": "new_device",
                "severity": "medium",
                "message": "Login from unrecognized device",
                "fingerprint_hash": new_fp_hash,
            })

        new_ip = fingerprint_data.get("ip_address", "")
        if known_ips and new_ip not in known_ips:
            alerts.append({
                "type": "new_ip",
                "severity": "low",
                "message": f"Login from new IP address: {new_ip}",
                "ip": new_ip,
            })

        return alerts

    def get_activity_log(self, user_id: Optional[str] = None,
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        activities = self._activity_log
        if user_id:
            activities = [a for a in activities if a["user_id"] == user_id]
        return activities[offset:offset + limit]

    def _log_activity(self, user_id: str, action: str, details: Dict[str, Any]) -> None:
        entry = {
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._activity_log.append(entry)
        if len(self._activity_log) > 10000:
            self._activity_log = self._activity_log[-5000:]

    def _cleanup_expired_sessions(self) -> None:
        now = datetime.utcnow()
        expired = [sid for sid, s in self._sessions.items() if now > s.expires_at]
        for sid in expired:
            s = self._sessions[sid]
            s.is_active = False
            if s.user_id in self._user_sessions and sid in self._user_sessions[s.user_id]:
                self._user_sessions[s.user_id].remove(sid)
            del self._sessions[sid]

    def get_statistics(self) -> Dict[str, Any]:
        self._cleanup_expired_sessions()
        active = sum(1 for s in self._sessions.values() if s.is_active)
        total_users = len(self._user_sessions)
        avg_sessions_per_user = round(active / total_users, 2) if total_users > 0 else 0
        auth_methods = {}
        for s in self._sessions.values():
            auth_methods[s.auth_method] = auth_methods.get(s.auth_method, 0) + 1
        platforms = {}
        for s in self._sessions.values():
            p = s.device_fingerprint.platform
            platforms[p] = platforms.get(p, 0) + 1
        return {
            "active_sessions": active,
            "total_users_with_sessions": total_users,
            "avg_sessions_per_user": avg_sessions_per_user,
            "auth_methods": auth_methods,
            "platforms": platforms,
            "session_ttl": self.session_ttl,
            "max_concurrent": self.max_concurrent_sessions,
        }

    def add_geo_entry(self, ip_address: str, data: Dict[str, Any]) -> None:
        self._geo_db.add_entry(ip_address, data)
