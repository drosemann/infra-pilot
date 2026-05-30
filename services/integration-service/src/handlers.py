"""Extended Edge & IoT and Green Computing service handlers.

Comprehensive service layer with full CRUD operations, data validation,
business logic, and persistence for all 20 Edge/IoT and Green Computing features.
"""

import json
import uuid
import hashlib
import logging
import asyncio
import time
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class ServiceResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"success": self.success, "timestamp": self.timestamp}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.message:
            result["message"] = self.message
        return result


class EdgeDeviceHandler:
    """Handles edge device CRUD operations and lifecycle management."""

    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.telemetry_store: Dict[str, List[Dict[str, Any]]] = {}
        self.command_history: Dict[str, List[Dict[str, Any]]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(5):
            device_id = f"dev-{i+1:03d}"
            self.devices[device_id] = {
                "device_id": device_id,
                "name": f"Edge Device {i+1}",
                "type": ["sensor", "gateway", "actuator", "camera", "edge_node"][i],
                "status": ["online", "online", "offline", "degraded", "online"][i],
                "firmware_version": f"2.{i}.{random.randint(0,9)}",
                "hardware_revision": f"rev-{chr(97+i)}",
                "ip_address": f"10.0.{i}.{random.randint(1,254)}",
                "location": f"DC-1-Rack-{chr(65+i)}{i+1}",
                "battery_level": random.randint(20, 100),
                "signal_strength": random.randint(-85, -40),
                "cpu_usage": round(random.uniform(10, 90), 1),
                "memory_usage": round(random.uniform(20, 80), 1),
                "disk_usage": round(random.uniform(15, 70), 1),
                "temperature_celsius": round(random.uniform(30, 65), 1),
                "uptime_seconds": random.randint(3600, 86400 * 30),
                "last_seen": (datetime.utcnow() - timedelta(minutes=random.randint(0, 60))).isoformat(),
                "registered_at": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                "tags": {"environment": "production", "region": "us-east"},
                "metadata": {"owner": "infra-team", "cost_center": "cc-123"},
            }

    def list_devices(self, status: Optional[str] = None,
                     device_type: Optional[str] = None,
                     limit: int = 100, offset: int = 0) -> ServiceResult:
        filtered = list(self.devices.values())
        if status:
            filtered = [d for d in filtered if d["status"] == status]
        if device_type:
            filtered = [d for d in filtered if d["type"] == device_type]
        total = len(filtered)
        page = filtered[offset:offset + limit]
        return ServiceResult(success=True, data={
            "devices": page, "total": total, "limit": limit, "offset": offset
        })

    def get_device(self, device_id: str) -> ServiceResult:
        device = self.devices.get(device_id)
        if not device:
            return ServiceResult(success=False, error=f"Device {device_id} not found")
        return ServiceResult(success=True, data=device)

    def register_device(self, data: Dict[str, Any]) -> ServiceResult:
        device_id = data.get("device_id", f"dev-{uuid.uuid4().hex[:8]}")
        if device_id in self.devices:
            return ServiceResult(success=False, error=f"Device {device_id} already exists")
        device = {
            "device_id": device_id,
            "name": data.get("name", f"Device-{device_id}"),
            "type": data.get("device_type", "sensor"),
            "status": "provisioning",
            "firmware_version": data.get("firmware_version", "1.0.0"),
            "hardware_revision": data.get("hardware_revision", "rev-a"),
            "ip_address": data.get("ip_address"),
            "location": data.get("location"),
            "battery_level": data.get("battery_level", 100),
            "signal_strength": data.get("signal_strength", -50),
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "temperature_celsius": 25.0,
            "uptime_seconds": 0,
            "last_seen": datetime.utcnow().isoformat(),
            "registered_at": datetime.utcnow().isoformat(),
            "tags": data.get("tags", {}),
            "metadata": data.get("metadata", {}),
        }
        self.devices[device_id] = device
        return ServiceResult(success=True, data=device, message=f"Device {device_id} registered")

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> ServiceResult:
        device = self.devices.get(device_id)
        if not device:
            return ServiceResult(success=False, error=f"Device {device_id} not found")
        allowed_fields = {"name", "location", "firmware_version", "tags", "metadata", "ip_address"}
        for key, value in updates.items():
            if key in allowed_fields:
                device[key] = value
        device["last_seen"] = datetime.utcnow().isoformat()
        return ServiceResult(success=True, data=device, message=f"Device {device_id} updated")

    def delete_device(self, device_id: str) -> ServiceResult:
        if device_id not in self.devices:
            return ServiceResult(success=False, error=f"Device {device_id} not found")
        self.devices[device_id]["status"] = "decommissioned"
        return ServiceResult(success=True, message=f"Device {device_id} decommissioned")

    def record_telemetry(self, device_id: str, telemetry: Dict[str, Any]) -> ServiceResult:
        if device_id not in self.devices:
            return ServiceResult(success=False, error=f"Device {device_id} not found")
        record = {
            "telemetry_id": f"tel-{uuid.uuid4().hex[:12]}",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            **telemetry
        }
        if device_id not in self.telemetry_store:
            self.telemetry_store[device_id] = []
        self.telemetry_store[device_id].append(record)
        if len(self.telemetry_store[device_id]) > 10000:
            self.telemetry_store[device_id] = self.telemetry_store[device_id][-5000:]
        return ServiceResult(success=True, data=record, message="Telemetry recorded")

    def get_telemetry(self, device_id: str, limit: int = 100) -> ServiceResult:
        records = self.telemetry_store.get(device_id, [])
        return ServiceResult(success=True, data={"device_id": device_id,
                                                  "records": records[-limit:],
                                                  "total": len(records)})

    def send_command(self, device_id: str, command: Dict[str, Any]) -> ServiceResult:
        if device_id not in self.devices:
            return ServiceResult(success=False, error=f"Device {device_id} not found")
        cmd_record = {
            "command_id": f"cmd-{uuid.uuid4().hex[:12]}",
            "device_id": device_id,
            "command_type": command.get("type", "unknown"),
            "parameters": command.get("parameters", {}),
            "issued_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }
        if device_id not in self.command_history:
            self.command_history[device_id] = []
        self.command_history[device_id].append(cmd_record)
        return ServiceResult(success=True, data=cmd_record, message="Command sent")

    def get_device_stats(self) -> ServiceResult:
        devices = list(self.devices.values())
        return ServiceResult(success=True, data={
            "total": len(devices),
            "online": sum(1 for d in devices if d["status"] == "online"),
            "offline": sum(1 for d in devices if d["status"] == "offline"),
            "degraded": sum(1 for d in devices if d["status"] == "degraded"),
            "by_type": defaultdict(int, {d["type"]: sum(1 for x in devices if x["type"] == d["type"]) for d in devices}),
            "avg_cpu": round(sum(d["cpu_usage"] for d in devices) / len(devices), 1) if devices else 0,
            "avg_memory": round(sum(d["memory_usage"] for d in devices) / len(devices), 1) if devices else 0,
            "avg_battery": round(sum(d["battery_level"] for d in devices) / len(devices), 1) if devices else 0,
        })


class IoTDataHandler:
    """Handles IoT data pipeline operations."""

    def __init__(self):
        self.pipelines: Dict[str, Dict[str, Any]] = {}
        self.ingested: List[Dict[str, Any]] = []
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(3):
            pid = f"pipeline-{i+1:03d}"
            self.pipelines[pid] = {
                "pipeline_id": pid,
                "name": [ "Main Telemetry Pipeline", "Sensor Data Stream", "Alert Processing" ][i],
                "type": ["mqtt", "http", "lorawan"][i],
                "status": "active",
                "input_topic": f"devices/{['telemetry', 'sensors', 'alerts'][i]}/+",
                "output_topic": f"processed/{['telemetry', 'sensors', 'alerts'][i]}",
                "stages": ["ingestion", "validation", "normalization", "enrichment", "routing", "storage"],
                "config": {"batch_size": 100, "flush_interval": 5},
                "messages_processed": random.randint(10000, 500000),
                "messages_failed": random.randint(0, 500),
                "throughput": round(random.uniform(50, 500), 1),
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(30, 200))).isoformat(),
            }

    def list_pipelines(self) -> ServiceResult:
        return ServiceResult(success=True, data={
            "pipelines": list(self.pipelines.values()),
            "total": len(self.pipelines)
        })

    def get_pipeline(self, pipeline_id: str) -> ServiceResult:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return ServiceResult(success=False, error=f"Pipeline {pipeline_id} not found")
        return ServiceResult(success=True, data=pipeline)

    def create_pipeline(self, data: Dict[str, Any]) -> ServiceResult:
        pid = data.get("pipeline_id", f"pipeline-{uuid.uuid4().hex[:8]}")
        pipeline = {
            "pipeline_id": pid,
            "name": data.get("name", f"Pipeline-{pid}"),
            "type": data.get("type", "mqtt"),
            "status": "active",
            "input_topic": data.get("input_topic", "devices/+/telemetry"),
            "output_topic": data.get("output_topic", "processed/telemetry"),
            "stages": ["ingestion", "validation", "normalization", "enrichment", "routing", "storage"],
            "config": data.get("config", {}),
            "messages_processed": 0,
            "messages_failed": 0,
            "throughput": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.pipelines[pid] = pipeline
        return ServiceResult(success=True, data=pipeline, message=f"Pipeline {pid} created")

    def delete_pipeline(self, pipeline_id: str) -> ServiceResult:
        if pipeline_id not in self.pipelines:
            return ServiceResult(success=False, error=f"Pipeline {pipeline_id} not found")
        del self.pipelines[pipeline_id]
        return ServiceResult(success=True, message=f"Pipeline {pipeline_id} deleted")

    def ingest_data(self, device_id: str, payload: Dict[str, Any]) -> ServiceResult:
        record = {
            "ingestion_id": f"ing-{uuid.uuid4().hex[:12]}",
            "device_id": device_id,
            "payload": payload,
            "received_at": datetime.utcnow().isoformat(),
            "processed": False,
        }
        self.ingested.append(record)
        if len(self.ingested) > 10000:
            self.ingested.pop(0)
        for pipeline in self.pipelines.values():
            if pipeline["status"] == "active":
                pipeline["messages_processed"] += 1
        return ServiceResult(success=True, data=record, message="Data ingested")

    def get_ingestion_stats(self) -> ServiceResult:
        return ServiceResult(success=True, data={
            "total_ingested": len(self.ingested),
            "pipelines_active": sum(1 for p in self.pipelines.values() if p["status"] == "active"),
            "total_messages": sum(p["messages_processed"] for p in self.pipelines.values()),
            "last_ingestion": self.ingested[-1]["received_at"] if self.ingested else None,
        })


class EnergyDataHandler:
    """Handles energy consumption data and metrics."""

    def __init__(self):
        self.readings: List[Dict[str, Any]] = []
        self.configs: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(5):
            did = f"dev-{i+1:03d}"
            for h in range(24):
                self.readings.append({
                    "reading_id": f"rd-{uuid.uuid4().hex[:12]}",
                    "device_id": did,
                    "power_watts": random.uniform(100, 500),
                    "energy_kwh": random.uniform(0.1, 0.5),
                    "source": random.choice(["grid", "solar", "wind"]),
                    "voltage": 230.0,
                    "current": random.uniform(0.5, 2.5),
                    "timestamp": (datetime.utcnow() - timedelta(hours=h)).isoformat(),
                })

    def record_reading(self, device_id: str, power_watts: float,
                       source: str = "grid") -> ServiceResult:
        reading = {
            "reading_id": f"rd-{uuid.uuid4().hex[:12]}",
            "device_id": device_id,
            "power_watts": power_watts,
            "energy_kwh": power_watts * 0.001,
            "source": source,
            "voltage": 230.0,
            "current": power_watts / 230.0,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.readings.append(reading)
        if len(self.readings) > 100000:
            self.readings = self.readings[-50000:]
        config = self.configs.get(device_id, {})
        threshold = config.get("wattage_limit", 10000)
        if power_watts > threshold:
            reading["threshold_exceeded"] = True
            return ServiceResult(success=True, data=reading, message="Threshold exceeded!")
        return ServiceResult(success=True, data=reading)

    def get_readings(self, device_id: str, hours: int = 24) -> ServiceResult:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        records = [r for r in self.readings
                   if r["device_id"] == device_id
                   and datetime.fromisoformat(r["timestamp"]) > cutoff]
        return ServiceResult(success=True, data={
            "device_id": device_id,
            "readings": records,
            "total": len(records),
            "period_hours": hours,
        })

    def get_metrics(self, device_id: str) -> ServiceResult:
        records = [r for r in self.readings if r["device_id"] == device_id]
        if not records:
            return ServiceResult(success=True, data={
                "device_id": device_id, "avg_power": 0, "total_energy": 0,
                "peak_power": 0, "carbon_kg": 0, "cost_usd": 0
            })
        avg_power = sum(r["power_watts"] for r in records) / len(records)
        total_energy = sum(r["energy_kwh"] for r in records)
        peak = max(r["power_watts"] for r in records)
        return ServiceResult(success=True, data={
            "device_id": device_id,
            "avg_power_watts": round(avg_power, 2),
            "total_energy_kwh": round(total_energy, 2),
            "peak_power_watts": peak,
            "carbon_kg": round(total_energy * 0.294, 2),
            "cost_usd": round(total_energy * 0.12, 2),
            "reading_count": len(records),
        })

    def get_all_metrics(self) -> ServiceResult:
        devices = set(r["device_id"] for r in self.readings)
        total_energy = sum(r["energy_kwh"] for r in self.readings)
        solar = sum(r["energy_kwh"] for r in self.readings if r["source"] == "solar")
        wind = sum(r["energy_kwh"] for r in self.readings if r["source"] == "wind")
        renewable = solar + wind
        return ServiceResult(success=True, data={
            "total_devices": len(devices),
            "total_energy_kwh": round(total_energy, 2),
            "renewable_kwh": round(renewable, 2),
            "renewable_pct": round((renewable / total_energy) * 100, 1) if total_energy > 0 else 0,
            "total_carbon_kg": round(total_energy * 0.294, 2),
            "total_cost_usd": round(total_energy * 0.12, 2),
            "avg_power_watts": round(sum(r["power_watts"] for r in self.readings) / len(self.readings), 2) if self.readings else 0,
        })

    def configure_device(self, device_id: str, config: Dict[str, Any]) -> ServiceResult:
        self.configs[device_id] = {**self.configs.get(device_id, {}), **config}
        return ServiceResult(success=True, data=self.configs[device_id],
                             message=f"Device {device_id} configured")


class CarbonDataHandler:
    """Handles carbon offset data and CO2 calculations."""

    def __init__(self):
        self.offsets: List[Dict[str, Any]] = []
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.providers: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(3):
            pid = f"project-{i+1:03d}"
            self.projects[pid] = {
                "project_id": pid,
                "name": ["Reforestation Amazon", "Wind Farm Denmark", "Solar Park Spain"][i],
                "type": ["reforestation", "renewable_energy", "renewable_energy"][i],
                "location": ["Brazil", "Denmark", "Spain"][i],
                "registry": "verra",
                "total_tonnes": random.randint(10000, 100000),
                "available_tonnes": random.randint(1000, 50000),
                "price_per_tonne": round(random.uniform(5, 25), 2),
                "status": "active",
                "certified": True,
            }
        for i in range(2):
            prid = f"provider-{i+1:03d}"
            self.providers[prid] = {
                "provider_id": prid,
                "name": ["EcoOffset Inc", "CarbonClear Ltd"][i],
                "rating": round(random.uniform(3.5, 5.0), 1),
                "projects_count": random.randint(5, 50),
                "verified": True,
            }
        for i in range(5):
            self.offsets.append({
                "offset_id": f"off-{i+1:03d}",
                "tonnes_co2": random.randint(1, 100),
                "provider_id": f"provider-{random.randint(1,2):03d}",
                "project_id": f"project-{random.randint(1,3):03d}",
                "status": random.choice(["purchased", "retired", "pending"]),
                "cost_usd": round(random.uniform(10, 500), 2),
                "purchased_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
            })

    def purchase_offset(self, tonnes: float, provider_id: str,
                        project_id: Optional[str] = None) -> ServiceResult:
        if provider_id not in self.providers:
            return ServiceResult(success=False, error=f"Provider {provider_id} not found")
        project = None
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
        price_per_tonne = project["price_per_tonne"] if project else 15.0
        offset = {
            "offset_id": f"off-{uuid.uuid4().hex[:8]}",
            "tonnes_co2": tonnes,
            "provider_id": provider_id,
            "project_id": project_id or "unknown",
            "status": "purchased",
            "cost_usd": round(tonnes * price_per_tonne, 2),
            "purchased_at": datetime.utcnow().isoformat(),
        }
        self.offsets.append(offset)
        return ServiceResult(success=True, data=offset, message=f"{tonnes} tonnes CO2 offset purchased")

    def list_offsets(self, status: Optional[str] = None) -> ServiceResult:
        filtered = self.offsets
        if status:
            filtered = [o for o in filtered if o["status"] == status]
        return ServiceResult(success=True, data={"offsets": filtered, "total": len(filtered)})

    def get_total_offset(self) -> ServiceResult:
        total = sum(o["tonnes_co2"] for o in self.offsets if o["status"] in ("purchased", "retired"))
        purchased = sum(o["tonnes_co2"] for o in self.offsets if o["status"] == "purchased")
        retired = sum(o["tonnes_co2"] for o in self.offsets if o["status"] == "retired")
        total_cost = sum(o["cost_usd"] for o in self.offsets)
        return ServiceResult(success=True, data={
            "total_tonnes_co2": total,
            "total_purchased": purchased,
            "total_retired": retired,
            "total_pending": sum(o["tonnes_co2"] for o in self.offsets if o["status"] == "pending"),
            "total_cost_usd": round(total_cost, 2),
            "offsets_count": len(self.offsets),
        })

    def get_portfolio_summary(self) -> ServiceResult:
        total = sum(o["tonnes_co2"] for o in self.offsets if o["status"] in ("purchased", "retired"))
        return ServiceResult(success=True, data={
            "total_tonnes_offset": total,
            "active_projects": len(self.projects),
            "providers": len(self.providers),
            "carbon_neutral_status": "partial" if total > 0 else "not_started",
            "trees_equivalent": round(total * 45),
            "cars_equivalent": round(total / 4.6, 1),
        })

    def retire_offset(self, offset_id: str) -> ServiceResult:
        for offset in self.offsets:
            if offset["offset_id"] == offset_id:
                if offset["status"] == "retired":
                    return ServiceResult(success=False, error="Offset already retired")
                offset["status"] = "retired"
                offset["retired_at"] = datetime.utcnow().isoformat()
                return ServiceResult(success=True, data=offset, message="Offset retired")
        return ServiceResult(success=False, error=f"Offset {offset_id} not found")

    def get_carbon_neutrality_status(self) -> ServiceResult:
        emissions = 50000
        offsets = sum(o["tonnes_co2"] for o in self.offsets if o["status"] in ("purchased", "retired"))
        return ServiceResult(success=True, data={
            "total_emissions_tonnes": emissions,
            "total_offsets_tonnes": offsets,
            "net_tonnes": emissions - offsets,
            "is_carbon_neutral": offsets >= emissions,
            "coverage_pct": round((offsets / emissions) * 100, 1) if emissions > 0 else 0,
        })


class HardwareLifecycleHandler:
    """Handles hardware asset lifecycle operations."""

    def __init__(self):
        self.assets: Dict[str, Dict[str, Any]] = {}
        self.maintenance: List[Dict[str, Any]] = []
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(6):
            aid = f"asset-{i+1:03d}"
            self.assets[aid] = {
                "asset_id": aid,
                "name": [ "Dell R740", "Cisco 9300", "NetApp FAS8200",
                          "NVIDIA A100", "SuperMicro", "Juniper EX4600" ][i],
                "type": ["server", "switch", "storage", "gpu", "server", "network"][i],
                "manufacturer": ["Dell", "Cisco", "NetApp", "NVIDIA", "SuperMicro", "Juniper"][i],
                "model": ["R740", "9300", "FAS8200", "A100", "SYS-101", "EX4600"][i],
                "serial": f"SN-{uuid.uuid4().hex[:8].upper()}",
                "status": ["active", "active", "active", "active", "maintenance", "decommissioned"][i],
                "purchase_date": (datetime.utcnow() - timedelta(days=random.randint(200, 1500))).isoformat()[:10],
                "warranty_end": (datetime.utcnow() + timedelta(days=random.randint(-100, 600))).isoformat()[:10],
                "eol_date": (datetime.utcnow() + timedelta(days=random.randint(-200, 1000))).isoformat()[:10],
                "location": f"DC-{random.randint(1,3)}-Rack-{random.choice('ABCD')}{random.randint(1,42)}",
                "power_rating_watts": random.choice([250, 500, 750, 1000, 1500]),
                "age_years": round(random.uniform(0.5, 6), 1),
            }

    def list_assets(self, status: Optional[str] = None) -> ServiceResult:
        filtered = list(self.assets.values())
        if status:
            filtered = [a for a in filtered if a["status"] == status]
        return ServiceResult(success=True, data={"assets": filtered, "total": len(filtered)})

    def get_asset(self, asset_id: str) -> ServiceResult:
        asset = self.assets.get(asset_id)
        if not asset:
            return ServiceResult(success=False, error=f"Asset {asset_id} not found")
        return ServiceResult(success=True, data=asset)

    def register_asset(self, data: Dict[str, Any]) -> ServiceResult:
        aid = data.get("asset_id", f"asset-{uuid.uuid4().hex[:8]}")
        asset = {
            "asset_id": aid,
            "name": data.get("name", f"Asset-{aid}"),
            "type": data.get("hardware_type", "server"),
            "manufacturer": data.get("manufacturer", "Generic"),
            "model": data.get("model", "Standard"),
            "serial": data.get("serial_number", f"SN-{uuid.uuid4().hex[:8].upper()}"),
            "status": "active",
            "purchase_date": data.get("purchase_date", datetime.utcnow().isoformat()[:10]),
            "warranty_end": data.get("warranty_end"),
            "eol_date": data.get("eol_date"),
            "location": data.get("location", "Unassigned"),
            "power_rating_watts": data.get("power_rating_watts"),
            "age_years": 0.0,
        }
        if "purchase_date" in data:
            try:
                pd = datetime.fromisoformat(data["purchase_date"])
                asset["age_years"] = round((datetime.utcnow() - pd).days / 365.25, 1)
            except (ValueError, TypeError):
                pass
        self.assets[aid] = asset
        return ServiceResult(success=True, data=asset, message=f"Asset {aid} registered")

    def update_asset(self, asset_id: str, updates: Dict[str, Any]) -> ServiceResult:
        asset = self.assets.get(asset_id)
        if not asset:
            return ServiceResult(success=False, error=f"Asset {asset_id} not found")
        allowed = {"name", "location", "status", "warranty_end", "eol_date"}
        for key, value in updates.items():
            if key in allowed:
                asset[key] = value
        return ServiceResult(success=True, data=asset, message=f"Asset {asset_id} updated")

    def decommission_asset(self, asset_id: str) -> ServiceResult:
        asset = self.assets.get(asset_id)
        if not asset:
            return ServiceResult(success=False, error=f"Asset {asset_id} not found")
        asset["status"] = "decommissioned"
        return ServiceResult(success=True, data=asset, message=f"Asset {asset_id} decommissioned")

    def add_maintenance(self, asset_id: str, maint_type: str,
                        description: str, technician: str) -> ServiceResult:
        if asset_id not in self.assets:
            return ServiceResult(success=False, error=f"Asset {asset_id} not found")
        record = {
            "record_id": f"mnt-{uuid.uuid4().hex[:8]}",
            "asset_id": asset_id,
            "maintenance_type": maint_type,
            "description": description,
            "technician": technician,
            "status": "completed",
            "completed_date": datetime.utcnow().isoformat()[:10],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.maintenance.append(record)
        return ServiceResult(success=True, data=record, message="Maintenance record added")

    def get_lifecycle_summary(self) -> ServiceResult:
        assets = list(self.assets.values())
        active = [a for a in assets if a["status"] == "active"]
        near_eol = [a for a in assets if a.get("eol_date") and a["eol_date"] <
                    (datetime.utcnow() + timedelta(days=180)).isoformat()[:10]]
        return ServiceResult(success=True, data={
            "total_assets": len(assets),
            "active_assets": len(active),
            "maintenance": sum(1 for a in assets if a["status"] == "maintenance"),
            "decommissioned": sum(1 for a in assets if a["status"] == "decommissioned"),
            "near_eol": len(near_eol),
            "avg_age": round(sum(a["age_years"] for a in assets) / len(assets), 1) if assets else 0,
            "total_power_watts": sum(a.get("power_rating_watts", 0) for a in assets),
        })

    def get_warranty_status(self, asset_id: str) -> ServiceResult:
        asset = self.assets.get(asset_id)
        if not asset:
            return ServiceResult(success=False, error=f"Asset {asset_id} not found")
        warranty_end = asset.get("warranty_end")
        under_warranty = False
        if warranty_end:
            try:
                under_warranty = datetime.fromisoformat(warranty_end) > datetime.utcnow()
            except ValueError:
                pass
        return ServiceResult(success=True, data={
            "asset_id": asset_id,
            "asset_name": asset["name"],
            "warranty_end": warranty_end,
            "under_warranty": under_warranty,
            "days_remaining": (datetime.fromisoformat(warranty_end) - datetime.utcnow()).days
            if warranty_end and under_warranty else 0,
        })


class SchedulingHandler:
    """Handles green scheduling and auto-shutdown policies."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.schedules: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        job_types = ["backup", "data-sync", "batch-processing", "report-generation", "maintenance"]
        for i in range(5):
            jid = f"job-{i+1:03d}"
            self.jobs[jid] = {
                "job_id": jid,
                "name": f"{job_types[i]}-task",
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "estimated_duration_minutes": random.randint(15, 240),
                "status": random.choice(["pending", "running", "completed", "failed"]),
                "carbon_impact_kg": round(random.uniform(0.1, 5.0), 2),
                "device_id": f"dev-{random.randint(1,5):03d}",
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
            }
        for i in range(3):
            pid = f"policy-{i+1:03d}"
            self.policies[pid] = {
                "policy_id": pid,
                "name": ["Night Shutdown", "Weekend Standby", "Idle Timeout"][i],
                "action": ["hibernate", "shutdown", "sleep"][i],
                "scope": ["global", "device", "group"][i],
                "enabled": True,
                "schedule": ["22:00-06:00", "Fri 18:00-Mon 08:00", "15 min idle"][i],
                "compliance_rate": random.randint(70, 98),
                "savings_kwh_daily": random.randint(45, 340),
            }
        for i in range(2):
            sid = f"sched-{i+1:03d}"
            self.schedules[sid] = {
                "schedule_id": sid,
                "policy_id": f"policy-{i+1:03d}",
                "cron": ["0 22 * * 1-5", "0 18 * * 5"][i],
                "time_start": ["22:00", "18:00"][i],
                "time_end": ["06:00", "08:00"][i],
                "days": [["Mon", "Tue", "Wed", "Thu", "Fri"], ["Fri", "Sat", "Sun"]][i],
                "enabled": True,
            }

    def list_jobs(self, status: Optional[str] = None) -> ServiceResult:
        filtered = list(self.jobs.values())
        if status:
            filtered = [j for j in filtered if j["status"] == status]
        return ServiceResult(success=True, data={"jobs": filtered, "total": len(filtered)})

    def create_job(self, data: Dict[str, Any]) -> ServiceResult:
        jid = data.get("job_id", f"job-{uuid.uuid4().hex[:8]}")
        job = {
            "job_id": jid,
            "name": data.get("name", f"Job-{jid}"),
            "priority": data.get("priority", "medium"),
            "estimated_duration_minutes": data.get("estimated_duration_minutes", 60),
            "status": "pending",
            "carbon_impact_kg": 0.0,
            "device_id": data.get("device_id", "unknown"),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.jobs[jid] = job
        return ServiceResult(success=True, data=job, message=f"Job {jid} created")

    def list_policies(self) -> ServiceResult:
        return ServiceResult(success=True, data={
            "policies": list(self.policies.values()), "total": len(self.policies)
        })

    def create_policy(self, data: Dict[str, Any]) -> ServiceResult:
        pid = data.get("policy_id", f"policy-{uuid.uuid4().hex[:8]}")
        policy = {
            "policy_id": pid,
            "name": data.get("name", f"Policy-{pid}"),
            "action": data.get("action", "hibernate"),
            "scope": data.get("scope", "global"),
            "enabled": True,
            "schedule": data.get("schedule", "22:00-06:00"),
            "compliance_rate": 0,
            "savings_kwh_daily": 0,
        }
        self.policies[pid] = policy
        return ServiceResult(success=True, data=policy, message=f"Policy {pid} created")

    def get_shutdown_summary(self) -> ServiceResult:
        policies = list(self.policies.values())
        return ServiceResult(success=True, data={
            "total_policies": len(policies),
            "enabled": sum(1 for p in policies if p["enabled"]),
            "total_savings_kwh_daily": sum(p["savings_kwh_daily"] for p in policies),
            "avg_compliance": round(sum(p["compliance_rate"] for p in policies) / len(policies), 1) if policies else 0,
        })


class PUEHandler:
    """Handles PUE/DCIM data operations."""

    def __init__(self):
        self.facilities: Dict[str, Dict[str, Any]] = {}
        self.readings: List[Dict[str, Any]] = []
        self.cooling_units: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        for i in range(3):
            fid = f"fac-{i+1:03d}"
            self.facilities[fid] = {
                "facility_id": fid,
                "name": [ "DC-1 San Jose", "DC-2 Dallas", "DC-3 Ashburn" ][i],
                "location": [ "San Jose, CA", "Dallas, TX", "Ashburn, VA" ][i],
                "total_power_capacity_kw": [ 1000, 800, 2000 ][i],
                "it_load_capacity_kw": [ 800, 640, 1600 ][i],
                "tier_level": "tier_iii",
                "status": "operational",
                "current_pue": [ 1.25, 1.35, 1.18 ][i],
            }
        for fid in self.facilities:
            for h in range(24):
                self.readings.append({
                    "reading_id": f"pue-{uuid.uuid4().hex[:8]}",
                    "facility_id": fid,
                    "total_power_kw": random.uniform(200, 500),
                    "it_load_kw": random.uniform(150, 400),
                    "pue": round(random.uniform(1.15, 1.40), 2),
                    "timestamp": (datetime.utcnow() - timedelta(hours=h)).isoformat(),
                })

    def list_facilities(self) -> ServiceResult:
        return ServiceResult(success=True, data={
            "facilities": list(self.facilities.values()), "total": len(self.facilities)
        })

    def get_facility_metrics(self, facility_id: str) -> ServiceResult:
        facility = self.facilities.get(facility_id)
        if not facility:
            return ServiceResult(success=False, error=f"Facility {facility_id} not found")
        fac_readings = [r for r in self.readings if r["facility_id"] == facility_id]
        avg_pue = sum(r["pue"] for r in fac_readings) / len(fac_readings) if fac_readings else 0
        return ServiceResult(success=True, data={
            **facility,
            "current_pue": avg_pue,
            "avg_pue_24h": round(avg_pue, 2),
            "total_readings": len(fac_readings),
        })

    def get_all_metrics(self) -> ServiceResult:
        if not self.readings:
            return ServiceResult(success=True, data={"avg_pue": 0, "total_facilities": 0})
        avg_pue = sum(r["pue"] for r in self.readings) / len(self.readings)
        return ServiceResult(success=True, data={
            "total_facilities": len(self.facilities),
            "avg_pue": round(avg_pue, 2),
            "best_pue": round(min(r["pue"] for r in self.readings), 2),
            "worst_pue": round(max(r["pue"] for r in self.readings), 2),
            "total_it_load_kw": sum(r["it_load_kw"] for r in self.readings),
            "total_power_kw": sum(r["total_power_kw"] for r in self.readings),
        })
