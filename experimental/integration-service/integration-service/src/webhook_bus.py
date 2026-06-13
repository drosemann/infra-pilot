import json
import os
import hmac
import hashlib
import asyncio
import time
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

WEBHOOK_EVENT_TYPES = [
    'server.*', 'server.created', 'server.started', 'server.stopped', 'server.deleted', 'server.error',
    'backup.*', 'backup.created', 'backup.restored', 'backup.failed',
    'alert.*', 'alert.created', 'alert.acknowledged', 'alert.resolved',
    'deployment.*', 'deployment.started', 'deployment.completed', 'deployment.failed',
    'user.*', 'user.created', 'user.updated', 'user.deleted',
]


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class WebhookEventBus:
    """Webhook Event Bus - Outgoing webhooks with retry, signing, and templating"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registrations_file = _data_file('webhook_registrations.json')
        self.deliveries_file = _data_file('webhook_deliveries.json')
        self.registrations: Dict[str, Dict[str, Any]] = {}
        self.deliveries: List[Dict[str, Any]] = []
        self.secret_key = config.get('webhook_secret', os.getenv('WEBHOOK_SECRET', 'default-webhook-secret'))
        self.max_retries = 5
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.registrations_file):
            try:
                with open(self.registrations_file, 'r') as f:
                    self.registrations = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load webhook registrations: {e}")
        if os.path.exists(self.deliveries_file):
            try:
                with open(self.deliveries_file, 'r') as f:
                    self.deliveries = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load deliveries: {e}")

    def _save_registrations(self):
        try:
            with open(self.registrations_file, 'w') as f:
                json.dump(self.registrations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registrations: {e}")

    def _save_deliveries(self):
        try:
            with open(self.deliveries_file, 'w') as f:
                json.dump(self.deliveries[-5000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save deliveries: {e}")

    def _generate_id(self) -> str:
        return f'wh_{int(time.time())}_{os.urandom(4).hex()}'

    def _sign_payload(self, payload: Dict[str, Any]) -> str:
        body = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        return hmac.new(
            self.secret_key.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

    def _apply_template(self, template: str, data: Dict[str, Any]) -> str:
        def replace_var(match):
            expr = match.group(1).strip()
            keys = expr.split('.')
            val = data
            for k in keys:
                if isinstance(val, dict):
                    val = val.get(k, '')
                else:
                    return match.group(0)
            return str(val) if not isinstance(val, (dict, list)) else json.dumps(val)
        return re.sub(r'\{\{(\s*[\w.]+\s*)\}\}', replace_var, template)

    def _format_payload(self, event_type: str, data: Dict[str, Any], registration: Dict[str, Any]) -> Dict[str, Any]:
        template = registration.get('template')
        if template:
            rendered = self._apply_template(template, {'event_type': event_type, 'data': data})
            try:
                return json.loads(rendered) if isinstance(rendered, str) else {'text': rendered}
            except (json.JSONDecodeError, TypeError):
                return {'text': rendered}
        return {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

    async def register_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        wh_id = self._generate_id()
        registration = {
            'id': wh_id,
            'url': data['url'],
            'event_types': data.get('event_types', ['*']),
            'template': data.get('template'),
            'headers': data.get('headers', {}),
            'name': data.get('name', ''),
            'active': data.get('active', True),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.registrations[wh_id] = registration
        self._save_registrations()
        return registration

    async def update_webhook(self, wh_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reg = self.registrations.get(wh_id)
        if not reg:
            return None
        for key in ['url', 'event_types', 'template', 'headers', 'name', 'active']:
            if key in data:
                reg[key] = data[key]
        reg['updated_at'] = datetime.now().isoformat()
        self._save_registrations()
        return reg

    async def delete_webhook(self, wh_id: str) -> bool:
        if wh_id in self.registrations:
            del self.registrations[wh_id]
            self._save_registrations()
            return True
        return False

    async def list_webhooks(self) -> List[Dict[str, Any]]:
        return list(self.registrations.values())

    async def get_webhook(self, wh_id: str) -> Optional[Dict[str, Any]]:
        return self.registrations.get(wh_id)

    async def get_deliveries(self, wh_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return [d for d in self.deliveries if d.get('webhook_id') == wh_id][-limit:]

    def _matches_event_type(self, registered_types: List[str], event_type: str) -> bool:
        for rt in registered_types:
            if rt == '*' or rt.endswith('.*'):
                prefix = rt[:-2]
                if not prefix or event_type.startswith(prefix):
                    return True
            elif rt == event_type:
                return True
        return False

    async def dispatch_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for wh_id, reg in self.registrations.items():
            if not reg.get('active', True):
                continue
            if not self._matches_event_type(reg.get('event_types', []), event_type):
                continue
            payload = self._format_payload(event_type, data, reg)
            signature = self._sign_payload(payload)
            headers = {
                **reg.get('headers', {}),
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': event_type,
                'Content-Type': 'application/json'
            }
            delivery_id = self._generate_id()
            delivery = {
                'id': delivery_id,
                'webhook_id': wh_id,
                'event_type': event_type,
                'payload': payload,
                'headers': headers,
                'status': 'pending',
                'attempts': 0,
                'created_at': datetime.now().isoformat()
            }
            self.deliveries.append(delivery)
            result = await self._deliver_with_retry(delivery, reg['url'], headers, payload)
            delivery['status'] = result.get('status', 'failed')
            delivery['attempts'] = result.get('attempts', 0)
            delivery['response'] = result.get('response')
            delivery['completed_at'] = datetime.now().isoformat()
            self._save_deliveries()
            results[wh_id] = result
        return {'event_type': event_type, 'deliveries': results}

    async def _deliver_with_retry(self, delivery: Dict[str, Any], url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        import aiohttp
        max_attempts = self.max_retries + 1
        for attempt in range(1, max_attempts + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status < 500:
                            return {'status': 'delivered', 'attempts': attempt, 'response': resp.status}
            except asyncio.TimeoutError:
                logger.warning(f"Webhook delivery timeout (attempt {attempt}/{max_attempts})")
            except Exception as e:
                logger.warning(f"Webhook delivery failed (attempt {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                wait = min(2 ** attempt * 10, 300)
                await asyncio.sleep(wait)
        return {'status': 'failed', 'attempts': max_attempts, 'response': None}

    async def test_webhook(self, wh_id: str) -> Dict[str, Any]:
        reg = self.registrations.get(wh_id)
        if not reg:
            return {'error': 'Webhook not found'}
        test_payload = {
            'event_type': 'test',
            'data': {'message': 'This is a test webhook delivery'},
            'timestamp': datetime.now().isoformat()
        }
        signature = self._sign_payload(test_payload)
        headers = {
            **reg.get('headers', {}),
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': 'test',
            'Content-Type': 'application/json'
        }
        result = await self._deliver_with_retry({'id': '', 'attempts': 0}, reg['url'], headers, test_payload)
        return {'webhook_id': wh_id, 'url': reg['url'], 'result': result}
