from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class PermissionManager:
    """Unified permission system with role-based access, inheritance, and Redis-backed cache"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.permissions_file = config.get('permissions_file', 'permissions.json')
        self.roles_file = config.get('roles_file', 'roles.json')
        self.cache_file = config.get('permission_cache_file', 'permission_cache.json')
        self.permissions: Dict[str, Dict[str, Any]] = {}
        self.roles: Dict[str, Dict[str, Any]] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.permissions_file):
            try:
                with open(self.permissions_file, 'r') as f:
                    self.permissions = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load permissions: {e}")
        if os.path.exists(self.roles_file):
            try:
                with open(self.roles_file, 'r') as f:
                    self.roles = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load roles: {e}")
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_permissions(self):
        try:
            with open(self.permissions_file, 'w') as f:
                json.dump(self.permissions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")

    def _save_roles(self):
        try:
            with open(self.roles_file, 'w') as f:
                json.dump(self.roles, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save roles: {e}")

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    async def check_permission(self, user_id: str, permission: str, resource: Optional[str] = None) -> bool:
        cache_key = f'{user_id}:{permission}:{resource or "*"}'
        cached = self.cache.get(cache_key)
        if cached:
            if cached.get('expires_at', 0) > datetime.now().timestamp():
                return cached.get('granted', False)
        user_perms = self.permissions.get(user_id, {})
        granted_perms = set(user_perms.get('permissions', []))
        denied_perms = set(user_perms.get('denied_permissions', []))
        user_roles = user_perms.get('roles', [])
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                granted_perms.update(role.get('permissions', []))
        resource_specific = f'{permission}:{resource}' if resource else permission
        if resource_specific in denied_perms:
            self.cache[cache_key] = {'granted': False, 'expires_at': datetime.now().timestamp() + 300}
            self._save_cache()
            return False
        if resource_specific in granted_perms:
            self.cache[cache_key] = {'granted': True, 'expires_at': datetime.now().timestamp() + 300}
            self._save_cache()
            return True
        if permission in denied_perms:
            self.cache[cache_key] = {'granted': False, 'expires_at': datetime.now().timestamp() + 300}
            self._save_cache()
            return False
        if permission in granted_perms:
            self.cache[cache_key] = {'granted': True, 'expires_at': datetime.now().timestamp() + 300}
            self._save_cache()
            return True
        admin_roles = {r for r in user_roles if self.roles.get(r, {}).get('admin', False)}
        if admin_roles:
            return True
        self.cache[cache_key] = {'granted': False, 'expires_at': datetime.now().timestamp() + 300}
        self._save_cache()
        return False

    async def grant_permission(self, user_id: str, permission: str, resource: Optional[str] = None) -> bool:
        if user_id not in self.permissions:
            self.permissions[user_id] = {'permissions': [], 'denied_permissions': [], 'roles': []}
        perm = f'{permission}:{resource}' if resource else permission
        if perm not in self.permissions[user_id]['permissions']:
            self.permissions[user_id]['permissions'].append(perm)
        if perm in self.permissions[user_id]['denied_permissions']:
            self.permissions[user_id]['denied_permissions'].remove(perm)
        self._save_permissions()
        self._invalidate_cache(user_id)
        return True

    async def revoke_permission(self, user_id: str, permission: str, resource: Optional[str] = None) -> bool:
        if user_id in self.permissions:
            perm = f'{permission}:{resource}' if resource else permission
            if perm in self.permissions[user_id]['permissions']:
                self.permissions[user_id]['permissions'].remove(perm)
            if perm not in self.permissions[user_id]['denied_permissions']:
                self.permissions[user_id]['denied_permissions'].append(perm)
            self._save_permissions()
            self._invalidate_cache(user_id)
        return True

    async def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        user_perms = self.permissions.get(user_id, {'permissions': [], 'denied_permissions': [], 'roles': []})
        effective_perms: Set[str] = set(user_perms.get('permissions', []))
        for role_name in user_perms.get('roles', []):
            role = self.roles.get(role_name)
            if role:
                effective_perms.update(role.get('permissions', []))
        denied = set(user_perms.get('denied_permissions', []))
        effective_perms -= denied
        return {
            'user_id': user_id,
            'roles': user_perms.get('roles', []),
            'permissions': list(effective_perms),
            'denied_permissions': list(denied)
        }

    async def create_role(self, name: str, permissions: List[str], admin: bool = False, inherits: Optional[List[str]] = None) -> Dict[str, Any]:
        self.roles[name] = {
            'name': name,
            'permissions': permissions,
            'admin': admin,
            'inherits': inherits or [],
            'created_at': datetime.now().isoformat()
        }
        self._save_roles()
        return self.roles[name]

    async def assign_role(self, user_id: str, role_name: str) -> bool:
        if role_name not in self.roles:
            return False
        if user_id not in self.permissions:
            self.permissions[user_id] = {'permissions': [], 'denied_permissions': [], 'roles': []}
        if role_name not in self.permissions[user_id]['roles']:
            self.permissions[user_id]['roles'].append(role_name)
        self._save_permissions()
        self._invalidate_cache(user_id)
        return True

    async def get_inherited_permissions(self, user_id: str) -> List[str]:
        user_perms = self.permissions.get(user_id, {'roles': []})
        all_perms: Set[str] = set()
        roles_to_check = list(user_perms.get('roles', []))
        checked_roles: Set[str] = set()
        while roles_to_check:
            role_name = roles_to_check.pop(0)
            if role_name in checked_roles:
                continue
            checked_roles.add(role_name)
            role = self.roles.get(role_name)
            if role:
                all_perms.update(role.get('permissions', []))
                roles_to_check.extend(role.get('inherits', []))
        return list(all_perms)

    def _invalidate_cache(self, user_id: str):
        keys_to_delete = [k for k in self.cache if k.startswith(f'{user_id}:')]
        for k in keys_to_delete:
            del self.cache[k]
        self._save_cache()
