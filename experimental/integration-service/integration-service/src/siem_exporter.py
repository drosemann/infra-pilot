from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import socket
import ssl
import asyncio

logger = logging.getLogger(__name__)


class SIEMExporter:
    """Stream audit logs to Splunk/ELK/Datadog/syslog with structured JSON and TLS"""

    FORMATS = ['splunk_hec', 'elastic_bulk', 'datadog', 'syslog_rfc5424']

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.targets_file = config.get('siem_targets_file', 'data/siem_targets.json')
        self.export_log_file = config.get('siem_export_log_file', 'data/siem_export_log.json')
        self.targets: Dict[str, Any] = {}
        self.export_log: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        for path, attr in [
            (self.targets_file, 'targets'),
            (self.export_log_file, 'export_log'),
        ]:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")

    def _save(self, attr: str, path: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(getattr(self, attr), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")

    def _format_splunk_hec(self, events: List[Dict[str, Any]]) -> str:
        lines = []
        for event in events:
            hec = {
                'time': datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat())).timestamp(),
                'event': event,
                'sourcetype': event.get('sourcetype', 'infra_pilot:audit'),
                'source': event.get('source', 'integration_service'),
                'host': event.get('host', socket.gethostname()),
            }
            lines.append(json.dumps(hec))
        return '\n'.join(lines)

    def _format_elastic_bulk(self, events: List[Dict[str, Any]]) -> str:
        lines = []
        for event in events:
            action = {'index': {'_index': event.get('index', 'infra-pilot-audit'), '_id': event.get('id', '')}}
            lines.append(json.dumps(action))
            lines.append(json.dumps(event))
        return '\n'.join(lines) + '\n'

    def _format_datadog(self, events: List[Dict[str, Any]]) -> str:
        series = []
        for event in events:
            series.append({
                'metric': event.get('metric', 'infra_pilot.audit.event'),
                'points': [{'timestamp': int(datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat())).timestamp()), 'value': 1}],
                'tags': [f"{k}:{v}" for k, v in event.get('tags', {}).items()],
                'host': event.get('host', socket.gethostname()),
            })
        return json.dumps({'series': series})

    def _format_syslog_rfc5424(self, events: List[Dict[str, Any]]) -> str:
        lines = []
        hostname = socket.gethostname()
        for event in events:
            ts = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))
            msg = json.dumps(event)
            priority = event.get('priority', 14)  # default: info
            app_name = event.get('app_name', 'InfraPilot')
            procid = event.get('procid', '-')
            msgid = event.get('msgid', 'AUDIT')
            lines.append(
                f"<{priority}>1 {ts.strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {hostname} {app_name} {procid} {msgid} [audit@1] {msg}"
            )
        return '\n'.join(lines)

    async def add_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        target_id = target.get('id', f'target_{len(self.targets)}_{int(datetime.now().timestamp())}')
        target['id'] = target_id
        target['format'] = target.get('format', 'splunk_hec')
        if target['format'] not in self.FORMATS:
            return {'error': f"Unsupported format. Choose from: {', '.join(self.FORMATS)}"}
        target['created_at'] = datetime.now().isoformat()
        target['enabled'] = target.get('enabled', True)
        target['tls_verify'] = target.get('tls_verify', True)
        self.targets[target_id] = target
        self._save('targets', self.targets_file)
        return target

    async def get_targets(self) -> Dict[str, Any]:
        return self.targets

    async def update_target(self, target_id: str, updates: Dict[str, Any]) -> bool:
        target = self.targets.get(target_id)
        if not target:
            return False
        target.update(updates)
        target['updated_at'] = datetime.now().isoformat()
        self.targets[target_id] = target
        self._save('targets', self.targets_file)
        return True

    async def delete_target(self, target_id: str) -> bool:
        if target_id in self.targets:
            del self.targets[target_id]
            self._save('targets', self.targets_file)
            return True
        return False

    async def export_now(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {}
        for tid, target in self.targets.items():
            if not target.get('enabled', True):
                continue

            fmt = target.get('format', 'splunk_hec')
            formatters = {
                'splunk_hec': self._format_splunk_hec,
                'elastic_bulk': self._format_elastic_bulk,
                'datadog': self._format_datadog,
                'syslog_rfc5424': self._format_syslog_rfc5424,
            }
            formatter = formatters.get(fmt)
            if not formatter:
                continue

            payload = formatter(events)
            endpoint = target.get('endpoint', '')
            token = target.get('token', '')

            try:
                if fmt == 'syslog_rfc5424':
                    success = await self._send_syslog(target, payload)
                else:
                    success = await self._send_http(target, payload, token)
            except Exception as e:
                success = False
                logger.error(f"Export to {tid} failed: {e}")

            results[tid] = {'success': success, 'target_name': target.get('name', tid), 'format': fmt}
            self._log_export(tid, len(events), success)
        return results

    async def _send_http(self, target: Dict[str, Any], payload: str, token: str) -> bool:
        import aiohttp
        headers = {'Content-Type': 'application/json'}
        if token:
            if target.get('format') == 'splunk_hec':
                headers['Authorization'] = f'Splunk {token}'
            elif target.get('format') == 'datadog':
                headers['DD-API-Key'] = token
            elif target.get('format') == 'elastic_bulk':
                headers['Authorization'] = f'ApiKey {token}'

        connector = None
        if target.get('tls_verify') is False:
            connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(target.get('endpoint', ''), data=payload, headers=headers, timeout=30) as resp:
                return resp.status in (200, 201, 202, 204)

    async def _send_syslog(self, target: Dict[str, Any], payload: str) -> bool:
        try:
            host = target.get('host', 'localhost')
            port = target.get('port', 514)
            use_tls = target.get('tls', False)

            if use_tls:
                context = ssl.create_default_context()
                if not target.get('tls_verify', True):
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                reader, writer = await asyncio.open_connection(host, port, ssl=context)
            else:
                reader, writer = await asyncio.open_connection(host, port)

            writer.write(payload.encode('utf-8'))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            logger.error(f"Syslog send failed: {e}")
            return False

    def _log_export(self, target_id: str, event_count: int, success: bool):
        self.export_log.append({
            'target_id': target_id,
            'event_count': event_count,
            'success': success,
            'timestamp': datetime.now().isoformat(),
        })
        self._save('export_log', self.export_log_file)

    async def get_export_log(self) -> List[Dict[str, Any]]:
        return self.export_log[-500:]

    async def test_target(self, target_id: str) -> Dict[str, Any]:
        target = self.targets.get(target_id)
        if not target:
            return {'error': 'Target not found'}

        test_event = [{
            'id': 'test_event',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'test',
            'message': 'SIEM connectivity test',
            'source': 'integration_service',
            'host': socket.gethostname(),
            'tags': {'test': 'true'},
        }]

        try:
            result = await self.export_now(test_event)
            return {'target_id': target_id, 'result': result.get(target_id, {}), 'test': True}
        except Exception as e:
            return {'target_id': target_id, 'error': str(e), 'test': True}
