"""Feature 100: iPaaS/Zapier Integration - Expose triggers for no-code platforms"""

import json
import os
import uuid
import asyncio
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class TriggerType(Enum):
    POLLING = "polling"
    WEBHOOK = "webhook"
    BOTH = "both"


IPaaS_TRIGGERS = {
    "server.created": {
        "name": "Server Created",
        "description": "Triggered when a new server is created",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "srv_123", "name": "My Server", "type": "minecraft", "status": "running", "created_at": "2024-01-01T00:00:00Z"}
    },
    "server.updated": {
        "name": "Server Updated",
        "description": "Triggered when a server configuration is updated",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "srv_123", "name": "My Server", "changes": {"memory": "2048"}}
    },
    "server.deleted": {
        "name": "Server Deleted",
        "description": "Triggered when a server is deleted",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "srv_123", "name": "My Server", "deleted_at": "2024-01-01T00:00:00Z"}
    },
    "server.started": {
        "name": "Server Started",
        "description": "Triggered when a server starts",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "srv_123", "name": "My Server", "started_at": "2024-01-01T00:00:00Z"}
    },
    "server.stopped": {
        "name": "Server Stopped",
        "description": "Triggered when a server stops",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "srv_123", "name": "My Server", "stopped_at": "2024-01-01T00:00:00Z"}
    },
    "alert.triggered": {
        "name": "Alert Triggered",
        "description": "Triggered when an alert is fired",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "alt_123", "severity": "high", "message": "CPU usage above 90%", "triggered_at": "2024-01-01T00:00:00Z"}
    },
    "alert.resolved": {
        "name": "Alert Resolved",
        "description": "Triggered when an alert is resolved",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "alt_123", "resolved_at": "2024-01-01T00:00:00Z"}
    },
    "backup.completed": {
        "name": "Backup Completed",
        "description": "Triggered when a backup completes successfully",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "bkp_123", "server_id": "srv_123", "size_mb": 256, "completed_at": "2024-01-01T00:00:00Z"}
    },
    "backup.failed": {
        "name": "Backup Failed",
        "description": "Triggered when a backup fails",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "bkp_123", "server_id": "srv_123", "error": "Insufficient disk space", "failed_at": "2024-01-01T00:00:00Z"}
    },
    "deployment.started": {
        "name": "Deployment Started",
        "description": "Triggered when a deployment begins",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "dep_123", "service": "api", "version": "v1.2.3", "started_at": "2024-01-01T00:00:00Z"}
    },
    "deployment.completed": {
        "name": "Deployment Completed",
        "description": "Triggered when a deployment finishes successfully",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "dep_123", "service": "api", "version": "v1.2.3", "completed_at": "2024-01-01T00:00:00Z"}
    },
    "deployment.failed": {
        "name": "Deployment Failed",
        "description": "Triggered when a deployment fails",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "dep_123", "service": "api", "version": "v1.2.3", "error": "Health check failed", "failed_at": "2024-01-01T00:00:00Z"}
    },
    "incident.created": {
        "name": "Incident Created",
        "description": "Triggered when a new incident is created",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "inc_123", "title": "Service outage", "severity": "critical", "status": "open", "created_at": "2024-01-01T00:00:00Z"}
    },
    "incident.resolved": {
        "name": "Incident Resolved",
        "description": "Triggered when an incident is resolved",
        "type": TriggerType.WEBHOOK.value,
        "sample_payload": {"id": "inc_123", "title": "Service outage", "resolved_at": "2024-01-01T00:00:00Z"}
    }
}

