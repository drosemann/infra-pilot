import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import os
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupManager:
    """Integrated Backup System - Single backup controls for all services"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8000')
        self.storage_path = config.get('backup_path', './backups')
        self.log_file = config.get('backup_log_file', 'backup_logs.json')
        self.backup_logs: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        os.makedirs(self.storage_path, exist_ok=True)
        self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.backup_logs = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load backup logs: {e}")

    def _save_logs(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.backup_logs[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup logs: {e}")

    def _log_backup(self, entry: Dict[str, Any]):
        self.backup_logs.append(entry)
        self._save_logs()

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("BackupManager initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def create_backup(self, service: str, server_id: Optional[str] = None) -> Dict[str, Any]:
        backup_id = f"{service}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = {}
        if service == 'service_core':
            result = await self._backup_service_core(server_id, backup_id)
        elif service == 'orchestrator':
            result = await self._backup_orchestrator(server_id, backup_id)
        elif service == 'all':
            result = await self._backup_all(backup_id)
        else:
            result = {'error': f'Unknown service: {service}'}
        self._log_backup({'backup_id': backup_id, 'service': service, 'result': result.get('status', 'completed'), 'timestamp': datetime.now().isoformat()})
        return result

    async def _backup_service_core(self, server_id: Optional[str], backup_id: str) -> Dict[str, Any]:
        try:
            async with self.session.get(f"{self.service_core_url}/api/backups") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    backup_file = os.path.join(self.storage_path, f"{backup_id}_service_core.json")
                    with open(backup_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    checksum = str(hash(json.dumps(data, sort_keys=True)))
                    return {'backup_id': backup_id, 'service': 'service_core', 'file': backup_file, 'checksum': checksum, 'status': 'completed'}
        except Exception as e:
            logger.error(f"Service Core backup failed: {e}")
        return {'backup_id': backup_id, 'service': 'service_core', 'status': 'failed'}

    async def _backup_orchestrator(self, server_id: Optional[str], backup_id: str) -> Dict[str, Any]:
        try:
            async with self.session.get(f"{self.orchestrator_url}/api/backups") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    backup_file = os.path.join(self.storage_path, f"{backup_id}_orchestrator.json")
                    with open(backup_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    checksum = str(hash(json.dumps(data, sort_keys=True)))
                    return {'backup_id': backup_id, 'service': 'orchestrator', 'file': backup_file, 'checksum': checksum, 'status': 'completed'}
        except Exception as e:
            logger.error(f"Orchestrator backup failed: {e}")
        return {'backup_id': backup_id, 'service': 'orchestrator', 'status': 'failed'}

    async def _backup_all(self, backup_id: str) -> Dict[str, Any]:
        results = await asyncio.gather(
            self._backup_service_core(None, backup_id),
            self._backup_orchestrator(None, backup_id),
            return_exceptions=True
        )
        services = {}
        for r in results:
            if isinstance(r, dict) and r.get('service'):
                services[r['service']] = r
        return {'backup_id': backup_id, 'services': services, 'status': 'completed'}

    async def restore_backup(self, backup_id: str, service: str) -> bool:
        backup_file = os.path.join(self.storage_path, f"{backup_id}_{service}.json")
        if not os.path.exists(backup_file):
            return False
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            endpoint = f"{self.service_core_url}/api/restore" if service == 'service_core' else f"{self.orchestrator_url}/api/restore"
            async with self.session.post(endpoint, json=data) as resp:
                success = resp.status == 200
                self._log_backup({'backup_id': backup_id, 'service': service, 'action': 'restore', 'result': 'success' if success else 'failed', 'timestamp': datetime.now().isoformat()})
                return success
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            self._log_backup({'backup_id': backup_id, 'service': service, 'action': 'restore', 'result': 'failed', 'error': str(e), 'timestamp': datetime.now().isoformat()})
            return False

    async def verify_backup(self, backup_id: str, service: str) -> Dict[str, Any]:
        backup_file = os.path.join(self.storage_path, f"{backup_id}_{service}.json")
        if not os.path.exists(backup_file):
            return {'verified': False, 'reason': 'Backup file not found'}
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            if not isinstance(data, dict) and not isinstance(data, list):
                return {'verified': False, 'reason': 'Invalid backup format'}
            file_size = os.path.getsize(backup_file)
            checksum = str(hash(json.dumps(data, sort_keys=True)))
            return {'verified': True, 'file_size': file_size, 'checksum': checksum, 'entries': len(data) if isinstance(data, (dict, list)) else 0}
        except Exception as e:
            return {'verified': False, 'reason': str(e)}

    async def cross_service_backup(self, services: List[str]) -> Dict[str, Any]:
        backup_id = f"cross_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tasks = []
        for srv in services:
            if srv == 'service_core':
                tasks.append(self._backup_service_core(None, backup_id))
            elif srv == 'orchestrator':
                tasks.append(self._backup_orchestrator(None, backup_id))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        services_result = {}
        for r in results:
            if isinstance(r, dict) and r.get('service'):
                services_result[r['service']] = r
        return {'backup_id': backup_id, 'services': services_result, 'type': 'cross_service', 'status': 'completed'}

    async def atomic_multi_service_restore(self, backup_id: str) -> Dict[str, Any]:
        services = ['service_core', 'orchestrator']
        results = {}
        for srv in services:
            results[srv] = await self.restore_backup(backup_id, srv)
        all_success = all(results.values())
        return {'backup_id': backup_id, 'results': results, 'all_success': all_success}

    def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                parts = filename.replace('.json', '').split('_')
                if len(parts) >= 2:
                    backups.append({
                        'filename': filename,
                        'backup_id': parts[0],
                        'service': parts[1] if len(parts) > 1 else 'unknown',
                        'file_size': os.path.getsize(os.path.join(self.storage_path, filename)),
                        'created': datetime.fromtimestamp(os.path.getctime(os.path.join(self.storage_path, filename))).isoformat()
                    })
        return sorted(backups, key=lambda b: b['created'], reverse=True)

    async def cleanup_old_backups(self, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        for backup in self.list_backups():
            created = datetime.fromisoformat(backup['created'])
            if created < cutoff:
                try:
                    os.remove(os.path.join(self.storage_path, backup['filename']))
                    removed += 1
                except Exception as e:
                    logger.error(f"Failed to remove {backup['filename']}: {e}")
        return removed

    async def get_backup_logs(self, limit: int = 100, service: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self.backup_logs
        if service:
            logs = [l for l in logs if l.get('service') == service]
        return logs[-limit:]

    async def get_backup_stats(self) -> Dict[str, Any]:
        logs = self.backup_logs
        total = len(logs)
        successful = len([l for l in logs if l.get('result') in ('completed', 'success')])
        failed = len([l for l in logs if l.get('result') == 'failed'])
        return {
            'total_backups': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful / total * 100, 2) if total > 0 else 0,
            'by_service': {}
        }


class UnifiedReporting:
    """Unified Reporting System - Cross-service usage/billing/security/performance reports"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_core_url = config.get('service_core_url', 'http://localhost:8080')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8000')
        self.dashboard_url = config.get('dashboard_url', 'http://localhost:5173')
        self.reports_file = config.get('reports_file', 'unified_reports.json')
        self.generated_reports: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self._load_reports()

    def _load_reports(self):
        if os.path.exists(self.reports_file):
            try:
                with open(self.reports_file, 'r') as f:
                    self.generated_reports = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load reports: {e}")

    def _save_reports(self):
        try:
            with open(self.reports_file, 'w') as f:
                json.dump(self.generated_reports[-100:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reports: {e}")

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("UnifiedReporting initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    async def generate_usage_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        report = {'period': {'start': start_date, 'end': end_date}, 'generated_at': datetime.now().isoformat(), 'services': {}}
        endpoints = {
            'service_core': f"{self.service_core_url}/api/usage",
            'orchestrator': f"{self.orchestrator_url}/api/usage",
            'dashboard': f"{self.dashboard_url}/api/usage"
        }
        for service, endpoint in endpoints.items():
            try:
                async with self.session.get(endpoint, params={'start': start_date, 'end': end_date}) as resp:
                    if resp.status == 200:
                        report['services'][service] = await resp.json()
            except Exception as e:
                logger.warning(f"Failed to get {service} usage: {e}")
        report['summary'] = self._calculate_summary(report['services'])
        report['type'] = 'usage'
        self.generated_reports.append({'type': 'usage', 'period': report['period'], 'generated_at': report['generated_at']})
        self._save_reports()
        return report

    def _calculate_summary(self, services: Dict[str, Any]) -> Dict[str, Any]:
        total_servers = 0
        total_cpu_hours = 0
        total_memory_hours = 0
        for service_data in services.values():
            if isinstance(service_data, dict):
                total_servers += service_data.get('server_count', 0)
                total_cpu_hours += service_data.get('cpu_hours', 0)
                total_memory_hours += service_data.get('memory_hours', 0)
        return {'total_servers': total_servers, 'total_cpu_hours': total_cpu_hours, 'total_memory_hours': total_memory_hours}

    async def generate_billing_report(self, user_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        report = {'user_id': user_id, 'period': {'start': start_date, 'end': end_date}, 'generated_at': datetime.now().isoformat(), 'line_items': []}
        endpoints = {
            'service_core': f"{self.service_core_url}/api/billing/{user_id}",
            'orchestrator': f"{self.orchestrator_url}/api/billing/{user_id}"
        }
        for service, endpoint in endpoints.items():
            try:
                async with self.session.get(endpoint, params={'start': start_date, 'end': end_date}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        report['line_items'].extend(data.get('items', []))
            except Exception as e:
                logger.warning(f"Failed to get {service} billing: {e}")
        report['total'] = sum(item.get('amount', 0) for item in report['line_items'])
        report['type'] = 'billing'
        self.generated_reports.append({'type': 'billing', 'user_id': user_id, 'period': report['period'], 'generated_at': report['generated_at']})
        self._save_reports()
        return report

    async def generate_security_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        report = {'period': {'start': start_date, 'end': end_date}, 'generated_at': datetime.now().isoformat(), 'events': []}
        endpoints = {
            'service_core': f"{self.service_core_url}/api/security/events",
            'orchestrator': f"{self.orchestrator_url}/api/security/events"
        }
        for service, endpoint in endpoints.items():
            try:
                async with self.session.get(endpoint, params={'start': start_date, 'end': end_date}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            report['events'].extend(data)
            except Exception as e:
                logger.warning(f"Failed to get {service} security events: {e}")
        report['total_events'] = len(report['events'])
        report['type'] = 'security'
        self.generated_reports.append({'type': 'security', 'period': report['period'], 'generated_at': report['generated_at']})
        self._save_reports()
        return report

    async def generate_performance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        report = {'period': {'start': start_date, 'end': end_date}, 'generated_at': datetime.now().isoformat(), 'services': {}}
        endpoints = {
            'service_core': f"{self.service_core_url}/api/performance",
            'orchestrator': f"{self.orchestrator_url}/api/performance"
        }
        for service, endpoint in endpoints.items():
            try:
                async with self.session.get(endpoint, params={'start': start_date, 'end': end_date}) as resp:
                    if resp.status == 200:
                        report['services'][service] = await resp.json()
            except Exception as e:
                logger.warning(f"Failed to get {service} performance: {e}")
        report['type'] = 'performance'
        self.generated_reports.append({'type': 'performance', 'period': report['period'], 'generated_at': report['generated_at']})
        self._save_reports()
        return report

    async def list_reports(self, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        reports = self.generated_reports
        if report_type:
            reports = [r for r in reports if r.get('type') == report_type]
        return reports[-50:]


async def main():
    config = {}
    backup_manager = BackupManager(config)
    await backup_manager.initialize()
    os.makedirs('./backups', exist_ok=True)
    print("Creating full system backup...")
    result = await backup_manager.create_backup('all')
    print(f"Backup result: {result}")
    await backup_manager.close()


if __name__ == '__main__':
    asyncio.run(main())
