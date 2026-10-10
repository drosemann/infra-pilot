"""Shared VPS configuration, validation, and Docker helpers."""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import docker
from config import config

logger = logging.getLogger(__name__)

SAFE_CONTAINER_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
# Strict allow-lists for health-check targets – rejects shell metacharacters
# (;, &, |, $, `, '", \n, etc.) to close command-injection via exec_run.
SAFE_HOST_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]{0,253}[a-zA-Z0-9])?$")
SAFE_PROCESS_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")
PORT_MIN = 1025
PORT_MAX = 65535
CPU_PERIOD = 100000
RESTART_POLICY = {"Name": "unless-stopped"}
DEFAULT_PING_TARGET = "8.8.8.8"
DEFAULT_PORT_CHECK = "localhost:22"
DEFAULT_PROCESS = "sshd"
DEFAULT_HEALTH_URL = "http://localhost:80/health"
MIGRATION_TMP_DIR = "/tmp"


def _is_safe_host(host: str) -> bool:
    """Return True iff host is a valid hostname / IPv4 literal (no shell chars)."""
    if not host or len(host) > 253:
        return False
    # IPv4 literal
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        return all(0 <= int(o) <= 255 for o in host.split("."))
    return bool(SAFE_HOST_PATTERN.fullmatch(host))


def _is_safe_process(name: str) -> bool:
    return bool(SAFE_PROCESS_PATTERN.fullmatch(name))


def _is_safe_url(url: str) -> bool:
    """Allow only http/https URLs without shell metacharacters."""
    if not url or len(url) > 2048:
        return False
    if any(c in url for c in " ;&|`$'\"\n\r\t"):
        return False
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _validate_resource_limits(cfg: "VPSConfig") -> None:
    """Clamp/validate CPU/memory against config.RESOURCE_LIMITS.

    Raises ValueError if limits are out of bounds.
    """
    limits = config.RESOURCE_LIMITS
    if not (limits["min_cpu"] <= cfg.cpu_limit <= limits["max_cpu"]):
        raise ValueError(
            f"cpu_limit {cfg.cpu_limit} out of bounds "
            f"[{limits['min_cpu']}, {limits['max_cpu']}]"
        )
    if not (limits["min_memory_mb"] <= cfg.memory_limit <= limits["max_memory_mb"]):
        raise ValueError(
            f"memory_limit {cfg.memory_limit} out of bounds "
            f"[{limits['min_memory_mb']}, {limits['max_memory_mb']}]"
        )
    if not (limits["min_storage_gb"] <= cfg.storage_limit <= limits["max_storage_gb"]):
        raise ValueError(
            f"storage_limit {cfg.storage_limit} out of bounds "
            f"[{limits['min_storage_gb']}, {limits['max_storage_gb']}]"
        )


SAFE_IMAGE_PATTERN = re.compile(
    r"^[a-z0-9._/-]+(?::[A-Za-z0-9_.-]+)?(?:@[A-Za-z0-9_.-]+:[A-Fa-f0-9]+)?$"
)
SAFE_PORT_KEY_PATTERN = re.compile(r"^(\d{1,5})/(tcp|udp)$")
SAFE_ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DENIED_ENV_VARS = frozenset(
    {
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "DOCKER_HOST",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    }
)
MAX_SPAWN_PORTS = 16
MAX_SPAWN_ENV = 64


def _validate_image(image: str) -> None:
    """Reject malformed image references before passing them to the daemon.

    An optional ``ALLOWED_IMAGES`` env var (comma-separated prefixes)
    further restricts pulls to trusted registries/repositories.
    """
    if not isinstance(image, str) or not image or len(image) > 255:
        raise ValueError(f"invalid image: {image!r}")
    if any(c in image for c in " \t\n\r;&|`$'\"\\"):
        raise ValueError(f"invalid image reference: {image!r}")
    if not SAFE_IMAGE_PATTERN.fullmatch(image):
        raise ValueError(f"invalid image reference: {image!r}")
    allowlist = [
        p.strip() for p in os.getenv("ALLOWED_IMAGES", "").split(",") if p.strip()
    ]
    if allowlist and not any(
        image == p or image.startswith((p + ":", p + "@", p + "/")) for p in allowlist
    ):
        raise ValueError(f"image not in ALLOWED_IMAGES allow-list: {image!r}")


