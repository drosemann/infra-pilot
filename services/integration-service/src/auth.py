import hmac
import hashlib
import base64
import json
import time
import os
import secrets
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


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
            return await self.generate_token(email, 'user', {'email': email})
        raise ValueError('Invalid credentials')

    async def verify(self, token: str) -> Dict[str, Any]:
        payload = await self.verify_token(token)
        if not payload:
            raise ValueError('Invalid or expired token')
        return {'valid': True, 'user_id': payload['user_id'], 'role': payload['role']}

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
