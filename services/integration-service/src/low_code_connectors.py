"""Feature 93: Low-Code Connector Builder - Visual API connector builder"""

import json
import os
import uuid
import re
import asyncio
import logging
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import hashlib
import hmac

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class NodeType(Enum):
    HTTP_REQUEST = "http_request"
    TRANSFORM = "transform"
    CONDITIONAL = "conditional"
    FILTER = "filter"
    AUTH = "auth"
    DELAY = "delay"
    LOG = "log"
    RESPONSE = "response"
    ERROR_HANDLER = "error_handler"
    LOOP = "loop"
    MERGE = "merge"
    SPLIT = "split"


class AuthType(Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    CUSTOM_HEADER = "custom_header"


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


CONNECTOR_TEMPLATES = {
    "github_api": {
        "name": "GitHub API Connector",
        "description": "Connect to GitHub API for repository operations",
        "nodes": [
            {"id": "auth1", "type": "auth", "config": {"auth_type": "bearer", "token_placeholder": "{{github_token}}"}},
            {"id": "req1", "type": "http_request", "config": {"method": "GET", "url": "https://api.github.com/repos/{{owner}}/{{repo}}"}},
            {"id": "transform1", "type": "transform", "config": {"template": "{\"name\": \"{{data.name}}\", \"stars\": {{data.stargazers_count}}, \"forks\": {{data.forks_count}}}"}}
        ]
    },
    "jira_issues": {
        "name": "Jira Issue Fetcher",
        "description": "Fetch issues from Jira project",
        "nodes": [
            {"id": "auth1", "type": "auth", "config": {"auth_type": "basic", "username_placeholder": "{{jira_email}}", "password_placeholder": "{{jira_token}}"}},
            {"id": "req1", "type": "http_request", "config": {"method": "GET", "url": "https://{{jira_url}}/rest/api/3/search?jql=project={{project_key}}"}},
            {"id": "transform1", "type": "transform", "config": {"template": "{{#each data.issues}}{\"key\": \"{{key}}\", \"summary\": \"{{fields.summary}}\", \"status\": \"{{fields.status.name}}\"}{{/each}}"}}
        ]
    },
    "slack_message": {
        "name": "Slack Message Sender",
        "description": "Send messages to Slack channels",
        "nodes": [
            {"id": "auth1", "type": "auth", "config": {"auth_type": "bearer", "token_placeholder": "{{slack_token}}"}},
            {"id": "req1", "type": "http_request", "config": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "headers": {"Content-Type": "application/json"}, "body": "{\"channel\": \"{{channel}}\", \"text\": \"{{message}}\"}"}}
        ]
    }
}


