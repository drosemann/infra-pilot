"""Extended privileged access management with session recording, approval workflows, and audit."""
import json
import uuid
import hashlib
import logging
import secrets
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PAMRoleDefinition:
    role_id: str
    name: str
    description: str
    permissions: List[str]
    max_duration_minutes: int
    requires_approval: bool
    requires_mfa: bool
    requires_ticket: bool
    approval_required_count: int
    allowed_approver_roles: List[str]
    notify_on_grant: bool
    notify_on_expiry: bool
    session_recording_required: bool
    allowed_ip_ranges: List[str]
    allowed_time_windows: List[Dict[str, Any]]
    risk_level: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "max_duration_minutes": self.max_duration_minutes,
            "requires_approval": self.requires_approval,
            "requires_mfa": self.requires_mfa,
            "requires_ticket": self.requires_ticket,
            "approval_required_count": self.approval_required_count,
            "allowed_approver_roles": self.allowed_approver_roles,
            "notify_on_grant": self.notify_on_grant,
            "notify_on_expiry": self.notify_on_expiry,
            "session_recording_required": self.session_recording_required,
            "allowed_ip_ranges": self.allowed_ip_ranges,
            "risk_level": self.risk_level,
            "tags": self.tags,
        }


@dataclass
class PAMAccessRequest:
    request_id: str
    user_id: str
    user_name: str
    target_role: str
    target_resource: str
    resource_type: str
    duration_minutes: int
    reason: str
    ticket_id: Optional[str]
    status: str
    approvers: List[Dict[str, Any]]
    approvals_required: int
    approvals_received: int
    approver_id: Optional[str]
    approved_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    is_break_glass: bool
    justification: Optional[str]
    mfa_verified: bool
    ip_address: Optional[str]
    risk_score: float
    session_recording_id: Optional[str]
    resource_ids: List[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    denial_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "target_role": self.target_role,
            "target_resource": self.target_resource,
            "resource_type": self.resource_type,
            "duration_minutes": self.duration_minutes,
            "reason": self.reason,
            "ticket_id": self.ticket_id,
            "status": self.status,
            "approvers": self.approvers,
            "approvals_required": self.approvals_required,
            "approvals_received": self.approvals_received,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "is_break_glass": self.is_break_glass,
            "justification": self.justification,
            "mfa_verified": self.mfa_verified,
            "ip_address": self.ip_address,
            "risk_score": round(self.risk_score, 2),
            "session_recording_id": self.session_recording_id,
            "resource_ids": self.resource_ids,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "denial_reason": self.denial_reason,
        }


@dataclass
class PAMSessionRecording:
    recording_id: str
    session_id: str
    user_id: str
    target_host: str
    target_port: int
    protocol: str
    start_time: datetime
    end_time: Optional[datetime]
    commands: List[Dict[str, Any]]
    keystrokes: List[Dict[str, Any]]
    file_transfers: List[Dict[str, Any]]
    command_count: int
    file_path: Optional[str]
    size_bytes: int
    status: str
    tags: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "target_host": self.target_host,
            "target_port": self.target_port,
            "protocol": self.protocol,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "command_count": self.command_count,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "tags": self.tags,
        }


