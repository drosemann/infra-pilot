"""Feature 92: Integration Marketplace - Community integrations (GitHub, Jira, PagerDuty)"""

import json
import os
import uuid
import asyncio
import logging
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


class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_CONFIG = "pending_config"


class IntegrationCategory(Enum):
    VERSION_CONTROL = "version_control"
    ISSUE_TRACKING = "issue_tracking"
    INCIDENT_MANAGEMENT = "incident_management"
    MONITORING = "monitoring"
    CI_CD = "ci_cd"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    SECURITY = "security"
    STORAGE = "storage"
    DATABASE = "database"
    CLOUD = "cloud"
    OTHER = "other"


BUILTIN_INTEGRATIONS = {
    "github": {
        "name": "GitHub",
        "description": "Connect repositories, sync PR status, and trigger deployments on push",
        "category": IntegrationCategory.VERSION_CONTROL.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "github",
        "config_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "GitHub personal access token"},
                "webhook_secret": {"type": "string", "description": "Webhook secret for verification"},
                "repositories": {"type": "array", "items": {"type": "string"}},
                "auto_deploy_branches": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["token"]
        }
    },
    "gitlab": {
        "name": "GitLab",
        "description": "GitLab integration for merge requests, pipelines, and deployments",
        "category": IntegrationCategory.VERSION_CONTROL.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "gitlab",
        "config_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "GitLab instance URL"},
                "token": {"type": "string", "description": "GitLab personal access token"},
                "projects": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["url", "token"]
        }
    },
    "jira": {
        "name": "Jira",
        "description": "Bidirectional issue sync between Infra Pilot incidents and Jira tickets",
        "category": IntegrationCategory.ISSUE_TRACKING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "jira",
        "config_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Jira instance URL"},
                "email": {"type": "string", "description": "Jira account email"},
                "api_token": {"type": "string", "description": "Jira API token"},
                "project_key": {"type": "string", "description": "Default Jira project key"}
            },
            "required": ["url", "email", "api_token"]
        }
    },
    "linear": {
        "name": "Linear",
        "description": "Linear issue tracking integration for incident-to-issue sync",
        "category": IntegrationCategory.ISSUE_TRACKING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "linear",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "Linear API key"},
                "team_id": {"type": "string", "description": "Linear team ID"}
            },
            "required": ["api_key"]
        }
    },
    "pagerduty": {
        "name": "PagerDuty",
        "description": "Sync incidents and on-call schedules with PagerDuty",
        "category": IntegrationCategory.INCIDENT_MANAGEMENT.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "pagerduty",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "PagerDuty API key"},
                "service_id": {"type": "string", "description": "PagerDuty service ID"},
                "escalation_policy_id": {"type": "string"}
            },
            "required": ["api_key", "service_id"]
        }
    },
    "datadog": {
        "name": "Datadog",
        "description": "Stream Datadog metrics, monitors, and events into Infra Pilot",
        "category": IntegrationCategory.MONITORING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "datadog",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "app_key": {"type": "string"},
                "site": {"type": "string", "enum": ["datadoghq.com", "datadoghq.eu"]}
            },
            "required": ["api_key", "app_key"]
        }
    },
    "slack": {
        "name": "Slack",
        "description": "Send notifications, reports, and alerts to Slack channels",
        "category": IntegrationCategory.COMMUNICATION.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "slack",
        "config_schema": {
            "type": "object",
            "properties": {
                "bot_token": {"type": "string"},
                "signing_secret": {"type": "string"},
                "default_channel": {"type": "string"}
            },
            "required": ["bot_token"]
        }
    },
    "discord_bot": {
        "name": "Discord Bot",
        "description": "Extended Discord integration for advanced bot features",
        "category": IntegrationCategory.COMMUNICATION.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "discord",
        "config_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "guild_id": {"type": "string"},
                "report_channel_id": {"type": "string"}
            },
            "required": ["token", "guild_id"]
        }
    },
    "sentry": {
        "name": "Sentry",
        "description": "Sync Sentry errors and create incidents from error thresholds",
        "category": IntegrationCategory.MONITORING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "sentry",
        "config_schema": {
            "type": "object",
            "properties": {
                "dsn": {"type": "string"},
                "auth_token": {"type": "string"},
                "organization": {"type": "string"},
                "project": {"type": "string"}
            },
            "required": ["dsn"]
        }
    },
    "grafana": {
        "name": "Grafana",
        "description": "Embed Grafana dashboards, receive alert webhooks",
        "category": IntegrationCategory.MONITORING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "grafana",
        "config_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "api_key": {"type": "string"},
                "dashboards": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["url"]
        }
    },
    "opsgenie": {
        "name": "OpsGenie",
        "description": "Alert routing and incident management with OpsGenie",
        "category": IntegrationCategory.INCIDENT_MANAGEMENT.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "opsgenie",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "endpoint": {"type": "string"}
            },
            "required": ["api_key"]
        }
    },
    "newrelic": {
        "name": "New Relic",
        "description": "APM data streaming and alert integration with New Relic",
        "category": IntegrationCategory.MONITORING.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "newrelic",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "account_id": {"type": "string"}
            },
            "required": ["api_key"]
        }
    },
    "twilio": {
        "name": "Twilio",
        "description": "SMS and voice call notifications via Twilio",
        "category": IntegrationCategory.COMMUNICATION.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "twilio",
        "config_schema": {
            "type": "object",
            "properties": {
                "account_sid": {"type": "string"},
                "auth_token": {"type": "string"},
                "from_number": {"type": "string"}
            },
            "required": ["account_sid", "auth_token", "from_number"]
        }
    },
    "aws": {
        "name": "Amazon Web Services",
        "description": "AWS cloud integration for resource management and cost analysis",
        "category": IntegrationCategory.CLOUD.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "aws",
        "config_schema": {
            "type": "object",
            "properties": {
                "access_key_id": {"type": "string"},
                "secret_access_key": {"type": "string"},
                "region": {"type": "string", "default": "us-east-1"},
                "role_arn": {"type": "string"}
            },
            "required": ["access_key_id", "secret_access_key"]
        }
    },
    "cloudflare": {
        "name": "Cloudflare",
        "description": "DNS, CDN, and WAF management through Cloudflare API",
        "category": IntegrationCategory.CLOUD.value,
        "version": "1.0.0",
        "author": "Infra Pilot",
        "icon": "cloudflare",
        "config_schema": {
            "type": "object",
            "properties": {
                "api_token": {"type": "string"},
                "email": {"type": "string"},
                "zones": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["api_token"]
        }
    }
}


