"""Feature 91: Pub/Sub Event Bus - Multi-tenant event bus with CloudEvents spec"""

import json
import os
import time
import uuid
import hashlib
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class CloudEvent:
    specversion: str = "1.0"
    id: str = ""
    source: str = ""
    specversion: str = "1.0"
    type: str = ""
    subject: Optional[str] = None
    time: str = ""
    datacontenttype: str = "application/json"
    data: Any = None
    dataschema: Optional[str] = None
    extensions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "specversion": self.specversion,
            "id": self.id,
            "source": self.source,
            "type": self.type,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data
        }
        if self.subject:
            result["subject"] = self.subject
        if self.dataschema:
            result["dataschema"] = self.dataschema
        result.update(self.extensions)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudEvent":
        extensions = {k: v for k, v in data.items() if k not in [
            "specversion", "id", "source", "type", "subject", "time",
            "datacontenttype", "data", "dataschema"
        ]}
        return cls(
            specversion=data.get("specversion", "1.0"),
            id=data.get("id", str(uuid.uuid4())),
            source=data.get("source", ""),
            type=data.get("type", ""),
            subject=data.get("subject"),
            time=data.get("time", datetime.utcnow().isoformat() + "Z"),
            datacontenttype=data.get("datacontenttype", "application/json"),
            data=data.get("data"),
            dataschema=data.get("dataschema"),
            extensions=extensions
        )


@dataclass
class Subscription:
    id: str
    topic: str
    endpoint: str
    protocol: str = "webhook"
    filter_expression: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    active: bool = True
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 5,
        "initial_backoff_ms": 1000,
        "max_backoff_ms": 60000,
        "backoff_multiplier": 2.0,
        "dead_letter_enabled": True
    })
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    id: str
    event: CloudEvent
    topic: str
    subscription_id: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: str = ""
    delivered_at: Optional[str] = None
    retry_count: int = 0
    last_error: Optional[str] = None
    ack_deadline: float = 60.0
    ack_id: Optional[str] = None


