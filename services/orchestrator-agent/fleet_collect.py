"""Living Fleet signal collector: real Docker/VPS signals into the mood engine.

Runs as a periodic loop (started by ``build_webhook_app`` when
``LIVING_FLEET_ENABLED``). Every signal below comes from an existing source:
Docker container attrs/stats, the VPS instance record, or the snapshots table.
Signals with no source stay absent (never defaulted), and one-shot Docker CPU
is deliberately omitted — it needs two samples to be honest.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import living_fleet

logger = logging.getLogger(__name__)

INTERVAL_S = int(os.getenv("LIVING_FLEET_INTERVAL_S", "60"))


def _days_since(value: Any) -> Any:
    """Parse ISO-8601 or datetime into age in days; ``None`` when unparseable."""
    try:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            dt = datetime.fromisoformat(value)
        else:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    except (ValueError, TypeError, OverflowError):
        return None


async def _docker_signals(vm: Any, container_id: str, info: Dict[str, Any]) -> Dict[str, Any]:
    """Gather per-container signals from Docker; fall back to the record."""
    signals: Dict[str, Any] = {}
    try:
        container = vm.client.containers.get(container_id)
        attrs = container.attrs or {}
        state = attrs.get("State", {})
        running = state.get("Running")
        if isinstance(running, bool):
            signals["running"] = running
        restarts = state.get("RestartCount")
        if isinstance(restarts, (int, float)):
            signals["restart_count_total"] = restarts
        health = (state.get("Health") or {}).get("Status")
        if health == "healthy":
            signals["healthcheck_ok"] = True
        elif health == "unhealthy":
            signals["healthcheck_ok"] = False
        try:
            stats = container.stats(stream=False)
            mem = stats.get("memory_stats", {})
            usage, limit = mem.get("usage"), mem.get("limit")
            if usage and limit:
                signals["mem_percent"] = float(usage) / float(limit) * 100.0
        except Exception as exc:
            logger.debug("fleet mem stats unavailable for %s: %s", container_id, exc)
        name = getattr(container, "name", None)
        if isinstance(name, str) and name:
            signals["display_name"] = name
    except Exception as exc:
        logger.debug("fleet docker lookup failed for %s: %s", container_id, exc)
    if "running" not in signals:
        status = info.get("status")
        if status == "running":
            signals["running"] = True
        elif status == "stopped":
            signals["running"] = False
    return signals


async def collect_once() -> Dict[str, Dict[str, Any]]:
    """Refresh every known workload once. Returns workload_id -> public view."""
    from vps_manager import VPSManager

    vm = VPSManager()
    instances = getattr(vm, "vps_instances", {}) or {}
    views: Dict[str, Dict[str, Any]] = {}
    for container_id, info in instances.items():
        try:
            signals = await _docker_signals(vm, container_id, info or {})
            age = _days_since((info or {}).get("created_at"))
            if age is not None:
                signals["days_since_deploy"] = age
            try:
                snaps = await vm.list_snapshots(container_id)
                ages = [
                    _days_since(s.get("created_at"))
                    for s in (snaps or [])
                    if isinstance(s, dict)
                ]
                ages = [a for a in ages if a is not None]
                if ages:
                    signals["days_since_backup"] = min(ages)
                    signals["last_backup_ok"] = True
            except Exception as exc:
                logger.debug("fleet snapshots unavailable for %s: %s", container_id, exc)
            views[container_id] = living_fleet.refresh(container_id, signals)
        except Exception as exc:
            logger.warning("fleet refresh failed for %s: %s", container_id, exc)
    return views


async def run_loop(interval_s: int = INTERVAL_S) -> None:
    """Collect forever; a failing loop iteration never kills the server."""
    while True:
        try:
            if living_fleet.ENABLED:
                await collect_once()
        except Exception as exc:
            logger.warning("fleet collect iteration failed: %s", exc)
        await asyncio.sleep(interval_s)


async def _fleet_startup(app: Any) -> None:
    app["fleet_task"] = asyncio.create_task(run_loop())


async def _fleet_cleanup(app: Any) -> None:
    task = app.get("fleet_task")
    if task is not None:
        task.cancel()


def register(app: Any) -> None:
    """Attach the collector loop to the app lifecycle (no-op unless enabled)."""
    if living_fleet.ENABLED:
        app.on_startup.append(_fleet_startup)
        app.on_cleanup.append(_fleet_cleanup)
        logger.info("living fleet collector every %ds", INTERVAL_S)
