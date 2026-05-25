import asyncio
import logging
from aiohttp import web
import json
from typing import Dict, Any
import os
from datetime import datetime, timedelta

from integration import (
    IntegrationService,
    UnifiedUserManager,
    CrossPlatformNotifier,
    UnifiedMetrics,
    SharedConfigManager
)
from auth import AuthManager
from users import UserProfileManager
from messaging import MessageBridge
from commands import CommandExecutor
from events import EventBroadcaster
from alerts import AlertManager
from announcements import AnnouncementScheduler
from permissions import PermissionManager
from logging import CrossPlatformLogger, ServerLogsIntegrator, BackupLogManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationAPIServer:
    """REST API for Integration Service with auth middleware and cross-platform features"""

    def __init__(self, config_path: str = 'integration_config.json'):
        self.service = IntegrationService(config_path)
        self.app = web.Application(middlewares=[self.auth_middleware])
        self._setup_routes()
        self.config_manager = SharedConfigManager()
        self.auth_manager: AuthManager = self.service.auth
        self.user_profiles: UserProfileManager = self.service.user_profiles
        self.message_bridge: MessageBridge = self.service.message_bridge
        self.command_executor: CommandExecutor = self.service.command_executor
        self.event_broadcaster: EventBroadcaster = self.service.event_broadcaster
        self.alert_manager: AlertManager = self.service.alert_manager
        self.announcement_scheduler: AnnouncementScheduler = self.service.announcement_scheduler
        self.permission_manager: PermissionManager = self.service.permission_manager
        from logging import UnifiedLogger
        from backup import BackupManager, UnifiedReporting
        from resource_tracker import (
            UnifiedResourceTracker, SharedResourcePoolManager, ResourceSynchronizer,
            ResourceAllocationManager, ResourceSchedulingCoordinator, ResourceOptimizationCoordinator
        )
        self.unified_logger = UnifiedLogger('integration-api')
        self.cross_logger = CrossPlatformLogger(self.service.config)
        self.server_logs = ServerLogsIntegrator(self.service.config)
        self.backup_log_manager = BackupLogManager(self.service.config)
        self.backup_manager = BackupManager(self.service.config)
        self.reporting = UnifiedReporting(self.service.config)
        self.resource_tracker = UnifiedResourceTracker(self.service.config)
        self.pool_manager = SharedResourcePoolManager(self.service.config)
        self.resource_sync = ResourceSynchronizer(self.service.config)
        self.resource_alloc = ResourceAllocationManager(self.service.config, self.resource_tracker)
        self.resource_sched = ResourceSchedulingCoordinator(self.service.config)
        self.resource_optim = ResourceOptimizationCoordinator(self.service.config, self.resource_tracker)

    @web.middleware
    async def auth_middleware(self, request: web.Request, handler) -> web.Response:
        public_paths = ['/', '/health', '/api/auth/login', '/api/auth/verify']
        if request.path in public_paths or request.path.startswith('/api/auth/'):
            return await handler(request)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return web.json_response({'error': 'Missing or invalid Authorization header'}, status=401)
        token = auth_header[7:]
        payload = await self.auth_manager.verify_token(token)
        if payload:
            request['user'] = payload
            return await handler(request)
        key_data = await self.auth_manager.validate_api_key(token)
        if key_data:
            request['user'] = key_data
            return await handler(request)
        return web.json_response({'error': 'Invalid or expired token'}, status=401)

    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_post('/api/auth/login', self.handle_auth_login)
        self.app.router.add_post('/api/auth/verify', self.handle_auth_verify)
        self.app.router.add_post('/api/auth/api-key', self.handle_auth_api_key)
        self.app.router.add_post('/api/auth/oauth2/{platform}', self.handle_auth_oauth2)
        self.app.router.add_post('/api/auth/oauth2/{platform}/callback', self.handle_auth_oauth2_callback)
        self.app.router.add_post('/api/auth/token-exchange', self.handle_auth_token_exchange)
        self.app.router.add_post('/api/users', self.handle_create_user)
        self.app.router.add_get('/api/users/{email}', self.handle_get_user)
        self.app.router.add_put('/api/users/{email}', self.handle_update_user)
        self.app.router.add_get('/api/users/{email}/profile', self.handle_get_unified_profile)
        self.app.router.add_put('/api/users/{email}/profile', self.handle_update_profile)
        self.app.router.add_post('/api/users/{email}/link', self.handle_link_account)
        self.app.router.add_get('/api/users/search', self.handle_search_users)
        self.app.router.add_post('/api/users/{email}/sync', self.handle_sync_user)
        self.app.router.add_post('/api/notifications', self.handle_notification)
        self.app.router.add_post('/api/notifications/server-event', self.handle_server_event)
        self.app.router.add_get('/api/notifications/preferences/{user_id}', self.handle_get_preferences)
        self.app.router.add_put('/api/notifications/preferences/{user_id}', self.handle_set_preferences)
        self.app.router.add_post('/api/notifications/digest/{user_id}', self.handle_send_digest)
        self.app.router.add_post('/api/notifications/priority', self.handle_notification_priority)
        self.app.router.add_post('/api/messaging/bridge', self.handle_message_bridge)
        self.app.router.add_post('/api/messaging/webhook/{platform}', self.handle_messaging_webhook)
        self.app.router.add_post('/api/messaging/convert', self.handle_format_convert)
        self.app.router.add_post('/api/commands/execute', self.handle_execute_command)
        self.app.router.add_get('/api/commands', self.handle_list_commands)
        self.app.router.add_post('/api/commands/register', self.handle_register_command)
        self.app.router.add_get('/api/commands/audit', self.handle_command_audit)
        self.app.router.add_post('/api/events/broadcast', self.handle_broadcast_event)
        self.app.router.add_get('/api/events', self.handle_get_events)
        self.app.router.add_post('/api/events/listener', self.handle_register_listener)
        self.app.router.add_post('/api/events/player/join', self.handle_player_join)
        self.app.router.add_post('/api/events/player/leave', self.handle_player_leave)
        self.app.router.add_post('/api/events/player/achievement', self.handle_player_achievement)
        self.app.router.add_post('/api/events/player/vote', self.handle_player_vote)
        self.app.router.add_post('/api/alerts', self.handle_create_alert)
        self.app.router.add_get('/api/alerts', self.handle_get_alerts)
        self.app.router.add_post('/api/alerts/{alert_id}/acknowledge', self.handle_acknowledge_alert)
        self.app.router.add_put('/api/alerts/channels/{channel_type}', self.handle_configure_channel)
        self.app.router.add_post('/api/announcements', self.handle_schedule_announcement)
        self.app.router.add_get('/api/announcements', self.handle_get_announcements)
        self.app.router.add_delete('/api/announcements/{announcement_id}', self.handle_cancel_announcement)
        self.app.router.add_post('/api/announcements/templates', self.handle_create_template)
        self.app.router.add_get('/api/announcements/templates', self.handle_get_templates)
        self.app.router.add_get('/api/metrics', self.handle_metrics)
        self.app.router.add_get('/api/metrics/dashboard', self.handle_metrics_dashboard)
        self.app.router.add_get('/api/metrics/prometheus', self.handle_metrics_prometheus)
        self.app.router.add_get('/api/metrics/statistics', self.handle_cross_platform_stats)
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_put('/api/config', self.handle_update_config)
        self.app.router.add_get('/api/config/version/{version}', self.handle_get_config_version)
        self.app.router.add_post('/api/config/rollback/{version}', self.handle_rollback_config)
        self.app.router.add_get('/api/config/diff/{version_a}/{version_b}', self.handle_diff_config)
        self.app.router.add_post('/api/config/validate', self.handle_validate_config)
        self.app.router.add_post('/api/config/overlay/{env_name}', self.handle_set_overlay)
        self.app.router.add_post('/api/permissions/check', self.handle_check_permission)
        self.app.router.add_post('/api/permissions/grant', self.handle_grant_permission)
        self.app.router.add_post('/api/permissions/revoke', self.handle_revoke_permission)
        self.app.router.add_get('/api/permissions/user/{user_id}', self.handle_get_user_permissions)
        self.app.router.add_post('/api/permissions/roles', self.handle_create_role)
        self.app.router.add_post('/api/permissions/roles/assign', self.handle_assign_role)
        self.app.router.add_post('/api/backups', self.handle_create_backup)
        self.app.router.add_get('/api/backups', self.handle_list_backups)
        self.app.router.add_post('/api/backups/restore', self.handle_restore_backup)
        self.app.router.add_post('/api/backups/verify', self.handle_verify_backup)
        self.app.router.add_delete('/api/backups/cleanup', self.handle_cleanup_backups)
        self.app.router.add_post('/api/backups/cross-service', self.handle_cross_service_backup)
        self.app.router.add_post('/api/backups/cross-service/restore', self.handle_atomic_restore)
        self.app.router.add_get('/api/backups/logs', self.handle_backup_logs)
        self.app.router.add_get('/api/backups/stats', self.handle_backup_stats)
        self.app.router.add_get('/api/resources', self.handle_get_resources)
        self.app.router.add_post('/api/resources/allocate', self.handle_allocate_resource)
        self.app.router.add_post('/api/resources/pools', self.handle_create_pool)
        self.app.router.add_get('/api/resources/pools', self.handle_get_pools)
        self.app.router.add_post('/api/resources/pools/allocate', self.handle_allocate_from_pool)
        self.app.router.add_post('/api/resources/sync', self.handle_sync_resources)
        self.app.router.add_get('/api/resources/allocation', self.handle_allocation_vs_usage)
        self.app.router.add_get('/api/resources/usage', self.handle_resource_usage)
        self.app.router.add_get('/api/resources/cost', self.handle_cost_allocation)
        self.app.router.add_get('/api/resources/trends', self.handle_trend_analysis)
        self.app.router.add_get('/api/resources/forecast', self.handle_forecast)
        self.app.router.add_get('/api/resources/rebalance', self.handle_rebalance_suggestions)
        self.app.router.add_post('/api/resources/optimization/analyze', self.handle_optimization_analyze)
        self.app.router.add_post('/api/resources/schedule', self.handle_schedule_event)
        self.app.router.add_get('/api/resources/schedule', self.handle_get_schedule)
        self.app.router.add_post('/api/logs/search', self.handle_log_search)
        self.app.router.add_get('/api/logs/levels', self.handle_log_levels)
        self.app.router.add_post('/api/logs/cross-platform', self.handle_cross_platform_log)
        self.app.router.add_get('/api/logs/cross-platform', self.handle_query_cross_platform_logs)
        self.app.router.add_post('/api/logs/server/ingest', self.handle_server_log_ingest)
        self.app.router.add_get('/api/logs/server/tail', self.handle_server_log_tail)
        self.app.router.add_get('/api/logs/backup', self.handle_backup_log_manager)
        self.app.router.add_get('/api/logs/backup/stats', self.handle_backup_log_stats)
        self.app.router.add_get('/api/monitoring', self.handle_integrated_monitoring)
        self.app.router.add_get('/api/monitoring/alerts', self.handle_alert_correlation)
        self.app.router.add_post('/api/maintenance/windows', self.handle_create_maintenance_window)
        self.app.router.add_get('/api/maintenance/windows', self.handle_get_schedule)
        self.app.router.add_get('/api/security/events', self.handle_security_events)
        self.app.router.add_post('/api/security/alert', self.handle_security_alert)
        self.app.router.add_post('/api/reports/usage', self.handle_usage_report)
        self.app.router.add_post('/api/reports/billing', self.handle_billing_report)
        self.app.router.add_post('/api/reports/security', self.handle_security_report)
        self.app.router.add_post('/api/reports/performance', self.handle_performance_report)
        self.app.router.add_get('/api/reports', self.handle_list_reports)
        self.app.router.add_get('/api/integrated/resource-management', self.handle_integrated_resource_management)

    async def handle_index(self, request: web.Request) -> web.Response:
        return web.json_response({
            'service': 'Integration Service',
            'version': '2.0.0',
            'features': [
                'auth', 'users', 'notifications', 'messaging', 'commands',
                'events', 'alerts', 'announcements', 'metrics', 'config',
                'permissions', 'backups', 'resources', 'logs', 'monitoring',
                'maintenance', 'security', 'reports'
            ]
        })

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({'status': 'healthy', 'service': 'integration-service'})

    async def handle_auth_login(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            result = await self.auth_manager.login(data.get('email', ''), data.get('password', ''))
            return web.json_response(result)
        except ValueError as e:
            return web.json_response({'error': str(e)}, status=401)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_auth_verify(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            result = await self.auth_manager.verify(data.get('token', ''))
            return web.json_response(result)
        except ValueError as e:
            return web.json_response({'error': str(e)}, status=401)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_auth_api_key(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            result = await self.auth_manager.create_api_key(
                data.get('user_id', ''), data.get('name', ''), data.get('role', 'user'), data.get('expires_in_days')
            )
            return web.json_response(result, status=201)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_auth_oauth2(self, request: web.Request) -> web.Response:
        platform = request.match_info['platform']
        data = await request.json()
        result = await self.auth_manager.oauth2_authorize(platform, data.get('redirect_uri', ''))
        return web.json_response(result)

    async def handle_auth_oauth2_callback(self, request: web.Request) -> web.Response:
        platform = request.match_info['platform']
        data = await request.json()
        result = await self.auth_manager.oauth2_callback(platform, data.get('code', ''), data.get('state', ''))
        return web.json_response(result)

    async def handle_auth_token_exchange(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.auth_manager.exchange_token(data.get('platform_token', ''), data.get('platform', ''))
        return web.json_response(result)

    async def handle_create_user(self, request: web.Request) -> web.Response:
        try:
            user_data = await request.json()
            result = await self.service.user_manager.create_user(user_data)
            return web.json_response(result, status=201)
        except Exception as e:
            logger.error(f"Create user failed: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def handle_get_user(self, request: web.Request) -> web.Response:
        email = request.match_info['email']
        profile = await self.service.user_manager.get_unified_profile(email)
        return web.json_response(profile)

    async def handle_update_user(self, request: web.Request) -> web.Response:
        try:
            email = request.match_info['email']
            updates = await request.json()
            success = await self.service.user_manager.update_user(email, updates)
            return web.json_response({'success': success})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_get_unified_profile(self, request: web.Request) -> web.Response:
        user_id = request.match_info['email']
        profile = await self.user_profiles.get_unified_profile(user_id)
        return web.json_response(profile)

    async def handle_update_profile(self, request: web.Request) -> web.Response:
        user_id = request.match_info['email']
        updates = await request.json()
        success = await self.user_profiles.update_profile(user_id, updates)
        return web.json_response({'success': success})

    async def handle_link_account(self, request: web.Request) -> web.Response:
        user_id = request.match_info['email']
        data = await request.json()
        success = await self.user_profiles.link_account(user_id, data.get('platform', ''), data.get('platform_user_id', ''))
        return web.json_response({'success': success})

    async def handle_search_users(self, request: web.Request) -> web.Response:
        query = request.query.get('q', '')
        users = await self.user_profiles.search_users(query)
        return web.json_response(users)

    async def handle_sync_user(self, request: web.Request) -> web.Response:
        email = request.match_info['email']
        data = await request.json()
        platform = data.get('platform', '')
        if data.get('type') == 'profile':
            result = await self.service.user_manager.profile_sync_on_login(platform, email)
        else:
            result = await self.service.user_manager.sync_roles(email)
        return web.json_response(result)

    async def handle_notification(self, request: web.Request) -> web.Response:
        try:
            message = await request.json()
            success = await self.service.notifier.broadcast(message)
            return web.json_response({'success': success})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_server_event(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            success = await self.service.notifier.notify_server_event(
                data.get('event_type', ''), data.get('server_name', ''), data.get('details', {})
            )
            return web.json_response({'success': success})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_get_preferences(self, request: web.Request) -> web.Response:
        user_id = request.match_info['user_id']
        prefs = await self.service.notifier.get_user_preferences(user_id)
        return web.json_response(prefs)

    async def handle_set_preferences(self, request: web.Request) -> web.Response:
        user_id = request.match_info['user_id']
        prefs = await request.json()
        success = await self.service.notifier.set_user_preferences(user_id, prefs)
        return web.json_response({'success': success})

    async def handle_send_digest(self, request: web.Request) -> web.Response:
        user_id = request.match_info['user_id']
        result = await self.service.notifier.send_digest(user_id)
        return web.json_response(result)

    async def handle_notification_priority(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.service.notifier.send_with_priority(
            data.get('message', {}), data.get('priority', 'info'), data.get('target_user')
        )
        return web.json_response({'success': success})

    async def handle_message_bridge(self, request: web.Request) -> web.Response:
        data = await request.json()
        source = data.get('source', 'discord')
        if source == 'discord':
            success = await self.message_bridge.send_discord_to_minecraft(data)
        else:
            success = await self.message_bridge.send_minecraft_to_discord(data)
        return web.json_response({'success': success})

    async def handle_messaging_webhook(self, request: web.Request) -> web.Response:
        platform = request.match_info['platform']
        payload = await request.json()
        success = await self.message_bridge.process_webhook(platform, payload)
        return web.json_response({'success': success})

    async def handle_format_convert(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.message_bridge.convert_format(
            data.get('text', ''), data.get('from_format', 'markdown'), data.get('to_format', 'minecraft')
        )
        return web.json_response(result)

    async def handle_execute_command(self, request: web.Request) -> web.Response:
        data = await request.json()
        user = request.get('user', {})
        result = await self.command_executor.execute_command(
            data.get('command', ''), data.get('platform', 'discord'),
            data.get('user_id', user.get('user_id', 'unknown')),
            data.get('user_roles')
        )
        return web.json_response(result)

    async def handle_list_commands(self, request: web.Request) -> web.Response:
        platform = request.query.get('platform')
        commands = await self.command_executor.list_commands(platform)
        return web.json_response(commands)

    async def handle_register_command(self, request: web.Request) -> web.Response:
        command_def = await request.json()
        result = await self.command_executor.register_command(command_def)
        return web.json_response(result, status=201)

    async def handle_command_audit(self, request: web.Request) -> web.Response:
        user_id = request.query.get('user_id')
        limit = int(request.query.get('limit', 100))
        logs = await self.command_executor.get_audit_log(limit, user_id)
        return web.json_response(logs)

    async def handle_broadcast_event(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.event_broadcaster.broadcast_event(data.get('event_type', ''), data.get('data', {}))
        return web.json_response(result)

    async def handle_get_events(self, request: web.Request) -> web.Response:
        event_type = request.query.get('event_type')
        limit = int(request.query.get('limit', 100))
        events = await self.event_broadcaster.get_events(event_type, limit)
        return web.json_response(events)

    async def handle_register_listener(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.event_broadcaster.register_listener(data.get('event_type', ''), data.get('platform', ''), data.get('webhook_url', ''))
        return web.json_response({'success': success})

    async def handle_player_join(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.event_broadcaster.player_join(data.get('player_name', ''), data.get('uuid', ''), data.get('server', ''))
        return web.json_response(result)

    async def handle_player_leave(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.event_broadcaster.player_leave(data.get('player_name', ''), data.get('uuid', ''), data.get('server', ''))
        return web.json_response(result)

    async def handle_player_achievement(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.event_broadcaster.achievement_unlocked(data.get('player_name', ''), data.get('uuid', ''), data.get('achievement', ''), data.get('server', ''))
        return web.json_response(result)

    async def handle_player_vote(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.event_broadcaster.vote_received(data.get('player_name', ''), data.get('uuid', ''), data.get('vote_count', 0), data.get('server', ''))
        return web.json_response(result)

    async def handle_create_alert(self, request: web.Request) -> web.Response:
        data = await request.json()
        alert = await self.alert_manager.create_alert(data)
        return web.json_response(alert, status=201)

    async def handle_get_alerts(self, request: web.Request) -> web.Response:
        status = request.query.get('status')
        severity = request.query.get('severity')
        limit = int(request.query.get('limit', 100))
        alerts = await self.alert_manager.get_alerts(status, severity, limit)
        return web.json_response(alerts)

    async def handle_acknowledge_alert(self, request: web.Request) -> web.Response:
        alert_id = request.match_info['alert_id']
        data = await request.json()
        success = await self.alert_manager.acknowledge_alert(alert_id, data.get('user_id', ''))
        return web.json_response({'success': success})

    async def handle_configure_channel(self, request: web.Request) -> web.Response:
        channel_type = request.match_info['channel_type']
        config = await request.json()
        success = await self.alert_manager.configure_channel(channel_type, config)
        return web.json_response({'success': success})

    async def handle_schedule_announcement(self, request: web.Request) -> web.Response:
        data = await request.json()
        ann = await self.announcement_scheduler.schedule_announcement(data)
        return web.json_response(ann, status=201)

    async def handle_get_announcements(self, request: web.Request) -> web.Response:
        announcements = await self.announcement_scheduler.get_scheduled()
        return web.json_response(announcements)

    async def handle_cancel_announcement(self, request: web.Request) -> web.Response:
        ann_id = request.match_info['announcement_id']
        success = await self.announcement_scheduler.cancel(ann_id)
        return web.json_response({'success': success})

    async def handle_create_template(self, request: web.Request) -> web.Response:
        data = await request.json()
        template = await self.announcement_scheduler.create_template(data.get('name', ''), data.get('content', ''))
        return web.json_response(template, status=201)

    async def handle_get_templates(self, request: web.Request) -> web.Response:
        templates = await self.announcement_scheduler.get_templates()
        return web.json_response(templates)

    async def handle_metrics(self, request: web.Request) -> web.Response:
        metrics = await self.service.metrics.collect_metrics()
        return web.json_response(metrics)

    async def handle_metrics_dashboard(self, request: web.Request) -> web.Response:
        dashboard = await self.service.metrics.get_unified_dashboard()
        return web.json_response(dashboard)

    async def handle_metrics_prometheus(self, request: web.Request) -> web.Response:
        metrics_text = await self.service.metrics.get_prometheus_metrics()
        return web.Response(text=metrics_text, content_type='text/plain')

    async def handle_cross_platform_stats(self, request: web.Request) -> web.Response:
        metrics = await self.service.metrics.collect_metrics()
        events = await self.event_broadcaster.get_events(limit=1000)
        stats = {
            'total_events': len(events),
            'events_by_type': {},
            'services': metrics.get('services', {}),
            'timestamp': metrics.get('timestamp')
        }
        for e in events:
            et = e.get('event_type', 'unknown')
            stats['events_by_type'][et] = stats['events_by_type'].get(et, 0) + 1
        return web.json_response(stats)

    async def handle_get_config(self, request: web.Request) -> web.Response:
        return web.json_response(self.config_manager.get_all())

    async def handle_update_config(self, request: web.Request) -> web.Response:
        try:
            updates = await request.json()
            self.config_manager.update(updates)
            return web.json_response({'success': True, 'version': self.config_manager.version})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def handle_get_config_version(self, request: web.Request) -> web.Response:
        version = int(request.match_info['version'])
        config = self.config_manager.get_version(version)
        if config:
            return web.json_response(config)
        return web.json_response({'error': 'Version not found'}, status=404)

    async def handle_rollback_config(self, request: web.Request) -> web.Response:
        version = int(request.match_info['version'])
        success = self.config_manager.rollback(version)
        return web.json_response({'success': success, 'version': self.config_manager.version})

    async def handle_diff_config(self, request: web.Request) -> web.Response:
        v1 = int(request.match_info['version_a'])
        v2 = int(request.match_info['version_b'])
        diff = self.config_manager.diff(v1, v2)
        return web.json_response(diff)

    async def handle_validate_config(self, request: web.Request) -> web.Response:
        schema = await request.json()
        result = self.config_manager.validate(schema)
        return web.json_response(result)

    async def handle_set_overlay(self, request: web.Request) -> web.Response:
        env_name = request.match_info['env_name']
        config = await request.json()
        self.config_manager.set_overlay(env_name, config)
        return web.json_response({'success': True})

    async def handle_check_permission(self, request: web.Request) -> web.Response:
        data = await request.json()
        granted = await self.permission_manager.check_permission(data.get('user_id', ''), data.get('permission', ''), data.get('resource'))
        return web.json_response({'granted': granted})

    async def handle_grant_permission(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.permission_manager.grant_permission(data.get('user_id', ''), data.get('permission', ''), data.get('resource'))
        return web.json_response({'success': success})

    async def handle_revoke_permission(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.permission_manager.revoke_permission(data.get('user_id', ''), data.get('permission', ''), data.get('resource'))
        return web.json_response({'success': success})

    async def handle_get_user_permissions(self, request: web.Request) -> web.Response:
        user_id = request.match_info['user_id']
        perms = await self.permission_manager.get_user_permissions(user_id)
        return web.json_response(perms)

    async def handle_create_role(self, request: web.Request) -> web.Response:
        data = await request.json()
        role = await self.permission_manager.create_role(data.get('name', ''), data.get('permissions', []), data.get('admin', False), data.get('inherits'))
        return web.json_response(role, status=201)

    async def handle_assign_role(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.permission_manager.assign_role(data.get('user_id', ''), data.get('role_name', ''))
        return web.json_response({'success': success})

    async def handle_create_backup(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.backup_manager.create_backup(data.get('service', 'all'), data.get('server_id'))
        return web.json_response(result)

    async def handle_list_backups(self, request: web.Request) -> web.Response:
        backups = self.backup_manager.list_backups()
        return web.json_response(backups)

    async def handle_restore_backup(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.backup_manager.restore_backup(data.get('backup_id', ''), data.get('service', ''))
        return web.json_response({'success': success})

    async def handle_verify_backup(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.backup_manager.verify_backup(data.get('backup_id', ''), data.get('service', ''))
        return web.json_response(result)

    async def handle_cleanup_backups(self, request: web.Request) -> web.Response:
        days = int(request.query.get('days', 30))
        removed = await self.backup_manager.cleanup_old_backups(days)
        return web.json_response({'removed': removed})

    async def handle_cross_service_backup(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.backup_manager.cross_service_backup(data.get('services', ['service_core', 'orchestrator']))
        return web.json_response(result)

    async def handle_atomic_restore(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.backup_manager.atomic_multi_service_restore(data.get('backup_id', ''))
        return web.json_response(result)

    async def handle_backup_logs(self, request: web.Request) -> web.Response:
        limit = int(request.query.get('limit', 100))
        service = request.query.get('service')
        logs = await self.backup_manager.get_backup_logs(limit, service)
        return web.json_response(logs)

    async def handle_backup_stats(self, request: web.Request) -> web.Response:
        stats = await self.backup_manager.get_backup_stats()
        return web.json_response(stats)

    async def handle_get_resources(self, request: web.Request) -> web.Response:
        resources = await self.resource_tracker.get_all_resources()
        return web.json_response(resources)

    async def handle_allocate_resource(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.resource_tracker.allocate_resource(data.get('service', ''), data.get('resource_type', ''), data.get('amount', 0))
        return web.json_response(result)

    async def handle_create_pool(self, request: web.Request) -> web.Response:
        data = await request.json()
        pool = await self.pool_manager.create_pool(data.get('name', ''), data.get('cpu_cores', 0), data.get('memory_mb', 0), data.get('storage_gb', 0))
        return web.json_response(pool, status=201)

    async def handle_get_pools(self, request: web.Request) -> web.Response:
        pools = await self.pool_manager.get_pools()
        return web.json_response(pools)

    async def handle_allocate_from_pool(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await self.pool_manager.allocate_from_pool(data.get('pool_name', ''), data.get('service', ''), data.get('cpu_cores', 0), data.get('memory_mb', 0), data.get('storage_gb', 0))
        return web.json_response(result)

    async def handle_sync_resources(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.resource_sync.initialize()
        result = await self.resource_sync.sync_allocations(data)
        await self.resource_sync.close()
        return web.json_response(result)

    async def handle_allocation_vs_usage(self, request: web.Request) -> web.Response:
        avu = await self.resource_alloc.get_allocation_vs_usage()
        return web.json_response(avu)

    async def handle_resource_usage(self, request: web.Request) -> web.Response:
        user_id = request.query.get('user_id')
        usage = await self.resource_tracker.get_resource_usage(user_id)
        return web.json_response(usage)

    async def handle_cost_allocation(self, request: web.Request) -> web.Response:
        start = request.query.get('start', (datetime.now() - timedelta(days=30)).isoformat())
        end = request.query.get('end', datetime.now().isoformat())
        cost = await self.resource_tracker.get_cost_allocation(start, end)
        return web.json_response(cost)

    async def handle_trend_analysis(self, request: web.Request) -> web.Response:
        days = int(request.query.get('days', 30))
        trends = await self.resource_tracker.get_trend_analysis(days)
        return web.json_response(trends)

    async def handle_forecast(self, request: web.Request) -> web.Response:
        days = int(request.query.get('days', 30))
        forecast = await self.resource_tracker.get_forecast(days)
        return web.json_response(forecast)

    async def handle_rebalance_suggestions(self, request: web.Request) -> web.Response:
        suggestions = await self.resource_alloc.get_rebalance_suggestions()
        return web.json_response(suggestions)

    async def handle_optimization_analyze(self, request: web.Request) -> web.Response:
        analysis = await self.resource_optim.analyze_optimization()
        return web.json_response(analysis)

    async def handle_schedule_event(self, request: web.Request) -> web.Response:
        data = await request.json()
        event = await self.resource_sched.add_event(data.get('event_type', ''), data.get('service', ''), data.get('scheduled_at', ''), data.get('duration_minutes', 60), data.get('description', ''))
        return web.json_response(event, status=201)

    async def handle_get_schedule(self, request: web.Request) -> web.Response:
        service = request.query.get('service')
        schedule = await self.resource_sched.get_schedule(service)
        return web.json_response(schedule)

    async def handle_log_search(self, request: web.Request) -> web.Response:
        data = await request.json()
        results = await self.unified_logger.search_logs(
            data.get('query', ''), data.get('level'), data.get('start_date'), data.get('end_date'), data.get('limit', 100)
        )
        return web.json_response(results)

    async def handle_log_levels(self, request: web.Request) -> web.Response:
        levels = await self.unified_logger.get_log_levels()
        return web.json_response(levels)

    async def handle_cross_platform_log(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.cross_logger.log_event(data.get('event_type', ''), data.get('platform', ''), data.get('data', {}), data.get('level', 'info'))
        return web.json_response({'success': True})

    async def handle_query_cross_platform_logs(self, request: web.Request) -> web.Response:
        logs = await self.cross_logger.query_logs(
            request.query.get('event_type'), request.query.get('platform'),
            request.query.get('level'), request.query.get('start_date'),
            request.query.get('end_date'), int(request.query.get('limit', 100))
        )
        return web.json_response(logs)

    async def handle_server_log_ingest(self, request: web.Request) -> web.Response:
        data = await request.json()
        success = await self.server_logs.ingest_log(data)
        return web.json_response({'success': success})

    async def handle_server_log_tail(self, request: web.Request) -> web.Response:
        lines = int(request.query.get('lines', 50))
        server = request.query.get('server')
        logs = await self.server_logs.tail_logs(lines, server)
        return web.json_response(logs)

    async def handle_backup_log_manager(self, request: web.Request) -> web.Response:
        logs = await self.backup_log_manager.logs[-100:]
        return web.json_response(logs)

    async def handle_backup_log_stats(self, request: web.Request) -> web.Response:
        stats = await self.backup_log_manager.get_stats()
        return web.json_response(stats)

    async def handle_integrated_monitoring(self, request: web.Request) -> web.Response:
        metrics = await self.service.metrics.collect_metrics()
        alerts = await self.alert_manager.get_alerts(status='unacknowledged')
        events = await self.event_broadcaster.get_events(limit=50)
        resources = await self.resource_tracker.get_all_resources()
        backup_stats = await self.backup_manager.get_backup_stats()
        return web.json_response({
            'metrics': metrics,
            'unacknowledged_alerts': len(alerts),
            'recent_events': len(events),
            'resources': resources.get('total', {}),
            'backup_stats': backup_stats,
            'timestamp': datetime.now().isoformat()
        })

    async def handle_alert_correlation(self, request: web.Request) -> web.Response:
        alerts = await self.alert_manager.get_alerts(limit=200)
        correlated = {}
        for alert in alerts:
            source = alert.get('source', 'unknown')
            if source not in correlated:
                correlated[source] = []
            correlated[source].append(alert)
        return web.json_response({'correlated_alerts': correlated, 'total': len(alerts)})

    async def handle_create_maintenance_window(self, request: web.Request) -> web.Response:
        data = await request.json()
        from resource_tracker import ResourceSchedulingCoordinator
        sched = ResourceSchedulingCoordinator(self.service.config)
        event = await sched.add_event('maintenance', data.get('service', ''), data.get('scheduled_at', ''), data.get('duration_minutes', 60), data.get('description', ''))
        return web.json_response(event, status=201)

    async def handle_security_events(self, request: web.Request) -> web.Response:
        events = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.service.config.get('service_core_url', 'http://localhost:8080')}/api/security/events") as resp:
                    if resp.status == 200:
                        events = await resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch security events: {e}")
        return web.json_response(events if isinstance(events, list) else [])

    async def handle_security_alert(self, request: web.Request) -> web.Response:
        data = await request.json()
        import aiohttp
        alert = await self.alert_manager.create_alert({
            'title': data.get('title', 'Security Alert'),
            'message': data.get('message', ''),
            'severity': data.get('severity', 'warning'),
            'source': 'security',
            'channels': ['discord', 'in_game']
        })
        return web.json_response(alert, status=201)

    async def handle_usage_report(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.reporting.initialize()
        report = await self.reporting.generate_usage_report(data.get('start_date', ''), data.get('end_date', ''))
        await self.reporting.close()
        return web.json_response(report)

    async def handle_billing_report(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.reporting.initialize()
        report = await self.reporting.generate_billing_report(data.get('user_id', ''), data.get('start_date', ''), data.get('end_date', ''))
        await self.reporting.close()
        return web.json_response(report)

    async def handle_security_report(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.reporting.initialize()
        report = await self.reporting.generate_security_report(data.get('start_date', ''), data.get('end_date', ''))
        await self.reporting.close()
        return web.json_response(report)

    async def handle_performance_report(self, request: web.Request) -> web.Response:
        data = await request.json()
        await self.reporting.initialize()
        report = await self.reporting.generate_performance_report(data.get('start_date', ''), data.get('end_date', ''))
        await self.reporting.close()
        return web.json_response(report)

    async def handle_list_reports(self, request: web.Request) -> web.Response:
        report_type = request.query.get('type')
        reports = await self.reporting.list_reports(report_type)
        return web.json_response(reports)

    async def handle_integrated_resource_management(self, request: web.Request) -> web.Response:
        resources = await self.resource_tracker.get_all_resources()
        avu = await self.resource_alloc.get_allocation_vs_usage()
        suggestions = await self.resource_alloc.get_rebalance_suggestions()
        pools = await self.pool_manager.get_pools()
        cost = await self.resource_tracker.get_cost_allocation(
            (datetime.now() - timedelta(days=30)).isoformat(), datetime.now().isoformat()
        )
        return web.json_response({
            'resources': resources,
            'allocation_vs_usage': avu,
            'suggestions': suggestions,
            'pools': pools,
            'cost_estimates': cost,
            'timestamp': datetime.now().isoformat()
        })

    async def start(self, host: str = '0.0.0.0', port: int = 9000):
        await self.service.start()
        await self.backup_manager.initialize()
        await self.resource_tracker.initialize()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Integration API running on http://{host}:{port}")

    async def stop(self):
        await self.backup_manager.close()
        await self.resource_tracker.close()
        await self.service.stop()


async def main():
    server = IntegrationAPIServer()
    await server.start()
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == '__main__':
    asyncio.run(main())
