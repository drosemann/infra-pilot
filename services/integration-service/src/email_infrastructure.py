"""Feature 94: Email as Infrastructure - SMTP relay, inbound email webhook"""

import json
import os
import uuid
import smtplib
import asyncio
import logging
import email
import quopri
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formataddr, parseaddr, formatdate
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from email import policy
from email.parser import BytesParser

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class EmailInfrastructureManager:
    """Email infrastructure manager - SMTP relay, inbound webhook, templates"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.smtp_host = config.get("smtp_host", "smtp.example.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_use_tls = config.get("smtp_use_tls", True)
        self.smtp_username = config.get("smtp_username", "")
        self.smtp_password = config.get("smtp_password", "")
        self.default_from_email = config.get("from_email", "noreply@infrapilot.example.com")
        self.default_from_name = config.get("from_name", "Infra Pilot")
        self.max_recipients_per_message = config.get("max_recipients_per_message", 50)
        self.rate_limit_per_second = config.get("rate_limit_per_second", 10)
        self.dkim_selector = config.get("dkim_selector", "default")
        self.dkim_private_key = config.get("dkim_private_key", "")

        self.templates_file = _data_file('email_templates.json')
        self.delivery_log_file = _data_file('email_delivery_log.json')

        self.templates: Dict[str, Dict[str, Any]] = {}
        self.delivery_log: List[Dict[str, Any]] = []
        self._load_data()
        self._rate_limit_semaphore = asyncio.Semaphore(self.rate_limit_per_second)

    def _load_data(self):
        for filepath, target in [
            (self.templates_file, "templates"),
            (self.delivery_log_file, "log")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "templates":
                        self.templates = data
                    elif target == "log":
                        self.delivery_log = data[-10000:]
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_templates(self):
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    def _save_log(self):
        try:
            with open(self.delivery_log_file, 'w') as f:
                json.dump(self.delivery_log[-10000:], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save delivery log: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    async def send_email(self, to: str, subject: str, body: str,
                          html_body: Optional[str] = None,
                          from_email: Optional[str] = None,
                          from_name: Optional[str] = None,
                          cc: Optional[List[str]] = None,
                          bcc: Optional[List[str]] = None,
                          attachments: Optional[List[Dict[str, Any]]] = None,
                          headers: Optional[Dict[str, str]] = None,
                          template_id: Optional[str] = None,
                          template_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            subject = template.get("subject", subject)
            body = template.get("body", body)
            html_body = template.get("html_body", html_body)
            if template_vars:
                subject = self._apply_template_vars(subject, template_vars)
                body = self._apply_template_vars(body, template_vars)
                if html_body:
                    html_body = self._apply_template_vars(html_body, template_vars)

        delivery_id = self._generate_id()
        msg = self._build_message(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email or self.default_from_email,
            from_name=from_name or self.default_from_name,
            cc=cc or [],
            attachments=attachments or [],
            headers=headers or {}
        )

        all_recipients = [to] + (cc or []) + (bcc or [])
        masked_recipients = [self._mask_email(r) for r in all_recipients]

        entry = {
            "id": delivery_id,
            "to": masked_recipients[0] if masked_recipients else "",
            "to_full": all_recipients[0] if all_recipients else "",
            "cc": masked_recipients[1:len(cc or []) + 1] if cc else [],
            "subject": subject,
            "status": "queued",
            "created_at": self._now(),
            "sent_at": None,
            "error": None,
            "has_attachments": len(attachments or []) > 0,
            "template_id": template_id
        }

        try:
            async with self._rate_limit_semaphore:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._send_smtp, msg, all_recipients
                )
            entry["status"] = result.get("status", "sent")
            entry["sent_at"] = self._now()
            if result.get("status") == "failed":
                entry["error"] = result.get("error", "Unknown error")
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = str(e)
            logger.error(f"Email send failed to {masked_recipients[0]}: {e}")

        self.delivery_log.append(entry)
        self._save_log()
        return {
            "delivery_id": delivery_id,
            "status": entry["status"],
            "to": masked_recipients[0],
            "error": entry.get("error")
        }

    def _build_message(self, to: str, subject: str, body: str,
                        html_body: Optional[str],
                        from_email: str, from_name: str,
                        cc: List[str],
                        attachments: List[Dict[str, Any]],
                        headers: Dict[str, str]) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name, from_email))
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = f"<{self._generate_id()}@infrapilot>"

        if cc:
            msg["Cc"] = ", ".join(cc)

        for key, value in headers.items():
            msg[key] = value

        msg.attach(MIMEText(body, "plain", "utf-8"))

        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        if attachments:
            msg_outer = MIMEMultipart("mixed")
            msg_outer.attach(msg)
            for attachment in attachments:
                part = MIMEBase(
                    attachment.get("type", "application"),
                    attachment.get("subtype", "octet-stream")
                )
                part.set_payload(attachment.get("content", b""))
                filename = attachment.get("filename", "attachment.bin")
                if isinstance(part.get_payload(), str):
                    pass
                else:
                    import email.encoders
                    email.encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{filename}\""
                )
                msg_outer.attach(part)
            return msg_outer

        return msg

    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> Dict[str, Any]:
        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            text = msg.as_string()
            server.sendmail(
                msg["From"],
                recipients,
                text.encode("utf-8")
            )
            server.quit()
            return {"status": "sent"}
        except smtplib.SMTPAuthenticationError as e:
            return {"status": "failed", "error": f"SMTP authentication failed: {e}"}
        except smtplib.SMTPRecipientsRefused as e:
            return {"status": "failed", "error": f"Recipients refused: {e}"}
        except smtplib.SMTPServerDisconnected as e:
            return {"status": "failed", "error": f"Server disconnected: {e}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _mask_email(self, email_addr: str) -> str:
        name, addr = parseaddr(email_addr)
        if addr and "@" in addr:
            local, domain = addr.split("@", 1)
            if len(local) >= 3:
                masked = local[0] + "***" + local[-1]
            else:
                masked = local[0] + "***"
            masked_addr = f"{masked}@{domain}"
            if name:
                return f"{name} <{masked_addr}>"
            return masked_addr
        return email_addr

    def _apply_template_vars(self, text: str, vars: Dict[str, Any]) -> str:
        result = text
        for key, value in vars.items():
            result = result.replace("{{" + key + "}}", str(value))
        return result

    async def send_templated_email(self, template_id: str, to: str,
                                    template_vars: Dict[str, Any],
                                    from_email: Optional[str] = None,
                                    from_name: Optional[str] = None) -> Dict[str, Any]:
        template = self.templates.get(template_id)
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}

        subject = self._apply_template_vars(template.get("subject", ""), template_vars)
        body = self._apply_template_vars(template.get("body", ""), template_vars)
        html_body = None
        if template.get("html_body"):
            html_body = self._apply_template_vars(template["html_body"], template_vars)

        return await self.send_email(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
            template_id=template_id
        )

    async def handle_inbound_email(self, raw_email: bytes,
                                    webhook_source: str = "smtp") -> Dict[str, Any]:
        try:
            parser = BytesParser(policy=policy.default)
            parsed = parser.parsebytes(raw_email)

            from_addr = parsed.get("From", "")
            to_addr = parsed.get("To", "")
            cc_addr = parsed.get("Cc", "")
            subject = parsed.get("Subject", "")
            message_id = parsed.get("Message-ID", str(uuid.uuid4()))
            references = parsed.get("References", "")

            body_text = ""
            body_html = ""
            attachments = []

            if parsed.is_multipart():
                for part in parsed.walk():
                    content_type = part.get_content_type()
                    content_disp = str(part.get("Content-Disposition", ""))

                    if "attachment" in content_disp:
                        filename = part.get_filename() or f"attachment_{len(attachments)}"
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b""),
                            "content": base64.b64encode(part.get_payload(decode=True) or b"").decode()
                        })
                    elif content_type == "text/plain":
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            body_text = part.get_payload(decode=True).decode(charset, errors="replace")
                        except Exception:
                            body_text = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    elif content_type == "text/html":
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            body_html = part.get_payload(decode=True).decode(charset, errors="replace")
                        except Exception:
                            body_html = part.get_payload(decode=True).decode("utf-8", errors="replace")
            else:
                charset = parsed.get_content_charset() or "utf-8"
                try:
                    body_text = parsed.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    body_text = parsed.get_payload(decode=True).decode("utf-8", errors="replace")

            inbound_record = {
                "id": self._generate_id(),
                "from": from_addr,
                "to": to_addr,
                "cc": cc_addr,
                "subject": subject,
                "message_id": message_id,
                "references": references,
                "body_text_preview": body_text[:500],
                "body_html_truncated": body_html[:200] if body_html else None,
                "has_html": bool(body_html),
                "attachments": attachments,
                "attachment_count": len(attachments),
                "received_at": self._now(),
                "webhook_source": webhook_source
            }

            logger.info(f"Inbound email from {from_addr}: {subject}")
            return inbound_record

        except Exception as e:
            logger.error(f"Failed to parse inbound email: {e}")
            return {
                "id": self._generate_id(),
                "error": str(e),
                "received_at": self._now(),
                "raw_size": len(raw_email)
            }

    async def create_template(self, template_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        template = {
            "id": template_id,
            "name": config.get("name", template_id),
            "subject": config.get("subject", ""),
            "body": config.get("body", ""),
            "html_body": config.get("html_body", ""),
            "category": config.get("category", "general"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "variables": self._extract_variables(config.get("body", "") + config.get("subject", "")),
            "metadata": config.get("metadata", {})
        }
        self.templates[template_id] = template
        self._save_templates()
        return template

    def _extract_variables(self, text: str) -> List[str]:
        import re
        return list(set(re.findall(r'\{\{(\w+)\}\}', text)))

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        return self.templates.get(template_id)

    async def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.get("category") == category]
        return templates

    async def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        template = self.templates.get(template_id)
        if not template:
            return None
        for key in ["name", "subject", "body", "html_body", "category", "metadata"]:
            if key in updates:
                template[key] = updates[key]
        template["updated_at"] = self._now()
        template["variables"] = self._extract_variables(
            template.get("body", "") + template.get("subject", "")
        )
        self._save_templates()
        return template

    async def delete_template(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
            return True
        return False

    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.delivery_log:
            if entry.get("id") == delivery_id:
                return entry
        return None

    async def get_delivery_stats(self) -> Dict[str, Any]:
        total = len(self.delivery_log)
        sent = sum(1 for e in self.delivery_log if e.get("status") == "sent")
        failed = sum(1 for e in self.delivery_log if e.get("status") == "failed")
        queued = sum(1 for e in self.delivery_log if e.get("status") == "queued")
        with_attachments = sum(1 for e in self.delivery_log if e.get("has_attachments"))
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "queued": queued,
            "with_attachments": with_attachments,
            "success_rate": round(sent / total * 100, 2) if total > 0 else 0
        }

    async def verify_email_address(self, email_address: str) -> Dict[str, Any]:
        name, addr = parseaddr(email_address)
        if not addr or "@" not in addr:
            return {"address": email_address, "valid": False, "reason": "Invalid format"}
        domain = addr.split("@", 1)[1]
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_format = bool(re.match(pattern, addr))
        return {
            "address": email_address,
            "parsed": addr,
            "domain": domain,
            "valid": valid_format,
            "format_valid": valid_format
        }

    async def initialize(self):
        logger.info("EmailInfrastructureManager initialized with SMTP %s:%d TLS=%s",
                     self.smtp_host, self.smtp_port, self.smtp_use_tls)

    async def close(self):
        self._save_log()
        self._save_templates()
        logger.info("EmailInfrastructureManager closed")
