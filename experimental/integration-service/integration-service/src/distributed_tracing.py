from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import uuid

logger = logging.getLogger(__name__)


class TraceQueryEngine:
    """Simple in-memory trace query engine for span aggregation and flamegraph generation"""

    def __init__(self):
        self.spans: List[Dict[str, Any]] = []

    def ingest_spans(self, spans: List[Dict[str, Any]]):
        self.spans.extend(spans)

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.spans if s['traceId'] == trace_id]

    def search_by_service(self, service: str, limit: int = 100) -> List[Dict[str, Any]]:
        results = [s for s in self.spans if s.get('service') == service]
        return results[-limit:]

    def search(self, service: Optional[str] = None, operation: Optional[str] = None,
               min_duration: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.spans
        if service:
            results = [s for s in results if s.get('service') == service]
        if operation:
            results = [s for s in results if s.get('operation') == operation]
        if min_duration is not None:
            results = [s for s in results if s.get('duration', 0) >= min_duration]
        return results[-limit:]

    def get_flamegraph(self, trace_id: str) -> Dict[str, Any]:
        spans = self.get_trace(trace_id)
        spans.sort(key=lambda s: s.get('startTime', 0))
        root = None
        for s in spans:
            if not s.get('parentSpanId'):
                root = s
                break
        if not root and spans:
            root = spans[0]
        levels = []
        if root:
            levels = self._build_flamegraph_levels(spans, root['spanId'], 0)
        return {'traceId': trace_id, 'root': root, 'levels': levels, 'totalSpans': len(spans)}

    def _build_flamegraph_levels(self, spans: List[Dict[str, Any]], parent_id: str, depth: int) -> List[Dict[str, Any]]:
        children = [s for s in spans if s.get('parentSpanId') == parent_id]
        if not children:
            return []
        level = {
            'depth': depth,
            'spans': [{
                'spanId': c['spanId'],
                'operation': c.get('operation', ''),
                'service': c.get('service', ''),
                'duration': c.get('duration', 0),
                'startTime': c.get('startTime', 0)
            } for c in children]
        }
        result = [level]
        for c in children:
            deeper = self._build_flamegraph_levels(spans, c['spanId'], depth + 1)
            result.extend(deeper)
        return result

    def get_dependencies(self) -> Dict[str, Any]:
        services = set()
        edges = []
        for s in self.spans:
            svc = s.get('service')
            if svc:
                services.add(svc)
            parent_id = s.get('parentSpanId')
            if parent_id:
                parent = next((p for p in self.spans if p['spanId'] == parent_id), None)
                if parent and parent.get('service') != svc:
                    edges.append({
                        'source': parent.get('service', 'unknown'),
                        'target': svc,
                        'calls': 1
                    })
        merged = {}
        for e in edges:
            key = f"{e['source']}->{e['target']}"
            if key in merged:
                merged[key]['calls'] += 1
            else:
                merged[key] = dict(e)
        return {
            'services': list(services),
            'edges': list(merged.values()),
            'totalSpans': len(self.spans)
        }


class DistributedTracingManager:
    """Distributed tracing with trace context propagation, span collection, and latency analysis"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.traces_file = config.get('traces_file', 'data/traces.json')
        self.engine = TraceQueryEngine()
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.traces_file):
            try:
                with open(self.traces_file, 'r') as f:
                    spans = json.load(f)
                    self.engine.ingest_spans(spans)
            except Exception as e:
                logger.warning(f"Failed to load traces: {e}")

    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.traces_file), exist_ok=True)
            with open(self.traces_file, 'w') as f:
                json.dump(self.engine.spans[-10000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save traces: {e}")

    async def ingest_spans(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for span in spans:
            span.setdefault('spanId', str(uuid.uuid4()))
            span.setdefault('traceId', str(uuid.uuid4()))
            span.setdefault('tags', {})
            span.setdefault('startTime', datetime.now().timestamp() * 1000)
        self.engine.ingest_spans(spans)
        self._save_data()
        return spans

    async def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        return self.engine.get_trace(trace_id)

    async def search_traces(self, service: Optional[str] = None, operation: Optional[str] = None,
                            min_duration: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.engine.search(service, operation, min_duration, limit)

    async def get_flamegraph(self, trace_id: str) -> Dict[str, Any]:
        return self.engine.get_flamegraph(trace_id)

    async def get_dependencies(self) -> Dict[str, Any]:
        return self.engine.get_dependencies()
