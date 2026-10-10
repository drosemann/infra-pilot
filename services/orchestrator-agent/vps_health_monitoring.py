"""Health checks, metrics, cloning, and usage history for VPS containers."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from vps_docker_support import (
    CPU_PERIOD,
    DEFAULT_HEALTH_URL,
    DEFAULT_PING_TARGET,
    DEFAULT_PORT_CHECK,
    DEFAULT_PROCESS,
    MIGRATION_TMP_DIR,
    RESTART_POLICY,
    _is_safe_host,
    _is_safe_process,
    _is_safe_url,
    _run_with_storage_opt_fallback,
    _storage_opt,
    logger,
)


class MonitoringMixin:
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
