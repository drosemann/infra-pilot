"""Secrets service wiring for the Orchestrator Agent.

Wraps a backend from ``secrets_manager.py`` selected by ``SECRETS_BACKEND``
('none' | 'vault' | 'aws' | 'azure'), adds an in-process TTL cache, the
``ref:secrets://<path>#<key>`` env convention, rotation, and a best-effort
Vault lease-renewal hook.

No method here ever logs or exposes secret values: logs carry path/key
names and outcomes only.
"""

import logging
import os
import re
import secrets as py_secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from config import config
from secrets_manager import (
    AWSSecretsManagerBackend,
    AzureKeyVaultBackend,
    SecretsBackend,
    VaultBackend,
)

logger = logging.getLogger(__name__)

SUPPORTED_BACKENDS: Tuple[str, ...] = ("none", "vault", "aws", "azure")

# Manifest env convention: ref:secrets://<path>#<key>. "no '#' inside
# path" follows from the allow-list below, which also applies to keys.
SECRET_REF_PREFIX = "ref:secrets://"
SECRET_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_/.-]{1,120}$")
SECRET_REF_PATTERN = re.compile(
    r"^ref:secrets://([A-Za-z0-9_/.-]{1,120})#([A-Za-z0-9_/.-]{1,120})$"
)


def _validate_secret_token(token: Any, label: str) -> None:
    """Enforce the path/key allow-list (A-Za-z0-9_/.- , 1..120 chars)."""
    if not isinstance(token, str) or not SECRET_TOKEN_PATTERN.fullmatch(token):
        raise ValueError(
            f"invalid {label}: expected 1..120 characters of [A-Za-z0-9_/.-]"
        )


def parse_secret_ref(value: Any) -> Tuple[str, str]:
    """Parse ``ref:secrets://<path>#<key>`` into (path, key).

    Raises ``ValueError`` for anything that is intended as a reference but
    is malformed, so callers can fail closed with a readable message.
    """
    if not isinstance(value, str) or not value.startswith(SECRET_REF_PREFIX):
        raise ValueError(
            f"not a secret ref: expected {SECRET_REF_PREFIX}<path>#<key>"
        )
    match = SECRET_REF_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(
            "malformed secret ref: expected ref:secrets://<path>#<key> "
            "with [A-Za-z0-9_/.-]{1,120} characters"
        )
    return match.group(1), match.group(2)


def is_secret_ref(value: Any) -> bool:
    """True when a manifest value is intentionally a secrets reference."""
    return isinstance(value, str) and value.startswith(SECRET_REF_PREFIX)


def _normalize_secret_payload(data: Any) -> Dict[str, Any]:
    """Bare strings are stored as {"value": <string>} so writes round-trip."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        return {"value": data}
    raise ValueError("secret data must be an object or a string")


class SecretsService:
    """Caching front-end for a secrets backend (secrets_manager.py).

    Reads are cached in-process for ``cache_ttl`` seconds and invalidated
    by set/rotate or by TTL expiry. Rotation writes a fresh random value
    on the backend and returns metadata only - the generated value is
    never part of any response or log call.
    """

    def __init__(
        self,
        backend: SecretsBackend,
        backend_name: str,
        cache_ttl: float = 60.0,
    ):
        self.backend = backend
        self.backend_name = backend_name
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, float] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _cache_key(path: str, key: Optional[str]) -> str:
        """Cache key is the bare path, or path#key for key-scoped reads."""
        return f"{path}#{key}" if key else path

    def get(self, path: str, key: Optional[str] = None) -> Any:
        """Resolve a secret through the TTL cache (backend errors propagate).

        ``None`` results are not cached, so a subsequent set/rotate
        becomes visible to the next read immediately.
        """
        _validate_secret_token(path, "secret path")
        if key is not None:
            _validate_secret_token(key, "secret key")
        cache_key = self._cache_key(path, key)
        if self.cache_ttl > 0:
            with self._lock:
                cached = self._cache.get(cache_key)
                if cached is not None and time.monotonic() < self._cache_expiry.get(
                    cache_key, 0.0
                ):
                    return cached
        resolved = self.backend.get_secret(path, key)
        if resolved is not None and self.cache_ttl > 0:
            with self._lock:
                self._cache[cache_key] = resolved
                self._cache_expiry[cache_key] = time.monotonic() + self.cache_ttl
        return resolved

    def set(self, path: str, data: Any) -> bool:
        """Write a secret (object or bare string) and invalidate the cache.

        Returns True on success, False when the backend reports a
        non-fatal write failure. Nothing sensitive is logged either way.
        """
        _validate_secret_token(path, "secret path")
        payload = _normalize_secret_payload(data)
        updated = bool(self.backend.set_secret(path, payload))
        if not updated:
            logger.error(
                "Secrets set failed for path=%s backend=%s", path, self.backend_name
            )
            return False
        self._invalidate_path(path)
        logger.info(
            "Secrets set succeeded for path=%s backend=%s", path, self.backend_name
        )
        return True

    def rotate(self, path: str) -> Dict[str, Any]:
        """Generate a fresh random value on the backend; metadata only.

        Raises ``RuntimeError`` when the write fails so API callers get a
        sanitized 500 without any backend error text echoing storage
        details. The generated value itself is discarded (stored on the
        backend only).
        """
        _validate_secret_token(path, "secret path")
        new_secret = py_secrets.token_hex(32)
        try:
            updated = bool(self.backend.set_secret(path, {"value": new_secret}))
        except Exception as exc:
            logger.error(
                "Secrets rotate failed for path=%s backend=%s (%s)",
                path,
                self.backend_name,
                type(exc).__name__,
            )
            raise RuntimeError("secret rotation failed on the secrets backend") from None
        if not updated:
            logger.error(
                "Secrets rotate failed for path=%s backend=%s", path, self.backend_name
            )
            raise RuntimeError("secret rotation failed on the secrets backend")
        self._invalidate_path(path)
        logger.info(
            "Secrets rotated for path=%s backend=%s", path, self.backend_name
        )
        return {"rotated": True, "path": path, "at": datetime.now(timezone.utc).isoformat()}

    def maybe_renew_lease(self) -> bool:
        """Best-effort Vault token/lease renewal (a poll hook, no threads).

        Only meaningful for Vault backends with a live hvac client. When
        the client exposes ``renew_self`` and renewal fails - for example
        because the token expired - backend connectivity is reset so the
        next operation re-authenticates (AppRole re-auth via the backend's
        own connect path) or fails closed. Never raises.
        """
        if self.backend_name != "vault":
            return False
        auth = getattr(getattr(self.backend, "client", None), "auth", None)
        token_renewer = getattr(getattr(auth, "token", None), "renew_self", None)
        if token_renewer is None:
            token_renewer = getattr(auth, "renew_self_token", None)
        if token_renewer is None:
            return False
        try:
            token_renewer()
            return True
        except Exception as exc:
            logger.info(
                "Secrets renewal failed (%s); triggering backend re-authentication",
                type(exc).__name__,
            )
            return self._reauthenticate()

    def _reauthenticate(self) -> bool:
        """Force the backend to reconnect/re-authenticate (defensive)."""
        try:
            if hasattr(self.backend, "_connected"):
                self.backend._connected = False
            reconnected = self.backend.check_connection()
        except Exception as exc:
            logger.info(
                "Secrets backend re-authentication failed (%s)", type(exc).__name__
            )
            return False
        if not reconnected:
            logger.info(
                "Secrets backend re-authentication unavailable; reads will fail closed"
            )
        return bool(reconnected)

    def _invalidate_path(self, path: str) -> None:
        """Drop cached entries for the path and its key-scoped variants."""
        prefix = f"{path}#"
        with self._lock:
            stale = [k for k in self._cache if k == path or k.startswith(prefix)]
            for cache_key in stale:
                self._cache.pop(cache_key, None)
                self._cache_expiry.pop(cache_key, None)


