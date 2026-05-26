import os
from typing import Dict, Any, Set
import requests

class Config:
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    CUTTLY_API_KEY: str = os.getenv("CUTTLY_API_KEY", "")
    PUBLIC_IP: str = os.getenv("PUBLIC_IP", "")
    WHITELIST_IDS: Set[str] = set(filter(None, os.getenv("WHITELIST_IDS", "").split(",")))
    INTEGRATION_SERVICE_URL: str = os.getenv("INTEGRATION_SERVICE_URL", "http://localhost:9000")

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "infra_pilot")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))

    VPS_INSTANCES_FILE: str = os.getenv("VPS_INSTANCES_FILE", "vps_instances.json")
    DATABASE_FILE: str = os.getenv("DATABASE_FILE", "database.txt")

    DEFAULT_IMAGE: str = os.getenv("DEFAULT_IMAGE", "ubuntu-22.04-with-tmate")
    RAM_LIMIT: str = os.getenv("RAM_LIMIT", "1g")
    SERVER_LIMIT: int = int(os.getenv("SERVER_LIMIT", "1"))
    DEFAULT_SSH_IMAGE: str = "ubuntu-22.04-with-tmate"

    RESOURCE_LIMITS: Dict[str, Any] = {
        "min_cpu": 0.5,
        "max_cpu": 4.0,
        "min_memory_mb": 512,
        "max_memory_mb": 8192,
        "min_storage_gb": 10,
        "max_storage_gb": 100,
    }

    PRICING: Dict[str, float] = {
        "cpu_per_core": 50.0,
        "memory_per_gb": 25.0,
        "storage_per_gb": 1.0,
        "bandwidth_per_gb": 0.5,
    }

    BILLING_INTERVAL_DAYS: int = 30
    GRACE_PERIOD_DAYS: int = 3

    ALERT_THRESHOLDS: Dict[str, float] = {
        "cpu": 90.0,
        "memory": 90.0,
        "disk": 90.0,
        "network": 90.0,
    }

    BACKUP_RETENTION: Dict[str, int] = {
        "daily": 7,
        "weekly": 4,
        "monthly": 3,
    }

    AUTO_SCALE_COOLDOWN_MINUTES: int = 5
    AUTO_SCALE_CPU_THRESHOLD: float = 80.0
    AUTO_SCALE_MEMORY_THRESHOLD: float = 80.0

    OVERSUBSCRIPTION_RATIOS: Dict[str, float] = {
        "cpu": 4.0,
        "memory": 2.0,
    }

    HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    MONITORING_INTERVAL_SECONDS: int = 60

    DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "ubuntu-22.04": {"image": "ubuntu:22.04", "cpu": 1, "memory": 1024, "storage": 20},
        "ubuntu-24.04": {"image": "ubuntu:24.04", "cpu": 1, "memory": 1024, "storage": 20},
        "debian-12": {"image": "debian:12", "cpu": 1, "memory": 1024, "storage": 20},
        "nginx-server": {"image": "nginx:latest", "cpu": 0.5, "memory": 512, "storage": 10},
        "postgres-db": {"image": "postgres:16", "cpu": 2, "memory": 2048, "storage": 50},
    }

    LB_HEALTH_CHECK_INTERVAL: int = 10
    LB_HEALTH_CHECK_TIMEOUT: int = 5
    LB_HEALTH_CHECK_RETRIES: int = 3

    DNS_TTL: int = 300
    DNS_DEFAULT_RECORD_TYPE: str = "A"

    SSL_RENEWAL_DAYS_BEFORE_EXPIRY: int = 30
    SSL_EMAIL: str = os.getenv("SSL_EMAIL", "admin@example.com")

    MONITORING_RETENTION_DAYS: int = 30
    CLEANUP_LOG_RETENTION_DAYS: int = 7

    QUOTA_DEFAULTS: Dict[str, int] = {
        "cpu_cores": 4,
        "memory_mb": 8192,
        "storage_gb": 100,
        "bandwidth_gb": 1000,
        "vps_count": 5,
    }

    BENCHMARK_TIMEOUT_SECONDS: int = 30

    RECOVERY_MAX_RETRIES: int = 3
    RECOVERY_PLAYBOOK_TIMEOUT: int = 60

    TRAFFIC_ANALYSIS_PERIODS: Dict[str, int] = {
        "24h": 24,
        "7d": 168,
        "30d": 720,
    }

    COST_PREDICTION_HISTORY_MONTHS: int = 3

config = Config()


def validate_discord_token(token: str) -> dict:
    headers = {"Authorization": f"Bot {token}"}
    try:
        resp = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=10)
        if resp.status_code == 200:
            user_data = resp.json()
            guild_resp = requests.get(
                "https://discord.com/api/v10/users/@me/guilds",
                headers=headers,
                timeout=10,
            )
            guild_count = len(guild_resp.json()) if guild_resp.ok else 0
            return {
                "valid": True,
                "botName": user_data.get("username", ""),
                "guildCount": guild_count,
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "Invalid token"}
        return {"valid": False, "error": "Discord API error"}
    except requests.RequestException:
        return {"valid": False, "error": "Failed to validate token"}
