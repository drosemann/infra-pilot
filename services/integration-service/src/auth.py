import hmac
import hashlib
import base64
import json
import time
import os
import secrets
import struct
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


TOTP_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'totp')


def _get_totp_dir() -> str:
    d = os.path.abspath(TOTP_DATA_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def _totp_file(user_id: str) -> str:
    return os.path.join(_get_totp_dir(), f'{user_id}.json')


def _load_totp_data(user_id: str) -> dict:
    path = _totp_file(user_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f'Failed to load TOTP data for {user_id}: {e}')
    return {'enabled': False, 'secret': None, 'hashed_backup_codes': []}


def _save_totp_data(user_id: str, data: dict):
    path = _totp_file(user_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f'Failed to save TOTP data for {user_id}: {e}')


def generate_totp_secret() -> str:
    secret = os.urandom(16)
    return base64.b32encode(secret).decode('utf-8').rstrip('=')


def get_totp_token_at_time(secret: str, timestamp: float) -> str:
    key = base64.b32decode(secret, True)
    counter = struct.pack('>Q', int(timestamp / 30))
    h = hmac.new(key, counter, hashlib.sha1).digest()
    offset = h[-1] & 0x0f
    code = (struct.unpack('>I', h[offset:offset + 4])[0] & 0x7fffffff) % 1000000
    return f'{code:06d}'


def get_totp_token(secret: str) -> str:
    return get_totp_token_at_time(secret, time.time())


def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    for i in range(-window, window + 1):
        expected = get_totp_token_at_time(secret, time.time() + i * 30)
        if token == expected:
            return True
    return False


def generate_totp_uri(secret: str, username: str, issuer: str = 'InfraPilot') -> str:
    return f'otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30'


class AuthManager:
    """Authentication & Security - JWT tokens, API keys, OAuth2 flows"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.secret_key = config.get('jwt_secret', os.getenv('JWT_SECRET', 'default-secret-change-me'))
        self.token_expiry = config.get('token_expiry_hours', 24)
        self.api_keys_file = config.get('api_keys_file', 'api_keys.json')
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self._load_api_keys()

    def _load_api_keys(self):
        if os.path.exists(self.api_keys_file):
            try:
                with open(self.api_keys_file, 'r') as f:
                    self.api_keys = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load API keys: {e}")

    def _save_api_keys(self):
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")

    def _generate_jwt(self, payload: Dict[str, Any]) -> str:
        header = base64.urlsafe_b64encode(
            json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()
        ).rstrip(b'=').decode()
        encoded_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b'=').decode()
        signature = hmac.new(
            self.secret_key.encode(),
            f'{header}.{encoded_payload}'.encode(),
            hashlib.sha256
        ).digest()
        encoded_sig = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        return f'{header}.{encoded_payload}.{encoded_sig}'

    def _verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts
            expected_sig = base64.urlsafe_b64encode(
                hmac.new(
                    self.secret_key.encode(),
                    f'{header_b64}.{payload_b64}'.encode(),
                    hashlib.sha256
                ).digest()
            ).rstrip(b'=').decode()
            if not hmac.compare_digest(sig_b64, expected_sig):
                return None
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            data = json.loads(base64.urlsafe_b64decode(payload_b64))
            if data.get('exp', 0) < time.time():
                return None
            return data
        except Exception as e:
            logger.debug(f"JWT verify failed: {e}")
            return None

    async def setup_totp(self, user_id: str) -> Dict[str, Any]:
        secret = generate_totp_secret()
        data = _load_totp_data(user_id)
        data['secret'] = secret
        data['enabled'] = False
        data['hashed_backup_codes'] = []
        _save_totp_data(user_id, data)
        return {
            'secret': secret,
            'uri': generate_totp_uri(secret, user_id),
            'qr_code_url': f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={generate_totp_uri(secret, user_id)}'
        }

    async def verify_totp_setup(self, user_id: str, token: str) -> bool:
        data = _load_totp_data(user_id)
        if not data.get('secret'):
            return False
        if not verify_totp_token(data['secret'], token):
            return False
        data['enabled'] = True
        _save_totp_data(user_id, data)
        return True

    async def validate_totp(self, user_id: str, token: str) -> bool:
        data = _load_totp_data(user_id)
        if not data.get('enabled') or not data.get('secret'):
            return False
        return verify_totp_token(data['secret'], token)

    async def disable_totp(self, user_id: str, password: str) -> bool:
        data = _load_totp_data(user_id)
        if not data.get('enabled'):
            return False
        _save_totp_data(user_id, {
            'enabled': False,
            'secret': None,
            'hashed_backup_codes': []
        })
        return True

    async def get_backup_codes(self, user_id: str) -> List[str]:
        data = _load_totp_data(user_id)
        if not data.get('enabled'):
            return []
        codes = []
        for _ in range(8):
            code = secrets.randbelow(100000000)
            code_str = f'{code:08d}'
            codes.append(code_str)
            code_hash = hashlib.sha256(code_str.encode()).hexdigest()
            if 'hashed_backup_codes' not in data:
                data['hashed_backup_codes'] = []
            data['hashed_backup_codes'].append(code_hash)
        _save_totp_data(user_id, data)
        return codes

    async def verify_backup_code(self, user_id: str, code: str) -> bool:
        data = _load_totp_data(user_id)
        if not data.get('enabled'):
            return False
        hashed = hashlib.sha256(code.encode()).hexdigest()
        if hashed in data.get('hashed_backup_codes', []):
            data['hashed_backup_codes'].remove(hashed)
            _save_totp_data(user_id, data)
            return True
        return False

    async def is_totp_enabled(self, user_id: str) -> bool:
        data = _load_totp_data(user_id)
        return data.get('enabled', False)

    async def generate_token(self, user_id: str, role: str = 'user', extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': int(time.time()),
            'exp': int(time.time()) + self.token_expiry * 3600,
            **(extra or {})
        }
        token = self._generate_jwt(payload)
        return {
            'token': token,
            'expires_at': payload['exp'],
            'user_id': user_id,
            'role': role
        }

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        return self._verify_jwt(token)

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        key_data = self.api_keys.get(api_key)
        if key_data and not key_data.get('revoked', False):
            if key_data.get('expires_at') and key_data['expires_at'] < time.time():
                return None
            return key_data
        return None

    async def create_api_key(self, user_id: str, name: str, role: str = 'user', expires_in_days: Optional[int] = None) -> Dict[str, Any]:
        api_key = f'ip_{secrets.token_urlsafe(32)}'
        key_data = {
            'api_key': api_key,
            'user_id': user_id,
            'name': name,
            'role': role,
            'created_at': time.time(),
            'expires_at': time.time() + expires_in_days * 86400 if expires_in_days else None,
            'revoked': False
        }
        self.api_keys[api_key] = key_data
        self._save_api_keys()
        return key_data

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        if email and password:
            if await self.is_totp_enabled(email):
                temp_token = self._generate_jwt({
                    'user_id': email,
                    'role': 'user',
                    'email': email,
                    '2fa_pending': True,
                    'iat': int(time.time()),
                    'exp': int(time.time()) + 300
                })
                return {
                    '2fa_required': True,
                    'temp_token': temp_token,
                    'user_id': email
                }
            return await self.generate_token(email, 'user', {'email': email})
        raise ValueError('Invalid credentials')

    async def verify(self, token: str) -> Dict[str, Any]:
        payload = await self.verify_token(token)
        if not payload:
            raise ValueError('Invalid or expired token')
        return {'valid': True, 'user_id': payload['user_id'], 'role': payload['role']}

    async def complete_2fa_login(self, temp_token: str, totp_code: str) -> Dict[str, Any]:
        payload = self._verify_jwt(temp_token)
        if not payload:
            raise ValueError('Invalid or expired temp token')
        if not payload.get('2fa_pending'):
            raise ValueError('Invalid temp token')
        user_id = payload['user_id']
        backup_verified = await self.verify_backup_code(user_id, totp_code)
        if not backup_verified:
            totp_valid = await self.validate_totp(user_id, totp_code)
            if not totp_valid:
                raise ValueError('Invalid TOTP code or backup code')
        return await self.generate_token(user_id, payload.get('role', 'user'), {'email': user_id})

    async def oauth2_authorize(self, platform: str, redirect_uri: str) -> Dict[str, Any]:
        state = secrets.token_urlsafe(32)
        auth_urls = {
            'discord': f'https://discord.com/api/oauth2/authorize?client_id={self.config.get("discord_client_id", "")}&redirect_uri={redirect_uri}&response_type=code&scope=identify&state={state}',
            'minecraft': f'https://api.minecraft.com/oauth2/authorize?client_id={self.config.get("minecraft_client_id", "")}&redirect_uri={redirect_uri}&response_type=code&state={state}',
            'dashboard': f'{self.config.get("dashboard_url", "http://localhost:5173")}/api/auth/oauth2/authorize?redirect_uri={redirect_uri}&state={state}'
        }
        return {
            'platform': platform,
            'state': state,
            'authorization_url': auth_urls.get(platform, auth_urls['dashboard'])
        }

    async def oauth2_callback(self, platform: str, code: str, state: str) -> Dict[str, Any]:
        return {
            'platform': platform,
            'access_token': f'{platform}_token_{secrets.token_urlsafe(16)}',
            'refresh_token': f'{platform}_refresh_{secrets.token_urlsafe(16)}',
            'expires_in': 3600
        }

    async def exchange_token(self, platform_token: str, platform: str) -> Dict[str, Any]:
        user_id = f'{platform}_user_{abs(hash(platform_token)) % 100000}'
        return await self.generate_token(user_id, 'user', {'platform': platform})
