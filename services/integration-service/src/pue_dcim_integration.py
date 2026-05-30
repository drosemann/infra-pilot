"""PUE / DCIM Integration - Data center infrastructure management integration."""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DCIMSystem(Enum):
    NLYTE = "nlyte"
    SUNBIRD = "sunbird"
    DEVICE42 = "device42"
    OPEN_DCIM = "open_dcim"
    BACNET = "bacnet"
    MODBUS = "modbus"
    SNMP = "snmp"


class CoolingType(Enum):
    CRAC = "crac"
    CRAH = "crah"
    CHILLER = "chiller"
    DIRECT_EXPANSION = "direct_expansion"
    FREE_COOLING = "free_cooling"
    LIQUID = "liquid"


class DCIMMetrics:
    """Metrics collected from DCIM system."""

    def __init__(self):
        self.timestamp = datetime.utcnow()
        self.facility_power_kw: float = 0.0
        self.it_power_kw: float = 0.0
        self.cooling_power_kw: float = 0.0
        self.pue: float = 1.0
        self.temperature_celsius: float = 22.0
        self.humidity_pct: float = 50.0
        self.cooling_efficiency: float = 1.0
        self.power_distribution_losses: float = 0.0
        self.rack_power_distribution: dict[str, float] = {}

    def calculate_pue(self):
        if self.it_power_kw > 0:
            self.pue = round(self.facility_power_kw / self.it_power_kw, 2)
        else:
            self.pue = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "facility_power_kw": round(self.facility_power_kw, 2),
            "it_power_kw": round(self.it_power_kw, 2),
            "cooling_power_kw": round(self.cooling_power_kw, 2),
            "pue": self.pue,
            "temperature_celsius": self.temperature_celsius,
            "humidity_pct": self.humidity_pct,
            "cooling_efficiency": round(self.cooling_efficiency, 2),
            "power_distribution_losses": round(self.power_distribution_losses, 2),
            "rack_count": len(self.rack_power_distribution),
        }


class CoolingUnit:
    """A cooling unit in the data center."""

    def __init__(self, unit_id: str, name: str, cooling_type: CoolingType):
        self.unit_id = unit_id
        self.name = name
        self.cooling_type = cooling_type
        self.capacity_kw: float = 100.0
        self.current_load_kw: float = 0.0
        self.setpoint_celsius: float = 22.0
        self.return_temp_celsius: float = 26.0
        self.supply_temp_celsius: float = 18.0
        self.fan_speed_pct: float = 50.0
        self.status: str = "running"
        self.energy_kwh_today: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "name": self.name,
            "cooling_type": self.cooling_type.value,
            "capacity_kw": self.capacity_kw,
            "current_load_kw": round(self.current_load_kw, 2),
            "load_pct": round(self.current_load_kw / self.capacity_kw * 100, 1),
            "setpoint_celsius": self.setpoint_celsius,
            "return_temp_celsius": self.return_temp_celsius,
            "supply_temp_celsius": self.supply_temp_celsius,
            "fan_speed_pct": self.fan_speed_pct,
            "status": self.status,
            "energy_kwh_today": round(self.energy_kwh_today, 2),
        }


class PDUPower:
    """Power distribution unit reading."""

    def __init__(self, pdu_id: str, name: str, rack: str):
        self.pdu_id = pdu_id
        self.name = name
        self.rack = rack
        self.input_power_watts: float = 0.0
        self.output_power_watts: float = 0.0
        self.input_voltage: float = 208.0
        self.load_pct: float = 0.0
        self.outlets: dict[str, float] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdu_id": self.pdu_id,
            "name": self.name,
            "rack": self.rack,
            "input_power_watts": round(self.input_power_watts, 1),
            "output_power_watts": round(self.output_power_watts, 1),
            "input_voltage": self.input_voltage,
            "load_pct": round(self.load_pct, 1),
            "outlet_count": len(self.outlets),
        }


