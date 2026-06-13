from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Isolated workspaces with member management, resource quotas, cross-workspace sharing"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = config.get('workspaces_file', 'data/workspaces.json')
        self.activity_file = config.get('workspace_activity_file', 'data/workspace_activity.json')
        self.workspaces: List[Dict[str, Any]] = []
        self.activity_log: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.workspaces = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load workspaces: {e}")
        if os.path.exists(self.activity_file):
            try:
                with open(self.activity_file, 'r') as f:
                    self.activity_log = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load workspace activity: {e}")

    def _save_workspaces(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.workspaces, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workspaces: {e}")

    def _save_activity(self):
        try:
            with open(self.activity_file, 'w') as f:
                json.dump(self.activity_log[-5000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save activity log: {e}")

    def _log_activity(self, workspace_id: str, action: str, user_id: str, details: Dict[str, Any] = None):
        entry = {
            'id': f"act_{int(datetime.now().timestamp())}_{len(self.activity_log)}",
            'workspace_id': workspace_id,
            'action': action,
            'user_id': user_id,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.activity_log.append(entry)
        self._save_activity()

    async def initialize(self):
        logger.info("WorkspaceManager initialized")

    async def close(self):
        logger.info("WorkspaceManager closed")

    async def create_workspace(self, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
        workspace = {
            'id': f"ws_{len(self.workspaces)}_{int(datetime.now().timestamp())}",
            'name': workspace_data.get('name', ''),
            'description': workspace_data.get('description', ''),
            'owner': workspace_data.get('owner', ''),
            'members': [{'user_id': workspace_data.get('owner', ''), 'role': 'owner'}],
            'quotas': workspace_data.get('quotas', {
                'max_members': 10,
                'max_projects': 5,
                'max_cpu_cores': 4,
                'max_memory_mb': 8192,
                'max_storage_gb': 100
            }),
            'shared_resources': [],
            'pending_shares': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.workspaces.append(workspace)
        self._save_workspaces()
        self._log_activity(workspace['id'], 'created', workspace_data.get('owner', ''))
        return workspace

    async def list_workspaces(self) -> List[Dict[str, Any]]:
        return self.workspaces

    async def update_workspace(self, workspace_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                self.workspaces[i].update(updates)
                self.workspaces[i]['updated_at'] = datetime.now().isoformat()
                self._save_workspaces()
                return self.workspaces[i]
        return None

    async def delete_workspace(self, workspace_id: str) -> bool:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                self.workspaces.pop(i)
                self._save_workspaces()
                self._log_activity(workspace_id, 'deleted', 'system')
                return True
        return False

    async def add_member(self, workspace_id: str, member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                if len(w['members']) >= w.get('quotas', {}).get('max_members', 10):
                    return None
                member = {
                    'user_id': member_data.get('user_id', ''),
                    'role': member_data.get('role', 'member'),
                    'added_at': datetime.now().isoformat()
                }
                self.workspaces[i]['members'].append(member)
                self._save_workspaces()
                self._log_activity(workspace_id, 'member_added', member_data.get('user_id', ''))
                return member
        return None

    async def remove_member(self, workspace_id: str, user_id: str) -> bool:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                for j, m in enumerate(w['members']):
                    if m['user_id'] == user_id:
                        self.workspaces[i]['members'].pop(j)
                        self._save_workspaces()
                        self._log_activity(workspace_id, 'member_removed', user_id)
                        return True
        return False

    async def set_quotas(self, workspace_id: str, quotas: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                self.workspaces[i]['quotas'] = {**w.get('quotas', {}), **quotas}
                self.workspaces[i]['updated_at'] = datetime.now().isoformat()
                self._save_workspaces()
                self._log_activity(workspace_id, 'quotas_updated', 'system', quotas)
                return self.workspaces[i]['quotas']
        return None

    async def share_resource(self, workspace_id: str, share_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, w in enumerate(self.workspaces):
            if w['id'] == workspace_id:
                share = {
                    'id': f"share_{int(datetime.now().timestamp())}",
                    'resource_type': share_data.get('resource_type', ''),
                    'resource_id': share_data.get('resource_id', ''),
                    'target_workspace_id': share_data.get('target_workspace_id', ''),
                    'permissions': share_data.get('permissions', 'read'),
                    'status': 'pending',
                    'requested_by': share_data.get('requested_by', ''),
                    'created_at': datetime.now().isoformat()
                }
                self.workspaces[i]['pending_shares'].append(share)
                self._save_workspaces()
                self._log_activity(workspace_id, 'resource_shared', share_data.get('requested_by', ''), share)
                return share
        return None

    async def get_activity(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return [a for a in self.activity_log if a.get('workspace_id') == workspace_id][-limit:]
