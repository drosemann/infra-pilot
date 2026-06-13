"""Support ticket system with SLA management, assignment rules, and canned responses."""

import json
import logging
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketChannel(str, Enum):
    EMAIL = "email"
    WEB = "web"
    PORTAL = "portal"
    API = "api"
    CHAT = "chat"
    PHONE = "phone"
    SOCIAL = "social"


@dataclass
class SLADefinition:
    sla_id: str
    name: str
    priority: TicketPriority
    response_time_minutes: int
    resolution_time_minutes: int
    business_hours_only: bool = True
    escalation_after_minutes: Optional[int] = None
    notification_channels: List[str] = field(default_factory=lambda: ["email", "in_app"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TicketAttachment:
    attachment_id: str
    filename: str
    content_type: str
    size_bytes: int
    url: str
    uploaded_by: str
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TicketComment:
    comment_id: str
    ticket_id: str
    author_id: str
    author_name: str
    body: str
    is_internal: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    edited_at: Optional[str] = None
    attachments: List[TicketAttachment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "ticket_id": self.ticket_id,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "body": self.body,
            "is_internal": self.is_internal,
            "created_at": self.created_at,
            "edited_at": self.edited_at,
            "attachments": [a.to_dict() for a in self.attachments],
        }


@dataclass
class Ticket:
    ticket_id: str
    subject: str
    description: str
    customer_id: str
    customer_name: str
    customer_email: str
    priority: TicketPriority
    status: TicketStatus
    channel: TicketChannel
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    sla_id: Optional[str] = None
    sla_deadline: Optional[str] = None
    sla_breached: bool = False
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    related_ticket_ids: List[str] = field(default_factory=list)
    satisfaction_rating: Optional[int] = None
    satisfaction_comment: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    first_response_at: Optional[str] = None
    response_count: int = 0
    comments: List[TicketComment] = field(default_factory=list)
    attachments: List[TicketAttachment] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "subject": self.subject,
            "description": self.description,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "priority": self.priority.value,
            "status": self.status.value,
            "channel": self.channel.value,
            "assigned_to": self.assigned_to,
            "assigned_team": self.assigned_team,
            "sla_id": self.sla_id,
            "sla_deadline": self.sla_deadline,
            "sla_breached": self.sla_breached,
            "tags": self.tags,
            "category": self.category,
            "related_ticket_ids": self.related_ticket_ids,
            "satisfaction_rating": self.satisfaction_rating,
            "satisfaction_comment": self.satisfaction_comment,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "closed_at": self.closed_at,
            "first_response_at": self.first_response_at,
            "response_count": self.response_count,
            "comment_count": len(self.comments),
            "attachment_count": len(self.attachments),
            "custom_fields": self.custom_fields,
        }


@dataclass
class CannedResponse:
    response_id: str
    title: str
    body: str
    category: str
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AssignmentRule:
    def __init__(
        self, rule_id: str, name: str, conditions: Dict[str, Any],
        team: str, priority: int = 0, enabled: bool = True,
    ):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.team = team
        self.priority = priority
        self.enabled = enabled

    def matches(self, ticket: Ticket) -> bool:
        if not self.enabled:
            return False
        for key, value in self.conditions.items():
            if key == "priority" and ticket.priority.value != value:
                return False
            if key == "category" and ticket.category != value:
                return False
            if key == "customer_tier" and ticket.custom_fields.get("tier") != value:
                return False
            if key == "tag" and value not in ticket.tags:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "conditions": self.conditions,
            "team": self.team,
            "priority": self.priority,
            "enabled": self.enabled,
        }