class LowCodeConnectorBuilder:
    """Visual API connector builder with drag-and-drop workflow designer"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connectors_file = _data_file('connectors.json')
        self.templates_file = _data_file('connector_templates.json')

        self.connectors: Dict[str, Dict[str, Any]] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.connectors_file, "connectors"),
            (self.templates_file, "templates")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "connectors":
                        self.connectors = data
                    elif target == "templates":
                        self.templates = data
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_connectors(self):
        try:
            with open(self.connectors_file, 'w') as f:
                json.dump(self.connectors, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save connectors: {e}")

    def _save_templates(self):
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    async def initialize(self):
        self.templates.update(CONNECTOR_TEMPLATES)
        self._save_templates()
        logger.info("LowCodeConnectorBuilder initialized with %d templates", len(self.templates))

    async def close(self):
        self._save_connectors()
        logger.info("LowCodeConnectorBuilder closed")

    def _validate_node(self, node: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        node_type = node.get("type")
        config = node.get("config", {})

        if node_type == NodeType.HTTP_REQUEST.value:
            if "method" not in config or "url" not in config:
                return False, "HTTP Request nodes require 'method' and 'url'"
            if config.get("method") not in [m.value for m in HttpMethod]:
                return False, f"Invalid HTTP method: {config.get('method')}"
        elif node_type == NodeType.TRANSFORM.value:
            if "template" not in config:
                return False, "Transform nodes require a 'template'"
        elif node_type == NodeType.CONDITIONAL.value:
            if "condition" not in config:
                return False, "Conditional nodes require a 'condition'"
        elif node_type == NodeType.AUTH.value:
            auth_type = config.get("auth_type")
            if auth_type not in [a.value for a in AuthType]:
                return False, f"Invalid auth type: {auth_type}"
        return True, None

    async def create_connector(self, connector_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        nodes = config.get("nodes", [])
        for node in nodes:
            valid, error = self._validate_node(node)
            if not valid:
                raise ValueError(f"Node '{node.get('id')}' validation failed: {error}")

        connector = {
            "id": connector_id,
            "name": config.get("name", "Unnamed Connector"),
            "description": config.get("description", ""),
            "version": config.get("version", "1.0.0"),
            "nodes": nodes,
            "edges": config.get("edges", []),
            "auth_config": config.get("auth_config", {}),
            "parameters": config.get("parameters", []),
            "response_mapping": config.get("response_mapping", {}),
            "error_handling": config.get("error_handling", {"max_retries": 3, "retry_delay_ms": 1000}),
            "tags": config.get("tags", []),
            "created_at": self._now(),
            "updated_at": self._now(),
            "execution_count": 0,
            "last_execution": None,
            "last_error": None
        }
        self.connectors[connector_id] = connector
        self._save_connectors()
        return connector

    async def get_connector(self, connector_id: str) -> Optional[Dict[str, Any]]:
        return self.connectors.get(connector_id)

    async def list_connectors(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        connectors = list(self.connectors.values())
        if tag:
            connectors = [c for c in connectors if tag in c.get("tags", [])]
        return connectors

    async def update_connector(self, connector_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        connector = self.connectors.get(connector_id)
        if not connector:
            return None
        for key in ["name", "description", "nodes", "edges", "auth_config",
                      "parameters", "response_mapping", "error_handling", "tags"]:
            if key in updates:
                connector[key] = updates[key]
        if "nodes" in updates:
            for node in updates["nodes"]:
                valid, error = self._validate_node(node)
                if not valid:
                    raise ValueError(f"Node '{node.get('id')}' validation failed: {error}")
        connector["updated_at"] = self._now()
        self._save_connectors()
        return connector

    async def delete_connector(self, connector_id: str) -> bool:
        if connector_id in self.connectors:
            del self.connectors[connector_id]
            self._save_connectors()
            return True
        return False

    async def execute_connector(self, connector_id: str,
                                  input_data: Dict[str, Any],
                                  parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        connector = self.connectors.get(connector_id)
        if not connector:
            raise ValueError(f"Connector '{connector_id}' not found")

        params = {**(parameters or {}), **input_data}
        nodes = connector.get("nodes", [])
        edges = connector.get("edges", [])
        error_handling = connector.get("error_handling", {})

        context = {
            "input": input_data,
            "params": params,
            "variables": {},
            "output": None
        }

        node_map = {n["id"]: n for n in nodes}
        adjacency = {}
        for edge in edges:
            source = edge.get("source")
            adjacency.setdefault(source, []).append(edge.get("target"))

        execution_order = self._topological_sort(nodes, edges) if edges else [n["id"] for n in nodes]
        max_retries = error_handling.get("max_retries", 3)

        for node_id in execution_order:
            node = node_map.get(node_id)
            if not node:
                continue

            node_type = node["type"]
            node_config = node.get("config", {})

            for attempt in range(max_retries + 1):
                try:
                    if node_type == NodeType.HTTP_REQUEST.value:
                        result = await self._execute_http_node(node_config, context)
                        context["variables"][node.get("output_var", f"{node_id}_result")] = result
                        context["last_response"] = result
                        if attempt > 0:
                            logger.info(f"Retry {attempt} succeeded for node {node_id}")
                        break
                    elif node_type == NodeType.TRANSFORM.value:
                        result = self._execute_transform_node(node_config, context)
                        context["variables"][node.get("output_var", f"{node_id}_result")] = result
                    elif node_type == NodeType.CONDITIONAL.value:
                        result = self._evaluate_condition(node_config, context)
                        context["last_condition"] = result
                    elif node_type == NodeType.FILTER.value:
                        result = self._execute_filter_node(node_config, context)
                        context["variables"][node.get("output_var", f"{node_id}_result")] = result
                    elif node_type == NodeType.AUTH.value:
                        result = self._configure_auth(node_config, context)
                        context["auth_headers"] = result
                    elif node_type == NodeType.DELAY.value:
                        delay_ms = self._resolve_template(node_config.get("duration", "1000"), context)
                        await asyncio.sleep(int(delay_ms) / 1000)
                    elif node_type == NodeType.LOG.value:
                        message = self._resolve_template(node_config.get("message", ""), context)
                        logger.info(f"[Connector {connector_id}] {message}")
                    elif node_type == NodeType.RESPONSE.value:
                        output = self._resolve_template(
                            json.dumps(node_config.get("body", {})), context
                        )
                        try:
                            context["output"] = json.loads(output)
                        except (json.JSONDecodeError, TypeError):
                            context["output"] = {"body": node_config.get("body")}
                    elif node_type == NodeType.ERROR_HANDLER.value:
                        context["error_handled"] = True
                    break
                except Exception as e:
                    logger.warning(f"Node {node_id} (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    if attempt >= max_retries:
                        if node_type != NodeType.ERROR_HANDLER.value:
                            raise e
                        context["last_error"] = str(e)

        connector["execution_count"] = connector.get("execution_count", 0) + 1
        connector["last_execution"] = self._now()
        self._save_connectors()

        return {
            "connector_id": connector_id,
            "execution_id": self._generate_id(),
            "status": "completed",
            "output": context.get("output"),
            "variables": context.get("variables", {}),
            "executed_at": self._now(),
            "node_count": len(nodes)
        }

    async def _execute_http_node(self, config: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        import aiohttp
        method = config.get("method", "GET")
        url = self._resolve_template(config.get("url", ""), context)
        headers = {k: self._resolve_template(v, context) for k, v in config.get("headers", {}).items()}
        auth_headers = context.get("auth_headers", {})
        headers.update(auth_headers)

        body = config.get("body")
        if body and isinstance(body, str):
            body = self._resolve_template(body, context)
            try:
                body = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                pass

        params = {}
        if config.get("query_params"):
            params = {k: self._resolve_template(v, context) for k, v in config["query_params"].items()}

        timeout_val = config.get("timeout_seconds", 30)
        verify_ssl = config.get("verify_ssl", True)

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) and body else None,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout_val),
                ssl=verify_ssl
            ) as resp:
                response_body = await resp.text()
                try:
                    response_json = json.loads(response_body)
                except (json.JSONDecodeError, TypeError):
                    response_json = response_body

                return {
                    "status_code": resp.status,
                    "headers": dict(resp.headers),
                    "body": response_json,
                    "body_text": response_body,
                    "elapsed": resp.elapsed.total_seconds() if hasattr(resp, 'elapsed') else 0
                }

    def _execute_transform_node(self, config: Dict[str, Any],
                                  context: Dict[str, Any]) -> Any:
        template = config.get("template", "")
        resolved = self._resolve_template(template, context)
        try:
            return json.loads(resolved)
        except (json.JSONDecodeError, TypeError):
            return resolved

    def _evaluate_condition(self, config: Dict[str, Any],
                              context: Dict[str, Any]) -> bool:
        condition = config.get("condition", "")
        resolved = self._resolve_template(condition, context)

        if condition.startswith("{{") and condition.endswith("}}"):
            return bool(resolved)

        if "==" in condition:
            parts = condition.split("==", 1)
            left = self._resolve_template(parts[0].strip(), context)
            right = self._resolve_template(parts[1].strip(), context)
            return str(left) == str(right)
        elif "!=" in condition:
            parts = condition.split("!=", 1)
            left = self._resolve_template(parts[0].strip(), context)
            right = self._resolve_template(parts[1].strip(), context)
            return str(left) != str(right)
        elif ">" in condition:
            parts = condition.split(">", 1)
            left = float(self._resolve_template(parts[0].strip(), context) or 0)
            right = float(self._resolve_template(parts[1].strip(), context) or 0)
            return left > right
        elif "<" in condition:
            parts = condition.split("<", 1)
            left = float(self._resolve_template(parts[0].strip(), context) or 0)
            right = float(self._resolve_template(parts[1].strip(), context) or 0)
            return left < right
        return bool(resolved)

    def _execute_filter_node(self, config: Dict[str, Any],
                               context: Dict[str, Any]) -> Any:
        field = config.get("field", "")
        filter_type = config.get("filter_type", "keep")
        value = config.get("value", "")

        data = context.get("last_response", {})
        if isinstance(data, dict):
            items = data.get(field, data.get("data", data.get("results", [])))
        else:
            items = data if isinstance(data, list) else [data]

        if not isinstance(items, list):
            items = [items]

        if filter_type == "keep":
            return [item for item in items if str(item.get(value if isinstance(item, dict) else 0)) == str(value)]
        elif filter_type == "remove":
            return [item for item in items if str(item.get(value if isinstance(item, dict) else 0)) != str(value)]

        return items

    def _configure_auth(self, config: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, str]:
        auth_type = config.get("auth_type", AuthType.NONE.value)
        headers = {}

        if auth_type == AuthType.API_KEY.value:
            key_name = config.get("key_name", "X-API-Key")
            key_value = self._resolve_template(config.get("key_value", ""), context)
            key_location = config.get("key_location", "header")
            if key_location == "header":
                headers[key_name] = key_value
            elif key_location == "query":
                context["auth_query_params"] = {key_name: key_value}
        elif auth_type == AuthType.BEARER.value:
            token = self._resolve_template(config.get("token_placeholder", ""), context)
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == AuthType.BASIC.value:
            username = self._resolve_template(config.get("username_placeholder", ""), context)
            password = self._resolve_template(config.get("password_placeholder", ""), context)
            import base64
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == AuthType.CUSTOM_HEADER.value:
            header_name = config.get("header_name", "Authorization")
            header_value = self._resolve_template(config.get("header_value", ""), context)
            headers[header_name] = header_value

        return headers

    def _resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        def replacer(match):
            expr = match.group(1).strip()
            keys = expr.split(".")
            value = context
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, match.group(0))
                elif isinstance(value, list) and key.isdigit():
                    idx = int(key)
                    value = value[idx] if idx < len(value) else match.group(0)
                else:
                    return match.group(0)
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value) if value is not None else ""

        return re.sub(r'\{\{([^}]+)\}\}', replacer, template)

    def _topological_sort(self, nodes: List[Dict[str, Any]],
                            edges: List[Dict[str, Any]]) -> List[str]:
        in_degree = {n["id"]: 0 for n in nodes}
        adjacency = {n["id"]: [] for n in nodes}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in adjacency and target in in_degree:
                adjacency[source].append(target)
                in_degree[target] = in_degree.get(target, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            nid = queue.pop(0)
            result.append(nid)
            for neighbor in adjacency.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        remaining = [n["id"] for n in nodes if n["id"] not in result]
        result.extend(remaining)
        return result

    async def test_connector(self, connector_id: str,
                               test_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        connector = self.connectors.get(connector_id)
        if not connector:
            raise ValueError(f"Connector '{connector_id}' not found")
        try:
            result = await self.execute_connector(connector_id, test_input or {})
            return {
                "connector_id": connector_id,
                "success": True,
                "output": result.get("output"),
                "execution_time_ms": 0
            }
        except Exception as e:
            return {
                "connector_id": connector_id,
                "success": False,
                "error": str(e),
                "execution_time_ms": 0
            }

    async def import_connector(self, connector_data: Dict[str, Any]) -> Dict[str, Any]:
        connector_id = connector_data.get("id", self._generate_id())
        return await self.create_connector(connector_id, connector_data)

    async def export_connector(self, connector_id: str) -> Optional[Dict[str, Any]]:
        connector = self.connectors.get(connector_id)
        if not connector:
            return None
        export = {k: v for k, v in connector.items() if k not in ["execution_count", "last_execution", "last_error"]}
        export["exported_at"] = self._now()
        return export
