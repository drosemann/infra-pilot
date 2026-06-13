"""Customer communication hub for broadcast announcements, maintenance notifications, and product updates."""

import json
import logging
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    ANNOUNCEMENT = "announcement"
    MAINTENANCE = "maintenance"
    PRODUCT_UPDATE = "product_update"
    BILLING = "billing"
    SECURITY = "security"
    SYSTEM = "system"
    PROMOTIONAL = "promotional"
    SURVEY = "survey"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ChannelType(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SLACK = "slack"
    DISCORD = "discord"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    CLICKED = "clicked"


@dataclass
class Template:
    template_id: str
    name: str
    subject: str
    body: str
    channel: ChannelType
    category: str = "general"
    variables: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def render(self, variables: Dict[str, str]) -> str:
        rendered = self.body
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return rendered


@dataclass
class NotificationBatch:
    batch_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    subject: str
    body: str
    channels: List[str]
    target_segment: str = "all"
    target_customer_ids: Optional[List[str]] = None
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = ""
    total_recipients: int = 0
    delivery_stats: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MaintenanceWindow:
    maintenance_id: str
    title: str
    description: str
    affected_services: List[str]
    start_time: str
    end_time: str
    expected_downtime_minutes: int
    status: str = "scheduled"
    notification_batch_id: Optional[str] = None
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    actual_downtime_minutes: Optional[int] = None
    post_mortem: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeliveryRecord:
    record_id: str
    batch_id: str
    customer_id: str
    channel: str
    recipient: str
    status: DeliveryStatus
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    clicked_at: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommunicationHubService:
    def __init__(self, storage_path: str = "communication_data.json"):
        self.storage_path = storage_path
        self.templates: Dict[str, Template] = {}
        self.batches: Dict[str, NotificationBatch] = {}
        self.maintenance_windows: Dict[str, MaintenanceWindow] = {}
        self.delivery_records: List[DeliveryRecord] = []
        self.customer_channels: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._init_default_templates()
        self._load_data()

    def _init_default_templates(self):
        defaults = [
            Template("tpl-announcement", "General Announcement", "Important Announcement: {{title}}", "Hello {{customer_name}},\n\n{{body}}\n\n---\nInfra Pilot Team", ChannelType.EMAIL, variables=["customer_name", "title", "body"]),
            Template("tpl-maintenance", "Maintenance Notification", "Scheduled Maintenance: {{title}}", "Hello {{customer_name}},\n\nWe will be performing scheduled maintenance on {{affected_services}}.\n\nStart: {{start_time}}\nEnd: {{end_time}}\nExpected downtime: {{downtime_minutes}} minutes\n\n{{body}}\n\n---\nInfra Pilot Team", ChannelType.EMAIL, variables=["customer_name", "title", "body", "affected_services", "start_time", "end_time", "downtime_minutes"]),
            Template("tpl-update", "Product Update", "New Update: {{title}}", "Hello {{customer_name}},\n\nWe're excited to share our latest update:\n\n{{body}}\n\nCheck out the full details in our changelog.\n\n---\nInfra Pilot Team", ChannelType.EMAIL, variables=["customer_name", "title", "body"]),
            Template("tpl-security", "Security Notification", "Security Notice", "Hello {{customer_name}},\n\n{{body}}\n\nIf you have questions, please contact our security team.\n\n---\nInfra Pilot Team", ChannelType.EMAIL, variables=["customer_name", "body"]),
            Template("tpl-in-app", "In-App Notification", "{{title}}", "{{body}}", ChannelType.IN_APP, variables=["title", "body"]),
            Template("tpl-slack", "Slack Notification", "*{{title}}*", "{{body}}\n\n_Infra Pilot Notifications_", ChannelType.SLACK, variables=["title", "body"]),
        ]
        for tpl in defaults:
            self.templates[tpl.template_id] = tpl

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for tdata in data.get("templates", []):
                        self.templates[tdata["template_id"]] = Template(**tdata)
                    for bdata in data.get("batches", []):
                        self.batches[bdata["batch_id"]] = NotificationBatch(**bdata)
                    for mdata in data.get("maintenance_windows", []):
                        self.maintenance_windows[mdata["maintenance_id"]] = MaintenanceWindow(**mdata)
                    for rdata in data.get("delivery_records", []):
                        self.delivery_records.append(DeliveryRecord(**rdata))
                    self.customer_channels = defaultdict(dict, data.get("customer_channels", {}))
            except Exception as e:
                logger.warning(f"Failed to load communication data: {e}")

    def _save_data(self):
        try:
            data = {
                "templates": [t.to_dict() for t in self.templates.values()],
                "batches": [b.to_dict() for b in self.batches.values()],
                "maintenance_windows": [m.to_dict() for m in self.maintenance_windows.values()],
                "delivery_records": [r.to_dict() for r in self.delivery_records[-10000:]],
                "customer_channels": dict(self.customer_channels),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save communication data: {e}")

    def create_template(self, name: str, subject: str, body: str, channel: str, category: str = "general", variables: Optional[List[str]] = None) -> Template:
        tpl_id = f"TPL-{uuid.uuid4().hex[:6].upper()}"
        template = Template(template_id=tpl_id, name=name, subject=subject, body=body, channel=ChannelType(channel), category=category, variables=variables or [])
        self.templates[tpl_id] = template
        self._save_data()
        return template

    def list_templates(self, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.templates.values())
        if channel:
            results = [t for t in results if t.channel.value == channel]
        return [t.to_dict() for t in results]

    def send_notification(
        self,
        notification_type: str,
        priority: str,
        subject: str,
        body: str,
        channels: List[str],
        target_segment: str = "all",
        target_customer_ids: Optional[List[str]] = None,
        template_id: Optional[str] = None,
        scheduled_at: Optional[str] = None,
        created_by: str = "",
    ) -> NotificationBatch:
        batch_id = f"BCH-{uuid.uuid4().hex[:8].upper()}"
        batch = NotificationBatch(
            batch_id=batch_id,
            notification_type=NotificationType(notification_type),
            priority=NotificationPriority(priority),
            subject=subject,
            body=body,
            channels=channels,
            target_segment=target_segment,
            target_customer_ids=target_customer_ids,
            template_id=template_id,
            scheduled_at=scheduled_at,
            created_by=created_by,
            status="scheduled" if scheduled_at else "sending",
        )
        self.batches[batch_id] = batch
        self._save_data()
        return batch

    def send_announcement(
        self, subject: str, body: str, channels: Optional[List[str]] = None,
        priority: str = "normal", target_segment: str = "all",
    ) -> NotificationBatch:
        return self.send_notification("announcement", priority, subject, body, channels or ["email", "in_app"], target_segment=target_segment)

    def schedule_maintenance_notification(
        self, title: str, description: str, affected_services: List[str],
        start_time: str, end_time: str, expected_downtime: int,
        created_by: str = "",
    ) -> MaintenanceWindow:
        mw_id = f"MTN-{uuid.uuid4().hex[:8].upper()}"
        window = MaintenanceWindow(
            maintenance_id=mw_id, title=title, description=description,
            affected_services=affected_services, start_time=start_time,
            end_time=end_time, expected_downtime_minutes=expected_downtime,
            created_by=created_by,
        )
        subject = f"Scheduled Maintenance: {title}"
        body = f"Affected services: {', '.join(affected_services)}\nStart: {start_time}\nEnd: {end_time}\nExpected downtime: {expected_downtime} minutes\n\n{description}"
        batch = self.send_notification("maintenance", "high", subject, body, ["email", "in_app", "slack"], target_segment="all", created_by=created_by)
        window.notification_batch_id = batch.batch_id
        self.maintenance_windows[mw_id] = window
        self._save_data()
        return window

    def complete_maintenance(self, maintenance_id: str, actual_downtime: Optional[int] = None, post_mortem: Optional[str] = None) -> Optional[MaintenanceWindow]:
        window = self.maintenance_windows.get(maintenance_id)
        if not window:
            return None
        window.status = "completed"
        window.completed_at = datetime.utcnow().isoformat()
        if actual_downtime is not None:
            window.actual_downtime_minutes = actual_downtime
        if post_mortem:
            window.post_mortem = post_mortem
        self._save_data()
        return window

    def get_maintenance_windows(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.maintenance_windows.values())
        if status:
            results = [m for m in results if m.status == status]
        results.sort(key=lambda m: m.start_time, reverse=True)
        return [m.to_dict() for m in results]

    def record_delivery(
        self, batch_id: str, customer_id: str, channel: str,
        recipient: str, status: str = "pending",
    ) -> DeliveryRecord:
        record = DeliveryRecord(
            record_id=f"DEL-{uuid.uuid4().hex[:8].upper()}",
            batch_id=batch_id, customer_id=customer_id,
            channel=channel, recipient=recipient,
            status=DeliveryStatus(status),
        )
        self.delivery_records.append(record)
        if len(self.delivery_records) > 10000:
            self.delivery_records = self.delivery_records[-10000:]
        self._save_data()
        return record

    def update_delivery_status(self, record_id: str, status: str) -> Optional[DeliveryRecord]:
        record = next((r for r in self.delivery_records if r.record_id == record_id), None)
        if not record:
            return None
        now = datetime.utcnow().isoformat()
        record.status = DeliveryStatus(status)
        if status in ("sent", "delivered"):
            record.sent_at = record.sent_at or now
            record.delivered_at = now
        elif status == "read":
            record.read_at = now
        elif status == "clicked":
            record.clicked_at = now
        self._save_data()
        return record

    def get_batch_stats(self, batch_id: str) -> Optional[Dict[str, Any]]:
        batch = self.batches.get(batch_id)
        if not batch:
            return None
        records = [r for r in self.delivery_records if r.batch_id == batch_id]
        total = len(records)
        delivered = sum(1 for r in records if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED))
        read = sum(1 for r in records if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED))
        clicked = sum(1 for r in records if r.status == DeliveryStatus.CLICKED)
        failed = sum(1 for r in records if r.status == DeliveryStatus.FAILED)
        return {
            "batch_id": batch_id,
            "total": total,
            "delivered": delivered,
            "delivery_rate": round(delivered / max(total, 1), 3),
            "read": read,
            "read_rate": round(read / max(delivered, 1), 3),
            "clicked": clicked,
            "click_rate": round(clicked / max(delivered, 1), 3),
            "failed": failed,
            "failure_rate": round(failed / max(total, 1), 3),
        }

    def set_customer_channel(self, customer_id: str, channel: str, address: str):
        self.customer_channels[customer_id][channel] = address
        self._save_data()

    def get_customer_channels(self, customer_id: str) -> Dict[str, str]:
        return dict(self.customer_channels.get(customer_id, {}))

    def list_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        batches = list(self.batches.values())
        batches.sort(key=lambda b: b.created_at, reverse=True)
        return [b.to_dict() for b in batches[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        total_sent = len(self.delivery_records)
        delivered = sum(1 for r in self.delivery_records if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED))
        read = sum(1 for r in self.delivery_records if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED))
        clicked = sum(1 for r in self.delivery_records if r.status == DeliveryStatus.CLICKED)
        upcoming_maintenance = sum(1 for m in self.maintenance_windows.values() if m.status == "scheduled" and m.start_time > datetime.utcnow().isoformat())
        return {
            "total_batches": len(self.batches),
            "total_deliveries": total_sent,
            "delivery_rate": round(delivered / max(total_sent, 1), 3),
            "read_rate": round(read / max(delivered, 1), 3),
            "click_rate": round(clicked / max(delivered, 1), 3),
            "templates": len(self.templates),
            "maintenance_windows": len(self.maintenance_windows),
            "upcoming_maintenance": upcoming_maintenance,
        }

    def send_broadcast(self, notification_type: str, subject: str, body: str, priority: str = "normal", channels: Optional[List[str]] = None) -> Dict[str, Any]:
        nid = str(uuid.uuid4())[:8]
        notification = Notification(notification_id=nid, notification_type=NotificationType(notification_type), subject=subject, body=body, priority=NotificationPriority(priority), channels=channels or ["email"], status=NotificationStatus.PENDING)
        self.notifications[nid] = notification
        self._save_data()
        return {"notification_id": nid, "status": "created", "channels": notification.channels, "priority": priority}

    def get_notification_stats(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [n for n in self.notifications.values() if n.created_at >= cutoff]
        by_type = defaultdict(int)
        for n in recent:
            by_type[n.notification_type.value] += 1
        return {"total": len(recent), "sent": sum(1 for n in recent if n.sent_at is not None), "scheduled": len([n for n in recent if n.scheduled_for]), "by_type": dict(by_type)}

    def schedule_maintenance(self, title: str, description: str, start_time: datetime, end_time: datetime, affected_services: List[str]) -> Dict[str, Any]:
        mw = MaintenanceWindow(maintenance_id=str(uuid.uuid4())[:8], title=title, description=description, start_time=start_time, end_time=end_time, affected_services=affected_services, status=MaintenanceStatus.SCHEDULED)
        self.maintenance_windows[mw.maintenance_id] = mw
        self._save_data()
        return {"maintenance_id": mw.maintenance_id, "title": title, "status": "scheduled"}

    def get_maintenance_timeline(self) -> List[Dict[str, Any]]:
        upcoming = [mw for mw in self.maintenance_windows.values() if mw.status != MaintenanceStatus.COMPLETED]
        upcoming.sort(key=lambda m: m.start_time)
        return [{"maintenance_id": m.maintenance_id, "title": m.title, "start": m.start_time.isoformat(), "end": m.end_time.isoformat(), "status": m.status.value, "services": m.affected_services} for m in upcoming[:20]]

    def cancel_maintenance(self, maintenance_id: str) -> bool:
        if maintenance_id in self.maintenance_windows:
            self.maintenance_windows[maintenance_id].status = MaintenanceStatus.CANCELLED
            self._save_data()
            return True
        return False

    def complete_maintenance(self, maintenance_id: str) -> bool:
        if maintenance_id in self.maintenance_windows:
            self.maintenance_windows[maintenance_id].status = MaintenanceStatus.COMPLETED
            self.maintenance_windows[maintenance_id].actual_end = datetime.utcnow()
            self._save_data()
            return True
        return False

    def create_template(self, name: str, subject_template: str, body_template: str, variables: List[str]) -> Dict[str, Any]:
        tid = str(uuid.uuid4())[:8]
        tpl = MessageTemplate(template_id=tid, name=name, subject_template=subject_template, body_template=body_template, variables=variables)
        self.templates[tid] = tpl
        self._save_data()
        return {"template_id": tid, "name": name, "variables": variables}

    def render_template(self, template_id: str, context: Dict[str, str]) -> Optional[Dict[str, str]]:
        tpl = self.templates.get(template_id)
        if not tpl:
            return None
        subject = tpl.subject_template
        body = tpl.body_template
        for var, val in context.items():
            subject = subject.replace(f"{{{{{var}}}}}", val)
            body = body.replace(f"{{{{{var}}}}}", val)
        return {"subject": subject, "body": body}

    def get_channel_effectiveness(self) -> Dict[str, Any]:
        channel_stats = defaultdict(lambda: {"sent": 0, "delivered": 0, "read": 0, "clicked": 0})
        for n in self.notifications.values():
            if n.sent_at:
                for ch in n.channels:
                    channel_stats[ch]["sent"] += 1
            for event in n.delivery_events:
                ch = event.get("channel", "unknown")
                if event.get("event") == "delivered":
                    channel_stats[ch]["delivered"] += 1
                elif event.get("event") == "read":
                    channel_stats[ch]["read"] += 1
                elif event.get("event") == "clicked":
                    channel_stats[ch]["clicked"] += 1
        return dict(channel_stats)

    def search_notifications(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [n.to_dict() for n in self.notifications.values() if q in n.subject.lower() or q in n.body.lower() or q in n.notification_type.value]
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    def resend_failed(self, notification_id: str) -> bool:
        n = self.notifications.get(notification_id)
        if not n or n.status != NotificationStatus.FAILED:
            return False
        n.status = NotificationStatus.PENDING
        n.sent_at = None
        self._save_data()
        return True

    def get_audit_log(self, days: int = 7) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [n.to_dict() for n in self.notifications.values() if n.created_at >= cutoff]

    def bulk_notify(self, notification_type: str, subject: str, body: str, customer_ids: List[str]) -> Dict[str, Any]:
        created = []
        for cid in customer_ids:
            nid = str(uuid.uuid4())[:8]
            n = Notification(notification_id=nid, notification_type=NotificationType(notification_type), subject=subject, body=body, status=NotificationStatus.PENDING)
            self.notifications[nid] = n
            created.append(nid)
        self._save_data()
        return {"created_count": len(created), "notification_ids": created}

    def get_delivery_summary(self, notification_id: str) -> Optional[Dict[str, Any]]:
        n = self.notifications.get(notification_id)
        if not n:
            return None
        delivered = sum(1 for e in n.delivery_events if e.get("event") == "delivered")
        read = sum(1 for e in n.delivery_events if e.get("event") == "read")
        clicked = sum(1 for e in n.delivery_events if e.get("event") == "clicked")
        return {"notification_id": notification_id, "subject": n.subject, "status": n.status.value, "delivered": delivered, "read": read, "clicked": clicked, "events": n.delivery_events[:10]}

    def prune_notifications(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        before = len(self.notifications)
        self.notifications = {k: v for k, v in self.notifications.items() if v.created_at >= cutoff}
        removed = before - len(self.notifications)
        if removed > 0:
            self._save_data()
        return removed

    def send_targeted_notification(self, customer_id: str, notification_type: str, subject: str, body: str, channels: Optional[List[str]] = None, priority: str = "normal") -> Optional[Dict[str, Any]]:
        batch = self.send_notification(notification_type, priority, subject, body, channels or ["email", "in_app"], target_customer_ids=[customer_id])
        if batch:
            for ch in (channels or ["email", "in_app"]):
                self.record_delivery(batch.batch_id, customer_id, ch, customer_id)
        return {"batch_id": batch.batch_id, "customer_id": customer_id, "channels": channels or ["email", "in_app"]} if batch else None

    def get_customer_notification_history(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        records = [r for r in self.delivery_records if r.customer_id == customer_id]
        records.sort(key=lambda r: r.created_at, reverse=True)
        seen_batches = set()
        history = []
        for r in records:
            if r.batch_id not in seen_batches:
                seen_batches.add(r.batch_id)
                batch = self.batches.get(r.batch_id)
                if batch:
                    history.append(batch.to_dict())
            if len(history) >= limit:
                break
        return history

    def get_delivery_analytics(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        records = [r for r in self.delivery_records if r.created_at >= cutoff]
        by_channel = defaultdict(lambda: {"sent": 0, "delivered": 0, "read": 0, "clicked": 0, "failed": 0})
        for r in records:
            ch = r.channel
            by_channel[ch]["sent"] += 1
            if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED):
                by_channel[ch]["delivered"] += 1
            if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED):
                by_channel[ch]["read"] += 1
            if r.status == DeliveryStatus.CLICKED:
                by_channel[ch]["clicked"] += 1
            if r.status == DeliveryStatus.FAILED:
                by_channel[ch]["failed"] += 1
        return {
            "period_days": days,
            "total_records": len(records),
            "by_channel": dict(by_channel),
            "overall_delivery_rate": round(sum(1 for r in records if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED)) / max(len(records), 1), 3),
            "overall_read_rate": round(sum(1 for r in records if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED)) / max(len(records), 1), 3),
        }

    def create_campaign(self, name: str, notification_type: str, subject: str, body: str, channels: List[str], target_segment: str = "all", schedule_at: Optional[str] = None) -> Dict[str, Any]:
        batch = self.send_notification(notification_type, "normal", subject, body, channels, target_segment=target_segment, scheduled_at=schedule_at)
        return {"campaign_id": batch.batch_id, "name": name, "status": "scheduled" if schedule_at else "active"} if batch else {"error": "Failed to create campaign"}

    def get_campaign_performance(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self.get_batch_stats(batch_id)

    def list_campaigns(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.list_batches(limit)

    def schedule_recurring_notification(self, name: str, notification_type: str, subject_template: str, body_template: str, channels: List[str], cron_expression: str, target_segment: str = "all") -> Dict[str, Any]:
        schedule_id = f"SCH-{uuid.uuid4().hex[:6].upper()}"
        return {
            "schedule_id": schedule_id,
            "name": name,
            "cron": cron_expression,
            "channels": channels,
            "target_segment": target_segment,
            "status": "active",
        }

    def get_channel_health(self) -> Dict[str, Any]:
        channel_health = {}
        for ch in ChannelType:
            records = [r for r in self.delivery_records if r.channel == ch.value]
            if not records:
                channel_health[ch.value] = {"status": "unknown", "total": 0}
                continue
            failed = sum(1 for r in records if r.status == DeliveryStatus.FAILED)
            failure_rate = failed / len(records)
            channel_health[ch.value] = {
                "status": "healthy" if failure_rate < 0.05 else "degraded" if failure_rate < 0.15 else "unhealthy",
                "total": len(records),
                "failed": failed,
                "failure_rate": round(failure_rate, 3),
            }
        return channel_health

    def get_notification_templates(self, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.list_templates(channel)

    def render_notification(self, template_id: str, context: Dict[str, str]) -> Optional[Dict[str, str]]:
        return self.render_template(template_id, context)

    def bulk_notify_segment(self, notification_type: str, subject: str, body: str, segment: str, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        batch = self.send_notification(notification_type, "normal", subject, body, channels or ["email", "in_app"], target_segment=segment)
        return {"batch_id": batch.batch_id, "segment": segment, "type": notification_type, "estimated_recipients": 0} if batch else {"error": "Failed"}

    def get_maintenance_schedule(self, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() + timedelta(days=days)).isoformat()
        upcoming = [m for m in self.maintenance_windows.values() if m.status == "scheduled" and m.start_time <= cutoff]
        upcoming.sort(key=lambda m: m.start_time)
        return [m.to_dict() for m in upcoming]

    def update_maintenance_status(self, maintenance_id: str, status: str, actual_downtime: Optional[int] = None, post_mortem: Optional[str] = None) -> Optional[MaintenanceWindow]:
        return self.complete_maintenance(maintenance_id, actual_downtime, post_mortem) if status == "completed" else None

    def get_notification_effectiveness(self) -> Dict[str, Any]:
        stats = self.get_stats()
        channel_stats = defaultdict(lambda: {"sent": 0, "delivered": 0, "read": 0})
        for r in self.delivery_records:
            channel_stats[r.channel]["sent"] += 1
            if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED):
                channel_stats[r.channel]["delivered"] += 1
            if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED):
                channel_stats[r.channel]["read"] += 1
        return {
            "overall": stats,
            "channel_effectiveness": {
                ch: {
                    "delivery_rate": round(data["delivered"] / max(data["sent"], 1), 3),
                    "read_rate": round(data["read"] / max(data["delivered"], 1), 3),
                }
                for ch, data in channel_stats.items()
            },
        }

    def send_test_notification(self, channel: str, recipient: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        test_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"
        return {"test_id": test_id, "channel": channel, "recipient": recipient, "status": "sent", "template_id": template_id}

    def get_unread_count(self, customer_id: str) -> int:
        return sum(1 for r in self.delivery_records if r.customer_id == customer_id and r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.SENT))

    def mark_as_read(self, record_id: str) -> bool:
        record = next((r for r in self.delivery_records if r.record_id == record_id), None)
        if not record:
            return False
        record.status = DeliveryStatus.READ
        record.read_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_preference_center(self, customer_id: str) -> Dict[str, Any]:
        channels = self.get_customer_channels(customer_id)
        return {
            "customer_id": customer_id,
            "email_enabled": "email" in channels,
            "in_app_enabled": True,
            "slack_enabled": "slack" in channels,
            "push_enabled": "push" in channels,
            "notification_types": {nt.value: True for nt in NotificationType},
        }

    def update_preferences(self, customer_id: str, preferences: Dict[str, bool]) -> bool:
        if preferences.get("email_enabled"):
            self.set_customer_channel(customer_id, "email", customer_id)
        return True

    def get_failed_deliveries(self, limit: int = 50) -> List[Dict[str, Any]]:
        failed = [r.to_dict() for r in self.delivery_records if r.status == DeliveryStatus.FAILED]
        failed.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return failed[:limit]

    def retry_failed_delivery(self, record_id: str) -> bool:
        record = next((r for r in self.delivery_records if r.record_id == record_id and r.status == DeliveryStatus.FAILED), None)
        if not record:
            return False
        record.status = DeliveryStatus.PENDING
        record.sent_at = None
        record.delivered_at = None
        self._save_data()
        return True

    def get_notification_history(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        records = [r.to_dict() for r in self.delivery_records if r.customer_id == customer_id]
        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records[:limit]

    def search_delivery_records(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [r.to_dict() for r in self.delivery_records if q in r.customer_id.lower() or q in r.channel.lower() or q in (r.error or "").lower()]
        results.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return results[:limit]

    def batch_retry_failed(self, record_ids: List[str]) -> Dict[str, Any]:
        succeeded = 0
        failed = 0
        for rid in record_ids:
            if self.retry_failed_delivery(rid):
                succeeded += 1
            else:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total": len(record_ids)}

    def get_channel_stats(self, channel: str) -> Dict[str, Any]:
        records = [r for r in self.delivery_records if r.channel == channel]
        sent = len(records)
        delivered = sum(1 for r in records if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED))
        read = sum(1 for r in records if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED))
        failed = sum(1 for r in records if r.status == DeliveryStatus.FAILED)
        return {"channel": channel, "sent": sent, "delivered": delivered, "read": read, "failed": failed, "delivery_rate": round(delivered / max(sent, 1), 3), "read_rate": round(read / max(delivered, 1), 3)}

    def create_notification_template(self, name: str, subject: str, body: str, channel: str, variables: Optional[List[str]] = None) -> Dict[str, Any]:
        template_id = f"TMPL-{uuid.uuid4().hex[:6].upper()}"
        self.templates[template_id] = NotificationTemplate(template_id=template_id, name=name, subject=subject, body=body, channel=channel, variables=variables or [])
        self._save_data()
        return self.templates[template_id].to_dict()

    def delete_notification_template(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_data()
            return True
        return False

    def update_notification_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        t = self.templates.get(template_id)
        if not t:
            return None
        if "name" in updates:
            t.name = updates["name"]
        if "subject" in updates:
            t.subject = updates["subject"]
        if "body" in updates:
            t.body = updates["body"]
        if "variables" in updates:
            t.variables = updates["variables"]
        t.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return t.to_dict()

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        summary_date = date or datetime.utcnow().strftime("%Y-%m-%d")
        records = [r for r in self.delivery_records if r.created_at and r.created_at.startswith(summary_date)]
        return {
            "date": summary_date,
            "total_sent": len(records),
            "delivered": sum(1 for r in records if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED)),
            "read": sum(1 for r in records if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED)),
            "failed": sum(1 for r in records if r.status == DeliveryStatus.FAILED),
            "by_channel": dict(Counter(r.channel for r in records)),
            "by_type": dict(Counter(r.notification_type for r in records if r.notification_type)),
        }

    def get_maintenance_events(self, days: int = 7) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        events = [m.to_dict() for m in self.maintenance_windows.values() if m.start_time >= cutoff]
        events.sort(key=lambda e: e.get("start_time", ""), reverse=True)
        return events

    def get_customer_channel_preferences(self, customer_id: str) -> Dict[str, Any]:
        channels = self.get_customer_channels(customer_id)
        return {
            "customer_id": customer_id,
            "channels": list(channels) if isinstance(channels, dict) else channels,
            "opted_out": False,
        }

    def opt_out_customer(self, customer_id: str) -> bool:
        self.customer_channels[customer_id] = {}
        self._save_data()
        return True

    def resubscribe_customer(self, customer_id: str, channels: List[str]) -> bool:
        for ch in channels:
            self.set_customer_channel(customer_id, ch, customer_id)
        return True

    def send_scheduled_notifications(self) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        scheduled = [m for m in self.maintenance_windows.values() if m.status == "scheduled" and m.start_time <= now and m.end_time >= now]
        sent = 0
        for m in scheduled:
            recipients = [cid for cid in self.customer_channels if self.customer_channels[cid]]
            for cid in recipients[:100]:
                self.send_notification("maintenance_alert", "high", f"Maintenance: {m.title}", "in_app", target_segment=None)
                sent += 1
        return {"active_maintenance": len(scheduled), "notifications_sent": sent}


class CommunicationBatchProcessor:
    def __init__(self, service: CommunicationHubService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_send_notifications(self, notifications: List[Dict[str, Any]]) -> List[NotificationBatch]:
        results = []
        for n in notifications:
            try:
                batch = self.service.send_notification(
                    notification_type=n["type"], priority=n.get("priority", "normal"),
                    subject=n["subject"], body=n["body"],
                    channels=n.get("channels", ["email"]),
                    target_segment=n.get("segment", "all"),
                    target_customer_ids=n.get("customer_ids"),
                    created_by=n.get("created_by", ""),
                )
                results.append(batch)
                self.batch_log.append({"action": "send", "batch_id": batch.batch_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "send", "subject": n.get("subject"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


@dataclass
class CommunicationStateTransition:
    from_state: str
    to_state: str
    trigger: str
    entity_id: str
    timestamp: str = ""
    actor: str = "system"


def paginate_delivery_records(records: List[DeliveryRecord], page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
    filtered = [r for r in records if r.status.value == status] if status else records
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [r.to_dict() for r in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_channel_roi(service: CommunicationHubService) -> Dict[str, Any]:
    channel_stats = defaultdict(lambda: {"sent": 0, "delivered": 0, "read": 0, "failed": 0})
    for r in service.delivery_records:
        ch = r.channel
        channel_stats[ch]["sent"] += 1
        if r.status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ, DeliveryStatus.CLICKED):
            channel_stats[ch]["delivered"] += 1
        if r.status in (DeliveryStatus.READ, DeliveryStatus.CLICKED):
            channel_stats[ch]["read"] += 1
        if r.status == DeliveryStatus.FAILED:
            channel_stats[ch]["failed"] += 1
    return {
        ch: {
            "sent": data["sent"],
            "delivery_rate": round(data["delivered"] / max(data["sent"], 1), 3),
            "read_rate": round(data["read"] / max(data["delivered"], 1), 3),
            "failure_rate": round(data["failed"] / max(data["sent"], 1), 3),
        }
        for ch, data in channel_stats.items()
    }


class CommunicationAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


class CommunicationMetricsCollector:
    def __init__(self):
        self._counts: Dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> Dict[str, int]:
        return dict(self._counts)


def validate_communication_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    max_retries = config.get("max_delivery_retries")
    if max_retries is not None and max_retries < 0:
        errors.append("max_delivery_retries must be >= 0")
    return errors


def merge_customer_communication_data(service: CommunicationHubService, source_customer: str, target_customer: str) -> int:
    count = 0
    for r in service.delivery_records:
        if r.customer_id == source_customer:
            r.customer_id = target_customer
            count += 1
    if source_customer in service.customer_channels:
        channels = service.customer_channels.pop(source_customer)
        service.customer_channels[target_customer].update(channels)
        count += 1
    if count:
        service._save_data()
    return count

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
