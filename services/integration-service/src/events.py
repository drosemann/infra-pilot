from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Cross-platform event broadcasting - player events, server events across all platforms"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.listeners_file = config.get('listeners_file', 'event_listeners.json')
        self.events_log_file = config.get('events_log_file', 'events_log.json')
        self.listeners: Dict[str, List[Dict[str, Any]]] = {}
        self.events_log: List[Dict[str, Any]] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.listeners_file):
            try:
                with open(self.listeners_file, 'r') as f:
                    self.listeners = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load listeners: {e}")
        if os.path.exists(self.events_log_file):
            try:
                with open(self.events_log_file, 'r') as f:
                    self.events_log = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load events log: {e}")

    def _save_listeners(self):
        try:
            with open(self.listeners_file, 'w') as f:
                json.dump(self.listeners, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save listeners: {e}")

    def _save_events_log(self):
        try:
            with open(self.events_log_file, 'w') as f:
                json.dump(self.events_log[-1000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save events log: {e}")

    async def register_listener(self, event_type: str, platform: str, webhook_url: str) -> bool:
        self.listeners.setdefault(event_type, []).append({
            'platform': platform,
            'webhook_url': webhook_url,
            'created_at': datetime.now().isoformat()
        })
        self._save_listeners()
        return True

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.events_log.append(entry)
        self._save_events_log()
        results = {}
        for listener in self.listeners.get(event_type, []):
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        listener['webhook_url'],
                        json={'event_type': event_type, 'data': data, 'timestamp': entry['timestamp']}
                    ) as resp:
                        results[listener['platform']] = resp.status
            except Exception as e:
                logger.warning(f"Event delivery to {listener.get('platform')} failed: {e}")
                results[listener['platform']] = str(e)
        for cb in self.callbacks.get(event_type, []):
            try:
                cb(event_type, data)
            except Exception as e:
                logger.error(f"Event callback failed: {e}")
        return {'event_type': event_type, 'delivered': results, 'timestamp': entry['timestamp']}

    async def player_join(self, player_name: str, uuid: str, server: str) -> Dict[str, Any]:
        return await self.broadcast_event('player.join', {
            'player_name': player_name,
            'uuid': uuid,
            'server': server
        })

    async def player_leave(self, player_name: str, uuid: str, server: str) -> Dict[str, Any]:
        return await self.broadcast_event('player.leave', {
            'player_name': player_name,
            'uuid': uuid,
            'server': server
        })

    async def achievement_unlocked(self, player_name: str, uuid: str, achievement: str, server: str) -> Dict[str, Any]:
        return await self.broadcast_event('player.achievement', {
            'player_name': player_name,
            'uuid': uuid,
            'achievement': achievement,
            'server': server
        })

    async def vote_received(self, player_name: str, uuid: str, vote_count: int, server: str) -> Dict[str, Any]:
        return await self.broadcast_event('player.vote', {
            'player_name': player_name,
            'uuid': uuid,
            'vote_count': vote_count,
            'server': server
        })

    async def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        events = self.events_log
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        return events[-limit:]

    def on(self, event_type: str, callback: Callable):
        self.callbacks.setdefault(event_type, []).append(callback)