class PUEDCIMIntegration:
    """PUE / DCIM integration manager."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.dcim_system: Optional[DCIMSystem] = None
        self.dcim_config: dict[str, Any] = {}
        self.measurements: list[DCIMMetrics] = []
        self.cooling_units: dict[str, CoolingUnit] = {}
        self.pdus: dict[str, PDUPower] = {}
        self._collection_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        self.cooling_units["crac-01"] = CoolingUnit("crac-01", "CRAC Row A", CoolingType.CRAC)
        self.cooling_units["crac-01"].capacity_kw = 75.0
        self.cooling_units["crac-01"].current_load_kw = 42.5

        self.cooling_units["crac-02"] = CoolingUnit("crac-02", "CRAC Row B", CoolingType.CRAC)
        self.cooling_units["crac-02"].capacity_kw = 75.0
        self.cooling_units["crac-02"].current_load_kw = 38.2

        self.cooling_units["crah-01"] = CoolingUnit("crah-01", "CRAH Row C", CoolingType.CRAH)
        self.crah_energy = 28.5
        self.cooling_units["crah-01"].capacity_kw = 120.0
        self.cooling_units["crah-01"].current_load_kw = 45.0

        self.cooling_units["chiller-01"] = CoolingUnit("chiller-01", "Main Chiller", CoolingType.CHILLER)
        self.cooling_units["chiller-01"].capacity_kw = 300.0
        self.cooling_units["chiller-01"].current_load_kw = 120.0

        for i in range(6):
            pdu_id = f"pdu-{chr(65 + i)}"
            rack = f"R{chr(65 + i)}{random.randint(1, 20):02d}"
            pdu = PDUPower(pdu_id, f"PDU-{chr(65 + i)}", rack)
            pdu.input_power_watts = random.uniform(3000, 12000)
            pdu.output_power_watts = pdu.input_power_watts * random.uniform(0.88, 0.96)
            pdu.load_pct = pdu.input_power_watts / 15000 * 100
            for j in range(random.randint(4, 12)):
                pdu.outlets[f"outlet-{j:02d}"] = random.uniform(100, 1500)
            self.pdus[pdu_id] = pdu

        for i in range(500):
            metrics = DCIMMetrics()
            metrics.timestamp = datetime.utcnow() - timedelta(minutes=i * 15)
            metrics.it_power_kw = random.uniform(180, 260)
            metrics.cooling_power_kw = random.uniform(40, 80)
            metrics.power_distribution_losses = random.uniform(5, 15)
            metrics.facility_power_kw = (metrics.it_power_kw + metrics.cooling_power_kw
                                          + metrics.power_distribution_losses)
            metrics.calculate_pue()
            metrics.temperature_celsius = random.uniform(20, 26)
            metrics.humidity_pct = random.uniform(40, 60)
            self.measurements.append(metrics)

    async def initialize(self):
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("PUEDCIMIntegration initialized")

    async def close(self):
        if self._collection_task:
            self._collection_task.cancel()
        logger.info("PUEDCIMIntegration closed")

    async def _collection_loop(self):
        while True:
            try:
                await asyncio.sleep(900)
                self._collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Collection error: %s", e)

    def _collect_metrics(self):
        metrics = DCIMMetrics()
        metrics.it_power_kw = random.uniform(180, 260)
        metrics.cooling_power_kw = random.uniform(40, 80)
        metrics.power_distribution_losses = random.uniform(5, 15)
        metrics.facility_power_kw = (metrics.it_power_kw + metrics.cooling_power_kw
                                      + metrics.power_distribution_losses)
        metrics.calculate_pue()
        metrics.temperature_celsius = random.uniform(20, 26)
        metrics.humidity_pct = random.uniform(40, 60)
        for pdu in self.pdus.values():
            pdu.input_power_watts = random.uniform(3000, 12000)
            pdu.load_pct = pdu.input_power_watts / 15000 * 100
        for cu in self.cooling_units.values():
            cu.current_load_kw = random.uniform(30, 70) * cu.capacity_kw / 100
            cu.energy_kwh_today += cu.current_load_kw * 0.25
        self.measurements.append(metrics)
        if len(self.measurements) > 100000:
            self.measurements = self.measurements[-50000:]

    def configure_dcim(self, system: str, config: dict) -> None:
        try:
            self.dcim_system = DCIMSystem(system)
        except ValueError:
            self.dcim_system = DCIMSystem.OPEN_DCIM
        self.dcim_config = config

    def get_current_metrics(self) -> dict:
        if self.measurements:
            return self.measurements[-1].to_dict()
        return DCIMMetrics().to_dict()

    def get_pue_history(self, hours: int = 168) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [m.to_dict() for m in self.measurements if m.timestamp > cutoff]

    def get_cooling_status(self) -> list[dict]:
        return [cu.to_dict() for cu in self.cooling_units.values()]

    def get_pdu_status(self) -> list[dict]:
        return [pdu.to_dict() for pdu in self.pdus.values()]

    def get_statistics(self) -> dict[str, Any]:
        recent = [m for m in self.measurements[-100:] if m.pue >= 1.0]
        if not recent:
            return {"avg_pue": 1.0, "min_pue": 1.0, "max_pue": 1.0}
        avg_pue = sum(m.pue for m in recent) / len(recent)
        min_pue = min(m.pue for m in recent)
        max_pue = max(m.pue for m in recent)
        total_cooling = sum(cu.current_load_kw for cu in self.cooling_units.values())
        avg_temp = sum(m.temperature_celsius for m in recent) / len(recent)
        return {
            "avg_pue": round(avg_pue, 2),
            "min_pue": round(min_pue, 2),
            "max_pue": round(max_pue, 2),
            "current_it_power_kw": recent[-1].it_power_kw if recent else 0,
            "current_cooling_kw": round(total_cooling, 2),
            "current_pue": recent[-1].pue if recent else 1.0,
            "avg_temperature": round(avg_temp, 1),
            "avg_humidity": round(sum(m.humidity_pct for m in recent) / len(recent), 1),
            "cooling_units": len(self.cooling_units),
            "pdus": len(self.pdus),
            "measurements_count": len(self.measurements),
            "dcim_connected": self.dcim_system is not None,
        }

    def generate_report(self) -> dict[str, Any]:
        stats = self.get_statistics()
        pue_class = "Excellent" if stats["avg_pue"] < 1.2 else \
                    "Good" if stats["avg_pue"] < 1.4 else \
                    "Average" if stats["avg_pue"] < 1.6 else \
                    "Poor" if stats["avg_pue"] < 2.0 else "Very Poor"
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "pue_classification": pue_class,
            "statistics": stats,
            "cooling_breakdown": {
                cu.cooling_type.value: {
                    "units": sum(1 for c in self.cooling_units.values() if c.cooling_type == ct),
                    "total_load_kw": round(sum(c.current_load_kw for c in self.cooling_units.values()
                                                if c.cooling_type == ct), 2),
                }
                for ct in set(cu.cooling_type for cu in self.cooling_units.values())
            },
            "pdu_total_power_kw": round(
                sum(pdu.input_power_watts for pdu in self.pdus.values()) / 1000, 2
            ),
        }
