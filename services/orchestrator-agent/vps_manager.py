"""VPS (container) manager for the Orchestrator Agent."""

import asyncio
import json
import logging
import os
import random
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
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


class VPSManager:
    """Manages Docker-based VPS containers with database persistence."""

    def __init__(self):
        self.client = docker.from_env()
        self.vps_instances: Dict[str, Any] = {}
        self.database_lock = Lock()
        self._load_instances()

    def _load_instances(self):
        """Load VPS instance metadata from PostgreSQL (primary) or JSON file (fallback)."""
        loaded = False
        try:
            conn = self._get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT container_id, user_id, container_name, ssh_command, "
                    "       status, metadata, created_at "
                    "FROM vps_containers"
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                for row in rows:
                    cid = row[0]
                    self.vps_instances[cid] = {
                        "container_id": cid,
                        "user_id": row[1],
                        "container_name": row[2],
                        "ssh_command": row[3],
                        "status": row[4] or "running",
                        "created_at": row[6].isoformat() if row[6] else None,
                        "config": {},
                    }
                    metadata = row[5] or {}
                    if isinstance(metadata, dict):
                        self.vps_instances[cid].update(metadata)
                loaded = True
        except Exception as exc:
            logger.warning("DB load failed, trying JSON fallback: %s", exc)
        if not loaded:
            try:
                if os.path.exists(config.VPS_INSTANCES_FILE):
                    with open(config.VPS_INSTANCES_FILE, "r") as f:
                        self.vps_instances = json.load(f)
            except Exception as exc:
                logger.error("Error loading VPS instances from JSON: %s", exc)
                self.vps_instances = {}

    async def save_instances(self):
        """Persist VPS instance metadata to PostgreSQL (primary) and JSON file (fallback)."""
        try:
            from db import get_pool

            pool = await get_pool()
            async with pool.acquire() as conn:
                for cid, info in self.vps_instances.items():
                    metadata = {
                        k: v
                        for k, v in info.items()
                        if k
                        not in (
                            "container_id",
                            "user_id",
                            "container_name",
                            "ssh_command",
                            "status",
                            "created_at",
                        )
                    }
                    await conn.execute(
                        "INSERT INTO vps_containers "
                        "(container_id, user_id, container_name, ssh_command, status, metadata) "
                        "VALUES ($1, $2, $3, $4, $5, $6::jsonb) "
                        "ON CONFLICT (container_id) DO UPDATE SET "
                        "  user_id = EXCLUDED.user_id, "
                        "  container_name = EXCLUDED.container_name, "
                        "  ssh_command = EXCLUDED.ssh_command, "
                        "  status = EXCLUDED.status, "
                        "  metadata = COALESCE(vps_containers.metadata, '{}'::jsonb) || EXCLUDED.metadata",
                        cid,
                        info.get("user_id", ""),
                        info.get("container_name", cid[:12]),
                        info.get("ssh_command", ""),
                        info.get("status", "running"),
                        json.dumps(metadata),
                    )
        except Exception as exc:
            logger.warning("DB save failed, falling back to JSON: %s", exc)
        # Always write JSON fallback as well
        try:
            content = json.dumps(self.vps_instances, indent=2)
            async with aiofiles.open(config.VPS_INSTANCES_FILE, "w") as f:
                await f.write(content)
        except Exception as exc:
            logger.error("Error saving VPS instances to JSON: %s", exc)

    def is_safe_name(self, name: str) -> bool:
        """Check if a container name is safe (matches allowed pattern).

        Args:
            name: The container name to validate.

        Returns:
            ``True`` if the name is safe.
        """
        return bool(SAFE_CONTAINER_PATTERN.fullmatch(name))

    def generate_random_port(self) -> int:
        """Generate a random port number in the ephemeral range.

        Returns:
            A random integer between 1025 and 65535.
        """
        return random.randint(PORT_MIN, PORT_MAX)

    def add_to_database(self, user_id: str, container_id: str, ssh_command: str):
        """Insert a VPS container record into the database.

        Args:
            user_id: The Discord user ID.
            container_id: The Docker container ID.
            ssh_command: The SSH command string for accessing the container.
        """
        with self.database_lock:
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO vps_containers "
                    "(container_id, user_id, container_name, ssh_command) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (container_id) DO NOTHING",
                    (container_id, user_id, container_id[:12], ssh_command),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as exc:
                logger.error("Error adding to database: %s", exc)

    def remove_from_database(self, container_id: str):
        """Remove a VPS container record from the database.

        Args:
            container_id: The Docker container ID.
        """
        with self.database_lock:
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vps_containers WHERE container_id = %s",
                    (container_id,),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as exc:
                logger.error("Error removing from database: %s", exc)

    def get_user_servers(self, user_id: str) -> List[Tuple]:
        """Retrieve all VPS containers belonging to a user.

        Args:
            user_id: The Discord user ID.

        Returns:
            A list of``(container_id, container_name, ssh_command)`` tuples.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT container_id, container_name, ssh_command "
                "FROM vps_containers WHERE user_id = %s",
                (user_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Exception:
            return []

    def count_user_servers(self, user_id: str) -> int:
        """Count how many VPS containers a user owns.

        Args:
            user_id: The Discord user ID.

        Returns:
            The server count.
        """
        return len(self.get_user_servers(user_id))

    def get_container_id_from_database(
        self, user_id: str, container_name: str
    ) -> Optional[str]:
        """Resolve a container name or partial ID to a full container ID.

        Args:
            user_id: The Discord user ID.
            container_name: Container name, full ID, or partial ID prefix.

        Returns:
            The matching container ID, or ``None``.
        """
        servers = self.get_user_servers(user_id)
        for cid, name, _ in servers:
            if (
                name == container_name
                or cid == container_name
                or cid.startswith(container_name)
            ):
                return cid
        return None

    def get_ssh_command_from_database(self, container_id: str) -> Optional[str]:
        """Retrieve the SSH command for a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            The SSH command string, or ``None``.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ssh_command FROM vps_containers " "WHERE container_id = %s",
                (container_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def _get_db_connection(self):
        """Create a PostgreSQL database connection using config settings.

        Returns:
            A ``psycopg2.connection`` instance.
        """
        from db import get_sync_connection

        return get_sync_connection()

    async def create_vps(self, user_id: str, cfg: VPSConfig) -> Optional[str]:
        """Create a new Docker container as a VPS.

        Args:
            user_id: The Discord user ID.
            cfg: The VPS configuration.

        Returns:
            The container ID on success, or ``None``.
        """
        try:
            _validate_resource_limits(cfg)
            run_kwargs: Dict[str, Any] = dict(
                image=cfg.image,
                detach=True,
                cpu_period=CPU_PERIOD,
                cpu_quota=int(cfg.cpu_limit * CPU_PERIOD),
                mem_limit=f"{cfg.memory_limit}m",
                ports=cfg.ports,
                environment=cfg.env_vars,
                restart_policy=RESTART_POLICY,
            )
            storage_opt = _storage_opt(cfg.storage_limit)
            if storage_opt:
                run_kwargs["storage_opt"] = storage_opt
            container = _run_with_storage_opt_fallback(self.client, run_kwargs)

            instance_info = {
                "container_id": container.id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_billing": datetime.now().isoformat(),
                "config": {
                    "cpu_limit": cfg.cpu_limit,
                    "memory_limit": cfg.memory_limit,
                    "storage_limit": cfg.storage_limit,
                    "image": cfg.image,
                    "ports": cfg.ports,
                },
                "status": "running",
                "host": (os.uname().nodename if hasattr(os, "uname") else "localhost"),
            }

            self.vps_instances[container.id] = instance_info
            await self.save_instances()
            return container.id
        except Exception as exc:
            logger.error("Error creating VPS: %s", exc)
            return None

    async def delete_vps(self, container_id: str) -> bool:
        """Delete (stop and remove) a VPS container.

        Args:
            container_id: The Docker container ID.

        Returns:
            ``True`` on success.
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            self.vps_instances.pop(container_id, None)
            await self.save_instances()
            self.remove_from_database(container_id)
            return True
        except Exception as exc:
            logger.error("Error deleting VPS: %s", exc)
            return False

    async def start_vps(self, container_id: str) -> bool:
        """Start a stopped VPS container.

        Args:
            container_id: The Docker container ID.

        Returns:
            ``True`` on success.
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()
            await self._update_status(container_id, "running")
            return True
        except Exception as exc:
            logger.error("Error starting VPS: %s", exc)
            return False

    async def stop_vps(self, container_id: str) -> bool:
        """Stop a running VPS container.

        Args:
            container_id: The Docker container ID.

        Returns:
            ``True`` on success.
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            await self._update_status(container_id, "stopped")
            return True
        except Exception as exc:
            logger.error("Error stopping VPS: %s", exc)
            return False

    async def restart_vps(self, container_id: str) -> bool:
        """Restart a VPS container.

        Args:
            container_id: The Docker container ID.

        Returns:
            ``True`` on success.
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            await self._update_status(container_id, "running")
            return True
        except Exception as exc:
            logger.error("Error restarting VPS: %s", exc)
            return False

    async def _update_status(self, container_id: str, status: str):
        """Update and persist the VPS instance status.

        Args:
            container_id: The Docker container ID.
            status: The new status string.
        """
        if container_id in self.vps_instances:
            self.vps_instances[container_id]["status"] = status
            await self.save_instances()

    async def get_vps_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve live CPU, memory, and network stats for a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A dict with ``status``, ``cpu_usage``, ``memory_usage``, and
            ``network`` keys, or ``None`` on failure.
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0

            networks = stats.get("networks", {})
            eth0 = networks.get("eth0", {})

            return {
                "status": container.status,
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory_percent, 2),
                "network": {
                    "rx_bytes": eth0.get("rx_bytes", 0),
                    "tx_bytes": eth0.get("tx_bytes", 0),
                },
            }
        except Exception as exc:
            logger.error("Error getting VPS stats: %s", exc)
            return None

    async def list_user_instances(self, user_id: str) -> List[Dict]:
        """List all VPS instances for a user with live stats.

        Args:
            user_id: The Discord user ID.

        Returns:
            A list of dicts with ``container_id``, ``info``, and ``stats``.
        """
        results = []
        for cid, info in self.vps_instances.items():
            if info["user_id"] == user_id:
                stats = await self.get_vps_stats(cid)
                results.append({"container_id": cid, "info": info, "stats": stats})
        return results

    async def update_vps_config(self, container_id: str, cfg: VPSConfig) -> bool:
        """Update a running VPS container's resource limits.

        Args:
            container_id: The Docker container ID.
            cfg: The new VPS configuration.

        Returns:
            ``True`` on success.
        """
        try:
            _validate_resource_limits(cfg)
            # Storage quota cannot be resized via container.update (writable layer size is immutable).
            # We update CPU/memory via container.update and persist the new storage_limit in metadata,
            # but the writable-layer quota will only be enforced after container recreation (e.g. via
            # clone/restore). Log that the live quota is not resized.
            if container_id in self.vps_instances:
                old_storage = (
                    self.vps_instances[container_id]
                    .get("config", {})
                    .get("storage_limit")
                )
                if old_storage is not None and cfg.storage_limit != old_storage:
                    logger.warning(
                        "Storage_limit change %s->%s for %s: quota requires recreation, live layer not resized (metadata updated)",
                        old_storage,
                        cfg.storage_limit,
                        container_id,
                    )
            container = self.client.containers.get(container_id)
            container.stop()
            container.update(
                cpu_period=CPU_PERIOD,
                cpu_quota=int(cfg.cpu_limit * CPU_PERIOD),
                mem_limit=f"{cfg.memory_limit}m",
            )
            if container_id in self.vps_instances:
                self.vps_instances[container_id]["config"].update(
                    {
                        "cpu_limit": cfg.cpu_limit,
                        "memory_limit": cfg.memory_limit,
                        "storage_limit": cfg.storage_limit,
                    }
                )
                await self.save_instances()
            container.start()
            return True
        except Exception as exc:
            logger.error("Error updating VPS config: %s", exc)
            return False

    async def create_backup(
        self, container_id: str, retention_type: str = "daily"
    ) -> Optional[str]:
        """Create a backup (Docker image commit) of a VPS.

        Args:
            container_id: The Docker container ID.
            retention_type: Retention category (daily, weekly, monthly).

        Returns:
            The image ID on success, or ``None``.
        """
        try:
            container = self.client.containers.get(container_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{container.name}_backup_{timestamp}"
            image = container.commit(repository=backup_name)

            if container_id in self.vps_instances:
                self.vps_instances[container_id].setdefault("backups", [])
                self.vps_instances[container_id]["backups"].append(
                    {
                        "image_id": image.id,
                        "created_at": timestamp,
                        "name": backup_name,
                        "retention_type": retention_type,
                    }
                )
                await self.save_instances()

            self._record_backup(container_id, image.id, backup_name, retention_type)
            self._apply_retention_policy(container_id)
            return image.id
        except Exception as exc:
            logger.error("Error creating backup: %s", exc)
            return None

    def _record_backup(
        self,
        container_id: str,
        image_id: str,
        name: str,
        retention_type: str,
    ):
        """Record a backup entry in the database.

        Args:
            container_id: The Docker container ID.
            image_id: The committed Docker image ID.
            name: The backup name.
            retention_type: Retention category.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO backup_rotation "
                "(container_id, image_id, name, retention_type) "
                "VALUES (%s, %s, %s, %s)",
                (container_id, image_id, name, retention_type),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as exc:
            logger.error("Error recording backup: %s", exc)

    def _apply_retention_policy(self, container_id: str):
        """Remove old backups exceeding the retention limit per category.

        Args:
            container_id: The Docker container ID.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for retention_type, max_count in config.BACKUP_RETENTION.items():
                cursor.execute(
                    "SELECT id, created_at FROM backup_rotation "
                    "WHERE container_id = %s AND retention_type = %s "
                    "ORDER BY created_at DESC",
                    (container_id, retention_type),
                )
                backups = cursor.fetchall()
                if len(backups) > max_count:
                    to_delete = backups[max_count:]
                    for b in to_delete:
                        cursor.execute(
                            "DELETE FROM backup_rotation WHERE id = %s",
                            (b["id"],),
                        )

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as exc:
            logger.error("Error applying retention policy: %s", exc)

    async def list_backups(self, container_id: str) -> List[Dict]:
        """List all backups for a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A list of backup dicts from the database, falling back to
            in-memory metadata.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM backup_rotation WHERE container_id = %s "
                "ORDER BY created_at DESC",
                (container_id,),
            )
            backups = cursor.fetchall()
            cursor.close()
            conn.close()
            return backups
        except Exception as exc:
            logger.error("Error listing backups: %s", exc)
            return self.vps_instances.get(container_id, {}).get("backups", [])

    async def restore_backup(self, container_id: str, backup_image_id: str) -> bool:
        """Restore a container from a backup image.

        Args:
            container_id: The current container ID (will be replaced).
            backup_image_id: The Docker image ID to restore from.

        Returns:
            ``True`` on success.

        Note: stop is performed before the new container is created; storage_opt
        fallback ensures the replacement still succeeds on hosts without XFS pquota.
        If creation ultimately fails, the caller sees False and the stopped
        container remains for manual recovery.
        """
        try:
            await self.stop_vps(container_id)
            instance_info = self.vps_instances.get(container_id)
            if not instance_info:
                return False

            cfg = instance_info["config"]
            restore_kwargs: Dict[str, Any] = dict(
                image=backup_image_id,
                detach=True,
                cpu_period=CPU_PERIOD,
                cpu_quota=int(cfg["cpu_limit"] * CPU_PERIOD),
                mem_limit=f"{cfg['memory_limit']}m",
                ports=cfg["ports"],
                restart_policy=RESTART_POLICY,
            )
            so = _storage_opt(int(cfg.get("storage_limit", 0) or 0))
            if so:
                restore_kwargs["storage_opt"] = so
            # Use shared fallback so XFS/pquota absence doesn't leave VPS stopped without replacement
            container = _run_with_storage_opt_fallback(self.client, restore_kwargs)

            instance_info["container_id"] = container.id
            self.vps_instances[container.id] = instance_info
            self.vps_instances.pop(container_id, None)
            await self.save_instances()
            return True
        except Exception as exc:
            logger.error("Error restoring backup: %s", exc)
            return False

    async def create_snapshot(
        self, container_id: str, name: Optional[str] = None
    ) -> Optional[str]:
        """Create a named snapshot of a container.

        Args:
            container_id: The Docker container ID.
            name: Optional snapshot name (auto-generated if not given).

        Returns:
            The image ID on success, or ``None``.
        """
        try:
            container = self.client.containers.get(container_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_name = name or f"{container.name}_snapshot_{timestamp}"
            image = container.commit(repository=snapshot_name)

            if container_id in self.vps_instances:
                self.vps_instances[container_id].setdefault("snapshots", [])
                self.vps_instances[container_id]["snapshots"].append(
                    {
                        "image_id": image.id,
                        "created_at": timestamp,
                        "name": snapshot_name,
                    }
                )
                await self.save_instances()

            self._record_snapshot(container_id, snapshot_name, image.id)
            return image.id
        except Exception as exc:
            logger.error("Error creating snapshot: %s", exc)
            return None

    def _record_snapshot(self, container_id: str, name: str, image_id: str):
        """Record a snapshot entry in the database.

        Args:
            container_id: The Docker container ID.
            name: The snapshot name.
            image_id: The committed Docker image ID.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO snapshots "
                "(container_id, name, image_id) VALUES (%s, %s, %s)",
                (container_id, name, image_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as exc:
            logger.error("Error recording snapshot: %s", exc)

    async def list_snapshots(self, container_id: str) -> List[Dict]:
        """List all snapshots for a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A list of snapshot dicts from the database.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM snapshots WHERE container_id = %s "
                "ORDER BY created_at DESC",
                (container_id,),
            )
            snapshots = cursor.fetchall()
            cursor.close()
            conn.close()
            return snapshots
        except Exception as exc:
            logger.error("Error listing snapshots: %s", exc)
            return self.vps_instances.get(container_id, {}).get("snapshots", [])

    async def restore_snapshot(self, container_id: str, snapshot_image_id: str) -> bool:
        """Restore a container from a snapshot image.

        Args:
            container_id: The Docker container ID.
            snapshot_image_id: The snapshot image ID.

        Returns:
            ``True`` on success.
        """
        return await self.restore_backup(container_id, snapshot_image_id)

    async def clone_vps(self, container_id: str, new_name: str) -> Optional[str]:
        """Clone a VPS container into a new container.

        Args:
            container_id: The source container ID.
            new_name: Name for the cloned container.

        Returns:
            The new container ID on success, or ``None``. Storage quota is
            propagated via _storage_opt with fallback so cloning succeeds even
            when the host's overlay2 lacks pquota.
        """
        try:
            container = self.client.containers.get(container_id)
            image = container.commit(repository=f"{new_name}_clone")

            instance_info = self.vps_instances.get(container_id)
            if not instance_info:
                return None

            cfg = instance_info["config"]
            clone_kwargs: Dict[str, Any] = dict(
                image=image.id,
                detach=True,
                cpu_period=CPU_PERIOD,
                cpu_quota=int(cfg["cpu_limit"] * CPU_PERIOD),
                mem_limit=f"{cfg['memory_limit']}m",
                ports=cfg["ports"],
                restart_policy=RESTART_POLICY,
            )
            so = _storage_opt(int(cfg.get("storage_limit", 0) or 0))
            if so:
                clone_kwargs["storage_opt"] = so
            new_container = _run_with_storage_opt_fallback(self.client, clone_kwargs)

            new_info = dict(instance_info)
            new_info["container_id"] = new_container.id
            new_info["created_at"] = datetime.now().isoformat()
            new_info["cloned_from"] = container_id
            self.vps_instances[new_container.id] = new_info
            await self.save_instances()
            return new_container.id
        except Exception as exc:
            logger.error("Error cloning VPS: %s", exc)
            return None

    async def migrate_vps(self, container_id: str, target_host: str) -> bool:
        """Migrate a VPS container to another host by saving its image.

        Args:
            container_id: The Docker container ID.
            target_host: The target hostname (for logging purposes).

        Returns:
            ``True`` on success.
        """
        try:
            logger.info("Migrating container %s to %s", container_id, target_host)
            container = self.client.containers.get(container_id)
            image = container.commit(repository=f"migration_{container_id[:12]}")

            save_path = os.path.join(MIGRATION_TMP_DIR, f"{container_id}_migration.tar")
            with open(save_path, "wb") as f:
                for chunk in self.client.images.get(image.id).save():
                    f.write(chunk)

            logger.info(
                "Container %s saved for migration to %s",
                container_id,
                target_host,
            )
            return True
        except Exception as exc:
            logger.error("Error migrating VPS: %s", exc)
            return False

    async def run_health_check(
        self,
        container_id: str,
        check_type: str,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a health check against a container.

        Supported check types: ``ping``, ``port``, ``process``, ``api``.
        All user-controlled ``target`` values are strictly validated against
        allow-lists before any container exec to prevent command injection.
        """
        result: Dict[str, Any] = {
            "status": "unknown",
            "response_time_ms": 0,
            "error": None,
        }
        start = datetime.now()

        try:
            container = self.client.containers.get(container_id)

            if check_type == "ping":
                ping_target = target or DEFAULT_PING_TARGET
                if not _is_safe_host(ping_target):
                    result["status"] = "failed"
                    result["error"] = f"Invalid ping target: {ping_target!r}"
                else:
                    success, _ = self._exec_in_container(
                        container, ["ping", "-c", "1", "-W", "2", ping_target]
                    )
                    result["status"] = "passed" if success else "failed"
            elif check_type == "port":
                raw = target or DEFAULT_PORT_CHECK
                try:
                    host, port_str = raw.split(":", 1)
                except ValueError:
                    result["status"] = "failed"
                    result["error"] = (
                        f"Invalid port target: {raw!r} (expected host:port)"
                    )
                    host = port_str = None  # type: ignore
                if host is not None:
                    if not _is_safe_host(host):
                        result["status"] = "failed"
                        result["error"] = f"Invalid port host: {host!r}"
                    elif not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
                        result["status"] = "failed"
                        result["error"] = f"Invalid port number: {port_str!r}"
                    else:
                        # exec_run with list avoids shell; bash tcp check still needs a shell
                        # but host/port are now strictly validated so no injection is possible.
                        success, _ = self._exec_in_container(
                            container,
                            [
                                "timeout",
                                "2",
                                "bash",
                                "-c",
                                f"echo >/dev/tcp/{host}/{port_str}",
                            ],
                        )
                        result["status"] = "passed" if success else "failed"
            elif check_type == "process":
                process = target or DEFAULT_PROCESS
                if not _is_safe_process(process):
                    result["status"] = "failed"
                    result["error"] = f"Invalid process name: {process!r}"
                else:
                    success, _ = self._exec_in_container(
                        container, ["pgrep", "-x", process]
                    )
                    result["status"] = "passed" if success else "failed"
            elif check_type == "api":
                url = target or DEFAULT_HEALTH_URL
                if not _is_safe_url(url):
                    result["status"] = "failed"
                    result["error"] = f"Invalid URL: {url!r}"
                else:
                    success, output = self._exec_in_container(
                        container,
                        [
                            "curl",
                            "-s",
                            "-o",
                            "/dev/null",
                            "-w",
                            "%{http_code}",
                            url,
                        ],
                    )
                    result["status"] = (
                        "passed"
                        if output.strip() in ("200", "201", "204")
                        else "failed"
                    )
            else:
                result["status"] = "unknown"
                result["error"] = f"Unknown check type: {check_type}"
        except Exception as exc:
            result["status"] = "failed"
            result["error"] = str(exc)

        elapsed = (datetime.now() - start).total_seconds() * 1000
        result["response_time_ms"] = int(elapsed)
        self._record_health_check_result(container_id, check_type, result)
        return result

    def _exec_in_container(
        self, container, command: "str | List[str]"
    ) -> Tuple[bool, str]:
        """Execute a command inside a container (list form avoids shell)."""
        try:
            result = container.exec_run(command)
            output = result.output
            if isinstance(output, bytes):
                output = output.decode()
            elif output is None:
                output = ""
            else:
                output = str(output)
            return result.exit_code == 0, output
        except Exception:
            return False, ""

    def _record_health_check_result(
        self,
        container_id: str,
        check_type: str,
        result: Dict[str, Any],
    ):
        """Persist a health check result to the database.

        Args:
            container_id: The Docker container ID.
            check_type: The type of health check.
            result: The check result dict.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO health_check_results "
                "(check_id, status, response_time_ms, error_message, "
                "checked_at) "
                "VALUES ("
                "(SELECT id FROM health_checks WHERE container_id = %s "
                "AND check_type = %s LIMIT 1), %s, %s, %s, NOW())",
                (
                    container_id,
                    check_type,
                    result["status"],
                    result["response_time_ms"],
                    result.get("error"),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as exc:
            logger.error("Error recording health check result: %s", exc)

    async def benchmark_cpu(self, container_id: str) -> Dict[str, Any]:
        """Run a CPU benchmark inside a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A dict with ``type``, ``score``, and optional ``error``.
        """
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(
                container,
                "sysbench cpu --cpu-max-prime=20000 run 2>/dev/null",
            )
            events_per_sec = 0.0
            for line in output.split("\n"):
                if "events per second" in line:
                    events_per_sec = float(line.split(":")[-1].strip())
            return {"type": "cpu", "score": events_per_sec}
        except Exception as exc:
            return {"type": "cpu", "score": 0, "error": str(exc)}

    async def benchmark_disk(self, container_id: str) -> Dict[str, Any]:
        """Run a disk write benchmark inside a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A dict with ``type``, ``score``, and optional ``error``.
        """
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(
                container,
                "dd if=/dev/zero of=/tmp/bench bs=1M count=128 2>&1",
            )
            speed = 0.0
            for line in output.split("\n"):
                if "MB/s" in line or "GB/s" in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if "MB/s" in p or "GB/s" in p:
                            speed = float(parts[i - 1])
            return {"type": "disk", "score": speed}
        except Exception as exc:
            return {"type": "disk", "score": 0, "error": str(exc)}

    async def benchmark_network(self, container_id: str) -> Dict[str, Any]:
        """Run a network throughput benchmark inside a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A dict with ``type``, ``score``, and optional ``error``.
        """
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(
                container,
                "iperf3 -c iperf.he.net -t 10 -f M 2>&1",
            )
            speed = 0.0
            for line in output.split("\n"):
                if "receiver" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if "Mbits" in p or "Mbits/sec" in p:
                            speed = float(parts[i - 1])
            return {"type": "network", "score": speed}
        except Exception as exc:
            return {"type": "network", "score": 0, "error": str(exc)}

    async def get_usage_history(
        self, container_id: str, hours: int = 24
    ) -> Optional[List[Dict]]:
        """Retrieve historical resource usage for a container.

        Args:
            container_id: The Docker container ID.
            hours: Look-back window in hours.

        Returns:
            A list of statistics dicts, or ``None`` on failure.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM vps_statistics WHERE container_id = %s "
                "AND timestamp > NOW() - INTERVAL '1 HOUR' * %s "
                "ORDER BY timestamp ASC",
                (container_id, hours),
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as exc:
            logger.error("Error getting usage history: %s", exc)
            return None

    async def get_network_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve aggregated network statistics for a container.

        Args:
            container_id: The Docker container ID.

        Returns:
            A dict with average/peak/total traffic metrics, or ``None``.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT AVG(network_rx) as avg_rx, "
                "AVG(network_tx) as avg_tx, "
                "MAX(network_rx) as peak_rx, "
                "MAX(network_tx) as peak_tx, "
                "SUM(network_rx + network_tx) as total_traffic "
                "FROM vps_statistics "
                "WHERE container_id = %s "
                "AND timestamp > NOW() - INTERVAL '24 HOURS'",
                (container_id,),
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Exception as exc:
            logger.error("Error getting network stats: %s", exc)
            return None