IPaaS_ACTIONS = {
    "list_servers": {
        "name": "List Servers",
        "description": "Retrieve list of all servers",
        "method": "GET",
        "endpoint": "/api/servers",
        "params": {"limit": {"type": "integer", "required": False, "default": 50}, "status": {"type": "string", "required": False}}
    },
    "get_server": {
        "name": "Get Server Details",
        "description": "Retrieve details of a specific server",
        "method": "GET",
        "endpoint": "/api/servers/{id}",
        "params": {"id": {"type": "string", "required": True}}
    },
    "create_server": {
        "name": "Create Server",
        "description": "Create a new server",
        "method": "POST",
        "endpoint": "/api/servers",
        "params": {"name": {"type": "string", "required": True}, "type": {"type": "string", "required": True}, "memory": {"type": "integer", "required": False, "default": 1024}}
    },
    "delete_server": {
        "name": "Delete Server",
        "description": "Delete a server",
        "method": "DELETE",
        "endpoint": "/api/servers/{id}",
        "params": {"id": {"type": "string", "required": True}}
    },
    "start_server": {
        "name": "Start Server",
        "description": "Start a server",
        "method": "POST",
        "endpoint": "/api/servers/{id}/start",
        "params": {"id": {"type": "string", "required": True}}
    },
    "stop_server": {
        "name": "Stop Server",
        "description": "Stop a server",
        "method": "POST",
        "endpoint": "/api/servers/{id}/stop",
        "params": {"id": {"type": "string", "required": True}}
    },
    "restart_server": {
        "name": "Restart Server",
        "description": "Restart a server",
        "method": "POST",
        "endpoint": "/api/servers/{id}/restart",
        "params": {"id": {"type": "string", "required": True}}
    },
    "list_backups": {
        "name": "List Backups",
        "description": "Retrieve list of backups",
        "method": "GET",
        "endpoint": "/api/backups",
        "params": {"server_id": {"type": "string", "required": False}, "limit": {"type": "integer", "required": False, "default": 50}}
    },
    "create_backup": {
        "name": "Create Backup",
        "description": "Create a new backup",
        "method": "POST",
        "endpoint": "/api/backups",
        "params": {"server_id": {"type": "string", "required": True}, "name": {"type": "string", "required": False}}
    },
    "list_alerts": {
        "name": "List Alerts",
        "description": "Retrieve list of alerts",
        "method": "GET",
        "endpoint": "/api/alerts",
        "params": {"status": {"type": "string", "required": False}, "severity": {"type": "string", "required": False}, "limit": {"type": "integer", "required": False, "default": 50}}
    },
    "acknowledge_alert": {
        "name": "Acknowledge Alert",
        "description": "Acknowledge an alert",
        "method": "POST",
        "endpoint": "/api/alerts/{id}/acknowledge",
        "params": {"id": {"type": "string", "required": True}}
    },
    "get_metrics": {
        "name": "Get Metrics",
        "description": "Retrieve server metrics",
        "method": "GET",
        "endpoint": "/api/servers/{id}/metrics",
        "params": {"id": {"type": "string", "required": True}, "period": {"type": "string", "required": False, "default": "1h"}}
    },
    "list_incidents": {
        "name": "List Incidents",
        "description": "Retrieve list of incidents",
        "method": "GET",
        "endpoint": "/api/incidents",
        "params": {"status": {"type": "string", "required": False}, "severity": {"type": "string", "required": False}, "limit": {"type": "integer", "required": False, "default": 50}}
    }
}


