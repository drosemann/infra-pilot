"""Feature 98: Jira/Linear Integration - Bidirectional ticket sync"""

import json
import os
import uuid
import asyncio
import logging
import hashlib
import hmac
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class SyncDirection(Enum):
    BIDIRECTIONAL = "bidirectional"
    TO_EXTERNAL = "to_external"
    FROM_EXTERNAL = "from_external"


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExternalPlatform(Enum):
    JIRA = "jira"
    LINEAR = "linear"


STATUS_MAPPING_DEFAULTS = {
    "jira_to_ip": {
        "To Do": "open",
        "In Progress": "investigating",
        "Done": "resolved",
        "Cancelled": "closed",
        "In Review": "investigating",
        "Blocked": "open",
        "Backlog": "open",
        "Selected for Development": "open"
    },
    "ip_to_jira": {
        "open": "To Do",
        "investigating": "In Progress",
        "identified": "In Progress",
        "resolved": "Done",
        "closed": "Cancelled",
        "monitoring": "In Progress"
    },
    "linear_to_ip": {
        "backlog": "open",
        "triage": "open",
        "in_progress": "investigating",
        "in_review": "investigating",
        "done": "resolved",
        "cancelled": "closed"
    },
    "ip_to_linear": {
        "open": "backlog",
        "investigating": "in_progress",
        "identified": "in_progress",
        "resolved": "done",
        "closed": "cancelled",
        "monitoring": "in_progress"
    }
}


