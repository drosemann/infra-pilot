"""Data models, schemas, and type definitions for Edge/IoT and Green Computing.

This module provides shared data structures, validation schemas, and
type definitions used across all 20 Edge/IoT and Green Computing features.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


# ─── Edge Device Models ───────────────────────────────────────────────

class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    PROVISIONING = "provisioning"
    DECOMMISSIONED = "decommissioned"


class DeviceType(Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    GATEWAY = "gateway"
    CAMERA = "camera"
    EDGE_NODE = "edge_node"
    ROUTER = "router"
    SWITCH = "switch"
    CONTROLLER = "controller"


class FirmwareUpdateStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    REBOOTING = "rebooting"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class OTAMethod(Enum):
    HTTP = "http"
    MQTT = "mqtt"
    COAP = "coap"
    BLE = "ble"
    LORAWAN = "lorawan"


@dataclass
class EdgeDevice:
    device_id: str
    name: str
    device_type: DeviceType = DeviceType.SENSOR
    status: DeviceStatus = DeviceStatus.OFFLINE
    firmware_version: str = "1.0.0"
    hardware_revision: str = "rev-a"
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: Optional[datetime] = None
    registered_at: datetime = field(default_factory=datetime.utcnow)
    battery_level: Optional[float] = None
    signal_strength: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    temperature_celsius: Optional[float] = None
    uptime_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeDevice":
        if "device_type" in data and isinstance(data["device_type"], str):
            data["device_type"] = DeviceType(data["device_type"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = DeviceStatus(data["status"])
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        if "registered_at" in data and isinstance(data["registered_at"], str):
            data["registered_at"] = datetime.fromisoformat(data["registered_at"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class OTAUpdate:
    update_id: str
    device_id: str
    target_version: str
    method: OTAMethod = OTAMethod.HTTP
    status: FirmwareUpdateStatus = FirmwareUpdateStatus.PENDING
    firmware_url: Optional[str] = None
    firmware_size_bytes: Optional[int] = None
    firmware_hash: Optional[str] = None
    checksum_verified: bool = False
    progress_pct: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


@dataclass
class DeviceTelemetry:
    telemetry_id: str
    device_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, float] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"telemetry_id": self.telemetry_id, "device_id": self.device_id,
                  "timestamp": self.timestamp.isoformat(), "metrics": self.metrics,
                  "events": self.events, "alerts": self.alerts}
        if self.raw_data:
            result["raw_data"] = self.raw_data
        return result


@dataclass
class DeviceCommand:
    command_id: str
    device_id: str
    command_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    issued_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timeout_seconds: int = 30
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


# ─── IoT Pipeline Models ──────────────────────────────────────────────

class PipelineStage(Enum):
    INGESTION = "ingestion"
    VALIDATION = "validation"
    NORMALIZATION = "normalization"
    ENRICHMENT = "enrichment"
    ROUTING = "routing"
    STORAGE = "storage"
    ANALYSIS = "analysis"


class PipelineStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINING = "draining"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class DataPipeline:
    pipeline_id: str
    name: str
    pipeline_type: str
    status: PipelineStatus = PipelineStatus.ACTIVE
    stages: List[PipelineStage] = field(default_factory=lambda: [s for s in PipelineStage])
    config: Dict[str, Any] = field(default_factory=dict)
    input_topic: Optional[str] = None
    output_topic: Optional[str] = None
    transform_function: Optional[str] = None
    error_handling: str = "dead_letter"
    batch_size: int = 100
    flush_interval_seconds: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages_processed: int = 0
    messages_failed: int = 0
    throughput_per_second: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, list) and v and isinstance(v[0], Enum):
                result[k] = [s.value for s in v]
            else:
                result[k] = v
        return result


# ─── Green Computing Models ───────────────────────────────────────────

class EnergySource(Enum):
    GRID = "grid"
    SOLAR = "solar"
    WIND = "wind"
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    BATTERY = "battery"
    BIOMASS = "biomass"
    GEOTHERMAL = "geothermal"


class CarbonMetric(Enum):
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"
    TOTAL = "total"
    INTENSITY = "intensity"
    OFFSET = "offset"


@dataclass
class EnergyRecord:
    record_id: str
    device_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    power_watts: float = 0.0
    energy_kwh: float = 0.0
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    power_factor: Optional[float] = None
    source: EnergySource = EnergySource.GRID
    source_pct: Dict[str, float] = field(default_factory=dict)
    cost_usd: Optional[float] = None
    co2_kg: Optional[float] = None
    carbon_intensity_g_per_kwh: Optional[float] = None
    temperature_celsius: Optional[float] = None
    humidity_pct: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


@dataclass
class CarbonFootprint:
    footprint_id: str
    device_id: str
    period_start: datetime
    period_end: datetime
    total_energy_kwh: float = 0.0
    total_co2_kg: float = 0.0
    scope_1_kg: float = 0.0
    scope_2_kg: float = 0.0
    scope_3_kg: float = 0.0
    avg_carbon_intensity: float = 0.0
    renewable_pct: float = 0.0
    offsets_purchased_kg: float = 0.0
    net_co2_kg: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


@dataclass
class OffsetProject:
    project_id: str
    name: str
    project_type: str
    location: str
    registry: str = "verra"
    verification_standard: str = "vcs"
    total_tonnes: float = 0.0
    available_tonnes: float = 0.0
    price_per_tonne_usd: float = 0.0
    status: str = "active"
    description: Optional[str] = None
    website: Optional[str] = None
    certified: bool = True
    listed_at: datetime = field(default_factory=datetime.utcnow)
    co_benefits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


# ─── PUE/DCIM Models ─────────────────────────────────────────────────

@dataclass
class Facility:
    facility_id: str
    name: str
    location: str
    total_power_capacity_kw: float = 0.0
    it_load_capacity_kw: float = 0.0
    cooling_capacity_kw: float = 0.0
    total_area_sqft: Optional[float] = None
    rack_count: int = 0
    pue_target: float = 1.2
    current_pue: Optional[float] = None
    status: str = "operational"
    tier_level: str = "tier_iii"
    certifications: List[str] = field(default_factory=list)
    contact_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


@dataclass
class CoolingUnit:
    unit_id: str
    facility_id: str
    name: str
    cooling_type: str
    capacity_kw: float = 0.0
    current_load_kw: float = 0.0
    efficiency_ratio: float = 1.0
    setpoint_celsius: float = 22.0
    return_water_temp: Optional[float] = None
    supply_water_temp: Optional[float] = None
    status: str = "running"
    runtime_hours: int = 0
    last_maintenance: Optional[datetime] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


# ─── Schedule & Policy Models ─────────────────────────────────────────

class ScheduleFrequency(Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class ShutdownAction(Enum):
    SHUTDOWN = "shutdown"
    HIBERNATE = "hibernate"
    SLEEP = "sleep"
    STOP = "stop"
    SUSPEND = "suspend"


@dataclass
class Schedule:
    schedule_id: str
    name: str
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    cron_expression: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    days_of_week: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"])
    action: ShutdownAction = ShutdownAction.HIBERNATE
    target_device_ids: List[str] = field(default_factory=list)
    enabled: bool = True
    cooldown_minutes: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


# ─── Hardware Models ─────────────────────────────────────────────────

class HardwareCategory(Enum):
    SERVER = "server"
    STORAGE = "storage"
    NETWORKING = "networking"
    GPU = "gpu"
    COOLING = "cooling"
    POWER = "power"
    RACK = "rack"
    CABLE = "cable"
    OTHER = "other"


@dataclass
class HardwareAsset:
    asset_id: str
    name: str
    category: HardwareCategory = HardwareCategory.SERVER
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    purchase_date: Optional[str] = None
    warranty_end: Optional[str] = None
    eol_date: Optional[str] = None
    location: str = ""
    rack_unit: Optional[str] = None
    status: str = "active"
    power_rating_watts: Optional[float] = None
    weight_kg: Optional[float] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    os_version: Optional[str] = None
    firmware_version: Optional[str] = None
    cpu_model: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                result[k] = v.value
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


@dataclass
class MaintenanceRecord:
    record_id: str
    asset_id: str
    maintenance_type: str
    description: str
    technician: str
    scheduled_date: Optional[str] = None
    completed_date: Optional[str] = None
    cost_usd: Optional[float] = None
    parts_replaced: List[str] = field(default_factory=list)
    downtime_hours: Optional[float] = None
    status: str = "scheduled"
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result


# ─── API Response Models ──────────────────────────────────────────────

@dataclass
class APIResponse:
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class PaginatedResponse(APIResponse):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0

    def __post_init__(self):
        if self.total > 0 and self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size


# ─── Validation Schemas ───────────────────────────────────────────────

DEVICE_REGISTRATION_SCHEMA = {
    "required": ["device_id", "name"],
    "types": {
        "device_id": "string",
        "name": "string",
        "firmware_version": "string",
        "device_type": "string",
        "location": "string",
    },
    "ranges": {
        "battery_level": [0.0, 100.0],
        "signal_strength": [-120, -20],
        "cpu_usage": [0.0, 100.0],
        "memory_usage": [0.0, 100.0],
        "disk_usage": [0.0, 100.0],
        "temperature_celsius": [-40, 85],
    }
}

TELEMETRY_SCHEMA = {
    "required": ["device_id", "timestamp"],
    "types": {
        "device_id": "string",
        "timestamp": "string",
    },
    "ranges": {
        "cpu_usage": [0.0, 100.0],
        "memory_usage": [0.0, 100.0],
        "disk_usage": [0.0, 100.0],
        "temperature": [-40, 85],
        "humidity": [0.0, 100.0],
        "power_watts": [0.0, 100000.0],
    }
}

ENERGY_READING_SCHEMA = {
    "required": ["device_id", "power_watts"],
    "types": {
        "device_id": "string",
        "power_watts": "number",
        "source": "string",
        "voltage": "number",
        "current": "number",
    },
    "ranges": {
        "power_watts": [0.0, 100000.0],
        "voltage": [0.0, 1000.0],
        "current": [0.0, 1000.0],
        "power_factor": [0.0, 1.0],
    }
}

CARBON_OFFSET_SCHEMA = {
    "required": ["tonnes_co2", "provider_id"],
    "types": {
        "tonnes_co2": "number",
        "provider_id": "string",
        "project_id": "string",
    },
    "ranges": {
        "tonnes_co2": [0.001, 1000000.0],
    }
}

PUE_READING_SCHEMA = {
    "required": ["facility_id", "total_power_kw", "it_load_kw"],
    "types": {
        "facility_id": "string",
        "total_power_kw": "number",
        "it_load_kw": "number",
    },
    "ranges": {
        "total_power_kw": [0.0, 100000.0],
        "it_load_kw": [0.0, 100000.0],
    }
}
