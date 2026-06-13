import json
import os
import logging
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class LogAnomalyDetector:
    """Collect logs from all services and detect anomalies using statistical methods."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_file = config.get('log_anomalies_file', 'data/log_anomalies.json')
        self.logs: List[Dict[str, Any]] = []
        self.anomalies: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.data_file) as f:
                data = json.load(f)
                self.logs = data.get('logs', [])
                self.anomalies = data.get('anomalies', [])
        except:
            self.logs = []
            self.anomalies = []

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'logs': self.logs[-5000:], 'anomalies': self.anomalies[-1000:]}, f, indent=2)

    async def ingest_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            'id': f'log_{len(self.logs)}_{int(datetime.now().timestamp())}',
            'service': log_entry.get('service', 'unknown'),
            'level': log_entry.get('level', 'info'),
            'message': log_entry.get('message', ''),
            'source': log_entry.get('source', ''),
            'timestamp': log_entry.get('timestamp', datetime.now().isoformat()),
            'metadata': log_entry.get('metadata', {}),
            'ingested_at': datetime.now().isoformat()
        }
        self.logs.append(entry)
        anomaly = self._detect_anomaly(entry)
        if anomaly:
            self.anomalies.append(anomaly)
            self._save()
            return {'log': entry, 'anomaly': anomaly}
        self._save()
        return {'log': entry, 'anomaly': None}

    def _detect_anomaly(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        level = entry.get('level', 'info')
        if level in ('critical', 'error'):
            recent = [l for l in self.logs[-100:] if l['service'] == entry.get('service')]
            error_rate = sum(1 for l in recent if l['level'] in ('error', 'critical')) / max(len(recent), 1)
            return {
                'id': f'anomaly_{len(self.anomalies)}_{int(datetime.now().timestamp())}',
                'type': 'error_spike' if error_rate > 0.3 else 'high_severity_log',
                'severity': level,
                'service': entry.get('service'),
                'message': entry.get('message', ''),
                'log_id': entry['id'],
                'details': {'error_rate': round(error_rate, 3), 'recent_count': len(recent)},
                'detected_at': datetime.now().isoformat(),
                'feedback': None
            }

        response_times = [l.get('metadata', {}).get('response_time_ms') for l in self.logs[-200:]
                          if l.get('metadata', {}).get('response_time_ms') is not None]
        if response_times:
            recent_time = entry.get('metadata', {}).get('response_time_ms')
            if recent_time is not None:
                mean = statistics.mean(response_times)
                stdev = statistics.stdev(response_times) if len(response_times) > 1 else 0
                if stdev > 0 and abs(recent_time - mean) / stdev > 3:
                    return {
                        'id': f'anomaly_{len(self.anomalies)}_{int(datetime.now().timestamp())}',
                        'type': 'z_score_anomaly',
                        'severity': 'warning',
                        'service': entry.get('service'),
                        'message': f'Response time {recent_time}ms is {abs(recent_time - mean) / stdev:.1f} stddevs from mean',
                        'log_id': entry['id'],
                        'details': {'value': recent_time, 'mean': round(mean, 2), 'stddev': round(stdev, 2), 'z_score': round(abs(recent_time - mean) / stdev, 2)},
                        'detected_at': datetime.now().isoformat(),
                        'feedback': None
                    }

            q1 = statistics.median_low(response_times) if len(response_times) > 1 else 0
            q3 = statistics.median_high(response_times) if len(response_times) > 1 else 0
            if len(response_times) > 3:
                sorted_rt = sorted(response_times)
                q1 = statistics.median_low(sorted_rt[:len(sorted_rt)//2]) if len(sorted_rt) > 1 else sorted_rt[0]
                q3 = statistics.median_high(sorted_rt[len(sorted_rt)//2:]) if len(sorted_rt) > 1 else sorted_rt[-1]
                iqr = q3 - q1
                if iqr > 0 and recent_time is not None and recent_time > q3 + 1.5 * iqr:
                    return {
                        'id': f'anomaly_{len(self.anomalies)}_{int(datetime.now().timestamp())}',
                        'type': 'iqr_anomaly',
                        'severity': 'warning',
                        'service': entry.get('service'),
                        'message': f'Response time {recent_time}ms exceeds IQR upper fence',
                        'log_id': entry['id'],
                        'details': {'value': recent_time, 'q1': q1, 'q3': q3, 'iqr': iqr, 'upper_fence': q3 + 1.5 * iqr},
                        'detected_at': datetime.now().isoformat(),
                        'feedback': None
                    }
        return None

    async def get_anomalies(self, service: Optional[str] = None, severity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.anomalies
        if service:
            results = [a for a in results if a.get('service') == service]
        if severity:
            results = [a for a in results if a.get('severity') == severity]
        return results[-limit:]

    async def provide_feedback(self, anomaly_id: str, feedback: str) -> bool:
        for anomaly in self.anomalies:
            if anomaly['id'] == anomaly_id:
                anomaly['feedback'] = feedback
                anomaly['feedback_at'] = datetime.now().isoformat()
                self._save()
                return True
        return False

    async def close(self):
        self._save()