class IPaaSService:
    """iPaaS/Zapier integration - expose triggers and actions for no-code platforms"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_secret = config.get("ipaas_webhook_secret", os.getenv("IPAAS_WEBHOOK_SECRET", "ipaas-secret-key"))
        self.base_url = config.get("api_base_url", "http://localhost:3001")
        self.triggers_file = _data_file('ipaas_triggers.json')
        self.actions_file = _data_file('ipaas_actions.json')

        self.registered_triggers: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.triggers_file):
            try:
                with open(self.triggers_file, 'r') as f:
                    data = json.load(f)
                self.registered_triggers = data
            except Exception as e:
                logger.warning(f"Failed to load triggers: {e}")

    def _save_triggers(self):
        try:
            with open(self.triggers_file, 'w') as f:
                json.dump(self.registered_triggers, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save triggers: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _sign_payload(self, payload: Dict[str, Any]) -> str:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hmac.new(
            self.webhook_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

    async def initialize(self):
        logger.info("IPaaSService initialized with %d triggers, %d actions",
                     len(IPaaS_TRIGGERS), len(IPaaS_ACTIONS))

    async def close(self):
        self._save_triggers()
        logger.info("IPaaSService closed")

    async def list_triggers(self) -> Dict[str, Any]:
        triggers = {}
        for trigger_id, trigger in IPaaS_TRIGGERS.items():
            registered = self.registered_triggers.get(trigger_id)
            triggers[trigger_id] = {
                **trigger,
                "subscribed": registered is not None,
                "webhook_url": registered.get("webhook_url") if registered else None,
                "subscribed_at": registered.get("subscribed_at") if registered else None
            }
        return triggers

    async def get_trigger(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        trigger = IPaaS_TRIGGERS.get(trigger_id)
        if not trigger:
            return None
        registered = self.registered_triggers.get(trigger_id)
        return {
            **trigger,
            "subscribed": registered is not None,
            "webhook_url": registered.get("webhook_url") if registered else None
        }

    async def subscribe_to_trigger(self, trigger_id: str,
                                     webhook_url: str,
                                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if trigger_id not in IPaaS_TRIGGERS:
            raise ValueError(f"Trigger '{trigger_id}' not found")

        subscription = {
            "id": self._generate_id(),
            "trigger_id": trigger_id,
            "webhook_url": webhook_url,
            "secret": self._generate_id(),
            "config": config or {},
            "subscribed_at": self._now(),
            "last_fired": None,
            "fire_count": 0
        }
        self.registered_triggers[trigger_id] = subscription
        self._save_triggers()
        return subscription

    async def unsubscribe_from_trigger(self, trigger_id: str) -> bool:
        if trigger_id in self.registered_triggers:
            del self.registered_triggers[trigger_id]
            self._save_triggers()
            return True
        return False

    async def list_actions(self) -> Dict[str, Any]:
        return IPaaS_ACTIONS

    async def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        return IPaaS_ACTIONS.get(action_id)

    async def execute_action(self, action_id: str,
                               params: Dict[str, Any],
                               auth_token: Optional[str] = None) -> Dict[str, Any]:
        action = IPaaS_ACTIONS.get(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found")

        required_params = {k: v for k, v in action.get("params", {}).items() if v.get("required")}
        for param_name in required_params:
            if param_name not in params:
                raise ValueError(f"Required parameter '{param_name}' missing for action '{action_id}'")

        execution_id = self._generate_id()
        endpoint = action.get("endpoint", "")
        for key, value in params.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))

        return {
            "execution_id": execution_id,
            "action_id": action_id,
            "name": action.get("name", ""),
            "method": action.get("method", "GET"),
            "endpoint": endpoint,
            "params": params,
            "status": "simulated",
            "simulated_at": self._now(),
            "note": "This is a simulated execution. In production, this would call the actual API."
        }

    async def fire_trigger(self, trigger_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        trigger = self.registered_triggers.get(trigger_id)
        if not trigger:
            return {"status": "not_subscribed", "trigger_id": trigger_id}

        webhook_url = trigger.get("webhook_url", "")
        secret = trigger.get("secret", "")

        payload = {
            "trigger_id": trigger_id,
            "event_id": self._generate_id(),
            "timestamp": self._now(),
            "data": data
        }

        signature = self._sign_payload(payload)

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Ipaas-Signature": signature,
                        "X-Ipaas-Event": trigger_id,
                        "User-Agent": "InfraPilot-IPaaS/1.0"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    trigger["fire_count"] = trigger.get("fire_count", 0) + 1
                    trigger["last_fired"] = self._now()
                    self._save_triggers()
                    return {
                        "status": "fired",
                        "trigger_id": trigger_id,
                        "webhook_url": webhook_url,
                        "response_status": resp.status,
                        "fired_at": self._now()
                    }
        except Exception as e:
            trigger["last_error"] = str(e)
            self._save_triggers()
            return {
                "status": "error",
                "trigger_id": trigger_id,
                "error": str(e),
                "fired_at": self._now()
            }

    async def fire_trigger_by_event(self, event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        trigger_id = event_type
        if trigger_id in self.registered_triggers:
            result = await self.fire_trigger(trigger_id, data)
            return [result]

        parts = event_type.split(".")
        if len(parts) >= 2:
            wildcard = f"{parts[0]}.*"
            if wildcard in self.registered_triggers:
                result = await self.fire_trigger(wildcard, data)
                return [result]

        return [{"status": "no_subscriber", "trigger_id": trigger_id}]

    async def list_subscribed_webhooks(self) -> List[Dict[str, Any]]:
        return [
            {"trigger_id": tid, **data}
            for tid, data in self.registered_triggers.items()
        ]

    async def generate_openapi_spec(self) -> Dict[str, Any]:
        paths = {}
        for action_id, action in IPaaS_ACTIONS.items():
            method = action.get("method", "GET").lower()
            endpoint = action.get("endpoint", f"/api/ipaas/actions/{action_id}/execute")
            params = action.get("params", {})
            parameters = []
            for param_name, param_config in params.items():
                parameters.append({
                    "name": param_name,
                    "in": "path" if f"{{{param_name}}}" in endpoint else "query",
                    "required": param_config.get("required", False),
                    "schema": {"type": param_config.get("type", "string")},
                    "description": f"{param_name} parameter"
                })
            paths[endpoint] = {
                method: {
                    "operationId": action_id,
                    "summary": action.get("name", ""),
                    "description": action.get("description", ""),
                    "parameters": parameters,
                    "responses": {
                        "200": {"description": "Successful operation"},
                        "400": {"description": "Invalid parameters"}
                    }
                }
            }

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Infra Pilot API - iPaaS Integration",
                "version": "1.0.0",
                "description": "REST API for no-code platform integration. Supports Zapier, n8n, Make, Pipedream, and more."
            },
            "servers": [{"url": self.base_url, "description": "Infra Pilot API"}],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                },
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "code": {"type": "integer"}
                        }
                    },
                    "WebhookPayload": {
                        "type": "object",
                        "properties": {
                            "trigger_id": {"type": "string"},
                            "event_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "data": {"type": "object"}
                        }
                    }
                }
            },
            "x-ipaas-config": {
                "triggers": [
                    {"id": tid, "name": t.get("name"), "description": t.get("description"),
                     "sample_payload": t.get("sample_payload"), "type": t.get("type")}
                    for tid, t in IPaaS_TRIGGERS.items()
                ],
                "authentication": {
                    "type": "api_key",
                    "location": "header",
                    "name": "X-API-Key"
                }
            }
        }
        return spec

    async def test_endpoint(self, endpoint_url: str, method: str = "GET") -> Dict[str, Any]:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=endpoint_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    body = await resp.text()
                    return {
                        "success": resp.status < 500,
                        "status_code": resp.status,
                        "response_preview": body[:200],
                        "headers": dict(resp.headers)
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