class JiraLinearSync:
    """Bidirectional ticket sync between Infra Pilot and Jira/Linear"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.configs_file = _data_file('ticket_sync_configs.json')
        self.audit_log_file = _data_file('ticket_sync_audit.json')
        self.field_mappings_file = _data_file('ticket_sync_fields.json')

        self.sync_configs: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.field_mappings: Dict[str, Dict[str, str]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.configs_file, "configs"),
            (self.audit_log_file, "audit"),
            (self.field_mappings_file, "mappings")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "configs":
                        self.sync_configs = data
                    elif target == "audit":
                        self.audit_log = data[-10000:]
                    elif target == "mappings":
                        self.field_mappings = data
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_configs(self):
        try:
            with open(self.configs_file, 'w') as f:
                json.dump(self.sync_configs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save configs: {e}")

    def _save_audit(self):
        try:
            with open(self.audit_log_file, 'w') as f:
                json.dump(self.audit_log[-10000:], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save audit: {e}")

    def _save_mappings(self):
        try:
            with open(self.field_mappings_file, 'w') as f:
                json.dump(self.field_mappings, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    async def initialize(self):
        if not self.field_mappings:
            self.field_mappings = {
                "jira": {
                    "title": "summary",
                    "description": "description",
                    "status": "status",
                    "priority": "priority",
                    "assignee": "assignee",
                    "labels": "labels"
                },
                "linear": {
                    "title": "title",
                    "description": "description",
                    "status": "stateId",
                    "priority": "priority",
                    "assignee": "assigneeId",
                    "labels": "labelIds"
                }
            }
            self._save_mappings()
        logger.info("JiraLinearSync initialized with %d configs", len(self.sync_configs))

    async def close(self):
        self._save_configs()
        self._save_audit()
        logger.info("JiraLinearSync closed")

    async def create_sync_config(self, config_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        sync_cfg = {
            "id": config_id,
            "name": config.get("name", config_id),
            "platform": config.get("platform", ExternalPlatform.JIRA.value),
            "direction": config.get("direction", SyncDirection.BIDIRECTIONAL.value),
            "external_url": config.get("external_url", ""),
            "credentials": config.get("credentials", {}),
            "project_mapping": config.get("project_mapping", {}),
            "status_mapping": config.get("status_mapping", {}),
            "field_mapping_overrides": config.get("field_mapping_overrides", {}),
            "sync_interval_minutes": config.get("sync_interval_minutes", 15),
            "auto_create": config.get("auto_create", True),
            "conflict_resolution": config.get("conflict_resolution", "external_wins"),
            "filter_expression": config.get("filter_expression"),
            "enabled": config.get("enabled", True),
            "created_at": self._now(),
            "updated_at": self._now(),
            "last_sync": None,
            "sync_count": 0
        }
        self.sync_configs[config_id] = sync_cfg
        self._save_configs()
        return sync_cfg

    async def get_sync_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        return self.sync_configs.get(config_id)

    async def list_sync_configs(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        configs = list(self.sync_configs.values())
        if platform:
            configs = [c for c in configs if c.get("platform") == platform]
        return configs

    async def update_sync_config(self, config_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        config = self.sync_configs.get(config_id)
        if not config:
            return None
        for key in ["name", "direction", "external_url", "credentials", "project_mapping",
                      "status_mapping", "field_mapping_overrides", "sync_interval_minutes",
                      "auto_create", "conflict_resolution", "filter_expression", "enabled"]:
            if key in updates:
                config[key] = updates[key]
        config["updated_at"] = self._now()
        self._save_configs()
        return config

    async def delete_sync_config(self, config_id: str) -> bool:
        if config_id in self.sync_configs:
            del self.sync_configs[config_id]
            self._save_configs()
            return True
        return False

    async def sync_ticket(self, config_id: str, ticket_data: Dict[str, Any],
                            direction: Optional[str] = None) -> Dict[str, Any]:
        config = self.sync_configs.get(config_id)
        if not config:
            raise ValueError(f"Sync config '{config_id}' not found")
        if not config.get("enabled"):
            return {"status": "skipped", "reason": "Sync config is disabled"}

        sync_direction = direction or config.get("direction", SyncDirection.BIDIRECTIONAL.value)
        platform = config.get("platform", ExternalPlatform.JIRA.value)
        external_id = ticket_data.get("external_id", ticket_data.get("id"))
        local_id = ticket_data.get("local_id", ticket_data.get("id"))

        audit_entry = {
            "id": self._generate_id(),
            "config_id": config_id,
            "platform": platform,
            "direction": sync_direction,
            "local_id": local_id,
            "external_id": external_id,
            "status": SyncStatus.PENDING.value,
            "started_at": self._now(),
            "completed_at": None,
            "error": None
        }

        try:
            if platform == ExternalPlatform.JIRA.value:
                result = await self._sync_jira_ticket(config, ticket_data, sync_direction)
            elif platform == ExternalPlatform.LINEAR.value:
                result = await self._sync_linear_ticket(config, ticket_data, sync_direction)
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            audit_entry["status"] = SyncStatus.SYNCED.value
            audit_entry["completed_at"] = self._now()
            audit_entry["result"] = result

            config["sync_count"] = config.get("sync_count", 0) + 1
            config["last_sync"] = self._now()
            self._save_configs()

        except Exception as e:
            audit_entry["status"] = SyncStatus.FAILED.value
            audit_entry["error"] = str(e)
            logger.error(f"Sync failed for config {config_id}: {e}")

        self.audit_log.append(audit_entry)
        self._save_audit()

        return {
            "config_id": config_id,
            "status": audit_entry["status"],
            "external_id": external_id,
            "local_id": local_id,
            "error": audit_entry.get("error")
        }

    async def _sync_jira_ticket(self, config: Dict[str, Any],
                                  ticket: Dict[str, Any],
                                  direction: str) -> Dict[str, Any]:
        external_url = config.get("external_url", "")
        credentials = config.get("credentials", {})
        email = credentials.get("email", "")
        api_token = credentials.get("api_token", "")

        status_mapping = config.get("status_mapping", {})
        if not status_mapping:
            status_mapping = STATUS_MAPPING_DEFAULTS

        project_key = ticket.get("project_key", config.get("project_mapping", {}).get("default", "IP"))

        if direction in (SyncDirection.TO_EXTERNAL.value, SyncDirection.BIDIRECTIONAL.value):
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(email, api_token)
                current_status = ticket.get("status", "open")
                mapped_status = status_mapping.get(f"ip_to_{ExternalPlatform.JIRA.value}", {}).get(current_status, "To Do")

                issue_data = {
                    "fields": {
                        "project": {"key": project_key},
                        "summary": ticket.get("title", ticket.get("summary", "No title")),
                        "description": ticket.get("description", ""),
                        "issuetype": {"name": ticket.get("issue_type", "Task")}
                    }
                }

                if ticket.get("external_id"):
                    async with session.put(
                        f"{external_url}/rest/api/3/issue/{ticket['external_id']}",
                        json=issue_data,
                        auth=auth
                    ) as resp:
                        if resp.status not in (200, 204):
                            raise Exception(f"Jira update failed: {await resp.text()}")
                        return {"action": "updated", "external_id": ticket["external_id"]}
                else:
                    async with session.post(
                        f"{external_url}/rest/api/3/issue",
                        json=issue_data,
                        auth=auth
                    ) as resp:
                        if resp.status != 201:
                            raise Exception(f"Jira create failed: {await resp.text()}")
                        created = await resp.json()
                        return {"action": "created", "external_id": created.get("id")}

        elif direction in (SyncDirection.FROM_EXTERNAL.value, SyncDirection.BIDIRECTIONAL.value):
            if ticket.get("external_id"):
                async with aiohttp.ClientSession() as session:
                    auth = aiohttp.BasicAuth(email, api_token)
                    async with session.get(
                        f"{external_url}/rest/api/3/issue/{ticket['external_id']}",
                        auth=auth
                    ) as resp:
                        if resp.status != 200:
                            raise Exception(f"Jira fetch failed: {await resp.text()}")
                        data = await resp.json()
                        return {
                            "action": "fetched",
                            "data": {
                                "title": data.get("fields", {}).get("summary", ""),
                                "description": data.get("fields", {}).get("description", {}).get("content", ""),
                                "status": data.get("fields", {}).get("status", {}).get("name", ""),
                                "priority": data.get("fields", {}).get("priority", {}).get("name", "")
                            }
                        }

        return {"action": "noop"}

    async def _sync_linear_ticket(self, config: Dict[str, Any],
                                    ticket: Dict[str, Any],
                                    direction: str) -> Dict[str, Any]:
        api_key = config.get("credentials", {}).get("api_key", "")
        team_id = config.get("credentials", {}).get("team_id", "")

        if not api_key:
            raise ValueError("Linear API key not configured")

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        linear_url = "https://api.linear.app/graphql"

        status_mapping = config.get("status_mapping", {})
        if not status_mapping:
            status_mapping = STATUS_MAPPING_DEFAULTS

        if direction in (SyncDirection.TO_EXTERNAL.value, SyncDirection.BIDIRECTIONAL.value):
            current_status = ticket.get("status", "open")
            mapped_status = status_mapping.get(f"ip_to_{ExternalPlatform.LINEAR.value}", {}).get(current_status, "backlog")

            if ticket.get("external_id"):
                mutation = """
                    mutation IssueUpdate($id: String!, $title: String!, $description: String) {
                        issueUpdate(id: $id, input: { title: $title, description: $description }) {
                            success
                            issue { id }
                        }
                    }
                """
            else:
                mutation = """
                    mutation IssueCreate($title: String!, $description: String, $teamId: String!) {
                        issueCreate(input: { title: $title, description: $description, teamId: $teamId }) {
                            success
                            issue { id }
                        }
                    }
                """

            async with aiohttp.ClientSession() as session:
                variables = {
                    "title": ticket.get("title", "No title"),
                    "description": ticket.get("description", ""),
                    "teamId": team_id
                }
                if ticket.get("external_id"):
                    variables["id"] = ticket["external_id"]

                async with session.post(
                    linear_url,
                    json={"query": mutation, "variables": variables},
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Linear API failed: {await resp.text()}")
                    data = await resp.json()
                    if data.get("errors"):
                        raise Exception(str(data["errors"]))

                    issue_data = data.get("data", {}).get("issueCreate") or data.get("data", {}).get("issueUpdate", {})
                    return {
                        "action": "created" if not ticket.get("external_id") else "updated",
                        "external_id": issue_data.get("issue", {}).get("id")
                    }

        return {"action": "noop"}

    async def sync_all(self, platform: Optional[str] = None) -> Dict[str, Any]:
        configs = await self.list_sync_configs(platform)
        results = {}
        for config in configs:
            if config.get("enabled"):
                try:
                    result = await self.sync_ticket(config["id"], config)
                    results[config["id"]] = result
                except Exception as e:
                    results[config["id"]] = {"status": "error", "error": str(e)}
        return {"synced": len(results), "results": results}

    async def test_connection(self, config_id: str) -> Dict[str, Any]:
        config = self.sync_configs.get(config_id)
        if not config:
            return {"success": False, "error": "Config not found"}

        platform = config.get("platform", ExternalPlatform.JIRA.value)

        try:
            if platform == ExternalPlatform.JIRA.value:
                async with aiohttp.ClientSession() as session:
                    auth = aiohttp.BasicAuth(
                        config.get("credentials", {}).get("email", ""),
                        config.get("credentials", {}).get("api_token", "")
                    )
                    async with session.get(
                        f"{config.get('external_url')}/rest/api/3/myself",
                        auth=auth
                    ) as resp:
                        if resp.status == 200:
                            return {"success": True, "message": "Jira connection successful"}
                        return {"success": False, "error": f"Jira returned status {resp.status}"}

            elif platform == ExternalPlatform.LINEAR.value:
                headers = {
                    "Authorization": config.get("credentials", {}).get("api_key", ""),
                    "Content-Type": "application/json"
                }
                query = "{ viewer { id name } }"
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.linear.app/graphql",
                        json={"query": query},
                        headers=headers
                    ) as resp:
                        data = await resp.json()
                        if data.get("data", {}).get("viewer"):
                            return {"success": True, "message": "Linear connection successful"}
                        return {"success": False, "error": "Invalid Linear API key"}

            return {"success": False, "error": f"Unsupported platform: {platform}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_field_mappings(self, platform: str) -> Dict[str, str]:
        return self.field_mappings.get(platform, {})

    async def update_field_mappings(self, platform: str, mappings: Dict[str, str]) -> Dict[str, str]:
        self.field_mappings[platform] = mappings
        self._save_mappings()
        return mappings

    async def get_audit_log(self, config_id: Optional[str] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        entries = list(reversed(self.audit_log))
        if config_id:
            entries = [e for e in entries if e.get("config_id") == config_id]
        return entries[:limit]
