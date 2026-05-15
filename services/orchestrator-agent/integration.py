import logging
import os
from typing import Dict, Any, Optional

import requests

# Configuration
INTEGRATION_SERVICE_URL = os.getenv("INTEGRATION_SERVICE_URL", "http://localhost:9000")
REQUEST_TIMEOUT = 5

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _send_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Send HTTP request to integration service.
    
    Args:
        method: HTTP method ("GET" or "POST")
        endpoint: API endpoint path
        data: JSON payload for POST requests
        
    Returns:
        Tuple of (success: bool, response_data: Optional[Dict])
    """
    try:
        url = f"{INTEGRATION_SERVICE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
        else:
            return False, None

        # Accept both 200 (OK) and 201 (Created)
        if response.status_code in (200, 201):
            return True, response.json()
        
        logger.warning(f"Request failed with status {response.status_code}: {response.text}")
        return False, None

    except requests.Timeout:
        logger.warning(f"Request timeout for {endpoint}")
        return False, None
    except requests.RequestException as e:
        logger.warning(f"Request error for {endpoint}: {e}")
        return False, None
    except ValueError as e:
        logger.warning(f"Failed to parse response JSON: {e}")
        return False, None


async def notify_integration(event_type: str, data: Dict[str, Any]) -> bool:
    """Notify integration service of an event."""
    payload = {
        "event_type": event_type,
        "server_name": data.get("server_name"),
        "details": data,
    }
    success, _ = _send_request("POST", "/api/notifications/server-event", payload)
    return success


async def notify_server_created(server_id: str, server_name: str) -> bool:
    """Notify that a server was created."""
    data = {
        "server_id": server_id,
        "server_name": server_name,
        "service": "orchestrator",
    }
    return await notify_integration("server_created", data)


async def notify_server_started(server_id: str, server_name: str) -> bool:
    """Notify that a server was started."""
    data = {
        "server_id": server_id,
        "server_name": server_name,
        "service": "orchestrator",
    }
    return await notify_integration("server_started", data)


async def notify_server_stopped(server_id: str, server_name: str) -> bool:
    """Notify that a server was stopped."""
    data = {
        "server_id": server_id,
        "server_name": server_name,
        "service": "orchestrator",
    }
    return await notify_integration("server_stopped", data)


async def notify_server_deleted(server_id: str, server_name: str) -> bool:
    """Notify that a server was deleted."""
    data = {
        "server_id": server_id,
        "server_name": server_name,
        "service": "orchestrator",
    }
    return await notify_integration("server_deleted", data)


async def sync_user_to_integration(
    user_id: str, email: str, username: str
) -> Dict[str, Any]:
    """Synchronize user to integration service."""
    payload = {
        "email": email,
        "username": username,
        "discord_id": user_id,
    }
    success, response = _send_request("POST", "/api/users", payload)
    return response or {}


async def get_unified_metrics() -> Dict[str, Any]:
    """Retrieve unified metrics from integration service."""
    success, response = _send_request("GET", "/api/metrics/dashboard")
    return response or {}


async def broadcast_notification(message: str, title: str = "Notification") -> bool:
    """Broadcast a notification to all users."""
    payload = {
        "content": message,
        "title": title,
    }
    success, _ = _send_request("POST", "/api/notifications", payload)
    return success


if __name__ == "__main__":
    import asyncio

    async def test():
        result = await notify_server_created("test-123", "test-server")
        print("Server created notification:", result)

        metrics = await get_unified_metrics()
        print("Metrics retrieved:", bool(metrics))

    asyncio.run(test())
