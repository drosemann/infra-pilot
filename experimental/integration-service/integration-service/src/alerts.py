from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """Unified alert system with delivery channels (Discord, in-game, email, webhook)"""

    CHANNELS = ['discord', 'in_game', 'email', 'webhook']

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alerts_file = config.get('alerts_file', 'alerts.json')
        self.channels_file = config.get('channels_file', 'alert_channels.json')
        self.alerts: List[Dict[str, Any]] = []
        self.channels: Dict[str, Dict[str, Any]] = {
            'discord': {'webhook_url': config.get('discord_webhook'), 'enabled': True},
            'in_game': {'endpoint': config.get('minecraft_webhook'), 'enabled': True},
            'email': {'smtp_server': config.get('smtp_server'), 'enabled': False},
            'webhook': {'url': '', 'enabled': True}
        }
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    self.alerts = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load alerts: {e}")
        if os.path.exists(self.channels_file):
            try:
                with open(self.channels_file, 'r') as f:
                    loaded = json.load(f)
                    self.channels.update(loaded)
            except Exception as e:
                logger.warning(f"Failed to load channels: {e}")

    def _save_alerts(self):
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump(self.alerts[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")

    def _save_channels(self):
        try:
            with open(self.channels_file, 'w') as f:
                json.dump(self.channels, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save channels: {e}")

    async def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        alert = {
            'id': f'alert_{len(self.alerts)}_{int(datetime.now().timestamp())}',
            'title': alert_data.get('title', 'Untitled Alert'),
            'message': alert_data.get('message', ''),
            'severity': alert_data.get('severity', 'info'),
            'source': alert_data.get('source', 'integration_service'),
            'channels': alert_data.get('channels', self.CHANNELS),
            'created_at': datetime.now().isoformat(),
            'acknowledged': False,
            'acknowledged_by': None,
            'acknowledged_at': None,
            'resolved': False
        }
        self.alerts.append(alert)
        self._save_alerts()
        await self._deliver_alert(alert)
        return alert

    async def _deliver_alert(self, alert: Dict[str, Any]):
        for channel in alert.get('channels', []):
            channel_config = self.channels.get(channel, {})
            if not channel_config.get('enabled', True):
                continue
            try:
                await self._send_to_channel(channel, channel_config, alert)
            except Exception as e:
                logger.warning(f"Alert delivery to {channel} failed: {e}")

    async def _send_to_channel(self, channel: str, config: Dict[str, Any], alert: Dict[str, Any]):
        import aiohttp
        if channel == 'discord':
            webhook = config.get('webhook_url')
            if webhook:
                async with aiohttp.ClientSession() as session:
                    embed = {
                        'embeds': [{
                            'title': f"{'🔴' if alert['severity'] == 'critical' else '🟡' if alert['severity'] == 'warning' else '🔵'} {alert['title']}",
                            'description': alert['message'],
                            'color': 0xFF0000 if alert['severity'] == 'critical' else 0xFFAA00 if alert['severity'] == 'warning' else 0x007BFF,
                            'timestamp': alert['created_at']
                        }]
                    }
                    await session.post(webhook, json=embed)
        elif channel == 'in_game':
            endpoint = config.get('endpoint')
            if endpoint:
                async with aiohttp.ClientSession() as session:
                    await session.post(endpoint, json={
                        'message': f"[ALERT] {alert['title']}: {alert['message']}",
                        'platform': 'alert'
                    })
        elif channel == 'webhook':
            url = config.get('url')
            if url:
                async with aiohttp.ClientSession() as session:
                    await session.post(url, json=alert)

    async def get_alerts(self, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.alerts
        if status == 'unacknowledged':
            results = [a for a in results if not a['acknowledged']]
        elif status == 'acknowledged':
            results = [a for a in results if a['acknowledged']]
        elif status == 'resolved':
            results = [a for a in results if a['resolved']]
        if severity:
            results = [a for a in results if a['severity'] == severity]
        return results[-limit:]

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_by'] = user_id
                alert['acknowledged_at'] = datetime.now().isoformat()
                self._save_alerts()
                return True
        return False

    async def configure_channel(self, channel_type: str, config: Dict[str, Any]) -> bool:
        if channel_type in self.channels:
            self.channels[channel_type].update(config)
            self._save_channels()
            return True
        return False

    async def send_alert_notification(self, alert: dict, notification_manager):
        """Send alert via configured notification channels."""
        channels = alert.get("notification_channels", [])
        if not channels:
            return

        subject = f"ALERT: {alert.get('name', 'Unknown')} - {alert.get('severity', 'info').upper()}"
        message = (
            f"Alert: {alert.get('name')}\n"
            f"Severity: {alert.get('severity')}\n"
            f"Metric: {alert.get('metric')}\n"
            f"Value: {alert.get('current_value')}\n"
            f"Threshold: {alert.get('threshold')}\n"
            f"Time: {alert.get('triggered_at')}\n"
            f"App: {alert.get('app_id', 'N/A')}"
        )

        await notification_manager.send_notification(
            channels=channels,
            subject=subject,
            message=message,
            recipients={c: alert.get(f"{c}_recipient", "") for c in channels},
            event="alert_triggered",
            timestamp=alert.get("triggered_at", ""),
        )
