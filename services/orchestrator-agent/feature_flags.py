"""Feature-flag consumer for the orchestrator agent.

The panel is the single source of truth; this client only reads the
``/api/feature-flags/evaluate`` endpoint, caches for ``poll_seconds``,
and falls back (in order) to: cache → FEATURE_FLAG_<KEY> env override →
code default. Evaluation never raises into caller code.
"""

import hashlib
import logging
import os
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def rollout_bucket(flag_key: str, subject_id: str) -> int:
    digest = hashlib.sha256(f"{flag_key}:{subject_id}".encode()).digest()
    return int.from_bytes(digest[:2], "big") % 100


class FeatureFlagClient:
    """Thin polling client with in-memory cache and safe defaults."""

    def __init__(
        self,
        panel_url: str = "",
        service_token: str = "",
        poll_seconds: int = 30,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.panel_url = (panel_url or os.getenv("FEATURE_FLAGS_PANEL_URL", "")).rstrip("/")
        self.service_token = service_token or os.getenv("FEATURE_FLAGS_SERVICE_TOKEN", "")
        try:
            self.poll_seconds = int(os.getenv("FEATURE_FLAGS_POLL_SECONDS", poll_seconds))
        except ValueError:
            self.poll_seconds = poll_seconds
        self.defaults = defaults or {}
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self.panel_url or self._thread:
            return
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _poll_loop(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            try:
                self.refresh()
            except Exception as exc:  # never crash the host on flag refresh
                logger.warning("feature-flags refresh failed: %s", exc)

    def refresh(self, org_id: str = "", project_id: str = "", user_id: str = "") -> Dict[str, Any]:
        import urllib.parse
        import urllib.request
        import json

        if not self.panel_url:
            return dict(self._cache)
        query = urllib.parse.urlencode(
            {k: v for k, v in {"orgId": org_id, "projectId": project_id, "userId": user_id}.items() if v}
        )
        req = urllib.request.Request(f"{self.panel_url}/api/feature-flags/evaluate?{query}")
        if self.service_token:
            req.add_header("Authorization", f"Bearer {self.service_token}")
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310 - panel URL is operator-configured
            data = json.loads(resp.read().decode())
        flags = data.get("flags", {})
        with self._lock:
            self._cache = flags
        return flags

    def is_enabled(
        self,
        key: str,
        org_id: str = "",
        project_id: str = "",
        user_id: str = "",
        default: bool = False,
    ) -> bool:
        """Return the flag value, honouring env override first, never raising."""
        try:
            env_key = "FEATURE_FLAG_" + "".join(c if c.isalnum() else "_" for c in key.upper())
            raw = os.getenv(env_key)
            if raw is not None:
                v = raw.strip().lower()
                if v in ("true", "1", "on"):
                    return True
                if v in ("false", "0", "off"):
                    return False
            with self._lock:
                cached = self._cache.get(key, None)
            if cached is not None:
                return bool(cached)
            if not self._cache:
                self.refresh(org_id=org_id, project_id=project_id, user_id=user_id)
                with self._lock:
                    cached = self._cache.get(key, None)
                if cached is not None:
                    return bool(cached)
            return self.defaults.get(key, default)
        except Exception as exc:
            logger.warning("feature-flag check failed for %s: %s", key, exc)
            return self.defaults.get(key, default)


client = FeatureFlagClient(defaults={"living_fleet": False, "discord_service_v2": False})


def is_enabled(key: str, default: bool = False, **subject: str) -> bool:
    """Module-level shortcut using the shared client."""
    return client.is_enabled(key, default=default, **subject)


def flag_gated(key: str, default: bool = False):
    """Decorator: run the function only when the flag is on, else return None."""
    def deco(fn):
        def wrapper(*args, **kwargs):
            if not is_enabled(key, default=default):
                logger.info("feature flag %s is off; skipping %s", key, fn.__name__)
                return None
            return fn(*args, **kwargs)
        return wrapper
    return deco
