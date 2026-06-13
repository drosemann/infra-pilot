import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import copy

from .notification_providers import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedUserManager:
    """Unified User Management - Cross-platform authentication and profile sync"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dashboard_url = config.get('dashboard_url', 'http://localhost:3000')
        self.discord_api_url = config.get('discord_api_url', 'http://localhost:3001')
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("UnifiedUserManager initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = user_data.get('email', '').replace('@', '_at_').replace('.', '_')
        platform_users = {}
        try:
            async with self.session.post(
                f"{self.dashboard_url}/api/users", json=user_data
            ) as resp:
                if resp.status == 200:
                    platform_users['dashboard'] = await resp.json()
        except Exception as e:
            logger.warning(f"Dashboard user creation failed: {e}")
        try:
            async with self.session.post(
                f"{self.discord_api_url}/api/users",
                json={**user_data, 'external_id': user_id}
            ) as resp:
                if resp.status == 200:
                    platform_users['discord'] = await resp.json()
        except Exception as e:
            logger.warning(f"Discord user creation failed: {e}")
        try:
            async with self.session.post(
                f"{self.service_core_url}/api/users", json=user_data
            ) as resp:
                if resp.status == 200:
                    platform_users['service_core'] = await resp.json()
        except Exception as e:
            logger.warning(f"Service Core user creation failed: {e}")
        return {
            'unified_id': user_id,
            'email': user_data.get('email'),
            'platforms': platform_users,
            'created_at': datetime.now().isoformat()
        }

    async def sync_user(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        try:
            endpoints = {
                'dashboard': f"{self.dashboard_url}/api/users/{user_id}",
                'discord': f"{self.discord_api_url}/api/users/{user_id}",
                'service_core': f"{self.service_core_url}/api/users/{user_id}"
            }
            async with self.session.get(endpoints.get(platform)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Sync from {platform} failed: {e}")
        return None

    async def get_unified_profile(self, email: str) -> Dict[str, Any]:
        profile = {'email': email, 'platforms': {}}
        tasks = [
            self.sync_user(email, 'dashboard'),
            self.sync_user(email, 'discord'),
            self.sync_user(email, 'service_core')
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        platform_names = ['dashboard', 'discord', 'service_core']
        for name, result in zip(platform_names, results):
            if isinstance(result, dict):
                profile['platforms'][name] = result
        return profile

    async def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
        tasks = []
        try:
            async with self.session.put(
                f"{self.dashboard_url}/api/users/{email}", json=updates
            ) as resp:
                tasks.append(resp.status == 200)
        except:
            tasks.append(False)
        try:
            async with self.session.put(
                f"{self.discord_api_url}/api/users/{email}", json=updates
            ) as resp:
                tasks.append(resp.status == 200)
        except:
            tasks.append(False)
        try:
            async with self.session.put(
                f"{self.service_core_url}/api/users/{email}", json=updates
            ) as resp:
                tasks.append(resp.status == 200)
        except:
            tasks.append(False)
        return any(tasks)

    async def profile_sync_on_login(self, platform: str, platform_user_id: str) -> Dict[str, Any]:
        profile = await self.sync_user(platform_user_id, platform)
        if not profile:
            return {'error': f'Could not sync profile from {platform}'}
        return {
            'platform': platform,
            'platform_user_id': platform_user_id,
            'profile': profile,
            'synced_at': datetime.now().isoformat()
        }

    async def sync_roles(self, email: str) -> Dict[str, Any]:
        profile = await self.get_unified_profile(email)
        all_roles = []
        for plat, data in profile.get('platforms', {}).items():
            if isinstance(data, dict):
                roles = data.get('roles', [])
                all_roles.extend(roles)
        return {'email': email, 'roles': list(set(all_roles)), 'synced_at': datetime.now().isoformat()}

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        results = []
        for platform in ['dashboard', 'discord', 'service_core']:
            try:
                endpoints = {
                    'dashboard': f"{self.dashboard_url}/api/users/search",
                    'discord': f"{self.discord_api_url}/api/users/search",
                    'service_core': f"{self.service_core_url}/api/users/search"
                }
                async with self.session.get(
                    endpoints[platform], params={'q': query}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            results.extend(data)
            except Exception as e:
                logger.warning(f"Search on {platform} failed: {e}")
        return results[:50]


class CrossPlatformNotifier:
    """Cross-Service Operations - Synchronized notifications with preferences and digest"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.discord_webhook = config.get('discord_webhook')
        self.dashboard_ws = config.get('dashboard_ws')
        self.session: Optional[aiohttp.ClientSession] = None
        self.preferences_file = config.get('notification_prefs_file', 'notification_prefs.json')
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self._load_preferences()

    def _load_preferences(self):
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load preferences: {e}")

    def _save_preferences(self):
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("CrossPlatformNotifier initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def broadcast(self, message: Dict[str, Any]) -> bool:
        results = []
        if self.discord_webhook:
            try:
                async with self.session.post(self.discord_webhook, json=message) as resp:
                    results.append(resp.status in [200, 204])
            except Exception as e:
                logger.warning(f"Discord webhook failed: {e}")
                results.append(False)
        if self.dashboard_ws:
            try:
                async with self.session.post(self.dashboard_ws, json=message) as resp:
                    results.append(resp.status == 200)
            except Exception as e:
                logger.warning(f"Dashboard notification failed: {e}")
                results.append(False)
        return any(results)

    async def notify_server_event(self, event_type: str, server_name: str, details: Dict[str, Any]) -> bool:
        event_messages = {
            'server_created': f"\U0001f389 New server '{server_name}' created!",
            'server_started': f"\U0001f7e2 Server '{server_name}' started",
            'server_stopped': f"\U0001f534 Server '{server_name}' stopped",
            'server_deleted': f"\U0001f5d1\ufe0f Server '{server_name}' deleted",
            'server_error': f"\u274c Error on server '{server_name}': {details.get('error', 'Unknown error')}"
        }
        message = {
            'embeds': [{
                'title': event_messages.get(event_type, f"Server event: {event_type}"),
                'description': json.dumps(details),
                'timestamp': datetime.now().isoformat(),
                'color': 0x007bff
            }]
        }
        return await self.broadcast(message)

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        return self.user_preferences.get(user_id, {
            'digest_enabled': False,
            'digest_interval': 'daily',
            'priority_minimum': 'info',
            'channels': ['discord'],
            'muted_events': []
        })

    async def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        self.user_preferences[user_id] = preferences
        self._save_preferences()
        return True

    async def send_with_priority(self, message: Dict[str, Any], priority: str = 'info', target_user: Optional[str] = None) -> bool:
        priority_levels = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
        if target_user:
            prefs = await self.get_user_preferences(target_user)
            min_priority = prefs.get('priority_minimum', 'info')
            if priority_levels.get(priority, 1) < priority_levels.get(min_priority, 1):
                return False
            if prefs.get('digest_enabled'):
                digest_file = f"digest_{target_user}.json"
                digest_queue = []
                if os.path.exists(digest_file):
                    try:
                        with open(digest_file, 'r') as f:
                            digest_queue = json.load(f)
                    except Exception:
                        pass
                digest_queue.append({'message': message, 'priority': priority, 'timestamp': datetime.now().isoformat()})
                with open(digest_file, 'w') as f:
                    json.dump(digest_queue, f, indent=2)
                return True
            channels = prefs.get('channels', ['discord'])
            if 'discord' not in message and self.discord_webhook:
                for channel in channels:
                    if channel == 'discord':
                        message['priority'] = priority
                        await self.broadcast(message)
            return True
        message['priority'] = priority
        return await self.broadcast(message)

    async def send_digest(self, user_id: str) -> Dict[str, Any]:
        digest_file = f"digest_{user_id}.json"
        if not os.path.exists(digest_file):
            return {'user_id': user_id, 'messages': [], 'sent': False, 'reason': 'No queued messages'}
        with open(digest_file, 'r') as f:
            queue = json.load(f)
        summary = f"**Digest for {user_id}** - {len(queue)} messages"
        for item in queue:
            summary += f"\n- [{item['priority'].upper()}] {item['message'].get('embeds', [{}])[0].get('title', 'No title')}"
        await self.broadcast({'content': summary})
        os.remove(digest_file)
        return {'user_id': user_id, 'messages_count': len(queue), 'sent': True}


class UnifiedMetrics:
    """Integrated Monitoring - Unified metrics aggregation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8000')
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("UnifiedMetrics initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def collect_metrics(self) -> Dict[str, Any]:
        metrics = {'timestamp': datetime.now().isoformat(), 'services': {}}
        try:
            async with self.session.get(f"{self.service_core_url}/api/metrics") as resp:
                if resp.status == 200:
                    metrics['services']['service_core'] = await resp.json()
        except Exception as e:
            logger.warning(f"Service Core metrics collection failed: {e}")
        try:
            async with self.session.get(f"{self.orchestrator_url}/api/metrics") as resp:
                if resp.status == 200:
                    metrics['services']['orchestrator'] = await resp.json()
        except Exception as e:
            logger.warning(f"Orchestrator metrics collection failed: {e}")
        return metrics

    async def get_unified_dashboard(self) -> Dict[str, Any]:
        metrics = await self.collect_metrics()
        summary = {'total_servers': 0, 'active_servers': 0, 'total_cpu_percent': 0, 'total_memory_percent': 0, 'by_platform': {}}
        if 'services' in metrics:
            for platform, data in metrics['services'].items():
                if isinstance(data, dict):
                    server_count = data.get('server_count', 0)
                    summary['total_servers'] += server_count
                    summary['by_platform'][platform] = {
                        'servers': server_count,
                        'cpu': data.get('cpu_percent', 0),
                        'memory': data.get('memory_percent', 0)
                    }
        return {**metrics, 'summary': summary}

    async def get_prometheus_metrics(self) -> str:
        metrics = await self.collect_metrics()
        lines = ['# HELP integration_service_info Integration service metrics', '# TYPE integration_service_info gauge']
        lines.append(f'integration_service_info{{version="1.0.0"}} 1')
        for service, data in metrics.get('services', {}).items():
            if isinstance(data, dict):
                lines.append(f'integration_service_servers{{service="{service}"}} {data.get("server_count", 0)}')
                lines.append(f'integration_service_cpu{{service="{service}"}} {data.get("cpu_percent", 0)}')
                lines.append(f'integration_service_memory{{service="{service}"}} {data.get("memory_percent", 0)}')
        lines.append(f'integration_service_timestamp {datetime.now().timestamp()}')
        return '\n'.join(lines)


class SharedConfigManager:
    """Shared Configuration Management with versioning, diff, rollback, validation"""

    def __init__(self, config_path: str = 'shared_config.json'):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.version = 0
        self.history_file = config_path.replace('.json', '_history.json')
        self.history: List[Dict[str, Any]] = []
        self.overlays: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.version = self.config.pop('__version__', 0)
                logger.info(f"Loaded config v{self.version} from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config history: {e}")

    def save(self):
        try:
            self.config['__version__'] = self.version
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.config.pop('__version__', None)
            logger.info(f"Saved config v{self.version} to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        for env_name in reversed(list(self.overlays.keys())):
            if key in self.overlays[env_name]:
                return self.overlays[env_name][key]
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        old_value = self.config.get(key)
        self.history.append({
            'version': self.version,
            'key': key,
            'old_value': old_value,
            'new_value': value,
            'timestamp': datetime.now().isoformat()
        })
        self.config[key] = value
        self.version += 1
        self.save()
        self._save_history()

    def get_all(self) -> Dict[str, Any]:
        result = self.config.copy()
        for env_name, overlay in self.overlays.items():
            for k, v in overlay.items():
                result[f'{k}__{env_name}'] = v
        result['__version__'] = self.version
        return result

    def update(self, updates: Dict[str, Any]):
        snapshot = copy.deepcopy(self.config)
        self.history.append({
            'version': self.version,
            'type': 'bulk_update',
            'old_value': snapshot,
            'new_value': {**snapshot, **updates},
            'timestamp': datetime.now().isoformat()
        })
        self.config.update(updates)
        self.version += 1
        self.save()
        self._save_history()

    def get_version(self, version: int) -> Optional[Dict[str, Any]]:
        for entry in reversed(self.history):
            if entry.get('version') == version:
                if 'old_value' in entry and isinstance(entry['old_value'], dict):
                    return entry['old_value']
                return None
        return None

    def rollback(self, version: int) -> bool:
        target_config = self.get_version(version)
        if target_config is None:
            snapshot = copy.deepcopy(self.config)
            for entry in reversed(self.history):
                if entry.get('version', -1) >= version:
                    key = entry.get('key')
                    old_val = entry.get('old_value')
                    if key and key in self.config:
                        self.config[key] = old_val
            self.config['__version__'] = version
            self.version = version
        else:
            self.config = target_config
            self.version = version
        self.history.append({
            'version': self.version,
            'type': 'rollback',
            'timestamp': datetime.now().isoformat(),
            'rolled_back_to': version
        })
        self.save()
        self._save_history()
        return True

    def diff(self, version_a: int, version_b: int) -> Dict[str, Any]:
        config_a = self.get_version(version_a) or {}
        config_b = self.get_version(version_b) or {}
        added = {k: config_b[k] for k in config_b if k not in config_a}
        removed = {k: config_a[k] for k in config_a if k not in config_b}
        changed = {k: {'from': config_a[k], 'to': config_b[k]} for k in config_a if k in config_b and config_a[k] != config_b[k]}
        return {'version_a': version_a, 'version_b': version_b, 'added': added, 'removed': removed, 'changed': changed}

    def validate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        for key, expected_type in schema.items():
            value = self.get(key)
            if value is None:
                errors.append({'key': key, 'error': 'Missing', 'expected': str(expected_type)})
            elif not isinstance(value, expected_type):
                errors.append({'key': key, 'error': f'Expected {expected_type.__name__}, got {type(value).__name__}', 'expected': str(expected_type)})
        return {'valid': len(errors) == 0, 'errors': errors}

    def validate_config(self, content: str, format: str) -> Dict[str, Any]:
        errors = []
        valid = False
        if format == 'json':
            try:
                json.loads(content)
                valid = True
            except json.JSONDecodeError as e:
                errors.append(str(e))
        elif format == 'yaml':
            try:
                import yaml
                yaml.safe_load(content)
                valid = True
            except ImportError:
                try:
                    import json
                    json.loads(content)
                    valid = True
                except json.JSONDecodeError as e:
                    errors.append(str(e))
            except Exception as e:
                errors.append(str(e))
        else:
            errors.append(f'Unsupported format: {format}')
        return {'valid': valid, 'errors': errors}

    def set_overlay(self, env_name: str, config: Dict[str, Any]):
        self.overlays[env_name] = config

    def remove_overlay(self, env_name: str):
        self.overlays.pop(env_name, None)

    def bulk_update(self, updates: Dict[str, Any]) -> int:
        count = 0
        for k, v in updates.items():
            self.set(k, v)
            count += 1
        return count


class ModpackService:
    """Modpack search and retrieval from CurseForge and Modrinth."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.curseforge_api_key = os.getenv('CURSEFORGE_API_KEY', '')

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("ModpackService initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def search_modpacks(self, query: str, platform: str = 'all', limit: int = 20) -> list:
        results = []
        if platform in ('all', 'modrinth'):
            try:
                async with self.session.get(
                    'https://api.modrinth.com/v2/search',
                    params={'query': query, 'limit': limit, 'facets': '[[\"project_type:modpack\"]]'}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for hit in data.get('hits', []):
                            results.append({
                                'id': f'modrinth:{hit["project_id"]}',
                                'name': hit['title'],
                                'platform': 'modrinth',
                                'summary': hit.get('description', ''),
                                'downloads': hit.get('downloads', 0),
                                'iconUrl': hit.get('icon_url', ''),
                                'minecraftVersions': hit.get('versions', []),
                                'loaders': hit.get('categories', []),
                                'url': f'https://modrinth.com/modpack/{hit["slug"]}',
                            })
            except Exception as e:
                logger.error(f'Modrinth search error: {e}')
        if platform in ('all', 'curseforge'):
            if not self.curseforge_api_key:
                logger.warning('CURSEFORGE_API_KEY not set')
            else:
                try:
                    async with self.session.get(
                        'https://api.curseforge.com/v1/mods/search',
                        params={'gameId': 432, 'slug': query, 'pageSize': limit},
                        headers={'x-api-key': self.curseforge_api_key}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for mod in data.get('data', []):
                                if mod.get('classId') == 4471:
                                    latest = mod.get('latestFiles', [{}])[0] if mod.get('latestFiles') else {}
                                    results.append({
                                        'id': f'curseforge:{mod["id"]}',
                                        'name': mod['name'],
                                        'platform': 'curseforge',
                                        'summary': mod.get('summary', ''),
                                        'downloads': mod.get('downloadCount', 0),
                                        'iconUrl': mod.get('logo', {}).get('url', ''),
                                        'minecraftVersions': [latest.get('gameVersion', '')] if latest else [],
                                        'loaders': latest.get('modLoaders', []) if latest else [],
                                        'url': mod.get('links', {}).get('websiteUrl', ''),
                                    })
                except Exception as e:
                    logger.error(f'CurseForge search error: {e}')
        results.sort(key=lambda r: r['downloads'], reverse=True)
        return results[:limit]

    async def get_modpack_details(self, platform: str, modpack_id: str) -> dict:
        if platform == 'modrinth':
            try:
                async with self.session.get(
                    f'https://api.modrinth.com/v2/project/{modpack_id}/version'
                ) as resp:
                    if resp.status == 200:
                        versions = await resp.json()
                        if versions:
                            latest = versions[0]
                            files = []
                            for f in latest.get('files', []):
                                files.append({
                                    'url': f['url'],
                                    'filename': f.get('filename', ''),
                                    'primary': f.get('primary', False),
                                    'size': f.get('size', 0),
                                })
                            return {
                                'id': f'modrinth:{modpack_id}',
                                'platform': 'modrinth',
                                'versions': [{
                                    'id': latest['id'],
                                    'name': latest.get('name', ''),
                                    'version_number': latest.get('version_number', ''),
                                    'game_versions': latest.get('game_versions', []),
                                    'loaders': latest.get('loaders', []),
                                    'files': files,
                                }],
                            }
            except Exception as e:
                logger.error(f'Modrinth details error: {e}')
        elif platform == 'curseforge':
            if not self.curseforge_api_key:
                return {'error': 'CURSEFORGE_API_KEY not set'}
            try:
                async with self.session.get(
                    f'https://api.curseforge.com/v1/mods/{modpack_id}/files',
                    headers={'x-api-key': self.curseforge_api_key}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        files = []
                        for f in data.get('data', []):
                            files.append({
                                'url': f.get('downloadUrl', ''),
                                'filename': f.get('fileName', ''),
                                'primary': f.get('isPrimary', False),
                                'size': f.get('fileLength', 0),
                            })
                        return {
                            'id': f'curseforge:{modpack_id}',
                            'platform': 'curseforge',
                            'files': files,
                        }
            except Exception as e:
                logger.error(f'CurseForge details error: {e}')
        return {'error': 'Not found'}


class IntegrationService:
    """Main Integration Service - Coordinates all integration features"""

    def __init__(self, config_path: str = 'integration_config.json'):
        self.config = self._load_config(config_path)
        self.user_manager = UnifiedUserManager(self.config)
        self.notifier = CrossPlatformNotifier(self.config)
        self.metrics = UnifiedMetrics(self.config)
        self.config_manager = SharedConfigManager()
        self._managers: Dict[str, Any] = {}
        self._init_managers()

    def _init_managers(self):
        from auth import AuthManager
        from users import UserProfileManager
        from messaging import MessageBridge
        from commands import CommandExecutor
        from events import EventBroadcaster
        from alerts import AlertManager
        from announcements import AnnouncementScheduler
        from permissions import PermissionManager
        from alert_fatigue import AlertFatigueReducer
        from compliance_reports import ComplianceReportManager
        from secrets_manager import SecretsManager
        from siem_exporter import SIEMExporter
        from gdpr_manager import GDPRDataManager
        from log_analyzer import LogAnomalyDetector
        from ai_assistant import AIAssistant
        from backup_validator import BackupValidator
        from ticket_triage import TicketTriage
        from webhook_bus import WebhookEventBus
        from api_gateway import APIGateway
        from opentelemetry_exporter import OpenTelemetryExporter
        from graphql_api import GraphQLHandler
        from multi_region import MultiRegionManager
        from cdn_waf import CDNWAFManager
        from service_mesh import ServiceMeshManager
        from workspaces import WorkspaceManager
        self.auth = AuthManager(self.config)
        self.user_profiles = UserProfileManager(self.config)
        self.message_bridge = MessageBridge(self.config)
        self.command_executor = CommandExecutor(self.config)
        self.event_broadcaster = EventBroadcaster(self.config)
        self.alert_manager = AlertManager(self.config)
        self.announcement_scheduler = AnnouncementScheduler(self.config)
        self.permission_manager = PermissionManager(self.config)
        self.alert_fatigue = AlertFatigueReducer(self.config)
        self.compliance_reports = ComplianceReportManager(self.config)
        self.secrets_manager = SecretsManager(self.config)
        self.siem_exporter = SIEMExporter(self.config)
        self.gdpr_manager = GDPRDataManager(self.config)
        self.log_anomaly_detector = LogAnomalyDetector(self.config)
        self.ai_assistant = AIAssistant(self.config)
        self.backup_validator = BackupValidator(self.config)
        self.ticket_triage = TicketTriage(self.config)
        self.webhook_bus = WebhookEventBus(self.config)
        self.api_gateway = APIGateway(self.config)
        self.otel_exporter = OpenTelemetryExporter(self.config)
        self.graphql_handler = GraphQLHandler(self.config)
        self.multi_region = MultiRegionManager(self.config)
        self.cdn_waf = CDNWAFManager(self.config)
        self.service_mesh = ServiceMeshManager(self.config)
        self.workspaces = WorkspaceManager(self.config)
        self._managers = {
            'auth': self.auth, 'user_profiles': self.user_profiles,
            'message_bridge': self.message_bridge, 'command_executor': self.command_executor,
            'event_broadcaster': self.event_broadcaster, 'alert_manager': self.alert_manager,
            'announcement_scheduler': self.announcement_scheduler, 'permission_manager': self.permission_manager,
            'alert_fatigue': self.alert_fatigue, 'compliance_reports': self.compliance_reports,
            'secrets_manager': self.secrets_manager, 'siem_exporter': self.siem_exporter,
            'gdpr_manager': self.gdpr_manager,
            'log_anomaly_detector': self.log_anomaly_detector,
            'ai_assistant': self.ai_assistant,
            'backup_validator': self.backup_validator,
            'ticket_triage': self.ticket_triage,
            'webhook_bus': self.webhook_bus, 'api_gateway': self.api_gateway,
            'otel_exporter': self.otel_exporter, 'graphql_handler': self.graphql_handler,
            'multi_region': self.multi_region, 'cdn_waf': self.cdn_waf,
            'service_mesh': self.service_mesh, 'workspaces': self.workspaces
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
        return {
            'dashboard_url': os.getenv('DASHBOARD_URL', 'http://localhost:5173'),
            'discord_api_url': os.getenv('DISCORD_API_URL', 'http://localhost:3001'),
            'service_core_url': os.getenv('SERVICE_CORE_URL', 'http://localhost:8080'),
            'orchestrator_url': os.getenv('ORCHESTRATOR_URL', 'http://localhost:8000'),
            'discord_webhook': os.getenv('DISCORD_WEBHOOK'),
            'jwt_secret': os.getenv('JWT_SECRET', 'default-secret-change-me')
        }

    async def start(self):
        await self.user_manager.initialize()
        await self.notifier.initialize()
        await self.metrics.initialize()
        await self.message_bridge.initialize()
        await self.announcement_scheduler.start()
        for name, mgr in self._managers.items():
            if hasattr(mgr, 'start'):
                await mgr.start()
        logger.info("Integration Service started with all managers")

    async def stop(self):
        await self.user_manager.close()
        await self.notifier.close()
        await self.metrics.close()
        await self.message_bridge.close()
        await self.announcement_scheduler.stop()
        for name, mgr in self._managers.items():
            if hasattr(mgr, 'stop'):
                await mgr.stop()
        logger.info("Integration Service stopped")


if __name__ == '__main__':
    service = IntegrationService()
    asyncio.run(service.start())
