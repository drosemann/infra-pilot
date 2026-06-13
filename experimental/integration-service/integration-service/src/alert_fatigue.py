from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging
import hashlib

logger = logging.getLogger(__name__)


class AlertFatigueReducer:
    """Alert deduplication, correlation, maintenance suppression, notification throttling, digest mode, auto-escalation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dedup_file = config.get('alert_dedup_file', 'data/alert_dedup.json')
        self.suppressions_file = config.get('alert_suppressions_file', 'data/alert_suppressions.json')
        self.digest_config_file = config.get('digest_config_file', 'data/digest_configs.json')
        self.escalation_file = config.get('escalation_policies_file', 'data/escalation_policies.json')
        self.dedup_window_minutes = config.get('dedup_window_minutes', 30)
        self.throttle_window_seconds = config.get('throttle_window_seconds', 60)
        self.alerts: List[Dict[str, Any]] = []
        self.suppressions: List[Dict[str, Any]] = []
        self.digest_configs: Dict[str, Any] = {}
        self.escalation_policies: List[Dict[str, Any]] = []
        self._recent_fingerprints: Dict[str, datetime] = {}
        self._throttle_counters: Dict[str, int] = {}
        self._load()

    def _load(self):
        for path, attr in [
            (self.dedup_file, 'alerts'),
            (self.suppressions_file, 'suppressions'),
            (self.digest_config_file, 'digest_configs'),
            (self.escalation_file, 'escalation_policies'),
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

    def _fingerprint(self, alert: Dict[str, Any]) -> str:
        raw = f"{alert.get('source', '')}:{alert.get('message', '')}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def ingest_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        fp = self._fingerprint(alert)
        now = datetime.now()

        if fp in self._recent_fingerprints:
            elapsed = (now - self._recent_fingerprints[fp]).total_seconds()
            if elapsed < self.dedup_window_minutes * 60:
                return {'deduplicated': True, 'original': self._recent_fingerprints[fp].isoformat()}

        source = alert.get('source', 'unknown')
        if source in self._throttle_counters:
            self._throttle_counters[source] += 1
        else:
            self._throttle_counters[source] = 1

        suppressed = False
        for s in self.suppressions:
            if s.get('active', False):
                match_source = s.get('source_matcher', '')
                if match_source and match_source in source:
                    suppressed = True
                    break

        entry = {
            'id': f'alert_{len(self.alerts)}_{int(now.timestamp())}',
            'fingerprint': fp,
            'title': alert.get('title', 'Untitled'),
            'message': alert.get('message', ''),
            'source': source,
            'severity': alert.get('severity', 'info'),
            'metadata': alert.get('metadata', {}),
            'ingested_at': now.isoformat(),
            'suppressed': suppressed,
            'acknowledged': False,
            'acknowledged_at': None,
            'escalated': False,
            'escalation_level': 0,
        }
        self._recent_fingerprints[fp] = now
        self.alerts.append(entry)
        self._save('alerts', self.dedup_file)

        if not suppressed:
            result = await self._check_escalation(entry)
            digest_mode = self._should_digest(source)
            return {
                'alert': entry,
                'deduplicated': False,
                'suppressed': suppressed,
                'digest_mode': digest_mode,
                'escalation': result,
            }
        return {'alert': entry, 'deduplicated': False, 'suppressed': True}

    def _should_digest(self, source: str) -> bool:
        for cfg in self.digest_configs.values():
            if isinstance(cfg, dict) and cfg.get('enabled', False):
                matchers = cfg.get('source_matchers', [])
                if any(m in source for m in matchers):
                    return True
        return False

    async def _check_escalation(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for policy in self.escalation_policies:
            if not policy.get('active', True):
                continue
            severity_match = policy.get('severity', 'critical') == alert.get('severity')
            source_match = policy.get('source_matcher', '') in alert.get('source', '')
            if severity_match or source_match:
                return {
                    'policy_id': policy.get('id'),
                    'escalate_after_minutes': policy.get('escalate_after_minutes', 15),
                    'target': policy.get('escalation_target', ''),
                    'escalation_level': alert.get('escalation_level', 0) + 1,
                }
        return None

    async def get_correlated(self) -> List[Dict[str, Any]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for alert in self.alerts:
            key = f"{alert.get('source', 'unknown')}:{alert.get('severity', 'info')}"
            if key not in groups:
                groups[key] = []
            groups[key].append(alert)
        correlated = []
        for key, group in groups.items():
            if len(group) > 1:
                source, severity = key.split(':', 1)
                correlated.append({
                    'correlation_key': key,
                    'source': source,
                    'severity': severity,
                    'count': len(group),
                    'alerts': group[-10:],
                    'first_at': group[0]['ingested_at'],
                    'last_at': group[-1]['ingested_at'],
                })
        correlated.sort(key=lambda c: c['count'], reverse=True)
        return correlated

    async def suppress(self, alert_id: str, reason: str = 'manual') -> bool:
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['suppressed'] = True
                alert['suppress_reason'] = reason
                alert['suppressed_at'] = datetime.now().isoformat()
                self._save('alerts', self.dedup_file)
                return True
        return False

    async def set_digest_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config_id = config.get('id', f'digest_{len(self.digest_configs)}_{int(datetime.now().timestamp())}')
        config['id'] = config_id
        config['updated_at'] = datetime.now().isoformat()
        self.digest_configs[config_id] = config
        self._save('digest_configs', self.digest_config_file)
        return config

    async def get_digest_config(self) -> Dict[str, Any]:
        return self.digest_configs

    async def set_escalation_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        policy_id = policy.get('id', f'escalation_{len(self.escalation_policies)}_{int(datetime.now().timestamp())}')
        policy['id'] = policy_id
        policy['created_at'] = datetime.now().isoformat()
        self.escalation_policies.append(policy)
        self._save('escalation_policies', self.escalation_file)
        return policy

    async def get_fatigue_stats(self) -> Dict[str, Any]:
        total = len(self.alerts)
        suppressed = sum(1 for a in self.alerts if a.get('suppressed'))
        deduped = total - len(self._recent_fingerprints)
        by_source: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for a in self.alerts:
            by_source[a.get('source', 'unknown')] = by_source.get(a.get('source', 'unknown'), 0) + 1
            by_severity[a.get('severity', 'info')] = by_severity.get(a.get('severity', 'info'), 0) + 1
        return {
            'total_alerts': total,
            'suppressed': suppressed,
            'unique_fingerprints': len(self._recent_fingerprints),
            'by_source': by_source,
            'by_severity': by_severity,
            'throttle_counters': self._throttle_counters,
            'escalation_policies_count': len(self.escalation_policies),
        }
