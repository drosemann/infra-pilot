"""Extended session manager with device fingerprinting, risk scoring, and geo-location."""
import json
import uuid
import hashlib
import hmac
import logging
import secrets
import math
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionAuthMethod(str, Enum):
    PASSWORD = "password"
    WEBAUTHN = "webauthn"
    PASSKEY = "passkey"
    OIDC = "oidc"
    SAML = "saml"
    MFA = "mfa"
    API_TOKEN = "api_token"
    CLIENT_CERT = "client_cert"
    MAGIC_LINK = "magic_link"
    OTP = "otp"
    BREAK_GLASS = "break_glass"
    SSO = "sso"


@dataclass
class EnhancedDeviceFingerprint:
    user_agent: str
    platform: str
    platform_version: Optional[str]
    screen_resolution: Optional[str]
    screen_orientation: Optional[str]
    color_depth: Optional[int]
    pixel_ratio: Optional[float]
    timezone: Optional[str]
    timezone_offset: Optional[int]
    language: Optional[str]
    languages: List[str]
    canvas_hash: Optional[str]
    webgl_vendor: Optional[str]
    webgl_renderer: Optional[str]
    webgl_version: Optional[str]
    installed_fonts: List[str]
    installed_plugins: List[str]
    ip_address: str
    accept_language: Optional[str]
    hardware_concurrency: Optional[int]
    device_memory: Optional[float]
    touch_support: bool
    max_touch_points: Optional[int]
    audio_fingerprint: Optional[str]
    battery_level: Optional[float]
    charging: Optional[bool]
    cpu_architecture: Optional[str]
    device_model: Optional[str]
    device_vendor: Optional[str]
    do_not_track: Optional[bool]
    ad_blocker_detected: Optional[bool]
    cookies_enabled: Optional[bool]
    localStorage_available: Optional[bool]
    sessionStorage_available: Optional[bool]
    indexed_db_available: Optional[bool]

    def compute_hash(self) -> str:
        components = [
            self.user_agent,
            self.platform,
            self.screen_resolution,
            self.canvas_hash,
            self.webgl_vendor,
            self.webgl_renderer,
            self.audio_fingerprint,
            self.installed_fonts[:10],
            self.hardware_concurrency,
            self.device_memory,
        ]
        data = "|".join(str(c) for c in components if c is not None)
        return hashlib.sha256(data.encode()).hexdigest()

    def compute_stable_hash(self) -> str:
        stable_components = [
            self.canvas_hash,
            self.webgl_vendor,
            self.webgl_renderer,
            self.audio_fingerprint,
            self.installed_fonts[:5],
        ]
        data = "|".join(str(c) for c in stable_components if c is not None)
        return hashlib.sha256(data.encode()).hexdigest() if data else self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_agent": self.user_agent,
            "platform": self.platform,
            "platform_version": self.platform_version,
            "screen_resolution": self.screen_resolution,
            "color_depth": self.color_depth,
            "timezone": self.timezone,
            "language": self.language,
            "languages": self.languages[:5],
            "canvas_hash": self.canvas_hash,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
            "installed_fonts": self.installed_fonts[:30],
            "ip_address": self.ip_address,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "touch_support": self.touch_support,
            "audio_fingerprint": self.audio_fingerprint,
            "device_model": self.device_model,
            "device_vendor": self.device_vendor,
            "fingerprint_hash": self.compute_hash(),
            "stable_hash": self.compute_stable_hash(),
        }


@dataclass
class EnhancedSession:
    session_id: str
    user_id: str
    device_fingerprint: EnhancedDeviceFingerprint
    location: Optional[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    is_current: bool
    auth_method: str
    ip_address: str
    risk_level: SessionRiskLevel
    risk_score: float
    failed_attempts: int
    mfa_verified: bool
    mfa_method: Optional[str]
    authn_context: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]
    geofence_violation: bool
    impossible_travel: bool
    login_anomaly_score: float
    device_trust_score: float

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
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 2),
            "failed_attempts": self.failed_attempts,
            "mfa_verified": self.mfa_verified,
            "mfa_method": self.mfa_method,
            "tags": self.tags,
            "geofence_violation": self.geofence_violation,
            "impossible_travel": self.impossible_travel,
            "login_anomaly_score": round(self.login_anomaly_score, 3),
            "device_trust_score": round(self.device_trust_score, 3),
            "metadata": self.metadata,
        }


