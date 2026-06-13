from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import math

logger = logging.getLogger(__name__)


class SLOTracker:
    """SLA / SLO tracking with SLI measurement, error budget calculation, and burn rate alerts"""

    SLI_TYPES = ['uptime', 'latency_p50', 'latency_p95', 'latency_p99', 'error_rate', 'backup_success_rate']

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.definitions_file = config.get('slo_definitions_file', 'data/slo_definitions.json')
        self.measurements_file = config.get('sli_measurements_file', 'data/sli_measurements.json')
        self.definitions: List[Dict[str, Any]] = []
        self.measurements: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.definitions_file, 'definitions'), (self.measurements_file, 'measurements')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_definitions(self):
        try:
            os.makedirs(os.path.dirname(self.definitions_file), exist_ok=True)
            with open(self.definitions_file, 'w') as f:
                json.dump(self.definitions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save SLO definitions: {e}")

    def _save_measurements(self):
        try:
            os.makedirs(os.path.dirname(self.measurements_file), exist_ok=True)
            with open(self.measurements_file, 'w') as f:
                json.dump(self.measurements[-10000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save SLI measurements: {e}")

    async def create_slo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sli_type = data.get('sli_type', 'uptime')
        if sli_type not in self.SLI_TYPES:
            return {'error': f'Unsupported SLI type: {sli_type}. Valid: {self.SLI_TYPES}'}
        slo = {
            'id': f'slo_{int(datetime.now().timestamp())}_{len(self.definitions)}',
            'name': data.get('name', 'Unnamed SLO'),
            'description': data.get('description', ''),
            'sli_type': sli_type,
            'target': data.get('target', 99.9),
            'window_days': data.get('window_days', 30),
            'created_at': datetime.now().isoformat(),
            'active': True,
            'tags': data.get('tags', []),
            'burn_rate_threshold': data.get('burn_rate_threshold', 2.0)
        }
        self.definitions.append(slo)
        self._save_definitions()
        return slo

    async def get_slos(self) -> List[Dict[str, Any]]:
        return self.definitions

    async def update_slo(self, slo_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for slo in self.definitions:
            if slo['id'] == slo_id:
                slo.update(updates)
                slo['updated_at'] = datetime.now().isoformat()
                self._save_definitions()
                return slo
        return None

    async def delete_slo(self, slo_id: str) -> bool:
        for i, slo in enumerate(self.definitions):
            if slo['id'] == slo_id:
                self.definitions.pop(i)
                self._save_definitions()
                return True
        return False

    async def get_slo_status(self, slo_id: str) -> Optional[Dict[str, Any]]:
        slo = next((s for s in self.definitions if s['id'] == slo_id), None)
        if not slo:
            return None
        relevant = [m for m in self.measurements if m.get('slo_id') == slo_id]
        window = datetime.now() - timedelta(days=slo.get('window_days', 30))
        relevant = [m for m in relevant if datetime.fromisoformat(m['timestamp']) > window]
        total = len(relevant)
        good = sum(1 for m in relevant if m.get('passed', False))
        current_sli = (good / total * 100) if total > 0 else 100.0
        return {
            'slo_id': slo_id,
            'name': slo.get('name'),
            'target': slo.get('target'),
            'current_sli': round(current_sli, 4),
            'total_measurements': total,
            'good_measurements': good,
            'status': 'at_risk' if current_sli < slo.get('target', 99.9) else 'healthy'
        }

    async def get_error_budget(self, slo_id: str) -> Optional[Dict[str, Any]]:
        status = await self.get_slo_status(slo_id)
        if not status:
            return None
        target = status['target']
        sli = status['current_sli']
        total = status['total_measurements']
        allowed_bad = math.ceil(total * (100 - target) / 100)
        actual_bad = total - status['good_measurements']
        remaining_budget = allowed_bad - actual_bad
        return {
            'slo_id': slo_id,
            'total_measurements': total,
            'allowed_bad_events': allowed_bad,
            'actual_bad_events': actual_bad,
            'remaining_budget': max(remaining_budget, 0),
            'budget_consumed_percent': round((actual_bad / allowed_bad * 100) if allowed_bad > 0 else 0, 2),
            'status': 'exhausted' if remaining_budget <= 0 else 'healthy'
        }

    async def record_sli(self, data: Dict[str, Any]) -> Dict[str, Any]:
        measurement = {
            'id': f'sli_{int(datetime.now().timestamp())}_{len(self.measurements)}',
            'slo_id': data.get('slo_id', ''),
            'value': data.get('value', 0),
            'passed': data.get('passed', True),
            'timestamp': datetime.now().isoformat(),
            'source': data.get('source', 'manual')
        }
        self.measurements.append(measurement)
        self._save_measurements()
        return measurement

    async def check_burn_rate(self, slo_id: str) -> Optional[Dict[str, Any]]:
        slo = next((s for s in self.definitions if s['id'] == slo_id), None)
        if not slo:
            return None
        threshold = slo.get('burn_rate_threshold', 2.0)
        recent = [m for m in self.measurements if m.get('slo_id') == slo_id
                  and datetime.fromisoformat(m['timestamp']) > datetime.now() - timedelta(hours=1)]
        if not recent:
            return {'alert': False, 'reason': 'Insufficient data'}
        failure_rate = sum(1 for m in recent if not m.get('passed', True)) / len(recent) * 100
        budget = slo.get('target', 99.9)
        expected_failure_rate = 100 - budget
        burn_rate = (failure_rate / expected_failure_rate) if expected_failure_rate > 0 else 0
        return {
            'slo_id': slo_id,
            'burn_rate': round(burn_rate, 2),
            'failure_rate_1h': round(failure_rate, 2),
            'alert': burn_rate >= threshold,
            'threshold': threshold
        }
