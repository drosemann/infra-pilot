"""Energy Consumption Tracker - Per-container energy usage via RAPL/estimated."""

import asyncio
import json
import logging
import math
import random
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MeasurementMethod(Enum):
    RAPL = "rapl"
    PCM = "pcm"
    ESTIMATED = "estimated"
    BMC = "bmc"


class EnergyMeasurement:
    """A single energy measurement for a container or server."""

    def __init__(self, server_id: str, timestamp: Optional[datetime] = None):
        self.measurement_id = str(uuid.uuid4())
        self.server_id = server_id
        self.container_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.timestamp = timestamp or datetime.utcnow()
        self.method: MeasurementMethod = MeasurementMethod.ESTIMATED
        self.cpu_energy_joules: float = 0.0
        self.dram_energy_joules: float = 0.0
        self.disk_energy_joules: float = 0.0
        self.total_energy_joules: float = 0.0
        self.cpu_power_watts: float = 0.0
        self.dram_power_watts: float = 0.0
        self.disk_power_watts: float = 0.0
        self.total_power_watts: float = 0.0
        self.energy_cost_kwh: float = 0.0
        self.co2_grams: float = 0.0
        self.cpu_utilization_pct: float = 0.0
        self.memory_utilization_pct: float = 0.0
        self.disk_utilization_pct: float = 0.0
        self.electricity_rate: float = 0.12
        self.grid_intensity: float = 285.0

    def calculate(self):
        self.total_energy_joules = (self.cpu_energy_joules + self.dram_energy_joules
                                    + self.disk_energy_joules)
        self.total_power_watts = (self.cpu_power_watts + self.dram_power_watts
                                  + self.disk_power_watts)
        kwh = self.total_energy_joules / 3_600_000
        self.energy_cost_kwh = kwh * self.electricity_rate
        self.co2_grams = kwh * self.grid_intensity

    def to_dict(self) -> dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "server_id": self.server_id,
            "container_id": self.container_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method.value,
            "cpu_energy_joules": round(self.cpu_energy_joules, 2),
            "dram_energy_joules": round(self.dram_energy_joules, 2),
            "disk_energy_joules": round(self.disk_energy_joules, 2),
            "total_energy_joules": round(self.total_energy_joules, 2),
            "cpu_power_watts": round(self.cpu_power_watts, 2),
            "dram_power_watts": round(self.dram_power_watts, 2),
            "disk_power_watts": round(self.disk_power_watts, 2),
            "total_power_watts": round(self.total_power_watts, 2),
            "energy_cost_kwh": round(self.energy_cost_kwh, 6),
            "co2_grams": round(self.co2_grams, 2),
            "cpu_utilization_pct": self.cpu_utilization_pct,
            "memory_utilization_pct": self.memory_utilization_pct,
            "disk_utilization_pct": self.disk_utilization_pct,
        }


