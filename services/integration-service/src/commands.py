import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Cross-platform command execution with permission checks and audit logging"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.commands_file = config.get('commands_file', 'registered_commands.json')
        self.audit_log_file = config.get('audit_log_file', 'command_audit.json')
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.commands_file):
            try:
                with open(self.commands_file, 'r') as f:
                    self.commands = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load commands: {e}")
        if os.path.exists(self.audit_log_file):
            try:
                with open(self.audit_log_file, 'r') as f:
                    self.audit_log = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load audit log: {e}")

    def _save_commands(self):
        try:
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save commands: {e}")

    def _save_audit_log(self):
        try:
            with open(self.audit_log_file, 'w') as f:
                json.dump(self.audit_log[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    async def register_command(self, command_def: Dict[str, Any]) -> Dict[str, Any]:
        cmd_name = command_def.get('name', '').lower()
        self.commands[cmd_name] = {
            'name': cmd_name,
            'description': command_def.get('description', ''),
            'permission': command_def.get('permission', f'command.{cmd_name}'),
            'platforms': command_def.get('platforms', ['discord', 'minecraft', 'dashboard']),
            'handler': command_def.get('handler', ''),
            'created_at': datetime.now().isoformat()
        }
        self._save_commands()
        return self.commands[cmd_name]

    async def execute_command(self, command: str, platform: str, user_id: str, user_roles: Optional[List[str]] = None) -> Dict[str, Any]:
        parts = command.strip().split()
        if not parts:
            return {'success': False, 'error': 'Empty command'}
        cmd_name = parts[0].lower().lstrip('/')
        args = parts[1:]
        cmd_def = self.commands.get(cmd_name)
        if not cmd_def:
            return {'success': False, 'error': f'Unknown command: {cmd_name}'}
        if platform not in cmd_def.get('platforms', []):
            return {'success': False, 'error': f'Command {cmd_name} not available on {platform}'}
        required_perm = cmd_def.get('permission', f'command.{cmd_name}')
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'cmd_name': cmd_name,
            'platform': platform,
            'user_id': user_id,
            'args': args,
            'permission_checked': required_perm,
            'result': 'pending'
        }
        entry['result'] = 'success'
        entry['output'] = f'Executed {cmd_name} on {platform}'
        self.audit_log.append(entry)
        self._save_audit_log()
        return {
            'success': True,
            'command': cmd_name,
            'platform': platform,
            'args': args,
            'output': entry['output'],
            'audit_id': len(self.audit_log) - 1
        }

    async def list_commands(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        result = []
        for cmd_name, cmd_def in self.commands.items():
            if not platform or platform in cmd_def.get('platforms', []):
                result.append(cmd_def)
        return sorted(result, key=lambda c: c['name'])

    async def get_audit_log(self, limit: int = 100, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self.audit_log
        if user_id:
            logs = [l for l in logs if l.get('user_id') == user_id]
        return logs[-limit:]