class PubSubEventBus:
    """Multi-tenant Pub/Sub Event Bus implementing CloudEvents specification"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.topics_file = _data_file('pubsub_topics.json')
        self.subscriptions_file = _data_file('pubsub_subscriptions.json')
        self.messages_file = _data_file('pubsub_messages.json')
        self.dead_letter_file = _data_file('pubsub_dead_letters.json')

        self.topics: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.messages: List[Message] = []
        self.dead_letter_messages: List[Message] = []
        self.subscriber_callbacks: Dict[str, List[Callable]] = {}

        self._load_data()
        self._background_tasks: List[asyncio.Task] = []

    def _load_data(self):
        for filepath, target in [
            (self.topics_file, 'topics'),
            (self.subscriptions_file, 'subscriptions'),
            (self.messages_file, 'messages'),
            (self.dead_letter_file, 'dead_letters')
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == 'topics':
                        self.topics = data
                    elif target == 'subscriptions':
                        self.subscriptions = {k: Subscription(**v) for k, v in data.items()}
                    elif target == 'messages':
                        self.messages = [Message(**m) for m in data]
                    elif target == 'dead_letters':
                        self.dead_letter_messages = [Message(**m) for m in data]
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_topics(self):
        try:
            with open(self.topics_file, 'w') as f:
                json.dump(self.topics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save topics: {e}")

    def _save_subscriptions(self):
        try:
            with open(self.subscriptions_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.subscriptions.items()}, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save subscriptions: {e}")

    def _save_messages(self):
        try:
            with open(self.messages_file, 'w') as f:
                json.dump([asdict(m) for m in self.messages[-10000:]], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")

    def _save_dead_letters(self):
        try:
            with open(self.dead_letter_file, 'w') as f:
                json.dump([asdict(m) for m in self.dead_letter_messages[-5000:]], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save dead letters: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    async def create_topic(self, topic_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if topic_id in self.topics:
            raise ValueError(f"Topic '{topic_id}' already exists")
        topic = {
            "id": topic_id,
            "name": config.get("name", topic_id),
            "description": config.get("description", ""),
            "created_at": self._now(),
            "updated_at": self._now(),
            "retention_period_days": config.get("retention_period_days", 7),
            "message_count": 0,
            "subscription_count": 0,
            "labels": config.get("labels", {}),
            "schema_enforced": config.get("schema_enforced", False),
            "schema": config.get("schema"),
            "tenant_id": config.get("tenant_id", "default")
        }
        self.topics[topic_id] = topic
        self._save_topics()
        return topic

    async def delete_topic(self, topic_id: str) -> bool:
        if topic_id not in self.topics:
            return False
        subs_to_remove = [k for k, v in self.subscriptions.items() if v.topic == topic_id]
        for sid in subs_to_remove:
            del self.subscriptions[sid]
        self._save_subscriptions()
        del self.topics[topic_id]
        self._save_topics()
        return True

    async def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        return self.topics.get(topic_id)

    async def list_topics(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        topics = list(self.topics.values())
        if tenant_id:
            topics = [t for t in topics if t.get("tenant_id") == tenant_id]
        return topics

    async def create_subscription(self, topic: str, endpoint: str, config: Dict[str, Any]) -> Subscription:
        if topic not in self.topics:
            raise ValueError(f"Topic '{topic}' does not exist")
        sub = Subscription(
            id=self._generate_id(),
            topic=topic,
            endpoint=endpoint,
            protocol=config.get("protocol", "webhook"),
            filter_expression=config.get("filter_expression"),
            created_at=self._now(),
            updated_at=self._now(),
            active=config.get("active", True),
            retry_policy=config.get("retry_policy", {
                "max_retries": 5,
                "initial_backoff_ms": 1000,
                "max_backoff_ms": 60000,
                "backoff_multiplier": 2.0,
                "dead_letter_enabled": True
            }),
            metadata=config.get("metadata", {})
        )
        self.subscriptions[sub.id] = sub
        self.topics[topic]["subscription_count"] = self.topics[topic].get("subscription_count", 0) + 1
        self._save_subscriptions()
        self._save_topics()
        return sub

    async def delete_subscription(self, sub_id: str) -> bool:
        if sub_id not in self.subscriptions:
            return False
        topic = self.subscriptions[sub_id].topic
        if topic in self.topics:
            self.topics[topic]["subscription_count"] = max(0, self.topics[topic].get("subscription_count", 0) - 1)
        del self.subscriptions[sub_id]
        self._save_subscriptions()
        self._save_topics()
        return True

    async def get_subscription(self, sub_id: str) -> Optional[Subscription]:
        return self.subscriptions.get(sub_id)

    async def list_subscriptions(self, topic: Optional[str] = None) -> List[Subscription]:
        subs = list(self.subscriptions.values())
        if topic:
            subs = [s for s in subs if s.topic == topic]
        return subs

    async def publish(self, source: str, event_type: str, data: Any,
                      subject: Optional[str] = None,
                      dataschema: Optional[str] = None,
                      extensions: Optional[Dict[str, Any]] = None,
                      topic: Optional[str] = None) -> CloudEvent:
        topic = topic or event_type.split('.')[0]
        event = CloudEvent(
            id=self._generate_id(),
            source=source,
            type=event_type,
            subject=subject,
            time=self._now(),
            data=data,
            dataschema=dataschema,
            extensions=extensions or {}
        )

        if topic not in self.topics:
            await self.create_topic(topic, {"name": topic, "description": f"Auto-created topic for {topic}"})

        self.topics[topic]["message_count"] = self.topics[topic].get("message_count", 0) + 1
        self._save_topics()

        matching_subs = [s for s in self.subscriptions.values()
                         if s.topic == topic and s.active]
        for sub in matching_subs:
            if sub.filter_expression:
                if not self._evaluate_filter(sub.filter_expression, event):
                    continue
            msg = Message(
                id=self._generate_id(),
                event=event,
                topic=topic,
                subscription_id=sub.id,
                created_at=self._now(),
                ack_id=self._generate_id()
            )
            self.messages.append(msg)
            asyncio.create_task(self._deliver_message(msg, sub))

        self._save_messages()

        for cb in self.subscriber_callbacks.get(topic, []):
            try:
                cb(event)
            except Exception as e:
                logger.error(f"Subscriber callback failed: {e}")

        return event

    def subscribe_local(self, topic: str, callback: Callable):
        self.subscriber_callbacks.setdefault(topic, []).append(callback)

    def _evaluate_filter(self, expression: str, event: CloudEvent) -> bool:
        try:
            expr = expression.strip()
            if expr.startswith("type == "):
                expected = expr[8:].strip().strip('"\'')
                return event.type == expected
            if expr.startswith("type in "):
                values_str = expr[8:].strip()
                if values_str.startswith("[") and values_str.endswith("]"):
                    values = [v.strip().strip('"\'') for v in values_str[1:-1].split(",")]
                    return event.type in values
            if expr.startswith("source == "):
                expected = expr[10:].strip().strip('"\'')
                return event.source == expected
            if expr.startswith("subject == "):
                expected = expr[11:].strip().strip('"\'')
                return event.subject == expected
            if " && " in expr:
                parts = expr.split(" && ")
                return all(self._evaluate_filter(p.strip(), event) for p in parts)
            if " || " in expr:
                parts = expr.split(" || ")
                return any(self._evaluate_filter(p.strip(), event) for p in parts)
            return True
        except Exception as e:
            logger.warning(f"Filter evaluation error: {e}")
            return True

    async def _deliver_message(self, msg: Message, sub: Subscription):
        protocol = sub.protocol
        msg.status = DeliveryStatus.DELIVERING
        self._save_messages()

        if protocol == "callback":
            await self._deliver_callback(msg, sub)
        elif protocol == "webhook":
            await self._deliver_webhook(msg, sub)
        elif protocol == "pull":
            msg.status = DeliveryStatus.PENDING
            self._save_messages()
        else:
            await self._deliver_webhook(msg, sub)

    async def _deliver_callback(self, msg: Message, sub: Subscription):
        try:
            callbacks = self.subscriber_callbacks.get(sub.topic, [])
            for cb in callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(msg.event)
                    else:
                        cb(msg.event)
                except Exception as e:
                    logger.error(f"Callback delivery failed: {e}")
            msg.status = DeliveryStatus.DELIVERED
            msg.delivered_at = self._now()
        except Exception as e:
            msg.status = DeliveryStatus.FAILED
            msg.last_error = str(e)
        self._save_messages()

    async def _deliver_webhook(self, msg: Message, sub: Subscription):
        import aiohttp
        max_retries = sub.retry_policy.get("max_retries", 5)
        initial_backoff = sub.retry_policy.get("initial_backoff_ms", 1000) / 1000
        max_backoff = sub.retry_policy.get("max_backoff_ms", 60000) / 1000
        multiplier = sub.retry_policy.get("backoff_multiplier", 2.0)

        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Content-Type": "application/json",
                        "Ce-Id": msg.event.id,
                        "Ce-Source": msg.event.source,
                        "Ce-Type": msg.event.type,
                        "Ce-Specversion": "1.0",
                        "Ce-Time": msg.event.time,
                        "Ce-Subject": msg.event.subject or "",
                    }
                    async with session.post(
                        sub.endpoint,
                        json=msg.event.to_dict(),
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status < 500:
                            msg.status = DeliveryStatus.DELIVERED
                            msg.delivered_at = self._now()
                            self._save_messages()
                            return
                        msg.last_error = f"HTTP {resp.status}"
            except asyncio.TimeoutError:
                msg.last_error = "timeout"
            except Exception as e:
                msg.last_error = str(e)

            if attempt < max_retries:
                backoff = min(initial_backoff * (multiplier ** attempt), max_backoff)
                await asyncio.sleep(backoff)

        msg.retry_count = max_retries
        if sub.retry_policy.get("dead_letter_enabled", True):
            msg.status = DeliveryStatus.DEAD_LETTER
            self.dead_letter_messages.append(msg)
            self._save_dead_letters()
        else:
            msg.status = DeliveryStatus.FAILED
        self._save_messages()

    async def pull_messages(self, sub_id: str, max_messages: int = 10,
                            ack_deadline_seconds: int = 60) -> List[Dict[str, Any]]:
        sub = self.subscriptions.get(sub_id)
        if not sub:
            raise ValueError(f"Subscription '{sub_id}' not found")

        pending = [m for m in self.messages
                   if m.subscription_id == sub_id and m.status == DeliveryStatus.PENDING]
        batch = pending[:max_messages]

        results = []
        for msg in batch:
            msg.status = DeliveryStatus.DELIVERING
            msg.ack_deadline = time.time() + ack_deadline_seconds
            results.append({
                "ack_id": msg.ack_id,
                "message": msg.event.to_dict(),
                "delivery_attempt": msg.retry_count + 1
            })
        self._save_messages()
        return results

    async def acknowledge_message(self, ack_ids: List[str]) -> int:
        acked = 0
        for msg in self.messages:
            if msg.ack_id in ack_ids and msg.status == DeliveryStatus.DELIVERING:
                msg.status = DeliveryStatus.DELIVERED
                msg.delivered_at = self._now()
                acked += 1
        self._save_messages()
        return acked

    async def get_dead_letter_messages(self, sub_id: Optional[str] = None) -> List[Dict[str, Any]]:
        msgs = self.dead_letter_messages
        if sub_id:
            msgs = [m for m in msgs if m.subscription_id == sub_id]
        return [{"id": m.id, "event": m.event.to_dict(), "subscription_id": m.subscription_id,
                 "last_error": m.last_error, "retry_count": m.retry_count,
                 "created_at": m.created_at} for m in msgs]

    async def redeliver_dead_letters(self, sub_id: str) -> int:
        to_redeliver = [m for m in self.dead_letter_messages if m.subscription_id == sub_id]
        sub = self.subscriptions.get(sub_id)
        if not sub:
            return 0
        count = 0
        for msg in to_redeliver:
            msg.status = DeliveryStatus.PENDING
            msg.retry_count = 0
            msg.last_error = None
            self.messages.append(msg)
            count += 1
        self.dead_letter_messages = [m for m in self.dead_letter_messages if m.subscription_id != sub_id]
        self._save_messages()
        self._save_dead_letters()
        return count

    async def get_topic_stats(self, topic_id: str) -> Dict[str, Any]:
        topic = self.topics.get(topic_id)
        if not topic:
            raise ValueError(f"Topic '{topic_id}' not found")
        subs = [s for s in self.subscriptions.values() if s.topic == topic_id]
        topic_messages = [m for m in self.messages if m.topic == topic_id]
        return {
            "topic_id": topic_id,
            "total_messages": len(topic_messages),
            "delivered": sum(1 for m in topic_messages if m.status == DeliveryStatus.DELIVERED),
            "pending": sum(1 for m in topic_messages if m.status == DeliveryStatus.PENDING),
            "failed": sum(1 for m in topic_messages if m.status == DeliveryStatus.FAILED),
            "dead_lettered": sum(1 for m in topic_messages if m.status == DeliveryStatus.DEAD_LETTER),
            "active_subscriptions": sum(1 for s in subs if s.active),
            "total_subscriptions": len(subs)
        }

    async def cleanup_expired_messages(self):
        retention_days = 7
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        before = len(self.messages)
        self.messages = [m for m in self.messages
                         if datetime.fromisoformat(m.created_at.replace("Z", "+00:00")) > cutoff]
        self._save_messages()
        logger.info(f"Cleaned up {before - len(self.messages)} expired messages")

    async def initialize(self):
        logger.info("PubSubEventBus initialized with %d topics, %d subscriptions, %d messages",
                     len(self.topics), len(self.subscriptions), len(self.messages))
        task = asyncio.create_task(self._periodic_cleanup())
        self._background_tasks.append(task)

    async def close(self):
        for task in self._background_tasks:
            task.cancel()
        self._save_messages()
        self._save_dead_letters()
        logger.info("PubSubEventBus closed")

    async def _periodic_cleanup(self):
        while True:
            await asyncio.sleep(3600)
            try:
                await self.cleanup_expired_messages()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