def _resolve_cache_ttl() -> float:
    """Cache TTL from SECRETS_CACHE_TTL (config fallback), defensible default."""
    raw = str(os.getenv("SECRETS_CACHE_TTL", "") or getattr(config, "secrets_cache_ttl", 60))
    try:
        ttl = float(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid SECRETS_CACHE_TTL=%r; using default 60s", raw)
        return 60.0
    if ttl < 0:
        logger.warning("Negative SECRETS_CACHE_TTL=%r; caching disabled", raw)
        return 0.0
    return ttl


def _build_backend(backend_name: str) -> SecretsBackend:
    """Instantiate the requested backend; raises when it is unusable."""
    if backend_name == "vault":
        backend = VaultBackend(
            kubernetes_auth=os.getenv("VAULT_KUBERNETES_AUTH", "").strip().lower()
            in ("1", "true", "yes", "on"),
            mount_point=os.getenv("VAULT_MOUNT_POINT", "secret"),
        )
        if not backend.check_connection():
            raise RuntimeError(
                "Vault is unreachable or not authenticated "
                "(check VAULT_ADDR/token/AppRole or the hvac optional dependency)"
            )
        return backend
    if backend_name == "aws":
        profile = os.getenv("AWS_PROFILE", "").strip()
        backend = AWSSecretsManagerBackend(
            region=os.getenv("AWS_REGION", "us-east-1"), profile=profile or None
        )
        if backend.client is None:
            raise RuntimeError(
                "AWS Secrets Manager client could not be initialised "
                "(check boto3 installation or AWS credentials)"
            )
        return backend
    if backend_name == "azure":
        backend = AzureKeyVaultBackend()
        if backend.client is None:
            raise RuntimeError(
                "Azure Key Vault client could not be initialised "
                "(check AZURE_KEY_VAULT_URL and credentials)"
            )
        return backend
    raise ValueError(f"Unknown secrets backend: {backend_name}")


def resolve_backend() -> Optional[SecretsService]:
    """Build the process SecretsService, or None when unused/broken.

    Selection: SECRETS_BACKEND ('vault' | 'aws' | 'azure'), falling back to
    ``config.secrets_backend`` (default 'none'). 'none', an unknown backend
    name, or a backend that cannot be proven usable (missing optional
    dependency, unreachable vault) disable the service so callers fail
    closed instead of pretending secrets are available.
    """
    backend_name = str(
        os.getenv("SECRETS_BACKEND", "")
        or getattr(config, "secrets_backend", "none")
        or "none"
    ).strip().lower()
    if backend_name not in SUPPORTED_BACKENDS:
        logger.warning(
            "Unsupported SECRETS_BACKEND=%r; secrets service disabled", backend_name
        )
        return None
    if backend_name == "none":
        return None
    try:
        backend = _build_backend(backend_name)
    except Exception as exc:
        logger.error(
            "Failed to initialise %s secrets backend (%s); secrets service disabled",
            backend_name,
            type(exc).__name__,
        )
        return None
    service = SecretsService(
        backend=backend,
        backend_name=backend_name,
        cache_ttl=_resolve_cache_ttl(),
    )
    logger.info(
        "Secrets service enabled (backend=%s, cache_ttl=%.0fs)",
        backend_name,
        service.cache_ttl,
    )
    return service


def resolve_secrets_service() -> Optional[SecretsService]:
    """Alias for ``resolve_backend`` (module wiring in webhook_server)."""
    return resolve_backend()