class GeoIPDatabaseExtended:
    def __init__(self):
        self._lookups: Dict[str, Dict[str, Any]] = {}
        self._rdns_cache: Dict[str, str] = {}

    def add_entry(self, ip_address: str, data: Dict[str, Any]) -> None:
        self._lookups[ip_address] = data

    def bulk_add(self, entries: Dict[str, Dict[str, Any]]) -> int:
        count = 0
        for ip, data in entries.items():
            self._lookups[ip] = data
            count += 1
        return count

    def lookup(self, ip_address: str) -> Dict[str, Any]:
        if ip_address in self._lookups:
            return self._lookups[ip_address]
        if ip_address.startswith("10.") or ip_address.startswith("192.168.") or ip_address == "127.0.0.1" or ip_address == "::1":
            return {
                "country": "PRIVATE",
                "country_code": "XX",
                "city": "Private Network",
                "region": "Private",
                "postal_code": None,
                "lat": 0.0,
                "lon": 0.0,
                "isp": "Private Network",
                "asn": "PRIVATE",
                "timezone": "UTC",
                "is_proxy": False,
                "is_datacenter": False,
                "is_vpn": False,
                "is_tor": False,
                "risk_score": 0.0,
            }
        return {
            "country": "UNKNOWN",
            "country_code": "ZZ",
            "city": "Unknown",
            "region": "Unknown",
            "postal_code": None,
            "lat": 0.0,
            "lon": 0.0,
            "isp": "Unknown",
            "asn": "UNKNOWN",
            "timezone": "UTC",
            "is_proxy": False,
            "is_datacenter": False,
            "is_vpn": False,
            "is_tor": False,
            "risk_score": 0.5,
        }

    def get_distance_km(self, ip1: str, ip2: str) -> float:
        loc1 = self.lookup(ip1)
        loc2 = self.lookup(ip2)
        lat1, lon1 = loc1.get("lat", 0.0), loc1.get("lon", 0.0)
        lat2, lon2 = loc2.get("lat", 0.0), loc2.get("lon", 0.0)
        if not lat1 or not lon1 or not lat2 or not lon2:
            return 0.0
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def is_same_country(self, ip1: str, ip2: str) -> bool:
        loc1 = self.lookup(ip1)
        loc2 = self.lookup(ip2)
        return loc1.get("country_code") == loc2.get("country_code")


class DeviceTrustScorer:
    def __init__(self):
        self._trusted_hashes: Dict[str, float] = {}
        self._known_locations: Dict[str, Set[str]] = {}

    def score_device(self, fingerprint: EnhancedDeviceFingerprint,
                     user_id: str, existing_sessions: List[EnhancedSession]) -> float:
        score = 0.5
        stable_hash = fingerprint.compute_stable_hash()
        if stable_hash in self._trusted_hashes:
            score = self._trusted_hashes[stable_hash]
        existing_hashes = [s.device_fingerprint.compute_stable_hash() for s in existing_sessions]
        if stable_hash in existing_hashes:
            score = min(1.0, score + 0.2)
        if fingerprint.canvas_hash and fingerprint.canvas_hash == fingerprint.webgl_vendor:
            score = max(0.0, score - 0.1)
        if not fingerprint.canvas_hash and not fingerprint.audio_fingerprint:
            score = max(0.0, score - 0.3)
        if fingerprint.hardware_concurrency and fingerprint.hardware_concurrency < 2:
            score = max(0.0, score - 0.15)
        if fingerprint.touch_support and fingerprint.max_touch_points and fingerprint.max_touch_points > 5:
            score = min(1.0, score + 0.05)
        return round(score, 3)

    def record_trusted_device(self, fingerprint_hash: str, score: float) -> None:
        self._trusted_hashes[fingerprint_hash] = score
        if len(self._trusted_hashes) > 10000:
            oldest = min(self._trusted_hashes.items(), key=lambda x: x[1])
            del self._trusted_hashes[oldest[0]]

    def record_location(self, user_id: str, ip_address: str) -> None:
        if user_id not in self._known_locations:
            self._known_locations[user_id] = set()
        self._known_locations[user_id].add(ip_address)

    def is_known_location(self, user_id: str, ip_address: str) -> bool:
        return ip_address in self._known_locations.get(user_id, set())

    def get_familiar_locations(self, user_id: str) -> List[str]:
        return list(self._known_locations.get(user_id, set()))


