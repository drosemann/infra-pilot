"""Feature 96: Calendar & Scheduling Sync - iCal/Caldav for maintenance windows"""

import json
import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class EventStatus(Enum):
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"


class CalendarSyncManager:
    """Calendar and scheduling sync manager with iCal/Caldav support"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.caldav_url = config.get("caldav_url")
        self.caldav_username = config.get("caldav_username")
        self.caldav_password = config.get("caldav_password")
        self.default_timezone = config.get("default_timezone", "UTC")
        self.sync_interval_minutes = config.get("sync_interval_minutes", 15)

        self.calendars_file = _data_file('calendars.json')
        self.events_file = _data_file('calendar_events.json')

        self.calendars: Dict[str, Dict[str, Any]] = {}
        self.events: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.calendars_file, "calendars"),
            (self.events_file, "events")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "calendars":
                        self.calendars = data
                    elif target == "events":
                        self.events = data
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_calendars(self):
        try:
            with open(self.calendars_file, 'w') as f:
                json.dump(self.calendars, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save calendars: {e}")

    def _save_events(self):
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save events: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _to_ical_dt(self, dt_str: str) -> str:
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%Y%m%dT%H%M%SZ")
        except Exception:
            return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    def _parse_rrule(self, rrule_str: Optional[str]) -> Optional[Dict[str, Any]]:
        if not rrule_str:
            return None
        parts = rrule_str.split(";")
        result = {}
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                result[key.upper()] = value
        return result

    async def create_calendar(self, calendar_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        calendar = {
            "id": calendar_id,
            "name": config.get("name", calendar_id),
            "description": config.get("description", ""),
            "color": config.get("color", "#3B82F6"),
            "timezone": config.get("timezone", self.default_timezone),
            "created_at": self._now(),
            "updated_at": self._now(),
            "sync_enabled": config.get("sync_enabled", False),
            "sync_url": config.get("sync_url"),
            "sync_credentials": config.get("sync_credentials", {}),
            "event_count": 0,
            "metadata": config.get("metadata", {})
        }
        self.calendars[calendar_id] = calendar
        self._save_calendars()
        return calendar

    async def get_calendar(self, calendar_id: str) -> Optional[Dict[str, Any]]:
        return self.calendars.get(calendar_id)

    async def list_calendars(self) -> List[Dict[str, Any]]:
        return list(self.calendars.values())

    async def update_calendar(self, calendar_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cal = self.calendars.get(calendar_id)
        if not cal:
            return None
        for key in ["name", "description", "color", "timezone", "sync_enabled", "sync_url", "metadata"]:
            if key in updates:
                cal[key] = updates[key]
        cal["updated_at"] = self._now()
        self._save_calendars()
        return cal

    async def delete_calendar(self, calendar_id: str) -> bool:
        if calendar_id not in self.calendars:
            return False
        events_to_remove = [k for k, v in self.events.items() if v.get("calendar_id") == calendar_id]
        for eid in events_to_remove:
            del self.events[eid]
        self._save_events()
        del self.calendars[calendar_id]
        self._save_calendars()
        return True

    async def create_event(self, event_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        calendar_id = config.get("calendar_id", "default")
        if calendar_id not in self.calendars:
            await self.create_calendar(calendar_id, {"name": "Default Calendar"})

        event = {
            "id": event_id,
            "calendar_id": calendar_id,
            "title": config.get("title", "Untitled Event"),
            "description": config.get("description", ""),
            "location": config.get("location", ""),
            "start_time": config.get("start_time", self._now()),
            "end_time": config.get("end_time", self._now()),
            "all_day": config.get("all_day", False),
            "status": config.get("status", EventStatus.CONFIRMED.value),
            "rrule": config.get("rrule"),
            "recurring": config.get("rrule") is not None,
            "reminders": config.get("reminders", []),
            "organizer": config.get("organizer", ""),
            "attendees": config.get("attendees", []),
            "categories": config.get("categories", []),
            "created_at": self._now(),
            "updated_at": self._now(),
            "metadata": config.get("metadata", {})
        }
        self.events[event_id] = event
        self.calendars[calendar_id]["event_count"] = self.calendars[calendar_id].get("event_count", 0) + 1
        self._save_events()
        self._save_calendars()
        return event

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.events.get(event_id)

    async def list_events(self, calendar_id: Optional[str] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        events = list(self.events.values())
        if calendar_id:
            events = [e for e in events if e.get("calendar_id") == calendar_id]
        if start_time:
            events = [e for e in events if e.get("end_time", "") >= start_time]
        if end_time:
            events = [e for e in events if e.get("start_time", "") <= end_time]
        if status_filter:
            events = [e for e in events if e.get("status") == status_filter]
        events.sort(key=lambda e: e.get("start_time", ""))
        return events

    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        event = self.events.get(event_id)
        if not event:
            return None
        for key in ["title", "description", "location", "start_time", "end_time",
                      "all_day", "status", "rrule", "reminders", "organizer",
                      "attendees", "categories", "metadata"]:
            if key in updates:
                event[key] = updates[key]
        event["updated_at"] = self._now()
        event["recurring"] = event.get("rrule") is not None
        self._save_events()
        return event

    async def delete_event(self, event_id: str) -> bool:
        if event_id not in self.events:
            return False
        cal_id = self.events[event_id].get("calendar_id", "default")
        if cal_id in self.calendars:
            self.calendars[cal_id]["event_count"] = max(0, self.calendars[cal_id].get("event_count", 0) - 1)
        del self.events[event_id]
        self._save_events()
        self._save_calendars()
        return True

    async def create_maintenance_window(self, window_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        calendar_id = config.get("calendar_id", "maintenance")
        if calendar_id not in self.calendars:
            await self.create_calendar(calendar_id, {
                "name": "Maintenance Windows",
                "color": "#EF4444",
                "description": "Scheduled maintenance windows"
            })

        event_config = {
            "calendar_id": calendar_id,
            "title": config.get("title", "Maintenance Window"),
            "description": config.get("description", ""),
            "start_time": config.get("start_time"),
            "end_time": config.get("end_time"),
            "status": EventStatus.CONFIRMED.value,
            "categories": ["maintenance"],
            "organizer": config.get("organizer", ""),
            "metadata": {
                "type": "maintenance_window",
                "affected_services": config.get("affected_services", []),
                "impact": config.get("impact", "none"),
                "approval_status": config.get("approval_status", "pending"),
                "approved_by": config.get("approved_by"),
                "rollback_plan": config.get("rollback_plan", ""),
                "change_ticket": config.get("change_ticket", "")
            }
        }
        return await self.create_event(window_id, event_config)

    async def list_maintenance_windows(self, upcoming_only: bool = False) -> List[Dict[str, Any]]:
        now = self._now()
        events = await self.list_events(calendar_id="maintenance")
        if upcoming_only:
            events = [e for e in events if e.get("end_time", "") >= now]
        return events

    async def generate_ical_feed(self, calendar_id: Optional[str] = None) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Infra Pilot//Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Infra Pilot{' - ' + self.calendars.get(calendar_id, {}).get('name', '') if calendar_id else 'Calendar'}",
            "X-WR-TIMEZONE:" + self.default_timezone,
        ]

        events = await self.list_events(calendar_id=calendar_id) if calendar_id else await self.list_events()

        for event in events:
            uid = event.get("id", self._generate_id())
            dtstart = self._to_ical_dt(event.get("start_time", self._now()))
            dtend = self._to_ical_dt(event.get("end_time", self._now()))

            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{uid}@infrapilot")
            lines.append(f"DTSTART:{dtstart}")
            lines.append(f"DTEND:{dtend}")
            lines.append(f"SUMMARY:{event.get('title', 'Untitled')}")
            if event.get("description"):
                desc = event["description"].replace("\n", "\\n")
                lines.append(f"DESCRIPTION:{desc}")
            if event.get("location"):
                lines.append(f"LOCATION:{event['location']}")
            lines.append(f"STATUS:{event.get('status', EventStatus.CONFIRMED.value)}")
            lines.append(f"DTSTAMP:{self._to_ical_dt(self._now())}")
            lines.append(f"CREATED:{self._to_ical_dt(event.get('created_at', self._now()))}")
            lines.append(f"LAST-MODIFIED:{self._to_ical_dt(event.get('updated_at', self._now()))}")

            rrule = event.get("rrule")
            if rrule:
                lines.append(f"RRULE:{rrule}")

            for attendee in event.get("attendees", []):
                if isinstance(attendee, str):
                    lines.append(f"ATTENDEE:mailto:{attendee}")

            for reminder in event.get("reminders", []):
                minutes = reminder.get("minutes", 30)
                lines.append("BEGIN:VALARM")
                lines.append(f"TRIGGER:-PT{minutes}M")
                lines.append("ACTION:" + reminder.get("action", "DISPLAY").upper())
                lines.append(f"DESCRIPTION:Reminder: {event.get('title', '')}")
                lines.append("END:VALARM")

            lines.append("END:VEVENT")

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    async def export_ics(self, event_ids: Optional[List[str]] = None) -> str:
        if event_ids:
            events = [self.events.get(eid) for eid in event_ids if eid in self.events]
        else:
            events = list(self.events.values())

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Infra Pilot//ICS Export//EN",
        ]

        for event in events:
            if not event:
                continue
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{event['id']}@infrapilot")
            lines.append(f"DTSTART:{self._to_ical_dt(event.get('start_time', self._now()))}")
            lines.append(f"DTEND:{self._to_ical_dt(event.get('end_time', self._now()))}")
            lines.append(f"SUMMARY:{event.get('title', '')}")
            if event.get("description"):
                lines.append(f"DESCRIPTION:{event['description'].replace(chr(10), '\\n')}")
            lines.append("END:VEVENT")

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    async def import_ics(self, ics_content: str, calendar_id: str = "imported") -> Dict[str, Any]:
        if calendar_id not in self.calendars:
            await self.create_calendar(calendar_id, {"name": "Imported Calendar"})

        import_count = 0
        error_count = 0
        current_event = {}
        in_event = False

        for line in ics_content.splitlines():
            line = line.strip()
            if line == "BEGIN:VEVENT":
                current_event = {}
                in_event = True
            elif line == "END:VEVENT":
                if current_event:
                    eid = self._generate_id()
                    await self.create_event(eid, {
                        "calendar_id": calendar_id,
                        "title": current_event.get("SUMMARY", "Imported Event"),
                        "description": current_event.get("DESCRIPTION", ""),
                        "start_time": current_event.get("DTSTART", self._now()),
                        "end_time": current_event.get("DTEND", self._now()),
                        "location": current_event.get("LOCATION", ""),
                    })
                    import_count += 1
                in_event = False
            elif in_event and ":" in line:
                key, value = line.split(":", 1)
                current_event[key] = value

        return {
            "calendar_id": calendar_id,
            "imported": import_count,
            "errors": error_count
        }

    async def sync_caldav(self, calendar_id: str) -> Dict[str, Any]:
        cal = self.calendars.get(calendar_id)
        if not cal or not cal.get("sync_enabled"):
            return {"status": "skipped", "reason": "Sync not enabled for this calendar"}

        sync_url = cal.get("sync_url") or self.caldav_url
        if not sync_url:
            return {"status": "error", "reason": "No CalDAV URL configured"}

        logger.info(f"Syncing calendar {calendar_id} with {sync_url}")
        try:
            import caldav
            client = caldav.DAVClient(
                url=sync_url,
                username=cal.get("sync_credentials", {}).get("username") or self.caldav_username,
                password=cal.get("sync_credentials", {}).get("password") or self.caldav_password
            )
            principal = client.principal()
            cal_objs = principal.calendars()

            synced = 0
            for cal_obj in cal_objs:
                for event in cal_obj.events():
                    try:
                        ical_data = event.data
                        await self.import_ics(ical_data, calendar_id)
                        synced += 1
                    except Exception as e:
                        logger.warning(f"Failed to sync event: {e}")

            return {"status": "success", "synced": synced}
        except ImportError:
            logger.warning("caldav library not available, skipping sync")
            return {"status": "skipped", "reason": "caldav library not installed"}
        except Exception as e:
            logger.error(f"CalDAV sync failed: {e}")
            return {"status": "error", "error": str(e)}

    async def check_conflicts(self, start_time: str, end_time: str,
                               calendar_id: Optional[str] = None) -> List[Dict[str, Any]]:
        events = await self.list_events(
            calendar_id=calendar_id,
            start_time=start_time,
            end_time=end_time
        )
        conflicts = []
        for event in events:
            e_start = event.get("start_time", "")
            e_end = event.get("end_time", "")
            if e_start < end_time and e_end > start_time:
                conflicts.append(event)
        return conflicts

    async def initialize(self):
        if "default" not in self.calendars:
            await self.create_calendar("default", {"name": "Default Calendar"})
        if "maintenance" not in self.calendars:
            await self.create_calendar("maintenance", {
                "name": "Maintenance Windows",
                "color": "#EF4444"
            })
        logger.info("CalendarSyncManager initialized with %d calendars, %d events",
                     len(self.calendars), len(self.events))

    async def close(self):
        self._save_calendars()
        self._save_events()
        logger.info("CalendarSyncManager closed")
