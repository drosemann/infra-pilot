import json
import os
import time
import secrets
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

RATE_LIMIT_TIERS = {
    'free': {'requests_per_hour': 100},
    'basic': {'requests_per_hour': 1000},
    'pro': {'requests_per_hour': 10000},
    'enterprise': {'requests_per_hour': None},
}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class TokenBucket:
    """Token bucket rate limiter"""

    def __init__(self, rate: int, per_seconds: int = 3600):
        self.max_tokens = rate
        self.tokens = rate
        self.per_seconds = per_seconds
        self.refill_rate = rate / per_seconds if rate else 0
        self.last_refill = time.time()

    def allow(self) -> bool:
        if self.max_tokens is None:
            return True
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def remaining(self) -> int:
        if self.max_tokens is None:
            return -1
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        return int(self.tokens)

    def reset(self):
        self.tokens = self.max_tokens
        self.last_refill = time.time()


class APIGateway:
    """API Gateway & Rate Limiting - Token bucket algorithm with per-key quotas"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.keys_file = _data_file('gateway_keys.json')
        self.usage_file = _data_file('gateway_usage.json')
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.usage: Dict[str, List[Dict[str, Any]]] = {}
        self.buckets: Dict[str, TokenBucket] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    self.keys = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load gateway keys: {e}")
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    self.usage = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load usage data: {e}")
        for kid, key_data in self.keys.items():
            tier = key_data.get('tier', 'free')
            rate = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS['free'])['requests_per_hour']
            if rate is not None:
                self.buckets[kid] = TokenBucket(rate)

    def _save_keys(self):
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save gateway keys: {e}")

    def _save_usage(self):
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")

    def _generate_key(self) -> str:
        return f'gw_{secrets.token_urlsafe(32)}'

    async def create_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        key_id = self._generate_key()
        tier = data.get('tier', 'free')
        if tier not in RATE_LIMIT_TIERS:
            tier = 'free'
        key_data = {
            'id': key_id,
            'name': data.get('name', ''),
            'tier': tier,
            'rate_limit': RATE_LIMIT_TIERS[tier]['requests_per_hour'],
            'owner': data.get('owner', ''),
            'active': data.get('active', True),
            'created_at': datetime.now().isoformat(),
            'rotated_at': None
        }
        self.keys[key_id] = key_data
        rate = RATE_LIMIT_TIERS[tier]['requests_per_hour']
        if rate is not None:
            self.buckets[key_id] = TokenBucket(rate)
        self._save_keys()
        return key_data

    async def list_keys(self) -> List[Dict[str, Any]]:
        return list(self.keys.values())

    async def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        return self.keys.get(key_id)

    async def delete_key(self, key_id: str) -> bool:
        if key_id in self.keys:
            del self.keys[key_id]
            self.buckets.pop(key_id, None)
            self.usage.pop(key_id, None)
            self._save_keys()
            self._save_usage()
            return True
        return False

    async def rotate_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        key_data = self.keys.get(key_id)
        if not key_data:
            return None
        new_id = self._generate_key()
        key_data['id'] = new_id
        key_data['rotated_at'] = datetime.now().isoformat()
        self.keys[new_id] = key_data
        tier = key_data.get('tier', 'free')
        rate = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS['free'])['requests_per_hour']
        if rate is not None:
            self.buckets[new_id] = TokenBucket(rate)
        del self.keys[key_id]
        self.buckets.pop(key_id, None)
        usage = self.usage.pop(key_id, None)
        if usage:
            self.usage[new_id] = usage
        self._save_keys()
        self._save_usage()
        return key_data

    async def get_usage(self, key_id: str) -> Dict[str, Any]:
        key_data = self.keys.get(key_id)
        if not key_data:
            return {'error': 'Key not found'}
        usage_log = self.usage.get(key_id, [])
        now = time.time()
        recent = [u for u in usage_log if now - u.get('timestamp', 0) < 3600]
        bucket = self.buckets.get(key_id)
        return {
            'key_id': key_id,
            'total_requests': len(usage_log),
            'requests_last_hour': len(recent),
            'rate_limit': key_data.get('rate_limit'),
            'remaining': bucket.remaining() if bucket else -1,
            'tier': key_data.get('tier')
        }

    def check_rate_limit(self, key_id: str) -> Dict[str, Any]:
        key_data = self.keys.get(key_id)
        if not key_data:
            return {'allowed': False, 'reason': 'Invalid key'}
        if not key_data.get('active', True):
            return {'allowed': False, 'reason': 'Key is disabled'}
        bucket = self.buckets.get(key_id)
        if bucket is None:
            return {'allowed': True}
        allowed = bucket.allow()
        usage_log = self.usage.setdefault(key_id, [])
        usage_log.append({'timestamp': time.time(), 'allowed': allowed})
        if len(usage_log) > 10000:
            self.usage[key_id] = usage_log[-5000:]
        self._save_usage()
        if not allowed:
            return {'allowed': False, 'reason': 'Rate limit exceeded'}
        return {'allowed': True}

    async def initialize(self):
        logger.info("APIGateway initialized")

    async def close(self):
        logger.info("APIGateway closed")
