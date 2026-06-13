from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class IncidentManager:
    """Incident management with on-call schedules, escalation policies, and post-mortems"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.incidents_file = config.get('incidents_file', 'data/incidents.json')
        self.schedules_file = config.get('oncall_schedules_file', 'data/oncall_schedules.json')
        self.templates_file = config.get('postmortem_templates_file', 'data/postmortem_templates.json')
        self.incidents: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        self.templates: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.incidents_file, 'incidents'), (self.schedules_file, 'schedules'), (self.templates_file, 'templates')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_incidents(self):
        try:
            os.makedirs(os.path.dirname(self.incidents_file), exist_ok=True)
            with open(self.incidents_file, 'w') as f:
                json.dump(self.incidents, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save incidents: {e}")

    def _save_schedules(self):
        try:
            os.makedirs(os.path.dirname(self.schedules_file), exist_ok=True)
            with open(self.schedules_file, 'w') as f:
                json.dump(self.schedules, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")

    def _save_templates(self):
        try:
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    async def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        incident = {
            'id': f'inc_{int(datetime.now().timestamp())}_{len(self.incidents)}',
            'title': data.get('title', 'Untitled Incident'),
            'description': data.get('description', ''),
            'severity': data.get('severity', 'minor'),
            'status': 'firing',
            'assigned_to': data.get('assigned_to'),
            'escalation_level': 0,
            'created_at': datetime.now().isoformat(),
            'acknowledged_at': None,
            'acknowledged_by': None,
            'resolved_at': None,
            'resolved_by': None,
            'tags': data.get('tags', []),
            'postmortem': None
        }
        self.incidents.append(incident)
        self._save_incidents()
        return incident

    async def get_incidents(self, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.incidents
        if status:
            results = [i for i in results if i['status'] == status]
        if severity:
            results = [i for i in results if i['severity'] == severity]
        return results[-limit:]

    async def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for incident in self.incidents:
            if incident['id'] == incident_id:
                incident.update(updates)
                incident['updated_at'] = datetime.now().isoformat()
                self._save_incidents()
                return incident
        return None

    async def acknowledge_incident(self, incident_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.update_incident(incident_id, {
            'status': 'acknowledged',
            'acknowledged_at': datetime.now().isoformat(),
            'acknowledged_by': user_id
        })

    async def resolve_incident(self, incident_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.update_incident(incident_id, {
            'status': 'resolved',
            'resolved_at': datetime.now().isoformat(),
            'resolved_by': user_id
        })

    async def escalate_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        for incident in self.incidents:
            if incident['id'] == incident_id:
                incident['escalation_level'] = incident.get('escalation_level', 0) + 1
                incident['status'] = 'escalated'
                incident['updated_at'] = datetime.now().isoformat()
                self._save_incidents()
                return incident
        return None

    async def create_oncall_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        schedule = {
            'id': f'sched_{int(datetime.now().timestamp())}_{len(self.schedules)}',
            'name': data.get('name', 'Unnamed Schedule'),
            'members': data.get('members', []),
            'rotation': data.get('rotation', 'weekly'),
            'escalation_policy': data.get('escalation_policy', []),
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        self.schedules.append(schedule)
        self._save_schedules()
        return schedule

    async def get_oncall_schedules(self) -> List[Dict[str, Any]]:
        return self.schedules

    async def add_escalation_policy(self, schedule_id: str, policy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for schedule in self.schedules:
            if schedule['id'] == schedule_id:
                schedule.setdefault('escalation_policy', []).append(policy)
                schedule['updated_at'] = datetime.now().isoformat()
                self._save_schedules()
                return schedule
        return None

    async def create_postmortem_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        template = {
            'id': f'tmpl_{int(datetime.now().timestamp())}_{len(self.templates)}',
            'name': data.get('name', 'Default Template'),
            'sections': data.get('sections', ['summary', 'timeline', 'root_cause', 'action_items']),
            'created_at': datetime.now().isoformat()
        }
        self.templates.append(template)
        self._save_templates()
        return template

    async def attach_postmortem(self, incident_id: str, template_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        template = next((t for t in self.templates if t['id'] == template_id), None)
        if not template:
            return None
        for incident in self.incidents:
            if incident['id'] == incident_id:
                postmortem = {
                    'template_id': template_id,
                    'sections': {s: data.get(s, '') for s in template.get('sections', [])},
                    'created_at': datetime.now().isoformat()
                }
                incident['postmortem'] = postmortem
                self._save_incidents()
                return incident
        return None
