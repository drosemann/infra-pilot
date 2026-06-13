import json
import os
import time
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class OpenTelemetryExporter:
    """OpenTelemetry Export - OTLP format traces, metrics, logs export"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = _data_file('telemetry_config.json')
        self.telemetry_config = self._load_config()
        self.sampling_rate = self.telemetry_config.get('sampling_rate', 1.0)
        self.endpoint = self.telemetry_config.get('endpoint', os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318'))
        self.headers = self.telemetry_config.get('headers', {})
        self.export_batch_size = self.telemetry_config.get('export_batch_size', 100)
        self.traces_buffer: List[Dict[str, Any]] = []
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.logs_buffer: List[Dict[str, Any]] = []

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load telemetry config: {e}")
        return {
            'sampling_rate': 1.0,
            'endpoint': os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318'),
            'headers': {},
            'export_batch_size': 100
        }

    def _save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.telemetry_config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save telemetry config: {e}")

    def _should_sample(self) -> bool:
        return random.random() < self.sampling_rate

    def _generate_span_id(self) -> str:
        return os.urandom(8).hex()

    def _generate_trace_id(self) -> str:
        return os.urandom(16).hex()

    def _otlp_encode_traces(self, spans: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'resourceSpans': [{
                'resource': {
                    'attributes': [{'key': 'service.name', 'value': {'stringValue': 'integration-service'}}]
                },
                'scopeSpans': [{
                    'scope': {'name': 'integration-service', 'version': '1.0.0'},
                    'spans': spans
                }]
            }]
        }

    def _otlp_encode_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'resourceMetrics': [{
                'resource': {
                    'attributes': [{'key': 'service.name', 'value': {'stringValue': 'integration-service'}}]
                },
                'scopeMetrics': [{
                    'scope': {'name': 'integration-service', 'version': '1.0.0'},
                    'metrics': metrics
                }]
            }]
        }

    def _otlp_encode_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'resourceLogs': [{
                'resource': {
                    'attributes': [{'key': 'service.name', 'value': {'stringValue': 'integration-service'}}]
                },
                'scopeLogs': [{
                    'scope': {'name': 'integration-service', 'version': '1.0.0'},
                    'logRecords': logs
                }]
            }]
        }

    def create_span(self, name: str, kind: str = 'INTERNAL', parent_span_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._should_sample():
            return None
        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()
        now_ns = int(time.time() * 1_000_000_000)
        span = {
            'traceId': trace_id,
            'spanId': span_id,
            'parentSpanId': parent_span_id or '',
            'name': name,
            'kind': {'INTERNAL': 1, 'SERVER': 2, 'CLIENT': 3, 'PRODUCER': 4, 'CONSUMER': 5}.get(kind, 1),
            'startTimeUnixNano': now_ns,
            'endTimeUnixNano': now_ns + 1_000_000,
            'attributes': [{'key': k, 'value': {'stringValue': str(v)}} for k, v in (attributes or {}).items()] if attributes else [],
            'status': {'code': 1}
        }
        return span

    async def export_traces(self, spans: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.traces_buffer.extend(spans)
        if len(self.traces_buffer) >= self.export_batch_size:
            return await self._flush_traces()
        return {'exported': len(spans), 'buffered': len(self.traces_buffer)}

    async def _flush_traces(self) -> Dict[str, Any]:
        if not self.traces_buffer:
            return {'exported': 0}
        batch = self.traces_buffer[:self.export_batch_size]
        self.traces_buffer = self.traces_buffer[self.export_batch_size:]
        body = self._otlp_encode_traces(batch)
        return await self._send(body, 'traces')

    async def export_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.metrics_buffer.extend(metrics)
        if len(self.metrics_buffer) >= self.export_batch_size:
            return await self._flush_metrics()
        return {'exported': len(metrics), 'buffered': len(self.metrics_buffer)}

    async def _flush_metrics(self) -> Dict[str, Any]:
        if not self.metrics_buffer:
            return {'exported': 0}
        batch = self.metrics_buffer[:self.export_batch_size]
        self.metrics_buffer = self.metrics_buffer[self.export_batch_size:]
        body = self._otlp_encode_metrics(batch)
        return await self._send(body, 'metrics')

    async def export_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.logs_buffer.extend(logs)
        if len(self.logs_buffer) >= self.export_batch_size:
            return await self._flush_logs()
        return {'exported': len(logs), 'buffered': len(self.logs_buffer)}

    async def _flush_logs(self) -> Dict[str, Any]:
        if not self.logs_buffer:
            return {'exported': 0}
        batch = self.logs_buffer[:self.export_batch_size]
        self.logs_buffer = self.logs_buffer[self.export_batch_size:]
        body = self._otlp_encode_logs(batch)
        return await self._send(body, 'logs')

    async def _send(self, body: Dict[str, Any], endpoint_type: str) -> Dict[str, Any]:
        import aiohttp
        try:
            url = f"{self.endpoint}/v1/{endpoint_type}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, headers={
                    'Content-Type': 'application/json',
                    **self.headers
                }, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return {'exported': True, 'count': len(body.get('resourceSpans', body.get('resourceMetrics', body.get('resourceLogs', [])))), 'status': resp.status}
                    return {'exported': False, 'status': resp.status, 'error': await resp.text()}
        except Exception as e:
            logger.warning(f"OTLP export failed for {endpoint_type}: {e}")
            return {'exported': False, 'error': str(e)}

    async def get_status(self) -> Dict[str, Any]:
        return {
            'endpoint': self.endpoint,
            'sampling_rate': self.sampling_rate,
            'export_batch_size': self.export_batch_size,
            'buffered_traces': len(self.traces_buffer),
            'buffered_metrics': len(self.metrics_buffer),
            'buffered_logs': len(self.logs_buffer),
            'configured': bool(self.endpoint)
        }

    async def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        for key in ['sampling_rate', 'endpoint', 'headers', 'export_batch_size']:
            if key in updates:
                self.telemetry_config[key] = updates[key]
                if key == 'sampling_rate':
                    self.sampling_rate = updates[key]
                elif key == 'endpoint':
                    self.endpoint = updates[key]
                elif key == 'headers':
                    self.headers = updates[key]
                elif key == 'export_batch_size':
                    self.export_batch_size = updates[key]
        self._save_config()
        return await self.get_status()

    async def initialize(self):
        logger.info("OpenTelemetryExporter initialized")

    async def close(self):
        await self._flush_traces()
        await self._flush_metrics()
        await self._flush_logs()
        logger.info("OpenTelemetryExporter closed")
