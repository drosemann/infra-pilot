import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PAMRequest:
    request_id: str
    user_id: str
    target_role: str
    duration_minutes: int
    reason: str
    status: str
    approver_id: Optional[str]
    approved_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    is_break_glass: bool
    justification: Optional[str]
    resource_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "target_role": self.target_role,
            "duration_minutes": self.duration_minutes,
            "reason": self.reason,
            "status": self.status,
            "approver_id": self.approver_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "is_break_glass": self.is_break_glass,
            "justification": self.justification,
            "resource_ids": self.resource_ids,
        }


@dataclass
class SessionRecording:
    recording_id: str
    session_id: str
    user_id: str
    target_host: str
    start_time: datetime
    end_time: Optional[datetime]
    recording_data: List[Dict[str, Any]]
    command_count: int
    file_path: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "target_host": self.target_host,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "command_count": self.command_count,
            "file_path": self.file_path,
        }


AVAILABLE_ROLES = {
    "viewer": {
        "description": "Read-only access to resources",
        "permissions": ["resource:list", "resource:get", "log:read"],
        "max_duration": 480,
        "requires_approval": False,
    },
    "operator": {
        "description": "Basic operational tasks",
        "permissions": ["resource:list", "resource:get", "resource:start", "resource:stop",
                        "resource:restart", "log:read", "log:stream"],
        "max_duration": 240,
        "requires_approval": False,
    },
    "admin": {
        "description": "Full administrative access",
        "permissions": ["resource:*", "config:*", "user:list", "user:get",
                        "deploy:*", "backup:*", "log:*"],
        "max_duration": 120,
        "requires_approval": True,
    },
    "break_glass": {
        "description": "Emergency super-admin access",
        "permissions": ["*"],
        "max_duration": 60,
        "requires_approval": False,
        "post_justification_required": True,
    },
}


class SessionRecorder:
    def __init__(self):
        self._recordings: Dict[str, SessionRecording] = {}
        self._active_recordings: Dict[str, str] = {}

    def start_recording(self, session_id: str, user_id: str, target_host: str) -> str:
        recording_id = str(uuid.uuid4())
        recording = SessionRecording(
            recording_id=recording_id,
            session_id=session_id,
            user_id=user_id,
            target_host=target_host,
            start_time=datetime.utcnow(),
            end_time=None,
            recording_data=[],
            command_count=0,
            file_path=f"/recordings/{recording_id}.cast",
        )
        self._recordings[recording_id] = recording
        self._active_recordings[session_id] = recording_id
        return recording_id

    def record_command(self, session_id: str, command: str, output: str,
                       timestamp: Optional[datetime] = None) -> None:
        recording_id = self._active_recordings.get(session_id)
        if not recording_id:
            return
        recording = self._recordings.get(recording_id)
        if not recording:
            return
        recording.recording_data.append({
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "command": command,
            "output": output[:1000],
        })
        recording.command_count += 1

    def stop_recording(self, session_id: str) -> Optional[str]:
        recording_id = self._active_recordings.pop(session_id, None)
        if not recording_id:
            return None
        recording = self._recordings.get(recording_id)
        if recording:
            recording.end_time = datetime.utcnow()
        return recording_id

    def get_recording(self, recording_id: str) -> Optional[SessionRecording]:
        return self._recordings.get(recording_id)

    def get_session_recording(self, session_id: str) -> Optional[SessionRecording]:
        recording_id = self._active_recordings.get(session_id)
        if recording_id:
            return self._recordings.get(recording_id)
        for rec in self._recordings.values():
            if rec.session_id == session_id:
                return rec
        return None

    def search_recordings(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for rec in self._recordings.values():
            if user_id and rec.user_id != user_id:
                continue
            for entry in rec.recording_data:
                if query.lower() in entry["command"].lower() or query.lower() in entry["output"].lower():
                    results.append({
                        "recording_id": rec.recording_id,
                        "session_id": rec.session_id,
                        "user_id": rec.user_id,
                        "timestamp": entry["timestamp"],
                        "command": entry["command"],
                        "output": entry["output"],
                    })
                    break
        return results[:100]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_recordings": len(self._recordings),
            "active_recordings": len(self._active_recordings),
            "total_commands": sum(r.command_count for r in self._recordings.values()),
            "total_duration_minutes": sum(
                ((r.end_time or datetime.utcnow()) - r.start_time).total_seconds() / 60
                for r in self._recordings.values()
            ),
        }


class PAMManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._requests: Dict[str, PAMRequest] = {}
        self._active_grants: Dict[str, Dict[str, Any]] = {}
        self._approval_chain: Dict[str, List[str]] = {}
        self.recorder = SessionRecorder()
        self._auto_approve_domains = config.get("auto_approve_domains", [])
        self._audit_log: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("PAMManager initialized")

    async def close(self) -> None:
        self._requests.clear()
        self._active_grants.clear()
        self._audit_log.clear()
        logger.info("PAMManager closed")

    def request_access(self, user_id: str, target_role: str, duration_minutes: int,
                       reason: str, resource_ids: Optional[List[str]] = None,
                       is_break_glass: bool = False) -> Dict[str, Any]:
        if target_role not in AVAILABLE_ROLES:
            raise ValueError(f"Invalid role: {target_role}. Valid roles: {list(AVAILABLE_ROLES.keys())}")

        role_config = AVAILABLE_ROLES[target_role]
        if duration_minutes > role_config["max_duration"]:
            raise ValueError(f"Duration {duration_minutes} exceeds max {role_config['max_duration']} for role {target_role}")

        request_id = str(uuid.uuid4())
        now = datetime.utcnow()

        if is_break_glass:
            self._audit_log.append({
                "type": "break_glass_requested",
                "user_id": user_id,
                "role": target_role,
                "timestamp": now.isoformat(),
                "request_id": request_id,
            })

        status = "pending_approval" if role_config["requires_approval"] and not is_break_glass else "approved"

        request = PAMRequest(
            request_id=request_id,
            user_id=user_id,
            target_role=target_role,
            duration_minutes=duration_minutes,
            reason=reason,
            status=status,
            approver_id=None,
            approved_at=now if status == "approved" else None,
            expires_at=now + timedelta(minutes=duration_minutes) if status == "approved" else None,
            created_at=now,
            is_break_glass=is_break_glass,
            justification=None,
            resource_ids=resource_ids or [],
        )

        self._requests[request_id] = request

        if status == "approved":
            self._grant_access(user_id, target_role, request_id, duration_minutes)

        logger.info(f"Access request {request_id} created for user {user_id} role {target_role} status={status}")
        return request.to_dict()

    def approve_request(self, request_id: str, approver_id: str) -> Optional[Dict[str, Any]]:
        request = self._requests.get(request_id)
        if not request or request.status != "pending_approval":
            return None

        request.status = "approved"
        request.approver_id = approver_id
        request.approved_at = datetime.utcnow()
        request.expires_at = datetime.utcnow() + timedelta(minutes=request.duration_minutes)

        self._grant_access(request.user_id, request.target_role, request_id, request.duration_minutes)

        self._audit_log.append({
            "type": "access_approved",
            "request_id": request_id,
            "user_id": request.user_id,
            "approver_id": approver_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info(f"Request {request_id} approved by {approver_id}")
        return request.to_dict()

    def deny_request(self, request_id: str, approver_id: str, reason: str = "") -> Optional[Dict[str, Any]]:
        request = self._requests.get(request_id)
        if not request or request.status != "pending_approval":
            return None

        request.status = "denied"
        request.approver_id = approver_id

        self._audit_log.append({
            "type": "access_denied",
            "request_id": request_id,
            "user_id": request.user_id,
            "approver_id": approver_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info(f"Request {request_id} denied by {approver_id}")
        return request.to_dict()

    def _grant_access(self, user_id: str, role: str, request_id: str, duration: int) -> None:
        grant_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=duration)

        self._active_grants[grant_id] = {
            "grant_id": grant_id,
            "user_id": user_id,
            "role": role,
            "request_id": request_id,
            "granted_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "permissions": AVAILABLE_ROLES[role]["permissions"],
        }

    def get_active_grant(self, user_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        for grant_id, grant in list(self._active_grants.items()):
            expiry = datetime.fromisoformat(grant["expires_at"])
            if now > expiry:
                del self._active_grants[grant_id]
                continue
            if grant["user_id"] == user_id:
                return grant
        return None

    def revoke_grant(self, user_id: str) -> bool:
        for grant_id, grant in list(self._active_grants.items()):
            if grant["user_id"] == user_id:
                del self._active_grants[grant_id]
                self._audit_log.append({
                    "type": "access_revoked",
                    "user_id": user_id,
                    "role": grant["role"],
                    "timestamp": datetime.utcnow().isoformat(),
                })
                logger.info(f"Access revoked for user {user_id}")
                return True
        return False

    def check_permission(self, user_id: str, permission: str) -> bool:
        grant = self.get_active_grant(user_id)
        if not grant:
            return False
        permissions = grant["permissions"]
        for p in permissions:
            if p == "*" or p == permission:
                return True
            if p.endswith(":*") and permission.startswith(p[:-2]):
                return True
        return False

    def get_pending_requests(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        requests = []
        for req in self._requests.values():
            if req.status == "pending_approval":
                if not user_id or req.user_id == user_id:
                    requests.append(req.to_dict())
        return sorted(requests, key=lambda r: r["created_at"], reverse=True)

    def get_request_history(self, user_id: Optional[str] = None,
                            limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        requests = list(self._requests.values())
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return [r.to_dict() for r in requests[offset:offset + limit]]

    def set_approval_chain(self, user_id: str, approvers: List[str]) -> None:
        self._approval_chain[user_id] = approvers

    def get_approval_chain(self, user_id: str) -> List[str]:
        return self._approval_chain.get(user_id, [])

    def break_glass(self, user_id: str, justification: str,
                    resource_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        result = self.request_access(
            user_id=user_id,
            target_role="break_glass",
            duration_minutes=60,
            reason="Emergency break-glass access",
            resource_ids=resource_ids,
            is_break_glass=True,
        )

        request = self._requests.get(result["request_id"])
        if request:
            request.justification = justification

        self._audit_log.append({
            "type": "break_glass_activated",
            "user_id": user_id,
            "justification": justification,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": result["request_id"],
        })

        logger.warning(f"BREAK GLASS activated for user {user_id}: {justification}")
        return result

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._audit_log[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._requests)
        approved = sum(1 for r in self._requests.values() if r.status == "approved")
        denied = sum(1 for r in self._requests.values() if r.status == "denied")
        pending = sum(1 for r in self._requests.values() if r.status == "pending_approval")
        active_grants = len(self._active_grants)
        return {
            "total_requests": total,
            "approved": approved,
            "denied": denied,
            "pending": pending,
            "active_grants": active_grants,
            "break_glass_events": sum(1 for r in self._requests.values() if r.is_break_glass),
            "avg_duration_minutes": round(
                sum(r.duration_minutes for r in self._requests.values()) / total, 1
            ) if total > 0 else 0,
        }
