import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AccessRequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"

class AccessLevel(Enum):
    READ_ONLY = "read_only"
    OPERATOR = "operator"
    ADMIN = "admin"
    BREAK_GLASS = "break_glass"

class JustificationLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

DATA_FILE = "data/pam_requests.json"

BREAK_GLASS_CONFIG = {
    "enabled": True,
    "max_duration_minutes": 60,
    "requires_approval": False,
    "notify_on_use": True,
    "audit_log_all_actions": True,
    "auto_revoke_on_expiry": True,
    "emergency_contacts": ["security-team@infra-pilot.local"],
}

PAM_POLICIES = [
    {"policy_id": "pam_default", "name": "Default PAM Policy",
     "description": "Standard privileged access policy",
     "max_session_duration": 14400, "require_mfa": True,
     "require_ticket": True, "approval_required": True,
     "approval_count": 1, "allowed_access_levels": ["read_only", "operator"],
     "justification_required": JustificationLevel.MEDIUM.value},
    {"policy_id": "pam_admin", "name": "Admin Access Policy",
     "description": "Elevated admin access policy",
     "max_session_duration": 3600, "require_mfa": True,
     "require_ticket": True, "approval_required": True,
     "approval_count": 2, "allowed_access_levels": ["read_only", "operator", "admin"],
     "justification_required": JustificationLevel.HIGH.value},
    {"policy_id": "pam_emergency", "name": "Emergency Break-Glass Policy",
     "description": "Emergency access with automatic approval",
     "max_session_duration": 3600, "require_mfa": True,
     "require_ticket": False, "approval_required": False,
     "approval_count": 0, "allowed_access_levels": ["read_only", "operator", "admin", "break_glass"],
     "justification_required": JustificationLevel.MEDIUM.value},
]


class AccessRequest:
    def __init__(self, request_id: str, user_id: str, resource: str,
                 requested_role: str, reason: str, duration: int = 3600,
                 access_level: str = "operator",
                 justification_level: str = "medium"):
        self.request_id = request_id
        self.user_id = user_id
        self.resource = resource
        self.requested_role = requested_role
        self.reason = reason
        self.duration = duration
        self.access_level = AccessLevel(access_level)
        self.justification_level = JustificationLevel(justification_level)
        self.status = AccessRequestStatus.PENDING
        self.approved_by: Optional[str] = None
        self.denied_by: Optional[str] = None
        self.approved_at: Optional[str] = None
        self.denied_at: Optional[str] = None
        self.expires_at = None
        self.created_at = datetime.utcnow().isoformat()
        self.ticket_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"request_id": self.request_id, "user_id": self.user_id,
                "resource": self.resource, "requested_role": self.requested_role,
                "reason": self.reason, "duration": self.duration,
                "access_level": self.access_level.value,
                "justification_level": self.justification_level.value,
                "status": self.status.value, "approved_by": self.approved_by,
                "denied_by": self.denied_by, "approved_at": self.approved_at,
                "denied_at": self.denied_at, "expires_at": self.expires_at,
                "created_at": self.created_at, "ticket_ref": self.ticket_ref}


class BreakGlassEvent:
    def __init__(self, event_id: str, user_id: str, resource: str,
                 reason: str, duration: int):
        self.event_id = event_id
        self.user_id = user_id
        self.resource = resource
        self.reason = reason
        self.duration = duration
        self.started_at = datetime.utcnow().isoformat()
        self.ended_at: Optional[str] = None
        self.actions_taken: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "user_id": self.user_id,
                "resource": self.resource, "reason": self.reason,
                "duration": self.duration, "started_at": self.started_at,
                "ended_at": self.ended_at, "actions_taken": self.actions_taken}


