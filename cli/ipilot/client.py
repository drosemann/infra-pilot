"""HTTP API client for the Infra Pilot backend.

Provides the ``ApiClient`` class with full coverage of all API endpoints.
"""

import json
import logging
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import urlencode

import requests

from .core.exceptions import APIError, AuthenticationError, ConnectionError

logger = logging.getLogger(__name__)

API_PREFIX = "/api"
DEFAULT_TIMEOUT = 30


# Keep the remote side honest; success-shaped responses are not always successful.
class ApiClient:
    """HTTP API client for Infra Pilot backend.

    Maintains full backward compatibility with existing ``cmd_*`` functions
    while adding session management and better error handling.

    Args:
        base_url: The base URL of the API server.
        token: Optional bearer token for authenticated requests.
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _headers(self) -> Dict[str, str]:
        """Return a copy of the current session headers.

        Returns:
            A dictionary of HTTP headers.
        """
        return dict(self.session.headers)

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Send an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            path: API endpoint path (appended to ``/api``).
            data: Optional JSON-serialisable request body.

        Returns:
            The parsed JSON response, or an error dict on failure.
        """
        url = f"{self.base_url}{API_PREFIX}{path}"
        try:
            resp = self.session.request(method, url, json=data, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return {}
        except requests.HTTPError as exc:
            status = exc.response.status_code
            try:
                body = exc.response.json()
                msg = body.get("message", body.get("error", str(exc)))
            except (json.JSONDecodeError, AttributeError):
                msg = str(exc)
            if status == 404:
                logger.warning(
                    "Endpoint not found (404): %s – this endpoint may not be implemented yet",
                    path,
                )
                msg = (
                    f"Not found: {path} – the backend does not implement this endpoint"
                )
            elif status == 501:
                logger.warning(
                    "Not implemented (501): %s – the backend received your request but does not support it",
                    path,
                )
                msg = f"Not implemented: {path} – the backend does not support this operation"
            elif status == 403 and body.get("code") == "scope_denied":
                # Scoped API keys (panel key model v2) surface required
                # scopes explicitly; CLI messages stay actionable.
                required = body.get("required", "?")
                hint = body.get(
                    "hint",
                    "Create a new key with the needed scope (ipilot apikeys create ... --scopes) "
                    "or use a wildcard key.",
                )
                msg = f"This API key lacks permission for {path}: missing scope '{required}'. {hint}"

            else:
                logger.warning("HTTP error %s on %s: %s", status, path, msg)
            return {"error": msg, "scope_denied": body.get("code") == "scope_denied"}
        except requests.ConnectionError as exc:
            logger.warning("Connection failed: %s", exc)
            return {"error": f"Connection failed: {exc}"}
        except requests.Timeout:
            logger.warning("Request timed out: %s %s", method, path)
            return {"error": "Request timed out"}

    def _get(self, path: str) -> Any:
        """Send a GET request.

        Args:
            path: API endpoint path.

        Returns:
            The parsed JSON response.
        """
        return self._request("GET", path)

    def _post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Send a POST request.

        Args:
            path: API endpoint path.
            data: Optional JSON payload.

        Returns:
            The parsed JSON response.
        """
        return self._request("POST", path, data)

    def _put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Send a PUT request.

        Args:
            path: API endpoint path.
            data: Optional JSON payload.

        Returns:
            The parsed JSON response.
        """
        return self._request("PUT", path, data)

    def _delete(self, path: str) -> Any:
        """Send a DELETE request.

        Args:
            path: API endpoint path.

        Returns:
            The parsed JSON response.
        """
        return self._request("DELETE", path)

    def _download(self, path: str) -> Dict[str, Any]:
        """Fetch a non-JSON (raw text) response body.

        Args:
            path: API endpoint path.

        Returns:
            ``{"content": text}`` on success or ``{"error": msg}``.
        """
        url = f"{self.base_url}{API_PREFIX}{path}"
        try:
            resp = self.session.request("GET", url, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return {"content": resp.text}
        except requests.HTTPError as exc:
            status = exc.response.status_code
            try:
                msg = exc.response.json().get("message", str(exc))
            except (json.JSONDecodeError, AttributeError):
                msg = str(exc)
            logger.warning("HTTP error %s on %s: %s", status, path, msg)
            return {"error": msg}
        except requests.ConnectionError as exc:
            logger.warning("Connection failed: %s", exc)
            return {"error": f"Connection failed: {exc}"}
        except requests.Timeout:
            logger.warning("Request timed out: GET %s", path)
            return {"error": "Request timed out"}

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, api_key: str) -> Any:
        """Authenticate with an API key.

        Args:
            api_key: The API key to authenticate with.

        Returns:
            Response data containing ``token``, the key's ``scopes``,
            ``key_class``, expiry and a ``needs_rotation`` hint on success
            (panel key model v2).
        """
        return self._request("POST", "/auth/login", {"api_key": api_key})

    def rotate_api_key(self, key_id: str, overlap_hours: int = 24) -> Any:
        """Rotate an API key; the old key keeps working until the overlap ends."""
        return self._request(
            "POST", f"/api-keys/{key_id}/rotate", {"rotate_overlap_hours": overlap_hours}
        )

    def logout(self) -> Any:
        """Invalidate the current session.

        Returns:
            Response data.
        """
        return self._request("POST", "/auth/logout")

    # ------------------------------------------------------------------
    # Server management
    # ------------------------------------------------------------------

    def list_servers(self) -> Any:
        """List all servers."""
        return self._request("GET", "/apps")

    def get_server(self, server_id: str) -> Any:
        """Get details for a specific server.

        Args:
            server_id: The server ID.

        Returns:
            Server details.
        """
        return self._request("GET", f"/apps/{server_id}")

    def create_server(
        self,
        name: str,
        image: Optional[str] = None,
        memory: Optional[int] = None,
        server_type: Optional[str] = None,
    ) -> Any:
        """Create a new server.

        Args:
            name: Server name.
            image: Docker image (e.g. ``nginx:latest``). Falls back to
                ``server_type`` for backward compatibility with older
                callers that passed a type identifier.
            memory: Optional memory limit in MB (sent as ``memoryLimit``).
            server_type: Deprecated alias for ``image``.

        Returns:
            Created server details.
        """
        actual_image = image or server_type
        payload: Dict[str, Any] = {"name": name, "image": actual_image}
        if memory is not None:
            payload["memoryLimit"] = f"{memory}m"
        return self._request(
            "POST",
            "/apps",
            payload,
        )

    def start_server(self, server_id: str) -> Any:
        """Start a server container.

        Args:
            server_id: The server ID.
        """
        return self._request("POST", f"/apps/{server_id}/start", {})

    def stop_server(self, server_id: str) -> Any:
        """Stop a server container.

        Args:
            server_id: The server ID.
        """
        return self._request("POST", f"/apps/{server_id}/stop", {})

    def restart_server(self, server_id: str) -> Any:
        """Restart a server container.

        Args:
            server_id: The server ID.
        """
        return self._request("POST", f"/apps/{server_id}/restart", {})

    def delete_server(self, server_id: str) -> Any:
        """Delete a server.

        Args:
            server_id: The server ID.
        """
        return self._request("DELETE", f"/apps/{server_id}")

    def server_status(self, server_id: str) -> Any:
        """Get server status.

        Args:
            server_id: The server ID.
        """
        return self._request("GET", f"/apps/{server_id}/status")

    def get_logs(self, server_id: str, lines: int = 50, follow: bool = False) -> Any:
        """Fetch server logs.

        Args:
            server_id: The server ID.
            lines: Number of log lines to return (sent as ``limit`` to match
                the panel API).
            follow: Whether to follow (stream) log output (currently
                informational; the panel returns a paginated snapshot).
        """
        return self._request(
            "GET",
            f"/apps/{server_id}/logs?limit={lines}",
        )

    def list_backups(self, server_id: Optional[str] = None) -> Any:
        """List backups for a server or all backups.

        Args:
            server_id: Optional server ID to filter by.
        """
        path = f"/backup-jobs?app_id={server_id}" if server_id else "/backup-jobs"
        return self._request("GET", path)

    def create_backup(self, server_id: str, s3_target: Optional[str] = None) -> Any:
        """Create a backup of a server.

        Args:
            server_id: The server ID.
            s3_target: Optional S3/Backblaze target for offsite storage.
        """
        data: Dict[str, Any] = {
            "app_id": server_id,
            "name": f"backup-{server_id}",
            "schedule_type": "manual",
        }
        if s3_target:
            data["s3_target"] = s3_target
        return self._request("POST", "/backup-jobs", data)

    def deploy(
        self, server_id: str, branch: str, repo_url: Optional[str] = None
    ) -> Any:
        """Deploy a branch to a server.

        Args:
            server_id: The server ID.
            branch: The branch name to deploy.
            repo_url: Optional git repository URL (fallback to server ID).
        """
        return self._request(
            "POST",
            "/deployments",
            {
                "name": f"deploy-{server_id}",
                "repoUrl": repo_url or server_id,
                "branch": branch,
                "containerId": server_id,
            },
        )

    def health_check(self) -> Any:
        """Check API health."""
        return self._request("GET", "/health")

    def dns_zones(self) -> Any:
        """List DNS zones."""
        return self._request("GET", "/dns-zones")

    def dns_records(self, zone_id: str) -> Any:
        """List DNS records for a zone.

        Args:
            zone_id: The DNS zone ID.
        """
        return self._request("GET", f"/dns-zones/{zone_id}/records")

    def drift_scan(self) -> Any:
        """Run a new configuration drift scan."""
        return self._request("POST", "/drift/scan")

    def drift_list(self) -> Any:
        """List detected configuration drift."""
        return self._request("GET", "/drift/list")

    # ------------------------------------------------------------------
    # SSH Session Management
    # ------------------------------------------------------------------

    def list_ssh_sessions(self, status: Optional[str] = None) -> Any:
        """List SSH sessions."""
        path = "/ssh/sessions"
        if status:
            path += f"?status={status}"
        return self._request("GET", path)

    def ssh_connect(
        self,
        server: str,
        user: str = "root",
        jump_host: Optional[str] = None,
        port: int = 22,
    ) -> Any:
        """Connect to a server via SSH."""
        data = {"server": server, "user": user, "port": port}
        if jump_host:
            data["jump_host"] = jump_host
        return self._request("POST", "/ssh/connect", data)

    def list_jump_hosts(self) -> Any:
        """List SSH jump hosts."""
        return self._request("GET", "/ssh/jump-hosts")

    def create_jump_host(self, name: str, host: str, user: str) -> Any:
        """Create a jump host entry."""
        return self._request(
            "POST", "/ssh/jump-hosts", {"name": name, "host": host, "user": user}
        )

    def list_ssh_keys(self) -> Any:
        """List SSH keys."""
        return self._request("GET", "/ssh/keys")

    def add_ssh_key(self, name: str, key: str) -> Any:
        """Add an SSH key."""
        return self._request("POST", "/ssh/keys", {"name": name, "key": key})

    def delete_ssh_key(self, key_id: str) -> Any:
        """Delete an SSH key."""
        return self._request("DELETE", f"/ssh/keys/{key_id}")

    def get_session_recording(self, session_id: str) -> Any:
        """Get SSH session recording."""
        return self._request("GET", f"/ssh/sessions/{session_id}/recording")

    def list_saved_hosts(self) -> Any:
        """List saved SSH hosts."""
        return self._request("GET", "/ssh/saved-hosts")

    def save_ssh_host(self, name: str, host: str, port: int = 22) -> Any:
        """Save an SSH host."""
        return self._request(
            "POST", "/ssh/saved-hosts", {"name": name, "host": host, "port": port}
        )

    def delete_saved_host(self, host_id: str) -> Any:
        """Delete a saved SSH host."""
        return self._request("DELETE", f"/ssh/saved-hosts/{host_id}")

    # ------------------------------------------------------------------
    # Server Inventory
    # ------------------------------------------------------------------

    def list_inventory(self, **filters) -> Any:
        """List server inventory with filters."""
        params = "&".join(f"{k}={v}" for k, v in filters.items() if v)
        path = f"/inventory?{params}" if params else "/inventory"
        return self._request("GET", path)

    def get_inventory(self, server_id: str) -> Any:
        """Get inventory metadata for a server."""
        return self._request("GET", f"/inventory/{server_id}")

    def update_inventory(self, server_id: str, metadata: Dict[str, Any]) -> Any:
        """Update server inventory metadata."""
        return self._request("PATCH", f"/inventory/{server_id}", metadata)

    def add_inventory_tag(self, server_id: str, tag: str) -> Any:
        """Add a tag to a server."""
        return self._request("POST", f"/inventory/{server_id}/tags", {"tag": tag})

    def remove_inventory_tag(self, server_id: str, tag: str) -> Any:
        """Remove a tag from a server."""
        return self._request("DELETE", f"/inventory/{server_id}/tags/{tag}")

    def get_inventory_tags(self, server_id: str) -> Any:
        """Get tags for a server."""
        return self._request("GET", f"/inventory/{server_id}/tags")

    def list_inventory_tags(self) -> Any:
        """List all inventory tags in use."""
        return self._request("GET", "/inventory/tags")

    # ------------------------------------------------------------------
    # Secret Management
    # ------------------------------------------------------------------

    def list_secrets(self, path: Optional[str] = None) -> Any:
        """List secrets."""
        p = f"/secrets?path={path}" if path else "/secrets"
        return self._request("GET", p)

    def get_secret(self, key: str, version: Optional[int] = None) -> Any:
        """Get a secret value."""
        p = f"/secrets/{key}"
        if version is not None:
            p += f"?version={version}"
        return self._request("GET", p)

    def set_secret(
        self, key: str, value: str, rotate: bool = False, rotation_days: int = 90
    ) -> Any:
        """Set a secret value."""
        return self._request(
            "POST",
            "/secrets",
            {
                "key": key,
                "value": value,
                "rotate": rotate,
                "rotation_days": rotation_days,
            },
        )

    def delete_secret(self, key: str) -> Any:
        """Delete a secret."""
        return self._request("DELETE", f"/secrets/{key}")

    def list_secret_versions(self, key: str) -> Any:
        """List versions of a secret."""
        return self._request("GET", f"/secrets/{key}/versions")

    def rotate_secret(self, key: str) -> Any:
        """Rotate a secret."""
        return self._request("POST", f"/secrets/{key}/rotate")

    def rotate_all_secrets(self) -> Any:
        """Rotate all secrets due for rotation."""
        return self._request("POST", "/secrets/rotate-all")

    def list_secrets_due_for_rotation(self) -> Any:
        """List secrets due for rotation."""
        return self._request("GET", "/secrets/due-for-rotation")

    def grant_secret_access(self, key: str, role: str) -> Any:
        """Grant role access to a secret."""
        return self._request("POST", f"/secrets/{key}/access", {"role": role})

    def revoke_secret_access(self, key: str, role: str) -> Any:
        """Revoke role access from a secret."""
        return self._request("DELETE", f"/secrets/{key}/access/{role}")

    def list_secret_access(self, key: str) -> Any:
        """List roles with access to a secret."""
        return self._request("GET", f"/secrets/{key}/access")

    # ------------------------------------------------------------------
    # Webhook Management
    # ------------------------------------------------------------------

    def list_webhooks(self) -> Any:
        """List webhooks."""
        return self._request("GET", "/webhooks")

    def create_webhook(
        self, name: str, url: str, events: List[str], secret: Optional[str] = None
    ) -> Any:
        """Create a webhook."""
        data = {"name": name, "url": url, "events": events}
        if secret:
            data["secret"] = secret
        return self._request("POST", "/webhooks", data)

    def delete_webhook(self, webhook_id: str) -> Any:
        """Delete a webhook."""
        return self._request("DELETE", f"/webhooks/{webhook_id}")

    def test_webhook(
        self, webhook_id: Optional[str] = None, event: str = "test"
    ) -> Any:
        """Test a webhook."""
        path = f"/webhooks/{webhook_id}/test" if webhook_id else "/webhooks/test"
        return self._request("POST", path, {"event": event})

    def get_webhook_logs(self, webhook_id: Optional[str] = None) -> Any:
        """Get webhook delivery logs."""
        path = f"/webhooks/{webhook_id}/logs" if webhook_id else "/webhooks/logs"
        return self._request("GET", path)

    # ------------------------------------------------------------------
    # API Key Management
    # ------------------------------------------------------------------

    def list_api_keys(self) -> Any:
        """List API keys."""
        return self._request("GET", "/api-keys")

    def create_api_key(
        self,
        name: str,
        role: str = "user",
        expire_days: Optional[int] = None,
        scopes: Optional[list] = None,
        key_class: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Any:
        """Create an API key (scoped keys: see panel key model v2)."""
        data: Dict[str, Any] = {"name": name, "role": role}
        if expire_days:
            data["expire_days"] = expire_days
        if scopes is not None:
            data["scopes"] = scopes
        if key_class:
            data["key_class"] = key_class
        if app_id:
            data["app_id"] = app_id
        return self._request("POST", "/api-keys", data)

    def revoke_api_key(self, key_id: str) -> Any:
        """Revoke an API key."""
        return self._request("DELETE", f"/api-keys/{key_id}")

    # ------------------------------------------------------------------
    # Plugin Management
    # ------------------------------------------------------------------

    def list_plugins(self, installed_only: bool = False) -> Any:
        """List plugins."""
        path = "/plugins?installed=true" if installed_only else "/plugins"
        return self._request("GET", path)

    def install_plugin(
        self, name: str, source: Optional[str] = None, version: Optional[str] = None
    ) -> Any:
        """Install a plugin."""
        data = {"name": name}
        if source:
            data["source"] = source
        if version:
            data["version"] = version
        return self._request("POST", "/plugins/install", data)

    def uninstall_plugin(self, name: str) -> Any:
        """Uninstall a plugin."""
        return self._request("POST", f"/plugins/{name}/uninstall")

    def update_plugin(self, name: str) -> Any:
        """Update a plugin."""
        return self._request("POST", f"/plugins/{name}/update")

    def update_all_plugins(self) -> Any:
        """Update all plugins."""
        return self._request("POST", "/plugins/update-all")

    def list_plugin_updates(self) -> Any:
        """List available plugin updates."""
        return self._request("GET", "/plugins/updates")

    def get_plugin_info(self, name: str) -> Any:
        """Get plugin info."""
        return self._request("GET", f"/plugins/{name}")

    # ------------------------------------------------------------------
    # Deployment Templates
    # ------------------------------------------------------------------

    def list_templates(self, template_type: Optional[str] = None) -> Any:
        """List deployment templates."""
        path = f"/templates?type={template_type}" if template_type else "/templates"
        return self._request("GET", path)

    def get_template(self, template: str) -> Any:
        """Get template details."""
        return self._request("GET", f"/templates/{template}")

    def deploy_template(
        self,
        template: str,
        name: str,
        server: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> Any:
        """Deploy a template."""
        data = {"template": template, "name": name}
        if server:
            data["server"] = server
        if variables:
            data["variables"] = variables
        if dry_run:
            data["dry_run"] = True
        return self._request("POST", "/templates/deploy", data)

    def init_template(self, template: str, name: str, output_dir: str = ".") -> Any:
        """Initialize a project from a template."""
        return self._request(
            "POST",
            "/templates/init",
            {"template": template, "name": name, "output_dir": output_dir},
        )

    # ------------------------------------------------------------------
    # Doctor / Benchmark / Diagnose
    # ------------------------------------------------------------------

    def benchmark_server(self, server: str, duration: int = 10) -> Any:
        """Benchmark a server."""
        return self._request(
            "POST", f"/doctor/benchmark/{server}", {"duration": duration}
        )

    def benchmark_system(self, duration: int = 10) -> Any:
        """Benchmark the local system."""
        return self._request("POST", "/doctor/benchmark", {"duration": duration})

    def diagnose_server(self, server: str, issue: Optional[str] = None) -> Any:
        """Diagnose a server."""
        data = {}
        if issue:
            data["issue"] = issue
        return self._request("POST", f"/doctor/diagnose/{server}", data)

    def diagnose_system(self, issue: Optional[str] = None) -> Any:
        """Diagnose the local system."""
        data = {}
        if issue:
            data["issue"] = issue
        return self._request("POST", "/doctor/diagnose", data)

    # ------------------------------------------------------------------
    # Rollback / Change History
    # ------------------------------------------------------------------

    def list_changes(self, resource: Optional[str] = None, limit: int = 20) -> Any:
        """List recent changes."""
        params = f"?limit={limit}"
        if resource:
            params += f"&resource={resource}"
        return self._request("GET", f"/changes{params}")

    def undo_change(self, change_id: str, dry_run: bool = False) -> Any:
        """Undo a change."""
        return self._request("POST", f"/changes/{change_id}/undo", {"dry_run": dry_run})

    def rollback_resource(
        self, resource_type: str, resource_id: str, version: Optional[str] = None
    ) -> Any:
        """Rollback a resource."""
        data = {"resource_type": resource_type, "resource_id": resource_id}
        if version:
            data["version"] = version
        return self._request("POST", "/rollback", data)

    def get_change_history(
        self, resource_type: Optional[str] = None, resource_id: Optional[str] = None
    ) -> Any:
        """Get change history."""
        params = []
        if resource_type:
            params.append(f"resource_type={resource_type}")
        if resource_id:
            params.append(f"resource_id={resource_id}")
        qs = "&".join(params)
        path = f"/changes/history?{qs}" if qs else "/changes/history"
        return self._request("GET", path)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def metrics_realtime(self, app_id: Optional[str] = None) -> Any:
        """Get real-time resource metrics.

        Args:
            app_id: Optional app ID for per-container stats.

        Returns:
            Real-time cpu/memory/disk/network snapshot.
        """
        path = "/metrics/realtime"
        if app_id:
            path += f"?appId={app_id}"
        return self._request("GET", path)

    def metrics_history(
        self,
        app_id: Optional[str] = None,
        period: str = "1h",
        resolution: str = "5m",
        until: Optional[str] = None,
    ) -> Any:
        """Get historical time-series metrics.

        Args:
            app_id: Optional app ID to filter by.
            period: Window length (1h, 6h, 24h, 7d).
            resolution: Aggregation bucket (1m, 5m, 1h).
            until: Optional ISO-8601 end of window (reserved for backends
                that support closed ranges).

        Returns:
            Time-series points with cpu/memory/tps/players averages.
        """
        params: List[str] = [f"period={period}", f"resolution={resolution}"]
        if app_id:
            params.append(f"appId={app_id}")
        if until:
            params.append(f"until={until}")
        return self._request("GET", f"/metrics/history?{'&'.join(params)}")

    def metrics_aggregated(self) -> Any:
        """Get aggregated metrics across all apps."""
        return self._request("GET", "/metrics/aggregated")

    def metrics_grafana_url(self) -> Any:
        """Get the configured Grafana embed URL (if any)."""
        return self._request("GET", "/metrics/grafana-url")

    # ------------------------------------------------------------------
    # Alert Rules & Incidents
    # ------------------------------------------------------------------

    def list_alert_configs(self) -> Any:
        """List alert rule configurations."""
        return self._request("GET", "/alert-configs")

    def create_alert_config(
        self,
        metric_type: str,
        operator: str,
        threshold: float,
        enabled: bool = True,
        notify_email: bool = False,
    ) -> Any:
        """Create an alert rule.

        Args:
            metric_type: Metric to watch (e.g. cpu, memory, tps, players).
            operator: Comparison operator (gt, lt, gte, lte, eq).
            threshold: Threshold value.
            enabled: Whether the rule starts enabled.
            notify_email: Whether email notifications are requested.

        Returns:
            The created alert configuration.
        """
        return self._request(
            "POST",
            "/alert-configs",
            {
                "metric_type": metric_type,
                "operator": operator,
                "threshold": threshold,
                "enabled": enabled,
                "notify_email": notify_email,
            },
        )

    def update_alert_config(self, config_id: str, **fields: Any) -> Any:
        """Update an alert rule.

        Args:
            config_id: Alert configuration ID.
            **fields: Fields to update (metric_type, operator, threshold,
                enabled, notify_email).

        Returns:
            The updated alert configuration.
        """
        return self._request("PATCH", f"/alert-configs/{config_id}", fields)

    def delete_alert_config(self, config_id: str) -> Any:
        """Delete an alert rule.

        Args:
            config_id: Alert configuration ID.
        """
        return self._request("DELETE", f"/alert-configs/{config_id}")

    def list_alert_history(self, limit: int = 100) -> Any:
        """List triggered alert incidents.

        Args:
            limit: Maximum number of incidents to return.
        """
        return self._request("GET", f"/alert-history?limit={limit}")

    def acknowledge_alert(self, alert_id: str) -> Any:
        """Acknowledge a triggered alert.

        Args:
            alert_id: Alert history entry ID.
        """
        return self._request("POST", f"/alert-history/{alert_id}/acknowledge", {})

    def resolve_alert(self, alert_id: str) -> Any:
        """Resolve a triggered alert.

        Args:
            alert_id: Alert history entry ID.
        """
        return self._request("POST", f"/alert-history/{alert_id}/resolve", {})

    # ------------------------------------------------------------------
    # Audit Log
    # ------------------------------------------------------------------

    def list_audit_log(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Any:
        """List audit log entries (server-side paginated).

        Args:
            actor: Optional user ID filter (forwarded; backends that scope
                the log to the token owner may ignore it).
            action: Optional action filter (e.g. ``alert:create``).
            resource: Optional entity type filter (e.g. ``alert_config``).
            start_date: Optional ISO-8601 lower bound on ``created_at``.
            end_date: Optional ISO-8601 upper bound on ``created_at``.
            limit: Page size (panel caps this at 200).
            offset: Pagination offset.

        Returns:
            ``{data, total, limit, offset}`` response.
        """
        params = [f"limit={limit}", f"offset={offset}"]
        for key, value in (
            ("user_id", actor),
            ("action", action),
            ("entity_type", resource),
            ("start_date", start_date),
            ("end_date", end_date),
        ):
            if value:
                params.append(f"{key}={value}")
        return self._request("GET", f"/audit-log?{'&'.join(params)}")

    # ------------------------------------------------------------------
    # Runbooks
    # ------------------------------------------------------------------

    def list_runbooks(self) -> Any:
        """List runbooks (built-in and user-defined)."""
        return self._request("GET", "/runbooks")

    def create_runbook(
        self, name: str, description: str, steps: List[Dict[str, Any]]
    ) -> Any:
        """Create a runbook.

        Args:
            name: Runbook name.
            description: Human-readable description.
            steps: Ordered step definitions (``action``/``target`` dicts).

        Returns:
            The created runbook.
        """
        return self._request(
            "POST",
            "/runbooks",
            {"name": name, "description": description, "steps": steps},
        )

    def update_runbook(
        self,
        runbook_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """Update a runbook.

        Args:
            runbook_id: Runbook ID.
            name: Optional new name.
            description: Optional new description.
            steps: Optional replacement step list.

        Returns:
            The updated runbook.
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if steps is not None:
            data["steps"] = steps
        return self._request("PATCH", f"/runbooks/{runbook_id}", data)

    def delete_runbook(self, runbook_id: str) -> Any:
        """Delete a runbook.

        Args:
            runbook_id: Runbook ID.
        """
        return self._request("DELETE", f"/runbooks/{runbook_id}")

    def execute_runbook(self, runbook_id: str) -> Any:
        """Execute a runbook.

        Args:
            runbook_id: Runbook ID.

        Returns:
            Execution result with status, execution_id, and step outputs.
        """
        return self._request("POST", f"/runbooks/{runbook_id}/execute", {})

    def get_runbook_execution(self, execution_id: str) -> Any:
        """Get the status of a runbook execution.

        Args:
            execution_id: Execution ID returned by ``execute_runbook``.
        """
        return self._request("GET", f"/runbooks/executions/{execution_id}")

    def list_runbook_executions(self, runbook_id: Optional[str] = None) -> Any:
        """List runbook executions.

        Args:
            runbook_id: Optional runbook ID to filter by.
        """
        path = "/runbooks/executions"
        if runbook_id:
            path += f"?runbook_id={runbook_id}"
        return self._request("GET", path)

    # ------------------------------------------------------------------
    # Maintenance Windows
    # ------------------------------------------------------------------

    def list_maintenance_windows(self) -> Any:
        """List maintenance windows."""
        return self._request("GET", "/maintenance-windows")

    def create_maintenance_window(
        self,
        title: str,
        starts_at: str,
        ends_at: str,
        description: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Any:
        """Create a maintenance window.

        Args:
            title: Window title.
            starts_at: ISO-8601 start timestamp.
            ends_at: ISO-8601 end timestamp.
            description: Optional description.
            app_id: Optional app the window applies to.

        Returns:
            The created maintenance window.
        """
        data: Dict[str, Any] = {
            "title": title,
            "starts_at": starts_at,
            "ends_at": ends_at,
        }
        if description is not None:
            data["description"] = description
        if app_id is not None:
            data["app_id"] = app_id
        return self._request("POST", "/maintenance-windows", data)

    def update_maintenance_window(self, window_id: str, **fields: Any) -> Any:
        """Update a maintenance window.

        Args:
            window_id: Maintenance window ID.
            **fields: Fields to update (title, description, app_id,
                starts_at, ends_at, status).

        Returns:
            The updated maintenance window.
        """
        return self._request("PATCH", f"/maintenance-windows/{window_id}", fields)

    def delete_maintenance_window(self, window_id: str) -> Any:
        """Delete a maintenance window.

        Args:
            window_id: Maintenance window ID.
        """
        return self._request("DELETE", f"/maintenance-windows/{window_id}")

    # ------------------------------------------------------------------
    # Notification Channels
    # ------------------------------------------------------------------

    def list_notification_channels(self) -> Any:
        """List notification channels."""
        return self._request("GET", "/notification-channels")

    def create_notification_channel(
        self, name: str, channel_type: str, config: Dict[str, Any]
    ) -> Any:
        """Create a notification channel.

        Args:
            name: Channel name.
            channel_type: One of email, webhook, telegram.
            config: Channel-specific configuration payload.

        Returns:
            The created channel.
        """
        return self._request(
            "POST",
            "/notification-channels",
            {"name": name, "type": channel_type, "config": config},
        )

    def update_notification_channel(self, channel_id: str, **fields: Any) -> Any:
        """Update a notification channel.

        Args:
            channel_id: Channel ID.
            **fields: Fields to update (name, config, enabled).

        Returns:
            The updated channel.
        """
        return self._request(
            "PATCH", f"/notification-channels/{channel_id}", fields
        )

    def delete_notification_channel(self, channel_id: str) -> Any:
        """Delete a notification channel.

        Args:
            channel_id: Channel ID.
        """
        return self._request("DELETE", f"/notification-channels/{channel_id}")

    def test_notification_channel(self, channel_id: str) -> Any:
        """Send a test notification through a channel.

        Args:
            channel_id: Channel ID.
        """
        return self._request("POST", f"/notification-channels/{channel_id}/test", {})

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------

    def list_organizations(self) -> Any:
        """List organizations the current user owns or belongs to."""
        return self._request("GET", "/organizations")

    def create_organization(self, name: str, slug: str) -> Any:
        """Create an organization.

        Args:
            name: Organization name.
            slug: URL-safe organization slug.

        Returns:
            The created organization.
        """
        return self._request("POST", "/organizations", {"name": name, "slug": slug})

    def list_organization_members(self, org_id: str) -> Any:
        """List members of an organization.

        Args:
            org_id: Organization ID.
        """
        return self._request("GET", f"/organizations/{org_id}/members")

    def invite_organization_member(
        self, org_id: str, email: str, role: str = "member"
    ) -> Any:
        """Invite a user to an organization.

        Args:
            org_id: Organization ID.
            email: Invitee email address.
            role: Role to assign (member, admin, owner).

        Returns:
            The invitation/membership record.
        """
        return self._request(
            "POST",
            f"/organizations/{org_id}/members",
            {"email": email, "role": role},
        )

    def remove_organization_member(self, org_id: str, user_id: str) -> Any:
        """Remove a member from an organization.

        Args:
            org_id: Organization ID.
            user_id: Member user ID.
        """
        return self._request("DELETE", f"/organizations/{org_id}/members/{user_id}")

    def set_organization_member_role(
        self, org_id: str, user_id: str, role: str
    ) -> Any:
        """Change a member's role in an organization.

        Args:
            org_id: Organization ID.
            user_id: Member user ID.
            role: New role (member, admin, owner).

        Returns:
            The updated membership record.
        """
        return self._request(
            "PATCH",
            f"/organizations/{org_id}/members/{user_id}",
            {"role": role},
        )

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    def list_databases(self) -> Any:
        """List managed databases for the current user."""
        return self._request("GET", "/databases")

    def create_database(self, name: str, app_id: Optional[str] = None) -> Any:
        """Create a managed database.

        Args:
            name: Database name (alphanumeric plus underscores).
            app_id: Optional app to associate.

        Returns:
            The created database (credentials partially masked).
        """
        data: Dict[str, Any] = {"name": name}
        if app_id:
            data["appId"] = app_id
        return self._request("POST", "/databases", data)

    def get_database(self, database_id: str) -> Any:
        """Get details for a managed database.

        Args:
            database_id: Database ID.
        """
        return self._request("GET", f"/databases/{database_id}")

    def delete_database(self, database_id: str) -> Any:
        """Delete a managed database.

        Args:
            database_id: Database ID.
        """
        return self._request("DELETE", f"/databases/{database_id}")

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def get_report(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Any:
        """Generate an on-demand usage report.

        Args:
            start_date: Optional ISO-8601 start of the report period.
            end_date: Optional ISO-8601 end of the report period.

        Returns:
            The computed report payload.
        """
        params = []
        if start_date:
            params.append(f"start_date={start_date}")
        if end_date:
            params.append(f"end_date={end_date}")
        qs = "&".join(params)
        return self._request("GET", f"/reports?{qs}" if qs else "/reports")

    def download_report(
        self,
        fmt: str = "csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Any:
        """Download a report in the given format.

        Args:
            fmt: Export format (csv, pdf, or json).
            start_date: Optional ISO-8601 start of the report period.
            end_date: Optional ISO-8601 end of the report period.

        Returns:
            ``{"content": str}`` on success or ``{"error": msg}``.
        """
        params = [f"format={fmt}"]
        if start_date:
            params.append(f"start_date={start_date}")
        if end_date:
            params.append(f"end_date={end_date}")
        return self._download(f"/reports/export?{'&'.join(params)}")

    def create_report_schedule(self, frequency: str = "daily") -> Any:
        """Schedule a recurring report.

        Args:
            frequency: Recurrence frequency (daily or weekly).
        """
        return self._request("POST", "/reports/schedules", {"frequency": frequency})

    # ------------------------------------------------------------------
    # Two-Factor Authentication
    # ------------------------------------------------------------------

    def setup_2fa(self, user_id: str) -> Any:
        """Begin 2FA setup for a user.

        Args:
            user_id: The user ID to provision 2FA for.

        Returns:
            ``{secret, uri, qr_code_url}`` for the authenticator app.
        """
        return self._request("POST", "/auth/2fa/setup", {"user_id": user_id})

    def verify_2fa_setup(self, user_id: str, totp_code: str) -> Any:
        """Confirm a 2FA setup with a TOTP code.

        Args:
            user_id: The user ID being provisioned.
            totp_code: 6-digit TOTP code from the authenticator app.

        Returns:
            ``{success: bool}``.
        """
        return self._request(
            "POST", "/auth/2fa/verify-setup", {"user_id": user_id, "totp_code": totp_code}
        )

    def verify_2fa(self, temp_token: str, totp_code: str) -> Any:
        """Complete a login challenge with a TOTP code.

        Args:
            temp_token: Temporary token issued by the login step.
            totp_code: 6-digit TOTP code.

        Returns:
            ``{token}`` session token on success.
        """
        return self._request(
            "POST", "/auth/2fa/verify", {"temp_token": temp_token, "totp_code": totp_code}
        )

    def verify_2fa_backup(self, temp_token: str, backup_code: str) -> Any:
        """Complete a login challenge with a backup code.

        Args:
            temp_token: Temporary token issued by the login step.
            backup_code: Single-use backup code.

        Returns:
            ``{token}`` session token on success.
        """
        return self._request(
            "POST",
            "/auth/2fa/verify-backup",
            {"temp_token": temp_token, "backup_code": backup_code},
        )

    def disable_2fa(self, user_id: str, password: str) -> Any:
        """Disable 2FA for a user.

        Args:
            user_id: The user ID.
            password: The user's password for confirmation.

        Returns:
            ``{success: bool}``.
        """
        return self._request(
            "POST", "/auth/2fa/disable", {"user_id": user_id, "password": password}
        )

    def get_2fa_backup_codes(self, user_id: Optional[str] = None) -> Any:
        """Get stored 2FA backup codes.

        Args:
            user_id: Optional user ID; the panel scopes this to the token
                owner regardless of the value sent.
        """
        path = "/auth/2fa/backup-codes"
        if user_id:
            path += f"?user_id={user_id}"
        return self._request("GET", path)

    def get_current_user(self) -> Any:
        """Get the authenticated user's profile."""
        return self._request("GET", "/user")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def global_search(self, query: str) -> Any:
        """Search across apps, servers, backups, runbooks, secrets, hosts.

        Args:
            query: Search term (at least 2 characters on the panel side).

        Returns:
            ``{results: [{type, id, title, subtitle}]}``.
        """
        return self._request("GET", f"/global-search?{urlencode({'q': query})}")

    def basic_search(self, query: str) -> Any:
        """Search apps, audit actions, and backups (legacy endpoint).

        Args:
            query: Search term.

        Returns:
            ``{results: [{id, name, type}]}``.
        """
        return self._request("GET", f"/search?{urlencode({'q': query})}")

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    def iter_paginated(
        self,
        path: str,
        key: str = "data",
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        limit: Optional[int] = None,
    ) -> Iterator[Any]:
        """Iterate through a paginated ``{data, total, limit, offset}`` API.

        Args:
            path: API endpoint path (may include existing query params).
            key: Key in the response containing the item list.
            params: Additional query params to send on every page.
            page_size: Number of items requested per page.
            limit: Maximum total items to yield across all pages.

        Yields:
            Individual items from paginated responses. Stops on errors,
            empty pages, or when ``total`` is reached.
        """
        offset = 0
        yielded = 0
        while True:
            qp: Dict[str, Any] = dict(params) if params else {}
            remaining = limit - yielded if limit else None
            qp["limit"] = min(page_size, remaining) if remaining else page_size
            qp["offset"] = offset
            sep = "&" if "?" in path else "?"
            resp = self._request("GET", f"{path}{sep}{urlencode(qp)}")
            if not isinstance(resp, dict) or "error" in resp:
                return
            items = resp.get(key)
            if not isinstance(items, list):
                for candidate in ("items", "results", "data"):
                    if isinstance(resp.get(candidate), list):
                        items = resp[candidate]
                        break
            if not items:
                return
            for item in items:
                yield item
                yielded += 1
                if limit and yielded >= limit:
                    return
            total = resp.get("total")
            if isinstance(total, int) and offset + len(items) >= total:
                return
            if len(items) < qp["limit"]:
                return
            offset += len(items)