class AnomalyDetector:
    def __init__(self):
        self._login_velocity: Dict[str, List[datetime]] = {}
        self._ip_changes: Dict[str, List[Tuple[str, datetime]]] = {}
        self._geo_velocity: Dict[str, List[Tuple[str, str, datetime]]] = {}

    def record_login(self, user_id: str, ip_address: str, location: Dict[str, Any]) -> None:
        now = datetime.utcnow()
        if user_id not in self._login_velocity:
            self._login_velocity[user_id] = []
        self._login_velocity[user_id].append(now)
        if len(self._login_velocity[user_id]) > 100:
            self._login_velocity[user_id] = self._login_velocity[user_id][-50:]
        if user_id not in self._ip_changes:
            self._ip_changes[user_id] = []
        self._ip_changes[user_id].append((ip_address, now))
        if len(self._ip_changes[user_id]) > 50:
            self._ip_changes[user_id] = self._ip_changes[user_id][-25:]
        country = location.get("country_code", "ZZ")
        if user_id not in self._geo_velocity:
            self._geo_velocity[user_id] = []
        self._geo_velocity[user_id].append((ip_address, country, now))
        if len(self._geo_velocity[user_id]) > 50:
            self._geo_velocity[user_id] = self._geo_velocity[user_id][-25:]

    def check_login_velocity(self, user_id: str, max_per_hour: int = 10) -> float:
        recent = self._login_velocity.get(user_id, [])
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_count = sum(1 for t in recent if t > cutoff)
        if recent_count == 0:
            return 0.0
        score = min(1.0, recent_count / max_per_hour)
        return round(score, 3)

    def check_impossible_travel(self, user_id: str, ip_address: str,
                                location: Dict[str, Any],
                                geo_db: GeoIPDatabaseExtended) -> Tuple[bool, float]:
        recent = self._geo_velocity.get(user_id, [])
        if len(recent) < 2:
            return False, 0.0
        last_entry = recent[-1]
        last_ip = last_entry[0]
        if last_ip == ip_address:
            return False, 0.0
        last_time = last_entry[2]
        elapsed_hours = (datetime.utcnow() - last_time).total_seconds() / 3600
        if elapsed_hours < 0.01:
            elapsed_hours = 0.01
        distance = geo_db.get_distance_km(last_ip, ip_address)
        speed_kmh = distance / elapsed_hours
        if speed_kmh > 900 and distance > 100:
            return True, min(1.0, speed_kmh / 2000)
        return False, 0.0

    def check_ip_frequency(self, user_id: str, ip_address: str) -> float:
        recent = self._ip_changes.get(user_id, [])
        total_ips = len(set(ip for ip, _ in recent))
        if total_ips <= 1:
            return 0.0
        cutoff = datetime.utcnow() - timedelta(days=7)
        weekly_ips = len(set(ip for ip, t in recent if t > cutoff))
        if weekly_ips > 5:
            return min(1.0, weekly_ips / 15)
        return 0.0


