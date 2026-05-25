import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import mysql.connector
import requests

from config import config

REQUEST_TIMEOUT = 5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _send_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[Dict[str, Any]]]:
    try:
        url = f"{config.INTEGRATION_SERVICE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
        else:
            return False, None
        if response.status_code in (200, 201):
            return True, response.json()
        logger.warning(f"Request failed with status {response.status_code}: {response.text}")
        return False, None
    except requests.Timeout:
        logger.warning(f"Request timeout for {endpoint}")
        return False, None
    except requests.RequestException as e:
        logger.warning(f"Request error for {endpoint}: {e}")
        return False, None
    except ValueError as e:
        logger.warning(f"Failed to parse response JSON: {e}")
        return False, None


def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT,
    )


def init_database_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = [
        """
        CREATE TABLE IF NOT EXISTS player_economy (
            uuid VARCHAR(255) PRIMARY KEY,
            balance DOUBLE DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS economy_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            uuid VARCHAR(255) NOT NULL,
            amount DOUBLE NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vps_statistics (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            container_id VARCHAR(255) NOT NULL,
            cpu_usage DOUBLE,
            memory_usage DOUBLE,
            memory_used BIGINT,
            memory_total BIGINT,
            network_rx BIGINT,
            network_tx BIGINT,
            disk_usage DOUBLE,
            status VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_container_id (container_id),
            INDEX idx_timestamp (timestamp)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vps_peak_statistics (
            container_id VARCHAR(255) PRIMARY KEY,
            peak_cpu DOUBLE DEFAULT 0,
            peak_memory DOUBLE DEFAULT 0,
            peak_network BIGINT DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vps_containers (
            container_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            container_name VARCHAR(255),
            ssh_command TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS health_checks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            container_id VARCHAR(255) NOT NULL,
            check_type VARCHAR(50) NOT NULL,
            target VARCHAR(255),
            interval_seconds INT DEFAULT 60,
            last_check TIMESTAMP,
            last_status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_container (container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS health_check_results (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            check_id INT NOT NULL,
            status VARCHAR(50) NOT NULL,
            response_time_ms INT,
            error_message TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_check_id (check_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS backup_rotation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            container_id VARCHAR(255) NOT NULL,
            image_id VARCHAR(255),
            name VARCHAR(255),
            retention_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_container (container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INT AUTO_INCREMENT PRIMARY KEY,
            container_id VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            image_id VARCHAR(255),
            snapshot_type VARCHAR(20) DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_container (container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS dns_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(10) DEFAULT 'A',
            value VARCHAR(255) NOT NULL,
            ttl INT DEFAULT 300,
            zone VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_name (name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ssl_certificates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            domain VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            expires_at TIMESTAMP,
            issued_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_domain (domain)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scaling_rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            container_id VARCHAR(255) NOT NULL,
            metric VARCHAR(50) NOT NULL,
            threshold DOUBLE NOT NULL,
            duration_minutes INT DEFAULT 5,
            action VARCHAR(50) NOT NULL,
            cooldown_until TIMESTAMP,
            enabled TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_container (container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS resource_quotas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            soft_limit BIGINT,
            hard_limit BIGINT,
            usage BIGINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_user_resource (user_id, resource_type)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS load_balancer_pools (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            algorithm VARCHAR(50) DEFAULT 'round_robin',
            health_check_type VARCHAR(50) DEFAULT 'tcp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_name (name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS lb_pool_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pool_id INT NOT NULL,
            container_id VARCHAR(255) NOT NULL,
            host VARCHAR(255),
            port INT,
            weight INT DEFAULT 1,
            enabled TINYINT(1) DEFAULT 1,
            UNIQUE KEY uk_pool_member (pool_id, container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recovery_playbooks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            steps JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_name (name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recovery_executions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            playbook_id INT NOT NULL,
            container_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            current_step INT DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            INDEX idx_container (container_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            version INT DEFAULT 1,
            config JSON,
            created_by VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_name_version (name, version)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            container_id VARCHAR(255),
            alert_type VARCHAR(50) NOT NULL,
            threshold DOUBLE,
            channel VARCHAR(50) DEFAULT 'dm',
            enabled TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id)
        )
        """,
    ]
    for table in tables:
        try:
            cursor.execute(table)
        except Exception as e:
            logger.error(f"Error creating table: {e}")
    conn.commit()
    cursor.close()
    conn.close()


async def notify_integration(event_type: str, data: Dict[str, Any]) -> bool:
    payload = {"event_type": event_type, "server_name": data.get("server_name"), "details": data}
    success, _ = _send_request("POST", "/api/notifications/server-event", payload)
    return success


async def notify_server_created(server_id: str, server_name: str) -> bool:
    data = {"server_id": server_id, "server_name": server_name, "service": "orchestrator"}
    return await notify_integration("server_created", data)


async def notify_server_started(server_id: str, server_name: str) -> bool:
    data = {"server_id": server_id, "server_name": server_name, "service": "orchestrator"}
    return await notify_integration("server_started", data)


async def notify_server_stopped(server_id: str, server_name: str) -> bool:
    data = {"server_id": server_id, "server_name": server_name, "service": "orchestrator"}
    return await notify_integration("server_stopped", data)


async def notify_server_deleted(server_id: str, server_name: str) -> bool:
    data = {"server_id": server_id, "server_name": server_name, "service": "orchestrator"}
    return await notify_integration("server_deleted", data)


async def sync_user_to_integration(user_id: str, email: str, username: str) -> Dict[str, Any]:
    payload = {"email": email, "username": username, "discord_id": user_id}
    success, response = _send_request("POST", "/api/users", payload)
    return response or {}


async def get_unified_metrics() -> Dict[str, Any]:
    success, response = _send_request("GET", "/api/metrics/dashboard")
    return response or {}


async def broadcast_notification(message: str, title: str = "Notification") -> bool:
    payload = {"content": message, "title": title}
    success, _ = _send_request("POST", "/api/notifications", payload)
    return success
