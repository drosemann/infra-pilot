"""Compatibility entry point for the VPS manager."""

import asyncio
from threading import Lock
from typing import Any, Dict

import docker

from vps_docker_support import (
    CPU_PERIOD,
    DEFAULT_HEALTH_URL,
    DEFAULT_PING_TARGET,
    DEFAULT_PORT_CHECK,
    DEFAULT_PROCESS,
    DENIED_ENV_VARS,
    MAX_SPAWN_ENV,
    MAX_SPAWN_PORTS,
    MIGRATION_TMP_DIR,
    PORT_MAX,
    PORT_MIN,
    RESTART_POLICY,
    SAFE_CONTAINER_PATTERN,
    SAFE_ENV_KEY_PATTERN,
    SAFE_HOST_PATTERN,
    SAFE_IMAGE_PATTERN,
    SAFE_PORT_KEY_PATTERN,
    SAFE_PROCESS_PATTERN,
    VPSConfig,
    _is_safe_host,
    _is_safe_process,
    _is_safe_url,
    _run_with_storage_opt_fallback,
    _storage_opt,
    _validate_image,
    _validate_resource_limits,
    _validate_spawn_config,
    _validate_spawn_env,
    _validate_spawn_ports,
    config,
    logger,
)
from vps_backup_snapshots import BackupsMixin
from vps_container_lifecycle import LifecycleMixin
from vps_health_monitoring import MonitoringMixin
from vps_instance_persistence import PersistenceMixin

__all__ = [
    "CPU_PERIOD",
    "DEFAULT_HEALTH_URL",
    "DEFAULT_PING_TARGET",
    "DEFAULT_PORT_CHECK",
    "DEFAULT_PROCESS",
    "DENIED_ENV_VARS",
    "MAX_SPAWN_ENV",
    "MAX_SPAWN_PORTS",
    "MIGRATION_TMP_DIR",
    "PORT_MAX",
    "PORT_MIN",
    "RESTART_POLICY",
    "SAFE_CONTAINER_PATTERN",
    "SAFE_ENV_KEY_PATTERN",
    "SAFE_HOST_PATTERN",
    "SAFE_IMAGE_PATTERN",
    "SAFE_PORT_KEY_PATTERN",
    "SAFE_PROCESS_PATTERN",
    "VPSConfig",
    "VPSManager",
    "_is_safe_host",
    "_is_safe_process",
    "_is_safe_url",
    "_run_with_storage_opt_fallback",
    "_storage_opt",
    "_validate_image",
    "_validate_resource_limits",
    "_validate_spawn_config",
    "_validate_spawn_env",
    "_validate_spawn_ports",
    "config",
    "logger",
]


class VPSManager(LifecycleMixin, BackupsMixin, MonitoringMixin, PersistenceMixin):
    """Manages Docker-based VPS containers with database persistence."""

    def __init__(self):
        self.client = docker.from_env()
        self.vps_instances: Dict[str, Any] = {}
        self.database_lock = Lock()
        # Several provisioning requests can complete at once.  Serialising
        # persistence prevents concurrent JSON writes from truncating the
        # fallback inventory while the database is unavailable.
        self._persistence_lock = asyncio.Lock()
        self._load_instances()
