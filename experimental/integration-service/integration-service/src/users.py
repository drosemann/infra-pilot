import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserProfileManager:
    """Cross-platform user profiles with sync, linking, and search"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.profiles_file = config.get('profiles_file', 'user_profiles.json')
        self.linkings_file = config.get('linkings_file', 'account_linkings.json')
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.linkings: Dict[str, Dict[str, str]] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    self.profiles = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load profiles: {e}")
        if os.path.exists(self.linkings_file):
            try:
                with open(self.linkings_file, 'r') as f:
                    self.linkings = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load linkings: {e}")

    def _save_profiles(self):
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")

    def _save_linkings(self):
        try:
            with open(self.linkings_file, 'w') as f:
                json.dump(self.linkings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save linkings: {e}")

    async def get_unified_profile(self, user_id: str) -> Dict[str, Any]:
        profile = self.profiles.get(user_id, {})
        linked = self.linkings.get(user_id, {})
        return {
            'user_id': user_id,
            'profile': profile,
            'linked_accounts': linked,
            'discord_name': profile.get('discord_name'),
            'minecraft_uuid': profile.get('minecraft_uuid'),
            'minecraft_name': profile.get('minecraft_name'),
            'stats': profile.get('stats', {}),
            'balance': profile.get('balance', 0),
            'achievements': profile.get('achievements', []),
            'bio': profile.get('bio', ''),
            'social_links': profile.get('social_links', {}),
            'roles': profile.get('roles', []),
            'created_at': profile.get('created_at'),
            'updated_at': profile.get('updated_at')
        }

    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                'created_at': datetime.now().isoformat(),
                'stats': {},
                'achievements': [],
                'social_links': {},
                'roles': []
            }
        profile = self.profiles[user_id]
        for key in ['discord_name', 'minecraft_uuid', 'minecraft_name', 'bio', 'social_links']:
            if key in updates:
                profile[key] = updates[key]
        if 'stats' in updates and isinstance(updates['stats'], dict):
            profile.setdefault('stats', {}).update(updates['stats'])
        if 'achievements' in updates and isinstance(updates['achievements'], list):
            existing = set(profile.get('achievements', []))
            for a in updates['achievements']:
                if isinstance(a, str):
                    existing.add(a)
            profile['achievements'] = list(existing)
        if 'balance' in updates:
            profile['balance'] = profile.get('balance', 0) + updates['balance']
        if 'roles' in updates:
            profile['roles'] = updates['roles']
        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()
        return True

    async def sync_profile_on_login(self, platform: str, platform_user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = None
        for uid, linkings in self.linkings.items():
            if linkings.get(platform) == platform_user_id:
                user_id = uid
                break
        if not user_id:
            user_id = f'{platform}_{platform_user_id}'
            self.linkings.setdefault(user_id, {})[platform] = platform_user_id
            self._save_linkings()
        await self.update_profile(user_id, profile_data)
        return await self.get_unified_profile(user_id)

    async def sync_roles(self, user_id: str) -> Dict[str, Any]:
        profile = self.profiles.get(user_id, {})
        roles = profile.get('roles', [])
        linked = self.linkings.get(user_id, {})
        synced_roles = set(roles)
        for platform, pid in linked.items():
            platform_roles = profile.get(f'{platform}_roles', [])
            synced_roles.update(platform_roles)
        profile['roles'] = list(synced_roles)
        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()
        return {'user_id': user_id, 'roles': list(synced_roles)}

    async def link_account(self, user_id: str, platform: str, platform_user_id: str) -> bool:
        self.linkings.setdefault(user_id, {})[platform] = platform_user_id
        self._save_linkings()
        return True

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        for user_id, profile in self.profiles.items():
            if q in user_id.lower() or q in profile.get('discord_name', '').lower() or q in profile.get('minecraft_name', '').lower() or q in profile.get('bio', '').lower():
                results.append({
                    'user_id': user_id,
                    'discord_name': profile.get('discord_name'),
                    'minecraft_name': profile.get('minecraft_name'),
                    'roles': profile.get('roles', [])
                })
        return results[:50]