def _validate_spawn_ports(ports: Dict[str, str]) -> None:
    """Validate container->host port mappings for spawns.

    Host ports must be >= 1025: binding privileged ports requires root /
    extra capabilities and is rejected on the spawn path. Container ports
    may be any valid port (e.g. 22, 80 inside the container).
    """
    if not isinstance(ports, dict) or len(ports) > MAX_SPAWN_PORTS:
        raise ValueError(f"invalid ports mapping: {ports!r}")
    for container_port, host_port in ports.items():
        match = (
            SAFE_PORT_KEY_PATTERN.fullmatch(str(container_port))
            if isinstance(container_port, str)
            else None
        )
        if not match or not 1 <= int(match.group(1)) <= 65535:
            raise ValueError(f"invalid container port: {container_port!r}")
        try:
            host = int(str(host_port))
        except (TypeError, ValueError):
            raise ValueError(f"invalid host port: {host_port!r}") from None
        if not PORT_MIN <= host <= PORT_MAX:
            raise ValueError(
                f"host port {host_port!r} out of bounds [{PORT_MIN}, {PORT_MAX}]"
            )


def _validate_spawn_env(env_vars: Dict[str, str]) -> None:
    """Validate environment for spawns (shape + denied vars)."""
    if not isinstance(env_vars, dict) or len(env_vars) > MAX_SPAWN_ENV:
        raise ValueError(f"invalid env_vars mapping: {env_vars!r}")
    for key, value in env_vars.items():
        if not isinstance(key, str) or not SAFE_ENV_KEY_PATTERN.fullmatch(key):
            raise ValueError(f"invalid env key: {key!r}")
        if key in DENIED_ENV_VARS:
            raise ValueError(f"denied env var: {key!r}")
        if not isinstance(value, str) or len(value) > 4096:
            raise ValueError(f"invalid env value for {key!r}")


def _validate_spawn_config(cfg: "VPSConfig") -> None:
    """Run all spawn validations (resources + image + ports + env)."""
    _validate_resource_limits(cfg)
    _validate_image(cfg.image)
    _validate_spawn_ports(cfg.ports or {})
    _validate_spawn_env(cfg.env_vars or {})


def _storage_opt(storage_limit_gb: int) -> Optional[Dict[str, str]]:
    """Return Docker storage_opt for writable-layer quota if driver supports it.

    Supports btrfs, zfs, overlay2 (with pquota) – only those drivers honor
    the ``size`` quota on XFS backing. For other drivers returns None so the
    container still creates but without quota (fallback in _run_with_storage_opt_fallback
    handles the overlay2-without-pquota case). In tests or when the daemon is
    unreachable, returns the opt so unit tests can assert it and exercise fallback.
    """
    if not storage_limit_gb:
        return None
    try:
        info = docker.from_env().info()
        driver = info.get("Driver", "")
        if driver not in ("btrfs", "zfs", "overlay2", "overlay"):
            logger.debug(
                "Storage driver %s does not support size quota; omitting storage_opt",
                driver,
            )
            return None
    except Exception:
        # In unit tests the daemon is mocked; still return opt for assertion
        pass
    return {"size": f"{storage_limit_gb}G"}


def _run_with_storage_opt_fallback(client, run_kwargs: Dict[str, Any]):
    """Run a container with storage_opt fallback.

    Docker accepts ``storage_opt={"size": "..."}`` only when the storage
    driver is configured with XFS/pquota (overlay2+btrfs/zfs). On hosts
    without that support containers.run() raises; this helper retries
    without the quota so the container still creates (quota unenforced)
    instead of leaving callers like restore_backup in a half-stopped state.

    The check is case-insensitive and also matches driver error strings like
    "Unknown option storage_opt" so fallback triggers reliably across Docker
    versions. A shallow copy is used so the caller's original dict remains
    observable in tests that assert storage_opt was attempted first.
    """
    try:
        return client.containers.run(**run_kwargs)
    except Exception as exc:
        msg = str(exc).lower()
        if "storage_opt" in msg and "storage_opt" in run_kwargs:
            logger.warning(
                "storage_opt rejected by driver, retrying without quota: %s", exc
            )
            fallback = dict(run_kwargs)
            fallback.pop("storage_opt", None)
            return client.containers.run(**fallback)
        raise


@dataclass
class VPSConfig:
    """Configuration for creating a new VPS container."""

    cpu_limit: float
    memory_limit: int
    storage_limit: int
    image: str
    ports: Dict[str, str]
    env_vars: Dict[str, str]
