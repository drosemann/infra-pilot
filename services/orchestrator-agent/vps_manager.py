import docker
import asyncio
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging
from datetime import datetime, timedelta
import json
import os
import re
import random
import subprocess
from threading import Lock

from config import config

SAFE_CONTAINER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


@dataclass
class VPSConfig:
    cpu_limit: float
    memory_limit: int
    storage_limit: int
    image: str
    ports: Dict[str, str]
    env_vars: Dict[str, str]


class VPSManager:
    def __init__(self):
        self.client = docker.from_env()
        self.logger = logging.getLogger('vps_manager')
        self.vps_instances = {}
        self.database_lock = Lock()
        self.load_instances()

    def load_instances(self):
        try:
            if os.path.exists(config.VPS_INSTANCES_FILE):
                with open(config.VPS_INSTANCES_FILE, 'r') as f:
                    self.vps_instances = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading VPS instances: {e}")
            self.vps_instances = {}

    def save_instances(self):
        try:
            with open(config.VPS_INSTANCES_FILE, 'w') as f:
                json.dump(self.vps_instances, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving VPS instances: {e}")

    def is_safe_name(self, name: str) -> bool:
        return bool(SAFE_CONTAINER_RE.fullmatch(name))

    def generate_random_port(self) -> int:
        return random.randint(1025, 65535)

    def add_to_database(self, user_id: str, container_id: str, ssh_command: str):
        with self.database_lock:
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT IGNORE INTO vps_containers (container_id, user_id, container_name, ssh_command) VALUES (%s, %s, %s, %s)",
                    (container_id, user_id, container_id[:12], ssh_command),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                self.logger.error(f"Error adding to database: {e}")

    def remove_from_database(self, container_id: str):
        with self.database_lock:
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM vps_containers WHERE container_id = %s", (container_id,))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                self.logger.error(f"Error removing from database: {e}")

    def get_user_servers(self, user_id: str) -> List[str]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT container_id, container_name, ssh_command FROM vps_containers WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except Exception:
            return []

    def count_user_servers(self, user_id: str) -> int:
        return len(self.get_user_servers(user_id))

    def get_container_id_from_database(self, user_id: str, container_name: str) -> Optional[str]:
        servers = self.get_user_servers(user_id)
        for container_id, name, _ in servers:
            if name == container_name or container_id == container_name or container_id.startswith(container_name):
                return container_id
        return None

    def get_ssh_command_from_database(self, container_id: str) -> Optional[str]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ssh_command FROM vps_containers WHERE container_id = %s", (container_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def _get_db_connection(self):
        import mysql.connector
        return mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )

    async def create_vps(self, user_id: str, cfg: VPSConfig) -> Optional[str]:
        try:
            container = self.client.containers.run(
                image=cfg.image,
                detach=True,
                cpu_period=100000,
                cpu_quota=int(cfg.cpu_limit * 100000),
                mem_limit=f"{cfg.memory_limit}m",
                ports=cfg.ports,
                environment=cfg.env_vars,
                restart_policy={"Name": "unless-stopped"},
            )

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
                "host": os.uname().nodename if hasattr(os, 'uname') else "localhost",
            }

            self.vps_instances[container.id] = instance_info
            self.save_instances()
            return container.id
        except Exception as e:
            self.logger.error(f"Error creating VPS: {e}")
            return None

    async def delete_vps(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            self.vps_instances.pop(container_id, None)
            self.save_instances()
            self.remove_from_database(container_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting VPS: {e}")
            return False

    async def start_vps(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.start()
            self._update_status(container_id, "running")
            return True
        except Exception as e:
            self.logger.error(f"Error starting VPS: {e}")
            return False

    async def stop_vps(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            self._update_status(container_id, "stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping VPS: {e}")
            return False

    async def restart_vps(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            self._update_status(container_id, "running")
            return True
        except Exception as e:
            self.logger.error(f"Error restarting VPS: {e}")
            return False

    def _update_status(self, container_id: str, status: str):
        if container_id in self.vps_instances:
            self.vps_instances[container_id]["status"] = status
            self.save_instances()

    async def get_vps_stats(self, container_id: str) -> Optional[Dict]:
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0

            return {
                "status": container.status,
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory_percent, 2),
                "network": {
                    "rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
                    "tx_bytes": stats["networks"]["eth0"]["tx_bytes"],
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting VPS stats: {e}")
            return None

    async def list_user_instances(self, user_id: str) -> List[Dict]:
        return [
            {"container_id": cid, "info": info, "stats": await self.get_vps_stats(cid)}
            for cid, info in self.vps_instances.items()
            if info["user_id"] == user_id
        ]

    async def update_vps_config(self, container_id: str, cfg: VPSConfig) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.update(
                cpu_period=100000,
                cpu_quota=int(cfg.cpu_limit * 100000),
                mem_limit=f"{cfg.memory_limit}m",
            )
            if container_id in self.vps_instances:
                self.vps_instances[container_id]["config"].update({
                    "cpu_limit": cfg.cpu_limit,
                    "memory_limit": cfg.memory_limit,
                    "storage_limit": cfg.storage_limit,
                })
                self.save_instances()
            container.start()
            return True
        except Exception as e:
            self.logger.error(f"Error updating VPS config: {e}")
            return False

    async def create_backup(self, container_id: str, retention_type: str = "daily") -> Optional[str]:
        try:
            container = self.client.containers.get(container_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{container.name}_backup_{timestamp}"
            image = container.commit(repository=backup_name)

            if container_id in self.vps_instances:
                if "backups" not in self.vps_instances[container_id]:
                    self.vps_instances[container_id]["backups"] = []
                self.vps_instances[container_id]["backups"].append({
                    "image_id": image.id,
                    "created_at": timestamp,
                    "name": backup_name,
                    "retention_type": retention_type,
                })
                self.save_instances()

            self._record_backup(container_id, image.id, backup_name, retention_type)
            self._apply_retention_policy(container_id)
            return image.id
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    def _record_backup(self, container_id: str, image_id: str, name: str, retention_type: str):
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO backup_rotation (container_id, image_id, name, retention_type) VALUES (%s, %s, %s, %s)",
                (container_id, image_id, name, retention_type),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error recording backup: {e}")

    def _apply_retention_policy(self, container_id: str):
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for retention_type, max_count in config.BACKUP_RETENTION.items():
                cursor.execute(
                    """SELECT id, created_at FROM backup_rotation
                       WHERE container_id = %s AND retention_type = %s
                       ORDER BY created_at DESC""",
                    (container_id, retention_type),
                )
                backups = cursor.fetchall()
                if len(backups) > max_count:
                    to_delete = backups[max_count:]
                    for b in to_delete:
                        cursor.execute("DELETE FROM backup_rotation WHERE id = %s", (b["id"],))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error applying retention policy: {e}")

    async def list_backups(self, container_id: str) -> List[Dict]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM backup_rotation WHERE container_id = %s ORDER BY created_at DESC",
                (container_id,),
            )
            backups = cursor.fetchall()
            cursor.close()
            conn.close()
            return backups
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
            return self.vps_instances.get(container_id, {}).get("backups", [])

    async def restore_backup(self, container_id: str, backup_image_id: str) -> bool:
        try:
            await self.stop_vps(container_id)
            instance_info = self.vps_instances.get(container_id)
            if not instance_info:
                return False
            config_data = instance_info["config"]

            container = self.client.containers.run(
                image=backup_image_id,
                detach=True,
                cpu_period=100000,
                cpu_quota=int(config_data["cpu_limit"] * 100000),
                mem_limit=f"{config_data['memory_limit']}m",
                ports=config_data["ports"],
                restart_policy={"Name": "unless-stopped"},
            )

            instance_info["container_id"] = container.id
            self.vps_instances[container.id] = instance_info
            self.vps_instances.pop(container_id, None)
            self.save_instances()
            return True
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False

    async def create_snapshot(self, container_id: str, name: str = None) -> Optional[str]:
        try:
            container = self.client.containers.get(container_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_name = name or f"{container.name}_snapshot_{timestamp}"
            image = container.commit(repository=snapshot_name)

            if container_id in self.vps_instances:
                if "snapshots" not in self.vps_instances[container_id]:
                    self.vps_instances[container_id]["snapshots"] = []
                self.vps_instances[container_id]["snapshots"].append({
                    "image_id": image.id,
                    "created_at": timestamp,
                    "name": snapshot_name,
                })
                self.save_instances()

            self._record_snapshot(container_id, snapshot_name, image.id)
            return image.id
        except Exception as e:
            self.logger.error(f"Error creating snapshot: {e}")
            return None

    def _record_snapshot(self, container_id: str, name: str, image_id: str):
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO snapshots (container_id, name, image_id) VALUES (%s, %s, %s)",
                (container_id, name, image_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error recording snapshot: {e}")

    async def list_snapshots(self, container_id: str) -> List[Dict]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM snapshots WHERE container_id = %s ORDER BY created_at DESC",
                (container_id,),
            )
            snapshots = cursor.fetchall()
            cursor.close()
            conn.close()
            return snapshots
        except Exception as e:
            self.logger.error(f"Error listing snapshots: {e}")
            return self.vps_instances.get(container_id, {}).get("snapshots", [])

    async def restore_snapshot(self, container_id: str, snapshot_image_id: str) -> bool:
        return await self.restore_backup(container_id, snapshot_image_id)

    async def clone_vps(self, container_id: str, new_name: str) -> Optional[str]:
        try:
            container = self.client.containers.get(container_id)
            image = container.commit(repository=f"{new_name}_clone")

            instance_info = self.vps_instances.get(container_id)
            if not instance_info:
                return None

            cfg = instance_info["config"]
            new_container = self.client.containers.run(
                image=image.id,
                detach=True,
                cpu_period=100000,
                cpu_quota=int(cfg["cpu_limit"] * 100000),
                mem_limit=f"{cfg['memory_limit']}m",
                ports=cfg["ports"],
                restart_policy={"Name": "unless-stopped"},
            )

            new_info = dict(instance_info)
            new_info["container_id"] = new_container.id
            new_info["created_at"] = datetime.now().isoformat()
            new_info["cloned_from"] = container_id
            self.vps_instances[new_container.id] = new_info
            self.save_instances()
            return new_container.id
        except Exception as e:
            self.logger.error(f"Error cloning VPS: {e}")
            return None

    async def migrate_vps(self, container_id: str, target_host: str) -> bool:
        try:
            self.logger.info(f"Migrating container {container_id} to {target_host}")

            container = self.client.containers.get(container_id)
            image = container.commit(repository=f"migration_{container_id[:12]}")

            save_path = f"/tmp/{container_id}_migration.tar"
            with open(save_path, 'wb') as f:
                for chunk in self.client.images.get(image.id).save():
                    f.write(chunk)

            self.logger.info(f"Container {container_id} saved for migration to {target_host}")
            return True
        except Exception as e:
            self.logger.error(f"Error migrating VPS: {e}")
            return False

    async def run_health_check(self, container_id: str, check_type: str, target: str = None) -> Dict:
        result = {"status": "unknown", "response_time_ms": 0, "error": None}
        start = datetime.now()

        try:
            container = self.client.containers.get(container_id)

            if check_type == "ping":
                success, _ = self._exec_in_container(container, f"ping -c 1 -W 2 {'8.8.8.8' if not target else target}")
                result["status"] = "passed" if success else "failed"
            elif check_type == "port":
                host, port = (target or "localhost:22").split(":")
                success, _ = self._exec_in_container(container, f"timeout 2 bash -c 'echo >/dev/tcp/{host}/{port}' 2>/dev/null")
                result["status"] = "passed" if success else "failed"
            elif check_type == "process":
                process = target or "sshd"
                success, _ = self._exec_in_container(container, f"pgrep -x {process}")
                result["status"] = "passed" if success else "failed"
            elif check_type == "api":
                url = target or "http://localhost:80/health"
                success, output = self._exec_in_container(container, f"curl -s -o /dev/null -w '%{{http_code}}' {url}")
                result["status"] = "passed" if output.strip() in ("200", "201", "204") else "failed"
            else:
                result["status"] = "unknown"
                result["error"] = f"Unknown check type: {check_type}"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        elapsed = (datetime.now() - start).total_seconds() * 1000
        result["response_time_ms"] = int(elapsed)
        self._record_health_check_result(container_id, check_type, result)
        return result

    def _exec_in_container(self, container, command: str) -> tuple:
        try:
            result = container.exec_run(command)
            return result.exit_code == 0, result.output.decode()
        except Exception:
            return False, ""

    def _record_health_check_result(self, container_id: str, check_type: str, result: Dict):
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO health_check_results (check_id, status, response_time_ms, error_message, checked_at) "
                "VALUES ((SELECT id FROM health_checks WHERE container_id = %s AND check_type = %s LIMIT 1), %s, %s, %s, NOW())",
                (container_id, check_type, result["status"], result["response_time_ms"], result.get("error")),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error recording health check result: {e}")

    async def benchmark_cpu(self, container_id: str) -> Dict:
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(container, "sysbench cpu --cpu-max-prime=20000 run 2>/dev/null")
            events_per_sec = 0
            for line in output.split("\n"):
                if "events per second" in line:
                    events_per_sec = float(line.split(":")[-1].strip())
            return {"type": "cpu", "score": events_per_sec}
        except Exception as e:
            return {"type": "cpu", "score": 0, "error": str(e)}

    async def benchmark_disk(self, container_id: str) -> Dict:
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(container, "dd if=/dev/zero of=/tmp/bench bs=1M count=128 2>&1")
            speed = 0
            for line in output.split("\n"):
                if "MB/s" in line or "GB/s" in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if "MB/s" in p or "GB/s" in p:
                            speed = float(parts[i-1])
            return {"type": "disk", "score": speed}
        except Exception as e:
            return {"type": "disk", "score": 0, "error": str(e)}

    async def benchmark_network(self, container_id: str) -> Dict:
        try:
            container = self.client.containers.get(container_id)
            _, output = self._exec_in_container(container, "iperf3 -c iperf.he.net -t 10 -f M 2>&1")
            speed = 0
            for line in output.split("\n"):
                if "receiver" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if "Mbits" in p or "Mbits/sec" in p:
                            speed = float(parts[i-1])
            return {"type": "network", "score": speed}
        except Exception as e:
            return {"type": "network", "score": 0, "error": str(e)}

    async def get_usage_history(self, container_id: str, hours: int = 24) -> Optional[List[Dict]]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM vps_statistics WHERE container_id = %s AND timestamp > DATE_SUB(NOW(), INTERVAL %s HOUR) ORDER BY timestamp ASC",
                (container_id, hours),
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"Error getting usage history: {e}")
            return None

    async def get_network_stats(self, container_id: str) -> Optional[Dict]:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT AVG(network_rx) as avg_rx, AVG(network_tx) as avg_tx, "
                "MAX(network_rx) as peak_rx, MAX(network_tx) as peak_tx, "
                "SUM(network_rx + network_tx) as total_traffic "
                "FROM vps_statistics WHERE container_id = %s AND timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)",
                (container_id,),
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            self.logger.error(f"Error getting network stats: {e}")
            return None