class PAMRoleManager:
    def __init__(self):
        self._roles: Dict[str, PAMRoleDefinition] = {}
        self._init_default_roles()

    def _init_default_roles(self) -> None:
        default_roles = [
            PAMRoleDefinition(
                role_id="role-viewer",
                name="Viewer",
                description="Read-only access to resources and logs",
                permissions=["resource:list", "resource:get", "log:read", "monitoring:view"],
                max_duration_minutes=480,
                requires_approval=False,
                requires_mfa=False,
                requires_ticket=False,
                approval_required_count=1,
                allowed_approver_roles=["admin", "super_admin"],
                notify_on_grant=False,
                notify_on_expiry=False,
                session_recording_required=False,
                allowed_ip_ranges=["0.0.0.0/0"],
                allowed_time_windows=[],
                risk_level="low",
                tags=["read-only", "monitoring"],
            ),
            PAMRoleDefinition(
                role_id="role-operator",
                name="Operator",
                description="Day-to-day operational tasks",
                permissions=["resource:list", "resource:get", "resource:start", "resource:stop",
                             "resource:restart", "log:read", "log:stream", "backup:list", "backup:create",
                             "monitoring:view", "monitoring:alert"],
                max_duration_minutes=240,
                requires_approval=False,
                requires_mfa=True,
                requires_ticket=False,
                approval_required_count=1,
                allowed_approver_roles=["admin", "super_admin"],
                notify_on_grant=False,
                notify_on_expiry=True,
                session_recording_required=False,
                allowed_ip_ranges=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
                allowed_time_windows=[],
                risk_level="medium",
                tags=["operations", "day-to-day"],
            ),
            PAMRoleDefinition(
                role_id="role-admin",
                name="Administrator",
                description="Full administrative access to resources",
                permissions=["resource:*", "config:*", "user:list", "user:get", "user:create",
                             "deploy:*", "backup:*", "log:*", "monitoring:*", "security:*",
                             "network:*", "storage:*", "database:*"],
                max_duration_minutes=120,
                requires_approval=True,
                requires_mfa=True,
                requires_ticket=True,
                approval_required_count=2,
                allowed_approver_roles=["super_admin"],
                notify_on_grant=True,
                notify_on_expiry=True,
                session_recording_required=True,
                allowed_ip_ranges=["10.0.0.0/8", "172.16.0.0/12"],
                allowed_time_windows=[{"days": ["Mon-Fri"], "start": "06:00", "end": "22:00"}],
                risk_level="high",
                tags=["administration", "elevated"],
            ),
            PAMRoleDefinition(
                role_id="role-super-admin",
                name="Super Administrator",
                description="Unrestricted access to all systems",
                permissions=["*"],
                max_duration_minutes=60,
                requires_approval=True,
                requires_mfa=True,
                requires_ticket=True,
                approval_required_count=3,
                allowed_approver_roles=["super_admin"],
                notify_on_grant=True,
                notify_on_expiry=True,
                session_recording_required=True,
                allowed_ip_ranges=["10.0.0.0/8"],
                allowed_time_windows=[{"days": ["Mon-Fri"], "start": "08:00", "end": "18:00"}],
                risk_level="critical",
                tags=["super-admin", "unrestricted"],
            ),
            PAMRoleDefinition(
                role_id="role-break-glass",
                name="Break Glass",
                description="Emergency access bypassing normal controls",
                permissions=["*"],
                max_duration_minutes=30,
                requires_approval=False,
                requires_mfa=False,
                requires_ticket=False,
                approval_required_count=0,
                allowed_approver_roles=[],
                notify_on_grant=True,
                notify_on_expiry=True,
                session_recording_required=True,
                allowed_ip_ranges=["0.0.0.0/0"],
                allowed_time_windows=[],
                risk_level="critical",
                tags=["emergency", "break-glass"],
            ),
        ]
        for role in default_roles:
            self._roles[role.role_id] = role

    def create_role(self, name: str, description: str, permissions: List[str],
                    max_duration_minutes: int, requires_approval: bool = True,
                    requires_mfa: bool = True, requires_ticket: bool = False,
                    approval_required_count: int = 1,
                    session_recording_required: bool = False,
                    risk_level: str = "medium",
                    tags: Optional[List[str]] = None) -> PAMRoleDefinition:
        role_id = f"role-{uuid.uuid4().hex[:8]}"
        role = PAMRoleDefinition(
            role_id=role_id,
            name=name,
            description=description,
            permissions=permissions,
            max_duration_minutes=max_duration_minutes,
            requires_approval=requires_approval,
            requires_mfa=requires_mfa,
            requires_ticket=requires_ticket,
            approval_required_count=approval_required_count,
            allowed_approver_roles=["admin", "super_admin"],
            notify_on_grant=True,
            notify_on_expiry=True,
            session_recording_required=session_recording_required,
            allowed_ip_ranges=["0.0.0.0/0"],
            allowed_time_windows=[],
            risk_level=risk_level,
            tags=tags or [],
        )
        self._roles[role_id] = role
        return role

    def get_role(self, role_id: str) -> Optional[PAMRoleDefinition]:
        return self._roles.get(role_id)

    def get_role_by_name(self, name: str) -> Optional[PAMRoleDefinition]:
        for role in self._roles.values():
            if role.name.lower() == name.lower():
                return role
        return None

    def update_role(self, role_id: str, updates: Dict[str, Any]) -> Optional[PAMRoleDefinition]:
        role = self._roles.get(role_id)
        if not role:
            return None
        allowed_fields = {"name", "description", "permissions", "max_duration_minutes",
                          "requires_approval", "requires_mfa", "requires_ticket",
                          "approval_required_count", "allowed_approver_roles",
                          "notify_on_grant", "notify_on_expiry", "session_recording_required",
                          "allowed_ip_ranges", "allowed_time_windows", "risk_level", "tags"}
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(role, key, value)
        return role

    def delete_role(self, role_id: str) -> bool:
        if role_id in self._roles:
            del self._roles[role_id]
            return True
        return False

    def list_roles(self, risk_level: Optional[str] = None,
                   tag: Optional[str] = None) -> List[Dict[str, Any]]:
        roles = list(self._roles.values())
        if risk_level:
            roles = [r for r in roles if r.risk_level == risk_level]
        if tag:
            roles = [r for r in roles if tag in r.tags]
        return [r.to_dict() for r in sorted(roles, key=lambda r: r.name)]

    def has_permission(self, role_id: str, permission: str) -> bool:
        role = self._roles.get(role_id)
        if not role:
            return False
        for p in role.permissions:
            if p == "*" or p == permission:
                return True
            if p.endswith(":*") and permission.startswith(p[:-2]):
                return True
        return False