class SessionManagerExtended:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session_ttl = config.get("session_ttl", 3600)
        self.max_concurrent_sessions = config.get("max_concurrent_sessions", 10)
        self.max_failed_attempts = config.get("max_failed_attempts", 5)
        self.lockout_duration = config.get("lockout_duration", 900)
        self.require_mfa = config.get("require_mfa", False)
        self.geofence_enabled = config.get("geofence_enabled", False)
        self.geofence_countries = config.get("geofence_allowed_countries", [])
        self.ip_whitelist = config.get("ip_whitelist", [])
        self.ip_blacklist = config.get("ip_blacklist", [])
        self._sessions: Dict[str, EnhancedSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}
        self._locked_users: Dict[str, datetime] = {}
        self._activity_log: List[Dict[str, Any]] = []
        self._geo_db = GeoIPDatabaseExtended()
        self._device_scorer = DeviceTrustScorer()
        self._anomaly_detector = AnomalyDetector()
        self._revoked_tokens: Dict[str, datetime] = {}
        self._user_metadata: Dict[str, Dict[str, Any]] = {}
        self._session_events: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("SessionManagerExtended initialized")

    async def close(self) -> None:
        self._sessions.clear()
        self._user_sessions.clear()
        self._activity_log.clear()
        self._session_events.clear()
        logger.info("SessionManagerExtended closed")

    def is_locked(self, user_id: str) -> bool:
        lockout = self._locked_users.get(user_id)
        if not lockout:
            return False
        if datetime.utcnow() > lockout:
            del self._locked_users[user_id]
            return False
        return True

    def create_session_ext(self, user_id: str, fingerprint_data: Dict[str, Any],
                           auth_method: str = SessionAuthMethod.PASSWORD.value,
                           location: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           mfa_verified: bool = False,
                           mfa_method: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self.is_locked(user_id):
            logger.warning(f"User {user_id} is locked out")
            return None
        self._cleanup_expired_sessions()
        existing = self._user_sessions.get(user_id, [])
        if len(existing) >= self.max_concurrent_sessions:
            oldest = sorted(existing, key=lambda sid: self._sessions[sid].last_activity)[0]
            self.revoke_session_ext(oldest)
        fingerprint = EnhancedDeviceFingerprint(
            user_agent=fingerprint_data.get("user_agent", ""),
            platform=fingerprint_data.get("platform", ""),
            platform_version=fingerprint_data.get("platform_version"),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            screen_orientation=fingerprint_data.get("screen_orientation"),
            color_depth=fingerprint_data.get("color_depth"),
            pixel_ratio=fingerprint_data.get("pixel_ratio"),
            timezone=fingerprint_data.get("timezone"),
            timezone_offset=fingerprint_data.get("timezone_offset"),
            language=fingerprint_data.get("language"),
            languages=fingerprint_data.get("languages", []),
            canvas_hash=fingerprint_data.get("canvas_hash"),
            webgl_vendor=fingerprint_data.get("webgl_vendor"),
            webgl_renderer=fingerprint_data.get("webgl_renderer"),
            webgl_version=fingerprint_data.get("webgl_version"),
            installed_fonts=fingerprint_data.get("installed_fonts", []),
            installed_plugins=fingerprint_data.get("installed_plugins", []),
            ip_address=fingerprint_data.get("ip_address", ""),
            accept_language=fingerprint_data.get("accept_language"),
            hardware_concurrency=fingerprint_data.get("hardware_concurrency"),
            device_memory=fingerprint_data.get("device_memory"),
            touch_support=fingerprint_data.get("touch_support", False),
            max_touch_points=fingerprint_data.get("max_touch_points"),
            audio_fingerprint=fingerprint_data.get("audio_fingerprint"),
            battery_level=fingerprint_data.get("battery_level"),
            charging=fingerprint_data.get("charging"),
            cpu_architecture=fingerprint_data.get("cpu_architecture"),
            device_model=fingerprint_data.get("device_model"),
            device_vendor=fingerprint_data.get("device_vendor"),
            do_not_track=fingerprint_data.get("do_not_track"),
            ad_blocker_detected=fingerprint_data.get("ad_blocker_detected"),
            cookies_enabled=fingerprint_data.get("cookies_enabled"),
            localStorage_available=fingerprint_data.get("localStorage_available"),
            sessionStorage_available=fingerprint_data.get("sessionStorage_available"),
            indexed_db_available=fingerprint_data.get("indexed_db_available"),
        )
        ip = fingerprint.ip_address
        if ip in self.ip_blacklist:
            logger.warning(f"Blacklisted IP: {ip}")
            return None
        if self.ip_whitelist and ip not in self.ip_whitelist:
            logger.warning(f"IP {ip} not in whitelist")
            return None
        if location is None:
            location = self._geo_db.lookup(ip)
        if self.geofence_enabled and self.geofence_countries:
            country = location.get("country_code", "")
            if country not in self.geofence_countries:
                geofence_violation = True
                logger.warning(f"Geofence violation: {country} not allowed for user {user_id}")
            else:
                geofence_violation = False
        else:
            geofence_violation = False
        existing_sessions = self.get_user_sessions_ext(user_id)
        device_score = self._device_scorer.score_device(fingerprint, user_id, self._get_active_sessions(user_id))
        self._anomaly_detector.record_login(user_id, ip, location)
        velocity_score = self._anomaly_detector.check_login_velocity(user_id)
        impossible_travel, travel_score = self._anomaly_detector.check_impossible_travel(user_id, ip, location, self._geo_db)
        ip_freq_score = self._anomaly_detector.check_ip_frequency(user_id, ip)
        anomaly_score = max(velocity_score, travel_score, ip_freq_score)
        risk_score = anomaly_score * 0.4 + (1 - device_score) * 0.3 + (0.1 if geofence_violation else 0)
        if ip in self.ip_whitelist:
            risk_score *= 0.3
        if mfa_verified:
            risk_score *= 0.5
        risk_level = self._determine_risk_level(risk_score)
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        session = EnhancedSession(
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
            ip_address=ip,
            risk_level=risk_level,
            risk_score=risk_score,
            failed_attempts=0,
            mfa_verified=mfa_verified,
            mfa_method=mfa_method,
            tags=[],
            geofence_violation=geofence_violation,
            impossible_travel=impossible_travel,
            login_anomaly_score=anomaly_score,
            device_trust_score=device_score,
            metadata=metadata or {},
        )
        self._sessions[session_id] = session
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)
        self._device_scorer.record_location(user_id, ip)
        self._add_session_event(session_id, "session_created", {
            "auth_method": auth_method,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "device_trust_score": device_score,
        })
        self._log_activity(user_id, "session_created", {
            "session_id": session_id,
            "fingerprint_hash": fingerprint.compute_hash(),
            "risk_level": risk_level.value,
        })
        logger.info(f"Session {session_id} created for user {user_id} (risk: {risk_level.value}, score: {risk_score:.2f})")
        return session.to_dict()

    def _determine_risk_level(self, score: float) -> SessionRiskLevel:
        if score >= 0.8:
            return SessionRiskLevel.CRITICAL
        if score >= 0.5:
            return SessionRiskLevel.HIGH
        if score >= 0.25:
            return SessionRiskLevel.MEDIUM
        return SessionRiskLevel.LOW

    def _get_active_sessions(self, user_id: str) -> List[EnhancedSession]:
        session_ids = self._user_sessions.get(user_id, [])
        result = []
        for sid in session_ids:
            session = self._sessions.get(sid)
            if session and session.is_active:
                result.append(session)
        return result

    def get_session_ext(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session or not session.is_active or datetime.utcnow() > session.expires_at:
            return None
        session.last_activity = datetime.utcnow()
        return session.to_dict()

    def touch_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return False
        session.last_activity = datetime.utcnow()
        return True

    def revoke_session_ext(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.is_active = False
        user_sessions = self._user_sessions.get(session.user_id, [])
        if session_id in user_sessions:
            user_sessions.remove(session_id)
        self._add_session_event(session_id, "session_revoked", {})
        self._log_activity(session.user_id, "session_revoked", {"session_id": session_id})
        logger.info(f"Session {session_id} revoked for user {session.user_id}")
        return True

    def revoke_all_user_sessions_ext(self, user_id: str, exclude_current: Optional[str] = None,
                                     reason: str = "manual") -> int:
        count = 0
        session_ids = list(self._user_sessions.get(user_id, []))
        for sid in session_ids:
            if exclude_current and sid == exclude_current:
                continue
            if self.revoke_session_ext(sid):
                count += 1
        self._log_activity(user_id, "all_sessions_revoked", {"count": count, "reason": reason})
        logger.info(f"Revoked {count} sessions for user {user_id} (reason: {reason})")
        return count

    def get_user_sessions_ext(self, user_id: str, current_session_id: Optional[str] = None,
                              include_inactive: bool = False) -> List[Dict[str, Any]]:
        self._cleanup_expired_sessions()
        sessions = []
        for sid in self._user_sessions.get(user_id, []):
            session = self._sessions.get(sid)
            if session and (session.is_active or include_inactive):
                session_dict = session.to_dict()
                session_dict["is_current"] = (sid == current_session_id)
                sessions.append(session_dict)
        return sorted(sessions, key=lambda s: s["last_activity"], reverse=True)

    def refresh_session_ext(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return False
        if datetime.utcnow() > session.expires_at:
            return False
        session.expires_at = datetime.utcnow() + timedelta(seconds=self.session_ttl)
        session.last_activity = datetime.utcnow()
        return True

    def record_failed_attempt(self, session_id: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {"locked": False, "failed_attempts": 0}
        session.failed_attempts += 1
        if session.failed_attempts >= self.max_failed_attempts:
            self._locked_users[session.user_id] = datetime.utcnow() + timedelta(seconds=self.lockout_duration)
            session.is_active = False
            self._log_activity(session.user_id, "user_locked", {
                "session_id": session_id,
                "failed_attempts": session.failed_attempts,
                "lockout_duration": self.lockout_duration,
            })
            return {"locked": True, "failed_attempts": session.failed_attempts, "lockout_until": self._locked_users[session.user_id].isoformat()}
        return {"locked": False, "failed_attempts": session.failed_attempts}

    def detect_anomalies(self, user_id: str, fingerprint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = []
        existing_sessions = self.get_user_sessions_ext(user_id)
        ip = fingerprint_data.get("ip_address", "")
        new_fingerprint = EnhancedDeviceFingerprint(
            user_agent=fingerprint_data.get("user_agent", ""),
            platform=fingerprint_data.get("platform", ""),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            canvas_hash=fingerprint_data.get("canvas_hash"),
            webgl_vendor=fingerprint_data.get("webgl_vendor"),
            webgl_renderer=fingerprint_data.get("webgl_renderer"),
            audio_fingerprint=fingerprint_data.get("audio_fingerprint"),
            installed_fonts=fingerprint_data.get("installed_fonts", []),
            ip_address=ip,
            hardware_concurrency=fingerprint_data.get("hardware_concurrency"),
            device_memory=fingerprint_data.get("device_memory"),
            touch_support=fingerprint_data.get("touch_support", False),
            timezone=fingerprint_data.get("timezone"),
            language=fingerprint_data.get("language"),
            languages=[],
            installed_plugins=[],
        )
        new_hash = new_fingerprint.compute_hash()
        known_hashes = []
        known_ips = set()
        known_countries = set()
        for s in existing_sessions:
            fp = s.get("device_fingerprint", {})
            known_hashes.append(fp.get("fingerprint_hash", ""))
            known_ips.add(s.get("ip_address", ""))
            loc = s.get("location", {})
            if loc and loc.get("country_code"):
                known_countries.add(loc["country_code"])
        if existing_sessions and new_hash not in known_hashes:
            alerts.append({
                "type": "new_device",
                "severity": "medium",
                "message": "Login from unrecognized device",
                "fingerprint_hash": new_hash,
                "timestamp": datetime.utcnow().isoformat(),
            })
        if known_ips and ip not in known_ips:
            location = self._geo_db.lookup(ip)
            country = location.get("country_code", "ZZ")
            if known_countries and country not in known_countries:
                alerts.append({
                    "type": "new_country",
                    "severity": "high",
                    "message": f"Login from new country: {country} - {location.get('country', 'Unknown')}",
                    "country": country,
                    "ip": ip,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            else:
                alerts.append({
                    "type": "new_ip",
                    "severity": "low",
                    "message": f"Login from new IP address: {ip}",
                    "ip": ip,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        if location := self._geo_db.lookup(ip):
            if location.get("is_proxy") or location.get("is_vpn") or location.get("is_tor"):
                alerts.append({
                    "type": "anonymizer_detected",
                    "severity": "high",
                    "message": f"Login via {('VPN' if location.get('is_vpn') else 'proxy') if location.get('is_vpn') or location.get('is_proxy') else 'TOR'} detected",
                    "ip": ip,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        velocity_score = self._anomaly_detector.check_login_velocity(user_id)
        if velocity_score > 0.5:
            alerts.append({
                "type": "high_login_velocity",
                "severity": "medium",
                "message": f"Unusual login frequency detected (score: {velocity_score:.2f})",
                "score": velocity_score,
                "timestamp": datetime.utcnow().isoformat(),
            })
        return alerts

    def get_session_events(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        events = self._session_events.get(session_id, [])
        return events[-limit:]

    def _add_session_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> None:
        if session_id not in self._session_events:
            self._session_events[session_id] = []
        self._session_events[session_id].append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        if len(self._session_events[session_id]) > 1000:
            self._session_events[session_id] = self._session_events[session_id][-500:]

    def get_activity_log_ext(self, user_id: Optional[str] = None,
                             limit: int = 100, offset: int = 0,
                             action_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        activities = self._activity_log
        if user_id:
            activities = [a for a in activities if a["user_id"] == user_id]
        if action_filter:
            activities = [a for a in activities if a["action"] == action_filter]
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

    def get_statistics_ext(self) -> Dict[str, Any]:
        self._cleanup_expired_sessions()
        active = sum(1 for s in self._sessions.values() if s.is_active)
        total_users = len(self._user_sessions)
        avg_sessions = round(active / total_users, 2) if total_users > 0 else 0
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        auth_methods = {}
        platforms = {}
        mfa_count = 0
        for s in self._sessions.values():
            risk_distribution[s.risk_level.value] = risk_distribution.get(s.risk_level.value, 0) + 1
            auth_methods[s.auth_method] = auth_methods.get(s.auth_method, 0) + 1
            p = s.device_fingerprint.platform
            platforms[p] = platforms.get(p, 0) + 1
            if s.mfa_verified:
                mfa_count += 1
        return {
            "active_sessions": active,
            "total_users_with_sessions": total_users,
            "avg_sessions_per_user": avg_sessions,
            "risk_distribution": risk_distribution,
            "auth_methods": auth_methods,
            "platforms": platforms,
            "mfa_verified_sessions": mfa_count,
            "mfa_verification_rate": round(mfa_count / active, 2) if active > 0 else 0,
            "geofence_violations": sum(1 for s in self._sessions.values() if s.geofence_violation),
            "impossible_travel_detected": sum(1 for s in self._sessions.values() if s.impossible_travel),
            "session_ttl": self.session_ttl,
            "max_concurrent": self.max_concurrent_sessions,
            "locked_users": len(self._locked_users),
        }

    def set_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> None:
        if user_id not in self._user_metadata:
            self._user_metadata[user_id] = {}
        self._user_metadata[user_id].update(metadata)

    def get_user_metadata(self, user_id: str) -> Dict[str, Any]:
        return self._user_metadata.get(user_id, {})

    def add_geo_entry(self, ip_address: str, data: Dict[str, Any]) -> None:
        self._geo_db.add_entry(ip_address, data)

    def bulk_add_geo_entries(self, entries: Dict[str, Dict[str, Any]]) -> int:
        return self._geo_db.bulk_add(entries)

    def add_to_whitelist(self, ip_address: str) -> None:
        if ip_address not in self.ip_whitelist:
            self.ip_whitelist.append(ip_address)

    def remove_from_whitelist(self, ip_address: str) -> bool:
        if ip_address in self.ip_whitelist:
            self.ip_whitelist.remove(ip_address)
            return True
        return False

    def add_to_blacklist(self, ip_address: str) -> None:
        if ip_address not in self.ip_blacklist:
            self.ip_blacklist.append(ip_address)

    def remove_from_blacklist(self, ip_address: str) -> bool:
        if ip_address in self.ip_blacklist:
            self.ip_blacklist.remove(ip_address)
            return True
        return False

    def get_whitelist(self) -> List[str]:
        return list(self.ip_whitelist)

    def get_blacklist(self) -> List[str]:
        return list(self.ip_blacklist)

    def tag_session(self, session_id: str, tag: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        if tag not in session.tags:
            session.tags.append(tag)
        return True

    def untag_session(self, session_id: str, tag: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        if tag in session.tags:
            session.tags.remove(tag)
        return True

    def search_sessions(self, query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if fields is None:
            fields = ["user_id", "ip_address", "auth_method"]
        results = []
        for session in self._sessions.values():
            if not session.is_active:
                continue
            for field in fields:
                value = getattr(session, field, None)
                if value and query.lower() in str(value).lower():
                    results.append(session.to_dict())
                    break
        return sorted(results, key=lambda s: s["last_activity"], reverse=True)[:100]