class IntegrationMarketplace:
    """Integration marketplace with community integrations and one-click install"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.marketplace_dir = config.get("marketplace_dir", os.path.join(DATA_DIR, "marketplace"))
        os.makedirs(self.marketplace_dir, exist_ok=True)

        self.registry_file = os.path.join(self.marketplace_dir, "registry.json")
        self.installed_file = os.path.join(self.marketplace_dir, "installed.json")

        self.registry: Dict[str, Dict[str, Any]] = {}
        self.installed: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        for filepath in [self.registry_file, self.installed_file]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if filepath == self.registry_file:
                        self.registry = data
                    else:
                        self.installed = data
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_registry(self):
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _save_installed(self):
        try:
            with open(self.installed_file, 'w') as f:
                json.dump(self.installed, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save installed: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    async def initialize(self):
        self.registry.update(BUILTIN_INTEGRATIONS)
        self._save_registry()
        logger.info("IntegrationMarketplace initialized with %d builtin integrations",
                     len(BUILTIN_INTEGRATIONS))

    async def close(self):
        self._save_registry()
        self._save_installed()
        logger.info("IntegrationMarketplace closed")

    async def list_marketplace_integrations(self, category: Optional[str] = None,
                                              search: Optional[str] = None,
                                              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        integrations = list(self.registry.values())
        if category:
            integrations = [i for i in integrations if i.get("category") == category]
        if search:
            search_lower = search.lower()
            integrations = [i for i in integrations if
                            search_lower in i.get("name", "").lower() or
                            search_lower in i.get("description", "").lower()]
        total = len(integrations)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = integrations[start:end]
        return {
            "integrations": page_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    async def get_marketplace_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(integration_id)

    async def install_integration(self, integration_id: str,
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        if integration_id not in self.registry:
            raise ValueError(f"Integration '{integration_id}' not found in marketplace")

        if integration_id in self.installed:
            raise ValueError(f"Integration '{integration_id}' is already installed")

        install_id = self._generate_id()
        installed_entry = {
            "id": install_id,
            "integration_id": integration_id,
            "name": self.registry[integration_id].get("name", integration_id),
            "version": self.registry[integration_id].get("version", "1.0.0"),
            "config": config,
            "status": IntegrationStatus.PENDING_CONFIG.value,
            "installed_at": self._now(),
            "updated_at": self._now(),
            "last_health_check": None,
            "health_status": "unknown",
            "metrics": {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0
            }
        }
        self.installed[integration_id] = installed_entry
        self._save_installed()
        return installed_entry

    async def uninstall_integration(self, integration_id: str) -> bool:
        if integration_id not in self.installed:
            raise ValueError(f"Integration '{integration_id}' is not installed")
        del self.installed[integration_id]
        self._save_installed()
        return True

    async def list_installed_integrations(self) -> List[Dict[str, Any]]:
        return list(self.installed.values())

    async def get_installed_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        return self.installed.get(integration_id)

    async def configure_integration(self, integration_id: str,
                                      config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        installed = self.installed.get(integration_id)
        if not installed:
            return None
        installed["config"] = {**installed.get("config", {}), **config}
        installed["status"] = IntegrationStatus.ACTIVE.value
        installed["updated_at"] = self._now()
        self._save_installed()
        return installed

    async def get_integration_config_schema(self, integration_id: str) -> Optional[Dict[str, Any]]:
        integration = self.registry.get(integration_id)
        if not integration:
            return None
        return integration.get("config_schema")

    async def publish_integration(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        integration_id = integration_data.get("id", self._generate_id())
        entry = {
            "id": integration_id,
            "name": integration_data.get("name", "Unnamed Integration"),
            "description": integration_data.get("description", ""),
            "category": integration_data.get("category", IntegrationCategory.OTHER.value),
            "version": integration_data.get("version", "1.0.0"),
            "author": integration_data.get("author", "Community"),
            "icon": integration_data.get("icon", "puzzle"),
            "config_schema": integration_data.get("config_schema", {}),
            "published_at": self._now(),
            "downloads": 0,
            "rating": 0.0,
            "reviews_count": 0,
            "source_url": integration_data.get("source_url", ""),
            "documentation_url": integration_data.get("documentation_url", ""),
            "tags": integration_data.get("tags", []),
            "verified": False
        }
        self.registry[integration_id] = entry
        self._save_registry()
        return entry

    async def update_integration_health(self, integration_id: str,
                                          health_status: str) -> Optional[Dict[str, Any]]:
        installed = self.installed.get(integration_id)
        if not installed:
            return None
        installed["health_status"] = health_status
        installed["last_health_check"] = self._now()
        if health_status == "error":
            installed["status"] = IntegrationStatus.ERROR.value
        elif health_status == "ok":
            installed["status"] = IntegrationStatus.ACTIVE.value
        self._save_installed()
        return installed

    async def record_integration_operation(self, integration_id: str,
                                            success: bool) -> Optional[Dict[str, Any]]:
        installed = self.installed.get(integration_id)
        if not installed:
            return None
        metrics = installed.get("metrics", {})
        metrics["total_operations"] = metrics.get("total_operations", 0) + 1
        if success:
            metrics["successful_operations"] = metrics.get("successful_operations", 0) + 1
        else:
            metrics["failed_operations"] = metrics.get("failed_operations", 0) + 1
        installed["metrics"] = metrics
        self._save_installed()
        return installed
