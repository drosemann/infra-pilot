"""Creation, lifecycle, and resource management for VPS containers."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from vps_docker_support import (
    CPU_PERIOD,
    RESTART_POLICY,
    VPSConfig,
    _run_with_storage_opt_fallback,
    _storage_opt,
    _validate_resource_limits,
    _validate_spawn_config,
    logger,
)


class LifecycleMixin:
    async def create_vps(self, user_id: str, cfg: VPSConfig) -> Optional[str]:
        """Create a new Docker container as a VPS.

        Args:
            user_id: The Discord user ID.
            cfg: The VPS configuration.

        Returns:
            The container ID on success, or ``None``.
        """
        try:
            _validate_spawn_config(cfg)
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
        container = None
        was_running = False
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
            was_running = container.status == "running"
            if was_running:
                container.stop()
            container.update(
                cpu_period=CPU_PERIOD,
                cpu_quota=int(cfg.cpu_limit * CPU_PERIOD),
                mem_limit=f"{cfg.memory_limit}m",
            )
            if was_running:
                container.start()
            container.reload()
            if container_id in self.vps_instances:
                self.vps_instances[container_id]["config"].update(
                    {
                        "cpu_limit": cfg.cpu_limit,
                        "memory_limit": cfg.memory_limit,
                        "storage_limit": cfg.storage_limit,
                    }
                )
                self.vps_instances[container_id]["status"] = container.status
                await self.save_instances()
            return True
        except Exception as exc:
            logger.error("Error updating VPS config: %s", exc)
            # A failed resize must not leave a previously running developer
            # workload down.  Docker updates are synchronous, so restarting is
            # the safest rollback we can perform here.
            status = "unknown"
            if container is not None and was_running:
                try:
                    container.start()
                except Exception as recovery_exc:
                    logger.error(
                        "Error restarting VPS after failed config update: %s",
                        recovery_exc,
                    )
            if container is not None:
                try:
                    container.reload()
                    status = container.status
                except Exception as state_exc:
                    logger.error(
                        "Error refreshing VPS state after failed config update: %s",
                        state_exc,
                    )
            if container_id in self.vps_instances:
                self.vps_instances[container_id]["status"] = status
                await self.save_instances()
            return False
