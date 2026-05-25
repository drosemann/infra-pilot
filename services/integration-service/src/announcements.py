from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import asyncio
import logging

logger = logging.getLogger(__name__)


class AnnouncementScheduler:
    """Server announcement scheduler with templates, recurrence, and cross-platform delivery"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.announcements_file = config.get('announcements_file', 'announcements.json')
        self.templates_file = config.get('templates_file', 'announcement_templates.json')
        self.announcements: List[Dict[str, Any]] = []
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.announcements_file):
            try:
                with open(self.announcements_file, 'r') as f:
                    self.announcements = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load announcements: {e}")
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r') as f:
                    self.templates = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load templates: {e}")

    def _save_announcements(self):
        try:
            with open(self.announcements_file, 'w') as f:
                json.dump(self.announcements, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save announcements: {e}")

    def _save_templates(self):
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("AnnouncementScheduler started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_scheduler(self):
        while self._running:
            now = datetime.now()
            for ann in self.announcements:
                if ann.get('status') == 'scheduled':
                    scheduled = datetime.fromisoformat(ann['scheduled_at'])
                    if scheduled <= now:
                        await self._send_announcement(ann)
                        ann['status'] = 'sent'
                        ann['sent_at'] = now.isoformat()
                        if ann.get('recurrence'):
                            next_time = self._next_recurrence(scheduled, ann['recurrence'])
                            if next_time:
                                new_ann = dict(ann)
                                new_ann['scheduled_at'] = next_time.isoformat()
                                new_ann['status'] = 'scheduled'
                                new_ann['sent_at'] = None
                                self.announcements.append(new_ann)
                        self._save_announcements()
            await asyncio.sleep(30)

    def _next_recurrence(self, from_time: datetime, recurrence: str) -> Optional[datetime]:
        if recurrence == 'hourly':
            return from_time + timedelta(hours=1)
        elif recurrence == 'daily':
            return from_time + timedelta(days=1)
        elif recurrence == 'weekly':
            return from_time + timedelta(weeks=1)
        elif recurrence == 'monthly':
            month = from_time.month + 1
            year = from_time.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            try:
                return from_time.replace(year=year, month=month)
            except ValueError:
                return from_time + timedelta(days=30)
        return None

    async def _send_announcement(self, ann: Dict[str, Any]):
        content = ann.get('content', '')
        platforms = ann.get('platforms', ['discord', 'minecraft'])
        import aiohttp
        async with aiohttp.ClientSession() as session:
            for platform in platforms:
                try:
                    if platform == 'discord' and self.config.get('discord_webhook'):
                        await session.post(self.config['discord_webhook'], json={
                            'embeds': [{
                                'title': '📢 Announcement',
                                'description': content,
                                'color': 0x6C5CE7,
                                'timestamp': datetime.now().isoformat()
                            }]
                        })
                    elif platform == 'minecraft' and self.config.get('minecraft_webhook'):
                        await session.post(self.config['minecraft_webhook'], json={
                            'message': f'[ANNOUNCEMENT] {content}',
                            'platform': 'announcement'
                        })
                except Exception as e:
                    logger.warning(f"Announcement delivery to {platform} failed: {e}")

    async def schedule_announcement(self, announcement_data: Dict[str, Any]) -> Dict[str, Any]:
        template_name = announcement_data.get('template')
        content = announcement_data.get('content', '')
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
            content = template.get('content', content)
        ann = {
            'id': f'ann_{len(self.announcements)}_{int(datetime.now().timestamp())}',
            'title': announcement_data.get('title', 'Announcement'),
            'content': content,
            'platforms': announcement_data.get('platforms', ['discord', 'minecraft']),
            'scheduled_at': announcement_data.get('scheduled_at', datetime.now().isoformat()),
            'recurrence': announcement_data.get('recurrence'),
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'sent_at': None
        }
        self.announcements.append(ann)
        self._save_announcements()
        return ann

    async def create_template(self, name: str, content: str) -> Dict[str, Any]:
        self.templates[name] = {
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_templates()
        return self.templates[name]

    async def get_scheduled(self) -> List[Dict[str, Any]]:
        return [a for a in self.announcements if a.get('status') == 'scheduled']

    async def cancel(self, announcement_id: str) -> bool:
        for ann in self.announcements:
            if ann.get('id') == announcement_id:
                ann['status'] = 'cancelled'
                self._save_announcements()
                return True
        return False

    async def get_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.templates