class PAMManagerExtended:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.role_manager = PAMRoleManager()
        self._requests: Dict[str, PAMAccessRequest] = {}
        self._active_grants: Dict[str, Dict[str, Any]] = {}
        self._grants_by_user: Dict[str, List[str]] = {}
        self._recordings: Dict[str, PAMSessionRecording] = {}
        self._active_recordings: Dict[str, str] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._approval_groups: Dict[str, List[str]] = {}
        self._emergency_contacts: Dict[str, List[str]] = {}
        self._scheduled_reviews: List[Dict[str, Any]] = []
        self._auto_approve_domains = config.get("auto_approve_domains", [])
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"PAMManagerExtended initialized with {len(self.role_manager.list_roles())} roles")

    async def close(self) -> None:
        self._requests.clear()
        self._active_grants.clear()
        self._recordings.clear()
        self._audit_log.clear()
        logger.info("PAMManagerExtended closed")

    def request_access_ext(self, user_id: str, user_name: str, target_role: str,
                           target_resource: str, resource_type: str,
                           duration_minutes: int, reason: str,
                           ticket_id: Optional[str] = None,
                           resource_ids: Optional[List[str]] = None,
                           mfa_verified: bool = False,
                           ip_address: Optional[str] = None,
                           is_break_glass: bool = False) -> Dict[str, Any]:
        role = self.role_manager.get_role(target_role) or self.role_manager.get_role_by_name(target_role)
        if not role:
            raise ValueError(f"Invalid role: {target_role}")
        if not role_id := (role.role_id if isinstance(role, PAMRoleDefinition) else target_role):
            role_id = target_role
        if duration_minutes > role.max_duration_minutes:
            raise ValueError(f"Duration {duration_minutes} exceeds max {role.max_duration_minutes} for role {role.name}")
        if is_break_glass and not mfa_verified:
            raise ValueError("Break glass access requires MFA verification")
        risk_score = self._calculate_risk_score(user_id, target_role, duration_minutes, ip_address)
        request_id = str(uuid.uuid4())
        now = datetime.utcnow()
        if is_break_glass:
            status = "approved"
            approvals_required = 0
            approvals_received = 0
            approvers = []
            self._audit_log.append({
                "type": "break_glass_activated",
                "user_id": user_id,
                "user_name": user_name,
                "role": role.name,
                "resource": target_resource,
                "timestamp": now.isoformat(),
                "request_id": request_id,
                "ip_address": ip_address,
            })
            logger.warning(f"BREAK GLASS activated by {user_name} ({user_id}) for {target_role}")
        elif role.requires_approval:
            status = "pending_approval"
            approvals_required = role.approval_required_count
            approvals_received = 0
            approvers = self._get_potential_approvers(user_id, role)
        else:
            status = "approved"
            approvals_required = 0
            approvals_received = 0
            approvers = []
        request = PAMAccessRequest(
            request_id=request_id,
            user_id=user_id,
            user_name=user_name,
            target_role=target_role,
            target_resource=target_resource,
            resource_type=resource_type,
            duration_minutes=duration_minutes,
            reason=reason,
            ticket_id=ticket_id,
            status=status,
            approvers=approvers,
            approvals_required=approvals_required,
            approvals_received=approvals_received,
            approver_id=None,
            approved_at=now if status == "approved" else None,
            expires_at=now + timedelta(minutes=duration_minutes) if status == "approved" else None,
            created_at=now,
            is_break_glass=is_break_glass,
            justification=None,
            mfa_verified=mfa_verified,
            ip_address=ip_address,
            risk_score=risk_score,
            session_recording_id=None,
            resource_ids=resource_ids or [],
            reviewed_by=None,
            reviewed_at=None,
            denial_reason=None,
        )
        self._requests[request_id] = request
        if status == "approved":
            self._grant_access(user_id, user_name, target_role, request_id, duration_minutes,
                               session_recording=role.session_recording_required)
        logger.info(f"Access request {request_id} created for {user_name} role={role.name} status={status}")
        return request.to_dict()

    def _calculate_risk_score(self, user_id: str, role: str,
                              duration: int, ip_address: Optional[str]) -> float:
        score = 0.0
        high_risk_roles = ["super_admin", "break_glass", "admin"]
        if any(r in role.lower() for r in high_risk_roles):
            score += 0.3
        if duration > 120:
            score += 0.2
        elif duration > 60:
            score += 0.1
        if ip_address and (ip_address.startswith("10.") or ip_address.startswith("192.168.")):
            score -= 0.1
        return min(1.0, max(0.0, score))

    def _get_potential_approvers(self, user_id: str, role: PAMRoleDefinition) -> List[Dict[str, Any]]:
        approvers = []
        for group_name, members in self._approval_groups.items():
            if user_id not in members:
                for member_id in members:
                    approvers.append({
                        "approver_id": member_id,
                        "group": group_name,
                        "status": "pending",
                        "responded_at": None,
                    })
                    if len(approvers) >= 5:
                        break
        return approvers[:5]

    def approve_request_ext(self, request_id: str, approver_id: str,
                            approver_name: str = "System") -> Optional[Dict[str, Any]]:
        request = self._requests.get(request_id)
        if not request or request.status != "pending_approval":
            return None
        request.approvals_received += 1
        for approver in request.approvers:
            if approver.get("approver_id") == approver_id:
                approver["status"] = "approved"
                approver["responded_at"] = datetime.utcnow().isoformat()
                break
        if request.approvals_received >= request.approvals_required:
            request.status = "approved"
            request.approver_id = approver_id
            request.approved_at = datetime.utcnow()
            request.expires_at = datetime.utcnow() + timedelta(minutes=request.duration_minutes)
            role = self.role_manager.get_role(request.target_role) or self.role_manager.get_role_by_name(request.target_role)
            session_recording = role.session_recording_required if role else False
            self._grant_access(request.user_id, request.user_name, request.target_role,
                               request_id, request.duration_minutes, session_recording=session_recording)
            self._audit_log.append({
                "type": "access_approved",
                "request_id": request_id,
                "user_id": request.user_id,
                "approver_id": approver_id,
                "approver_name": approver_name,
                "role": request.target_role,
                "resource": request.target_resource,
                "timestamp": datetime.utcnow().isoformat(),
            })
            logger.info(f"Request {request_id} approved by {approver_name}")
        return request.to_dict()

    def deny_request_ext(self, request_id: str, approver_id: str,
                         approver_name: str = "System",
                         reason: str = "No reason provided") -> Optional[Dict[str, Any]]:
        request = self._requests.get(request_id)
        if not request or request.status != "pending_approval":
            return None
        request.status = "denied"
        request.approver_id = approver_id
        request.denial_reason = reason
        request.reviewed_by = approver_id
        request.reviewed_at = datetime.utcnow()
        for approver in request.approvers:
            if approver.get("approver_id") == approver_id:
                approver["status"] = "denied"
                approver["responded_at"] = datetime.utcnow().isoformat()
                break
        self._audit_log.append({
            "type": "access_denied",
            "request_id": request_id,
            "user_id": request.user_id,
            "user_name": request.user_name,
            "approver_id": approver_id,
            "approver_name": approver_name,
            "reason": reason,
            "role": request.target_role,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Request {request_id} denied by {approver_name}: {reason}")
        return request.to_dict()

    def _grant_access(self, user_id: str, user_name: str, role: str,
                      request_id: str, duration_minutes: int,
                      session_recording: bool = False) -> str:
        grant_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=duration_minutes)
        recording_id = None
        if session_recording:
            recording_id = self.start_recording(grant_id, user_id, role)
        grant = {
            "grant_id": grant_id,
            "user_id": user_id,
            "user_name": user_name,
            "role": role,
            "request_id": request_id,
            "granted_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "duration_minutes": duration_minutes,
            "remaining_minutes": duration_minutes,
            "session_recording_id": recording_id,
            "active": True,
            "extended_count": 0,
        }
        self._active_grants[grant_id] = grant
        if user_id not in self._grants_by_user:
            self._grants_by_user[user_id] = []
        self._grants_by_user[user_id].append(grant_id)
        logger.info(f"Grant {grant_id} issued to {user_name} for role {role} ({duration_minutes}min)")
        return grant_id

    def check_grant(self, user_id: str, required_permission: str) -> bool:
        now = datetime.utcnow()
        for grant_id in self._grants_by_user.get(user_id, []):
            grant = self._active_grants.get(grant_id)
            if not grant or not grant["active"]:
                continue
            expiry = datetime.fromisoformat(grant["expires_at"])
            if now > expiry:
                grant["active"] = False
                continue
            role_def = self.role_manager.get_role(grant["role"]) or self.role_manager.get_role_by_name(grant["role"])
            if role_def and self.role_manager.has_permission(role_def.role_id, required_permission):
                return True
        return False

    def extend_grant(self, grant_id: str, additional_minutes: int = 30,
                     max_extensions: int = 3) -> Optional[Dict[str, Any]]:
        grant = self._active_grants.get(grant_id)
        if not grant or not grant["active"]:
            return None
        if grant["extended_count"] >= max_extensions:
            return None
        old_expiry = datetime.fromisoformat(grant["expires_at"])
        new_expiry = old_expiry + timedelta(minutes=additional_minutes)
        grant["expires_at"] = new_expiry.isoformat()
        grant["remaining_minutes"] = int((new_expiry - datetime.utcnow()).total_seconds() / 60)
        grant["extended_count"] += 1
        logger.info(f"Grant {grant_id} extended by {additional_minutes}min")
        return grant

    def revoke_grant_ext(self, grant_id: str, reason: str = "Manual revocation") -> bool:
        grant = self._active_grants.pop(grant_id, None)
        if not grant:
            return False
        grant["active"] = False
        if grant["user_id"] in self._grants_by_user and grant_id in self._grants_by_user[grant["user_id"]]:
            self._grants_by_user[grant["user_id"]].remove(grant_id)
        if grant.get("session_recording_id"):
            self.stop_recording_by_grant(grant_id)
        self._audit_log.append({
            "type": "access_revoked",
            "grant_id": grant_id,
            "user_id": grant["user_id"],
            "user_name": grant["user_name"],
            "role": grant["role"],
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Grant {grant_id} revoked for {grant['user_name']}: {reason}")
        return True

    def get_active_grant_ext(self, user_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        for grant_id in self._grants_by_user.get(user_id, []):
            grant = self._active_grants.get(grant_id)
            if grant and grant["active"]:
                expiry = datetime.fromisoformat(grant["expires_at"])
                if now < expiry:
                    grant["remaining_minutes"] = int((expiry - now).total_seconds() / 60)
                    return grant
                else:
                    grant["active"] = False
        return None

    def list_active_grants(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self._cleanup_expired_grants()
        if user_id:
            grant_ids = self._grants_by_user.get(user_id, [])
            grants = [self._active_grants.get(gid) for gid in grant_ids if gid in self._active_grants]
        else:
            grants = list(self._active_grants.values())
        return sorted(grants, key=lambda g: g["granted_at"], reverse=True)

    def _cleanup_expired_grants(self) -> None:
        now = datetime.utcnow()
        expired = []
        for gid, grant in list(self._active_grants.items()):
            expiry = datetime.fromisoformat(grant["expires_at"])
            if now > expiry:
                grant["active"] = False
                expired.append(gid)
        for gid in expired:
            grant = self._active_grants.pop(gid, None)
            if grant and grant["user_id"] in self._grants_by_user and gid in self._grants_by_user[grant["user_id"]]:
                self._grants_by_user[grant["user_id"]].remove(gid)

    def get_pending_requests_ext(self, user_id: Optional[str] = None,
                                 approver_id: Optional[str] = None) -> List[Dict[str, Any]]:
        requests = []
        for req in self._requests.values():
            if req.status == "pending_approval":
                if user_id and req.user_id != user_id:
                    continue
                if approver_id:
                    is_approver = any(a.get("approver_id") == approver_id and a.get("status") == "pending"
                                      for a in req.approvers)
                    if not is_approver:
                        continue
                requests.append(req.to_dict())
        return sorted(requests, key=lambda r: r["created_at"], reverse=True)

    def get_request_history_ext(self, user_id: Optional[str] = None,
                                limit: int = 50, offset: int = 0,
                                status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        requests = list(self._requests.values())
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        if status_filter:
            requests = [r for r in requests if r.status == status_filter]
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return [r.to_dict() for r in requests[offset:offset + limit]]

    def start_recording(self, session_id: str, user_id: str, resource: str,
                        target_host: str = "localhost",
                        target_port: int = 22,
                        protocol: str = "ssh") -> str:
        recording_id = str(uuid.uuid4())
        recording = PAMSessionRecording(
            recording_id=recording_id,
            session_id=session_id,
            user_id=user_id,
            target_host=target_host,
            target_port=target_port,
            protocol=protocol,
            start_time=datetime.utcnow(),
            end_time=None,
            commands=[],
            keystrokes=[],
            file_transfers=[],
            command_count=0,
            file_path=f"/recordings/{recording_id}.cast",
            size_bytes=0,
            status="recording",
            tags=[],
            metadata={"resource": resource},
        )
        self._recordings[recording_id] = recording
        self._active_recordings[session_id] = recording_id
        return recording_id

    def record_command_ext(self, session_id: str, command: str, output: str,
                           exit_code: Optional[int] = None,
                           user_name: Optional[str] = None,
                           working_directory: Optional[str] = None,
                           duration_ms: Optional[int] = None) -> None:
        recording_id = self._active_recordings.get(session_id)
        if not recording_id:
            return
        recording = self._recordings.get(recording_id)
        if not recording:
            return
        command_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "command": command,
            "output": output[:2000],
            "exit_code": exit_code,
            "user_name": user_name,
            "working_directory": working_directory,
            "duration_ms": duration_ms,
        }
        recording.commands.append(command_entry)
        recording.command_count += 1
        recording.size_bytes += len(command) + min(len(output), 2000)

    def record_keystroke(self, session_id: str, key: str, timestamp: Optional[str] = None) -> None:
        recording_id = self._active_recordings.get(session_id)
        if not recording_id:
            return
        recording = self._recordings.get(recording_id)
        if not recording:
            return
        recording.keystrokes.append({
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "key": key,
        })
        if len(recording.keystrokes) > 100000:
            recording.keystrokes = recording.keystrokes[-50000:]

    def record_file_transfer(self, session_id: str, file_name: str,
                             file_size: int, direction: str,
                             destination: str) -> None:
        recording_id = self._active_recordings.get(session_id)
        if not recording_id:
            return
        recording = self._recordings.get(recording_id)
        if not recording:
            return
        recording.file_transfers.append({
            "timestamp": datetime.utcnow().isoformat(),
            "file_name": file_name,
            "file_size": file_size,
            "direction": direction,
            "destination": destination,
        })

    def stop_recording(self, session_id: str) -> Optional[str]:
        recording_id = self._active_recordings.pop(session_id, None)
        if not recording_id:
            return None
        recording = self._recordings.get(recording_id)
        if recording:
            recording.end_time = datetime.utcnow()
            recording.status = "completed"
        return recording_id

    def stop_recording_by_grant(self, grant_id: str) -> Optional[str]:
        recording_id = self._active_recordings.get(grant_id)
        if recording_id:
            return self.stop_recording(grant_id)
        for rid, rec in self._recordings.items():
            if rec.session_id == grant_id and rec.status == "recording":
                rec.end_time = datetime.utcnow()
                rec.status = "completed"
                return rid
        return None

    def get_recording_ext(self, recording_id: str) -> Optional[Dict[str, Any]]:
        rec = self._recordings.get(recording_id)
        return rec.to_dict() if rec else None

    def search_recordings_ext(self, query: str, user_id: Optional[str] = None,
                               target_host: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for rec in self._recordings.values():
            if user_id and rec.user_id != user_id:
                continue
            if target_host and rec.target_host != target_host:
                continue
            for cmd in rec.commands:
                if query.lower() in cmd.get("command", "").lower() or query.lower() in cmd.get("output", "").lower():
                    results.append({
                        "recording_id": rec.recording_id,
                        "session_id": rec.session_id,
                        "user_id": rec.user_id,
                        "timestamp": cmd["timestamp"],
                        "command": cmd["command"],
                        "output": cmd.get("output", "")[:500],
                        "exit_code": cmd.get("exit_code"),
                    })
                    break
        return sorted(results, key=lambda r: r["timestamp"], reverse=True)[:100]

    def set_approval_group(self, group_name: str, member_ids: List[str]) -> None:
        self._approval_groups[group_name] = member_ids

    def get_approval_groups(self) -> Dict[str, List[str]]:
        return dict(self._approval_groups)

    def add_emergency_contact(self, user_id: str, contact_user_id: str) -> None:
        if user_id not in self._emergency_contacts:
            self._emergency_contacts[user_id] = []
        if contact_user_id not in self._emergency_contacts[user_id]:
            self._emergency_contacts[user_id].append(contact_user_id)

    def get_emergency_contacts(self, user_id: str) -> List[str]:
        return self._emergency_contacts.get(user_id, [])

    def schedule_review(self, grant_id: str, reviewer_id: str,
                        scheduled_date: str, reason: str = "Scheduled access review") -> Dict[str, Any]:
        review = {
            "review_id": str(uuid.uuid4()),
            "grant_id": grant_id,
            "reviewer_id": reviewer_id,
            "scheduled_date": scheduled_date,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "findings": None,
        }
        self._scheduled_reviews.append(review)
        return review

    def get_scheduled_reviews(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        reviews = self._scheduled_reviews
        if status:
            reviews = [r for r in reviews if r["status"] == status]
        return sorted(reviews, key=lambda r: r["scheduled_date"])

    def complete_review(self, review_id: str, findings: str, status: str = "completed") -> bool:
        for review in self._scheduled_reviews:
            if review["review_id"] == review_id:
                review["status"] = status
                review["completed_at"] = datetime.utcnow().isoformat()
                review["findings"] = findings
                return True
        return False

    def get_audit_log_ext(self, limit: int = 100, offset: int = 0,
                          type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        entries = self._audit_log
        if type_filter:
            entries = [e for e in entries if e["type"] == type_filter]
        return entries[offset:offset + limit]

    def get_statistics_ext(self) -> Dict[str, Any]:
        total = len(self._requests)
        approved = sum(1 for r in self._requests.values() if r.status == "approved")
        denied = sum(1 for r in self._requests.values() if r.status == "denied")
        pending = sum(1 for r in self._requests.values() if r.status == "pending_approval")
        expired = sum(1 for r in self._requests.values() if r.status == "expired")
        active_grants = len(self._active_grants)
        total_recordings = len(self._recordings)
        active_recordings = len(self._active_recordings)
        total_commands = sum(r.command_count for r in self._recordings.values())
        avg_duration = round(
            sum(r.duration_minutes for r in self._requests.values()) / total, 1
        ) if total > 0 else 0
        break_glass_count = sum(1 for r in self._requests.values() if r.is_break_glass)
        return {
            "total_requests": total,
            "approved": approved,
            "denied": denied,
            "pending": pending,
            "expired": expired,
            "active_grants": active_grants,
            "total_recordings": total_recordings,
            "active_recordings": active_recordings,
            "total_commands_recorded": total_commands,
            "avg_duration_minutes": avg_duration,
            "break_glass_events": break_glass_count,
            "approval_groups": len(self._approval_groups),
            "scheduled_reviews": len(self._scheduled_reviews),
            "total_roles": len(self.role_manager.list_roles()),
        }
