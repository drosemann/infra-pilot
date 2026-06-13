import json
import os
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIAssistant:
    """Natural language processing for server commands with intent classification and entity extraction."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_file = config.get('assistant_conversations_file', 'data/assistant_conversations.json')
        self.conversations: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.data_file) as f:
                self.conversations = json.load(f)
        except:
            self.conversations = []

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.conversations[-500:], f, indent=2)

    def _classify_intent(self, query: str) -> str:
        q = query.lower().strip()
        if any(w in q for w in ['start', 'launch', 'boot', 'turn on']):
            return 'start_server'
        if any(w in q for w in ['stop', 'shutdown', 'turn off', 'kill']):
            return 'stop_server'
        if any(w in q for w in ['restart', 'reboot', 'reload']):
            return 'restart_server'
        if any(w in q for w in ['create', 'new', 'deploy', 'provision', 'setup']):
            return 'create_server'
        if any(w in q for w in ['delete', 'remove', 'destroy', 'terminate']):
            return 'delete_server'
        if any(w in q for w in ['backup', 'snapshot', 'save']):
            return 'backup'
        if any(w in q for w in ['restore', 'recover']):
            return 'restore'
        if any(w in q for w in ['status', 'info', 'check', 'list', 'show']):
            return 'get_status'
        if any(w in q for w in ['update', 'upgrade', 'install', 'mod', 'plugin']):
            return 'update_server'
        if any(w in q for w in ['help', 'what can', 'commands', 'capabilities']):
            return 'help'
        return 'general_query'

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        entities = {}
        server_patterns = [
            r'(?:server\s+)([\w\-_]+)',
            r'(?:on\s+)([\w\-_]+)',
            r'(?:for\s+)([\w\-_]+)',
        ]
        for pat in server_patterns:
            m = re.search(pat, query, re.IGNORECASE)
            if m:
                entities['server'] = m.group(1)
                break

        version_match = re.search(r'(?:version\s+)?(\d+\.\d+(?:\.\d+)?)', query)
        if version_match:
            entities['version'] = version_match.group(1)

        platform_match = re.search(r'(?:on|for|using)\s+(discord|minecraft|dashboard)', query, re.IGNORECASE)
        if platform_match:
            entities['platform'] = platform_match.group(1).lower()

        mod_match = re.search(r'(?:mod|plugin|pack)\s+["\']?([\w\-_ ]+)["\']?', query, re.IGNORECASE)
        if mod_match:
            entities['mod'] = mod_match.group(1).strip()

        return entities

    def _generate_response(self, intent: str, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        responses = {
            'start_server': f"I'll start server '{entities.get('server', 'the specified server')}'.",
            'stop_server': f"I'll stop server '{entities.get('server', 'the specified server')}'.",
            'restart_server': f"I'll restart server '{entities.get('server', 'the specified server')}'.",
            'create_server': "I'll create a new server. Please confirm the configuration details.",
            'delete_server': f"I'll delete server '{entities.get('server', 'the specified server')}'. This action cannot be undone.",
            'backup': f"I'll create a backup of '{entities.get('server', 'all servers')}'.",
            'restore': f"I'll restore from backup for '{entities.get('server', 'the specified server')}'.",
            'get_status': f"Here's the current status of '{entities.get('server', 'all servers')}'.",
            'update_server': f"I'll update server '{entities.get('server', 'the specified server')}'.",
            'help': "I can help manage servers: start, stop, restart, create, delete, backup, restore, update, and check status.",
            'general_query': f"I understand you're asking about: '{query}'. I can help with server management commands.",
        }
        return {
            'intent': intent,
            'entities': entities,
            'message': responses.get(intent, responses['general_query']),
            'requires_confirmation': intent in ('delete_server', 'restart_server', 'create_server', 'restore'),
        }

    async def process_query(self, query: str) -> Dict[str, Any]:
        intent = self._classify_intent(query)
        entities = self._extract_entities(query)
        response = self._generate_response(intent, entities, query)

        conversation = {
            'id': f'conv_{len(self.conversations)}_{int(datetime.now().timestamp())}',
            'query': query,
            'intent': intent,
            'entities': entities,
            'response': response['message'],
            'requires_confirmation': response['requires_confirmation'],
            'confirmed': False,
            'executed': False,
            'timestamp': datetime.now().isoformat()
        }
        self.conversations.append(conversation)
        self._save()
        return response | {'conversation_id': conversation['id']}

    async def execute_action(self, conversation_id: str) -> Dict[str, Any]:
        for conv in self.conversations:
            if conv['id'] == conversation_id:
                if conv['executed']:
                    raise ValueError(f'Action {conversation_id} already executed')
                conv['confirmed'] = True
                conv['executed'] = True
                conv['executed_at'] = datetime.now().isoformat()
                self._save()
                return {
                    'success': True,
                    'conversation_id': conversation_id,
                    'intent': conv['intent'],
                    'entities': conv['entities'],
                    'action': conv['intent'],
                    'executed_at': conv['executed_at']
                }
        raise ValueError(f'Conversation {conversation_id} not found')

    async def close(self):
        self._save()
