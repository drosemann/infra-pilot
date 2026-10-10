"""Backup and snapshot creation, rotation, and restoration for VPS containers."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from vps_docker_support import (
    CPU_PERIOD,
    RESTART_POLICY,
    _run_with_storage_opt_fallback,
    _storage_opt,
    config,
    logger,
)


class BackupsMixin:
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