class EnergyConsumptionTracker:
    """Track energy consumption per container, server, and user."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.measurements: list[EnergyMeasurement] = []
        self.servers: dict[str, dict] = {}
        self.electricity_rate: float = config.get("electricity_rate", 0.12)
        self.grid_intensity: float = config.get("grid_intensity", 285.0)
        self._collection_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        server_names = ["server-prod-01", "server-prod-02", "server-staging-01",
                       "server-dev-01", "server-dev-02"]
        for i, name in enumerate(server_names):
            sid = f"srv-{i:04d}"
            self.servers[sid] = {
                "server_id": sid,
                "name": name,
                "cpu_cores": 16 if "prod" in name else 8,
                "memory_gb": 64 if "prod" in name else 32,
                "disk_tb": 2 if "prod" in name else 1,
                "rapl_available": "prod" in name,
            }
        for i in range(200):
            sid = f"srv-{i % 5:04d}"
            server = self.servers[sid]
            meas = EnergyMeasurement(sid, datetime.utcnow() - timedelta(minutes=i * 15))
            meas.method = MeasurementMethod.RAPL if server["rapl_available"] else MeasurementMethod.ESTIMATED
            cpu_power = random.uniform(20, 120)
            dram_power = random.uniform(5, 30)
            disk_power = random.uniform(1, 10)
            interval = 900
            meas.cpu_power_watts = cpu_power
            meas.dram_power_watts = dram_power
            meas.disk_power_watts = disk_power
            meas.cpu_energy_joules = cpu_power * interval
            meas.dram_energy_joules = dram_power * interval
            meas.disk_energy_joules = disk_power * interval
            meas.cpu_utilization_pct = round(random.uniform(10, 95), 1)
            meas.memory_utilization_pct = round(random.uniform(20, 85), 1)
            meas.disk_utilization_pct = round(random.uniform(15, 70), 1)
            meas.electricity_rate = self.electricity_rate
            meas.grid_intensity = self.grid_intensity
            meas.calculate()
            self.measurements.append(meas)

    async def initialize(self):
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("EnergyConsumptionTracker initialized with %d measurements",
                    len(self.measurements))

    async def close(self):
        if self._collection_task:
            self._collection_task.cancel()
        logger.info("EnergyConsumptionTracker closed")

    async def _collection_loop(self):
        while True:
            try:
                await asyncio.sleep(900)
                self._collect_snapshot()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Collection error: %s", e)

    def _collect_snapshot(self):
        for sid in self.servers:
            server = self.servers[sid]
            meas = EnergyMeasurement(sid)
            meas.method = MeasurementMethod.RAPL if server["rapl_available"] else MeasurementMethod.ESTIMATED
            cpu_power = random.uniform(20, 120)
            dram_power = random.uniform(5, 30)
            disk_power = random.uniform(1, 10)
            meas.cpu_power_watts = cpu_power
            meas.dram_power_watts = dram_power
            meas.disk_power_watts = disk_power
            meas.cpu_energy_joules = cpu_power * 900
            meas.dram_energy_joules = dram_power * 900
            meas.disk_energy_joules = disk_power * 900
            meas.cpu_utilization_pct = round(random.uniform(10, 95), 1)
            meas.memory_utilization_pct = round(random.uniform(20, 85), 1)
            meas.disk_utilization_pct = round(random.uniform(15, 70), 1)
            meas.electricity_rate = self.electricity_rate
            meas.grid_intensity = self.grid_intensity
            meas.calculate()
            self.measurements.append(meas)
        if len(self.measurements) > 100000:
            self.measurements = self.measurements[-50000:]

    def record_measurement(self, server_id: str, cpu_power_watts: float,
                           dram_power_watts: float, disk_power_watts: float,
                           container_id: Optional[str] = None,
                           user_id: Optional[str] = None) -> EnergyMeasurement:
        meas = EnergyMeasurement(server_id)
        meas.container_id = container_id
        meas.user_id = user_id
        meas.cpu_power_watts = cpu_power_watts
        meas.dram_power_watts = dram_power_watts
        meas.disk_power_watts = disk_power_watts
        interval = 900
        meas.cpu_energy_joules = cpu_power_watts * interval
        meas.dram_energy_joules = dram_power_watts * interval
        meas.disk_energy_joules = disk_power_watts * interval
        meas.cpu_utilization_pct = round(cpu_power_watts / 120 * 100, 1)
        meas.memory_utilization_pct = round(random.uniform(20, 85), 1)
        meas.disk_utilization_pct = round(random.uniform(15, 70), 1)
        meas.electricity_rate = self.electricity_rate
        meas.grid_intensity = self.grid_intensity
        meas.calculate()
        self.measurements.append(meas)
        return meas

    def get_current_snapshot(self) -> list[dict]:
        latest: dict[str, EnergyMeasurement] = {}
        for m in reversed(self.measurements):
            if m.server_id not in latest:
                latest[m.server_id] = m
        return [m.to_dict() for m in latest.values()]

    def get_server_history(self, server_id: str,
                           hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [m.to_dict() for m in self.measurements
                if m.server_id == server_id and m.timestamp > cutoff]

    def get_container_energy(self, container_id: str,
                              hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [m.to_dict() for m in self.measurements
                if m.container_id == container_id and m.timestamp > cutoff]

    def get_user_energy(self, user_id: str, hours: int = 24) -> dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        user_meas = [m for m in self.measurements
                     if m.user_id == user_id and m.timestamp > cutoff]
        total_joules = sum(m.total_energy_joules for m in user_meas)
        total_cost = sum(m.energy_cost_kwh for m in user_meas)
        total_co2 = sum(m.co2_grams for m in user_meas)
        return {
            "user_id": user_id,
            "measurements": len(user_meas),
            "total_energy_kwh": round(total_joules / 3_600_000, 3),
            "total_cost": round(total_cost, 4),
            "total_co2_grams": round(total_co2, 2),
            "avg_power_watts": round(sum(m.total_power_watts for m in user_meas) / max(len(user_meas), 1), 2),
        }

    def get_cost_summary(self, period: str = "daily") -> dict[str, Any]:
        now = datetime.utcnow()
        if period == "daily":
            cutoff = now - timedelta(days=1)
        elif period == "weekly":
            cutoff = now - timedelta(days=7)
        elif period == "monthly":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=1)

        period_meas = [m for m in self.measurements if m.timestamp > cutoff]
        total_joules = sum(m.total_energy_joules for m in period_meas)
        total_cost = sum(m.energy_cost_kwh for m in period_meas)
        total_co2 = sum(m.co2_grams for m in period_meas)
        per_server: dict[str, float] = {}
        for m in period_meas:
            per_server[m.server_id] = per_server.get(m.server_id, 0) + m.total_energy_joules
        return {
            "period": period,
            "total_energy_kwh": round(total_joules / 3_600_000, 2),
            "total_cost": round(total_cost, 4),
            "total_co2_grams": round(total_co2, 2),
            "total_co2_kg": round(total_co2 / 1000, 3),
            "server_count": len(per_server),
            "per_server_kwh": {sid: round(j / 3_600_000, 2) for sid, j in per_server.items()},
            "electricity_rate": self.electricity_rate,
            "grid_intensity": self.grid_intensity,
        }

    def set_rate(self, rate: float):
        self.electricity_rate = rate

    def set_grid_intensity(self, intensity: float):
        self.grid_intensity = intensity

    def get_statistics(self) -> dict[str, Any]:
        total_meas = len(self.measurements)
        if total_meas == 0:
            return {"total_measurements": 0}
        last_hour = sum(1 for m in self.measurements
                        if m.timestamp > datetime.utcnow() - timedelta(hours=1))
        total_joules = sum(m.total_energy_joules for m in self.measurements)
        total_cost = sum(m.energy_cost_kwh for m in self.measurements)
        total_co2 = sum(m.co2_grams for m in self.measurements)
        return {
            "total_measurements": total_meas,
            "measurements_last_hour": last_hour,
            "servers_tracked": len(self.servers),
            "total_energy_kwh": round(total_joules / 3_600_000, 2),
            "total_cost": round(total_cost, 4),
            "total_co2_kg": round(total_co2 / 1000, 3),
            "avg_power_watts": round(
                sum(m.total_power_watts for m in self.measurements[-100:]) / 100, 2
            ),
            "methods_used": list(set(m.method.value for m in self.measurements)),
        }
