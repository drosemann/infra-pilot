from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import logging

logger = logging.getLogger(__name__)


class GDPRDataManager:
    """Data classification, retention policies, automated purge, right-to-erasure, consent management"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classifications_file = config.get('gdpr_classifications_file', 'data/gdpr_classifications.json')
        self.policies_file = config.get('gdpr_policies_file', 'data/gdpr_policies.json')
        self.erasure_file = config.get('gdpr_erasure_file', 'data/gdpr_erasure_requests.json')
        self.consent_file = config.get('gdpr_consent_file', 'data/gdpr_consent.json')
        self.inventory_file = config.get('gdpr_inventory_file', 'data/gdpr_inventory.json')
        self.classifications: List[Dict[str, Any]] = []
        self.policies: List[Dict[str, Any]] = []
        self.erasure_requests: List[Dict[str, Any]] = []
        self.consent_records: Dict[str, Any] = {}
        self.inventory: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        for path, attr in [
            (self.classifications_file, 'classifications'),
            (self.policies_file, 'policies'),
            (self.erasure_file, 'erasure_requests'),
            (self.consent_file, 'consent_records'),
            (self.inventory_file, 'inventory'),
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

    async def classify_data(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            'id': f'class_{len(self.classifications)}_{int(datetime.now().timestamp())}',
            'data_type': classification.get('data_type', ''),
            'category': classification.get('category', 'general'),
            'sensitivity': classification.get('sensitivity', 'low'),
            'description': classification.get('description', ''),
            'retention_days': classification.get('retention_days', 365),
            'jurisdiction': classification.get('jurisdiction', 'GDPR'),
            'created_at': datetime.now().isoformat(),
        }
        self.classifications.append(entry)
        self._save('classifications', self.classifications_file)
        return entry

    async def get_classifications(self) -> List[Dict[str, Any]]:
        return self.classifications

    async def create_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            'id': f'policy_{len(self.policies)}_{int(datetime.now().timestamp())}',
            'name': policy.get('name', ''),
            'data_category': policy.get('data_category', ''),
            'retention_days': policy.get('retention_days', 365),
            'action': policy.get('action', 'purge'),
            'active': policy.get('active', True),
            'created_at': datetime.now().isoformat(),
        }
        self.policies.append(entry)
        self._save('policies', self.policies_file)
        return entry

    async def get_policies(self) -> List[Dict[str, Any]]:
        return self.policies

    async def delete_policy(self, policy_id: str) -> bool:
        for i, p in enumerate(self.policies):
            if p['id'] == policy_id:
                self.policies.pop(i)
                self._save('policies', self.policies_file)
                return True
        return False

    async def create_erasure_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            'id': f'erasure_{len(self.erasure_requests)}_{int(datetime.now().timestamp())}',
            'user_id': request.get('user_id', ''),
            'email': request.get('email', ''),
            'reason': request.get('reason', ''),
            'requested_by': request.get('requested_by', ''),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'data_types': request.get('data_types', []),
        }
        self.erasure_requests.append(entry)
        self._save('erasure_requests', self.erasure_file)
        return entry

    async def get_erasure_requests(self) -> List[Dict[str, Any]]:
        return self.erasure_requests

    async def execute_erasure(self, request_id: str) -> Optional[Dict[str, Any]]:
        req = next((r for r in self.erasure_requests if r['id'] == request_id), None)
        if not req:
            return None
        if req['status'] == 'executed':
            return {'error': 'Already executed'}

        user_id = req.get('user_id', '')
        data_types = req.get('data_types', [])
        purged = []

        for item in self.inventory:
            if item.get('user_id') == user_id:
                if not data_types or item.get('data_type') in data_types:
                    purged.append(item.get('data_type', 'unknown'))
                    self.inventory.remove(item)

        if user_id in self.consent_records:
            del self.consent_records[user_id]
            purged.append('consent_records')

        req['status'] = 'executed'
        req['executed_at'] = datetime.now().isoformat()
        req['purged_data_types'] = purged
        self._save('inventory', self.inventory_file)
        self._save('consent_records', self.consent_file)
        self._save('erasure_requests', self.erasure_file)
        return req

    async def get_data_inventory(self) -> List[Dict[str, Any]]:
        return self.inventory

    async def set_consent(self, consent: Dict[str, Any]) -> Dict[str, Any]:
        user_id = consent.get('user_id', '')
        record = {
            'user_id': user_id,
            'purposes': consent.get('purposes', []),
            'granted': consent.get('granted', True),
            'granted_at': datetime.now().isoformat(),
            'expires_at': consent.get('expires_at'),
            'ip_address': consent.get('ip_address', ''),
            'user_agent': consent.get('user_agent', ''),
        }
        self.consent_records[user_id] = record
        self._save('consent_records', self.consent_file)
        return record

    async def get_consent(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.consent_records.get(user_id)

    async def auto_purge(self) -> Dict[str, Any]:
        now = datetime.now()
        purged_count = 0
        for policy in self.policies:
            if not policy.get('active', True):
                continue
            retention = policy.get('retention_days', 365)
            cutoff = now - timedelta(days=retention)
            category = policy.get('data_category', '')

            before = len(self.inventory)
            self.inventory = [
                item for item in self.inventory
                if not (item.get('data_category') == category and
                        datetime.fromisoformat(item.get('created_at', now.isoformat())) < cutoff)
            ]
            purged_count += before - len(self.inventory)

        self._save('inventory', self.inventory_file)
        return {'purged_items': purged_count, 'remaining': len(self.inventory), 'executed_at': now.isoformat()}
