from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import base64

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _get_cipher(key: Optional[bytes] = None):
    if not HAS_CRYPTO:
        raise ImportError("cryptography is required for SecretsManager")
    if key is None:
        key = os.getenv('SECRETS_ENCRYPTION_KEY', base64.urlsafe_b64encode(b'x' * 32).decode())
        if isinstance(key, str):
            key = key.encode()
    return Fernet(key)


class SecretsManager:
    """HashiCorp Vault integration, dynamic secrets, credential rotation, encrypted env injection"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.secrets_file = config.get('secrets_file', 'data/secrets.json')
        self.audit_file = config.get('secrets_audit_file', 'data/secrets_audit.json')
        self.vault_addr = config.get('vault_addr', os.getenv('VAULT_ADDR', 'http://localhost:8200'))
        self.vault_token = config.get('vault_token', os.getenv('VAULT_TOKEN', ''))
        self._secrets: Dict[str, Any] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.secrets_file):
                with open(self.secrets_file, 'rb') as f:
                    encrypted = f.read()
                if encrypted:
                    cipher = _get_cipher()
                    decrypted = cipher.decrypt(encrypted)
                    self._secrets = json.loads(decrypted.decode())
        except Exception as e:
            logger.warning(f"Failed to load secrets: {e}")
        try:
            if os.path.exists(self.audit_file):
                with open(self.audit_file, 'r') as f:
                    self._audit_log = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load audit log: {e}")

    def _save_secrets(self):
        try:
            os.makedirs(os.path.dirname(self.secrets_file), exist_ok=True)
            cipher = _get_cipher()
            plaintext = json.dumps(self._secrets, indent=2).encode()
            encrypted = cipher.encrypt(plaintext)
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")

    def _save_audit(self):
        try:
            os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)
            with open(self.audit_file, 'w') as f:
                json.dump(self._audit_log[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    def _audit(self, action: str, secret_id: str, user: str = 'system', details: Optional[Dict[str, Any]] = None):
        self._audit_log.append({
            'action': action,
            'secret_id': secret_id,
            'user': user,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
        })
        self._save_audit()

    def _mask_value(self, value: str) -> str:
        if len(value) <= 8:
            return '*' * len(value)
        return value[:4] + '*' * (len(value) - 8) + value[-4:]

    async def create_secret(self, secret_data: Dict[str, Any], user: str = 'system') -> Dict[str, Any]:
        secret_id = secret_data.get('id', f'secret_{len(self._secrets)}_{int(datetime.now().timestamp())}')
        entry = {
            'id': secret_id,
            'name': secret_data.get('name', ''),
            'value': secret_data.get('value', ''),
            'type': secret_data.get('type', 'static'),
            'ttl': secret_data.get('ttl'),  # seconds
            'rotatable': secret_data.get('rotatable', False),
            'rotation_interval': secret_data.get('rotation_interval'),  # seconds
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'expires_at': secret_data.get('expires_at'),
            'metadata': secret_data.get('metadata', {}),
        }
        self._secrets[secret_id] = entry
        self._save_secrets()
        self._audit('create', secret_id, user)

        result = {k: v for k, v in entry.items() if k != 'value'}
        result['value'] = self._mask_value(entry['value'])
        return result

    async def get_secrets(self) -> Dict[str, Any]:
        result = {}
        for sid, entry in self._secrets.items():
            result[sid] = {k: v for k, v in entry.items() if k != 'value'}
            result[sid]['value'] = self._mask_value(entry['value'])
        return result

    async def get_secret(self, secret_id: str) -> Optional[Dict[str, Any]]:
        entry = self._secrets.get(secret_id)
        if not entry:
            return None
        self._audit('read', secret_id, 'system')
        return entry

    async def update_secret(self, secret_id: str, updates: Dict[str, Any], user: str = 'system') -> bool:
        entry = self._secrets.get(secret_id)
        if not entry:
            return False
        entry.update({k: v for k, v in updates.items() if k != 'id'})
        entry['updated_at'] = datetime.now().isoformat()
        self._secrets[secret_id] = entry
        self._save_secrets()
        self._audit('update', secret_id, user, {'fields': list(updates.keys())})
        return True

    async def delete_secret(self, secret_id: str, user: str = 'system') -> bool:
        if secret_id in self._secrets:
            del self._secrets[secret_id]
            self._save_secrets()
            self._audit('delete', secret_id, user)
            return True
        return False

    async def rotate_secret(self, secret_id: str, user: str = 'system') -> Optional[Dict[str, Any]]:
        entry = self._secrets.get(secret_id)
        if not entry or not entry.get('rotatable'):
            return None

        if self.vault_addr and self.vault_token:
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.vault_addr}/v1/{entry.get('name', '')}/rotate",
                        headers={'X-Vault-Token': self.vault_token}
                    ) as resp:
                        if resp.status == 200:
                            vault_data = await resp.json()
                            entry['value'] = vault_data.get('data', {}).get('value', '')
            except Exception:
                logger.warning("Vault rotation failed")

        entry['updated_at'] = datetime.now().isoformat()
        entry['last_rotated_at'] = datetime.now().isoformat()
        self._secrets[secret_id] = entry
        self._save_secrets()
        self._audit('rotate', secret_id, user)

        result = {k: v for k, v in entry.items() if k != 'value'}
        result['value'] = self._mask_value(entry['value'])
        return result

    async def inject_env(self, inject_config: Dict[str, Any]) -> Dict[str, Any]:
        secrets_map = inject_config.get('secrets', {})
        resolved = {}
        for env_var, secret_id in secrets_map.items():
            entry = self._secrets.get(secret_id)
            if entry:
                resolved[env_var] = entry['value']
                os.environ[env_var] = entry['value']
        self._audit('inject', ','.join(secrets_map.values()), inject_config.get('user', 'system'), {'env_vars': list(secrets_map.keys())})
        return {'injected': list(resolved.keys()), 'count': len(resolved)}

    async def get_audit_log(self) -> List[Dict[str, Any]]:
        return self._audit_log[-500:]
