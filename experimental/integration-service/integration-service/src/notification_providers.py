"""Notification channel providers for email, webhook, and Telegram delivery."""
import asyncio
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class NotificationProvider:
    """Base class for notification providers."""

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        raise NotImplementedError


class EmailProvider(NotificationProvider):
    """Send notifications via SMTP email."""

    def __init__(self, config: Dict[str, Any]):
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user", "")
        self.smtp_pass = config.get("smtp_pass", "")
        self.from_addr = config.get("from_addr", "noreply@infrapilot.local")
        self.use_tls = config.get("use_tls", True)

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = recipient

            text_part = MIMEText(message, "plain", "utf-8")
            html_part = MIMEText(kwargs.get("html", message), "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)

            loop = asyncio.get_event_loop()

            def _send():
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls()
                    if self.smtp_user:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.from_addr, [recipient], msg.as_string())

            await loop.run_in_executor(None, _send)
            logger.info(f"Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False


class WebhookProvider(NotificationProvider):
    """Send notifications via HTTP webhook."""

    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get("webhook_url", "")
        self.method = config.get("method", "POST")
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.template = config.get("template", "default")

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            logger.error("No webhook URL configured")
            return False

        payload = {
            "event": kwargs.get("event", "notification"),
            "subject": subject,
            "message": message,
            "timestamp": kwargs.get("timestamp", ""),
            "source": "infra-pilot",
            "recipient": recipient,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    self.method,
                    self.webhook_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status < 400:
                        logger.info(f"Webhook sent to {self.webhook_url}: {subject}")
                        return True
                    else:
                        logger.error(f"Webhook returned {resp.status}: {await resp.text()}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send webhook to {self.webhook_url}: {e}")
            return False


class TelegramProvider(NotificationProvider):
    """Send notifications via Telegram bot."""

    def __init__(self, config: Dict[str, Any]):
        self.bot_token = config.get("bot_token", "")
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        if not self.bot_token:
            logger.error("No Telegram bot token configured")
            return False

        chat_id = recipient  # recipient is the chat ID for Telegram
        text = f"*{subject}*\n\n{message}"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Telegram message sent to chat {chat_id}")
                        return True
                    else:
                        logger.error(f"Telegram API returned {resp.status}: {await resp.text()}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False


class NotificationManager:
    """Manages notification delivery across multiple providers."""

    def __init__(self):
        self._providers: Dict[str, NotificationProvider] = {}

    def register_provider(self, name: str, provider: NotificationProvider):
        self._providers[name] = provider

    def unregister_provider(self, name: str):
        self._providers.pop(name, None)

    async def send_notification(
        self,
        channels: list[str],
        subject: str,
        message: str,
        recipients: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, bool]:
        """Send a notification through specified channels.

        Args:
            channels: List of provider names to send through
            subject: Notification subject
            message: Notification body
            recipients: Dict mapping provider names to recipient addresses
            **kwargs: Additional provider-specific options

        Returns:
            Dict mapping provider names to success status
        """
        recipients = recipients or {}
        results = {}

        for channel in channels:
            provider = self._providers.get(channel)
            if not provider:
                logger.warning(f"Unknown notification channel: {channel}")
                results[channel] = False
                continue

            recipient = recipients.get(channel, "")
            if not recipient:
                logger.warning(f"No recipient configured for channel: {channel}")
                results[channel] = False
                continue

            try:
                success = await provider.send(recipient, subject, message, **kwargs)
                results[channel] = success
            except Exception as e:
                logger.error(f"Error sending via {channel}: {e}")
                results[channel] = False

        return results
