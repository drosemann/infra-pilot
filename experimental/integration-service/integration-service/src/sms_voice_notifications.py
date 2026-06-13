"""Feature 95: SMS/Voice Notification - Twilio/Plivo integration with escalation chains"""

import json
import os
import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class NotificationProvider(Enum):
    TWILIO = "twilio"
    PLIVO = "plivo"
    VONAGE = "vonage"
    AWS_SNS = "aws_sns"


class EscalationLevel(Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class DeliveryStatus(Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class SMSVoiceNotificationManager:
    """SMS and Voice notification manager with Twilio/Plivo integration and escalation chains"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("sms_provider", "twilio")
        self.account_sid = config.get("twilio_account_sid") or config.get("plivo_auth_id", "")
        self.auth_token = config.get("twilio_auth_token") or config.get("plivo_auth_token", "")
        self.phone_number = config.get("sms_from_number", "+15551234567")
        self.voice_enabled = config.get("voice_enabled", True)
        self.sms_enabled = config.get("sms_enabled", True)

        self.templates_file = _data_file('sms_templates.json')
        self.escalation_chains_file = _data_file('escalation_chains.json')
        self.delivery_log_file = _data_file('sms_delivery_log.json')

        self.templates: Dict[str, Dict[str, Any]] = {}
        self.escalation_chains: Dict[str, Dict[str, Any]] = {}
        self.delivery_log: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.templates_file, "templates"),
            (self.escalation_chains_file, "chains"),
            (self.delivery_log_file, "log")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "templates":
                        self.templates = data
                    elif target == "chains":
                        self.escalation_chains = data
                    elif target == "log":
                        self.delivery_log = data[-5000:]
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_templates(self):
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    def _save_chains(self):
        try:
            with open(self.escalation_chains_file, 'w') as f:
                json.dump(self.escalation_chains, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chains: {e}")

    def _save_log(self):
        try:
            with open(self.delivery_log_file, 'w') as f:
                json.dump(self.delivery_log[-5000:], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save delivery log: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _mask_phone(self, phone: str) -> str:
        if len(phone) >= 4:
            return phone[:2] + "***" + phone[-2:]
        return phone

    async def send_sms(self, to: str, message: str,
                       template_id: Optional[str] = None,
                       template_vars: Optional[Dict[str, str]] = None,
                       priority: str = "normal") -> Dict[str, Any]:
        if not self.sms_enabled:
            return {"status": "disabled", "message": "SMS is disabled"}

        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            tmpl = template.get("body", message)
            if template_vars:
                for k, v in (template_vars or {}).items():
                    tmpl = tmpl.replace("{{" + k + "}}", str(v))
            message = tmpl

        delivery_id = self._generate_id()
        entry = {
            "id": delivery_id,
            "type": "sms",
            "to": self._mask_phone(to),
            "to_full": to,
            "message_preview": message[:100],
            "status": DeliveryStatus.QUEUED.value,
            "provider": self.provider,
            "priority": priority,
            "created_at": self._now(),
            "sent_at": None,
            "delivered_at": None,
            "error": None,
            "cost": 0
        }

        try:
            result = await self._send_via_provider(to, message, "sms")
            entry["status"] = result.get("status", DeliveryStatus.SENT.value)
            entry["sent_at"] = self._now()
            entry["cost"] = result.get("cost", 0.0075)
            if result.get("status") == "failed":
                entry["status"] = DeliveryStatus.FAILED.value
                entry["error"] = result.get("error", "Unknown error")
        except Exception as e:
            entry["status"] = DeliveryStatus.FAILED.value
            entry["error"] = str(e)
            logger.error(f"SMS delivery failed to {self._mask_phone(to)}: {e}")

        self.delivery_log.append(entry)
        self._save_log()
        return {
            "delivery_id": delivery_id,
            "status": entry["status"],
            "to": self._mask_phone(to),
            "cost": entry["cost"],
            "error": entry.get("error")
        }

    async def send_voice_call(self, to: str, message: str,
                              template_id: Optional[str] = None,
                              template_vars: Optional[Dict[str, str]] = None,
                              voice: str = "alice",
                              language: str = "en-US") -> Dict[str, Any]:
        if not self.voice_enabled:
            return {"status": "disabled", "message": "Voice calls are disabled"}

        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            tmpl = template.get("voice_body", template.get("body", message))
            if template_vars:
                for k, v in (template_vars or {}).items():
                    tmpl = tmpl.replace("{{" + k + "}}", str(v))
            message = tmpl

        delivery_id = self._generate_id()
        entry = {
            "id": delivery_id,
            "type": "voice",
            "to": self._mask_phone(to),
            "to_full": to,
            "message_preview": message[:100],
            "status": DeliveryStatus.QUEUED.value,
            "provider": self.provider,
            "voice": voice,
            "language": language,
            "created_at": self._now(),
            "sent_at": None,
            "duration_seconds": 0,
            "cost": 0,
            "error": None
        }

        try:
            result = await self._send_via_provider(to, message, "voice", {"voice": voice, "language": language})
            entry["status"] = result.get("status", DeliveryStatus.SENT.value)
            entry["sent_at"] = self._now()
            entry["cost"] = result.get("cost", 0.05)
            entry["duration_seconds"] = result.get("duration", 0)
            if result.get("status") == "failed":
                entry["status"] = DeliveryStatus.FAILED.value
                entry["error"] = result.get("error", "Unknown error")
        except Exception as e:
            entry["status"] = DeliveryStatus.FAILED.value
            entry["error"] = str(e)
            logger.error(f"Voice call failed to {self._mask_phone(to)}: {e}")

        self.delivery_log.append(entry)
        self._save_log()
        return {
            "delivery_id": delivery_id,
            "status": entry["status"],
            "to": self._mask_phone(to),
            "cost": entry["cost"],
            "error": entry.get("error")
        }

    async def _send_via_provider(self, to: str, message: str,
                                  msg_type: str,
                                  options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        provider = self.provider
        if provider == "twilio":
            return await self._send_twilio(to, message, msg_type, options or {})
        elif provider == "plivo":
            return await self._send_plivo(to, message, msg_type, options or {})
        elif provider == "vonage":
            return await self._send_vonage(to, message, msg_type, options or {})
        else:
            logger.warning(f"Unknown provider {provider}, simulating delivery")
            await asyncio.sleep(0.5)
            return {"status": "sent", "cost": 0.0075, "provider": provider}

    async def _send_twilio(self, to: str, message: str,
                            msg_type: str,
                            options: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            if msg_type == "sms":
                twilio_msg = client.messages.create(
                    body=message,
                    from_=self.phone_number,
                    to=to,
                    status_callback=self.config.get("twilio_status_callback")
                )
                return {
                    "status": "sent",
                    "provider": "twilio",
                    "message_sid": twilio_msg.sid,
                    "cost": float(twilio_msg.price or 0.0075),
                    "status_raw": twilio_msg.status
                }
            else:
                twilio_call = client.calls.create(
                    twiml=f'<Response><Say voice="{options.get("voice", "alice")}" language="{options.get("language", "en-US")}">{message}</Say></Response>',
                    from_=self.phone_number,
                    to=to,
                    status_callback=self.config.get("twilio_voice_status_callback")
                )
                return {
                    "status": "sent",
                    "provider": "twilio",
                    "call_sid": twilio_call.sid,
                    "cost": float(twilio_call.price or 0.05),
                    "duration": 0
                }
        except ImportError:
            logger.warning("twilio package not installed, simulating")
            await asyncio.sleep(0.3)
            return {"status": "sent", "cost": 0.0075, "provider": "twilio_simulated"}
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            return {"status": "failed", "error": str(e)}

    async def _send_plivo(self, to: str, message: str,
                           msg_type: str,
                           options: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import plivo
            client = plivo.RestClient(auth_id=self.account_sid, auth_token=self.auth_token)
            if msg_type == "sms":
                response = client.messages.create(
                    src=self.phone_number,
                    dst=to,
                    text=message
                )
                return {
                    "status": "sent",
                    "provider": "plivo",
                    "message_uuid": response.message_uuid[0] if response.message_uuid else "",
                    "cost": 0.0075,
                    "status_raw": "sent"
                }
            else:
                xml_content = f'<Response><Speak voice="{options.get("voice", "MAN")}" language="{options.get("language", "en-US")}">{message}</Speak></Response>'
                response = client.calls.create(
                    from_=self.phone_number,
                    to=to,
                    answer_url="https://s3.amazonaws.com/plivosamplexml/speak_url.xml",
                    answer_method="GET"
                )
                return {
                    "status": "sent",
                    "provider": "plivo",
                    "call_uuid": response.request_uuid,
                    "cost": 0.05,
                    "duration": 0
                }
        except ImportError:
            logger.warning("plivo package not installed, simulating")
            await asyncio.sleep(0.3)
            return {"status": "sent", "cost": 0.0075, "provider": "plivo_simulated"}
        except Exception as e:
            logger.error(f"Plivo error: {e}")
            return {"status": "failed", "error": str(e)}

    async def _send_vonage(self, to: str, message: str,
                            msg_type: str,
                            options: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import vonage
            client = vonage.Client(key=self.account_sid, secret=self.auth_token)
            sms = vonage.Sms(client)
            if msg_type == "sms":
                response = sms.send_message({
                    "from": self.phone_number,
                    "to": to,
                    "text": message
                })
                if response["messages"][0]["status"] == "0":
                    return {"status": "sent", "provider": "vonage", "cost": 0.0075}
                return {"status": "failed", "error": response["messages"][0].get("error-text", "Unknown")}
            else:
                logger.warning("Vonage voice not fully implemented")
                return {"status": "failed", "error": "Voice not supported with Vonage"}
        except ImportError:
            logger.warning("vonage package not installed, simulating")
            await asyncio.sleep(0.3)
            return {"status": "sent", "cost": 0.0075, "provider": "vonage_simulated"}
        except Exception as e:
            logger.error(f"Vonage error: {e}")
            return {"status": "failed", "error": str(e)}

    async def create_template(self, template_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        template = {
            "id": template_id,
            "name": config.get("name", template_id),
            "body": config.get("body", ""),
            "voice_body": config.get("voice_body", config.get("body", "")),
            "type": config.get("type", "sms"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "variables": self._extract_variables(config.get("body", "")),
            "metadata": config.get("metadata", {})
        }
        self.templates[template_id] = template
        self._save_templates()
        return template

    def _extract_variables(self, text: str) -> List[str]:
        import re
        return re.findall(r'\{\{(\w+)\}\}', text)

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        return self.templates.get(template_id)

    async def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        templates = list(self.templates.values())
        if template_type:
            templates = [t for t in templates if t.get("type") == template_type]
        return templates

    async def delete_template(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
            return True
        return False

    async def create_escalation_chain(self, chain_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        chain = {
            "id": chain_id,
            "name": config.get("name", chain_id),
            "levels": config.get("levels", []),
            "timeout_seconds": config.get("timeout_seconds", 300),
            "repeat_count": config.get("repeat_count", 1),
            "created_at": self._now(),
            "updated_at": self._now(),
            "active": config.get("active", True),
            "metadata": config.get("metadata", {})
        }
        self.escalation_chains[chain_id] = chain
        self._save_chains()
        return chain

    async def get_escalation_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        return self.escalation_chains.get(chain_id)

    async def list_escalation_chains(self) -> List[Dict[str, Any]]:
        return list(self.escalation_chains.values())

    async def update_escalation_chain(self, chain_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        chain = self.escalation_chains.get(chain_id)
        if not chain:
            return None
        for key in ["name", "levels", "timeout_seconds", "repeat_count", "active", "metadata"]:
            if key in updates:
                chain[key] = updates[key]
        chain["updated_at"] = self._now()
        self._save_chains()
        return chain

    async def delete_escalation_chain(self, chain_id: str) -> bool:
        if chain_id in self.escalation_chains:
            del self.escalation_chains[chain_id]
            self._save_chains()
            return True
        return False

    async def execute_escalation_chain(self, chain_id: str, message: str,
                                        initial_recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        chain = self.escalation_chains.get(chain_id)
        if not chain:
            return {"status": "error", "message": f"Chain {chain_id} not found"}

        results = []
        for level_config in chain.get("levels", []):
            level_num = level_config.get("level", 1)
            recipients = level_config.get("recipients", initial_recipients if level_num == 1 else [])
            method = level_config.get("method", "sms")

            if not recipients:
                continue

            for recipient in recipients:
                phone = recipient.get("phone", "")
                name = recipient.get("name", "Unknown")

                if method == "sms":
                    result = await self.send_sms(phone, message)
                elif method == "voice":
                    result = await self.send_voice_call(phone, message)
                elif method == "both":
                    sms_result = await self.send_sms(phone, message)
                    voice_result = await self.send_voice_call(phone, message)
                    result = {"sms": sms_result, "voice": voice_result}
                else:
                    result = {"status": "unknown_method", "method": method}

                results.append({
                    "level": level_num,
                    "recipient": name,
                    "phone": self._mask_phone(phone),
                    "method": method,
                    "result": result
                })

            if level_num < len(chain.get("levels", [])):
                timeout = level_config.get("timeout", chain.get("timeout_seconds", 300))
                await asyncio.sleep(min(timeout, 60))

        return {
            "chain_id": chain_id,
            "chain_name": chain.get("name"),
            "results": results,
            "total_attempts": len(results),
            "completed_at": self._now()
        }

    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.delivery_log:
            if entry.get("id") == delivery_id:
                return entry
        return None

    async def get_delivery_history(self, limit: int = 100,
                                    status_filter: Optional[str] = None,
                                    type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        entries = list(reversed(self.delivery_log))
        if status_filter:
            entries = [e for e in entries if e.get("status") == status_filter]
        if type_filter:
            entries = [e for e in entries if e.get("type") == type_filter]
        return entries[:limit]

    async def get_cost_summary(self) -> Dict[str, Any]:
        total_cost = sum(e.get("cost", 0) for e in self.delivery_log)
        sms_cost = sum(e.get("cost", 0) for e in self.delivery_log if e.get("type") == "sms")
        voice_cost = sum(e.get("cost", 0) for e in self.delivery_log if e.get("type") == "voice")
        total_count = len(self.delivery_log)
        sms_count = sum(1 for e in self.delivery_log if e.get("type") == "sms")
        voice_count = sum(1 for e in self.delivery_log if e.get("type") == "voice")
        return {
            "total_cost": round(total_cost, 4),
            "sms_cost": round(sms_cost, 4),
            "voice_cost": round(voice_cost, 4),
            "total_messages": total_count,
            "sms_count": sms_count,
            "voice_count": voice_count,
            "average_cost_per_message": round(total_cost / total_count, 4) if total_count > 0 else 0
        }

    async def handle_inbound_sms(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from_number = payload.get("From", "")
        body = payload.get("Body", "")
        message_sid = payload.get("MessageSid", str(uuid.uuid4()))

        logger.info(f"Inbound SMS from {self._mask_phone(from_number)}: {body[:50]}")
        return {
            "status": "received",
            "from": self._mask_phone(from_number),
            "body_preview": body[:100],
            "message_sid": message_sid,
            "received_at": self._now()
        }

    async def initialize(self):
        logger.info("SMSVoiceNotificationManager initialized with provider=%s, sms=%s, voice=%s",
                     self.provider, self.sms_enabled, self.voice_enabled)

    async def close(self):
        self._save_log()
        self._save_templates()
        self._save_chains()
        logger.info("SMSVoiceNotificationManager closed")
