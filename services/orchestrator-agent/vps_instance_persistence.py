"""Persistence operations for VPS instance metadata."""

import json
import os
from typing import List, Optional, Tuple

import aiofiles

from vps_docker_support import config, logger

class PersistenceMixin:
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
        async with self._persistence_lock:
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
