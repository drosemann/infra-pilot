import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MFAMethod(Enum):
    TOTP = "totp"
    WEBAUTHN = "webauthn"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"

DATA_FILE = "data/sessions.json"

RISK_FACTORS = [
    {"factor": "new_location", "weight": 20, "description": "Login from unrecognized location"},
    {"factor": "new_device", "weight": 25, "description": "Login from unrecognized device"},
    {"factor": "off_hours", "weight": 15, "description": "Login outside normal hours"},
    {"factor": "failed_attempts", "weight": 30, "description": "Multiple failed login attempts"},
    {"factor": "vpn_proxy", "weight": 20, "description": "Login via VPN or proxy"},
    {"factor": "velocity", "weight": 25, "description": "Unusual geographic velocity"},
    {"factor": "new_ip", "weight": 15, "description": "Login from never-before-seen IP"},
    {"factor": "tor", "weight": 35, "description": "Login from Tor exit node"},
    {"factor": "known_malicious", "weight": 50, "description": "IP associated with malicious activity"},
]

RISK_THRESHOLDS = [
    {"level": RiskLevel.LOW, "max_score": 20},
    {"level": RiskLevel.MEDIUM, "max_score": 50},
    {"level": RiskLevel.HIGH, "max_score": 80},
    {"level": RiskLevel.CRITICAL, "max_score": 100},
]

SESSION_DURATIONS = {
    "web": timedelta(hours=24),
    "mobile": timedelta(days=30),
    "api": timedelta(hours=1),
    "cli": timedelta(hours=8),
}


class UserSession:
    def __init__(self, session_id: str, user_id: str, user_agent: str,
                 ip_address: str, client_type: str = "web",
                 mfa_method: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.client_type = client_type
        self.mfa_method = mfa_method
        self.status = SessionStatus.ACTIVE
        self.risk_score = 0
        self.risk_level = RiskLevel.LOW
        self.created_at = datetime.utcnow().isoformat()
        self.last_activity_at = self.created_at
        duration = SESSION_DURATIONS.get(client_type, timedelta(hours=24))
        self.expires_at = (datetime.utcnow() + duration).isoformat()
        self.failed_refresh_count = 0
        self.device_fingerprint = uuid.uuid4().hex[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "user_id": self.user_id,
                "user_agent": self.user_agent, "ip_address": self.ip_address,
                "client_type": self.client_type, "mfa_method": self.mfa_method,
                "status": self.status.value, "risk_score": self.risk_score,
                "risk_level": self.risk_level.value, "created_at": self.created_at,
                "last_activity_at": self.last_activity_at, "expires_at": self.expires_at,
                "device_fingerprint": self.device_fingerprint}


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        self._risk_history: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"sessions": [], "risk_history": []}
        for s in data.get("sessions", []):
            session = UserSession(s["session_id"], s["user_id"], s.get("user_agent", ""),
                                  s.get("ip_address", ""), s.get("client_type", "web"))
            session.status = SessionStatus(s.get("status", "active"))
            session.risk_score = s.get("risk_score", 0)
            session.risk_level = RiskLevel(s.get("risk_level", "low"))
            session.created_at = s.get("created_at", session.created_at)
            session.last_activity_at = s.get("last_activity_at", session.last_activity_at)
            session.expires_at = s.get("expires_at", session.expires_at)
            session.mfa_method = s.get("mfa_method")
            session.device_fingerprint = s.get("device_fingerprint", session.device_fingerprint)
            self._sessions[s["session_id"]] = session
        self._risk_history = data.get("risk_history", [])
        self._initialized = True
        logger.info(f"SessionManager initialized with {len(self._sessions)} sessions")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"sessions": [s.to_dict() for s in self._sessions.values()],
                "risk_history": self._risk_history[-1000:]}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def create_session(self, user_id: str, user_agent: str, ip_address: str,
                       client_type: str = "web",
                       mfa_method: Optional[str] = None) -> Dict[str, Any]:
        sid = uuid.uuid4().hex[:24]
        session = UserSession(sid, user_id, user_agent, ip_address, client_type, mfa_method)
        risk = self.evaluate_risk(user_id, ip_address, user_agent)
        session.risk_score = risk["score"]
        session.risk_level = risk["level"]
        self._sessions[sid] = session
        self._risk_history.append({"session_id": sid, "user_id": user_id,
                                    "risk_score": risk["score"], "risk_level": risk["level"].value,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "factors": risk.get("triggered_factors", [])})
        return session.to_dict()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        s = self._sessions.get(session_id)
        return s.to_dict() if s else None

    def list_sessions(self, user_id: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = self._sessions.values()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        if status:
            sessions = [s for s in sessions if s.status.value == status]
        return [s.to_dict() for s in sessions]

    def update_activity(self, session_id: str) -> bool:
        s = self._sessions.get(session_id)
        if not s:
            return False
        s.last_activity_at = datetime.utcnow().isoformat()
        return True

    def revoke_session(self, session_id: str) -> bool:
        s = self._sessions.get(session_id)
        if not s:
            return False
        s.status = SessionStatus.REVOKED
        return True

    def expire_session(self, session_id: str) -> bool:
        s = self._sessions.get(session_id)
        if not s:
            return False
        s.status = SessionStatus.EXPIRED
        return True

    def list_risk_factors(self) -> List[Dict[str, Any]]:
        return RISK_FACTORS

    def evaluate_risk(self, user_id: str, ip_address: str,
                      user_agent: str) -> Dict[str, Any]:
        score = 0
        triggered = []
        for factor in RISK_FACTORS:
            if factor["factor"] == "off_hours":
                hour = datetime.utcnow().hour
                if hour < 6 or hour > 22:
                    score += factor["weight"]
                    triggered.append(factor["factor"])
            elif factor["factor"] == "new_device":
                existing = [s for s in self._sessions.values()
                            if s.user_id == user_id and s.user_agent != user_agent]
                if len(existing) > 3:
                    score += factor["weight"]
                    triggered.append(factor["factor"])
            elif factor["factor"] == "failed_attempts":
                pass
            else:
                if factor["weight"] > 0 and score < factor["weight"] * 2:
                    score += 5
        score = min(score, 100)
        level = RiskLevel.LOW
        for t in RISK_THRESHOLDS:
            if score <= t["max_score"]:
                level = t["level"]
                break
        return {"score": score, "level": level, "triggered_factors": triggered}

    def get_statistics(self) -> Dict[str, Any]:
        sessions = self._sessions.values()
        return {"total_sessions": len(sessions),
                "active_sessions": sum(1 for s in sessions if s.status == SessionStatus.ACTIVE),
                "expired_sessions": sum(1 for s in sessions if s.status == SessionStatus.EXPIRED),
                "revoked_sessions": sum(1 for s in sessions if s.status == SessionStatus.REVOKED),
                "high_risk_sessions": sum(1 for s in sessions if s.risk_level == RiskLevel.HIGH or s.risk_level == RiskLevel.CRITICAL)}

    def cleanup_expired(self):
        now = datetime.utcnow().isoformat()
        expired = [sid for sid, s in self._sessions.items() if s.expires_at < now and s.status == SessionStatus.ACTIVE]
        for sid in expired:
            self._sessions[sid].status = SessionStatus.EXPIRED
        return len(expired)