class PAMManager:
    def __init__(self):
        self._requests: Dict[str, AccessRequest] = {}
        self._break_glass_events: Dict[str, BreakGlassEvent] = {}
        self._initialized = False

    async def initialize(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"requests": [], "break_glass_events": []}
        for r in data.get("requests", []):
            req = AccessRequest(r["request_id"], r["user_id"], r["resource"],
                                r["requested_role"], r["reason"], r.get("duration", 3600))
            req.status = AccessRequestStatus(r.get("status", "pending"))
            req.approved_by = r.get("approved_by")
            req.denied_by = r.get("denied_by")
            req.approved_at = r.get("approved_at")
            req.denied_at = r.get("denied_at")
            req.expires_at = r.get("expires_at")
            req.created_at = r.get("created_at", req.created_at)
            req.ticket_ref = r.get("ticket_ref")
            req.access_level = AccessLevel(r.get("access_level", "operator"))
            self._requests[r["request_id"]] = req
        for e in data.get("break_glass_events", []):
            evt = BreakGlassEvent(e["event_id"], e["user_id"], e["resource"],
                                  e["reason"], e.get("duration", 3600))
            evt.started_at = e.get("started_at", evt.started_at)
            evt.ended_at = e.get("ended_at")
            evt.actions_taken = e.get("actions_taken", [])
            self._break_glass_events[e["event_id"]] = evt
        self._initialized = True
        logger.info(f"PAMManager initialized with {len(self._requests)} requests, {len(self._break_glass_events)} break-glass events")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"requests": [r.to_dict() for r in self._requests.values()],
                "break_glass_events": [e.to_dict() for e in self._break_glass_events.values()]}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def list_policies(self) -> List[Dict[str, Any]]:
        return PAM_POLICIES

    def get_break_glass_config(self) -> Dict[str, Any]:
        return BREAK_GLASS_CONFIG

    def list_requests(self, user_id: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        requests = self._requests.values()
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        if status:
            requests = [r for r in requests if r.status.value == status]
        return [r.to_dict() for r in requests]

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        r = self._requests.get(request_id)
        return r.to_dict() if r else None

    def create_request(self, user_id: str, resource: str, role: str,
                       reason: str, duration: int = 3600,
                       access_level: str = "operator") -> Dict[str, Any]:
        rid = uuid.uuid4().hex[:16]
        req = AccessRequest(rid, user_id, resource, role, reason, duration, access_level)
        self._requests[rid] = req
        return req.to_dict()

    def approve_request(self, request_id: str, approver_id: str) -> bool:
        r = self._requests.get(request_id)
        if not r or r.status != AccessRequestStatus.PENDING:
            return False
        r.status = AccessRequestStatus.APPROVED
        r.approved_by = approver_id
        r.approved_at = datetime.utcnow().isoformat()
        r.expires_at = (datetime.utcnow() + timedelta(seconds=r.duration)).isoformat()
        return True

    def deny_request(self, request_id: str, approver_id: str) -> bool:
        r = self._requests.get(request_id)
        if not r or r.status != AccessRequestStatus.PENDING:
            return False
        r.status = AccessRequestStatus.DENIED
        r.denied_by = approver_id
        r.denied_at = datetime.utcnow().isoformat()
        return True

    def expire_request(self, request_id: str) -> bool:
        r = self._requests.get(request_id)
        if not r:
            return False
        r.status = AccessRequestStatus.EXPIRED
        return True

    def initiate_break_glass(self, user_id: str, resource: str,
                              reason: str, duration: int = 3600) -> Dict[str, Any]:
        eid = uuid.uuid4().hex[:16]
        evt = BreakGlassEvent(eid, user_id, resource, reason, duration)
        self._break_glass_events[eid] = evt
        return evt.to_dict()

    def end_break_glass(self, event_id: str) -> bool:
        evt = self._break_glass_events.get(event_id)
        if not evt:
            return False
        evt.ended_at = datetime.utcnow().isoformat()
        return True

    def log_break_glass_action(self, event_id: str, action: str) -> bool:
        evt = self._break_glass_events.get(event_id)
        if not evt:
            return False
        evt.actions_taken.append(action)
        return True

    def get_statistics(self) -> Dict[str, Any]:
        requests = self._requests.values()
        return {"total_requests": len(requests),
                "pending": sum(1 for r in requests if r.status == AccessRequestStatus.PENDING),
                "approved": sum(1 for r in requests if r.status == AccessRequestStatus.APPROVED),
                "denied": sum(1 for r in requests if r.status == AccessRequestStatus.DENIED),
                "break_glass_events": len(self._break_glass_events),
                "active_policies": len(PAM_POLICIES)}