class TicketingService:
    def __init__(self, storage_path: str = "ticketing_data.json"):
        self.storage_path = storage_path
        self.tickets: Dict[str, Ticket] = {}
        self.slas: Dict[str, SLADefinition] = {}
        self.canned_responses: Dict[str, CannedResponse] = {}
        self.assignment_rules: List[AssignmentRule] = []
        self.teams: Dict[str, List[str]] = defaultdict(list)
        self._init_default_slas()
        self._init_canned_responses()
        self._load_data()

    def _init_default_slas(self):
        defaults = [
            SLADefinition("sla-critical", "Critical Priority SLA", TicketPriority.CRITICAL, 15, 60, escalation_after_minutes=30),
            SLADefinition("sla-high", "High Priority SLA", TicketPriority.HIGH, 30, 240, escalation_after_minutes=120),
            SLADefinition("sla-medium", "Medium Priority SLA", TicketPriority.MEDIUM, 120, 480),
            SLADefinition("sla-low", "Low Priority SLA", TicketPriority.LOW, 480, 2880),
        ]
        for sla in defaults:
            self.slas[sla.sla_id] = sla

    def _init_canned_responses(self):
        responses = [
            CannedResponse("cr-001", "Greeting & Acknowledge", "Hello {customer_name},\n\nThank you for reaching out. We have received your request and will get back to you shortly.\n\nBest regards,\n{agent_name}", "general"),
            CannedResponse("cr-002", "Request More Info", "Hi {customer_name},\n\nCould you please provide additional details about this issue? Specifically:\n\n{questions}\n\nThis will help us investigate more quickly.\n\nBest regards,\n{agent_name}", "troubleshooting"),
            CannedResponse("cr-003", "Issue Resolved", "Hi {customer_name},\n\nWe believe this issue has been resolved. Please let us know if everything is working correctly.\n\nBest regards,\n{agent_name}", "resolution"),
            CannedResponse("cr-004", "Apology & Escalation", "Dear {customer_name},\n\nWe sincerely apologize for the inconvenience. I have escalated this to our senior team for priority handling.\n\nBest regards,\n{agent_name}", "escalation"),
            CannedResponse("cr-005", "Follow-up Check", "Hi {customer_name},\n\nJust checking in — has the issue been resolved on your end? Please don't hesitate to reach out if you need further assistance.\n\nBest regards,\n{agent_name}", "follow_up"),
        ]
        for cr in responses:
            self.canned_responses[cr.response_id] = cr

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for tdata in data.get("tickets", []):
                        ticket = self._dict_to_ticket(tdata)
                        self.tickets[ticket.ticket_id] = ticket
                    for sla_data in data.get("slas", []):
                        sla = SLADefinition(**sla_data)
                        self.slas[sla.sla_id] = sla
                    for cr_data in data.get("canned_responses", []):
                        cr = CannedResponse(**cr_data)
                        self.canned_responses[cr.response_id] = cr
                    for rule_data in data.get("assignment_rules", []):
                        rule = AssignmentRule(**rule_data)
                        self.assignment_rules.append(rule)
                    self.teams = defaultdict(list, data.get("teams", {}))
            except Exception as e:
                logger.warning(f"Failed to load ticketing data: {e}")

    def _save_data(self):
        try:
            data = {
                "tickets": [t.to_dict() for t in self.tickets.values()],
                "slas": [s.to_dict() for s in self.slas.values()],
                "canned_responses": [cr.to_dict() for cr in self.canned_responses.values()],
                "assignment_rules": [r.to_dict() for r in self.assignment_rules],
                "teams": dict(self.teams),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ticketing data: {e}")

    def _dict_to_ticket(self, data: Dict[str, Any]) -> Ticket:
        ticket = Ticket(
            ticket_id=data["ticket_id"],
            subject=data["subject"],
            description=data["description"],
            customer_id=data["customer_id"],
            customer_name=data.get("customer_name", ""),
            customer_email=data.get("customer_email", ""),
            priority=TicketPriority(data.get("priority", "medium")),
            status=TicketStatus(data.get("status", "new")),
            channel=TicketChannel(data.get("channel", "web")),
            assigned_to=data.get("assigned_to"),
            assigned_team=data.get("assigned_team"),
            sla_id=data.get("sla_id"),
            sla_deadline=data.get("sla_deadline"),
            sla_breached=data.get("sla_breached", False),
            tags=data.get("tags", []),
            category=data.get("category"),
            related_ticket_ids=data.get("related_ticket_ids", []),
            satisfaction_rating=data.get("satisfaction_rating"),
            satisfaction_comment=data.get("satisfaction_comment"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            resolved_at=data.get("resolved_at"),
            closed_at=data.get("closed_at"),
            first_response_at=data.get("first_response_at"),
            response_count=data.get("response_count", 0),
            custom_fields=data.get("custom_fields", {}),
        )
        for cdata in data.get("comments", []):
            ticket.comments.append(TicketComment(**cdata))
        for adata in data.get("attachments", []):
            ticket.attachments.append(TicketAttachment(**adata))
        return ticket

    def _calculate_sla_deadline(self, sla_id: str) -> Optional[str]:
        sla = self.slas.get(sla_id)
        if not sla:
            return None
        now = datetime.utcnow()
        if sla.business_hours_only:
            deadline = now + timedelta(minutes=sla.resolution_time_minutes * 2)
        else:
            deadline = now + timedelta(minutes=sla.resolution_time_minutes)
        return deadline.isoformat()

    def _auto_assign(self, ticket: Ticket) -> Tuple[Optional[str], Optional[str]]:
        sorted_rules = sorted(self.assignment_rules, key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            if rule.matches(ticket):
                team = rule.team
                members = self.teams.get(team, [])
                if members:
                    assigned = members[len(self.tickets) % len(members)]
                    return assigned, team
                return None, team
        return None, None

    def create_ticket(
        self,
        subject: str,
        description: str,
        customer_id: str,
        customer_name: str = "",
        customer_email: str = "",
        priority: str = "medium",
        channel: str = "web",
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        priority_enum = TicketPriority(priority)
        sla_id = self._select_sla(priority_enum)
        sla_deadline = self._calculate_sla_deadline(sla_id) if sla_id else None
        ticket = Ticket(
            ticket_id=ticket_id,
            subject=subject,
            description=description,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            priority=priority_enum,
            status=TicketStatus.NEW,
            channel=TicketChannel(channel),
            sla_id=sla_id,
            sla_deadline=sla_deadline,
            tags=tags or [],
            category=category,
            custom_fields=custom_fields or {},
        )
        assigned_to, assigned_team = self._auto_assign(ticket)
        ticket.assigned_to = assigned_to
        ticket.assigned_team = assigned_team
        self.tickets[ticket_id] = ticket
        self._save_data()
        return ticket

    def _select_sla(self, priority: TicketPriority) -> Optional[str]:
        for sla_id, sla in self.slas.items():
            if sla.priority == priority:
                return sla_id
        return None

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        return self.tickets.get(ticket_id)

    def update_ticket_status(self, ticket_id: str, status: str, agent_id: Optional[str] = None) -> Optional[Ticket]:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        new_status = TicketStatus(status)
        now = datetime.utcnow().isoformat()
        if new_status == TicketStatus.IN_PROGRESS and ticket.status == TicketStatus.OPEN:
            pass
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = now
        if new_status == TicketStatus.CLOSED:
            ticket.closed_at = now
        if new_status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS) and not ticket.first_response_at:
            ticket.first_response_at = now
        ticket.status = new_status
        ticket.updated_at = now
        self._check_sla_breach(ticket)
        self._save_data()
        return ticket

    def assign_ticket(self, ticket_id: str, agent_id: str, team: Optional[str] = None) -> Optional[Ticket]:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        ticket.assigned_to = agent_id
        if team:
            ticket.assigned_team = team
        ticket.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return ticket

    def add_comment(
        self, ticket_id: str, author_id: str, author_name: str,
        body: str, is_internal: bool = False,
    ) -> Optional[TicketComment]:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        comment = TicketComment(
            comment_id=f"CMT-{uuid.uuid4().hex[:8].upper()}",
            ticket_id=ticket_id,
            author_id=author_id,
            author_name=author_name,
            body=body,
            is_internal=is_internal,
        )
        ticket.comments.append(comment)
        ticket.response_count += 1
        ticket.updated_at = datetime.utcnow().isoformat()
        if not ticket.first_response_at and not is_internal:
            ticket.first_response_at = ticket.updated_at
        self._save_data()
        return comment

    def _check_sla_breach(self, ticket: Ticket):
        if ticket.sla_deadline and ticket.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            deadline = datetime.fromisoformat(ticket.sla_deadline)
            if datetime.utcnow() > deadline:
                ticket.sla_breached = True

    def set_satisfaction(self, ticket_id: str, rating: int, comment: Optional[str] = None) -> Optional[Ticket]:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        ticket.satisfaction_rating = max(1, min(5, rating))
        ticket.satisfaction_comment = comment
        self._save_data()
        return ticket

    def list_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        team: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        results = list(self.tickets.values())
        if status:
            results = [t for t in results if t.status.value == status]
        if priority:
            results = [t for t in results if t.priority.value == priority]
        if customer_id:
            results = [t for t in results if t.customer_id == customer_id]
        if assigned_to:
            results = [t for t in results if t.assigned_to == assigned_to]
        if team:
            results = [t for t in results if t.assigned_team == team]
        if search:
            search_lower = search.lower()
            results = [
                t for t in results
                if search_lower in t.subject.lower()
                or search_lower in t.description.lower()
                or search_lower in t.ticket_id.lower()
            ]
        total = len(results)
        results.sort(key=lambda t: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(t.priority.value, 99),
            t.created_at,
        ))
        page = results[offset:offset + limit]
        return [t.to_dict() for t in page], total

    def create_sla(self, name: str, priority: str, response_time: int, resolution_time: int, business_hours: bool = True) -> SLADefinition:
        sla_id = f"SLA-{uuid.uuid4().hex[:6].upper()}"
        sla = SLADefinition(
            sla_id=sla_id, name=name, priority=TicketPriority(priority),
            response_time_minutes=response_time,
            resolution_time_minutes=resolution_time,
            business_hours_only=business_hours,
        )
        self.slas[sla_id] = sla
        self._save_data()
        return sla

    def list_slas(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.slas.values()]

    def create_canned_response(self, title: str, body: str, category: str, tags: Optional[List[str]] = None, created_by: str = "") -> CannedResponse:
        cr_id = f"CR-{uuid.uuid4().hex[:6].upper()}"
        cr = CannedResponse(
            response_id=cr_id, title=title, body=body,
            category=category, tags=tags or [], created_by=created_by,
        )
        self.canned_responses[cr_id] = cr
        self._save_data()
        return cr

    def list_canned_responses(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.canned_responses.values())
        if category:
            results = [cr for cr in results if cr.category == category]
        return [cr.to_dict() for cr in results]

    def add_assignment_rule(self, name: str, conditions: Dict[str, Any], team: str, priority: int = 0) -> AssignmentRule:
        rule_id = f"RULE-{uuid.uuid4().hex[:6].upper()}"
        rule = AssignmentRule(rule_id, name, conditions, team, priority)
        self.assignment_rules.append(rule)
        self._save_data()
        return rule

    def list_assignment_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.assignment_rules]

    def add_team_member(self, team: str, agent_id: str):
        self.teams[team].append(agent_id)
        self._save_data()

    def get_ticket_stats(self) -> Dict[str, Any]:
        total = len(self.tickets)
        by_status = defaultdict(int)
        by_priority = defaultdict(int)
        breached = 0
        for t in self.tickets.values():
            by_status[t.status.value] += 1
            by_priority[t.priority.value] += 1
            if t.sla_breached:
                breached += 1
        resolved = [t for t in self.tickets.values() if t.resolved_at]
        avg_resolution_hours = 0
        if resolved:
            times = []
            for t in resolved:
                created = datetime.fromisoformat(t.created_at)
                resolved_time = datetime.fromisoformat(t.resolved_at)
                times.append((resolved_time - created).total_seconds() / 3600)
            avg_resolution_hours = sum(times) / len(times) if times else 0
        ratings = [t.satisfaction_rating for t in self.tickets.values() if t.satisfaction_rating]
        avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0
        return {
            "total_tickets": total,
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "open_tickets": by_status.get("open", 0) + by_status.get("new", 0) + by_status.get("in_progress", 0),
            "sla_breaches": breached,
            "avg_resolution_time_hours": round(avg_resolution_hours, 1),
            "avg_satisfaction": round(avg_satisfaction, 1),
        }

    def get_customer_tickets(self, customer_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        tickets = [t for t in self.tickets.values() if t.customer_id == customer_id]
        tickets.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tickets[:limit]]

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        return t.to_dict() if t else None

    def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        t = self.tickets.get(ticket_id)
        if not t: return False
        if "subject" in updates: t.subject = updates["subject"]
        if "description" in updates: t.description = updates["description"]
        if "priority" in updates: t.priority = TicketPriority(updates["priority"]) if isinstance(updates["priority"], str) else updates["priority"]
        if "status" in updates: t.status = TicketStatus(updates["status"]) if isinstance(updates["status"], str) else updates["status"]
        if "assigned_to" in updates: t.assigned_to = updates["assigned_to"]
        if "tags" in updates: t.tags = updates["tags"]
        t.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def delete_ticket(self, ticket_id: str) -> bool:
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            self._save_data()
            return True
        return False

    def add_comment(self, ticket_id: str, author: str, content: str, internal: bool = False) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t: return None
        comment = TicketComment(comment_id=str(uuid.uuid4())[:8], ticket_id=ticket_id, author=author, content=content, internal=internal)
        t.comments.append(comment)
        t.updated_at = datetime.utcnow()
        self._save_data()
        return {"comment_id": comment.comment_id, "author": author, "content": content, "internal": internal, "created_at": comment.created_at.isoformat()}

    def assign_ticket(self, ticket_id: str, assignee: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t: return False
        t.assigned_to = assignee
        t.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def get_sla_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t: return None
        sla = t.sla_breach_at
        if not sla: return {"ticket_id": ticket_id, "sla_breach_at": None, "status": "no_sla"}
        remaining = (sla - datetime.utcnow()).total_seconds()
        breached = remaining <= 0
        return {"ticket_id": ticket_id, "sla_breach_at": sla.isoformat(), "remaining_seconds": max(0, int(remaining)), "breached": breached, "status": "breached" if breached else "within_sla"}

    def get_unassigned_tickets(self) -> List[Dict[str, Any]]:
        unassigned = [t for t in self.tickets.values() if not t.assigned_to and t.status != TicketStatus.CLOSED]
        unassigned.sort(key=lambda t: t.priority.value)
        return [t.to_dict() for t in unassigned]

    def get_overdue_tickets(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        overdue = [t for t in self.tickets.values() if t.sla_breach_at and t.sla_breach_at < now and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
        overdue.sort(key=lambda t: t.sla_breach_at)
        return [t.to_dict() for t in overdue]

    def get_ticket_stats(self) -> Dict[str, Any]:
        total = len(self.tickets)
        by_status = defaultdict(int)
        by_priority = defaultdict(int)
        breached = 0
        now = datetime.utcnow()
        for t in self.tickets.values():
            by_status[t.status.value] += 1
            by_priority[t.priority.value] += 1
            if t.sla_breach_at and t.sla_breach_at < now and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                breached += 1
        return {"total_tickets": total, "by_status": dict(by_status), "by_priority": dict(by_priority), "breached_sla": breached, "unassigned": len([t for t in self.tickets.values() if not t.assigned_to])}

    def search_tickets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [t.to_dict() for t in self.tickets.values() if q in t.subject.lower() or q in t.description.lower() or any(q in tag.lower() for tag in t.tags)]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]

    def merge_tickets(self, ticket_ids: List[str], target_id: str) -> bool:
        target = self.tickets.get(target_id)
        if not target or not ticket_ids: return False
        for tid in ticket_ids:
            if tid == target_id: continue
            t = self.tickets.get(tid)
            if not t: continue
            for comment in t.comments:
                target.comments.append(comment)
            if t.priority.value > target.priority.value:
                target.priority = t.priority
            del self.tickets[tid]
        target.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def bulk_update_status(self, ticket_ids: List[str], status: str) -> int:
        new_status = TicketStatus(status) if isinstance(status, str) else status
        count = 0
        for tid in ticket_ids:
            t = self.tickets.get(tid)
            if t:
                t.status = new_status
                t.updated_at = datetime.utcnow()
                count += 1
        if count > 0:
            self._save_data()
        return count

    def get_tickets_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.tickets.values() if tag.lower() in [tg.lower() for tg in t.tags]]

    def get_canned_responses(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        responses = list(self.canned_responses.values())
        if category:
            responses = [r for r in responses if r.category == category]
        return [{"id": r.response_id, "title": r.title, "content": r.content, "category": r.category} for r in responses]

    def create_canned_response(self, title: str, content: str, category: str = "general") -> Dict[str, Any]:
        rid = str(uuid.uuid4())[:8]
        cr = CannedResponse(response_id=rid, title=title, content=content, category=category)
        self.canned_responses[rid] = cr
        self._save_data()
        return {"response_id": rid, "title": title, "category": category}

    def get_escalation_matrix(self) -> Dict[str, Any]:
        return {"levels": [{"level": 1, "description": "First-line support", "max_priority": "medium"}, {"level": 2, "description": "Technical team", "max_priority": "high"}, {"level": 3, "description": "Engineering lead", "max_priority": "critical"}], "sla_targets": {"critical": 60, "high": 240, "medium": 1440, "low": 4320}}

    def export_tickets(self, format: str = "json") -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "tickets": [t.to_dict() for t in self.tickets.values()], "stats": self.get_ticket_stats(), "format": format}

    def get_customer_satisfaction(self, customer_id: str) -> Dict[str, Any]:
        tickets = [t for t in self.tickets.values() if t.customer_id == customer_id and t.satisfaction_score is not None]
        if not tickets: return {"customer_id": customer_id, "avg_satisfaction": None, "rated_tickets": 0}
        scores = [t.satisfaction_score for t in tickets]
        return {"customer_id": customer_id, "avg_satisfaction": round(sum(scores) / len(scores), 1), "rated_tickets": len(scores), "max_score": max(scores), "min_score": min(scores)}

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        return t.to_dict() if t else None

    def reopen_ticket(self, ticket_id: str, reason: str = "") -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t or t.status != TicketStatus.CLOSED:
            return None
        t.status = TicketStatus.OPEN
        t.updated_at = datetime.utcnow().isoformat()
        t.metadata["reopened"] = True
        t.metadata["reopen_reason"] = reason
        t.metadata["reopened_at"] = datetime.utcnow().isoformat()
        self._save_data()
        return t.to_dict()

    def bulk_assign(self, ticket_ids: List[str], assignee: str, team: Optional[str] = None) -> int:
        count = 0
        for tid in ticket_ids:
            t = self.tickets.get(tid)
            if t:
                t.assigned_to = assignee
                if team:
                    t.assigned_team = team
                t.updated_at = datetime.utcnow().isoformat()
                count += 1
        if count:
            self._save_data()
        return count

    def get_tickets_by_customer(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        results = [t.to_dict() for t in self.tickets.values() if t.customer_id == customer_id]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]

    def get_tickets_by_assignee(self, assignee: str, limit: int = 50) -> List[Dict[str, Any]]:
        results = [t.to_dict() for t in self.tickets.values() if t.assigned_to == assignee]
        results.sort(key=lambda x: (0 if x.get("priority") == "critical" else 1 if x.get("priority") == "high" else 2, x.get("created_at", "")))
        return results[:limit]

    def get_sla_breach_report(self) -> Dict[str, Any]:
        breached = [t for t in self.tickets.values() if t.sla_breached]
        at_risk = [t for t in self.tickets.values() if t.sla_deadline and not t.sla_breached and datetime.fromisoformat(t.sla_deadline) > datetime.utcnow()]
        return {
            "total_breached": len(breached),
            "total_at_risk": len(at_risk),
            "breach_rate": round(len(breached) / max(len(self.tickets), 1), 3),
            "breached_tickets": [t.to_dict() for t in breached[:20]],
            "at_risk_tickets": [t.to_dict() for t in at_risk[:20]],
        }

    def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        tag_lower = tag.lower()
        results = [t.to_dict() for t in self.tickets.values() if any(tag_lower == tg.lower() for tg in t.tags)]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def get_ticket_volume_forecast(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [t for t in self.tickets.values() if t.created_at >= cutoff]
        daily_counts = defaultdict(int)
        for t in recent:
            day = t.created_at[:10]
            daily_counts[day] += 1
        values = list(daily_counts.values())
        avg = sum(values) / max(len(values), 1)
        return {
            "period_days": days,
            "total_tickets": len(recent),
            "daily_average": round(avg, 1),
            "peak_day": max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else ("", 0),
            "daily_breakdown": dict(sorted(daily_counts.items())),
        }

    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        assigned = [t for t in self.tickets.values() if t.assigned_to == agent_id]
        resolved = [t for t in assigned if t.resolved_at]
        avg_resolution = 0
        if resolved:
            times = [(datetime.fromisoformat(t.resolved_at) - datetime.fromisoformat(t.created_at)).total_seconds() / 3600 for t in resolved]
            avg_resolution = sum(times) / len(times)
        return {
            "agent_id": agent_id,
            "total_assigned": len(assigned),
            "total_resolved": len(resolved),
            "resolution_rate": round(len(resolved) / max(len(assigned), 1), 3),
            "avg_resolution_hours": round(avg_resolution, 1),
            "avg_satisfaction": round(sum(t.satisfaction_rating or 0 for t in resolved) / max(len(resolved), 1), 1),
            "current_open": len([t for t in assigned if t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]),
        }

    def merge_customers(self, source_customer_id: str, target_customer_id: str) -> int:
        count = 0
        for t in self.tickets.values():
            if t.customer_id == source_customer_id:
                t.customer_id = target_customer_id
                count += 1
            if t.customer_id == source_customer_id:
                t.customer_id = target_customer_id
                for c in t.comments:
                    c.customer_id = target_customer_id
                count += 1
        if count:
            self._save_data()
        return count

    def get_escalation_path(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t:
            return None
        return {
            "ticket_id": ticket_id,
            "priority": t.priority.value,
            "current_assignee": t.assigned_to,
            "current_team": t.assigned_team,
            "sla_status": "breached" if t.sla_breached else ("at_risk" if t.sla_deadline else "no_sla"),
            "escalation_level": 1 if t.priority == TicketPriority.LOW else 2 if t.priority == TicketPriority.MEDIUM else 3 if t.priority == TicketPriority.HIGH else 4,
            "escalation_contact": self._get_escalation_contact(t.priority),
        }

    def _get_escalation_contact(self, priority: TicketPriority) -> str:
        contacts = {
            TicketPriority.CRITICAL: "Engineering On-Call + VP Engineering",
            TicketPriority.HIGH: "Senior Support Manager",
            TicketPriority.MEDIUM: "Team Lead",
            TicketPriority.LOW: "Support Agent",
        }
        return contacts.get(priority, "Support Team")

    def get_category_breakdown(self) -> Dict[str, int]:
        breakdown = defaultdict(int)
        for t in self.tickets.values():
            breakdown[t.category or "uncategorized"] += 1
        return dict(breakdown)

    def get_channel_breakdown(self) -> Dict[str, int]:
        breakdown = defaultdict(int)
        for t in self.tickets.values():
            breakdown[t.channel.value] += 1
        return dict(breakdown)

    def apply_canned_response(self, ticket_id: str, response_id: str, agent_name: str, customer_name: str) -> Optional[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        cr = self.canned_responses.get(response_id)
        if not t or not cr:
            return None
        rendered = cr.body.replace("{customer_name}", customer_name).replace("{agent_name}", agent_name)
        comment = self.add_comment(ticket_id=ticket_id, author_id="system", author_name=agent_name, body=rendered)
        cr.usage_count += 1
        self._save_data()
        return {"ticket_id": ticket_id, "response_id": response_id, "comment": comment.to_dict() if comment else None}

    def create_sla_policy(self, name: str, priority: str, response_time: int, resolution_time: int, business_hours: bool = True) -> Dict[str, Any]:
        sla_id = f"SLA-{uuid.uuid4().hex[:6].upper()}"
        sla = SLAPolicy(sla_id=sla_id, name=name, priority=TicketPriority(priority), response_time_minutes=response_time, resolution_time_minutes=resolution_time, business_hours_only=business_hours)
        self.slas[sla_id] = sla
        self._save_data()
        return sla.to_dict()

    def preview_canned_response(self, response_id: str, customer_name: str = "Customer", agent_name: str = "Agent") -> Optional[str]:
        cr = self.canned_responses.get(response_id)
        if not cr:
            return None
        return cr.body.replace("{customer_name}", customer_name).replace("{agent_name}", agent_name)

    def get_team_workload(self, team: str) -> Dict[str, Any]:
        members = self.teams.get(team, [])
        workload = {}
        for m in members:
            open_tickets = [t for t in self.tickets.values() if t.assigned_to == m and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
            workload[m] = {
                "open_count": len(open_tickets),
                "critical_count": sum(1 for t in open_tickets if t.priority == TicketPriority.CRITICAL),
                "high_count": sum(1 for t in open_tickets if t.priority == TicketPriority.HIGH),
            }
        return {"team": team, "members": workload, "total_members": len(members)}

    def rebalance_team(self, team: str) -> Dict[str, Any]:
        members = self.teams.get(team, [])
        if not members:
            return {"team": team, "message": "No members in team"}
        open_tickets = [t for t in self.tickets.values() if t.assigned_team == team and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
        tickets_per_member = len(open_tickets) // len(members) if members else 0
        remainder = len(open_tickets) % len(members) if members else 0
        assignments = {}
        idx = 0
        for i, m in enumerate(members):
            count = tickets_per_member + (1 if i < remainder else 0)
            assignments[m] = count
            for _ in range(count):
                if idx < len(open_tickets):
                    open_tickets[idx].assigned_to = m
                    idx += 1
        self._save_data()
        return {"team": team, "assignments": assignments, "total_reassigned": idx}

    def export_tickets_csv(self) -> str:
        lines = ["ticket_id,subject,customer_id,priority,status,channel,assigned_to,created_at,resolved_at"]
        for t in self.tickets.values():
            lines.append(f"{t.ticket_id},{t.subject},{t.customer_id},{t.priority.value},{t.status.value},{t.channel.value},{t.assigned_to or ''},{t.created_at},{t.resolved_at or ''}")
        return "\n".join(lines)

    def get_ticket_chain(self, ticket_id: str) -> List[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t:
            return []
        chain = [t.to_dict()]
        for related_id in t.related_ticket_ids:
            related = self.tickets.get(related_id)
            if related:
                chain.append(related.to_dict())
        return chain

    def link_tickets(self, ticket_id: str, related_id: str) -> bool:
        t1 = self.tickets.get(ticket_id)
        t2 = self.tickets.get(related_id)
        if not t1 or not t2:
            return False
        if related_id not in t1.related_ticket_ids:
            t1.related_ticket_ids.append(related_id)
        if ticket_id not in t2.related_ticket_ids:
            t2.related_ticket_ids.append(ticket_id)
        t1.updated_at = datetime.utcnow().isoformat()
        t2.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def add_ticket_tag(self, ticket_id: str, tag: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t:
            return False
        if tag not in t.tags:
            t.tags.append(tag)
            t.updated_at = datetime.utcnow().isoformat()
            self._save_data()
        return True

    def remove_ticket_tag(self, ticket_id: str, tag: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t:
            return False
        if tag in t.tags:
            t.tags = [tg for tg in t.tags if tg != tag]
            t.updated_at = datetime.utcnow().isoformat()
            self._save_data()
        return True

    def get_ticket_audit_log(self, ticket_id: str) -> List[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t:
            return []
        log = []
        log.append({"action": "created", "timestamp": t.created_at, "actor": t.customer_id})
        if t.first_response_at:
            log.append({"action": "first_response", "timestamp": t.first_response_at})
        if t.resolved_at:
            log.append({"action": "resolved", "timestamp": t.resolved_at, "actor": t.assigned_to})
        if t.closed_at:
            log.append({"action": "closed", "timestamp": t.closed_at})
        for c in t.comments:
            log.append({"action": "comment_added", "timestamp": c.created_at, "actor": c.author_id, "internal": c.is_internal})
        return log

    def get_ticket_dependencies(self, ticket_id: str) -> List[Dict[str, Any]]:
        t = self.tickets.get(ticket_id)
        if not t:
            return []
        deps = []
        for dep_id in t.metadata.get("depends_on", []):
            dep = self.tickets.get(dep_id)
            if dep:
                deps.append({"ticket_id": dep_id, "subject": dep.subject, "status": dep.status.value, "priority": dep.priority.value})
        for tid, other in self.tickets.items():
            if tid != ticket_id and ticket_id in other.metadata.get("depends_on", []):
                deps.append({"blocked_by": tid, "subject": other.subject, "status": other.status.value})
        return deps

    def add_dependency(self, ticket_id: str, depends_on_id: str) -> bool:
        t = self.tickets.get(ticket_id)
        dep = self.tickets.get(depends_on_id)
        if not t or not dep:
            return False
        if "depends_on" not in t.metadata:
            t.metadata["depends_on"] = []
        if depends_on_id not in t.metadata["depends_on"]:
            t.metadata["depends_on"].append(depends_on_id)
            t.updated_at = datetime.utcnow().isoformat()
            self._save_data()
        return True

    def remove_dependency(self, ticket_id: str, depends_on_id: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t or "depends_on" not in t.metadata:
            return False
        if depends_on_id in t.metadata["depends_on"]:
            t.metadata["depends_on"].remove(depends_on_id)
            t.updated_at = datetime.utcnow().isoformat()
            self._save_data()
        return True

    def get_blocked_tickets(self) -> List[Dict[str, Any]]:
        blocked = []
        for t in self.tickets.values():
            deps = t.metadata.get("depends_on", [])
            if deps:
                unresolved = [d for d in deps if (dep := self.tickets.get(d)) and dep.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
                if unresolved:
                    ticket_dict = t.to_dict()
                    ticket_dict["blocked_by"] = unresolved
                    blocked.append(ticket_dict)
        return blocked

    def get_ticket_metrics(self) -> Dict[str, Any]:
        total = len(self.tickets)
        if not total:
            return {"total": 0}
        resolved = [t for t in self.tickets.values() if t.resolved_at]
        first_response_times = []
        resolution_times = []
        for t in self.tickets.values():
            if t.first_response_at and t.created_at:
                fr = (datetime.fromisoformat(t.first_response_at) - datetime.fromisoformat(t.created_at)).total_seconds() / 60
                first_response_times.append(fr)
            if t.resolved_at and t.created_at:
                rt = (datetime.fromisoformat(t.resolved_at) - datetime.fromisoformat(t.created_at)).total_seconds() / 3600
                resolution_times.append(rt)
        return {
            "total": total,
            "open": sum(1 for t in self.tickets.values() if t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)),
            "resolved": len(resolved),
            "avg_first_response_minutes": round(sum(first_response_times) / max(len(first_response_times), 1), 1) if first_response_times else None,
            "avg_resolution_hours": round(sum(resolution_times) / max(len(resolution_times), 1), 1) if resolution_times else None,
            "sla_compliance": round(sum(1 for t in self.tickets.values() if t.sla_id and not t.sla_breached) / max(sum(1 for t in self.tickets.values() if t.sla_id), 1), 3),
            "reopened_count": sum(1 for t in self.tickets.values() if t.metadata.get("reopened")),
        }

    def get_busiest_hours(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [t for t in self.tickets.values() if t.created_at >= cutoff]
        hourly = defaultdict(int)
        for t in recent:
            hour = datetime.fromisoformat(t.created_at).hour
            hourly[f"{hour:02d}:00"] += 1
        sorted_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)
        return {
            "busiest_hour": sorted_hours[0][0] if sorted_hours else "",
            "hourly_breakdown": dict(sorted(hourly.items())),
            "quietest_hour": sorted_hours[-1][0] if sorted_hours else "",
        }

    def get_sla_compliance_report(self) -> Dict[str, Any]:
        with_sla = [t for t in self.tickets.values() if t.sla_id]
        breached = [t for t in with_sla if t.sla_breached]
        compliant = [t for t in with_sla if not t.sla_breached and t.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
        active = [t for t in with_sla if not t.sla_breached and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
        return {
            "total_with_sla": len(with_sla),
            "compliant": len(compliant),
            "breached": len(breached),
            "active_within_sla": len(active),
            "compliance_rate": round(len(compliant) / max(len(with_sla), 1), 3),
            "breach_rate": round(len(breached) / max(len(with_sla), 1), 3),
            "breaches_by_priority": dict(Counter(t.priority.value for t in breached)),
        }

    def get_ticket_templates(self) -> List[Dict[str, Any]]:
        return [
            {"id": "bug_report", "name": "Bug Report", "fields": {"subject": "", "description": "", "steps_to_reproduce": "", "expected": "", "actual": "", "environment": ""}},
            {"id": "feature_request", "name": "Feature Request", "fields": {"subject": "", "description": "", "use_case": "", "priority": "medium"}},
            {"id": "incident", "name": "Incident Report", "fields": {"subject": "", "description": "", "impact": "", "affected_services": [], "severity": "high"}},
            {"id": "billing", "name": "Billing Issue", "fields": {"subject": "", "description": "", "invoice_id": "", "amount": 0}},
        ]

    def create_from_template(self, template_id: str, customer_id: str, fields: Dict[str, Any]) -> Optional[Ticket]:
        templates = {
            "bug_report": {"priority": "high", "tags": ["bug"]},
            "feature_request": {"priority": "medium", "tags": ["feature-request"]},
            "incident": {"priority": "critical", "tags": ["incident"]},
            "billing": {"priority": "medium", "tags": ["billing"]},
        }
        tpl = templates.get(template_id)
        if not tpl:
            return None
        return self.create_ticket(
            subject=fields.get("subject", f"New {template_id}"),
            description=str(fields),
            customer_id=customer_id,
            priority=tpl["priority"],
            tags=tpl["tags"],
        )

    def get_ticket_export(self, format: str = "json") -> Dict[str, Any]:
        return self.export_tickets(format)

    def get_ticket_timeline(self, ticket_id: str) -> List[Dict[str, Any]]:
        return self.get_ticket_audit_log(ticket_id)

    def add_watcher(self, ticket_id: str, user_id: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t:
            return False
        if "watchers" not in t.metadata:
            t.metadata["watchers"] = []
        if user_id not in t.metadata["watchers"]:
            t.metadata["watchers"].append(user_id)
            self._save_data()
        return True

    def remove_watcher(self, ticket_id: str, user_id: str) -> bool:
        t = self.tickets.get(ticket_id)
        if not t:
            return False
        if "watchers" in t.metadata and user_id in t.metadata["watchers"]:
            t.metadata["watchers"].remove(user_id)
            self._save_data()
        return True

    def get_ticket_watchers(self, ticket_id: str) -> List[str]:
        t = self.tickets.get(ticket_id)
        return t.metadata.get("watchers", []) if t else []

    def get_sla_definitions(self) -> List[Dict[str, Any]]:
        return self.list_slas()

    def update_sla_definition(self, sla_id: str, updates: Dict[str, Any]) -> Optional[SLADefinition]:
        sla = self.slas.get(sla_id)
        if not sla:
            return None
        if "name" in updates:
            sla.name = updates["name"]
        if "response_time_minutes" in updates:
            sla.response_time_minutes = updates["response_time_minutes"]
        if "resolution_time_minutes" in updates:
            sla.resolution_time_minutes = updates["resolution_time_minutes"]
        if "business_hours_only" in updates:
            sla.business_hours_only = updates["business_hours_only"]
        self._save_data()
        return sla

    def delete_sla(self, sla_id: str) -> bool:
        if sla_id in self.slas:
            del self.slas[sla_id]
            self._save_data()
            return True
        return False

    def get_ticket_suggestion(self, customer_id: str) -> List[Dict[str, Any]]:
        recent = [t for t in self.tickets.values() if t.customer_id == customer_id]
        recent.sort(key=lambda t: t.created_at, reverse=True)
        if not recent:
            return []
        last_category = recent[0].category
        last_tags = recent[0].tags
        suggestions = []
        for cr in self.canned_responses.values():
            if last_category and cr.category == last_category:
                suggestions.append({"type": "canned_response", "id": cr.response_id, "title": cr.title})
        similar = [t for t in self.tickets.values() if t.category == last_category and t.ticket_id != recent[0].ticket_id and t.resolved_at]
        for t in similar[:3]:
            suggestions.append({"type": "similar_ticket", "ticket_id": t.ticket_id, "subject": t.subject})
        return suggestions

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_customers": 0, "active_users": 0, "nps_score": 0.0, "satisfaction_rate": 0.0}

    def validate_engagement(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class CXResult(BaseModel):
    success: bool = True
    operation: str = ""
    customer_id: Optional[str] = None
    interaction_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CXBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    campaign: str = Field(default="general")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    responded: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_response(self) -> None:
        self.responded += 1

    def complete(self) -> None:
        self.status = "completed"

class CustomerProfile(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    tier: str = Field(default="standard")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    total_spend: float = Field(default=0.0)
    interaction_count: int = Field(default=0)
    nps_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

class CustomerRepository:
    def __init__(self) -> None:
        self._customers: Dict[str, CustomerProfile] = {}

    def create(self, name: str, email: str, tier: str = "standard") -> CustomerProfile:
        customer = CustomerProfile(name=name, email=email, tier=tier)
        self._customers[customer.customer_id] = customer
        return customer

    def get(self, customer_id: str) -> Optional[CustomerProfile]:
        return self._customers.get(customer_id)

    def update_last_active(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if customer:
            customer.last_active = datetime.utcnow()
            customer.interaction_count += 1
            return True
        return False

    def get_by_tier(self, tier: str) -> List[CustomerProfile]:
        return [c for c in self._customers.values() if c.tier == tier]

    def get_at_risk(self, days_inactive: int = 30) -> List[CustomerProfile]:
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)
        return [c for c in self._customers.values() if c.last_active and c.last_active < cutoff]

    def get_statistics(self) -> Dict[str, Any]:
        customers = list(self._customers.values())
        return {"total": len(customers), "avg_spend": round(sum(c.total_spend for c in customers) / max(len(customers), 1), 2),
                "by_tier": {t: sum(1 for c in customers if c.tier == t) for t in set(c.tier for c in customers)},
                "at_risk": len(self.get_at_risk())}

class NPSRecord(BaseModel):
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    score: int = Field(default=0, ge=0, le=10)
    comment: str = ""
    category: str = Field(default="general")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    def is_promoter(self) -> bool:
        return self.score >= 9

    def is_passive(self) -> bool:
        return 7 <= self.score <= 8

    def is_detractor(self) -> bool:
        return self.score <= 6

class NPSTracker:
    def __init__(self) -> None:
        self._surveys: List[NPSRecord] = []

    def record(self, customer_id: str, score: int, comment: str = "", category: str = "general") -> NPSRecord:
        survey = NPSRecord(customer_id=customer_id, score=score, comment=comment, category=category)
        self._surveys.append(survey)
        return survey

    def get_score(self) -> float:
        total = len(self._surveys)
        if total == 0:
            return 0.0
        promoters = sum(1 for s in self._surveys if s.is_promoter())
        detractors = sum(1 for s in self._surveys if s.is_detractor())
        return round((promoters - detractors) / total * 100, 1)

    def get_by_category(self, category: str) -> List[NPSRecord]:
        return [s for s in self._surveys if s.category == category]

    def get_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [s for s in self._surveys if s.submitted_at >= cutoff]
        return {"period_days": days, "surveys": len(recent),
                "score": round((sum(1 for s in recent if s.is_promoter()) - sum(1 for s in recent if s.is_detractor())) / max(len(recent), 1) * 100, 1),
                "promoters": sum(1 for s in recent if s.is_promoter()),
                "passives": sum(1 for s in recent if s.is_passive()),
                "detractors": sum(1 for s in recent if s.is_detractor())}

class TicketRecord(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    subject: str
    description: str = ""
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    satisfaction_score: Optional[int] = None

class TicketSystem:
    def __init__(self) -> None:
        self._tickets: Dict[str, TicketRecord] = {}

    def create(self, customer_id: str, subject: str, description: str = "", priority: str = "medium") -> TicketRecord:
        ticket = TicketRecord(customer_id=customer_id, subject=subject, description=description, priority=priority)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve(self, ticket_id: str, satisfaction: Optional[int] = None) -> bool:
        ticket = self._tickets.get(ticket_id)
        if ticket and ticket.status == "open":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            ticket.satisfaction_score = satisfaction
            return True
        return False

    def get_open(self) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.status == "open"]

    def get_by_priority(self, priority: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_by_customer(self, customer_id: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.customer_id == customer_id]

    def get_statistics(self) -> Dict[str, Any]:
        tickets = list(self._tickets.values())
        open_tickets = self.get_open()
        resolved = [t for t in tickets if t.status == "resolved"]
        avg_resolution = 0.0
        if resolved:
            durations = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved if t.resolved_at]
            avg_resolution = round(sum(durations) / len(durations), 1) if durations else 0.0
        return {"total": len(tickets), "open": len(open_tickets), "resolved": len(resolved),
                "avg_resolution_hours": avg_resolution,
                "by_priority": {p: sum(1 for t in tickets if t.priority == p) for p in set(t.priority for t in tickets)},
                "avg_satisfaction": round(sum(t.satisfaction_score for t in resolved if t.satisfaction_score) / max(len([t for t in resolved if t.satisfaction_score]), 1), 1)}

class OnboardingStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    step_name: str
    status: str = Field(default="pending")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class OnboardingWorkflow:
    def __init__(self) -> None:
        self._steps: Dict[str, OnboardingStep] = {}

    def add_step(self, customer_id: str, step_name: str) -> OnboardingStep:
        step = OnboardingStep(customer_id=customer_id, step_name=step_name)
        self._steps[step.step_id] = step
        return step

    def start_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "pending":
            step.status = "in_progress"
            step.started_at = datetime.utcnow()
            return True
        return False

    def complete_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "in_progress":
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_minutes = int((step.completed_at - step.started_at).total_seconds() / 60) if step.started_at else 0
            return True
        return False

    def get_progress(self, customer_id: str) -> Dict[str, Any]:
        steps = [s for s in self._steps.values() if s.customer_id == customer_id]
        completed = sum(1 for s in steps if s.status == "completed")
        return {"customer_id": customer_id, "total_steps": len(steps),
                "completed": completed, "in_progress": sum(1 for s in steps if s.status == "in_progress"),
                "pending": sum(1 for s in steps if s.status == "pending"),
                "progress_pct": round(completed / max(len(steps), 1) * 100, 1)}
