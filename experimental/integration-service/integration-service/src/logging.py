import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UnifiedLogger:
    """Cross-Service Operations - Unified logging system with aggregation, filtering, search, retention"""

    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.config = config or {}
        self.log_file = self.config.get('log_file', f'{service_name}_logs.json')
        self.retention_days = self.config.get('retention_days', 30)
        self.max_logs = self.config.get('max_logs', 10000)
        self.log_store: List[Dict[str, Any]] = []
        self.handlers = []
        self._setup_logger()
        self._load_logs()

    def _setup_logger(self):
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.log_store = json.load(f)
            except Exception as e:
                logger = logging.getLogger(self.service_name)
                logger.warning(f"Failed to load logs: {e}")

    def _save_logs(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.log_store[-self.max_logs:], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save logs: {e}")

    def _enforce_retention(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        self.log_store = [l for l in self.log_store if datetime.fromisoformat(l['timestamp']) >= cutoff]
        self.log_store = self.log_store[-self.max_logs:]

    def _format_message(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now().isoformat(),
            'service': self.service_name,
            'level': level,
            'message': message,
            'extra': extra or {}
        }

    def _emit_log(self, level: str, message: str, extra: Dict[str, Any]):
        formatted = self._format_message(level, message, extra)
        self.log_store.append(formatted)
        self._enforce_retention()
        self._save_logs()
        print(json.dumps(formatted), flush=True)

    def debug(self, message: str, **extra):
        self.logger.debug(message, extra=extra)
        self._emit_log('DEBUG', message, extra)

    def info(self, message: str, **extra):
        self.logger.info(message, extra=extra)
        self._emit_log('INFO', message, extra)

    def warning(self, message: str, **extra):
        self.logger.warning(message, extra=extra)
        self._emit_log('WARNING', message, extra)

    def error(self, message: str, **extra):
        self.logger.error(message, extra=extra)
        self._emit_log('ERROR', message, extra)

    def critical(self, message: str, **extra):
        self.logger.critical(message, extra=extra)
        self._emit_log('CRITICAL', message, extra)

    async def search_logs(self, query: str = '', level: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, page: int = 1, limit: int = 100, use_regex: bool = False) -> Dict[str, Any]:
        import re
        results = self.log_store
        if level:
            results = [l for l in results if l.get('level') == level.upper()]
        if start_date:
            results = [l for l in results if l.get('timestamp', '') >= start_date]
        if end_date:
            results = [l for l in results if l.get('timestamp', '') <= end_date]
        if query:
            if use_regex:
                try:
                    pattern = re.compile(query, re.IGNORECASE)
                    results = [l for l in results if pattern.search(l.get('message', '')) or pattern.search(str(l.get('extra', {})))]
                except re.error:
                    pass
            else:
                q = query.lower()
                results = [l for l in results if q in l.get('message', '').lower() or q in str(l.get('extra', {})).lower()]
        total = len(results)
        offset = (page - 1) * limit
        paged = results[offset:offset + limit]
        return {'logs': paged, 'total': total, 'page': page, 'limit': limit}

    async def get_log_levels(self) -> Dict[str, int]:
        counts = {}
        for log_entry in self.log_store:
            level = log_entry.get('level', 'UNKNOWN')
            counts[level] = counts.get(level, 0) + 1
        return counts


class AuditLogger:
    """Audit logging for compliance"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}_audit")
        self.audit_file = f'{service_name}_audit.json'
        self.audit_store: List[Dict[str, Any]] = []
        self._load_audit()

    def _load_audit(self):
        if os.path.exists(self.audit_file):
            try:
                with open(self.audit_file, 'r') as f:
                    self.audit_store = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load audit log: {e}")

    def _save_audit(self):
        try:
            with open(self.audit_file, 'w') as f:
                json.dump(self.audit_store[-5000:], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save audit log: {e}")

    def log_operation(self, user_id: str, operation: str, resource: str, result: str, details: Optional[Dict[str, Any]] = None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'service': self.service_name,
            'user_id': user_id,
            'operation': operation,
            'resource': resource,
            'result': result,
            'details': details or {}
        }
        self.audit_store.append(entry)
        self._save_audit()
        self.logger.info(json.dumps(entry))

    def log_access(self, user_id: str, resource: str, granted: bool):
        self.log_operation(user_id, 'ACCESS', resource, 'GRANTED' if granted else 'DENIED')

    def log_modification(self, user_id: str, resource: str, changes: Dict[str, Any]):
        self.log_operation(user_id, 'MODIFY', resource, 'SUCCESS', {'changes': changes})


class CrossPlatformLogger:
    """Cross-platform logging - Log all cross-platform events, query API with filters"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cross_log_file = config.get('cross_platform_log_file', 'cross_platform_logs.json')
        self.logs: List[Dict[str, Any]] = []
        self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.cross_log_file):
            try:
                with open(self.cross_log_file, 'r') as f:
                    self.logs = json.load(f)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load cross-platform logs: {e}")

    def _save_logs(self):
        try:
            with open(self.cross_log_file, 'w') as f:
                json.dump(self.logs[-5000:], f, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save cross-platform logs: {e}")

    async def log_event(self, event_type: str, platform: str, data: Dict[str, Any], level: str = 'info'):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'platform': platform,
            'level': level,
            'data': data
        }
        self.logs.append(entry)
        self._save_logs()

    async def query_logs(self, event_type: Optional[str] = None, platform: Optional[str] = None, level: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.logs
        if event_type:
            results = [l for l in results if l.get('event_type') == event_type]
        if platform:
            results = [l for l in results if l.get('platform') == platform]
        if level:
            results = [l for l in results if l.get('level') == level]
        if start_date:
            results = [l for l in results if l.get('timestamp', '') >= start_date]
        if end_date:
            results = [l for l in results if l.get('timestamp', '') <= end_date]
        return results[-limit:]


class ServerLogsIntegrator:
    """Server logs integration - Minecraft server logs to Discord channel, level filtering, tail/search"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.discord_webhook = config.get('discord_webhook')
        self.server_log_file = config.get('server_log_file', 'server_logs.json')
        self.logs: List[Dict[str, Any]] = []
        self.level_filters: Dict[str, bool] = {'debug': False, 'info': True, 'warn': True, 'error': True, 'fatal': True}
        self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.server_log_file):
            try:
                with open(self.server_log_file, 'r') as f:
                    self.logs = json.load(f)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to load server logs: {e}")

    def _save_logs(self):
        try:
            with open(self.server_log_file, 'w') as f:
                json.dump(self.logs[-10000:], f, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save server logs: {e}")

    async def ingest_log(self, log_entry: Dict[str, Any]) -> bool:
        level = log_entry.get('level', 'info').lower()
        if not self.level_filters.get(level, True):
            return False
        entry = {
            'timestamp': datetime.now().isoformat(),
            'server': log_entry.get('server', 'unknown'),
            'level': level,
            'message': log_entry.get('message', ''),
            'logger': log_entry.get('logger', '')
        }
        self.logs.append(entry)
        self._save_logs()
        if self.discord_webhook and level in ('error', 'fatal', 'warn'):
            import aiohttp
            colors = {'error': 0xFF0000, 'fatal': 0x8B0000, 'warn': 0xFFAA00}
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(self.discord_webhook, json={
                        'embeds': [{
                            'title': f"[{level.upper()}] {entry['server']}",
                            'description': entry['message'][:2000],
                            'color': colors.get(level, 0x007BFF),
                            'timestamp': entry['timestamp']
                        }]
                    })
            except Exception as e:
                logging.getLogger(__name__).warning(f"Discord log relay failed: {e}")
        return True

    async def set_level_filter(self, level: str, enabled: bool):
        self.level_filters[level.lower()] = enabled

    async def tail_logs(self, lines: int = 50, server: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.logs
        if server:
            results = [l for l in results if l.get('server') == server]
        return results[-lines:]

    async def search_logs(self, query: str, level: Optional[str] = None, server: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.logs
        if level:
            results = [l for l in results if l.get('level') == level]
        if server:
            results = [l for l in results if l.get('server') == server]
        if query:
            q = query.lower()
            results = [l for l in results if q in l.get('message', '').lower()]
        return results[-limit:]


class BackupLogManager:
    """Centralized backup status - success/failure rate, backup logs query"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backup_log_file = config.get('backup_log_file', 'backup_status_logs.json')
        self.logs: List[Dict[str, Any]] = []
        self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.backup_log_file):
            try:
                with open(self.backup_log_file, 'r') as f:
                    self.logs = json.load(f)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to load backup logs: {e}")

    def _save_logs(self):
        try:
            with open(self.backup_log_file, 'w') as f:
                json.dump(self.logs[-2000:], f, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save backup logs: {e}")

    async def log_backup(self, backup_id: str, service: str, status: str, size_bytes: int = 0, error: Optional[str] = None):
        entry = {
            'backup_id': backup_id,
            'service': service,
            'status': status,
            'size_bytes': size_bytes,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.logs.append(entry)
        self._save_logs()

    async def get_stats(self) -> Dict[str, Any]:
        total = len(self.logs)
        if total == 0:
            return {'total': 0, 'success_rate': 0, 'by_service': {}}
        successful = len([l for l in self.logs if l.get('status') in ('completed', 'success')])
        failed = len([l for l in self.logs if l.get('status') == 'failed'])
        by_service = {}
        for entry in self.logs:
            svc = entry.get('service', 'unknown')
            if svc not in by_service:
                by_service[svc] = {'total': 0, 'successful': 0, 'failed': 0}
            by_service[svc]['total'] += 1
            if entry.get('status') in ('completed', 'success'):
                by_service[svc]['successful'] += 1
            elif entry.get('status') == 'failed':
                by_service[svc]['failed'] += 1
        for svc in by_service:
            t = by_service[svc]['total']
            by_service[svc]['success_rate'] = round(by_service[svc]['successful'] / t * 100, 2) if t > 0 else 0
        return {'total': total, 'successful': successful, 'failed': failed, 'success_rate': round(successful / total * 100, 2) if total > 0 else 0, 'by_service': by_service}


def get_unified_logger(service_name: str) -> UnifiedLogger:
    return UnifiedLogger(service_name)


def get_audit_logger(service_name: str) -> AuditLogger:
    return AuditLogger(service_name)


if __name__ == '__main__':
    logger = get_unified_logger('test-service')
    logger.info('Test message', test_value='hello')
    logger.warning('Warning message', warning_code=123)
    logger.error('Error occurred', error_details={'code': 500})
